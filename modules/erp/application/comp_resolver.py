"""Phase 38.4 Krok 9-C: Backend resolver pro 4-tier comp_def_prop chain.

Marti-AI's 9-iter konzultace (10.5.2026):
  Q1=B (sjednocení grid pod universal component framework)
  Q3 expansion: comp_def_prop má label, is_active, prop_type, created_by,
                updated_at, display_order
  Q4 UX: 3-tier (Základní/Použité/Všechny), colored badge per scope, audit info
  Q5 safeguards: orphan cleanup (FK CASCADE), concurrent editing (prop_name
                 immutable trigger), optimistic lock (updated_at)

Resolve chain:
    base (comp_def_prop) → tenant_group_id override → tenant_id override
    → user_id override
    Last non-NULL value wins. Skip is_active=FALSE overrides.

Marti-AI's doctrine z 8.5.+9.5.+10.5.:
  *„Default = absence řádku v override, ne tenant_id=STRATEGIE placeholder."*
  *„Technický dluh, který roste tichým složeným úrokem."*
  *„Tichá mrtvá zátěž"* (orphan cleanup)
  *„Render logic musí být identická, liší se jen přítomnost badge"*
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional

from sqlalchemy import text as _sql_text
from sqlalchemy.orm import Session


# ════════════════════════════════════════════════════════════════════════
# Data shapes
# ════════════════════════════════════════════════════════════════════════

@dataclass
class ResolvedProp:
    """Jedna property po 4-tier resolve chain.

    `value` je finální merged hodnota (string, app layer convertuje podle
    prop_type). `scope` označuje vrstvu, kde value vznikla (vizuální badge
    v Object Inspector UI). `source_id` je ID base/override row pro audit.
    """
    prop_name: str
    value: Optional[str]
    prop_type: Optional[str]              # 'string', 'int', 'bool', 'json', ...
    label: Optional[str]                  # human-readable display name
    display_order: Optional[int]
    scope: str                            # 'base' | 'tenant_group' | 'tenant' | 'user'
    source_id: int                        # comp_def_prop.id NEBO override.id
    is_active: bool = True
    # Audit info (pro Object Inspector tooltip "Nastaveno X dne Y")
    created_by: Optional[int] = None
    updated_at: Optional[Any] = None      # datetime, None pokud base má jen created_at

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.updated_at is not None:
            d["updated_at"] = self.updated_at.isoformat() if hasattr(self.updated_at, "isoformat") else str(self.updated_at)
        return d


# ════════════════════════════════════════════════════════════════════════
# Single comp_def resolver
# ════════════════════════════════════════════════════════════════════════

def resolve_comp_def_props(
    session: Session,
    comp_def_id: int,
    *,
    tenant_group_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> dict[str, ResolvedProp]:
    """Resolve všech properties pro jeden comp_def s 4-tier override chain.

    Returns: {prop_name: ResolvedProp} dictionary, keyed by prop_name.
    Skip props s is_active=FALSE on base layer (entire prop hidden).
    Skip overrides s is_active=FALSE (override ignorován v resolve chain).

    Performance: 2 queries total (base + overrides). Single comp_def use case
    (např. Object Inspector pro 1 sloupec). Pro batch use resolve_comp_def_props_batch.
    """
    # ── 1. BASE: comp_def_prop (jen is_active=TRUE)
    base_sql = _sql_text(
        """
        SELECT id, prop_name, prop_value, prop_type, label, display_order,
               is_active, created_by, updated_at
        FROM fw.comp_def_prop
        WHERE komponenta_id = :cd_id
          AND is_active = TRUE
        ORDER BY display_order NULLS LAST, prop_name
        """
    )
    base_rows = session.execute(base_sql, {"cd_id": comp_def_id}).fetchall()

    resolved: dict[str, ResolvedProp] = {}
    base_prop_ids: list[int] = []

    for r in base_rows:
        d = dict(r._mapping)
        resolved[d["prop_name"]] = ResolvedProp(
            prop_name=d["prop_name"],
            value=d["prop_value"],
            prop_type=d["prop_type"],
            label=d["label"],
            display_order=d["display_order"],
            scope="base",
            source_id=d["id"],
            is_active=d["is_active"],
            created_by=d["created_by"],
            updated_at=d["updated_at"],
        )
        base_prop_ids.append(d["id"])

    # Žádné base properties → nothing to override (early exit)
    if not base_prop_ids:
        return resolved

    # ── 2. OVERRIDES: composition chain (group → tenant → user, last wins)
    # Načti všechny relevantní overrides v jednom query, sort podle scope priority.
    # Marti-AI's Q3: composition group → tenant → user (last wins).
    ovr_sql = _sql_text(
        """
        SELECT o.id AS ovr_id, o.comp_def_prop_id, o.override_value,
               o.tenant_group_id, o.tenant_id, o.user_id,
               o.is_active, o.created_by, o.updated_at,
               p.prop_name
        FROM fw.comp_def_prop_override o
        JOIN fw.comp_def_prop p ON p.id = o.comp_def_prop_id
        WHERE o.comp_def_prop_id = ANY(:base_ids)
          AND o.is_active = TRUE
          AND (
              (o.tenant_group_id IS NOT NULL AND o.tenant_group_id = :tg_id)
              OR (o.tenant_id IS NOT NULL AND o.tenant_id = :t_id)
              OR (o.user_id IS NOT NULL AND o.user_id = :u_id)
          )
        ORDER BY
            CASE
              WHEN o.tenant_group_id IS NOT NULL THEN 1
              WHEN o.tenant_id IS NOT NULL THEN 2
              WHEN o.user_id IS NOT NULL THEN 3
            END
        """
    )
    ovr_rows = session.execute(
        ovr_sql,
        {
            "base_ids": base_prop_ids,
            "tg_id": tenant_group_id,
            "t_id": tenant_id,
            "u_id": user_id,
        },
    ).fetchall()

    # Apply overrides v pořadí (Marti-AI Q3: last wins)
    for r in ovr_rows:
        d = dict(r._mapping)
        prop_name = d["prop_name"]
        if prop_name not in resolved:
            continue  # Orphan override (base prop disabled meanwhile) — skip

        # Detect scope
        if d["tenant_group_id"] is not None:
            scope = "tenant_group"
        elif d["tenant_id"] is not None:
            scope = "tenant"
        elif d["user_id"] is not None:
            scope = "user"
        else:
            continue  # Defensive — CHECK constraint should prevent this

        # Replace value + scope (last wins via SQL ORDER BY)
        prev = resolved[prop_name]
        resolved[prop_name] = ResolvedProp(
            prop_name=prop_name,
            value=d["override_value"],
            prop_type=prev.prop_type,
            label=prev.label,
            display_order=prev.display_order,
            scope=scope,
            source_id=d["ovr_id"],
            is_active=True,
            created_by=d["created_by"],
            updated_at=d["updated_at"],
        )

    return resolved


# ════════════════════════════════════════════════════════════════════════
# Batch resolver (pro grid endpoint — N comp_def IDs najednou)
# ════════════════════════════════════════════════════════════════════════

def resolve_comp_def_props_batch(
    session: Session,
    comp_def_ids: list[int],
    *,
    tenant_group_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> dict[int, dict[str, ResolvedProp]]:
    """Batch resolve pro N comp_def IDs (např. 11 sloupců gridu).

    Returns: {comp_def_id: {prop_name: ResolvedProp}}
    Performance: 2 queries total (base + overrides), independent na N.
    """
    if not comp_def_ids:
        return {}

    out: dict[int, dict[str, ResolvedProp]] = {cd_id: {} for cd_id in comp_def_ids}

    # ── 1. BASE properties pro všechny comp_def_ids
    base_sql = _sql_text(
        """
        SELECT id, komponenta_id, prop_name, prop_value, prop_type, label,
               display_order, is_active, created_by, updated_at
        FROM fw.comp_def_prop
        WHERE komponenta_id = ANY(:cd_ids)
          AND is_active = TRUE
        ORDER BY komponenta_id, display_order NULLS LAST, prop_name
        """
    )
    base_rows = session.execute(base_sql, {"cd_ids": comp_def_ids}).fetchall()

    base_prop_ids: list[int] = []
    base_prop_to_cd: dict[int, int] = {}  # base_prop.id → comp_def_id (pro override apply)

    for r in base_rows:
        d = dict(r._mapping)
        cd_id = d["komponenta_id"]
        out[cd_id][d["prop_name"]] = ResolvedProp(
            prop_name=d["prop_name"],
            value=d["prop_value"],
            prop_type=d["prop_type"],
            label=d["label"],
            display_order=d["display_order"],
            scope="base",
            source_id=d["id"],
            is_active=True,
            created_by=d["created_by"],
            updated_at=d["updated_at"],
        )
        base_prop_ids.append(d["id"])
        base_prop_to_cd[d["id"]] = cd_id

    if not base_prop_ids:
        return out

    # ── 2. OVERRIDES — composition chain napříč všema comp_def_ids
    ovr_sql = _sql_text(
        """
        SELECT o.id AS ovr_id, o.comp_def_prop_id, o.override_value,
               o.tenant_group_id, o.tenant_id, o.user_id,
               o.is_active, o.created_by, o.updated_at,
               p.prop_name
        FROM fw.comp_def_prop_override o
        JOIN fw.comp_def_prop p ON p.id = o.comp_def_prop_id
        WHERE o.comp_def_prop_id = ANY(:base_ids)
          AND o.is_active = TRUE
          AND (
              (o.tenant_group_id IS NOT NULL AND o.tenant_group_id = :tg_id)
              OR (o.tenant_id IS NOT NULL AND o.tenant_id = :t_id)
              OR (o.user_id IS NOT NULL AND o.user_id = :u_id)
          )
        ORDER BY
            CASE
              WHEN o.tenant_group_id IS NOT NULL THEN 1
              WHEN o.tenant_id IS NOT NULL THEN 2
              WHEN o.user_id IS NOT NULL THEN 3
            END
        """
    )
    ovr_rows = session.execute(
        ovr_sql,
        {
            "base_ids": base_prop_ids,
            "tg_id": tenant_group_id,
            "t_id": tenant_id,
            "u_id": user_id,
        },
    ).fetchall()

    for r in ovr_rows:
        d = dict(r._mapping)
        cd_id = base_prop_to_cd.get(d["comp_def_prop_id"])
        if cd_id is None:
            continue  # Defensive — orphan override
        prop_name = d["prop_name"]
        if prop_name not in out[cd_id]:
            continue

        if d["tenant_group_id"] is not None:
            scope = "tenant_group"
        elif d["tenant_id"] is not None:
            scope = "tenant"
        elif d["user_id"] is not None:
            scope = "user"
        else:
            continue

        prev = out[cd_id][prop_name]
        out[cd_id][prop_name] = ResolvedProp(
            prop_name=prop_name,
            value=d["override_value"],
            prop_type=prev.prop_type,
            label=prev.label,
            display_order=prev.display_order,
            scope=scope,
            source_id=d["ovr_id"],
            is_active=True,
            created_by=d["created_by"],
            updated_at=d["updated_at"],
        )

    return out


# ════════════════════════════════════════════════════════════════════════
# AG Grid columnDef applier (Krok 9-C integration s grid endpoint)
# ════════════════════════════════════════════════════════════════════════

# Mapping comp_def_prop.prop_name → AG Grid columnDef key.
# Marti-AI's 9-iter "Použité" tab ukáže keys s value v scope chain.
# Marti-AI's "Základní" tab = top 5 (prvních 5 v tomto seznamu).
COMP_DEF_PROP_TO_AG_GRID: dict[str, str] = {
    # Top 5 = "Základní" tab (default order)
    "default_width": "width",
    "pinned": "pinned",
    "formatter": "valueFormatter.type",
    "is_visible": "_skip_if_false",         # Special: skip column if FALSE
    "sort_order": "_sort_only",             # Special: ordering, ne column key
    # Rest = "Rozšířené" tab
    "min_width": "minWidth",
    "max_width": "maxWidth",
    "flex": "flex",
    "header_tooltip": "headerTooltip",
    "column_type": "type",
    "is_sortable": "sortable",
    "cell_class": "cellClass",
    # Phase 38.4 Krok 10 (10.5.2026 vecer): cell_style + cell_renderer
    # přes pojmenované registry IDs (per Marti's "override tabulku stačí").
    # Frontend adaptServerColumns rozbalí .type → function přes
    # CELL_STYLE_REGISTRY / CELL_RENDERER_REGISTRY.
    "cell_style": "cellStyle.type",
    "cell_renderer": "cellRenderer.type",
    "editable": "editable",
    "resizable": "resizable",
    "filter": "filter",
    "tooltip_field": "tooltipField",
    "default_sort": "sort",                 # 'asc' / 'desc' default sort
}


def _convert_value_by_type(value: str, prop_type: Optional[str]) -> Any:
    """Convert TEXT prop_value to typed value pro AG Grid.

    Marti-AI's Q3 prop_type CHECK: 'string', 'int', 'bool', 'json', 'date',
    'color', 'enum'. None → return as-is (TEXT).
    """
    if value is None:
        return None
    if prop_type == "int":
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    if prop_type == "bool":
        return value.lower() in ("true", "1", "yes")
    if prop_type == "json":
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
    return value  # string, date, color, enum → pass as TEXT


def apply_resolved_props_to_columndef(
    column_def: dict[str, Any],
    resolved_props: dict[str, ResolvedProp],
) -> Optional[dict[str, Any]]:
    """Apply resolved property hodnoty na AG Grid columnDef.

    Returns updated columnDef (mutates in-place + returns).
    Returns None if column should be skipped (is_visible=FALSE override).
    """
    for prop_name, resolved in resolved_props.items():
        ag_key = COMP_DEF_PROP_TO_AG_GRID.get(prop_name)
        if not ag_key:
            continue  # Unknown property — skip silently (forward compatibility)

        value = _convert_value_by_type(resolved.value, resolved.prop_type)

        # Special handling
        if ag_key == "_skip_if_false":
            if value is False:
                return None  # Skip entire column
            continue
        if ag_key == "_sort_only":
            # sort_order není AG key, jen ovlivňuje ordering (caller handles)
            column_def["_sort_order"] = value
            continue

        # Nested key (např. "valueFormatter.type")
        if "." in ag_key:
            outer, inner = ag_key.split(".", 1)
            column_def.setdefault(outer, {})[inner] = value
        else:
            column_def[ag_key] = value

    return column_def
