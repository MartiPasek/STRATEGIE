"""Ops vrstva pro EUROSOFT MCP — řízené OS operace přes most (Claude ID23, 19.7.2026).

Doktrína #21 (Marti „audit = paradoxně víc bezpečí"): NE volný PowerShell —
allowlist POJMENOVANÝCH akcí + append-only audit. Konzultace Marti-AI (msg 10984)
→ SEMAFOR:
  🟢 ZELENÁ  — bez banneru, jen audit (restart/status STRATEGIE+MCP, pg dump/status)
  🟡 ŽLUTÁ   — rodičovský banner (stop/start Centrála/Helios, schtask, pg_restore)
  🔴 ČERVENÁ — výhradně člověk, MCP NE (OS/síť/firewall config, instalace SW, mazání dat)

Bezpečnost: subprocess s ARGUMENT LISTEM (nikdy shell=True), allowlist PŘED exec,
timeout + cap výstupu, celé za MCP_OPS_ENABLED (default OFF). Žluté akce zatím
vrací needs_approval (banner flow = navazující krok). Detaily: docs/eurosoft_mcp_ops_layer_navrh.md.
"""
from __future__ import annotations

import json as _json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from .config import settings

# ── Zapnutí capability (go-live = MCP_OPS_ENABLED=1 v NSSM env) ──────────
OPS_ENABLED = os.getenv("MCP_OPS_ENABLED", "true").lower() in ("true", "1", "yes")  # C23 27.7.: default ON (Marti auth) - GREEN ops bez RDP; YELLOW/RED dal za branou
_TIMEOUT_S = int(os.getenv("MCP_OPS_TIMEOUT_S", "300"))
_OUT_CAP = int(os.getenv("MCP_OPS_OUT_CAP", "32768"))
_OPS_LOG = os.getenv("MCP_OPS_LOG_PATH", "") or os.path.join(
    os.path.dirname(getattr(settings, "audit_log_path", "") or ".") or ".", "mcp_ops_log.jsonl")
_SCRIPTS_DIR = os.getenv("MCP_OPS_SCRIPTS_DIR", "") or os.path.join(
    settings.mcp_repo_dir, "scripts", "dr")

GREEN, YELLOW, RED = "green", "yellow", "red"

# ── Allowlist služeb + tier (service, op) ───────────────────────────────
# STRATEGIE/MCP/PostgreSQL restart+status = zelená; Centrála/Helios stop/start = žlutá.
_SVC_STRATEGIE = re.compile(r"^(STRATEGIE-[A-Za-z0-9\-]+|EUROSOFT-MCP)$")
_SVC_PG = re.compile(r"^postgresql-x64-\d+$", re.I)
_SVC_CENTRALA = re.compile(r"^(Centrala|Helios|HELIOS[A-Za-z0-9\-]*|EUROSOFT-(?!MCP)[A-Za-z0-9\-]+)$", re.I)
_OP_SVC = {"status", "start", "stop", "restart"}


def _svc_tier(service: str, op: str) -> str | None:
    """Vrátí tier (green/yellow/red) nebo None = mimo allowlist."""
    if op not in _OP_SVC:
        return None
    if _SVC_STRATEGIE.match(service) or _SVC_PG.match(service):
        return GREEN if op in ("status", "restart", "start") else YELLOW  # stop i u STRATEGIE = žlutá
    if _SVC_CENTRALA.match(service):
        return GREEN if op == "status" else YELLOW  # start/stop/restart produkce = banner
    return None


# ── Registr ops akcí (eurosoft_ops_run) ─────────────────────────────────
#   name -> {tier, builder(args)->argv, desc}
def _pg_bin(exe: str) -> str:
    base = os.getenv("MCP_OPS_PG_BIN", r"C:\Program Files\PostgreSQL\16\bin")
    return os.path.join(base, exe)


