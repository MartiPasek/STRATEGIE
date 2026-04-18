import anthropic

from core.config import settings
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.infrastructure.repository import (
    create_conversation,
    save_message,
    get_messages,
)

logger = get_logger("conversation")

MODEL = "claude-haiku-4-5-20251001"


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str]:
    """
    Hlavní orchestrace konverzace.
    Po odpovědi AI spustí extrakci pamětí na pozadí.
    """
    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    save_message(conversation_id, role="user", content=user_message)

    system_prompt, messages = build_prompt(conversation_id)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    assistant_reply = response.content[0].text

    save_message(conversation_id, role="assistant", content=assistant_reply)

    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

    # Spusť extrakci pamětí — tiše, selhání nerozbije chat
    try:
        from modules.memory.application.service import extract_and_save
        all_messages = get_messages(conversation_id)
        extract_and_save(
            conversation_id=conversation_id,
            messages=all_messages,
            user_id=user_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
    except Exception as e:
        logger.error(f"MEMORY | background extraction failed: {e}")

    return conversation_id, assistant_reply
