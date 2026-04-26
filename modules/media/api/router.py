"""
Multimedia REST API (Faze 12a).

Base: /api/v1/media

Endpointy:
  POST   /upload          -- multipart/form-data upload
  GET    /                -- list (filter persona_id, kind, limit)
  GET    /{id}/meta       -- JSON metadata
  GET    /{id}/raw        -- binary content (FileResponse)
  GET    /{id}/preview    -- thumbnail JPEG (image only)
  DELETE /{id}            -- soft delete

Auth: cookie 'user_id' (analog ostatnich modulu). Tenant scope se resi
v service vrstve (rodicovsky bypass pro is_marti_parent=True).

Rate limit: settings.media_rate_limit_per_user_per_hour (default 50/h).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.media.application import service as media_service
from modules.media.application.service import (
    MediaValidationError,
    MediaStorageError,
)

logger = get_logger("media.api")

router = APIRouter(prefix="/api/v1/media", tags=["media"])


# ── Auth helper ────────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _get_user_context(user_id: int, conversation_id: int | None = None) -> dict:
    """
    Nacte user info pro upload.

    tenant_id: z User.last_active_tenant_id (kde Marti zrovna sedi).
    persona_id:
      - Primarne z Conversation.active_agent_id (kdyz user uploaduje
        do existujici konverzace, persona je defacto vlastnik media).
      - Fallback: bez persony (NULL = system / orphan upload).
    """
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u is None:
            raise HTTPException(status_code=401, detail="User neexistuje.")
        tenant_id = u.last_active_tenant_id
    finally:
        cs.close()

    persona_id: int | None = None
    if conversation_id is not None:
        from core.database_data import get_data_session
        from modules.core.infrastructure.models_data import Conversation
        ds = get_data_session()
        try:
            conv = ds.query(Conversation).filter_by(id=conversation_id).first()
            if conv is not None:
                persona_id = conv.active_agent_id
        finally:
            ds.close()

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "persona_id": persona_id,
    }


# ── In-memory rate limiter (per user, sliding hour window) ──────────────────

_rate_lock = Lock()
_rate_buckets: dict[int, deque[float]] = defaultdict(deque)


def _check_rate_limit(user_id: int) -> None:
    """Sliding 1h window. Ulozime timestampy uploadu, vyhodime starsi nez 1h."""
    limit = settings.media_rate_limit_per_user_per_hour
    now = time.time()
    cutoff = now - 3600
    with _rate_lock:
        bucket = _rate_buckets[user_id]
        # Remove starsi
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit: {limit} uploadu/hod. Zkus to za chvili."
                ),
            )
        bucket.append(now)


# ── POST /upload ────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload(
    req: Request,
    file: UploadFile = File(...),
    persona_id: int | None = Form(None),
    conversation_id: int | None = Form(None),
    source: str = Form("upload"),
):
    """
    Nahravani souboru z UI (multipart/form-data).

    Required: `file` (binary blob).
    Optional: persona_id (default z user.last_active_agent_id),
              conversation_id (kdyz patri ke konkretni konverzaci),
              source ('upload' | 'voice_memo' | atd.).

    Vraci JSON: kompletni MediaFile metadata vcetne id.
    """
    user_id = _get_uid(req)
    _check_rate_limit(user_id)
    ctx = _get_user_context(user_id, conversation_id=conversation_id)

    # Persona override / default
    effective_persona = persona_id if persona_id is not None else ctx["persona_id"]

    # Read content (FastAPI nam to dava jako stream)
    try:
        content = await file.read()
    except Exception as e:
        logger.exception(f"MEDIA | upload read failed | {e}")
        raise HTTPException(status_code=400, detail=f"Chyba cteni souboru: {e}")

    if not content:
        raise HTTPException(status_code=400, detail="Prazdny soubor.")

    # MIME type: bereme z UploadFile.content_type (browser/client si o tom rekne).
    # Server-side validace v storage_service (whitelist + Pillow image dimensions
    # = de-facto magic bytes check pro images).
    # Faze 12b fix: nektere browsery posilaji parametrizovany mime, napr.
    # Chrome MediaRecorder vraci `audio/webm;codecs=opus`. Storage MIME whitelist
    # dela exact match -- ostrihame parametry pred validaci.
    mime_type = (file.content_type or "").lower().strip()
    if ";" in mime_type:
        mime_type = mime_type.split(";", 1)[0].strip()
    if not mime_type:
        raise HTTPException(status_code=400, detail="Chybi Content-Type.")

    try:
        result = media_service.upload_media(
            content,
            mime_type=mime_type,
            user_id=ctx["user_id"],
            persona_id=effective_persona,
            tenant_id=ctx["tenant_id"],
            conversation_id=conversation_id,
            source=source,
            original_filename=file.filename,
        )
    except MediaValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MediaStorageError as e:
        logger.exception(f"MEDIA | upload storage failed | {e}")
        raise HTTPException(status_code=500, detail=f"Storage chyba: {e}")

    # Faze 12b: po audio uploadu (jen u nove vlozenych radek, ne u dedup hits)
    # zaradime media_transcribe task -- worker ho zpracuje pres Whisper.
    if (
        settings.whisper_enabled
        and result.get("kind") == "audio"
        and not result.get("processed_at")  # jeste neni transkribovano (dedup hit
        and not result.get("transcript")     # by mohl mit prepis z drivejsiho)
    ):
        try:
            from modules.tasks.application import service as task_service
            fname = result.get("original_filename") or f"audio_{result['id']}"
            t = task_service.create_task_from_source(
                tenant_id=ctx["tenant_id"],
                persona_id=effective_persona,
                source_type="media_transcribe",
                source_id=result["id"],
                title=f"Transkripce: {fname}",
                description=(
                    f"Whisper prepis audio souboru media_files.id={result['id']}. "
                    f"Po dokonceni vysledek bude v media_files.transcript."
                ),
                priority="normal",
            )
            logger.info(
                f"MEDIA | enqueued media_transcribe | task_id={t['id']} | "
                f"media_id={result['id']} | persona_id={effective_persona}"
            )
        except Exception as e:
            # Enqueue selhal -- upload je hotov, ale transkripce nepojede.
            # Marti muze manualne re-trigger pres POST /api/v1/media/{id}/transcribe
            # (nebo pres AI tool extract_from_audio v 12b-3, ktery si task vyrobi sam).
            logger.warning(
                f"MEDIA | media_transcribe enqueue failed | media_id={result['id']} | {e}"
            )

    return JSONResponse(content=result, status_code=201)


# ── GET / (list) ────────────────────────────────────────────────────────────

@router.get("/")
def list_media(
    req: Request,
    persona_id: int | None = None,
    kind: str | None = None,
    limit: int = 50,
):
    """
    Seznam media (filter persona_id, kind, limit). Rodic vidi cross-tenant.
    """
    user_id = _get_uid(req)
    rows = media_service.list_media(
        user_id=user_id,
        persona_id=persona_id,
        kind=kind,
        limit=limit,
    )
    return {"items": rows, "count": len(rows)}


# ── GET /{id}/meta ──────────────────────────────────────────────────────────

@router.get("/{media_id}/meta")
def get_meta(media_id: int, req: Request):
    """JSON metadata o media file."""
    user_id = _get_uid(req)
    row = media_service.get_media(media_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Media neexistuje nebo neni viditelne.")
    return row


# ── GET /{id}/raw ───────────────────────────────────────────────────────────

@router.get("/{media_id}/raw")
def get_raw(media_id: int, req: Request):
    """
    Binary content -- streamuje soubor z FS pres FileResponse.
    Setuje Content-Type podle DB mime_type, Content-Disposition inline
    (browser ho zobrazi misto download).
    """
    user_id = _get_uid(req)
    serving = media_service.get_media_for_serving(media_id, user_id)
    if serving is None:
        raise HTTPException(status_code=404, detail="Media neexistuje nebo neni viditelne.")
    row, abs_path = serving

    return FileResponse(
        abs_path,
        media_type=row.mime_type,
        filename=row.original_filename or f"media_{media_id}",
        # inline = browser zobrazi (image/audio), ne download
        headers={"Content-Disposition": "inline"},
    )


# ── GET /{id}/preview ───────────────────────────────────────────────────────

@router.get("/{media_id}/preview")
def get_preview(media_id: int, req: Request):
    """
    Thumbnail JPEG (jen pro images). Pokud thumbnail neexistuje, vygeneruje ho.
    Pokud media neni image, vrati 415.
    """
    user_id = _get_uid(req)
    abs_path = media_service.get_thumbnail_for_serving(media_id, user_id)
    if abs_path is None:
        raise HTTPException(
            status_code=415,
            detail="Preview neni dostupny (jen pro images).",
        )
    return FileResponse(
        abs_path,
        media_type="image/jpeg",
        headers={"Content-Disposition": "inline"},
    )


# ── DELETE /{id} ────────────────────────────────────────────────────────────

@router.delete("/{media_id}")
def delete_media(media_id: int, req: Request):
    """Soft delete (deleted_at SET). Fyzicke mazani souboru pres retention cron."""
    user_id = _get_uid(req)
    ok = media_service.soft_delete_media(media_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Media neexistuje nebo nemas pravo.")
    return {"ok": True, "id": media_id}
