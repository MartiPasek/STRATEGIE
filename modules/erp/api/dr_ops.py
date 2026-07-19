"""DR: streaming ZIVY pg_dump data_db Praha (API 188.11 → DB 188.12) → Plzeň.
Claude ID23, 19.7.2026 (r3: stream místo file-serve — API nevidí E: na 188.12).

Machine-to-machine, token X-DR-Token (env DR_TRANSFER_TOKEN nebo soubor <repo>/dr_token.txt).
  GET /api/v1/ops/dr/meta         → JSON {ok, mode, db, host, pg_dump} (readiness bez dumpu)
  GET /api/v1/ops/dr/stream-dump  → StreamingResponse (živý pg_dump -Fc -Z6, žádný soubor/sdílení)

Reuse pg_dump resolveru + DB URL parseru z admin.backup_service (API to už umí).
Plzeň tahá scripts/dr/fetch_dump.ps1 (WebClient stream → Incoming → restore).
"""
from __future__ import annotations

import hmac
import os
import pathlib
import subprocess
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from core.config import settings
from modules.admin.application.backup_service import _parse_db_url, _resolve_pg_dump

drops_router = APIRouter(prefix="/api/v1/ops", tags=["dr-ops"])

_REPO = str(pathlib.Path(__file__).resolve().parents[3])
_TOKEN_FILE = os.environ.get("DR_TOKEN_FILE", "") or os.path.join(_REPO, "dr_token.txt")


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
        return JSONResponse({"ok": False, "error": "token_not_configured",
                             "hint": "vytvoř %s s tajným tokenem (nebo env DR_TRANSFER_TOKEN)" % _TOKEN_FILE},
                            status_code=503)
    got = req.headers.get("X-DR-Token", "") or ""
    if not hmac.compare_digest(got, want):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return None


def _pgdump_cmd():
    pg_dump = _resolve_pg_dump()
    host, port, user, password, dbname = _parse_db_url(settings.database_url)
    cmd = [pg_dump, "-h", host, "-p", port, "-U", user, "-d", dbname,
           "-Fc", "-Z", "6", "--no-owner"]
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    return cmd, env, host, dbname, pg_dump


@drops_router.get("/dr/meta")
async def dr_meta(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    try:
        _cmd, _env, host, dbname, pg_dump = _pgdump_cmd()
    except Exception as e:
        return JSONResponse({"ok": False, "error": "not_ready", "detail": str(e)[:300]})
    return JSONResponse({"ok": True, "mode": "live-pg_dump", "db": dbname, "host": host,
                         "pg_dump": pg_dump, "name_hint": "data_db_<ts>.dump"})


@drops_router.get("/dr/stream-dump")
async def dr_stream_dump(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    try:
        cmd, env, _host, _db, _pg = _pgdump_cmd()
    except Exception as e:
        return JSONResponse({"ok": False, "error": "not_ready", "detail": str(e)[:300]}, status_code=500)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    def _gen():
        try:
            while True:
                chunk = proc.stdout.read(262144)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass
            proc.wait()

    fname = "data_db_%s.dump" % datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(_gen(), media_type="application/octet-stream",
                             headers={"Content-Disposition": 'attachment; filename="%s"' % fname})
