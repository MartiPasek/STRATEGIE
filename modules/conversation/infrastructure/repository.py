from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import SystemPrompt
from modules.core.infrastructure.models_data import Conversation, Message

logger = get_logger("conversation")


def get_system_prompt() -> str | None:
    """
    Načte první dostupný system prompt z css_db.
    Vrátí content nebo None pokud žádný neexistuje.
    """
    session = get_core_session()
    try:
        prompt = session.query(SystemPrompt).first()
        return prompt.content if prompt else None
    finally:
        session.close()


def create_conversation() -> int:
    """Vytvoří novou konverzaci v data_db. Vrátí její id."""
    session = get_data_session()
    try:
        conversation = Conversation()
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info(f"CONVERSATION | created | id={conversation.id}")
        return conversation.id
    finally:
        session.close()


def save_message(conversation_id: int, role: str, content: str) -> int:
    """Uloží zprávu do data_db. Vrátí její id."""
    session = get_data_session()
    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        return message.id
    finally:
        session.close()


def get_messages(conversation_id: int) -> list[dict]:
    """
    Načte všechny zprávy konverzace seřazené podle id.
    Vrátí list slovníků {role, content}.
    """
    session = get_data_session()
    try:
        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.id)
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]
    finally:
        session.close()
