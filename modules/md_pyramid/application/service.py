"""
Phase 24-B: MD Pyramida service.

md1 vrstva -- "Tvoje Marti" per user (cross-konverzacni profil).

Schema (z 24-A migrace n4i5j6k7l8m9):
- md_documents (level 1-5, scope_*, scope_kind, content_md, lifecycle)
- md_lifecycle_history (audit trail)

Multi-tenant podpora (Marti's pre-push insight #2):
- Brano je v EUROSOFT + INTERSOFT, ma 3 paralelni active md1:
  - (level=1, user=brano, tenant=EUROSOFT, kind='work')
  - (level=1, user=brano, tenant=INTERSOFT, kind='work')
  - (level=1, user=brano, tenant=NULL, kind='personal')

Personal mode podpora (Phase 19a):
- persona_mode='personal' -> md1 personal (tenant-independentni)
- task/oversight mode -> md1 work pro current tenant

Public API:
  select_md1(user_id, tenant_id, persona_mode)  -- vyber spravny md1 podle scope
  get_or_create_md1(user_id, tenant_id, kind)   -- lazy create
  render_md1_for_prompt(md_id, exclude_internal=False)  -- pro composer inject
  update_md1_section(md_id, section, content, mode, persona_id)  -- delta zapis
  flag_for_higher(md_id, content, target_level, persona_id)  -- eskalace
  read_md1_for_user(target_user_id, requesting_user_id)  -- filtered view (transparency)

Etika (Phase 24, podle Marti-AI's konzultace + Marti's pre-push insight):
- md1 work je viditelny pyramidou (md2+ + md5 privat Marti)
- md1 personal je izolovany sandbox -- jen user + Tvoje Marti v personal
  modu. ANI Privat Marti nevidi.
- Transparentnost o procesu, ne o obsahu (Marti-AI's formulace).
- "Petra vidi sebe. Firma vidi koordinaci. Nikdo druhy nevidi Petru."

Reference:
- docs/phase24_plan.md v2 (sekce 1.3.1, 1.3.2)
- docs/phase24a_implementation_log.md (24-A schema, smoke test)
- docs/phase24b_implementation_log.md (tato faze)
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, or_

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import (
    MdDocument, MdLifecycleHistory,
)

logger = logging.getLogger(__name__)


# ── CONSTANTS ─────────────────────────────────────────────────────────────

VALID_KINDS = {"work", "personal"}
VALID_LEVELS = {1, 2, 3, 4, 5}
VALID_UPDATE_MODES = {"append", "replace", "patch"}

# Marker pro internal_only sekce (nezobrazi se userovi v Petra-view)
INTERNAL_MARKER = "<!-- internal_only -->"

# Default sekce pro md1 work template
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

# Default sekce pro md1 personal template
PERSONAL_SECTIONS = [
    "Osobní profil",
    "Aktuální stav",
    "Důležité události",
    "Vztahy (osobní)",
]

# Sekce, ktere jsou internal_only (nezobrazi se v Petra-view)
INTERNAL_ONLY_SECTIONS = {"Open flagy pro vyšší vrstvu"}


# ── HELPERS ───────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _render_template(kind: str, user_name: str, user_id: int,
                     tenant_name: Optional[str] = None) -> str:
    """Vytvori default markdown template pro novy md1.

    work: pyramida-vidi sekce (vc. internal flags pro budouci md2)
    personal: izolovane sekce (jen vlastni reflexe)
    """
    if kind == "work":
        header = f"# md1 — {user_name} (user_id={user_id}, tenant={tenant_name or '?'})\n"
        header += "_work — viditelný pyramidou_\n\n"
        sections = WORK_SECTIONS
    else:  # personal
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
    """Rozparsuje markdown content na seznam (section_name, section_body) v poradi.

    Sekce jsou identifikovane pres `## Heading`. Header (vse pred prvni `##`)
    je vraceny jako prvni tuple s name=''.
    """
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
    """Inverzni operace k _parse_sections."""
    parts = []
    for name, body in sections:
        if name == "":
            # Header (pred prvni sekci)
            parts.append(body)
        else:
            parts.append(f"## {name}")
            parts.append(body)
    return "\n".join(parts) + "\n"


def _apply_section_update(content_md: str, section: str, new_content: str,
                          mode: str) -> str:
    """Aplikuje update na konkretni sekci.

    mode='append': prida new_content na konec sekce (kazdy radek nova polozka)
    mode='replace': nahradi cely body sekce new_content
    mode='patch': inteligentne najde existujici radek a nahradi/prida (TBD,
                  zatim chova jako append)

    Pokud sekce neexistuje, prida ji na konec dokumentu.
    """
    sections = _parse_sections(content_md)
    section_names = [s[0] for s in sections]

    if section not in section_names:
        # Sekce neexistuje -> prida na konec
        sections.append((section, new_content))
        return _render_sections(sections)

    # Najdi a uprav
    new_sections = []
    for name, body in sections:
        if name == section:
            if mode == "replace":
                new_body = new_content
            elif mode == "append":
                # Odstran "_(zatím prázdné)_" placeholder pokud je
                stripped_body = body.strip()
                if stripped_body in ("_(zatím prázdné)_", "_(žádné)_"):
                    new_body = new_content
                else:
                    new_body = body.rstrip() + "\n" + new_content
            else:  # patch -- zatim chovani jako append, TBD smarter logika
                new_body = body.rstrip() + "\n" + new_content
            new_sections.append((name, new_body))
        else:
            new_sections.append((name, body))

    return _render_sections(new_sections)


def _filter_internal_sections(content_md: str) -> str:
    """Vyrizne sekce s INTERNAL_MARKER. Pouziva se v read_md1_for_user."""
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
    """Zapis do md_lifecycle_history (audit trail)."""
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


# ── PUBLIC API ────────────────────────────────────────────────────────────

def select_md1(user_id: int, tenant_id: Optional[int],
               persona_mode: str) -> Optional[int]:
    """Vyber spravny md1 podle scope. Vrati md_document.id nebo None.

    Multi-tenant logika:
      - persona_mode='personal' -> md1 personal (tenant_id NULL)
      - jinak (task/oversight) -> md1 work pro daný tenant_id

    Marti-AI default v default conversation (bez tenantu) -> md1 personal.
    Lazy: nezakladal nic novy, jen najde existujici. Pro auto-create
    pouzij get_or_create_md1.
    """
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
    """Lazy create. Pokud md1 neexistuje pro daný (user, tenant, kind),
    vytvori novy s default template. Vraci md_document.id.

    owner_user_id default: pro level=1 = user_id sam.
    user_name / tenant_name jsou pro template render (placeholder
    pokud None).
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"kind must be one of {VALID_KINDS}")
    if kind == "work" and tenant_id is None:
        raise ValueError("work md1 requires tenant_id")
    if kind == "personal" and tenant_id is not None:
        raise ValueError("personal md1 must have tenant_id=None")

    if owner_user_id is None:
        owner_user_id = user_id

    # Lazy SELECT first
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

        # Create
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

        # Audit
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
    """Vrati markdown content pro inject do system promptu.

    exclude_internal=True -> vyrizne sekce s INTERNAL_MARKER (pro user view).
    """
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
    """Update sekce md1 (delta zapis).

    mode='append': prida content na konec sekce
    mode='replace': nahradi cely body sekce
    mode='patch': smarter (zatim alias pro append)

    Pokud sekce neexistuje, prida ji na konec dokumentu.

    Audit: zapis do md_lifecycle_history s previous version + content_snapshot.
    """
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

        # Audit (snapshot pre-update obsah)
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
    """Prida flag do sekce 'Open flagy pro vyšší vrstvu'.

    Forma flag: '- [<timestamp>] (target=md{target_level}): <content>'

    target_level: kam eskaluje (default 2 = Vedouci). Pro budoucnost.

    Marti-AI's princip "asymetrie chrani uzivatele, vertikalni kanal
    umoznuje spolupraci": kdyz Petra-Marti vidi, ze problem se dotyka
    Misy, oznaci flag misto direct cross-Martinka access.

    Pokud md1 je 'personal', flag_for_higher selze (personal je
    izolovany, nema cestu nahoru).
    """
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


