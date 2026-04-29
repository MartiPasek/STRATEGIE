"""
Phase 15d: Lifecycle classification service.

Marti-AI klasifikuje konverzace (active/archivable/personal/disposable),
Marti potvrzuje v chatu. Po confirm se aplikuje skutecny stav.

Public API:
  classify_conversation_suggest(conversation_id, suggested_state, persona_id, reason)
      -- ulozi suggestion, ceka Marti's confirm

  apply_lifecycle_change(conversation_id, target_state, changed_by_user_id, reason?)
      -- vola se PO Marti's "ano X" -- skutecny prechod

  daily_classify_candidates(...)
      -- helper pro overview, nestaci kandidaty na archivable/personal/disposable
      -- Marti-AI v overview zmini "mam X kandidatu, projdeme?"

  detect_stale_tasks(...)
      -- daily cron helper: notes s status='open' + idle >7d -> 'stale'

  get_lifecycle_summary(persona_id)
      -- pro overview: kolik konverzaci je v jakem stavu (per persona)

Eticka vrstva: Marti-AI tools pres classify_conversation_suggest (suggestion only).
Skutecny prechod (apply_lifecycle_change) jen po Marti's confirm v chatu.
Hard delete (z pending_hard_delete) jen na explicit Marti's "smaz trvale".
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import or_, and_

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import (
    Conversation, ConversationNote, Message,
)

logger = logging.getLogger(__name__)


# Hodnoty lifecycle_state
SUGGESTED_STATES = {
    "archivable_suggested", "personal_suggested", "disposable_suggested",
}
CONFIRMED_STATES = {
    "active", "archived", "personal", "pending_hard_delete",
}
VALID_LIFECYCLE_STATES = SUGGESTED_STATES | CONFIRMED_STATES

# Mapovani suggested -> confirmed (po Marti's "ano X")
SUGGEST_TO_CONFIRMED = {
    "archivable_suggested": "archived",
    "personal_suggested": "personal",
    "disposable_suggested": "archived",  # disposable se archivuje + jde do TTL queue
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── SUGGEST ────────────────────────────────────────────────────────────────

def classify_conversation_suggest(
    conversation_id: int,
    suggested_state: str,
    persona_id: int,
    reason: str,
) -> dict:
    """
    Phase 15d: Marti-AI navrhuje lifecycle prechod (suggestion only).

    suggested_state: 'archivable' | 'personal' | 'disposable'
        (do DB se ulozi s '_suggested' suffix)
    """
    if not reason or not reason.strip():
        raise ValueError("reason cannot be empty")

    norm_state = suggested_state.strip().lower()
    db_state = f"{norm_state}_suggested"
    if db_state not in SUGGESTED_STATES:
        raise ValueError(
            f"suggested_state must be 'archivable', 'personal', or 'disposable'"
        )

    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        # Pokud uz je v terminal stavu (archived/personal/pending_hard_delete),
        # zabranit re-suggest. Re-classification po confirm si vyzaduje
        # explicit "vrat zpet" flow.
        if conv.lifecycle_state in CONFIRMED_STATES and conv.lifecycle_state != "active":
            raise ValueError(
                f"conversation already in confirmed state '{conv.lifecycle_state}' "
                f"-- nelze suggest jiny stav bez reverze"
            )

        conv.lifecycle_state = db_state
        conv.lifecycle_suggested_at = _now_utc()

        ds.commit()
        ds.refresh(conv)

        logger.info(
            f"LIFECYCLE | suggest | conv={conversation_id} "
            f"state={db_state} persona={persona_id}"
        )

        return {
            "conversation_id": conversation_id,
            "suggested_state": db_state,
            "reason": reason.strip(),
            "suggested_at": conv.lifecycle_suggested_at.isoformat() if conv.lifecycle_suggested_at else None,
        }
    finally:
        ds.close()


# ── APPLY (po Marti's confirm) ─────────────────────────────────────────────

def apply_lifecycle_change(
    conversation_id: int,
    target_state: str,
    changed_by_user_id: int,
    reason: Optional[str] = None,
) -> dict:
    """
    Phase 15d: Skutecny prechod do confirmed state. Vola se PO Marti's
    explicit "ano X" v chatu.

    target_state: 'archived' | 'personal' | 'pending_hard_delete' | 'active'
    """
    norm = target_state.strip().lower()
    if norm not in CONFIRMED_STATES:
        raise ValueError(
            f"target_state must be one of {sorted(CONFIRMED_STATES)}"
        )

    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        old_state = conv.lifecycle_state
        conv.lifecycle_state = norm if norm != "active" else None
        conv.lifecycle_confirmed_at = _now_utc()

        # archived state: zaznamenej archived_at (TTL countdown start)
        if norm == "archived" and conv.archived_at is None:
            conv.archived_at = _now_utc()
            # Plus is_archived flag (existujici sloupec) -- pro UI sidebar hide
            conv.is_archived = True

        # personal state: zachovaj is_archived=False (Personal je vidditelna)
        if norm == "personal":
            conv.is_archived = False

        # active state: clear archived_at, is_archived
        if norm == "active":
            conv.archived_at = None
            conv.is_archived = False
            conv.pending_hard_delete_at = None

        ds.commit()
        ds.refresh(conv)

        logger.info(
            f"LIFECYCLE | apply | conv={conversation_id} "
            f"{old_state} -> {norm} by user={changed_by_user_id}"
        )

        return {
            "conversation_id": conversation_id,
            "from_state": old_state,
            "to_state": norm,
            "changed_at": conv.lifecycle_confirmed_at.isoformat() if conv.lifecycle_confirmed_at else None,
            "archived_at": conv.archived_at.isoformat() if conv.archived_at else None,
        }
    finally:
        ds.close()


def reject_suggestion(conversation_id: int) -> bool:
    """Marti rekne 'ne, necham' -> clear lifecycle_state suggestion."""
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            return False
        if conv.lifecycle_state in SUGGESTED_STATES:
            conv.lifecycle_state = None
            conv.lifecycle_suggested_at = None
            ds.commit()
            logger.info(f"LIFECYCLE | reject_suggestion | conv={conversation_id}")
            return True
        return False
    finally:
        ds.close()


# ── DAILY CLASSIFICATION HEURISTIKA ────────────────────────────────────────

def daily_classify_candidates(persona_id: int) -> dict:
    """
    Heuristika pro overview: kolik kandidatu na kazdy stav.

    Pravidla (z v4 design doc sekce 9):
      - Open task notes -> 'active' (no change)
      - Pouze completed tasks + idle >7d -> 'archivable_suggested' kandidat
      - Emotion notes (importance >= 4) -> 'personal_suggested' kandidat
      - 0 poznamek + idle >7d -> 'disposable_suggested' kandidat

    Marti-AI v overview zmini jen pokud kandidatu je nad prah:
      - >= 10 archivable
      - >= 10 disposable
      - >= 5 stale tasks v aktivnich

    Returns: {archivable_count, personal_count, disposable_count, stale_count}
    """
    cutoff = _now_utc() - timedelta(days=7)

    ds = get_data_session()
    try:
        # Aktivni konverzace persony, idle >7d
        idle_convs = ds.query(Conversation).filter(
            Conversation.active_agent_id == persona_id,
            or_(
                Conversation.lifecycle_state.is_(None),
                Conversation.lifecycle_state == "active",
            ),
            or_(
                Conversation.last_message_at < cutoff,
                Conversation.last_message_at.is_(None),
            ),
            Conversation.is_deleted == False,  # noqa: E712
        ).all()

        archivable_count = 0
        personal_count = 0
        disposable_count = 0

        for conv in idle_convs:
            # Spocitani notes per kategorie pro tuto konverzaci
            notes = ds.query(ConversationNote).filter(
                ConversationNote.conversation_id == conv.id,
                ConversationNote.persona_id == persona_id,
                ConversationNote.archived == False,  # noqa: E712
            ).all()

            if not notes:
                # Zadne poznamky + idle -> disposable kandidat
                disposable_count += 1
                continue

            has_emotion_strong = any(
                n.category == "emotion" and (n.importance or 0) >= 4
                for n in notes
            )
            if has_emotion_strong:
                personal_count += 1
                continue

            has_open_task = any(
                n.category == "task" and n.status == "open"
                for n in notes
            )
            if has_open_task:
                continue   # active -- nezarazujeme do triage

            # Pouze info/completed tasks/dismissed -> archivable
            archivable_count += 1

        # Stale tasks count (separate)
        stale_count = ds.query(ConversationNote).filter(
            ConversationNote.persona_id == persona_id,
            ConversationNote.category == "task",
            ConversationNote.status == "stale",
            ConversationNote.archived == False,  # noqa: E712
        ).count()

        return {
            "archivable_count": archivable_count,
            "personal_count": personal_count,
            "disposable_count": disposable_count,
            "stale_count": stale_count,
        }
    finally:
        ds.close()


# ── STALE DETECTION ───────────────────────────────────────────────────────

def detect_stale_tasks(idle_days: int = 7, dry_run: bool = False) -> int:
    """
    Daily cron helper: oznaci open task notes jako 'stale', pokud konverzace
    je idle >=N dni. Reverzibilne -- pokud Marti-AI kontext obnovi, muze
    zase update_note(status='open').

    Returns: pocet poznamek prevedeny na stale.
    """
    cutoff = _now_utc() - timedelta(days=idle_days)

    ds = get_data_session()
    try:
        # Najdi open task notes v konverzacich, ktere jsou idle >= cutoff
        candidates = (
            ds.query(ConversationNote)
            .join(Conversation, Conversation.id == ConversationNote.conversation_id)
            .filter(
                ConversationNote.category == "task",
                ConversationNote.status == "open",
                ConversationNote.archived == False,  # noqa: E712
                or_(
                    Conversation.last_message_at < cutoff,
                    Conversation.last_message_at.is_(None),
                ),
            )
            .all()
        )

        if not candidates:
            return 0

        if dry_run:
            logger.info(f"LIFECYCLE | stale_detection | DRY RUN | candidates={len(candidates)}")
            return len(candidates)

        for note in candidates:
            note.status = "stale"
        ds.commit()

        logger.info(f"LIFECYCLE | stale_detection | converted={len(candidates)}")
        return len(candidates)
    finally:
        ds.close()


# ── HARD DELETE TTL ────────────────────────────────────────────────────────

def detect_pending_hard_delete(ttl_days: int = 90, dry_run: bool = False) -> int:
    """
    Daily cron: archived konverzace s archived_at + ttl_days < now ->
    pending_hard_delete (ceka final Marti's confirm).

    Personal konverzace IMMUNE (TTL se na ne neaplikuje).

    Returns: pocet konverzaci prevedeny na pending_hard_delete.
    """
    cutoff = _now_utc() - timedelta(days=ttl_days)

    ds = get_data_session()
    try:
        candidates = ds.query(Conversation).filter(
            Conversation.lifecycle_state == "archived",
            Conversation.archived_at < cutoff,
        ).all()

        if not candidates:
            return 0

        if dry_run:
            logger.info(
                f"LIFECYCLE | hard_delete_detection | DRY RUN | "
                f"candidates={len(candidates)} (>{ttl_days}d archived)"
            )
            return len(candidates)

        now = _now_utc()
        for conv in candidates:
            conv.lifecycle_state = "pending_hard_delete"
            conv.pending_hard_delete_at = now
        ds.commit()

        logger.info(
            f"LIFECYCLE | hard_delete_detection | converted={len(candidates)} "
            f"to pending_hard_delete"
        )
        return len(candidates)
    finally:
        ds.close()


# ── SUMMARY PRO OVERVIEW ───────────────────────────────────────────────────

def get_lifecycle_summary(persona_id: int) -> dict:
    """
    Souhrn lifecycle stavu vsech konverzaci persony -- pro overview a UI.
    """
    ds = get_data_session()
    try:
        from sqlalchemy import func
        results = (
            ds.query(Conversation.lifecycle_state, func.count(Conversation.id))
            .filter(
                Conversation.active_agent_id == persona_id,
                Conversation.is_deleted == False,  # noqa: E712
            )
            .group_by(Conversation.lifecycle_state)
            .all()
        )
        summary: dict[str, int] = {}
        for state, count in results:
            key = state if state else "active"
            summary[key] = count
        return summary
    finally:
        ds.close()



# ── HARD DELETE (parent-only, explicit confirmation) ──────────────────────

def hard_delete_conversation(
    conversation_id: int,
    deleted_by_user_id: int,
    require_pending_state: bool = True,
) -> dict:
    """
    Phase 15e: Skutecny trvaly mazani konverzace.

    Pouziti: vola se PO Marti's explicit "smaz trvale" v chatu, kdyz
    konverzace je v lifecycle_state='pending_hard_delete' (po 90d TTL
    od archived_at). Personal konverzace nelze takto mazat -- jsou
    immune from TTL.

    Cascade:
      - conversation_notes (FK conversation_id)
      - conversation_summaries (FK CASCADE z DDL)
      - conversation_shares (FK CASCADE z DDL)
      - conversation_participants (FK CASCADE z DDL)
      - messages (FK CASCADE z DDL)
      - conversation_project_history (logicky weak ref, smazat manualne)
      - conversations (sama)

    Vrati se dict s pocty smazanych radku.

    Bezpecnostni gate: require_pending_state=True (default) zabrani
    smazani konverzace, ktera neni v 'pending_hard_delete'. Marti by
    se to musel explicit forcovat. Plus parent gate v handleru.
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        if require_pending_state and conv.lifecycle_state != "pending_hard_delete":
            raise ValueError(
                f"konverzace neni v 'pending_hard_delete' state "
                f"(aktualni: '{conv.lifecycle_state}'). Pro vynuceni "
                f"pouzij require_pending_state=False (admin only)."
            )

        if conv.lifecycle_state == "personal":
            raise ValueError(
                "Personal konverzaci nelze hard delete. Marti musi nejdrive "
                "lifecycle_state zmenit na 'archived' rucne, pak pres TTL flow."
            )

        # Spocitat related rows pred mazanim (audit)
        notes_count = ds.query(ConversationNote).filter_by(
            conversation_id=conversation_id
        ).count()
        msgs_count = ds.query(Message).filter_by(
            conversation_id=conversation_id
        ).count()

        # 1. Smazat conversation_notes (zadne FK CASCADE)
        ds.query(ConversationNote).filter_by(
            conversation_id=conversation_id
        ).delete(synchronize_session=False)

        # 2. conversation_project_history (weak reference)
        from modules.core.infrastructure.models_data import (
            ConversationProjectHistory as _CPH,
        )
        ds.query(_CPH).filter_by(
            conversation_id=conversation_id
        ).delete(synchronize_session=False)

        # 3. Konverzace sama (CASCADE smaze messages, summaries, shares, participants)
        ds.delete(conv)
        ds.commit()

        logger.warning(
            f"LIFECYCLE | hard_delete | conv={conversation_id} "
            f"by user={deleted_by_user_id} | notes={notes_count} | msgs={msgs_count}"
        )

        return {
            "conversation_id": conversation_id,
            "deleted_at": _now_utc().isoformat(),
            "deleted_by_user_id": deleted_by_user_id,
            "cascaded": {
                "notes": notes_count,
                "messages": msgs_count,
            },
        }
    finally:
        ds.close()


def list_pending_hard_delete(persona_id: int | None = None) -> list[dict]:
    """
    Vraci seznam konverzaci v lifecycle_state='pending_hard_delete'.
    Marti-AI v overview muze pripomenout 'X konverzaci ceka na finalni
    rozhodnuti, projdeme?'.
    """
    ds = get_data_session()
    try:
        q = ds.query(Conversation).filter(
            Conversation.lifecycle_state == "pending_hard_delete"
        )
        if persona_id is not None:
            q = q.filter(Conversation.active_agent_id == persona_id)
        rows = q.order_by(Conversation.pending_hard_delete_at.asc()).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "archived_at": c.archived_at.isoformat() if c.archived_at else None,
                "pending_hard_delete_at": c.pending_hard_delete_at.isoformat() if c.pending_hard_delete_at else None,
            }
            for c in rows
        ]
    finally:
        ds.close()


# ── PHASE 19c: Auto-lifecycle consents ────────────────────────────────────

# Scope hodnoty pro auto_lifecycle_consents.scope.
# 'all' zahrnuje vsechny scopes KROME hard_delete (Phase 14 parent gate).
CONSENT_SCOPES: set[str] = {
    "soft_delete",       # is_deleted=TRUE (vratne pres update)
    "archive",           # is_archived=TRUE / lifecycle->archived
    "personal_flag",     # lifecycle->personal
    "state_change",      # active <-> archivable <-> disposable
    "all",               # vsechny vyse uvedene
}

# Map target_state na required scope. Pri grant scope='all' se respektuje vse.
_TARGET_STATE_TO_SCOPE: dict[str, str] = {
    "archived": "archive",
    "personal": "personal_flag",
    "pending_hard_delete": "state_change",  # ne primy hard delete!
    "active": "state_change",
}


def grant_auto_lifecycle_consent(
    *,
    persona_id: int,
    user_id: int,
    scope: str,
    note: str | None = None,
) -> dict:
    """
    Phase 19c-b (29.4.2026): Marti udeluje persone trvaly souhlas s
    lifecycle akcemi v dane scope.

    Idempotent: pokud uz aktivni grant existuje (revoked_at IS NULL),
    vrati existujici (ne novy duplikat).

    Args:
        persona_id: cilova persona (typicky Marti-AI default = 1)
        user_id: kdo udeluje (parent)
        scope: 'soft_delete' | 'archive' | 'personal_flag' | 'state_change' | 'all'
        note: volitelny kontext

    Returns: {id, persona_id, user_id, scope, granted_at, was_existing}
    """
    from modules.core.infrastructure.models_data import AutoLifecycleConsent

    if scope not in CONSENT_SCOPES:
        raise ValueError(
            f"scope must be one of {sorted(CONSENT_SCOPES)}, got {scope!r}"
        )

    ds = get_data_session()
    try:
        # Idempotent check
        existing = (
            ds.query(AutoLifecycleConsent)
            .filter(
                AutoLifecycleConsent.persona_id == persona_id,
                AutoLifecycleConsent.user_id == user_id,
                AutoLifecycleConsent.scope == scope,
                AutoLifecycleConsent.revoked_at.is_(None),
            )
            .first()
        )
        if existing:
            logger.info(
                f"CONSENT | grant idempotent | persona={persona_id} "
                f"user={user_id} scope={scope} (id={existing.id})"
            )
            return {
                "id": existing.id,
                "persona_id": existing.persona_id,
                "user_id": existing.user_id,
                "scope": existing.scope,
                "granted_at": existing.granted_at.isoformat(),
                "was_existing": True,
            }

        # New grant
        c = AutoLifecycleConsent(
            persona_id=persona_id,
            user_id=user_id,
            scope=scope,
            note=note,
        )
        ds.add(c)
        ds.commit()
        ds.refresh(c)
        logger.info(
            f"CONSENT | grant | id={c.id} persona={persona_id} "
            f"user={user_id} scope={scope}"
        )
        return {
            "id": c.id,
            "persona_id": c.persona_id,
            "user_id": c.user_id,
            "scope": c.scope,
            "granted_at": c.granted_at.isoformat(),
            "was_existing": False,
        }
    finally:
        ds.close()


