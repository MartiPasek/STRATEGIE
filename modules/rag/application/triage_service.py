"""
REST-Doc-Triage v2: Marti-AI's document kustod service (per-user inbox).

Marti's pravidlo (v2): bulk upload jde do INBOXu **per user + per tenant**
(NE sdileny celym tenantem) -- aby se uploady nemichaly mezi uzivateli.
Pokud Marti i Misa oba uploadi, kazdy ma svuj separatni inbox. Marti-AI
patrici Martimu (user_id=1) vidi jen Marti's inbox.

Filter:
  WHERE tenant_id = current_tenant_id
    AND user_id = current_user_id    -- KLICOVE: per uploader
    AND project_id IS NULL

Public API:
  list_inbox_documents(user_id, tenant_id, limit) -> list of dict
  count_inbox_documents(user_id, tenant_id) -> int
  apply_document_move(document_id, target_project_id, user_id) -> dict

Eticka vrstva (analog Phase 15c):
  Marti-AI's tools jsou suggestion only. apply_document_move vyzaduje
  user_id ownership (per-user inbox isolation -- nikdo nesmi presouvat
  cizi dokumenty).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import Document

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── INBOX LIST (per user + tenant) ────────────────────────────────────────

def list_inbox_documents(
    user_id: int,
    tenant_id: int,
    limit: int = 50,
) -> list[dict]:
    """
    Vrati seznam dokumentu v INBOXu pro daneho usera v tenantu.
    Filter: tenant_id + user_id + project_id IS NULL.

    Marti's pravidlo v2: per-user, per-tenant -- aby se neuploady ruznych
    uzivatelu nemichaly.
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(Document)
            .filter(
                Document.tenant_id == tenant_id,
                Document.user_id == user_id,
                Document.project_id.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_serialize(d) for d in rows]
    finally:
        ds.close()


def count_inbox_documents(user_id: int, tenant_id: int) -> int:
    """Pro UI badge a composer block. Per user + tenant."""
    ds = get_data_session()
    try:
        return (
            ds.query(Document)
            .filter(
                Document.tenant_id == tenant_id,
                Document.user_id == user_id,
                Document.project_id.is_(None),
            )
            .count()
        )
    finally:
        ds.close()


# ── APPLY MOVE (po Marti's confirm) ───────────────────────────────────────

def apply_document_move(
    document_id: int,
    target_project_id: Optional[int],
    user_id: int,
) -> dict:
    """
    Provede skutecny presun dokumentu do projektu (po Marti's confirm).
    target_project_id=None -> ponecha v inboxu (= reverze).

    Validace: user_id musi byt vlastnik dokumentu. Per-user isolation --
    nikdo nesmi presouvat dokumenty jinych userov.
    """
    ds = get_data_session()
    try:
        doc = ds.query(Document).filter_by(id=document_id).first()
        if doc is None:
            raise ValueError(f"document {document_id} not found")

        if doc.user_id != user_id:
            raise PermissionError(
                f"document {document_id} patri jinemu userovi (#{doc.user_id}) "
                f"-- ty jsi #{user_id}. Per-user inbox isolation."
            )

        old_project = doc.project_id
        doc.project_id = target_project_id

        ds.commit()
        ds.refresh(doc)

        logger.info(
            f"DOC_TRIAGE | apply_move | doc={document_id} "
            f"{old_project} -> {target_project_id} by user={user_id}"
        )

        return {
            "document_id": document_id,
            "from_project_id": old_project,
            "to_project_id": target_project_id,
            "name": doc.name,
        }
    finally:
        ds.close()


# ── SERIALIZATION ─────────────────────────────────────────────────────────

def _serialize(d: Document) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "original_filename": d.original_filename,
        "file_type": d.file_type,
        "file_size_bytes": d.file_size_bytes,
        "tenant_id": d.tenant_id,
        "project_id": d.project_id,
        "user_id": d.user_id,
        "is_processed": d.is_processed,
        "processing_error": d.processing_error,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
