class StrategieError(Exception):
    """Base exception for STRATEGIE platform."""
    pass


class ProcessingError(StrategieError):
    """
    Raised when AI processing fails.
    Covers: missing API key, LLM call failure, invalid response, parse error.
    """
    pass


class LLMCallError(ProcessingError):
    """Raised when the LLM API call itself fails (network, auth, timeout)."""
    pass


class LLMParseError(ProcessingError):
    """Raised when LLM response cannot be parsed (invalid JSON, wrong structure)."""
    pass
