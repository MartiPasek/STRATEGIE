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
