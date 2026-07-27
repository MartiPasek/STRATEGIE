# -*- coding: utf-8 -*-
"""Žlutý banner — API schvalovacího toku pro rizikový `eurosoft_exec` (#3).

Roadmapa `doc-marti-ai-produkce-roadmap` #3. Cowork instance B, 27.7.2026.

Samostatný router (vzor automat.py / iso_cockpit.py) → registruje se v apps/api/main.py.
NESAHÁ na modules/erp/api/router.py (zámek C26). Auth helpery si jen importuje.

Endpointy (VŠECHNY parent-only — tvrdé pravidlo #3: schválení = lidský tap, ne nástroj):
  GET  /api/v1/erp/app/exec_approval          — seznam čekajících žádostí (banner)
  GET  /api/v1/erp/app/exec_approval/count    — počet čekajících (badge dlaždice)
  POST /api/v1/erp/app/exec_approval/{aid}/schvalit   — palec ✅ → provedení příkazu
  POST /api/v1/erp/app/exec_approval/{aid}/zamitnout  — palec ⛔

Marti-AI NEMÁ tenhle router jako nástroj a neprojde parent guardem → nemůže se
schválit sama.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

exec_approval_router = APIRouter(prefix="/api/v1/erp", tags=["exec-approval"])
_log = logging.getLogger(__name__)


def _parent(req: Request):
    """Vrátí (uid, je_rodic). Bearer token (nativní appka) i cookie (web)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from modules.thoughts.application.service import is_marti_parent
    uid = _uid_from_token_or_cookie(req)
    return uid, bool(uid and is_marti_parent(uid))


@exec_approval_router.get("/app/exec_approval")
async def exec_approval_list(req: Request) -> JSONResponse:
    """Seznam čekajících žádostí o schválení příkazu (banner). Jen rodič.
    Před výpisem materializuje čerstvé needs_approval z auditu (fw.ops_request)."""
    uid, ok = _parent(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "Nepřihlášen"}, status_code=401)
    if not ok:
        return JSONResponse({"ok": False, "error": "Jen rodič může schvalovat příkazy."}, status_code=403)
    from modules.eurosoft_mcp import exec_approval as ea
    try:
        await run_in_threadpool(ea.materialize_from_ops_request)
        items = await run_in_threadpool(ea.list_pending)
        return JSONResponse({"ok": True, "zadosti": items})
    except Exception as exc:
        _log.exception("[exec_approval_list] %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@exec_approval_router.get("/app/exec_approval/count")
async def exec_approval_count(req: Request) -> JSONResponse:
    """Počet čekajících (pro badge na dlaždici). Jen rodič."""
    uid, ok = _parent(req)
    if not uid or not ok:
        return JSONResponse({"ok": True, "count": 0})
    from modules.eurosoft_mcp import exec_approval as ea
    try:
        await run_in_threadpool(ea.materialize_from_ops_request)
        items = await run_in_threadpool(ea.list_pending)
        return JSONResponse({"ok": True, "count": len(items)})
    except Exception as exc:
        _log.warning("[exec_approval_count] %s", exc)
        return JSONResponse({"ok": True, "count": 0})


@exec_approval_router.post("/app/exec_approval/{aid}/schvalit")
async def exec_approval_schvalit(req: Request, aid: int) -> JSONResponse:
    """✅ Palec rodiče → spustí TEN KONKRÉTNÍ příkaz přes eurosoft_exec, vrátí výsledek.
    Out-of-band lidský tap — jádro pravidla #3."""
    uid, ok = _parent(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "Nepřihlášen"}, status_code=401)
    if not ok:
        return JSONResponse({"ok": False, "error": "Jen rodič může schvalovat příkazy."}, status_code=403)
    from modules.eurosoft_mcp import exec_approval as ea
    try:
        res = await run_in_threadpool(ea.approve_and_execute, aid, uid)
        code = 200 if res.get("ok") or res.get("status") else 400
        return JSONResponse(res, status_code=code if not res.get("ok") and not res.get("status") else 200)
    except Exception as exc:
        _log.exception("[exec_approval_schvalit] %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@exec_approval_router.post("/app/exec_approval/{aid}/zamitnout")
async def exec_approval_zamitnout(req: Request, aid: int) -> JSONResponse:
    """⛔ Palec rodiče → zamítne žádost."""
    uid, ok = _parent(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "Nepřihlášen"}, status_code=401)
    if not ok:
        return JSONResponse({"ok": False, "error": "Jen rodič může schvalovat příkazy."}, status_code=403)
    from modules.eurosoft_mcp import exec_approval as ea
    try:
        res = await run_in_threadpool(ea.reject, aid, uid)
        return JSONResponse(res, status_code=200 if res.get("ok") else 400)
    except Exception as exc:
        _log.exception("[exec_approval_zamitnout] %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
