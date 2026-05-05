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

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

# B+4.2 (5.5.2026): cache busting pro static assets — každý API restart
# = nová version = browser donucen stáhnout čerstvé /static/erp/datagrid.js+css.
# Hodnota fixed při module load (= API process start), neměnná do restartu.
_STATIC_VERSION = str(int(time.time()))

from core.logging import get_logger
from modules.erp.application.centrala_reader import CentralaReader, TYP_NAMES
from modules.erp.application.render_generator import render_form
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


# ── Public endpoints ────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
def erp_home(req: Request) -> HTMLResponse:
    """Phase B nástřel: 3-pane workspace (sidebar tree + main pane prehled+jadro)."""
    uid = _get_uid(req)
    _require_parent(uid)
    return HTMLResponse(content=_render_workspace_page(uid))


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

    return JSONResponse({
        "ok": True,
        "phase": "A",
        "mcp_klient_available": mcp_ok,
        "supported_typs": len(TYP_NAMES),
        "user_id": uid,
    })


# ── Phase B (5.5.2026): Tree + Přehled JSON endpoints ────────────────


@api_router.get("/strom")
def strom_json(req: Request) -> JSONResponse:
    """JSON tree z EC_CentralaMenu (Phase B nástřel)."""
    uid = _get_uid(req)
    _require_parent(uid)

    reader = CentralaReader()
    tree = reader.load_menu_tree()

    return JSONResponse({"ok": True, "tree": tree, "root_count": len(tree)})


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
    """
    uid = _get_uid(req)
    _require_parent(uid)

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


@api_router.get("/jadro/{form_id}/components")
def jadro_components_json(form_id: int, req: Request) -> JSONResponse:
    """JSON dump komponent jádra (debug, Phase A)."""
    uid = _get_uid(req)
    _require_parent(uid)

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


# ── HTML page builders ──────────────────────────────────────────────


def _render_full_page(title: str, content: str, breadcrumb: list[tuple[str, str | None]]) -> str:
    """Wrap content do full HTML page — STRATEGIE BLACK theme."""
    bc_html = []
    for label, url in breadcrumb:
        if url:
            bc_html.append(f'<a href="{url}" class="erp-bc-link">{html.escape(label)}</a>')
        else:
            bc_html.append(f'<span class="erp-bc-current">{html.escape(label)}</span>')
    bc_str = ' <span class="erp-bc-sep">/</span> '.join(bc_html)

    return f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | STRATEGIE ERP</title>
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
    .erp-logo {{
      font-family: 'Galano Grotesque','Montserrat',sans-serif;
      font-size: 18px; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
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

    /* ── Phase B+2.2 (5.5.2026): full-width workspace + jádro modal ── */
    /* Override <main> wrapper max-width pro workspace stranky (jiné stránky
       jako landing/jadro full-page si max-width 1280px ponechávají). */
    main:has(.erp-workspace) {{
      max-width: none !important;
      padding: 0 !important;
      margin: 0 !important;
    }}
    /* B+2.1: tree flush left, full viewport width, resize handle mezi tree a main */
    /* B+2.3: zero right padding — grid fills full viewport width edge-to-edge */
    .erp-workspace {{
      --erp-tree-width: 240px;
      max-width: none; margin: 0;
      display: grid;
      grid-template-columns: var(--erp-tree-width) 5px 1fr;
      gap: 0;
      padding: 8px 0 8px 0;
      min-height: calc(100vh - 90px);
    }}
    /* B+2.2-3: workspace 2-pane, jádro je modal, grid flush right */
    .erp-workspace .erp-tree-pane {{ margin-right: 0; }}
    .erp-workspace .erp-main-pane {{ margin-left: 6px; margin-right: 0; }}

    /* B+2.1: resize handle mezi tree a main */
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
      background: var(--surface); border: 1px solid var(--border);
      /* B+2.1: flush-left → border-radius jen vpravo (nahoře+dole),
         vlevo plynule splývá s viewport edge */
      border-radius: 0 10px 10px 0;
      border-left: none;
      overflow: hidden;
      max-height: calc(100vh - 90px); display: flex; flex-direction: column;
    }}
    .erp-tree-header {{
      padding: 12px 14px; border-bottom: 1px solid var(--border);
      font-size: 13px; font-weight: 600; color: var(--text);
      background: var(--surface2);
    }}
    .erp-tree-root {{
      overflow-y: auto; padding: 6px 0; flex: 1;
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
    }}
    .erp-tree-row:hover {{ background: var(--surface2); color: var(--text); }}
    .erp-tree-row.active {{
      background: rgba(79,142,247,0.18);
      color: var(--accent);
      border-left-color: var(--accent);
      font-weight: 500;
    }}
    .erp-tree-toggle {{ width: 12px; font-size: 9px; color: var(--muted); flex-shrink: 0; }}
    .erp-tree-spacer {{ width: 12px; flex-shrink: 0; }}
    /* Tree icon numbers (n.ikona % 100) hidden — were noise.
       Future: map to Unicode icons (📁/📋/🛒/...) per ikona category. */
    .erp-tree-ico {{ display: none; }}
    .erp-tree-label {{ flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .erp-tree-leaf .erp-tree-label {{ color: var(--text); font-weight: 400; }}
    .erp-tree-folder .erp-tree-label {{ color: var(--text-muted); font-weight: 500; }}

    /* B+2.3: padding=0 na main-pane, grid flush proti edges; padding drží header/placeholders */
    .erp-main-pane {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px 0 0 10px;  /* B+2.3: flat right edge (flush with viewport) */
      border-right: none;
      padding: 0;
      max-height: calc(100vh - 110px); overflow: hidden;
      display: flex; flex-direction: column;
    }}
    .erp-main-content {{
      display: flex; flex-direction: column;
      flex: 1; min-height: 0; overflow: hidden;
    }}
    .erp-main-loading, .erp-main-error {{ color: var(--muted); padding: 14px 18px; font-size: 13px; }}
    .erp-main-error {{ color: var(--error); }}
    .erp-main-placeholder {{ color: var(--muted); padding: 24px; max-width: 540px; }}
    .erp-main-placeholder h2 {{ color: var(--text); font-size: 18px; font-weight: 600; margin-bottom: 10px; }}
    .erp-main-placeholder p {{ font-size: 14px; line-height: 1.6; margin-bottom: 8px; }}
    .erp-main-placeholder code {{ font-family: 'DM Mono',monospace; color: var(--accent); padding: 1px 5px; background: var(--bg); border-radius: 3px; }}

    .erp-prehled-header {{
      padding: 12px 18px 10px 18px;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
      background: var(--surface);
    }}
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
      from {{ opacity: 0; transform: translate(-50%, -50%) scale(0.96); }}
      to   {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
    }}
    .erp-jadro-pane {{
      position: fixed;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: min(92vw, 1200px);
      height: min(90vh, 920px);
      max-height: 90vh;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
      z-index: 100;
      display: flex; flex-direction: column;
      overflow: hidden;
      animation: erp-modal-pop 180ms ease-out;
    }}
    .erp-jadro-pane[hidden] {{ display: none; }}
    .erp-jadro-header {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      background: var(--bg);
      display: flex; align-items: center; gap: 12px;
      flex-shrink: 0;
    }}
    .erp-jadro-title {{
      font-size: 13px; font-weight: 600; color: var(--text);
      flex: 1; min-width: 0;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .erp-jadro-meta {{
      font-size: 11px; color: var(--muted);
      font-family: 'DM Mono',monospace; flex-shrink: 0;
    }}
    .erp-jadro-close {{
      background: transparent; border: none; color: var(--text-muted);
      font-size: 20px; cursor: pointer; padding: 0 6px;
      line-height: 1; transition: color .12s;
      flex-shrink: 0;
    }}
    .erp-jadro-close:hover {{ color: var(--accent); }}
    .erp-jadro-content {{
      flex: 1; overflow-y: auto; padding: 0;
      background: var(--surface);
    }}
    .erp-jadro-content .erp-form {{
      max-width: none;
      margin: 14px;
      padding: 18px;
    }}
    .erp-jadro-loading, .erp-jadro-error {{
      padding: 24px; color: var(--muted); font-size: 13px;
    }}
    .erp-jadro-error {{ color: var(--error); }}

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
      text-align: center; font-size: 11px; color: var(--muted);
      padding: 32px 16px 16px; font-family: 'DM Mono',monospace;
    }}
  </style>
</head>
<body>
  <header class="erp-header">
    <div class="erp-header-inner">
      <div style="display: flex; align-items: center; gap: 12px;">
        <a href="/erp/" class="erp-logo">STRATEGIE ERP</a>
        <span class="erp-phase-badge">Phase A · read-only</span>
      </div>
      <nav class="erp-bc">{bc_str}</nav>
    </div>
  </header>
  <main>
    {content}
  </main>
  <footer class="erp-footer">
    STRATEGIE ERP renderer · Phase A MVP · 5.5.2026
  </footer>
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
        breadcrumb=[("ERP", None)],
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

    <div class="erp-workspace">
      <aside class="erp-tree-pane">
        <div class="erp-tree-header">Centrála — moduly</div>
        <div id="erpTreeRoot" class="erp-tree-root">
          <div class="erp-tree-skeleton">
            <div class="erp-skel-line"></div>
            <div class="erp-skel-line short"></div>
            <div class="erp-skel-line"></div>
            <div class="erp-skel-line short"></div>
            <div class="erp-skel-line"></div>
          </div>
        </div>
      </aside>
      <div id="erpResizeHandle" class="erp-resize-handle" role="separator" aria-label="Resize tree pane" title="Drag pro změnu šířky stromu"></div>
      <main class="erp-main-pane">
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
          const cls = hasPrehled ? "erp-tree-leaf" : "erp-tree-folder";
          const isExpanded = hasChildren && expanded.has(nid);
          const toggle = hasChildren
            ? '<span class="erp-tree-toggle">' + (isExpanded ? "▼" : "▶") + '</span>'
            : '<span class="erp-tree-spacer"></span>';
          const ico = n.ikona ? '<span class="erp-tree-ico">' + (n.ikona % 100) + '</span>' : '';
          html += '<li class="erp-tree-item ' + cls + '" data-id="' + nid +
                  '" data-cislo-def="' + (n.cislo_def || '') +
                  '" data-text="' + escapeAttr(n.menu_text) + '">';
          html += '<div class="erp-tree-row" style="padding-left: ' + (depth * 16) + 'px;">';
          html += toggle + ico + '<span class="erp-tree-label">' + escapeHtml(n.menu_text) + '</span>';
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
          row.addEventListener("click", () => {
            const item = row.closest(".erp-tree-item");
            const nid = item.getAttribute("data-id");
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
            // Load přehled if cislo_def
            const cisloDef = item.getAttribute("data-cislo-def");
            if (cisloDef && cisloDef !== "") {
              setActive(item, parseInt(cisloDef, 10));
            }
          });
        });
      }

      function setActive(item, cislo) {
        treeRoot.querySelectorAll(".erp-tree-row.active").forEach(r => r.classList.remove("active"));
        const row = item.querySelector(":scope > .erp-tree-row");
        if (row) row.classList.add("active");
        saveActive(String(cislo));
        loadPrehled(cislo, item);
      }

      function tryRestoreActive() {
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
        loadPrehled(parseInt(cislo, 10), item);
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

        // B+4.4: limit dropdown — render po headeru, before grid
        const appliedLimit = data.applied_limit || rows.length;
        const limitOptions = [100, 500, 1000, 5000, 100000];
        let limitSelectHtml = '<select id="erpLimitSelect" class="erp-limit-select" title="Maximum řádků">';
        for (const opt of limitOptions) {
          const selected = (opt === appliedLimit) ? ' selected' : '';
          const label = (opt === 100000) ? 'Vše (max 100k)' : opt.toLocaleString("cs-CZ");
          limitSelectHtml += '<option value="' + opt + '"' + selected + '>' + label + '</option>';
        }
        limitSelectHtml += '</select>';

        let html = '<div class="erp-prehled-header">';
        html += '<div class="erp-bc-path">' + breadcrumb + '</div>';
        html += '<div class="erp-prehled-titlebar">';
        html += '<h2>' + escapeHtml(data.nazev || ("Přehled #" + data.cislo)) + '</h2>';
        html += '<div class="erp-prehled-meta">';
        html += '<span class="erp-prehled-rowcount">' + rows.length.toLocaleString("cs-CZ") + ' řádků';
        if (data.has_more) html += ' <span class="erp-prehled-hasmore">(limit, má víc)</span>';
        html += '</span>';
        if (data.target_table) html += ' · <code>' + escapeHtml(data.target_table) + '</code>';
        if (data.id_edit) html += ' · jádro #' + data.id_edit;
        html += ' · <label class="erp-limit-label">limit ' + limitSelectHtml + '</label>';
        html += '</div>';
        html += '</div>';
        if (data.warning) html += '<div class="erp-prehled-warning">⚠ ' + escapeHtml(data.warning) + '</div>';
        html += '</div>';

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
          // MVP standard 5.5.2026: single click = select (Ctrl/Shift multi),
          // double click = open jádro detail. Šipky pouze navigují (Excel-like).
          onRowDoubleClick: (rowData) => {
            const rowId = rowData.ID != null ? rowData.ID : (rowData.id != null ? rowData.id : null);
            if (rowId == null || data.id_edit == null) return;
            openJadroInPane(data.id_edit, rowId);
          },
        });

        // B+4.4: limit dropdown change → re-fetch s novým limitem + persist
        const limitSelect = document.getElementById("erpLimitSelect");
        if (limitSelect) {
          limitSelect.addEventListener("change", (ev) => {
            const newLimit = parseInt(ev.target.value, 10);
            if (!newLimit || newLimit <= 0) return;
            savePrehledLimit(cislo, newLimit);
            loadPrehled(cislo, item, newLimit);
          });
        }
      }

      // ── Phase B+2.2: jádro modal popup (centered overlay) ───────
      async function openJadroInPane(formId, rowId) {
        if (!jadroPane || !jadroContent) return;
        currentJadro = { form_id: formId, row_id: rowId };
        // B+2.2: modal overlay — žádný grid template shift, tabulka beze změny
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
            "/erp/jadro/" + formId + "/" + rowId + "?fragment=1",
            { credentials: "include" }
          );
          if (!r.ok) {
            const txt = await r.text();
            jadroContent.innerHTML = txt || (
              '<div class="erp-jadro-error">Status ' + r.status + '</div>'
            );
            if (jadroTitle) jadroTitle.textContent = "Chyba";
            return;
          }
          const headerTitle = r.headers.get("X-Jadro-Title");
          if (jadroTitle) {
            jadroTitle.textContent = headerTitle || ("Jádro #" + formId);
          }
          const html = await r.text();
          jadroContent.innerHTML = html;
        } catch (e) {
          jadroContent.innerHTML =
            '<div class="erp-jadro-error">Nelze načíst: ' +
            escapeHtml(e.message || String(e)) + '</div>';
          if (jadroTitle) jadroTitle.textContent = "Chyba";
        }
      }

      function closeJadroPane() {
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

      loadTree();
    })();
    </script>
    '''
    return _render_full_page(
        title="STRATEGIE ERP",
        content=content,
        breadcrumb=[("ERP", None)],
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
