"""
Selection service -- per-user multi-select dokumentu pro batch akce.

Marti's REST-Doc-Triage v4: user oznaci skupinu souboru pres Ctrl/Shift+klik
v Files modalu, Marti-AI cte selection (`list_selected_documents` AI tool)
a po Marti's confirmu provede batch akci (`apply_to_selection` -- delete
nebo move_to_project).

Tenant scope: selection je perzistentni napric tenanty, ale pri toggle
overujeme, ze document.tenant_id == aktualni tenant usera (aby user
nemohl pridat do selection cizi dokumenty). Pri list_for_tenant filtrujeme
jen rows aktualniho tenantu.

API:
  toggle_documents(user_id, document_ids, tenant_id) -> dict (added/removed counts)
  list_selection(user_id, tenant_id) -> list[dict] (s JOIN document info)
  count_selection(user_id, tenant_id) -> int
  clear_selection(user_id, tenant_id=None) -> int (kolik smazano)
  remove_documents(user_id, document_ids) -> int
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    UserDocumentSelection, Document,
)

logger = get_logger("rag.selection")


def _normalize_ids(document_ids: Iterable[int]) -> list[int]:
    """Sanitize -- jen positive ints, dedup, max 200 per call."""
    result: list[int] = []
    seen: set[int] = set()
    for raw in document_ids:
        try:
            i = int(raw)
        except (TypeError, ValueError):
            continue
        if i <= 0 or i in seen:
            continue
        seen.add(i)
        result.append(i)
        if len(result) >= 200:
            break
    return result


def toggle_documents(
    user_id: int,
    document_ids: Iterable[int],
    tenant_id: int,
) -> dict:
    """
    Smart toggle: pro kazde ID -- pokud uz je v selection user_idu, odebrat;
    pokud neni, pridat (po overeni ze document patri user's tenantu).

    Cross-tenant ochrana: dokumenty z jineho tenantu se NEpridaji (silently
    skipped, vrati se v 'rejected_tenant' pro UI feedback).

    Vraci: {added: [ids], removed: [ids], rejected_tenant: [ids], rejected_missing: [ids]}
    """
    ids = _normalize_ids(document_ids)
    if not ids:
        return {"added": [], "removed": [], "rejected_tenant": [], "rejected_missing": []}

    ds = get_data_session()
    try:
        # 1) Najdi existujici selection rows pro tyto ID
        existing_rows = (
            ds.query(UserDocumentSelection)
            .filter(
                UserDocumentSelection.user_id == user_id,
                UserDocumentSelection.document_id.in_(ids),
            )
            .all()
        )
        existing_ids = {r.document_id for r in existing_rows}

        # 2) Najdi dokumenty (pro tenant check) pro ID, ktere nejsou jeste v selection
        new_candidates = [i for i in ids if i not in existing_ids]
        valid_to_add: list[int] = []
        rejected_tenant: list[int] = []
        rejected_missing: list[int] = []
        if new_candidates:
            docs = (
                ds.query(Document.id, Document.tenant_id)
                .filter(Document.id.in_(new_candidates))
                .all()
            )
            doc_map = {d.id: d.tenant_id for d in docs}
            for i in new_candidates:
                if i not in doc_map:
                    rejected_missing.append(i)
                elif doc_map[i] != tenant_id:
                    rejected_tenant.append(i)
                else:
                    valid_to_add.append(i)

        # 3) Toggle: existing -> remove, new valid -> add
        removed: list[int] = []
        if existing_rows:
            for r in existing_rows:
                ds.delete(r)
                removed.append(r.document_id)

        added: list[int] = []
        if valid_to_add:
            now = datetime.now(timezone.utc)
            for i in valid_to_add:
                ds.add(UserDocumentSelection(
                    user_id=user_id, document_id=i, selected_at=now,
                ))
                added.append(i)

        ds.commit()
        logger.info(
            f"SELECTION | toggle | user={user_id} tenant={tenant_id} | "
            f"added={len(added)} removed={len(removed)} "
            f"rejected_tenant={len(rejected_tenant)} rejected_missing={len(rejected_missing)}"
        )
        return {
            "added": added,
            "removed": removed,
            "rejected_tenant": rejected_tenant,
            "rejected_missing": rejected_missing,
        }
    finally:
        ds.close()


def list_selection(user_id: int, tenant_id: int) -> list[dict]:
    """
    Vrati seznam dokumentu, ktere ma user oznacene a patri aktualnimu tenantu.
    JOIN s Document pro display metadata (name, type, project_id, storage_only).
    Order: nejnovejsi vyber nahore (podle selected_at DESC).
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(
                UserDocumentSelection.document_id,
                UserDocumentSelection.selected_at,
                Document.name,
                Document.original_filename,
                Document.file_type,
                Document.file_size_bytes,
                Document.project_id,
                Document.storage_only,
                Document.is_processed,
                Document.tenant_id,
            )
            .join(Document, Document.id == UserDocumentSelection.document_id)
            .filter(
                UserDocumentSelection.user_id == user_id,
                Document.tenant_id == tenant_id,
            )
            .order_by(UserDocumentSelection.selected_at.desc())
            .all()
        )
        return [
            {
                "document_id": r.document_id,
                "name": r.name,
                "original_filename": r.original_filename,
                "file_type": r.file_type,
                "file_size_bytes": r.file_size_bytes,
                "project_id": r.project_id,
                "storage_only": bool(r.storage_only),
                "is_processed": bool(r.is_processed),
                "selected_at": r.selected_at.isoformat() if r.selected_at else None,
            }
            for r in rows
        ]
    finally:
        ds.close()


