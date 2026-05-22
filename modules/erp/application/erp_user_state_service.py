"""
Phase B+8.1 (6.5.2026): ERP user state service.

CRUD operace pro user-specific UI state v workspace:
  - Open tabs (multi-tab přehled — Centrála 1 pattern)
  - Favorites (★ pinned přehledy)
  - Recent (MRU — auto-tracked při openTab)
  - Tree drag-drop order (per skupina)

Per user/tenant scope. Předtím localStorage MVP (B+8.2a) — teď
production-ready cross-device sync.

Marti's spec 6.5.2026: "Per user, per tenant... do data_db".

Plus offline fallback frontend keeps localStorage as cache (write-through
pattern: API první, localStorage backup pro offline).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    ErpUserTab,
    ErpUserFavorite,
    ErpUserRecent,
    ErpUserTreeOrder,
)

logger = get_logger("erp.user_state_service")


# ── Constants ──────────────────────────────────────────────────────────

MAX_RECENT_PER_USER_TENANT = 20
MAX_FAVORITES_PER_USER_TENANT = 200
MAX_TABS_PER_USER_TENANT = 50


class ErpUserStateError(Exception):
    """Domain-level chyba při operacích s user state."""
    pass


# ── Helpers ────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_tab(t: ErpUserTab) -> dict:
    return {
        "cislo": int(t.menu_node_id),  # JSON key 'cislo' preserved (frontend backward compat); value je menu_node.id
        "label": t.label,
        "itemId": t.item_id,
        "sortOrder": int(t.sort_order or 0),
        "isActive": bool(t.is_active),
        # Phase 38.4 (11.5.2026 vecer): pinned + lastAccessedAt persistence
        # přes DB. Frontend write-through při right-click contextmenu (pin)
        # a při switchTab (bump access). Naformátováno jako ISO + epoch ms
        # pro frontend rovnou (Date.now() compat).
        "pinned": bool(t.pinned),
        "lastAccessedAt": (
            int(t.last_accessed_at.timestamp() * 1000) if t.last_accessed_at else None
        ),
        "openedAt": t.opened_at.isoformat() if t.opened_at else None,
    }


def _serialize_favorite(f: ErpUserFavorite) -> dict:
    return {
        "cislo": int(f.menu_node_id),  # JSON key 'cislo' preserved
        "sortOrder": int(f.sort_order or 0),
        "addedAt": f.added_at.isoformat() if f.added_at else None,
    }


def _serialize_recent(r: ErpUserRecent) -> dict:
    return {
        "cislo": int(r.menu_node_id),  # JSON key 'cislo' preserved
        "label": r.label,
        "lastUsedAt": r.last_used_at.isoformat() if r.last_used_at else None,
        "useCount": int(r.use_count or 0),
    }


# ── TABS ──────────────────────────────────────────────────────────────

def list_tabs(user_id: int, tenant_id: int) -> list[dict]:
    """Vrať seznam tabs pro user/tenant, sorted podle sort_order."""
    ds = get_data_session()
    try:
        rows = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
            )
            .order_by(ErpUserTab.sort_order.asc(), ErpUserTab.opened_at.asc())
            .all()
        )
        active_idx = -1
        for i, r in enumerate(rows):
            if r.is_active:
                active_idx = i
                break
        return {
            "tabs": [_serialize_tab(r) for r in rows],
            "activeIndex": active_idx,
        }
    finally:
        ds.close()


def open_tab(
    user_id: int,
    tenant_id: int,
    menu_node_id: int,
    label: str,
    item_id: str | None = None,
) -> dict:
    """Open tab — pokud existuje, aktualizuje label/item_id; jinak vloží."""
    ds = get_data_session()
    try:
        # Anti-spam: max tabs per user/tenant
        count = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
            )
            .count()
        )
        if count >= MAX_TABS_PER_USER_TENANT:
            raise ErpUserStateError(
                f"Max {MAX_TABS_PER_USER_TENANT} tabs per user/tenant"
            )

        existing = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
                ErpUserTab.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if existing:
            existing.label = label
            if item_id:
                existing.item_id = item_id
            ds.commit()
            ds.refresh(existing)
            return _serialize_tab(existing)
        # New — append na konec
        max_order = (
            ds.query(ErpUserTab.sort_order)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
            )
            .order_by(desc(ErpUserTab.sort_order))
            .first()
        )
        next_order = ((max_order[0] if max_order else 0) or 0) + 1
        new_tab = ErpUserTab(
            user_id=user_id,
            tenant_id=tenant_id,
            menu_node_id=menu_node_id,
            label=label,
            item_id=item_id,
            sort_order=next_order,
            is_active=False,
            opened_at=_now(),
        )
        ds.add(new_tab)
        ds.commit()
        ds.refresh(new_tab)
        return _serialize_tab(new_tab)
    except IntegrityError:
        ds.rollback()
        raise ErpUserStateError(
            f"Tab pro menu_node_id={menu_node_id} už existuje (race condition)"
        )
    finally:
        ds.close()


def close_tab(user_id: int, tenant_id: int, menu_node_id: int) -> bool:
    """Smazání tabu. Returns True pokud existoval."""
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
                ErpUserTab.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if not existing:
            return False
        ds.delete(existing)
        ds.commit()
        return True
    finally:
        ds.close()


def set_active_tab(user_id: int, tenant_id: int, menu_node_id: int) -> bool:
    """Mark tab as active (deactivate others). Returns True pokud našel."""
    ds = get_data_session()
    try:
        # Vypnout active flag na všech ostatních
        ds.query(ErpUserTab).filter(
            ErpUserTab.user_id == user_id,
            ErpUserTab.tenant_id == tenant_id,
        ).update({ErpUserTab.is_active: False})
        # Zapnout target
        existing = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
                ErpUserTab.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if not existing:
            ds.commit()
            return False
        existing.is_active = True
        # Phase 38.4 (11.5.2026 vecer): bump last_accessed_at pro LRU
        # eviction když taby overflow bar šířku.
        existing.last_accessed_at = _now()
        ds.commit()
        return True
    finally:
        ds.close()


def set_tab_pinned(
    user_id: int, tenant_id: int, menu_node_id: int, pinned: bool
) -> bool:
    """Phase 38.4 (11.5.2026 vecer): toggle pinned status pro záložku.

    Right-click v UI → toggle. Pinned záložky se neeviktují při overflow
    a close ikona vpravo se mění × → 📌 (decorative, no-op click).
    Returns True pokud tab existoval.
    """
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserTab)
            .filter(
                ErpUserTab.user_id == user_id,
                ErpUserTab.tenant_id == tenant_id,
                ErpUserTab.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if not existing:
            return False
        existing.pinned = bool(pinned)
        ds.commit()
        return True
    finally:
        ds.close()


def reorder_tabs(user_id: int, tenant_id: int, menu_node_ids_in_order: list[int]) -> int:
    """Update sort_order podle pořadí menu_node_ids. Returns count updated."""
    ds = get_data_session()
    try:
        updated = 0
        for idx, mnid in enumerate(menu_node_ids_in_order):
            r = (
                ds.query(ErpUserTab)
                .filter(
                    ErpUserTab.user_id == user_id,
                    ErpUserTab.tenant_id == tenant_id,
                    ErpUserTab.menu_node_id == mnid,
                )
                .one_or_none()
            )
            if r:
                r.sort_order = idx
                updated += 1
        ds.commit()
        return updated
    finally:
        ds.close()


# ── FAVORITES ─────────────────────────────────────────────────────────

def list_favorites(user_id: int, tenant_id: int) -> list[dict]:
    ds = get_data_session()
    try:
        rows = (
            ds.query(ErpUserFavorite)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
            )
            .order_by(ErpUserFavorite.sort_order.asc(), ErpUserFavorite.added_at.asc())
            .all()
        )
        return [_serialize_favorite(r) for r in rows]
    finally:
        ds.close()


def add_favorite(user_id: int, tenant_id: int, menu_node_id: int) -> dict:
    """Add to favorites. Idempotent — pokud existuje, no-op a vrátí current."""
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserFavorite)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
                ErpUserFavorite.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if existing:
            return _serialize_favorite(existing)
        # Anti-spam
        count = (
            ds.query(ErpUserFavorite)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
            )
            .count()
        )
        if count >= MAX_FAVORITES_PER_USER_TENANT:
            raise ErpUserStateError(
                f"Max {MAX_FAVORITES_PER_USER_TENANT} favorites per user/tenant"
            )
        max_order = (
            ds.query(ErpUserFavorite.sort_order)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
            )
            .order_by(desc(ErpUserFavorite.sort_order))
            .first()
        )
        next_order = ((max_order[0] if max_order else 0) or 0) + 1
        new_fav = ErpUserFavorite(
            user_id=user_id,
            tenant_id=tenant_id,
            menu_node_id=menu_node_id,
            sort_order=next_order,
            added_at=_now(),
        )
        ds.add(new_fav)
        ds.commit()
        ds.refresh(new_fav)
        return _serialize_favorite(new_fav)
    except IntegrityError:
        ds.rollback()
        raise ErpUserStateError(f"Favorite menu_node_id={menu_node_id} race condition")
    finally:
        ds.close()


def remove_favorite(user_id: int, tenant_id: int, menu_node_id: int) -> bool:
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserFavorite)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
                ErpUserFavorite.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        if not existing:
            return False
        ds.delete(existing)
        ds.commit()
        return True
    finally:
        ds.close()


def reorder_favorites(user_id: int, tenant_id: int, menu_node_ids_in_order: list[int]) -> int:
    ds = get_data_session()
    try:
        updated = 0
        for idx, mnid in enumerate(menu_node_ids_in_order):
            r = (
                ds.query(ErpUserFavorite)
                .filter(
                    ErpUserFavorite.user_id == user_id,
                    ErpUserFavorite.tenant_id == tenant_id,
                    ErpUserFavorite.menu_node_id == mnid,
                )
                .one_or_none()
            )
            if r:
                r.sort_order = idx
                updated += 1
        ds.commit()
        return updated
    finally:
        ds.close()


def clear_favorites(user_id: int, tenant_id: int) -> int:
    ds = get_data_session()
    try:
        deleted = (
            ds.query(ErpUserFavorite)
            .filter(
                ErpUserFavorite.user_id == user_id,
                ErpUserFavorite.tenant_id == tenant_id,
            )
            .delete()
        )
        ds.commit()
        return int(deleted or 0)
    finally:
        ds.close()


# ── RECENT (MRU) ──────────────────────────────────────────────────────

def list_recent(user_id: int, tenant_id: int, limit: int = MAX_RECENT_PER_USER_TENANT) -> list[dict]:
    ds = get_data_session()
    try:
        rows = (
            ds.query(ErpUserRecent)
            .filter(
                ErpUserRecent.user_id == user_id,
                ErpUserRecent.tenant_id == tenant_id,
            )
            .order_by(desc(ErpUserRecent.last_used_at))
            .limit(limit)
            .all()
        )
        return [_serialize_recent(r) for r in rows]
    finally:
        ds.close()


def track_recent(user_id: int, tenant_id: int, menu_node_id: int, label: str | None = None) -> dict:
    """Update last_used_at + use_count (nebo insert). Pak trim na MAX entries."""
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserRecent)
            .filter(
                ErpUserRecent.user_id == user_id,
                ErpUserRecent.tenant_id == tenant_id,
                ErpUserRecent.menu_node_id == menu_node_id,
            )
            .one_or_none()
        )
        now = _now()
        if existing:
            existing.last_used_at = now
            existing.use_count = (existing.use_count or 0) + 1
            if label:
                existing.label = label
            ds.commit()
            ds.refresh(existing)
            result = _serialize_recent(existing)
        else:
            new_rec = ErpUserRecent(
                user_id=user_id,
                tenant_id=tenant_id,
                menu_node_id=menu_node_id,
                label=label,
                last_used_at=now,
                use_count=1,
            )
            ds.add(new_rec)
            ds.commit()
            ds.refresh(new_rec)
            result = _serialize_recent(new_rec)

        # Trim: keep top N podle last_used_at, smaž starší
        all_rows = (
            ds.query(ErpUserRecent)
            .filter(
                ErpUserRecent.user_id == user_id,
                ErpUserRecent.tenant_id == tenant_id,
            )
            .order_by(desc(ErpUserRecent.last_used_at))
            .all()
        )
        if len(all_rows) > MAX_RECENT_PER_USER_TENANT:
            for old in all_rows[MAX_RECENT_PER_USER_TENANT:]:
                ds.delete(old)
            ds.commit()

        return result
    except IntegrityError:
        ds.rollback()
        raise ErpUserStateError(f"Recent track menu_node_id={menu_node_id} race condition")
    finally:
        ds.close()


def clear_recent(user_id: int, tenant_id: int) -> int:
    ds = get_data_session()
    try:
        deleted = (
            ds.query(ErpUserRecent)
            .filter(
                ErpUserRecent.user_id == user_id,
                ErpUserRecent.tenant_id == tenant_id,
            )
            .delete()
        )
        ds.commit()
        return int(deleted or 0)
    finally:
        ds.close()


# ── TREE ORDER (D&D persistence per skupina) ──────────────────────────

def get_tree_order(user_id: int, tenant_id: int) -> dict[str, list]:
    """Vrať dict {group_key: [tree-item-id, ...]} pro restore D&D order."""
    ds = get_data_session()
    try:
        rows = (
            ds.query(ErpUserTreeOrder)
            .filter(
                ErpUserTreeOrder.user_id == user_id,
                ErpUserTreeOrder.tenant_id == tenant_id,
            )
            .all()
        )
        return {r.group_key: list(r.order_array or []) for r in rows}
    finally:
        ds.close()


def save_tree_order(
    user_id: int, tenant_id: int, group_key: str, order_array: list[str]
) -> None:
    """Upsert order pro daný group_key."""
    ds = get_data_session()
    try:
        existing = (
            ds.query(ErpUserTreeOrder)
            .filter(
                ErpUserTreeOrder.user_id == user_id,
                ErpUserTreeOrder.tenant_id == tenant_id,
                ErpUserTreeOrder.group_key == group_key,
            )
            .one_or_none()
        )
        now = _now()
        if existing:
            existing.order_array = order_array
            existing.updated_at = now
        else:
            new = ErpUserTreeOrder(
                user_id=user_id,
                tenant_id=tenant_id,
                group_key=group_key,
                order_array=order_array,
                updated_at=now,
            )
            ds.add(new)
        ds.commit()
    except IntegrityError:
        ds.rollback()
        raise ErpUserStateError(f"Tree order {group_key} race condition")
    finally:
        ds.close()


def reset_tree_order(user_id: int, tenant_id: int) -> int:
    ds = get_data_session()
    try:
        deleted = (
            ds.query(ErpUserTreeOrder)
            .filter(
                ErpUserTreeOrder.user_id == user_id,
                ErpUserTreeOrder.tenant_id == tenant_id,
            )
            .delete()
        )
        ds.commit()
        return int(deleted or 0)
    finally:
        ds.close()