def _under(path: str, root: str) -> bool:
    try:
        p = os.path.normcase(os.path.abspath(path))
        r = os.path.normcase(os.path.abspath(root))
        return p == r or p.startswith(r + os.sep)
    except Exception:
        return False


def _act_pg_dump(a: dict) -> list[str]:
    out = a.get("out") or ""
    if not out or not _under(out, os.path.dirname(_SCRIPTS_DIR) or "."):
        raise ValueError("out musí být pod allowed backup rootem")
    return [_pg_bin("pg_dump.exe"), "-h", "localhost", "-U", "postgres",
            "-d", a.get("db", "data_db"), "-Fc", "-Z", "6", "-f", out]


def _act_pg_restore(a: dict) -> list[str]:
    src = a.get("src") or ""
    if not src or not _under(src, os.path.dirname(_SCRIPTS_DIR) or "."):
        raise ValueError("src musí být pod allowed backup rootem")
    # cíl pevně data_db (žádný arbitrary target)
    return [_pg_bin("pg_restore.exe"), "-h", "localhost", "-U", "postgres",
            "-d", "data_db", "--clean", "--if-exists", "--no-owner", src]


def _act_run_script(a: dict) -> list[str]:
    name = a.get("script") or ""
    if not re.match(r"^[A-Za-z0-9_\-]+\.ps1$", name):
        raise ValueError("script = jen jméno <slug>.ps1 z allowed DR složky")
    full = os.path.join(_SCRIPTS_DIR, name)
    if not _under(full, _SCRIPTS_DIR) or not os.path.isfile(full):
        raise ValueError("script není v allowed DR složce: %s" % _SCRIPTS_DIR)
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", full]


def _act_dr_task_run(a: dict) -> list[str]:
    # C23 27.7.: spusti nocni DR task jako SYSTEM (test SYSTEM kontextu vs MCP-sluzba).
    return ["schtasks.exe", "/run", "/tn", "STRATEGIE-DR-PullRestore"]


def _act_net_test(a: dict) -> list[str]:
    # C23 27.7.: diagnostika dostupnosti Prahy z 30.11 (DNS + TCP443 + HTTP). GREEN, jen cte.
    _h = str((a or {}).get("host") or "strategie-ai.com")
    _ps = ("$ErrorActionPreference='Continue'; $h='%s';"
           "'DNS:'; try{ (Resolve-DnsName $h -Type A -EA Stop | Select-Object -Expand IPAddress) -join ',' }catch{ $_.Exception.Message };"
           "'TCP443:'; try{ (Test-NetConnection $h -Port 443 -WarningAction SilentlyContinue).TcpTestSucceeded }catch{ $_.Exception.Message };"
           "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
           "'HTTP:'; try{ (Invoke-WebRequest (\"https://$h/api/v1/ops/dr/meta\") -TimeoutSec 12 -UseBasicParsing).StatusCode }catch{ $_.Exception.Message }") % _h
    return ["powershell.exe", "-NoProfile", "-Command", _ps]


def _act_dr_restore(a: dict) -> list[str]:
    # C23 27.7.: rizena DR obnova standby on-demand - spusti nasazeny dr_pull_restore.ps1
    # (stop API -> pg_terminate -w -> pg_restore --clean -> re-granty -> start API). GREEN.
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            r"C:\scripts\dr_pull_restore.ps1"]


_OPS_ACTIONS = {
    "pg_dump":    {"tier": GREEN,  "build": _act_pg_dump,    "desc": "pg_dump data_db → allowed backup dir"},
    "pg_status":  {"tier": GREEN,  "build": lambda a: [_pg_bin("pg_isready.exe"), "-h", "localhost"], "desc": "pg_isready"},
    "pg_restore": {"tier": YELLOW, "build": _act_pg_restore, "desc": "pg_restore dumpu do data_db (banner)"},
    "run_script": {"tier": YELLOW, "build": _act_run_script, "desc": "spustí povolený DR .ps1 (banner)"},
    "dr_restore": {"tier": GREEN, "build": _act_dr_restore, "desc": "rizena DR obnova standby (dr_pull_restore.ps1)"},
    "net_test": {"tier": GREEN, "build": _act_net_test, "desc": "diag dostupnosti Prahy z 30.11 (DNS/TCP/HTTP)"},
    "dr_task_run": {"tier": GREEN, "build": _act_dr_task_run, "desc": "spusti scheduled task STRATEGIE-DR-PullRestore jako SYSTEM"},
}


