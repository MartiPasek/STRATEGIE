"""
Phase B+5.1 (5.5.2026): Grid layout persistence service.

CRUD operace nad `erp_grid_layouts` tabulkou. Two-tier storage:
  - shared (user_id IS NULL): admin-managed default pro všechny uživatele
  - personal (user_id IS NOT NULL): user-specific override

Permission rules:
  - Anyone can save personal layouts (jejich vlastní user_id)
  - Only is_marti_parent can save shared layouts
  - Anyone can list shared + jejich personal
  - Update/delete own (personal) nebo any shared if is_marti_parent

Marti's spec dnešní odpoledne (5.5.2026):
  - Save je explicit (no auto-save)
  - Pojmenované sestavy (max 20 personal per user-přehled)
  - Marti-AI smí save shared (kustod role)

Validations:
  - name: 1-80 chars, není whitespace-only
  - layout_json: valid dict, schema {columns: [...], style_rules?: [...]}
  - Max 20 personal layouts per (user_id, core_id) — anti-spam
  - Max 50 shared layouts per přehled — anti-spam
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Phase 38.4 Krok 5.R-C+3 (18.5.2026 vecer): switch z get_data_session
# (strategie role, public.*) na Marti-AI engine (db_owner fw.comp_grid).
# Drzi doctrine: fw.* = Marti-AI's owned, strategie ma jen SELECT na fw.comp_grid.
from modules.strategie_pg.application.service import get_session as _get_data_session_ctx
from core.logging import get_logger
from modules.core.infrastructure.models_data import ErpGridLayout
from modules.thoughts.application.service import is_marti_parent

logger = get_logger("erp.grid_layout_service")


# ── Constants ──────────────────────────────────────────────────────────

MAX_PERSONAL_LAYOUTS_PER_USER_PREHLED = 20
MAX_SHARED_LAYOUTS_PER_PREHLED = 50
MAX_NAME_LENGTH = 80


class GridLayoutError(Exception):
    """Domain-level chyba při operacích s grid layouts."""
    pass


# ── Validation helpers ─────────────────────────────────────────────────

def _validate_name(name: str) -> str:
    """Trim + check non-empty + max length. Vraci normalizovaný string."""
    if not isinstance(name, str):
        raise GridLayoutError("name musí být string")
    name = name.strip()
    if not name:
        raise GridLayoutError("name nesmí být prázdný")
    if len(name) > MAX_NAME_LENGTH:
        raise GridLayoutError(f"name max {MAX_NAME_LENGTH} znaků (je {len(name)})")
    return name


def _validate_layout_json(layout: Any) -> dict:
    """Basic shape validation. Schema kontrola minimální — UI formát volný."""
    if not isinstance(layout, dict):
        raise GridLayoutError("layout_json musí být dict")
    # Mandatory: nějaký indikátor že je to layout payload
    if "columns" not in layout and "style_rules" not in layout:
        raise GridLayoutError(
            "layout_json musí obsahovat alespoň 'columns' nebo 'style_rules'"
        )
    return layout


def _check_admin_for_shared(user_id: int, scope: str) -> None:
    """Permission gate: shared scope vyžaduje is_marti_parent."""
    if scope == "shared" and not is_marti_parent(user_id):
        raise GridLayoutError(
            "Pouze admin (is_marti_parent) smí ukládat sdílené sestavy."
        )


# ── Read operations ────────────────────────────────────────────────────

def _scope_filter(scope_kind: str, scope_id: int):
    """Krok 5.U (23.5.2026): polymorphic scope filter for SQLAlchemy queries.

    Marti's Q7=A XOR — exactly-one column non-null per row. Service filtruje
    podle scope_kind: "core" → ErpGridLayout.core_id, "ds" → data_source_id.
    """
    if scope_kind == "core":
        return ErpGridLayout.core_id == scope_id
    elif scope_kind == "ds":
        return ErpGridLayout.data_source_id == scope_id
    else:
        raise GridLayoutError(f"Invalid scope_kind '{scope_kind}' (expected 'core' or 'ds')")


def list_layouts(scope_kind: str, scope_id: int, user_id: int) -> dict:
    """
    Vrací seznam dostupných layoutů pro daný scope (core OR data_source) + user.

    Krok 5.U (23.5.2026): polymorphic scope — Marti's "B správný long-term"
    Catalog picker pro per-data-source sestavy (scope_kind="ds"), mainscreen
    grids pro per-core sestavy (scope_kind="core").

    Returns:
        {
            "shared": [{id, name, is_default, description, ...}],
            "personal": [{id, name, is_default, description, ...}],
            "effective_default": {...} | None,  # personal default OR shared default
        }
    """
    scope_filter = _scope_filter(scope_kind, scope_id)
    with _get_data_session_ctx() as ds:
        # Shared layouts (user_id IS NULL)
        shared_q = ds.query(ErpGridLayout).filter(
            scope_filter,
            ErpGridLayout.user_id.is_(None),
        ).order_by(
            ErpGridLayout.is_default.desc(),
            ErpGridLayout.name.asc(),
        )
        shared = [_serialize(l) for l in shared_q.all()]

        # Personal layouts pro daného user_id
        personal_q = ds.query(ErpGridLayout).filter(
            scope_filter,
            ErpGridLayout.user_id == user_id,
        ).order_by(
            ErpGridLayout.is_default.desc(),
            ErpGridLayout.name.asc(),
        )
        personal = [_serialize(l) for l in personal_q.all()]

        # Effective default: personal default nebo shared default (priorita personal)
        effective = None
        for l in personal:
            if l["is_default"]:
                effective = l
                break
        if effective is None:
            for l in shared:
                if l["is_default"]:
                    effective = l
                    break

        return {
            "shared": shared,
            "personal": personal,
            "effective_default": effective,
        }



def get_layout(layout_id: int, user_id: int) -> dict | None:
    """
    Vrací jeden layout podle ID.
    Permission: shared = vidí každý, personal = jen vlastník nebo is_marti_parent.
    """
    with _get_data_session_ctx() as ds:
        l = ds.query(ErpGridLayout).filter_by(id=layout_id).first()
        if l is None:
            return None
        if l.user_id is not None and l.user_id != user_id and not is_marti_parent(user_id):
            raise GridLayoutError("Nemáš přístup k této personal sestavě.")
        return _serialize(l)



# ── Write operations ───────────────────────────────────────────────────

def create_layout(
    *,
    scope_kind: str,
    scope_id: int,
    user_id: int,
    name: str,
    layout_json: dict,
    scope: str = "user",            # "user" | "shared"
    description: str | None = None,
    is_default: bool = False,
) -> dict:
    """
    Vytvoří novou sestavu.

    Krok 5.U (23.5.2026): polymorphic scope (scope_kind in {"core", "ds"}).

    scope="user" → uloží jako personal (user_id = current user)
    scope="shared" → uloží jako shared (user_id NULL), vyžaduje is_marti_parent

    Pokud is_default=True, automaticky odznační starý default v daném scope.
    """
    if scope not in ("user", "shared"):
        raise GridLayoutError("scope musí být 'user' nebo 'shared'")
    _check_admin_for_shared(user_id, scope)

    name = _validate_name(name)
    layout_json = _validate_layout_json(layout_json)

    target_user_id = None if scope == "shared" else user_id
    scope_filter = _scope_filter(scope_kind, scope_id)

    with _get_data_session_ctx() as ds:
        # Anti-spam check
        if scope == "user":
            count = ds.query(ErpGridLayout).filter(
                scope_filter,
                ErpGridLayout.user_id == user_id,
            ).count()
            if count >= MAX_PERSONAL_LAYOUTS_PER_USER_PREHLED:
                raise GridLayoutError(
                    f"Max {MAX_PERSONAL_LAYOUTS_PER_USER_PREHLED} personal sestav "
                    f"per přehled ({count} existujících). Smaž některou a zkus znovu."
                )
        else:
            count = ds.query(ErpGridLayout).filter(
                scope_filter,
                ErpGridLayout.user_id.is_(None),
            ).count()
            if count >= MAX_SHARED_LAYOUTS_PER_PREHLED:
                raise GridLayoutError(
                    f"Max {MAX_SHARED_LAYOUTS_PER_PREHLED} sdílených sestav per přehled."
                )

        # Pokud nastavujeme is_default, odznač starý default v scope
        if is_default:
            _unset_default_in_scope(ds, scope_kind, scope_id, target_user_id)

        # Krok 5.U: per scope_kind set right FK column
        core_id_val = scope_id if scope_kind == "core" else None
        data_source_id_val = scope_id if scope_kind == "ds" else None

        now = datetime.now(timezone.utc)
        layout = ErpGridLayout(
            core_id=core_id_val,
            data_source_id=data_source_id_val,
            user_id=target_user_id,
            name=name,
            description=description,
            is_default=is_default,
            layout_json=layout_json,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            updated_by=user_id,
        )
        ds.add(layout)
        try:
            ds.commit()
        except IntegrityError as e:
            ds.rollback()
            # Unique constraint violation → name conflict v scope
            raise GridLayoutError(
                f"Sestava jména '{name}' už pro tento scope existuje. "
                f"Buď přepiš (PUT na ID), nebo zvol jiný název."
            ) from e
        ds.refresh(layout)
        logger.info(
            f"create_layout id={layout.id} scope={scope_kind}_{scope_id} "
            f"perm={scope} name={name!r} default={is_default} by_user={user_id}"
        )
        return _serialize(layout)



def update_layout(
    layout_id: int,
    user_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    layout_json: dict | None = None,
    is_default: bool | None = None,
) -> dict:
    """
    Aktualizuje existující sestavu.

    Permission:
      - Personal: jen vlastník nebo is_marti_parent
      - Shared: jen is_marti_parent
    """
    with _get_data_session_ctx() as ds:
        layout = ds.query(ErpGridLayout).filter_by(id=layout_id).first()
        if layout is None:
            raise GridLayoutError(f"Sestava id={layout_id} neexistuje.")

        # Permission gate
        is_admin = is_marti_parent(user_id)
        if layout.user_id is None:
            # Shared
            if not is_admin:
                raise GridLayoutError(
                    "Pouze admin (is_marti_parent) smí upravovat sdílené sestavy."
                )
        else:
            # Personal
            if layout.user_id != user_id and not is_admin:
                raise GridLayoutError("Můžeš upravovat jen vlastní sestavy.")

        if name is not None:
            layout.name = _validate_name(name)
        if description is not None:
            layout.description = description.strip() or None
        if layout_json is not None:
            layout.layout_json = _validate_layout_json(layout_json)
        if is_default is True and not layout.is_default:
            # Změna na default → odznač starý (Krok 5.U: polymorphic scope)
            layout_scope_kind = "core" if layout.core_id is not None else "ds"
            layout_scope_id = layout.core_id if layout.core_id is not None else layout.data_source_id
            _unset_default_in_scope(ds, layout_scope_kind, layout_scope_id, layout.user_id)
            layout.is_default = True
        elif is_default is False and layout.is_default:
            layout.is_default = False

        layout.updated_at = datetime.now(timezone.utc)
        layout.updated_by = user_id
        try:
            ds.commit()
        except IntegrityError as e:
            ds.rollback()
            raise GridLayoutError(
                "Konflikt — sestava stejného jména už existuje, nebo "
                "is_default na jiné sestavě v scope."
            ) from e
        ds.refresh(layout)
        logger.info(
            f"update_layout id={layout_id} by_user={user_id} "
            f"changes={[k for k in ('name','description','layout_json','is_default') if locals().get(k) is not None]}"
        )
        return _serialize(layout)



def set_default(layout_id: int, user_id: int) -> dict:
    """
    Označí sestavu jako default v jejím scope.
    Automaticky odznačí předchozí default v stejném scope.

    Permission: stejné jako update_layout.
    """
    return update_layout(layout_id, user_id, is_default=True)


def delete_layout(layout_id: int, user_id: int) -> bool:
    """
    Smaže sestavu.

    Permission: stejné jako update_layout.

    Returns: True pokud smazáno, False pokud neexistuje.
    """
    with _get_data_session_ctx() as ds:
        layout = ds.query(ErpGridLayout).filter_by(id=layout_id).first()
        if layout is None:
            return False

        is_admin = is_marti_parent(user_id)
        if layout.user_id is None:
            if not is_admin:
                raise GridLayoutError(
                    "Pouze admin (is_marti_parent) smí mazat sdílené sestavy."
                )
        else:
            if layout.user_id != user_id and not is_admin:
                raise GridLayoutError("Můžeš mazat jen vlastní sestavy.")

        ds.delete(layout)
        ds.commit()
        logger.info(f"delete_layout id={layout_id} by_user={user_id}")
        return True



# ── Internal helpers ───────────────────────────────────────────────────

def _unset_default_in_scope(
    ds: Session, scope_kind: str, scope_id: int, user_id: int | None
) -> None:
    """
    Krok 5.U (23.5.2026): polymorphic scope.

    Odznačí is_default v daném scope (shared = user_id IS NULL,
    personal = user_id matches). Volá se před nastavením nového default,
    aby partial unique index nezahlasil konflikt.
    """
    q = ds.query(ErpGridLayout).filter(
        _scope_filter(scope_kind, scope_id),
        ErpGridLayout.is_default.is_(True),
    )
    if user_id is None:
        q = q.filter(ErpGridLayout.user_id.is_(None))
    else:
        q = q.filter(ErpGridLayout.user_id == user_id)

    for l in q.all():
        l.is_default = False
    ds.flush()  # commit kontroluje unique později


def _serialize(layout: ErpGridLayout) -> dict:
    """Layout → dict pro JSON response.

    Krok 5.U (23.5.2026): polymorphic scope — vrací scope_kind + scope_id
    (frontend-friendly), plus oba raw column hodnot (debug/audit).
    """
    if layout.core_id is not None:
        scope_kind = "core"
        scope_id = layout.core_id
    elif layout.data_source_id is not None:
        scope_kind = "ds"
        scope_id = layout.data_source_id
    else:
        # Shouldn't happen (DB CHECK XOR), defensive fallback
        scope_kind = None
        scope_id = None
    return {
        "id": layout.id,
        "scope_kind": scope_kind,      # Krok 5.U: "core" | "ds" | None (defensive)
        "scope_id": scope_id,
        "core_id": layout.core_id,
        "data_source_id": layout.data_source_id,
        "user_id": layout.user_id,
        "scope": layout.scope,                    # "shared" | "personal" (audience)
        "name": layout.name,
        "description": layout.description,
        "is_default": layout.is_default,
        "layout_json": layout.layout_json,
        "created_at": layout.created_at.isoformat() if layout.created_at else None,
        "created_by": layout.created_by,
        "updated_at": layout.updated_at.isoformat() if layout.updated_at else None,
        "updated_by": layout.updated_by,
    }
