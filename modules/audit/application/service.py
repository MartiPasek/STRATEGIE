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
    V1: do logu jako text. V2: persistence do DB (rozhraní zůstane stejné).

    status: "success" | "error"
    error: chybová zpráva při status="error"
    """
    if status == "success" and output is not None:
        message = (
            f"AUDIT | analysis | status=success"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | action_items={len(output.get('action_items', []))}"
            f" | persons={len(output.get('persons', []))}"
            f" | has_summary={bool(output.get('summary'))}"
        )
        logger.info(message)
    else:
        message = (
            f"AUDIT | analysis | status=error"
            f" | model={model}"
            f" | duration_ms={duration_ms}"
            f" | input_length={len(input_text)}"
            f" | error={error or 'unknown'}"
        )
        logger.error(message)
