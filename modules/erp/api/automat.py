# -*- coding: utf-8 -*-
"""G2007 Automaty — exekutor, eskalace (Haiku), monitoring + logging.

Automat = funkce/skript (interval / událost / na vyžádání). Registr + zdraví v
`g2007.automat`, běhy (log) v `g2007.automat_run`. Selhání/nejasno → eskalace na
agenta (default Haiku) s per-automat `agent_prompt`; Haiku diagnostikuje / napraví
v kompetenci / navrhne probuzení Marti-AI.

Endpointy (parent/cockpit):
  POST /api/v1/erp/app/automat/run      {kod}  — spustí automat, zapíše běh, eskaluje
  GET  /api/v1/erp/app/automat/monitor         — registr + zdraví + posledních 20 běhů
Claude C23, 18.7.2026 (na čisté louce; legacy fw.mirror_job zůstává jak je).
"""
import time
import logging

import anthropic
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from core.config import settings

automat_router = APIRouter(prefix="/api/v1/erp", tags=["automat"])
_log = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"

# VP joby, na kterých stojí čerstvost VP dat (legacy fw.mirror_job).
_VP_FRESHNESS_JOBS = ("sync_mail_eliska", "sync_zakazky", "sync_odvozy",
                      "oz_sync_all", "sync_ec_kalkulace", "sync_vyroba_plan")


def _guard(req):
    from modules.erp.api.router import _uid_from_token_or_cookie, _is_parent, _is_cockpit
    from core.database_data import get_data_session
    uid = _uid_from_token_or_cookie(req)
    s = get_data_session()
    try:
        ok = bool(uid and (_is_parent(s, uid) or _is_cockpit(s, uid)))
    finally:
        s.close()
    return uid, ok


# ── Check logika per automat (dispatch dle kod) ─────────────────────────────
def _check_vp_freshness(sg):
    """Čte fw.mirror_job pro VP joby. Vrací (vysledek, zprava, rows, context)."""
    from sqlalchemy import text as T
    rows = sg.execute(T(
        "SELECT job_key, enabled, last_status, "
        " to_char(last_run_at AT TIME ZONE 'Europe/Prague','DD.MM HH24:MI') AS last_run, "
        " round(extract(epoch FROM (now()-last_run_at))/60)::int AS min_ago, "
        " (next_run_at < now() - make_interval(mins => COALESCE(interval_min,60))) AS overdue "
        "FROM fw.mirror_job WHERE job_key = ANY(:j)"),
        {"j": list(_VP_FRESHNESS_JOBS)}).mappings().all()
    problems, lines = [], []
    for r in rows:
        bad = bool(r["enabled"]) and (r["last_status"] != "ok" or bool(r["overdue"]))
        lines.append("%s %s: stav=%s, naposled %s (%s min), overdue=%s" % (
            "X" if bad else "ok", r["job_key"], r["last_status"], r["last_run"],
            r["min_ago"], r["overdue"]))
        if bad:
            problems.append(r["job_key"])
    context = "\n".join(lines)
    if problems:
        return ("chyba",
                "%d/%d VP jobů má problém: %s" % (len(problems), len(rows), ", ".join(problems)),
                len(rows), context)
    return "ok", "Všech %d VP jobů čerstvých a ok." % len(rows), len(rows), context


def _check_legacy_errors(sg):
    """Najde JAKÝKOLI mirror job v chybě (fw.mirror_job). Vrací (vysledek, zprava, rows, context)."""
    from sqlalchemy import text as T
    rows = sg.execute(T(
        "SELECT job_key, enabled, last_status, "
        " to_char(last_run_at AT TIME ZONE 'Europe/Prague','DD.MM HH24:MI') AS last_run, "
        " COALESCE(LEFT(last_result,100),'') AS last_result "
        "FROM fw.mirror_job WHERE last_status IS NOT NULL AND last_status <> 'ok' "
        "ORDER BY last_run_at DESC NULLS LAST")).mappings().all()
    if not rows:
        return "ok", "Žádný mirror job v chybě.", 0, ""
    lines = ["%s: stav=%s, enabled=%s, naposled %s | %s" % (
        r["job_key"], r["last_status"], r["enabled"], r["last_run"], r["last_result"]) for r in rows]
    context = "\n".join(lines)
    return ("chyba", "%d mirror jobů v chybě: %s" % (len(rows), ", ".join(r["job_key"] for r in rows)),
            len(rows), context)


