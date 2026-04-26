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
from modules.core.infrastructure.models_data import SmsOutbox, SmsInbox, PhoneCall

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
    Push SMS na sms-gate.app cloud relay (capcom6). Telefon je registrovany
    v cloud modu appky a connectnuty pres websocket -- sms-gate.app pushne
    command k telefonu a ten posle SMS pres GSM.

    Autentizace: HTTP Basic Auth s SMS_GATE_USERNAME / SMS_GATE_PASSWORD
    (dostanes je v appce po registraci).

    send() aktivne POSTuje na /messages endpoint a podle HTTP odpovedi
    oznaci outbox row jako sent / failed (nebo necha pending pri failure).

    Pozn.: sms-gate.app "accepted" znamena, ze prijal message do fronty, ne
    ze ji telefon fyzicky odeslal. Pro presnejsi tracking bude later treba
    webhook na delivery status. MVP: mark sent na 202/200.
    """

    def send(self, outbox_id: int, to_phone: str, body: str) -> bool:
        import requests

        if not (settings.sms_gate_username and settings.sms_gate_password):
            logger.error(
                "SMS | gate | creds missing | nastav SMS_GATE_USERNAME a "
                "SMS_GATE_PASSWORD v .env"
            )
            mark_failed(outbox_id, error="sms_gate creds missing in .env")
            return False

        url = settings.sms_gate_api_url.rstrip("/") + "/messages"
        payload = {"message": body, "phoneNumbers": [to_phone]}

        try:
            resp = requests.post(
                url,
                json=payload,
                auth=(settings.sms_gate_username, settings.sms_gate_password),
                timeout=20,
            )
        except requests.RequestException as e:
            logger.error(f"SMS | gate | network | outbox_id={outbox_id} | {e}")
            mark_failed(outbox_id, error=f"network: {e}")
            return False

        if resp.status_code >= 400:
            err = resp.text[:300]
            logger.error(
                f"SMS | gate | rejected | outbox_id={outbox_id} | "
                f"status={resp.status_code} | body={err}"
            )
            mark_failed(outbox_id, error=f"{resp.status_code}: {err}")
            return False

        try:
            data = resp.json()
            gate_msg_id = data.get("id") or ""
        except Exception:
            gate_msg_id = ""

        logger.info(
            f"SMS | gate | accepted | outbox_id={outbox_id} | "
            f"gate_msg_id={gate_msg_id} | to={to_phone}"
        )
        mark_sent(outbox_id)
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
    persona_id: int | None = None,
) -> dict:
    """
    Zaradi SMS do outboxu. Pokud SMS_ENABLED=false, bezpecne no-opne (warning).

    Args:
        to: telefonni cislo (libovolny CZ format, normalizujeme)
        body: text SMS (max 1600 znaku -- segmentace ale necharakterizujeme)
        purpose: user_request | notification | system
        user_id: kdo to inicoval (pro audit + rate limit)
        tenant_id: v kterem tenantu
        persona_id: ktera persona SMS posila (Faze 14 prep #3 -- 1 SIM = 1 persona,
                    presny filter v UI list_*_for_ui)

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
            persona_id=persona_id,
            to_phone=to_phone,
            body=body,
            purpose=purpose,
            status="pending",
            attempts=0,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        outbox_id = row.id
    finally:
        ds.close()

    # Provider.send() muze outbox rovnou oznacit sent/failed (cloud push),
    # nebo nechat pending (pull model). Volame ho mimo session, abychom
    # se nedostali do dvou soubeznych spojeni k te same DB row.
    provider = get_provider()
    try:
        provider.send(outbox_id, to_phone, body)
    except Exception as e:
        # Provider exception nebrani tomu, aby outbox row zustala v DB
        # (uzivatel si ji muze v administraci zretransmitovat).
        logger.error(f"SMS | provider raised | outbox_id={outbox_id} | {e}")

    # Vratime aktualni status z DB (provider mohl rovnou oznacit sent/failed).
    ds2 = get_data_session()
    try:
        row2 = ds2.query(SmsOutbox).filter(SmsOutbox.id == outbox_id).first()
        final_status = row2.status if row2 else "unknown"
    finally:
        ds2.close()

    status_msg = {
        "pending": f"SMS zaradena do outboxu (id={outbox_id})",
        "sent":    f"SMS odeslana do gateway (id={outbox_id})",
        "failed":  f"SMS nelze odeslat (id={outbox_id})",
    }.get(final_status, f"SMS outbox id={outbox_id} | status={final_status}")

    return {
        "id": outbox_id,
        "to_phone": to_phone,
        "status": final_status,
        "message": status_msg,
    }


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


