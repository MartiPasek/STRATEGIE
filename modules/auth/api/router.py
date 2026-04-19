from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.database_core import get_core_session
from core.logging import get_logger
from modules.auth.api.schemas import LoginRequest, LoginResponse, SwitchTenantRequest
from modules.auth.application.service import login_by_email, AmbiguousEmailError
from modules.auth.application.invitation_service import create_invitation, accept_invitation
from modules.auth.application.user_context import get_user_context
from modules.notifications.application.email_service import send_invitation_email
from modules.core.infrastructure.models_core import User, UserContact, UserTenant

logger = get_logger("auth.api")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── LOGIN ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response) -> LoginResponse:
    """Jednoduchý login přes email. MVP: bez hesla."""
    try:
        result = login_by_email(request.email)
    except AmbiguousEmailError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if not result:
        raise HTTPException(status_code=401, detail="Email nenalezen nebo účet není aktivní.")

    response.set_cookie(key="user_id", value=str(result["user_id"]), httponly=True, max_age=60*60*24*30)
    response.set_cookie(key="tenant_id", value=str(result["tenant_id"] or ""), httponly=True, max_age=60*60*24*30)

    return LoginResponse(**result)


@router.post("/logout")
def logout(response: Response) -> dict:
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


# ── INVITATIONS ────────────────────────────────────────────────────────────

class InviteRequest(BaseModel):
    email: str


@router.post("/invite")
def invite(request: InviteRequest, req: Request) -> dict:
    """Pozve nového uživatele emailem."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")

    invited_by_user_id = int(user_id_str)

    session = get_core_session()
    try:
        inviter = session.query(User).filter_by(id=invited_by_user_id).first()
        inviter_name = " ".join(filter(None, [inviter.first_name, inviter.last_name])) if inviter else "Člen týmu"
        tenant_id = inviter.last_active_tenant_id if inviter else 1
    finally:
        session.close()

    token = create_invitation(
        email=request.email,
        invited_by_user_id=invited_by_user_id,
        tenant_id=tenant_id or 1,
    )

    sent = send_invitation_email(
        to=request.email,
        invited_by=inviter_name,
        token=token,
    )

    return {
        "token": token,
        "email": request.email,
        "email_sent": sent,
    }


@router.get("/accept/{token}")
def accept(token: str, response: Response) -> dict:
    """Přijme pozvánku a přihlásí uživatele."""
    result = accept_invitation(token)
    if not result:
        raise HTTPException(status_code=404, detail="Pozvánka není platná nebo vypršela.")

    response.set_cookie(key="user_id", value=str(result["user_id"]), httponly=True, max_age=60*60*24*30)
    response.set_cookie(key="tenant_id", value=str(result["tenant_id"] or ""), httponly=True, max_age=60*60*24*30)

    return result
