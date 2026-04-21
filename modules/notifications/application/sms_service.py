"""
SMS service -- provider-agnostic interface pro odesilani SMS.

Architektura (pull model):
    STRATEGIE ---> sms_outbox  <---- poll HTTPS ---- Android telefon
                     ^                                      |
                     |                                      |
              queue_sms() zapisuje               posila SMS pres GSM
                                                           |
                                                 potvrzuje status

Tim, ze aplikace fyzicky SMS NEposila sama (to dela telefon), tak
AndroidGatewayProvider.send() je vlastne no-op a "send" = zapis
do outboxu. Telefon si pendingy sam stahne pres /gateway/outbox API.

Pro budouci providery (SMSEagle, Twilio) pujde stejnym interfacem:
  - implementace SmsProvider.send() posle primo pres jejich HTTP API
  - outbox muze zustat jako audit/retry queue, nebo se preskakuje

queue_sms() provadi:
  1. normalizaci telefonniho cisla (E.164)
  2. validaci (delka, format)
  3. rate limit check per user
  4. zapis do sms_outbox se status='pending'
"""
from __future__ import annotations
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import SmsOutbox

logger = get_logger("notifications.sms")


class SmsError(Exception):
    """Baseline chyba pro SMS operace (validation, rate limit, provider)."""


class SmsRateLimitError(SmsError):
    """User prekrocil rate limit (SMS_RATE_LIMIT_PER_USER_PER_HOUR)."""


class SmsValidationError(SmsError):
    """Neplatne telefonni cislo nebo prazdny body."""


# ── Phone number normalization ─────────────────────────────────────────────

_CZ_PREFIX = "+420"


def normalize_phone(raw: str) -> str:
    """
    Normalizace CZ telefonniho cisla do E.164 formatu.

    Akceptovatelne vstupy:
      "777180511"         -> "+420777180511"
      "+420777180511"     -> "+420777180511"
      "00420 777 180 511" -> "+420777180511"
      "+420 777-180-511"  -> "+420777180511"
      "420777180511"      -> "+420777180511"  (bez + hacky)

    Zahranicni cisla se zatim NEpodporuji -- raise SmsValidationError.
    Az bude treba, lze rozsirit.
    """
    if not raw:
        raise SmsValidationError("prazdne cislo")

    # Strip everything non-digit or +
    s = re.sub(r"[^\d+]", "", str(raw).strip())

    # "00420..." -> "+420..."
    if s.startswith("00"):
        s = "+" + s[2:]
    # "420..." (bez +) -> "+420..."
    elif s.startswith("420") and not s.startswith("+"):
        s = "+" + s
    # "777..." (9 cislic) -> "+420777..."
    elif not s.startswith("+"):
        if len(s) == 9 and s[0] in ("6", "7"):   # mobilni prefix CZ
            s = _CZ_PREFIX + s
        else:
            raise SmsValidationError(
                f"nepodporovany format cisla: {raw!r} "
                f"(ocekavam +420XXXXXXXXX nebo 9 cislic s mobilnim prefixem)"
            )

    # Po normalizaci musi byt +420 + 9 cislic
    if not (s.startswith(_CZ_PREFIX) and len(s) == 13 and s[1:].isdigit()):
        raise SmsValidationError(f"neplatne cislo po normalizaci: {s!r}")

    return s


# ── Rate limiting ──────────────────────────────────────────────────────────

def _count_recent_sms(ds, user_id: int, window_hours: int = 1) -> int:
    """Kolik SMS poslal user za poslednich `window_hours` hodin?"""
    if user_id is None:
        return 0
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    return (
        ds.query(SmsOutbox)
        .filter(SmsOutbox.user_id == user_id)
        .filter(SmsOutbox.created_at >= since)
        .count()
    )


# ── Provider interface ─────────────────────────────────────────────────────

class SmsProvider(ABC):
    """Abstract interface pro SMS provider (android gateway / smseagle / twilio)."""

    @abstractmethod
    def send(self, outbox_id: int, to_phone: str, body: str) -> bool:
        """
        Posle SMS a vrati True pri uspechu. Pro pull providery (android_gateway)
        je no-op -- telefon si to sam stahne pres outbox API. Pro push providery
        (twilio) udela HTTP POST primo.
        """
        ...


class AndroidGatewayProvider(SmsProvider):
    """
    Android telefon pulluje pres /api/v1/sms/gateway/outbox. send() je no-op,
    jen logne, ze zaznam ceka v outboxu.
    """

    def send(self, outbox_id: int, to_phone: str, body: str) -> bool:
        logger.info(
            f"SMS | queued | id={outbox_id} | to={to_phone} | "
            f"body_len={len(body)} | awaits android gateway poll"
        )
        return True


_provider_instance: SmsProvider | None = None


