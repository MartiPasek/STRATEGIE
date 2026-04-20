"""
Conversation sharing service -- sdileni AI konverzaci mezi useri.

MVP: READ ONLY. Vlastnik konverzace sdili s dalsimi userami v jeho tenantu,
ti vidi historii (readonly). Write je mimo scope MVP (komplikace s append
zpravam -- kdo za koho pise? jak vypada vlastnikovi?).

Opravneni:
- Share / unshare: jen vlastnik konverzace (Conversation.user_id).
- View sdilene: vlastnik + shared_with_user_id ze share zaznamu.
- Target user pro sdileni musi byt aktivnim clenem stejneho tenantu jako vlastnik.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserTenant
from modules.core.infrastructure.models_data import Conversation, ConversationShare

logger = get_logger("conversation.share")


class ShareError(Exception):
    pass


def _assert_owner(session, conversation_id: int, user_id: int) -> Conversation:
    """Vraci Conversation pokud je user owner, jinak raise."""
    conv = session.query(Conversation).filter_by(id=conversation_id).first()
    if conv is None:
        raise ShareError("Konverzace neexistuje.")
    if conv.user_id != user_id:
        raise ShareError("Nejsi vlastnik teto konverzace, nemuzes ji sdilet.")
    if conv.is_deleted:
        raise ShareError("Konverzace je smazana.")
    return conv


def list_shares(*, user_id: int, conversation_id: int) -> list[dict]:
    """
    Seznam aktualnich sdileni konverzace. Jen owner vidi.
    """
    ds = get_data_session()
    try:
        _assert_owner(ds, conversation_id, user_id)
        rows = (
            ds.query(ConversationShare)
            .filter_by(conversation_id=conversation_id)
            .order_by(ConversationShare.id.asc())
            .all()
        )
        share_by_uid = {r.shared_with_user_id: r for r in rows}
    finally:
        ds.close()

    if not share_by_uid:
        return []

    # Obohacene o jmena z User table (css_db)
    cs = get_core_session()
    try:
        users = cs.query(User).filter(User.id.in_(share_by_uid.keys())).all()
        user_by_id = {u.id: u for u in users}
    finally:
        cs.close()

    out = []
    for uid, share in share_by_uid.items():
        u = user_by_id.get(uid)
        full_name = ""
        if u:
            full_name = " ".join(filter(None, [u.first_name, u.last_name])).strip() or (u.short_name or f"#{u.id}")
        out.append({
            "id": share.id,
            "conversation_id": share.conversation_id,
            "shared_with_user_id": uid,
            "shared_with_name": full_name or f"#{uid}",
            "access_level": share.access_level,
            "created_at": share.created_at,
        })
    return out


def add_share(
    *,
    user_id: int,
    conversation_id: int,
    target_user_id: int,
    access_level: str = "read",
) -> dict:
    """
    Sdili konverzaci s target user. Validace:
      - access_level musi byt read (MVP)
      - target musi byt aktivnim clenem stejneho tenantu
      - nesmi byt already shared (idempotentni -- vratime existujici)
      - nelze sdilet sam sobe
    """
    if access_level not in ("read", "write"):
        raise ShareError("access_level musi byt 'read' nebo 'write'.")
    # MVP: write zatim nepodporujeme
    if access_level == "write":
        raise ShareError("Write sdileni zatim neni implementovano, pouzij 'read'.")

    if target_user_id == user_id:
        raise ShareError("Nemuzes sdilet konverzaci sam se sebou.")

    # Owner check + nacteni konverzace pro tenant_id
    ds = get_data_session()
    try:
        conv = _assert_owner(ds, conversation_id, user_id)
        conv_tenant_id = conv.tenant_id
    finally:
        ds.close()

    # Target musi byt aktivni clen stejneho tenantu
    cs = get_core_session()
    try:
        target = cs.query(User).filter_by(id=target_user_id, status="active").first()
        if target is None:
            raise ShareError("Cilovy uzivatel neexistuje nebo neni aktivni.")
        if conv_tenant_id is not None:
            membership = (
                cs.query(UserTenant)
                .filter_by(
                    user_id=target_user_id,
                    tenant_id=conv_tenant_id,
                    membership_status="active",
                )
                .first()
            )
            if membership is None:
                raise ShareError(
                    "Cilovy uzivatel neni clenem tenantu teto konverzace. "
                    "Nejdriv ho pozvi do tenantu."
                )
        target_name = " ".join(filter(None, [target.first_name, target.last_name])).strip() or (target.short_name or f"#{target.id}")
    finally:
        cs.close()

    # Check duplicate + create
    ds = get_data_session()
    try:
        existing = (
            ds.query(ConversationShare)
            .filter_by(conversation_id=conversation_id, shared_with_user_id=target_user_id)
            .first()
        )
        if existing is not None:
            # Update access_level pokud se lisi (idempotentni upgrade/downgrade)
            if existing.access_level != access_level:
                existing.access_level = access_level
                ds.commit()
                logger.info(
                    f"SHARE | updated | conv={conversation_id} | target={target_user_id} | "
                    f"access={access_level}"
                )
            return {
                "id": existing.id,
                "conversation_id": conversation_id,
                "shared_with_user_id": target_user_id,
                "shared_with_name": target_name,
                "access_level": existing.access_level,
                "created_at": existing.created_at,
                "already_existed": True,
            }

        share = ConversationShare(
            conversation_id=conversation_id,
            project_id=conv.project_id if hasattr(conv, "project_id") else None,
            shared_with_user_id=target_user_id,
            access_level=access_level,
            created_at=datetime.now(timezone.utc),
        )
        ds.add(share)
        ds.commit()
        ds.refresh(share)
        logger.info(
            f"SHARE | created | conv={conversation_id} | "
            f"owner={user_id} | target={target_user_id} | access={access_level}"
        )
        return {
            "id": share.id,
            "conversation_id": conversation_id,
            "shared_with_user_id": target_user_id,
            "shared_with_name": target_name,
            "access_level": access_level,
            "created_at": share.created_at,
            "already_existed": False,
        }
    finally:
        ds.close()


def remove_share(*, user_id: int, conversation_id: int, share_id: int) -> bool:
    """Odebere sdileni. Jen owner."""
    ds = get_data_session()
    try:
        _assert_owner(ds, conversation_id, user_id)
        share = ds.query(ConversationShare).filter_by(id=share_id).first()
        if share is None or share.conversation_id != conversation_id:
            return False
        ds.delete(share)
        ds.commit()
        logger.info(f"SHARE | removed | id={share_id} | conv={conversation_id}")
        return True
    finally:
        ds.close()


def list_shared_with_me(*, user_id: int) -> list[dict]:
    """
    Seznam konverzaci sdilenych S uzivatelem (nikoli jeho vlastnich).
    Pouziva sidebar "Sdilene se mnou".
    Vraci per-item: conversation_id, title (preview), owner_name, access_level,
    shared_at.
    """
    ds = get_data_session()
    try:
        shares = (
            ds.query(ConversationShare, Conversation)
            .join(Conversation, Conversation.id == ConversationShare.conversation_id)
            .filter(
                ConversationShare.shared_with_user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
            .order_by(ConversationShare.id.desc())
            .all()
        )
        items = []
        owner_ids = set()
        for share, conv in shares:
            items.append({
                "share_id": share.id,
                "conversation_id": conv.id,
                "title": conv.title or f"Konverzace #{conv.id}",
                "access_level": share.access_level,
                "shared_at": share.created_at,
                "last_message_at": conv.last_message_at,
                "owner_user_id": conv.user_id,
            })
            if conv.user_id:
                owner_ids.add(conv.user_id)
    finally:
        ds.close()

    # Obohaceni o jmena vlastniku
    if owner_ids:
        cs = get_core_session()
        try:
            owners = cs.query(User).filter(User.id.in_(owner_ids)).all()
            owner_names = {}
            for u in owners:
                owner_names[u.id] = " ".join(filter(None, [u.first_name, u.last_name])).strip() or (u.short_name or f"#{u.id}")
        finally:
            cs.close()
        for item in items:
            item["owner_name"] = owner_names.get(item["owner_user_id"]) or f"#{item['owner_user_id']}"
    return items


def can_user_view_conversation(user_id: int, conversation_id: int) -> tuple[bool, str | None]:
    """
    Vrati (can_view, role). Role = 'owner' | 'shared_read' | 'shared_write' | None.
    Owner check + vyhledani share zaznamu.
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None or conv.is_deleted:
            return False, None
        if conv.user_id == user_id:
            return True, "owner"
        share = (
            ds.query(ConversationShare)
            .filter_by(conversation_id=conversation_id, shared_with_user_id=user_id)
            .first()
        )
        if share is None:
            return False, None
        role = f"shared_{share.access_level}"
        return True, role
    finally:
        ds.close()
