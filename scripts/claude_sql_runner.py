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
  MULTI-LANE (Marti 21.7.2026; lane 3 pridana 21.7. pro Kristy+Peta = 3 session):
  kdyz na jednom stroji bezi VIC Cowork session, kazda dalsi ma vlastni kanal,
  at se nepreskakuji. Lane 2 = CLAUDE2_*, Lane 3 = CLAUDE3_* (SQL.sql / GO.txt /
  OUT.txt / OUT_FULL.txt). DEFAULT = lanes 2 a 3. Dalsi pres env
  CLAUDE_EXTRA_LANES="2,3,4". Lane "" (bez indexu) je puvodni kanal beze zmeny.

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
# Mobilni APK publish z buildu (Marti 5.6.2026): watcher precte verzi z
# version.properties (gradle ji pri release buildu auto-zvysi predchozi+1)
# + APK z release/ a nahraje na server (zadny rucni vyber souboru v UI).
APP_MOBILE_DIR = REPO_ROOT / "APP" / "Mobile"
APP_VERSION_PROPS = APP_MOBILE_DIR / "version.properties"
# Sideload APK = flavor `internal` (SE SMS branou). Play AAB stavi build_aab.ps1
# z flavoru `play` (bez SMS). Flavor split Jirka 26.6.2026.
APP_APK = APP_MOBILE_DIR / "app" / "build" / "outputs" / "apk" / "internal" / "release" / "app-internal-release.apk"
SQL_FILE = BRIDGE_DIR / "CLAUDE_SQL.sql"
GO_FILE = BRIDGE_DIR / "CLAUDE_GO.txt"
OUT_FILE = BRIDGE_DIR / "CLAUDE_OUT.txt"
OUT_FULL_FILE = BRIDGE_DIR / "CLAUDE_OUT_FULL.txt"   # plný nezkrácený TSV (bez ořezu buněk/řádků)
LOG_FILE = BRIDGE_DIR / "watcher.log"
LOG_MAX_BYTES = 1_500_000                            # rotace watcher.log > ~1.5 MB (drž složku lehkou pro 9p mount)

# Nonce-pojmenovaný výstup (Marti 10.7.2026): Cowork device-bridge (9p mount) kešuje
# obsah PODLE CESTY → re-stage stejné CLAUDE_OUT.txt vrací starou (stale) verzi.
# Fix: když GO obsahuje `nonce=<token>`, watcher zapíše výstup NAVÍC do
# CLAUDE_OUT__<token>.txt / CLAUDE_OUT_FULL__<token>.txt. Cowork čte vždy poprvé
# viděnou cestu → nikdy stale. Dev session (Claude Code) čte přímo z FS = beze změny.
_current_nonce: str | None = None
NONCE_KEEP = 8                                        # kolik nonce kopií na base držet (úklid starších)

# ── Multi-lane vstup (Marti 21.7.2026) ────────────────────────────────────
# Víc Cowork session na JEDNOM stroji psalo do jednoho kanálu (CLAUDE_SQL.sql/
# CLAUDE_GO.txt) → přepisovaly si dotazy (kolize). Fix: každá další session má
# vlastní „lane" s indexem. Lane "" = default (CLAUDE_SQL/CLAUDE_GO/CLAUDE_OUT/
# CLAUDE_OUT_FULL — BEZE ZMĚNY, plná zpětná kompatibilita). Lane "2" = CLAUDE2_SQL.sql
# / CLAUDE2_GO.txt / CLAUDE2_OUT.txt / CLAUDE2_OUT_FULL.txt. Prefix CLAUDE<N>_ (NE __N)
# schválně — kdyby lane out byl CLAUDE_OUT__2.txt, sežral by ho nonce úklid lane1
# (glob CLAUDE_OUT__*.txt). CLAUDE2_* má jiný prefix → žádná kolize s nonce kopiemi.
# DEFAULT = lanes 2 a 3 (Marti 21.7.2026: Kristý+Peťa jedou 3 Cowork session naráz).
# Rozšíření na víc: env CLAUDE_EXTRA_LANES="2,3,4". Watcher obsluhuje lanes serializovaně
# (žádný file-clobber; souběžný BĚH dotazů se neřeší — write drží smyčku jako dnes).
_EXTRA_LANES = [s.strip() for s in os.environ.get("CLAUDE_EXTRA_LANES", "2,3").split(",") if s.strip()]
LANES = [""] + _EXTRA_LANES


def _laneset(prefix: str) -> dict:
    """Fileset pro danou lane. prefix '' = base (CLAUDE_*, shodné s SQL_FILE/GO_FILE/
    OUT_FILE/OUT_FULL_FILE), '2' = CLAUDE2_*. Používá se global-swap v _run_lane()."""
    p = f"CLAUDE{prefix}_"
    return {
        "sql":  BRIDGE_DIR / f"{p}SQL.sql",
        "go":   BRIDGE_DIR / f"{p}GO.txt",
        "out":  BRIDGE_DIR / f"{p}OUT.txt",
        "full": BRIDGE_DIR / f"{p}OUT_FULL.txt",
    }

# Auto-deploy (Marti 2.6.2026): Claude zapíše commit message + seznam souborů,
# watcher na NB udělá git add/commit/push + zavolá cloud /deploy/now.
DEPLOY_MSG_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY.txt"      # 1. řádek = commit msg; další řádky = cesty (nebo "ALL")
DEPLOY_GO_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY_GO.txt"    # trigger (zapsat JAKO POSLEDNÍ)
DEPLOY_OUT_FILE = BRIDGE_DIR / "CLAUDE_DEPLOY_OUT.txt"  # watcher zapíše výsledek

# Build mobilní appky (Marti 5.6.2026): Claude spustí gradlew přes bridge a vidí
# průběh (start → běží → OK/ERR). CLAUDE_BUILD.txt volby (volitelné): "noupload".
BUILD_MSG_FILE = BRIDGE_DIR / "CLAUDE_BUILD.txt"        # volby: "noupload" = jen postavit, nenahrávat
BUILD_GO_FILE = BRIDGE_DIR / "CLAUDE_BUILD_GO.txt"      # trigger (zapsat JAKO POSLEDNÍ)
BUILD_OUT_FILE = BRIDGE_DIR / "CLAUDE_BUILD_OUT.txt"    # watcher zapíše průběh + výsledek

# Notifikace na mobil (Marti 5.6.2026): Claude cinkne uzivateli "hotovo/výsledek".
# CLAUDE_NOTIFY.txt: 1. řádek = title, další řádky = zpráva; volitelně "user=<id>".
NOTIFY_MSG_FILE = BRIDGE_DIR / "CLAUDE_NOTIFY.txt"
NOTIFY_GO_FILE = BRIDGE_DIR / "CLAUDE_NOTIFY_GO.txt"    # trigger (zapsat JAKO POSLEDNÍ)
NOTIFY_OUT_FILE = BRIDGE_DIR / "CLAUDE_NOTIFY_OUT.txt"  # watcher zapíše výsledek

# Git pull (Marti 11.6.2026): Claude si srovná lokál na origin/main PŘED editem
# sdílených souborů (anti-stale, když druhá instance/Kristý pushla). Bez commitu.
PULL_GO_FILE = BRIDGE_DIR / "CLAUDE_PULL_GO.txt"        # trigger (zapsat JAKO POSLEDNÍ)
PULL_OUT_FILE = BRIDGE_DIR / "CLAUDE_PULL_OUT.txt"      # watcher zapíše výsledek

