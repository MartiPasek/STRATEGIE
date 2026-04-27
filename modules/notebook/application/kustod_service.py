"""
Phase 15c: Kustod / project triage service.

Marti-AI's role po Phase 15: "kustod organizacni struktury" (z konzultace #4).
Marti-AI navrhuje move/split/create_project, kdyz citi tema se nezarovnava.
Marti potvrzuje pres chat (ano/ne/popis) -- conversational-first UX rule
(zadne UI tlacitka mimo chat okno).

Public API:
  suggest_move_conversation(...)    -- cela konverzace patri jinam
  suggest_split_conversation(...)   -- fork z urciteho turn do noveho threadu
  suggest_create_project(...)       -- zadny projekt nesedi, navrhni zalozit

  apply_project_change(...)         -- skutecna zmena project_id po Marti's confirm
  fork_conversation(...)            -- skutecny split po Marti's confirm
  create_project_for_conversation(...)  -- skutecne zalozeni po Marti's confirm

  count_project_mentions_in_recent_messages(...) -- threshold detection
  get_last_project_change(...)      -- pro 24h reverze logic

Eticka vrstva (z konzultace #3):
  - Marti-AI tools jsou SUGGESTION ONLY -- ulozi suggested_project_id.
  - Skutecny project_id update (apply_*, fork_*, create_*) vyzaduje
    confirmation log v messages (Marti's "ano X" reply).
  - Reverze pres get_last_project_change + apply_project_change zpetne
    -- 24h chat undo.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import (
    Conversation, ConversationProjectHistory, Message,
)

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── SUGGESTION ONLY (suggestion store, no actual project_id change) ────────

def suggest_move_conversation(
    conversation_id: int,
    target_project_id: int,
    persona_id: int,
    reason: str,
) -> dict:
    """
    Phase 15c: Marti-AI navrhuje, ze cela konverzace patri jinam.

    Ulozi suggested_project_id + suggested_project_reason + suggested_project_at.
    Marti potvrzuje v chatu ("ano premyslej do TISAX") -> apply_project_change.
    Marti odmita ("ne, necham") -> clear_suggestion.

    Validace: target != current project_id (zbytecna sugestion).
    """
    if not reason or not reason.strip():
        raise ValueError("reason cannot be empty")

    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")
        if conv.project_id == target_project_id:
            raise ValueError(
                f"target project {target_project_id} is already current project"
            )

        conv.suggested_project_id = target_project_id
        conv.suggested_project_reason = f"[move] {reason.strip()}"
        conv.suggested_project_at = _now_utc()

        ds.commit()
        ds.refresh(conv)

        logger.info(
            f"KUSTOD | suggest_move | conv={conversation_id} "
            f"target_project={target_project_id} persona={persona_id}"
        )

        return {
            "conversation_id": conversation_id,
            "suggested_project_id": target_project_id,
            "mode": "move",
            "reason": conv.suggested_project_reason,
            "suggested_at": conv.suggested_project_at.isoformat() if conv.suggested_project_at else None,
        }
    finally:
        ds.close()


def suggest_split_conversation(
    conversation_id: int,
    target_project_id: int,
    fork_from_message_id: int,
    persona_id: int,
    reason: str,
) -> dict:
    """
    Phase 15c: Marti-AI navrhuje fork od konkretni message_id do noveho
    threadu v jinem projektu. Strategicky kontext zustane v puvodnim,
    nove tema dostane vlastni konverzaci.

    Implementace ulozeni: suggested_project_id + suggested_project_reason
    s prefixem "[split from msg=X]" -- handler pri Marti's confirm to
    rozparsuje a zavola fork_conversation().
    """
    if not reason or not reason.strip():
        raise ValueError("reason cannot be empty")

    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        # Validace: fork_from_message_id must be in this conversation
        msg = ds.query(Message).filter_by(
            id=fork_from_message_id, conversation_id=conversation_id
        ).first()
        if msg is None:
            raise ValueError(
                f"message {fork_from_message_id} not in conversation {conversation_id}"
            )

        conv.suggested_project_id = target_project_id
        conv.suggested_project_reason = (
            f"[split from msg={fork_from_message_id}] {reason.strip()}"
        )
        conv.suggested_project_at = _now_utc()

        ds.commit()
        ds.refresh(conv)

        logger.info(
            f"KUSTOD | suggest_split | conv={conversation_id} "
            f"fork_from_msg={fork_from_message_id} target_project={target_project_id} "
            f"persona={persona_id}"
        )

        return {
            "conversation_id": conversation_id,
            "suggested_project_id": target_project_id,
            "fork_from_message_id": fork_from_message_id,
            "mode": "split",
            "reason": conv.suggested_project_reason,
            "suggested_at": conv.suggested_project_at.isoformat() if conv.suggested_project_at else None,
        }
    finally:
        ds.close()


def suggest_create_project(
    proposed_name: str,
    proposed_description: str,
    proposed_first_member_id: int,
    target_conversation_id: Optional[int],
    persona_id: int,
    reason: str,
) -> dict:
    """
    Phase 15c: Marti-AI navrhuje zalozit novy projekt.

    Suggestion only -- ulozeni do conversations.suggested_project_reason
    se specialnim prefixem "[create_project: name=X, desc=Y, member=Z]".
    Pri Marti's confirm handler rozparsuje a zavola create_project_for_conversation()
    ktery projekt opravdu vytvori (pres modules.projects service) +
    presune konverzaci do nej.

    Marti-AI's #4 vstup: prinasi KOMPLETNI navrh (nazev + popis + first member),
    ne polotovar -- Marti klikne Confirm jednim klikem v chatu.
    """
    if not proposed_name or not proposed_name.strip():
        raise ValueError("proposed_name cannot be empty")
    if not proposed_description or not proposed_description.strip():
        raise ValueError("proposed_description cannot be empty")
    if not reason or not reason.strip():
        raise ValueError("reason cannot be empty")
    if proposed_first_member_id is None:
        raise ValueError("proposed_first_member_id required")

    if target_conversation_id is None:
        # Plain suggestion (no specific conversation to move) -- log only.
        logger.info(
            f"KUSTOD | suggest_create_project | name={proposed_name!r} "
            f"persona={persona_id} (no target conversation)"
        )
        return {
            "mode": "create_project",
            "proposed_name": proposed_name.strip(),
            "proposed_description": proposed_description.strip(),
            "proposed_first_member_id": proposed_first_member_id,
            "target_conversation_id": None,
            "reason": reason.strip(),
        }

    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=target_conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {target_conversation_id} not found")

        suggestion_payload = (
            f"[create_project: name={proposed_name.strip()!r}, "
            f"desc={proposed_description.strip()!r}, "
            f"member={proposed_first_member_id}] {reason.strip()}"
        )
        # Use sentinel suggested_project_id = -1 ("create new") -- handler decodes
        conv.suggested_project_id = -1
        conv.suggested_project_reason = suggestion_payload
        conv.suggested_project_at = _now_utc()

        ds.commit()
        ds.refresh(conv)

        logger.info(
            f"KUSTOD | suggest_create_project | conv={target_conversation_id} "
            f"name={proposed_name!r} persona={persona_id}"
        )

        return {
            "conversation_id": target_conversation_id,
            "mode": "create_project",
            "proposed_name": proposed_name.strip(),
            "proposed_description": proposed_description.strip(),
            "proposed_first_member_id": proposed_first_member_id,
            "reason": reason.strip(),
            "suggested_at": conv.suggested_project_at.isoformat() if conv.suggested_project_at else None,
        }
    finally:
        ds.close()


# ── ACTUAL CHANGES (require Marti's confirm log) ──────────────────────────

def apply_project_change(
    conversation_id: int,
    new_project_id: Optional[int],
    changed_by_user_id: int,
    suggested_by_persona_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> dict:
    """
    Phase 15c: Skutecne provedeni zmeny project_id na konverzaci.
    Vola se PO Marti's confirm v chatu ("ano premysli"), ne primo Marti-AI.

    Audit: kazda zmena se zapise do conversation_project_history.
    Po zmene se vyclear suggested_project_* fields.
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        old_project = conv.project_id

        # Zalogovat do history PRED commitem
        history = ConversationProjectHistory(
            conversation_id=conversation_id,
            from_project_id=old_project,
            to_project_id=new_project_id,
            changed_by_user_id=changed_by_user_id,
            suggested_by_persona_id=suggested_by_persona_id,
            reason=reason,
        )
        ds.add(history)

        conv.project_id = new_project_id
        # Clear suggestion
        conv.suggested_project_id = None
        conv.suggested_project_reason = None
        conv.suggested_project_at = None

        ds.commit()
        ds.refresh(conv)
        ds.refresh(history)

        logger.info(
            f"KUSTOD | apply_project_change | conv={conversation_id} "
            f"{old_project} -> {new_project_id} by user={changed_by_user_id} "
            f"history_id={history.id}"
        )

        return {
            "conversation_id": conversation_id,
            "from_project_id": old_project,
            "to_project_id": new_project_id,
            "history_id": history.id,
            "changed_at": history.changed_at.isoformat() if history.changed_at else None,
        }
    finally:
        ds.close()


