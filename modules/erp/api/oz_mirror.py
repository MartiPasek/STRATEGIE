"""
OZ mirror (Marti 2.7.2026) — zrcadlení EUROSOFT přehledů (Oběh zboží) na cloud PG.

Doktrína (Marti): NEMIGRUJEME na nové schéma. Každý přehledový MSSQL dotaz běží
tam, kam patří (on-prem DB_EC přes MCP), a jeho VÝSLEDEK se nasype do ploché
produkční PG tabulky `tenant.oz_<...>`. Sloupce = aliasy dotazu (čisté názvy
zadarmo). FW přehled pak čte `SELECT * FROM tenant.oz_<...>` (PG, connection 1).

Schéma cílové tabulky se odvodí z `sp_describe_first_result_set` (běží přes MCP,
NE přes bridge — bridge EXEC=write nevrací řádky).
"""
from __future__ import annotations

import json as _j


def _mcp_query(sql: str, db: str = "DB_EC"):
    """Spustí libovolný SQL na EUROSOFT MSSQL přes MCP, vrátí list dict řádků."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupný")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": db}, conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error") or r)[:300])
        return r.get("rows") or []
    return r or []


def _pg_type(mssql_type: str) -> str:
    """MSSQL system_type_name (např. 'numeric(19,2)', 'nvarchar(255)') → PG typ."""
    t = (mssql_type or "").strip().lower()
    base = t.split("(")[0].strip()
    if base in ("int", "integer"):
        return "integer"
    if base in ("bigint",):
        return "bigint"
    if base in ("smallint", "tinyint"):
        return "smallint"
    if base in ("bit",):
        return "boolean"
    if base in ("numeric", "decimal", "money", "smallmoney"):
        # zachovej přesnost pokud je
        if "(" in t:
            return "numeric" + t[t.index("("):]
        return "numeric"
    if base in ("float", "real"):
        return "double precision"
    if base in ("date",):
        return "date"
    if base in ("datetime", "datetime2", "smalldatetime", "datetimeoffset"):
        return "timestamp"
    if base in ("time",):
        return "time"
    if base in ("uniqueidentifier",):
        return "text"
    if base in ("varbinary", "binary", "image", "timestamp", "rowversion"):
        return "text"  # bin/rowversion nezrcadlíme binárně
    # nvarchar/varchar/nchar/char/text/ntext/xml a cokoli ostatní
    return "text"


def describe(sql: str):
    """sp_describe_first_result_set → [{name, pg_type, ord}] v pořadí sloupců."""
    esc = sql.replace("'", "''")
    rows = _mcp_query("EXEC sp_describe_first_result_set N'%s', NULL, 0" % esc)
    cols = []
    for r in rows:
        nm = r.get("name") if isinstance(r, dict) else None
        st = r.get("system_type_name") if isinstance(r, dict) else None
        ordv = r.get("column_ordinal") if isinstance(r, dict) else None
        if not nm:
            # bezejmenný sloupec (chybějící alias) — pojmenuj
            nm = "col_%s" % (ordv or len(cols) + 1)
        cols.append({"name": str(nm), "pg_type": _pg_type(st or ""), "ord": ordv or (len(cols) + 1)})
    return cols


def _qi(name: str) -> str:
    """Bezpečný quoted identifier pro PG."""
    return '"' + str(name).replace('"', '""') + '"'


def create_table(oz_table: str, cols: list, tenant_id: int = 2, drop: bool = True):
    """Vytvoří tenant.<oz_table> podle sloupců (drop+create). Vrací DDL."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    coldefs = ", ".join("%s %s" % (_qi(c["name"]), c["pg_type"]) for c in cols)
    ddl = "CREATE TABLE tenant.%s (%s)" % (oz_table, coldefs)
    s = get_data_session()
    try:
        if drop:
            s.execute(_t("DROP TABLE IF EXISTS tenant.%s" % oz_table))
        s.execute(_t(ddl))
        s.execute(_t('GRANT ALL ON tenant.%s TO strategie, "Marti-AI"' % oz_table))
        s.commit()
    finally:
        s.close()
    return ddl


def _to_val(v, pg_type):
    if v is None or v == "":
        # prázdný string u n/ časových typů = NULL
        if pg_type != "text":
            return None
        return v
    return v


