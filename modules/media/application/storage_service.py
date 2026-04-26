"""
Multimedia storage service -- FS layer (Faze 12a).

Storage strategy: lokalni filesystem pod MEDIA_STORAGE_ROOT, persona/sha256
sharding. Atomic write (temp + rename), sha256-based dedup, eager thumbnail
generation pro images.

Path scheme:
  {MEDIA_STORAGE_ROOT}/{persona_id}/{sha256[:2]}/{sha256}.{ext}
  thumbnails: same dir, {sha256}_thumb.jpg

Public API:
  - save_file(content, persona_id, mime_type, original_filename)
      -> {sha256, storage_path, file_size, width, height, ...}
      Atomicke ulozeni + sha256 + image dimensions detection.
  - read_file(storage_path) -> bytes
  - get_full_path(storage_path) -> Path  (FS abs path)
  - generate_thumbnail(storage_path, max_size) -> str (thumb relative path)
  - delete_file(storage_path) -- fyzicke smazani souboru z FS

Provider-agnostic v budoucnu: aktualne 'local'. Future S3/R2 abstrakce
prijde v MediaStorageProvider interface (analog SmsProvider).
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError

from core.config import settings
from core.logging import get_logger

logger = get_logger("media.storage")

# Mutagen je optional dep -- pokud chybi v poetry env, audio upload pouze
# nedoplni duration_ms (NULL v DB), zbytek pipeline funguje. Nemusime
# blokovat upload jen protoze poetry lock je out of date.
try:
    import mutagen as _mutagen
    _MUTAGEN_AVAILABLE = True
except Exception as _e:  # pragma: no cover -- env-specific
    _mutagen = None
    _MUTAGEN_AVAILABLE = False
    logger.warning(
        f"MEDIA | mutagen not available, audio duration detection skipped: {_e}"
    )


# ── MIME -> extension mapping (pouze whitelist, ostatni rejectneme) ─────────

MIME_TO_EXT: dict[str, str] = {
    # Images
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    # Audio
    "audio/webm": "webm",
    "audio/m4a": "m4a",
    "audio/mp4": "m4a",      # Safari posila audio/mp4 pro m4a containery
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",     # standardni MIME pro mp3
    "audio/wav": "wav",
    "audio/x-wav": "wav",    # alternativni MIME pro wav
    "audio/ogg": "ogg",
}

# Images, kde umime detekovat width/height pres Pillow.
IMAGE_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
}

# Audio MIME types, kde umime detekovat duration pres mutagen (Faze 12b).
AUDIO_MIME_TYPES = {
    "audio/mpeg", "audio/mp3",
    "audio/m4a", "audio/mp4",
    "audio/wav", "audio/x-wav",
    "audio/ogg",
    "audio/webm",
}


class MediaStorageError(Exception):
    """Storage selhalo z technickych duvodu (FS, permissions, IO)."""


class MediaValidationError(ValueError):
    """Storage selhalo z duvodu user inputu (MIME nepovolen, velikost, atd.)."""


# ── Path generation ─────────────────────────────────────────────────────────

def _get_root() -> Path:
    """Vraci absolutni Path k MEDIA_STORAGE_ROOT, vytvori adresar pokud neexistuje."""
    root = Path(settings.media_storage_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_full_path(storage_path: str) -> Path:
    """
    Z relativni storage_path (jak je v DB) odvodi absolutni FS path.

    Storage path format: '{persona_id}/{sha256[:2]}/{sha256}.{ext}'
    """
    return _get_root() / storage_path


def _build_storage_path(persona_id: int | None, sha256: str, ext: str) -> str:
    """
    Postavi relativni storage_path. Ulozeni:
      <persona_id>/<sha256[:2]>/<sha256>.<ext>

    persona_id=None (system / orphan upload) -> '_system' folder.
    """
    persona_folder = str(persona_id) if persona_id is not None else "_system"
    shard = sha256[:2]
    filename = f"{sha256}.{ext}"
    # Forward slashes pro DB storage, OS-specific separator se vyresi v Path.
    return f"{persona_folder}/{shard}/{filename}"


# ── Save ────────────────────────────────────────────────────────────────────

def save_file(
    content: bytes,
    *,
    persona_id: int | None,
    mime_type: str,
    original_filename: str | None = None,
) -> dict:
    """
    Atomicky ulozi soubor na FS, vrati metadata pro DB row.

    Atomic = zapis do tmp souboru + os.replace() na finalni jmeno. Pri panicu
    uprostred zapisu nezustane half-written soubor pod finalnim jmenem.

    Deduplication: pokud soubor s tymto sha256 uz existuje na FS, neukladame
    znovu, jen vratime existujici path. (DB row se vyresi v service layer.)

    Vraci dict s fields, ktera se pak vkladaji do MediaFile row:
      {sha256, storage_path, file_size, mime_type, kind,
       width, height, deduplicated (bool)}
    """
    if not content:
        raise MediaValidationError("Prazdny obsah souboru.")

    file_size = len(content)
    if file_size > settings.media_max_upload_bytes:
        raise MediaValidationError(
            f"Soubor je prilis velky: {file_size} bytes "
            f"(limit {settings.media_max_upload_bytes})."
        )

    if mime_type not in MIME_TO_EXT:
        raise MediaValidationError(
            f"MIME typ '{mime_type}' neni v whitelist. "
            f"Povoleno: {', '.join(sorted(MIME_TO_EXT.keys()))}"
        )

    ext = MIME_TO_EXT[mime_type]
    sha256 = hashlib.sha256(content).hexdigest()
    storage_path = _build_storage_path(persona_id, sha256, ext)
    abs_path = get_full_path(storage_path)

    # Dedup check: stejny sha256 + persona = uz ulozeno
    deduplicated = abs_path.exists()

    # Image dimensions detection (Pillow)
    width: int | None = None
    height: int | None = None
    if mime_type in IMAGE_MIME_TYPES:
        try:
            from io import BytesIO
            with Image.open(BytesIO(content)) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError) as e:
            logger.warning(
                f"MEDIA | image dimensions detection failed | "
                f"sha256={sha256[:8]}... | {e}"
            )

    # Audio duration detection (mutagen) -- Faze 12b. Optional dep:
    # pokud mutagen v env neni, duration_ms zustane None a upload pokracuje.
    duration_ms: int | None = None
    if mime_type in AUDIO_MIME_TYPES and _MUTAGEN_AVAILABLE:
        try:
            from io import BytesIO
            # Mutagen.File podporuje fileobj argument (cti z memory, ne z FS).
            # Returns None pokud format neni rozeznatelny -- pak duration_ms
            # zustane None (nullable v DB).
            audio = _mutagen.File(fileobj=BytesIO(content))
            if audio is not None and getattr(audio, "info", None) is not None:
                length_s = float(getattr(audio.info, "length", 0.0))
                duration_ms = int(round(length_s * 1000))
        except Exception as e:
            # Detekce neni blocker -- soubor lze ulozit i bez duration metadata.
            logger.warning(
                f"MEDIA | audio duration detection failed | "
                f"sha256={sha256[:8]}... | mime={mime_type} | {e}"
            )

    # Atomic write (jen pokud uz neexistuje -- jinak je to dedup hit)
    if not deduplicated:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        # Tmp v stejnem adresari (musi byt na same FS partition pro os.replace)
        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{sha256}_",
            suffix=f".{ext}.tmp",
            dir=abs_path.parent,
        )
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)
            os.replace(tmp_path, abs_path)
            tmp_path = None  # uspesne presunuto
        except Exception as e:
            logger.exception(f"MEDIA | save_file failed | sha256={sha256[:8]}... | {e}")
            raise MediaStorageError(f"Ulozeni selhalo: {e}") from e
        finally:
            # Cleanup tmp pokud zustal (neco selhalo pred os.replace)
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    # Eager thumbnail (jen pro images)
    if mime_type in IMAGE_MIME_TYPES and not deduplicated:
        try:
            generate_thumbnail(storage_path, settings.media_thumbnail_size)
        except Exception as e:
            # Thumbnail failure neni blocker -- file je ulozeny, jen UI
            # bude muset pouzit raw misto preview.
            logger.warning(
                f"MEDIA | thumbnail generation failed | "
                f"sha256={sha256[:8]}... | {e}"
            )

    kind = _detect_kind(mime_type)

    logger.info(
        f"MEDIA | save_file ok | persona_id={persona_id} | kind={kind} | "
        f"sha256={sha256[:8]}... | size={file_size} | dedup={deduplicated}"
    )

    return {
        "sha256": sha256,
        "storage_path": storage_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "kind": kind,
        "width": width,
        "height": height,
        "duration_ms": duration_ms,
        "deduplicated": deduplicated,
        "original_filename": original_filename,
    }


def _detect_kind(mime_type: str) -> str:
    """Z MIME typu odvodi kind (image/audio/video/document)."""
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    return "document"


# ── Read ────────────────────────────────────────────────────────────────────

def read_file(storage_path: str) -> bytes:
    """Nacte raw obsah souboru z FS."""
    abs_path = get_full_path(storage_path)
    if not abs_path.exists():
        raise MediaStorageError(f"Soubor neexistuje: {storage_path}")
    return abs_path.read_bytes()


# ── Thumbnails (eager pro images) ───────────────────────────────────────────

def get_thumbnail_path(storage_path: str) -> str:
    """Vraci storage_path pro thumbnail variantu (vedle puvodniho)."""
    p = Path(storage_path)
    # {sha256}.{ext} -> {sha256}_thumb.jpg
    stem = p.stem
    return str(p.parent / f"{stem}_thumb.jpg").replace("\\", "/")


def generate_thumbnail(storage_path: str, max_size: int = 800) -> str:
    """
    Vytvori zmenseny JPEG (max_size x max_size, fit-inside, quality 85)
    vedle originalniho souboru. Vraci storage_path thumbnailu.

    Idempotent: pokud thumbnail uz existuje, jen vrati path.
    """
    src_path = get_full_path(storage_path)
    if not src_path.exists():
        raise MediaStorageError(f"Source file neexistuje: {storage_path}")

    thumb_storage_path = get_thumbnail_path(storage_path)
    thumb_abs_path = get_full_path(thumb_storage_path)

    if thumb_abs_path.exists():
        return thumb_storage_path

    try:
        with Image.open(src_path) as img:
            # Konverze RGBA/P na RGB (JPEG nepodporuje alpha)
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Atomic write (tmp + replace)
            fd, tmp_path = tempfile.mkstemp(
                prefix=f".{thumb_abs_path.stem}_",
                suffix=".jpg.tmp",
                dir=thumb_abs_path.parent,
            )
            try:
                os.close(fd)
                img.save(tmp_path, "JPEG", quality=85, optimize=True)
                os.replace(tmp_path, thumb_abs_path)
                tmp_path = None
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
    except Exception as e:
        logger.exception(f"MEDIA | thumbnail | {e}")
        raise MediaStorageError(f"Thumbnail generation selhala: {e}") from e

    logger.info(f"MEDIA | thumbnail ok | {thumb_storage_path}")
    return thumb_storage_path


# ── Delete (soft / hard) ────────────────────────────────────────────────────

def delete_file_physical(storage_path: str) -> bool:
    """
    Fyzicky smaze soubor z FS (pro hard delete / retention cron).
    Soft delete (mazani DB rowy) ridi service layer, nemaze FS.
    Vraci True pokud bylo neco smazano.
    """
    abs_path = get_full_path(storage_path)
    if not abs_path.exists():
        return False
    try:
        abs_path.unlink()
        # Smazat thumbnail kdyz existuje
        thumb_path = get_full_path(get_thumbnail_path(storage_path))
        if thumb_path.exists():
            thumb_path.unlink()
        logger.info(f"MEDIA | physical delete ok | {storage_path}")
        return True
    except OSError as e:
        logger.error(f"MEDIA | physical delete failed | {storage_path} | {e}")
        raise MediaStorageError(f"Fyzicke mazani selhalo: {e}") from e
