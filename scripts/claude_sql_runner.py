r"""Claude SQL bridge — NB watcher / forwarder (Marti 1.6.2026).

Zrychleni spoluprace: Claude (Cowork) nema primy pristup k DB. Zapise SELECT
do souboru, tenhle watcher ho FORWARDNE na cloud APP endpoint /api/v1/erp/diag-sql,
ktery ho spusti pres EXISTUJICI STRATEGIE tooly (strategie_pg pro PG /
EUROSOFT MCP pro MSSQL) proti PRODUKCI a vrati vysledek. Watcher ho zapise zpet.

Proc forwarder: NB nedosahne na produkcni cloud SQL (interni VPN) — ale na
verejne HTTPS strategie-ai.com ano. SQL fakt bezi na cloud APP. Pouziva jen
stdlib (urllib) — zadny venv, zadne DB drivery, bezi i systemovym Pythonem.

KROK 1: read-only SELECT (PG + MSSQL). Cloud endpoint to vynuti (query_raw guard).
KROK 2 (pozdeji): write -> potvrzovaci popup v chatu/ERP.

Protokol (slozka scripts/claude_sql/, gitignored):
  CLAUDE_SQL.sql   - Claude zapise SELECT (cely soubor = jeden dotaz).
  CLAUDE_GO.txt    - trigger (Claude zapise JAKO POSLEDNI). Volitelne 1. radek:
                       db=pg (default) nebo db=mssql
  CLAUDE_OUT.txt   - watcher zapise vysledek (markdown tabulka + status).

Env (povinne):
  STRATEGIE_DEPLOY_TOKEN  - stejny token jako na cloud APP (auth diag-sql).
Env (volitelne):
  CLAUDE_SQL_CLOUD_URL    - default https://strategie-ai.com/api/v1/erp/diag-sql

NSSM install (NB) — diky urllib staci SYSTEMOVY python (ne venv):
  $nssm = "C:\Users\Martin\AppData\Local\Microsoft\WinGet\Links\nssm.exe"
  & $nssm install STRATEGIE-CLAUDE-SQL "python" "D:\Projekty\STRATEGIE\scripts\claude_sql_runner.py"
  & $nssm set STRATEGIE-CLAUDE-SQL AppDirectory D:\Projekty\STRATEGIE
  & $nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra "STRATEGIE_DEPLOY_TOKEN=<token>"
  & $nssm set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START
  & $nssm restart STRATEGIE-CLAUDE-SQL

Manual (debug):  python scripts/claude_sql_runner.py   (Ctrl+C konec)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
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
HTTP_TIMEOUT_SEC = 30
ROW_CAP = 500
CELL_MAX = 200
CLOUD_URL = os.environ.get(
    "CLAUDE_SQL_CLOUD_URL", "https://strategie-ai.com/api/v1/erp/diag-sql"
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


def _forward(sql: str, db: str) -> dict:
    """POST {sql, db} na cloud diag-sql endpoint. Returns parsed dict."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return {"ok": False, "error": "chybí env STRATEGIE_DEPLOY_TOKEN na NB"}
    payload = json.dumps({"sql": sql, "db": db}).encode("utf-8")
    rq = urllib.request.Request(
        CLOUD_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token},
    )
    try:
        with urllib.request.urlopen(rq, timeout=HTTP_TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code}: {body or e.reason}"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _md_table(columns: list, rows: list) -> str:
    def _cell(v) -> str:
        s = "" if v is None else str(v)
        s = s.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
        return s if len(s) <= CELL_MAX else s[:CELL_MAX] + "…"
    if not columns:
        return "(0 sloupců)"
    capped = rows[:ROW_CAP]
    head = "| " + " | ".join(str(c) for c in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body_lines = []
    for r in capped:
        if isinstance(r, dict):
            vals = [_cell(r.get(c)) for c in columns]
        else:
            vals = [_cell(v) for v in r]
        body_lines.append("| " + " | ".join(vals) + " |")
    body = "\n".join(body_lines)
    return head + "\n" + sep + ("\n" + body if body else "")


def _write_out(text_body: str) -> None:
    try:
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(text_body, encoding="utf-8")
    except OSError as exc:
        _log(f"write OUT failed: {exc}")


def _process() -> None:
    db = "pg"
    try:
        go_raw = GO_FILE.read_text(encoding="utf-8", errors="replace").strip().lower()
        import re
        m = re.search(r"db\s*=\s*(pg|mssql)", go_raw)
        if m:
            db = m.group(1)
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

    _log(f"forward {db}: {sql[:80]!r}")
    t0 = time.time()
    res = _forward(sql, db)
    el = int((time.time() - t0) * 1000)

    if not isinstance(res, dict) or not res.get("ok"):
        err = (res.get("error") if isinstance(res, dict) else str(res)) or "neznámá chyba"
        _write_out(
            f"# STATUS: CHYBA\n# {ts}\n# db={db} · {el} ms\n\n{err}\n\n"
            "```sql\n" + sql[:2000] + "\n```\n"
        )
        _log(f"ERROR ({db}): {str(err)[:160]}")
        _consume()
        return

    columns = res.get("columns")
    rows = res.get("rows") or []
    if not columns and rows and isinstance(rows[0], dict):
        columns = list(rows[0].keys())
    count = res.get("count")
    if count is None:
        count = len(rows)
    cap_note = f" (zobrazeno {ROW_CAP})" if count and count > ROW_CAP else ""
    md = _md_table(columns or [], rows)
    _write_out(
        f"# STATUS: OK · {count} řádků{cap_note} · {el} ms · db={db}\n# {ts}\n\n"
        + md + "\n"
    )
    _log(f"OK ({db}): {count} rows, {el} ms")
    _consume()


def _consume() -> None:
    try:
        if GO_FILE.exists():
            GO_FILE.unlink()
    except OSError as exc:
        _log(f"consume GO unlink failed: {exc}")


def main() -> None:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"STRATEGIE-CLAUDE-SQL forwarder started · dir={BRIDGE_DIR} · cloud={CLOUD_URL} · interval={SCAN_INTERVAL_SEC}s")
    if not os.environ.get("STRATEGIE_DEPLOY_TOKEN"):
        _log("WARNING: STRATEGIE_DEPLOY_TOKEN není nastaven — dotazy selžou na auth.")
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
        _log("STRATEGIE-CLAUDE-SQL forwarder stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