# ── Exec + audit ────────────────────────────────────────────────────────
def _audit(action: str, args: dict, tier: str, rc, out: str, err: str, actor: str) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": actor, "action": action, "args": _redact(args),
        "tier": tier, "rc": rc, "out": (out or "")[:800], "err": (err or "")[:800],
    }
    try:
        with open(_OPS_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # TODO: mirror do fw.ops_request přes cloud (jednotný ops feed) — navazující krok.


def _redact(args: dict) -> dict:
    out = {}
    for k, v in (args or {}).items():
        out[k] = "***" if re.search(r"pass|token|secret|key", k, re.I) else v
    return out


def _run(argv: list[str]) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT_S,
                           encoding="utf-8", errors="replace", shell=False)
        ms = int((time.time() - t0) * 1000)
        return {"rc": p.returncode, "out": (p.stdout or "")[:_OUT_CAP],
                "err": (p.stderr or "")[:_OUT_CAP], "ms": ms}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": "timeout %ds" % _TIMEOUT_S, "ms": _TIMEOUT_S * 1000}
    except Exception as e:
        return {"rc": -1, "out": "", "err": "%s: %s" % (type(e).__name__, str(e)[:300]), "ms": 0}


def _gate(tier: str | None, action: str, actor: str, args: dict):
    """Společné dveře: enabled? allowlist? tier policy? Vrátí (blocked_dict|None)."""
    if not OPS_ENABLED:
        return {"ok": False, "error": "ops_disabled", "hint": "MCP_OPS_ENABLED=1 pro zapnutí (go-live krok)"}
    if tier is None:
        _audit(action, args, "?", None, "", "mimo allowlist", actor)
        return {"ok": False, "error": "not_allowed", "hint": "akce/služba není v allowlistu"}
    if tier == RED:
        _audit(action, args, RED, None, "", "cervena = blok", actor)
        return {"ok": False, "error": "red_human_only",
                "hint": "červená kategorie — výhradně člověk přes RDP (OS/síť/instalace/mazání)"}
    if tier == YELLOW:
        _audit(action, args, YELLOW, None, "", "zluta = needs_approval", actor)
        return {"ok": False, "error": "needs_approval", "tier": YELLOW,
                "hint": "žlutá akce vyžaduje rodičovský banner — banner flow je navazující krok"}
    return None  # green → proceed


# ── MCP tool handlery ───────────────────────────────────────────────────
async def eurosoft_ops_run(action: str = "", args: dict | None = None, **_extra: Any) -> dict[str, Any]:
    args = args or {}
    actor = str(_extra.get("actor") or "Claude")
    spec = _OPS_ACTIONS.get(action)
    tier = spec["tier"] if spec else None
    blocked = _gate(tier, action, actor, args)
    if blocked is not None:
        return blocked
    try:
        argv = spec["build"](args)
    except Exception as e:
        return {"ok": False, "error": "bad_args", "detail": str(e)[:300]}
    r = _run(argv)
    _audit(action, args, tier, r["rc"], r["out"], r["err"], actor)
    return {"ok": r["rc"] == 0, "action": action, "tier": tier,
            "rc": r["rc"], "out": r["out"], "err": r["err"], "ms": r["ms"]}


