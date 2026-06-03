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

Protokol SQL (slozka scripts/claude_sql/, gitignored):
  CLAUDE_SQL.sql   - Claude zapise SELECT (cely soubor = jeden dotaz).
  CLAUDE_GO.txt    - trigger (Claude zapise JAKO POSLEDNI). Volitelne 1. radek:
                       db=pg (default) nebo db=mssql
  CLAUDE_OUT.txt   - watcher zapise vysledek (markdown tabulka + status).

Protokol AUTO-DEPLOY (Marti 2.6.2026) — Claude nasadi bez rucniho git:
  CLAUDE_DEPLOY.txt     - 1. radek = commit message; dalsi radky = cesty souboru
                            ke `git add` (relativne k repo). Radek "ALL" = git add -A.
  CLAUDE_DEPLOY_GO.txt   - trigger (Claude zapise JAKO POSLEDNI).
  CLAUDE_DEPLOY_OUT.txt  - watcher zapise vysledek (git add/commit/push + cloud deploy).
  Tok: git add <soubory> -> commit -> push (PAT) -> POST cloud /deploy/now
       (git pull + restart API pres RESTART-WATCHER).

Env (povinne):
  STRATEGIE_DEPLOY_TOKEN  - stejny token jako na cloud APP (auth diag-sql + deploy).
Env (volitelne):
  STRATEGIE_GIT_PAT       - GitHub PAT (Contents: read/write) pro `git push` bez
                              credential manageru (funguje i pod LocalSystem). Bez
                              nej fallback na `git push origin main`.
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
import socket
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

# Auto-deploy (Marti 2.6.2026): Claude zapíše commit message + seznam souborů,
# watcher na NB udělá git add/commit/push + zavolá cloud /deploy/now.
DEPLOY_MSG_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY.txt"      # 1. řádek = commit msg; další řádky = cesty (nebo "ALL")
DEPLOY_GO_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY_GO.txt"    # trigger (zapsat JAKO POSLEDNÍ)
DEPLOY_OUT_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY_OUT.txt"  # watcher zapíše výsledek

SCAN_INTERVAL_SEC = 1.5
HTTP_TIMEOUT_SEC = 30
ROW_CAP = 500
CELL_MAX = 200
CLOUD_URL = os.environ.get(
    "CLAUDE_SQL_CLOUD_URL", "https://strategie-ai.com/api/v1/erp/diag-sql"
)
DEPLOY_URL = CLOUD_URL.replace("/diag-sql", "/deploy/now")

# Instance identita (Marti 2.6.2026) — dvě běžící instance Claude se nesmí poprat.
#   NB Marti = 23, NB Kristy = 24. Nastav v NSSM AppEnvironmentExtra:
#     nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra "...";"CLAUDE_INSTANCE_ID=23"
INSTANCE_ID = (os.environ.get("CLAUDE_INSTANCE_ID") or "?").strip()
_INSTANCE_NAMES = {"23": "Marti", "24": "Kristy"}
INSTANCE_NAME = (os.environ.get("CLAUDE_INSTANCE_NAME")
                 or _INSTANCE_NAMES.get(INSTANCE_ID, "?"))
INSTANCE_LABEL = f"Claude-{INSTANCE_ID} ({INSTANCE_NAME})"
try:
    HOSTNAME = socket.gethostname()
except Exception:
    HOSTNAME = "?"

# Presence heartbeat (Marti 3.6.2026): periodicky hlásí na cloud, ze instance
# zije — i v klidu (bez GO souboru). Cloud upsertne fw.claude_instance.
HEARTBEAT_INTERVAL_SEC = 30
HEARTBEAT_URL = CLOUD_URL.replace("/diag-sql", "/instance/heartbeat")


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
    payload = json.dumps({"sql": sql, "db": db, "instance_id": INSTANCE_ID,
                          "hostname": HOSTNAME}).encode("utf-8")
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