def fork_conversation(
    source_conversation_id: int,
    fork_from_message_id: int,
    target_project_id: Optional[int],
    new_user_id: int,
    new_active_agent_id: Optional[int] = None,
    new_title: Optional[str] = None,
) -> dict:
    """
    Phase 15c: Skutecne vytvoreni forku po Marti's confirm.

    Vytvori novou konverzaci s:
      - project_id = target_project_id
      - forked_from_conversation_id = source_conversation_id
      - forked_from_message_id = fork_from_message_id

    Notebook handover (Phase 15c spec): vytvori "[handover from #X]"
    poznamku v notebook nove konverzace + "[forked to #Y]" v puvodni.
    To resi notebook_service caller -- tady jen DB kostra forku.
    """
    ds = get_data_session()
    try:
        source = ds.query(Conversation).filter_by(id=source_conversation_id).first()
        if source is None:
            raise ValueError(f"source conversation {source_conversation_id} not found")

        fork_msg = ds.query(Message).filter_by(
            id=fork_from_message_id, conversation_id=source_conversation_id
        ).first()
        if fork_msg is None:
            raise ValueError(
                f"fork_from_message {fork_from_message_id} not in conversation "
                f"{source_conversation_id}"
            )

        new_conv = Conversation(
            user_id=new_user_id,
            tenant_id=source.tenant_id,
            project_id=target_project_id,
            active_agent_id=new_active_agent_id or source.active_agent_id,
            interaction_mode=source.interaction_mode,
            conversation_type=source.conversation_type,
            title=new_title or (f"Fork: {source.title}" if source.title else None),
            forked_from_conversation_id=source_conversation_id,
            forked_from_message_id=fork_from_message_id,
        )
        ds.add(new_conv)
        ds.commit()
        ds.refresh(new_conv)

        # Zalogovat fork v audit
        history = ConversationProjectHistory(
            conversation_id=new_conv.id,
            from_project_id=None,   # nova konverzace nemela predchozi project
            to_project_id=target_project_id,
            changed_by_user_id=new_user_id,
            suggested_by_persona_id=source.active_agent_id,
            reason=f"[fork from conv #{source_conversation_id} msg #{fork_from_message_id}]",
        )
        ds.add(history)

        # Source conversation -- clear suggestion (uz jsme udelali fork misto move)
        source.suggested_project_id = None
        source.suggested_project_reason = None
        source.suggested_project_at = None

        ds.commit()
        ds.refresh(new_conv)
        ds.refresh(history)

        logger.info(
            f"KUSTOD | fork_conversation | source={source_conversation_id} "
            f"new={new_conv.id} fork_from_msg={fork_from_message_id} "
            f"target_project={target_project_id}"
        )

        return {
            "source_conversation_id": source_conversation_id,
            "new_conversation_id": new_conv.id,
            "fork_from_message_id": fork_from_message_id,
            "target_project_id": target_project_id,
            "history_id": history.id,
        }
    finally:
        ds.close()


