"""
DM service — business logika user↔user chatu.

Pravidla MVP:
  - DM může vzniknout jen mezi usery ve stejném tenantu
  - Cílový user musí mít status 'active' nebo 'pending' (disabled = archiv)
  - Na dvojici userů je nejvýš jedna DM konverzace (vynuceno partial unique indexem)
  - AI se do DM nevolá
  - Zprávy se ukládají jen jednou (ne mirror)
"""
from core.logging import get_logger
from modules.conversation.infrastructure import dm_repository as dm_repo
from modules.conversation.infrastructure.repository import save_message

logger = get_logger("conversation.dm_service")


# ── CUSTOM ERRORS ────────────────────────────────────────────────────────

class DMError(Exception):
    """Základní business chyba DM vrstvy."""


class TargetUserNotFound(DMError):
    pass


class TargetUserDisabled(DMError):
    pass


class TenantMismatch(DMError):
    pass


class NotParticipant(DMError):
    pass


class SelfChatNotAllowed(DMError):
    pass


# ── START ────────────────────────────────────────────────────────────────

def start_dm(requester_user_id: int, target_user_id: int) -> dict:
    """
    Najde existující DM mezi (requester, target) nebo založí nový.
    Ověří:
      - target != requester
      - target existuje a není disabled
      - oba ve stejném tenantu (bere se last_active_tenant_id requestera)
    """
    if requester_user_id == target_user_id:
        raise SelfChatNotAllowed("Nelze zahájit DM sám se sebou.")

    target = dm_repo.get_user_basic(target_user_id)
    if not target:
        raise TargetUserNotFound(f"User {target_user_id} neexistuje.")
    if target["status"] == "disabled":
        raise TargetUserDisabled(f"User {target_user_id} je archivovaný.")

    requester_tenants = dm_repo.get_user_tenants(requester_user_id)
    if not requester_tenants:
        raise TenantMismatch("Requester nemá žádný tenant.")

    # MVP: bereme první společný tenant (v praxi = aktuální tenant uživatele).
    # Pozdější iterace by měla číst last_active_tenant_id z usera.
    tenant_id: int | None = None
    for t in requester_tenants:
        if dm_repo.are_users_in_same_tenant(requester_user_id, target_user_id, t):
            tenant_id = t
            break
    if tenant_id is None:
        raise TenantMismatch("Uživatelé nesdílí žádný tenant.")

    existing = dm_repo.find_dm_conversation(requester_user_id, target_user_id)
    if existing:
        logger.info(f"DM | reuse | conv={existing} | requester={requester_user_id} | target={target_user_id}")
        return {"conversation_id": existing, "created": False, "tenant_id": tenant_id}

    new_id = dm_repo.create_dm_conversation(requester_user_id, target_user_id, tenant_id)
    return {"conversation_id": new_id, "created": True, "tenant_id": tenant_id}


# ── SEND / LIST / FETCH / READ ───────────────────────────────────────────

def send_dm(requester_user_id: int, conversation_id: int, content: str) -> dict:
    """Pošle zprávu do DM konverzace. AI se NEVOLÁ."""
    content = (content or "").strip()
    if not content:
        raise DMError("Prázdná zpráva.")

    conv = dm_repo.get_conversation(conversation_id)
    if conv is None or conv.conversation_type != "dm":
        raise DMError("Konverzace neexistuje nebo není DM.")
    if not dm_repo.is_participant(conversation_id, requester_user_id):
        raise NotParticipant("Nemáš přístup k této konverzaci.")

    message_id = save_message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        author_type="human",
        author_user_id=requester_user_id,
        agent_id=None,
        message_type="text",
    )
    logger.info(f"DM | sent | conv={conversation_id} | from={requester_user_id} | msg={message_id}")
    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
    }


