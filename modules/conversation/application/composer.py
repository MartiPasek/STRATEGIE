from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import SystemPrompt, Persona
from modules.core.infrastructure.models_data import Message, ConversationSummary

logger = get_logger("conversation.composer")

DEFAULT_SYSTEM_PROMPT = "Jsi neutrální asistent. Odpovídej věcně a srozumitelně."
MAX_TOKENS = 6000
CHARS_PER_TOKEN = 4  # přibližná aproximace


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _get_system_prompt() -> str:
    """Načte default system prompt z css_db."""
    session = get_core_session()
    try:
        prompt = session.query(SystemPrompt).first()
        return prompt.content if prompt else DEFAULT_SYSTEM_PROMPT
    finally:
        session.close()


def _get_persona_prompt() -> str | None:
    """Načte default personu z css_db."""
    session = get_core_session()
    try:
        persona = session.query(Persona).filter_by(is_default=True).first()
        return persona.system_prompt if persona else None
    finally:
        session.close()


def _get_latest_summary(conversation_id: int) -> ConversationSummary | None:
    """Načte nejnovější summary pro konverzaci."""
    session = get_data_session()
    try:
        return (
            session.query(ConversationSummary)
            .filter_by(conversation_id=conversation_id)
            .order_by(ConversationSummary.id.desc())
            .first()
        )
    finally:
        session.close()


def _get_messages(conversation_id: int, after_id: int | None = None) -> list[dict]:
    """
    Načte zprávy konverzace.
    Pokud after_id je zadán, načte jen zprávy s id > after_id.
    Skládá od nejnovějších a respektuje token budget.
    """
    session = get_data_session()
    try:
        query = session.query(Message).filter_by(conversation_id=conversation_id)
        if after_id is not None:
            query = query.filter(Message.id > after_id)
        messages = query.order_by(Message.id.desc()).all()

        # Skládáme od nejnovějších, dokud se vejdeme do budgetu
        selected = []
        used_tokens = 0
        for msg in messages:
            tokens = _estimate_tokens(msg.content)
            if used_tokens + tokens > MAX_TOKENS:
                break
            selected.append({"role": msg.role, "content": msg.content})
            used_tokens += tokens

        # Otočíme zpět do chronologického pořadí
        selected.reverse()
        return selected
    finally:
        session.close()


def build_prompt(conversation_id: int) -> tuple[str, list[dict]]:
    """
    Sestaví prompt pro LLM z více vrstev:
    1. system prompt (css_db)
    2. persona prompt (css_db)
    3. summary (data_db) — jako system zpráva
    4. detailní zprávy (data_db) — jen po to_message_id summary

    Vrátí (system_prompt, messages).
    """
    # 1. System prompt
    system_prompt = _get_system_prompt()

    # 2. Persona prompt — přidáme k system promptu
    persona_prompt = _get_persona_prompt()
    if persona_prompt:
        system_prompt = f"{system_prompt}\n\n{persona_prompt}"

    # 3. Summary
    summary = _get_latest_summary(conversation_id)
    after_id = summary.to_message_id if summary else None

    # 4. Detailní zprávy
    messages = _get_messages(conversation_id, after_id=after_id)

    # Přidáme summary jako první system zprávu v messages
    if summary:
        messages = [
            {"role": "user", "content": f"[Shrnutí předchozí konverzace]: {summary.summary_text}"},
            {"role": "assistant", "content": "Rozumím, pokračujeme."},
        ] + messages

    return system_prompt, messages
