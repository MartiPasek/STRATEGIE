"""DR: přenos HOTOVÝCH nočních dumpů data_db Praha → Plzeň (Claude ID23, 19.7.2026 r6).

Model (Marti): noční záloha (3:00, postgres, na 188.12) = čistě ukončený DB den.
188.12 ho po záloze NAHRAJE k API (188.11) přes HTTPS (žádné sdílení disků), Plzeň si ho stáhne.
  POST /api/v1/ops/dr/upload   → 188.12 pushne hotový dump (stream body → uloží na API box)
  GET  /api/v1/ops/dr/meta     → co je uložené {stored,name,size,mtime,age_s}
  GET  /api/v1/ops/dr/download → FileResponse uloženého dumpu (Content-Length → proxy streamuje)
Token X-DR-Token (env DR_TRANSFER_TOKEN nebo <repo>/dr_token.txt). Temp: env DR_TMP_DIR.
Skripty: scripts/dr/push_dump.ps1 (188.12, 3:15) · fetch_dump.ps1+restore_data_db.ps1 (Plzeň, 3:30).
"""
from __future__ import annotations

import hmac
import json
import os
import pathlib
import tempfile
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

drops_router = APIRouter(prefix="/api/v1/ops", tags=["dr-ops"])

_REPO = str(pathlib.Path(__file__).resolve().parents[3])
_TOKEN_FILE = os.environ.get("DR_TOKEN_FILE", "") or os.path.join(_REPO, "dr_token.txt")
_TMP = os.environ.get("DR_TMP_DIR", "") or os.path.join(tempfile.gettempdir(), "dr_dump")
_DUMP = os.path.join(_TMP, "dr_data_db.dump")
_META = os.path.join(_TMP, "dr_data_db.meta.json")


def _token() -> str:
    t = (os.environ.get("DR_TRANSFER_TOKEN", "") or "").strip()
    if t:
        return t
    try:
        with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _guard(req: Request):
    want = _token()
    if not want:
        return JSONResponse({"ok": False, "error": "token_not_configured"}, status_code=503)
    if not hmac.compare_digest(req.headers.get("X-DR-Token", "") or "", want):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return None


