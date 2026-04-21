"""
Avatar persony -- upload + serve.

Storage: {AVATARS_STORAGE_DIR}/persona_{id}.jpg
Resize: 256x256 (cover-fit), JPEG quality 85
Format: vse konvertujeme na JPEG (jednotny vystup, mensi velikost)

Doplneny do persona modelu pres avatar_path sloupec (migrace d2e7c4a9f1b3).
NULL = persona nema avatar -> frontend fallback na generovane iniciály.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

from core.config import settings
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import Persona

logger = get_logger("personas.avatar")

AVATAR_SIZE = 256
JPEG_QUALITY = 85
MAX_UPLOAD_BYTES = 5 * 1024 * 1024   # 5 MB


def _avatars_dir() -> Path:
    """Storage root pro avatary. Lazy create."""
    d = Path(settings.avatars_storage_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _avatar_path_for(persona_id: int) -> Path:
    return _avatars_dir() / f"persona_{persona_id}.jpg"


def save_avatar(persona_id: int, image_bytes: bytes) -> str:
    """
    Resize + ulozi avatar. Vraci absolutni cestu (ulozit do persona.avatar_path).

    - Resize na AVATAR_SIZE x AVATAR_SIZE (cover-fit -- crop na ctverec)
    - Konverze na JPEG quality 85 (i kdyz vstup byl PNG)
    - Pillow odhali nevalidni image a vyhodi exception -> caller vrati 400
    """
    if not image_bytes:
        raise ValueError("Prazdny soubor")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Soubor je vetsi nez {MAX_UPLOAD_BYTES // 1024 // 1024} MB")

    from PIL import Image, ImageOps   # markitdown[pdf,...] uz Pillow nainstaloval

    img = Image.open(io.BytesIO(image_bytes))
    # ImageOps.exif_transpose: respektuje EXIF orientation tag (telefon fotky)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    # ImageOps.fit: cover-fit (zachova aspect, crop center)
    img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    target = _avatar_path_for(persona_id)
    img.save(target, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    abs_path = str(target.absolute())

    # Update DB
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        if p:
            p.avatar_path = abs_path
            cs.commit()
    finally:
        cs.close()

    logger.info(f"AVATAR | saved | persona_id={persona_id} | path={abs_path}")
    return abs_path


def delete_avatar(persona_id: int) -> bool:
    """Smaze avatar (FS + DB). Vraci True pokud existoval."""
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        had_path = bool(p and p.avatar_path)
        if p:
            p.avatar_path = None
            cs.commit()
    finally:
        cs.close()

    target = _avatar_path_for(persona_id)
    if target.is_file():
        try:
            target.unlink()
        except Exception as e:
            logger.warning(f"AVATAR | delete failed | persona_id={persona_id} | error={e}")

    if had_path:
        logger.info(f"AVATAR | deleted | persona_id={persona_id}")
    return had_path


def get_avatar_path(persona_id: int) -> str | None:
    """Vraci absolutni cestu k avataru pokud existuje, jinak None."""
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        if not p or not p.avatar_path:
            return None
        if not os.path.isfile(p.avatar_path):
            # DB ma cestu, ale fyzicky soubor zmizel -- vyhodime DB referenci
            p.avatar_path = None
            cs.commit()
            return None
        return p.avatar_path
    finally:
        cs.close()
