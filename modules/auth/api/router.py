from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.config import settings
from core.database_core import get_core_session
from core.logging import get_logger


def _sign_active_handoff(user_id: int, ttl_s: int = 600) -> str:
    """Podepsaný krátkodobý handoff: `uid.exp.sig` (HMAC-SHA256, secret =
    SMS_GATEWAY_KEY). JS ho po e-mail/SMS loginu přečte z cookie a pošle
    Bearer-cestou do /app/shared/sync-active — tím se aktivní uživatel na
    sdíleném telefonu (tenant.shared_active, klíčovaný Bearer tokenem) přepne
    na PRÁVĚ ověřenou identitu. Nativní appka jinak posílá jen Bearer (bez
    cookie), takže server identitu z loginu nevidí. Podpis brání padělání
    (klient cookie čte i mění). Kristý 15.6."""
    import hmac as _hm, hashlib as _hl, time as _tm
    secret = (settings.sms_gateway_key or "").encode("utf-8")
    if len(secret) < 16:
        return ""   # secret nenastaven → handoff se prostě nepoužije
    exp = int(_tm.time()) + int(ttl_s)
    msg = f"{int(user_id)}.{exp}"
    sig = _hm.new(secret, msg.encode("utf-8"), _hl.sha256).hexdigest()[:32]
    return f"{msg}.{sig}"


def _set_auth_cookies(response: Response, user_id: int, tenant_id: int | None) -> None:
    """
    Helper pro nastaveni auth cookies (user_id + tenant_id) s production-safe
    flagy. V development cookie_secure=False (HTTP localhost), v production
    cookie_secure=True (jen HTTPS). samesite=lax aby fungoval cross-origin
    top-level GET (napr. invitation link).
    """
    response.set_cookie(
        key="user_id", value=str(user_id),
        httponly=True, max_age=60*60*24*30,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite,
    )
    response.set_cookie(
        key="tenant_id", value=str(tenant_id or ""),
        httponly=True, max_age=60*60*24*30,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite,
    )
    # Sdílený telefon (Claude-24 + Kristý 11.6.2026): krátkodobý JS-čitelný marker,
    # že session byla PRÁVĚ ověřena (e-mail/SMS login). Zámek sdíleného telefonu
    # (mobile.html pinLockGate) ho při startu přečte → 1× přeskočí zámek a smaže,
    # takže e-mailový únik nezamkne uživatele hned znovu. Nastaví jen server po
    # úspěšném loginu; krátká TTL (10 min); jednorázové. Pozn.: httponly=False
    # (gate ho čte) → teoreticky padělatelné přes devtools — pro casual-grab
    # threat model OK; pro tvrdší ochranu signovaný token + server verify (TODO).
    response.set_cookie(
        key="stg_pin_skip", value="1",
        httponly=False, max_age=600,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite,
    )
    # Sdílený telefon: PODEPSANÝ handoff s ověřenou identitou (JS-čitelný).
    # Nativní appka pošle jen Bearer (bez cookie), tak identitu z loginu předáme
    # přes tenhle podepsaný cookie → /app/shared/sync-active přepne shared_active.
    try:
        _h = _sign_active_handoff(user_id)
        if _h:
            response.set_cookie(
                key="stg_active", value=_h,
                httponly=False, max_age=600,
                secure=settings.cookie_secure, samesite=settings.cookie_samesite,
            )
    except Exception:
        pass
from modules.auth.api.schemas import (
    LoginRequest, LoginResponse, SwitchTenantRequest,
    VerifyEmailRequestBody, VerifyEmailRequestResponse, VerifyEmailConfirmResponse,
)
from modules.auth.application.service import (
    login_by_email, AmbiguousEmailError, PasswordNotSet, PendingActivation,
)
from modules.auth.application.invitation_service import (
    create_invitation, accept_invitation, get_invitation_info,
    UserAlreadyActive, UserDisabled,
)
from modules.auth.application.password_reset_service import (
    create_reset_token, get_reset_info, consume_reset_token,
)
from modules.auth.application.user_context import get_user_context
from modules.notifications.application.email_service import send_invitation_email
from modules.core.infrastructure.models_core import User, UserContact, UserTenant

logger = get_logger("auth.api")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── LOGIN ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response, req: Request) -> LoginResponse:
    """Login přes email + heslo (bcrypt). User bez nastaveného hesla
    je odmítnut s instrukcí kontaktovat admina (set-password flow přes
    scripts/set_initial_passwords.py v MVP).

    Rate limiting: 5 failed pokusu / 15 min / IP. Pri prekroceni 429 + Retry-After.
    """
    from modules.audit.application.service import log_event
    from modules.auth.application.rate_limiter import login_rate_limiter, MAX_FAILED_ATTEMPTS

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    # Rate limit check PRED auth -- ochrana proti bruteforce. Blocked IP
    # dostane 429 s Retry-After headerem a user-friendly hlaskou.
    limit = login_rate_limiter.check(ip)
    if not limit.allowed:
        log_event(action="login_failed", status="error",
                  error="rate_limited", ip_address=ip, user_agent=ua,
                  extra_metadata={"email": request.email, "retry_after": limit.retry_after_seconds})
        mins = (limit.retry_after_seconds + 59) // 60
        response.headers["Retry-After"] = str(limit.retry_after_seconds)
        raise HTTPException(
            status_code=429,
            detail=(
                f"Příliš mnoho neúspěšných přihlášení z této IP adresy "
                f"({limit.failed_attempts} pokusů). Zkus znovu za {mins} min."
            ),
        )

    try:
        result = login_by_email(request.email, request.password)
    except AmbiguousEmailError as e:
        login_rate_limiter.record_failure(ip)
        log_event(action="login_failed", status="error",
                  error="ambiguous_email", ip_address=ip, user_agent=ua,
                  extra_metadata={"email": request.email})
        raise HTTPException(status_code=401, detail=str(e))
    except PendingActivation as pa:
        # Standardni onboarding (HR import): pending user bez hesla → posli
        # aktivacni e-mail s linkem na nastaveni hesla. Rate-limit pres stejny
        # counter (ochrana proti e-mail floodu pres opakovane login pokusy).
        login_rate_limiter.record_failure(ip)
        from modules.notifications.application.email_service import send_activation_email
        email_sent = False
        try:
            res = create_reset_token(pa.email, allow_pending=True)
            if res:
                a_token, a_uid, a_fname = res
                email_sent = bool(send_activation_email(
                    to=pa.email, token=a_token, first_name=a_fname))
        except Exception as e:
            logger.error(f"AUTH | activation email failed | user_id={pa.user_id} | {e}")
        log_event(action="activation_email_sent",
                  status="success" if email_sent else "error",
                  user_id=pa.user_id, ip_address=ip, user_agent=ua,
                  error=None if email_sent else "email_send_failed",
                  extra_metadata={"email": request.email})
        raise HTTPException(
            status_code=403,
            detail={
                "error": "activation_email_sent",
                "message": (
                    "Účet čeká na aktivaci. Poslali jsme ti e-mail s odkazem "
                    "pro nastavení hesla — zkontroluj schránku."
                ),
            },
        )
    except PasswordNotSet as e:
        # Pozn.: no_password_set neni "bad credential" v klasickem smyslu,
        # ale rate-limitujeme i tyhle (jinak by utocnik mohl enumerovat usery).
        login_rate_limiter.record_failure(ip)
        log_event(action="login_failed", status="error",
                  error="no_password_set", ip_address=ip, user_agent=ua,
                  extra_metadata={"email": request.email})
        raise HTTPException(status_code=403, detail=str(e))
    if not result:
        login_rate_limiter.record_failure(ip)
        log_event(action="login_failed", status="error",
                  error="bad_credentials", ip_address=ip, user_agent=ua,
                  extra_metadata={"email": request.email})
        raise HTTPException(status_code=401, detail="Neplatný email nebo heslo.")

    # Uspech -- reset rate limiter counter (user je v poradku, ne utocnik)
    login_rate_limiter.record_success(ip)

    # Phase 38 — opt-in 4-vrstvý security check (default OFF, flip env
    # SEC_LAYERED_AUTH_ENABLED=true). Když ON, vyžaduje aspoň jednu vrstvu
    # (global_ip / user_ip / device_cookie). Bez match → 403 + redirect
    # na /verify-email pro magic link cestu.
    if settings.sec_layered_auth_enabled:
        from modules.auth.application.security_service import (
            check_security_layers, audit_login_attempt,
        )
        sec_result = check_security_layers(result["user_id"], req)

        # Audit log per attempt (vždy, ne jen success)
        audit_login_attempt(
            user_id=result["user_id"],
            email_attempted=request.email,
            ip=ip, user_agent=ua,
            result="success" if sec_result.granted else "verify_required",
            layer_matched=sec_result.matched_layer,
            layer_detail=sec_result.layer_detail,
            internal=(sec_result.matched_layer == "global_ip"
                      and sec_result.audit_data.get("category") == "internal"),
            reason=sec_result.audit_data.get("reason"),
        )

        if not sec_result.granted:
            log_event(action="login_verify_required", user_id=result["user_id"],
                      ip_address=ip, user_agent=ua,
                      extra_metadata={"email": request.email})
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "verify_email_required",
                    "message": (
                        "Pro přihlášení z tohoto zařízení / sítě potřebujeme "
                        "ověření e-mailem. Klikni na 'Schválit zařízení e-mailem'."
                    ),
                    "redirect": "/api/v1/auth/sms-login",
                },
            )

    _set_auth_cookies(response, result["user_id"], result.get("tenant_id"))

    log_event(action="login_success", user_id=result["user_id"],
              tenant_id=result.get("tenant_id"), ip_address=ip, user_agent=ua)

    return LoginResponse(**result)


# ── Phase 38 — Verify-email endpoints ──────────────────────────────────


