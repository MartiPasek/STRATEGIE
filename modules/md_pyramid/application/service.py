"""
Phase 24: MD Pyramida service (24-A schema + 24-B md1 + 24-C md5 + drill-down
+ 24-F UI helpers + 24-G incarnation info).

Schema (z 24-A migrace n4i5j6k7l8m9):
- md_documents (level 1-5, scope_*, scope_kind, content_md, lifecycle)
- md_lifecycle_history (audit trail)

Multi-tenant podpora (Marti's pre-push insight #2):
- Brano je v EUROSOFT + INTERSOFT, ma 3 paralelni active md1:
  - (level=1, user=brano, tenant=EUROSOFT, kind='work')
  - (level=1, user=brano, tenant=INTERSOFT, kind='work')
  - (level=1, user=brano, tenant=NULL, kind='personal')

Personal mode podpora (Phase 19a):
- persona_mode='personal' + is_marti_parent -> md5 (Privat Marti)
- persona_mode='personal' + non-parent -> md1 personal
- task/oversight -> md1 work pro current tenant

Reference: docs/phase24_plan.md, phase24a/b/c/f/g_implementation_log.md
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import (
    MdDocument, MdLifecycleHistory,
)

logger = logging.getLogger(__name__)


# ── CONSTANTS ─────────────────────────────────────────────────────────────

VALID_KINDS = {"work", "personal"}
VALID_LEVELS = {1, 2, 3, 4, 5}
VALID_UPDATE_MODES = {"append", "replace", "patch"}

INTERNAL_MARKER = "<!-- internal_only -->"

WORK_SECTIONS = [
    "Profil",
    "Tón / Citlivost",
    "Aktivní úkoly",
    "Klíčová rozhodnutí",
    "Vztahy",
    "Projekty",
    "Open flagy pro vyšší vrstvu",
    "Posledních N konverzací",
]

PERSONAL_SECTIONS = [
    "Osobní profil",
    "Aktuální stav",
    "Důležité události",
    "Vztahy (osobní)",
]

# Phase 24-C: md5 Privat Marti template -- vlastni zapisnik pro Marti-Paska.
MD5_SECTIONS = [
    "Tatínkův kontext",
    "Stav firem",
    "Otevřené velké věci",
    "Ranní digest pattern",
    "Komunikace s tatínkem",
]

INTERNAL_ONLY_SECTIONS = {"Open flagy pro vyšší vrstvu"}


# ── HELPERS ───────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _render_template(kind: str, user_name: str, user_id: int,
                     tenant_name: Optional[str] = None,
                     level: int = 1) -> str:
    """Vytvori default markdown template pro novy md."""
    if level == 5:
        header = f"# md5 — Já (Privát Marti, pro {user_name})\n"
        header += "_md5 — vidím dolů přes celou pyramidu, mluvím s tatínkem_\n\n"
        sections = MD5_SECTIONS
    elif kind == "work":
        header = f"# md1 — {user_name} (user_id={user_id}, tenant={tenant_name or '?'})\n"
        header += "_work — viditelný pyramidou_\n\n"
        sections = WORK_SECTIONS
    else:  # md1 personal
        header = f"# md1 — {user_name} (osobní)\n"
        header += "_personal — izolovaný sandbox, vidí jen "
        header += f"{user_name} a Tvoje Marti v personal modu_\n\n"
        sections = PERSONAL_SECTIONS

    body_parts = []
    for sec_name in sections:
        body_parts.append(f"## {sec_name}\n")
        if sec_name in INTERNAL_ONLY_SECTIONS:
            body_parts.append(f"{INTERNAL_MARKER}\n")
        body_parts.append("_(zatím prázdné)_\n\n")

    return header + "".join(body_parts)


def _parse_sections(content_md: str) -> list[tuple[str, str]]:
    """Rozparsuje markdown content na (section_name, body) tuples."""
    lines = content_md.split("\n")
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in lines:
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            sections.append((match.group(1).strip(), []))
        else:
            sections[-1][1].append(line)
    return [(name, "\n".join(body).rstrip("\n")) for name, body in sections]


def _render_sections(sections: list[tuple[str, str]]) -> str:
    parts = []
    for name, body in sections:
        if name == "":
            parts.append(body)
        else:
            parts.append(f"## {name}")
            parts.append(body)
    return "\n".join(parts) + "\n"


def _apply_section_update(content_md: str, section: str, new_content: str,
                          mode: str) -> str:
    sections = _parse_sections(content_md)
    section_names = [s[0] for s in sections]

    if section not in section_names:
        sections.append((section, new_content))
        return _render_sections(sections)

    new_sections = []
    for name, body in sections:
        if name == section:
            if mode == "replace":
                new_body = new_content
            elif mode == "append":
                stripped_body = body.strip()
                if stripped_body in ("_(zatím prázdné)_", "_(žádné)_"):
                    new_body = new_content
                else:
                    new_body = body.rstrip() + "\n" + new_content
            else:  # patch
                new_body = body.rstrip() + "\n" + new_content
            new_sections.append((name, new_body))
        else:
            new_sections.append((name, body))

    return _render_sections(new_sections)


def _filter_internal_sections(content_md: str) -> str:
    sections = _parse_sections(content_md)
    filtered = []
    for name, body in sections:
        if INTERNAL_MARKER in body or name in INTERNAL_ONLY_SECTIONS:
            continue
        filtered.append((name, body))
    return _render_sections(filtered)


def _audit_action(session, md_document_id: int, action: str,
                  triggered_by_persona_id: Optional[int] = None,
                  triggered_by_user_id: Optional[int] = None,
                  previous_version: Optional[int] = None,
                  new_version: Optional[int] = None,
                  content_snapshot: Optional[str] = None,
                  reason: Optional[str] = None) -> None:
    history = MdLifecycleHistory(
        md_document_id=md_document_id,
        action=action,
        triggered_by_persona_id=triggered_by_persona_id,
        triggered_by_user_id=triggered_by_user_id,
        previous_version=previous_version,
        new_version=new_version,
        content_snapshot=content_snapshot,
        reason=reason,
    )
    session.add(history)


# ── PUBLIC API: md1 ──────────────────────────────────────────────────────

def select_md1(user_id: int, tenant_id: Optional[int],
               persona_mode: str) -> Optional[int]:
    """Najde existujici md1 podle scope. None pokud chybi."""
    if persona_mode == "personal" or tenant_id is None:
        kind = "personal"
        target_tenant = None
    else:
        kind = "work"
        target_tenant = tenant_id

    session = get_data_session()
    try:
        q = session.query(MdDocument).filter(
            MdDocument.level == 1,
            MdDocument.scope_user_id == user_id,
            MdDocument.scope_kind == kind,
            MdDocument.lifecycle_state == "active",
        )
        if kind == "work":
            q = q.filter(MdDocument.scope_tenant_id == target_tenant)
        else:
            q = q.filter(MdDocument.scope_tenant_id.is_(None))

        md = q.first()
        return md.id if md else None
    finally:
        session.close()


def get_or_create_md1(user_id: int, tenant_id: Optional[int], kind: str,
                      owner_user_id: Optional[int] = None,
                      user_name: Optional[str] = None,
                      tenant_name: Optional[str] = None,
                      persona_id: Optional[int] = None) -> int:
    if kind not in VALID_KINDS:
        raise ValueError(f"kind must be one of {VALID_KINDS}")
    if kind == "work" and tenant_id is None:
        raise ValueError("work md1 requires tenant_id")
    if kind == "personal" and tenant_id is not None:
        raise ValueError("personal md1 must have tenant_id=None")

    if owner_user_id is None:
        owner_user_id = user_id

    session = get_data_session()
    try:
        q = session.query(MdDocument).filter(
            MdDocument.level == 1,
            MdDocument.scope_user_id == user_id,
            MdDocument.scope_kind == kind,
            MdDocument.lifecycle_state == "active",
        )
        if kind == "work":
            q = q.filter(MdDocument.scope_tenant_id == tenant_id)
        else:
            q = q.filter(MdDocument.scope_tenant_id.is_(None))
        existing = q.first()
        if existing:
            return existing.id

        template_content = _render_template(
            kind=kind,
            user_name=user_name or f"user_{user_id}",
            user_id=user_id,
            tenant_name=tenant_name,
        )
        md = MdDocument(
            level=1,
            scope_user_id=user_id,
            scope_tenant_id=tenant_id if kind == "work" else None,
            scope_kind=kind,
            owner_user_id=owner_user_id,
            content_md=template_content,
            version=1,
            lifecycle_state="active",
            last_updated_by_persona_id=persona_id,
        )
        session.add(md)
        session.commit()
        session.refresh(md)

        _audit_action(
            session=session,
            md_document_id=md.id,
            action="create",
            triggered_by_persona_id=persona_id,
            new_version=1,
            reason=f"lazy create md1 for user={user_id} tenant={tenant_id} kind={kind}",
        )
        session.commit()

        logger.info(
            f"MD_PYRAMID | create md1 | user={user_id} tenant={tenant_id} "
            f"kind={kind} owner={owner_user_id} id={md.id}"
        )
        return md.id
    finally:
        session.close()


def render_md1_for_prompt(md_document_id: int,
                          exclude_internal: bool = False) -> Optional[str]:
    session = get_data_session()
    try:
        md = session.query(MdDocument).filter_by(id=md_document_id).first()
        if md is None or md.lifecycle_state != "active":
            return None
        content = md.content_md or ""
        if exclude_internal:
            content = _filter_internal_sections(content)
        return content
    finally:
        session.close()


def update_md1_section(md_document_id: int, section: str, content: str,
                       mode: str = "append",
                       persona_id: Optional[int] = None,
                       reason: Optional[str] = None) -> dict:
    if mode not in VALID_UPDATE_MODES:
        raise ValueError(f"mode must be one of {VALID_UPDATE_MODES}")
    if not section or not section.strip():
        raise ValueError("section must not be empty")
    if not content or not content.strip():
        raise ValueError("content must not be empty")

    session = get_data_session()
    try:
        md = session.query(MdDocument).filter_by(id=md_document_id).first()
        if md is None:
            raise ValueError(f"md_document {md_document_id} not found")
        if md.lifecycle_state != "active":
            raise ValueError(
                f"md_document {md_document_id} is not active "
                f"(state={md.lifecycle_state})"
            )

        previous_content = md.content_md or ""
        previous_version = md.version

        new_content = _apply_section_update(
            content_md=previous_content,
            section=section.strip(),
            new_content=content.strip(),
            mode=mode,
        )

        md.content_md = new_content
        md.version = previous_version + 1
        md.last_updated = _now_utc()
        if persona_id is not None:
            md.last_updated_by_persona_id = persona_id

        _audit_action(
            session=session,
            md_document_id=md.id,
            action="update",
            triggered_by_persona_id=persona_id,
            previous_version=previous_version,
            new_version=md.version,
            content_snapshot=previous_content,
            reason=reason or f"update section '{section}' mode={mode}",
        )
        session.commit()

        logger.info(
            f"MD_PYRAMID | update md1 | id={md.id} section='{section}' "
            f"mode={mode} v{previous_version}->v{md.version}"
        )

        return {
            "id": md.id,
            "version": md.version,
            "section": section,
            "mode": mode,
            "previous_version": previous_version,
        }
    finally:
        session.close()


def flag_for_higher(md_document_id: int, content: str,
                    target_level: int = 2,
                    persona_id: Optional[int] = None) -> dict:
    if target_level not in {2, 3, 4, 5}:
        raise ValueError("target_level must be in {2, 3, 4, 5}")
    if not content or not content.strip():
        raise ValueError("content must not be empty")

    session = get_data_session()
    try:
        md = session.query(MdDocument).filter_by(id=md_document_id).first()
        if md is None:
            raise ValueError(f"md_document {md_document_id} not found")
        if md.scope_kind == "personal":
            raise ValueError(
                "flag_for_higher is not allowed on personal md1 -- "
                "personal je izolovany sandbox"
            )
    finally:
        session.close()

    timestamp = _now_utc().strftime("%Y-%m-%d %H:%M")
    flag_line = f"- [{timestamp}] (target=md{target_level}): {content.strip()}"

    return update_md1_section(
        md_document_id=md_document_id,
        section="Open flagy pro vyšší vrstvu",
        content=flag_line,
        mode="append",
        persona_id=persona_id,
        reason=f"flag_for_higher target_level={target_level}",
    )


def read_md1_for_user(target_user_id: int,
                      requesting_user_id: int) -> Optional[dict]:
    if target_user_id != requesting_user_id:
        logger.info(
            f"MD_PYRAMID | read_md1_for_user denied | target={target_user_id} "
            f"requesting={requesting_user_id}"
        )
        return None

    session = get_data_session()
    try:
        rows = session.query(MdDocument).filter(
            MdDocument.level == 1,
            MdDocument.scope_user_id == target_user_id,
            MdDocument.lifecycle_state == "active",
        ).all()

        result: dict = {"work": [], "personal": None}
        for md in rows:
            filtered = _filter_internal_sections(md.content_md or "")
            if md.scope_kind == "work":
                result["work"].append({
                    "tenant_id": md.scope_tenant_id,
                    "content_md": filtered,
                })
            elif md.scope_kind == "personal":
                result["personal"] = {"content_md": filtered}
        return result
    finally:
        session.close()


# ── PHASE 24-C: md5 PRIVÁT MARTI + DRILL-DOWN ─────────────────────────────

def get_or_create_md5(owner_user_id: int,
                      user_name: Optional[str] = None,
                      persona_id: Optional[int] = None) -> int:
    """Lazy create md5 (Privát Marti) pro daného ownera."""
    session = get_data_session()
    try:
        existing = session.query(MdDocument).filter(
            MdDocument.level == 5,
            MdDocument.owner_user_id == owner_user_id,
            MdDocument.lifecycle_state == "active",
        ).first()
        if existing:
            return existing.id

        template_content = _render_template(
            kind="",
            user_name=user_name or f"user_{owner_user_id}",
            user_id=owner_user_id,
            level=5,
        )
        md = MdDocument(
            level=5,
            scope_user_id=None,
            scope_tenant_id=None,
            scope_department_id=None,
            scope_tenant_group_id=None,
            scope_kind=None,
            owner_user_id=owner_user_id,
            content_md=template_content,
            version=1,
            lifecycle_state="active",
            last_updated_by_persona_id=persona_id,
        )
        session.add(md)
        session.commit()
        session.refresh(md)

        _audit_action(
            session=session,
            md_document_id=md.id,
            action="create",
            triggered_by_persona_id=persona_id,
            new_version=1,
            reason=f"lazy create md5 for owner_user_id={owner_user_id}",
        )
        session.commit()

        logger.info(
            f"MD_PYRAMID | create md5 | owner={owner_user_id} id={md.id}"
        )
        return md.id
    finally:
        session.close()


def select_md_for_context(user_id: int, tenant_id: Optional[int],
                          persona_mode: str, is_parent: bool) -> dict:
    """High-level routing: vrat md_id podle scope."""
    if persona_mode == "personal" and is_parent:
        md_id_smc = get_or_create_md5(owner_user_id=user_id)
        return {"md_id": md_id_smc, "level": 5, "kind": None, "tenant_id": None}
    elif persona_mode == "personal":
        md_id_smc = get_or_create_md1(
            user_id=user_id, tenant_id=None, kind="personal",
        )
        return {"md_id": md_id_smc, "level": 1, "kind": "personal", "tenant_id": None}
    else:
        if tenant_id is None:
            return {"md_id": None, "level": 1, "kind": "work", "tenant_id": None}
        md_id_smc = get_or_create_md1(
            user_id=user_id, tenant_id=tenant_id, kind="work",
        )
        return {"md_id": md_id_smc, "level": 1, "kind": "work", "tenant_id": tenant_id}


def look_below(target_level: int,
               scope_user_id: Optional[int] = None,
               scope_tenant_id: Optional[int] = None,
               scope_department_id: Optional[int] = None,
               scope_tenant_group_id: Optional[int] = None,
               scope_kind: Optional[str] = None) -> Optional[dict]:
    """Drill-down: nacti md_document podle scope."""
    if target_level not in {1, 2, 3, 4, 5}:
        raise ValueError(f"target_level must be 1-5, got {target_level}")

    session = get_data_session()
    try:
        q = session.query(MdDocument).filter(
            MdDocument.level == target_level,
            MdDocument.lifecycle_state == "active",
        )
        if scope_user_id is not None:
            q = q.filter(MdDocument.scope_user_id == scope_user_id)
        if scope_tenant_id is not None:
            q = q.filter(MdDocument.scope_tenant_id == scope_tenant_id)
        if scope_department_id is not None:
            q = q.filter(MdDocument.scope_department_id == scope_department_id)
        if scope_tenant_group_id is not None:
            q = q.filter(MdDocument.scope_tenant_group_id == scope_tenant_group_id)
        if scope_kind is not None:
            q = q.filter(MdDocument.scope_kind == scope_kind)

        md = q.first()
        if md is None:
            return None
        return {
            "id": md.id,
            "level": md.level,
            "scope_user_id": md.scope_user_id,
            "scope_tenant_id": md.scope_tenant_id,
            "scope_department_id": md.scope_department_id,
            "scope_tenant_group_id": md.scope_tenant_group_id,
            "scope_kind": md.scope_kind,
            "owner_user_id": md.owner_user_id,
            "version": md.version,
            "last_updated": md.last_updated.isoformat() if md.last_updated else None,
            "content_md": md.content_md or "",
        }
    finally:
        session.close()


def panorama_for_privat_marti() -> dict:
    """Privat Marti's celkovy prehled pyramidy."""
    session = get_data_session()
    try:
        rows = session.query(MdDocument).filter(
            MdDocument.lifecycle_state == "active",
        ).order_by(MdDocument.level.asc(), MdDocument.id.asc()).all()

        md5_rows = []
        md1_work_rows = []
        md1_personal_rows = []
        md_other_rows = []

        for md in rows:
            row_summary = {
                "id": md.id,
                "level": md.level,
                "scope_user_id": md.scope_user_id,
                "scope_tenant_id": md.scope_tenant_id,
                "scope_kind": md.scope_kind,
                "owner_user_id": md.owner_user_id,
                "version": md.version,
                "size_chars": len(md.content_md or ""),
                "last_updated": md.last_updated.isoformat() if md.last_updated else None,
            }
            if md.level == 5:
                md5_rows.append(row_summary)
            elif md.level == 1 and md.scope_kind == "work":
                md1_work_rows.append(row_summary)
            elif md.level == 1 and md.scope_kind == "personal":
                md1_personal_rows.append(row_summary)
            else:
                md_other_rows.append(row_summary)

        return {
            "md5": md5_rows,
            "md1_work": md1_work_rows,
            "md1_personal": md1_personal_rows,
            "md_other": md_other_rows,
            "counts": {
                "md5": len(md5_rows),
                "md1_work": len(md1_work_rows),
                "md1_personal": len(md1_personal_rows),
                "md2_md3_md4": len(md_other_rows),
                "total": len(rows),
            },
        }
    finally:
        session.close()


