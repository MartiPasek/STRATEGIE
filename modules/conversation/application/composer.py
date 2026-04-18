"""
Composer — skládá prompt z více vrstev.
Načítá personu podle active_agent_id konverzace.
"""
from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import SystemPrompt, Persona
from modules.core.infrastructure.models_data import Message, ConversationSummary, Conversation

logger = get_logger("conversation.composer")

DEFAULT_SYSTEM_PROMPT = "Jsi neutrální asistent. Odpovídej věcně a srozumitelně."
MAX_TOKENS = 6000
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _get_system_prompt() -> str:
    session = get_core_session()
    try:
        prompt = session.query(SystemPrompt).first()
        return prompt.content if prompt else DEFAULT_SYSTEM_PROMPT
    finally:
        session.close()


def _get_persona_prompt(conversation_id: int) -> str | None:
    """
    Načte personu podle active_agent_id konverzace.
    Pokud není nastavena, použije default personu.
    """
    data_session = get_data_session()
    try:
        conversation = data_session.query(Conversation).filter_by(id=conversation_id).first()
        active_agent_id = conversation.active_agent_id if conversation else None
    finally:
        data_session.close()

    core_session = get_core_session()
    try:
        if active_agent_id:
            persona = core_session.query(Persona).filter_by(id=active_agent_id).first()
        else:
            persona = core_session.query(Persona).filter_by(is_default=True).first()
        return persona.system_prompt if persona else None
    finally:
        core_session.close()


def _get_latest_summary(conversation_id: int) -> ConversationSummary | None:
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
    session = get_data_session()
    try:
        query = session.query(Message).filter_by(conversation_id=conversation_id)
        if after_id is not None:
            query = query.filter(Message.id > after_id)
        messages = query.order_by(Message.id.desc()).all()

        selected = []
        used_tokens = 0
        for msg in messages:
            tokens = _estimate_tokens(msg.content)
            if used_tokens + tokens > MAX_TOKENS:
                break
            selected.append({"role": msg.role, "content": msg.content})
            used_tokens += tokens

        selected.reverse()
        return selected
    finally:
        session.close()


def build_prompt(conversation_id: int) -> tuple[str, list[dict]]:
    """
    Vrátí (system_prompt, messages) pro LLM.
    Persona se načte podle active_agent_id konverzace.
    """
    system_prompt = _get_system_prompt()

    persona_prompt = _get_persona_prompt(conversation_id)
    if persona_prompt:
        system_prompt = f"{system_prompt}\n\n{persona_prompt}"

    summary = _get_latest_summary(conversation_id)
    after_id = summary.to_message_id if summary else None

    messages = _get_messages(conversation_id, after_id=after_id)

    if summary:
        messages = [
            {"role": "user", "content": f"[Shrnutí předchozí konverzace]: {summary.summary_text}"},
            {"role": "assistant", "content": "Rozumím, pokračujeme."},
        ] + messages

    return system_prompt, messages