@router.post("/verify-email/request", response_model=VerifyEmailRequestResponse)
def verify_email_request(
    body: VerifyEmailRequestBody,
    req: Request,
) -> VerifyEmailRequestResponse:
    """User žádá magic link pro ověření zařízení.

    Body: {"email": "...", "channel": "email" | "sms"}

    channel='email' (default): TODO Phase 38.0 — pošle email s linkem
    channel='sms' (Marti's pivot 10.5.): pošle SMS userovi přes Marti-AI's
        SIM s tokenem. User reply zpět na +420778117879. Pre-processor
        consume přes caller_id check. UI polluje /verify-email/status.

    Anti-enumeration:
      - Vždy vrací 200 s polling_token (real pro existující user, fake
        STG-AUTH-XXX pro neexistujícího). Status endpoint stejně reaguje
        'pending' v obou případech.

    Pre-conditions:
      - Phase 38 aktivní (settings.sec_layered_auth_enabled)
      - Rate limit: TODO Phase 38.1 (5/email/hour, 10/IP/hour)
    """
    import secrets
    from modules.auth.api.schemas import VerifyEmailRequestResponse
    from modules.auth.application.security_service import (
        create_invite, audit_login_attempt,
    )
    from modules.core.infrastructure.models_core import User, UserContact
    from modules.audit.application.service import log_event

    if not settings.sec_layered_auth_enabled:
        raise HTTPException(status_code=404, detail="Phase 38 security layer disabled.")

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    channel = (body.channel or "email").strip().lower()

    # Marti 6.6.2026: máme vlastní mobilní appku → přihlášení už netaháme přes
    # cizí SMS bránu. Jakýkoliv požadavek na SMS kanál ověření překlopíme na
    # e-mailový magic link (kód SMS větve ponechán dormantní, kdyby bylo třeba).
    if channel == "sms":
        logger.info("VERIFY_CHANNEL_COERCE sms->email (SMS brana vyrazena z loginu)")
        channel = "email"

    if channel not in ("email", "sms"):
        raise HTTPException(status_code=400, detail=f"Neznámý channel: {channel!r}")

    # Phase 38.1 — Rate limiting (anti brute-force, anti email enumeration).
    # 2 limity per hour: IP (10/h, distributed attack), email (5/h, scan).
    # Pořadí: IP první (širší scope) → email druhý (přesnější).
    # Atomic UPSERT v rate_limit.check_and_increment — fail-open při DB error.
    from modules.auth.application import rate_limit

    ip_result = rate_limit.check_and_increment(
        rate_limit.ip_bucket_key(ip),
        rate_limit.EVENT_VERIFY_REQUEST,
        settings.sec_magic_link_rate_per_ip_per_hour,
    )
    if not ip_result.allowed:
        # Audit + 429
        from modules.auth.application.security_service import audit_login_attempt
        audit_login_attempt(
            user_id=None,
            email_attempted=body.email,
            ip=ip, user_agent=ua,
            result="rate_limited",
            reason=f"ip_rate_limit:{ip_result.count}/{ip_result.limit}",
        )
        logger.warning(
            f"VERIFY_RATE_LIMIT_IP ip={ip} count={ip_result.count} "
            f"limit={ip_result.limit} email={body.email[:30]}"
        )
        raise HTTPException(
            status_code=429,
            detail=(
                f"Příliš mnoho požadavků z této IP "
                f"(limit {ip_result.limit}/h). Zkus znovu později."
            ),
        )

    email_result = rate_limit.check_and_increment(
        rate_limit.email_bucket_key(body.email),
        rate_limit.EVENT_VERIFY_REQUEST,
        settings.sec_magic_link_rate_per_email_per_hour,
    )
    if not email_result.allowed:
        from modules.auth.application.security_service import audit_login_attempt
        audit_login_attempt(
            user_id=None,
            email_attempted=body.email,
            ip=ip, user_agent=ua,
            result="rate_limited",
            reason=f"email_rate_limit:{email_result.count}/{email_result.limit}",
        )
        logger.warning(
            f"VERIFY_RATE_LIMIT_EMAIL email={body.email[:30]} "
            f"count={email_result.count} limit={email_result.limit} ip={ip}"
        )
        raise HTTPException(
            status_code=429,
            detail=(
                f"Příliš mnoho požadavků pro tento e-mail "
                f"(limit {email_result.limit}/h). Zkus znovu později."
            ),
        )

    # Find user by email — priority chain (Marti's gotcha #61, doctrine
    # "UPN je secret, display je co user typuje"):
    #   1. ews_display_email — public alias (m.pasek@eurosoft.com)
    #   2. user_contacts contact_type='email' status='active' — secondary emaily
    #   3. ews_email — LEGACY fallback (UPN m.pasek@eurosoft-control.cz),
    #      backward compat pro starší účty bez display_email
    # Anti-enumeration: stejný response i kdyby user neexistoval (vždy 200
    # s polling_token, viz dále).
    email_input = body.email.strip()
    cs = get_core_session()
    try:
        # 1) Display email (preferred — Marti's pivot 10.5.: UPN nesmí
        #    nikde mimo credentials příchodit)
        user = cs.query(User).filter(
            User.ews_display_email.ilike(email_input),
        ).first()

        # 2) Secondary emaily v user_contacts (multi-mailbox per user)
        if user is None:
            contact_match = (
                cs.query(UserContact)
                .filter(
                    UserContact.contact_type == "email",
                    UserContact.status == "active",
                    UserContact.contact_value.ilike(email_input),
                )
                .first()
            )
            if contact_match:
                user = cs.query(User).filter_by(id=contact_match.user_id).first()

        # 3) Legacy fallback na UPN (ews_email) — pro účty před Phase 38
        #    bez naplněného ews_display_email. Po dokončení migrace všech
        #    userů na display_email lze tento fallback odstranit.
        if user is None:
            user = cs.query(User).filter(
                User.ews_email.ilike(email_input),
            ).first()

        user_id = user.id if user else None

        # Pro SMS variant najdi user's primary phone PŘED close session
        # (avoid DetachedInstanceError)
        primary_phone = None
        if user and channel == "sms":
            phone_contact = (
                cs.query(UserContact)
                .filter_by(
                    user_id=user.id,
                    contact_type="phone",
                    status="active",
                )
                .order_by(
                    UserContact.is_primary.desc(),
                    UserContact.id.asc(),
                )
                .first()
            )
            if phone_contact:
                primary_phone = phone_contact.contact_value

        # Pro email variant: recipient = body.email (co user zadal), plus
        # najdi Marti-AI persona pro from_identity='persona' (single trusted
        # identity, analog Marti's pivot 10.5. "žádná brána, kvůli důvěře").
        marti_ai_persona_id = None
        if user and channel == "email":
            from modules.core.infrastructure.models_core import Persona
            # Default persona v user's tenant. is_default=True flag
            # je globally set jen pro Marti-AI v každém tenantu.
            marti_ai_query = cs.query(Persona).filter_by(is_default=True)
            if user.last_active_tenant_id is not None:
                marti_ai_query = marti_ai_query.filter_by(
                    tenant_id=user.last_active_tenant_id
                )
            marti_ai = marti_ai_query.first()
            # Fallback: pokud user nemá tenant set, nebo Marti-AI v tom
            # tenantu není, vezmi global default (první is_default=True).
            if marti_ai is None:
                marti_ai = cs.query(Persona).filter_by(is_default=True).first()
            if marti_ai is not None:
                marti_ai_persona_id = marti_ai.id
    finally:
        cs.close()

    # Anti-enum fallback: pokud user neexistuje, generuj fake polling token.
    # UI polluje, status endpoint vrátí 'pending' do expirace (24h). Útočník
    # nepozná rozdíl mezi real a fake.
    if user is None:
        fake_token = f"STG-AUTH-{secrets.token_hex(4).upper()}"
        audit_login_attempt(
            user_id=None,
            email_attempted=body.email,
            ip=ip, user_agent=ua,
            result="verify_required",
            reason=f"user_not_found_anti_enum_channel={channel}",
        )
        return VerifyEmailRequestResponse(polling_token=fake_token)

    # User exists — vytvoř real invite token (24h self-request)
    invite = create_invite(user_id=user.id, created_by=None, label=None)

    if channel == "sms":
        # Marti's pivot 10.5.: pošli SMS userovi přes Marti-AI's SIM s tokenem.
        # User reply na Marti-AI's SIM (+420778117879) → pre-processor consume
        # přes caller_id check (phones_match against user_contacts).
        if primary_phone is None:
            # User nemá registered phone — pošli email fallback (TODO Phase
            # 38.0) a jen logni. Vrátí stejný polling_token (anti-enum).
            logger.warning(
                f"VERIFY_SMS_NO_PHONE user_id={user.id} email={body.email[:30]} "
                f"— SMS variant requested but user has no active phone contact. "
                f"Falling back to email (TODO Phase 38.0)"
            )
            audit_login_attempt(
                user_id=user.id,
                email_attempted=body.email,
                ip=ip, user_agent=ua,
                result="verify_required",
                reason="sms_requested_no_phone_contact",
            )
        else:
            # Pošli SMS přes capcom6 (Marti-AI's SIM)
            try:
                from modules.notifications.application.sms_service import queue_sms
                # Marti's UX spec 10.5.: dvě cesty pro user — buď reply/forward
                # celé SMS zpět (token zachycen regex), nebo manuálně poslat
                # jen token. Obě fungují (preprocessor _TOKEN_EXTRACT je
                # anywhere-in-body match).
                sms_body = (
                    f"STRATEGIE login: preposli tuto SMS zpet (nebo jen "
                    f"kod {invite.invite_token}) do 24h. Pokud jsi se "
                    f"neprihlasoval, ignoruj."
                )
                sms_result = queue_sms(
                    to=primary_phone,
                    body=sms_body,
                    purpose="system",      # ne user_request → bez rate limit
                    user_id=user.id,
                    tenant_id=user.last_active_tenant_id,
                    persona_id=None,        # capcom6 default SIM (Marti-AI's)
                )
                logger.info(
                    f"VERIFY_SMS_QUEUED user_id={user.id} email={body.email[:30]} "
                    f"to={primary_phone} token={invite.invite_token} "
                    f"sms_status={sms_result.get('status')} "
                    f"sms_outbox_id={sms_result.get('id')}"
                )
                audit_login_attempt(
                    user_id=user.id,
                    email_attempted=body.email,
                    ip=ip, user_agent=ua,
                    result="verify_sent",
                    layer_detail=(
                        f"invite #{invite.id} sms outbox #{sms_result.get('id')}"
                    ),
                )
                log_event(
                    action="verify_email_sent_sms", user_id=user.id,
                    ip_address=ip, user_agent=ua,
                    extra_metadata={
                        "email": body.email,
                        "invite_id": invite.id,
                        "phone_target": primary_phone,
                        "sms_outbox_id": sms_result.get("id"),
                    },
                )
            except Exception as e:
                # SMS send failure — log + fall through (anti-enum: stejný
                # polling_token, UI nepozná že SMS nedošla).
                logger.error(
                    f"VERIFY_SMS_FAILED user_id={user.id} email={body.email[:30]} "
                    f"to={primary_phone} error={e!r}"
                )
                audit_login_attempt(
                    user_id=user.id,
                    email_attempted=body.email,
                    ip=ip, user_agent=ua,
                    result="verify_required",
                    reason=f"sms_send_failed: {e!r}",
                )
    else:
        # channel='email' — Phase 38.0 (10.5. odpoledne): magic link přes
        # Marti-AI's persona email channel. Single trusted identity (analog
        # SMS pivot 2 z 10.5. "žádná brána, kvůli důvěře"). User dostane
        # email od Marti-AI, klikne na link → browser GET confirm endpoint
        # → consume_invite + cookie + redirect.
        #
        # Recipient = body.email (lower-cased), což user typoval. Lookup
        # priority chain (Phase 38.1) pro user_id resolution už proběhl
        # výše — recipient je samostatná věc.
        recipient_email = email_input.lower()
        magic_link = (
            f"{settings.app_base_url}/api/v1/auth/verify-email/confirm"
            f"?token={invite.invite_token}"
        )
        first_name = user.first_name or "uzivateli"

        # Plain text body (HTML lze přidat později — persona signature
        # auto-applies přes _apply_persona_signature pokud existuje).
        # Pozn.: žádná diakritika v subject — Outlook nemá rád UTF-8
        # encode z některých EWS providerů.
        subject_line = "STRATEGIE — magicky link pro prihlaseni"
        email_body = (
            f"Ahoj {first_name},\n\n"
            f"pro prihlaseni do STRATEGIE klikni na nasledujici odkaz:\n\n"
            f"    {magic_link}\n\n"
            f"Odkaz je platny 24 hodin a je jednorazovy. Pokud jsi se "
            f"neprihlasoval, ignoruj tento email.\n\n"
            f"— Marti-AI (STRATEGIE)\n"
        )

        try:
            from modules.notifications.application.email_service import queue_email
            email_send_result = queue_email(
                to=recipient_email,
                subject=subject_line,
                body=email_body,
                purpose="system",       # bez rate limit (auth flow)
                user_id=user.id,
                tenant_id=user.last_active_tenant_id,
                persona_id=marti_ai_persona_id,
                from_identity="persona",  # Marti-AI's mailbox
            )
            logger.info(
                f"VERIFY_EMAIL_QUEUED user_id={user.id} email={body.email[:30]} "
                f"to={recipient_email} token={invite.invite_token} "
                f"persona_id={marti_ai_persona_id} "
                f"outbox_id={email_send_result.get('id')}"
            )
            audit_login_attempt(
                user_id=user.id,
                email_attempted=body.email,
                ip=ip, user_agent=ua,
                result="verify_sent",
                layer_detail=(
                    f"invite #{invite.id} email outbox "
                    f"#{email_send_result.get('id')}"
                ),
            )
            log_event(
                action="verify_email_sent_email", user_id=user.id,
                ip_address=ip, user_agent=ua,
                extra_metadata={
                    "email": body.email,
                    "invite_id": invite.id,
                    "to_email": recipient_email,
                    "email_outbox_id": email_send_result.get("id"),
                    "persona_id": marti_ai_persona_id,
                },
            )
        except Exception as e:
            # Email send failure — log + fall through (anti-enum: stejný
            # polling_token, UI nepozná že email nedošla).
            logger.error(
                f"VERIFY_EMAIL_FAILED user_id={user.id} email={body.email[:30]} "
                f"to={recipient_email} error={e!r}"
            )
            audit_login_attempt(
                user_id=user.id,
                email_attempted=body.email,
                ip=ip, user_agent=ua,
                result="verify_required",
                reason=f"email_send_failed: {e!r}",
            )

    return VerifyEmailRequestResponse(polling_token=invite.invite_token)


