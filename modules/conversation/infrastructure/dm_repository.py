"""
DM (direct-message) repository — databázové operace pro user-to-user chat.

Záměrně odděleno od `repository.py`, aby AI chat a user↔user chat zůstaly
strukturálně oddělené i v kódu. Sdílené primitiva (save_message atd.)
zůstávají v repository.py.
"""
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserContact, UserTenant
from modules.core.infrastructure.models_data import (
    Conversation,
    ConversationParticipant,
    Message,
)

logger = get_logger("conversation.dm")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _pair(user_a: int, user_b: int) -> tuple[int, int]:
    """Uspořádaná dvojice (low, high) — pořadí userů je pro DM irelevantní."""
    return (user_a, user_b) if user_a < user_b else (user_b, user_a)


# ── LOOKUP & CREATE ───────────────────────────────────────────────────────

def find_dm_conversation(user_a: int, user_b: int) -> int | None:
    """Najde existující DM konverzaci pro dvojici userů; vrací id nebo None."""
    low, high = _pair(user_a, user_b)
    session = get_data_session()
    try:
        conv = (
            session.query(Conversation)
            .filter(
                Conversation.conversation_type == "dm",
                Conversation.dm_user_low_id == low,
                Conversation.dm_user_high_id == high,
                Conversation.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        return conv.id if conv else None
    finally:
        session.close()


def create_dm_conversation(creator_id: int, target_id: int, tenant_id: int) -> int:
    """
    Založí DM konverzaci mezi dvěma usery a vloží 2 participant řádky.
    Předpokládá, že volající ověřil, že konverzace ještě neexistuje a že uživatelé
    patří do stejného tenantu (viz dm_service.start_dm).
    """
    low, high = _pair(creator_id, target_id)
    session = get_data_session()
    try:
        conv = Conversation(
            user_id=creator_id,
            tenant_id=tenant_id,
            conversation_type="dm",
            interaction_mode="human",
            created_by_user_id=creator_id,
            dm_user_low_id=low,
            dm_user_high_id=high,
            title=None,
        )
        session.add(conv)
        session.flush()

        session.add_all([
            ConversationParticipant(
                conversation_id=conv.id,
                user_id=creator_id,
                participant_role="owner",
            ),
            ConversationParticipant(
                conversation_id=conv.id,
                user_id=target_id,
                participant_role="member",
            ),
        ])
        session.commit()
        session.refresh(conv)
        logger.info(
            f"DM | created | id={conv.id} | creator={creator_id} | target={target_id} | tenant={tenant_id}"
        )
        return conv.id
    finally:
        session.close()


# ── PARTICIPANT CHECKS ────────────────────────────────────────────────────

def is_participant(conversation_id: int, user_id: int) -> bool:
    """True pokud je user účastník DM konverzace."""
    session = get_data_session()
    try:
        exists = (
            session.query(ConversationParticipant.id)
            .filter_by(conversation_id=conversation_id, user_id=user_id)
            .first()
            is not None
        )
        return exists
    finally:
        session.close()


def get_conversation(conversation_id: int) -> Conversation | None:
    session = get_data_session()
    try:
        return session.query(Conversation).filter_by(id=conversation_id).first()
    finally:
        session.close()


def get_counterparty_user_id(conversation_id: int, me_user_id: int) -> int | None:
    """V DM konverzaci vrátí id druhého účastníka."""
    session = get_data_session()
    try:
        row = (
            session.query(ConversationParticipant.user_id)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id != me_user_id,
            )
            .first()
        )
        return row[0] if row else None
    finally:
        session.close()


# ── LIST ──────────────────────────────────────────────────────────────────

def list_dm_conversations_for_user(user_id: int) -> list[dict]:
    """
    Vrátí seznam DM vláken usera s:
      - conversation_id
      - counterparty_user_id
      - last_message_id / last_message_at
      - unread_count (messages.id > my_participant.last_read_message_id)
      - is_archived / is_muted (z mého participant rowu)
    Seřazené od nejaktuálnějšího.
    """
    data_session = get_data_session()
    try:
        # moje participant rows
        my_parts = (
            data_session.query(ConversationParticipant)
            .filter(ConversationParticipant.user_id == user_id)
            .all()
        )
        conv_ids = [p.conversation_id for p in my_parts]
        if not conv_ids:
            return []

        convs = {
            c.id: c
            for c in data_session.query(Conversation)
            .filter(
                Conversation.id.in_(conv_ids),
                Conversation.conversation_type == "dm",
                Conversation.is_deleted == False,  # noqa: E712
            )
            .all()
        }

        # counterparty pro každou konverzaci
        other_parts = (
            data_session.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id.in_(conv_ids),
                ConversationParticipant.user_id != user_id,
            )
            .all()
        )
        counterparty_by_conv = {p.conversation_id: p.user_id for p in other_parts}

        # unread count per konverzaci
        unread_rows = (
            data_session.query(
                Message.conversation_id,
                func.count(Message.id),
            )
            .filter(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
            .all()
        )
        total_by_conv = {cid: cnt for cid, cnt in unread_rows}

        out: list[dict] = []
        for p in my_parts:
            conv = convs.get(p.conversation_id)
            if conv is None:
                continue
            last_read_id = p.last_read_message_id or 0
            # unread = messages.id > last_read_id — spočteme přímo filtrem
            unread_count = (
                data_session.query(func.count(Message.id))
                .filter(
                    Message.conversation_id == conv.id,
                    Message.id > last_read_id,
                    # zprávy, které user sám poslal, se mu nepočítají jako nepřečtené
                    (Message.author_user_id != user_id) | (Message.author_user_id.is_(None)),
                )
                .scalar()
                or 0
            )
            out.append({
                "conversation_id": conv.id,
                "counterparty_user_id": counterparty_by_conv.get(conv.id),
                "last_message_id": conv.last_message_id,
                "last_message_at": conv.last_message_at,
                "unread_count": unread_count,
                "is_archived": p.is_archived,
                "is_muted": p.is_muted,
            })

        out.sort(
            key=lambda r: (r["last_message_at"] or datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )
        return out
    finally:
        data_session.close()


# ── MESSAGES ──────────────────────────────────────────────────────────────

def get_dm_messages(
    conversation_id: int,
    since_message_id: int | None = None,
    limit: int = 200,
) -> list[dict]:
    """Vrátí zprávy DM konverzace (chronologicky). Volitelně jen novější než given id."""
    session = get_data_session()
    try:
        q = session.query(Message).filter_by(conversation_id=conversation_id)
        if since_message_id is not None:
            q = q.filter(Message.id > since_message_id)
        rows = q.order_by(Message.id.asc()).limit(limit).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "author_type": m.author_type,
                "author_user_id": m.author_user_id,
                "message_type": m.message_type,
                "created_at": m.created_at,
            }
            for m in rows
        ]
    finally:
        session.close()


