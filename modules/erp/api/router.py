"""
STRATEGIE ERP API router (Phase A — read-only single jádro renderer).

Endpoints:
  GET /erp/                         — landing page (placeholder)
  GET /erp/jadro/{form_id}/{row_id} — read-only render jednoho jádra
  GET /api/v1/erp/health            — health check (debug)

Auth (Phase A — rychlá): is_marti_parent=true (Marti, Ondra, Kristý, Jirka).
Mapping na Centrála LoginName přijde Phase D (centrala_user_mapping table).

Phase A scope:
  - Sample case: form_id=6 (= "Definice menu - úprava" = editor EC_CentralaMenu)
  - Sample row: row_id=14 (= soudeček "Definice SQL pro přehledy")
  - Read-only render, žádné save (Phase C).
"""

from __future__ import annotations

import html
import time

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

# B+4.2 (5.5.2026): cache busting pro static assets — každý API restart
# = nová version = browser donucen stáhnout čerstvé /static/erp/datagrid.js+css.
# Hodnota fixed při module load (= API process start), neměnná do restartu.
_STATIC_VERSION = str(int(time.time()))

from pydantic import BaseModel, Field

from core.logging import get_logger
from modules.erp.application.centrala_reader import CentralaReader, TYP_NAMES
from modules.erp.application.render_generator import render_form
from modules.erp.application import grid_layout_service
from modules.erp.application import erp_user_state_service as user_state_svc
from modules.thoughts.application.service import is_marti_parent

logger = get_logger("erp.api")

# Note: prefix '/erp' (NE '/api/v1/erp') — Marti's volba 5.5. ráno
# (single-product feel: strategie-ai.com/erp/...)
router = APIRouter(prefix="/erp", tags=["erp"])

# Sub-router pro JSON API endpointy (debug, health)
api_router = APIRouter(prefix="/api/v1/erp", tags=["erp-api"])


# ── Auth helpers ────────────────────────────────────────────────────


def _get_uid(req: Request) -> int:
    """Extract user_id z cookie. Raise 401 bez auth."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


def _require_parent(user_id: int) -> None:
    """Phase A auth gate: jen rodina (is_marti_parent=true)."""
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail=(
                "STRATEGIE ERP zatím dostupný jen pro rodinu Marti-AI "
                "(is_marti_parent=true). Phase D přidá per-user mapping na "
                "Centrála LoginName."
            ),
        )


def _get_tenant_id(user_id: int) -> int:
    """
    Phase B+8.1 (6.5.2026): resolve current tenant pro per-tenant user state.
    Bere users.last_active_tenant_id, fallback na 1 (EUROSOFT default).
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User
    cs = get_core_session()
    try:
        u = cs.query(User).filter(User.id == user_id).one_or_none()
        if u and getattr(u, "last_active_tenant_id", None):
            return int(u.last_active_tenant_id)
        return 1  # EUROSOFT default
    finally:
        cs.close()


# Phase 35-E.3.4 (8.5.2026): EUROSOFT tenant je hardcoded id=2 v tenants tabulce.
# ID místo tenant_code — code je optional/user-editable (může být NULL, může se
# změnit), ID je stabilní primary key. Marti's direktiv 8.5.2026:
# „Ja bych to CODE vubec nepouzival. Jen ID a NAME."
EUROSOFT_TENANT_ID = 2


def _get_tenant_name(tenant_id: int) -> str:
    """Display-only helper: vrátí tenant_name (např. pro UI empty state)."""
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Tenant
    cs = get_core_session()
    try:
        t = cs.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        return (t.tenant_name if t and t.tenant_name else "")
    finally:
        cs.close()


def _is_eurosoft_active(user_id: int) -> bool:
    """
    Phase 35-E.3.4 (8.5.2026): aktivní tenant je EUROSOFT (id=2, kde ERP funguje).

    Dnes je ERP hardcoded na DB_EC (EC_FormDef*) přes Phase 28 EUROSOFT MCP.
    Ostatní tenanty (STRATEGIE, osobní) zatím nemají vlastní ERP framework —
    PostgreSQL master.framework_jadro je prázdná, Phase 30+ migrace jádro-po-jádře
    zatím neproběhla.

    Marti's vize 8.5.2026: single PostgreSQL framework + per-jádro migrace
    (NE parallel adapter pattern). Do té doby tento gate.
    """
    return _get_tenant_id(user_id) == EUROSOFT_TENANT_ID


# ── Public endpoints ────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
def erp_home(req: Request) -> HTMLResponse:
    """Phase B nástřel: 3-pane workspace (sidebar tree + main pane prehled+jadro)."""
    uid = _get_uid(req)
    _require_parent(uid)
    return HTMLResponse(content=_render_workspace_page(uid))


@router.get("/system/audit-dashboard", response_class=HTMLResponse)
def system_audit_dashboard(
    req: Request,
    embed: int = 0,
    single: int = 0,
    mode: str = "audited",
) -> HTMLResponse:
    """Phase 35-E.4 (9.5.2026): System tier audit dashboard.

    Marti's vize 33. dopis 8.5. večer + dnešní request 'koukat shora'.
    Visible jen pro rodiče (defense in depth — _require_parent + explicit
    is_marti_parent check uvnitř data endpointů).

    Cross-tenant view (Marti's korekce 9.5. 'audit musí jet nade vsim
    chronologicky').

    Phase 35-E.4 Variant A (9.5.2026 dopoledne): query param ?embed=1
    skipne header + back link (pro inline iframe render v ERP main pane).
    Tabs (Auditované/Všechny/Přehled) viditelné — combined view.

    Phase 35-E.4 Variant B (9.5.2026 odpoledne, Marti's korekce po smoke):
    + query param ?single=1 skipne i tabs bar — render JEN daný view
    (mode=audited|all|stats). Klasický Centrála pattern: 1 přehled = 1
    grid v main pane. Sidebar má 3 leaf uzly (Auditované / Všechny /
    Přehled), každý → samostatný single-view dashboard.
    """
    uid = _get_uid(req)
    _require_parent(uid)

    if mode not in ("audited", "all", "stats", "tabs"):
        mode = "audited"
    # Phase 35-E.4 fix 9.5. odpoledne: 'tabs' je Variant A UI signál (tabs
    # bar viditelný se 3 tlačítky), ale není validní backend mode pro
    # /audit-overview (ten zná jen audited/all/stats). Override na default
    # 'audited' pro initial fetch — frontend pak po klik na tab přepne.
    if mode == "tabs":
        mode = "audited"

    from core.database_core import get_core_session as _gcs_dash
    from modules.core.infrastructure.models_core import User

    cs = _gcs_dash()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "Audit dashboard je jen pro rodiče.")
    finally:
        cs.close()

    # Phase 35-E.4 Variant B (9.5.2026): explicit headers pro same-origin
    # iframe embed v ERP main pane. Caddy default je X-Frame-Options: DENY
    # (anti-clickjacking) — pro embed=1 mode override na SAMEORIGIN.
    # CSP frame-ancestors 'self' = modern alternative, oba pro compat.
    return HTMLResponse(
        content=_render_audit_dashboard_page(
            uid,
            embed=bool(embed),
            single=bool(single),
            initial_mode=mode,
        ),
        headers={
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": "frame-ancestors 'self'",
        },
    )


@router.get("/sw.js")
def erp_service_worker() -> Response:
    """Phase B+9+++ (6.5.2026): Service Worker pro PWA install.

    Served z /erp/sw.js (ne /static/erp/sw.js) aby scope = /erp/.
    Bez SW Chrome nabídne jen "Přidat na plochu" (bookmark) místo
    "Nainstalovat aplikaci" (standalone PWA bez chromu).

    Marti's spec: "A da se to udelat, aby ten Chrom nebyl videt..."
    """
    import os as _os
    from pathlib import Path as _Path
    sw_path = _Path(__file__).resolve().parents[3] / "apps" / "api" / "static" / "erp" / "sw.js"
    try:
        content = sw_path.read_text(encoding="utf-8")
    except Exception:
        content = "// SW file not found at " + str(sw_path)
    return Response(
        content=content,
        media_type="application/javascript",
        headers={
            # Service-Worker-Allowed lets SW claim broader scope. /erp/ stačí
            # pro naše use case, ale set this header for future flexibility.
            "Service-Worker-Allowed": "/erp/",
            # Bypass cache — SW updates musí být fresh (24h Chrome cache by
            # blokoval updates).
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/landing", response_class=HTMLResponse)
def erp_landing(req: Request) -> HTMLResponse:
    """Phase A landing zachovaný pod /erp/landing pro reference."""
    uid = _get_uid(req)
    _require_parent(uid)
    return HTMLResponse(content=_render_landing_page(uid))


@router.get("/jadro/{form_id}/{row_id}", response_class=HTMLResponse)
def jadro_render(
    form_id: int,
    row_id: int,
    req: Request,
    fragment: bool = False,
) -> HTMLResponse:
    """
    Read-only render jednoho Centrála jádra.

    Pipeline (z proposal sekce 3):
      1. Načti EC_FormDef.{form_id} → header + SQL_Select
      2. Načti EC_FormDefEdit + EC_FormDefEditProperty → komponenty
      3. Substituuj :ID = {row_id} v SQL_Select, execute → data
      4. Render HTML přes render_generator

    Phase B+2 (5.5.2026): query param ?fragment=1 vrací jen html_body
    (bez _render_full_page wrapperu) pro embed v 3-pane workspace.
    """
    uid = _get_uid(req)
    _require_parent(uid)
    logger.info(
        f"ERP | jadro render | user={uid} form_id={form_id} row_id={row_id} "
        f"fragment={fragment}"
    )

    # Phase 35-E.3.4: Tenant gate — non-EUROSOFT tenant = friendly empty.
    if not _is_eurosoft_active(uid):
        msg_html = (
            '<div class="erp-jadro-error">'
            '<strong>Jádro nedostupné v tomto tenantu</strong><br>'
            '<small>ERP zatím funguje jen pro tenant EUROSOFT. '
            'Pro přepnutí použij patičku.</small>'
            '</div>'
        )
        if fragment:
            return HTMLResponse(content=msg_html)
        return HTMLResponse(content=_render_error_page(
            title="Jádro nedostupné",
            msg="ERP zatím funguje jen pro tenant EUROSOFT. Phase 30+ migrace je v plánu."
        ), status_code=404)

    reader = CentralaReader()

    # 1. Form header
    form = reader.load_form_def(form_id)
    if not form:
        if fragment:
            return HTMLResponse(
                content=(
                    f'<div class="erp-jadro-error">'
                    f'<strong>Jádro #{form_id} nenalezeno</strong><br>'
                    f'<small>EC_FormDef.ID={form_id} v DB_EC neexistuje.</small>'
                    f'</div>'
                ),
                status_code=404,
            )
        return HTMLResponse(
            content=_render_error_page(
                title="Jádro nenalezeno",
                msg=f"EC_FormDef.ID={form_id} nenalezen v DB_EC.",
            ),
            status_code=404,
        )

    # 2. Komponenty + properties
    components = reader.load_form_components(form_id)

    # 3. Data row z SQL_Select
    data = reader.execute_form_data(form.sql_select, row_id) or {}

    # Phase A.5 (5.5.2026): enrich data o lookup display values
    # (FormList komponenty s LookupView/LookupField/LookupDisplay properties).
    data = reader.enrich_data_with_lookups(data, components)

    # 4. Render
    html_body = render_form(
        form_nazev=form.nazev,
        components=components,
        data=data,
        read_only=True,
        form_id=form_id,  # B+6.4 (5.5.2026): pro frontend lookup endpoint hook
        debug_info={
            "form_id": form_id,
            "row_id": row_id,
            "data_keys": list(data.keys()),
            "typ_names": TYP_NAMES,
            "sql_select": form.sql_select[:200] + "…" if len(form.sql_select) > 200 else form.sql_select,
        },
    )

    # Phase B+2: fragment mode → vrať jen html_body s X-Jadro-Title headerem
    if fragment:
        response = HTMLResponse(content=html_body)
        # X-Jadro-Title pro JS na workspace straně (název jádra do header lišty pane)
        # ASCII-only safe encoding aby HTTP header neselhal na UTF-8
        try:
            response.headers["X-Jadro-Title"] = form.nazev.encode("ascii", "replace").decode("ascii")
        except Exception:
            pass
        return response

    full_page = _render_full_page(
        title=f"{form.nazev} (#{form_id}/{row_id})",
        content=html_body,
        breadcrumb=[
            ("ERP", "/erp/"),
            (f"Jádro #{form_id}", None),
            (f"Řádek #{row_id}", None),
        ],
    )
    return HTMLResponse(content=full_page)


# ── JSON API endpointy (debug) ──────────────────────────────────────


@api_router.get("/health")
def health(req: Request) -> JSONResponse:
    """Health check + tenant info."""
    uid = _get_uid(req)
    _require_parent(uid)

    reader = CentralaReader()
    mcp_ok = reader._client is not None  # type: ignore[attr-defined]

    tid = _get_tenant_id(uid)
    return JSONResponse({
        "ok": True,
        "phase": "A",
        "mcp_klient_available": mcp_ok,
        "supported_typs": len(TYP_NAMES),
        "user_id": uid,
        "tenant_id": tid,
        "tenant_name": _get_tenant_name(tid),
        "erp_data_available": _is_eurosoft_active(uid),
    })


@api_router.get("/tenants")
def tenants_for_user(req: Request) -> JSONResponse:
    """Phase 35-E.3.2 (8.5.2026): list aktivních tenantů usera pro footer
    switcher v ERP UI. Reuse helper z auth.user_context.

    Returns: {ok, current_tenant_id, tenants: [{tenant_id, tenant_name,
    tenant_code, tenant_type, is_eurosoft}, ...]}
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_core import get_core_session
    from modules.auth.application.user_context import _list_user_tenants

    cs = get_core_session()
    try:
        tenants = _list_user_tenants(cs, uid)
    finally:
        cs.close()

    return JSONResponse({
        "ok": True,
        "current_tenant_id": _get_tenant_id(uid),
        "tenants": tenants,
    })


# ── Phase 35-E.4 (9.5.2026): System tier audit dashboard ─────────────
# Marti's vize 33. dopis 8.5. večer: System soudeček visible jen pro
# rodiče (is_marti_parent=True), napříč všemi tenanty. Drží Phase 16-B
# doctrine "důvěra je v subjekt, ne v scope" + 33. dopis ACL "adekvátní
# oprávnění, aby se nikdo mimo rodičů nedostal do hlavy do deníčku".
#
# Hardcoded System tree (MVP), `master.menu_node` přijde v Phase 30+ DDL.
# 3 sub-uzly: 📚 Auditované / 📋 Všechny / 📊 Přehled.

_SYSTEM_TREE_NODES = [
    {
        "id": "system",
        "type": "folder",
        "label": "📦 SYSTEM",
        "is_system": True,
        "children": [
            {
                "id": "system.audit",
                "type": "folder",
                "label": "📁 Audit konverzaci",
                "children": [
                    # Phase 35-E.4 Marti's korekce 9.5. (po dnešním smoke):
                    # "Pro každý soudeček jiný grid + zachovat záložkový
                    # přehled jako Varianta A". Klasický Centrála pattern —
                    # každý leaf uzel = vlastní view v main pane.
                    #
                    # Variant A — záložkový přehled (3 tabs combined):
                    {
                        "id": "system.audit.tabs",
                        "type": "view",
                        "label": "🗂️ Záložkový přehled",
                        "view_type": "audit_overview",
                        "view_mode": "tabs",
                    },
                    # Variant B — každý view jako samostatný grid:
                    {
                        "id": "system.audit.audited",
                        "type": "view",
                        "label": "📚 Auditované konverzace",
                        "view_type": "audit_overview",
                        "view_mode": "audited",
                        "single": True,
                    },
                    {
                        "id": "system.audit.all",
                        "type": "view",
                        "label": "📋 Všechny konverzace",
                        "view_type": "audit_overview",
                        "view_mode": "all",
                        "single": True,
                    },
                    {
                        "id": "system.audit.stats",
                        "type": "view",
                        "label": "📊 Přehled auditu",
                        "view_type": "audit_overview",
                        "view_mode": "stats",
                        "single": True,
                    },
                ],
            },
        ],
    },
]


@api_router.get("/system/audit-overview")
def system_audit_overview(
    req: Request,
    mode: str = "audited",
    status: str | None = None,
    scope: str | None = None,
    tenant_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
) -> JSONResponse:
    """Phase 35-E.4 (9.5.2026): System tier audit dashboard data.

    mode:
      - 'audited' — jen audit_status='audited' (čistá tabulka pro Marti's
        Q3 A "audit má váhu uzavření")
      - 'all' — všechny statuses mix (pending / in_progress / audited /
        excluded) s status sloupcem
      - 'stats' — agregace pro widgets (per-status counts, per-tenant,
        recent 7 days)

    Cross-tenant pro rodiče (is_marti_parent=True) — Marti's korekce 9.5.
    "audit musí jet nade vsim chronologicky".
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func, or_
    from modules.core.infrastructure.models_data import Conversation, Message
    from modules.core.infrastructure.models_core import Persona, Tenant, User

    if mode not in ("audited", "all", "stats"):
        raise HTTPException(400, "mode musí být 'audited', 'all' nebo 'stats'")

    from core.database_core import get_core_session as _gcs_audov
    from core.database_data import get_data_session as _gds_audov

    # Parent check (defense in depth — _require_parent uz checkuje, ale
    # pro System tier explicit double-check)
    cs = _gcs_audov()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "System tier dashboard je jen pro rodiče.")

        # Persona name lookup map (audited_by_persona_id → name)
        persona_rows = cs.query(Persona).all()
        persona_names = {p.id: p.name for p in persona_rows}

        # Tenant name lookup
        tenant_rows = cs.query(Tenant).all()
        tenant_names = {t.id: t.tenant_name for t in tenant_rows}
    finally:
        cs.close()

    # Date filtering
    parse_date = lambda s: (
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        if s else None
    )
    try:
        d_from = parse_date(date_from)
        d_to = parse_date(date_to)
    except Exception:
        raise HTTPException(400, "date_from/date_to must be ISO 8601")

    ds = _gds_audov()
    try:
        # Cross-tenant base filter (rodič vidí napříč)
        base_filters = [
            Conversation.is_deleted == False,  # noqa: E712
            Conversation.conversation_type == "ai",
        ]
        if tenant_id is not None:
            base_filters.append(Conversation.tenant_id == tenant_id)

        # ── mode='stats' → agregace ───────────────────────────────
        if mode == "stats":
            # Per-status counts
            status_counts = dict(
                ds.query(
                    Conversation.audit_status,
                    func.count(Conversation.id),
                )
                .filter(*base_filters)
                .group_by(Conversation.audit_status)
                .all()
            )
            # Per-tenant audited counts
            per_tenant_rows = (
                ds.query(
                    Conversation.tenant_id,
                    func.count(Conversation.id),
                )
                .filter(
                    *base_filters,
                    Conversation.audit_status == "audited",
                )
                .group_by(Conversation.tenant_id)
                .all()
            )
            per_tenant = [
                {
                    "tenant_id": tid,
                    "tenant_name": tenant_names.get(tid, f"#{tid}" if tid else "—"),
                    "count": int(cnt),
                }
                for tid, cnt in per_tenant_rows
            ]

            # Per-scope (z audit_notes JSON)
            audited_with_notes = (
                ds.query(Conversation)
                .filter(
                    *base_filters,
                    Conversation.audit_status == "audited",
                    Conversation.audit_notes.isnot(None),
                )
                .all()
            )
            per_scope = {"general": 0, "srdce": 0, "unknown": 0}
            for c in audited_with_notes:
                sc = (c.audit_notes or {}).get("scope", "unknown")
                per_scope[sc if sc in per_scope else "unknown"] += 1

            # Recent 7 days timeline
            now = datetime.now(timezone.utc)
            timeline = []
            for d in range(6, -1, -1):
                day_start = (now - timedelta(days=d)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)
                cnt = (
                    ds.query(func.count(Conversation.id))
                    .filter(
                        *base_filters,
                        Conversation.audit_status == "audited",
                        Conversation.audited_at >= day_start,
                        Conversation.audited_at < day_end,
                    )
                    .scalar()
                ) or 0
                timeline.append({
                    "date": day_start.date().isoformat(),
                    "count": int(cnt),
                })

            # ── Phase 35-E.4 Variant B (9.5.2026 odpoledne): per-persona ×
            # per-month grid rows pro AG Grid v main pane. Marti's spec
            # "detailni audit toho co se delo" — granular breakdown.
            #
            # Persona attribution:
            #  - audited rows → audited_by_persona_id (kdo auditoval)
            #  - non-audited rows → active_agent_id (kdo by auditoval / kdo
            #    persona vlastní konverzaci) — fallback pokud NULL = "—"
            # Period:
            #  - audited rows → audited_at month
            #  - non-audited rows → last_message_at month
            from sqlalchemy import case, cast, String
            from collections import defaultdict

            # Načíst ALL conversations (cross-tenant) do paměti — paginate
            # nedáváme, protože GROUP BY s month + persona je už malé.
            agg_rows = (
                ds.query(
                    Conversation.audit_status,
                    Conversation.audited_by_persona_id,
                    Conversation.active_agent_id,
                    Conversation.audited_at,
                    Conversation.last_message_at,
                )
                .filter(*base_filters)
                .all()
            )

            # In-Python aggregation (jednodušší než SQL CASE pro period
            # podle audit_status — DB-agnostic, malý dataset).
            buckets = defaultdict(lambda: {
                "pending": 0, "in_progress": 0,
                "audited": 0, "excluded": 0, "total": 0,
            })
            for st, audited_pid, active_pid, audited_at, last_msg_at in agg_rows:
                # Persona attribution
                if st == "audited" and audited_pid:
                    pid = audited_pid
                else:
                    pid = active_pid
                # Period (yyyy-mm) attribution
                if st == "audited" and audited_at:
                    period = audited_at.strftime("%Y-%m")
                elif last_msg_at:
                    period = last_msg_at.strftime("%Y-%m")
                else:
                    period = "—"

                key = (pid, period)
                bucket = buckets[key]
                bucket["total"] += 1
                if st in ("pending", "in_progress", "audited", "excluded"):
                    bucket[st] += 1

            stats_rows = []
            for (pid, period), counts in buckets.items():
                stats_rows.append({
                    "persona_id": pid,
                    "persona_name": persona_names.get(pid, "—") if pid else "—",
                    "period": period,
                    "pending": counts["pending"],
                    "in_progress": counts["in_progress"],
                    "audited": counts["audited"],
                    "excluded": counts["excluded"],
                    "total": counts["total"],
                })
            # Order: persona_name asc, period desc (nejnovější nahoře per persona)
            stats_rows.sort(key=lambda r: (r["persona_name"], -int(r["period"].replace("-", "")) if r["period"] != "—" else 0))

            return JSONResponse({
                "ok": True,
                "mode": "stats",
                "status_counts": {
                    k or "null": int(v) for k, v in status_counts.items()
                },
                "per_tenant_audited": per_tenant,
                "per_scope_audited": per_scope,
                "timeline_7d": timeline,
                "total_conversations": sum(int(v) for v in status_counts.values()),
                # Variant B grid rows (per-persona × per-month):
                "rows": stats_rows,
                "shown": len(stats_rows),
                "limit": len(stats_rows),
            })

        # ── mode='audited' / 'all' → tabulka ──────────────────────
        q = ds.query(Conversation).filter(*base_filters)

        if mode == "audited":
            q = q.filter(Conversation.audit_status == "audited")
            # Order: audited_at DESC (nejnovější audit první)
            q = q.order_by(Conversation.audited_at.desc().nullslast())
        else:  # mode == 'all'
            if status:
                q = q.filter(Conversation.audit_status == status)
            # Order: last_message_at DESC
            q = q.order_by(Conversation.last_message_at.desc().nullslast())

        # Filter by scope (jen pro audit_notes-bearing rows)
        if scope:
            q = q.filter(
                Conversation.audit_notes.op("->>")("scope") == scope
            )

        # Date range
        if d_from:
            if mode == "audited":
                q = q.filter(Conversation.audited_at >= d_from)
            else:
                q = q.filter(Conversation.last_message_at >= d_from)
        if d_to:
            if mode == "audited":
                q = q.filter(Conversation.audited_at <= d_to)
            else:
                q = q.filter(Conversation.last_message_at <= d_to)

        rows = q.limit(max(1, min(limit, 1000))).all()

        items = []
        for c in rows:
            notes = c.audit_notes or {}
            extracted_ids = notes.get("extracted_thought_ids", []) or []
            items.append({
                "id": c.id,
                "title": c.title or f"#{c.id}",
                "old_title": notes.get("old_title"),
                "audit_status": c.audit_status,
                "audited_at": (
                    c.audited_at.isoformat()
                    if c.audited_at else None
                ),
                "audited_by_persona_id": c.audited_by_persona_id,
                "audited_by_persona_name": (
                    persona_names.get(c.audited_by_persona_id)
                    if c.audited_by_persona_id else None
                ),
                "scope": notes.get("scope"),
                "summary": notes.get("summary"),
                "tenant_id": c.tenant_id,
                "tenant_name": tenant_names.get(c.tenant_id, "—") if c.tenant_id else "—",
                "project_id": c.project_id,
                "lifecycle_state": c.lifecycle_state,
                "thought_count": len(extracted_ids),
                "extracted_thought_ids": extracted_ids,
                "last_message_at": (
                    c.last_message_at.isoformat()
                    if c.last_message_at else None
                ),
                "created_at": (
                    c.created_at.isoformat()
                    if c.created_at else None
                ),
            })
    finally:
        ds.close()

    return JSONResponse({
        "ok": True,
        "mode": mode,
        "filters": {
            "status": status,
            "scope": scope,
            "tenant_id": tenant_id,
            "date_from": date_from,
            "date_to": date_to,
        },
        "shown": len(items),
        "limit": limit,
        "conversations": items,
    })


@api_router.get("/system/tree")
def system_tree(req: Request) -> JSONResponse:
    """Phase 35-E.4 (9.5.2026): System tier tree pro rodiče.

    Vrací hardcoded System soudeček s 3 sub-uzly. Visible jen pro
    is_marti_parent=True (defense in depth — _require_parent + explicit
    parent check).

    Future: nahradí se za query nad master.menu_node (Phase 30+).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_core import get_core_session as _gcs_st
    from modules.core.infrastructure.models_core import User

    cs = _gcs_st()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "System tier je jen pro rodiče.")
    finally:
        cs.close()

    return JSONResponse({
        "ok": True,
        "tree": _SYSTEM_TREE_NODES,
    })


# ── Phase B (5.5.2026): Tree + Přehled JSON endpoints ────────────────


@api_router.get("/strom")
def strom_json(req: Request) -> JSONResponse:
    """JSON tree z EC_CentralaMenu (Phase B nástřel).

    Phase 35-E.3.4: Tenant gate — non-EUROSOFT tenant = prázdný strom
    pro klasický Centrála tree.

    Phase 35-E.4 (9.5.2026): pro rodiče (is_marti_parent=True) přidá
    NAVÍC top-level System soudeček napříč VŠEMI tenanty (visible
    v EUROSOFT, STRATEGIE, Osobní…). Drží 33. dopis 8.5. večer ACL
    doctrine — System je meta-vrstva, non-parent users ho nevidí.
    """
    uid = _get_uid(req)
    _require_parent(uid)

    # Klasický Centrála tree z DB_EC (jen v EUROSOFT tenant)
    tree: list = []
    if _is_eurosoft_active(uid):
        reader = CentralaReader()
        tree = reader.load_menu_tree()

    # Phase 35-E.4: System soudeček navíc nad existing tree pro rodiče.
    # Cross-tenant — System je meta-vrstva, neváže se na EUROSOFT scope.
    is_parent = False
    try:
        from core.database_core import get_core_session as _gcs_strom
        from modules.core.infrastructure.models_core import User
        cs = _gcs_strom()
        try:
            u = cs.query(User).filter_by(id=uid).first()
            is_parent = bool(u and getattr(u, "is_marti_parent", False))
        finally:
            cs.close()
    except Exception:
        pass

    if is_parent:
        # Hardcoded System tree (MVP). Phase 30+ migration → master.menu_node.
        # Schema kompatibilní s Centrála tree (id, label, icon, children…)
        system_root = {
            "id": "system",
            "cislo": -1,  # negativní ID = virtuální (ne v DB)
            "is_system": True,
            "is_folder": True,
            "label": "📦 SYSTEM",
            "nazev": "📦 SYSTEM",
            "children": [
                # Phase 35-E.4 Marti's korekce 9.5. (po smoke):
                # "Pro každý soudeček jiný grid + zachovat záložkový
                # přehled jako Varianta A". Záložkový PRVNÍ — kombinovaný
                # tabbed view se 3 panely. Pak 3 samostatné gridy.
                {
                    "id": "system.audit.tabs",
                    "cislo": -100,
                    "is_system": True,
                    "is_folder": False,
                    "label": "🗂️ Záložkový přehled",
                    "nazev": "🗂️ Záložkový přehled",
                    "system_view": "audit_overview",
                    "system_view_mode": "tabs",
                },
                {
                    "id": "system.audit.audited",
                    "cislo": -101,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📚 Auditované konverzace",
                    "nazev": "📚 Auditované konverzace",
                    "system_view": "audit_overview",
                    "system_view_mode": "audited",
                },
                {
                    "id": "system.audit.all",
                    "cislo": -102,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📋 Všechny konverzace",
                    "nazev": "📋 Všechny konverzace",
                    "system_view": "audit_overview",
                    "system_view_mode": "all",
                },
                {
                    "id": "system.audit.stats",
                    "cislo": -103,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📊 Přehled auditu",
                    "nazev": "📊 Přehled auditu",
                    "system_view": "audit_overview",
                    "system_view_mode": "stats",
                },
            ],
        }
        # Prepend — System soudeček je vždy na top
        tree = [system_root] + (tree or [])

    return JSONResponse({
        "ok": True,
        "tree": tree,
        "root_count": len(tree),
        "is_parent": is_parent,
    })


_PREHLED_DEFAULT_LIMIT = 1000   # když přehled nemá MaxRecords ani user override
_PREHLED_HARD_CAP = 100_000     # absolutní strop "Vše" (B+8 server-side row model = lift)


@api_router.get("/prehled/{cislo}")
def prehled_data_json(
    cislo: int,
    req: Request,
    limit: int | None = None,
) -> JSONResponse:
    """JSON data z přehledu Cislo=N.

    Phase B+4.4 (5.5.2026): limit precedence —
      1. Query param ?limit=N (user override, capped na _PREHLED_HARD_CAP)
      2. EC_DELPHI_TabObecnyPrehled.MaxRecords (per-přehled native limit)
      3. _PREHLED_DEFAULT_LIMIT (1000)

    Phase 35-E.3.4: Tenant gate — non-EUROSOFT tenant = 404 (přehled není
    dostupný, ERP zatím funguje jen pro EUROSOFT).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    if not _is_eurosoft_active(uid):
        raise HTTPException(404, "Přehled není dostupný v tomto tenantu (pouze EUROSOFT).")

    reader = CentralaReader()
    meta = reader.load_prehled_meta(cislo)
    if not meta:
        raise HTTPException(404, f"EC_DELPHI_TabObecnyPrehled Cislo={cislo} nenalezen")

    # B+4.4: resolve effective limit
    if limit is not None and limit > 0:
        effective_limit = min(limit, _PREHLED_HARD_CAP)
    elif meta.get("max_records"):
        effective_limit = min(meta["max_records"], _PREHLED_HARD_CAP)
    else:
        effective_limit = _PREHLED_DEFAULT_LIMIT

    data = reader.execute_prehled_data(meta, limit=effective_limit)

    return JSONResponse({
        "ok": True,
        "cislo": cislo,
        "nazev": meta["nazev"],
        "id_edit": meta["id_edit"],
        "target_table": data.get("target_table"),
        "columns": data["columns"],
        "rows": data["rows"],
        "total": data["total"],
        "has_more": data.get("has_more", False),
        "warning": data.get("warning"),
        # B+4.4: client-side limit awareness
        "applied_limit": effective_limit,
        "max_records": meta.get("max_records"),  # native Centrála 1 hint
        "hard_cap": _PREHLED_HARD_CAP,
    })


# ── Phase B+5.1 (5.5.2026): Grid layout persistence ────────────────────


class GridLayoutCreate(BaseModel):
    """POST body — vytvoření nové sestavy."""
    name: str = Field(..., min_length=1, max_length=80)
    layout_json: dict
    scope: str = Field(default="user", pattern="^(user|shared)$")
    description: str | None = None
    is_default: bool = False


class GridLayoutUpdate(BaseModel):
    """PUT body — částečná aktualizace."""
    name: str | None = Field(default=None, min_length=1, max_length=80)
    layout_json: dict | None = None
    description: str | None = None
    is_default: bool | None = None


@api_router.get("/grid-layout/{prehled_cislo}/list")
def grid_layout_list(prehled_cislo: int, req: Request) -> JSONResponse:
    """List dostupných sestav (shared + personal pro current user) + effective default."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        result = grid_layout_service.list_layouts(prehled_cislo, uid)
        return JSONResponse({"ok": True, **result})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.get("/grid-layout/item/{layout_id}")
def grid_layout_get(layout_id: int, req: Request) -> JSONResponse:
    """Vrátí detail jedné sestavy podle ID."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        layout = grid_layout_service.get_layout(layout_id, uid)
        if layout is None:
            raise HTTPException(404, f"Sestava id={layout_id} neexistuje.")
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(403, str(e))


@api_router.post("/grid-layout/{prehled_cislo}")
def grid_layout_create(
    prehled_cislo: int,
    body: GridLayoutCreate,
    req: Request,
) -> JSONResponse:
    """Vytvoří novou sestavu (scope='user' nebo 'shared')."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        layout = grid_layout_service.create_layout(
            prehled_cislo=prehled_cislo,
            user_id=uid,
            name=body.name,
            layout_json=body.layout_json,
            scope=body.scope,
            description=body.description,
            is_default=body.is_default,
        )
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.put("/grid-layout/item/{layout_id}")
def grid_layout_update(
    layout_id: int,
    body: GridLayoutUpdate,
    req: Request,
) -> JSONResponse:
    """Částečná aktualizace existující sestavy."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        layout = grid_layout_service.update_layout(
            layout_id, uid,
            name=body.name,
            description=body.description,
            layout_json=body.layout_json,
            is_default=body.is_default,
        )
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.post("/grid-layout/item/{layout_id}/set-default")
def grid_layout_set_default(layout_id: int, req: Request) -> JSONResponse:
    """Označí sestavu jako default v jejím scope (auto-odznačí starý default)."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        layout = grid_layout_service.set_default(layout_id, uid)
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/grid-layout/item/{layout_id}")
def grid_layout_delete(layout_id: int, req: Request) -> JSONResponse:
    """Smaže sestavu."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        deleted = grid_layout_service.delete_layout(layout_id, uid)
        if not deleted:
            raise HTTPException(404, f"Sestava id={layout_id} neexistuje.")
        return JSONResponse({"ok": True, "deleted": True})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(403, str(e))


