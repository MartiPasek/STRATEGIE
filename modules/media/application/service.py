"""
Multimedia business service (Faze 12a).

Business logic nad storage_service: vola FS layer + DB CRUD + auth scope.

Public API:
  - upload_media(content, mime_type, ..., user_id, persona_id, tenant_id, ...)
      -> dict s MediaFile metadata. Vola storage_service.save_file +
      vytvori MediaFile row. Pokud deduplicated (stejny sha256 v ramci
      stejne persony), vrati existujici row.
  - get_media(media_id, user_id) -> dict | None
      Vrati MediaFile + auth check (user musi byt v stejnem tenantu).
  - list_media(persona_id, kind, limit) -> list[dict]
  - soft_delete_media(media_id, user_id) -> bool
      Set deleted_at na DB row, FS soubor zatim necha (retention cron later).
  - attach_to_message(media_ids, message_id) -> int
      Late-fill pattern: po save_message() se zavola, doplni message_id na
      vsechny media_files row.
"""
from __future__ import annotations

from datetime import datetime, timezone

from core.database_data import get_data_session
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import MediaFile
from modules.core.infrastructure.models_core import User

from . import storage_service
from .storage_service import (
    MediaStorageError,
    MediaValidationError,
    MIME_TO_EXT,
)

logger = get_logger("media.service")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_dict(row: MediaFile) -> dict:
    """Serializuje MediaFile row do JSON-friendly dictu (pro API response)."""
    return {
        "id": row.id,
        "persona_id": row.persona_id,
        "user_id": row.user_id,
        "tenant_id": row.tenant_id,
        "conversation_id": row.conversation_id,
        "message_id": row.message_id,
        "kind": row.kind,
        "source": row.source,
        "mime_type": row.mime_type,
        "file_size": row.file_size,
        "sha256": row.sha256,
        "storage_provider": row.storage_provider,
        "storage_path": row.storage_path,
        "original_filename": row.original_filename,
        "width": row.width,
        "height": row.height,
        "duration_ms": row.duration_ms,
        "transcript": row.transcript,
        "description": row.description,
        "ai_metadata": row.ai_metadata,
        "processed_at": row.processed_at.isoformat() if row.processed_at else None,
        "processing_error": row.processing_error,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# ── Auth helper (cross-tenant view pro rodice) ──────────────────────────────

def _user_can_see(user_id: int, media: MediaFile) -> bool:
    """
    Auth check: user smi cist media pokud:
      - je rodic (is_marti_parent=True) -- cross-tenant view, jako u SMS/memory
      - jeho last_active_tenant_id sedi s media.tenant_id
      - media.tenant_id je NULL (system / orphan)

    Pattern: konzistentni s sms_ui_router._is_marti_parent (Faze 11-darek).
    """
    if media.tenant_id is None:
        return True  # system/orphan -- viditelne pro autentizovaneho usera
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u is None:
            return False
        if getattr(u, "is_marti_parent", False):
            return True
        return u.last_active_tenant_id == media.tenant_id
    finally:
        cs.close()


# ── Upload ──────────────────────────────────────────────────────────────────

def upload_media(
    content: bytes,
    *,
    mime_type: str,
    user_id: int | None,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    conversation_id: int | None = None,
    source: str = "upload",
    original_filename: str | None = None,
) -> dict:
    """
    Hlavni vstupni bod pro nahravani souboru.

    Flow:
      1. storage_service.save_file (atomic FS write, sha256, dedup, thumbnail)
      2. DB lookup: pokud row se stejnym sha256 + persona_id existuje, vratime ji
         (merge: pridame conversation_id pokud je novy)
      3. Jinak vytvoreni nove MediaFile row.

    Vraci dict s metadata. Validacni chyby (MIME, velikost) -> MediaValidationError.
    """
    storage_meta = storage_service.save_file(
        content,
        persona_id=persona_id,
        mime_type=mime_type,
        original_filename=original_filename,
    )

    ds = get_data_session()
    try:
        # Dedup lookup -- pokud user/persona uz tenhle soubor nahral, vratime existujici row
        existing = (
            ds.query(MediaFile)
            .filter(
                MediaFile.sha256 == storage_meta["sha256"],
                MediaFile.persona_id == persona_id,
                MediaFile.deleted_at.is_(None),
            )
            .first()
        )
        if existing is not None:
            # Pripadne pripoj k nove konverzaci (existujici media muze byt forwarded)
            if conversation_id is not None and existing.conversation_id is None:
                existing.conversation_id = conversation_id
                ds.commit()
            ds.refresh(existing)
            logger.info(
                f"MEDIA | upload dedup hit | id={existing.id} | "
                f"sha256={storage_meta['sha256'][:8]}..."
            )
            return _row_to_dict(existing)

        # Novy row
        row = MediaFile(
            persona_id=persona_id,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            kind=storage_meta["kind"],
            source=source,
            mime_type=storage_meta["mime_type"],
            file_size=storage_meta["file_size"],
            sha256=storage_meta["sha256"],
            storage_provider="local",
            storage_path=storage_meta["storage_path"],
            original_filename=storage_meta.get("original_filename"),
            width=storage_meta.get("width"),
            height=storage_meta.get("height"),
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        logger.info(
            f"MEDIA | upload new | id={row.id} | kind={row.kind} | "
            f"persona_id={persona_id} | tenant_id={tenant_id}"
        )
        return _row_to_dict(row)
    finally:
        ds.close()


# ── Retrieve ────────────────────────────────────────────────────────────────

def get_media(media_id: int, user_id: int) -> dict | None:
    """
    Nacte MediaFile row + auth check. Vrati None pokud row neexistuje
    nebo user nema access. Soft-deleted rows nejsou viditelne.
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(MediaFile)
            .filter(MediaFile.id == media_id, MediaFile.deleted_at.is_(None))
            .first()
        )
        if row is None:
            return None
        if not _user_can_see(user_id, row):
            return None
        return _row_to_dict(row)
    finally:
        ds.close()


def get_media_for_serving(media_id: int, user_id: int) -> tuple[MediaFile, str] | None:
    """
    Vrati (MediaFile row, abs_storage_path) pro file serving (raw / preview).
    Pouziva se v API endpointu pred FileResponse.
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(MediaFile)
            .filter(MediaFile.id == media_id, MediaFile.deleted_at.is_(None))
            .first()
        )
        if row is None:
            return None
        if not _user_can_see(user_id, row):
            return None
        abs_path = str(storage_service.get_full_path(row.storage_path))
        # Detach z session pred returnem (caller pouziva fields, ale ne pripsat)
        ds.expunge(row)
        return row, abs_path
    finally:
        ds.close()


def get_thumbnail_for_serving(media_id: int, user_id: int) -> str | None:
    """
    Vrati abs path k thumbnailu (jen pro images). None pokud neni image
    nebo user nema access. Pokud thumbnail neexistuje, zkusi ho vygenerovat.
    """
    serving = get_media_for_serving(media_id, user_id)
    if serving is None:
        return None
    row, _ = serving
    if not row.mime_type.startswith("image/"):
        return None
    try:
        thumb_storage_path = storage_service.generate_thumbnail(row.storage_path)
        return str(storage_service.get_full_path(thumb_storage_path))
    except MediaStorageError as e:
        logger.warning(f"MEDIA | thumbnail serve | media_id={media_id} | {e}")
        return None


# ── List ────────────────────────────────────────────────────────────────────

def list_media(
    *,
    user_id: int,
    persona_id: int | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Seznam media (default scope: aktivni tenant usera, pripadne persona filter).
    Rodic vidi cross-tenant.
    """
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u is None:
            return []
        is_parent = bool(getattr(u, "is_marti_parent", False))
        tenant_scope = u.last_active_tenant_id
    finally:
        cs.close()

    ds = get_data_session()
    try:
        q = ds.query(MediaFile).filter(MediaFile.deleted_at.is_(None))
        if not is_parent and tenant_scope is not None:
            q = q.filter(MediaFile.tenant_id == tenant_scope)
        if persona_id is not None:
            q = q.filter(MediaFile.persona_id == persona_id)
        if kind is not None:
            q = q.filter(MediaFile.kind == kind)
        rows = (
            q.order_by(MediaFile.created_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )
        return [_row_to_dict(r) for r in rows]
    finally:
        ds.close()


# ── Soft delete ─────────────────────────────────────────────────────────────

def soft_delete_media(media_id: int, user_id: int) -> bool:
    """
    Soft delete: nastavi deleted_at. FS soubor zustava, retention cron ho
    fyzicky smaze pozdeji.
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(MediaFile)
            .filter(MediaFile.id == media_id, MediaFile.deleted_at.is_(None))
            .first()
        )
        if row is None:
            return False
        if not _user_can_see(user_id, row):
            return False
        row.deleted_at = _now_utc()
        ds.commit()
        logger.info(f"MEDIA | soft delete | media_id={media_id} | user_id={user_id}")
        return True
    finally:
        ds.close()


# ── Late-fill: attach k message po save_message ─────────────────────────────

def attach_to_message(media_ids: list[int], message_id: int) -> int:
    """
    Late-fill pattern (Q5 z design doc): upload probehne pred save_message,
    composer dostane media_ids v request, po save_message zavolame tuhle
    funkci pro doplneni FK.

    POZN: VYNECHAVAME 'IS NULL' filter -- pri dedup hit (stejny sha256
    uploadnuty znovu, treba do nove konverzace) by jinak attach selhal,
    protoze existujici row jiz ma message_id z drivejsiho uploadu.
    Last-attach-wins -- image patri posledni zprave, ktera ho poslala.
    Pro multi-attach (jeden image v nekolika zpravach) bude treba
    message_media_links table (variant C z multimedia.md, future).

    Vraci pocet updatovanych rows.
    """
    if not media_ids:
        return 0
    ds = get_data_session()
    try:
        updated = (
            ds.query(MediaFile)
            .filter(MediaFile.id.in_(media_ids))
            .update({"message_id": message_id}, synchronize_session=False)
        )
        ds.commit()
        if updated:
            logger.info(
                f"MEDIA | late-fill | message_id={message_id} | "
                f"updated={updated} | requested={len(media_ids)}"
            )
        return updated
    finally:
        ds.close()


# ── AI processing helpers (description / transcript persist) ────────────────

def save_description(media_id: int, description: str | None = None, ai_metadata: dict | None = None) -> bool:
    """
    Po describe_image / read_text_from_image AI tool ulozi vystup do DB.

    description=None: zachova existujici (jen update ai_metadata) -- vhodne
    pro OCR co ma vlastni storage v ai_metadata.ocr_text.
    """
    ds = get_data_session()
    try:
        row = ds.query(MediaFile).filter_by(id=media_id).first()
        if row is None:
            return False
        if description is not None:
            row.description = description
        if ai_metadata is not None:
            row.ai_metadata = (row.ai_metadata or {}) | ai_metadata
        row.processed_at = _now_utc()
        row.processing_error = None
        ds.commit()
        return True
    finally:
        ds.close()


def save_transcript(media_id: int, transcript: str, ai_metadata: dict | None = None) -> bool:
    """Po transcribe_audio AI tool ulozi prepis do DB (pro Faze 12b)."""
    ds = get_data_session()
    try:
        row = ds.query(MediaFile).filter_by(id=media_id).first()
        if row is None:
            return False
        row.transcript = transcript
        if ai_metadata is not None:
            row.ai_metadata = (row.ai_metadata or {}) | ai_metadata
        row.processed_at = _now_utc()
        row.processing_error = None
        ds.commit()
        return True
    finally:
        ds.close()


def save_processing_error(media_id: int, error: str) -> bool:
    """Po failnute AI processing ulozi chybu (debug + UI feedback)."""
    ds = get_data_session()
    try:
        row = ds.query(MediaFile).filter_by(id=media_id).first()
        if row is None:
            return False
        row.processing_error = error[:500]  # cap pro DB column
        row.processed_at = _now_utc()
        ds.commit()
        return True
    finally:
        ds.close()


# Re-export validation/storage chyb pro pohodlne handling v router/handler
__all__ = [
    "upload_media",
    "get_media",
    "get_media_for_serving",
    "get_thumbnail_for_serving",
    "list_media",
    "soft_delete_media",
    "attach_to_message",
    "save_description",
    "save_transcript",
    "save_processing_error",
    "MediaValidationError",
    "MediaStorageError",
    "MIME_TO_EXT",
]
