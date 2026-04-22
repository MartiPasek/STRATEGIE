"""
Email UI router -- endpointy pro frontend (email modal).
Base: /api/v1/email/ui

Paralelni struktura k sms_ui_router. Hlavni rozdil:
  - "suggest-reply" endpoint -- manualni AI task trigger (SMS ma auto-task,
    email ma opt-in). Viz PR3 scope: uzivatel klika "Navrhni odpoved" u emailu.
  - outbox je persona-scoped (kazda persona ma vlastni EWS kanal), ne
    tenant-scoped.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.notifications.application import email_inbox_service
from modules.notifications.application.email_inbox_service import (
    EmailInboxValidationError,
)
from modules.notifications.application.email_service import (
    EmailAuthError, EmailSendError, EmailNoUserChannelError,
)


class _ReplyRequest(BaseModel):
    body: str = Field(min_length=1, max_length=50000)


logger = get_logger("email_ui.api")

router = APIRouter(prefix="/api/v1/email/ui", tags=["email-ui"])


# ── Auth helper ────────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _get_tenant_for_user(user_id: int) -> int | None:
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return u.last_active_tenant_id if u else None
    finally:
        cs.close()


# ── Endpointy ──────────────────────────────────────────────────────────────

@router.get("/inbox")
def get_inbox(
    req: Request,
    persona_id: int,
    filter: str = "new",        # 'new' | 'processed'
    limit: int = 50,
):
    """
    List prichozich emailu pro tab 'Prichozi' / 'Zpracovane'.
    """
    _get_uid(req)
    try:
        rows = email_inbox_service.list_inbox_for_ui(
            persona_id=persona_id,
            filter_mode=filter,
            limit=limit,
        )
    except EmailInboxValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": rows, "filter": filter, "persona_id": persona_id}


@router.get("/outbox")
def get_outbox(
    req: Request,
    persona_id: int | None = None,
    limit: int = 50,
):
    """
    List odchozich emailu pro tab 'Odeslane'. Filtrujeme per-persona +
    tenant. Zobrazuje vsechny statusy (pending / sent / failed).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    rows = email_inbox_service.list_outbox_for_ui(
        persona_id=persona_id,
        tenant_id=tenant_id,
        limit=limit,
    )
    return {"items": rows, "persona_id": persona_id}


@router.post("/inbox/{email_id}/mark-read")
def mark_read_endpoint(email_id: int, req: Request):
    """
    Oznaci email jako precteny (read_at = now). Pouziva se kdyz user rozklikne
    detail v UI -- badge v hlavicce klesne.
    """
    _get_uid(req)
    result = email_inbox_service.mark_read(email_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Email id={email_id} neexistuje.")
    return {"ok": True, **result}


@router.post("/inbox/{email_id}/mark-processed")
def mark_processed(email_id: int, req: Request):
    """
    Manualni presun emailu do 'Zpracovane'. Bez kontextu tasku -- pouziva se
    na "ok, videl jsem, nic dalsiho s tim nedelam".
    """
    _get_uid(req)
    result = email_inbox_service.mark_inbox_processed(email_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Email id={email_id} neexistuje.")
    return {"ok": True, **result}


@router.post("/inbox/{email_id}/suggest-reply")
def suggest_reply_endpoint(email_id: int, req: Request):
    """
    Manualni AI task trigger -- vytvori task nad timto emailem, worker
    pote vygeneruje draft odpovedi. UI muze nasledne pollovat
    GET /inbox/{id}/draft dokud se result_summary nenaplni.

    Pozor: endpoint je non-blocking -- vraci okamzite info o vytvorenem
    tasku, ne hotovy draft. Draft se picknuje samostatnym GET /draft.
    """
    _get_uid(req)
    try:
        result = email_inbox_service.suggest_reply(email_id)
    except EmailInboxValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, **result}


@router.get("/inbox/{email_id}/draft")
def get_draft(email_id: int, req: Request):
    """
    Vrati nejnovejsi AI draft odpovedi z tasku nad timto emailem (pokud existuje).
    UI pro prefill reply textarea.
    """
    _get_uid(req)
    return email_inbox_service.get_draft_for_inbox(email_id)


@router.post("/inbox/{email_id}/reply")
def reply_to_email(email_id: int, body: _ReplyRequest, req: Request):
    """
    Odpoved na prichozi email:
      - queue_email() -> email_outbox (worker odesle pres EWS)
      - mark email_inbox.processed_at
      - cancel open tasku nad timto emailem
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    try:
        result = email_inbox_service.reply_to_inbox(
            inbox_id=email_id,
            body=body.body,
            user_id=user_id,
            tenant_id=tenant_id,
        )
    except EmailInboxValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EmailAuthError, EmailSendError, EmailNoUserChannelError) as e:
        raise HTTPException(status_code=502, detail=f"Email nelze zaradit: {e}")
    return {"ok": True, **result}
