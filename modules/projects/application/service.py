"""
Project application service -- business logika nad repository.

Kluciv design:
  - Projekt patri TENANTU. Scope listu / switchu je vzdy current tenant usera.
  - Switch: user.last_active_project_id = X  (None = "bez projektu").
  - Guard: switchnout lze jen na projekt, kde je user clen / owner tenantu.
  - Create: jen tenant owner + tenant admin. MVP: jen tenant owner (minimal).
  - Archive: jen project owner / tenant owner.
"""
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, Tenant
from modules.projects.infrastructure import repository as repo

logger = get_logger("projects.service")


class ProjectError(Exception):
    """Obecna chyba projektove operace."""


class NotTenantMember(ProjectError):
    """User neni clenem tenantu, ve kterem chce projekt delat."""


class NotProjectMember(ProjectError):
    """User nema pristup k projektu (switch nebo archivace)."""


class NotAuthorizedToCreate(ProjectError):
    """User nema opravneni vytvaret projekty v tenantu (MVP: jen tenant owner)."""


def _get_current_tenant(user_id: int) -> int | None:
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return u.last_active_tenant_id if u else None
    finally:
        cs.close()


def list_projects_for_user(user_id: int) -> list[dict]:
    """
    Vrati aktivni projekty aktualniho tenantu usera, razene podle aktivity.
    Pokud user nema last_active_tenant_id, vrati [].
    """
    tenant_id = _get_current_tenant(user_id)
    if tenant_id is None:
        return []
    return repo.list_active_projects_for_user(user_id=user_id, tenant_id=tenant_id)


def create_project(*, user_id: int, name: str) -> int:
    """
    Vytvori novy projekt v aktualnim tenantu usera. User musi byt tenant owner.
    MVP zkratka -- pozdeji lze rozsirit o admin role.
    """
    name = (name or "").strip()
    if not name:
        raise ProjectError("Jmeno projektu nesmi byt prazdne.")

    tenant_id = _get_current_tenant(user_id)
    if tenant_id is None:
        raise NotTenantMember("Nemas aktivni tenant -- neni kam projekt zalozit.")

    cs = get_core_session()
    try:
        tenant = cs.query(Tenant).filter_by(id=tenant_id).first()
        if tenant is None:
            raise NotTenantMember("Tenant neexistuje.")
        if tenant.owner_user_id != user_id:
            raise NotAuthorizedToCreate(
                "Jen vlastnik tenantu muze zakladat projekty (MVP)."
            )
    finally:
        cs.close()

    return repo.create_project(
        tenant_id=tenant_id,
        name=name,
        owner_user_id=user_id,
    )


def switch_project_for_user(user_id: int, project_id: int | None) -> dict:
    """
    Nastavi user.last_active_project_id. None = "bez projektu".
    Pokud project_id zadan, overime ze user ma pristup.

    Vraci dict {"project_id": int | None, "project_name": str | None}.
    """
    if project_id is None:
        repo.set_user_last_active_project(user_id, None)
        return {"project_id": None, "project_name": None}

    if not repo.is_user_member_or_owner(user_id, project_id):
        raise NotProjectMember("Nemas pristup k tomuto projektu.")

    project = repo.get_project(project_id)
    if project is None or not project.is_active:
        raise ProjectError("Projekt neexistuje nebo je archivovany.")

    # Konzistence: projekt musi byt v aktualnim tenantu usera
    current_tenant = _get_current_tenant(user_id)
    if current_tenant is not None and project.tenant_id != current_tenant:
        raise ProjectError(
            "Projekt je v jinem tenantu nez ve kterem jsi aktualne aktivni."
        )

    repo.set_user_last_active_project(user_id, project_id)
    return {"project_id": project_id, "project_name": project.name}


def rename_project(*, user_id: int, project_id: int, new_name: str) -> bool:
    """
    Prejmenuje projekt. Opravneni: project owner nebo tenant owner.
    """
    new_name = (new_name or "").strip()
    if not new_name:
        raise ProjectError("Jmeno projektu nesmi byt prazdne.")

    project = repo.get_project(project_id)
    if project is None:
        raise ProjectError("Projekt neexistuje.")

    cs = get_core_session()
    try:
        tenant = cs.query(Tenant).filter_by(id=project.tenant_id).first()
    finally:
        cs.close()

    is_project_owner = project.owner_user_id == user_id
    is_tenant_owner = tenant is not None and tenant.owner_user_id == user_id
    if not (is_project_owner or is_tenant_owner):
        raise ProjectError("Nemas opravneni prejmenovat tento projekt.")

    return repo.rename_project(project_id, new_name)


