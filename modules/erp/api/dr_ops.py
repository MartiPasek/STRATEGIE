"""DR: decouple přenos dumpu data_db Praha (API 188.11 → DB 188.12) → Plzeň.
Claude ID23, 19.7.2026 r4 — dump do souboru na pozadí + FileResponse (obchází buffer proxy).

Token X-DR-Token (env DR_TRANSFER_TOKEN nebo <repo>/dr_token.txt).
  GET /api/v1/ops/dr/meta      → readiness {ok,mode,db,host,pg_dump}
  GET /api/v1/ops/dr/prepare   → spustí pg_dump do temp souboru na pozadí (vrací hned)
  GET /api/v1/ops/dr/status    → {ok,ready,building,size,age_s,last}
  GET /api/v1/ops/dr/download  → FileResponse hotového dumpu (Content-Length → proxy streamuje)
Temp: env DR_TMP_DIR (default systémový temp/dr_dump). Plzeň: scripts/dr/fetch_dump.ps1.
"""
from __future__ import annotations

import hmac
import json
import os
import pathlib
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from modules.admin.application.backup_service import _parse_db_url, _resolve_pg_dump

drops_router = APIRouter(prefix="/api/v1/ops", tags=["dr-ops"])

_REPO = str(pathlib.Path(__file__).resolve().parents[3])
_TOKEN_FILE = os.environ.get("DR_TOKEN_FILE", "") or os.path.join(_REPO, "dr_token.txt")
_TMP = os.environ.get("DR_TMP_DIR", "") or os.path.join(tempfile.gettempdir(), "dr_dump")
_DUMP = os.path.join(_TMP, "dr_data_db.dump")
_BUILDING = os.path.join(_TMP, "dr_data_db.building")
_META = os.path.join(_TMP, "dr_data_db.meta.json")
_MAX_BUILD_AGE = 3600  # zaseknutý building marker starší než hodina → dovol restart
_lock = threading.Lock()


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


def _pgdump_cmd(outfile: str):
    pg_dump = _resolve_pg_dump()
    # Privilegovaná role pro dump (env DR_DUMP_URL, napr. postgres/Marti-AI se
    # čtecími právy na VŠE — app login nema prava na bak/sekvence). Fallback = app url.
    _dump_url = (os.environ.get("DR_DUMP_URL", "") or "").strip() or settings.database_data_url
    host, port, user, password, dbname = _parse_db_url(_dump_url)
    cmd = [pg_dump, "-h", host, "-p", port, "-U", user, "-d", dbname,
           "-Fc", "-Z", "6", "--no-owner"]
    # Schémata, na která app uživatel nemá práva (vlastník postgres apod.) — mimo DR dump.
    for _sch in (os.environ.get("DR_EXCLUDE_SCHEMAS", "bak") or "").split(","):
        _sch = _sch.strip()
        if _sch:
            cmd += ["--exclude-schema", _sch]
    cmd += ["-f", outfile]
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    return cmd, env, host, dbname, pg_dump


def _write_meta(d: dict):
    try:
        with open(_META, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


def _building_age():
    try:
        return time.time() - os.path.getmtime(_BUILDING)
    except Exception:
        return None


def _do_dump():
    part = _DUMP + ".part"
    try:
        os.makedirs(_TMP, exist_ok=True)
        cmd, env, _h, _d, _p = _pgdump_cmd(part)
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=3600,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            _write_meta({"ok": False, "error": (r.stderr or r.stdout or "")[:500],
                         "at": datetime.now(timezone.utc).isoformat()})
            try:
                os.remove(part)
            except Exception:
                pass
            return
        os.replace(part, _DUMP)
        st = os.stat(_DUMP)
        _write_meta({"ok": True, "name": os.path.basename(_DUMP), "size": st.st_size,
                     "mtime": int(st.st_mtime), "at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        _write_meta({"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400]),
                     "at": datetime.now(timezone.utc).isoformat()})
    finally:
        try:
            os.remove(_BUILDING)
        except Exception:
            pass


@drops_router.get("/dr/meta")
async def dr_meta(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    try:
        _cmd, _env, host, dbname, pg_dump = _pgdump_cmd(os.path.join(_TMP, "_probe"))
    except Exception as e:
        return JSONResponse({"ok": False, "error": "not_ready", "detail": str(e)[:300]})
    return JSONResponse({"ok": True, "mode": "decouple pg_dump→file→download",
                         "db": dbname, "host": host, "pg_dump": pg_dump, "tmp": _TMP})


@drops_router.get("/dr/prepare")
async def dr_prepare(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    with _lock:
        age = _building_age()
        if age is not None and age < _MAX_BUILD_AGE:
            return JSONResponse({"ok": True, "status": "building", "age_s": int(age)})
        try:
            _pgdump_cmd(_DUMP + ".part")  # validace configu (nespouští)
        except Exception as e:
            return JSONResponse({"ok": False, "error": "not_ready", "detail": str(e)[:300]}, status_code=500)
        os.makedirs(_TMP, exist_ok=True)
        with open(_BUILDING, "w", encoding="utf-8") as f:
            f.write(datetime.now(timezone.utc).isoformat())
        threading.Thread(target=_do_dump, daemon=True).start()
        return JSONResponse({"ok": True, "status": "started"})


@drops_router.get("/dr/status")
async def dr_status(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    age = _building_age()
    if age is not None and age < _MAX_BUILD_AGE:
        return JSONResponse({"ok": True, "ready": False, "building": True, "age_s": int(age)})
    last = {}
    try:
        with open(_META, "r", encoding="utf-8") as f:
            last = json.load(f)
    except Exception:
        pass
    if os.path.isfile(_DUMP):
        st = os.stat(_DUMP)
        return JSONResponse({"ok": True, "ready": True, "building": False, "size": st.st_size,
                             "mtime": int(st.st_mtime), "age_s": int(time.time() - st.st_mtime), "last": last})
    return JSONResponse({"ok": True, "ready": False, "building": False, "last": last})


@drops_router.get("/dr/download")
async def dr_download(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    if not os.path.isfile(_DUMP):
        return JSONResponse({"ok": False, "error": "not_ready",
                             "hint": "zavolej /dr/prepare a počkej na /dr/status ready"}, status_code=404)
    return FileResponse(_DUMP, media_type="application/octet-stream", filename=os.path.basename(_DUMP))