def get_provider() -> SmsProvider:
    """Singleton factory -- vrati aktualni provider podle settings.sms_provider."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    name = (settings.sms_provider or "android_gateway").lower()
    if name == "android_gateway":
        _provider_instance = AndroidGatewayProvider()
    else:
        raise SmsError(f"neznamy SMS provider: {name!r}")
    return _provider_instance


# ── Public API ─────────────────────────────────────────────────────────────

def queue_sms(
    to: str,
    body: str,
    purpose: str = "user_request",
    user_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    """
    Zaradi SMS do outboxu. Pokud SMS_ENABLED=false, bezpecne no-opne (warning).

    Args:
        to: telefonni cislo (libovolny CZ format, normalizujeme)
        body: text SMS (max 1600 znaku -- segmentace ale necharakterizujeme)
        purpose: user_request | notification | system
        user_id: kdo to inicoval (pro audit + rate limit)
        tenant_id: v kterem tenantu

    Returns:
        dict s outbox id + normalizovanym cislem + status:
        {
            "id": 42,
            "to_phone": "+420777180511",
            "status": "pending" | "disabled" | "failed",
            "message": "...",
        }

    Raises:
        SmsValidationError -- neplatny vstup
        SmsRateLimitError  -- user prekrocil rate limit
    """
    if not settings.sms_enabled:
        logger.warning(
            f"SMS | disabled | queue_sms called but SMS_ENABLED=false "
            f"| to={to!r} | purpose={purpose}"
        )
        return {
            "id": None,
            "to_phone": None,
            "status": "disabled",
            "message": "SMS are disabled (SMS_ENABLED=false)",
        }

    # Validace body
    body = (body or "").strip()
    if not body:
        raise SmsValidationError("prazdny body")
    if len(body) > 1600:
        raise SmsValidationError(f"body prilis dlouhy: {len(body)} znaku (max 1600)")

    # Normalizace cisla
    to_phone = normalize_phone(to)

    # Validace purpose
    if purpose not in ("user_request", "notification", "system"):
        raise SmsValidationError(f"neznamy purpose: {purpose!r}")

    ds = get_data_session()
    try:
        # Rate limit (jen pro user_request, ne pro system/notifikace)
        if user_id is not None and purpose == "user_request":
            recent = _count_recent_sms(ds, user_id, window_hours=1)
            if recent >= settings.sms_rate_limit_per_user_per_hour:
                raise SmsRateLimitError(
                    f"user_id={user_id} poslal {recent} SMS za posledni hodinu "
                    f"(limit {settings.sms_rate_limit_per_user_per_hour})"
                )

        # Zapis do outboxu
        row = SmsOutbox(
            user_id=user_id,
            tenant_id=tenant_id,
            to_phone=to_phone,
            body=body,
            purpose=purpose,
            status="pending",
            attempts=0,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)

        # Notify provider (android gateway = no-op log, ostatni = primy send)
        provider = get_provider()
        provider.send(row.id, to_phone, body)

        return {
            "id": row.id,
            "to_phone": to_phone,
            "status": "pending",
            "message": f"SMS zaradena do outboxu (id={row.id})",
        }
    finally:
        ds.close()


def list_pending(limit: int = 50) -> list[dict]:
    """
    Vrati pending SMS (status='pending'), serazeno FIFO (oldest first).
    Pouzije gateway router pro response na GET /gateway/outbox.
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(SmsOutbox)
            .filter(SmsOutbox.status == "pending")
            .order_by(SmsOutbox.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "to_phone": r.to_phone,
                "body": r.body,
                "purpose": r.purpose,
                "attempts": r.attempts,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    finally:
        ds.close()


def mark_sent(outbox_id: int) -> bool:
    """Telefon potvrzuje uspesne odeslani SMS."""
    ds = get_data_session()
    try:
        row = ds.query(SmsOutbox).filter(SmsOutbox.id == outbox_id).first()
        if not row:
            return False
        row.status = "sent"
        row.sent_at = datetime.now(timezone.utc)
        row.attempts = (row.attempts or 0) + 1
        ds.commit()
        logger.info(f"SMS | sent | id={outbox_id} | to={row.to_phone}")
        return True
    finally:
        ds.close()


def mark_failed(outbox_id: int, error: str | None = None) -> bool:
    """Telefon hlasi, ze SMS nesla (provider error, rate limit, SIM bez kreditu...)."""
    ds = get_data_session()
    try:
        row = ds.query(SmsOutbox).filter(SmsOutbox.id == outbox_id).first()
        if not row:
            return False
        row.status = "failed"
        row.attempts = (row.attempts or 0) + 1
        row.last_error = (error or "unknown")[:2000]
        ds.commit()
        logger.warning(
            f"SMS | failed | id={outbox_id} | to={row.to_phone} | error={row.last_error!r}"
        )
        return True
    finally:
        ds.close()


def mark_claimed(outbox_ids: list[int]) -> int:
    """
    Oznaci, ze telefon stahl tyto IDs pres GET /outbox (claimed_at).
    Zatim jen informativni -- nemenime status; pokud se telefon zasekne,
    SMS se stejne dorucuje pokud je status='pending'.
    Pro budouci locking / timeout logiku.
    """
    if not outbox_ids:
        return 0
    ds = get_data_session()
    try:
        now = datetime.now(timezone.utc)
        updated = (
            ds.query(SmsOutbox)
            .filter(SmsOutbox.id.in_(outbox_ids))
            .update({"claimed_at": now}, synchronize_session=False)
        )
        ds.commit()
        return updated
    finally:
        ds.close()
