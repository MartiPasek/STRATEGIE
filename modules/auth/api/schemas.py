from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    user_id: int
    first_name: str | None
    last_name: str | None
    email: str
    tenant_id: int | None
