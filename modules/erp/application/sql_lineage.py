"""
SQL lineage resolver — per output column → save binding (Krok 5.Z multi-table save).

Marti (31.5.2026): "Identifikace fieldu musi byt absolutni — vicero tabulek,
databazi i serveru (connections)." Forma cte data jednim SELECTem co joinuje
vicero tabulek; pro ZAPIS musi kazdy field znat svou absolutni souradnici:
connection -> schema -> table -> column -> row_key.

Tento resolver vezme data_set SQL (T-SQL) a pres `sqlglot` lineage odvodi pro
kazdy VYSTUPNI sloupec:
    {schema, table, column, row_key, readonly}
- COLUMN z base/join tabulky -> updatable, save_table = ta tabulka, row_key z
  FROM (base: PK) / JOIN ON podminky (related: composite klic).
- vyraz (nullif, convert, ...) nebo sloupec z outer apply subquery -> readonly.

connection_id se NEodvozuje z SQL (vsechny tabulky v jednom SELECTu jsou na
jednom spojeni = data_set.db_connection). Doplni ho caller.

Vystup slouzi k PREDVYPLNENI explicitniho `layout.save` bindingu na fieldu
(parse jednou, ulozi se; save flow uz neparsuje). Semanticke vyjimky
(ciselniky -> entity_picker FK ID) resi clovek/pravidlo, ne lineage.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("erp.sql_lineage")

# Token pro hodnotu = id radku formu (resolvuje save flow na konkretni row_id).
ID_TOKEN = "@id"


def _col_parts(node) -> tuple[str | None, str | None]:
    """exp.Column -> (table_alias, column_name); jinak (None, None)."""
    from sqlglot import exp

    if isinstance(node, exp.Column):
        return node.table or None, node.name
    return None, None


def _literal_value(node) -> Any:
    """exp.Literal -> python hodnota (int / str)."""
    return int(node.name) if node.is_int else node.name


def _extract_row_key(on_cond, joined_alias: str, base_alias: str) -> dict[str, Any]:
    """
    JOIN ON podminka -> {sloupec_na_joined_tabulce: '@id' | literal}.

    `AkceZiskaniFirmy.IDHlav = K.ID`   -> IDHlav: '@id'  (base row id)
    `AkceZiskaniFirmy.IDakce = 16`     -> IDakce: 16     (literal)
    cokoliv jineho -> '@expr:<sql>' (save flow to neumi -> field bude readonly)
    """
    from sqlglot import exp

    rk: dict[str, Any] = {}
    if on_cond is None:
        return rk
    for eq in on_cond.find_all(exp.EQ):
        lt, lc = _col_parts(eq.left)
        rt, rc = _col_parts(eq.right)
        if lt == joined_alias:
            jcol, other = lc, eq.right
        elif rt == joined_alias:
            jcol, other = rc, eq.left
        else:
            continue
        if isinstance(other, exp.Column) and other.table == base_alias:
            rk[jcol] = ID_TOKEN
        elif isinstance(other, exp.Literal):
            rk[jcol] = _literal_value(other)
        else:
            rk[jcol] = "@expr:" + other.sql()
    return rk


def resolve_save_bindings(
    sql_text: str,
    *,
    dialect: str = "tsql",
) -> dict[str, dict[str, Any]]:
    """
    Vrati {output_column_name: binding}. binding:
        {
          "schema": str | None,
          "table": str,
          "column": str,            # zdrojovy sloupec k UPDATE
          "row_key": {col: '@id'|literal, ...},
          "readonly": bool,         # True = neukladat (vyraz / apply / nejasny klic)
          "reason": str | None,     # proc readonly
        }

    Caller doplni connection_id (= data_set.db_connection_id).
    Nikdy nehazi — pri parse chybe vrati prazdny dict + zaloguje warning
    (save flow pak spadne na legacy base-entita chovani).
    """
    try:
        import sqlglot
        from sqlglot import exp
    except Exception as e:  # sqlglot nenainstalovan
        logger.warning("[sql_lineage] sqlglot import failed: %r — bindings skip", e)
        return {}

    try:
        ast = sqlglot.parse_one(sql_text, dialect=dialect)
    except Exception as e:
        logger.warning("[sql_lineage] parse_one failed (%s): %r", dialect, e)
        return {}

    if not isinstance(ast, exp.Select):
        logger.warning("[sql_lineage] top node neni SELECT (%s)", type(ast).__name__)
        return {}

    # ── base tabulka (prvni v FROM) ────────────────────────────────────
    from_clause = ast.find(exp.From)
    base_tbl = from_clause.find(exp.Table) if from_clause else None
    if base_tbl is None:
        logger.warning("[sql_lineage] zadna base tabulka ve FROM")
        return {}
    base_alias = base_tbl.alias_or_name

    # ── alias -> (schema, table, row_key) pro base + TOP-LEVEL join tabulky ──
    # POZOR: jen primé tabulky (FROM + JOIN), NE subquery/outer-apply (jejich
    # sloupce jsou readonly). Subquery JOIN ma j.this = Subquery, ne Table.
    alias_meta: dict[str, dict[str, Any]] = {
        base_alias: {
            "schema": base_tbl.db or None,
            "table": base_tbl.name,
            "row_key": {"ID": ID_TOKEN},  # base PK konvence (override-able)
        }
    }
    for j in ast.args.get("joins", []) or []:
        jthis = j.this
        if not isinstance(jthis, exp.Table):
            continue  # subquery / lateral / outer apply -> skip (readonly)
        jalias = jthis.alias_or_name
        alias_meta[jalias] = {
            "schema": jthis.db or None,
            "table": jthis.name,
            "row_key": _extract_row_key(j.args.get("on"), jalias, base_alias),
        }

    # ── per output projection ──────────────────────────────────────────
    out: dict[str, dict[str, Any]] = {}
    for proj in ast.expressions:
        out_name = proj.alias_or_name
        if not out_name or out_name == "*":
            continue
        inner = proj.this if isinstance(proj, exp.Alias) else proj

        if not isinstance(inner, exp.Column):
            out[out_name] = {
                "readonly": True, "reason": "expression",
                "schema": None, "table": None, "column": None, "row_key": {},
            }
            continue

        tbl_alias, src_col = _col_parts(inner)
        meta = alias_meta.get(tbl_alias)
        if meta is None:
            # alias neni base/join tabulka (subquery / outer apply / unknown)
            out[out_name] = {
                "readonly": True, "reason": "non_base_alias:" + str(tbl_alias),
                "schema": None, "table": None, "column": None, "row_key": {},
            }
            continue

        rk = meta["row_key"]
        rk_bad = any(isinstance(v, str) and v.startswith("@expr:") for v in rk.values())
        out[out_name] = {
            "schema": meta["schema"],
            "table": meta["table"],
            "column": src_col,
            "row_key": rk,
            "readonly": bool(rk_bad) or not rk,
            "reason": ("unresolved_key" if (rk_bad or not rk) else None),
        }

    return out