def count_selection(user_id: int, tenant_id: int) -> int:
    """Pocet oznacenych dokumentu user_idu v aktualnim tenantu."""
    ds = get_data_session()
    try:
        return (
            ds.query(UserDocumentSelection)
            .join(Document, Document.id == UserDocumentSelection.document_id)
            .filter(
                UserDocumentSelection.user_id == user_id,
                Document.tenant_id == tenant_id,
            )
            .count()
        )
    finally:
        ds.close()


def clear_selection(user_id: int, tenant_id: int | None = None) -> int:
    """
    Smaze vsechny selection rows usera. Pokud je tenant_id, smaze jen rows
    s dokumenty toho tenantu (UI 'Clear all' v current tenantu, ne globalne).
    Vraci pocet smazanych rows.
    """
    ds = get_data_session()
    try:
        q = ds.query(UserDocumentSelection).filter(UserDocumentSelection.user_id == user_id)
        if tenant_id is not None:
            # Filter cestou JOIN: smazeme jen ty kde document.tenant_id matchne
            doc_ids = (
                ds.query(Document.id)
                .filter(Document.tenant_id == tenant_id)
                .subquery()
            )
            q = q.filter(UserDocumentSelection.document_id.in_(doc_ids))
        # Predtim nez deletneme, ulozime IDs pro logging
        ids_to_delete = [r.document_id for r in q.all()]
        if ids_to_delete:
            (
                ds.query(UserDocumentSelection)
                .filter(
                    UserDocumentSelection.user_id == user_id,
                    UserDocumentSelection.document_id.in_(ids_to_delete),
                )
                .delete(synchronize_session=False)
            )
        ds.commit()
        logger.info(
            f"SELECTION | clear | user={user_id} tenant={tenant_id} | "
            f"deleted={len(ids_to_delete)}"
        )
        return len(ids_to_delete)
    finally:
        ds.close()


def remove_documents(user_id: int, document_ids: Iterable[int]) -> int:
    """
    Odebere konkretni dokumenty ze selection (bez tenant check -- volane
    z apply_to_selection po dokoncenem deletu / move, kde uz nezalezi).
    Vraci pocet odebranych.
    """
    ids = _normalize_ids(document_ids)
    if not ids:
        return 0
    ds = get_data_session()
    try:
        deleted = (
            ds.query(UserDocumentSelection)
            .filter(
                UserDocumentSelection.user_id == user_id,
                UserDocumentSelection.document_id.in_(ids),
            )
            .delete(synchronize_session=False)
        )
        ds.commit()
        return int(deleted)
    finally:
        ds.close()