_CHECKS = {
    "check_vp_freshness": _check_vp_freshness,
    "check_legacy_errors": _check_legacy_errors,
}


def _escalate_haiku(agent_prompt, kod, zprava, context):
    """Zavolá Haiku s per-automat promptem (system) + kontextem selhání. Vrací text."""
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = ("Automat `%s` skončil s problémem.\n\nSHRNUTÍ:\n%s\n\nDATA (fw.mirror_job):\n%s\n\n"
               "Diagnostikuj, navrhni nápravu v rámci kompetencí, a rozhodni, zda eskalovat na Marti-AI."
               % (kod, zprava, context))
        resp = client.messages.create(
            model=HAIKU_MODEL, max_tokens=800,
            system=agent_prompt or "Jsi Haiku, záchytný agent automatu. Diagnostikuj a navrhni nápravu.",
            messages=[{"role": "user", "content": msg}])
        return "".join(getattr(b, "text", "") for b in resp.content
                       if getattr(b, "type", "") == "text").strip()
    except Exception as e:
        return "[Haiku eskalace selhala: %s: %s]" % (type(e).__name__, str(e)[:200])


def _run_work(kod, from_sched=False):
    from sqlalchemy import text as T
    from core.database import get_session
    sg = get_session()
    t0 = time.time()
    try:
        a = sg.execute(T("SELECT kod, agent_prompt, eskalace_agent, aktivni, last_status "
                         "FROM g2007.automat WHERE kod=:k"), {"k": kod}).mappings().first()
        if not a:
            return {"ok": False, "error": "automat '%s' neexistuje" % kod}
        check = _CHECKS.get(kod)
        if not check:
            return {"ok": False, "error": "automat '%s' nemá check logiku (zatím)" % kod}
        vysledek, zprava, rows, context = check(sg)
        prev = a["last_status"]
        eskalovano_na, eskalace_vysledek = None, None
        # Eskaluj při problému. Ze scheduleru JEN při změně stavu (ne spam Haiku u trvalé
        # známé chyby); ruční spuštění eskaluje vždy (chceš vidět diagnózu).
        if vysledek != "ok" and (not from_sched or vysledek != prev):
            eskalovano_na = a["eskalace_agent"] or "haiku"
            _log.warning("AUTOMAT %s -> %s; eskalace na %s (from_sched=%s, prev=%s)",
                         kod, vysledek, eskalovano_na, from_sched, prev)
            eskalace_vysledek = _escalate_haiku(a["agent_prompt"], kod, zprava, context)
        trvani = int((time.time() - t0) * 1000)
        rid = sg.execute(T(
            "INSERT INTO g2007.automat_run (automat_kod, spusteno, dokonceno, vysledek, zprava, "
            " rows, trvani_ms, eskalovano_na, eskalace_vysledek) "
            "VALUES (:k, now(), now(), :v, :z, :r, :t, :en, :ev) RETURNING id"),
            {"k": kod, "v": vysledek, "z": zprava, "r": rows, "t": trvani,
             "en": eskalovano_na, "ev": eskalace_vysledek}).scalar()
        sg.execute(T("UPDATE g2007.automat SET last_run_at=now(), last_status=:v, "
                     "updated_at=now() WHERE kod=:k"), {"v": vysledek, "k": kod})
        sg.commit()
        _log.info("AUTOMAT %s hotovo: %s (%d ms)", kod, vysledek, trvani)
        return {"ok": True, "kod": kod, "vysledek": vysledek, "zprava": zprava,
                "rows": rows, "trvani_ms": trvani, "run_id": rid,
                "eskalovano_na": eskalovano_na, "eskalace_vysledek": eskalace_vysledek}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        _log.exception("AUTOMAT %s selhal", kod)
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