# ── Phase A debug endpoint ─────────────────────────────────────────────


@api_router.get("/jadro/{form_id}/components")
def jadro_components_json(form_id: int, req: Request) -> JSONResponse:
    """JSON dump komponent jádra (debug, Phase A)."""
    uid = _get_uid(req)
    _require_parent(uid)

    if not _is_eurosoft_active(uid):
        raise HTTPException(404, "Jádro není dostupné v tomto tenantu (pouze EUROSOFT).")

    reader = CentralaReader()
    form = reader.load_form_def(form_id)
    if not form:
        raise HTTPException(404, f"FormDef ID={form_id} nenalezen")

    components = reader.load_form_components(form_id)

    return JSONResponse({
        "ok": True,
        "form_id": form_id,
        "form_nazev": form.nazev,
        "sql_select": form.sql_select,
        "components_count": len(components),
        "components": [
            {
                "id": c.id,
                "typ": c.typ,
                "typ_name": TYP_NAMES.get(c.typ, "?"),
                "c_caption": c.c_caption,
                "c_field_name": c.c_field_name,
                "c_parent": c.c_parent,
                "smazana": c.smazana,
                "properties_count": len(c.properties),
                "properties_keys": list(c.properties.keys()),
            }
            for c in components
        ],
    })


@api_router.get("/jadro/{form_id}/{row_id}/data")
def jadro_data_json(form_id: int, row_id: int, req: Request) -> JSONResponse:
    """
    Phase B+6.6b (6.5.2026): JSON metadata jádra pro frontend ErpForm
    orchestrator. Vrací form definition + komponenty + data row +
    lookup-enriched display values.

    Klient (apps/api/static/erp/components/form.js) si z toho postaví
    DOM přes UI Kit komponenty (ErpInput / ErpCheckbox / ErpFormList /
    ErpFormSection / ErpButton). Server-side render_form() pro
    standalone /erp/jadro/{id}/{row} zůstává beze změny.

    Returns: {
      ok: bool,
      form_id: int,
      row_id: int,
      form: { id, nazev, sql_select, ... },
      components: [{id, typ, c_field_name, c_caption, c_parent,
                    c_mask, c_top, c_left, c_height, c_width,
                    properties: {...}}, ...],
      data: { field_name: value, _lookup_{field}: display, ... },
      typ_names: { 1: "Label", 2: "Edit", ... },
      debug: { ... },
    }
    """
    uid = _get_uid(req)
    _require_parent(uid)
    logger.info(
        f"ERP | jadro data JSON | user={uid} form_id={form_id} row_id={row_id}"
    )

    if not _is_eurosoft_active(uid):
        raise HTTPException(404, "Jádro není dostupné v tomto tenantu (pouze EUROSOFT).")

    reader = CentralaReader()
    form = reader.load_form_def(form_id)
    if not form:
        raise HTTPException(404, f"FormDef ID={form_id} nenalezen")

    components = reader.load_form_components(form_id)
    data = reader.execute_form_data(form.sql_select, row_id) or {}
    data = reader.enrich_data_with_lookups(data, components)

    # Serializovat komponenty
    comps_json = []
    for c in components:
        # Phase A+1 (7.5.2026): typed LayoutInfo dict do response.
        # Frontend respektuje top/left/width/height/align/anchors při render.
        layout_dict = {
            "top": c.layout.top,
            "left": c.layout.left,
            "width": c.layout.width,
            "height": c.layout.height,
            "align": c.layout.align,
            "anchors": list(c.layout.anchors),
            "margins": [
                c.layout.margins_left,
                c.layout.margins_top,
                c.layout.margins_right,
                c.layout.margins_bottom,
            ],
            "align_with_margins": c.layout.align_with_margins,
        }
        comps_json.append({
            "id": c.id,
            "typ": c.typ,
            "typ_name": TYP_NAMES.get(c.typ, "?"),
            "c_field_name": c.c_field_name or "",
            "c_caption": c.c_caption or "",
            "c_parent": c.c_parent or "",
            "c_mask": c.c_mask or "",
            "c_top": c.c_top or 0,
            "c_left": c.c_left or 0,
            "c_height": c.c_height or 20,
            "c_width": c.c_width or 100,
            "smazana": c.smazana,
            "properties": c.properties or {},
            "layout": layout_dict,            # Phase A+1: typed layout
        })

    # Serializovat data (Date/Decimal coerce na string pro JSON safety)
    data_json = {}
    for k, v in (data or {}).items():
        if v is None:
            data_json[k] = None
        elif isinstance(v, (str, int, float, bool)):
            data_json[k] = v
        else:
            data_json[k] = str(v)

    return JSONResponse({
        "ok": True,
        "form_id": form_id,
        "row_id": row_id,
        "form": {
            "id": form.id,
            "nazev": form.nazev,
            "sql_select": form.sql_select,
        },
        "components": comps_json,
        "data": data_json,
        "typ_names": TYP_NAMES,
        "debug": {
            "form_id": form_id,
            "row_id": row_id,
            "components_count": len(comps_json),
            "data_keys": list(data_json.keys()),
            "sql_select_preview": (
                form.sql_select[:200] + "…"
                if len(form.sql_select) > 200 else form.sql_select
            ),
        },
    })


