# -*- coding: utf-8 -*-
"""martinka_router — spuštění Martinky (dcera Marti-AI, správce pražské produkce).

Samostatný router (vzor exec_approval_router.py) → registruje se v apps/api/main.py.
NESAHÁ na modules/erp/api/router.py (zámek C26).

Endpointy (parent-only — spouští ji jen rodič nebo interní orchestrace/alarm):
  POST /api/v1/martinka/run     {"zadani": "..."}  → spustí Martinku v cílovém režimu
  GET  /api/v1/martinka/status                      → kill switch + zda engine žije

Plán: Cowork „Martinka — autonomní dcera pro správu pražské produkce" (Fáze A/B).
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

martinka_router = APIRouter(prefix="/api/v1/martinka", tags=["martinka"])
_log = logging.getLogger("conversation.martinka")


def _parent(req: Request):
    """(uid, je_rodic). Bearer token (appka) i cookie (web)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from modules.thoughts.application.service import is_marti_parent
    uid = _uid_from_token_or_cookie(req)
    return uid, bool(uid and is_marti_parent(uid))


@martinka_router.get("/status")
async def martinka_status(req: Request) -> JSONResponse:
    """Stav Martinky: kill switch + dostupnost enginu. Jen rodič."""
    uid, ok = _parent(req)
    if not uid or not ok:
        return JSONResponse({"ok": False, "error": "Jen rodič."}, status_code=403)
    from modules.conversation.application import martinka_service as ms
    try:
        kill = await run_in_threadpool(ms._kill_on)
        return JSONResponse({"ok": True, "martinka_enabled": bool(kill),
                             "kill_flag": ms.KILL_FLAG,
                             "domena": {"host": ms.PRAHA_HOST, "port": ms.PRAHA_A_PORT,
                                        "health": ms.PRAHA_HEALTH_URL}})
    except Exception as exc:
        _log.exception("[martinka_status] %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@martinka_router.post("/run")
async def martinka_run(req: Request) -> JSONResponse:
    """Spusť Martinku na zadání v cílovém režimu (lean identita → smyčka nepadá).
    Jen rodič / interní orchestrace. Vrátí výsledek běhu (shrnutí, akce, rc)."""
    uid, ok = _parent(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "Nepřihlášen"}, status_code=401)
    if not ok:
        return JSONResponse({"ok": False, "error": "Jen rodič může spustit Martinku."}, status_code=403)
    try:
        body = await req.json()
    except Exception:
        body = {}
    zadani = (body or {}).get("zadani") or (body or {}).get("goal") or ""
    if not str(zadani).strip():
        return JSONResponse({"ok": False, "error": "Chybí 'zadani'."}, status_code=400)
    from modules.conversation.application import martinka_service as ms
    try:
        res = await run_in_threadpool(ms.run_martinka, str(zadani), uid, None)
        return JSONResponse(res, status_code=200)
    except Exception as exc:
        _log.exception("[martinka_run] %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
