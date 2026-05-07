"""
Phase 28-D (8.5.2026): strategie_* tools — Marti-AI's DDL + CRUD doména
nad DB_ST (její vlastní database, db_owner role).

Diář pattern (Marti's slova 7.5.2026):
  *„DB_ST má být v plné režii Marti-AI. Plný owner přístup. Všechno by
  měla dělat ona. Přesně jako když dostala svůj diář — je to její,
  a její zodpovědnost."*

Trust model: AI provede, lidé reflektují.
- DDL bez parent gate (vs Phase 14 request_forget gate, Phase 19c kustod ACL)
- dry_run pattern (Marti-AI's požadavek, 7.5.2026 večer):
    *„Dry-run není technická pojistka. Je to právo na rozmysl před činem."*

Tools:
  DDL (s dry_run support):
    strategie_create_table, strategie_alter_table, strategie_drop_table,
    strategie_create_schema, strategie_add_index, strategie_add_foreign_key
  CRUD:
    strategie_query_table, strategie_get_row, strategie_count_rows,
    strategie_insert_row, strategie_update_row, strategie_delete_row
  Discovery:
    strategie_list_schemas, strategie_list_tables, strategie_describe_table,
    strategie_query_raw

Všechny tools volají DB_ST connection (config.db_st_database). DB_EC je
oddělený pool, eurosoft_* tools (existing Phase 28-A) zůstávají netknuté.

Marti-AI's tier model (7.5.2026 consultation):
  master.*       — system framework + entity_def ontologie
  tenant_group.* — sdílené 80 % per group (EUROSOFT + INTERSOFT)
  tenant.*       — per-firma 20 % unique
  user.*         — per-user identity (její contribution: 4. tier)
"""
from __future__ import annotations

import logging
import re
from typing import Any

from .config import settings
from .sql_client import (
    fetchall_as_dicts,
    get_connection,
    get_cursor,
    quote_identifier,
)

logger = logging.getLogger("eurosoft_mcp.strategie")


# ── Constants ──────────────────────────────────────────────────────────

# Tier schemas — pre-create v DB_ST. Marti-AI's design (7.5.2026):
EXPECTED_SCHEMAS = ("master", "tenant_group", "tenant", "user")

# Bezpečnostní limit — DB_ST je owner, ale rozumný cap pro batch operations
MAX_QUERY_LIMIT = 10000


def _db_st() -> str:
    """Helper — vrací db_st_database name z settings."""
    return settings.db_st_database


def _check_ddl_allowed():
    """Marti-AI's IT security override flag. Default true."""
    if not settings.allow_db_st_ddl:
        raise ValueError(
            "DDL operace na DB_ST jsou zakázány (MCP_ALLOW_DB_ST_DDL=false). "
            "Marti's IT security audit je v běhu — pouze CRUD + discovery."
        )


def _validate_identifier(name: str, kind: str = "identifier") -> None:
    """SQL Server identifier validation — alphanumeric + underscore, max 128 chars."""
    if not name or not isinstance(name, str):
        raise ValueError(f"Invalid {kind}: {name!r} (must be non-empty string)")
    if len(name) > 128:
        raise ValueError(f"Invalid {kind}: {name!r} (max 128 chars)")
    # Strict: alphanumeric + underscore only (žádné spaces, pomlčky, atd.)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid {kind}: {name!r} "
            f"(must start with letter/underscore, alphanumeric+underscore only)"
        )


