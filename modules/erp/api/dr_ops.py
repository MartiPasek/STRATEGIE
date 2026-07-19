"""DR: streaming přenos posledního data_db dumpu Praha → Plzeň (Claude ID23, 19.7.2026).

Machine-to-machine, token v hlavičce X-DR-Token.
  GET /api/v1/ops/dr/latest-dump/meta → JSON {ok,name,size,mtime,root}
  GET /api/v1/ops/dr/latest-dump      → stream souboru (FileResponse, žádný 50 MB strop mostu)

Token (bez NSSM zásahu): env DR_TRANSFER_TOKEN, jinak soubor DR_TOKEN_FILE
(default <repo>/dr_token.txt — stačí ho na APP boxu vytvořit, čte se za běhu, bez restartu).
Kořen dumpů: env DR_DUMP_ROOT, jinak první existující z [E:\\STRATEGIE, \\\\10.200.188.12\\E$\\STRATEGIE]
(API běží na 188.11, dumpy na 188.12 → UNC admin share).
Plzeň tahá scripts/dr/fetch_dump.ps1 (WebClient stream → Incoming → restore).
"""
from __future__ import annotations

import glob
import hmac
import os
import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

drops_router = APIRouter(prefix="/api/v1/ops", tags=["dr-ops"])

_REPO = str(pathlib.Path(__file__).resolve().parents[3])
_TOKEN_FILE = os.environ.get("DR_TOKEN_FILE", "") or os.path.join(_REPO, "dr_token.txt")
_DUMP_CANDIDATES = [r"E:\STRATEGIE", r"\\10.200.188.12\E$\STRATEGIE"]


def _token() -> str:
    t = (os.environ.get("DR_TRANSFER_TOKEN", "") or "").strip()
    if t:
        return t
    try:
        with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _dump_root() -> str:
    env = (os.environ.get("DR_DUMP_ROOT", "") or "").strip()
    for c in ([env] if env else []) + _DUMP_CANDIDATES:
        try:
            if c and os.path.isdir(c):
                return c
        except Exception:
            pass
    return env or _DUMP_CANDIDATES[0]


def _latest_dump():
    root = _dump_root()
    files = []
    for pat in (os.path.join(root, "*", "*.dump"), os.path.join(root, "*.dump")):
        try:
            files.extend(glob.glob(pat))
        except Exception:
            pass
    if not files:
        return None, root
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0], root


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


@drops_router.get("/dr/latest-dump/meta")
async def dr_latest_meta(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    f, root = _latest_dump()
    if not f:
        return JSONResponse({"ok": False, "error": "no_dump", "root": root,
                             "hint": "kořen není vidět nebo je prázdný — zkontroluj dosah API na dump box / DR_DUMP_ROOT"})
    st = os.stat(f)
    return JSONResponse({"ok": True, "name": os.path.basename(f), "size": st.st_size,
                         "mtime": int(st.st_mtime), "root": root})


@drops_router.get("/dr/latest-dump")
async def dr_latest_dump(req: Request):
    g = _guard(req)
    if g is not None:
        return g
    f, root = _latest_dump()
    if not f:
        return JSONResponse({"ok": False, "error": "no_dump", "root": root}, status_code=404)
    return FileResponse(f, media_type="application/octet-stream", filename=os.path.basename(f))
