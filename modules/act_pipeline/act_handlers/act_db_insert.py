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
        # přes EUROSOFT MCP (cross-connection). MCP tool strategie_insert_row
        # ocekava `data` (ne `values`) + `db_name` (None=DB_ST, "DB_EC"=Centrala).
        # CRM tabulky (st.*) zijou v DB_EC -> params musi mit db_name="DB_EC".
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return {"result_code": "error", "output": {"detail": "MCP nedostupný"}}
        # Audit actor (Marti 4.6.): Autor/Zmenil = jmeno uzivatele co pipeline
        # spustil (ne MCP service login). Text z user_tenants.db_login per
        # tenant (EUROSOFT: Marti->"Martin", Pavel->"PZeman"), fallback na jmeno
        # z profilu. Jen text — uzivatel NEmusi byt EUROSOFT DB user. Opt-in
        # pres params.audit_tenant_id; nikdy neshodi insert.
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
                    row.setdefault("Autor", _nm)
                    row.setdefault("Zmenil", _nm)
            except Exception:
                pass  # audit selhani nesmi shodit insert akce
        args = {"schema": schema, "table": table, "data": row}
        if p.get("db_name"):
            args["db_name"] = p["db_name"]
        rj = mcp.call_tool_sync("eurosoft_strategie_insert_row", args, conversation_id=None)
        if rj is None or (isinstance(rj, str) and rj.strip() == ""):
            return {"result_code": "error", "output": {"detail": "MCP vrátil prázdnou odpověď (insert)"}}
        res = json.loads(rj) if isinstance(rj, str) else (rj or {})
        if isinstance(res, dict) and res.get("ok"):
            return {"result_code": "ok", "output": {"new_id": res.get("id") or res.get("new_id")}}
        _det = (res.get("message") or res.get("exception_repr") or res.get("error")
                if isinstance(res, dict) else str(res))
        return {"result_code": "error", "output": {"detail": _det}}

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
