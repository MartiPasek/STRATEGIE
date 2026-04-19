from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    user_id: int
    first_name: str | None
    last_name: str | None
    email: str
    tenant_id: int | None

    # Identity refactor v2 — rozšíření o tenantový kontext.
    # Frontend tyto fieldy zobrazuje v UI hlavičce a používá je jako
    # zdroj pravdy o aktuálním kontextu uživatele.
    display_name: str | None = None     # z user_tenant_profiles aktuálního tenantu
    tenant_name: str | None = None      # z tenants
    tenant_code: str | None = None      # z tenants — krátký kód (EUR, MARTI)
    aliases: list[str] = []             # z user_aliases (active, primary first)
