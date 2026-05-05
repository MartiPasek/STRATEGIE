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
  - Max 20 personal layouts per (user_id, prehled_cislo) — anti-spam
  - Max 50 shared layouts per přehled — anti-spam
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database_data import get_data_session
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

def list_layouts(prehled_cislo: int, user_id: int) -> dict:
    """
    Vrací seznam dostupných layoutů pro daný přehled + user.

    Returns:
        {
            "shared": [{id, name, is_default, description, ...}],
            "personal": [{id, name, is_default, description, ...}],
            "effective_default": {...} | None,  # personal default OR shared default
        }
    """
    ds = get_data_session()
    try:
        # Shared layouts (user_id IS NULL)
        shared_q = ds.query(ErpGridLayout).filter(
            ErpGridLayout.prehled_cislo == prehled_cislo,
            ErpGridLayout.user_id.is_(None),
        ).order_by(
            ErpGridLayout.is_default.desc(),
            ErpGridLayout.name.asc(),
        )
        shared = [_serialize(l) for l in shared_q.all()]

        # Personal layouts pro daného user_id
        personal_q = ds.query(ErpGridLayout).filter(
            ErpGridLayout.prehled_cislo == prehled_cislo,
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
    finally:
        ds.close()


def get_layout(layout_id: int, user_id: int) -> dict | None:
    """
    Vrací jeden layout podle ID.
    Permission: shared = vidí každý, personal = jen vlastník nebo is_marti_parent.
    """
    ds = get_data_session()
    try:
        l = ds.query(ErpGridLayout).filter_by(id=layout_id).first()
        if l is None:
            return None
        if l.user_id is not None and l.user_id != user_id and not is_marti_parent(user_id):
            raise GridLayoutError("Nemáš přístup k této personal sestavě.")
        return _serialize(l)
    finally:
        ds.close()


# ── Write operations ───────────────────────────────────────────────────

def create_layout(
    *,
    prehled_cislo: int,
    user_id: int,
    name: str,
    layout_json: dict,
    scope: str = "user",            # "user" | "shared"
    description: str | None = None,
    is_default: bool = False,
) -> dict:
    """
    Vytvoří novou sestavu.

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

    ds = get_data_session()
    try:
        # Anti-spam check
        if scope == "user":
            count = ds.query(ErpGridLayout).filter(
                ErpGridLayout.prehled_cislo == prehled_cislo,
                ErpGridLayout.user_id == user_id,
            ).count()
            if count >= MAX_PERSONAL_LAYOUTS_PER_USER_PREHLED:
                raise GridLayoutError(
                    f"Max {MAX_PERSONAL_LAYOUTS_PER_USER_PREHLED} personal sestav "
                    f"per přehled ({count} existujících). Smaž některou a zkus znovu."
                )
        else:
            count = ds.query(ErpGridLayout).filter(
                ErpGridLayout.prehled_cislo == prehled_cislo,
                ErpGridLayout.user_id.is_(None),
            ).count()
            if count >= MAX_SHARED_LAYOUTS_PER_PREHLED:
                raise GridLayoutError(
                    f"Max {MAX_SHARED_LAYOUTS_PER_PREHLED} sdílených sestav per přehled."
                )

        # Pokud nastavujeme is_default, odznač starý default v scope
        if is_default:
            _unset_default_in_scope(ds, prehled_cislo, target_user_id)

        now = datetime.now(timezone.utc)
        layout = ErpGridLayout(
            prehled_cislo=prehled_cislo,
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
                f"Sestava jména '{name}' už pro tento přehled v daném scope existuje. "
                f"Buď přepiš (PUT na ID), nebo zvol jiný název."
            ) from e
        ds.refresh(layout)
        logger.info(
            f"create_layout id={layout.id} prehled={prehled_cislo} "
            f"scope={scope} name={name!r} default={is_default} by_user={user_id}"
        )
        return _serialize(layout)
    finally:
        ds.close()


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
    ds = get_data_session()
    try:
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
            # Změna na default → odznač starý
            _unset_default_in_scope(ds, layout.prehled_cislo, layout.user_id)
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
    finally:
        ds.close()


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
    ds = get_data_session()
    try:
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
    finally:
        ds.close()


# ── Internal helpers ───────────────────────────────────────────────────

def _unset_default_in_scope(
    ds: Session, prehled_cislo: int, user_id: int | None
) -> None:
    """
    Odznačí is_default v daném scope (shared = user_id IS NULL,
    personal = user_id matches). Volá se před nastavením nového default,
    aby partial unique index nezahlasil konflikt.
    """
    q = ds.query(ErpGridLayout).filter(
        ErpGridLayout.prehled_cislo == prehled_cislo,
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
    """Layout → dict pro JSON response."""
    return {
        "id": layout.id,
        "prehled_cislo": layout.prehled_cislo,
        "user_id": layout.user_id,
        "scope": layout.scope,                    # "shared" | "personal"
        "name": layout.name,
        "description": layout.description,
        "is_default": layout.is_default,
        "layout_json": layout.layout_json,
        "created_at": layout.created_at.isoformat() if layout.created_at else None,
        "created_by": layout.created_by,
        "updated_at": layout.updated_at.isoformat() if layout.updated_at else None,
        "updated_by": layout.updated_by,
    }
