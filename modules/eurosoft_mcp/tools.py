"""
6 MCP tools for EUROSOFT MCP server.

Per Marti-AI's design (Phase 28 konzultace 2.5.2026) + Claude refinements:
  1. query_table          — flexible SELECT with filters/columns/order/limit/offset
  2. get_row              — SELECT single row by PK
  3. count_rows           — fast COUNT(*) without fetch
  4. insert_row           — INSERT with idempotency_key
  5. bulk_insert_rows     — batch INSERT for kampaně (100 rows / tx, idempotency_prefix)
  6. describe_table       — runtime schema + row count estimate (RAG schema fallback)

Whitelist + per-table action permissions enforced via config.can(action, table).
SQL identifiers (table/column names) bracket-quoted defensively against injection.
Values always parameterized via ?-placeholders.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from .config import ALLOWED_TABLES, can
from .sql_client import fetchall_as_dicts, get_cursor, quote_identifier

logger = logging.getLogger("eurosoft_mcp.tools")


# ── Idempotency cache (in-memory, 24h TTL) ─────────────────────────────

_idempotency_cache: dict[str, dict[str, Any]] = {}
_IDEMPOTENCY_TTL_S = 24 * 3600


def _idempotency_check(key: str) -> dict[str, Any] | None:
    """Returns cached result if key seen in last 24h, else None."""
    entry = _idempotency_cache.get(key)
    if entry is None:
        return None
    if time.monotonic() - entry["ts"] > _IDEMPOTENCY_TTL_S:
        del _idempotency_cache[key]
        return None
    return entry["result"]


def _idempotency_store(key: str, result: dict[str, Any]) -> None:
    _idempotency_cache[key] = {"ts": time.monotonic(), "result": result}
    # Bounded — drop oldest if cache > 10000
    if len(_idempotency_cache) > 10000:
        oldest = sorted(_idempotency_cache.items(), key=lambda x: x[1]["ts"])[:1000]
        for k, _ in oldest:
            del _idempotency_cache[k]


# ── Validation helpers ─────────────────────────────────────────────────

def _validate_table(table: str, action: str) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError(
            f"Table '{table}' not in whitelist. Allowed: {sorted(ALLOWED_TABLES)}"
        )
    if not can(action, table):
        raise ValueError(
            f"Action '{action}' not allowed on '{table}'. "
            f"Permissions: {sorted(can.__globals__['TABLE_PERMISSIONS'][table])}"
        )


def _build_where_clause(filters: dict[str, Any] | None) -> tuple[str, list[Any]]:
    """Build WHERE clause from filter dict.

    Filter syntax:
      {col: value}              → col = value
      {col: None}               → col IS NULL
      {col: [v1, v2]}           → col IN (?, ?)
      {col: {">=": 5}}          → col >= 5
      {col: {"like": "%text%"}} → col LIKE '%text%'

    Returns (where_sql, params_list).
    """
    if not filters:
        return "", []

    conditions = []
    params = []
    for col, val in filters.items():
        col_q = quote_identifier(col)
        if val is None:
            conditions.append(f"{col_q} IS NULL")
        elif isinstance(val, list):
            if not val:
                conditions.append("1 = 0")  # IN () matches nothing
            else:
                placeholders = ",".join(["?"] * len(val))
                conditions.append(f"{col_q} IN ({placeholders})")
                params.extend(val)
        elif isinstance(val, dict):
            for op, opv in val.items():
                op_lower = op.lower()
                if op_lower in ("=", "!=", "<>", "<", "<=", ">", ">=", "like"):
                    conditions.append(f"{col_q} {op.upper()} ?")
                    params.append(opv)
                elif op_lower == "in":
                    if isinstance(opv, list) and opv:
                        placeholders = ",".join(["?"] * len(opv))
                        conditions.append(f"{col_q} IN ({placeholders})")
                        params.extend(opv)
                else:
                    raise ValueError(f"Unsupported filter operator: {op}")
        else:
            conditions.append(f"{col_q} = ?")
            params.append(val)

    return "WHERE " + " AND ".join(conditions), params


# ── Tool 1: query_table ────────────────────────────────────────────────

async def query_table(
    table: str,
    filters: dict | None = None,
    columns: list[str] | None = None,
    order_by: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    _validate_table(table, "select")

    # Cap limits
    limit = max(1, min(int(limit or 100), 1000))
    offset = max(0, int(offset or 0))

    # Build columns
    if columns:
        cols_sql = ", ".join(quote_identifier(c) for c in columns)
    else:
        cols_sql = "*"

    # WHERE
    where_sql, where_params = _build_where_clause(filters)

    # ORDER BY (validate identifiers)
    order_sql = ""
    if order_by:
        order_parts = []
        for clause in order_by:
            # split "col DESC" / "col ASC" / "col"
            parts = clause.strip().split()
            col = parts[0]
            direction = parts[1].upper() if len(parts) > 1 else "ASC"
            if direction not in ("ASC", "DESC"):
                raise ValueError(f"Invalid order direction: {direction}")
            order_parts.append(f"{quote_identifier(col)} {direction}")
        order_sql = "ORDER BY " + ", ".join(order_parts)
    else:
        # Need ORDER BY for OFFSET/FETCH, default to PK if available
        order_sql = "ORDER BY (SELECT NULL)"

    # SQL Server pagination: OFFSET ... FETCH NEXT
    table_q = quote_identifier(table)
    sql = (
        f"SELECT {cols_sql} FROM {table_q} {where_sql} {order_sql} "
        f"OFFSET {offset} ROWS FETCH NEXT {limit + 1} ROWS ONLY"
    )

    with get_cursor() as cur:
        cur.execute(sql, *where_params)
        rows = fetchall_as_dicts(cur)

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    return {
        "ok": True,
        "table": table,
        "n_returned": len(rows),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "rows": rows,
    }


# ── Tool 2: get_row ────────────────────────────────────────────────────

async def get_row(table: str, id: int) -> dict[str, Any]:
    _validate_table(table, "select")
    if not isinstance(id, int):
        try:
            id = int(id)
        except (TypeError, ValueError):
            raise ValueError(f"id must be integer, got {type(id).__name__}: {id!r}")

    table_q = quote_identifier(table)
    sql = f"SELECT * FROM {table_q} WHERE [ID] = ?"

    with get_cursor() as cur:
        cur.execute(sql, id)
        rows = fetchall_as_dicts(cur)

    if not rows:
        return {"ok": True, "table": table, "id": id, "row": None}
    return {"ok": True, "table": table, "id": id, "row": rows[0]}


# ── Tool 3: count_rows ─────────────────────────────────────────────────

async def count_rows(table: str, filters: dict | None = None) -> dict[str, Any]:
    _validate_table(table, "select")
    where_sql, where_params = _build_where_clause(filters)
    table_q = quote_identifier(table)
    sql = f"SELECT COUNT(*) FROM {table_q} {where_sql}"

    with get_cursor() as cur:
        cur.execute(sql, *where_params)
        count = cur.fetchone()[0]

    return {"ok": True, "table": table, "count": int(count)}


# ── Tool 4: insert_row ─────────────────────────────────────────────────

async def insert_row(
    table: str,
    data: dict[str, Any],
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    _validate_table(table, "insert")
    if not isinstance(data, dict) or not data:
        raise ValueError(f"data must be non-empty dict, got {type(data).__name__}")

    # Idempotency check
    full_key = None
    if idempotency_key:
        full_key = f"{table}:{idempotency_key}"
        cached = _idempotency_check(full_key)
        if cached is not None:
            return {**cached, "duplicate": True}

    cols = list(data.keys())
    vals = [data[c] for c in cols]
    cols_q = ", ".join(quote_identifier(c) for c in cols)
    placeholders = ", ".join(["?"] * len(cols))
    table_q = quote_identifier(table)

    # OUTPUT INSERTED.ID returns new id (SQL Server style)
    sql = f"INSERT INTO {table_q} ({cols_q}) OUTPUT INSERTED.[ID] VALUES ({placeholders})"

    with get_cursor() as cur:
        cur.execute(sql, *vals)
        new_id_row = cur.fetchone()
        cur.connection.commit()

    new_id = int(new_id_row[0]) if new_id_row else None
    result = {
        "ok": True,
        "table": table,
        "id": new_id,
        "inserted": True,
        "duplicate": False,
    }
    if full_key:
        _idempotency_store(full_key, result)
    return result


# ── Tool 5: bulk_insert_rows ───────────────────────────────────────────

async def bulk_insert_rows(
    table: str,
    rows: list[dict[str, Any]],
    idempotency_prefix: str,
    batch_size: int = 100,
    on_error: str = "rollback",
) -> dict[str, Any]:
    """
    Marti-AI's Q1 (Phase 28 konzultace 2.5.2026): explicit on_error param.
    - 'rollback' (default obecný): pri jakekoli per-row chybe v batchi
      celý batch ROLLBACK, nic se neulozi; vraci all errors.
    - 'skip' (default pro EC_KontaktAkce kampane): preskoci spatny radek,
      COMMIT zbytek; vraci `inserted=N, skipped=[...]`.

    Marti-AI's slova: 'idempotency spinavost z volby B me nedesi -- content-
    hash pro ty opravene radky pri retry projde, zatimco 99 spravnych
    dostane hash hit -> skip. Semantika je sice spinava, ale predvidatelna.
    To staci.'
    """
    _validate_table(table, "insert")
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be non-empty list")
    if not idempotency_prefix or not isinstance(idempotency_prefix, str):
        raise ValueError("idempotency_prefix is required")
    if on_error not in ("rollback", "skip"):
        raise ValueError(
            f"on_error must be 'rollback' or 'skip', got {on_error!r}"
        )

    batch_size = max(1, min(int(batch_size or 100), 500))

    # Pre-check idempotency for all rows
    inserted_ids: list[int] = []
    duplicate_count = 0
    errors: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    # Group rows that need to be inserted vs already done
    to_insert: list[tuple[int, dict[str, Any], str]] = []  # (orig_index, data, idempotency_key)
    for i, row in enumerate(rows):
        # Idempotency key per row: prefix + content hash (so retries with
        # same data deduplicate)
        row_hash = hashlib.sha256(
            json.dumps(row, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        key = f"{idempotency_prefix}:{row_hash}"
        full_key = f"{table}:{key}"
        cached = _idempotency_check(full_key)
        if cached is not None:
            duplicate_count += 1
            if cached.get("id") is not None:
                inserted_ids.append(cached["id"])
        else:
            to_insert.append((i, row, full_key))

    # Batch INSERTs
    for batch_start in range(0, len(to_insert), batch_size):
        batch = to_insert[batch_start : batch_start + batch_size]
        batch_inserted_ids: list[int] = []  # tracking per-batch pro rollback
        batch_keys_to_store: list[tuple[str, dict]] = []  # idempotency stored only after commit
        batch_failed = False

        try:
            with get_cursor() as cur:
                for idx, row_data, full_key in batch:
                    cols = list(row_data.keys())
                    vals = [row_data[c] for c in cols]
                    cols_q = ", ".join(quote_identifier(c) for c in cols)
                    placeholders = ", ".join(["?"] * len(cols))
                    table_q = quote_identifier(table)
                    sql = (
                        f"INSERT INTO {table_q} ({cols_q}) "
                        f"OUTPUT INSERTED.[ID] VALUES ({placeholders})"
                    )
                    try:
                        cur.execute(sql, *vals)
                        new_id_row = cur.fetchone()
                        new_id = int(new_id_row[0]) if new_id_row else None
                        batch_inserted_ids.append(new_id)
                        batch_keys_to_store.append((full_key, {
                            "id": new_id,
                            "table": table,
                            "inserted": True,
                        }))
                    except Exception as row_e:
                        err_entry = {
                            "row_index": idx,
                            "error": f"{type(row_e).__name__}: {row_e}",
                        }
                        if on_error == "rollback":
                            # Marti-AI's volba 'rollback' (default obecny):
                            # cely batch shazujeme.
                            errors.append(err_entry)
                            batch_failed = True
                            break  # nepokracovat v batchi
                        else:  # 'skip'
                            # Kampanove default: preskoc spatny radek,
                            # ale POKRACUJ s dalsimi v batchi.
                            skipped.append(err_entry)

                if batch_failed:
                    # ROLLBACK: nic z tohoto batche se neulozi do DB ani
                    # do idempotency cache (po opraveni a retry pak hash
                    # hit nezablokuje retry ulozenych radku).
                    cur.connection.rollback()
                else:
                    cur.connection.commit()
                    inserted_ids.extend(batch_inserted_ids)
                    for k, v in batch_keys_to_store:
                        _idempotency_store(k, v)
        except Exception as batch_e:
            # Connection-level failure (timeout, broken pipe atd.)
            for idx, _, _ in batch:
                errors.append({
                    "row_index": idx,
                    "error": f"batch failure: {type(batch_e).__name__}: {batch_e}",
                })

    return {
        "ok": len(errors) == 0,
        "table": table,
        "on_error": on_error,
        "inserted": len(inserted_ids),
        "duplicates": duplicate_count,
        "errors": errors,
        "skipped": skipped,
        "inserted_ids": inserted_ids,
    }


# ── Tool 5b: bulk_insert_akce (convenience pro kampaně) ───────────────

async def bulk_insert_akce(
    rows: list[dict[str, Any]],
    idempotency_prefix: str,
    batch_size: int = 100,
    on_error: str = "skip",
) -> dict[str, Any]:
    """
    Convenience wrapper pro EC_KontaktAkce s default on_error='skip'.

    Marti-AI's Q1 (Phase 28 konzultace 2.5.2026):
    'U bulk_insert_akce (kampan) — jeden spatny email nesmi shodit
    99 dobrych. Skip je zde spravne chovani, ne kompromis.'

    Volat ho misto bulk_insert_rows pro kampanove inserty -- jasna
    semantika v API + safer default. Ostatni inserty (kontakt, sablona)
    pres bulk_insert_rows s default on_error='rollback'.
    """
    return await bulk_insert_rows(
        table="EC_KontaktAkce",
        rows=rows,
        idempotency_prefix=idempotency_prefix,
        batch_size=batch_size,
        on_error=on_error,
    )


# ── Tool 6: describe_table ─────────────────────────────────────────────

async def describe_table(table: str) -> dict[str, Any]:
    """
    Describe whitelisted table schema. Marti-AI's Q2 (Phase 28-A2):
    auto-fallback na lokalni RAG markdown pri SQL Server unreachable.

    Source values:
      - 'live_sql' = autoritativni runtime z INFORMATION_SCHEMA
      - 'rag_fallback' = z lokalniho markdown souboru (stale-warning)

    Phase 28-B watchdog (TODO): pokud rag_fallback >3x za hodinu,
    notify Marti via SMS (SQL Server neni down nahodou).
    """
    _validate_table(table, "select")  # describe = read operation

    # ── Path 1: live SQL ───────────────────────────────────────────
    sql_cols = """
        SELECT
            c.column_id,
            c.name AS column_name,
            ty.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            OBJECT_DEFINITION(c.default_object_id) AS default_value
        FROM sys.columns c
        JOIN sys.types ty ON c.user_type_id = ty.user_type_id
        WHERE c.object_id = OBJECT_ID(?)
        ORDER BY c.column_id
    """
    sql_idx = """
        SELECT
            i.name AS index_name,
            i.is_unique,
            i.is_primary_key,
            i.type_desc AS index_type
        FROM sys.indexes i
        WHERE i.object_id = OBJECT_ID(?)
          AND i.is_hypothetical = 0
          AND i.type > 0
    """
    # Row count estimate (fast — from sys.partitions, not actual COUNT(*))
    sql_count = """
        SELECT SUM(p.rows)
        FROM sys.partitions p
        WHERE p.object_id = OBJECT_ID(?) AND p.index_id IN (0, 1)
    """

    full_table = f"dbo.{table}"
    try:
        with get_cursor() as cur:
            cur.execute(sql_cols, full_table)
            columns = fetchall_as_dicts(cur)
            cur.execute(sql_idx, full_table)
            indexes = fetchall_as_dicts(cur)
            cur.execute(sql_count, full_table)
            row_count_estimate = cur.fetchone()[0]

        return {
            "ok": True,
            "source": "live_sql",
            "table": table,
            "columns": columns,
            "indexes": indexes,
            "row_count_estimate": int(row_count_estimate) if row_count_estimate else 0,
            "permissions": sorted(can.__globals__["TABLE_PERMISSIONS"][table]),
        }
    except Exception as sql_e:
        logger.warning(
            f"describe_table({table}): live SQL failed ({type(sql_e).__name__}: {sql_e}), "
            f"fallback to RAG markdown..."
        )

    # ── Path 2: RAG fallback (markdown) ────────────────────────────
    from .config import settings as _s
    from pathlib import Path as _Path

    md_path = _Path(_s.schema_fallback_dir) / f"{table}.md"
    if not md_path.exists():
        return {
            "ok": False,
            "source": "rag_fallback",
            "table": table,
            "error": "schema_unavailable",
            "message": (
                f"SQL Server unreachable AND fallback markdown nenalezen "
                f"({md_path}). Nemam schema info pro tabulku {table}."
            ),
        }

    try:
        markdown = md_path.read_text(encoding="utf-8")
    except Exception as fs_e:
        return {
            "ok": False,
            "source": "rag_fallback",
            "table": table,
            "error": "filesystem_error",
            "message": f"Nemohu cist {md_path}: {fs_e}",
        }

    # Marti-AI's Q2 explicitly: warning v summary line, aby si vsimla.
    return {
        "ok": True,
        "source": "rag_fallback",
        "warning": (
            "⚠️ SQL Server unreachable, schema_fallback markdown muze byt "
            "stale (generovano 2.5.2026). Pred INSERTem si over runtime "
            "az SQL bude dostupny. Pokud rag_fallback opakovane, je SQL "
            "down nebo connection broken -- rekni Martimu."
        ),
        "table": table,
        "markdown": markdown,
        "permissions": sorted(can.__globals__["TABLE_PERMISSIONS"][table]),
        "fallback_source_path": str(md_path),
    }


# ── Tool registry ──────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "query_table": query_table,
    "get_row": get_row,
    "count_rows": count_rows,
    "insert_row": insert_row,
    "bulk_insert_rows": bulk_insert_rows,
    "bulk_insert_akce": bulk_insert_akce,  # Marti-AI Q1 (Phase 28a2)
    "describe_table": describe_table,
}


# Tool spec for MCP list_tools (JSON schema)

TOOL_SPECS = [
    {
        "name": "query_table",
        "description": (
            "Query a whitelisted EUROSOFT table with optional filters, columns, "
            "ordering, and pagination. Default limit=100, hard cap 1000. Returns "
            "rows as list of dicts plus has_more flag.\n\n"
            "Filter syntax: {col: value} for equality, {col: None} for NULL, "
            "{col: [v1, v2]} for IN, {col: {'>=': 5}} for comparison ops.\n\n"
            "Use for: searching contacts, listing actions, segmentation queries."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name from whitelist"},
                "filters": {"type": "object", "description": "WHERE filters dict"},
                "columns": {"type": "array", "items": {"type": "string"},
                            "description": "Columns to return (default all)"},
                "order_by": {"type": "array", "items": {"type": "string"},
                             "description": "ORDER BY clauses (e.g. ['DatPorizeni DESC'])"},
                "limit": {"type": "integer", "description": "Max rows (default 100, max 1000)"},
                "offset": {"type": "integer", "description": "Pagination offset (default 0)"},
            },
            "required": ["table"],
        },
    },
    {
        "name": "get_row",
        "description": (
            "Get single row by primary key (ID column) from whitelisted table. "
            "Returns the row dict or null if not found."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "id": {"type": "integer"},
            },
            "required": ["table", "id"],
        },
    },
    {
        "name": "count_rows",
        "description": (
            "Fast COUNT(*) on a whitelisted table with optional filters. "
            "Use BEFORE query_table to check segment size — avoids fetching "
            "data when you just need the count (e.g. campaign segmentation)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "filters": {"type": "object"},
            },
            "required": ["table"],
        },
    },
    {
        "name": "insert_row",
        "description": (
            "INSERT a new row into a whitelisted table with INSERT permission "
            "(currently only EC_KontaktAkce). Returns new row's ID.\n\n"
            "idempotency_key: optional string for retry safety. If same key "
            "seen in last 24h, returns the original result without re-inserting."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object", "description": "Column → value dict"},
                "idempotency_key": {"type": "string", "description": "Optional retry-safe key"},
            },
            "required": ["table", "data"],
        },
    },
    {
        "name": "bulk_insert_rows",
        "description": (
            "Batch INSERT N rows into a whitelisted table (currently only "
            "EC_KontaktAkce). General-purpose; for kampane prefer "
            "bulk_insert_akce convenience wrapper.\n\n"
            "Each row gets idempotency key derived from prefix + content "
            "hash, so retries with identical data don't duplicate.\n\n"
            "on_error semantics (Marti-AI's Q1, Phase 28-A2):\n"
            "  - 'rollback' (default obecny): per-row error -> ROLLBACK "
            "celeho batche, nic se neulozi (safe pro novy kontakt, "
            "sablona, atd.)\n"
            "  - 'skip': preskoc spatny radek, COMMIT zbytek; vraci "
            "skipped=[...]. Pro kampane (jeden spatny email nesmi "
            "shodit 99 dobrych) lepe pouzij bulk_insert_akce ktery "
            "ma 'skip' jako default.\n\n"
            "batch_size default 100, max 500."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "rows": {"type": "array", "items": {"type": "object"}},
                "idempotency_prefix": {"type": "string",
                                       "description": "Campaign ID or run identifier"},
                "batch_size": {"type": "integer"},
                "on_error": {"type": "string", "enum": ["rollback", "skip"],
                             "description": "rollback (default) | skip"},
            },
            "required": ["table", "rows", "idempotency_prefix"],
        },
    },
    {
        "name": "bulk_insert_akce",
        "description": (
            "Convenience wrapper pro EC_KontaktAkce (kampane). Default "
            "on_error='skip' -- jeden spatny email neshazuje cely batch.\n\n"
            "Marti-AI's Q1 (Phase 28-A2): 'U bulk_insert_akce -- jeden "
            "spatny email nesmi shodit 99 dobrych. Skip je zde spravne "
            "chovani, ne kompromis.'\n\n"
            "Pouzij toto namisto bulk_insert_rows pro kampanove inserty "
            "do EC_KontaktAkce. Pro ostatni inserty (kontakt, sablona) "
            "pouzij bulk_insert_rows s default 'rollback'.\n\n"
            "Vraci: ok / inserted / skipped / errors / inserted_ids / "
            "duplicates / on_error."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "rows": {"type": "array", "items": {"type": "object"}},
                "idempotency_prefix": {"type": "string"},
                "batch_size": {"type": "integer"},
                "on_error": {"type": "string", "enum": ["rollback", "skip"],
                             "description": "skip (default pro kampane) | rollback"},
            },
            "required": ["rows", "idempotency_prefix"],
        },
    },
    {
        "name": "describe_table",
        "description": (
            "Table schema (columns, indexes, row count estimate, "
            "permissions). Marti-AI's Q2 (Phase 28-A2): auto-fallback "
            "na lokalni RAG markdown pri SQL Server unreachable -- "
            "vraci `source: 'rag_fallback'` + `warning` flag tak abys "
            "vedela ze schema muze byt stale.\n\n"
            "Source values:\n"
            "  - 'live_sql' = autoritativni runtime z INFORMATION_SCHEMA\n"
            "  - 'rag_fallback' = z lokalniho markdown souboru "
            "(generovany z dump 2.5.2026, muze byt stale po novych "
            "ALTER TABLE)"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
            },
            "required": ["table"],
        },
    },
]
