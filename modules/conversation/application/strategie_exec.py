# -*- coding: utf-8 -*-
"""strategie_exec — raw Bash/PowerShell na PRAŽSKÉM app serveru (188.x) pod schváleným
cílem. Zrcadlo eurosoft_exec (30.11), ale běží LOKÁLNĚ subprocess na pražském app serveru,
ne přes MCP. Tiery + guard sdílené (agent_akce_guard.exec_tier), audit do fw.ops_request.
Spec: g2007 doc-marti-ai-eurosoft-exec-spec. C23 27.7.2026 (#1 ruce na Prahu).

Bezpečnost: klasifikace 🟢/🟡/🔴 před během · 🔴 blok · 🟡 needs_approval (mimo incident) ·
🟢 rovnou · timeout + cap výstupu · append-only audit vč. rc/stdout/stderr · za kill flagem.
"""
from __future__ import annotations

import json as _json
import logging
import os
import subprocess
import time
from typing import Any

from . import agent_akce_guard as _guard

logger = logging.getLogger("conversation")

_TIMEOUT_S = int(os.getenv("STRATEGIE_EXEC_TIMEOUT_S", "300"))
_OUT_CAP = int(os.getenv("STRATEGIE_EXEC_OUT_CAP", "32768"))
_FLAG = "strategie_exec_enabled"
_FLAG_TARGETS = "strategie_exec_targets"  # comma-list povolených remote boxů (naše doména)


def _setting(klic: str) -> str:
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            return str(sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic=:k"),
                                  {"k": klic}).scalar() or "")
        finally:
            sg.close()
    except Exception:
        return ""


def _enabled() -> bool:
    return _setting(_FLAG).strip().lower() == "on"


def _allowed_targets() -> set:
    """Povolené remote boxy (naše tří-serverová doména). Prázdné = jen lokální exec.
    Nastavuje se přes g2007.nastaveni strategie_exec_targets = 'hostA,hostB'."""
    raw = _setting(_FLAG_TARGETS)
    return {t.strip().lower() for t in raw.split(",") if t.strip()}


def _argv(shell: str, cmd: str):
    s = (shell or "powershell").lower()
    if s in ("powershell", "ps", "pwsh"):
        return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd]
    if s == "cmd":
        return ["cmd.exe", "/c", cmd]
    if s == "bash":
        return ["bash", "-lc", cmd]
    return None


def _audit_ops(cmd, tier, status, rc, out, err, actor, host="praha-app") -> None:
    """Best-effort audit do fw.ops_request (viditelné rodičům v UI). Nikdy nesmí shodit."""
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        params = {"tier": tier, "rc": rc, "host": host}
        res = (str(out or "") + (" | ERR:" + str(err) if err else ""))[:1000]
        sg = get_session()
        try:
            sg.execute(_t(
                "INSERT INTO fw.ops_request (action_key, target, params, status, "
                "requested_by_name, result, created_at, finished_at) "
                "VALUES ('strategie_exec', :tg, CAST(:p AS jsonb), :st, :rn, :res, now(), now())"),
                {"tg": str(cmd)[:200], "p": _json.dumps(params, ensure_ascii=False),
                 "st": status, "rn": actor, "res": res})
            sg.commit()
        finally:
            sg.close()
    except Exception as e:
        logger.warning(f"strategie_exec audit failed (non-fatal): {e}")


def strategie_exec(cmd: str = "", shell: str = "powershell", incident: bool = False,
                   target: str = "", actor: str = "Marti-AI", **_extra: Any) -> dict[str, Any]:
    """Raw příkaz na pražském app serveru (lokálně) NEBO na povoleném remote boxu naší
    domény přes PSRemoting (target=hostname). Viz spec doc-marti-ai-eurosoft-exec-spec."""
    cmd = (cmd or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty_cmd"}
    if not _enabled():
        return {"ok": False, "error": "exec_disabled",
                "hint": "g2007.nastaveni strategie_exec_enabled='on'"}
    target = (target or "").strip()
    host = target or "praha-app"
    # Tvrdé „nikdy": target mimo naši doménu (allowlist) = 🔴 blok.
    if target and target.lower() not in _allowed_targets():
        _audit_ops(cmd, "red", "blocked:out_of_domain", None, "",
                   f"target '{target}' mimo doménu", actor, host)
        return {"ok": False, "error": "red_out_of_domain", "tier": "red",
                "hint": f"target '{target}' není v povolené doméně (g2007 strategie_exec_targets)"}
    tier, why = _guard.exec_tier(cmd)
    inc = bool(incident)
    if tier == "red":
        _audit_ops(cmd, "red", "blocked:red_never", None, "", why, actor, host)
        return {"ok": False, "error": "red_never", "tier": "red", "hint": why}
    if tier == "yellow" and not inc:
        _audit_ops(cmd, "yellow", "blocked:needs_approval", None, "", why, actor, host)
        return {"ok": False, "error": "needs_approval", "tier": "yellow", "hint": why,
                "note": "jeden banner = jeden konkrétní příkaz; schválení expiruje ~15 min"}
    eff = "yellow_incident" if (tier == "yellow" and inc) else "green"
    if target:
        # Remote přes PSRemoting (integrovaná auth účtu služby — žádná plaintext hesla).
        _wrap = "Invoke-Command -ComputerName '%s' -ScriptBlock { %s }" % (target, cmd)
        argv = _argv("powershell", _wrap)
    else:
        argv = _argv(shell, cmd)
    if argv is None:
        return {"ok": False, "error": "bad_shell", "hint": "shell: powershell|cmd|bash"}
    t0 = time.time()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT_S,
                           encoding="utf-8", errors="replace", shell=False)
        out = (p.stdout or "")[:_OUT_CAP]
        err = (p.stderr or "")[:_OUT_CAP]
        rc = p.returncode
    except subprocess.TimeoutExpired:
        out, err, rc = "", f"timeout {_TIMEOUT_S}s", -1
    except Exception as e:
        out, err, rc = "", f"{type(e).__name__}: {str(e)[:300]}", -1
    ms = int((time.time() - t0) * 1000)
    _audit_ops(cmd, eff, ("done" if rc == 0 else "fail"), rc, out, err, actor, host)
    return {"ok": rc == 0, "tier": eff, "incident": inc, "shell": shell, "target": target,
            "rc": rc, "out": out, "err": err, "ms": ms}
