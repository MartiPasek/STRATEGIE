"""STRATEGIE-API-HEALTH-WATCHDOG — per-instance health watchdog (29.7.2026, C23).

DUVOD (incident 28.7.): primarni API (A, 8002) spadla a NIKDO se to nedozvedel.
Caddy failover to zamaskoval — verejny web zustal zeleny (chat jel pres B/D),
takze zadny check na verejny endpoint vypadek neodhalil. Rozbite bylo jen to,
co sekundary neumi (deploy token) -> hodiny honeni "proc nejde token".

RESENI: standalone NSSM sluzba na cloud APP, ktera kontroluje KAZDOU instanci
na JEJIM portu (localhost:8002/8003/...), ne pres Caddy. Pri vypadku:
  1. throttlovany auto-restart sluzby (proti crash-loopu),
  2. push alert vsem adminum (fw.mobile_command),
  3. re-alert kdyz zustava dole, + zprava o zotaveni.

Vzor: scripts/restart_watcher.py (stejne konvence — _log, NSSM, cloud C:\\Data).
NEBEZI v STRATEGIE-API procesu (aby ho neshodil sam se sebou).

--------------------------------------------------------------------------
NSSM install (jednorazove na cloud APP, PowerShell jako admin):
  New-Item -ItemType Directory -Path "C:\\Data\\STRATEGIE\\api_health" -Force

  $py = "C:\\Users\\Administrator\\AppData\\Local\\pypoetry\\Cache\\virtualenvs\\strategie-W5adySD1-py3.14\\Scripts\\python.exe"
  C:\\Tools\\nssm.exe install STRATEGIE-API-HEALTH-WATCHDOG $py "C:\\Projekty\\STRATEGIE\\scripts\\api_health_watchdog.py"
  C:\\Tools\\nssm.exe set STRATEGIE-API-HEALTH-WATCHDOG AppDirectory C:\\Projekty\\STRATEGIE
  C:\\Tools\\nssm.exe set STRATEGIE-API-HEALTH-WATCHDOG AppStdout C:\\Data\\STRATEGIE\\api_health\\watchdog.log
  C:\\Tools\\nssm.exe set STRATEGIE-API-HEALTH-WATCHDOG AppStderr C:\\Data\\STRATEGIE\\api_health\\watchdog.log
  C:\\Tools\\nssm.exe set STRATEGIE-API-HEALTH-WATCHDOG Start SERVICE_AUTO_START
  C:\\Tools\\nssm.exe start STRATEGIE-API-HEALTH-WATCHDOG

Pozn.: sluzba MUSI bezet pod uctem s pravy na Restart-Service (LocalSystem OK,
jako STRATEGIE-RESTART-WATCHER) a musi mit venv python (kvuli core.database_data).

Config pres env (nepovinne):
  STRATEGIE_HEALTH_INSTANCES = "STRATEGIE-API:8002,STRATEGIE-API-B:8003"
  STRATEGIE_HEALTH_ADMIN_IDS = "1,11,20"
  STRATEGIE_HEALTH_INTERVAL  = "120"        (sekundy mezi koly)
--------------------------------------------------------------------------
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Skript bezi z scripts/, takze sys.path[0] je scripts/, NE koren repa. Alert
# importuje core.* (fw.mobile_command) -> bez korene repa na ceste: "No module
# named 'core'". Doplnime koren repa (scripts/ = parents[1]).
_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Konzole pod NSSM jede v cp1250 -> print(" ") skoncil na
# UnicodeEncodeError('charmap' codec can't encode '✅') a ta vyjimka
# 29.7. shodila _handle_instance JESTE PRED resetem stavu -> hlidac hlasil
# zotaveni v kazdem kole (187 pushu adminum). Dolozeno primo z watchdog.log.
# Reseni je dvoji: (1) tady prepneme vystup na UTF-8 s nahradou neznamych znaku,
# aby log zustal citelny; (2) _log nize navic nikdy nevyhodi vyjimku (pojistka,
# kdyby reconfigure nebyl k dispozici).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---- Konfigurace (env-overridable) ------------------------------------
LOG_FILE = Path(os.environ.get("STRATEGIE_HEALTH_LOG")
                or r"C:\Data\STRATEGIE\api_health\watchdog.log")
NSSM_EXE = os.environ.get("STRATEGIE_NSSM_EXE") or r"C:\Tools\nssm.exe"
HEALTH_PATH = os.environ.get("STRATEGIE_HEALTH_PATH") or "/api/v1/health"
HEALTH_TIMEOUT_S = float(os.environ.get("STRATEGIE_HEALTH_TIMEOUT") or "6")
CHECK_INTERVAL_S = float(os.environ.get("STRATEGIE_HEALTH_INTERVAL") or "120")
RESTART_TIMEOUT_S = 90

# Produkcni instance A + B (D=8004 je test/data_db_test -> vynechano, zadny noise).
# Format env: "svc:port,svc:port".
_DEFAULT_INSTANCES = "STRATEGIE-API:8002,STRATEGIE-API-B:8003"
# Kolik po sobe jdoucich neuspechu = "dole" (proti jednorazovemu blipu behem restartu).
FAILS_TO_DOWN = int(os.environ.get("STRATEGIE_HEALTH_FAILS") or "2")
# Auto-restart throttle: max N restartu v okne (proti crash-loopu).
MAX_RESTARTS = int(os.environ.get("STRATEGIE_HEALTH_MAX_RESTARTS") or "3")
THROTTLE_WINDOW_S = float(os.environ.get("STRATEGIE_HEALTH_THROTTLE_WIN") or str(30 * 60))
# Re-alert kdyz zustava dole (aby to nezapadlo, ale nespamovalo).
REALERT_EVERY_S = float(os.environ.get("STRATEGIE_HEALTH_REALERT") or str(60 * 60))
# Tvrda pojistka proti spamu (C28 29.7., schvalila Marti-AI): stejny TITULEK alertu
# neodejde casteji nez jednou za tento interval, at se ve stavovem automatu stane
# cokoli. Cil dle Jirky: jedna zprava kdyz spadne, jedna kdyz nabehne, nic mezi tim.
ALERT_MIN_GAP_S = float(os.environ.get("STRATEGIE_HEALTH_ALERT_GAP") or str(30 * 60))
# ...ale u PADU kratsi (C28 29.7., schvalila Marti-AI msg 11777). Zjisteno z ostrych
# dat: 29.7. byly dva skutecne vypadky 26 min po sobe a ten druhy jednotna 30min
# pojistka spolkla. Dva pady za pul hodiny jsou pattern, ne sum - to clovek videt musi.
# Spam nehrozi: stavovy automat po oprave pusti alert jen pri skutecne zmene stavu.
ALERT_DOWN_GAP_S = float(os.environ.get("STRATEGIE_HEALTH_ALERT_GAP_DOWN") or str(10 * 60))
# Liveness heartbeat do logu (aby bylo videt, ze watchdog sam zije a hlida).
HEARTBEAT_EVERY_S = float(os.environ.get("STRATEGIE_HEALTH_HEARTBEAT") or str(30 * 60))

_ADMIN_IDS = [int(x) for x in (os.environ.get("STRATEGIE_HEALTH_ADMIN_IDS")
                               or "1,11,20").split(",") if x.strip().isdigit()]

# Tichy signal zivota (C28 29.7., navrh schvalila Marti-AI msg 11765): sluzby na
# pozadi umiraji potichu - mlci stejne, kdyz jedou, i kdyz stoji. Kazde kolo si
# sem hlidac zapise last_seen a uloha `watchdog_alive_check` hlida zastarani.
SERVICE_NAME = os.environ.get("STRATEGIE_HEALTH_SERVICE_NAME") or "STRATEGIE-API-HEALTH-WATCHDOG"
_HOST = socket.gethostname()
_STARTED_AT = datetime.now(timezone.utc)
_LAST_BEAT_ERR_LOG = 0.0   # throttle logu, aby vypadek DB nezaplavil watchdog.log


def _parse_instances() -> list[dict]:
    raw = os.environ.get("STRATEGIE_HEALTH_INSTANCES") or _DEFAULT_INSTANCES
    out = []
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        svc, port = part.rsplit(":", 1)
        try:
            out.append({"svc": svc.strip(), "port": int(port.strip())})
        except ValueError:
            continue
    return out


def _log(msg: str) -> None:
    # C28 29.7.: _log NESMI nikdy vyhodit vyjimku. Kdyz vyletela (rozbity stdout
    # NSSM logu), shodila _handle_instance JESTE PRED resetem stavu -> priznak
    # "je dole" zustal viset a watchdog hlasil zotaveni v KAZDEM kole
    # (137 pushu adminum 29.7. za 4,5 h). Log je diagnostika, ne kriticka cesta.
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def _now() -> float:
    return time.time()


# ---- Health check -----------------------------------------------------
def _check_health(port: int) -> tuple[bool, str]:
    url = f"http://127.0.0.1:{port}{HEALTH_PATH}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=HEALTH_TIMEOUT_S) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                return True, f"HTTP {code}"
            return False, f"HTTP {code}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:120]}"


# ---- Auto-restart (throttlovany) --------------------------------------
def _restart(service: str) -> tuple[bool, str]:
    cmd = [NSSM_EXE, "restart", service]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=RESTART_TIMEOUT_S, encoding="utf-8", errors="replace")
        return r.returncode == 0, ((r.stdout or "") + (r.stderr or "")).strip()[:300]
    except subprocess.TimeoutExpired:
        return False, f"nssm restart timeout {RESTART_TIMEOUT_S}s"
    except FileNotFoundError:
        return False, f"NSSM nenalezen: {NSSM_EXE}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


# ---- Alert (push adminum pres fw.mobile_command) ----------------------
_LAST_ALERT: dict[str, float] = {}   # titulek -> cas posledniho odeslani


def _alert(title: str, message: str, min_gap: float | None = None) -> None:
    """Vlozi push notifikaci pro kazdeho admina. Vzor = disk monitor (_DISK_MON).
    Pojistka: stejny titulek nejdriv za min_gap (vychozi ALERT_MIN_GAP_S = zotaveni
    30 min; u padu se predava ALERT_DOWN_GAP_S = 10 min)."""
    gap = ALERT_MIN_GAP_S if min_gap is None else min_gap
    _prev = _LAST_ALERT.get(title)
    if _prev is not None and (_now() - _prev) < gap:
        _log("ALERT potlacen (stejny titulek pred %ds, limit %ds): %s"
             % (int(_now() - _prev), int(gap), title))
        return
    _LAST_ALERT[title] = _now()
    if not _ADMIN_IDS:
        _log("ALERT (bez prijemcu): %s | %s" % (title, message))
        return
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        s = _gds()
        try:
            for uid in _ADMIN_IDS:
                s.execute(_t(
                    "INSERT INTO fw.mobile_command "
                    "(app_key, target_user_id, command_type, title, message, created_by) "
                    "VALUES ('mobile', :uid, 'claude_msg', :ti, :m, 1)"),
                    {"uid": uid, "ti": title[:120], "m": message[:2000]})
            s.commit()
        finally:
            s.close()
        _log("ALERT sent -> admins %s: %s" % (_ADMIN_IDS, title))
    except Exception as exc:
        # Alert je smysl watchdogu — kdyz selze, logni HLASITE (uvidime v logu).
        _log("!!! ALERT DELIVERY FAILED (%s): %s | %s" % (exc, title, message))


# ---- Stav per instance ------------------------------------------------
def _fresh_state() -> dict:
    return {
        "down": False,          # potvrzeny vypadek (>= FAILS_TO_DOWN)
        "fails": 0,             # po sobe jdouci neuspechy
        "down_since": 0.0,
        "restart_times": [],    # timestampy auto-restartu (throttle okno)
        "last_alert": 0.0,      # posledni alert (re-alert throttle)
        "gave_up": False,       # throttle vycerpan -> uz nerestartujeme, jen alertujeme
    }


def _prune_restarts(state: dict) -> None:
    cutoff = _now() - THROTTLE_WINDOW_S
    state["restart_times"] = [t for t in state["restart_times"] if t >= cutoff]


def _handle_instance(inst: dict, state: dict) -> None:
    svc, port = inst["svc"], inst["port"]
    ok, detail = _check_health(port)

    if ok:
        was_down = bool(state["down"])
        downtime = int(_now() - state["down_since"]) if state["down_since"] else 0
        # POZOR na poradi (C28 29.7.): stav se resetuje JAKO PRVNI, jeste pred
        # logem a alertem. Kdyz predtim cokoli mezi alertem a resetem vyletelo,
        # priznak "je dole" zustal viset a zotaveni se hlasilo v kazdem kole.
        state.update({"down": False, "fails": 0, "down_since": 0.0, "gave_up": False,
                      "last_alert": 0.0})
        if was_down:
            _log(f"RECOVERED {svc}:{port} ({detail}) po {downtime}s")
            _alert(f"✅ {svc} zase běží",
                   f"Instance {svc} (port {port}) je zpět nahoře po ~{downtime}s dole. Zotaveno.")
        return

    # --- neuspech ---
    state["fails"] += 1
    if state["fails"] < FAILS_TO_DOWN:
        _log(f"WARN {svc}:{port} health fail {state['fails']}/{FAILS_TO_DOWN} ({detail})")
        return

    first_down = not state["down"]
    if first_down:
        state["down"] = True
        state["down_since"] = _now()
        _log(f"DOWN {svc}:{port} potvrzeno ({detail})")

    # Auto-restart (throttlovany)
    _prune_restarts(state)
    if not state["gave_up"] and len(state["restart_times"]) < MAX_RESTARTS:
        state["restart_times"].append(_now())
        n = len(state["restart_times"])
        _log(f"AUTO-RESTART {svc} (pokus {n}/{MAX_RESTARTS} v okne)...")
        r_ok, r_out = _restart(svc)
        _log(("restart OK: " if r_ok else "restart FAIL: ") + (r_out or ""))
        # Alert na prvni pad hned (i kdyz restartujeme — admin ma vedet)
        if first_down:
            _alert(f"🔴 {svc} spadla — zkouším restart",
                   f"Instance {svc} (port {port}) neodpovídá na health ({detail}). "
                   f"Auto-restart {n}/{MAX_RESTARTS} spuštěn. Pokud nenaběhne, ozvu se znovu.",
                   ALERT_DOWN_GAP_S)
            state["last_alert"] = _now()
    else:
        # Throttle vycerpan -> vzdat auto-restart, eskalovat
        if not state["gave_up"]:
            state["gave_up"] = True
            _log(f"GAVE UP {svc}: {MAX_RESTARTS} restartu v okne nepomohlo — jen alertuji")
            _alert(f"🔴🔴 {svc} DOLE — auto-restart vzdal",
                   f"Instance {svc} (port {port}) je opakovaně dole a {MAX_RESTARTS} "
                   f"auto-restartů v okně nepomohlo ({detail}). POTŘEBA RUČNÍ ZÁSAH na Praze.",
                   ALERT_DOWN_GAP_S)
            state["last_alert"] = _now()

    # Re-alert kdyz zustava dole dlouho
    if state["down"] and (_now() - state["last_alert"]) >= REALERT_EVERY_S:
        downtime = int(_now() - state["down_since"]) if state["down_since"] else 0
        _alert(f"🔴 {svc} stále dole ({downtime // 60} min)",
               f"Instance {svc} (port {port}) je pořád dole ({detail}). Downtime ~{downtime // 60} min.",
               ALERT_DOWN_GAP_S)
        state["last_alert"] = _now()


def _beat(note: str = "") -> None:
    """Zapise tichy signal zivota do fw.service_heartbeat. Best-effort: kdyz DB
    nejede, jen si to poznamenam do logu (throttlovane) a jedu dal - hlidac nesmi
    umrit na tom, ze si nemohl zapsat, ze zije."""
    global _LAST_BEAT_ERR_LOG
    try:
        from core.database_data import get_data_session as _gds_b
        from sqlalchemy import text as _t_b
        s = _gds_b()
        try:
            s.execute(_t_b(
                "INSERT INTO fw.service_heartbeat "
                "(service_name, host, pid, started_at, last_seen, note) "
                "VALUES (:n, :h, :p, :st, now(), :note) "
                "ON CONFLICT (service_name) DO UPDATE SET last_seen = now(), "
                "host = EXCLUDED.host, pid = EXCLUDED.pid, "
                "started_at = EXCLUDED.started_at, note = EXCLUDED.note, updated_at = now()"),
                {"n": SERVICE_NAME, "h": _HOST, "p": os.getpid(),
                 "st": _STARTED_AT, "note": (note or "")[:500]})
            s.commit()
        finally:
            s.close()
    except Exception as exc:
        if _now() - _LAST_BEAT_ERR_LOG >= 1800:
            _LAST_BEAT_ERR_LOG = _now()
            _log("signal zivota se nezapsal (jedu dal): %s: %s"
                 % (type(exc).__name__, str(exc)[:200]))


def _selftest_alert_path() -> None:
    """Na startu overi, ze DB (alert cesta) je dosazitelna z kontextu sluzby —
    at to nezjistime az pri ostrem vypadku. Nemeni nic, jen SELECT 1 + log."""
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        s = _gds()
        try:
            s.execute(_t("SELECT 1"))
        finally:
            s.close()
        _log("ALERT PATH OK — DB dosazitelna, fw.mobile_command pripraveno (alerty dorazi).")
    except Exception as exc:
        _log("!!! ALERT PATH BROKEN — DB nedosazitelna z kontextu sluzby: %s" % exc)
        _log("!!! Health-check + auto-restart POJEDOU, ale ALERTY NEDORAZI. "
             "Oprav venv python / .env u sluzby STRATEGIE-API-HEALTH-WATCHDOG.")


def main() -> None:
    instances = _parse_instances()
    _log("STRATEGIE-API-HEALTH-WATCHDOG start · instance=%s · admini=%s · interval=%ss · health=%s"
         % ([f"{i['svc']}:{i['port']}" for i in instances], _ADMIN_IDS, CHECK_INTERVAL_S, HEALTH_PATH))
    _selftest_alert_path()
    if not instances:
        _log("CHYBA: zadne instance ke sledovani (STRATEGIE_HEALTH_INSTANCES). Koncim.")
        return
    states = {i["svc"]: _fresh_state() for i in instances}
    last_heartbeat = _now()
    try:
        while True:
            for inst in instances:
                try:
                    _handle_instance(inst, states[inst["svc"]])
                except Exception as exc:
                    _log(f"handle {inst.get('svc')} crash: {type(exc).__name__}: {exc}")
            # Tichy signal zivota do DB (kazde kolo) — odtud pozna uloha
            # watchdog_alive_check, ze watchdog jeste zije.
            _beat(" ".join("%s:%s" % (i["svc"], "DOLE" if states[i["svc"]]["down"] else "up")
                           for i in instances))
            # Liveness heartbeat — potvrzeni, ze watchdog sam bezi a hlida.
            if _now() - last_heartbeat >= HEARTBEAT_EVERY_S:
                summary = " ".join(
                    "%s:%s" % (i["svc"], "DOLE" if states[i["svc"]]["down"] else "up")
                    for i in instances)
                _log("HEARTBEAT alive · %s" % summary)
                last_heartbeat = _now()
            time.sleep(CHECK_INTERVAL_S)
    except KeyboardInterrupt:
        _log("STRATEGIE-API-HEALTH-WATCHDOG stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
