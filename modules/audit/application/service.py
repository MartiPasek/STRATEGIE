"""
Audit service — přepojeno na css_db.
AuditLog model je v modules/core/infrastructure/models_core.py.
Pozn: AuditLog bude přidán do models_core v další iteraci.
Pro teď logujeme do souboru.
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
    """
    Zapíše audit záznam analýzy.
    TODO: přesunout AuditLog do css_db a zapsat do DB.
    """
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
