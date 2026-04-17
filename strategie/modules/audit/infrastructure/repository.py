from datetime import datetime, timezone

from core.database import get_db_session
from modules.audit.infrastructure.models import AuditLog


def save_audit_log(
    entity_type: str,
    action: str,
    status: str,
    model: str,
    duration_ms: int,
    input_length: int,
    error: str | None = None,
) -> None:
    """
    Zapíše audit záznam do DB.
    Jednoduchý přímý zápis — bez abstraktních repository vrstev.
    """
    session = get_db_session()
    try:
        record = AuditLog(
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
