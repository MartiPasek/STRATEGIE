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
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from core.config import settings
from core.logging import get_logger
from modules.notifications.application.sms_service import (
    list_pending,
    mark_sent,
    mark_failed,
    mark_claimed,
    store_inbound_sms,
    store_phone_call,
    SmsValidationError,
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


# ── Inbound SMS ────────────────────────────────────────────────────────────

class InboxItem(BaseModel):
    from_phone: str = Field(..., description="Cislo odesilatele (ktery pisek nam)")
    body: str = Field(..., max_length=3200, description="Text SMS")
    # to_phone = na jakou SIMku to prislo; pro resolvovani persony. Volitelne
    # -- kdyz gateway app neposila, mame NULL a zaznam jde do globalniho inboxu.
    to_phone: str | None = Field(None, description="Nase SIMka (E.164)")
    received_at: str | None = Field(
        None,
        description=(
            "ISO 8601 timestamp kdy SMS prisla do telefonu. Pokud None, "
            "pouzijeme server time (kdy jsme dostali POST)."
        ),
    )
    meta: str | None = Field(None, description="Volitelny JSON / debug string")


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # fromisoformat umi i '+00:00' od Python 3.11+, tak jak S23/A3 posila
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


@router.post("/inbox")
def post_inbox(
    req: Request,
    body: InboxItem,
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
) -> dict:
    """
    Telefon sem pushuje prichozi SMS (capcom6 webhook / Tasker).
    Server ulozi do sms_inbox a resolvuje persona_id podle to_phone.
    """
    _require_gateway_key(req, x_gateway_key)
    try:
        result = store_inbound_sms(
            from_phone=body.from_phone,
            body=body.body,
            to_phone=body.to_phone,
            received_at=_parse_iso(body.received_at),
            meta=body.meta,
        )
    except SmsValidationError as e:
        raise HTTPException(400, f"validation: {e}")
    return {"ok": True, **result}


# ── Call log ───────────────────────────────────────────────────────────────

class CallEvent(BaseModel):
    peer_phone: str = Field(..., description="Druha strana hovoru (volajici nebo volany)")
    direction: str = Field(..., description="in | out | missed")
    started_at: str | None = Field(None, description="ISO 8601 kdy hovor zacal")
    duration_s: int | None = Field(None, ge=0, description="Trvani v sekundach; NULL pro missed")
    to_phone: str | None = Field(None, description="Nase SIMka, pro resolve persony")
    meta: str | None = Field(None)


@router.post("/calls")
def post_call(
    req: Request,
    body: CallEvent,
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
) -> dict:
    """
    Telefon (Tasker profil) sem pushuje zaznam hovoru. Server ulozi do phone_calls.
    """
    _require_gateway_key(req, x_gateway_key)
    try:
        result = store_phone_call(
            peer_phone=body.peer_phone,
            direction=body.direction,
            started_at=_parse_iso(body.started_at),
            duration_s=body.duration_s,
            to_phone=body.to_phone,
            meta=body.meta,
        )
    except SmsValidationError as e:
        raise HTTPException(400, f"validation: {e}")
    return {"ok": True, **result}


# ── sms-gate.app webhook adapter ───────────────────────────────────────────
# capcom6 cloud posila prichozi SMS v jinem payloadu nez nase interni
# /inbox endpointu. Tenhle endpoint prijme jejich format a prelozi ho.
# Konfigurace v sms-gate.app dashboardu:
#   URL     : https://app.strategie-system.com/api/v1/sms/gateway/inbox-webhook
#   Method  : POST
#   Headers : X-Gateway-Key: <nas SMS_GATEWAY_KEY>
#   Events  : sms:received   (optional: sms:delivered / sms:sent / sms:failed)

def _resolve_gateway_key(
    req: Request,
    x_gateway_key: str | None,
    query_key: str | None,
) -> None:
    """
    Overuje gateway key z X-Gateway-Key headeru NEBO `?key=` query param.
    Pouzite pro webhooky ze sluzeb co neumi custom headers (sms-gate.app).
    """
    if x_gateway_key:
        _require_gateway_key(req, x_gateway_key)
        return
    if query_key:
        _require_gateway_key(req, query_key)
        return
    # Neither provided
    _require_gateway_key(req, None)  # vyhodi 401


@router.post("/inbox-webhook")
async def post_inbox_webhook(
    req: Request,
    x_gateway_key: str | None = Header(default=None, alias="X-Gateway-Key"),
    key: str | None = None,   # ?key=... query param -- fallback pro sms-gate.app
) -> dict:
    """
    Webhook adapter pro sms-gate.app (capcom6 cloud).

    Ocekava payload typu:
      {
        "event": "sms:received" | "sms:delivered" | "sms:sent" | "sms:failed",
        "deviceId": "cdtGorl...",
        "payload": {
          "messageId": "...",
          "phoneNumber": "+420...",
          "simNumber": 1,
          "message": "text SMS",
          "receivedAt": "2026-04-21T14:30:00.000Z"
        }
      }

    Podporovane eventy:
      sms:received -- prichozi SMS, ulozi do sms_inbox
      mms:received -- prichozi MMS (dnes v CR defaultni format, RCS fallback)
      ostatni      -- jen logujeme pro delivery tracking v budoucnu

    Auth: X-Gateway-Key header NEBO ?key=... query param (sms-gate.app neumi
    custom headers). URL v sms-gate.app konfiguraci:
        https://app.strategie-system.com/api/v1/sms/gateway/inbox-webhook?key=<SMS_GATEWAY_KEY>
    """
    _resolve_gateway_key(req, x_gateway_key, key)

    try:
        raw = await req.json()
    except Exception as e:
        raise HTTPException(400, f"bad json: {e}")

    event = (raw.get("event") or "").lower()
    payload = raw.get("payload") or {}

    # Log CELY raw payload pro prvnich par zprav -- potrebujeme videt format MMS
    # ktery se muze lisit od SMS. Jakmile format potvrdime, muzeme odstranit.
    import json as _json
    logger.info(
        f"SMS | webhook | event={event} | raw_payload={_json.dumps(raw)[:1000]}"
    )

    if event in ("sms:received", "mms:received"):
        from_phone = payload.get("phoneNumber") or ""
        # MMS muze mit obsah v "message", "text", nebo i v "subject" / "parts"
        # -- sbirame permisivne, prvni neprazdny text vyhrava.
        message_text = (
            payload.get("message")
            or payload.get("text")
            or payload.get("subject")
            or ""
        )
        # Pro MMS mohou byt attachmenty -- zaznamename do meta, text vse co mame
        attachments = payload.get("attachments") or []
        if attachments and not message_text:
            message_text = f"[MMS s {len(attachments)} priloh]"

        received_at = _parse_iso(payload.get("receivedAt"))

        if not from_phone or not message_text:
            raise HTTPException(
                400,
                f"{event} requires phoneNumber and message/text/subject "
                f"(got: from={from_phone!r}, text={message_text!r})",
            )

        # to_phone -- pro MVP bereme SMS_FROM_NUMBER (nase SIM), az bude dual-SIM
        # musime resolvovat podle simNumber z payloadu.
        from core.config import settings as _s
        to_phone = _s.sms_from_number or None

        meta = _json.dumps({
            "event": event,
            "device_id": raw.get("deviceId"),
            "message_id": payload.get("messageId"),
            "sim_number": payload.get("simNumber"),
            "attachments_count": len(attachments) if attachments else 0,
        })

        try:
            result = store_inbound_sms(
                from_phone=from_phone,
                body=message_text,
                to_phone=to_phone,
                received_at=received_at,
                meta=meta,
            )
        except SmsValidationError as e:
            raise HTTPException(400, f"validation: {e}")

        logger.info(
            f"SMS | webhook | stored | event={event} | inbox_id={result['id']} | "
            f"from={from_phone} | len={len(message_text)}"
        )
        return {"ok": True, "stored": True, **result}

    # Jine eventy jen logujeme (sms:delivered / sms:sent / sms:failed apod.)
    logger.info(
        f"SMS | webhook | other_event={event} | device={raw.get('deviceId')} | "
        f"message_id={payload.get('messageId')}"
    )
    return {"ok": True, "stored": False, "event": event}
