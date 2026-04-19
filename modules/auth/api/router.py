from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.database_core import get_core_session
from core.logging import get_logger
from modules.auth.api.schemas import LoginRequest, LoginResponse
from modules.auth.application.service import login_by_email, AmbiguousEmailError
from modules.auth.application.invitation_service import create_invitation, accept_invitation
from modules.notifications.application.email_service import send_invitation_email
from modules.core.infrastructure.models_core import User, UserContact

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

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")
        primary = (
            session.query(UserContact)
            .filter_by(user_id=user_id, contact_type="email", is_primary=True, status="active")
            .first()
        )
        return LoginResponse(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=primary.contact_value if primary else "",
            tenant_id=user.last_active_tenant_id,
        )
    finally:
        session.close()


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