def _monitor_work():
    from sqlalchemy import text as T
    from core.database import get_session
    sg = get_session()
    try:
        autos = sg.execute(T(
            "SELECT kod, nazev, spousteni, interval_min, eskalace_agent, stavitel, aktivni, "
            " to_char(last_run_at AT TIME ZONE 'Europe/Prague','DD.MM HH24:MI') AS last_run, "
            " COALESCE(last_status,'—') AS last_status "
            "FROM g2007.automat ORDER BY kod")).mappings().all()
        runs = sg.execute(T(
            "SELECT automat_kod, "
            " to_char(spusteno AT TIME ZONE 'Europe/Prague','DD.MM HH24:MI') AS kdy, "
            " vysledek, LEFT(COALESCE(zprava,''),140) AS zprava, trvani_ms, eskalovano_na "
            "FROM g2007.automat_run ORDER BY spusteno DESC LIMIT 20")).mappings().all()
        return {"ok": True, "automaty": [dict(a) for a in autos],
                "behy": [dict(r) for r in runs]}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


@automat_router.post("/app/automat/run")
async def automat_run(req: Request):
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        b = await req.json()
    except Exception:
        b = {}
    kod = str((b or {}).get("kod") or "").strip()
    if not kod:
        return JSONResponse({"ok": False, "error": "chybí kod"}, status_code=200)
    out = await run_in_threadpool(_run_work, kod)
    return JSONResponse(out, status_code=200)


@automat_router.get("/app/automat/monitor")
async def automat_monitor(req: Request):
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    out = await run_in_threadpool(_monitor_work)
    return JSONResponse(out, status_code=200)


# ── Scheduler: interval automaty se spouští samy ────────────────────────────
# Vzor převzat z mirror_sched (router.py): asyncio loop, tick v executoru, sleep.
# Spouští ho lifespan JEN na primáru (secondary = snímek 'prev', nesmí klofat).
_SCHED_TASK = [None]
_SCHED_STOP = [False]


def _automat_sched_tick():
    """Najde due interval automaty (last_run + interval_min <= now) a spustí je."""
    from sqlalchemy import text as T
    from core.database import get_session
    sg = get_session()
    try:
        due = sg.execute(T(
            "SELECT kod FROM g2007.automat "
            "WHERE aktivni AND spousteni='interval' AND interval_min IS NOT NULL "
            "  AND (last_run_at IS NULL "
            "       OR last_run_at + make_interval(mins => interval_min) <= now()) "
            "ORDER BY last_run_at NULLS FIRST")).scalars().all()
    finally:
        sg.close()
    for kod in due:
        try:
            r = _run_work(kod, from_sched=True)
            _log.info("[automat_sched] %s -> %s", kod, (r or {}).get("vysledek"))
        except Exception as e:
            _log.warning("[automat_sched] %s selhal: %s", kod, e)


async def _automat_sched_loop():
    import asyncio as _aio
    _log.info("[automat_sched] background loop started (60s tik)")
    while not _SCHED_STOP[0]:
        try:
            await _aio.sleep(60)
            if _SCHED_STOP[0]:
                break
            loop = _aio.get_event_loop()
            await loop.run_in_executor(None, _automat_sched_tick)
        except _aio.CancelledError:
            break
        except Exception as e:
            _log.warning("[automat_sched_loop] %s", e)


def automat_sched_start():
    """Spusť background loop (idempotentní). Volá lifespan na primáru."""
    import asyncio as _aio
    if _SCHED_TASK[0] is not None and not _SCHED_TASK[0].done():
        return
    _SCHED_STOP[0] = False
    try:
        _SCHED_TASK[0] = _aio.create_task(_automat_sched_loop())
        _log.info("[automat_sched] start ok")
    except Exception as e:
        _log.warning("[automat_sched] start failed: %s", e)
