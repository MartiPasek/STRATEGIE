# ============================================================================
# fw.executable_artifact orchestrator
# ID: 3
# CODE: hr_migrate_dbec
# ============================================================================
"""HR migrace z DB_EC do mod.* (PostgreSQL) — server-side, idempotentni.

Cte DB_EC pres EUROSOFT MCP (eurosoft_strategie_query_raw) a vola nainstalovane
PG funkce mod.hr_ingest_employees + mod.hr_ingest_contacts pres psycopg2
(STRATEGIE_DATA_DB_URL injektovany v trusted sandbox path, with_strategie_pythonpath=True).

Cela logika mapovani / provenance / idempotence je v PG funkcich (hr_source_ref
guard). Tento skript jen prenese JSON z DB_EC do tech funkci. Data nikdy
neopusti server (zadny pyodbc, zadne heslo, zadny bridge).

Vstup (SANDBOX_CONTEXT env var, JSON):
  {
    "limit": int|null,       # TOP N zamestnancu (test); null/0 = vsichni
    "dry_run": bool,         # true = spusti + vrati pocty, ale ROLLBACK (nic nezapise)
    "skip_contacts": bool,   # true = jen zamestnanci (kontakty preskocit)
    "batch": str             # migration_batch tag (default 'dbec')
  }

Doctrine (Marti):
  - zadny tichy ok=True na chybe -> RAISE (runner zapise ok=False + stdout duvod)
  - "ID je svaty" / idempotentni (funkce maji hr_source_ref UNIQUE guard)
  - tenant = 2 (EUROSOFT)
"""
import os
import sys
import json

import psycopg2

# Windows subprocess stdout = cp1252 -> diakritika by crashla UnicodeEncodeError.
# PYTHONIOENCODING=utf-8 to resi v python_runneru; tohle je 2. pojistka.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TENANT_EUROSOFT = 2
MSSQL_DB = "DB_EC"

# Sloupce zamestnancu — nazvy MUSI sedet na klice, ktere cte mod.hr_ingest_employees.
# Overeno proti INFORMATION_SCHEMA.COLUMNS (5.6.2026): vsechny existuji 1:1.
EMP_COLS = (
    "z.ID, z.Jmeno, z.Prijmeni, z.RodnePrijmeni, z.TitulPred, z.TitulZa, "
    "z.DatumNarozeni, z.RodneCislo, z.Pohlavi, z.MistoNarozeni, z.StatNarozeni, "
    "z.Narodnost, z.RodinnyStav, z.StatniPrislus, z.OsobniIC, z.VyraditZPrehledu, "
    "z.AdrTrvUlice, z.AdrTrvOrCislo, z.AdrTrvPopCislo, z.AdrTrvMisto, z.AdrTrvPSC, z.AdrTrvZeme, "
    "z.AdrPrechUlice, z.AdrPrechOrCislo, z.AdrPrechPopCislo, z.AdrPrechMisto, z.AdrPrechPSC, z.AdrPrechZeme, "
    "z.AdrKontJmeno, z.AdrKontPrijmeni, "
    "e._Firma, e._HPP, e._DPP, e._OSVC, e._DatumNastupu, e._DatumOdchodu, e._neaktivni"
)


def _fail(msg):
    """Vytiskni duvod + RAISE (ne sys.exit!) -> runner wrapper chytne Exception
    a zapise ok=False SE zachycenym stdoutem (duvod)."""
    print()
    print("=" * 70)
    print("FAIL: " + str(msg))
    print("=" * 70)
    raise RuntimeError(str(msg))


def _mcp_query(sql):
    """Spusti SELECT proti DB_EC pres MCP. Vrati list[dict] rows nebo _fail."""
    try:
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    except Exception as e:
        _fail("import get_eurosoft_mcp_client selhal: " + repr(e))
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        _fail("MCP client je None (eurosoft_mcp_enabled=False / server down)")
    try:
        rj = mcp.call_tool_sync(
            "eurosoft_strategie_query_raw",
            {"sql": sql, "db_name": MSSQL_DB},
            conversation_id=None,
        )
        res = json.loads(rj) if isinstance(rj, str) else rj
    except Exception as e:
        _fail("MCP query_raw call failed: " + repr(e))
    if not isinstance(res, dict) or not res.get("ok"):
        err = res.get("error") if isinstance(res, dict) else res
        _fail("MCP query_raw vratil error: " + str(err))
    return res.get("rows") or []