def fill(oz_table: str, sql: str, cols: list, tenant_id: int = 2, batch: int = 500):
    """Naplní tenant.<oz_table> výsledkem MSSQL dotazu (TRUNCATE + INSERT)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    rows = _mcp_query(sql)
    names = [c["name"] for c in cols]
    types = {c["name"]: c["pg_type"] for c in cols}
    collist = ", ".join(_qi(n) for n in names)
    params = ", ".join(":p%d" % i for i in range(len(names)))
    ins = "INSERT INTO tenant.%s (%s) VALUES (%s)" % (oz_table, collist, params)
    s = get_data_session()
    vloz = 0
    chyb = 0
    prvni = None
    try:
        s.execute(_t("TRUNCATE tenant.%s" % oz_table))
        buf = []

        def _flush(b):
            nonlocal vloz, chyb, prvni
            if not b:
                return
            try:
                s.execute(_t(ins), b)
                s.commit()
                vloz += len(b)
            except Exception as e:  # noqa: BLE001
                s.rollback()
                # per-row fallback
                for one in b:
                    try:
                        s.execute(_t(ins), one)
                        s.commit()
                        vloz += 1
                    except Exception as e2:  # noqa: BLE001
                        s.rollback()
                        chyb += 1
                        if prvni is None:
                            prvni = str(e2)[:200]

        for r in rows:
            d = r if isinstance(r, dict) else {}
            row = {}
            for i, n in enumerate(names):
                val = d.get(n)
                if val is None:
                    # sp_describe názvy sedí na klíče query_raw; kdyby ne, zkus case-insensitive
                    for k in d.keys():
                        if k.lower() == n.lower():
                            val = d[k]
                            break
                row["p%d" % i] = _to_val(val, types[n])
            buf.append(row)
            if len(buf) >= batch:
                _flush(buf)
                buf = []
        _flush(buf)
        return {"ok": True, "vlozeno": vloz, "chyb": chyb, "prvni_chyba": prvni, "zdroj_radku": len(rows)}
    finally:
        s.close()


def _ensure_def_table(tenant_id: int = 2):
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        s.execute(_t(
            "CREATE TABLE IF NOT EXISTS tenant.oz_mirror_def ("
            "oz_table text PRIMARY KEY, fw_code text, sql_mssql text, "
            "last_sync_at timestamp, last_rows int, updated_at timestamp DEFAULT now())"))
        s.execute(_t('GRANT ALL ON tenant.oz_mirror_def TO strategie, "Marti-AI"'))
        s.commit()
    finally:
        s.close()


def mirror(fw_code: str, oz_table: str, tenant_id: int = 2, repoint: bool = True):
    """Kompletní zrcadlení: vezme MSSQL dotaz z fw.data_set[fw_code], odvodí schéma,
    vytvoří tenant.<oz_table>, naplní, uloží def a přepne fw.data_set na PG."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    _ensure_def_table(tenant_id)
    s = get_data_session()
    try:
        src = s.execute(_t(
            "SELECT dset.sql_text, dset.db_connection_id, dset.id AS dsid "
            "FROM fw.data_source ds JOIN fw.data_source_op op ON op.data_source_id=ds.id "
            "JOIN fw.data_set dset ON dset.id=op.data_set_id "
            "WHERE ds.code=:c AND op.operation_kind='select'"),
            {"c": fw_code}).mappings().first()
    finally:
        s.close()
    if not src:
        return {"ok": False, "error": "fw.data_set pro %s nenalezen" % fw_code}
    sql_mssql = src["sql_text"]
    if "tenant." in sql_mssql.lower() and "from tenant.oz_" in sql_mssql.lower():
        # už přepnuto na PG — vezmi uloženou MSSQL definici
        s2 = get_data_session()
        try:
            saved = s2.execute(_t("SELECT sql_mssql FROM tenant.oz_mirror_def WHERE oz_table=:o"),
                               {"o": oz_table}).scalar()
        finally:
            s2.close()
        if saved:
            sql_mssql = saved
        else:
            return {"ok": False, "error": "data_set už přepnut na PG a chybí uložený MSSQL def"}

    cols = describe(sql_mssql)
    if not cols:
        return {"ok": False, "error": "sp_describe nevrátil sloupce"}
    create_table(oz_table, cols, tenant_id=tenant_id, drop=True)
    res = fill(oz_table, sql_mssql, cols, tenant_id=tenant_id)

    s3 = get_data_session()
    try:
        s3.execute(_t(
            "INSERT INTO tenant.oz_mirror_def(oz_table,fw_code,sql_mssql,last_sync_at,last_rows) "
            "VALUES(:o,:f,:q,now(),:n) ON CONFLICT (oz_table) DO UPDATE SET "
            "fw_code=EXCLUDED.fw_code, sql_mssql=EXCLUDED.sql_mssql, last_sync_at=now(), "
            "last_rows=EXCLUDED.last_rows, updated_at=now()"),
            {"o": oz_table, "f": fw_code, "q": sql_mssql, "n": res.get("vlozeno")})
        if repoint:
            s3.execute(_t("UPDATE fw.data_set SET db_connection_id=1, sql_text=:q WHERE id=:i"),
                       {"q": "SELECT * FROM tenant.%s" % oz_table, "i": src["dsid"]})
        s3.commit()
    finally:
        s3.close()
    return {"ok": True, "oz_table": oz_table, "fw_code": fw_code, "sloupcu": len(cols),
            "vlozeno": res.get("vlozeno"), "chyb": res.get("chyb"),
            "prvni_chyba": res.get("prvni_chyba"), "repoint": repoint,
            "cols": [c["name"] + " " + c["pg_type"] for c in cols]}