def _poll_write_status(request_id, max_wait_sec: int = 120) -> dict | None:
    """Krok 2: write čeká na schválení Marti. Polluje /diag-write/{id}/status
    dokud done/rejected/error nebo timeout. Returns final dict nebo None (timeout)."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    url = CLOUD_URL.replace("/diag-sql", f"/diag-write/{request_id}/status")
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        try:
            rq = urllib.request.Request(
                url, method="GET", headers={"X-Deploy-Token": token})
            with urllib.request.urlopen(rq, timeout=HTTP_TIMEOUT_SEC) as resp:
                j = json.loads(resp.read().decode("utf-8", errors="replace"))
            if j.get("status") in ("done", "rejected", "error"):
                return j
        except Exception:
            pass
        time.sleep(2.0)
    return None


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

    # Krok 2: write detekován na cloudu → pending → poll na schválení Marti
    if isinstance(res, dict) and res.get("pending") and res.get("request_id"):
        rid = res["request_id"]
        _log(f"WRITE pending #{rid} — čekám na schválení Marti…")
        _write_out(
            f"# STATUS: ČEKÁ NA SCHVÁLENÍ · request #{rid} · db={db}\n# {ts}\n\n"
            "Write detekován → Marti to schvaluje v banneru (chat/ERP). "
            "Polluju stav (max 120 s)…\n\n```sql\n" + sql[:2000] + "\n```\n"
        )
        final = _poll_write_status(rid)
        if final is None:
            _write_out(f"# STATUS: TIMEOUT · request #{rid} pořád pending po 120 s.\n# {ts}\n")
        elif final.get("status") == "done":
            _write_out(f"# STATUS: WRITE OK · {final.get('row_count')} řádků · request #{rid}\n"
                       f"# {ts}\n\n{final.get('result_text') or 'hotovo'}\n")
        elif final.get("status") == "rejected":
            _write_out(f"# STATUS: ODMÍTNUTO Marti · request #{rid}\n# {ts}\n")
        elif final.get("status") == "error":
            _write_out(f"# STATUS: WRITE CHYBA · request #{rid}\n# {ts}\n\n{final.get('error')}\n")
        else:
            _write_out(f"# STATUS: {final.get('status')} · request #{rid}\n# {ts}\n")
        _log(f"WRITE #{rid} resolved: {final.get('status') if final else 'timeout'}")
        _consume()
        return

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


# ── Auto-deploy (git add/commit/push na NB → cloud /deploy/now) ──────────
import subprocess


def _git_exe() -> str:
    """git v PATH, jinak běžné Windows cesty."""
    for cand in (
        "git",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ):
        try:
            subprocess.run([cand, "--version"], capture_output=True, timeout=10)
            return cand
        except Exception:
            continue
    return "git"


_GIT = None


def _run_git(args: list[str], timeout: int = 90) -> tuple[int, str]:
    """Spustí git v REPO_ROOT. Vrací (returncode, stdout+stderr)."""
    global _GIT
    if _GIT is None:
        _GIT = _git_exe()
    # Inline -c (žádný global config; služba běží pod LocalSystem bez git identity):
    #  • safe.directory → repo vlastní Marti, jinak "dubious ownership"
    #  • user.name/email → commit author (LocalSystem nemá ~/.gitconfig)
    #  • credential.helper= (prázdné) → vypne helpery (push jede přes PAT v URL)
    safe = [
        "-c", "safe.directory=*",
        "-c", f"safe.directory={REPO_ROOT.as_posix()}",
        "-c", f"user.name={INSTANCE_LABEL}",
        "-c", f"user.email=claude-{INSTANCE_ID}@strategie-ai.com",
        "-c", "credential.helper=",
    ]
    # GIT_TERMINAL_PROMPT=0 → špatné/chybějící creds selžou rychle, nezaseknou se
    # na interaktivním promptu (služba nemá konzoli → jinak hang do timeoutu).
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        p = subprocess.run(
            [_GIT] + safe + args, cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", env=env,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def _push_cmd() -> list[str]:
    """git push args. PAT z env → authed URL (bez závislosti na credential
    manageru, funguje i pod LocalSystem). Jinak fallback na origin."""
    pat = os.environ.get("STRATEGIE_GIT_PAT")
    if pat:
        rc, url = _run_git(["remote", "get-url", "origin"])
        url = url.strip()
        if rc == 0 and url.startswith("https://"):
            authed = url.replace("https://", f"https://{pat}@", 1)
            return ["push", authed, "HEAD:main"]
    return ["push", "origin", "main"]


def _authed_remote() -> str:
    """Authed URL pro fetch (PAT v URL → funguje na privátní repo pod
    LocalSystem) nebo 'origin' fallback."""
    pat = os.environ.get("STRATEGIE_GIT_PAT")
    rc, url = _run_git(["remote", "get-url", "origin"])
    url = url.strip()
    if pat and rc == 0 and url.startswith("https://"):
        return url.replace("https://", f"https://{pat}@", 1)
    return "origin"


def _sync_with_remote() -> tuple[str, str]:
    """Anti-přepis (Marti 2.6.2026): rebase lokálních commitů na aktuální
    origin/main PŘED push, aby si dvě instance Claude (23/24) nepřepsaly main.
    Returns ('ok'|'conflict'|'fail', detail). Při konfliktu rebase abortne."""
    remote = _authed_remote()
    rc_f, out_f = _run_git(["fetch", remote, "main"])
    if rc_f != 0:
        return "fail", "fetch: " + out_f
    rc_r, out_r = _run_git(["rebase", "FETCH_HEAD"])
    if rc_r != 0:
        _run_git(["rebase", "--abort"])
        return "conflict", "rebase: " + out_r
    return "ok", (out_r or "(rebase ok / už aktuální)")


def _cloud_deploy(description: str) -> dict:
    """POST cloud /deploy/now (git pull + restart API přes RESTART-WATCHER)."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    payload = json.dumps({"description": description, "instance_id": INSTANCE_ID,
                          "hostname": HOSTNAME}).encode("utf-8")
    rq = urllib.request.Request(
        DEPLOY_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token},
    )
    try:
        with urllib.request.urlopen(rq, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code}: {body or e.reason}"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _write_deploy_out(text_body: str) -> None:
    try:
        DEPLOY_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEPLOY_OUT_FILE.write_text(text_body, encoding="utf-8")
    except OSError as exc:
        _log(f"write DEPLOY_OUT failed: {exc}")