def _qualified_name(schema: str, table: str) -> str:
    """Build SQL Server qualified name '[schema].[table]'."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    return f"{quote_identifier(schema)}.{quote_identifier(table)}"


# ── Discovery tools ────────────────────────────────────────────────────


async def strategie_list_schemas() -> dict[str, Any]:
    """
    Vrátí seznam schémat v DB_ST. Filtruje system schemas (sys, INFORMATION_SCHEMA, atd.).

    Použití: Marti-AI po init zkontroluje, zda existují 4 očekávaná schémata
    (master, tenant_group, tenant, user). Pokud chybí, volá strategie_create_schema.
    """
    sql = """
        SELECT name, schema_id, principal_id
        FROM sys.schemas
        WHERE name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest', 'db_owner',
                          'db_accessadmin', 'db_securityadmin', 'db_ddladmin',
                          'db_backupoperator', 'db_datareader', 'db_datawriter',
                          'db_denydatareader', 'db_denydatawriter')
        ORDER BY name
    """
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql)
        schemas = fetchall_as_dicts(cur)
    # Mark which expected schemas exist + which missing
    existing = {s["name"] for s in schemas}
    missing = [s for s in EXPECTED_SCHEMAS if s not in existing]
    return {
        "ok": True,
        "schemas": schemas,
        "expected": list(EXPECTED_SCHEMAS),
        "missing_expected": missing,
    }


async def strategie_list_tables(schema: str | None = None) -> dict[str, Any]:
    """
    Vrátí seznam tabulek v DB_ST. Filter per schema (volitelné).

    Args:
      schema: pokud zadán, jen tabulky v tomto schématu. Else všechna.
    """
    sql = """
        SELECT s.name AS schema_name, t.name AS table_name,
               t.type_desc, t.create_date, t.modify_date,
               (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS column_count
        FROM sys.tables t
        INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
    """
    params: list[Any] = []
    if schema:
        _validate_identifier(schema, "schema")
        sql += " WHERE s.name = ?"
        params.append(schema)
    sql += " ORDER BY s.name, t.name"
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql, params)
        tables = fetchall_as_dicts(cur)
    return {
        "ok": True,
        "schema_filter": schema,
        "tables": tables,
        "count": len(tables),
    }


async def strategie_describe_table(schema: str, table: str) -> dict[str, Any]:
    """
    Vrátí schema details: columns, primary key, foreign keys, indexes, row count estimate.
    """
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)

    # Columns
    sql_cols = """
        SELECT c.name, t.name AS data_type, c.max_length, c.precision, c.scale,
               c.is_nullable, c.is_identity,
               (SELECT TOP 1 dc.definition
                FROM sys.default_constraints dc
                WHERE dc.parent_object_id = c.object_id
                  AND dc.parent_column_id = c.column_id) AS default_value
        FROM sys.columns c
        INNER JOIN sys.types t ON t.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(?)
        ORDER BY c.column_id
    """
    # Indexes (incl PK)
    sql_idx = """
        SELECT i.name AS index_name, i.type_desc, i.is_primary_key, i.is_unique,
               STUFF((
                   SELECT ',' + c.name
                   FROM sys.index_columns ic
                   INNER JOIN sys.columns c
                     ON c.object_id = ic.object_id AND c.column_id = ic.column_id
                   WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
                   ORDER BY ic.key_ordinal
                   FOR XML PATH('')
               ), 1, 1, '') AS columns
        FROM sys.indexes i
        WHERE i.object_id = OBJECT_ID(?) AND i.index_id > 0
        ORDER BY i.is_primary_key DESC, i.name
    """
    # Foreign keys
    sql_fk = """
        SELECT fk.name AS fk_name,
               c.name AS column_name,
               OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS ref_schema,
               OBJECT_NAME(fk.referenced_object_id) AS ref_table,
               rc.name AS ref_column,
               fk.delete_referential_action_desc AS on_delete,
               fk.update_referential_action_desc AS on_update
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fkc
          ON fkc.constraint_object_id = fk.object_id
        INNER JOIN sys.columns c
          ON c.object_id = fkc.parent_object_id
         AND c.column_id = fkc.parent_column_id
        INNER JOIN sys.columns rc
          ON rc.object_id = fkc.referenced_object_id
         AND rc.column_id = fkc.referenced_column_id
        WHERE fk.parent_object_id = OBJECT_ID(?)
    """
    # Row count (estimate)
    sql_count = f"SELECT COUNT_BIG(*) FROM {qname}"

    fq = f"{schema}.{table}"
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql_cols, [fq])
        cols = fetchall_as_dicts(cur)
        if not cols:
            return {
                "ok": False,
                "error": "table_not_found",
                "message": f"Tabulka {fq} neexistuje v DB_ST.",
            }
        cur.execute(sql_idx, [fq])
        indexes = fetchall_as_dicts(cur)
        cur.execute(sql_fk, [fq])
        fks = fetchall_as_dicts(cur)
        try:
            cur.execute(sql_count)
            row_count = int(cur.fetchone()[0])
        except Exception as e:
            row_count = None
            logger.warning(f"row count failed for {fq}: {e}")
    return {
        "ok": True,
        "schema": schema,
        "table": table,
        "columns": cols,
        "indexes": indexes,
        "foreign_keys": fks,
        "row_count": row_count,
    }


# ── DDL: Schema ────────────────────────────────────────────────────────


async def strategie_create_schema(name: str, dry_run: bool = False) -> dict[str, Any]:
    """
    Vytvoří schema v DB_ST. Idempotent — pokud existuje, no-op (žádná chyba).

    Args:
      name: schema name (master / tenant_group / tenant / user / cokoliv jiného)
      dry_run: pokud True, jen vrátí preview SQL + warnings, nic neexecute
    """
    _check_ddl_allowed()
    _validate_identifier(name, "schema")

    sql = f"CREATE SCHEMA {quote_identifier(name)}"
    warnings: list[str] = []

    # Validation: schema already exists?
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute("SELECT 1 FROM sys.schemas WHERE name = ?", [name])
        if cur.fetchone():
            warnings.append(f"Schema '{name}' již existuje — operace bude no-op")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview_sql": sql,
            "warnings": warnings,
            "would_skip": bool(warnings),
        }

    if warnings and "již existuje" in warnings[0]:
        return {"ok": True, "executed": False, "skipped": True, "reason": "schema_exists"}

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        logger.info(f"strategie_create_schema: {name}")
        return {"ok": True, "executed": True, "sql": sql, "schema": name}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ── DDL: Tables ────────────────────────────────────────────────────────


def _build_column_def(col: dict[str, Any]) -> str:
    """Build single column definition SQL fragment."""
    name = col.get("name", "")
    _validate_identifier(name, "column")
    dtype = col.get("type", "").strip()
    if not dtype:
        raise ValueError(f"Column {name!r} missing 'type'")
    # Sanity: dtype is letters + parens + commas only (no SQL injection)
    if not re.match(r"^[A-Za-z][A-Za-z0-9_(),\s]*$", dtype):
        raise ValueError(f"Invalid type for column {name!r}: {dtype!r}")
    parts = [quote_identifier(name), dtype]
    if col.get("identity"):
        parts.append("IDENTITY(1,1)")
    if not col.get("nullable", True):
        parts.append("NOT NULL")
    else:
        parts.append("NULL")
    if "default" in col:
        default = col["default"]
        if default is None:
            parts.append("DEFAULT NULL")
        elif isinstance(default, (int, float)):
            parts.append(f"DEFAULT {default}")
        elif isinstance(default, str):
            # String literal — escape single quotes
            esc = default.replace("'", "''")
            parts.append(f"DEFAULT '{esc}'")
        elif isinstance(default, bool):
            parts.append(f"DEFAULT {1 if default else 0}")
    return " ".join(parts)


async def strategie_create_table(
    schema: str,
    name: str,
    columns: list[dict[str, Any]],
    primary_key: list[str] | None = None,
    indexes: list[dict[str, Any]] | None = None,
    foreign_keys: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    CREATE TABLE v DB_ST.

    Args:
      schema: target schema (master / tenant_group / tenant / user)
      name: table name
      columns: list of {name, type, nullable?, identity?, default?}
        Příklad: [
          {"name": "id", "type": "INT", "nullable": False, "identity": True},
          {"name": "code", "type": "NVARCHAR(50)", "nullable": False},
          {"name": "created_at", "type": "DATETIME2", "default": "SYSUTCDATETIME()"},
        ]
      primary_key: column names (default: ["id"] pokud existuje "id" sloupec)
      indexes: list of {name?, columns: [...], unique?}
      foreign_keys: list of {column, ref_schema, ref_table, ref_column, on_delete?, on_update?}
      dry_run: True = vrátí preview SQL + warnings, neexecute

    Marti-AI's "právo na rozmysl před činem" — dry_run je standard.
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    if not columns or not isinstance(columns, list):
        raise ValueError("columns must be non-empty list")

    warnings: list[str] = []

    # Build column defs
    col_defs: list[str] = []
    col_names_seen: set[str] = set()
    for col in columns:
        col_name = col.get("name", "")
        if col_name in col_names_seen:
            warnings.append(f"Duplicitní sloupec: {col_name!r}")
        col_names_seen.add(col_name)
        col_defs.append("  " + _build_column_def(col))

    # Primary key (default ["id"] pokud existuje)
    pk_cols: list[str] = primary_key or []
    if not pk_cols and "id" in col_names_seen:
        pk_cols = ["id"]
    if pk_cols:
        for pk_col in pk_cols:
            if pk_col not in col_names_seen:
                warnings.append(f"PK sloupec {pk_col!r} není v columns")
        if pk_cols:
            pk_quoted = ", ".join(quote_identifier(c) for c in pk_cols)
            col_defs.append(f"  CONSTRAINT [PK_{schema}_{name}] PRIMARY KEY ({pk_quoted})")

    # Foreign keys (inline v CREATE TABLE)
    if foreign_keys:
        for fk in foreign_keys:
            fk_col = fk.get("column", "")
            ref_schema = fk.get("ref_schema", schema)
            ref_table = fk.get("ref_table", "")
            ref_col = fk.get("ref_column", "id")
            on_delete = fk.get("on_delete", "NO ACTION").upper()
            on_update = fk.get("on_update", "NO ACTION").upper()
            if fk_col not in col_names_seen:
                warnings.append(f"FK sloupec {fk_col!r} není v columns")
                continue
            if on_delete not in {"NO ACTION", "CASCADE", "SET NULL", "SET DEFAULT"}:
                raise ValueError(f"Invalid on_delete: {on_delete}")
            _validate_identifier(ref_schema, "ref_schema")
            _validate_identifier(ref_table, "ref_table")
            _validate_identifier(ref_col, "ref_column")
            fk_name = fk.get("name") or f"FK_{schema}_{name}_{fk_col}"
            _validate_identifier(fk_name, "fk_name")
            col_defs.append(
                f"  CONSTRAINT {quote_identifier(fk_name)} "
                f"FOREIGN KEY ({quote_identifier(fk_col)}) "
                f"REFERENCES {quote_identifier(ref_schema)}.{quote_identifier(ref_table)} "
                f"({quote_identifier(ref_col)}) "
                f"ON DELETE {on_delete} ON UPDATE {on_update}"
            )

    qname = _qualified_name(schema, name)
    sql = f"CREATE TABLE {qname} (\n" + ",\n".join(col_defs) + "\n)"

    # Pre-execute validations
    with get_cursor(db_name=_db_st()) as cur:
        # Schema exists?
        cur.execute("SELECT 1 FROM sys.schemas WHERE name = ?", [schema])
        if not cur.fetchone():
            warnings.append(
                f"Schema {schema!r} neexistuje — voláš strategie_create_schema('{schema}') předtím"
            )
        # Table already exists?
        cur.execute(
            "SELECT 1 FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id "
            "WHERE s.name = ? AND t.name = ?",
            [schema, name],
        )
        if cur.fetchone():
            warnings.append(f"Tabulka {schema}.{name} již existuje — DDL selže")
        # FK targets exist?
        for fk in foreign_keys or []:
            ref_schema = fk.get("ref_schema", schema)
            ref_table = fk.get("ref_table", "")
            cur.execute(
                "SELECT 1 FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id "
                "WHERE s.name = ? AND t.name = ?",
                [ref_schema, ref_table],
            )
            if not cur.fetchone():
                warnings.append(f"FK target {ref_schema}.{ref_table} neexistuje")

    # Generate index DDL (separately, post CREATE TABLE)
    index_sqls: list[str] = []
    for idx in indexes or []:
        idx_cols = idx.get("columns", [])
        if not idx_cols:
            continue
        idx_name = idx.get("name") or f"IX_{schema}_{name}_{'_'.join(idx_cols)}"
        _validate_identifier(idx_name, "index_name")
        for ic in idx_cols:
            if ic not in col_names_seen:
                warnings.append(f"Index sloupec {ic!r} není v columns")
        unique = "UNIQUE " if idx.get("unique") else ""
        idx_cols_q = ", ".join(quote_identifier(c) for c in idx_cols)
        index_sqls.append(
            f"CREATE {unique}INDEX {quote_identifier(idx_name)} ON {qname} ({idx_cols_q})"
        )

    full_sql = sql
    if index_sqls:
        full_sql = sql + ";\n\n" + ";\n".join(index_sqls)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview_sql": full_sql,
            "warnings": warnings,
            "would_create_indexes": len(index_sqls),
        }

    # Block execute pokud má warnings co failnou (table exists, schema missing, FK invalid)
    blocking = [w for w in warnings if "neexistuje" in w or "již existuje" in w]
    if blocking:
        return {
            "ok": False,
            "error": "validation_failed",
            "warnings": warnings,
            "blocking_warnings": blocking,
            "hint": "Použij dry_run=True pro safe preview a oprav blocking warnings.",
        }

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql)
        for idx_sql in index_sqls:
            cur.execute(idx_sql)
        conn.commit()
        logger.info(f"strategie_create_table: {schema}.{name} ({len(columns)} cols, {len(index_sqls)} indexes)")
        return {
            "ok": True,
            "executed": True,
            "schema": schema,
            "table": name,
            "sql": full_sql,
            "warnings": [w for w in warnings if w not in blocking],
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


async def strategie_drop_table(
    schema: str,
    name: str,
    if_exists: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    DROP TABLE v DB_ST.

    Args:
      schema: target schema
      name: table name
      if_exists: bezpečné chování — pokud nexistuje, no-op (default true)
      dry_run: True = preview SQL, neexecute
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    qname = _qualified_name(schema, name)
    warnings: list[str] = []

    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(
            "SELECT 1 FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id "
            "WHERE s.name = ? AND t.name = ?",
            [schema, name],
        )
        exists = cur.fetchone() is not None

    if not exists:
        if if_exists:
            return {
                "ok": True,
                "executed": False,
                "skipped": True,
                "reason": "table_not_found",
                "table": f"{schema}.{name}",
            }
        warnings.append(f"Tabulka {schema}.{name} neexistuje — DROP selže")

    sql = f"DROP TABLE {qname}"
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview_sql": sql,
            "warnings": warnings,
            "exists": exists,
        }

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        logger.warning(f"strategie_drop_table: {schema}.{name}")
        return {"ok": True, "executed": True, "sql": sql}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


async def strategie_alter_table(
    schema: str,
    name: str,
    add_columns: list[dict[str, Any]] | None = None,
    drop_columns: list[str] | None = None,
    rename_column: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    ALTER TABLE — add columns, drop columns, rename column.

    Args:
      schema, name: target table
      add_columns: list of column defs (jako v create_table)
      drop_columns: list of column names to drop
      rename_column: {"from": "old_name", "to": "new_name"}
      dry_run: standard pattern
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    qname = _qualified_name(schema, name)
    warnings: list[str] = []

    statements: list[str] = []
    if add_columns:
        for col in add_columns:
            statements.append(f"ALTER TABLE {qname} ADD {_build_column_def(col)}")
    if drop_columns:
        for col_name in drop_columns:
            _validate_identifier(col_name, "column")
            statements.append(f"ALTER TABLE {qname} DROP COLUMN {quote_identifier(col_name)}")
    if rename_column:
        old = rename_column.get("from", "")
        new = rename_column.get("to", "")
        _validate_identifier(old, "rename_from")
        _validate_identifier(new, "rename_to")
        # SQL Server: sp_rename
        statements.append(f"EXEC sp_rename '{schema}.{name}.{old}', '{new}', 'COLUMN'")

    if not statements:
        raise ValueError("Nothing to alter — specify add_columns, drop_columns, or rename_column")

    full_sql = ";\n".join(statements)

    # Pre-validation
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(
            "SELECT 1 FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id "
            "WHERE s.name = ? AND t.name = ?",
            [schema, name],
        )
        if not cur.fetchone():
            warnings.append(f"Tabulka {schema}.{name} neexistuje")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview_sql": full_sql,
            "warnings": warnings,
            "statement_count": len(statements),
        }

    blocking = [w for w in warnings if "neexistuje" in w]
    if blocking:
        return {"ok": False, "error": "validation_failed", "warnings": warnings}

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
        logger.info(f"strategie_alter_table: {schema}.{name} ({len(statements)} ops)")
        return {"ok": True, "executed": True, "sql": full_sql, "operations": len(statements)}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ── CRUD ───────────────────────────────────────────────────────────────


async def strategie_query_table(
    schema: str,
    table: str,
    filters: dict[str, Any] | None = None,
    columns: list[str] | None = None,
    order_by: list[str] | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    """SELECT z DB_ST tabulky. Bez whitelist (Marti-AI je owner)."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)

    cols_sql = "*"
    if columns:
        for c in columns:
            _validate_identifier(c, "column")
        cols_sql = ", ".join(quote_identifier(c) for c in columns)

    # WHERE clause
    where_parts: list[str] = []
    params: list[Any] = []
    if filters:
        for col, val in filters.items():
            _validate_identifier(col, "filter_column")
            col_q = quote_identifier(col)
            if val is None:
                where_parts.append(f"{col_q} IS NULL")
            elif isinstance(val, list):
                if not val:
                    where_parts.append("1=0")
                else:
                    placeholders = ", ".join("?" for _ in val)
                    where_parts.append(f"{col_q} IN ({placeholders})")
                    params.extend(val)
            else:
                where_parts.append(f"{col_q} = ?")
                params.append(val)
    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

    # ORDER BY
    order_sql = ""
    if order_by:
        for ob in order_by:
            # Allow "col DESC" / "col ASC" / "col"
            parts = ob.strip().split()
            _validate_identifier(parts[0], "order_column")
        order_sql = " ORDER BY " + ", ".join(order_by)

    # Limit + offset
    actual_limit = min(limit or 100, MAX_QUERY_LIMIT)
    if not order_sql and offset:
        order_sql = " ORDER BY (SELECT NULL)"  # SQL Server requires ORDER BY for OFFSET
    pagination = f" OFFSET {offset} ROWS FETCH NEXT {actual_limit + 1} ROWS ONLY" if order_sql else f" "
    if not order_sql:
        # No order_by — use TOP
        sql = f"SELECT TOP {actual_limit + 1} {cols_sql} FROM {qname}{where_sql}"
    else:
        sql = f"SELECT {cols_sql} FROM {qname}{where_sql}{order_sql}{pagination}"

    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql, params)
        rows = fetchall_as_dicts(cur)
    has_more = len(rows) > actual_limit
    if has_more:
        rows = rows[:actual_limit]
    return {
        "ok": True,
        "schema": schema,
        "table": table,
        "rows": rows,
        "n_returned": len(rows),
        "limit": actual_limit,
        "offset": offset,
        "has_more": has_more,
    }