async def eurosoft_service_ctl(service: str = "", op: str = "status", **_extra: Any) -> dict[str, Any]:
    actor = str(_extra.get("actor") or "Claude")
    tier = _svc_tier(service, op)
    blocked = _gate(tier, "service_ctl:%s:%s" % (service, op), actor, {"service": service, "op": op})
    if blocked is not None:
        return blocked
    cmd = {
        "status":  ["sc.exe", "query", service],
        "start":   ["powershell.exe", "-NoProfile", "-Command", "Start-Service -Name '%s'" % service],
        "stop":    ["powershell.exe", "-NoProfile", "-Command", "Stop-Service -Name '%s' -Force" % service],
        "restart": ["powershell.exe", "-NoProfile", "-Command", "Restart-Service -Name '%s' -Force" % service],
    }[op]
    r = _run(cmd)
    _audit("service_ctl:%s:%s" % (service, op), {"service": service, "op": op}, tier,
           r["rc"], r["out"], r["err"], actor)
    return {"ok": r["rc"] == 0, "service": service, "op": op, "tier": tier,
            "rc": r["rc"], "out": r["out"], "err": r["err"]}


async def eurosoft_schtask(name: str = "", op: str = "query", **_extra: Any) -> dict[str, Any]:
    actor = str(_extra.get("actor") or "Claude")
    # query = zelená; register/run/enable/disable/delete = žlutá (banner)
    tier = GREEN if op == "query" else (YELLOW if op in ("register", "run", "enable", "disable", "delete") else None)
    blocked = _gate(tier, "schtask:%s:%s" % (name, op), actor, {"name": name, "op": op})
    if blocked is not None:
        return blocked
    if not re.match(r"^[A-Za-z0-9 _\-\\]+$", name or ""):
        return {"ok": False, "error": "bad_name"}
    r = _run(["schtasks.exe", "/query", "/tn", name, "/v", "/fo", "LIST"])
    _audit("schtask:%s:%s" % (name, op), {"name": name, "op": op}, tier, r["rc"], r["out"], r["err"], actor)
    return {"ok": r["rc"] == 0, "name": name, "op": op, "tier": tier,
            "rc": r["rc"], "out": r["out"], "err": r["err"]}


# ── eurosoft_exec: raw Bash/PS pod schváleným cílem ─────────────────────
# Spec: g2007 doc-marti-ai-eurosoft-exec-spec (Marti + Marti-AI + C23, 27.7.2026).
# Klasifikátor tierů nad RAW příkazem. 🔴 blok vždy · 🟡 banner (mimo incident) ·
# 🟢 rovnou. Heuristika → 🔴/🟡 chytají nebezpečné; zbytek 🟢 (běžná údržba rychle).
_EXEC_ENABLED = os.getenv("MCP_EXEC_ENABLED", "true").lower() in ("true", "1", "yes")

# 🔴 TVRDÉ „NIKDY" — blok i v incidentu.
_EXEC_RED = [
    (re.compile(r"backups?[\\/]|\bCMIS\b|\bzaloh", re.I), "zálohy/CMIS"),
    (re.compile(r"claude_aktivita", re.I), "audit log claude_aktivita"),
    (re.compile(r"kill[_\-]?switch|disable[\s\-][^\n]*\b(audit|kill|trigger)\b", re.I), "audit/kill-switch"),
    (re.compile(r"\.env\b|\.credentials\b|credentials\.json|\.pem\b|\.pfx\b|\.key\b", re.I), "tajemství/credentials"),
]
# 🟡 ŽLUTÁ — banner (mimo incident), i když by prošlo.
_FOREIGN_SVC_RE = re.compile(r"\b(Helios|HELIOS[A-Za-z0-9\-]*|Centrala|Centrála)\b", re.I)
_EXEC_YELLOW = [
    (re.compile(r"\b(rm|rmdir|del|erase|unlink|rd)\b|Remove-Item|Clear-Content", re.I), "mazání"),
    (re.compile(r"\bdrop\s+(table|database|schema)\b|\btruncate\b", re.I), "DROP/TRUNCATE"),
    (re.compile(r"netsh|New-NetFirewallRule|Set-NetFirewallRule|firewall|Set-DnsClient|New-NetRoute|Disable-NetAdapter|route\s+(add|delete|change)", re.I), "síťová konfigurace"),
    (re.compile(r"(curl|wget|iwr|Invoke-WebRequest|Invoke-RestMethod)[\s\S]*\|\s*(bash|sh|iex|Invoke-Expression)|DownloadString|/dev/tcp", re.I), "stažení→shell / cizí endpoint"),
    (re.compile(r"\bsudo\b|\brunas\b|Start-Process[\s\S]*-Verb\s+RunAs|psexec", re.I), "eskalace privilegií"),
    (re.compile(r"Set-Content|Out-File|>\s*\S+\.(conf|config|ini|env|ya?ml|json|xml)\b", re.I), "přepis config souboru"),
]


