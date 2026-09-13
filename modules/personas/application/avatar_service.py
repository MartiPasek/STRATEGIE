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


# ── Zaloha fotky v databazi (fw.persona_photo) ──────────────────────────────
# Zadal Jirka Honomichl 13.9.2026, schvalila Marti-AI (msg 15342).
# Duvod: nocni zaloha bere POUZE databazi -- soubory na aplikacnim serveru
# (vcetne teto slozky) v zalohovanem retezu NEJSOU. Navic kdyz soubor chybi,
# get_avatar_path drive rovnou vymazal cestu v DB, takze se fotka ztratila
# potichu (naostro se to stalo 13.9.2026). Proto: pri ulozeni jde kopie i do
# databaze a pri vydeji se z ni chybejici soubor OBNOVI -- teprve kdyz neni
# ani tam, cesta se vynuluje.

def _db_uloz(persona_id: int, image_bytes: bytes, mime: str = "image/jpeg",
             user_id: int | None = None) -> None:
    """Ulozi (nebo prepise) zalohu fotky persony v databazi."""
    from sqlalchemy import text as _sql
    cs = get_core_session()
    try:
        cs.execute(_sql("""
            INSERT INTO fw.persona_photo
                   (persona_id, mime, foto, velikost_b, nahrano_kdy, nahral_kdo)
            VALUES (:pid, :mime, :foto, :vel, now(), :uid)
            ON CONFLICT (persona_id) DO UPDATE
               SET mime = EXCLUDED.mime,
                   foto = EXCLUDED.foto,
                   velikost_b = EXCLUDED.velikost_b,
                   nahrano_kdy = now(),
                   nahral_kdo = EXCLUDED.nahral_kdo
        """), {"pid": int(persona_id), "mime": mime, "foto": image_bytes,
               "vel": len(image_bytes), "uid": user_id})
        cs.commit()
        logger.info(f"AVATAR | zaloha do DB | persona_id={persona_id} | "
                    f"bajtu={len(image_bytes)}")
    except Exception as e:
        cs.rollback()
        # Zaloha nesmi shodit samotne nahrani fotky -- soubor uz na disku je.
        logger.warning(f"AVATAR | zaloha do DB SELHALA | persona_id={persona_id} | {e}")
    finally:
        cs.close()


def _db_obnov(persona_id: int, cil: Path) -> bool:
    """Obnovi chybejici soubor ze zalohy v databazi. True = obnoveno."""
    from sqlalchemy import text as _sql
    cs = get_core_session()
    try:
        row = cs.execute(_sql(
            "SELECT foto FROM fw.persona_photo WHERE persona_id = :pid"
        ), {"pid": int(persona_id)}).first()
        if not row or not row[0]:
            return False
        data = bytes(row[0])
        cil.parent.mkdir(parents=True, exist_ok=True)
        cil.write_bytes(data)
        logger.warning(f"AVATAR | soubor chybel, OBNOVEN ze zalohy v DB | "
                       f"persona_id={persona_id} | bajtu={len(data)} | cesta={cil}")
        return True
    except Exception as e:
        logger.warning(f"AVATAR | obnova z DB selhala | persona_id={persona_id} | {e}")
        return False
    finally:
        cs.close()


def _db_smaz(persona_id: int) -> None:
    """Smaze zalohu fotky v databazi (volane pri smazani avataru)."""
    from sqlalchemy import text as _sql
    cs = get_core_session()
    try:
        cs.execute(_sql("DELETE FROM fw.persona_photo WHERE persona_id = :pid"),
                   {"pid": int(persona_id)})
        cs.commit()
    except Exception as e:
        cs.rollback()
        logger.warning(f"AVATAR | smazani zalohy v DB selhalo | persona_id={persona_id} | {e}")
    finally:
        cs.close()


def save_avatar(persona_id: int, image_bytes: bytes, user_id: int | None = None) -> str:
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

    # Zaloha do databaze -- disk se nezalohuje (13.9.2026, viz komentar vyse).
    _db_uloz(persona_id, target.read_bytes(), "image/jpeg", user_id)

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

    # Se souborem jde pryc i zaloha v DB -- jinak by se fotka pri pristim
    # vydeji sama obnovila (13.9.2026).
    _db_smaz(persona_id)

    if had_path:
        logger.info(f"AVATAR | deleted | persona_id={persona_id}")
    return had_path


def get_avatar_path(persona_id: int) -> str | None:
    """Vraci absolutni cestu k avataru pokud existuje, jinak None."""
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        if not p:
            return None

        # Cesta chybi (napr. ji driv vymazal tento kod) -- zkus zalohu v DB.
        if not p.avatar_path:
            vychozi = _avatar_path_for(persona_id)
            if vychozi.is_file() or _db_obnov(persona_id, vychozi):
                p.avatar_path = str(vychozi.absolute())
                cs.commit()
                return p.avatar_path
            return None

        if not os.path.isfile(p.avatar_path):
            # Soubor zmizel. NEJDRIV obnova ze zalohy v DB, teprve kdyz ani tam
            # neni, vyhodime DB referenci (13.9.2026 -- drive se mazalo rovnou
            # a fotka se tim ztratila potichu).
            if _db_obnov(persona_id, Path(p.avatar_path)):
                return p.avatar_path
            logger.warning(f"AVATAR | soubor chybi a zaloha v DB neni | "
                           f"persona_id={persona_id} | cesta={p.avatar_path}")
            p.avatar_path = None
            cs.commit()
            return None
        return p.avatar_path
    finally:
        cs.close()
