"""
Conversation repository — používá modely z modules/core/infrastructure.
"""
from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import SystemPrompt, Persona
from modules.core.infrastructure.models_data import Conversation, Message

logger = get_logger("conversation")


def get_system_prompt() -> str | None:
    session = get_core_session()
    try:
        prompt = session.query(SystemPrompt).first()
        return prompt.content if prompt else None
    finally:
        session.close()


def create_conversation(user_id: int | None = None) -> int:
    session = get_data_session()
    try:
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info(f"CONVERSATION | created | id={conversation.id} | user_id={user_id}")
        return conversation.id
    finally:
        session.close()


def save_message(conversation_id: int, role: str, content: str) -> int:
    session = get_data_session()
    try:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        session.add(message)
        session.commit()
        session.refresh(message)
        return message.id
    finally:
        session.close()


def get_messages(conversation_id: int) -> list[dict]:
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


def get_active_persona_name(conversation_id: int) -> str:
    """Vrátí název aktivní persony pro konverzaci."""
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
            if persona:
                return persona.name
        # Default
        persona = core_session.query(Persona).filter_by(is_default=True).first()
        return persona.name if persona else "Marti-AI"
    finally:
        core_session.close()


def get_last_conversation(user_id: int) -> dict | None:
    session = get_data_session()
    try:
        conversation = (
            session.query(Conversation)
            .filter_by(user_id=user_id, is_deleted=False)
            .order_by(Conversation.id.desc())
            .first()
        )
        if not conversation:
            return None

        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation.id)
            .order_by(Message.id)
            .all()
        )
        return {
            "conversation_id": conversation.id,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
    finally:
        session.close()