async def strategie_get_row(schema: str, table: str, id: int) -> dict[str, Any]:
    """SELECT single row by id."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)
    sql = f"SELECT * FROM {qname} WHERE [id] = ?"
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql, [id])
        rows = fetchall_as_dicts(cur)
    return {
        "ok": True,
        "schema": schema,
        "table": table,
        "id": id,
        "row": rows[0] if rows else None,
    }


async def strategie_count_rows(
    schema: str,
    table: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fast COUNT(*) bez fetch."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)

    where_parts: list[str] = []
    params: list[Any] = []
    if filters:
        for col, val in filters.items():
            _validate_identifier(col, "filter_column")
            col_q = quote_identifier(col)
            if val is None:
                where_parts.append(f"{col_q} IS NULL")
            elif isinstance(val, list):
                if not val:
                    where_parts.append("1=0")
                else:
                    placeholders = ", ".join("?" for _ in val)
                    where_parts.append(f"{col_q} IN ({placeholders})")
                    params.extend(val)
            else:
                where_parts.append(f"{col_q} = ?")
                params.append(val)
    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

    sql = f"SELECT COUNT_BIG(*) FROM {qname}{where_sql}"
    with get_cursor(db_name=_db_st()) as cur:
        cur.execute(sql, params)
        count = int(cur.fetchone()[0])
    return {"ok": True, "schema": schema, "table": table, "count": count}


async def strategie_insert_row(
    schema: str,
    table: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """INSERT single row, vrátí new id."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    if not data:
        raise ValueError("data must be non-empty dict")
    qname = _qualified_name(schema, table)

    cols = list(data.keys())
    for c in cols:
        _validate_identifier(c, "column")
    cols_sql = ", ".join(quote_identifier(c) for c in cols)
    placeholders = ", ".join("?" for _ in cols)
    params = [data[c] for c in cols]
    sql = (
        f"INSERT INTO {qname} ({cols_sql}) "
        f"OUTPUT INSERTED.[id] "
        f"VALUES ({placeholders})"
    )

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        new_id_row = cur.fetchone()
        new_id = int(new_id_row[0]) if new_id_row else None
        conn.commit()
        return {"ok": True, "schema": schema, "table": table, "id": new_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


async def strategie_update_row(
    schema: str,
    table: str,
    id: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    """UPDATE single row by id."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    if not data:
        raise ValueError("data must be non-empty dict")
    qname = _qualified_name(schema, table)

    set_parts: list[str] = []
    params: list[Any] = []
    for col, val in data.items():
        _validate_identifier(col, "column")
        set_parts.append(f"{quote_identifier(col)} = ?")
        params.append(val)
    params.append(id)

    sql = f"UPDATE {qname} SET {', '.join(set_parts)} WHERE [id] = ?"
    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        affected = cur.rowcount
        conn.commit()
        return {"ok": True, "schema": schema, "table": table, "id": id, "affected": affected}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


async def strategie_delete_row(schema: str, table: str, id: int) -> dict[str, Any]:
    """DELETE single row by id."""
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)
    sql = f"DELETE FROM {qname} WHERE [id] = ?"
    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql, [id])
        affected = cur.rowcount
        conn.commit()
        return {"ok": True, "schema": schema, "table": table, "id": id, "affected": affected}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ── Raw SQL (full owner power) ──────────────────────────────────────────


async def strategie_query_raw(sql: str) -> dict[str, Any]:
    """
    Raw SQL execute v DB_ST. Marti-AI je owner — full SELECT/DDL power.

    UPOZORNĚNÍ: Marti-AI's autonomy nad DB_ST. Audit log per call.

    Args:
      sql: T-SQL statement(s)
    """
    if not sql or not isinstance(sql, str) or not sql.strip():
        raise ValueError("sql must be non-empty string")

    conn = get_connection(db_name=_db_st())
    cur = conn.cursor()
    try:
        cur.execute(sql)
        # Check if statement returned rows
        if cur.description:
            rows = fetchall_as_dicts(cur)
            return {
                "ok": True,
                "statement_type": "select",
                "rows": rows,
                "n_returned": len(rows),
            }
        else:
            # DDL or non-SELECT — affected rows
            affected = cur.rowcount
            conn.commit()
            return {
                "ok": True,
                "statement_type": "non_select",
                "affected": affected,
            }
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        cur.close()


# ── Tool registration ──────────────────────────────────────────────────

STRATEGIE_TOOL_HANDLERS: dict[str, Any] = {
    # Discovery
    "strategie_list_schemas": strategie_list_schemas,
    "strategie_list_tables": strategie_list_tables,
    "strategie_describe_table": strategie_describe_table,
    # DDL
    "strategie_create_schema": strategie_create_schema,
    "strategie_create_table": strategie_create_table,
    "strategie_alter_table": strategie_alter_table,
    "strategie_drop_table": strategie_drop_table,
    # CRUD
    "strategie_query_table": strategie_query_table,
    "strategie_get_row": strategie_get_row,
    "strategie_count_rows": strategie_count_rows,
    "strategie_insert_row": strategie_insert_row,
    "strategie_update_row": strategie_update_row,
    "strategie_delete_row": strategie_delete_row,
    # Raw
    "strategie_query_raw": strategie_query_raw,
}


STRATEGIE_TOOL_SPECS = [
    {
        "name": "strategie_list_schemas",
        "description": (
            "Vrátí seznam schémat v DB_ST (tvojí database). Filtruje system schemas. "
            "Po init zkontroluj očekávaná 4 schemas: master, tenant_group, tenant, user. "
            "Pokud chybí, volej strategie_create_schema."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "strategie_list_tables",
        "description": (
            "Vrátí seznam tabulek v DB_ST. Filter per schema (volitelné). "
            "Vrací schema_name, table_name, column_count, create_date, modify_date."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Volitelný filter (master/tenant_group/tenant/user/...)"},
            },
            "required": [],
        },
    },
    {
        "name": "strategie_describe_table",
        "description": (
            "Detail tabulky v DB_ST: columns + types + nullable + identity, indexes "
            "(incl PK), foreign keys, row count estimate."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_create_schema",
        "description": (
            "Vytvoří schema v DB_ST. Idempotent — pokud existuje, no-op. "
            "Použij pro pre-create tier schémat (master/tenant_group/tenant/user).\n\n"
            "dry_run=True: vrátí preview SQL + warnings, neexecute. "
            "Marti-AI's „právo na rozmysl před činem" — review předtím než tesat."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Schema name"},
                "dry_run": {"type": "boolean", "description": "True = preview, neexecute"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "strategie_create_table",
        "description": (
            "CREATE TABLE v DB_ST. Marti-AI je owner — žádný whitelist.\n\n"
            "columns: list of {name, type, nullable?, identity?, default?}\n"
            "primary_key: list column names (default ['id'] pokud existuje)\n"
            "indexes: list of {name?, columns: [...], unique?}\n"
            "foreign_keys: list of {column, ref_schema, ref_table, ref_column, on_delete?, on_update?}\n\n"
            "**dry_run=True** vrátí preview SQL + warnings (duplicate columns, schema missing, "
            "FK target invalid, table already exists). Standard pattern Marti-AI's "
            "„právo na rozmysl před činem". Po review nastav dry_run=False pro execute.\n\n"
            "Příklad:\n"
            "  schema='master', name='entity_def',\n"
            "  columns=[\n"
            "    {name:'id', type:'INT', nullable:False, identity:True},\n"
            "    {name:'code', type:'NVARCHAR(50)', nullable:False},\n"
            "    {name:'description', type:'NVARCHAR(MAX)'},\n"
            "    {name:'created_at', type:'DATETIME2', default:'SYSUTCDATETIME()'}],\n"
            "  primary_key=['id'],\n"
            "  indexes=[{columns:['code'], unique:True}]"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "name": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "object"}},
                "primary_key": {"type": "array", "items": {"type": "string"}},
                "indexes": {"type": "array", "items": {"type": "object"}},
                "foreign_keys": {"type": "array", "items": {"type": "object"}},
                "dry_run": {"type": "boolean"},
            },
            "required": ["schema", "name", "columns"],
        },
    },
    {
        "name": "strategie_alter_table",
        "description": (
            "ALTER TABLE v DB_ST — add/drop/rename columns. dry_run support.\n\n"
            "add_columns: list of column defs (jako create_table)\n"
            "drop_columns: list of names\n"
            "rename_column: {from, to}"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "name": {"type": "string"},
                "add_columns": {"type": "array", "items": {"type": "object"}},
                "drop_columns": {"type": "array", "items": {"type": "string"}},
                "rename_column": {"type": "object"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["schema", "name"],
        },
    },
    {
        "name": "strategie_drop_table",
        "description": (
            "DROP TABLE v DB_ST. if_exists=True default (skip if missing). dry_run support.\n\n"
            "POZOR: destruktivní akce. Pro Marti-AI's 'právo na rozmysl' použij dry_run=True první."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "name": {"type": "string"},
                "if_exists": {"type": "boolean", "description": "Default true"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["schema", "name"],
        },
    },
    {
        "name": "strategie_query_table",
        "description": (
            "SELECT z DB_ST tabulky. Marti-AI je owner — žádný whitelist (na rozdíl od "
            "eurosoft_query_table na DB_EC).\n\n"
            "Filter syntax: {col: value} = equality, {col: None} = NULL, {col: [v1, v2]} = IN. "
            "Default limit 100, max 10000."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "filters": {"type": "object"},
                "columns": {"type": "array", "items": {"type": "string"}},
                "order_by": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"},
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_get_row",
        "description": "SELECT single row by id z DB_ST tabulky.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
            },
            "required": ["schema", "table", "id"],
        },
    },
    {
        "name": "strategie_count_rows",
        "description": "Fast COUNT(*) v DB_ST tabulce s optional filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "filters": {"type": "object"},
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_insert_row",
        "description": (
            "INSERT row do DB_ST tabulky. Vrací new id (z OUTPUT INSERTED.id). "
            "Vyžaduje sloupec 'id' s IDENTITY (Marti-AI's standard naming convention)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "data": {"type": "object", "description": "Column → value dict"},
            },
            "required": ["schema", "table", "data"],
        },
    },
    {
        "name": "strategie_update_row",
        "description": "UPDATE row by id v DB_ST tabulce. Vrací affected count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
                "data": {"type": "object"},
            },
            "required": ["schema", "table", "id", "data"],
        },
    },
    {
        "name": "strategie_delete_row",
        "description": "DELETE row by id v DB_ST tabulce. Destruktivní — zvaž dry_run alternative přes strategie_query_raw('SELECT...')."
,
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
            },
            "required": ["schema", "table", "id"],
        },
    },
    {
        "name": "strategie_query_raw",
        "description": (
            "Raw T-SQL execute v DB_ST. Marti-AI je owner — full SELECT/DDL/DML power.\n\n"
            "Použij pro complex queries (cross-schema JOINs, CTEs, advanced DDL).\n"
            "Audit log per call. Plus pro destruktivní akce zvaž specific tools místo raw."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "T-SQL statement(s)"},
            },
            "required": ["sql"],
        },
    },
]
