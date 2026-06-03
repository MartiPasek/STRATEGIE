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


@act_router.get("/pipeline/{ref}/graph")
async def act_pipeline_graph(ref: str, req: Request) -> JSONResponse:
    """Grafický přehled pipeline pro vizualizaci (Marti 3.6.2026) — kroky
    pod sebe jako akční karty. Vrací meta pipeline + uspořádané kroky
    s resolvnutou akcí (code/name/handler context backend|frontend|sub),
    error_mode a větvením (act_condition_def: result_code -> next_step_no)."""
    _uid(req)
    from core.database_data import get_data_session
    from sqlalchemy import text as _t

    ds = get_data_session()
    try:
        if ref.isdigit():
            pl = ds.execute(_t("SELECT * FROM fw.act_pipeline_def WHERE id = :x"),
                            {"x": int(ref)}).mappings().first()
        else:
            pl = ds.execute(_t("SELECT * FROM fw.act_pipeline_def WHERE code = :x"),
                            {"x": ref}).mappings().first()
        if not pl:
            return JSONResponse({"ok": False, "error": f"pipeline '{ref}' nenalezena"},
                                status_code=404)
        pl = dict(pl)

        steps = [dict(r) for r in ds.execute(_t(
            "SELECT * FROM fw.act_step_def WHERE pipeline_id = :p ORDER BY step_no"
        ), {"p": pl["id"]}).mappings().all()]

        out_steps = []
        for st in steps:
            node = {
                "step_no": st["step_no"],
                "step_type": st.get("step_type"),
                "label": st.get("label"),
                "error_mode": st.get("error_mode") or pl.get("error_mode") or "stop",
            }
            if st.get("step_type") == "sub" and st.get("sub_pipeline_id"):
                sub = ds.execute(_t("SELECT code, name FROM fw.act_pipeline_def WHERE id = :i"),
                                 {"i": st["sub_pipeline_id"]}).mappings().first()
                node["action_code"] = sub["code"] if sub else None
                node["title"] = st.get("label") or (sub["name"] if sub and sub["name"] else None) \
                    or (sub["code"] if sub else f"pipeline #{st['sub_pipeline_id']}")
                node["context"] = "sub"
                node["kind"] = "sub_pipeline"
                node["description"] = "Vnořená pipeline (složená akce)"
                node["detail"] = {
                    "sub_pipeline_id": st["sub_pipeline_id"],
                    "sub_pipeline_code": (sub["code"] if sub else None),
                }
            else:
                td = ds.execute(_t("SELECT * FROM fw.act_task_def WHERE step_id = :s ORDER BY id LIMIT 1"),
                                {"s": st["id"]}).mappings().first()
                if td:
                    ad = ds.execute(_t("SELECT * FROM fw.act_def WHERE id = :i"),
                                    {"i": td["action_id"]}).mappings().first()
                    code = ad["code"] if ad else None
                    node["action_code"] = code
                    node["title"] = st.get("label") or (ad["name"] if ad and ad["name"] else None) \
                        or code or f"krok {st['step_no']}"
                    node["description"] = (ad["description"] if ad else None)
                    node["context"] = act_registry.context_of(code) if code else None
                    node["handler"] = (ad["handler"] if ad else None)
                    node["kind"] = "task"
                    # Inspektor parametrů (Marti 3.6.2026): co krok fyzicky dělá.
                    node["detail"] = {
                        "action_type": (ad["action_type"] if ad else None),
                        "timeout_ms": (ad["timeout_ms"] if ad else None),
                        "action_version": (ad["version"] if ad else None),
                        "action_status": (ad["status"] if ad else None),
                        "input_mapping": td.get("input_mapping"),
                        "params_schema": td.get("params_schema"),
                        "idempotency_key_template": td.get("idempotency_key_template"),
                        "input_schema": (ad["input_schema"] if ad else None),
                        "output_schema": (ad["output_schema"] if ad else None),
                    }
                else:
                    node["title"] = st.get("label") or f"krok {st['step_no']} (bez tasku)"
                    node["kind"] = "empty"
                    node["context"] = None

            node["branches"] = [
                {"result_code": c["result_code"], "next_step_no": c["next_step_no"]}
                for c in ds.execute(_t(
                    "SELECT result_code, next_step_no FROM fw.act_condition_def "
                    "WHERE step_id = :s ORDER BY sort_order NULLS LAST, id"
                ), {"s": st["id"]}).mappings().all()
            ]
            out_steps.append(node)

        return JSONResponse({"ok": True, "pipeline": {
            "id": pl["id"], "code": pl["code"], "name": pl.get("name"),
            "version": pl.get("version"), "description": pl.get("description"),
            "error_mode": pl.get("error_mode"), "status": pl.get("status"),
            "step_count": len(out_steps),
        }, "steps": out_steps})
    finally:
        ds.close()


# Bootstrap registry při importu (FE/BE handlery). Fail-soft — chyba importu
# handleru nesmí shodit celé API; zaloguje se.
try:
    act_registry.bootstrap()
except Exception as _exc:  # pragma: no cover
    import sys as _sys
    _sys.stderr.write("[act_router] registry bootstrap selhal: %r\n" % (_exc,))
