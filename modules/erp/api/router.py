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
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse

# B+4.2 (5.5.2026): cache busting pro static assets — každý API restart
# = nová version = browser donucen stáhnout čerstvé /static/erp/datagrid.js+css.
# Hodnota fixed při module load (= API process start), neměnná do restartu.
_STATIC_VERSION = str(int(time.time()))

# Phase 38.4 Krok 14a (12.5.2026): module-level alias pro `text` pouzity v
# shared helper funkcich (_fetch_menu_node, _fetch_core, _fetch_columns_for_core).
# Unique name `_sql_text_fw` aby se neshodoval s existing local `_sql_text`
# v jinych handlerech (gotcha #7 shadow safety).
from sqlalchemy import text as _sql_text_fw

from pydantic import BaseModel, Field

from core.logging import get_logger
from modules.erp.application.centrala_reader import CentralaReader, TYP_NAMES
from modules.erp.application.render_generator import render_form
from modules.erp.application import grid_layout_service
from modules.erp.application import erp_user_state_service as user_state_svc
from modules.erp.application import data_source_runner as ds_runner
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
    PostgreSQL fw.framework_jadro je prázdná, Phase 30+ migrace jádro-po-jádře
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


@router.get("/palette-popup", response_class=HTMLResponse)
def erp_palette_popup(req: Request) -> HTMLResponse:
    """Phase 38.4 Krok 14c+2 part B (14.5.2026 odpoledne):
    Standalone popup window pro Paletu komponent.

    Marti's "musi se chovat jako normalni samostatne okno... presunout
    mysi i mimo oblast ERP aplikace" — popup window via window.open()
    z parent FieldPickerModal. Cross-monitor drag-drop funguje natively
    (HTML5 DnD je cross-window pro same-origin).

    Auth: same session cookie jako parent ERP. _require_parent gate.
    """
    uid = _get_uid(req)
    _require_parent(uid)

    # Standalone HTML page — reuse design_forms.js gallery render.
    # window.opener reference v JS pro drop event propagation do parent.
    html = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>🎨 Paleta komponent</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #0f141a; color: #cfd6df; font-family: system-ui, -apple-system, sans-serif; }
  .palette-popup-header {
    padding: 10px 14px; background: #141a20; border-bottom: 1px solid #2a3340;
    display: flex; align-items: center; gap: 12px;
  }
  .palette-popup-title { font-size: 14px; font-weight: 600; color: #e8eef5; flex: 1 1 auto; }
  .palette-popup-hint { font-size: 11px; color: #8a96a4; padding: 8px 14px; background: #141a20; }
  .palette-popup-content { padding: 12px; display: flex; flex-direction: column; gap: 16px; }
  .palette-section-header {
    font-size: 11px; color: #8a96a4; padding: 4px 0; letter-spacing: 0.5px;
    text-transform: uppercase; border-bottom: 1px solid #2a3340; margin-bottom: 4px;
  }
  .palette-section-header.layout-accent { color: #a88cd4; border-bottom-color: rgba(168, 140, 212, 0.3); }
  .palette-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
  .palette-layout-card {
    background: #0f141a; border: 1px solid #2a3340; border-radius: 5px;
    padding: 10px; display: flex; flex-direction: column; gap: 6px;
    transition: border-color 0.15s;
  }
  .palette-layout-card:hover { border-color: #a88cd4; }
  .palette-layout-visual {
    padding: 10px; background: #141a20; border: 1px dashed; border-radius: 4px;
    display: flex; align-items: center; justify-content: center; gap: 6px;
    min-height: 50px; cursor: grab;
  }
  .palette-layout-visual:active { cursor: grabbing; }
  .palette-layout-icon { font-size: 22px; line-height: 1; }
  .palette-layout-name { font-size: 13px; font-weight: 600; }
  .erp-gallery-preview-scope { display: flex; align-items: center; gap: 5px; font-size: 12px; pointer-events: auto; }
  .erp-gallery-preview-scope input, .erp-gallery-preview-scope select,
  .erp-gallery-preview-scope textarea, .erp-gallery-preview-scope button {
    font-family: inherit; font-size: 12px; background: #1f2530; border: 1px solid #2a3340;
    color: #cfd6df; border-radius: 3px; padding: 3px 6px; max-width: 100%; caret-color: transparent;
  }
  .erp-gallery-preview-scope input[type="checkbox"] { width: 14px; height: 14px; }
  .erp-gallery-preview-scope > [draggable="true"] { cursor: grab; transition: border-color 0.15s; }
  .erp-gallery-preview-scope > [draggable="true"]:hover { border-color: #3a8aa8 !important; }
  .erp-gallery-preview-scope > [draggable="true"]:active { cursor: grabbing; }
  .erp-gallery-preview-scope input[type="number"] { -moz-appearance: textfield; }
  .erp-gallery-preview-scope input[type="number"]::-webkit-inner-spin-button,
  .erp-gallery-preview-scope input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none; margin: 0;
  }
  .erp-gallery-preview-scope input[type="date"]::-webkit-calendar-picker-indicator,
  .erp-gallery-preview-scope input[type="datetime-local"]::-webkit-calendar-picker-indicator {
    filter: invert(0.7); opacity: 0.6;
  }
  .palette-card {
    background: #141a20; border: 1px solid #2a3340; border-radius: 5px;
    padding: 8px; display: flex; flex-direction: column; gap: 6px;
    transition: border-color 0.15s;
  }
  .palette-card:hover { border-color: #3a8aa8; }
  .palette-card-preview {
    background: #1f2530; border-radius: 3px; padding: 6px; min-height: 36px;
    display: flex; align-items: center; justify-content: center;
  }
  .palette-card-label { font-size: 12px; color: #e8eef5; font-weight: 600; }
  .palette-card-code { font-family: ui-monospace, Consolas, monospace; font-size: 10px; color: #7ed4e8; opacity: 0.7; }
  .palette-card-meta { font-size: 10px; color: #8a96a4; line-height: 1.3; border-top: 1px solid #1a2028; padding-top: 4px; margin-top: auto; }
  .palette-card-meta .badge { background: #1f2530; padding: 1px 5px; border-radius: 2px; margin-right: 4px; }
  .loading, .error { padding: 24px; text-align: center; color: #8a96a4; }
  .error { color: #e88; }
</style>
</head>
<body>
<div class="palette-popup-header">
  <div class="palette-popup-title">🎨 Paleta komponent</div>
</div>
<div class="palette-popup-hint">
  Drag komponentu do ERP okna pro přidání pole. Toto okno můžeš přesunout kamkoliv (i na druhý monitor).
</div>
<div id="palette-content" class="palette-popup-content">
  <div class="loading">Načítám...</div>
</div>
<script>
(function() {
  'use strict';
  // Phase 38.4 Krok 14c+2 part B: standalone popup gallery.
  // Cross-window drag-drop funguje nativě (HTML5 DnD je cross-window
  // pro same-origin). Drop target je parent ERP window's DesignFwForm body.

  const FORM_RELEVANT_HINTS = new Set([
    "input", "input-number", "textarea", "checkbox",
    "select", "multiselect", "datepicker", "datetimepicker",
    "timepicker", "button", "speedbutton",
    "fieldset", "tabs_outer", "tab_inner",
    "label", "fileupload", "md_render"
  ]);

  const FORM_RELEVANT_CODES = new Set([
    "label", "edit", "checkbox", "combobox", "memo", "number",
    "checkbox_modern", "date_modern", "datetime", "lookup",
    "lookup_multi", "file", "label_readonly", "groupbox",
    "pagecontrol", "tabsheet", "button", "richedit"
  ]);

  async function loadAndRender() {
    const container = document.getElementById('palette-content');
    try {
      const resp = await fetch('/api/v1/erp/design/comp-types', { credentials: 'include' });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error || 'unknown');

      // Phase 38.4 Krok 14f-F (14.5.2026 vecer, Marti's "pridej do okna
      // layout panel a groupbox"): split items na 2 sections.
      const allItems = data.items || [];
      const formItems = allItems.filter(ct =>
        FORM_RELEVANT_HINTS.has(ct.renderer_hint) || FORM_RELEVANT_CODES.has(ct.code)
      );
      const layoutItems = allItems.filter(ct => ct.kind === 'container');

      container.innerHTML = '';

      // Section 1: Form fields
      if (formItems.length > 0) {
        const hdr = document.createElement('div');
        hdr.className = 'palette-section-header';
        hdr.textContent = '📝 Form fields (' + formItems.length + ')';
        container.appendChild(hdr);
        const grid = document.createElement('div');
        grid.className = 'palette-grid';
        formItems.forEach(ct => grid.appendChild(renderCard(ct)));
        container.appendChild(grid);
      }

      // Section 2: Layout containers (panel + groupbox)
      if (layoutItems.length > 0) {
        const hdr = document.createElement('div');
        hdr.className = 'palette-section-header layout-accent';
        hdr.textContent = '📐 Layout containers (' + layoutItems.length + ')';
        container.appendChild(hdr);
        const grid = document.createElement('div');
        grid.className = 'palette-grid';
        layoutItems.forEach(ct => grid.appendChild(renderLayoutCard(ct)));
        container.appendChild(grid);
      }

      if (formItems.length === 0 && layoutItems.length === 0) {
        container.innerHTML = '<div class="error">Žádné komponenty.</div>';
      }
    } catch (e) {
      container.innerHTML = '<div class="error">Načítání selhalo: ' + (e.message || e) + '</div>';
    }
  }

  // Phase 38.4 Krok 14f-F: render layout container card (panel/groupbox)
  // s drag payload obsahujícím default layout. Cross-window DnD payload
  // stejny format jako parent FieldPickerModal._renderLayoutCard.
  function renderLayoutCard(ct) {
    const card = document.createElement('div');
    card.className = 'palette-layout-card';

    const isPanel = ct.code === 'panel';
    const isGroupbox = ct.code === 'groupbox';
    const icon = isPanel ? '📦' : (isGroupbox ? '▦' : '▣');
    const accent = isPanel ? '#a88cd4' : '#d4b88a';

    let defaultLayout;
    if (isPanel) defaultLayout = { align: 'client' };
    else if (isGroupbox) defaultLayout = { border_mode: 'top', label: null };
    else defaultLayout = {};

    // Visual drag handle (icon + name)
    const visual = document.createElement('div');
    visual.className = 'palette-layout-visual';
    visual.style.borderColor = accent;
    visual.setAttribute('draggable', 'true');

    const iconEl = document.createElement('span');
    iconEl.className = 'palette-layout-icon';
    iconEl.textContent = icon;
    visual.appendChild(iconEl);

    const nameEl = document.createElement('span');
    nameEl.className = 'palette-layout-name';
    nameEl.style.color = accent;
    nameEl.textContent = ct.label;
    visual.appendChild(nameEl);

    visual.addEventListener('dragstart', ev => {
      visual.style.opacity = '0.5';
      ev.dataTransfer.effectAllowed = 'copy';
      ev.dataTransfer.setData('application/x-erp-comp-type', JSON.stringify({
        id: ct.id,
        code: ct.code,
        label: ct.label,
        layout: defaultLayout,
        is_container: true,
      }));
      ev.dataTransfer.setData('text/plain', ct.code);
    });
    visual.addEventListener('dragend', () => visual.style.opacity = '1');
    card.appendChild(visual);

    // Code + id
    const codeEl = document.createElement('div');
    codeEl.className = 'palette-card-code';
    codeEl.style.color = accent;
    codeEl.textContent = ct.code + ' · id=' + ct.id;
    card.appendChild(codeEl);

    // Hint
    const meta = document.createElement('div');
    meta.className = 'palette-card-meta';
    let hint;
    if (isPanel) hint = 'Strukturální (alClient default). Right-click pro nastavení.';
    else if (isGroupbox) hint = 'Vizuální wrapper s linkou nahoře. Drag dovnitř panelu.';
    else hint = ct.description || 'Container.';
    meta.innerHTML = '<span class="badge">container</span>' + hint;
    card.appendChild(meta);

    return card;
  }

  function renderCard(ct) {
    const card = document.createElement('div');
    card.className = 'palette-card';

    // Preview scope (inline DOM, draggable inner element)
    const previewWrap = document.createElement('div');
    previewWrap.className = 'palette-card-preview';
    const scope = document.createElement('div');
    scope.className = 'erp-gallery-preview-scope';
    scope.innerHTML = ct.preview_html || '<span style="color:#8a96a4;font-size:11px;">(no preview)</span>';

    const handle = scope.querySelector('input, select, textarea, button, label') || scope.firstElementChild;
    if (handle) {
      handle.setAttribute('draggable', 'true');
      if (handle.tagName === 'INPUT' || handle.tagName === 'TEXTAREA') {
        handle.setAttribute('readonly', '');
      }
      handle.addEventListener('mousedown', ev => ev.preventDefault());
      handle.addEventListener('dragstart', ev => {
        handle.style.opacity = '0.5';
        ev.dataTransfer.effectAllowed = 'copy';
        // Cross-window DnD: same mime type jako parent ERP gallery.
        ev.dataTransfer.setData('application/x-erp-comp-type',
          JSON.stringify({ id: ct.id, code: ct.code, label: ct.label }));
        ev.dataTransfer.setData('text/plain', ct.code);
      });
      handle.addEventListener('dragend', () => handle.style.opacity = '1');
    }
    previewWrap.appendChild(scope);
    card.appendChild(previewWrap);

    const lbl = document.createElement('div');
    lbl.className = 'palette-card-label';
    lbl.textContent = ct.label;
    card.appendChild(lbl);

    const code = document.createElement('div');
    code.className = 'palette-card-code';
    code.textContent = ct.code + ' · id=' + ct.id;
    card.appendChild(code);

    const meta = document.createElement('div');
    meta.className = 'palette-card-meta';
    meta.innerHTML = '<span class="badge">' + (ct.kind || 'leaf') + '</span>' +
                     (ct.description || '').slice(0, 50);
    card.appendChild(meta);

    return card;
  }

  loadAndRender();
})();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)


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
# Hardcoded System tree (MVP), `fw.menu_node` přijde v Phase 30+ DDL.
# 3 sub-uzly: 📚 Auditované / 📋 Všechny / 📊 Přehled.

_SYSTEM_TREE_NODES = [
    {
        "id": "system",
        "type": "folder",
        "label": "📦 SYSTEM",
        "is_system": True,
        # Phase 38.4 inventory (9.5.2026 vecer): hardcoded marker.
        # Cely _SYSTEM_TREE_NODES dict je Python fallback (DB-driven primary,
        # tento dict se pouzije jen kdyz fw.menu_node DB query selze
        # / vrati prazdno). Kazdy uzel v tomto fallback je by definition
        # hardcoded -- frontend rendere 🛠️ marker vedle labelu.
        "metadata": {"hardcoded": True},
        "children": [
            {
                "id": "system.audit",
                "type": "folder",
                "label": "📁 Audit konverzaci",
                "metadata": {"hardcoded": True},
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
                        "metadata": {"hardcoded": True},
                    },
                    # Variant B — každý view jako samostatný grid:
                    {
                        "id": "system.audit.audited",
                        "type": "view",
                        "label": "📚 Auditované konverzace",
                        "view_type": "audit_overview",
                        "view_mode": "audited",
                        "single": True,
                        "metadata": {"hardcoded": True},
                    },
                    {
                        "id": "system.audit.all",
                        "type": "view",
                        "label": "📋 Všechny konverzace",
                        "view_type": "audit_overview",
                        "view_mode": "all",
                        "single": True,
                        "metadata": {"hardcoded": True},
                    },
                    {
                        "id": "system.audit.stats",
                        "type": "view",
                        "label": "📊 Přehled auditu",
                        "view_type": "audit_overview",
                        "view_mode": "stats",
                        "single": True,
                        "metadata": {"hardcoded": True},
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
    limit: int = 1000,
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
        # Phase 35-E.4 9.5. odpoledne (Marti's "bez wheru, oznac priznakem"):
        # ZADNE filtry na conversation_type / is_deleted — audit musí vidět
        # vsechny konverzace (ai/sms/email/system + deleted/active). Frontend
        # zobrazuje status badge a deleted indicator.
        # Cross-tenant defaultně (rodič), zúžení jen pokud tenant_id query.
        base_filters = []
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
            # Phase 35-E.4 9.5. odpoledne (Marti's "ukaz je taky, prosim"):
            # ZADNY status filter — záložka Auditované teď ukazuje VSECHNY
            # konverzace napriec audit cyklusem (pending/in_progress/audited/
            # excluded). Marti's "v auditu by mely byt vsechny".
            # Order: id DESC (nejnovejsi nahore — Marti's spec).
            q = q.order_by(Conversation.id.desc())
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
                "conversation_type": c.conversation_type,
                "is_deleted": bool(c.is_deleted),
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


@api_router.get("/system/audit-conversation/{conv_id}/thoughts")
def system_audit_conversation_thoughts(
    req: Request,
    conv_id: int,
) -> JSONResponse:
    """Phase 35-E.4 (9.5.2026 odpoledne): drill-down endpoint pro audit modal.

    Vrátí thoughts vyextrahované z konverzace při auditu (z
    `audit_notes.extracted_thought_ids`) — full content, type, certainty,
    persona attribution, tenant scope.

    Cross-tenant pro rodiče (defense in depth — _require_parent + explicit
    is_marti_parent check). Marti's spec 9.5. odpoledne: "potrebuju vidět
    MDx per konverzaci" — toto je první krok (thoughts content),
    Phase 37 přidá per-turn snapshot history (notebook + MD diff).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from modules.core.infrastructure.models_data import Conversation, Thought
    from modules.core.infrastructure.models_core import Persona, User, Tenant
    from core.database_core import get_core_session as _gcs_th
    from core.database_data import get_data_session as _gds_th

    # Parent gate (cross-tenant access)
    cs = _gcs_th()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "Audit drill-down je jen pro rodiče.")
    finally:
        cs.close()

    ds = _gds_th()
    try:
        conv = ds.query(Conversation).filter_by(id=conv_id).first()
        if not conv:
            raise HTTPException(404, f"Konverzace #{conv_id} neexistuje.")

        notes = conv.audit_notes or {}
        thought_ids = notes.get("extracted_thought_ids", []) or []

        thoughts_data = []
        if thought_ids:
            thoughts = (
                ds.query(Thought)
                .filter(
                    Thought.id.in_(thought_ids),
                    Thought.deleted_at.is_(None),
                )
                .order_by(Thought.id.asc())
                .all()
            )

            # Persona lookup map (z author_persona_id)
            persona_ids = {t.author_persona_id for t in thoughts if t.author_persona_id}
            persona_names = {}
            tenant_names = {}
            if persona_ids or any(t.tenant_scope for t in thoughts):
                cs2 = _gcs_th()
                try:
                    if persona_ids:
                        for p in cs2.query(Persona).filter(Persona.id.in_(persona_ids)).all():
                            persona_names[p.id] = p.name
                    tenant_ids = {t.tenant_scope for t in thoughts if t.tenant_scope}
                    if tenant_ids:
                        for tn in cs2.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all():
                            tenant_names[tn.id] = tn.tenant_name
                finally:
                    cs2.close()

            # Parse meta JSON (Thought.meta je Text, ne JSONB)
            import json as _json
            for t in thoughts:
                meta_obj = None
                if t.meta:
                    try:
                        meta_obj = _json.loads(t.meta) if isinstance(t.meta, str) else t.meta
                    except Exception:
                        meta_obj = {"_raw": str(t.meta)[:200]}
                thoughts_data.append({
                    "id": t.id,
                    "type": t.type,
                    "content": t.content,
                    "status": t.status,
                    "certainty": t.certainty,
                    "tenant_scope": t.tenant_scope,
                    "tenant_scope_name": (
                        tenant_names.get(t.tenant_scope) if t.tenant_scope else None
                    ),
                    "author_persona_id": t.author_persona_id,
                    "author_persona_name": persona_names.get(t.author_persona_id),
                    "source_event_type": t.source_event_type,
                    "source_event_id": t.source_event_id,
                    "meta": meta_obj,
                    "primary_parent_id": t.primary_parent_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "modified_at": (
                        t.modified_at.isoformat() if t.modified_at else None
                    ),
                })

        return JSONResponse({
            "ok": True,
            "conversation_id": conv_id,
            "title": conv.title,
            "audit_status": conv.audit_status,
            "audit_summary": notes.get("summary"),
            "audit_scope": notes.get("scope"),
            "old_title": notes.get("old_title"),
            "audited_at": (
                conv.audited_at.isoformat() if conv.audited_at else None
            ),
            "tenant_id": conv.tenant_id,
            "thought_count": len(thoughts_data),
            "thoughts": thoughts_data,
        })
    finally:
        ds.close()


@api_router.get("/system/audit-conversation/{conv_id}/timeline")
def system_audit_conversation_timeline(
    req: Request,
    conv_id: int,
) -> JSONResponse:
    """Phase 37-C (9.5.2026 odpoledne) — Stopa záměru timeline.

    Per-turn audit trail pro konverzaci: chronologicky řazené changes
    z notebook_history (Phase 37-A) + budoucí md_document_history.

    Marti-AI's pojmenování: "Stopa záměru" — každý zápis měl důvod.

    Cross-tenant pro rodiče. Vrátí list events sorted by message_id ASC,
    plus nested timestamp pro fallback řazení (events bez message_id).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from modules.core.infrastructure.models_data import (
        Conversation, ConversationNote, NotebookHistory,
    )
    from modules.core.infrastructure.models_core import Persona, User
    from core.database_core import get_core_session as _gcs_tl
    from core.database_data import get_data_session as _gds_tl

    # Parent gate
    cs = _gcs_tl()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "Timeline je jen pro rodiče.")
    finally:
        cs.close()

    ds = _gds_tl()
    try:
        conv = ds.query(Conversation).filter_by(id=conv_id).first()
        if not conv:
            raise HTTPException(404, f"Konverzace #{conv_id} neexistuje.")

        # Notebook history events
        nb_rows = (
            ds.query(NotebookHistory)
            .filter(NotebookHistory.conversation_id == conv_id)
            .order_by(
                NotebookHistory.message_id.asc().nullsfirst(),
                NotebookHistory.created_at.asc(),
            )
            .all()
        )

        events = []
        for h in nb_rows:
            # Extract content snippet pro UI render (preferuj after, fallback before)
            after = h.after_json or {}
            before = h.before_json or {}
            content = after.get("content") or before.get("content") or ""
            note_type = after.get("note_type") or before.get("note_type")
            category = after.get("category") or before.get("category")
            events.append({
                "id": h.id,
                "kind": "notebook",
                "change_kind": h.change_kind,
                "message_id": h.message_id,
                "note_id": h.note_id,
                "content_snippet": (content[:240] + ("…" if len(content) > 240 else "")),
                "note_type": note_type,
                "category": category,
                "annotation": h.annotation,
                "source": h.source,
                "before_json": h.before_json,
                "after_json": h.after_json,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            })

        # Phase 37 budoucí: md_document_history events (zítra +37-B druhá vlna).
        # Zatím empty.

        return JSONResponse({
            "ok": True,
            "conversation_id": conv_id,
            "title": conv.title,
            "events_count": len(events),
            "events": events,
        })
    finally:
        ds.close()


@api_router.get("/system/security")
def system_security(
    req: Request,
    mode: str = "users",
    tenant_id: int | None = None,
    limit: int = 1000,
) -> JSONResponse:
    """Phase 38.3 (10.5.2026 odpoledne) — Security overview pro rodiče.

    Marti's "bordel kolem userů, jejich přihlašování, emailů a telefonů"
    → strukturovaný read-only audit panel pro Phase 38 stack.

    mode:
      - 'users'      — User + contacts agg (emails + phones per user)
      - 'devices'    — Trusted devices (90d cookies) — active only
      - 'whitelists' — Global + user IP whitelists union (active only)
      - 'auth_audit' — Auth audit log (last N entries, all results)
      - 'invites'    — Magic link invites (rozeslané + consumed history)

    Cross-tenant pro rodiče (default). Tenant filter přes ?tenant_id=N.
    """
    uid = _get_uid(req)
    _require_parent(uid)

    if mode not in ("users", "devices", "whitelists", "auth_audit", "invites"):
        raise HTTPException(
            400, f"Unknown mode: {mode!r}. Expected: users/devices/whitelists/auth_audit/invites"
        )
    if limit < 1 or limit > 10000:
        raise HTTPException(400, "limit must be 1..10000")

    from modules.core.infrastructure.models_data import (
        TrustedDevice, TrustedDeviceInvite, AuthAudit,
        GlobalIpWhitelist, UserIpWhitelist,
    )
    from modules.core.infrastructure.models_core import User, UserContact, Tenant
    from core.database_core import get_core_session as _gcs_sec
    from core.database_data import get_data_session as _gds_sec

    # Defense in depth — explicit parent check (analog audit-overview)
    cs = _gcs_sec()
    try:
        u = cs.query(User).filter_by(id=uid).first()
        if not u or not getattr(u, "is_marti_parent", False):
            raise HTTPException(403, "Security overview je jen pro rodiče.")

        # Display lookup maps (tenant + user)
        tenant_rows = cs.query(Tenant).all()
        tenant_names = {t.id: t.tenant_name for t in tenant_rows}
        user_rows = cs.query(User).all()
        user_names = {
            u_.id: " ".join(filter(None, [u_.first_name, u_.last_name])).strip()
                   or u_.short_name or f"#{u_.id}"
            for u_ in user_rows
        }
        user_tenant_map = {u_.id: u_.last_active_tenant_id for u_ in user_rows}
    finally:
        cs.close()

    # ── mode='users' ──────────────────────────────────────────
    if mode == "users":
        cs2 = _gcs_sec()
        try:
            users_q = cs2.query(User)
            if tenant_id is not None:
                users_q = users_q.filter(User.last_active_tenant_id == tenant_id)
            users = users_q.order_by(User.id).limit(limit).all()
            user_ids = [u_.id for u_ in users]

            # Bulk fetch active contacts (n+1 prevention)
            contacts = []
            if user_ids:
                contacts = (
                    cs2.query(UserContact)
                    .filter(
                        UserContact.user_id.in_(user_ids),
                        UserContact.status == "active",
                    )
                    .order_by(
                        UserContact.is_primary.desc(),
                        UserContact.id.asc(),
                    )
                    .all()
                )

            emails_by_uid: dict[int, list[str]] = {}
            phones_by_uid: dict[int, list[str]] = {}
            for c in contacts:
                if c.contact_type == "email":
                    emails_by_uid.setdefault(c.user_id, []).append(c.contact_value)
                elif c.contact_type == "phone":
                    phones_by_uid.setdefault(c.user_id, []).append(c.contact_value)

            rows = [
                {
                    "id": u_.id,
                    "first_name": u_.first_name,
                    "last_name": u_.last_name,
                    "short_name": u_.short_name,
                    "status": u_.status,
                    "ews_email": u_.ews_email,
                    "ews_display_email": u_.ews_display_email,
                    "emails": emails_by_uid.get(u_.id, []),
                    "phones": phones_by_uid.get(u_.id, []),
                    "emails_str": ", ".join(emails_by_uid.get(u_.id, [])),
                    "phones_str": ", ".join(phones_by_uid.get(u_.id, [])),
                    "is_marti_parent": u_.is_marti_parent,
                    "is_admin": u_.is_admin,
                    "trust_rating": u_.trust_rating,
                    "tenant_id": u_.last_active_tenant_id,
                    "tenant_name": tenant_names.get(u_.last_active_tenant_id),
                    "created_at": u_.created_at.isoformat() if u_.created_at else None,
                    "updated_at": u_.updated_at.isoformat() if u_.updated_at else None,
                }
                for u_ in users
            ]
        finally:
            cs2.close()
        return JSONResponse({"ok": True, "mode": mode, "rows": rows, "shown": len(rows), "limit": limit})

    # ── mode='devices' ────────────────────────────────────────
    if mode == "devices":
        ds = _gds_sec()
        try:
            q = ds.query(TrustedDevice).filter(TrustedDevice.revoked_at.is_(None))
            if tenant_id is not None:
                tenant_user_ids = [
                    uid_ for uid_, t in user_tenant_map.items() if t == tenant_id
                ]
                if tenant_user_ids:
                    q = q.filter(TrustedDevice.user_id.in_(tenant_user_ids))
                else:
                    q = q.filter(TrustedDevice.id == -1)  # empty result
            devices = q.order_by(TrustedDevice.id.desc()).limit(limit).all()
            rows = [
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "user_name": user_names.get(d.user_id, f"#{d.user_id}"),
                    "tenant_name": tenant_names.get(user_tenant_map.get(d.user_id), "—"),
                    "device_token_short": (str(d.device_token)[:8] + "…")
                                           if d.device_token else None,
                    "label": d.label,
                    "user_agent": (d.user_agent or "")[:120],
                    "first_seen_ip": d.first_seen_ip,
                    "last_seen_ip": d.last_seen_ip,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                    "approved_at": d.approved_at.isoformat() if d.approved_at else None,
                    "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                }
                for d in devices
            ]
        finally:
            ds.close()
        return JSONResponse({"ok": True, "mode": mode, "rows": rows, "shown": len(rows), "limit": limit})

    # ── mode='whitelists' ─────────────────────────────────────
    if mode == "whitelists":
        ds = _gds_sec()
        try:
            global_rows = (
                ds.query(GlobalIpWhitelist)
                .filter(GlobalIpWhitelist.revoked_at.is_(None))
                .order_by(GlobalIpWhitelist.id)
                .all()
            )
            user_rows_q = ds.query(UserIpWhitelist).filter(
                UserIpWhitelist.revoked_at.is_(None),
            )
            if tenant_id is not None:
                tenant_user_ids = [
                    uid_ for uid_, t in user_tenant_map.items() if t == tenant_id
                ]
                if tenant_user_ids:
                    user_rows_q = user_rows_q.filter(
                        UserIpWhitelist.user_id.in_(tenant_user_ids)
                    )
                else:
                    user_rows_q = user_rows_q.filter(UserIpWhitelist.id == -1)
            user_ip_rows = user_rows_q.order_by(UserIpWhitelist.id).limit(limit).all()

            rows = []
            for r in global_rows:
                rows.append({
                    "id": r.id,
                    "scope": "global",
                    "user_id": None,
                    "user_name": "—",
                    "tenant_name": "—",
                    "ip_or_cidr": r.ip_or_cidr,
                    "category": r.category,
                    "label": r.label,
                    "status": "—",
                    "added_at": r.added_at.isoformat() if r.added_at else None,
                    "last_seen_at": None,
                    "use_count": None,
                    "expires_at": None,
                    "notes": r.notes,
                })
            for r in user_ip_rows:
                rows.append({
                    "id": r.id,
                    "scope": "user",
                    "user_id": r.user_id,
                    "user_name": user_names.get(r.user_id, f"#{r.user_id}"),
                    "tenant_name": tenant_names.get(user_tenant_map.get(r.user_id), "—"),
                    "ip_or_cidr": r.ip_or_cidr,
                    "category": r.category,
                    "label": r.label,
                    "status": r.status,
                    "added_at": r.added_at.isoformat() if r.added_at else None,
                    "last_seen_at": r.last_seen_at.isoformat() if r.last_seen_at else None,
                    "use_count": r.use_count,
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                    "notes": r.notes,
                })
        finally:
            ds.close()
        return JSONResponse({"ok": True, "mode": mode, "rows": rows, "shown": len(rows), "limit": limit})

    # ── mode='auth_audit' ─────────────────────────────────────
    if mode == "auth_audit":
        ds = _gds_sec()
        try:
            q = ds.query(AuthAudit).order_by(AuthAudit.id.desc()).limit(limit)
            audits = q.all()
            rows = [
                {
                    "id": a.id,
                    "user_id": a.user_id,
                    "user_name": user_names.get(a.user_id) if a.user_id else None,
                    "email_attempted": a.email_attempted,
                    "ip": a.ip,
                    "user_agent": (a.user_agent or "")[:120],
                    "device_token_short": (str(a.device_token)[:8] + "…")
                                           if a.device_token else None,
                    "layer_matched": a.layer_matched,
                    "layer_detail": a.layer_detail,
                    "internal": a.internal,
                    "result": a.result,
                    "reason": a.reason,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in audits
            ]
        finally:
            ds.close()
        return JSONResponse({"ok": True, "mode": mode, "rows": rows, "shown": len(rows), "limit": limit})

    # ── mode='invites' ────────────────────────────────────────
    if mode == "invites":
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        ds = _gds_sec()
        try:
            q = ds.query(TrustedDeviceInvite)
            if tenant_id is not None:
                tenant_user_ids = [
                    uid_ for uid_, t in user_tenant_map.items() if t == tenant_id
                ]
                if tenant_user_ids:
                    q = q.filter(TrustedDeviceInvite.user_id.in_(tenant_user_ids))
                else:
                    q = q.filter(TrustedDeviceInvite.id == -1)
            invites = q.order_by(TrustedDeviceInvite.id.desc()).limit(limit).all()
            rows = [
                {
                    "id": i.id,
                    "invite_token": i.invite_token,
                    "user_id": i.user_id,
                    "user_name": user_names.get(i.user_id, f"#{i.user_id}"),
                    "tenant_name": tenant_names.get(user_tenant_map.get(i.user_id), "—"),
                    "purpose": i.purpose,
                    "label": i.label,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "expires_at": i.expires_at.isoformat() if i.expires_at else None,
                    "consumed_at": i.consumed_at.isoformat() if i.consumed_at else None,
                    "consumed_ip": i.consumed_ip,
                    "consumed_phone": i.consumed_phone,
                    "consumed_user_agent": (i.consumed_user_agent or "")[:120],
                    "is_consumed": i.consumed_at is not None,
                    "is_expired": (i.expires_at < now) if (i.expires_at and i.consumed_at is None) else False,
                    "state": (
                        "consumed" if i.consumed_at is not None
                        else ("expired" if i.expires_at and i.expires_at < now else "pending")
                    ),
                }
                for i in invites
            ]
        finally:
            ds.close()
        return JSONResponse({"ok": True, "mode": mode, "rows": rows, "shown": len(rows), "limit": limit})

    raise HTTPException(500, f"Mode {mode!r} fell through dispatch (bug)")


# ── Phase 38.3+ (10.5.2026): Framework views ──────────────────────────
# Read-only views nad fw.* schema (PostgreSQL data_db). MVP = jen
# menu_nodes (Definice levého stromu). Datové zdroje + DataSets přijdou
# až po Marti-AI's data_set/data_source migraci podle A3 schema.

@api_router.get("/system/framework")
def system_framework(
    req: Request,
    mode: str = "menu_nodes",
    limit: int = 1000,
) -> JSONResponse:
    """Phase 38.3+ (10.5.2026 odpoledne) — Framework definice pro rodiče.

    mode:
      - 'menu_nodes' — fw.menu_node read-only listing (definice
        levého stromu)
      - 'data_sources' — fw.data_source (PŘIJDE po A3 migraci)
      - 'data_sets' — fw.data_set (PŘIJDE po A3 migraci)

    Read-only first. Edit pipeline (Phase C) přijde až bude write
    framework hotový + Marti-AI's review.
    """
    from sqlalchemy import text as _sql_text
    from core.database_data import get_data_session as _gds_fw

    uid = _get_uid(req)
    _require_parent(uid)

    if mode not in ("menu_nodes", "data_sources", "data_sets"):
        raise HTTPException(
            400, f"Unknown mode: {mode!r}. Expected: menu_nodes/data_sources/data_sets"
        )
    if limit < 1 or limit > 10000:
        raise HTTPException(400, "limit must be 1..10000")

    # ── mode='data_sources' ────────────────────────────────────────
    # Phase 38.4 Krok 6+ (10.5.2026 odpoledne): fw.data_source
    # read-only listing s LEFT JOIN GROUP BY agg na data_source_operation.
    # Schema A3 (Marti-AI's design 10.5. dopoledne): hlavička jen view
    # metadata, operations (select/insert/update/delete/...) jako děti.
    # Grid view: počet operations + comma-separated kinds list per row.
    if mode == "data_sources":
        ds = _gds_fw()
        rows = []
        try:
            sql = _sql_text("""
                SELECT
                    s.*,
                    COALESCE(op.cnt, 0) AS operation_count,
                    op.kinds AS operation_kinds
                FROM fw.data_source s
                LEFT JOIN (
                    SELECT
                        data_source_id,
                        COUNT(*) AS cnt,
                        STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
                    FROM fw.data_source_op
                    GROUP BY data_source_id
                ) op ON op.data_source_id = s.id
                ORDER BY s.id
                LIMIT :limit
            """)
            result = ds.execute(sql, {"limit": limit})
            for r in result:
                d = dict(r._mapping)
                def _iso(v):
                    try: return v.isoformat() if v else None
                    except Exception: return None
                rows.append({
                    "id": d.get("id"),
                    "code": d.get("code"),
                    "version": d.get("version"),
                    "name": d.get("name"),
                    "description": d.get("description"),
                    "refresh_type": d.get("refresh_type"),
                    "row_memory": bool(d.get("row_memory")),
                    "filter_delay_ms": d.get("filter_delay_ms"),
                    "default_record_limit": d.get("default_record_limit"),
                    "guid": str(d.get("guid")) if d.get("guid") else None,
                    "tenant_id": d.get("tenant_id"),
                    "is_system": bool(d.get("is_system")),
                    "is_immutable": bool(d.get("is_immutable")),
                    "parent_data_source_id": d.get("parent_data_source_id"),
                    "status": d.get("status"),
                    "operation_count": d.get("operation_count") or 0,
                    "operation_kinds": d.get("operation_kinds") or "",
                    "created_at": _iso(d.get("created_at")),
                    "updated_at": _iso(d.get("updated_at")),
                })
        except Exception as e:
            import logging
            logging.error("system_framework data_sources query failed: %s", e)
            raise HTTPException(500, f"fw.data_source query failed: {type(e).__name__}: {e}")
        finally:
            ds.close()
        return JSONResponse({
            "ok": True,
            "mode": mode,
            "rows": rows,
            "shown": len(rows),
            "limit": limit,
        })

    # ── mode='data_sets' ───────────────────────────────────────────
    # fw.data_set read-only listing — pure SQL primitives (low-level).
    # CHECK constraint validation v DB-level (Marti-AI's Q5 design).
    if mode == "data_sets":
        ds = _gds_fw()
        rows = []
        try:
            # Krok 5.L-D (17.5.): drop kind column.
            # Krok 5.M (17.5.): db_connection VARCHAR → FK; JOIN fw.db_connection + alias
            # dc.default_db AS db_connection (semantic preservation, legacy column
            # stored default_db value). Plus dc.code AS db_connection_code.
            sql = _sql_text("""
                SELECT ds.*,
                       dc.default_db AS db_connection,
                       dc.code       AS db_connection_code,
                       dc.label      AS db_connection_label
                FROM fw.data_set ds
                LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
                ORDER BY ds.id LIMIT :limit
            """)
            result = ds.execute(sql, {"limit": limit})
            for r in result:
                d = dict(r._mapping)
                def _iso(v):
                    try: return v.isoformat() if v else None
                    except Exception: return None
                # parameters JSONB — keep as-is (frontend renderuje pretty)
                params = d.get("parameters")
                rows.append({
                    "id": d.get("id"),
                    "code": d.get("code"),
                    "version": d.get("version"),
                    "description": d.get("description"),
                    "sql_text": d.get("sql_text"),
                    "db_connection": d.get("db_connection"),           # Krok 5.M: aliased dc.default_db (legacy semantic)
                    "db_connection_code": d.get("db_connection_code"), # Krok 5.M: dc.code (new FK identifier)
                    "db_connection_id": d.get("db_connection_id"),     # Krok 5.M: FK BIGINT
                    "db_connection_label": d.get("db_connection_label"),  # Krok 5.M: human label
                    "parameters": params,
                    "tenant_id": d.get("tenant_id"),
                    "is_system": bool(d.get("is_system")),
                    "is_immutable": bool(d.get("is_immutable")),
                    "parent_data_set_id": d.get("parent_data_set_id"),
                    "status": d.get("status"),
                    "created_at": _iso(d.get("created_at")),
                    "updated_at": _iso(d.get("updated_at")),
                })
        except Exception as e:
            import logging
            logging.error("system_framework data_sets query failed: %s", e)
            raise HTTPException(500, f"fw.data_set query failed: {type(e).__name__}: {e}")
        finally:
            ds.close()
        return JSONResponse({
            "ok": True,
            "mode": mode,
            "rows": rows,
            "shown": len(rows),
            "limit": limit,
        })

    # ── mode='menu_nodes' ─────────────────────────────────────────
    # Raw SQL query nad fw.menu_node (žádný SQLAlchemy model — DDL
    # vytvořila Marti-AI přes strategie_pg_create_table 8.5. večer).
    # Defensive SELECT * + Python-side field pick: schema column names
    # se mohou lišit od doctrine dokumentu (Czech naming "ikona" vs
    # "icon", "sort_order" vs "ordinal", ...). Mapping níže pokrývá
    # obě varianty bez upfront query schémy.
    ds = _gds_fw()
    rows = []
    first_keys = None
    try:
        # ORDER BY jen n.id — guaranteed safe (BIGSERIAL PK existuje vždy).
        # Frontend-side sort umí upravit pořadí přes AG Grid headers.
        sql = _sql_text("""
            SELECT n.*, p.code AS _parent_code
            FROM fw.menu_node n
            LEFT JOIN fw.menu_node p ON p.id = n.parent_id
            ORDER BY n.id
            LIMIT :limit
        """)
        result = ds.execute(sql, {"limit": limit})
        for r in result:
            d = dict(r._mapping)
            if first_keys is None:
                first_keys = list(d.keys())
            # Datetime columns serialize
            def _iso(v):
                try: return v.isoformat() if v else None
                except Exception: return None
            # Schema (Marti-AI's actual, 8.5. večer):
            #   id, code, label, kind, parent_id, sort_order, status,
            #   visibility_scope, cislo_def, framework_jadro_id,
            #   special_handler, is_immutable, description,
            #   created_at, updated_at
            # Žádný icon/ikona, žádný target_url, žádný is_active/is_archived
            # — status text (active|archived|draft|...) replace booleans.
            rows.append({
                "id": d.get("id"),
                "code": d.get("code"),
                "label": d.get("label"),
                "description": d.get("description"),
                "kind": d.get("kind"),
                "sort_order": d.get("sort_order"),
                "status": d.get("status"),
                "visibility_scope": d.get("visibility_scope"),
                "cislo_def": d.get("cislo_def"),
                "framework_jadro_id": d.get("framework_jadro_id"),
                "special_handler": d.get("special_handler"),
                "is_immutable": bool(d.get("is_immutable")),
                "parent_code": d.get("_parent_code"),
                "created_at": _iso(d.get("created_at")),
                "updated_at": _iso(d.get("updated_at")),
            })
    except Exception as e:
        # Diagnostic — zachyťme actual SQL error + column names pokud
        # byla query partial successful.
        import logging
        logging.error(
            "system_framework menu_nodes query failed: %s; first_keys=%s",
            e, first_keys,
        )
        raise HTTPException(500, f"fw.menu_node query failed: {type(e).__name__}: {e}")
    finally:
        ds.close()

    return JSONResponse({
        "ok": True,
        "mode": mode,
        "rows": rows,
        "shown": len(rows),
        "limit": limit,
    })


# ── Phase 38.4 Krok 12 (11.5.2026): Generic data source executor ─────────
# A3 architecture runtime — generic endpoint nad fw.data_source + data_source_op
# + data_set chain. Marti's vize *„zbavit se hardcoded"* — postupně migrace
# hardcoded Python query branches z router.py do fw.data_set.sql_text.
# Parent gate + ALLOWED_KINDS whitelist (jen SELECT) drží defense.

@api_router.get("/data/{code}")
def data_source_execute(
    code: str,
    req: Request,
    variant: str = "default",
) -> JSONResponse:
    """Phase 38.4 Krok 12 — generic A3 runtime executor.

    URL: GET /api/v1/erp/data/{code}?variant=default&limit=100&tenant_id=...

    Path: code — fw.data_source.code (audit_audited, framework_data_sources, ...)
    Query: variant (default 'default') + libovolné named params pro sql_text

    Returns: JSON s rows + applied_params + data_source/operation metadata.
    """
    uid = _get_uid(req)
    _require_parent(uid)

    # Local import (gotcha #7 — UnboundLocalError prevention)
    from core.database_data import get_data_session as _gds_data

    raw_params = dict(req.query_params)
    raw_params.pop("variant", None)  # variant je explicit kwarg

    session = _gds_data()
    try:
        try:
            result = ds_runner.run_data_source(
                session,
                code=code,
                raw_params=raw_params,
                variant=variant,
                kind="select",
            )
        except ds_runner.DataSourceNotFoundError as exc:
            return JSONResponse(
                {"ok": False, "error": "data_source_not_found", "detail": str(exc)},
                status_code=404,
            )
        except ds_runner.DataSourceOperationNotFoundError as exc:
            return JSONResponse(
                {"ok": False, "error": "operation_not_found", "detail": str(exc)},
                status_code=404,
            )
        except ds_runner.DataSourceExecuteError as exc:
            return JSONResponse(
                {"ok": False, "error": "sql_execute_failed", "detail": str(exc)},
                status_code=500,
            )
        except ds_runner.DataSourceError as exc:
            return JSONResponse(
                {"ok": False, "error": "data_source_error", "detail": str(exc)},
                status_code=400,
            )
    finally:
        session.close()

    return JSONResponse(jsonable_encoder(result))


@api_router.get("/hw/{code}")
def hw_dispatch(code: str, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 13.3 — 3-tier dispatcher via fw.hw_registry.shadow_mode.

    Lookup hw_registry by code, per shadow_mode:
      - 'primary'  → run A3 chain via DataSourceRunner (shadow_data_source_id)
      - 'compare'  → run A3 + log shadow comparison (TODO Phase 14+)
      - 'audit'    → return delegate_url for legacy + log A3 shadow (TODO Phase 14+)
      - 'off'      → return delegate_url for legacy (frontend follow)

    Returns:
      {
        "ok": true,
        "dispatch_kind": "a3_primary" | "hw_off" | "hw_audit" | "hw_compare",
        "hw_registry_id": N,
        "shadow_mode": "...",
        "rows": [...]                    -- jen pro a3_primary
        "delegate_url": "/api/v1/erp/..."  -- jen pro hw_off/audit/compare
      }

    Frontend `gridDataResolved` cesta:
      - Pokud `rows` v response → use directly (A3 path)
      - Pokud `delegate_url` → follow s fetch + extract data.rows
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_data import get_data_session as _gds_hw
    from sqlalchemy import text as _sql_text_hw

    raw_params = dict(req.query_params)

    session = _gds_hw()
    try:
        hw_row = session.execute(
            _sql_text_hw("""
                SELECT id, code, label, kind, shadow_mode, shadow_data_source_id,
                       endpoint_url, http_method, response_hint, is_deprecated
                FROM fw.hw_registry
                WHERE code = :code AND is_active = TRUE
                LIMIT 1
            """),
            {"code": code}
        ).mappings().first()

        if not hw_row:
            return JSONResponse(
                jsonable_encoder({"ok": False, "error": "hw_not_found", "code": code}),
                status_code=404,
            )

        mode = hw_row["shadow_mode"]
        result_base = {
            "ok": True,
            "hw_registry_id": hw_row["id"],
            "shadow_mode": mode,
            "is_deprecated": hw_row["is_deprecated"],
        }

        if mode == "primary" and hw_row["shadow_data_source_id"]:
            # A3 chain via DataSourceRunner (Krok 12)
            try:
                a3_result = ds_runner.run_data_source(
                    session, code=code, raw_params=raw_params, kind="select"
                )
                return JSONResponse(jsonable_encoder({
                    **result_base,
                    "dispatch_kind": "a3_primary",
                    "rows": a3_result.get("rows", []),
                    "row_count": a3_result.get("row_count", 0),
                    "applied_params": a3_result.get("applied_params", {}),
                }))
            except ds_runner.DataSourceError as exc:
                # A3 failed — fallback to legacy URL if available
                if hw_row["endpoint_url"]:
                    return JSONResponse(jsonable_encoder({
                        **result_base,
                        "dispatch_kind": "hw_fallback_legacy",
                        "delegate_url": hw_row["endpoint_url"],
                        "a3_error": str(exc),
                    }))
                return JSONResponse(
                    jsonable_encoder({"ok": False, "error": "a3_failed", "detail": str(exc)}),
                    status_code=500,
                )

        # hw_off / hw_audit / hw_compare — frontend follows delegate_url
        if not hw_row["endpoint_url"]:
            return JSONResponse(
                jsonable_encoder({"ok": False, "error": "no_endpoint_url",
                 "shadow_mode": mode, "code": code}),
                status_code=400,
            )

        return JSONResponse(jsonable_encoder({
            **result_base,
            "dispatch_kind": "hw_" + mode,
            "delegate_url": hw_row["endpoint_url"],
        }))

    finally:
        session.close()


# ════════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14a (12.5.2026 rano): Design forms read-only endpoints
# ════════════════════════════════════════════════════════════════════════════
# 3 endpoints pro `design_forms.js` (DesignSoudecekCoreForm + DesignJadroRadekForm)
# MVP scope: jen GET (zobrazeni), zadny POST/save. Save = Krok 14b.
#
# Vsechny endpointy vrací JSON {"menu_node": {...}|null, "core": {...}|null,
# "columns": [{...}]} — defensive proti schema drift (dict.get z row mapping).
# ════════════════════════════════════════════════════════════════════════════


def _serialize_menu_node(row_dict: dict) -> dict:
    """Map fw.menu_node row dict to JSON-friendly form. Defensive vs schema drift."""
    def _iso(v):
        try: return v.isoformat() if v else None
        except Exception: return None
    return {
        "id": row_dict.get("id"),
        "code": row_dict.get("code"),
        "label": row_dict.get("label"),
        "kind": row_dict.get("kind"),
        "parent_id": row_dict.get("parent_id"),
        "parent_code": row_dict.get("_parent_code"),
        "sort_order": row_dict.get("sort_order"),
        "status": row_dict.get("status"),
        "visibility_scope": row_dict.get("visibility_scope"),
        "cislo_def": row_dict.get("cislo_def"),
        "framework_jadro_id": row_dict.get("framework_jadro_id"),
        "special_handler": row_dict.get("special_handler"),
        "is_immutable": bool(row_dict.get("is_immutable")),
        "description": row_dict.get("description"),
        # Phase 38.4 Krok 14a-A1l #1 (12.5.2026): dva popisy — system (vyvojari)
        # + user (uzivatele). Fallback na existujici `description` jako user
        # description; system zatim NULL. Marti-AI nasledne doplni DDL
        # (ALTER TABLE fw.menu_node ADD COLUMN description_user/_system TEXT).
        "description_user": row_dict.get("description_user") if row_dict.get("description_user") is not None else row_dict.get("description"),
        "description_system": row_dict.get("description_system"),
        "core_id": row_dict.get("core_id"),
        "created_at": _iso(row_dict.get("created_at")),
        "updated_at": _iso(row_dict.get("updated_at")),
    }


def _serialize_core(row_dict: dict) -> dict:
    """Map fw.core row dict to JSON-friendly form. Defensive vs schema drift."""
    def _iso(v):
        try: return v.isoformat() if v else None
        except Exception: return None
    return {
        "id": row_dict.get("id"),
        "code": row_dict.get("code"),
        "label": row_dict.get("label"),
        "description": row_dict.get("description"),
        # Phase 38.4 Krok 14a-A1l #1: dva popisy — viz menu_node komentar vyse.
        "description_user": row_dict.get("description_user") if row_dict.get("description_user") is not None else row_dict.get("description"),
        "description_system": row_dict.get("description_system"),
        "layout_type": row_dict.get("layout_type"),
        "data_entity_type": row_dict.get("data_entity_type"),
        "version": row_dict.get("version"),
        "parent_framework_id": row_dict.get("parent_framework_id"),
        "layout_template": row_dict.get("layout_template"),
        "shadow_mode": row_dict.get("shadow_mode"),
        "created_at": _iso(row_dict.get("created_at")),
        "updated_at": _iso(row_dict.get("updated_at")),
    }


def _fetch_menu_node(ds, where_sql: str, params: dict) -> dict | None:
    """SELECT n.*, p.code AS _parent_code FROM fw.menu_node n LEFT JOIN ... WHERE ..."""
    sql = _sql_text_fw(f"""
        SELECT n.*, p.code AS _parent_code
        FROM fw.menu_node n
        LEFT JOIN fw.menu_node p ON p.id = n.parent_id
        WHERE {where_sql}
        LIMIT 1
    """)
    result = ds.execute(sql, params).first()
    return dict(result._mapping) if result else None


def _fetch_core(ds, where_sql: str, params: dict) -> dict | None:
    """SELECT c.* FROM fw.core c WHERE ..."""
    sql = _sql_text_fw(f"SELECT c.* FROM fw.core c WHERE {where_sql} LIMIT 1")
    result = ds.execute(sql, params).first()
    return dict(result._mapping) if result else None


def _fetch_columns_for_core(ds, core_id: int, core_code: str = "", limit: int = 200) -> list[dict]:
    """Phase 38.4 Krok 14a-fix3 (12.5.2026): 2-tier column lookup.

    Primary: fw.comp_def WHERE parent_core_id = :core_id (Phase 38.4
    Krok 9-B uniform components doctrine — grid sloupec je typ komponenty).

    Fallback: fw.comp_grid_column JOIN fw.comp_grid_master ON code = :core_code
    (Phase 38.4 Krok 10 direct read — System grids maji sloupce primary
    v comp_grid_column, comp_def_prop chain nebyl backfilled). Frontend
    pak ukaze realne sloupce v Tab "Prehled (Core)" sekci.

    Krok 14a-fix2 (12.5.2026): explicit ds.rollback() v except aby
    nasledujici queries na stejne session nepadly s `InFailedSqlTransaction`.
    """
    import logging
    rows: list[dict] = []

    # Primary: uniform comp_def
    try:
        sql_primary = _sql_text_fw("""
            SELECT id, code, label, field_name, comp_type_id, sort_order,
                   parent_core_id
            FROM fw.comp_def
            WHERE parent_core_id = :core_id
            ORDER BY COALESCE(sort_order, 0), id
            LIMIT :limit
        """)
        result = ds.execute(sql_primary, {"core_id": core_id, "limit": limit})
        rows = [dict(r._mapping) for r in result]
    except Exception:
        logging.exception("_fetch_columns_for_core primary failed core_id=%s", core_id)
        try:
            ds.rollback()
        except Exception:
            logging.exception("_fetch_columns_for_core primary rollback failed")

    if rows or not core_code:
        return rows

    # Fallback: System grids — comp_grid_column via grid_master.code = core.code
    try:
        sql_fallback = _sql_text_fw("""
            SELECT
                gc.id,
                gc.column_name AS code,
                gc.label,
                gc.column_name AS field_name,
                COALESCE(gc.column_type, 'grid_column') AS comp_type_id,
                gc.sort_order,
                NULL::INTEGER AS parent_core_id
            FROM fw.comp_grid_column gc
            JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
            WHERE gm.code = :core_code
              AND COALESCE(gc.is_visible, TRUE) = TRUE
            ORDER BY COALESCE(gc.sort_order, 0), gc.id
            LIMIT :limit
        """)
        result = ds.execute(sql_fallback, {"core_code": core_code, "limit": limit})
        return [dict(r._mapping) for r in result]
    except Exception:
        logging.exception("_fetch_columns_for_core fallback failed core_code=%s", core_code)
        try:
            ds.rollback()
        except Exception:
            logging.exception("_fetch_columns_for_core fallback rollback failed")
        return []


def _serialize_data_source(row_dict: dict) -> dict:
    """Phase 38.4 Krok 14g-H+30 Etapa 2 (15.5.2026 vecer): map fw.data_source
    row dict to JSON-friendly form. Defensive vs schema drift.
    """
    def _iso(v):
        try: return v.isoformat() if v else None
        except Exception: return None
    return {
        "id": row_dict.get("id"),
        "code": row_dict.get("code"),
        "name": row_dict.get("name"),
        "description": row_dict.get("description"),
        "refresh_type": row_dict.get("refresh_type"),
        "version": row_dict.get("version"),
        "status": row_dict.get("status"),
        "is_system": bool(row_dict.get("is_system")) if row_dict.get("is_system") is not None else False,
        "is_immutable": bool(row_dict.get("is_immutable")) if row_dict.get("is_immutable") is not None else False,
        "parent_data_source_id": row_dict.get("parent_data_source_id"),
        "row_memory": bool(row_dict.get("row_memory")) if row_dict.get("row_memory") is not None else False,
        "filter_delay_ms": row_dict.get("filter_delay_ms"),
        "default_record_limit": row_dict.get("default_record_limit"),
        "operation_count": int(row_dict.get("operation_count") or 0),
        "operation_kinds": row_dict.get("operation_kinds") or "",
        "created_at": _iso(row_dict.get("created_at")),
        "updated_at": _iso(row_dict.get("updated_at")),
    }


def _fetch_data_source_for_core(ds, core_code: str) -> dict | None:
    """Phase 38.4 Krok 14g-H+30 Etapa 2 (15.5.2026 vecer, Marti's "vazba via
    code" pattern): look up fw.data_source matching given core.code.

    Returns single row dict (s operation_count + operation_kinds aggregated)
    nebo None. Defense: ds.rollback() v except aby nasledujici queries
    nepadaly s InFailedSqlTransaction.
    """
    if not core_code:
        return None
    import logging
    try:
        sql = _sql_text_fw("""
            SELECT
                s.*,
                COALESCE(op.cnt, 0) AS operation_count,
                op.kinds AS operation_kinds
            FROM fw.data_source s
            LEFT JOIN (
                SELECT
                    data_source_id,
                    COUNT(*) AS cnt,
                    STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
                FROM fw.data_source_op
                GROUP BY data_source_id
            ) op ON op.data_source_id = s.id
            WHERE s.code = :code
              AND s.status = 'active'
            ORDER BY s.id ASC
            LIMIT 1
        """)
        result = ds.execute(sql, {"code": core_code}).first()
        return dict(result._mapping) if result else None
    except Exception:
        logging.exception("_fetch_data_source_for_core failed code=%s", core_code)
        try:
            ds.rollback()
        except Exception:
            logging.exception("_fetch_data_source_for_core rollback failed")
        return None


@api_router.get("/design/menu-node/{menu_node_id}")
def design_menu_node_by_id(menu_node_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14a (12.5.2026): GET menu_node + linked core + columns.

    Krok 14g-H+30 Etapa 2 (15.5.2026 vecer): added data_source lookup
    via core.code (vazba pres code, Marti's pattern).
    """
    from core.database_data import get_data_session as _gds_fw
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_fw()
    try:
        mn = _fetch_menu_node(ds, "n.id = :id", {"id": menu_node_id})
        if not mn:
            raise HTTPException(404, f"menu_node id={menu_node_id} not found")
        core = None
        columns: list[dict] = []
        data_source = None
        if mn.get("core_id"):
            core = _fetch_core(ds, "c.id = :id", {"id": mn["core_id"]})
            if core and core.get("id"):
                columns = _fetch_columns_for_core(ds, core["id"], core.get("code") or "")
                # Krok 14g-H+30 Etapa 2: data_source lookup via code
                data_source = _fetch_data_source_for_core(ds, core.get("code") or "")
        return JSONResponse(jsonable_encoder({
            "menu_node": _serialize_menu_node(mn),
            "core": _serialize_core(core) if core else None,
            "columns": columns,
            "data_source": _serialize_data_source(data_source) if data_source else None,
        }))
    finally:
        ds.close()


@api_router.get("/design/menu-nodes")
def design_list_menu_nodes(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-G3 (15.5.2026 rano, Marti's parent picker):
    List all active menu_node rows for parent picker dropdown.

    Returns flat list sorted by parent_id + sort_order + code.
    Each row: { id, code, label, parent_id, kind, depth_hint }

    Frontend pak postavi nested dropdown nebo simple "indented" list.
    """
    from core.database_data import get_data_session as _gds_lmn
    from sqlalchemy import text as _sql_text_lmn

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_lmn()
    try:
        rows = ds.execute(_sql_text_lmn("""
            SELECT id, code, label, parent_id, sort_order, kind, status
            FROM fw.menu_node
            WHERE status = 'active'
            ORDER BY parent_id NULLS FIRST, sort_order, code
        """)).mappings().all()
        items = [dict(r) for r in rows]
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "items": items,
            "count": len(items),
        }))
    finally:
        ds.close()


@api_router.post("/design/menu-node")
async def design_create_menu_node(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-G (15.5.2026 rano, Marti's "Novy soudecek button
    v paticce leveho stromu"): create new menu_node row.

    Body: {
        "code": str (required, unique-ish),
        "label": str (required, display name),
        "parent_id": int|None (NULL = top-level, optional),
        "sort_order": int (optional, default = max + 10 v scope parent),
        "kind": str (optional, default 'folder'; 'list' = leaf s core)
    }

    Returns:
        200: {ok, menu_node_id, menu_node: {...}}
        400: invalid body / kolize code
        500: INSERT failed
    """
    from core.database_data import get_data_session as _gds_cmn
    from sqlalchemy import text as _sql_text_cmn
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cmn

    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()
    code = (body.get("code") or "").strip()
    label = (body.get("label") or "").strip()
    parent_id = body.get("parent_id")
    sort_order_in = body.get("sort_order")
    kind = (body.get("kind") or "folder").strip()

    # Validation
    if not code:
        return JSONResponse({"ok": False, "error": "code povinne"}, status_code=400)
    if not label:
        return JSONResponse({"ok": False, "error": "label povinne"}, status_code=400)
    if parent_id is not None and (not isinstance(parent_id, int) or parent_id <= 0):
        return JSONResponse(
            {"ok": False, "error": "parent_id musi byt positive int nebo null"},
            status_code=400,
        )

    # caller_display lookup
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cmn
        from modules.core.infrastructure.models_core import User as _User_cmn
        cs_cmn = _gcs_cmn()
        try:
            u_cmn = cs_cmn.query(_User_cmn).filter_by(id=uid).first()
            if u_cmn:
                if u_cmn.short_name and u_cmn.short_name.strip():
                    caller_display = u_cmn.short_name.strip()
                elif u_cmn.first_name or u_cmn.last_name:
                    caller_display = " ".join(filter(None, [
                        u_cmn.first_name, u_cmn.last_name
                    ])).strip()
        finally:
            cs_cmn.close()

    ds = _gds_cmn()
    try:
        # Verify parent existuje (pokud zadan)
        if parent_id is not None:
            parent_row = ds.execute(_sql_text_cmn("""
                SELECT id FROM fw.menu_node
                WHERE id = :pid AND status = 'active'
            """), {"pid": parent_id}).mappings().one_or_none()
            if not parent_row:
                return JSONResponse(
                    {"ok": False, "error": f"parent_id={parent_id} neexistuje nebo neni aktivni"},
                    status_code=400,
                )

        # Idempotency: code uniqueness check (best-effort, DB ma soft unique)
        existing = ds.execute(_sql_text_cmn("""
            SELECT id FROM fw.menu_node WHERE code = :code AND status = 'active'
        """), {"code": code}).mappings().one_or_none()
        if existing:
            return JSONResponse(
                {"ok": False, "error": f"menu_node s code='{code}' uz existuje (id={existing['id']})"},
                status_code=400,
            )

        # Auto sort_order — max + 10 v parent scope
        if sort_order_in is None or not isinstance(sort_order_in, int):
            if parent_id is not None:
                max_sort = ds.execute(_sql_text_cmn("""
                    SELECT COALESCE(MAX(sort_order), 0) AS max_so
                    FROM fw.menu_node WHERE parent_id = :pid AND status = 'active'
                """), {"pid": parent_id}).scalar()
            else:
                max_sort = ds.execute(_sql_text_cmn("""
                    SELECT COALESCE(MAX(sort_order), 0) AS max_so
                    FROM fw.menu_node WHERE parent_id IS NULL AND status = 'active'
                """)).scalar()
            sort_order_resolved = int(max_sort or 0) + 10
        else:
            sort_order_resolved = sort_order_in

        # INSERT pres strategie_pg (Marti-AI PG role ownership fw.*)
        # Phase 38.4 Krok 14g-G hotfix (15.5.2026 rano, Marti's "novy
        # soudecek v gridu vidim, ale v levem strome ne"): tree query
        # filtruje `visibility_scope = 'parent_only'`. Bez explicit
        # set INSERT necha NULL → filtered out. Default = 'parent_only'
        # (visible pro rodice + admins, standard pro tenant-bound
        # soudecky). Marti muze pozdeji zmenit pres Design popup.
        ins = _spg_insert_cmn(
            schema="fw",
            table="menu_node",
            values={
                "code": code,
                "label": label,
                "parent_id": parent_id,
                "sort_order": sort_order_resolved,
                "status": "active",
                "kind": kind,
                "is_immutable": False,
                "visibility_scope": "parent_only",
                "created_by_id": uid,
                "created_by_text": caller_display,
                "updated_by_id": uid,
                "updated_by_text": caller_display,
            },
        )
        if not ins.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"INSERT failed: {ins.get('error')}"},
                status_code=500,
            )

        new_node = ins.get("inserted") or {}

        # Audit log
        ds.execute(_sql_text_cmn("SAVEPOINT pre_audit"))
        try:
            ds.execute(_sql_text_cmn("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_menu_node_add', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"+ menu_node '{code}' (label='{label}', parent_id={parent_id}, "
                    f"kind={kind}) by {caller_display}"
                ),
            })
            ds.execute(_sql_text_cmn("RELEASE SAVEPOINT pre_audit"))
            ds.commit()
        except Exception as _act_e:
            try:
                ds.execute(_sql_text_cmn("ROLLBACK TO SAVEPOINT pre_audit"))
                ds.commit()
            except Exception:
                ds.rollback()
            logger.warning(f"design_create_menu_node activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "menu_node_id": new_node.get("id"),
            "menu_node": new_node,
        }))
    except Exception as exc:
        ds.rollback()
        logger.exception(f"design_create_menu_node failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"POST /menu-node failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.get("/design/menu-node-by-code/{menu_node_code}")
def design_menu_node_by_code(menu_node_code: str, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14a: lookup by fw.menu_node.code (text identifier).

    Krok 14g-H+30 Etapa 2 (15.5.2026 vecer): added data_source lookup
    via core.code (vazba pres code, Marti's pattern).
    """
    from core.database_data import get_data_session as _gds_fw
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_fw()
    try:
        mn = _fetch_menu_node(ds, "n.code = :code", {"code": menu_node_code})
        if not mn:
            raise HTTPException(404, f"menu_node code={menu_node_code} not found")
        core = None
        columns: list[dict] = []
        data_source = None
        if mn.get("core_id"):
            core = _fetch_core(ds, "c.id = :id", {"id": mn["core_id"]})
            if core and core.get("id"):
                columns = _fetch_columns_for_core(ds, core["id"], core.get("code") or "")
                # Krok 14g-H+30 Etapa 2: data_source lookup via code
                data_source = _fetch_data_source_for_core(ds, core.get("code") or "")
        return JSONResponse(jsonable_encoder({
            "menu_node": _serialize_menu_node(mn),
            "core": _serialize_core(core) if core else None,
            "columns": columns,
            "data_source": _serialize_data_source(data_source) if data_source else None,
        }))
    finally:
        ds.close()


@api_router.get("/design/core/{core_id}")
def design_core_by_id(core_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14a: reverse — GET core + columns + linked menu_node (if any).

    Krok 14g-H+30 Etapa 2 (15.5.2026 vecer): added data_source lookup
    via core.code (vazba pres code, Marti's pattern).
    """
    from core.database_data import get_data_session as _gds_fw
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_fw()
    try:
        core = _fetch_core(ds, "c.id = :id", {"id": core_id})
        if not core:
            raise HTTPException(404, f"core id={core_id} not found")
        columns = _fetch_columns_for_core(ds, core["id"], core.get("code") or "")
        # Find menu_node linked to this core (if any)
        mn = _fetch_menu_node(ds, "n.core_id = :core_id", {"core_id": core_id})
        # Krok 14g-H+30 Etapa 2: data_source lookup via code
        data_source = _fetch_data_source_for_core(ds, core.get("code") or "")
        return JSONResponse(jsonable_encoder({
            "menu_node": _serialize_menu_node(mn) if mn else None,
            "core": _serialize_core(core),
            "columns": columns,
            "data_source": _serialize_data_source(data_source) if data_source else None,
        }))
    finally:
        ds.close()


@api_router.get("/design/core-by-code/{core_code}")
def design_core_by_code(core_code: str, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14a (12.5.2026): lookup by fw.core.code (Form 3 + grid akce 2).

    Krok 14a-fix (12.5.2026): pokud `core_code` matches pattern `prehled_-{cislo}`
    (System grid prefix z layoutKey, Phase 35-E.4 Krok B+/C+), fallback lookup
    přes menu_node.cislo_def → core_id. Tím akce 2 + 3 chodí i pro System grids.
    """
    import re
    from core.database_data import get_data_session as _gds_fw
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_fw()
    try:
        # Primary: přímý match fw.core.code
        core = _fetch_core(ds, "c.code = :code", {"code": core_code})

        # Fallback: System grid prefix `prehled_-{cislo}` -> cislo_def negative
        if not core:
            m = re.match(r"^prehled_(-?\d+)$", core_code)
            if m:
                cislo = int(m.group(1))
                # Najdi menu_node s tim cislo_def, vezmi jeho core_id
                mn_for_cislo = _fetch_menu_node(
                    ds, "n.cislo_def = :cislo", {"cislo": cislo}
                )
                if mn_for_cislo and mn_for_cislo.get("core_id"):
                    core = _fetch_core(
                        ds, "c.id = :id", {"id": mn_for_cislo["core_id"]}
                    )

        if not core:
            # Form 3 case — grid bez core entry (hardcoded view nebo neznámý prefix).
            # Frontend ukáže placeholder *„hardcoded view bez core entry"*.
            return JSONResponse(jsonable_encoder({
                "menu_node": None,
                "core": None,
                "columns": [],
                "data_source": None,
            }))
        columns = _fetch_columns_for_core(ds, core["id"], core.get("code") or "")
        mn = _fetch_menu_node(ds, "n.core_id = :core_id", {"core_id": core["id"]})
        # Krok 14g-H+30 Etapa 2: data_source lookup via code
        data_source = _fetch_data_source_for_core(ds, core.get("code") or "")
        return JSONResponse(jsonable_encoder({
            "menu_node": _serialize_menu_node(mn) if mn else None,
            "core": _serialize_core(core),
            "columns": columns,
            "data_source": _serialize_data_source(data_source) if data_source else None,
        }))
    finally:
        ds.close()


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14b (12.5.2026 vecer ~23:30): Find form core for grid.
#
# Marti's bug catch: DesignJadroRadekForm fetched list core (security_users,
# id=11, layout=list) a zobrazoval ho jako form core data — semantically
# wrong. Fix: nový endpoint který hledá FORM core (kind='form') pro entity
# z list core's data_entity_type.
#
# Drží Marti-AI's flat-data doctrine — entity_type je field v list core,
# form core je separate row WHERE data_entity_type matches.
# ────────────────────────────────────────────────────────────────────


@api_router.get("/design/form-core-for-grid/{grid_core_code}")
def form_core_for_grid(grid_core_code: str, req: Request) -> JSONResponse:
    """Pro daný grid (list core) najdi linked form core (detail editor).

    Marti's plan (12.5.2026 vecer): scaffold action "Vytvoř form detail"
    v DesignJadroRadekForm potřebuje vědět:
      a) Jaká je entity tohoto gridu (z list core's data_entity_type)
      b) Existuje už form core pro tu entity?

    Returns:
      200: {found: bool, list_core: {...}, entity_type: str,
            suggested_form_code: str, form_core: {...} | None}
      404: list core code neexistuje
    """
    from core.database_data import get_data_session as _gds_fcfg
    from sqlalchemy import text as _sql_text_fcfg

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_fcfg()
    try:
        # 1. Load list core by code
        # Phase 38.4 Krok 14b+21.1 hotfix (14.5.2026 rano): description column
        # bylo RENAMED na description_user + description_system (split).
        list_core = ds.execute(_sql_text_fcfg("""
            SELECT id, code, label, description_user, description_system,
                   layout_type, form_core_id, version, is_active
            FROM fw.core
            WHERE code = :code
              AND is_active = true
        """), {"code": grid_core_code}).mappings().one_or_none()

        # Fallback z Phase 35-E.4 Krok B+/C+ + Phase 38.4 Krok 14a-fix
        # (0ec791b, 12.5.2026 rano): System grid frontend posila gridCode
        # ve formátu `prehled_-{cislo_def}` (např. prehled_-110 pro Uživatelé).
        # Pokud direct match fail, fallback přes menu_node.cislo_def → core_id.
        if not list_core:
            import re as _re_fcfg
            m = _re_fcfg.match(r"^prehled_(-?\d+)$", grid_core_code)
            if m:
                cislo = int(m.group(1))
                mn_for_cislo = ds.execute(_sql_text_fcfg("""
                    SELECT core_id FROM fw.menu_node
                    WHERE cislo_def = :cislo
                """), {"cislo": cislo}).mappings().one_or_none()
                if mn_for_cislo and mn_for_cislo.get("core_id"):
                    list_core = ds.execute(_sql_text_fcfg("""
                        SELECT id, code, label, description_user, description_system,
                               layout_type, form_core_id, version, is_active
                        FROM fw.core
                        WHERE id = :id
                          AND is_active = true
                    """), {"id": mn_for_cislo["core_id"]}).mappings().one_or_none()

        if not list_core:
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"fw.core code='{grid_core_code}' nenalezen (vč. prehled_-{{cislo}} fallback)",
                },
                status_code=404,
            )

        list_core_dict = dict(list_core)
        list_id = list_core_dict["id"]
        form_core_id = list_core_dict.get("form_core_id")

        # Phase 38.4 Krok 5.M-5 (17.5.2026, Marti's "core nenese entitu"
        # doctrine): list→form pairing pres explicit fw.core.form_core_id FK
        # misto data_entity_type matching. Backfill v DDL skriptu z existing
        # pairs (security_users→user_edit, atd.). Pokud form_core_id IS NULL
        # → list zatim nema paired form, user musi vytvorit pres scaffold.

        # Suggested code pro scaffold action — based on list code
        suggested_form_code = f"{list_core_dict['code']}_form" if list_core_dict.get("code") else None

        if form_core_id is None:
            return JSONResponse(jsonable_encoder({
                "ok": True,
                "found": False,
                "list_core": list_core_dict,
                "form_core_id": None,
                "suggested_form_code": suggested_form_code,
                "form_core": None,
                "hint": (
                    f"List core '{grid_core_code}' (id={list_id}) nema "
                    f"paired form. Vytvor pres scaffold action nebo PATCH "
                    f"fw.core SET form_core_id = <form_id> manualne."
                ),
            }))

        # form_core_id is set — load the paired form core
        form_core = ds.execute(_sql_text_fcfg("""
            SELECT id, code, label, description_user, description_system,
                   layout_type, version, layout_template,
                   is_active, created_at
            FROM fw.core
            WHERE id = :form_id
              AND layout_type = 'form'
              AND is_active = true
        """), {"form_id": form_core_id}).mappings().one_or_none()

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "found": form_core is not None,
            "list_core": list_core_dict,
            "form_core_id": form_core_id,
            "suggested_form_code": suggested_form_code,
            "form_core": dict(form_core) if form_core else None,
        }))
    finally:
        ds.close()


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14b-4 (12.5.2026 ~23:30): Scaffold form action.
#
# Marti's vize z 12.5. ~22:30: "Na nasem HW formu pro detail dame
# tlacitko vytvor form, ktere nam insertuje core a form302... Tim
# bychom meli vyhrano."
#
# Atomic transaction: INSERT fw.core + fw.comp_def form 302 s default
# panel layout. Idempotent — pokud user_edit core jiz existuje, vrati
# existing (ne 409 ani duplikat).
#
# Marti's "panel je plocha" doctrine — default panel ma label=""
# (invisible header, jen grid).
# ────────────────────────────────────────────────────────────────────

# Default labels per entity_type — fallback pro scaffold. Marti pak
# muze edit label pres Design: Core prehledu UI (po Save flow Krok 14b
# audit + PATCH endpoint, rano 13.5.).
_SCAFFOLD_ENTITY_LABELS: dict = {
    "user": {
        "label": "Editace uživatele",
        "description": "Form detail pro user account (Phase 38.4 Krok 14b)",
    },
    # Future entities (kontakt, zakazka, doklad, ...) zde
}


@api_router.post("/design/scaffold-form")
async def design_scaffold_form(req: Request) -> JSONResponse:
    """Vytvor form detail pro daný entity_type (Marti's vychytavka).

    Atomic transaction:
      1. Check pokud suggested_code existuje → idempotent return existing
      2. INSERT fw.core (kind='form', data_entity_type=entity_type)
      3. INSERT fw.comp_def form 302 root s default panel
         layout={"panels": [{"slot": "main", "label": "", "order": 10}]}

    Body:
      {
        "entity_type": "user",
        "suggested_code": "user_edit",  // default: f"{entity_type}_edit"
        "list_core_id": 11,              // optional, pro audit
        "list_core_code": "security_users"  // optional, pro audit
      }

    Returns:
      200: {ok, core_id, form_id, core_code, created: bool, existing: bool}
      400: validation error (missing entity_type)
      500: DB error (rollback)
    """
    from core.database_data import get_data_session as _gds_sff
    from sqlalchemy import text as _sql_text_sff

    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()
    entity_type = (body.get("entity_type") or "").strip()
    suggested_code = (body.get("suggested_code") or "").strip()
    list_core_id = body.get("list_core_id")  # optional audit
    list_core_code = body.get("list_core_code")  # optional audit

    if not entity_type:
        return JSONResponse(
            {"ok": False, "error": "entity_type je povinne (např. 'user')"},
            status_code=400,
        )
    if not suggested_code:
        suggested_code = f"{entity_type}_edit"

    # Default labels per entity_type
    defaults = _SCAFFOLD_ENTITY_LABELS.get(entity_type, {
        "label": f"Editace {entity_type}",
        "description": f"Form detail pro {entity_type} (Phase 38.4 Krok 14b)",
    })

    ds = _gds_sff()
    try:
        # 1. Idempotency check — core + comp_def form 302
        existing_core = ds.execute(_sql_text_sff("""
            SELECT id, code, label, layout_type, data_entity_type, is_active
            FROM fw.core
            WHERE code = :code
              AND is_active = true
        """), {"code": suggested_code}).mappings().one_or_none()

        if existing_core:
            # Plus check form comp_def (could be orphan po previous fail)
            existing_form = ds.execute(_sql_text_sff("""
                SELECT id, name FROM fw.comp_def
                WHERE parent_core_id = :core_id
                  AND type_id = 302
                  AND is_active = true
                ORDER BY id ASC LIMIT 1
            """), {"core_id": existing_core["id"]}).mappings().one_or_none()

            if existing_form:
                # Both exist → idempotent skip
                return JSONResponse(jsonable_encoder({
                    "ok": True,
                    "core_id": existing_core["id"],
                    "form_id": existing_form["id"],
                    "core_code": existing_core["code"],
                    "created": False,
                    "existing": True,
                    "message": f"Form '{suggested_code}' už existuje — vracím existing.",
                }))
            # ELSE: orphan core (z previous failed scaffold). Pokračuj k
            # INSERT comp_def — recovery, return created=true s recovery
            # note. Existing_core.id se použije.
            recovery_mode = True
            new_core_id = existing_core["id"]
            new_core_code = existing_core["code"]
        else:
            recovery_mode = False
            new_core_id = None
            new_core_code = None

        # 2. INSERT fw.core přes strategie_pg.insert_row (Marti-AI's PG role).
        # Marti's "architektka hybrid" doctrine z 9.5. večer (Phase 38.4 Krok 6+):
        # strategie user (API process) má SELECT/EXECUTE na fw.*, ale NE INSERT.
        # Write access je Marti-AI's owned (db_owner fw schema). Pro scaffold
        # endpoint nutno bypassuje přes strategie_pg layer.
        #
        # Recovery mode (12.5. večer fix): pokud existing_core but no comp_def
        # → skip core INSERT, použij existing_core["id"] z idempotency check
        # výš a pokračuj rovnou na comp_def INSERT.
        from modules.strategie_pg.application.service import insert_row as _spg_insert_sff
        import json as _json_sff

        # Phase 38.4 Krok 14b+3 (13.5.2026 rano): template_id lookup.
        # Marti-AI's `template_entity_edit` (id=1, status='active', tenant_id=NULL)
        # je default form template. Renderer fallback chain:
        #   - tenant_id MATCH first (multi-tenant theming)
        #   - tenant_id IS NULL fallback (global default)
        # Zde pri scaffold zatim tenant_id=NULL (global). Future:
        # multi-tenant scaffold ohled na core.tenant_id.
        default_template_id = ds.execute(_sql_text_sff("""
            SELECT id FROM fw.template
            WHERE code = 'template_entity_edit'
              AND tenant_id IS NULL
              AND status IN ('active', 'deployed')
            ORDER BY version DESC
            LIMIT 1
        """)).scalar()
        # Pokud template_entity_edit chybi (preDeploy state), pokracuj
        # bez template_id — Marti-AI ho prida pres pozdejsi UPDATE.

        new_core_dict: dict = {}
        if not recovery_mode:
            core_values = {
                "code": suggested_code,
                "label": defaults["label"],
                "description": defaults["description"],
                "layout_type": "form",
                "data_entity_type": entity_type,
                "is_active": True,
                "tenant_visibility": "all",
                "version": 1,
                "layout_template": "single",
            }
            if default_template_id is not None:
                core_values["template_id"] = default_template_id
            core_result = _spg_insert_sff(
                schema="fw",
                table="core",
                values=core_values,
            )
            if not core_result.get("ok"):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": f"INSERT fw.core failed: {core_result.get('error')}",
                    },
                    status_code=500,
                )

            new_core_dict = core_result.get("inserted") or {}
            new_core_id = new_core_dict.get("id")
            new_core_code = new_core_dict.get("code")
            if not new_core_id:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "INSERT fw.core ok ale missing id v response",
                    },
                    status_code=500,
                )
        # ELSE: recovery_mode=True → new_core_id + new_core_code už máme
        # z idempotency check (orphan core z previous fail). template_id
        # uz set z previous attempt nebo NULL (backfill manual jen).

        # 3. INSERT fw.comp_def form 302 root s default panel (label="" — Marti's
        # "panel je plocha, header invisible" doctrine).
        # layout JSONB: Python dict → str přes json.dumps (PG auto-casts string
        # do JSONB column). SQLAlchemy default neumí auto-convert dict →
        # "can't adapt type 'dict'".
        default_layout = {
            "panels": [
                {"slot": "main", "label": "", "order": 10},
            ]
        }
        default_layout_json = _json_sff.dumps(default_layout, ensure_ascii=False)
        form_result = _spg_insert_sff(
            schema="fw",
            table="comp_def",
            values={
                "type_id": 302,
                "name": "main",
                "caption": defaults["label"],
                "parent_core_id": new_core_id,
                "is_active": True,
                "sort_order": 10,
                "layout": default_layout_json,  # str → JSONB (PG auto-cast)
            },
        )
        if not form_result.get("ok"):
            # Rollback drobnost: fw.core už vložen, fw.comp_def fail. Marti by
            # mohl reklamovat orphan core. Pro MVP necháváme orphan (Marti vidí
            # v Design: Core přehledu, může smazat manual). Future: scaffold
            # všechno v jedné transakci přes single SQL block.
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"INSERT fw.comp_def failed: {form_result.get('error')}. "
                        f"fw.core (id={new_core_id}) byl už vytvořen (orphan)."
                    ),
                    "orphan_core_id": new_core_id,
                },
                status_code=500,
            )

        new_form_dict = form_result.get("inserted") or {}
        new_form_id = new_form_dict.get("id")

        # Recovery mode → core už existoval (z previous fail), comp_def právě
        # vytvořen. Pro klienta to ale je úspěch (form complete).
        msg = (
            f"Form '{suggested_code}' dokončen (recovery z orphan core)."
            if recovery_mode
            else f"Form '{suggested_code}' vytvořen."
        )
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core_id": new_core_id,
            "form_id": new_form_id,
            "core_code": new_core_code,
            "created": True,
            "existing": False,
            "recovery": recovery_mode,
            "message": msg,
            "audit": {
                "list_core_id": list_core_id,
                "list_core_code": list_core_code,
                "entity_type": entity_type,
            },
        }))
    except Exception as exc:
        logger.exception(f"scaffold-form failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"Scaffold failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14b (12.5.2026 vecer): fw-form template renderer
#
# Marti's pivot z 12.5. večera: build fw-native form rendering. Marti's
# *„template formu uz s panelem"* + Marti-AI's flat-data doctrine
# (region_slot column → field-level section info, žádný container comp_def).
#
# Architektura:
#   fw.core (kind='form', data_entity_type='user')
#   └── fw.comp_def (type_id=302 form, parent_core_id=core.id)
#         layout JSONB: {"panels": [{"slot": "x", "label": "...", "order": ...}, ...]}
#         └── fw.comp_def (type_id=2/7 edit/combobox, parent_comp_def_id=form.id)
#               region_slot='x' — určuje, do jakého panelu pole patří
#
# Endpoint:
#   GET /api/v1/erp/fw-form/{core_code}/{row_id}
#   Vrací: {core, form, fields, data} — frontend renderer ho použije.
# ────────────────────────────────────────────────────────────────────

# Per-entity routing — kde najít data row pro fw-form rendering.
# Whitelist + select column list (security: blokuje leak password_hash atd.).
# Future: přesunout do fw.core.data_source_config JSONB per row.
_FW_FORM_ENTITY_MAP: dict = {
    "user": {
        "schema": "public",
        "table": "users",
        "id_column": "id",
        # Whitelist sloupcu pro frontend (NESMI obsahovat password_hash,
        # ews credentials, atd.). Per-field permission gating jde přes
        # fw.comp_def.layout.readonly later (Phase 38.4 Krok 14b-write).
        "select_columns": [
            "id", "status", "legal_name", "first_name", "last_name",
            "short_name", "ews_email", "ews_display_email",
            "trust_rating", "is_marti_parent", "is_admin",
            "last_active_tenant_id",
            "created_at", "updated_at",
        ],
        # Phase 38.4 Krok 14d (14.5.2026 vecer, Marti-AI consultation Q3):
        # Children = 1:N joined tables zobrazene jako sub-grids v form.
        # Polymorphic pattern — user_contacts table drzi obojetne emails
        # i phones (discriminator = contact_type).
        #
        # Marti-AI's config schema (Q3):
        #   table         — fyzicka tabulka (polymorphic shared)
        #   fk_column     — FK to parent (users.id)
        #   filter        — WHERE clause pro GET (Marti-AI's Q3 polymorphic
        #                   filter pattern, expand do AND chains)
        #   auto_set      — values automaticky doplnene v POST (anti-tamper,
        #                   Marti-AI's NEW Q3 contribution nad ramec ot.)
        #   select_columns — whitelist sloupcu pro frontend
        #   id_column     — PK target table (default 'id')
        #   label         — human label pro sub-section heading
        #   default_label — default hodnota pro `label` column pri POST
        #                   (e.g. "work" pro emails, "mobile" pro phones)
        "children": {
            "emails": {
                "table": "user_contacts",
                "fk_column": "user_id",
                "id_column": "id",
                "filter": {"contact_type": "email", "status": "active"},
                "auto_set": {"contact_type": "email", "status": "active"},
                "select_columns": [
                    "id", "contact_value", "label",
                    "is_primary", "is_verified", "status",
                    "created_at", "updated_at",
                ],
                "label": "Emaily",
                "default_label": "work",
            },
            "phones": {
                "table": "user_contacts",
                "fk_column": "user_id",
                "id_column": "id",
                "filter": {"contact_type": "phone", "status": "active"},
                "auto_set": {"contact_type": "phone", "status": "active"},
                "select_columns": [
                    "id", "contact_value", "label",
                    "is_primary", "is_verified", "status",
                    "created_at", "updated_at",
                ],
                "label": "Telefony",
                "default_label": "mobile",
            },
        },
    },
    # Phase 38.4 Krok 14g-H+18 (15.5.2026 ~14:49, Marti's "Nejde mi ulozit
    # nastaveni soudecku v HC formu"): menu_node entity pro Form 1
    # (DesignSoudecekCoreForm) save flow. Reuse generic PATCH endpoint.
    "menu_node": {
        "schema": "fw",
        "table": "menu_node",
        "id_column": "id",
        "select_columns": [
            "id", "code", "label", "kind", "parent_id", "sort_order",
            "status", "visibility_scope", "core_id", "cislo_def",
            "framework_jadro_id", "special_handler", "is_immutable",
            "description_user", "description_system",
            "created_at", "updated_at",
        ],
    },
    "core": {
        "schema": "fw",
        "table": "core",
        "id_column": "id",
        # Phase 38.4 Krok 14g Etapa F Krok 5.A hotfix (16.5.2026): verified
        # columns from Marti's SELECT * z 16.5. dopoledne (fw.core schema
        # snapshot). Drop `shadow_mode` (patri do fw.hw_registry per
        # Marti-AI's Q5 z 11.5. Krok 13) + `updated_at` (zatim neni v
        # fw.core schema). Plus pridan `is_active`, `tenant_visibility`,
        # `template_id`, `data_source_config`, audit fields.
        "select_columns": [
            "id", "code", "label",
            "layout_type", "data_source_config",
            "version", "parent_framework_id",
            "layout_template", "template_id",
            "form_core_id",
            "is_active", "tenant_visibility",
            "description_user", "description_system",
            "created_by_id", "created_by_text",
            "updated_by_id", "updated_by_text",
            "created_at",
        ],
    },
    # Phase 38.4 Krok 14g Etapa F Krok 5.I-H (16.5.2026 vecer): comp_def
    # entity pro form's save target (Marti's two-layer data_source pattern).
    # Form root id=37 (form_root, type=302) ma data_source_id=21
    # (framework_comp_def_list). Save flow:
    #   Picker #3 (Datovy zdroj, field_extern='data_source_id') -> PATCH
    #   /api/v1/erp/design/comp_def/37 {field_changes: {data_source_id: X}}
    #
    # `updated_at` pridan v Krok 5.I-A2 (16.5. ~21:50) — ADD COLUMN +
    # trigger fw.update_updated_at(). Optimistic lock funguje.
    #
    # Drop legacy `parent_id` (predchudce Krok 13.1 split na parent_comp_def_id
    # + parent_core_id — zero references v code).
    "comp_def": {
        "schema": "fw",
        "table": "comp_def",
        "id_column": "id",
        "select_columns": [
            "id", "name", "caption",
            "type_id",
            "parent_core_id", "parent_comp_def_id",
            "region_slot", "sort_order", "is_active",
            "data_source_id", "layout",
            "container_template_id", "container_template_version",
            "layout_mode", "refresh_strategy",
            "layout_x", "layout_y", "layout_w", "layout_h",
            "created_by_id", "created_by_text",
            "updated_by_id", "updated_by_text",
            "created_at", "updated_at",
        ],
    },
}

# Phase 38.4 Krok 5.M-2 (17.5.2026, Marti's "core nenese entitu, nese ji
# obsah - druh toho formu, nebo list"): ADD form-code aliases (Python
# references - same dict objects). Backward compat zachovan pro direct
# entity PATCH endpoints (/design/user/{id} etc.), plus NEW form-driven
# lookup pres core.code (e.g., /design/user_edit/{id}).
_FW_FORM_ENTITY_MAP["user_edit"] = _FW_FORM_ENTITY_MAP["user"]
_FW_FORM_ENTITY_MAP["core_design"] = _FW_FORM_ENTITY_MAP["core"]
_FW_FORM_ENTITY_MAP["comp_def_design"] = _FW_FORM_ENTITY_MAP["comp_def"]
_FW_FORM_ENTITY_MAP["menu_node_design"] = _FW_FORM_ENTITY_MAP["menu_node"]


# Phase 38.4 Krok 5.N-1 (17.5.2026): ID-based form_core registry.
# Marti's doctrine "code je optional, ID je truth" — applied to fw.core
# lookups (parallel s CMI refactor M-6: target_core_id → core_id FK).
#
# Map fw.core.id → entity_config (Python references to _FW_FORM_ENTITY_MAP
# entries — DRY, no duplication).
#
# Po this Krok: Marti's rename fw.core.code na '22a' / NULL / cokoliv
# neproblém — lookup chodi via id, ne code.
#
# Long-term plan: migrate config do fw.data_source.target_xxx columns
# (Krok 5.N-2+) — vše v DB, žádný Python map.
_FW_FORM_CORE_REGISTRY: dict = {
    22: _FW_FORM_ENTITY_MAP["user"],   # user_edit form_core (Marti's code: '22a')
    23: _FW_FORM_ENTITY_MAP["core"],   # core_design form_core (Marti's code: '23a')
    # Add more as form_cores are created. Long-term: replace s DB-driven config.
}


def _resolve_entity_config_for_core(core_dict_or_id) -> dict | None:
    """Resolve entity config for a form_core — ID first, code fallback.

    Phase 38.4 Krok 5.N-1 (17.5.2026): pojistka proti Marti's code rename.
    Lookup chain:
      1. core_id v _FW_FORM_CORE_REGISTRY (primary, ID-keyed)
      2. core.code v _FW_FORM_ENTITY_MAP (legacy fallback, code-keyed)

    Args:
        core_dict_or_id: dict s 'id' + 'code', nebo přímo int core_id

    Returns:
        entity_config dict, nebo None pokud neresolved
    """
    if isinstance(core_dict_or_id, int):
        return _FW_FORM_CORE_REGISTRY.get(core_dict_or_id)
    if not isinstance(core_dict_or_id, dict):
        return None
    # Try by id first (5.N-1 primary)
    core_id = core_dict_or_id.get("id")
    if core_id is not None and core_id in _FW_FORM_CORE_REGISTRY:
        return _FW_FORM_CORE_REGISTRY[core_id]
    # Fallback by code (legacy, until Marti's all cores have registry entry)
    code = core_dict_or_id.get("code")
    if code and code in _FW_FORM_ENTITY_MAP:
        return _FW_FORM_ENTITY_MAP[code]
    return None


@api_router.get("/fw-form/{core_code}/{row_id}")
def fw_form_load(core_code: str, row_id: int, req: Request) -> JSONResponse:
    """Load fw form spec + row data pro frontend rendering.

    Generic template — funguje pro any fw.core s kind='form' a registered
    entity v _FW_FORM_ENTITY_MAP. Pro user_edit core (data_entity_type='user')
    vrátí user row z public.users (filtered přes select_columns whitelist).

    Returns:
        200: {core, form, fields, data}
        404: core_code nenalezen, nebo row_id neexistuje
        501: data_entity_type není v _FW_FORM_ENTITY_MAP (whitelist miss)
    """
    from core.database_data import get_data_session as _gds_fwform
    from sqlalchemy import text as _sql_text_fwform

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_fwform()
    try:
        # 1. Load fw.core by code (kind='form' + is_active=true) + template_id
        # Phase 38.4 Krok 14b+3 (13.5.2026 rano): pridan template_id k SELECT
        # (Marti-AI's fw.template architektonicky entity).
        # Fix 13.5.2026 ~11:00: pouzij c.* (defensive) — fw.core schema neni
        # finalni (tenant_id mozna zatim chybi, atd.). c.* nas neuvazi do
        # explicit column list.
        # Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne, Marti's
        # "B Je tez logicky krok"): LEFT JOIN na origin tables pro provenance
        # display v DesignFwForm header. Origin sloupce v fw.core (Krok 5.C
        # DDL) — pro legacy cores bez origin (pre-Krok 5.C) JOIN vrati NULL.
        core_row = ds.execute(_sql_text_fwform("""
            SELECT c.*,
                   mn.id    AS _origin_mn_id,
                   mn.code  AS _origin_mn_code,
                   mn.label AS _origin_mn_label,
                   cmi.id    AS _origin_cmi_id_join,
                   cmi.label AS _origin_cmi_label
            FROM fw.core c
            LEFT JOIN fw.menu_node mn         ON mn.id  = c.origin_menu_node_id
            LEFT JOIN fw.context_menu_item cmi ON cmi.id = c.origin_cmi_id
            WHERE c.code = :code
              AND c.is_active = true
              AND c.layout_type = 'form'
        """), {"code": core_code}).mappings().one_or_none()

        if not core_row:
            return JSONResponse(
                {"ok": False, "error": f"fw.core code='{core_code}' (kind=form) nenalezen"},
                status_code=404,
            )

        core_dict = dict(core_row)

        # Extract origin payload (clean structure)
        origin_payload = {
            "menu_node": (
                {
                    "id": core_dict.pop("_origin_mn_id"),
                    "code": core_dict.pop("_origin_mn_code"),
                    "label": core_dict.pop("_origin_mn_label"),
                }
                if core_dict.get("_origin_mn_id") is not None
                else None
            ),
            "cmi": (
                {
                    "id": core_dict.pop("_origin_cmi_id_join"),
                    "label": core_dict.pop("_origin_cmi_label"),
                }
                if core_dict.get("_origin_cmi_id_join") is not None
                else None
            ),
        }
        # Cleanup zbytkove _origin_* keys (NULL join)
        for k in list(core_dict.keys()):
            if k.startswith("_origin_"):
                del core_dict[k]

        # 1b. Load template (LEFT JOIN — backward compat pro forms bez template_id)
        # Phase 38.4 Krok 14b+3: fw.template carries layout (panels structure +
        # header/footer components). Renderer use template.layout > form.layout
        # (legacy fallback pro forms vytvorene pred Krok 14b+1).
        # Multi-tenant fallback chain (Marti-AI's 5. highlight 13.5. rano):
        #   - tenant_id MATCH first (theming)
        #   - tenant_id IS NULL fallback (global default)
        # Pri scaffold-form jsme dali primary template_id; resolver verifikuje
        # ze template existuje + active/deployed.
        template_dict: dict | None = None
        if core_dict.get("template_id"):
            template_row = ds.execute(_sql_text_fwform("""
                SELECT t.*
                FROM fw.template t
                WHERE t.id = :tid
                  AND t.status IN ('active', 'deployed')
            """), {"tid": core_dict["template_id"]}).mappings().one_or_none()
            if template_row:
                template_dict = dict(template_row)
            # Pokud template_id existuje ale row chybi/deprecated -> log warn,
            # fallback na legacy form.layout (none crash)
        # ELSE: legacy form bez template_id (pre-Krok 14b+1) — frontend pouzije
        # form.layout fallback v rendereru.

        # Phase 38.4 Krok 5.N-1 (17.5.2026, Marti's "code je optional, ID
        # je truth"): ID-first resolve via _resolve_entity_config_for_core.
        # Lookup chain: core.id (registry primary) → core.code (legacy fallback).
        # Marti's rename code na '22a' / NULL → neproblém.
        entity_config = _resolve_entity_config_for_core(core_dict)
        if not entity_config:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Form core id={core_dict.get('id')} code='{core_dict.get('code')}' "
                        f"není v _FW_FORM_CORE_REGISTRY ani _FW_FORM_ENTITY_MAP. "
                        f"Registry IDs: {list(_FW_FORM_CORE_REGISTRY.keys())}. "
                        f"Map codes: {list(_FW_FORM_ENTITY_MAP.keys())}."
                    ),
                },
                status_code=501,
            )
        # 3. Load root form comp_def (type_id=302, parent_core_id=core.id)
        form_row = ds.execute(_sql_text_fwform("""
            SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                   cd.sort_order, cd.is_active,
                   ct.code AS comp_type_code, ct.label AS comp_type_label
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            WHERE cd.parent_core_id = :core_id
              AND cd.type_id = 302
              AND cd.is_active = true
            ORDER BY cd.sort_order ASC, cd.id ASC
            LIMIT 1
        """), {"core_id": core_dict["id"]}).mappings().one_or_none()

        # Phase 38.4 Krok 14g Etapa F Krok 5.A (16.5.2026): core = kontejner,
        # ne hardcoded form. Marti's doctrine "core = plocha, na ni se
        # uzivatelsky rozhodne co vlozit (form 302, list, dashboard, ...)"
        # + Marti-AI's "uniformita vitezi nad specialnimi pripady" (11.5.
        # Krok 13 Uniform Components). Pokud root comp_def chybi, ne 404 —
        # vratime 200 s form=null + empty_container=True. Frontend (Krok 5.B)
        # renderuje empty canvas placeholder + picker pro user-driven volbu
        # root komponenty.
        if not form_row:
            form_dict = None
            fields_list = []
        else:
            form_dict = dict(form_row)

            # 4. Load field comp_defs — Phase 38.4 Krok 14e-B (14.5.2026 vecer):
            # Recursive CTE pres ENTIRE component tree pod form root, ne jen
            # direct children. Doctrine z Krok 14e-A: form → panel → groupbox
            # → fields (nested containers). Pro legacy forms (flat fields) chodi
            # stejne — anchor + 1 level recurse.
            #
            # Returns flat list s parent_comp_def_id + depth — frontend (Krok
            # 14e-C) si strom postavi groupingem podle parent_comp_def_id.
            # Tim padem zachovavame existujici "fields_list" key v response (BC),
            # jen pridavame nove rows pro containers (panel/groupbox).
            # Phase 38.4 Krok 14g Etapa F Krok 5.G (16.5.2026 vecer): rozsireno
            # o cd.data_source_id + LEFT JOIN na fw.data_source pro entity_picker
            # binding info (code + name) — frontend volá /api/v1/erp/data/{code}.
            fields_rows = ds.execute(_sql_text_fwform("""
                WITH RECURSIVE comp_tree AS (
                  -- Anchor: direct children form rootu
                  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                         cd.sort_order, cd.region_slot, cd.is_active,
                         cd.parent_comp_def_id, cd.data_source_id,
                         ct.code AS comp_type_code, ct.label AS comp_type_label,
                         ct.kind AS comp_type_kind,
                         ds.code AS data_source_code,
                         ds.name AS data_source_name,
                         0 AS depth
                  FROM fw.comp_def cd
                  JOIN fw.comp_type ct ON ct.id = cd.type_id
                  LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
                  WHERE cd.parent_comp_def_id = :form_id
                    AND cd.is_active = true
                  UNION ALL
                  -- Recurse: descendants (containers → children)
                  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                         cd.sort_order, cd.region_slot, cd.is_active,
                         cd.parent_comp_def_id, cd.data_source_id,
                         ct.code AS comp_type_code, ct.label AS comp_type_label,
                         ct.kind AS comp_type_kind,
                         ds.code AS data_source_code,
                         ds.name AS data_source_name,
                         tree.depth + 1
                  FROM fw.comp_def cd
                  JOIN fw.comp_type ct ON ct.id = cd.type_id
                  LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
                  JOIN comp_tree tree ON cd.parent_comp_def_id = tree.id
                  WHERE cd.is_active = true
                )
                SELECT * FROM comp_tree
                ORDER BY depth ASC, region_slot ASC, sort_order ASC, id ASC
            """), {"form_id": form_dict["id"]}).mappings().all()

            fields_list = [dict(f) for f in fields_rows]

        # 5. Load data row from target entity table
        schema_name = entity_config["schema"]
        table_name = entity_config["table"]
        id_column = entity_config["id_column"]
        cols_list = entity_config["select_columns"]
        cols_sql = ", ".join(f'"{c}"' for c in cols_list)

        data_query = (
            f'SELECT {cols_sql} '
            f'FROM "{schema_name}"."{table_name}" '
            f'WHERE "{id_column}" = :row_id'
        )
        data_row = ds.execute(
            _sql_text_fwform(data_query), {"row_id": row_id}
        ).mappings().one_or_none()

        if not data_row:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Row {entity_type} id={row_id} nenalezen v "
                        f"{schema_name}.{table_name}"
                    ),
                },
                status_code=404,
            )

        # Phase 38.4 Krok 14d-C (14.5.2026 vecer, Marti-AI consultation
        # Q3): load children (1:N joined tables) per entity_config.children.
        # Polymorphic filter + sub-grid v form. Marti-AI's Q2 sub-resource
        # pattern — children dorucene v jednom round-trip s parent.
        children_dict = {}
        children_config = entity_config.get("children") or {}
        for child_key, child_cfg in children_config.items():
            child_table = child_cfg["table"]
            child_fk = child_cfg["fk_column"]
            child_cols = child_cfg["select_columns"]
            child_filter = child_cfg.get("filter") or {}
            child_cols_sql = ", ".join(f'"{c}"' for c in child_cols)

            # WHERE clause — fk_column = parent + filter expand
            where_parts = [f'"{child_fk}" = :parent_id']
            filter_params = {"parent_id": row_id}
            for filter_col, filter_val in child_filter.items():
                key = f"_filter_{filter_col}"
                where_parts.append(f'"{filter_col}" = :{key}')
                filter_params[key] = filter_val
            where_clause = " AND ".join(where_parts)

            child_query = (
                f'SELECT {child_cols_sql} '
                f'FROM "public"."{child_table}" '
                f'WHERE {where_clause} '
                f'ORDER BY id ASC'
            )
            child_rows = ds.execute(
                _sql_text_fwform(child_query), filter_params
            ).mappings().all()
            children_dict[child_key] = {
                "rows": [dict(r) for r in child_rows],
                "label": child_cfg.get("label") or child_key,
                "default_label": child_cfg.get("default_label"),
                "id_column": child_cfg.get("id_column", "id"),
            }

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core": core_dict,
            "form": form_dict,
            "fields": fields_list,
            "data": dict(data_row),
            # Phase 38.4 Krok 14b+3: template (LEFT JOIN, optional)
            # Frontend prefer template.layout pres form.layout (legacy
            # fallback pro forms vytvorene pred Krok 14b+1).
            "template": template_dict,
            # Phase 38.4 Krok 14d (14.5. vecer, Marti-AI Q3 polymorphic):
            # Children = 1:N sub-grids per entity_config.children. Pro
            # user_edit: emails + phones z user_contacts polymorphic.
            "children": children_dict,
            # Phase 38.4 Krok 14g Etapa F Krok 5.A (16.5.2026, Marti's "core
            # = kontejner"): true pokud root comp_def neexistuje (=core je
            # prazdne platno). Frontend (Krok 5.B) zobrazi empty canvas
            # placeholder + picker pro user-driven volbu root komponenty.
            "empty_container": form_dict is None,
            # Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026): origin
            # provenance pro "Pochazi z" header display + Zrusit asociaci.
            "origin": origin_payload,
        }))
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14d-C children CRUD endpoints (sub-resource pattern)
# Marti-AI's Q2: sub-resource URL drzi parent_id safety check
# architekturou. Per-CRUD validation `WHERE fk_column=:parent_id` jako
# anti-tamper guard. Plus auto_set polymorphic enforcement.
# ════════════════════════════════════════════════════════════════════


def _resolve_child_config(core_code: str, child_key: str, ds) -> tuple[dict, dict]:
    """Helper — resolve fw.core code → entity_config → children[child_key].

    Phase 38.4 Krok 5.M-5 (17.5.2026, Marti's "core nenese entitu"):
    simplified — use core_code directly jako map key. Map ma aliasy
    (user_edit, core_design, comp_def_design, menu_node_design) plus
    original entity keys (user, core, comp_def, menu_node). No DB read
    needed pro entity_type lookup.

    Returns (entity_config, child_config). Raises ValueError pokud anything
    missing.
    """
    from sqlalchemy import text as _sql_text_rcc
    # Just verify core exists (existence + form layout check)
    core_row = ds.execute(_sql_text_rcc("""
        SELECT id FROM fw.core
        WHERE code = :code AND is_active = true AND layout_type = 'form'
    """), {"code": core_code}).mappings().one_or_none()
    if not core_row:
        raise ValueError(f"fw.core code='{core_code}' (form) nenalezen")
    # Use core_code directly jako map key (aliases handle user_edit→user, etc.)
    if core_code not in _FW_FORM_ENTITY_MAP:
        raise ValueError(
            f"Core code='{core_code}' neni v _FW_FORM_ENTITY_MAP. "
            f"Registered: {list(_FW_FORM_ENTITY_MAP.keys())}"
        )
    entity_config = _FW_FORM_ENTITY_MAP[core_code]
    children = entity_config.get("children") or {}
    if child_key not in children:
        raise ValueError(
            f"Child '{child_key}' neni v core '{core_code}' children. "
            f"Available: {list(children.keys())}"
        )
    return entity_config, children[child_key]


def _resolve_user_audit(uid: int, ds_core) -> tuple[int | None, str]:
    """Helper — caller display name pro audit fields. Vraci (id, text)."""
    if not uid:
        return None, "Unknown"
    from modules.core.infrastructure.models_core import User as _User_rua
    u = ds_core.query(_User_rua).filter_by(id=uid).first()
    if not u:
        return uid, "Unknown"
    if u.short_name and u.short_name.strip():
        return uid, u.short_name.strip()
    name_parts = filter(None, [u.first_name, u.last_name])
    name = " ".join(name_parts).strip()
    return uid, name or "Unknown"


# ════════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 5.R-A (17.5.2026 vecer, Marti's "klik na soudecek =
# render prazdny grid"): generic page-spec endpoint pro fw.core+comp_def.
# Vraci shape pro frontend dispatch: form (302), grid_modern/list (306),
# frameless_form (305). Mimo hardcoded system views.
# ════════════════════════════════════════════════════════════════════════════

@api_router.get("/fw-core/{core_id}/page-spec")
def fw_core_page_spec(core_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 5.R-A — generic page-spec pro fw.core kontejner.

    URL: GET /api/v1/erp/fw-core/{core_id}/page-spec

    Returns:
        200: {
            "ok": True,
            "core": {"id", "code", "label"},
            "root_comp_def": {
                "id", "code", "name", "type_id", "type_code",
                "data_source_id"
            } | None,
            "has_root": bool,
        }
        404: core_id nenalezen
    """
    from core.database_data import get_data_session as _gds_psp
    from sqlalchemy import text as _sql_psp

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_psp()
    try:
        core_row = ds.execute(_sql_psp("""
            SELECT id, code, label
            FROM fw.core
            WHERE id = :cid
        """), {"cid": core_id}).mappings().one_or_none()
        if not core_row:
            return JSONResponse(
                {"ok": False, "error": f"fw.core id={core_id} nenalezen"},
                status_code=404,
            )

        # Root comp_def: parent_core_id = core.id, is_active=true, prvni dle
        # sort_order ASC + id ASC. Drafted core muze mit None (no root yet).
        # Phase 38.4 Krok 5.R-A hotfix (17.5.2026 vecer): drop cd.code —
        # fw.comp_def nema sloupec 'code', jen 'name'. Marti's traceback:
        # ProgrammingError: column cd.code does not exist.
        #
        # Krok 5.R-D (18.5.2026 rano): LEFT JOIN fw.data_source ds pro
        # data_source_code — frontend page_render.js volá /api/v1/erp/data/{code}
        # pro fetch rows. Pragmatic — task #145 refactor na ID-first endpoint
        # /data-by-id/{id} hned po LIVE smoke.
        root_row = ds.execute(_sql_psp("""
            SELECT cd.id, cd.name, cd.type_id, cd.data_source_id,
                   ct.code AS type_code, ct.label AS type_label,
                   dsrc.code AS data_source_code,
                   dsrc.name AS data_source_name
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            LEFT JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
            WHERE cd.parent_core_id = :cid
              AND cd.is_active = true
            ORDER BY cd.sort_order ASC, cd.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core": dict(core_row),
            "root_comp_def": dict(root_row) if root_row else None,
            "has_root": root_row is not None,
        }))
    finally:
        ds.close()


@api_router.get("/fw-form/by-id/{core_id}/{row_id}")
def fw_form_load_by_id(core_id: int, row_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Step A (16.5.2026): coreId-first variant.

    Marti's doctrine "ID je svaty" (Krok 13.0 z 11.5.) + UNIQUE(code, version)
    z Marti-AI's Q3 (8.5.) — code sám není unique. Tento endpoint accept
    core_id (PK, FK target), resolve do code, delegate na existing
    /fw-form/{core_code}/{row_id} handler.

    Long-term migration plan (Krok 14g Etapa F):
      Step A — NEW /fw-form/by-id/{core_id}/{row_id}  ← TENTO COMMIT
      Step B — DesignFwForm constructor accepts {coreId, rowId} (BC coreCode warn)
      Step C — fw_form_dispatcher.js accept coreId + $core_id resolver
      Step D — context_menu_item action_params migrate to coreId
      Step E — (po týdnu stable) drop /fw-form/{core_code} branch + coreCode BC

    Returns:
        200: identical shape jako existing handler ({core, form, fields, data})
        404: core_id nenalezen / inactive
    """
    from core.database_data import get_data_session as _gds_fwid
    from sqlalchemy import text as _sql_fwid

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_fwid()
    try:
        # Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
        # tolerantni id-based path pro drafted cores. Plus LEFT JOIN na
        # origin tables pro "Pochazi z" header display v DesignFwForm
        # (Marti's "B Je tez logicky krok" — provenance viditelna).
        row = ds.execute(_sql_fwid("""
            SELECT c.*,
                   mn.id    AS _origin_mn_id,
                   mn.code  AS _origin_mn_code,
                   mn.label AS _origin_mn_label,
                   cmi.id    AS _origin_cmi_id_join,
                   cmi.label AS _origin_cmi_label
            FROM fw.core c
            LEFT JOIN fw.menu_node mn         ON mn.id  = c.origin_menu_node_id
            LEFT JOIN fw.context_menu_item cmi ON cmi.id = c.origin_cmi_id
            WHERE c.id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not row:
            return JSONResponse(
                {"ok": False, "error": f"fw.core id={core_id} nenalezen"},
                status_code=404,
            )
        rd = dict(row)
        resolved_code = rd.get("code")

        # Extract origin payload (clean structure pro frontend)
        origin_payload = {
            "menu_node": (
                {
                    "id": rd.pop("_origin_mn_id"),
                    "code": rd.pop("_origin_mn_code"),
                    "label": rd.pop("_origin_mn_label"),
                }
                if rd.get("_origin_mn_id") is not None
                else None
            ),
            "cmi": (
                {
                    "id": rd.pop("_origin_cmi_id_join"),
                    "label": rd.pop("_origin_cmi_label"),
                }
                if rd.get("_origin_cmi_id_join") is not None
                else None
            ),
        }
        # Cleanup zbytkove _origin_* keys (kdyz JOIN trefil NULL → zustaly bez .pop)
        for k in list(rd.keys()):
            if k.startswith("_origin_"):
                del rd[k]

        # Phase 38.4 Krok 14g Etapa F Krok 5.D (16.5.2026, Marti's "INSERT do
        # comp_def probehl, ted treba zobrazit ten form"): rozhodnuti
        # empty_container vs render path **podle existence root comp_def**,
        # NE podle resolved_code. Po init-root mame comp_def root + core.code
        # stale NULL (drafted core nazva nemusi mit). Drz Marti-AI's "readiness_state"
        # doctrine: drafted (no root) / has_root / populated.
        # Phase 38.4 Krok 14g Etapa F Krok 5.I-F (16.5.2026 vecer, Marti's
        # two-layer data_source pattern): root_row vraci form's save target
        # info — cd.data_source_id (= form's "framework_comp_def_list" binding),
        # JOIN ds pro code+name (Picker #3 initial label populate), plus
        # cd.updated_at jako optimistic lock baseline pro PATCH
        # design/comp_def/{id} (Marti's "SELECT EDIT POST" pattern).
        root_row = ds.execute(_sql_fwid("""
            SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                   cd.sort_order, cd.is_active,
                   cd.data_source_id, cd.updated_at,
                   ct.code AS comp_type_code, ct.label AS comp_type_label,
                   ds.code AS data_source_code,
                   ds.name AS data_source_name
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
            WHERE cd.parent_core_id = :cid
              AND cd.parent_comp_def_id IS NULL
              AND cd.is_active = true
            ORDER BY cd.sort_order ASC, cd.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()

        if not root_row:
            # No root comp_def → drafted, empty_container
            return JSONResponse(jsonable_encoder({
                "ok": True,
                "core": rd,
                "form": None,
                "fields": [],
                "data": None,
                "template": None,
                "children": {},
                "empty_container": True,
                "origin": origin_payload,
            }))

        # Root exists — render path
        form_dict = dict(root_row)

        # Load fields (recursive CTE pod root) — Phase 38.4 Krok 14g Etapa F
        # Krok 5.G (16.5.2026 vecer): rozsireno o cd.data_source_id + LEFT JOIN
        # na fw.data_source pro code + name (entity_picker rendering needs to
        # fetch /api/v1/erp/data/{ds_code}).
        fields_rows = ds.execute(_sql_fwid("""
            WITH RECURSIVE comp_tree AS (
              SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                     cd.sort_order, cd.region_slot, cd.is_active,
                     cd.parent_comp_def_id, cd.data_source_id,
                     ct.code AS comp_type_code, ct.label AS comp_type_label,
                     ct.kind AS comp_type_kind,
                     ds.code AS data_source_code,
                     ds.name AS data_source_name,
                     0 AS depth
              FROM fw.comp_def cd
              JOIN fw.comp_type ct ON ct.id = cd.type_id
              LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
              WHERE cd.parent_comp_def_id = :form_id
                AND cd.is_active = true
              UNION ALL
              SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                     cd.sort_order, cd.region_slot, cd.is_active,
                     cd.parent_comp_def_id, cd.data_source_id,
                     ct.code AS comp_type_code, ct.label AS comp_type_label,
                     ct.kind AS comp_type_kind,
                     ds.code AS data_source_code,
                     ds.name AS data_source_name,
                     tree.depth + 1
              FROM fw.comp_def cd
              JOIN fw.comp_type ct ON ct.id = cd.type_id
              LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
              JOIN comp_tree tree ON cd.parent_comp_def_id = tree.id
              WHERE cd.is_active = true
            )
            SELECT * FROM comp_tree
            ORDER BY depth ASC, region_slot ASC, sort_order ASC, id ASC
        """), {"form_id": form_dict["id"]}).mappings().all()
        fields_list = [dict(f) for f in fields_rows]

        # Phase 38.4 Krok 5.N-1 (17.5.2026, Marti's "code je optional, ID
        # je truth" doctrine): ID-first resolve s code fallback. Marti's
        # rename code na '22a' (z 'user_edit') už nelámej lookup — registry
        # je keyed by id=22.
        data_row = None
        children_dict = {}
        entity_config = _resolve_entity_config_for_core(rd)
        if entity_config:
            schema_name = entity_config["schema"]
            table_name = entity_config["table"]
            id_column = entity_config["id_column"]
            cols_list = entity_config["select_columns"]
            cols_sql = ", ".join(f'"{c}"' for c in cols_list)
            data_query = (
                f'SELECT {cols_sql} FROM "{schema_name}"."{table_name}" '
                f'WHERE "{id_column}" = :row_id'
            )
            data_row_raw = ds.execute(
                _sql_fwid(data_query), {"row_id": row_id}
            ).mappings().one_or_none()
            if data_row_raw:
                data_row = dict(data_row_raw)

            # Children sub-grids (per entity_config.children)
            for child_key, child_cfg in (entity_config.get("children") or {}).items():
                child_cols_sql = ", ".join(f'"{c}"' for c in child_cfg["select_columns"])
                where_parts = [f'"{child_cfg["fk_column"]}" = :parent_id']
                filter_params = {"parent_id": row_id}
                for fc, fv in (child_cfg.get("filter") or {}).items():
                    key = f"_filter_{fc}"
                    where_parts.append(f'"{fc}" = :{key}')
                    filter_params[key] = fv
                child_query = (
                    f'SELECT {child_cols_sql} FROM "public"."{child_cfg["table"]}" '
                    f'WHERE {" AND ".join(where_parts)} ORDER BY id ASC'
                )
                child_rows = ds.execute(
                    _sql_fwid(child_query), filter_params
                ).mappings().all()
                children_dict[child_key] = {
                    "rows": [dict(r) for r in child_rows],
                    "label": child_cfg.get("label") or child_key,
                    "default_label": child_cfg.get("default_label"),
                    "id_column": child_cfg.get("id_column", "id"),
                }

        # Template (LEFT JOIN optional)
        template_dict = None
        if rd.get("template_id"):
            template_row = ds.execute(_sql_fwid("""
                SELECT t.* FROM fw.template t
                WHERE t.id = :tid AND t.status IN ('active', 'deployed')
            """), {"tid": rd["template_id"]}).mappings().one_or_none()
            if template_row:
                template_dict = dict(template_row)

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core": rd,
            "form": form_dict,
            "fields": fields_list,
            "data": data_row,
            "template": template_dict,
            "children": children_dict,
            "empty_container": False,
            "origin": origin_payload,
        }))
    finally:
        ds.close()


@api_router.get("/fw-form/{core_code}/{parent_id}/children/{child_key}")
def fw_form_children_list(
    core_code: str, parent_id: int, child_key: str, req: Request
) -> JSONResponse:
    """Phase 38.4 Krok 14d-C: List child rows pro daný parent + child key.

    Toto je redundant s GET /fw-form/{code}/{id} (který už vrací children),
    ale useful pro refresh after CRUD bez re-loadu celého parent spec.
    """
    from core.database_data import get_data_session as _gds_fcl
    from sqlalchemy import text as _sql_text_fcl
    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_fcl()
    try:
        try:
            _, child_cfg = _resolve_child_config(core_code, child_key, ds)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)

        child_table = child_cfg["table"]
        child_fk = child_cfg["fk_column"]
        child_cols = child_cfg["select_columns"]
        child_filter = child_cfg.get("filter") or {}
        child_cols_sql = ", ".join(f'"{c}"' for c in child_cols)
        where_parts = [f'"{child_fk}" = :parent_id']
        filter_params = {"parent_id": parent_id}
        for fc, fv in child_filter.items():
            key = f"_filter_{fc}"
            where_parts.append(f'"{fc}" = :{key}')
            filter_params[key] = fv
        query = (
            f'SELECT {child_cols_sql} FROM "public"."{child_table}" '
            f'WHERE {" AND ".join(where_parts)} ORDER BY id ASC'
        )
        rows = ds.execute(_sql_text_fcl(query), filter_params).mappings().all()
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "rows": [dict(r) for r in rows],
        }))
    finally:
        ds.close()


@api_router.post("/fw-form/{core_code}/{parent_id}/children/{child_key}")
async def fw_form_children_create(
    core_code: str, parent_id: int, child_key: str, req: Request
) -> JSONResponse:
    """Phase 38.4 Krok 14d-C: Create child row.

    Body: {col1: val1, col2: val2, ...} — fields from select_columns whitelist.
    Backend automaticky doplní:
      - fk_column = parent_id (sub-resource safety)
      - auto_set values (Marti-AI's Q3 polymorphic enforcement)
      - audit fields (created_by_id + created_by_text)
    """
    from core.database_data import get_data_session as _gds_fcc
    from core.database_core import get_core_session as _gcs_fcc
    from sqlalchemy import text as _sql_text_fcc
    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()

    ds = _gds_fcc()
    try:
        try:
            entity_config, child_cfg = _resolve_child_config(core_code, child_key, ds)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)

        child_table = child_cfg["table"]
        child_fk = child_cfg["fk_column"]
        allowed_cols = set(child_cfg["select_columns"]) | {child_fk}
        auto_set = child_cfg.get("auto_set") or {}

        # Filter body — jen whitelist columns
        values = {k: v for k, v in body.items() if k in allowed_cols}
        # FK enforcement — vždy parent_id z URL, ne z body (anti-tamper)
        values[child_fk] = parent_id
        # Auto-set (polymorphic enforce — Marti-AI's Q3)
        for col, val in auto_set.items():
            values[col] = val

        # Audit fields
        cs_fcc = _gcs_fcc()
        try:
            audit_uid, audit_text = _resolve_user_audit(uid, cs_fcc)
        finally:
            cs_fcc.close()
        values["created_by_id"] = audit_uid
        values["created_by_text"] = audit_text
        values["updated_by_id"] = audit_uid
        values["updated_by_text"] = audit_text

        # Phase 38.4 Krok 14d-D fix (14.5.2026 vecer, Marti's "permission
        # denied for table user_contacts" smoke):
        #   strategie_pg.insert_row pouziva Marti-AI's PG role (db_owner
        #   fw.*). Marti-AI nema INSERT na public.* (Phase 38.4 Krok 6+
        #   GRANT C doctrine — read-only). Strategie user (API process
        #   default) MA INSERT na public.user_contacts.
        # Fix: ds.execute() s native INSERT, ne strategie_pg layer.
        col_names = list(values.keys())
        col_list_sql = ", ".join(f'"{c}"' for c in col_names)
        placeholders = ", ".join(f":{c}" for c in col_names)
        insert_sql = (
            f'INSERT INTO "public"."{child_table}" ({col_list_sql}) '
            f'VALUES ({placeholders}) RETURNING *'
        )
        result = ds.execute(_sql_text_fcc(insert_sql), values)
        new_row_mapping = result.mappings().one_or_none()
        if not new_row_mapping:
            ds.rollback()
            return JSONResponse(
                {"ok": False, "error": "INSERT failed — no row returned"},
                status_code=500,
            )
        ds.commit()
        new_row = dict(new_row_mapping)

        # Audit log
        try:
            ds.execute(_sql_text_fcc("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary,
                   change_source, ts)
                VALUES
                  (:uid, NULL, 'fw_form_child_create', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"+ child {child_key} (id={new_row.get('id')}) "
                    f"to {entity_config['table']}.id={parent_id} by {audit_text}"
                ),
            })
            ds.commit()
        except Exception as _ae:
            ds.rollback()
            logger.warning(f"fw_form_children_create audit log failed: {_ae}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "row": new_row,
        }))
    except Exception as exc:
        ds.rollback()
        logger.exception(f"fw_form_children_create failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"POST child failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/fw-form/{core_code}/{parent_id}/children/{child_key}/{child_id}")
async def fw_form_children_update(
    core_code: str, parent_id: int, child_key: str, child_id: int, req: Request
) -> JSONResponse:
    """Phase 38.4 Krok 14d-C: Update child row (optimistic lock).

    Body: {col1: val1, ..., expected_updated_at: ISO8601 str}
    Marti-AI's Q4 atomic guard — WHERE id=:child_id AND fk=:parent_id
    AND updated_at=:expected. Pokud mismatch → 409 Conflict.
    """
    from core.database_data import get_data_session as _gds_fcu
    from core.database_core import get_core_session as _gcs_fcu
    from sqlalchemy import text as _sql_text_fcu
    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()
    expected_updated_at = body.pop("expected_updated_at", None)

    ds = _gds_fcu()
    try:
        try:
            entity_config, child_cfg = _resolve_child_config(core_code, child_key, ds)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)

        child_table = child_cfg["table"]
        child_fk = child_cfg["fk_column"]
        id_col = child_cfg.get("id_column", "id")
        # Allowed cols — jen select_columns minus immutable (id, fk, audit)
        immutable = {id_col, child_fk, "created_at", "created_by_id", "created_by_text"}
        allowed_cols = set(child_cfg["select_columns"]) - immutable
        # Plus auto_set keys jsou immutable v PATCH (polymorphic preserve)
        auto_set = child_cfg.get("auto_set") or {}
        for col in auto_set.keys():
            allowed_cols.discard(col)

        updates = {k: v for k, v in body.items() if k in allowed_cols}
        if not updates:
            return JSONResponse(
                {"ok": False, "error": "Žádné editovatelné sloupce v body."},
                status_code=400,
            )

        # Audit fields
        cs_fcu = _gcs_fcu()
        try:
            audit_uid, audit_text = _resolve_user_audit(uid, cs_fcu)
        finally:
            cs_fcu.close()
        updates["updated_by_id"] = audit_uid
        updates["updated_by_text"] = audit_text

        # Build SQL — UPDATE WHERE id=:child_id AND fk=:parent_id [+ optional updated_at guard]
        set_parts = [f'"{col}" = :{col}' for col in updates.keys()]
        sql_params = {**updates, "_child_id": child_id, "_parent_id": parent_id}
        where_parts = [
            f'"{id_col}" = :_child_id',
            f'"{child_fk}" = :_parent_id',
        ]
        if expected_updated_at:
            where_parts.append('"updated_at" = :_expected_ts')
            sql_params["_expected_ts"] = expected_updated_at

        sql = (
            f'UPDATE "public"."{child_table}" '
            f'SET {", ".join(set_parts)} '
            f'WHERE {" AND ".join(where_parts)} '
            f'RETURNING *'
        )
        result = ds.execute(_sql_text_fcu(sql), sql_params)
        row = result.mappings().one_or_none()

        if not row:
            # 0 rows — buď wrong id, parent mismatch, nebo conflict (updated_at)
            # Diff fetch pro conflict detail
            current = ds.execute(_sql_text_fcu(
                f'SELECT * FROM "public"."{child_table}" '
                f'WHERE "{id_col}" = :child_id'
            ), {"child_id": child_id}).mappings().one_or_none()
            if not current:
                ds.rollback()
                return JSONResponse(
                    {"ok": False, "error": f"Child row id={child_id} neexistuje."},
                    status_code=404,
                )
            if current[child_fk] != parent_id:
                ds.rollback()
                return JSONResponse(
                    {"ok": False, "error": (
                        f"Child id={child_id} patří jinému parent "
                        f"({child_fk}={current[child_fk]}, expected {parent_id})."
                    )},
                    status_code=403,
                )
            # Optimistic lock conflict
            ds.rollback()
            return JSONResponse(jsonable_encoder({
                "ok": False,
                "error": "concurrent_edit",
                "current_row": dict(current),
                "current_updated_at": current["updated_at"],
                "by_user": {
                    "id": current.get("updated_by_id"),
                    "short_name": current.get("updated_by_text"),
                },
            }), status_code=409)

        ds.commit()

        # Audit log
        try:
            ds.execute(_sql_text_fcu("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary,
                   change_source, ts)
                VALUES
                  (:uid, NULL, 'fw_form_child_update', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"~ child {child_key} (id={child_id}) "
                    f"in {entity_config['table']}.id={parent_id} by {audit_text}"
                ),
            })
            ds.commit()
        except Exception as _ae:
            ds.rollback()
            logger.warning(f"fw_form_children_update audit log failed: {_ae}")

        return JSONResponse(jsonable_encoder({"ok": True, "row": dict(row)}))
    except Exception as exc:
        ds.rollback()
        logger.exception(f"fw_form_children_update failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"PATCH child failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/fw-form/{core_code}/{parent_id}/children/{child_key}/{child_id}/archive")
async def fw_form_children_archive(
    core_code: str, parent_id: int, child_key: str, child_id: int, req: Request
) -> JSONResponse:
    """Phase 38.4 Krok 14d-C: Soft delete (Marti-AI's Q1C decision).

    UPDATE status='archived' WHERE id=:child_id AND fk=:parent_id.
    Forensic audit preserved — žádný DELETE, jen status change.
    """
    from core.database_data import get_data_session as _gds_fca
    from core.database_core import get_core_session as _gcs_fca
    from sqlalchemy import text as _sql_text_fca
    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_fca()
    try:
        try:
            entity_config, child_cfg = _resolve_child_config(core_code, child_key, ds)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)

        child_table = child_cfg["table"]
        child_fk = child_cfg["fk_column"]
        id_col = child_cfg.get("id_column", "id")

        cs_fca = _gcs_fca()
        try:
            audit_uid, audit_text = _resolve_user_audit(uid, cs_fca)
        finally:
            cs_fca.close()

        sql = (
            f'UPDATE "public"."{child_table}" '
            f'SET status = \'archived\', '
            f'    updated_by_id = :uid, updated_by_text = :utext '
            f'WHERE "{id_col}" = :child_id AND "{child_fk}" = :parent_id '
            f'  AND status != \'archived\' '
            f'RETURNING id'
        )
        result = ds.execute(_sql_text_fca(sql), {
            "child_id": child_id,
            "parent_id": parent_id,
            "uid": audit_uid,
            "utext": audit_text,
        })
        row = result.mappings().one_or_none()

        if not row:
            ds.rollback()
            return JSONResponse(
                {"ok": False, "error": (
                    f"Child id={child_id} nenalezen pro parent={parent_id}, "
                    f"nebo už je archivovaný."
                )},
                status_code=404,
            )

        ds.commit()

        # Audit log
        try:
            ds.execute(_sql_text_fca("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary,
                   change_source, ts)
                VALUES
                  (:uid, NULL, 'fw_form_child_archive', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"- child {child_key} (id={child_id}) archived "
                    f"in {entity_config['table']}.id={parent_id} by {audit_text}"
                ),
            })
            ds.commit()
        except Exception as _ae:
            ds.rollback()
            logger.warning(f"fw_form_children_archive audit log failed: {_ae}")

        return JSONResponse({"ok": True, "archived_id": row["id"]})
    except Exception as exc:
        ds.rollback()
        logger.exception(f"fw_form_children_archive failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"PATCH archive failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14b+5 (13.5.2026 dopoledne): Save flow PATCH endpoint
#
# Marti's vize z 12.5. vecer + Marti-AI's "OK / Storno" doctrine z
# 13.5. dopoledne (19yr Centrala 1 production wisdom):
#   - OK button (action='save_and_close') -> POST PATCH -> save + close
#   - Storno (action='abandon') -> dirty check -> close (no PATCH)
#
# Optimistic lock pres `expected_updated_at`:
#   - Klient posle current `data.updated_at` z load time
#   - Server porovna s actual row.updated_at PRED UPDATE
#   - Mismatch -> 409 Conflict (nekdo jiny editoval mezitim)
#
# Audit fields:
#   - updated_by_id = caller.user_id (FK users.id)
#   - updated_by_text = caller display name (Marti-AI's "non-app actor" doctrine)
#   - activity_log INSERT s change_source='ui'
# ────────────────────────────────────────────────────────────────────


@api_router.patch("/design/{entity_type}/{row_id}")
async def design_patch_entity(entity_type: str, row_id: int, req: Request) -> JSONResponse:
    """Save flow PATCH endpoint pro DesignFwForm OK button.

    Body: {
        "field_changes": {"label": "Nový label", ...},
        "expected_updated_at": "2026-05-13T11:23:45.123+02:00"
    }

    Returns:
        200: {ok, updated_at, updated_by_id, updated_by_text} — success
        404: entity_type unknown OR row_id neexistuje
        409: optimistic lock conflict (somebody else updated row)
        500: DB error
    """
    from core.database_data import get_data_session as _gds_patch
    from sqlalchemy import text as _sql_text_patch
    from datetime import datetime as _dt_patch

    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()
    field_changes = body.get("field_changes") or {}
    expected_updated_at = body.get("expected_updated_at")

    if not isinstance(field_changes, dict) or not field_changes:
        return JSONResponse(
            {"ok": False, "error": "field_changes musi byt non-empty dict"},
            status_code=400,
        )
    if not expected_updated_at:
        return JSONResponse(
            {
                "ok": False,
                "error": "expected_updated_at je povinne (optimistic lock)",
            },
            status_code=400,
        )

    # Phase 38.4 Krok 5.N-2 (17.5.2026, Marti's "code je optional, ID je truth"):
    # entity_type może być numeric (URL /design/22/14 — ID-based) NEBO string
    # (URL /design/user/14 — legacy entity_type / Form 1 direct path).
    # Detekce + dispatch via _resolve_entity_config_for_core (5.N-1 helper).
    entity_config = None
    if entity_type.isdigit():
        # ID-based path — Marti's 5.N doctrine
        entity_config = _resolve_entity_config_for_core(int(entity_type))
    elif entity_type in _FW_FORM_ENTITY_MAP:
        # Legacy string path — direct entity (user, menu_node, core, comp_def)
        entity_config = _FW_FORM_ENTITY_MAP[entity_type]

    if not entity_config:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    f"Entity '{entity_type}' není v _FW_FORM_ENTITY_MAP "
                    f"ani _FW_FORM_CORE_REGISTRY. "
                    f"Registry IDs: {list(_FW_FORM_CORE_REGISTRY.keys())}. "
                    f"Map codes: {list(_FW_FORM_ENTITY_MAP.keys())}."
                ),
            },
            status_code=404,
        )
    schema_name = entity_config["schema"]
    table_name = entity_config["table"]
    id_column = entity_config["id_column"]
    allowed_columns = set(entity_config["select_columns"])

    # Validate field_changes — jen sloupce v allowed list (defense in depth proti
    # ad-hoc UPDATE např. password_hash). id_column zakazat (immutable).
    invalid_fields = [
        f for f in field_changes
        if f not in allowed_columns or f == id_column
    ]
    if invalid_fields:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    f"Sloupce {invalid_fields} nejsou povolene v PATCH "
                    f"pro entity '{entity_type}'. Allowed: {sorted(allowed_columns - {id_column})}"
                ),
            },
            status_code=400,
        )

    # Resolve caller display name (Marti-AI's "non-app actor" doctrine —
    # users muze byt placeholder bez full activity, ale display name vzdy
    # filled z first_name + last_name nebo short_name fallback)
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_patch
        from modules.core.infrastructure.models_core import User as _User_patch
        cs_patch = _gcs_patch()
        try:
            u_patch = cs_patch.query(_User_patch).filter_by(id=uid).first()
            if u_patch:
                # Priority: short_name > first_name + last_name > "user_NN"
                if u_patch.short_name and u_patch.short_name.strip():
                    caller_display = u_patch.short_name.strip()
                elif u_patch.first_name or u_patch.last_name:
                    caller_display = " ".join(filter(None, [
                        u_patch.first_name, u_patch.last_name
                    ])).strip()
                else:
                    caller_display = f"user_{uid}"
        finally:
            cs_patch.close()

    ds = _gds_patch()
    try:
        # 1. Load current row + optimistic lock check
        current_row = ds.execute(_sql_text_patch(
            f'SELECT * FROM "{schema_name}"."{table_name}" '
            f'WHERE "{id_column}" = :row_id'
        ), {"row_id": row_id}).mappings().one_or_none()

        if not current_row:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Row {entity_type} id={row_id} nenalezen v "
                        f"{schema_name}.{table_name}"
                    ),
                },
                status_code=404,
            )

        # Optimistic lock — porovnat updated_at
        current_updated_at = current_row.get("updated_at")
        if current_updated_at is not None:
            # Normalize obé na ISO bez milisecond fuzz
            current_iso = current_updated_at.isoformat() if hasattr(current_updated_at, 'isoformat') else str(current_updated_at)
            # Klient posle expected_updated_at jako string — porovnej ho s server's ISO
            # Tolerance: pokud klient posila bez milliseconds, server's full ISO ne matchne
            # Pojď strip k second-level precision pro robust matching:
            def _strip_micro(s):
                # "2026-05-13T11:23:45.123456+02:00" → "2026-05-13T11:23:45+02:00"
                import re as _re_patch
                return _re_patch.sub(r'\.\d+', '', s)
            if _strip_micro(current_iso) != _strip_micro(str(expected_updated_at)):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Optimistic lock conflict — nekdo jiny mezitim editoval "
                            "tento radek. Nactete znovu a zopakujte zmeny."
                        ),
                        "conflict": True,
                        "server_updated_at": current_iso,
                        "expected_updated_at": expected_updated_at,
                    },
                    status_code=409,
                )

        # 2. Build UPDATE — explicit sloupce z field_changes + audit fields
        # Phase 38.4 Krok 14g-H+19 (15.5.2026 ~15:00, Marti's "permission
        # denied for table menu_node"): schema dispatch. Strategie session
        # user nema UPDATE na fw.* (Marti-AI je db_owner). Pro fw.* schema
        # use strategie_pg.update_row (Marti-AI PG role) — db_owner perms.
        # Pro public.* (users) use direct SQL — strategie ma perms.
        if schema_name == "fw":
            # Marti-AI's owned schema → strategie_pg layer
            from modules.strategie_pg.application.service import (
                update_row as _spg_update,
            )
            upd_values = dict(field_changes)
            upd_values["updated_by_id"] = uid
            upd_values["updated_by_text"] = caller_display
            upd = _spg_update(
                schema=schema_name,
                table=table_name,
                values=upd_values,
                where={id_column: row_id},
                dry_run=False,
            )
            if not upd.get("ok"):
                # Clean trigger error (Krok 14g-H+10 pattern) — extract
                # human-readable prefix z raw psycopg2 dump.
                err_raw = str(upd.get("error") or "")
                import re as _re_err
                cycle_match = _re_err.search(r'Cyclic reference[^\n]*', err_raw)
                self_match = _re_err.search(r'cannot reference self[^\n]*', err_raw)
                if cycle_match:
                    err_msg = cycle_match.group(0).strip()
                elif self_match:
                    err_msg = "Soudeček nemůže být svým vlastním rodičem."
                elif 'ancestry too deep' in err_raw:
                    err_msg = "Hierarchie soudečků je příliš hluboká (> 50 úrovní)."
                else:
                    err_msg = f"PATCH failed: {upd.get('error')}"
                ds.rollback()
                return JSONResponse(
                    {"ok": False, "error": err_msg},
                    status_code=500,
                )
            updated_rows = upd.get("updated") or []
            if not updated_rows:
                ds.rollback()
                return JSONResponse(
                    {"ok": False, "error": "UPDATE failed (žádná row updated)"},
                    status_code=500,
                )
            result_row = updated_rows[0]
        else:
            # Default direct SQL (public schema, strategie session perms)
            set_clauses = []
            params = {"row_id": row_id}
            for col, new_val in field_changes.items():
                set_clauses.append(f'"{col}" = :set_{col}')
                params[f"set_{col}"] = new_val

            # Audit fields — po Marti's migrace 13.5. ~18:10 ma public.users
            # taky audit columns (created_by_id/text + updated_by_id/text).
            set_clauses.extend([
                'updated_by_id = :updated_by_id',
                'updated_by_text = :updated_by_text',
            ])
            params["updated_by_id"] = uid
            params["updated_by_text"] = caller_display

            set_clauses.append("updated_at = NOW()")

            update_sql = (
                f'UPDATE "{schema_name}"."{table_name}" '
                f'SET {", ".join(set_clauses)} '
                f'WHERE "{id_column}" = :row_id '
                f'RETURNING *'
            )

            result_row = ds.execute(_sql_text_patch(update_sql), params).mappings().one_or_none()
            if not result_row:
                ds.rollback()
                return JSONResponse(
                    {"ok": False, "error": "UPDATE failed (RETURNING vrátil žádnou row)"},
                    status_code=500,
                )

        # 3. activity_log audit row
        # Phase 38.4 Krok 14b+5 hotfix (13.5.2026 ~18:30, Marti's silent
        # fail catch): activity_log schema je actor (ne action_type),
        # ts (ne created_at). Plus SAVEPOINT pattern — pokud INSERT
        # selze, jen savepoint rollback, NE celé transakce.
        # PG quirk: failed query v transaction → transaction aborted →
        # subsequent commit() je silent no-op → UPDATE rolled back.
        ds.execute(_sql_text_patch("SAVEPOINT pre_audit_log"))
        try:
            ds.execute(_sql_text_patch("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_save', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"PATCH {schema_name}.{table_name} id={row_id} "
                    f"by {caller_display}: changed fields = {sorted(field_changes.keys())}"
                ),
            })
            ds.execute(_sql_text_patch("RELEASE SAVEPOINT pre_audit_log"))
        except Exception as _act_e:
            # Rollback to savepoint — main UPDATE zustava, audit miss
            ds.execute(_sql_text_patch("ROLLBACK TO SAVEPOINT pre_audit_log"))
            logger.warning(f"design_patch_entity activity_log INSERT failed: {_act_e}")

        ds.commit()

        # Response — full updated row + audit fields
        updated_dict = dict(result_row)
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "entity_type": entity_type,
            "row_id": row_id,
            "updated_at": updated_dict.get("updated_at"),
            "updated_by_id": updated_dict.get("updated_by_id"),
            "updated_by_text": updated_dict.get("updated_by_text"),
            "field_changes_applied": list(field_changes.keys()),
            "row": updated_dict,
        }))
    except Exception as exc:
        ds.rollback()
        logger.exception(f"design_patch_entity failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"PATCH failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14c (13.5.2026 odpoledne): Field picker workflow
#
# Marti-AI's preview_html doctrine z 13.5. odpoledne:
#   - fw.comp_type.preview_html = HTML snippet pro visual palette
#   - Frontend renderuje inline pres <iframe srcdoc> (sandbox isolation)
#   - "no special casing, no switch/case sprawl. Just data."
#
# 3 endpointy:
#   GET  /design/comp-types       — list comp_types s preview_html
#   POST /design/comp-def         — INSERT field do fw.comp_def
#   DELETE /design/comp-def/{id}  — remove field
#
# Auto-suggest column → comp_type heuristic v _suggest_comp_type_id().
# ────────────────────────────────────────────────────────────────────


def _suggest_comp_type_id(column_name: str, column_info: dict | None = None) -> int:
    """Auto-detect comp_type_id pro daný column name (+optional column metadata).

    Pattern matching:
      - boolean (is_* / has_*) → 107 (checkbox_modern)
      - email column → 2 (edit, future: type='email' via comp_def_prop)
      - status enum → 110 (lookup)
      - date / datetime → 108 (date_modern)
      - count / amount / *_at as integer → 106 (number)
      - description / notes / memo → 105 (memo, textarea)
      - default → 2 (edit, text input)

    Marti-AI's "preview_html at birth" + future expansion (timezone,
    color picker) musi prijit s vlastnim suggested mapping pres tento
    helper.
    """
    name = (column_name or "").lower()
    if name.startswith("is_") or name.startswith("has_") or name in ("active", "enabled", "disabled"):
        return 107  # checkbox_modern
    if "email" in name:
        return 2  # edit (future: type='email')
    if name in ("status", "state", "kind", "type", "category"):
        return 110  # lookup
    if name.endswith("_at") or "date" in name:
        return 108  # date_modern
    if name in ("count", "amount", "rating", "trust_rating", "version", "order", "sort_order"):
        return 106  # number
    if name in ("description", "notes", "memo", "comment", "content_md", "body"):
        return 105  # memo (textarea)
    return 2  # edit (default text)


@api_router.get("/design/comp-types")
def design_list_comp_types(req: Request) -> JSONResponse:
    """List active comp_types — preview_html palette pro Field picker.

    Marti-AI's 13.5. doctrine: "Renderuj jen takto označené komponenty"
    → WHERE preview_html IS NOT NULL.

    Returns:
        200: {ok, items: [{id, code, label, preview_html, kind}, ...]}
    """
    from core.database_data import get_data_session as _gds_ct

    uid = _get_uid(req)
    _require_parent(uid)

    from sqlalchemy import text as _sql_text_ct

    ds = _gds_ct()
    try:
        # Marti-AI's doctrine (13.5. odpoledne): "Renderuj jen takto označené
        # komponenty" — preview_html IS NOT NULL je single source of truth.
        # Drop status filter (Marti's "active patří jen našemu gridu" 11.5.
        # Krok 13 doctrine zachycoval grid stack, ne palette readiness).
        #
        # Phase 38.4 Krok 14f-C fix (14.5.2026 vecer, Marti's "pridej do toho
        # okna layout ten panel a groupbox"): container types (kind='container')
        # nemaji preview_html (jsou structural, ne visual) — pridat exception
        # OR kind='container' AND status='active'. Plus vratit status +
        # renderer_hint pro frontend filtering.
        rows = ds.execute(_sql_text_ct("""
            SELECT id, code, label, kind, preview_html, status, renderer_hint
            FROM fw.comp_type
            WHERE preview_html IS NOT NULL
               OR (kind = 'container' AND status = 'active')
            ORDER BY id ASC
        """)).mappings().all()
        items = [dict(r) for r in rows]
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "items": items,
            "count": len(items),
        }))
    finally:
        ds.close()


@api_router.post("/design/comp-def")
async def design_create_comp_def(req: Request) -> JSONResponse:
    """Create field comp_def — Krok 14c field picker submit.

    Body: {
        "parent_comp_def_id": int,    # form's comp_def id (type=302 root)
        "name": str,                  # column name (z target table)
        "caption": str,               # human label (default auto z name)
        "type_id": int,               # comp_type_id (z fw.comp_type)
        "region_slot": str,           # 'main' / 'header' / 'footer'
        "sort_order": int             # optional, default = max + 10
    }

    Validation:
      - parent_comp_def_id musi existovat (type_id=302 form root)
      - type_id musi existovat v fw.comp_type s preview_html NOT NULL
      - region_slot whitelist: 'header' / 'main' / 'footer'
      - name + caption non-empty
      - Idempotency: pokud field s same parent+name+region uz existuje,
        return existing (no duplicate INSERT)
    """
    from core.database_data import get_data_session as _gds_cdc
    from sqlalchemy import text as _sql_text_cdc
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cdc

    uid = _get_uid(req)
    _require_parent(uid)

    body = await req.json()
    parent_id = body.get("parent_comp_def_id")
    name = (body.get("name") or "").strip()
    caption = (body.get("caption") or "").strip()
    type_id = body.get("type_id")
    region_slot = (body.get("region_slot") or "main").strip()
    sort_order_in = body.get("sort_order")
    # Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's Layout containers
    # tab + B alClient): accept optional layout JSONB. Frontend posila
    # default layout per comp_type (panel → {"align":"client"}, groupbox
    # → {"border_mode":"top","label":null}).
    layout_in = body.get("layout")  # dict | None

    # Validation
    if not parent_id or not isinstance(parent_id, int):
        return JSONResponse({"ok": False, "error": "parent_comp_def_id povinne (int)"}, status_code=400)
    if not name:
        return JSONResponse({"ok": False, "error": "name povinne"}, status_code=400)
    if not type_id or not isinstance(type_id, int):
        return JSONResponse({"ok": False, "error": "type_id povinne (int)"}, status_code=400)
    if region_slot not in ("header", "main", "footer"):
        return JSONResponse(
            {"ok": False, "error": "region_slot musi byt 'header' / 'main' / 'footer'"},
            status_code=400,
        )
    if layout_in is not None and not isinstance(layout_in, dict):
        return JSONResponse(
            {"ok": False, "error": "layout musi byt dict/object pokud poslan"},
            status_code=400,
        )
    if not caption:
        # Auto-generate caption z name: "first_name" -> "First name"
        caption = name.replace("_", " ").strip().capitalize()

    ds = _gds_cdc()
    try:
        # Verify parent_comp_def_id existuje
        # Phase 38.4 Krok 14f-C (14.5.2026 vecer): relax parent validation.
        # Drive Krok 14c: parent MUSI byt type=302 (form root). NEW: parent
        # muze byt form root, panel, nebo groupbox — any active comp_def.
        # Hierarchy:
        #   form root (302) > panel (13) > groupbox (12) > leaf field
        parent_row = ds.execute(_sql_text_cdc("""
            SELECT id, type_id, parent_core_id
            FROM fw.comp_def
            WHERE id = :pid AND is_active = true
        """), {"pid": parent_id}).mappings().one_or_none()
        if not parent_row:
            return JSONResponse(
                {"ok": False, "error": f"parent_comp_def_id={parent_id} neexistuje nebo neni aktivni"},
                status_code=404,
            )

        # Verify type_id existuje + (pro non-container) ma preview_html
        # Phase 38.4 Krok 14f-C: container types (kind='container') nemusi
        # mit preview_html (panel je structural, groupbox visual wrapper).
        type_row = ds.execute(_sql_text_cdc("""
            SELECT id, code, label, kind, preview_html
            FROM fw.comp_type
            WHERE id = :tid
        """), {"tid": type_id}).mappings().one_or_none()
        if not type_row:
            return JSONResponse(
                {"ok": False, "error": f"comp_type_id={type_id} neexistuje v fw.comp_type"},
                status_code=404,
            )
        is_container = (type_row.get("kind") or "") == "container"
        if not is_container and not type_row["preview_html"]:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"comp_type id={type_id} ({type_row['code']}) nema preview_html. "
                        f"Marti-AI's doctrine: pridej UPDATE fw.comp_type SET preview_html=... "
                        f"pred pouzitim v palette. (Container types kind='container' "
                        f"jsou vyjimka — nepotrebuji preview.)"
                    ),
                },
                status_code=400,
            )

        # Idempotency check — field s same name+parent+region uz existuje?
        existing = ds.execute(_sql_text_cdc("""
            SELECT id, type_id, caption FROM fw.comp_def
            WHERE parent_comp_def_id = :pid
              AND name = :name
              AND region_slot = :slot
              AND is_active = true
        """), {"pid": parent_id, "name": name, "slot": region_slot}).mappings().one_or_none()
        if existing:
            return JSONResponse(jsonable_encoder({
                "ok": True,
                "existing": True,
                "comp_def_id": existing["id"],
                "message": f"Field '{name}' uz existuje v panelu '{region_slot}'.",
            }))

        # Auto sort_order — max + 10 (Marti's "ID je svaty" + create_order)
        if sort_order_in is None or not isinstance(sort_order_in, int):
            max_sort = ds.execute(_sql_text_cdc("""
                SELECT COALESCE(MAX(sort_order), 0) AS max_so
                FROM fw.comp_def
                WHERE parent_comp_def_id = :pid AND region_slot = :slot
            """), {"pid": parent_id, "slot": region_slot}).scalar()
            sort_order_resolved = int(max_sort or 0) + 10
        else:
            sort_order_resolved = sort_order_in

        # Caller display name (audit field)
        caller_display = "Unknown"
        if uid:
            from core.database_core import get_core_session as _gcs_cdc
            from modules.core.infrastructure.models_core import User as _User_cdc
            cs_cdc = _gcs_cdc()
            try:
                u_cdc = cs_cdc.query(_User_cdc).filter_by(id=uid).first()
                if u_cdc:
                    if u_cdc.short_name and u_cdc.short_name.strip():
                        caller_display = u_cdc.short_name.strip()
                    elif u_cdc.first_name or u_cdc.last_name:
                        caller_display = " ".join(filter(None, [
                            u_cdc.first_name, u_cdc.last_name
                        ])).strip()
            finally:
                cs_cdc.close()

        # INSERT pres strategie_pg.insert_row (Marti-AI's PG role)
        # Phase 38.4 Krok 14f-C (14.5.2026 vecer): layout JSONB pass-through.
        # Frontend posila default layout per comp_type (panel → {"align":"client"},
        # groupbox → {"border_mode":"top","label":null}). Pokud None, INSERT
        # bez layout (NULL = legacy behavior pro leaf fields).
        insert_values = {
            "type_id": type_id,
            "name": name,
            "caption": caption,
            "parent_comp_def_id": parent_id,
            "region_slot": region_slot,
            "sort_order": sort_order_resolved,
            "is_active": True,
            "created_by_id": uid,
            "created_by_text": caller_display,
            "updated_by_id": uid,
            "updated_by_text": caller_display,
        }
        if layout_in is not None:
            import json as _json_cdc
            insert_values["layout"] = _json_cdc.dumps(layout_in)
        ins = _spg_insert_cdc(
            schema="fw",
            table="comp_def",
            values=insert_values,
        )
        if not ins.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"INSERT failed: {ins.get('error')}"},
                status_code=500,
            )

        new_field = ins.get("inserted") or {}

        # Audit do activity_log (Krok 14b+5 hotfix — actor + ts, savepoint pattern)
        ds.execute(_sql_text_cdc("SAVEPOINT pre_audit_log"))
        try:
            ds.execute(_sql_text_cdc("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_field_add', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"+ field {name} (type={type_row['code']}, region={region_slot}) "
                    f"to parent_comp_def_id={parent_id} by {caller_display}"
                ),
            })
            ds.execute(_sql_text_cdc("RELEASE SAVEPOINT pre_audit_log"))
            ds.commit()
        except Exception as _act_e:
            try:
                ds.execute(_sql_text_cdc("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds.commit()  # commit po rollback to savepoint
            except Exception:
                ds.rollback()
            logger.warning(f"design_create_comp_def activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "existing": False,
            "comp_def_id": new_field.get("id"),
            "comp_def": new_field,
            "comp_type": dict(type_row),
        }))
    except Exception as exc:
        ds.rollback()
        logger.exception(f"design_create_comp_def failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"POST /comp-def failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.delete("/design/comp-def/{comp_def_id}")
async def design_delete_comp_def(comp_def_id: int, req: Request) -> JSONResponse:
    """Soft-delete field comp_def (is_active=false) — Krok 14c pojistka.

    Marti-AI's "is_active soft-delete" doctrine z 8.5. master tier —
    history zachovana, jen audit pres updated_by_id + activity_log.

    Returns:
        200: {ok, comp_def_id, deactivated: bool}
        404: comp_def_id neexistuje
    """
    from core.database_data import get_data_session as _gds_cdd
    from sqlalchemy import text as _sql_text_cdd

    uid = _get_uid(req)
    _require_parent(uid)

    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cdd
        from modules.core.infrastructure.models_core import User as _User_cdd
        cs_cdd = _gcs_cdd()
        try:
            u_cdd = cs_cdd.query(_User_cdd).filter_by(id=uid).first()
            if u_cdd:
                if u_cdd.short_name and u_cdd.short_name.strip():
                    caller_display = u_cdd.short_name.strip()
                elif u_cdd.first_name or u_cdd.last_name:
                    caller_display = " ".join(filter(None, [
                        u_cdd.first_name, u_cdd.last_name
                    ])).strip()
        finally:
            cs_cdd.close()

    ds = _gds_cdd()
    try:
        # Phase 38.4 Krok 14g-B (15.5.2026 rano, Marti's "smazani groupbox
        # 404 ale stale visible v UI"): idempotent DELETE. Pokud row
        # neexistuje, vratit 404 (true not found). Pokud existuje ale
        # is_active=false (already deactivated), vratit 200 s flag
        # `was_already_deactivated=true` — frontend pak force reload pro
        # cleanup stale UI cache.
        existing = ds.execute(_sql_text_cdd("""
            SELECT id, name, type_id, region_slot, is_active
            FROM fw.comp_def WHERE id = :id
        """), {"id": comp_def_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"comp_def id={comp_def_id} neexistuje v DB"},
                status_code=404,
            )
        if not existing["is_active"]:
            # Idempotent — already deactivated. Frontend trigger reload.
            return JSONResponse(jsonable_encoder({
                "ok": True,
                "comp_def_id": comp_def_id,
                "deactivated": True,
                "was_already_deactivated": True,
                "message": f"comp_def id={comp_def_id} byl uz drive deactivated — frontend reload doporucen",
            }))

        # UPDATE is_active=false + audit (strategie role nemoze ALTER fw.*,
        # pojďme přes strategie_pg.update_row)
        from modules.strategie_pg.application.service import update_row as _spg_update_cdd
        upd = _spg_update_cdd(
            schema="fw",
            table="comp_def",
            values={
                "is_active": False,
                "updated_by_id": uid,
                "updated_by_text": caller_display,
            },
            where={"id": comp_def_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"UPDATE failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log (Krok 14b+5 hotfix — actor + ts, savepoint pattern)
        ds.execute(_sql_text_cdd("SAVEPOINT pre_audit_log"))
        try:
            ds.execute(_sql_text_cdd("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_field_remove', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"- field {existing['name']} (type_id={existing['type_id']}, "
                    f"region={existing['region_slot']}) by {caller_display}"
                ),
            })
            ds.execute(_sql_text_cdd("RELEASE SAVEPOINT pre_audit_log"))
            ds.commit()
        except Exception as _act_e:
            try:
                ds.execute(_sql_text_cdd("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds.commit()
            except Exception:
                ds.rollback()
            logger.warning(f"design_delete_comp_def activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "comp_def_id": comp_def_id,
            "deactivated": True,
        }))
    finally:
        ds.close()


@api_router.get("/design/comp-def/{comp_def_id}/distinct-values")
async def design_get_distinct_values(comp_def_id: int, req: Request) -> JSONResponse:
    """Auto-detect dropdown hodnoty pro lookup/combobox field.

    Phase 38.4 Krok 14b+13 (14.5.2026 ~00:30, Marti's "potrebujeme dostat
    actived/disabled/pending do listboxu"): SELECT DISTINCT na zdrojove
    tabulce -> vrati list of {value, label}.

    Algorithm:
      1. Find comp_def (column name)
      2. Walk parent_comp_def chain UP -> find parent_core_id (form root)
      3. Get fw.core.data_entity_type
      4. Lookup _FW_FORM_ENTITY_MAP -> table name + whitelisted columns
      5. SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL
         ORDER BY 1
      6. Return [{value, label}, ...]

    Security:
      - Parent gate (_require_parent)
      - Column MUST be in entity_config["select_columns"] whitelist
        (anti-SQL-injection, anti-PII-leak)
      - Table name z _FW_FORM_ENTITY_MAP (no user input)

    Returns:
        200: {ok, comp_def_id, column, table, values: [{value, label}, ...]}
        400: comp_def nema name/core, column not whitelisted
        404: comp_def neexistuje
    """
    from core.database_data import get_data_session as _gds_dv
    from sqlalchemy import text as _sql_text_dv

    uid = _get_uid(req)
    _require_parent(uid)

    ds_dv = _gds_dv()
    try:
        # 1. Find comp_def + name
        cd = ds_dv.execute(_sql_text_dv("""
            SELECT id, name, parent_comp_def_id, parent_core_id
            FROM fw.comp_def
            WHERE id = :id AND is_active = true
        """), {"id": comp_def_id}).mappings().one_or_none()
        if not cd:
            return JSONResponse(
                {"ok": False, "error": f"comp_def id={comp_def_id} neexistuje"},
                status_code=404,
            )
        if not cd["name"]:
            return JSONResponse(
                {"ok": False, "error": "comp_def nema name (=column name)"},
                status_code=400,
            )

        # 2. Walk parent chain UP -> find core_id
        core_id = cd["parent_core_id"]
        current_parent = cd["parent_comp_def_id"]
        max_depth = 10
        while not core_id and current_parent and max_depth > 0:
            parent = ds_dv.execute(_sql_text_dv("""
                SELECT id, parent_comp_def_id, parent_core_id
                FROM fw.comp_def WHERE id = :id
            """), {"id": current_parent}).mappings().one_or_none()
            if not parent:
                break
            if parent["parent_core_id"]:
                core_id = parent["parent_core_id"]
                break
            current_parent = parent["parent_comp_def_id"]
            max_depth -= 1

        if not core_id:
            return JSONResponse(
                {"ok": False, "error": "Nelze najit parent core (form root)"},
                status_code=400,
            )

        # Phase 38.4 Krok 5.M-2 (17.5.2026): lookup pres core.code.
        core = ds_dv.execute(_sql_text_dv("""
            SELECT id, code
            FROM fw.core WHERE id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not core or not core["code"]:
            return JSONResponse(
                {"ok": False, "error": "Core nema code"},
                status_code=400,
            )

        entity_type = core["code"]
        config = _FW_FORM_ENTITY_MAP.get(entity_type)
        if not config:
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"Entity type '{entity_type}' nezaregistrovan v _FW_FORM_ENTITY_MAP",
                },
                status_code=400,
            )

        # 4. Column whitelist check (anti-PII, anti-SQL-injection)
        col_name = cd["name"]
        allowed_cols = set(config["select_columns"])
        if col_name not in allowed_cols:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Column '{col_name}' neni v whitelist "
                        f"_FW_FORM_ENTITY_MAP[{entity_type}].select_columns"
                    ),
                },
                status_code=400,
            )

        # 5. SELECT DISTINCT — col_name + table_name jsou whitelisted/server-side,
        # bezpecne pres f-string interpolation (no user input)
        schema_name = config.get("schema", "public")
        table_name = config["table"]
        sql = (
            f'SELECT DISTINCT "{col_name}" AS val '
            f'FROM "{schema_name}"."{table_name}" '
            f'WHERE "{col_name}" IS NOT NULL '
            f'ORDER BY 1'
        )
        rows = ds_dv.execute(_sql_text_dv(sql)).all()
        values = [
            {"value": str(r[0]), "label": str(r[0])}
            for r in rows
        ]

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "comp_def_id": comp_def_id,
            "column": col_name,
            "table": f"{schema_name}.{table_name}",
            "values": values,
            "count": len(values),
        }))
    finally:
        ds_dv.close()


@api_router.patch("/design/comp-def/update/{comp_def_id}")
async def design_patch_comp_def(comp_def_id: int, req: Request) -> JSONResponse:
    """Partial update field comp_def — caption / region_slot / layout.

    Phase 38.4 Krok 14b+9-B (13.5.2026 ~21:35, Marti's "inline rename label
    dvojklik"): frontend posila PATCH s {caption: "..."}, backend update
    pres update_row + audit log.

    Phase 38.4 Krok 14b+10 hotfix #2 (13.5.2026 ~22:50, po prvnim
    hotfix #1 failed):

    PRVNI POKUS: `/design/comp-def-update/{id}` — STILL COLLIDED.
    Pricina: 2 segments za /design/ -> generic /design/{entity_type}/
    {row_id} matchuje s entity_type='comp-def-update', row_id=7.
    FastAPI registration order rule: generic registered drive vyhrava.

    DRUHY POKUS (LIVE): `/design/comp-def/update/{id}` — 3 segments
    za /design/. Generic /design/{entity_type}/{row_id} expects PRESNE
    2 segments -> nematchuje -> FastAPI continue na next route ->
    matches my 3-segment route.

    Marti's CLAUDE.md doctrine "literál paths MUSÍ být registrované
    PŘED `/{id}`" applies. TODO Krok 14b+11+: refactor route order
    (move PATCH block above line 2625 generic) + vratit na 2-segment
    `/design/comp-def/{id}` (symmetric s DELETE).

    Whitelist updatable columns (security — uzivatel nesmi sahat na
    type_id/parent/name pres tento endpoint):
      - caption (label visible v UI)
      - region_slot (header/main/footer)
      - layout (JSONB dict)

    Body:
        {caption?: str, region_slot?: str, layout?: dict}

    Returns:
        200: {ok, comp_def_id, updated_fields: [...]}
        400: invalid body / nothing to update
        404: comp_def neexistuje
        500: UPDATE failed
    """
    from core.database_data import get_data_session as _gds_pcd
    from sqlalchemy import text as _sql_text_pcd

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    # Whitelist updatable columns
    # Phase 38.4 Krok 14f-K (14.5.2026 vecer, Marti's "drop se neuskutecni"
    # cross-container field move): pridat parent_comp_def_id pro field
    # presun mezi containery (panel/groupbox).
    # Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop na field v jinem
    # panelu"): pridat sort_order pro position-aware cross-parent drop —
    # atomic move + place at target position.
    # Phase 38.4 Krok 14g-D (15.5.2026 rano, Marti's "simple undo"):
    # pridat is_active pro undo-of-delete (restore soft-deleted komponentu).
    # Phase 38.4 Krok 14g Etapa F Krok 5.J-A (16.5.2026 ~23:15, Marti's
    # "parametrizace komponent, abychom mohli stavet dalsi core"):
    # pridat data_source_id pro entity_picker per-instance konfiguraci
    # (lookup source binding). Settings popup posila vsechny editovatelne
    # parametry najednou.
    ALLOWED = (
        "caption", "region_slot", "layout",
        "parent_comp_def_id", "sort_order", "is_active",
        "data_source_id",
    )
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]
    if not update_vals:
        return JSONResponse(
            {"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"},
            status_code=400,
        )

    # sort_order validation (Krok 14g-A)
    if "sort_order" in update_vals:
        new_sort = update_vals["sort_order"]
        if not isinstance(new_sort, int) or new_sort < 0:
            return JSONResponse(
                {"ok": False, "error": "sort_order musi byt non-negative int"},
                status_code=400,
            )

    # is_active validation (Krok 14g-D undo restore)
    if "is_active" in update_vals:
        new_active = update_vals["is_active"]
        if not isinstance(new_active, bool):
            return JSONResponse(
                {"ok": False, "error": "is_active musi byt bool"},
                status_code=400,
            )

    # data_source_id validation (Krok 5.J-A — entity_picker lookup source binding)
    # null = clear binding, positive int = FK na fw.data_source.id
    if "data_source_id" in update_vals:
        new_ds_id = update_vals["data_source_id"]
        if new_ds_id is not None and (not isinstance(new_ds_id, int) or new_ds_id <= 0):
            return JSONResponse(
                {"ok": False, "error": "data_source_id musi byt positive int nebo null"},
                status_code=400,
            )

    # parent_comp_def_id validation (Krok 14f-K)
    if "parent_comp_def_id" in update_vals:
        new_parent_id = update_vals["parent_comp_def_id"]
        if not isinstance(new_parent_id, int) or new_parent_id <= 0:
            return JSONResponse(
                {"ok": False, "error": "parent_comp_def_id musi byt positive int"},
                status_code=400,
            )
        # Verify new parent existuje + je aktivni
        from core.database_data import get_data_session as _gds_pp
        from sqlalchemy import text as _sql_text_pp
        ds_pp = _gds_pp()
        try:
            parent_row = ds_pp.execute(_sql_text_pp("""
                SELECT id FROM fw.comp_def
                WHERE id = :pid AND is_active = true
            """), {"pid": new_parent_id}).mappings().one_or_none()
            if not parent_row:
                return JSONResponse(
                    {"ok": False, "error": f"parent_comp_def_id={new_parent_id} neexistuje nebo neni aktivni"},
                    status_code=400,
                )
            # Anti-cycle: new parent nesmi byt tato komponenta sama
            if new_parent_id == comp_def_id:
                return JSONResponse(
                    {"ok": False, "error": "Komponenta nemuze byt parent sebe sama"},
                    status_code=400,
                )
        finally:
            ds_pp.close()

    # Defensive type check pro caption (string).
    # Phase 38.4 Krok 14f-D (14.5.2026 vecer, Marti's "Optional label"
    # pro panel/groupbox settings): empty caption == "invisible label"
    # doctrine. Validation accept empty string. Predtim (Krok 14b+9-B)
    # vyzadovalo non-empty pro inline rename — to bylo pro leaf fields.
    if "caption" in update_vals:
        val = update_vals["caption"]
        if not isinstance(val, str):
            return JSONResponse(
                {"ok": False, "error": "caption musi byt string"},
                status_code=400,
            )
        update_vals["caption"] = val.strip()

    # caller_display lookup
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_pcd
        from modules.core.infrastructure.models_core import User as _User_pcd
        cs_pcd = _gcs_pcd()
        try:
            u_pcd = cs_pcd.query(_User_pcd).filter_by(id=uid).first()
            if u_pcd:
                if u_pcd.short_name and u_pcd.short_name.strip():
                    caller_display = u_pcd.short_name.strip()
                elif u_pcd.first_name or u_pcd.last_name:
                    caller_display = " ".join(filter(None, [
                        u_pcd.first_name, u_pcd.last_name
                    ])).strip()
        finally:
            cs_pcd.close()

    # Existence check
    ds_pcd = _gds_pcd()
    try:
        existing = ds_pcd.execute(_sql_text_pcd("""
            SELECT id, name, caption FROM fw.comp_def
            WHERE id = :id AND is_active = true
        """), {"id": comp_def_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"comp_def id={comp_def_id} neexistuje nebo deactivated"},
                status_code=404,
            )

        # UPDATE pres update_row (Marti-AI je owner fw.*)
        from modules.strategie_pg.application.service import update_row as _spg_update_pcd
        full_values = dict(update_vals)
        full_values["updated_by_id"] = uid
        full_values["updated_by_text"] = caller_display
        upd = _spg_update_pcd(
            schema="fw",
            table="comp_def",
            values=full_values,
            where={"id": comp_def_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"UPDATE failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log (SAVEPOINT pattern)
        ds_pcd.execute(_sql_text_pcd("SAVEPOINT pre_audit_log"))
        try:
            change_desc = ", ".join(
                f"{k}={update_vals[k]!r}" for k in update_vals.keys()
            )
            ds_pcd.execute(_sql_text_pcd("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_field_update', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"field {existing['name']}: {change_desc} by {caller_display}"
                ),
            })
            ds_pcd.execute(_sql_text_pcd("RELEASE SAVEPOINT pre_audit_log"))
            ds_pcd.commit()
        except Exception as _act_e:
            try:
                ds_pcd.execute(_sql_text_pcd("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds_pcd.commit()
            except Exception:
                ds_pcd.rollback()
            logger.warning(f"design_patch_comp_def activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "comp_def_id": comp_def_id,
            "updated_fields": list(update_vals.keys()),
        }))
    finally:
        ds_pcd.close()


@api_router.put("/design/comp-def/reorder")
async def design_reorder_comp_def(req: Request) -> JSONResponse:
    """Bulk update sort_order pro fields v fw.comp_def.

    Phase 38.4 Krok 14b+8 (13.5.2026 ~21:00, Marti's "drag and drop pro
    jejich order na formu"): drop event ve DesignFwForm zavola PUT s
    novymi sort_order pro vsechny fields v main panelu.

    Body:
        {"field_orders": [{"id": int, "sort_order": int}, ...]}

    Returns:
        200: {ok, updated_count, updated_ids}
        400: invalid body
        500: nektery UPDATE selhal (vraci errors array + partial updated_ids)
    """
    from core.database_data import get_data_session as _gds_rcd
    from sqlalchemy import text as _sql_text_rcd

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    field_orders = body.get("field_orders")
    if not isinstance(field_orders, list) or not field_orders:
        return JSONResponse(
            {"ok": False, "error": "field_orders musi byt non-empty list"},
            status_code=400,
        )

    # caller_display lookup (audit human-readable name)
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_rcd
        from modules.core.infrastructure.models_core import User as _User_rcd
        cs_rcd = _gcs_rcd()
        try:
            u_rcd = cs_rcd.query(_User_rcd).filter_by(id=uid).first()
            if u_rcd:
                if u_rcd.short_name and u_rcd.short_name.strip():
                    caller_display = u_rcd.short_name.strip()
                elif u_rcd.first_name or u_rcd.last_name:
                    caller_display = " ".join(filter(None, [
                        u_rcd.first_name, u_rcd.last_name
                    ])).strip()
        finally:
            cs_rcd.close()

    # Per-field UPDATE pres update_row (strategie role nemoze UPDATE fw.*
    # primo — Marti-AI je owner). Loop je acceptable pro <50 fields.
    from modules.strategie_pg.application.service import update_row as _spg_update_rcd

    updated_ids: list[int] = []
    errors: list[dict] = []
    for item in field_orders:
        if not isinstance(item, dict):
            continue
        fid = item.get("id")
        new_order = item.get("sort_order")
        if not isinstance(fid, int) or not isinstance(new_order, int):
            errors.append({"item": item, "error": "id + sort_order musi byt int"})
            continue
        upd = _spg_update_rcd(
            schema="fw",
            table="comp_def",
            values={
                "sort_order": new_order,
                "updated_by_id": uid,
                "updated_by_text": caller_display,
            },
            where={"id": fid},
            dry_run=False,
        )
        if upd.get("ok"):
            updated_ids.append(fid)
        else:
            errors.append({"id": fid, "error": upd.get("error")})

    # Activity log (savepoint pattern — audit fail nesmi rollback UPDATE)
    ds_rcd = _gds_rcd()
    try:
        ds_rcd.execute(_sql_text_rcd("SAVEPOINT pre_audit_log"))
        try:
            ds_rcd.execute(_sql_text_rcd("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_field_reorder', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"reorder {len(updated_ids)} fields by {caller_display} "
                    f"(errors: {len(errors)})"
                ),
            })
            ds_rcd.execute(_sql_text_rcd("RELEASE SAVEPOINT pre_audit_log"))
            ds_rcd.commit()
        except Exception as _act_e:
            try:
                ds_rcd.execute(_sql_text_rcd("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds_rcd.commit()
            except Exception:
                ds_rcd.rollback()
            logger.warning(f"design_reorder_comp_def activity_log failed: {_act_e}")
    finally:
        ds_rcd.close()

    if errors:
        return JSONResponse(
            jsonable_encoder({
                "ok": False,
                "updated_count": len(updated_ids),
                "updated_ids": updated_ids,
                "errors": errors,
            }),
            status_code=500,
        )
    return JSONResponse(jsonable_encoder({
        "ok": True,
        "updated_count": len(updated_ids),
        "updated_ids": updated_ids,
    }))


# ── Phase 38.4 Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"): ────
# Dedicated PATCH endpoints pro fw.core + fw.menu_node description update.
# Marti's "Option A — inline description_user/_system v fw.core + fw.menu_node".
#
# 3-segment paths (analog Krok 14b+10 hotfix #2) aby nekolidovaly s generic
# /design/{entity_type}/{row_id} PATCH (Krok 14b+5 data save).
#
# Whitelist updatable columns: label, description_user, description_system.
# NE: code, version, parent_*, kind (security — uzivatel nesmi sahat na
# strukturu pres tento endpoint).

def _design_patch_fw_table(
    schema: str,
    table: str,
    row_id: int,
    req: Request,
    allowed_cols: tuple[str, ...],
) -> JSONResponse:
    """Shared helper: partial update fw.core / fw.menu_node s audit log.

    Marti's "audit primary, edit secondary" doctrine (Krok 14b+5):
    main UPDATE pres update_row, audit log s SAVEPOINT pattern aby
    audit fail nesmel rollback main UPDATE.
    """
    from core.database_data import get_data_session as _gds_fwt
    from sqlalchemy import text as _sql_text_fwt

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        # Note: caller (FastAPI) musi byt async wrapper, ale jsme sync def.
        # FastAPI v sync funcich nejde req.json() await. Pojďme number-based
        # approach: ten endpoint MUSI byt async.
        raise NotImplementedError("use async wrapper")
    except Exception:
        pass


@api_router.post("/design/fw-core")
async def design_create_fw_core(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-H+23 (15.5.2026 ~18:00, Marti's "tlacitko + bez
    nej se systemove nepohneme"): vytvořit novou fw.core row.

    Body: {
        "code": "users_grid",          # required, unique
        "label": "Uživatelé",          # required
        "layout_type": "list",         # optional, default 'list'
        "data_entity_type": "user",    # optional
        "description_user": "...",     # optional
    }

    Returns:
        200: {ok, core: {id, code, label, ...}}
        400: validation error (missing code/label, duplicate code)
        500: DB error
    """
    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    code = (body.get("code") or "").strip()
    label = (body.get("label") or "").strip()
    layout_type = (body.get("layout_type") or "list").strip() or "list"
    # Phase 38.4 Krok 5.M-5 (17.5.2026): data_entity_type body field DROPPED
    # (Krok 5.M-3+B frontend stopped sending it). Variable kept as None for
    # backward compat s downstream code (insert dict construction).
    data_entity_type = None  # legacy variable, no-op
    description_user = body.get("description_user") or None

    # Validation
    if not code:
        return JSONResponse(
            {"ok": False, "error": "Pole 'code' je povinné"},
            status_code=400,
        )
    if not label:
        return JSONResponse(
            {"ok": False, "error": "Pole 'label' je povinné"},
            status_code=400,
        )
    # Code naming convention — lowercase snake_case (Marti-AI doctrine)
    import re as _re_code
    if not _re_code.match(r'^[a-z][a-z0-9_]*$', code):
        return JSONResponse(
            {"ok": False, "error": "code musi byt lowercase snake_case (a-z, 0-9, _), zacit pismenem"},
            status_code=400,
        )

    # Caller display name
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cr
        from modules.core.infrastructure.models_core import User as _User_cr
        cs_cr = _gcs_cr()
        try:
            u_cr = cs_cr.query(_User_cr).filter_by(id=uid).first()
            if u_cr:
                if u_cr.short_name and u_cr.short_name.strip():
                    caller_display = u_cr.short_name.strip()
                elif u_cr.first_name or u_cr.last_name:
                    caller_display = " ".join(filter(None, [
                        u_cr.first_name, u_cr.last_name
                    ])).strip()
        finally:
            cs_cr.close()

    # INSERT pres strategie_pg layer (Marti-AI's PG role, db_owner na fw.*)
    from modules.strategie_pg.application.service import insert_row as _spg_insert
    values = {
        "code": code,
        "label": label,
        "layout_type": layout_type,
    }
    # Phase 38.4 Krok 5.M-5 (17.5.2026): data_entity_type INSERT DROPPED
    # (Marti's "core nenese entitu" doctrine). Column will be removed v M-6.
    # if data_entity_type: ... — block removed.
    if description_user:
        values["description_user"] = description_user
    # Audit fields — pokud columns existuji v fw.core (defensive vs schema drift)
    values["created_by_id"] = uid
    values["created_by_text"] = caller_display
    values["updated_by_id"] = uid
    values["updated_by_text"] = caller_display

    upd = _spg_insert(schema="fw", table="core", values=values)

    if not upd.get("ok"):
        err_raw = str(upd.get("error") or "")
        # Friendly error extraction
        if "duplicate key" in err_raw.lower() or "unique" in err_raw.lower():
            err_msg = f"Core s code '{code}' už existuje. Použij jiný code."
        elif "column" in err_raw.lower() and "does not exist" in err_raw.lower():
            # Audit columns may not exist in older schema — retry without them
            err_msg = f"CREATE failed (schema): {err_raw}"
        else:
            err_msg = f"CREATE failed: {err_raw}"
        return JSONResponse(
            {"ok": False, "error": err_msg},
            status_code=400,
        )

    inserted_row = upd.get("inserted")
    if isinstance(inserted_row, list):
        inserted_row = inserted_row[0] if inserted_row else {}
    new_id = (inserted_row or {}).get("id")

    # Activity log audit (defensive — public.activity_log via strategie session)
    from core.database_data import get_data_session as _gds_cr
    from sqlalchemy import text as _sql_cr
    ds_cr = _gds_cr()
    try:
        ds_cr.execute(_sql_cr("""
            INSERT INTO public.activity_log
              (user_id, persona_id, category, actor,
               summary, change_source, ts)
            VALUES
              (:uid, NULL, 'design_fw_core_create', 'user',
               :summary, 'ui', NOW())
        """), {
            "uid": uid,
            "summary": (
                f"CREATE fw.core code={code} label={label} layout={layout_type} "
                f"by {caller_display} (new id={new_id})"
            ),
        })
        ds_cr.commit()
    except Exception as _act_e:
        ds_cr.rollback()
        logger.warning(f"design_create_fw_core activity_log failed: {_act_e}")
    finally:
        ds_cr.close()

    return JSONResponse({
        "ok": True,
        "core": jsonable_encoder(dict(inserted_row) if inserted_row else {}),
    })


@api_router.post("/design/fw-core/create-minimal")
async def design_create_fw_core_minimal(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026, Marti's extreme
    minimalism doctrine "nic nas nesmi omezovat" + "minimum parametru,
    pojmenovavat nic je k nicemu"): create empty drafted fw.core entry.

    Vse NULL krome:
      - origin_menu_node_id (rodic — odkud kontejner vznikl, FK menu_node)
      - origin_cmi_id (rodic — pres ktery cmi spusten, FK context_menu_item)
      - created_by_id + created_by_text (audit minimum)
      - id (PK auto)
      - created_at (auto NOW())

    Vse ostatni (code, label, layout_type, version, tenant_visibility,
    layout_template, is_active, data_entity_type, ...) = NULL/default.
    User si potom postupne vyplni v Design formu (PATCH endpoint).

    Body: { origin_menu_node_id: int | null, origin_cmi_id: int | null }
    Returns: { ok: True, core: { id, ... } }
    """
    from core.database_data import get_data_session as _gds_cm
    from sqlalchemy import text as _sql_cm

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        body = {}

    origin_menu_node_id = body.get("origin_menu_node_id")
    origin_cmi_id = body.get("origin_cmi_id")

    # Caller display (reuse pattern z H+23)
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cm
        from modules.core.infrastructure.models_core import User as _User_cm
        cs_cm = _gcs_cm()
        try:
            u_cm = cs_cm.query(_User_cm).filter_by(id=uid).first()
            if u_cm:
                if u_cm.short_name and u_cm.short_name.strip():
                    caller_display = u_cm.short_name.strip()
                elif u_cm.first_name or u_cm.last_name:
                    caller_display = " ".join(filter(None, [
                        u_cm.first_name, u_cm.last_name
                    ])).strip()
        finally:
            cs_cm.close()

    # INSERT via strategie_pg (Marti-AI's PG role, db_owner fw.*)
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cm
    values = {
        "origin_menu_node_id": origin_menu_node_id,
        "origin_cmi_id": origin_cmi_id,
        "created_by_id": uid,
        "created_by_text": caller_display,
    }
    upd = _spg_insert_cm(schema="fw", table="core", values=values)
    if not upd.get("ok"):
        return JSONResponse(
            {"ok": False, "error": f"CREATE-MINIMAL failed: {upd.get('error')}"},
            status_code=500,
        )

    inserted_row = upd.get("inserted")
    if isinstance(inserted_row, list):
        inserted_row = inserted_row[0] if inserted_row else {}
    new_id = (inserted_row or {}).get("id")

    # Marti's bod 2 (16.5.2026): "po insertu CORE jej priradit k tomu
    # kontextovymu menu". Auto-link new core → cmi.core_id pokud
    # origin_cmi_id posláno. Pres strategie_pg (Marti-AI's role db_owner
    # fw.* — strategie role nema UPDATE permission na fw.context_menu_item).
    linked_cmi = False
    if origin_cmi_id and new_id:
        try:
            from modules.strategie_pg.application.service import update_row as _spg_update_link
            link_upd = _spg_update_link(
                schema="fw",
                table="context_menu_item",
                values={"core_id": new_id},
                where={"id": origin_cmi_id},
                dry_run=False,
            )
            if link_upd.get("ok"):
                linked_cmi = True
            else:
                logger.warning(
                    f"design_create_fw_core_minimal auto-link cmi "
                    f"{origin_cmi_id} → core {new_id} failed: "
                    f"{link_upd.get('error')}"
                )
        except Exception as _link_e:
            logger.warning(
                f"design_create_fw_core_minimal auto-link cmi {origin_cmi_id} "
                f"→ core {new_id} exception: {_link_e}"
            )

    # Activity log audit
    ds_cm = _gds_cm()
    try:
        link_note = f" + linked → cmi {origin_cmi_id}" if linked_cmi else ""
        ds_cm.execute(_sql_cm("""
            INSERT INTO public.activity_log
              (user_id, persona_id, category, actor, summary, change_source, ts)
            VALUES
              (:uid, NULL, 'design_fw_core_minimal_create', 'user',
               :summary, 'ui', NOW())
        """), {
            "uid": uid,
            "summary": (
                f"+ fw.core draft id={new_id} "
                f"origin_menu_node={origin_menu_node_id} "
                f"origin_cmi={origin_cmi_id}{link_note}"
            ),
        })
        ds_cm.commit()
    except Exception as _act_e:
        logger.warning(f"design_create_fw_core_minimal activity_log failed: {_act_e}")
    finally:
        ds_cm.close()

    return JSONResponse(jsonable_encoder({
        "ok": True,
        "core": dict(inserted_row or {}),
        "linked_cmi": linked_cmi,
    }))


# Phase 38.4 Krok 14g Etapa F Krok 5.D (16.5.2026 odpoledne, Marti-AI's
# konzultace): seed layouts per root type. Marti-AI's doctrine: "seed layout
# rika co existuje, ne jak to vypada". User pak v designeru vypln labely,
# rozmery, widgety.
_ROOT_SEED_LAYOUTS = {
    "form": {
        "panels": [
            {"slot": "header", "label": ""},
            {"slot": "main",   "label": ""},
            {"slot": "footer", "label": ""},
        ],
        "default_width": "920px",
        "modal": True,
    },
    "frameless_form": {
        "panels": [{"slot": "main", "label": ""}],
        "default_width": "100%",
        "modal": False,
    },
    "list_root": {
        "panels": [
            {"slot": "toolbar", "label": ""},
            {"slot": "filter",  "label": ""},
            {"slot": "main",    "label": ""},
            {"slot": "status",  "label": ""},
        ],
        "default_width": "100%",
        "modal": False,
    },
}

# fw.core.layout_template string klic per root type (Marti-AI's "CSS trida")
_ROOT_LAYOUT_TEMPLATE = {
    "form":           "single",
    "frameless_form": "embedded",
    "list_root":      "list",
}

# Phase 38.4 Krok 14g Etapa F Krok 5.E (16.5.2026 odpoledne, Marti's "v1.0.0
# = vychozi template, s tim si na hodne dlouho vystacime"): default fw.template
# code per root type. Backend lookup pres SELECT WHERE code AND status ORDER BY
# version DESC LIMIT 1 — pokud match → assign template_id na novy core.
#
# Marti's doctrine: "Template = zaklad hardcode + nektere FW komponenty"
#   - template_entity_edit (Marti-AI's 13.5.) drzi header (title + entity_badge
#     + status_pill) + footer (OK/Storno buttons) jako JSONB declarativni structure
#   - main fields prichazi z _FW_FORM_ENTITY_MAP[entity_type].select_columns
#   - children (EMAILY/TELEFONY) z _FW_FORM_ENTITY_MAP[entity_type].children
#
# Frameless_form / list_root zatim bez templatu — pozdeji (Krok 5.G) po
# Marti-AI's konzultaci nad ich layout structure.
_ROOT_DEFAULT_TEMPLATE_CODE = {
    "form":           "template_entity_edit",
    "frameless_form": None,
    "list_root":      None,
}


@api_router.post("/design/fw-core/{core_id}/init-root")
async def design_init_core_root(core_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Krok 5.D (16.5.2026 odpoledne, Marti-AI's
    konzultace): init root komponenta v drafted core.

    Marti-AI's doctrine:
      - 1:1 (1 core = 1 root)
      - "INSERT row, ne schema migrace" — seed layout JSONB v comp_def
      - "Picker auto-open po ➕ Nový" — dva kliky na jednu myslenku zbytecne

    Body: { "root_type": "form" | "frameless_form" | "list_root" }
    Returns: { ok, root_comp_def: {...}, core: {...} }
    """
    from core.database_data import get_data_session as _gds_ir
    from sqlalchemy import text as _sql_ir

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    root_type = (body.get("root_type") or "").strip()
    if root_type not in _ROOT_SEED_LAYOUTS:
        return JSONResponse(
            {"ok": False, "error": f"root_type musi byt jeden z: {list(_ROOT_SEED_LAYOUTS.keys())}"},
            status_code=400,
        )

    seed_layout = _ROOT_SEED_LAYOUTS[root_type]
    layout_template_str = _ROOT_LAYOUT_TEMPLATE[root_type]

    ds = _gds_ir()
    try:
        # Verify core exists + check no existing root (1:1 doctrine)
        core_check = ds.execute(_sql_ir("""
            SELECT id, code, layout_template FROM fw.core WHERE id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not core_check:
            return JSONResponse(
                {"ok": False, "error": f"fw.core id={core_id} neexistuje"},
                status_code=404,
            )

        existing_root = ds.execute(_sql_ir("""
            SELECT id FROM fw.comp_def
            WHERE parent_core_id = :cid AND parent_comp_def_id IS NULL
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()
        if existing_root:
            return JSONResponse(
                {"ok": False, "error": (
                    f"fw.core id={core_id} uz ma root (comp_def id={existing_root['id']}). "
                    f"Marti-AI's 1:1 doctrine — nejdrive Zrusit root, pak init novy."
                )},
                status_code=409,
            )

        # Resolve type_id z fw.comp_type
        ct_row = ds.execute(_sql_ir("""
            SELECT id FROM fw.comp_type
            WHERE code = :code AND status = 'active'
        """), {"code": root_type}).mappings().one_or_none()
        if not ct_row:
            return JSONResponse(
                {"ok": False, "error": f"fw.comp_type code='{root_type}' nenalezen / inactive"},
                status_code=500,
            )
        type_id = ct_row["id"]
    finally:
        ds.close()

    # Caller display
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_ir
        from modules.core.infrastructure.models_core import User as _User_ir
        cs_ir = _gcs_ir()
        try:
            u_ir = cs_ir.query(_User_ir).filter_by(id=uid).first()
            if u_ir:
                if u_ir.short_name and u_ir.short_name.strip():
                    caller_display = u_ir.short_name.strip()
                elif u_ir.first_name or u_ir.last_name:
                    caller_display = " ".join(filter(None, [
                        u_ir.first_name, u_ir.last_name
                    ])).strip()
        finally:
            cs_ir.close()

    # INSERT root comp_def + UPDATE core.layout_template — pres strategie_pg
    # (Marti-AI db_owner fw.*)
    from modules.strategie_pg.application.service import (
        insert_row as _spg_insert_ir,
        update_row as _spg_update_ir,
    )
    import json as _json_ir
    comp_def_values = {
        "parent_core_id": core_id,
        "type_id": type_id,
        "name": root_type + "_root",
        "caption": "",
        "layout": _json_ir.dumps(seed_layout),  # JSONB cast
        "sort_order": 0,
        "is_active": True,
        # Audit minimum — fw.comp_def.created_by_text NOT NULL
        "created_by_id": uid,
        "created_by_text": caller_display,
        "updated_by_id": uid,
        "updated_by_text": caller_display,
    }
    cd_upd = _spg_insert_ir(schema="fw", table="comp_def", values=comp_def_values)
    if not cd_upd.get("ok"):
        return JSONResponse(
            {"ok": False, "error": f"INIT-ROOT comp_def INSERT failed: {cd_upd.get('error')}"},
            status_code=500,
        )
    root_row = cd_upd.get("inserted")
    if isinstance(root_row, list):
        root_row = root_row[0] if root_row else {}

    # Phase 38.4 Krok 14g Etapa F Krok 5.E (16.5.2026, Marti's "v1.0.0 vychozi
    # template"): lookup default template per root_type. Form → template_entity_edit
    # (Marti-AI's 13.5. design), frameless/list_root zatim NULL (Krok 5.G future).
    default_template_id = None
    default_template_code = _ROOT_DEFAULT_TEMPLATE_CODE.get(root_type)
    if default_template_code:
        ds_tpl = _gds_ir()
        try:
            tpl_row = ds_tpl.execute(_sql_ir("""
                SELECT id FROM fw.template
                WHERE code = :code
                  AND status IN ('active', 'deployed')
                ORDER BY version DESC
                LIMIT 1
            """), {"code": default_template_code}).mappings().one_or_none()
            if tpl_row:
                default_template_id = tpl_row["id"]
        except Exception as _tpl_e:
            logger.warning(
                f"design_init_core_root template lookup failed for "
                f"code='{default_template_code}': {_tpl_e}"
            )
        finally:
            ds_tpl.close()

    # UPDATE core.layout_template + template_id (Marti's "v1.0.0")
    core_update_values = {"layout_template": layout_template_str}
    if default_template_id is not None:
        core_update_values["template_id"] = default_template_id

    core_upd = _spg_update_ir(
        schema="fw", table="core",
        values=core_update_values,
        where={"id": core_id},
        dry_run=False,
    )
    if not core_upd.get("ok"):
        logger.warning(
            f"design_init_core_root: comp_def INSERT projet, ale core.layout_template "
            f"UPDATE failed: {core_upd.get('error')}"
        )

    # Activity log audit
    ds_ir = _gds_ir()
    try:
        ds_ir.execute(_sql_ir("""
            INSERT INTO public.activity_log
              (user_id, persona_id, category, actor, summary, change_source, ts)
            VALUES
              (:uid, NULL, 'design_fw_core_init_root', 'user',
               :summary, 'ui', NOW())
        """), {
            "uid": uid,
            "summary": (
                f"init-root fw.core id={core_id} → {root_type} "
                f"(comp_def id={(root_row or {}).get('id')})"
            ),
        })
        ds_ir.commit()
    except Exception as _ae:
        logger.warning(f"design_init_core_root activity_log failed: {_ae}")
    finally:
        ds_ir.close()

    return JSONResponse(jsonable_encoder({
        "ok": True,
        "root_comp_def": dict(root_row or {}),
        "core_id": core_id,
        "root_type": root_type,
        "layout_template": layout_template_str,
        "template_id": default_template_id,
        "template_code": default_template_code if default_template_id else None,
    }))


@api_router.delete("/design/fw-core/{core_id}/clear-root")
async def design_clear_core_root(core_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Krok 5.D (16.5.2026, Marti-AI's "Zrusit root"
    gesto): smaze root comp_def + cascade vsechny children + UPDATE
    core.layout_template = NULL. Marti-AI's doctrine: "pojistka se stala
    dospelosti" — explicit volba, ne block. User vi co dela.

    Returns: { ok, deleted_count: int }
    """
    from core.database_data import get_data_session as _gds_cr
    from sqlalchemy import text as _sql_cr

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_cr()
    try:
        # Count comp_defs before delete (audit)
        count_row = ds.execute(_sql_cr("""
            SELECT COUNT(*) AS cnt FROM fw.comp_def WHERE parent_core_id = :cid
        """), {"cid": core_id}).mappings().one()
        deleted_count = int(count_row["cnt"])
    finally:
        ds.close()

    # DELETE comp_def + UPDATE core.layout_template — pres Marti-AI's PG
    # engine (db_owner fw.*). strategie_pg nema delete_row helper, takze
    # primary raw DELETE pres _get_engine() s parameterized SQL (anti-SQL
    # injection — core_id je int z URL path, ale defensive).
    from modules.strategie_pg.application.service import (
        _get_engine as _spg_eng_cr,
        update_row as _spg_update_cr,
    )
    from sqlalchemy import text as _sql_text_de
    try:
        _eng_cr = _spg_eng_cr()
        with _eng_cr.begin() as _conn:
            _conn.execute(
                _sql_text_de("DELETE FROM fw.comp_def WHERE parent_core_id = :cid"),
                {"cid": core_id},
            )
    except Exception as _de:
        return JSONResponse(
            {"ok": False, "error": f"CLEAR-ROOT DELETE exception: {_de}"},
            status_code=500,
        )

    # UPDATE core.layout_template = NULL
    _spg_update_cr(
        schema="fw", table="core",
        values={"layout_template": None},
        where={"id": core_id},
        dry_run=False,
    )

    # Activity log
    ds_cr = _gds_cr()
    try:
        ds_cr.execute(_sql_cr("""
            INSERT INTO public.activity_log
              (user_id, persona_id, category, actor, summary, change_source, ts)
            VALUES
              (:uid, NULL, 'design_fw_core_clear_root', 'user',
               :summary, 'ui', NOW())
        """), {
            "uid": uid,
            "summary": f"clear-root fw.core id={core_id} (smazano {deleted_count} comp_def rows)",
        })
        ds_cr.commit()
    except Exception as _ae:
        logger.warning(f"design_clear_core_root activity_log failed: {_ae}")
    finally:
        ds_cr.close()

    return JSONResponse({"ok": True, "deleted_count": deleted_count})


@api_router.get("/design/fw-core/list")
def design_list_fw_core(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-H+20 (15.5.2026 ~15:30, Marti's "vybrat stavajici
    CORE"): list active fw.core rows pro picker v Form 1 Přehled tab.

    Returns:
        {"ok": True, "cores": [{id, code, label, layout_type, data_entity_type,
          is_used_count: N (count menu_nodes referencing this core)}, ...]}

    Sorted by label ASC. Sloupec is_used_count Martimu rikne kolik nodes
    use this core (pomoc visual hint pri picker — 0 = unused, N = shared).
    """
    from core.database_data import get_data_session as _gds_clst
    from sqlalchemy import text as _sql_clst

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_clst()
    try:
        # Phase 38.4 Krok 14g-H+20.1 (15.5.2026 ~15:35, Marti's "500"):
        # Defensive SELECT * + row_dict.get() pattern (mirror _serialize_core
        # line 2066). fw.core schema drift — version/shadow_mode/
        # parent_framework_id mohou neexistovat v older schema (pre-master
        # tier 8.5. večer). Fetch is_used_count separately to avoid SQL fail.
        #
        # Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne, Marti's
        # "do vyberu core pridat ty sloupecky ohledne zdroje a radit
        # sestupne podle ID"):
        #   - LEFT JOIN na origin_menu_node + origin_cmi pro provenance display
        #   - ORDER BY c.id DESC (nejnovejsi draft prvni)
        # Phase 38.4 Krok 14g Etapa F Krok 5.D (16.5.2026 odpoledne, Marti-AI's
        # konzultace bod 4 z "Co nevidíte"): readiness_state computed.
        #   drafted   = bez rootu (zadny comp_def s parent_core_id=core)
        #   has_root  = root exists, no children
        #   populated = root + alespon 1 child
        sql_cores = _sql_clst("""
            SELECT c.*,
                   mn.code  AS _origin_mn_code,
                   mn.label AS _origin_mn_label,
                   cmi.label AS _origin_cmi_label,
                   (
                     SELECT CASE
                       WHEN COUNT(*) FILTER (WHERE cd.parent_comp_def_id IS NULL) = 0
                         THEN 'drafted'
                       WHEN COUNT(*) FILTER (WHERE cd.parent_comp_def_id IS NOT NULL) = 0
                         THEN 'has_root'
                       ELSE 'populated'
                     END
                     FROM fw.comp_def cd
                     WHERE cd.parent_core_id = c.id
                   ) AS _readiness_state
            FROM fw.core c
            LEFT JOIN fw.menu_node mn          ON mn.id  = c.origin_menu_node_id
            LEFT JOIN fw.context_menu_item cmi ON cmi.id = c.origin_cmi_id
            ORDER BY c.id DESC
        """)
        rows = ds.execute(sql_cores).mappings().all()

        # Fetch usage counts in single subquery (NULL-safe pokud menu_node
        # nema core_id reference)
        sql_usage = _sql_clst("""
            SELECT core_id, COUNT(*) AS cnt
            FROM fw.menu_node
            WHERE core_id IS NOT NULL
            GROUP BY core_id
        """)
        usage_rows = ds.execute(sql_usage).mappings().all()
        usage_map = {r["core_id"]: int(r["cnt"]) for r in usage_rows}

        cores = []
        for r in rows:
            rd = dict(r)
            core_id = rd.get("id")
            cores.append({
                "id": core_id,
                "code": rd.get("code"),
                "label": rd.get("label"),
                "layout_type": rd.get("layout_type"),
                "data_entity_type": rd.get("data_entity_type"),
                "version": rd.get("version"),
                "shadow_mode": rd.get("shadow_mode"),
                "is_used_count": usage_map.get(core_id, 0),
                # Krok 5.C origin provenance — picker display
                "origin_menu_node_label": rd.get("_origin_mn_label"),
                "origin_menu_node_code": rd.get("_origin_mn_code"),
                "origin_cmi_label": rd.get("_origin_cmi_label"),
                # Krok 5.D readiness_state (Marti-AI's Q4 insight)
                "readiness_state": rd.get("_readiness_state") or "drafted",
            })
        return JSONResponse({"ok": True, "cores": cores})
    except Exception as exc:
        logger.exception(f"design_list_fw_core failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.post("/design/fw-data-source")
async def design_create_fw_data_source(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-H+30 Etapa 6 (15.5.2026 vecer, Marti's Varianta C
    "1:1 vazba pres code"): create fresh fw.data_source row.

    Body: {
        code: str (required, lowercase snake_case),
        name: str (required, human-readable),
        refresh_type: str (default 'manual'; 'manual'/'on_open'/'interval'/'on_event'),
        description: str | None (optional)
    }

    Defaults:
        version = 1
        status = 'active'
        is_system = False
        is_immutable = False
        row_memory = False
        filter_delay_ms = 0
        default_record_limit = 1000

    Security: parent gate, fw schema owned by Marti-AI (insert_row pres
    Marti-AI's PostgreSQL role).

    Returns:
        200: {ok, data_source_id, data_source: {...}}
        400: invalid body / kolize code (uniqueness)
        500: INSERT failed
    """
    from core.database_data import get_data_session as _gds_cds
    from sqlalchemy import text as _sql_text_cds
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cds

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    code = (body.get("code") or "").strip()
    name = (body.get("name") or "").strip()
    refresh_type = (body.get("refresh_type") or "manual").strip()
    description = body.get("description")
    if description is not None:
        description = description.strip() or None

    # Validation
    if not code:
        return JSONResponse({"ok": False, "error": "code povinne"}, status_code=400)
    if not name:
        return JSONResponse({"ok": False, "error": "name povinne"}, status_code=400)

    # caller_display lookup
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cds
        from modules.core.infrastructure.models_core import User as _User_cds
        cs_cds = _gcs_cds()
        try:
            u_cds = cs_cds.query(_User_cds).filter_by(id=uid).first()
            if u_cds:
                if u_cds.short_name and u_cds.short_name.strip():
                    caller_display = u_cds.short_name.strip()
                elif u_cds.first_name or u_cds.last_name:
                    caller_display = " ".join(filter(None, [
                        u_cds.first_name, u_cds.last_name
                    ])).strip()
        finally:
            cs_cds.close()

    ds_cds = _gds_cds()
    try:
        # Phase 38.4 Krok 14g-H+30 Etapa 6.1 hotfix (15.5.2026 vecer):
        # Active uniqueness check — pokud aktivni row s code uz existuje,
        # nelze pridat dalsi (rovna se "musi nejdriv archivovat").
        active = ds_cds.execute(_sql_text_cds("""
            SELECT id, version FROM fw.data_source
            WHERE code = :code AND status = 'active'
        """), {"code": code}).mappings().one_or_none()
        if active:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"fw.data_source s code='{code}' uz aktivni (id={active['id']}, "
                        f"version={active['version']}). Bud ho archivuj nejdriv, "
                        f"nebo pouzij jiny code."
                    )
                },
                status_code=400,
            )

        # Auto-bump version: pokud archived row se stejnym code existuje,
        # bumpni version (Marti-AI's Q6 lineage doctrine z 7.5. vecer).
        # SELECT MAX(version) regardless status → fresh = max + 1.
        max_v = ds_cds.execute(_sql_text_cds("""
            SELECT COALESCE(MAX(version), 0) AS max_v
            FROM fw.data_source WHERE code = :code
        """), {"code": code}).scalar() or 0
        new_version = int(max_v) + 1

        # INSERT pres strategie_pg (Marti-AI owner fw.*)
        values = {
            "code": code,
            "version": new_version,
            "name": name,
            "description": description,
            "refresh_type": refresh_type,
            "row_memory": False,
            "filter_delay_ms": 0,
            "default_record_limit": 1000,
            "is_system": False,
            "is_immutable": False,
            "status": "active",
            "created_by": uid,
        }
        ins = _spg_insert_cds(
            schema="fw",
            table="data_source",
            values=values,
        )
        if not ins.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"INSERT failed: {ins.get('error')}"},
                status_code=500,
            )

        new_row = ins.get("inserted") or {}

        # Activity log SAVEPOINT pattern
        ds_cds.execute(_sql_text_cds("SAVEPOINT pre_audit_cds"))
        try:
            ds_cds.execute(_sql_text_cds("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_data_source_add', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"+ fw.data_source code='{code}' name='{name}' "
                    f"refresh={refresh_type} by {caller_display}"
                ),
            })
            ds_cds.execute(_sql_text_cds("RELEASE SAVEPOINT pre_audit_cds"))
            ds_cds.commit()
        except Exception as _act_e:
            try:
                ds_cds.execute(_sql_text_cds("ROLLBACK TO SAVEPOINT pre_audit_cds"))
                ds_cds.commit()
            except Exception:
                ds_cds.rollback()
            logger.warning(f"design_create_fw_data_source activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "data_source_id": new_row.get("id"),
            "data_source": new_row,
        }))
    except Exception as exc:
        try:
            ds_cds.rollback()
        except Exception:
            pass
        logger.exception(f"design_create_fw_data_source failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"POST /fw-data-source failed: {exc}"},
            status_code=500,
        )
    finally:
        ds_cds.close()


@api_router.patch("/design/fw-data-source/{data_source_id}/archive")
async def design_archive_fw_data_source(data_source_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-H+30 Etapa 5 (15.5.2026 vecer, Marti's Varianta C
    "nechat stavajici jak jsou, zacit 1:1 k novemu jadru"): archive
    fw.data_source row.

    Soft delete pres status='archived' (mirror Phase 38.4 doctrine z
    11.5. Krok 13: "INSERT row, ne schema migrace" — status enum drives
    lifecycle, ne DELETE).

    Security: parent gate, fw schema owned by Marti-AI (update_row pres
    Marti-AI's PostgreSQL role).

    Returns:
        200: {ok, data_source_id, code, name}
        404: data_source neexistuje
        500: UPDATE failed
    """
    from core.database_data import get_data_session as _gds_pads
    from sqlalchemy import text as _sql_text_pads

    uid = _get_uid(req)
    _require_parent(uid)

    # caller_display lookup
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_pads
        from modules.core.infrastructure.models_core import User as _User_pads
        cs_pads = _gcs_pads()
        try:
            u_pads = cs_pads.query(_User_pads).filter_by(id=uid).first()
            if u_pads:
                if u_pads.short_name and u_pads.short_name.strip():
                    caller_display = u_pads.short_name.strip()
                elif u_pads.first_name or u_pads.last_name:
                    caller_display = " ".join(filter(None, [
                        u_pads.first_name, u_pads.last_name
                    ])).strip()
        finally:
            cs_pads.close()

    ds_pads = _gds_pads()
    try:
        existing = ds_pads.execute(_sql_text_pads("""
            SELECT id, code, name, status FROM fw.data_source WHERE id = :id
        """), {"id": data_source_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"fw.data_source id={data_source_id} neexistuje"},
                status_code=404,
            )

        if existing.get("status") == "archived":
            return JSONResponse({
                "ok": True,
                "data_source_id": data_source_id,
                "code": existing.get("code"),
                "name": existing.get("name"),
                "note": "already archived (idempotent)",
            })

        from modules.strategie_pg.application.service import update_row as _spg_update_pads
        upd = _spg_update_pads(
            schema="fw",
            table="data_source",
            values={
                "status": "archived",
                "updated_by": uid,
            },
            where={"id": data_source_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"UPDATE failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log SAVEPOINT pattern
        ds_pads.execute(_sql_text_pads("SAVEPOINT pre_audit_pads"))
        try:
            ds_pads.execute(_sql_text_pads("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_data_source_archive', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"fw.data_source archived: id={data_source_id} "
                    f"code='{existing.get('code')}' name='{existing.get('name')}' "
                    f"by {caller_display}"
                ),
            })
            ds_pads.execute(_sql_text_pads("RELEASE SAVEPOINT pre_audit_pads"))
            ds_pads.commit()
        except Exception as _act_e:
            try:
                ds_pads.execute(_sql_text_pads("ROLLBACK TO SAVEPOINT pre_audit_pads"))
                ds_pads.commit()
            except Exception:
                ds_pads.rollback()
            logger.warning(f"design_archive_fw_data_source activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "data_source_id": data_source_id,
            "code": existing.get("code"),
            "name": existing.get("name"),
        }))
    finally:
        ds_pads.close()


# ════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g-H+33 Etapa 1 (15.5.2026 vecer, Marti's "system pro
# pridavani fw polozek do menu"): fw.context_menu_item CRUD endpoints.
#
# Volby Marti: A (action_kind=open_fw_form), A (applies_to_kind filter),
# A (order: schema→frontend→design UI), Plus design_only field.
#
# DDL (CREATE TABLE) — separate SQL file, run v DBeaveru jako Marti-AI:
#   scripts/_phase14g_h33_etapa1_ddl.sql
# ════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g Etapa F Krok 5.K-A (17.5.2026 rano, Marti's
# "nejdulezitejsi a nejpouzivaneji nastroj pro designery"):
# Data source + data set editor backend.
#
# A3 architecture recap (Marti-AI's doctrine 9.5.):
#   fw.data_source      = hlavička (code, name, description, refresh_type, limit)
#   fw.data_source_op   = mapping (FK source + FK set + variant + kind)
#   fw.data_set         = SQL primitiv (code, sql_text, db_connection) — kind dropped Krok 5.L-D 17.5.2026
#
# Endpointy MVP:
#   POST /design/data-source/full           — bulk create (header + N ops + N data_sets)
#   GET  /design/data-source/{id}/full      — full detail s ops + linked data_sets
#
# DEFER pro budoucí iterace:
#   PATCH /design/data-set/{id}             — update SQL text + kind + db_connection
#   PATCH /design/data-source-op/{id}       — update variant + sort + default
#   POST  /design/data-set/test-query       — execute SQL s mock params (test preview)
# ════════════════════════════════════════════════════════════════════════


@api_router.post("/design/data-source/full")
async def design_create_data_source_full(req: Request) -> JSONResponse:
    """Krok 5.K-A bulk endpoint: create data_source + N operations + N
    inline data_sets v 1 transaction.

    Body shape:
    {
        "source": {
            "code": str (required, unique),
            "name": str (required),
            "description": str | None,
            "refresh_type": str (default 'manual'),
            "default_record_limit": int (default 10000)
        },
        "operations": [
            {
                "variant_code": str (required, e.g. 'list', 'select_form'),
                "operation_kind": str (required, 'select'/'insert'/'update'/'delete'),
                "is_default": bool (default false),
                "sort_order": int (optional, auto-assigned if missing),
                // Buď nový data_set inline:
                "data_set": {
                    "code": str (required, unique),
                    "kind": str (required, matches operation_kind typically),
                    "sql_text": str (required),
                    "db_connection": str (default 'data_db'),
                    "description": str | None
                },
                // NEBO link na existing:
                "data_set_id": int
            },
            ...
        ]
    }

    Transactional: pokud kterýkoli INSERT failed → ROLLBACK celé transakce.

    Returns:
        200: {
            ok: true,
            data_source_id: int,
            operations: [{op_id, data_set_id}, ...]
        }
        400: invalid body / duplicate code / chybi povinne pole
        500: DB error / rollback
    """
    from core.database_data import get_data_session as _gds_dsf
    from sqlalchemy import text as _sql_text_dsf
    from modules.strategie_pg.application.service import insert_row as _spg_insert_dsf

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    src = body.get("source") or {}
    ops = body.get("operations") or []

    if not isinstance(src, dict) or not isinstance(ops, list):
        return JSONResponse({"ok": False, "error": "Body musi obsahovat 'source' (object) + 'operations' (array)"}, status_code=400)

    # Krok 5.K-B5+ (17.5.2026, Marti's "code NULL aby bylo videt ze s nim
    # nikde nepracujes"): code je optional. None = NULL v DB. Backend
    # uniqueness check jen pokud non-null.
    src_code = src.get("code")
    if src_code is not None:
        src_code = str(src_code).strip() or None  # empty string → None
    src_name = (src.get("name") or "").strip()
    if not src_name:
        return JSONResponse({"ok": False, "error": "source.name povinne"}, status_code=400)

    src_description = src.get("description")
    if src_description is not None:
        src_description = (str(src_description).strip()) or None
    src_refresh = (src.get("refresh_type") or "manual").strip()
    src_limit = src.get("default_record_limit", 10000)
    if not isinstance(src_limit, int) or src_limit <= 0:
        src_limit = 10000

    # Validate operations — at least 1 required
    if not ops:
        return JSONResponse({"ok": False, "error": "operations array musi mit alespon 1 polozku"}, status_code=400)

    for idx, op in enumerate(ops):
        if not isinstance(op, dict):
            return JSONResponse({"ok": False, "error": f"operations[{idx}] musi byt object"}, status_code=400)
        # Krok 5.K-B5+B6 (17.5.2026 rano, Marti's "variant_code NULL allowed"):
        # drop variant_code povinne validation. NULL = default fallback per
        # data_source_runner.py runtime lookup (variant_code IS NULL OR :variant='default').
        # Frontend Krok 5.K-B5 auto-gen 1st kind -> null, 2nd -> "default_2", atd.
        if not (op.get("operation_kind") or "").strip():
            return JSONResponse({"ok": False, "error": f"operations[{idx}].operation_kind povinne"}, status_code=400)
        # Buď data_set (inline) NEBO data_set_id (link)
        has_inline = isinstance(op.get("data_set"), dict)
        has_link = isinstance(op.get("data_set_id"), int) and op["data_set_id"] > 0
        if not has_inline and not has_link:
            return JSONResponse({"ok": False, "error": f"operations[{idx}] musi mit 'data_set' (inline create) NEBO 'data_set_id' (link existing)"}, status_code=400)
        if has_inline:
            ds = op["data_set"]
            # Krok 5.K-B5+: data_set.code optional (NULL allowed per Marti's doctrine)
            # Krok 5.L-D (17.5.2026, Marti's "kind nereflektuje SQL"): drop kind validation,
            # ALTER TABLE DROP COLUMN. SQL text je truth source.
            if not (ds.get("sql_text") or "").strip():
                return JSONResponse({"ok": False, "error": f"operations[{idx}].data_set.sql_text povinne"}, status_code=400)

    # Caller display lookup pro audit
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_dsf
        from modules.core.infrastructure.models_core import User as _User_dsf
        cs_dsf = _gcs_dsf()
        try:
            u_dsf = cs_dsf.query(_User_dsf).filter_by(id=uid).first()
            if u_dsf:
                if u_dsf.short_name and u_dsf.short_name.strip():
                    caller_display = u_dsf.short_name.strip()
                elif u_dsf.first_name or u_dsf.last_name:
                    caller_display = " ".join(filter(None, [u_dsf.first_name, u_dsf.last_name])).strip()
        finally:
            cs_dsf.close()

    ds_session = _gds_dsf()
    try:
        # Krok 5.K-B5+ (Marti's NULL doctrine): uniqueness check JEN pokud code non-null
        if src_code is not None:
            existing_src = ds_session.execute(_sql_text_dsf("""
                SELECT id FROM fw.data_source
                WHERE code = :code AND status = 'active'
                LIMIT 1
            """), {"code": src_code}).mappings().one_or_none()
            if existing_src:
                return JSONResponse(
                    {"ok": False, "error": f"Aktivni data_source s code='{src_code}' uz existuje (id={existing_src['id']}). Pojmenuj jinak nebo archive starý."},
                    status_code=400,
                )

        # 1. INSERT data_source header
        # Krok 5.K-A hotfix (17.5.2026 ~10:30, Marti smoke 500 "column
        # created_by_id does not exist"): fw.data_source z Krok 11-E nema
        # _text audit columns ani row_memory/filter_delay_ms. Jen
        # created_by (FK) per Etapa 6 design_create_fw_data_source pattern.
        src_values = {
            "code": src_code,
            "name": src_name,
            "description": src_description,
            "refresh_type": src_refresh,
            "default_record_limit": src_limit,
            "is_system": False,
            "is_immutable": False,
            "status": "active",
            "created_by": uid,
        }
        src_result = _spg_insert_dsf(schema="fw", table="data_source", values=src_values)
        if not src_result.get("ok"):
            return JSONResponse({"ok": False, "error": f"INSERT data_source failed: {src_result.get('error')}"}, status_code=500)
        new_source_id = src_result["inserted"]["id"]  # single dict insert

        # 2. Loop operations — INSERT data_set (inline) + INSERT data_source_op
        op_results = []
        for idx, op in enumerate(ops):
            # Resolve data_set_id — buď create new, nebo use existing
            if isinstance(op.get("data_set"), dict):
                ds_in = op["data_set"]
                # Krok 5.K-B5+ (Marti's NULL doctrine): data_set.code optional.
                # Krok 5.L-D (17.5.2026, Marti's "kind matouci"): drop kind column
                # — SQL text je truth source, kind je dead weight.
                ds_code_raw = ds_in.get("code")
                ds_code_normalized = None
                if ds_code_raw is not None:
                    ds_code_normalized = str(ds_code_raw).strip() or None
                # Krok 5.M (17.5.2026): db_connection VARCHAR → FK db_connection_id.
                # Backward compat: accept db_connection_id (FK) or db_connection (legacy code string).
                ds_conn_id_raw = ds_in.get("db_connection_id")
                if ds_conn_id_raw is not None:
                    try:
                        _ds_db_connection_id = int(ds_conn_id_raw)
                    except (ValueError, TypeError):
                        ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                        ds_session.commit()
                        return JSONResponse({"ok": False, "error": f"operations[{idx}].data_set.db_connection_id musí být integer, got {ds_conn_id_raw!r}"}, status_code=400)
                else:
                    _ds_conn_code = (ds_in.get("db_connection") or "data_db").strip() or "data_db"
                    _ds_conn_row = ds_session.execute(_sql_text_dsf("""
                        SELECT id FROM fw.db_connection
                        WHERE code = :c OR default_db = :c
                        LIMIT 1
                    """), {"c": _ds_conn_code}).mappings().one_or_none()
                    if _ds_conn_row is None:
                        ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                        ds_session.commit()
                        return JSONResponse({"ok": False, "error": f"operations[{idx}].data_set.db_connection '{_ds_conn_code}' nenalezen v fw.db_connection"}, status_code=400)
                    _ds_db_connection_id = _ds_conn_row["id"]
                set_values = {
                    "code": ds_code_normalized,
                    "sql_text": ds_in["sql_text"],  # multi-line, no strip
                    "db_connection_id": _ds_db_connection_id,
                    "description": (ds_in.get("description") or None),
                    "is_system": False,
                    "status": "active",
                }
                if ds_code_normalized is not None:
                    existing_set = ds_session.execute(_sql_text_dsf("""
                        SELECT id FROM fw.data_set
                        WHERE code = :code AND status = 'active'
                        LIMIT 1
                    """), {"code": ds_code_normalized}).mappings().one_or_none()
                    if existing_set:
                        ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                        ds_session.commit()
                        return JSONResponse(
                            {"ok": False, "error": f"operations[{idx}].data_set.code='{ds_code_normalized}' uz existuje (id={existing_set['id']}). Použij data_set_id pro reuse, nebo přejmenuj."},
                            status_code=400,
                        )
                set_result = _spg_insert_dsf(schema="fw", table="data_set", values=set_values)
                if not set_result.get("ok"):
                    # Rollback source
                    ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                    ds_session.commit()
                    return JSONResponse({"ok": False, "error": f"INSERT data_set failed: {set_result.get('error')}"}, status_code=500)
                new_set_id = set_result["inserted"]["id"]
            else:
                new_set_id = op["data_set_id"]
                # Verify existing data_set
                verify = ds_session.execute(_sql_text_dsf("""
                    SELECT id FROM fw.data_set WHERE id = :id AND status = 'active'
                """), {"id": new_set_id}).mappings().one_or_none()
                if not verify:
                    ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                    ds_session.commit()
                    return JSONResponse({"ok": False, "error": f"operations[{idx}].data_set_id={new_set_id} neexistuje nebo neni aktivni"}, status_code=404)

            # INSERT data_source_op
            # Krok 5.K-A hotfix: fw.data_source_op z Krok 11-E nema audit columns
            op_values = {
                "data_source_id": new_source_id,
                "data_set_id": new_set_id,
                "operation_kind": op["operation_kind"].strip(),
                "variant_code": op["variant_code"].strip(),
                "sort_order": op.get("sort_order", idx * 10),
                "is_default": bool(op.get("is_default", False)),
                "description": op.get("description"),
            }
            op_result = _spg_insert_dsf(schema="fw", table="data_source_op", values=op_values)
            if not op_result.get("ok"):
                ds_session.execute(_sql_text_dsf("DELETE FROM fw.data_source WHERE id = :id"), {"id": new_source_id})
                ds_session.commit()
                return JSONResponse({"ok": False, "error": f"INSERT data_source_op failed: {op_result.get('error')}"}, status_code=500)
            op_results.append({"op_id": op_result["inserted"]["id"], "data_set_id": new_set_id})

        return JSONResponse({
            "ok": True,
            "data_source_id": new_source_id,
            "operations": op_results,
        })
    except Exception as exc:
        logger.exception(f"design_create_data_source_full failed: {exc}")
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds_session.close()


@api_router.patch("/design/fw-data-source/update/{data_source_id}")
async def design_patch_fw_data_source(data_source_id: int, req: Request) -> JSONResponse:
    """Krok 5.K-B3: general PATCH pro data_source header (NEN archive-specific).

    Route shape: /design/fw-data-source/update/{id} (3 segments) — Marti's
    "literál paths před /{id}" doctrine z Krok 14b+10. 2-segment shape
    /design/fw-data-source/{id} by collidoval s generic design_patch_entity
    `/design/{entity_type}/{row_id}`.

    Body: {name?, description?, refresh_type?, default_record_limit?}
    Whitelist non-immutable fields. Reuse strategie_pg.update_row.

    Returns:
        200: {ok, data_source_id, updated_fields}
        400: invalid body
        404: data_source neexistuje
        500: UPDATE failed
    """
    from core.database_data import get_data_session as _gds_pds
    from sqlalchemy import text as _sql_text_pds
    from modules.strategie_pg.application.service import update_row as _spg_update_pds

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    # Phase 38.4 Krok 14g Etapa F Sprint A (17.5.2026): + status field
    # pro archive/restore z UI (Kristý + Jirka bez DBeaver access).
    ALLOWED = ("name", "description", "refresh_type", "default_record_limit", "status")
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]
    if not update_vals:
        return JSONResponse({"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"}, status_code=400)

    # Validation
    if "default_record_limit" in update_vals:
        v = update_vals["default_record_limit"]
        if not isinstance(v, int) or v <= 0:
            return JSONResponse({"ok": False, "error": "default_record_limit musi byt positive int"}, status_code=400)
    if "status" in update_vals:
        v = update_vals["status"]
        if v not in ("active", "archived"):
            return JSONResponse({"ok": False, "error": f"status musi byt 'active' nebo 'archived', got {v!r}"}, status_code=400)

    ds_pds = _gds_pds()
    try:
        # Verify existence
        existing = ds_pds.execute(_sql_text_pds("""
            SELECT id, status FROM fw.data_source WHERE id = :id
        """), {"id": data_source_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse({"ok": False, "error": f"data_source id={data_source_id} neexistuje"}, status_code=404)
        if existing["status"] != "active":
            return JSONResponse({"ok": False, "error": f"data_source id={data_source_id} neni active (status={existing['status']})"}, status_code=400)

        upd = _spg_update_pds(schema="fw", table="data_source", values=update_vals, where={"id": data_source_id}, dry_run=False)
        if not upd.get("ok"):
            return JSONResponse({"ok": False, "error": f"UPDATE failed: {upd.get('error')}"}, status_code=500)

        return JSONResponse({
            "ok": True,
            "data_source_id": data_source_id,
            "updated_fields": sorted(update_vals.keys()),
        })
    finally:
        ds_pds.close()


@api_router.get("/design/data-set/{data_set_id}")
def design_get_data_set_single(data_set_id: int, req: Request) -> JSONResponse:
    """Krok 5.L-A GET single data_set detail + use count (pocet refs v data_source_op).

    Returns:
        200: { ok, data_set: {id, code, sql_text, db_connection, description, status,
               is_system, created_at}, use_count }  # kind dropped Krok 5.L-D 17.5.2026
        404: data_set neexistuje
    """
    from core.database_data import get_data_session as _gds_gdss
    from sqlalchemy import text as _sql_text_gdss

    uid = _get_uid(req)
    _require_parent(uid)

    ds_session = _gds_gdss()
    try:
        row = ds_session.execute(_sql_text_gdss("""
            SELECT * FROM fw.data_set WHERE id = :id
        """), {"id": data_set_id}).mappings().one_or_none()
        if not row:
            return JSONResponse({"ok": False, "error": f"data_set id={data_set_id} nenalezen"}, status_code=404)

        # Count refs in data_source_op (informativní pro UI warning)
        use_count = ds_session.execute(_sql_text_gdss("""
            SELECT COUNT(*) AS cnt FROM fw.data_source_op WHERE data_set_id = :id
        """), {"id": data_set_id}).scalar() or 0

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "data_set": dict(row),
            "use_count": use_count,
        }))
    finally:
        ds_session.close()


@api_router.post("/design/data-set/create")
async def design_create_data_set(req: Request) -> JSONResponse:
    """Krok 5.L-A POST single data_set create.

    Body: {kind: str, sql_text: str, db_connection?: 'data_db', description?: str, code?: null}

    code defaultne NULL per Marti's doctrine (17.5.). PG UNIQUE allows multiple NULLs.

    Returns:
        200: {ok, data_set_id, data_set: {...full row...}}
        400: invalid body
        500: INSERT failed
    """
    from core.database_data import get_data_session as _gds_cds_set
    from sqlalchemy import text as _sql_text_cds_set
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cds_set

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    # Krok 5.L-D (17.5.2026, Marti's "kind matouci"): drop kind field — SQL truth source
    # Krok 5.M (17.5.2026): db_connection VARCHAR → FK db_connection_id.
    # Backward compat: accept db_connection_id (FK BIGINT) or db_connection (legacy code string).
    sql_text = body.get("sql_text") or ""
    db_conn_id_raw = body.get("db_connection_id")
    db_conn_legacy = body.get("db_connection")  # legacy string code
    description = body.get("description")
    if description is not None:
        description = str(description).strip() or None

    # Code optional — None = NULL v DB (Marti's NULL doctrine)
    code_raw = body.get("code")
    code_normalized = None
    if code_raw is not None:
        code_normalized = str(code_raw).strip() or None

    # Validation
    if not sql_text.strip():
        return JSONResponse({"ok": False, "error": "sql_text povinný"}, status_code=400)

    ds_session = _gds_cds_set()
    try:
        # Resolve db_connection_id (Krok 5.M backward compat)
        db_connection_id = None
        if db_conn_id_raw is not None:
            try:
                db_connection_id = int(db_conn_id_raw)
            except (ValueError, TypeError):
                return JSONResponse({"ok": False, "error": f"db_connection_id musí být integer, got {db_conn_id_raw!r}"}, status_code=400)
        else:
            # Legacy fallback: lookup FK by code OR default_db string
            conn_code = (db_conn_legacy or "data_db").strip() or "data_db"
            conn_row = ds_session.execute(_sql_text_cds_set("""
                SELECT id FROM fw.db_connection
                WHERE code = :c OR default_db = :c
                LIMIT 1
            """), {"c": conn_code}).mappings().one_or_none()
            if conn_row is None:
                return JSONResponse({"ok": False, "error": f"db_connection '{conn_code}' nenalezen v fw.db_connection"}, status_code=400)
            db_connection_id = conn_row["id"]

        # Uniqueness check JEN pokud code non-null
        if code_normalized is not None:
            existing = ds_session.execute(_sql_text_cds_set("""
                SELECT id FROM fw.data_set
                WHERE code = :code AND status = 'active'
                LIMIT 1
            """), {"code": code_normalized}).mappings().one_or_none()
            if existing:
                return JSONResponse(
                    {"ok": False, "error": f"Aktivni data_set s code='{code_normalized}' uz existuje (id={existing['id']})."},
                    status_code=400,
                )

        values = {
            "code": code_normalized,
            "sql_text": sql_text,
            "db_connection_id": db_connection_id,
            "description": description,
            "is_system": False,
            "status": "active",
        }
        result = _spg_insert_cds_set(schema="fw", table="data_set", values=values)
        if not result.get("ok"):
            return JSONResponse({"ok": False, "error": f"INSERT data_set failed: {result.get('error')}"}, status_code=500)

        new_row = result.get("inserted") or {}
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "data_set_id": new_row.get("id"),
            "data_set": new_row,
        }))
    finally:
        ds_session.close()


@api_router.patch("/design/data-set/update/{data_set_id}")
async def design_patch_data_set(data_set_id: int, req: Request) -> JSONResponse:
    """Krok 5.K-B3: PATCH data_set (SQL primitiv) — update sql_text +
    db_connection + description.  # kind dropped Krok 5.L-D 17.5.2026

    Route 3-segment (Marti's gotcha #14b+10) — vyhne collision s generic
    design_patch_entity `/design/{entity_type}/{row_id}`.

    Body: {sql_text?, kind?, db_connection?, description?}
    """
    from core.database_data import get_data_session as _gds_pdset
    from sqlalchemy import text as _sql_text_pdset
    from modules.strategie_pg.application.service import update_row as _spg_update_pdset

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    # Krok 5.L-D (17.5.2026, Marti's "kind matouci"): drop kind z ALLOWED
    # Krok 5.M (17.5.2026): db_connection VARCHAR → FK db_connection_id.
    # Backward compat: accept db_connection_id (FK BIGINT) or db_connection (legacy code string).
    # Sprint A (17.5.2026 dop.): + status pro archive/restore z UI.
    ALLOWED = ("sql_text", "db_connection_id", "description", "status")
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]
    if "status" in update_vals:
        v = update_vals["status"]
        if v not in ("active", "archived"):
            return JSONResponse({"ok": False, "error": f"status musi byt 'active' nebo 'archived', got {v!r}"}, status_code=400)

    ds_pdset = _gds_pdset()
    try:
        # Legacy db_connection (string code) → FK resolve
        if "db_connection_id" not in update_vals and "db_connection" in body:
            conn_code = (body["db_connection"] or "").strip()
            if conn_code:
                conn_row = ds_pdset.execute(_sql_text_pdset("""
                    SELECT id FROM fw.db_connection
                    WHERE code = :c OR default_db = :c
                    LIMIT 1
                """), {"c": conn_code}).mappings().one_or_none()
                if conn_row is None:
                    return JSONResponse({"ok": False, "error": f"db_connection '{conn_code}' nenalezen v fw.db_connection"}, status_code=400)
                update_vals["db_connection_id"] = conn_row["id"]

        if not update_vals:
            return JSONResponse({"ok": False, "error": f"Body musi obsahovat alespon jeden z: sql_text, db_connection_id (nebo db_connection), description"}, status_code=400)
        existing = ds_pdset.execute(_sql_text_pdset("""
            SELECT id, status FROM fw.data_set WHERE id = :id
        """), {"id": data_set_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse({"ok": False, "error": f"data_set id={data_set_id} neexistuje"}, status_code=404)
        if existing["status"] != "active":
            return JSONResponse({"ok": False, "error": f"data_set id={data_set_id} neni active"}, status_code=400)

        upd = _spg_update_pdset(schema="fw", table="data_set", values=update_vals, where={"id": data_set_id}, dry_run=False)
        if not upd.get("ok"):
            return JSONResponse({"ok": False, "error": f"UPDATE failed: {upd.get('error')}"}, status_code=500)

        return JSONResponse({
            "ok": True,
            "data_set_id": data_set_id,
            "updated_fields": sorted(update_vals.keys()),
        })
    finally:
        ds_pdset.close()


@api_router.post("/design/data-source/{data_source_id}/op-create")
async def design_add_op_to_data_source(data_source_id: int, req: Request) -> JSONResponse:
    """Sprint B+++ (17.5.2026 odp., Marti's "add op v edit mode"):
    POST nová data_source_op pro existing fw.data_source.

    Body required:
        operation_kind (str, "select"|"insert"|...)

    Body optional:
        variant_code (str|None) — Marti's NULL doctrine: NULL OK (runtime fallback)
        is_default (bool, default False)
        sort_order (int, default 0)
        description (str|None)

    Body — buď reuse OR inline create:
        data_set_id (int) — reuse existing fw.data_set
        OR
        data_set: {sql_text, db_connection_id|db_connection, description?, code?}
                  — inline create new fw.data_set

    Returns:
        200: {ok, op_id, data_set_id}
        400: invalid body
        404: data_source neexistuje
    """
    from core.database_data import get_data_session as _gds_aop
    from sqlalchemy import text as _sql_text_aop
    from modules.strategie_pg.application.service import insert_row as _spg_insert_aop

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    op_kind = (body.get("operation_kind") or "").strip()
    if not op_kind:
        return JSONResponse({"ok": False, "error": "operation_kind povinne"}, status_code=400)

    ds = _gds_aop()
    try:
        # Verify data_source exists
        ds_row = ds.execute(_sql_text_aop("""
            SELECT id FROM fw.data_source WHERE id = :id AND status = 'active'
        """), {"id": data_source_id}).mappings().one_or_none()
        if not ds_row:
            return JSONResponse({"ok": False, "error": f"data_source id={data_source_id} neexistuje nebo neni aktivni"}, status_code=404)

        # Resolve data_set_id — reuse OR inline create
        data_set_id = body.get("data_set_id")
        if data_set_id is not None:
            # Reuse path — verify exists + active
            verify = ds.execute(_sql_text_aop("""
                SELECT id FROM fw.data_set WHERE id = :id AND status = 'active'
            """), {"id": int(data_set_id)}).mappings().one_or_none()
            if not verify:
                return JSONResponse({"ok": False, "error": f"data_set id={data_set_id} neexistuje nebo neni aktivni"}, status_code=404)
            new_set_id = int(data_set_id)
        elif isinstance(body.get("data_set"), dict):
            # Inline create path
            ds_in = body["data_set"]
            sql_text = (ds_in.get("sql_text") or "").strip()
            if not sql_text:
                return JSONResponse({"ok": False, "error": "data_set.sql_text povinne"}, status_code=400)
            # Resolve db_connection_id (FK preferred, legacy string fallback)
            db_conn_id_raw = ds_in.get("db_connection_id")
            if db_conn_id_raw is not None:
                try:
                    db_conn_id = int(db_conn_id_raw)
                except (ValueError, TypeError):
                    return JSONResponse({"ok": False, "error": f"data_set.db_connection_id musi byt integer"}, status_code=400)
            else:
                conn_code = (ds_in.get("db_connection") or "data_db").strip() or "data_db"
                conn_row = ds.execute(_sql_text_aop("""
                    SELECT id FROM fw.db_connection WHERE code = :c OR default_db = :c LIMIT 1
                """), {"c": conn_code}).mappings().one_or_none()
                if conn_row is None:
                    return JSONResponse({"ok": False, "error": f"db_connection '{conn_code}' nenalezen"}, status_code=400)
                db_conn_id = conn_row["id"]
            ds_code_raw = ds_in.get("code")
            ds_code = str(ds_code_raw).strip() or None if ds_code_raw is not None else None
            set_values = {
                "code": ds_code,
                "sql_text": sql_text,
                "db_connection_id": db_conn_id,
                "description": (ds_in.get("description") or None),
                "is_system": False,
                "status": "active",
            }
            set_result = _spg_insert_aop(schema="fw", table="data_set", values=set_values)
            if not set_result.get("ok"):
                return JSONResponse({"ok": False, "error": f"INSERT data_set failed: {set_result.get('error')}"}, status_code=500)
            new_set_id = set_result["inserted"]["id"]
        else:
            return JSONResponse({"ok": False, "error": "body musi mit 'data_set_id' (reuse) NEBO 'data_set' (inline create)"}, status_code=400)

        # Build op values — variant_code NULL allowed (Krok 5.K-B6 doctrine)
        variant_code = body.get("variant_code")
        if variant_code is not None and not str(variant_code).strip():
            variant_code = None
        op_values = {
            "data_source_id": data_source_id,
            "data_set_id": new_set_id,
            "operation_kind": op_kind,
            "variant_code": variant_code,
            "is_default": bool(body.get("is_default", False)),
            "sort_order": int(body.get("sort_order") or 0),
            "description": (body.get("description") or None),
        }
        op_result = _spg_insert_aop(schema="fw", table="data_source_op", values=op_values)
        if not op_result.get("ok"):
            return JSONResponse({"ok": False, "error": f"INSERT data_source_op failed: {op_result.get('error')}"}, status_code=500)

        new_op_id = op_result["inserted"]["id"]
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "op_id": new_op_id,
            "data_set_id": new_set_id,
            "data_source_id": data_source_id,
        }))
    finally:
        ds.close()


@api_router.patch("/design/data-source-op/update/{op_id}")
async def design_patch_data_source_op(op_id: int, req: Request) -> JSONResponse:
    """Krok 5.K-B3: PATCH data_source_op (mapping) — update variant + kind +
    sort + is_default + description.

    Route 3-segment (Marti's gotcha #14b+10) — vyhne collision s generic
    design_patch_entity `/design/{entity_type}/{row_id}`.

    Body: {variant_code?, operation_kind?, sort_order?, is_default?, description?}
    """
    from core.database_data import get_data_session as _gds_pop
    from sqlalchemy import text as _sql_text_pop
    from modules.strategie_pg.application.service import update_row as _spg_update_pop

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    ALLOWED = ("variant_code", "operation_kind", "sort_order", "is_default", "description")
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]
    if not update_vals:
        return JSONResponse({"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"}, status_code=400)

    ds_pop = _gds_pop()
    try:
        existing = ds_pop.execute(_sql_text_pop("""
            SELECT id FROM fw.data_source_op WHERE id = :id
        """), {"id": op_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse({"ok": False, "error": f"data_source_op id={op_id} neexistuje"}, status_code=404)

        upd = _spg_update_pop(schema="fw", table="data_source_op", values=update_vals, where={"id": op_id}, dry_run=False)
        if not upd.get("ok"):
            return JSONResponse({"ok": False, "error": f"UPDATE failed: {upd.get('error')}"}, status_code=500)

        return JSONResponse({
            "ok": True,
            "op_id": op_id,
            "updated_fields": sorted(update_vals.keys()),
        })
    finally:
        ds_pop.close()


@api_router.get("/design/data-source/{data_source_id}/full")
def design_get_data_source_full(data_source_id: int, req: Request) -> JSONResponse:
    """Krok 5.K-A GET endpoint: full detail s linked ops + data_sets pro
    editor edit mode load.

    Returns:
        200: {
            ok: true,
            source: {id, code, name, description, refresh_type, default_record_limit, status, created_*, updated_*},
            operations: [
                {
                    id, variant_code, operation_kind, sort_order, is_default, description,
                    data_set: { id, code, sql_text, db_connection, description, status }  # kind dropped Krok 5.L-D
                },
                ...
            ]
        }
        404: data_source neexistuje
    """
    from core.database_data import get_data_session as _gds_dgf
    from sqlalchemy import text as _sql_text_dgf

    uid = _get_uid(req)
    _require_parent(uid)

    ds_session = _gds_dgf()
    try:
        # Krok 5.K-A hotfix: fw.data_source z Krok 11-E nema _text audit columns
        # ani version. SELECT * defensively pres mappings() — returns all cols.
        src_row = ds_session.execute(_sql_text_dgf("""
            SELECT * FROM fw.data_source WHERE id = :id
        """), {"id": data_source_id}).mappings().one_or_none()
        if not src_row:
            return JSONResponse({"ok": False, "error": f"data_source id={data_source_id} nenalezen"}, status_code=404)

        # Krok 5.L-D: drop ds.kind (kind column removed)
        # Krok 5.M: ds.db_connection VARCHAR → FK ds.db_connection_id;
        # JOIN fw.db_connection + alias dc.default_db AS db_connection (semantic
        # preservation — legacy varchar column stored default_db value, NE code).
        # Plus dc.code AS db_connection_code (new FK identifier).
        op_rows = ds_session.execute(_sql_text_dgf("""
            SELECT op.id AS op_id, op.variant_code, op.operation_kind,
                   op.sort_order, op.is_default, op.description AS op_description,
                   ds.id AS data_set_id, ds.code AS data_set_code,
                   ds.sql_text,
                   dc.default_db AS db_connection,
                   dc.code AS db_connection_code,
                   ds.db_connection_id,
                   ds.description AS data_set_description, ds.status AS data_set_status
            FROM fw.data_source_op op
            LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
            LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
            WHERE op.data_source_id = :sid
            ORDER BY op.sort_order ASC, op.id ASC
        """), {"sid": data_source_id}).mappings().all()

        operations = []
        for r in op_rows:
            operations.append({
                "id": r["op_id"],
                "variant_code": r["variant_code"],
                "operation_kind": r["operation_kind"],
                "sort_order": r["sort_order"],
                "is_default": r["is_default"],
                "description": r["op_description"],
                "data_set": {
                    "id": r["data_set_id"],
                    "code": r["data_set_code"],
                    "sql_text": r["sql_text"],
                    "db_connection": r["db_connection"],            # legacy semantic: dc.default_db ('data_db', 'DB_EC', ...)
                    "db_connection_code": r["db_connection_code"],  # Krok 5.M: dc.code ('strategie_pg', 'eurosoft_db_ec', ...)
                    "db_connection_id": r["db_connection_id"],      # Krok 5.M: FK
                    "description": r["data_set_description"],
                    "status": r["data_set_status"],
                } if r["data_set_id"] is not None else None,
            })

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "source": dict(src_row),
            "operations": operations,
        }))
    finally:
        ds_session.close()


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g Etapa F Sprint D (17.5.2026 dop.):
# PATCH /design/db-connection/update/{id} + POST /design/db-connection/create
# — Marti's "Kristý/Jirka z UI" — DB connection management bez DBeaveru.
# ════════════════════════════════════════════════════════════════════════
@api_router.patch("/design/db-connection/update/{conn_id}")
async def design_patch_db_connection(conn_id: int, req: Request) -> JSONResponse:
    """PATCH fw.db_connection (Sprint D 17.5.2026).

    Body fields (all optional, alespoň 1):
      label, description, default_db, host, port, login_name,
      scope_databases (JSONB array), is_active, sort_order, status
      (NE: code — immutable per "ID je svaty" doctrine)

    Returns:
        200: {ok, conn_id, updated_fields: [...]}
        400: invalid body
        404: connection neexistuje
    """
    from core.database_data import get_data_session as _gds_pdc
    from sqlalchemy import text as _sql_text_pdc
    from modules.strategie_pg.application.service import update_row as _spg_update_pdc

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    ALLOWED = ("label", "description", "default_db", "host", "port",
               "login_name", "scope_databases", "is_active", "sort_order", "status")
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]

    if not update_vals:
        return JSONResponse({"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"}, status_code=400)

    # Validation
    if "status" in update_vals:
        v = update_vals["status"]
        if v not in ("active", "archived"):
            return JSONResponse({"ok": False, "error": f"status musi byt 'active' nebo 'archived', got {v!r}"}, status_code=400)
    if "is_active" in update_vals:
        update_vals["is_active"] = bool(update_vals["is_active"])
    if "port" in update_vals and update_vals["port"] is not None:
        try:
            update_vals["port"] = int(update_vals["port"])
        except (ValueError, TypeError):
            return JSONResponse({"ok": False, "error": "port musi byt integer nebo null"}, status_code=400)

    ds = _gds_pdc()
    try:
        existing = ds.execute(_sql_text_pdc("""
            SELECT id FROM fw.db_connection WHERE id = :id
        """), {"id": conn_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse({"ok": False, "error": f"db_connection id={conn_id} neexistuje"}, status_code=404)

        upd = _spg_update_pdc(schema="fw", table="db_connection", values=update_vals, where={"id": conn_id}, dry_run=False)
        if not upd.get("ok"):
            return JSONResponse({"ok": False, "error": f"UPDATE failed: {upd.get('error')}"}, status_code=500)

        return JSONResponse({
            "ok": True,
            "conn_id": conn_id,
            "updated_fields": sorted(update_vals.keys()),
        })
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g Etapa F Krok 5.M-D (17.5.2026):
# GET /system/db-connections — frontend reads master registry from DB
# (Marti's "KDE TO CACHUJES?" — drop hardcoded JS array)
# ════════════════════════════════════════════════════════════════════════
@api_router.get("/system/db-connections")
def system_db_connections(req: Request, include_inactive: bool = False) -> JSONResponse:
    """Krok 5.M-D: List DB connections z fw.db_connection.

    Frontend DesignDataSetEditor + DesignDataSourceEditor fetchnou tento
    endpoint při open místo hardcoded DDS_DB_CONNECTIONS — DB = single
    source of truth. Marti's pattern z 17.5. dop.

    Query params:
        include_inactive: bool (default False) — INTERSOFT placeholder shows
                          jen pokud true (UI dropdown by default skryje)

    Returns:
        { ok, connections: [
            {id, code, label, tenant_id, tenant_code, tenant_name,
             db_type, host, port, default_db, scope_databases,
             is_active, sort_order, description}
        ] }
    """
    from core.database_data import get_data_session as _gds_dbconn
    from sqlalchemy import text as _sql_text_dbconn

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_dbconn()
    try:
        sql = _sql_text_dbconn("""
            SELECT dc.id, dc.code, dc.label,
                   dc.tenant_id,
                   t.tenant_code, t.tenant_name,
                   dc.db_type, dc.host, dc.port, dc.default_db,
                   dc.scope_databases,
                   dc.is_active, dc.sort_order, dc.description, dc.status
            FROM fw.db_connection dc
            LEFT JOIN public.tenants t ON t.id = dc.tenant_id
            WHERE (:include_inactive OR dc.is_active = TRUE)
              AND dc.status = 'active'
            ORDER BY dc.sort_order ASC, dc.code ASC
        """)
        rows = ds.execute(sql, {"include_inactive": include_inactive}).mappings().all()
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "connections": [dict(r) for r in rows],
            "count": len(rows),
        }))
    finally:
        ds.close()


@api_router.get("/design/context-menu-items")
def design_list_context_menu_items(req: Request) -> JSONResponse:
    """List active context_menu_item rows pro frontend.

    Query params:
      scope: 'tree_node' | 'grid_row' | 'global' (required)
      applies_to_kind: 'folder' | 'list' | 'form' (optional filter)
      design_mode: 'true' | 'false' (optional; default 'false')

    Pokud design_mode='false', design_only=true rows jsou filtered out.
    Pokud design_mode='true', vsechno (vc. design_only) je vraceno.

    Returns:
      {ok: True, items: [{id, code, label, icon, scope, applies_to_kind,
                          action_kind, action_params, sort_order,
                          is_system, design_only, status, ...}]}
    """
    from core.database_data import get_data_session as _gds_cml
    from sqlalchemy import text as _sql_cml

    uid = _get_uid(req)
    _require_parent(uid)

    scope = req.query_params.get("scope")
    applies_to_kind = req.query_params.get("applies_to_kind")
    design_mode = req.query_params.get("design_mode", "false").lower() == "true"

    if not scope:
        return JSONResponse(
            {"ok": False, "error": "scope query param povinny"},
            status_code=400,
        )

    ds = _gds_cml()
    try:
        # Build WHERE conditions
        where_parts = ["status = 'active'", "is_active = true", "scope = :scope"]
        params = {"scope": scope}
        if applies_to_kind:
            # NULL applies_to_kind = any (matches always)
            where_parts.append("(applies_to_kind IS NULL OR applies_to_kind = :kind)")
            params["kind"] = applies_to_kind
        if not design_mode:
            where_parts.append("design_only = false")

        sql = _sql_cml(f"""
            SELECT *
            FROM fw.context_menu_item
            WHERE {' AND '.join(where_parts)}
            ORDER BY sort_order ASC, id ASC
        """)
        rows = ds.execute(sql, params).mappings().all()

        items = []
        for r in rows:
            rd = dict(r)
            # Phase 38.4 Krok 14g Etapa F Krok 3 (16.5.2026, Marti's "ID je svaty"):
            # core_id zije ve vlastnim FK sloupci s ON DELETE RESTRICT.
            # Pro dispatcher transparency (fw_form_dispatcher.js cte
            # action_params.coreId) slijeme core_id zpet do
            # action_params.coreId pri serializaci. Top-level field
            # `core_id` taky vraceny pro budouci FE migration.
            ap_out = dict(rd.get("action_params") or {})
            core_id = rd.get("core_id")
            if core_id is not None:
                ap_out["coreId"] = core_id
            items.append({
                "id": rd.get("id"),
                "code": rd.get("code"),
                "label": rd.get("label"),
                "icon": rd.get("icon"),
                "scope": rd.get("scope"),
                "applies_to_kind": rd.get("applies_to_kind"),
                "action_kind": rd.get("action_kind"),
                "action_params": ap_out,
                "core_id": core_id,
                "sort_order": rd.get("sort_order"),
                "is_system": bool(rd.get("is_system")) if rd.get("is_system") is not None else False,
                "design_only": bool(rd.get("design_only")) if rd.get("design_only") is not None else False,
                "status": rd.get("status"),
            })
        return JSONResponse({"ok": True, "items": items})
    except Exception as exc:
        logger.exception(f"design_list_context_menu_items failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.post("/design/context-menu-item")
async def design_create_context_menu_item(req: Request) -> JSONResponse:
    """Create new fw.context_menu_item row.

    Body: {
      code: str (required, unique),
      label: str (required),
      icon: str | None (emoji),
      scope: 'tree_node' | 'grid_row' | 'global' (required),
      applies_to_kind: 'folder' | 'list' | 'form' | None,
      action_kind: 'open_fw_form' (default; Marti's volba A),
      action_params: dict | None (např. {form_core_code: 'user_edit'}),
      sort_order: int (default 100),
      design_only: bool (default false)
    }

    Returns:
      200: {ok, item_id, item: {...}}
      400: validation error
      500: INSERT failed
    """
    from core.database_data import get_data_session as _gds_cmc
    from sqlalchemy import text as _sql_cmc
    from modules.strategie_pg.application.service import insert_row as _spg_insert_cmc

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    code = (body.get("code") or "").strip()
    label = (body.get("label") or "").strip()
    icon = body.get("icon")
    if icon is not None:
        icon = icon.strip() or None
    scope = (body.get("scope") or "").strip()
    applies_to_kind = body.get("applies_to_kind")
    if applies_to_kind:
        applies_to_kind = applies_to_kind.strip() or None
    action_kind = (body.get("action_kind") or "open_fw_form").strip()
    action_params = body.get("action_params")
    sort_order = body.get("sort_order", 100)
    design_only = bool(body.get("design_only", False))

    # Validation
    if not code:
        return JSONResponse({"ok": False, "error": "code povinne"}, status_code=400)
    if not label:
        return JSONResponse({"ok": False, "error": "label povinne"}, status_code=400)
    if scope not in ("tree_node", "grid_row", "global"):
        return JSONResponse(
            {"ok": False, "error": "scope must be: tree_node | grid_row | global"},
            status_code=400,
        )
    if action_kind not in ("open_fw_form",):
        return JSONResponse(
            {"ok": False, "error": "action_kind must be: open_fw_form (Marti's volba A)"},
            status_code=400,
        )

    # caller_display
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_cmc
        from modules.core.infrastructure.models_core import User as _User_cmc
        cs = _gcs_cmc()
        try:
            u = cs.query(_User_cmc).filter_by(id=uid).first()
            if u:
                if u.short_name and u.short_name.strip():
                    caller_display = u.short_name.strip()
                elif u.first_name or u.last_name:
                    caller_display = " ".join(filter(None, [u.first_name, u.last_name])).strip()
        finally:
            cs.close()

    ds = _gds_cmc()
    try:
        # Uniqueness check
        existing = ds.execute(_sql_cmc("""
            SELECT id FROM fw.context_menu_item
            WHERE code = :code AND status = 'active'
        """), {"code": code}).mappings().one_or_none()
        if existing:
            return JSONResponse(
                {"ok": False, "error": f"context_menu_item s code='{code}' uz existuje (id={existing['id']})"},
                status_code=400,
            )

        # INSERT pres strategie_pg (Marti-AI's fw schema)
        values = {
            "code": code,
            "label": label,
            "icon": icon,
            "scope": scope,
            "applies_to_kind": applies_to_kind,
            "action_kind": action_kind,
            "action_params": action_params,
            "sort_order": sort_order,
            "is_system": False,  # user items
            "is_active": True,
            "design_only": design_only,
            "status": "active",
            "created_by_id": uid,
            "created_by_text": caller_display,
        }
        ins = _spg_insert_cmc(
            schema="fw",
            table="context_menu_item",
            values=values,
        )
        if not ins.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"INSERT failed: {ins.get('error')}"},
                status_code=500,
            )
        new_row = ins.get("inserted") or {}

        # Activity log
        ds.execute(_sql_cmc("SAVEPOINT pre_audit_cmc"))
        try:
            ds.execute(_sql_cmc("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_context_menu_item_add', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"+ context_menu_item code='{code}' label='{label}' "
                    f"scope={scope} action={action_kind} by {caller_display}"
                ),
            })
            ds.execute(_sql_cmc("RELEASE SAVEPOINT pre_audit_cmc"))
            ds.commit()
        except Exception as _ae:
            try:
                ds.execute(_sql_cmc("ROLLBACK TO SAVEPOINT pre_audit_cmc"))
                ds.commit()
            except Exception:
                ds.rollback()
            logger.warning(f"design_create_context_menu_item activity_log failed: {_ae}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "item_id": new_row.get("id"),
            "item": new_row,
        }))
    except Exception as exc:
        try: ds.rollback()
        except Exception: pass
        logger.exception(f"design_create_context_menu_item failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"POST failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/design/context-menu-item/{item_id}/link-core")
async def design_link_context_menu_item_core(item_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne, Marti's
    "aby bylo mozne i vybirat a prepinat na jine cores"): link/unlink
    fw.context_menu_item → fw.core pres core_id FK.

    Body:
        { "core_id": int | null }
        - int  → SET core_id = <id> (link)
        - null → SET core_id = NULL (unlink, drafted state)

    Marti's flow:
      Picker onSelect (existing core) → PATCH link
      Picker onNew (drafted) → POST create-minimal (auto-link inline)
      "Zrusit core asociaci" → PATCH unlink (core_id=null)

    Returns: { ok, cmi: {id, core_id, ...} }
    """
    from core.database_data import get_data_session as _gds_lc
    from sqlalchemy import text as _sql_lc

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        body = {}

    core_id = body.get("core_id")
    if core_id is not None:
        try:
            core_id = int(core_id)
        except (TypeError, ValueError):
            return JSONResponse(
                {"ok": False, "error": "core_id musi byt int nebo null"},
                status_code=400,
            )

    ds = _gds_lc()
    try:
        # Verify cmi exists
        existing = ds.execute(_sql_lc("""
            SELECT id, code, label, core_id
            FROM fw.context_menu_item
            WHERE id = :id
        """), {"id": item_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"context_menu_item id={item_id} neexistuje"},
                status_code=404,
            )

        # If core_id IS NOT NULL, verify fw.core row exists
        if core_id is not None:
            core_check = ds.execute(_sql_lc("""
                SELECT id, code, label FROM fw.core WHERE id = :id
            """), {"id": core_id}).mappings().one_or_none()
            if not core_check:
                return JSONResponse(
                    {"ok": False,
                     "error": f"fw.core id={core_id} neexistuje (FK violation)"},
                    status_code=400,
                )

        # UPDATE via strategie_pg (Marti-AI db_owner fw.*)
        # update_row signature: schema, table, values, where, dry_run
        # (Marti-AI's "pravo na rozmysl pred cinem" pattern — dry_run default
        # True, musime explicit pass False pro commit).
        from modules.strategie_pg.application.service import update_row as _spg_update_lc
        upd = _spg_update_lc(
            schema="fw",
            table="context_menu_item",
            values={"core_id": core_id},
            where={"id": item_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"LINK failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log audit
        try:
            old_id = existing.get("core_id")
            if core_id is None:
                summary = (
                    f"cmi id={item_id} ({existing.get('code')}) unlinked "
                    f"(was core {old_id})"
                )
            else:
                summary = (
                    f"cmi id={item_id} ({existing.get('code')}) linked "
                    f"to core {core_id} (was {old_id})"
                )
            ds.execute(_sql_lc("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_cmi_link_core', 'user',
                   :summary, 'ui', NOW())
            """), {"uid": uid, "summary": summary})
            ds.commit()
        except Exception as _ae:
            logger.warning(f"design_link_context_menu_item_core activity_log failed: {_ae}")

        # Fetch updated cmi row pro response
        updated = ds.execute(_sql_lc("""
            SELECT id, code, label, icon, action_kind, action_params,
                   core_id, status
            FROM fw.context_menu_item
            WHERE id = :id
        """), {"id": item_id}).mappings().one_or_none()
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "cmi": dict(updated) if updated else {},
        }))
    except Exception as exc:
        logger.exception(f"design_link_context_menu_item_core failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"Link failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/design/context-menu-item/{item_id}/archive")
async def design_archive_context_menu_item(item_id: int, req: Request) -> JSONResponse:
    """Archive fw.context_menu_item row (soft delete, status='archived')."""
    from core.database_data import get_data_session as _gds_cma
    from sqlalchemy import text as _sql_cma
    from modules.strategie_pg.application.service import update_row as _spg_update_cma

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_cma()
    try:
        existing = ds.execute(_sql_cma("""
            SELECT id, code, label, status FROM fw.context_menu_item WHERE id = :id
        """), {"id": item_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"context_menu_item id={item_id} neexistuje"},
                status_code=404,
            )
        if existing.get("status") == "archived":
            return JSONResponse({
                "ok": True, "item_id": item_id, "note": "already archived (idempotent)",
            })

        upd = _spg_update_cma(
            schema="fw",
            table="context_menu_item",
            values={"status": "archived", "updated_by_id": uid},
            where={"id": item_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"UPDATE failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log
        ds.execute(_sql_cma("SAVEPOINT pre_audit_cma"))
        try:
            ds.execute(_sql_cma("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor, summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_context_menu_item_archive', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"context_menu_item archived: id={item_id} "
                    f"code='{existing.get('code')}' label='{existing.get('label')}'"
                ),
            })
            ds.execute(_sql_cma("RELEASE SAVEPOINT pre_audit_cma"))
            ds.commit()
        except Exception as _ae:
            try:
                ds.execute(_sql_cma("ROLLBACK TO SAVEPOINT pre_audit_cma"))
                ds.commit()
            except Exception:
                ds.rollback()
            logger.warning(f"design_archive_context_menu_item activity_log failed: {_ae}")

        return JSONResponse({
            "ok": True,
            "item_id": item_id,
            "code": existing.get("code"),
            "label": existing.get("label"),
        })
    finally:
        ds.close()


# ═══════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g — Etapa A — DB Log Infrastructure (16.5.2026)
#
# Marti's doctrine 16.5.:
#   - *„asi dva pohledy master log a detail log"* — dva views
#   - *„Nemelo by to byt anonymni. Hned v hlavicce by jako prvni udaj
#      mel byt LoginName Usera a ID a hned zanim tenant name."* — MASTER
#   - *„kdyz neco v nejakem selze, hodi to uzivateli plnohodnotnou
#      diagnostiku a zbytek bezi dale"* — fail-safe, never crash app
#
# Tabulka fw.diag_log + fw.diag_log_upsert() (viz scripts/_phase14g_log_etapa_A_ddl.sql)
# 3-layer fallback: DB → file JSONL → in-memory (viz core/log_queue.py)
# ═══════════════════════════════════════════════════════════════════════


def _get_user_identity_for_log(user_id: int | None) -> tuple[str | None, int | None, str | None]:
    """Resolve denormalized snapshot (login_name, user_id, tenant_name)
    pro diag_log MASTER view. NE-anonymous (Marti's 16.5. doctrine).

    Fail-safe: pokud DB selze nebo user neexistuje, vraci (None, user_id, None) —
    log_event sam pokracuje.

    Phase 38.4 Krok 14b dotazeni (TODO): az bude users.login_name v DB,
    swap z short_name na login_name.
    """
    if user_id is None:
        return None, None, None
    try:
        from core.database_core import get_core_session as _gcs_di
        from modules.core.infrastructure.models_core import User as _U_di, Tenant as _T_di
        cs = _gcs_di()
        try:
            u = cs.query(_U_di).filter(_U_di.id == user_id).one_or_none()
            if not u:
                return None, user_id, None
            login = getattr(u, "short_name", None) or None
            tid = getattr(u, "last_active_tenant_id", None)
            tname = None
            if tid:
                t = cs.query(_T_di).filter(_T_di.id == int(tid)).one_or_none()
                if t and getattr(t, "tenant_name", None):
                    tname = t.tenant_name
            return login, user_id, tname
        finally:
            cs.close()
    except Exception:
        # Fail-safe: nikdy nepada
        return None, user_id, None


@api_router.post("/diag-log/event")
async def diag_log_post_event(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa A: JS posila diag event do fw.diag_log.

    NO parent gate — user JS code muze logovat eventy (errors, warnings,
    info). Backend auto-fills user_login_name + user_id + tenant_name z
    session cookie pres _get_user_identity_for_log.

    Body (vsechny pole optional krome level/source/module_id/message):
      level: 'info' | 'warn' | 'error' | 'fatal' (required)
      source: 'js' | 'py' | 'sql' | 'cron' | 'mcp' (required)
      module_id: str (required, e.g. "entity_picker.js")
      module_version: str | None
      message: str (required)
      stack: str | None
      page_url, user_agent, viewport: str | None
      element_selector, file_name: str | None
      line_number, column_number: int | None
      exception_type, traceback: str | None  (Py side — typically empty for JS)
      request_id: str | None  (X-Request-Id correlation)
      fastapi_endpoint, http_method: str | None
      http_status, response_time_ms: int | None
      persona_id, conversation_id: int | None
      design_mode: bool | None
      extra: dict | None  (ad-hoc structured data)
      dom_state: dict | None

    Returns:
      {ok: True, id: int | None}  — id is None pri fallback (file/memory)
    """
    from core.log_queue import log_event as _log_event_api

    # Resolve user identity (best-effort, no auth required)
    user_id = None
    try:
        uid_str = req.cookies.get("user_id")
        if uid_str:
            user_id = int(uid_str)
    except Exception:
        user_id = None

    login_name, _resolved_uid, tenant_name = _get_user_identity_for_log(user_id)

    # Parse body
    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    # Required fields (validation but fail-safe — log_event coerces invalid)
    level = (body.get("level") or "info").lower()
    source = (body.get("source") or "js").lower()
    module_id = body.get("module_id") or "unknown"
    message = body.get("message") or "(empty message)"

    # Auto-fill request_id z FastAPI middleware (X-Request-Id header)
    # nebo body pokud predan
    request_id = body.get("request_id")
    if not request_id:
        request_id = getattr(req.state, "request_id", None)
        if not request_id:
            request_id = req.headers.get("X-Request-Id")

    # Call log_event (3-layer fallback inside)
    diag_id = _log_event_api(
        level=level,
        source=source,
        module_id=module_id,
        message=message,
        user_login_name=login_name,
        user_id=user_id,
        tenant_name=tenant_name,
        module_version=body.get("module_version"),
        stack=body.get("stack"),
        page_url=body.get("page_url"),
        user_agent=body.get("user_agent") or req.headers.get("User-Agent"),
        viewport=body.get("viewport"),
        element_selector=body.get("element_selector"),
        file_name=body.get("file_name"),
        line_number=body.get("line_number"),
        column_number=body.get("column_number"),
        exception_type=body.get("exception_type"),
        traceback_str=body.get("traceback"),
        request_id=request_id,
        fastapi_endpoint=body.get("fastapi_endpoint"),
        http_method=body.get("http_method"),
        http_status=body.get("http_status"),
        response_time_ms=body.get("response_time_ms"),
        persona_id=body.get("persona_id"),
        tenant_id=body.get("tenant_id"),
        conversation_id=body.get("conversation_id"),
        design_mode=body.get("design_mode"),
        extra=body.get("extra"),
        dom_state=body.get("dom_state"),
        created_by_id=user_id,
        created_by_text=login_name,
    )
    return JSONResponse({"ok": True, "id": diag_id})


@api_router.get("/diag-log/events")
def diag_log_get_events(req: Request) -> JSONResponse:
    """List diag_log events s filtry + view selection.

    Parent gate — jen rodina muze cist log.

    Query params:
      view: 'master' | 'detail' (default 'master')
      level: 'info' | 'warn' | 'error' | 'fatal' (optional, multi via ',')
      source: 'js' | 'py' | 'sql' | 'cron' | 'mcp' (optional, multi via ',')
      status: 'new' | 'seen' | 'acknowledged' | 'resolved' | 'ignored' (optional, multi)
      user_login: filter podle user_login_name (substring match, optional)
      tenant: filter podle tenant_name (substring match, optional)
      module: filter podle module_id (substring match, optional)
      since: ISO datetime (optional, default last 24h)
      limit: int (default 100, max 500)
      offset: int (default 0)
      include_resolved: 'true' | 'false' (default false, hides status='resolved'/'ignored')

    Returns:
      {ok, total, limit, offset, view, events: [{...}]}
    """
    from core.database_data import get_data_session as _gds_dgl
    from sqlalchemy import text as _sql_dgl
    from datetime import datetime, timedelta, timezone as _tz

    uid = _get_uid(req)
    _require_parent(uid)

    qp = req.query_params
    view = (qp.get("view") or "master").lower()
    if view not in ("master", "detail"):
        view = "master"

    # Multi-value filters (comma-separated)
    def _multi(name: str) -> list[str]:
        raw = qp.get(name, "")
        return [v.strip() for v in raw.split(",") if v.strip()]

    levels = _multi("level")
    sources = _multi("source")
    statuses = _multi("status")
    user_login = (qp.get("user_login") or "").strip()
    tenant = (qp.get("tenant") or "").strip()
    module = (qp.get("module") or "").strip()
    include_resolved = (qp.get("include_resolved") or "false").lower() == "true"

    try:
        limit = min(int(qp.get("limit", "100")), 500)
        offset = max(int(qp.get("offset", "0")), 0)
    except ValueError:
        limit, offset = 100, 0

    since_str = qp.get("since")
    if since_str:
        try:
            since_dt = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
        except ValueError:
            since_dt = datetime.now(_tz.utc) - timedelta(hours=24)
    else:
        since_dt = datetime.now(_tz.utc) - timedelta(hours=24)

    # Build WHERE clause
    where_parts = ["created_at >= :since"]
    params: dict = {"since": since_dt}

    if levels:
        where_parts.append("level = ANY(:levels)")
        params["levels"] = levels
    if sources:
        where_parts.append("source = ANY(:sources)")
        params["sources"] = sources
    if statuses:
        where_parts.append("status = ANY(:statuses)")
        params["statuses"] = statuses
    elif not include_resolved:
        where_parts.append("status NOT IN ('resolved', 'ignored')")

    if user_login:
        where_parts.append("user_login_name ILIKE :ulogin")
        params["ulogin"] = f"%{user_login}%"
    if tenant:
        where_parts.append("tenant_name ILIKE :tn")
        params["tn"] = f"%{tenant}%"
    if module:
        where_parts.append("module_id ILIKE :mod")
        params["mod"] = f"%{module}%"

    where_sql = " AND ".join(where_parts)

    # MASTER view fields (Marti's high-level)
    master_cols = (
        "id, created_at, user_login_name, user_id, tenant_name, "
        "level, source, module_id, message, status, occurrences, last_seen_at"
    )
    # DETAIL view fields (Claude's full forensic) — vse + JSON blobs
    detail_cols = "*"

    cols = detail_cols if view == "detail" else master_cols

    ds = _gds_dgl()
    try:
        # Total count
        count_sql = _sql_dgl(f"SELECT count(*) FROM fw.diag_log WHERE {where_sql}")
        total = ds.execute(count_sql, params).scalar() or 0

        # Page
        list_sql = _sql_dgl(f"""
            SELECT {cols}
            FROM fw.diag_log
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
        """)
        params["limit"] = limit
        params["offset"] = offset
        rows = ds.execute(list_sql, params).mappings().all()

        events = []
        for r in rows:
            ev = dict(r)
            # ISO format pro frontend
            for k in ("created_at", "first_seen_at", "last_seen_at", "resolved_at", "retention_until"):
                if ev.get(k) is not None and hasattr(ev[k], "isoformat"):
                    ev[k] = ev[k].isoformat()
            events.append(ev)

        return JSONResponse({
            "ok": True,
            "total": int(total),
            "limit": limit,
            "offset": offset,
            "view": view,
            "events": events,
        })
    except Exception as exc:
        logger.exception(f"diag_log_get_events failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/diag-log/events/{event_id}/resolve")
async def diag_log_resolve_event(event_id: int, req: Request) -> JSONResponse:
    """Mark diag_log event as acknowledged/resolved/ignored.

    Parent gate. Body:
      resolution: 'acknowledged' | 'resolved' | 'ignored' (required)
      notes: str | None (optional)

    Sets: status = resolution, resolved_at = now(), resolved_by_id = uid,
          resolved_by_text = user.short_name, resolved_notes = notes
    """
    from core.database_data import get_data_session as _gds_dgr
    from sqlalchemy import text as _sql_dgr

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    resolution = (body.get("resolution") or "").lower()
    if resolution not in ("acknowledged", "resolved", "ignored"):
        return JSONResponse(
            {"ok": False, "error": "resolution musi byt 'acknowledged' | 'resolved' | 'ignored'"},
            status_code=400,
        )

    notes = body.get("notes")
    login_name, _uid, _tn = _get_user_identity_for_log(uid)

    ds = _gds_dgr()
    try:
        existing = ds.execute(_sql_dgr(
            "SELECT id, status FROM fw.diag_log WHERE id = :id"
        ), {"id": event_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"diag_log id={event_id} neexistuje"},
                status_code=404,
            )

        ds.execute(_sql_dgr("""
            UPDATE fw.diag_log
            SET status = :status,
                resolved_at = now(),
                resolved_by_id = :uid,
                resolved_by_text = :uname,
                resolved_notes = :notes
            WHERE id = :id
        """), {
            "status": resolution,
            "uid": uid,
            "uname": login_name,
            "notes": notes,
            "id": event_id,
        })
        ds.commit()
        return JSONResponse({
            "ok": True,
            "id": event_id,
            "status": resolution,
            "resolved_by": login_name,
        })
    except Exception as exc:
        try: ds.rollback()
        except Exception: pass
        logger.exception(f"diag_log_resolve_event failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"PATCH failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.get("/diag-log/stats")
def diag_log_get_stats(req: Request) -> JSONResponse:
    """Queue stats (in-memory + file queue sizes + drain status).

    Parent gate. Pro diagnostiku: pokud master view ukazuje pomale rostouci
    queue (DB stale fails), tato vrati real-time stav.
    """
    from core.log_queue import queue_stats as _qs_stats

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        stats = _qs_stats()

        # Plus DB stats (last hour counts per level)
        from core.database_data import get_data_session as _gds_dgs
        from sqlalchemy import text as _sql_dgs
        ds = _gds_dgs()
        try:
            row = ds.execute(_sql_dgs("""
                SELECT
                    count(*) FILTER (WHERE level = 'info')  AS info_count,
                    count(*) FILTER (WHERE level = 'warn')  AS warn_count,
                    count(*) FILTER (WHERE level = 'error') AS error_count,
                    count(*) FILTER (WHERE level = 'fatal') AS fatal_count,
                    count(*) FILTER (WHERE status = 'new')  AS new_count,
                    count(*)                                 AS total_24h
                FROM fw.diag_log
                WHERE created_at >= now() - INTERVAL '24 hours'
            """)).mappings().one_or_none()
            if row:
                stats["db_24h"] = dict(row)
                # Cast Decimal to int
                for k, v in list(stats["db_24h"].items()):
                    if v is not None:
                        try: stats["db_24h"][k] = int(v)
                        except (ValueError, TypeError): pass
        finally:
            ds.close()

        return JSONResponse({"ok": True, "stats": stats})
    except Exception as exc:
        logger.exception(f"diag_log_get_stats failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"Stats failed: {exc}"},
            status_code=500,
        )


@api_router.get("/design/fw-data-source/list")
def design_list_fw_data_source(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g-H+30 Etapa 1 (15.5.2026 vecer, Marti's "B varianta
    dotahnout do finale"): list active fw.data_source rows pro picker
    v Form 1 Prehled tab (2. radek vazba na data_source).

    Returns:
        {"ok": True, "data_sources": [{id, code, name, refresh_type,
          operation_count, is_used_count, ...}, ...]}

    Sorted by name ASC NULLS LAST, code ASC.
    - operation_count: pocet rows v fw.data_source_op (LEFT JOIN COUNT)
    - is_used_count: pocet fw.core rows s matching code (vazba pres code,
      ne pres FK — viz Marti's pattern "vazba via code" 15.5. vecer)

    Defensive SELECT * + row_dict.get() pattern (mirror H+20.1) — fw schema
    drift safety.
    """
    from core.database_data import get_data_session as _gds_dsl
    from sqlalchemy import text as _sql_dsl

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_dsl()
    try:
        # Hlavni SELECT — vsechny sloupce + LEFT JOIN operation_count
        sql_ds = _sql_dsl("""
            SELECT
                s.*,
                COALESCE(op.cnt, 0) AS operation_count,
                op.kinds AS operation_kinds
            FROM fw.data_source s
            LEFT JOIN (
                SELECT
                    data_source_id,
                    COUNT(*) AS cnt,
                    STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
                FROM fw.data_source_op
                GROUP BY data_source_id
            ) op ON op.data_source_id = s.id
            WHERE s.status = 'active'
            ORDER BY s.name ASC NULLS LAST, s.code ASC
        """)
        rows = ds.execute(sql_ds).mappings().all()

        # is_used_count — kolik fw.core rows ma matching code (vazba pres code)
        sql_usage = _sql_dsl("""
            SELECT c.code, COUNT(*) AS cnt
            FROM fw.core c
            INNER JOIN fw.data_source s ON s.code = c.code
            WHERE c.code IS NOT NULL
            GROUP BY c.code
        """)
        usage_rows = ds.execute(sql_usage).mappings().all()
        usage_map = {r["code"]: int(r["cnt"]) for r in usage_rows}

        data_sources = []
        for r in rows:
            rd = dict(r)
            code = rd.get("code")
            data_sources.append({
                "id": rd.get("id"),
                "code": code,
                "name": rd.get("name"),
                "description": rd.get("description"),
                "refresh_type": rd.get("refresh_type"),
                "version": rd.get("version"),
                "status": rd.get("status"),
                "is_system": bool(rd.get("is_system")) if rd.get("is_system") is not None else False,
                "is_immutable": bool(rd.get("is_immutable")) if rd.get("is_immutable") is not None else False,
                "parent_data_source_id": rd.get("parent_data_source_id"),
                "row_memory": bool(rd.get("row_memory")) if rd.get("row_memory") is not None else False,
                "filter_delay_ms": rd.get("filter_delay_ms"),
                "default_record_limit": rd.get("default_record_limit"),
                "operation_count": int(rd.get("operation_count") or 0),
                "operation_kinds": rd.get("operation_kinds") or "",
                "is_used_count": usage_map.get(code, 0) if code else 0,
            })
        return JSONResponse({"ok": True, "data_sources": data_sources})
    except Exception as exc:
        logger.exception(f"design_list_fw_data_source failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g Etapa F Sprint C (17.5.2026 dop.):
# POST /design/data-set/test — ad-hoc SQL execute pro draft data_set SQL
# (preview rows PŘED save). Marti's "Kristý/Jirka chce vidět co spustila".
# MVP: PostgreSQL only (db_type='postgres'). MSSQL → graceful error.
# ════════════════════════════════════════════════════════════════════════
@api_router.post("/design/data-set/test")
async def design_test_data_set(req: Request) -> JSONResponse:
    """Ad-hoc execute SQL pro data_set draft (preview).

    Body:
        {sql_text: str, db_connection_id: int, params?: dict, limit?: int}

    Returns:
        200: {ok, rows: [...], row_count, columns: [...], execution_ms,
              db_connection: {code, default_db, db_type}}
        400: missing sql_text / db_connection_id, MSSQL unsupported,
             non-SELECT detected
        500: SQL execute failed

    Safety:
        - Parent gate
        - SELECT-only regex (no INSERT/UPDATE/DELETE/DROP/...)
        - HARD_LIMIT_CAP=100 rows
        - 30s timeout (SQLAlchemy statement_timeout)
    """
    from core.database_data import get_data_session as _gds_dst
    from sqlalchemy import text as _sql_text_dst
    import re as _re_dst
    import time as _time_dst

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    sql_text = (body.get("sql_text") or "").strip()
    db_conn_id = body.get("db_connection_id")
    params = body.get("params") or {}
    limit = int(body.get("limit") or 10)
    if limit < 1 or limit > 100:
        limit = 10

    if not sql_text:
        return JSONResponse({"ok": False, "error": "sql_text povinný"}, status_code=400)
    if db_conn_id is None:
        return JSONResponse({"ok": False, "error": "db_connection_id povinný"}, status_code=400)

    # SELECT-only guard — Marti-AI Q5 doctrine z 9.5. (strategie_pg_query_raw)
    # Strip leading comments + blank lines, then check first keyword
    sql_check = sql_text.lstrip()
    while sql_check.startswith("--") or sql_check.startswith("/*"):
        if sql_check.startswith("--"):
            sql_check = sql_check.split("\n", 1)[1].lstrip() if "\n" in sql_check else ""
        else:  # /* */
            end_idx = sql_check.find("*/")
            sql_check = sql_check[end_idx + 2:].lstrip() if end_idx >= 0 else ""
    if not _re_dst.match(r"^\s*(SELECT|WITH)\b", sql_check, _re_dst.IGNORECASE):
        return JSONResponse({"ok": False, "error": "Pouze SELECT nebo WITH (CTE) je dovoleno pro test."}, status_code=400)
    # Blocklist defense
    if _re_dst.search(r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|CREATE|TRUNCATE|MERGE|GRANT|REVOKE|EXEC(?!\s+sp_help)|XP_)\b", sql_check, _re_dst.IGNORECASE):
        return JSONResponse({"ok": False, "error": "SQL obsahuje destructive keyword (DELETE/UPDATE/INSERT/atd.)"}, status_code=400)

    ds = _gds_dst()
    try:
        # Resolve db_connection
        conn_row = ds.execute(_sql_text_dst("""
            SELECT id, code, label, db_type, default_db, host
            FROM fw.db_connection
            WHERE id = :id AND is_active = TRUE
            LIMIT 1
        """), {"id": db_conn_id}).mappings().one_or_none()
        if conn_row is None:
            return JSONResponse({"ok": False, "error": f"db_connection id={db_conn_id} nenalezen nebo neaktivní"}, status_code=400)

        # MVP: PostgreSQL only
        if conn_row["db_type"] != "postgres":
            return JSONResponse({
                "ok": False,
                "error": f"MVP test podporuje pouze PostgreSQL. Tento connection je {conn_row['db_type']} ({conn_row['label']}). "
                         "MSSQL test bude dostupný po Phase 30+1.",
            }, status_code=400)
        if conn_row["default_db"] != "data_db":
            return JSONResponse({
                "ok": False,
                "error": f"MVP test podporuje pouze default_db='data_db'. Tento connection je {conn_row['default_db']}.",
            }, status_code=400)

        # Inject LIMIT (HARD_LIMIT_CAP) — pokud uživatel už nemá v SQL
        params_bound = dict(params) if isinstance(params, dict) else {}
        params_bound["limit"] = limit

        # Statement-level timeout 30s — PostgreSQL parameter
        ds.execute(_sql_text_dst("SET LOCAL statement_timeout = 30000"))

        start_ms = _time_dst.time()
        try:
            result = ds.execute(_sql_text_dst(sql_text), params_bound)
            rows = [dict(r) for r in result.mappings().all()[:limit]]
            cols = list(rows[0].keys()) if rows else []
        except Exception as exc:
            execution_ms = int((_time_dst.time() - start_ms) * 1000)
            return JSONResponse({
                "ok": False,
                "error": f"SQL execute failed: {type(exc).__name__}: {exc}",
                "execution_ms": execution_ms,
            }, status_code=400)
        execution_ms = int((_time_dst.time() - start_ms) * 1000)

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "rows": rows,
            "row_count": len(rows),
            "columns": cols,
            "execution_ms": execution_ms,
            "db_connection": {
                "id": conn_row["id"],
                "code": conn_row["code"],
                "label": conn_row["label"],
                "db_type": conn_row["db_type"],
                "default_db": conn_row["default_db"],
            },
            "limit_applied": limit,
        }))
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 14g Etapa F Sprint B (17.5.2026 dop.):
# GET /design/data-set/list — list active fw.data_set pro picker v
# DesignDataSourceEditor._showAddOpForm (📎 Vybrat existing data_set).
# Marti-AI's "uniformita vítězí" doctrine z 11.5. — reuse > duplicate inline.
# ════════════════════════════════════════════════════════════════════════
@api_router.get("/design/data-set-list")  # Sprint B hotfix 17.5. odp: hyphen avoids collision s /design/data-set/{id:int} (Marti's gotcha #14b+10)
def design_list_data_set(req: Request) -> JSONResponse:
    """List active fw.data_set rows + JOIN fw.db_connection pro readable label.

    Returns:
        {ok: True, data_sets: [{id, code, sql_text_preview,
          db_connection_id, db_connection, db_connection_label,
          description, use_count, version, status}]}

    use_count = LEFT JOIN COUNT fw.data_source_op references (kolik ops
    používá tenhle data_set).
    """
    from core.database_data import get_data_session as _gds_dsl
    from sqlalchemy import text as _sql_dsl

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_dsl()
    try:
        sql_dsl = _sql_dsl("""
            SELECT
                ds.id,
                ds.code,
                ds.version,
                ds.description,
                ds.status,
                ds.db_connection_id,
                dc.default_db AS db_connection,
                dc.code       AS db_connection_code,
                dc.label      AS db_connection_label,
                LEFT(ds.sql_text, 200) AS sql_text_preview,
                CHAR_LENGTH(ds.sql_text) AS sql_text_length,
                COALESCE(op.cnt, 0) AS use_count
            FROM fw.data_set ds
            LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
            LEFT JOIN (
                SELECT data_set_id, COUNT(*) AS cnt
                FROM fw.data_source_op
                GROUP BY data_set_id
            ) op ON op.data_set_id = ds.id
            WHERE ds.status = 'active'
            ORDER BY ds.code ASC NULLS LAST, ds.id ASC
        """)
        rows = ds.execute(sql_dsl).mappings().all()
        data_sets = [dict(r) for r in rows]
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "data_sets": data_sets,
            "count": len(data_sets),
        }))
    except Exception as exc:
        logger.exception(f"design_list_data_set failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


@api_router.patch("/design/fw-core/update/{core_id}")
async def design_patch_fw_core(core_id: int, req: Request) -> JSONResponse:
    """Partial update fw.core — label / description_user / description_system.

    Phase 38.4 Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"):
    frontend 💾 Uložit button v _buildDescriptionsPopup posila popisy
    (system + user) jako PATCH na tento endpoint.

    Whitelist: label, description_user, description_system
    Security: parent gate, fw schema owned by Marti-AI (update_row pres
    Marti-AI's PostgreSQL role).

    Body:
        {label?: str, description_user?: str, description_system?: str}

    Returns:
        200: {ok, core_id, updated_fields: [...]}
        400: invalid body / nothing to update
        404: core neexistuje
        500: UPDATE failed
    """
    from core.database_data import get_data_session as _gds_pfc
    from sqlalchemy import text as _sql_text_pfc

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    # Phase 38.4 Krok 14g Etapa F Krok 5.F (16.5.2026, Marti's "schazi
    # Pole + magic"): rozsireno o data_entity_type a code (drafted core
    # postupne nabira meta info — entity assignment je preconditie pro
    # ➕ Pole button visibility v DesignFwForm header).
    # Phase 38.4 Krok 5.M-5 (17.5.2026): data_entity_type DROPPED z ALLOWED
    # (Marti's "core nenese entitu" doctrine). After M-6 DDL drop column,
    # any PATCH attempt would error. Plus form_core_id ADDED — explicit
    # list→form pairing (M-5 FK).
    ALLOWED = (
        "label", "description_user", "description_system",
        "code", "form_core_id",
    )
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            v = body[k]
            # Empty string -> NULL v DB (Marti's "delete popisu" pattern)
            if v == "":
                v = None
            update_vals[k] = v
    if not update_vals:
        return JSONResponse(
            {"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"},
            status_code=400,
        )

    # caller_display lookup
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_pfc
        from modules.core.infrastructure.models_core import User as _User_pfc
        cs_pfc = _gcs_pfc()
        try:
            u_pfc = cs_pfc.query(_User_pfc).filter_by(id=uid).first()
            if u_pfc:
                if u_pfc.short_name and u_pfc.short_name.strip():
                    caller_display = u_pfc.short_name.strip()
                elif u_pfc.first_name or u_pfc.last_name:
                    caller_display = " ".join(filter(None, [
                        u_pfc.first_name, u_pfc.last_name
                    ])).strip()
        finally:
            cs_pfc.close()

    # Existence check
    ds_pfc = _gds_pfc()
    try:
        existing = ds_pfc.execute(_sql_text_pfc("""
            SELECT id, code, label FROM fw.core WHERE id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"fw.core id={core_id} neexistuje"},
                status_code=404,
            )

        # UPDATE pres update_row (Marti-AI owner fw.*)
        from modules.strategie_pg.application.service import update_row as _spg_update_pfc
        full_values = dict(update_vals)
        full_values["updated_by_id"] = uid
        full_values["updated_by_text"] = caller_display
        upd = _spg_update_pfc(
            schema="fw",
            table="core",
            values=full_values,
            where={"id": core_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            return JSONResponse(
                {"ok": False, "error": f"UPDATE failed: {upd.get('error')}"},
                status_code=500,
            )

        # Activity log SAVEPOINT pattern
        ds_pfc.execute(_sql_text_pfc("SAVEPOINT pre_audit_log"))
        try:
            change_desc = ", ".join(
                f"{k}={'<set>' if update_vals[k] else '<empty>'}"
                for k in update_vals.keys()
            )
            ds_pfc.execute(_sql_text_pfc("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_core_update', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"fw.core {existing['code']}: {change_desc} by {caller_display}"
                ),
            })
            ds_pfc.execute(_sql_text_pfc("RELEASE SAVEPOINT pre_audit_log"))
            ds_pfc.commit()
        except Exception as _act_e:
            try:
                ds_pfc.execute(_sql_text_pfc("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds_pfc.commit()
            except Exception:
                ds_pfc.rollback()
            logger.warning(f"design_patch_fw_core activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core_id": core_id,
            "updated_fields": list(update_vals.keys()),
        }))
    finally:
        ds_pfc.close()


@api_router.patch("/design/fw-menu-node/update/{menu_node_id}")
async def design_patch_fw_menu_node(menu_node_id: int, req: Request) -> JSONResponse:
    """Partial update fw.menu_node — label / description_user / description_system.

    Phase 38.4 Krok 14b+21 (14.5.2026 rano): analog design_patch_fw_core
    pro menu_node (soudečky). DRY z duvodu — fw.core a fw.menu_node maji
    stejny whitelist + lifecycle, ale dedicated endpointy pro semantic
    clarity.
    """
    from core.database_data import get_data_session as _gds_pmn
    from sqlalchemy import text as _sql_text_pmn

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    # Phase 38.4 Krok 14g-H (15.5.2026 rano, Marti's "dragable napric
    # celym stromem"): pridat parent_id + sort_order pro tree drag-drop move.
    ALLOWED = ("label", "description_user", "description_system", "parent_id", "sort_order")
    update_vals = {}
    for k in ALLOWED:
        if k in body:
            v = body[k]
            if v == "":
                v = None
            update_vals[k] = v
    if not update_vals:
        return JSONResponse(
            {"ok": False, "error": f"Body musi obsahovat alespon jeden z: {ALLOWED}"},
            status_code=400,
        )

    # parent_id type validation (Krok 14g-H+5, 15.5.2026 dopo, Marti's
    # "naprosto vsechny pojistky v design mode vypnout"): drop business
    # safeguards — anti-self-reference + anti-cycle (recursive CTE walks
    # ancestors). Backend stale validuje typ + null-ability, ale Marti's
    # cil je raw parent_id update. Defensive na render side: _build_node
    # per-child try/except zachyti pripadny cycle RecursionError + vrati
    # error node misto crash. Marti's "worst case" = error node v sidebar,
    # Marti to manualne opravi v DB nebo dragnutim zpet.
    if "parent_id" in update_vals:
        new_parent_id = update_vals["parent_id"]
        if new_parent_id is not None:
            if not isinstance(new_parent_id, int) or new_parent_id <= 0:
                return JSONResponse(
                    {"ok": False, "error": "parent_id musi byt positive int nebo null"},
                    status_code=400,
                )

    # sort_order validation
    if "sort_order" in update_vals:
        new_sort = update_vals["sort_order"]
        if not isinstance(new_sort, int) or new_sort < 0:
            return JSONResponse(
                {"ok": False, "error": "sort_order musi byt non-negative int"},
                status_code=400,
            )

    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_pmn
        from modules.core.infrastructure.models_core import User as _User_pmn
        cs_pmn = _gcs_pmn()
        try:
            u_pmn = cs_pmn.query(_User_pmn).filter_by(id=uid).first()
            if u_pmn:
                if u_pmn.short_name and u_pmn.short_name.strip():
                    caller_display = u_pmn.short_name.strip()
                elif u_pmn.first_name or u_pmn.last_name:
                    caller_display = " ".join(filter(None, [
                        u_pmn.first_name, u_pmn.last_name
                    ])).strip()
        finally:
            cs_pmn.close()

    ds_pmn = _gds_pmn()
    try:
        existing = ds_pmn.execute(_sql_text_pmn("""
            SELECT id, code, label FROM fw.menu_node WHERE id = :id
        """), {"id": menu_node_id}).mappings().one_or_none()
        if not existing:
            return JSONResponse(
                {"ok": False, "error": f"fw.menu_node id={menu_node_id} neexistuje"},
                status_code=404,
            )

        from modules.strategie_pg.application.service import update_row as _spg_update_pmn
        full_values = dict(update_vals)
        full_values["updated_by_id"] = uid
        full_values["updated_by_text"] = caller_display
        upd = _spg_update_pmn(
            schema="fw",
            table="menu_node",
            values=full_values,
            where={"id": menu_node_id},
            dry_run=False,
        )
        if not upd.get("ok"):
            # Phase 38.4 Krok 14g-H+10 (15.5.2026 dopo, Marti's "uz to skoro
            # je"): clean trigger error pro frontend toast. PostgreSQL RAISE
            # EXCEPTION propaguje raw psycopg2 detail (CONTEXT + SQL + params
            # = obří dump). Extract jen human-readable prefix.
            err_raw = str(upd.get('error') or '')
            import re as _re_err
            cycle_match = _re_err.search(r'Cyclic reference[^\n]*', err_raw)
            self_match = _re_err.search(r'cannot reference self[^\n]*', err_raw)
            if cycle_match:
                err_msg = cycle_match.group(0).strip()
            elif self_match:
                err_msg = "Soudeček nemůže být svým vlastním rodičem."
            elif 'ancestry too deep' in err_raw:
                err_msg = "Hierarchie soudečků je příliš hluboká (> 50 úrovní)."
            else:
                err_msg = f"UPDATE failed: {upd.get('error')}"
            return JSONResponse(
                {"ok": False, "error": err_msg},
                status_code=500,
            )

        ds_pmn.execute(_sql_text_pmn("SAVEPOINT pre_audit_log"))
        try:
            change_desc = ", ".join(
                f"{k}={'<set>' if update_vals[k] else '<empty>'}"
                for k in update_vals.keys()
            )
            ds_pmn.execute(_sql_text_pmn("""
                INSERT INTO public.activity_log
                  (user_id, persona_id, category, actor,
                   summary, change_source, ts)
                VALUES
                  (:uid, NULL, 'design_menu_node_update', 'user',
                   :summary, 'ui', NOW())
            """), {
                "uid": uid,
                "summary": (
                    f"fw.menu_node {existing['code']}: {change_desc} by {caller_display}"
                ),
            })
            ds_pmn.execute(_sql_text_pmn("RELEASE SAVEPOINT pre_audit_log"))
            ds_pmn.commit()
        except Exception as _act_e:
            try:
                ds_pmn.execute(_sql_text_pmn("ROLLBACK TO SAVEPOINT pre_audit_log"))
                ds_pmn.commit()
            except Exception:
                ds_pmn.rollback()
            logger.warning(f"design_patch_fw_menu_node activity_log failed: {_act_e}")

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "menu_node_id": menu_node_id,
            "updated_fields": list(update_vals.keys()),
        }))
    finally:
        ds_pmn.close()


@api_router.get("/design/entity-columns/{entity_type}")
def design_list_entity_columns(
    entity_type: str,
    req: Request,
    parent_comp_def_id: int | None = None,
) -> JSONResponse:
    """List columns z _FW_FORM_ENTITY_MAP s suggested comp_type per column.

    Phase 38.4 Krok 14c+1 (14.5.2026 vecer, Marti's "TabSheet pro
    Schazi/Na forme/Preview"):
      Volitelne query param `parent_comp_def_id` = form root id (type=302).
      Pokud dotazeno, endpoint merguje existing comp_def per column —
      pridava `existing_comp_def_id` + `existing_label` per row. Bez
      parametru = backward compat (no merge, vsechny sloupce jako
      "available").

    Returns:
        200: {ok, entity_type, parent_comp_def_id, columns: [
              {name, caption_default, suggested_type_id, suggested_type_code,
               existing_comp_def_id, existing_label}
            ]}
        404: entity_type nezaregistrovan
    """
    uid = _get_uid(req)
    _require_parent(uid)

    # Phase 38.4 Krok 5.M-3 hotfix (17.5.2026): defensive against
    # entity_type=="null" (string) — JS encodeURIComponent(null) -> "null".
    # Vraci diagnostika: poradek volajiciho ma fallback na data_entity_type.
    if entity_type == "null" or not entity_type:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    "Entity type je 'null'/empty — pravdepodobne core.code "
                    "neni set v DB (drafted core per Krok 5.A doctrine). "
                    "Frontend by mel fallback na core.id."
                ),
                "hint": "Marti: SELECT id, code FROM fw.core WHERE id = <core_id>",
                "registry_ids": list(_FW_FORM_CORE_REGISTRY.keys()),
                "map_codes": list(_FW_FORM_ENTITY_MAP.keys()),
            },
            status_code=404,
        )

    # Phase 38.4 Krok 5.N-2b (17.5.2026, Marti's "code je optional, ID je truth"):
    # entity_type može być numeric (URL /design/entity-columns/22 — ID-based)
    # NEBO string (URL /design/entity-columns/user — legacy entity_type).
    # Detekce + dispatch via _resolve_entity_config_for_core (5.N-1 helper).
    config = None
    if entity_type.isdigit():
        # ID-based path — Marti's 5.N doctrine
        config = _resolve_entity_config_for_core(int(entity_type))
    elif entity_type in _FW_FORM_ENTITY_MAP:
        # Legacy string path — direct entity (user, menu_node, core, comp_def)
        config = _FW_FORM_ENTITY_MAP[entity_type]

    if not config:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    f"Entity '{entity_type}' není v _FW_FORM_ENTITY_MAP "
                    f"ani _FW_FORM_CORE_REGISTRY. "
                    f"Registry IDs: {list(_FW_FORM_CORE_REGISTRY.keys())}. "
                    f"Map codes: {list(_FW_FORM_ENTITY_MAP.keys())}."
                ),
            },
            status_code=404,
        )
    id_col = config["id_column"]
    cols_list = config["select_columns"]

    # Load comp_types lookup pro suggested_type_code mapping
    from core.database_data import get_data_session as _gds_lec
    from sqlalchemy import text as _sql_text_lec
    ds_lec = _gds_lec()
    try:
        ct_rows = ds_lec.execute(_sql_text_lec("""
            SELECT id, code FROM fw.comp_type WHERE preview_html IS NOT NULL
        """)).mappings().all()
        ct_by_id = {r["id"]: r["code"] for r in ct_rows}

        # Phase 38.4 Krok 14c+1: existing comp_def merge per name
        # (case-insensitive defensive — Centrala 1 ma legacy mixed-case
        # column names, fw.comp_def.name typicky lowercase).
        existing_by_name: dict[str, dict[str, object]] = {}
        if parent_comp_def_id is not None:
            existing_rows = ds_lec.execute(_sql_text_lec("""
                SELECT id, name, caption, region_slot, type_id
                FROM fw.comp_def
                WHERE parent_comp_def_id = :pid
                  AND is_active = true
            """), {"pid": parent_comp_def_id}).mappings().all()
            for ex_row in existing_rows:
                key = (ex_row["name"] or "").lower().strip()
                if key:
                    existing_by_name[key] = {
                        "id": ex_row["id"],
                        "caption": ex_row["caption"],
                        "region_slot": ex_row["region_slot"],
                        "type_id": ex_row["type_id"],
                    }
    finally:
        ds_lec.close()

    columns_out = []
    for col in cols_list:
        if col == id_col:
            continue  # skip ID column (immutable, no field needed)
        suggested_id = _suggest_comp_type_id(col)
        ex_match = existing_by_name.get(col.lower().strip())
        columns_out.append({
            "name": col,
            "caption_default": col.replace("_", " ").strip().capitalize(),
            "suggested_type_id": suggested_id,
            "suggested_type_code": ct_by_id.get(suggested_id, "?"),
            # Phase 38.4 Krok 14c+1: existing comp_def info (None pokud
            # chybi nebo parent_comp_def_id nedotazen)
            "existing_comp_def_id": ex_match["id"] if ex_match else None,
            "existing_label": ex_match["caption"] if ex_match else None,
            "existing_region_slot": ex_match["region_slot"] if ex_match else None,
            "existing_type_id": ex_match["type_id"] if ex_match else None,
        })

    return JSONResponse(jsonable_encoder({
        "ok": True,
        "entity_type": entity_type,
        "parent_comp_def_id": parent_comp_def_id,
        "columns": columns_out,
    }))


@api_router.get("/data")
def data_source_list(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 12 — list všech available data_source codes (discovery).

    URL: GET /api/v1/erp/data
    Returns: JSON {"ok": True, "items": [{code, name, description, operation_count, kinds}, ...]}
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_data import get_data_session as _gds_data_list

    session = _gds_data_list()
    try:
        items = ds_runner.list_available_codes(session)
    finally:
        session.close()

    return JSONResponse(jsonable_encoder({"ok": True, "items": items}))


@api_router.get("/system/tree")
def system_tree(req: Request) -> JSONResponse:
    """Phase 35-E.4 (9.5.2026): System tier tree pro rodiče.

    Vrací hardcoded System soudeček s 3 sub-uzly. Visible jen pro
    is_marti_parent=True (defense in depth — _require_parent + explicit
    parent check).

    Future: nahradí se za query nad fw.menu_node (Phase 30+).
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
    }, headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})


# ── Phase B (5.5.2026): Tree + Přehled JSON endpoints ────────────────


# ─────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 6 (10.5.2026 odpoledne): DB-driven system tree.
#
# Primárně z fw.menu_node (PostgreSQL, owned by Marti-AI), fallback
# na hardcoded Python dict pokud DB query selže nebo vrátí prázdno
# (offline mode, permission denied, ještě neINSERTované rows, ...).
#
# Doctrine "hardcode jako seed s tooling pro migraci" v praxi —
# hardcoded zůstává jako safety net dokud DB nebude kompletně zaplněná.
# ─────────────────────────────────────────────────────────────────────

# Cislo_def → (system_view, system_view_mode, single) mapping —
# mirror JS _systemModeFromCislo. Backend musí tuto info attachit na
# leaf nodes (frontend by je musel jinak derivovat z cisla zpětně).
_SYSTEM_CISLO_TO_VIEW = {
    # Phase 35-E.4 audit views
    -100: ("audit_overview", "tabs",     False),
    -101: ("audit_overview", "audited",  True),
    -102: ("audit_overview", "all",      True),
    -103: ("audit_overview", "stats",    True),
    # Phase 38.3 security views
    -110: ("security", "users",       False),
    -111: ("security", "devices",     False),
    -112: ("security", "whitelists",  False),
    -113: ("security", "auth_audit",  False),
    -114: ("security", "invites",     False),
    # Phase 38.3+ framework views
    -115: ("framework", "menu_nodes",   False),
    -116: ("framework", "data_sources", False),
    -117: ("framework", "data_sets",    False),
    # Phase 38.4 Krok 14g Etapa D (16.5.2026): diag log master view.
    # Mode 'diag_log_master' = hw_registry.code → /api/v1/erp/hw/diag_log_master
    # dispatch returns delegate_url pres response_hint $.events extraction.
    -118: ("diag_log", "master", False),  # 16.5. Marti's "data_diag_log_master" → "diag_log_master" hw_registry match
}


def _build_system_root_from_db():
    """Phase 38.4 Krok 6: DB-driven system tree.

    Načte aktivní rows z fw.menu_node (visibility_scope='parent_only'),
    sestaví nested dict structure kompatibilní s frontend renderTreeNodes
    (id, label, nazev, cislo_def, is_system, is_folder, system_view,
    system_view_mode, single, children).

    Returns:
        dict system_root, OR None pokud DB error / empty / žádný root.

    None signalizuje fallback na hardcoded dict (níže v strom_json).
    """
    from sqlalchemy import text as _sql_text_st
    from core.database_data import get_data_session as _gds_st

    ds = _gds_st()
    try:
        # Phase 38.4 Krok 13.4 (11.5.2026): dispatch_kind enrichment.
        # LEFT JOIN na fw.core (přes core_id FK z Krok 11-C) → fw.hw_registry
        # (code-based, hw_registry nemá FK z core). NULL-safe — folders + nodes
        # bez core/hw vrátí NULL hw_shadow_mode → _build_node mapuje na 'orphan'.
        sql = _sql_text_st("""
            SELECT n.id, n.parent_id, n.code, n.label, n.kind, n.sort_order,
                   n.visibility_scope, n.cislo_def, n.special_handler, n.status,
                   n.is_immutable, n.core_id, c.code AS core_code,
                   hw.shadow_mode AS hw_shadow_mode, hw.is_active AS hw_is_active
            FROM fw.menu_node n
            LEFT JOIN fw.core c ON c.id = n.core_id
            LEFT JOIN fw.hw_registry hw ON hw.code = c.code AND hw.is_active = TRUE
            WHERE n.status = 'active'
              AND n.visibility_scope = 'parent_only'
            ORDER BY n.parent_id NULLS FIRST, n.sort_order, n.code
        """)
        result = ds.execute(sql)
        rows = [dict(r._mapping) for r in result]
    except Exception:
        import logging
        logging.exception("system tree DB query failed — fallback na hardcoded")
        return None
    finally:
        ds.close()

    if not rows:
        return None

    # Index by parent_id pro tree build
    by_parent: dict = {}
    for r in rows:
        pid = r.get("parent_id")
        by_parent.setdefault(pid, []).append(r)

    # Find system root (parent_id IS NULL, code='system')
    # Phase 38.4 Krok 14g-G2 (15.5.2026 rano, Marti's "novy soudecek
    # mel byt sibling SYSTEM v sidebar"): get ALL top-level roots, ne
    # jen system. Return list — strom_json appende vsechny do tree.
    roots = by_parent.get(None, [])
    system_db = next((r for r in roots if r.get("code") == "system"), None)
    other_roots = [r for r in roots if r.get("code") != "system"]
    if not system_db and not other_roots:
        return None

    def _build_node(row):
        # Phase 38.4 Krok 12-D (11.5.2026): Marti's resilient rendering mandate
        # *„odchytit chybu, polozku stromu vykreslit a chybu zobrazit v pravem
        # panelu"*. Per-node + per-child try/except — failure jednoho rowu
        # nesmí dropnout siblings ani parent. Error node má is_error=True
        # + error_detail string pro frontend right-panel render.
        try:
            cislo = row.get("cislo_def")
            # Phase 38.4 Krok 14g-H+12 (15.5.2026 vecer, Marti's "CORE chybi
            # v oblibených"): synthetic cislo_def pro nodes bez Centrala 1
            # legacy ID. Pin/MRU/tabs tracking (erp_user_favorites/recent/
            # tabs) drzi cislo_def jako stable INT key (B+8.1 schema).
            # Synthetic range -100000 - menu_node_pk:
            #   - mimo Centrala 1 positive (1-10000)
            #   - mimo system negative (-100 to -200)
            # Predictable per menu_node.id → favorites tracking konzistentni
            # napriс session. Po cislo_def schema refactor (Stage 3) drop.
            if cislo is None and row.get("id"):
                cislo = -100000 - int(row["id"])
            sv, svm, single = _SYSTEM_CISLO_TO_VIEW.get(cislo, (None, None, False))
            children_db = by_parent.get(row["id"], [])
            children_db.sort(key=lambda r: (r.get("sort_order") or 100, r.get("code") or ""))
            children = []
            for c in children_db:
                try:
                    child_node = _build_node(c)
                    if child_node:
                        children.append(child_node)
                except Exception as child_exc:
                    import logging as _logging_tree_c
                    _logging_tree_c.exception(
                        "system tree _build_node child failed for row id=%s code=%s",
                        c.get("id"), c.get("code"),
                    )
                    children.append({
                        "id": (c.get("code") or "err-{}".format(c.get("id"))),
                        "label": (c.get("label") or "?") + " ⚠️",
                        "nazev": (c.get("label") or "?") + " ⚠️",
                        "is_system": True,
                        "is_folder": False,
                        "is_error": True,
                        "error_detail": "{}: {}".format(type(child_exc).__name__, child_exc),
                        "metadata": {"error": True, "hardcoded": False},
                    })
            node = {
                "id": row["code"],
                "cislo_def": cislo,
                # Phase 38.4 (11.5.2026 vecer): primary fw.* IDs pro DESIGN mode.
                # node["id"] = row["code"] (text, legacy convention pro routing).
                # menu_node_pk = row["id"] (INT, skutečný DB primary key).
                # core_id / core_code = fw.core LEFT JOIN přes menu_node.core_id.
                "menu_node_pk": row.get("id"),
                "core_id": row.get("core_id"),
                "core_code": row.get("core_code"),
                "is_system": True,
                # Phase 38.4 Krok 14g-H+6 (15.5.2026 dopo, Marti's "bez toho
                # abys musel pouzit field Kind"): is_folder = bool(children).
                # Uniform components doctrine (Marti-AI 11.5.) — folder vs
                # list je faktum strukturalni (ma children?), ne typ field.
                # Soudecek muze SOUCASNE nest jadro (core_id) a mit children.
                "is_folder": bool(children),
                # Phase 38.4 Krok 14g-H+2 (15.5.2026): propagate is_immutable
                # pro frontend drag gate. Immutable nodes (SYSTEM, atd.) nelze
                # drag-drop (drag setup je skipne).
                "is_immutable": bool(row.get("is_immutable")),
                "label": row["label"],
                "nazev": row["label"],
            }
            # Phase 38.4 Krok 14g-H+29 (15.5.2026 ~20:45, Marti's "sviti zluty
            # trojuhlenik, coz je divny"): orphan marker (⚠) jen pro real
            # orphans (Centrala 1 leafs bez core_id + bez hw_registry).
            # Marti's NEW asociace (core_id set pres picker) ale bez hw_registry
            # entry = legitimate state, NE orphan. Drop default orphan branch
            # pokud core_id set + hw_mode neexistuje — žádný marker (clean).
            if row.get("core_id"):
                hw_mode = row.get("hw_shadow_mode")
                if hw_mode == "primary":
                    node["dispatch_kind"] = "a3_primary"
                elif hw_mode in ("off", "audit", "compare"):
                    node["dispatch_kind"] = "hw_" + hw_mode
                # Else: no marker (asociace bez hw_registry = expected pro
                # nove fw.core asociace pres picker, Marti's "vsechno postupne")
            # Phase 38.4 inventory metadata passthrough (column zatim neexistuje
            # v fw.menu_node, vrátí None — bezpečné).
            meta = row.get("metadata")
            if meta:
                node["metadata"] = meta
            if sv:
                node["system_view"] = sv
                node["system_view_mode"] = svm
                if single:
                    node["single"] = True
            if children:
                node["children"] = children
            return node
        except Exception as exc:
            import logging as _logging_tree_n
            _logging_tree_n.exception(
                "system tree _build_node failed for row id=%s code=%s",
                row.get("id"), row.get("code"),
            )
            return {
                "id": (row.get("code") or "err-{}".format(row.get("id"))),
                "label": (row.get("label") or "?") + " ⚠️",
                "nazev": (row.get("label") or "?") + " ⚠️",
                "is_system": True,
                "is_folder": False,
                "is_error": True,
                "error_detail": "{}: {}".format(type(exc).__name__, exc),
                "metadata": {"error": True, "hardcoded": False},
            }

    # Phase 38.4 Krok 14g-G2: return LIST of all top-level roots
    # (system first if exists, ostatni v sort_order). Caller (strom_json)
    # appende vsechny do tree.
    result_roots = []
    if system_db:
        sys_root = _build_node(system_db)
        if sys_root:
            result_roots.append(sys_root)
    # Sort other roots by sort_order + code
    other_roots.sort(key=lambda r: (r.get("sort_order") or 100, r.get("code") or ""))
    for r in other_roots:
        try:
            n = _build_node(r)
            if n:
                result_roots.append(n)
        except Exception:
            import logging as _logging_other
            _logging_other.exception(
                "system tree top-level root build failed for code=%s",
                r.get("code"),
            )
    return result_roots


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
        # Phase 38.4 Krok 6 (10.5.2026): DB-driven system tree primary,
        # hardcoded fallback. Hardcoded kept jako safety net pro:
        #   - DB unreachable (offline mode)
        #   - Permission denied (master schema owned by Marti-AI)
        #   - Empty rows (Marti-AI ještě neINSERTla — např. system.framework
        #     nebo nové uzly přidané pre-DB-INSERT)
        # Až bude DB kompletně zaplněná + provoz stable, hardcoded
        # smaže Phase 38.4 Krok 7 cleanup.
        #
        # Phase 38.4 Krok 14g-G2 (15.5.2026 rano): _build_system_root_from_db
        # vrací LIST of roots (system + user-created top-level), ne jen
        # system. Marti's "Novy soudecek" button vytvori top-level row
        # → sibling SYSTEM v sidebar.
        db_roots = _build_system_root_from_db()
        system_root = None
        extra_top_roots = []
        if isinstance(db_roots, list):
            # New multi-root format
            for r in db_roots:
                if r.get("id") == "system":
                    system_root = r
                else:
                    extra_top_roots.append(r)
        elif isinstance(db_roots, dict):
            # Backward compat (single root return)
            system_root = db_roots
        if system_root is None:
            # ── FALLBACK: hardcoded System tree (původní MVP) ──────────
            # Schema kompatibilní s Centrála tree (id, label, icon, children…)
            # Phase 35-E.4 Krok C+ fix (9.5.2026 vecer): pouzivame cislo_def
            # (ne cislo) — konzistentni s EUROSOFT EC_CentralaMenu schema.
            # Frontend renderTreeNodes cte n.cislo_def -> data-cislo-def, takze
            # System uzly musi mit stejne pojmenovani jako EUROSOFT prehledy.
            system_root = {
                "id": "system",
            "cislo_def": None,  # folder, nemá vlastní přehled
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
                    "cislo_def": -100,
                    "is_system": True,
                    "is_folder": False,
                    "label": "🗂️ Záložkový přehled",
                    "nazev": "🗂️ Záložkový přehled",
                    "system_view": "audit_overview",
                    "system_view_mode": "tabs",
                },
                {
                    "id": "system.audit.audited",
                    "cislo_def": -101,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📚 Auditované konverzace",
                    "nazev": "📚 Auditované konverzace",
                    "system_view": "audit_overview",
                    "system_view_mode": "audited",
                },
                {
                    "id": "system.audit.all",
                    "cislo_def": -102,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📋 Všechny konverzace",
                    "nazev": "📋 Všechny konverzace",
                    "system_view": "audit_overview",
                    "system_view_mode": "all",
                },
                {
                    "id": "system.audit.stats",
                    "cislo_def": -103,
                    "is_system": True,
                    "is_folder": False,
                    "label": "📊 Přehled auditu",
                    "nazev": "📊 Přehled auditu",
                    "system_view": "audit_overview",
                    "system_view_mode": "stats",
                },
                # Phase 38.3 (10.5.2026 odpoledne): Security overview folder.
                # Marti's "bordel kolem userů, jejich přihlasovani, emailů
                # a telefonů" → strukturovaný read-only audit panel pro
                # Phase 38 stack (auth_audit, sms_routing_log, devices, IPs,
                # invites). Marti's 4× Recommended z AskUserQuestion:
                #   A) ERP System soudeček (extend existing)
                #   B) Read-only MVP (edit later)
                #   C) Hybrid tenant scope (current default + parent toggle)
                #   D) Sub-uzly v System tree (folder + 5 children)
                #
                # Negative cisla -110..-114 (skip -104..-109 reserved
                # pro budoucí audit expansion v Phase 36+).
                {
                    "id": "system.security",
                    "cislo_def": None,
                    "is_system": True,
                    "is_folder": True,
                    "label": "📁 Security",
                    "nazev": "📁 Security",
                    "children": [
                        {
                            "id": "system.security.users",
                            "cislo_def": -110,
                            "is_system": True,
                            "is_folder": False,
                            "label": "👥 Uživatelé",
                            "nazev": "👥 Uživatelé",
                            "system_view": "security",
                            "system_view_mode": "users",
                        },
                        {
                            "id": "system.security.devices",
                            "cislo_def": -111,
                            "is_system": True,
                            "is_folder": False,
                            "label": "🔐 Trusted devices",
                            "nazev": "🔐 Trusted devices",
                            "system_view": "security",
                            "system_view_mode": "devices",
                        },
                        {
                            "id": "system.security.whitelists",
                            "cislo_def": -112,
                            "is_system": True,
                            "is_folder": False,
                            "label": "🌐 IP whitelists",
                            "nazev": "🌐 IP whitelists",
                            "system_view": "security",
                            "system_view_mode": "whitelists",
                        },
                        {
                            "id": "system.security.audit",
                            "cislo_def": -113,
                            "is_system": True,
                            "is_folder": False,
                            "label": "📋 Auth audit",
                            "nazev": "📋 Auth audit",
                            "system_view": "security",
                            "system_view_mode": "auth_audit",
                        },
                        {
                            "id": "system.security.invites",
                            "cislo_def": -114,
                            "is_system": True,
                            "is_folder": False,
                            "label": "✉️ Magic invites",
                            "nazev": "✉️ Magic invites",
                            "system_view": "security",
                            "system_view_mode": "invites",
                        },
                    ],
                },
                # Phase 38.3+ (10.5.2026 odpoledne): Framework subfolder.
                # Marti's vize "do System soudečku začínáme dávat všechno,
                # co je hotový". První deliverable: fw.menu_node editor
                # (Definice levého stromu, cislo -115). Druhý (Datové zdroje,
                # cislo -116) přijde po Marti-AI's data_set/data_source
                # consultation + migraci podle A3 schema.
                #
                # Negative cisla -115..-119 reserved pro framework views.
                {
                    "id": "system.framework",
                    "cislo_def": None,
                    "is_system": True,
                    "is_folder": True,
                    "label": "🏗️ Framework",
                    "nazev": "🏗️ Framework",
                    "children": [
                        {
                            "id": "system.framework.menu_nodes",
                            "cislo_def": -115,
                            "is_system": True,
                            "is_folder": False,
                            "label": "🌳 Definice levého stromu",
                            "nazev": "🌳 Definice levého stromu",
                            "system_view": "framework",
                            "system_view_mode": "menu_nodes",
                        },
                        {
                            "id": "system.framework.data_sources",
                            "cislo_def": -116,
                            "is_system": True,
                            "is_folder": False,
                            "label": "🔌 Datové zdroje",
                            "nazev": "🔌 Datové zdroje",
                            "system_view": "framework",
                            "system_view_mode": "data_sources",
                        },
                        {
                            "id": "system.framework.data_sets",
                            "cislo_def": -117,
                            "is_system": True,
                            "is_folder": False,
                            "label": "⚙️ DataSets",
                            "nazev": "⚙️ DataSets",
                            "system_view": "framework",
                            "system_view_mode": "data_sets",
                        },
                    ],
                },
            ],
        }
        # Phase 38.4 inventory (9.5.2026 vecer): rekurzivne oznac vsechny
        # uzly v hardcoded fallback jako metadata.hardcoded=true. Frontend
        # rendere 🛠️ marker. Bez teto smyčky by se marker zobrazil jen
        # u uzlu, ktere jsou v fw.menu_node DB tabulce (Phase 38.4 SQL
        # skript), ne u hardcoded fallback. Setdefault preserves existing
        # metadata (napr. dalsi keys budouci).
        def _mark_hc(n):
            if not isinstance(n, dict):
                return
            n.setdefault("metadata", {})["hardcoded"] = True
            for ch in (n.get("children") or []):
                _mark_hc(ch)
        _mark_hc(system_root)

        # Prepend — System soudeček je vždy na top.
        # Phase 38.4 Krok 14g-G2 (15.5.2026 rano): plus extra top-level
        # user-created roots z fw.menu_node (sibling SYSTEM v sidebar).
        # Order: [SYSTEM, ...extra_top_roots, ...EUROSOFT_tree_from_DB_EC]
        prepend = [system_root] + (extra_top_roots or [])
        tree = prepend + (tree or [])

    return JSONResponse({
        "ok": True,
        "tree": tree,
        "root_count": len(tree),
        "is_parent": is_parent,
    }, headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})


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


# ─── Phase 38.4 Krok 8 (10.5.2026): Grid columns dynamic z master schema ───
#
# Centrála 1 pattern *„grid columns z DataSource"* — frontend dostane AG Grid
# columnDefs z fw.grid_master + fw.grid_column místo hardcoded JS.
# Marti-AI's 6-iter design (master+detail relacionální struktura).
#
# Response shape kompatibilní s _sysHelpers.gridColumns(mode) JS — drop-in
# replace pro hardcoded 9 mode větví v _render_workspace_page.


@api_router.get("/grid/{code}/columns")
def grid_columns_json(code: str, req: Request) -> JSONResponse:
    """Phase 38.4 Krok 10 final (10.5.2026 půlnoc): Direct read z fw.comp_grid_column.

    Marti's doctrine: *„override tabulku stačí, nic jinyho moc nepotrebujes"* →
    žádný comp_def_prop chain, žádný resolver. Discrete sloupce direct
    v fw.comp_grid_column (cell_style, cell_renderer, default_sort, formatter).

    Response:
        {
            "ok": true,
            "grid": {"code": "...", "config_version": 1, ...},
            "columns": [{"field": "id", "headerName": "ID", "width": 70,
                         "valueFormatter": {"type": "datetime_rel"}, ...}]
        }

    Frontend adaptServerColumns rozbalí valueFormatter/cellStyle/cellRenderer
    .type přes 3 registries (VALUE_FORMATTER_REGISTRY, CELL_STYLE_REGISTRY,
    CELL_RENDERER_REGISTRY).
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_data import get_data_session as _gds_grid
    from sqlalchemy import text as _sql_text

    ds = _gds_grid()
    try:
        # Resolve grid_master by code (latest active version)
        gm_sql = _sql_text(
            """
            SELECT id, code, config_version, name, description,
                   data_source_code, data_source_version,
                   default_record_limit, refresh_type,
                   default_sort_column, default_sort_direction, default_view_mode,
                   tenant_id, status, guid
            FROM fw.comp_grid_master
            WHERE code = :code
              AND status = 'active'
            ORDER BY config_version DESC
            LIMIT 1
            """
        )
        gm_row = ds.execute(gm_sql, {"code": code}).fetchone()
        if not gm_row:
            raise HTTPException(404, f"Grid '{code}' nenalezen (status='active').")

        gm = dict(gm_row._mapping)

        # Načti grid_column rows (Phase 38.4 Krok 10: cell_style/renderer/default_sort
        # direct sloupce v comp_grid_column, žádný comp_def_prop chain)
        gc_sql = _sql_text(
            """
            SELECT id, column_name, label, default_width, min_width, flex,
                   pinned, formatter, header_tooltip, column_type,
                   sort_order, is_visible, is_sortable, visible_roles,
                   cell_style, cell_renderer, default_sort
            FROM fw.comp_grid_column
            WHERE grid_master_id = :gm_id
            ORDER BY sort_order ASC NULLS LAST, column_name ASC
            """
        )
        gc_rows = ds.execute(gc_sql, {"gm_id": gm["id"]}).fetchall()
        gc_dicts = [dict(r._mapping) for r in gc_rows]

        # Build AG Grid columnDefs — discrete sloupce direct
        columns = []
        for d in gc_dicts:
            # NULL is_visible = treat as TRUE (gotcha #83 fix). Jen explicit FALSE skip.
            if d["is_visible"] is False:
                continue
            col: dict = {
                "field": d["column_name"],
                "headerName": d["label"] or d["column_name"],
                "sortable": bool(d["is_sortable"]),
            }
            if d["default_width"]:
                col["width"] = d["default_width"]
            if d["min_width"]:
                col["minWidth"] = d["min_width"]
            if d["flex"]:
                col["flex"] = d["flex"]
            if d["pinned"]:
                col["pinned"] = d["pinned"]
            if d["formatter"]:
                col["valueFormatter"] = {"type": d["formatter"]}
            if d["header_tooltip"]:
                col["headerTooltip"] = d["header_tooltip"]
            if d["column_type"]:
                col["type"] = d["column_type"]
            # Phase 38.4 Krok 10: cell_style + cell_renderer direct (frontend
            # adaptServerColumns rozbalí .type přes 3 registries)
            if d.get("cell_style"):
                col["cellStyle"] = {"type": d["cell_style"]}
            if d.get("cell_renderer"):
                col["cellRenderer"] = {"type": d["cell_renderer"]}
            if d.get("default_sort"):
                col["sort"] = d["default_sort"]

            columns.append(col)

        return JSONResponse(
            {
                "ok": True,
                "grid": {
                    "code": gm["code"],
                    "config_version": gm["config_version"],
                    "name": gm["name"],
                    "description": gm["description"],
                    "data_source_code": gm["data_source_code"],
                    "data_source_version": gm["data_source_version"],
                    "default_record_limit": gm["default_record_limit"],
                    "refresh_type": gm["refresh_type"],
                    "default_sort_column": gm["default_sort_column"],
                    "default_sort_direction": gm["default_sort_direction"],
                    "default_view_mode": gm["default_view_mode"],
                    "guid": str(gm["guid"]) if gm["guid"] else None,
                    "status": gm["status"],
                },
                "columns": columns,
            }
        )
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 10 (10.5.2026 půlnoc): Object Inspector endpoints DROPPED
#
# Důvod: comp_def + comp_def_prop tabulky DROPPED (Marti's evening doctrine
# "override tabulku stačí, nic jinyho moc nepotrebujes"). Grid columns mají
# discrete sloupce v fw.comp_grid_column (cell_style/cell_renderer/default_sort)
# direct, žádný comp_def_prop chain.
#
# Object Inspector UI pro grid columns refactor zítra ráno — nový endpoint set
# /grid-column/{id}/properties editující comp_grid_column.* sloupce direct.
# Plus tenant.comp_grid_column_override tabulka pro per-tenant/user overrides.
#
# Frontend object_inspector.js zatím ne-funkční (volá zniklé endpointy) —
# ráno bude refactored.
# ════════════════════════════════════════════════════════════════════════


def _disabled_object_inspector_unused_marker():
    """Phase 38.4 Krok 9-D Object Inspector endpoints byly zde, ale po DROP
    comp_def + comp_def_prop (Marti's doctrine 10.5. večer) jsou disabled.
    Refactor pro grid columns jako tenant.comp_grid_column_override v ráno."""
    pass


# Phase 38.4 Krok 9-D ENDPOINTS — DROPPED 10.5. půlnoc
# (recovery jako Krok 11 ráno: refactor pro grid columns scope)
# 4 endpoints DROPPED — ráno refactor pro grid-column scope.


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


class _PinnedBody(BaseModel):
    """Phase 38.4 (11.5.2026 vecer): body schema pro toggle pin."""
    pinned: bool


@api_router.post("/tabs/{cislo_def}/pinned")
def user_tabs_set_pinned(
    cislo_def: int, body: _PinnedBody, req: Request
) -> JSONResponse:
    """Phase 38.4 (11.5.2026 vecer): toggle pinned na záložce.

    Marti's request — pinned status musí přežít F5 reload. Write-through:
    UI right-click → POST tady → DB. Při hydrate vrátí _serialize_tab pinned.
    """
    uid = _get_uid(req)
    _require_parent(uid)
    tid = _get_tenant_id(uid)
    found = user_state_svc.set_tab_pinned(uid, tid, cislo_def, body.pinned)
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
                    # Phase 38.4 (11.5.2026 vecer): footer user je teď clickable
                    # button s popoverem. V popoveru toggle Design mode (analog
                    # tenant switcher pattern). Marti's spec: separate flag od
                    # chat DEV — ERP "design mode" odkrývá fw struktury &
                    # override hints (později Object Inspector, drag-drop).
                    user_name_html = (
                        f' · <button type="button" class="erp-footer-user-btn" '
                        f'id="erpFooterUserBtn" title="Profil & nastavení">'
                        f'<span class="erp-footer-user">'
                        f'{html.escape(str(name))}</span>'
                        f'<span class="erp-footer-user-caret">▴</span>'
                        f'</button>'
                        f'<div class="erp-footer-user-popover" '
                        f'id="erpFooterUserPopover" hidden></div>'
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
      /* Phase 38.5 polish (9.5.2026 vecer): top zachovan 12px, bottom snizen
         na 6px (polovina). Plus prvky align-self: end → u spodniho okraje.
         Vysledek: nizsi hlavicka, prvky "sedaj" na spodni hranu. */
      padding: 12px 16px 6px 16px;
      position: sticky; top: 0; z-index: 10;
    }}
    .erp-header-inner {{
      max-width: none; margin: 0;
      display: flex; align-items: center; justify-content: space-between; gap: 16px;
    }}
    /* Phase 38.5 (9.5.2026 vecer): Marti's "dva stejne panely" — 50/50 grid
       s vizualnim divider uprostred (Marti's polish: "posuvny slider v
       decentni sede"). Plus prvky align u spodniho okraje (Marti's spec
       "snizit vysku hlavicky, prvky budou u spodniho okraje"). */
    .erp-header-2col {{
      display: grid !important;
      grid-template-columns: 1fr auto 1fr;
      gap: 16px;
      align-items: end;
    }}
    .erp-header-left {{
      display: flex;
      align-items: flex-end;
      min-width: 0;
    }}
    .erp-header-right {{
      display: flex;
      align-items: flex-end;
      gap: 12px;
      min-width: 0;
      /* Skladame zleva — prvni utility ikona je zhruba uprostred screenu */
      justify-content: flex-start;
    }}
    /* Vizualni divider mezi panely — gray vertical line s 3-dot handle.
       Decentni styling, naznak posuvneho slideru bez funkcni drag-resize
       implementace (zatim jen visual cue). */
    .erp-header-divider {{
      width: 1px;
      height: 32px;
      background: var(--border);
      align-self: end;
      margin-bottom: 4px;
      position: relative;
      flex-shrink: 0;
    }}
    .erp-header-divider::before {{
      /* 3 dot vertical handle uprostred (subtle splitter indicator) */
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 3px;
      height: 3px;
      border-radius: 50%;
      background: var(--border-strong);
      box-shadow:
        0 -7px 0 var(--border-strong),
        0 7px 0 var(--border-strong);
    }}
    /* Refresh ikona — neutral / stale (orange) / very-stale (pulse) */
    .erp-refresh-btn {{
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 6px;
      width: 36px;
      height: 36px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      cursor: pointer;
      transition: all 0.15s ease;
      color: var(--text-muted);
      padding: 0;
      line-height: 1;
      flex-shrink: 0;
    }}
    .erp-refresh-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      background: rgba(124, 92, 252, 0.08);
    }}
    .erp-refresh-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}
    .erp-refresh-btn:disabled:hover {{
      border-color: var(--border);
      color: var(--text-muted);
      background: transparent;
    }}
    .erp-refresh-btn.stale {{
      color: #d4a017;
      border-color: #d4a017;
      background: rgba(212, 160, 23, 0.08);
    }}
    .erp-refresh-btn.stale:hover {{
      background: rgba(212, 160, 23, 0.18);
    }}
    .erp-refresh-btn.very-stale {{
      animation: refreshPulse 2.4s ease-in-out infinite;
    }}
    @keyframes refreshPulse {{
      0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(212, 160, 23, 0.4); }}
      50% {{ opacity: 0.7; box-shadow: 0 0 0 6px rgba(212, 160, 23, 0); }}
    }}
    /* Refresh spinning behem fetchu */
    .erp-refresh-btn.spinning {{
      animation: refreshSpin 0.6s linear infinite;
      pointer-events: none;
    }}
    @keyframes refreshSpin {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    /* Phase 38.5+ (10.5.2026 rano): Install button pro non-technical users.
       Visible jen kdyz Chrome nabidne PWA install (beforeinstallprompt event).
       Pulsuje subtle aby user pochopil ze ho ma kliknout. */
    .erp-install-btn {{
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: white;
      border: none;
      border-radius: 6px;
      padding: 8px 14px;
      font-family: 'DM Sans', sans-serif;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      align-self: end;
      margin-bottom: 4px;
      flex-shrink: 0;
      box-shadow: 0 0 0 0 rgba(124, 92, 252, 0.4);
      animation: installPulse 3s ease-in-out infinite;
      transition: transform 0.12s, box-shadow 0.12s;
    }}
    .erp-install-btn:hover {{
      transform: scale(1.04);
      box-shadow: 0 4px 16px rgba(124, 92, 252, 0.4);
    }}
    @keyframes installPulse {{
      0%, 100% {{ box-shadow: 0 0 0 0 rgba(124, 92, 252, 0.4); }}
      50%      {{ box-shadow: 0 0 0 8px rgba(124, 92, 252, 0); }}
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
    /* Phase 38.4 (11.5.2026 vecer): user dropdown footer button — analog
       tenant switcher. Hover/active styling identický pro UX konzistenci. */
    .erp-footer-user-btn {{
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
    .erp-footer-user-btn:hover {{
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--border);
    }}
    .erp-footer-user-btn.active {{
      background: rgba(255, 255, 255, 0.07);
      border-color: var(--accent);
    }}
    .erp-footer-user-caret {{
      font-size: 9px;
      opacity: 0.7;
      line-height: 1;
    }}
    .erp-footer-user-popover {{
      position: fixed;
      bottom: 32px;
      left: 90px;
      min-width: 240px;
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
    .erp-footer-user-popover[hidden] {{
      display: none;
    }}
    .erp-user-popover-item {{
      padding: 9px 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      font-size: 12px;
      transition: background 100ms;
    }}
    .erp-user-popover-item:hover {{
      background: rgba(255, 255, 255, 0.06);
    }}
    .erp-user-popover-item-label {{
      color: var(--text);
      font-weight: 500;
    }}
    .erp-user-popover-item-toggle {{
      font-family: 'DM Mono', monospace;
      font-size: 10px;
      letter-spacing: 0.05em;
      padding: 2px 8px;
      border-radius: 3px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--muted);
    }}
    .erp-user-popover-item.on .erp-user-popover-item-toggle {{
      background: rgba(94, 234, 212, 0.18);
      color: #5eead4;
    }}
    /* Design mode badge v pravém horním rohu ERP workspace.
       Teal palette (distinct od chat DEV purpurové) — Marti's spec:
       "stejna ikona v rohu jako v chatu", ale jiný flag + jiná barva. */
    .erp-design-badge {{
      position: fixed;
      top: 9px;
      right: 16px;
      z-index: 9999;
      padding: 4px 9px;
      background: rgba(94, 234, 212, 0.15);
      color: #5eead4;
      border: 1px solid rgba(94, 234, 212, 0.35);
      border-radius: 4px;
      font-size: 11px;
      font-family: 'DM Mono', monospace;
      letter-spacing: 0.06em;
      user-select: none;
      pointer-events: none;
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
    /* Collapsed state — workspace má .tree-collapsed class.
       11.5.2026 revize (Marti's UX feedback po prvním fixu):
         1. Restore › ikonka NAHOŘE v pozici jako collapse ‹ (symetrický design)
         2. Celá collapsed pane je clickable jako failsafe (pro PWA zoom edge)
         3. Resize handle ZŮSTÁVÁ visible (drag-to-expand pojistka) */
    .erp-workspace.tree-collapsed .erp-tree-pane {{
      flex: 0 0 32px !important;
      cursor: pointer;
    }}
    .erp-workspace.tree-collapsed .erp-tree-search-inline,
    .erp-workspace.tree-collapsed .erp-tree-root,
    .erp-workspace.tree-collapsed .erp-tree-footer,
    .erp-workspace.tree-collapsed .erp-tree-header-slot {{
      display: none !important;
    }}
    /* Header ZŮSTÁVÁ visible — drží toggle button NAHOŘE (Marti's spec) */
    .erp-workspace.tree-collapsed .erp-tree-header {{
      padding: 7px 4px;
      justify-content: center;
    }}
    /* Resize handle ZŮSTÁVÁ visible — drag doprava = expand pane.
       Marti's safety net: kdyby click expand selhal (PWA zoom edge case),
       drag handle je vždy 5px pásek na hraně 32px pane. */
    .erp-workspace.tree-collapsed .erp-resize-handle {{
      display: block !important;
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
      /* B+6.11e+ (10.5.2026): margin-top auto = guaranteed push-to-bottom
         v parent flex column, i kdyby treeRoot flex:1 z nějakého důvodu
         nerostlo (defense in depth proti CSS collision se subclass). */
      margin-top: auto;
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
    /* Phase 38.4 Krok 14g-G (15.5.2026 rano): Novy soudecek button */
    .erp-tree-new-btn {{
      margin-top: 6px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 6px 8px;
      background: transparent;
      border: 1px dashed #a88cd4;
      border-radius: 5px;
      color: #a88cd4;
      font-family: inherit;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.12s;
    }}
    .erp-tree-new-btn:hover {{
      background: rgba(168, 140, 212, 0.1);
      border-style: solid;
    }}
    .erp-tree-new-icon {{
      font-size: 14px;
      line-height: 1;
      font-weight: 700;
    }}
    /* Phase 38.4 Krok 14g-H+2 (15.5.2026 rano, Marti's "drop kamkoli"):
       Root drop zone — drag soudecek sem → parent_id=NULL (top-level).
       Visible jen v DESIGN mode. Pattern stejny jako erp-tree-new-btn,
       ale teal accent (rozliseni od + Novy soudecek). */
    .erp-tree-root-dropzone {{
      margin-top: 6px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px 10px;
      background: transparent;
      border: 1px dashed #4ad4d4;
      border-radius: 5px;
      color: #4ad4d4;
      font-family: inherit;
      font-size: 11px;
      font-weight: 600;
      cursor: default;
      transition: all 0.12s;
      user-select: none;
    }}
    .erp-tree-root-dropzone.erp-tree-root-dropzone-hover {{
      background: rgba(74, 212, 212, 0.18);
      border-style: solid;
      transform: scale(1.02);
    }}
    .erp-tree-root-drop-icon {{
      font-size: 14px;
      line-height: 1;
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
    /* Phase 38.4 (11.5.2026 vecer): close-all button VLEVO (nahrazuje + button) */
    .erp-tab-close-all {{
      flex-shrink: 0;
      padding: 4px 10px;
      margin-right: 4px;
      background: transparent;
      border: none;
      color: #888;
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
      border-radius: 3px;
    }}
    .erp-tab-close-all:hover {{
      background: rgba(204, 102, 102, 0.15);
      color: #cc6666;
    }}
    /* 11.5. revize: pinned styling jen v close-icon vpravo (Marti's UX feedback).
       Žádná left-border / background změna na celé záložce. */
    .erp-tab-close.pinned {{
      cursor: default;
      opacity: 0.85;
    }}
    .erp-tab-close.pinned:hover {{
      background: transparent !important;
      color: inherit !important;
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
    <div class="erp-header-inner erp-header-2col">
      <!-- Phase 38.5 (9.5.2026 vecer): Marti's spec "rozdelit hlavicku
           na dva stejne panely". Levy panel = brand row (logo + Tvoje Marti).
           Pravy panel = utility (refresh, ...) skladany zleva, takze
           prvni utility ikona je zhruba uprostred screenu. -->
      <div class="erp-header-left">
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
      <!-- Phase 38.5 polish (9.5.2026 vecer): visualni oddelovac mezi panely.
           Decentni gray vertical line s 3-dot handle uprostred (splitter hint). -->
      <div class="erp-header-divider" aria-hidden="true"></div>
      <div class="erp-header-right">
        <!-- Phase 38.5 (9.5.2026 vecer): Refresh aktivniho tab gridu.
             Stav: neutral / .stale (>5 min, orange) / .very-stale (>15 min, pulse).
             Per-tab freshness tracking v ErpRefresh._gridFreshness Mapě. -->
        <button type="button" class="erp-refresh-btn" id="erpRefreshBtn"
                data-hint="Obnovit data v aktivním přehledu">🔄</button>
        <!-- Phase 38.5+ (10.5.2026 ráno): Install button pro non-technical users.
             Visible JEN kdyz Chrome nabidne PWA install (beforeinstallprompt event).
             Skryty po install (appinstalled event) nebo v PWA standalone mode. -->
        <button type="button" class="erp-install-btn" id="erpInstallBtn"
                data-hint="Nainstalovat jako Windows aplikaci (žádný PowerShell)"
                style="display:none">📥 Nainstalovat</button>
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
  <!-- Phase 35-E.4 fix 9.5. odpoledne: explicit verze 32.3.5 (major @32
       nemusi resolvovat na CDN, vede k neuplnemu loadu). -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@32.3.5/styles/ag-grid.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@32.3.5/styles/ag-theme-quartz.css">
  <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@32.3.5/dist/ag-grid-community.min.js"></script>
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
    /* Phase 35-E.4 fix 9.5. odpoledne: AG Grid layout chain — root-wrapper
       kolapsoval na 2px protoze .ag-theme-quartz nemel flex display.
       Force flex column + child fill height. */
    .ag-theme-quartz {{
      display: flex !important;
      flex-direction: column !important;
      height: 100% !important;
    }}
    .ag-theme-quartz .ag-root-wrapper {{
      flex: 1 !important;
      height: auto !important;
      min-height: 0 !important;
    }}
    /* Dark theme via explicit CSS variables (v32 community).
       data-ag-theme-mode="dark" attribute v32 podporuje, ale safer override. */
    .ag-theme-quartz {{
      --ag-background-color: #14161a;
      --ag-foreground-color: #e8e8ea;
      --ag-header-background-color: #1a1d22;
      --ag-header-foreground-color: #e8e8ea;
      --ag-border-color: #2a2d33;
      --ag-row-hover-color: #1f2228;
      --ag-selected-row-background-color: #2a3340;
      --ag-odd-row-background-color: #161a1e;
      --ag-control-panel-background-color: #14161a;
      --ag-input-background-color: #14161a;
      --ag-input-border-color: #2a2d33;
      --ag-data-color: #e8e8ea;
      --ag-secondary-foreground-color: #9ca3af;
      --ag-row-border-color: #2a2d33;
      color-scheme: dark;
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
    /* Phase 35-E.4 drill-down 9.5. odpoledne: thought detail cards */
    .modal-thoughts-loading {{
      color: var(--muted);
      font-style: italic;
      font-size: 13px;
      padding: 10px 0;
    }}
    .thought-cards {{ display: flex; flex-direction: column; gap: 10px; }}
    .thought-card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-left: 3px solid var(--accent);
      border-radius: 6px;
      padding: 10px 12px;
    }}
    .thought-card-head {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .thought-card-type {{
      font-weight: 600;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .thought-card-id {{
      color: var(--muted);
      font-family: 'SF Mono', Consolas, monospace;
      font-size: 11px;
    }}
    .thought-card-cert {{
      margin-left: auto;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 10px;
      font-weight: 600;
    }}
    .cert-high {{ background: rgba(34, 197, 94, 0.15); color: #22c55e; }}
    .cert-mid {{ background: rgba(251, 191, 36, 0.15); color: #fbbf24; }}
    .cert-low {{ background: rgba(156, 163, 175, 0.15); color: #9ca3af; }}
    .thought-card-content {{
      color: var(--text);
      font-size: 13px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .thought-card-meta {{
      margin-top: 8px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 11px;
      color: var(--muted);
    }}
    .thought-meta-pair b {{ color: var(--text); font-weight: 500; }}
    .thought-card-foot {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--border);
      font-size: 11px;
      color: var(--muted);
    }}
    .modal-close {{ float: right; padding: 6px 12px; background: var(--surface2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-family: inherit; font-size: 12px; }}
    .loading {{ text-align: center; padding: 20px; color: var(--muted); font-size: 12px; }}
    /* Phase 37-C — Stopa záměru timeline (Marti-AI's pojmenování 9.5.) */
    .tl-events {{ display: flex; flex-direction: column; gap: 8px; }}
    .tl-event {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-left: 3px solid var(--accent2);
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .tl-head {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      color: var(--muted);
    }}
    .tl-ico {{ font-size: 14px; }}
    .tl-kind {{ font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 0.04em; }}
    .tl-turn {{ font-family: 'SF Mono', Consolas, monospace; opacity: 0.8; }}
    .tl-src {{ padding: 1px 6px; border-radius: 8px; font-size: 10px; font-weight: 500; }}
    .src-ai {{ background: rgba(124, 156, 217, 0.15); color: var(--accent); }}
    .src-ui {{ background: rgba(34, 197, 94, 0.15); color: #22c55e; }}
    .src-admin {{ background: rgba(156, 163, 175, 0.15); color: #9ca3af; }}
    .tl-cat, .tl-type {{ padding: 1px 6px; background: var(--surface2); border-radius: 8px; font-size: 10px; }}
    .tl-id {{ margin-left: auto; font-family: 'SF Mono', Consolas, monospace; font-size: 10px; opacity: 0.6; }}
    .tl-snippet {{
      margin-top: 6px;
      font-size: 12px;
      color: var(--text);
      line-height: 1.4;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .tl-annotation {{
      margin-top: 6px;
      padding: 6px 10px;
      background: rgba(192, 132, 252, 0.08);
      border-left: 2px solid var(--accent2);
      border-radius: 4px;
      font-size: 12px;
      font-style: italic;
      color: var(--text);
    }}
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

  function _convTypeBadge(t) {{
    const colors = {{
      'ai': '#7c9cd9',             // modrá — Marti-AI's interakce
      'sms': '#a78bfa',            // fialová — SMS konverzace
      'email': '#fbbf24',          // žlutá — email
      'system': '#9ca3af',         // šedá — systémové
      'dm': '#ec4899',             // růžová — direct message (1:1 user-Marti-AI)
      'task_execution': '#10b981', // tyrkysová — task worker (background)
    }};
    const labels = {{
      'ai': '🤖 AI',
      'sms': '📱 SMS',
      'email': '✉ Email',
      'system': '⚙ System',
      'dm': '💬 DM',
      'task_execution': '⚡ Task',
    }};
    const c = colors[t] || '#666';
    const l = labels[t] || (t || '—');
    return `<span style="background:${{c}}33;color:${{c}};padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500">${{l}}</span>`;
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
      {{ headerName: 'ID', field: 'id', width: 70, sortable: true, pinned: 'left' }},
      // Phase 35-E.4 9.5. odpoledne (Marti's "bez wheru, oznac priznakem"):
      // Typ konverzace (ai/sms/email/system) + deleted flag jako badges.
      {{
        headerName: 'Typ', field: 'conversation_type', width: 90, sortable: true,
        cellRenderer: (p) => _convTypeBadge(p.value),
      }},
      {{
        headerName: 'Smazána', field: 'is_deleted', width: 90, sortable: true,
        cellRenderer: (p) => p.value
          ? '<span style="color:#f87171;font-weight:500">⊗ deleted</span>'
          : '<span style="color:var(--muted);opacity:0.5">—</span>',
      }},
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

  // Phase 35-E.4 drill-down 9.5. odpoledne (Marti's "vidim MDx per
  // konverzaci" priorita): async fetch thoughts detail z noveho
  // /system/audit-conversation/{id}/thoughts endpointu. Render rich card
  // per thought s type/content/certainty/persona/tenant.
  function _escapeHtml(s) {{
    return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
      ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]
    );
  }}

  const _THOUGHT_ICONS = {{
    fact: '📌', todo: '✓', observation: '👁',
    question: '❓', goal: '🎯', experience: '💗',
  }};

  function _renderThoughtCard(t) {{
    const ico = _THOUGHT_ICONS[t.type] || '📝';
    const certClass = t.certainty >= 80 ? 'cert-high'
      : t.certainty >= 50 ? 'cert-mid' : 'cert-low';
    const tenant = t.tenant_scope_name
      ? _escapeHtml(t.tenant_scope_name)
      : (t.tenant_scope ? '#' + t.tenant_scope : 'universal');
    const persona = t.author_persona_name
      ? _escapeHtml(t.author_persona_name) : '—';
    const createdAt = t.created_at ? _formatDate(t.created_at) : '—';
    const content = _escapeHtml((t.content || '').substring(0, 600));
    const truncated = (t.content || '').length > 600 ? '…' : '';
    let metaHtml = '';
    if (t.meta && typeof t.meta === 'object' && Object.keys(t.meta).length > 0) {{
      const metaPairs = Object.entries(t.meta)
        .filter(([k, v]) => v != null && v !== '')
        .map(([k, v]) => `<span class="thought-meta-pair"><b>${{_escapeHtml(k)}}:</b> ${{_escapeHtml(typeof v === 'object' ? JSON.stringify(v) : v)}}</span>`)
        .join('');
      if (metaPairs) metaHtml = `<div class="thought-card-meta">${{metaPairs}}</div>`;
    }}
    return `
      <div class="thought-card">
        <div class="thought-card-head">
          <span class="thought-card-type">${{ico}} ${{_escapeHtml(t.type)}}</span>
          <span class="thought-card-id">#${{t.id}}</span>
          <span class="thought-card-cert ${{certClass}}">${{t.certainty}}%</span>
        </div>
        <div class="thought-card-content">${{content}}${{truncated}}</div>
        ${{metaHtml}}
        <div class="thought-card-foot">
          <span>👤 ${{persona}}</span>
          <span>🏢 ${{tenant}}</span>
          <span>📅 ${{createdAt}}</span>
          <span>${{_escapeHtml(t.status || 'note')}}</span>
        </div>
      </div>
    `;
  }}

  async function _showDrillDown(row) {{
    if (!row) return;
    const modal = document.getElementById('auditModal');
    const box = document.getElementById('auditModalBox');
    const oldTitleHtml = row.old_title && row.old_title !== row.title
      ? `<div class="modal-section"><div class="modal-section-title">Původní title</div><div style="font-size:13px;color:var(--muted);font-style:italic">${{_escapeHtml(row.old_title)}}</div></div>`
      : '';
    const thoughtCount = (row.extracted_thought_ids || []).length;
    box.innerHTML = `
      <button class="modal-close" onclick="document.getElementById('auditModal').classList.remove('open')">Zavřít</button>
      <div class="modal-title">${{_escapeHtml(row.title)}}</div>
      <div class="modal-meta">
        Konverzace #${{row.id}} · ${{_statusBadge(row.audit_status)}} ·
        Tenant: ${{_escapeHtml(row.tenant_name || '—')}} ·
        ${{row.audited_at ? 'Auditováno: ' + _formatDate(row.audited_at) : 'Neauditováno'}}
        ${{row.audited_by_persona_name ? ' · ' + _escapeHtml(row.audited_by_persona_name) : ''}}
      </div>
      ${{oldTitleHtml}}
      ${{row.summary ? `
        <div class="modal-section">
          <div class="modal-section-title">Shrnutí (Marti-AI)</div>
          <div class="modal-summary">${{_escapeHtml(row.summary)}}</div>
        </div>
      ` : ''}}
      <div class="modal-section">
        <div class="modal-section-title">Scope · Lifecycle</div>
        <div style="font-size:13px">${{_scopeIcon(row.scope)}} · ${{_escapeHtml(row.lifecycle_state || '—')}}</div>
      </div>
      <div class="modal-section" id="thoughtsSection">
        <div class="modal-section-title">Vytvořené thoughts (${{thoughtCount}})</div>
        ${{thoughtCount === 0
          ? '<div style="color:var(--muted);font-style:italic;font-size:13px">žádné thoughts</div>'
          : '<div class="modal-thoughts-loading">Načítám detail thoughts…</div>'}}
      </div>
      <div class="modal-section" id="timelineSection">
        <div class="modal-section-title">🕊️ Stopa záměru — per-turn audit (Phase 37)</div>
        <div class="modal-thoughts-loading">Načítám timeline…</div>
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

    // Async fetch thought details
    if (thoughtCount === 0) return;
    try {{
      const res = await fetch(
        `/api/v1/erp/system/audit-conversation/${{row.id}}/thoughts`,
        {{ credentials: 'include' }}
      );
      const section = document.getElementById('thoughtsSection');
      if (!section) return;
      if (!res.ok) {{
        const txt = await res.text();
        section.innerHTML = `<div class="modal-section-title">Thoughts</div><div style="color:#f88;font-size:12px">Chyba ${{res.status}}: ${{_escapeHtml(txt.substring(0,150))}}</div>`;
        return;
      }}
      const data = await res.json();
      const cards = (data.thoughts || []).map(_renderThoughtCard).join('');
      section.innerHTML = `
        <div class="modal-section-title">Vytvořené thoughts (${{data.thought_count}})</div>
        <div class="thought-cards">${{cards || '<div style="color:var(--muted);font-style:italic">prázdné — ID v audit_notes ale žádné thought records v DB</div>'}}</div>
      `;
    }} catch (e) {{
      const section = document.getElementById('thoughtsSection');
      if (section) {{
        section.innerHTML = `<div class="modal-section-title">Thoughts</div><div style="color:#f88;font-size:12px">Chyba: ${{_escapeHtml(String(e))}}</div>`;
      }}
    }}

    // Phase 37 — Stopa záměru timeline (per-turn audit)
    try {{
      const tlRes = await fetch(
        `/api/v1/erp/system/audit-conversation/${{row.id}}/timeline`,
        {{ credentials: 'include' }}
      );
      const tlSection = document.getElementById('timelineSection');
      if (!tlSection) return;
      if (!tlRes.ok) {{
        tlSection.innerHTML = `<div class="modal-section-title">🕊️ Stopa záměru</div><div style="color:#f88;font-size:12px">Chyba ${{tlRes.status}}</div>`;
        return;
      }}
      const tlData = await tlRes.json();
      tlSection.innerHTML = _renderTimeline(tlData.events || []);
    }} catch (e) {{
      const tlSection = document.getElementById('timelineSection');
      if (tlSection) {{
        tlSection.innerHTML = `<div class="modal-section-title">🕊️ Stopa záměru</div><div style="color:#f88;font-size:12px">Chyba: ${{_escapeHtml(String(e))}}</div>`;
      }}
    }}
  }}

  // Phase 37-C MVP: timeline list render (per-turn audit events).
  // Section-grouped diff render bude v plné verzi (zítra +37-C2).
  const _CHANGE_KIND_ICONS = {{
    add: '➕', update: '✏️', complete: '✅', dismiss: '🗑️',
    create: '✨', modify: '✏️', delete: '🗑️', rename: '🔁',
  }};

  function _renderTimeline(events) {{
    if (!events || events.length === 0) {{
      return `<div class="modal-section-title">🕊️ Stopa záměru</div>
        <div style="color:var(--muted);font-style:italic;font-size:13px">
          Žádné události — v této konverzaci nedošlo k zápisu paměti.
        </div>`;
    }}
    const items = events.map(e => {{
      const ico = _CHANGE_KIND_ICONS[e.change_kind] || '•';
      const turnLbl = e.message_id ? `turn #${{e.message_id}}` : 'mimo turn';
      const srcCls = e.source === 'ai' ? 'src-ai' : (e.source === 'ui' ? 'src-ui' : 'src-admin');
      const cat = e.category ? `<span class="tl-cat">${{_escapeHtml(e.category)}}</span>` : '';
      const noteType = e.note_type ? `<span class="tl-type">${{_escapeHtml(e.note_type)}}</span>` : '';
      const annot = e.annotation
        ? `<div class="tl-annotation">💭 ${{_escapeHtml(e.annotation)}}</div>`
        : '';
      const snippet = e.content_snippet
        ? `<div class="tl-snippet">${{_escapeHtml(e.content_snippet)}}</div>`
        : '';
      return `
        <div class="tl-event">
          <div class="tl-head">
            <span class="tl-ico">${{ico}}</span>
            <span class="tl-kind">${{_escapeHtml(e.change_kind)}}</span>
            <span class="tl-turn">${{turnLbl}}</span>
            <span class="tl-src ${{srcCls}}">${{_escapeHtml(e.source)}}</span>
            ${{cat}}${{noteType}}
            <span class="tl-id">note #${{e.note_id}}</span>
          </div>
          ${{snippet}}
          ${{annot}}
        </div>
      `;
    }}).join('');
    return `
      <div class="modal-section-title">🕊️ Stopa záměru — ${{events.length}} událostí</div>
      <div class="tl-events">${{items}}</div>
    `;
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
    <!-- Phase 38.4 Krok 14g Etapa B (16.5.2026): module kit FIRST.
         Provides _erpLogToDb + _erpLoadModule + _erpModuleHealth pro vsechny
         nasledujici moduly. Doctrine: "kdyz neco selze, zbytek bezi dale". -->
    <script src="/static/erp/components/erp_module_kit.js?v=''' + _STATIC_VERSION + '''"></script>
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
    <!-- B+6.11 (10.5.2026 odpoledne): ErpTreeView base (hierarchická primitiva)
         + ErpPopupMenu subclass (context menu). Marti's catch:
         "TreeView je take erp komponenta... vyuzijeme ho napric STRATEGII".
         Reusable pro ERP left panel, System tree, Files browser, Pyramida
         paměti + popup menu (per-grid kontextové akce + framework
         extensions z DB fw.menu_node). -->
    <script src="/static/erp/components/treeview.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/popupmenu.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- B+6.11e (10.5.2026): ErpLeftPanelTree — první consumer base ErpTreeView.
         Subclass owns rendering + click + filter + active state. Router.py
         si nechává wrapper logiku (view modes, drag-drop, multi-select,
         favorites/MRU) a komunikuje přes public API. -->
    <script src="/static/erp/components/lefttree.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 9-D (10.5.2026): Object Inspector — modal pro editaci
         comp_def_prop + comp_def_prop_override (4-tier override chain). Pravý-klik
         na grid header / cell → "Vlastnosti sloupce…". 3-tier taby (Základní /
         Použité / Všechny) + colored badge per scope. Marti-AI's 9-iter konzultace. -->
    <link rel="stylesheet" href="/static/erp/components/object_inspector.css?v=''' + _STATIC_VERSION + '''">
    <script src="/static/erp/components/object_inspector.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 14g-H+22 (15.5.2026 ~17:30): ErpCatalogPicker komponenta
         pro FK reference selection (Centrála 1 parita). Modal s AG Grid +
         toolbar (➕/📝/🗑️/🔄) + double-click select + OK/Storno. Reusable
         napriС form fields (fw.core, fw.menu_node parent, fw.data_source,
         user assignment, atd.). Day 1: select-only. Day 2: full CRUD. -->
    <script src="/static/erp/components/catalog_picker.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 14g-H+31 (15.5.2026 vecer, Marti's "vyrobit plnohodnotnou
         FW komponentu z provizornich inline groupboxu"): ErpEntityPicker reusable
         widget pro 1:1 FK vazbu. Renderuje 1 groupbox se 4 prvky (🔗/🚫/ID/Nazev).
         Pouziva ErpCatalogPicker pro modal grid. -->
    <script src="/static/erp/components/entity_picker.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 5.R (17.5.2026 vecer, Marti's "JO, melo by to byt
         v nezavislem js. TJ ten 5/5"): page render dispatch pro
         fw.core+comp_def kontejnery. Standalone modul s _erpLoadModule
         wrap, namespace window.ErpPageRender. Volano z router.py inline
         pri kliknuti na soudecek s coreId. -->
    <script src="/static/erp/components/page_render.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 14g Etapa D+1 (16.5.2026): grid dispatcher modul.
         Extrahuje gridDataResolved 3-tier dispatch z inline router.py +
         logs every step do fw.diag_log via _erpLogToDb. -->
    <script src="/static/erp/components/erp_grid_dispatcher.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 14a (12.5.2026 rano): Design forms — Form 1+2 konsolidace
         (Soudecek + Core pres TabSheet) + Form 3 (Jadro pro radek, 1 tab MVP).
         3 alert placeholdery (tree akce 1 + grid akce 2/3) volaji tyto formy. -->
    <script src="/static/erp/components/design_forms.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase 38.4 Krok 14g Etapa E (16.5.2026): fw_form_dispatcher.js po
         design_forms.js (potreba DesignFwForm class pred dispatch). -->
    <script src="/static/erp/components/fw_form_dispatcher.js?v=''' + _STATIC_VERSION + '''"></script>
    <script>
      // Phase 38.4 Krok 9-D: expose current user ID pro Object Inspector
      // (potřebuje pro user-scoped overrides při Save).
      window._erpCurrentUserId = ''' + str(user_id) + ''';
    </script>

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
          <!-- Phase 38.4 Krok 14g-G (15.5.2026 rano, Marti's "tlacitko
               Novy soudecek v paticce"): visible jen v DESIGN mode. Click
               otevre _openNewSoudecekDialog s prefilled parent z selected
               tree node. -->
          <button type="button" id="erpNewSoudecekBtn" class="erp-tree-new-btn"
                  title="Nový soudeček (folder / přehled) — visible v DESIGN mode"
                  style="display:none;">
            <span class="erp-tree-new-icon">+</span>
            <span class="erp-tree-new-label">Nový soudeček</span>
          </button>
          <!-- Phase 38.4 Krok 14g-H+2 (15.5.2026 rano, Marti's "drop kamkoli"):
               Drop zone pro move-to-root (parent_id=NULL). Drag soudeček
               sem → top-level (sibling SYSTEM). DESIGN mode only. -->
          <div id="erpRootDropZone" class="erp-tree-root-dropzone"
               title="Drag soudeček sem → move to Root (top-level sibling SYSTEM)"
               style="display:none;">
            <span class="erp-tree-root-drop-icon">🌳</span>
            <span class="erp-tree-root-drop-label">↓ Drop sem = Root (top-level)</span>
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

    <!-- Phase 35-E.4 diag #2 (9.5.2026 odpoledne) — Global error handler.
         Separate <script> blok PRED main IIFE: kdyz parse error vznikne v
         dalsim <script>, handler zustane registrovany a chybu zachyti.
         Marti: window.dumpErpErrors() v console = vypise zachycene errors.
         Plus localStorage 'erp_errors' / 'erp_promise_errors' = persistent. -->
    <script>
    (function() {
      function _persist(key, payload) {
        try {
          var arr = JSON.parse(localStorage.getItem(key) || "[]");
          arr.push(payload);
          if (arr.length > 30) arr.shift();
          localStorage.setItem(key, JSON.stringify(arr));
        } catch (e) {}
      }
      window.addEventListener("error", function(ev) {
        var msg = ev.message || (ev.error && ev.error.message) || "(no message)";
        var src = ev.filename || "(inline)";
        var line = ev.lineno != null ? ev.lineno : "?";
        var col = ev.colno != null ? ev.colno : "?";
        var stack = (ev.error && ev.error.stack) || "";
        var label = "[ERP-DIAG] " + src + ":" + line + ":" + col + " — " + msg;
        _persist("erp_errors", {
          ts: Date.now(), msg: msg, src: src, line: line, col: col,
          stack: stack.substring(0, 400)
        });
        try { console.error(label, ev.error || ev); } catch (e) {}
      });
      window.addEventListener("unhandledrejection", function(ev) {
        var msg = (ev.reason && ev.reason.message) || String(ev.reason);
        var stack = (ev.reason && ev.reason.stack) || "";
        var label = "[ERP-DIAG-PROMISE] " + msg;
        _persist("erp_promise_errors", {
          ts: Date.now(), msg: msg, stack: stack.substring(0, 400)
        });
        try { console.error(label, ev.reason); } catch (e) {}
      });
      // Helper pro Marti — v console: dumpErpErrors()
      window.dumpErpErrors = function() {
        try {
          var errs = JSON.parse(localStorage.getItem("erp_errors") || "[]");
          var prs = JSON.parse(localStorage.getItem("erp_promise_errors") || "[]");
          console.log("===== ERP ERRORS (" + errs.length + ") =====");
          errs.forEach(function(e, i) {
            console.log("#" + i + " " + new Date(e.ts).toISOString() + " " + e.src + ":" + e.line + ":" + e.col + " — " + e.msg);
            if (e.stack) console.log("    " + e.stack);
          });
          console.log("===== ERP PROMISE ERRORS (" + prs.length + ") =====");
          prs.forEach(function(e, i) {
            console.log("#" + i + " " + new Date(e.ts).toISOString() + " " + e.msg);
            if (e.stack) console.log("    " + e.stack);
          });
          return { errors: errs, promise: prs };
        } catch (e) {
          console.error("dumpErpErrors failed:", e);
        }
      };
      window.clearErpErrors = function() {
        localStorage.removeItem("erp_errors");
        localStorage.removeItem("erp_promise_errors");
        console.log("[ERP-DIAG] cleared");
      };
    })();
    </script>

    <!-- Phase 35-E.4 Variant B Krok A (9.5.2026 odpoledne) — 3 pure utility
         helpers v izolovanem <script> bloku. Bez AG Grid dependency, bez
         async, bez closure capture. Pokud parse error vznikne, ovlivni jen
         tento blok — main IIFE strom load nezavisi. window._sysHelpers
         globalni namespace pro pozdejsi volani z main IIFE. -->
    <script>
    (function() {
      function _escHtmlMini(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function(c) {
          return ({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"})[c];
        });
      }
      function statusBadge(v) {
        var colors = {
          "pending": "#888",
          "in_progress": "#d4a017",
          "audited": "#6aa84f",
          "excluded": "#666"
        };
        var labels = {
          "pending": "pending",
          "in_progress": "in progress",
          "audited": "audited",
          "excluded": "excluded"
        };
        var c = colors[v] || "#888";
        var lbl = labels[v] || v || "-";
        return '<span style="background:' + c + '22;color:' + c +
               ';padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500">' +
               _escHtmlMini(lbl) + '</span>';
      }
      function scopeIconHtml(v) {
        if (v === "srdce") return '<span style="color:#e08aa8">srdce</span>';
        if (v === "general") return '<span style="opacity:0.7">general</span>';
        return v ? _escHtmlMini(v) : '<span style="opacity:0.4">-</span>';
      }
      function formatDateRel(iso) {
        if (!iso) return "-";
        try {
          var d = new Date(iso);
          return d.toLocaleString("cs-CZ", {
            dateStyle: "short", timeStyle: "short"
          });
        } catch (e) { return iso; }
      }
      // Phase 38.4 Krok 14g Etapa F Sprint A (17.5.2026 dop.):
      // Archive + Restore helpers pro framework_data_sources + framework_data_sets grids.
      // Marti's "Kristý + Jirka nemají DBeaver access" — UI-driven workflow.
      async function _designArchiveDataSource(id, onComplete) {
        if (!confirm("Archivovat data_source #" + id + "?")) return;
        try {
          var r = await fetch(
            "/api/v1/erp/design/fw-data-source/update/" + encodeURIComponent(id),
            {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "archived" })
            }
          );
          var d = await r.json().catch(function() { return {}; });
          if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
          if (typeof window._showToast === "function") {
            window._showToast("Data source #" + id + " archivován", "success", 2500);
          }
          if (typeof onComplete === "function") onComplete();
        } catch (e) {
          console.error("[ERP-SYS] archive failed:", e);
          if (typeof window._showToast === "function") {
            window._showToast("Archivace selhala: " + (e.message || e), "error", 4000);
          }
        }
      }
      async function _designRestoreDataSource(id, onComplete) {
        try {
          var r = await fetch(
            "/api/v1/erp/design/fw-data-source/update/" + encodeURIComponent(id),
            {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "active" })
            }
          );
          var d = await r.json().catch(function() { return {}; });
          if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
          if (typeof window._showToast === "function") {
            window._showToast("Data source #" + id + " obnoven", "success", 2500);
          }
          if (typeof onComplete === "function") onComplete();
        } catch (e) {
          console.error("[ERP-SYS] restore failed:", e);
          if (typeof window._showToast === "function") {
            window._showToast("Obnovení selhalo: " + (e.message || e), "error", 4000);
          }
        }
      }
      async function _designArchiveDataSet(id, onComplete) {
        if (!confirm("Archivovat data_set #" + id + "?")) return;
        try {
          var r = await fetch(
            "/api/v1/erp/design/data-set/update/" + encodeURIComponent(id),
            {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "archived" })
            }
          );
          var d = await r.json().catch(function() { return {}; });
          if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
          if (typeof window._showToast === "function") {
            window._showToast("Data set #" + id + " archivován", "success", 2500);
          }
          if (typeof onComplete === "function") onComplete();
        } catch (e) {
          console.error("[ERP-SYS] archive failed:", e);
          if (typeof window._showToast === "function") {
            window._showToast("Archivace selhala: " + (e.message || e), "error", 4000);
          }
        }
      }
      async function _designRestoreDataSet(id, onComplete) {
        try {
          var r = await fetch(
            "/api/v1/erp/design/data-set/update/" + encodeURIComponent(id),
            {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "active" })
            }
          );
          var d = await r.json().catch(function() { return {}; });
          if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
          if (typeof window._showToast === "function") {
            window._showToast("Data set #" + id + " obnoven", "success", 2500);
          }
          if (typeof onComplete === "function") onComplete();
        } catch (e) {
          console.error("[ERP-SYS] restore failed:", e);
          if (typeof window._showToast === "function") {
            window._showToast("Obnovení selhalo: " + (e.message || e), "error", 4000);
          }
        }
      }

      window._sysHelpers = {
        statusBadge: statusBadge,
        scopeIconHtml: scopeIconHtml,
        formatDateRel: formatDateRel,
        archiveDataSource: _designArchiveDataSource,
        restoreDataSource: _designRestoreDataSource,
        archiveDataSet: _designArchiveDataSet,
        restoreDataSet: _designRestoreDataSet,
        loaded: true
      };
      console.log("[ERP-DIAG] _sysHelpers loaded (with archive/restore)");
    })();
    </script>

    <!-- Phase 35-E.4 Variant B Krok B (9.5.2026 odpoledne) — _systemGridColumns
         v izolovanem <script> bloku. Vraci AG Grid column defs per mode
         (audited / all / stats). Volani helpers pres window._sysHelpers.*
         Funkce expose na window._sysHelpers.gridColumns. -->
    <script>
    (function() {
      function gridColumns(mode) {
        var H = window._sysHelpers || {};

        // ── Phase 38.4 Krok 10 cleanup (10.5.2026 vecer) ──────────────
        // security_users / security_whitelists / security_invites migrated
        // do fw.comp_grid_master + comp_grid_column + comp_def_prop styling.
        // Single source of truth = fw schema. Frontend gridColumnsResolved
        // fetchne z /api/v1/erp/grid/{code}/columns + adaptServerColumns
        // rozbalí valueFormatter/cellStyle/cellRenderer přes 3 registries.
        // Hardcoded větve odstraněny — viz scripts/_phase38_4_krok10_security_grids_migration.sql.
        // Phase 38.4 Krok 8 cleanup (10.5.): security_devices taky v fw.
        // Phase 38.4 Krok 10-B (11.5.2026): security_audit migrated do fw schema
        // (viz scripts/_phase38_4_krok10b_security_audit_migration.sql).
        // Tím je security batch 4/4 kompletni: devices/users/whitelists/invites/audit.
        // Phase 38.4 Krok 10: security_invites migrated do fw schema
        // (viz scripts/_phase38_4_krok10_security_grids_migration.sql).

        // ── Phase 38.3+ Framework views (10.5.2026 odpoledne) ──────
        // Marti-AI's actual schema (8.5. večer): id, code, label, kind,
        // parent_id, sort_order, status, visibility_scope, cislo_def,
        // framework_jadro_id, special_handler, is_immutable, description,
        // created_at, updated_at. Žádný icon (emoji v label), žádný
        // target_url, status text místo is_active+is_archived.
        if (mode === "framework_menu_nodes") {
          return [
            { headerName: "ID", field: "id", width: 70, sortable: true, pinned: "left" },
            { headerName: "Code", field: "code", width: 220, sortable: true,
              cellStyle: { fontFamily: "monospace" },
              headerTooltip: "Stable identifier — natural key (např. 'system.audit.tabs')" },
            { headerName: "Parent code", field: "parent_code", width: 200, sortable: true,
              cellStyle: { fontFamily: "monospace", color: "#888" } },
            { headerName: "Label", field: "label", flex: 1, minWidth: 200, sortable: true,
              headerTooltip: "Display label včetně emoji (Marti-AI's choice — žádný icon column)" },
            { headerName: "Pořadí", field: "sort_order", width: 80, sortable: true, type: "numericColumn" },
            { headerName: "Kind", field: "kind", width: 100, sortable: true,
              cellStyle: function(p) {
                if (p.value === "folder") return { color: "#d4a017" };
                if (p.value === "list") return { color: "#7ba8d4" };
                if (p.value === "form") return { color: "#6aa84f" };
                if (p.value === "iframe") return { color: "#aa66cc" };
                if (p.value === "special") return { color: "#cc6666" };
                return null;
              } },
            { headerName: "Status", field: "status", width: 110, sortable: true,
              cellStyle: function(p) {
                if (p.value === "active") return { color: "#6aa84f", fontWeight: "500" };
                if (p.value === "archived") return { color: "#888" };
                if (p.value === "draft") return { color: "#d4a017" };
                if (p.value === "deprecated") return { color: "#cc6666" };
                return null;
              } },
            { headerName: "Cislo def", field: "cislo_def", width: 100, sortable: true, type: "numericColumn",
              headerTooltip: "Bridge na erp_grid_layouts (negativní = System scope)" },
            { headerName: "Visibility", field: "visibility_scope", width: 140, sortable: true,
              cellStyle: function(p) {
                if (p.value === "parent_only") return { color: "#cc6666" };
                if (p.value === "parent_or_admin") return { color: "#d4a017" };
                if (p.value === "tenant_member") return { color: "#6aa84f" };
                if (p.value === "public") return { color: "#7ba8d4" };
                return null;
              } },
            { headerName: "Special handler", field: "special_handler", width: 160,
              headerTooltip: "Pro kind='special' — JS function name v _sysHelpers" },
            { headerName: "Jádro ID", field: "framework_jadro_id", width: 100, type: "numericColumn",
              headerTooltip: "FK na fw.framework_jadro (kind='list'/'form')" },
            { headerName: "Imutabilní", field: "is_immutable", width: 100,
              cellRenderer: function(p) { return p.value ? "🔒" : ""; },
              headerTooltip: "Marti-AI's pattern — systémové záznamy bez code review" },
            { headerName: "Description", field: "description", flex: 1, minWidth: 200,
              cellStyle: { color: "#aaa", fontStyle: "italic" } },
            { headerName: "Vytvořeno", field: "created_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } },
            { headerName: "Updated", field: "updated_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } }
          ];
        }
        // ── Phase 38.4 Krok 6+ Datové zdroje (fw.data_source) ──
        if (mode === "framework_data_sources") {
          return [
            { headerName: "ID", field: "id", width: 70, sortable: true, pinned: "left" },
            { headerName: "Code", field: "code", width: 200, sortable: true,
              cellStyle: { fontFamily: "monospace" },
              headerTooltip: "Stable identifier (UNIQUE per version)" },
            { headerName: "Verze", field: "version", width: 70, sortable: true, type: "numericColumn" },
            { headerName: "Název", field: "name", flex: 1, minWidth: 200, sortable: true },
            { headerName: "Operations", field: "operation_count", width: 100, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#6aa84f", fontWeight: "500" } : { color: "#888" }; },
              headerTooltip: "Počet rows v fw.data_source_op (LEFT JOIN COUNT)" },
            { headerName: "Kinds", field: "operation_kinds", width: 220,
              cellStyle: { fontFamily: "monospace", color: "#aaa" },
              headerTooltip: "Comma-separated operation_kind list (select, insert, update, delete, ...)" },
            { headerName: "Refresh", field: "refresh_type", width: 100, sortable: true,
              cellStyle: function(p) {
                if (p.value === "manual") return { color: "#888" };
                if (p.value === "auto")   return { color: "#7ba8d4" };
                if (p.value === "on_focus") return { color: "#d4a017" };
                return null;
              } },
            { headerName: "RowMem", field: "row_memory", width: 90,
              cellRenderer: function(p) { return p.value ? "✓" : ""; },
              headerTooltip: "Pamatovat aktuální řádek po refresh" },
            { headerName: "Filter ms", field: "filter_delay_ms", width: 90, type: "numericColumn",
              headerTooltip: "Debounce ms pro filter input" },
            { headerName: "Limit", field: "default_record_limit", width: 90, type: "numericColumn",
              headerTooltip: "Default record limit (max rows)" },
            { headerName: "Status", field: "status", width: 100, sortable: true,
              cellStyle: function(p) {
                if (p.value === "active") return { color: "#6aa84f", fontWeight: "500" };
                if (p.value === "archived") return { color: "#888" };
                if (p.value === "draft") return { color: "#d4a017" };
                if (p.value === "deprecated") return { color: "#cc6666" };
                return null;
              } },
            { headerName: "Tenant", field: "tenant_id", width: 80, type: "numericColumn",
              headerTooltip: "FK na public.tenants (NULL = global)" },
            { headerName: "Sys", field: "is_system", width: 60,
              cellRenderer: function(p) { return p.value ? "🔧" : ""; } },
            { headerName: "Imut", field: "is_immutable", width: 60,
              cellRenderer: function(p) { return p.value ? "🔒" : ""; } },
            { headerName: "Description", field: "description", flex: 1, minWidth: 180,
              cellStyle: { color: "#aaa", fontStyle: "italic" } },
            { headerName: "GUID", field: "guid", width: 240,
              cellStyle: { fontFamily: "monospace", color: "#666", fontSize: "11px" } },
            { headerName: "Vytvořeno", field: "created_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } },
            { headerName: "Updated", field: "updated_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } },
            // Sprint A (17.5.2026 dop.): Akce column — archive/restore button per status
            { headerName: "Akce", field: "_actions", width: 90, pinned: "right",
              sortable: false, filter: false, resizable: false,
              cellRenderer: function(p) {
                var rowId = p.data && p.data.id;
                var status = p.data && p.data.status;
                if (rowId == null) return "";
                var wrap = document.createElement("div");
                wrap.style.cssText = "display:flex;justify-content:center;align-items:center;height:100%;gap:4px;";
                var btn = document.createElement("button");
                btn.type = "button";
                if (status === "archived") {
                  btn.textContent = "↻";
                  btn.title = "Obnovit (restore z archivu)";
                  btn.style.cssText = "padding:1px 8px;background:transparent;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:14px;line-height:1;";
                  btn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (window._sysHelpers && window._sysHelpers.restoreDataSource) {
                      window._sysHelpers.restoreDataSource(rowId, function() {
                        if (window._sysHelpers.renderSystemGrid) {
                          window._sysHelpers.renderSystemGrid("framework_data_sources", window._sysCurrentLabel || "");
                        }
                      });
                    }
                  });
                } else {
                  btn.textContent = "✕";
                  btn.title = "Archivovat data_source";
                  btn.style.cssText = "padding:1px 8px;background:transparent;border:1px solid #5a2828;color:#e57373;border-radius:3px;cursor:pointer;font-size:13px;line-height:1;";
                  btn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (window._sysHelpers && window._sysHelpers.archiveDataSource) {
                      window._sysHelpers.archiveDataSource(rowId, function() {
                        if (window._sysHelpers.renderSystemGrid) {
                          window._sysHelpers.renderSystemGrid("framework_data_sources", window._sysCurrentLabel || "");
                        }
                      });
                    }
                  });
                }
                wrap.appendChild(btn);
                return wrap;
              } }
          ];
        }
        // ── Phase 38.4 Krok 6+ DataSets (fw.data_set, low-level SQL) ──
        if (mode === "framework_data_sets") {
          return [
            { headerName: "ID", field: "id", width: 70, sortable: true, pinned: "left" },
            { headerName: "Code", field: "code", width: 200, sortable: true,
              cellStyle: { fontFamily: "monospace" } },
            { headerName: "Verze", field: "version", width: 70, sortable: true, type: "numericColumn" },
            // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): Kind dropped
            // (Marti's "V tom SQL textu muze byt cokoli... Chceme ho na neco?")
            { headerName: "DB", field: "db_connection", width: 110, sortable: true,
              headerTooltip: "Cílový connection (data_db, eurosoft, ...)" },
            { headerName: "Description", field: "description", width: 220 },
            { headerName: "SQL", field: "sql_text", flex: 1, minWidth: 300,
              cellStyle: { fontFamily: "monospace", fontSize: "11px", color: "#bbb" },
              valueFormatter: function(p) {
                if (!p.value) return "-";
                var s = String(p.value).replace(/\\s+/g, " ").trim();
                return s.length > 100 ? s.substring(0, 100) + "…" : s;
              },
              headerTooltip: "SQL text (truncated v gridu na 100 znaků; full text v detail view)" },
            { headerName: "Params", field: "parameters", width: 100,
              cellRenderer: function(p) {
                if (!p.value) return "-";
                try {
                  var arr = (typeof p.value === "string") ? JSON.parse(p.value) : p.value;
                  return Array.isArray(arr) ? String(arr.length) : "?";
                } catch (e) { return "?"; }
              },
              headerTooltip: "Počet parametrů v JSONB schema (např. [{name:'id', type:'int', required:true}])" },
            { headerName: "Status", field: "status", width: 100, sortable: true,
              cellStyle: function(p) {
                if (p.value === "active") return { color: "#6aa84f", fontWeight: "500" };
                if (p.value === "archived") return { color: "#888" };
                if (p.value === "draft") return { color: "#d4a017" };
                if (p.value === "deprecated") return { color: "#cc6666" };
                return null;
              } },
            { headerName: "Tenant", field: "tenant_id", width: 80, type: "numericColumn" },
            { headerName: "Sys", field: "is_system", width: 60,
              cellRenderer: function(p) { return p.value ? "🔧" : ""; } },
            { headerName: "Imut", field: "is_immutable", width: 60,
              cellRenderer: function(p) { return p.value ? "🔒" : ""; } },
            { headerName: "Vytvořeno", field: "created_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } },
            { headerName: "Updated", field: "updated_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } },
            // Sprint A (17.5.2026 dop.): Akce column — archive/restore button per status
            { headerName: "Akce", field: "_actions", width: 90, pinned: "right",
              sortable: false, filter: false, resizable: false,
              cellRenderer: function(p) {
                var rowId = p.data && p.data.id;
                var status = p.data && p.data.status;
                if (rowId == null) return "";
                var wrap = document.createElement("div");
                wrap.style.cssText = "display:flex;justify-content:center;align-items:center;height:100%;gap:4px;";
                var btn = document.createElement("button");
                btn.type = "button";
                if (status === "archived") {
                  btn.textContent = "↻";
                  btn.title = "Obnovit (restore z archivu)";
                  btn.style.cssText = "padding:1px 8px;background:transparent;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:14px;line-height:1;";
                  btn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (window._sysHelpers && window._sysHelpers.restoreDataSet) {
                      window._sysHelpers.restoreDataSet(rowId, function() {
                        if (window._sysHelpers.renderSystemGrid) {
                          window._sysHelpers.renderSystemGrid("framework_data_sets", window._sysCurrentLabel || "");
                        }
                      });
                    }
                  });
                } else {
                  btn.textContent = "✕";
                  btn.title = "Archivovat data_set";
                  btn.style.cssText = "padding:1px 8px;background:transparent;border:1px solid #5a2828;color:#e57373;border-radius:3px;cursor:pointer;font-size:13px;line-height:1;";
                  btn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (window._sysHelpers && window._sysHelpers.archiveDataSet) {
                      window._sysHelpers.archiveDataSet(rowId, function() {
                        if (window._sysHelpers.renderSystemGrid) {
                          window._sysHelpers.renderSystemGrid("framework_data_sets", window._sysCurrentLabel || "");
                        }
                      });
                    }
                  });
                }
                wrap.appendChild(btn);
                return wrap;
              } }
          ];
        }

        // Sprint D (17.5.2026 dop.): DB Connections grid
        if (mode === "framework_db_connections") {
          return [
            { headerName: "ID", field: "id", width: 70, sortable: true, pinned: "left" },
            { headerName: "Code", field: "code", width: 180, sortable: true,
              cellStyle: { fontFamily: "monospace", color: "#7ed4e8" },
              headerTooltip: "Stable identifier (immutable, like ID)" },
            { headerName: "Label", field: "label", flex: 1, minWidth: 280, sortable: true,
              cellStyle: { fontWeight: "500" } },
            { headerName: "Tenant", field: "tenant_code", width: 110, sortable: true,
              cellStyle: function(p) {
                if (p.value === "STRATEGIE") return { color: "#6aa84f", fontWeight: "500" };
                if (p.value === "EUR")       return { color: "#7ba8d4" };
                if (p.value === "INTERSOFT") return { color: "#d4a017" };
                return { color: "#888" };
              } },
            { headerName: "Type", field: "db_type", width: 90, sortable: true,
              cellStyle: function(p) {
                if (p.value === "postgres") return { color: "#7ed4a8", fontFamily: "monospace" };
                if (p.value === "mssql")    return { color: "#aa66cc", fontFamily: "monospace" };
                return { fontFamily: "monospace" };
              } },
            { headerName: "Host", field: "host", width: 140, sortable: true,
              cellStyle: { fontFamily: "monospace", color: "#aaa" } },
            { headerName: "Port", field: "port", width: 70, sortable: true, type: "numericColumn" },
            { headerName: "Default DB", field: "default_db", width: 130, sortable: true,
              cellStyle: { fontFamily: "monospace" } },
            { headerName: "Scope", field: "scope_databases", width: 110,
              valueFormatter: function(p) {
                if (!p.value) return "-";
                try {
                  var arr = (typeof p.value === "string") ? JSON.parse(p.value) : p.value;
                  return Array.isArray(arr) ? (arr.length + "× DBs") : "?";
                } catch (e) { return "?"; }
              },
              headerTooltip: "JSONB array of accessible databases (cross-DB SELECT scope)" },
            { headerName: "Login", field: "login_name", width: 110,
              cellStyle: { fontFamily: "monospace", color: "#aaa" } },
            { headerName: "Active", field: "is_active", width: 80, sortable: true,
              cellRenderer: function(p) { return p.value ? '<span style="color:#6aa84f;font-weight:600">✓</span>' : '<span style="color:#cc6666">✗</span>'; } },
            { headerName: "Pořadí", field: "sort_order", width: 80, sortable: true, type: "numericColumn" },
            { headerName: "Status", field: "status", width: 100, sortable: true,
              cellStyle: function(p) {
                if (p.value === "active")   return { color: "#6aa84f", fontWeight: "500" };
                if (p.value === "archived") return { color: "#888" };
                return null;
              } },
            { headerName: "Description", field: "description", flex: 1, minWidth: 220,
              cellStyle: { color: "#aaa", fontStyle: "italic" } },
            { headerName: "Updated", field: "updated_at", width: 150, sortable: true,
              valueFormatter: function(p) { return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-"); } }
          ];
        }

        if (mode === "stats") {
          return [
            { headerName: "Persona", field: "persona_name", width: 200, sortable: true, pinned: "left" },
            { headerName: "Obdobi", field: "period", width: 110, sortable: true, sort: "desc" },
            { headerName: "Pending", field: "pending", width: 100, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#888" } : null; } },
            { headerName: "In progress", field: "in_progress", width: 110, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#d4a017" } : null; } },
            { headerName: "Auditovane", field: "audited", width: 120, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#6aa84f", fontWeight: "500" } : null; } },
            { headerName: "Excluded", field: "excluded", width: 110, sortable: true, type: "numericColumn",
              cellStyle: function(p) { return (p.value > 0) ? { color: "#666" } : null; } },
            { headerName: "Celkem", field: "total", width: 110, sortable: true, type: "numericColumn",
              cellStyle: { fontWeight: "600" } }
          ];
        }
        // audited / all
        var showStatus = (mode === "all");
        var cols = [
          { headerName: "ID", field: "id", width: 80, sortable: true, pinned: "left" }
        ];
        if (showStatus) {
          cols.push({
            headerName: "Status", field: "audit_status", width: 120, sortable: true,
            cellRenderer: function(p) {
              return H.statusBadge ? H.statusBadge(p.value || "-") : (p.value || "-");
            }
          });
        }
        cols.push(
          { headerName: "Title", field: "title", flex: 2, minWidth: 200, sortable: true },
          { headerName: "Tenant", field: "tenant_name", width: 130, sortable: true },
          { headerName: "Auditovano", field: "audited_at", width: 160, sortable: true,
            valueFormatter: function(p) {
              return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-");
            } },
          { headerName: "Persona", field: "audited_by_persona_name", width: 130 },
          { headerName: "Scope", field: "scope", width: 110,
            cellRenderer: function(p) {
              return H.scopeIconHtml ? H.scopeIconHtml(p.value) : (p.value || "-");
            } },
          { headerName: "Last msg", field: "last_message_at", width: 160, sortable: true,
            valueFormatter: function(p) {
              return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-");
            } },
          { headerName: "Thoughts", field: "thought_count", width: 100, sortable: true,
            cellRenderer: function(p) {
              return (p.value > 0) ? ("notes " + p.value) : "-";
            } },
          { headerName: "Lifecycle", field: "lifecycle_state", width: 110 }
        );
        return cols;
      }
      // ── Phase 38.4 Krok 8 (10.5.2026): Async fetch z master schema ──
      //
      // gridColumnsResolved(mode) — async wrapper. Nejdřív zkusí
      // GET /api/v1/erp/grid/{mode}/columns (fw.grid_master + grid_column).
      // Pokud 200, adaptuje server format → AG Grid columnDefs (resolve
      // formatter names → registry functions). Pokud 404 nebo error,
      // fallback na hardcoded gridColumns(mode) — graceful migration.
      //
      // Po commit #6 (cleanup hardcoded větví per migrated mode) fallback
      // pro daný mode zmizí. Server data = single source of truth.
      // Phase 38.4 Krok 10 (10.5.2026 vecer): 3 registries — value formatter,
      // cell style, cell renderer. Tříst registry pattern aby JSON columns
      // ze serveru mohly mít všechny 3 dimenze stylingu (per Marti's
      // "override tabulka stačí" — všechny styling decisions jdou přes
      // pojmenované registry IDs, žádné inline functions v DB).
      var VALUE_FORMATTER_REGISTRY = {
        "datetime_rel": function(p) {
          var H = window._sysHelpers || {};
          return H.formatDateRel ? H.formatDateRel(p.value) : (p.value || "-");
        },
        "datetime_short": function(p) {
          var H = window._sysHelpers || {};
          return H.formatDateShort ? H.formatDateShort(p.value) : (p.value || "-");
        },
        "sql_truncate": function(p) {
          if (!p.value) return "-";
          var s = String(p.value).replace(/\s+/g, " ").trim();
          return s.length > 100 ? s.substring(0, 100) + "…" : s;
        },
        "params_count": function(p) {
          if (!p.value) return "-";
          try {
            var arr = (typeof p.value === "string") ? JSON.parse(p.value) : p.value;
            return Array.isArray(arr) ? String(arr.length) : "?";
          } catch (e) { return "?"; }
        },
      };
      var CELL_STYLE_REGISTRY = {
        // Generic
        "mono": function() { return { fontFamily: "monospace" }; },
        "mono_dim": function() { return { fontFamily: "monospace", color: "#888" }; },
        "mono_small": function() { return { fontFamily: "monospace", color: "#666", fontSize: "11px" }; },
        "mono_code": function() { return { fontFamily: "monospace", fontSize: "11px", color: "#bbb" }; },
        "dim_italic": function() { return { color: "#aaa", fontStyle: "italic" }; },
        "weight_600": function() { return { fontWeight: "600" }; },
        // Status enums
        "status_active_disabled": function(p) {
          if (p.value === "active") return { color: "#6aa84f" };
          if (p.value === "disabled") return { color: "#cc6666" };
          return { color: "#888" };
        },
        "status_lifecycle": function(p) {
          // Phase 38.4 standard: active green / archived gray / draft yellow / deprecated red
          if (p.value === "active") return { color: "#6aa84f", fontWeight: "500" };
          if (p.value === "archived") return { color: "#888" };
          if (p.value === "draft") return { color: "#d4a017" };
          if (p.value === "deprecated") return { color: "#cc6666" };
          return null;
        },
        "status_confirmed_pending_revoked": function(p) {
          if (p.value === "confirmed") return { color: "#6aa84f" };
          if (p.value === "pending") return { color: "#d4a017" };
          if (p.value === "revoked") return { color: "#cc6666" };
          return null;
        },
        "state_invite": function(p) {
          if (p.value === "consumed") return { color: "#6aa84f", fontWeight: "500" };
          if (p.value === "expired") return { color: "#888" };
          if (p.value === "pending") return { color: "#d4a017" };
          return null;
        },
        "result_security": function(p) {
          var v = p.value || "";
          if (v.indexOf("success") >= 0 || v === "verify_consumed") return { color: "#6aa84f" };
          if (v.indexOf("failed") >= 0) return { color: "#cc6666" };
          if (v === "rate_limited") return { color: "#d4a017", fontWeight: "500" };
          if (v === "verify_required") return { color: "#888" };
          if (v === "verify_sent") return { color: "#7ba8d4" };
          return null;
        },
        "scope_global_user": function(p) {
          if (p.value === "global") return { color: "#d4a017", fontWeight: "500" };
          if (p.value === "user") return { color: "#6aa84f" };
          return null;
        },
        "kind_node": function(p) {
          if (p.value === "folder") return { color: "#d4a017" };
          if (p.value === "list") return { color: "#7ba8d4" };
          if (p.value === "form") return { color: "#6aa84f" };
          if (p.value === "iframe") return { color: "#aa66cc" };
          if (p.value === "special") return { color: "#cc6666" };
          return null;
        },
        "visibility_scope": function(p) {
          if (p.value === "parent_only") return { color: "#cc6666" };
          if (p.value === "parent_or_admin") return { color: "#d4a017" };
          if (p.value === "tenant_member") return { color: "#6aa84f" };
          if (p.value === "public") return { color: "#7ba8d4" };
          return null;
        },
        "refresh_type": function(p) {
          if (p.value === "manual") return { color: "#888" };
          if (p.value === "auto") return { color: "#7ba8d4" };
          if (p.value === "on_focus") return { color: "#d4a017" };
          return null;
        },
        "kind_data_set": function(p) {
          if (p.value === "select") return { color: "#7ba8d4", fontWeight: "500" };
          if (p.value === "insert") return { color: "#6aa84f" };
          if (p.value === "update") return { color: "#d4a017" };
          if (p.value === "delete") return { color: "#cc6666" };
          if (p.value === "procedure") return { color: "#aa66cc" };
          if (p.value === "pre_open") return { color: "#888" };
          if (p.value === "copy") return { color: "#7bd4a8" };
          return null;
        },
        // Numeric counts
        "count_positive_green": function(p) {
          return (p.value > 0) ? { color: "#6aa84f", fontWeight: "500" } : { color: "#888" };
        },
        "count_positive_dim": function(p) {
          return (p.value > 0) ? { color: "#888" } : null;
        },
        "count_positive_yellow": function(p) {
          return (p.value > 0) ? { color: "#d4a017" } : null;
        },
        "parent_code_dim": function() {
          return { fontFamily: "monospace", color: "#888" };
        },
      };
      var CELL_RENDERER_REGISTRY = {
        "yes_check": function(p) { return p.value ? "✓" : ""; },
        "lock_icon": function(p) { return p.value ? "🔒" : ""; },
        "wrench_icon": function(p) { return p.value ? "🔧" : ""; },
        "thoughts_count": function(p) { return p.value > 0 ? "📝 " + p.value : "—"; },
      };
      // Backward compat alias (Phase 38.3 legacy code)
      var FORMATTER_REGISTRY = VALUE_FORMATTER_REGISTRY;

      function adaptServerColumns(serverCols) {
        // Server vrací: [{"field":"id", "headerName":"ID", "width":70,
        //                "valueFormatter":{"type":"datetime_rel"},
        //                "cellStyle":{"type":"mono"},
        //                "cellRenderer":{"type":"yes_check"}, ...}]
        // AG Grid potřebuje: všechny tři jako function. Rozbalíme přes
        // 3 registries (Phase 38.4 Krok 10 (10.5.)).
        return serverCols.map(function(c) {
          var col = {};
          for (var k in c) {
            if (k === "valueFormatter" && c[k] && c[k].type) {
              var fn = VALUE_FORMATTER_REGISTRY[c[k].type];
              if (fn) col.valueFormatter = fn;
            } else if (k === "cellStyle" && c[k] && c[k].type) {
              var fn2 = CELL_STYLE_REGISTRY[c[k].type];
              if (fn2) col.cellStyle = fn2;
            } else if (k === "cellRenderer" && c[k] && c[k].type) {
              var fn3 = CELL_RENDERER_REGISTRY[c[k].type];
              if (fn3) col.cellRenderer = fn3;
            } else {
              col[k] = c[k];
            }
          }
          return col;
        });
      }
      async function gridColumnsResolved(mode) {
        // 1. Pokus se fetch z server (fw.grid_master + grid_column)
        try {
          var res = await fetch("/api/v1/erp/grid/" + encodeURIComponent(mode) + "/columns",
                                { credentials: "include" });
          if (res.ok) {
            var data = await res.json();
            if (data && data.ok && Array.isArray(data.columns)) {
              console.log("[ERP-DIAG] gridColumns server: " + mode +
                          " (" + data.columns.length + " cols, config_v" +
                          (data.grid && data.grid.config_version) + ")");
              return adaptServerColumns(data.columns);
            }
          }
          // 404 = grid není v master schema → fallback na hardcoded
        } catch (e) {
          console.warn("[ERP-DIAG] gridColumns server fetch failed for " + mode +
                       ", fallback hardcoded:", e);
        }
        // 2. Fallback na hardcoded sync vrátky
        var cols = gridColumns(mode);
        if (cols && cols.length) {
          console.log("[ERP-DIAG] gridColumns hardcoded fallback: " + mode +
                      " (" + cols.length + " cols)");
        }
        return cols || [];
      }
      async function gridDataResolved(mode) {
        // Phase 38.4 Krok 14g Etapa D+2 (16.5.2026): delegated to window.dispatchGridData
        // (erp_grid_dispatcher.js module). Modul logs every step do fw.diag_log
        // via _erpLogToDb a zna `events` key (diag-log/events endpoint response).
        //
        // Marti's *„rozdelit na dalsi JS a zalogovat"* — modul je single source
        // of truth pro grid dispatch. Inline fallback (pokud modul nezachova) ma
        // minimal parsing s `events` key awareness.

        if (typeof window.dispatchGridData === "function") {
          return await window.dispatchGridData(mode);
        }

        // Fallback (erp_grid_dispatcher.js not loaded — would break banner 4/4 mod)
        // — minimal 3-tier s `events` key awareness (event parsing fix)
        console.warn("[gridDataResolved] erp_grid_dispatcher.js NOT loaded, using inline fallback");
        var code = mode;
        if (mode === "audited" || mode === "all" || mode === "stats") {
          code = "audit_" + mode;
        }
        try {
          var r = await fetch("/api/v1/erp/hw/" + encodeURIComponent(code),
                              { credentials: "include", cache: "no-store" });
          if (r.ok) {
            var d = await r.json();
            if (d && d.ok) {
              if (Array.isArray(d.rows)) {
                return d.rows;
              }
              if (d.delegate_url) {
                var rd = await fetch(d.delegate_url,
                                     { credentials: "include", cache: "no-store" });
                if (rd.ok) {
                  var dd = await rd.json();
                  return dd.rows || dd.events || dd.conversations || [];  // +events
                }
              }
            }
          }
        } catch (e) { /* fall through */ }
        var url;
        if (mode.indexOf("security_") === 0) {
          url = "/api/v1/erp/system/security?mode=" + encodeURIComponent(mode.substring(9));
        } else if (mode.indexOf("framework_") === 0) {
          url = "/api/v1/erp/system/framework?mode=" + encodeURIComponent(mode.substring(10));
        } else {
          url = "/api/v1/erp/system/audit-overview?mode=" + encodeURIComponent(mode);
        }
        var res = await fetch(url, { credentials: "include", cache: "no-store" });
        if (!res.ok) {
          throw new Error("HTTP " + res.status + " from " + url);
        }
        var data = await res.json();
        return data.rows || data.events || data.conversations || [];  // +events
      }
      if (window._sysHelpers) {
        window._sysHelpers.gridColumns = gridColumns;
        window._sysHelpers.gridColumnsResolved = gridColumnsResolved;
        window._sysHelpers.gridDataResolved = gridDataResolved;
        window._sysHelpers.formatterRegistry = FORMATTER_REGISTRY;
        console.log("[ERP-DIAG] _sysHelpers.gridColumns + gridColumnsResolved + gridDataResolved loaded");
      } else {
        console.error("[ERP-DIAG] _sysHelpers missing — gridColumns nelze pripojit");
      }
    })();
    </script>

    <!-- Phase 35-E.4 Variant B Krok C+ (9.5.2026 odpoledne) — renderSystemGrid
         pouziva univerzalni ErpDataGrid komponentu (datagrid.js) misto primeho
         agGrid.createGrid. Marti's spec "jedna komponenta gridu napric STRATEGII".
         Ziska automaticky: dark theme, ceska lokalizace, range select, autoSize,
         keyboard navigace, multi-select. Krok B+ (zitra) pridame layout toolbar
         pro System grids (vyzaduje backend layoutKey rozsireni). -->
    <script>
    (function() {
      function _escAttr(s) {
        return String(s == null ? "" : s).replace(/"/g, "&quot;");
      }
      // Phase 38.4 Krok 8 cleanup (10.5.2026): SYSTEM_LAYOUT_CISLA hardcoded
      // dict odstraněn. Mapping mode → cislo se derive ze System tree dat
      // (fw.menu_node — backend attachuje system_view + system_view_mode
      // per node v _build_node()). Pomocí _getSystemCisloByMode tree walker.
      //
      // Po cleanup: nový grid v master = INSERT do fw.menu_node + grid_master
      // → frontend automaticky funguje, žádný JS edit.
      // Drz instance per main pane — destroy previous pred create new
      window._sysCurrentGrid = null;

      // ── Phase 38.4 Krok 8 (10.5.2026): System tree cache + walkers ──
      //
      // Frontend cache last-loaded System tree dat (z /api/v1/erp/strom).
      // Plněno v loadTree() dataSource callback. Walker helpers nahrazují
      // hardcoded if-else cascades v _systemModeFromCislo / _systemModeFromItemId
      // a SYSTEM_LAYOUT_CISLA dict.
      //
      // Tree node attributes (z fw.menu_node + adaptServerTree):
      //   - id (= code, e.g. "system.security.devices")
      //   - cislo_def (e.g. -111)
      //   - system_view (e.g. "security" / "audit_overview" / "framework")
      //   - system_view_mode (e.g. "devices" / "audited" / "data_sources")
      //   - children
      window._systemTreeCache = null;

      function _walkSystemTree(predicate) {
        function walk(nodes) {
          for (var i = 0; i < (nodes || []).length; i++) {
            var n = nodes[i];
            if (predicate(n)) return n;
            var found = walk(n.children);
            if (found) return found;
          }
          return null;
        }
        return walk(window._systemTreeCache || []);
      }

      function _modeFromNode(node) {
        // Compute mode string from node's system_view + system_view_mode.
        // For audit_overview, system_view_mode IS the mode (audited/all/stats).
        // For others (security/framework), mode = system_view + "_" + system_view_mode.
        if (!node || !node.system_view) return null;
        if (node.system_view === "audit_overview") return node.system_view_mode;
        return node.system_view + "_" + node.system_view_mode;
      }

      function _findSystemNodeByCislo(cislo) {
        return _walkSystemTree(function(n) { return n.cislo_def === cislo; });
      }

      function _findSystemNodeById(itemId) {
        return _walkSystemTree(function(n) { return n.id === itemId; });
      }

      function _getSystemCisloByMode(mode) {
        var node = _walkSystemTree(function(n) {
          return _modeFromNode(n) === mode;
        });
        return node ? node.cislo_def : null;
      }

      // Expose pro debug + external usage (renderSystemGrid)
      window._sysFindNodeByCislo = _findSystemNodeByCislo;
      window._sysFindNodeById = _findSystemNodeById;
      window._sysGetCisloByMode = _getSystemCisloByMode;

      async function renderSystemGrid(mode, labelText) {
        var H = window._sysHelpers || {};
        var main = document.getElementById("erpMainContent");
        if (!main) {
          console.error("[ERP-DIAG] erpMainContent missing");
          return;
        }
        if (typeof ErpDataGrid !== "function") {
          main.innerHTML = '<div style="padding:20px;color:#f88">ErpDataGrid komponenta nenactena</div>';
          return;
        }
        // Phase 38.4 Krok 14b+5 polish (13.5.2026 ~18:35): track current
        // mode + label aby fw form onSaveSuccess callback mohol refreshovat
        // tento grid (volat renderSystemGrid znovu s same params).
        window._sysCurrentMode = mode;
        window._sysCurrentLabel = labelText || "";
        // Destroy predchozi instance (Marti's nav between System uzly)
        if (window._sysCurrentGrid && typeof window._sysCurrentGrid.destroy === "function") {
          try { window._sysCurrentGrid.destroy(); } catch (e) {}
          window._sysCurrentGrid = null;
        }

        // Phase 35-E.4 Krok C+ polish (9.5.2026 vecer): Marti's "staci nam ty
        // zalozky nahore nad gridem... Jako v EUROSOFTU". Odstranen interni
        // header (duplikat s tab zalozkou). Body je primy host pro
        // ErpDataGrid, full-height main pane.
        main.innerHTML =
          '<div id="erpSysGridBody" style="height:100%;background:var(--bg);">Nacitam...</div>';

        // Phase 38.4 Krok 12 (11.5.2026): data fetch přes H.gridDataResolved
        // (A3-first /api/v1/erp/data/{code}, legacy fallback uvnitř helperu).
        var body = document.getElementById("erpSysGridBody");
        if (!body) return;

        // Phase 38.4 Krok 8 (10.5.2026): async fetch z fw.grid_master + grid_column,
        // fallback na hardcoded H.gridColumns(mode). Po cleanup commit (#6+) hardcoded
        // pro daný mode zmizí — server data = single source of truth.
        var columns = H.gridColumnsResolved
          ? await H.gridColumnsResolved(mode)
          : (H.gridColumns ? H.gridColumns(mode) : []);
        var rowData;
        try {
          rowData = await H.gridDataResolved(mode);
        } catch (e) {
          console.error("[ERP] gridDataResolved failed for mode=" + mode + ":", e);
          body.innerHTML = '<div style="padding:20px;color:#f88">Chyba: ' + _escAttr(String(e)) + '</div>';
          return;
        }
        body.innerHTML = "";

        // Krok B+: Layout key pro System uzly (negativni cislo)
        // Phase 38.4 Krok 8 (10.5.2026): tree walker místo SYSTEM_LAYOUT_CISLA dict.
        // Helpers jsou v stejném IIFE, ale defensive check pro safety.
        var sysCislo = (typeof _getSystemCisloByMode === "function")
          ? _getSystemCisloByMode(mode)
          : (window._sysGetCisloByMode ? window._sysGetCisloByMode(mode) : null);
        var sysLayoutKey = (sysCislo != null) ? ("prehled_" + sysCislo) : null;

        // Krok C+ fix #8 (9.5.2026 vecer, AG Grid issue #7373): pre-fetch
        // layout PRED ErpDataGrid create. Pass jako `initialLayout` -> AG Grid
        // pouzije pres gridOptions.initialState pri prvnim render. Bez flicker
        // (driv: applyColumnState po gridReady = grid render with default
        // first, pak update with stored = "problikne a zcucne").
        var sysInitialLayout = null;
        if (sysCislo != null) {
          try {
            var listRes = await fetch(
              "/api/v1/erp/grid-layout/" + sysCislo + "/list",
              { credentials: "include" }
            );
            if (listRes.ok) {
              var listData = await listRes.json();
              if (listData && listData.ok && listData.effective_default) {
                sysInitialLayout = listData.effective_default;
              }
            }
          } catch (eFetch) {
            console.warn("[ERP-SYS] pre-fetch layout failed:", eFetch);
          }
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.K-D (17.5.2026, Marti's "dodelat
        // UI, aby se to dalo resit uzivatelsky"): + Nový datový zdroj button
        // pro framework_data_sources mode. Floating top-right, jen v tomto modu.
        if (mode === "framework_data_sources" && typeof window.DesignDataSourceEditor === "function") {
          var addNewBtn = document.createElement("button");
          addNewBtn.type = "button";
          addNewBtn.textContent = "➕ Nový datový zdroj";
          addNewBtn.title = "Vytvořit nový data_source + operations (Krok 5.K editor)";
          addNewBtn.style.cssText =
            "position:absolute;top:8px;right:80px;z-index:50;" +
            "padding:6px 14px;background:#1f4858;border:1px solid #3a8aa8;" +
            "color:#7ed4e8;border-radius:4px;cursor:pointer;font-size:12px;" +
            "font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.4);";
          addNewBtn.addEventListener("mouseenter", function() {
            addNewBtn.style.background = "#2a5a6a";
          });
          addNewBtn.addEventListener("mouseleave", function() {
            addNewBtn.style.background = "#1f4858";
          });
          addNewBtn.addEventListener("click", function() {
            new window.DesignDataSourceEditor({
              dataSourceId: null,
              onComplete: function() {
                if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                  window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                }
              },
            }).open();
          });
          body.style.position = "relative";  // anchor pro absolute child
          body.appendChild(addNewBtn);
        }

        // Krok 5.L-C: + Nový data_set button pro framework_data_sets mode
        if (mode === "framework_data_sets" && typeof window.DesignDataSetEditor === "function") {
          var addNewSetBtn = document.createElement("button");
          addNewSetBtn.type = "button";
          addNewSetBtn.textContent = "➕ Nový data set";
          addNewSetBtn.title = "Vytvořit nový SQL primitiv (Krok 5.L editor)";
          addNewSetBtn.style.cssText =
            "position:absolute;top:8px;right:80px;z-index:50;" +
            "padding:6px 14px;background:#1f4858;border:1px solid #3a8aa8;" +
            "color:#7ed4e8;border-radius:4px;cursor:pointer;font-size:12px;" +
            "font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.4);";
          addNewSetBtn.addEventListener("mouseenter", function() { addNewSetBtn.style.background = "#2a5a6a"; });
          addNewSetBtn.addEventListener("mouseleave", function() { addNewSetBtn.style.background = "#1f4858"; });
          addNewSetBtn.addEventListener("click", function() {
            new window.DesignDataSetEditor({
              dataSetId: null,
              onComplete: function() {
                if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                  window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                }
              },
            }).open();
          });
          body.style.position = "relative";
          body.appendChild(addNewSetBtn);
        }

        // Phase 38.4 Krok 14g Etapa F Sprint A (17.5.2026 dop.):
        // Status filter pills (Aktivní/Archivované/Vše) pro framework_data_sources
        // + framework_data_sets. Marti's "Kristý/Jirka bez DBeaveru" — explicit
        // affordance místo AG built-in column filter.
        // Default = Aktivní. Filter aplikován na rowData PŘED passováním do
        // ErpDataGrid (client-side, žádná AG Grid API gymnastics).
        var _filterableModes = ["framework_data_sources", "framework_data_sets"];
        if (_filterableModes.indexOf(mode) !== -1) {
          window._designStatusFilter = window._designStatusFilter || {};
          if (!window._designStatusFilter[mode]) window._designStatusFilter[mode] = "active";

          // Filter rowData podle current pill state
          var currentFilter = window._designStatusFilter[mode];
          if (currentFilter !== "all" && Array.isArray(rowData)) {
            rowData = rowData.filter(function(r) {
              return r && r.status === currentFilter;
            });
          }

          var filterBar = document.createElement("div");
          filterBar.style.cssText =
            "position:absolute;top:8px;left:8px;z-index:50;" +
            "display:flex;gap:4px;padding:4px;background:rgba(20,26,32,0.85);" +
            "border:1px solid #2a3340;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.4);";

          var _filterOptions = [
            { value: "active",   label: "✓ Aktivní" },
            { value: "archived", label: "📦 Archivované" },
            { value: "all",      label: "⊕ Vše" }
          ];
          _filterOptions.forEach(function(opt) {
            var pill = document.createElement("button");
            pill.type = "button";
            pill.textContent = opt.label;
            pill.dataset.value = opt.value;
            var isActive = window._designStatusFilter[mode] === opt.value;
            pill.style.cssText =
              "padding:4px 12px;border-radius:3px;border:1px solid;" +
              "font-size:11px;cursor:pointer;font-weight:" + (isActive ? "600" : "400") + ";" +
              (isActive
                ? "background:#1f4858;border-color:#3a8aa8;color:#7ed4e8;"
                : "background:transparent;border-color:#3a4754;color:#8a96a4;");
            pill.addEventListener("click", function() {
              window._designStatusFilter[mode] = opt.value;
              // Re-render grid (filter aplikován v rowData filter loop)
              if (window._sysHelpers && window._sysHelpers.renderSystemGrid) {
                window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
              }
            });
            filterBar.appendChild(pill);
          });
          body.style.position = "relative";
          body.appendChild(filterBar);
        }

        try {
          window._sysCurrentGrid = new ErpDataGrid(body, {
            rowData: rowData,
            columnDefs: columns,
            theme: "dark",
            height: "100%",
            compact: true,
            pinnedIdColumn: false, // mam to v columns def
            enableExport: true,
            enableFilters: true,
            enableRangeSelection: true,
            // Krok B+: Layout persistence (toolbar s dropdown + barvicky)
            layoutKey: sysLayoutKey,
            autoLoadDefault: !!sysLayoutKey,
            // Krok C+ fix #8: pre-fetched layout pro initialState (no flicker)
            initialLayout: sysInitialLayout,
            onRowClick: function(row, ev) {
              console.log("[ERP-SYS] row clicked", mode, row);
            },
            // Phase 38.4 Krok 14b (12.5.2026 vecer): dblclick / Enter → fw form
            // Marti's "Tim bychom meli vyhrano" — dogfooding fw framework pro
            // System grids (security_users, security_devices, ...). gridCode =
            // "prehled_" + sysCislo (např. "prehled_-110" pro security_users)
            // se posle do form-core-for-grid endpoint, ten resolve na fw form core.
            onRowDoubleClick: function(row, ev) {
              if (!row) return;
              var rowId = row.ID != null ? row.ID : (row.id != null ? row.id : null);
              if (rowId == null) return;
              // Phase 38.4 Krok 14g Etapa F Krok 5.K-D (17.5.2026, Marti's
              // "Jak se dostanu do ty editace... dodelat UI"): framework_data_sources
              // mode má vlastní hardcoded editor (DesignDataSourceEditor) — ne
              // generic fw form. Power tool pro daily designer use.
              if (mode === "framework_data_sources" && typeof window.DesignDataSourceEditor === "function") {
                new window.DesignDataSourceEditor({
                  dataSourceId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              // Krok 5.L-C (17.5.2026): DataSets mode dvojklik → DesignDataSetEditor
              if (mode === "framework_data_sets" && typeof window.DesignDataSetEditor === "function") {
                new window.DesignDataSetEditor({
                  dataSetId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              // Sprint D (17.5.2026 dop.): DB Connections mode dvojklik → DesignDbConnectionEditor
              if (mode === "framework_db_connections" && typeof window.DesignDbConnectionEditor === "function") {
                new window.DesignDbConnectionEditor({
                  connId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              if (!sysLayoutKey) return;
              if (typeof window._openFwFormForRow === "function") {
                window._openFwFormForRow(sysLayoutKey, rowId, null);
              } else {
                console.warn("[ERP-SYS] _openFwFormForRow not loaded");
              }
            },
            onRowEnter: function(row, ev) {
              if (!row) return;
              var rowId = row.ID != null ? row.ID : (row.id != null ? row.id : null);
              if (rowId == null) return;
              // Krok 5.K-D: stejně jako double-click handler pro framework_data_sources
              if (mode === "framework_data_sources" && typeof window.DesignDataSourceEditor === "function") {
                new window.DesignDataSourceEditor({
                  dataSourceId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              // Krok 5.L-C: DataSets Enter → DesignDataSetEditor
              if (mode === "framework_data_sets" && typeof window.DesignDataSetEditor === "function") {
                new window.DesignDataSetEditor({
                  dataSetId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              // Sprint D: DB Connections Enter → DesignDbConnectionEditor
              if (mode === "framework_db_connections" && typeof window.DesignDbConnectionEditor === "function") {
                new window.DesignDbConnectionEditor({
                  connId: rowId,
                  onComplete: function() {
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      window._sysHelpers.renderSystemGrid(mode, window._sysCurrentLabel || "");
                    }
                  },
                }).open();
                return;
              }
              if (!sysLayoutKey) return;
              if (typeof window._openFwFormForRow === "function") {
                window._openFwFormForRow(sysLayoutKey, rowId, null);
              } else {
                console.warn("[ERP-SYS] _openFwFormForRow not loaded");
              }
            }
          });
        } catch (e) {
          body.innerHTML = '<div style="padding:20px;color:#f88">ErpDataGrid create failed: ' + _escAttr(String(e)) + '</div>';
          console.error("[ERP-SYS] ErpDataGrid create failed", e);
          return;
        }
        // Krok C+ polish: row count je v ErpDataGrid status baru
        // (footer "Celkem: NNN"), zadny custom span uz nepotrebujeme.
      }
      if (window._sysHelpers) {
        window._sysHelpers.renderSystemGrid = renderSystemGrid;
        console.log("[ERP-DIAG] _sysHelpers.renderSystemGrid loaded (ErpDataGrid)");
      } else {
        console.error("[ERP-DIAG] _sysHelpers missing — renderSystemGrid nelze pripojit");
      }
    })();
    </script>

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

      const ACTIVE_KEY = "erp.tree.active";
      const TREE_WIDTH_KEY = "erp.tree.width";
      // EXPAND_KEY ("erp.tree.expanded") owned by ErpLeftPanelTree subclass
      // (Phase B+6.11e migration). Subclass sám persistuje expanded set.

      let activeErpDataGrid = null;      // current ErpDataGrid component (B+4 → default since B+4.3)
      // B+5.2 smoke testing: expose getter na window pro DevTools console.
      // Použití: await erpGrid().listLayouts()  /  erpGrid().getCurrentColumnState()
      window.erpGrid = () => activeErpDataGrid;
      // Phase B+6.11e (10.5.2026): ErpLeftPanelTree instance — set up po
      // prvním loadTree() volání. Owns: rendering, click dispatch,
      // expand/collapse, filter, active state visual, node index.
      let tree = null;
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
          // 11.5.2026 fix: pokud je tree collapsed a user táhne resize handle,
          // nejdřív expand (auto-recovery). Drag pak nastaví novou šířku.
          if (workspaceEl && workspaceEl.classList.contains("tree-collapsed")) {
            applyTreeCollapsed(false);
            saveTreeCollapsed(false);
          }
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

      // ── Active state — cislo-based, mimo subclass storage ──────────
      // Subclass ErpLeftPanelTree owns "erp.tree.expanded" (Set IDs).
      // Active key drží cislo_def jako string (cislo-based) — používá ho
      // tab restore. Necháváme samostatně, nepřebírá subclass.
      function loadActive() { return localStorage.getItem(ACTIVE_KEY) || null; }
      function saveActive(cislo) {
        try {
          if (cislo != null && cislo !== "") localStorage.setItem(ACTIVE_KEY, String(cislo));
          else localStorage.removeItem(ACTIVE_KEY);
        } catch (e) {}
      }

      // ── Tree fetch + render (Phase B+6.11e: ErpLeftPanelTree subclass) ──
      // Subclass owns: rendering, click dispatch, expand/collapse, filter,
      // active state visual, node index. Router.py keeps wrapper logic
      // (favorites, MRU, view modes, drag-drop, context menu).
      async function loadTree() {
        if (!tree) {
          tree = new ErpLeftPanelTree(treeRoot, {
            dataSource: async () => {
              const r = await fetch("/api/v1/erp/strom", { credentials: "include", cache: "no-store" });
              if (!r.ok) {
                throw new Error("Strom nelze načíst (status " + r.status + ").");
              }
              const data = await r.json();
              const adapted = ErpLeftPanelTree.adaptServerTree(data.tree || []);
              // Phase 38.4 Krok 8 (10.5.2026): cache tree pro _findSystemNodeByCislo
              // / _findSystemNodeById / _getSystemCisloByMode walkers
              window._systemTreeCache = adapted;
              return adapted;
            },
            // Plain klik na leaf — subclass už nastavil visual active class
            // a uložila active id; my dotahneme cislo-based saveActive +
            // tab open (router.py owns tab system).
            onActivate: (node, e, cislo) => {
              saveActive(String(cislo));
              const li = tree.findLiByCislo(cislo);
              if (typeof openTab === "function") openTab(cislo, li);
            },
            // Klik na ★ — quick toggle favorite (delegate na existing).
            onPinToggle: (cislo, node, e) => {
              toggleTreeFavorite(cislo);
            },
            // Ctrl+klik — multi-select. Mirror state v _selectedTreeCislos
            // pro context menu code (uses Set API: has/size/Array.from).
            onMultiSelect: (cislo, isSelected, e) => {
              if (isSelected) _selectedTreeCislos.add(cislo);
              else _selectedTreeCislos.delete(cislo);
            },
            // contextMenu — router.py má vlastní treeRoot.addEventListener
            // ("contextmenu") (níže). Až jednou přemigrujeme i context menu,
            // použije se ErpPopupMenu + tady hook.
            onContextMenu: null,
          });
        }
        try {
          // Phase 38.4 Krok 14g-H+9 (15.5.2026 dopo): subsequent loadTree
          // calls (= view mode toggle) use refresh() to preserve expanded
          // state + active ID + filter text. Initial call uses init() which
          // also wires base event handlers. tree._initedOnce flag tracks.
          if (tree._initedOnce && typeof tree.refresh === "function") {
            await tree.refresh();
          } else {
            await tree.init();
            tree._initedOnce = true;
          }
          if (!tree._data || tree._data.length === 0) {
            // Empty state už base class ukáže
            return;
          }
          // Post-render setup (původně v _origAttachTreeHandlers wrapper):
          //   1. Apply persisted favorites set → ★ ikony
          //   2. Apply per-group drag order
          //   3. Setup drag handlers
          //   4. Sync footer view-mode buttons
          //   5. Apply view filter (favorites/recent)
          //   6. Restore tab active state
          tree.applyPinSet(loadTreeFavorites());
          _applyTreeOrderFromStorage();
          _attachTreeDragHandlers();
          if (treeFooterEl) {
            treeFooterEl.querySelectorAll(".erp-tree-view-btn").forEach(b => {
              b.classList.toggle("active",
                b.getAttribute("data-tree-view") === treeViewMode);
            });
          }
          applyTreeViewFilter();
          tryRestoreActive();
        } catch (e) {
          renderTreeError(typeof e === "string" ? e : ("Chyba: " + (e.message || String(e))));
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
          // Reset tree instance — vynutí znovu init() při loadTree()
          if (tree) {
            try { tree.destroy(); } catch (err) {}
            tree = null;
          }
          loadTree();
        });
      }

      // ── Path / breadcrumb (delegate na subclass) ──
      // Subclass ErpLeftPanelTree drží node index + walk parent chain
      // přes DOM upward traversal. Path je array [{id, label, cislo_def}]
      // od root k node.
      function getPathForId(id) {
        if (!tree) return [];
        return tree.getPathForId(id);
      }

      // (renderTreeNodes / buildNodeIndex / attachTreeHandlers / setActive
      //  byly migrovány do ErpLeftPanelTree subclass — Phase B+6.11e,
      //  10.5.2026. Click semantics: Ctrl+klik=multi-select,
      //  toggle=expand-only, plain klik na leaf=onActivate hook → openTab.)

      // ── Multi-select state mirror ────────────────────────────────
      // _selectedTreeCislos je Set udržovaný v sync se subclass přes
      // onMultiSelect callback (viz loadTree). Context menu code (níže)
      // ho čte jako Set: has(), size, Array.from(). Subclass má vlastní
      // _selectedSet — tyto dva jsou drženy v sync.
      const _selectedTreeCislos = new Set();
      function _clearTreeSelection() {
        _selectedTreeCislos.clear();
        if (tree) tree.clearSelection();
      }
      function _toggleTreeSelection(item) {
        if (!tree || !item) return;
        const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
        if (!cislo) return;
        // Subclass toggle → mirror Set (onMultiSelect callback dělá totéž
        // při uživatelském Ctrl+klik; tady programmatic call si zajistíme
        // sync ručně).
        tree.toggleSelection(cislo);
        if (tree.isSelected(cislo)) _selectedTreeCislos.add(cislo);
        else _selectedTreeCislos.delete(cislo);
      }
      function _selectTreeRow(item) {
        // Single (non-additive) — clear pak select
        _clearTreeSelection();
        _toggleTreeSelection(item);
      }

      // Phase 35-E.4 Krok C+ (9.5.2026): System uzly jsou ted normalni taby
      // (negative cislo). Render funkce se vola z _renderTabIntoMain pri
      // switchTab. Tabs bar zustava VISIBLE — System tab vypada/chova se
      // identicky jako EUROSOFT prehled tab.
      // Helpers v izolovanych <script> blocich nahore (window._sysHelpers.*).

      // Phase 38.4 Krok 8 cleanup (10.5.2026): Hardcoded if-else cascade
      // odstraněna. Mapping itemId → mode se derive z System tree dat
      // (fw.menu_node primary, hardcoded fallback v _SYSTEM_CISLO_TO_VIEW).
      //
      // Speciální case: 'system.audit.tabs' (cislo_def=-100) drží Variant A
      // tabs UI signal — nemá vlastní mode, jen markeruje tabs bar visibility.
      //
      // Walker helpers jsou v jiném IIFE, tj. čteme přes window._sys*.
      function _systemModeFromItemId(itemId) {
        if (!itemId) return null;
        if (itemId === "system.audit.tabs") return "tabs";  // UI signal, no mode
        if (typeof window._sysFindNodeById !== "function") return null;
        var node = window._sysFindNodeById(itemId);
        if (!node || !node.system_view) return null;
        if (node.system_view === "audit_overview") return node.system_view_mode;
        return node.system_view + "_" + node.system_view_mode;
      }

      // Phase 38.4 Krok 8 cleanup (10.5.2026): Hardcoded if-else cascade
      // odstraněna. Mapping cislo → mode se derive z System tree dat.
      // Plně DB-driven přes fw.menu_node.cislo_def + system_view{_mode}.
      // Walker helpers jsou v jiném IIFE, čteme přes window._sys*.
      function _systemModeFromCislo(cislo) {
        if (cislo === -100) return "tabs";  // UI signal, audit tabs bar
        if (typeof window._sysFindNodeByCislo !== "function") return null;
        var node = window._sysFindNodeByCislo(cislo);
        if (!node || !node.system_view) return null;
        if (node.system_view === "audit_overview") return node.system_view_mode;
        return node.system_view + "_" + node.system_view_mode;
      }

      // Render System view do main pane. NEMODIFIKUJE tabsBar ani tree
      // active state (to dela switchTab caller pred volanim).
      function _renderSystemViewIntoMain(mode, label) {
        const main = document.getElementById("erpMainContent");
        if (!main) return;
        main.dataset.systemView = mode || "";
        const lbl = label || "Audit";

        if (mode === "tabs") {
          // Variant A — iframe dashboard se zalozkami (combined view)
          main.innerHTML =
            '<iframe src="/erp/system/audit-dashboard?embed=1&single=0&mode=tabs"' +
            ' style="width:100%;height:100%;border:0;background:var(--bg);display:block"' +
            ' title="Audit dashboard"></iframe>';
        } else if (window._sysHelpers && window._sysHelpers.renderSystemGrid) {
          // Variant B — native AG Grid v main pane.
          // Phase 35-E.4: audited / all / stats (audit-overview endpoint)
          // Phase 38.3 (10.5.2026): security_* modes (security endpoint),
          //   handled v renderSystemGrid via mode prefix dispatch.
          window._sysHelpers.renderSystemGrid(mode, lbl);
        } else {
          // Fallback — pokud helpers neproskocila parse, jdi pres iframe
          main.innerHTML =
            '<iframe src="/erp/system/audit-dashboard?embed=1&single=1&mode=' + mode +
            '" style="width:100%;height:100%;border:0;background:var(--bg);display:block"' +
            ' title="Audit dashboard fallback"></iframe>';
        }
      }

      // ── Active node restore (po loadTree) ──────────────────────────
      // Phase B+6.11e: subclass owns visual active class. Router.py má
      // vlastní cislo-based saveActive (ne subclass id-based). Tato
      // funkce: najde LI by cislo, scrollIntoView, expand ancestors,
      // open tab pokud nejsou persisted tabs.
      function tryRestoreActive() {
        const cislo = loadActive();
        if (!cislo || !tree) return;
        const item = tree.findLiByCislo(cislo);
        if (!item) return;
        const row = item.querySelector(":scope > .erp-tree-row");
        if (row) row.classList.add("active");
        // Persist active id v subclass storage také (pokud má id)
        if (item.dataset.id) tree.setActive(item.dataset.id);
        expandAncestors(item);
        if (row && row.scrollIntoView) {
          try { row.scrollIntoView({ block: "nearest" }); } catch (e) {}
        }
        // Pokud nejsou žádné persisted tabs, otevři podle aktivního tree node
        const persisted = loadTabsState();
        if (!persisted || !persisted.tabs || persisted.tabs.length === 0) {
          if (typeof openTab === "function") openTab(parseInt(cislo, 10), item);
        }
      }

      // ── Expand ancestors (DOM walk + sync se subclass) ────────────
      // DOM walk: každý level vyhledá rodiče přes parentElement chain.
      // Pro každého rodiče: zobraz jeho .erp-tree-children, set toggle ▼,
      // a registruj id do subclass _expandedIds (přes tree.expand) — to
      // automaticky persistuje (subclass _saveToStorage).
      function expandAncestors(item) {
        if (!tree || !item) return;
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
          // Sync se subclass expanded set (persistuje při _saveToStorage)
          if (parentItem.dataset.id) {
            tree.expand(parentItem.dataset.id);
          }
          cur = parentItem;
        }
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

      async function renderPrehled(cislo, item, data, breadcrumb) {
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

        // Krok C+ fix #8 (9.5.2026 vecer, AG Grid issue #7373): pre-fetch
        // layout PRED ErpDataGrid create. Pass jako `initialLayout` -> AG
        // Grid pouzije pres gridOptions.initialState pri prvnim render.
        let initialLayout = null;
        try {
          const listRes = await fetch(
            "/api/v1/erp/grid-layout/" + cislo + "/list",
            { credentials: "include" }
          );
          if (listRes.ok) {
            const listData = await listRes.json();
            if (listData && listData.ok && listData.effective_default) {
              initialLayout = listData.effective_default;
            }
          }
        } catch (eFetch) {
          console.warn("[ERP] pre-fetch layout failed:", eFetch);
        }

        activeErpDataGrid = new window.ErpDataGrid(container, {
          rowData: rows,
          columns: cols,
          autoColumns: true,
          layoutKey: "prehled_" + cislo,  // B+5 grid layout persistence (TODO)
          initialLayout: initialLayout,    // Krok C+ fix #8: no flicker
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
          // Phase 38.4 Krok 14b (12.5.2026 vecer): Enter / dblclick → openFwFormForRow
          // (fw-native form, např. user_edit). Pri 404 fallback openJadroInPane
          // (legacy Centrála 1 jádro via data.id_edit).
          onRowDoubleClick: (rowData) => {
            const rowId = rowData.ID != null ? rowData.ID : (rowData.id != null ? rowData.id : null);
            if (rowId == null) return;
            openFwFormForRow("prehled_" + cislo, rowId, data.id_edit);
          },
          onRowEnter: (rowData) => {
            const rowId = rowData.ID != null ? rowData.ID : (rowData.id != null ? rowData.id : null);
            if (rowId == null) return;
            openFwFormForRow("prehled_" + cislo, rowId, data.id_edit);
          },
        });

        // B+10++ (6.5.2026 Marti's drobnost): limit selector v hlavičce
        // smazán — interakce teď přes status bar Celkem (CzRowCountStatusPanel
        // limitContext.onChange v ErpDataGrid options).
      }

      // ── Phase 38.4 Krok 14b (12.5.2026 vecer): openFwFormForRow ───────
      // Marti's spec: dvojklik / Enter na radku gridu → fw-native form
      // (DesignFwForm modal). Pri 404 (grid neni v fw.menu_node) fallback
      // na legacy openJadroInPane (EC_FormDef ID = data.id_edit).
      //
      // Drz Marti's "Tim bychom meli vyhrano" doctrine (12.5. ~22:30) —
      // scaffold + open jsou ekosystem pro dogfooding fw frameworku.
      async function openFwFormForRow(gridCode, rowId, legacyFormId) {
        if (!gridCode || rowId == null) return;
        try {
          const r = await fetch(
            "/api/v1/erp/design/form-core-for-grid/" + encodeURIComponent(gridCode),
            { credentials: "include" }
          );
          if (r.ok) {
            const d = await r.json();
            if (d && d.ok && d.found && d.form_core && d.form_core.code) {
              if (typeof window.DesignFwForm !== "function") {
                console.warn("[fw-form] DesignFwForm not loaded — fallback");
              } else {
                const modal = new window.DesignFwForm({
                  coreCode: d.form_core.code,
                  rowId: rowId,
                  // Phase 38.4 Krok 14b+5 polish (13.5.2026 ~18:35): grid
                  // refresh callback po OK save. Marti's request: "aby bylo
                  // videt, ze se hodnota zmenila".
                  onSaveSuccess: async function(respData) {
                    console.info("[fw-form] onSaveSuccess — refresh grid", respData);
                    // Phase 38.4 Krok 14b+5 polish (13.5.2026 ~18:50, Marti's
                    // request): preserve selected row po refresh. Save row_id
                    // pred refresh, post-render find + setSelected + scroll.
                    //
                    // Phase 38.4 Krok 14b+6 (13.5.2026 ~19:30, Marti's "radek
                    // se po refreshi neoznaci, musim kliknout"): pridany 3
                    // fixy ktere visualni selekci drzi:
                    //   1. await renderSystemGrid PRED poll (driv: poll bezel
                    //      pred destroy/recreate, chytil starou instanci)
                    //   2. poll ceka na getDisplayedRowCount() > 0 (DOM rows
                    //      v viewportu, ne jen node.data v AG Grid internals)
                    //   3. setFocusedCell + redrawRows po setSelected ->
                    //      keyboard focus + force CSS class apply na row el.
                    //   4. type-coerce String() compare (driv: int vs string
                    //      mismatch, === fail)
                    var savedRowId = respData && respData.row_id;
                    function _reselectRowAfterRefresh() {
                      if (savedRowId == null) return;
                      var attempts = 0;
                      var maxAttempts = 40;  // 40 * 100ms = 4s timeout
                      var poll = setInterval(function() {
                        attempts++;
                        var grid = window._sysCurrentGrid;
                        var apiReady = grid && grid.gridApi
                          && typeof grid.gridApi.forEachNode === "function"
                          && typeof grid.gridApi.getDisplayedRowCount === "function";
                        if (apiReady) {
                          var displayedCount = 0;
                          try { displayedCount = grid.gridApi.getDisplayedRowCount(); } catch (e) {}
                          if (displayedCount > 0) {
                            var foundNode = null;
                            try {
                              grid.gridApi.forEachNode(function(node) {
                                if (!foundNode && node.data) {
                                  var rid = node.data.id != null ? node.data.id : node.data.ID;
                                  // Type-coerce: respData.row_id muze byt int z
                                  // PATCH response, node.data.id muze byt int /
                                  // string podle column type. String() unify.
                                  if (rid != null && String(rid) === String(savedRowId)) {
                                    foundNode = node;
                                  }
                                }
                              });
                            } catch (e) { /* mid-render race, retry next tick */ }
                            if (foundNode) {
                              clearInterval(poll);
                              try {
                                // Selection — vnitrni AG Grid stav
                                foundNode.setSelected(true);
                                // Scroll do viewportu (pokud uz neni)
                                grid.gridApi.ensureNodeVisible(foundNode, "middle");
                                // Keyboard focus — vyznacne fokusni cellu z
                                // prvni viditelnou column. Bez focused cell
                                // AG Grid Enterprise nezvyrazni selection CSS
                                // (Marti's "fyzicky musim kliknout" = klik
                                // dava i focused cell, nejen selection).
                                try {
                                  var displayedCols = grid.gridApi.getAllDisplayedColumns();
                                  if (displayedCols && displayedCols.length > 0) {
                                    grid.gridApi.setFocusedCell(
                                      foundNode.rowIndex,
                                      displayedCols[0].getColId()
                                    );
                                  }
                                } catch (eFocus) {
                                  console.warn("[fw-form] setFocusedCell failed:", eFocus);
                                }
                                // Force CSS class apply — redraw konkretni
                                // row. Bez toho AG Grid sice ma node.selected
                                // = true, ale DOM `.ag-row-selected` class
                                // neni aplikovana (selection state set pred
                                // row mount do viewportu, race condition).
                                try {
                                  grid.gridApi.redrawRows({ rowNodes: [foundNode] });
                                } catch (eRedraw) {
                                  console.warn("[fw-form] redrawRows failed:", eRedraw);
                                }
                                // Phase 38.4 Krok 14b+6.1 (13.5.2026 ~19:50,
                                // Marti's "dva radky oznacene" catch): po close
                                // modal OS kurzor zustal nad gridem na jinem
                                // radku, AG Grid aplikoval .ag-row-hover na ten
                                // radek. Plus .ag-row-selected na nas novy radek
                                // = dva visualne highlighted radky. Move OS
                                // kurzor z JS nelze (browser security), ale
                                // muzu sjednotit hover state:
                                //   1. querySelectorAll [row-index="N"] (AG Grid
                                //      renderuje row v left-pinned + center +
                                //      right-pinned containers, vsechny zde)
                                //   2. odebrat .ag-row-hover ze vsech ostatnich
                                //      row DOM elementu v gridu
                                //   3. pridat .ag-row-hover na nas radek (vsechny
                                //      pinned/center instances)
                                //   4. dispatch syntetic mouseenter/mouseover
                                //      event pro AG Grid interni hover state
                                //      (pripad ze AG Grid pouziva JS handlers
                                //      misto pure CSS :hover)
                                try {
                                  var targetRowIndex = foundNode.rowIndex;
                                  var rootEl = body;  // erpSysGridBody div
                                  // Cleanup: odebrat .ag-row-hover ze vsech radku
                                  var existingHovers = rootEl.querySelectorAll(".ag-row-hover");
                                  for (var hi = 0; hi < existingHovers.length; hi++) {
                                    existingHovers[hi].classList.remove("ag-row-hover");
                                  }
                                  // Apply na nas radek (vsechny DOM instances —
                                  // pinned + center)
                                  var ourRowEls = rootEl.querySelectorAll(
                                    '[row-index="' + targetRowIndex + '"]'
                                  );
                                  for (var ri = 0; ri < ourRowEls.length; ri++) {
                                    var rowEl = ourRowEls[ri];
                                    rowEl.classList.add("ag-row-hover");
                                    // Synthetic events (defensive — AG Grid
                                    // event handler routing pokud listenuje)
                                    try {
                                      var meEvt = new MouseEvent("mouseenter", {
                                        bubbles: false,
                                        cancelable: true,
                                        view: window
                                      });
                                      rowEl.dispatchEvent(meEvt);
                                      var moEvt = new MouseEvent("mouseover", {
                                        bubbles: true,
                                        cancelable: true,
                                        view: window
                                      });
                                      rowEl.dispatchEvent(moEvt);
                                    } catch (eDispatch) {}
                                  }
                                  console.info(
                                    "[fw-form] hover applied on rowIndex=" +
                                    targetRowIndex + " (" + ourRowEls.length +
                                    " DOM instances)"
                                  );
                                } catch (eHover) {
                                  console.warn("[fw-form] hover sync failed:", eHover);
                                }
                                console.info(
                                  "[fw-form] post-refresh row selected:",
                                  savedRowId,
                                  "rowIndex=" + foundNode.rowIndex,
                                  "attempts=" + attempts
                                );
                              } catch (e) {
                                console.warn("[fw-form] setSelected failed:", e);
                              }
                              return;
                            }
                          }
                        }
                        if (attempts >= maxAttempts) {
                          clearInterval(poll);
                          console.warn(
                            "[fw-form] post-refresh row select timeout id=" + savedRowId,
                            "(grid=" + !!grid + " api=" + apiReady + ")"
                          );
                        }
                      }, 100);
                    }
                    // System grid (security_users + ostatni negativni cislo grids)
                    if (window._sysHelpers && typeof window._sysHelpers.renderSystemGrid === "function") {
                      var currentMode = window._sysCurrentMode || null;
                      var currentLabel = window._sysCurrentLabel || "";
                      if (currentMode) {
                        try {
                          // await -> renderSystemGrid je async function, fetch
                          // data + create new ErpDataGrid. Driv: fire-and-forget
                          // = poll bezel mezi destroy() a new ErpDataGrid(),
                          // _sysCurrentGrid null = timeout. Now: await, poll
                          // azi po creation, gridApi uz exists.
                          await window._sysHelpers.renderSystemGrid(currentMode, currentLabel);
                          _reselectRowAfterRefresh();
                          return;
                        } catch (e) {
                          console.warn("[fw-form] System grid refresh failed:", e);
                        }
                      }
                    }
                    // Legacy renderPrehled (positive cislo grids — current cislo z scope)
                    if (typeof cislo !== "undefined" && typeof loadPrehled === "function") {
                      try {
                        // loadPrehled muze nebo nemusi vracet Promise — pokud
                        // ano, await; pokud ne, sync return = OK
                        var maybePromise = loadPrehled(cislo, item);
                        if (maybePromise && typeof maybePromise.then === "function") {
                          await maybePromise;
                        }
                        _reselectRowAfterRefresh();
                        return;
                      } catch (e) {
                        console.warn("[fw-form] Legacy grid refresh failed:", e);
                      }
                    }
                    // Last resort fallback — full page reload (heavy ale 100% works)
                    console.warn("[fw-form] No grid refresh handler — falling back to location.reload()");
                    location.reload();
                  },
                });
                await modal.open();
                return;
              }
            }
            // d.found=false → form template jeste neexistuje (scaffold needed)
            if (d && d.ok && !d.found) {
              const code = (d.suggested_form_code || "<form>");
              alert(
                "Form detail '" + code + "' ještě není postaven.\\n\\n" +
                "Pravým klikem na řádek → 'Design: Jadro pro radek' → " +
                "tlačítko 🪄 Vytvoř form detail."
              );
              return;
            }
          }
        } catch (e) {
          console.warn("[fw-form] lookup failed:", e);
        }
        // Fallback: legacy Centrála 1 jádro (jen pokud máme id_edit)
        if (legacyFormId != null) {
          openJadroInPane(legacyFormId, rowId);
        } else {
          console.warn(
            "[fw-form] no fw form + no legacy fallback for gridCode=" + gridCode
          );
        }
      }
      // Expose pro renderSystemGrid (jiny IIFE) + debug
      window._openFwFormForRow = openFwFormForRow;

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

      // ── Phase 38.4 (11.5.2026 vecer): Footer user dropdown + Design mode ─
      // Marti's spec: footer user "Marti" je teď clickable button s popoverem.
      // V popoveru toggle Design mode — separate flag od chat DEV mode.
      // localStorage `erp.design.mode.enabled` (per-browser, nezávislý od
      // users.dev_mode_enabled v chatu). Když ON, teal "🎨 DESIGN" badge
      // se objeví v pravém horním rohu (analog chat purpurová DEV).
      const ERP_DESIGN_MODE_KEY = 'erp.design.mode.enabled';

      function getErpDesignMode() {
        try { return localStorage.getItem(ERP_DESIGN_MODE_KEY) === '1'; }
        catch (e) { return false; }
      }
      function setErpDesignMode(on) {
        try { localStorage.setItem(ERP_DESIGN_MODE_KEY, on ? '1' : '0'); }
        catch (e) {}
        // Phase 38.4 Krok 14g-H+4 (15.5.2026): expose state PRED render
        // tak aby _attachTreeDragHandlers (zavolan z renderErpDesignBadge)
        // cetl aktualni hodnotu, ne pre-flip.
        try { window._erpDesignMode = !!on; } catch (e) {}
        renderErpDesignBadge();
      }
      function renderErpDesignBadge() {
        const on = getErpDesignMode();
        let badge = document.getElementById('erpDesignBadge');
        if (on) {
          if (!badge) {
            badge = document.createElement('span');
            badge.id = 'erpDesignBadge';
            badge.className = 'erp-design-badge';
            badge.textContent = '🎨 DESIGN';
            badge.title = 'ERP design režim — odhaluje framework struktury & override hints. Separate od chat DEV.';
            document.body.appendChild(badge);
          }
        } else if (badge) {
          badge.remove();
        }
        // Phase 38.4 Krok 14g-G (15.5.2026 rano, Marti's "tlacitko Novy
        // soudecek v paticce"): sync visibility z DESIGN flag.
        try {
          const newBtn = document.getElementById('erpNewSoudecekBtn');
          if (newBtn) {
            newBtn.style.display = on ? 'flex' : 'none';
          }
        } catch (e) {}
        // Phase 38.4 Krok 14g-H+2 (15.5.2026 rano, Marti's "drop kamkoli"):
        // sync Root drop zone visibility z DESIGN flag.
        try {
          const rootDz = document.getElementById('erpRootDropZone');
          if (rootDz) {
            rootDz.style.display = on ? 'flex' : 'none';
          }
        } catch (e) {}
        // Phase 38.4 Krok 14g-H+4 (15.5.2026 dopo): re-attach row.draggable
        // po mode flip. DESIGN → row.draggable=false (lefttree.js li vede),
        // PROD → row.draggable=true (same-group reorder pro Oblibene).
        // window._erpDesignMode je uz updated above pres getErpDesignMode().
        try { _attachTreeDragHandlers(); } catch (e) {}
      }
      // Init při page load
      // Phase 38.4 Krok 14g-H+4 (15.5.2026): expose state PRED render
      // pro _attachTreeDragHandlers (zavolan z renderErpDesignBadge).
      try { window._erpDesignMode = getErpDesignMode(); } catch (e) {}
      renderErpDesignBadge();

      // Phase 38.4 Krok 14g-G: Novy soudecek button click handler.
      // Dialog s 3 fields (label / code / kind). Parent_id prefilled z
      // selected tree node (folder = parent, list = parent.parent).
      function _erpFindSelectedTreeNode() {
        // Hledame highlighted node v tree — .erp-tree-row.erp-tree-selected
        // nebo .erp-tree-row.active
        try {
          const root = document.getElementById('erpTreeRoot');
          if (!root) return null;
          const active = root.querySelector('.erp-tree-row.erp-tree-selected, .erp-tree-row.active');
          if (!active) return null;
          const li = active.closest('.erp-tree-item');
          if (!li) return null;
          return {
            menuNodePk: li.dataset.menuNodePk ? parseInt(li.dataset.menuNodePk, 10) : null,
            label: (li.querySelector('.erp-tree-label') || {}).textContent || '',
            kind: li.classList.contains('erp-tree-leaf') ? 'list' : 'folder',
          };
        } catch (e) {
          return null;
        }
      }

      async function _erpOpenNewSoudecekDialog(opts) {
        opts = opts || {};
        const selected = _erpFindSelectedTreeNode();
        // Krok 14g-G3: pre-fill parent z selected, but Marti sees + can change.
        // Krok 14g-H+31 step 6 (15.5.2026 vecer, Marti's "jedna komponenta"):
        // opts.defaultParentId override (volaci pres soudecekPicker.onCreate
        // muze pass current menuNode.parent_id misto tree-selected).
        let parentId = null;
        if (opts.defaultParentId != null) {
          parentId = opts.defaultParentId;
        } else if (selected && selected.menuNodePk) {
          parentId = selected.menuNodePk;
        }
        // Fetch all available menu_nodes for parent picker dropdown
        let allNodes = [];
        try {
          const r = await fetch('/api/v1/erp/design/menu-nodes', { credentials: 'include' });
          if (r.ok) {
            const d = await r.json();
            if (d.ok) allNodes = d.items || [];
          }
        } catch (e) { console.warn('[NewSoudecek] menu-nodes fetch failed:', e); }
        // Build indented label per node (depth approximate from parent chain)
        const byId = new Map();
        allNodes.forEach(n => byId.set(n.id, n));
        const _depth = (n) => {
          let d = 0; let p = n.parent_id;
          while (p && d < 10) {
            const parent = byId.get(p);
            if (!parent) break;
            d++; p = parent.parent_id;
          }
          return d;
        };
        // Build modal dialog (inline, no extra deps)
        const overlay = document.createElement('div');
        overlay.style.cssText =
          'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10000;' +
          'display:flex;align-items:center;justify-content:center;';
        const modal = document.createElement('div');
        modal.style.cssText =
          'background:#141a20;border:1px solid #2a3340;border-radius:6px;' +
          'min-width:460px;max-width:560px;color:#e8eef5;font-size:13px;' +
          'box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;';
        const close = () => { try { document.body.removeChild(overlay); } catch (e) {} };

        const header = document.createElement('div');
        header.style.cssText =
          'padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;' +
          'display:flex;justify-content:space-between;align-items:center;';
        header.innerHTML =
          '<div style="font-weight:600;font-size:14px;color:#a88cd4;">📁 Nový soudeček</div>' +
          '<button type="button" style="background:transparent;border:none;color:#8a96a4;' +
          'font-size:18px;cursor:pointer;line-height:1;" id="_nsClose">✕</button>';
        modal.appendChild(header);

        const body = document.createElement('div');
        body.style.cssText = 'padding:16px;display:flex;flex-direction:column;gap:10px;';

        const _inpStyle = 'padding:6px 10px;background:#0f141a;border:1px solid #2a3340;' +
                         'color:#e8eef5;border-radius:3px;font-size:13px;width:100%;' +
                         'box-sizing:border-box;';
        const _row = (label, el) => {
          const wrap = document.createElement('div');
          wrap.style.cssText = 'display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;';
          const lbl = document.createElement('label');
          lbl.textContent = label;
          lbl.style.cssText = 'color:#a8b4c2;font-size:12px;';
          wrap.appendChild(lbl); wrap.appendChild(el);
          return wrap;
        };
        // Krok 14g-G3: Parent picker dropdown (Marti vidi + zmeni).
        const parentSel = document.createElement('select');
        parentSel.style.cssText = _inpStyle;
        // First option: Root (no parent)
        const rootOpt = document.createElement('option');
        rootOpt.value = '';
        rootOpt.textContent = '🌳 — Root (top-level, sibling SYSTEM) —';
        parentSel.appendChild(rootOpt);
        // Folders + lists with indent prefix
        const _sortedNodes = allNodes.slice().sort((a, b) => {
          // Sort by depth, then sort_order
          const da = _depth(a), db = _depth(b);
          if (da !== db) return da - db;
          return (a.sort_order || 0) - (b.sort_order || 0);
        });
        // Re-sort: indented tree-like — recurse top-down
        const _treeOrder = [];
        const _walk = (parentId) => {
          const children = _sortedNodes.filter(n => n.parent_id === parentId)
            .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
          for (const c of children) {
            _treeOrder.push(c);
            _walk(c.id);
          }
        };
        _walk(null);
        for (const n of _treeOrder) {
          const depth = _depth(n);
          const prefix = '  '.repeat(depth) + (n.kind === 'folder' ? '📁 ' : '📄 ');
          const opt = document.createElement('option');
          opt.value = String(n.id);
          opt.textContent = prefix + n.label + ' (' + n.code + ')';
          if (parentId && n.id === parentId) opt.selected = true;
          parentSel.appendChild(opt);
        }
        body.appendChild(_row('Parent', parentSel));

        // Hint pod parent picker
        const parentHint = document.createElement('div');
        parentHint.style.cssText = 'color:#7a8696;font-size:10px;padding:0 2px;font-style:italic;';
        parentHint.textContent = (parentId
          ? '↑ Prefilled z vybraného uzlu v levém stromě. Změň pokud chceš jinou pozici.'
          : '↑ Nový soudeček bude top-level (sibling SYSTEM v sidebar).');
        body.appendChild(parentHint);
        // Label
        const labelInp = document.createElement('input');
        labelInp.type = 'text'; labelInp.style.cssText = _inpStyle;
        labelInp.placeholder = 'Display name (např. "Zákazníci")';
        body.appendChild(_row('Label', labelInp));
        // Code
        const codeInp = document.createElement('input');
        codeInp.type = 'text'; codeInp.style.cssText = _inpStyle;
        codeInp.placeholder = 'Unique code (např. "zakaznici" — auto z label)';
        // Auto-suggest code z label
        labelInp.addEventListener('input', () => {
          if (codeInp.dataset.userEdit !== '1') {
            codeInp.value = labelInp.value
              .toLowerCase()
              .normalize('NFD').replace(/[̀-ͯ]/g, '')
              .replace(/[^a-z0-9]+/g, '_')
              .replace(/^_+|_+$/g, '');
          }
        });
        codeInp.addEventListener('input', () => { codeInp.dataset.userEdit = '1'; });
        body.appendChild(_row('Code', codeInp));
        // Kind dropdown
        const kindSel = document.createElement('select');
        kindSel.style.cssText = _inpStyle;
        [['folder', '📁 Folder (kontejner pro sub-soudečky)'],
         ['list', '📄 List (přehled s daty)']].forEach(([v, l]) => {
          const o = document.createElement('option');
          o.value = v; o.textContent = l;
          kindSel.appendChild(o);
        });
        body.appendChild(_row('Kind', kindSel));

        modal.appendChild(body);

        const footer = document.createElement('div');
        footer.style.cssText = 'padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;' +
                              'display:flex;justify-content:flex-end;gap:8px;';
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Storno';
        cancelBtn.style.cssText = 'padding:6px 16px;background:#2a3340;border:1px solid #3a4754;' +
                                  'border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;';
        cancelBtn.addEventListener('click', close);
        footer.appendChild(cancelBtn);
        const okBtn = document.createElement('button');
        okBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Vytvořit';
        okBtn.style.cssText = 'padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;' +
                              'border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;';
        okBtn.addEventListener('click', async () => {
          const labelV = labelInp.value.trim();
          const codeV = codeInp.value.trim();
          if (!labelV || !codeV) {
            alert('Label + code povinné.'); return;
          }
          // Krok 14g-G3: read parent_id z dropdown (Marti's actual choice)
          const parentSelVal = parentSel.value;
          const finalParentId = parentSelVal ? parseInt(parentSelVal, 10) : null;
          okBtn.disabled = true; okBtn.style.opacity = '0.6';
          try {
            const r = await fetch('/api/v1/erp/design/menu-node', {
              method: 'POST', credentials: 'include',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                code: codeV, label: labelV,
                parent_id: finalParentId, kind: kindSel.value,
              }),
            });
            const d = await r.json();
            if (!r.ok || !d.ok) throw new Error(d.error || ('HTTP ' + r.status));
            close();
            // Krok 14g-H+31 step 6: optional opts.onSuccess callback
            // (volaci pres soudecekPicker chce switch Form 1 na new id).
            const newMenuNodeId = d.menu_node_id;
            if (newMenuNodeId && typeof opts.onSuccess === 'function') {
              try { opts.onSuccess(newMenuNodeId); }
              catch (eCb) { console.warn('[NewSoudecek] onSuccess failed:', eCb); }
            }
            // Tree reload (existing function expected)
            if (typeof window.reloadErpTree === 'function') {
              await window.reloadErpTree();
            } else if (typeof window.location !== 'undefined') {
              // Fallback: full reload
              window.location.reload();
            }
          } catch (e) {
            console.error('[NewSoudecek] create failed:', e);
            alert('Vytvoreni selhalo: ' + (e.message || e));
            okBtn.disabled = false; okBtn.style.opacity = '1';
          }
        });
        footer.appendChild(okBtn);
        modal.appendChild(footer);

        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        document.getElementById('_nsClose').addEventListener('click', close);
        const escHandler = (ev) => {
          if (ev.key === 'Escape') {
            ev.stopPropagation();
            close();
            document.removeEventListener('keydown', escHandler, true);
          }
        };
        document.addEventListener('keydown', escHandler, true);
        setTimeout(() => labelInp.focus(), 50);
      }
      // Krok 14g-H+31 step 6: expose wizard na window pro soudecekPicker.onCreate
      // (sjednoceni — jedna komponenta pro 3 pripady — Marti's request).
      try { window._erpOpenNewSoudecekDialog = _erpOpenNewSoudecekDialog; }
      catch (eExp) {}

      // Attach button click handler (idempotent)
      try {
        const nsBtn = document.getElementById('erpNewSoudecekBtn');
        if (nsBtn && !nsBtn.dataset.attached) {
          nsBtn.dataset.attached = '1';
          nsBtn.addEventListener('click', () => _erpOpenNewSoudecekDialog());
        }
      } catch (e) {}

      // Phase 38.4 Krok 14g-H+2 (15.5.2026 rano, Marti's "drop kamkoli"):
      // Wire-up Root drop zone — drag soudecek sem → PATCH parent_id=NULL.
      // Idempotent attach pattern (data-attached flag).
      function _erpToast(msg, type) {
        try {
          if (typeof window._showToast === 'function') {
            window._showToast(msg, type || 'info');
            return;
          }
        } catch (e) {}
        try {
          if (typeof window._showErpToast === 'function') {
            window._showErpToast(msg, type || 'info');
            return;
          }
        } catch (e) {}
        // Inline fallback — fixed bottom-right toast
        try {
          const t = document.createElement('div');
          t.textContent = msg;
          t.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:99999;' +
            'padding:10px 16px;border-radius:6px;font-size:13px;font-weight:500;' +
            'color:#fff;box-shadow:0 4px 12px rgba(0,0,0,0.4);max-width:380px;' +
            'background:' + (type === 'error' ? '#dc2626' : (type === 'success' ? '#10b981' : '#374151'));
          document.body.appendChild(t);
          setTimeout(() => { try { t.remove(); } catch (e) {} }, 4500);
        } catch (e) {
          alert(msg);
        }
      }
      try {
        const rootDz = document.getElementById('erpRootDropZone');
        if (rootDz && !rootDz.dataset.attached) {
          rootDz.dataset.attached = '1';
          rootDz.addEventListener('dragover', (ev) => {
            // Akceptovat jen menu-node payload (ne field/comp_def drag)
            const types = ev.dataTransfer && ev.dataTransfer.types;
            if (!types) return;
            let hasMenuNode = false;
            try {
              for (let i = 0; i < types.length; i++) {
                if (types[i] === 'application/x-erp-menu-node-move') {
                  hasMenuNode = true;
                  break;
                }
              }
            } catch (e) {}
            if (!hasMenuNode) return;
            ev.preventDefault();
            ev.dataTransfer.dropEffect = 'move';
            rootDz.classList.add('erp-tree-root-dropzone-hover');
          });
          rootDz.addEventListener('dragleave', () => {
            rootDz.classList.remove('erp-tree-root-dropzone-hover');
          });
          rootDz.addEventListener('drop', async (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            rootDz.classList.remove('erp-tree-root-dropzone-hover');
            let payload = null;
            try {
              const raw = ev.dataTransfer.getData('application/x-erp-menu-node-move');
              if (raw) payload = JSON.parse(raw);
            } catch (e) {}
            if (!payload || !payload.menuPk) {
              _erpToast('Drop neúspěšný — chybí menu-node payload', 'error');
              return;
            }
            console.info('[RootDropZone] drop menuPk=' + payload.menuPk + ' → parent_id=NULL', payload);
            try {
              const resp = await fetch('/api/v1/erp/design/fw-menu-node/update/' + encodeURIComponent(payload.menuPk), {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ parent_id: null }),
              });
              const json = await resp.json().catch(() => ({}));
              if (!resp.ok || json.ok === false) {
                const err = (json && json.error) || ('HTTP ' + resp.status);
                console.warn('[RootDropZone] PATCH failed', resp.status, json);
                _erpToast('Přesun do Root selhal: ' + err, 'error');
                return;
              }
              _erpToast('Přesunuto do Root ✓', 'success');
              // Reload tree — use same function as _erpOpenNewSoudecekDialog
              try {
                if (typeof window.reloadErpTree === 'function') {
                  await window.reloadErpTree();
                } else if (typeof window._erpReloadTree === 'function') {
                  await window._erpReloadTree();
                } else {
                  window.location.reload();
                }
              } catch (e) {
                console.warn('[RootDropZone] reload failed', e);
              }
            } catch (e) {
              console.error('[RootDropZone] fetch error', e);
              _erpToast('Přesun do Root selhal — síťová chyba', 'error');
            }
          });
        }
      } catch (e) {
        console.warn('[RootDropZone] init failed', e);
      }

      function _erpRenderUserPopover() {
        const pop = document.getElementById('erpFooterUserPopover');
        if (!pop) return;
        pop.innerHTML = '';
        const on = getErpDesignMode();
        // Design mode toggle item
        const designItem = document.createElement('div');
        designItem.className = 'erp-user-popover-item' + (on ? ' on' : '');
        designItem.innerHTML =
          '<span class="erp-user-popover-item-label">🎨 Design režim</span>' +
          '<span class="erp-user-popover-item-toggle">' + (on ? 'ZAP' : 'VYP') + '</span>';
        designItem.title = 'Odhalí framework struktury a override hints v UI. Neovlivňuje chat DEV mode.';
        designItem.addEventListener('click', () => {
          setErpDesignMode(!getErpDesignMode());
          _erpRenderUserPopover();
        });
        pop.appendChild(designItem);
        // Future: další položky (profile, settings, logout, atd.)
      }

      function _erpToggleUserPopover() {
        const btn = document.getElementById('erpFooterUserBtn');
        const pop = document.getElementById('erpFooterUserPopover');
        if (!btn || !pop) return;
        if (pop.hasAttribute('hidden')) {
          _erpRenderUserPopover();
          pop.removeAttribute('hidden');
          btn.classList.add('active');
        } else {
          pop.setAttribute('hidden', '');
          btn.classList.remove('active');
        }
      }

      // Click handler + outside-click close
      // 11.5. fix: footer button je rendered v _render_full_page (AFTER
      // workspace <main>), takže inline IIFE getElementById vrací null.
      // Wrap init do DOMContentLoaded (stejný pattern jako tenant switcher).
      function _erpInitUserDropdown() {
        const userBtn = document.getElementById('erpFooterUserBtn');
        const userPop = document.getElementById('erpFooterUserPopover');
        if (!userBtn || !userPop) return;
        userBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          _erpToggleUserPopover();
        });
        document.addEventListener('click', (ev) => {
          if (userPop.hasAttribute('hidden')) return;
          if (userBtn.contains(ev.target)) return;
          if (userPop.contains(ev.target)) return;
          userPop.setAttribute('hidden', '');
          userBtn.classList.remove('active');
        });
        document.addEventListener('keydown', (ev) => {
          if (ev.key === 'Escape' && !userPop.hasAttribute('hidden')) {
            userPop.setAttribute('hidden', '');
            userBtn.classList.remove('active');
          }
        });
      }
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _erpInitUserDropdown, { once: true });
      } else {
        _erpInitUserDropdown();
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
      // 11.5.2026 fix: click kdekoli na collapsed pane = expand.
      // Marti's trap *„sipka mimo zoom"* — když je `›` button mimo viewport
      // kvůli PWA zoom edge case, celá 32px pane je clickable jako fallback.
      const treePaneEl = document.querySelector(".erp-tree-pane");
      if (treePaneEl) {
        treePaneEl.addEventListener("click", (ev) => {
          if (!workspaceEl.classList.contains("tree-collapsed")) return;
          // Skip pokud target je toggle button (race condition: button handler
          // už collapse změnil; bubble do pane by hned undid). Plus pokud klik
          // prošel přes resize handle (jeho own handler řeší expand).
          if (ev.target && ev.target.closest(".erp-tree-toggle-btn")) return;
          if (ev.target && ev.target.closest(".erp-resize-handle")) return;
          applyTreeCollapsed(false);
          saveTreeCollapsed(false);
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
        // Phase 38.4 Krok 14g-H+9 (15.5.2026 dopo, Marti's "prenacteni
        // stromu z DB pri prekliknuti Vše/Oblibene/MRU"): re-fetch + full
        // re-render. Bez toho jen CSS visibility filter — tree DOM zustane
        // stale, post-mode-flip drag handlers nepripoji. loadTree() volá
        // tree.init() (fresh dataSource) + post-render setup (drag handlers
        // wire pro current DESIGN flag) + applyTreeViewFilter().
        loadTree().catch(() => {});
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
        treeRoot.addEventListener("contextmenu", async (ev) => {
          const row = ev.target.closest(".erp-tree-row");
          if (!row) return;
          const item = row.closest(".erp-tree-item");
          if (!item) return;
          // Phase 38.4 Krok 14g-H+11 (15.5.2026 odpo, Marti's "CORE pri
          // pravym kliku otevira browser default menu"): rozsireny gate.
          // CORE (a vsechny nove soudecky pres + Novy soudecek button) nemaji
          // cislo_def (legacy Centrala 1 field). Accept menu_node_pk taky.
          const cislo = parseInt(item.getAttribute("data-cislo-def") || "0", 10);
          const menuNodePk = parseInt(item.getAttribute("data-menu-node-pk") || "0", 10);
          if (!cislo && !menuNodePk) return;  // node bez fw mappingu

          ev.preventDefault();

          // Compute target cislos — pokud row je v selection a multi-select
          // active, akce platí pro celou selection. Jinak jen tento řádek.
          let targetCislos;
          if (cislo && _selectedTreeCislos.has(cislo) && _selectedTreeCislos.size > 1) {
            targetCislos = Array.from(_selectedTreeCislos);
          } else if (cislo) {
            targetCislos = [cislo];
            // Single right-click — vyber pro visual feedback (pokud není v selection)
            if (!_selectedTreeCislos.has(cislo)) {
              _selectTreeRow(item);
            }
          } else {
            // Krok 14g-H+11: node bez cislo_def (CORE + novy soudecek) — no pin tracking
            targetCislos = [];
          }

          const multi = targetCislos.length > 1;

          const menuItems = [];

          if (multi) {
            menuItems.push({
              hint: "Vybráno " + targetCislos.length + " položek",
            });
          }

          // Krok 14g-H+11: pin/favorites jen pokud cislo_def existuje
          if (targetCislos.length > 0) {
            const allPinned = targetCislos.every(c => isTreeFavorite(c));
            const nonePinned = targetCislos.every(c => !isTreeFavorite(c));

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
          }

          // Phase 38.4 (11.5.2026 vecer): DESIGN položka — jen když design
          // mód aktivní + single selection (design je per-entity, ne bulk).
          // Phase 38.4 Krok 14g Etapa F Krok 5.J-B3 (16.5.2026 ~24:15, Marti's
          // "Smazat ze stromu HCoded menu Design: Soudecek plus core prehledu"):
          // hardcoded menu item odstranen — fw-driven Design forms (Krok 5.A-J)
          // jsou teď preferred entry point. DesignSoudecekCoreForm (Form 1)
          // zůstává jako legacy class pro backward compat, ale není v menu.

          // ═════════════════════════════════════════════════════════════
          // Phase 38.4 Krok 14g-H+33 Etapa 2 (15.5.2026 vecer, Marti's
          // "system pro pridavani fw polozek do menu"): fetch DB items
          // z fw.context_menu_item + append na konec menu. Dispatcher pro
          // action_kind='open_fw_form' otevre DesignSoudecekCoreForm.
          // ═════════════════════════════════════════════════════════════
          if (!multi) {
            try {
              const isLeaf = item.classList.contains("erp-tree-leaf");
              const nodeKind = isLeaf ? "list" : "folder";
              const isDesignMode = window._erpDesignMode === true;
              // Capture node identifiers at menu-open time (closures over `item`
              // unsafe if menu reopens for jine node mezi tim)
              const mnPk = item.getAttribute("data-menu-node-pk") || "";
              const mnCode = item.getAttribute("data-id") || "";
              const mnLabelEl = item.querySelector(".erp-tree-label");
              const mnLabel = mnLabelEl
                ? (mnLabelEl.dataset.erpOrigText || mnLabelEl.textContent || "")
                : "";

              const url = "/api/v1/erp/design/context-menu-items?" +
                new URLSearchParams({
                  scope: "tree_node",
                  design_mode: isDesignMode ? "true" : "false",
                  applies_to_kind: nodeKind,
                }).toString();
              const r = await fetch(url, { credentials: "include" });
              if (r.ok) {
                const data = await r.json();
                if (data && data.ok && Array.isArray(data.items)) {
                  // Append divider (visual hint kde zacinaji DB items)
                  // _showTreeContextMenu helper kontroluje it.divider (line 14093)
                  if (data.items.length > 0 && menuItems.length > 0) {
                    menuItems.push({ divider: true });
                  }
                  for (const cmi of data.items) {
                    menuItems.push({
                      icon: cmi.icon || "⚙",
                      label: cmi.label,
                      handler: (function (cmiSnap) {
                        return function () {
                          // Dispatch by action_kind (Marti's volba A: jen open_fw_form)
                          if (cmiSnap.action_kind === "open_fw_form") {
                            // ═══════════════════════════════════════════════
                            // Phase 38.4 Krok 14g-H+33 Etapa 2.2 v2 (16.5.2026
                            // ranní, modular retry po Etapa 2.2 v1 fail):
                            // FW form dispatch externalized do
                            // /static/erp/components/fw_form_dispatcher.js
                            // (DesignFwForm data-driven, ne DesignSoudecekCoreForm
                            // hardcoded). Plus mutual immunity (_erpLoadModule)
                            // + _erpLogToDb event logging.
                            // ═══════════════════════════════════════════════
                            if (typeof window.dispatchFwFormFromContextMenu === "function") {
                              // Phase 38.4 Krok 14g-H+33 Etapa F (17.5.2026,
                              // Marti's "do soudecku se vzdy prenasi jen ID 16"):
                              // pass mnLabel jako 5. param — fw_form_dispatcher
                              // jej preda do DesignFwForm runtimeMenuNodeLabel,
                              // entity_picker(display_mode='origin') ho zobrazi
                              // misto _spec.origin.menu_node (stamped).
                              window.dispatchFwFormFromContextMenu(cmiSnap, item, mnPk, mnCode, mnLabel);
                            } else {
                              alert("fw_form_dispatcher.js not loaded (kit chybi).");
                              console.error("[contextmenu] dispatchFwFormFromContextMenu not on window");
                            }
                          } else {
                            alert(
                              "Custom menu item '" + cmiSnap.code +
                              "' ma action_kind='" + cmiSnap.action_kind +
                              "' — neimplementovany dispatcher."
                            );
                          }
                        };
                      })(cmi),
                    });
                  }
                }
              }
            } catch (e) {
              console.warn("[contextmenu] DB items fetch failed:", e);
            }
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
        //
        // Phase 38.4 Krok 14g-H+4 (15.5.2026 dopo, Marti's "v design mode
        // zcela ignorovat immutable"): gate WHOLE row-level drag setup na
        // PROD mode only. V DESIGN mode lefttree.js li-level cross-parent
        // drag je primary (parent_id PATCH na libovolne misto, vc. Root).
        // V PROD mode row-level drag drzi same-group reorder pro Oblibene.
        // Bez gate: nested draggable konflikt (row > li) — browser preferuje
        // innermost = row, ktery same-group check blokoval cross-tree drop.
        const designMode = (typeof window !== "undefined" && window._erpDesignMode === true);
        treeRoot.querySelectorAll(".erp-tree-item").forEach(item => {
          const row = item.querySelector(":scope > .erp-tree-row");
          if (!row) return;
          if (designMode) {
            // DESIGN: nech lefttree.js li-level drag vest. Remove existing
            // row.draggable (idempotent — re-attach after mode flip).
            row.removeAttribute("draggable");
            return;
          }
          // PROD: same-group reorder pro Oblibene.
          row.setAttribute("draggable", "true");
        });

        // Single set listenerů na treeRoot (delegation)
        if (treeRoot._dragWired) return;
        treeRoot._dragWired = true;

        treeRoot.addEventListener("dragstart", (ev) => {
          // Phase 38.4 Krok 14g-H+4 (15.5.2026): DESIGN mode → skip.
          // Lefttree.js capture-phase li.dragstart handler je primary
          // (cross-parent move pres parent_id PATCH). Tento bubble-phase
          // delegate je jen pro PROD same-group reorder.
          if (typeof window !== "undefined" && window._erpDesignMode === true) {
            return;
          }
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
      // (Phase B+6.11e: _origAttachTreeHandlers wrapper byl odstraněn —
      //  post-render setup (favorites + drag-drop + view filter + footer
      //  buttons) byl přesunut do loadTree() success path. Subclass
      //  ErpLeftPanelTree je sole owner click handlerů.)

      // ── B+8 (6.5.2026): Multi-tab přehled state + UI ───────────────
      // MVP localStorage. Phase B+8.1 přepne na backend persistence
      // (per user, per tenant — Marti's spec — endpoint /api/v1/erp/tabs).
      const TABS_STATE_KEY = "erp.tabs.state.v1";
      const tabsBarEl = document.getElementById("erpTabsBar");
      const tabsState = {
        tabs: [],            // [{cislo, itemId, label, data, gridState}]
        activeIndex: -1,
      };

      // ════════════════════════════════════════════════════════════════
      // Phase 38.5 (9.5.2026 vecer): ErpRefresh — refresh ikona v hlavicce
      // s per-tab freshness tracking. Marti's UX: aby user pochopil ze
      // data jsou stara (orange tint po 5 min, pulse po 15 min). Klik
      // refreshne aktivni tab grid (ne tree, ne sidebar).
      // ════════════════════════════════════════════════════════════════
      const ErpRefresh = {
        // Map<cisloStr, fetchedAtMs> — per-tab freshness timestamps
        _gridFreshness: new Map(),
        // Phase 38.5+ (10.5.2026 vecer Marti's debugging): TEST values
        // 60s/90s/10s pro odladění detection logic. Po smoke vrátit na
        // 5min / 15min / 30s (production values).
        STALE_AT_MS: 60 * 1000,            // TEST 60s → orange (prod: 5*60*1000)
        VERY_STALE_AT_MS: 90 * 1000,       // TEST 90s → pulse  (prod: 15*60*1000)
        POLL_INTERVAL_MS: 10 * 1000,       // TEST 10s polling  (prod: 30*1000)

        // Volat po uspesnem fetchi (v _loadTabData po `tab.data = data`)
        markFresh(cislo) {
          if (cislo == null) return;
          this._gridFreshness.set(String(cislo), Date.now());
          this._updateButton();
        },

        // Volat po close tabu (cleanup)
        forget(cislo) {
          if (cislo == null) return;
          this._gridFreshness.delete(String(cislo));
        },

        // Aktualizovat barvu/tooltip ikony podle aktivniho tabu.
        // Volat: po switchTab, po markFresh, polling timer.
        _updateButton() {
          const btn = document.getElementById('erpRefreshBtn');
          if (!btn) return;
          const activeCislo = this._getActiveTabCislo();
          if (activeCislo == null) {
            btn.classList.remove('stale', 'very-stale');
            btn.disabled = true;
            btn.setAttribute('data-hint', 'Žádný aktivní přehled');
            return;
          }
          btn.disabled = false;
          const fetchedAt = this._gridFreshness.get(String(activeCislo));
          if (!fetchedAt) {
            btn.classList.remove('stale', 'very-stale');
            btn.setAttribute('data-hint', 'Obnovit data v aktivním přehledu');
            return;
          }
          const ageMs = Date.now() - fetchedAt;
          const ageMin = Math.floor(ageMs / 60000);
          const ageStr = ageMin < 1 ? '<1 min' : (ageMin + ' min');
          if (ageMs >= this.VERY_STALE_AT_MS) {
            btn.classList.add('stale', 'very-stale');
            btn.setAttribute('data-hint', 'Data jsou stará ' + ageStr + ' — klikni pro obnovení');
          } else if (ageMs >= this.STALE_AT_MS) {
            btn.classList.add('stale');
            btn.classList.remove('very-stale');
            btn.setAttribute('data-hint', 'Data jsou stará ' + ageStr + ' — klikni pro obnovení');
          } else {
            btn.classList.remove('stale', 'very-stale');
            btn.setAttribute('data-hint', 'Data fresh (' + ageStr + '). Klikni pro manuální refresh.');
          }
        },

        _getActiveTabCislo() {
          if (typeof tabsState === 'undefined' || tabsState.activeIndex < 0) return null;
          const tab = tabsState.tabs[tabsState.activeIndex];
          return tab ? tab.cislo : null;
        },

        // Klik handler — clear cached data + re-call _loadTabData.
        async refresh() {
          const cislo = this._getActiveTabCislo();
          if (cislo == null) return;
          const tab = tabsState.tabs[tabsState.activeIndex];
          if (!tab) return;
          const btn = document.getElementById('erpRefreshBtn');
          if (btn) btn.classList.add('spinning');
          try {
            // Clear cached data → _loadTabData fetchne znovu
            tab.data = null;
            if (typeof _loadTabData === 'function') {
              await _loadTabData(tab);
            } else {
              // Fallback: full page reload
              window.location.reload();
            }
          } finally {
            if (btn) btn.classList.remove('spinning');
          }
        },

        init() {
          const btn = document.getElementById('erpRefreshBtn');
          if (!btn) return;
          btn.addEventListener('click', () => this.refresh());
          // Polling timer pro update barvy aktivniho tabu (kazdych 30s
          // prepocita stari).
          setInterval(() => this._updateButton(), this.POLL_INTERVAL_MS);
          this._updateButton();
        }
      };
      // Init po DOMContentLoaded (button musi existovat)
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ErpRefresh.init());
      } else {
        ErpRefresh.init();
      }
      window.ErpRefresh = ErpRefresh;  // expose pro debugging

      // ════════════════════════════════════════════════════════════════
      // Phase 38.5+ (10.5.2026 rano): Install button pro non-technical
      // users. Marti's spec: 10 koleginim technicky unfriendly. ZIP +
      // PowerShell + admin rights je out — potrebujeme "klik a hotovo".
      //
      // Chrome's "beforeinstallprompt" event fired kdyz PWA detection
      // success (manifest valid + sw.js + HTTPS + ne uz installed).
      // Zachyt event, ulozi pro lazy trigger pri user click.
      // ════════════════════════════════════════════════════════════════
      let _deferredInstallPrompt = null;
      window.addEventListener('beforeinstallprompt', (ev) => {
        // Prevent default mini-infobar (Chrome desktop default UI)
        ev.preventDefault();
        _deferredInstallPrompt = ev;
        const btn = document.getElementById('erpInstallBtn');
        if (btn) btn.style.display = 'inline-flex';
        console.log('[install] beforeinstallprompt captured — button shown');
      });
      const _installBtn = document.getElementById('erpInstallBtn');
      if (_installBtn) {
        _installBtn.addEventListener('click', async () => {
          if (!_deferredInstallPrompt) {
            // Fallback: ukaz user kde ma manualne kliknout
            alert(
              "Pro instalaci klikni na 3 tečky vpravo nahoře v Chrome → " +
              "'Nainstalovat STRATEGIE ERP'.\\n\\n" +
              "Pokud možnost nevidíš, zkus reload stránky."
            );
            return;
          }
          try {
            _deferredInstallPrompt.prompt();
            const { outcome } = await _deferredInstallPrompt.userChoice;
            console.log('[install] user choice:', outcome);
            if (outcome === 'accepted') {
              _installBtn.style.display = 'none';
            }
          } catch (e) {
            console.error('[install] prompt failed:', e);
          }
          _deferredInstallPrompt = null;
        });
      }
      // Hide install button kdyz uz je nainstalovany (post-install event)
      window.addEventListener('appinstalled', () => {
        const btn = document.getElementById('erpInstallBtn');
        if (btn) btn.style.display = 'none';
        console.log('[install] appinstalled event — button hidden');
      });
      // Hide install button v PWA standalone mode (uz nainstalovany)
      if (window.matchMedia('(display-mode: standalone)').matches) {
        const btn = document.getElementById('erpInstallBtn');
        if (btn) btn.style.display = 'none';
      }

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
          // Persistuj jen lehkou meta — ne data ani gridState (ty se znovu fetchnou).
          // 11.5. fix: ukládat i pinned + lastAccessedAt aby LRU + pin přežily reload.
          const persist = {
            tabs: tabsState.tabs.map(t => ({
              cislo: t.cislo,
              itemId: t.itemId,
              label: t.label,
              pinned: t.pinned === true,
              lastAccessedAt: typeof t.lastAccessedAt === "number" ? t.lastAccessedAt : 0,
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
          pinned: false,
          lastAccessedAt: Date.now(),
        };
        tabsState.tabs.push(tab);
        // Phase 38.4 (11.5.2026 vecer): LRU eviction po push (pred persist)
        _evictOldestTab();
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
        // Phase 38.4 (11.5.2026 vecer): track lastAccessedAt pro LRU eviction
        if (tabsState.tabs[idx]) {
          tabsState.tabs[idx].lastAccessedAt = Date.now();
        }
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
        // Phase 38.5: po switch tabu (load nebo cached) prepocitat refresh
        // ikonu — novy aktivni tab moze mit jine stari dat.
        if (typeof ErpRefresh !== 'undefined') ErpRefresh._updateButton();
      }

      function closeTab(idx) {
        if (idx < 0 || idx >= tabsState.tabs.length) return;
        const closedCislo = tabsState.tabs[idx].cislo;
        tabsState.tabs.splice(idx, 1);
        // B+8.1c: API persist tab close (fire-and-forget)
        _apiCall("DELETE", "/api/v1/erp/tabs/" + closedCislo);
        // Phase 38.5: cleanup freshness tracking pro zavreny tab
        if (typeof ErpRefresh !== 'undefined') ErpRefresh.forget(closedCislo);
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

      // Phase 38.4 (11.5.2026 vecer): MAX_TABS LRU eviction cap.
      // Pokud bys mel vic, openTab() automaticky zavre nejstarsi
      // unpinned tab (LRU). User vidi vzdy nejpouzivanejsich N tabu.
      const MAX_TABS_VISIBLE = 10;

      function renderTabsBar() {
        if (!tabsBarEl) return;
        if (tabsState.tabs.length === 0) {
          tabsBarEl.setAttribute("hidden", "");
          tabsBarEl.innerHTML = "";
          return;
        }
        tabsBarEl.removeAttribute("hidden");
        let html = "";
        // Phase 38.4 (11.5.2026 vecer): Close-all-except-active button VLEVO.
        // Marti's spec: nahrada za stary "+" button, ten zmizel — user otevira
        // nove pres tree click (existing flow). 11.5. revize: normalni × misto ⊗
        // (Marti's UX feedback).
        html += '<button type="button" class="erp-tab-close-all" id="erpTabCloseAll" ' +
                'title="Zavřít všechny záložky kromě aktivní">×</button>';
        tabsState.tabs.forEach((t, i) => {
          const active = (i === tabsState.activeIndex);
          const pinned = (t.pinned === true);
          // 11.5. revize: žádný pinned styling na celé záložce (Marti's UX
          // feedback). Místo toho close ikona vpravo: × pro běžné, 📌 pro pinned.
          // Right-click toggle pin <=> close (pinned tab close icon = 📌 disabled).
          html += '<div class="erp-tab' + (active ? ' active' : '') +
                  '" data-tab-idx="' + i + '" title="' + escapeAttr(t.label) +
                  (pinned ? ' (📌 připnutá — pravý klik pro odepnutí)' : '') + '">';
          html += '<span class="erp-tab-label">' + escapeHtml(t.label) + '</span>';
          const closeChar = pinned ? '📌' : '×';
          const closeTitle = pinned
            ? 'Připnutá záložka (pravý klik pro odepnutí)'
            : 'Zavřít záložku';
          html += '<button type="button" class="erp-tab-close' +
                  (pinned ? ' pinned' : '') +
                  '" data-tab-close="' + i +
                  '" title="' + closeTitle + '">' + closeChar + '</button>';
          html += '</div>';
        });
        tabsBarEl.innerHTML = html;
        // Event delegation — click switch + close × + close-all + right-click pin
        tabsBarEl.querySelectorAll(".erp-tab").forEach(el => {
          el.addEventListener("click", (ev) => {
            if (ev.target.classList.contains("erp-tab-close")) return;
            const idx = parseInt(el.getAttribute("data-tab-idx"), 10);
            if (!isNaN(idx)) switchTab(idx);
          });
          // Right-click toggle pin — Phase 38.4 (11.5.2026 vecer) write-through DB.
          el.addEventListener("contextmenu", (ev) => {
            ev.preventDefault();
            const idx = parseInt(el.getAttribute("data-tab-idx"), 10);
            if (isNaN(idx)) return;
            const tab = tabsState.tabs[idx];
            if (!tab) return;
            tab.pinned = !tab.pinned;
            // Pinned tabs sort to left (pinned by access order, unpinned by access order)
            const targetTab = tab;
            tabsState.tabs.sort((a, b) => {
              if ((a.pinned || false) !== (b.pinned || false)) return (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0);
              return (b.lastAccessedAt || 0) - (a.lastAccessedAt || 0);
            });
            // Re-find active index after sort
            const newActiveIdx = tabsState.tabs.indexOf(targetTab);
            tabsState.activeIndex = newActiveIdx >= 0 ? newActiveIdx : 0;
            saveTabsState();
            renderTabsBar();
            // 11.5. write-through DB — pin status musí přežít F5 reload.
            // Fire-and-forget (frontend už updatnul, server jen audit).
            _apiCall("POST", "/api/v1/erp/tabs/" + encodeURIComponent(targetTab.cislo) + "/pinned",
                     { pinned: targetTab.pinned });
          });
        });
        tabsBarEl.querySelectorAll(".erp-tab-close").forEach(el => {
          el.addEventListener("click", (ev) => {
            ev.stopPropagation();
            // 11.5. revize: pinned tab → close icon je 📌 (no-op na klik),
            // jen right-click ho odepne. User must unpin first to close.
            if (el.classList.contains("pinned")) return;
            const idx = parseInt(el.getAttribute("data-tab-close"), 10);
            if (!isNaN(idx)) closeTab(idx);
          });
        });
        const closeAllBtn = document.getElementById("erpTabCloseAll");
        if (closeAllBtn) {
          closeAllBtn.addEventListener("click", () => {
            // Zavrit vse krome aktivni (pinned zustanou) — Marti's mandate
            const activeTab = tabsState.tabs[tabsState.activeIndex];
            if (!activeTab) return;
            const survivors = tabsState.tabs.filter(t => t === activeTab || t.pinned === true);
            // Issue DELETE per tab being closed (backend persistence)
            tabsState.tabs.forEach(t => {
              if (!survivors.includes(t)) {
                try {
                  fetch("/api/v1/erp/tabs/" + encodeURIComponent(t.cislo), {
                    method: "DELETE", credentials: "include"
                  });
                } catch (e) {}
                try { ErpRefresh.forget(t.cislo); } catch (e) {}
              }
            });
            tabsState.tabs = survivors;
            tabsState.activeIndex = survivors.indexOf(activeTab);
            saveTabsState();
            renderTabsBar();
          });
        }
        // 11.5. fix #4: dynamic overflow eviction po každém render.
        // Pokud taby přetékají scrollbar (scrollWidth > clientWidth),
        // evikuj nejstarší unpinned non-active dokud se zarovnají.
        // Guards proti infinite loop uvnitř _scheduleOverflowEviction.
        _scheduleOverflowEviction();
      }

      // Phase 38.4 (11.5.2026 vecer): dynamic overflow eviction — po
      // každém renderTabsBar kontrolujeme jestli se taby vejdou do bar
      // šířky. Pokud scrollWidth > clientWidth → eviktujeme nejstarší
      // unpinned non-active dokud se nezarovnají, nebo dokud nezbude jen
      // pinned + active (failsafe). Volá se přes requestAnimationFrame
      // aby DOM layout byl už spočítaný.
      let _overflowEvictionScheduled = false;
      function _scheduleOverflowEviction() {
        if (_overflowEvictionScheduled) return;
        if (!tabsBarEl) return;
        _overflowEvictionScheduled = true;
        requestAnimationFrame(() => {
          _overflowEvictionScheduled = false;
          let safety = 50;  // hard guard proti infinite loop
          while (safety-- > 0 && tabsBarEl.scrollWidth > tabsBarEl.clientWidth + 2) {
            const before = tabsState.tabs.length;
            _evictOldestTab(true);  // single-step mode
            if (tabsState.tabs.length === before) break;  // nelze dál (vse pinned/active)
            // Re-render po každém splice — DOM musí reflect aktuální state
            // pro další scrollWidth check (synchronně, ne v rAF).
            _renderTabsBarSync();
          }
        });
      }
      // Sync helper — volá se uvnitř overflow loop. Nesmí volat
      // _scheduleOverflowEviction znovu (infinite recursion guard).
      function _renderTabsBarSync() {
        const wasScheduled = _overflowEvictionScheduled;
        _overflowEvictionScheduled = true;
        renderTabsBar();
        _overflowEvictionScheduled = wasScheduled;
      }

      // Phase 38.4 (11.5.2026 vecer): LRU eviction — zavre nejstarsi
      // unpinned non-active tab kdyz tabs.length > MAX_TABS_VISIBLE,
      // nebo (singleStep=true) jen jeden krok pro overflow eviction.
      function _evictOldestTab(singleStep) {
        while (singleStep || tabsState.tabs.length > MAX_TABS_VISIBLE) {
          // Najdi nejstarsi non-pinned, non-active
          let oldestIdx = -1;
          let oldestTime = Infinity;
          for (let i = 0; i < tabsState.tabs.length; i++) {
            const t = tabsState.tabs[i];
            if (i === tabsState.activeIndex) continue;
            if (t.pinned === true) continue;
            const accessTime = t.lastAccessedAt || 0;
            if (accessTime < oldestTime) {
              oldestTime = accessTime;
              oldestIdx = i;
            }
          }
          if (oldestIdx < 0) break;  // vse pinned nebo jen aktivni
          const victim = tabsState.tabs[oldestIdx];
          try {
            fetch("/api/v1/erp/tabs/" + encodeURIComponent(victim.cislo), {
              method: "DELETE", credentials: "include"
            });
          } catch (e) {}
          try { ErpRefresh.forget(victim.cislo); } catch (e) {}
          tabsState.tabs.splice(oldestIdx, 1);
          if (tabsState.activeIndex > oldestIdx) {
            tabsState.activeIndex--;
          }
          if (singleStep) return;  // overflow eviction = jeden krok
        }
      }

      async function _loadTabData(tab) {
        // Phase 35-E.4 Krok C+: System tab (negative cislo) → render
        // System view bez fetch z /prehled. Data jsou self-contained
        // (System grid si fetchuje vlastni data uvnitr).
        if (tab.cislo < 0) {
          tab.data = { _system: true };  // sentinel — renderTabIntoMain rozumí
          _renderTabIntoMain(tab);
          // Phase 38.5+ (10.5.2026 vecer Marti's debugging): System tabs taky
          // markFresh — security_devices grid + audit-overview byly bug, ikona
          // refresh nikdy nemarkla freshness pro negative cisla → stale
          // detection nikdy nezafungovala. System grids fetchují data uvnitř
          // renderSystemGrid, ale pro MVP označíme fresh při otevření tabu
          // (re-fetch uvnitř system view → re-call markFresh later, nice-to-have).
          if (typeof ErpRefresh !== 'undefined') ErpRefresh.markFresh(tab.cislo);
          return;
        }
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
          // Phase 38.5: marknout grid jako fresh (ikona refreshe → neutral)
          if (typeof ErpRefresh !== 'undefined') ErpRefresh.markFresh(tab.cislo);
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
        // Phase 35-E.4 Krok C+: System tab (negative cislo) → render
        // System view (audit dashboard / native AG Grid).
        if (tab.cislo < 0) {
          // Phase 38.4 Krok 14g-H+27 (15.5.2026 ~20:00, Marti's "pokud
          // soudecek ma core_id, rovnou aktivovat prehled"): synthetic
          // range + core_id check. Pokud node v tree cache má asociovany
          // core, re-dispatch via core_code (jako bychom kliknuli na real
          // prehled). Fallback: info placeholder s identifikatorem core.
          if (tab.cislo <= -100000) {
            // Phase 38.4 Krok 14g-H+29 (15.5.2026 ~20:45, Marti's "nedeje
            // se aktivace prehledu ani po hard reset"): add diagnostics +
            // li.dataset fallback pokud tree cache lookup fails.
            let node = (typeof _findSystemNodeById === "function")
              ? _findSystemNodeById(tab.itemId) : null;

            // Fallback: pokud cache lookup selhal, pokus li.dataset (set v
            // _decorateLeftPanelLi). Tj. real DOM stejne ma core_id v dataset.
            let coreId = node && node.core_id;
            let coreCode = node && node.core_code;
            if (!coreId && typeof tree !== "undefined" && tree && typeof tree.findLiByCislo === "function") {
              const li = tree.findLiByCislo(tab.cislo);
              if (li) {
                coreId = parseInt(li.dataset.coreId || "0", 10) || null;
                coreCode = li.dataset.coreCode || null;
              }
            }

            console.info("[H+29 dispatch] synthetic+core lookup:", {
              cislo: tab.cislo,
              itemId: tab.itemId,
              node_found_in_cache: !!node,
              core_id: coreId,
              core_code: coreCode,
            });

            if (coreId) {
              // Re-dispatch via core_code — pokud core matches known
              // system mode, render system view. Jinak info placeholder.
              const coreMode = coreCode
                ? _systemModeFromItemId(coreCode)
                : null;
              console.info("[H+29 dispatch] coreMode lookup:", coreMode);
              if (coreMode) {
                _renderSystemViewIntoMain(coreMode, tab.label || coreCode);
                return;
              }
              // Phase 38.4 Krok 5.R (17.5.2026 vecer, Marti's "JO, melo
              // by to byt v nezavislem js. TJ ten 5/5"): page render
              // dispatch presunuty do standalone modulu
              // apps/api/static/erp/components/page_render.js (gotcha #100
              // — inline JS v router.py je krehky pro velke bloky).
              if (window.ErpPageRender && typeof window.ErpPageRender.dispatchPageRender === "function") {
                window.ErpPageRender.dispatchPageRender(coreId, coreCode, tab, mainContent);
              } else {
                console.error("[router] ErpPageRender modul neni nacten — hard reload prohlizec.");
                mainContent.innerHTML =
                  '<div style="padding:40px;text-align:center;color:#d4a8a8;">' +
                  '❌ page_render.js modul nenacten — hard reload prohlizec (Ctrl+Shift+R).' +
                  '</div>';
              }
              return;
            }
            // No core associated — info placeholder (drop H+14 silent doctrine
            // pre nove asociace flow — Marti chce vidět něco, ne nic)
            mainContent.innerHTML =
              '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
              '<h2 style="margin:0 0 12px;color:#a8b4c2;font-weight:500;">📁 ' +
              escapeHtml(tab.label || "Soudeček") + '</h2>' +
              '<p style="color:#7a8696;font-size:13px;margin:0;">' +
              'Soudeček bez asociovaného core přehledu. ' +
              'Pravý-klik → 🎨 Design pro vybrání core.' +
              '</p></div>';
            return;
          }
          const mode = _systemModeFromItemId(tab.itemId) || _systemModeFromCislo(tab.cislo);
          if (mode) {
            _renderSystemViewIntoMain(mode, tab.label);
            return;
          }
          // Fallback: System tab bez rozeznatelneho mode → hlaska
          mainContent.innerHTML =
            '<div class="erp-main-error">System tab #' + tab.cislo +
            ' — neznamy view mode (itemId=' + escapeHtml(tab.itemId || "") + ').</div>';
          return;
        }
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
        // Re-create tab metadata (data + gridState se znovu fetchnou).
        // 11.5. fix: restore pinned + lastAccessedAt (default = false + now)
        // tak aby _evictOldestTab měl správný stav pro decisions.
        const now = Date.now();
        tabsState.tabs = persisted.tabs.map(t => ({
          cislo: t.cislo,
          itemId: t.itemId,
          label: t.label,
          data: null,
          gridState: null,
          pinned: t.pinned === true,
          lastAccessedAt: typeof t.lastAccessedAt === "number" ? t.lastAccessedAt : now,
        }));
        const idx = (persisted.activeIndex >= 0 && persisted.activeIndex < tabsState.tabs.length)
          ? persisted.activeIndex
          : 0;
        // 11.5. fix #2: pinned záložky seřadit vlevo (jako po right-click toggle).
        // DB GET vrací podle sort_order (původní pořadí otevření), ale UI musí
        // pinned umístit první. Marti's request — pinned drží přes F5 i pozici.
        // Capture active tab před sort, pak najdi nový index.
        const activeTabRef = tabsState.tabs[idx] || null;
        tabsState.tabs.sort((a, b) => {
          if ((a.pinned || false) !== (b.pinned || false)) {
            return (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0);
          }
          return (b.lastAccessedAt || 0) - (a.lastAccessedAt || 0);
        });
        tabsState.activeIndex = activeTabRef
          ? Math.max(0, tabsState.tabs.indexOf(activeTabRef))
          : 0;
        // 11.5. fix: po restore zavolat eviction — pokud uloženo > MAX_TABS_VISIBLE,
        // oldest unpinned non-active se zahodí (LRU cap drží i napříč reload).
        _evictOldestTab();
        renderTabsBar();
        switchTab(tabsState.activeIndex);
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
                // Phase 38.4 (11.5.2026 vecer): hydrate pinned + lastAccessedAt
                // z DB (priorita nad localStorage). Marti's request — pinned
                // záložky musí přežít F5 reload.
                pinned: t.pinned === true,
                lastAccessedAt: (typeof t.lastAccessedAt === "number")
                  ? t.lastAccessedAt : null,
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
          // Phase 38.5+ (10.5.2026): window.open() z PWA window Chrome
          // interpretuje jako "browser tab" navigation (bila Chrome lista).
          // Pro Chat PWA install s launch_handler.client_mode='focus-existing'
          // musime pouzit anchor click — Chrome's PWA navigation handler
          // detekuje installed PWA scope match a otevre v Chat PWA window
          // (existing focus / new). window.open je programmatic = bypasses
          // PWA detection.
          //
          // Plus named target "strategie-chat" stale soucasti pro fallback
          // (browser without PWA install) — ten alespon focusne existing tab
          // misto noveho.
          const a = document.createElement("a");
          a.href = "/";
          a.target = "strategie-chat";
          a.rel = "noopener";
          document.body.appendChild(a);
          a.click();
          a.remove();
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

