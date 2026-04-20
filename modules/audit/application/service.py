"""
Audit service — zapisuje do css_db (AuditLog model).
"""
from core.logging import get_logger

logger = get_logger("audit")


def log_analysis(
    input_text: str,
    output: dict | None,
    model: str,
    duration_ms: int,
    status: str = "success",
    error: str | None = None,
    user_id: int | None = None,
) -> None:
    """Zapíše audit záznam analýzy do css_db."""
    if status == "success":
        logger.info(
            f"AUDIT | analysis | status=success"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | user_id={user_id or 'anonymous'}"
        )
    else:
        logger.error(
            f"AUDIT | analysis | status=error"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | error={error or 'unknown'}"
            f" | user_id={user_id or 'anonymous'}"
        )

    try:
        _save_to_db(
            entity_type="analysis",
            action="analyse_text",
            status=status,
            model=model,
            duration_ms=duration_ms,
            input_length=len(input_text),
            error=error,
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"AUDIT_DB_FAILED | {e}")


def log_action(
    action: str,
    status: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    error: str | None = None,
) -> None:
    """Zapíše audit záznam akce (send_email, find_user apod.)."""
    logger.info(f"AUDIT | action={action} | status={status} | user_id={user_id or 'anonymous'}")
    try:
        _save_to_db(
            entity_type="action",
            action=action,
            status=status,
            user_id=user_id,
            tenant_id=tenant_id,
            error=error,
        )
    except Exception as e:
        logger.error(f"AUDIT_DB_FAILED | {e}")


def _save_to_db(
    entity_type: str,
    action: str,
    status: str,
    model: str | None = None,
    duration_ms: int | None = None,
    input_length: int | None = None,
    error: str | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
) -> None:
    """Interní funkce — zapíše záznam do css_db."""
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import AuditLog

    session = get_core_session()
    try:
        record = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            action=action,
            status=status,
            model=model,
            duration_ms=duration_ms,
            input_length=input_length,
            error=error,
        )
        session.add(record)
        session.commit()
    finally:
        session.close()


# ── ROZSIRENE EVENT LOGGING (security + operations) ───────────────────────
# Pridano pri zavedeni audit_log extensionu (migrace f1b2c3d4e5f6).
# Stare log_analysis / log_action zustavaji pro backward compat.

# Mapping action prefix -> entity_type pro auto-categorization
_ACTION_PREFIX_TO_ENTITY_TYPE = {
    "login_": "auth",
    "logout": "auth",
    "password_": "auth",
    "forgot_password": "auth",
    "invite_": "invite",
    "accept_invitation": "invite",
    "document_": "rag",
    "tenant_switch": "auth",
    "persona_switch": "auth",
    "project_switch": "auth",
}


def _entity_type_for(action: str) -> str:
    for prefix, et in _ACTION_PREFIX_TO_ENTITY_TYPE.items():
        if action.startswith(prefix):
            return et
    return "action"


def log_event(
    *,
    action: str,
    status: str = "success",
    user_id: int | None = None,
    tenant_id: int | None = None,
    entity_id: int | None = None,
    entity_type: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    error: str | None = None,
    extra_metadata: dict | None = None,
    duration_ms: int | None = None,
    model: str | None = None,
    input_length: int | None = None,
) -> None:
    """
    Comprehensive audit event logger -- security a operation events.
    Best-effort: pri DB pad logujeme do app loggeru, neshazujeme volajiciho.

    Pouziti:
        log_event(action="login_success", user_id=42, ip_address=req.client.host)
        log_event(action="login_failed", status="error", error="bad_password",
                  extra_metadata={"email": "test@x.cz"}, ip_address=...)
        log_event(action="document_uploaded", user_id=42, tenant_id=1,
                  entity_id=doc.id, extra_metadata={"filename": "x.pdf", "size": 12345})
    """
    from datetime import datetime, timezone
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import AuditLog

    et = entity_type or _entity_type_for(action)
    if user_agent and len(user_agent) > 500:
        user_agent = user_agent[:497] + "..."

    session = get_core_session()
    try:
        entry = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            entity_type=et,
            action=action,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            entity_id=entity_id,
            extra_metadata=extra_metadata,
            error=error,
            duration_ms=duration_ms,
            model=model,
            input_length=input_length,
            created_at=datetime.now(timezone.utc),
        )
        session.add(entry)
        session.commit()
        logger.info(
            f"AUDIT | {action} | status={status} | "
            f"user={user_id or '-'} | tenant={tenant_id or '-'}"
        )
    except Exception as e:
        logger.warning(
            f"AUDIT | log_event failed | action={action} | status={status} | error={e}"
        )
        try:
            session.rollback()
        except Exception:
            pass
    finally:
        try:
            session.close()
        except Exception:
            pass


def list_recent_events(
    limit: int = 100,
    *,
    action_filter: str | None = None,
    user_id_filter: int | None = None,
    tenant_id_filter: int | None = None,
    entity_type_filter: str | None = None,
) -> list[dict]:
    """Vrati posledni audit events pro admin UI / API."""
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import AuditLog

    session = get_core_session()
    try:
        q = session.query(AuditLog).order_by(AuditLog.id.desc())
        if action_filter:
            q = q.filter(AuditLog.action == action_filter)
        if user_id_filter is not None:
            q = q.filter(AuditLog.user_id == user_id_filter)
        if tenant_id_filter is not None:
            q = q.filter(AuditLog.tenant_id == tenant_id_filter)
        if entity_type_filter:
            q = q.filter(AuditLog.entity_type == entity_type_filter)
        rows = q.limit(min(limit, 500)).all()
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "user_id": r.user_id,
                "tenant_id": r.tenant_id,
                "entity_type": r.entity_type,
                "action": r.action,
                "status": r.status,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "entity_id": r.entity_id,
                "extra_metadata": r.extra_metadata,
                "error": r.error,
                "duration_ms": r.duration_ms,
            }
            for r in rows
        ]
    finally:
        session.close()
