# -*- coding: utf-8 -*-
"""G2007 Automaty — poschoďový eskalační žebřík + infra watchery (C23, #4).

Rozšiřuje `automat.py`, ANIŽ by sahalo na jeho jádro:
  • WATCHERS  — check funkce navíc (běh služeb, čerstvost záloh); automat.py je
    zaregistruje do svého `_CHECKS`.
  • escalovat() — žebřík **L0 automat → L1 Haiku → L2 Marti-AI → L3 člověk**.
    Výsledek se ukládá do stávajících sloupců `automat_run.eskalovano_na`
    a `eskalace_vysledek` (žádné nové DDL).

Pouze VOLÁ (needituje) zakázané jádro:
  strategie_exec (Praha, lokální subprocess), eurosoft_mcp_client (30.11 přes MCP),
  martiai_agent_service.run_goal (L2 = Marti-AI) / _notify (L3 = e-mail člověku).
Probe služeb/disku i restart NAŠÍ služby = tier 🟢 (rovnou + audit).

Claude C23, 27.7.2026.
"""
import logging

import anthropic

from core.config import settings

_log = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"

# NAŠE služby (restart NAŠÍ služby = 🟢). Praha = app server, 30.11 = Plzeň.
_OUR_SERVICES_PRAHA = ("STRATEGIE-API", "STRATEGIE-CLAUDE-SQL")
_OUR_SERVICES_3011 = ("EUROSOFT-MCP",)
_BACKUP_STALE_DNU = 2  # dump starší než tolik dnů = problém


# ── Volání exec (sync, oba tolerantní: při nedostupnosti vrací None) ─────────
def _praha_exec(cmd):
    """strategie_exec na pražském app serveru. Vrací dict {ok,rc,out,err,...} nebo None."""
    try:
        from modules.conversation.application.strategie_exec import strategie_exec
        return strategie_exec(cmd=cmd, shell="powershell")
    except Exception as e:  # noqa: BLE001
        _log.warning("automat_eskalace praha_exec selhal: %s", e)
        return None


def _plzen_exec(cmd):
    """eurosoft_exec na 30.11 přes MCP klienta. Vrací dict (parsed) nebo None."""
    try:
        import json as _json
        from modules.conversation.application.eurosoft_mcp_client import (
            get_eurosoft_mcp_client,
        )
        c = get_eurosoft_mcp_client()
        if c is None:
            return None
        r = c.call_tool_sync("eurosoft_exec", {"cmd": cmd, "shell": "powershell"},
                             conversation_id=None)
        return _json.loads(r) if isinstance(r, str) else r
    except Exception as e:  # noqa: BLE001
        _log.warning("automat_eskalace plzen_exec selhal: %s", e)
        return None


def _svc_probe(exec_fn, pattern):
    """Get-Service <pattern> → {name: status_str}. Vrací (dict, None) nebo (None, err)."""
    import json as _json
    cmd = ("Get-Service %s -ErrorAction SilentlyContinue | "
           "Select-Object Name,@{N='St';E={\"$($_.Status)\"}} | "
           "ConvertTo-Json -Compress") % pattern
    r = exec_fn(cmd)
    if not r or not r.get("ok"):
        return None, ((r or {}).get("err") or (r or {}).get("error") or "probe nedostupný")
    txt = (r.get("out") or "").strip()
    if not txt:
        return {}, None
    try:
        data = _json.loads(txt)
    except Exception:  # noqa: BLE001
        return None, "nečitelný výstup Get-Service"
    if isinstance(data, dict):
        data = [data]
    svc = {}
    for d in data:
        if isinstance(d, dict) and d.get("Name"):
            svc[str(d["Name"])] = str(d.get("St") or d.get("Status") or "")
    return svc, None