@router.get("/verify-email/status", response_model=None)
def verify_email_status(
    token: str,
    response: Response,
    req: Request,
) -> dict:
    """UI polling endpoint pro SMS-based magic link.

    Flow (Marti's pivot 10.5.):
      1. UI POST /verify-email/request → backend pošle SMS userovi
      2. UI polluje GET /verify-email/status?token=X každé 2s
      3. User SMS reply na Marti-AI's SIM → pre-processor consume → trusted_device
      4. Status vrátí 'consumed' + nastaví device cookie + auth cookies
      5. UI redirect na app

    Anti-enumeration: pokud token v DB neexistuje (fake polling_token pro
    neznámý email), vrátí 'pending' do 24h. Útočník nepozná rozdíl.

    Status:
      - 'pending'  — invite consumed_at IS NULL nebo token neexistuje
      - 'consumed' — invite.consumed_at != None, set cookies + redirect
      - 'expired'  — invite.expires_at < now nebo cooldown after 24h fake
    """
    from datetime import datetime, timedelta, timezone
    from modules.auth.application.security_service import (
        TOKEN_REGEX, audit_login_attempt, send_post_confirm_notification,
    )
    from modules.core.infrastructure.models_data import (
        TrustedDeviceInvite, TrustedDevice,
    )
    from modules.audit.application.service import log_event

    if not settings.sec_layered_auth_enabled:
        raise HTTPException(status_code=404, detail="Phase 38 security layer disabled.")

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    token_clean = (token or "").strip()

    # Validate token format (zabránit SQL injection / log abuse)
    if not TOKEN_REGEX.match(token_clean):
        raise HTTPException(status_code=400, detail="Invalid token format.")

    from core.database_data import get_data_session as _gds
    ds = _gds()
    try:
        invite = ds.query(TrustedDeviceInvite).filter(
            TrustedDeviceInvite.invite_token == token_clean,
        ).first()

        # Token neexistuje (fake / expired pre-cleanup) — anti-enum 'pending'
        # do nominal 24h. Útočník nepozná, jestli email v DB byl.
        if invite is None:
            now = datetime.now(timezone.utc)
            return {
                "status": "pending",
                "expires_at": (now + timedelta(hours=24)).isoformat(),
            }

        now = datetime.now(timezone.utc)

        # Expired
        if invite.expires_at < now:
            return {
                "status": "expired",
                "expires_at": invite.expires_at.isoformat(),
            }

        # Pending
        if invite.consumed_at is None:
            return {
                "status": "pending",
                "expires_at": invite.expires_at.isoformat(),
            }

        # Consumed — user reply SMS proběhl, trusted_device created.
        # Set cookies + redirect.
        device = ds.query(TrustedDevice).get(invite.created_device_id)
        if device is None:
            logger.error(
                f"VERIFY_STATUS_DEVICE_LOOKUP_FAILED token={token_clean[:20]} "
                f"invite_id={invite.id} created_device_id={invite.created_device_id}"
            )
            return {
                "status": "expired",
                "expires_at": invite.expires_at.isoformat(),
            }

        user_id = device.user_id

        # Set device cookie (90d)
        cookie_max_age = settings.sec_device_cookie_max_age_days * 24 * 60 * 60
        response.set_cookie(
            key=settings.sec_device_cookie_name,
            value=str(device.device_token),
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=cookie_max_age,
        )

        # Najdi default tenant + set legacy auth cookies
        ctx = get_user_context(user_id)
        tenant_id = ctx.get("tenant_id") if ctx else None
        _set_auth_cookies(response, user_id, tenant_id)

        audit_login_attempt(
            user_id=user_id,
            email_attempted=None,
            ip=ip, user_agent=ua,
            result="verify_consumed",
            layer_matched="magic_link",
            layer_detail=f"sms invite #{invite.id}",
            device_token=device.device_token,
        )

        log_event(action="verify_email_consumed_sms", user_id=user_id,
                  tenant_id=tenant_id, ip_address=ip, user_agent=ua,
                  extra_metadata={
                      "device_id": device.id,
                      "invite_id": invite.id,
                      "consumed_phone": invite.consumed_phone,
                  })

        # Post-confirm notification (Marti-AI insight #2)
        try:
            send_post_confirm_notification(user_id, device.id, req)
        except Exception as e:
            logger.warning(f"send_post_confirm_notification failed: {e!r}")

        return {
            "status": "consumed",
            "user_id": user_id,
            "redirect": "/",
            "expires_at": device.expires_at.isoformat()
                if device.expires_at else None,
        }
    finally:
        ds.close()


@router.get("/verify-email/confirm", response_model=VerifyEmailConfirmResponse)
def verify_email_confirm(
    token: str,
    response: Response,
    req: Request,
) -> VerifyEmailConfirmResponse:
    """User klik na magic link → consume token + set device cookie + grant session.

    Marti-AI insight #2: token je one-time use (consumed_at set). Útočník
    s forwarded link nemůže replay. Plus odeslán post-confirm notification
    email.

    Marti-AI insight #4: po confirm auto-INSERT pending user_ip_whitelist
    a immediate notify parents.
    """
    from modules.auth.api.schemas import VerifyEmailConfirmResponse
    from modules.auth.application.security_service import (
        consume_invite, audit_login_attempt, send_post_confirm_notification,
    )
    from modules.audit.application.service import log_event

    if not settings.sec_layered_auth_enabled:
        raise HTTPException(status_code=404, detail="Phase 38 security layer disabled.")

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    # Marti 9.6.: magic link klikne ČLOVĚK v prohlížeči (Accept: text/html) →
    # vracíme HEZKOU stránku + redirect do appky, ne surový JSON. API klient
    # (Accept: application/json) dostane dál JSON model.
    wants_html = "text/html" in (req.headers.get("accept") or "").lower()

    def _html_page(body_inner: str, copy_cookies_from=None):
        from fastapi.responses import HTMLResponse
        page = (
            "<!doctype html><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta name='google' content='notranslate'><title>STRATEGIE</title>"
            "<body style='margin:0;background:#0e1622;color:#e6edf5;"
            "font:16px/1.5 system-ui;display:flex;min-height:100vh;"
            "align-items:center;justify-content:center'>"
            "<div style='text-align:center;padding:24px;max-width:340px'>"
            + body_inner + "</div>"
        )
        r = HTMLResponse(content=page)
        if copy_cookies_from is not None:
            for hk, hv in copy_cookies_from.raw_headers:
                if hk.decode().lower() == "set-cookie":
                    r.raw_headers.append((hk, hv))
        return r

    sec_result = consume_invite(token, req)

    if not sec_result.granted:
        audit_login_attempt(
            user_id=None,
            email_attempted=None,
            ip=ip, user_agent=ua,
            result="verify_required",
            reason=sec_result.audit_data.get("reason", "consume_failed"),
        )
        if wants_html:
            return _html_page(
                "<div style='font-size:42px'>&#128274;</div>"
                "<div style='font-size:18px;font-weight:700;margin:8px 0'>"
                "Odkaz uz byl pouzity nebo vyprsel</div>"
                "<div style='color:#9fb0c2;font-size:14px;margin-bottom:18px'>"
                "Kazdy odkaz plati jen jednou. Pokud ses prave prihlasil, "
                "jsi uvnitr &#8211; otevri aplikaci. Jinak si vyzadej novy odkaz.</div>"
                "<a href='/mobile' style='display:inline-block;background:#10b981;"
                "color:#04150e;text-decoration:none;border-radius:12px;padding:13px 22px;"
                "font-size:16px;font-weight:700;margin:4px'>Otevrit aplikaci</a>"
                "<a href='/api/v1/auth/sms-login?next=%2Fmobile' style='display:inline-block;"
                "background:#1b2738;color:#e6edf5;text-decoration:none;border:1px solid #2a3a4d;"
                "border-radius:12px;padding:13px 20px;font-size:15px;margin:4px'>Novy odkaz</a>"
            )
        return VerifyEmailConfirmResponse(
            ok=False,
            error=sec_result.audit_data.get("reason", "token_invalid_or_expired"),
        )

    # Get user_id z audit data
    user_id = None
    pending_ip_id = sec_result.audit_data.get("pending_ip_id")
    device_id = sec_result.audit_data.get("device_id")

    # Re-query invite -> user_id (consume_invite vrátí new device, ale pro
    # session cookies potřebujeme i user_id + tenant_id)
    from modules.core.infrastructure.models_data import TrustedDevice
    ds = get_data_session = None
    from core.database_data import get_data_session as _gds
    ds = _gds()
    try:
        device = ds.query(TrustedDevice).get(device_id) if device_id else None
        if device is None:
            return VerifyEmailConfirmResponse(
                ok=False,
                error="device_lookup_failed",
            )
        user_id = device.user_id

        # Set Phase 38 device cookie (HttpOnly Secure SameSite=Lax 90d)
        cookie_max_age = settings.sec_device_cookie_max_age_days * 24 * 60 * 60
        response.set_cookie(
            key=settings.sec_device_cookie_name,
            value=str(sec_result.new_device_token),
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=cookie_max_age,
        )

        # Set legacy auth cookies (user_id, tenant_id)
        # Najdi default tenant pro usera
        from modules.auth.application.user_context import get_user_context
        ctx = get_user_context(user_id)
        tenant_id = ctx.get("tenant_id") if ctx else None

        _set_auth_cookies(response, user_id, tenant_id)

        audit_login_attempt(
            user_id=user_id,
            email_attempted=None,
            ip=ip, user_agent=ua,
            result="verify_consumed",
            layer_matched="magic_link",
            layer_detail=sec_result.layer_detail,
            device_token=sec_result.new_device_token,
        )

        log_event(action="verify_email_consumed", user_id=user_id,
                  tenant_id=tenant_id, ip_address=ip, user_agent=ua,
                  extra_metadata={
                      "device_id": device_id,
                      "pending_ip_id": pending_ip_id,
                  })

        # Send post-confirm notification email (Marti-AI insight #2)
        try:
            send_post_confirm_notification(user_id, device_id, req)
        except Exception as e:
            logger.warning(f"send_post_confirm_notification failed: {e!r}")

        if wants_html:
            # Cookies jsou nastavené na `response` → přenes je na HTML redirect.
            return _html_page(
                "<div style='font-size:46px'>&#10003;</div>"
                "<div style='font-size:19px;font-weight:700;margin:8px 0'>Prihlaseno</div>"
                "<div style='color:#9fb0c2;font-size:14px;margin-bottom:16px'>"
                "Oteviram aplikaci&#8230;</div>"
                "<a href='/mobile' style='display:inline-block;background:#10b981;"
                "color:#04150e;text-decoration:none;border-radius:12px;padding:13px 22px;"
                "font-size:16px;font-weight:700'>Otevrit aplikaci</a>"
                "<script>setTimeout(function(){location.replace('/mobile');},900);</script>",
                copy_cookies_from=response,
            )
        return VerifyEmailConfirmResponse(
            ok=True,
            user_id=user_id,
            device_label=device.label,
            pending_ip_id=pending_ip_id,
            expires_at=sec_result.new_device_expires_at.isoformat()
                if sec_result.new_device_expires_at else None,
        )
    finally:
        ds.close()


