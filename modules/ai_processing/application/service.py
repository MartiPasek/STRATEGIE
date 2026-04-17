import json
import re
import time

import anthropic

from core.config import settings
from core.common import ProcessingError, LLMCallError, LLMParseError
from core.logging import get_logger
from modules.ai_processing.application.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    build_analysis_prompt,
)
from modules.ai_processing.application.schemas import AnalysisInput, AnalysisOutput
from modules.audit.application.service import log_analysis

logger = get_logger("ai_processing")

MODEL = "claude-haiku-4-5-20251001"


def _check_api_key() -> None:
    if not settings.anthropic_api_key:
        raise ProcessingError(
            "ANTHROPIC_API_KEY is not set. "
            "Please configure it in your .env file."
        )


def _call_llm(text: str) -> str:
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_analysis_prompt(text)}
            ],
        )
    except Exception as e:
        logger.error(f"LLM_CALL_FAILED | {type(e).__name__}: {e}")
        raise LLMCallError(f"LLM call failed: {type(e).__name__}")

    text_parts = [
        block.text
        for block in message.content
        if hasattr(block, "text") and block.text and block.text.strip()
    ]

    if not text_parts:
        logger.error("LLM_EMPTY_RESPONSE | No text blocks in LLM response.")
        raise LLMCallError("LLM returned an empty response.")

    return "\n".join(text_parts).strip()


def _parse_response(raw: str) -> AnalysisOutput:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"LLM_INVALID_JSON | {e} | Raw (first 300): {raw[:300]}")
        raise LLMParseError("LLM returned an invalid JSON response.")

    try:
        return AnalysisOutput(**data)
    except Exception as e:
        logger.error(f"LLM_INVALID_STRUCTURE | {e} | Data: {data}")
        raise LLMParseError("LLM response does not match expected structure.")


def analyse_text(
    input_data: AnalysisInput,
    user_id: str | None = None,
) -> AnalysisOutput:
    """
    Hlavní orchestrace analýzy textu.
    user_id: volitelný, předává se z dev headeru X-Dev-User-Id.
    """
    _check_api_key()

    start = time.time()

    try:
        raw = _call_llm(input_data.text)
        output = _parse_response(raw)
    except ProcessingError as e:
        duration_ms = int((time.time() - start) * 1000)
        log_analysis(
            input_text=input_data.text,
            output=None,
            model=MODEL,
            duration_ms=duration_ms,
            status="error",
            error=str(e),
            user_id=user_id,
        )
        raise
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        logger.exception("UNEXPECTED_ERROR | analyse_text failed unexpectedly.")
        log_analysis(
            input_text=input_data.text,
            output=None,
            model=MODEL,
            duration_ms=duration_ms,
            status="error",
            error=f"Unexpected: {type(e).__name__}",
            user_id=user_id,
        )
        raise

    duration_ms = int((time.time() - start) * 1000)
    log_analysis(
        input_text=input_data.text,
        output=output.model_dump(),
        model=MODEL,
        duration_ms=duration_ms,
        status="success",
        user_id=user_id,
    )

    return output
