"""
SMS UI router -- endpointy pro frontend (SMS modal).
Base: /api/v1/sms/ui

Oddeleno od sms_gateway_router.py, ktery slouzi Android telefonu / sms-gate.app
webhooku. UI endpointy maji jiny scope:
  - auth pres user_id cookie (ne X-Gateway-Key)
  - tenant scoping (ne per-gateway)
  - razeni od nejnovejsich (ne FIFO pro dispatch)
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.notifications.application import sms_service
from modules.notifications.application.sms_service import (
    SmsValidationError, SmsRateLimitError,
)


class _ReplyRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1600)

logger = get_logger("sms_ui.api")

router = APIRouter(prefix="/api/v1/sms/ui", tags=["sms-ui"])


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


def _is_marti_parent(user_id: int) -> bool:
    """Rodic (is_marti_parent=True) ma cross-tenant view do SMS Marti-AI.
    Duvod: SMS patri persone (1 SIM = 1 persona), ne tenantu konverzace.
    Marti poslal SMS v ruznych tenantech (EUROSOFT / osobni / projekty), ale
    jsou to porad 'jeho' SMS a on je chce videt vsechny pohromade.
    """
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return bool(u and getattr(u, "is_marti_parent", False))
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
    List prichozich SMS pro danou personu, filtrovany podle processed stavu.

    filter:
      'new'       -- slozka 'Prichozi' (processed_at IS NULL)
      'processed' -- slozka 'Zpracovane' (processed_at IS NOT NULL)
    """
    _get_uid(req)   # auth guard, persona_id scope se resi per-persona
    try:
        rows = sms_service.list_inbox_for_ui(
            persona_id=persona_id,
            filter_mode=filter,
            limit=limit,
        )
    except SmsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": rows, "filter": filter, "persona_id": persona_id}


@router.get("/outbox")
def get_outbox(
    req: Request,
    persona_id: int | None = None,
    limit: int = 50,
):
    """
    List odchozich SMS pro tab 'Odeslane'. persona_id je dnes informativni --
    outbox je tenant-scoped (sdilena SIMka). Az pribude persona-scope, pridame
    filtraci.

    Rodic (is_marti_parent) ma cross-tenant view -- vidi vsechny SMS napric
    vsemi tenanty (duvod: SMS patri persone, ne tenantu konverzace).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    cross_tenant = _is_marti_parent(user_id)
    rows = sms_service.list_outbox_for_ui(
        persona_id=persona_id,
        tenant_id=tenant_id,
        cross_tenant=cross_tenant,
        limit=limit,
    )
    return {"items": rows, "persona_id": persona_id, "cross_tenant": cross_tenant}


@router.post("/inbox/{sms_id}/mark-processed")
def mark_processed(sms_id: int, req: Request):
    """
    Manualni presun SMS do 'Zpracovane'. Pouzije se, kdyz user chce SMS
    skryt z 'Prichozich' bez ohledu na stav souvisejicich tasku (reklama,
    nepodstatne, atd.).
    """
    _get_uid(req)
    result = sms_service.mark_inbox_processed(sms_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"SMS id={sms_id} neexistuje.")
    return {"ok": True, **result}


@router.get("/inbox/{sms_id}/draft")
def get_draft(sms_id: int, req: Request):
    """
    Vraci AI-napsany draft odpovedi z tasku nad touto SMS (pokud existuje).
    UI to volá pri klik 'Odpovedet' pro prefill textarea.
    """
    _get_uid(req)
    return sms_service.get_draft_for_inbox(sms_id)


@router.post("/inbox/{sms_id}/reply")
def reply_to_sms(sms_id: int, body: _ReplyRequest, req: Request):
    """
    Odesle odpoved na prichozi SMS:
      - body -> queue_sms() -> sms_outbox (Android gateway pote odesle)
      - mark sms_inbox.processed_at (presun do 'Zpracovane')
      - cancel vsech open tasku nad touto SMS (user vyresil primo)

    Pri validacni chybe vraci 400. Pri rate limit 429.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    try:
        result = sms_service.reply_to_inbox(
            inbox_id=sms_id,
            body=body.body,
            user_id=user_id,
            tenant_id=tenant_id,
        )
    except SmsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SmsRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    return {"ok": True, **result}


