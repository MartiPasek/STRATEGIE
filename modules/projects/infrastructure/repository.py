"""
Project repository — pristup k css_db.projects + cross-DB merge s data_db
pro radeni projektu podle aktivity (MAX(conversation.last_message_at)).

CSS_DB ma projects a user_projects (hard relational pravda).
DATA_DB ma conversations s project_id nullable -- pres ty pocitame aktivitu.
Mergujeme v Pythonu, protoze PostgreSQL neumi cross-database join.
"""
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    Project, UserProject, Tenant, UserTenant, User,
)
from modules.core.infrastructure.models_data import Conversation

logger = get_logger("projects.repo")


def list_active_projects_for_user(user_id: int, tenant_id: int) -> list[dict]:
    """
    Vrati aktivni projekty v danem tenantu, ve kterych je user clenem
    (nebo ownerem tenantu -- viz nize). Razeno dle aktivity DESC, pak
    dle created_at DESC.

    Scope:
      - Tenant owner vidi vsechny aktivni projekty tenantu (muze s nimi
        pracovat i kdyz neni explicitne clen). Demokraticka ale prakticka
        volba pro MVP -- bez ni by tenant owner musel byt rucne pridavan
        do kazdeho projektu.
      - Ne-owner uzivatel vidi jen projekty, kde je v user_projects.

    Vraci list[dict] s klici:
      id, name, owner_user_id, created_at (datetime),
      last_activity_at (datetime | None), my_role (str | None)
    """
    cs = get_core_session()
    try:
        # Kdo je user, je vlastnik tenantu?
        tenant_owner = (
            cs.query(Tenant)
            .filter(Tenant.id == tenant_id, Tenant.owner_user_id == user_id)
            .first()
            is not None
        )

        base = (
            cs.query(Project)
            .filter(Project.tenant_id == tenant_id, Project.is_active.is_(True))
        )
        if tenant_owner:
            projects = base.all()
            # Owner ma implicitni pristup -- role sestavime v druhem pruchodu
        else:
            # Jen tam, kde je user v user_projects
            projects = (
                base.join(UserProject, UserProject.project_id == Project.id)
                .filter(UserProject.user_id == user_id)
                .all()
            )

        # User -> project role mapa (pro vraceni my_role)
        my_roles: dict[int, str] = {}
        if projects:
            rows = (
                cs.query(UserProject)
                .filter(
                    UserProject.user_id == user_id,
                    UserProject.project_id.in_([p.id for p in projects]),
                )
                .all()
            )
            my_roles = {r.project_id: r.role for r in rows}

        result = [
            {
                "id": p.id,
                "name": p.name,
                "owner_user_id": p.owner_user_id,
                "created_at": p.created_at,
                "my_role": my_roles.get(p.id) or ("owner_tenant" if tenant_owner and p.id not in my_roles else None),
                "default_persona_id": p.default_persona_id,
                # Phase 30 (2.5.2026): hierarchicke projekty
                "parent_project_id": p.parent_project_id,
            }
            for p in projects
        ]
    finally:
        cs.close()

    # Cross-DB: doplnime last_activity_at z data_db
    if not result:
        return []

    ds = get_data_session()
    try:
        activity_rows = (
            ds.query(
                Conversation.project_id,
                func.max(Conversation.last_message_at).label("last_activity"),
            )
            .filter(
                Conversation.project_id.in_([p["id"] for p in result]),
                Conversation.is_deleted.is_(False),
            )
            .group_by(Conversation.project_id)
            .all()
        )
        activity_map = {r.project_id: r.last_activity for r in activity_rows}
    finally:
        ds.close()

    for p in result:
        p["last_activity_at"] = activity_map.get(p["id"])

    # Sort: aktivni (last_activity_at) DESC, NULL dolu, pak created_at DESC
    result.sort(
        key=lambda p: (
            p["last_activity_at"] is None,        # False (ma aktivitu) pred True (nema)
            -(p["last_activity_at"].timestamp()) if p["last_activity_at"] else 0,
            -p["created_at"].timestamp(),
        )
    )
    return result


def get_project(project_id: int) -> Project | None:
    """Load project by id (nebo None). Vraci SQLAlchemy instanci v otevrenem sezení."""
    cs = get_core_session()
    try:
        return cs.query(Project).filter_by(id=project_id).first()
    finally:
        cs.close()