def main():
    ctx_raw = os.environ.get("SANDBOX_CONTEXT", "{}")
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        _fail("SANDBOX_CONTEXT JSON parse selhal: " + repr(e))
    if not isinstance(ctx, dict):
        _fail("SANDBOX_CONTEXT neni dict: " + repr(ctx_raw))

    limit = ctx.get("limit")
    if limit in (None, "", 0, "0"):
        limit = None
    else:
        try:
            limit = int(limit)
        except Exception:
            _fail("limit neni cislo: " + repr(limit))

    dry_run = bool(ctx.get("dry_run"))
    skip_contacts = bool(ctx.get("skip_contacts"))
    batch = str(ctx.get("batch") or "dbec")

    db_url = os.environ.get("STRATEGIE_DATA_DB_URL", "")
    if not db_url:
        _fail("STRATEGIE_DATA_DB_URL neni v sandbox env (spusteno mimo trusted path?).")

    print(
        "HR migrace | limit={} dry_run={} skip_contacts={} batch={!r} tenant={}".format(
            limit, dry_run, skip_contacts, batch, TENANT_EUROSOFT
        )
    )

    # ── 1) zamestnanci (TabCisZam + _EXT) ──
    top = "TOP ({}) ".format(limit) if limit else ""
    emp_sql = (
        "SELECT " + top + EMP_COLS + " "
        "FROM dbo.TabCisZam z "
        "LEFT JOIN dbo.TabCisZam_EXT e ON e.ID = z.ID "
        "ORDER BY z.ID"
    )
    emp_rows = _mcp_query(emp_sql)
    print("DB_EC: nacteno {} zamestnancu".format(len(emp_rows)))
    if not emp_rows:
        _fail("0 zamestnancu z DB_EC (prazdna tabulka / spatny JOIN?)")
    emp_ids = [r.get("ID") for r in emp_rows if r.get("ID") is not None]

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT mod.hr_ingest_employees(%s::jsonb, %s, %s)",
            (json.dumps(emp_rows, ensure_ascii=False, default=str), TENANT_EUROSOFT, batch),
        )
        emp_res = cur.fetchone()[0]
        print("hr_ingest_employees -> {}".format(emp_res))

        # ── 2) kontakty (TabKontakty) — az po zamestnancich ──
        con_res = None
        if not skip_contacts:
            if limit and emp_ids:
                in_list = ",".join(str(int(i)) for i in emp_ids)
                con_where = "WHERE IDCisZam IN ({})".format(in_list)
            else:
                con_where = "WHERE IDCisZam IS NOT NULL"
            con_sql = (
                "SELECT ID, IDCisZam, Druh, Kam, Spojeni, Prednastaveno "
                "FROM dbo.TabKontakty " + con_where + " ORDER BY ID"
            )
            con_rows = _mcp_query(con_sql)
            print("DB_EC: nacteno {} kontaktu".format(len(con_rows)))
            cur.execute(
                "SELECT mod.hr_ingest_contacts(%s::jsonb, %s)",
                (json.dumps(con_rows, ensure_ascii=False, default=str), batch),
            )
            con_res = cur.fetchone()[0]
            print("hr_ingest_contacts -> {}".format(con_res))

        if dry_run:
            conn.rollback()
            print("DRY-RUN: rollback (nic nezapsano)")
        else:
            conn.commit()
            print("COMMIT: zapsano do mod.*")

        print()
        print("=" * 70)
        print("OK | employees={} contacts={} dry_run={}".format(emp_res, con_res, dry_run))
        print("=" * 70)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


main()
