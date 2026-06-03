"""act_db_insert — backend handler: INSERT řádku do tabulky.

params (act_task_def.params_schema):
    schema, table          — cíl (např. "fw", "phone_dial_request")
    db                     — "pg" (default) | "mssql"
    values                 — statické sloupce {col: const}
    returning              — PK sloupec pro new_id (default "id")
inputs (z input_mapping)   — dynamické sloupce {col: hodnota}

Výsledný řádek = {**values, **inputs}. result: ok(+new_id) / error.
dry_run → nic nevloží, vrátí simulovaný výstup.
"""
from __future__ import annotations

import json
from sqlalchemy import text as _t
from core.database_data import get_data_session


def validate(ctx):
    p = ctx.get("params") or {}
    if not p.get("schema") or not p.get("table"):
        raise ValueError("db_insert: chybí params.schema / params.table")


def run(ctx):
    p = ctx.get("params") or {}
    row = dict(p.get("values") or {})
    row.update(ctx.get("inputs") or {})
    if not row:
        return {"result_code": "error", "output": {"detail": "prázdný řádek"}}

    if ctx.get("dry_run"):
        return {"result_code": "ok", "output": {"new_id": None, "dry_run": True, "row": row}}

    db = (p.get("db") or "pg").lower()
    schema, table = p["schema"], p["table"]
    returning = p.get("returning", "id")

    if db == "mssql":
        # přes EUROSOFT MCP (cross-connection), idempotency_key z kontextu
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return {"result_code": "error", "output": {"detail": "MCP nedostupný"}}
        rj = mcp.call_tool_sync("eurosoft_strategie_insert_row",
                                {"schema": schema, "table": table, "values": row}, conversation_id=None)
        res = json.loads(rj) if isinstance(rj, str) else (rj or {})
        if res.get("ok"):
            return {"result_code": "ok", "output": {"new_id": res.get("id") or res.get("new_id")}}
        return {"result_code": "error", "output": {"detail": res.get("error")}}

    # PG cesta — parametrizovaný INSERT (JSONB hodnoty se castují)
    ds = get_data_session()
    try:
        cols = list(row.keys())
        collist = ", ".join('"%s"' % c for c in cols)
        phs = []
        params = {}
        for c in cols:
            v = row[c]
            if isinstance(v, (dict, list)):
                phs.append("CAST(:%s AS jsonb)" % c)
                params[c] = json.dumps(v)
            else:
                phs.append(":%s" % c)
                params[c] = v
        sql = 'INSERT INTO "%s"."%s" (%s) VALUES (%s) RETURNING "%s"' % (
            schema, table, collist, ", ".join(phs), returning)
        new_id = ds.execute(_t(sql), params).scalar()
        ds.commit()
        return {"result_code": "ok", "output": {"new_id": new_id}}
    except Exception as exc:
        ds.rollback()
        return {"result_code": "error", "output": {"detail": "%s: %s" % (type(exc).__name__, exc)}}
    finally:
        ds.close()
