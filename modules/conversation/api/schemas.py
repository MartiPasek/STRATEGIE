from pydantic import BaseModel


class ChatRequest(BaseModel):
    text: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    active_persona: str | None = None
    switch_to_conversation_id: int | None = None
    # Když se v tomto cyklu vytvořilo nové summary, frontend tuto hlášku zobrazí
    # jako banner (např. „⏳ Shrnul jsem 10 starších zpráv"). Jinak None.
    summary_notice: str | None = None
    # Aktuální tenant kontext — frontend tím aktualizuje UI hlavičku.
    # Zachycuje i tenant switch provedený přes chat („přepni do EUROSOFTu").
    tenant_id: int | None = None
    tenant_name: str | None = None
    tenant_code: str | None = None
    # Display jméno usera v aktuálním tenantu (z user_tenant_profiles).
    # Frontend ho používá pro „Marti - EUROSOFT" hlavičkovou pilulku.
    display_name: str | None = None


class HistoryMessage(BaseModel):
    role: str
    content: str


class LastConversationResponse(BaseModel):
    conversation_id: int
    messages: list[HistoryMessage]
    active_persona: str | None = None
