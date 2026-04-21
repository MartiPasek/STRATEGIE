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


def create_conversation(
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> int:
    """
    Vytvoří novou AI konverzaci. Tenant_id + project_id se ukládají, aby se
    konverzace daly filtrovat podle aktuálního kontextu (sidebar musí ukazovat
    jen konverzace patřící k danému tenantu, a uvnitř tenantu se dají grupovat
    podle projektu). project_id=None znamená "bez projektu" — konverzace žije
    v tenantu mimo jakýkoli project scope.
    """
    session = get_data_session()
    try:
        conversation = Conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info(
            f"CONVERSATION | created | id={conversation.id} | "
            f"user_id={user_id} | tenant_id={tenant_id} | project_id={project_id}"
        )
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


def _resolve_persona_names(agent_ids: set[int]) -> dict[int, str]:
    """Bulk lookup persona ID -> name. Funguje napric data_db / css_db hranici
    (Persona zije v css_db). Vraci pouze ID ktere existuji a jsou aktivni."""
    if not agent_ids:
        return {}
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Persona
    cs = get_core_session()
    try:
        rows = cs.query(Persona).filter(Persona.id.in_(agent_ids)).all()
        return {p.id: p.name for p in rows}
    finally:
        cs.close()


def _serialize_messages(messages: list[Message]) -> list[dict]:
    """Serializace listu Message ORM -> dict pro API. Pridava persona_name
    pres bulk JOIN s personas tabulkou (1 query pro N zprav) a created_at
    ve formatu ISO 8601 (frontend si format upravuje sam)."""
    agent_ids = {m.agent_id for m in messages if m.agent_id}
    persona_names = _resolve_persona_names(agent_ids)
    return [
        {
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "agent_id": m.agent_id,
            "persona_name": persona_names.get(m.agent_id) if m.agent_id else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


def get_last_conversation(user_id: int) -> dict | None:
    from modules.core.infrastructure.models_data import ConversationShare
    from sqlalchemy import or_

    # Tenant scope: bereme jen konverzace v aktualnim tenantu (last_active_tenant_id)
    # + legacy konverzace bez tenant_id (NULL). Bez tohoto by switch tenantu
    # neukoncil aktualne otevrenou konverzaci -- user by pokracoval v psani
    # do konverzace ze stareho tenantu, aniz by to vedel.
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        active_tenant_id = u.last_active_tenant_id if u else None
    finally:
        cs.close()

    session = get_data_session()
    try:
        q = session.query(Conversation).filter_by(user_id=user_id, is_deleted=False)
        if active_tenant_id is not None:
            q = q.filter(or_(
                Conversation.tenant_id == active_tenant_id,
                Conversation.tenant_id.is_(None),   # legacy bez tenantu
            ))
        conversation = q.order_by(Conversation.id.desc()).first()
        if not conversation:
            return None

        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation.id)
            .order_by(Message.id)
            .all()
        )
        shares_count = (
            session.query(ConversationShare)
            .filter_by(conversation_id=conversation.id)
            .count()
        )
        msg_rows = _serialize_messages(messages)
    finally:
        session.close()

    return {
        "conversation_id": conversation.id,
        "is_archived": bool(conversation.is_archived),
        "my_role": "owner",    # /last vraci vzdy moji konverzaci
        "shares_count": shares_count,
        "messages": msg_rows,
    }


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
        from modules.core.infrastructure.models_data import ConversationShare
        out: list[dict] = []
        for c in rows:
            msg_count = (
                session.query(Message)
                .filter_by(conversation_id=c.id)
                .count()
            )
            shares_count = (
                session.query(ConversationShare)
                .filter_by(conversation_id=c.id)
                .count()
            )
            out.append({
                "id": c.id,
                "title": _conversation_title(session, c),
                "tenant_id": c.tenant_id,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "message_count": msg_count,
                "shares_count": shares_count,
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
    Přístup: vlastník (Conversation.user_id == user_id) NEBO sdílený user
    (ConversationShare záznam). Shared readonly -> frontend disable send.

    Vrací None pokud user nemá žádný přístup (frontend interpretuje jako 404).
    """
    from modules.core.infrastructure.models_data import ConversationShare
    session = get_data_session()
    try:
        conversation = (
            session.query(Conversation)
            .filter_by(id=conversation_id, is_deleted=False)
            .first()
        )
        if not conversation:
            return None

        # Oprávnění: vlastník nebo shared
        my_role: str | None = None
        if conversation.user_id == user_id:
            my_role = "owner"
        else:
            share = (
                session.query(ConversationShare)
                .filter_by(conversation_id=conversation.id, shared_with_user_id=user_id)
                .first()
            )
            if share:
                my_role = f"shared_{share.access_level}"
        if my_role is None:
            return None

        messages = (
            session.query(Message)
            .filter_by(conversation_id=conversation.id)
            .order_by(Message.id)
            .all()
        )
        # Kolik user pushe tuhle konverzaci sdileno (pro owner banner)
        shares_count = (
            session.query(ConversationShare)
            .filter_by(conversation_id=conversation.id)
            .count()
        )
        # Zachyt atributy pred close (DetachedInstanceError prevention)
        conv_id_val = conversation.id
        conv_is_archived = bool(conversation.is_archived)
        conv_owner_id = conversation.user_id
        msg_rows = _serialize_messages(messages)
    finally:
        session.close()

    # Owner jmeno (pro shared viewer -- "Sdileno od X")
    owner_name: str | None = None
    if my_role != "owner":
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            owner = cs.query(User).filter_by(id=conv_owner_id).first()
            if owner:
                owner_name = " ".join(filter(None, [owner.first_name, owner.last_name])).strip() or (owner.short_name or f"#{owner.id}")
        finally:
            cs.close()

    return {
        "conversation_id": conv_id_val,
        "is_archived": conv_is_archived,
        "my_role": my_role,
        "owner_name": owner_name,
        "shares_count": shares_count,
        "messages": msg_rows,
    }