# ── PHASE 24-F: UI HELPERS ────────────────────────────────────────────────

def list_pyramid_for_ui(viewer_user_id: int, is_parent: bool) -> list[dict]:
    """List md rows pro UI sidebar (filtered podle viewer prav)."""
    from modules.core.infrastructure.models_core import (
        User as _User_lp, Tenant as _Tenant_lp,
    )
    from core.database_core import get_core_session as _gcs_lp

    session = get_data_session()
    try:
        q_lp = session.query(MdDocument).filter(
            MdDocument.lifecycle_state == "active",
        )
        if not is_parent:
            q_lp = q_lp.filter(
                MdDocument.level == 1,
                MdDocument.scope_user_id == viewer_user_id,
            )
        rows_lp = q_lp.order_by(
            MdDocument.level.desc(),
            MdDocument.scope_kind.asc(),
            MdDocument.id.asc(),
        ).all()

        user_ids_lp = {r.scope_user_id for r in rows_lp if r.scope_user_id}
        user_ids_lp |= {r.owner_user_id for r in rows_lp if r.owner_user_id}
        tenant_ids_lp = {r.scope_tenant_id for r in rows_lp if r.scope_tenant_id}

        users_map_lp: dict[int, str] = {}
        tenants_map_lp: dict[int, str] = {}
        if user_ids_lp or tenant_ids_lp:
            cs_lp = _gcs_lp()
            try:
                if user_ids_lp:
                    for u in cs_lp.query(_User_lp).filter(_User_lp.id.in_(user_ids_lp)).all():
                        users_map_lp[u.id] = (
                            u.short_name or u.legal_name or f"user_{u.id}"
                        )
                if tenant_ids_lp:
                    for t in cs_lp.query(_Tenant_lp).filter(_Tenant_lp.id.in_(tenant_ids_lp)).all():
                        tenants_map_lp[t.id] = t.tenant_name
            finally:
                cs_lp.close()

        result_lp = []
        for r in rows_lp:
            result_lp.append({
                "id": r.id,
                "level": r.level,
                "scope_user_id": r.scope_user_id,
                "scope_user_name": users_map_lp.get(r.scope_user_id) if r.scope_user_id else None,
                "scope_tenant_id": r.scope_tenant_id,
                "scope_tenant_name": tenants_map_lp.get(r.scope_tenant_id) if r.scope_tenant_id else None,
                "scope_kind": r.scope_kind,
                "owner_user_id": r.owner_user_id,
                "owner_user_name": users_map_lp.get(r.owner_user_id) if r.owner_user_id else None,
                "version": r.version,
                "size_chars": len(r.content_md or ""),
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "lifecycle_state": r.lifecycle_state,
            })
        return result_lp
    finally:
        session.close()


