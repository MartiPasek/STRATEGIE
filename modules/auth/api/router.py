from fastapi import APIRouter, HTTPException, Response

from core.logging import get_logger
from modules.auth.api.schemas import LoginRequest, LoginResponse
from modules.auth.application.service import login_by_email

logger = get_logger("auth.api")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response) -> LoginResponse:
    """
    Jednoduchý login přes email.
    MVP: bez hesla — jen ověření existence.
    Nastaví cookie s user_id pro další requesty.
    """
    result = login_by_email(request.email)

    if not result:
        raise HTTPException(status_code=401, detail="Email nenalezen nebo účet není aktivní.")

    # Uložíme user_id do cookie
    response.set_cookie(
        key="user_id",
        value=str(result["user_id"]),
        httponly=True,
        max_age=60 * 60 * 24 * 30,  # 30 dní
    )
    response.set_cookie(
        key="tenant_id",
        value=str(result["tenant_id"] or ""),
        httponly=True,
        max_age=60 * 60 * 24 * 30,
    )

    return LoginResponse(**result)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("user_id")
    response.delete_cookie("tenant_id")
    return {"status": "logged out"}
