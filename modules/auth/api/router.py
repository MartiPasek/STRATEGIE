from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.config import settings
from core.database_core import get_core_session
from core.logging import get_logger


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
from modules.auth.api.schemas import LoginRequest, LoginResponse, SwitchTenantRequest
from modules.auth.application.service import login_by_email, AmbiguousEmailError, PasswordNotSet
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
    _set_auth_cookies(response, result["user_id"], result.get("tenant_id"))

    log_event(action="login_success", user_id=result["user_id"],
              tenant_id=result.get("tenant_id"), ip_address=ip, user_agent=ua)

    return LoginResponse(**result)


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

    result = create_reset_token(email)
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

    return {"status": "password_reset", "email": result["email"]}


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
