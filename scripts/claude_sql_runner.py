"""Claude SQL bridge — watcher (Marti 1.6.2026).

Zrychleni spoluprace: Claude (Cowork) nema primy pristup k DB. Misto rucniho
copy-paste vysledku Claude zapise SELECT do souboru a tenhle watcher ho spusti
a vrati vysledek do souboru.

KROK 1 (tento soubor): read-only SELECT auto (PG + MSSQL EUROSOFT) + audit.
KROK 2 (pozdeji): write (UPDATE/INSERT/DDL) -> popup v chatu/ERP, Marti potvrdi.

Protokol (slozka scripts/claude_sql/, gitignored):
  CLAUDE_SQL.sql   - Claude zapise SELECT (cely soubor = jeden dotaz).
  CLAUDE_GO.txt    - trigger (Claude zapise JAKO POSLEDNI). Volitelne 1. radek:
                       db=pg   (default) nebo db=mssql
  CLAUDE_OUT.txt   - watcher zapise vysledek (markdown tabulka + status).

Workflow watcheru:
  1. polluje CLAUDE_GO.txt kazde ~1.5 s
  2. precte CLAUDE_SQL.sql + db target z CLAUDE_GO.txt
  3. SELECT-only guard (WITH/SELECT/EXPLAIN). Write -> blok (Krok 2).
  4. spusti read-only proti DB (PG SQLAlchemy / MSSQL pyodbc)
  5. zapise markdown vysledek do CLAUDE_OUT.txt + audit do fw.claude_sql_log
  6. smaze CLAUDE_GO.txt (consumed)

NSSM install (jednorazove na NB, z repo rootu D:\Projekty\STRATEGIE):
  C:\Tools\nssm.exe install STRATEGIE-CLAUDE-SQL python ^
    "D:\Projekty\STRATEGIE\scripts\claude_sql_runner.py"
  C:\Tools\nssm.exe set STRATEGIE-CLAUDE-SQL AppDirectory D:\Projekty\STRATEGIE
  C:\Tools\nssm.exe set STRATEGIE-CLAUDE-SQL AppStdout D:\Projekty\STRATEGIE\scripts\claude_sql\watcher.log
  C:\Tools\nssm.exe set STRATEGIE-CLAUDE-SQL AppStderr D:\Projekty\STRATEGIE\scripts\claude_sql\watcher.log
  C:\Tools\nssm.exe set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START
  C:\Tools\nssm.exe start STRATEGIE-CLAUDE-SQL
  (pokud poetry venv: nastav Application na cestu k venv python.exe)

MSSQL (volitelne, pro db=mssql) - nastav env:
  CLAUDE_SQL_MSSQL_CONN = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.30.11;DATABASE=DB_EC;UID=Marti-AI;PWD=<heslo>;TrustServerCertificate=yes"

Manual (debug):  python scripts/claude_sql_runner.py   (Ctrl+C konec)
"""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = REPO_ROOT / "scripts" / "claude_sql"
SQL_FILE = BRIDGE_DIR / "CLAUDE_SQL.sql"
GO_FILE = BRIDGE_DIR / "CLAUDE_GO.txt"
OUT_FILE = BRIDGE_DIR / "CLAUDE_OUT.txt"
LOG_FILE = BRIDGE_DIR / "watcher.log"

SCAN_INTERVAL_SEC = 1.5
ROW_CAP = 500
STMT_TIMEOUT_MS = 15000   # 15 s
CELL_MAX = 200            # max delka bunky v markdown

# SELECT-only guard (Krok 1). Write detekce -> blok + hlaska na Krok 2.
_READ_PREFIX = re.compile(r"^\s*(WITH|SELECT|EXPLAIN)\b", re.IGNORECASE)
_WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|GRANT|"
    r"REVOKE|REPLACE|CALL|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


def _strip_comments(sql: str) -> str:
    s = re.sub(r"--[^\n]*", " ", sql)
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    return s.strip()


def _is_read_only(sql: str) -> bool:
    s = _strip_comments(sql)
    if not _READ_PREFIX.match(s):
        return False
    # WITH ... muze obsahovat data-modifying CTE (INSERT/UPDATE) -> blok pro jistotu
    return _WRITE_KEYWORDS.search(s) is None


def _pg_url() -> str | None:
    # env override -> jinak core.config settings
    env = os.environ.get("CLAUDE_SQL_PG_URL") or os.environ.get("STRATEGIE_DATA_DB_URL")
    if env:
        return env
    try:
        from core.config import settings
        return settings.database_data_url or settings.database_url or None
    except Exception as exc:
        _log(f"core.config import failed: {exc}")
        return None


def _md_table(columns: list[str], rows: list[tuple]) -> str:
    def _cell(v) -> str:
        s = "" if v is None else str(v)
        s = s.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
        return s if len(s) <= CELL_MAX else s[:CELL_MAX] + "…"
    if not columns:
        return "(0 sloupců)"
    head = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = "\n".join("| " + " | ".join(_cell(c) for c in r) + " |" for r in rows)
    return head + "\n" + sep + ("\n" + body if body else "")


def _audit(db_target: str, sql: str, status: str,
           row_count: int | None, elapsed_ms: int, error: str | None) -> None:
    url = _pg_url()
    if not url:
        return
    try:
        from sqlalchemy import create_engine, text
        eng = create_engine(url, pool_pre_ping=True)
        with eng.begin() as conn:
            conn.execute(text(
                "INSERT INTO fw.claude_sql_log "
                "(actor, db_target, sql_text, status, row_count, elapsed_ms, error) "
                "VALUES ('claude', :db, :sql, :st, :rc, :el, :err)"
            ), {"db": db_target, "sql": sql[:8000], "st": status,
                "rc": row_count, "el": elapsed_ms, "err": (error or None)})
        eng.dispose()
    except Exception as exc:
        _log(f"audit insert failed: {exc}")