def _consume_deploy() -> None:
    try:
        if DEPLOY_GO_FILE.exists():
            DEPLOY_GO_FILE.unlink()
    except OSError as exc:
        _log(f"consume DEPLOY_GO unlink failed: {exc}")


def _process_deploy() -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    # 1) commit message + soubory ke stage
    msg = "Auto-deploy od Claude"
    file_specs: list[str] = []
    try:
        raw = DEPLOY_MSG_FILE.read_text(encoding="utf-8", errors="replace")
        lines = [ln.rstrip() for ln in raw.splitlines()]
        if lines and lines[0].strip():
            msg = lines[0].strip()
        file_specs = [ln.strip() for ln in lines[1:] if ln.strip()]
    except Exception:
        pass

    log_lines: list[str] = []

    def _step(label: str, rc: int, out: str) -> None:
        status = "OK" if rc == 0 else f"FAIL(rc={rc})"
        log_lines.append(f"## {label} — {status}\n{out or '(bez výstupu)'}")
        _log(f"DEPLOY {label}: {status} · {out[:120]!r}")

    _log(f"DEPLOY trigger · msg={msg!r} · files={file_specs or 'ALL'}")

    # 2) git add
    if not file_specs or file_specs == ["ALL"]:
        rc, out = _run_git(["add", "-A"])
        _step("git add -A", rc, out)
    else:
        rc, out = _run_git(["add", "--"] + file_specs)
        _step("git add " + " ".join(file_specs), rc, out)

    # 3) je co commitnout?
    rc_diff, _ = _run_git(["diff", "--cached", "--quiet"])
    committed_sha = None
    if rc_diff == 1:  # jsou staged změny
        rc, out = _run_git(["commit", "-m", msg])
        _step("git commit", rc, out)
        if rc == 0:
            rc2, sha = _run_git(["rev-parse", "--short", "HEAD"])
            committed_sha = sha.strip() if rc2 == 0 else None
    else:
        log_lines.append("## git commit — SKIP (nic ke commitnutí)")
        _log("DEPLOY commit: skip (clean index)")

    # 3.5) anti-přepis: srovnej se s origin/main (druhá instance mohla pushnout)
    sync_state, sync_out = _sync_with_remote()
    _pat0 = os.environ.get("STRATEGIE_GIT_PAT")
    if _pat0:
        sync_out = sync_out.replace(_pat0, "***")
    if sync_state == "conflict":
        _step("git rebase origin/main", 1, sync_out +
              "\n⚠ KONFLIKT — druhá instance Claude měnila stejné soubory. "
              "Deploy ZASTAVEN, push přeskočen. Sjednoť/přegeneruj změnu.")
        _write_deploy_out(
            f"# DEPLOY: KONFLIKT (rebase) · {INSTANCE_LABEL}\n# {ts}\n"
            f"# commit: {committed_sha or '(žádný nový)'} — NEPUSHNUTO\n\n"
            + "\n\n".join(log_lines) + "\n"
        )
        _consume_deploy()
        return
    _step("git rebase origin/main", 0 if sync_state == "ok" else 1, sync_out)

    # 4) git push (+ 1 retry po rebase, kdyby někdo pushnul mezitím)
    rc, out = _run_git(_push_cmd())
    if rc != 0 and any(k in out for k in
                       ("non-fast-forward", "rejected", "fetch first", "behind")):
        s2, _so2 = _sync_with_remote()
        if s2 == "ok":
            rc, out = _run_git(_push_cmd())
        else:
            out = out + f"\n(retry rebase: {s2} — push přeskočen)"
            rc = 1
    push_ok = rc == 0
    # ututlej PAT v logu
    safe = out
    pat = os.environ.get("STRATEGIE_GIT_PAT")
    if pat:
        safe = safe.replace(pat, "***")
    _step("git push", rc, safe)

    # 5) cloud deploy (pull + restart) — jen pokud push prošel
    cloud_summary = "(přeskočeno — push selhal)"
    if push_ok:
        cd = _cloud_deploy(f"Auto-deploy: {msg}")
        if cd.get("ok") or cd.get("status") == "deployed":
            cloud_summary = (
                f"OK — {cd.get('files_changed', '?')} souborů, "
                f"target {cd.get('target_sha', '?')}, API restart (~5 s)"
            )
        elif cd.get("reason") == "already_up_to_date":
            cloud_summary = "cloud už běží na nejnovější verzi"
        else:
            cloud_summary = f"NENASAZENO: reason={cd.get('reason')} error={cd.get('error')}"
        _log(f"DEPLOY cloud: {cloud_summary}")

    header = "OK" if push_ok else "CHYBA (push selhal)"
    _write_deploy_out(
        f"# DEPLOY: {header}\n# {ts}\n"
        f"# commit: {committed_sha or '(žádný nový)'} · cloud: {cloud_summary}\n\n"
        + "\n\n".join(log_lines) + "\n"
    )
    _consume_deploy()


