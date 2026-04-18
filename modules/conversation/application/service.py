"""
Conversation service s Execution layer.
"""
import json
import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.application.tools import (
    TOOLS, format_email_preview, find_user_in_system,
    invite_user_to_strategie, start_chat_with_user,
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
    logger.info(f"CONFIRM_CHECK | text='{cleaned}'")
    if "@" in cleaned or len(cleaned.split()) > 3:
        return False
    return cleaned in CONFIRM_KEYWORDS


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
        logger.info(f"PENDING_ACTION | saved | type={action_type}")
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


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> tuple[str, int | None]:
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
        ), None

    if tool_name == "find_user":
        result = find_user_in_system(tool_input.get("query", ""))
        if result["found"]:
            status = result["status"]
            name = result["name"]
            if status == "active":
                return f"✅ {name} je v systému.\n\nChceš zahájit chat nebo poslat email?", None
            else:
                return f"⏳ {name} má pozvánku ale ještě se nepřihlásil/a.", None
        return f"❌ '{tool_input.get('query', '')}' není v systému.\n\nChceš ho/ji pozvat?", None

    if tool_name == "invite_user":
        email = tool_input.get("email", "")
        result = invite_user_to_strategie(email=email, name=tool_input.get("name", ""), invited_by_user_id=user_id or 1)
        if result["success"] and result["email_sent"]:
            return f"✅ Pozvánka odeslána na {email}.", None
        return f"⚠️ Pozvánka vytvořena ale email se nepodařilo odeslat.", None

    if tool_name == "start_chat":
        query = tool_input.get("query", "")
        user_result = find_user_in_system(query)
        if not user_result["found"]:
            return f"❌ '{query}' není v systému.\n\nChceš ho/ji pozvat?", None
        if user_result["status"] != "active":
            return f"⏳ {user_result['name']} ještě nepřijal/a pozvánku.", None

        result = start_chat_with_user(
            target_user_id=user_result["user_id"],
            target_name=user_result["name"],
            initiated_by_user_id=user_id or 1,
        )
        if result["success"]:
            new_conv_id = result["conversation_id"]
            name = result["target_name"]
            msg = (
                f"✅ Zahájil/a jsem konverzaci s {name}.\n\n"
                f"Konverzace #{new_conv_id} je sdílená. Napiš svou zprávu."
            )
            return msg, new_conv_id
        return f"❌ Nepodařilo se zahájit konverzaci.", None

    return "", None


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str, int | None]:
    """
    Vrátí (conversation_id, reply, switch_to_conversation_id).
    """
    switch_to = None

    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    # Potvrzení čekající akce
    if _is_confirmation(user_message) and _get_pending_action(conversation_id):
        save_message(conversation_id, role="user", content=user_message)
        result = _execute_pending_action(conversation_id)
        if result:
            save_message(conversation_id, role="assistant", content=result)
            return conversation_id, result, None

    # Uložíme zprávu uživatele do AKTUÁLNÍ konverzace
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
            tool_text, new_conv_id = _handle_tool(block.name, block.input, conversation_id, user_id=user_id)
            assistant_reply += tool_text
            if new_conv_id:
                switch_to = new_conv_id

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    # Odpověď AI uložíme do SDÍLENÉ konverzace pokud došlo k přepnutí
    save_conv_id = switch_to if switch_to else conversation_id
    save_message(save_conv_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | original={conversation_id} | saved_to={save_conv_id} | user_id={user_id}")

    # Memory extrakce z původní konverzace
    try:
        from modules.memory.application.service import extract_and_save
        all_messages = get_messages(conversation_id)
        extract_and_save(
            conversation_id=conversation_id,
            messages=all_messages,
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"MEMORY | failed: {e}")

    # Vrátíme sdílenou konverzaci jako aktivní
    return save_conv_id, assistant_reply, switch_to
