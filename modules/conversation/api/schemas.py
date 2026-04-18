from pydantic import BaseModel


class ChatRequest(BaseModel):
    text: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
