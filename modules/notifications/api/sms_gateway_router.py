"""
Gateway API pro Android SMS bridge (capcom6/android-sms-gateway a kompatibilni).

Auth: shared secret v hlavicce `X-Gateway-Key`. Porovnavame s
settings.sms_gateway_key (konstantni-time compare). Zadne cookies/sessions --
tenhle router je pro MACHINE-TO-MACHINE, ne pro usery.

Endpointy:
    GET  /api/v1/sms/gateway/outbox             -- stahni pending SMS (FIFO)
    POST /api/v1/sms/gateway/outbox/{id}/sent   -- potvrdit odeslani
    POST /api/v1/sms/gateway/outbox/{id}/failed -- reportovat chybu

Bezpecnost:
    - Gateway key MUSI byt min. 32 znaku (jinak router endpointy rejectuje)
    - V .env pouzivej dlouhy random: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
    - Klic nikdy necommituj do kodu, jen do .env (gitignored)
"""
from __future__ import annotations
import hmac
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from core.config import settings
from core.logging import get_logger
from modules.notifications.application.sms_service import (
    list_pending,
    mark_sent,
    mark_failed,
    mark_claimed,
)

logger = get_logger("notifications.sms_gateway")

router = APIRouter(prefix="/api/v1/sms/gateway", tags=["sms-gateway"])

# Minimum gateway key length -- brzda proti slabym klicum nebo
# prazdnemu .env v dev kdy nekdo omylem otevre port.
_MIN_KEY_LEN = 32


def _require_gateway_key(req: Request, x_gateway_key: str | None) -> None:
    """
    Overeni shared secretu v hlavicce X-Gateway-Key. Constant-time compare
    aby se nedal klic tahat timing attackem.
    Loguje zdrojovou IP pri selhani pro audit.
    """
    if not settings.sms_enabled:
        raise HTTPException(503, "SMS gateway is disabled (SMS_ENABLED=false)")

    expected = settings.sms_gateway_key or ""
    if len(expected) < _MIN_KEY_LEN:
        logger.error(
            f"SMS | gateway | rejected | reason=weak_or_missing_key "
            f"| expected_len={len(expected)} "
            f"(nastav SMS_GATEWAY_KEY min {_MIN_KEY_LEN} znaku)"
        )
        raise HTTPException(503, "SMS gateway key not configured")

    provided = (x_gateway_key or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        client_ip = req.client.host if req.client else "unknown"
        logger.warning(
            f"SMS | gateway | rejected | reason=bad_key | client_ip={client_ip}"
        )
        raise HTTPException(401, "invalid gateway key")


# ── Schemas ────────────────────────────────────────────────────────────────

class OutboxItem(BaseModel):
    id: int
    to_phone: str
    body: str
    purpose: str
    attempts: int
    created_at: str | None


class OutboxResponse(BaseModel):
    items: list[OutboxItem]
    count: int


class FailedReport(BaseModel):
    error: str | None = Field(None, max_length=2000)


# ── Endpointy ──────────────────────────────────────────────────────────────

@router.get("/outbox", response_model=OutboxResponse)
def get_outbox(
    req: Request,
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
    limit: int = 50,
) -> OutboxResponse:
    """
    Android telefon sem pulluje pending SMS.

    Doporuceny polling interval: 10-30 sekund.
    Server vrati FIFO serazeno od nejstarsich.
    """
    _require_gateway_key(req, x_gateway_key)

    if limit < 1 or limit > 200:
        raise HTTPException(400, "limit must be 1..200")

    items = list_pending(limit=limit)

    # Oznac, ze telefon tyto IDs stahl (claimed_at). Informativni,
    # status zustava 'pending' dokud telefon nepotvrdi.
    if items:
        mark_claimed([it["id"] for it in items])

    return OutboxResponse(
        items=[OutboxItem(**it) for it in items],
        count=len(items),
    )


@router.post("/outbox/{outbox_id}/sent")
def post_sent(
    outbox_id: int,
    req: Request,
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
) -> dict:
    """Telefon potvrzuje uspesne odeslani."""
    _require_gateway_key(req, x_gateway_key)
    ok = mark_sent(outbox_id)
    if not ok:
        raise HTTPException(404, f"sms_outbox id={outbox_id} not found")
    return {"ok": True, "id": outbox_id, "status": "sent"}


@router.post("/outbox/{outbox_id}/failed")
def post_failed(
    outbox_id: int,
    req: Request,
    body: FailedReport = FailedReport(),
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
) -> dict:
    """Telefon reportuje selhani odeslani (rate limit, SIM, ...)."""
    _require_gateway_key(req, x_gateway_key)
    ok = mark_failed(outbox_id, error=body.error)
    if not ok:
        raise HTTPException(404, f"sms_outbox id={outbox_id} not found")
    return {"ok": True, "id": outbox_id, "status": "failed"}
