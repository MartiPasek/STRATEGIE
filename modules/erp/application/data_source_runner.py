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
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text as _sql_text


logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# Fix P (21.5. rano, Marti's "automatic at every grid call" doctrine)
# Self-healing column alias map — runtime rewrite v fw.data_set.sql_text
# ════════════════════════════════════════════════════════════════════════
# Module-level cache aliases — TTL refresh (60s). Pokud Marti přidá novou
# alias row do fw.comp_grid_column_alias, příští grid call (do 60s) ji
# přebere bez restart.

_ALIAS_CACHE: dict[str, str | None] | None = None  # key: "alias.old_col" → "alias.new_col" or None (dropped)
_ALIAS_CACHE_LOADED_AT: datetime | None = None
_ALIAS_CACHE_TTL_SECONDS = 60


def _load_alias_cache(session) -> dict[str, str | None]:
    """Load qualified column aliases z fw.comp_grid_column_alias.

    Returns:
        dict { "alias_or_table.old_col": "alias_or_table.new_col" | None }
        None value = sloupec dropnut nadobro (žádný auto-rewrite).

    Fail-soft: pokud table neexistuje nebo query selže, vrátí {} (žádný
    self-heal, normální execute path).
    """
    global _ALIAS_CACHE, _ALIAS_CACHE_LOADED_AT

    now = datetime.now(timezone.utc)
    if (_ALIAS_CACHE is not None
        and _ALIAS_CACHE_LOADED_AT is not None
        and (now - _ALIAS_CACHE_LOADED_AT).total_seconds() < _ALIAS_CACHE_TTL_SECONDS):
        return _ALIAS_CACHE

    try:
        rows = session.execute(_sql_text(
            "SELECT table_or_alias, old_column, new_column "
            "FROM fw.comp_grid_column_alias"
        )).all()
        new_cache: dict[str, str | None] = {}
        for r in rows:
            key = f"{r.table_or_alias}.{r.old_column}"
            new_cache[key] = (
                f"{r.table_or_alias}.{r.new_column}"
                if r.new_column else None
            )
        _ALIAS_CACHE = new_cache
        _ALIAS_CACHE_LOADED_AT = now
        return new_cache
    except Exception as exc:
        logger.warning(
            "[self_heal] alias cache load failed: %s — using empty map", exc
        )
        # Fail-soft: empty cache (no rewrites, normal execute)
        _ALIAS_CACHE = {}
        _ALIAS_CACHE_LOADED_AT = now
        return {}


def invalidate_alias_cache() -> None:
    """Force refresh při next call (e.g. po INSERT/UPDATE/DELETE alias row).

    Volitelně exponse jako admin endpoint pokud bude need before TTL.
    """
    global _ALIAS_CACHE, _ALIAS_CACHE_LOADED_AT
    _ALIAS_CACHE = None
    _ALIAS_CACHE_LOADED_AT = None