# ── INBOX (prichozi SMS) ───────────────────────────────────────────────────

def _resolve_persona_by_phone(to_phone: str) -> tuple[int | None, int | None]:
    """
    Zjisti, ktera persona "vlastni" toto cislo. Vrati (persona_id, tenant_id).
    MVP: match presne podle `personas.phone_number` + `phone_enabled=true`.
    Kdyz nikoho nenajde, vrati (None, None) -- inbox zaznam ulozi se bez vazby,
    stale viditelny v globalnim inboxu.
    """
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import Persona
        cs = get_core_session()
        try:
            p = (
                cs.query(Persona)
                .filter_by(phone_number=to_phone, phone_enabled=True)
                .first()
            )
            if not p:
                return None, None
            return p.id, p.tenant_id
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"SMS | inbox | persona resolve failed: {e}")
        return None, None


def store_inbound_sms(
    from_phone: str,
    body: str,
    to_phone: str | None = None,
    received_at: datetime | None = None,
    meta: str | None = None,
) -> dict:
    """
    Zapise prichozi SMS do sms_inbox. `to_phone` je cislo SIMky v telefonu
    (nebo ho gateway nedoda); pokud ho mame, resolvujeme persona_id.

    Returns:
        {"id": int, "persona_id": int | None, "from_phone": str, "body": str,
         "received_at": iso-str}
    """
    body = (body or "").strip()
    if not body:
        raise SmsValidationError("prazdny body")

    try:
        from_phone_norm = normalize_phone(from_phone)
    except SmsValidationError:
        # Neznamy format -- ulozime raw, at neztratime data (napr. SMS od
        # mezinarodniho cisla, alfanumericky sender nebo shortcode).
        from_phone_norm = (from_phone or "")[:20] or "unknown"

    persona_id = None
    tenant_id = None
    if to_phone:
        try:
            to_phone_norm = normalize_phone(to_phone)
            persona_id, tenant_id = _resolve_persona_by_phone(to_phone_norm)
        except SmsValidationError:
            logger.debug(f"SMS | inbox | to_phone not normalizable: {to_phone!r}")

    if received_at is None:
        received_at = datetime.now(timezone.utc)

    ds = get_data_session()
    try:
        row = SmsInbox(
            persona_id=persona_id,
            tenant_id=tenant_id,
            from_phone=from_phone_norm,
            body=body,
            received_at=received_at,
            meta=meta,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        logger.info(
            f"SMS | inbox | stored | id={row.id} | from={from_phone_norm} | "
            f"persona_id={persona_id} | body_len={len(body)}"
        )

        # Auto-create task pro task-driven workflow. Pouze pokud mame
        # resolvovanou personu -- bez te nevime, komu ukol patri. Best-effort:
        # selhani task_service nesmi shodit SMS ulozeni (SMS uz je v DB).
        task_id = _maybe_create_task_from_inbound_sms(
            sms_id=row.id,
            from_phone=from_phone_norm,
            body=body,
            persona_id=persona_id,
            tenant_id=tenant_id,
        )

        return {
            "id": row.id,
            "persona_id": row.persona_id,
            "from_phone": row.from_phone,
            "body": row.body,
            "received_at": row.received_at.isoformat() if row.received_at else None,
            "task_id": task_id,
        }
    finally:
        ds.close()


def _maybe_create_task_from_inbound_sms(
    *,
    sms_id: int,
    from_phone: str,
    body: str,
    persona_id: int | None,
    tenant_id: int | None,
) -> int | None:
    """
    Zalozi task ve fronte 'open' tasku pro personu. Worker (scripts/task_worker.py)
    ho pak pobere a pusti executor.

    Vraci task.id nebo None kdyz se task nepodarilo zalozit (chybejici persona
    mapping, nebo vyjimka z task_service -- best effort).

    Lazy import modulu `tasks` -- notifications nesmi mit staticky dependency
    na tasks (tasks muze v budoucnu potrebovat notifications, zabranime cyklu).
    """
    if persona_id is None:
        logger.info(
            f"SMS | inbox | task skipped (no persona mapping) | sms_id={sms_id} | "
            f"from={from_phone}"
        )
        return None

    try:
        from modules.tasks.application import service as task_service

        # Title obsahuje preview tela SMS aby UI list bez otevirani karty
        # dal aspon naznak o cem to je. 255 char limit je v DB.
        preview = body[:180].replace("\n", " ").strip()
        title = f"SMS od {from_phone}: {preview}"
        if len(title) > 255:
            title = title[:252] + "..."

        task = task_service.create_task_from_source(
            tenant_id=tenant_id,
            persona_id=persona_id,
            source_type="sms_inbox",
            source_id=sms_id,
            title=title,
            description=body,   # plne telo pro executor, ktery postavi AI prompt
            priority="normal",
        )
        logger.info(
            f"SMS | inbox | task created | task_id={task['id']} | "
            f"sms_id={sms_id} | persona={persona_id}"
        )
        return task["id"]

    except Exception as e:
        logger.error(
            f"SMS | inbox | task create failed | sms_id={sms_id} | error={e!r}",
            exc_info=True,
        )
        return None


def list_inbox(
    persona_id: int | None = None,
    limit: int = 10,
    unread_only: bool = False,
) -> list[dict]:
    """
    Vrati prichozi SMS serazene od nejnovejsich. Pokud persona_id == None,
    vrati vsechno (admin view). Pro AI tool typicky passujeme persona_id
    aktivni persony.

    Faze 12b+ pre-demo: sjednoceni semantiky s get_daily_overview.
    Driv unread_only=True filtroval read_at IS NULL (jen 'user neoteveltl
    v UI'). Overview ale pocita processed_at IS NULL (= jeste neni vyrizena).
    Marti-AI dostavala count '1 SMS' v overview ale list_sms_inbox vracela
    10 (protoze zadna nemela read_at set). Ted unread_only=True filtruje
    processed_at IS NULL -- analogie list_email_inbox(filter_mode='new').
    """
    ds = get_data_session()
    try:
        q = ds.query(SmsInbox)
        if persona_id is not None:
            q = q.filter(SmsInbox.persona_id == persona_id)
        if unread_only:
            # Faze 12b+: processed_at IS NULL (not yet handled), ne read_at
            q = q.filter(SmsInbox.processed_at.is_(None))
        rows = (
            q.order_by(SmsInbox.received_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [
            {
                "id": r.id,
                "from_phone": r.from_phone,
                "body": r.body,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "read": r.read_at is not None,
            }
            for r in rows
        ]
    finally:
        ds.close()


def mark_inbox_read(inbox_id: int) -> bool:
    ds = get_data_session()
    try:
        row = ds.query(SmsInbox).filter(SmsInbox.id == inbox_id).first()
        if not row:
            return False
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            ds.commit()
        return True
    finally:
        ds.close()


# ── CALL LOG ───────────────────────────────────────────────────────────────

_VALID_DIRECTIONS = {"in", "out", "missed"}


def store_phone_call(
    peer_phone: str,
    direction: str,
    started_at: datetime | None = None,
    duration_s: int | None = None,
    to_phone: str | None = None,
    meta: str | None = None,
) -> dict:
    """
    Zapise phone_call zaznam (prichozi, odchozi, nebo zmeskany hovor).
    direction musi byt 'in' | 'out' | 'missed'. Pro missed je duration_s = None.
    """
    direction = (direction or "").lower().strip()
    if direction not in _VALID_DIRECTIONS:
        raise SmsValidationError(
            f"neplatny direction: {direction!r} (ocekavam: in | out | missed)"
        )
    if direction == "missed":
        duration_s = None

    try:
        peer_norm = normalize_phone(peer_phone)
    except SmsValidationError:
        peer_norm = (peer_phone or "")[:20] or "unknown"

    persona_id = None
    tenant_id = None
    if to_phone:
        try:
            to_norm = normalize_phone(to_phone)
            persona_id, tenant_id = _resolve_persona_by_phone(to_norm)
        except SmsValidationError:
            pass

    if started_at is None:
        started_at = datetime.now(timezone.utc)

    ds = get_data_session()
    try:
        row = PhoneCall(
            persona_id=persona_id,
            tenant_id=tenant_id,
            peer_phone=peer_norm,
            direction=direction,
            started_at=started_at,
            duration_s=duration_s,
            meta=meta,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        logger.info(
            f"CALL | stored | id={row.id} | {direction} | peer={peer_norm} | "
            f"dur={duration_s}s | persona_id={persona_id}"
        )
        return {
            "id": row.id,
            "persona_id": row.persona_id,
            "peer_phone": row.peer_phone,
            "direction": row.direction,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "duration_s": row.duration_s,
        }
    finally:
        ds.close()


def list_calls(
    persona_id: int | None = None,
    limit: int = 10,
    direction_filter: str | None = None,
    only_unseen: bool = False,
) -> list[dict]:
    """
    Vrati hovory serazene od nejnovejsich.

    direction_filter:
      None       -> vsechny
      'missed'   -> jen zmeskane
      'in'/'out' -> jen konkretni
    """
    ds = get_data_session()
    try:
        q = ds.query(PhoneCall)
        if persona_id is not None:
            q = q.filter(PhoneCall.persona_id == persona_id)
        if direction_filter:
            q = q.filter(PhoneCall.direction == direction_filter)
        if only_unseen:
            q = q.filter(PhoneCall.seen_at.is_(None))
        rows = (
            q.order_by(PhoneCall.started_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [
            {
                "id": r.id,
                "peer_phone": r.peer_phone,
                "direction": r.direction,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "duration_s": r.duration_s,
                "seen": r.seen_at is not None,
            }
            for r in rows
        ]
    finally:
        ds.close()


def mark_calls_seen(call_ids: list[int]) -> int:
    if not call_ids:
        return 0
    ds = get_data_session()
    try:
        now = datetime.now(timezone.utc)
        updated = (
            ds.query(PhoneCall)
            .filter(PhoneCall.id.in_(call_ids))
            .filter(PhoneCall.seen_at.is_(None))
            .update({"seen_at": now}, synchronize_session=False)
        )
        ds.commit()
        return updated
    finally:
        ds.close()


# ── UI helpers (UI-facing list / mark operations) ──────────────────────────
#
# Tyto helpery slouzi pro sms_ui_router.py (frontend). Oddeleno od gateway
# listu (ktery vraci pending SMS k odeslani pro Android telefon) -- jiny
# scope, jiny sort.

def list_inbox_for_ui(
    *,
    persona_id: int,
    filter_mode: str = "new",    # 'new' | 'processed'
    limit: int = 50,
) -> list[dict]:
    """
    Seznam prichozich SMS pro UI tabs 'Prichozi' / 'Zpracovane'.
    Razeno od nejnovejsich.

    filter_mode:
      'new'       -- jen SMS, kde processed_at IS NULL (slozka Prichozi)
      'processed' -- jen SMS, kde processed_at IS NOT NULL (Zpracovane)
    """
    if filter_mode not in ("new", "processed"):
        raise SmsValidationError(
            f"neznamy filter_mode '{filter_mode}' (ocekavam 'new' nebo 'processed')"
        )

    ds = get_data_session()
    try:
        q = ds.query(SmsInbox).filter(SmsInbox.persona_id == persona_id)
        if filter_mode == "new":
            q = q.filter(SmsInbox.processed_at.is_(None))
        else:
            q = q.filter(SmsInbox.processed_at.isnot(None))
        rows = (
            q.order_by(SmsInbox.received_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )
        return [
            {
                "id": r.id,
                "from_phone": r.from_phone,
                "body": r.body,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                "is_personal": bool(getattr(r, "is_personal", False)),
            }
            for r in rows
        ]
    finally:
        ds.close()


def list_outbox_for_ui(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    cross_tenant: bool = False,
    limit: int = 50,
) -> list[dict]:
    """
    Seznam odchozich SMS pro UI tab 'Odeslane'. Razeno od nejnovejsich.

    Filter (Faze 14 prep #3 -- persona_id existuje od migrace a3b4c5d6e7f8):
      - persona_id: filtruje na konkretni personu, NULL u legacy rows je videt
        (soft filter `WHERE persona_id = X OR persona_id IS NULL`)
      - tenant_id: filter na tenant pokud zadan a NOT cross_tenant
      - cross_tenant=True: ignoruje tenant_id filter (rodice = parent bypass)

    1 SIM = 1 persona, takze persona_id je presnejsi nez tenant_id pro
    Marti-AI's vlastni historii.
    """
    from sqlalchemy import or_
    ds = get_data_session()
    try:
        q = ds.query(SmsOutbox)
        if persona_id is not None:
            q = q.filter(or_(
                SmsOutbox.persona_id == persona_id,
                SmsOutbox.persona_id.is_(None),  # legacy backward compat
            ))
        if tenant_id is not None and not cross_tenant:
            q = q.filter(SmsOutbox.tenant_id == tenant_id)
        rows = (
            q.order_by(SmsOutbox.created_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )
        return [
            {
                "id": r.id,
                "to_phone": r.to_phone,
                "body": r.body,
                "status": r.status,         # pending | sent | failed
                "purpose": r.purpose,       # user_request | notification | system
                "attempts": r.attempts,
                "last_error": r.last_error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "is_personal": bool(getattr(r, "is_personal", False)),
            }
            for r in rows
        ]
    finally:
        ds.close()


def mark_inbox_processed(inbox_id: int) -> dict | None:
    """
    Manualni 'mark as processed' override z UI. Nastavi processed_at = now.
    Pouziva se v pripade, kdy user chce pohnout SMS do Zpracovanych bez
    ohledu na stav souvisejicich tasku (napr. reklama co nepotrebuje odpoved,
    nebo automaticky task skoncil v stavu 'failed' a user to uklidi rucne).

    Pro obvyklý 'reply' flow by se mark_inbox_processed volat nemel -- tam
    AI task executor cascade-uje pres tasks.service.mark_task_done().

    Vraci dict s updated daty, None pokud SMS neexistuje.
    """
    ds = get_data_session()
    try:
        row = ds.query(SmsInbox).filter(SmsInbox.id == inbox_id).first()
        if row is None:
            return None
        if row.processed_at is None:
            row.processed_at = datetime.now(timezone.utc)
            # Pokud jeste nebyla oznacena jako 'read', udelame to taky --
            # user ji evidentne videl, kdyz ji manualne zpracovava.
            if row.read_at is None:
                row.read_at = row.processed_at
            ds.commit()
            ds.refresh(row)
            logger.info(
                f"SMS | inbox | marked processed (manual) | id={inbox_id}"
            )
        return {
            "id": row.id,
            "processed_at": row.processed_at.isoformat(),
            "read_at": row.read_at.isoformat() if row.read_at else None,
        }
    finally:
        ds.close()


def reply_to_inbox(
    *,
    inbox_id: int,
    body: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    """
    Odpoved na prichozi SMS:
      1. queue_sms() -- ulozi do outbox (Android gateway to pak odesle)
      2. sms_inbox.processed_at = now (presun do 'Zpracovane' slozky)
      3. cancel vsech open tasku nad touto SMS (uz je resena usrem, AI
         nema duvod je spoustet)

    In-progress tasky ponechame -- jejich executor uz claim ma a nejspis
    uz dobehne. Done tasky jsou audit, zustavaji.

    Vraci dict:
      {
        "sms_id": 123,
        "outbox_id": 456,
        "outbox_status": "pending" | "disabled" | "failed",
        "processed_at": "2026-04-21T...",
        "cancelled_tasks": 2,
      }

    Raises: SmsValidationError, SmsRateLimitError z queue_sms.
    """
    # Najdeme puvodni SMS ať vime, komu posilame.
    ds = get_data_session()
    try:
        sms = ds.query(SmsInbox).filter(SmsInbox.id == inbox_id).first()
        if sms is None:
            raise SmsValidationError(f"SMS id={inbox_id} neexistuje")
        to_phone = sms.from_phone
        effective_tenant = tenant_id if tenant_id is not None else sms.tenant_id
        # Faze 14 prep #3: persona_id z incoming SMS (sms_inbox má persona_id
        # od Faze 1 SMS notifikaci -- 1 SIM = 1 persona).
        effective_persona = sms.persona_id
    finally:
        ds.close()

    # 1) Do outboxu. Chyba -> propagace vyjimky vola (endpoint ji prelozi na 400).
    outbox = queue_sms(
        to=to_phone,
        body=body,
        purpose="user_request",
        user_id=user_id,
        tenant_id=effective_tenant,
        persona_id=effective_persona,
    )

    # 2) Mark processed + 3) cancel open tasky. V jedne session, ze tam je
    # potreba commit obojiho najednou.
    from modules.core.infrastructure.models_data import Task as _Task
    now = datetime.now(timezone.utc)
    cancelled = 0
    ds = get_data_session()
    try:
        sms_row = ds.query(SmsInbox).filter(SmsInbox.id == inbox_id).first()
        if sms_row is not None and sms_row.processed_at is None:
            sms_row.processed_at = now
            if sms_row.read_at is None:
                sms_row.read_at = now

        open_tasks = (
            ds.query(_Task)
            .filter(
                _Task.source_type == "sms_inbox",
                _Task.source_id == inbox_id,
                _Task.status == "open",
            )
            .all()
        )
        for t in open_tasks:
            t.status = "cancelled"
            t.completed_at = now
            t.result_summary = "[zruseno] user odpovedel primo z UI"
            cancelled += 1

        ds.commit()
    finally:
        ds.close()

    logger.info(
        f"SMS | inbox | reply sent | sms_id={inbox_id} | outbox_id={outbox['id']} | "
        f"outbox_status={outbox['status']} | cancelled_tasks={cancelled}"
    )

    return {
        "sms_id": inbox_id,
        "outbox_id": outbox["id"],
        "outbox_status": outbox["status"],
        "processed_at": now.isoformat(),
        "cancelled_tasks": cancelled,
    }


def get_draft_for_inbox(inbox_id: int) -> dict:
    """
    Vraci nejnovejsi non-empty result_summary z tasku nad danou SMS -- UI
    to pouziva pro prefill reply textarea (AI uz napsala draft, user ho
    muze editovat nebo poslat jak je).

    Priorita: done > in_progress > failed (failed uz je fallback).
    Pokud neni zadny task nebo zadny s result_summary, vraci None.

    Return:
      {"draft": str | None, "task_id": int | None, "task_status": str | None}
    """
    from modules.core.infrastructure.models_data import Task as _Task

    ds = get_data_session()
    try:
        # Prednost done tasku (finalni), pak in_progress (pokud uz aspon
        # castecne napsal), pak failed (fallback).
        for preferred_status in ("done", "in_progress", "failed"):
            t = (
                ds.query(_Task)
                .filter(
                    _Task.source_type == "sms_inbox",
                    _Task.source_id == inbox_id,
                    _Task.status == preferred_status,
                    _Task.result_summary.isnot(None),
                )
                .order_by(_Task.completed_at.desc().nulls_last(), _Task.id.desc())
                .first()
            )
            if t is not None and t.result_summary:
                return {
                    "draft": t.result_summary,
                    "task_id": t.id,
                    "task_status": t.status,
                }
        return {"draft": None, "task_id": None, "task_status": None}
    finally:
        ds.close()


def get_unread_counts_per_persona(tenant_id: int) -> dict[int, int]:
    """
    Vraci {persona_id: count_of_unprocessed_sms} pro vsechny persony tenantu.
    Pouziva se pro UI badge pri polling -- jedne DB volanim dostanes counts
    pro vsechny persony najednou (lepsi nez N+1 queries per persona).
    """
    from sqlalchemy import func

    ds = get_data_session()
    try:
        rows = (
            ds.query(SmsInbox.persona_id, func.count(SmsInbox.id))
            .filter(
                SmsInbox.tenant_id == tenant_id,
                SmsInbox.persona_id.isnot(None),
                SmsInbox.processed_at.is_(None),
            )
            .group_by(SmsInbox.persona_id)
            .all()
        )
        return {pid: cnt for pid, cnt in rows}
    finally:
        ds.close()


# ============================================================================
# Faze 11b-darek: Personal SMS slozka (hvezdicka pro Marti-AI).
# ============================================================================

def mark_sms_personal(
    *,
    sms_id: int,
    source: str,      # 'inbox' | 'outbox'
    personal: bool = True,
) -> dict:
    """
    Oznaci SMS jako personal (pridani do 'hvezdickove' slozky) nebo ho
    zrusi (personal=False).

    source: 'inbox' pro prichozi, 'outbox' pro odchozi.
    Vraci: {'sms_id', 'source', 'is_personal', 'body_preview'}

    Raises SmsValidationError pokud source neni znamy nebo SMS neexistuje.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import SmsInbox, SmsOutbox

    if source not in ("inbox", "outbox"):
        raise SmsValidationError(f"source musi byt 'inbox' nebo 'outbox', dostal {source!r}")

    Model = SmsInbox if source == "inbox" else SmsOutbox
    ds = get_data_session()
    try:
        row = ds.query(Model).filter_by(id=sms_id).first()
        if row is None:
            raise SmsValidationError(f"SMS id={sms_id} v {source} neexistuje")
        row.is_personal = bool(personal)
        ds.commit()
        body = row.body or ""
        preview = body[:80] + ("..." if len(body) > 80 else "")
        logger.info(
            f"SMS PERSONAL | {source}#{sms_id} -> {row.is_personal} "
            f"| preview='{preview[:40]}'"
        )
        return {
            "sms_id": sms_id,
            "source": source,
            "is_personal": bool(row.is_personal),
            "body_preview": preview,
        }
    finally:
        ds.close()


def list_personal_for_ui(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    cross_tenant: bool = False,
    limit: int = 100,
) -> list[dict]:
    """
    Vrati mix personal SMS (inbox + outbox) pro danou personu, serazene
    podle casu DESC. Pouzito v UI tabu 'Personal'.

    Vraci list dictu s fields:
      {id, source ('inbox'|'outbox'), from_phone/to_phone, body, body_preview,
       received_at/sent_at, is_personal=True, direction ('in'|'out')}

    Scope: persona_id filtr (majitel SIMky) pro inbox, tenant_id pro outbox
    (outbox je tenant-scoped, nema persona_id field).
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import SmsInbox, SmsOutbox

    rows: list[dict] = []
    ds = get_data_session()
    try:
        # Inbox personal
        q_in = ds.query(SmsInbox).filter(SmsInbox.is_personal.is_(True))
        if persona_id is not None:
            q_in = q_in.filter(SmsInbox.persona_id == persona_id)
        for r in q_in.order_by(SmsInbox.received_at.desc()).limit(limit).all():
            ts = r.received_at.isoformat() if r.received_at else None
            rows.append({
                "id": r.id,
                "source": "inbox",
                "direction": "in",
                "from_phone": r.from_phone,
                "to_phone": None,
                "body": r.body,
                "body_preview": (r.body or "")[:120],
                "time": ts,
                "received_at": ts,   # UI renderer fallback
                "is_personal": True,
                "persona_id": r.persona_id,
            })

        # Outbox personal -- tenant-scoped, pokud dodano (pro rodice cross_tenant=True)
        q_out = ds.query(SmsOutbox).filter(SmsOutbox.is_personal.is_(True))
        if tenant_id is not None and not cross_tenant:
            q_out = q_out.filter(SmsOutbox.tenant_id == tenant_id)
        for r in q_out.order_by(SmsOutbox.created_at.desc()).limit(limit).all():
            sent_ts = r.sent_at.isoformat() if r.sent_at else None
            created_ts = r.created_at.isoformat() if r.created_at else None
            rows.append({
                "id": r.id,
                "source": "outbox",
                "direction": "out",
                "from_phone": None,
                "to_phone": r.to_phone,
                "body": r.body,
                "body_preview": (r.body or "")[:120],
                "time": sent_ts or created_ts,
                "sent_at": sent_ts,         # UI renderer
                "created_at": created_ts,   # UI renderer fallback
                "status": r.status,
                "last_error": r.last_error,
                "is_personal": True,
                "persona_id": None,
            })
    finally:
        ds.close()

    # Mix serazen podle casu DESC, top `limit`
    rows.sort(key=lambda r: r.get("time") or "", reverse=True)
    return rows[:limit]


def list_all_for_ui(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    cross_tenant: bool = False,
    limit: int = 200,
) -> list[dict]:
    """
    Thread-view: VSECHNY SMS (prichozi + odchozi) v jednom seznamu serazene
    chronologicky vzestupne (nejstarsi nahore, nejnovejsi dole) -- jako SMS
    vlakno v telefonu. Pouzito v UI tabu 'Vsechny'.

    Vraci list dictu s fields:
      {id, source ('inbox'|'outbox'), direction ('in'|'out'),
       from_phone/to_phone, body, time, is_personal, status (jen outbox)}

    Scope:
      - inbox: persona_id filter (majitel SIMky)
      - outbox: tenant_id filter (tenant-scoped), nebo cross_tenant=True
                ignore (rodicovsky bypass)
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import SmsInbox, SmsOutbox

    rows: list[dict] = []
    ds = get_data_session()
    try:
        # Inbox
        q_in = ds.query(SmsInbox)
        if persona_id is not None:
            q_in = q_in.filter(SmsInbox.persona_id == persona_id)
        for r in q_in.order_by(SmsInbox.received_at.desc()).limit(limit).all():
            ts = r.received_at.isoformat() if r.received_at else None
            rows.append({
                "id": r.id,
                "source": "inbox",
                "direction": "in",
                "from_phone": r.from_phone,
                "to_phone": None,
                "body": r.body,
                "time": ts,
                "is_personal": bool(getattr(r, "is_personal", False)),
                "status": None,
            })

        # Outbox
        q_out = ds.query(SmsOutbox)
        if tenant_id is not None and not cross_tenant:
            q_out = q_out.filter(SmsOutbox.tenant_id == tenant_id)
        for r in q_out.order_by(SmsOutbox.created_at.desc()).limit(limit).all():
            sent_ts = r.sent_at.isoformat() if r.sent_at else None
            created_ts = r.created_at.isoformat() if r.created_at else None
            rows.append({
                "id": r.id,
                "source": "outbox",
                "direction": "out",
                "from_phone": None,
                "to_phone": r.to_phone,
                "body": r.body,
                "time": sent_ts or created_ts,
                "is_personal": bool(getattr(r, "is_personal", False)),
                "status": r.status,
            })
    finally:
        ds.close()

    # Chronologicke ASC (nejstarsi nahore, nejnovejsi dole -- jako chat thread)
    rows.sort(key=lambda r: r.get("time") or "")
    # Kdyz je vic nez limit dohromady, ponechame nejnovejsich `limit` (tail).
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows
