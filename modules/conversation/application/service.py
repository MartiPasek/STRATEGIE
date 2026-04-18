"""
Conversation service s Execution layer.
Pending akce jsou uložené v DB — přežijí restart serveru.
"""
import json
import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.application.tools import TOOLS, format_email_preview, find_user_in_system
from modules.conversation.infrastructure.repository import (
    create_conversation,
    save_message,
    get_messages,
)
from modules.core.infrastructure.models_data import PendingAction

logger = get_logger("conversation")

MODEL = "claude-haiku-4-5-20251001"

CONFIRM_KEYWORDS = {"ano", "pošli", "odeslat", "posli", "ok", "jo", "yes", "send"}


def _is_confirmation(text: str) -> bool:
    cleaned = text.strip().lower()
    logger.info(f"CONFIRM_CHECK | text='{cleaned}' | has_at={'@' in cleaned} | words={len(cleaned.split())}")
    if "@" in cleaned or len(cleaned.split()) > 3:
        return False
    result = cleaned in CONFIRM_KEYWORDS
    logger.info(f"CONFIRM_CHECK | result={result}")
    return result


def _save_pending_action(conversation_id: int, action_type: str, payload: dict) -> None:
    session = get_data_session()
    try:
        session.query(PendingAction).filter_by(conversation_id=conversation_id).delete()
        action = PendingAction(
            conversation_id=conversation_id,
            action_type=action_type,
            payload=json.dumps(payload),
        )
        session.add(action)
        session.commit()
        logger.info(f"PENDING_ACTION | saved | conversation_id={conversation_id} | type={action_type}")
    finally:
        session.close()


def _get_pending_action(conversation_id: int) -> dict | None:
    session = get_data_session()
    try:
        action = session.query(PendingAction).filter_by(conversation_id=conversation_id).first()
        if not action:
            logger.info(f"PENDING_ACTION | not found | conversation_id={conversation_id}")
            return None
        logger.info(f"PENDING_ACTION | found | conversation_id={conversation_id} | type={action.action_type}")
        return {"type": action.action_type, **json.loads(action.payload)}
    finally:
        session.close()


def _delete_pending_action(conversation_id: int) -> None:
    session = get_data_session()
    try:
        session.query(PendingAction).filter_by(conversation_id=conversation_id).delete()
        session.commit()
    finally:
        session.close()


def _execute_pending_action(conversation_id: int) -> str | None:
    action = _get_pending_action(conversation_id)
    if not action:
        return None

    _delete_pending_action(conversation_id)

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


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int) -> str:
    logger.info(f"TOOL | name={tool_name} | input={tool_input}")

    if tool_name == "send_email":
        _save_pending_action(conversation_id, "send_email", {
            "to": tool_input.get("to", ""),
            "subject": tool_input.get("subject", ""),
            "body": tool_input.get("body", ""),
        })
        return format_email_preview(
            to=tool_input.get("to", ""),
            subject=tool_input.get("subject", ""),
            body=tool_input.get("body", ""),
        )

    if tool_name == "find_user":
        result = find_user_in_system(tool_input.get("query", ""))
        logger.info(f"FIND_USER | result={result}")
        if result["found"]:
            name = result["name"]
            status = result["status"]
            if status == "active":
                return (
                    f"✅ {name} je v systému STRATEGIE.\n\n"
                    f"Chceš:\n- Poslat mu/jí email?\n- Nebo něco jiného?"
                )
            else:
                return (
                    f"⏳ {name} má pozvánku do STRATEGIE, ale ještě se nepřihlásil/a.\n\n"
                    f"Chceš poslat připomínku?"
                )
        else:
            return (
                f"❌ '{tool_input.get('query', '')}' není v systému STRATEGIE.\n\n"
                f"Chceš ho/ji pozvat? Řekni mi email a pošleme pozvánku."
            )

    return ""


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str]:
    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    # Potvrzení čekající akce z DB
    if _is_confirmation(user_message) and _get_pending_action(conversation_id):
        save_message(conversation_id, role="user", content=user_message)
        result = _execute_pending_action(conversation_id)
        if result:
            save_message(conversation_id, role="assistant", content=result)
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

    assistant_reply = ""
    for block in response.content:
        logger.info(f"BLOCK | type={block.type}")
        if block.type == "text":
            assistant_reply += block.text
        elif block.type == "tool_use":
            logger.info(f"TOOL_USE | name={block.name} | input={block.input}")
            tool_result = _handle_tool(block.name, block.input, conversation_id)
            logger.info(f"TOOL_RESULT | result={tool_result[:100] if tool_result else 'EMPTY'}")
            assistant_reply += tool_result

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    save_message(conversation_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

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
