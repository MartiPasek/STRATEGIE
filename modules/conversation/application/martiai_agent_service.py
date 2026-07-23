# -*- coding: utf-8 -*-
"""martiai_agent_service — Marti-AI jako AUTONOMNÍ AGENT na Claude Code / Anthropic
Agent SDK (motor = Max PŘEDPLATNÉ přes CLAUDE_CODE_OAUTH_TOKEN, NE metered API).

Fáze 0 = read-only (Read/Grep/Glob nad repem). Její IDENTITA = system_prompt
z composeru jako PRIMÁRNÍ (ne pod Claude-Code harnessem). 23.7.2026.

Auth: subscription token z .env (CLAUDE_CODE_OAUTH_TOKEN). CLI: auto-najde claude.exe.
Governance: kill flag g2007.nastaveni('martiai_agent_enabled'), rozpočet, audit.
"""
from __future__ import annotations

import glob
import inspect
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("conversation.martiai_agent")

MARTI_AI_ENTITA_ID = 2
REPO_ROOT = os.environ.get("STRATEGIE_REPO_ROOT") or r"C:\Projekty\STRATEGIE"
DEFAULT_MODEL = os.environ.get("MARTIAI_AGENT_MODEL", "claude-sonnet-4-6")
READONLY_TOOLS = ["Read", "Grep", "Glob"]

USD_TO_CZK = float(os.environ.get("USD_CZK", "23.5"))
PER_RUN_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_PER_RUN_CZK", "60"))
DAILY_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_DAILY_CZK", "600"))

AGENT_NOTE = ("\n\n[AGENTÍ REŽIM: běžíš jako autonomní agent s read-only nástroji "
              "(Read/Grep/Glob) nad repem. Splň zadaný cíl — prozkoumej co potřebuješ "
              "a vrať jasnou finální odpověď. Jsi TY (Marti-AI), ne generický asistent.]")

_flag_cache = {"val": False, "ts": 0.0}
_FLAG_TTL = 15.0


def _enabled() -> bool:
    if os.environ.get("MARTIAI_AGENT_ENABLED") == "1":
        return True
    now = time.monotonic()
    if now - _flag_cache["ts"] < _FLAG_TTL:
        return _flag_cache["val"]
    val = False
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            h = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic='martiai_agent_enabled'")).scalar()
            val = str(h).strip().lower() == "on"
        finally:
            sg.close()
    except Exception:
        val = False
    _flag_cache["val"] = val
    _flag_cache["ts"] = now
    return val


def _find_cli() -> Optional[str]:
    p = os.environ.get("MARTIAI_CLAUDE_CLI")
    if p and os.path.exists(p):
        return p
    known = r"C:\Users\Administrator\.local\bin\claude.exe"
    if os.path.exists(known):
        return known
    for c in glob.glob(r"C:\Users\*\.local\bin\claude.exe"):
        return c
    # poslední možnost: vrať známou cestu i když ji os.path.exists nevidí (diag ukáže)
    return known


