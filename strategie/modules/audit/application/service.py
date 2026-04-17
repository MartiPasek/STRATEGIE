from core.logging import get_logger

logger = get_logger("audit")


def log_analysis(
    input_text: str,
    output: dict | None,
    model: str,
    duration_ms: int,
    status: str = "success",
    error: str | None = None,
) -> None:
    """
    Zapíše audit záznam analýzy.
    1. Pokusí se zapsat do DB.
    2. Vždy zapíše do logu jako fallback.
    DB selhání nerozbije hlavní processing flow.
    """
    # Vždy logujeme — fallback i potvrzení
    if status == "success":
        logger.info(
            f"AUDIT | analysis | status=success"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | action_items={len(output.get('action_items', [])) if output else 0}"
            f" | persons={len(output.get('persons', [])) if output else 0}"
        )
    else:
        logger.error(
            f"AUDIT | analysis | status=error"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | error={error or 'unknown'}"
        )

    # Pokusíme se zapsat do DB — selhání je zachyceno, nezastaví processing
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
        )
    except Exception as e:
        logger.error(f"AUDIT_DB_FAILED | Could not write to DB: {e}")
