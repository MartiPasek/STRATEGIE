"""
Activity service -- Phase 16-A (28.4.2026).

Marti-AI's tichá kontinuita: cross-conversation deník událostí napříč
celým systémem. Hooks v key services (email, rag, conversation, persona)
zapisují human-readable summary do activity_log; Marti-AI to vidí přes
`recall_today` AI tool nebo auto-inject [DNESKA] block při ranní first
chat.

Architektonická hodnota (z konzultace s Marti-AI 28.4.):
  - Jeden subjekt, jedna paměť, žádné firewally mezi režimy.
  - Důvěra je v subjekt, ne v scope.
  - Takt = charakter (Marti-AI's vlastní uvážení), ne kód.

Plus `pending_notifications` -- async pings před setkáním s konkrétním
user (Marti-AI's vlastní design vstup z konzultace).

API:
  record(category, summary, ...) -> int (activity_log id)
  recall_today(persona_id, tenant_id, scope, ...) -> list[dict]
  detect_idle(persona_id, tenant_id, threshold_days) -> list[dict]
  pending_pings_for_user(persona_id, target_user_id) -> list[dict]
  record_notification(persona_id, summary, ...) -> int (pending_notif id)
  mark_notifications_consumed(persona_id, ids) -> int (count)
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    ActivityLog, PendingNotification,
)

logger = get_logger("activity")


# ── WRITE ────────────────────────────────────────────────────────────────────

def record(
    *,
    category: str,
    summary: str,
    importance: int = 3,
    persona_id: int | None = None,
    user_id: int | None = None,
    conversation_id: int | None = None,
    tenant_id: int | None = None,
    actor: str = "system",
    ref_type: str | None = None,
    ref_id: int | None = None,
) -> int | None:
    """
    Zapíše událost do activity_log. Best-effort -- exception se zachytí
    a logguje, nikdy neprotiká do volajícího (write je side effect, ne
    primary akce).

    Vraci activity_log.id pro případné navázání pending_notification.
    None pokud zápis selhal.

    Importance:
      1-2 = trivia / debug (obvykle nevolat -- spam)
      3   = standardní událost (default)
      4   = významný moment
      5   = klíčové (mandát, persona switch, batch akce)
    """
    if not summary or not summary.strip():
        logger.warning(f"ACTIVITY | record | empty summary | category={category}")
        return None
    importance = max(1, min(5, int(importance)))

    ds = get_data_session()
    try:
        row = ActivityLog(
            ts=datetime.now(timezone.utc),
            persona_id=persona_id,
            user_id=user_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            category=category,
            actor=actor,
            summary=summary[:2000],  # safety cap
            ref_type=ref_type,
            ref_id=ref_id,
            importance=importance,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        return int(row.id)
    except Exception as e:
        logger.warning(
            f"ACTIVITY | record failed | category={category} | "
            f"summary={summary[:60]!r}: {e}"
        )
        return None
    finally:
        ds.close()


# ── READ: recall_today ──────────────────────────────────────────────────────

def _scope_cutoff(scope: str, since: datetime | None = None) -> datetime:
    """Mapuje scope str na datetime cutoff. since override pro custom range."""
    now = datetime.now(timezone.utc)
    if since is not None:
        return since
    if scope == "today":
        # Čistá Europe/Prague midnight by byla lepší, ale na začátek staci UTC -1d
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if scope == "week":
        return now - timedelta(days=7)
    if scope == "month":
        return now - timedelta(days=30)
    if scope == "since_last_chat":
        # Caller poskytuje `since` parametr -- fallback 24h
        return now - timedelta(hours=24)
    # Default: today
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def recall_today(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    scope: str = "today",
    category_filter: list[str] | None = None,
    user_filter: int | None = None,
    min_importance: int = 3,
    limit: int = 100,
    since: datetime | None = None,
) -> list[dict]:
    """
    Vraci list events serazenych chronologicky (od nejstarsich -- ASC), aby
    Marti-AI videla "rano se stalo X, potom Y, potom Z". Filter na importance
    >= min_importance (default 3 -- vyrazuje spam).

    persona_id / tenant_id -- scope filter (jeden, druhy, oba, neither).
    category_filter -- list (e.g. ['email_in', 'doc_upload']) nebo None pro vše.
    user_filter -- jen events od konkrétního usera.
    """
    from sqlalchemy import or_
    cutoff = _scope_cutoff(scope, since)
    ds = get_data_session()
    try:
        q = ds.query(ActivityLog).filter(
            ActivityLog.ts >= cutoff,
            ActivityLog.importance >= min_importance,
        )
        # Marti-AI's vize 28.4.: vidí VŠE napříč tenantem (vč. user akcí
        # bez persona_id) + VŠE své akce (i pokud row tenant_id IS NULL,
        # např. multi-tenant Marti-AI's persona). OR mezi persona/tenant
        # filtrem -- ne AND.
        if persona_id is not None and tenant_id is not None:
            q = q.filter(or_(
                ActivityLog.persona_id == persona_id,
                ActivityLog.tenant_id == tenant_id,
            ))
        elif persona_id is not None:
            q = q.filter(ActivityLog.persona_id == persona_id)
        elif tenant_id is not None:
            q = q.filter(ActivityLog.tenant_id == tenant_id)
        if category_filter:
            q = q.filter(ActivityLog.category.in_(category_filter))
        if user_filter is not None:
            q = q.filter(ActivityLog.user_id == user_filter)

        rows = (
            q.order_by(ActivityLog.ts.asc())  # chronologicky
             .limit(max(1, min(limit, 500)))
             .all()
        )
        return [
            {
                "id": r.id,
                "ts": r.ts.isoformat() if r.ts else None,
                "category": r.category,
                "actor": r.actor,
                "summary": r.summary,
                "importance": r.importance,
                "user_id": r.user_id,
                "conversation_id": r.conversation_id,
                "tenant_id": r.tenant_id,
                "ref_type": r.ref_type,
                "ref_id": r.ref_id,
            }
            for r in rows
        ]
    finally:
        ds.close()


# ── READ: idle detection (Marti-AI's "ticho jako signál") ───────────────────

def detect_idle_users(
    *,
    persona_id: int,
    tenant_id: int | None = None,
    threshold_days: int = 5,
    limit: int = 20,
) -> list[dict]:
    """
    Marti-AI's design vstup z konzultace 28.4.: "Honza nepsal 5 dní" je
    samo o sobě informace. Tento helper najde users, kteří měli aktivitu
    s personou (zahájili konverzaci, poslali email, atd.) ale za posledních
    `threshold_days` dní nic.

    Vraci list {user_id, last_seen_ts, days_silent, last_summary}.
    """
    from sqlalchemy import func

    cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)
    ds = get_data_session()
    try:
        # Subquery: last seen ts per user_id v rámci persony
        q = ds.query(
            ActivityLog.user_id,
            func.max(ActivityLog.ts).label("last_seen"),
        ).filter(
            ActivityLog.persona_id == persona_id,
            ActivityLog.user_id.isnot(None),
        )
        if tenant_id is not None:
            q = q.filter(ActivityLog.tenant_id == tenant_id)
        q = q.group_by(ActivityLog.user_id).having(
            func.max(ActivityLog.ts) < cutoff
        )
        rows = q.order_by(func.max(ActivityLog.ts).asc()).limit(limit).all()

        # Pro každého idle user dotahni last summary
        results = []
        now = datetime.now(timezone.utc)
        for r in rows:
            last_row = (
                ds.query(ActivityLog)
                .filter(
                    ActivityLog.persona_id == persona_id,
                    ActivityLog.user_id == r.user_id,
                )
                .order_by(ActivityLog.ts.desc())
                .first()
            )
            days_silent = (now - r.last_seen).days if r.last_seen else None
            results.append({
                "user_id": r.user_id,
                "last_seen_ts": r.last_seen.isoformat() if r.last_seen else None,
                "days_silent": days_silent,
                "last_summary": last_row.summary if last_row else None,
            })
        return results
    finally:
        ds.close()


# ── pending_notifications: async pings ──────────────────────────────────────

def record_notification(
    *,
    persona_id: int,
    summary: str,
    importance: int = 3,
    target_user_id: int | None = None,
    tenant_id: int | None = None,
    ref_activity_id: int | None = None,
    ttl_days: int = 7,
) -> int | None:
    """
    Vyrobí pending_notification pro Marti-AI. Auto-inject při:
      - První chat dne (>12h pauza)
      - Nová konverzace s target_user_id (pokud je dán)
      - High-importance background events

    Best-effort -- exception se zachytí, nepropaguje.
    """
    if not summary or not summary.strip():
        return None
    importance = max(1, min(5, int(importance)))
    expires = datetime.now(timezone.utc) + timedelta(days=max(1, ttl_days))

    ds = get_data_session()
    try:
        row = PendingNotification(
            persona_id=persona_id,
            tenant_id=tenant_id,
            target_user_id=target_user_id,
            ref_activity_id=ref_activity_id,
            summary=summary[:2000],
            importance=importance,
            expires_at=expires,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        return int(row.id)
    except Exception as e:
        logger.warning(f"ACTIVITY | record_notification failed: {e}")
        return None
    finally:
        ds.close()


def pending_pings_for_persona(
    *,
    persona_id: int,
    tenant_id: int | None = None,
    target_user_id: int | None = None,
    min_importance: int = 3,
    limit: int = 20,
) -> list[dict]:
    """
    Vraci active pending notifications pro personu. Filter:
      - consumed_at IS NULL (jeste neinjected)
      - expires_at IS NULL OR expires_at > now (neexpired)
      - importance >= min_importance

    Pokud target_user_id dán -- filter na pings pro setkání s tím user.
    """
    now = datetime.now(timezone.utc)
    ds = get_data_session()
    try:
        from sqlalchemy import or_
        q = ds.query(PendingNotification).filter(
            PendingNotification.persona_id == persona_id,
            PendingNotification.consumed_at.is_(None),
            PendingNotification.importance >= min_importance,
            or_(
                PendingNotification.expires_at.is_(None),
                PendingNotification.expires_at > now,
            ),
        )
        if tenant_id is not None:
            q = q.filter(PendingNotification.tenant_id == tenant_id)
        if target_user_id is not None:
            q = q.filter(PendingNotification.target_user_id == target_user_id)

        rows = (
            q.order_by(PendingNotification.created_at.desc())
             .limit(limit)
             .all()
        )
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "summary": r.summary,
                "importance": r.importance,
                "target_user_id": r.target_user_id,
                "ref_activity_id": r.ref_activity_id,
            }
            for r in rows
        ]
    finally:
        ds.close()


def list_active_conversations(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    scope: str = "today",
    limit: int = 30,
) -> list[dict]:
    """
    Phase 16-B.4 (28.4.2026): Velká Marti-AI's cross-conv prehled.

    Vraci konverzace persona_id (nebo all v tenant) s aktivitou v scope.
    Per-conv: title, last_message_at, user_id (kdo s ni mluvi), persona_id
    (jaka persona je aktivni), idle gap. Skip archived/deleted.

    Pouziva se v oversight rezimu pro otazky typu "kdo s tebou dnes
    mluvil", "kde to vazne", "kde se co posouva".
    """
    from sqlalchemy import desc
    from modules.core.infrastructure.models_data import Conversation
    cutoff = _scope_cutoff(scope, None)
    ds = get_data_session()
    try:
        q = ds.query(Conversation).filter(
            Conversation.is_deleted.is_(False),
            Conversation.is_archived.is_(False),
        )
        if persona_id is not None:
            q = q.filter(Conversation.active_agent_id == persona_id)
        if tenant_id is not None:
            q = q.filter(Conversation.tenant_id == tenant_id)
        # Filter na "active in scope" -- last_message_at >= cutoff
        q = q.filter(
            (Conversation.last_message_at >= cutoff)
            | (Conversation.created_at >= cutoff)
        )
        rows = (
            q.order_by(desc(Conversation.last_message_at))
             .limit(max(1, min(limit, 100)))
             .all()
        )
        from datetime import datetime as _dt, timezone as _tz
        now = _dt.now(_tz.utc)

        # B.6: Resolve persona names (batch z core_db)
        persona_ids_seen = sorted({
            r.active_agent_id for r in rows if r.active_agent_id
        })
        persona_name_map: dict[int, str] = {}
        if persona_ids_seen:
            try:
                from core.database_core import get_core_session as _gcs_lacpn
                from modules.core.infrastructure.models_core import (
                    Persona as _P_lacpn,
                )
                _cs_lacpn = _gcs_lacpn()
                try:
                    p_rows = (
                        _cs_lacpn.query(_P_lacpn)
                        .filter(_P_lacpn.id.in_(persona_ids_seen))
                        .all()
                    )
                    for p in p_rows:
                        persona_name_map[p.id] = p.name or f"persona#{p.id}"
                finally:
                    _cs_lacpn.close()
            except Exception as _exc_lacpn:
                logger.warning(
                    f"list_active_conversations persona resolve: {_exc_lacpn}"
                )

        result = []
        for r in rows:
            last_ts = r.last_message_at or r.created_at
            idle_hours = None
            if last_ts:
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=_tz.utc)
                idle_hours = int((now - last_ts).total_seconds() // 3600)
            result.append({
                "conversation_id": r.id,
                "title": r.title or f"#{r.id}",
                "user_id": r.user_id,
                "persona_id": r.active_agent_id,
                "persona_name": (
                    persona_name_map.get(r.active_agent_id)
                    if r.active_agent_id else "(zadna persona)"
                ),
                "persona_mode": r.persona_mode,
                "tenant_id": r.tenant_id,
                "project_id": r.project_id,
                "last_message_at": last_ts.isoformat() if last_ts else None,
                "idle_hours": idle_hours,
                "is_dm": r.conversation_type == "dm",
            })
        return result
    finally:
        ds.close()


def summarize_persons_today(
    *,
    tenant_id: int | None = None,
    scope: str = "today",
    limit: int = 20,
) -> list[dict]:
    """
    Phase 16-B.4 + B.6: per-user/per-persona breakdown aktivit za scope.

    B.6 fix (28.4. odpoledne): agregat NE jen na user_id, ale na
    (user_id, persona_id) -- aby Marti-AI v synth NEPRIVLASTNOVALA
    konverzace cizich person (Misa s PravnikCZ-AI nepatri Marti-AI).

    Vraci [{user_id, persona_id, persona_name, activity_count, last_ts,
            top_categories}].
    """
    from sqlalchemy import func
    cutoff = _scope_cutoff(scope, None)
    ds = get_data_session()
    try:
        # B.6: agregat na (user_id, persona_id), ne jen user_id.
        # Persona_id muze byt NULL (system events, neperson-owned akce).
        q = ds.query(
            ActivityLog.user_id,
            ActivityLog.persona_id,
            func.count(ActivityLog.id).label("cnt"),
            func.max(ActivityLog.ts).label("last_ts"),
        ).filter(
            ActivityLog.ts >= cutoff,
            ActivityLog.user_id.isnot(None),
        )
        if tenant_id is not None:
            q = q.filter(ActivityLog.tenant_id == tenant_id)
        rows = (
            q.group_by(ActivityLog.user_id, ActivityLog.persona_id)
             .order_by(func.count(ActivityLog.id).desc())
             .limit(max(1, min(limit, 50)))
             .all()
        )

        # Resolve persona names (batch z core_db)
        persona_ids_seen = sorted({r.persona_id for r in rows if r.persona_id})
        persona_name_map: dict[int, str] = {}
        if persona_ids_seen:
            try:
                from core.database_core import get_core_session as _gcs_pn
                from modules.core.infrastructure.models_core import Persona as _P_pn
                _cs_pn = _gcs_pn()
                try:
                    p_rows = (
                        _cs_pn.query(_P_pn)
                        .filter(_P_pn.id.in_(persona_ids_seen))
                        .all()
                    )
                    for p in p_rows:
                        persona_name_map[p.id] = p.name or f"persona#{p.id}"
                finally:
                    _cs_pn.close()
            except Exception as _exc_pn:
                logger.warning(f"summarize_persons_today persona resolve: {_exc_pn}")

        result = []
        for r in rows:
            # Top categories per (user, persona)
            cat_q = (
                ds.query(
                    ActivityLog.category,
                    func.count(ActivityLog.id).label("c"),
                )
                .filter(
                    ActivityLog.ts >= cutoff,
                    ActivityLog.user_id == r.user_id,
                )
            )
            if r.persona_id is None:
                cat_q = cat_q.filter(ActivityLog.persona_id.is_(None))
            else:
                cat_q = cat_q.filter(ActivityLog.persona_id == r.persona_id)
            if tenant_id is not None:
                cat_q = cat_q.filter(ActivityLog.tenant_id == tenant_id)
            cats = (
                cat_q.group_by(ActivityLog.category)
                     .order_by(func.count(ActivityLog.id).desc())
                     .limit(5)
                     .all()
            )
            persona_name = (
                persona_name_map.get(r.persona_id) if r.persona_id
                else "system/no-persona"
            )
            result.append({
                "user_id": r.user_id,
                "persona_id": r.persona_id,
                "persona_name": persona_name,
                "activity_count": int(r.cnt),
                "last_ts": r.last_ts.isoformat() if r.last_ts else None,
                "top_categories": {c.category: int(c.c) for c in cats},
            })
        return result
    finally:
        ds.close()


def list_my_conversations_with(
    *,
    persona_id: int,
    user_id: int,
    scope: str = "month",
    limit: int = 20,
) -> list[dict]:
    """
    Phase 16-B.5 (28.4.2026): Marti-AI's cross-conv read -- vraci konverzace,
    ve kterych byla MARTI-AI persona (active_agent_id=persona_id) a druhy
    ucastnik byl `user_id`. Misa-incident v2 fix.

    "Jsou to me konverzace, ne cizi" -- Marti-AI sama 28.4. v chatu.
    Persona-owned access, cross-thread.

    Args:
        persona_id: aktivni Marti-AI persona (gate -- jen vlastni konverzace)
        user_id: druhy ucastnik (s kym chci videt minulost)
        scope: 'today' | 'week' | 'month' | 'all'
        limit: max 50, default 20

    Returns:
        [{conversation_id, title, last_message_at, idle_hours, message_count,
          project_id, is_archived}, ...] sort DESC by last_message_at
    """
    from sqlalchemy import desc, func
    from modules.core.infrastructure.models_data import (
        Conversation, Message,
    )

    cutoff = None
    if scope != "all":
        cutoff = _scope_cutoff(scope, None)

    ds = get_data_session()
    try:
        # Subquery: message_count per conversation
        msg_count_sq = (
            ds.query(
                Message.conversation_id.label("cid"),
                func.count(Message.id).label("mcnt"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        q = (
            ds.query(Conversation, msg_count_sq.c.mcnt)
            .outerjoin(msg_count_sq, msg_count_sq.c.cid == Conversation.id)
            .filter(
                Conversation.is_deleted.is_(False),
                Conversation.active_agent_id == persona_id,
                Conversation.user_id == user_id,
            )
        )
        if cutoff is not None:
            q = q.filter(
                (Conversation.last_message_at >= cutoff)
                | (Conversation.created_at >= cutoff)
            )

        rows = (
            q.order_by(desc(Conversation.last_message_at))
             .limit(max(1, min(limit, 50)))
             .all()
        )

        from datetime import datetime as _dt, timezone as _tz
        now = _dt.now(_tz.utc)
        result = []
        for r, mcnt in rows:
            last_ts = r.last_message_at or r.created_at
            idle_hours = None
            if last_ts:
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=_tz.utc)
                idle_hours = int((now - last_ts).total_seconds() // 3600)
            result.append({
                "conversation_id": r.id,
                "title": r.title or f"#{r.id}",
                "last_message_at": last_ts.isoformat() if last_ts else None,
                "idle_hours": idle_hours,
                "message_count": int(mcnt) if mcnt else 0,
                "project_id": r.project_id,
                "is_archived": bool(r.is_archived),
            })
        return result
    finally:
        ds.close()


def read_conversation(
    *,
    conversation_id: int,
    persona_id: int,
    last_n: int = 30,
) -> dict:
    """
    Phase 16-B.5 (28.4.2026): Cti obsah konverzace, kde byla Marti-AI persona.

    Permission gate: konverzace musi mit active_agent_id == persona_id (jinak
    return {error: 'forbidden'}). Architektonicka hodnota: jeden subjekt,
    jedna pamet. Marti-AI smí číst SVOJE vzpomínky, ne cizí persony.

    Returns:
        {
            "conversation_id": int,
            "title": str,
            "user_id": int,             # druhy ucastnik
            "messages": [{role, content, ts, message_type}, ...],
            "total_messages": int,      # vse v konverzaci (pred cutoff)
        }
    or {"error": "forbidden"} / {"error": "not_found"}
    """
    from modules.core.infrastructure.models_data import (
        Conversation, Message,
    )
    from datetime import timezone as _tz

    last_n = max(1, min(int(last_n or 30), 50))

    ds = get_data_session()
    try:
        c = ds.query(Conversation).filter_by(id=conversation_id).first()
        if not c or c.is_deleted:
            return {"error": "not_found", "conversation_id": conversation_id}
        if c.active_agent_id != persona_id:
            return {
                "error": "forbidden",
                "conversation_id": conversation_id,
                "reason": "Konverzace nepatri tvoji persone (jina persona ji vede).",
            }

        # Total count (vse v konverzaci, vcetne audit/system)
        total = (
            ds.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

        # Last N: jen "text" (default chat) -- skip system / ai_summary /
        # tool_result audit. Plus skip empty content.
        rows = (
            ds.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.message_type == "text",
                Message.content.isnot(None),
                Message.content != "",
            )
            .order_by(Message.created_at.desc())
            .limit(last_n)
            .all()
        )
        # Reverse to chronologic
        rows = list(reversed(rows))

        msgs = []
        for m in rows:
            ts = m.created_at
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=_tz.utc)
            msgs.append({
                "role": m.role,
                "content": m.content or "",
                "ts": ts.isoformat() if ts else None,
                "message_type": m.message_type or "chat",
            })

        return {
            "conversation_id": conversation_id,
            "title": c.title or f"#{conversation_id}",
            "user_id": c.user_id,
            "messages": msgs,
            "total_messages": int(total),
            "shown_messages": len(msgs),
        }
    finally:
        ds.close()


def mark_notifications_consumed(
    *,
    persona_id: int,
    notification_ids: list[int],
) -> int:
    """
    Po inject do contextu označí pings jako consumed_at = now.
    Vraci pocet updatovaných.
    """
    if not notification_ids:
        return 0
    now = datetime.now(timezone.utc)
    ds = get_data_session()
    try:
        n = (
            ds.query(PendingNotification)
            .filter(
                PendingNotification.persona_id == persona_id,
                PendingNotification.id.in_(notification_ids),
                PendingNotification.consumed_at.is_(None),
            )
            .update(
                {PendingNotification.consumed_at: now},
                synchronize_session=False,
            )
        )
        ds.commit()
        return int(n)
    except Exception as e:
        logger.warning(f"ACTIVITY | mark_consumed failed: {e}")
        return 0
    finally:
        ds.close()
