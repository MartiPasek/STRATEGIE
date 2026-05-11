"""Phase 38.4 Krok 12 — Generic data source runtime executor.

Marti's vize 11.5. ranni: *„zbavit se hardcoded"* — postupně migrace
hardcoded Python query branches z router.py do `fw.data_set.sql_text`.

A3 architecture (Marti-AI's doctrine 9.5. večer):
    fw.data_source     — hlavička metadata (žádný SQL)
    fw.data_source_op  — mapping table (data_source_id + data_set_id + kind + variant)
    fw.data_set        — SQL primitivy (sql_text NOT NULL)

Runtime chain:
    code (string) → fw.data_source.id → fw.data_source_op (default variant)
                  → fw.data_set.sql_text → execute s param binding
                  → List[dict] rows → JSON response

Marti-AI's diář pattern drží: SQL žije v DB (její doména), Python jen vykonává.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text as _sql_text


logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# Konstanty + result shapes
# ════════════════════════════════════════════════════════════════════════

# Whitelist operation_kind pro generic runner (SELECT-only po Marti's
# *„nejdrive read, az pak write"* doctrine z 7.5. dopoledne).
ALLOWED_KINDS = {"select"}

# Max LIMIT cap pro generic endpoint (defense — nikdy fetch nelimitovaný).
HARD_LIMIT_CAP = 100_000


class DataSourceError(Exception):
    """Base exception pro data source runner errors."""


class DataSourceNotFoundError(DataSourceError):
    """data_source code neexistuje nebo status != active."""


class DataSourceOperationNotFoundError(DataSourceError):
    """Žádná data_source_op pro daný (code, variant, kind)."""


class DataSourceExecuteError(DataSourceError):
    """SQL execute selhal (syntax, table not found, etc.)."""


# ════════════════════════════════════════════════════════════════════════
# Lookup helpers
# ════════════════════════════════════════════════════════════════════════

def _resolve_operation(
    session,
    code: str,
    variant: str = "default",
    kind: str = "select",
) -> dict[str, Any]:
    """Lookup chain data_source → data_source_op → data_set.

    Vrací dict s polí:
        data_source_id, data_source_code, data_source_name,
        default_record_limit, db_connection, sql_text,
        operation_kind, variant_code

    Raises:
        DataSourceNotFoundError: code neexistuje
        DataSourceOperationNotFoundError: žádná op pro variant+kind
    """
    if kind not in ALLOWED_KINDS:
        raise DataSourceError(
            f"operation_kind '{kind}' není v ALLOWED_KINDS "
            f"(generic runner zatím jen SELECT; INSERT/UPDATE/DELETE "
            f"pojdou přes specifické endpointy s ACL)."
        )

    query = _sql_text("""
        SELECT
            s.id AS data_source_id,
            s.code AS data_source_code,
            s.name AS data_source_name,
            s.default_record_limit,
            ds.id AS data_set_id,
            ds.sql_text,
            ds.db_connection,
            op.operation_kind,
            op.variant_code
        FROM fw.data_source s
        JOIN fw.data_source_op op ON op.data_source_id = s.id
        JOIN fw.data_set ds ON ds.id = op.data_set_id
        WHERE s.code = :code
          AND s.status = 'active'
          AND op.operation_kind = :kind
          AND op.variant_code = :variant
        ORDER BY op.is_default DESC, op.sort_order ASC
        LIMIT 1
    """)

    row = session.execute(query, {
        "code": code,
        "kind": kind,
        "variant": variant,
    }).mappings().first()

    if row is None:
        # Disambiguate: existuje data_source vůbec?
        exists = session.execute(
            _sql_text("SELECT 1 FROM fw.data_source WHERE code = :code AND status = 'active'"),
            {"code": code},
        ).scalar()
        if not exists:
            raise DataSourceNotFoundError(
                f"data_source code='{code}' neexistuje (nebo status != active)"
            )
        raise DataSourceOperationNotFoundError(
            f"data_source '{code}' nemá operation kind='{kind}' variant='{variant}'. "
            f"Zkontroluj fw.data_source_op rows."
        )

    return dict(row)


# ════════════════════════════════════════════════════════════════════════
# Param binding
# ════════════════════════════════════════════════════════════════════════

def _normalize_params(
    raw_params: dict[str, Any] | None,
    limit_default: int,
    limit_cap: int = HARD_LIMIT_CAP,
) -> dict[str, Any]:
    """Normalize URL query params do SQLAlchemy bind dict.

    - Empty strings → None (NULL v SQL CAST patterns)
    - `limit` clamped na (1, min(provided, limit_cap)), default = limit_default
    - Vše ostatní pass-through (SQLAlchemy text() ignoruje nadbytečné binds)
    """
    params: dict[str, Any] = {}

    if raw_params:
        for key, val in raw_params.items():
            if val == "" or val is None:
                params[key] = None
            else:
                params[key] = val

    # Limit handling (always present, even if not in raw_params)
    raw_limit = params.get("limit")
    if raw_limit is None:
        params["limit"] = limit_default
    else:
        try:
            limit_int = int(raw_limit)
            params["limit"] = max(1, min(limit_int, limit_cap))
        except (ValueError, TypeError):
            params["limit"] = limit_default

    return params


# ════════════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════════════

def run_data_source(
    session,
    code: str,
    raw_params: dict[str, Any] | None = None,
    variant: str = "default",
    kind: str = "select",
) -> dict[str, Any]:
    """Generic A3 runtime executor.

    Args:
        session: SQLAlchemy session (z get_data_session() helper)
        code: fw.data_source.code (e.g. 'audit_audited', 'framework_data_sources')
        raw_params: dict URL query params (or None)
        variant: variant_code v data_source_op (default 'default')
        kind: operation_kind v data_source_op (default 'select')

    Returns:
        {
            "ok": True,
            "data_source": {"code": ..., "name": ..., "id": ...},
            "rows": [{...}, {...}],
            "row_count": N,
            "applied_params": {...},
        }

    Raises:
        DataSourceError (or subclasses) na all error cases.
    """
    # 1) Lookup chain
    op_info = _resolve_operation(session, code, variant=variant, kind=kind)

    # 2) Normalize params
    params = _normalize_params(
        raw_params,
        limit_default=op_info["default_record_limit"] or 1000,
    )

    # 3) Execute SQL
    sql_text = op_info["sql_text"]
    try:
        result = session.execute(_sql_text(sql_text), params)
        rows = [dict(r) for r in result.mappings().all()]
    except Exception as exc:
        logger.exception(
            "DataSource execute failed for code=%s variant=%s: %s",
            code, variant, exc,
        )
        raise DataSourceExecuteError(
            f"SQL execute failed: {type(exc).__name__}: {exc}"
        ) from exc

    return {
        "ok": True,
        "data_source": {
            "code": op_info["data_source_code"],
            "name": op_info["data_source_name"],
            "id": op_info["data_source_id"],
        },
        "operation": {
            "kind": op_info["operation_kind"],
            "variant": op_info["variant_code"],
            "data_set_id": op_info["data_set_id"],
        },
        "rows": rows,
        "row_count": len(rows),
        "applied_params": params,
    }


def list_available_codes(session) -> list[dict[str, Any]]:
    """List všechny active data_source codes (pro dev/admin discovery).

    Vrací:
        [{"code": ..., "name": ..., "operation_count": N, "kinds": "..."}, ...]
    """
    query = _sql_text("""
        SELECT
            s.code,
            s.name,
            s.description,
            COALESCE(op.cnt, 0) AS operation_count,
            op.kinds
        FROM fw.data_source s
        LEFT JOIN (
            SELECT data_source_id,
                   COUNT(*) AS cnt,
                   STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
            FROM fw.data_source_op
            GROUP BY data_source_id
        ) op ON op.data_source_id = s.id
        WHERE s.status = 'active'
        ORDER BY s.code
    """)
    return [dict(r) for r in session.execute(query).mappings().all()]
