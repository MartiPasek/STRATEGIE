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


def create_conversation(user_id: int | None = None, tenant_id: int | None = None) -> int:
    """
    Vytvoří novou AI konverzaci. Tenant_id se ukládá, aby se konverzace
    daly filtrovat podle aktuálního tenantu uživatele (sidebar/dropdown
    musí ukazovat jen konverzace patřící k danému tenantu — Osobní vs.
    EUROSOFT vs. DOMA atd.).
    """
    session = get_data_session()
    try:
        conversation = Conversation(user_id=user_id, tenant_id=tenant_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info(f"CONVERSATION | created | id={conversation.id} | user_id={user_id} | tenant_id={tenant_id}")
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

        # Denormalizace pro rychlý listing + auto-fill agent_id.
        # Pokud volající neurčil agent_id a zpráva je od AI, použij aktivní
        # agent konverzace — ať se dá zpětně rekonstruovat, která persona
        # danou repliku dala (důležité pro multi-agent flow a audit).
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()
        effective_agent_id = agent_id
        if effective_agent_id is None and author_type == "ai" and conversation is not None:
            effective_agent_id = conversation.active_agent_id

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            author_type=author_type,
            author_user_id=author_user_id,
            agent_id=effective_agent_id,
            message_type=message_type,
        )
        session.add(message)
        session.flush()   # získá id před commitem

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
            "is_archived": bool(conversation.is_archived),
            "messages": [{"role": m.role, "content": m.content, "message_type": m.message_type} for m in messages],
        }
    finally:
        session.close()


def _conversation_title(session, conversation: Conversation) -> str:
    """
    Vrátí title konverzace pro UI sidebar:
      1) conversation.title (pokud je vyplněn — třeba ručně přejmenovaný)
      2) první user/text message zkrácená na 60 znaků
      3) fallback: 'Konverzace #{id}'
    """
    if conversation.title:
        return conversation.title
    first_msg = (
        session.query(Message)
        .filter_by(conversation_id=conversation.id, message_type="text")
        .order_by(Message.id.asc())
        .first()
    )
    if first_msg and first_msg.content:
        text = first_msg.content.strip().replace("\n", " ")
        return text[:60] + ("…" if len(text) > 60 else "")
    return f"Konverzace #{conversation.id}"


def list_conversations(user_id: int, tenant_id: int | None = None, limit: int = 50) -> list[dict]:
    """
    Vrátí seznam AI konverzací usera pro UI sidebar (nejnovější první).

    Filtruje podle aktivního tenantu — Marti v Osobním tenantu nemá
    vidět EUROSOFT konverzace a naopak. Konverzace s tenant_id IS NULL
    (legacy z doby před filtraci) jsou vidět ve VŠECH tenantech, dokud
    se neudělá backfill — zatím nezpůsobí ztrátu historie.

    Pole per item: id, title (preview), tenant_id, last_message_at,
    message_count. DM konverzace vynechány (mají vlastní UI).
    """
    from sqlalchemy import or_
    session = get_data_session()
    try:
        filters = [
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,  # noqa: E712
            Conversation.is_archived == False,  # noqa: E712 — archive je samostatný view
            Conversation.conversation_type == "ai",
        ]
        if tenant_id is not None:
            filters.append(or_(
                Conversation.tenant_id == tenant_id,
                Conversation.tenant_id.is_(None),  # legacy — viditelné všude
            ))
        rows = (
            session.query(Conversation)
            .filter(*filters)
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.id.desc(),
            )
            .limit(limit)
            .all()
        )
        out: list[dict] = []
        for c in rows:
            msg_count = (
                session.query(Message)
                .filter_by(conversation_id=c.id)
                .count()
            )
            out.append({
                "id": c.id,
                "title": _conversation_title(session, c),
                "tenant_id": c.tenant_id,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "message_count": msg_count,
            })
        return out
    finally:
        session.close()


def list_archived_conversations(user_id: int, tenant_id: int | None = None, limit: int = 100) -> list[dict]:
    """
    Vrátí archivované AI konverzace usera (is_archived=true, is_deleted=false).
    Filtruje podle aktivního tenantu jako list_conversations — Marti v Osobním
    nevidí archivy z EUROSOFTu a naopak.
    """
    from sqlalchemy import or_
    session = get_data_session()
    try:
        filters = [
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,  # noqa: E712
            Conversation.is_archived == True,  # noqa: E712
            Conversation.conversation_type == "ai",
        ]
        if tenant_id is not None:
            filters.append(or_(
                Conversation.tenant_id == tenant_id,
                Conversation.tenant_id.is_(None),
            ))
        rows = (
            session.query(Conversation)
            .filter(*filters)
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.id.desc(),
            )
            .limit(limit)
            .all()
        )
        out: list[dict] = []
        for c in rows:
            msg_count = session.query(Message).filter_by(conversation_id=c.id).count()
            out.append({
                "id": c.id,
                "title": _conversation_title(session, c),
                "tenant_id": c.tenant_id,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "message_count": msg_count,
            })
        return out
    finally:
        session.close()


def rename_conversation(user_id: int, conversation_id: int, new_title: str) -> bool:
    """
    Přejmenuje konverzaci (ručně zvolený popisek místo auto-generovaného
    z první zprávy). Title se ukládá do conversations.title.
    Ověří vlastnictví, vrací False při 404.
    Prázdný / whitespace-only title → ulož NULL (vrátí se k auto-titlu).
    """
    cleaned = (new_title or "").strip()
    if len(cleaned) > 255:
        cleaned = cleaned[:255]
    session = get_data_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv or conv.user_id != user_id:
            return False
        conv.title = cleaned if cleaned else None
        session.commit()
        return True
    finally:
        session.close()


def set_conversation_flag(
    user_id: int, conversation_id: int, *, is_deleted: bool | None = None, is_archived: bool | None = None,
) -> bool:
    """
    Soft-update flagu konverzace (smaže / archivuje). Ověří vlastnictví —
    pokud user_id nesedí, vrátí False (router přeloží na 404).
    Vrací True při úspěchu.
    """
    session = get_data_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv or conv.user_id != user_id:
            return False
        if is_deleted is not None:
            conv.is_deleted = is_deleted
        if is_archived is not None:
            conv.is_archived = is_archived
        session.commit()
        return True
    finally:
        session.close()


def load_conversation(user_id: int, conversation_id: int) -> dict | None:
    """
    Načte konkrétní konverzaci pro UI (po kliknutí v sidebaru).
    Ověří vlastnictví (user_id) — pokud nesedí, vrátí None (frontend
    interpretuje jako 404 a nezobrazí cizí obsah).
    """
    session = get_data_session()
    try:
        conversation = (
            session.query(Conversation)
            .filter_by(id=conversation_id, is_deleted=False)
            .first()
        )
        if not conversation or conversation.user_id != user_id:
            return None

        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation.id)
            .order_by(Message.id)
            .all()
        )
        return {
            "conversation_id": conversation.id,
            "is_archived": bool(conversation.is_archived),
            "messages": [
                {"role": m.role, "content": m.content, "message_type": m.message_type}
                for m in messages
            ],
        }
    finally:
        session.close()
