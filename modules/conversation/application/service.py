"""
Conversation service s Execution layer.
AI může navrhovat akce (send_email), uživatel potvrzuje.
"""
import json
import anthropic

from core.config import settings
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.application.tools import TOOLS, format_email_preview
from modules.conversation.infrastructure.repository import (
    create_conversation,
    save_message,
    get_messages,
)

logger = get_logger("conversation")

MODEL = "claude-haiku-4-5-20251001"

# Klíčová slova pro potvrzení akce
CONFIRM_KEYWORDS = {"ano", "pošli", "odeslat", "posli", "ok", "jo", "yes", "send"}

# Dočasné úložiště čekajících akcí (per conversation)
# V produkci by šlo do DB nebo Redis
_pending_actions: dict[int, dict] = {}


def _is_confirmation(text: str) -> bool:
    """Zjistí jestli zpráva je potvrzení čekající akce."""
    return text.strip().lower() in CONFIRM_KEYWORDS


def _execute_pending_action(conversation_id: int) -> str | None:
    """Vykoná čekající akci pokud existuje."""
    action = _pending_actions.pop(conversation_id, None)
    if not action:
        return None

    if action["type"] == "send_email":
        from modules.notifications.application.email_service import send_email
        sent = send_email(
            to=action["to"],
            subject=action["subject"],
            body=action["body"],
        )
        if sent:
            return f"✅ Email byl odeslán na {action['to']}."
        else:
            return f"❌ Email se nepodařilo odeslat. Zkus to znovu."

    return None


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str]:
    """
    Hlavní orchestrace konverzace s Execution layer.

    Tok:
    1. Zkontroluj jestli jde o potvrzení čekající akce
    2. Pokud ano — vykonej akci
    3. Pokud ne — zavolej LLM s nástroji
    4. Pokud LLM navrhne akci — ulož ji a zobraz návrh
    5. Jinak vrať normální odpověď
    """
    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    # Zkontroluj potvrzení čekající akce
    if conversation_id in _pending_actions and _is_confirmation(user_message):
        save_message(conversation_id, role="user", content=user_message)
        result = _execute_pending_action(conversation_id)
        save_message(conversation_id, role="assistant", content=result)
        logger.info(f"CONVERSATION | action executed | conversation_id={conversation_id}")
        return conversation_id, result

    save_message(conversation_id, role="user", content=user_message)

    system_prompt, messages = build_prompt(conversation_id)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        tools=TOOLS,
    )

    # Zpracuj odpověď — může být text nebo tool_use
    assistant_reply = ""

    for block in response.content:
        if block.type == "text":
            assistant_reply += block.text

        elif block.type == "tool_use":
            if block.name == "send_email":
                # AI navrhuje poslat email — ulož akci a zobraz návrh
                tool_input = block.input
                _pending_actions[conversation_id] = {
                    "type": "send_email",
                    "to": tool_input.get("to", ""),
                    "subject": tool_input.get("subject", ""),
                    "body": tool_input.get("body", ""),
                }
                assistant_reply += format_email_preview(
                    to=tool_input.get("to", ""),
                    subject=tool_input.get("subject", ""),
                    body=tool_input.get("body", ""),
                )
                logger.info(f"CONVERSATION | email action pending | conversation_id={conversation_id}")

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    save_message(conversation_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

    # Extrakce pamětí na pozadí
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