def _run_pg(sql: str) -> tuple[str, int | None, int, str | None]:
    """Returns (markdown, row_count, elapsed_ms, error)."""
    url = _pg_url()
    if not url:
        return "", None, 0, "PG connection URL nenalezena (env / core.config)."
    from sqlalchemy import create_engine, text
    t0 = time.time()
    eng = create_engine(url, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            try:
                conn.execute(text("SET statement_timeout = :t"), {"t": STMT_TIMEOUT_MS})
                conn.execute(text("SET TRANSACTION READ ONLY"))
            except Exception:
                pass
            res = conn.execute(text(sql))
            cols = list(res.keys())
            rows = res.fetchmany(ROW_CAP)
        elapsed = int((time.time() - t0) * 1000)
        md = _md_table(cols, [tuple(r) for r in rows])
        return md, len(rows), elapsed, None
    except Exception as exc:
        elapsed = int((time.time() - t0) * 1000)
        return "", None, elapsed, f"{type(exc).__name__}: {exc}"
    finally:
        eng.dispose()


def _run_mssql(sql: str) -> tuple[str, int | None, int, str | None]:
    conn_str = os.environ.get("CLAUDE_SQL_MSSQL_CONN")
    if not conn_str:
        return "", None, 0, ("MSSQL není nakonfigurován (chybí env "
                             "CLAUDE_SQL_MSSQL_CONN). Viz docstring.")
    try:
        import pyodbc
    except ImportError:
        return "", None, 0, "pyodbc není nainstalován na NB (pip install pyodbc)."
    t0 = time.time()
    try:
        cn = pyodbc.connect(conn_str, timeout=10, readonly=True)
        try:
            cur = cn.cursor()
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(ROW_CAP) if cols else []
        finally:
            cn.close()
        elapsed = int((time.time() - t0) * 1000)
        md = _md_table(cols, [tuple(r) for r in rows])
        return md, len(rows), elapsed, None
    except Exception as exc:
        elapsed = int((time.time() - t0) * 1000)
        return "", None, elapsed, f"{type(exc).__name__}: {exc}"


def _write_out(text_body: str) -> None:
    try:
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(text_body, encoding="utf-8")
    except OSError as exc:
        _log(f"write OUT failed: {exc}")


def _process() -> None:
    # db target z GO souboru (1. radek "db=pg" / "db=mssql")
    db_target = "pg"
    try:
        go_raw = GO_FILE.read_text(encoding="utf-8", errors="replace").strip().lower()
        m = re.search(r"db\s*=\s*(pg|mssql)", go_raw)
        if m:
            db_target = m.group(1)
    except Exception:
        pass

    try:
        sql = SQL_FILE.read_text(encoding="utf-8", errors="replace").strip()
    except Exception as exc:
        sql = ""
        _log(f"read SQL failed: {exc}")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if not sql:
        _write_out(f"# STATUS: prázdný SQL\n# {ts}\n")
        _consume()
        return

    if not _is_read_only(sql):
        _write_out(
            f"# STATUS: BLOKOVÁNO (write detekován)\n# {ts}\n# db={db_target}\n\n"
            "Watcher v Kroku 1 pouští jen read-only SELECT/WITH/EXPLAIN.\n"
            "Write (INSERT/UPDATE/DELETE/DDL) bude přes potvrzovací popup v Kroku 2.\n\n"
            "```sql\n" + sql[:2000] + "\n```\n"
        )
        _audit(db_target, sql, "blocked", None, 0, "write blocked (krok 1)")
        _log(f"BLOCKED write ({db_target}): {sql[:80]!r}")
        _consume()
        return

    _log(f"run {db_target}: {sql[:80]!r}")
    if db_target == "mssql":
        md, rc, el, err = _run_mssql(sql)
    else:
        md, rc, el, err = _run_pg(sql)

    if err:
        _write_out(
            f"# STATUS: CHYBA\n# {ts}\n# db={db_target} · {el} ms\n\n{err}\n\n"
            "```sql\n" + sql[:2000] + "\n```\n"
        )
        _audit(db_target, sql, "error", None, el, err)
        _log(f"ERROR ({db_target}): {err[:160]}")
    else:
        cap_note = f" (capped {ROW_CAP})" if (rc is not None and rc >= ROW_CAP) else ""
        _write_out(
            f"# STATUS: OK · {rc} řádků{cap_note} · {el} ms · db={db_target}\n# {ts}\n\n"
            + md + "\n"
        )
        _audit(db_target, sql, "ok", rc, el, None)
        _log(f"OK ({db_target}): {rc} rows, {el} ms")

    _consume()


def _consume() -> None:
    try:
        if GO_FILE.exists():
            GO_FILE.unlink()
    except OSError as exc:
        _log(f"consume GO unlink failed: {exc}")


def main() -> None:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"STRATEGIE-CLAUDE-SQL watcher started · dir={BRIDGE_DIR} · interval={SCAN_INTERVAL_SEC}s")
    try:
        while True:
            try:
                if GO_FILE.exists():
                    _process()
            except Exception as exc:
                _log(f"scan loop crash: {type(exc).__name__}: {exc}")
                try:
                    _write_out(f"# STATUS: WATCHER CRASH\n{type(exc).__name__}: {exc}\n")
                    _consume()
                except Exception:
                    pass
            time.sleep(SCAN_INTERVAL_SEC)
    except KeyboardInterrupt:
        _log("STRATEGIE-CLAUDE-SQL watcher stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
