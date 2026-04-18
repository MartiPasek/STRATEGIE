"""
HTTP endpointy pro user↔user DM chat.

Auth: v MVP stejný mechanismus jako /chat — user_id z cookie `user_id`.
Později nahradit skutečným auth layerem.
"""
from fastapi import APIRouter, HTTPException, Query, Request

from core.logging import get_logger
from modules.conversation.api.dm_schemas import (
    DMDetailResponse,
    DMListItem,
    DMMessage,
    DMMessagesResponse,
    MarkReadRequest,
    SendDMRequest,
    SendDMResponse,
    StartDMRequest,
    StartDMResponse,
    UserLite,
    UserSearchResponse,
)
from modules.conversation.application import dm_service
from modules.conversation.application.dm_service import (
    DMError,
    NotParticipant,
    SelfChatNotAllowed,
    TargetUserDisabled,
    TargetUserNotFound,
    TenantMismatch,
)

logger = get_logger("conversation.dm.api")

router = APIRouter(prefix="/api/v1/dm", tags=["dm"])


def _require_user_id(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


def _map_dm_error(e: Exception) -> HTTPException:
    if isinstance(e, TargetUserNotFound):
        return HTTPException(status_code=404, detail=str(e))
    if isinstance(e, TargetUserDisabled):
        return HTTPException(status_code=409, detail=str(e))
    if isinstance(e, TenantMismatch):
        return HTTPException(status_code=403, detail=str(e))
    if isinstance(e, NotParticipant):
        return HTTPException(status_code=403, detail=str(e))
    if isinstance(e, SelfChatNotAllowed):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, DMError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail="Neznámá chyba DM vrstvy.")


# ── START ────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartDMResponse)
def start_dm_endpoint(body: StartDMRequest, req: Request) -> StartDMResponse:
    me = _require_user_id(req)
    try:
        result = dm_service.start_dm(me, body.target_user_id)
    except DMError as e:
        raise _map_dm_error(e)
    return StartDMResponse(conversation_id=result["conversation_id"], created=result["created"])


# ── LIST ─────────────────────────────────────────────────────────────────

@router.get("/list", response_model=list[DMListItem])
def list_dms_endpoint(req: Request) -> list[DMListItem]:
    me = _require_user_id(req)
    rows = dm_service.list_dms(me)
    return [
        DMListItem(
            conversation_id=r["conversation_id"],
            counterparty=UserLite(**r["counterparty"]) if r.get("counterparty") else None,
            last_message_id=r.get("last_message_id"),
            last_message_at=r.get("last_message_at"),
            unread_count=r.get("unread_count") or 0,
            is_archived=r.get("is_archived") or False,
            is_muted=r.get("is_muted") or False,
        )
        for r in rows
    ]


# ── DETAIL ───────────────────────────────────────────────────────────────

@router.get("/{conversation_id}", response_model=DMDetailResponse)
def dm_detail_endpoint(conversation_id: int, req: Request) -> DMDetailResponse:
    me = _require_user_id(req)
    try:
        info = dm_service.get_dm_detail(me, conversation_id)
    except DMError as e:
        raise _map_dm_error(e)
    return DMDetailResponse(
        conversation_id=info["conversation_id"],
        conversation_type=info["conversation_type"],
        counterparty=UserLite(**info["counterparty"]) if info.get("counterparty") else None,
        created_at=info.get("created_at"),
        last_message_at=info.get("last_message_at"),
        last_message_id=info.get("last_message_id"),
    )


# ── SEND ─────────────────────────────────────────────────────────────────

@router.post("/{conversation_id}/send", response_model=SendDMResponse)
def send_dm_endpoint(conversation_id: int, body: SendDMRequest, req: Request) -> SendDMResponse:
    me = _require_user_id(req)
    try:
        result = dm_service.send_dm(me, conversation_id, body.content)
    except DMError as e:
        raise _map_dm_error(e)
    return SendDMResponse(**result)


# ── FETCH MESSAGES ───────────────────────────────────────────────────────

@router.get("/{conversation_id}/messages", response_model=DMMessagesResponse)
def dm_messages_endpoint(
    conversation_id: int,
    req: Request,
    since_message_id: int | None = Query(default=None, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
) -> DMMessagesResponse:
    me = _require_user_id(req)
    try:
        msgs = dm_service.fetch_dm_messages(
            me, conversation_id, since_message_id=since_message_id, limit=limit
        )
    except DMError as e:
        raise _map_dm_error(e)
    return DMMessagesResponse(
        conversation_id=conversation_id,
        messages=[DMMessage(**m) for m in msgs],
    )


# ── READ STATE ───────────────────────────────────────────────────────────

@router.post("/{conversation_id}/read")
def mark_dm_read_endpoint(conversation_id: int, body: MarkReadRequest, req: Request) -> dict:
    me = _require_user_id(req)
    try:
        dm_service.mark_read(me, conversation_id, body.last_read_message_id)
    except DMError as e:
        raise _map_dm_error(e)
    return {"ok": True}


# ── USER SEARCH (pro výběr protistrany) ──────────────────────────────────

@router.get("/_users/search", response_model=UserSearchResponse)
def search_users_endpoint(
    req: Request,
    q: str = Query(min_length=2, max_length=100),
) -> UserSearchResponse:
    """
    Vyhledávání uživatelů v rámci tenantu requestera, pro výběr protistrany v DM.
    Umístěno pod /dm/_users/search, aby to zůstalo v doméně DM modulu (MVP).
    """
    me = _require_user_id(req)
    results = dm_service.search_users_for_dm(me, q)
    return UserSearchResponse(results=[UserLite(**u) for u in results])
