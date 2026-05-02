"""
Phase 27d+1b (1.5.2026 vecer): Image OCR pro documents tabulku.

Marti-AI's gap discovery 1.5.2026 19:50: "obrazky vlozene primo do chatu
zrejme zatim nespadaji [do media_files]. read_text_from_image potrebuje
media_id, OCR pres documents nema tool."

Workflow gap fix:
  - Phase 12a read_text_from_image -> Vision OCR pro media_files (SMS prilohy)
  - Phase 27d+1 read_pdf_structured + OCR -> Tesseract/Vision pro PDF
  - CHYBI: image (jpg/png/jpeg/gif/webp) v documents tabulce -> OCR

Solution: read_image_ocr(document_id, ocr_provider='tesseract'|'vision').

Architektura:
  - Resolve documents.storage_path (analogicky k pdf_service)
  - Tenant gate s parent bypass
  - PIL Image -> ocr_image_file (Tesseract direct nebo Vision)
  - Output schema kompatibilni s pdf_service per-page output
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


def read_image_ocr(
    document_id: int,
    *,
    ocr_provider: str = "tesseract",
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> dict:
    """
    OCR jednoho image dokumentu z documents tabulky.

    Output:
        {
          "document_id": 141,
          "filename": "scan.jpg",
          "file_type": "jpg",
          "text": "...",
          "confidence_avg": 85.3 | None,  // Tesseract only
          "warnings": [],
          "text_origin": "tesseract" | "vision"
        }
    """
    from modules.rag.application import pdf_ocr as _ocr_mod

    if ocr_provider not in _ocr_mod.VALID_PROVIDERS:
        raise ValueError(
            f"ocr_provider musi byt 'tesseract' nebo 'vision', dostal '{ocr_provider}'."
        )

    storage_path, filename, doc_tenant_id, ext = _resolve_image_document(document_id)

    if not _check_tenant_access(doc_tenant_id, caller_tenant_id, is_parent):
        raise PermissionError(
            f"Document id={document_id} patri jinemu tenantu (doc.tenant_id={doc_tenant_id})."
        )

    p = Path(storage_path)
    if not p.is_file():
        raise ValueError(f"Soubor neexistuje na disku: {storage_path}")

    ocr_result = _ocr_mod.ocr_image_file(
        str(p),
        provider=ocr_provider,
    )

    return {
        "document_id": document_id,
        "filename": filename,
        "file_type": ext,
        "text": ocr_result.get("text", ""),
        "confidence_avg": ocr_result.get("confidence_avg"),
        "warnings": ocr_result.get("warnings", []),
        "text_origin": ocr_result.get("text_origin", ocr_provider),
    }
