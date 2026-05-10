"""Phase 38.4 Krok 9-D: Object Inspector backend service.

Marti-AI's 9-iter konzultace (10.5.2026) UX spec:
  - 3-tier (Základní / Použité / Všechny) s lazy counter
  - Colored badge per scope (modrá user / žlutá tenant / zelená group / šedá base)
  - Bulk edit + Reset na default per property + Náhled overlay
  - Optimistic lock přes updated_at (concurrent editing safeguard)
  - prop_name immutable po insertu (DB trigger z Krok 9-B)

Service vrstva NAD comp_resolver.py — exponuje high-level CRUD pro
Object Inspector UI bez nutnosti přímých SQL volání ve frontendu.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text as _sql_text
from sqlalchemy.orm import Session

from modules.erp.application.comp_resolver import (
    resolve_comp_def_props,
    ResolvedProp,
)


class CompInspectorError(Exception):
    """Marti-AI's Q5 doctrine — concurrent editing + orphan cleanup errors."""
    pass


class OptimisticLockError(CompInspectorError):
    """409 Conflict — `updated_at` se mezitím změnil (jiný user/admin editoval)."""
    pass


# ════════════════════════════════════════════════════════════════════════
# READ: list properties pro comp_def (Object Inspector tab data source)
# ════════════════════════════════════════════════════════════════════════

