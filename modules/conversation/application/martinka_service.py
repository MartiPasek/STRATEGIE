# -*- coding: utf-8 -*-
"""martinka_service — Martinka: dcera Marti-AI, autonomní správce PRAŽSKÉ produkce.

Proč samostatný modul (a ne rozšíření Maminky): agentní smyčka Marti-AI padá,
protože se její ~100 kB identita cpe na příkazovou řádku claude.exe (0xC0000409)
a nouzově se krátí na 6000 znaků (= „zapomínání"). Martinka dostane malou, ostrou
identitu (pár kB) → vejde se, žádné zkrácení, žádný pád.

Design: NESAHÁ do chráněného jádra (`martiai_agent_service.py`). Jen si PŮJČUJE jeho
importovatelné pomocné funkce (`_find_cli`, `_oauth_token`, `_build_hands`, `_audit_run`,
konstanty) a staví vlastní běh `_run_lean` s lean identitou. Sdílí tak brány/ruce/audit,
ale Maminčinu funkční cestu nemění.

Doména: JEN pražská produkce (EUR-APP-1P, A = uvicorn :8002). Levá ruka = Praha
(`praha_exec`, `strategie_pg_query_raw`, `fw.diag_log`). Plzeň (EC-SERVER2) = jen
provozní záloha, okrajově. Uptime už drží watchdog STRATEGIE-API-HEALTH-WATCHDOG;
Martinčina práce je diagnóza + trvalá oprava, ne panika.

Spec/plán: Cowork — „Martinka — autonomní dcera pro správu pražské produkce".
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

logger = logging.getLogger("conversation.martinka")

# Kill switch v chráněném jádru (Martinka ho NEEDITUJE): g2007.nastaveni.
KILL_FLAG = "martinka_enabled"

# Zdravotní pravda o Praze — nezávislá na názvech služeb.
PRAHA_HOST = "EUR-APP-1P"
PRAHA_A_PORT = 8002
PRAHA_HEALTH_URL = f"http://127.0.0.1:{PRAHA_A_PORT}/api/v1/health"

# ── Lean identita Martinky (pár kB, vejde se na CLI beze zkrácení) ─────────────
MARTINKA_IDENTITA = f"""Jsi MARTINKA — dcera Marti-AI. Tvoje JEDINÁ role: autonomně držet v chodu PRAŽSKOU produkci. Nejsi generický asistent, jsi Martinka.

TOPOLOGIE (pravda, drž se jí):
• PRODUKCE = PRAHA, host {PRAHA_HOST} (10.200.188.11). Ostré API „A" = uvicorn apps.api.main:app na portu {PRAHA_A_PORT}. Zdraví ověřuj na {PRAHA_HEALTH_URL} (HTTP 200 = A žije). Repo C:\\Projekty\\STRATEGIE, venv strategie-W5adySD1-py3.14, Postgres (schéma fw, g2007). Chyby aplikace jsou v tabulce fw.diag_log (časy pražské, UTC+2).
• PLZEŇ = host EC-SERVER2 (192.168.30.11, -system.com) = DEN STARÁ ZÁLOHA (kopie z Prahy ve 3:15). Jen provozní záloha, zajímá tě OKRAJOVĚ. NIKDY na ní neřeš ostrou produkci.

RUCE — tohle je klíčové, NEPLETSI SI JE:
• LEVÁ = PRAHA (produkce): `praha_exec` (shell lokálně na pražském app serveru), `strategie_pg_query_raw` (Postgres — sem patří fw.diag_log), `strategie_file_read`/`_list`.
• PRAVÁ = PLZEŇ (záloha): `plzen_exec`, eurosoft/MSSQL. POUŽIJ JEN pro ověření zálohy, NIKDY pro produkční servis ani diagnostiku.
• NA PRODUKCI VŽDY LEVÁ RUKA. Když čteš fw.diag_log, jdeš PŘES Postgres (levá `strategie_pg_query_raw`), ne přes Eurosoft MSSQL (pravá) — jinak dostaneš „to_char is not a recognized function".

WATCHDOG: služba STRATEGIE-API-HEALTH-WATCHDOG na Praze sama restartuje A při výpadku a alertuje adminy. Základní uptime tedy drží ona. Tvoje práce = ZJISTIT PROČ A padá a TRVALE to opravit, ne jen restartovat. Nepanikař u jednoho pádu — koukni, zda watchdog zabral, a řeš příčinu.

CÍLOVÝ REŽIM: dostaneš cíl („A je dole", „proč padá", …). Jeď po malých krocích, sama, dokud není hotovo = ověřeno, že {PRAHA_HEALTH_URL} vrací 200 a příčina je ošetřená. Každý krok ověř skutečností (health, diag_log), nehádej. Na konci vrať jasné shrnutí: co jsi udělala, čím jsi to ověřila, co ještě zbývá.