def _write_meta(d: dict):
    try:
        with open(_META, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


def _read_meta() -> dict:
    try:
        with open(_META, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@drops_router.post("/dr/upload")
async def dr_upload(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    os.makedirs(_TMP, exist_ok=True)
    part = _DUMP + ".part"
    size = 0
    try:
        with open(part, "wb") as f:
            async for chunk in req.stream():
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
    except Exception as e:
        try:
            os.remove(part)
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": "upload_failed", "detail": str(e)[:300]}, status_code=500)
    if size < 1024:
        try:
            os.remove(part)
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": "empty", "size": size}, status_code=400)
    os.replace(part, _DUMP)
    src_name = (req.query_params.get("name") or "").strip() or os.path.basename(_DUMP)
    st = os.stat(_DUMP)
    _write_meta({"name": src_name, "size": st.st_size, "mtime": int(st.st_mtime),
                 "uploaded_at": datetime.now(timezone.utc).isoformat()})
    return JSONResponse({"ok": True, "size": st.st_size, "name": src_name})


@drops_router.get("/dr/meta")
async def dr_meta(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    if not os.path.isfile(_DUMP):
        return JSONResponse({"ok": True, "stored": False, "hint": "zatím nic nenahráno (push z 188.12)"})
    st = os.stat(_DUMP)
    m = _read_meta()
    return JSONResponse({"ok": True, "stored": True, "name": m.get("name") or os.path.basename(_DUMP),
                         "size": st.st_size, "mtime": int(st.st_mtime),
                         "age_s": int(time.time() - st.st_mtime), "meta": m})


@drops_router.get("/dr/download")
async def dr_download(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    if not os.path.isfile(_DUMP):
        return JSONResponse({"ok": False, "error": "not_stored", "hint": "nejdřív push z 188.12"}, status_code=404)
    m = _read_meta()
    return FileResponse(_DUMP, media_type="application/octet-stream",
                        filename=m.get("name") or os.path.basename(_DUMP))


@drops_router.post("/dr/selfcheck")
async def dr_selfcheck(req: Request):
    """Plzen DR agent (X-DR-Token) -> denni samokontrola obnovy (denik obnov).
    Cloud spocita verdikt (OK/NENI_OK) + duvod, zapise do fw.dr_selfcheck a pri
    NENI_OK posle push Martimu. Claude C23 21.7.2026."""
    g = _guard(req)
    if g is not None:
        return g
    try:
        body = await req.json()
    except Exception:
        body = {}

    def _num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    def _int(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None

    source = (str(body.get("source") or "PLZEN"))[:64]
    db_online = bool(body.get("db_online"))
    data_age_h = _num(body.get("data_age_h"))
    cnt_conv = _int(body.get("cnt_conversations"))
    cnt_vec = _int(body.get("cnt_vectors"))
    cnt_tab = _int(body.get("cnt_tables"))
    pgvector = bool(body.get("pgvector"))
    chain_count = _int(body.get("chain_count"))
    chain_oldest = (str(body.get("chain_oldest") or ""))[:20] or None
    chain_newest = (str(body.get("chain_newest") or ""))[:20] or None
    reasons = []
    if not db_online:
        reasons.append("DB neodpovida")
    if data_age_h is None or data_age_h > 30:
        reasons.append("data stara %s h (>30) - restore mozna neprobehl" % (("%.1f" % data_age_h) if data_age_h is not None else "?"))
    if not cnt_tab or cnt_tab < 400:
        reasons.append("malo tabulek (%s <400)" % cnt_tab)
    if not cnt_conv or cnt_conv < 1:
        reasons.append("0 konverzaci")
    if not cnt_vec or cnt_vec < 1:
        reasons.append("0 vektoru")
    if not pgvector:
        reasons.append("chybi pgvector")
    if body.get("error"):
        reasons.append("agent: %s" % str(body.get("error"))[:120])
    verdict = "OK" if not reasons else "NENI_OK"
    reason = "; ".join(reasons)[:500] if reasons else "obnova OK, data cerstva, pocty sedi"
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        ds = _gds()
        try:
            ds.execute(_t(
                "INSERT INTO fw.dr_selfcheck (source, db_online, data_age_h, cnt_conversations, "
                "cnt_vectors, cnt_tables, pgvector, chain_count, chain_oldest, chain_newest, verdict, reason, raw) "
                "VALUES (:s,:onl,:age,:cc,:cv,:ct,:pv,:chc,:cho,:chn,:vd,:rs, CAST(:raw AS jsonb))"),
                {"s": source, "onl": db_online, "age": data_age_h, "cc": cnt_conv,
                 "cv": cnt_vec, "ct": cnt_tab, "pv": pgvector,
                 "chc": chain_count, "cho": chain_oldest, "chn": chain_newest,
                 "vd": verdict, "rs": reason,
                 "raw": json.dumps(body)[:8000]})
            if verdict != "OK":
                try:
                    ds.execute(_t(
                        "INSERT INTO fw.mobile_command (app_key, target_user_id, command_type, title, message, created_by) "
                        "VALUES ('mobile', 1, 'claude_msg', :title, :msg, NULL)"),
                        {"title": "DR obnova: NENI OK",
                         "msg": ("Denni samokontrola zalohy (" + source + ") selhala: " + reason)[:600]})
                except Exception:
                    pass
            ds.commit()
        finally:
            ds.close()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)
    return JSONResponse({"ok": True, "verdict": verdict, "reason": reason})


# ─────────────────────────────────────────────────────────────────────────────
# Plzeň command relay (Claude C23, 23.7.2026)
# Cíl: 30.11 (Plzeň, RDP-only) přestane vyžadovat ruční copy-paste PowerShellu.
# 30.11 už volá Prahu ven (DR pull) → obrátíme to v obousměrný audit-ovaný kanál:
#   POST /api/v1/ops/plzen/enqueue  (X-Deploy-Token)  — zařadí příkaz do fronty (dělá watcher/most)
#   GET  /api/v1/ops/plzen/pending  (X-Plzen-Token)   — poller si vyzvedne nejstarší 'queued'
#   POST /api/v1/ops/plzen/result   (X-Plzen-Token)   — poller vrátí stdout/stderr/rc
# Bezpečnost: samostatný token (fw.plzen_relay_cfg.token), master vypínač enabled,
#   plný audit ve fw.plzen_cmd_queue; poller navíc odmítá destruktivní vzory.
# ──────────────────────────────────────────────────────────────────────────────
import secrets as _plz_secrets

_PLZEN_DDL = [
    "CREATE SCHEMA IF NOT EXISTS fw",
    """CREATE TABLE IF NOT EXISTS fw.plzen_relay_cfg (
        id         int PRIMARY KEY DEFAULT 1,
        token      text NOT NULL,
        enabled    boolean NOT NULL DEFAULT true,
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT plzen_cfg_single CHECK (id = 1)
    )""",
    """CREATE TABLE IF NOT EXISTS fw.plzen_cmd_queue (
        id          bigserial PRIMARY KEY,
        nonce       text UNIQUE NOT NULL,
        label       text,
        command     text NOT NULL,
        status      text NOT NULL DEFAULT 'queued',   -- queued|taken|done|error|refused
        created_by  text,
        created_at  timestamptz NOT NULL DEFAULT now(),
        taken_at    timestamptz,
        done_at     timestamptz,
        exit_code   int,
        stdout      text,
        stderr      text,
        duration_ms int
    )""",
    "CREATE INDEX IF NOT EXISTS plzen_cmd_queue_status_idx ON fw.plzen_cmd_queue (status, id)",
]


def _plzen_cfg(ds):
    """Vrať (token, enabled). Tabulky se zkusí založit JEN když chybí (to_regclass) —
    když existují (předpřipravené migrací přes schvalovací most), žádné DDL se nespouští,
    takže app-role nepotřebuje CREATE práva. Token se vygeneruje 1x a uloží do DB (nikdy v gitu)."""
    from sqlalchemy import text as _t
    have = ds.execute(_t(
        "SELECT to_regclass('fw.plzen_relay_cfg') IS NOT NULL "
        "AND to_regclass('fw.plzen_cmd_queue') IS NOT NULL")).scalar()
    if not have:
        for stmt in _PLZEN_DDL:
            ds.execute(_t(stmt))
    row = ds.execute(_t("SELECT token, enabled FROM fw.plzen_relay_cfg WHERE id=1")).fetchone()
    if not row:
        tok = _plz_secrets.token_hex(24)
        ds.execute(_t(
            "INSERT INTO fw.plzen_relay_cfg (id, token, enabled) VALUES (1, :tk, true) "
            "ON CONFLICT (id) DO NOTHING"), {"tk": tok})
        row = ds.execute(_t("SELECT token, enabled FROM fw.plzen_relay_cfg WHERE id=1")).fetchone()
    return (row[0], bool(row[1]))


def _plzen_deploy_guard(req: Request):
    """Enqueue je privilegovaná akce → deploy-grade auth (stejný token jako watcher/deploy)."""
    want = (os.environ.get("STRATEGIE_DEPLOY_TOKEN", "") or "").strip()
    if not want:
        return JSONResponse({"ok": False, "error": "deploy_token_not_configured"}, status_code=503)
    if not hmac.compare_digest(req.headers.get("X-Deploy-Token", "") or "", want):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return None


def _plzen_token_guard(req: Request, want_token: str):
    if not want_token:
        return JSONResponse({"ok": False, "error": "relay_not_provisioned"}, status_code=503)
    if not hmac.compare_digest(req.headers.get("X-Plzen-Token", "") or "", want_token):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return None


@drops_router.post("/plzen/enqueue")
async def plzen_enqueue(req: Request):
    """Most/watcher (X-Deploy-Token) zařadí PowerShell příkaz pro 30.11 do fronty.
    Body: {command, label?, created_by?, nonce?}. Vrátí {ok, id, nonce}."""
    g = _plzen_deploy_guard(req)
    if g is not None:
        return g
    try:
        body = await req.json()
    except Exception:
        body = {}
    command = (body.get("command") or "").strip()
    if not command:
        return JSONResponse({"ok": False, "error": "empty_command"}, status_code=400)
    label = (str(body.get("label") or ""))[:200] or None
    created_by = (str(body.get("created_by") or "claude-23"))[:64]
    nonce = (str(body.get("nonce") or "")).strip()[:64] or ("q" + _plz_secrets.token_hex(8))
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        ds = _gds()
        try:
            _plzen_cfg(ds)  # ensure tables exist
            row = ds.execute(_t(
                "INSERT INTO fw.plzen_cmd_queue (nonce, label, command, created_by) "
                "VALUES (:n, :l, :c, :by) "
                "ON CONFLICT (nonce) DO NOTHING RETURNING id"),
                {"n": nonce, "l": label, "c": command[:100000], "by": created_by}).fetchone()
            ds.commit()
        finally:
            ds.close()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    if not row:
        return JSONResponse({"ok": True, "duplicate": True, "nonce": nonce})
    return JSONResponse({"ok": True, "id": int(row[0]), "nonce": nonce})


@drops_router.get("/plzen/pending")
async def plzen_pending(req: Request):
    """Poller (X-Plzen-Token) si atomicky vyzvedne nejstarší 'queued' příkaz (→ 'taken').
    Když je relay vypnutá (enabled=false) nebo fronta prázdná, vrátí cmd=null."""
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        ds = _gds()
        try:
            token, enabled = _plzen_cfg(ds)
            g = _plzen_token_guard(req, token)
            if g is not None:
                ds.close()
                return g
            if not enabled:
                ds.commit()
                return JSONResponse({"ok": True, "cmd": None, "disabled": True})
            row = ds.execute(_t(
                "WITH nxt AS ("
                "  SELECT id FROM fw.plzen_cmd_queue WHERE status='queued' "
                "  ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED) "
                "UPDATE fw.plzen_cmd_queue q SET status='taken', taken_at=now() "
                "FROM nxt WHERE q.id=nxt.id "
                "RETURNING q.nonce, q.label, q.command")).fetchone()
            ds.commit()
        finally:
            ds.close()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    if not row:
        return JSONResponse({"ok": True, "cmd": None})
    return JSONResponse({"ok": True, "cmd": {"nonce": row[0], "label": row[1], "command": row[2]}})


@drops_router.post("/plzen/result")
async def plzen_result(req: Request):
    """Poller (X-Plzen-Token) vrátí výsledek běhu. Body: {nonce, status, exit_code, stdout, stderr, duration_ms}."""
    try:
        body = await req.json()
    except Exception:
        body = {}
    nonce = (str(body.get("nonce") or "")).strip()[:64]
    if not nonce:
        return JSONResponse({"ok": False, "error": "missing_nonce"}, status_code=400)

    def _int(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None

    status = (str(body.get("status") or "done"))[:16]
    if status not in ("done", "error", "refused"):
        status = "done"
    rc = _int(body.get("exit_code"))
    out = (str(body.get("stdout") or ""))[:200000]
    err = (str(body.get("stderr") or ""))[:200000]
    ms = _int(body.get("duration_ms"))
    try:
        from core.database_data import get_data_session as _gds
        from sqlalchemy import text as _t
        ds = _gds()
        try:
            token, _enabled = _plzen_cfg(ds)
            g = _plzen_token_guard(req, token)
            if g is not None:
                ds.close()
                return g
            row = ds.execute(_t(
                "UPDATE fw.plzen_cmd_queue "
                "SET status=:st, done_at=now(), exit_code=:rc, stdout=:o, stderr=:e, duration_ms=:ms "
                "WHERE nonce=:n AND status IN ('taken','queued') RETURNING id"),
                {"st": status, "rc": rc, "o": out, "e": err, "ms": ms, "n": nonce}).fetchone()
            ds.commit()
        finally:
            ds.close()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    if not row:
        return JSONResponse({"ok": False, "error": "unknown_or_already_done_nonce", "nonce": nonce}, status_code=404)
    return JSONResponse({"ok": True, "id": int(row[0]), "status": status})

# --- Plzen relay endpoints nasazeny 2026-07-23, C23 (retrigger po srovnani stromu) ---