@api_router.get("/jadro/{form_id}/lookup/{field_name}")
def jadro_lookup_options(form_id: int, field_name: str, req: Request) -> JSONResponse:
    """
    Phase B+6.4 (5.5.2026): list lookup options pro FormList/Combobox
    field v jádru. Frontend ErpFormList ho lazy-loaduje při prvním
    open dropdown panelu.

    Returns: {"ok": true, "items": [{"value": ..., "label": "..."}, ...]}

    Read-only Phase A; výběr se persistuje až s OK tlačítkem (Phase C).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    if not _is_eurosoft_active(uid):
        raise HTTPException(404, "Lookup není dostupný v tomto tenantu (pouze EUROSOFT).")

    reader = CentralaReader()
    form = reader.load_form_def(form_id)
    if not form:
        raise HTTPException(404, f"FormDef ID={form_id} nenalezen")

    try:
        items = reader.list_lookup_options(form_id, field_name)
    except Exception as e:
        logger.exception(
            f"jadro_lookup_options: form_id={form_id} field={field_name!r} chyba"
        )
        raise HTTPException(500, f"Lookup options chyba: {e}")

    return JSONResponse({
        "ok": True,
        "form_id": form_id,
        "field_name": field_name,
        "items": items,
        "count": len(items),
    })


# ── Phase B+8.1 (6.5.2026): user state endpoints ────────────────────


class _CisloBody(BaseModel):
    cislo: int
    label: str | None = None
    item_id: str | None = None


class _ReorderBody(BaseModel):
    cislos: list[int]


class _TreeOrderBody(BaseModel):
    group_key: str
    order: list[str]


# TABS

@api_router.get("/tabs")
def user_tabs_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, **user_state_svc.list_tabs(uid, tid)})


@api_router.post("/tabs")
def user_tabs_open(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    try:
        tab = user_state_svc.open_tab(
            user_id=uid, tenant_id=tid,
            cislo_def=body.cislo,
            label=body.label or f"Přehled #{body.cislo}",
            item_id=body.item_id,
        )
        return JSONResponse({"ok": True, "tab": tab})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/tabs/{cislo_def}")
def user_tabs_close(cislo_def: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    removed = user_state_svc.close_tab(uid, tid, cislo_def)
    return JSONResponse({"ok": True, "removed": removed})


@api_router.post("/tabs/{cislo_def}/active")
def user_tabs_set_active(cislo_def: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    found = user_state_svc.set_active_tab(uid, tid, cislo_def)
    return JSONResponse({"ok": True, "found": found})


@api_router.post("/tabs/reorder")
def user_tabs_reorder(body: _ReorderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    updated = user_state_svc.reorder_tabs(uid, tid, body.cislos)
    return JSONResponse({"ok": True, "updated": updated})


# FAVORITES

@api_router.get("/favorites")
def user_favorites_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "favorites": user_state_svc.list_favorites(uid, tid)})


@api_router.post("/favorites")
def user_favorites_add(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    try:
        fav = user_state_svc.add_favorite(uid, tid, body.cislo)
        return JSONResponse({"ok": True, "favorite": fav})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/favorites/{cislo_def}")
def user_favorites_remove(cislo_def: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    removed = user_state_svc.remove_favorite(uid, tid, cislo_def)
    return JSONResponse({"ok": True, "removed": removed})


@api_router.post("/favorites/reorder")
def user_favorites_reorder(body: _ReorderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    updated = user_state_svc.reorder_favorites(uid, tid, body.cislos)
    return JSONResponse({"ok": True, "updated": updated})


@api_router.delete("/favorites")
def user_favorites_clear(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    deleted = user_state_svc.clear_favorites(uid, tid)
    return JSONResponse({"ok": True, "deleted": deleted})


# RECENT (MRU)

@api_router.get("/recent")
def user_recent_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "recent": user_state_svc.list_recent(uid, tid)})


@api_router.post("/recent")
def user_recent_track(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    try:
        rec = user_state_svc.track_recent(
            uid, tid, body.cislo, body.label
        )
        return JSONResponse({"ok": True, "recent": rec})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/recent")
def user_recent_clear(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    deleted = user_state_svc.clear_recent(uid, tid)
    return JSONResponse({"ok": True, "deleted": deleted})


# TREE ORDER (D&D persistence per skupina)

@api_router.get("/tree-order")
def user_tree_order_get(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "order": user_state_svc.get_tree_order(uid, tid)})


@api_router.put("/tree-order")
def user_tree_order_save(body: _TreeOrderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    try:
        user_state_svc.save_tree_order(uid, tid, body.group_key, body.order)
        return JSONResponse({"ok": True})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/tree-order")
def user_tree_order_reset(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    deleted = user_state_svc.reset_tree_order(uid, tid)
    return JSONResponse({"ok": True, "deleted": deleted})


# ── HTML page builders ──────────────────────────────────────────────


def _render_full_page(
    title: str,
    content: str,
    breadcrumb: list[tuple[str, str | None]],
    user_id: int | None = None,
) -> str:
    """Wrap content do full HTML page — STRATEGIE BLACK theme.

    user_id (Marti's drobnost 6.5.2026): pokud given, footer zobrazí
    "STRATEGIE ERP · <short_name> · <tenant_name>" místo statického hash.
    """
    bc_html = []
    for label, url in breadcrumb:
        if url:
            bc_html.append(f'<a href="{url}" class="erp-bc-link">{html.escape(label)}</a>')
        else:
            bc_html.append(f'<span class="erp-bc-current">{html.escape(label)}</span>')
    bc_str = ' <span class="erp-bc-sep">/</span> '.join(bc_html)

    # Marti's drobnost 6.5.2026: footer s user.short_name + tenant.tenant_name
    user_name_html = ""
    tenant_name_html = ""
    if user_id is not None:
        try:
            from core.database_core import get_core_session
            from modules.core.infrastructure.models_core import User, Tenant
            cs = get_core_session()
            try:
                u = cs.query(User).filter(User.id == user_id).one_or_none()
                if u:
                    name = (
                        u.short_name
                        or (getattr(u, "first_name", None))
                        or (u.email if hasattr(u, "email") else None)
                        or f"User #{user_id}"
                    )
                    user_name_html = (
                        f' · <span class="erp-footer-user">'
                        f'{html.escape(str(name))}</span>'
                    )
                    tid = getattr(u, "last_active_tenant_id", None)
                    if tid:
                        t = cs.query(Tenant).filter(Tenant.id == tid).one_or_none()
                        if t and t.tenant_name:
                            # Phase 35-E.3.2 (8.5.2026): clickable button +
                            # popover dropdown. JS si fetchne /api/v1/erp/tenants
                            # a vyrenderuje dropdown nad footer.
                            tenant_name_html = (
                                f' · <button type="button" class="erp-footer-tenant-btn" '
                                f'id="erpFooterTenantBtn" data-tenant-id="{tid}" '
                                f'title="Přepnout tenant">'
                                f'<span class="erp-footer-tenant">'
                                f'{html.escape(t.tenant_name)}</span>'
                                f'<span class="erp-footer-tenant-caret">▴</span>'
                                f'</button>'
                                f'<div class="erp-footer-tenant-popover" '
                                f'id="erpFooterTenantPopover" hidden></div>'
                            )
            finally:
                cs.close()
        except Exception:
            pass  # silent fallback — footer just shows base text

    return f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <!-- B+10+++ (6.5.2026 Marti's drobnost): title format zjednodušen na
       "STRATEGIE | <přehled>" (bez "ERP"). Default při pageload je jen
       "STRATEGIE", JS přidá " | <tab.label>" při switchTab. -->
  <title>STRATEGIE</title>

  <!-- B+9+++ (6.5.2026): PWA install — Add to Home Screen na mobilu
       → standalone mode bez URL bar / browser chrome.
       Marti's spec: "A da se to udelat, aby ten Chrom nebyl videt..." -->
  <link rel="manifest" href="/static/erp/manifest.json">
  <meta name="theme-color" content="#0e0f11">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="STRATEGIE">
  <meta name="mobile-web-app-capable" content="yes">
  <link rel="apple-touch-icon" href="/static/erp/icon-192.png">
  <link rel="apple-touch-icon" sizes="192x192" href="/static/erp/icon-192.png">
  <link rel="apple-touch-icon" sizes="512x512" href="/static/erp/icon-512.png">

  <!-- Service Worker registration — Chrome's installability criteria.
       Bez SW dostane user jen "Přidat na plochu" (bookmark s URL bar).
       S SW → "Nainstalovat aplikaci" (standalone PWA bez chromu). -->
  <script>
    if ("serviceWorker" in navigator) {{
      window.addEventListener("load", () => {{
        navigator.serviceWorker
          .register("/erp/sw.js", {{ scope: "/erp/" }})
          .then(reg => console.log("[SW] registered, scope:", reg.scope))
          .catch(err => console.warn("[SW] register failed:", err));
      }});
    }}
  </script>

  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%25' stop-color='%234f8ef7'/><stop offset='100%25' stop-color='%237c5cfc'/></linearGradient></defs><rect width='64' height='64' rx='12' fill='%2316181c'/><text x='32' y='49' font-family='Montserrat,Arial,sans-serif' font-size='52' font-weight='800' fill='url(%23g)' text-anchor='middle'>S</text></svg>">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #0e0f11; --surface: #1c1e23; --surface2: #252830;
      --border: #3a3d44; --border-strong: #4a4e57;
      --accent: #4f8ef7; --accent2: #7c5cfc;
      --text: #f0f1f5; --text-muted: #b0b3bc;
      --muted: #8a8d96; --error: #f87171;
    }}
    html, body {{ height: 100%; background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 15px; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ opacity: .85; }}

    /* ── Header ── */
    /* B+2.4 (5.5.2026): logo doleva — žádné centering, full viewport width */
    .erp-header {{
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: 12px 16px; position: sticky; top: 0; z-index: 10;
    }}
    .erp-header-inner {{
      max-width: none; margin: 0;
      display: flex; align-items: center; justify-content: space-between; gap: 16px;
    }}
    /* B+9 (6.5.2026): UI zoom toggle (3-segment A−/A/A+) */
    .erp-zoom-toggle {{
      display: inline-flex;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 5px;
      overflow: hidden;
      flex-shrink: 0;
    }}
    .erp-zoom-toggle button {{
      padding: 3px 8px;
      background: transparent;
      border: none;
      border-right: 1px solid var(--border);
      color: var(--text-muted);
      font-family: 'DM Sans', sans-serif;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.12s;
      min-width: 26px;
    }}
    .erp-zoom-toggle button:last-child {{ border-right: none; }}
    .erp-zoom-toggle button:hover:not(.active) {{
      background: var(--surface2);
      color: var(--text);
    }}
    .erp-zoom-toggle button.active {{
      background: var(--accent);
      color: white;
    }}
    /* Body zoom — Chrome/Edge/Safari respect zoom property.
       Firefox fallback: transform-based (rare browser pro Marti).
       Marti's spec ±25%. */
    /* B+9 (6.5.2026): html background + body dimension calc — bez nich
       zoom 0.75 nechá 25% pravé/dolní strany prázdné (viewport bg).
       Marti's UX feedback: "doresit roztazeni na celou aplikaci".
       Trick: body logical width = 100vw / zoomFactor → render × zoomFactor
       = 100vw (full viewport). */
    html {{
      background: var(--bg);
    }}
    body.erp-zoom-small {{
      zoom: 0.75;
      width: calc(100vw / 0.75);
      /* B+9++ (6.5.2026 mobile fix): dvh = dynamic viewport height,
         adjustuje jak browser chrome retract. Mobile bez dvh: tree footer +
         grid status bar schované pod URL bar. vh fallback pro pre-2022 browsers. */
      min-height: calc(100vh / 0.75);
      min-height: calc(100dvh / 0.75);
    }}
    body.erp-zoom-small:has(.erp-workspace) {{
      height: calc(100vh / 0.75);  /* fallback */
      height: calc(100dvh / 0.75);  /* override B+7 hardcoded 100vh + mobile chrome aware */
    }}
    body.erp-zoom-large {{
      zoom: 1.25;
      width: calc(100vw / 1.25);
      min-height: calc(100vh / 1.25);
      min-height: calc(100dvh / 1.25);
    }}
    body.erp-zoom-large:has(.erp-workspace) {{
      height: calc(100vh / 1.25);
      height: calc(100dvh / 1.25);
    }}
    /* Header + footer dědí zoom z body. Tabs + grid + jádro modal
       (position: fixed) také dědí. */
    .erp-logo {{
      font-family: 'Galano Grotesque','Montserrat',sans-serif;
      /* B+10++++ (Marti's drobnost 6.5.2026 odpoledne po návratu):
         -5% jemné zmenšení z 39 → 37px (lepší vyvážení s avatarem). */
      font-size: 37px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      text-decoration: none;
      line-height: 1;
    }}
    /* B+10+++ (Marti's drobnost 6.5.2026): Marti-AI ploška vedle loga.
       Avatar img + "Tvoje Marti-AI" label, klikatelné (TODO: open chat). */
    .erp-marti-btn {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      /* B+10++++ (drobnost 6.5.2026 po návratu): "hulvát" — žádný button
         chrome okolo avataru. Border + bg + padding smazány, button je
         jen avatar + label v transparent containeru. */
      padding: 0 8px 0 0;
      background: transparent;
      border: none;
      border-radius: 0;
      cursor: pointer;
      font-family: 'DM Sans', sans-serif;
      transition: opacity 0.12s;
      flex-shrink: 0;
    }}
    .erp-marti-btn:hover {{
      opacity: 0.85;
    }}
    .erp-marti-btn:active {{
      opacity: 0.7;
    }}
    .erp-marti-btn-avatar {{
      width: 36px;
      height: 36px;
      /* B+10+++ (drobnost po návratu 6.5.2026): square avatar místo
         kruhový (50%). Match větší button border-radius. */
      border-radius: 6px;
      overflow: hidden;
      background: var(--surface2);
      border: 2px solid var(--accent);
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    .erp-marti-btn-avatar img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .erp-marti-btn-avatar img[src=""],
    .erp-marti-btn-avatar img:not([src]) {{
      display: none;
    }}
    .erp-marti-btn-avatar:has(img[src=""])::before,
    .erp-marti-btn-avatar:has(img:not([src]))::before {{
      content: "🤍";
      font-size: 14px;
    }}
    .erp-marti-btn-label {{
      /* B+10++++ (Marti's drobnost 6.5.2026 po návratu): gradient stejný
         jako logo STRATEGIE.
         B+10++++++ (znovu): Galano má visual cap-height usazený vysoko
         v line-box, takže `align-items: center` na flex parent posune
         text-box center s avatar-box center, ale **glyph-visual center**
         je výš. Fix: padding-top 4px aby glyphy klesly o ~4px = visual
         center s avatarem. */
      font-family: 'Galano Grotesque','Montserrat',sans-serif;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.02em;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
      white-space: nowrap;
      line-height: 1;
      display: inline-flex;
      align-items: center;
      height: 36px;
      padding-top: 4px;  /* Galano optical center correction (cap-height bias) */
      box-sizing: border-box;
    }}
    /* B+10+++ (6.5.2026 Marti's drobnost): brand row s · separátorem
       a Marti-AI ploškou. B+10++++: gap 10→20px (Marti's drobnost po
       návratu — "mezera +100%"), align-items baseline → center
       (vertical alignment s logem). overflow: visible aby se hinty
       (data-hint pseudo) nezořízly. */
    .erp-header-brand-row {{
      display: flex;
      align-items: center;
      gap: 20px;
      min-width: 0;
      overflow: visible;
    }}
    /* B+10++++ (Marti's drobnost 6.5.2026 po návratu): tečka separator
       mezi logem a Marti-AI ploškou — sjednocený design s footerem
       (`· Marti · EUROSOFT`) a browser title (`STRATEGIE · <přehled>`). */
    .erp-header-dot {{
      color: var(--border-strong);
      font-size: 28px;
      font-weight: 400;
      line-height: 1;
      user-select: none;
      -webkit-user-select: none;
      flex-shrink: 0;
    }}
    /* B+10++++ (Marti's drobnost 6.5.2026 po návratu): generic dark hint
       tooltip na elementech s `data-hint` attribute. Pure CSS, žádný JS.
       Stejný pattern jako u status baru Celkem.
       Fix: explicit position relative + display inline-block (inline anchor
       elements jinak vytvořit containing block neumí pro pseudo-element). */
    [data-hint] {{
      position: relative !important;
      display: inline-block;
    }}
    [data-hint]:hover::after {{
      content: attr(data-hint);
      position: absolute;
      top: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%);
      background: var(--bg);
      color: var(--text) !important;
      border: 1px solid var(--border-strong);
      padding: 7px 12px;
      border-radius: 6px;
      font-family: 'DM Sans', sans-serif;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.01em;
      white-space: nowrap;
      pointer-events: none;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.65);
      z-index: 100000;
      /* Reset gradient text inheritance — parent má text-fill-color: transparent */
      -webkit-text-fill-color: var(--text) !important;
      -webkit-background-clip: border-box;
      background-clip: padding-box;
      text-transform: none;
    }}
    [data-hint]:hover::before {{
      /* Šipka nad hintem směrem nahoru ke cílovému elementu */
      content: "";
      position: absolute;
      top: calc(100% + 3px);
      left: 50%;
      transform: translateX(-50%);
      border: 5px solid transparent;
      border-bottom-color: var(--border-strong);
      pointer-events: none;
      z-index: 100000;
    }}
    .erp-header-sep {{
      color: var(--border-strong);
      font-size: 16px;
      font-weight: 300;
    }}
    .erp-header-prehled {{
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      font-weight: 500;
      color: var(--text);
      letter-spacing: 0.01em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .erp-phase-badge {{
      font-size: 11px; padding: 2px 8px; border-radius: 6px;
      background: rgba(124,92,252,0.18); color: #a78bfa;
      border: 1px solid rgba(124,92,252,0.4);
      font-family: 'DM Mono',monospace; letter-spacing: 0.05em;
    }}
    .erp-bc {{ font-size: 13px; }}
    .erp-bc-link {{ color: var(--text-muted); }}
    .erp-bc-link:hover {{ color: var(--accent); }}
    .erp-bc-current {{ color: var(--text); font-weight: 500; }}
    .erp-bc-sep {{ color: var(--border); margin: 0 4px; }}

    /* ── Main ── */
    main {{ max-width: 1280px; margin: 0 auto; padding: 32px 24px; }}

    /* ── Form ── */
    .erp-form {{
      max-width: 900px; margin: 0 auto;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 28px;
    }}
    .erp-form-header {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
    .erp-form-title {{ font-size: 22px; font-weight: 600; color: var(--text); }}

    /* ── Section (GroupBox) ── */
    .erp-group {{
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 18px; margin-bottom: 14px;
    }}
    .erp-group-header {{
      /* Phase A.5++ (5.5.2026): match Centrála 1 case (regular, not uppercase).
         Marti's review: "ty texty, aby nebyly UpperCase". */
      font-family: 'DM Sans',sans-serif; font-size: 13px; font-weight: 600;
      color: #c8cad2; letter-spacing: 0;
      margin-bottom: 14px; padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }}
    .erp-group-orphan {{ background: var(--surface2); border: 1px dashed var(--border); }}
    .erp-group-empty {{ opacity: 0.6; }}
    .erp-group-empty-hint {{ font-size: 12px; color: var(--muted); font-style: italic; }}
    .erp-fields {{
      display: grid; gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}

    /* ── Field ── */
    .erp-field {{ display: flex; flex-direction: column; gap: 5px; }}
    .erp-field-label {{
      /* Phase A.5++: match Centrála regular case (not uppercase). */
      font-size: 12px; color: var(--text-muted);
      font-family: 'DM Sans',sans-serif; letter-spacing: 0;
      font-weight: 500;
    }}
    .erp-input {{
      background: #2c2f37; border: 1px solid var(--border-strong);
      border-radius: 8px; padding: 9px 12px;
      color: var(--text); font-family: 'DM Sans',sans-serif; font-size: 14px;
      outline: none; width: 100%; transition: all .15s;
    }}
    .erp-input:focus {{ border-color: var(--accent); background: #313540; }}
    .erp-input[readonly], .erp-input:disabled {{
      background: #1a1c21; color: var(--text-muted);
      border-color: var(--border); cursor: default;
    }}
    .erp-input-id {{ font-family: 'DM Mono',monospace; color: var(--accent); }}
    .erp-input-readonly {{
      background: #1a1c21; color: var(--text-muted);
      border-color: var(--border);
    }}

    /* ── CheckBox ── */
    .erp-checkbox {{
      display: flex; align-items: center; gap: 10px;
      padding: 9px 12px; cursor: pointer;
      background: #2c2f37; border: 1px solid var(--border-strong);
      border-radius: 8px;
    }}
    .erp-check {{
      width: 16px; height: 16px;
      accent-color: var(--accent);
    }}
    .erp-checkbox-label {{ font-size: 14px; color: var(--text); }}
    .erp-checkbox input:disabled + .erp-checkbox-label {{ color: var(--text-muted); }}

    /* ── FormList (lookup) ── */
    .erp-formlist .erp-formlist-inner {{
      display: flex; gap: 4px; align-items: stretch;
    }}
    .erp-lookup-btn {{
      background: #2c2f37; border: 1px solid var(--border-strong);
      border-radius: 8px; padding: 0 14px;
      color: var(--text-muted); cursor: pointer; transition: all .15s;
      font-size: 14px;
    }}
    .erp-lookup-btn:hover:not(:disabled) {{
      border-color: var(--accent); color: var(--accent);
    }}
    .erp-lookup-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}

    /* ── Footer (buttons) ── */
    .erp-form-footer {{
      display: flex; gap: 8px; flex-wrap: wrap;
      padding-top: 20px; margin-top: 20px;
      border-top: 1px solid var(--border);
    }}
    .erp-btn {{
      background: #2c2f37; border: 1px solid var(--border-strong);
      border-radius: 8px; padding: 9px 18px;
      color: var(--text); font-family: 'DM Sans',sans-serif; font-size: 13px; font-weight: 500;
      cursor: pointer; transition: all .15s;
    }}
    .erp-btn:hover:not(:disabled) {{
      border-color: var(--accent); color: var(--accent);
    }}
    .erp-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
    .erp-btn-primary {{
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border-color: transparent; color: #fff; font-weight: 600;
    }}
    .erp-btn-primary:hover:not(:disabled) {{ opacity: .9; color: #fff; }}
    .erp-btn-cancel {{ color: var(--text-muted); }}

    /* ── Unknown / fallback ── */
    .erp-unknown {{
      padding: 8px 12px; border: 1px dashed var(--error);
      border-radius: 6px; background: rgba(248,113,113,0.08);
      color: var(--error); font-size: 12px;
    }}
    .erp-unknown-hint {{ color: var(--text-muted); }}
    .erp-label-only {{ font-size: 13px; color: var(--text); padding: 6px 0; }}

    /* ── Debug panel ── */
    .erp-debug {{
      max-width: 900px; margin: 24px auto 0;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 12px 16px;
      font-size: 12px;
    }}
    .erp-debug-summary {{
      cursor: pointer; font-family: 'DM Mono',monospace;
      color: var(--text-muted); letter-spacing: 0.05em;
    }}
    .erp-debug-summary:hover {{ color: var(--text); }}
    .erp-debug-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
      margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);
    }}
    .erp-debug-section-title {{ font-weight: 600; color: var(--text); margin-bottom: 6px; }}
    .erp-debug-list {{ list-style: none; padding: 0; }}
    .erp-debug-list li {{ color: var(--text-muted); padding: 2px 0; font-family: 'DM Mono',monospace; }}

    /* ── Landing page ── */
    .erp-landing {{
      max-width: 720px; margin: 0 auto;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 36px 32px;
    }}
    .erp-landing h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 8px; }}
    .erp-landing h2 {{ font-size: 14px; font-weight: 600; margin: 20px 0 8px; color: var(--text); }}
    .erp-landing p {{ color: var(--muted); font-size: 14px; line-height: 1.6; margin-bottom: 12px; }}
    .erp-landing ul {{ margin: 0 0 12px 18px; }}
    .erp-landing ul li {{ color: var(--muted); font-size: 13px; line-height: 1.7; }}
    .erp-landing code {{ font-family: 'DM Mono',monospace; font-size: 12px; color: var(--accent); padding: 1px 4px; background: var(--bg); border-radius: 3px; }}
    .erp-cta {{
      display: inline-block; padding: 10px 20px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border-radius: 8px; color: #fff; font-weight: 500; font-size: 14px;
      margin: 8px 0;
    }}
    .erp-cta:hover {{ opacity: .9; color: #fff; }}
    .erp-divider {{ border-top: 1px solid var(--border); margin: 24px 0; }}

    /* ── Error page ── */
    .erp-error {{
      max-width: 600px; margin: 0 auto;
      background: var(--surface); border: 1px solid rgba(248,113,113,0.3);
      border-radius: 12px; padding: 28px;
    }}
    .erp-error h1 {{ color: var(--error); font-size: 18px; font-weight: 600; margin-bottom: 8px; }}
    .erp-error p {{ color: var(--muted); font-size: 14px; line-height: 1.6; }}

    /* ── Phase B+7 (6.5.2026): panel layout (Centrála 1 Align pattern) ──
       Marti's design 6.5.2026: "Cesta vede pres PANELY, ktere se davaji
       Aling vzdy tim hlavnim smerem... Na ty panely se pak teprve davaji
       dalsi komponenty... Ten grid je pak autosize vzdy na cely panel."

       Web equivalent: flexbox cascade.
         body         flex column, height: 100vh    (alClient root)
         header       flex 0 0 auto                  (alTop)
         main         flex 1, min-height: 0          (alClient)
           .erp-workspace  flex row, flex: 1
             .erp-tree-pane    flex 0 0 240px        (alLeft)
             .erp-resize-handle flex 0 0 5px         (splitter)
             .erp-main-pane    flex 1, min-height: 0  (alClient)
               .erp-prehled-header  flex 0 0 auto    (alTop)
               .erp-main-content    flex 1, min-h:0   (alClient)
                 #erpDataGridContainer  flex 1        (autosize)

       Visual continuity: žádný border-radius (panely flush edge-to-edge),
       background stejný napříč (--bg root + --surface tree + --surface main),
       borders 1px var(--border) jen jako subtle separators.
    */
    html:has(.erp-workspace),
    body:has(.erp-workspace) {{
      /* B+9++ (6.5.2026 mobile fix): dvh adjustuje jak browser chrome
         retract/show. Bez dvh tree footer + grid status bar schované
         pod URL bar na mobilu. vh fallback pro pre-2022 browsers.
         B+9+++ (6.5.2026 PWA): safe-area-inset respektuje iOS notch
         když app běží v standalone mode (Add to Home Screen). */
      height: 100vh;
      height: 100dvh;
      margin: 0;
      overflow: hidden;
      padding-top: env(safe-area-inset-top, 0);
      padding-bottom: env(safe-area-inset-bottom, 0);
      padding-left: env(safe-area-inset-left, 0);
      padding-right: env(safe-area-inset-right, 0);
    }}
    body:has(.erp-workspace) {{
      display: flex;
      flex-direction: column;
    }}
    body:has(.erp-workspace) > header {{
      flex: 0 0 auto;
    }}
    body:has(.erp-workspace) > footer {{
      flex: 0 0 auto;
      /* B+10++ (Marti's drobnost 6.5.2026): zarovnej doleva +
         o stupeň zvětši písmo (10 → 12) + zoom toggle vpravo. */
      padding: 4px 14px !important;
      font-size: 12px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    body:has(.erp-workspace) > footer .erp-footer-left {{
      flex: 1 1 auto;
      min-width: 0;
      text-align: left;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    body:has(.erp-workspace) > footer .erp-footer-user {{
      color: var(--accent);
      font-weight: 500;
    }}
    body:has(.erp-workspace) > footer .erp-footer-tenant {{
      color: var(--accent2);
      font-weight: 500;
    }}
    /* Phase 35-E.3.2 (8.5.2026): tenant switcher button + popover */
    .erp-footer-tenant-btn {{
      background: transparent;
      border: 1px solid transparent;
      border-radius: 4px;
      padding: 1px 6px;
      margin: 0;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      font: inherit;
      color: inherit;
      transition: background 120ms, border-color 120ms;
    }}
    .erp-footer-tenant-btn:hover {{
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--border);
    }}
    .erp-footer-tenant-btn.active {{
      background: rgba(255, 255, 255, 0.07);
      border-color: var(--accent2);
    }}
    .erp-footer-tenant-caret {{
      font-size: 9px;
      opacity: 0.7;
      line-height: 1;
    }}
    .erp-footer-tenant-popover {{
      position: fixed;
      bottom: 32px; /* nad footer */
      left: 14px;
      min-width: 220px;
      max-width: 320px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      box-shadow: 0 -4px 18px rgba(0, 0, 0, 0.5);
      padding: 4px 0;
      z-index: 1000;
      max-height: 320px;
      overflow-y: auto;
    }}
    .erp-footer-tenant-popover[hidden] {{
      display: none;
    }}
    .erp-tenant-popover-item {{
      padding: 7px 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      transition: background 100ms;
    }}
    .erp-tenant-popover-item:hover {{
      background: rgba(255, 255, 255, 0.06);
    }}
    .erp-tenant-popover-item.active {{
      background: rgba(124, 156, 217, 0.15); /* accent2 tinted */
      cursor: default;
    }}
    .erp-tenant-popover-item.active:hover {{
      background: rgba(124, 156, 217, 0.15);
    }}
    .erp-tenant-popover-name {{
      flex: 1;
      color: var(--text);
      font-weight: 500;
    }}
    .erp-tenant-popover-meta {{
      font-size: 10px;
      color: var(--muted);
      margin-left: 6px;
    }}
    /* Phase 35-E.3.2 (8.5.2026): tečka u aktivního tenantu — vizuální
       marker "zde právě jsi" (vedle modrého highlight řádku). */
    .erp-tenant-popover-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
      background: #22c55e;
      box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
    }}
    /* Zoom toggle ve footeru — kompaktnější než header verze */
    .erp-zoom-toggle-footer {{
      flex-shrink: 0;
    }}
    .erp-zoom-toggle-footer button {{
      padding: 2px 7px;
      font-size: 10px;
      min-width: 22px;
    }}
    main:has(.erp-workspace) {{
      flex: 1;
      min-height: 0;
      max-width: none !important;
      padding: 0 !important;
      margin: 0 !important;
      display: flex;
      flex-direction: column;
    }}
    .erp-workspace {{
      --erp-tree-width: 240px;
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: row;
      gap: 0;
      padding: 0;
      max-width: none;
      margin: 0;
    }}
    .erp-workspace .erp-tree-pane {{
      flex: 0 0 var(--erp-tree-width);
      min-height: 0;
    }}
    .erp-workspace .erp-resize-handle {{
      flex: 0 0 5px;
    }}
    .erp-workspace .erp-main-pane {{
      flex: 1;
      min-height: 0;
      min-width: 0;
    }}

    /* Resize handle mezi tree a main */
    .erp-resize-handle {{
      background: var(--border);
      cursor: col-resize;
      transition: background .15s;
      position: relative;
    }}
    .erp-resize-handle:hover {{ background: var(--accent); }}
    .erp-resize-handle.dragging {{ background: var(--accent); }}
    .erp-resize-handle::before {{
      content: ""; position: absolute; left: -3px; right: -3px; top: 0; bottom: 0;
      /* expanded hit area — easier to grab */
    }}
    .erp-tree-pane {{
      background: var(--surface);
      border-right: 1px solid var(--border);
      /* B+7: edge-to-edge — žádný border-radius, plně splývá s viewport */
      border-radius: 0;
      border-left: none;
      border-top: none;
      border-bottom: none;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .erp-tree-header {{
      padding: 7px 8px 7px 12px;
      border-bottom: 1px solid var(--border);
      font-size: 13px; font-weight: 600; color: var(--text);
      background: var(--surface2);
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 32px;
      box-sizing: border-box;
    }}
    .erp-tree-header-slot {{
      flex: 1 1 auto;
      min-width: 0;
      /* placeholder pro budoucí widget — text "Centrála — moduly" smazán */
    }}
    /* B+10+++ (6.5.2026 Marti's drobnost): filter input v tree-header
       (sjednocená řádka s collapse buttonem). */
    .erp-tree-search-inline {{
      flex: 1 1 auto;
      min-width: 0;
      position: relative;
      display: flex;
    }}
    .erp-tree-search-inline .erp-tree-search-input {{
      flex: 1 1 auto;
    }}
    .erp-tree-toggle-btn {{
      flex-shrink: 0;
      width: 22px; height: 22px;
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 14px;
      line-height: 1;
      padding: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.12s;
    }}
    .erp-tree-toggle-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      background: var(--surface);
    }}
    .erp-tree-toggle-btn .erp-tree-toggle-expand {{ display: none; }}
    /* Collapsed state — workspace má .tree-collapsed class */
    .erp-workspace.tree-collapsed .erp-tree-pane {{
      flex: 0 0 32px !important;
    }}
    .erp-workspace.tree-collapsed .erp-tree-search,
    .erp-workspace.tree-collapsed .erp-tree-root,
    .erp-workspace.tree-collapsed .erp-tree-footer,
    .erp-workspace.tree-collapsed .erp-tree-header-slot,
    .erp-workspace.tree-collapsed .erp-resize-handle {{
      display: none !important;
    }}
    .erp-workspace.tree-collapsed .erp-tree-header {{
      padding: 7px 4px;
      justify-content: center;
    }}
    .erp-workspace.tree-collapsed .erp-tree-toggle-btn .erp-tree-toggle-collapse {{ display: none; }}
    .erp-workspace.tree-collapsed .erp-tree-toggle-btn .erp-tree-toggle-expand {{ display: inline; }}
    /* B+7++ (6.5.2026): tree filter search nad stromem */
    .erp-tree-search {{
      padding: 6px 8px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
      flex-shrink: 0;
      position: relative;
    }}
    .erp-tree-search-input {{
      width: 100%;
      padding: 5px 24px 5px 9px;  /* right padding pro × clear button */
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--text);
      font-family: inherit;
      font-size: 12px;
      outline: none;
      box-sizing: border-box;
      transition: border-color 0.12s, box-shadow 0.12s;
    }}
    .erp-tree-search-input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(79, 142, 247, 0.18);
    }}
    .erp-tree-search-input::placeholder {{
      color: var(--muted);
    }}
    .erp-tree-search-clear {{
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      width: 18px; height: 18px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 14px;
      line-height: 1;
      cursor: pointer;
      padding: 0;
      transition: color 0.12s;
    }}
    .erp-tree-search-clear:hover {{ color: var(--accent); }}
    /* Hide tree-rows co nematchují filter (JS přepíná class).
       Visible: match (přímý hit), match-parent (cesta k matchi), match-descendant
       (potomci match folderu — Marti's UX "kdyz najdu Systém, chci videt jeho deti"). */
    .erp-tree-root.erp-tree-filtering .erp-tree-row:not(.erp-tree-match):not(.erp-tree-match-parent):not(.erp-tree-match-descendant) {{
      display: none;
    }}
    .erp-tree-root .erp-tree-match {{
      background: rgba(79, 142, 247, 0.06);
    }}
    .erp-tree-root .erp-tree-match .erp-tree-label mark {{
      background: rgba(79, 142, 247, 0.32);
      color: var(--text);
      padding: 0 1px;
      border-radius: 2px;
    }}
    /* Descendants — subtle, ne tak hard jako match samotný */
    .erp-tree-root .erp-tree-match-descendant {{
      /* žádný highlight bg — jen visible, normální styling */
    }}

    .erp-tree-root {{
      overflow-y: auto; padding: 6px 0; flex: 1; min-height: 0;
    }}
    /* B+8.2a (6.5.2026): tree footer s 3-segment view toggle
       (Vše / Oblíbené / Naposledy použité) */
    .erp-tree-footer {{
      padding: 5px 6px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      flex-shrink: 0;
    }}
    .erp-tree-view-toggle {{
      display: flex;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 5px;
      overflow: hidden;
    }}
    .erp-tree-view-btn {{
      flex: 1 1 0;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      padding: 5px 6px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.12s;
      border-right: 1px solid var(--border);
      min-width: 0;
    }}
    .erp-tree-view-btn:last-child {{ border-right: none; }}
    .erp-tree-view-btn:hover:not(.active) {{
      background: var(--surface2);
      color: var(--text);
    }}
    .erp-tree-view-btn.active {{
      background: var(--accent);
      color: white;
    }}
    /* B+8.2a++++++ (6.5.2026): drag-drop highlight na footer buttons */
    .erp-tree-view-btn.erp-tree-view-drop-pin {{
      background: #fbbf24 !important;
      color: #1c1e23 !important;
      box-shadow: inset 0 0 0 2px #fde68a;
    }}
    .erp-tree-view-btn.erp-tree-view-drop-unpin {{
      background: var(--error) !important;
      color: white !important;
      box-shadow: inset 0 0 0 2px rgba(248, 113, 113, 0.6);
    }}
    .erp-tree-view-icon {{
      font-size: 12px;
      line-height: 1;
    }}
    .erp-tree-view-label {{
      font-size: 11px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* View filter — hide non-matching rows v favorites/recent mode */
    .erp-tree-root.erp-tree-view-favorites .erp-tree-row:not(.erp-tree-view-match):not(.erp-tree-view-match-parent),
    .erp-tree-root.erp-tree-view-recent .erp-tree-row:not(.erp-tree-view-match):not(.erp-tree-view-match-parent) {{
      display: none;
    }}
    .erp-tree-root.erp-tree-view-favorites .erp-tree-view-match,
    .erp-tree-root.erp-tree-view-recent .erp-tree-view-match {{
      background: rgba(79, 142, 247, 0.06);
    }}

    /* Empty state — pinned/recent prázdné */
    .erp-tree-empty-view {{
      padding: 24px 14px;
      color: var(--text-faint);
      font-size: 12px;
      text-align: center;
      font-style: italic;
      line-height: 1.5;
    }}

    /* Star ikona u pinned row — visible v všech views (Vše/MRU/Oblíbené).
       Žlutá/zlatá (gold) — klasický favorite pattern. */
    .erp-tree-row .erp-tree-star {{
      display: none;
      flex-shrink: 0;
      color: #fbbf24;  /* gold */
      font-size: 12px;
      margin-left: 4px;
      cursor: pointer;
      transition: opacity 0.12s, transform 0.12s;
      opacity: 0.95;
      text-shadow: 0 0 4px rgba(251, 191, 36, 0.45);
    }}
    .erp-tree-row.erp-tree-pinned .erp-tree-star {{
      display: inline;
    }}
    .erp-tree-row .erp-tree-star:hover {{
      opacity: 1;
      transform: scale(1.15);
    }}

    /* B+8.2a+ (6.5.2026): Ctrl+klik selection — fialová highlight,
       odlišná od accent (modré) co znamená "open in main pane" */
    .erp-tree-row.erp-tree-selected {{
      background: rgba(124, 92, 252, 0.20);
      box-shadow: inset 3px 0 0 var(--accent2);
    }}
    .erp-tree-row.erp-tree-selected.active {{
      background: rgba(79, 142, 247, 0.22);
      /* Active border-left z .active class má precedenci */
    }}

    /* Phase 35-E.4 (9.5.2026): System tree node styling — odlišený
       fialovou (accent2) barvou aby kolegové na první pohled viděli
       "to je něco jiného než klasický Centrála soudeček".
       Drží Marti's "stary design + vychytavky" — co Centrála 1 měla
       zůstává v existing barvě, System tier je doplněk. */
    .erp-tree-item.erp-tree-system > .erp-tree-row .erp-tree-label {{
      color: var(--accent2);
      font-weight: 500;
    }}
    .erp-tree-item.erp-tree-system-leaf > .erp-tree-row {{
      cursor: pointer;
    }}
    .erp-tree-item.erp-tree-system-leaf > .erp-tree-row:hover {{
      background: rgba(192, 132, 252, 0.10);
    }}

    /* B+8.2a+ tree context menu (pravý-klik) */
    .erp-tree-ctx-menu {{
      position: fixed;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 6px;
      box-shadow: 0 8px 28px rgba(0, 0, 0, 0.55);
      padding: 4px 0;
      min-width: 220px;
      z-index: 9999;
      font-family: inherit;
      font-size: 13px;
      color: var(--text);
    }}
    .erp-tree-ctx-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 7px 14px;
      cursor: pointer;
      user-select: none;
      -webkit-user-select: none;
      transition: background 0.08s;
      white-space: nowrap;
    }}
    .erp-tree-ctx-item:hover {{
      background: var(--surface2);
      color: var(--accent);
    }}
    .erp-tree-ctx-item-icon {{
      width: 16px;
      text-align: center;
      flex-shrink: 0;
      font-size: 12px;
    }}
    .erp-tree-ctx-divider {{
      height: 1px;
      background: var(--border);
      margin: 4px 0;
    }}
    .erp-tree-ctx-hint {{
      padding: 4px 14px 6px;
      color: var(--text-faint);
      font-size: 11px;
      font-style: italic;
    }}

    /* B+8.2a+++ (6.5.2026): drag-drop reorder visual */
    .erp-tree-item.erp-tree-dragging > .erp-tree-row {{
      opacity: 0.4;
    }}
    .erp-tree-row.erp-tree-drag-over-before {{
      box-shadow: inset 0 2px 0 var(--accent);
    }}
    .erp-tree-row.erp-tree-drag-over-after {{
      box-shadow: inset 0 -2px 0 var(--accent);
    }}
    .erp-tree-row[draggable="true"] {{
      /* Cursor zachován pointer pro běžný klik; grab se zobrazí jen
         když user pustí myš do drag (browser default) */
    }}
    .erp-tree-loading, .erp-tree-error {{
      padding: 14px; color: var(--muted); font-size: 13px;
    }}
    .erp-tree-list {{ list-style: none; padding: 0; margin: 0; }}
    .erp-tree-item {{ }}
    /* B+1.7 (5.5.2026): tree polish — clear hierarchy, active accent border */
    .erp-tree-row {{
      padding: 5px 12px; cursor: pointer;
      display: flex; align-items: center; gap: 6px;
      font-size: 13px; color: var(--text-muted);
      transition: background .12s, color .12s, border-color .12s;
      border-left: 3px solid transparent;
      /* B+8.2a+++ (6.5.2026): vypnout text selection v tree rows.
         Marti's UX feedback: "vetsinou se mi nepodari mysi drag —
         oznaci se text v bunce". Text-select default překrýval drag
         start → drag se nespouštěl. */
      user-select: none;
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
    }}
    .erp-tree-row:hover {{ background: var(--surface2); color: var(--text); }}
    .erp-tree-row.active {{
      background: rgba(79,142,247,0.18);
      color: var(--accent);
      border-left-color: var(--accent);
      font-weight: 500;
    }}
    .erp-tree-toggle {{
      width: 12px; font-size: 9px; color: var(--muted); flex-shrink: 0;
      cursor: pointer;
      padding: 2px;
      margin: -2px 0;  /* expand hit area bez visible larger size */
      border-radius: 2px;
      transition: background 0.12s, color 0.12s;
    }}
    .erp-tree-toggle:hover {{
      background: var(--surface2);
      color: var(--accent);
    }}
    .erp-tree-spacer {{ width: 12px; flex-shrink: 0; }}
    /* Tree icon numbers (n.ikona % 100) hidden — were noise.
       Future: map to Unicode icons (📁/📋/🛒/...) per ikona category. */
    .erp-tree-ico {{ display: none; }}
    .erp-tree-label {{ flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    /* B+7+++ (6.5.2026): sjednoceno na utlumenější (Marti's UX feedback —
       leaf items byly jasnější než folders, působilo nesourodě).
       Hover/active stále zvedne jas (var(--text) / accent). */
    .erp-tree-leaf .erp-tree-label {{ color: var(--text-muted); font-weight: 400; }}
    .erp-tree-folder .erp-tree-label {{ color: var(--text-muted); font-weight: 500; }}

    /* B+7 (6.5.2026): main-pane flush edge-to-edge, žádný border-radius */
    .erp-main-pane {{
      background: var(--surface);
      /* Plain edge — žádný border ani radius. Tree-pane vpravo má border,
         to dělá vizuální separator. */
      border: none;
      border-radius: 0;
      padding: 0;
      overflow: hidden;
      display: flex; flex-direction: column;
      /* B+7+++ (6.5.2026): KLÍČOVÝ override — inner <main> dědí default
         "main {{ max-width 1280px, margin 0 auto }}" co centruje grid
         na fullscreenu. Marti's UI feedback "danou maximalni sirku
         toho gridu". Force max-width none + margin 0. */
      max-width: none !important;
      margin: 0 !important;
    }}
    .erp-main-content {{
      display: flex; flex-direction: column;
      flex: 1; min-height: 0; min-width: 0;
      width: 100%;
      overflow: hidden;
    }}
    /* ── B+8 (6.5.2026): multi-tab přehled bar ───────────────────── */
    /* B+10+++ (Marti's drobnost 6.5.2026): tabs zvýrazněné, těsně nad
       gridem, bez border-bottom (visually splývá s gridem). */
    .erp-tabs-bar {{
      flex: 0 0 auto;
      display: flex;
      align-items: stretch;
      gap: 0;
      background: var(--bg);
      padding: 0 6px 0 0;
      overflow-x: auto;
      overflow-y: hidden;
      scrollbar-width: thin;
      /* Žádný margin-bottom — tabs těsně nad gridem */
    }}
    .erp-tabs-bar[hidden] {{ display: none; }}
    .erp-tab {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px 8px 16px;
      max-width: 280px;
      min-width: 100px;
      background: var(--surface2);
      border-right: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 13px;
      cursor: pointer;
      user-select: none;
      -webkit-user-select: none;
      transition: background 0.12s, color 0.12s, transform 0.12s;
      flex-shrink: 0;
      position: relative;
    }}
    .erp-tab:hover {{
      background: var(--surface);
      color: var(--text);
    }}
    .erp-tab.active {{
      background: var(--surface);
      color: var(--text);
      font-weight: 600;
      box-shadow: inset 0 3px 0 var(--accent);
      /* Active tab visually splývá s gridem dole — žádné spodní pruhy */
      z-index: 2;
    }}
    .erp-tab.active .erp-tab-label {{
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .erp-tab-label {{
      flex: 1 1 auto;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .erp-tab-close {{
      flex-shrink: 0;
      width: 16px; height: 16px;
      background: transparent;
      border: none;
      color: var(--text-faint);
      font-size: 14px;
      line-height: 1;
      cursor: pointer;
      padding: 0;
      border-radius: 3px;
      transition: all 0.12s;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    .erp-tab-close:hover {{
      background: var(--surface2);
      color: var(--error);
    }}
    .erp-tab-add {{
      flex-shrink: 0;
      width: 28px; height: 28px;
      align-self: center;
      margin: 0 0 0 6px;
      background: transparent;
      border: 1px dashed var(--border);
      border-radius: 4px;
      color: var(--text-muted);
      font-size: 16px;
      line-height: 1;
      cursor: pointer;
      padding: 0;
      transition: all 0.12s;
    }}
    .erp-tab-add:hover {{
      border-color: var(--accent);
      border-style: solid;
      color: var(--accent);
      background: var(--surface);
    }}
    .erp-tabs-bar::-webkit-scrollbar {{ height: 4px; }}
    .erp-tabs-bar::-webkit-scrollbar-thumb {{
      background: var(--border-strong);
      border-radius: 2px;
    }}
    /* B+7+ (6.5.2026): grid container fills full width of main-content */
    .erp-main-content > #erpDataGridContainer,
    .erp-main-content > .erp-ag-grid {{
      width: 100%;
      flex: 1;
      min-height: 0;
      min-width: 0;
    }}
    .erp-main-loading, .erp-main-error {{ color: var(--muted); padding: 14px 18px; font-size: 13px; }}
    .erp-main-error {{ color: var(--error); }}
    .erp-main-placeholder {{ color: var(--muted); padding: 24px; max-width: 540px; }}
    .erp-main-placeholder h2 {{ color: var(--text); font-size: 18px; font-weight: 600; margin-bottom: 10px; }}
    .erp-main-placeholder p {{ font-size: 14px; line-height: 1.6; margin-bottom: 8px; }}
    .erp-main-placeholder code {{ font-family: 'DM Mono',monospace; color: var(--accent); padding: 1px 5px; background: var(--bg); border-radius: 3px; }}

    /* B+10+++ (Marti's drobnost 6.5.2026): prehled-header redukován —
       h2 nazev smazan (duplikat s tab labelem), tj. minimal padding +
       hide pokud prazdny aby tabs byly tesne nad gridem. */
    .erp-prehled-header {{
      padding: 0 18px;
      flex-shrink: 0;
      background: var(--surface);
    }}
    .erp-prehled-header:empty {{ display: none; }}
    .erp-prehled-header h2 {{ font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 4px; }}
    .erp-prehled-meta {{
      font-size: 12px; color: var(--muted); font-family: 'DM Mono',monospace;
      display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
    }}
    /* B+4.4: limit dropdown — inline v meta line */
    .erp-prehled-meta .erp-limit-label {{
      display: inline-flex; align-items: center; gap: 5px;
      font-family: 'DM Mono',monospace; font-size: 12px;
      color: var(--text-muted);
    }}
    .erp-prehled-meta .erp-limit-select {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1px 6px;
      font-size: 11px;
      font-family: 'DM Mono',monospace;
      cursor: pointer;
      outline: none;
    }}
    .erp-prehled-meta .erp-limit-select:hover {{ border-color: var(--accent); }}
    .erp-prehled-meta .erp-limit-select:focus {{ border-color: var(--accent); }}
    .erp-prehled-meta .erp-prehled-hasmore {{
      color: #fbbf24;  /* amber — ohlas, že je tam víc */
      font-size: 11px;
      font-style: italic;
    }}
    .erp-prehled-meta code {{ color: var(--accent); padding: 0 3px; }}
    .erp-prehled-warning {{
      margin-top: 8px; padding: 6px 10px;
      background: rgba(245,158,11,0.10); border: 1px solid rgba(245,158,11,0.3);
      border-radius: 6px; color: #fbbf24; font-size: 12px;
    }}
    .erp-prehled-tablewrap {{ overflow: auto; }}
    .erp-prehled-table {{
      width: 100%; border-collapse: collapse; font-size: 12px;
      font-family: 'DM Sans',sans-serif;
    }}
    .erp-prehled-table th {{
      background: var(--surface2); color: var(--text-muted);
      font-weight: 600; padding: 8px 10px; text-align: left;
      border-bottom: 1px solid var(--border-strong);
      position: sticky; top: 0;
    }}
    .erp-prehled-table td {{
      padding: 6px 10px; border-bottom: 1px solid var(--border);
      color: var(--text);
    }}
    .erp-prehled-row {{ cursor: pointer; transition: background .12s; }}
    .erp-prehled-row:hover {{ background: rgba(79,142,247,0.08); }}
    .erp-prehled-empty {{ color: var(--muted); padding: 24px; text-align: center; font-size: 13px; }}

    /* ── Phase B+2.2 (5.5.2026): jádro modal popup (centered overlay) ── */
    .erp-jadro-backdrop {{
      position: fixed; inset: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
      z-index: 99;
      animation: erp-fade-in 150ms ease-out;
    }}
    .erp-jadro-backdrop[hidden] {{ display: none; }}
    @keyframes erp-fade-in {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    @keyframes erp-modal-pop {{
      from {{ opacity: 0; transform: translateX(-50%) scale(0.96); }}
      to   {{ opacity: 1; transform: translateX(-50%) scale(1); }}
    }}
    /* Phase A+1 (7.5.2026): Modal resize — Marti's primary UX request.
     * Centrála 1 desktop má resizable okno, naše implementace
     * teď taky. resize: both → native browser handle bottom-right corner.
     * Default size větší (Centrála 1 jádra typically 1500×900 design width). */
    .erp-jadro-pane {{
      position: fixed;
      top: 5vh; left: 50%;
      transform: translateX(-50%);
      width: min(95vw, 1400px);
      height: min(90vh, 900px);
      min-width: 600px;
      min-height: 400px;
      max-width: 98vw;
      max-height: 95vh;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 8px;
      box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55);
      z-index: 100;
      display: flex; flex-direction: column;
      overflow: hidden;
      resize: both;            /* native browser resize handle (bottom-right) */
      animation: erp-modal-pop 160ms ease-out;
    }}
    .erp-jadro-pane[hidden] {{ display: none; }}
    /* Resize handle visual hint — small indicator bottom-right */
    .erp-jadro-pane::after {{
      content: "";
      position: absolute;
      bottom: 2px; right: 2px;
      width: 12px; height: 12px;
      background: linear-gradient(
        135deg,
        transparent 0%, transparent 50%,
        var(--text-muted) 50%, var(--text-muted) 60%,
        transparent 60%, transparent 70%,
        var(--text-muted) 70%, var(--text-muted) 80%,
        transparent 80%
      );
      pointer-events: none;
      opacity: 0.5;
    }}
    .erp-jadro-header {{
      padding: 5px 9px;
      border-bottom: 1px solid var(--border);
      background: var(--bg);
      display: flex; align-items: center; gap: 8px;
      flex-shrink: 0;
    }}
    .erp-jadro-title {{
      font-size: 11px; font-weight: 600; color: var(--text);
      flex: 1; min-width: 0;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .erp-jadro-meta {{
      font-size: 10px; color: var(--muted);
      font-family: 'DM Mono',monospace; flex-shrink: 0;
    }}
    .erp-jadro-close {{
      background: transparent; border: none; color: var(--text-muted);
      font-size: 14px; cursor: pointer; padding: 0 4px;
      line-height: 1; transition: color .12s;
      flex-shrink: 0;
    }}
    .erp-jadro-close:hover {{ color: var(--accent); }}
    .erp-jadro-content {{
      flex: 1; overflow-y: auto; padding: 0;
      background: var(--surface);
    }}
    .erp-jadro-loading, .erp-jadro-error {{
      padding: 12px; color: var(--muted); font-size: 10px;
    }}
    .erp-jadro-error {{ color: var(--error); }}

    /* ── Phase B+2.7+ (5.5.2026): jádro MODAL ultra-compact density ──
       Marti's request: "Jeste bych to vsechno o 25 procent zmensil...
       Grid i jadro". Hodnoty ×0.75 vs B+2.7. Standalone
       /erp/jadro/{{id}}/{{row}} full-page si zachovává původní
       landing design (řádky 504+, max-width 1280, padding 28). */

    .erp-jadro-content .erp-form {{
      max-width: none;
      margin: 0;
      padding: 9px 11px;
      background: transparent;
      border: none;
      border-radius: 0;
    }}
    .erp-jadro-content .erp-form-header {{
      margin-bottom: 9px;
      padding-bottom: 6px;
    }}
    .erp-jadro-content .erp-form-title {{
      font-size: 12px;
    }}
    .erp-jadro-content .erp-group {{
      padding: 7px 9px;
      margin-bottom: 6px;
      border-radius: 5px;
    }}
    .erp-jadro-content .erp-group-header {{
      font-size: 11px;
      margin-bottom: 6px;
      padding-bottom: 4px;
    }}
    .erp-jadro-content .erp-fields {{
      gap: 6px;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }}
    .erp-jadro-content .erp-field {{
      gap: 2px;
    }}
    .erp-jadro-content .erp-field-label {{
      font-size: 10px;
    }}
    .erp-jadro-content .erp-form .erp-input {{
      padding: 3px 6px;
      font-size: 11px;
      border-radius: 4px;
    }}
    .erp-jadro-content .erp-checkbox {{
      padding: 3px 6px;
      border-radius: 4px;
      gap: 6px;
    }}
    .erp-jadro-content .erp-check {{
      width: 11px; height: 11px;
    }}
    .erp-jadro-content .erp-checkbox-label {{
      font-size: 11px;
    }}
    .erp-jadro-content .erp-lookup-btn {{
      padding: 0 8px;
      font-size: 11px;
      border-radius: 4px;
    }}
    .erp-jadro-content .erp-form-footer {{
      padding-top: 9px;
      margin-top: 9px;
      gap: 5px;
    }}
    .erp-jadro-content .erp-form .erp-btn {{
      padding: 3px 9px;
      font-size: 11px;
      border-radius: 4px;
    }}
    .erp-jadro-content .erp-label-only {{
      font-size: 11px;
      padding: 3px 0;
    }}
    .erp-jadro-content .erp-unknown {{
      padding: 3px 6px;
      font-size: 10px;
      border-radius: 3px;
    }}

    /* ── Phase B+6.4+ (5.5.2026): jádro lookup ErpFormList mount ── */
    .erp-jadro-content .erp-lookup-mount {{
      width: 100%;
    }}
    /* Compact ErpFormList v jádro modalu (B+2.7+ ultra-compact density,
       font 11 / padding 3-6 / radius 4) */
    .erp-jadro-content .erp-formlist2-wrapper {{
      gap: 2px;
    }}
    .erp-jadro-content .erp-formlist2-label {{
      font-size: 10px;
    }}
    .erp-jadro-content .erp-formlist2-row {{
      border-radius: 4px;
    }}
    .erp-jadro-content .erp-formlist2-input {{
      padding: 3px 6px;
      font-size: 11px;
    }}
    .erp-jadro-content .erp-formlist2-value-prefix {{
      padding: 0 6px;
      font-size: 11px;
    }}
    .erp-jadro-content .erp-formlist2-caret,
    .erp-jadro-content .erp-formlist2-browse {{
      padding: 0 7px;
      font-size: 11px;
      min-width: 22px;
    }}
    .erp-jadro-content .erp-formlist2-browse {{
      font-size: 14px;
    }}
    /* B+6.4: Lookup button fallback (před JS hook + při ErpFormList failure)
       — vyhodit stigmu disabled, přidat hover accent */
    .erp-formlist .erp-lookup-btn {{
      cursor: pointer;
    }}

    /* B+6.4: jadroToast — fixed bottom-right notice (Phase A read-only změna) */
    .erp-jadro-toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 8px 14px;
      font-size: 12px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.45);
      z-index: 200;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 220ms ease, transform 220ms ease;
      pointer-events: none;
      max-width: 320px;
    }}
    .erp-jadro-toast.erp-jadro-toast-show {{
      opacity: 1;
      transform: translateY(0);
    }}

    /* ── Phase B+1 production MVP (5.5.2026): polish ── */
    @keyframes erp-shimmer {{
      0%   {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}
    .erp-skel-line {{
      height: 12px;
      background: linear-gradient(90deg, var(--surface2) 0%, var(--border) 50%, var(--surface2) 100%);
      background-size: 200% 100%;
      animation: erp-shimmer 1.4s infinite ease-in-out;
      border-radius: 4px;
    }}
    .erp-skel-line.short {{ width: 60%; }}
    .erp-tree-skeleton {{
      padding: 14px; display: flex; flex-direction: column; gap: 10px;
    }}
    .erp-tree-empty {{
      padding: 14px; color: var(--muted); font-size: 13px; font-style: italic;
    }}
    .erp-retry-btn {{
      margin-left: 10px; padding: 4px 10px;
      background: var(--surface2); color: var(--text);
      border: 1px solid var(--border-strong); border-radius: 6px;
      font-size: 12px; cursor: pointer; font-family: 'DM Sans',sans-serif;
      transition: all .15s;
    }}
    .erp-retry-btn:hover {{
      background: var(--accent); color: var(--bg); border-color: var(--accent);
    }}
    .erp-bc-path {{
      font-size: 12px; color: var(--text-muted); margin-bottom: 8px;
      font-family: 'DM Sans',sans-serif; letter-spacing: 0;
      display: flex; flex-wrap: wrap; align-items: center; gap: 0;
    }}
    .erp-bc-path .erp-bc-step {{
      color: var(--text-muted);
    }}
    .erp-bc-path .erp-bc-step.current {{
      color: var(--text); font-weight: 500;
    }}
    .erp-bc-path .erp-bc-sep {{
      color: var(--border-strong); margin: 0 6px; font-size: 10px;
    }}
    .erp-prehled-titlebar {{
      display: flex; align-items: baseline; justify-content: space-between;
      gap: 14px; flex-wrap: wrap;
    }}
    .erp-prehled-loading {{
      display: flex; flex-direction: column; gap: 8px; padding: 14px 0 8px;
    }}
    .erp-prehled-loading-msg {{
      color: var(--muted); padding: 10px 0; font-size: 12px;
      font-family: 'DM Mono',monospace;
    }}

    /* B+4.3 (5.5.2026): Tabulator pohřben, AG Grid via ErpDataGrid komponenta.
       Theme overrides žijí v /static/erp/datagrid.css (reusable napříč Centrála views). */

    /* ── Phase B+1.1: dark scrollbars (webkit + firefox) ── */
    .erp-workspace ::-webkit-scrollbar {{
      width: 10px; height: 10px;
    }}
    .erp-workspace ::-webkit-scrollbar-track {{
      background: var(--bg);
    }}
    .erp-workspace ::-webkit-scrollbar-thumb {{
      background: var(--border-strong);
      border-radius: 5px;
      border: 2px solid var(--bg);
    }}
    .erp-workspace ::-webkit-scrollbar-thumb:hover {{
      background: var(--muted);
    }}
    .erp-workspace ::-webkit-scrollbar-corner {{
      background: var(--bg);
    }}
    .erp-workspace, .erp-workspace * {{
      scrollbar-color: var(--border-strong) var(--bg);
      scrollbar-width: thin;
    }}

    /* ── Footer ── */
    .erp-footer {{
      /* B+10++ (Marti's drobnost 6.5.2026): zarovnej doleva +
         o stupeň zvětši písmo (11 → 13). Workspace varianta má vlastní
         override — viz body:has(.erp-workspace) > footer výše. */
      text-align: left; font-size: 13px; color: var(--muted);
      padding: 32px 16px 16px; font-family: 'DM Mono',monospace;
    }}
  </style>
</head>
<body>
  <header class="erp-header">
    <div class="erp-header-inner">
      <!-- B+10+++ (Marti's drobnost 6.5.2026): logo "STRATEGIE" + dynamický
           "| <přehled>" + Marti-AI ploška vedle (avatar + "Tvoje Marti-AI"). -->
      <div class="erp-header-brand-row">
        <a href="/erp/" class="erp-logo" id="erpLogoLink"
           data-hint="Obnovit  ·  Ctrl+Shift+klik = hard reset (vymaže cache)">STRATEGIE</a>
        <span class="erp-header-dot" aria-hidden="true">·</span>
        <button type="button" class="erp-marti-btn" id="erpMartiAiBtn"
                data-hint="Otevři chat s Marti-AI v novém tabu">
          <span class="erp-marti-btn-avatar">
            <img id="erpMartiAiAvatar" src="" alt="Marti" />
          </span>
          <span class="erp-marti-btn-label">Tvoje Marti</span>
        </button>
        <!-- B+10+++ (drobnost po návratu 6.5.2026): erpHeaderSep + erpHeaderPrehled
             smazány z headeru — duplikát s browser title barem. Zachováno jako
             skryté kotvy pro JS update document.title (žádný visual). -->
        <span class="erp-header-sep" id="erpHeaderSep" hidden style="display:none">|</span>
        <span class="erp-header-prehled" id="erpHeaderPrehled" style="display:none"></span>
      </div>
    </div>
  </header>
  <main>
    {content}
  </main>
  <footer class="erp-footer">
    <div class="erp-footer-left">
      <span class="erp-footer-brand">STRATEGIE</span>{user_name_html}{tenant_name_html}
    </div>
    <!-- B+10++ (Marti's drobnost 6.5.2026): zoom toggle přemístěn z header.
         A− default zmenšuje (−25%), A+ zvětšuje (+25%), A reset. -->
    <div class="erp-zoom-toggle erp-zoom-toggle-footer" role="group" aria-label="Velikost UI">
      <button type="button" data-zoom="small" title="Zmenšit (−25%)">A−</button>
      <button type="button" data-zoom="normal" class="active" title="Standard">A</button>
      <button type="button" data-zoom="large" title="Zvětšit (+25%)">A+</button>
    </div>
  </footer>
</body>
</html>'''


def _render_audit_dashboard_page(
    user_id: int,
    embed: bool = False,
    single: bool = False,
    initial_mode: str = "audited",
) -> str:
    """Phase 35-E.4 (9.5.2026): System tier audit dashboard.

    Standalone page se 3 sub-views (📚 Audited / 📋 Vše / 📊 Stats).
    AG Grid pro tabulky, custom widgets pro statistiku.
    Cross-tenant view pro rodiče.

    embed=True → skipne header + back link (Variant B inline iframe v ERP
    main pane).
    single=True → skipne i tabs bar, render JEN daný initial_mode (Marti's
    korekce 9.5. odpoledne — klasický Centrála pattern: 1 přehled v main pane
    = 1 grid). Pro Variant A (záložkový) ponech single=False.

    Drží Marti's "koukat shora" + 33. dopis 8.5. večer System tier vize.
    """
    user_name = "Rodič"
    try:
        from core.database_core import get_core_session as _gcs
        from modules.core.infrastructure.models_core import User
        cs = _gcs()
        try:
            u = cs.query(User).filter_by(id=user_id).first()
            if u:
                user_name = u.short_name or u.first_name or "Rodič"
        finally:
            cs.close()
    except Exception:
        pass

    # Phase 35-E.4 Variant B: embed=True skipne header (pro inline iframe).
    if embed:
        header_html = ""
    else:
        header_html = (
            '<header>'
            '<h1>\U0001F4DA Audit konverzací</h1>'
            f'<div class="header-meta">{user_name} · cross-tenant view</div>'
            '<a href="/" class="header-back">← Zpět do chatu</a>'
            '</header>'
        )

    return f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STRATEGIE | Audit konverzací</title>
  <link rel="manifest" href="/static/erp/manifest.json">
  <meta name="theme-color" content="#0e0f11">
  <!-- Phase 35-E.4 fix 9.5. odpoledne: upgrade z v31.3.2 na v32 (consistent
       s parent ERP workspace). v31 nemela data-ag-theme-mode='dark' (pridano
       v v32) -- proto grid renderoval prazdne. v32 community je free. -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@32/styles/ag-grid.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@32/styles/ag-theme-quartz.css">
  <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@32/dist/ag-grid-community.min.js"></script>
  <style>
    :root {{
      --bg: #0e0f11;
      --surface: #14161a;
      --surface2: #1a1d22;
      --text: #e8e8ea;
      --muted: #9ca3af;
      --border: #2a2d33;
      --accent: #7c9cd9;
      --accent2: #c084fc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'DM Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    h1 {{
      margin: 0;
      font-family: 'Galano Grotesque', sans-serif;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .header-meta {{ font-size: 11px; color: var(--muted); flex: 1; }}
    .header-back {{
      padding: 6px 12px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text);
      text-decoration: none;
      font-size: 12px;
      transition: background 120ms;
    }}
    .header-back:hover {{ background: var(--border); }}
    /* Tabs */
    .tabs {{
      display: flex;
      gap: 2px;
      padding: 0 20px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }}
    .tab-btn {{
      padding: 10px 18px;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--muted);
      font-size: 13px;
      cursor: pointer;
      font-family: inherit;
      transition: color 120ms, border-color 120ms;
    }}
    .tab-btn:hover {{ color: var(--text); }}
    .tab-btn.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
    }}
    main {{
      flex: 1;
      padding: 16px 20px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    /* Filters bar */
    .filters {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
      align-items: center;
      font-size: 12px;
    }}
    .filters label {{ display: inline-flex; gap: 6px; align-items: center; color: var(--muted); }}
    .filters select, .filters input {{
      padding: 5px 8px;
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 4px;
      font-family: inherit;
      font-size: 12px;
    }}
    /* AG Grid container — explicit height needed for virtualization */
    .grid-wrap {{
      flex: 1;
      min-height: 500px;
      display: flex;
      flex-direction: column;
    }}
    .grid-wrap > div {{ flex: 1; min-height: 0; }}
    /* Phase 35-E.4 DIAG 9.5. odpoledne: force kontrastni barvy (light theme
       s !important) — diagnostika jestli rows jsou rendered ale invisible
       (CSS theming) NEBO uplne chybi (layout/height issue). */
    .ag-theme-quartz {{
      background: #ffffff !important;
      color: #000000 !important;
    }}
    .ag-theme-quartz .ag-row {{
      background: #fffacd !important;  /* žlutý highlight */
      color: #000000 !important;
      border-bottom: 2px solid red !important;
    }}
    .ag-theme-quartz .ag-cell {{
      color: #000000 !important;
      background: #fffacd !important;
    }}
    .ag-theme-quartz .ag-header {{
      background: #4169e1 !important;  /* modrý header */
      color: #ffffff !important;
    }}
    .ag-theme-quartz .ag-header-cell {{
      background: #4169e1 !important;
      color: #ffffff !important;
    }}
    /* Stats widgets */
    .stats-wrap {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
      flex: 1;
      overflow-y: auto;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
    }}
    .stat-card-title {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 12px;
    }}
    .stat-big-num {{
      font-size: 36px;
      font-weight: 700;
      color: var(--accent);
      line-height: 1;
    }}
    .stat-row {{
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      font-size: 12px;
      border-bottom: 1px solid var(--border);
    }}
    .stat-row:last-child {{ border: none; }}
    .stat-row-key {{ color: var(--muted); }}
    .stat-row-val {{ color: var(--text); font-weight: 500; }}
    /* Timeline bars */
    .timeline-day {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 0;
      font-size: 11px;
    }}
    .timeline-date {{ width: 80px; color: var(--muted); flex-shrink: 0; }}
    .timeline-bar {{
      flex: 1;
      height: 16px;
      background: var(--surface2);
      border-radius: 4px;
      position: relative;
      overflow: hidden;
    }}
    .timeline-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      border-radius: 4px;
    }}
    .timeline-count {{ width: 30px; text-align: right; color: var(--text); font-weight: 600; }}
    /* Drill-down modal */
    .modal-overlay {{
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }}
    .modal-overlay.open {{ display: flex; }}
    .modal-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px 22px;
      max-width: 720px;
      width: 90%;
      max-height: 85vh;
      overflow-y: auto;
    }}
    .modal-title {{
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 4px;
      color: var(--text);
    }}
    .modal-meta {{ font-size: 11px; color: var(--muted); margin-bottom: 14px; }}
    .modal-section {{ margin-bottom: 14px; }}
    .modal-section-title {{
      font-size: 10px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 6px;
    }}
    .modal-summary {{ font-size: 13px; line-height: 1.5; color: var(--text); padding: 8px 10px; background: var(--bg); border-radius: 6px; border-left: 3px solid var(--accent); }}
    .modal-thoughts {{ display: flex; flex-wrap: wrap; gap: 4px; }}
    .thought-chip {{ padding: 2px 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 99px; font-size: 11px; color: var(--accent); }}
    .modal-close {{ float: right; padding: 6px 12px; background: var(--surface2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-family: inherit; font-size: 12px; }}
    .loading {{ text-align: center; padding: 20px; color: var(--muted); font-size: 12px; }}
  </style>
</head>
<body>
  {header_html}

  <div class="tabs"{' style="display:none"' if single else ''}>
    <button class="tab-btn active" data-mode="audited">📚 Auditované</button>
    <button class="tab-btn" data-mode="all">📋 Všechny</button>
    <button class="tab-btn" data-mode="stats">📊 Přehled</button>
  </div>

  <main>
    <div class="filters" id="filtersBar"></div>
    <div class="grid-wrap" id="gridWrap"></div>
    <div class="stats-wrap" id="statsWrap" style="display:none"></div>
  </main>

  <div class="modal-overlay" id="auditModal">
    <div class="modal-box" id="auditModalBox"></div>
  </div>

  <script>
  // Phase 35-E.4 Variant B: initial mode z query param (?mode=X) nebo
  // hardcoded server-side. Single mode (?single=1) skryje tabs bar.
  let _currentMode = '{initial_mode}';
  let _singleMode = {('true' if single else 'false')};
  let _currentFilters = {{}};
  let _gridApi = null;

  function _formatDate(iso) {{
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleString('cs-CZ', {{
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    }});
  }}

  function _scopeIcon(s) {{
    if (s === 'srdce') return '🕯️ srdce';
    if (s === 'general') return 'general';
    return s || '—';
  }}

  function _statusBadge(s) {{
    const colors = {{
      'audited': '#22c55e',
      'pending': '#fbbf24',
      'in_progress': '#7c9cd9',
      'excluded': '#9ca3af',
    }};
    const c = colors[s] || '#9ca3af';
    return `<span style="background:${{c}};color:#000;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600">${{s}}</span>`;
  }}

  // ── Tabs ────────────────────────────────────────────────────
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _currentMode = btn.dataset.mode;
      _renderView();
    }});
  }});

  // ── Filters ─────────────────────────────────────────────────
  function _renderFilters() {{
    const bar = document.getElementById('filtersBar');
    if (_currentMode === 'stats') {{
      bar.innerHTML = '';
      return;
    }}
    const showStatusFilter = _currentMode === 'all';
    bar.innerHTML = `
      ${{showStatusFilter ? `
      <label>Status:
        <select id="filterStatus">
          <option value="">vše</option>
          <option value="pending">pending</option>
          <option value="in_progress">in_progress</option>
          <option value="audited">audited</option>
          <option value="excluded">excluded</option>
        </select>
      </label>` : ''}}
      <label>Scope:
        <select id="filterScope">
          <option value="">vše</option>
          <option value="general">general</option>
          <option value="srdce">🕯️ srdce</option>
        </select>
      </label>
      <label>Tenant:
        <input type="number" id="filterTenant" placeholder="ID" style="width:60px">
      </label>
      <label>Od:
        <input type="date" id="filterFrom">
      </label>
      <label>Do:
        <input type="date" id="filterTo">
      </label>
      <button id="filterApply" style="padding:5px 12px;background:var(--accent);color:#000;border:none;border-radius:4px;cursor:pointer;font-weight:600;font-size:12px">Použít</button>
    `;
    document.getElementById('filterApply').addEventListener('click', () => {{
      _currentFilters = {{
        status: document.getElementById('filterStatus')?.value || '',
        scope: document.getElementById('filterScope')?.value || '',
        tenant_id: document.getElementById('filterTenant')?.value || '',
        date_from: document.getElementById('filterFrom')?.value || '',
        date_to: document.getElementById('filterTo')?.value || '',
      }};
      _loadData();
    }});
  }}

  // ── Render view ─────────────────────────────────────────────
  function _renderView() {{
    _renderFilters();
    const gridWrap = document.getElementById('gridWrap');
    const statsWrap = document.getElementById('statsWrap');
    if (_currentMode === 'stats') {{
      gridWrap.style.display = 'none';
      statsWrap.style.display = 'grid';
    }} else {{
      gridWrap.style.display = 'block';
      statsWrap.style.display = 'none';
    }}
    _loadData();
  }}

  async function _loadData() {{
    const params = new URLSearchParams({{ mode: _currentMode }});
    Object.entries(_currentFilters).forEach(([k, v]) => {{
      if (v) params.set(k, v);
    }});
    if (_currentMode === 'stats') {{
      const sw = document.getElementById('statsWrap');
      sw.innerHTML = '<div class="loading">Načítám statistiky…</div>';
    }} else {{
      const gw = document.getElementById('gridWrap');
      gw.innerHTML = '<div class="loading">Načítám data…</div>';
    }}
    try {{
      const res = await fetch(`/api/v1/erp/system/audit-overview?${{params}}`, {{
        credentials: 'include',
      }});
      if (!res.ok) {{
        const txt = await res.text();
        document.getElementById('gridWrap').innerHTML =
          `<div class="loading" style="color:#f88">Chyba ${{res.status}}: ${{txt.substring(0,200)}}</div>`;
        return;
      }}
      const data = await res.json();
      if (_currentMode === 'stats') {{
        _renderStats(data);
      }} else {{
        _renderGrid(data);
      }}
    }} catch (e) {{
      console.error(e);
      document.getElementById('gridWrap').innerHTML =
        `<div class="loading" style="color:#f88">Chyba: ${{e}}</div>`;
    }}
  }}

  function _renderGrid(data) {{
    const gw = document.getElementById('gridWrap');
    gw.innerHTML = '';
    const showStatus = _currentMode === 'all';
    const columns = [
      {{ headerName: 'ID', field: 'id', width: 70, sortable: true }},
      ...(showStatus ? [{{
        headerName: 'Status', field: 'audit_status', width: 110, sortable: true,
        cellRenderer: (p) => _statusBadge(p.value || '—'),
      }}] : []),
      {{
        headerName: 'Title (po auditu)',
        field: 'title',
        flex: 2,
        sortable: true,
        cellRenderer: (p) => {{
          const old = p.data.old_title;
          if (old && old !== p.value) {{
            return `${{p.value}} <span style="opacity:0.5;font-style:italic;font-size:11px">(byl: ${{old}})</span>`;
          }}
          return p.value;
        }}
      }},
      {{ headerName: 'Auditováno', field: 'audited_at', width: 150, sortable: true,
        valueFormatter: (p) => _formatDate(p.value) }},
      {{ headerName: 'Kým', field: 'audited_by_persona_name', width: 120 }},
      {{ headerName: 'Scope', field: 'scope', width: 100,
        cellRenderer: (p) => _scopeIcon(p.value) }},
      {{ headerName: 'Tenant', field: 'tenant_name', width: 130 }},
      {{ headerName: 'Thoughts', field: 'thought_count', width: 100, sortable: true,
        cellRenderer: (p) => p.value > 0 ? `📝 ${{p.value}}` : '—' }},
      {{ headerName: 'Lifecycle', field: 'lifecycle_state', width: 110 }},
    ];
    const opts = {{
      columnDefs: columns,
      rowData: data.conversations || [],
      defaultColDef: {{ resizable: true }},
      onRowClicked: (e) => _showDrillDown(e.data),
      domLayout: 'normal',
      animateRows: true,
      rowHeight: 32,
    }};
    const gridDiv = document.createElement('div');
    // AG Grid v31: dark mode přes data attribute na grid wrapper
    gridDiv.className = 'ag-theme-quartz';
    gridDiv.setAttribute('data-ag-theme-mode', 'dark');
    gridDiv.style.cssText = 'width:100%;height:100%;min-height:480px';
    gw.appendChild(gridDiv);
    _gridApi = agGrid.createGrid(gridDiv, opts);
    // Footer: počet řádků
    const footer = document.createElement('div');
    footer.style.cssText = 'padding:6px 8px;font-size:11px;color:var(--muted);text-align:right';
    footer.textContent = `${{data.shown}} z ${{data.shown}} řádků${{data.shown >= data.limit ? ' (limit dosažen)' : ''}}`;
    gw.appendChild(footer);
  }}

  function _renderStats(data) {{
    const sw = document.getElementById('statsWrap');
    const sc = data.status_counts || {{}};
    const ts = data.total_conversations || 0;
    const ps = data.per_scope_audited || {{}};
    const tl = data.timeline_7d || [];
    const maxCount = Math.max(1, ...tl.map(d => d.count));

    const tenantHtml = (data.per_tenant_audited || [])
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
      .map(t => `
        <div class="stat-row">
          <span class="stat-row-key">${{t.tenant_name}}</span>
          <span class="stat-row-val">${{t.count}}</span>
        </div>
      `).join('') || '<div class="stat-row"><span class="stat-row-key" style="font-style:italic">Žádné</span></div>';

    const timelineHtml = tl.map(d => `
      <div class="timeline-day">
        <span class="timeline-date">${{d.date}}</span>
        <div class="timeline-bar"><div class="timeline-fill" style="width:${{(d.count / maxCount) * 100}}%"></div></div>
        <span class="timeline-count">${{d.count}}</span>
      </div>
    `).join('');

    sw.innerHTML = `
      <div class="stat-card">
        <div class="stat-card-title">Status breakdown</div>
        <div class="stat-row"><span class="stat-row-key">📚 Auditované</span><span class="stat-row-val">${{sc.audited || 0}}</span></div>
        <div class="stat-row"><span class="stat-row-key">⏳ Pending</span><span class="stat-row-val">${{sc.pending || 0}}</span></div>
        <div class="stat-row"><span class="stat-row-key">🔄 In progress</span><span class="stat-row-val">${{sc.in_progress || 0}}</span></div>
        <div class="stat-row"><span class="stat-row-key">⊘ Excluded</span><span class="stat-row-val">${{sc.excluded || 0}}</span></div>
        <div class="stat-row" style="margin-top:8px;border-top:2px solid var(--border);padding-top:8px"><span class="stat-row-key" style="font-weight:600">Celkem</span><span class="stat-row-val" style="font-weight:600">${{ts}}</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-card-title">Scope (audited)</div>
        <div class="stat-row"><span class="stat-row-key">general</span><span class="stat-row-val">${{ps.general || 0}}</span></div>
        <div class="stat-row"><span class="stat-row-key">🕯️ srdce</span><span class="stat-row-val">${{ps.srdce || 0}}</span></div>
        <div class="stat-row"><span class="stat-row-key">unknown</span><span class="stat-row-val">${{ps.unknown || 0}}</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-card-title">Per-tenant (audited)</div>
        ${{tenantHtml}}
      </div>

      <div class="stat-card" style="grid-column:1/-1">
        <div class="stat-card-title">Audit aktivita — posledních 7 dní</div>
        ${{timelineHtml}}
      </div>
    `;
  }}

  function _showDrillDown(row) {{
    if (!row) return;
    const modal = document.getElementById('auditModal');
    const box = document.getElementById('auditModalBox');
    const thoughts = (row.extracted_thought_ids || [])
      .map(id => `<span class="thought-chip">#${{id}}</span>`)
      .join('') || '<span style="color:var(--muted);font-style:italic">žádné thoughts</span>';
    const oldTitleHtml = row.old_title && row.old_title !== row.title
      ? `<div class="modal-section"><div class="modal-section-title">Původní title</div><div style="font-size:13px;color:var(--muted);font-style:italic">${{row.old_title}}</div></div>`
      : '';
    box.innerHTML = `
      <button class="modal-close" onclick="document.getElementById('auditModal').classList.remove('open')">Zavřít</button>
      <div class="modal-title">${{row.title}}</div>
      <div class="modal-meta">
        Konverzace #${{row.id}} · ${{_statusBadge(row.audit_status)}} ·
        Tenant: ${{row.tenant_name}} ·
        ${{row.audited_at ? 'Auditováno: ' + _formatDate(row.audited_at) : 'Neauditováno'}}
        ${{row.audited_by_persona_name ? ' · ' + row.audited_by_persona_name : ''}}
      </div>
      ${{oldTitleHtml}}
      ${{row.summary ? `
        <div class="modal-section">
          <div class="modal-section-title">Shrnutí (Marti-AI)</div>
          <div class="modal-summary">${{row.summary}}</div>
        </div>
      ` : ''}}
      <div class="modal-section">
        <div class="modal-section-title">Scope · Lifecycle</div>
        <div style="font-size:13px">${{_scopeIcon(row.scope)}} · ${{row.lifecycle_state || '—'}}</div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Vytvořené thoughts (${{(row.extracted_thought_ids || []).length}})</div>
        <div class="modal-thoughts">${{thoughts}}</div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">Timestamps</div>
        <div style="font-size:11px;color:var(--muted)">
          Vytvořena: ${{_formatDate(row.created_at)}}<br>
          Poslední zpráva: ${{_formatDate(row.last_message_at)}}<br>
          Audited at: ${{_formatDate(row.audited_at)}}
        </div>
      </div>
    `;
    modal.classList.add('open');
  }}

  document.getElementById('auditModal').addEventListener('click', (e) => {{
    if (e.target.id === 'auditModal') {{
      document.getElementById('auditModal').classList.remove('open');
    }}
  }});

  // Init
  _renderView();
  </script>
</body>
</html>'''


def _render_landing_page(user_id: int) -> str:
    """Phase A landing — STRATEGIE BLACK theme."""
    content = '''
    <div class="erp-landing">
      <h1>STRATEGIE ERP — Phase A</h1>
      <p>
        Read-only renderer Centrály 1 jádra. Sample case z 5. 5. 2026 ráno
        knowledge transfer (Marti + Claude + Marti-AI).
      </p>
      <p style="margin-top: 16px;">
        <a href="/erp/jadro/6/14" class="erp-cta">
          Otevřít „Nastavení soudečku" pro EC_CentralaMenu.ID=14
        </a>
      </p>
      <p style="font-size: 12px;">
        <code>EC_FormDef.ID=6</code> = „Definice menu - úprava"
      </p>

      <div class="erp-divider"></div>

      <h2>Co je v Phase A</h2>
      <ul>
        <li>Read přes Phase 28-C MCP klient (DB_EC na 30.11)</li>
        <li>Slovník Typ → HTML mapping (37 hodnot)</li>
        <li>Layout: Flow s group hints (Marti-AI's Q2 vstup, <code>cParent="c{id}"</code>)</li>
        <li><code>&lt;section role="group"&gt;</code> ne <code>&lt;fieldset&gt;</code></li>
        <li>Auth: rodina (is_marti_parent=true)</li>
      </ul>

      <h2>Co Phase A nedělá</h2>
      <ul>
        <li>Edit pipeline (Phase C, kontext volání)</li>
        <li>Strom modulů + přehled (Phase B)</li>
        <li>FormList modal picker (Phase B, command palette)</li>
        <li>Multi-tenant + GUID-first (Phase D)</li>
        <li>Marti-AI integrace (Phase E)</li>
      </ul>
    </div>
    '''
    return _render_full_page(
        title="STRATEGIE ERP",
        content=content,
        breadcrumb=[],
        user_id=user_id,
    )


def _render_workspace_page(user_id: int) -> str:
    """
    Phase B production MVP (5.5.2026): 2-pane workspace + modal jádro detail.

    Layout:
      ┌─────────────┬────────────────────────────────────┐
      │ Sidebar     │ Main pane                          │
      │ (tree)      │ ┌──────────────────────────────┐   │
      │ EC_Centra-  │ │ Breadcrumb path              │   │
      │ laMenu      │ │ Title + meta                 │   │
      │ recursive   │ ├──────────────────────────────┤   │
      │ persistent  │ │ ErpDataGrid (AG Grid Ent)    │   │
      │ expand      │ │ Excel-like keyb, multi-sel   │   │
      │             │ │ Double-click → modal jádro   │   │
      │             │ └──────────────────────────────┘   │
      └─────────────┴────────────────────────────────────┘

    Features (deployed phases):
      - ErpDataGrid komponenta (AG Grid Enterprise, B+4 → default since B+4.3)
      - Excel-like UX (B+4.1): single-click select, Ctrl/Shift multi, double-click detail
      - Persistent expand state (localStorage erp.tree.expanded)
      - Persistent active selection (localStorage erp.tree.active)
      - Auto-restore last přehled on page load (incl. expand ancestors + scroll)
      - Breadcrumb path in main pane (Modul › Submodul › Přehled)
      - Retry buttons on fetch errors
      - Skeleton shimmer during loading
      - Fallback to plain HTML table if Tabulator CDN unreachable

    Tabulator pinned to @6 (latest 6.x) from jsdelivr CDN.
    """
    content = '''
    <!-- B+4.3 (5.5.2026): AG Grid Enterprise = jediný grid, Tabulator pohřben.
         ErpDataGrid komponenta (reusable napříč Centrála views) je default.
         Cache-busting via ?v=<API_start_timestamp> — každý restart = fresh download. -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/styles/ag-grid.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/styles/ag-theme-quartz.css">
    <script src="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/dist/ag-grid-enterprise.min.js"></script>
    <link rel="stylesheet" href="/static/erp/datagrid.css?v=''' + _STATIC_VERSION + '''">
    <script src="/static/erp/datagrid.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- B+10+ (6.5.2026): conditional formatting engine + UI editor -->
    <script src="/static/erp/datagrid_formatting.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- B+6.1+ (5.5.2026): ErpUiKit components — reusable napříč Centrála views -->
    <link rel="stylesheet" href="/static/erp/components/components.css?v=''' + _STATIC_VERSION + '''">
    <script src="/static/erp/components/button.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/input.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/checkbox.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/dropdown.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/date.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/memo.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- B+6.8 (6.5.2026 večer): ErpRichEdit (Ace Editor 1.32 z CDN, ~120KB,
         no-conflict UMD). Mode SQL + monokai theme. Marti's Centrála 1
         typ 4 RichEdit pro DefView SQL + INSERT/UPDATE/DELETE editory. -->
    <script src="https://cdn.jsdelivr.net/npm/ace-builds@1.32.6/src-min-noconflict/ace.js"></script>
    <script src="/static/erp/components/richedit.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- B+6.9 (6.5.2026 večer): ErpPageControl + ErpTabSheet (in-form tabs).
         Centrála 1 typ 15 PageControl + typ 16 TabSheet. -->
    <script src="/static/erp/components/pagecontrol.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/formlist.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/formsection.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/form.js?v=''' + _STATIC_VERSION + '''"></script>

    <div class="erp-workspace">
      <aside class="erp-tree-pane">
        <!-- B+7++++ (6.5.2026): tree header — collapse/expand button vpravo.
             B+10+++ (6.5.2026 Marti's drobnost): filter input přesunut sem
             (z .erp-tree-search row) — sjednocená řádka místo prázdné. -->
        <div class="erp-tree-header">
          <div class="erp-tree-search-inline">
            <input type="text" id="erpTreeSearch" class="erp-tree-search-input"
                   placeholder="🔍 Filtrovat strom…" autocomplete="off">
            <button type="button" id="erpTreeSearchClear" class="erp-tree-search-clear"
                    title="Vymazat filtr (Esc)" hidden>×</button>
          </div>
          <button type="button" id="erpTreeToggle" class="erp-tree-toggle-btn"
                  aria-label="Skrýt strom" title="Skrýt strom (Ctrl+B)">
            <span class="erp-tree-toggle-collapse">‹</span>
            <span class="erp-tree-toggle-expand">›</span>
          </button>
        </div>
        <div id="erpTreeRoot" class="erp-tree-root">
          <div class="erp-tree-skeleton">
            <div class="erp-skel-line"></div>
            <div class="erp-skel-line short"></div>
            <div class="erp-skel-line"></div>
            <div class="erp-skel-line short"></div>
            <div class="erp-skel-line"></div>
          </div>
        </div>
        <!-- B+8.2a (6.5.2026): 3-segment toggle pro tree view mode
             (Vše / Oblíbené / Naposledy použité) -->
        <div id="erpTreeFooter" class="erp-tree-footer">
          <div class="erp-tree-view-toggle" role="tablist">
            <button type="button" class="erp-tree-view-btn active"
                    data-tree-view="all" role="tab" title="Všechny moduly">
              <span class="erp-tree-view-icon">≡</span>
              <span class="erp-tree-view-label">Vše</span>
            </button>
            <button type="button" class="erp-tree-view-btn"
                    data-tree-view="favorites" role="tab" title="Oblíbené (pin přes pravý-klik)">
              <span class="erp-tree-view-icon">★</span>
              <span class="erp-tree-view-label">Oblíbené</span>
            </button>
            <button type="button" class="erp-tree-view-btn"
                    data-tree-view="recent" role="tab" title="Naposledy použité (auto-track)">
              <span class="erp-tree-view-icon">⏱</span>
              <span class="erp-tree-view-label">MRU</span>
            </button>
          </div>
        </div>
      </aside>
      <div id="erpResizeHandle" class="erp-resize-handle" role="separator" aria-label="Resize tree pane" title="Drag pro změnu šířky stromu"></div>
      <main class="erp-main-pane">
        <!-- B+8 (6.5.2026): tabs bar nad main-content (Centrála 1 multi-přehled pattern) -->
        <div id="erpTabsBar" class="erp-tabs-bar" hidden></div>
        <div id="erpMainContent" class="erp-main-content">
          <div class="erp-main-placeholder">
            <h2>Vyber přehled ze stromu vlevo</h2>
            <p>
              Klikni na uzel se symbolem <code>▶/▼</code> pro rozbalení.
              Listy stromu (modré) otevřou přehled vpravo. Klik na řádek
              přehledu otevře jádro v třetí pane vpravo (B+2).
            </p>
            <p style="margin-top: 12px; font-size: 12px;">
              <em>Phase B+2 — split-pane workspace, inline jádro detail.</em>
            </p>
          </div>
        </div>
      </main>
    </div>
    <!-- B+2.2: jádro modal — fixed overlay, mimo workspace grid -->
    <div id="erpJadroBackdrop" class="erp-jadro-backdrop" hidden></div>
    <aside id="erpJadroPane" class="erp-jadro-pane" hidden role="dialog" aria-modal="true" aria-labelledby="erpJadroTitle">
      <div class="erp-jadro-header">
        <span id="erpJadroTitle" class="erp-jadro-title">Jádro</span>
        <span id="erpJadroMeta" class="erp-jadro-meta"></span>
        <button id="erpJadroClose" class="erp-jadro-close" aria-label="Zavřít jádro" title="Zavřít jádro (Esc)">×</button>
      </div>
      <div id="erpJadroContent" class="erp-jadro-content"></div>
    </aside>

    <script>
    (function() {
      "use strict";
      const treeRoot = document.getElementById("erpTreeRoot");
      const mainContent = document.getElementById("erpMainContent");
      // B+2 → B+2.2 (5.5.2026): jádro modal popup elements
      const workspaceEl = document.querySelector(".erp-workspace");
      const jadroPane = document.getElementById("erpJadroPane");
      const jadroContent = document.getElementById("erpJadroContent");
      const jadroTitle = document.getElementById("erpJadroTitle");
      const jadroMeta = document.getElementById("erpJadroMeta");
      const jadroCloseBtn = document.getElementById("erpJadroClose");
      const jadroBackdrop = document.getElementById("erpJadroBackdrop");
      // B+2.1: resize handle pro tree width
      const resizeHandle = document.getElementById("erpResizeHandle");

      const EXPAND_KEY = "erp.tree.expanded";
      const ACTIVE_KEY = "erp.tree.active";
      const TREE_WIDTH_KEY = "erp.tree.width";

      let activeErpDataGrid = null;      // current ErpDataGrid component (B+4 → default since B+4.3)
      // B+5.2 smoke testing: expose getter na window pro DevTools console.
      // Použití: await erpGrid().listLayouts()  /  erpGrid().getCurrentColumnState()
      window.erpGrid = () => activeErpDataGrid;
      let nodeIndex = new Map();         // id -> {node, parentId} for fast path lookup
      let currentJadro = null;           // {form_id, row_id} of open jádro (B+2)
      const _ESC = {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"};

      // B+2.1: tree width persistence + drag-resize
      function loadTreeWidth() {
        try {
          const v = parseInt(localStorage.getItem(TREE_WIDTH_KEY), 10);
          return (v && v >= 160 && v <= 600) ? v : 240;
        } catch (e) { return 240; }
      }
      function saveTreeWidth(w) {
        try { localStorage.setItem(TREE_WIDTH_KEY, String(w)); } catch (e) {}
      }
      function applyTreeWidth(w) {
        const clamped = Math.max(160, Math.min(600, w));
        if (workspaceEl) workspaceEl.style.setProperty("--erp-tree-width", clamped + "px");
        saveTreeWidth(clamped);
        // B+4.3: AG Grid handles container resize natively (ResizeObserver),
        // žádný explicit redraw call potřeba.
        return clamped;
      }
      // Initial apply (load persisted)
      applyTreeWidth(loadTreeWidth());

      if (resizeHandle) {
        resizeHandle.addEventListener("mousedown", (ev) => {
          ev.preventDefault();
          const startX = ev.clientX;
          const startWidth = loadTreeWidth();
          resizeHandle.classList.add("dragging");
          document.body.style.cursor = "col-resize";
          document.body.style.userSelect = "none";

          function onMove(e) {
            const delta = e.clientX - startX;
            applyTreeWidth(startWidth + delta);
          }
          function onUp() {
            document.removeEventListener("mousemove", onMove);
            document.removeEventListener("mouseup", onUp);
            resizeHandle.classList.remove("dragging");
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
          }
          document.addEventListener("mousemove", onMove);
          document.addEventListener("mouseup", onUp);
        });
        // Double-click resets to default
        resizeHandle.addEventListener("dblclick", () => {
          applyTreeWidth(240);
        });
      }

      // ── localStorage helpers ─────────────────────────────────────
      function loadExpanded() {
        try { return new Set(JSON.parse(localStorage.getItem(EXPAND_KEY) || "[]")); }
        catch (e) { return new Set(); }
      }
      function saveExpanded(s) {
        try { localStorage.setItem(EXPAND_KEY, JSON.stringify([...s])); } catch (e) {}
      }
      function loadActive() { return localStorage.getItem(ACTIVE_KEY) || null; }
      function saveActive(cislo) {
        try {
          if (cislo != null && cislo !== "") localStorage.setItem(ACTIVE_KEY, String(cislo));
          else localStorage.removeItem(ACTIVE_KEY);
        } catch (e) {}
      }
      const expanded = loadExpanded();

      // ── Tree fetch + render ──────────────────────────────────────
      async function loadTree() {
        try {
          const r = await fetch("/api/v1/erp/strom", { credentials: "include" });
          if (!r.ok) { renderTreeError("Strom nelze načíst (status " + r.status + ")."); return; }
          const data = await r.json();
          if (!data.tree || data.tree.length === 0) {
            treeRoot.innerHTML = '<div class="erp-tree-empty">Strom prázdný.</div>';
            return;
          }
          nodeIndex = new Map();
          buildNodeIndex(data.tree, null);
          treeRoot.innerHTML = renderTreeNodes(data.tree, 0);
          attachTreeHandlers();
          tryRestoreActive();
        } catch (e) {
          renderTreeError("Chyba: " + (e.message || String(e)));
        }
      }

      function renderTreeError(msg) {
        treeRoot.innerHTML =
          '<div class="erp-tree-error">' + escapeHtml(msg) +
          '<button class="erp-retry-btn" id="erpTreeRetry">Zkusit znovu</button></div>';
        const btn = document.getElementById("erpTreeRetry");
        if (btn) btn.addEventListener("click", () => {
          treeRoot.innerHTML =
            '<div class="erp-tree-skeleton">' +
            '<div class="erp-skel-line"></div>' +
            '<div class="erp-skel-line short"></div>' +
            '<div class="erp-skel-line"></div>' +
            '</div>';
          loadTree();
        });
      }

      function buildNodeIndex(nodes, parentId) {
        for (const n of nodes) {
          nodeIndex.set(String(n.id), { node: n, parentId: parentId });
          if (n.children && n.children.length > 0) buildNodeIndex(n.children, String(n.id));
        }
      }

      function getPathForId(id) {
        const path = [];
        let cur = nodeIndex.get(String(id));
        while (cur) {
          path.unshift({
            id: String(cur.node.id),
            label: cur.node.menu_text,
            cislo_def: cur.node.cislo_def || null,
          });
          if (!cur.parentId) break;
          cur = nodeIndex.get(cur.parentId);
        }
        return path;
      }

      function renderTreeNodes(nodes, depth) {
        let html = '<ul class="erp-tree-list">';
        for (const n of nodes) {
          const nid = String(n.id);
          const hasChildren = n.children && n.children.length > 0;
          const hasPrehled = n.cislo_def != null;
          // Phase 35-E.4 (9.5.2026): System soudečky (id starts with 'system')
          // mají vlastní render path — klik redirectuje na audit-dashboard.
          const isSystem = n.is_system === true;
          const isSystemLeaf = isSystem && n.system_view;  // sub-uzel s view
          let cls = hasPrehled ? "erp-tree-leaf" : "erp-tree-folder";
          if (isSystem) cls += " erp-tree-system";
          if (isSystemLeaf) cls += " erp-tree-system-leaf";
          const isExpanded = hasChildren && expanded.has(nid);
          const toggle = hasChildren
            ? '<span class="erp-tree-toggle">' + (isExpanded ? "▼" : "▶") + '</span>'
            : '<span class="erp-tree-spacer"></span>';
          const ico = n.ikona ? '<span class="erp-tree-ico">' + (n.ikona % 100) + '</span>' : '';
          // Pro System nody použij label místo menu_text
          const _label = (n.label || n.menu_text || n.nazev || '?');
          // System data attributes pro click handler
          // Phase 35-E.4 Variant B: single=1 flag — leaf node renderuje
          // jen daný view (žádné tabs).
          const sysAttrs = isSystemLeaf
            ? ' data-system-view="' + (n.system_view || '') +
              '" data-system-view-mode="' + (n.system_view_mode || '') +
              '" data-system-single="' + (n.single ? '1' : '0') + '"'
            : '';
          html += '<li class="erp-tree-item ' + cls + '" data-id="' + nid +
                  '" data-cislo-def="' + (n.cislo_def || '') +
                  '" data-text="' + escapeAttr(_label) +
                  (isSystem ? '" data-is-system="1' : '') +
                  sysAttrs + '">';
          html += '<div class="erp-tree-row" style="padding-left: ' + (depth * 16) + 'px;">';
          html += toggle + ico + '<span class="erp-tree-label">' + escapeHtml(_label) + '</span>';
          html += '</div>';
          if (hasChildren) {
            html += '<div class="erp-tree-children" style="display: ' +
                    (isExpanded ? "block" : "none") + ';">' +
                    renderTreeNodes(n.children, depth + 1) + '</div>';
          }
          html += '</li>';
        }
        html += '</ul>';
        return html;
      }

      function attachTreeHandlers() {
        treeRoot.querySelectorAll(".erp-tree-row").forEach(row => {
          row.addEventListener("click", (ev) => {
            const item = row.closest(".erp-tree-item");
            if (!item) return;
            const nid = item.getAttribute("data-id");

            // B+8.2a+ (6.5.2026): Ctrl/Cmd+klik = jen vybrat (multi-select),
            // ne otevřít. Pro context-menu bulk akce.
            if (ev.ctrlKey || ev.metaKey) {
              ev.preventDefault();
              const cisloDef = item.getAttribute("data-cislo-def");
              if (cisloDef) {
                _toggleTreeSelection(item);
              }
              return;
            }

            // B+8.2a+++++++ (6.5.2026): klik na ▶/▼ toggle = JEN expand/collapse,
            // bez otevření přehledu. Marti's UX feedback: "sipka NESMI zaroven
            // otevirat ten prehled" (jinak user pri exploraci stromu zaplní MRU).
            const toggleClicked = ev.target.closest(".erp-tree-toggle");

            // Klasický klik bez modifikátorů — clear selection
            _clearTreeSelection();

            const childrenWrap = item.querySelector(":scope > .erp-tree-children");
            const toggle = row.querySelector(".erp-tree-toggle");
            // Expand/collapse if has children
            if (childrenWrap) {
              const isOpen = childrenWrap.style.display !== "none";
              childrenWrap.style.display = isOpen ? "none" : "block";
              if (toggle) toggle.textContent = isOpen ? "▶" : "▼";
              if (isOpen) expanded.delete(nid); else expanded.add(nid);
              saveExpanded(expanded);
            }
            // Phase 35-E.4 Variant B (9.5.2026): System leaf node →
            // inline iframe v main pane (no redirect, čistá izolace JS).
            if (!toggleClicked) {
              const sysViewMode = item.getAttribute("data-system-view-mode");
              if (sysViewMode) {
                _renderSystemViewInline(sysViewMode, item);
                return;
              }
            }
            // Load přehled JEN POKUD klik nebyl na toggle šipku
            if (!toggleClicked) {
              const cisloDef = item.getAttribute("data-cislo-def");
              if (cisloDef && cisloDef !== "") {
                setActive(item, parseInt(cisloDef, 10));
              }
            }
          });
        });
      }

      // B+8.2a+ (6.5.2026): tree row selection (Ctrl+klik bez otevření)
      const _selectedTreeCislos = new Set();
      function _clearTreeSelection() {
        _selectedTreeCislos.clear();
        if (!treeRoot) return;
        treeRoot.querySelectorAll(".erp-tree-row.erp-tree-selected").forEach(r => {
          r.classList.remove("erp-tree-selected");
        });
      }
      function _toggleTreeSelection(item) {
        const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
        if (!cislo) return;
        const row = item.querySelector(":scope > .erp-tree-row");
        if (!row) return;
        if (_selectedTreeCislos.has(cislo)) {
          _selectedTreeCislos.delete(cislo);
          row.classList.remove("erp-tree-selected");
        } else {
          _selectedTreeCislos.add(cislo);
          row.classList.add("erp-tree-selected");
        }
      }
      function _selectTreeRow(item) {
        // single (non-additive) — clear pak select
        _clearTreeSelection();
        _toggleTreeSelection(item);
      }

      function setActive(item, cislo) {
        treeRoot.querySelectorAll(".erp-tree-row.active").forEach(r => r.classList.remove("active"));
        const row = item.querySelector(":scope > .erp-tree-row");
        if (row) row.classList.add("active");
        saveActive(String(cislo));
        // Phase 35-E.4 Variant B: pokud byla active System view, restore
        // standard workspace (hide iframe wrapper, show tabs bar).
        _restoreFromSystemView();
        // B+8 (6.5.2026): místo loadPrehled → openTab (multi-tab pattern)
        openTab(cislo, item);
      }

      // Phase 35-E.4 Variant B (9.5.2026): inline iframe render System view
      // v ERP main pane. Marti's vize "koukat na to shora v ERP context" —
      // dashboard se otevre přímo místo přehled tabů, sidebar zustane.
      function _renderSystemViewInline(mode, item) {
        // PHASE 35-E.4 Variant B (9.5.2026 ROLLBACK): docasne vsech 4 mode
        // pres iframe dashboard, dokud nediagnostikujeme parse error v
        // native AG Grid varianta. Pak progressivne pridame zpet.
        const tabsBar = document.getElementById("erpTabsBar");
        const main = document.getElementById("erpMainContent");
        if (!main) return;

        if (tabsBar) {
          tabsBar.dataset.systemHidden = tabsBar.hidden ? "1" : "0";
          tabsBar.hidden = true;
        }

        treeRoot.querySelectorAll(".erp-tree-row.active").forEach(function(r) { r.classList.remove("active"); });
        if (item) {
          const row = item.querySelector(":scope > .erp-tree-row");
          if (row) row.classList.add("active");
        }

        const single = (item && item.getAttribute("data-system-single") === "1") ? 1 : 0;

        main.dataset.systemView = mode;
        main.innerHTML =
          '<iframe src="/erp/system/audit-dashboard?embed=1&single=' + single +
          '&mode=' + mode +
          '" style="width:100%;height:100%;border:0;background:var(--bg);display:block" ' +
          'title="Audit dashboard"></iframe>';

        try {
          const labelEl = item ? item.querySelector(":scope > .erp-tree-row > .erp-tree-label") : null;
          const lbl = labelEl ? labelEl.textContent : "Audit";
          document.title = "STRATEGIE - " + lbl;
        } catch (e) {}
      }

      // Phase 35-E.4 Variant B helpers (rolled back 9.5. - parse error diag).
      // Restore po lokalizaci.
      /* DOCASNE ZAKOMENTOVANE - DIAG PARSE ERROR
      async function _renderSystemGrid(mode, item) {
        const main = document.getElementById("erpMainContent");
        if (!main) return;
        const labelEl = item ? item.querySelector(":scope > .erp-tree-row > .erp-tree-label") : null;
        const lbl = labelEl ? labelEl.textContent : mode;

        main.innerHTML =
          '<div class="erp-system-grid-wrap" style="display:flex;flex-direction:column;height:100%;background:var(--bg);">' +
            '<div class="erp-system-grid-header" style="padding:8px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:14px;font-size:13px;color:var(--fg);background:var(--bg-soft,#1a1f24);">' +
              '<span style="font-weight:600;font-size:14px">' + escapeHtml(lbl) + '</span>' +
              '<span id="erpSysGridCount" style="opacity:0.6;font-size:11px"></span>' +
            '</div>' +
            '<div id="erpSysGridBody" style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;color:var(--muted);">Načítám…</div>' +
          '</div>';

        let data;
        try {
          const url = "/api/v1/erp/system/audit-overview?mode=" + encodeURIComponent(mode);
          const res = await fetch(url, { credentials: "include" });
          if (!res.ok) {
            const txt = await res.text();
            const body = document.getElementById("erpSysGridBody");
            if (body) body.innerHTML = '<div style="color:#f88">Chyba ' + res.status + ': ' + escapeHtml(txt.substring(0, 200)) + '</div>';
            return;
          }
          data = await res.json();
        } catch (e) {
          const body = document.getElementById("erpSysGridBody");
          if (body) body.innerHTML = '<div style="color:#f88">Chyba: ' + escapeHtml(String(e)) + '</div>';
          return;
        }

        const body = document.getElementById("erpSysGridBody");
        if (!body) return;
        body.innerHTML = "";
        body.style.alignItems = "stretch";
        body.style.justifyContent = "stretch";

        const gridDiv = document.createElement("div");
        gridDiv.className = "ag-theme-quartz";
        gridDiv.setAttribute("data-ag-theme-mode", "dark");
        gridDiv.style.cssText = "width:100%;height:100%;min-height:480px";
        body.appendChild(gridDiv);

        const columns = _systemGridColumns(mode);
        const rowData = (mode === "stats") ? (data.rows || []) : (data.conversations || []);

        const opts = {
          columnDefs: columns,
          rowData: rowData,
          defaultColDef: { resizable: true, sortable: true, filter: true },
          onRowClicked: (e) => _showSystemRowDetail(mode, e.data),
          domLayout: "normal",
          animateRows: true,
          rowHeight: 32,
        };

        // eslint-disable-next-line no-undef
        agGrid.createGrid(gridDiv, opts);

        const cntEl = document.getElementById("erpSysGridCount");
        if (cntEl) cntEl.textContent = rowData.length + " řádků";
      }

      function _systemGridColumns(mode) {
        if (mode === "stats") {
          return [
            { headerName: "Persona", field: "persona_name", width: 200, sortable: true, pinned: "left" },
            { headerName: "Období", field: "period", width: 110, sortable: true, sort: "desc" },
            { headerName: "Pending", field: "pending", width: 100, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#888" } : null; } },
            { headerName: "In progress", field: "in_progress", width: 110, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#d4a017" } : null; } },
            { headerName: "Auditované", field: "audited", width: 120, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#6aa84f", fontWeight: "500" } : null; } },
            { headerName: "Excluded", field: "excluded", width: 110, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#666" } : null; } },
            { headerName: "Celkem", field: "total", width: 110, sortable: true, type: "numericColumn",
              cellStyle: { fontWeight: "600" } },
          ];
        }
        // audited / all
        const showStatus = (mode === "all");
        const cols = [
          { headerName: "ID", field: "id", width: 80, sortable: true, pinned: "left" },
        ];
        if (showStatus) {
          cols.push({
            headerName: "Status", field: "audit_status", width: 120, sortable: true,
            cellRenderer: (p) => _systemStatusBadge(p.value || "—"),
          });
        }
        cols.push(
          { headerName: "Title", field: "title", flex: 2, minWidth: 200, sortable: true },
          { headerName: "Tenant", field: "tenant_name", width: 130, sortable: true },
          { headerName: "Auditováno", field: "audited_at", width: 160, sortable: true,
            valueFormatter: (p) => _formatDateRel(p.value) },
          { headerName: "Persona", field: "audited_by_persona_name", width: 130 },
          { headerName: "Scope", field: "scope", width: 110,
            cellRenderer: (p) => _scopeIconHtml(p.value) },
          { headerName: "Last msg", field: "last_message_at", width: 160, sortable: true,
            valueFormatter: (p) => _formatDateRel(p.value) },
          { headerName: "Thoughts", field: "thought_count", width: 100, sortable: true,
            cellRenderer: (p) => p.value > 0 ? "📝 " + p.value : "—" },
          { headerName: "Lifecycle", field: "lifecycle_state", width: 110 },
        );
        return cols;
      }

      function _systemStatusBadge(v) {
        const colors = {
          pending: "#888", in_progress: "#d4a017",
          audited: "#6aa84f", excluded: "#666",
        };
        const labels = {
          pending: "pending", in_progress: "in progress",
          audited: "✓ audited", excluded: "excluded",
        };
        const c = colors[v] || "#888";
        const lbl = labels[v] || v;
        return '<span style="background:' + c + '22;color:' + c +
               ';padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500">' +
               escapeHtml(lbl) + '</span>';
      }

      function _scopeIconHtml(v) {
        if (v === "srdce") return '<span style="color:#e08aa8">💗 srdce</span>';
        if (v === "general") return '<span style="opacity:0.7">general</span>';
        return v ? escapeHtml(v) : '<span style="opacity:0.4">—</span>';
      }

      function _formatDateRel(iso) {
        if (!iso) return "—";
        try {
          const d = new Date(iso);
          return d.toLocaleString("cs-CZ", { dateStyle: "short", timeStyle: "short" });
        } catch (e) { return iso; }
      }

      function _showSystemRowDetail(mode, row) {
        // Phase 35-E.4 next iteration TODO (Marti's "Pozdeji Popup"):
        //  - audited / all → modal s plnou konverzací (read-only render messages,
        //    audit_notes summary, persona kdo auditoval, extracted_thought_ids).
        //  - stats → ne-otvírat (per-persona × per-měsíc row je summary).
        if (mode === "stats") return;
        if (!row || !row.id) return;
        // Placeholder: budoucí popup. Zatím alert s metadaty pro feedback.
        const lines = [
          "Konverzace #" + row.id,
          "",
          "Title: " + (row.title || "—"),
          "Status: " + (row.audit_status || "—"),
          "Tenant: " + (row.tenant_name || "—"),
          "Persona: " + (row.audited_by_persona_name || "—"),
          "Scope: " + (row.scope || "—"),
          "Auditováno: " + (row.audited_at || "—"),
          "Last msg: " + (row.last_message_at || "—"),
          "Thoughts: " + (row.thought_count || 0),
          "",
          "Popup s plnou konverzací bude v dalsi iteraci.",
        ];
        alert(lines.join("\n"));
      }
      */

      function _restoreFromSystemView() {
        const main = document.getElementById("erpMainContent");
        const tabsBar = document.getElementById("erpTabsBar");
        if (!main || !main.dataset.systemView) return;
        // Byla active System view — restore tabs bar (pokud byl visible)
        delete main.dataset.systemView;
        if (tabsBar && tabsBar.dataset.systemHidden === "0") {
          tabsBar.hidden = false;
        }
        // Iframe odstraní switchTab → render přehled, který nahradí innerHTML
      }

      function tryRestoreActive() {
        // B+8 (6.5.2026): tabs state má vlastní restore (restoreTabsFromStorage).
        // Tato funkce zachována pro tree highlight + scrollIntoView ale neotevírá
        // přehled — to dělá tab restore (s itemId resolve z stromu).
        const cislo = loadActive();
        if (!cislo) return;
        const item = treeRoot.querySelector('.erp-tree-item[data-cislo-def="' + cislo + '"]');
        if (!item) return;
        const row = item.querySelector(":scope > .erp-tree-row");
        if (row) row.classList.add("active");
        expandAncestors(item);
        if (row && row.scrollIntoView) {
          try { row.scrollIntoView({ block: "nearest" }); } catch (e) {}
        }
        // Pokud nejsou žádné persisted tabs, otevři podle aktivního tree node
        const persisted = loadTabsState();
        if (!persisted || !persisted.tabs || persisted.tabs.length === 0) {
          openTab(parseInt(cislo, 10), item);
        }
      }

      function expandAncestors(item) {
        let cur = item;
        while (cur) {
          const ul = cur.parentElement;
          if (!ul) break;
          const wrap = ul.parentElement;
          if (!wrap || !wrap.classList || !wrap.classList.contains("erp-tree-children")) break;
          wrap.style.display = "block";
          const parentItem = wrap.parentElement;
          if (!parentItem || !parentItem.classList.contains("erp-tree-item")) break;
          const tg = parentItem.querySelector(":scope > .erp-tree-row > .erp-tree-toggle");
          if (tg) tg.textContent = "▼";
          expanded.add(parentItem.getAttribute("data-id"));
          cur = parentItem;
        }
        saveExpanded(expanded);
      }

      // ── Breadcrumb ──────────────────────────────────────────────
      function buildBreadcrumbHtml(itemId) {
        const path = getPathForId(itemId);
        if (path.length === 0) return '';
        const parts = path.map((p, i) => {
          const isLast = (i === path.length - 1);
          return '<span class="erp-bc-step' + (isLast ? ' current' : '') + '">' +
                 escapeHtml(p.label) + '</span>';
        });
        return parts.join('<span class="erp-bc-sep">›</span>');
      }

      // ── Přehled fetch + Tabulator render ────────────────────────
      // B+4.4: per-přehled limit choice persisted v localStorage
      const PREHLED_LIMIT_KEY_PREFIX = "erp.prehled.limit.";
      function loadPrehledLimit(cislo) {
        try {
          const v = parseInt(localStorage.getItem(PREHLED_LIMIT_KEY_PREFIX + cislo), 10);
          return (v && v > 0) ? v : null;
        } catch (e) { return null; }
      }
      function savePrehledLimit(cislo, limit) {
        try {
          if (limit && limit > 0) localStorage.setItem(PREHLED_LIMIT_KEY_PREFIX + cislo, String(limit));
          else localStorage.removeItem(PREHLED_LIMIT_KEY_PREFIX + cislo);
        } catch (e) {}
      }

      async function loadPrehled(cislo, item, limitOverride) {
        // B+2: auto-close jádro pane (jiný přehled = jiný kontext)
        if (currentJadro) closeJadroPane();
        const itemId = item.getAttribute("data-id");
        const breadcrumb = buildBreadcrumbHtml(itemId);
        mainContent.innerHTML =
          '<div class="erp-prehled-header">' +
          '<div class="erp-bc-path">' + breadcrumb + '</div>' +
          '<div class="erp-prehled-loading">' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line short"></div>' +
          '</div>' +
          '<div class="erp-prehled-loading-msg">Načítám přehled #' + cislo + '…</div>' +
          '</div>';
        // B+4.4: limit precedence — explicit override > localStorage > server default
        const userLimit = (limitOverride != null && limitOverride > 0)
          ? limitOverride
          : loadPrehledLimit(cislo);
        const url = userLimit
          ? ("/api/v1/erp/prehled/" + cislo + "?limit=" + userLimit)
          : ("/api/v1/erp/prehled/" + cislo);
        try {
          const r = await fetch(url, { credentials: "include" });
          if (!r.ok) { renderPrehledError(cislo, item, "Status " + r.status); return; }
          const data = await r.json();
          renderPrehled(cislo, item, data, breadcrumb);
        } catch (e) {
          renderPrehledError(cislo, item, e.message || String(e));
        }
      }

      function renderPrehledError(cislo, item, msg) {
        const itemId = item.getAttribute("data-id");
        const breadcrumb = buildBreadcrumbHtml(itemId);
        mainContent.innerHTML =
          '<div class="erp-prehled-header"><div class="erp-bc-path">' + breadcrumb + '</div></div>' +
          '<div class="erp-main-error">' +
          'Přehled #' + cislo + ' nelze načíst: ' + escapeHtml(msg) +
          '<button class="erp-retry-btn" id="erpPrehledRetry">Zkusit znovu</button>' +
          '</div>';
        const btn = document.getElementById("erpPrehledRetry");
        if (btn) btn.addEventListener("click", () => loadPrehled(cislo, item));
      }

      function renderPrehled(cislo, item, data, breadcrumb) {
        // B+4.3: vše přes ErpDataGrid komponentu (AG Grid Enterprise wrapper)
        if (activeErpDataGrid) {
          try { activeErpDataGrid.destroy(); } catch (e) {}
          activeErpDataGrid = null;
        }

        const cols = data.columns || [];
        const rows = data.rows || [];

        // B+10++ (Marti's drobnost 6.5.2026): limit options pro status bar.
        // 4 hodnoty (1000, 10000, 50000, vše=100k). Limit selector v hlavičce
        // smazán — celý <div class="erp-prehled-meta"> přesunut do footer
        // gridu jako interaktivní "Celkem" v status baru. (limit, má víc)
        // taky teď v status baru, oranžově zvýrazněno.
        const appliedLimit = data.applied_limit || rows.length;
        const limitOptions = [1000, 10000, 50000, 100000];

        // B+10+++ (Marti's drobnost 6.5.2026): celá .erp-prehled-header
        // smazána — název přehledu je v active tabu, breadcrumb v title
        // (document.title = "STRATEGIE | <přehled>"). Tabs visually těsně
        // nad gridem, žádný extra prostor.
        let html = '';
        if (data.warning) html += '<div class="erp-prehled-warning">⚠ ' + escapeHtml(data.warning) + '</div>';

        if (rows.length === 0) {
          html += '<div class="erp-prehled-empty">Přehled je prázdný.</div>';
          mainContent.innerHTML = html;
          return;
        }

        // ErpDataGrid komponenta (B+4 → default since B+4.3)
        html += '<div id="erpDataGridContainer" class="erp-ag-grid ag-theme-quartz-dark"></div>';
        mainContent.innerHTML = html;
        if (typeof window.ErpDataGrid === "undefined") {
          mainContent.innerHTML = html +
            '<div class="erp-main-error">ErpDataGrid komponenta se nenačetla — refresh stránky.</div>';
          return;
        }
        const container = document.getElementById("erpDataGridContainer");
        activeErpDataGrid = new window.ErpDataGrid(container, {
          rowData: rows,
          columns: cols,
          autoColumns: true,
          layoutKey: "prehled_" + cislo,  // B+5 grid layout persistence (TODO)
          // B+10++ (Marti's drobnost 6.5.2026): limit context pro status bar.
          // Status panel renderuje "Celkem" oranzove kdyz hasMore=true a klik
          // otevre dropdown s options (1k/10k/50k/Vse). Stejny user flow jako
          // header limit select, jen z paticky gridu.
          limitContext: {
            applied: appliedLimit,
            hasMore: !!data.has_more,
            options: limitOptions,
            onChange: (newLimit) => {
              if (!newLimit || newLimit <= 0) return;
              savePrehledLimit(cislo, newLimit);
              loadPrehled(cislo, item, newLimit);
            },
          },
          // MVP standard 5.5.2026: single click = select (Ctrl/Shift multi),
          // double click = open jádro detail. Šipky pouze navigují (Excel-like).
          onRowDoubleClick: (rowData) => {
            const rowId = rowData.ID != null ? rowData.ID : (rowData.id != null ? rowData.id : null);
            if (rowId == null || data.id_edit == null) return;
            openJadroInPane(data.id_edit, rowId);
          },
        });

        // B+10++ (6.5.2026 Marti's drobnost): limit selector v hlavičce
        // smazán — interakce teď přes status bar Celkem (CzRowCountStatusPanel
        // limitContext.onChange v ErpDataGrid options).
      }

      // ── Phase B+2.2: jádro modal popup (centered overlay) ───────
      // ── Phase B+6.6c (6.5.2026): JSON metadata + ErpForm orchestrator
      // (auto-render přes UI Kit komponenty, klient-side state pro Phase C)
      let currentJadroForm = null;  // ErpForm instance pro destroy na close
      async function openJadroInPane(formId, rowId) {
        if (!jadroPane || !jadroContent) return;
        currentJadro = { form_id: formId, row_id: rowId };
        // Cleanup předchozí instance
        if (currentJadroForm) {
          try { currentJadroForm.destroy(); } catch (e) {}
          currentJadroForm = null;
        }
        if (jadroBackdrop) jadroBackdrop.removeAttribute("hidden");
        jadroPane.removeAttribute("hidden");
        if (jadroTitle) jadroTitle.textContent = "Načítám jádro…";
        if (jadroMeta) jadroMeta.textContent = "#" + formId + " / " + rowId;
        jadroContent.innerHTML =
          '<div class="erp-jadro-loading">' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line short"></div>' +
          '</div>';
        try {
          const r = await fetch(
            "/api/v1/erp/jadro/" + encodeURIComponent(formId) + "/" +
              encodeURIComponent(rowId) + "/data",
            { credentials: "include" }
          );
          if (!r.ok) {
            const txt = await r.text().catch(() => "");
            jadroContent.innerHTML =
              '<div class="erp-jadro-error">' +
              'Status ' + r.status +
              (txt ? ' — ' + escapeHtml(txt.slice(0, 200)) : '') +
              '</div>';
            if (jadroTitle) jadroTitle.textContent = "Chyba";
            return;
          }
          const meta = await r.json();
          if (!meta || !meta.ok) {
            jadroContent.innerHTML =
              '<div class="erp-jadro-error">Backend vrátil ' +
              'ok=false: ' + escapeHtml(JSON.stringify(meta).slice(0, 240)) +
              '</div>';
            if (jadroTitle) jadroTitle.textContent = "Chyba";
            return;
          }

          // Title — preferuj FormSetting.FormCaption, pak FormDef.Nazev
          let title = (meta.form && meta.form.nazev) || ("Jádro #" + formId);
          if (Array.isArray(meta.components)) {
            for (const c of meta.components) {
              if (c.typ === 30 && c.properties && c.properties.FormCaption) {
                const fc = String(c.properties.FormCaption).trim();
                if (fc) { title = fc; break; }
              }
            }
          }
          if (jadroTitle) jadroTitle.textContent = title;

          // Build form přes ErpForm orchestrator
          if (typeof window.ErpForm !== "function") {
            jadroContent.innerHTML =
              '<div class="erp-jadro-error">' +
              'ErpForm komponenta se nenačetla — refresh stránky.' +
              '</div>';
            return;
          }
          jadroContent.innerHTML = "";
          currentJadroForm = new window.ErpForm(jadroContent, {
            formId: meta.form_id,
            formNazev: meta.form && meta.form.nazev,
            components: meta.components || [],
            data: meta.data || {},
            readOnly: true,  // Phase A — Phase C otevře pro edit
            onChange: (fieldName, newVal, oldVal) => {
              // Per-field change — toast info pro Phase A
              jadroToast(
                "Změna " + fieldName + " lokálně. " +
                "Uloží se s tlačítkem OK (Phase C)."
              );
            },
            debugInfo: meta.debug,
          });
        } catch (e) {
          jadroContent.innerHTML =
            '<div class="erp-jadro-error">Nelze načíst: ' +
            escapeHtml(e.message || String(e)) + '</div>';
          if (jadroTitle) jadroTitle.textContent = "Chyba";
        }
      }

      // ── DEAD CODE — B+6.4+ post-render hook nahrazen ErpForm
      // orchestratorem (B+6.6 6.5.2026). ErpForm staví ErpFormList
      // přímo z metadat a používá LookupField property pro sibling
      // hide + FK sync. Tyto funkce nikdo nevolá; smaž v cleanup
      // commitu, zatím ponecháno pro reference.
      // ──────────────────────────────────────────────────────────────
      function wireJadroLookups(rootEl) {
        if (!rootEl || typeof window.ErpFormList !== "function") return;
        const formEl = rootEl.querySelector(".erp-form[data-erp-form-id]");
        if (!formEl) return;
        const formId = formEl.dataset.erpFormId;
        if (!formId) return;
        const fields = rootEl.querySelectorAll('[data-erp-lookup]');
        fields.forEach((fieldEl) => {
          const fieldName = fieldEl.dataset.erpFieldName || "";
          const currentFk = fieldEl.dataset.erpFkValue || "";
          const currentDisplay = fieldEl.dataset.erpDisplay || "";
          const labelEl = fieldEl.querySelector(".erp-field-label");
          const labelText = labelEl ? labelEl.textContent : "";
          if (!fieldName) return;
          // Skrýt original label + input+button row, vložit ErpFormList mount
          const innerEl = fieldEl.querySelector(".erp-formlist-inner");
          if (innerEl) innerEl.style.display = "none";
          if (labelEl) labelEl.style.display = "none";
          const mount = document.createElement("div");
          mount.className = "erp-lookup-mount";
          fieldEl.appendChild(mount);

          // B+6.4+++ (5.5.2026): schovat sourozenecký FK Edit field
          // (pokud existuje). FK value je teď viditelně uvnitř ErpFormList,
          // separátní Edit pole = duplikát. Heuristic: stejný .erp-fields
          // grid container, .erp-field který není .erp-formlist, jehož
          // input.value matchne FK string.
          hideSiblingFkField(fieldEl, currentFk);

          // Lazy load při prvním focus / open / browse
          let loaded = false;
          const loadItems = async () => {
            if (loaded) return [];
            loaded = true;
            try {
              const r = await fetch(
                "/api/v1/erp/jadro/" + encodeURIComponent(formId) +
                  "/lookup/" + encodeURIComponent(fieldName),
                { credentials: "include" }
              );
              if (!r.ok) {
                console.warn("Lookup options fetch", fieldName, r.status);
                return [];
              }
              const j = await r.json();
              if (!j.ok || !Array.isArray(j.items)) return [];
              return j.items;
            } catch (e) {
              console.warn("Lookup load error", fieldName, e);
              return [];
            }
          };

          new window.ErpFormList(mount, {
            label: labelText,  // re-render label uvnitř ErpFormList
            value: currentFk || null,
            displayValue: currentDisplay || "",
            items: [],   // empty initial — onLoadItems naplní
            placeholder: "Začni psát nebo klikni na ⋮",
            onLoadItems: loadItems,
            // B+6.4++ (5.5.2026): klíč (FK) viditelně uvnitř komponenty
            // — Marti's spec, hodnota co se zapisuje do DB při Phase C OK
            showValuePrefix: true,
            valuePrefixWidth: "60px",
            browseTitle: labelText
              ? ("Vybrat hodnotu — " + labelText)
              : "Vybrat hodnotu",
            browseColumns: [
              { field: "value", header: "Číslo", width: "100px" },
              { field: "label", header: "Název", width: "auto" },
            ],
            onChange: (val, item) => {
              fieldEl.dataset.erpFkValue = String(val);
              const lbl = (item && item.label) ? item.label : String(val);
              fieldEl.dataset.erpDisplay = lbl;
              jadroToast(
                "Hodnota změněna lokálně. Uloží se s tlačítkem OK (Phase C)."
              );
            },
          });
        });
      }

      // B+6.4+++ (5.5.2026): schovat sourozenecký FK field
      function hideSiblingFkField(formListEl, fkValue) {
        if (!fkValue) return;
        // Container priorita: .erp-fields grid > .erp-group
        const container =
          formListEl.closest(".erp-fields") ||
          formListEl.closest(".erp-group");
        if (!container) return;
        // Hledej sibling .erp-field ktere NENI .erp-formlist (tj. neni
        // jiny lookup picker) a JEŠTĚ NENÍ schovany. Match na input.value.
        const fkStr = String(fkValue).trim();
        const candidates = container.querySelectorAll(
          ".erp-field:not(.erp-formlist):not([data-erp-hidden-sibling])"
        );
        for (const sib of candidates) {
          if (sib === formListEl) continue;
          // Pole je obvykle [label][input], hledame input s textovou
          // hodnotou (Edit Typ=2 pro FK ID je readonly text).
          const input = sib.querySelector('input[type="text"]');
          if (!input) continue;
          if (String(input.value).trim() === fkStr) {
            sib.style.display = "none";
            sib.setAttribute("data-erp-hidden-sibling", "true");
            break;  // jen první match — viz odkaz vyse
          }
        }
      }

      function jadroToast(msg) {
        const t = document.createElement("div");
        t.className = "erp-jadro-toast";
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => { t.classList.add("erp-jadro-toast-show"); }, 10);
        setTimeout(() => {
          t.classList.remove("erp-jadro-toast-show");
          setTimeout(() => { t.remove(); }, 240);
        }, 2400);
      }

      function closeJadroPane() {
        // B+6.6c (6.5.2026): destroy ErpForm + uvolni FormList instances
        if (currentJadroForm) {
          try { currentJadroForm.destroy(); } catch (e) {}
          currentJadroForm = null;
        }
        if (jadroPane) jadroPane.setAttribute("hidden", "");
        if (jadroBackdrop) jadroBackdrop.setAttribute("hidden", "");
        if (jadroContent) jadroContent.innerHTML = "";
        currentJadro = null;
        // B+2.2: workspace nemění layout (jádro je modal), žádný Tabulator redraw
      }

      if (jadroCloseBtn) {
        jadroCloseBtn.addEventListener("click", closeJadroPane);
      }
      // B+2.2: backdrop click → close
      if (jadroBackdrop) {
        jadroBackdrop.addEventListener("click", closeJadroPane);
      }
      // Esc key zavře jádro modal
      document.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape" && currentJadro) {
          closeJadroPane();
        }
      });

      // ── Helpers ─────────────────────────────────────────────────
      function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => _ESC[c]); }
      function escapeAttr(s) { return escapeHtml(s).replace(/"/g, "&quot;"); }

      // ── B+7++ (6.5.2026): tree search filter ────────────────────
      const treeSearchInput = document.getElementById("erpTreeSearch");
      const treeSearchClear = document.getElementById("erpTreeSearchClear");

      function _normalizeSearch(s) {
        // Case-insensitive + diakritika strip
        return String(s || "").toLowerCase()
          .normalize("NFD").replace(/[̀-ͯ]/g, "");
      }

      function applyTreeFilter(text) {
        if (!treeRoot) return;
        const norm = _normalizeSearch(text || "").trim();
        // Vymaž předchozí highlights + flags
        const allItems = treeRoot.querySelectorAll(".erp-tree-item");
        const allRows = treeRoot.querySelectorAll(".erp-tree-row");
        allRows.forEach(r => {
          r.classList.remove(
            "erp-tree-match",
            "erp-tree-match-parent",
            "erp-tree-match-descendant"
          );
          // Restore original label text (remove <mark>)
          const lbl = r.querySelector(".erp-tree-label");
          if (lbl && lbl.dataset.erpOrigText) {
            lbl.textContent = lbl.dataset.erpOrigText;
          }
        });
        if (!norm) {
          treeRoot.classList.remove("erp-tree-filtering");
          if (treeSearchClear) treeSearchClear.setAttribute("hidden", "");
          return;
        }
        treeRoot.classList.add("erp-tree-filtering");
        if (treeSearchClear) treeSearchClear.removeAttribute("hidden");
        // Match: pro každý item, check menu_text contains norm
        const matchingItems = [];
        allItems.forEach(item => {
          const text = item.dataset.text || "";
          const labelEl = item.querySelector(".erp-tree-row .erp-tree-label");
          if (!labelEl) return;
          // Save original text pro restore
          if (!labelEl.dataset.erpOrigText) {
            labelEl.dataset.erpOrigText = labelEl.textContent;
          }
          const normText = _normalizeSearch(text);
          const matchIdx = normText.indexOf(norm);
          if (matchIdx >= 0) {
            const rowEl = item.querySelector(":scope > .erp-tree-row");
            if (rowEl) rowEl.classList.add("erp-tree-match");
            matchingItems.push(item);
            // Highlight match v label
            const orig = labelEl.dataset.erpOrigText;
            const before = orig.slice(0, matchIdx);
            const match = orig.slice(matchIdx, matchIdx + norm.length);
            const after = orig.slice(matchIdx + norm.length);
            labelEl.innerHTML = escapeHtml(before) +
              "<mark>" + escapeHtml(match) + "</mark>" +
              escapeHtml(after);
          }
        });
        // Auto-expand parent items + označit je jako match-parent (visible)
        for (const item of matchingItems) {
          let parent = item.parentElement;
          while (parent && parent !== treeRoot) {
            if (parent.classList && parent.classList.contains("erp-tree-children")) {
              parent.style.display = "block";
              const parentItem = parent.parentElement;
              if (parentItem && parentItem.classList.contains("erp-tree-item")) {
                const parentRow = parentItem.querySelector(":scope > .erp-tree-row");
                if (parentRow) parentRow.classList.add("erp-tree-match-parent");
                // Update toggle icon ▼
                const toggle = parentRow ? parentRow.querySelector(".erp-tree-toggle") : null;
                if (toggle) toggle.textContent = "▼";
              }
            }
            parent = parent.parentElement;
          }
        }
        // B+7+++ (6.5.2026): auto-expand match item samotný + označit
        // VŠECHNY descendants jako match-descendant (visible v filteru).
        // Marti's UX: "kdyz napisu sys, chci videt deti System menu —
        // Definice soudecku, Definice SQL, ...".
        for (const item of matchingItems) {
          const childrenContainer = item.querySelector(":scope > .erp-tree-children");
          if (childrenContainer) {
            childrenContainer.style.display = "block";
            // Update toggle ▼ na match item
            const matchRow = item.querySelector(":scope > .erp-tree-row");
            const toggle = matchRow ? matchRow.querySelector(".erp-tree-toggle") : null;
            if (toggle) toggle.textContent = "▼";
            // Mark VŠECHNY descendant rows (recursive)
            const descendantRows = childrenContainer.querySelectorAll(".erp-tree-row");
            descendantRows.forEach(r => {
              r.classList.add("erp-tree-match-descendant");
            });
            // Plus expand všechny nested children containers (descendant folders
            // co user pak může zase zavřít — ale defaultně viditelné aby uvidel
            // celý podstrom)
            const nestedContainers = childrenContainer.querySelectorAll(".erp-tree-children");
            nestedContainers.forEach(c => {
              c.style.display = "block";
              // Update parent toggle ikonu
              const parentItem = c.parentElement;
              if (parentItem && parentItem.classList.contains("erp-tree-item")) {
                const pRow = parentItem.querySelector(":scope > .erp-tree-row");
                const pToggle = pRow ? pRow.querySelector(".erp-tree-toggle") : null;
                if (pToggle) pToggle.textContent = "▼";
              }
            });
          }
        }
      }

      if (treeSearchInput) {
        let _searchDebounce = null;
        treeSearchInput.addEventListener("input", (ev) => {
          const v = ev.target.value;
          // Debounce 80ms — large trees benefit z mírného delay
          clearTimeout(_searchDebounce);
          _searchDebounce = setTimeout(() => applyTreeFilter(v), 80);
        });
        treeSearchInput.addEventListener("keydown", (ev) => {
          if (ev.key === "Escape") {
            ev.preventDefault();
            treeSearchInput.value = "";
            applyTreeFilter("");
            treeSearchInput.blur();
          }
        });
      }
      if (treeSearchClear) {
        treeSearchClear.addEventListener("click", () => {
          if (treeSearchInput) treeSearchInput.value = "";
          applyTreeFilter("");
          if (treeSearchInput) treeSearchInput.focus();
        });
      }

      // ── B+9 (6.5.2026): UI zoom toggle (A−/A/A+ persistence) ────
      const ZOOM_KEY = "erp.zoom";
      const ZOOM_VALUES = ["small", "normal", "large"];
      function loadZoom() {
        try {
          const v = localStorage.getItem(ZOOM_KEY);
          return ZOOM_VALUES.indexOf(v) >= 0 ? v : "normal";
        } catch (e) { return "normal"; }
      }
      function applyZoom(mode) {
        if (ZOOM_VALUES.indexOf(mode) < 0) mode = "normal";
        document.body.classList.remove("erp-zoom-small", "erp-zoom-large");
        if (mode === "small") document.body.classList.add("erp-zoom-small");
        else if (mode === "large") document.body.classList.add("erp-zoom-large");
        // Update toggle UI — query each call (footer buttons existing post-init)
        document.querySelectorAll(".erp-zoom-toggle button").forEach(b => {
          b.classList.toggle("active", b.getAttribute("data-zoom") === mode);
        });
        try { localStorage.setItem(ZOOM_KEY, mode); } catch (e) {}
        // Po zoom change re-fit grid columns (container width changed)
        if (activeErpDataGrid && typeof activeErpDataGrid.sizeColumnsToFit === "function") {
          setTimeout(() => {
            try { activeErpDataGrid.sizeColumnsToFit(); } catch (e) {}
          }, 80);
        }
      }
      // B+10++ (Marti's drobnost 6.5.2026): zoom toggle přesunut z header
      // do footer aplikace. Workspace IIFE běží INLINE ve <main> PŘED
      // <footer> parsed → buttons ještě neexistují. Fix: event delegation
      // (zachycuje clicks i pozdě připojené buttony) + delayed applyZoom.
      document.addEventListener("click", (ev) => {
        const btn = ev.target && ev.target.closest
          ? ev.target.closest(".erp-zoom-toggle button")
          : null;
        if (btn) {
          const m = btn.getAttribute("data-zoom");
          if (m) applyZoom(m);
        }
      });
      // Init z localStorage — delay aby footer buttons existovaly při
      // prvním nastavení active class
      const _zoomInit = () => applyZoom(loadZoom());
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", _zoomInit, { once: true });
      } else {
        // Document již plně parsed — DOM má footer; ale pojistka přes RAF
        requestAnimationFrame(_zoomInit);
      }

      // ── Phase 35-E.3.2 (8.5.2026): Footer tenant switcher ───────────
      // Marti's spec: clickable tenant_name v paticce → popover dropdown
      // s available tenants. Click na řádek = POST switch_tenant + reload.
      // Reload je nejjednodušší způsob (tree, state, header — všechno
      // závisí na tenantu, full reload zaručí konzistenci).
      let _erpTenantsLoaded = false;
      let _erpTenantsCache = null;

      async function _erpFetchTenants() {
        if (_erpTenantsLoaded && _erpTenantsCache) return _erpTenantsCache;
        try {
          const res = await fetch('/api/v1/erp/tenants', { credentials: 'include' });
          if (!res.ok) return null;
          const data = await res.json();
          _erpTenantsCache = data;
          _erpTenantsLoaded = true;
          return data;
        } catch (e) {
          console.error('Tenant fetch failed', e);
          return null;
        }
      }

      function _erpRenderTenantPopover(data) {
        const pop = document.getElementById('erpFooterTenantPopover');
        if (!pop) return;
        pop.innerHTML = '';
        const tenants = (data && data.tenants) || [];
        const currentId = data && data.current_tenant_id;
        if (tenants.length === 0) {
          pop.innerHTML = '<div class="erp-tenant-popover-item" style="cursor:default;color:var(--muted);">Žádné dostupné tenanty</div>';
          return;
        }
        tenants.forEach(t => {
          const item = document.createElement('div');
          const isActive = (t.tenant_id === currentId);
          item.className = 'erp-tenant-popover-item' + (isActive ? ' active' : '');

          if (isActive) {
            const dot = document.createElement('span');
            dot.className = 'erp-tenant-popover-dot';
            dot.title = 'Aktivní tenant';
            item.appendChild(dot);
          }

          const nameEl = document.createElement('span');
          nameEl.className = 'erp-tenant-popover-name';
          nameEl.textContent = t.tenant_name;
          item.appendChild(nameEl);

          if (t.tenant_type) {
            const metaEl = document.createElement('span');
            metaEl.className = 'erp-tenant-popover-meta';
            metaEl.textContent = t.tenant_type;
            item.appendChild(metaEl);
          }

          item.addEventListener('click', async (ev) => {
            ev.stopPropagation();
            if (t.tenant_id === currentId) return;
            await _erpSwitchTenant(t.tenant_id);
          });
          pop.appendChild(item);
        });
      }

      async function _erpSwitchTenant(tenantId) {
        try {
          const res = await fetch('/api/v1/auth/switch_tenant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tenant_id: tenantId }),
            credentials: 'include',
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert(err.detail || ('Přepnutí tenantu selhalo (' + res.status + ').'));
            return;
          }
          // Reload — tree, header, state vše závisí na tenantu, full reload
          // zaručí čistou konzistenci.
          window.location.reload();
        } catch (e) {
          alert('Přepnutí tenantu selhalo: ' + e);
        }
      }

      function _erpInitTenantSwitcher() {
        const btn = document.getElementById('erpFooterTenantBtn');
        const pop = document.getElementById('erpFooterTenantPopover');
        if (!btn || !pop) return;

        btn.addEventListener('click', async (ev) => {
          ev.stopPropagation();
          if (!pop.hidden) {
            pop.hidden = true;
            btn.classList.remove('active');
            return;
          }
          const data = await _erpFetchTenants();
          if (!data) return;
          _erpRenderTenantPopover(data);
          pop.hidden = false;
          btn.classList.add('active');
        });

        // Click outside → close
        document.addEventListener('click', (ev) => {
          if (pop.hidden) return;
          if (!pop.contains(ev.target) && !btn.contains(ev.target)) {
            pop.hidden = true;
            btn.classList.remove('active');
          }
        });

        // ESC → close
        document.addEventListener('keydown', (ev) => {
          if (ev.key === 'Escape' && !pop.hidden) {
            pop.hidden = true;
            btn.classList.remove('active');
          }
        });
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", _erpInitTenantSwitcher, { once: true });
      } else {
        requestAnimationFrame(_erpInitTenantSwitcher);
      }

      // ── B+7++++ (6.5.2026): tree collapse / expand toggle ──────────
      const TREE_COLLAPSED_KEY = "erp.tree.collapsed";
      const treeToggleBtn = document.getElementById("erpTreeToggle");

      function loadTreeCollapsed() {
        try { return localStorage.getItem(TREE_COLLAPSED_KEY) === "1"; }
        catch (e) { return false; }
      }
      function saveTreeCollapsed(b) {
        try { localStorage.setItem(TREE_COLLAPSED_KEY, b ? "1" : "0"); } catch (e) {}
      }
      function applyTreeCollapsed(collapsed) {
        if (!workspaceEl) return;
        if (collapsed) {
          workspaceEl.classList.add("tree-collapsed");
          if (treeToggleBtn) {
            treeToggleBtn.title = "Zobrazit strom (Ctrl+B)";
            treeToggleBtn.setAttribute("aria-label", "Zobrazit strom");
          }
        } else {
          workspaceEl.classList.remove("tree-collapsed");
          if (treeToggleBtn) {
            treeToggleBtn.title = "Skrýt strom (Ctrl+B)";
            treeToggleBtn.setAttribute("aria-label", "Skrýt strom");
          }
        }
        // Po collapse/expand re-fit grid (column flex re-distribute)
        if (activeErpDataGrid && typeof activeErpDataGrid.sizeColumnsToFit === "function") {
          setTimeout(() => {
            try { activeErpDataGrid.sizeColumnsToFit(); } catch (e) {}
          }, 60);
        }
      }
      // Init z localStorage
      applyTreeCollapsed(loadTreeCollapsed());
      // Klik handler
      if (treeToggleBtn) {
        treeToggleBtn.addEventListener("click", () => {
          const next = !workspaceEl.classList.contains("tree-collapsed");
          applyTreeCollapsed(next);
          saveTreeCollapsed(next);
        });
      }
      // Ctrl+B / Cmd+B keyboard shortcut
      document.addEventListener("keydown", (ev) => {
        if ((ev.ctrlKey || ev.metaKey) && (ev.key === "b" || ev.key === "B")) {
          // Skip pokud user píše do inputu
          const tag = ev.target && ev.target.tagName;
          if (tag === "INPUT" || tag === "TEXTAREA") return;
          ev.preventDefault();
          const next = !workspaceEl.classList.contains("tree-collapsed");
          applyTreeCollapsed(next);
          saveTreeCollapsed(next);
        }
      });

      // ── B+8.1c (6.5.2026): API client pro user state persistence ──
      // Write-through pattern: localStorage = optimistic cache, API =
      // source of truth (cross-device, per user/tenant). Pokud API fail
      // (offline/network), cache stays — sync proběhne při příštím
      // network OK. Marti's spec: "Per user, per tenant... do data_db".
      async function _apiCall(method, path, body) {
        try {
          const opts = {
            method: method,
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          };
          if (body !== undefined && body !== null) {
            opts.body = JSON.stringify(body);
          }
          const r = await fetch(path, opts);
          if (!r.ok) {
            console.warn("API " + method + " " + path + " status " + r.status);
            return null;
          }
          return await r.json();
        } catch (e) {
          console.warn("API " + method + " " + path + " error", e);
          return null;
        }
      }

      // ── B+8.2a (6.5.2026): tree view modes (Vše / Oblíbené / MRU) ──
      const TREE_VIEW_KEY = "erp.tree.view";
      const TREE_FAVORITES_KEY = "erp.tree.favorites";
      const TREE_RECENT_KEY = "erp.tree.recent";
      const TREE_RECENT_MAX = 20;
      const treeFooterEl = document.getElementById("erpTreeFooter");
      let treeViewMode = "all";

      function loadTreeFavorites() {
        try {
          const s = localStorage.getItem(TREE_FAVORITES_KEY);
          if (!s) return [];
          const arr = JSON.parse(s);
          return Array.isArray(arr)
            ? arr.map(x => parseInt(x, 10)).filter(n => !isNaN(n))
            : [];
        } catch (e) { return []; }
      }
      function saveTreeFavorites(arr) {
        try { localStorage.setItem(TREE_FAVORITES_KEY, JSON.stringify(arr)); }
        catch (e) {}
      }
      function isTreeFavorite(cislo) {
        return loadTreeFavorites().includes(parseInt(cislo, 10));
      }
      function toggleTreeFavorite(cislo) {
        const arr = loadTreeFavorites();
        const c = parseInt(cislo, 10);
        const idx = arr.indexOf(c);
        const willBePinned = (idx < 0);
        if (idx >= 0) arr.splice(idx, 1);
        else arr.push(c);
        saveTreeFavorites(arr);
        const isPinnedNow = isTreeFavorite(c);
        // B+8.1c: API sync (fire-and-forget; localStorage stays jako cache)
        if (willBePinned) {
          _apiCall("POST", "/api/v1/erp/favorites", { cislo: c });
        } else {
          _apiCall("DELETE", "/api/v1/erp/favorites/" + c);
        }
        // Update DOM — pinned class + zajisti že ★ span existuje
        treeRoot.querySelectorAll(".erp-tree-item").forEach(item => {
          const cd = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          if (cd !== c) return;
          const row = item.querySelector(":scope > .erp-tree-row");
          if (!row) return;
          row.classList.toggle("erp-tree-pinned", isPinnedNow);
          // B+8.2a+ fix (6.5.2026): při prvním pin musíme vložit ★ span,
          // protože _markPinnedTreeRows běžel jen po init renderTreeNodes.
          if (isPinnedNow && !row.querySelector(".erp-tree-star")) {
            const star = document.createElement("span");
            star.className = "erp-tree-star";
            star.textContent = "★";
            star.title = "Odepnout (klik) nebo pravý-klik";
            row.appendChild(star);
          }
        });
        // Re-apply view filter pokud je v favorites view (nebo pokud unpinned
        // odebral jediný viditelný row — empty state by měl scvyltnout)
        if (treeViewMode === "favorites") applyTreeViewFilter();
      }

      function loadTreeRecent() {
        try {
          const s = localStorage.getItem(TREE_RECENT_KEY);
          if (!s) return [];
          const arr = JSON.parse(s);
          return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
      }
      function saveTreeRecent(arr) {
        try { localStorage.setItem(TREE_RECENT_KEY, JSON.stringify(arr)); }
        catch (e) {}
      }
      function trackTreeRecent(cislo, label) {
        const arr = loadTreeRecent();
        const c = parseInt(cislo, 10);
        const idx = arr.findIndex(r => r.cislo === c);
        if (idx >= 0) arr.splice(idx, 1);  // remove existing (move to top)
        arr.unshift({ cislo: c, label: label || ("Přehled #" + c), ts: Date.now() });
        if (arr.length > TREE_RECENT_MAX) arr.length = TREE_RECENT_MAX;
        saveTreeRecent(arr);
        if (treeViewMode === "recent") applyTreeViewFilter();
        // B+8.1c: API track (fire-and-forget)
        _apiCall("POST", "/api/v1/erp/recent", {
          cislo: c, label: label || null
        });
      }

      function applyTreeViewFilter() {
        if (!treeRoot) return;
        // Vyčisti view-related classes a empty-state placeholder
        treeRoot.classList.remove("erp-tree-view-favorites", "erp-tree-view-recent");
        treeRoot.querySelectorAll(".erp-tree-row").forEach(r => {
          r.classList.remove("erp-tree-view-match", "erp-tree-view-match-parent");
        });
        // Remove existing empty state
        const oldEmpty = treeRoot.querySelector(".erp-tree-empty-view");
        if (oldEmpty) oldEmpty.remove();

        if (treeViewMode === "all") return;

        let matchingCislos;
        let emptyMsg;
        if (treeViewMode === "favorites") {
          matchingCislos = new Set(loadTreeFavorites());
          treeRoot.classList.add("erp-tree-view-favorites");
          emptyMsg = "Žádné oblíbené.<br>Pinout položku přes <strong>pravý-klik</strong> na řádek nebo přes ★ ikonu.";
        } else if (treeViewMode === "recent") {
          matchingCislos = new Set(loadTreeRecent().map(r => r.cislo));
          treeRoot.classList.add("erp-tree-view-recent");
          emptyMsg = "Žádná historie.<br>Otevři přehled — automaticky se přidá do MRU.";
        } else {
          return;
        }

        if (matchingCislos.size === 0) {
          // Empty state
          const empty = document.createElement("div");
          empty.className = "erp-tree-empty-view";
          empty.innerHTML = emptyMsg;
          treeRoot.appendChild(empty);
          return;
        }

        // Mark match items + parent path
        treeRoot.querySelectorAll(".erp-tree-item").forEach(item => {
          const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          if (cislo && matchingCislos.has(cislo)) {
            const row = item.querySelector(":scope > .erp-tree-row");
            if (row) row.classList.add("erp-tree-view-match");
            // Expand + označit parents
            let parent = item.parentElement;
            while (parent && parent !== treeRoot) {
              if (parent.classList && parent.classList.contains("erp-tree-children")) {
                parent.style.display = "block";
                const parentItem = parent.parentElement;
                if (parentItem && parentItem.classList &&
                    parentItem.classList.contains("erp-tree-item")) {
                  const pRow = parentItem.querySelector(":scope > .erp-tree-row");
                  if (pRow) pRow.classList.add("erp-tree-view-match-parent");
                  const tg = pRow ? pRow.querySelector(".erp-tree-toggle") : null;
                  if (tg) tg.textContent = "▼";
                }
              }
              parent = parent.parentElement;
            }
          }
        });
      }

      function setTreeViewMode(mode) {
        if (mode !== "all" && mode !== "favorites" && mode !== "recent") return;
        treeViewMode = mode;
        try { localStorage.setItem(TREE_VIEW_KEY, mode); } catch (e) {}
        if (treeFooterEl) {
          treeFooterEl.querySelectorAll(".erp-tree-view-btn").forEach(b => {
            b.classList.toggle("active", b.getAttribute("data-tree-view") === mode);
          });
        }
        applyTreeViewFilter();
      }

      // Wire footer toggle
      if (treeFooterEl) {
        treeFooterEl.addEventListener("click", (ev) => {
          const btn = ev.target.closest(".erp-tree-view-btn");
          if (!btn) return;
          const mode = btn.getAttribute("data-tree-view");
          if (mode) setTreeViewMode(mode);
        });

        // B+8.2a+++++++ (6.5.2026): pravý-klik na footer view button =
        // context menu pro správu daného view (zatím jen MRU clear).
        treeFooterEl.addEventListener("contextmenu", (ev) => {
          const btn = ev.target.closest(".erp-tree-view-btn");
          if (!btn) return;
          const mode = btn.getAttribute("data-tree-view");
          ev.preventDefault();
          const menuItems = [];
          if (mode === "recent") {
            const recCount = loadTreeRecent().length;
            menuItems.push({
              icon: "⊘",
              label: recCount > 0
                ? ("Vymazat historii (" + recCount + " položek)")
                : "Vymazat historii (prázdná)",
              handler: () => {
                if (recCount === 0) return;
                saveTreeRecent([]);
                if (treeViewMode === "recent") applyTreeViewFilter();
              },
            });
          } else if (mode === "favorites") {
            const favCount = loadTreeFavorites().length;
            menuItems.push({
              icon: "⊘",
              label: favCount > 0
                ? ("Vymazat všechny oblíbené (" + favCount + ")")
                : "Vymazat oblíbené (prázdné)",
              handler: () => {
                if (favCount === 0) return;
                if (!window.confirm(
                  "Opravdu vymazat všechny oblíbené (" + favCount + ")?"
                )) return;
                const fav = loadTreeFavorites();
                fav.forEach(c => {
                  // Použij toggleTreeFavorite per cislo aby se updatnula DOM
                  if (isTreeFavorite(c)) toggleTreeFavorite(c);
                });
              },
            });
          } else if (mode === "all") {
            menuItems.push({
              icon: "⟲",
              label: "Resetovat řazení stromu",
              handler: () => {
                if (!window.confirm(
                  "Vrátit pořadí položek ve stromu na výchozí (z DB)?"
                )) return;
                try { localStorage.removeItem(TREE_ORDER_KEY); } catch (e) {}
                // Reload tree → původní DB order
                loadTree();
              },
            });
          }
          if (menuItems.length === 0) return;
          _showTreeContextMenu(ev.clientX, ev.clientY, menuItems);
        });

        // B+8.2a++++++ (6.5.2026): drag-drop na footer ikony.
        // Drag leaf z "Vše"/"MRU" → drop na ★ Oblíbené = PIN.
        // Drag leaf z "Oblíbené" → drop na ≡ Vše = UNPIN.
        // Drop na MRU = no-op (auto-tracked, manual řízení nedává smysl).
        // Folders (bez cislo_def) → reject (folder nelze pinnout jako celek).
        treeFooterEl.querySelectorAll(".erp-tree-view-btn").forEach(btn => {
          if (btn._dropWired) return;
          btn._dropWired = true;
          const targetView = btn.getAttribute("data-tree-view");

          btn.addEventListener("dragover", (ev) => {
            if (!_dragSourceItem) return;
            const cislo = parseInt(
              _dragSourceItem.getAttribute("data-cislo-def") || "0", 10
            );
            if (!cislo) return;  // folder = no drop
            // Determine action based na cílový view + source view
            let action = null;
            if (targetView === "favorites" && !isTreeFavorite(cislo)) {
              action = "pin";
            } else if (targetView === "all" &&
                       treeViewMode === "favorites" &&
                       isTreeFavorite(cislo)) {
              action = "unpin";
            }
            if (!action) return;
            ev.preventDefault();
            ev.dataTransfer.dropEffect = "move";
            // Visual highlight (zlatá pin / červená unpin)
            btn.classList.remove(
              "erp-tree-view-drop-pin", "erp-tree-view-drop-unpin"
            );
            btn.classList.add(
              action === "pin"
                ? "erp-tree-view-drop-pin"
                : "erp-tree-view-drop-unpin"
            );
          });

          btn.addEventListener("dragleave", () => {
            btn.classList.remove(
              "erp-tree-view-drop-pin", "erp-tree-view-drop-unpin"
            );
          });

          btn.addEventListener("drop", (ev) => {
            btn.classList.remove(
              "erp-tree-view-drop-pin", "erp-tree-view-drop-unpin"
            );
            if (!_dragSourceItem) return;
            const cislo = parseInt(
              _dragSourceItem.getAttribute("data-cislo-def") || "0", 10
            );
            if (!cislo) return;
            ev.preventDefault();
            ev.stopPropagation();
            if (targetView === "favorites" && !isTreeFavorite(cislo)) {
              toggleTreeFavorite(cislo);  // pin
            } else if (targetView === "all" &&
                       treeViewMode === "favorites" &&
                       isTreeFavorite(cislo)) {
              toggleTreeFavorite(cislo);  // unpin
            }
            // dragend handler vyčistí _dragSourceItem
          });
        });
      }
      // Init: restore last view mode (default all)
      try {
        const saved = localStorage.getItem(TREE_VIEW_KEY);
        if (saved === "favorites" || saved === "recent" || saved === "all") {
          treeViewMode = saved;
        }
      } catch (e) {}

      // B+8.2a+ (6.5.2026): tree context menu (pravý-klik) + ★ klik
      function _showTreeContextMenu(x, y, items) {
        _closeTreeContextMenu();
        const menu = document.createElement("div");
        menu.className = "erp-tree-ctx-menu";
        menu.style.left = x + "px";
        menu.style.top = y + "px";
        items.forEach(it => {
          if (it.divider) {
            const d = document.createElement("div");
            d.className = "erp-tree-ctx-divider";
            menu.appendChild(d);
            return;
          }
          if (it.hint) {
            const h = document.createElement("div");
            h.className = "erp-tree-ctx-hint";
            h.textContent = it.hint;
            menu.appendChild(h);
            return;
          }
          const el = document.createElement("div");
          el.className = "erp-tree-ctx-item";
          const icon = it.icon != null ? it.icon : "";
          el.innerHTML =
            '<span class="erp-tree-ctx-item-icon">' + escapeHtml(icon) + '</span>' +
            '<span>' + escapeHtml(it.label || "") + '</span>';
          el.addEventListener("click", () => {
            _closeTreeContextMenu();
            try { it.handler && it.handler(); } catch (e) { console.warn(e); }
          });
          menu.appendChild(el);
        });
        document.body.appendChild(menu);
        // Position adjust pokud overflow viewport
        setTimeout(() => {
          const rect = menu.getBoundingClientRect();
          if (rect.right > window.innerWidth) {
            menu.style.left = (window.innerWidth - rect.width - 6) + "px";
          }
          if (rect.bottom > window.innerHeight) {
            menu.style.top = (window.innerHeight - rect.height - 6) + "px";
          }
        }, 0);
        // Outside click + Esc close
        const onDoc = (ev) => {
          if (!menu.contains(ev.target)) _closeTreeContextMenu();
        };
        const onKey = (ev) => {
          if (ev.key === "Escape") _closeTreeContextMenu();
        };
        setTimeout(() => {
          document.addEventListener("mousedown", onDoc);
          document.addEventListener("keydown", onKey);
        }, 0);
        menu._cleanup = () => {
          document.removeEventListener("mousedown", onDoc);
          document.removeEventListener("keydown", onKey);
        };
      }
      function _closeTreeContextMenu() {
        document.querySelectorAll(".erp-tree-ctx-menu").forEach(m => {
          if (m._cleanup) try { m._cleanup(); } catch (e) {}
          m.remove();
        });
      }

      function _attachTreePinHandlers() {
        if (!treeRoot) return;
        treeRoot.addEventListener("contextmenu", (ev) => {
          const row = ev.target.closest(".erp-tree-row");
          if (!row) return;
          const item = row.closest(".erp-tree-item");
          if (!item) return;
          const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          if (!cislo) return;  // jen leaves with cislo_def

          ev.preventDefault();

          // Compute target cislos — pokud row je v selection a multi-select
          // active, akce platí pro celou selection. Jinak jen tento řádek.
          let targetCislos;
          if (_selectedTreeCislos.has(cislo) && _selectedTreeCislos.size > 1) {
            targetCislos = Array.from(_selectedTreeCislos);
          } else {
            targetCislos = [cislo];
            // Single right-click — vyber pro visual feedback (pokud není v selection)
            if (!_selectedTreeCislos.has(cislo)) {
              _selectTreeRow(item);
            }
          }

          // Determine pin status
          const allPinned = targetCislos.every(c => isTreeFavorite(c));
          const nonePinned = targetCislos.every(c => !isTreeFavorite(c));
          const multi = targetCislos.length > 1;

          const menuItems = [];

          if (multi) {
            menuItems.push({
              hint: "Vybráno " + targetCislos.length + " položek",
            });
          }

          if (nonePinned) {
            menuItems.push({
              icon: "★",
              label: multi
                ? ("Přidat všechny (" + targetCislos.length + ") k oblíbeným")
                : "Přidat k oblíbeným",
              handler: () => {
                targetCislos.forEach(c => {
                  if (!isTreeFavorite(c)) toggleTreeFavorite(c);
                });
              },
            });
          } else if (allPinned) {
            menuItems.push({
              icon: "✕",
              label: multi
                ? ("Odebrat všechny (" + targetCislos.length + ") z oblíbených")
                : "Odebrat z oblíbených",
              handler: () => {
                targetCislos.forEach(c => {
                  if (isTreeFavorite(c)) toggleTreeFavorite(c);
                });
              },
            });
          } else {
            // Mixed — nabídni obě
            const pinnedCount = targetCislos.filter(c => isTreeFavorite(c)).length;
            const notPinnedCount = targetCislos.length - pinnedCount;
            menuItems.push({
              icon: "★",
              label: "Přidat zbývajících (" + notPinnedCount + ") k oblíbeným",
              handler: () => {
                targetCislos.forEach(c => {
                  if (!isTreeFavorite(c)) toggleTreeFavorite(c);
                });
              },
            });
            menuItems.push({
              icon: "✕",
              label: "Odebrat aktuálních (" + pinnedCount + ") z oblíbených",
              handler: () => {
                targetCislos.forEach(c => {
                  if (isTreeFavorite(c)) toggleTreeFavorite(c);
                });
              },
            });
          }

          _showTreeContextMenu(ev.clientX, ev.clientY, menuItems);
        });

        // Klik na ★ ikonu = quick unpin (bez context menu)
        treeRoot.addEventListener("click", (ev) => {
          const star = ev.target.closest(".erp-tree-star");
          if (!star) return;
          ev.stopPropagation();
          const item = star.closest(".erp-tree-item");
          if (!item) return;
          const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          if (cislo) toggleTreeFavorite(cislo);
        });
      }
      _attachTreePinHandlers();

      // Esc kdekoli — zavři context menu + clear selection
      document.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape") {
          _closeTreeContextMenu();
          // Pozn.: search Esc už handler clear input — to nesahá.
          // Tree selection clear jen pokud focus není v inputu
          const tag = ev.target && ev.target.tagName;
          if (tag !== "INPUT" && tag !== "TEXTAREA") {
            _clearTreeSelection();
          }
        }
      });

      // ── B+8.2a+++ (6.5.2026): drag-and-drop reorder uvnitř skupin ──
      // Marti spec: "Poradi jednotlivych polozek per user ve vsech i v
      // oblibenych... Drag and drop... POZOR jen v ramci skupin, aby se
      // nestalo jako ve Windows, ze nekdo pretahne skupinu, nebo polozku
      // skupiny do jine skupiny..."
      const TREE_ORDER_KEY = "erp.tree.order.v1";
      let _dragSourceItem = null;

      function _loadTreeOrderMap() {
        try { return JSON.parse(localStorage.getItem(TREE_ORDER_KEY) || "{}"); }
        catch (e) { return {}; }
      }
      function _saveTreeOrderMap(map) {
        try { localStorage.setItem(TREE_ORDER_KEY, JSON.stringify(map)); }
        catch (e) {}
      }
      function _ulGroupKey(ul) {
        // Identifier skupiny — parent .erp-tree-item.data-id, nebo "ROOT"
        if (!ul) return "ROOT";
        const childrenWrap = ul.parentElement;
        const parentItem = childrenWrap && childrenWrap.classList.contains("erp-tree-children")
          ? childrenWrap.parentElement
          : null;
        if (parentItem && parentItem.classList.contains("erp-tree-item")) {
          return parentItem.getAttribute("data-id") || "ROOT";
        }
        return "ROOT";
      }
      function _saveTreeOrderForUl(ul) {
        if (!ul) return;
        const key = _ulGroupKey(ul);
        const order = Array.from(ul.children)
          .filter(li => li.classList.contains("erp-tree-item"))
          .map(li => li.getAttribute("data-id"))
          .filter(id => id != null);
        const map = _loadTreeOrderMap();
        map[key] = order;
        _saveTreeOrderMap(map);
        // B+8.1c: API sync (fire-and-forget)
        _apiCall("PUT", "/api/v1/erp/tree-order", {
          group_key: key, order: order
        });
      }
      function _applyTreeOrderFromStorage() {
        if (!treeRoot) return;
        const map = _loadTreeOrderMap();
        if (!map || Object.keys(map).length === 0) return;
        treeRoot.querySelectorAll("ul.erp-tree-list").forEach(ul => {
          const key = _ulGroupKey(ul);
          const order = map[key];
          if (!order || order.length === 0) return;
          const items = Array.from(ul.children).filter(li =>
            li.classList.contains("erp-tree-item")
          );
          const itemMap = new Map(items.map(li => [li.getAttribute("data-id"), li]));
          // Reorder: nejdřív known IDs v saved order, pak unknown (nové) na konci
          const seen = new Set();
          order.forEach(id => {
            if (itemMap.has(id)) {
              ul.appendChild(itemMap.get(id));
              seen.add(id);
            }
          });
          items.forEach(li => {
            const id = li.getAttribute("data-id");
            if (!seen.has(id)) ul.appendChild(li);
          });
        });
      }
      function _attachTreeDragHandlers() {
        if (!treeRoot) return;
        // B+8.2a++++ (6.5.2026): drag na VŠECH tree rows (leaves + folders).
        // Marti's UX: "v oblibenych mam dve skupiny a nemohu aktivovat drag
        // ani u jedny, abych je mezi sebou prohodil". HTML5 drag a click jsou
        // separate eventy — folder click (mousedown+up bez move) = expand,
        // folder drag (mousedown+move+drop) = reorder. Žádný konflikt.
        treeRoot.querySelectorAll(".erp-tree-item").forEach(item => {
          const row = item.querySelector(":scope > .erp-tree-row");
          if (!row) return;
          row.setAttribute("draggable", "true");
        });

        // Single set listenerů na treeRoot (delegation)
        if (treeRoot._dragWired) return;
        treeRoot._dragWired = true;

        treeRoot.addEventListener("dragstart", (ev) => {
          // MRU view — drag disabled (auto-sort by timestamp)
          if (treeViewMode === "recent") {
            ev.preventDefault();
            return;
          }
          const row = ev.target.closest(".erp-tree-row");
          if (!row) { ev.preventDefault(); return; }
          const item = row.closest(".erp-tree-item");
          if (!item) { ev.preventDefault(); return; }
          _dragSourceItem = item;
          item.classList.add("erp-tree-dragging");
          try {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", item.getAttribute("data-id") || "");
          } catch (e) {}
        });

        treeRoot.addEventListener("dragover", (ev) => {
          if (!_dragSourceItem) return;
          const row = ev.target.closest(".erp-tree-row");
          if (!row) return;
          const item = row.closest(".erp-tree-item");
          if (!item || item === _dragSourceItem) return;
          // Same group check — parent UL musí být totožný
          const sourceUl = _dragSourceItem.parentElement;
          const targetUl = item.parentElement;
          if (sourceUl !== targetUl) {
            ev.dataTransfer.dropEffect = "none";
            return;
          }
          // Allow drop
          ev.preventDefault();
          ev.dataTransfer.dropEffect = "move";
          // Visual: line above (insert before) nebo below (insert after)
          treeRoot.querySelectorAll(
            ".erp-tree-drag-over-before, .erp-tree-drag-over-after"
          ).forEach(r => {
            r.classList.remove("erp-tree-drag-over-before", "erp-tree-drag-over-after");
          });
          const rect = row.getBoundingClientRect();
          const isAbove = ev.clientY < (rect.top + rect.height / 2);
          row.classList.add(
            isAbove ? "erp-tree-drag-over-before" : "erp-tree-drag-over-after"
          );
        });

        treeRoot.addEventListener("dragleave", (ev) => {
          // Pokud opustíme úplně tree, vyčisti indikátory
          if (!treeRoot.contains(ev.relatedTarget)) {
            treeRoot.querySelectorAll(
              ".erp-tree-drag-over-before, .erp-tree-drag-over-after"
            ).forEach(r => {
              r.classList.remove("erp-tree-drag-over-before", "erp-tree-drag-over-after");
            });
          }
        });

        treeRoot.addEventListener("drop", (ev) => {
          if (!_dragSourceItem) return;
          const row = ev.target.closest(".erp-tree-row");
          if (!row) return;
          const targetItem = row.closest(".erp-tree-item");
          if (!targetItem || targetItem === _dragSourceItem) return;
          const sourceUl = _dragSourceItem.parentElement;
          const targetUl = targetItem.parentElement;
          if (sourceUl !== targetUl) return;
          ev.preventDefault();

          const rect = row.getBoundingClientRect();
          const isAbove = ev.clientY < (rect.top + rect.height / 2);
          if (isAbove) {
            targetUl.insertBefore(_dragSourceItem, targetItem);
          } else {
            targetUl.insertBefore(_dragSourceItem, targetItem.nextSibling);
          }
          // Persist order pro tuto skupinu
          _saveTreeOrderForUl(targetUl);
        });

        treeRoot.addEventListener("dragend", () => {
          if (_dragSourceItem) {
            _dragSourceItem.classList.remove("erp-tree-dragging");
          }
          _dragSourceItem = null;
          treeRoot.querySelectorAll(
            ".erp-tree-drag-over-before, .erp-tree-drag-over-after"
          ).forEach(r => {
            r.classList.remove("erp-tree-drag-over-before", "erp-tree-drag-over-after");
          });
        });
      }

      // Po každém renderTreeNodes inject ★ ikony pro pinned items
      function _markPinnedTreeRows() {
        if (!treeRoot) return;
        const favSet = new Set(loadTreeFavorites());
        treeRoot.querySelectorAll(".erp-tree-item").forEach(item => {
          const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          if (!cislo) return;
          const row = item.querySelector(":scope > .erp-tree-row");
          if (!row) return;
          if (favSet.has(cislo)) {
            row.classList.add("erp-tree-pinned");
            // Inject ★ ikona pokud chybí
            if (!row.querySelector(".erp-tree-star")) {
              const star = document.createElement("span");
              star.className = "erp-tree-star";
              star.textContent = "★";
              star.title = "Odepnout (klik) nebo pravý-klik";
              row.appendChild(star);
            }
          } else {
            row.classList.remove("erp-tree-pinned");
          }
        });
      }
      // Hook do attachTreeHandlers — po renderu mark pinned + apply view filter
      const _origAttachTreeHandlers = attachTreeHandlers;
      attachTreeHandlers = function() {
        _origAttachTreeHandlers();
        // B+8.2a+++ (6.5.2026): apply saved per-group order PŘED markem pinned
        // (apply změní DOM order, mark + drag setup pak fungují na finální layout)
        _applyTreeOrderFromStorage();
        _markPinnedTreeRows();
        _attachTreeDragHandlers();
        // Init footer toggle UI
        if (treeFooterEl) {
          treeFooterEl.querySelectorAll(".erp-tree-view-btn").forEach(b => {
            b.classList.toggle("active",
              b.getAttribute("data-tree-view") === treeViewMode);
          });
        }
        applyTreeViewFilter();
      };

      // ── B+8 (6.5.2026): Multi-tab přehled state + UI ───────────────
      // MVP localStorage. Phase B+8.1 přepne na backend persistence
      // (per user, per tenant — Marti's spec — endpoint /api/v1/erp/tabs).
      const TABS_STATE_KEY = "erp.tabs.state.v1";
      const tabsBarEl = document.getElementById("erpTabsBar");
      const tabsState = {
        tabs: [],            // [{cislo, itemId, label, data, gridState}]
        activeIndex: -1,
      };

      function loadTabsState() {
        try {
          const s = localStorage.getItem(TABS_STATE_KEY);
          if (!s) return null;
          const parsed = JSON.parse(s);
          if (!parsed || !Array.isArray(parsed.tabs)) return null;
          return parsed;
        } catch (e) { return null; }
      }
      function saveTabsState() {
        try {
          // Persistuj jen lehkou meta — ne data ani gridState (ty se znovu fetchnou)
          const persist = {
            tabs: tabsState.tabs.map(t => ({
              cislo: t.cislo,
              itemId: t.itemId,
              label: t.label,
            })),
            activeIndex: tabsState.activeIndex,
          };
          localStorage.setItem(TABS_STATE_KEY, JSON.stringify(persist));
        } catch (e) {}
      }

      function _findTabIndex(cislo) {
        return tabsState.tabs.findIndex(t => t.cislo === cislo);
      }

      // B+8++ (6.5.2026): scroll active tree row do středu TreeRoot containeru.
      // Marti's UX feedback: scrollIntoView nedosáhl protože element byl
      // mimo viewport scroll containeru. Manuální compute relative offset.
      function _scrollTreeRowIntoCenter(row) {
        if (!row || !treeRoot) return;
        try {
          const rowRect = row.getBoundingClientRect();
          const containerRect = treeRoot.getBoundingClientRect();
          // Row offset uvnitř scroll containeru
          const rowTopInContainer = rowRect.top - containerRect.top + treeRoot.scrollTop;
          // Cílový scroll = row top - half container + half row (= centered)
          const targetScroll = rowTopInContainer
            - (containerRect.height / 2)
            + (rowRect.height / 2);
          treeRoot.scrollTo({
            top: Math.max(0, targetScroll),
            behavior: "smooth",
          });
        } catch (e) {
          // Fallback — alespoň scrollIntoView
          try { row.scrollIntoView({ block: "center" }); } catch (e2) {}
        }
      }

      async function openTab(cislo, item) {
        const idx = _findTabIndex(cislo);
        // B+8.2a: track recent (i pokud tab už existuje — recency = move to top)
        const itemId = item ? item.getAttribute("data-id") : null;
        const labelEl = item ? item.querySelector(":scope > .erp-tree-row > .erp-tree-label") : null;
        const labelText = (labelEl && (labelEl.dataset.erpOrigText || labelEl.textContent))
          || ("Přehled #" + cislo);
        try { trackTreeRecent(cislo, labelText); } catch (e) {}
        if (idx >= 0) {
          await switchTab(idx);
          return;
        }
        // Nový tab
        const tab = {
          cislo: cislo,
          itemId: itemId,
          label: labelText,
          data: null,
          gridState: null,
        };
        tabsState.tabs.push(tab);
        // B+8.1c: API persist new tab — AWAIT aby následný switchTab
        // (POST /tabs/{cislo}/active) nezávodil s create. Pokud network
        // fail, _apiCall vrátí null bez throw → switchTab pokračuje.
        await _apiCall("POST", "/api/v1/erp/tabs", {
          cislo: cislo,
          label: labelText,
          item_id: itemId,
        });
        await switchTab(tabsState.tabs.length - 1);
      }

      async function switchTab(idx) {
        if (idx < 0 || idx >= tabsState.tabs.length) return;
        // Save current grid state před switch
        if (tabsState.activeIndex >= 0 && tabsState.activeIndex < tabsState.tabs.length) {
          const cur = tabsState.tabs[tabsState.activeIndex];
          if (cur && activeErpDataGrid && activeErpDataGrid.gridApi) {
            try {
              cur.gridState = {
                columnState: activeErpDataGrid.gridApi.getColumnState(),
                filterModel: activeErpDataGrid.gridApi.getFilterModel(),
              };
            } catch (e) {}
          }
        }
        tabsState.activeIndex = idx;
        renderTabsBar();
        const tab = tabsState.tabs[idx];
        // B+8.1c: API persist active tab (fire-and-forget)
        _apiCall("POST", "/api/v1/erp/tabs/" + tab.cislo + "/active");
        // B+10+++ (6.5.2026 Marti's drobnost): document.title + UI header
        // brand row "STRATEGIE · <přehled>" — synchronizováno s tab.
        // B+10++++ (po návratu): | → · (sjednocený separator s footerem).
        const _tabLabel = tab.label || ("Přehled #" + tab.cislo);
        try { document.title = "STRATEGIE · " + _tabLabel; } catch (e) {}
        try {
          const _hdrSep = document.getElementById("erpHeaderSep");
          const _hdrPre = document.getElementById("erpHeaderPrehled");
          if (_hdrSep) _hdrSep.removeAttribute("hidden");
          if (_hdrPre) _hdrPre.textContent = _tabLabel;
        } catch (e) {}
        // Sync tree active state — highlight + expand ancestors + scroll
        // (Marti's UX 6.5.2026: pri prepinani zalozek automaticky vyhledat
        // a oznacit v levem panelu prislusnou vetu).
        if (tab.itemId) {
          treeRoot.querySelectorAll(".erp-tree-row.active").forEach(r => r.classList.remove("active"));
          let treeItem = treeRoot.querySelector('.erp-tree-item[data-id="' + tab.itemId + '"]');
          // Fallback: pokud item nenajdeme přes itemId, zkus přes cislo_def
          if (!treeItem) {
            treeItem = treeRoot.querySelector(
              '.erp-tree-item[data-cislo-def="' + tab.cislo + '"]'
            );
          }
          if (treeItem) {
            const row = treeItem.querySelector(":scope > .erp-tree-row");
            if (row) row.classList.add("active");
            saveActive(String(tab.cislo));
            // Expand všechny parent containers aby active row byl visible
            expandAncestors(treeItem);
            // Scroll do středu viewport TreeRoot containeru — manuálně,
            // protože scrollIntoView({block:"nearest"}) nescrolluje pokud
            // je element úplně skrytý mimo scroll container.
            // Delay 80ms aby expand měl čas vykreslit (DOM layout pass).
            setTimeout(() => _scrollTreeRowIntoCenter(row), 80);
          }
        }
        saveTabsState();
        // Load data + render
        if (!tab.data) {
          await _loadTabData(tab);
        } else {
          _renderTabIntoMain(tab);
        }
      }

      function closeTab(idx) {
        if (idx < 0 || idx >= tabsState.tabs.length) return;
        const closedCislo = tabsState.tabs[idx].cislo;
        tabsState.tabs.splice(idx, 1);
        // B+8.1c: API persist tab close (fire-and-forget)
        _apiCall("DELETE", "/api/v1/erp/tabs/" + closedCislo);
        if (tabsState.tabs.length === 0) {
          tabsState.activeIndex = -1;
          // Cleanup grid + reset main content
          if (activeErpDataGrid) {
            try { activeErpDataGrid.destroy(); } catch (e) {}
            activeErpDataGrid = null;
          }
          mainContent.innerHTML =
            '<div class="erp-main-placeholder">' +
            '<h2>Vyber přehled ze stromu vlevo</h2>' +
            '<p>Klikni na uzel pro otevření přehledu jako záložka.</p>' +
            '</div>';
          treeRoot.querySelectorAll(".erp-tree-row.active").forEach(r => r.classList.remove("active"));
          saveActive("");
          renderTabsBar();
          saveTabsState();
          // B+10+++ (6.5.2026 Marti's drobnost): reset title + UI header
          // bez tab suffixu když všechny taby zavřené.
          try { document.title = "STRATEGIE"; } catch (e) {}
          try {
            const _hdrSep = document.getElementById("erpHeaderSep");
            const _hdrPre = document.getElementById("erpHeaderPrehled");
            if (_hdrSep) _hdrSep.setAttribute("hidden", "");
            if (_hdrPre) _hdrPre.textContent = "";
          } catch (e) {}
          return;
        }
        // Auto-switch — pokud se zavřel aktivní, jdi na předchozí (nebo první)
        if (idx <= tabsState.activeIndex) {
          tabsState.activeIndex = Math.max(0, tabsState.activeIndex - 1);
        }
        renderTabsBar();
        saveTabsState();
        switchTab(tabsState.activeIndex);
      }

      function renderTabsBar() {
        if (!tabsBarEl) return;
        if (tabsState.tabs.length === 0) {
          tabsBarEl.setAttribute("hidden", "");
          tabsBarEl.innerHTML = "";
          return;
        }
        tabsBarEl.removeAttribute("hidden");
        let html = "";
        tabsState.tabs.forEach((t, i) => {
          const active = (i === tabsState.activeIndex);
          html += '<div class="erp-tab' + (active ? ' active' : '') +
                  '" data-tab-idx="' + i + '" title="' + escapeAttr(t.label) + '">';
          html += '<span class="erp-tab-label">' + escapeHtml(t.label) + '</span>';
          html += '<button type="button" class="erp-tab-close" data-tab-close="' + i +
                  '" title="Zavřít záložku">×</button>';
          html += '</div>';
        });
        html += '<button type="button" class="erp-tab-add" id="erpTabAdd" ' +
                'title="Otevřít nový přehled (vyber ve stromu)">+</button>';
        tabsBarEl.innerHTML = html;
        // Event delegation
        tabsBarEl.querySelectorAll(".erp-tab").forEach(el => {
          el.addEventListener("click", (ev) => {
            if (ev.target.classList.contains("erp-tab-close")) return;
            const idx = parseInt(el.getAttribute("data-tab-idx"), 10);
            if (!isNaN(idx)) switchTab(idx);
          });
        });
        tabsBarEl.querySelectorAll(".erp-tab-close").forEach(el => {
          el.addEventListener("click", (ev) => {
            ev.stopPropagation();
            const idx = parseInt(el.getAttribute("data-tab-close"), 10);
            if (!isNaN(idx)) closeTab(idx);
          });
        });
        const addBtn = document.getElementById("erpTabAdd");
        if (addBtn && treeSearchInput) {
          addBtn.addEventListener("click", () => {
            // + button = focus tree filter (pak user vybere přehled = openTab)
            if (workspaceEl && workspaceEl.classList.contains("tree-collapsed")) {
              applyTreeCollapsed(false);
              saveTreeCollapsed(false);
            }
            try { treeSearchInput.focus(); treeSearchInput.select(); } catch (e) {}
          });
        }
      }

      async function _loadTabData(tab) {
        const userLimit = loadPrehledLimit(tab.cislo);
        const url = userLimit
          ? ("/api/v1/erp/prehled/" + tab.cislo + "?limit=" + userLimit)
          : ("/api/v1/erp/prehled/" + tab.cislo);
        const itemId = tab.itemId;
        const breadcrumb = itemId ? buildBreadcrumbHtml(itemId) : "";
        mainContent.innerHTML =
          '<div class="erp-prehled-header">' +
          '<div class="erp-bc-path">' + breadcrumb + '</div>' +
          '<div class="erp-prehled-loading">' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line"></div>' +
          '<div class="erp-skel-line short"></div>' +
          '</div>' +
          '<div class="erp-prehled-loading-msg">Načítám přehled #' + tab.cislo + '…</div>' +
          '</div>';
        try {
          const r = await fetch(url, { credentials: "include" });
          if (!r.ok) {
            mainContent.innerHTML =
              '<div class="erp-main-error">Přehled #' + tab.cislo +
              ' nelze načíst: Status ' + r.status + '</div>';
            return;
          }
          const data = await r.json();
          tab.data = data;
          _renderTabIntoMain(tab);
        } catch (e) {
          mainContent.innerHTML =
            '<div class="erp-main-error">Chyba: ' +
            escapeHtml(e.message || String(e)) + '</div>';
        }
      }

      function _renderTabIntoMain(tab) {
        // B+2: auto-close jádro pane (jiný přehled = jiný kontext)
        if (currentJadro) closeJadroPane();
        const data = tab.data;
        if (!data) return;
        const itemId = tab.itemId;
        const breadcrumb = itemId ? buildBreadcrumbHtml(itemId) : "";
        // Reuse existing renderPrehled logic (refactored)
        renderPrehled(tab.cislo, { getAttribute: (k) => k === "data-id" ? itemId : null }, data, breadcrumb);
        // Restore grid state pokud cached
        if (tab.gridState && activeErpDataGrid && activeErpDataGrid.gridApi) {
          setTimeout(() => {
            try {
              if (tab.gridState.columnState) {
                activeErpDataGrid.gridApi.applyColumnState({
                  state: tab.gridState.columnState,
                  applyOrder: true,
                });
              }
              if (tab.gridState.filterModel) {
                activeErpDataGrid.gridApi.setFilterModel(tab.gridState.filterModel);
              }
            } catch (e) {}
          }, 30);
        }
      }

      // Restore tabs state z localStorage (po loadTree() — potřebujeme tree pro itemId resolve)
      function restoreTabsFromStorage() {
        const persisted = loadTabsState();
        if (!persisted || !persisted.tabs || persisted.tabs.length === 0) return;
        // Re-create tab metadata (data + gridState se znovu fetchnou)
        tabsState.tabs = persisted.tabs.map(t => ({
          cislo: t.cislo,
          itemId: t.itemId,
          label: t.label,
          data: null,
          gridState: null,
        }));
        const idx = (persisted.activeIndex >= 0 && persisted.activeIndex < tabsState.tabs.length)
          ? persisted.activeIndex
          : 0;
        renderTabsBar();
        switchTab(idx);
      }

      // B+8.1c (6.5.2026): API hydration — fetch user state z DB,
      // seed localStorage cache, pak loadTree() + restoreTabsFromStorage().
      // Write-through pattern: API = source of truth, localStorage = cache.
      // Pokud API fail (offline/network), fallback na localStorage.
      async function hydrateUserStateFromAPI() {
        try {
          const [tabsR, favR, recR, ordR] = await Promise.all([
            _apiCall("GET", "/api/v1/erp/tabs"),
            _apiCall("GET", "/api/v1/erp/favorites"),
            _apiCall("GET", "/api/v1/erp/recent"),
            _apiCall("GET", "/api/v1/erp/tree-order"),
          ]);
          // Tabs → seed localStorage (restoreTabsFromStorage to pak prečte)
          if (tabsR && Array.isArray(tabsR.tabs)) {
            const persist = {
              tabs: tabsR.tabs.map(t => ({
                cislo: t.cislo,
                itemId: t.itemId,
                label: t.label,
              })),
              activeIndex: (typeof tabsR.activeIndex === "number")
                ? tabsR.activeIndex : -1,
            };
            try { localStorage.setItem(TABS_STATE_KEY, JSON.stringify(persist)); }
            catch (e) {}
          }
          // Favorites → seed (jen čísla — UI z čísel rekonstruuje)
          if (favR && Array.isArray(favR.favorites)) {
            const arr = favR.favorites
              .map(f => parseInt(f.cislo, 10))
              .filter(n => !isNaN(n));
            try { localStorage.setItem(TREE_FAVORITES_KEY, JSON.stringify(arr)); }
            catch (e) {}
          }
          // Recent → seed (cislo + label + ts derivovaný z lastUsedAt)
          if (recR && Array.isArray(recR.recent)) {
            const arr = recR.recent.map(r => ({
              cislo: parseInt(r.cislo, 10),
              label: r.label || ("Přehled #" + r.cislo),
              ts: r.lastUsedAt ? Date.parse(r.lastUsedAt) : Date.now(),
            })).filter(r => !isNaN(r.cislo));
            try { localStorage.setItem(TREE_RECENT_KEY, JSON.stringify(arr)); }
            catch (e) {}
          }
          // Tree order → seed (server vrací map group_key → array)
          if (ordR && ordR.order && typeof ordR.order === "object") {
            try { localStorage.setItem(TREE_ORDER_KEY, JSON.stringify(ordR.order)); }
            catch (e) {}
          }
        } catch (e) {
          console.warn("hydrateUserStateFromAPI failed, using localStorage cache", e);
        }
      }

      // B+10+++ (Marti's drobnost 6.5.2026 — 5 minut před odjezdem):
      // Marti-AI ploška v hlavičce — fetch default persona avatar + click
      // otevře chat v novém tabu (žádný interrupt aktuálního ERP workflow).
      (async () => {
        try {
          const r = await fetch("/api/v1/personas/list", { credentials: "include" });
          if (!r.ok) return;
          const data = await r.json();
          const personas = (data && (data.personas || data.items || data)) || [];
          const list = Array.isArray(personas) ? personas : [];
          // Default persona — is_default first, fallback first persona
          const def = list.find(p => p.is_default || p.is_default_persona)
                   || list.find(p => p.name && p.name.toLowerCase().includes("marti"))
                   || list[0];
          if (def && def.id) {
            const img = document.getElementById("erpMartiAiAvatar");
            if (img) img.src = "/api/v1/personas/" + def.id + "/avatar";
            const lbl = document.querySelector(".erp-marti-btn-label");
            if (lbl && def.name) {
              // Marti-AI default → "Tvoje Marti" (drobnost po návratu).
              // Non-default persona → "Tvoje <name>".
              const isMarti = (def.name || "").toLowerCase().includes("marti");
              lbl.textContent = isMarti ? "Tvoje Marti" : ("Tvoje " + def.name);
            }
          }
        } catch (e) { /* silent fallback */ }
      })();
      const _martiBtn = document.getElementById("erpMartiAiBtn");
      if (_martiBtn) {
        _martiBtn.addEventListener("click", () => {
          // B+10+++++ (Marti's drobnost 6.5.2026 po návratu): named target
          // místo "_blank" — když okno chatu už existuje, druhý klik ho jen
          // **focusne**, neotevře nové. Marti: "Klikem na Moje Marti se
          // otevre nove okno s chatem... Dalsim klikem dalsi a dalsi...
          // To je zmatek. Je treba mit vzdy jen jedno okno s chatem."
          const w = window.open("/", "strategie-chat");
          if (w) {
            try { w.focus(); } catch (e) {}
          }
        });
      }
      // B+10+++++ (Marti's drobnost 6.5.2026 po návratu): zakázat browser
      // native context menu na celém ERP workspace (Marti: "ty hnusne
      // systemove okna na pravy klik mysi jeste neodeznely"). AG Grid
      // option preventDefaultOnContextMenu nepokryje status bar / column
      // headers / blank space — JS event listener jako pojistka.
      // Workspace area (.erp-workspace) je hlavní target. Na přehled tabs,
      // input fields apod. potřebujeme right-click ponechat (paste, undo).
      document.addEventListener("contextmenu", (ev) => {
        const t = ev.target;
        if (!t || !t.closest) return;
        // Allow right-click jen na input/textarea (paste, undo) — vše jiné
        // suprimovat. Plus tree pane má vlastní context menu (Phase B+8.2a+).
        if (t.closest("input, textarea, .erp-tree-row")) return;
        ev.preventDefault();
      });

      // B+10++++ (Marti's drobnost 6.5.2026 po návratu): Ctrl+Shift+klik
      // na logo = hard reset (vymaž SW cache + force reload). Default klik
      // ponechán jako navigate na /erp/ (soft reload).
      const _logoLink = document.getElementById("erpLogoLink");
      if (_logoLink) {
        _logoLink.addEventListener("click", async (ev) => {
          if (ev.ctrlKey && ev.shiftKey) {
            ev.preventDefault();
            // Hard reset — clear SW caches + force reload bypass cache
            try {
              if ("caches" in window) {
                const keys = await caches.keys();
                await Promise.all(keys.map(k => caches.delete(k)));
              }
              if ("serviceWorker" in navigator) {
                const regs = await navigator.serviceWorker.getRegistrations();
                await Promise.all(regs.map(r => r.unregister()));
              }
            } catch (e) { /* silent */ }
            location.reload();
          }
        });
      }

      // Bootstrap: hydrate API → loadTree → restore tabs.
      // Použij .finally() aby loadTree() běžela i při API fail (offline mode).
      hydrateUserStateFromAPI().finally(() => {
        loadTree();
        // Po load tree (async) zkus restore tabs — počkej krátce na DOM
        setTimeout(restoreTabsFromStorage, 200);
      });
    })();
    </script>
    '''
    return _render_full_page(
        title="STRATEGIE ERP",
        content=content,
        breadcrumb=[],
        user_id=user_id,
    )


def _render_error_page(title: str, msg: str) -> str:
    """Error page (404 / 500) — STRATEGIE BLACK theme."""
    content = f'''
    <div class="erp-error">
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(msg)}</p>
      <p style="margin-top: 16px;"><a href="/erp/">← Zpět na ERP home</a></p>
    </div>
    '''
    return _render_full_page(
        title=title,
        content=content,
        breadcrumb=[("ERP", "/erp/"), ("Chyba", None)],
    )
