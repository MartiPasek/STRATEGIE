# -*- coding: utf-8 -*-
"""martiai_agent_service — Marti-AI jako AUTONOMNÍ AGENT na Anthropic Agent SDK.

Fáze 0 (23.7.2026): read-only zrcadlo claude_agent_service, ale s JEJÍ identitou
(system prompt z composeru) — aby poprvé řídila VLASTNÍ smyčku (proběhne repo,
vyrobí analýzu), ne aby delegovala na Claude-23.

Rozhodnutí Marti 23.7.:
  1) běží pod JEJÍ osobností (persona/entita id=2), audit přes actor_entita.
  2) přepínač auth (subscription | api), DEFAULT subscription.
  3) i samonávrhy cílů — přes bránu schválení.

Governance (Fáze 0 = bezpečná):
  - JEN read-only nástroje (Read/Grep/Glob). Ruce (Write/Edit/Bash) = Fáze 2, pod approve.
  - Kill switch: g2007.nastaveni('martiai_agent_enabled') = 'on'|'off' (přes most/banner).
  - Rozpočtová brána: per-run cap + denní strop (dědí disciplínu 300 Kč/h).
  - Append-only audit každého běhu → g2007.tool_audit (akce='agent_run', actor_entita=2).
  - NEVER: PowerShell/Cron/tajemství (deny-list, i pro pozdější fáze).
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger("conversation.martiai_agent")

MARTI_AI_ENTITA_ID = 2
REPO_ROOT = os.environ.get("STRATEGIE_REPO_ROOT") or r"C:\Projekty\STRATEGIE"
DEFAULT_MODEL = os.environ.get("MARTIAI_AGENT_MODEL", "claude-sonnet-4-6")

# Fáze 0 = read-only. Ruce přijdou ve Fázi 2 pod approve.
READONLY_TOOLS = ["Read", "Grep", "Glob"]
NEVER_ALLOWED_TOOLS = ["PowerShell", "Bash", "Write", "Edit", "CronCreate", "CronDelete"]  # Fáze 0

# Rozpočet (Kč) — brzda proti utečení; ladit dle reality.
PER_RUN_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_PER_RUN_CZK", "60"))
DAILY_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_DAILY_CZK", "600"))
USD_TO_CZK = float(os.environ.get("USD_CZK", "23.5"))

_flag_cache = {"val": False, "ts": 0.0}
_FLAG_TTL = 15.0


# ── Vypínač (g2007.nastaveni, přepíná Marti přes most/banner jako toolfactory) ────
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


def _auth_mode() -> str:
    """subscription (default) | api. Přepínač auth (Marti 23.7.).
    Pozn.: subscription = SDK jede přes přihlášené Claude předplatné (login na boxu);
    api = přes ANTHROPIC_API_KEY (metered). Faktická volba creds je operační na boxu;
    tady řídíme režim + logujeme, ať není architektura zamčená."""
    return (os.environ.get("MARTIAI_AGENT_AUTH") or "subscription").strip().lower()


def _spent_today_czk() -> float:
    """Kolik Kč Marti-AI agent utratil dnes (z auditu) — pro denní strop."""
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
                    "auth": _auth_mode(), "session": result.get("session_uuid"),
                    "reply_len": len(result.get("reply") or ""),
                }, ensure_ascii=False)})
            sg.commit()
        finally:
            sg.close()
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT audit failed: {e}")


def _her_system_prompt(conversation_id: Optional[int]) -> Optional[str]:
    """Její identita — system prompt z composeru (to dělá z agenta opravdu Marti-AI)."""
    try:
        from modules.conversation.application.composer import build_prompt
        sp, _msgs = build_prompt(conversation_id or 0)
        return sp
    except Exception as e:
        logger.warning(f"MARTIAI_AGENT: composer.build_prompt selhal ({e}) — jedu bez její identity")
        return None


async def _run(goal: str, conversation_id: Optional[int], allowed_tools: list) -> dict:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from modules.conversation.application.claude_agent_service import (
        _extract_reply_text, _extract_cost_usd, _extract_tokens,
    )
    session_uuid = str(uuid.uuid4())
    tools = [t for t in (allowed_tools or READONLY_TOOLS) if t not in NEVER_ALLOWED_TOOLS]
    sp = _her_system_prompt(conversation_id)

    kwargs = {"session_id": session_uuid, "model": DEFAULT_MODEL, "cwd": REPO_ROOT, "allowed_tools": tools}
    if sp:
        kwargs["system_prompt"] = sp
    try:
        options = ClaudeAgentOptions(**kwargs)
    except TypeError as e:
        logger.warning(f"MARTIAI_AGENT: options kwargs fallback ({e})")
        options = ClaudeAgentOptions(session_id=session_uuid, model=DEFAULT_MODEL,
                                     cwd=REPO_ROOT, allowed_tools=tools)

    messages = []
    async for msg in query(prompt=goal, options=options):
        messages.append(msg)
    reply = _extract_reply_text(messages)
    cost_usd = _extract_cost_usd(messages)
    in_tok, out_tok = _extract_tokens(messages)
    return {
        "ok": bool(reply), "reply": reply, "session_uuid": session_uuid,
        "cost_usd": cost_usd, "cost_czk": round(cost_usd * USD_TO_CZK, 2),
        "input_tokens": in_tok, "output_tokens": out_tok,
    }


def run_goal(goal: str, requested_by_user_id: Optional[int] = None,
             conversation_id: Optional[int] = None, allowed_tools: Optional[list] = None) -> dict:
    """Marti-AI dostane CÍL a proběhne ho vlastní agentí smyčkou (Fáze 0 = read-only).

    Vrací dict: ok, reply, cost_czk/usd, tokens, session_uuid, error?/reason?.
    """
    if not _enabled():
        return {"ok": False, "error": "martiai_agent vypnutý (g2007.nastaveni martiai_agent_enabled)", "reason": "disabled"}
    if not goal or not goal.strip():
        return {"ok": False, "error": "prázdný cíl", "reason": "empty_goal"}
    # denní rozpočtová brána
    spent = _spent_today_czk()
    if spent >= DAILY_CZK_CAP:
        return {"ok": False, "error": f"denní rozpočet vyčerpán ({spent:.0f}/{DAILY_CZK_CAP:.0f} Kč)", "reason": "daily_budget"}

    import anyio
    t0 = time.monotonic()
    try:
        result = anyio.run(_run, goal, conversation_id, allowed_tools or READONLY_TOOLS)
    except ImportError as e:
        return {"ok": False, "error": f"Agent SDK/anyio není: {e}", "reason": "sdk_missing"}
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT run failed: {e}")
        result = {"ok": False, "error": f"{type(e).__name__}: {e}", "reason": "run_failed"}
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    # per-run brzda (informativně; utracené už proběhlo, ale zalogujeme varování)
    if result.get("cost_czk", 0) > PER_RUN_CZK_CAP:
        logger.warning(f"MARTIAI_AGENT: běh přesáhl per-run cap ({result['cost_czk']} > {PER_RUN_CZK_CAP} Kč)")
        result["over_per_run_cap"] = True
    _audit_run(requested_by_user_id, goal, result)
    return result