def create_project(
    *,
    tenant_id: int,
    name: str,
    owner_user_id: int,
    parent_project_id: int | None = None,
) -> int:
    """
    Vytvori projekt + user_projects row pro ownera. Vrati project.id.

    Phase 30 (2.5.2026): parent_project_id volitelny pro hierarchii. Validace
    parent (existuje, stejny tenant, depth < 6) provedena v service vrstve.
    """
    cs = get_core_session()
    try:
        project = Project(
            tenant_id=tenant_id,
            name=name.strip(),
            owner_user_id=owner_user_id,
            parent_project_id=parent_project_id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        cs.add(project)
        cs.flush()

        # Owner dostane explicitni user_projects row s roli owner --
        # aby pri archivaci tenantu / zmene vlastnictvi nezmizel z projektu.
        membership = UserProject(
            user_id=owner_user_id,
            project_id=project.id,
            role="owner",
            created_at=datetime.now(timezone.utc),
        )
        cs.add(membership)
        cs.commit()
        logger.info(
            f"PROJECT | created | id={project.id} | tenant={tenant_id} | "
            f"owner={owner_user_id} | name={name!r} | parent={parent_project_id}"
        )
        return project.id
    finally:
        cs.close()


# ── Phase 30 (2.5.2026): hierarchical projects helpers ─────────────────

# Marti's Q1 volba: max depth 6 urovni (root = depth 0). Validace pri create
# i pri move (reparenting). Recursive walk parent chain v Pythonu (cheap pro
# 6 urovni i pri tisicich projektech).
PROJECT_MAX_DEPTH = 6


def get_project_depth(project_id: int) -> int:
    """
    Vrati hloubku projektu v stromu. Root projekt = 0, child = 1, atd.
    Pri broken chain (parent neexistuje) vrati hloubku az do bodu rozbiti.

    Bezpecne proti cyklum -- limit 100 hops jako pojistka.
    """
    cs = get_core_session()
    try:
        depth = 0
        seen: set[int] = set()
        current_id = project_id
        for _ in range(100):
            if current_id in seen:
                logger.warning(f"PROJECT | cycle detected at project_id={current_id}")
                break
            seen.add(current_id)
            p = cs.query(Project).filter_by(id=current_id).first()
            if p is None or p.parent_project_id is None:
                break
            depth += 1
            current_id = p.parent_project_id
        return depth
    finally:
        cs.close()


def is_descendant_of(potential_descendant_id: int, ancestor_id: int) -> bool:
    """
    Zkontroluje jestli potential_descendant je potomek ancestor v project tree.
    Pouziva se pred move_project pro cycle prevention -- nesmime presunout
    projekt pod jeho vlastniho potomka.
    """
    cs = get_core_session()
    try:
        seen: set[int] = set()
        current_id = potential_descendant_id
        for _ in range(100):
            if current_id in seen:
                return False
            seen.add(current_id)
            if current_id == ancestor_id:
                return True
            p = cs.query(Project).filter_by(id=current_id).first()
            if p is None or p.parent_project_id is None:
                return False
            current_id = p.parent_project_id
        return False
    finally:
        cs.close()


def update_project_parent(project_id: int, new_parent_id: int | None) -> bool:
    """
    Zmeni parent_project_id. Validace cyklu + depth se dela v service vrstve
    pred volanim. Tady jen update + commit.
    """
    cs = get_core_session()
    try:
        project = cs.query(Project).filter_by(id=project_id).first()
        if project is None:
            return False
        project.parent_project_id = new_parent_id
        cs.commit()
        logger.info(
            f"PROJECT | move | id={project_id} | new_parent={new_parent_id}"
        )
        return True
    finally:
        cs.close()


def get_descendant_project_ids(project_id: int) -> list[int]:
    """
    Vrati ID vsech potomku projektu (nikoli sam projekt). Recursive walk
    pres parent_project_id, BFS. Pouziva se pri RAG scope='recursive'.

    Pro hloubku 6 a tisíce projektů je to mensi memory load nez recursive CTE
    pri každém RAG search -- cache friendly v Pythonu.
    """
    cs = get_core_session()
    try:
        descendants: list[int] = []
        queue = [project_id]
        seen: set[int] = set()
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            children = (
                cs.query(Project.id)
                .filter(Project.parent_project_id == current)
                .all()
            )
            for (cid,) in children:
                if cid not in descendants:
                    descendants.append(cid)
                    queue.append(cid)
        return descendants
    finally:
        cs.close()


def archive_project(project_id: int) -> bool:
    """Set is_active=False. Vrati True pokud nalezen a zmenen."""
    cs = get_core_session()
    try:
        project = cs.query(Project).filter_by(id=project_id).first()
        if project is None:
            return False
        if not project.is_active:
            return True  # already archived -- idempotentni
        project.is_active = False
        cs.commit()
        logger.info(f"PROJECT | archived | id={project_id}")
        return True
    finally:
        cs.close()


def rename_project(project_id: int, new_name: str) -> bool:
    """Zmeni Project.name. Vraci True pokud projekt nalezen a zmenen."""
    cs = get_core_session()
    try:
        project = cs.query(Project).filter_by(id=project_id).first()
        if project is None:
            return False
        project.name = new_name.strip()
        cs.commit()
        logger.info(f"PROJECT | renamed | id={project_id} | new_name={new_name!r}")
        return True
    finally:
        cs.close()


def set_project_default_persona(project_id: int, persona_id: int | None) -> bool:
    """
    Nastavi project.default_persona_id. NULL = vyčisteni (zpět na globální).
    Vraci True pokud nalezen.
    """
    cs = get_core_session()
    try:
        project = cs.query(Project).filter_by(id=project_id).first()
        if project is None:
            return False
        project.default_persona_id = persona_id
        cs.commit()
        logger.info(
            f"PROJECT | default_persona set | id={project_id} | persona_id={persona_id}"
        )
        return True
    finally:
        cs.close()


def set_user_last_active_project(user_id: int, project_id: int | None) -> None:
    """Set user.last_active_project_id. None = 'bez projektu'."""
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        if user is None:
            return
        user.last_active_project_id = project_id
        cs.commit()
        logger.info(
            f"PROJECT | user switch | user_id={user_id} | project_id={project_id}"
        )
    finally:
        cs.close()


def is_user_member_or_owner(user_id: int, project_id: int) -> bool:
    """True, pokud user je v user_projects NEBO je owner tenantu projektu."""
    cs = get_core_session()
    try:
        project = cs.query(Project).filter_by(id=project_id).first()
        if project is None:
            return False
        # Tenant owner ma implicitni pristup
        tenant = cs.query(Tenant).filter_by(id=project.tenant_id).first()
        if tenant and tenant.owner_user_id == user_id:
            return True
        # Jinak explicitni membership
        up = (
            cs.query(UserProject)
            .filter_by(user_id=user_id, project_id=project_id)
            .first()
        )
        return up is not None
    finally:
        cs.close()


def list_project_members(project_id: int) -> list[dict]:
    """
    Vrati clenove projektu (z user_projects) obohacene o info z User table
    + primarni email z UserContact (pro email tooly a UI).

    Pole per item: user_id, full_name, role, added_at, email.
    """
    from modules.core.infrastructure.models_core import User, UserContact

    cs = get_core_session()
    try:
        rows = (
            cs.query(UserProject, User)
            .join(User, User.id == UserProject.user_id)
            .filter(UserProject.project_id == project_id)
            .order_by(UserProject.id.asc())
            .all()
        )
        user_ids = [u.id for _, u in rows]
        # Nacti primarni emaily jednou (ne per-user query)
        primary_emails: dict[int, str] = {}
        if user_ids:
            primary_rows = (
                cs.query(UserContact)
                .filter(
                    UserContact.user_id.in_(user_ids),
                    UserContact.contact_type == "email",
                    UserContact.status == "active",
                    UserContact.is_primary.is_(True),
                )
                .all()
            )
            for c in primary_rows:
                primary_emails[c.user_id] = c.contact_value
            # Fallback: jakykoli aktivni email
            missing = [uid for uid in user_ids if uid not in primary_emails]
            if missing:
                fb = (
                    cs.query(UserContact)
                    .filter(
                        UserContact.user_id.in_(missing),
                        UserContact.contact_type == "email",
                        UserContact.status == "active",
                    )
                    .all()
                )
                for c in fb:
                    primary_emails.setdefault(c.user_id, c.contact_value)

        return [
            {
                "user_id": u.id,
                "full_name": " ".join(filter(None, [u.first_name, u.last_name])).strip()
                             or (u.short_name or "—"),
                "role": up.role,
                "added_at": up.created_at,
                "email": primary_emails.get(u.id) or "",
            }
            for up, u in rows
        ]
    finally:
        cs.close()


def add_project_member(project_id: int, user_id: int, role: str = "member") -> bool:
    """
    Prida usera jako clena projektu. Idempotentni: pokud uz je clenem,
    vrati False (nic se nedeje, ale neni to error).
    """
    cs = get_core_session()
    try:
        existing = (
            cs.query(UserProject)
            .filter_by(user_id=user_id, project_id=project_id)
            .first()
        )
        if existing is not None:
            return False  # uz je clenem
        membership = UserProject(
            user_id=user_id,
            project_id=project_id,
            role=role,
            created_at=datetime.now(timezone.utc),
        )
        cs.add(membership)
        cs.commit()
        logger.info(
            f"PROJECT | member added | project_id={project_id} | "
            f"user_id={user_id} | role={role}"
        )
        return True
    finally:
        cs.close()


def remove_project_member(project_id: int, user_id: int) -> bool:
    """
    Odebere user z user_projects. Vraci True pokud byl odebran, False
    pokud tam ani nebyl. Pokud user mel projekt jako last_active_project_id,
    vyresetujeme ho na NULL (bezpecnost — uz tam nesmi byt).
    """
    from modules.core.infrastructure.models_core import User

    cs = get_core_session()
    try:
        existing = (
            cs.query(UserProject)
            .filter_by(user_id=user_id, project_id=project_id)
            .first()
        )
        if existing is None:
            return False
        cs.delete(existing)

        # Bezpecnost: pokud user mel projekt jako aktivni, uvolnime
        u = cs.query(User).filter_by(id=user_id).first()
        if u is not None and u.last_active_project_id == project_id:
            u.last_active_project_id = None

        cs.commit()
        logger.info(
            f"PROJECT | member removed | project_id={project_id} | user_id={user_id}"
        )
        return True
    finally:
        cs.close()
