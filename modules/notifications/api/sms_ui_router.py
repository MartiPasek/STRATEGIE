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

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.notifications.application import sms_service
from modules.notifications.application.sms_service import SmsValidationError

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
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    rows = sms_service.list_outbox_for_ui(
        persona_id=persona_id,
        tenant_id=tenant_id,
        limit=limit,
    )
    return {"items": rows, "persona_id": persona_id}


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
