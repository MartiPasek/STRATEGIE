"""act_executor — běhový engine FW Action Pipelines (Marti 3.6.2026).

Kontrakt akce: validate -> run -> finalize. Robustnost: každá akce povinně
vrátí result_code, má timeout, loguje start+konec; žádný throw do prázdna,
žádné zamrznutí. Pipeline = složená akce (sub_pipeline_id) se stejným
kontraktem. Větvení přes act_condition_def (result_code -> next_step_no).
Deferred (FE akce) -> run.status='paused' + resume_token, pokračování přes
resume(). Vše se zapisuje do act_run / act_run_step / act_run_task /
act_run_log / act_run_data (monitorovatelné po krocích).

Stavy: pending / running / paused / done / error / timeout.
error_mode (pipeline nebo per-step override): stop / continue / branch.
"""
from __future__ import annotations

import time
import uuid
import json
from typing import Any, Optional

from sqlalchemy import text as _t

from core.database_data import get_data_session
from modules.act_pipeline import act_registry

_FAILURE_CODES = {"error", "failed", "timeout"}


# ─────────────────────────── DB helpers ───────────────────────────

def _scalar(ds, sql: str, **p):
    return ds.execute(_t(sql), p).scalar()


def _row(ds, sql: str, **p):
    r = ds.execute(_t(sql), p).mappings().first()
    return dict(r) if r else None


def _rows(ds, sql: str, **p):
    return [dict(r) for r in ds.execute(_t(sql), p).mappings().all()]


def _log(ds, run_id, message, level="info", step_id=None, task_id=None, detail=None):
    ds.execute(_t(
        "INSERT INTO fw.act_run_log (run_id, run_step_id, run_task_id, level, message, detail) "
        "VALUES (:r, :s, :t, :l, :m, CAST(:d AS jsonb))"
    ), {"r": run_id, "s": step_id, "t": task_id, "l": level, "m": str(message)[:4000],
        "d": json.dumps(detail) if detail is not None else None})


def _put_data(ds, run_id, step_key, value):
    ds.execute(_t(
        "INSERT INTO fw.act_run_data (run_id, step_key, value) VALUES (:r, :k, CAST(:v AS jsonb))"
    ), {"r": run_id, "k": str(step_key), "v": json.dumps(value)})


def _get_data(ds, run_id, step_key):
    return _scalar(ds, "SELECT value FROM fw.act_run_data WHERE run_id=:r AND step_key=:k "
                       "ORDER BY id DESC LIMIT 1", r=run_id, k=str(step_key))


# ─────────────────────────── input mapping ───────────────────────────

def _resolve_inputs(ds, run_id, context: dict, input_mapping: Optional[dict]) -> dict:
    """input_mapping JSONB → konkrétní hodnoty. Podporované formy per klíč:
       {"const": v} | {"context": "key"} | {"step": N, "field": "f"} | skalár (=const).
       Explicitní, viditelné — žádný skrytý kontext-bag."""
    out: dict = {}
    if not input_mapping:
        return out
    for key, spec in input_mapping.items():
        if isinstance(spec, dict):
            if "const" in spec:
                out[key] = spec["const"]
            elif "context" in spec:
                out[key] = (context or {}).get(spec["context"])
            elif "step" in spec:
                val = _get_data(ds, run_id, spec["step"])
                if isinstance(val, dict) and "field" in spec:
                    out[key] = val.get(spec["field"])
                else:
                    out[key] = val
            else:
                out[key] = spec
        else:
            out[key] = spec
    return out


# ─────────────────────────── handler invocation ───────────────────────────