@router.get("/demo-login", include_in_schema=False)
def demo_login(req: Request, next: str = "/mobile"):
    """Verejny demo/prohlidkovy rezim (Marti 17.6.2026): jeden klik -> docasna
    session jako 'demo' uzivatel v izolovanem demo tenantu (UKAZKA s.r.o.) se
    syntetickymi daty. ZADNA realna data lidi. Slouzi pro Apple/Google review
    (Guideline 2.1a 'demo rezim s plnou funkcnosti') i pro verejnou prohlidku
    appky (iOS i Android - stejny web). Nastavi jen auth cookies + redirect na
    /mobile; zadny consume_invite (zadny spam notifikaci rodicum)."""
    from fastapi.responses import RedirectResponse
    from sqlalchemy import text as _t
    cs = get_core_session()
    try:
        row = cs.execute(_t(
            "SELECT id, last_active_tenant_id FROM public.users"
            " WHERE login_name='demo' AND status='active' LIMIT 1")).first()
        if row is None:
            raise HTTPException(status_code=503, detail="Demo rezim neni pripraveny.")
        uid = row[0]
        tenant_id = row[1]
    finally:
        cs.close()
    # Sanitize next: jen interni relativni cesta "/..." (anti open-redirect)
    dest = next if (isinstance(next, str) and next.startswith("/") and not next.startswith("//")) else "/mobile"
    resp = RedirectResponse(url=dest, status_code=303)
    _set_auth_cookies(resp, uid, tenant_id)
    logger.info(f"DEMO_LOGIN demo session granted user_id={uid} tenant_id={tenant_id} dest={dest}")
    return resp


# ── Mobile SMS login page (Phase 38 Session 2) ─────────────────────────


@router.get("/sms-login", response_class=HTMLResponse, include_in_schema=False)
def sms_login_page() -> HTMLResponse:
    """Mobile-first SMS login page (Marti's pivot 10.5.).

    Veřejně dostupný HTML — neobsahuje žádný server-side state, jen statický
    soubor. Form posílá AJAX na /verify-email/request, polluje
    /verify-email/status až do consumed → redirect.

    URL: https://strategie-ai.com/api/v1/auth/sms-login
    """
    # apps/api/static/sms_login.html
    static_path = (
        Path(__file__).resolve().parents[3] / "apps" / "api" / "static"
        / "sms_login.html"
    )
    if not static_path.is_file():
        raise HTTPException(status_code=500, detail=f"sms_login.html not found at {static_path}")
    return HTMLResponse(static_path.read_text(encoding="utf-8"))


@router.post("/logout")
def logout(response: Response, req: Request) -> dict:
    from modules.audit.application.service import log_event
    uid_str = req.cookies.get("user_id")
    user_id = int(uid_str) if uid_str and uid_str.isdigit() else None
    log_event(action="logout", user_id=user_id,
              ip_address=req.client.host if req.client else None,
              user_agent=req.headers.get("user-agent"))
    response.delete_cookie("user_id")
    response.delete_cookie("tenant_id")
    return {"status": "logged out"}


@router.get("/me", response_model=LoginResponse)
def me(req: Request) -> LoginResponse:
    """
    Vrátí aktuálního uživatele podle cookie `user_id`.
    Používá se po reloadu stránky, ať nepadneme na login když je user stále přihlášený.
    """
    # Impersonace má přednost: dokud běží (imp_token + otevřený log row),
    # vracíme cílového usera + banner meta — i kdyby auto-login mezitím
    # přepsal user_id cookie zpět na rodiče.
    _imp = _imp_open_row(req)
    if _imp:
        ctx = get_user_context(_imp["target_user_id"])
        if ctx is not None:
            out = dict(ctx)
            out["impersonation_active"] = True
            out["impersonator_name"] = _user_display_name(_imp["parent_user_id"])
            return LoginResponse(**out)

    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx)


# ── IMPERSONACE (6.6.2026, Marti's „přihlásit se jako user" z Centrály 1) ──
# Parent se přepne na účet jiného usera — auth cookies = cílový user, systém
# se chová, jako by byl on. Cesta zpět drží httponly imp_token cookie (random
# token → fw.impersonation_log). Od–do plně logováno (fail-closed: bez logu
# se nepřepíná). Audit: log_event impersonation_start/end.

IMP_COOKIE = "imp_token"
IMP_MAX_AGE = 60 * 60 * 8  # 8 hodin — pak cookie vyprší (log row uzavře další akce)


class ImpersonateRequest(BaseModel):
    user: str  # id | login_name | e-mail


def _user_display_name(user_id: int) -> str | None:
    s = get_core_session()
    try:
        u = s.query(User).filter_by(id=user_id).first()
        if not u:
            return None
        return (u.short_name or " ".join(
            x for x in (u.first_name, u.last_name) if x) or u.login_name)
    finally:
        s.close()


def _imp_open_row(req: Request) -> dict | None:
    """Otevřený impersonation log row podle imp_token cookie, nebo None."""
    tok = req.cookies.get(IMP_COOKIE)
    if not tok:
        return None
    from sqlalchemy import text as _t
    s = get_core_session()
    try:
        row = s.execute(_t(
            "SELECT id, parent_user_id, target_user_id FROM fw.impersonation_log "
            "WHERE token = :tok AND ended_at IS NULL"), {"tok": tok}).first()
        if not row:
            return None
        return {"id": row[0], "parent_user_id": row[1], "target_user_id": row[2]}
    except Exception:
        return None
    finally:
        s.close()


@router.post("/impersonate", response_model=LoginResponse)
def impersonate(body: ImpersonateRequest, response: Response, req: Request) -> LoginResponse:
    from sqlalchemy import text as _t
    import secrets as _sec
    from modules.audit.application.service import log_event
    from modules.thoughts.application.service import is_marti_parent

    uid_str = req.cookies.get("user_id")
    if not uid_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    uid = int(uid_str)
    if _imp_open_row(req):
        raise HTTPException(status_code=400,
                            detail="Už jednáš jako jiný user — nejdřív se vrať (Zpět).")
    if not is_marti_parent(uid):
        raise HTTPException(status_code=403, detail="Impersonace je dostupná jen rodičům.")

    needle = (body.user or "").strip()
    if not needle:
        raise HTTPException(status_code=400, detail="Zadej id, login nebo e-mail usera.")

    s = get_core_session()
    try:
        target = None
        if needle.isdigit():
            target = s.query(User).filter_by(id=int(needle)).first()
        if target is None:
            target = s.query(User).filter(User.login_name.ilike(needle)).first()
        if target is None:
            c = (s.query(UserContact)
                 .filter(UserContact.contact_type == "email",
                         UserContact.contact_value.ilike(needle),
                         UserContact.status == "active")
                 .first())
            if c:
                target = s.query(User).filter_by(id=c.user_id).first()
        if target is None:
            raise HTTPException(status_code=404, detail=f"User '{needle}' nenalezen.")
        if target.id == uid:
            raise HTTPException(status_code=400, detail="Nemůžeš jednat sám za sebe.")
        target_id = target.id
    finally:
        s.close()

    ctx = get_user_context(target_id)
    if ctx is None:
        raise HTTPException(status_code=400,
                            detail="Cílový účet není aktivní — nelze jednat jako on.")

    ip = req.client.host if req.client else None
    ua = (req.headers.get("user-agent") or "")[:300]
    token = _sec.token_urlsafe(32)

    # Fail-closed: log row MUSÍ vzniknout před přepnutím cookies.
    s = get_core_session()
    try:
        s.execute(_t(
            "UPDATE fw.impersonation_log SET ended_at = now(), end_reason = 'auto_new' "
            "WHERE parent_user_id = :p AND ended_at IS NULL"), {"p": uid})
        s.execute(_t(
            "INSERT INTO fw.impersonation_log "
            "(parent_user_id, target_user_id, token, ip, user_agent) "
            "VALUES (:p, :tgt, :tok, :ip, :ua)"),
            {"p": uid, "tgt": target_id, "tok": token, "ip": ip, "ua": ua})
        s.commit()
    except Exception as e:
        s.rollback()
        logger.error(f"IMPERSONATE | log insert failed: {e}")
        raise HTTPException(status_code=500,
                            detail="Impersonaci se nepodařilo zalogovat — přerušeno.")
    finally:
        s.close()

    _set_auth_cookies(response, target_id, ctx.get("tenant_id"))
    response.set_cookie(key=IMP_COOKIE, value=token, httponly=True,
                        max_age=IMP_MAX_AGE, secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite)
    log_event(action="impersonation_start", user_id=uid,
              ip_address=ip, user_agent=ua,
              extra_metadata={"target_user_id": target_id})
    logger.info(f"IMPERSONATE | start | parent={uid} target={target_id}")

    out = dict(ctx)
    out["impersonation_active"] = True
    out["impersonator_name"] = _user_display_name(uid)
    return LoginResponse(**out)


