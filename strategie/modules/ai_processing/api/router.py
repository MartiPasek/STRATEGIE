from fastapi import APIRouter, HTTPException

from core.common import ProcessingError
from core.logging import get_logger
from modules.ai_processing.api.schemas import AnalyseRequest, AnalyseResponse
from modules.ai_processing.application.schemas import AnalysisInput
from modules.ai_processing.application.service import analyse_text

logger = get_logger("ai_processing.api")

router = APIRouter(prefix="/api/v1", tags=["ai_processing"])

# Obecná zpráva pro klienta — detail chyby se neposílá ven
_PROCESSING_ERROR_MESSAGE = (
    "The analysis could not be completed. Please try again later."
)


@router.post("/analyse", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest) -> AnalyseResponse:
    """
    Analyse input text and return structured output.

    - **summary**: brief summary of the text
    - **action_items**: concrete tasks or next steps
    - **persons**: people or organizations mentioned
    - **recommendations**: suggestions based on the content
    """
    try:
        result = analyse_text(AnalysisInput(text=request.text))
        return AnalyseResponse(**result.model_dump())
    except ProcessingError as e:
        logger.error(f"Processing error (not exposed to client): {e}")
        raise HTTPException(status_code=503, detail=_PROCESSING_ERROR_MESSAGE)
    except Exception:
        logger.exception("Unexpected error in /analyse endpoint.")
        raise HTTPException(status_code=500, detail="Internal server error.")