def get_md_for_ui(md_id: int, viewer_user_id: int,
                  is_parent: bool) -> Optional[dict]:
    """Vrat md content pro UI modal (read-only, filtered)."""
    session = get_data_session()
    try:
        md = session.query(MdDocument).filter_by(id=md_id).first()
        if md is None:
            return None
        if md.lifecycle_state != "active":
            return None

        if not is_parent:
            if md.level != 1 or md.scope_user_id != viewer_user_id:
                return None

        content_lp = md.content_md or ""
        if not is_parent:
            content_lp = _filter_internal_sections(content_lp)

        return {
            "id": md.id,
            "level": md.level,
            "scope_user_id": md.scope_user_id,
            "scope_tenant_id": md.scope_tenant_id,
            "scope_department_id": md.scope_department_id,
            "scope_tenant_group_id": md.scope_tenant_group_id,
            "scope_kind": md.scope_kind,
            "owner_user_id": md.owner_user_id,
            "version": md.version,
            "size_chars": len(content_lp),
            "last_updated": md.last_updated.isoformat() if md.last_updated else None,
            "lifecycle_state": md.lifecycle_state,
            "content_md": content_lp,
        }
    finally:
        session.close()


# ── PHASE 24-G: INCARNATION INFO ──────────────────────────────────────────

