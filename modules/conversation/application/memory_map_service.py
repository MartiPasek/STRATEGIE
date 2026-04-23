"""
Memory map service (Fáze 9.2) -- kompaktní scope-specific přehledy pro
system prompt injection.

Každá funkce vrací str (ready to inject) nebo None při chybě. Limit
~500-800 tokenů per mapa, aby se prompt nepřehltil.

Volá se z composer.py *po* routeru rozhodl o módu, a podle módu vybere
odpovídající mapu:
  mode='personal' -> personal_memory_map(user_id, tenant_id, is_parent)
  mode='project'  -> project_memory_map(project_id, user_id)
  mode='work'     -> work_memory_map(tenant_id, user_id)  [stub]
  mode='system'   -> system_memory_map()                   [stub]

Každá mapa je ROZCESTNÍK -- udává overview ("o kom vím, kolik, kde je detail"),
ne plný obsah. AI pak volá konkrétní tooly (recall_thoughts, rag_search, ...)
pro detail.

Failure: při jakékoli chybě vrací None + log warning. Composer fallbackuje
na dnešní chování (build_marti_memory_block).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger

logger = get_logger("conversation.memory_map")


# ── NAME RESOLVERS (entity_type + entity_id -> display name) ───────────────

def _resolve_entity_names(
    entity_refs: list[tuple[str, int]],
) -> dict[tuple[str, int], str]:
    """
    Efektivne dohleda display names pro seznam (entity_type, entity_id) tuple-u.
    Groupy dotazy per typ -> 4 queries max (user, persona, tenant, project).

    Vrací: {(entity_type, entity_id): display_name}
    Pokud se entita nepodari resolve, klic neni v dict (volajici muze fallback
    na "#{id}").
    """
    if not entity_refs:
        return {}

    by_type: dict[str, list[int]] = {}
    for etype, eid in entity_refs:
        by_type.setdefault(etype, []).append(eid)

    resolved: dict[tuple[str, int], str] = {}

    # Users
    if "user" in by_type:
        try:
            from modules.core.infrastructure.models_core import User
            cs = get_core_session()
            try:
                users = cs.query(User).filter(User.id.in_(by_type["user"])).all()
                for u in users:
                    name = u.legal_name or ""
                    if not name:
                        first = u.first_name or ""
                        last = u.last_name or ""
                        name = f"{first} {last}".strip()
                    if not name:
                        name = u.canonical_email or f"user#{u.id}"
                    resolved[("user", u.id)] = name
            finally:
                cs.close()
        except Exception as e:
            logger.warning(f"MEMORY_MAP | resolve users failed | {e}")

    # Personas
    if "persona" in by_type:
        try:
            from modules.core.infrastructure.models_core import Persona
            cs = get_core_session()
            try:
                rows = cs.query(Persona).filter(Persona.id.in_(by_type["persona"])).all()
                for p in rows:
                    resolved[("persona", p.id)] = p.name or f"persona#{p.id}"
            finally:
                cs.close()
        except Exception as e:
            logger.warning(f"MEMORY_MAP | resolve personas failed | {e}")

    # Tenants
    if "tenant" in by_type:
        try:
            from modules.core.infrastructure.models_core import Tenant
            cs = get_core_session()
            try:
                rows = cs.query(Tenant).filter(Tenant.id.in_(by_type["tenant"])).all()
                for t in rows:
                    resolved[("tenant", t.id)] = t.name or f"tenant#{t.id}"
            finally:
                cs.close()
        except Exception as e:
            logger.warning(f"MEMORY_MAP | resolve tenants failed | {e}")

    # Projects
    if "project" in by_type:
        try:
            from modules.core.infrastructure.models_core import Project
            cs = get_core_session()
            try:
                rows = cs.query(Project).filter(Project.id.in_(by_type["project"])).all()
                for p in rows:
                    resolved[("project", p.id)] = p.name or f"project#{p.id}"
            finally:
                cs.close()
        except Exception as e:
            logger.warning(f"MEMORY_MAP | resolve projects failed | {e}")

    return resolved


# ── PERSONAL MEMORY MAP ────────────────────────────────────────────────────

def personal_memory_map(
    user_id: int | None,
    tenant_id: int | None,
    is_parent: bool = False,
) -> str | None:
    """
    Personal mode mapa: osoby s nejvíc myšlenkami + projekty + todos + diář metadata.

    Scope:
      - is_parent=True  -> cross-tenant bypass (vidí všechno)
      - is_parent=False -> jen aktuální tenant + universal (tenant_scope IS NULL)

    Limit: top 8 entit per typ (aby se prompt nepřehltil).
    """
    try:
        from modules.thoughts.application.service import (
            tree_overview as _tree,
            list_todos as _list_todos,
            diary_owners_overview as _diary,
        )

        tree = _tree(
            tenant_scope=tenant_id,
            bypass_tenant_scope=is_parent,
            include_empty_entities=False,
        )
        todos = _list_todos(
            tenant_scope=tenant_id,
            bypass_tenant_scope=is_parent,
            status_filter="open",
            limit=500,
        )
        diary_overview = _diary()
    except Exception as e:
        logger.warning(f"MEMORY_MAP | personal | core queries failed | {e}")
        return None

    # Grouping per type
    users_in_map = [t for t in tree if t["entity_type"] == "user"][:8]
    projects_in_map = [t for t in tree if t["entity_type"] == "project"][:6]
    personas_in_map = [t for t in tree if t["entity_type"] == "persona"][:4]
    tenants_in_map = [t for t in tree if t["entity_type"] == "tenant"][:4]

    # Resolve names in bulk
    refs: list[tuple[str, int]] = []
    for group in (users_in_map, projects_in_map, personas_in_map, tenants_in_map):
        refs.extend([(t["entity_type"], t["entity_id"]) for t in group])
    names = _resolve_entity_names(refs)

    def _line(t: dict) -> str:
        name = names.get((t["entity_type"], t["entity_id"])) or f"#{t['entity_id']}"
        cnt = t["total_count"]
        k = t["knowledge_count"]
        n = t["note_count"]
        return f"  • {name} (id={t['entity_id']}) — {cnt} myšlenek [{k} znal / {n} pozn]"

    parts: list[str] = ["═══ PAMĚŤOVÁ MAPA (personal mode) ═══"]

    if users_in_map:
        parts.append("\nO kom vím (osoby):")
        for t in users_in_map:
            parts.append(_line(t))
    if projects_in_map:
        parts.append("\nO kterých projektech:")
        for t in projects_in_map:
            parts.append(_line(t))
    if personas_in_map:
        parts.append("\nO kterých personách:")
        for t in personas_in_map:
            parts.append(_line(t))
    if tenants_in_map:
        parts.append("\nO kterých tenantech:")
        for t in tenants_in_map:
            parts.append(_line(t))

    # Todos
    open_todo_count = len(todos)
    if open_todo_count > 0:
        parts.append(f"\nOtevřené úkoly: {open_todo_count}")
        for t in todos[:3]:
            content = (t.get("content") or "")[:80]
            parts.append(f"  • {content}")
        if open_todo_count > 3:
            parts.append(f"  … + {open_todo_count - 3} dalších")

    # Diary summary
    if diary_overview:
        total_diary = sum(d.get("entry_count", 0) for d in diary_overview)
        parts.append(f"\nDiář: {total_diary} zápisů ({len(diary_overview)} person)")

    if len(parts) == 1:
        # Žádné myšlenky ani todos -> prázdná mapa
        parts.append("\n(Zatím si nic nepamatuješ. Proaktivně zapisuj přes `record_thought`.)")

    parts.append(
        "\nPro DETAIL: "
        "`recall_thoughts(about_user_id=X)` / `recall_thoughts(about_project_id=X)` / "
        "`recall_thoughts(query='...')`. Touto mapou vidíš jen overview, ne obsah."
    )

    return "\n".join(parts)


# ── PROJECT MEMORY MAP ─────────────────────────────────────────────────────

def project_memory_map(project_id: int, user_id: int | None = None) -> str | None:
    """
    Project mode mapa: členové, RAG dokumenty, open úkoly, project-scoped thoughts.

    Vrací text ready to inject. Pokud projekt neexistuje nebo dotaz selže, None.
    """
    if not project_id:
        return None

    try:
        from modules.core.infrastructure.models_core import Project

        cs = get_core_session()
        try:
            proj = cs.query(Project).filter_by(id=project_id).first()
            if proj is None:
                logger.warning(f"MEMORY_MAP | project_id={project_id} nenalezen")
                return None
            project_name = proj.name or f"project#{project_id}"
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"MEMORY_MAP | project | lookup failed | {e}")
        return None

    parts: list[str] = [f"═══ PROJECT SCOPE: {project_name} (id={project_id}) ═══"]

    # Členové
    try:
        from modules.projects.application.service import list_project_members
        members = list_project_members(user_id=user_id or 0, project_id=project_id)
    except Exception as e:
        logger.warning(f"MEMORY_MAP | project | members failed | {e}")
        members = []
    if members:
        parts.append("\nČlenové:")
        for m in members[:10]:
            name = m.get("display_name") or m.get("name") or f"user#{m.get('user_id')}"
            role = m.get("role") or "member"
            parts.append(f"  • {name} ({role})")
    else:
        parts.append("\nČlenové: (neznámí nebo žádní)")

    # Project-scoped thoughts count
    try:
        from modules.core.infrastructure.models_data import Thought, ThoughtEntityLink
        ds = get_data_session()
        try:
            thought_count = (
                ds.query(Thought)
                .join(ThoughtEntityLink, ThoughtEntityLink.thought_id == Thought.id)
                .filter(
                    ThoughtEntityLink.entity_type == "project",
                    ThoughtEntityLink.entity_id == project_id,
                    Thought.deleted_at.is_(None),
                )
                .count()
            )
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"MEMORY_MAP | project | thoughts count failed | {e}")
        thought_count = 0
    if thought_count > 0:
        parts.append(f"\nMyšlenky o projektu: {thought_count}")
        parts.append(
            f"  → detail: `recall_thoughts(about_project_id={project_id})`"
        )

    # RAG documents count
    try:
        from modules.core.infrastructure.models_data import Document
        ds = get_data_session()
        try:
            doc_count = (
                ds.query(Document)
                .filter(Document.project_id == project_id)
                .count()
            )
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"MEMORY_MAP | project | docs count failed | {e}")
        doc_count = 0
    if doc_count > 0:
        parts.append(f"\nDokumenty v RAG: {doc_count}")
        parts.append(
            f"  → hledej: `rag_search(query='...', project_id={project_id})`"
        )

    # Open tasks (if Task model exists and has project_id)
    try:
        from modules.core.infrastructure.models_data import Task
        ds = get_data_session()
        try:
            task_rows = (
                ds.query(Task)
                .filter(
                    Task.tenant_id.isnot(None),  # any tenant ok; we filter later
                    Task.status.in_(["open", "in_progress"]),
                )
                .limit(30)
                .all()
            )
            # Tasks don't have direct project_id in current model -- filter heuristicky
            # (můžeme přeskočit pokud není explicitní vazba)
        finally:
            ds.close()
        open_task_count = 0   # conservative -- model nemá project_id field
    except Exception as e:
        logger.warning(f"MEMORY_MAP | project | tasks failed | {e}")
        open_task_count = 0

    parts.append(
        "\nPro DETAIL: `list_project_members(project_name='" + project_name + "')`, "
        f"`recall_thoughts(about_project_id={project_id})`, "
        f"`rag_search(query='...', project_id={project_id})`."
    )
    return "\n".join(parts)


# ── WORK MEMORY MAP (stub) ─────────────────────────────────────────────────

def work_memory_map(tenant_id: int | None, user_id: int | None = None) -> str | None:
    """
    Work mode mapa (stub Fáze 9.2): tenant team + projekty.
    Plná implementace v pozdější iteraci (až bude práce reálně používaná).

    Dnes vrací minimální přehled -- seznam projektů tenantu + počet kolegů.
    Kdyby nic -> None (composer spadne na fallback).
    """
    if not tenant_id:
        return None

    try:
        from modules.core.infrastructure.models_core import (
            Tenant, UserTenant, User, Project,
        )

        cs = get_core_session()
        try:
            tenant = cs.query(Tenant).filter_by(id=tenant_id).first()
            if tenant is None:
                return None
            tenant_name = tenant.name or f"tenant#{tenant_id}"

            member_count = (
                cs.query(UserTenant)
                .filter_by(tenant_id=tenant_id, membership_status="active")
                .count()
            )

            projects = (
                cs.query(Project)
                .filter_by(tenant_id=tenant_id)
                .limit(10)
                .all()
            )
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"MEMORY_MAP | work | failed | {e}")
        return None

    parts = [f"═══ WORK SCOPE: {tenant_name} (id={tenant_id}) ═══"]
    parts.append(f"\nČlenové tenantu: {member_count} aktivních")
    if projects:
        parts.append(f"\nProjekty ({len(projects)}):")
        for p in projects:
            parts.append(f"  • {p.name} (id={p.id})")
    parts.append(
        "\nPro DETAIL: `list_users`, `list_projects`, `list_project_members(project_name='...')`."
    )
    return "\n".join(parts)


# ── SYSTEM MEMORY MAP (stub) ───────────────────────────────────────────────

def system_memory_map() -> str | None:
    """
    System mode mapa: admin operace. Minimální -- jen co je dostupné.
    """
    parts = [
        "═══ SYSTEM SCOPE (admin / maintenance) ═══",
        "",
        "Dostupné operace:",
        "  • Backup databází (UI tlačítko `💾 Zálohovat databáze` nebo API `POST /api/v1/admin/backup-databases`)",
        "  • Restart Windows služeb (STRATEGIE-API / STRATEGIE-TASK-WORKER / ...)",
        "  • Správa person (UI v Lidé / persona edit)",
        "  • Auto-send consents (UI `✉️ Důvěryhodní příjemci`)",
        "",
        "Poznámka: system mode je pro rodiče + admin operace. V této mapě nejsou "
        "osobní ani projektové informace -- soustředím se na správu systému.",
    ]
    return "\n".join(parts)


# ── DISPATCH (volá se z composer) ──────────────────────────────────────────

def build_memory_map_for_mode(
    mode: str,
    *,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
    is_parent: bool = False,
) -> str | None:
    """
    Dispatcher podle módu. Složí volání správné mapy.

    Při neznámém módu nebo chybě -> None (composer fallbackuje).
    """
    try:
        if mode == "personal":
            return personal_memory_map(user_id=user_id, tenant_id=tenant_id, is_parent=is_parent)
        if mode == "project":
            return project_memory_map(project_id=project_id, user_id=user_id)
        if mode == "work":
            return work_memory_map(tenant_id=tenant_id, user_id=user_id)
        if mode == "system":
            return system_memory_map()
        logger.warning(f"MEMORY_MAP | unknown mode '{mode}' -> None")
        return None
    except Exception as e:
        logger.exception(f"MEMORY_MAP | dispatcher failed | mode={mode} | {e}")
        return None
