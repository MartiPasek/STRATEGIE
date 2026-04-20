from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TenantInfo(BaseModel):
    """Minimální info o tenantu pro UI dropdown / list."""
    tenant_id: int
    tenant_name: str
    tenant_code: str | None = None
    tenant_type: str | None = None      # company / personal / family / project


class SwitchTenantRequest(BaseModel):
    tenant_id: int
    # Volitelně ID konverzace, do které se má vložit system zpráva o přepnutí.
    # AI tak v message historii uvidí explicitní změnu kontextu a nezmate se
    # z dřívějších zpráv v původním tenantu.
    conversation_id: int | None = None


class LoginResponse(BaseModel):
    user_id: int
    first_name: str | None
    last_name: str | None
    email: str
    tenant_id: int | None
    # Gender — pro UI editor v profilu (volitelné).
    gender: str | None = None
    short_name: str | None = None

    # Identity refactor v2 — rozšíření o tenantový kontext.
    # Frontend tyto fieldy zobrazuje v UI hlavičce a používá je jako
    # zdroj pravdy o aktuálním kontextu uživatele.
    display_name: str | None = None     # z user_tenant_profiles aktuálního tenantu
    tenant_name: str | None = None      # z tenants
    tenant_code: str | None = None      # z tenants — krátký kód (EUR, MARTI)
    aliases: list[str] = []             # z user_aliases (active, primary first)
    # Default persona (typicky "Marti-AI") — UI ji ukazuje v hlavičce
    # "Mluvíš s: …" hned po loginu / nové konverzaci, aby user věděl s kým
    # mluví ještě před první zprávou.
    default_persona_name: str | None = None
    # Superadmin flag — pro UI skrýva/odhaluje admin akce (např. "+ Nová persona").
    # Definováno centrálně v modules/personas/application/service._is_superadmin.
    is_superadmin: bool = False
    # Aktuální projekt usera (uvnitř current tenantu). None = "bez projektu".
    # UI zobrazuje v hlavičce i v agent baru ("Projekt: …").
    project_id: int | None = None
    project_name: str | None = None
    # Všechny aktivní tenanty, jichž je user členem — pro UI tenant dropdown.
    available_tenants: list[TenantInfo] = []
    # Pokud /switch_tenant vložil do konverzace systémový marker, vrátí se tu
    # jeho přesné znění — frontend ho rovnou vykreslí jako persistentní
    # systémovou zprávu (label STRATEGIE), aby uživatel viděl totéž co AI.
    # /me a /login mají vždy None.
    tenant_switch_marker: str | None = None
