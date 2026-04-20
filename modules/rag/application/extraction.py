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