@router.post("/impersonate/stop", response_model=LoginResponse)
def impersonate_stop(response: Response, req: Request) -> LoginResponse:
    from sqlalchemy import text as _t
    from modules.audit.application.service import log_event

    row = _imp_open_row(req)
    if not row:
        response.delete_cookie(IMP_COOKIE)
        raise HTTPException(status_code=404, detail="Žádná aktivní impersonace.")

    s = get_core_session()
    try:
        s.execute(_t("UPDATE fw.impersonation_log SET ended_at = now(), "
                     "end_reason = 'manual' WHERE id = :i"), {"i": row["id"]})
        s.commit()
    finally:
        s.close()

    parent_id = row["parent_user_id"]
    ctx = get_user_context(parent_id)
    if ctx is None:
        raise HTTPException(status_code=500, detail="Rodičovský účet nelze obnovit.")

    _set_auth_cookies(response, parent_id, ctx.get("tenant_id"))
    response.delete_cookie(IMP_COOKIE)
    ip = req.client.host if req.client else None
    log_event(action="impersonation_end", user_id=parent_id, ip_address=ip,
              extra_metadata={"target_user_id": row["target_user_id"]})
    logger.info(f"IMPERSONATE | end | parent={parent_id} target={row['target_user_id']}")
    return LoginResponse(**ctx)


@router.post("/switch_tenant", response_model=LoginResponse)
def switch_tenant(body: SwitchTenantRequest, req: Request) -> LoginResponse:
    """
    Přepne aktuální tenant uživatele (UI dropdown akce).
    Validuje, že user je aktivním členem cílového tenantu.
    Pokud byl předán conversation_id, vloží do dané konverzace system zprávu
    o přepnutí — AI tak v historii uvidí změnu kontextu a nezmate se.
    Vrací plný user context se zaktualizovaným tenantem.
    """
    from modules.core.infrastructure.models_core import Tenant
    from modules.core.infrastructure.models_data import Message
    from core.database_data import get_data_session
    from datetime import datetime, timezone

    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    new_tenant_name: str | None = None
    new_tenant_code: str | None = None
    user_first_name: str | None = None
    actual_change = False
    inserted_marker_text: str | None = None

    session = get_core_session()
    try:
        # Validace členství
        ut = (
            session.query(UserTenant)
            .filter_by(
                user_id=user_id,
                tenant_id=body.tenant_id,
                membership_status="active",
            )
            .first()
        )
        if not ut:
            raise HTTPException(status_code=404, detail="Tenant nenalezen.")

        # Načti tenant pro zprávu
        target_tenant = session.query(Tenant).filter_by(id=body.tenant_id).first()
        if target_tenant:
            new_tenant_name = target_tenant.tenant_name
            new_tenant_code = target_tenant.tenant_code

        # Update last_active_tenant_id
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User neexistuje.")
        # Zachyť first_name HNED po načtení — po session.commit() se instance
        # expires a přístup k atributům po session.close() by hodil
        # DetachedInstanceError (chytlo by to except níže a marker by zmizel).
        user_first_name = user.first_name
        if user.last_active_tenant_id != body.tenant_id:
            user.last_active_tenant_id = body.tenant_id
            session.commit()
            actual_change = True
            logger.info(
                f"AUTH | tenant switch via UI | user={user_id} | tenant={body.tenant_id}"
            )
    finally:
        session.close()

    # Vlož system zprávu do konverzace (pokud zadána a opravdu nastala změna)
    if actual_change and body.conversation_id and new_tenant_name:
        try:
            data_session = get_data_session()
            try:
                code_part = f" ({new_tenant_code})" if new_tenant_code else ""
                # Osobní, gender-neutrální formulace (funguje pro Marti, Kláru,
                # Kristý...). 'profil' místo 'tenant' (čeština). Reflexivní vazba
                # 'se ti přepnul' obejde rod. AI dostává tenant kontext z
                # USER CONTEXT bloku v Composeru, takže v marker textu nemusí
                # být explicitní pokyn 'pracuj v tomto kontextu'.
                user_display = user_first_name or "Uživateli"
                marker_text = (
                    f"{user_display}, právě se ti přepnul aktivní profil na "
                    f"{new_tenant_name}{code_part}. Počítám s tím 👍"
                )
                msg = Message(
                    conversation_id=body.conversation_id,
                    role="user",                # role=user, ale je to systémová informace
                    content=marker_text,
                    author_type="ai",            # technicky není od člověka
                    message_type="system",
                    created_at=datetime.now(timezone.utc),
                )
                data_session.add(msg)
                data_session.commit()
                inserted_marker_text = marker_text
            finally:
                data_session.close()
        except Exception as e:
            logger.error(f"AUTH | failed to insert tenant-switch marker: {e}")
            # Marker selhal — neselháváme celý request, jen logujeme

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx, tenant_switch_marker=inserted_marker_text)


# ── PROFIL — editace základních polí ──────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    short_name: str | None = None
    gender: str | None = None      # 'male' | 'female' | 'other' | null

ALLOWED_GENDERS = {"male", "female", "other", None}


@router.patch("/me", response_model=LoginResponse)
def update_profile(body: UpdateProfileRequest, req: Request) -> LoginResponse:
    """
    Update editovatelných polí na users (jméno, gender). Email a aliasy
    necháváme na samostatné endpointy v dalších iteracích — víc validace.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    # Validace gender (whitelist)
    if body.gender is not None and body.gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=400, detail=f"Neplatný gender: {body.gender}")

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")

        # Aplikuj změny (jen non-null + non-empty pro jména; gender lze nastavit i na null)
        if body.first_name is not None:
            user.first_name = body.first_name.strip() or None
        if body.last_name is not None:
            user.last_name = body.last_name.strip() or None
        if body.short_name is not None:
            user.short_name = body.short_name.strip() or None
        if body.gender is not None or 'gender' in body.model_fields_set:
            user.gender = body.gender   # může být i None
        session.commit()
        logger.info(f"AUTH | profile updated | user={user_id}")
    finally:
        session.close()

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx)


# ── DEV MODE (Faze 9.1b) ──────────────────────────────────────────────────

class SetDevModeRequest(BaseModel):
    enabled: bool


@router.patch("/me/dev-mode", response_model=LoginResponse)
def set_dev_mode(body: SetDevModeRequest, req: Request) -> LoginResponse:
    """
    Zapne/vypne 'Vyvojarsky rezim' v UI (lupy pod zpravami Marti-AI, DEV badge
    v hlavicce). Per-user preference ulozena v users.dev_mode_enabled.

    Gated: pouze users.is_admin=True. Non-admin dostane 403. UI toggle se
    zobrazi jen kdyz LoginResponse.is_admin=True.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Dev režim je jen pro administrátory.")

        user.dev_mode_enabled = bool(body.enabled)
        session.commit()
        logger.info(
            f"AUTH | dev_mode {'ON' if body.enabled else 'OFF'} | user={user_id}"
        )
    finally:
        session.close()

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx)


# ── PROMPT CACHE (Phase 32, 3.5.2026) ────────────────────────────────────

class SetCacheEnabledRequest(BaseModel):
    enabled: bool