def _send_heartbeat(action: str = "heartbeat") -> None:
    """Presence (Marti 3.6.2026): POST /instance/heartbeat — cloud upsertne
    fw.claude_instance. Best-effort, tichy fail. Bez instance_id (="?") skip."""
    if INSTANCE_ID == "?":
        return
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    payload = json.dumps({"instance_id": INSTANCE_ID, "hostname": HOSTNAME,
                          "action": action}).encode("utf-8")
    rq = urllib.request.Request(
        HEARTBEAT_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token},
    )
    try:
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        others = (j or {}).get("others") or []
        if others:
            who = ", ".join("Claude-%s (%s)" % (o.get("instance_id"), o.get("instance_name") or "?")
                            for o in others)
            _log(f"heartbeat OK · DALŠÍ AKTIVNÍ: {who}")
    except Exception:
        pass  # presence je nice-to-have, nikdy neblokuj watcher


def main() -> None:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"STRATEGIE-CLAUDE-SQL forwarder started · {INSTANCE_LABEL} · host={HOSTNAME} · dir={BRIDGE_DIR} · cloud={CLOUD_URL} · interval={SCAN_INTERVAL_SEC}s")
    if INSTANCE_ID == "?":
        _log("WARNING: CLAUDE_INSTANCE_ID není nastaven — atribuce commitů/deploye bude '?'. Nastav v NSSM (23=Marti, 24=Kristy).")
    if not os.environ.get("STRATEGIE_DEPLOY_TOKEN"):
        _log("WARNING: STRATEGIE_DEPLOY_TOKEN není nastaven — dotazy selžou na auth.")
    _send_heartbeat("startup")   # hned po startu hlas presence
    _last_hb = time.time()
    try:
        while True:
            try:
                if DEPLOY_GO_FILE.exists():
                    _process_deploy()
                if GO_FILE.exists():
                    _process()
                # Presence heartbeat každých ~30 s (i v klidu)
                if time.time() - _last_hb >= HEARTBEAT_INTERVAL_SEC:
                    _send_heartbeat()
                    _last_hb = time.time()
            except Exception as exc:
                _log(f"scan loop crash: {type(exc).__name__}: {exc}")
                try:
                    _write_out(f"# STATUS: WATCHER CRASH\n{type(exc).__name__}: {exc}\n")
                    _consume()
                    _write_deploy_out(f"# DEPLOY: WATCHER CRASH\n{type(exc).__name__}: {exc}\n")
                    _consume_deploy()
                except Exception:
                    pass
            time.sleep(SCAN_INTERVAL_SEC)
    except KeyboardInterrupt:
        _log("STRATEGIE-CLAUDE-SQL forwarder stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
