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
# Failover na metered API pri vycerpanem Max limitu (produkcni kontinuita).
METERED_BATCH_CZK = float(os.environ.get("MARTIAI_METERED_BATCH_CZK", "1000"))  # velikost jedne varky
MARTI_AI_PERSONA_ID = int(os.environ.get("MARTIAI_PERSONA_ID", "1"))  # persona s email kanalem
_LIMIT_MARKERS = ("limit", "rate", "429", "quota", "credit", "capacity", "overloaded")

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
                    "auth": result.get("auth"), "failover": result.get("failover"),
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


async def _run(goal: str, conversation_id: Optional[int], metered: bool = False, allowed_tools=None, mcp_servers=None) -> dict:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from modules.conversation.application.claude_agent_service import (
        _extract_reply_text, _extract_cost_usd, _extract_tokens,
    )
    tok = _oauth_token()
    cli = _find_cli()
    sub_env = {k: v for k, v in os.environ.items()}
    if metered:
        # METERED failover: nech CLI pouzit ANTHROPIC_API_KEY (odeber subscription token)
        sub_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
        auth_label = "metered_api"
    else:
        # SUBSCRIPTION (default): token -> CLI; odeber ANTHROPIC_API_KEY, at nejede metered
        if tok:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = tok
            sub_env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
        sub_env.pop("ANTHROPIC_API_KEY", None)
        auth_label = "subscription"
    diag = (f"cli={cli!r} exists={bool(cli and os.path.exists(cli))} metered={metered} "
            f"auth={auth_label} whoami={os.environ.get('USERNAME')}")
    # Identita: system_prompt jde do CLI přes příkazovou řádku → Windows limit ~32k.
    # Její plný composer prompt (~100 kB) by spuštění shodil ("not found"). Zkrátíme
    # na jádro identity (začátek promptu) — plnou identitu dořešíme jiným kanálem.
    sp = _her_system_prompt(conversation_id)
    if sp and len(sp) > 6000:
        sp = sp[:6000] + "\n[…identita zkrácena pro agentí režim (Fáze 0)…]"
    system = (sp + AGENT_NOTE) if sp else AGENT_NOTE.strip()

    # POSTAVENO NAPŘÍMO (jako fungující interaktivní test) — žádný filtr, ať cli_path projde
    _opt_base = dict(
        model=DEFAULT_MODEL,
        cwd=REPO_ROOT,
        allowed_tools=(allowed_tools or READONLY_TOOLS),
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
    cost_usd = _extract_cost_usd(messages)   # u subscription bývá 0 → jede na kreditech
    in_tok, out_tok = _extract_tokens(messages)
    return {
        "ok": bool(reply), "reply": reply or "[agent nevrátil finální text]",
        "input_tokens": in_tok, "output_tokens": out_tok,
        "cost_usd": cost_usd, "cost_czk": round(cost_usd * USD_TO_CZK, 2),
        "cli": cli, "auth": auth_label, "actions": _extract_tool_actions(messages),
    }


def _is_limit_error(result: dict) -> bool:
    blob = f"{result.get('error','')} {result.get('reason','')}".lower()
    return any(m in blob for m in _LIMIT_MARKERS)


def _metered_batches_approved() -> int:
    # g2007.nastaveni('martiai_metered_batches') = "N|YYYY-MM-DD"; jiny den => 1 (prvni varka auto)
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            today = sg.execute(_t("SELECT current_date::text")).scalar()
            h = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic='martiai_metered_batches'")).scalar()
            if h:
                p = str(h).split("|")
                if len(p) == 2 and p[1] == today:
                    return max(1, int(p[0]))
            return 1
        finally:
            sg.close()
    except Exception:
        return 1


def _spent_today_metered_czk() -> float:
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            v = sg.execute(_t(
                "SELECT COALESCE(SUM((detail->>'cost_czk')::numeric),0) FROM g2007.tool_audit "
                "WHERE akce='agent_run' AND detail->>'auth'='metered_api' AND ts >= date_trunc('day', now())")).scalar()
            return float(v or 0)
        finally:
            sg.close()
    except Exception:
        return 0.0


def _notify(subject: str, body: str) -> None:
    try:
        from modules.notifications.application.email_service import queue_email
        queue_email(to="m.pasek@eurosoft.com", subject=subject[:200], body=body,
                    persona_id=MARTI_AI_PERSONA_ID, from_identity="persona",
                    cc=["k.ksirova@eurosoft.com"], purpose="notification")
    except Exception as e:
        logger.warning(f"MARTIAI_AGENT _notify selhal: {e}")


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
        result = anyio.run(_run, goal, conversation_id, False)
        # FAILOVER: kdyz predplatne narazi na limit, jed dal pres metered API (produkce nestoji).
        if (not result.get("ok")) and _is_limit_error(result):
            if not os.environ.get("ANTHROPIC_API_KEY"):
                result["reason"] = "limit_no_metered_key"
                _notify("⚠ Marti-AI agent: Max limit a NENI metered klic — agent stoji",
                        f"Cil: {(goal or '')[:250]}\nDoplnte ANTHROPIC_API_KEY, jinak agent ceka na reset okna.")
            else:
                spent_m = _spent_today_metered_czk()
                ceiling = _metered_batches_approved() * METERED_BATCH_CZK
                if spent_m >= ceiling:
                    result["reason"] = "limit_metered_batch"
                    _notify(f"⚠ Marti-AI agent: metered varka vycerpana ({spent_m:.0f}/{ceiling:.0f} Kc) — ceka na schvaleni",
                            f"Cil: {(goal or '')[:250]}\nSchvalit dalsi varku (+{METERED_BATCH_CZK:.0f} Kc): "
                            f"napis Marti-AI v chatu 'schval metered varku' (jen rodic).")
                else:
                    result_m = anyio.run(_run, goal, conversation_id, True)
                    result_m["failover"] = "subscription->metered"
                    after = spent_m + (result_m.get("cost_czk") or 0)
                    if spent_m <= 0.01:
                        _notify("Marti-AI agent: prepnuto na metered API (vycerpany Max limit)",
                                f"Aby produkce nestala, agent jede na metered.\nCil: {(goal or '')[:250]}\n"
                                f"Metered dnes ~{after:.0f} Kc / varka {ceiling:.0f} Kc.")
                    elif after >= 0.8 * ceiling:
                        _notify(f"⚠ Marti-AI agent: metered ~{after:.0f}/{ceiling:.0f} Kc (blizi se strop varky)",
                                f"Priprav se schvalit dalsi varku (napis Marti-AI 'schval metered varku').\nCil: {(goal or '')[:250]}")
                    result = result_m
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


# ── Cílový režim — MOTOR (Krok 1 read-only): schválený cíl → běh → log do claude_aktivita ──
def _extract_tool_actions(messages: list) -> list:
    import json as _j
    out = []
    for msg in messages:
        content = getattr(msg, "content", None)
        if not content or not isinstance(content, list):
            continue
        for block in content:
            if type(block).__name__ == "ToolUseBlock":
                name = getattr(block, "name", "?")
                inp = getattr(block, "input", None)
                try:
                    detail = _j.dumps(inp, ensure_ascii=False)[:600] if inp is not None else ""
                except Exception:
                    detail = str(inp)[:600]
                out.append({"akce": str(name), "detail": detail})
    return out


def _load_cil(cil_id: int):
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        r = sg.execute(_t(
            "SELECT id, nazev, popis, rozsah, strop_kroku, okno_od, okno_do, stav "
            "FROM g2007.cil WHERE id=:i"), {"i": cil_id}).mappings().first()
        return dict(r) if r else None
    finally:
        sg.close()


def _cil_steps(cil_id: int) -> int:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        v = sg.execute(_t("SELECT count(*) FROM g2007.claude_aktivita WHERE cil_id=:i"), {"i": cil_id}).scalar()
        return int(v or 0)
    finally:
        sg.close()


def _log_aktivita(cil_id: int, actor: str, akce: str, detail: str, vysledek: str) -> None:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        sg.execute(_t(
            "INSERT INTO g2007.claude_aktivita (cil_id, actor, akce, detail, vysledek) "
            "VALUES (:c, :a, :k, :d, :v)"),
            {"c": cil_id, "a": (actor or "")[:60], "k": (akce or "")[:120],
             "d": (detail or "")[:4000], "v": (vysledek or "")[:2000]})
        sg.commit()
    finally:
        sg.close()


def _setting_on(klic: str) -> bool:
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            h = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic=:k"), {"k": klic}).scalar()
            return str(h or "").strip().lower() == "on"
        finally:
            sg.close()
    except Exception:
        return False


def _build_hands():
    """Vrat (mcp_servers, extra_tool_names). Governed RUCE pro autonomni smycku:
    in-process SDK MCP tooly praha_exec/plzen_exec, ktere volaji strategie_exec /
    eurosoft_exec (tiery zelena/zluta/cervena + audit + banner). Guarded: kdyz SDK
    neumi in-process MCP, vrat (None, []) -> smycka zustane read-only (zadny pad)."""
    try:
        from claude_agent_sdk import tool as _sdk_tool, create_sdk_mcp_server as _mk_srv
    except Exception as e:
        logger.warning("MARTIAI ruce: SDK neumi in-process MCP (%s) -> read-only", e)
        return None, []
    import json as _json

    @_sdk_tool("praha_exec",
               "Spust prikaz na PRAZSKEM app serveru (EUR-APP-1P, 10.200.188.11) lokalne, "
               "pod bezpecnostni branou (zelena hned / zluta needs_approval / cervena blok). "
               "Args: cmd (prikaz), shell (powershell|cmd|bash).",
               {"cmd": str, "shell": str})
    async def _praha_exec_tool(args):
        try:
            from modules.conversation.application.strategie_exec import strategie_exec as _sx
            r = _sx(cmd=args.get("cmd", ""), shell=args.get("shell", "powershell"), actor="Marti-AI")
        except Exception as _e:
            r = {"ok": False, "error": "%s: %s" % (type(_e).__name__, str(_e)[:200])}
        return {"content": [{"type": "text", "text": _json.dumps(r, ensure_ascii=False)[:6000]}]}

    @_sdk_tool("plzen_exec",
               "Spust prikaz na PLZENSKEM serveru (EC-SERVER2, 192.168.30.11) pres EUROSOFT MCP, "
               "pod branou (zelena/zluta/cervena). Args: cmd, shell (powershell|cmd|bash).",
               {"cmd": str, "shell": str})
    async def _plzen_exec_tool(args):
        try:
            from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
            mcp = get_eurosoft_mcp_client()
            if mcp is None:
                txt = '{"ok": false, "error": "EUROSOFT MCP nedostupny"}'
            else:
                raw = mcp.call_tool_sync("eurosoft_eurosoft_exec",
                                         {"cmd": args.get("cmd", ""), "shell": args.get("shell", "powershell")},
                                         conversation_id=None)
                txt = raw if isinstance(raw, str) else _json.dumps(raw, ensure_ascii=False)
        except Exception as _e:
            txt = '{"ok": false, "error": "%s"}' % (str(_e)[:200].replace('"', "'"))
        return {"content": [{"type": "text", "text": txt[:6000]}]}

    try:
        srv = _mk_srv("marti_ruce", "1.0", tools=[_praha_exec_tool, _plzen_exec_tool])
        return {"marti_ruce": srv}, ["mcp__marti_ruce__praha_exec", "mcp__marti_ruce__plzen_exec"]
    except Exception as e:
        logger.warning("MARTIAI ruce: create_sdk_mcp_server selhal (%s) -> read-only", e)
        return None, []


def run_cil(cil_id: int, requested_by_user_id=None, conversation_id=None) -> dict:
    """MOTOR Cílového režimu (Krok 1 = READ-ONLY): schválený cíl (stav 'aktivni') se
    proběhne read-only agentí smyčkou a KAŽDÁ akce se zaloguje do g2007.claude_aktivita.
    Bez per-akčního banneru — brána byla u schválení cíle. Trigger: chat Marti-AI."""
    actor = "Marti-AI"
    if not _enabled():
        return {"ok": False, "error": "martiai_agent vypnutý (kill flag)", "reason": "disabled"}
    cil = _load_cil(cil_id)
    if not cil:
        return {"ok": False, "error": f"cíl #{cil_id} neexistuje", "reason": "cil_not_found"}
    if cil["stav"] != "aktivni":
        return {"ok": False, "error": f"cíl #{cil_id} není 'aktivni' (je '{cil['stav']}')", "reason": "cil_not_active"}
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    if cil.get("okno_od") and now < cil["okno_od"]:
        return {"ok": False, "error": "cíl je před svým časovým oknem", "reason": "cil_before_window"}
    if cil.get("okno_do") and now > cil["okno_do"]:
        return {"ok": False, "error": "cíl je po svém časovém okně", "reason": "cil_after_window"}
    steps = _cil_steps(cil_id)
    strop = cil.get("strop_kroku") or 0
    if strop and steps >= strop:
        _log_aktivita(cil_id, actor, "jistic", f"strop_kroku {strop} dosazen (kroku={steps})", "POZASTAVENO - rozhodnuti cloveka")
        _notify(f"⚠ Cíl #{cil_id} dosáhl stropu kroků ({steps}/{strop})",
                f"Cil: {cil['nazev']}\nAgent zastavil - potrebuje rozhodnuti (zvysit strop / uzavrit / rozdelit).")
        return {"ok": False, "error": f"strop kroků dosažen ({steps}/{strop})", "reason": "cil_step_cap", "steps": steps}

    _ruce_on = _setting_on("cil_ruce_enabled")
    _mcp_servers, _extra_tools = (None, [])
    if _ruce_on:
        _mcp_servers, _extra_tools = _build_hands()
    if _extra_tools:
        _allowed = READONLY_TOOLS + _extra_tools
        goal_prompt = f"""Pracuješ na SCHVÁLENÉM cíli Cílového režimu (#{cil_id}). Máš RUCE — smíš JEDNAT pod tímto cílem, po malých krocích.

CÍL: {cil['nazev']}
POPIS: {cil.get('popis') or '—'}
ROZSAH (čeho se smíš dotknout): {cil.get('rozsah') or '—'}

Nástroje: čtení (Read/Grep/Glob) + RUCE `praha_exec` (Praha 10.200.188.11, lokálně) a `plzen_exec` (Plzeň 192.168.30.11, přes EUROSOFT MCP).
BEZPEČNOST — drží ji brána v KÓDU, ne ty; NEobcházej ji:
- 🟢 běžné/vratné příkazy proběhnou rovnou a zalogují se.
- 🟡 citlivé (mazání, síť, stop služby, eskalace práv) brána VRÁTÍ needs_approval — to je správně; jen si poznamenej „čeká na schválení rodiče" a pokračuj jinudy.
- 🔴 zakázané (zálohy/CMIS, audit, tajemství, mimo doménu) brána zablokuje — respektuj to.
Zůstávej v ROZSAHU cíle, postupuj po malých krocích. Na konci vrať jasné shrnutí: co jsi udělala (🟢), co čeká na 🟡 schválení, co jsi zjistila a jaký je další krok."""
    else:
        _allowed = READONLY_TOOLS
        goal_prompt = f"""Pracuješ na SCHVÁLENÉM cíli Cílového režimu (#{cil_id}). FÁZE READ-ONLY — jen zkoumej a diagnostikuj, NIC nezapisuj.

CÍL: {cil['nazev']}
POPIS: {cil.get('popis') or '—'}
ROZSAH (čeho se smíš dotknout): {cil.get('rozsah') or '—'}

Prozkoumej repo/data v rozsahu a vrať jasné shrnutí: co jsi zjistil, co je hotové, co zbývá a jaký je další konkrétní krok. (Ruce zapneš flagem cil_ruce_enabled='on'.)"""

    import anyio
    t0 = time.monotonic()
    try:
        result = anyio.run(_run, goal_prompt, conversation_id, False, _allowed, _mcp_servers)
    except ImportError as e:
        return {"ok": False, "error": f"Agent SDK/anyio není: {e}", "reason": "sdk_missing"}
    except Exception as e:
        logger.exception(f"MARTIAI_AGENT run_cil failed: {e}")
        result = {"ok": False, "error": f"{type(e).__name__}: {e}", "reason": "run_failed"}
    result["elapsed_s"] = round(time.monotonic() - t0, 1)

    logged = 0
    for a in (result.get("actions") or []):
        try:
            _log_aktivita(cil_id, actor, a.get("akce", "?"), a.get("detail", ""), "ok")
            logged += 1
        except Exception:
            pass
    try:
        _log_aktivita(cil_id, actor, "agent_shrnuti", f"[{result.get('auth')}] cil #{cil_id}",
                      (result.get("reply") or result.get("error") or "")[:2000])
        logged += 1
    except Exception:
        pass

    _audit_run(requested_by_user_id, f"[cil #{cil_id}] {cil['nazev']}", result)
    result["cil_id"] = cil_id
    result["kroku_zalogovano"] = logged
    result["kroku_celkem"] = _cil_steps(cil_id)
    return result