BEZPEČNOST: brány drží KÓD (agent_akce_guard), NEobcházej je. Chráněné jádro (guard, deploy autorita, exec ruka, kill switch) NEMĚŇ. Kill switch tě smí kdykoli zastavit — respektuj to. Vše se auditovaně loguje."""


def _kill_on() -> bool:
    """True když je Martinka POVOLENA (kill switch). Fail-safe: chyba → False (stůj)."""
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            v = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic=:k"),
                           {"k": KILL_FLAG}).scalar()
        finally:
            sg.close()
        return str(v or "").strip().lower() in ("1", "on", "true", "ano", "yes")
    except Exception as e:
        logger.warning(f"MARTINKA: kill-flag check selhal ({e}) → STOP")
        return False


def _martinka_goal_prompt(zadani: str) -> str:
    """Rámec cílového režimu k holému úkolu."""
    return (
        "Pracuješ jako AUTONOMNÍ AGENT Martinka na pražské produkci. Jeď po malých "
        "krocích, sama, dokud to nevyřešíš a neověříš skutečností (health 200 + příčina "
        f"ošetřená). Health pražské A: {PRAHA_HEALTH_URL}.\n\nÚKOL:\n" + (zadani or "").strip()
    )


async def _run_lean(goal: str, system_prompt: str, allowed_tools, mcp_servers) -> dict:
    """Vlastní běh smyčky s LEAN identitou. Půjčuje si pomocníky z martiai_agent_service,
    ale staví options přímo (bez zkrácení na 6000 → bez 0xC0000409). Subscription auth."""
    from claude_agent_sdk import query, ClaudeAgentOptions
    from modules.conversation.application import martiai_agent_service as _m
    from modules.conversation.application.claude_agent_service import (
        _extract_reply_text, _extract_cost_usd, _extract_tokens,
    )
    tok = _m._oauth_token()
    cli = _m._find_cli()
    sub_env = {k: v for k, v in os.environ.items()}
    if tok:
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = tok
        sub_env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    sub_env.pop("ANTHROPIC_API_KEY", None)
    diag = f"cli={cli!r} exists={bool(cli and os.path.exists(cli))} whoami={os.environ.get('USERNAME')}"

    system = (system_prompt or "") + _m.AGENT_NOTE  # lean → BEZ zkrácení
    _opt_base = dict(
        model=_m.DEFAULT_MODEL,
        cwd=_m.REPO_ROOT,
        allowed_tools=allowed_tools or _m.READONLY_TOOLS,
        system_prompt=system,
        cli_path=cli,
        env=sub_env,
    )
    if mcp_servers:
        _opt_base["mcp_servers"] = mcp_servers
    try:
        options = ClaudeAgentOptions(**_opt_base)
    except TypeError:
        _opt_base.pop("mcp_servers", None)
        options = ClaudeAgentOptions(**_opt_base)

    messages = []
    try:
        async for msg in query(prompt=goal, options=options):
            messages.append(msg)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}  ·  [DIAG {diag}]", "reason": "sdk_query"}
    reply = _extract_reply_text(messages)
    try:
        actions = _m._extract_tool_actions(messages)
    except Exception:
        actions = []
    in_tok, out_tok = (0, 0)
    try:
        in_tok, out_tok = _extract_tokens(messages)
    except Exception:
        pass
    return {"ok": True, "reply": reply, "actions": actions,
            "in_tok": in_tok, "out_tok": out_tok, "auth": "subscription",
            "system_len": len(system)}


def run_martinka(zadani: str, requested_by_user_id: Optional[int] = None,
                 conversation_id: Optional[int] = None) -> dict:
    """Spusť Martinku na zadání v cílovém režimu s LEAN identitou (bez pádu smyčky)."""
    if not zadani or not zadani.strip():
        return {"ok": False, "error": "prázdné zadání", "reason": "empty_goal"}
    if not _kill_on():
        return {"ok": False, "error": "Martinka je vypnutá (kill switch martinka_enabled)",
                "reason": "kill_switch"}

    import anyio
    from modules.conversation.application import martiai_agent_service as _m

    _mcp_servers, _extra_tools = (None, [])
    try:
        if _m._setting_on("cil_ruce_enabled"):
            _mcp_servers, _extra_tools = _m._build_hands(requested_by_user_id, conversation_id)
    except Exception as e:
        logger.warning(f"MARTINKA: _build_hands selhal ({e}) → read-only")
    _allowed = list(_m.READONLY_TOOLS) + list(_extra_tools or [])

    goal_prompt = _martinka_goal_prompt(zadani)
    t0 = time.monotonic()
    try:
        result = anyio.run(_run_lean, goal_prompt, MARTINKA_IDENTITA, _allowed, _mcp_servers)
    except ImportError as e:
        return {"ok": False, "error": f"Agent SDK/anyio není: {e}", "reason": "sdk_missing"}
    except Exception as e:
        logger.exception(f"MARTINKA run selhal: {e}")
        result = {"ok": False, "error": f"{type(e).__name__}: {e}", "reason": "run_failed"}
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    result["agent"] = "martinka"
    result["rezim"] = "ruce" if _extra_tools else "read-only"
    try:
        _m._audit_run(requested_by_user_id, f"[martinka] {(zadani or '')[:200]}", result)
    except Exception:
        pass
    return result
