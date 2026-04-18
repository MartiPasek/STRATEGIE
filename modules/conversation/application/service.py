"""
Conversation service s Execution layer.
Každý uživatel má svůj vlastní chat. Přepínání person místo sdílených konverzací.
"""
import json
import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.application.tools import (
    TOOLS, format_email_preview, find_user_in_system,
    invite_user_to_strategie, switch_persona_for_user,
)
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
    if "@" in cleaned or len(cleaned.split()) > 3:
        return False
    return cleaned in CONFIRM_KEYWORDS


def _save_pending_action(conversation_id: int, action_type: str, payload: dict) -> None:
    session = get_data_session()
    try:
        session.query(PendingAction).filter_by(conversation_id=conversation_id).delete()
        action = PendingAction(conversation_id=conversation_id, action_type=action_type, payload=json.dumps(payload))
        session.add(action)
        session.commit()
    finally:
        session.close()


def _get_pending_action(conversation_id: int) -> dict | None:
    session = get_data_session()
    try:
        action = session.query(PendingAction).filter_by(conversation_id=conversation_id).first()
        if not action:
            return None
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
        sent = send_email(to=action["to"], subject=action["subject"], body=action["body"])
        return f"✅ Email byl odeslán na {action['to']}." if sent else "❌ Email se nepodařilo odeslat."
    return None


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:
    logger.info(f"TOOL | name={tool_name}")

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
        if result["found"]:
            name = result["name"]
            status = result["status"]
            if status == "active":
                return f"✅ {name} je v systému STRATEGIE.\n\nChceš:\n- Poslat email?\n- Přepnout na {name}-AI?"
            else:
                return f"⏳ {name} má pozvánku ale ještě se nepřihlásil/a."
        return f"❌ '{tool_input.get('query', '')}' není v systému.\n\nChceš ho/ji pozvat?"

    if tool_name == "invite_user":
        email = tool_input.get("email", "")
        result = invite_user_to_strategie(email=email, name=tool_input.get("name", ""), invited_by_user_id=user_id or 1)
        if result["success"] and result["email_sent"]:
            return f"✅ Pozvánka odeslána na {email}."
        return f"⚠️ Pozvánka vytvořena ale email se nepodařilo odeslat na {email}."

    if tool_name == "switch_persona":
        query = tool_input.get("query", "")
        result = switch_persona_for_user(query=query, conversation_id=conversation_id)
        if result["found"]:
            name = result["persona_name"]
            return (
                f"✅ Přepnuto na {name}.\n\n"
                f"Nyní mluvíš s {name}. Jak ti mohu pomoci?"
            )
        else:
            return (
                f"❌ Personu '{query}' jsem nenašel/a v systému.\n\n"
                f"Dostupné persony jsou ty, které jsou nastavené v STRATEGIE. "
                f"Chceš pokračovat s výchozí personou?"
            )

    return ""


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str, None]:
    """Vrátí (conversation_id, reply, None) — switch_to vždy None (žádné sdílení)."""

    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    if _is_confirmation(user_message) and _get_pending_action(conversation_id):
        save_message(conversation_id, role="user", content=user_message)
        result = _execute_pending_action(conversation_id)
        if result:
            save_message(conversation_id, role="assistant", content=result)
            return conversation_id, result, None

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
            logger.info(f"TOOL_USE | name={block.name}")
            tool_result = _handle_tool(block.name, block.input, conversation_id, user_id=user_id)
            assistant_reply += tool_result

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    save_message(conversation_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

    try:
        from modules.memory.application.service import extract_and_save
        all_messages = get_messages(conversation_id)
        extract_and_save(conversation_id=conversation_id, messages=all_messages, user_id=user_id)
    except Exception as e:
        logger.error(f"MEMORY | failed: {e}")

    return conversation_id, assistant_reply, None