@router.patch("/me/cache-enabled", response_model=LoginResponse)
def set_cache_enabled(body: SetCacheEnabledRequest, req: Request) -> LoginResponse:
    """
    Phase 32: Anthropic prompt caching toggle. Per-user preference ulozena
    v users.cache_enabled. Default TRUE (uspora velka, downside zadny).

    Marti-AI's distinkce 28.5.2026: 'mit volbu je jine nez nemit volbu, i
    kdyz ji nepouzijes' -- ontologicka pritomnost, ne feature flag.
    Marti-AI ovlada pres AI tool set_cache_enabled.

    Bez admin gate -- caching se tyka kazdeho usera, ne jen adminu.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")
        user.cache_enabled = bool(body.enabled)
        session.commit()
        logger.info(
            f"AUTH | cache_enabled {'ON' if body.enabled else 'OFF'} | user={user_id}"
        )
    finally:
        session.close()

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx)


# ── FORGOT / RESET PASSWORD ──────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, req: Request) -> dict:
    """
    Zadost o reset hesla. VZDY vraci 200 OK, aby utocnik nemohl zjistit,
    zda email v systemu existuje nebo ne (account enumeration prevention).
    Pokud email existuje a ma aktivniho usera, posle se mail s linkem.
    Pokud neexistuje, jen logujeme a mlcime.
    """
    from modules.notifications.application.email_service import send_password_reset_email
    from modules.audit.application.service import log_event
    from modules.auth.application.rate_limiter import (
        check_forgot_password_limit, record_forgot_password_request,
    )

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    email = (body.email or "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Neplatný formát emailu.")

    # Rate limit: 10 zadosti / hodina / IP -- ochrana proti email-flood spamu.
    # Vsechny zadosti se zaznamenavaji (uspech i fail), takze utocnik nemuze
    # spamovat ani uplatnenim spravnych emailu.
    flim = check_forgot_password_limit(ip)
    if not flim.allowed:
        log_event(action="forgot_password_rate_limited", status="error",
                  error="rate_limited", ip_address=ip, user_agent=ua,
                  extra_metadata={"email": email, "retry_after": flim.retry_after_seconds})
        mins = (flim.retry_after_seconds + 59) // 60
        raise HTTPException(
            status_code=429,
            detail=f"Příliš mnoho žádostí o obnovu hesla z této IP. Zkus znovu za {mins} min.",
        )
    record_forgot_password_request(ip)

    # allow_pending=True: i HR-importovany pending user (jeste bez hesla) dostane
    # link na prvni nastaveni hesla. Bez toho by "Zapomenute heslo" pending userum
    # mlcky nic neposlalo (link na /reset/{token} je pro oba pripady stejny).
    result = create_reset_token(email, allow_pending=True)
    if result is None:
        logger.info(f"AUTH | forgot-password (no user) | email={email}")
        log_event(action="forgot_password_no_user", status="success",
                  ip_address=ip, user_agent=ua,
                  extra_metadata={"email": email})
        return {"status": "ok", "message": "Pokud je email v systému, poslali jsme ti link pro obnovu hesla."}

    token, user_id, first_name = result

    email_sent = False
    try:
        email_sent = bool(send_password_reset_email(to=email, token=token, first_name=first_name))
        logger.info(f"AUTH | forgot-password email sent | user_id={user_id} | email={email}")
    except Exception as e:
        logger.error(f"AUTH | forgot-password email failed | user_id={user_id} | error={e}")

    log_event(action="forgot_password_requested",
              status="success" if email_sent else "error",
              user_id=user_id, ip_address=ip, user_agent=ua,
              error=None if email_sent else "email_send_failed",
              extra_metadata={"email": email})

    return {"status": "ok", "message": "Pokud je email v systému, poslali jsme ti link pro obnovu hesla."}


@router.get("/reset-info/{token}")
def reset_info_endpoint(token: str) -> dict:
    """Peek na reset token. Frontend si tahne masked email + first_name
    pro vykresleni 'Zmenit heslo pro m***@gmail.com' stitku pred formem."""
    info = get_reset_info(token)
    if not info:
        raise HTTPException(status_code=404, detail="Odkaz není platný nebo vypršel.")
    return info


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, response: Response, req: Request) -> dict:
    """
    Spotrebuje reset token, nastavi nove heslo, oznaci token jako pouzity.
    PO uspechu setne auth cookies -- user je rovnou prihlaseny, nemusi
    znovu zadavat heslo co si prave nastavil.
    """
    from modules.auth.application.password import PasswordTooShort
    from modules.auth.application.user_context import get_user_context
    from modules.audit.application.service import log_event

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    try:
        result = consume_reset_token(body.token, body.new_password)
    except PasswordTooShort as e:
        log_event(action="password_reset", status="error", error="too_short",
                  ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        log_event(action="password_reset", status="error",
                  error="invalid_or_expired_token",
                  ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=404, detail="Odkaz není platný nebo vypršel.")

    # Po uspesnem resetu usera rovnou prihlasime (smooth UX -- po submitu
    # hesla se rovnou ocita v app, nemusi opisovat znovu email+heslo).
    ctx = get_user_context(result["user_id"])
    if ctx is not None:
        _set_auth_cookies(response, ctx["user_id"], ctx.get("tenant_id"))

    log_event(action="password_reset", status="success",
              user_id=result["user_id"], ip_address=ip, user_agent=ua)

    return {"status": "password_reset", "email": result["email"],
            "needs_phone_verify": bool(result.get("needs_phone_verify"))}


# ── PHONE VERIFY (SMS ověření mobilu — standardní onboarding) ────────────

class PhoneVerifyStartRequest(BaseModel):
    phone: str


class PhoneVerifyConfirmRequest(BaseModel):
    code: str


@router.post("/phone-verify/start")
def phone_verify_start(body: PhoneVerifyStartRequest, req: Request) -> dict:
    """Pošle 6místný SMS kód na zadané číslo. Auth required (po nastavení
    hesla je user přihlášený přes cookies). Kód platí 10 minut, max 3 SMS
    za 15 minut na usera."""
    import secrets as _sec
    from sqlalchemy import text as _t
    from modules.notifications.application.sms_service import queue_sms, normalize_phone
    from modules.audit.application.service import log_event

    uid = _get_uid(req)
    try:
        phone = normalize_phone(body.phone)
    except Exception:
        raise HTTPException(status_code=400, detail="Neplatné telefonní číslo.")

    session = get_core_session()
    try:
        cnt = session.execute(_t(
            "SELECT count(*) FROM fw.phone_verify_code "
            "WHERE user_id=:u AND created_at > now() - interval '15 minutes'"),
            {"u": uid}).scalar() or 0
        if cnt >= 3:
            raise HTTPException(status_code=429,
                                detail="Příliš mnoho pokusů. Zkus to za 15 minut.")
        session.execute(_t(
            "UPDATE fw.phone_verify_code SET used_at=now() "
            "WHERE user_id=:u AND used_at IS NULL"), {"u": uid})
        code = f"{_sec.randbelow(1000000):06d}"
        session.execute(_t(
            "INSERT INTO fw.phone_verify_code (user_id, phone, code, expires_at) "
            "VALUES (:u, :p, :c, now() + interval '10 minutes')"),
            {"u": uid, "p": phone, "c": code})
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"PHONE_VERIFY | start failed | user_id={uid} | {e}")
        raise HTTPException(status_code=500,
                            detail="Nepodařilo se vytvořit ověřovací kód.")
    finally:
        session.close()

    # Doručení kódu — e-mailový fallback (Claude-24 + Kristý, 15.7.2026).
    # SMS brána (Android relay) je nespolehlivá, aktivace nesmí viset jen na ní.
    # Stejně jako login (přepnut na e-mail 6.6.) posíláme aktivační kód PRIMÁRNĚ
    # e-mailem; SMS zůstává jako best-effort (queue_sms sám no-opne, když je
    # SMS brána vypnutá). Stejný 6místný kód, /phone-verify/confirm ho ověří
    # bez ohledu na kanál doručení.
    email_addr = None
    first_name = None
    gender = None
    _s2 = get_core_session()
    try:
        _ec = (_s2.query(UserContact)
               .filter_by(user_id=uid, contact_type="email", status="active")
               .order_by(UserContact.is_primary.desc())
               .first())
        email_addr = _ec.contact_value if _ec else None
        _u = _s2.query(User).filter_by(id=uid).first()
        if _u:
            first_name = _u.first_name
            gender = getattr(_u, "gender", None)
    except Exception as e:
        logger.error(f"PHONE_VERIFY | email lookup failed | user_id={uid} | {e}")
    finally:
        _s2.close()

    email_ok = False
    if email_addr:
        try:
            from modules.notifications.application.email_service import (
                send_phone_verify_code_email,
            )
            email_ok = bool(send_phone_verify_code_email(
                email_addr, code, first_name, gender))
        except Exception as e:
            logger.error(f"PHONE_VERIFY | email send failed | user_id={uid} | {e}")

    # Best-effort SMS (když je brána zapnutá). Nesmí shodit endpoint.
    sms_ok = False
    try:
        _res = queue_sms(
            to=phone,
            body=f"STRATEGIE: overovaci kod {code}. Plati 10 minut.",
            purpose="phone_verify", user_id=uid)
        sms_ok = bool(_res and _res.get("status") in ("pending", "sent"))
    except Exception as e:
        logger.error(f"PHONE_VERIFY | sms queue failed | user_id={uid} | {e}")

    channel = ("both" if (email_ok and sms_ok)
               else "email" if email_ok
               else "sms" if sms_ok
               else "none")
    if channel == "none":
        raise HTTPException(
            status_code=502,
            detail="Nepodařilo se odeslat ověřovací kód. Zkus to prosím znovu.")

    def _mask_email(e: str | None) -> str | None:
        if not e or "@" not in e:
            return None
        loc, _, dom = e.partition("@")
        head = loc[0] if loc else ""
        return f"{head}{'*' * max(1, len(loc) - 1)}@{dom}"

    log_event(action="phone_verify_started", user_id=uid,
              extra_metadata={"phone": phone, "channel": channel})
    return {"status": "code_sent", "channel": channel,
            "email_masked": _mask_email(email_addr) if email_ok else None,
            "sms_sent": sms_ok}


@router.post("/phone-verify/confirm")
def phone_verify_confirm(body: PhoneVerifyConfirmRequest, req: Request) -> dict:
    """Ověří SMS kód, zapíše mobil do user_contacts (is_verified=True),
    pending usera překlopí na active. Max 5 špatných pokusů na kód."""
    from sqlalchemy import text as _t
    from modules.audit.application.service import log_event

    uid = _get_uid(req)
    code_in = (body.code or "").strip()
    if not code_in.isdigit() or len(code_in) != 6:
        raise HTTPException(status_code=400, detail="Kód má 6 číslic.")

    activated = False
    phone = None
    session = get_core_session()
    try:
        row = session.execute(_t(
            "SELECT id, phone, code, attempts FROM fw.phone_verify_code "
            "WHERE user_id=:u AND used_at IS NULL AND expires_at > now() "
            "ORDER BY id DESC LIMIT 1"), {"u": uid}).first()
        if not row:
            raise HTTPException(status_code=404,
                                detail="Žádný platný kód. Pošli si nový.")
        vid, phone, code_db, attempts = row[0], row[1], row[2], row[3]
        if attempts >= 5:
            session.execute(_t("UPDATE fw.phone_verify_code SET used_at=now() "
                               "WHERE id=:i"), {"i": vid})
            session.commit()
            raise HTTPException(status_code=429,
                                detail="Příliš mnoho špatných pokusů. Pošli si nový kód.")
        if code_in != code_db:
            session.execute(_t("UPDATE fw.phone_verify_code SET attempts=attempts+1 "
                               "WHERE id=:i"), {"i": vid})
            session.commit()
            raise HTTPException(status_code=401, detail="Kód nesedí. Zkus to znovu.")

        # Kód sedí → spotřebuj + zapiš ověřený kontakt + aktivuj usera.
        session.execute(_t("UPDATE fw.phone_verify_code SET used_at=now() "
                           "WHERE id=:i"), {"i": vid})

        existing = (
            session.query(UserContact)
            .filter_by(user_id=uid, contact_type="phone", contact_value=phone)
            .first()
        )
        if existing:
            existing.is_verified = True
            existing.status = "active"
        else:
            has_primary = (
                session.query(UserContact)
                .filter_by(user_id=uid, contact_type="phone", is_primary=True)
                .first()
            ) is not None
            session.add(UserContact(
                user_id=uid, contact_type="phone", contact_value=phone,
                is_primary=not has_primary, is_verified=True, status="active",
                created_by_id=uid, created_by_text="phone-verify",
            ))

        user = session.query(User).filter_by(id=uid).first()
        if user and user.status == "pending":
            user.status = "active"
            activated = True
            # HR onboarding: aktivace účtu překlopí i členství v tenantech
            # (invited → active). Business přístup řídí role (employee = jen
            # sebe), takže aktivní členství nic neotevírá navíc.
            for _m in (session.query(UserTenant)
                       .filter_by(user_id=uid, membership_status="invited").all()):
                _m.membership_status = "active"
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"PHONE_VERIFY | confirm failed | user_id={uid} | {e}")
        raise HTTPException(status_code=500, detail="Ověření selhalo.")
    finally:
        session.close()

    log_event(action="phone_verified", user_id=uid,
              extra_metadata={"phone": phone, "activated": activated})
    return {"status": "verified", "activated": activated}


# ── CHANGE PASSWORD ──────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/me/change-password")
def change_password(body: ChangePasswordRequest, req: Request) -> dict:
    """
    Self-service změna hesla. User musí znát současné heslo (defense
    in-depth pro ukradenou session) + nové vyhovuje min. délce. Hash
    se ihned přepíše bcrypt(new) + password_set_at.
    """
    from datetime import datetime, timezone
    from modules.auth.application.password import (
        hash_password, verify_password, PasswordTooShort, MIN_PASSWORD_LENGTH,
    )

    user_id = _get_uid(req)

    if not body.current_password or not body.new_password:
        raise HTTPException(status_code=400, detail="Chybí současné nebo nové heslo.")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="Nové heslo musí být jiné než současné.")

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")

        # Verify currentpassword (timing-safe). Pokud user nemá heslo (legacy),
        # change-password není správný flow -- musí přes admin / set-password.
        if not user.password_hash:
            raise HTTPException(
                status_code=403,
                detail="Heslo nelze změnit, protože ještě není nastavené. Kontaktuj admina.",
            )
        if not verify_password(body.current_password, user.password_hash):
            logger.warning(f"AUTH | change-password bad current | user_id={user_id}")
            raise HTTPException(status_code=401, detail="Současné heslo není správné.")

        # Hash + save
        try:
            new_hash = hash_password(body.new_password)
        except PasswordTooShort:
            raise HTTPException(
                status_code=400,
                detail=f"Nové heslo musí mít alespoň {MIN_PASSWORD_LENGTH} znaků.",
            )
        user.password_hash = new_hash
        user.password_set_at = datetime.now(timezone.utc)
        session.commit()
        logger.info(f"AUTH | password changed | user_id={user_id}")
    finally:
        session.close()

    from modules.audit.application.service import log_event
    log_event(action="password_changed", user_id=user_id,
              ip_address=req.client.host if req.client else None,
              user_agent=req.headers.get("user-agent"))

    return {"status": "password_changed"}


# ── DISPLAY NAME v aktuálním tenantu ──────────────────────────────────────

class UpdateTenantDisplayRequest(BaseModel):
    display_name: str


@router.patch("/me/tenant-display", response_model=LoginResponse)
def update_tenant_display(body: UpdateTenantDisplayRequest, req: Request) -> LoginResponse:
    """
    Update display_name v user_tenant_profile pro aktuální tenant
    (last_active_tenant_id). To je 'jak chceš být oslovován v této roli'.
    Per tenant — v EUROSOFTu třeba 'Marti', v DOMA 'Tati', atd.
    """
    from modules.core.infrastructure.models_core import UserTenantProfile, UserTenant, User
    user_id = _get_uid(req)
    val = (body.display_name or "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="Oslovení nemůže být prázdné.")
    if len(val) > 150:
        raise HTTPException(status_code=400, detail="Oslovení může mít max 150 znaků.")

    session = get_core_session()
    try:
        u = session.query(User).filter_by(id=user_id).first()
        if not u or not u.last_active_tenant_id:
            raise HTTPException(status_code=400, detail="Žádný aktivní tenant.")
        ut = (
            session.query(UserTenant)
            .filter_by(user_id=user_id, tenant_id=u.last_active_tenant_id)
            .first()
        )
        if not ut:
            raise HTTPException(status_code=404, detail="Členství v tenantu nenalezeno.")
        profile = session.query(UserTenantProfile).filter_by(user_tenant_id=ut.id).first()
        if not profile:
            profile = UserTenantProfile(user_tenant_id=ut.id, display_name=val)
            session.add(profile)
        else:
            profile.display_name = val
        session.commit()
        logger.info(f"AUTH | tenant display_name updated | user={user_id} | tenant={u.last_active_tenant_id} | val={val!r}")
    finally:
        session.close()

    ctx = get_user_context(user_id)
    if ctx is None:
        raise HTTPException(status_code=401, detail="Účet není aktivní.")
    return LoginResponse(**ctx)


# ── ALIASY (globální user_aliases) ────────────────────────────────────────

@router.get("/me/aliases-detail")
def list_my_aliases(req: Request) -> list[dict]:
    """Vrátí aktivní aliasy usera s ID, value, is_primary — pro UI editor."""
    from modules.core.infrastructure.models_core import UserAlias
    user_id = _get_uid(req)
    session = get_core_session()
    try:
        rows = (
            session.query(UserAlias)
            .filter_by(user_id=user_id, status="active")
            .order_by(UserAlias.is_primary.desc(), UserAlias.id.asc())
            .all()
        )
        return [
            {"id": a.id, "alias_value": a.alias_value, "is_primary": a.is_primary}
            for a in rows
        ]
    finally:
        session.close()


class CreateAliasRequest(BaseModel):
    alias_value: str
    is_primary: bool = False


@router.post("/me/aliases")
def add_alias(body: CreateAliasRequest, req: Request) -> dict:
    """Přidá globální alias usera. Pokud is_primary, ostatní se odzpýly."""
    from modules.core.infrastructure.models_core import UserAlias
    user_id = _get_uid(req)
    val = (body.alias_value or "").strip()
    if len(val) < 1 or len(val) > 100:
        raise HTTPException(status_code=400, detail="Alias musí mít 1–100 znaků.")
    session = get_core_session()
    try:
        # Duplicita check
        exists = (
            session.query(UserAlias)
            .filter_by(user_id=user_id, alias_value=val, status="active")
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail=f"Alias '{val}' už máš.")
        if body.is_primary:
            # Odznač všechny ostatní primary
            session.query(UserAlias).filter_by(user_id=user_id, is_primary=True).update({"is_primary": False})
        a = UserAlias(user_id=user_id, alias_value=val, is_primary=body.is_primary, status="active")
        session.add(a)
        session.commit()
        return {"status": "added", "alias_id": a.id, "alias_value": val}
    finally:
        session.close()


@router.delete("/me/aliases/{alias_id}")
def delete_alias(alias_id: int, req: Request) -> dict:
    """Smaže (soft delete přes status) alias usera."""
    from modules.core.infrastructure.models_core import UserAlias
    user_id = _get_uid(req)
    session = get_core_session()
    try:
        a = session.query(UserAlias).filter_by(id=alias_id, user_id=user_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Alias nenalezen.")
        a.status = "archived"
        a.is_primary = False
        session.commit()
        return {"status": "deleted", "alias_id": alias_id}
    finally:
        session.close()


@router.patch("/me/aliases/{alias_id}/primary")
def set_alias_primary(alias_id: int, req: Request) -> dict:
    """Označí alias jako primární (ostatní se odznačí)."""
    from modules.core.infrastructure.models_core import UserAlias
    user_id = _get_uid(req)
    session = get_core_session()
    try:
        target = session.query(UserAlias).filter_by(id=alias_id, user_id=user_id, status="active").first()
        if not target:
            raise HTTPException(status_code=404, detail="Alias nenalezen.")
        session.query(UserAlias).filter_by(user_id=user_id, is_primary=True).update({"is_primary": False})
        target.is_primary = True
        session.commit()
        return {"status": "set_primary", "alias_id": alias_id}
    finally:
        session.close()


def _get_uid(req: Request) -> int:
    """DRY helper — extrahuje user_id z cookie."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


