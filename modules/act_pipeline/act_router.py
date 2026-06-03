"""act_router — REST API pro FW Action Pipelines (Marti 3.6.2026).

Endpointy (prefix /api/v1/erp/act):
  POST /run           — spusť pipeline (id/code + context + dry_run)
  POST /resume        — pokračuj deferred pipeline (resume_token + result + outputs)
  GET  /run/{id}      — stav běhu + kroky (monitoring)
  GET  /handlers      — katalog registrovaných handlerů (diagnostika)

Auth: user_id cookie (jako zbytek ERP API).
"""
from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from modules.act_pipeline import act_executor, act_registry

act_router = APIRouter(prefix="/api/v1/erp/act", tags=["act-pipeline"])


def _uid(req: Request):
    s = req.cookies.get("user_id")
    if not s:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(s)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


@act_router.post("/run")
async def act_run(req: Request) -> JSONResponse:
    uid = _uid(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    pipeline = body.get("pipeline")
    if pipeline in (None, ""):
        return JSONResponse({"ok": False, "error": "chybí pipeline (id/code)"}, status_code=400)
    res = act_executor.run_pipeline(
        pipeline,
        context=body.get("context") or {},
        started_by_user_id=uid,
        started_by_persona_id=body.get("persona_id"),
        dry_run=bool(body.get("dry_run")),
    )
    return JSONResponse({"ok": res.get("status") != "error", **res})


@act_router.post("/resume")
async def act_resume(req: Request) -> JSONResponse:
    _uid(req)
    try:
        body = await req.json()
    except Exception:
        body = {}
    token = body.get("resume_token")
    if not token:
        return JSONResponse({"ok": False, "error": "chybí resume_token"}, status_code=400)
    res = act_executor.resume(token, result_code=body.get("result_code") or "ok",
                              outputs=body.get("outputs") or {})
    return JSONResponse({"ok": res.get("status") != "error", **res})


@act_router.get("/run/{run_id}")
async def act_run_status(run_id: int, req: Request) -> JSONResponse:
    _uid(req)
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(jsonable_encoder(act_executor.run_status(run_id)))


@act_router.get("/handlers")
async def act_handlers(req: Request) -> JSONResponse:
    _uid(req)
    return JSONResponse({"ok": True, "handlers": act_registry.all_handlers()})


# Bootstrap registry při importu (FE/BE handlery). Fail-soft — chyba importu
# handleru nesmí shodit celé API; zaloguje se.
try:
    act_registry.bootstrap()
except Exception as _exc:  # pragma: no cover
    import sys as _sys
    _sys.stderr.write("[act_router] registry bootstrap selhal: %r\n" % (_exc,))
