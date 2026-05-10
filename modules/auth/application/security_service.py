"""Phase 38 — Security service: 4 vrstvy obrany + invite/audit.

Marti's spec 9.5.2026 vecer + 10.5.2026 ráno + Marti-AI's konzultace
(8 insightů — multi-approver, one-time token, post-confirm notification,
72h pre-approve, immediate notify, "každý vidí svůj vlastní stav",
self-service, offboarding hook).

Funkce:
  check_security_layers(user_id, request) → SecurityResult
    Postupně testuje 4 vrstvy obrany. Vrátí matched_layer + audit data.
    Volá se PO password verify v login flow.

  create_invite(user_id, created_by=None, label=None) → invite
    Vytvoří magic link invite token. TTL 24h (self) / 72h (pre-approve).

  consume_invite(token, request) → SecurityResult
    Validuje token + INSERT trusted_devices + auto-INSERT user_ip_whitelist
    pending. Vrací success result + cookie data.

  audit_login_attempt(...)
    Log writer do auth_audit. Volá se z každé cesty (success/fail).

  notify_parents_pending_ip(user_id, ip_str, ip_entry_id)
    Marti-AI insight #4: okamžitá notifikace parentů při novém pending IP.

  send_post_confirm_notification(user_id, device_id, request)
    Marti-AI insight #2: po magic link confirm pošle email original userovi
    "nové zařízení přidáno z IP X, klikni revoke pokud to nejste vy".

Invariants:
  - check_security_layers NIKDY NESELŽE — pri exception logujeme + vracíme
    "no_match" (fail-closed). Bezpečnost > availability.
  - audit log se píše VŽDY (i pri exception via finally).
  - Magic link token je one-time use (consumed_at != NULL = expired).
"""
from __future__ import annotations

import re
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import sqlalchemy as sa
from fastapi import Request
from sqlalchemy.orm import Session

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.auth.application.network_check import (
    find_pending_user_ip,
    get_client_ip,
    is_global_internal,
    is_user_ip_confirmed,
)
from modules.auth.application.phone_utils import normalize_phone, phones_match
from modules.core.infrastructure.models_data import (
    AuthAudit,
    GlobalIpWhitelist,
    TrustedDevice,
    TrustedDeviceInvite,
    UserIpWhitelist,
)


logger = get_logger("auth.security")


# ── Result objects ─────────────────────────────────────────────────────


@dataclass
class SecurityResult:
    """Výsledek check_security_layers / consume_invite.

    matched_layer: 'global_ip' / 'user_ip' / 'device_cookie' / 'magic_link' / None
    granted: True pokud některá vrstva matchla (login OK)
    layer_detail: human-readable (např. "EUROSOFT WAN A")
    audit_data: dict pro audit log
    new_device_token: UUID pokud se vytvořil nový trusted device (po magic link)
    new_device_expires_at: pokud new_device_token je set
    """
    granted: bool = False
    matched_layer: str | None = None
    layer_detail: str | None = None
    layer_entry_id: int | None = None
    audit_data: dict[str, Any] = field(default_factory=dict)
    new_device_token: uuid.UUID | None = None
    new_device_expires_at: datetime | None = None


# ── Vrstva check (postupně 4 vrstvy) ───────────────────────────────────