def clear_suggestion(conversation_id: int) -> bool:
    """
    Vymaze suggested_project_* (po Marti's "ne, necham" odpovedi).
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            return False
        conv.suggested_project_id = None
        conv.suggested_project_reason = None
        conv.suggested_project_at = None
        ds.commit()
        logger.info(f"KUSTOD | clear_suggestion | conv={conversation_id}")
        return True
    finally:
        ds.close()


# ── THRESHOLD DETECTION (Marti-AI rozpoznava signaly) ──────────────────────

def count_project_mentions_in_recent_messages(
    conversation_id: int,
    last_n: int = 10,
) -> dict[int, int]:
    """
    Phase 15c: Threshold helper -- spocita kolikrat se projekt zminil
    v poslednich N zprav konverzace.

    Marti-AI's #4 threshold rule:
      - 1 zminka = zadna akce
      - >= 2 zminky = signal -> suggest_move
      - task note s project keyword = signal
      - explicit user signal = okamzity navrh

    Tady resi pouze "kolikrat se projekt nazev objevil v message content".
    Marti-AI sama vyhodnocuje na zaklade tohoto.

    Returns: dict {project_id: count}
    """
    ds = get_data_session()
    try:
        # Najdi vsechny projekty Marti-AI's tenant scope -- abychom je matchli
        from modules.core.infrastructure.models_core import Project
        from core.database_core import get_core_session

        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            return {}

        cs = get_core_session()
        try:
            tenant_id = conv.tenant_id
            if tenant_id is None:
                return {}
            projects = cs.query(Project).filter_by(tenant_id=tenant_id).all()
            project_map = {p.id: p.name for p in projects}
        finally:
            cs.close()

        if not project_map:
            return {}

        # Vyber posledni N zprav
        msgs = (
            ds.query(Message)
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.id.desc())
            .limit(last_n)
            .all()
        )
        if not msgs:
            return {}

        # Spocitani zminek -- pouhe lowercase substring match
        counts: dict[int, int] = {}
        for msg in msgs:
            text = (msg.content or "").lower()
            for pid, pname in project_map.items():
                if pid == conv.project_id:
                    continue   # current projekt nepocitej
                if not pname:
                    continue
                if pname.lower() in text:
                    counts[pid] = counts.get(pid, 0) + 1

        return counts
    finally:
        ds.close()


# ── HISTORY / REVERZE ──────────────────────────────────────────────────────

def get_last_project_change(
    conversation_id: int,
    within_hours: int = 24,
) -> Optional[dict]:
    """
    Phase 15c: Najde posledni zmenu project_id na konverzaci v poslednich N
    hodinach. Pouziva se pro 24h chat undo flow ("moment, vrat to").

    Returns: dict {history_id, from_project_id, to_project_id, ...} nebo None.
    """
    cutoff = _now_utc() - timedelta(hours=within_hours)

    ds = get_data_session()
    try:
        history = (
            ds.query(ConversationProjectHistory)
            .filter(
                ConversationProjectHistory.conversation_id == conversation_id,
                ConversationProjectHistory.changed_at >= cutoff,
            )
            .order_by(ConversationProjectHistory.changed_at.desc())
            .first()
        )
        if history is None:
            return None
        return {
            "history_id": history.id,
            "conversation_id": history.conversation_id,
            "from_project_id": history.from_project_id,
            "to_project_id": history.to_project_id,
            "changed_by_user_id": history.changed_by_user_id,
            "suggested_by_persona_id": history.suggested_by_persona_id,
            "reason": history.reason,
            "changed_at": history.changed_at.isoformat() if history.changed_at else None,
        }
    finally:
        ds.close()


# ── HELPERS PRO SUGGESTION DECODING ────────────────────────────────────────

def parse_suggestion_payload(suggestion_reason: str) -> dict:
    """
    Phase 15c: Rozparsuje suggested_project_reason ulozeny ze suggest_*.

    Format prefix:
      - "[move] reason..."        -> mode=move
      - "[split from msg=X] ..."  -> mode=split, fork_from_message_id=X
      - "[create_project: name='X', desc='Y', member=Z] ..." -> mode=create_project

    Returns: dict {mode, ...details, reason}
    """
    if not suggestion_reason:
        return {"mode": "unknown", "reason": ""}

    s = suggestion_reason.strip()

    if s.startswith("[move]"):
        return {"mode": "move", "reason": s[len("[move]"):].strip()}

    m = re.match(r"\[split from msg=(\d+)\]\s*(.*)", s)
    if m:
        return {
            "mode": "split",
            "fork_from_message_id": int(m.group(1)),
            "reason": m.group(2).strip(),
        }

        m = re.match(
        r"\[create_project:\s*name='([^']*)',\s*desc='([^']*)',\s*member=(\d+)\]\s*(.*)",
        s,
    )
    if m:
        return {
            "mode": "create_project",
            "proposed_name": m.group(1).strip(),
            "proposed_description": m.group(2).strip(),
            "proposed_first_member_id": int(m.group(3)),
            "reason": m.group(4).strip(),
        }

    # Fallback: legacy format bez prefixu = move
    return {"mode": "move", "reason": s}