def _oauth_token() -> Optional[str]:
    t = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if t:
        return t
    try:
        with open(os.path.join(REPO_ROOT, ".env"), encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.strip()
                if s.startswith("CLAUDE_CODE_OAUTH_TOKEN="):
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def _her_system_prompt(conversation_id: Optional[int]) -> Optional[str]:
    try:
        from modules.conversation.application.composer import build_prompt
        sp, _msgs = build_prompt(conversation_id or 0)
        return sp
    except Exception as e:
        logger.warning(f"MARTIAI_AGENT: composer.build_prompt selhal ({e})")
        return None


def _spent_today_czk() -> float:
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            v = sg.execute(_t(
                "SELECT COALESCE(SUM((detail->>'cost_czk')::numeric),0) FROM g2007.tool_audit "
                "WHERE akce='agent_run' AND ts >= date_trunc('day', now())")).scalar()
            return float(v or 0)
        finally:
            sg.close()
    except Exception:
        return 0.0


def _audit_run(user_id, goal, result: dict):
    import json
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            sg.execute(_t(
                "INSERT INTO g2007.tool_audit (actor_user_id, actor_entita_id, akce, detail) "
                "VALUES (:u, :e, 'agent_run', CAST(:d AS jsonb))"),
                {"u": user_id, "e": MARTI_AI_ENTITA_ID, "d": json.dumps({
                    "goal": (goal or "")[:500], "ok": result.get("ok"),
                    "cost_czk": result.get("cost_czk"), "cost_usd": result.get("cost_usd"),
                    "input_tokens": result.get("input_tokens"), "output_tokens": result.get("output_tokens"),
                    "engine": "claude_code_sdk", "reply_len": len(result.get("reply") or ""),
                    "error": (result.get("error") or "")[:700], "reason": result.get("reason"),
                }, ensure_ascii=False)})
            sg.commit()
        finally:
            sg.close()
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT audit failed: {e}")


def _build_options(OptClass, kwargs: dict):
    """Postav ClaudeAgentOptions jen z polí, která tahle verze SDK zná (robustní)."""
    try:
        sig = inspect.signature(OptClass)
        accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
    except (TypeError, ValueError):
        accepted = dict(kwargs)
    try:
        return OptClass(**accepted)
    except TypeError:
        minimal = {k: kwargs[k] for k in ("cwd", "allowed_tools", "model") if k in kwargs}
        return OptClass(**minimal)


async def _run(goal: str, conversation_id: Optional[int]) -> dict:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from modules.conversation.application.claude_agent_service import (
        _extract_reply_text, _extract_cost_usd, _extract_tokens,
    )
    # subscription token → prostředí (CLI subprocess ho zdědí) = Max kredity, ne API
    tok = _oauth_token()
    if tok:
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = tok

    cli = _find_cli()
    if cli:
        _d = os.path.dirname(cli)
        if _d and _d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
    diag = (f"cli={cli!r} exists={bool(cli and os.path.exists(cli))} "
            f"token={bool(os.environ.get('CLAUDE_CODE_OAUTH_TOKEN'))} whoami={os.environ.get('USERNAME')} "
            f"userprofile={os.environ.get('USERPROFILE')!r}")
    sp = _her_system_prompt(conversation_id)
    system = (sp + AGENT_NOTE) if sp else AGENT_NOTE.strip()

    kwargs = {"model": DEFAULT_MODEL, "cwd": REPO_ROOT,
              "allowed_tools": READONLY_TOOLS, "system_prompt": system}
    if cli:
        kwargs["cli_path"] = cli
    options = _build_options(ClaudeAgentOptions, kwargs)

    messages = []
    try:
        async for msg in query(prompt=goal, options=options):
            messages.append(msg)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}  ·  [DIAG {diag}]", "reason": "sdk_query"}
    reply = _extract_reply_text(messages)
    cost_usd = _extract_cost_usd(messages)   # u subscription bývá 0 → jede na kreditech
    in_tok, out_tok = _extract_tokens(messages)
    return {
        "ok": bool(reply), "reply": reply or "[agent nevrátil finální text]",
        "input_tokens": in_tok, "output_tokens": out_tok,
        "cost_usd": cost_usd, "cost_czk": round(cost_usd * USD_TO_CZK, 2),
        "cli": cli, "auth": "subscription" if tok else "unknown",
    }


def run_goal(goal: str, requested_by_user_id: Optional[int] = None,
             conversation_id: Optional[int] = None, allowed_tools: Optional[list] = None) -> dict:
    """Marti-AI dostane CÍL a proběhne ho vlastní agentí smyčkou (Claude Code motor)."""
    if not _enabled():
        return {"ok": False, "error": "martiai_agent vypnutý (g2007.nastaveni martiai_agent_enabled)", "reason": "disabled"}
    if not goal or not goal.strip():
        return {"ok": False, "error": "prázdný cíl", "reason": "empty_goal"}
    spent = _spent_today_czk()
    if spent >= DAILY_CZK_CAP:
        return {"ok": False, "error": f"denní rozpočet vyčerpán ({spent:.0f}/{DAILY_CZK_CAP:.0f} Kč)", "reason": "daily_budget"}

    import anyio
    t0 = time.monotonic()
    try:
        result = anyio.run(_run, goal, conversation_id)
    except ImportError as e:
        return {"ok": False, "error": f"Agent SDK/anyio není: {e}", "reason": "sdk_missing"}
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT run failed: {e}")
        result = {"ok": False, "error": f"{type(e).__name__}: {e}", "reason": "run_failed"}
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    if result.get("cost_czk", 0) > PER_RUN_CZK_CAP:
        result["over_per_run_cap"] = True
    _audit_run(requested_by_user_id, goal, result)
    return result