def _run_be_task(ds, run, step, task_def, action_def) -> dict:
    """Spustí backend handler dle kontraktu validate->run->finalize. Vždy vrátí
    {"result_code", "output"}; nikdy nehází výjimku ven (chyceno → error)."""
    code = action_def["code"]
    module = act_registry.be_module(code)
    inputs = _resolve_inputs(ds, run["id"], run.get("context") or {}, task_def.get("input_mapping"))
    ctx = {
        "params": task_def.get("params_schema") or {},
        "inputs": inputs,
        "run_id": run["id"], "step_no": step["step_no"],
        "dry_run": bool(run.get("dry_run")),
        "timeout_ms": action_def.get("timeout_ms") or 30000,
        "started_by_user_id": run.get("started_by_user_id"),
        "started_by_persona_id": run.get("started_by_persona_id"),
        "idempotency_key_template": task_def.get("idempotency_key_template"),
    }
    task_run_id = _scalar(ds,
        "INSERT INTO fw.act_run_task (run_step_id, task_def_id, status, input, action_version, started_at) "
        "VALUES (:s, :t, 'running', CAST(:i AS jsonb), :v, now()) RETURNING id",
        s=step["_run_step_id"], t=task_def["id"], i=json.dumps(inputs), v=action_def.get("version"))
    ds.commit()

    result = {"result_code": "error", "output": {}}
    t0 = time.monotonic()
    try:
        if module is None:
            raise RuntimeError(f"handler '{code}' není registrován")
        # validate (volitelné) — raise = nespustí run
        if hasattr(module, "validate"):
            module.validate(ctx)
        # run (povinné)
        res = module.run(ctx) or {}
        rc = res.get("result_code") or "ok"
        result = {"result_code": rc, "output": res.get("output") or {}}
    except Exception as exc:  # žádný throw do prázdna
        result = {"result_code": "error", "output": {}, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        # finalize (volitelné) — nesmí shodit běh
        try:
            if module is not None and hasattr(module, "finalize"):
                module.finalize(ctx, result)
        except Exception as fexc:
            _log(ds, run["id"], f"finalize selhal: {fexc}", level="error",
                 step_id=step["_run_step_id"], task_id=task_run_id)

    dur = int((time.monotonic() - t0) * 1000)
    ds.execute(_t(
        "UPDATE fw.act_run_task SET status=:st, output=CAST(:o AS jsonb), "
        "error_message=:e, finished_at=now() WHERE id=:id"
    ), {"st": ("error" if result["result_code"] in _FAILURE_CODES else "done"),
        "o": json.dumps(result.get("output") or {}), "e": result.get("error"), "id": task_run_id})
    _put_data(ds, run["id"], step["step_no"], result.get("output") or {})
    _log(ds, run["id"], f"task {code} -> {result['result_code']} ({dur} ms)",
         level=("error" if result["result_code"] in _FAILURE_CODES else "info"),
         step_id=step["_run_step_id"], task_id=task_run_id,
         detail={"result_code": result["result_code"], "duration_ms": dur, "error": result.get("error")})
    ds.commit()
    return result


# ─────────────────────────── branching ───────────────────────────

def _next_step_no(ds, step, result_code) -> Optional[int]:
    """Z act_condition_def: branch result_code -> next_step_no. None = konec.
    Pokud žádná podmínka nematchne, sekvenčně další step_no (vrací 'SEQ')."""
    conds = _rows(ds, "SELECT * FROM fw.act_condition_def WHERE step_id=:s "
                      "AND cond_type='branch' ORDER BY sort_order", s=step["id"])
    for c in conds:
        rc = c.get("result_code")
        if rc is None or rc == result_code:
            return c.get("next_step_no")  # může být None = konec
    return "SEQ"  # žádná branch podmínka → sekvenční pokračování


# ─────────────────────────── core drive ───────────────────────────

def _finish_run(ds, run_id, status, error=None):
    ds.execute(_t("UPDATE fw.act_run SET status=:st, error_message=:e, finished_at=now() WHERE id=:id"),
               {"st": status, "e": error, "id": run_id})
    ds.commit()


def _drive(ds, run_id, from_step_no: int) -> dict:
    """Vykonává pipeline od daného step_no. Vrací stav pro klienta:
    {"status": done|error|paused, ...}. Při FE akci pausne a vrátí client_action."""
    run = _row(ds, "SELECT * FROM fw.act_run WHERE id=:id", id=run_id)
    pipeline = _row(ds, "SELECT * FROM fw.act_pipeline_def WHERE id=:id", id=run["pipeline_id"])
    steps = _rows(ds, "SELECT * FROM fw.act_step_def WHERE pipeline_id=:p ORDER BY step_no",
                  p=run["pipeline_id"])
    by_no = {s["step_no"]: s for s in steps}
    order = sorted(by_no.keys())

    cur = from_step_no
    guard = 0
    while cur is not None and cur in by_no:
        guard += 1
        if guard > 500:
            _finish_run(ds, run_id, "error", "guard: >500 kroků (smyčka?)")
            return {"status": "error", "error": "loop_guard"}
        step = by_no[cur]
        run_step_id = _scalar(ds,
            "INSERT INTO fw.act_run_step (run_id, step_id, status, started_at) "
            "VALUES (:r, :s, 'running', now()) RETURNING id", r=run_id, s=step["id"])
        ds.commit()
        step["_run_step_id"] = run_step_id

        # ── sub-pipeline (composite) ──
        if (step.get("step_type") == "sub") and step.get("sub_pipeline_id"):
            sub = run_pipeline(step["sub_pipeline_id"], context=run.get("context") or {},
                               started_by_user_id=run.get("started_by_user_id"),
                               started_by_persona_id=run.get("started_by_persona_id"),
                               dry_run=bool(run.get("dry_run")), _parent_run=run_id)
            rc = "ok" if sub.get("status") == "done" else "error"
            ds.execute(_t("UPDATE fw.act_run_step SET status=:st, finished_at=now() WHERE id=:id"),
                       {"st": ("done" if rc == "ok" else "error"), "id": run_step_id})
            ds.commit()
            result = {"result_code": rc, "output": sub.get("result") or {}}
        else:
            # ── task step ──
            task_def = _row(ds, "SELECT * FROM fw.act_task_def WHERE step_id=:s ORDER BY id LIMIT 1",
                            s=step["id"])
            if not task_def:
                _log(ds, run_id, f"step {cur} nemá task_def — skip", level="warn", step_id=run_step_id)
                ds.execute(_t("UPDATE fw.act_run_step SET status='done', finished_at=now() WHERE id=:id"),
                           {"id": run_step_id}); ds.commit()
                result = {"result_code": "ok", "output": {}}
            else:
                action = _row(ds, "SELECT * FROM fw.act_def WHERE id=:id", id=task_def["action_id"])
                ctx_kind = act_registry.context_of(action["code"]) if action else None

                if ctx_kind == "frontend":
                    # deferred — pipeline čeká na prohlížeč
                    token = uuid.uuid4().hex
                    inputs = _resolve_inputs(ds, run_id, run.get("context") or {},
                                             task_def.get("input_mapping"))
                    ds.execute(_t("UPDATE fw.act_run_step SET status='paused', input=CAST(:i AS jsonb) WHERE id=:id"),
                               {"i": json.dumps(inputs), "id": run_step_id})
                    ds.execute(_t("UPDATE fw.act_run SET status='paused', resume_token=:tok WHERE id=:id"),
                               {"tok": token, "id": run_id})
                    _log(ds, run_id, f"paused na FE akci {action['code']} (step {cur})",
                         level="info", step_id=run_step_id)
                    ds.commit()
                    return {"status": "paused", "run_id": run_id, "resume_token": token,
                            "client_action": {"handler": action["code"], "step_no": cur,
                                              "params": task_def.get("params_schema") or {},
                                              "inputs": inputs}}

                if ctx_kind == "backend":
                    result = _run_be_task(ds, run, step, task_def, action)
                else:
                    _log(ds, run_id, f"step {cur}: neznámý handler '{action['code'] if action else '?'}'",
                         level="error", step_id=run_step_id)
                    ds.execute(_t("UPDATE fw.act_run_step SET status='error', finished_at=now() WHERE id=:id"),
                               {"id": run_step_id}); ds.commit()
                    result = {"result_code": "error", "output": {}}

            ds.execute(_t("UPDATE fw.act_run_step SET status=:st, output=CAST(:o AS jsonb), finished_at=now() WHERE id=:id"),
                       {"st": ("error" if result["result_code"] in _FAILURE_CODES else "done"),
                        "o": json.dumps(result.get("output") or {}), "id": run_step_id})
            ds.commit()

        # ── chyba uprostřed → error_mode ──
        if result["result_code"] in _FAILURE_CODES:
            mode = step.get("error_mode") or pipeline.get("error_mode") or "stop"
            if mode == "continue":
                _log(ds, run_id, f"step {cur} chyba ({result['result_code']}), error_mode=continue", level="warn",
                     step_id=run_step_id)
                # pokračuj sekvenčně
            else:  # stop (default) — branch řešíme přes act_condition_def níže jen u non-failure
                _finish_run(ds, run_id, "error", result.get("error") or result["result_code"])
                return {"status": "error", "run_id": run_id, "error": result.get("error") or result["result_code"]}

        # ── další krok (větvení) ──
        nxt = _next_step_no(ds, step, result["result_code"])
        if nxt == "SEQ":
            later = [n for n in order if n > cur]
            cur = later[0] if later else None
        else:
            cur = nxt  # konkrétní step_no nebo None (konec)

    _finish_run(ds, run_id, "done")
    final = _row(ds, "SELECT * FROM fw.act_run WHERE id=:id", id=run_id)
    return {"status": "done", "run_id": run_id, "result": final.get("result")}


# ─────────────────────────── public API ───────────────────────────

def run_pipeline(pipeline_ref, context: dict | None = None, started_by_user_id=None,
                 started_by_persona_id=None, trigger_binding_id=None, dry_run=False,
                 _parent_run=None) -> dict:
    """Spustí pipeline (id nebo code). Vrací stav pro klienta (done/error/paused)."""
    ds = get_data_session()
    try:
        if isinstance(pipeline_ref, int) or (isinstance(pipeline_ref, str) and pipeline_ref.isdigit()):
            pl = _row(ds, "SELECT * FROM fw.act_pipeline_def WHERE id=:id", id=int(pipeline_ref))
        else:
            pl = _row(ds, "SELECT * FROM fw.act_pipeline_def WHERE code=:c", c=str(pipeline_ref))
        if not pl:
            return {"status": "error", "error": f"pipeline '{pipeline_ref}' nenalezena"}
        run_id = _scalar(ds,
            "INSERT INTO fw.act_run (pipeline_id, trigger_binding_id, status, context, dry_run, "
            "started_by_user_id, started_by_persona_id, started_at) "
            "VALUES (:p, :tb, 'running', CAST(:c AS jsonb), :dr, :u, :pe, now()) RETURNING id",
            p=pl["id"], tb=trigger_binding_id, c=json.dumps(context or {}), dr=bool(dry_run),
            u=started_by_user_id, pe=started_by_persona_id)
        ds.commit()
        _log(ds, run_id, f"pipeline {pl['code']} start (dry_run={bool(dry_run)})",
             detail={"context": context or {}})
        first = _scalar(ds, "SELECT min(step_no) FROM fw.act_step_def WHERE pipeline_id=:p", p=pl["id"])
        if first is None:
            _finish_run(ds, run_id, "done")
            return {"status": "done", "run_id": run_id, "result": None}
        return _drive(ds, run_id, int(first))
    finally:
        ds.close()


def resume(resume_token: str, result_code: str = "ok", outputs: dict | None = None) -> dict:
    """Pokračování deferred pipeline (FE akce dokončena). Najde paused run dle
    tokenu, zapíše výsledek FE kroku, pokračuje dál (větvení dle result_code)."""
    ds = get_data_session()
    try:
        run = _row(ds, "SELECT * FROM fw.act_run WHERE resume_token=:tok AND status='paused'",
                   tok=resume_token)
        if not run:
            return {"status": "error", "error": "paused run pro token nenalezen"}
        rstep = _row(ds, "SELECT * FROM fw.act_run_step WHERE run_id=:r AND status='paused' "
                         "ORDER BY id DESC LIMIT 1", r=run["id"])
        if not rstep:
            return {"status": "error", "error": "paused step nenalezen"}
        step = _row(ds, "SELECT * FROM fw.act_step_def WHERE id=:id", id=rstep["step_id"])
        # zapiš výsledek FE kroku
        _put_data(ds, run["id"], step["step_no"], outputs or {})
        ds.execute(_t("UPDATE fw.act_run_step SET status='done', output=CAST(:o AS jsonb), finished_at=now() WHERE id=:id"),
                   {"o": json.dumps(outputs or {}), "id": rstep["id"]})
        ds.execute(_t("UPDATE fw.act_run SET status='running', resume_token=NULL WHERE id=:id"),
                   {"id": run["id"]})
        _log(ds, run["id"], f"resume step {step['step_no']} -> {result_code}", step_id=rstep["id"],
             detail={"outputs": outputs or {}})
        ds.commit()
        # další krok dle větvení
        nxt = _next_step_no(ds, step, result_code)
        if nxt == "SEQ":
            order = _rows(ds, "SELECT step_no FROM fw.act_step_def WHERE pipeline_id=:p ORDER BY step_no",
                          p=run["pipeline_id"])
            later = [r["step_no"] for r in order if r["step_no"] > step["step_no"]]
            nxt = later[0] if later else None
        if nxt is None:
            _finish_run(ds, run["id"], "done")
            return {"status": "done", "run_id": run["id"]}
        return _drive(ds, run["id"], int(nxt))
    finally:
        ds.close()


def run_status(run_id: int) -> dict:
    """Stav běhu + kroky (monitoring)."""
    ds = get_data_session()
    try:
        run = _row(ds, "SELECT * FROM fw.act_run WHERE id=:id", id=run_id)
        if not run:
            return {"ok": False, "error": "run nenalezen"}
        steps = _rows(ds, "SELECT id, step_id, status, result_code, started_at, finished_at, error_message "
                          "FROM fw.act_run_step WHERE run_id=:r ORDER BY id", r=run_id)
        return {"ok": True, "run": run, "steps": steps}
    finally:
        ds.close()
