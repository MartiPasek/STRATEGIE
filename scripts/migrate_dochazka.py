"""Migrace EC_Dochazka (Centrala 1, MSSQL DB_EC) -> tenant.att_* (PostgreSQL).

Idempotentni: UPSERT podle (tenant_id, source_system, source_id=EC_Dochazka.ID).
Opakovatelne -> da se pustit znovu pro doimport aktualniho mesice.

Spusteni na cloud APP (ma pristup k PG i k EUROSOFT MCP):
    cd C:\\Projekty\\STRATEGIE
    python -m poetry run python scripts/migrate_dochazka.py            # cely 2026 (od 1.1.)
    python -m poetry run python scripts/migrate_dochazka.py 2026-06-01 # jen od data

Tenant: env DOCHAZKA_TENANT_ID (default 1). POZN.: EC_Dochazka = jen odpracovany
cas (prace na zakazce / rezie). Absence (dovolena/nemoc/OCR) a vychozi stavy konta
NEJSOU v teto tabulce -> doplnime z jineho zdroje zvlast.  Marti 6.6.2026.
"""
import os
import sys
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("migrate_dochazka")

TENANT_ID = int(os.environ.get("DOCHAZKA_TENANT_ID", "1"))
SOURCE_SYSTEM = "centrala1"
FROM_DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-01-01"
PAGE = 1000


def mcp_query(sql):
    """Cti z MSSQL DB_EC pres EUROSOFT MCP. Vraci list dict radku."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupny (spustit na cloud APP).")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
    res = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(res, dict):
        if res.get("ok") is False:
            raise RuntimeError("MCP error: %s" % res.get("error"))
        for k in ("rows", "data", "result", "records"):
            v = res.get(k)
            if isinstance(v, list):
                return v
    if isinstance(res, list):
        return res
    raise RuntimeError("Neznamy tvar MCP odpovedi: %s" % str(res)[:200])


def _i(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def main():
    from core.database_data import get_data_session
    from sqlalchemy import text
    ds = get_data_session()
    try:
        # 1) Zajisti typy zaznamu (prace / rezie).
        def ensure_type(code, label, category):
            r = ds.execute(text("SELECT id FROM tenant.att_entry_type "
                                "WHERE tenant_id=:t AND code=:c"),
                           {"t": TENANT_ID, "c": code}).first()
            if r:
                return r[0]
            r = ds.execute(text(
                "INSERT INTO tenant.att_entry_type "
                "(tenant_id,code,label,category,is_paid,affects_balance,"
                " requires_approval,is_active,created_at,updated_at) "
                "VALUES (:t,:c,:l,:cat,true,true,false,true,now(),now()) RETURNING id"),
                {"t": TENANT_ID, "c": code, "l": label, "cat": category}).first()
            return r[0]
        type_work = ensure_type("work", "Prace", "presence")
        type_oh = ensure_type("overhead", "Rezie", "presence")
        ds.commit()
        log.info("entry_type: work=%s overhead=%s tenant=%s from=%s",
                 type_work, type_oh, TENANT_ID, FROM_DATE)

        # 2) Cache zamestnancu (upsert podle cisla zamestnance).
        emp_cache = {}

        def emp_id(cislo):
            key = str(cislo)
            if key in emp_cache:
                return emp_cache[key]
            r = ds.execute(text("SELECT id FROM tenant.att_employee "
                                "WHERE tenant_id=:t AND cislo_zam=:c"),
                           {"t": TENANT_ID, "c": key}).first()
            if not r:
                r = ds.execute(text(
                    "INSERT INTO tenant.att_employee "
                    "(tenant_id,cislo_zam,is_active,created_at,updated_at) "
                    "VALUES (:t,:c,true,now(),now()) RETURNING id"),
                    {"t": TENANT_ID, "c": key}).first()
            emp_cache[key] = r[0]
            return r[0]

        def map_source(lf):
            return {"D": "tablet", "C": "manual", "A": "mobile_app"}.get(
                (lf or "").strip().upper(), "import")

        def map_status(ved, sef, uz):
            if _i(uz):
                return "locked"
            if _i(ved) and _i(sef):
                return "approved"
            return "pending"

        # 3) Cti EC_Dochazka po strankach (podle ID) a UPSERT do att_entry.
        last_id = 0
        total = ins = upd = 0
        while True:
            sql = (
                "SELECT TOP %d ID, CisloZam, "
                "CONVERT(varchar(10),DatumPripadu,23) AS d, "
                "CONVERT(varchar(19),CasZacatek,120) AS z, "
                "CONVERT(varchar(19),CasKonec,120) AS k, "
                "CasPauza, CasCelkemZakazka AS hod, CisloZakazky, DruhCinnosti, "
                "LoginFrom, CAST(VedSchvaleno AS int) AS ved, "
                "CAST(SefSchvaleno AS int) AS sef, CAST(Uzavreno AS int) AS uz, "
                "ZamPoznamka "
                "FROM EC_Dochazka WHERE DatumPripadu >= '%s' AND ID > %d "
                "ORDER BY ID" % (PAGE, FROM_DATE, last_id))
            rows = mcp_query(sql)
            if not rows:
                break
            for r in rows:
                rid = int(r["ID"])
                last_id = rid
                total += 1
                zak = (r.get("CisloZakazky") or "").strip()
                is_rezie = zak.lower() == "rezie"
                params = {
                    "t": TENANT_ID,
                    "emp": emp_id(r["CisloZam"]),
                    "d": r.get("d"),
                    "et": type_oh if is_rezie else type_work,
                    "h": r.get("hod"),
                    "z": r.get("z"),
                    "k": r.get("k"),
                    "br": _i(r.get("CasPauza")),
                    "proj": None if is_rezie else (zak or None),
                    "note": (r.get("ZamPoznamka") or None),
                    "st": map_status(r.get("ved"), r.get("sef"), r.get("uz")),
                    "src": map_source(r.get("LoginFrom")),
                    "ss": SOURCE_SYSTEM,
                    "sid": rid,
                }
                res = ds.execute(text(
                    "UPDATE tenant.att_entry SET employee_id=:emp, entry_date=:d, "
                    "entry_type_id=:et, hours=:h, started_at=:z, ended_at=:k, "
                    "break_minutes=:br, project_ref=:proj, note=:note, status=:st, "
                    "source=:src, updated_at=now() "
                    "WHERE tenant_id=:t AND source_system=:ss AND source_id=:sid"),
                    params)
                if (res.rowcount or 0) == 0:
                    ds.execute(text(
                        "INSERT INTO tenant.att_entry "
                        "(tenant_id,employee_id,entry_date,entry_type_id,hours,"
                        " started_at,ended_at,break_minutes,project_ref,note,status,"
                        " source,source_system,source_id,is_active,created_at,updated_at) "
                        "VALUES (:t,:emp,:d,:et,:h,:z,:k,:br,:proj,:note,:st,:src,"
                        ":ss,:sid,false,now(),now())"), params)
                    ins += 1
                else:
                    upd += 1
                if total % 500 == 0:
                    ds.commit()
                    log.info("... %d (ins %d upd %d) last_id=%d", total, ins, upd, last_id)
            ds.commit()
        log.info("HOTOVO: %d radku (ins %d, upd %d), zamestnancu %d",
                 total, ins, upd, len(emp_cache))
    except Exception:
        ds.rollback()
        raise
    finally:
        ds.close()


if __name__ == "__main__":
    main()