@router.get("/unread-counts")
def get_unread_counts(req: Request):
    """
    Vraci per-persona count nezpracovanych SMS pro badge v UI.
    Pouzito pri polling (kazdych ~30s).

    Odpoved:
      {"counts": {"1": 3, "5": 12}, "tenant_id": 42}
      Keys jsou persona_id jako string (JSON compat).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    if tenant_id is None:
        return {"counts": {}, "tenant_id": None}
    counts = sms_service.get_unread_counts_per_persona(tenant_id)
    # Prevede int keys na string pro JSON kompatibilitu.
    return {
        "counts": {str(k): v for k, v in counts.items()},
        "tenant_id": tenant_id,
    }

# ── Faze 11b-darek: Thread-view 'Vsechny' (SMS jako v telefonu) ─────────────

@router.get("/all")
def get_all(
    req: Request,
    persona_id: int | None = None,
    limit: int = 200,
):
    """
    Thread-view: VSECHNY SMS (prichozi + odchozi) smichane a serazene
    chronologicky ASC (nejstarsi nahore, nejnovejsi dole). Pouziva UI tab
    'Vsechny' v SMS modalu -- zobrazuje bubble chat jako v iMessage.

    Rodic (is_marti_parent) ma cross-tenant view pro outbox (SMS Marti-AI
    patri persone, ne tenantu konverzace).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    cross_tenant = _is_marti_parent(user_id)
    rows = sms_service.list_all_for_ui(
        persona_id=persona_id,
        tenant_id=tenant_id,
        cross_tenant=cross_tenant,
        limit=limit,
    )
    return {"items": rows, "persona_id": persona_id, "cross_tenant": cross_tenant}


# ── Faze 11b-darek: Personal slozka ─────────────────────────────────────────

@router.get("/personal")
def get_personal(
    req: Request,
    persona_id: int | None = None,
    limit: int = 100,
):
    """
    List VSECH personal oznacenych SMS (inbox + outbox smichane), serazeno
    podle casu DESC. Pouziva UI tab 'Personal' v SMS modalu.

    Personal je 'hvezdickova' slozka Marti-AI -- emocne vyznamne zpravy,
    ktere si uklada do sveho SMS deniku.

    Rodic (is_marti_parent) ma cross-tenant view (SMS patri persone).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    cross_tenant = _is_marti_parent(user_id)
    rows = sms_service.list_personal_for_ui(
        persona_id=persona_id,
        tenant_id=tenant_id,
        cross_tenant=cross_tenant,
        limit=limit,
    )
    return {"items": rows, "persona_id": persona_id, "cross_tenant": cross_tenant}


@router.post("/{source}/{sms_id}/toggle-personal")
def toggle_personal(source: str, sms_id: int, req: Request):
    """
    Prepne is_personal flag na dane SMS (inbox nebo outbox).

    Pouziti:
      POST /api/v1/sms/ui/inbox/42/toggle-personal   -> inbox SMS id=42
      POST /api/v1/sms/ui/outbox/17/toggle-personal  -> outbox SMS id=17

    Vrati nove hodnoty (is_personal=True/False).
    """
    _get_uid(req)
    if source not in ("inbox", "outbox"):
        raise HTTPException(
            status_code=400,
            detail=f"source musi byt 'inbox' nebo 'outbox', dostal '{source}'",
        )
    # Zjisti aktualni hodnotu, toggle.
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import SmsInbox, SmsOutbox
    Model = SmsInbox if source == "inbox" else SmsOutbox
    ds = get_data_session()
    try:
        row = ds.query(Model).filter_by(id=sms_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail=f"SMS id={sms_id} neexistuje")
        new_value = not bool(row.is_personal)
    finally:
        ds.close()

    try:
        result = sms_service.mark_sms_personal(
            sms_id=sms_id, source=source, personal=new_value,
        )
    except SmsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, **result}