def switch_project_by_query(user_id: int, query: str) -> dict:
    """
    Najde projekt v aktualnim tenantu usera podle jmena (substring,
    case + accent insensitive) a prepne user.last_active_project_id.

    Vraci dict:
      {
        "found": bool,
        "already_active": bool,           # pokud byl uz aktivni
        "project_id": int | None,
        "project_name": str | None,
        "ambiguous": bool,
        "candidates": [{"id": int, "name": str}, ...],   # pri ambiguous
        "no_projects": bool,              # tenant nema zadne aktivni projekty
      }

    Zaclujeme se jen na aktivni projekty v current tenantu.
    """
    import unicodedata

    def _normalize(s: str) -> str:
        if s is None:
            return ""
        n = unicodedata.normalize("NFKD", s.strip().lower())
        return "".join(c for c in n if unicodedata.category(c) != "Mn")

    needle = _normalize(query)
    if not needle:
        return {"found": False, "ambiguous": False, "candidates": [],
                "no_projects": False, "already_active": False,
                "project_id": None, "project_name": None}

    projects = list_projects_for_user(user_id)
    if not projects:
        return {"found": False, "ambiguous": False, "candidates": [],
                "no_projects": True, "already_active": False,
                "project_id": None, "project_name": None}

    # Hledame substring match v normalizovanem jmene
    matches = [p for p in projects if needle in _normalize(p["name"])]

    if not matches:
        return {"found": False, "ambiguous": False, "candidates": [],
                "no_projects": False, "already_active": False,
                "project_id": None, "project_name": None}

    if len(matches) > 1:
        # Pokud je presny match jednoznacny, pouzijeme ho
        exact = [p for p in matches if _normalize(p["name"]) == needle]
        if len(exact) == 1:
            matches = exact
        else:
            return {
                "found": False, "ambiguous": True,
                "candidates": [{"id": p["id"], "name": p["name"]} for p in matches[:5]],
                "no_projects": False, "already_active": False,
                "project_id": None, "project_name": None,
            }

    target = matches[0]
    # Uz aktivni?
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        already = (u is not None and u.last_active_project_id == target["id"])
    finally:
        cs.close()
    if already:
        return {
            "found": True, "already_active": True,
            "project_id": target["id"], "project_name": target["name"],
            "ambiguous": False, "candidates": [], "no_projects": False,
        }

    repo.set_user_last_active_project(user_id, target["id"])
    return {
        "found": True, "already_active": False,
        "project_id": target["id"], "project_name": target["name"],
        "ambiguous": False, "candidates": [], "no_projects": False,
    }


def clear_project_for_user(user_id: int) -> dict:
    """Odhlaseni projektu — nastav last_active_project_id na NULL."""
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        already_none = (u is not None and u.last_active_project_id is None)
    finally:
        cs.close()
    if already_none:
        return {"already_clear": True}
    repo.set_user_last_active_project(user_id, None)
    return {"already_clear": False}


def _can_manage_project_members(user_id: int, project_id: int) -> tuple[bool, str | None]:
    """
    Vrati (can_manage, reason_if_not). Prava pro add/remove clenov:
      - project owner (UserProject.role == 'owner' pro tento user_id)
      - tenant owner (Tenant.owner_user_id == user_id)
    """
    project = repo.get_project(project_id)
    if project is None:
        return False, "Projekt neexistuje."

    cs = get_core_session()
    try:
        from modules.core.infrastructure.models_core import UserProject
        # Tenant owner check
        tenant = cs.query(Tenant).filter_by(id=project.tenant_id).first()
        if tenant is not None and tenant.owner_user_id == user_id:
            return True, None
        # Project owner check
        up = (
            cs.query(UserProject)
            .filter_by(user_id=user_id, project_id=project_id, role="owner")
            .first()
        )
        if up is not None:
            return True, None
        return False, "Nemas opravneni spravovat cleny tohoto projektu."
    finally:
        cs.close()


def list_project_members(*, user_id: int, project_id: int) -> list[dict]:
    """Seznam clenov projektu. Vidi je kazdy clen projektu / tenant owner."""
    if not repo.is_user_member_or_owner(user_id=user_id, project_id=project_id):
        raise NotProjectMember("Nemas pristup k tomuto projektu.")
    return repo.list_project_members(project_id)


def add_project_member(*, user_id: int, project_id: int, target_user_id: int, role: str = "member") -> dict:
    """
    Prida targeted user jako clena projektu.
    Opravneni: project owner / tenant owner.
    Guard: target musi byt aktivni clen STEJNEHO tenantu jako projekt.
    """
    can, reason = _can_manage_project_members(user_id, project_id)
    if not can:
        raise ProjectError(reason or "Nemas opravneni.")

    project = repo.get_project(project_id)
    if project is None:
        raise ProjectError("Projekt neexistuje.")

    # Target user musi byt aktivni clen tenantu projektu
    from modules.core.infrastructure.models_core import UserTenant, User as _User
    cs = get_core_session()
    try:
        target = cs.query(_User).filter_by(id=target_user_id, status="active").first()
        if target is None:
            raise ProjectError("Cilovy uzivatel neexistuje nebo neni aktivni.")
        membership = (
            cs.query(UserTenant)
            .filter_by(
                user_id=target_user_id,
                tenant_id=project.tenant_id,
                membership_status="active",
            )
            .first()
        )
        if membership is None:
            raise ProjectError(
                "Cilovy uzivatel neni aktivnim clenem tenantu tohoto projektu. "
                "Nejdriv ho pozvi do tenantu."
            )
    finally:
        cs.close()

    added = repo.add_project_member(project_id=project_id, user_id=target_user_id, role=role)
    return {"added": added, "user_id": target_user_id}


