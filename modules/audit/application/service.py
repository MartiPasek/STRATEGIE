from core.logging import get_logger

logger = get_logger("audit")


def log_analysis(
    input_text: str,
    output: dict | None,
    model: str,
    duration_ms: int,
    status: str = "success",
    error: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Zapíše audit záznam analýzy.
    1. Vždy zapíše do logu.
    2. Pokusí se zapsat do DB — selhání nezastaví processing.
    user_id: volitelný, předává se z X-Dev-User-Id headeru.
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

    try:
        from modules.audit.infrastructure.repository import save_audit_log
        save_audit_log(
            entity_type="analysis",
            action="analyse_text",
            status=status,
            model=model,
            duration_ms=duration_ms,
            input_length=len(input_text),
            error=error,
            user_id=user_id,
        )
        logger.info("AUDIT_DB_OK | Record saved to DB")
    except Exception as e:
        logger.error(f"AUDIT_DB_FAILED | Could not write to DB: {e}")
