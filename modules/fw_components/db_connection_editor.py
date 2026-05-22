"""db_connection_editor — Power tool — fw.db_connection config (URL + credentials).

DB registry: fw.hw_registry name='db_connection_editor'
JS implementation: apps/api/static/erp/components/design_db_connection_editor.js

Iterace B Vlna 2-1 (22.5.2026): Extract z router.py 2 endpointy do per-komponenta file.
  - PATCH /design/db-connection/update/{conn_id}
  - GET   /system/db-connections

Plus register_routes(api_router) classmethod — Marti's "vsechen refaktor dnes" pattern.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from modules.fw_components.base import ComponentBase


NAME = "db_connection_editor"
JS_PATH = "components/design_db_connection_editor.js"
BINDING = {"db_connection_id": "int?"}
CLASS_NAME = "DbConnectionEditorComponent"


# Sub-router pro 2 endpointy (registered via register_routes)
_router = APIRouter()


@_router.patch("/design/db-connection/update/{conn_id}")
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
    # Import helpers z parent router.py (lazy to avoid circular)
    from modules.erp.api.router import _get_uid, _require_parent

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    ALLOWED = ("label", "description", "default_db", "host", "port",
               "login_name", "scope_databases", "is_active", "sort_order", "status")
    update_vals: dict[str, Any] = {}
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


@_router.get("/system/db-connections")
def system_db_connections(req: Request, include_inactive: bool = False) -> JSONResponse:
    """Krok 5.M-D: List DB connections z fw.db_connection.

    Frontend DesignDataSetEditor + DesignDataSourceEditor fetchnou tento
    endpoint při open místo hardcoded DDS_DB_CONNECTIONS — DB = single
    source of truth. Marti's pattern z 17.5. dop.

    Query params:
        include_inactive: bool (default False) — INTERSOFT placeholder shows
                          jen pokud true (UI dropdown by default skryje)
    """
    from core.database_data import get_data_session as _gds_dbconn
    from sqlalchemy import text as _sql_text_dbconn
    from modules.erp.api.router import _get_uid, _require_parent

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


class DbConnectionEditorComponent(ComponentBase):
    """Power tool — fw.db_connection config (URL + credentials)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Power tool — fw.db_connection config (URL + credentials)."

    @classmethod
    def register_routes(cls, parent_router: APIRouter) -> None:
        """Register 2 endpoints na parent api_router.

        Volat raz pri startup v router.py po api_router definici:
            from modules.fw_components.db_connection_editor import DbConnectionEditorComponent
            DbConnectionEditorComponent.register_routes(api_router)
        """
        parent_router.include_router(_router)
