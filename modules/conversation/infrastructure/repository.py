"""
Conversation repository — používá modely z modules/core/infrastructure.
"""
from datetime import datetime, timezone

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import SystemPrompt, Persona
from modules.core.infrastructure.models_data import (
    Conversation,
    ConversationParticipant,
    Message,
)

logger = get_logger("conversation")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


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


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    *,
    author_type: str = "ai",
    author_user_id: int | None = None,
    agent_id: int | None = None,
    message_type: str = "text",
) -> int:
    """
    Uloží zprávu a zároveň aktualizuje denormalizovaná pole v konverzaci
    (last_message_id, last_message_at) — potřebné pro listing DM vláken.

    Zpětně kompatibilní: staré volání `save_message(cid, role, content)`
    zůstává funkční a použije defaulty pro AI chat.
    """
    session = get_data_session()
    try:
        now = _now_utc()
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            author_type=author_type,
            author_user_id=author_user_id,
            agent_id=agent_id,
            message_type=message_type,
        )
        session.add(message)
        session.flush()   # získá id před commitem

        # Denormalizace pro rychlý listing
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation is not None:
            conversation.last_message_id = message.id
            conversation.last_message_at = now

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
        return [{"role": m.role, "content": m.content, "message_type": m.message_type} for m in messages]
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
