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
