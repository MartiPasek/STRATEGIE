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

from pydantic import BaseModel, Field

from core.logging import get_logger
from modules.erp.application.centrala_reader import CentralaReader, TYP_NAMES
from modules.erp.application.render_generator import render_form
from modules.erp.application import grid_layout_service
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
      height: 100vh;
      margin: 0;
      overflow: hidden;
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
      padding: 4px 12px !important;
      font-size: 10px;
      border-top: 1px solid var(--border);
      background: var(--surface);
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
      right: 14px;
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
    /* B+7++ (6.5.2026): tree footer (Oblíbené + akce) */
    .erp-tree-footer {{
      padding: 6px 8px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .erp-tree-footer-btn {{
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.12s;
      text-align: left;
    }}
    .erp-tree-footer-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      background: var(--surface);
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
    .erp-tabs-bar {{
      flex: 0 0 auto;
      display: flex;
      align-items: stretch;
      gap: 0;
      background: var(--bg);
      border-bottom: 1px solid var(--border-strong);
      padding: 0 6px 0 0;
      overflow-x: auto;
      overflow-y: hidden;
      scrollbar-width: thin;
    }}
    .erp-tabs-bar[hidden] {{ display: none; }}
    .erp-tab {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 8px 5px 12px;
      max-width: 240px;
      min-width: 80px;
      background: var(--surface2);
      border-right: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 12px;
      cursor: pointer;
      user-select: none;
      -webkit-user-select: none;
      transition: background 0.12s, color 0.12s;
      flex-shrink: 0;
      position: relative;
    }}
    .erp-tab:hover {{
      background: var(--surface);
      color: var(--text);
    }}
    .erp-tab.active {{
      background: var(--surface);
      color: var(--accent);
      font-weight: 500;
      box-shadow: inset 0 -2px 0 var(--accent);
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
      width: min(80vw, 825px);
      max-height: 78vh;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 8px;
      box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55);
      z-index: 100;
      display: flex; flex-direction: column;
      overflow: hidden;
      animation: erp-modal-pop 160ms ease-out;
    }}
    .erp-jadro-pane[hidden] {{ display: none; }}
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
    <!-- B+6.1+ (5.5.2026): ErpUiKit components — reusable napříč Centrála views -->
    <link rel="stylesheet" href="/static/erp/components/components.css?v=''' + _STATIC_VERSION + '''">
    <script src="/static/erp/components/button.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/input.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/checkbox.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/dropdown.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/formlist.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/formsection.js?v=''' + _STATIC_VERSION + '''"></script>
    <script src="/static/erp/components/form.js?v=''' + _STATIC_VERSION + '''"></script>

    <div class="erp-workspace">
      <aside class="erp-tree-pane">
        <!-- B+7++++ (6.5.2026): tree header — text smazán (placeholder
             pro budoucí features), collapse/expand button vpravo -->
        <div class="erp-tree-header">
          <div class="erp-tree-header-slot"></div>
          <button type="button" id="erpTreeToggle" class="erp-tree-toggle-btn"
                  aria-label="Skrýt strom" title="Skrýt strom (Ctrl+B)">
            <span class="erp-tree-toggle-collapse">‹</span>
            <span class="erp-tree-toggle-expand">›</span>
          </button>
        </div>
        <!-- B+7++ (6.5.2026): live filter input nad stromem (Marti's spec) -->
        <div class="erp-tree-search">
          <input type="text" id="erpTreeSearch" class="erp-tree-search-input"
                 placeholder="🔍 Filtrovat strom…" autocomplete="off">
          <button type="button" id="erpTreeSearchClear" class="erp-tree-search-clear"
                  title="Vymazat filtr (Esc)" hidden>×</button>
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
        <!-- B+7++ (6.5.2026): footer slot pro Oblíbené + akce (Marti's spec) -->
        <div id="erpTreeFooter" class="erp-tree-footer">
          <button type="button" class="erp-tree-footer-btn" data-erp-tree-action="oblibene"
                  title="Oblíbené přehledy">★ Oblíbené</button>
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
        // B+8 (6.5.2026): místo loadPrehled → openTab (multi-tab pattern)
        openTab(cislo, item);
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

      // Tree footer button placeholder handlers
      const treeFooterEl = document.getElementById("erpTreeFooter");
      if (treeFooterEl) {
        treeFooterEl.addEventListener("click", (ev) => {
          const btn = ev.target.closest("[data-erp-tree-action]");
          if (!btn) return;
          const action = btn.getAttribute("data-erp-tree-action");
          // Phase A read-only: jen toast informující o budoucím feature
          console.log("Tree footer action:", action);
          // TODO: Phase ?? — implementovat Oblíbené (per-user list FK na cislo_def)
        });
      }

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

      async function openTab(cislo, item) {
        const idx = _findTabIndex(cislo);
        if (idx >= 0) {
          await switchTab(idx);
          return;
        }
        // Nový tab
        const itemId = item ? item.getAttribute("data-id") : null;
        const labelEl = item ? item.querySelector(":scope > .erp-tree-row > .erp-tree-label") : null;
        const labelText = (labelEl && (labelEl.dataset.erpOrigText || labelEl.textContent))
          || ("Přehled #" + cislo);
        const tab = {
          cislo: cislo,
          itemId: itemId,
          label: labelText,
          data: null,
          gridState: null,
        };
        tabsState.tabs.push(tab);
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
            // Scroll into view (s delay aby expand měl čas vykreslit)
            setTimeout(() => {
              if (row && row.scrollIntoView) {
                try { row.scrollIntoView({ block: "nearest", behavior: "smooth" }); } catch (e) {}
              }
            }, 30);
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
        tabsState.tabs.splice(idx, 1);
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

      loadTree();
      // Po load tree (async) zkus restore tabs — počkej krátce na DOM
      setTimeout(restoreTabsFromStorage, 200);
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