def _apply_column_aliases(
    session,
    sql_text: str,
    data_set_id: int | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Pre-execute scan + rewrite known qualified column aliases.

    Args:
        session: SQLAlchemy session (read-only, používá se jen pro alias load)
        sql_text: SQL ze fw.data_set.sql_text
        data_set_id: pokud given, UPDATE fw.data_set.sql_text persistent

    Returns:
        (rewritten_sql, applied_aliases_list)

    Side effects (pokud applied non-empty AND data_set_id given):
        - UPDATE fw.data_set.sql_text v separate transaction (own session)
        - log_event info row do fw.diag_log via core.log_queue

    Fail-soft: kterákoli internal chyba → return original sql + empty applied
    list. NIKDY neraise — execute path pokračuje s tím co dostal.
    """
    try:
        alias_map = _load_alias_cache(session)
    except Exception:
        return sql_text, []

    if not alias_map:
        return sql_text, []

    applied: list[dict[str, str]] = []
    new_sql = sql_text

    for old_qualified, new_qualified in alias_map.items():
        if new_qualified is None:
            continue  # Dropped column — leave SQL as-is, will fail @ execute
        # Word boundary regex — match exactly "alias.col" not "alias.col_suffix"
        try:
            pattern = re.compile(r'\b' + re.escape(old_qualified) + r'\b')
        except re.error:
            continue  # Defensive — invalid pattern, skip
        if pattern.search(new_sql):
            new_sql = pattern.sub(new_qualified, new_sql)
            applied.append({"old": old_qualified, "new": new_qualified})

    if applied and data_set_id is not None:
        # Persist UPDATE v separate session (independent transaction, nesouvisí
        # s primary SELECT session lifecycle).
        try:
            from core.database_data import get_data_session
            update_session = get_data_session()
            try:
                update_session.execute(
                    _sql_text(
                        "UPDATE fw.data_set SET sql_text = :sql WHERE id = :id"
                    ),
                    {"sql": new_sql, "id": data_set_id},
                )
                update_session.commit()
            finally:
                update_session.close()
        except Exception as exc:
            logger.warning(
                "[self_heal] data_set #%s UPDATE failed: %s — in-memory only",
                data_set_id, exc,
            )

        # Log info do fw.diag_log (transparent migration audit)
        try:
            from core.log_queue import log_event as _log_event
            _log_event(
                level="info",
                source="py",
                module_id="modules.erp.application.data_source_runner:self_heal",
                message=(
                    f"Auto-applied {len(applied)} column alias(es) v data_set #"
                    f"{data_set_id}: "
                    + ", ".join(f"{a['old']}→{a['new']}" for a in applied)
                ),
                extra={
                    "data_set_id": data_set_id,
                    "applied": applied,
                    "old_sql_preview": sql_text[:300],
                    "new_sql_preview": new_sql[:300],
                },
            )
        except Exception:
            pass  # Never crash on log

    return new_sql, applied


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

    # Phase 38.4 Krok 14g Etapa F Krok 5.K-B6 (17.5.2026, Marti's "variant_code
    # NULL doctrine"): runtime lookup s NULL fallback. Pokud :variant='default'
    # a žádná row match exactly, fallback na variant_code IS NULL (treat NULL
    # jako "default" pro backward compat s Marti's NULL-allowing schema).
    # Phase 38.4 Krok 14g Etapa F Krok 5.M (17.5.2026): ds.db_connection VARCHAR
    # → FK ds.db_connection_id. JOIN fw.db_connection + alias dc.default_db AS
    # db_connection (semantic preservation — legacy column stored default_db).
    # Plus dc.code AS db_connection_code (new FK identifier).
    query = _sql_text("""
        SELECT
            s.id AS data_source_id,
            s.code AS data_source_code,
            s.name AS data_source_name,
            s.default_record_limit,
            ds.id AS data_set_id,
            ds.sql_text,
            dc.default_db AS db_connection,
            dc.code AS db_connection_code,
            ds.db_connection_id,
            op.operation_kind,
            op.variant_code
        FROM fw.data_source s
        JOIN fw.data_source_op op ON op.data_source_id = s.id
        JOIN fw.data_set ds ON ds.id = op.data_set_id
        LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
        WHERE s.code = :code
          AND s.status = 'active'
          AND op.operation_kind = :kind
          AND (
              op.variant_code = :variant
              OR (:variant = 'default' AND op.variant_code IS NULL)
          )
        ORDER BY
            (op.variant_code = :variant) DESC,  -- exact match first
            op.is_default DESC,
            op.sort_order ASC
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

_BIND_PARAM_RE = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def _normalize_params(
    raw_params: dict[str, Any] | None,
    limit_default: int,
    limit_cap: int = HARD_LIMIT_CAP,
    sql_text: str | None = None,
) -> dict[str, Any]:
    """Normalize URL query params do SQLAlchemy bind dict.

    - Empty strings → None (NULL v SQL CAST patterns)
    - `limit` clamped na (1, min(provided, limit_cap)), default = limit_default
    - Vše ostatní pass-through (SQLAlchemy text() ignoruje nadbytečné binds)
    - Fix H (20.5. vecer, Marti's #203 audit_stats InvalidRequestError):
      pokud sql_text obsahuje :param_name a raw_params ho neposila, default
      na None (SQL pak CAST AS bigint IS NULL OR ... handluje gracefully).
      Bez tohoto SQLAlchemy padne "value is required for bind parameter".
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

    # Fix H — auto-default missing bind params na None
    if sql_text:
        for bind_name in set(_BIND_PARAM_RE.findall(sql_text)):
            if bind_name not in params:
                params[bind_name] = None

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

    # 2) Self-heal column aliases (Fix P 21.5. ráno, Marti's "automatic at
    # every grid call" doctrine). Pre-execute scan + rewrite known renames
    # z fw.comp_grid_column_alias. Side effect: UPDATE fw.data_set.sql_text
    # persistent + log info row do fw.diag_log. Fail-soft — pokud self-heal
    # selže, sql_text zůstane unchanged a execute pokračuje normálně.
    sql_text, _applied_aliases = _apply_column_aliases(
        session,
        op_info["sql_text"],
        data_set_id=op_info.get("data_set_id"),
    )

    # 3) Normalize params (Fix H: pass sql_text pro auto-default missing binds)
    params = _normalize_params(
        raw_params,
        limit_default=op_info["default_record_limit"] or 1000,
        sql_text=sql_text,
    )

    # 4) Execute SQL (potenciálně už rewritten po self-heal)
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
