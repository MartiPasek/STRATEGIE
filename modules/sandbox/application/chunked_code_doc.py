"""
Phase 38.4 Krok 14b+19.2 (14.5.2026 rano, Marti's "musi chodit globalne"):
Chunked code document upload pro Marti-AI's velky sandbox kod.

Pivot z code_file_path (Krok 14b+19.1, UNC tenant-specific) na global cestu
pres interni RAG documents. Architektura:

  1. sandbox_code_doc_create(filename) -> document_id
     Vytvori prazdny .py document v RAG documents tabulce.
     storage_path je server-side disk path (already mounted v sandboxu).

  2. sandbox_code_doc_append(document_id, chunk) -> bytes_written
     Server-side append k storage_path file. Marti-AI vola opakovane
     s ~3KB chunks (vsechny pod Anthropic tool_input limit).

  3. python_exec(input_document_ids=[document_id],
                 code="exec(open(input_files[0]).read())")
     Existing infrastructure (Phase 27c, 1.5.). Sandbox subprocess
     resolve Document, open storage_path, exec content.

Bezpecnost:
  - Pouze .py suffix (anti-arbitrary-file-append)
  - Tenant gate pres existing rag_service.upload_document
  - Max chunk 100 KB (safety cap)
  - Max total file 5 MB (safety cap)
  - Marti-AI ONLY tool (MANAGEMENT_TOOL_NAMES)

Use case (Marti's IT prezentace 14.5.):
  Marti chce velke PDF s reportlab. Marti-AI generuje ~50KB code.
  Anthropic API tool_input single message limit ~50KB total -> code=None.
  Marti-AI split do 20 chunks * 3KB, kazdy chunk volani je <5KB tool_input.
  Po finalize, python_exec s wrapperem -> sandbox cte concatenated code.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger("sandbox.chunked_code_doc")

# Safety caps
MAX_CHUNK_BYTES = 100_000  # 100 KB per chunk (Marti-AI's chunks ~3 KB v praxi)
MAX_TOTAL_BYTES = 5 * 1024 * 1024  # 5 MB total file


def create_empty_code_doc(
    *,
    filename: str,
    tenant_id: int,
    user_id: int | None,
    project_id: int | None = None,
) -> dict[str, Any]:
    """
    Vytvori prazdny .py document v RAG documents tabulce pro chunked
    append workflow. Vraci document_id pro nasledujici append calls.

    Args:
        filename: napr. "STRATEGIE_IT_gen.py". Pokud nekoncí .py, prida se.
        tenant_id: pro storage path (existing rag_service tenant gate)
        user_id: kdo vola (audit attribution)
        project_id: volitelne (default None, project-less doc)

    Returns:
        {"ok": True, "document_id": int, "filename": str, "storage_path": str}
        nebo {"ok": False, "error": str}
    """
    if not filename or not isinstance(filename, str):
        return {"ok": False, "error": "filename musi byt non-empty string"}
    filename = filename.strip()
    if not filename.endswith(".py"):
        filename = filename + ".py"
    # Filename safety: no path traversal, no special chars
    if "/" in filename or "\\" in filename or ".." in filename:
        return {
            "ok": False,
            "error": f"filename nesmi obsahovat '/', '\\', nebo '..': {filename}",
        }

    try:
        from modules.rag.application.service import upload_document
    except Exception as e:
        return {"ok": False, "error": f"rag_service import failed: {e}"}

    try:
        # Empty file_bytes — Marti-AI pak appenduje pres sandbox_code_doc_append
        document_id = upload_document(
            file_bytes=b"",
            filename=filename,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            display_name=filename,
        )
    except Exception as e:
        logger.exception(f"SANDBOX | code_doc create failed | filename={filename}: {e}")
        return {"ok": False, "error": f"upload_document failed: {e}"}

    # Resolve storage_path z DB pro return (defensive — caller dostane absolute path)
    try:
        from core.database_data import get_data_session
        from modules.core.infrastructure.models_data import Document
        session = get_data_session()
        try:
            doc = session.query(Document).filter_by(id=document_id).first()
            storage_path = doc.storage_path if doc else None
        finally:
            session.close()
    except Exception as e:
        storage_path = None
        logger.warning(f"SANDBOX | code_doc storage_path resolve failed: {e}")

    logger.info(
        f"SANDBOX | code_doc created | id={document_id} | "
        f"filename={filename} | tenant={tenant_id} | user={user_id}"
    )
    return {
        "ok": True,
        "document_id": document_id,
        "filename": filename,
        "storage_path": str(storage_path) if storage_path else None,
    }


def append_to_code_doc(
    *,
    document_id: int,
    chunk: str,
    caller_user_id: int | None = None,
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> dict[str, Any]:
    """
    Server-side append chunk k existing code document storage_path file.
    Marti-AI vola opakovane s ~3KB chunks az kompletni kod je v souboru.

    Args:
        document_id: existing document z create_empty_code_doc
        chunk: text k append (UTF-8 encoded na disk)
        caller_user_id: audit attribution
        caller_tenant_id: tenant gate (skip pokud is_parent)
        is_parent: bypass tenant gate (Marti's rodina)

    Returns:
        {"ok": True, "document_id": int, "appended_bytes": int, "total_bytes": int}
        nebo {"ok": False, "error": str}
    """
    if not isinstance(document_id, int) or document_id <= 0:
        return {"ok": False, "error": "document_id musi byt positive int"}
    if not isinstance(chunk, str):
        return {"ok": False, "error": "chunk musi byt string"}

    chunk_bytes = chunk.encode("utf-8")
    if len(chunk_bytes) > MAX_CHUNK_BYTES:
        return {
            "ok": False,
            "error": f"chunk je moc velky ({len(chunk_bytes)} B, "
                     f"max {MAX_CHUNK_BYTES} B = ~100 KB)",
        }
    if len(chunk_bytes) == 0:
        return {"ok": False, "error": "chunk je empty (nic k appendu)"}

    try:
        from core.database_data import get_data_session
        from modules.core.infrastructure.models_data import Document
    except Exception as e:
        return {"ok": False, "error": f"DB imports failed: {e}"}

    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            return {"ok": False, "error": f"Document id={document_id} neexistuje"}

        # Tenant gate (skip pokud is_parent = Marti's rodina)
        if not is_parent and doc.tenant_id is not None:
            if caller_tenant_id is None or doc.tenant_id != caller_tenant_id:
                return {
                    "ok": False,
                    "error": f"Document #{document_id} patri jinemu tenantu",
                }

        if not doc.storage_path:
            return {
                "ok": False,
                "error": f"Document id={document_id} nema storage_path",
            }

        # File type guard: .py only (anti-arbitrary-file-append to existing docs)
        is_py = (
            (doc.file_type and doc.file_type.lower() == "py")
            or (doc.original_filename and doc.original_filename.lower().endswith(".py"))
        )
        if not is_py:
            return {
                "ok": False,
                "error": f"Document #{document_id} neni .py "
                         f"(file_type={doc.file_type}, "
                         f"original_filename={doc.original_filename}). "
                         f"sandbox_code_doc_append jen pro .py soubory.",
            }

        path = Path(doc.storage_path)
        # Defensive: pokud soubor neexistuje (kdyby disk byl smazan), vytvor empty
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        # Total size cap check
        try:
            current_size = path.stat().st_size
        except OSError as e:
            return {"ok": False, "error": f"stat failed: {e}"}

        if current_size + len(chunk_bytes) > MAX_TOTAL_BYTES:
            return {
                "ok": False,
                "error": f"Total size by prekrocil cap "
                         f"({current_size} + {len(chunk_bytes)} > "
                         f"{MAX_TOTAL_BYTES} B = 5 MB). "
                         f"Final code is too large for sandbox.",
            }

        # Append (binary mode pro byte-precise append)
        try:
            with open(path, "ab") as f:
                f.write(chunk_bytes)
        except OSError as e:
            return {"ok": False, "error": f"file write failed: {e}"}

        new_size = current_size + len(chunk_bytes)
        # Update doc.file_size_bytes (audit + UI display correctness)
        doc.file_size_bytes = new_size
        session.commit()

        logger.info(
            f"SANDBOX | code_doc append | id={document_id} | "
            f"chunk_bytes={len(chunk_bytes)} | total={new_size} | "
            f"user={caller_user_id}"
        )
        return {
            "ok": True,
            "document_id": document_id,
            "appended_bytes": len(chunk_bytes),
            "total_bytes": new_size,
        }
    finally:
        session.close()