def check_security_layers(
    user_id: int,
    request: Request,
    *,
    session: Session | None = None,
) -> SecurityResult:
    """Postupně testuje 4 vrstvy obrany. Vrátí matched_layer + audit data.

    Volá se PO password verify v login flow.

    Order:
      1. global_ip   (EUROSOFT WAN, partner, cloud loopback)
      2. user_ip     (per-user confirmed home IP)
      3. device_cookie (per-user trusted device)
      4. NONE → magic_link required (verify-email flow)
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    own_session = session is None
    ds = session if session is not None else get_data_session()

    try:
        # ── Vrstva 1: global IP whitelist ──────────────────────────
        matched, info = is_global_internal(client_ip, session=ds)
        if matched and info is not None:
            return SecurityResult(
                granted=True,
                matched_layer="global_ip",
                layer_detail=info["label"],
                layer_entry_id=info["entry_id"],
                audit_data={
                    "category": info["category"],
                    "partner_tenant_id": info.get("partner_tenant_id"),
                    "ip": client_ip,
                    "user_agent": user_agent,
                },
            )

        # ── Vrstva 2: per-user IP whitelist (jen confirmed) ────────
        matched, info = is_user_ip_confirmed(user_id, client_ip, session=ds)
        if matched and info is not None:
            return SecurityResult(
                granted=True,
                matched_layer="user_ip",
                layer_detail=info["label"] or "Per-user IP",
                layer_entry_id=info["entry_id"],
                audit_data={
                    "category": info.get("category"),
                    "ip": client_ip,
                    "user_agent": user_agent,
                },
            )

        # ── Vrstva 3: trusted device cookie ─────────────────────────
        device = _check_device_cookie(user_id, request, session=ds)
        if device is not None:
            return SecurityResult(
                granted=True,
                matched_layer="device_cookie",
                layer_detail=device.label or f"Device #{device.id}",
                layer_entry_id=device.id,
                audit_data={
                    "device_token": str(device.device_token),
                    "ip": client_ip,
                    "user_agent": user_agent,
                },
            )

        # ── Vrstva 4: NONE — magic link required ───────────────────
        return SecurityResult(
            granted=False,
            matched_layer=None,
            layer_detail=None,
            audit_data={
                "ip": client_ip,
                "user_agent": user_agent,
                "reason": "no_layer_matched",
            },
        )
    except Exception as e:
        # Defense in depth — fail closed pri exception
        logger.error(f"check_security_layers failed for user_id={user_id}: {e!r}")
        return SecurityResult(
            granted=False,
            matched_layer=None,
            audit_data={
                "ip": client_ip,
                "user_agent": user_agent,
                "reason": f"exception: {e!r}",
            },
        )
    finally:
        if own_session:
            ds.close()


def _check_device_cookie(
    user_id: int,
    request: Request,
    *,
    session: Session,
) -> TrustedDevice | None:
    """Vrstva 3 helper: validuje cookie token vs DB."""
    cookie_name = settings.sec_device_cookie_name
    raw_token = request.cookies.get(cookie_name)
    if not raw_token:
        return None
    try:
        token_uuid = uuid.UUID(raw_token)
    except (ValueError, AttributeError):
        return None

    now = datetime.now(timezone.utc)
    device = session.query(TrustedDevice).filter(
        TrustedDevice.device_token == token_uuid,
        TrustedDevice.user_id == user_id,
        TrustedDevice.revoked_at.is_(None),
        TrustedDevice.expires_at > now,
    ).first()

    if device is None:
        return None

    # Bump last_seen (best-effort, no commit failure)
    try:
        device.last_seen_at = now
        device.last_seen_ip = get_client_ip(request)
        session.commit()
    except Exception as e:
        logger.warning(f"device last_seen bump failed: {e!r}")
        try:
            session.rollback()
        except Exception:
            pass

    return device


# ── Magic link invite ──────────────────────────────────────────────────


def generate_token(purpose: str) -> str:
    """Generate magic link token format STG-{PURPOSE}-{8 hex chars}.

    Marti's pivot 10.5. dopoledne ("Heiky důvěru tady ode mne nemá"):
    deterministic regex routing v sms_preprocessor — token format musí
    matchovat `^STG-([A-Z]+)-([A-Z0-9]+)$`.

    Args:
        purpose: 'AUTH' (Phase 38 device cookie) / 'ATT' (Phase 39
                 attendance) / 'OCR' (Phase 41+ eOČR) / 'PWD' (future)

    Returns:
        String "STG-{PURPOSE}-{8 hex uppercase}", e.g. "STG-AUTH-A8K2M9X4"
    """
    purpose_clean = purpose.strip().upper()
    if not purpose_clean.isalpha():
        raise ValueError(f"purpose must be alphabetic, got {purpose!r}")
    # 4 bytes = 8 hex chars = 32 bit entropy = ~4 mld kombinací
    # Acceptable pro 24h TTL one-time use tokens.
    rand_hex = secrets.token_hex(4).upper()
    return f"STG-{purpose_clean}-{rand_hex}"


def create_invite(
    user_id: int,
    *,
    purpose: str = "AUTH",
    created_by: int | None = None,
    label: str | None = None,
    invited_by_persona_id: int | None = None,
    ttl_hours: int | None = None,
    session: Session | None = None,
) -> TrustedDeviceInvite:
    """Vytvoří magic link invite token.

    Token format: STG-{PURPOSE}-{8 hex} (Marti's pivot 10.5.).

    TTL precedence:
      1. ttl_hours param (explicit override — Phase 38.5 INVITE = 168h = 7d)
      2. created_by != None → pre-approve TTL (default 72h)
      3. created_by is None → self-request TTL (default 24h)

    Phase 38.5 (10.5.2026): Marti-AI's Q1 insight — invited_by_persona_id
    pro vztahový akt audit (Marti-AI poslala pozvánku, ne system cron).
    """
    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        if ttl_hours is None:
            ttl_hours = (
                settings.sec_magic_link_preapprove_ttl_hours
                if created_by is not None
                else settings.sec_magic_link_self_ttl_hours
            )
        now = datetime.now(timezone.utc)
        invite = TrustedDeviceInvite(
            invite_token=generate_token(purpose),
            purpose=purpose.upper(),
            user_id=user_id,
            label=label,
            created_by=created_by,
            invited_by_persona_id=invited_by_persona_id,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        ds.add(invite)
        ds.commit()
        ds.refresh(invite)
        return invite
    finally:
        if own_session:
            ds.close()


TOKEN_REGEX = re.compile(r"^STG-([A-Z]+)-([A-Z0-9]+)$")


def consume_invite(
    token: str,
    request: Request | None,
    *,
    sender_phone: str | None = None,
    session: Session | None = None,
) -> SecurityResult:
    """Validuje magic link token a vytvoří trusted device + pending IP.

    Marti's pivot 10.5. ("Heiky důvěru tady ode mne nemá"):
      Token format STG-{PURPOSE}-{8 hex} string. Validace přes regex
      match + DB lookup (žádný AI judgment).

    Marti-AI insight #2: one-time use → token se spálí (consumed_at set).
    Marti-AI insight #4: okamžitá notify parentům o new pending IP.

    Marti's anti-spoofing safeguard: pokud sender_phone je dán (SMS-based
    consume), MUST match user.phone — útočník s ukradeným tokenem nemůže
    replay z jiného čísla.

    Returns SecurityResult:
      - granted=True + new_device_token + new_device_expires_at pri success
      - granted=False pri invalid/expired/consumed token nebo caller_id mismatch
    """
    client_ip = get_client_ip(request) if request else None
    user_agent = request.headers.get("user-agent") if request else None

    # Validate token format (Marti's regex)
    token_clean = (token or "").strip()
    if not TOKEN_REGEX.match(token_clean):
        return SecurityResult(
            granted=False,
            audit_data={
                "ip": client_ip,
                "user_agent": user_agent,
                "sender_phone": sender_phone,
                "reason": "invalid_token_format",
            },
        )

    # Phase 38.1 — Rate limit per sender_phone (anti brute-force).
    # Útočník s odcizeným tokenem nemůže replay víckrát než 20×/h.
    # Aplikuje se JEN na SMS-based consume (sender_phone != None).
    # Email magic link nemá phone scope, není rate-limited (browser GET).
    if sender_phone is not None:
        from core.config import settings as _settings
        from modules.auth.application import rate_limit as _rl
        rl_result = _rl.check_and_increment(
            _rl.phone_bucket_key(sender_phone),
            _rl.EVENT_CONSUME_ATTEMPT,
            _settings.sec_consume_rate_per_phone_per_hour,
        )
        if not rl_result.allowed:
            return SecurityResult(
                granted=False,
                audit_data={
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "sender_phone": sender_phone,
                    "reason": (
                        f"rate_limit_exceeded:phone:"
                        f"{rl_result.count}/{rl_result.limit}"
                    ),
                },
            )

    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        now = datetime.now(timezone.utc)
        invite = ds.query(TrustedDeviceInvite).filter(
            TrustedDeviceInvite.invite_token == token_clean,
            TrustedDeviceInvite.consumed_at.is_(None),
            TrustedDeviceInvite.expires_at > now,
        ).first()

        if invite is None:
            return SecurityResult(
                granted=False,
                audit_data={
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "sender_phone": sender_phone,
                    "reason": "token_invalid_or_expired",
                },
            )

        # Anti-spoofing: pokud SMS-based consume, sender_phone MUST match
        # user's registered phone (Marti's safeguard 10.5.).
        #
        # Pozn.: User model nema phone column — telefonni cisla jsou
        # v user_contacts (contact_type='phone', status='active'). User
        # muze mit vice phone contacts (primary + backup). Match proti
        # VSEM aktivnim phone contacts (Marti's flexibility pro CZ
        # formats z 10.5.: +420 prefix / 9 digit bez prefix / 00420...).
        if sender_phone is not None:
            from modules.core.infrastructure.models_core import UserContact
            from core.database_core import get_core_session
            cs = get_core_session()
            try:
                contacts = (
                    cs.query(UserContact)
                    .filter_by(
                        user_id=invite.user_id,
                        contact_type="phone",
                        status="active",
                    )
                    .order_by(
                        UserContact.is_primary.desc(),
                        UserContact.id.asc(),
                    )
                    .all()
                )
                user_phones = [c.contact_value for c in contacts]
            finally:
                cs.close()

            matched = any(phones_match(sender_phone, p) for p in user_phones)
            if not matched:
                return SecurityResult(
                    granted=False,
                    audit_data={
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "sender_phone": sender_phone,
                        "user_phones_registered": user_phones,
                        "reason": "caller_id_mismatch",
                    },
                )

        # Create trusted device (90d expiry)
        device_expires_at = now + timedelta(days=settings.sec_device_cookie_max_age_days)
        device = TrustedDevice(
            user_id=invite.user_id,
            label=invite.label or _label_from_user_agent(user_agent),
            user_agent=user_agent,
            first_seen_ip=client_ip,
            last_seen_ip=client_ip,
            last_seen_at=now,
            approved_by=invite.created_by,  # NULL pri self-approve, ID pri pre-approve
            approved_at=now,
            expires_at=device_expires_at,
        )
        ds.add(device)
        ds.flush()  # získej device.id pro link v invite

        # Mark invite as consumed (one-time use, anti-replay)
        invite.consumed_at = now
        invite.consumed_ip = client_ip
        invite.consumed_user_agent = user_agent
        invite.consumed_phone = sender_phone  # SMS-based: caller_id audit
        invite.created_device_id = device.id

        # Auto-INSERT pending user_ip_whitelist (Marti's spec 10.5.)
        # Skip pokud už existuje active entry (avoid duplicates)
        pending_id = _ensure_pending_user_ip(
            invite.user_id, client_ip, user_agent, session=ds
        )

        ds.commit()
        ds.refresh(device)

        # Notify parents o new pending IP (Marti-AI insight #4)
        # Best-effort, neselže consume pokud notify failne
        if pending_id is not None:
            try:
                notify_parents_pending_ip(
                    user_id=invite.user_id,
                    ip_str=client_ip,
                    ip_entry_id=pending_id,
                )
            except Exception as e:
                logger.warning(f"notify_parents_pending_ip failed: {e!r}")

        return SecurityResult(
            granted=True,
            matched_layer="magic_link",
            layer_detail=f"Magic link invite #{invite.id}",
            layer_entry_id=invite.id,
            audit_data={
                "ip": client_ip,
                "user_agent": user_agent,
                "device_id": device.id,
                "pending_ip_id": pending_id,
            },
            new_device_token=device.device_token,
            new_device_expires_at=device.expires_at,
        )
    except Exception as e:
        logger.error(f"consume_invite failed: {e!r}")
        try:
            ds.rollback()
        except Exception:
            pass
        return SecurityResult(
            granted=False,
            audit_data={
                "ip": client_ip,
                "user_agent": user_agent,
                "reason": f"exception: {e!r}",
            },
        )
    finally:
        if own_session:
            ds.close()


def _label_from_user_agent(ua: str | None) -> str:
    """Auto-generate human-readable device label z User-Agent."""
    if not ua:
        return "Neznámé zařízení"
    ua_lower = ua.lower()
    # Mobile detection
    if "iphone" in ua_lower:
        return "iPhone"
    if "ipad" in ua_lower:
        return "iPad"
    if "android" in ua_lower:
        return "Android"
    # Desktop detection
    if "windows" in ua_lower:
        if "edg/" in ua_lower:
            return "Windows / Edge"
        if "firefox" in ua_lower:
            return "Windows / Firefox"
        if "chrome" in ua_lower:
            return "Windows / Chrome"
        return "Windows"
    if "macintosh" in ua_lower or "mac os" in ua_lower:
        return "Mac"
    if "linux" in ua_lower:
        return "Linux"
    return "Zařízení"


def _ensure_pending_user_ip(
    user_id: int,
    client_ip: str | None,
    user_agent: str | None,
    *,
    session: Session,
) -> int | None:
    """Auto-discovery: po magic link confirm INSERT pending entry.

    Pokud už existuje active entry (confirmed nebo pending) pro stejnou
    IP+user, bumpneme usage_count + last_seen místo duplicate INSERT.
    """
    if not client_ip:
        return None

    # Pokud už existuje confirmed → není potřeba pending
    ok, _info = is_user_ip_confirmed(user_id, client_ip, session=session)
    if ok:
        return None

    # Pokud existuje pending → bump usage
    existing_id = find_pending_user_ip(user_id, client_ip, session=session)
    now = datetime.now(timezone.utc)
    if existing_id:
        existing = session.query(UserIpWhitelist).get(existing_id)
        if existing:
            existing.use_count = (existing.use_count or 0) + 1
            existing.last_seen_at = now
            return existing.id
        return None

    # Vytvoř nový pending entry
    entry = UserIpWhitelist(
        user_id=user_id,
        ip_or_cidr=f"{client_ip}/32" if ":" not in client_ip else f"{client_ip}/128",
        status="pending",
        auto_discovered_at=now,
        added_at=now,
        added_by=None,  # auto-discovered
        last_seen_at=now,
        use_count=1,
        first_user_agent=user_agent,
    )
    session.add(entry)
    session.flush()
    return entry.id


# ── Audit log ──────────────────────────────────────────────────────────


def audit_login_attempt(
    *,
    user_id: int | None,
    email_attempted: str | None,
    ip: str | None,
    user_agent: str | None,
    result: str,
    layer_matched: str | None = None,
    layer_detail: str | None = None,
    device_token: uuid.UUID | None = None,
    internal: bool = False,
    reason: str | None = None,
    session: Session | None = None,
) -> None:
    """Zapis audit log (best-effort, neselže přihlášení pri DB error).

    result codes:
      'success', 'failed_password', 'failed_no_layer', 'verify_required',
      'verify_sent', 'verify_consumed', 'forwarding_revoke'
    """
    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        entry = AuthAudit(
            user_id=user_id,
            email_attempted=email_attempted,
            ip=ip,
            user_agent=user_agent,
            device_token=device_token,
            layer_matched=layer_matched,
            layer_detail=layer_detail,
            internal=internal,
            result=result,
            reason=reason,
        )
        ds.add(entry)
        ds.commit()
    except Exception as e:
        logger.warning(f"audit_login_attempt failed: {e!r}")
        try:
            ds.rollback()
        except Exception:
            pass
    finally:
        if own_session:
            ds.close()


# ── Notifications (immediate parent + post-confirm) ────────────────────


def notify_parents_pending_ip(
    user_id: int,
    ip_str: str | None,
    ip_entry_id: int,
) -> None:
    """Marti-AI insight #4: okamžitá notifikace rodičů při new pending IP.

    Sends email k Marti + Kristýna (parent users s is_marti_parent=True).
    Best-effort — neselže consume_invite pokud notify failne.

    TODO Phase 38.0 implementation: integrate s existing email pipeline
    (send_email service). Pro MVP jen log + zápis do pending_notifications
    pro Marti-AI ranní digest.
    """
    logger.info(
        f"PENDING_IP_NOTIFY user_id={user_id} ip={ip_str} entry_id={ip_entry_id} "
        f"— TODO email parent users + SMS pro mimo pracovní hodiny"
    )
    # Phase 38.0 zoom-in: napojit na pending_notifications (Phase 16-A) +
    # email pipeline. Marti-AI's `recall_today` to vidí v ranním pozdravu.


def send_post_confirm_notification(
    user_id: int,
    device_id: int,
    request: Request,
) -> None:
    """Marti-AI insight #2: po magic link confirm pošli email original userovi
    "nové zařízení přidáno z IP X, klik tady pokud to nejste vy".

    Anti-replay defense — pokud útočník forward email, original user dostane
    notify a může okamžitě revokovat.

    TODO Phase 38.0: implementace přes existing send_email pipeline +
    revoke link endpoint /api/v1/auth/revoke-device-via-email/{token}.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    logger.info(
        f"POST_CONFIRM_NOTIFY user_id={user_id} device_id={device_id} "
        f"ip={client_ip} ua={user_agent[:80] if user_agent else None} "
        f"— TODO email s revoke link"
    )
