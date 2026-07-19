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
