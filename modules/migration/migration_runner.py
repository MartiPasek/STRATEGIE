"""Reusable migration runner — server-side, parent-only, davkovany.

Jednu migraci = "precti zdroj (MSSQL pres tepy MCP v hlavnim procesu) a nakrm
JSON do cilove PG funkce (spustene jako Marti-AI)". Bezi v HLAVNIM procesu, kde
je MCP klient tepy a rychly (na rozdil od sandbox subprocessu, kde se MCP SSE
klient cold-startuje a zasekava). Data nikdy neopusti server.

Znovupouzitelne: kazda dalsi migrace = INSERT radku do fw.migration_job
(zdrojovy SQL + cilova funkce + argy). Zadny novy kod per migrace.

Velke objemy: davkovani (batch_size) — cte + zapisuje po blocich pres MSSQL
OFFSET/FETCH (vyzaduje order_by), commit PO KAZDE DAVCE. Postup se prubezne
uklada; re-run plynule pokracuje (idempotence pres hr_source_ref guard
v cilove funkci). Pamet i payload zustavaji omezene bez ohledu na celkovy objem.

Registr (fw.migration_job):
  code          text PK         -- napr. 'hr_employees'
  source_db     text NOT NULL   -- napr. 'DB_EC' (MSSQL pres EUROSOFT MCP)
  source_sql    text NOT NULL   -- SELECT bez ORDER BY (wrapuje se TOP/OFFSET)
  target_schema text NOT NULL   -- napr. 'mod'
  target_fn     text NOT NULL   -- napr. 'hr_ingest_employees'
  arg_order     jsonb NOT NULL  -- poradi argumentu, napr. ["payload","tenant","batch"]
                                --   "payload" = JSON radku ze zdroje -> (:payload)::jsonb
                                --   ostatni = skalarni binds z default_args / body.args
  order_by      text            -- sloupec pro stabilni pagination (napr. 'ID');
                                --   musi byt ve vystupu source_sql. Nutny pro batch_size.
  default_args  jsonb DEFAULT {} -- napr. {"tenant":2,"batch":"dbec"}
  description   text
  updated_at    timestamp

Endpoint:
  POST /api/v1/erp/migrate/{job_code}
    body (vse volitelne): {"limit": int, "batch_size": int, "dry_run": bool, "args": {...}}
      limit      -> TOP (N) jednorazove (test); ignoruje batch_size
      batch_size -> davkovani po N (velke objemy); vyzaduje order_by; commit per davka
      dry_run    -> spusti + vrati pocty, ale ROLLBACK kazde davky (nic nezapise)
      args       -> override default_args (napr. {"batch":"dbec-test"})
    returns: {ok, job_code, source_rows, batches, dry_run, result, runtime_ms}

  GET /api/v1/erp/migrate/_jobs
    -> seznam registrovanych jobu

Doctrine:
  - parent-only (_require_parent)
  - idempotence v cilove PG funkci (hr_source_ref guard); commit per davka = resumable
  - zadne arbitrary SQL z requestu — jen pojmenovane joby z registru
  - identifikatory (schema/fn/order_by) validovany regexem (defense-in-depth)
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
# order_by smi byt "ID" nebo "alias.ID" nebo "ID DESC" (jen bezpecne znaky)
_ORDER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?( (ASC|DESC))?$")
_MAX_BATCHES = 100000  # tvrda pojistka proti nekonecne smycce

_router = APIRouter()


def _load_job(job_code: str) -> dict | None:
    from modules.strategie_pg.application.service import get_session as _pg_marti
    from sqlalchemy import text as _sql

    with _pg_marti() as s:
        row = s.execute(
            _sql(
                "SELECT code, source_db, source_sql, target_schema, target_fn, "
                "arg_order, order_by, default_args, description "
                "FROM fw.migration_job WHERE code = :c"
            ),
            {"c": job_code},
        ).mappings().first()
    return dict(row) if row else None


def _mcp_read(mcp, sql: str, db_name: str) -> list[dict]:
    """DB_EC read pres tepy MCP. Vrati list[dict] nebo raise RuntimeError."""
    rj = mcp.call_tool_sync(
        "eurosoft_strategie_query_raw",
        {"sql": sql, "db_name": db_name},
        conversation_id=None,
    )
    res = json.loads(rj) if isinstance(rj, str) else rj
    if not isinstance(res, dict) or not res.get("ok"):
        err = res.get("error") if isinstance(res, dict) else str(res)
        raise RuntimeError(f"MCP query error: {err}")
    return res.get("rows") or []


def _accumulate(total: dict, part) -> dict:
    """Secti numericke klice z vysledku funkce napric davkami."""
    if isinstance(part, str):
        try:
            part = json.loads(part)
        except Exception:
            return total
    if isinstance(part, dict):
        for k, v in part.items():
            if isinstance(v, (int, float)):
                total[k] = total.get(k, 0) + v
    return total


@_router.get("/migrate/_jobs")
async def list_migration_jobs(req: Request) -> JSONResponse:
    from modules.erp.api.router import _get_uid, _require_parent
    from modules.strategie_pg.application.service import get_session as _pg_marti
    from sqlalchemy import text as _sql

    uid = _get_uid(req)
    _require_parent(uid)

    with _pg_marti() as s:
        rows = s.execute(
            _sql(
                "SELECT code, source_db, target_schema, target_fn, arg_order, "
                "order_by, default_args, description, updated_at "
                "FROM fw.migration_job ORDER BY code"
            )
        ).mappings().all()
    return JSONResponse({"ok": True, "jobs": [dict(r) for r in rows], "count": len(rows)}, status_code=200)


@_router.post("/migrate/{job_code}")
async def run_migration_job(job_code: str, req: Request) -> JSONResponse:
    from modules.erp.api.router import _get_uid, _require_parent
    from modules.strategie_pg.application.service import get_session as _pg_marti
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    from core.log_queue import log_event
    from sqlalchemy import text as _sql

    uid = _get_uid(req)
    _require_parent(uid)

    # ── body ──
    limit = None
    batch_size = None
    dry_run = False
    body_args: dict[str, Any] = {}
    try:
        body = await req.json()
        if isinstance(body, dict):
            if body.get("limit") not in (None, "", 0, "0"):
                limit = int(body["limit"])
            if body.get("batch_size") not in (None, "", 0, "0"):
                batch_size = int(body["batch_size"])
            dry_run = bool(body.get("dry_run"))
            if isinstance(body.get("args"), dict):
                body_args = body["args"]
    except Exception:
        pass

    # ── job ──
    job = _load_job(job_code)
    if not job:
        return JSONResponse({"ok": False, "error": f"migration_job '{job_code}' neexistuje"}, status_code=404)

    schema = job["target_schema"]
    fn = job["target_fn"]
    if not _IDENT_RE.match(schema or "") or not _IDENT_RE.match(fn or ""):
        return JSONResponse({"ok": False, "error": f"neplatny target_schema/target_fn: {schema!r}.{fn!r}"}, status_code=400)
    arg_order = job["arg_order"] or []
    if not isinstance(arg_order, list) or "payload" not in arg_order:
        return JSONResponse({"ok": False, "error": "arg_order musi byt list obsahujici 'payload'"}, status_code=400)
    order_by = (job.get("order_by") or "").strip()
    if batch_size and not order_by:
        return JSONResponse({"ok": False, "error": "batch_size vyzaduje order_by v jobu (stabilni pagination)"}, status_code=400)
    if order_by and not _ORDER_RE.match(order_by):
        return JSONResponse({"ok": False, "error": f"neplatny order_by: {order_by!r}"}, status_code=400)

    # ── call_sql (bezpecne binds; v registru zadny bind-syntax) ──
    parts = []
    for a in arg_order:
        if not _IDENT_RE.match(str(a)):
            return JSONResponse({"ok": False, "error": f"neplatny arg name: {a!r}"}, status_code=400)
        parts.append("(:payload)::jsonb" if a == "payload" else f":{a}")
    call_sql = f"SELECT {schema}.{fn}({', '.join(parts)})"

    base_params: dict[str, Any] = {}
    merged = dict(job["default_args"] or {})
    merged.update(body_args)
    for k, v in merged.items():
        if k != "payload":
            base_params[k] = v

    started = time.monotonic()
    try:
        log_event(
            level="info", source="py", module_id=f"migration.{job_code}",
            message=f"START job={job_code} limit={limit} batch_size={batch_size} dry_run={dry_run}",
            extra={"uid": uid, "limit": limit, "batch_size": batch_size, "dry_run": dry_run, "args": body_args},
        )
    except Exception:
        pass

    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        return JSONResponse({"ok": False, "error": "MCP klient nedostupny (eurosoft_mcp_enabled=False)"}, status_code=503)

    src = job["source_sql"]

    def _run_chunk(rows: list[dict]) -> Any:
        """Spusti cilovou funkci na jedne davce; commit / dry_run rollback."""
        params = dict(base_params)
        params["payload"] = json.dumps(rows, ensure_ascii=False, default=str)
        with _pg_marti() as s:
            row = s.execute(_sql(call_sql), params).fetchone()
            res = row[0] if row else None
            if dry_run:
                s.rollback()
            else:
                s.commit()
            return res

    total: dict[str, Any] = {}
    source_rows = 0
    batches = 0

    try:
        if limit:
            # ── test: jedna davka TOP (N) ──
            chunk_sql = f"SELECT TOP ({int(limit)}) _q.* FROM (\n{src}\n) AS _q"
            rows = _mcp_read(mcp, chunk_sql, job["source_db"])
            source_rows = len(rows)
            batches = 1
            _accumulate(total, _run_chunk(rows))
        elif batch_size:
            # ── velky objem: pagination OFFSET/FETCH, commit per davka ──
            off = 0
            while batches < _MAX_BATCHES:
                chunk_sql = (
                    f"SELECT _q.* FROM (\n{src}\n) AS _q "
                    f"ORDER BY {order_by} "
                    f"OFFSET {int(off)} ROWS FETCH NEXT {int(batch_size)} ROWS ONLY"
                )
                rows = _mcp_read(mcp, chunk_sql, job["source_db"])
                if not rows:
                    break
                source_rows += len(rows)
                batches += 1
                _accumulate(total, _run_chunk(rows))
                if len(rows) < batch_size:
                    break
                off += batch_size
        else:
            # ── maly objem: vse najednou ──
            rows = _mcp_read(mcp, src, job["source_db"])
            source_rows = len(rows)
            batches = 1 if rows else 0
            if rows:
                _accumulate(total, _run_chunk(rows))
    except Exception as e:
        try:
            log_event(
                level="error", source="py", module_id=f"migration.{job_code}",
                message=f"FAIL job={job_code} po {batches} davkach / {source_rows} radcich: {type(e).__name__}: {e}",
                extra={"uid": uid, "call_sql": call_sql, "batches_done": batches, "rows_done": source_rows},
            )
        except Exception:
            pass
        return JSONResponse(
            {"ok": False, "error": f"{type(e).__name__}: {e}",
             "job_code": job_code, "batches_done": batches, "rows_done": source_rows,
             "partial_result": total, "note": "commit per davka — uz zapsane davky zustavaji, re-run pokracuje (idempotence)"},
            status_code=500,
        )

    runtime_ms = int((time.monotonic() - started) * 1000)
    try:
        log_event(
            level="info", source="py", module_id=f"migration.{job_code}",
            message=f"DONE job={job_code} rows={source_rows} batches={batches} dry_run={dry_run} result={total}",
            extra={"uid": uid, "source_rows": source_rows, "batches": batches, "dry_run": dry_run, "result": total},
        )
    except Exception:
        pass

    return JSONResponse(
        {"ok": True, "job_code": job_code, "source_rows": source_rows,
         "batches": batches, "dry_run": dry_run, "result": total, "runtime_ms": runtime_ms},
        status_code=200,
    )


def register_routes(parent_router: APIRouter) -> None:
    """Volat raz pri startup v router.py:
        from modules.migration.migration_runner import register_routes as register_migration_routes
        register_migration_routes(api_router)
    """
    parent_router.include_router(_router)
