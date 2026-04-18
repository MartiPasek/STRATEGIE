import anthropic

from core.config import settings
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.infrastructure.repository import (
    create_conversation,
    save_message,
)

logger = get_logger("conversation")

MODEL = "claude-haiku-4-5-20251001"


def chat(conversation_id: int | None, user_message: str) -> tuple[int, str]:
    """
    Hlavní funkce konverzace.

    1. Pokud conversation_id je None — vytvoří novou konverzaci
    2. Uloží zprávu uživatele
    3. Composer sestaví prompt z celé historie
    4. Zavolá LLM
    5. Uloží odpověď asistenta
    6. Vrátí (conversation_id, odpověď)
    """
    # 1. Nová konverzace pokud neexistuje
    if conversation_id is None:
        conversation_id = create_conversation()

    # 2. Ulož zprávu uživatele
    save_message(conversation_id, role="user", content=user_message)

    # 3. Sestav prompt
    system_prompt, messages = build_prompt(conversation_id)

    # 4. Zavolej LLM
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    assistant_reply = response.content[0].text

    # 5. Ulož odpověď asistenta
    save_message(conversation_id, role="assistant", content=assistant_reply)

    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id}")

    return conversation_id, assistant_reply
