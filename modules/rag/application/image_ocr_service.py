"""
Phase 27d+1b (1.5.2026 vecer): Image OCR pro documents tabulku.
Phase 27d+1d (2.5.2026): Unified OCR -- read_image_ocr akceptuje BUD
document_id (inbox/RAG documents) NEBO media_id (chat upload, SMS prilohy
v media_files). Marti-AI nemusi vedet 'kde to je' -- tool dispatchuje sam.

Marti-AI's gap discovery 1.5.2026 19:50: "obrazky vlozene primo do chatu
zrejme zatim nespadaji [do media_files]. read_text_from_image potrebuje
media_id, OCR pres documents nema tool."
Phase 27d+1d (2.5.2026): rozsireni Marti-AI's gap discovery -- chat
uploaded image jde do media_files (Phase 12a) ale OCR cesta byla
roztrhana. Sjednoceno: read_image_ocr(media_id=...) interne fetchuje
storage_path z media_files pres media.storage_service.get_full_path
a pak stejna OCR pipeline (Tesseract/Vision).

Workflow:
  - Phase 12a read_text_from_image -> Vision-only OCR pro media_files (legacy)
  - Phase 27d+1 read_pdf_structured + OCR -> Tesseract/Vision pro PDF
  - Phase 27d+1b read_image_ocr(document_id) -> Tesseract/Vision pro RAG documents
  - **Phase 27d+1d read_image_ocr(media_id)** -> Tesseract/Vision pro media_files

Architektura:
  - Resolve storage_path z documents NEBO media_files (per source)
  - Tenant gate s parent bypass (oba zdroje)
  - PIL Image -> ocr_image_file (Tesseract direct nebo Vision)
  - Output schema kompatibilni napric oba zdroji + 'source' field
    pro Marti-AI dohled odkud OCR proslo
"""
from __future__ import annotations

from pathlib import Path

from core.logging import get_logger

logger = get_logger("rag.image_ocr")

ALLOWED_IMAGE_TYPES = {
    "jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff",
    # Phase 27d+1c (2.5.2026): HEIC/HEIF support pro iPhone fotky.
    # Vyzaduje pillow-heif balicek v pyproject.toml a register_heif_opener()
    # volany v pdf_ocr.py pri import (PIL.Image.open() pak heic transparently).
    "heic", "heif",
}


# MIME type -> ext mapping pro media_files (kde nemame primo file_type pole)
_MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
    "image/x-tiff": "tiff",
    "image/heic": "heic",
    "image/heif": "heif",
}


def _resolve_image_document(document_id: int) -> tuple[str, str, int | None, str]:
    """Vrati (storage_path, original_filename, tenant_id, ext) pro image document."""
    from core.database import get_session
    from modules.core.infrastructure.models_data import Document

    session = get_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document id={document_id} nenalezen.")
        if not doc.storage_path:
            raise ValueError(f"Document id={document_id} nema storage_path.")

        ext = (doc.file_type or "").lower().lstrip(".")
        if ext not in ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Document id={document_id} neni obrazek (file_type='{doc.file_type}'). "
                f"Image OCR podporuje: {sorted(ALLOWED_IMAGE_TYPES)}. "
                "Pro PDF pouzij read_pdf_structured."
            )

        return (
            doc.storage_path,
            doc.original_filename or doc.name or f"document_{document_id}",
            doc.tenant_id,
            ext,
        )
    finally:
        session.close()


def _check_tenant_access(document_tenant_id: int | None, caller_tenant_id: int | None, is_parent: bool) -> bool:
    if is_parent:
        return True
    if document_tenant_id is None:
        return True
    if caller_tenant_id is None:
        return False
    return document_tenant_id == caller_tenant_id