# ── Watcher check funkce: (sg) -> (vysledek, zprava, rows, context) ─────────
def _check_service_down(sg):
    """Běží STRATEGIE* (Praha) a EUROSOFT-MCP (30.11)? Ne-Running = problém."""
    problems, lines, probed_any = [], [], False
    for label, exec_fn, pattern in (("Praha", _praha_exec, "STRATEGIE*"),
                                     ("30.11", _plzen_exec, "EUROSOFT-MCP")):
        svc, err = _svc_probe(exec_fn, pattern)
        if svc is None:
            lines.append("%s: probe nedostupný (%s)" % (label, err))
            continue
        probed_any = True
        if not svc:
            lines.append("%s: žádná služba dle vzoru %s" % (label, pattern))
            continue
        for nm, st in svc.items():
            ok = (st.lower() == "running")
            lines.append("%s %s/%s: %s" % ("ok" if ok else "X", label, nm, st))
            if not ok:
                problems.append("%s:%s(%s)" % (label, nm, st))
    context = "\n".join(lines)
    if problems:
        return ("chyba", "Služby ne-Running: %s" % ", ".join(problems),
                len(problems), context)
    if not probed_any:
        # Nic se nedalo sondovat (exec vypnutý/nedostupný) → nehlásíme planý poplach.
        return "ok", "Probe služeb nedostupný (exec off) — bez poplachu.", 0, context
    return "ok", "Všechny sledované služby běží.", 0, context


def _check_backup_freshness(sg):
    """Nejnovější dump v D:/STRATEGIE přes g2007.backup_freshness() (SECURITY DEFINER;\n    app role nema pg_read_server_files). Bez exec. Starý = problém."""
    from sqlalchemy import text as T
    try:
        row = sg.execute(T(
            "SELECT newest, stari FROM g2007.backup_freshness()"
        )).mappings().first()
    except Exception as e:  # noqa: BLE001  (watcher nesmi shodit runner)
        return ("ok", "Backup probe nedostupny (%s) - bez poplachu." % type(e).__name__,
                0, str(e)[:200])
    newest = row["newest"] if row else None
    stari = row["stari"] if row else None
    if newest is None:
        return ("chyba", "Žádný datovaný dump v D:/STRATEGIE.", 0,
                "backup_freshness bez datovaných složek")
    ctx = "nejnovější dump: %s (stáří %s dnů)" % (newest, stari)
    if stari is not None and stari > _BACKUP_STALE_DNU:
        return "chyba", "Záloha zastaralá: %s (%s dnů)" % (newest, stari), 1, ctx
    return "ok", "Záloha čerstvá: %s (%s dnů)." % (newest, stari), 1, ctx


WATCHERS = {
    "check_service_down": _check_service_down,
    "check_backup_freshness": _check_backup_freshness,
}


# ── L0: mechanická náprava (per-kod) ────────────────────────────────────────
def _remediate_service_down(kod, zprava, context, sg):
    """Restartuje NAŠI službu, která není Running (🟢), a znovu sonduje.
    Vrací (vyreseno: bool, detail: str)."""
    acted = []
    for exec_fn, names in ((_praha_exec, _OUR_SERVICES_PRAHA),
                           (_plzen_exec, _OUR_SERVICES_3011)):
        for nm in names:
            svc, _err = _svc_probe(exec_fn, nm)
            if svc and str(svc.get(nm, "")).lower() != "running":
                r = exec_fn("Restart-Service -Name '%s' -ErrorAction Stop; "
                            "\"restarted %s\"" % (nm, nm))
                acted.append("%s:%s" % (nm, "ok" if (r and r.get("ok")) else "restart_fail"))
    if not acted:
        return False, "L0: žádná NAŠE služba k restartu"
    vysledek2, zprava2, _r, _c = _check_service_down(sg)
    return (vysledek2 == "ok"), "L0 restart [%s] → re-probe: %s" % ("; ".join(acted), zprava2)


_L0 = {
    "check_service_down": _remediate_service_down,
}


# ── L1: Haiku (diagnostika + strojově čitelný verdikt) ──────────────────────
def _l1_haiku(agent_prompt, kod, zprava, context):
    """Vrací (text, eskalovat: bool). eskalovat=True když Haiku řekne ať jde výš
    (nebo když verdikt chybí — bezpečná strana)."""
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = ("Automat `%s` má problém.\n\nSHRNUTÍ:\n%s\n\nKONTEXT:\n%s\n\n"
               "Diagnostikuj a navrhni/proveď nápravu v rámci svých kompetencí. "
               "NAKONEC připoj přesně jeden token: [VERDIKT: VYRESENO] pokud je to "
               "vyřešené nebo neškodné, nebo [VERDIKT: ESKALOVAT] pokud to potřebuje "
               "Marti-AI nebo člověka." % (kod, zprava, context))
        resp = client.messages.create(
            model=HAIKU_MODEL, max_tokens=800,
            system=(agent_prompt or "Jsi Haiku, první záchytný agent automatu. "
                    "Diagnostikuj a navrhni nápravu."),
            messages=[{"role": "user", "content": msg}])
        text = "".join(getattr(b, "text", "") for b in resp.content
                       if getattr(b, "type", "") == "text").strip()
        up = text.upper()
        eskalovat = ("[VERDIKT: ESKALOVAT]" in up) or ("[VERDIKT: VYRESENO]" not in up)
        return text, eskalovat
    except Exception as e:  # noqa: BLE001
        return "[Haiku selhala: %s: %s]" % (type(e).__name__, str(e)[:200]), True