# Doc push (Marti 5.7.2026): watcher přečte lokální soubory dokumentů (zůstaly na
# tomto stroji z doby, kdy běžel jako produkce před migrací na cloud) a nahraje je
# na cloud přes /app/docs/push-blob (uloží na server + srovná storage_path + RO zrcadlo).
DOCPUSH_MSG_FILE = BRIDGE_DIR / "CLAUDE_DOCPUSH.txt"    # ř.1 = lokální složka; ř.2 (volit.) = ro_subdir
DOCPUSH_GO_FILE = BRIDGE_DIR / "CLAUDE_DOCPUSH_GO.txt"  # trigger (zapsat JAKO POSLEDNÍ)
DOCPUSH_OUT_FILE = BRIDGE_DIR / "CLAUDE_DOCPUSH_OUT.txt"

# Sync Claudů (Marti 3.6.2026): freshness + work-lock
WORK_LOCK_FILE = BRIDGE_DIR / "WORK_LOCK.txt"           # Claude píše: 1.ř popis, další ř soubory
OTHER_WORK_FILE = BRIDGE_DIR / "OTHER_CLAUDE_WORK.txt"  # watcher píše: co staví ostatní
LOCAL_STATUS_FILE = BRIDGE_DIR / "LOCAL_STATUS.txt"     # watcher píše: jsi N commitů pozadu
FRESHNESS_INTERVAL_SEC = 90                            # git fetch + behind check á 90s
_freshness = {"behind": 0, "head": None, "origin_sha": None,
              "origin_author": None, "origin_msg": None, "checked_at": None}

SCAN_INTERVAL_SEC = 1.5
# Adaptivní cadence (Marti 26.6.2026): když pracujeme, tikat svižně, ať se banner
# a výsledek objeví hned; když je delší dobu ticho, zpomalit (šetří NB i síť).
# „Aktivně" = od poslední akce (jakýkoli *_GO soubor) uplynulo < ACTIVE_WINDOW.
SCAN_ACTIVE_SEC = 0.6          # rychlé tikání během práce
SCAN_IDLE_SEC = 5.0           # klidové tikání, když se nic neděje
ACTIVE_WINDOW_SEC = 180.0     # jak dlouho po poslední akci zůstat ve „svižném" režimu
HTTP_TIMEOUT_SEC = 30
ROW_CAP = 500
CELL_MAX = 200
CLOUD_URL = os.environ.get(
    "CLAUDE_SQL_CLOUD_URL", "https://strategie-ai.com/api/v1/erp/diag-sql"
)
DEPLOY_URL = CLOUD_URL.replace("/diag-sql", "/deploy/now")
PUSH_URL = CLOUD_URL.replace("/diag-sql", "/app/docs/push-blob")

# Instance identita (Marti 2.6.2026) — dvě běžící instance Claude se nesmí poprat.
#   NB Marti = 23, NB Kristy = 24. Nastav v NSSM AppEnvironmentExtra:
#     nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra "...";"CLAUDE_INSTANCE_ID=23"
def _resolve_instance_id() -> str:
    """ID instance Claude (23 Marti / 24 Kristy). Priorita: env CLAUDE_INSTANCE_ID,
    pak soubor scripts/claude_sql/INSTANCE_ID.txt (gitignored, per-machine — bez
    žonglování s NSSM AppEnvironmentExtra, kde hrozí přepsání tokenu). Jinak '?'."""
    v = (os.environ.get("CLAUDE_INSTANCE_ID") or "").strip()
    if v:
        return v
    try:
        f = BRIDGE_DIR / "INSTANCE_ID.txt"
        if f.exists():
            first = f.read_text(encoding="utf-8").strip().split()
            if first:
                return first[0]
    except Exception:
        pass
    return "?"


INSTANCE_ID = _resolve_instance_id()
_INSTANCE_NAMES = {"23": "Marti", "24": "Kristy", "25": "Sarka"}
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

# Inbox otevřených úkolů (Marti 9.6.2026): při heartbeatu stáhni svoje otevřené
# úkoly (řešitel = tahle instance) a zapiš je do CLAUDE_TASKS.txt. Claude se na
# "go" kouká jen tam — žádné ruční SELECTy.
INBOX_URL = CLOUD_URL.replace("/diag-sql", "/claude-inbox")
TASKS_FILE = BRIDGE_DIR / "CLAUDE_TASKS.txt"

# Snimky obrazovky (Marti 11.6.2026): Marti v appce zmrazi obrazovku, nakresli
# a posle Claudovi. Cloud ji ulozi; watcher polluje a stahne k Claudovi do
# screenshots/latest.png (gitignored), aby si ji Claude precetl Read toolem.
SCREENSHOT_POLL_URL = CLOUD_URL.replace("/diag-sql", "/app/screenshot/poll")
SCREENSHOT_GET_URL = CLOUD_URL.replace("/diag-sql", "/app/screenshot/latest")
SCREENSHOTS_DIR = REPO_ROOT / "screenshots"
SCREENSHOT_POLL_INTERVAL_SEC = 5

# Marti-AI email + dialog most (Marti 24.6.2026): watcher pollne nové PŘÍCHOZÍ
# emaily Marti-AI a její ODPOVĚDI v konverzaci Claude<->Marti-AI → soubory, ať
# na ně Claude hned reaguje. Watermark soubory gitignored (per-machine).
MARTI_MAIL_URL = CLOUD_URL.replace("/diag-sql", "/claude-marti-mail")
MARTI_MAIL_FILE = BRIDGE_DIR / "INBOX_MARTI.txt"
MARTI_MAIL_LOG = BRIDGE_DIR / "INBOX_MARTI_LOG.txt"
MARTI_MAIL_WM = BRIDGE_DIR / ".marti_mail_seen"
MARTIAI_MSG_URL = CLOUD_URL.replace("/diag-sql", "/claude-martiai-msgs")
MARTIAI_MSG_FILE = BRIDGE_DIR / "MARTIAI_TO_CLAUDE.txt"
MARTIAI_MSG_LOG = BRIDGE_DIR / "MARTIAI_TO_CLAUDE_LOG.txt"
MARTIAI_MSG_WM = BRIDGE_DIR / ".martiai_msg_seen"
MAIL_POLL_INTERVAL_SEC = 20
# Ktery user posila k teto instanci (23=Marti uid 1, 24=Kristy uid 11).
SCREENSHOT_UID = os.environ.get("CLAUDE_SCREENSHOT_UID") or ("11" if INSTANCE_ID == "24" else "1")
_shot_last_epoch = 0


def _rotate_log() -> None:
    """Rotace watcher.log když překročí LOG_MAX_BYTES → watcher.log.1 (drž složku
    lehkou, jinak se 9p mount na 12MB logu dusí a čtení z Coworku je stale)."""
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > LOG_MAX_BYTES:
            bak = LOG_FILE.with_name("watcher.log.1")
            try:
                if bak.exists():
                    bak.unlink()
                LOG_FILE.rename(bak)          # tento proces mezi zápisy handle nedrží → rename projde
            except OSError:
                try:
                    LOG_FILE.write_text("", encoding="utf-8")   # fallback: truncate
                except OSError:
                    pass
    except OSError:
        pass


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _rotate_log()
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


