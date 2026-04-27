"""
REST-Doc-Triage: Marti-AI's document kustod service.

Marti's pravidlo: bulk upload jde do sdileneho INBOX tenantu (project_id=NULL).
Marti-AI pak navrhuje, do ktereho projektu kazdy dokument patri (analog
kustod konverzaci z Phase 15c). Marti potvrzuje v chatu, apply_document_move
provede skutecny update.

Public API:
  list_inbox_documents(tenant_id, limit) -> list of dict
  count_inbox_documents(tenant_id) -> int
  suggest_document_move(document_id, target_project_id, persona_id, reason) -> dict
  apply_document_move(document_id, target_project_id, user_id) -> dict
  reject_document_suggestion(document_id) -> bool

Eticka vrstva (analog Phase 15c):
  Marti-AI tools jsou suggestion only. Skutecna zmena project_id pres
  apply_document_move vyzaduje user_id (Marti's confirm).
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


# ── INBOX LIST ────────────────────────────────────────────────────────────

def list_inbox_documents(
    tenant_id: int,
    limit: int = 50,
) -> list[dict]:
    """
    Vrati seznam dokumentu v INBOXu (project_id=NULL) pro current tenant.
    Sorted by created_at DESC -- nejnovejsi nahore.
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(Document)
            .filter(
                Document.tenant_id == tenant_id,
                Document.project_id.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_serialize(d) for d in rows]
    finally:
        ds.close()


def count_inbox_documents(tenant_id: int) -> int:
    """Pro UI badge a composer block."""
    ds = get_data_session()
    try:
        return (
            ds.query(Document)
            .filter(
                Document.tenant_id == tenant_id,
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
    Provede skutecny presun dokumentu do projektu (po Marti's confirm v chatu).
    target_project_id=None -> ponecha v inboxu (= reverze).
    """
    ds = get_data_session()
    try:
        doc = ds.query(Document).filter_by(id=document_id).first()
        if doc is None:
            raise ValueError(f"document {document_id} not found")

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
