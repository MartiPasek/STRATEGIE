from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.database_core import get_core_session
from core.logging import get_logger
from modules.auth.api.schemas import LoginRequest, LoginResponse, SwitchTenantRequest
from modules.auth.application.service import login_by_email, AmbiguousEmailError
from modules.auth.application.invitation_service import (
    create_invitation, accept_invitation,
    UserAlreadyActive, UserDisabled,
)
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