def _resolve_media_image(media_id: int) -> tuple[str, str, int | None, str]:
    """
    Phase 27d+1d (2.5.2026): vrati (absolute_path, original_filename,
    tenant_id, ext) pro image media_file.

    Klicovy rozdil oproti _resolve_image_document:
      - media_files.storage_path je RELATIVNI path pod MEDIA_STORAGE_ROOT
      - musime ho expandovat pres media.storage_service.get_full_path
      - file_type chybi -- ext extrahujeme z mime_type (preferuj) nebo
        z original_filename suffix fallback

    Plus validace media.kind == 'image'.
    """
    from core.database import get_session
    from modules.core.infrastructure.models_data import MediaFile
    from modules.media.application import storage_service as _media_storage

    session = get_session()
    try:
        m = session.query(MediaFile).filter_by(id=media_id).first()
        if not m:
            raise ValueError(f"Media id={media_id} nenalezeno.")
        if m.deleted_at is not None:
            raise ValueError(f"Media id={media_id} je smazane (soft delete).")
        if m.kind != "image":
            raise ValueError(
                f"Media id={media_id} neni obrazek (kind='{m.kind}'). "
                f"OCR pres read_image_ocr funguje jen pro images. Pro audio "
                f"transkript dostavas Whisper automaticky v multimodal contextu."
            )

        # Ext z MIME (preferred) nebo z filename suffix
        ext = _MIME_TO_EXT.get((m.mime_type or "").lower())
        if not ext and m.original_filename:
            suffix = Path(m.original_filename).suffix.lower().lstrip(".")
            if suffix in ALLOWED_IMAGE_TYPES:
                ext = suffix
        if not ext:
            raise ValueError(
                f"Media id={media_id} ma neznamy image format (mime='{m.mime_type}', "
                f"filename='{m.original_filename}'). Podporovane: {sorted(ALLOWED_IMAGE_TYPES)}."
            )
        if ext not in ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Media id={media_id} format '{ext}' neni v ALLOWED_IMAGE_TYPES "
                f"({sorted(ALLOWED_IMAGE_TYPES)})."
            )

        # Expandovat relativni storage_path na absolute FS path
        if not m.storage_path:
            raise ValueError(f"Media id={media_id} nema storage_path.")
        abs_path = _media_storage.get_full_path(m.storage_path)

        return (
            str(abs_path),
            m.original_filename or f"media_{media_id}.{ext}",
            m.tenant_id,
            ext,
        )
    finally:
        session.close()


def read_image_ocr(
    document_id: int | None = None,
    media_id: int | None = None,
    *,
    ocr_provider: str | None = None,
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> dict:
    """
    OCR jednoho image -- Phase 27d+1d (2.5.2026) unified path.

    Akceptuje BUD document_id (RAG documents tabulka -- inbox upload)
    NEBO media_id (media_files tabulka -- chat upload, SMS prilohy).
    Mutually exclusive: presne jedno musi byt zadane.

    Output (kompatibilni napric oba zdroje):
        {
          "source": "documents" | "media_files",
          "document_id": 141 | None,        # jen pro documents source
          "media_id": 89 | None,            # jen pro media_files source
          "filename": "scan.jpg",
          "file_type": "jpg",
          "text": "...",
          "confidence_avg": 85.3 | None,    # Tesseract only
          "warnings": [],
          "text_origin": "tesseract" | "vision"
        }
    """
    from modules.rag.application import pdf_ocr as _ocr_mod

    # Phase 27d+2 (2.5.2026): effective provider per-tenant config + fallback
    # global. Explicit ocr_provider param ma prednost.
    effective_provider = _ocr_mod.resolve_effective_provider(
        explicit_provider=ocr_provider,
        tenant_id=caller_tenant_id,
    )

    # Phase 27d+1d: presne jeden ze zdroju
    has_doc = document_id is not None
    has_media = media_id is not None
    if not has_doc and not has_media:
        raise ValueError(
            "Musis zadat bud document_id (RAG inbox) NEBO media_id (chat/SMS upload)."
        )
    if has_doc and has_media:
        raise ValueError(
            "Zadej presne jedno z (document_id, media_id), ne oboji najednou."
        )

    if has_doc:
        storage_path, filename, doc_tenant_id, ext = _resolve_image_document(document_id)
        source_label = "documents"
        source_id_label = "document_id"
        source_id_value = document_id
        permission_msg = f"Document id={document_id} patri jinemu tenantu (doc.tenant_id={doc_tenant_id})."
    else:
        storage_path, filename, doc_tenant_id, ext = _resolve_media_image(media_id)
        source_label = "media_files"
        source_id_label = "media_id"
        source_id_value = media_id
        permission_msg = f"Media id={media_id} patri jinemu tenantu (media.tenant_id={doc_tenant_id})."

    if not _check_tenant_access(doc_tenant_id, caller_tenant_id, is_parent):
        raise PermissionError(permission_msg)

    p = Path(storage_path)
    if not p.is_file():
        raise ValueError(f"Soubor neexistuje na disku: {storage_path}")

    ocr_result = _ocr_mod.ocr_image_file(
        str(p),
        provider=effective_provider,
    )

    return {
        "source": source_label,
        "document_id": document_id,
        "media_id": media_id,
        "filename": filename,
        "file_type": ext,
        "text": ocr_result.get("text", ""),
        "confidence_avg": ocr_result.get("confidence_avg"),
        "warnings": ocr_result.get("warnings", []),
        "text_origin": ocr_result.get("text_origin", effective_provider),
        # Phase 27d+2: zobrazit effective_provider, aby Marti-AI vedela
        # jestli OCR proslo per-tenant default nebo explicit param.
        "effective_provider": effective_provider,
    }