# ── READ STATE ────────────────────────────────────────────────────────────

def mark_dm_read(conversation_id: int, user_id: int, last_read_message_id: int) -> bool:
    """
    Aktualizuje participant.last_read_message_id (nikdy nesnižuje — only monotonic up).
    Vrací True pokud participant existuje.
    """
    session = get_data_session()
    try:
        p = (
            session.query(ConversationParticipant)
            .filter_by(conversation_id=conversation_id, user_id=user_id)
            .first()
        )
        if not p:
            return False
        if p.last_read_message_id is None or last_read_message_id > p.last_read_message_id:
            p.last_read_message_id = last_read_message_id
            p.last_read_at = _now_utc()
            session.commit()
        return True
    finally:
        session.close()


# ── USERS (css_db) ────────────────────────────────────────────────────────

def get_user_tenants(user_id: int) -> list[int]:
    """Vrátí seznam tenant_id pro usera (aktivní)."""
    session = get_core_session()
    try:
        rows = (
            session.query(UserTenant.tenant_id)
            .filter_by(user_id=user_id)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def are_users_in_same_tenant(user_a: int, user_b: int, tenant_id: int) -> bool:
    session = get_core_session()
    try:
        a = (
            session.query(UserTenant.id)
            .filter_by(user_id=user_a, tenant_id=tenant_id)
            .first()
        )
        b = (
            session.query(UserTenant.id)
            .filter_by(user_id=user_b, tenant_id=tenant_id)
            .first()
        )
        return a is not None and b is not None
    finally:
        session.close()


def get_user_basic(user_id: int) -> dict | None:
    """Minimální info o userovi pro UI (jméno, status, primární email)."""
    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        primary = (
            session.query(UserContact)
            .filter_by(user_id=user_id, contact_type="email", is_primary=True, status="active")
            .first()
        )
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "status": user.status,
            "email": primary.contact_value if primary else None,
        }
    finally:
        session.close()


