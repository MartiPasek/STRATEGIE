"""
File storage pro uploaded dokumenty.

Cilovy layout:
    {DOCUMENTS_STORAGE_DIR}/
      {tenant_id}/
        {document_id}.{ext}

Proc tenant_id v ceste:
  - Izolace na uroveni FS (pri omylem leaking backupu jsou tenant scopy
    fyzicky oddelene).
  - Snadny cleanup (smazat cely adresar pri destroy tenant).

Proc NE original filename v ceste:
  - Predejde kolizim (dva usery nahraji 'report.pdf')
  - Predejde issuum s nepovolymi znaky (pri uploadu PDF "výkaz 2025.pdf"
    bys musel escapovat unicode / mezery / lomitka)
  - Original filename ulozen v documents.original_filename (audit + download UI)
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from core.config import settings
from core.logging import get_logger

logger = get_logger("rag.storage")


def storage_root() -> Path:
    """Root storage dir. Vraci Path object. Neni idempotentni -- vytvari pokud neni."""
    root = Path(settings.documents_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def tenant_dir(tenant_id: int) -> Path:
    """Tenant-specificky subfolder. Lazy create."""
    d = storage_root() / str(tenant_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_upload(tenant_id: int, document_id: int, file_extension: str, file_bytes: bytes) -> str:
    """
    Ulozi bytes na disk. Vraci absolutni cestu (pro zapis do documents.storage_path).
    """
    ext = (file_extension or "").lstrip(".").lower() or "bin"
    target = tenant_dir(tenant_id) / f"{document_id}.{ext}"
    with open(target, "wb") as f:
        f.write(file_bytes)
    logger.info(f"STORAGE | saved | path={target} | size={len(file_bytes)}")
    return str(target.absolute())


def delete_document_file(storage_path: str | None) -> None:
    """Smaze fyzicky soubor. Tise ignoruje neexistujici."""
    if not storage_path:
        return
    try:
        p = Path(storage_path)
        if p.is_file():
            p.unlink()
            logger.info(f"STORAGE | deleted | path={storage_path}")
    except Exception as e:
        logger.warning(f"STORAGE | delete failed | path={storage_path} | error={e}")
