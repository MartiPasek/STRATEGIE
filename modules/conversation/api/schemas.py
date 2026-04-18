from pydantic import BaseModel


class ChatRequest(BaseModel):
    text: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


class HistoryMessage(BaseModel):
    role: str
    content: str


class LastConversationResponse(BaseModel):
    conversation_id: int
    messages: list[HistoryMessage]
