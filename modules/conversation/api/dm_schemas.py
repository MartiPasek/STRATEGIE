"""Pydantic schémata pro DM endpointy."""
from datetime import datetime

from pydantic import BaseModel, Field


class StartDMRequest(BaseModel):
    target_user_id: int


class StartDMResponse(BaseModel):
    conversation_id: int
    created: bool


class UserLite(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    status: str | None = None


class DMListItem(BaseModel):
    conversation_id: int
    counterparty: UserLite | None = None
    last_message_id: int | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    is_archived: bool = False
    is_muted: bool = False


class DMDetailResponse(BaseModel):
    conversation_id: int
    conversation_type: str
    counterparty: UserLite | None = None
    created_at: datetime | None = None
    last_message_at: datetime | None = None
    last_message_id: int | None = None


class DMMessage(BaseModel):
    id: int
    role: str
    content: str
    author_type: str
    author_user_id: int | None = None
    message_type: str
    created_at: datetime


class DMMessagesResponse(BaseModel):
    conversation_id: int
    messages: list[DMMessage]


class SendDMRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class SendDMResponse(BaseModel):
    message_id: int
    conversation_id: int


class MarkReadRequest(BaseModel):
    last_read_message_id: int


class UserSearchResponse(BaseModel):
    results: list[UserLite]