def list_dms(requester_user_id: int) -> list[dict]:
    """Vrátí seznam DM vláken pro daného usera, obohacený o info o protistraně."""
    raw = dm_repo.list_dm_conversations_for_user(requester_user_id)
    out: list[dict] = []
    for row in raw:
        counterparty = None
        if row["counterparty_user_id"]:
            counterparty = dm_repo.get_user_basic(row["counterparty_user_id"])
        out.append({
            **row,
            "counterparty": counterparty,
        })
    return out


def get_dm_detail(requester_user_id: int, conversation_id: int) -> dict:
    """Vrátí metadata DM konverzace + info o protistraně."""
    conv = dm_repo.get_conversation(conversation_id)
    if conv is None or conv.conversation_type != "dm":
        raise DMError("Konverzace neexistuje nebo není DM.")
    if not dm_repo.is_participant(conversation_id, requester_user_id):
        raise NotParticipant("Nemáš přístup k této konverzaci.")

    counterparty_id = dm_repo.get_counterparty_user_id(conversation_id, requester_user_id)
    counterparty = dm_repo.get_user_basic(counterparty_id) if counterparty_id else None

    return {
        "conversation_id": conv.id,
        "conversation_type": conv.conversation_type,
        "created_at": conv.created_at,
        "last_message_at": conv.last_message_at,
        "last_message_id": conv.last_message_id,
        "counterparty": counterparty,
    }


def fetch_dm_messages(
    requester_user_id: int,
    conversation_id: int,
    since_message_id: int | None = None,
    limit: int = 200,
) -> list[dict]:
    conv = dm_repo.get_conversation(conversation_id)
    if conv is None or conv.conversation_type != "dm":
        raise DMError("Konverzace neexistuje nebo není DM.")
    if not dm_repo.is_participant(conversation_id, requester_user_id):
        raise NotParticipant("Nemáš přístup k této konverzaci.")
    return dm_repo.get_dm_messages(conversation_id, since_message_id=since_message_id, limit=limit)


def mark_read(requester_user_id: int, conversation_id: int, last_read_message_id: int) -> None:
    conv = dm_repo.get_conversation(conversation_id)
    if conv is None or conv.conversation_type != "dm":
        raise DMError("Konverzace neexistuje nebo není DM.")
    ok = dm_repo.mark_dm_read(conversation_id, requester_user_id, last_read_message_id)
    if not ok:
        raise NotParticipant("Nemáš přístup k této konverzaci.")


# ── USER SEARCH ──────────────────────────────────────────────────────────

def _resolve_active_tenant(requester_user_id: int) -> int | None:
    """Vrátí user.last_active_tenant_id; fallback na první tenant z user_tenants."""
    from modules.core.infrastructure.models_core import User
    from core.database_core import get_core_session
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=requester_user_id).first()
        if u and u.last_active_tenant_id:
            return u.last_active_tenant_id
    finally:
        cs.close()
    tenants = dm_repo.get_user_tenants(requester_user_id)
    return tenants[0] if tenants else None


def search_users_for_dm(requester_user_id: int, query: str) -> list[dict]:
    """
    Hledá usery v aktuálním tenantu requestera (last_active_tenant_id).
    Sám sebe z výsledků vyhazuje.
    """
    tenant_id = _resolve_active_tenant(requester_user_id)
    if tenant_id is None:
        return []
    raw = dm_repo.search_users_in_tenant(tenant_id, query, limit=20)
    return [u for u in raw if u["user_id"] != requester_user_id]


def list_users_for_dm(requester_user_id: int) -> list[dict]:
    """
    Vrátí seznam všech aktivních uživatelů v aktuálním tenantu requestera
    (bez fulltextu, pro UI dropdown 'dostupní lidé v tenantu').
    Sám sebe vynechává.
    """
    tenant_id = _resolve_active_tenant(requester_user_id)
    if tenant_id is None:
        return []
    return dm_repo.list_users_in_tenant(tenant_id, exclude_user_id=requester_user_id, limit=100)