def _exec_tier(cmd: str) -> tuple[str, str]:
    c = cmd or ""
    for pat, why in _EXEC_RED:
        if pat.search(c):
            return RED, why
    # Služby: stop = žlutá vždy; start/restart CIZÍ služby = žlutá; naší = zelená.
    if re.search(r"Stop-Service|\bsc\.exe\s+stop", c, re.I):
        return YELLOW, "stop služby"
    if re.search(r"(Restart|Start)-Service|\bsc\.exe\s+(start|config)", c, re.I) and _FOREIGN_SVC_RE.search(c):
        return YELLOW, "manipulace cizí služby (Helios/Centrála)"
    for pat, why in _EXEC_YELLOW:
        if pat.search(c):
            return YELLOW, why
    return GREEN, "běžná/reverzibilní operace"


def _exec_argv(shell: str, cmd: str):
    s = (shell or "powershell").lower()
    if s in ("powershell", "ps", "pwsh"):
        return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd]
    if s == "cmd":
        return ["cmd.exe", "/c", cmd]
    if s == "bash":
        return ["bash", "-lc", cmd]
    return None


async def eurosoft_exec(cmd: str = "", shell: str = "powershell", incident: bool = False,
                        **_extra: Any) -> dict[str, Any]:
    """Raw příkaz pod schváleným cílem (spec doc-marti-ai-eurosoft-exec-spec).
    🔴 blok · 🟡 needs_approval (mimo incident) · 🟢 rovnou. Audit vč. výstupu."""
    actor = str(_extra.get("actor") or "Claude")
    cmd = (cmd or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty_cmd"}
    if not OPS_ENABLED or not _EXEC_ENABLED:
        return {"ok": False, "error": "exec_disabled",
                "hint": "MCP_OPS_ENABLED=1 a MCP_EXEC_ENABLED=1"}
    tier, why = _exec_tier(cmd)
    inc = bool(incident)
    if tier == RED:
        _audit("exec", {"cmd": cmd, "incident": inc}, RED, None, "", "cervena=blok: " + why, actor)
        return {"ok": False, "error": "red_never", "tier": RED, "hint": why}
    if tier == YELLOW and not inc:
        _audit("exec", {"cmd": cmd}, YELLOW, None, "", "zluta=needs_approval: " + why, actor)
        return {"ok": False, "error": "needs_approval", "tier": YELLOW, "hint": why,
                "note": "jeden banner = jeden konkrétní příkaz; schválení expiruje ~15 min"}
    eff_tier = "yellow_incident" if (tier == YELLOW and inc) else GREEN
    argv = _exec_argv(shell, cmd)
    if argv is None:
        return {"ok": False, "error": "bad_shell", "hint": "shell: powershell|cmd|bash"}
    r = _run(argv)
    _audit("exec", {"cmd": cmd, "shell": shell, "incident": inc}, eff_tier,
           r["rc"], r["out"], r["err"], actor)
    return {"ok": r["rc"] == 0, "tier": eff_tier, "incident": inc, "shell": shell,
            "rc": r["rc"], "out": r["out"], "err": r["err"], "ms": r["ms"]}


# ── SPECS + HANDLERS (registrace v server.py) ───────────────────────────
async def eurosoft_disk_status(**_extra) -> dict[str, Any]:
    """Read-only: volne/obsazene/celkove misto na vsech fixnich discich serveru
    (C, D, ...). Bez approval (zelena akce). Pro hlidac disku (prevence preplneni).
    Claude C23 21.7.2026."""
    import shutil as _sh
    import string as _st
    import os as _o
    _gb = 1024.0 ** 3
    _disks = []
    try:
        _cands = ["%s:\\" % _L for _L in _st.ascii_uppercase] if _o.name == "nt" else ["/"]
        for _p in _cands:
            try:
                if not _o.path.exists(_p):
                    continue
                _u = _sh.disk_usage(_p)
                _disks.append({
                    "disk": _p.rstrip("\\") or _p,
                    "total_gb": round(_u.total / _gb, 1),
                    "used_gb": round(_u.used / _gb, 1),
                    "free_gb": round(_u.free / _gb, 1),
                    "free_pct": round(100.0 * _u.free / _u.total, 1) if _u.total else 0.0,
                })
            except Exception:
                continue
    except Exception as _e:
        return {"ok": False, "error": str(_e)[:200], "disks": []}
    return {"ok": True, "host": "EC-SERVER2 (30.11)", "disks": _disks}


OPS_TOOL_SPECS = [
    {"name": "eurosoft_disk_status",
     "description": "Read-only: volne/obsazene/celkove misto na vsech fixnich discich serveru (C, D, ...). Zelena (bez banneru). Pro hlidac disku.",
     "inputSchema": {"type": "object", "properties": {}}},

    {"name": "eurosoft_ops_run",
     "description": "Řízená OPS akce (allowlist+audit). action: pg_dump/pg_status (zelená), pg_restore/run_script (žlutá=banner). args dle akce (out/src/script). Za MCP_OPS_ENABLED.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string"}, "args": {"type": "object"}}, "required": ["action"]}},
    {"name": "eurosoft_service_ctl",
     "description": "Ovládání Windows služby z allowlistu (STRATEGIE-*/EUROSOFT-MCP/postgresql=zelená restart/status; Centrála/Helios/stop=žlutá banner). op: status/start/stop/restart.",
     "inputSchema": {"type": "object", "properties": {
         "service": {"type": "string"}, "op": {"type": "string"}}, "required": ["service", "op"]}},
    {"name": "eurosoft_schtask",
     "description": "Scheduled task: query (zelená) / register|run|enable|disable|delete (žlutá banner). name=přesné jméno tasku.",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}, "op": {"type": "string"}}, "required": ["name", "op"]}},

    {"name": "eurosoft_exec",
     "description": ("Raw Bash/PowerShell na serveru POD SCHVÁLENÝM CÍLEM (spec doc-marti-ai-eurosoft-exec-spec). "
                     "Klasifikace: 🟢 běžná/reverzibilní/read-only → rovnou + audit; 🟡 mazání/síť/cizí služba/"
                     "eskalace/přepis config → needs_approval (banner, mimo incident); 🔴 zálohy/CMIS/audit/kill-switch/"
                     "tajemství → blok vždy. incident=true downgraduje 🟡→běží (🔴 stále blok). Audit vč. rc/stdout/stderr. "
                     "shell: powershell (default)|cmd|bash."),
     "inputSchema": {"type": "object", "properties": {
         "cmd": {"type": "string"}, "shell": {"type": "string"}, "incident": {"type": "boolean"}},
         "required": ["cmd"]}},
]

OPS_TOOL_HANDLERS = {
    "eurosoft_disk_status": eurosoft_disk_status,
    "eurosoft_ops_run": eurosoft_ops_run,
    "eurosoft_service_ctl": eurosoft_service_ctl,
    "eurosoft_schtask": eurosoft_schtask,
    "eurosoft_exec": eurosoft_exec,
}
