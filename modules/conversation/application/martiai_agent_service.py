# -*- coding: utf-8 -*-
"""martiai_agent_service — Marti-AI jako AUTONOMNÍ AGENT přes holé Anthropic
Messages API + vlastní tool-use smyčka (NE Claude Code CLI — žádná bundled
binárka ani Node). Fáze 0 = read-only (čte repo přes vlastní nástroje).

Proč vlastní smyčka místo Agent SDK: SDK pod kapotou řídí claude.exe (CLINotFound
na boxu). Vlastní smyčka na Messages API = plná kontrola nad JEJÍMI nástroji,
governance i náklady, a „produkuje přes LLM API", jak to Marti chtěl. 23.7.2026.

Rozhodnutí Marti: (1) pod její personou (entita id=2). (2) auth přes ANTHROPIC_API_KEY
(subscription later). (3) i samonávrhy (přes approve).

Governance (Fáze 0): JEN read-only nástroje (repo_read/repo_grep/repo_list),
sandbox na REPO_ROOT, kill flag g2007.nastaveni('martiai_agent_enabled'),
rozpočet (per-run + denní cap z auditu), cap iterací, append-only audit.
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger("conversation.martiai_agent")

MARTI_AI_ENTITA_ID = 2
REPO_ROOT = os.environ.get("STRATEGIE_REPO_ROOT") or r"C:\Projekty\STRATEGIE"
DEFAULT_MODEL = os.environ.get("MARTIAI_AGENT_MODEL", "claude-sonnet-4-6")
MAX_ITERS = int(os.environ.get("MARTIAI_AGENT_MAX_ITERS", "16"))
MAX_TOKENS = int(os.environ.get("MARTIAI_AGENT_MAX_TOKENS", "4096"))

# Odhad ceny (USD/Mtok) — sonnet-ish; ladit dle reality.
IN_USD_PER_MTOK = float(os.environ.get("MARTIAI_AGENT_IN_USD", "3.0"))
OUT_USD_PER_MTOK = float(os.environ.get("MARTIAI_AGENT_OUT_USD", "15.0"))
USD_TO_CZK = float(os.environ.get("USD_CZK", "23.5"))

PER_RUN_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_PER_RUN_CZK", "60"))
DAILY_CZK_CAP = float(os.environ.get("MARTIAI_AGENT_DAILY_CZK", "600"))

_flag_cache = {"val": False, "ts": 0.0}
_FLAG_TTL = 15.0


# ── Vypínač (g2007.nastaveni, přepíná rodič přes menu/most) ──────────────────────
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


# ── Read-only nástroje nad repem (sandbox na REPO_ROOT) ──────────────────────────
def _safe_path(rel: str) -> str:
    root = os.path.realpath(REPO_ROOT)
    full = os.path.realpath(os.path.join(root, rel))
    if not (full == root or full.startswith(root + os.sep)):
        raise ValueError(f"cesta mimo repo: {rel}")
    return full


_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "backups", ".pytest_cache"}


def _tool_repo_read(args: dict) -> str:
    rel = (args.get("path") or "").strip()
    full = _safe_path(rel)
    if not os.path.isfile(full):
        return f"[soubor neexistuje: {rel}]"
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        data = f.read(60000)
    return data or "[prázdný soubor]"


def _tool_repo_list(args: dict) -> str:
    rel = (args.get("path") or ".").strip()
    base = _safe_path(rel)
    pat = args.get("glob")
    out = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name in _SKIP_DIRS:
                continue
            p = os.path.join(base, name)
            tag = "/" if os.path.isdir(p) else ""
            if not pat or re.search(pat.replace("*", ".*"), name):
                out.append(name + tag)
    else:
        return f"[není adresář: {rel}]"
    return "\n".join(out[:400]) or "[prázdný adresář]"


def _tool_repo_grep(args: dict) -> str:
    pattern = args.get("pattern") or ""
    rel = (args.get("path") or ".").strip()
    base = _safe_path(rel)
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"[neplatný regex: {e}]"
    hits = []
    root = os.path.realpath(REPO_ROOT)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith((".py", ".js", ".html", ".md", ".sql", ".txt", ".json", ".css", ".kt")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            rp = os.path.relpath(fp, root).replace(os.sep, "/")
                            hits.append(f"{rp}:{i}: {line.strip()[:200]}")
                            if len(hits) >= 200:
                                return "\n".join(hits) + "\n[… oříznuto na 200]"
            except Exception:
                continue
    return "\n".join(hits) or "[žádná shoda]"


TOOLS_SPEC = [
    {"name": "repo_read", "description": "Přečti soubor z repa (relativní cesta). Read-only.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "repo_list", "description": "Vypiš obsah adresáře v repu (volitelně glob). Read-only.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "glob": {"type": "string"}}}},
    {"name": "repo_grep", "description": "Hledej regex v repu (volitelně podadresář path). Read-only.",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}},
]
_TOOL_FUNCS = {"repo_read": _tool_repo_read, "repo_list": _tool_repo_list, "repo_grep": _tool_repo_grep}


# ── Rozpočet + audit ─────────────────────────────────────────────────────────────
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
                    "iters": result.get("iters"), "reply_len": len(result.get("reply") or ""),
                }, ensure_ascii=False)})
            sg.commit()
        finally:
            sg.close()
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT audit failed: {e}")


def _her_system_prompt(conversation_id: Optional[int]) -> Optional[str]:
    try:
        from modules.conversation.application.composer import build_prompt
        sp, _msgs = build_prompt(conversation_id or 0)
        return sp
    except Exception as e:
        logger.warning(f"MARTIAI_AGENT: composer.build_prompt selhal ({e})")
        return None


# ── Vlastní agentí smyčka (Messages API tool-use) ────────────────────────────────
def _run_loop(goal: str, conversation_id: Optional[int]) -> dict:
    import anthropic
    from core.config import settings
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    sp = _her_system_prompt(conversation_id)
    agent_note = ("\n\n[AGENTÍ REŽIM: běžíš jako autonomní agent. Máš read-only nástroje "
                  "repo_read/repo_list/repo_grep nad repem. Splň cíl: prozkoumej co potřebuješ "
                  "a vrať jasný výsledek. Až budeš hotová, napiš finální odpověď bez volání nástroje.]")
    system = (sp + agent_note) if sp else agent_note.strip()

    messages = [{"role": "user", "content": goal}]
    in_tok = out_tok = 0
    iters = 0
    final_text = ""
    while iters < MAX_ITERS:
        iters += 1
        resp = client.messages.create(
            model=DEFAULT_MODEL, max_tokens=MAX_TOKENS, system=system,
            messages=messages, tools=TOOLS_SPEC,
        )
        in_tok += getattr(resp.usage, "input_tokens", 0) or 0
        out_tok += getattr(resp.usage, "output_tokens", 0) or 0
        # text bloky
        texts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if resp.stop_reason != "tool_use" or not tool_uses:
            final_text = "\n".join(texts).strip()
            break
        # proveď nástroje, vrať výsledky
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in tool_uses:
            try:
                out = _TOOL_FUNCS[tu.name](tu.input or {})
            except Exception as e:
                out = f"[chyba nástroje {tu.name}: {type(e).__name__}: {e}]"
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(out)[:60000]})
        messages.append({"role": "user", "content": results})

    cost_usd = round(in_tok / 1e6 * IN_USD_PER_MTOK + out_tok / 1e6 * OUT_USD_PER_MTOK, 4)
    return {
        "ok": bool(final_text), "reply": final_text or "[agent nevrátil finální text]",
        "input_tokens": in_tok, "output_tokens": out_tok,
        "cost_usd": cost_usd, "cost_czk": round(cost_usd * USD_TO_CZK, 2), "iters": iters,
    }


def run_goal(goal: str, requested_by_user_id: Optional[int] = None,
             conversation_id: Optional[int] = None, allowed_tools: Optional[list] = None) -> dict:
    """Marti-AI dostane CÍL a proběhne ho vlastní agentí smyčkou (Fáze 0 read-only)."""
    if not _enabled():
        return {"ok": False, "error": "martiai_agent vypnutý (g2007.nastaveni martiai_agent_enabled)", "reason": "disabled"}
    if not goal or not goal.strip():
        return {"ok": False, "error": "prázdný cíl", "reason": "empty_goal"}
    spent = _spent_today_czk()
    if spent >= DAILY_CZK_CAP:
        return {"ok": False, "error": f"denní rozpočet vyčerpán ({spent:.0f}/{DAILY_CZK_CAP:.0f} Kč)", "reason": "daily_budget"}

    t0 = time.monotonic()
    try:
        result = _run_loop(goal, conversation_id)
    except ImportError as e:
        return {"ok": False, "error": f"anthropic balík není: {e}", "reason": "anthropic_missing"}
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT run failed: {e}")
        result = {"ok": False, "error": f"{type(e).__name__}: {e}", "reason": "run_failed"}
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    if result.get("cost_czk", 0) > PER_RUN_CZK_CAP:
        logger.warning(f"MARTIAI_AGENT: běh přesáhl per-run cap ({result['cost_czk']} > {PER_RUN_CZK_CAP} Kč)")
        result["over_per_run_cap"] = True
    _audit_run(requested_by_user_id, goal, result)
    return result