def _also_nonce(base: Path, content: str) -> None:
    """Zapíše kopii výstupu do <stem>__<nonce><suffix> (poprvé viděná cesta pro
    Cowork = obchází 9p cache-by-path) + úklid starších nonce kopií daného base.
    No-op když GO nonce neobsahuje (dev session)."""
    n = _current_nonce
    if not n:
        return
    try:
        nf = base.with_name(f"{base.stem}__{n}{base.suffix}")
        nf.write_text(content, encoding="utf-8", errors="replace")
    except Exception as exc:
        _log(f"nonce write failed ({base.name}): {exc}")
    try:
        pat = f"{base.stem}__*{base.suffix}"
        olds = sorted(base.parent.glob(pat),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        for p in olds[NONCE_KEEP:]:
            try:
                p.unlink()
            except OSError:
                pass
    except Exception:
        pass


def _write_full(columns: list, rows: list) -> None:
    """Plný nezkrácený výstup do CLAUDE_OUT_FULL.txt (TSV) — bez ořezu buněk i
    řádků. Claude si ho přečte Read toolem, když náhled v OUT nestačí. Marti 3.7."""
    try:
        def _c(v):
            s = "" if v is None else str(v)
            return s.replace("\t", " ").replace("\r", " ").replace("\n", " ")
        lines = ["\t".join(str(c) for c in (columns or []))]
        for r in rows:
            if isinstance(r, dict):
                lines.append("\t".join(_c(r.get(c)) for c in (columns or [])))
            else:
                lines.append("\t".join(_c(v) for v in r))
        full = "\n".join(lines)
        OUT_FULL_FILE.write_text(full, encoding="utf-8", errors="replace")
        _also_nonce(OUT_FULL_FILE, full)
    except Exception as exc:
        _log(f"_write_full failed: {exc}")


def _freshness_banner() -> str:
    """Varování pro Clauda, když je lokál pozadu (předřadí se do OUT/DEPLOY_OUT).
    Prázdné, když je aktuální."""
    try:
        b = int(_freshness.get("behind") or 0)
    except Exception:
        b = 0
    if b <= 0:
        return ""
    osha = _freshness.get("origin_sha") or "?"
    oau = _freshness.get("origin_author") or "?"
    omsg = (_freshness.get("origin_msg") or "")[:60]
    return (f"# ⚠ TVUJ LOKAL JE POZADI o {b} commitu (posledni: {osha} {oau} '{omsg}').\n"
            f"# Nez budes editovat sdilene soubory, udelej: git pull origin main\n"
            f"# (jinak stavis na starem kodu).\n\n")


def _write_out(text_body: str) -> None:
    content = _freshness_banner() + text_body
    try:
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(content, encoding="utf-8")
    except OSError as exc:
        _log(f"write OUT failed: {exc}")
    _also_nonce(OUT_FILE, content)


def _read_work_lock() -> tuple:
    """WORK_LOCK.txt → (popis, soubory_str). 1. řádek = co stavím, další = soubory.
    Chybí/prázdné → (None, None)."""
    try:
        if not WORK_LOCK_FILE.exists():
            return (None, None)
        lines = [ln.strip() for ln in
                 WORK_LOCK_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
                 if ln.strip()]
        if not lines:
            return (None, None)
        work = lines[0]
        files = ", ".join(lines[1:]) if len(lines) > 1 else None
        return (work, files)
    except Exception:
        return (None, None)


def _check_freshness() -> None:
    """git fetch + spočítej behind (HEAD..origin/main) + poslední cizí commit.
    Uloží do _freshness + LOCAL_STATUS.txt. Best-effort — nikdy neshodí watcher."""
    global _freshness
    try:
        remote = _authed_remote()
        _run_git(["fetch", remote, "main"], timeout=30)
        rc_h, head = _run_git(["rev-parse", "--short", "HEAD"])
        rc_b, behind = _run_git(["rev-list", "--count", "HEAD..FETCH_HEAD"])
        rc_o, oinfo = _run_git(["log", "-1", "--format=%h|%an|%s", "FETCH_HEAD"])
        bn = int(behind.strip()) if rc_b == 0 and behind.strip().isdigit() else 0
        o_sha = o_au = o_msg = None
        if rc_o == 0 and "|" in oinfo:
            p = oinfo.strip().split("|", 2)
            o_sha = p[0] if len(p) > 0 else None
            o_au = p[1] if len(p) > 1 else None
            o_msg = p[2] if len(p) > 2 else None
        _freshness = {
            "behind": bn, "head": (head.strip() if rc_h == 0 else None),
            "origin_sha": o_sha, "origin_author": o_au, "origin_msg": o_msg,
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        if bn > 0:
            body = (f"# LOKAL POZADI o {bn} commitu\n"
                    f"# posledni origin: {o_sha} | {o_au} | {o_msg}\n"
                    f"# tvuj HEAD: {_freshness['head']} · {_freshness['checked_at']}\n"
                    f"# >>> git pull origin main  (nez budes editovat sdilene soubory)\n")
        else:
            body = (f"# LOKAL AKTUALNI (HEAD {_freshness['head']} == origin/main)\n"
                    f"# {_freshness['checked_at']}\n")
        try:
            LOCAL_STATUS_FILE.write_text(body, encoding="utf-8")
        except OSError:
            pass
    except Exception as exc:
        _log(f"freshness check failed: {type(exc).__name__}: {exc}")


def _write_other_work(others: list) -> None:
    """Zapiš OTHER_CLAUDE_WORK.txt — co staví ostatní instance (pro tohoto Clauda)."""
    try:
        lines = []
        for o in (others or []):
            iid = o.get("instance_id")
            nm = o.get("instance_name") or "?"
            cw = o.get("current_work")
            if cw:
                files = o.get("current_work_files")
                age = o.get("work_age_s")
                age_txt = (f" (pred {int(age)//60} min)"
                           if isinstance(age, (int, float)) else "")
                lines.append(f"Claude-{iid} ({nm}) STAVI: {cw}"
                             + (f" | soubory: {files}" if files else "") + age_txt)
            else:
                beh = o.get("local_behind")
                beh_txt = f" [lokal {beh} pozadu]" if beh else ""
                lines.append(f"Claude-{iid} ({nm}): nic nestavi (idle){beh_txt}")
        if not (others or []):
            lines.append("Zadna jina instance neni aktivni.")
        body = ("# Co staví ostatní instance Claude (heartbeat ~30s)\n"
                f"# {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                + "\n".join(lines) + "\n")
        OTHER_WORK_FILE.write_text(body, encoding="utf-8")
    except Exception:
        pass


def _ps_quote(s) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _local_alert(title: str, msg: str) -> None:
    """Lokální cinknutí přímo na NB (Marti 26.6.2026): jakmile zápis čeká na
    schválení, hned pípni + vyskoč Windows toast u Martiho — nezávisle na webu
    a mobilu (ty mají latenci: záložka na pozadí se uspí, push chodí později).
    Best-effort, nikdy neshodí watcher."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        winsound.Beep(880, 160)
        winsound.Beep(1175, 220)
    except Exception:
        pass
    try:
        import subprocess
        ps = (
            "$ErrorActionPreference='SilentlyContinue';"
            "Add-Type -AssemblyName System.Windows.Forms;"
            "Add-Type -AssemblyName System.Drawing;"
            "$n=New-Object System.Windows.Forms.NotifyIcon;"
            "$n.Icon=[System.Drawing.SystemIcons]::Information;"
            "$n.BalloonTipTitle=" + _ps_quote(title) + ";"
            "$n.BalloonTipText=" + _ps_quote(msg) + ";"
            "$n.Visible=$true;$n.ShowBalloonTip(8000);"
            "Start-Sleep -Milliseconds 9000;$n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=0x08000000)  # CREATE_NO_WINDOW
    except Exception:
        pass


def _process() -> None:
    global _current_nonce
    _current_nonce = None
    db = "pg"
    try:
        go_raw = GO_FILE.read_text(encoding="utf-8", errors="replace").strip().lower()
        import re
        m = re.search(r"db\s*=\s*([a-z0-9_]+)", go_raw)
        if m:
            db = m.group(1)
        mn = re.search(r"nonce\s*=\s*([a-z0-9_]+)", go_raw)
        if mn:
            _current_nonce = mn.group(1)
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
        _local_alert("Claude čeká na schválení",
                     f"Zápis #{rid} ({db}) čeká na potvrzení v banneru.")
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

    # Souborový most READ (Marti 20.6.2026): obsah souboru ulož lokálně, ať ho
    # Claude přečte Read toolem (obejde ořez buněk md tabulky na 200 znaků).
    if isinstance(res, dict) and res.get("file_read"):
        import os as _osfr
        fn = _osfr.path.basename((res.get("path") or "soubor").replace("\\", "/")) or "soubor"
        files_dir = BRIDGE_DIR / "files"
        try:
            files_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        content = res.get("content") or ""
        target = files_dir / fn
        try:
            target.write_text(content, encoding="utf-8", errors="replace")
        except Exception as _wexc:
            _log(f"file write failed: {_wexc}")
        _write_out(
            f"# STATUS: FILE OK · {res.get('length')} znaků → scripts/claude_sql/files/{fn}\n"
            f"# {ts}\n\nObsah souboru uložen lokálně. Claude si ho přečte Read toolem:\n"
            f"  scripts/claude_sql/files/{fn}\n"
        )
        _log(f"FILE READ ok: {fn} ({res.get('length')} znaků)")
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
    _write_full(columns or [], rows)
    # footer s odkazem na plný výstup, když se v náhledu něco ořízlo (buňka >CELL_MAX nebo řádky >ROW_CAP)
    _trunc = bool(count and count > ROW_CAP) or any(
        (len(str(v)) > CELL_MAX) for r in rows[:ROW_CAP]
        for v in (r.values() if isinstance(r, dict) else r))
    _foot = ("\n# ↳ plný výstup bez ořezu: scripts/claude_sql/CLAUDE_OUT_FULL.txt (Read tool)\n"
             if _trunc else "")
    _write_out(
        f"# STATUS: OK · {count} řádků{cap_note} · {el} ms · db={db}\n# {ts}\n\n"
        + md + "\n" + _foot
    )
    _log(f"OK ({db}): {count} rows, {el} ms")
    _consume()


def _consume() -> None:
    try:
        if GO_FILE.exists():
            GO_FILE.unlink()
    except OSError as exc:
        _log(f"consume GO unlink failed: {exc}")


def _run_lane(fs: dict) -> None:
    """Zpracuj jednu lane: dočasně přesměruj globály SQL/GO/OUT/OUT_FULL na její
    soubory, zavolej _process() (+ jeho _write_out/_write_full/_consume, které tyhle
    globály čtou), pak vrať zpět. Jednovláknová smyčka → žádná reentrance, bezpečné.
    Lane "" ukazuje na stejné base objekty → no-op swap (chování 1:1 jako dřív)."""
    global SQL_FILE, GO_FILE, OUT_FILE, OUT_FULL_FILE
    _save = (SQL_FILE, GO_FILE, OUT_FILE, OUT_FULL_FILE)
    SQL_FILE, GO_FILE, OUT_FILE, OUT_FULL_FILE = fs["sql"], fs["go"], fs["out"], fs["full"]
    try:
        _process()
    finally:
        SQL_FILE, GO_FILE, OUT_FILE, OUT_FULL_FILE = _save


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
    # --autostash (3.6.2026): rozdělané (unstaged) změny v worktree — typicky
    # scratch SQL/docs — si rebase sám odloží a zase vrátí. Bez toho rebase
    # padal na "cannot rebase: You have unstaged changes" a deploy se zasekl.
    rc_r, out_r = _run_git(["rebase", "--autostash", "FETCH_HEAD"])
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

    # Marti 3.6.2026: pojistka — neidentifikovana instance = deploy bez atribuce
    # (v gridu Claude aktivita se ukaze jako '?'). Hlasite varuj, at to nikdo
    # neprehledne. Deploy NEBLOKUJEME (emergency deploy musi projit), jen flag.
    if INSTANCE_ID == "?":
        _inst_warn = ("INSTANCE_ID neni nastaven ('?') — tento deploy NEBUDE "
                      "atribuovany. Oprava: zapis '24' (Kristy) nebo '23' (Marti) "
                      "do scripts\\claude_sql\\INSTANCE_ID.txt + "
                      "Restart-Service STRATEGIE-CLAUDE-SQL.")
        log_lines.append("## !!! INSTANCE NEIDENTIFIKOVANA\n" + _inst_warn)
        _log("DEPLOY WARN: " + _inst_warn)

    _log(f"DEPLOY trigger · msg={msg!r} · files={file_specs or 'ALL'}")

    # 2) git add
    if not file_specs or file_specs == ["ALL"]:
        rc, out = _run_git(["add", "-A"])
        _step("git add -A", rc, out)
    else:
        rc, out = _run_git(["add", "--"] + file_specs)
        _step("git add " + " ".join(file_specs), rc, out)

    # 2.5) PRE-DEPLOY SYNTAX CHECK (Claude 8.6.2026 — lekce z outage):
    # py_compile na všech staged .py souborech. Syntax chyba → deploy STOP,
    # nic se nepushne ani nenasadí, primary zůstane na funkční verzi.
    import sys as _sys
    if not file_specs or file_specs == ["ALL"]:
        _rcn, _names = _run_git(["diff", "--cached", "--name-only"])
        _pyfiles = [n.strip() for n in (_names.splitlines() if _rcn == 0 else [])
                    if n.strip().endswith(".py")]
    else:
        _pyfiles = [f for f in file_specs if f.endswith(".py")]
    # Claude-26 (Peťa) 21.7.2026: SMAZANÉ .py přeskoč — py_compile na neexistující
    # cestu spadne na FileNotFoundError a zastavil by deploy, takže odstranit .py
    # soubor přes most dosud vůbec nešlo (narazili jsme na to při úklidu
    # modules/erp/api/dochazka_zakazky.py). Kontrolujeme jen to, co na disku je.
    _pyfiles = [_p for _p in _pyfiles if (REPO_ROOT / _p).is_file()]
    _bad = []
    for _pf in _pyfiles:
        try:
            _r = subprocess.run([_sys.executable, "-m", "py_compile", str(REPO_ROOT / _pf)],
                                capture_output=True, text=True, timeout=60,
                                encoding="utf-8", errors="replace")
            if _r.returncode != 0:
                _bad.append(_pf + ":\n" + ((_r.stderr or _r.stdout or "")[:800]))
        except Exception as _exc:
            _bad.append(_pf + ": " + type(_exc).__name__ + ": " + str(_exc))
    if _bad:
        _step("py_compile syntax check", 1,
              "SYNTAX CHYBA — deploy ZASTAVEN (nic nepushnuto):\n" + "\n".join(_bad))
        # odstage změny, ať zůstane čistý index
        try:
            _run_git(["reset", "HEAD", "--"] + _pyfiles)
        except Exception:
            pass
        _write_deploy_out(
            f"# DEPLOY: ZASTAVEN (syntax check) · {INSTANCE_LABEL}\n# {ts}\n"
            f"# Syntax chyba ve staged .py — nic nepushnuto/nenasazeno. Oprav a deployni znovu.\n\n"
            + "\n\n".join(log_lines) + "\n"
        )
        _consume_deploy()
        return
    if _pyfiles:
        _step("py_compile syntax check", 0, f"OK — {len(_pyfiles)} .py souborů bez chyby")

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

    # Work-lock release (Marti 3.6.): po úspěšném pushi je práce odeslaná →
    # uvolni WORK_LOCK + jsme na špici (behind=0).
    if push_ok:
        try:
            if WORK_LOCK_FILE.exists():
                WORK_LOCK_FILE.unlink()
        except OSError:
            pass
        _freshness["behind"] = 0

    header = "OK" if push_ok else "CHYBA (push selhal)"
    _write_deploy_out(
        f"# DEPLOY: {header}\n# {ts}\n"
        f"# commit: {committed_sha or '(žádný nový)'} · cloud: {cloud_summary}\n\n"
        + "\n\n".join(log_lines) + "\n"
    )
    _consume_deploy()


def _ops_report(req_id, status: str, result: str) -> None:
    """Reportni vysledek ops akce zpet na cloud (audit). Best-effort."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    url = CLOUD_URL.replace("/diag-sql", f"/ops/{req_id}/result")
    payload = json.dumps({"status": status, "result": result}).encode("utf-8")
    rq = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token},
    )
    try:
        with urllib.request.urlopen(rq, timeout=10) as resp:
            resp.read()
    except Exception:
        pass


def _restart_self() -> None:
    """Restartuj vlastni NSSM sluzbu (STRATEGIE-CLAUDE-SQL). Spusti odpojeny
    PowerShell, ktery po 3 s sluzbu restartne (= zabije tento proces a spusti
    fresh s aktualnim kodem). LocalSystem ma na Restart-Service prava."""
    svc = os.environ.get("CLAUDE_WATCHER_SERVICE", "STRATEGIE-CLAUDE-SQL")
    cmd = ('powershell -NoProfile -ExecutionPolicy Bypass -Command '
           '"Start-Sleep -Seconds 3; Restart-Service -Name \'%s\' -Force"' % svc)
    flags = 0
    try:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    except Exception:
        flags = 0
    try:
        subprocess.Popen(cmd, shell=True, creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except Exception as exc:
        _log(f"restart_self spawn failed: {exc}")


def _read_app_version() -> tuple:
    """Precte (versionCode:int, versionName:str) z version.properties."""
    vc, vn = 0, ""
    try:
        for line in APP_VERSION_PROPS.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("versionCode"):
                vc = int(line.split("=", 1)[1].strip())
            elif line.startswith("versionName"):
                vn = line.split("=", 1)[1].strip()
    except Exception:
        pass
    return vc, vn


def _git_head_subject() -> str:
    """Posledni commit subject (pro poznamku k verzi, kdyz nedam vlastni)."""
    import subprocess
    try:
        p = subprocess.run(["git", "log", "-1", "--pretty=%s"],
                           cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=10)
        if p.returncode == 0:
            return (p.stdout or "").strip()[:300]
    except Exception:
        pass
    return ""


def _publish_app_mobile(notes: str = "") -> dict:
    """Precte APK z release/ + verzi z gradle a nahraje na server (multipart,
    X-Deploy-Token). notes = poznamka k verzi (kdyz prazdna → posledni commit)."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    if not token:
        return {"status": "error", "msg": "chybi STRATEGIE_DEPLOY_TOKEN na NB"}
    if not APP_APK.exists():
        return {"status": "error", "msg": "APK nenalezeno: nejdriv gradlew assembleInternalRelease"}
    vc, vn = _read_app_version()
    if vc <= 0:
        return {"status": "error", "msg": "neprecetl jsem versionCode z build.gradle.kts"}
    try:
        apk = APP_APK.read_bytes()
    except Exception as exc:
        return {"status": "error", "msg": f"cteni APK selhalo: {exc}"}
    notes = (notes or "").strip() or _git_head_subject()
    boundary = "----STRATEGIEpublish" + str(int(time.time()))

    def _part(nm: str, val: str) -> bytes:
        return (f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{nm}"\r\n\r\n{val}\r\n').encode("utf-8")

    body = _part("version_code", str(vc)) + _part("version_name", vn)
    if notes:
        body += _part("notes", notes)
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"app-release.apk\"\r\n"
             f"Content-Type: application/vnd.android.package-archive\r\n\r\n").encode("utf-8")
    body += apk + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")
    url = CLOUD_URL.replace("/diag-sql", "/app/mobile/upload")
    rq = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Deploy-Token": token,
    })
    try:
        with urllib.request.urlopen(rq, timeout=180) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if j.get("ok"):
            return {"status": "done",
                    "msg": f"nahrano v{vn} (code {vc}, {len(apk) // 1024} KB)"}
        return {"status": "error", "msg": f"upload: {j.get('error')}"}
    except urllib.error.HTTPError as e:
        return {"status": "error",
                "msg": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}
    except Exception as exc:
        return {"status": "error", "msg": str(exc)}


def _build_app_mobile() -> dict:
    """Spusti `gradlew.bat assembleInternalRelease` v APP/Mobile (sideload flavor SE
    SMS; release build auto-zvysi verzi predchozi+1 a vyrobi app-internal-release.apk).
    JAVA_HOME nastavi na Android Studio JBR, kdyz chybi. Vraci {status, msg}; pri
    chybe tail gradle vystupu."""
    import subprocess
    gradlew = APP_MOBILE_DIR / "gradlew.bat"
    if not gradlew.exists():
        return {"status": "error", "msg": "gradlew.bat nenalezen v APP/Mobile"}
    env = dict(os.environ)
    jh = env.get("JAVA_HOME")
    if not jh or not Path(jh).exists():
        for cand in (
            r"C:\Program Files\Android\Android Studio\jbr",
            r"C:\Program Files\Android\Android Studio1\jbr",
            r"C:\Program Files\Android\Android Studio Preview\jbr",
        ):
            if Path(cand).exists():
                env["JAVA_HOME"] = cand
                break
    try:
        p = subprocess.run(
            ["cmd", "/c", str(gradlew), "assembleInternalRelease"],
            cwd=str(APP_MOBILE_DIR), env=env,
            capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "msg": "build timeout (>15 min)"}
    except Exception as exc:
        return {"status": "error", "msg": "build spusteni selhalo: %s" % exc}
    if p.returncode != 0:
        tail = ((p.stdout or "") + (p.stderr or ""))[-400:]
        tail = tail.replace("\r", " ").replace("\n", " ")
        return {"status": "error", "msg": "build selhal (rc=%d): ...%s" % (p.returncode, tail)}
    return {"status": "done", "msg": "build OK"}


def _build_publish_app_mobile() -> dict:
    """Postavi APK (gradlew assembleInternalRelease) a hned ho nahraje na server."""
    b = _build_app_mobile()
    if b.get("status") != "done":
        return b
    return _publish_app_mobile()


def _write_build_out(text_body: str) -> None:
    try:
        BUILD_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        BUILD_OUT_FILE.write_text(text_body, encoding="utf-8")
    except Exception as exc:
        _log(f"write BUILD_OUT failed: {exc}")


def _process_build() -> None:
    """Bridge build: Claude zapíše CLAUDE_BUILD_GO.txt → spustíme gradlew
    assembleInternalRelease (sideload flavor SE SMS, verze +1) a STREAMUJEME průběh
    do CLAUDE_BUILD_OUT.txt (start → běží → OK/ERR). Po úspěchu APK nahrajeme
    (pokud není 'noupload')."""
    import subprocess
    do_upload = True
    notes = ""
    try:
        if BUILD_MSG_FILE.exists():
            raw = BUILD_MSG_FILE.read_text(encoding="utf-8", errors="replace")
            kept = []
            for ln in raw.splitlines():
                if ln.strip().lower() == "noupload":
                    do_upload = False
                    continue
                kept.append(ln)
            notes = "\n".join(kept).strip()[:300]
    except Exception:
        pass
    # GO zkonzumuj hned (idempotence — at to nebezi dvakrat)
    try:
        if BUILD_GO_FILE.exists():
            BUILD_GO_FILE.unlink()
    except Exception as exc:
        _log(f"consume BUILD_GO unlink failed: {exc}")

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    gradlew = APP_MOBILE_DIR / "gradlew.bat"
    if not gradlew.exists():
        _write_build_out(f"# BUILD: ERR\n# {ts}\ngradlew.bat nenalezen v APP/Mobile\n")
        return
    env = dict(os.environ)
    jh = env.get("JAVA_HOME")
    if not jh or not Path(jh).exists():
        for cand in (
            r"C:\Program Files\Android\Android Studio\jbr",
            r"C:\Program Files\Android\Android Studio1\jbr",
            r"C:\Program Files\Android\Android Studio Preview\jbr",
        ):
            if Path(cand).exists():
                env["JAVA_HOME"] = cand
                break
    jdk = env.get("JAVA_HOME", "(systemovy)")
    _log("BUILD: gradlew assembleInternalRelease …")
    vc0, vn0 = _read_app_version()
    head = "# BUILD: start\n# %s · JAVA_HOME=%s\n# verze pred: %s (code %s) → bude +1\n\n" % (
        ts, jdk, vn0, vc0)
    _write_build_out(head + "gradlew assembleInternalRelease se spousti…\n")

    tail = []
    rc = None
    try:
        p = subprocess.Popen(
            ["cmd", "/c", str(gradlew), "assembleInternalRelease", "--console=plain"],
            cwd=str(APP_MOBILE_DIR), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        last_flush = 0.0
        for line in p.stdout:
            line = line.rstrip()
            if not line:
                continue
            tail.append(line)
            if len(tail) > 80:
                tail = tail[-80:]
            now = time.time()
            if now - last_flush > 1.5:
                _write_build_out("# BUILD: bezi…\n# %s · JAVA_HOME=%s\n\n%s\n"
                                 % (ts, jdk, "\n".join(tail[-50:])))
                last_flush = now
        p.wait(timeout=60)
        rc = p.returncode
    except Exception as exc:
        _write_build_out("# BUILD: ERR\n# %s\nspusteni/cteni selhalo: %s\n\n%s\n"
                         % (ts, exc, "\n".join(tail[-40:])))
        _log(f"BUILD: ERR exception {exc}")
        return

    done_ts = time.strftime("%Y-%m-%d %H:%M:%S")
    if rc != 0:
        _write_build_out("# BUILD: ERR · rc=%d\n# %s\n\n%s\n"
                         % (rc, done_ts, "\n".join(tail[-50:])))
        _log(f"BUILD: ERR rc={rc}")
        return

    vc, vn = _read_app_version()
    if not do_upload:
        _write_build_out("# BUILD: OK (bez nahrani) · v%s code%s\n# %s\n\n%s\n"
                         % (vn, vc, done_ts, "\n".join(tail[-15:])))
        _log(f"BUILD: OK v{vn} code{vc} (bez nahrani)")
        return

    pub = _publish_app_mobile(notes)
    done_ts = time.strftime("%Y-%m-%d %H:%M:%S")
    if pub.get("status") == "done":
        _write_build_out("# BUILD: OK · %s\n# %s\n\n%s\n"
                         % (pub.get("msg", ""), done_ts, "\n".join(tail[-15:])))
        _log(f"BUILD: OK {pub.get('msg')}")
    else:
        _write_build_out("# BUILD: build OK, UPLOAD ERR · %s\n# %s\n\n%s\n"
                         % (pub.get("msg", ""), done_ts, "\n".join(tail[-15:])))
        _log(f"BUILD: upload ERR {pub.get('msg')}")


def _write_notify_out(text_body: str) -> None:
    try:
        NOTIFY_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        NOTIFY_OUT_FILE.write_text(text_body, encoding="utf-8")
    except Exception as exc:
        _log(f"write NOTIFY_OUT failed: {exc}")


def _process_notify() -> None:
    """Bridge: Claude zapíše CLAUDE_NOTIFY.txt (1. řádek title, další = zpráva;
    volitelně řádek 'user=<id>') → POST /app/notify (claude_msg cinkne na mobil)."""
    title = ""
    msg_lines = []
    uid = None
    try:
        raw = NOTIFY_MSG_FILE.read_text(encoding="utf-8", errors="replace") if NOTIFY_MSG_FILE.exists() else ""
    except Exception:
        raw = ""
    for ln in raw.splitlines():
        s = ln.strip()
        if uid is None and s.lower().startswith("user="):
            try:
                uid = int(s.split("=", 1)[1].strip())
            except Exception:
                uid = None
            continue
        if not title and s:
            title = s
            continue
        msg_lines.append(ln)
    message = "\n".join(msg_lines).strip()
    try:
        if NOTIFY_GO_FILE.exists():
            NOTIFY_GO_FILE.unlink()
    except Exception as exc:
        _log(f"consume NOTIFY_GO unlink failed: {exc}")

    if not title and not message:
        _write_notify_out("# NOTIFY: ERR\nprazdna zprava\n")
        return
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    if not token:
        _write_notify_out("# NOTIFY: ERR\nchybi STRATEGIE_DEPLOY_TOKEN na NB\n")
        return
    payload = {"title": title or "Zpráva od Claude", "message": message}
    if uid is not None:
        payload["user_id"] = uid
    url = CLOUD_URL.replace("/diag-sql", "/app/notify")
    rq = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token})
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with urllib.request.urlopen(rq, timeout=15) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if j.get("ok"):
            _write_notify_out("# NOTIFY: OK · id=%s\n# %s\n" % (j.get("id"), ts))
            _log(f"NOTIFY OK id={j.get('id')}")
        else:
            _write_notify_out("# NOTIFY: ERR\n# %s\n%s\n" % (ts, j.get("error")))
    except Exception as exc:
        _write_notify_out("# NOTIFY: ERR\n# %s\n%s\n" % (ts, exc))


def _handle_ops(ops: list) -> None:
    """Zpracuj pending ops z heartbeat odpovedi (whitelist akci z cloudu)."""
    for op in (ops or []):
        rid = op.get("id")
        kind = op.get("op")
        _log(f"OPS #{rid}: {op.get('action_key')} (op={kind})")
        if kind == "restart_self":
            _ops_report(rid, "done", f"restart watcheru {INSTANCE_LABEL} na {HOSTNAME} (za ~3 s)")
            _log(f"OPS #{rid}: restartuji vlastni sluzbu za 3 s…")
            _restart_self()
            time.sleep(1.0)
            sys.exit(0)   # restarter naběhne fresh proces
        elif kind == "publish_app_mobile":
            _log(f"OPS #{rid}: publikuji mobilni APK z buildu…")
            res = _publish_app_mobile()
            _ops_report(rid, res.get("status", "done"), res.get("msg", ""))
        elif kind == "build_publish_app_mobile":
            _log(f"OPS #{rid}: stavim APK (gradlew assembleInternalRelease) + nahravam…")
            res = _build_publish_app_mobile()
            _ops_report(rid, res.get("status", "done"), res.get("msg", ""))
        else:
            _ops_report(rid, "error", f"neznama op '{kind}' na watcheru")


def _send_heartbeat(action: str = "heartbeat") -> None:
    """Presence (Marti 3.6.2026): POST /instance/heartbeat — cloud upsertne
    fw.claude_instance. Best-effort, tichy fail. Bez instance_id (="?") skip.
    V odpovedi muze prijit 'ops' (pending akce pro tuhle instanci)."""
    if INSTANCE_ID == "?":
        return
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    # Work-lock + freshness (Marti 3.6.): co stavím (WORK_LOCK.txt) + stav lokálu.
    work, files = _read_work_lock()
    payload = json.dumps({
        "instance_id": INSTANCE_ID, "hostname": HOSTNAME, "action": action,
        "current_work": work, "current_work_files": files,
        "work_status": ("active" if work else "idle"),
        "local_head_sha": _freshness.get("head"),
        "local_behind": int(_freshness.get("behind") or 0),
    }).encode("utf-8")
    rq = urllib.request.Request(
        HEARTBEAT_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": token},
    )
    try:
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        others = (j or {}).get("others") or []
        _write_other_work(others)   # → OTHER_CLAUDE_WORK.txt (co staví druhý)
        if others:
            who = ", ".join("Claude-%s (%s)" % (o.get("instance_id"), o.get("instance_name") or "?")
                            for o in others)
            _log(f"heartbeat OK · DALŠÍ AKTIVNÍ: {who}")
        ops = (j or {}).get("ops") or []
        if ops:
            _handle_ops(ops)   # může proces ukončit (restart_self)
    except SystemExit:
        raise
    except Exception:
        pass  # presence je nice-to-have, nikdy neblokuj watcher


def _poll_claude_inbox() -> None:
    """Stáhni otevřené úkoly pro tuhle instanci (řešitel) a zapiš je do
    CLAUDE_TASKS.txt. Zapisuje jen při změně. Best-effort, NIKDY neblokuj
    watcher (vše v try/except). Marti 9.6.2026."""
    if INSTANCE_ID == "?":
        return
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    try:
        url = INBOX_URL + ("?uid=%s" % INSTANCE_ID)
        rq = urllib.request.Request(url, method="GET",
                                    headers={"X-Deploy-Token": token})
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if not (isinstance(j, dict) and j.get("ok") and isinstance(j.get("text"), str)):
            return
        new = j["text"]
        try:
            old = TASKS_FILE.read_text(encoding="utf-8") if TASKS_FILE.exists() else ""
        except Exception:
            old = ""
        if new != old:
            TASKS_FILE.write_text(new, encoding="utf-8")
            cnt = int(j.get("count") or 0)
            if cnt:
                _log(f"inbox: {cnt} otevřených úkolů → CLAUDE_TASKS.txt")
    except Exception:
        pass  # inbox je nice-to-have, nikdy neblokuj watcher


def _poll_screenshot() -> None:
    """Stáhni nový snímek obrazovky od usera (Marti zmrazil+nakreslil v appce)
    do screenshots/latest.png, aby si ho Claude přečetl Read toolem. Best-effort,
    NIKDY neblokuj watcher. Marti 11.6.2026."""
    global _shot_last_epoch
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    try:
        url = SCREENSHOT_POLL_URL + ("?uid=%s" % SCREENSHOT_UID)
        rq = urllib.request.Request(url, method="GET", headers={"X-Deploy-Token": token})
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if not (isinstance(j, dict) and j.get("ok") and j.get("has")):
            return
        epoch = int(j.get("epoch") or 0)
        if epoch and epoch <= _shot_last_epoch:
            return
        gurl = SCREENSHOT_GET_URL + ("?uid=%s" % SCREENSHOT_UID)
        rq2 = urllib.request.Request(gurl, method="GET", headers={"X-Deploy-Token": token})
        with urllib.request.urlopen(rq2, timeout=30) as resp2:
            data = resp2.read()
        if not data:
            return
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = j.get("ts") or time.strftime("%Y%m%d_%H%M%S")
        note = (j.get("note") or "").strip()
        (SCREENSHOTS_DIR / ("shot_%s.png" % ts)).write_bytes(data)
        (SCREENSHOTS_DIR / "latest.png").write_bytes(data)
        (SCREENSHOTS_DIR / "latest.txt").write_text(
            "ts=%s\nnote=%s\nfile=screenshots/shot_%s.png\n" % (ts, note, ts),
            encoding="utf-8")
        _shot_last_epoch = epoch
        try:
            (SCREENSHOTS_DIR / ".last_epoch").write_text(str(epoch), encoding="utf-8")
        except Exception:
            pass
        _log("screenshot: novy snimek ts=%s (%d B)%s -> screenshots/latest.png"
             % (ts, len(data), (" · " + note[:50]) if note else ""))
    except Exception:
        pass  # snimky jsou nice-to-have, nikdy neblokuj watcher


def _poll_marti_mail() -> None:
    """Stáhni nové PŘÍCHOZÍ emaily Marti-AI (persona 1) → INBOX_MARTI.txt (+log),
    ať na ně Claude hned reaguje. Watermark .marti_mail_seen (první běh = jen
    baseline, neflooduj starými). Best-effort, NIKDY neblokuj watcher. Marti 24.6."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    try:
        init = not MARTI_MAIL_WM.exists()
        since = -1
        if not init:
            try:
                since = int(MARTI_MAIL_WM.read_text(encoding="utf-8").strip() or "-1")
            except Exception:
                since, init = -1, True
        rq = urllib.request.Request(MARTI_MAIL_URL + ("?since=%d" % since),
                                    method="GET", headers={"X-Deploy-Token": token})
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if not (isinstance(j, dict) and j.get("ok")):
            return
        max_id = int(j.get("max_id") or 0)
        emails = j.get("emails") or []
        if init:
            MARTI_MAIL_WM.write_text(str(max_id), encoding="utf-8")
            return
        if emails:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            blocks = []
            for e in emails:
                blocks.append("id=%s | %s | %s\nOd: %s <%s>\nPredmet: %s\n--\n%s\n" % (
                    e.get("id"), e.get("received", ""),
                    ("NEPRECTENO" if e.get("unread") else "cteno"),
                    e.get("from_name", ""), e.get("from_email", ""),
                    e.get("subject", ""), (e.get("snippet", "") or "").strip()))
            txt = ("# NOVY EMAIL Marti-AI (%d) -- %s\n"
                   "# Cti cele: @@INBOX READ <id>  |  odpovez: @@EMAIL / @@MARTIAI\n\n%s"
                   % (len(emails), now, "\n========\n".join(blocks)))
            MARTI_MAIL_FILE.write_text(txt, encoding="utf-8")
            try:
                with open(MARTI_MAIL_LOG, "a", encoding="utf-8") as f:
                    f.write("\n\n# %s\n%s" % (now, txt))
            except Exception:
                pass
            _log("marti-mail: %d novych prichozich -> INBOX_MARTI.txt" % len(emails))
        if max_id > since:
            MARTI_MAIL_WM.write_text(str(max_id), encoding="utf-8")
    except Exception:
        pass  # nice-to-have, nikdy neblokuj watcher


def _poll_martiai_msgs() -> None:
    """Stáhni nové ODPOVĚDI Marti-AI v konverzaci Claude<->Marti-AI →
    MARTIAI_TO_CLAUDE.txt (+log). Watermark .martiai_msg_seen. Best-effort.
    Marti 24.6. ("ať ti Marti-AI přes most odpoví")."""
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN")
    if not token:
        return
    try:
        init = not MARTIAI_MSG_WM.exists()
        since = -1
        if not init:
            try:
                since = int(MARTIAI_MSG_WM.read_text(encoding="utf-8").strip() or "-1")
            except Exception:
                since, init = -1, True
        rq = urllib.request.Request(MARTIAI_MSG_URL + ("?since=%d" % since),
                                    method="GET", headers={"X-Deploy-Token": token})
        with urllib.request.urlopen(rq, timeout=10) as resp:
            j = json.loads(resp.read().decode("utf-8", errors="replace"))
        if not (isinstance(j, dict) and j.get("ok")):
            return
        max_id = int(j.get("max_id") or 0)
        msgs = j.get("msgs") or []
        if init:
            MARTIAI_MSG_WM.write_text(str(max_id), encoding="utf-8")
            return
        if msgs:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            blocks = []
            for mrow in msgs:
                blocks.append("# Marti-AI (%s, msg %s):\n%s" % (
                    mrow.get("when", ""), mrow.get("id"), (mrow.get("text", "") or "").strip()))
            txt = ("# ODPOVED Marti-AI (%d) -- %s\n# Reaguj: @@MARTIAI <text>\n\n%s"
                   % (len(msgs), now, "\n\n========\n".join(blocks)))
            MARTIAI_MSG_FILE.write_text(txt, encoding="utf-8")
            try:
                with open(MARTIAI_MSG_LOG, "a", encoding="utf-8") as f:
                    f.write("\n\n# %s\n%s" % (now, txt))
            except Exception:
                pass
            _log("martiai-msgs: %d novych odpovedi -> MARTIAI_TO_CLAUDE.txt" % len(msgs))
        if max_id > since:
            MARTIAI_MSG_WM.write_text(str(max_id), encoding="utf-8")
    except Exception:
        pass  # nice-to-have, nikdy neblokuj watcher


def _process_pull() -> None:
    """Git pull (fetch + rebase --autostash) lokálu na origin/main — bez commitu.
    Srovná working tree, aby Claude editoval aktuální soubory (anti-stale)."""
    try:
        _, head0 = _run_git(["rev-parse", "--short", "HEAD"])
        status, detail = _sync_with_remote()
        _, head1 = _run_git(["rev-parse", "--short", "HEAD"])
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        if status == "ok":
            body = "# PULL: OK\n# %s\n# HEAD %s -> %s\n\n%s\n" % (now, head0.strip(), head1.strip(), detail)
        else:
            body = "# PULL: %s\n# %s\n\n%s\n" % (status.upper(), now, detail)
        try:
            PULL_OUT_FILE.write_text(body, encoding="utf-8")
        except OSError as exc:
            _log(f"write PULL_OUT failed: {exc}")
        _log("pull: %s (HEAD %s -> %s)" % (status, head0.strip(), head1.strip()))
    finally:
        try:
            if PULL_GO_FILE.exists():
                PULL_GO_FILE.unlink()
        except OSError:
            pass


def _process_docpush() -> None:
    """Nahraje lokální soubory dokumentů na cloud (push-blob). CLAUDE_DOCPUSH.txt:
    ř.1 = lokální složka (např. D:\\Data\\STRATEGIE\\Dokumenty\\2), ř.2 volit. = ro_subdir (TISAX).
    Soubor musí být pojmenován <doc_id>.<ext>."""
    import base64 as _b64, json as _j
    token = os.environ.get("STRATEGIE_DEPLOY_TOKEN") or ""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        lines = DOCPUSH_MSG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        lines = []
    folder = (lines[0].strip() if lines else "")
    ro_subdir = (lines[1].strip() if len(lines) > 1 else "")
    if not folder or not os.path.isdir(folder):
        try:
            DOCPUSH_OUT_FILE.write_text(f"# DOCPUSH CHYBA\n# {ts}\nSlozka neexistuje: {folder!r}\n",
                                        encoding="utf-8")
        except Exception:
            pass
        try:
            DOCPUSH_GO_FILE.unlink()
        except Exception:
            pass
        return
    ok = err = 0
    rows = []
    for fn in sorted(os.listdir(folder)):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        stem = os.path.splitext(fn)[0]
        if not stem.isdigit():
            continue
        doc_id = int(stem)
        try:
            with open(fp, "rb") as fh:
                data = fh.read()
            if len(data) > 60 * 1024 * 1024:
                rows.append(f"{fn}: PRESKOCENO (>60 MB)"); err += 1; continue
            payload = _j.dumps({"doc_id": doc_id, "b64": _b64.b64encode(data).decode("ascii"),
                                "ro_subdir": ro_subdir}).encode("utf-8")
            rq = urllib.request.Request(PUSH_URL, data=payload, method="POST",
                headers={"Content-Type": "application/json", "X-Deploy-Token": token})
            with urllib.request.urlopen(rq, timeout=90) as resp:
                r = _j.loads(resp.read().decode("utf-8"))
            if isinstance(r, dict) and r.get("ok"):
                ok += 1
                rows.append(f"{fn}: OK {r.get('bytes')} B" + (" +RO" if r.get("ro_mirror") else ""))
            else:
                err += 1
                rows.append(f"{fn}: ERR {r.get('error') if isinstance(r, dict) else r}")
        except Exception as exc:
            err += 1
            rows.append(f"{fn}: EXC {type(exc).__name__}: {str(exc)[:80]}")
    body = "\n".join(rows[-500:])
    try:
        DOCPUSH_OUT_FILE.write_text(
            f"# DOCPUSH OK · nahrano {ok} · chyb {err} · slozka {folder}\n# {ts}\n\n{body}\n",
            encoding="utf-8")
    except Exception:
        pass
    _log(f"docpush: ok={ok} err={err} folder={folder}")
    try:
        DOCPUSH_GO_FILE.unlink()
    except Exception:
        pass


def main() -> None:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"STRATEGIE-CLAUDE-SQL forwarder started · {INSTANCE_LABEL} · host={HOSTNAME} · dir={BRIDGE_DIR} · cloud={CLOUD_URL} · interval={SCAN_INTERVAL_SEC}s")
    if INSTANCE_ID == "?":
        _log("WARNING: CLAUDE_INSTANCE_ID není nastaven — atribuce commitů/deploye bude '?'. Nastav v NSSM (23=Marti, 24=Kristy).")
    if not os.environ.get("STRATEGIE_DEPLOY_TOKEN"):
        _log("WARNING: STRATEGIE_DEPLOY_TOKEN není nastaven — dotazy selžou na auth.")
    _check_freshness()           # hned po startu zjisti, jestli jsme aktuální
    _send_heartbeat("startup")   # hned po startu hlas presence
    _last_hb = time.time()
    _last_fresh = time.time()
    _last_shot = 0.0             # snímky obrazovky — pollni hned po startu
    _last_mail = 0.0             # emaily + odpovědi Marti-AI — pollni hned po startu
    _last_activity = time.time() # poslední akce (GO soubor) — řídí adaptivní cadenci
    global _shot_last_epoch
    try:
        _shot_last_epoch = int((SCREENSHOTS_DIR / ".last_epoch").read_text(encoding="utf-8").strip())
    except Exception:
        _shot_last_epoch = 0
    try:
        while True:
            try:
                _did_work = False
                if PULL_GO_FILE.exists():
                    _process_pull(); _did_work = True
                if DEPLOY_GO_FILE.exists():
                    _process_deploy(); _did_work = True
                if BUILD_GO_FILE.exists():
                    _process_build(); _did_work = True
                if NOTIFY_GO_FILE.exists():
                    _process_notify(); _did_work = True
                if DOCPUSH_GO_FILE.exists():
                    _process_docpush(); _did_work = True
                for _pfx in LANES:
                    _fs = _laneset(_pfx)
                    if _fs["go"].exists():
                        _run_lane(_fs); _did_work = True
                if _did_work:
                    _last_activity = time.time()
                # Freshness (Marti 3.6.): git fetch + behind check á ~90 s →
                # LOCAL_STATUS.txt + banner v OUT (Claude na startu práce vidí,
                # jestli má pullnout).
                if time.time() - _last_fresh >= FRESHNESS_INTERVAL_SEC:
                    _check_freshness()
                    _last_fresh = time.time()
                # Presence heartbeat každých ~30 s (i v klidu) + inbox úkolů
                if time.time() - _last_hb >= HEARTBEAT_INTERVAL_SEC:
                    _send_heartbeat()
                    _poll_claude_inbox()
                    _last_hb = time.time()
                # Snímky obrazovky (Marti 11.6.): pollni á ~5 s a stáhni nový.
                if time.time() - _last_shot >= SCREENSHOT_POLL_INTERVAL_SEC:
                    _poll_screenshot()
                    _last_shot = time.time()
                # Emaily Marti-AI + její odpovědi (Marti 24.6.) á ~20 s
                if time.time() - _last_mail >= MAIL_POLL_INTERVAL_SEC:
                    _poll_marti_mail()
                    _poll_martiai_msgs()
                    _last_mail = time.time()
            except Exception as exc:
                _log(f"scan loop crash: {type(exc).__name__}: {exc}")
                try:
                    _write_out(f"# STATUS: WATCHER CRASH\n{type(exc).__name__}: {exc}\n")
                    _consume()
                    _write_deploy_out(f"# DEPLOY: WATCHER CRASH\n{type(exc).__name__}: {exc}\n")
                    _consume_deploy()
                except Exception:
                    pass
            # Adaptivní spánek: svižně během práce, klidně když je ticho (Marti 26.6.)
            _idle = (time.time() - _last_activity) >= ACTIVE_WINDOW_SEC
            time.sleep(SCAN_IDLE_SEC if _idle else SCAN_ACTIVE_SEC)
    except KeyboardInterrupt:
        _log("STRATEGIE-CLAUDE-SQL forwarder stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