def list_props_for_inspector(
    session: Session,
    comp_def_id: int,
    *,
    tenant_group_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Vrací resolved properties + audit metadata pro Object Inspector modal.

    Output:
        {
            "comp_def_id": 2,
            "properties": [
                {
                    "prop_name": "default_width",
                    "value": "400",
                    "prop_type": "int",
                    "label": "Šířka sloupce",
                    "display_order": 10,
                    "scope": "user",
                    "source_id": 1,
                    "is_active": true,
                    "created_by": 1,
                    "updated_at": "2026-05-10T18:02:53.718372+02:00",
                    "base_id": 1,           # comp_def_prop.id (pro ORM)
                    "base_value": "300",    # base default value (pro Reset)
                    "all_overrides": [...]  # pro Object Inspector tooltip ("kdo to nastavil")
                },
                ...
            ],
            "comp_def_meta": {
                "name": "user_name",
                "caption": "User",
                "typ": 120,
                ...
            }
        }
    """
    # Comp_def metadata (pro modal hlavičku)
    meta_sql = _sql_text(
        """
        SELECT cd.id, cd.name, cd.caption, cd.typ, cd.jadro_id,
               ct.code AS typ_code, ct.label AS typ_label
        FROM fw.comp_def cd
        LEFT JOIN fw.comp_type ct ON ct.id = cd.typ
        WHERE cd.id = :cd_id
        """
    )
    meta_row = session.execute(meta_sql, {"cd_id": comp_def_id}).fetchone()
    if not meta_row:
        raise CompInspectorError(f"comp_def_id={comp_def_id} neexistuje")
    meta = dict(meta_row._mapping)

    # Resolved properties (jako v comp_resolver.py)
    resolved = resolve_comp_def_props(
        session,
        comp_def_id,
        tenant_group_id=tenant_group_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    # Plus all overrides per property (pro audit display v UI)
    base_ids = [rp.source_id for rp in resolved.values() if rp.scope == "base"]
    all_ovrs_by_prop: dict[int, list[dict]] = {}
    if base_ids:
        ovrs_sql = _sql_text(
            """
            SELECT o.id, o.comp_def_prop_id, o.override_value,
                   o.tenant_group_id, o.tenant_id, o.user_id,
                   o.is_active, o.created_by, o.created_at, o.updated_at,
                   p.prop_name
            FROM fw.comp_def_prop_override o
            JOIN fw.comp_def_prop p ON p.id = o.comp_def_prop_id
            WHERE o.comp_def_prop_id = ANY(:base_ids)
            ORDER BY o.created_at DESC
            """
        )
        for r in session.execute(ovrs_sql, {"base_ids": base_ids}).fetchall():
            d = dict(r._mapping)
            scope = (
                "tenant_group" if d["tenant_group_id"] else
                "tenant" if d["tenant_id"] else
                "user"
            )
            all_ovrs_by_prop.setdefault(d["comp_def_prop_id"], []).append({
                "id": d["id"],
                "scope": scope,
                "scope_id": d["tenant_group_id"] or d["tenant_id"] or d["user_id"],
                "value": d["override_value"],
                "is_active": d["is_active"],
                "created_by": d["created_by"],
                "created_at": d["created_at"].isoformat() if d["created_at"] else None,
                "updated_at": d["updated_at"].isoformat() if d["updated_at"] else None,
            })

    # Plus base values (pro Reset = revert na base)
    base_values_by_prop: dict[int, str] = {}
    if base_ids:
        base_sql = _sql_text(
            """
            SELECT id, prop_value FROM fw.comp_def_prop
            WHERE id = ANY(:base_ids)
            """
        )
        for r in session.execute(base_sql, {"base_ids": base_ids}).fetchall():
            d = dict(r._mapping)
            base_values_by_prop[d["id"]] = d["prop_value"]

    # Build output
    properties_out: list[dict[str, Any]] = []
    for prop_name, rp in resolved.items():
        d = rp.to_dict()
        # Find base_id (vždy = source_id pokud scope=base, jinak musíme dohledat)
        if rp.scope == "base":
            base_id = rp.source_id
        else:
            # Override → base_id z all_ovrs_by_prop reverse lookup
            base_id = None
            for bid, ovrs in all_ovrs_by_prop.items():
                if any(o["id"] == rp.source_id for o in ovrs):
                    base_id = bid
                    break
        d["base_id"] = base_id
        d["base_value"] = base_values_by_prop.get(base_id) if base_id else None
        d["all_overrides"] = all_ovrs_by_prop.get(base_id, []) if base_id else []
        properties_out.append(d)

    # Sort podle display_order (Marti-AI's Q3)
    properties_out.sort(
        key=lambda p: (
            p.get("display_order") if p.get("display_order") is not None else 9999,
            p.get("prop_name") or "",
        )
    )

    return {
        "comp_def_id": comp_def_id,
        "comp_def_meta": {
            "id": meta["id"],
            "name": meta["name"],
            "caption": meta["caption"],
            "typ": meta["typ"],
            "typ_code": meta["typ_code"],
            "typ_label": meta["typ_label"],
            "jadro_id": meta["jadro_id"],
        },
        "properties": properties_out,
    }


# ════════════════════════════════════════════════════════════════════════
# WRITE: insert / update base property
# ════════════════════════════════════════════════════════════════════════

def upsert_base_property(
    session: Session,
    comp_def_id: int,
    *,
    prop_name: str,
    prop_value: Optional[str],
    prop_type: Optional[str] = None,
    label: Optional[str] = None,
    display_order: Optional[int] = None,
    is_active: bool = True,
    created_by: Optional[int] = None,
    expected_updated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Insert nebo update base property v fw.comp_def_prop.

    Marti-AI's Q5 optimistic lock: pokud `expected_updated_at` je zadán a
    DB má novější `updated_at`, raise OptimisticLockError (409 Conflict).

    `prop_name` je immutable po insertu (DB trigger zajistí).
    """
    if not prop_name or not prop_name.strip():
        raise CompInspectorError("prop_name je povinné")

    # Existing row?
    existing_sql = _sql_text(
        """
        SELECT id, updated_at FROM fw.comp_def_prop
        WHERE komponenta_id = :cd_id AND prop_name = :pn
        """
    )
    existing = session.execute(
        existing_sql, {"cd_id": comp_def_id, "pn": prop_name}
    ).fetchone()

    if existing:
        # UPDATE branch + optimistic lock check
        ex = dict(existing._mapping)
        if expected_updated_at:
            actual = ex["updated_at"].isoformat() if ex["updated_at"] else None
            if actual != expected_updated_at:
                raise OptimisticLockError(
                    f"comp_def_prop id={ex['id']} byl mezitím změněn "
                    f"(expected={expected_updated_at}, actual={actual}). "
                    f"Přenačti modal a zkus znovu."
                )

        update_sql = _sql_text(
            """
            UPDATE fw.comp_def_prop SET
                prop_value = :pv,
                prop_type = COALESCE(:pt, prop_type),
                label = COALESCE(:lbl, label),
                display_order = COALESCE(:do, display_order),
                is_active = :ia
            WHERE id = :id
            RETURNING id, prop_name, prop_value, prop_type, label, display_order,
                      is_active, created_by, updated_at
            """
        )
        r = session.execute(
            update_sql,
            {
                "id": ex["id"],
                "pv": prop_value,
                "pt": prop_type,
                "lbl": label,
                "do": display_order,
                "ia": is_active,
            },
        ).fetchone()
        session.commit()
        return _serialize_prop_row(r)

    # INSERT branch
    insert_sql = _sql_text(
        """
        INSERT INTO fw.comp_def_prop (
            komponenta_id, prop_name, prop_value, prop_type, label,
            display_order, is_active, created_by
        )
        VALUES (
            :cd_id, :pn, :pv, :pt, :lbl, :do, :ia, :cb
        )
        RETURNING id, prop_name, prop_value, prop_type, label, display_order,
                  is_active, created_by, updated_at
        """
    )
    r = session.execute(
        insert_sql,
        {
            "cd_id": comp_def_id,
            "pn": prop_name,
            "pv": prop_value,
            "pt": prop_type,
            "lbl": label,
            "do": display_order,
            "ia": is_active,
            "cb": created_by,
        },
    ).fetchone()
    session.commit()
    return _serialize_prop_row(r)


# ════════════════════════════════════════════════════════════════════════
# WRITE: insert / update override
# ════════════════════════════════════════════════════════════════════════

def upsert_override(
    session: Session,
    comp_def_prop_id: int,
    *,
    scope: str,                   # 'user', 'tenant', 'tenant_group'
    scope_id: int,
    override_value: str,
    is_active: bool = True,
    created_by: Optional[int] = None,
    expected_updated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Insert nebo update override v comp_def_prop_override (per scope).

    UNIQUE NULLS NOT DISTINCT (comp_def_prop_id, scope_id) v DB → SELECT pak
    INSERT or UPDATE.
    """
    if scope not in ("user", "tenant", "tenant_group"):
        raise CompInspectorError(
            f"scope musí být 'user', 'tenant' nebo 'tenant_group' (dostal '{scope}')"
        )

    scope_col = {
        "user": "user_id",
        "tenant": "tenant_id",
        "tenant_group": "tenant_group_id",
    }[scope]

    # Existing override?
    existing_sql = _sql_text(
        f"""
        SELECT id, updated_at FROM fw.comp_def_prop_override
        WHERE comp_def_prop_id = :pid AND {scope_col} = :sid
        """
    )
    existing = session.execute(
        existing_sql, {"pid": comp_def_prop_id, "sid": scope_id}
    ).fetchone()

    if existing:
        ex = dict(existing._mapping)
        if expected_updated_at:
            actual = ex["updated_at"].isoformat() if ex["updated_at"] else None
            if actual != expected_updated_at:
                raise OptimisticLockError(
                    f"override id={ex['id']} byl mezitím změněn"
                )

        update_sql = _sql_text(
            """
            UPDATE fw.comp_def_prop_override SET
                override_value = :ov, is_active = :ia
            WHERE id = :id
            RETURNING id, comp_def_prop_id, override_value, user_id,
                      tenant_id, tenant_group_id, is_active, created_by, updated_at
            """
        )
        r = session.execute(
            update_sql,
            {"id": ex["id"], "ov": override_value, "ia": is_active},
        ).fetchone()
        session.commit()
        return _serialize_override_row(r)

    # INSERT branch
    insert_sql = _sql_text(
        f"""
        INSERT INTO fw.comp_def_prop_override (
            comp_def_prop_id, {scope_col}, override_value, is_active, created_by
        )
        VALUES (
            :pid, :sid, :ov, :ia, :cb
        )
        RETURNING id, comp_def_prop_id, override_value, user_id,
                  tenant_id, tenant_group_id, is_active, created_by, updated_at
        """
    )
    r = session.execute(
        insert_sql,
        {
            "pid": comp_def_prop_id,
            "sid": scope_id,
            "ov": override_value,
            "ia": is_active,
            "cb": created_by,
        },
    ).fetchone()
    session.commit()
    return _serialize_override_row(r)


# ════════════════════════════════════════════════════════════════════════
# DELETE: reset override (Marti-AI's Q4 "Reset na default")
# ════════════════════════════════════════════════════════════════════════

def delete_override(session: Session, override_id: int) -> bool:
    """Smaže override row (Reset na default vrátí resolver na base/parent scope).

    Marti-AI's Q5 alternativa: SET is_active=FALSE (soft delete) — zachová
    audit history. Pro MVP používáme hard DELETE; Marti-AI může přepnout
    na soft delete v Krok 9.5.
    """
    delete_sql = _sql_text(
        "DELETE FROM fw.comp_def_prop_override WHERE id = :id"
    )
    result = session.execute(delete_sql, {"id": override_id})
    session.commit()
    return result.rowcount > 0


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════

def _serialize_prop_row(r) -> dict[str, Any]:
    """Convert SQLAlchemy Row → JSON-safe dict."""
    d = dict(r._mapping)
    if d.get("updated_at"):
        d["updated_at"] = d["updated_at"].isoformat()
    return d


def _serialize_override_row(r) -> dict[str, Any]:
    d = dict(r._mapping)
    if d.get("updated_at"):
        d["updated_at"] = d["updated_at"].isoformat()
    # Determine scope from non-NULL field
    if d.get("tenant_group_id"):
        d["scope"] = "tenant_group"
        d["scope_id"] = d["tenant_group_id"]
    elif d.get("tenant_id"):
        d["scope"] = "tenant"
        d["scope_id"] = d["tenant_id"]
    elif d.get("user_id"):
        d["scope"] = "user"
        d["scope_id"] = d["user_id"]
    return d