def list_users_in_tenant(tenant_id: int, exclude_user_id: int | None = None, limit: int = 100) -> list[dict]:
    """
    Vrátí všechny aktivní/pending uživatele v daném tenantu (bez fulltextu).
    Pro UI dropdown 'dostupní lidé v tenantu' v DM view.
    Excluduje sebe (exclude_user_id) — nemá smysl si chatovat sám se sebou.
    """
    session = get_core_session()
    try:
        tenant_user_ids = [
            r[0] for r in session.query(UserTenant.user_id).filter_by(tenant_id=tenant_id).all()
        ]
        if exclude_user_id is not None:
            tenant_user_ids = [uid for uid in tenant_user_ids if uid != exclude_user_id]
        if not tenant_user_ids:
            return []

        emails = {
            row[0]: row[1]
            for row in session.query(UserContact.user_id, UserContact.contact_value)
            .filter(
                UserContact.user_id.in_(tenant_user_ids),
                UserContact.contact_type == "email",
                UserContact.is_primary == True,  # noqa: E712
                UserContact.status == "active",
            )
            .all()
        }
        for row in session.query(UserContact.user_id, UserContact.contact_value).filter(
            UserContact.user_id.in_(tenant_user_ids),
            UserContact.contact_type == "email",
            UserContact.status == "active",
        ):
            emails.setdefault(row[0], row[1])

        users = (
            session.query(User)
            .filter(
                User.id.in_(tenant_user_ids),
                User.status.in_(("active", "pending")),
            )
            .order_by(User.first_name.asc().nullslast(), User.last_name.asc().nullslast())
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": emails.get(u.id),
                "status": u.status,
            }
            for u in users
        ]
    finally:
        session.close()


def search_users_in_tenant(tenant_id: int, query: str, limit: int = 20) -> list[dict]:
    """
    Hledá usery v daném tenantu podle jména, příjmení nebo emailu (ilike).
    - Query se rozdělí na tokeny (whitespace). Každý token musí sedět
      alespoň v jednom poli (first_name / last_name / email) — AND přes tokeny,
      OR přes pole. Tím zvládneme dotazy typu "Klára Vlková".
    - Vrací jen active/pending; disabled (archiv) je vynechán.
    - Diakritika: ILIKE v Postgres není accent-insensitive. Pro správnou
      shodu zadávej s diakritikou, případně v budoucnu nasadit rozšíření
      `unaccent`.
    """
    if not query or len(query.strip()) < 2:
        return []
    tokens = [t for t in query.strip().split() if t]
    if not tokens:
        return []

    session = get_core_session()
    try:
        # usery z tenantu
        tenant_user_ids = [
            r[0] for r in session.query(UserTenant.user_id).filter_by(tenant_id=tenant_id).all()
        ]
        if not tenant_user_ids:
            return []

        # map user_id -> primary email (pro hledání i výstup)
        emails = {
            row[0]: row[1]
            for row in session.query(UserContact.user_id, UserContact.contact_value)
            .filter(
                UserContact.user_id.in_(tenant_user_ids),
                UserContact.contact_type == "email",
                UserContact.is_primary == True,  # noqa: E712
                UserContact.status == "active",
            )
            .all()
        }
        # když user nemá primary, vezmi aspoň první aktivní email
        for row in session.query(UserContact.user_id, UserContact.contact_value).filter(
            UserContact.user_id.in_(tenant_user_ids),
            UserContact.contact_type == "email",
            UserContact.status == "active",
        ):
            emails.setdefault(row[0], row[1])

        candidates = (
            session.query(User)
            .filter(
                User.id.in_(tenant_user_ids),
                User.status.in_(("active", "pending")),
            )
            .all()
        )

        def user_matches(u: User) -> bool:
            fields = [
                (u.first_name or "").lower(),
                (u.last_name or "").lower(),
                (emails.get(u.id) or "").lower(),
            ]
            for tok in tokens:
                t = tok.lower()
                if not any(t in f for f in fields):
                    return False
            return True

        results: list[dict] = []
        for u in candidates:
            if user_matches(u):
                results.append({
                    "user_id": u.id,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "email": emails.get(u.id),
                    "status": u.status,
                })
                if len(results) >= limit:
                    break
        return results
    finally:
        session.close()