def remove_project_member(*, user_id: int, project_id: int, target_user_id: int) -> dict:
    """
    Odebere usera z projektu.
    Opravneni: project owner / tenant owner. User muze odebrat i sam sebe
    (opustit projekt) — tj. target_user_id == user_id je povoleno vzdy.
    """
    is_self_leave = (target_user_id == user_id)
    if not is_self_leave:
        can, reason = _can_manage_project_members(user_id, project_id)
        if not can:
            raise ProjectError(reason or "Nemas opravneni.")
    else:
        # Self-leave: staci byt clenem projektu
        if not repo.is_user_member_or_owner(user_id=user_id, project_id=project_id):
            raise NotProjectMember("Nemas pristup k tomuto projektu.")

    # Pojistka: owner projektu se nesmi odebrat (nechceme projekty bez ownera)
    project = repo.get_project(project_id)
    if project and project.owner_user_id == target_user_id:
        raise ProjectError(
            "Owner projektu nemuze byt odebran. Nejdriv prevyd vlastnictvi nebo projekt archivuj."
        )

    removed = repo.remove_project_member(project_id=project_id, user_id=target_user_id)
    return {"removed": removed, "user_id": target_user_id}


def set_project_default_persona(
    *, user_id: int, project_id: int, persona_id: int | None,
) -> dict:
    """
    Nastavi default personu pro projekt. Opravneni: project owner / tenant
    owner. persona_id=None znamena zruseni overridu (projekt bude pouzivat
    globalni default -- Marti-AI).

    Validace:
      - Persona musi existovat.
      - Persona musi byt v scope usera (globalni nebo stejny tenant jako projekt).
    """
    project = repo.get_project(project_id)
    if project is None:
        raise ProjectError("Projekt neexistuje.")

    # Oprávnění: project owner / tenant owner
    from modules.core.infrastructure.models_core import Tenant, Persona
    cs = get_core_session()
    try:
        tenant = cs.query(Tenant).filter_by(id=project.tenant_id).first()
    finally:
        cs.close()
    is_project_owner = project.owner_user_id == user_id
    is_tenant_owner = tenant is not None and tenant.owner_user_id == user_id
    if not (is_project_owner or is_tenant_owner):
        raise ProjectError("Nemas opravneni menit default personu projektu.")

    # Validace persony
    persona_name = None
    if persona_id is not None:
        cs = get_core_session()
        try:
            persona = cs.query(Persona).filter_by(id=persona_id).first()
            if persona is None:
                raise ProjectError("Persona neexistuje.")
            # Global persona OK, nebo persona ze stejneho tenantu jako projekt
            if persona.tenant_id is not None and persona.tenant_id != project.tenant_id:
                raise ProjectError(
                    "Persona je z jineho tenantu nez projekt. Pouzij globalni "
                    "personu nebo personu z tohoto tenantu."
                )
            persona_name = persona.name
        finally:
            cs.close()

    repo.set_project_default_persona(project_id, persona_id)
    return {
        "project_id": project_id,
        "default_persona_id": persona_id,
        "default_persona_name": persona_name,
    }


def archive_project(*, user_id: int, project_id: int) -> bool:
    """
    Archivuj projekt. Opravneni: project owner nebo tenant owner.
    """
    project = repo.get_project(project_id)
    if project is None:
        raise ProjectError("Projekt neexistuje.")

    cs = get_core_session()
    try:
        tenant = cs.query(Tenant).filter_by(id=project.tenant_id).first()
    finally:
        cs.close()

    is_project_owner = project.owner_user_id == user_id
    is_tenant_owner = tenant is not None and tenant.owner_user_id == user_id
    if not (is_project_owner or is_tenant_owner):
        raise ProjectError("Nemas opravneni archivovat tento projekt.")

    # Pokud byl projekt aktivnim projektem user-a, uvolnit (clear).
    # Bezpecnost: pokud ma user archivovany projekt jako last_active, dostane
    # se mu do UI do "bez projektu" (NULL) -- nezablokuje ho to.
    cs = get_core_session()
    try:
        users_on_project = (
            cs.query(User).filter(User.last_active_project_id == project_id).all()
        )
        for u in users_on_project:
            u.last_active_project_id = None
        cs.commit()
    finally:
        cs.close()

    return repo.archive_project(project_id)
