"""
Text extraction z dokumentu pres markitdown.

Markitdown podporuje vetsinu beznych formatu (PDF, DOCX, XLSX, PPTX, MD,
HTML, TXT, RTF, CSV, EPUB, IMG s OCR, audio s transcription, ...) a vraci
markdown jako sjednoceny vystup. Ten dale pouzijeme do chunkingu.

API:
    extract_text(file_path) -> str         # markdown text
    detect_file_type(filename) -> str      # 'pdf', 'docx', 'md', ...
"""
from __future__ import annotations

import os
from pathlib import Path

from core.logging import get_logger

logger = get_logger("rag.extraction")


def detect_file_type(filename: str) -> str:
    """Vraci normalizovanou priponu (lowercase, bez tecky). Pro neznam vraci ''."""
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext


def extract_text(file_path: str) -> str:
    """
    Extrahuje text z dokumentu. Pouziva markitdown (podporuje vse rozumne).
    Pro plain text (txt, md) bypassuje markitdown a cte primo (rychlejsi,
    deterministicke).

    Raises:
        FileNotFoundError: soubor neexistuje
        Exception: extrakce selhala (markitdown vyhodi ruzne typy)
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Soubor neexistuje: {file_path}")

    ext = detect_file_type(file_path)

    # Plain text bypass -- nemusime tahat markitdown
    if ext in ("txt", "md", "csv", "log"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return _sanitize_text(f.read())
        except UnicodeDecodeError:
            # Fallback na latin-1 / windows-1250 pro ceske texty bez UTF-8
            with open(file_path, "r", encoding="windows-1250", errors="replace") as f:
                return _sanitize_text(f.read())

    # Vsechno ostatni jde pres markitdown
    from markitdown import MarkItDown
    md = MarkItDown()
    result = md.convert(file_path)
    text = result.text_content or ""

    # PDF OCR fallback (Marti 5.7.2026): markitdown u naskenovanych PDF (bez textove
    # vrstvy) vrati prazdno. Rasterizace pres pypdfium2 (na cloudu je; Poppler/fitz
    # nemusi byt) + Tesseract (ces+deu+eng). Cap 40 stran.
    if ext == "pdf" and not (text and text.strip()):
        try:
            import pypdfium2 as _pdfium
            from modules.rag.application.pdf_ocr import _import_tesseract as _imp_t
            _pt, _ = _imp_t()
            _pdf = _pdfium.PdfDocument(file_path)
            _parts = []
            _n = min(len(_pdf), 40)
            for _i in range(_n):
                _pil = _pdf[_i].render(scale=200 / 72.0).to_pil()
                try:
                    _t = _pt.image_to_string(_pil, lang="ces+deu+eng")
                except Exception:
                    _t = _pt.image_to_string(_pil, lang="eng")
                if _t and _t.strip():
                    _parts.append(_t)
            try:
                _pdf.close()
            except Exception:
                pass
            text = "\n\n".join(_parts)
            logger.info("RAG | PDF OCR fallback | %s | stran=%d | text_len=%d",
                        file_path, _n, len(text))
        except Exception as _oexc:
            logger.warning("RAG | PDF OCR fallback selhal: %s", _oexc)

    # PostgreSQL TEXT sloupce nemohou obsahovat NUL bytes (\x00). Nektere
    # binarni formaty (.msg, .doc) muzou pres extrakci pustit residual NUL,
    # ktery pak rozbije insert. Defensivne strip + collapse opakovaneho whitespace.
    return _sanitize_text(text)


def _sanitize_text(text: str) -> str:
    """Odstrani NUL bytes a normalizuje whitespace -- bezpecne pro Postgres TEXT."""
    if not text:
        return ""
    # NUL bytes raw remove
    text = text.replace("\x00", "")
    # Vetsi rady whitespace tisku zachovaji ale srotuji na nej zadnou tabulkou
    return text
