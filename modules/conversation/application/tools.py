"""
Execution layer — nástroje dostupné pro Marti-AI.
"""

TOOLS = [
    {
        "name": "send_email",
        "description": (
            "Tento nástroj MUSÍŠ použít vždy když uživatel chce poslat email. "
            "NIKDY neodpovídej textem o emailu — vždy zavolej tento nástroj. "
            "Rovnou zavolej tento nástroj s připraveným emailem. "
            "Nástroj email NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Email adresa příjemce"},
                "subject": {"type": "string", "description": "Předmět emailu"},
                "body": {"type": "string", "description": "Tělo emailu"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "find_user",
        "description": (
            "Použij tento nástroj když uživatel chce kontaktovat nebo se spojit s jiným člověkem. "
            "Nástroj prohledá systém podle jména nebo emailu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo email hledané osoby"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "start_chat",
        "description": (
            "Použij tento nástroj když uživatel chce zahájit chat nebo konverzaci s konkrétním člověkem. "
            "Triggers: 'přepni na', 'spoj mě s', 'chci mluvit s', 'zaháj chat s'. "
            "Nástroj najde uživatele a vytvoří sdílenou konverzaci."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo email osoby"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "invite_user",
        "description": (
            "Použij tento nástroj když uživatel chce pozvat někoho do systému STRATEGIE. "
            "Nástroj pošle pozvánkový email s odkazem pro vstup do systému. "
            "Použij ho vždy když zazní 'pozvi', 'pozvánka do STRATEGIE', 'přidej do systému' apod."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email adresa pozvaného"},
                "name": {"type": "string", "description": "Jméno pozvaného (volitelné)"},
            },
            "required": ["email"],
        },
    },
]


def format_email_preview(to: str, subject: str, body: str) -> str:
    return (
        f"📧 Návrh emailu\n\n"
        f"Komu: {to}\n"
        f"Předmět: {subject}\n\n"
        f"{body}\n\n"
        f"---\n"
        f"Mám email odeslat? Napiš ano nebo pošli."
    )


def find_user_in_system(query: str) -> dict:
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, UserIdentity
    from sqlalchemy import or_

    session = get_core_session()
    try:
        query_lower = query.strip().lower()

        identity = session.query(UserIdentity).filter(
            UserIdentity.value.ilike(f"%{query_lower}%"),
            UserIdentity.type == "email",
        ).first()

        if identity:
            user = session.query(User).filter_by(id=identity.user_id).first()
            if user:
                name = " ".join(filter(None, [user.first_name, user.last_name]))
                return {
                    "found": True,
                    "user_id": user.id,
                    "name": name or identity.value,
                    "email": identity.value,
                    "status": user.status,
                }

        users = session.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query_lower}%"),
                User.last_name.ilike(f"%{query_lower}%"),
            )
        ).all()

        if users:
            user = users[0]
            identity = session.query(UserIdentity).filter_by(
                user_id=user.id, type="email"
            ).first()
            name = " ".join(filter(None, [user.first_name, user.last_name]))
            return {
                "found": True,
                "user_id": user.id,
                "name": name,
                "email": identity.value if identity else "",
                "status": user.status,
            }

        return {"found": False, "query": query}

    finally:
        session.close()


def invite_user_to_strategie(
    email: str,
    name: str | None,
    invited_by_user_id: int,
) -> dict:
    """
    Pozve uživatele do STRATEGIE a odešle pozvánkový email.
    Vrátí výsledek operace.
    """
    from modules.auth.application.invitation_service import create_invitation
    from modules.notifications.application.email_service import send_invitation_email
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User

    session = get_core_session()
    try:
        inviter = session.query(User).filter_by(id=invited_by_user_id).first()
        inviter_name = " ".join(filter(None, [inviter.first_name, inviter.last_name])) if inviter else "Člen týmu"
        tenant_id = inviter.last_active_tenant_id if inviter else 1
    finally:
        session.close()

    try:
        token = create_invitation(
            email=email.strip().lower(),
            invited_by_user_id=invited_by_user_id,
            tenant_id=tenant_id or 1,
        )

        sent = send_invitation_email(
            to=email,
            invited_by=inviter_name,
            token=token,
        )

        return {
            "success": True,
            "email": email,
            "email_sent": sent,
            "name": name,
        }
    except Exception as e:
        return {
            "success": False,
            "email": email,
            "error": str(e),
        }


def start_chat_with_user(
    target_user_id: int,
    target_name: str,
    initiated_by_user_id: int,
) -> dict:
    """
    Zahájí nebo najde existující sdílenou konverzaci mezi dvěma uživateli.
    Vrátí conversation_id a informaci o tom co se stalo.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import Conversation, ConversationShare
    from datetime import datetime, timezone

    session = get_data_session()
    try:
        # Hledej existující sdílenou konverzaci
        existing_share = (
            session.query(ConversationShare)
            .filter_by(shared_with_user_id=target_user_id)
            .join(Conversation, Conversation.id == ConversationShare.conversation_id)
            .filter(Conversation.user_id == initiated_by_user_id)
            .first()
        )

        if existing_share:
            return {
                "success": True,
                "conversation_id": existing_share.conversation_id,
                "new": False,
                "target_name": target_name,
            }

        # Vytvoř novou konverzaci
        conversation = Conversation(
            user_id=initiated_by_user_id,
            title=f"Chat s {target_name}",
        )
        session.add(conversation)
        session.flush()

        # Sdílej s druhým uživatelem
        share = ConversationShare(
            conversation_id=conversation.id,
            shared_with_user_id=target_user_id,
            access_level="write",
        )
        session.add(share)
        session.commit()

        return {
            "success": True,
            "conversation_id": conversation.id,
            "new": True,
            "target_name": target_name,
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()





def start_chat_with_user(
    target_user_id: int,
    target_name: str,
    initiated_by_user_id: int,
) -> dict:
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import Conversation, ConversationShare
    from core.logging import get_logger
    
    logger = get_logger("start_chat")
    logger.info(f"START_CHAT | target={target_user_id} | by={initiated_by_user_id}")
    
    session = get_data_session()
    try:
        conversation = Conversation(
            user_id=initiated_by_user_id,
            title=f"Chat s {target_name}",
        )
        session.add(conversation)
        session.flush()
        logger.info(f"START_CHAT | conversation created | id={conversation.id}")

        share = ConversationShare(
            conversation_id=conversation.id,
            shared_with_user_id=target_user_id,
            access_level="write",
        )
        session.add(share)
        session.commit()
        logger.info(f"START_CHAT | share created | conversation_id={conversation.id} | shared_with={target_user_id}")

        return {"success": True, "conversation_id": conversation.id, "new": True, "target_name": target_name}
    except Exception as e:
        session.rollback()
        logger.error(f"START_CHAT | error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()        