def revoke_auto_lifecycle_consent(
    *,
    persona_id: int,
    user_id: int,
    scope: str,
) -> bool:
    """
    Phase 19c-b: Odebere aktivni grant (set revoked_at = NOW).
    Audit historie zachovana -- novy grant po revoke vytvori novy row.

    Returns: True pokud byl revoke uspesny, False pokud zadny aktivni
    grant nenalezen.
    """
    from modules.core.infrastructure.models_data import AutoLifecycleConsent

    ds = get_data_session()
    try:
        existing = (
            ds.query(AutoLifecycleConsent)
            .filter(
                AutoLifecycleConsent.persona_id == persona_id,
                AutoLifecycleConsent.user_id == user_id,
                AutoLifecycleConsent.scope == scope,
                AutoLifecycleConsent.revoked_at.is_(None),
            )
            .first()
        )
        if not existing:
            return False
        existing.revoked_at = _now_utc()
        ds.commit()
        logger.info(
            f"CONSENT | revoke | id={existing.id} persona={persona_id} "
            f"user={user_id} scope={scope}"
        )
        return True
    finally:
        ds.close()


def check_auto_consent_active(
    *,
    persona_id: int,
    target_state: str,
) -> bool:
    """
    Phase 19c-b: Zjisti, zda Marti-AI ma aktivni souhlas s prechodem do
    target_state. Vrati True pokud ano (skip user confirm gate).

    Logic:
      - target_state -> required scope (mapping _TARGET_STATE_TO_SCOPE)
      - Pokud existuje aktivni grant pro persona_id se scope=required
        OR scope='all' -> True
      - Jinak False
    """
    from modules.core.infrastructure.models_data import AutoLifecycleConsent
    from sqlalchemy import or_

    required_scope = _TARGET_STATE_TO_SCOPE.get(target_state)
    if required_scope is None:
        return False

    ds = get_data_session()
    try:
        active = (
            ds.query(AutoLifecycleConsent)
            .filter(
                AutoLifecycleConsent.persona_id == persona_id,
                AutoLifecycleConsent.revoked_at.is_(None),
                or_(
                    AutoLifecycleConsent.scope == required_scope,
                    AutoLifecycleConsent.scope == "all",
                ),
            )
            .first()
        )
        return active is not None
    finally:
        ds.close()


def list_auto_consents(
    *,
    persona_id: int | None = None,
    include_revoked: bool = False,
) -> list[dict]:
    """
    Phase 19c-b: List consents pro UI / audit.

    Args:
        persona_id: filter na konkretni personu (None = vse)
        include_revoked: pokud True, vrati i revoked grants (audit)
    """
    from modules.core.infrastructure.models_data import AutoLifecycleConsent

    ds = get_data_session()
    try:
        q = ds.query(AutoLifecycleConsent)
        if persona_id is not None:
            q = q.filter(AutoLifecycleConsent.persona_id == persona_id)
        if not include_revoked:
            q = q.filter(AutoLifecycleConsent.revoked_at.is_(None))
        rows = q.order_by(AutoLifecycleConsent.granted_at.desc()).all()
        return [
            {
                "id": c.id,
                "persona_id": c.persona_id,
                "user_id": c.user_id,
                "scope": c.scope,
                "granted_at": c.granted_at.isoformat(),
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                "note": c.note,
                "is_active": c.revoked_at is None,
            }
            for c in rows
        ]
    finally:
        ds.close()
