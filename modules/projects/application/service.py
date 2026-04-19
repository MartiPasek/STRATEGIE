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