# ── L2: Marti-AI (sankcionovaný run_goal; degraduje na L3 když je agent off) ─
def _l2_marti_ai(kod, zprava, context, haiku_text):
    """Vrací (vyreseno: bool, souhrn: str)."""
    try:
        from modules.conversation.application.martiai_agent_service import run_goal
        goal = ("Automat `%s` hlásí problém, který L0 ani Haiku (L1) nevyřešily.\n"
                "Problém: %s\n\nKontext:\n%s\n\nHaiku diagnóza:\n%s\n\n"
                "Diagnostikuj a naprav v rámci svých kompetencí (exec pod cílem, 🟢 "
                "rovnou). Pokud to vyžaduje rozhodnutí člověka, řekni to jasně."
                % (kod, zprava, context, (haiku_text or "")[:1500]))
        r = run_goal(goal=goal, requested_by_user_id=None) or {}
        ok = bool(r.get("ok"))
        summ = (r.get("summary") or r.get("result") or r.get("error")
                or r.get("reason") or str(r))
        return ok, str(summ)[:1500]
    except Exception as e:  # noqa: BLE001
        return False, "[Marti-AI eskalace selhala: %s: %s]" % (type(e).__name__, str(e)[:200])


# ── L3: člověk (e-mail Martimu + cc Kristý přes Marti-AI notify) ────────────
def _l3_clovek(kod, zprava, context, haiku_text, marti_text):
    try:
        from modules.conversation.application.martiai_agent_service import _notify
        _notify("🤖 Automat %s — eskalace na člověka" % kod,
                "Automat `%s` selhal a nevyřešil to ani L0/L1/L2.\n\n"
                "Problém: %s\n\nKontext:\n%s\n\nHaiku (L1):\n%s\n\nMarti-AI (L2):\n%s"
                % (kod, zprava, context, (haiku_text or "")[:800], (marti_text or "")[:800]))
        return "L3 člověk: e-mail odeslán (m.pasek + k.ksirova)"
    except Exception as e:  # noqa: BLE001
        return "L3 notify selhal: %s: %s" % (type(e).__name__, str(e)[:200])


def escalovat(kod, vysledek, zprava, context, agent_prompt=None, sg=None,
              from_sched=False):
    """Poschoďový žebřík. Vrací (eskalovano_na, eskalace_vysledek) pro automat_run.

    L0 automat → L1 Haiku → L2 Marti-AI → L3 člověk. Zastaví se na první vrstvě,
    která problém vyřeší; jinak jede výš. Nikdy nesmí shodit volajícího."""
    trace = []

    # L0 — mechanická náprava (jen automaty, které ji mají definovanou)
    l0 = _L0.get(kod)
    if l0 is not None and sg is not None:
        try:
            fixed, detail = l0(kod, zprava, context, sg)
            trace.append(detail)
            if fixed:
                return "L0-automat", " || ".join(trace)
        except Exception as e:  # noqa: BLE001
            trace.append("L0 chyba: %s: %s" % (type(e).__name__, str(e)[:200]))

    # L1 — Haiku
    haiku_text, jdi_vys = _l1_haiku(agent_prompt, kod, zprava, context)
    trace.append("L1 Haiku: " + (haiku_text or "")[:700])
    if not jdi_vys:
        return "haiku", " || ".join(trace)

    # L2 — Marti-AI
    ok2, marti_text = _l2_marti_ai(kod, zprava, context, haiku_text)
    trace.append("L2 Marti-AI: " + (marti_text or "")[:700])
    if ok2:
        return "marti-ai", " || ".join(trace)

    # L3 — člověk
    trace.append(_l3_clovek(kod, zprava, context, haiku_text, marti_text))
    return "clovek", " || ".join(trace)
