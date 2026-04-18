from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.conversation.api.schemas import ChatRequest, ChatResponse, LastConversationResponse
from modules.conversation.application.service import chat
from modules.conversation.infrastructure.repository import get_last_conversation

logger = get_logger("conversation.api")

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    try:
        user_id_str = req.cookies.get("user_id")
        user_id = int(user_id_str) if user_id_str else None

        conversation_id, reply, switch_to = chat(
            conversation_id=request.conversation_id,
            user_message=request.text,
            user_id=user_id,
        )
        return ChatResponse(
            conversation_id=conversation_id,
            reply=reply,
            switch_to_conversation_id=switch_to,
        )
    except Exception as e:
        logger.exception(f"Chat failed: {e}")
        raise HTTPException(status_code=503, detail="Chat service unavailable.")


@router.get("/last", response_model=LastConversationResponse | None)
def get_last(req: Request):
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        return None
    user_id = int(user_id_str)
    return get_last_conversation(user_id)
