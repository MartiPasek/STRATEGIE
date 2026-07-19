"""DR: streaming přenos posledního data_db dumpu Praha → Plzeň (Claude ID23, 19.7.2026).

Machine-to-machine, token v hlavičce X-DR-Token = env DR_TRANSFER_TOKEN.
  GET /api/v1/ops/dr/latest-dump/meta → JSON {ok,name,size,mtime,root}
  GET /api/v1/ops/dr/latest-dump      → stream souboru (FileResponse, žádný 50 MB strop base64 mostu)
Kořen dumpů = env DR_DUMP_ROOT (default E:\\STRATEGIE, může být i UNC).
Plzeň tahá přes scripts/dr/fetch_dump.ps1 (WebClient stream → Incoming → restore).
"""
from __future__ import annotations

import glob
import hmac
import os

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

drops_router = APIRouter(prefix="/api/v1/ops", tags=["dr-ops"])

_DUMP_ROOT = os.environ.get("DR_DUMP_ROOT", r"E:\STRATEGIE")


def _token_ok(req: Request):
    want = os.environ.get("DR_TRANSFER_TOKEN", "")
    if not want:
        return None  # not configured on server
    got = req.headers.get("X-DR-Token", "") or ""
    return hmac.compare_digest(got, want)


def _latest_dump():
    files = []
    for pat in (os.path.join(_DUMP_ROOT, "*", "*.dump"), os.path.join(_DUMP_ROOT, "*.dump")):
        files.extend(glob.glob(pat))
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]


def _guard(req: Request):
    ok = _token_ok(req)
    if ok is None:
        return JSONResponse({"ok": False, "error": "token_not_configured",
                             "hint": "nastav DR_TRANSFER_TOKEN v env API serveru"}, status_code=503)
    if not ok:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return None


@drops_router.get("/dr/latest-dump/meta")
async def dr_latest_meta(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    f = _latest_dump()
    if not f:
        return JSONResponse({"ok": False, "error": "no_dump", "root": _DUMP_ROOT,
                             "hint": "kořen není vidět nebo je prázdný — zkontroluj DR_DUMP_ROOT / dosah API na dump box"})
    st = os.stat(f)
    return JSONResponse({"ok": True, "name": os.path.basename(f), "size": st.st_size,
                         "mtime": int(st.st_mtime), "root": _DUMP_ROOT})


@drops_router.get("/dr/latest-dump")
async def dr_latest_dump(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    f = _latest_dump()
    if not f:
        return JSONResponse({"ok": False, "error": "no_dump", "root": _DUMP_ROOT}, status_code=404)
    return FileResponse(f, media_type="application/octet-stream", filename=os.path.basename(f))
