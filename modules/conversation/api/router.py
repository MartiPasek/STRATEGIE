from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.conversation.api.schemas import (
    ChatRequest, ChatResponse, LastConversationResponse, ConversationListItem,
)
from modules.conversation.application.service import chat
from modules.conversation.infrastructure.repository import (
    get_last_conversation, get_active_persona_name,
    list_conversations, load_conversation, set_conversation_flag,
    rename_conversation, list_archived_conversations,
)
from pydantic import BaseModel
from core.database_core import get_core_session
from modules.core.infrastructure.models_core import User, Tenant

logger = get_logger("conversation.api")

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


def _get_current_tenant_for_user(
    user_id: int | None,
) -> tuple[int | None, str | None, str | None, str | None]:
    """
    Vrátí (tenant_id, tenant_name, tenant_code, display_name) aktuálního
    tenantu usera. Display_name je z user_tenant_profiles pro daný tenant.
    """
    if not user_id:
        return None, None, None, None
    from modules.core.infrastructure.models_core import UserTenant, UserTenantProfile

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.last_active_tenant_id:
            return None, None, None, None
        tenant = session.query(Tenant).filter_by(id=user.last_active_tenant_id).first()
        if not tenant:
            return None, None, None, None
        # Display name z user_tenant_profiles
        display_name = None
        ut = (
            session.query(UserTenant)
            .filter_by(user_id=user_id, tenant_id=tenant.id)
            .first()
        )
        if ut:
            profile = (
                session.query(UserTenantProfile)
                .filter_by(user_tenant_id=ut.id)
                .first()
            )
            if profile:
                display_name = profile.display_name
        if not display_name:
            display_name = user.first_name or user.short_name
        return tenant.id, tenant.tenant_name, tenant.tenant_code, display_name
    finally:
        session.close()


def _get_current_project_for_user(
    user_id: int | None,
) -> tuple[int | None, str | None]:
    """
    Vrátí (project_id, project_name) aktuálního projektu usera.
    None/None pokud user nemá projekt (last_active_project_id = NULL),
    pokud projekt už neexistuje nebo je archivovaný.
    """
    if not user_id:
        return None, None
    from modules.core.infrastructure.models_core import Project

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.last_active_project_id:
            return None, None
        project = session.query(Project).filter_by(id=user.last_active_project_id).first()
        if not project or not project.is_active:
            return None, None
        return project.id, project.name
    finally:
        session.close()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    try:
        user_id_str = req.cookies.get("user_id")
        user_id = int(user_id_str) if user_id_str else None

        conversation_id, reply, summary_info = chat(
            conversation_id=request.conversation_id,
            user_message=request.text,
            user_id=user_id,
            preferred_persona_id=request.preferred_persona_id,
        )

        persona_name = get_active_persona_name(conversation_id)

        summary_notice: str | None = None
        switch_to_cid: int | None = None
        switch_to_dm_uid: int | None = None
        if summary_info:
            # summary_info je polyvalentni dict: ma message_count (summary),
            # switch_to_conversation_id (selekce z list_conversations), nebo
            # switch_to_dm_user_id (volba "Otevri DM" po list_users).
            cnt = summary_info.get("message_count")
            if cnt:
                summary_notice = f"⏳ Shrnul jsem {cnt} starších zpráv do historie."
            switch_to_cid = summary_info.get("switch_to_conversation_id")
            switch_to_dm_uid = summary_info.get("switch_to_dm_user_id")

        # Aktuální tenant po této zprávě (zachycuje i tenant switch v chatu)
        tenant_id, tenant_name, tenant_code, display_name = _get_current_tenant_for_user(user_id)

        # Aktuální projekt po této zprávě (zachycuje i project switch v chatu)
        project_id, project_name = _get_current_project_for_user(user_id)

        return ChatResponse(
            conversation_id=conversation_id,
            reply=reply,
            active_persona=persona_name,
            summary_notice=summary_notice,
            switch_to_conversation_id=switch_to_cid,
            switch_to_dm_user_id=switch_to_dm_uid,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tenant_code=tenant_code,
            display_name=display_name,
            project_id=project_id,
            project_name=project_name,
        )
    except Exception as e:
        logger.exception(f"Chat failed: {e}")
        raise HTTPException(status_code=503, detail="Chat service unavailable.")


