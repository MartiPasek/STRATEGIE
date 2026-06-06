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

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
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
# (DROP Phase 2.C 18.5.) centrala_reader import
# (DROP Phase 2.C 18.5.) render_generator import
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


def _uid_from_token_or_cookie(req: Request) -> int:
    """user_id z Bearer tokenu (nativní mobilní appka — sdílí CardDAV device
    token z "user".carddav_token) NEBO z cookie (PWA). Marti 4.6.2026 —
    background služba nemá cookie, autentizuje se tokenem (jeden token pro
    kontakty i vytáčení). Fallback na cookie když token chybí/neplatí."""
    auth = req.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        tok = auth[7:].strip()
        if tok:
            import hashlib
            from core.database_data import get_data_session as _gds_tok
            from sqlalchemy import text as _sql_tok
            th = hashlib.sha256(tok.encode("utf-8")).hexdigest()
            ds = _gds_tok()
            try:
                uid = ds.execute(_sql_tok(
                    'SELECT user_id FROM "user".carddav_token '
                    'WHERE token_hash = :h AND revoked_at IS NULL'
                ), {"h": th}).scalar()
                if uid is not None:
                    ds.execute(_sql_tok(
                        'UPDATE "user".carddav_token SET last_used_at = now() '
                        'WHERE token_hash = :h'
                    ), {"h": th})
                    ds.commit()
                    return int(uid)
            except Exception:
                ds.rollback()
            finally:
                ds.close()
    return _get_uid(req)


def _require_parent(user_id: int) -> None:
    """Auth gate pro DESIGN / framework / system / audit endpointy:
    jen rodina (is_marti_parent=true). Business/nav endpointy používají
    _require_erp_member (Phase D)."""
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail=(
                "Tato část STRATEGIE ERP (framework / design / system) je "
                "dostupná jen pro rodinu Marti-AI (is_marti_parent=true)."
            ),
        )


# ── Phase D member access (1.6.2026) ────────────────────────────────
# Marti's volba 1.6.: EUROSOFT tenant useři (Pavel Zeman atd.) dostanou
# PLNÝ BUSINESS R/W do ERP — procházet (jen business soudečky), otevírat
# přehledy/formuláře, editovat+přidávat+mazat business záznamy. System
# soudeček (framework builder, audit, Marti-AI paměť) + DESIGN mód zůstanou
# JEN rodičům (is_marti_parent) a jsou členům skryté (tree filter + frontend
# gate). Business endpointy → _require_erp_member; design/system → _require_parent.

def _is_active_eurosoft_member(user_id: int) -> bool:
    """True pokud user je aktivní člen EUROSOFT tenantu (id=2)."""
    from core.database_core import get_core_session
    from modules.auth.application.user_context import _list_user_tenants
    cs = get_core_session()
    try:
        tenants = _list_user_tenants(cs, user_id) or []
        for t in tenants:
            tid = t.get("tenant_id") if isinstance(t, dict) else None
            if tid is not None and int(tid) == EUROSOFT_TENANT_ID:
                return True
        return False
    except Exception:
        return False
    finally:
        cs.close()


def _require_erp_member(user_id: int) -> None:
    """Phase D gate (business/nav endpointy): rodič NEBO aktivní člen
    ERP-enabled tenantu (EUROSOFT id=2)."""
    if is_marti_parent(user_id):
        return
    if _is_active_eurosoft_member(user_id):
        return
    raise HTTPException(
        status_code=403,
        detail="Nemáš přístup do STRATEGIE ERP. Kontaktuj administrátora.",
    )


# Design/system string entity types — blokované pro non-parent v data CRUD
# (design_patch/insert/delete_entity). Člen smí editovat jen business data
# (numeric core_id resolved na datovou tabulku), ne framework metadata
# (comp_def/menu_node/core/data_source/...) ani user management.
_DESIGN_ENTITY_TYPES = frozenset({
    "comp_def", "comp_def_design", "menu_node", "menu_node_design",
    "core", "data_source", "data_source_op", "data_set", "fw_form", "user",
})


def _require_data_write_access(user_id: int, entity_type: str) -> None:
    """Data CRUD gate (design_patch/insert/delete_entity). Rodič smí vše.
    Člen smí jen business data (numeric core_id) — NE framework/system entity
    (string v _DESIGN_ENTITY_TYPES). Defense in depth nad _require_erp_member."""
    _require_erp_member(user_id)
    if is_marti_parent(user_id):
        return
    et = (entity_type or "").strip()
    if not et.isdigit() or et in _DESIGN_ENTITY_TYPES:
        raise HTTPException(
            status_code=403,
            detail=(
                "Úprava framework/system entit je dostupná jen rodičům. "
                "Členové mohou editovat jen business záznamy."
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
def erp_home(req: Request):
    """Phase B nástřel: 3-pane workspace (sidebar tree + main pane prehled+jadro).

    1.6.2026 (Marti, Pavel Zeman bug): bez session NEhážeme holý 401
    "Nejsi přihlášen" (ERP nemá login dialog), ale přesměrujeme na chat
    login s ?return=/erp → po přihlášení se uživatel vrátí zpět na /erp.

    2.6.2026 (Pavel Zeman "web nedostupný"): NE 302 server-redirect! ERP
    Service Worker (network-first) u navigace dělá fetch(redirect:follow)
    → výsledná "redirected" response → Chrome ji pro navigaci ODMÍTNE
    (ERR_FAILED = "web nedostupný"). Vracíme 200 HTML stub s client-side
    přesměrováním → SW dostane čistou 200, žádný redirect, funguje i se
    stávajícím (starým) SW bez reinstalu.
    """
    if not req.cookies.get("user_id"):
        return HTMLResponse(content=(
            '<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            '<meta http-equiv="refresh" content="0; url=/?return=%2Ferp">'
            '<title>STRATEGIE</title></head>'
            '<body style="margin:0;background:#0e0f11;color:#cfd6df;'
            'font-family:system-ui,-apple-system,sans-serif;display:flex;'
            'align-items:center;justify-content:center;height:100vh;">'
            '<div>Přihlášení…</div>'
            '<script>location.replace("/?return=%2Ferp");</script>'
            '</body></html>'
        ))
    uid = _get_uid(req)
    _require_erp_member(uid)
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

    # (DROP Phase 2.C) reader removed

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
            "typ_names": {},  # Phase 2.C: dropped
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

    tid = _get_tenant_id(uid)
    return JSONResponse({
        "ok": True,
        "phase": "FW",
        "mcp_klient_available": False,  # Phase 2.C: centrala_reader dropped
        "supported_typs": 0,
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
    _require_erp_member(uid)

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


# ─────────────────────────────────────────────────────────────────────
# Phase SYSTEM NEW (22.5.2026): 4 HC handlers dropped.
# - /system/audit-overview (4 modes: audited/all/stats/tabs)
# - /system/audit-conversation/{conv_id}/thoughts
# - /system/audit-conversation/{conv_id}/timeline
# - /system/framework (3 modes: menu_nodes/data_sources/data_sets)
#
# Vse migrated to FW chain pres fw.menu_node 'system_new.audit*' /
# 'system_new.framework*' + fw.data_source + fw.data_set with SELECT *
# pattern (Marti's MVP doctrine 21.5.).
#
# ~800 lines dropped. ORM models (Conversation, ConversationShare,
# Persona, Tenant, etc.) zustavaji v models_*.py — pouzivaji se v
# chat flow, persona management, Phase 38 auth.
# ─────────────────────────────────────────────────────────────────────


def _introspect_edit_base_table(session, core_id: int):
    """1.6.2026 (Marti: "detail core = jednoduchý SELECT WHERE ID=:ID"): pro
    edit core s VLASTNÍM data_set edit-opem (≠ grid select) parsuje base table
    z FROM + introspektuje sloupce (MCP describe_table pro mssql / info_schema
    pro pg). Vrací {schema, table, columns:[names], db_type} nebo None (caller
    fallback na grid select). Zvládne `SELECT *` i `:ID` (neběží query — čte
    schema tabulky).
    """
    import re as _re_iebt
    from sqlalchemy import text as _sql_iebt

    row = session.execute(_sql_iebt("""
        SELECT dset.sql_text, dc.db_type, op.data_set_id,
               (SELECT op2.data_set_id FROM fw.data_source_op op2
                WHERE op2.data_source_id = op.data_source_id AND op2.operation_kind = 'select'
                ORDER BY op2.is_default DESC NULLS LAST, op2.id LIMIT 1) AS sel_dset_id
        FROM fw.data_source_op op
        JOIN fw.data_set dset ON dset.id = op.data_set_id
        LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
        WHERE op.core_id = :cid AND op.operation_kind IN ('edit', 'insert')
        ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id LIMIT 1
    """), {"cid": core_id}).mappings().one_or_none()
    if not row or not row["sql_text"]:
        return None
    if row["data_set_id"] == row["sel_dset_id"]:
        return None  # edit-op sdílí grid select → není dedikovaný edit-select

    sql = row["sql_text"]
    db_type = (row["db_type"] or "").lower().strip()
    s = _re_iebt.sub(r'--[^\n]*', ' ', sql)
    s = _re_iebt.sub(r'/\*.*?\*/', ' ', s, flags=_re_iebt.S)
    m = _re_iebt.search(
        r'\bFROM\s+[\[\"]?([A-Za-z_]\w*)[\]\"]?\s*\.\s*[\[\"]?([A-Za-z_]\w*)[\]\"]?',
        s, _re_iebt.I,
    )
    if m:
        schema, table = m.group(1), m.group(2)
    else:
        m2 = _re_iebt.search(r'\bFROM\s+[\[\"]?([A-Za-z_]\w*)[\]\"]?', s, _re_iebt.I)
        if not m2:
            return None
        schema, table = None, m2.group(1)

    if db_type == "mssql":
        try:
            from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
            import json as _j_iebt
            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                return None
            rj = mcp.call_tool_sync(
                "eurosoft_strategie_describe_table",
                {"schema": schema or "dbo", "table": table, "db_name": "DB_EC"},
                conversation_id=None,
            )
            res = _j_iebt.loads(rj) if isinstance(rj, str) else rj
            if not isinstance(res, dict) or res.get("ok", True) is not True:
                return None
            cols = [(c.get("name") or c.get("column_name") or "")
                    for c in (res.get("columns") or []) if isinstance(c, dict)]
            cols = [c for c in cols if c]
        except Exception:
            return None
    else:
        from sqlalchemy import text as _t2
        cols = [r2[0] for r2 in session.execute(_t2("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = :s AND table_name = :t ORDER BY ordinal_position
        """), {"s": (schema or "public").lower(), "t": table.lower()}).fetchall()]
    if not cols:
        return None
    return {"schema": schema, "table": table, "columns": cols, "db_type": db_type}


@api_router.get("/core/{core_id}/dataset-fields")
def core_dataset_fields(core_id: int, req: Request) -> JSONResponse:
    """Krok H+6 (1.6.2026, Marti orchestrator): fieldy datasetu pro edit core.

    Orchestrator (sandbox subprocess) má MCP UNREACHABLE (vlastní klient se
    nepřipojí) → nemůže si fieldy MSSQL datasetu zjistit. Tenhle endpoint běží
    v API procesu (kde MCP funguje — grid loady to dokazují) — resolve edit
    core → data_source → SELECT op (limit 1 přes run_data_source) → názvy
    sloupců výsledku. Frontend je pošle orchestrátoru jako ctx.fields.
    Parent-only (orchestrator je taky parent-only).

    Returns: {ok, fields: [str], data_source_code} | {ok:False, error}
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_data import get_data_session as _gds_df
    from sqlalchemy import text as _sql_df

    session = _gds_df()
    try:
        # 1.6.2026 (Marti): edit core s VLASTNÍM edit-selectem (SELECT * FROM
        # tabulka WHERE ID=:ID) → introspektuj base tabulku (reálné sloupce),
        # NE grid composite. Zvládne SELECT * i :ID (čte schema, neběží query).
        _edit_tbl = _introspect_edit_base_table(session, core_id)
        if _edit_tbl and _edit_tbl.get("columns"):
            _et_name = ((_edit_tbl.get("schema") + ".") if _edit_tbl.get("schema") else "") + _edit_tbl["table"]
            return JSONResponse({
                "ok": True,
                "fields": _edit_tbl["columns"],
                "source": "edit_table_introspect",
                "edit_table": _et_name,
            })

        op_row = session.execute(_sql_df("""
            SELECT ds.code
            FROM fw.data_source_op op
            JOIN fw.data_source ds ON ds.id = op.data_source_id
            WHERE op.core_id = :cid
              AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()
        if not op_row or not op_row["code"]:
            return JSONResponse(
                {"ok": False, "error": f"core #{core_id}: žádný edit/insert op s data_source.code"},
                status_code=404,
            )
        ds_code = op_row["code"]
        try:
            result = ds_runner.run_data_source(
                session, code=ds_code, raw_params={"limit": "1"},
                variant="default", kind="select",
            )
        except Exception as exc:
            return JSONResponse(
                {"ok": False, "error": f"select run failed: {type(exc).__name__}: {exc}"},
                status_code=500,
            )
        rows = result.get("rows") or []
        if not rows:
            return JSONResponse(
                {"ok": False, "error": "select vrátil 0 rows — nelze odvodit sloupce"},
                status_code=200,
            )
        fields = list(rows[0].keys())
        return JSONResponse({"ok": True, "fields": fields, "data_source_code": ds_code})
    finally:
        try:
            session.close()
        except Exception:
            pass


@api_router.get("/core/{core_id}/dataset-sql")
def core_dataset_sql(core_id: int, req: Request) -> JSONResponse:
    """1.6.2026 (Marti: "na CORE zobrazit dataset, ať se nezamotáme"): vrátí
    raw SELECT sql_text data_source daného edit core + metadata. Pro UI náhled
    + debug save bindingů (resolver). Parent-only.

    Returns: {ok, sql, data_source{id,code,name}, data_set_id, db_type, connection{id,code}}
    """
    uid = _get_uid(req)
    _require_parent(uid)

    from core.database_data import get_data_session as _gds_dsql
    from sqlalchemy import text as _sql_dsql

    session = _gds_dsql()
    try:
        row = session.execute(_sql_dsql("""
            SELECT ds.id AS ds_id, ds.code AS ds_code, ds.name AS ds_name,
                   dset.id AS dset_id, dset.sql_text AS sql_text,
                   dc.id AS conn_id, dc.code AS conn_code, dc.db_type AS db_type
            FROM fw.data_source_op op
            JOIN fw.data_source ds ON ds.id = op.data_source_id
            LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
            LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
            WHERE op.data_source_id = (
                SELECT op2.data_source_id FROM fw.data_source_op op2
                WHERE op2.core_id = :cid AND op2.operation_kind IN ('edit', 'insert')
                ORDER BY CASE op2.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op2.id ASC
                LIMIT 1
            )
              AND op.operation_kind = 'select'
            ORDER BY op.is_default DESC NULLS LAST, op.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()
        if not row:
            return JSONResponse(
                {"ok": False, "error": f"core #{core_id}: nenalezen SELECT op datasetu (edit/insert op → data_source → select)"},
                status_code=404,
            )
        # edit-op vlastní data_set sql (pokud má dedikovaný — pro prefill editoru)
        edit_row = session.execute(_sql_dsql("""
            SELECT dset.sql_text, op.data_set_id
            FROM fw.data_source_op op
            JOIN fw.data_set dset ON dset.id = op.data_set_id
            WHERE op.core_id = :cid AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()
        # dedikovaný edit-select jen pokud != grid select data_set
        edit_sql = None
        if edit_row and edit_row["data_set_id"] != row["dset_id"]:
            edit_sql = edit_row["sql_text"]
        return JSONResponse({
            "ok": True,
            "core_id": core_id,
            "data_source": {"id": row["ds_id"], "code": row["ds_code"], "name": row["ds_name"]},
            "data_set_id": row["dset_id"],
            "db_type": row["db_type"],
            "connection": {"id": row["conn_id"], "code": row["conn_code"]},
            "sql": row["sql_text"] or "",
            "edit_sql": edit_sql,
        })
    finally:
        try:
            session.close()
        except Exception:
            pass


@api_router.post("/core/{core_id}/edit-select")
async def core_set_edit_select(core_id: int, req: Request) -> JSONResponse:
    """1.6.2026 (Marti: "detail core = jednoduchý SELECT WHERE ID=:ID, ne grid
    composite"): nastaví edit-opu VLASTNÍ data_set s jednoduchým edit-selectem.
    Grid composite (select op) zůstává nedotčený. Parent-only.

    Body: {sql}. Pokud edit-op už má vlastní data_set → UPDATE sql_text. Jinak
    naklonuje grid data_set (schema-agnostic přes information_schema), přepíše
    sql_text + code, a přiřadí edit-opu. Returns {ok, data_set_id, created}.
    """
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        body = await req.json()
    except Exception:
        body = {}
    new_sql = (body.get("sql") or "").strip()
    if not new_sql:
        return JSONResponse({"ok": False, "error": "prázdný sql"}, status_code=422)

    from core.database_data import get_data_session as _gds_es
    from sqlalchemy import text as _sql_es

    session = _gds_es()
    try:
        op = session.execute(_sql_es("""
            SELECT op.id AS op_id, op.data_source_id, op.data_set_id
            FROM fw.data_source_op op
            WHERE op.core_id = :cid AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()
        if not op:
            return JSONResponse(
                {"ok": False, "error": f"core #{core_id}: žádný edit/insert op"},
                status_code=404,
            )
        sel = session.execute(_sql_es("""
            SELECT op.data_set_id FROM fw.data_source_op op
            WHERE op.data_source_id = :dsid AND op.operation_kind = 'select'
            ORDER BY op.is_default DESC NULLS LAST, op.id ASC LIMIT 1
        """), {"dsid": op["data_source_id"]}).mappings().one_or_none()
        select_dset_id = sel["data_set_id"] if sel else None
        edit_dset_id = op["data_set_id"]

        # edit-op už má VLASTNÍ data_set (ne sdílený s grid select) → update sql
        if edit_dset_id is not None and edit_dset_id != select_dset_id:
            session.execute(_sql_es("UPDATE fw.data_set SET sql_text = :s WHERE id = :i"),
                            {"s": new_sql, "i": edit_dset_id})
            session.commit()
            return JSONResponse({"ok": True, "data_set_id": edit_dset_id, "created": False})

        # jinak CREATE dedicated data_set — clone grid template (schema-agnostic)
        if select_dset_id is None:
            return JSONResponse(
                {"ok": False, "error": "select op nemá data_set (nelze klonovat template)"},
                status_code=422,
            )
        cols = [r[0] for r in session.execute(_sql_es("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'fw' AND table_name = 'data_set'
            ORDER BY ordinal_position
        """)).fetchall()]
        skip = {"id", "created_at", "updated_at"}
        clone_cols = [c for c in cols if c not in skip]
        sel_parts = []
        for c in clone_cols:
            if c == "sql_text":
                sel_parts.append(":newsql AS sql_text")
            elif c == "code":
                sel_parts.append("(COALESCE(code, 'ds') || '_edit_c" + str(int(core_id)) + "') AS code")
            else:
                sel_parts.append(c)
        new_id = session.execute(_sql_es(
            "INSERT INTO fw.data_set (" + ", ".join(clone_cols) + ") "
            "SELECT " + ", ".join(sel_parts) + " FROM fw.data_set WHERE id = :tid RETURNING id"
        ), {"newsql": new_sql, "tid": select_dset_id}).scalar()
        session.execute(_sql_es("UPDATE fw.data_source_op SET data_set_id = :nid WHERE id = :oid"),
                        {"nid": new_id, "oid": op["op_id"]})
        session.commit()
        return JSONResponse({"ok": True, "data_set_id": new_id, "created": True})
    except Exception as exc:
        session.rollback()
        return JSONResponse({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status_code=500)
    finally:
        try:
            session.close()
        except Exception:
            pass


def _ds_execute_error_response(exc) -> JSONResponse:
    """Klasifikace chyby data_source execute (Marti 3.6.2026, prezentace eve).

    MCP / EUROSOFT connectivity (MSSQL DB_EC přes EUROSOFT MCP — timeout, drop,
    circuit open, unreachable) → 503 + PŘÍVĚTIVÁ hláška, že je dočasně nedostupná
    externí Centrála, NE chyba STRATEGIE. Frontend ji zobrazí v gridu místo
    prázdna. Skutečná SQL chyba (syntax, sloupec) → 500 sql_execute_failed (jako dřív).
    """
    s = str(exc) or ""
    low = s.lower()
    _mcp_markers = (
        "mcp_call_failed", "mcp_unreachable", "circuit_open", "mcp tool",
        "timeouterror", "timeout", "closedresource", "brokenresource",
        "endofstream", "mcp strategie_query_raw", "mcp response",
    )
    if any(m in low for m in _mcp_markers):
        return JSONResponse({
            "ok": False,
            "error": "source_unavailable",
            "source": "EUROSOFT (Centrála 1)",
            "user_message": (
                "Spojení s daty EUROSOFT (Centrála 1) je teď dočasně nedostupné. "
                "Systém se sám zkouší znovu připojit — dej tomu chvíli a načti "
                "znovu. Není to chyba STRATEGIE."
            ),
            "detail": s[:500],
        }, status_code=503)
    return JSONResponse(
        {"ok": False, "error": "sql_execute_failed", "detail": s},
        status_code=500,
    )


@api_router.get("/data-by-id/{ds_id}")
def data_source_execute_by_id(
    ds_id: int,
    req: Request,
    variant: str = "default",
) -> JSONResponse:
    """Phase 38.4 Krok 5.R-D+1 — ID-first data executor.

    URL: GET /api/v1/erp/data-by-id/{ds_id}?variant=default&limit=100&...

    Lookup data_source.code by ds_id, delegate na run_data_source(code=...).
    Pokud data_source.code je NULL nebo data_source neni found → 404.

    Returns: identicky shape jako /data/{code} (run_data_source response).
    """
    uid = _get_uid(req)
    _require_erp_member(uid)

    from core.database_data import get_data_session as _gds_dbi
    from sqlalchemy import text as _sql_dbi

    session = _gds_dbi()
    try:
        # Lookup data_source.code by ID
        ds_row = session.execute(_sql_dbi("""
            SELECT id, code, name, status
            FROM fw.data_source
            WHERE id = :did
        """), {"did": ds_id}).mappings().one_or_none()
        if not ds_row:
            return JSONResponse(
                {"ok": False, "error": f"data_source id={ds_id} nenalezen"},
                status_code=404,
            )
        ds_code = ds_row["code"]
        if not ds_code:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"data_source id={ds_id} nema code (NULL). "
                        f"Pragmatic fix: UPDATE fw.data_source SET code='{ds_id}' WHERE id={ds_id}"
                    ),
                },
                status_code=404,
            )

        # Reuse existing run_data_source via code
        raw_params = dict(req.query_params)
        raw_params.pop("variant", None)
        try:
            result = ds_runner.run_data_source(
                session,
                code=ds_code,
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
            # Phase Etapa A+ polish (20.5.2026, Marti's catch z Praha hotelu):
            # wire logger.error → fw.diag_log. Bez tohoto by SQL execute failures
            # byly tiche pro audit ("Marti's permission gap z dnesniho rana").
            # Fix #2 (20.5. vecer, Marti's "musime videt vic"): expanded context —
            # data_source_code/id, variant, fastapi_endpoint, user_id, raw_params.
            # `locals().get(...)` pattern protoze 3 endpointy maji `ds_code` + `ds_id`,
            # 4. (data_source_execute) ma jen `code` z path param.
            _locals_snapshot = locals()
            logger.error(
                "data_source SQL execute FAILED",
                exc_info=exc,
                extra={
                    "endpoint_context": "ds_runner.run_data_source",
                    "exception_type": type(exc).__name__,
                    "exception_str": str(exc)[:500],
                    # Fix #2 — rich context pre drill-down:
                    "data_source_code": _locals_snapshot.get("ds_code") or _locals_snapshot.get("code"),
                    "data_source_id": _locals_snapshot.get("ds_id"),
                    "variant": variant,
                    "fastapi_endpoint": req.url.path,
                    "http_method": req.method,
                    "user_id": uid,
                    "raw_params_keys": list(raw_params.keys()) if raw_params else [],
                    "raw_params_preview": {k: str(v)[:200] for k, v in (raw_params or {}).items()},
                },
            )
            return _ds_execute_error_response(exc)
        except ds_runner.DataSourceError as exc:
            return JSONResponse(
                {"ok": False, "error": "data_source_error", "detail": str(exc)},
                status_code=400,
            )
    finally:
        session.close()

    return JSONResponse(jsonable_encoder(result))


# ════════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 5.R-D+1 (18.5.2026 rano, Marti's "refactor code na ID"):
# ID-first endpoint parallel s /data/{code}. Marti's doctrine "ID je svaty"
# (11.5. Krok 13.0) applied k data_source executor. /data/{code} zachovany
# pro backward compat (Form 1 data source picker + jine callers).
# ════════════════════════════════════════════════════════════════════════════

@api_router.get("/data-by-id/{ds_id}")
def data_source_execute_by_id(
    ds_id: int,
    req: Request,
    variant: str = "default",
) -> JSONResponse:
    """Phase 38.4 Krok 5.R-D+1 — ID-first data executor.

    URL: GET /api/v1/erp/data-by-id/{ds_id}?variant=default&limit=100&...

    Lookup data_source.code by ds_id, delegate na run_data_source(code=...).
    Pokud data_source.code je NULL nebo data_source neni found → 404.

    Returns: identicky shape jako /data/{code} (run_data_source response).
    """
    uid = _get_uid(req)
    _require_erp_member(uid)

    from core.database_data import get_data_session as _gds_dbi
    from sqlalchemy import text as _sql_dbi

    session = _gds_dbi()
    try:
        # Lookup data_source.code by ID
        ds_row = session.execute(_sql_dbi("""
            SELECT id, code, name, status
            FROM fw.data_source
            WHERE id = :did
        """), {"did": ds_id}).mappings().one_or_none()
        if not ds_row:
            return JSONResponse(
                {"ok": False, "error": f"data_source id={ds_id} nenalezen"},
                status_code=404,
            )
        ds_code = ds_row["code"]
        if not ds_code:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"data_source id={ds_id} nema code (NULL). "
                        f"Pragmatic fix: UPDATE fw.data_source SET code='{ds_id}' WHERE id={ds_id}"
                    ),
                },
                status_code=404,
            )

        # Reuse existing run_data_source via code
        raw_params = dict(req.query_params)
        raw_params.pop("variant", None)
        try:
            result = ds_runner.run_data_source(
                session,
                code=ds_code,
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
            # Phase Etapa A+ polish (20.5.2026, Marti's catch z Praha hotelu):
            # wire logger.error → fw.diag_log. Bez tohoto by SQL execute failures
            # byly tiche pro audit ("Marti's permission gap z dnesniho rana").
            # Fix #2 (20.5. vecer, Marti's "musime videt vic"): expanded context —
            # data_source_code/id, variant, fastapi_endpoint, user_id, raw_params.
            # `locals().get(...)` pattern protoze 3 endpointy maji `ds_code` + `ds_id`,
            # 4. (data_source_execute) ma jen `code` z path param.
            _locals_snapshot = locals()
            logger.error(
                "data_source SQL execute FAILED",
                exc_info=exc,
                extra={
                    "endpoint_context": "ds_runner.run_data_source",
                    "exception_type": type(exc).__name__,
                    "exception_str": str(exc)[:500],
                    # Fix #2 — rich context pre drill-down:
                    "data_source_code": _locals_snapshot.get("ds_code") or _locals_snapshot.get("code"),
                    "data_source_id": _locals_snapshot.get("ds_id"),
                    "variant": variant,
                    "fastapi_endpoint": req.url.path,
                    "http_method": req.method,
                    "user_id": uid,
                    "raw_params_keys": list(raw_params.keys()) if raw_params else [],
                    "raw_params_preview": {k: str(v)[:200] for k, v in (raw_params or {}).items()},
                },
            )
            return _ds_execute_error_response(exc)
        except ds_runner.DataSourceError as exc:
            return JSONResponse(
                {"ok": False, "error": "data_source_error", "detail": str(exc)},
                status_code=400,
            )
    finally:
        session.close()

    return JSONResponse(jsonable_encoder(result))


# ════════════════════════════════════════════════════════════════════════════
# Phase 38.4 Krok 5.R-D+1 (18.5.2026 rano, Marti's "refactor code na ID"):
# ID-first endpoint parallel s /data/{code}. Marti's doctrine "ID je svaty"
# (11.5. Krok 13.0) applied k data_source executor. /data/{code} zachovany
# pro backward compat (Form 1 data source picker + jine callers).
# ════════════════════════════════════════════════════════════════════════════

@api_router.get("/data-by-id/{ds_id}")
def data_source_execute_by_id(
    ds_id: int,
    req: Request,
    variant: str = "default",
) -> JSONResponse:
    """Phase 38.4 Krok 5.R-D+1 — ID-first data executor.

    URL: GET /api/v1/erp/data-by-id/{ds_id}?variant=default&limit=100&...

    Lookup data_source.code by ds_id, delegate na run_data_source(code=...).
    Pokud data_source.code je NULL nebo data_source neni found → 404.

    Returns: identicky shape jako /data/{code} (run_data_source response).
    """
    uid = _get_uid(req)
    _require_erp_member(uid)

    from core.database_data import get_data_session as _gds_dbi
    from sqlalchemy import text as _sql_dbi

    session = _gds_dbi()
    try:
        # Lookup data_source.code by ID
        ds_row = session.execute(_sql_dbi("""
            SELECT id, code, name, status
            FROM fw.data_source
            WHERE id = :did
        """), {"did": ds_id}).mappings().one_or_none()
        if not ds_row:
            return JSONResponse(
                {"ok": False, "error": f"data_source id={ds_id} nenalezen"},
                status_code=404,
            )
        ds_code = ds_row["code"]
        if not ds_code:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"data_source id={ds_id} nema code (NULL). "
                        f"Pragmatic fix: UPDATE fw.data_source SET code='{ds_id}' WHERE id={ds_id}"
                    ),
                },
                status_code=404,
            )

        # Reuse existing run_data_source via code
        raw_params = dict(req.query_params)
        raw_params.pop("variant", None)
        try:
            result = ds_runner.run_data_source(
                session,
                code=ds_code,
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
            # Phase Etapa A+ polish (20.5.2026, Marti's catch z Praha hotelu):
            # wire logger.error → fw.diag_log. Bez tohoto by SQL execute failures
            # byly tiche pro audit ("Marti's permission gap z dnesniho rana").
            # Fix #2 (20.5. vecer, Marti's "musime videt vic"): expanded context —
            # data_source_code/id, variant, fastapi_endpoint, user_id, raw_params.
            # `locals().get(...)` pattern protoze 3 endpointy maji `ds_code` + `ds_id`,
            # 4. (data_source_execute) ma jen `code` z path param.
            _locals_snapshot = locals()
            logger.error(
                "data_source SQL execute FAILED",
                exc_info=exc,
                extra={
                    "endpoint_context": "ds_runner.run_data_source",
                    "exception_type": type(exc).__name__,
                    "exception_str": str(exc)[:500],
                    # Fix #2 — rich context pre drill-down:
                    "data_source_code": _locals_snapshot.get("ds_code") or _locals_snapshot.get("code"),
                    "data_source_id": _locals_snapshot.get("ds_id"),
                    "variant": variant,
                    "fastapi_endpoint": req.url.path,
                    "http_method": req.method,
                    "user_id": uid,
                    "raw_params_keys": list(raw_params.keys()) if raw_params else [],
                    "raw_params_preview": {k: str(v)[:200] for k, v in (raw_params or {}).items()},
                },
            )
            return _ds_execute_error_response(exc)
        except ds_runner.DataSourceError as exc:
            return JSONResponse(
                {"ok": False, "error": "data_source_error", "detail": str(exc)},
                status_code=400,
            )
    finally:
        session.close()

    return JSONResponse(jsonable_encoder(result))


@api_router.get("/data/{code}")
def data_source_execute(
    code: str,
    req: Request,
    variant: str = "default",
    kind: str = "select",
) -> JSONResponse:
    """Phase 38.4 Krok 12 — generic A3 runtime executor.

    URL: GET /api/v1/erp/data/{code}?variant=default&kind=select&limit=100&tenant_id=...

    Path: code — fw.data_source.code (audit_audited, framework_data_sources, ...)
    Query:
      - variant (default 'default')
      - kind (default 'select') — Krok H+3 26.5.2026 ranni: support pre
        polymorphic operation_kind (select, select-detail, atd.). Per-master
        nested grids (Volba A z 24.5.) posilaji 'select-detail' pro
        per-master SQL filter (:master_id), zatimco standalone soudecky
        posilaji default 'select' (= bez :master_id).
        Marti's "uniformita vitezi" doctrine (11.5. Krok 13) — jeden
        data_source + N ops ruzneho kind, ne N data_sources.
      - libovolné další named params pro sql_text (master_id, atd.)

    Returns: JSON s rows + applied_params + data_source/operation metadata.
    """
    uid = _get_uid(req)
    _require_erp_member(uid)

    # Local import (gotcha #7 — UnboundLocalError prevention)
    from core.database_data import get_data_session as _gds_data

    raw_params = dict(req.query_params)
    raw_params.pop("variant", None)  # variant je explicit kwarg
    raw_params.pop("kind", None)     # kind je explicit kwarg (Krok H+3)

    session = _gds_data()
    try:
        try:
            result = ds_runner.run_data_source(
                session,
                code=code,
                raw_params=raw_params,
                variant=variant,
                kind=kind,
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
            # Phase Etapa A+ polish (20.5.2026, Marti's catch z Praha hotelu):
            # wire logger.error → fw.diag_log. Bez tohoto by SQL execute failures
            # byly tiche pro audit ("Marti's permission gap z dnesniho rana").
            # Fix #2 (20.5. vecer, Marti's "musime videt vic"): expanded context —
            # data_source_code/id, variant, fastapi_endpoint, user_id, raw_params.
            # `locals().get(...)` pattern protoze 3 endpointy maji `ds_code` + `ds_id`,
            # 4. (data_source_execute) ma jen `code` z path param.
            _locals_snapshot = locals()
            logger.error(
                "data_source SQL execute FAILED",
                exc_info=exc,
                extra={
                    "endpoint_context": "ds_runner.run_data_source",
                    "exception_type": type(exc).__name__,
                    "exception_str": str(exc)[:500],
                    # Fix #2 — rich context pre drill-down:
                    "data_source_code": _locals_snapshot.get("ds_code") or _locals_snapshot.get("code"),
                    "data_source_id": _locals_snapshot.get("ds_id"),
                    "variant": variant,
                    "fastapi_endpoint": req.url.path,
                    "http_method": req.method,
                    "user_id": uid,
                    "raw_params_keys": list(raw_params.keys()) if raw_params else [],
                    "raw_params_preview": {k: str(v)[:200] for k, v in (raw_params or {}).items()},
                },
            )
            return _ds_execute_error_response(exc)
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
    _require_erp_member(uid)

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
        "label": row_dict.get("label"),
        "parent_id": row_dict.get("parent_id"),
        "sort_order": row_dict.get("sort_order"),
        "status": row_dict.get("status"),
        "visibility_scope": row_dict.get("visibility_scope"),
        "framework_jadro_id": row_dict.get("framework_jadro_id"),
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
        "version": row_dict.get("version"),
        "shadow_mode": row_dict.get("shadow_mode"),
        "created_at": _iso(row_dict.get("created_at")),
        "updated_at": _iso(row_dict.get("updated_at")),
    }


def _fetch_menu_node(ds, where_sql: str, params: dict) -> dict | None:
    """SELECT n.* FROM fw.menu_node n WHERE ... (Phase: code column dropped 22.5.)."""
    sql = _sql_text_fw(f"""
        SELECT n.*
        FROM fw.menu_node n
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

    Primary: fw.comp_def WHERE core_id = :core_id (Phase 38.4
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
                   core_id
            FROM fw.comp_def
            WHERE core_id = :core_id
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
                NULL::INTEGER AS core_id
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
    label = (body.get("label") or "").strip()
    parent_id = body.get("parent_id")
    sort_order_in = body.get("sort_order")

    # Validation
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

        # Idempotency check dropped (code column removed 22.5.) — DB has no
        # unique constraint on (parent_id, label). Multiple soudecky se stejnym
        # label povolene; user vidi labels v sidebaru a sam vola jinak.

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
                "label": label,
                "parent_id": parent_id,
                "sort_order": sort_order_resolved,
                "status": "active",
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
                    f"+ menu_node label='{label}' parent_id={parent_id} "
                    f"by {caller_display}"
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


# /design/menu-node-by-code/{code} dropped 22.5.2026 — code column removed.
# Frontend uses /design/menu-node/{id} (ID-based, line 1562).


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
    přes menu_node.menu_node_pk → core_id. Tím akce 2 + 3 chodí i pro System grids.
    """
    import re
    from core.database_data import get_data_session as _gds_fw
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_fw()
    try:
        # Primary: přímý match fw.core.code
        core = _fetch_core(ds, "c.code = :code", {"code": core_code})

        # Phase 22.5.2026: System grid prefix `core_-{cislo}` fallback dropped.
        # cislo_def column removed — lookup by negative synthetic cislo no longer
        # possible. Frontend now sends menu_node_pk directly (no cislo_def).
        # Phase 38.4 Krok 5.R-C+5.1 (18.5.2026 vecer): regex rename z
        # `^prehled_` na `^core_` po Krok 5.R-C+2 layoutKey rename.
        if not core:
            m = re.match(r"^core_(-?\d+)$", core_code)
            if m:
                cislo = int(m.group(1))
                # Najdi menu_node s tim cislo_def, vezmi jeho core_id
                # Phase 22.5.2026: cislo_def dropped from fw.menu_node.
                # `cislo` value is now menu_node.id directly — use id lookup:
                mn_for_cislo = _fetch_menu_node(
                    ds, "n.id = :id", {"id": cislo}
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

        form_core_data = None  # Phase fw.core slim 20.5.2026: form_core_id sloupec dropnut

        return JSONResponse(jsonable_encoder({
            "menu_node": _serialize_menu_node(mn) if mn else None,
            "core": _serialize_core(core),
            "columns": columns,
            "data_source": _serialize_data_source(data_source) if data_source else None,
            "form_core": form_core_data,  # Phase 2.A hotfix
        }))
    finally:
        ds.close()



# Phase fw.core slim 20.5.2026: design_scaffold_form endpoint DROPPED (Marti's Decision 2A)


# ────────────────────────────────────────────────────────────────────
# Phase 38.4 Krok 14b (12.5.2026 vecer): fw-form template renderer
#
# Marti's pivot z 12.5. večera: build fw-native form rendering. Marti's
# *„template formu uz s panelem"* + Marti-AI's flat-data doctrine
# (region_slot column → field-level section info, žádný container comp_def).
#
# Architektura:
#   fw.core (kind='form', data_entity_type='user')
#   └── fw.comp_def (type_id=302 form, core_id=core.id)
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
            "id", "status", "login_name",
            "legal_name", "first_name", "last_name",
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
            "status", "visibility_scope", "core_id",
            "framework_jadro_id", "special_handler", "is_immutable",
            "description_user", "description_system",
            "created_at", "updated_at",
        ],
    },
    "core": {
        "schema": "fw",
        "table": "core",
        "id_column": "id",
        # Phase fw.core slim 20.5.2026 (Marti's 1B+2A): drop 9 sloupcu
        # layout_type/data_entity_type/data_source_config/parent_framework_id/
        # layout_template/template_id/origin_menu_node_id/origin_cmi_id/form_core_id.
        "select_columns": [
            "id", "code", "label",
            "version",
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
    # + core_id — zero references v code).
    "comp_def": {
        "schema": "fw",
        "table": "comp_def",
        "id_column": "id",
        "select_columns": [
            "id", "name", "caption",
            "type_id",
            "core_id", "parent_comp_def_id",
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
    # Excel mode Faze 2-B Step 3 wire (24.5.2026 vecer pozde, Marti's
    # "musi chodit i v detailu gridu" requirement): data_source_op entity
    # pro detail grid Save flow (data_source_op_detail.js).
    # Detail grid renderuje fw.data_source_op rows pro master fw.data_source row.
    # select_columns=None -> trust frontend (Marti's "NULL = all editable"
    # doctrine z 22.5. vecer, applied napric design forms).
    "data_source_op": {
        "schema": "fw",
        "table": "data_source_op",
        "id_column": "id",
        "select_columns": None,  # NULL = no whitelist (trust frontend)
    },
    # Krok 5-B Fix (28.5.2026 vecer pozde, Marti's "dnesni den blbec"):
    # DataSets edit form crash — _FW_FORM_ENTITY_MAP nemelo entries pro
    # data_set ani data_source entity. Frontend resolved fw.core code='fw_form'
    # a dispatch na PATCH endpoint /design/fw_form/{id} → backend KeyError →
    # API worker crash → 503. Fix: pridat data_set + data_source entries +
    # alias 'fw_form' → data_set (Marti's DataSets core code).
    "data_set": {
        "schema": "fw",
        "table": "data_set",
        "id_column": "id",
        "select_columns": None,  # NULL = trust frontend
    },
    "data_source": {
        "schema": "fw",
        "table": "data_source",
        "id_column": "id",
        "select_columns": None,  # NULL = trust frontend
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
# Krok 5-B Fix (28.5.2026 vecer pozde): DataSets fw.core has code='fw_form'.
_FW_FORM_ENTITY_MAP["fw_form"] = _FW_FORM_ENTITY_MAP["data_set"]
_FW_FORM_ENTITY_MAP["data_set_design"] = _FW_FORM_ENTITY_MAP["data_set"]
_FW_FORM_ENTITY_MAP["data_source_design"] = _FW_FORM_ENTITY_MAP["data_source"]

# Phase 38.4 Krok 5.N-2 LIVE (22.5.2026 vecer, Marti's "čistý stůl"):
# System cores (Diag log, DataSets, DataSources, DB Connections, Knowledge
# Entries, atd.) NEMAJÍ explicit entries v _FW_FORM_ENTITY_MAP. Resolvuji
# se DB-driven pres fw.data_source.target_xxx columns (deployed _phase_krok5_n_2_
# data_source_target_columns.sql). Marti's audit log RO doctrine (21.5. Fix N)
# zustava intact — direct UPDATE pres design_patch_entity je servisni override
# (Excel mode = vedome zapnuti, Marti's "dva mody, nez to vsechno doladime").


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
    22: _FW_FORM_ENTITY_MAP["user"],       # user_edit form_core (Marti's code: '22a')
    23: _FW_FORM_ENTITY_MAP["core"],       # core_design form_core (Marti's code: '23a')
    # Phase 38.4 Krok 5.N-2 LIVE (22.5.2026 vecer, Marti's "čistý stůl"):
    # Ostatní cores resolvuji DB-driven pres fw.data_source.target_xxx columns.
    # _resolve_entity_config_from_db() je PRIMARY path; this map je legacy
    # fallback pro 22+23 (user/core form_cores postavené pre-Krok 5.N-2).
}


def _resolve_entity_config_from_db(core_id: int) -> dict | None:
    """Phase 38.4 Krok 5.N-2 LIVE v2 (22.5.2026 vecer, Marti's "patri to do
    instance gridu, ne data_source"): drop fw.data_source.target_xxx columns
    bastl plan. Backend resolver extract target via SQL parse z data_set.sql_text.

    Lookup chain:
      JOIN fw.core c → fw.comp_def cd (region_slot='main', is_active)
          → fw.data_source dsrc (cd.data_source_id)
          → fw.data_source_op op (default, operation_kind='select')
          → fw.data_set dset (op.data_set_id)
      → regex extract FROM <schema>.<table> z dset.sql_text
      → target = (schema, table, id='id', no whitelist)

    Marti's design (22.5. vecer):
      - select_columns = None (trust frontend, NULL = all editable per
        fw.comp_grid.layout_json.editable_columns NULL default)
      - Future: read fw.comp_grid for active user + use editable_columns
        OR layout_json.columns[].colId as whitelist (server safety net).
    """
    import re as _re_resolve
    from core.database_data import get_data_session as _gds_resolve
    from sqlalchemy import text as _sql_resolve

    ds = _gds_resolve()
    try:
        # Krok 5-Z (28.5.2026): JOIN db_connection pro db_type detect.
        # PG path: existing direct SELECT, MSSQL path: dispatch via MCP
        # eurosoft_strategie_get_row (Marti's (α) doctrine 28.5. ranni).
        # 1.6.2026 (Marti): edit core s VLASTNÍM edit-selectem (dedikovaný
        # data_set edit-opu ≠ grid select) → read+save z NĚJ (jednoduchý SELECT
        # WHERE ID=:ID), ne z grid composite (jehož sloupce nesedí na pole).
        edit_row = ds.execute(_sql_resolve("""
            SELECT dset.id AS dset_id, dset.sql_text, dc.db_type, dc.code AS dc_code
            FROM fw.data_source_op op
            JOIN fw.data_set dset ON dset.id = op.data_set_id
            LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
            WHERE op.core_id = :core_id AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """), {"core_id": core_id}).mappings().one_or_none()
        sel_row = ds.execute(_sql_resolve("""
            SELECT dset.id AS dset_id, dset.sql_text, dc.db_type, dc.code AS dc_code
            FROM fw.core c
            JOIN fw.comp_def cd
                ON cd.core_id = c.id
               AND cd.region_slot = 'main'
               AND cd.is_active = TRUE
            JOIN fw.data_source dsrc
                ON dsrc.id = cd.data_source_id
            JOIN fw.data_source_op op
                ON op.data_source_id = dsrc.id
               AND op.operation_kind = 'select'
            JOIN fw.data_set dset
                ON dset.id = op.data_set_id
            LEFT JOIN fw.db_connection dc
                ON dc.id = dset.db_connection_id
            WHERE c.id = :core_id
            ORDER BY op.is_default DESC NULLS LAST, op.id ASC
            LIMIT 1
        """), {"core_id": core_id}).mappings().one_or_none()
        # preferuj edit-op data_set pokud dedikovaný (≠ grid select data_set)
        if edit_row and (sel_row is None or edit_row["dset_id"] != sel_row["dset_id"]):
            row = edit_row
        else:
            row = sel_row
        if not row:
            logger.info(f"_resolve_entity_config_from_db: no core/data_set chain for core_id={core_id}")
            return None
        sql_text = row["sql_text"] or ""
        db_type = (row["db_type"] or "").lower().strip() or "pg"  # default PG
        # Regex extract: FROM <schema>.<table>
        # Krok 5-Z (28.5.): preserve case pro MSSQL (Centrála 1 PascalCase
        # — st.CRM_Kontakt_ZemeCis — vs PG lowercase). PG path lower() na end,
        # MSSQL path zachova case.
        match = _re_resolve.search(
            r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)",
            sql_text,
            _re_resolve.IGNORECASE,
        )
        if not match:
            logger.warning(
                f"_resolve_entity_config_from_db: no FROM <schema>.<table> v "
                f"data_set sql_text pro core_id={core_id} (composite SQL? CTE? subquery?)"
            )
            return None
        if db_type == "mssql":
            schema = match.group(1)  # preserve case (st, dbo)
            table = match.group(2)   # preserve case (CRM_Kontakt_ZemeCis)
            id_col = "ID"            # Centrála 1 idiom uppercase
        else:
            schema = match.group(1).lower()
            table = match.group(2).lower()
            id_col = "id"
        return {
            "schema": schema,
            "table": table,
            "id_column": id_col,
            "db_type": db_type,
            "dc_code": row["dc_code"],  # napr. 'eurosoft_db_ec' pro MCP db_name
            # Krok 5-B Fix #15 sidecar (30.5.2026): core_id pro fieldKey
            # column_name resolve v MSSQL UPDATE branch design_patch_entity.
            "core_id": core_id,
            # select_columns = None: Marti's "NULL = all editable" design.
            "select_columns": None,
            # Phase CRM Foundation Krok 5-B Fix C (28.5.2026 vecer, Marti's
            # "SELECT je TABULKA Fieldu, ne fyzicka tabulka v DB"):
            # pass-through raw data_set SQL pro MSSQL edit form read flow.
            # Backend wrappne jako:
            #   SELECT * FROM (<sql_text>) AS sub WHERE [ID] = <row_id>
            # -> vraci row s aliases z SELECT projection (FirmaText, Firma,
            # Kategorie, Zeme, PoslAkceNazev, TelKontakt, MaZajemORozvadece, ...)
            # bez data migration (Centrala 1 paradigm: edit form display = grid SELECT).
            "sql_text": sql_text,
        }
    except Exception as exc:
        logger.warning(f"_resolve_entity_config_from_db(core_id={core_id}) failed: {exc}")
        return None
    finally:
        ds.close()


def _resolve_entity_config_for_core(core_dict_or_id) -> dict | None:
    """Resolve entity config for a form_core — DB-first (Krok 5.N-2), legacy fallback.

    Phase 38.4 Krok 5.N-2 (22.5.2026 vecer, Marti's "čistý stůl za námi"):
    Lookup chain:
      1. DB-driven via fw.data_source.target_xxx columns (PRIMARY, universal)
      2. core_id v _FW_FORM_CORE_REGISTRY (legacy fallback, user_edit/core_design)
      3. core.code v _FW_FORM_ENTITY_MAP (legacy code-keyed)

    Args:
        core_dict_or_id: dict s 'id' + 'code', nebo přímo int core_id

    Returns:
        entity_config dict, nebo None pokud neresolved
    """
    # Extract core_id
    if isinstance(core_dict_or_id, int):
        core_id = core_dict_or_id
        core_code = None
    elif isinstance(core_dict_or_id, dict):
        core_id = core_dict_or_id.get("id")
        core_code = core_dict_or_id.get("code")
    else:
        return None

    # 1. DB-driven (PRIMARY, Krok 5.N-2)
    if core_id is not None:
        config = _resolve_entity_config_from_db(core_id)
        if config:
            return config

    # 2. Legacy hardcoded registry (user/core form_cores, 17.5. Krok 5.N-1)
    if core_id is not None and core_id in _FW_FORM_CORE_REGISTRY:
        return _FW_FORM_CORE_REGISTRY[core_id]

    # 3. Legacy code-keyed map (oldest fallback)
    if core_code and core_code in _FW_FORM_ENTITY_MAP:
        return _FW_FORM_ENTITY_MAP[core_code]

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
    _require_erp_member(uid)

    ds = _gds_fwform()
    try:
        # Phase fw.core slim 20.5.2026 (Marti's 1B): drop layout_type='form' filter
        # + drop origin_* LEFT JOINs. Form/list discrimination jde pres root
        # comp_def.type_id (302=form, 306=list) — handled v frontend dispatcher.
        core_row = ds.execute(_sql_text_fwform("""
            SELECT c.*
            FROM fw.core c
            WHERE c.code = :code
              AND c.is_active = true
        """), {"code": core_code}).mappings().one_or_none()

        if not core_row:
            return JSONResponse(
                {"ok": False, "error": f"fw.core code='{core_code}' (kind=form) nenalezen"},
                status_code=404,
            )

        core_dict = dict(core_row)
        # Phase fw.core slim 20.5.2026: origin_payload dropnut (origin_* sloupce pryc)
        origin_payload = {"menu_node": None, "cmi": None}

        # Phase fw.core slim 20.5.2026: template_id sloupec dropnut (Marti's 2A)
        template_dict: dict | None = None

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
        # 3. Load root form comp_def (type_id=302, core_id=core.id)
        form_row = ds.execute(_sql_text_fwform("""
            SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,
                   cd.sort_order, cd.is_active,
                   ct.code AS comp_type_code, ct.label AS comp_type_label
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            WHERE cd.core_id = :core_id
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

    Phase 38.4 Krok 5.X+1 hotfix (27.5.2026, Marti's "Pridavani polozek
    do gridu selhava — 404 po code rename"):
    Lookup chain id-or-code (analog Krok 5.N-1/-2/-2b dispatch):
      1. _FW_FORM_ENTITY_MAP by core_code (legacy, pre-rename codes
         like 'user', 'user_edit')
      2. _FW_FORM_CORE_REGISTRY by core_id (id-keyed, survives code
         rename — Marti's '22aBBB' fw.core.code rename z 27.5. ranní
         testing)
    ID-first dispatch je robustni proti uzivatelskemu rename
    fw.core.code (uniform parity s Krok 5.N pattern).

    Returns (entity_config, child_config). Raises ValueError pokud anything
    missing.
    """
    from sqlalchemy import text as _sql_text_rcc
    # Resolve core_code → fw.core row (existence check + capture id for fallback)
    core_row = ds.execute(_sql_text_rcc("""
        SELECT id FROM fw.core
        WHERE code = :code AND is_active = true
    """), {"code": core_code}).mappings().one_or_none()
    if not core_row:
        raise ValueError(f"fw.core code='{core_code}' (form) nenalezen")
    core_id = core_row["id"]
    # Lookup chain: code first (legacy), then id-keyed registry (rename-safe)
    entity_config = _FW_FORM_ENTITY_MAP.get(core_code)
    if entity_config is None and core_id in _FW_FORM_CORE_REGISTRY:
        entity_config = _FW_FORM_CORE_REGISTRY[core_id]
    if entity_config is None:
        raise ValueError(
            f"Core code='{core_code}' (id={core_id}) neni v _FW_FORM_ENTITY_MAP "
            f"ani _FW_FORM_CORE_REGISTRY. "
            f"ENTITY_MAP keys: {list(_FW_FORM_ENTITY_MAP.keys())}. "
            f"CORE_REGISTRY ids: {list(_FW_FORM_CORE_REGISTRY.keys())}"
        )
    children = entity_config.get("children") or {}
    if child_key not in children:
        raise ValueError(
            f"Child '{child_key}' neni v core '{core_code}' (id={core_id}) children. "
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
    _require_erp_member(uid)

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

        # Root comp_def: core_id = core.id, is_active=true, prvni dle
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
            WHERE cd.core_id = :cid
              AND cd.is_active = true
            ORDER BY cd.sort_order ASC, cd.id ASC
            LIMIT 1
        """), {"cid": core_id}).mappings().one_or_none()

        # Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer): columns_list dropped —
        # native ErpDataGrid toolbar resi sestavu pres /grid-layout/{core_id}
        # API. fw.comp_grid_master* schema deprecated.

        # Krok 5.S (22.5.2026 vecer, Marti's "od lesa" Centrala 1 toolbar parita):
        # grid_actions driven by fw.data_source_op rows per root_comp_def's
        # data_source_id. Aggregace:
        #   has_insert / has_edit / has_delete = bool (kind row EXISTS)
        #   edit_core_id = core_id z 'edit' row (kam otevrit form)
        # Marti's doctrine: visibility per row presence (no status column).
        grid_actions = None
        root_ds_id = root_row["data_source_id"] if root_row else None
        if root_ds_id is not None:
            ga_row = ds.execute(_sql_psp("""
                SELECT
                    bool_or(operation_kind = 'insert') AS has_insert,
                    bool_or(operation_kind = 'edit')   AS has_edit,
                    bool_or(operation_kind = 'delete') AS has_delete,
                    MAX(core_id) FILTER (WHERE operation_kind = 'edit') AS edit_core_id
                FROM fw.data_source_op
                WHERE data_source_id = :ds_id
            """), {"ds_id": root_ds_id}).mappings().one_or_none()
            grid_actions = {
                "has_insert": bool(ga_row["has_insert"]) if ga_row else False,
                "has_edit": bool(ga_row["has_edit"]) if ga_row else False,
                "has_delete": bool(ga_row["has_delete"]) if ga_row else False,
                "edit_core_id": ga_row["edit_core_id"] if ga_row else None,
            }

        root_comp_def_payload = dict(root_row) if root_row else None
        if root_comp_def_payload is not None:
            root_comp_def_payload["grid_actions"] = grid_actions

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core": dict(core_row),
            "root_comp_def": root_comp_def_payload,
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
    _require_erp_member(uid)

    ds = _gds_fwid()
    try:
        # Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
        # tolerantni id-based path pro drafted cores. Plus LEFT JOIN na
        # origin tables pro "Pochazi z" header display v DesignFwForm
        # (Marti's "B Je tez logicky krok" — provenance viditelna).
        # Phase fw.core slim 20.5.2026: origin_* JOINs dropnuty
        row = ds.execute(_sql_fwid("""
            SELECT c.*
            FROM fw.core c
            WHERE c.id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not row:
            return JSONResponse(
                {"ok": False, "error": f"fw.core id={core_id} nenalezen"},
                status_code=404,
            )
        rd = dict(row)
        resolved_code = rd.get("code")
        # Phase fw.core slim 20.5.2026: origin_payload dropnut
        origin_payload = {"menu_node": None, "cmi": None}

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
            WHERE cd.core_id = :cid
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
                "embedded_grids": [],
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
                     cd.core_id AS grid_core_id,
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
                     cd.core_id AS grid_core_id,
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

        # Krok 5.Z (31.5.2026, Marti: "melo by to byt kodove stejne!!!"):
        # grid_actions per nested grid — CODE-PARITA se standalone prehledem.
        # Standalone (page_render) cte rootCd.grid_actions (derived z data_source
        # ops: has_insert/edit/delete + edit_core_id). Nested grid potreboval
        # totez, jinak mel CRUD hardcoded false. Spocti z ops jeho data_source.
        for _f in fields_list:
            if _f.get("comp_type_code") == "grid_modern" and _f.get("data_source_id"):
                _ga = ds.execute(_sql_fwid("""
                    SELECT bool_or(operation_kind = 'insert') AS has_insert,
                           bool_or(operation_kind = 'edit')   AS has_edit,
                           bool_or(operation_kind = 'delete') AS has_delete,
                           MAX(core_id) FILTER (WHERE operation_kind = 'edit') AS edit_core_id
                    FROM fw.data_source_op
                    WHERE data_source_id = :dsid
                """), {"dsid": _f["data_source_id"]}).mappings().first()
                if _ga:
                    _f["grid_actions"] = {
                        "has_insert": bool(_ga["has_insert"]),
                        "has_edit": bool(_ga["has_edit"]),
                        "has_delete": bool(_ga["has_delete"]),
                        "edit_core_id": _ga["edit_core_id"],
                    }

        # Krok 5.Z (30.5.2026, Marti's "Klasickou komponentu gridu 306 pro
        # nase vseobecne pouziti"): embedded grid_modern komponenty (children
        # comp_def s ct.code='grid_modern' AND parent_comp_def_id IS NOT NULL).
        # Render pattern analog ErpEntityPicker — inline ErpDataGrid uvnitr
        # form tabu (autoColumns, layoutKey persistent, Excel mode CRUD).
        # Pivot z comp_type=304 (nested_grid, HTML <table>) na 306 kvuli
        # AG Grid features (filter/sort/copy/layout). Layout JSONB nese
        # data_source_code + filter_field + filter_source (:master_id) +
        # height_px + title + context_menu.
        # Krok 5.Z (30.5.2026, Marti: "na nestes gridech ma byt core_id tech
        # prehledu detailu, ne 72 formulare" -> "72 tam byt nemaji, momentalne
        # NULL, protoze core nested gridu jeste neexistuje").
        # grid_core_id = VLASTNI core nested gridu. Dnes nested gridy dedi
        # core formulare (cd.core_id == :cid == 72), sve vlastni "prehled detail"
        # jadro jeste nemaji -> emit NULL (pill core cast schovana, zadne spatne
        # 72). Az se zalozi nested detail jadra (zitra rano, kvuli insert/edit
        # v nested gridu) a priradi se nested gridum jejich core_id (!= :cid),
        # CASE je propusti a pill + Core setting je ukazou automaticky.
        # POZN: discovery deti formu je zatim pres cd.core_id = :cid; az nested
        # gridy dostanou vlastni core_id, musi se prepnout na parent_comp_def_id
        # tree traversal (zitra rano refactor).
        # Krok 5.Z (31.5.2026): discovery embedded gridů přes parent_comp_def_id
        # tree traversal (shodný s fields_list ~ř. 2793) — robustní, najde grid
        # bez ohledu na jeho core_id. NUTNÉ: nested grid má teď VLASTNÍ core_id
        # (≠ form 72), staré WHERE cd.core_id=:cid by ho minulo.
        #
        # grid_core_id = cd.core_id přímo. Trigger comp_def_inherit_core_id má
        # od 31.5. výjimku pro grid_modern (nested grid smí vlastní core), takže
        # grid nese svůj master přehled core (Akce 79 / Osoby 80). Pill ho čte
        # odtud, CRUD přes layout.edit_core_id (frontend ř. 5239).
        embedded_grids_rows = ds.execute(_sql_fwid("""
            WITH RECURSIVE form_tree AS (
                SELECT cd.id, cd.parent_comp_def_id
                FROM fw.comp_def cd
                WHERE cd.parent_comp_def_id = :form_id AND cd.is_active = true
                UNION ALL
                SELECT child.id, child.parent_comp_def_id
                FROM fw.comp_def child
                JOIN form_tree ft ON child.parent_comp_def_id = ft.id
                WHERE child.is_active = true
            )
            SELECT cd.id AS comp_def_id, cd.parent_comp_def_id, cd.name,
                   cd.caption, cd.layout, cd.sort_order, cd.data_source_id,
                   ds.code AS data_source_code, ds.name AS data_source_name,
                   cd.core_id AS grid_core_id
            FROM form_tree ft
            JOIN fw.comp_def cd ON cd.id = ft.id
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
            WHERE ct.code = 'grid_modern'
              AND cd.parent_comp_def_id IS NOT NULL
              AND cd.is_active = true
            ORDER BY cd.sort_order ASC, cd.id ASC
        """), {"form_id": form_dict["id"]}).mappings().all()
        embedded_grids = [dict(r) for r in embedded_grids_rows]

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
            cols_list = entity_config.get("select_columns")
            # Phase 38.4 Krok 5.N-2 (22.5.2026 vecer, Marti's "NULL = trust
            # frontend"): None = no whitelist, SELECT * z target table.
            # DB-driven resolver (_resolve_entity_config_from_db) returns
            # select_columns=None — server trust frontend payload.
            if cols_list:
                cols_sql = ", ".join(f'"{c}"' for c in cols_list)
            else:
                cols_sql = "*"
            # Krok 5-A v2 (27.5.2026 ~23:50) + Krok 5-Z (28.5.2026): db_type dispatch.
            # row_id=0 = CREATE mode placeholder → skip SELECT.
            # PG target → direct SELECT.
            # MSSQL target → MCP eurosoft_strategie_get_row (Marti's (α) doctrine).
            _db_type = (entity_config.get("db_type") or "pg").lower()
            _dc_code = entity_config.get("dc_code") or ""
            if row_id and row_id > 0:
                if _db_type == "mssql":
                    # Phase CRM Foundation Krok 5-B Fix C (28.5.2026 vecer,
                    # Marti's "SELECT je TABULKA Fieldu, ne fyzicka tabulka v DB"):
                    # MSSQL edit form read = wrap data_set SQL jako subquery
                    # s WHERE [ID] = <row_id>. Tj. stejny SELECT jako grid,
                    # jen jeden radek. Centrala 1 paradigm bez data migration.
                    #
                    # Dispatch: eurosoft_strategie_query_raw misto get_row.
                    # Vraci row s aliases z SELECT projection (FirmaText, Firma,
                    # Kategorie, Zeme, PoslAkceNazev, TelKontakt, MaZajemORozvadece,
                    # ID, Autor, atd.) napric joinovanych tables — bez NULL bias
                    # z naive SELECT * FROM <base>.
                    #
                    # Fallback: pokud data_set SQL prazdne (entity_config.sql_text=None),
                    # ponecha naive get_row jako legacy compat path.
                    _ds_sql_raw = entity_config.get("sql_text") if entity_config else None
                    try:
                        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
                        import json as _json_fwid
                        import re as _re_fwid
                        mcp = get_eurosoft_mcp_client()
                        if mcp is None:
                            logger.warning(
                                "[fw_form_load_by_id] MCP client None (eurosoft_mcp_enabled=False?) — data_row=None"
                            )
                        else:
                            # dc_code = 'eurosoft_db_ec' → MCP db_name = 'DB_EC'.
                            mcp_db_name = "DB_EC"
                            if _dc_code and _dc_code.lower().startswith("eurosoft_"):
                                mcp_db_name = _dc_code[len("eurosoft_"):].upper()

                            # Krok 5-B Fix C: wrap data_set SQL or fallback na naive get_row.
                            # DIAG_K5B_FIXC (28.5.2026 brutal stderr print pro guaranteed visibility)
                            import sys as _sys_diag
                            print(
                                f"[DIAG_K5B_FIXC] ENTRY MSSQL branch core={rd.get('id')} row={row_id} "
                                f"_db_type={_db_type!r} _dc_code={_dc_code!r} "
                                f"_ds_sql_raw_is_none={_ds_sql_raw is None} "
                                f"_ds_sql_raw_len={len(_ds_sql_raw) if _ds_sql_raw else 0} "
                                f"mcp_db_name={mcp_db_name!r}",
                                file=_sys_diag.stderr, flush=True,
                            )
                            if _ds_sql_raw and _ds_sql_raw.strip():
                                # Strip TOP-LEVEL ORDER BY (MSSQL subquery constraint
                                # without TOP). HOTFIX 28.5.2026 vecer: Marti's grid SQL
                                # ma multiple ORDER BY (uvnitr outer apply subqueries
                                # + top-level). Naive regex \bORDER\s+BY\b.*$ s DOTALL
                                # smaze prvni (v subquery) -> broken SQL -> 0 rows.
                                # Pojd paren-depth-aware: najdi posledni ORDER BY
                                # kde paren depth=0, strip od nej.
                                _sql_clean = _ds_sql_raw.rstrip().rstrip(";").rstrip()
                                _last_top_order_by = -1
                                _depth = 0
                                _in_string = False
                                _string_char = ""
                                _i = 0
                                _n = len(_sql_clean)
                                while _i < _n:
                                    _ch = _sql_clean[_i]
                                    if _in_string:
                                        if _ch == _string_char:
                                            # Doubled char = escaped quote (SQL idiom)
                                            if _i + 1 < _n and _sql_clean[_i + 1] == _string_char:
                                                _i += 2
                                                continue
                                            _in_string = False
                                        _i += 1
                                        continue
                                    if _ch in ("'", '"'):
                                        _in_string = True
                                        _string_char = _ch
                                        _i += 1
                                        continue
                                    if _ch == "(":
                                        _depth += 1
                                        _i += 1
                                        continue
                                    if _ch == ")":
                                        _depth -= 1
                                        _i += 1
                                        continue
                                    # Detect "ORDER BY" at top level (depth=0)
                                    if _depth == 0 and _i + 8 <= _n:
                                        _chunk = _sql_clean[_i:_i + 8].upper()
                                        if _chunk == "ORDER BY":
                                            # Word boundary check (prev char non-alnum or start)
                                            _prev = _sql_clean[_i - 1] if _i > 0 else " "
                                            if not (_prev.isalnum() or _prev == "_"):
                                                _last_top_order_by = _i
                                    _i += 1
                                if _last_top_order_by >= 0:
                                    _sql_clean = _sql_clean[:_last_top_order_by].rstrip()
                                # Krok 5-B Fix C+1 (28.5.2026 vecer pozde):
                                # Detect :ID bind placeholder (Marti's detail SQL
                                # idiom). pyodbc neumi :named, jen ? positional —
                                # substituujeme :ID za int(row_id) pred dispatch.
                                # Plus pokud SQL ma vlastni WHERE K.ID = :ID
                                # (single-row filtered), skip outer wrap.
                                _row_id_int = int(row_id)
                                _has_id_placeholder = ":ID" in _sql_clean
                                if _has_id_placeholder:
                                    # Substitute :ID -> int row_id, skip outer wrap.
                                    # Word boundary defensive: jen ":ID" jako standalone
                                    # token (nebo na konci stringu). MSSQL ID column
                                    # nazev nepouziva ":" prefix, takze :ID je vzdy
                                    # bind placeholder.
                                    _wrapped_sql = _sql_clean.replace(":ID", str(_row_id_int))
                                    logger.info(
                                        "[fw_form_load_by_id] :ID placeholder substitute (single-row filtered, no outer wrap) pro core=%s row=%s",
                                        rd.get("id"), row_id,
                                    )
                                else:
                                    # Outer wrap pattern (existing Fix C behavior pro
                                    # grid SELECT bez vlastniho filteru).
                                    _wrapped_sql = (
                                        f"SELECT * FROM (\n{_sql_clean}\n) AS _edit_form_sub "
                                        f"WHERE [ID] = {_row_id_int}"
                                    )
                                logger.info(
                                    "[fw_form_load_by_id] MSSQL edit-form data_set SQL wrap pro core=%s row=%s (sql_text_len=%d)",
                                    rd.get("id"), row_id, len(_ds_sql_raw),
                                )
                                # DIAG_K5B_FIXC: print wrapped SQL preview + has_id_placeholder outcome
                                print(
                                    f"[DIAG_K5B_FIXC] WRAPPED SQL core={rd.get('id')} row={row_id} "
                                    f"has_id_placeholder={_has_id_placeholder} "
                                    f"wrapped_sql_len={len(_wrapped_sql)} "
                                    f"preview={_wrapped_sql[:200]!r}",
                                    file=_sys_diag.stderr, flush=True,
                                )
                                result_json = mcp.call_tool_sync(
                                    "eurosoft_strategie_query_raw",
                                    {
                                        "sql": _wrapped_sql,
                                        "db_name": mcp_db_name,
                                    },
                                    conversation_id=None,
                                )
                                result = _json_fwid.loads(result_json) if isinstance(result_json, str) else result_json
                                # DIAG_K5B_FIXC: print MCP query_raw result shape
                                print(
                                    f"[DIAG_K5B_FIXC] MCP RESULT core={rd.get('id')} row={row_id} "
                                    f"result_type={type(result).__name__} "
                                    f"result_ok={result.get('ok') if isinstance(result, dict) else 'N/A'} "
                                    f"result_keys={list(result.keys()) if isinstance(result, dict) else 'N/A'} "
                                    f"result_preview={str(result)[:300]!r}",
                                    file=_sys_diag.stderr, flush=True,
                                )
                                if isinstance(result, dict) and result.get("ok"):
                                    _rows = result.get("rows") or []
                                    if _rows:
                                        data_row = _rows[0]
                                        logger.info(
                                            "[fw_form_load_by_id] MSSQL edit-form row loaded via data_set SQL wrap: core=%s id=%s (%d cols)",
                                            rd.get("id"), row_id, len(data_row),
                                        )
                                    else:
                                        logger.warning(
                                            "[fw_form_load_by_id] MSSQL data_set SQL wrap vratil 0 rows pro core=%s id=%s",
                                            rd.get("id"), row_id,
                                        )
                                else:
                                    logger.warning(
                                        "[fw_form_load_by_id] MSSQL data_set SQL wrap failed pro core=%s id=%s: %r",
                                        rd.get("id"), row_id, result,
                                    )
                            else:
                                # LEGACY FALLBACK: data_set sql_text neexistuje -> naive get_row.
                                result_json = mcp.call_tool_sync(
                                    "eurosoft_strategie_get_row",
                                    {
                                        "schema": schema_name,
                                        "table": table_name,
                                        "id": int(row_id),
                                        "db_name": mcp_db_name,
                                    },
                                    conversation_id=None,
                                )
                                result = _json_fwid.loads(result_json) if isinstance(result_json, str) else result_json
                                if isinstance(result, dict) and result.get("ok") and result.get("row"):
                                    data_row = result["row"]
                                    logger.info(
                                        "[fw_form_load_by_id] MSSQL legacy get_row pro %s.%s id=%s (%d cols, naive SELECT *)",
                                        schema_name, table_name, row_id, len(data_row),
                                    )
                                else:
                                    logger.warning(
                                        "[fw_form_load_by_id] MCP get_row vratil prazdno/error pro %s.%s id=%s: %r",
                                        schema_name, table_name, row_id, result,
                                    )
                    except Exception as exc:
                        logger.warning(
                            "[fw_form_load_by_id] MSSQL MCP dispatch failed for core=%s row=%s: %s",
                            rd.get("id"), row_id, exc,
                        )
                        # DIAG_K5B_FIXC: print full traceback
                        import traceback as _tb_diag
                        print(
                            f"[DIAG_K5B_FIXC] EXCEPTION core={rd.get('id')} row={row_id} "
                            f"exc_type={type(exc).__name__} exc={exc!r}\n"
                            f"{_tb_diag.format_exc()}",
                            file=_sys_diag.stderr, flush=True,
                        )
                        data_row = None
                else:
                    # PG path — existing direct SELECT, savepoint pojistka.
                    try:
                        with ds.begin_nested():
                            data_query = (
                                f'SELECT {cols_sql} FROM "{schema_name}"."{table_name}" '
                                f'WHERE "{id_column}" = :row_id'
                            )
                            data_row_raw = ds.execute(
                                _sql_fwid(data_query), {"row_id": row_id}
                            ).mappings().one_or_none()
                            if data_row_raw:
                                data_row = dict(data_row_raw)
                    except Exception as exc:
                        logger.warning(
                            "[fw_form_load_by_id] PG SELECT failed for %s.%s row=%s: %s",
                            schema_name, table_name, row_id, exc,
                        )
                        data_row = None
            # else: row_id=0 (CREATE) — data_row zůstává None (init line 2783)

            # Krok 5.X (27.5.2026, Marti's "Jsou to normalni komponenty"):
            # Nested grids = fw.comp_def rows (type_id=304 'nested_grid'),
            # parent_comp_def_id na main panel. layout.child_key references
            # entity_config.children[key] for SELECT config. Doctrine:
            # "uniformita vítězí" (Krok 13, 11.5.) + "fw self edited" (22.5.).
            #
            # Backward compat fallback: pokud nested_grid comp_defs neexistuji
            # (jiny form bez DDL migration) ALE entity_config.children
            # non-empty → legacy iteration (warning log).
            child_config_map = entity_config.get("children") or {}
            _nested_grid_seen = False
            for fld in fields_list:
                if fld.get("comp_type_code") != "nested_grid":
                    continue
                _nested_grid_seen = True
                lay = fld.get("layout") or {}
                child_key = lay.get("child_key") if isinstance(lay, dict) else None
                if not child_key:
                    logger.warning(
                        "[fw_form_load_by_id] nested_grid comp_def #%s missing layout.child_key, skipping",
                        fld.get("id"),
                    )
                    continue
                child_cfg = child_config_map.get(child_key)
                if not child_cfg:
                    logger.warning(
                        "[fw_form_load_by_id] nested_grid comp_def #%s references unknown child_key=%r (entity_config keys: %s)",
                        fld.get("id"), child_key, list(child_config_map.keys()),
                    )
                    continue
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
                # Krok 5.X: caption z comp_def (Marti's user-editable label)
                # má prioritu nad entity_config.label. comp_def_id +
                # parent_comp_def_id + sort_order pro frontend orchestrace
                # (palette ✕ delete, ⚙ settings, ←→↑↓ reorder).
                # Krok 5.X+1 Fix E (27.5.2026, Marti's Volba B "pinned-CSS"):
                # layout JSONB pass-through pro frontend pinned rendering
                # (layout.pinned=true → left-align CSS class).
                children_dict[child_key] = {
                    "rows": [dict(r) for r in child_rows],
                    "label": fld.get("caption") or child_cfg.get("label") or child_key,
                    "default_label": child_cfg.get("default_label"),
                    "id_column": child_cfg.get("id_column", "id"),
                    "comp_def_id": fld.get("id"),
                    "parent_comp_def_id": fld.get("parent_comp_def_id"),
                    "sort_order": fld.get("sort_order"),
                    "layout": lay,
                }

            # Legacy fallback: forms bez Krok 5.X DDL migration ještě
            # nemají nested_grid comp_defs → použij entity_config iteration.
            if not _nested_grid_seen and child_config_map:
                logger.warning(
                    "[fw_form_load_by_id] core %s: entity_config has children %s but no nested_grid comp_defs in fields_list — using legacy memory-only fallback (run Krok 5.X DDL pro full parita)",
                    core_id, list(child_config_map.keys()),
                )
                for child_key, child_cfg in child_config_map.items():
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
                        # No comp_def_id → frontend ví že je legacy memory-only
                    }

        # Phase fw.core slim 20.5.2026: template_id sloupec dropnut (Marti's 2A)
        template_dict = None

        # FW Component State Rules (31.5.2026): effective stavové overrides per
        # komponenta podle hodnot řídicích polí (discriminators) — viz
        # docs/fw_component_state_rules.md. Fail-soft: chyba → form bez stavů.
        _discriminators_out = []   # zpřístupněno frontendu pro živý přepočet
        try:
            _discr_rows = ds.execute(_sql_fwid(
                "SELECT field_name, source FROM fw.form_discriminator "
                "WHERE form_core_id = :cid AND is_active = TRUE"
            ), {"cid": core_id}).mappings().all()
            _discr_values = {}
            if _discr_rows:
                _discriminators_out = [
                    {"field_name": _dr["field_name"], "source": _dr["source"]}
                    for _dr in _discr_rows
                ]
                _is_new = not (row_id and row_id > 0)
                for _dr in _discr_rows:
                    _fn = _dr["field_name"]
                    if _dr["source"] == "context":
                        if _fn in ("_mode", "mode"):
                            _discr_values[_fn] = "new" if _is_new else "edit"
                        # další context fields (role, device…) — doplnit dle potřeby
                    else:  # 'column' — hodnota z editovaného řádku
                        if isinstance(data_row, dict) and data_row.get(_fn) is not None:
                            _discr_values[_fn] = str(data_row[_fn])
            # Resolve VŽDY (i bez discriminatorů / hodnot) — statická (default)
            # vrstva (form_discriminator_id IS NULL) se aplikuje pořád; aktivní
            # pravidla z _discr_values ji přebijí. (Krok 2 static default.)
            from modules.erp.application.comp_resolver import resolve_state_overrides
            _state_ovr = resolve_state_overrides(ds, core_id, _discr_values)
            if _state_ovr:
                for _f in fields_list:
                    _ov = _state_ovr.get(_f.get("id"))
                    if _ov:
                        _f["state_overrides"] = _ov
        except Exception as _e_sr:
            logger.warning("[fw_form_load_by_id] state overrides core=%s failed: %r", core_id, _e_sr)

        return JSONResponse(jsonable_encoder({
            "ok": True,
            "core": rd,
            "form": form_dict,
            "fields": fields_list,
            "data": data_row,
            "template": template_dict,
            "children": children_dict,
            "embedded_grids": embedded_grids,
            "empty_container": False,
            "origin": origin_payload,
            "discriminators": _discriminators_out,
        }))
    finally:
        ds.close()


@api_router.post("/fw-form/{core_id}/state-resolve")
async def fw_form_state_resolve(core_id: int, req: Request) -> JSONResponse:
    """FW State Rules — živý přepočet (31.5.2026).

    Body: {"discr_values": {field_name: value, ...}} — aktuální hodnoty řídicích
    polí (frontend je čte z živých inputů + kontextu mode). Vrací
    {"overrides": {comp_def_id: {prop_name: prop_value}}} — effective stavové
    overrides. Volá se při změně řídicího pole (insert flow / dynamický form).
    Fail-soft: chyba → prázdné overrides.
    """
    from core.database_data import get_data_session as _gds_sr
    ds = _gds_sr()
    try:
        try:
            body = await req.json()
        except Exception:
            body = {}
        discr_values = (body or {}).get("discr_values") or {}
        if not isinstance(discr_values, dict):
            discr_values = {}
        from modules.erp.application.comp_resolver import resolve_state_overrides
        overrides = resolve_state_overrides(ds, core_id, {str(k): str(v) for k, v in discr_values.items()})
        return JSONResponse({"ok": True, "core_id": core_id, "overrides": overrides})
    except Exception as exc:
        logger.warning("[fw_form_state_resolve] core=%s failed: %r", core_id, exc)
        return JSONResponse({"ok": False, "error": str(exc), "overrides": {}}, status_code=200)
    finally:
        ds.close()


# ════════════════════════════════════════════════════════════════════════════
# FW Component State Rules — authoring CRUD (31.5.2026, #2 design-mode UI)
# docs/fw_component_state_rules.md §8. Unikátní prefix /fw-state-* (žádná kolize
# s /fw-form/{core_code}/{parent_id}/...). Soft-delete (is_active=FALSE) — GRANT
# strategie nemá DELETE (doctrine #11). Audit = přihlášený user (Marti), ne
# hardcoded Marti-AI.
# ════════════════════════════════════════════════════════════════════════════

_STATE_PROP_PALETTE = frozenset({
    "visible", "sort_order", "parent", "required", "readonly",
    "color", "label_color", "background", "cell_background", "bold", "italic", "underline", "strikethrough", "default_value", "label_text", "hint", "inside_hint",
})


def _sr_audit(uid: int) -> tuple[int | None, str]:
    """Caller display pro audit (core session lookup). (id, text)."""
    if not uid:
        return None, "Unknown"
    from core.database_core import get_core_session as _gcs_sra
    from modules.core.infrastructure.models_core import User as _U_sra
    cs = _gcs_sra()
    try:
        u = cs.query(_U_sra).filter_by(id=uid).first()
        if not u:
            return uid, "Unknown"
        if u.short_name and u.short_name.strip():
            return uid, u.short_name.strip()
        nm = " ".join(filter(None, [u.first_name, u.last_name])).strip()
        return uid, nm or "Unknown"
    finally:
        cs.close()


@api_router.get("/fw-state-discriminators/{core_id:int}")
def fw_state_discriminators_list(core_id: int, req: Request) -> JSONResponse:
    """List řídicích polí (raw: id/source/priority/label/is_active) pro authoring."""
    from core.database_data import get_data_session as _gds_sdl
    from sqlalchemy import text as _t_sdl
    ds = _gds_sdl()
    try:
        rows = ds.execute(_t_sdl(
            "SELECT id, field_name, source, priority, label, is_active "
            "FROM fw.form_discriminator WHERE form_core_id = :cid "
            "ORDER BY priority ASC, id ASC"
        ), {"cid": core_id}).mappings().all()
        return JSONResponse({"ok": True, "core_id": core_id,
                             "discriminators": [dict(r) for r in rows]})
    finally:
        ds.close()


@api_router.post("/fw-state-discriminators/{core_id:int}")
async def fw_state_discriminator_create(core_id: int, req: Request) -> JSONResponse:
    """Upsert řídicí pole (ON CONFLICT form_core_id+field_name → update)."""
    uid = _get_uid(req)
    _require_parent(uid)
    body = await req.json()
    field_name = (body.get("field_name") or "").strip()
    source = (body.get("source") or "column").strip()
    if not field_name:
        return JSONResponse({"ok": False, "error": "field_name required"}, status_code=400)
    if source not in ("column", "context"):
        return JSONResponse({"ok": False, "error": "source musí být column|context"}, status_code=400)
    try:
        priority = int(body.get("priority") if body.get("priority") is not None else 200)
    except (TypeError, ValueError):
        priority = 200
    label = body.get("label")
    audit_uid, audit_text = _sr_audit(uid)
    from core.database_data import get_data_session as _gds_sdc
    from sqlalchemy import text as _t_sdc
    ds = _gds_sdc()
    try:
        row = ds.execute(_t_sdc(
            "INSERT INTO fw.form_discriminator "
            "(form_core_id, field_name, source, priority, label, is_active, "
            " created_by_id, created_by_text, updated_by_id, updated_by_text) "
            "VALUES (:cid, :fn, :src, :prio, :lbl, TRUE, :uid, :txt, :uid, :txt) "
            "ON CONFLICT (form_core_id, field_name) DO UPDATE SET "
            "  source = EXCLUDED.source, priority = EXCLUDED.priority, "
            "  label = EXCLUDED.label, is_active = TRUE, "
            "  updated_by_id = :uid, updated_by_text = :txt "
            "RETURNING id, field_name, source, priority, label, is_active"
        ), {"cid": core_id, "fn": field_name, "src": source, "prio": priority,
            "lbl": label, "uid": audit_uid, "txt": audit_text}).mappings().first()
        ds.commit()
        return JSONResponse({"ok": True, "discriminator": dict(row)})
    except Exception as exc:
        ds.rollback()
        logger.warning("[fw_state_discriminator_create] core=%s failed: %r", core_id, exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.patch("/fw-state-discriminator/{discr_id:int}")
async def fw_state_discriminator_patch(discr_id: int, req: Request) -> JSONResponse:
    """Update priority/label/source/is_active řídicího pole."""
    uid = _get_uid(req)
    _require_parent(uid)
    body = await req.json()
    sets = []
    params = {"id": discr_id}
    if body.get("priority") is not None:
        try:
            params["prio"] = int(body["priority"]); sets.append("priority = :prio")
        except (TypeError, ValueError):
            pass
    if "label" in body:
        sets.append("label = :lbl"); params["lbl"] = body["label"]
    if body.get("source") in ("column", "context"):
        sets.append("source = :src"); params["src"] = body["source"]
    if "is_active" in body:
        sets.append("is_active = :act"); params["act"] = bool(body["is_active"])
    if not sets:
        return JSONResponse({"ok": False, "error": "no fields to update"}, status_code=400)
    audit_uid, audit_text = _sr_audit(uid)
    sets.append("updated_by_id = :uid"); params["uid"] = audit_uid
    sets.append("updated_by_text = :txt"); params["txt"] = audit_text
    from core.database_data import get_data_session as _gds_sdp
    from sqlalchemy import text as _t_sdp
    ds = _gds_sdp()
    try:
        row = ds.execute(_t_sdp(
            "UPDATE fw.form_discriminator SET " + ", ".join(sets) +
            " WHERE id = :id "
            "RETURNING id, field_name, source, priority, label, is_active"
        ), params).mappings().first()
        ds.commit()
        if not row:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        return JSONResponse({"ok": True, "discriminator": dict(row)})
    except Exception as exc:
        ds.rollback()
        logger.warning("[fw_state_discriminator_patch] id=%s failed: %r", discr_id, exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.delete("/fw-state-discriminator/{discr_id:int}")
async def fw_state_discriminator_delete(discr_id: int, req: Request) -> JSONResponse:
    """Soft-delete řídicí pole + jeho overrides (is_active=FALSE; GRANT bez DELETE)."""
    uid = _get_uid(req)
    _require_parent(uid)
    audit_uid, audit_text = _sr_audit(uid)
    from core.database_data import get_data_session as _gds_sdd
    from sqlalchemy import text as _t_sdd
    ds = _gds_sdd()
    try:
        ds.execute(_t_sdd(
            "UPDATE fw.comp_state_override SET is_active = FALSE, "
            "updated_by_id = :uid, updated_by_text = :txt "
            "WHERE form_discriminator_id = :id AND is_active = TRUE"
        ), {"id": discr_id, "uid": audit_uid, "txt": audit_text})
        row = ds.execute(_t_sdd(
            "UPDATE fw.form_discriminator SET is_active = FALSE, "
            "updated_by_id = :uid, updated_by_text = :txt "
            "WHERE id = :id RETURNING id"
        ), {"id": discr_id, "uid": audit_uid, "txt": audit_text}).first()
        ds.commit()
        if not row:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        return JSONResponse({"ok": True, "id": discr_id})
    except Exception as exc:
        ds.rollback()
        logger.warning("[fw_state_discriminator_delete] id=%s failed: %r", discr_id, exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.get("/fw-state-overrides/{core_id:int}")
def fw_state_overrides_list(core_id: int, req: Request) -> JSONResponse:
    """List raw override řádků pro jádro (JOIN discriminator).

    Volitelné filtry: ?comp_def_id= ?discriminator_id= ?value=
    """
    from core.database_data import get_data_session as _gds_sol
    from sqlalchemy import text as _t_sol
    qp = dict(req.query_params)
    ds = _gds_sol()
    try:
        if qp.get("static"):
            # Statické (default) overrides — bez řídicího pole
            # (form_discriminator_id IS NULL). Scope dle comp_def_id (frontend
            # ho vždy posílá pro per-pole sekci). Žádný JOIN na discriminator.
            where = ["o.form_discriminator_id IS NULL", "o.is_active = TRUE"]
            params = {}
            if qp.get("comp_def_id"):
                try:
                    params["comp"] = int(qp["comp_def_id"]); where.append("o.comp_def_id = :comp")
                except ValueError:
                    pass
            rows = ds.execute(_t_sol(
                "SELECT o.id, o.comp_def_id, o.form_discriminator_id, "
                "       o.discriminator_value, o.prop_name, o.prop_value, "
                "       NULL AS discriminator_field "
                "FROM fw.comp_state_override o "
                "WHERE " + " AND ".join(where) +
                " ORDER BY o.comp_def_id, o.prop_name"
            ), params).mappings().all()
            return JSONResponse({"ok": True, "overrides": [dict(r) for r in rows]})

        # Podmíněné (discriminator-bound) overrides
        where = ["d.form_core_id = :cid", "o.is_active = TRUE", "d.is_active = TRUE"]
        params = {"cid": core_id}
        if qp.get("comp_def_id"):
            try:
                params["comp"] = int(qp["comp_def_id"]); where.append("o.comp_def_id = :comp")
            except ValueError:
                pass
        if qp.get("discriminator_id"):
            try:
                params["did"] = int(qp["discriminator_id"]); where.append("o.form_discriminator_id = :did")
            except ValueError:
                pass
        if qp.get("value") not in (None, ""):
            where.append("o.discriminator_value = :val"); params["val"] = str(qp["value"])
        rows = ds.execute(_t_sol(
            "SELECT o.id, o.comp_def_id, o.form_discriminator_id, "
            "       o.discriminator_value, o.prop_name, o.prop_value, "
            "       d.field_name AS discriminator_field "
            "FROM fw.comp_state_override o "
            "JOIN fw.form_discriminator d ON d.id = o.form_discriminator_id "
            "WHERE " + " AND ".join(where) +
            " ORDER BY o.comp_def_id, o.form_discriminator_id, "
            "          o.discriminator_value, o.prop_name"
        ), params).mappings().all()
        return JSONResponse({"ok": True, "overrides": [dict(r) for r in rows]})
    finally:
        ds.close()


@api_router.post("/fw-state-override")
async def fw_state_override_upsert(req: Request) -> JSONResponse:
    """Upsert jeden override (comp_def + discriminator + value + prop_name).

    ON CONFLICT na uq_comp_state_override → update prop_value + reaktivace.
    Prázdná hodnota prop_value (None/"") s daným prop → uloží NULL (= 'bez
    efektu' jako reset jen té vlastnosti). Pro úplné zrušení použij DELETE.
    """
    uid = _get_uid(req)
    _require_parent(uid)
    body = await req.json()
    try:
        comp_def_id = int(body.get("comp_def_id"))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "comp_def_id required"}, status_code=400)
    # form_discriminator_id null/0/chybí → STATICKÉ (default) pravidlo (Krok 2):
    # override bez řídicího pole, discriminator_value = NULL, aplikuje se vždy.
    _raw_did = body.get("form_discriminator_id")
    if _raw_did in (None, "", 0, "0"):
        discr_id = None
        value = None
    else:
        try:
            discr_id = int(_raw_did)
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "error": "form_discriminator_id musí být int nebo null (static)"}, status_code=400)
        value = body.get("discriminator_value")
        if value is None:
            return JSONResponse({"ok": False, "error": "discriminator_value required (pro podmíněné pravidlo)"}, status_code=400)
        value = str(value)
    prop_name = (body.get("prop_name") or "").strip()
    if prop_name not in _STATE_PROP_PALETTE:
        return JSONResponse({"ok": False, "error": "prop_name musí být z palety: " + ", ".join(sorted(_STATE_PROP_PALETTE))}, status_code=400)
    prop_value = body.get("prop_value")
    if prop_value is not None:
        prop_value = str(prop_value)
    audit_uid, audit_text = _sr_audit(uid)
    from core.database_data import get_data_session as _gds_sou
    from sqlalchemy import text as _t_sou
    ds = _gds_sou()
    try:
        row = ds.execute(_t_sou(
            "INSERT INTO fw.comp_state_override "
            "(comp_def_id, form_discriminator_id, discriminator_value, prop_name, "
            " prop_value, is_active, created_by_id, created_by_text, "
            " updated_by_id, updated_by_text) "
            "VALUES (:comp, :did, :val, :pn, :pv, TRUE, :uid, :txt, :uid, :txt) "
            "ON CONFLICT ON CONSTRAINT uq_comp_state_override "
            "DO UPDATE SET prop_value = EXCLUDED.prop_value, is_active = TRUE, "
            "  updated_by_id = :uid, updated_by_text = :txt "
            "RETURNING id, comp_def_id, form_discriminator_id, "
            "          discriminator_value, prop_name, prop_value"
        ), {"comp": comp_def_id, "did": discr_id, "val": value, "pn": prop_name,
            "pv": prop_value, "uid": audit_uid, "txt": audit_text}).mappings().first()
        ds.commit()
        return JSONResponse({"ok": True, "override": dict(row)})
    except Exception as exc:
        ds.rollback()
        logger.warning("[fw_state_override_upsert] failed: %r", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.delete("/fw-state-override/{ovr_id:int}")
async def fw_state_override_delete(ovr_id: int, req: Request) -> JSONResponse:
    """Soft-delete jeden override (is_active=FALSE)."""
    uid = _get_uid(req)
    _require_parent(uid)
    audit_uid, audit_text = _sr_audit(uid)
    from core.database_data import get_data_session as _gds_sod
    from sqlalchemy import text as _t_sod
    ds = _gds_sod()
    try:
        row = ds.execute(_t_sod(
            "UPDATE fw.comp_state_override SET is_active = FALSE, "
            "updated_by_id = :uid, updated_by_text = :txt "
            "WHERE id = :id RETURNING id"
        ), {"id": ovr_id, "uid": audit_uid, "txt": audit_text}).first()
        ds.commit()
        if not row:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        return JSONResponse({"ok": True, "id": ovr_id})
    except Exception as exc:
        ds.rollback()
        logger.warning("[fw_state_override_delete] id=%s failed: %r", ovr_id, exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
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
    _require_erp_member(uid)

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
    _require_erp_member(uid)

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
    _require_erp_member(uid)

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

        # Phase 38.4 Krok 5.X+1 Fix H (27.5.2026, Marti's UniqueViolation
        # "ux_user_primary_contact (user_id, contact_type)"):
        # Partial unique constraint na is_primary=TRUE → naive UPDATE
        # selhava pri primary swap (target dostane TRUE, ale existing
        # primary stale TRUE → 2 rows s is_primary=TRUE pro stejny
        # (user_id, contact_type) → violation).
        # Fix: atomic pre-clear existing primary v same transaction.
        # Filter: same parent + same auto_set polymorphic scope (napr.
        # contact_type='phone' pro phones, 'email' pro emails) +
        # is_primary=TRUE + id != target. Update audit fields tak ze
        # change je viditelny.
        if updates.get("is_primary") is True:
            clear_where = [
                f'"{child_fk}" = :_parent_id',
                '"is_primary" = TRUE',
                f'"{id_col}" != :_child_id_skip',
            ]
            clear_params = {
                "_parent_id": parent_id,
                "_child_id_skip": child_id,
                "_audit_uid": audit_uid,
                "_audit_text": audit_text,
            }
            # Polymorphic scope guard — same contact_type/etc per auto_set
            for _ac, _av in auto_set.items():
                _key = f"_auto_{_ac}"
                clear_where.append(f'"{_ac}" = :{_key}')
                clear_params[_key] = _av
            ds.execute(_sql_text_fcu(
                f'UPDATE "public"."{child_table}" '
                f'SET "is_primary" = FALSE, '
                f'    "updated_by_id" = :_audit_uid, '
                f'    "updated_by_text" = :_audit_text, '
                f'    "updated_at" = NOW() '
                f'WHERE {" AND ".join(clear_where)}'
            ), clear_params)

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
    _require_erp_member(uid)

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


@api_router.post("/design/core/{core_id}/resolve-save-bindings")
async def design_resolve_save_bindings(core_id: int, req: Request) -> JSONResponse:
    """
    Krok 5.Z (31.5.2026): sqlglot lineage → predvyplni layout.save na fieldech.

    Vezme root data_source SELECT daneho core, pres sqlglot column-lineage
    odvodi pro kazdy field jeho absolutni save souradnici (connection_id +
    schema + table + column + row_key) a zapise ji do fw.comp_def.layout.save.
    Vyrazy / outer-apply / nejasny klic -> readonly:true.

    Query: ?dry_run=true (default true) — jen preview, NEzapisuje.
           ?dry_run=false — zapise layout.save (merge) do comp_def.

    Matchuje field -> output column pres (layout.column_name OR name),
    case-insensitive. Field bez matche se nedotkne (zustane base fallback).
    Reusable — Marti muze re-runnout po zmene SELECTu (fw self edited).
    """
    from core.database_data import get_data_session as _gds_rsb
    from sqlalchemy import text as _sql_rsb
    import json as _json_rsb

    uid = _get_uid(req)
    _require_parent(uid)

    dry_run = (req.query_params.get("dry_run", "true").lower() != "false")

    try:
        from modules.erp.application.sql_lineage import resolve_save_bindings
    except Exception as _imp_e:
        return JSONResponse(
            {"ok": False, "error": f"sql_lineage import failed: {_imp_e}"},
            status_code=500,
        )

    ds = _gds_rsb()
    try:
        # 1.6.2026 (Marti): edit core s VLASTNÍM edit-selectem (SELECT * FROM
        # tabulka WHERE ID=:ID) → bindingy z introspekce base tabulky (každý
        # sloupec → table, row_key {ID:@id}). NE z grid composite. Zvládne
        # SELECT * i :ID. Fallback (grid composite multi-table) → sqlglot lineage.
        bindings = None
        conn_id = None
        dsid = None
        _edit_tbl = _introspect_edit_base_table(ds, core_id)
        if _edit_tbl and _edit_tbl.get("columns"):
            _sch = _edit_tbl.get("schema")
            _tbl = _edit_tbl["table"]
            bindings = {}
            for _col in _edit_tbl["columns"]:
                bindings[_col] = {
                    "schema": _sch, "table": _tbl, "column": _col,
                    "row_key": {"ID": "@id"}, "readonly": False, "reason": None,
                }
            _cr = ds.execute(_sql_rsb(
                "SELECT dset.db_connection_id FROM fw.data_source_op op "
                "JOIN fw.data_set dset ON dset.id = op.data_set_id "
                "WHERE op.core_id = :cid AND op.operation_kind IN ('edit','insert') "
                "ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id LIMIT 1"
            ), {"cid": core_id}).mappings().first()
            conn_id = _cr["db_connection_id"] if _cr else None

        if bindings is None:
            # fallback — grid composite (multi-table) → sqlglot lineage
            # 1) root data_source core -> select op data_set SQL + db_connection_id
            root = ds.execute(_sql_rsb(
                "SELECT data_source_id FROM fw.comp_def "
                "WHERE core_id = :cid AND parent_comp_def_id IS NULL "
                "AND data_source_id IS NOT NULL ORDER BY id LIMIT 1"
            ), {"cid": core_id}).mappings().first()
            if not root:
                return JSONResponse(
                    {"ok": False, "error": f"core {core_id} nema root comp_def s data_source"},
                    status_code=404,
                )
            dsid = root["data_source_id"]
            op = ds.execute(_sql_rsb(
                "SELECT dset.sql_text, dset.db_connection_id "
                "FROM fw.data_source_op o JOIN fw.data_set dset ON dset.id = o.data_set_id "
                "WHERE o.data_source_id = :dsid AND o.operation_kind = 'select' "
                "ORDER BY o.is_default DESC NULLS LAST, o.id LIMIT 1"
            ), {"dsid": dsid}).mappings().first()
            if not op or not op["sql_text"]:
                return JSONResponse(
                    {"ok": False, "error": f"data_source {dsid} nema select op s SQL"},
                    status_code=404,
                )
            conn_id = op["db_connection_id"]
            bindings = resolve_save_bindings(op["sql_text"])
            if not bindings:
                return JSONResponse(
                    {"ok": False, "error": "sqlglot nevratil zadne bindings (parse fail?)"},
                    status_code=422,
                )
        # case-insensitive lookup
        bind_ci = {k.lower(): (k, v) for k, v in bindings.items()}

        # 3) active leaf fieldy core
        fields = ds.execute(_sql_rsb(
            "SELECT id, name, layout FROM fw.comp_def "
            "WHERE core_id = :cid AND parent_comp_def_id IS NOT NULL "
            "AND is_active = true"
        ), {"cid": core_id}).mappings().all()

        preview = []
        applied = 0
        for f in fields:
            lay = f["layout"] or {}
            if not isinstance(lay, dict):
                continue
            out_key = (lay.get("column_name") or f["name"] or "")
            match = bind_ci.get(out_key.lower())
            if not match:
                continue
            _src_out, b = match
            save_binding = {
                "connection_id": conn_id,
                "schema": b["schema"],
                "table": b["table"],
                "column": b["column"],
                "row_key": b["row_key"],
                "readonly": bool(b["readonly"]),
            }
            if b.get("reason"):
                save_binding["reason"] = b["reason"]
            preview.append({
                "comp_def_id": f["id"], "name": f["name"],
                "output_column": out_key, "save": save_binding,
            })
            if not dry_run:
                ds.execute(_sql_rsb(
                    "UPDATE fw.comp_def "
                    "SET layout = COALESCE(layout, '{}'::jsonb) "
                    "    || jsonb_build_object('save', CAST(:b AS jsonb)) "
                    "WHERE id = :id"
                ), {"b": _json_rsb.dumps(save_binding), "id": f["id"]})
                applied += 1
        if not dry_run:
            ds.commit()

        return JSONResponse(jsonable_encoder({
            "ok": True, "core_id": core_id, "data_source_id": dsid,
            "connection_id": conn_id, "dry_run": dry_run,
            "matched": len(preview), "applied": applied,
            "bindings": preview,
            "unmatched_outputs": sorted(
                set(bindings.keys())
                - {p["output_column"] for p in preview}
            ),
        }))
    except Exception as exc:
        ds.rollback()
        logger.exception("[design_resolve_save_bindings] core=%s failed: %s", core_id, exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


# ── CardDAV caller-ID: aktivní sada (Fáze 1.2, 2.6.2026) ────────────────────
# Po click-to-call přidej/obnov kontakt v user.carddav_active_contact.
# Klasifikace: EC_Kontakt.TypZakazky=10 ('prvotní oslovení') → 'potential',
# jinak (vč. NULL = zavedená DB) → 'real' (oddělené adresáře, Marti's B).
# Best-effort — vytáčení proběhlo client-side, tohle ho nikdy nesmí shodit.

def _vc_escape(v) -> str:
    return (str(v).replace("\\", "\\\\").replace(",", "\\,")
            .replace(";", "\\;").replace("\n", "\\n").replace("\r", ""))


def _build_crm_vcard(contact_ref, called_phone, row: dict, category=None,
                     name=None, fn_prefix="") -> str:
    fn = str(name or row.get("FirmaText") or row.get("KontaktText") or "Kontakt").strip() or "Kontakt"
    # Prefix do jména (STR-P/STR-Z) → vyhledatelné v telefonu (Marti: telefon
    # neumí hledat dle skupiny, ale dle jména ano).
    if fn_prefix:
        fn = fn_prefix + " " + fn
    lines = ["BEGIN:VCARD", "VERSION:3.0",
             "UID:strategie-crm-" + str(contact_ref),
             "FN:" + _vc_escape(fn)]
    # ORG jen když máme reálnou firmu odlišnou od jména (žádná duplicita FN/ORG).
    _firma = (str(row.get("FirmaText")).strip() if row.get("FirmaText") else "")
    if _firma and _firma != fn:
        lines.append("ORG:" + _vc_escape(_firma))
    # CATEGORIES → viditelný štítek/skupina v telefonu (DAVx5 režim "categories").
    if category:
        lines.append("CATEGORIES:" + _vc_escape(category))
    phones = []
    for p in (called_phone, row.get("FirmaTelefon")):
        if p:
            ps = str(p).strip()
            if ps and ps not in phones:
                phones.append(ps)
    for ps in phones:
        lines.append("TEL;TYPE=WORK:" + _vc_escape(ps))
    if row.get("FirmaEmail"):
        lines.append("EMAIL;TYPE=WORK:" + _vc_escape(str(row["FirmaEmail"]).strip()))
    if row.get("FirmaWeb"):
        lines.append("URL:" + _vc_escape(str(row["FirmaWeb"]).strip()))
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def _carddav_touch_from_call(uid: int, contact_ref, called_phone,
                             contact_name=None, typ_zakazky=None,
                             contact_table=None) -> None:
    """Best-effort upsert kontaktu do CardDAV aktivní sady po hovoru.

    Grid-agnostic: frontend pošle jméno (+ volitelně TypZakazky) z řádku →
    vCard z jména + voleného čísla, klasifikace z typu. Fallback (bez jména):
    firemní grid (rowId = EC_Kontakt.ID) → MCP fetch z EC_Kontakt.
    """
    try:
        if not uid or not called_phone:
            return
        # CRM kontakty jsou EUROSOFT bez ohledu na to, v jakém tenantu user
        # zrovna "sedí". Povol: rodič (cross-tenant) NEBO aktivní člen EUROSOFT.
        # (Dřív se gateovalo na last_active_tenant → blokovalo rodiče jako Marti.)
        from core.database_data import get_data_session as _gds_chk
        from sqlalchemy import text as _sql_chk
        _chk = _gds_chk()
        try:
            _allowed = _chk.execute(_sql_chk(
                "SELECT (u.is_marti_parent OR EXISTS("
                "  SELECT 1 FROM public.user_tenants ut "
                "  WHERE ut.user_id = u.id AND ut.tenant_id = :t "
                "    AND ut.membership_status = 'active')) "
                "FROM public.users u WHERE u.id = :uid"
            ), {"uid": uid, "t": EUROSOFT_TENANT_ID}).scalar()
        finally:
            _chk.close()
        if not _allowed:
            return

        name = (str(contact_name).strip() if contact_name not in (None, "") else "")
        import re as _re_cd
        # contact_ref klíč: stabilní per řádek (grid-agnostic). Bez rowId → dle čísla.
        if contact_ref not in (None, ""):
            cref = (str(contact_table) + ":" + str(contact_ref)) if contact_table else str(contact_ref)
        else:
            cref = "tel:" + (_re_cd.sub(r"\D", "", str(called_phone)) or "x")

        if name:
            # Frontend dal jméno → grid-agnostic, žádný MCP fetch. row={} →
            # FN=name, žádné ORG (nevíme firmu, ať není duplicita).
            row = {}
            if typ_zakazky not in (None, ""):
                try:
                    addressbook = "potential" if int(typ_zakazky) == 10 else "real"
                except (TypeError, ValueError):
                    addressbook = "real"
            else:
                addressbook = "real"
        else:
            # Fallback: firemní grid, rowId = EC_Kontakt.ID → MCP fetch.
            try:
                cref_int = int(contact_ref)
            except (TypeError, ValueError):
                return
            from modules.conversation.application.eurosoft_mcp_client import (
                get_eurosoft_mcp_client,
            )
            import json as _json_cd
            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                return
            sql = (
                "SELECT ID, FirmaText, FirmaTelefon, FirmaEmail, FirmaWeb, "
                "TypZakazky, KontaktText FROM EC_Kontakt WHERE ID = " + str(cref_int)
            )
            raw = mcp.call_tool_sync(
                full_name="eurosoft_strategie_query_raw",
                arguments={"sql": sql, "db_name": "DB_EC"},
                conversation_id=None,
            )
            res = _json_cd.loads(raw)
            if not res.get("ok") or not res.get("rows"):
                return
            row = res["rows"][0]
            addressbook = "potential" if row.get("TypZakazky") == 10 else "real"
            cref = str(cref_int)

        if addressbook == "potential":
            _prefix, _cat = "STR-P", "Potenciální"
        else:
            _prefix, _cat = "STR-Z", "Zákazníci"
        vcard = _build_crm_vcard(cref, called_phone, row, category=_cat,
                                 name=(name or None), fn_prefix=_prefix)

        from core.database_data import get_data_session as _gds_cd
        from sqlalchemy import text as _sql_cd
        tenant_id = EUROSOFT_TENANT_ID  # CRM kontakt → vždy EUROSOFT tenant
        s = _gds_cd()
        try:
            s.execute(_sql_cd('''
                INSERT INTO "user".carddav_active_contact
                  (user_id, tenant_id, contact_ref, addressbook, vcard_cache,
                   last_active_at, last_active_action, ttl_days)
                VALUES (:uid, :tid, :cr, :ab, :vc, now(), 'call_outbound', 30)
                ON CONFLICT (user_id, contact_ref) DO UPDATE SET
                   last_active_at = now(),
                   last_active_action = 'call_outbound',
                   addressbook = EXCLUDED.addressbook,
                   vcard_cache = EXCLUDED.vcard_cache,
                   ttl_days = 30,
                   removed_at = NULL
            '''), {"uid": uid, "tid": tenant_id, "cr": cref,
                   "ab": addressbook, "vc": vcard})
            s.execute(_sql_cd('''
                INSERT INTO "user".carddav_sync_event (user_id, contact_ref, event_type)
                VALUES (:uid, :cr, 'add')
            '''), {"uid": uid, "cr": cref})
            s.commit()
        finally:
            s.close()
        logger.info("[carddav] active-set upsert user=%s ref=%s ab=%s name=%r",
                    uid, cref, addressbook, name or "(mcp)")
    except Exception as exc:
        logger.warning("[carddav_touch] best-effort skip: %s", exc)


@api_router.post("/contact-action")
async def log_contact_action(req: Request) -> JSONResponse:
    """Fáze 1A (1.6.2026, Marti: "archivovat čísla která se vytáčely"):
    archiv akcí na buňkách/polích (phone/email/web). Volá frontend
    erp_cell_actions.js _log() při dvojkliku v gridu / klik na ikonu ve formu.

    Append-only audit (Fix N doctrine) — jen INSERT. Auth: jakýkoliv
    přihlášený user (Pavel obchodník to potřebuje, ne jen parent).
    NE-anonymní — user_id + login_name.

    Body: {action_kind: phone|email|web, value, contact_table?,
           contact_row_id?, template_id?}
    """
    from core.database_data import get_data_session as _gds_ca
    from sqlalchemy import text as _sql_ca

    uid = _get_uid(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    kind = (str(body.get("action_kind") or "")).strip().lower()
    if kind not in ("phone", "email", "web"):
        return JSONResponse({"ok": False, "error": "neznámý action_kind"}, status_code=400)
    value = body.get("value")
    contact_table = body.get("contact_table")
    _cr_raw = body.get("contact_row_id")
    try:
        contact_row_id = int(_cr_raw) if _cr_raw not in (None, "") else None
    except (TypeError, ValueError):
        contact_row_id = None
    _tid_raw = body.get("template_id")
    try:
        template_id = int(_tid_raw) if _tid_raw not in (None, "") else None
    except (TypeError, ValueError):
        template_id = None
    contact_name = body.get("contact_name")       # CardDAV F1.2: jméno z řádku
    typ_zakazky = body.get("typ_zakazky")          # CardDAV F1.2: TypZakazky z řádku (10=potential)

    ds = _gds_ca()
    try:
        ln = ds.execute(_sql_ca(
            "SELECT COALESCE(login_name, short_name, first_name, '') "
            "FROM public.users WHERE id = :uid"
        ), {"uid": uid}).scalar()
        ds.execute(_sql_ca("""
            INSERT INTO fw.contact_action_log
              (user_id, user_login_name, action_kind, value,
               contact_table, contact_row_id, template_id)
            VALUES (:uid, :ln, :k, :v, :ct, :cr, :tid)
        """), {"uid": uid, "ln": ln, "k": kind, "v": value,
               "ct": contact_table, "cr": contact_row_id, "tid": template_id})
        ds.commit()
        # CardDAV F1.2: po hovoru přidej kontakt do aktivní sady (best-effort).
        if kind == "phone":
            _carddav_touch_from_call(uid, contact_row_id, value,
                                     contact_name=contact_name,
                                     typ_zakazky=typ_zakazky,
                                     contact_table=contact_table)
        return JSONResponse({"ok": True})
    except Exception as exc:
        ds.rollback()
        logger.exception("[log_contact_action] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/phone-dial-request")
async def create_phone_dial_request(req: Request) -> JSONResponse:
    """Fáze 3A (1.6.2026, Marti: telefon cross-device): PC klik na telefon →
    fronta pro mobil. target_user_id = sám sebe (Marti na PC chce vytočit
    svůj mobil). Mobil pollne /pending → ťukací banner → tel: → consume."""
    from core.database_data import get_data_session as _gds_pdr
    from sqlalchemy import text as _sql_pdr

    uid = _get_uid(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    phone = (str(body.get("phone") or "")).strip()
    if not phone:
        return JSONResponse({"ok": False, "error": "chybí phone"}, status_code=400)
    raw_value = (str(body.get("raw_value") or "")).strip() or None
    label = (str(body.get("label") or "")).strip() or None

    ds = _gds_pdr()
    try:
        rid = ds.execute(_sql_pdr("""
            INSERT INTO fw.phone_dial_request
              (target_user_id, phone, raw_value, label)
            VALUES (:uid, :ph, :rv, :lb) RETURNING id
        """), {"uid": uid, "ph": phone[:64],
               "rv": raw_value[:128] if raw_value else None,
               "lb": label[:200] if label else None}).scalar()
        ds.commit()
        # Marti 3.6.: po založení záznamu vrať i edit core (Protokol vytáčení
        # → poznámka), ať PC po vytočení rovnou otevře jádro pro zápis hovoru.
        # Lookup dle code (stabilní), ne magic id. None = frontend neotevře.
        edit_core_id = None
        try:
            edit_core_id = ds.execute(_sql_pdr(
                "SELECT id FROM fw.core WHERE code = 'crm.phone_dial_log_edit'"
            )).scalar()
        except Exception:
            pass
        return JSONResponse({"ok": True, "id": rid, "edit_core_id": edit_core_id})
    except Exception as exc:
        ds.rollback()
        logger.exception("[create_phone_dial_request] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.get("/phone-dial-request/pending")
async def list_pending_phone_dials(req: Request) -> JSONResponse:
    """Pending dial requesty pro current usera (last 10 min). Mobil poll."""
    from core.database_data import get_data_session as _gds_pdr2
    from sqlalchemy import text as _sql_pdr2

    uid = _uid_from_token_or_cookie(req)
    ds = _gds_pdr2()
    try:
        rows = ds.execute(_sql_pdr2("""
            SELECT id, phone, raw_value, label, created_at
            FROM fw.phone_dial_request
            WHERE target_user_id = :uid AND status = 'pending'
              AND created_at > now() - interval '10 minutes'
            ORDER BY id ASC
        """), {"uid": uid}).mappings().all()
        return JSONResponse(jsonable_encoder({
            "ok": True, "requests": [dict(r) for r in rows],
        }))
    except Exception as exc:
        logger.exception("[list_pending_phone_dials] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/phone-dial-request/{req_id}/consume")
async def consume_phone_dial_request(req_id: int, req: Request) -> JSONResponse:
    """Mobil označí dial request done/dismissed po tapu na banner."""
    from core.database_data import get_data_session as _gds_pdr3
    from sqlalchemy import text as _sql_pdr3

    uid = _uid_from_token_or_cookie(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    status = (str(body.get("status") or "done")).strip().lower()
    if status not in ("done", "dismissed"):
        status = "done"

    ds = _gds_pdr3()
    try:
        ds.execute(_sql_pdr3("""
            UPDATE fw.phone_dial_request
            SET status = :st, consumed_at = now()
            WHERE id = :id AND target_user_id = :uid AND status = 'pending'
        """), {"st": status, "id": req_id, "uid": uid})
        ds.commit()
        return JSONResponse({"ok": True})
    except Exception as exc:
        ds.rollback()
        logger.exception("[consume_phone_dial_request] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/phone-dial-request/{req_id}/call-result")
async def report_phone_call_result(req_id: int, req: Request) -> JSONResponse:
    """Mobilní appka po dokončení hovoru propíše do tabulky vyzvánění výsledek
    z call-logu: start hovoru (started_at_ms) + doba hovoru (talk_duration_s)
    + volitelně odhad doby vyzvánění (ring_estimate_s). Bearer token (sdílí
    CardDAV) NEBO cookie. Identifikace kontaktu = řádek vyzvánění (phone+label).
    Marti 4.6.2026."""
    from core.database_data import get_data_session as _gds_cr
    from sqlalchemy import text as _sql_cr

    uid = _uid_from_token_or_cookie(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    started_ms = body.get("started_at_ms")
    talk = body.get("talk_duration_s")
    ring = body.get("ring_estimate_s")
    ds = _gds_cr()
    try:
        ds.execute(_sql_cr("""
            UPDATE fw.phone_dial_request
            SET call_started_at = CASE WHEN :ms IS NULL THEN call_started_at
                                       ELSE to_timestamp(:ms / 1000.0) END,
                talk_duration_s = :talk,
                ring_estimate_s = :ring,
                call_reported_at = now()
            WHERE id = :id AND target_user_id = :uid
        """), {"ms": started_ms, "talk": talk, "ring": ring,
               "id": req_id, "uid": uid})
        ds.commit()
        return JSONResponse({"ok": True})
    except Exception as exc:
        ds.rollback()
        logger.exception("[report_phone_call_result] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


# ── Distribuce mobilních appek (vlastní APK na našem serveru + samo-aktualizace).
# UNIVERZÁLNÍ pro víc aplikací přes {app_key} (Marti 4.6.2026). Bez Obchodu Play:
# appka pollne /app/{key}/latest (token), porovná version_code, novější stáhne
# z /app/{key}/download a nabídne instalaci. Upload jen rodič. Heartbeat = přehled
# kdo na jaké verzi + nastavení (fw.mobile_device).
import re as _re_app

_APP_KEY_RE = _re_app.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")


def _app_key_ok(key: str) -> bool:
    return bool(_APP_KEY_RE.match(key or ""))


def _app_releases_dir(app_key: str) -> str:
    import os as _os_ar
    base = _os_ar.environ.get("APP_RELEASES_DIR")
    if not base:
        from core.config import settings as _st_ar
        media = getattr(_st_ar, "media_storage_root", "D:/Data/STRATEGIE/media")
        base = _os_ar.path.join(_os_ar.path.dirname(media.rstrip("/\\")), "app_releases")
    d = _os_ar.path.join(base, app_key)
    _os_ar.makedirs(d, exist_ok=True)
    return d


def _app_latest_row(app_key: str) -> dict:
    """Nejnovější verze appky z fw.app_version (DB = zdroj pravdy, jako ERP)."""
    from core.database_data import get_data_session as _gds_lr
    from sqlalchemy import text as _sql_lr
    ds = _gds_lr()
    try:
        r = ds.execute(_sql_lr("""
            SELECT app_key, app_name, version_code, version_name, apk_file, size, notes,
                   to_char(released_at,'YYYY-MM-DD HH24:MI') AS released_at
            FROM fw.app_version
            WHERE app_key = :app
            ORDER BY version_code DESC
            LIMIT 1
        """), {"app": app_key}).mappings().first()
        return dict(r) if r else {}
    except Exception:
        return {}
    finally:
        ds.close()


@api_router.get("/app/{app_key}/latest")
async def app_latest(app_key: str, req: Request) -> JSONResponse:
    """Nejnovější dostupná verze appky {app_key} (token NEBO cookie)."""
    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    _uid_from_token_or_cookie(req)
    row = _app_latest_row(app_key)
    if not row.get("version_code"):
        return JSONResponse({"ok": True, "available": False})
    return JSONResponse({
        "ok": True,
        "available": True,
        "app_key": app_key,
        "app_name": row.get("app_name") or "",
        "version_code": int(row.get("version_code") or 0),
        "version_name": row.get("version_name") or "",
        "notes": row.get("notes") or "",
        "size": int(row.get("size") or 0),
        "released_at": row.get("released_at") or "",
        "download_url": "/api/v1/erp/app/%s/download" % app_key,
    })


@api_router.get("/app/{app_key}/download")
async def app_download(app_key: str, req: Request):
    """Stáhne nejnovější APK appky {app_key} (token NEBO cookie)."""
    import os as _os_ad
    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    _uid_from_token_or_cookie(req)
    row = _app_latest_row(app_key)
    fn = row.get("apk_file")
    if not fn:
        return JSONResponse({"ok": False, "error": "Žádná verze"}, status_code=404)
    path = _os_ad.path.join(_app_releases_dir(app_key), fn)
    if not _os_ad.path.isfile(path):
        return JSONResponse({"ok": False, "error": "Soubor chybí"}, status_code=404)
    return FileResponse(
        path,
        media_type="application/vnd.android.package-archive",
        filename="%s.apk" % app_key,
    )


@api_router.get("/app/{app_key}/versions")
async def app_versions(app_key: str, req: Request) -> JSONResponse:
    """Historie verzí appky (jako ERP verzování — s datem a časem). Jen rodič."""
    from core.database_data import get_data_session as _gds_av
    from sqlalchemy import text as _sql_av
    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_av()
    try:
        rows = ds.execute(_sql_av("""
            SELECT version_code, version_name, size, notes,
                   to_char(released_at,'YYYY-MM-DD HH24:MI') AS released_at
            FROM fw.app_version
            WHERE app_key = :app
            ORDER BY version_code DESC
        """), {"app": app_key}).mappings().all()
        return JSONResponse({"ok": True, "app_key": app_key,
                             "versions": [dict(r) for r in rows]})
    except Exception as exc:
        logger.exception("[app_versions] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/app/{app_key}/upload")
async def app_upload(
    app_key: str,
    req: Request,
    file: UploadFile = File(...),
    version_code: int = Form(...),
    version_name: str = Form(""),
    app_name: str = Form(""),
    notes: str = Form(""),
) -> JSONResponse:
    """Nahraje novou verzi APK appky {app_key} (jen rodič). Uloží APK + záznam
    verze do fw.app_version (datum+čas vydání = released_at)."""
    import os as _os_au
    from core.database_data import get_data_session as _gds_up
    from sqlalchemy import text as _sql_up

    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    # Auth: parent session (UI) NEBO X-Deploy-Token (watcher „nahraj z buildu").
    _tok = req.headers.get("X-Deploy-Token")
    _env_tok = _os_au.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if _tok and _env_tok and _tok == _env_tok:
        uid = 0  # systémový (watcher publish z NB buildu)
    else:
        uid = _get_uid(req)
        _require_parent(uid)

    name = (file.filename or "").lower()
    if not name.endswith(".apk"):
        return JSONResponse({"ok": False, "error": "Jen soubor .apk"}, status_code=400)
    if int(version_code) <= 0:
        return JSONResponse({"ok": False, "error": "Neplatný version_code"}, status_code=400)

    rel_dir = _app_releases_dir(app_key)
    fname = "%s-%d.apk" % (app_key, int(version_code))
    dest = _os_au.path.join(rel_dir, fname)
    size = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                size += len(chunk)
                if size > 200 * 1024 * 1024:  # cap 200 MB
                    out.close()
                    _os_au.remove(dest)
                    return JSONResponse(
                        {"ok": False, "error": "APK je příliš velké (>200 MB)"},
                        status_code=400,
                    )
    except Exception as exc:
        logger.exception("[app_upload] save failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    ds = _gds_up()
    try:
        ds.execute(_sql_up("""
            INSERT INTO fw.app_version
              (app_key, app_name, version_code, version_name, apk_file, size, notes,
               released_at, uploaded_by)
            VALUES (:app,:aname,:vc,:vn,:file,:size,:notes, now(), :uid)
            ON CONFLICT (app_key, version_code) DO UPDATE SET
              app_name=EXCLUDED.app_name, version_name=EXCLUDED.version_name,
              apk_file=EXCLUDED.apk_file, size=EXCLUDED.size, notes=EXCLUDED.notes,
              released_at=now(), uploaded_by=EXCLUDED.uploaded_by
        """), {"app": app_key, "aname": app_name.strip() or None,
               "vc": int(version_code), "vn": version_name.strip() or None,
               "file": fname, "size": size, "notes": notes.strip() or None,
               "uid": uid})
        ds.commit()
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_upload] db insert failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()

    logger.info("[app_upload] %s verze %s (code %d, %d B) nahrál uid=%d",
                app_key, version_name, int(version_code), size, uid)
    return JSONResponse({"ok": True, "app_key": app_key, "version_code": int(version_code),
                         "version_name": version_name.strip(), "size": size})


@api_router.post("/app/{app_key}/heartbeat")
async def app_heartbeat(app_key: str, req: Request) -> JSONResponse:
    """Appka hlásí svůj stav (verze + nastavení) → fw.mobile_device. Token NEBO cookie."""
    from core.database_data import get_data_session as _gds_hb
    from sqlalchemy import text as _sql_hb

    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    uid = _uid_from_token_or_cookie(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    dev = (str(body.get("device_id") or "")).strip()[:120]
    if not dev:
        return JSONResponse({"ok": False, "error": "device_id required"}, status_code=400)

    def _b(v):
        return bool(v) if v is not None else None

    params = {
        "app": app_key, "uid": uid, "dev": dev,
        "label": (str(body.get("device_label") or "")[:120]) or None,
        "vc": body.get("version_code"),
        "vn": (str(body.get("version_name") or "")[:40]) or None,
        "rel": (str(body.get("android_release") or "")[:40]) or None,
        "svc": _b(body.get("service_enabled")),
        "clog": _b(body.get("call_log_enabled")),
        "notif": _b(body.get("notif_enabled")),
        "fs": _b(body.get("fullscreen_enabled")),
        "url": (str(body.get("server_url") or "")[:200]) or None,
    }
    ds = _gds_hb()
    try:
        ds.execute(_sql_hb("""
            INSERT INTO fw.mobile_device
              (app_key, user_id, device_id, device_label, version_code, version_name,
               android_release, service_enabled, call_log_enabled, notif_enabled,
               fullscreen_enabled, server_url, last_seen_at)
            VALUES (:app,:uid,:dev,:label,:vc,:vn,:rel,:svc,:clog,:notif,:fs,:url, now())
            ON CONFLICT (app_key, user_id, device_id) DO UPDATE SET
              device_label=EXCLUDED.device_label, version_code=EXCLUDED.version_code,
              version_name=EXCLUDED.version_name, android_release=EXCLUDED.android_release,
              service_enabled=EXCLUDED.service_enabled, call_log_enabled=EXCLUDED.call_log_enabled,
              notif_enabled=EXCLUDED.notif_enabled, fullscreen_enabled=EXCLUDED.fullscreen_enabled,
              server_url=EXCLUDED.server_url, last_seen_at=now()
        """), params)
        ds.commit()

        # HR inventura + presence (5.6.): telefon appky → fw.hr_device.
        # in_building z firemní IP NEBO firemní WiFi (SSID hlásí appka).
        # Best-effort, neovlivní odpověď heartbeatu.
        try:
            from modules.hr.presence import (touch_device as _hr_td,
                                             client_ip as _hr_ip,
                                             ip_in_building as _hr_inb,
                                             ssid_in_building as _hr_sib)
            _hb_ip = _hr_ip(req)
            _hb_ssid = (str(body.get("wifi_ssid") or "")[:64]) or None
            _hr_td(device_key=dev, device_type="phone",
                   name=params.get("label"), uid=uid, ip_str=_hb_ip,
                   source="mobile_app", ssid=_hb_ssid)
            try:
                from core.log_queue import log_event as _hb_log
                _hb_log(level="info", source="py", module_id="hr.heartbeat",
                        message=(f"heartbeat uid={uid} dev={dev} ip={_hb_ip} "
                                 f"ssid={_hb_ssid} in_building="
                                 f"{_hr_inb(_hb_ip) or _hr_sib(_hb_ssid)}"))
            except Exception:
                pass
        except Exception:
            pass

        return JSONResponse({"ok": True})
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_heartbeat] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


# ── Ověření telefonního čísla přes SMS (Marti 6.6.2026) ──────────────────
# Appka po potvrzení uživatelem pošle z telefonu SMS s tokenem STG-PAIR-XXXX
# na trusted SIM STRATEGIE; příchozí SMS (sms_preprocessor purpose=PAIR) z ní
# přečte číslo odesílatele → zapíše k zařízení + označí ověřeno. App pollne /status.
_SMS_VERIFY_TO = "+420778117879"  # Marti-AI / trusted SIM (sdílí 2FA)


@api_router.post("/app/phone-verify/start")
async def app_phone_verify_start(req: Request) -> JSONResponse:
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    dev = (str((body or {}).get("device_id") or "")).strip()[:120] or None
    lbl = (str((body or {}).get("device_label") or "")).strip()[:120] or None
    # Zjisti id carddav_tokenu, kterým se appka autentizovala — ať umíme zapsat
    # ověřené číslo přímo na ten záznam (a dedupovat podle čísla). Marti 6.6.2026.
    _ctid = None
    _auth = req.headers.get("authorization") or ""
    if _auth.lower().startswith("bearer "):
        _tk = _auth[7:].strip()
        if _tk:
            import hashlib as _h_pv
            from core.database_data import get_data_session as _gds_t
            from sqlalchemy import text as _sql_t
            _th = _h_pv.sha256(_tk.encode("utf-8")).hexdigest()
            _dt = _gds_t()
            try:
                _ctid = _dt.execute(_sql_t(
                    'SELECT id FROM "user".carddav_token '
                    'WHERE token_hash = :h AND revoked_at IS NULL'
                ), {"h": _th}).scalar()
            except Exception:
                _ctid = None
            finally:
                _dt.close()
    import secrets as _sec_pv
    token = "STG-PAIR-" + _sec_pv.token_hex(4).upper()
    from core.database_data import get_data_session as _gds_pv
    from sqlalchemy import text as _sql_pv
    ds = _gds_pv()
    try:
        ds.execute(_sql_pv("DELETE FROM fw.phone_verify WHERE expires_at < now()"))
        ds.execute(_sql_pv(
            "INSERT INTO fw.phone_verify (token, user_id, device_id, device_label, carddav_token_id, expires_at) "
            "VALUES (:t, :u, :d, :l, :ct, now() + interval '15 minutes')"
        ), {"t": token, "u": uid, "d": dev, "l": lbl, "ct": _ctid})
        ds.commit()
    except Exception as exc:
        ds.rollback()
        logger.warning("[phone-verify start] %s", exc)
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    finally:
        ds.close()
    return JSONResponse({"ok": True, "token": token, "send_to": _SMS_VERIFY_TO,
                         "body": token, "ttl_min": 15})


@api_router.get("/app/phone-verify/status")
async def app_phone_verify_status(req: Request, token: str = "") -> JSONResponse:
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    from core.database_data import get_data_session as _gds_ps
    from sqlalchemy import text as _sql_ps
    ds = _gds_ps()
    try:
        row = ds.execute(_sql_ps(
            "SELECT phone_number, verified_at FROM fw.phone_verify "
            "WHERE token = :t AND user_id = :u"
        ), {"t": (token or "").strip(), "u": uid}).first()
    finally:
        ds.close()
    if not row:
        return JSONResponse({"ok": True, "verified": False, "unknown": True})
    return JSONResponse({"ok": True, "verified": row[1] is not None,
                         "phone_number": row[0]})


@api_router.post("/app/phone-set")
async def app_phone_set(req: Request) -> JSONResponse:
    """Uloží číslo telefonu přímo z appky (přečtené ze SIM + potvrzené uživatelem)
    — bez SMS brány. Zapíše k carddav_tokenu (kterým se appka hlásí) + k zařízení
    a dedupuje: jiné aktivní tokeny téhož uživatele se stejným číslem odpojí.
    Marti 6.6.2026 (vlastní appka = nepotřebujeme cizí SMS providera)."""
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    phone = (str((body or {}).get("phone_number") or "")).strip()[:32]
    dev = (str((body or {}).get("device_id") or "")).strip()[:120] or None
    if len(phone.replace("+", "").replace(" ", "")) < 6:
        return JSONResponse({"ok": False, "error": "invalid_phone"}, status_code=400)
    import hashlib as _h_set
    from core.database_data import get_data_session as _gds_set
    from sqlalchemy import text as _sql_set
    # id tokenu, kterým se appka autentizovala (ať číslo zapíšeme na ten záznam)
    ctid = None
    _auth = req.headers.get("authorization") or ""
    if _auth.lower().startswith("bearer "):
        _tk = _auth[7:].strip()
        if _tk:
            _dh = _gds_set()
            try:
                ctid = _dh.execute(_sql_set(
                    'SELECT id FROM "user".carddav_token '
                    'WHERE token_hash = :h AND revoked_at IS NULL'
                ), {"h": _h_set.sha256(_tk.encode("utf-8")).hexdigest()}).scalar()
            except Exception:
                ctid = None
            finally:
                _dh.close()
    ds = _gds_set()
    try:
        if dev:
            ds.execute(_sql_set(
                "UPDATE fw.mobile_device SET phone_number=:p, phone_verified_at=now() "
                "WHERE user_id=:u AND device_id=:d"
            ), {"p": phone, "u": uid, "d": dev})
        else:
            ds.execute(_sql_set(
                "UPDATE fw.mobile_device SET phone_number=:p, phone_verified_at=now() "
                "WHERE user_id=:u"
            ), {"p": phone, "u": uid})
        if ctid:
            ds.execute(_sql_set(
                'UPDATE "user".carddav_token SET phone_number=:p WHERE id=:c'
            ), {"p": phone, "c": ctid})
            # dedup: stejné číslo u téhož uživatele → ostatní odpoj (drž jen tenhle)
            ds.execute(_sql_set(
                'UPDATE "user".carddav_token SET revoked_at=now() '
                'WHERE user_id=:u AND phone_number=:p AND revoked_at IS NULL AND id<>:c'
            ), {"u": uid, "p": phone, "c": ctid})
        ds.commit()
    except Exception as exc:
        ds.rollback()
        logger.warning("[phone-set] %s", exc)
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    finally:
        ds.close()
    return JSONResponse({"ok": True, "phone_number": phone})


@api_router.get("/app/devices")
async def app_devices(req: Request) -> JSONResponse:
    """Přehled všech mobilních zařízení (kdo / appka / verze / nastavení). Jen rodič."""
    from core.database_data import get_data_session as _gds_dv
    from sqlalchemy import text as _sql_dv

    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_dv()
    try:
        rows = ds.execute(_sql_dv("""
            SELECT d.id AS device_row_id, d.app_key, d.user_id,
                   COALESCE(NULLIF(TRIM(CONCAT(u.first_name,' ',u.last_name)),''),
                            u.login_name, '#'||d.user_id) AS user_name,
                   d.device_label, d.version_code, d.version_name, d.android_release,
                   d.service_enabled, d.call_log_enabled, d.notif_enabled,
                   d.fullscreen_enabled, d.server_url,
                   EXTRACT(EPOCH FROM (now() - d.last_seen_at))::int AS secs_ago,
                   to_char(d.last_seen_at,'YYYY-MM-DD HH24:MI') AS last_seen
            FROM fw.mobile_device d
            LEFT JOIN public.users u ON u.id = d.user_id
            WHERE d.removed_at IS NULL
            ORDER BY d.last_seen_at DESC NULLS LAST
        """)).mappings().all()
        return JSONResponse({"ok": True, "devices": [dict(r) for r in rows]})
    except Exception as exc:
        logger.exception("[app_devices] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/app/device/{device_row_id}/remove")
async def app_device_remove(device_row_id: int, req: Request) -> JSONResponse:
    """Odebere zařízení z přehledu (soft: removed_at). Jen rodič."""
    from core.database_data import get_data_session as _gds_dr
    from sqlalchemy import text as _sql_dr
    uid = _get_uid(req)
    _require_parent(uid)
    ds = _gds_dr()
    try:
        ds.execute(_sql_dr(
            "UPDATE fw.mobile_device SET removed_at = now() WHERE id = :id"
        ), {"id": int(device_row_id)})
        ds.commit()
        return JSONResponse({"ok": True})
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_device_remove] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.get("/app/avatar")
def app_avatar(req: Request):
    """Avatar default persony (Marti-AI) pro mobilní appku. Token NEBO cookie."""
    from core.database_data import get_data_session as _gds_avt
    from sqlalchemy import text as _sql_avt
    from modules.personas.application import avatar_service as _avs
    _uid_from_token_or_cookie(req)
    ds = _gds_avt()
    try:
        pid = ds.execute(_sql_avt(
            "SELECT id FROM personas WHERE is_default = true ORDER BY id LIMIT 1"
        )).scalar()
    except Exception:
        pid = None
    finally:
        ds.close()
    if pid is None:
        raise HTTPException(status_code=404, detail="Žádná default persona")
    path = _avs.get_avatar_path(int(pid))
    if not path:
        raise HTTPException(status_code=404, detail="Avatar neexistuje")
    return FileResponse(path, media_type="image/jpeg")


# ── Vzdálená doporučení parentů → na mobilu dialog Povolit/Zamítnout (Marti 5.6).
_CMD_DEFAULTS = {
    "fullscreen": ("Povolení: vytáčení přes celou obrazovku",
        "Aby po odemčení vyskočil rovnou dialer, povol „Zobrazit přes celou "
        "obrazovku“. Klepni Povolit a otevře se přesné nastavení."),
    "calllog": ("Povolení: seznam hovorů",
        "Pro zápis délky hovoru do CRM povol přístup k seznamu hovorů. Klepni Povolit."),
    "notif": ("Povolení: oznámení",
        "Aby ti chodila upozornění (vytáčení, aktualizace), povol oznámení."),
    "battery": ("Vypnout úsporu baterie",
        "Aby appka spolehlivě běžela na pozadí, vyjmi ji z optimalizace baterie."),
    "update": ("Aktualizace appky",
        "Je k dispozici novější verze appky. Klepni Povolit pro stažení a instalaci."),
    "message": ("Zpráva od STRATEGIE", ""),
    "claude_confirm": ("Claude čeká na potvrzení",
        "Claude chce provést akci. Klepni Povolit pro provedení, nebo Odmítnout."),
    "claude_msg": ("Zpráva od Claude", ""),
}


@api_router.post("/app/command")
async def app_command_create(req: Request) -> JSONResponse:
    """Parent pošle doporučení uživateli (na mobilu dialog). Jen rodič."""
    import json as _json_cc
    from core.database_data import get_data_session as _gds_cc
    from sqlalchemy import text as _sql_cc
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        body = await req.json()
    except Exception:
        body = {}
    target = body.get("target_user_id")
    ctype = (str(body.get("command_type") or "")).strip()
    if not target or not ctype:
        return JSONResponse({"ok": False, "error": "target_user_id + command_type"}, status_code=400)
    app_key = (str(body.get("app_key") or "mobile")).strip() or "mobile"
    d_title, d_msg = _CMD_DEFAULTS.get(ctype, ("Doporučení", ""))
    title = (str(body.get("title") or d_title))[:120]
    message = (str(body.get("message") or d_msg))[:600]
    payload = body.get("payload")
    ds = _gds_cc()
    try:
        new_id = ds.execute(_sql_cc("""
            INSERT INTO fw.mobile_command
              (app_key, target_user_id, command_type, title, message, payload, created_by)
            VALUES (:app,:uid,:ct,:title,:msg,
                    CASE WHEN :payload IS NULL THEN NULL ELSE CAST(:payload AS jsonb) END,
                    :by)
            RETURNING id
        """), {"app": app_key, "uid": int(target), "ct": ctype, "title": title,
               "msg": message,
               "payload": (_json_cc.dumps(payload) if payload else None),
               "by": uid}).scalar()
        ds.commit()
        return JSONResponse({"ok": True, "id": new_id})
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_command_create] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.get("/app/{app_key}/commands/pending")
async def app_commands_pending(app_key: str, req: Request) -> JSONResponse:
    """Appka načte čekající doporučení pro přihlášeného uživatele (token NEBO cookie)."""
    from core.database_data import get_data_session as _gds_cp
    from sqlalchemy import text as _sql_cp
    if not _app_key_ok(app_key):
        return JSONResponse({"ok": False, "error": "Neplatný app_key"}, status_code=400)
    uid = _uid_from_token_or_cookie(req)
    # HR presence (5.6.): tento poll běží často (á 4 s) dokud appka žije →
    # osvěžíme čerstvost telefonu (řeší řídké ~20min heartbeaty). Throttle 60s.
    try:
        from modules.hr.presence import refresh_user_phone as _cp_rp, client_ip as _cp_ip
        _cp_rp(uid, _cp_ip(req))
    except Exception:
        pass
    ds = _gds_cp()
    try:
        rows = ds.execute(_sql_cp("""
            SELECT id, command_type, title, message, payload
            FROM fw.mobile_command
            WHERE app_key=:app AND target_user_id=:uid AND status='pending'
            ORDER BY id ASC LIMIT 20
        """), {"app": app_key, "uid": uid}).mappings().all()
        # Adaptivní interval pollu (Marti 6.6.): je-li co schválit → rychle;
        # pracuje-li Claude (nedávná aktivita) → svižně; v klidu → šetři baterii.
        if rows:
            next_poll_s = 3
        else:
            recent = False
            try:
                recent = ds.execute(_sql_cp(
                    "SELECT 1 FROM fw.claude_sql_log "
                    "WHERE created_at > now() - interval '5 minutes' LIMIT 1"
                )).first() is not None
            except Exception:
                recent = False
            next_poll_s = 6 if recent else 20
        return JSONResponse({"ok": True, "commands": [dict(r) for r in rows],
                             "next_poll_s": next_poll_s})
    except Exception as exc:
        logger.exception("[app_commands_pending] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/app/command/{cmd_id}/result")
async def app_command_result(cmd_id: int, req: Request) -> JSONResponse:
    """Appka hlásí rozhodnutí uživatele (accept/reject). Token NEBO cookie."""
    from core.database_data import get_data_session as _gds_cr2
    from sqlalchemy import text as _sql_cr2
    uid = _uid_from_token_or_cookie(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    decision = (str(body.get("decision") or "")).strip().lower()
    status = "accepted" if decision == "accept" else (
        "rejected" if decision == "reject" else "done")
    note = (str(body.get("note") or ""))[:300] or None
    ds = _gds_cr2()
    try:
        cmd = ds.execute(_sql_cr2(
            "SELECT command_type, payload FROM fw.mobile_command "
            "WHERE id=:id AND target_user_id=:uid"
        ), {"id": int(cmd_id), "uid": uid}).mappings().first()
        ds.execute(_sql_cr2("""
            UPDATE fw.mobile_command
            SET status=:st, result_note=:note, decided_at=now()
            WHERE id=:id AND target_user_id=:uid AND status='pending'
        """), {"st": status, "note": note, "id": int(cmd_id), "uid": uid})
        ds.commit()
        # claude_confirm → potvrzení z mobilu rovnou schválí/zamítne zápis
        wres = None
        if cmd and cmd["command_type"] == "claude_confirm" and decision in ("accept", "reject"):
            payload = cmd["payload"] or {}
            if isinstance(payload, str):
                try:
                    import json as _json_cr
                    payload = _json_cr.loads(payload)
                except Exception:
                    payload = {}
            wr = payload.get("write_request_id") if isinstance(payload, dict) else None
            if wr:
                wdec = "approve" if decision == "accept" else "reject"
                wres = _apply_write_decision(int(wr), wdec, uid)
                wres.pop("code", None)
        return JSONResponse({"ok": True, "write": wres})
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_command_result] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/app/notify")
async def app_notify(req: Request) -> JSONResponse:
    """Claude (X-Deploy-Token) pošle uživateli notifikaci na mobil — „hotovo /
    výsledek / potřebuju pozornost". Vytvoří claude_msg command → appka pollne
    (á 4 s) a cinkne. Bez potvrzování (jen informace). Marti 5.6."""
    import os as _os_n
    from core.database_data import get_data_session as _gn
    from sqlalchemy import text as _tn
    token = req.headers.get("X-Deploy-Token")
    env = _os_n.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env and token == env):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    try:
        uid = int(body.get("user_id") or _DEFAULT_APPROVER_UID)
    except (TypeError, ValueError):
        uid = _DEFAULT_APPROVER_UID
    title = (str(body.get("title") or "Zpráva od Claude"))[:120]
    message = (str(body.get("message") or ""))[:600]
    ds = _gn()
    try:
        nid = ds.execute(_tn("""
            INSERT INTO fw.mobile_command
              (app_key, target_user_id, command_type, title, message, created_by)
            VALUES ('mobile', :uid, 'claude_msg', :title, :msg, NULL)
            RETURNING id
        """), {"uid": uid, "title": title, "msg": message}).scalar()
        ds.commit()
        return JSONResponse({"ok": True, "id": nid})
    except Exception as exc:
        ds.rollback()
        logger.exception("[app_notify] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        ds.close()


@api_router.post("/app/netscan/ingest")
async def netscan_ingest(req: Request) -> JSONResponse:
    """Mikrotik/netscan agent (X-Deploy-Token) → seznam zařízení na firemní síti.
    Body: {devices:[{mac, ip?, hostname?, ssid?, active?}]}. Aktivní = na síti =
    v budově. Upsert do fw.hr_device dle MAC (device_key='mac:<mac>'). Vlastníka
    nezná → bez vazby na uživatele (link_user=False). Marti 5.6."""
    import os as _os_ns
    token = req.headers.get("X-Deploy-Token")
    env = _os_ns.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env and token == env):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    devices = body.get("devices") or []
    if not isinstance(devices, list):
        return JSONResponse({"ok": False, "error": "devices must be list"}, status_code=400)
    from modules.hr.presence import touch_device as _ni_td
    n = 0
    for d in devices:
        try:
            mac = (str(d.get("mac") or "")).strip().lower()
            if not mac or not d.get("active", True):
                continue
            host = (str(d.get("hostname") or "")[:120]) or None
            ip = (str(d.get("ip") or "")).strip() or None
            ssid = (str(d.get("ssid") or "")).strip() or None
            # Síťově objevené = na firemní síti = v budově (i drátové).
            # Vlastník neznámý → link_user=False. Kategorie 'other' (Marti
            # přeřadí v inventáři); existující typ se nepřepíše (touch_device
            # name=COALESCE, ale device_type ano — proto u nových 'other').
            _ni_td(device_key="mac:" + mac, device_type="other", name=host,
                   uid=None, ip_str=ip, source="mikrotik", ssid=ssid,
                   force_place="building", link_user=False)
            n += 1
        except Exception:
            pass
    return JSONResponse({"ok": True, "count": n})


@api_router.get("/contact-vcard")
async def contact_vcard(req: Request):
    """Fáze (1.6.2026, Marti: "přidávat čísla do kontaktů telefonu" — callback
    caller-ID): vygeneruje vCard 3.0 (.vcf). Web nemůže psát do adresáře přímo;
    .vcf s Content-Disposition attachment → OS nabídne "Přidat do kontaktů".

    Query (vše optional): given, family, fn, org, email, url,
    tel_cell, tel_work, tel. Slouží MVP banneru (fn+tel_cell) i plnému
    kontaktu z CRM řádku (frontend namapuje pole → params).
    """
    from fastapi.responses import Response as _VResp

    _get_uid(req)  # jakýkoliv přihlášený
    q = req.query_params

    def _vesc(s):
        return (str(s or "")
                .replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\r", "").replace("\n", "\\n"))

    given = (q.get("given") or "").strip()
    family = (q.get("family") or "").strip()
    org = (q.get("org") or "").strip()
    fn = (q.get("fn") or "").strip() or (given + " " + family).strip() or org or "Kontakt"
    email = (q.get("email") or "").strip()
    url = (q.get("url") or "").strip()

    lines = ["BEGIN:VCARD", "VERSION:3.0",
             "N:%s;%s;;;" % (_vesc(family), _vesc(given)),
             "FN:%s" % _vesc(fn)]
    if org:
        lines.append("ORG:%s" % _vesc(org))
    for key, typ in (("tel_cell", "CELL"), ("tel_work", "WORK"), ("tel", "VOICE")):
        num = (q.get(key) or "").strip()
        if num:
            lines.append("TEL;TYPE=%s:%s" % (typ, _vesc(num)))
    if email:
        lines.append("EMAIL;TYPE=WORK:%s" % _vesc(email))
    if url:
        lines.append("URL:%s" % _vesc(url))
    lines.append("END:VCARD")
    vcf = "\r\n".join(lines) + "\r\n"

    safe = "".join(c for c in fn if c.isalnum() or c in " _-")[:50].strip() or "kontakt"
    return _VResp(
        content=vcf,
        media_type="text/vcard; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="%s.vcf"' % safe},
    )


# ── Fáze (1.6.2026, Marti: "při každém nasazení request na Hard Reset") ──────
# Verze = git HEAD sha (mění se KAŽDÝM deployem — i static-only, čteme z disku).
# Klient (app_version_watch.js) polluje; při změně vs načtená verze → lišta
# "Nová verze — Obnovit". 30s in-memory cache (disk read levný, ne per-request).
_APP_VERSION_CACHE = {"v": None, "ts": 0.0}


def _read_git_head_sha():
    try:
        from pathlib import Path as _PathAV
        root = _PathAV(__file__).resolve().parents[3]  # modules/erp/api → repo root
        head = (root / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            refp = root / ".git" / ref
            if refp.exists():
                return refp.read_text(encoding="utf-8").strip()[:12]
            packed = root / ".git" / "packed-refs"
            if packed.exists():
                for line in packed.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and line.endswith(ref):
                        return line.split(" ", 1)[0].strip()[:12]
            return None
        return head[:12]  # detached HEAD = přímo sha
    except Exception:
        return None


@api_router.get("/app-version")
async def app_version(req: Request) -> JSONResponse:
    """Aktuální verze nasazeného kódu (git HEAD sha). Veřejné (žádný auth) —
    klient porovnává s verzí při načtení a nabídne obnovení po deployi."""
    import time as _time_av
    now = _time_av.time()
    if _APP_VERSION_CACHE["v"] is None or (now - _APP_VERSION_CACHE["ts"]) > 10:
        _APP_VERSION_CACHE["v"] = _read_git_head_sha() or "unknown"
        _APP_VERSION_CACHE["ts"] = now
    return JSONResponse({"version": _APP_VERSION_CACHE["v"]})


# ── Per-user UI preference (2.6.2026, Marti: chování e-mailových odkazů) ─────
# Uloženo v "user".ui_pref (Marti-AI's 4. tier — per-user config). App (strategie
# role) má SELECT/INSERT/UPDATE (GRANT v DDL). JSONB prefs — zatím email_link_mode,
# additivně další klíče. email_link_mode: 'mailto' (default) | 'owa' | 'copy'.
_UI_PREF_EMAIL_MODES = {"mailto", "owa", "copy"}


@api_router.get("/user-prefs")
def get_user_prefs(req: Request) -> JSONResponse:
    """Vrací per-user UI prefs ({} pokud nic nenastaveno / tabulka chybí)."""
    uid = _get_uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "not_authenticated"}, status_code=401)
    from core.database_data import get_data_session as _gds_up
    from sqlalchemy import text as _sql_up
    s = _gds_up()
    try:
        row = s.execute(_sql_up(
            'SELECT prefs FROM "user".ui_pref WHERE user_id = :uid'
        ), {"uid": uid}).mappings().one_or_none()
        prefs = (row["prefs"] if row else None) or {}
    except Exception as exc:
        logger.warning("get_user_prefs failed (table missing?): %s", exc)
        prefs = {}
    finally:
        s.close()
    return JSONResponse({"ok": True, "prefs": prefs})


@api_router.post("/user-prefs")
async def set_user_prefs(req: Request) -> JSONResponse:
    """Merge per-user UI prefs (upsert do "user".ui_pref). Body: {email_link_mode}."""
    uid = _get_uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "not_authenticated"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    patch = {}
    elm = body.get("email_link_mode")
    if elm is not None:
        if elm not in _UI_PREF_EMAIL_MODES:
            return JSONResponse(
                {"ok": False, "error": "invalid_email_link_mode",
                 "allowed": sorted(_UI_PREF_EMAIL_MODES)},
                status_code=400,
            )
        patch["email_link_mode"] = elm
    if not patch:
        return JSONResponse(
            {"ok": False, "error": "no_known_pref_keys"}, status_code=400)
    from core.database_data import get_data_session as _gds_up
    from sqlalchemy import text as _sql_up
    import json as _json_up
    s = _gds_up()
    try:
        s.execute(_sql_up('''
            INSERT INTO "user".ui_pref (user_id, prefs, updated_at)
            VALUES (:uid, CAST(:patch AS jsonb), now())
            ON CONFLICT (user_id)
            DO UPDATE SET prefs = "user".ui_pref.prefs || EXCLUDED.prefs,
                          updated_at = now()
        '''), {"uid": uid, "patch": _json_up.dumps(patch)})
        s.commit()
        row = s.execute(_sql_up(
            'SELECT prefs FROM "user".ui_pref WHERE user_id = :uid'
        ), {"uid": uid}).mappings().one_or_none()
        prefs = (row["prefs"] if row else patch) or {}
    except Exception as exc:
        s.rollback()
        logger.warning("set_user_prefs failed: %s", exc)
        return JSONResponse(
            {"ok": False, "error": "save_failed", "detail": str(exc)[:300]},
            status_code=500)
    finally:
        s.close()
    return JSONResponse({"ok": True, "prefs": prefs})


# ── Deploy na povel (1.6.2026, Marti: "git pull + restart na povel") ────────
# Reuse Phase 42 deployment_service (git pull + marker → RESTART-WATCHER).
# Jednoklik: spuštění = schválení. Auth: parent session (UI) NEBO X-Deploy-Token
# (NB skript / push-to-deploy). Token z env STRATEGIE_DEPLOY_TOKEN.

# ── Koordinace dvou instancí Claude (23 Marti / 24 Kristy) — Marti 3.6.2026 ──
# Advisory lock serializuje cloud deploy (git pull + restart) — dvě instance
# nesmí pullovat/restartovat současně. Presence board (fw.claude_instance)
# eviduje, kdo je online + co dělá.
_DEPLOY_LOCK_KEY = 778899   # pg_advisory_lock klíč pro /deploy/now
_CLAUDE_INSTANCE_NAMES = {"23": "Marti", "24": "Kristy"}
# Binding User<->Claude (Marti 3.6.): write-approval banner musí být per-user.
# Claude-23 komunikuje s Marti (1), Claude-24 s Kristý (11). Navázání je
# uložené v fw.claude_instance.bound_user_id; neatribuované/legacy requesty
# schvaluje default approver (Marti), aby nic neuvázlo.
_DEFAULT_APPROVER_UID = 1


def _record_instance_presence(instance_id, action: str, hostname=None) -> None:
    """Upsert fw.claude_instance (presence board). Best-effort — nikdy neshodí
    endpoint. Volá se na každý bridge call (deploy / sql / restart / heartbeat)."""
    iid = str(instance_id or "").strip()
    if not iid or iid == "?":
        return
    try:
        from core.database_data import get_data_session as _gp_pi
        from sqlalchemy import text as _tp_pi
        name = _CLAUDE_INSTANCE_NAMES.get(iid)
        s = _gp_pi()
        try:
            s.execute(_tp_pi(
                "INSERT INTO fw.claude_instance "
                "(instance_id, instance_name, hostname, last_seen_at, last_action, last_action_at) "
                "VALUES (:id, :nm, :host, now(), :act, now()) "
                "ON CONFLICT (instance_id) DO UPDATE SET "
                "  last_seen_at = now(), last_action = EXCLUDED.last_action, last_action_at = now(), "
                "  instance_name = COALESCE(EXCLUDED.instance_name, fw.claude_instance.instance_name), "
                "  hostname = COALESCE(EXCLUDED.hostname, fw.claude_instance.hostname)"
            ), {"id": iid, "nm": name, "host": (str(hostname).strip() or None) if hostname else None,
                "act": action})
            s.commit()
        finally:
            s.close()
    except Exception:
        pass


def _update_instance_work(iid: str, body: dict) -> None:
    """Work-lock + freshness (Marti 3.6.2026): heartbeat nese co instance staví
    (current_work + files) a stav lokálu (local_head/behind). Uloží do
    fw.claude_instance. Best-effort — nikdy neshodí heartbeat. Sloupce mohou
    chybět (před ALTER) → tichý fail."""
    try:
        from core.database_data import get_data_session as _gp_uw
        from sqlalchemy import text as _tp_uw
        cw = body.get("current_work")
        cwf = body.get("current_work_files")
        ws = (str(body.get("work_status") or "").strip() or
              ("active" if cw else "idle"))
        lh = body.get("local_head_sha")
        lb = body.get("local_behind")
        s = _gp_uw()
        try:
            s.execute(_tp_uw(
                "UPDATE fw.claude_instance SET "
                "  current_work = :cw, current_work_files = :cwf, "
                "  current_work_at = CASE WHEN :cw IS NOT NULL AND :cw <> '' "
                "                         THEN now() ELSE current_work_at END, "
                "  work_status = :ws, "
                "  local_head_sha = COALESCE(:lh, local_head_sha), "
                "  local_behind = COALESCE(:lb, local_behind) "
                "WHERE instance_id = :id"
            ), {"cw": cw, "cwf": cwf, "ws": ws, "lh": lh,
                "lb": (int(lb) if lb is not None else None), "id": iid})
            s.commit()
        finally:
            s.close()
    except Exception:
        pass


def _active_instances(exclude_id=None, within_min: int = 3) -> list:
    """Vrátí instance s heartbeatem < within_min (online). exclude_id vynechá
    volajícího (pro 'kdo DALŠÍ je aktivní'). Vč. work-lock (co staví) + freshness
    (kolik commitů pozadu). current_work jen pokud work_status='active' a není
    starší 2 h (jinak idle/stale → null)."""
    try:
        from core.database_data import get_data_session as _gp_ai
        from sqlalchemy import text as _tp_ai
        s = _gp_ai()
        try:
            rows = s.execute(_tp_ai(
                "SELECT instance_id, instance_name, hostname, last_action, "
                "  EXTRACT(EPOCH FROM (now() - last_seen_at))::int AS seen_ago_s, "
                "  CASE WHEN work_status = 'active' "
                "         AND current_work_at > now() - interval '2 hours' "
                "       THEN current_work ELSE NULL END AS current_work, "
                "  CASE WHEN work_status = 'active' "
                "         AND current_work_at > now() - interval '2 hours' "
                "       THEN current_work_files ELSE NULL END AS current_work_files, "
                "  work_status, "
                "  EXTRACT(EPOCH FROM (now() - current_work_at))::int AS work_age_s, "
                "  local_head_sha, local_behind "
                "FROM fw.claude_instance "
                "WHERE last_seen_at > now() - make_interval(mins => :m) "
                "ORDER BY instance_id"
            ), {"m": within_min}).mappings().all()
            out = [dict(r) for r in rows]
            if exclude_id:
                out = [r for r in out if str(r.get("instance_id")) != str(exclude_id)]
            return out
        finally:
            s.close()
    except Exception:
        # Fallback (sloupce ještě nejsou / chyba) — základní presence bez work.
        try:
            from core.database_data import get_data_session as _gp_ai2
            from sqlalchemy import text as _tp_ai2
            s2 = _gp_ai2()
            try:
                rows = s2.execute(_tp_ai2(
                    "SELECT instance_id, instance_name, hostname, last_action, "
                    "  EXTRACT(EPOCH FROM (now() - last_seen_at))::int AS seen_ago_s "
                    "FROM fw.claude_instance "
                    "WHERE last_seen_at > now() - make_interval(mins => :m) "
                    "ORDER BY instance_id"
                ), {"m": within_min}).mappings().all()
                out = [dict(r) for r in rows]
                if exclude_id:
                    out = [r for r in out if str(r.get("instance_id")) != str(exclude_id)]
                return out
            finally:
                s2.close()
        except Exception:
            return []


@api_router.get("/deploy/preview")
async def deploy_preview(req: Request) -> JSONResponse:
    """Náhled co se nasadí (pro confirm dialog + parent-check pro UI tlačítko).
    Parent-only → 403 schová tlačítko non-parentům. ?fetch=1 udělá git fetch
    (čerstvý origin); bez něj jen lokální porovnání (levné, pro init)."""
    uid = _get_uid(req)
    _require_parent(uid)
    from modules.conversation.application import deployment_service as _dep

    clean, detail = _dep._git_working_tree_clean()
    if not clean:
        return JSONResponse({"ok": True, "deployable": False,
                             "reason": "dirty_working_tree", "detail": detail[:500]})
    if req.query_params.get("fetch") == "1":
        fok, fmsg = _dep._git_fetch_origin()
        if not fok:
            return JSONResponse({"ok": True, "deployable": False,
                                 "reason": "fetch_failed", "detail": fmsg})
    head = _dep._git_current_head_sha()
    origin = _dep._git_origin_head_sha()
    if not head or not origin:
        return JSONResponse({"ok": True, "deployable": False, "reason": "git_sha_failed"})
    if head == origin:
        return JSONResponse({"ok": True, "deployable": False,
                             "reason": "already_up_to_date", "head": head[:12]})
    files, _diff = _dep._git_diff_stat(head, origin)
    msg = _dep._git_commit_message_first_line(origin)
    return JSONResponse({
        "ok": True, "deployable": True,
        "head": head[:12], "target": origin[:12],
        "files_changed": files, "commit_message": (msg or "")[:200],
        # Koordinace 23/24 (Marti 3.6.): kdo je teď aktivní (awareness před deployem)
        "active_instances": _active_instances(),
    })


@api_router.post("/deploy/now")
async def deploy_now(req: Request) -> JSONResponse:
    """Jednoklik deploy: git pull origin main + marker (RESTART-WATCHER restartne
    STRATEGIE-API). Auth: X-Deploy-Token (NB push-to-deploy) NEBO parent session
    (UI tlačítko). Zaznamená proposal pro audit (Phase 42 tabulka)."""
    import os as _os_dn
    from modules.conversation.application import deployment_service as _dep

    token = req.headers.get("X-Deploy-Token")
    env_token = _os_dn.environ.get("STRATEGIE_DEPLOY_TOKEN")
    proposed_by = None
    if token and env_token and token == env_token:
        pass  # token auth (NB) — předautorizováno
    else:
        uid = _get_uid(req)
        _require_parent(uid)
        proposed_by = uid

    try:
        body = await req.json()
    except Exception:
        body = {}
    desc = (str(body.get("description") or "").strip()
            or "Deploy na povel (one-shot)")
    # Atribuce (Marti 2.6.): ktera instance Claude (23/24) deploy spustila
    _inst = str(body.get("instance_id") or "").strip()
    if _inst and _inst != "?":
        desc = "[Claude-%s] %s" % (_inst, desc)
    # Presence board (Marti 3.6.): zaznamenej, ze instance prave deployuje.
    _record_instance_presence(_inst, "deploy", body.get("hostname"))

    # Advisory lock (Marti 3.6.): serializace cloud deploye — dvě instance
    # Claude nesmí pullovat/restartovat současně (kolize git indexu, dvojí
    # restart). pg_try_advisory_lock → když nezískám, druhý deploy běží.
    from core.database_data import get_data_session as _gl_dn
    from sqlalchemy import text as _tl_dn
    _lock_sess = _gl_dn()
    try:
        _got = _lock_sess.execute(
            _tl_dn("SELECT pg_try_advisory_lock(:k)"), {"k": _DEPLOY_LOCK_KEY}
        ).scalar()
        if not _got:
            others = _active_instances(exclude_id=_inst)
            who = ", ".join("Claude-%s" % o["instance_id"] for o in others) or "jiná instance"
            return JSONResponse({
                "ok": False, "reason": "deploy_locked",
                "message": "Jiný deploy právě běží (%s) — zkus za chvíli." % who,
            }, status_code=200)
        try:
            prop = _dep.propose_deployment(
                description=desc, conversation_id=None, proposed_by_user_id=proposed_by,
            )
            if not prop.get("ok"):
                # not deployable (dirty / already up-to-date / fetch fail)
                return JSONResponse(prop, status_code=200)
            pid = prop["proposal_id"]
            result = _dep._execute_deployment(pid)  # git pull + marker
            result.setdefault("proposal_id", pid)
            result["files_changed"] = prop.get("files_changed")
            result["target_sha"] = prop.get("target_sha")
            result["commit_message"] = prop.get("commit_message", "")
            # Mobil push (Marti 6.6.): po úspěšném deployi cinkni rodiči na telefon.
            if result.get("ok"):
                try:
                    _notify_deploy_done(_inst, result)
                except Exception as _ndd:
                    logger.warning("[notify_deploy_done] %s", _ndd)
            return JSONResponse(result)
        finally:
            _lock_sess.execute(_tl_dn("SELECT pg_advisory_unlock(:k)"), {"k": _DEPLOY_LOCK_KEY})
            _lock_sess.commit()
    finally:
        _lock_sess.close()


@api_router.post("/restart-api")
async def restart_api(req: Request) -> JSONResponse:
    """Restart STRATEGIE-API BEZ git pull (recovery — např. zaseklý EUROSOFT
    MCP po restartu EC-SERVER2, TODO #18). Touch marker → RESTART-WATCHER
    restartne službu. Auth: parent session NEBO X-Deploy-Token."""
    import os as _os_ra
    from modules.conversation.application import deployment_service as _dep

    token = req.headers.get("X-Deploy-Token")
    env_token = _os_ra.environ.get("STRATEGIE_DEPLOY_TOKEN")
    actor = "token"
    if token and env_token and token == env_token:
        pass
    else:
        uid = _get_uid(req)
        _require_parent(uid)
        actor = "user_%s" % uid

    ok, info = _dep._touch_restart_marker(0, "restart_%s" % actor)
    if not ok:
        return JSONResponse({"ok": False, "error": info}, status_code=500)
    try:
        logger.warning("[restart_api] manual restart triggered by %s, marker=%s", actor, info)
    except Exception:
        pass
    return JSONResponse({"ok": True, "marker": info, "message": "Restart spuštěn"})


@api_router.post("/diag-sql")
async def diag_sql(req: Request) -> JSONResponse:
    """Claude SQL bridge (1.6.2026, Marti: "máme na to tooly ve STRATEGII"):
    read-only diagnostický SQL proti PRODUKCI přes existující tooly —
    strategie_pg.query_raw (PG) / EUROSOFT MCP strategie_query_raw (MSSQL).
    Běží na cloud APP (dosáhne na cloud SQL i MSSQL). Volá NB watcher
    (forwarder přes HTTPS). Auth: parent session NEBO X-Deploy-Token.
    Read-only guard je v query_raw (SELECT/WITH/EXPLAIN/SHOW)."""
    import os as _os_ds
    token = req.headers.get("X-Deploy-Token")
    env_token = _os_ds.environ.get("STRATEGIE_DEPLOY_TOKEN")
    actor = "token"
    if token and env_token and token == env_token:
        pass
    else:
        uid = _get_uid(req)
        _require_parent(uid)
        actor = "user_%s" % uid

    try:
        body = await req.json()
    except Exception:
        body = {}
    sql = (str(body.get("sql") or "")).strip()
    db = (str(body.get("db") or "pg")).strip().lower()
    # Atribuce (Marti 2.6.): token auth -> ktera instance Claude (23/24)
    _inst = str(body.get("instance_id") or "").strip()
    if actor == "token" and _inst and _inst != "?":
        actor = "Claude-%s" % _inst
    # Presence board (Marti 3.6.): instance prave bezi SQL pres bridge.
    _record_instance_presence(_inst, "sql", body.get("hostname"))
    if not sql:
        return JSONResponse({"ok": False, "error": "sql chybí"}, status_code=400)

    # Krok 2 (1.6.2026): WRITE (ne SELECT/WITH/EXPLAIN/SHOW) → nespouštět,
    # vytvořit pending request → Marti schválí v chatu/ERP banneru.
    import re as _re_ds
    _s_chk = _re_ds.sub(r"--[^\n]*", " ", sql)
    _s_chk = _re_ds.sub(r"/\*.*?\*/", " ", _s_chk, flags=_re_ds.S).strip()
    _is_read = bool(_re_ds.match(r"\s*(SELECT|WITH|EXPLAIN|SHOW)\b", _s_chk, _re_ds.I))
    if not _is_read:
        if db != "pg":
            return JSONResponse({"ok": False,
                                 "error": "Write přes bridge zatím jen pro PG (Krok 2)."})
        from core.database_data import get_data_session as _gw_ds
        from sqlalchemy import text as _tw_ds
        _wds = _gw_ds()
        try:
            rid = _wds.execute(_tw_ds(
                "INSERT INTO fw.claude_write_request (db_target, sql_text, requested_by) "
                "VALUES (:db, :sql, :by) RETURNING id"
            ), {"db": db, "sql": sql, "by": actor}).scalar()
            _wds.commit()
        finally:
            _wds.close()
        # Mobil push (Marti 5.6.): cinkni schvalovateli na telefon (claude_confirm)
        try:
            _push_confirm_to_phone(rid, db, sql, actor)
        except Exception as _pexc:
            logger.warning("[push_confirm_to_phone] %s", _pexc)
        return JSONResponse({"ok": False, "pending": True, "request_id": rid,
                             "message": "Write čeká na schválení Marti (request #%s)." % rid})

    if db == "mssql":
        try:
            from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
            import json as _j_ds
            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                res = {"ok": False, "error": "EUROSOFT MCP nedostupný"}
            else:
                rj = mcp.call_tool_sync(
                    "eurosoft_strategie_query_raw",
                    {"sql": sql, "db_name": "DB_EC"},
                    conversation_id=None,
                )
                res = _j_ds.loads(rj) if isinstance(rj, str) else rj
        except Exception as exc:
            res = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    else:
        try:
            from modules.strategie_pg.application import service as _pg_ds
            res = _pg_ds.query_raw(sql)
        except Exception as exc:
            res = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    # Audit (best-effort) do fw.claude_sql_log
    try:
        from core.database_data import get_data_session as _gds_ds
        from sqlalchemy import text as _t_ds
        _ds = _gds_ds()
        try:
            _ds.execute(_t_ds(
                "INSERT INTO fw.claude_sql_log "
                "(actor, db_target, sql_text, status, row_count, error) "
                "VALUES (:a, :db, :sql, :st, :rc, :err)"
            ), {"a": actor, "db": db, "sql": sql[:8000],
                "st": "ok" if (isinstance(res, dict) and res.get("ok")) else "error",
                "rc": (res.get("count") if isinstance(res, dict) else None),
                "err": (None if (isinstance(res, dict) and res.get("ok"))
                        else str(res.get("error"))[:2000] if isinstance(res, dict) else None)})
            _ds.commit()
        finally:
            _ds.close()
    except Exception:
        pass

    return JSONResponse(res if isinstance(res, dict) else {"ok": False, "error": "neznámý výstup"})


@api_router.get("/diag-write/pending")
async def diag_write_pending(req: Request) -> JSONResponse:
    """Claude SQL bridge Krok 2: pending write requesty pro approval banner.
    Parent-only → 403 schová banner non-parentům."""
    uid = _get_uid(req)
    _require_parent(uid)
    from core.database_data import get_data_session as _gp
    from sqlalchemy import text as _tp
    ds = _gp()
    try:
        # Binding User<->Claude (Marti 3.6.): rodič vidí jen requesty SVÉ Claude
        # instance. requested_by 'Claude-23'/'Claude-24' -> instance_id ->
        # fw.claude_instance.bound_user_id. Neatribuované/legacy -> default (Marti).
        rows = ds.execute(_tp(
            "SELECT w.id, w.db_target, w.sql_text, w.requested_by, w.created_at "
            "FROM fw.claude_write_request w "
            "LEFT JOIN fw.claude_instance ci "
            "  ON ci.instance_id = regexp_replace(w.requested_by, '^Claude-', '') "
            "WHERE w.status='pending' "
            "  AND ( ci.bound_user_id = :uid "
            "        OR (ci.bound_user_id IS NULL AND :uid = :du) ) "
            "ORDER BY w.id ASC"
        ), {"uid": uid, "du": _DEFAULT_APPROVER_UID}).mappings().all()
        return JSONResponse(jsonable_encoder({"ok": True, "requests": [dict(r) for r in rows]}))
    finally:
        ds.close()


def _push_confirm_to_phone(req_id: int, db_target: str, sql: str, actor: str) -> None:
    """Při pending zápisu cinkne schvalovateli na mobil (claude_confirm command).
    Cíl = rodič navázaný na danou Claude instanci (Claude-23→Marti), jinak default
    approver. Appka pollne /commands/pending (á 4 s) a vyvolá oznámení s Povolit/
    Odmítnout → /app/command/result přímo schválí zápis. Marti 5.6."""
    import json as _jp
    import re as _rp
    from core.database_data import get_data_session as _gp
    from sqlalchemy import text as _tp
    ds = _gp()
    try:
        iid = _rp.sub(r"^Claude-", "", (actor or "")).strip()
        uid = None
        if iid:
            uid = ds.execute(_tp("SELECT bound_user_id FROM fw.claude_instance WHERE instance_id=:i"),
                             {"i": iid}).scalar()
        if not uid:
            uid = _DEFAULT_APPROVER_UID
        op = "ZÁPIS"
        m = _rp.match(r"\s*(\w+)", sql or "")
        if m:
            op = m.group(1).upper()
        snippet = " ".join((sql or "").split())[:160]
        title = "Claude čeká na potvrzení (#%s)" % req_id
        message = "%s · %s" % (op, snippet)
        ds.execute(_tp("""
            INSERT INTO fw.mobile_command
              (app_key, target_user_id, command_type, title, message, payload, created_by)
            VALUES ('mobile', :uid, 'claude_confirm', :title, :msg, CAST(:payload AS jsonb), NULL)
        """), {"uid": int(uid), "title": title[:120], "msg": message[:600],
               "payload": _jp.dumps({"write_request_id": int(req_id), "db": db_target})})
        ds.commit()
    finally:
        ds.close()


def _notify_deploy_done(instance_id: str, result: dict) -> None:
    """Po úspěšném deployi cinkne rodiči navázanému na danou Claude instanci
    (Claude-23→Marti, Claude-24→Kristý) na mobil jako claude_msg. Marti 6.6.2026."""
    import re as _rp2
    from core.database_data import get_data_session as _gp2
    from sqlalchemy import text as _tp2
    ds = _gp2()
    try:
        iid = _rp2.sub(r"^Claude-", "", (instance_id or "")).strip()
        uid = None
        if iid and iid != "?":
            uid = ds.execute(_tp2(
                "SELECT bound_user_id FROM fw.claude_instance WHERE instance_id=:i"
            ), {"i": iid}).scalar()
        if not uid:
            uid = _DEFAULT_APPROVER_UID
        sha = (result.get("target_sha") or "")[:7]
        cm = ""
        if result.get("commit_message"):
            cm = str(result["commit_message"]).splitlines()[0][:80]
        who = ("Claude-%s" % iid) if (iid and iid != "?") else "Claude"
        title = "%s — nasazeno ✓" % who
        message = (cm or "Deploy hotový") + ((" (%s)" % sha) if sha else "")
        ds.execute(_tp2("""
            INSERT INTO fw.mobile_command
              (app_key, target_user_id, command_type, title, message, created_by)
            VALUES ('mobile', :uid, 'claude_msg', :title, :msg, NULL)
        """), {"uid": int(uid), "title": title[:120], "msg": message[:600]})
        ds.commit()
    finally:
        ds.close()


def _apply_write_decision(req_id: int, decision: str, uid: int) -> dict:
    """Sdílené jádro schválení/zamítnutí pending claude_write_request — volá ERP
    banner (/diag-write/decide) i mobil (potvrzení z notifikace). approve → spustí
    SQL přes strategie_pg (Marti-AI engine). Binding guard: rozhoduje jen rodič
    navázaný na danou Claude instanci (jinak default approver Marti). Vrací dict;
    klíč 'code' = HTTP status pro chybu."""
    from core.database_data import get_data_session as _gd
    from sqlalchemy import text as _td
    if decision not in ("approve", "reject"):
        return {"ok": False, "error": "decision musí být approve|reject", "code": 400}
    ds = _gd()
    try:
        row = ds.execute(_td(
            "SELECT id, db_target, sql_text, status, requested_by FROM fw.claude_write_request WHERE id=:id"
        ), {"id": req_id}).mappings().first()
        if not row:
            return {"ok": False, "error": "request nenalezen", "code": 404}
        if row["status"] != "pending":
            return {"ok": False, "error": "request už není pending (%s)" % row["status"]}
        appr = ds.execute(_td(
            "SELECT ci.bound_user_id FROM fw.claude_instance ci "
            "WHERE ci.instance_id = regexp_replace(:rb, '^Claude-', '')"
        ), {"rb": row["requested_by"] or ""}).scalar()
        if appr is not None:
            if appr != uid:
                return {"ok": False,
                        "error": "Tento request schvaluje jiný uživatel (jeho Claude instance).",
                        "code": 403}
        elif uid != _DEFAULT_APPROVER_UID:
            return {"ok": False,
                    "error": "Neatribuovaný request schvaluje pouze Marti.", "code": 403}

        if decision == "reject":
            ds.execute(_td("UPDATE fw.claude_write_request SET status='rejected', "
                           "decided_by_user_id=:u, decided_at=now() WHERE id=:id"),
                       {"u": uid, "id": req_id})
            ds.execute(_td("UPDATE fw.mobile_command SET status='done', decided_at=now() "
                           "WHERE command_type='claude_confirm' AND status='pending' "
                           "AND payload->>'write_request_id' = :ridtxt"),
                       {"ridtxt": str(req_id)})
            ds.commit()
            return {"ok": True, "status": "rejected"}

        sql = row["sql_text"]
        err = None
        rc = None
        try:
            from modules.strategie_pg.application.service import get_session as _pgs
            with _pgs() as s:
                r = s.execute(_td(sql))
                try:
                    rc = r.rowcount
                except Exception:
                    rc = None
                s.commit()
        except Exception as exc:
            err = "%s: %s" % (type(exc).__name__, exc)

        if err:
            ds.execute(_td("UPDATE fw.claude_write_request SET status='error', error=:e, "
                           "decided_by_user_id=:u, decided_at=now() WHERE id=:id"),
                       {"e": err[:4000], "u": uid, "id": req_id})
            ds.commit()
            return {"ok": False, "status": "error", "error": err}

        result_text = "OK · %s řádků dotčeno" % (rc if rc is not None else "?")
        ds.execute(_td("UPDATE fw.claude_write_request SET status='done', row_count=:rc, "
                       "result_text=:rt, decided_by_user_id=:u, decided_at=now() WHERE id=:id"),
                   {"rc": rc, "rt": result_text, "u": uid, "id": req_id})
        ds.execute(_td("UPDATE fw.mobile_command SET status='done', decided_at=now() "
                       "WHERE command_type='claude_confirm' AND status='pending' "
                       "AND payload->>'write_request_id' = :ridtxt"),
                   {"ridtxt": str(req_id)})
        ds.commit()
        return {"ok": True, "status": "done", "row_count": rc, "result_text": result_text}
    finally:
        ds.close()


@api_router.post("/diag-write/{req_id}/decide")
async def diag_write_decide(req_id: int, req: Request) -> JSONResponse:
    """Marti approve/reject pending write z ERP banneru. Parent-only."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        body = await req.json()
    except Exception:
        body = {}
    decision = (str(body.get("decision") or "")).strip().lower()
    res = _apply_write_decision(req_id, decision, uid)
    code = res.pop("code", None) if isinstance(res, dict) else None
    return JSONResponse(res, status_code=int(code or 200))


@api_router.get("/diag-write/{req_id}/status")
async def diag_write_status(req_id: int, req: Request) -> JSONResponse:
    """Watcher polluje (X-Deploy-Token) NEBO parent. Vrací stav + výsledek."""
    import os as _os_ws
    token = req.headers.get("X-Deploy-Token")
    env_token = _os_ws.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env_token and token == env_token):
        uid = _get_uid(req)
        _require_parent(uid)
    from core.database_data import get_data_session as _gws
    from sqlalchemy import text as _tws
    ds = _gws()
    try:
        row = ds.execute(_tws(
            "SELECT status, row_count, result_text, error "
            "FROM fw.claude_write_request WHERE id=:id"
        ), {"id": req_id}).mappings().first()
        if not row:
            return JSONResponse({"ok": False, "error": "request nenalezen"}, status_code=404)
        return JSONResponse(jsonable_encoder({"ok": True, **dict(row)}))
    finally:
        ds.close()


# ── Presence board dvou instancí Claude (Marti 3.6.2026) ────────────────────
@api_router.post("/instance/heartbeat")
async def instance_heartbeat(req: Request) -> JSONResponse:
    """Watcher periodicky (~30 s) hlásí, že žije. Auth: X-Deploy-Token.
    Upsert fw.claude_instance + vrátí ostatní aktivní instance (awareness)."""
    import os as _os_hb
    token = req.headers.get("X-Deploy-Token")
    env_token = _os_hb.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env_token and token == env_token):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=403)
    try:
        body = await req.json()
    except Exception:
        body = {}
    iid = str(body.get("instance_id") or "").strip()
    if not iid or iid == "?":
        return JSONResponse({"ok": False, "error": "instance_id chybí"}, status_code=400)
    _record_instance_presence(iid, str(body.get("action") or "heartbeat"), body.get("hostname"))
    # Work-lock + freshness (Marti 3.6.): ulož co instance staví + stav lokálu.
    _update_instance_work(iid, body)
    # Ops framework (Marti 3.6.): watcher si v odpovedi vyzvedne pending ops
    # pro svou instanci (napr. restart_watcher) — oznaci je ack, provede, reportne.
    ops = _ops_pending_for_instance(iid)
    return JSONResponse(jsonable_encoder({
        "ok": True, "others": _active_instances(exclude_id=iid), "ops": ops,
    }))


@api_router.get("/instance/active")
async def instance_active(req: Request) -> JSONResponse:
    """Kdo je online (heartbeat < 3 min). Parent session NEBO X-Deploy-Token."""
    import os as _os_ia
    token = req.headers.get("X-Deploy-Token")
    env_token = _os_ia.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env_token and token == env_token):
        uid = _get_uid(req)
        _require_parent(uid)
    return JSONResponse(jsonable_encoder({"ok": True, "instances": _active_instances()}))


# ── Ops framework (Marti 3.6.2026): eliminovat ručně spouštěný PowerShell ────
# Whitelist pojmenovaných akcí (žádný volný příkaz). Parent + confirm + audit
# do fw.ops_request. Cloud akce běží inline; remote (instance/EC-SERVER2) jdou
# do fronty, agent (watcher) si je vyzvedne v heartbeatu.
_OPS_ACTIONS = {
    "restart_watcher_23": {
        "label": "Restartovat watcher Claude-23 (Marti NB)",
        "target": "instance:23", "remote": True, "op": "restart_self",
    },
    "restart_watcher_24": {
        "label": "Restartovat watcher Claude-24 (Kristy)",
        "target": "instance:24", "remote": True, "op": "restart_self",
    },
    "restart_api": {
        "label": "Restartovat cloud API (recovery)",
        "target": "cloud", "remote": False,
    },
    "publish_app_mobile": {
        "label": "Nahrát mobilní APK z buildu (NB → server)",
        "target": "instance:23", "remote": True, "op": "publish_app_mobile",
    },
    "build_publish_app_mobile": {
        "label": "Postavit APK (gradlew) + nahrát (NB → server, verze +1)",
        "target": "instance:23", "remote": True, "op": "build_publish_app_mobile",
    },
}


def _ops_pending_for_instance(iid: str) -> list:
    """Vrátí pending ops pro instanci a označí je 'ack' (picked_at). Watcher je
    provede + reportne přes /ops/{id}/result. Best-effort."""
    target = "instance:%s" % iid
    try:
        from core.database_data import get_data_session as _gp_op
        from sqlalchemy import text as _tp_op
        s = _gp_op()
        try:
            rows = s.execute(_tp_op(
                "SELECT id, action_key, params FROM fw.ops_request "
                "WHERE target = :t AND status = 'pending' ORDER BY id ASC"
            ), {"t": target}).mappings().all()
            out = [dict(r) for r in rows]
            if out:
                ids = [r["id"] for r in out]
                s.execute(_tp_op(
                    "UPDATE fw.ops_request SET status='ack', picked_at=now() "
                    "WHERE id = ANY(:ids)"
                ), {"ids": ids})
                s.commit()
            # přidej op-handler key z registru (watcher ví, co dělat)
            for r in out:
                meta = _OPS_ACTIONS.get(r["action_key"], {})
                r["op"] = meta.get("op")
            return out
        finally:
            s.close()
    except Exception:
        return []


@api_router.post("/ops/request")
async def ops_request(req: Request) -> JSONResponse:
    """Parent požádá o pojmenovanou ops akci (z whitelistu). Cloud akce běží
    hned; remote jdou do fronty pro agenta. Vše do fw.ops_request (audit)."""
    uid = _get_uid(req)
    _require_parent(uid)
    try:
        body = await req.json()
    except Exception:
        body = {}
    action_key = str(body.get("action_key") or "").strip()
    meta = _OPS_ACTIONS.get(action_key)
    if not meta:
        return JSONResponse({"ok": False, "error": "neznámá akce (mimo whitelist)"}, status_code=400)

    # jméno žadatele pro audit
    name = None
    try:
        from core.database_core import get_core_session as _gcs_op
        from modules.core.infrastructure.models_core import User as _U_op
        _cs = _gcs_op()
        try:
            u = _cs.query(_U_op).filter_by(id=uid).first()
            if u:
                name = (u.short_name or getattr(u, "first_name", None) or ("#%s" % uid))
        finally:
            _cs.close()
    except Exception:
        pass

    from core.database_data import get_data_session as _gp_or
    from sqlalchemy import text as _tp_or
    s = _gp_or()
    try:
        rid = s.execute(_tp_or(
            "INSERT INTO fw.ops_request (action_key, target, status, requested_by_user_id, requested_by_name) "
            "VALUES (:ak, :tg, 'pending', :uid, :nm) RETURNING id"
        ), {"ak": action_key, "tg": meta["target"], "uid": uid, "nm": name}).scalar()
        s.commit()
    finally:
        s.close()

    # Cloud akce → spustit hned inline.
    if not meta.get("remote"):
        result = _ops_execute_cloud(action_key, rid, uid)
        return JSONResponse(jsonable_encoder({"ok": True, "request_id": rid,
                                              "remote": False, **result}))
    # Remote akce → ve frontě, agent si ji vyzvedne v heartbeatu (do ~30 s).
    return JSONResponse({"ok": True, "request_id": rid, "remote": True,
                         "message": "Příkaz zařazen — %s provede do ~30 s." % meta["target"]})


def _ops_execute_cloud(action_key: str, rid, uid) -> dict:
    """Spustí cloud-lokální ops akci (běží na cloud APP). Zatím: restart_api
    přes RESTART-WATCHER marker. Aktualizuje fw.ops_request."""
    from core.database_data import get_data_session as _gp_ec
    from sqlalchemy import text as _tp_ec
    status = "done"
    result = ""
    try:
        if action_key == "restart_api":
            from modules.conversation.application import deployment_service as _dep_ec
            ok, info = _dep_ec._touch_restart_marker(0, "ops_restart_api_user_%s" % uid)
            status = "done" if ok else "error"
            result = "marker: %s" % info
        else:
            status, result = "error", "cloud handler chybí pro %s" % action_key
    except Exception as exc:
        status, result = "error", "%s: %s" % (type(exc).__name__, exc)
    try:
        s = _gp_ec()
        try:
            s.execute(_tp_ec("UPDATE fw.ops_request SET status=:st, result=:r, finished_at=now() WHERE id=:id"),
                      {"st": status, "r": result[:4000], "id": rid})
            s.commit()
        finally:
            s.close()
    except Exception:
        pass
    return {"status": status, "result": result}


@api_router.post("/ops/{req_id}/result")
async def ops_result(req_id: int, req: Request) -> JSONResponse:
    """Agent (watcher) reportuje výsledek ops akce. Auth: X-Deploy-Token."""
    import os as _os_orr
    token = req.headers.get("X-Deploy-Token")
    env_token = _os_orr.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not (token and env_token and token == env_token):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=403)
    try:
        body = await req.json()
    except Exception:
        body = {}
    st = (str(body.get("status") or "done")).strip()
    if st not in ("done", "error", "ack"):
        st = "done"
    result = str(body.get("result") or "")[:4000]
    from core.database_data import get_data_session as _gp_orr
    from sqlalchemy import text as _tp_orr
    s = _gp_orr()
    try:
        s.execute(_tp_orr(
            "UPDATE fw.ops_request SET status=:st, result=:r, finished_at=now() WHERE id=:id"
        ), {"st": st, "r": result, "id": req_id})
        s.commit()
    finally:
        s.close()
    return JSONResponse({"ok": True})


@api_router.get("/ops/actions")
async def ops_actions(req: Request) -> JSONResponse:
    """Whitelist dostupných ops akcí pro UI (parent-only)."""
    uid = _get_uid(req)
    _require_parent(uid)
    items = [{"action_key": k, "label": v["label"], "target": v["target"]}
             for k, v in _OPS_ACTIONS.items()]
    return JSONResponse({"ok": True, "actions": items})


@api_router.get("/ops/log")
async def ops_log(req: Request) -> JSONResponse:
    """Audit posledních ops akcí (parent-only)."""
    uid = _get_uid(req)
    _require_parent(uid)
    from core.database_data import get_data_session as _gp_ol
    from sqlalchemy import text as _tp_ol
    s = _gp_ol()
    try:
        rows = s.execute(_tp_ol(
            "SELECT id, action_key, target, status, requested_by_name, "
            "  created_at, finished_at, result "
            "FROM fw.ops_request ORDER BY id DESC LIMIT 30"
        )).mappings().all()
        return JSONResponse(jsonable_encoder({"ok": True, "log": [dict(r) for r in rows]}))
    finally:
        s.close()


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
    _require_data_write_access(uid, entity_type)

    body = await req.json()
    field_changes = body.get("field_changes") or {}
    expected_updated_at = body.get("expected_updated_at")

    if not isinstance(field_changes, dict) or not field_changes:
        return JSONResponse(
            {"ok": False, "error": "field_changes musi byt non-empty dict"},
            status_code=400,
        )
    # Phase 38.4 Krok 5.R-D+3 (18.5.2026, Marti's "FW save preprocessor"
    # doctrine z Centrály 1 19yr expertise): drop hard requirement na
    # expected_updated_at. Optimistic lock check (line ~4715) už správně
    # skipne pokud current_updated_at je NULL (= never touched row).
    # Client může neposlat expected_updated_at → service mode pro designery
    # bez pojistek (Marti's 17.5. večer "bez pojistek zatim").
    #
    # Pokud client posílá + DB má hodnotu → optimistic lock proběhne.
    # Pokud client neposílá → server-side auto-fill updated_at = NOW() v
    # patch 2 níže.

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
    # Phase 38.4 Krok 5.N-2 v2 (22.5.2026 vecer, Marti's "NULL = all editable,
    # trust frontend"): resolver vrací select_columns=None pro DB-driven
    # entity configs (Excel mode + dynamic comp_grid columns). Legacy
    # _FW_FORM_CORE_REGISTRY a _FW_FORM_ENTITY_MAP entries vrací explicit list.
    #
    # 23.5.2026 hotfix Marti's smoke "Save 0 OK, 2 FAIL" — fw.diag_log core_id=44
    # PATCH 500 bare text → set(None) TypeError → unhandled exception.
    _raw_cols = entity_config.get("select_columns")
    allowed_columns = set(_raw_cols) if _raw_cols is not None else None  # None = no whitelist

    # Phase 38.4 Krok 5.R-D+3 extend (18.5.2026, Marti's "neni jej treba
    # komplikovat"): universal optional fields — pokud v target table
    # existuji, used/auto-filled; pokud ne, silent drop. Marti's FW save
    # preprocessor doctrine (Centrála 1 19yr) napříč všemi entity_types.
    #
    # Bezpečnost: konstants definované server-side (no password_hash leak).
    # Validation v allowed_columns expansion zachovává defense in depth.
    UNIVERSAL_OPTIONAL_FIELDS = frozenset({
        "description_user",   # User-edited memo (Krok 14b+21 doctrine)
        "description_system", # System-edited memo (DESIGN mode only)
        "updated_at",         # Auto-fill NOW() (5.R-D+3 doctrine)
        "version",            # Optimistic lock alt
    })

    # Validate field_changes — jen sloupce v allowed list (defense in depth proti
    # ad-hoc UPDATE např. password_hash). id_column zakazat (immutable).
    # Universal fields se kontrolují separátně po current_row load.
    if allowed_columns is not None:
        # Legacy whitelist mode (explicit select_columns list)
        invalid_fields = [
            f for f in field_changes
            if (f not in allowed_columns and f not in UNIVERSAL_OPTIONAL_FIELDS)
                or f == id_column
        ]
        if invalid_fields:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Sloupce {invalid_fields} nejsou povolene v PATCH "
                        f"pro entity '{entity_type}'. Allowed: {sorted(allowed_columns - {id_column})} "
                        f"+ universal: {sorted(UNIVERSAL_OPTIONAL_FIELDS)}"
                    ),
                },
                status_code=400,
            )
    else:
        # NULL whitelist mode (Marti's "trust frontend, DB-driven" 22.5. doctrine).
        # Server safety net: blokovat jen id_column (immutable). Žádné jiné
        # restriction — frontend pošle field_changes obsahující jen sloupce
        # z visible/editable columns v fw.comp_grid.layout_json.
        # Audit pro forensic: log_event(level='info') s field_changes keys.
        invalid_fields = [f for f in field_changes if f == id_column]
        if invalid_fields:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"ID column '{id_column}' je immutable — nelze PATCH. "
                        f"Field changes: {list(field_changes.keys())}"
                    ),
                },
                status_code=400,
            )

    # Phase Audit Actor (28.5.2026 vecer pozde, Marti's "Krok C audit
    # columns autofill univerzalne"): sjednoceno pres resolve_audit_actor.
    # Pro PG branch potrebujeme pg_text (users.short_name). Pro MSSQL
    # branch (nize) navic mssql_text (user_tenants.db_login per tenant).
    #
    # uid IS NULL → fallback na STRATEGIE_USER_ID=3 (Marti's "STRATEGIE
    # = normalni user", system actor convention).
    from modules.auth.application.audit_actor import (
        resolve_audit_actor as _audit_resolve,
        resolve_tenant_id_from_dc_code as _audit_tenant_from_dc,
    )
    # Tmp: caller_display naplnen dale podle target db_kind. Pro PG branch
    # (default fallthrough) = audit_pg["pg_text"]. Pro MSSQL branch
    # (nize, early return) audit resolve znovu s target_db_kind="mssql".
    audit_pg = None
    try:
        # Need fresh ds for audit lookup (data_db session). _gds_patch is
        # imported above (line ~3463).
        _ds_audit = _gds_patch()
        try:
            audit_pg = _audit_resolve(
                uid=uid,
                target_tenant_id=None,
                target_db_kind="pg",
                ds=_ds_audit,
            )
        finally:
            _ds_audit.close()
        caller_display = audit_pg["pg_text"]
    except ValueError as _audit_exc:
        # Fail visible — pokud audit resolver raise, return 500
        logger.exception(f"design_patch_entity audit resolve failed: {_audit_exc}")
        return JSONResponse(
            {"ok": False, "error": f"Audit actor resolve failed: {_audit_exc}"},
            status_code=500,
        )

    # ── Krok 5-A v3 (28.5.2026 vecer): MSSQL save dispatch ───────────
    # Marti's "(α) MCP retry via HTTP loopback" doctrine 28.5.2026 ráno.
    # Mirror pattern z fw_form_load_by_id (line ~2820). Optimistic lock
    # OFF (Marti's "becko by si komplikovalo progres"). Audit user-facing
    # fields only (Marti's "zatim a" — no auto-fill DatZmeny/Zmenil).
    # Cross-DB audit do PG public.activity_log zustava.
    _db_type_patch = (entity_config.get("db_type") or "pg").lower()
    _dc_code_patch = entity_config.get("dc_code") or ""
    if _db_type_patch == "mssql":
        import json as _json_patch_mssql
        try:
            from modules.conversation.application.eurosoft_mcp_client import (
                get_eurosoft_mcp_client,
            )
            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                logger.warning(
                    "[design_patch_entity] MCP client None (eurosoft_mcp_enabled=False?) — MSSQL save abort"
                )
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "MCP client neni dostupny (eurosoft_mcp_enabled=False?). "
                            "MSSQL save flow vyzaduje MCP."
                        ),
                    },
                    status_code=503,
                )

            # dc_code = 'eurosoft_db_ec' → MCP db_name = 'DB_EC' (parity s form_load)
            mcp_db_name = "DB_EC"
            if _dc_code_patch and _dc_code_patch.lower().startswith("eurosoft_"):
                mcp_db_name = _dc_code_patch[len("eurosoft_"):].upper()

            # ── Phase Audit Actor (Fáze E, 28.5.2026 vecer pozde): ─────
            # MSSQL audit columns autofill — Zmenil + DatZmeny per
            # Centrala 1 idiom. Pre-introspect target columns (cached),
            # inject jen pokud column existuje (defense in depth proti
            # "column does not exist" v UPDATE).
            #
            # Resolve audit actor s target_db_kind="mssql" → mssql_text =
            # user_tenants.db_login per (uid, tenant_id). NULL db_login
            # → ValueError = fail visible (Marti's "kdyz nevyplneno, tak
            # chyba zatim" 28.5.).
            from modules.conversation.application.eurosoft_mcp_client import (
                get_mssql_columns_cached as _get_mssql_cols,
            )
            from datetime import datetime as _dt_audit

            _audit_tenant_id = _audit_tenant_from_dc(_dc_code_patch)
            if not _audit_tenant_id:
                logger.warning(
                    "[design_patch_entity] MSSQL audit: tenant_id neresolved "
                    "z dc_code=%r — skip audit autofill (proceeds bez Zmenil/DatZmeny)",
                    _dc_code_patch,
                )

            audit_mssql_text = None
            if _audit_tenant_id:
                try:
                    _ds_audit_mssql = _gds_patch()
                    try:
                        audit_mssql = _audit_resolve(
                            uid=uid,
                            target_tenant_id=_audit_tenant_id,
                            target_db_kind="mssql",
                            ds=_ds_audit_mssql,
                        )
                    finally:
                        _ds_audit_mssql.close()
                    audit_mssql_text = audit_mssql["mssql_text"]
                except ValueError as _audit_mssql_exc:
                    # Fail visible — db_login chybi pro tenant
                    logger.exception(
                        f"design_patch_entity MSSQL audit resolve failed: {_audit_mssql_exc}"
                    )
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": f"MSSQL audit actor resolve failed: {_audit_mssql_exc}",
                        },
                        status_code=500,
                    )

            # Pre-introspect target columns (cached)
            _mssql_cols = _get_mssql_cols(mcp_db_name, schema_name, table_name)

            # ── Krok 5-B Fix #15 (30.5.2026) + Krok 5.Z (31.5.2026):
            # fieldKey → DB column + cilova tabulka z fw.comp_def.layout.
            # Krok 5.Z (31.5.2026, Marti: "identifikace fieldu absolutni —
            # vicero tabulek/databazi/serveru"): per-field layout.save binding.
            # {schema, table, column, row_key{col:'@id'|literal}, readonly}.
            # Fieldy bez save -> base entita (schema_name/table_name, WHERE
            # id_column=row_id) + column_name fallback (zpetna kompat).
            _field_layout_map = {}   # field name -> layout dict
            _resolve_core_id = entity_config.get("core_id")
            if _resolve_core_id:
                try:
                    _ds_resolve = _gds_patch()
                    try:
                        _rows_resolve = _ds_resolve.execute(
                            _sql_text_patch(
                                "SELECT name, layout FROM fw.comp_def "
                                "WHERE core_id = :cid AND parent_comp_def_id IS NOT NULL "
                                "AND is_active = true"
                            ),
                            {"cid": _resolve_core_id},
                        ).mappings().all()
                        for _r in _rows_resolve:
                            _field_layout_map[_r["name"]] = _r["layout"] or {}
                    finally:
                        _ds_resolve.close()
                except Exception as _resolve_exc:
                    logger.warning(
                        "[design_patch_entity] MSSQL layout resolve failed "
                        "(core_id=%s): %r — fallback base entita",
                        _resolve_core_id, _resolve_exc,
                    )
                    _field_layout_map = {}

            def _resolve_rk(_row_key, _rid):
                """row_key tokeny -> hodnoty (@id -> row_id, literaly as-is)."""
                _o = {}
                for _k, _v in (_row_key or {}).items():
                    _o[_k] = int(_rid) if _v == "@id" else _v
                return _o

            # Seskup dirty fieldy podle absolutni souradnice (schema,table,row_key).
            # group value: {schema, table, where(resolved), data{col:val}}
            _save_groups = {}
            _skipped_fields = []
            for _fk_name, _fk_val in field_changes.items():
                _lay = _field_layout_map.get(_fk_name) or {}
                _save = _lay.get("save") if isinstance(_lay, dict) else None
                if isinstance(_save, dict) and _save.get("readonly"):
                    _skipped_fields.append((_fk_name, "readonly"))
                    continue
                if isinstance(_save, dict) and _save.get("table"):
                    _g_schema = _save.get("schema") or schema_name
                    _g_table = _save["table"]
                    _g_col = _save.get("column") or _fk_name
                    _g_rk = _resolve_rk(_save.get("row_key"), row_id)
                    if not _g_rk:
                        # bez klice = NIKDY neukladat (jinak UPDATE bez WHERE!)
                        _skipped_fields.append((_fk_name, "no_row_key"))
                        continue
                else:
                    # base entita fallback (puvodni chovani + column_name)
                    _g_schema = schema_name
                    _g_table = table_name
                    _g_col = (
                        _lay.get("column_name") if isinstance(_lay, dict) else None
                    ) or _fk_name
                    _g_rk = {id_column: int(row_id)}
                _gkey = (_g_schema, _g_table, tuple(sorted(_g_rk.items())))
                _grp = _save_groups.setdefault(
                    _gkey,
                    {"schema": _g_schema, "table": _g_table, "where": _g_rk, "data": {}},
                )
                _grp["data"][_g_col] = _fk_val

            # Audit autofill (Zmenil/DatZmeny) jen do base-entita skupiny,
            # pokud existuje a sloupce existuji.
            _base_gkey = (
                schema_name, table_name,
                tuple(sorted({id_column: int(row_id)}.items())),
            )
            if audit_mssql_text and _mssql_cols and _base_gkey in _save_groups:
                if "Zmenil" in _mssql_cols:
                    _save_groups[_base_gkey]["data"]["Zmenil"] = audit_mssql_text
                if "DatZmeny" in _mssql_cols:
                    _save_groups[_base_gkey]["data"]["DatZmeny"] = (
                        _dt_audit.now().isoformat(timespec="seconds")
                    )

            if _skipped_fields:
                logger.info(
                    "[design_patch_entity] MSSQL skip fields (readonly/no-key): %s",
                    _skipped_fields,
                )
            if not _save_groups:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Zadne ukladatelne fieldy — vse read-only nebo bez "
                            "row_key. Zkontroluj layout.save bindingy."
                        ),
                    },
                    status_code=422,
                )
            logger.info(
                "[design_patch_entity] MSSQL save groups: %s",
                [(g["schema"], g["table"], g["where"], sorted(g["data"].keys()))
                 for g in _save_groups.values()],
            )

            # UPDATE per skupina (multi-table) via MCP. Kazda skupina =
            # jedna tabulka + svuj composite WHERE (row_key). Krok 5.Z.
            # POZN: skupiny commitují nezavisle (MCP per-call commit) — neni
            # cross-table atomicita. Pri chybe vraci 500/422 (fail visible);
            # base skupina uz mohla projit (partial save) — zatim akceptovatelne.
            affected = 0
            for _grp in _save_groups.values():
                if not _grp["data"]:
                    continue
                upd_json = mcp.call_tool_sync(
                    "eurosoft_strategie_update_row",
                    {
                        "schema": _grp["schema"],
                        "table": _grp["table"],
                        "data": _grp["data"],
                        "where": _grp["where"],
                        "db_name": mcp_db_name,
                    },
                    conversation_id=None,
                )
                upd = (
                    _json_patch_mssql.loads(upd_json)
                    if isinstance(upd_json, str) else upd_json
                )
                if not (isinstance(upd, dict) and upd.get("ok")):
                    err_msg = (
                        (upd or {}).get("error")
                        if isinstance(upd, dict) else str(upd)
                    )
                    logger.warning(
                        "[design_patch_entity] MSSQL group update failed %s.%s where=%s db=%s: %r",
                        _grp["schema"], _grp["table"], _grp["where"], mcp_db_name, upd,
                    )
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                f"MSSQL UPDATE failed "
                                f"({_grp['schema']}.{_grp['table']}): {err_msg}"
                            ),
                        },
                        status_code=500,
                    )
                _grp_aff = upd.get("affected", 0)
                affected += _grp_aff
                logger.info(
                    "[design_patch_entity] MSSQL group updated %s.%s where=%s "
                    "affected=%s cols=%s",
                    _grp["schema"], _grp["table"], _grp["where"],
                    _grp_aff, sorted(_grp["data"].keys()),
                )
                # Silent-success detection per skupina (Marti-AI 9.5. "bezpecnost
                # pres probuzeni, ne pres ticho"). affected=0 = related radek
                # neexistuje / sloupec drop / hodnoty stejne.
                if _grp_aff == 0:
                    logger.warning(
                        "[design_patch_entity] MSSQL group affected=0 %s.%s where=%s cols=%s",
                        _grp["schema"], _grp["table"], _grp["where"],
                        sorted(_grp["data"].keys()),
                    )
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                f"UPDATE {_grp['schema']}.{_grp['table']} "
                                f"WHERE {_grp['where']} probehl ale 0 rows affected. "
                                f"Mozne priciny: (1) cilovy radek s timto klicem "
                                f"neexistuje (napr. souvisejici Akce IDAkce=16 pro "
                                f"tento kontakt zatim neni zalozena); (2) sloupce "
                                f"{sorted(_grp['data'].keys())} neexistuji v tabulce; "
                                f"(3) hodnoty se nezmenily oproti DB."
                            ),
                        },
                        status_code=422,
                    )

            # Re-fetch updated row pro response (frontend needs fresh values)
            fetched_row = None
            try:
                fetch_json = mcp.call_tool_sync(
                    "eurosoft_strategie_get_row",
                    {
                        "schema": schema_name,
                        "table": table_name,
                        "id": int(row_id),
                        "db_name": mcp_db_name,
                    },
                    conversation_id=None,
                )
                fetched = (
                    _json_patch_mssql.loads(fetch_json)
                    if isinstance(fetch_json, str) else fetch_json
                )
                if isinstance(fetched, dict) and fetched.get("ok"):
                    fetched_row = fetched.get("row")
            except Exception as _fe:
                logger.warning(
                    "[design_patch_entity] MSSQL post-update re-fetch failed: %s",
                    _fe,
                )

            # Audit log INSERT do PG public.activity_log (cross-DB OK)
            try:
                ds_audit = _gds_patch()
                try:
                    ds_audit.execute(_sql_text_patch("""
                        INSERT INTO public.activity_log
                          (user_id, persona_id, category, actor,
                           summary, change_source, ts)
                        VALUES
                          (:uid, NULL, 'design_save', 'user',
                           :summary, 'ui', NOW())
                    """), {
                        "uid": uid,
                        "summary": (
                            f"PATCH (MSSQL) {schema_name}.{table_name} id={row_id} "
                            f"db={mcp_db_name} by {caller_display}: "
                            f"changed fields = {sorted(field_changes.keys())}"
                        ),
                    })
                    ds_audit.commit()
                finally:
                    ds_audit.close()
            except Exception as _act_e:
                logger.warning(
                    "[design_patch_entity] MSSQL audit INSERT failed (non-fatal): %s",
                    _act_e,
                )

            return JSONResponse(jsonable_encoder({
                "ok": True,
                "entity_type": entity_type,
                "row_id": row_id,
                "updated_at": None,  # MSSQL DB_EC dbo nemá updated_at v naší convention
                "updated_by_id": uid,
                "updated_by_text": caller_display,
                "field_changes_applied": list(field_changes.keys()),
                "row": fetched_row or {},
                "_db_type": "mssql",
                "_db_name": mcp_db_name,
            }))
        except Exception as exc:
            logger.exception(
                "[design_patch_entity] MSSQL MCP dispatch failed for %s.%s row=%s: %s",
                schema_name, table_name, row_id, exc,
            )
            return JSONResponse(
                {"ok": False, "error": f"MSSQL PATCH dispatch failed: {exc}"},
                status_code=500,
            )
    # ── End MSSQL dispatch — PG path continues below ─────────────────

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
        # Krok 5-B Fix #13 (29.5.2026 vecer): skip check kdyz klient
        # neposlal expected_updated_at (service mode, designer fast path).
        # Marti's "je to jen update fieldu is_active a parent" doctrine.
        current_updated_at = current_row.get("updated_at")
        if current_updated_at is not None and expected_updated_at:
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

        # Phase 38.4 Krok 5.R-D+3 (18.5.2026, Marti's "FW save preprocessor"
        # doctrine): introspect target table columns z current_row.keys()
        # (SELECT * vrátil all). Auto-fill standardized fields:
        #   - updated_at = NOW() ISO (pokud column exists, ne uz v field_changes)
        # Centrála 1 19yr universal pattern — napříč všemi FW save endpointy.
        # Plus optional pojistka pro field_changes mutace post-validation.
        _table_cols = set(current_row.keys()) if current_row else set()
        if "updated_at" in _table_cols and "updated_at" not in field_changes:
            field_changes["updated_at"] = _dt_patch.now().astimezone().isoformat()

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
            # Phase 38.4 Krok 5.N-2 hotfix #2 (23.5.2026, Marti's smoke
            # Excel mode fw.diag_log): defensive audit injection. fw.diag_log
            # (append-only audit per Fix N doctrine 21.5.) nemá updated_by_*
            # columns — má jen created_by_* + resolved_by_*. Inject jen pokud
            # target table sloupec MÁ (z _table_cols introspect SELECT * vrátil).
            if "updated_by_id" in _table_cols:
                upd_values["updated_by_id"] = uid
            if "updated_by_text" in _table_cols:
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

            # Phase 38.4 Krok 5.R-C+5.2 hotfix (18.5.2026 vecer): drop
            # explicit "updated_at = NOW()" — FW save preprocessor
            # (line 4775-4776) uz pridava updated_at do field_changes s ISO
            # timestamp, takze loop (line 4831-4833) ho builduje. Bez drop
            # PostgreSQL: SyntaxError multiple assignments to same column.

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
# Phase 38.4 Krok 5.S Fáze 4 (22.5.2026 vecer, Marti's "od lesa" toolbar):
# DELETE entity endpoint — analog design_patch_entity ale DELETE flow.
# Reuse _resolve_entity_config_for_core (5.N-2 v2 SQL parse resolver).
# Marti's Q7=A "drz jednoduchost" — hard delete bez soft delete branch.
# ────────────────────────────────────────────────────────────────────

@api_router.delete("/design/{core_id:int}/{row_id:int}")
async def design_delete_entity(core_id: int, row_id: int, req: Request) -> JSONResponse:
    """Hard DELETE row z entity table.

    URL: DELETE /api/v1/erp/design/{core_id}/{row_id}

    Phase 38.4 Krok H+5 (26.5.2026): :int path converter — Starlette
    matchuje jen kdyz oba segmenty jsou integers. Zabranuje route
    collision s /design/comp-def/{comp_def_id} + /design/db-connection/...
    + /design/fw-data-source/... (Pydantic 422 fix).

    Resolves target table via _resolve_entity_config_for_core (DB-first
    z 5.N-2 v2 SQL parse, fallback _FW_FORM_CORE_REGISTRY pro user/core).
    Returns:
        200: {ok, deleted_rows} — success (idempotent: 0 rows pokud row neexistuje)
        404: core_id not resolvable to entity_config
        500: DB error
    """
    from core.database_data import get_data_session as _gds_del
    from sqlalchemy import text as _sql_text_del

    uid = _get_uid(req)
    # Phase D: core_id je numeric → business data → _require_data_write_access
    # dovolí členům (str(core_id).isdigit()=True), rodičům vše.
    _require_data_write_access(uid, str(core_id))

    # Resolve entity config (schema, table, id_column) via 5.N-2 v2 chain
    config = _resolve_entity_config_for_core(core_id)
    if not config:
        return JSONResponse(
            {"ok": False, "error": f"Entity '{core_id}' nelze resolvovat (chybi data_source/data_set chain)"},
            status_code=404,
        )

    schema = config["schema"]
    table = config["table"]
    id_column = config.get("id_column", "id")

    ds = _gds_del()
    try:
        # Krok 5.W diag #3 (23.5.2026): connection identity check BEFORE DELETE.
        # Marti's paradox: manual DBeaver DELETE+COMMIT persistuje, backend ne.
        # Hypotéza: ds connects k JINÉ DB nebo serveru než DBeaver.
        ds_conn_info = ds.execute(_sql_text_del(
            "SELECT pg_backend_pid() AS pid, current_database() AS db, "
            "current_user AS pg_user, session_user AS sess_user, "
            "inet_server_addr()::text AS host, inet_server_port() AS port"
        )).mappings().first()

        # Direct DELETE — _require_parent gate sufficient authz (Marti's "rodice maji full trust")
        result = ds.execute(_sql_text_del(
            f'DELETE FROM "{schema}"."{table}" WHERE "{id_column}" = :rid'
        ), {"rid": row_id})
        deleted_rows = result.rowcount

        # Krok 5.W diag (23.5.2026): immediate same-session re-check PŘED commit.
        # Pokud DELETE skutečně proběhl, count by mělo být 0 i v této session.
        # Marti's paradox: rowcount=1, ale row stále v DB.
        check_pre_commit = ds.execute(_sql_text_del(
            f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{id_column}" = :rid'
        ), {"rid": row_id}).scalar()

        # Krok 5.W diag #3: tx state check PŘED commit
        ds_tx_pre = ds.execute(_sql_text_del(
            "SELECT pg_current_xact_id_if_assigned()::text AS tx_id"
        )).scalar()

        # Activity log audit (Krok 5.S doctrine NE-anonymous: kdo kdy co)
        # Krok 5.W fix (23.5.2026): ROOT CAUSE paradox FOUND!
        # Backend používal OLD column names (action_kind/target_kind/target_id/
        # payload/created_at) které v aktuálním schema NEEXISTUJÍ. Schema má:
        # (id, ts, persona_id, user_id, conversation_id, tenant_id, category,
        #  actor, summary, ref_type, ref_id, importance, change_source).
        #
        # Krok 5.W FIX (23.5.2026): activity_log INSERT s correct column names
        # + SAVEPOINT wrap. Doctrine "Bezpečnost přes probuzení, ne přes ticho"
        # (Marti-AI 9.5. + Fix N 21.5.): pokud INSERT failuje, jen savepoint
        # rollback — main tx zůstane clean a DELETE commit projde. Plus
        # explicit log_event(level='error') na fresh session pro forensic
        # visibility (Krok 5.W observability extension).
        #
        # Schema fw.activity_log: user_id, category, actor, summary, ref_type,
        # ref_id, change_source, importance, ts (NE OLD action_kind/target_kind/
        # target_id/payload/created_at — silent abort risk).
        #
        # Kanárek 23.5.2026 11:00 LIVE confirmed pipeline end-to-end:
        # log_event() → fw.diag_log → /badge polling → POPUP DIALOG.
        try:
            ds.execute(_sql_text_del("SAVEPOINT sp_activity_log"))
            try:
                ds.execute(_sql_text_del("""
                    INSERT INTO activity_log
                        (user_id, category, actor, summary, ref_type, ref_id,
                         change_source, importance, ts)
                    VALUES
                        (:uid, 'delete', 'user', :summary, :rt, :rid,
                         'ui', 3, NOW())
                """), {
                    "uid": uid,
                    "summary": f"DELETE {schema}.{table} id={row_id} (core_id={core_id}, deleted_rows={deleted_rows})",
                    "rt": f"{schema}.{table}",
                    "rid": row_id,
                })
                ds.execute(_sql_text_del("RELEASE SAVEPOINT sp_activity_log"))
            except Exception as _act_e:
                # Rollback savepoint — main tx zůstane clean (DELETE staged OK)
                try:
                    ds.execute(_sql_text_del("ROLLBACK TO SAVEPOINT sp_activity_log"))
                except Exception:
                    pass
                # Krok 5.W explicit log_event — fresh session immune to aborted tx
                try:
                    import traceback as _tb_act
                    from core.log_queue import log_event as _log_event_act
                    _log_event_act(
                        level="error",
                        source="py",
                        module_id="modules.erp.api.router:design_delete_entity:activity_log",
                        message=(
                            f"activity_log INSERT failed (savepoint rolled back): "
                            f"{type(_act_e).__name__}: {str(_act_e)[:300]}"
                        ),
                        exception_type=type(_act_e).__name__,
                        traceback_str=_tb_act.format_exc(),
                        extra={
                            "schema": schema,
                            "table": table,
                            "row_id": row_id,
                            "core_id": core_id,
                            "deleted_rows": deleted_rows,
                            "error_str": str(_act_e)[:500],
                        },
                    )
                except Exception:
                    pass  # last resort — never crash on log
                logger.warning(f"design_delete_entity activity_log INSERT failed (rolled back to savepoint): {_act_e}")
        except Exception as _sp_e:
            logger.warning(f"design_delete_entity savepoint setup failed: {_sp_e}")

        ds.commit()

        # Krok 5.W diag #3: tx state check PO commit. Mělo být NULL = tx closed.
        ds_tx_post = None
        try:
            ds_tx_post = ds.execute(_sql_text_del(
                "SELECT pg_current_xact_id_if_assigned()::text AS tx_id"
            )).scalar()
        except Exception as _e:
            ds_tx_post = f"err: {type(_e).__name__}"

        # Krok 5.W diag: fresh session re-check POST commit.
        # Pokud check_pre=0 ale check_post=1, commit se rolloutoval mimo
        # tuto session (deferred trigger? connection pool issue?).
        ds2 = _gds_del()
        check_post_commit = None
        ds2_conn_info = None
        try:
            ds2_conn_info = ds2.execute(_sql_text_del(
                "SELECT pg_backend_pid() AS pid, current_database() AS db, "
                "current_user AS pg_user, session_user AS sess_user, "
                "inet_server_addr()::text AS host, inet_server_port() AS port"
            )).mappings().first()
            check_post_commit = ds2.execute(_sql_text_del(
                f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{id_column}" = :rid'
            ), {"rid": row_id}).scalar()
        except Exception:
            pass
        finally:
            ds2.close()

        # Krok 5.W diag #3: full diag log s connection identity comparison
        ds_info_str = dict(ds_conn_info) if ds_conn_info else None
        ds2_info_str = dict(ds2_conn_info) if ds2_conn_info else None
        same_pid = (ds_conn_info and ds2_conn_info
                    and ds_conn_info["pid"] == ds2_conn_info["pid"])
        same_db = (ds_conn_info and ds2_conn_info
                   and ds_conn_info["db"] == ds2_conn_info["db"])
        same_host = (ds_conn_info and ds2_conn_info
                     and ds_conn_info["host"] == ds2_conn_info["host"])
        logger.info(
            f"design_delete_entity DELETE FROM {schema}.{table} id={row_id}:\n"
            f"  rowcount={deleted_rows}, pre={check_pre_commit}, post={check_post_commit}\n"
            f"  ds (DELETE+pre): {ds_info_str}\n"
            f"  ds tx pre={ds_tx_pre}, post={ds_tx_post} (None=tx closed)\n"
            f"  ds2 (post check): {ds2_info_str}\n"
            f"  same_pid={same_pid}, same_db={same_db}, same_host={same_host}"
        )

        return JSONResponse({
            "ok": True,
            "deleted_rows": deleted_rows,
            "core_id": core_id,
            "row_id": row_id,
            "schema": schema,
            "table": table,
            # Diag fields — frontend zobrazí v paradox warning pokud nesedí
            "check_pre_commit": check_pre_commit,
            "check_post_commit": check_post_commit,
            "ds_conn": ds_info_str,
            "ds2_conn": ds2_info_str,
            "ds_tx_pre": ds_tx_pre,
            "ds_tx_post": ds_tx_post,
            "same_pid": same_pid,
            "same_db": same_db,
            "same_host": same_host,
        })
    except Exception as exc:
        ds.rollback()
        logger.exception(f"design_delete_entity failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"DELETE failed: {exc}"},
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
            SELECT id, code, label, kind, preview_html, status, renderer_hint,
                   default_props
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


@api_router.get("/design/comp-type/{type_id:int}/defaults")
def design_get_comp_type_defaults(type_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok H+5 (26.5.2026, Marti's "Nacist vychozi"):
    Vrati fw.comp_type.default_props pro dany type_id. Frontend popup
    "Nacist vychozi" tlacitko zavola tento endpoint + fill form fields.

    Returns:
        200: {ok, type_id, code, label, default_props}
        404: type_id neexistuje
    """
    from core.database_data import get_data_session as _gds_ctd
    from sqlalchemy import text as _sql_text_ctd

    uid = _get_uid(req)
    _require_parent(uid)

    ds = _gds_ctd()
    try:
        row = ds.execute(_sql_text_ctd("""
            SELECT id, code, label, default_props
            FROM fw.comp_type
            WHERE id = :id
        """), {"id": type_id}).mappings().one_or_none()
        if not row:
            return JSONResponse(
                {"ok": False, "error": f"comp_type id={type_id} neexistuje"},
                status_code=404,
            )
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "type_id": row["id"],
            "code": row["code"],
            "label": row["label"],
            "default_props": row["default_props"] or {},
        }))
    finally:
        ds.close()


@api_router.put("/design/comp-type/{type_id:int}/defaults")
async def design_put_comp_type_defaults(type_id: int, req: Request) -> JSONResponse:
    """Phase 38.4 Krok H+5 (26.5.2026, Marti's "Ulozit jako vychozi"):
    SET fw.comp_type.default_props pro dany type_id. Frontend popup
    "Ulozit jako vychozi" tlacitko posila aktualni form values jako
    JSON. Pristi add tohoto typu dostane defaults.

    Body:
        {default_props: dict}  # complete replace (ne merge)

    Returns:
        200: {ok, type_id, default_props}
        400: invalid body
        404: type_id neexistuje
    """
    from core.database_data import get_data_session as _gds_ctp
    from sqlalchemy import text as _sql_text_ctp
    import json as _json_ctp

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Body musi byt JSON"},
            status_code=400,
        )

    default_props = body.get("default_props")
    if not isinstance(default_props, dict):
        return JSONResponse(
            {"ok": False, "error": "default_props musi byt dict (objekt)"},
            status_code=400,
        )

    # Marti-AI's PG role (db_owner fw schema) — strategie session
    # nepustila UPDATE fw.comp_type kvuli ownership boundary.
    # GOTCHA (26.5.2026): update_row default dry_run=True (preview only) —
    # MUSI explicit dry_run=False jinak SQL nikdy nebezi a vraci
    # matched_count misto count → rows_affected None → falesny 404.
    from modules.strategie_pg.application.service import update_row as _spg_update_ctp
    try:
        result = _spg_update_ctp(
            schema="fw",
            table="comp_type",
            values={"default_props": _json_ctp.dumps(default_props)},
            where={"id": type_id},
            dry_run=False,
        )
        if not result.get("ok"):
            return JSONResponse(
                {"ok": False, "error": result.get("error") or "update_row failed"},
                status_code=500,
            )
        # update_row(dry_run=False) returns {"ok", "updated": [...], "count": N}
        _rows_updated = (result.get("count")
                         if result.get("count") is not None
                         else (result.get("rows_affected") or 0))
        if not _rows_updated:
            return JSONResponse(
                {"ok": False, "error": f"comp_type id={type_id} neexistuje"},
                status_code=404,
            )
        return JSONResponse(jsonable_encoder({
            "ok": True,
            "type_id": type_id,
            "default_props": default_props,
        }))
    except Exception as exc:
        logger.error(
            f"design_put_comp_type_defaults failed: {exc}",
            extra={"type_id": type_id},
        )
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=500,
        )


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
            SELECT id, type_id, core_id
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


@api_router.get("/design/comp-def/get/{comp_def_id}")
async def design_get_comp_def(comp_def_id: int, req: Request) -> JSONResponse:
    """Čerstvý comp_def pro settings popup (Marti 3.6.: memo nenačítal layout).

    Popup dosud bral field z (možná stale) this._spec.fields. Tento GET vrací
    aktuální DB stav (layout JSONB + caption + data_source_id + comp_type_code),
    takže load parametrů nezávisí na stáří front-endového spec. 3-segmentová
    cesta /design/comp-def/get/{id} se vyhne kolizi s generic /design/{e}/{id}.
    """
    uid = _get_uid(req)
    _require_parent(uid)
    from core.database_data import get_data_session as _gds_gcd
    from sqlalchemy import text as _sql_gcd
    ds = _gds_gcd()
    try:
        row = ds.execute(_sql_gcd("""
            SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.region_slot,
                   cd.parent_comp_def_id, cd.data_source_id, cd.layout,
                   ct.code AS comp_type_code, ct.label AS comp_type_label
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.type_id
            WHERE cd.id = :id AND cd.is_active = true
        """), {"id": comp_def_id}).mappings().one_or_none()
        if not row:
            return JSONResponse({"ok": False, "error": "comp_def neexistuje"}, status_code=404)
        # no-store: settings popup musí vždy číst aktuální DB stav (Marti 3.6.:
        # cachovaný GET ukazoval stará layout data — max_width drželo starou hodnotu).
        return JSONResponse(
            jsonable_encoder({"ok": True, "comp_def": dict(row)}),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )
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
      2. Walk parent_comp_def chain UP -> find core_id (form root)
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
            SELECT id, name, parent_comp_def_id, core_id
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
        core_id = cd["core_id"]
        current_parent = cd["parent_comp_def_id"]
        max_depth = 10
        while not core_id and current_parent and max_depth > 0:
            parent = ds_dv.execute(_sql_text_dv("""
                SELECT id, parent_comp_def_id, core_id
                FROM fw.comp_def WHERE id = :id
            """), {"id": current_parent}).mappings().one_or_none()
            if not parent:
                break
            if parent["core_id"]:
                core_id = parent["core_id"]
                break
            current_parent = parent["parent_comp_def_id"]
            max_depth -= 1

        if not core_id:
            return JSONResponse(
                {"ok": False, "error": "Nelze najit parent core (form root)"},
                status_code=400,
            )

        # Phase 38.4 Krok H+5++++++ (26.5.2026 vecer, Marti's "rozchodit
        # kombobox"): pouzit univerzalni resolver misto code-only path.
        # _resolve_entity_config_for_core(core_id) zvlada:
        #   1. DB-driven pres fw.data_source.target_xxx (Krok 5.N-2, PRIMARY)
        #   2. _FW_FORM_CORE_REGISTRY (legacy id-keyed)
        #   3. _FW_FORM_ENTITY_MAP (legacy code-keyed)
        # → funguje i pro drafted cores s code=NULL (Krok 5.A doctrine).
        core_row = ds_dv.execute(_sql_text_dv("""
            SELECT id, code
            FROM fw.core WHERE id = :id
        """), {"id": core_id}).mappings().one_or_none()
        if not core_row:
            return JSONResponse(
                {"ok": False, "error": f"Core id={core_id} neexistuje"},
                status_code=400,
            )
        config = _resolve_entity_config_for_core(dict(core_row))
        if not config:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Nelze resolve entity config pro core_id={core_id} "
                        f"(code={core_row['code']!r}) — chybí target_table na "
                        f"fw.data_source nebo neni v _FW_FORM_CORE_REGISTRY."
                    ),
                },
                status_code=400,
            )

        # 4. Column whitelist check (anti-PII, anti-SQL-injection)
        # Krok H+5++++++ (26.5.2026 vecer): select_columns=None znamena
        # "trust frontend" (Marti's Krok 5.N-2 doctrine) — DB-driven cores
        # nemaji explicit whitelist. Fallback validace pres
        # information_schema.columns: col_name musi existovat v target table.
        # Tim drzime SQL injection guard bez per-entity registrace.
        col_name = cd["name"]
        allowed_cols = config.get("select_columns")
        schema_name = config.get("schema", "public")
        table_name = config["table"]
        if allowed_cols is not None:
            # Explicit whitelist (legacy _FW_FORM_ENTITY_MAP / _FW_FORM_CORE_REGISTRY)
            if col_name not in set(allowed_cols):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            f"Column '{col_name}' neni v whitelist "
                            f"select_columns pro tuto entitu."
                        ),
                    },
                    status_code=400,
                )
        else:
            # DB-driven (Krok 5.N-2): validate via information_schema.columns
            col_check = ds_dv.execute(_sql_text_dv("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :s
                  AND table_name = :t
                  AND column_name = :c
                LIMIT 1
            """), {"s": schema_name, "t": table_name, "c": col_name}).scalar()
            if not col_check:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            f"Column '{col_name}' neexistuje v "
                            f"{schema_name}.{table_name}."
                        ),
                    },
                    status_code=400,
                )

        # 5. SELECT DISTINCT — col_name + table_name jsou whitelisted/server-side,
        # bezpecne pres f-string interpolation (no user input)
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


# ────────────────────────────────────────────────────────────────────
# Krok H+4 (26.5.2026 ranni, Marti's "C=CREATE INSERT NOVY"):
# POST INSERT endpoint — analog design_patch_entity ale CREATE flow.
# Reuse _resolve_entity_config_for_core (5.N-2 v2 SQL parse resolver).
# Marti's Q1=A "naproste minimum at se nezamotame" — drop expected_updated_at,
# drop child rows (= jen parent INSERT). Body shape mirror PATCH
# (field_changes dict). Response: {ok, id, created_at, created_by_id, ...}.
# Audit Marti-AI (created_by_*).
# ────────────────────────────────────────────────────────────────────

@api_router.post("/design/{core_id:int}")
async def design_insert_entity(core_id: int, req: Request) -> JSONResponse:
    """CREATE flow POST endpoint pro DesignFwForm Nový (C) button.

    Phase 38.4 Krok H+5 (26.5.2026): :int path converter — same lesson
    jako DELETE /design/{core_id}/{row_id} (route collision s /design/comp-def
    + /design/db-connection atd.).

    Body: {
        "field_changes": {"label": "Nový label", ...},
    }
    (Marti's Q5=A: same shape jako PATCH — reuse parsing logic.)

    Returns:
        200: {ok, id, created_at, created_by_id, created_by_text} — success
        404: core_id nema entity_config v _FW_FORM_CORE_REGISTRY
        400: field_changes prazdne nebo ID column included
        500: DB error
    """
    from core.database_data import get_data_session as _gds_insert
    from sqlalchemy import text as _sql_text_insert

    uid = _get_uid(req)
    # Phase D: numeric core_id → business data, členové smí (rodič vše).
    _require_data_write_access(uid, str(core_id))

    body = await req.json()
    field_changes = body.get("field_changes") or {}

    if not isinstance(field_changes, dict) or not field_changes:
        return JSONResponse(
            {"ok": False, "error": "field_changes musi byt non-empty dict"},
            status_code=400,
        )

    # ID-based resolver (Marti's 5.N doctrine — core_id always numeric path)
    entity_config = _resolve_entity_config_for_core(core_id)
    if not entity_config:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    f"Core ID {core_id} nema entity_config v _FW_FORM_CORE_REGISTRY. "
                    f"Registry IDs: {list(_FW_FORM_CORE_REGISTRY.keys())}."
                ),
            },
            status_code=404,
        )
    schema_name = entity_config["schema"]
    table_name = entity_config["table"]
    id_column = entity_config["id_column"]
    _raw_cols = entity_config.get("select_columns")
    allowed_columns = set(_raw_cols) if _raw_cols is not None else None

    # Universal optional fields (mirror PATCH UNIVERSAL_OPTIONAL_FIELDS)
    UNIVERSAL_OPTIONAL_FIELDS_INSERT = frozenset({
        "description_user",
        "description_system",
        "version",
    })

    # Validate field_changes — block id_column (auto-generated)
    if allowed_columns is not None:
        invalid_fields = [
            f for f in field_changes
            if (f not in allowed_columns and f not in UNIVERSAL_OPTIONAL_FIELDS_INSERT)
                or f == id_column
        ]
        if invalid_fields:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"Sloupce {invalid_fields} nejsou povolene v POST "
                        f"pro core_id={core_id}. Allowed: {sorted(allowed_columns - {id_column})}"
                    ),
                },
                status_code=400,
            )
    else:
        # NULL whitelist — block jen id_column (immutable auto-gen)
        invalid_fields = [f for f in field_changes if f == id_column]
        if invalid_fields:
            return JSONResponse(
                {
                    "ok": False,
                    "error": (
                        f"ID column '{id_column}' je auto-generated — nelze "
                        f"poslat v field_changes. Keys: {list(field_changes.keys())}"
                    ),
                },
                status_code=400,
            )

    # ─────────────────────────────────────────────────────────────────────
    # Krok #11 — cross-connection INSERT routing (31.5.2026, Marti: "Co ma
    # PostgreSQL co delat s insertem pres MCP. Bez toho dal jit nemuzeme").
    # CRM data zijou v MSSQL DB_EC, ne v PostgreSQL. design_insert_entity byl
    # PG-only → insert na MSSQL core hazel "relation st.X does not exist".
    # Fix: MSSQL vetev = zrcadlo design_patch_entity UPDATE vetve. Insert pres
    # MCP eurosoft_strategie_insert_row do DB_EC. Audit (Vytvoril/DatPorizeni/
    # Zmenil/DatZmeny) autofill jen pokud sloupce existuji (defense in depth).
    # ─────────────────────────────────────────────────────────────────────
    _db_type_insert = (entity_config.get("db_type") or "pg").lower()
    _dc_code_insert = entity_config.get("dc_code") or ""
    if _db_type_insert == "mssql":
        import json as _json_insert_mssql
        try:
            from modules.conversation.application.eurosoft_mcp_client import (
                get_eurosoft_mcp_client,
                get_mssql_columns_cached as _get_mssql_cols_ins,
            )
            from modules.auth.application.audit_actor import (
                resolve_audit_actor as _audit_resolve_ins,
                resolve_tenant_id_from_dc_code as _audit_tenant_from_dc_ins,
            )
            from datetime import datetime as _dt_insert_audit

            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                logger.warning(
                    "[design_insert_entity] MCP client None "
                    "(eurosoft_mcp_enabled=False?) — MSSQL insert abort"
                )
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "MCP client neni dostupny (eurosoft_mcp_enabled=False?). "
                            "MSSQL insert flow vyzaduje MCP."
                        ),
                    },
                    status_code=503,
                )

            # dc_code = 'eurosoft_db_ec' → MCP db_name = 'DB_EC' (parity s patch)
            mcp_db_name = "DB_EC"
            if _dc_code_insert and _dc_code_insert.lower().startswith("eurosoft_"):
                mcp_db_name = _dc_code_insert[len("eurosoft_"):].upper()

            # Audit actor (mssql_text = user_tenants.db_login). NULL → fail visible.
            _audit_tenant_id_ins = _audit_tenant_from_dc_ins(_dc_code_insert)
            audit_mssql_text_ins = None
            if _audit_tenant_id_ins:
                try:
                    _ds_audit_ins = _gds_insert()
                    try:
                        audit_mssql_ins = _audit_resolve_ins(
                            uid=uid,
                            target_tenant_id=_audit_tenant_id_ins,
                            target_db_kind="mssql",
                            ds=_ds_audit_ins,
                        )
                    finally:
                        _ds_audit_ins.close()
                    audit_mssql_text_ins = audit_mssql_ins["mssql_text"]
                except ValueError as _audit_ins_exc:
                    logger.exception(
                        f"design_insert_entity MSSQL audit resolve failed: {_audit_ins_exc}"
                    )
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": f"MSSQL audit actor resolve failed: {_audit_ins_exc}",
                        },
                        status_code=500,
                    )
            else:
                logger.warning(
                    "[design_insert_entity] MSSQL audit: tenant_id neresolved "
                    "z dc_code=%r — insert bez Vytvoril/Zmenil autofill",
                    _dc_code_insert,
                )

            # ── Resolve field → real DB column via layout.save (PARITY s UPDATE).
            # Asymetrie kterou Marti nasel (31.5.): UPDATE resolvuje fieldy na
            # realne sloupce pres save binding (column_name 'fld_test_*' jsou jen
            # placeholdery), INSERT puvodne posilal raw keys → MSSQL "invalid
            # column". Fix: mirror patch _field_layout_map resolution. INSERT
            # zapisuje jen BASE tabulku (related tabulky = nested, az po master
            # insertu — chicken-egg s master ID).
            _field_layout_map_ins = {}
            _resolve_core_id_ins = entity_config.get("core_id")
            if _resolve_core_id_ins:
                try:
                    _ds_lay_ins = _gds_insert()
                    try:
                        _rows_lay_ins = _ds_lay_ins.execute(
                            _sql_text_insert(
                                "SELECT name, layout FROM fw.comp_def "
                                "WHERE core_id = :cid AND parent_comp_def_id IS NOT NULL "
                                "AND is_active = true"
                            ),
                            {"cid": _resolve_core_id_ins},
                        ).mappings().all()
                        for _r in _rows_lay_ins:
                            _field_layout_map_ins[_r["name"]] = _r["layout"] or {}
                    finally:
                        _ds_lay_ins.close()
                except Exception as _lay_ins_exc:
                    logger.warning(
                        "[design_insert_entity] MSSQL layout resolve failed "
                        "(core_id=%s): %r — fallback column_name",
                        _resolve_core_id_ins, _lay_ins_exc,
                    )

            # Group fieldy podle save coordinate (schema, table, row_key).
            # Master-detail: base group (CRM_Kontakt) + related groups
            # (CRM_Kontakt_Akce s row_key {IDHlav:@id, IDakce:16}). @id = master
            # ID doplnime az PO base insertu (chicken-egg).
            def _rk_template_ins(_rk):
                """row_key dict → (literal_cols, id_cols[]). @id = master ID."""
                _lits, _idc = {}, []
                for _rk_k, _rk_v in (_rk or {}).items():
                    if _rk_v == "@id":
                        _idc.append(_rk_k)
                    else:
                        _lits[_rk_k] = _rk_v
                return _lits, _idc

            # Base fieldy (schema_name.table_name) → master row; jejich row_key
            # {ID:@id} = self-PK (auto-gen identity) → ignorujeme. Related fieldy
            # (jina tabulka, napr CRM_Kontakt_Akce) → groups s @id (master ID
            # doplnime po base insertu) + literaly (IDakce=16).
            _base_data_fields = {}
            _ins_groups = {}
            _skipped_ins = []
            for _fk_name, _fk_val in field_changes.items():
                if _fk_name == id_column:
                    continue
                _lay = _field_layout_map_ins.get(_fk_name) or {}
                _save = _lay.get("save") if isinstance(_lay, dict) else None
                if isinstance(_save, dict) and _save.get("readonly"):
                    _skipped_ins.append((_fk_name, "readonly"))
                    continue
                if isinstance(_save, dict) and _save.get("table"):
                    _g_schema = _save.get("schema") or schema_name
                    _g_table = _save["table"]
                    _g_col = _save.get("column") or _fk_name
                    _g_lits, _g_idc = _rk_template_ins(_save.get("row_key"))
                else:
                    _g_schema = schema_name
                    _g_table = table_name
                    _g_col = (
                        _lay.get("column_name") if isinstance(_lay, dict) else None
                    ) or _fk_name
                    _g_lits, _g_idc = {}, []
                # BASE tabulka = master row → sloupec do base, row_key
                # (self-PK @id) ignorujeme (ID auto-gen identity).
                if (_g_schema, _g_table) == (schema_name, table_name):
                    _base_data_fields[_g_col] = _fk_val
                    continue
                # RELATED tabulka → group dle (schema, table, literals, id_cols).
                _gkey = (
                    _g_schema, _g_table,
                    tuple(sorted(_g_lits.items())), tuple(sorted(_g_idc)),
                )
                _grp = _ins_groups.setdefault(_gkey, {
                    "schema": _g_schema, "table": _g_table,
                    "data": dict(_g_lits), "id_cols": _g_idc,
                })
                _grp["data"][_g_col] = _fk_val
            if _skipped_ins:
                logger.info(
                    "[design_insert_entity] MSSQL skip fields (readonly): %s",
                    _skipped_ins,
                )

            # ── Master-detail INSERT (31.5.2026, Marti "A souhlasim"):
            # 1) base group (schema_name.table_name) → master ID.
            # 2) related groups (jina tabulka, row_key @id) → @id=master ID +
            #    literaly (napr IDakce=16) → insert. Tim vznikne i Akce radek,
            #    ktery SELECT (outer join IDakce=16) cte → read = write konzist.
            # Bez cross-table transakce (MCP per-call commit); pri related fail
            # po base insertu = partial (master vznikne) → 500 s info.
            _now_ins = _dt_insert_audit.now().strftime("%Y-%m-%d %H:%M:%S")

            # Base data = master row sloupce (z _base_data_fields, naplnene
            # v grouping loop). Anchor pro related — i kdyz uziv nezmenil zadne
            # base pole (vyplnil jen firemni Akce pole), audit nize zajisti
            # aspon 1 sloupec.
            _base_data = _base_data_fields

            # Audit do base group (best-effort introspect; fallback optimistic
            # Autor/DatPorizeni — CRM_Kontakt je ma per SSMS 31.5.).
            try:
                _mssql_cols_ins = _get_mssql_cols_ins(
                    mcp_db_name, schema_name, table_name
                )
                _colset_ins = {str(c).lower() for c in (_mssql_cols_ins or [])}
            except Exception as _cols_ins_exc:
                logger.warning(
                    "[design_insert_entity] describe base %s.%s failed: %r "
                    "— optimistic audit (Autor/DatPorizeni)",
                    schema_name, table_name, _cols_ins_exc,
                )
                _colset_ins = None
            for _ac, _av in (
                ("Autor", audit_mssql_text_ins),
                ("DatPorizeni", _now_ins),
                ("Zmenil", audit_mssql_text_ins),
                ("DatZmeny", _now_ins),
            ):
                if _av is None or _ac in _base_data:
                    continue
                if _colset_ins is None:
                    if _ac in ("Autor", "DatPorizeni"):
                        _base_data[_ac] = _av
                elif _ac.lower() in _colset_ins:
                    _base_data[_ac] = _av
            # base musi mit aspon 1 sloupec (strategie_insert_row vyzaduje data)
            if not _base_data:
                _base_data["DatPorizeni"] = _now_ins

            import re as _re_ins_default

            def _unwrap_sql_default(_v):
                # SQL Server COLUMN_DEFAULT leak: default_value misset na raw
                # SQL vyraz '((0))' / "('text')" → unwrap na hodnotu (jinak
                # conversion fail napr. '((0))' -> bit). Marti 31.5.: "do
                # fieldu Splneno leze default 0".
                if not isinstance(_v, str):
                    return _v
                _s = _v.strip()
                _mnum = _re_ins_default.match(r"^\(+\s*(-?\d+)\s*\)+$", _s)
                if _mnum:
                    return int(_mnum.group(1))
                _mstr = _re_ins_default.match(
                    r"^\(+\s*N?'(.*)'\s*\)+$", _s, _re_ins_default.DOTALL
                )
                if _mstr:
                    return _mstr.group(1)
                return _v

            def _mcp_insert_row(_schema, _table, _data):
                _clean = {
                    _ck: _unwrap_sql_default(_cv)
                    for _ck, _cv in _data.items()
                }
                _j = mcp.call_tool_sync(
                    "eurosoft_strategie_insert_row",
                    {"schema": _schema, "table": _table,
                     "data": _clean, "db_name": mcp_db_name},
                    conversation_id=None,
                )
                return (
                    _json_insert_mssql.loads(_j)
                    if isinstance(_j, str) else _j
                )

            def _ins_err(_r):
                return (
                    (_r.get("message") or _r.get("exception_repr")
                     or _r.get("error"))
                    if isinstance(_r, dict) else str(_r)
                )

            # 1) base insert → master ID
            _base_res = _mcp_insert_row(
                schema_name, table_name, _base_data
            )
            if not (isinstance(_base_res, dict) and _base_res.get("ok")):
                logger.warning(
                    "[design_insert_entity] base insert failed %s.%s: %r",
                    schema_name, table_name, _base_res,
                )
                return JSONResponse(
                    {"ok": False, "error": (
                        f"MSSQL INSERT base ({schema_name}.{table_name}): "
                        f"{_ins_err(_base_res)}")},
                    status_code=500,
                )
            _master_id = _base_res.get("id")

            # 2) related groups (resolve @id → master ID)
            # Vsechny _ins_groups jsou related (base fieldy jsou v _base_data).
            _related_ins = []
            for _gk, _grp in _ins_groups.items():
                _rdata = dict(_grp["data"])
                for _idcol in _grp["id_cols"]:
                    _rdata[_idcol] = _master_id
                if not _rdata:
                    continue
                _rel_res = _mcp_insert_row(
                    _grp["schema"], _grp["table"], _rdata
                )
                if not (isinstance(_rel_res, dict) and _rel_res.get("ok")):
                    # MSSQL conversion error nepojmenuje sloupec → surface
                    # poslane sloupce+hodnoty, at Marti vidi ktery sloupec
                    # dostal spatnou hodnotu (napr. '((0))' do bit sloupce).
                    _rdata_dump = ", ".join(
                        f"{_dk}={_dv!r}" for _dk, _dv in _rdata.items()
                    )
                    logger.warning(
                        "[design_insert_entity] related insert failed "
                        "%s.%s data={%s}: %r",
                        _grp["schema"], _grp["table"], _rdata_dump, _rel_res,
                    )
                    return JSONResponse(
                        {"ok": False, "id": _master_id,
                         "data_sent": {_dk: str(_dv) for _dk, _dv in _rdata.items()},
                         "error": (
                            f"Base zalozen (id={_master_id}), ale related "
                            f"INSERT ({_grp['schema']}.{_grp['table']}) "
                            f"selhal: {_ins_err(_rel_res)}\n\nPoslane sloupce: "
                            f"{{{_rdata_dump}}}")},
                        status_code=500,
                    )
                _related_ins.append(
                    {"table": _grp["table"], "id": _rel_res.get("id")}
                )

            logger.info(
                "[design_insert_entity] MSSQL master-detail OK master=%s.%s "
                "id=%s related=%s",
                schema_name, table_name, _master_id, _related_ins,
            )
            return JSONResponse({
                "ok": True,
                "id": _master_id,
                "created_at": None,
                "created_by_id": uid,
                "created_by_text": audit_mssql_text_ins,
                "related": _related_ins,
            })
        except Exception as _ins_mssql_exc:
            logger.exception(
                f"design_insert_entity MSSQL branch failed: {_ins_mssql_exc}"
            )
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"MSSQL INSERT failed: {str(_ins_mssql_exc)[:300]}",
                },
                status_code=500,
            )

    # Caller display name (mirror PATCH pattern)
    caller_display = "Unknown"
    if uid:
        from core.database_core import get_core_session as _gcs_insert
        from modules.core.infrastructure.models_core import User as _User_insert
        cs_insert = _gcs_insert()
        try:
            u_insert = cs_insert.query(_User_insert).filter_by(id=uid).first()
            if u_insert:
                if u_insert.short_name and u_insert.short_name.strip():
                    caller_display = u_insert.short_name.strip()
                elif u_insert.first_name or u_insert.last_name:
                    caller_display = " ".join(filter(None, [
                        u_insert.first_name, u_insert.last_name
                    ])).strip() or "Unknown"
                else:
                    caller_display = f"user_{uid}"
        finally:
            cs_insert.close()

    # Build INSERT — drop None values, add created_by_* if columns exist
    insert_fields = dict(field_changes)
    # Audit injection (defensive — only if column exists v target table)
    ds = _gds_insert()
    try:
        # Discover real columns v target table (catch missing audit columns)
        col_check = ds.execute(_sql_text_insert(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = :s AND table_name = :t"
        ), {"s": schema_name, "t": table_name}).fetchall()
        real_cols = {r[0] for r in col_check}

        # Inject audit if columns exist (mirror PATCH Krok 5.N-2 hotfix #2)
        if "created_by_id" in real_cols and "created_by_id" not in insert_fields:
            insert_fields["created_by_id"] = uid
        if "created_by_text" in real_cols and "created_by_text" not in insert_fields:
            insert_fields["created_by_text"] = caller_display

        # ─────────────────────────────────────────────────────────────────
        # Krok H+4 follow-up (26.5.2026, Marti's "ID je svaty" doctrine):
        # Pre-validate NOT NULL columns PRED INSERT execute. Důvod —
        # PostgreSQL sequence (SERIAL/IDENTITY) konzumuje nextval() i pri
        # failed INSERT → rollback NEVRATI sequence → gap v IDs (Marti's
        # 26.5. catch "preskcily IDcka 24/25/26").
        #
        # Fix: check NOT NULL columns bez column_default → pokud chybi v
        # insert_fields → return 400 Bad Request → sequence se NEbumpne.
        #
        # NOT excluded: kolony s column_default (sequence, NOW(), '...') —
        # DB se postara o defaults bez user input. Exclusion list jen pro
        # case kdy column nema default ALE generuje se elsewhere (rare).
        # ─────────────────────────────────────────────────────────────────
        try:
            required_rows = ds.execute(_sql_text_insert(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = :t "
                "  AND is_nullable = 'NO' "
                "  AND column_default IS NULL"
            ), {"s": schema_name, "t": table_name}).fetchall()
            required_cols = {r[0] for r in required_rows}
            # Exclude id column (auto-generated by sequence) + audit fields
            # (backend injects above)
            auto_filled = {id_column}
            missing = required_cols - auto_filled - set(insert_fields.keys())
            if missing:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            f"Povinná pole nejsou vyplněna: "
                            f"{', '.join(sorted(missing))}"
                        ),
                        "missing_columns": sorted(missing),
                    },
                    status_code=400,
                )
        except Exception as exc_validate:
            # Pre-validation selhala — log warning a pokracuj na INSERT
            # (DB constraint stejne zachyti, jen bez friendly msg)
            logger.warning(
                f"design_insert_entity pre-validation failed for "
                f"{schema_name}.{table_name}: {exc_validate}"
            )

        # Build INSERT SQL
        col_list = ", ".join(insert_fields.keys())
        placeholders = ", ".join(f":{k}" for k in insert_fields.keys())
        insert_sql = (
            f"INSERT INTO {schema_name}.{table_name} ({col_list}) "
            f"VALUES ({placeholders}) "
            f"RETURNING {id_column}, "
            f"{'created_at' if 'created_at' in real_cols else 'NULL AS created_at'}, "
            f"{'created_by_id' if 'created_by_id' in real_cols else 'NULL AS created_by_id'}, "
            f"{'created_by_text' if 'created_by_text' in real_cols else 'NULL AS created_by_text'}"
        )

        try:
            result_row = ds.execute(
                _sql_text_insert(insert_sql), insert_fields
            ).mappings().one()
            ds.commit()
        except Exception as ex:
            ds.rollback()
            logger.exception(f"design_insert_entity INSERT failed: {ex}")
            return JSONResponse(
                {"ok": False, "error": f"INSERT failed: {str(ex)[:300]}"},
                status_code=500,
            )

        return JSONResponse({
            "ok": True,
            "id": result_row[id_column],
            "created_at": str(result_row.get("created_at")) if result_row.get("created_at") else None,
            "created_by_id": result_row.get("created_by_id"),
            "created_by_text": result_row.get("created_by_text"),
        })
    finally:
        ds.close()


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
    # Phase 38.4 Krok H+5 (26.5.2026, Marti's "menit typ dynamicky"):
    # type_id pridan do whitelist — change comp_type live z palety
    # ("Jiz na forme" tab dropdown). Bezpecne: type_id je INT FK na
    # fw.comp_type, FK constraint chrani proti garbage values.
    ALLOWED = (
        "caption", "region_slot", "layout",
        "parent_comp_def_id", "sort_order", "is_active",
        "data_source_id", "type_id",
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
        # Phase fw.core slim 20.5.2026: layout_type + data_entity_type DROPNUTE
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
    # Phase fw.core slim 20.5.2026: layout_type + data_entity_type body fields DROPPED
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
                f"CREATE fw.core code={code} label={label} "
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

    # Phase fw.core slim 20.5.2026: origin_menu_node_id + origin_cmi_id DROPNUTE
    origin_menu_node_id = None
    origin_cmi_id = None

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


# ============================================================================
# Executable artifact PoC (25.5.2026 vecer, Marti's strategic shift
# "DESCRIBE-FIRST INSERT epoch + executable_artifact PoC v jednom epochu"):
# POST /api/v1/erp/sandbox/execute/<code> loads source z fw.executable_artifact
# + dispatch Python (via existing sandbox) nebo SQL (deferred PoC). Marti
# edituje source pres DBeaver UPDATE, Phase 45 = UI editor + version lineage.
#
# Marti's doctrine: "PoC najde realitu, Production navrhuje refaktor".
# ============================================================================

# Marti's PoC PoC sentinel marker (idempotence + audit grep):
#   _executable_artifact_poc_endpoint_v1

@api_router.post("/sandbox/execute/{artifact_code}")
async def sandbox_execute_artifact(artifact_code: str, req: Request) -> JSONResponse:
    """Krok B PoC: execute artifact (Python) from fw.executable_artifact.

    Marti's scope 25.5.2026:
      - Parent-only (is_marti_parent gate)
      - Python only (artifact_type='python')
      - SQL → 501 Not Implemented (defer)
      - Reuse existing sandbox python_runner (Phase 27c)
      - log_event START + FINISH do fw.diag_log

    Path param:
      artifact_code: fw.executable_artifact.code (UNIQUE)

    Returns:
      {
        ok: bool,
        artifact_code: str,
        artifact_type: str,
        runtime_ms: int,
        stdout: str,
        stderr: str,
        error: str | None,
        error_kind: str | None,
      }
    """
    from core.database_data import get_data_session as _gds_sx
    from sqlalchemy import text as _sql_sx
    from core.log_queue import log_event as _log_event_sx

    # Parent gate (PoC scope — drz security tight)
    uid = _get_uid(req)
    _require_parent(uid)

    # Krok F (25.5.2026 vecer, Marti's PoC): parse optional POST body
    # pro context (coreId, coreCode, rowId, atd.). Orchestrator dostane
    # serialized JSON v env var SANDBOX_CONTEXT pres sandbox extra_env.
    _sandbox_ctx_json_sx = "{}"
    try:
        _body_sx = await req.json()
        if isinstance(_body_sx, dict):
            import json as _json_sx_F
            _sandbox_ctx_json_sx = _json_sx_F.dumps(_body_sx, ensure_ascii=True, default=str)
    except Exception:
        # No body or non-JSON — orchestrator dostane prazdny {}
        pass

    # Lookup artifact
    ds_sx = _gds_sx()
    try:
        row = ds_sx.execute(_sql_sx("""
            SELECT id, code, artifact_type, source, description
            FROM fw.executable_artifact
            WHERE code = :code
        """), {"code": artifact_code}).fetchone()
    finally:
        ds_sx.close()

    if not row:
        # log_event 'warning' — Marti might typo code
        try:
            _log_event_sx(
                level="warning",
                source="py",
                module_id=f"sandbox.execute.{artifact_code}",
                message=f"Artifact not found: {artifact_code}",
                extra={"artifact_code": artifact_code, "uid": uid},
            )
        except Exception:
            pass
        return JSONResponse(
            {"ok": False, "error": f"Artifact '{artifact_code}' not found"},
            status_code=404,
        )

    artifact_id = row.id
    artifact_type = row.artifact_type
    source = row.source

    # ────────────────────────────────────────────────────────────────────────
    # Krok H+5 auto-sync (26.5.2026 vecer, Marti's "git je truth, DB je cache"):
    # Pred execute zkontroluj scripts/executable_artifacts/{code}.{ext} —
    # pokud existuje + content != DB source → UPSERT DB, return file content
    # pro execute. Pokud file neexistuje → continue s DB source ("kdyz neni
    # na disku, spusti se z DB" doctrine).
    # ────────────────────────────────────────────────────────────────────────
    try:
        from modules.sandbox.application.artifact_autosync import (
            autosync_from_file as _autosync_sx,
        )
        ds_sync_sx = _gds_sx()
        try:
            source = _autosync_sx(
                artifact_id=artifact_id,
                code=artifact_code,
                artifact_type=artifact_type,
                db_source=source,
                ds_session=ds_sync_sx,
                sql_text=_sql_sx,
                log_event_fn=_log_event_sx,
            )
        finally:
            ds_sync_sx.close()
    except ValueError as _autosync_corruption:
        # File # ID marker mismatch — HARD ERROR (data corruption signal)
        try:
            _log_event_sx(
                level="error",
                source="py",
                module_id=f"sandbox.autosync.{artifact_code}",
                message=f"AUTOSYNC HARD ERROR: {_autosync_corruption}",
                extra={"artifact_id": artifact_id, "uid": uid},
            )
        except Exception:
            pass
        return JSONResponse(
            {
                "ok": False,
                "error": f"Auto-sync corruption: {_autosync_corruption}",
                "error_kind": "autosync_id_mismatch",
            },
            status_code=500,
        )
    except Exception as _autosync_other:
        # Defensive — autosync chyba nesmi blokovat execute, pokracujeme s DB source
        try:
            _log_event_sx(
                level="warning",
                source="py",
                module_id=f"sandbox.autosync.{artifact_code}",
                message=f"Auto-sync skipped (error): {_autosync_other}",
                extra={"artifact_id": artifact_id, "uid": uid},
            )
        except Exception:
            pass

    # log_event START
    # Marti 1.6.2026: loguj i PARAMETRY, se kterými se artefakt spustil
    # (POST body context = SANDBOX_CONTEXT, např. {coreId, coreCode, rowId,
    # gridCode, ...}) — pro diagnostiku gridů vidět, co skript reálně cílí.
    _ctx_preview_sx = (
        _sandbox_ctx_json_sx if len(_sandbox_ctx_json_sx) <= 400
        else (_sandbox_ctx_json_sx[:400] + "…")
    )
    try:
        _log_event_sx(
            level="info",
            source="py",
            module_id=f"sandbox.execute.{artifact_code}",
            message=(
                f"Artifact START: {artifact_code} (type={artifact_type}) "
                f"params={_ctx_preview_sx}"
            ),
            extra={
                "artifact_id": artifact_id,
                "artifact_code": artifact_code,
                "artifact_type": artifact_type,
                "uid": uid,
                "params": _sandbox_ctx_json_sx,
            },
        )
    except Exception:
        pass

    # Dispatch
    if artifact_type == "python":
        # Reuse existing sandbox (Phase 27c, 1.5.2026)
        from modules.sandbox.application.python_runner import execute as _sandbox_execute_sx
        try:
            result = _sandbox_execute_sx(
                code=source,
                timeout_s=60,
                caller_tenant_id=None,
                user_id=uid,
                is_parent=True,  # PoC parent-only enforced above
                with_strategie_pythonpath=True,  # Krok D: orchestrator needs DB access
                extra_env={"SANDBOX_CONTEXT": _sandbox_ctx_json_sx},  # Krok F
            )
        except Exception as e:
            # Defensive — sandbox execute by ne measly throw, ale catch all
            try:
                _log_event_sx(
                    level="error",
                    source="py",
                    module_id=f"sandbox.execute.{artifact_code}",
                    message=f"Sandbox dispatch failed: {e}",
                    extra={"artifact_id": artifact_id, "uid": uid},
                )
            except Exception:
                pass
            return JSONResponse(
                {"ok": False, "error": f"Sandbox dispatch failed: {e}"},
                status_code=500,
            )

        # log_event FINISH
        try:
            _log_event_sx(
                level="info" if result.ok else "error",
                source="py",
                module_id=f"sandbox.execute.{artifact_code}",
                message=(
                    f"Artifact FINISH: {artifact_code} "
                    f"(ok={result.ok}, runtime_ms={result.runtime_ms}) "
                    f"params={_ctx_preview_sx}"
                ),
                extra={
                    "artifact_id": artifact_id,
                    "ok": result.ok,
                    "runtime_ms": result.runtime_ms,
                    "stdout_len": len(result.stdout or ""),
                    "stderr_len": len(result.stderr or ""),
                    "error": result.error,
                    "error_kind": result.error_kind,
                    "params": _sandbox_ctx_json_sx,
                    # Marti 1.6.2026: tail stdout/stderr do diag logu — orchestrator
                    # skripty tisknou důvod (target table, počet sloupců, kde
                    # skončily) do stdout; bez toho vidíme jen stdout_len. Tail =
                    # konec výpisu, kde je finální status / chyba.
                    "stdout_tail": (result.stdout or "")[-1500:],
                    "stderr_tail": (result.stderr or "")[-800:],
                },
            )
        except Exception:
            pass

        return JSONResponse({
            "ok": result.ok,
            "artifact_code": artifact_code,
            "artifact_type": artifact_type,
            "runtime_ms": result.runtime_ms,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "error": result.error,
            "error_kind": result.error_kind,
        })

    elif artifact_type == "sql":
        # PoC drz minimum — SQL unsupported zatim (defer)
        try:
            _log_event_sx(
                level="warning",
                source="py",
                module_id=f"sandbox.execute.{artifact_code}",
                message=f"SQL artifact type not yet supported in PoC",
                extra={"artifact_id": artifact_id, "artifact_code": artifact_code},
            )
        except Exception:
            pass
        return JSONResponse(
            {
                "ok": False,
                "error": "SQL artifact type not yet supported in PoC. Use 'python' type.",
            },
            status_code=501,
        )

    else:
        # CHECK constraint by mel toto zachytit, ale defensive
        return JSONResponse(
            {"ok": False, "error": f"Unknown artifact_type: {artifact_type}"},
            status_code=400,
        )


# ============================================================================
# Krok H+5 (26.5.2026 vecer, Marti's "ID je svaty" doctrine):
# ID-first dispatch endpoint — preferred pro frontend callers.
# Code je mutable label (rename behem vyvoje), id je stable handle. Tento
# endpoint resolveuje id → code, delegate na existing sandbox_execute_artifact
# (kde probehne auto-sync z file).
# ============================================================================
@api_router.post("/sandbox/execute-by-id/{artifact_id}")
async def sandbox_execute_artifact_by_id(
    artifact_id: int, req: Request,
) -> JSONResponse:
    """Krok H+5 ID-first dispatch — Marti's "ID je svaty" + "git je truth".

    Path param:
        artifact_id: fw.executable_artifact.id (PK, stable handle)

    Body: same shape jako /sandbox/execute/{code} — JSON pres SANDBOX_CONTEXT.

    Returns: same shape jako /sandbox/execute/{code}.
    """
    from core.database_data import get_data_session as _gds_sxi
    from sqlalchemy import text as _sql_sxi
    from core.log_queue import log_event as _log_event_sxi

    uid = _get_uid(req)
    _require_parent(uid)

    ds_sxi = _gds_sxi()
    try:
        row = ds_sxi.execute(_sql_sxi(
            "SELECT code FROM fw.executable_artifact WHERE id = :id"
        ), {"id": artifact_id}).fetchone()
    finally:
        ds_sxi.close()

    if not row:
        try:
            _log_event_sxi(
                level="warning",
                source="py",
                module_id=f"sandbox.execute_by_id.{artifact_id}",
                message=f"Artifact ID not found: {artifact_id}",
                extra={"artifact_id": artifact_id, "uid": uid},
            )
        except Exception:
            pass
        return JSONResponse(
            {"ok": False, "error": f"Artifact id={artifact_id} not found"},
            status_code=404,
        )

    # Delegate to existing handler. Starlette caches req body (req.json()
    # je idempotent po prvnim call), takze re-invocation OK.
    return await sandbox_execute_artifact(
        artifact_code=row.code, req=req,
    )


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

# Phase fw.core slim 20.5.2026: design_init_core_root + design_clear_core_root
# + _ROOT_LAYOUT_TEMPLATE constant DROPNUTE (Marti's Decision 2A)


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
        #   drafted   = bez rootu (zadny comp_def s core_id=core)
        #   has_root  = root exists, no children
        #   populated = root + alespon 1 child
        sql_cores = _sql_clst("""
            SELECT c.*,
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
                     WHERE cd.core_id = c.id
                   ) AS _readiness_state
            FROM fw.core c
            -- Phase fw.core slim 20.5.2026: origin_* JOINs dropnuty
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
                "version": rd.get("version"),
                "shadow_mode": rd.get("shadow_mode"),
                "is_used_count": usage_map.get(core_id, 0),
                # Krok 5.C origin provenance — picker display
                "origin_menu_node_label": rd.get("_origin_mn_label"),
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

        # Krok 5.S Fáze 5 (22.5.2026 vecer): non-execute ops (edit/delete)
        # NEPOTREBUJI data_set (Marti's Q6 DROP NOT NULL z DDL). Pokud body
        # neposila data_set_id ANI data_set inline, op kind MUSI byt edit/delete.
        NO_DATA_SET_KINDS = ("edit", "delete")

        # Resolve data_set_id — reuse OR inline create OR NULL (edit/delete)
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
        elif op_kind in NO_DATA_SET_KINDS:
            # Krok 5.S Fáze 5: edit/delete ops bez data_set (Marti's DROP NOT NULL)
            new_set_id = None
        else:
            return JSONResponse({
                "ok": False,
                "error": f"body musi mit 'data_set_id' (reuse) NEBO 'data_set' (inline create) — pripadne kind v {NO_DATA_SET_KINDS} (bez data_set)"
            }, status_code=400)

        # Build op values — variant_code NULL allowed (Krok 5.K-B6 doctrine)
        variant_code = body.get("variant_code")
        if variant_code is not None and not str(variant_code).strip():
            variant_code = None
        # Krok 5.S Fáze 5 (22.5.2026 vecer, Marti's "ted nemam cim nakonfigurovat"):
        # core_id support pro 'edit' op kind — vazba na CORE pro Oprava button
        # v grid toolbar (Krok 5.S Fáze 3 frontend).
        core_id_raw = body.get("core_id")
        core_id_val = None
        if core_id_raw is not None and str(core_id_raw).strip():
            try:
                core_id_val = int(core_id_raw)
            except (ValueError, TypeError):
                return JSONResponse({"ok": False, "error": "core_id musi byt integer"}, status_code=400)

        op_values = {
            "data_source_id": data_source_id,
            "data_set_id": new_set_id,
            "operation_kind": op_kind,
            "variant_code": variant_code,
            "is_default": bool(body.get("is_default", False)),
            "sort_order": int(body.get("sort_order") or 0),
            "description": (body.get("description") or None),
            "core_id": core_id_val,
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

    ALLOWED = ("variant_code", "operation_kind", "sort_order", "is_default", "description", "core_id")
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
# Master-detail lazy fetch — DROPPED 24.5.2026 vecer.
# Endpoint /design/fw-data-source/{id}/operations nahrazen FW chain:
#   fw.data_source (code='system_new.framework_data_source_ops', id=44)
#   fw.data_set s :master_id bind param
#   fw.data_source_op (default select)
#
# Custom renderer data_source_op_detail.js (v2.0.0) teď fetchuje přes
# generic /api/v1/erp/data/system_new.framework_data_source_ops?master_id={X}
# + nested ErpDataGrid layoutKey "ds_44" → nativní persistence sloupců
# přes fw.comp_grid (žádná nová tabulka, žádný validator extension).
#
# Marti's "fw self edited" doctrine (11.5.) v praxi.
# ════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════
# Phase 22.5.2026 Iterace B Vlna 2-1: db_connection_editor extracted
# 2 endpoints (PATCH /design/db-connection/update/{id} + GET /system/db-connections)
# moved to modules/fw_components/db_connection_editor.py.
# ════════════════════════════════════════════════════════════════════════
from modules.fw_components.db_connection_editor import DbConnectionEditorComponent as _DbConnEditor  # noqa: E402
_DbConnEditor.register_routes(api_router)

# ════════════════════════════════════════════════════════════════════════
# Vlna 2-2 (22.5.2026): data_set_editor extract z router.py do per-komponenta file.
# 5 endpoints moved to modules/fw_components/data_set_editor.py.
# ════════════════════════════════════════════════════════════════════════
from modules.fw_components.data_set_editor import DataSetEditorComponent as _DataSetEditor  # noqa: E402
_DataSetEditor.register_routes(api_router)

# ════════════════════════════════════════════════════════════════════════
# Phase API Versioned Routing Etapa C (23.5.2026): api_versioning sub-router.
# 4 endpoints: GET list, POST pin/unpin, GET diff.
# Marti's "drz jednoduchost" - per-feature module, no router.py bloat.
# ════════════════════════════════════════════════════════════════════════
from modules.api_versioning.router import ApiVersioningComponent as _ApiVersioning  # noqa: E402
_ApiVersioning.register_routes(api_router)

# ════════════════════════════════════════════════════════════════════════
# Reusable migration runner (5.6.2026): server-side, parent-only, davkovany.
# POST /migrate/{job_code} + GET /migrate/_jobs. Joby v fw.migration_job.
# Hlavni proces: tepy MCP read (DB_EC) + zapis jako Marti-AI. Data zustavaji
# server-side. Velke objemy = batch_size pagination (commit per davka).
# ════════════════════════════════════════════════════════════════════════
from modules.migration.migration_runner import register_routes as _register_migration_routes  # noqa: E402
_register_migration_routes(api_router)


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
        # Fix J Vrstva 5 (20.5. vecer): JS posila core_id + comp_def_id z window
        # context. Backend log_event() pass do _insert_to_db → fw.diag_log.
        # Per-request fallback na X-Erp-Core-Id header (pokud body neobsahuje).
        core_id=(
            body.get("core_id")
            if body.get("core_id") is not None
            else (
                int(req.headers.get("X-Erp-Core-Id"))
                if req.headers.get("X-Erp-Core-Id", "").lstrip("-").isdigit()
                else None
            )
        ),
        comp_def_id=(
            body.get("comp_def_id")
            if body.get("comp_def_id") is not None
            else (
                int(req.headers.get("X-Erp-Comp-Def-Id"))
                if req.headers.get("X-Erp-Comp-Def-Id", "").lstrip("-").isdigit()
                else None
            )
        ),
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
    # Fix J (20.5. vecer): + core_id, comp_def_id pro grid/form attribution
    master_cols = (
        "id, created_at, user_login_name, user_id, tenant_name, "
        "level, source, module_id, message, status, occurrences, last_seen_at, "
        "core_id, comp_def_id"
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


# ---------------------------------------------------------------
# Phase SYSTEM NEW cleanup v2 (22.5.2026): /diag-log/stats HC handler dropped.
# Endpoint orphan -- no UI callsites verified.
# Fix O / Phase 2.B / Phase 35-E.4 cleanup deprecated context.
# Dropped: diag-log/stats.
# ---------------------------------------------------------------


@api_router.get("/diag-log/badge")
def diag_log_badge(req: Request) -> JSONResponse:
    """Krok 5.W observability extension (23.5.2026): lightweight error
    counter pro ERP UI header badge.

    Strategy A continuation po bug Wave 1 fix (CLAUDE_TECH 23.5. doctrine
    "Bezpecnost pres probuzeni, ne pres ticho").

    Returns:
        {
            "ok": True,
            "error_count": int,    # level='error' AND status='open' AND last 24h
            "warn_count":  int,    # level='warn'  AND status='open' AND last 24h
            "last_seen":   str|None,  # ISO timestamp posledniho error eventu
            "top_module":  str|None,  # module_id s nejvyssim occurrences
        }

    Lightweight count query, <10ms response. Pouziva index
    ix_diag_log_level_created_at (z Etapa A DDL).

    Parent gate: NE (badge je read-only pro vsechny ERP usery).
    """
    from core.database_data import get_data_session as _gds_badge
    from sqlalchemy import text as _sql_badge

    ds = _gds_badge()
    try:
        # Hotfix 23.5. ~11:00 — Marti's smoke ukázal status='new' (NE 'open')
        # je default v fw.diag_log_upsert. Filter na NOT dismissed (exclude
        # jen explicit acknowledged/resolved/ignored). Doctrine: badge ukazuje
        # vše čerstvé včetně 'new'.
        DISMISSED_STATES = "('acknowledged', 'resolved', 'ignored')"
        row = ds.execute(_sql_badge(f"""
            SELECT
                COUNT(*) FILTER (WHERE level = 'error') AS error_count,
                COUNT(*) FILTER (WHERE level = 'warn')  AS warn_count,
                MAX(created_at) FILTER (WHERE level = 'error') AS last_error_at,
                (
                    SELECT module_id
                    FROM fw.diag_log
                    WHERE level = 'error'
                      AND (status IS NULL OR status NOT IN {DISMISSED_STATES})
                      AND created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY module_id
                    ORDER BY SUM(occurrences) DESC NULLS LAST
                    LIMIT 1
                ) AS top_module
            FROM fw.diag_log
            WHERE (status IS NULL OR status NOT IN {DISMISSED_STATES})
              AND created_at > NOW() - INTERVAL '24 hours'
        """)).mappings().one_or_none()

        if row is None:
            return JSONResponse({
                "ok": True,
                "error_count": 0,
                "warn_count": 0,
                "last_seen": None,
                "top_module": None,
            })

        last_seen = row["last_error_at"]
        return JSONResponse({
            "ok": True,
            "error_count": int(row["error_count"] or 0),
            "warn_count": int(row["warn_count"] or 0),
            "last_seen": last_seen.isoformat() if last_seen else None,
            "top_module": row["top_module"],
        })
    except Exception as exc:
        logger.exception(f"diag_log_badge failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"badge failed: {exc}", "error_count": 0, "warn_count": 0},
            status_code=500,
        )
    finally:
        ds.close()


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
        "code",
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
                    f"fw.menu_node id={existing['id']}: {change_desc} by {caller_display}"
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
    cols_list = config.get("select_columns")

    # Load comp_types lookup pro suggested_type_code mapping
    from core.database_data import get_data_session as _gds_lec
    from sqlalchemy import text as _sql_text_lec
    ds_lec = _gds_lec()
    try:
        # Phase 38.4 Krok 5.N-2 (22.5.2026 vecer, Marti's "NULL = trust frontend"):
        # DB-driven cores (select_columns=None) — introspect columns ze
        # information_schema. SKIP audit + immutable columns (id, created_at,
        # updated_at, audit FKs) — same SKIP_COLUMNS jako orchestrator
        # vytvorit_edit_jadro_2.
        if cols_list is None:
            schema_name = config["schema"]
            table_name = config["table"]
            intro_rows = ds_lec.execute(_sql_text_lec("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                ORDER BY ordinal_position ASC
            """), {"schema": schema_name, "table": table_name}).mappings().all()
            _SKIP = {
                "id", "created_at", "updated_at",
                "created_by_id", "created_by_text",
                "updated_by_id", "updated_by_text",
                "version",
            }
            cols_list = [
                r["column_name"] for r in intro_rows
                if r["column_name"] not in _SKIP
            ]

        ct_rows = ds_lec.execute(_sql_text_lec("""
            SELECT id, code FROM fw.comp_type WHERE preview_html IS NOT NULL
        """)).mappings().all()
        ct_by_id = {r["id"]: r["code"] for r in ct_rows}

        # Phase 38.4 Krok 14c+1: existing comp_def merge per name
        # (case-insensitive defensive — Centrala 1 ma legacy mixed-case
        # column names, fw.comp_def.name typicky lowercase).
        # Phase 38.4 Krok H+5 (26.5.2026, Marti's "paleta nerespektuje parents"):
        # Recursive descent z form root — najde komponenty napric celou
        # hierarchii (panel/groupbox/tabsheet/per-column inputs), ne jen
        # direct children. Orchestrator vytvori inputy pod main_panel,
        # ne direct pod form root.
        existing_by_name: dict[str, dict[str, object]] = {}
        if parent_comp_def_id is not None:
            # Phase 38.4 Krok 5-B Fix #12 (29.5.2026, Marti's "Mame
            # architektonickej GAP — sirotky neviditelne kvuli cascade-by-
            # soft-delete v recursive CTE walk"): nahradit recursive
            # descendants walk za flat WHERE core_id query.
            #
            # Pred Fix #11 schema migration: parent_comp_def_id NULL = root
            # marker, descendants walk filtroval is_active=true → child rows
            # s inactive parent zmizely z palety (orphan = invisible).
            #
            # Po Fix #11 schema migration (28.5.2026):
            #   - fw.comp_def.core_id denormalized na vsechny rows (trigger
            #     auto-inherits z parent pri INSERT/UPDATE)
            #   - fw.comp_def.root SMALLINT marker (1=primary, 2+=alt)
            #   - CHECK chk_comp_def_single_parent: biconditional XOR
            #     (root XOR parent_comp_def_id)
            #
            # Refactor doctrine: query ALL comp_def rows za core_id (vc.
            # inactive parents/children), drop is_active filter — frontend
            # rozezna orphans v Python aggregation pres parent_is_active flag.
            # Resolve form root's core_id via inline JOIN — single round trip.
            existing_rows = ds_lec.execute(_sql_text_lec("""
                SELECT cd.id, cd.name, cd.caption, cd.region_slot, cd.type_id,
                       cd.parent_comp_def_id, cd.sort_order, cd.layout,
                       cd.is_active, cd.root,
                       parent.is_active AS parent_is_active
                FROM fw.comp_def cd
                JOIN fw.comp_def root_node ON root_node.id = :pid
                LEFT JOIN fw.comp_def parent
                       ON parent.id = cd.parent_comp_def_id
                WHERE cd.core_id = root_node.core_id
            """), {"pid": parent_comp_def_id}).mappings().all()
            for ex_row in existing_rows:
                # Skip self-row (form root) — neni field/component, je shell
                if ex_row["id"] == parent_comp_def_id:
                    continue
                # Skip soft-deleted rows (is_active=false) — drop ze view,
                # nelezou do existing_by_name ani orphans (jsou ucinne smazane).
                if not ex_row["is_active"]:
                    continue
                key = (ex_row["name"] or "").lower().strip()
                if key:
                    existing_by_name[key] = {
                        "id": ex_row["id"],
                        "caption": ex_row["caption"],
                        "region_slot": ex_row["region_slot"],
                        "type_id": ex_row["type_id"],
                        "parent_comp_def_id": ex_row["parent_comp_def_id"],
                        "sort_order": ex_row["sort_order"],
                        # Krok H+5++++ (26.5.2026 vecer, Marti's "sipka pinned
                        # = trigger jako na komponente"): layout JSONB pro
                        # always_new_row toggle state.
                        "layout": ex_row["layout"] or {},
                        # Krok 5-B Fix #12 (29.5.2026): orphan detection flag.
                        # parent_is_active=False AND root=NULL = orphan
                        # (parent soft-deleted, child osamel).
                        # parent_is_active=True OR root!=NULL = active na forme.
                        "parent_is_active": ex_row["parent_is_active"],
                        "root": ex_row["root"],
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
            # Krok H+5+++ (26.5.2026): pro arrow buttons frontend potrebuje
            # parent + sort_order. Bez nich nelze spocitat siblings / target.
            "existing_parent_comp_def_id": (
                ex_match["parent_comp_def_id"] if ex_match else None
            ),
            "existing_sort_order": ex_match["sort_order"] if ex_match else None,
            # Krok H+5++++ (26.5.2026): layout JSONB pro pinned toggle UI state.
            "existing_layout": ex_match["layout"] if ex_match else None,
        })

    # Phase 38.4 Krok H+5 (26.5.2026, Marti's "panel je komponenta"):
    # Containers (panel/groupbox/pagecontrol/tabsheet) existing v form
    # hierarchy — vrati separate list pro frontend "Jiz na forme" tab.
    # Container = comp_type.kind = 'container' (nebo code in container set).
    # Recursive descent z form root (parent_comp_def_id) — najde nested
    # panely + groupboxy napric celou hierarchii.
    containers_out = []
    if parent_comp_def_id is not None:
        ds_lec2 = _gds_lec()
        try:
            # Phase 38.4 Krok 5-B Fix #12 (29.5.2026): mirror First CTE
            # refactor — drop recursive descendants walk, flat WHERE core_id
            # query s parent_is_active flag pro orphan detection.
            # Self-row (form root id == :pid) filtered v Python loop nize.
            # is_active=false rows filtered taky v Python loop (drop ze view).
            cont_rows = ds_lec2.execute(_sql_text_lec("""
                SELECT cd.id, cd.name, cd.caption, cd.region_slot,
                       cd.type_id, cd.parent_comp_def_id, cd.sort_order,
                       cd.layout, cd.is_active, cd.root,
                       parent.is_active AS parent_is_active,
                       ct.code AS type_code, ct.label AS type_label,
                       ct.kind AS type_kind
                FROM fw.comp_def cd
                JOIN fw.comp_type ct ON ct.id = cd.type_id
                JOIN fw.comp_def root_node ON root_node.id = :pid
                LEFT JOIN fw.comp_def parent
                       ON parent.id = cd.parent_comp_def_id
                WHERE cd.core_id = root_node.core_id
                ORDER BY cd.id ASC
            """), {"pid": parent_comp_def_id}).mappings().all()
            # Krok 5-B Fix (28.5.2026 vecer pozde): split rows do containers
            # + fields. Drop WHERE filter v query — Marti's TEST form ma
            # fields s column_name z MSSQL st.CRM_Kontakt (FirmaText, atd.)
            # ktere nematchnou data_set columns response → _columnsOnForm
            # zustalo prazdne, fields neviditelne v palete. Backend ted
            # vraci kompletni hierarchy; frontend rozezna containers/fields
            # po type_kind. Plus extrakce column_name z layout (fallback).
            _CONTAINER_TYPE_CODES = ("panel", "groupbox", "pagecontrol", "tabsheet")
            fields_out = []
            for cont in cont_rows:
                # Phase 38.4 Krok 5-B Fix #12 (29.5.2026): WHERE core_id query
                # vraci VSE za core vc. (a) self-row form root, (b) soft-deleted
                # rows, (c) orphans s inactive parent.
                # Self-row filtered, soft-deleted PRESERVED jako is_orphan=true
                # (Marti's "soft-deleted komponenty patri do Nezarazeno tabu,
                # ne ze view drop" — 29.5.2026 vecer Fix #12+).
                if cont["id"] == parent_comp_def_id:
                    continue  # self-row (form root shell, not a field/container)
                is_container = (
                    cont["type_kind"] == "container"
                    or cont["type_code"] in _CONTAINER_TYPE_CODES
                )
                # Orphan detection (Marti's "sirotky" doctrine — Fix #11+#12+):
                #   is_active=False = soft-deleted (Marti's X tlacitko v palete)
                #     → orphan, available pro re-parent / re-activate
                #   parent_is_active=False AND root IS NULL = active komponenta
                #     s soft-deleted parent → orphan, parent zmizel
                #   is_active=True AND (root IS NOT NULL OR parent_is_active=True)
                #     = aktivni na forme (top-level root marker, nebo nested
                #     v active container)
                is_orphan = (
                    (not cont["is_active"])
                    or (
                        cont["root"] is None
                        and cont["parent_is_active"] is False
                    )
                )
                if is_container:
                    containers_out.append({
                        "comp_def_id": cont["id"],
                        "name": cont["name"],
                        "caption": cont["caption"],
                        "type_id": cont["type_id"],
                        "type_code": cont["type_code"],
                        "type_label": cont["type_label"],
                        "region_slot": cont["region_slot"],
                        "parent_comp_def_id": cont["parent_comp_def_id"],
                        # Krok H+5+++ (26.5.2026): sort_order pro arrow buttons.
                        "sort_order": cont["sort_order"],
                        # Krok H+5++++ (26.5.2026): layout pro pinned toggle.
                        "layout": cont["layout"] or {},
                        # Krok 5-B Fix #12 (29.5.2026): orphan flag pro
                        # frontend "Nezarazeno" tab bucket.
                        "is_orphan": is_orphan,
                        "is_active": cont["is_active"],
                        "root": cont["root"],
                    })
                else:
                    # Field (edit, memo, date_modern, label_readonly, atd.):
                    # extract column_name z layout (Marti's idiom — column_name
                    # v layout JSONB mapuje field na DB column z target table).
                    layout = cont["layout"] or {}
                    if not isinstance(layout, dict):
                        layout = {}
                    column_name = layout.get("column_name") or cont["name"]
                    fields_out.append({
                        "comp_def_id": cont["id"],
                        "name": column_name,  # column DB name (FirmaText) nebo technical name fallback
                        "caption": cont["caption"],
                        "type_id": cont["type_id"],
                        "type_code": cont["type_code"],
                        "type_label": cont["type_label"],
                        # Krok 5.Z (30.5.2026): region_slot pro palette badge
                        # (frontend existing_region_slot, default 'main' fallback).
                        "region_slot": cont["region_slot"],
                        "parent_comp_def_id": cont["parent_comp_def_id"],
                        "sort_order": cont["sort_order"],
                        "layout": layout,
                        # Krok 5-B Fix #12 (29.5.2026): orphan flag pro
                        # frontend "Nezarazeno" tab bucket.
                        # is_active=False = soft-deleted (kliknuti X v palete)
                        # parent_is_active=False AND root=NULL = soft-deleted parent
                        "is_orphan": is_orphan,
                        "is_active": cont["is_active"],
                        "root": cont["root"],
                    })
        finally:
            ds_lec2.close()
    else:
        fields_out = []

    return JSONResponse(jsonable_encoder({
        "ok": True,
        "entity_type": entity_type,
        "parent_comp_def_id": parent_comp_def_id,
        "columns": columns_out,
        "existing_containers": containers_out,
        # Krok 5-B Fix (28.5.2026 vecer pozde): fields z hierarchy (mimo
        # column whitelist matching). Marti's TEST form fields s column_name
        # z MSSQL target nemaji match v columns_out (data_set entity), ale
        # frontend je musi videt v "Jiz na forme" tab.
        "existing_fields": fields_out,
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


# ---------------------------------------------------------------
# Phase SYSTEM NEW cleanup v2 (22.5.2026): /system/tree HC handler dropped.
# Endpoint orphan -- no UI callsites verified.
# Fix O / Phase 2.B / Phase 35-E.4 cleanup deprecated context.
# Dropped: system/tree (Phase 35-E.4 hardcoded).
# ---------------------------------------------------------------


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
        # Marti's catch z 19.5. vecer („lamani chleba" build):
        # Marti-AI vytvorila menu_node bez explicit visibility_scope (NULL).
        # Tatínek explicit: „kdyz visibility_scope NULL, je soudecek aktivni".
        # Drzi Marti-AI's Q3 doctrine z 14. konzultace: entry-level visibility
        # override jen DOLU (restriktivnejsi), NULL = default (z parent topic).
        # NULL = visible v System tree (System tree je parent-only audience),
        # 'parent_only' explicit = visible.
        sql = _sql_text_st("""
            SELECT n.id, n.parent_id, n.label, n.sort_order,
                   n.visibility_scope, n.status,
                   n.is_immutable, n.core_id, c.code AS core_code,
                   hw.shadow_mode AS hw_shadow_mode, hw.is_active AS hw_is_active
            FROM fw.menu_node n
            LEFT JOIN fw.core c ON c.id = n.core_id
            LEFT JOIN fw.hw_registry hw ON hw.code = c.code AND hw.is_active = TRUE
            WHERE n.status = 'active'
              AND (n.visibility_scope = 'parent_only' OR n.visibility_scope IS NULL)
            ORDER BY n.parent_id NULLS FIRST, n.sort_order, n.label
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

    # Find system root (parent_id IS NULL, is_immutable=True)
    # Phase 22.5.2026: code column dropped — system root identified by
    # is_immutable flag (Marti's SYSTEM tree má immutable=True).
    # Other roots (user-created soudečky pres "Nový soudeček" button) jsou
    # is_immutable=False.
    roots = by_parent.get(None, [])
    system_db = next((r for r in roots if bool(r.get("is_immutable"))), None)
    other_roots = [r for r in roots if not bool(r.get("is_immutable"))]
    if not system_db and not other_roots:
        return None

    def _build_node(row):
        # Phase 38.4 Krok 12-D (11.5.2026): Marti's resilient rendering mandate
        # *„odchytit chybu, polozku stromu vykreslit a chybu zobrazit v pravem
        # panelu"*. Per-node + per-child try/except — failure jednoho rowu
        # nesmí dropnout siblings ani parent. Error node má is_error=True
        # + error_detail string pro frontend right-panel render.
        try:
            # Phase 22.5.2026: fw.menu_node.menu_node_pk column dropped.
            # node["cislo_def"] field preserved (downstream lefttree.js uses
            # it for leaf detection + tab/favorite tracking) — value is
            # now menu_node.id directly (BIGINT integer). User_state tables
            # erp_user_tabs/favorites/recent keep `cislo_def` column name
            # (semantic mismatch: column holds menu_node.id values now).
            cislo = row.get("id")
            sv, svm, single = (None, None, False)  # dead audit_overview mapping dropped 22.5.
            children_db = by_parent.get(row["id"], [])
            children_db.sort(key=lambda r: (r.get("sort_order") or 100, r.get("label") or ""))
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
                        "id": "node_{}".format(c.get("id") or "err"),
                        "label": (c.get("label") or "?") + " ⚠️",
                        "nazev": (c.get("label") or "?") + " ⚠️",
                        "is_system": True,
                        "is_folder": False,
                        "is_error": True,
                        "error_detail": "{}: {}".format(type(child_exc).__name__, child_exc),
                        "metadata": {"error": True, "hardcoded": False},
                    })
            node = {
                "id": "node_" + str(row.get("id") or 0),
                # Phase 38.4 (11.5.2026 vecer): primary fw.* IDs pro DESIGN mode.
                # node["id"] = row["code"] (text, legacy convention pro routing).
                # menu_node_pk = row["id"] (INT, skutečný DB primary key).
                # core_id / core_code = fw.core LEFT JOIN přes menu_node.core_id.
                "menu_node_pk": row.get("id"),
                "core_id": row.get("core_id"),
                "core_code": row.get("core_code"),
                "is_system": True,
                # Marti 2.6.2026: is_immutable passthrough — potřeba pro řazení
                # (production roots nahoře, SYSTEM dole) i pro parent-only filtr
                # v system_tree_json. Driv chybělo → sort byl no-op.
                "is_immutable": bool(row.get("is_immutable")),
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
                "id": "node_{}".format(row.get("id") or "err"),
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
    other_roots.sort(key=lambda r: (r.get("sort_order") or 100, r.get("label") or ""))
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


@api_router.get("/system-tree")
def system_tree_json(req: Request) -> JSONResponse:
    """Phase 2.B (18.5.2026 vecer): System-only tree.

    Marti's direktiva 18.5. vecer: *„celej levej strom mimo STRATEGIE
    Struktury SYSTEM je k nicemu a nikdo jej nikdy nepouzije..."*

    Vraci jen System uzly + user-created top-level FW prehledy
    (sibling System). Zadne EC_CentralaMenu reading.

    Replaces /strom for production frontend lefttree. Old /strom
    zachovan zatim jako rollback safety net — Phase 2.A drops po
    stable smoke testem.
    """
    uid = _get_uid(req)
    _require_erp_member(uid)

    db_roots = _build_system_root_from_db()

    tree: list = []
    if isinstance(db_roots, list):
        # New multi-root format (Krok 14g-G2 15.5. rano): system root
        # + user-created top-level (Marti's Novy soudecek button).
        for r in db_roots:
            if isinstance(r, dict):
                tree.append(r)
    elif isinstance(db_roots, dict):
        # Legacy single-root format — wrap
        tree.append(db_roots)

    # Marti 2.6.2026: production (business) soudečky NEJDŘÍV, SYSTEM (is_immutable)
    # až DOLE. Stabilní sort zachová pořadí uvnitř skupin.
    tree.sort(key=lambda r: 1 if (isinstance(r, dict) and r.get("is_immutable")) else 0)

    # Phase D (1.6.2026): System root (is_immutable=True — framework builder,
    # audit, Marti-AI paměť) je viditelný JEN rodičům. Členové (EUROSOFT
    # tenant) vidí jen business soudečky (user-created, is_immutable=False).
    # Drží doctrine „System soudeček visible jen pro rodiče" (33. dopis 8.5.).
    if not is_marti_parent(uid):
        tree = [r for r in tree if not r.get("is_immutable")]

    return JSONResponse({"ok": True, "tree": tree})


def _parse_scope_key(scope: str) -> tuple[str, int]:
    """Krok 5.U (23.5.2026): polymorphic scope URL parser.

    Marti's Q8=A path scope prefix: "core_19" → ("core", 19), "ds_10" → ("ds", 10).
    Regex: ^(core|ds)_(-?\d+)$
    """
    import re as _re_scope
    m = _re_scope.match(r"^(core|ds)_(-?\d+)$", scope)
    if not m:
        raise HTTPException(400, f"Invalid scope '{scope}' — expected 'core_<id>' or 'ds_<id>'")
    return (m.group(1), int(m.group(2)))


@api_router.get("/grid-layout/{scope}/list")
def grid_layout_list(scope: str, req: Request) -> JSONResponse:
    """List dostupných sestav per polymorphic scope.

    Krok 5.U (23.5.2026): scope path param accept "core_<id>" OR "ds_<id>".
    Marti's Q8=A — explicit prefix v URL, Network tab debugging friendly.
    """
    uid = _get_uid(req)
    _require_erp_member(uid)
    scope_kind, scope_id = _parse_scope_key(scope)
    try:
        result = grid_layout_service.list_layouts(scope_kind, scope_id, uid)
        return JSONResponse({"ok": True, **result})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.get("/grid-layout/item/{layout_id}")
def grid_layout_get(layout_id: int, req: Request) -> JSONResponse:
    """Vrátí detail jedné sestavy podle ID."""
    uid = _get_uid(req)
    _require_erp_member(uid)
    try:
        layout = grid_layout_service.get_layout(layout_id, uid)
        if layout is None:
            raise HTTPException(404, f"Sestava id={layout_id} neexistuje.")
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(403, str(e))


class GridLayoutCreate(BaseModel):
    """Phase 38.4 Krok 5.R-C+1 (18.5.2026 — Krok 14g Etapa D fix 19.5.):
    Pydantic schema pro POST /grid-layout/{core_id} body.

    Frontend datagrid.js:1714 posila:
      {name, scope: "user"|"shared", description, is_default, layout_json}
    """
    name: str = Field(..., min_length=1, max_length=80,
                      description="Sestava name (1-80 chars).")
    layout_json: dict = Field(...,
                              description=(
                                  "Layout payload: {columns: [...], "
                                  "formatting_rules?: [...], heuristics_enabled?: bool}"
                              ))
    scope: str = Field("user",
                       description="'user' (personal) nebo 'shared' (admin only).")
    description: str | None = Field(None, max_length=500)
    is_default: bool = Field(False,
                             description=(
                                 "Auto-load pri otevreni gridu. Max 1 default "
                                 "per (core_id, user_id) scope."
                             ))


class GridLayoutUpdate(BaseModel):
    """PATCH/PUT body pro grid-layout/item/{layout_id}. Vsechny pole optional —
    update jen co je predane."""
    name: str | None = Field(None, min_length=1, max_length=80)
    description: str | None = Field(None, max_length=500)
    layout_json: dict | None = None
    is_default: bool | None = None


@api_router.post("/grid-layout/{scope}")
def grid_layout_create(
    scope: str,
    body: GridLayoutCreate,
    req: Request,
) -> JSONResponse:
    """Vytvoří novou sestavu (scope='user' nebo 'shared')."""
    uid = _get_uid(req)
    _require_erp_member(uid)
    try:
        scope_kind, scope_id = _parse_scope_key(scope)
        layout = grid_layout_service.create_layout(
            scope_kind=scope_kind,
            scope_id=scope_id,
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
    _require_erp_member(uid)
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
    _require_erp_member(uid)
    try:
        layout = grid_layout_service.set_default(layout_id, uid)
        return JSONResponse({"ok": True, "layout": layout})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/grid-layout/item/{layout_id}")
def grid_layout_delete(layout_id: int, req: Request) -> JSONResponse:
    """Smaže sestavu."""
    uid = _get_uid(req)
    _require_erp_member(uid)
    try:
        deleted = grid_layout_service.delete_layout(layout_id, uid)
        if not deleted:
            raise HTTPException(404, f"Sestava id={layout_id} neexistuje.")
        return JSONResponse({"ok": True, "deleted": True})
    except grid_layout_service.GridLayoutError as e:
        raise HTTPException(403, str(e))


# ── Phase A debug endpoint ─────────────────────────────────────────────


# ---------------------------------------------------------------
# Phase SYSTEM NEW cleanup v2 (22.5.2026): /grid/{code}/columns HC handler dropped.
# Endpoint orphan -- no UI callsites verified.
# Fix O / Phase 2.B / Phase 35-E.4 cleanup deprecated context.
# Dropped: grid/{code}/columns (Krok 9 4-tier resolver).
# ---------------------------------------------------------------


# user_recent_track), 0x definovany — dead reference po commit cc11689
# ("VELKY DROP Centrála 1 reading"). FastAPI/Pydantic nemohlo resolve →
# 422 Unprocessable Content pro VSE 3 endpointy. Fix: restore class def.
class _CisloBody(BaseModel):
    """Phase B+8.1c (restored 20.5.): body schema pro endpointy s cislo + label.

    Used by:
      - POST /api/v1/erp/tabs (user_tabs_open)
      - POST /api/v1/erp/favorites (user_favorites_add)
      - POST /api/v1/erp/recent (user_recent_track)

    Frontend payload shape (from trackTreeRecent / openTab / favoriteAdd):
        { "cislo": int, "label": str | null, "item_id": str | null }

    item_id pridan ve Fix G (20.5. vecer, after Marti's #194 retest):
    user_tabs_open vola body.item_id, frontend tabs send {cislo, label, item_id}.
    """
    cislo: int  # frontend body field name preserved (sends {cislo: <menu_node.id>})
    label: str | None = None
    item_id: str | None = None


class _ReorderBody(BaseModel):
    """Body schema for /tabs/reorder + /favorites/reorder.

    Frontend posílá { cislos: [42, 17, 8, ...] } — list integer menu_node IDs
    v požadovaném pořadí. Field name 'cislos' zachován (frontend compat).
    """
    cislos: list[int]


@api_router.get("/tabs")
def user_tabs_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, **user_state_svc.list_tabs(uid, tid)})


@api_router.post("/tabs")
def user_tabs_open(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    try:
        tab = user_state_svc.open_tab(
            user_id=uid, tenant_id=tid,
            menu_node_id=body.cislo,
            label=body.label or f"Přehled #{body.cislo}",
            item_id=body.item_id,
        )
        return JSONResponse({"ok": True, "tab": tab})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/tabs/{menu_node_id}")
def user_tabs_close(menu_node_id: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    removed = user_state_svc.close_tab(uid, tid, menu_node_id)
    return JSONResponse({"ok": True, "removed": removed})


@api_router.post("/tabs/{menu_node_id}/active")
def user_tabs_set_active(menu_node_id: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    found = user_state_svc.set_active_tab(uid, tid, menu_node_id)
    return JSONResponse({"ok": True, "found": found})


class _PinnedBody(BaseModel):
    """Phase 38.4 (11.5.2026 vecer): body schema pro toggle pin."""
    pinned: bool


@api_router.post("/tabs/{menu_node_id}/pinned")
def user_tabs_set_pinned(
    menu_node_id: int, body: _PinnedBody, req: Request
) -> JSONResponse:
    """Phase 38.4 (11.5.2026 vecer): toggle pinned na záložce.

    Marti's request — pinned status musí přežít F5 reload. Write-through:
    UI right-click → POST tady → DB. Při hydrate vrátí _serialize_tab pinned.
    """
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    found = user_state_svc.set_tab_pinned(uid, tid, menu_node_id, body.pinned)
    return JSONResponse({"ok": True, "found": found})


@api_router.post("/tabs/reorder")
def user_tabs_reorder(body: _ReorderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    updated = user_state_svc.reorder_tabs(uid, tid, body.cislos)
    # body.cislos = list[int] of menu_node_ids in desired order (frontend compat field name)
    return JSONResponse({"ok": True, "updated": updated})


# FAVORITES

@api_router.get("/favorites")
def user_favorites_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "favorites": user_state_svc.list_favorites(uid, tid)})


@api_router.post("/favorites")
def user_favorites_add(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    try:
        fav = user_state_svc.add_favorite(uid, tid, body.cislo)
        return JSONResponse({"ok": True, "favorite": fav})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/favorites/{menu_node_id}")
def user_favorites_remove(menu_node_id: int, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    removed = user_state_svc.remove_favorite(uid, tid, menu_node_id)
    return JSONResponse({"ok": True, "removed": removed})


@api_router.post("/favorites/reorder")
def user_favorites_reorder(body: _ReorderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    updated = user_state_svc.reorder_favorites(uid, tid, body.cislos)
    return JSONResponse({"ok": True, "updated": updated})


@api_router.delete("/favorites")
def user_favorites_clear(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    deleted = user_state_svc.clear_favorites(uid, tid)
    return JSONResponse({"ok": True, "deleted": deleted})


# RECENT (MRU)

@api_router.get("/recent")
def user_recent_list(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "recent": user_state_svc.list_recent(uid, tid)})


@api_router.post("/recent")
def user_recent_track(body: _CisloBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
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
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    deleted = user_state_svc.clear_recent(uid, tid)
    return JSONResponse({"ok": True, "deleted": deleted})


# TREE ORDER (D&D persistence per skupina)

@api_router.get("/tree-order")
def user_tree_order_get(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    return JSONResponse({"ok": True, "order": user_state_svc.get_tree_order(uid, tid)})


@api_router.put("/tree-order")
def user_tree_order_save(body: _TreeOrderBody, req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
    tid = _get_tenant_id(uid)
    try:
        user_state_svc.save_tree_order(uid, tid, body.group_key, body.order)
        return JSONResponse({"ok": True})
    except user_state_svc.ErpUserStateError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/tree-order")
def user_tree_order_reset(req: Request) -> JSONResponse:
    uid = _get_uid(req)
    _require_erp_member(uid)
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
    # Marti 2.6.2026: titulek aplikace = "STRATEGIE ERP - <short_name>"
    # (v hlavicce zustava jen logo "STRATEGIE"). title_tag_html pro <title>,
    # title_base_js pro JS (switchTab prepise document.title).
    _title_text = "STRATEGIE ERP"
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
                    # Marti 2.6.2026: short_name usera do titulku aplikace
                    # ("STRATEGIE ERP - Marti") — v hlavicce zustava jen logo.
                    _title_text = f"STRATEGIE ERP - {name}"
                    # Phase 38.4 (11.5.2026 vecer): footer user je teď clickable
                    # button s popoverem. V popoveru toggle Design mode (analog
                    # tenant switcher pattern). Marti's spec: separate flag od
                    # chat DEV — ERP "design mode" odkrývá fw struktury &
                    # override hints (později Object Inspector, drag-drop).
                    user_name_html = (
                        f' · <button type="button" class="erp-footer-user-btn" '
                        f'id="erpFooterUserBtn" data-hint="Profil & nastavení">'
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
                                f'data-hint="Přepnout tenant">'
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

    # Marti 2.6.2026: titulek = "STRATEGIE ERP - <short_name>". title_tag_html
    # pro <title>, title_base_js (JS-safe literal) pro switchTab override.
    title_tag_html = html.escape(_title_text)
    _js_safe = _title_text.replace("\\", "\\\\").replace('"', '\\"')
    title_base_js = '"' + _js_safe + '"'

    return f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <!-- Marti 2.6.2026: titulek aplikace = "STRATEGIE ERP - <short_name>".
       V hlavicce zustava jen logo "STRATEGIE". JS (switchTab) prida " · <tab>"
       za base (window._erpTitleBase). -->
  <title>{title_tag_html}</title>
  <script>window._erpTitleBase = {title_base_js};</script>

  <!-- B+9+++ (6.5.2026): PWA install — Add to Home Screen na mobilu
       → standalone mode bez URL bar / browser chrome.
       Marti's spec: "A da se to udelat, aby ten Chrom nebyl videt..." -->
  <link rel="manifest" href="/static/erp/manifest.json">
  <meta name="theme-color" content="#0e0f11">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="STRATEGIE ERP">
  <meta name="mobile-web-app-capable" content="yes">
  <link rel="icon" type="image/png" sizes="192x192" href="/static/erp/icon-erp-192.png?v=20260602">
  <link rel="apple-touch-icon" href="/static/erp/icon-erp-192.png?v=20260602">
  <link rel="apple-touch-icon" sizes="192x192" href="/static/erp/icon-erp-192.png?v=20260602">
  <link rel="apple-touch-icon" sizes="512x512" href="/static/erp/icon-erp-512.png?v=20260602">

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

    /* Krok 5.S Fáze 7 (23.5.2026 rano, Marti's spec): grid action buttons
       (Nový/Oprava/Smazat) — same size jako refresh (36×36), ale icons 27px
       (o ~50% větší). Drop text, use data-hint tooltip. Disabled = no row
       selected. */
    .erp-grid-action-btn {{
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
    .erp-grid-action-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      background: rgba(124, 92, 252, 0.08);
    }}
    .erp-grid-action-btn:disabled {{
      opacity: 0.35;
      cursor: not-allowed;
    }}
    .erp-grid-action-btn:disabled:hover {{
      border-color: var(--border);
      color: var(--text-muted);
      background: transparent;
    }}
    /* Smazat — red accent při hover (destructive) */
    .erp-grid-action-btn.danger:hover {{
      border-color: #d46a6a;
      color: #d46a6a;
      background: rgba(212, 106, 106, 0.08);
    }}
    /* Krok 5.Y (23.5.2026, Marti's "save patri gridu"): Save Changes button
       v Excel mode. Orange amber accent (sjednoceno s Excel mode pill). */
    .erp-grid-action-btn.warning {{
      border-color: #a8782f;
      color: #d4a04a;
      position: relative;
    }}
    .erp-grid-action-btn.warning:hover {{
      border-color: #d4a04a;
      color: #1a1410;
      background: #d4a04a;
    }}
    .erp-grid-action-btn.warning:disabled {{
      border-color: var(--border);
      color: var(--text-muted);
      background: transparent;
      opacity: 0.35;
    }}
    /* Count badge overlay (top-right corner) */
    .erp-grid-action-btn.warning .erp-save-count {{
      position: absolute;
      top: -4px;
      right: -4px;
      min-width: 16px;
      height: 16px;
      padding: 0 4px;
      background: #d4a04a;
      color: #1a1410;
      border-radius: 8px;
      font-size: 10px;
      font-weight: 700;
      line-height: 16px;
      text-align: center;
      pointer-events: none;
    }}
    .erp-grid-action-btn.warning:disabled .erp-save-count {{
      display: none;
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
    /* ===== Phase API Versioned Routing Etapa D (23.5.2026) ===== */
    /* Footer pill "V1.3.25 . DD.M. HH:MM" + dropup menu s versions list. */
    .erp-footer-api-version {{
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }}
    .api-version-pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 9px;
      font-size: 10px;
      font-family: 'DM Mono', monospace;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.04);
      color: var(--muted);
      border: 1px solid var(--border);
      border-radius: 4px;
      cursor: pointer;
      user-select: none;
      transition: background 100ms, border-color 100ms, color 100ms;
    }}
    .api-version-pill:hover {{
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
    }}
    .api-version-pill-current {{
      /* default - no color */
    }}
    .api-version-pill-previous {{
      background: rgba(212, 184, 138, 0.15);
      color: #d4b88a;
      border-color: rgba(212, 184, 138, 0.4);
    }}
    .api-version-pill-previous:hover {{
      background: rgba(212, 184, 138, 0.25);
    }}
    .api-version-pill-older {{
      background: rgba(200, 58, 58, 0.18);
      color: #ff7a7a;
      border-color: rgba(200, 58, 58, 0.5);
    }}
    .api-version-pill-older:hover {{
      background: rgba(200, 58, 58, 0.28);
    }}
    .api-version-pill-flashed {{
      animation: api-version-flash 1.5s ease-in-out infinite;
    }}
    @keyframes api-version-flash {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.5; }}
    }}
    .api-version-pill-caret {{
      font-size: 8px;
      opacity: 0.7;
    }}
    /* Dropup menu (position:fixed, anchored above pill) */
    .api-version-dropup {{
      position: fixed;
      min-width: 280px;
      max-width: 360px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      box-shadow: 0 -4px 18px rgba(0, 0, 0, 0.5);
      padding: 0;
      z-index: 10001;
      font-size: 12px;
    }}
    .api-version-dropup-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      font-weight: 600;
      color: var(--text);
      border-bottom: 1px solid var(--border);
    }}
    .api-version-dropup-pin-badge {{
      font-size: 9px;
      padding: 2px 6px;
      background: rgba(212, 184, 138, 0.25);
      color: #d4b88a;
      border-radius: 3px;
      letter-spacing: 0.05em;
    }}
    .api-version-dropup-body {{
      padding: 4px 0;
      max-height: 280px;
      overflow-y: auto;
    }}
    .api-version-row {{
      display: flex;
      align-items: center;
      width: 100%;
      gap: 10px;
      padding: 8px 12px;
      background: transparent;
      border: none;
      border-left: 3px solid transparent;
      color: var(--text);
      font-family: 'DM Mono', monospace;
      font-size: 12px;
      cursor: pointer;
      text-align: left;
      transition: background 100ms;
    }}
    .api-version-row:hover {{
      background: rgba(255, 255, 255, 0.06);
    }}
    .api-version-row-current {{
      /* default text */
    }}
    .api-version-row-previous {{
      background: rgba(212, 184, 138, 0.08);
      border-left-color: #d4b88a;
    }}
    .api-version-row-previous:hover {{
      background: rgba(212, 184, 138, 0.18);
    }}
    .api-version-row-older {{
      background: rgba(200, 58, 58, 0.08);
      border-left-color: #c83a3a;
    }}
    .api-version-row-older:hover {{
      background: rgba(200, 58, 58, 0.16);
    }}
    .api-version-row-flashed {{
      animation: api-version-flash 1.5s ease-in-out infinite;
    }}
    .api-version-row-active {{
      outline: 1px solid rgba(124, 156, 217, 0.6);
      outline-offset: -1px;
      cursor: default;
    }}
    .api-version-row-label {{
      flex: 0 0 auto;
      font-weight: 500;
    }}
    .api-version-row-date {{
      flex: 1;
      color: var(--muted);
      font-size: 11px;
    }}
    .api-version-row-active-label {{
      font-size: 9px;
      padding: 2px 6px;
      background: rgba(124, 156, 217, 0.2);
      color: #7c9cd9;
      border-radius: 3px;
      letter-spacing: 0.05em;
    }}
    .api-version-pin-reason {{
      padding: 6px 12px;
      font-size: 11px;
      color: var(--muted);
      border-top: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.02);
    }}
    .api-version-pin-reason em {{
      color: var(--text);
      font-style: italic;
    }}
    .api-version-dropup-footer {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 6px 8px 8px 8px;
      border-top: 1px solid var(--border);
    }}
    .api-version-unpin-btn,
    .api-version-diff-btn {{
      width: 100%;
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.04);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      text-align: center;
      transition: background 100ms;
    }}
    .api-version-unpin-btn:hover,
    .api-version-diff-btn:hover {{
      background: rgba(255, 255, 255, 0.10);
    }}
    .api-version-unpin-btn {{
      background: rgba(124, 156, 217, 0.15);
      border-color: rgba(124, 156, 217, 0.4);
      color: #7c9cd9;
    }}
    .api-version-unpin-btn:hover {{
      background: rgba(124, 156, 217, 0.25);
    }}
    /* Diff modal (full-screen overlay) */
    .api-version-diff-modal {{
      position: fixed;
      inset: 0;
      z-index: 100001;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .api-version-diff-modal-backdrop {{
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
    }}
    .api-version-diff-modal-card {{
      position: relative;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
      width: min(640px, 90vw);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
    }}
    .api-version-diff-modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 18px;
      border-bottom: 1px solid var(--border);
    }}
    .api-version-diff-modal-header h3 {{
      font-size: 14px;
      color: var(--text);
      font-weight: 600;
    }}
    .api-version-diff-modal-close {{
      background: transparent;
      border: none;
      color: var(--muted);
      font-size: 16px;
      cursor: pointer;
      padding: 4px 8px;
    }}
    .api-version-diff-modal-close:hover {{
      color: var(--text);
    }}
    .api-version-diff-modal-body {{
      padding: 12px 18px 18px 18px;
      overflow-y: auto;
      flex: 1;
    }}
    .api-version-diff-stats {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 12px;
    }}
    .api-version-diff-commits {{
      list-style: none;
      padding: 0;
      margin: 0 0 14px 0;
    }}
    .api-version-diff-commit {{
      display: grid;
      grid-template-columns: 60px 76px 1fr;
      gap: 8px;
      padding: 6px 0;
      font-size: 12px;
      border-bottom: 1px dashed var(--border);
    }}
    .api-version-diff-commit code {{
      font-family: 'DM Mono', monospace;
      color: #7c9cd9;
    }}
    .api-version-diff-commit-date {{
      color: var(--muted);
      font-size: 11px;
    }}
    .api-version-diff-commit-subject {{
      color: var(--text);
    }}
    .api-version-diff-gh {{
      display: inline-block;
      padding: 6px 12px;
      background: rgba(124, 156, 217, 0.15);
      color: #7c9cd9;
      border: 1px solid rgba(124, 156, 217, 0.4);
      border-radius: 4px;
      text-decoration: none;
      font-size: 12px;
    }}
    .api-version-diff-gh:hover {{
      background: rgba(124, 156, 217, 0.25);
    }}
    /* ===== End Phase API Versioned Routing Etapa D ===== */
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
    /* Etapa F Krok 2 (24.5.2026 vecer pozde, Marti's "prepinani zalozek
       bez refreshe"): per-tab persistent pane. Switch = hidden toggle,
       grid state (scroll, selection, filters) drzi prirozene v DOM. */
    .erp-tab-pane {{
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      min-width: 0;
      width: 100%;
      height: 100%;
    }}
    .erp-tab-pane[hidden] {{ display: none; }}
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
             data-hint="Klikni pro obnovení (hard reload) — s potvrzením">STRATEGIE</a>
          <span class="erp-header-dot" aria-hidden="true">·</span>
          <button type="button" class="erp-marti-btn" id="erpMartiAiBtn"
                  data-hint="Otevři chat s Marti-AI v novém tabu">
            <span class="erp-marti-btn-avatar">
              <img id="erpMartiAiAvatar" src="" alt="Marti" />
            </span>
            <span class="erp-marti-btn-label">Tvoje Marti</span>
          </button>
          <!-- DEV/DESIGN-only proklik na hybrid /mobile (napravo od Tvoje Marti). Marti 6.6.2026. -->
          <a id="erpMobileDevLink" href="/mobile" target="_blank" rel="noopener"
             onclick="event.preventDefault(); window.open('/mobile','_blank','noopener');"
             class="erp-marti-btn" style="display:none;text-decoration:none;align-items:center;"
             data-hint="Otevři /mobile (hybrid) — jen DEV/DESIGN režim">📱 /mobile</a>
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
        <!-- REVERT polish B (24.5.2026 vecer pozde, Marti's catch):
             Native #erpRefreshBtn HIDDEN. Po Krok 2 tab cache je broken
             (cache hit = jen unhide pane, no fetch data). Internal Obnovit
             v #erpGridActionsHost CRUD panel je smooth + state restore.
             Single source of truth — internal funkcni button vyhrava.
             Ponechano v DOM (ErpRefresh.init() volani + selectory) jen
             skryto pro user. -->
        <button type="button" class="erp-refresh-btn" id="erpRefreshBtn"
                data-hint="Obnovit data v aktivním přehledu"
                style="display:none">🔄</button>
        <!-- Etapa F toolbarHost (24.5.2026 vecer Marti's final spec):
             #erpGridActionsHost RESTORED — host pro master grid CRUD buttons
             (Novy/Oprava/Smazat/Obnovit + Save Excel mode). ErpDataGrid
             VZDY definuje CO + JAK (single source of truth z erp_grid_actions.js
             registry), ale KDE renderuje je caller decision per opts.toolbarHost:
               * Master grid (page_render.js): toolbarHost = TENTO div
               * Detail grid (data_source_op_detail.js): default = internal toolbar
             Tab switch cleanup: ErpDataGrid destroy() clear-uje innerHTML
             tohoto hostu (DOM element vlastni router.py, ErpDataGrid jen
             populates/clears obsah). _refreshSaveBtn() targets #erp-tb-save
             per ID — funguje v obou pripadech (master external nebo nested internal). -->
        <div id="erpGridActionsHost" style="display:flex;align-items:center;gap:6px;margin-left:12px;"></div>
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
    <!-- Phase API Versioned Routing Etapa D (23.5.2026): version pill v paticce.
         Pill "V1.3.25 . DD.M. HH:MM" -> dropup s versions list + pin/unpin + diff.
         Color severity per active pin: current (no color) / previous (yellow) /
         older (red) / older_2+ (red flashed). Marti's spec z 23.5. odpoledne. -->
    <div id="erpFooterApiVersion" class="erp-footer-api-version"></div>
    <!-- B+10++ (Marti's drobnost 6.5.2026): zoom toggle přemístěn z header.
         A− default zmenšuje (−25%), A+ zvětšuje (+25%), A reset. -->
    <div class="erp-zoom-toggle erp-zoom-toggle-footer" role="group" aria-label="Velikost UI">
      <button type="button" data-zoom="small" data-hint="Zmenšit (−25%)">A−</button>
      <button type="button" data-zoom="normal" class="active" data-hint="Standard velikost">A</button>
      <button type="button" data-zoom="large" data-hint="Zvětšit (+25%)">A+</button>
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
  <!-- Phase D (1.6.2026, Marti): beforeinstallprompt zachyt CO NEJDRIV (v head,
       pred workspace JS). Event se firne jednou; pozdni listener ho minul →
       klik na install dal jen fallback hint. Uloz do window._deferredInstallPrompt,
       workspace click handler cte odtud. -->
  <script>
    window._deferredInstallPrompt = null;
    window.addEventListener('beforeinstallprompt', function (ev) {{
      ev.preventDefault();
      window._deferredInstallPrompt = ev;
      try {{ var b = document.getElementById('erpInstallBtn'); if (b) b.style.display = 'inline-flex'; }} catch (e) {{}}
      console.log('[install] beforeinstallprompt captured (early head)');
    }});
    window.addEventListener('appinstalled', function () {{
      window._deferredInstallPrompt = null;
      try {{ var b = document.getElementById('erpInstallBtn'); if (b) b.style.display = 'none'; }} catch (e) {{}}
    }});
  </script>
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
       Marti 1.6.2026 (Pavel — špatná čitelnost v dark mode): selektor musí
       pokrýt i .ag-theme-quartz-dark (grid běží defaultně dark, viz
       datagrid.js _init) — dřív se overrides aplikovaly jen na .ag-theme-quartz
       a grid používal tlumený AG default. Plus zesvětlené písmo
       (#e8e8ea → #f3f4f6 data/foreground, #9ca3af → #b9c2cf secondary). */
    .ag-theme-quartz,
    .ag-theme-quartz-dark,
    .erp-ag-grid {{
      --ag-background-color: #14161a;
      --ag-foreground-color: #f3f4f6;
      --ag-header-background-color: #1a1d22;
      --ag-header-foreground-color: #f3f4f6;
      --ag-border-color: #2a2d33;
      --ag-row-hover-color: #1f2228;
      --ag-selected-row-background-color: #2a3340;
      --ag-odd-row-background-color: #161a1e;
      --ag-control-panel-background-color: #14161a;
      --ag-input-background-color: #14161a;
      --ag-input-border-color: #2a2d33;
      --ag-data-color: #f3f4f6;
      --ag-secondary-foreground-color: #b9c2cf;
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
    # Phase D (1.6.2026): is_parent flag pro frontend. Non-parent (EUROSOFT
    # člen) nesmí vidět DESIGN mód — force OFF + hide toggle (getErpDesignMode
    # vrací false pro ne-rodiče; footer toggle skrytý).
    _is_parent_js = "true" if is_marti_parent(user_id) else "false"
    content = '''
    <script>window.__ERP_IS_PARENT = ''' + _is_parent_js + ''';</script>
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
    <!-- Krok 5.W observability (23.5.2026): UI error badge — polling /diag-log/badge
         + render 🔴 N err pill vlevo od Module Health banner. Marti's doctrine
         "Bezpecnost pres probuzeni, ne pres ticho". -->
    <script src="/static/erp/components/erp_error_badge.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase D (1.6.2026, Marti): per-user nastaveni prostredi. Prvni
         setting = prosviceni textu gridu (injektovany <style> s !important
         prebije inline AG theme override). Auto-init aplikuje ulozeny jas. -->
    <script src="/static/erp/erp_user_settings.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Krok 5.X (23.5.2026): batch row action helper — Mód 1 (Centrála 1
         cyklicky per-row). Generic _erpBatchRowAction(opts) — reusable napříč
         existing Smazat + future HW/FW dynamic actions. -->
    <script src="/static/erp/components/erp_batch_action.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Universal CRUD Etapa A (24.5.2026 vecer): shared action registry
         (Novy/Oprava/Smazat/Obnovit) — JEDEN truth source pro 3 vrstvy
         (context menu, grid header, workspace toolbar). Marti doctrine
         "stejne zobrazit, stejne funkce". -->
    <script src="/static/erp/components/erp_grid_actions.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Cell actions Fáze 1 (1.6.2026, Marti: dvojklik na telefon/email/web
         → tel:/mailto:/open + auto-archiv fw.contact_action_log). Dispatcher
         pro grid (onCellDoubleClicked) i form (dblclick na pole). -->
    <script src="/static/erp/components/erp_cell_actions.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- FW Action Pipelines — FE orchestrátor (3.6.2026, Marti): ActPipeline.run()
         + resume loop + FE handlery (cell_trigger/open_core/grid_refresh). -->
    <script src="/static/erp/components/act_orchestrator.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- FW Action Pipelines — grafický přehled (3.6.2026, Marti prezentace):
         ErpActionCard + openPipelineGraph (kroky jako karty pod sebe). -->
    <script src="/static/erp/components/action_card.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Update prompt (1.6.2026, Marti): po deployi nabídne "Obnovit". -->
    <script src="/static/app_version_watch.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Deploy na povel (1.6.2026, Marti): 🚀 tlačítko jen pro rodiče. -->
    <script src="/static/deploy_button.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Claude SQL bridge Krok 2: write approval banner (jen rodiče). -->
    <script src="/static/claude_write_approval.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- PWA → nabídka instalace nativní appky (jen Android). -->
    <script src="/static/app_install_prompt.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Master-detail Krok 6 (24.5.2026): custom JS renderer pro Data
         Sources → Data Source Op detail (nested ErpDataGrid s layoutKey
         "data_source_op" persistence). Marti's Varianta B — full features
         v detail (toolbar, filter glow, compact). -->
    <script src="/static/erp/components/data_source_op_detail.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Phase API Versioned Routing Etapa D (23.5.2026): footer version dropup.
         Renders pill v <div id="erpFooterApiVersion"> + dropup menu s pin/unpin/diff.
         Polluje GET /api/v1/erp/api-versions every 60s pro current_pin + versions list. -->
    <script src="/static/erp/components/api_version_dropup.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- CardDAV F1.6 (3.6.2026, Marti — "kontakty pro Pavla"): self-service
         připojení telefonu (token + návod). window.openCarddavConnect(). -->
    <script src="/static/carddav_connect.js?v=''' + _STATIC_VERSION + '''"></script>
    <!-- Signál nové zprávy ve sdílené konverzaci (3.6.2026): ding + animace
         „Tvoje Marti" (#erpMartiAiBtn) + proklik do chatu na tu konverzaci. -->
    <script src="/static/shared_signal.js?v=''' + _STATIC_VERSION + '''"></script>
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
    <script src="/static/erp/components/design_form_helpers.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/design_db_connection_editor.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/design_data_set_editor.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/design_jadro_radek_form.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/design_soudecek_core_form.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/field_picker_modal.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/design_data_source_editor.js?v=''' + _STATIC_VERSION + '''"></script>
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
        // framework_jadro_id, is_immutable, description,
        // created_at, updated_at. Žádný icon (emoji v label), žádný
        // target_url, status text místo is_active+is_archived.
                // [framework_menu_nodes] dead inline grid def dropped 22.5.2026 (dispatcher via fw.data_source.dispatchPageRender)
        // ── Phase 38.4 Krok 6+ Datové zdroje (fw.data_source) ──
                // [framework_data_sources] dead inline grid def dropped 22.5.2026 (dispatcher via fw.data_source.dispatchPageRender)
        // ── Phase 38.4 Krok 6+ DataSets (fw.data_set, low-level SQL) ──
                // [framework_data_sets] dead inline grid def dropped 22.5.2026 (dispatcher via fw.data_source.dispatchPageRender)

        // Sprint D (17.5.2026 dop.): DB Connections grid
                // [framework_db_connections] dead inline grid def dropped 22.5.2026 (dispatcher via fw.data_source.dispatchPageRender)

                // [stats] dead inline grid def dropped 22.5.2026 (dispatcher via fw.data_source.dispatchPageRender)
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
      // ── Phase 38.4 Krok 5.R-C+5 (18.5.2026 vecer pozde) ──
      // Marti's doctrine: "my prece nepotrebujeme resit ty sloupce...
      // Nam staci, aby se chovaly nativne. Tj defaultne aby zobrazovaly
      // vsechny sloupce z datasetu, aniz by byly tabulky sloupcu definovany"
      // ──
      // gridColumns(mode) wrapper: pokud mode neni v explicit hardcoded
      // switch (audited/all/stats only), vrati []. _sysCurrentGrid pak
      // prepne na autoColumns:true → AG Grid si gene columns z rowData
      // keys. Bez recreate fw.comp_grid_master schema.
      const _hardcodedColumnModes = new Set([
        "audited", "all", "stats",
        "framework_menu_nodes",  // explicit case v gridColumns existuje
      ]);
      const _gridColumns_orig = gridColumns;
      gridColumns = function _gridColumnsNativeWrapper(mode) {
        if (!_hardcodedColumnModes.has(mode)) {
          // Native autoColumns mode — frontend prepne na rowData-driven cols
          return [];
        }
        return _gridColumns_orig(mode);
      };
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
        // Phase 38.4 Krok 5.R-C+3 (11.5.) deprecated /grid/{code}/columns endpoint.
        // Modern path: autoColumns from dataset[0] keys (datagrid.js native).
        // Fix N+ (21.5. rano, Marti's "co ty warningy?"): drop fetch entirely,
        // protože každý call generuje 404 warn row v fw.diag_log (middleware
        // Fix E captures 4xx). Hardcoded sync fallback (gridColumns) zachován
        // pro legacy mode-specific columns. Pokud mode neexistuje v hardcoded
        // mapě, vrátí [] a autoColumns přeberou.
        var cols = gridColumns(mode);
        if (cols && cols.length) {
          console.log("[ERP-DIAG] gridColumns hardcoded: " + mode +
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
      // Frontend cache last-loaded System tree dat (z /api/v1/erp/system-tree).
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
        return _walkSystemTree(function(n) { return n.menu_node_pk === cislo; });
      }

      function _findSystemNodeById(itemId) {
        return _walkSystemTree(function(n) { return n.id === itemId; });
      }

      function _getSystemCisloByMode(mode) {
        var node = _walkSystemTree(function(n) {
          return _modeFromNode(n) === mode;
        });
        return node ? node.menu_node_pk : null;
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
        var sysLayoutKey = (sysCislo != null) ? ("core_" + sysCislo) : null;

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
          // Phase 38.4 Krok 5.R-C+5 (18.5.2026): native autoColumns gate
          // Pokud columns prazdny ([] z gridColumns wrapper), AG Grid si
          // gene columns z rowData keys. Bez hardcoded fw.comp_grid_master.
          var _useAutoCols = (!columns || columns.length === 0);
          // Krok 5.R-C+7 (18.5.2026): coreInfo pill — sysCislo = core_id
          // (negativní pro hardcoded, positive pro fw.core).
          // Phase 38.4 Krok 5.R-C+7.1 hotfix (18.5.2026): drop undefined
          // `label` reference (in scope chybi), use window._sysCurrentLabel.
          var _ciHard = {
            coreId: sysCislo,
            mode: mode,
            coreLabel: (window._sysCurrentLabel || mode),
            hardcoded: true,
          };
          window._sysCurrentGrid = new ErpDataGrid(body, {
            rowData: rowData,
            columnDefs: _useAutoCols ? null : columns,
            autoColumns: _useAutoCols,
            coreInfo: _ciHard,
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
              const r = await fetch("/api/v1/erp/system-tree", { credentials: "include", cache: "no-store" });
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

      // Phase 22.5.2026 cleanup C: _systemModeFromItemId/_systemModeFromCislo/
      // _renderSystemViewIntoMain droppnuté (3 dead functions, ~55 LOC).
      // Po cislo_def drop refactor + dead negative branch drop v
      // _renderTabIntoMain jsou bez callsitů. System view dispatch jde teď
      // unified přes ErpPageRender.dispatchPageRender (fw.data_source path).

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
        // Phase 2.E (18.5.2026): legacy /prehled dropped — FW přehledy go via /data-by-id endpoint.
        mainContent.innerHTML =
          '<div class="erp-prehled-error" style="padding:24px;color:#a09080;">' +
          '<strong>📋 Centrála 1 přehledy odstraněny</strong><br><br>' +
          'Použij <em>System tree</em> nebo <em>Soudeček picker</em> pro FW přehledy.<br>' +
          '<small style="color:#807060;">Phase 2.E cleanup 18.5.2026 — legacy /prehled endpoint dropped.</small>' +
          '</div>';
      }

      function renderPrehledError(cislo, item, msg) {
        // Phase 2.E (18.5.2026): legacy stub — never called (loadPrehled stubed).
        console.warn("[Phase 2.E] renderPrehledError stub, cislo=" + cislo);
        return;
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
          // Phase 2.A hotfix (18.5.2026): /form-core-for-grid endpoint dropped,
          // replaced by /design/core-by-code (which now returns form_core in response).
          const r = await fetch(
            "/api/v1/erp/design/core-by-code/" + encodeURIComponent(gridCode),
            { credentials: "include" }
          );
          if (r.ok) {
            const d = await r.json();
            if (d && d.form_core && d.form_core.code) {
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
        // Phase 2.E (18.5.2026): legacy /jadro dropped.
        console.warn("[Phase 2.E] openJadroInPane stub, formId=" + formId);
        return;
      }
      function closeJadroPane() {
        // Phase JS-cleanup hotfix (18.5.2026 ~00:15): no-op stub. Original
        // closeJadroPane closed jadro pane DOM. Po Phase 2.A jadro endpoints
        // dropped, pane never opens. Keep stub aby _renderTabIntoMain callsite
        // neselhalo (defensive "if (currentJadro) closeJadroPane()").
        currentJadro = null;
        currentJadroForm = null;
      }

      // ── DEAD CODE — B+6.4+ post-render hook nahrazen ErpForm
      // orchestratorem (B+6.6 6.5.2026). ErpForm staví ErpFormList
      // přímo z metadat a používá LookupField property pro sibling
      // hide + FK sync. Tyto funkce nikdo nevolá; smaž v cleanup
      // commitu, zatím ponecháno pro reference.
      // ──────────────────────────────────────────────────────────────

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
        // Phase D (1.6.2026): DESIGN mód jen pro rodiče. Členové (EUROSOFT
        // tenant) vždy PROD — i kdyby localStorage měl '1'.
        try { if (window.__ERP_IS_PARENT !== true) return false; } catch (e) {}
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
        try { var _ml = document.getElementById('erpMobileDevLink'); if (_ml) _ml.style.display = on ? 'inline-flex' : 'none'; } catch (e) {}
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
          const prefix = '  '.repeat(depth) + (n.is_folder ? '📁 ' : '📄 ');
          const opt = document.createElement('option');
          opt.value = String(n.id);
          opt.textContent = prefix + n.label;
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
        // Code input dropped 22.5.2026 — code column removed.
        // Kind dropdown dropped 22.5.2026 — kind column removed.

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
          if (!labelV) {
            alert('Label povinný.'); return;
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
                label: labelV,
                parent_id: finalParentId,
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
        // Phase D (1.6.2026): Design režim toggle JEN pro rodiče. Členové
        // (EUROSOFT tenant) ho v popoveru nevidí — DESIGN mód je parent-only.
        let _isParentUI = true;
        try { _isParentUI = (window.__ERP_IS_PARENT === true); } catch (e) {}
        if (_isParentUI) {
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
        }
        // Phase D (1.6.2026, Marti): Nastavení prostředí — per-user, pro VŠECHNY
        // (rodiče i členy). První setting = prosvícení gridu (Pavel). Otevře
        // ErpUserSettings panel.
        try {
          if (window.ErpUserSettings) {
            const setItem = document.createElement('div');
            setItem.className = 'erp-user-popover-item';
            setItem.innerHTML =
              '<span class="erp-user-popover-item-label">⚙ Nastavení prostředí</span>';
            setItem.title = 'Per-user nastavení vzhledu (prosvícení gridu, …).';
            setItem.addEventListener('click', () => {
              const pop2 = document.getElementById('erpFooterUserPopover');
              if (pop2) pop2.setAttribute('hidden', '');
              window.ErpUserSettings.openPanel();
            });
            pop.appendChild(setItem);
          }
        } catch (e) { console.warn('[user-settings menu] failed', e); }
        // CardDAV F1.6 (3.6.2026, Marti — "kontakty pro Pavla"): připoj telefon
        // -> při hovoru jméno klienta. Pro VŠECHNY (rodiče i členy).
        try {
          if (window.openCarddavConnect) {
            const cdItem = document.createElement('div');
            cdItem.className = 'erp-user-popover-item';
            cdItem.innerHTML =
              '<span class="erp-user-popover-item-label">📱 Synchronizace s telefonem</span>';
            cdItem.title = 'Synchronizace kontaktů do telefonu — při hovoru uvidíš jméno klienta.';
            cdItem.addEventListener('click', () => {
              const pop2 = document.getElementById('erpFooterUserPopover');
              if (pop2) pop2.setAttribute('hidden', '');
              window.openCarddavConnect();
            });
            pop.appendChild(cdItem);
          }
        } catch (e) { console.warn('[carddav menu] failed', e); }
        // Future: další položky (profile, logout, atd.)
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
          // Fix J Vrstva 5 (20.5. vecer): auto-add X-Erp-Core-Id +
          // X-Erp-Comp-Def-Id headers z window context. Backend middleware
          // (Fix J) cte tyto headery → log_event(core_id, comp_def_id) →
          // fw.diag_log row dostane grid/form attribution.
          try {
            const _coreId = window._erpActiveCoreId;
            if (_coreId !== undefined && _coreId !== null) {
              opts.headers["X-Erp-Core-Id"] = String(_coreId);
            }
            const _compDefId = window._erpActiveCompDefId;
            if (_compDefId !== undefined && _compDefId !== null) {
              opts.headers["X-Erp-Comp-Def-Id"] = String(_compDefId);
            }
          } catch (_e) { /* never crash _apiCall */ }
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
            // Fix Q (21.5. rano, Marti's catch): clear window ERP context před
            // refresh — eliminate stale core_id z předchozích interakcí. Pokud
            // dispatchPageRender pak fire (FW tab), přepíše. HC tab → null
            // zůstane → Fix L wrapper neinjectne X-Erp-Core-Id → correct.
            try {
              window._erpActiveCoreId = null;
              window._erpActiveCompDefId = null;
            } catch (_e) { /* never crash refresh */ }
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
      // Phase D (1.6.2026): beforeinstallprompt už zachycen brzy v <head>
      // (window._deferredInstallPrompt). Tento listener je backup pokud event
      // přijde později — sync do window.
      window.addEventListener('beforeinstallprompt', (ev) => {
        ev.preventDefault();
        window._deferredInstallPrompt = ev;
        const btn = document.getElementById('erpInstallBtn');
        if (btn) btn.style.display = 'inline-flex';
      });
      const _installBtn = document.getElementById('erpInstallBtn');
      if (_installBtn) {
        _installBtn.addEventListener('click', async () => {
          if (!window._deferredInstallPrompt) {
            // Marti 1.6.2026: ŽÁDNÉ blokující dialogové okno. Když deferred
            // prompt není k dispozici (Chrome ho nenabídl / už nainstalováno),
            // klik tiše nedělá nic — instalace přes nativní install ikonu
            // v adresním řádku prohlížeče. Dřívější alert blokoval flow.
            console.log('[install] no deferred prompt — silent (native install via address bar)');
            return;
          }
          try {
            window._deferredInstallPrompt.prompt();
            const { outcome } = await window._deferredInstallPrompt.userChoice;
            console.log('[install] user choice:', outcome);
            if (outcome === 'accepted') {
              _installBtn.style.display = 'none';
            }
          } catch (e) {
            console.error('[install] prompt failed:', e);
          }
          window._deferredInstallPrompt = null;
        });
      }
      // Hide install button kdyz uz je nainstalovany (post-install event)
      window.addEventListener('appinstalled', () => {
        const btn = document.getElementById('erpInstallBtn');
        if (btn) btn.style.display = 'none';
        console.log('[install] appinstalled event — button hidden');
      });
      // Phase D (1.6.2026, Marti): persistentní install nabídka. Pokud ERP
      // NEběží jako standalone PWA (= je v browser tabu → méně místa na
      // obrazovce), ukaž install ikonu VŽDY — i bez beforeinstallprompt
      // (iOS Safari ho nefírne nikdy; Chrome ho nemusí fírnout dle heuristiky
      // nebo když už je nainstalovaný chat na stejné doméně). Klik → deferred
      // prompt (pokud zachycen) nebo platform-aware hint. V standalone mode
      // (už nainstalováno) ikonu schovej.
      (function _erpInitInstallAffordance() {
        const btn = document.getElementById('erpInstallBtn');
        if (!btn) return;
        const _standalone = window.matchMedia('(display-mode: standalone)').matches
          || window.navigator.standalone === true;  // iOS Safari standalone
        btn.style.display = _standalone ? 'none' : 'inline-flex';
      })();

      // Logo "STRATEGIE" → HARD RELOAD s potvrzovacím dialogem (parita s Chatem,
      // Marti 2.6.2026). Drive jen <a href="/erp/"> bez potvrzeni.
      (function _erpInitLogoReload() {
        const logo = document.getElementById('erpLogoLink');
        if (!logo) return;
        logo.addEventListener('click', async (ev) => {
          ev.preventDefault();
          let ok = true;
          try {
            if (window._erpDFH && typeof window._erpDFH._confirmDarkDialog === 'function') {
              ok = await window._erpDFH._confirmDarkDialog({
                title: 'Obnovit STRATEGIE ERP?',
                message: 'Hard reload — načte nejnovější verzi aplikace.',
                ok: 'Obnovit',
                cancel: 'Zrušit'
              });
            } else {
              ok = window.confirm('Obnovit STRATEGIE ERP? (hard reload)');
            }
          } catch (_e) {
            ok = window.confirm('Obnovit STRATEGIE ERP? (hard reload)');
          }
          if (ok) window.location.reload();
        });
      })();

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
        // Etapa F Krok 2 (24.5.2026 vecer pozde): drop dead gridState
        // capture. Per-tab pane cache drzi grid state v DOM/AG Grid prirozene
        // — zadny save/restore needed, switch = hidden toggle.
        // (Predtim: cur.gridState = {columnState, filterModel} but restore
        //  was dead code v _renderTabIntoMain za unreachable return.)
        // Fix Q+ (21.5. revize, po Marti's catch "FW tabs neloguji při switch"):
        // per-tab window context caching. tab.coreId/compDefId se ukládá na
        // konci switchTab (po dispatchPageRender běhu). Při switchu zpět
        // restorneme cached value — FW tab dostane správný coreId, HC tab
        // dostane null. Eliminuje stale leak Z FW→HC switch a zachová
        // attribution při FW↔FW switching mezi cached taby.
        try {
          window._erpActiveCoreId = (tabsState.tabs[idx].coreId !== undefined
            ? tabsState.tabs[idx].coreId
            : null);
          window._erpActiveCompDefId = (tabsState.tabs[idx].compDefId !== undefined
            ? tabsState.tabs[idx].compDefId
            : null);
        } catch (_e) { /* never crash tab switch */ }
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
        // Marti 2.6.2026: base = "STRATEGIE ERP - <short_name>" (window._erpTitleBase),
        // za nej " · <přehled>". V hlavicce zustava jen logo "STRATEGIE".
        try {
          const _base = window._erpTitleBase || "STRATEGIE ERP";
          document.title = _base + " · " + _tabLabel;
        } catch (e) {}
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
        // Fix Q+ (21.5. revize): po load/render zachyt window state na tab —
        // dispatchPageRender (pokud běhal, FW path) nastavil window._erpActiveCoreId
        // → ulož pro budoucí switchTab restore. HC tab (dispatchPageRender ne)
        // → window stayed null (z initial restore) → tab.coreId zůstane null.
        try {
          tab.coreId = (typeof window._erpActiveCoreId !== 'undefined'
            ? window._erpActiveCoreId
            : null);
          tab.compDefId = (typeof window._erpActiveCompDefId !== 'undefined'
            ? window._erpActiveCompDefId
            : null);
        } catch (_e) { /* never crash capture */ }
        // Phase 38.5: po switch tabu (load nebo cached) prepocitat refresh
        // ikonu — novy aktivni tab moze mit jine stari dat.
        if (typeof ErpRefresh !== 'undefined') ErpRefresh._updateButton();
      }

      function closeTab(idx) {
        if (idx < 0 || idx >= tabsState.tabs.length) return;
        const closedCislo = tabsState.tabs[idx].cislo;
        const closedItemId = tabsState.tabs[idx].itemId;
        // Etapa F Krok 2 (24.5.2026 vecer pozde): destroy + remove pane DOM
        // pred splice. Per-tab pane cache cleanup — grid instance destroy
        // (memory), pane element remove (DOM).
        try {
          const closedPaneId = String(closedItemId != null ? closedItemId : closedCislo);
          const closedPane = mainContent.querySelector(
            '.erp-tab-pane[data-tab-pane-id="' + closedPaneId + '"]'
          );
          if (closedPane) {
            if (closedPane._erpGridInstance
                && typeof closedPane._erpGridInstance.destroy === "function") {
              try { closedPane._erpGridInstance.destroy(); } catch (_eDes) {}
            }
            closedPane._erpGridInstance = null;
            closedPane.remove();
          }
        } catch (_eClose) { /* never crash tab close */ }
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
        // Marti's 25.5. drobnost: convert všechny tab hinty na dark mode pres
        // data-hint pattern (existing [data-hint]:hover::after styling).
        // Plus update texty:
        // - close-all: "kromě připnutých a aktivní" (clarification)
        // - pinned tab: jen pin info, drop label (label je viditelný v span)
        // - nepinned tab: učit usera right-click feature
        // - close × na nepinned: drop hint úplně (visual ×, action obvious)
        html += '<button type="button" class="erp-tab-close-all" id="erpTabCloseAll" ' +
                'data-hint="Zavřít všechny záložky kromě připnutých a aktivní">×</button>';
        tabsState.tabs.forEach((t, i) => {
          const active = (i === tabsState.activeIndex);
          const pinned = (t.pinned === true);
          // Tab body hint (data-hint = dark mode tooltip)
          const tabHint = pinned
            ? ' data-hint="📌 Připnutá záložka — pravým klikem odepnout"'
            : ' data-hint="Pravým klikem můžeš záložku připnout"';
          html += '<div class="erp-tab' + (active ? ' active' : '') +
                  '" data-tab-idx="' + i + '"' + tabHint + '>';
          html += '<span class="erp-tab-label">' + escapeHtml(t.label) + '</span>';
          const closeChar = pinned ? '📌' : '×';
          // Close button: pinned má hint o pravém kliku, nepinned bez hintu
          // (action je obvious z visual × ikony — netřeba duplicate hintu).
          const closeHintAttr = pinned
            ? ' data-hint="Pravým klikem odepnout"'
            : '';
          html += '<button type="button" class="erp-tab-close' +
                  (pinned ? ' pinned' : '') +
                  '" data-tab-close="' + i + '"' + closeHintAttr + '>' + closeChar + '</button>';
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
        // Phase 22.5.2026: po cislo_def drop refactor — tab.cislo je teď
        // VŽDY menu_node.id (positive integer). Žádný negative synthetic
        // range, žádný Centrála 1 legacy. Sjednocená render cesta přes
        // _renderTabIntoMain (System view / FW přehled / Design form
        // dispatch dle node typu).
        tab.data = { _system: true };  // sentinel pro renderTabIntoMain
        _renderTabIntoMain(tab);
        if (typeof ErpRefresh !== 'undefined') ErpRefresh.markFresh(tab.cislo);
      }

      function _renderTabIntoMain(tab) {
        // B+2: auto-close jádro pane (jiný přehled = jiný kontext)
        if (currentJadro) closeJadroPane();

        // Etapa F Krok 2 (24.5.2026 vecer pozde, Marti's directive
        // "MY NESMIME PRI PREPINANI ZALOZEK gridu recreate prehledy"):
        // per-tab persistent DOM pane architecture. Cached pane = no
        // recreate, grid state drzi prirozene v DOM/AG Grid.
        const paneId = String(tab.itemId != null ? tab.itemId : tab.cislo);

        // Hide all OTHER existing panes (siblings)
        mainContent.querySelectorAll('.erp-tab-pane').forEach(function (p) {
          if (p.dataset.tabPaneId !== paneId) {
            p.setAttribute('hidden', '');
          }
        });

        // Check for cached pane (already built v predchozim switchu/openu)
        let pane = mainContent.querySelector(
          '.erp-tab-pane[data-tab-pane-id="' + paneId + '"]'
        );
        if (pane) {
          // CACHED — just unhide, grid state preserved (scroll, selection,
          // filters, sort, expand). activeErpDataGrid pointer update pro
          // backward compat (sizeColumnsToFit calls, closeTab destroy).
          pane.removeAttribute('hidden');
          activeErpDataGrid = pane._erpGridInstance || null;
          // Etapa F Krok 2 HOTFIX (Marti's catch "vedle Tvoje Marti zmizelo
          // CRUD"): external toolbarHost (#erpGridActionsHost) je shared
          // DOM — po cache hit treba re-populate s tohoto gridu CRUD
          // buttons + re-wire handlers (predtim mohly byt overwritten
          // jinym tab gridem). Internal toolbar = per-pane DOM, no-op.
          if (activeErpDataGrid && typeof activeErpDataGrid._repopulateCrudToolbar === "function") {
            try { activeErpDataGrid._repopulateCrudToolbar(); } catch (_eRepop) {}
          }
          // Etapa F Krok 2 HOTFIX 2 (24.5.2026 vecer pozde, Marti's catch
          // "sjednoti siri bunek napric celym gridem"): DROP sizeColumnsToFit
          // call po cache hit. Method IGNORUJE disableColumnFlex doctrine
          // (Marti's task #436 master-detail Volba A — saved widths drzi
          // jen pokud disableColumnFlex=true) a sjednocuje widths k
          // container width. AG Grid v32+ ma built-in ResizeObserver,
          // detekuje display:none -> flex transition sam — explicit call
          // byl zbytecny + skodlivy.
          return;
        }

        // FIRST TIME — clear any legacy direct mainContent children (old
        // architecture pred Krok 2) + create new pane + dispatch render
        Array.from(mainContent.childNodes).forEach(function (n) {
          if (n.nodeType === 1 && !n.classList.contains('erp-tab-pane')) {
            n.remove();
          }
        });
        pane = document.createElement('div');
        pane.className = 'erp-tab-pane';
        pane.dataset.tabPaneId = paneId;
        mainContent.appendChild(pane);

        // Phase 22.5.2026 (po cislo_def drop refactor): VŠECHNY tab.cislo jsou
        // positive menu_node.id. Žádný synthetic negative range, žádný legacy
        // Centrála 1 negative ID. Dispatch přes core_id lookup z tree cache +
        // ErpPageRender.dispatchPageRender (single path, no branching).
        let node = (typeof _findSystemNodeById === "function")
          ? _findSystemNodeById(tab.itemId) : null;
        let coreId = node && node.core_id;
        let coreCode = node && node.core_code;
        if (!coreId && typeof tree !== "undefined" && tree && typeof tree.findLiByCislo === "function") {
          const li = tree.findLiByCislo(tab.cislo);
          if (li) {
            coreId = parseInt(li.dataset.coreId || "0", 10) || null;
            coreCode = li.dataset.coreCode || null;
          }
        }
        if (coreId) {
          if (window.ErpPageRender && typeof window.ErpPageRender.dispatchPageRender === "function") {
            // Etapa F Krok 2: dispatchPageRender targets pane (NOT mainContent).
            // page_render.js assigns pane._erpGridInstance po ErpDataGrid init.
            window.ErpPageRender.dispatchPageRender(coreId, coreCode, tab, pane);
          } else {
            console.error("[router] ErpPageRender modul neni nacten — hard reload prohlizec.");
            pane.innerHTML =
              '<div style="padding:40px;text-align:center;color:#d4a8a8;">' +
              '❌ page_render.js modul nenacten — hard reload prohlizec (Ctrl+Shift+R).' +
              '</div>';
          }
          return;
        }
        // No core associated — folder placeholder INTO PANE (cached too)
        pane.innerHTML =
          '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
          '<h2 style="margin:0 0 12px;color:#a8b4c2;font-weight:500;">📁 ' +
          escapeHtml(tab.label || "Soudeček") + '</h2>' +
          '<p style="color:#7a8696;font-size:13px;margin:0;">' +
          'Soudeček bez asociovaného core přehledu. ' +
          'Pravý-klik → 🎨 Design pro vybrání core.' +
          '</p></div>';
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