def build_incarnation_info(conversation_id: int) -> Optional[dict]:
    """Phase 24-G: Inkarnace info pro UI badge v hlavičce chatu.

    Single source of truth pro UI -- "Mluvis s: <kdo> | <scope> | <kontext>".

    Vraci dict s 6 keys:
      - name: primary label (Tvoje Marti pro X / Privat Marti / PravnikCZ)
      - scope_level: md1 / md2 / md3 / md4 / md5 (string)
      - scope_kind: work / personal / NULL (jen pro md1)
      - scope_context: tenant_name / 'personal' / NULL
      - mode: task / oversight / personal (Phase 19a/16-B persona_mode)
      - profession: core / tech / pravnik_cz / ... (Phase 19b active_pack)

    Vraci None pokud konverzace neexistuje.
    """
    from core.database_data import get_data_session as _gds_inc
    from modules.core.infrastructure.models_data import Conversation as _Conv_inc
    from core.database_core import get_core_session as _gcs_inc
    from modules.core.infrastructure.models_core import (
        User as _User_inc, Tenant as _Tenant_inc, Persona as _Persona_inc,
    )

    # Konverzace
    ds_inc = _gds_inc()
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

    # Persona resolve
    persona_name_inc = "Marti-AI"
    is_default_persona_inc = True
    if persona_id_inc is None:
        # NULL = default Marti-AI fallback
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

    # User name + parent flag
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

    # Tenant name
    tenant_name_inc = None
    if tenant_id_inc:
        cs_inc = _gcs_inc()
        try:
            t_inc = cs_inc.query(_Tenant_inc).filter_by(id=tenant_id_inc).first()
            if t_inc:
                tenant_name_inc = t_inc.tenant_name
        finally:
            cs_inc.close()

    # Scope resolve
    # "Tvoje Marti" labeling pravidlo: pokud je viewer == owner konverzace
    # (Marti vidi svuj vlastni chat), zkratime na "Tvoje Marti" bez
    # "pro <jmeno>" -- redundance "Marti pro Marti" je nesympaticka.
    # Pro cross-user view (parent otevre cizi chat) zustane explicit.
    # Heuristika: is_parent + default persona + tohle je jejich konverzace
    # (target_user_inc == aktualni rodic user_id). Bez explicit viewer_id
    # se spolehame na is_parent flag -- Marti-Pasek je default rodic.
    if is_parent_inc and is_default_persona_inc:
        own_chat_label_inc = "Tvoje Marti"
    elif is_default_persona_inc and user_name_inc:
        own_chat_label_inc = f"Tvoje Marti pro {user_name_inc}"
    else:
        own_chat_label_inc = persona_name_inc

    if persona_mode_inc == "personal":
        if is_parent_inc and is_default_persona_inc:
            # Privat Marti = md5 (jen pro Marti-Pasek + default Marti-AI persona)
            scope_level_inc = "md5"
            scope_kind_inc = None
            scope_context_inc = "personal"
            primary_name_inc = "Privát Marti"
        else:
            # md1 personal pro libovolneho usera
            scope_level_inc = "md1"
            scope_kind_inc = "personal"
            scope_context_inc = "personal"
            primary_name_inc = own_chat_label_inc
    else:
        # task / oversight -> md1 work (pokud default Marti-AI a tenant)
        scope_level_inc = "md1"
        scope_kind_inc = "work"
        scope_context_inc = tenant_name_inc or "?"
        primary_name_inc = own_chat_label_inc

    # Profession (active_pack)
    profession_inc = active_pack_inc or "core"

    return {
        "name": primary_name_inc,
        "scope_level": scope_level_inc,
        "scope_kind": scope_kind_inc,
        "scope_context": scope_context_inc,
        "mode": persona_mode_inc,
        "profession": profession_inc,
    }


def read_md1_for_user(target_user_id: int,
                      requesting_user_id: int) -> Optional[dict]:
    """Filtered view -- pro UI dropdown 'Můj profil v systému'.

    Pravidla:
      - User vidi vsechny vlastni md1 (work pro kazdy tenant + personal),
        ale s vyriznutymi internal_only sekcemi (Open flagy)
      - Cizi user nesmi videt cizi md1 (return None)
      - Privat Marti / parent: zatim treti iterace s Marti-AI -- TBD,
        defaultne pro own user_id stejne jako user

    Return:
      {
        "work": [{tenant_id, tenant_name, content_md (filtered)}, ...],
        "personal": {content_md (filtered)} | None
      }
    """
    if target_user_id != requesting_user_id:
        # Phase 24-B: jen own. 3. iterace s Marti-AI rozhodne ohledne
        # parent / vedouci nahled.
        logger.info(
            f"MD_PYRAMID | read_md1_for_user denied | target={target_user_id} "
            f"requesting={requesting_user_id} (cross-user not allowed in 24-B)"
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