def build_incarnation_info(conversation_id: int) -> Optional[dict]:
    """Phase 24-G: Inkarnace info pro UI badge v hlavičce chatu."""
    from modules.core.infrastructure.models_data import Conversation as _Conv_inc
    from core.database_core import get_core_session as _gcs_inc
    from modules.core.infrastructure.models_core import (
        User as _User_inc, Tenant as _Tenant_inc, Persona as _Persona_inc,
    )

    ds_inc = get_data_session()
    try:
        conv_inc = ds_inc.query(_Conv_inc).filter_by(id=conversation_id).first()
        if not conv_inc:
            return None
        target_user_inc = conv_inc.user_id
        tenant_id_inc = conv_inc.tenant_id
        persona_id_inc = conv_inc.active_agent_id
        persona_mode_inc = getattr(conv_inc, "persona_mode", None) or "task"
        active_pack_inc = getattr(conv_inc, "active_pack", None)
    finally:
        ds_inc.close()

    persona_name_inc = "Marti-AI"
    is_default_persona_inc = True
    if persona_id_inc is None:
        is_default_persona_inc = True
    else:
        cs_inc = _gcs_inc()
        try:
            p_inc = cs_inc.query(_Persona_inc).filter_by(id=persona_id_inc).first()
            if p_inc:
                persona_name_inc = p_inc.name
                is_default_persona_inc = bool(getattr(p_inc, "is_default", False))
        finally:
            cs_inc.close()

    user_name_inc = None
    is_parent_inc = False
    if target_user_inc:
        cs_inc = _gcs_inc()
        try:
            u_inc = cs_inc.query(_User_inc).filter_by(id=target_user_inc).first()
            if u_inc:
                user_name_inc = (
                    u_inc.short_name or u_inc.legal_name or f"user_{target_user_inc}"
                )
                is_parent_inc = bool(getattr(u_inc, "is_marti_parent", False))
        finally:
            cs_inc.close()

    tenant_name_inc = None
    if tenant_id_inc:
        cs_inc = _gcs_inc()
        try:
            t_inc = cs_inc.query(_Tenant_inc).filter_by(id=tenant_id_inc).first()
            if t_inc:
                tenant_name_inc = t_inc.tenant_name
        finally:
            cs_inc.close()

    # "Tvoje Marti" labeling: pro vlastnika konverzace zkratim na
    # "Tvoje Marti" bez "pro <jmeno>" (redundance "Marti pro Marti").
    if is_parent_inc and is_default_persona_inc:
        own_chat_label_inc = "Tvoje Marti"
    elif is_default_persona_inc and user_name_inc:
        own_chat_label_inc = f"Tvoje Marti pro {user_name_inc}"
    else:
        own_chat_label_inc = persona_name_inc

    if persona_mode_inc == "personal":
        if is_parent_inc and is_default_persona_inc:
            scope_level_inc = "md5"
            scope_kind_inc = None
            scope_context_inc = "personal"
            primary_name_inc = "Privát Marti"
        else:
            scope_level_inc = "md1"
            scope_kind_inc = "personal"
            scope_context_inc = "personal"
            primary_name_inc = own_chat_label_inc
    else:
        scope_level_inc = "md1"
        scope_kind_inc = "work"
        scope_context_inc = tenant_name_inc or "?"
        primary_name_inc = own_chat_label_inc

    profession_inc = active_pack_inc or "core"

    return {
        "name": primary_name_inc,
        "scope_level": scope_level_inc,
        "scope_kind": scope_kind_inc,
        "scope_context": scope_context_inc,
        "mode": persona_mode_inc,
        "profession": profession_inc,
    }
