"""act_note_writeback — backend handler: propíše poznámku do cílové tabulky.

Dva módy (params.mode):
  - "update_column" — UPDATE cíl SET note_column = :note WHERE id_column = :row_id.
                      Funguje hned (PG i MSSQL přes MCP).
  - "insert_action" — vloží Akci (typ + entita) do akční tabulky. Vyžaduje FW
                      systém akcí (katalog typů) — zatím TODO → vrací 'skip' +
                      log, ať flow nespadne (Marti: nejdřív engine, akce potom).

params: mode, schema, table, note_column, id_column (default "id"), db ("pg"|"mssql")
inputs: note (text), row_id (klíč cílového řádku)
result: ok / skip
"""
from __future__ import annotations

import json
from sqlalchemy import text as _t
from core.database_data import get_data_session


def run(ctx):
    p = ctx.get("params") or {}
    inp = ctx.get("inputs") or {}
    mode = (p.get("mode") or "update_column").lower()
    note = inp.get("note")
    row_id = inp.get("row_id")

    if note is None or row_id is None:
        return {"result_code": "skip", "output": {"detail": "chybí note nebo row_id"}}

    if ctx.get("dry_run"):
        return {"result_code": "ok", "output": {"mode": mode, "dry_run": True}}

    if mode == "insert_action":
        # FW systém akcí (katalog typů) zatím není — neblokuj flow.
        return {"result_code": "skip", "output": {"detail": "insert_action čeká na FW systém akcí (TODO)"}}

    # update_column
    schema, table = p.get("schema"), p.get("table")
    note_col = p.get("note_column")
    id_col = p.get("id_column", "id")
    if not (schema and table and note_col):
        return {"result_code": "skip", "output": {"detail": "neúplná params pro update_column"}}

    db = (p.get("db") or "pg").lower()
    if db == "mssql":
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return {"result_code": "skip", "output": {"detail": "MCP nedostupný"}}
        rj = mcp.call_tool_sync("eurosoft_strategie_update_row",
                                {"schema": schema, "table": table,
                                 "values": {note_col: note}, "where": {id_col: row_id}},
                                conversation_id=None)
        res = json.loads(rj) if isinstance(rj, str) else (rj or {})
        return {"result_code": "ok" if res.get("ok") else "skip", "output": {"detail": res.get("error")}}

    ds = get_data_session()
    try:
        sql = 'UPDATE "%s"."%s" SET "%s" = :note WHERE "%s" = :rid' % (schema, table, note_col, id_col)
        ds.execute(_t(sql), {"note": note, "rid": row_id})
        ds.commit()
        return {"result_code": "ok", "output": {"updated": True}}
    except Exception as exc:
        ds.rollback()
        return {"result_code": "skip", "output": {"detail": "%s: %s" % (type(exc).__name__, exc)}}
    finally:
        ds.close()
