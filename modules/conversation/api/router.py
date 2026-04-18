from fastapi import APIRouter, HTTPException

from core.logging import get_logger
from modules.conversation.api.schemas import ChatRequest, ChatResponse
from modules.conversation.application.service import chat

logger = get_logger("conversation.api")

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Konverzační endpoint.
    Přijme text a volitelně conversation_id.
    Vrátí odpověď a conversation_id (nové nebo stávající).
    """
    try:
        conversation_id, reply = chat(
            conversation_id=request.conversation_id,
            user_message=request.text,
        )
        return ChatResponse(conversation_id=conversation_id, reply=reply)
    except Exception as e:
        logger.exception(f"Chat failed: {e}")
        raise HTTPException(status_code=503, detail="Chat service unavailable.")