@router.get("/last", response_model=LastConversationResponse | None)
def get_last(req: Request):
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        return None
    user_id = int(user_id_str)
    result = get_last_conversation(user_id)
    if not result:
        return None

    persona_name = get_active_persona_name(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
        is_archived=result.get("is_archived", False),
    )


@router.get("/list", response_model=list[ConversationListItem])
def list_user_conversations(req: Request):
    """
    Vrátí seznam AI konverzací usera pro UI sidebar (nejnovější první).
    Filtrováno podle aktivního tenantu (user.last_active_tenant_id) —
    Marti v Osobním vidí jen osobní konverzace, v EUROSOFTu jen firemní.
    Bez auth (cookie user_id) -> 401.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    # Aktivní tenant z DB (single source of truth, ne cookie — cookie
    # je optional a může být zastaralý po tenant switche).
    active_tenant_id: int | None = None
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u:
            active_tenant_id = u.last_active_tenant_id
    finally:
        cs.close()

    items = list_conversations(user_id, tenant_id=active_tenant_id)
    return [ConversationListItem(**i) for i in items]


def _get_user_id_from_cookie(req: Request) -> int:
    """Extrahuje a validuje user_id z cookie. Vyhodí 401 pokud chybí/neplatný."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


class RenameRequest(BaseModel):
    title: str


@router.patch("/{conversation_id}/rename")
def rename_user_conversation(conversation_id: int, body: RenameRequest, req: Request) -> dict:
    """
    Přejmenuje konverzaci. Prázdný title → vrátí se k auto-titlu z první zprávy.
    """
    user_id = _get_user_id_from_cookie(req)
    logger.info(f"RENAME | user={user_id} | conv={conversation_id} | new_title={body.title!r}")
    ok = rename_conversation(user_id, conversation_id, body.title)
    if not ok:
        logger.warning(f"RENAME | 404 | user={user_id} | conv={conversation_id} | (not owner / not found)")
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    logger.info(f"RENAME | OK | user={user_id} | conv={conversation_id}")
    return {"status": "renamed", "conversation_id": conversation_id, "title": (body.title or "").strip() or None}


@router.delete("/{conversation_id}")
def delete_user_conversation(conversation_id: int, req: Request) -> dict:
    """
    Soft-delete konverzace (set is_deleted=true). Konverzace zmizí ze
    sidebaru/dropdownu i z archivu, ale fyzicky zůstává v DB pro audit.
    """
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_deleted=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/{conversation_id}/archive")
def archive_user_conversation(conversation_id: int, req: Request) -> dict:
    """
    Archivace konverzace (set is_archived=true). Zmizí ze sidebaru,
    zůstane dostupná přes 'Můj archiv konverzací'.
    """
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_archived=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "archived", "conversation_id": conversation_id}


@router.post("/{conversation_id}/unarchive")
def unarchive_user_conversation(conversation_id: int, req: Request) -> dict:
    """Vrátí konverzaci z archivu zpět do hlavního sidebaru/dropdownu."""
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_archived=False)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "unarchived", "conversation_id": conversation_id}


@router.get("/list-archived", response_model=list[ConversationListItem])
def list_user_archived(req: Request):
    """
    Vrátí archivované AI konverzace usera (filtr podle aktivního tenantu),
    pro modal 'Můj archiv konverzací'.
    """
    user_id = _get_user_id_from_cookie(req)
    active_tenant_id: int | None = None
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u:
            active_tenant_id = u.last_active_tenant_id
    finally:
        cs.close()
    items = list_archived_conversations(user_id, tenant_id=active_tenant_id)
    return [ConversationListItem(**i) for i in items]


@router.get("/load/{conversation_id}", response_model=LastConversationResponse | None)
def load_user_conversation(conversation_id: int, req: Request):
    """
    Načte konkrétní konverzaci pro UI (klik v sidebaru).
    Vlastnictví ověřuje repository — 404 pokud user není vlastník.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")
    result = load_conversation(user_id, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    persona_name = get_active_persona_name(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
        is_archived=result.get("is_archived", False),
    )
