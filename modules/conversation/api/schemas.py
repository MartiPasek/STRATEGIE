from pydantic import BaseModel


class ChatRequest(BaseModel):
    text: str
    conversation_id: int | None = None
    # Pokud user v UI vybral personu PŘED vznikem konverzace (empty chat stav),
    # frontend ji pošle sem. Backend ji použije jako active_agent_id nově
    # vytvořené konverzace (přepíše default persona fallback).
    preferred_persona_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    active_persona: str | None = None
    switch_to_conversation_id: int | None = None
    # Když user vybere "Otevři DM" v selekci po list_users, backend vrátí
    # cíl user_id — frontend přepne do DM módu a otevře vlákno s tím userem.
    switch_to_dm_user_id: int | None = None
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
    # Aktuální projekt po této zprávě (zachycuje i project switch v chatu
    # přes „přepni do projektu X" / „bez projektu"). Frontend porovná s
    # currentUser.project_id a pokud se liší, refreshne /me.
    project_id: int | None = None
    project_name: str | None = None


class HistoryMessage(BaseModel):
    # Faze 9.1c: message_id pro Dev View (lupy -> /messages/{id}/llm-calls).
    # Frontend ho uklada do msg.dataset.messageId a pouziva pri kliku na lupu.
    id: int | None = None
    role: str
    content: str
    # message_type: 'text' (běžné) | 'system' (systémové markery jako tenant switch).
    # Frontend podle toho rozhodne renderování (left-aligned, label 'STRATEGIE').
    message_type: str = "text"
    # Persona, ktera zpravu autorsky napsala. Pro role=assistant uzitecne
    # pro zobrazeni jmena persony v bublino ('Marti-AI' / 'Honza-AI') --
    # zejmena pri multi-persona konverzaci, kde aktualni persona nemusi
    # souhlasit s autorem historicke zpravy.
    agent_id: int | None = None
    persona_name: str | None = None
    # ISO 8601 timestamp kdy zprava vznikla. Frontend ho formatuje pro UI
    # (HH:MM pro dnes, '20.4 14:32' pro starsi, pro rychly orientaci v case).
    created_at: str | None = None
    # Faze 9.2b: Dev View -- seznam VSECH LLM volani pro tuto zpravu.
    # [{id, kind, latency_ms}, ...] ORDER BY id ASC. UI vyrobi lupu
    # za kazdy call -- tool loop s N composer rounds znamena N lup.
    # Prazdny list = neni zapsan zadny trace (starsi zprava pred 9.1a).
    llm_calls: list[dict] = []


class LastConversationResponse(BaseModel):
    conversation_id: int
    messages: list[HistoryMessage]
    active_persona: str | None = None
    # Frontend potřebuje vědět, jestli konverzace je archivovaná —
    # pokud ano, před odesláním nové zprávy se uživatele zeptá,
    # jestli má konverzaci nejdřív vrátit z archivu.
    is_archived: bool = False
    # Role aktuálního usera v této konverzaci (z pohledu přístupu):
    #   owner        — vlastník, může vše
    #   shared_read  — sdílené, jen čtení (frontend disable send)
    #   shared_write — sdílené, může psát (zatím neimplementováno)
    my_role: str | None = None
    # Pokud je user shared viewer (ne owner), tady je jméno vlastníka — pro
    # banner "Sdíleno od X". Null pokud own.
    owner_name: str | None = None
    # Počet sdílení této konverzace (pro owner banner "Sdíleno s 2 lidmi").
    shares_count: int = 0


class ConversationListItem(BaseModel):
    """Jedna položka v sidebaru se seznamem konverzací."""
    id: int
    title: str
    tenant_id: int | None = None
    last_message_at: str | None = None  # ISO 8601 string
    message_count: int
    shares_count: int = 0   # >0 = moje, ale sdileno s nekym (ikonka v listu)


class ShareInfo(BaseModel):
    id: int
    conversation_id: int
    shared_with_user_id: int
    shared_with_name: str
    access_level: str
    created_at: str


class AddShareRequest(BaseModel):
    user_id: int
    access_level: str = "read"   # MVP: jen read


class SharedWithMeItem(BaseModel):
    share_id: int
    conversation_id: int
    title: str
    owner_user_id: int
    owner_name: str
    access_level: str
    shared_at: str
    last_message_at: str | None = None
