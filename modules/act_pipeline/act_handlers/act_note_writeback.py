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
        # MCP tool strategie_update_row ocekava `data` (ne `values`) + `db_name`.
        _data = {note_col: note}
        # Audit (Marti 4.6.): Zmenil = jmeno uzivatele co update spustil (text
        # z user_tenants.db_login per tenant, fallback profil). Opt-in pres
        # params.audit_tenant_id; nikdy neshodi update.
        _audit_tid = p.get("audit_tenant_id")
        _uid = ctx.get("started_by_user_id")
        if _audit_tid and _uid:
            try:
                _dsa = get_data_session()
                try:
                    _nm = _dsa.execute(_t(
                        "SELECT COALESCE(NULLIF(ut.db_login,''), NULLIF(u.short_name,''), "
                        "NULLIF(BTRIM(CONCAT(u.first_name,' ',u.last_name)),''), 'user_'||u.id) "
                        "FROM public.users u "
                        "LEFT JOIN public.user_tenants ut ON ut.user_id=u.id AND ut.tenant_id=:tid "
                        "WHERE u.id=:uid"),
                        {"uid": _uid, "tid": int(_audit_tid)}).scalar()
                finally:
                    _dsa.close()
                if _nm:
                    _data.setdefault("Zmenil", _nm)
            except Exception:
                pass
        args = {"schema": schema, "table": table,
                "data": _data, "where": {id_col: row_id}}
        if p.get("db_name"):
            args["db_name"] = p["db_name"]
        rj = mcp.call_tool_sync("eurosoft_strategie_update_row", args, conversation_id=None)
        if rj is None or (isinstance(rj, str) and rj.strip() == ""):
            return {"result_code": "skip", "output": {"detail": "MCP vrátil prázdnou odpověď (update)"}}
        res = json.loads(rj) if isinstance(rj, str) else (rj or {})
        _ok = isinstance(res, dict) and res.get("ok")
        _det = (res.get("message") or res.get("exception_repr") or res.get("error")
                if isinstance(res, dict) else str(res))
        return {"result_code": "ok" if _ok else "skip", "output": {"detail": _det}}

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