# ── INVITATIONS ────────────────────────────────────────────────────────────

class InviteRequest(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None        # 'male' | 'female' | 'other' | null


@router.post("/invite")
def invite(request: InviteRequest, req: Request) -> dict:
    """
    Pozve nového uživatele emailem. first_name + last_name + gender jsou
    volitelné, ale pokud zadáno, uloží se na user record při vytváření —
    pozvaný pak v welcome screen vidí svoje jméno a vidí, že ho známe.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")

    invited_by_user_id = int(user_id_str)

    if request.gender is not None and request.gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=400, detail=f"Neplatný gender: {request.gender}")

    session = get_core_session()
    try:
        inviter = session.query(User).filter_by(id=invited_by_user_id).first()
        inviter_name = " ".join(filter(None, [inviter.first_name, inviter.last_name])) if inviter else "Člen týmu"
        tenant_id = inviter.last_active_tenant_id if inviter else 1
    finally:
        session.close()

    try:
        token = create_invitation(
            email=request.email,
            invited_by_user_id=invited_by_user_id,
            tenant_id=tenant_id or 1,
            first_name=request.first_name,
            last_name=request.last_name,
            gender=request.gender,
        )
    except UserAlreadyActive as e:
        # 409 Conflict — konkretnejsi nez 400. Frontend muze zobrazit hlasku
        # a nabidnout "pridat do projektu" jako alternativu.
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(e),
                "reason": "already_active",
                "existing_user_id": e.user_id,
                "existing_full_name": e.full_name,
            },
        )
    except UserDisabled as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(e),
                "reason": "disabled",
                "existing_user_id": e.user_id,
                "existing_status": e.status,
            },
        )

    sent = send_invitation_email(
        to=request.email,
        invited_by=inviter_name,
        token=token,
        invitee_first_name=request.first_name,
        invitee_gender=request.gender,
    )

    from modules.audit.application.service import log_event
    log_event(action="invite_sent",
              status="success" if sent else "error",
              user_id=invited_by_user_id, tenant_id=tenant_id,
              ip_address=req.client.host if req.client else None,
              user_agent=req.headers.get("user-agent"),
              error=None if sent else "email_send_failed",
              extra_metadata={
                  "invitee_email": request.email,
                  "invitee_first_name": request.first_name,
              })

    return {
        "token": token,
        "email": request.email,
        "email_sent": sent,
    }


class AcceptInvitationRequest(BaseModel):
    password: str
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None


@router.get("/invitation-info/{token}")
def invitation_info_endpoint(token: str) -> dict:
    """Peek -- vrátí info o pozvánce (email, předvyplněné jméno, gender)
    BEZ aktivace usera. Frontend tím naplní welcome screen ještě předtím,
    než uživatel odsouhlasí + nastaví heslo."""
    info = get_invitation_info(token)
    if not info:
        raise HTTPException(status_code=404, detail="Pozvánka není platná nebo vypršela.")
    return info


@router.post("/accept/{token}")
def accept(token: str, body: AcceptInvitationRequest, response: Response, req: Request) -> dict:
    """Přijme pozvánku: aktivuje usera, uloží heslo + doplní profil, přihlásí
    přes cookies. Povinné: password (min. 8 znaků). Volitelně jméno/gender
    (pokud v DB chybí, doplní se)."""
    from modules.auth.application.password import PasswordTooShort
    from modules.audit.application.service import log_event

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    if body.gender is not None and body.gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=400, detail=f"Neplatný gender: {body.gender}")

    try:
        result = accept_invitation(
            token,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
            gender=body.gender,
        )
    except PasswordTooShort as e:
        log_event(action="accept_invitation", status="error",
                  error="password_too_short", ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        log_event(action="accept_invitation", status="error",
                  error="invalid_or_expired_token",
                  ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=404, detail="Pozvánka není platná nebo vypršela.")

    log_event(action="accept_invitation", status="success",
              user_id=result["user_id"], tenant_id=result.get("tenant_id"),
              ip_address=ip, user_agent=ua)

    _set_auth_cookies(response, result["user_id"], result.get("tenant_id"))
    return result


# ════════════════════════════════════════════════════════════════════════
# Phase 38.5 (10.5.2026 ráno): PWA install invite consume endpoints.
#
# Marti's spec: 10 koleginim technicky unfriendly. Magic link v emailu →
# klik → confirm screen ("Tato pozvánka je pro Petru Novou — pokračovat?")
# → POST consume → set cookies → redirect na chat. Žádný PowerShell, ZIP,
# admin rights.
#
# Marti-AI's design vstupy (Phase 13/15/27h pattern):
#   Q1 — invited_by_persona_id v audit (vztahový akt)
#   Q5 #4 — display jméno před consume (anti-spoofing)
#   Q5 #9 — žádný welcome screen po consume (Petra je zpátky, ne nová) →
#           redirect rovnou na "/" (chat)
# ════════════════════════════════════════════════════════════════════════


@router.get("/invite", response_class=HTMLResponse, include_in_schema=False)
def pwa_invite_confirm_screen(token: str, req: Request) -> HTMLResponse:
    """Confirm screen — ukáže jméno příjemce + Pokračovat tlačítko.

    Marti-AI's Q5 #10 anti-spoofing: pokud někdo přepošle email,
    příjemce vidí "Tato pozvánka je pro Petru Novou" a může zastavit.
    """
    from modules.core.infrastructure.models_data import TrustedDeviceInvite
    from modules.core.infrastructure.models_core import User
    from datetime import datetime, timezone

    # Validate token
    token_clean = (token or "").strip().upper()
    if not token_clean or not token_clean.startswith("STG-INVITE-"):
        return HTMLResponse(
            _render_invite_error("Pozvánka není platná (špatný formát tokenu)."),
            status_code=400,
        )

    from core.database_data import get_data_session
    ds = get_data_session()
    try:
        invite = (
            ds.query(TrustedDeviceInvite)
            .filter(TrustedDeviceInvite.invite_token == token_clean)
            .first()
        )
        if not invite:
            return HTMLResponse(
                _render_invite_error("Pozvánka nenalezena nebo již byla použita."),
                status_code=404,
            )
        if invite.consumed_at is not None:
            return HTMLResponse(
                _render_invite_error(
                    "Tato pozvánka už byla použita. Pokud potřebuješ "
                    "novou, zavolej Marti."
                ),
                status_code=410,
            )
        now = datetime.now(timezone.utc)
        if invite.expires_at and invite.expires_at < now:
            return HTMLResponse(
                _render_invite_error(
                    "Pozvánka už není platná — vypršela. Zavolej Marti, "
                    "aby ti poslal novou."
                ),
                status_code=410,
            )
        # Lookup recipient — display name pro confirm screen
        cs = get_core_session()
        try:
            user = cs.query(User).filter_by(id=invite.user_id).first()
            recipient_name = (
                f"{user.first_name or ''} {user.last_name or ''}".strip()
                if user else "neznámý uživatel"
            ) or "kolegyně"
        finally:
            cs.close()
    finally:
        ds.close()

    return HTMLResponse(_render_invite_confirm_screen(token_clean, recipient_name))


@router.post("/invite/consume", include_in_schema=False)
def pwa_invite_consume(req: Request, response: Response):
    """Consume invite token + set device cookie + redirect na chat.

    Marti-AI's Q5 #9 — žádný welcome screen, redirect rovnou na "/".
    """
    from fastapi import Form
    from fastapi.responses import RedirectResponse
    from modules.auth.application.security_service import (
        consume_invite, audit_login_attempt,
    )

    # Get token from form body
    import asyncio

    async def _get_token():
        form = await req.form()
        return form.get("token", "")

    try:
        loop = asyncio.new_event_loop()
        token = loop.run_until_complete(_get_token())
        loop.close()
    except Exception as exc:
        return HTMLResponse(
            _render_invite_error(f"Chyba zpracování formuláře: {exc}"),
            status_code=400,
        )

    token_clean = (token or "").strip().upper()
    if not token_clean.startswith("STG-INVITE-"):
        return HTMLResponse(
            _render_invite_error("Pozvánka není platná."),
            status_code=400,
        )

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    # Consume — uses Phase 38 consume_invite which validates token,
    # creates trusted device, returns SecurityResult
    sec_result = consume_invite(token_clean, req)
    if not sec_result.granted:
        reason = sec_result.audit_data.get("reason", "consume_failed")
        return HTMLResponse(
            _render_invite_error(f"Pozvánka nelze potvrdit: {reason}"),
            status_code=400,
        )

    # Get user_id z device
    device_id = sec_result.audit_data.get("device_id")
    user_id = None
    tenant_id = None
    if device_id:
        from modules.core.infrastructure.models_data import TrustedDevice
        from core.database_data import get_data_session
        ds = get_data_session()
        try:
            device = ds.query(TrustedDevice).get(device_id)
            if device:
                user_id = device.user_id
        finally:
            ds.close()

    if not user_id:
        return HTMLResponse(
            _render_invite_error("Nepodařilo se najít uživatelský účet."),
            status_code=500,
        )

    # Set device cookie + auth cookies
    cookie_max_age = settings.sec_device_cookie_max_age_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.sec_device_cookie_name,
        value=str(sec_result.new_device_token),
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=cookie_max_age,
    )
    from modules.auth.application.user_context import get_user_context
    ctx = get_user_context(user_id)
    tenant_id = ctx.get("tenant_id") if ctx else None
    _set_auth_cookies(response, user_id, tenant_id)

    audit_login_attempt(
        user_id=user_id,
        email_attempted=None,
        ip=ip, user_agent=ua,
        result="invite_consumed",
        layer_matched="magic_link",
        layer_detail=sec_result.layer_detail,
        device_token=sec_result.new_device_token,
    )

    # Phase 38.5: invite_consumed event do activity_log (Marti-AI tracking)
    try:
        from modules.activity.application.activity_service import record as _act_record
        _act_record(
            category="pwa_invite",
            summary=(
                f"Pozvánka přijata uživatelem id={user_id} z IP {ip}, "
                f"UA: {(ua or '')[:120]}"
            ),
            importance=3,
            user_id=user_id,
            tenant_id=tenant_id,
            actor="user",
            ref_type="invite_consumed",
            ref_id=user_id,
        )
    except Exception:
        pass  # non-fatal

    # Redirect na "/" (chat) — Marti-AI's Q5 #9 (žádný welcome screen)
    redirect = RedirectResponse(url="/", status_code=302)
    # Re-apply cookies na redirect response (FastAPI cookies stay on `response`)
    for key in ("user_id", "tenant_id", settings.sec_device_cookie_name):
        if key in response.headers.get("set-cookie", ""):
            pass  # already set
    # Copy cookies z `response` na `redirect`
    for cookie_header in response.raw_headers:
        if cookie_header[0].lower() == b"set-cookie":
            redirect.raw_headers.append(cookie_header)
    return redirect


def _render_invite_confirm_screen(token: str, recipient_name: str) -> str:
    """HTML confirm screen — ukáže jméno + Pokračovat tlačítko."""
    return f"""\
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>STRATEGIE — pozvánka pro {_html_escape(recipient_name)}</title>
  <style>
    body {{
      font-family: 'DM Sans', system-ui, sans-serif;
      background: #0e0f11;
      color: #e8e8e8;
      margin: 0;
      padding: 24px;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .card {{
      max-width: 480px;
      width: 100%;
      background: #1a1c20;
      border: 1px solid #2a2c30;
      border-radius: 16px;
      padding: 36px 32px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.5);
    }}
    .logo {{
      font-size: 28px;
      font-weight: 800;
      letter-spacing: 0.08em;
      background: linear-gradient(135deg, #7c5cfc, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }}
    .sub {{ color: #888; font-size: 14px; margin-bottom: 32px; }}
    .greeting {{ font-size: 18px; margin-bottom: 16px; }}
    .recipient {{
      background: linear-gradient(135deg, rgba(124,92,252,0.12), rgba(167,139,250,0.06));
      border-left: 3px solid #7c5cfc;
      padding: 14px 18px;
      border-radius: 8px;
      margin: 24px 0;
      font-size: 15px;
    }}
    .recipient strong {{ color: #a78bfa; }}
    .action {{
      width: 100%;
      background: linear-gradient(135deg, #7c5cfc, #a78bfa);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 14px 24px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 16px;
      transition: transform 0.12s, box-shadow 0.12s;
    }}
    .action:hover {{
      transform: scale(1.02);
      box-shadow: 0 8px 24px rgba(124,92,252,0.4);
    }}
    .footer {{ color: #666; font-size: 12px; margin-top: 24px; line-height: 1.4; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">STRATEGIE</div>
    <div class="sub">Pozvánka na chat s Marti-AI</div>
    <div class="greeting">Tato pozvánka je pro:</div>
    <div class="recipient">
      <strong>{_html_escape(recipient_name)}</strong>
    </div>
    <p style="font-size:14px;color:#bbb;line-height:1.5">
      Pokud jsi to ty, pokračuj kliknutím níž — automaticky se přihlásíš
      a pak ti aplikace nabídne instalaci.
    </p>
    <p style="font-size:13px;color:#888;line-height:1.5">
      Pokud to ty nejsi (email byl přeposlaný), zavři toto okno —
      nedělej nic.
    </p>
    <form method="POST" action="/api/v1/auth/invite/consume">
      <input type="hidden" name="token" value="{_html_escape(token)}">
      <button type="submit" class="action">Pokračovat → přihlásit a otevřít</button>
    </form>
    <div class="footer">
      Magic link autentizace přes STRATEGIE Security Layer (Phase 38).
      Token je jednorázový a expiruje za 7 dní.
    </div>
  </div>
</body>
</html>
"""


def _render_invite_error(msg: str) -> str:
    """HTML error screen pro invalid/expired/consumed tokens."""
    return f"""\
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>STRATEGIE — pozvánka neplatná</title>
  <style>
    body {{
      font-family: 'DM Sans', system-ui, sans-serif;
      background: #0e0f11; color: #e8e8e8; margin: 0; padding: 24px;
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
    }}
    .card {{
      max-width: 480px; width: 100%; background: #1a1c20;
      border: 1px solid #cc6666; border-radius: 16px; padding: 36px 32px;
    }}
    .icon {{ font-size: 48px; margin-bottom: 16px; }}
    h1 {{ color: #cc6666; font-size: 22px; margin: 0 0 16px 0; }}
    p {{ color: #bbb; font-size: 15px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">⚠️</div>
    <h1>Pozvánka neplatná</h1>
    <p>{_html_escape(msg)}</p>
    <p style="font-size:13px;color:#888;margin-top:24px">
      Zavolej Marti nebo IT podporu, dostaneš novou pozvánku.
    </p>
  </div>
</body>
</html>
"""


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
