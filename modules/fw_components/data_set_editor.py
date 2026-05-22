"""data_set_editor — Power tool — fw.data_set SQL primitives (sql_text + db_connection).

DB registry: fw.hw_registry name='data_set_editor'
JS implementation: apps/api/static/erp/components/design_data_set_editor.js

Iterace B Vlna 2-2 (22.5.2026): Extract z router.py 5 endpointu do per-komponenta file.
  - GET   /design/data-set/{data_set_id}      — single detail + use_count
  - POST  /design/data-set/create             — create new SQL primitive
  - PATCH /design/data-set/update/{data_set_id} — update sql_text + db_connection
  - POST  /design/data-set/test               — ad-hoc execute SQL preview
  - GET   /design/data-set-list               — list active rows pro picker

Plus register_routes(api_router) classmethod — Marti's "vsechen refaktor dnes" pattern.

Pattern: Marti-AI's "uniformita vitezi" doctrine z 11.5. (Krok 13).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from modules.fw_components.base import ComponentBase


NAME = "data_set_editor"
JS_PATH = "components/design_data_set_editor.js"
BINDING = {"data_set_id": "int?"}
CLASS_NAME = "DataSetEditorComponent"


# Sub-router pro 5 endpointu (registered via register_routes)
_router = APIRouter()


@_router.get("/design/data-set/{data_set_id}")
def design_get_data_set_single(data_set_id: int, req: Request) -> JSONResponse:
    """Krok 5.L-A GET single data_set detail + use count (pocet refs v data_source_op).

    Returns:
        200: { ok, data_set: {id, code, sql_text, db_connection, description, status,
               is_system, created_at}, use_count }  # kind dropped Krok 5.L-D 17.5.2026
        404: data_set neexistuje
    """
    from core.database_data import get_data_session as _gds_gdss
    from sqlalchemy import text as _sql_text_gdss
    from modules.erp.api.router import _get_uid, _require_parent

    uid = _get_uid(req)
    _require_parent(uid)

    ds_session = _gds_gdss()
    try:
        row = ds_session.execute(_sql_text_gdss("""
            SELECT * FROM fw.data_set WHERE id = :id
        """), {"id": data_set_id}).mappings().one_or_none()
        if not row:
            return JSONResponse({"ok": False, "error": f"data_set id={data_set_id} nenalezen"}, status_code=404)

        # Count refs in data_source_op (informativni pro UI warning)
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


@_router.post("/design/data-set/create")
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
    from modules.erp.api.router import _get_uid, _require_parent

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    # Krok 5.L-D (17.5.2026, Marti's "kind matouci"): drop kind field - SQL truth source
    # Krok 5.M (17.5.2026): db_connection VARCHAR -> FK db_connection_id.
    # Backward compat: accept db_connection_id (FK BIGINT) or db_connection (legacy code string).
    sql_text = body.get("sql_text") or ""
    db_conn_id_raw = body.get("db_connection_id")
    db_conn_legacy = body.get("db_connection")  # legacy string code
    description = body.get("description")
    if description is not None:
        description = str(description).strip() or None

    # Code optional - None = NULL v DB (Marti's NULL doctrine)
    code_raw = body.get("code")
    code_normalized = None
    if code_raw is not None:
        code_normalized = str(code_raw).strip() or None

    # Validation
    if not sql_text.strip():
        return JSONResponse({"ok": False, "error": "sql_text povinny"}, status_code=400)

    ds_session = _gds_cds_set()
    try:
        # Resolve db_connection_id (Krok 5.M backward compat)
        db_connection_id = None
        if db_conn_id_raw is not None:
            try:
                db_connection_id = int(db_conn_id_raw)
            except (ValueError, TypeError):
                return JSONResponse({"ok": False, "error": f"db_connection_id musi byt integer, got {db_conn_id_raw!r}"}, status_code=400)
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


@_router.patch("/design/data-set/update/{data_set_id}")
async def design_patch_data_set(data_set_id: int, req: Request) -> JSONResponse:
    """Krok 5.K-B3: PATCH data_set (SQL primitiv) - update sql_text +
    db_connection + description.  # kind dropped Krok 5.L-D 17.5.2026

    Route 3-segment (Marti's gotcha #14b+10) - vyhne collision s generic
    design_patch_entity `/design/{entity_type}/{row_id}`.

    Body: {sql_text?, kind?, db_connection?, description?}
    """
    from core.database_data import get_data_session as _gds_pdset
    from sqlalchemy import text as _sql_text_pdset
    from modules.strategie_pg.application.service import update_row as _spg_update_pdset
    from modules.erp.api.router import _get_uid, _require_parent

    uid = _get_uid(req)
    _require_parent(uid)

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body musi byt JSON"}, status_code=400)

    # Krok 5.L-D (17.5.2026, Marti's "kind matouci"): drop kind z ALLOWED
    # Krok 5.M (17.5.2026): db_connection VARCHAR -> FK db_connection_id.
    # Backward compat: accept db_connection_id (FK BIGINT) or db_connection (legacy code string).
    # Sprint A (17.5.2026 dop.): + status pro archive/restore z UI.
    ALLOWED = ("sql_text", "db_connection_id", "description", "status")
    update_vals: dict[str, Any] = {}
    for k in ALLOWED:
        if k in body:
            update_vals[k] = body[k]
    if "status" in update_vals:
        v = update_vals["status"]
        if v not in ("active", "archived"):
            return JSONResponse({"ok": False, "error": f"status musi byt 'active' nebo 'archived', got {v!r}"}, status_code=400)

    ds_pdset = _gds_pdset()
    try:
        # Legacy db_connection (string code) -> FK resolve
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
            return JSONResponse({"ok": False, "error": "Body musi obsahovat alespon jeden z: sql_text, db_connection_id (nebo db_connection), description"}, status_code=400)
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


@_router.post("/design/data-set/test")
async def design_test_data_set(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Sprint C (17.5.2026 dop.):
    Ad-hoc execute SQL pro data_set draft (preview).

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
    from modules.erp.api.router import _get_uid, _require_parent

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
        return JSONResponse({"ok": False, "error": "sql_text povinny"}, status_code=400)
    if db_conn_id is None:
        return JSONResponse({"ok": False, "error": "db_connection_id povinny"}, status_code=400)

    # SELECT-only guard - Marti-AI Q5 doctrine z 9.5. (strategie_pg_query_raw)
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
            return JSONResponse({"ok": False, "error": f"db_connection id={db_conn_id} nenalezen nebo neaktivni"}, status_code=400)

        # MVP: PostgreSQL only
        if conn_row["db_type"] != "postgres":
            return JSONResponse({
                "ok": False,
                "error": f"MVP test podporuje pouze PostgreSQL. Tento connection je {conn_row['db_type']} ({conn_row['label']}). "
                         "MSSQL test bude dostupny po Phase 30+1.",
            }, status_code=400)
        if conn_row["default_db"] != "data_db":
            return JSONResponse({
                "ok": False,
                "error": f"MVP test podporuje pouze default_db='data_db'. Tento connection je {conn_row['default_db']}.",
            }, status_code=400)

        # Inject LIMIT (HARD_LIMIT_CAP) - pokud uzivatel uz nema v SQL
        params_bound = dict(params) if isinstance(params, dict) else {}
        params_bound["limit"] = limit

        # Statement-level timeout 30s - PostgreSQL parameter
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


@_router.get("/design/data-set-list")  # Sprint B hotfix 17.5. odp: hyphen avoids collision s /design/data-set/{id:int} (Marti's gotcha #14b+10)
def design_list_data_set(req: Request) -> JSONResponse:
    """Phase 38.4 Krok 14g Etapa F Sprint B (17.5.2026 dop.):
    List active fw.data_set rows + JOIN fw.db_connection pro readable label.

    Returns:
        {ok: True, data_sets: [{id, code, sql_text_preview,
          db_connection_id, db_connection, db_connection_label,
          description, use_count, version, status}]}

    use_count = LEFT JOIN COUNT fw.data_source_op references (kolik ops
    pouziva tenhle data_set).
    """
    from core.database_data import get_data_session as _gds_dsl
    from sqlalchemy import text as _sql_dsl
    import logging as _logging_dsl
    from modules.erp.api.router import _get_uid, _require_parent

    _logger_dsl = _logging_dsl.getLogger(__name__)

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
        _logger_dsl.exception(f"design_list_data_set failed: {exc}")
        return JSONResponse(
            {"ok": False, "error": f"List failed: {exc}"},
            status_code=500,
        )
    finally:
        ds.close()


class DataSetEditorComponent(ComponentBase):
    """Power tool - fw.data_set SQL primitives (sql_text + db_connection)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Power tool - fw.data_set SQL primitives editor."

    @classmethod
    def register_routes(cls, parent_router: APIRouter) -> None:
        """Register 5 endpoints na parent api_router.

        Volat raz pri startup v router.py po api_router definici:
            from modules.fw_components.data_set_editor import DataSetEditorComponent
            DataSetEditorComponent.register_routes(api_router)
        """
        parent_router.include_router(_router)