# Plán zrcadel: (fw.data_source code, cílová PG tabulka). Zkratky Marti 2.7.:
# prij_ = přijaté, vy_ = vydané, fa = faktury.
_OZ_PLAN = [
    ("vp_zakazky", "oz_zakazky"),
    ("vp_poptavky", "oz_prij_popt"),
    ("vp_kalkulace", "oz_nabidky"),
    ("vp_prijate_obj", "oz_prij_obj"),
    ("vp_kalk_nakup", "oz_kalkulace"),
    ("vp_vydane_obj", "oz_vy_obj"),
    ("fin_prijate_faktury", "oz_prij_fa"),
    ("fin_vydane_faktury", "oz_vy_fa"),
]


def mirror_all(tenant_id: int = 2, plan=None):
    """Sekvenčně zrcadlí všechny přehledy z plánu (jeden po druhém — MCP rate limit)."""
    res = []
    for fw, tbl in (plan or _OZ_PLAN):
        try:
            r = mirror(fw, tbl, tenant_id=tenant_id)
            res.append({"oz": tbl, "ok": r.get("ok"), "vlozeno": r.get("vlozeno"),
                        "chyb": r.get("chyb"), "err": r.get("error") or r.get("prvni_chyba")})
        except Exception as e:  # noqa: BLE001
            res.append({"oz": tbl, "ok": False, "err": str(e)[:200]})
    return {"ok": True, "vysledky": res}


def sync_all(tenant_id: int = 2):
    """Obnoví data ve všech zrcadlech z uložených MSSQL dotazů (scheduled refresh)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        tbls = [r[0] for r in s.execute(_t("SELECT oz_table FROM tenant.oz_mirror_def ORDER BY oz_table"))]
    finally:
        s.close()
    res = []
    for t in tbls:
        try:
            r = sync(t, tenant_id=tenant_id)
            res.append({"oz": t, "vlozeno": r.get("vlozeno"), "chyb": r.get("chyb"), "err": r.get("error")})
        except Exception as e:  # noqa: BLE001
            res.append({"oz": t, "err": str(e)[:200]})
    return {"ok": True, "vysledky": res}


def sync(oz_table: str, tenant_id: int = 2):
    """Obnoví data v tenant.<oz_table> z uloženého MSSQL dotazu (pro scheduled refresh)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        d = s.execute(_t("SELECT fw_code, sql_mssql FROM tenant.oz_mirror_def WHERE oz_table=:o"),
                      {"o": oz_table}).mappings().first()
    finally:
        s.close()
    if not d:
        return {"ok": False, "error": "oz_mirror_def pro %s neexistuje" % oz_table}
    cols = describe(d["sql_mssql"])
    res = fill(oz_table, d["sql_mssql"], cols, tenant_id=tenant_id)
    s2 = get_data_session()
    try:
        s2.execute(_t("UPDATE tenant.oz_mirror_def SET last_sync_at=now(), last_rows=:n WHERE oz_table=:o"),
                   {"n": res.get("vlozeno"), "o": oz_table})
        s2.commit()
    finally:
        s2.close()
    return {"ok": True, "oz_table": oz_table, "vlozeno": res.get("vlozeno"), "chyb": res.get("chyb")}
