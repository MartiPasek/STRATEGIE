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

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

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
def jadro_render(form_id: int, row_id: int, req: Request) -> HTMLResponse:
    """
    Read-only render jednoho Centrála jádra.

    Pipeline (z proposal sekce 3):
      1. Načti EC_FormDef.{form_id} → header + SQL_Select
      2. Načti EC_FormDefEdit + EC_FormDefEditProperty → komponenty
      3. Substituuj :ID = {row_id} v SQL_Select, execute → data
      4. Render HTML přes render_generator
    """
    uid = _get_uid(req)
    _require_parent(uid)
    logger.info(
        f"ERP | jadro render | user={uid} form_id={form_id} row_id={row_id}"
    )

    reader = CentralaReader()

    # 1. Form header
    form = reader.load_form_def(form_id)
    if not form:
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
    # Po této enrich:
    #   data['NadrazeneMenu']         = 11    (raw FK)
    #   data['_lookup_NadrazeneMenu'] = 'Systém'  (display from lookup view)
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


@api_router.get("/prehled/{cislo}")
def prehled_data_json(cislo: int, req: Request) -> JSONResponse:
    """JSON data z přehledu Cislo=N (Phase B nástřel)."""
    uid = _get_uid(req)
    _require_parent(uid)

    reader = CentralaReader()
    meta = reader.load_prehled_meta(cislo)
    if not meta:
        raise HTTPException(404, f"EC_DELPHI_TabObecnyPrehled Cislo={cislo} nenalezen")

    data = reader.execute_prehled_data(meta, limit=100)

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
    .erp-header {{
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: 14px 24px; position: sticky; top: 0; z-index: 10;
    }}
    .erp-header-inner {{
      max-width: 1280px; margin: 0 auto;
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

    /* ── Phase B nástřel: 3-pane workspace (5.5.2026) ── */
    .erp-workspace {{
      max-width: 1280px; margin: 0 auto;
      display: grid; grid-template-columns: 280px 1fr;
      gap: 14px; padding: 14px;
      min-height: calc(100vh - 90px);
    }}
    .erp-tree-pane {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; overflow: hidden;
      max-height: calc(100vh - 110px); display: flex; flex-direction: column;
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
    .erp-tree-row {{
      padding: 5px 12px; cursor: pointer;
      display: flex; align-items: center; gap: 6px;
      font-size: 13px; color: var(--text-muted);
      transition: background .12s, color .12s;
    }}
    .erp-tree-row:hover {{ background: var(--surface2); color: var(--text); }}
    .erp-tree-row.active {{ background: rgba(79,142,247,0.15); color: var(--accent); }}
    .erp-tree-toggle {{ width: 12px; font-size: 9px; color: var(--muted); flex-shrink: 0; }}
    .erp-tree-spacer {{ width: 12px; flex-shrink: 0; }}
    .erp-tree-ico {{ font-size: 11px; color: var(--muted); padding: 0 4px; flex-shrink: 0; }}
    .erp-tree-label {{ flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .erp-tree-leaf .erp-tree-label {{ color: var(--text); }}

    .erp-main-pane {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 18px;
      max-height: calc(100vh - 110px); overflow: auto;
    }}
    .erp-main-content {{ }}
    .erp-main-loading, .erp-main-error {{ color: var(--muted); padding: 14px; font-size: 13px; }}
    .erp-main-error {{ color: var(--error); }}
    .erp-main-placeholder {{ color: var(--muted); padding: 24px; max-width: 540px; }}
    .erp-main-placeholder h2 {{ color: var(--text); font-size: 18px; font-weight: 600; margin-bottom: 10px; }}
    .erp-main-placeholder p {{ font-size: 14px; line-height: 1.6; margin-bottom: 8px; }}
    .erp-main-placeholder code {{ font-family: 'DM Mono',monospace; color: var(--accent); padding: 1px 5px; background: var(--bg); border-radius: 3px; }}

    .erp-prehled-header {{
      margin-bottom: 14px; padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }}
    .erp-prehled-header h2 {{ font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 4px; }}
    .erp-prehled-meta {{ font-size: 12px; color: var(--muted); font-family: 'DM Mono',monospace; }}
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
    Phase B nástřel (5.5.2026): 3-pane workspace.

    Layout:
      ┌─────────────┬────────────────────────────────────┐
      │ Sidebar     │ Main pane                          │
      │ (tree)      │ ┌──────────────────────────────┐   │
      │ ec_menu     │ │ Toolbar (Nazev přehledu)     │   │
      │ recursive   │ ├──────────────────────────────┤   │
      │             │ │ Prehled (HTML table)         │   │
      │             │ │ Click row → /erp/jadro/...   │   │
      │             │ └──────────────────────────────┘   │
      └─────────────┴────────────────────────────────────┘

    Vanilla JS (no Tabulator yet, no HTMX yet -- Phase B+1).
    Fetch tree on load, fetch prehled on tree-node click.
    """
    content = '''
    <div class="erp-workspace">
      <aside class="erp-tree-pane">
        <div class="erp-tree-header">Centrála — moduly</div>
        <div id="erpTreeRoot" class="erp-tree-root">
          <div class="erp-tree-loading">Načítám strom…</div>
        </div>
      </aside>
      <main class="erp-main-pane">
        <div id="erpMainContent" class="erp-main-content">
          <div class="erp-main-placeholder">
            <h2>Vyber modul ze stromu vlevo</h2>
            <p>
              Klikni na uzel v levém stromě. Pokud má přehled
              (<code>CisloDef</code>), zobrazí se vpravo. Klik na řádek
              v přehledu otevře jádro pro tu položku.
            </p>
            <p style="margin-top: 12px; font-size: 12px;">
              <em>Phase B nástřel — vanilla HTML, žádný Tabulator/HTMX zatím.</em>
            </p>
          </div>
        </div>
      </main>
    </div>

    <script>
    (function() {
      const treeRoot = document.getElementById("erpTreeRoot");
      const mainContent = document.getElementById("erpMainContent");

      // ── Tree fetch + render ────────────────────────────────────
      async function loadTree() {
        try {
          const r = await fetch("/api/v1/erp/strom", { credentials: "include" });
          if (!r.ok) {
            treeRoot.innerHTML = '<div class="erp-tree-error">Strom nelze načíst (status ' + r.status + ').</div>';
            return;
          }
          const data = await r.json();
          if (!data.tree || data.tree.length === 0) {
            treeRoot.innerHTML = '<div class="erp-tree-error">Strom prázdný.</div>';
            return;
          }
          treeRoot.innerHTML = renderTreeNodes(data.tree, 0);
          attachTreeHandlers();
        } catch (e) {
          treeRoot.innerHTML = '<div class="erp-tree-error">Chyba: ' + e.message + '</div>';
        }
      }

      function renderTreeNodes(nodes, depth) {
        let html = '<ul class="erp-tree-list">';
        for (const n of nodes) {
          const hasChildren = n.children && n.children.length > 0;
          const hasPrehled = n.cislo_def != null;
          const cls = hasPrehled ? "erp-tree-leaf" : "erp-tree-folder";
          const toggle = hasChildren ? '<span class="erp-tree-toggle">▶</span>' : '<span class="erp-tree-spacer"></span>';
          const ico = n.ikona ? '<span class="erp-tree-ico">' + (n.ikona % 100) + '</span>' : '';
          html += '<li class="erp-tree-item ' + cls + '" data-id="' + n.id + '" data-cislo-def="' + (n.cislo_def || '') + '" data-text="' + escapeAttr(n.menu_text) + '">';
          html += '  <div class="erp-tree-row" style="padding-left: ' + (depth * 14) + 'px;">';
          html += toggle + ico + '<span class="erp-tree-label">' + escapeHtml(n.menu_text) + '</span>';
          html += '  </div>';
          if (hasChildren) {
            html += '<div class="erp-tree-children" style="display: none;">' + renderTreeNodes(n.children, depth + 1) + '</div>';
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
            const childrenWrap = item.querySelector(":scope > .erp-tree-children");
            const toggle = row.querySelector(".erp-tree-toggle");
            // Expand/collapse if has children
            if (childrenWrap) {
              const isOpen = childrenWrap.style.display !== "none";
              childrenWrap.style.display = isOpen ? "none" : "block";
              if (toggle) toggle.textContent = isOpen ? "▶" : "▼";
            }
            // Load přehled if cislo_def
            const cisloDef = item.getAttribute("data-cislo-def");
            if (cisloDef && cisloDef !== "") {
              loadPrehled(parseInt(cisloDef, 10), item.getAttribute("data-text"));
              treeRoot.querySelectorAll(".erp-tree-row.active").forEach(r => r.classList.remove("active"));
              row.classList.add("active");
            }
          });
        });
      }

      // ── Přehled fetch + render ────────────────────────────────
      async function loadPrehled(cislo, label) {
        mainContent.innerHTML = '<div class="erp-main-loading">Načítám přehled #' + cislo + '…</div>';
        try {
          const r = await fetch("/api/v1/erp/prehled/" + cislo, { credentials: "include" });
          if (!r.ok) {
            mainContent.innerHTML = '<div class="erp-main-error">Přehled #' + cislo + ' nelze načíst (' + r.status + ').</div>';
            return;
          }
          const data = await r.json();
          mainContent.innerHTML = renderPrehled(data);
          attachPrehledHandlers(data);
        } catch (e) {
          mainContent.innerHTML = '<div class="erp-main-error">Chyba: ' + e.message + '</div>';
        }
      }

      function renderPrehled(data) {
        const cols = data.columns || [];
        const rows = data.rows || [];
        let html = '<div class="erp-prehled-header">';
        html += '  <h2>' + escapeHtml(data.nazev || ('Přehled #' + data.cislo)) + '</h2>';
        html += '  <div class="erp-prehled-meta">' + rows.length + ' řádků';
        if (data.has_more) html += ' (zobrazeno ' + rows.length + ', má víc)';
        if (data.target_table) html += ' · <code>' + escapeHtml(data.target_table) + '</code>';
        if (data.id_edit) html += ' · jádro #' + data.id_edit;
        html += '  </div>';
        if (data.warning) html += '  <div class="erp-prehled-warning">⚠ ' + escapeHtml(data.warning) + '</div>';
        html += '</div>';
        if (rows.length === 0) {
          html += '<div class="erp-prehled-empty">Přehled je prázdný.</div>';
          return html;
        }
        html += '<div class="erp-prehled-tablewrap"><table class="erp-prehled-table">';
        html += '<thead><tr>';
        for (const c of cols) html += '<th>' + escapeHtml(c) + '</th>';
        html += '</tr></thead><tbody>';
        for (const row of rows) {
          const rowId = row.ID != null ? row.ID : (row.id != null ? row.id : '');
          html += '<tr data-row-id="' + rowId + '" class="erp-prehled-row">';
          for (const c of cols) {
            let v = row[c];
            if (v == null) v = '';
            else if (typeof v === 'object') v = JSON.stringify(v);
            else v = String(v);
            if (v.length > 80) v = v.slice(0, 80) + '…';
            html += '<td>' + escapeHtml(v) + '</td>';
          }
          html += '</tr>';
        }
        html += '</tbody></table></div>';
        return html;
      }

      function attachPrehledHandlers(data) {
        if (!data.id_edit) return;  // bez jádra nemá smysl klik na řádek
        mainContent.querySelectorAll(".erp-prehled-row").forEach(tr => {
          tr.addEventListener("click", () => {
            const rowId = tr.getAttribute("data-row-id");
            if (!rowId) return;
            window.location.href = "/erp/jadro/" + data.id_edit + "/" + rowId;
          });
        });
      }

      // ── Helpers ────────────────────────────────────────────────
      function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[c]));
      }
      function escapeAttr(s) {
        return escapeHtml(s).replace(/"/g, "&quot;");
      }

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
