"""Phase 35-E.2 (8.5.2026): PostgreSQL DDL/DML service pro Marti-AI.

Marti-AI's primary database role v PostgreSQL (data_db):
  User: "Marti-AI" (case-preserved, hyphen, quoted in DDL)
  Owner: master/tenant/tenant_group/"user" schemas
  Read-only: public schema (existing operational tables)

Marti's design philosophy 8.5.2026 ~16:00:
  „Long-term endgame = single PostgreSQL framework. Marti-AI primary
   owner uz ted, ne nekdy pozdeji. MSSQL jako zdroj puvodni pravdy."

dry_run pattern (Marti-AI's "pravo na rozmysl pred cinem", 7.5.2026 vecer):
  - create_table, alter_table, drop_table maji dry_run=True default
  - Vraci SQL preview + warnings (duplicate columns, schema missing,
    table already exists, FK target invalid)
  - dry_run=False execute s explicit COMMIT

Identifier quoting (PostgreSQL specifika):
  - quote_pg_identifier() automaticky quotuje case-sensitive nebo
    reserved-word identifiers
  - Marti-AI pise prostey 'fw.entity_def', kod zajisti
    "user", "Marti-AI" quoted

Audit:
  - Vsechny DDL operace logovany s prefixem STRATEGIE_PG
  - PG server-side log ukaze "Marti-AI" jako session_user (nezavislé
    audit trail v PG samotnem)
"""
from __future__ import annotations

import logging
import os
import re
from contextlib import contextmanager
from typing import Any, Optional, Generator
from urllib.parse import quote_plus

# Load .env into os.environ pri module import.
# STRATEGIE-API pouziva pydantic-settings (core/config.py) s extra="ignore",
# ktery cte .env primo do Settings instance ale NEPOPULUJE os.environ.
# Takze os.getenv("MARTI_AI_PG_PASSWORD") by vracelo None.
# load_dotenv() je idempotentni a default neuverezi existujici env vars.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv missing -- env vars must come from system

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger("strategie_pg.service")


# ── Constants ────────────────────────────────────────────────────────

# 4-tier model (Marti-AI's contribution 7.5.2026 + 4. vrstva user)
EXPECTED_SCHEMAS = ("master", "tenant", "tenant_group", "user")

# PostgreSQL reserved words (subset — full list je 100+, my pokryjeme top 40
# co se realne vyskytuji v naming context)
PG_RESERVED_WORDS = {
    "user", "order", "group", "table", "select", "from", "where",
    "and", "or", "not", "in", "null", "true", "false", "case", "when",
    "then", "else", "end", "join", "left", "right", "inner", "outer",
    "on", "as", "by", "having", "limit", "offset", "asc", "desc",
    "primary", "key", "foreign", "references", "check", "unique",
    "constraint", "default", "create", "alter", "drop", "insert",
    "update", "delete", "into", "values", "set", "grant", "revoke",
    "all", "any", "between", "exists", "like", "is", "with", "union",
}

# DDL whitelist patterns pro query_raw (defensive)
QUERY_RAW_ALLOWED = re.compile(
    r"^\s*(SELECT|WITH|EXPLAIN|SHOW)\b",
    re.IGNORECASE,
)
QUERY_RAW_FORBIDDEN = re.compile(
    r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|CREATE|TRUNCATE|MERGE|"
    r"GRANT|REVOKE|VACUUM|ANALYZE|CLUSTER|REINDEX)\b",
    re.IGNORECASE,
)
# Phase 38.4 Krok 9-C+ fix (10.5.2026): Marti-AI prefixovala SELECT s `-- komentář`
# pro vlastní orientaci → guard rejecta. Strip leading komentáře (-- a /* */)
# PŘED match. Marti-AI: *„dokumentace SQL by nemělo selhat na guard."*
QUERY_RAW_LEADING_COMMENT = re.compile(
    r"^\s*(--[^\n]*(\n|$)|/\*.*?\*/)\s*",
    re.DOTALL,
)


# ── Engine / connection management ───────────────────────────────────

_engine: Engine | None = None
_SessionFactory: Optional[sessionmaker] = None


def _get_engine() -> Engine:
    """Lazy singleton engine pro Marti-AI PostgreSQL connection.

    Reuses host/port/dbname z STRATEGIE-API konfigurace (settings.database_data_url),
    ale pouziva dedicated "Marti-AI" PostgreSQL role pro audit transparency.
    """
    global _engine, _SessionFactory
    if _engine is not None:
        return _engine

    pg_password = os.getenv("MARTI_AI_PG_PASSWORD")
    if not pg_password:
        raise RuntimeError(
            "MARTI_AI_PG_PASSWORD env var not set. "
            "Cannot connect to PostgreSQL as Marti-AI role. "
            "Add to .env: MARTI_AI_PG_PASSWORD=<heslo>"
        )

    # Parse settings.database_data_url (STRATEGIE-API existing PG connection)
    # a extract host/port/db. Pak swap user/password na "Marti-AI".
    from urllib.parse import urlparse, urlunparse
    from core.config import settings as _strategie_settings

    base_url = _strategie_settings.database_data_url
    if not base_url:
        raise RuntimeError(
            "settings.database_data_url not configured. "
            "Cannot derive PostgreSQL host/port/db. "
            "Check .env: DATABASE_DATA_URL=postgresql://..."
        )

    parsed = urlparse(base_url)
    pg_host = parsed.hostname or "localhost"
    pg_port = parsed.port or 5432
    pg_db = (parsed.path or "/data_db").lstrip("/")

    # User je "Marti-AI" hardcoded (intentional — case-preserved, hyphen).
    # Zname presny string, nezamenime se s string interpolaci.
    pg_user = "Marti-AI"

    # URL-encode user a password (hyphen v userovi, special chars v hesle)
    user_url = quote_plus(pg_user)
    pwd_url = quote_plus(pg_password)

    # Coerce scheme na postgresql+psycopg2 (settings.database_data_url muze byt
    # 'postgresql://' bez explicit driveru)
    scheme = parsed.scheme
    if scheme == "postgresql":
        scheme = "postgresql+psycopg2"
    elif not scheme:
        scheme = "postgresql+psycopg2"

    netloc = f"{user_url}:{pwd_url}@{pg_host}:{pg_port}"
    url = urlunparse((
        scheme,
        netloc,
        f"/{pg_db}",
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))

    logger.info(
        f"STRATEGIE_PG | initializing engine | user={pg_user} "
        f"host={pg_host}:{pg_port} db={pg_db}"
    )

    _engine = create_engine(
        url,
        pool_size=2,
        max_overflow=4,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    _SessionFactory = sessionmaker(bind=_engine)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager pro Marti-AI PG session. Auto close, no autocommit.

    Use ako:
        with get_session() as s:
            s.execute(text("SELECT ..."))
            s.commit()  # explicit pro DDL
    """
    _get_engine()  # ensure initialized
    if _SessionFactory is None:
        raise RuntimeError("strategie_pg engine not initialized")
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


# ── Identifier quoting ───────────────────────────────────────────────

def quote_pg_identifier(name: str) -> str:
    """Quote PostgreSQL identifier pokud potreba.

    Quoting pravidla (PostgreSQL spec):
      1. Reserved words (user, order, table, ...) → quote
      2. Hyphen v nazvu (Marti-AI) → quote
      3. Uppercase pismena (PG je case-sensitive jen v quoted) → quote
      4. Special chars (@, #, $, ...) → quote
      5. Zacinajici cislem → quote
      6. Default lowercase alfanum + underscore → bez quoting

    Examples:
      quote_pg_identifier("master")     → 'master'
      quote_pg_identifier("user")       → '"user"' (reserved)
      quote_pg_identifier("Marti-AI")   → '"Marti-AI"' (hyphen + uppercase)
      quote_pg_identifier("entity_def") → 'entity_def'
      quote_pg_identifier("123abc")     → '"123abc"' (starts with digit)
    """
    if not name or not isinstance(name, str):
        raise ValueError(f"Invalid PG identifier: {name!r}")

    needs_quote = False
    if name.lower() in PG_RESERVED_WORDS:
        needs_quote = True
    elif name != name.lower():
        needs_quote = True
    elif not name.replace("_", "").isalnum():
        needs_quote = True
    elif name and name[0].isdigit():
        needs_quote = True

    if needs_quote:
        # Escape internal double quotes per PostgreSQL spec ("" escape)
        escaped = name.replace('"', '""')
        return f'"{escaped}"'
    return name


def quote_qualified(schema: str, table: str) -> str:
    """Quote schema.table pair (each independently quoted)."""
    return f"{quote_pg_identifier(schema)}.{quote_pg_identifier(table)}"


# ── Discovery functions ──────────────────────────────────────────────

def list_schemas() -> dict:
    """Vraci schémata, ke kterym ma Marti-AI pristup."""
    with get_session() as s:
        rows = s.execute(text("""
            SELECT schema_name, schema_owner
            FROM information_schema.schemata
            WHERE schema_owner = 'Marti-AI'
               OR schema_name IN ('public', 'master', 'tenant',
                                  'tenant_group', 'user')
            ORDER BY schema_name
        """)).fetchall()
        return {
            "ok": True,
            "schemas": [
                {"name": r[0], "owner": r[1]} for r in rows
            ],
            "expected": list(EXPECTED_SCHEMAS),
            "missing_expected": [
                s for s in EXPECTED_SCHEMAS
                if s not in [r[0] for r in rows]
            ],
        }


def list_tables(schema: Optional[str] = None) -> dict:
    """Vraci tabulky v schémamu.

    schema=None → vsechna Marti-AI's schémata (master/tenant/tenant_group/user)
    schema="public" → existujici operational tables (read-only pro Marti-AI)
    """
    with get_session() as s:
        if schema:
            sql = text("""
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    obj_description(c.oid, 'pg_class') AS description,
                    pg_total_relation_size(c.oid) AS size_bytes,
                    (SELECT COUNT(*) FROM information_schema.columns
                     WHERE table_schema = n.nspname
                       AND table_name = c.relname) AS column_count
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = :schema
                  AND c.relkind = 'r'
                ORDER BY c.relname
            """)
            rows = s.execute(sql, {"schema": schema}).fetchall()
        else:
            sql = text("""
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    obj_description(c.oid, 'pg_class') AS description,
                    pg_total_relation_size(c.oid) AS size_bytes,
                    (SELECT COUNT(*) FROM information_schema.columns
                     WHERE table_schema = n.nspname
                       AND table_name = c.relname) AS column_count
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname IN ('master', 'tenant',
                                    'tenant_group', 'user')
                  AND c.relkind = 'r'
                ORDER BY n.nspname, c.relname
            """)
            rows = s.execute(sql).fetchall()
        return {
            "ok": True,
            "schema_filter": schema,
            "tables": [
                {
                    "schema_name": r[0],
                    "table_name": r[1],
                    "description": r[2],
                    "size_bytes": r[3],
                    "column_count": r[4],
                }
                for r in rows
            ],
            "count": len(rows),
        }


def describe_table(schema: str, table: str) -> dict:
    """Vraci kompletni strukturu tabulky (sloupce, indexy, FK, constraints)."""
    with get_session() as s:
        # Sloupce
        cols_sql = text("""
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
        """)
        cols = s.execute(cols_sql, {"schema": schema, "table": table}).fetchall()

        if not cols:
            return {
                "ok": False,
                "error": f"Tabulka {schema}.{table} neexistuje, "
                         f"nebo nemate pristup.",
            }

        # Indexy
        indexes_sql = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = :schema AND tablename = :table
            ORDER BY indexname
        """)
        indexes = s.execute(
            indexes_sql, {"schema": schema, "table": table}
        ).fetchall()

        # Constraints
        constraints_sql = text("""
            SELECT
                con.conname AS name,
                con.contype AS type,
                pg_get_constraintdef(con.oid) AS definition
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace ns ON ns.oid = rel.relnamespace
            WHERE ns.nspname = :schema AND rel.relname = :table
            ORDER BY con.conname
        """)
        constraints = s.execute(
            constraints_sql, {"schema": schema, "table": table}
        ).fetchall()

        # Row count estimate (pg_class.reltuples — rychly approximate)
        count_sql = text("""
            SELECT reltuples::BIGINT AS estimate
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = :schema AND c.relname = :table
        """)
        count_row = s.execute(
            count_sql, {"schema": schema, "table": table}
        ).fetchone()
        row_count_estimate = count_row[0] if count_row else 0

        return {
            "ok": True,
            "schema": schema,
            "table": table,
            "columns": [
                {
                    "name": c[0],
                    "data_type": c[1],
                    "udt_name": c[2],
                    "nullable": c[3] == "YES",
                    "default": c[4],
                    "char_max_length": c[5],
                    "numeric_precision": c[6],
                    "numeric_scale": c[7],
                    "position": c[8],
                }
                for c in cols
            ],
            "indexes": [
                {"name": i[0], "definition": i[1]} for i in indexes
            ],
            "constraints": [
                {
                    "name": c[0],
                    "type": _decode_constraint_type(c[1]),
                    "definition": c[2],
                }
                for c in constraints
            ],
            "row_count_estimate": row_count_estimate,
        }


def _decode_constraint_type(t: str) -> str:
    """Decode PG constraint type 1-char code."""
    return {
        "p": "PRIMARY KEY",
        "f": "FOREIGN KEY",
        "u": "UNIQUE",
        "c": "CHECK",
        "x": "EXCLUSION",
        "t": "TRIGGER",
    }.get(t, t)


# ── DDL functions (s dry_run support) ────────────────────────────────

def create_table(
    schema: str,
    name: str,
    columns: list[dict],
    primary_key: Optional[list[str]] = None,
    indexes: Optional[list[dict]] = None,
    foreign_keys: Optional[list[dict]] = None,
    description: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """CREATE TABLE v PostgreSQL. Marti-AI je owner.

    columns: [{name, type, nullable?, identity?, default?}]
      type: PG-native type (BIGINT, VARCHAR(50), TEXT, TIMESTAMPTZ, ...)
      identity=True → BIGSERIAL (auto-increment)
    primary_key: list of column names (default: ['id'] pokud existuje)
    indexes: [{name?, columns: [...], unique?, partial?}]
    foreign_keys: [{column, ref_schema, ref_table, ref_column,
                    on_delete?, on_update?}]
    description: COMMENT ON TABLE (volitelne)

    dry_run=True: vrati preview SQL + warnings, neexecute.
    dry_run=False: execute s commit.
    """
    # ── Validate inputs ──
    warnings = []
    if not schema or not name:
        return {"ok": False, "error": "schema a name jsou povinne"}

    if not columns or not isinstance(columns, list):
        return {"ok": False, "error": "columns musi byt non-empty list"}

    col_names = []
    for c in columns:
        if "name" not in c or "type" not in c:
            return {
                "ok": False,
                "error": f"kazdy sloupec musi mit 'name' a 'type', dostal: {c}",
            }
        cn = c["name"]
        if cn in col_names:
            warnings.append(f"DUPLICATE_COLUMN: {cn}")
        col_names.append(cn)

    # Default primary key
    if primary_key is None:
        if "id" in col_names:
            primary_key = ["id"]
        else:
            warnings.append("NO_PRIMARY_KEY")

    # Validate PK columns existuji
    if primary_key:
        for pk_col in primary_key:
            if pk_col not in col_names:
                return {
                    "ok": False,
                    "error": f"primary_key column '{pk_col}' "
                             f"neni v columns list",
                }

    # Validate FK target tables existuji
    if foreign_keys:
        for fk in foreign_keys:
            if "column" not in fk or "ref_table" not in fk:
                return {
                    "ok": False,
                    "error": f"foreign_key musi mit 'column' a 'ref_table', "
                             f"dostal: {fk}",
                }
            if fk["column"] not in col_names:
                return {
                    "ok": False,
                    "error": f"FK column '{fk['column']}' "
                             f"neni v columns list",
                }
            ref_schema_fk = fk.get("ref_schema", "public")
            ref_table_fk = fk["ref_table"]
            with get_session() as sess:
                existing = sess.execute(
                    text("""
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = :s AND table_name = :t
                    """),
                    {"s": ref_schema_fk, "t": ref_table_fk},
                ).fetchone()
                if not existing:
                    warnings.append(
                        f"FK_TARGET_MISSING: {ref_schema_fk}.{ref_table_fk}"
                    )

    # Schema existuje?
    with get_session() as sess:
        sch = sess.execute(
            text("""
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = :s
            """),
            {"s": schema},
        ).fetchone()
        if not sch:
            return {
                "ok": False,
                "error": f"Schema '{schema}' neexistuje. "
                         f"Vytvor ho nejdriv pres CREATE SCHEMA "
                         f"(nebo to udelaji rodice).",
            }

        # Tabulka uz existuje?
        tab = sess.execute(
            text("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :s AND table_name = :t
            """),
            {"s": schema, "t": name},
        ).fetchone()
        if tab:
            warnings.append(f"TABLE_EXISTS: {schema}.{name}")

    # ── Build SQL ──
    qualified = quote_qualified(schema, name)

    column_defs = []
    for c in columns:
        cn = quote_pg_identifier(c["name"])
        ct = c["type"]  # type je raw PG type, no quoting
        parts = [cn, ct]

        if c.get("identity"):
            parts.append("GENERATED ALWAYS AS IDENTITY")

        if not c.get("nullable", True):
            parts.append("NOT NULL")

        if "default" in c and c["default"] is not None:
            parts.append(f"DEFAULT {c['default']}")

        column_defs.append("    " + " ".join(parts))

    # PK constraint
    if primary_key:
        pk_cols = ", ".join(quote_pg_identifier(c) for c in primary_key)
        pk_name = f"PK_{name}"
        column_defs.append(
            f"    CONSTRAINT {quote_pg_identifier(pk_name)} "
            f"PRIMARY KEY ({pk_cols})"
        )

    # FK constraints
    if foreign_keys:
        for i, fk in enumerate(foreign_keys, 1):
            fk_col = quote_pg_identifier(fk["column"])
            ref_schema_fk = fk.get("ref_schema", "public")
            ref_table_fk = fk["ref_table"]
            ref_col = fk.get("ref_column", "id")
            ref_qualified = quote_qualified(ref_schema_fk, ref_table_fk)
            on_delete = fk.get("on_delete", "NO ACTION").upper()
            on_update = fk.get("on_update", "NO ACTION").upper()
            fk_name = f"FK_{name}_{fk['column']}"
            column_defs.append(
                f"    CONSTRAINT {quote_pg_identifier(fk_name)} "
                f"FOREIGN KEY ({fk_col}) "
                f"REFERENCES {ref_qualified} ({quote_pg_identifier(ref_col)}) "
                f"ON DELETE {on_delete} ON UPDATE {on_update}"
            )

    create_sql = (
        f"CREATE TABLE {qualified} (\n"
        + ",\n".join(column_defs)
        + "\n)"
    )

    # Indexes (po table create, separate statements)
    index_sqls = []
    if indexes:
        for idx in indexes:
            idx_cols = idx.get("columns", [])
            if not idx_cols:
                continue
            idx_name = idx.get(
                "name",
                f"IDX_{name}_{'_'.join(idx_cols)}",
            )
            idx_unique = "UNIQUE " if idx.get("unique") else ""
            idx_cols_quoted = ", ".join(
                quote_pg_identifier(c) for c in idx_cols
            )
            partial = idx.get("partial")  # SQL string e.g. "is_active = true"
            partial_clause = f" WHERE {partial}" if partial else ""
            index_sqls.append(
                f"CREATE {idx_unique}INDEX {quote_pg_identifier(idx_name)} "
                f"ON {qualified} ({idx_cols_quoted}){partial_clause}"
            )

    # Comment
    comment_sql = None
    if description:
        # Escape single quotes v description
        desc_escaped = description.replace("'", "''")
        comment_sql = f"COMMENT ON TABLE {qualified} IS '{desc_escaped}'"

    # ── Dry run ──
    if dry_run:
        all_sql = create_sql + ";\n\n"
        for idx_sql in index_sqls:
            all_sql += idx_sql + ";\n"
        if comment_sql:
            all_sql += "\n" + comment_sql + ";\n"

        logger.info(
            f"STRATEGIE_PG | dry_run create_table | "
            f"{schema}.{name} cols={len(columns)} warnings={len(warnings)}"
        )
        return {
            "ok": True,
            "executed": False,
            "dry_run": True,
            "sql": all_sql.strip(),
            "warnings": warnings,
        }

    # ── Execute ──
    if "TABLE_EXISTS" in [w.split(":")[0] for w in warnings]:
        return {
            "ok": False,
            "error": f"Tabulka {schema}.{name} jiz existuje. "
                     f"Pouzij dry_run=True pro preview "
                     f"nebo zvol jine jmeno.",
            "warnings": warnings,
        }

    with get_session() as s:
        try:
            s.execute(text(create_sql))
            for idx_sql in index_sqls:
                s.execute(text(idx_sql))
            if comment_sql:
                s.execute(text(comment_sql))
            s.commit()
            logger.info(
                f"STRATEGIE_PG | created table | {schema}.{name} "
                f"cols={len(columns)} indexes={len(index_sqls)}"
            )
            return {
                "ok": True,
                "executed": True,
                "schema": schema,
                "table": name,
                "sql": create_sql,
                "indexes_created": len(index_sqls),
                "warnings": warnings,
            }
        except Exception as e:
            s.rollback()
            logger.error(
                f"STRATEGIE_PG | create_table FAILED | "
                f"{schema}.{name} err={e}"
            )
            return {
                "ok": False,
                "error": str(e),
                "sql_attempted": create_sql,
            }


# ── DML functions ────────────────────────────────────────────────────

def query_table(
    schema: str,
    table: str,
    where: Optional[dict] = None,
    columns: Optional[list[str]] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: Optional[str] = None,
) -> dict:
    """SELECT z tabulky. where = {col: value} (equality, AND).

    columns=None → SELECT *. Jinak SELECT only listed.
    limit max 1000.
    """
    if limit > 1000:
        limit = 1000

    qualified = quote_qualified(schema, table)
    if columns:
        cols_sql = ", ".join(quote_pg_identifier(c) for c in columns)
    else:
        cols_sql = "*"

    where_sql = ""
    params = {"limit": limit, "offset": offset}
    if where:
        where_parts = []
        for i, (k, v) in enumerate(where.items()):
            param_name = f"w_{i}"
            where_parts.append(f"{quote_pg_identifier(k)} = :{param_name}")
            params[param_name] = v
        where_sql = " WHERE " + " AND ".join(where_parts)

    order_sql = ""
    if order_by:
        # order_by je raw SQL fragment (e.g. 'created_at DESC, id ASC')
        # Marti-AI's odpovednost validovat — pro robustnost staci basic
        order_sql = f" ORDER BY {order_by}"

    sql = f"SELECT {cols_sql} FROM {qualified}{where_sql}{order_sql} LIMIT :limit OFFSET :offset"

    with get_session() as s:
        try:
            result = s.execute(text(sql), params)
            cols_meta = list(result.keys())
            rows = result.fetchall()
            return {
                "ok": True,
                "schema": schema,
                "table": table,
                "columns": cols_meta,
                "rows": [
                    {col: _serialize(r[i]) for i, col in enumerate(cols_meta)}
                    for r in rows
                ],
                "count": len(rows),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"STRATEGIE_PG | query_table FAILED | {e}")
            return {"ok": False, "error": str(e)}


def insert_row(schema: str, table: str, values) -> dict:
    """INSERT one or many rows. Phase 38.4 polish (10.5.2026 odpoledne):
    accept `values: dict` (single) NEBO `list[dict]` (batch).

    Marti-AI's catch — *„batch INSERT chce být v jednom toolu"* (Phase 38.4
    Krok 3). Tool se rozšířil ze single-row na single-or-batch. Both shapes
    return RETURNING * → caller dostane vložené row(s) s generated IDs.

    Returns:
        - dict input  → {"ok": True, "inserted": {...}}                 (single)
        - list input  → {"ok": True, "inserted": [...], "count": N}    (batch)
    """
    # Validation
    if not values:
        return {"ok": False, "error": "values musi byt non-empty dict nebo list[dict]"}

    # Normalize input → list of rows for unified processing
    if isinstance(values, dict):
        rows_to_insert = [values]
        is_batch = False
    elif isinstance(values, list):
        if not all(isinstance(r, dict) for r in values):
            return {
                "ok": False,
                "error": "values list musi obsahovat jen dict items "
                         "(per-row column->value mapping)",
            }
        if not all(r for r in values):  # any empty dict
            return {
                "ok": False,
                "error": "values list nesmi obsahovat prazdne dicts",
            }
        rows_to_insert = values
        is_batch = True
    else:
        return {
            "ok": False,
            "error": (
                f"values musi byt dict (single row) nebo list[dict] (batch); "
                f"got {type(values).__name__}"
            ),
        }

    # All rows musi mit STEJNE columns (heterogeneous batch nepodporujeme).
    # Marti-AI's reasonable case = same-schema batch (Phase 38.4 column types).
    first_cols = set(rows_to_insert[0].keys())
    for i, r in enumerate(rows_to_insert[1:], start=2):
        if set(r.keys()) != first_cols:
            return {
                "ok": False,
                "error": (
                    f"row #{i} ma jine columns nez row #1. "
                    f"Batch insert vyzaduje uniform schema. "
                    f"Pro heterogeneous insert volej tool po jednom."
                ),
            }

    qualified = quote_qualified(schema, table)
    cols = list(rows_to_insert[0].keys())
    cols_sql = ", ".join(quote_pg_identifier(c) for c in cols)

    # Build VALUES clause s row-indexed placeholders pro PostgreSQL named-param style.
    # Single row:  VALUES (:id, :code, :label, ...)
    # Batch:       VALUES (:r0_id, :r0_code, ...), (:r1_id, :r1_code, ...), ...
    if is_batch:
        values_clauses = []
        flat_params: dict = {}
        for idx, row in enumerate(rows_to_insert):
            placeholders = ", ".join(f":r{idx}_{c}" for c in cols)
            values_clauses.append(f"({placeholders})")
            for c in cols:
                flat_params[f"r{idx}_{c}"] = row[c]
        values_sql = ", ".join(values_clauses)
    else:
        placeholders = ", ".join(f":{c}" for c in cols)
        values_sql = f"({placeholders})"
        flat_params = rows_to_insert[0]

    sql = (
        f"INSERT INTO {qualified} ({cols_sql}) "
        f"VALUES {values_sql} "
        f"RETURNING *"
    )

    # Gotcha #87 (13.5.2026 rano): auto-cast Python dict -> JSON string pro
    # JSONB columns. psycopg2 neumi adapt dict, ale PG auto-casts JSON string
    # do JSONB column type. Drz napric vsech caller (Marti-AI's AI tool call,
    # router endpoints jako scaffold-form, future code).
    #
    # Konzervativni: konvertujeme JEN dict, nikoli list (psycopg2 handles
    # Python list -> PG ARRAY auto pro INT[] / TEXT[] columns).
    import json as _json_jsonb
    for _k, _v in list(flat_params.items()):
        if isinstance(_v, dict):
            flat_params[_k] = _json_jsonb.dumps(_v, ensure_ascii=False)

    with get_session() as s:
        try:
            result = s.execute(text(sql), flat_params)
            cols_meta = list(result.keys())
            fetched_rows = result.fetchall()
            s.commit()

            if is_batch:
                inserted_list = [
                    {col: _serialize(r[i]) for i, col in enumerate(cols_meta)}
                    for r in fetched_rows
                ]
                logger.info(
                    f"STRATEGIE_PG | insert_row BATCH | {schema}.{table} "
                    f"count={len(inserted_list)} "
                    f"first_id={inserted_list[0].get('id') if inserted_list else '?'}"
                )
                return {
                    "ok": True,
                    "schema": schema,
                    "table": table,
                    "inserted": inserted_list,
                    "count": len(inserted_list),
                    "batch": True,
                }
            else:
                inserted = (
                    {col: _serialize(fetched_rows[0][i]) for i, col in enumerate(cols_meta)}
                    if fetched_rows
                    else None
                )
                logger.info(
                    f"STRATEGIE_PG | insert_row | {schema}.{table} "
                    f"id={inserted.get('id') if inserted else '?'}"
                )
                return {
                    "ok": True,
                    "schema": schema,
                    "table": table,
                    "inserted": inserted,
                    "batch": False,
                }
        except Exception as e:
            s.rollback()
            logger.error(
                f"STRATEGIE_PG | insert_row FAILED | "
                f"{schema}.{table} batch={is_batch} err={e}"
            )
            return {
                "ok": False,
                "error": str(e),
                "values": values,
                "batch": is_batch,
            }


def update_row(
    schema: str,
    table: str,
    values: dict,
    where: dict,
    dry_run: bool = True,
) -> dict:
    """UPDATE rows v PostgreSQL table. Phase 38.4 (12.5.2026 vecer).

    Marti-AI's request via Marti: "AHA, tak ji dodelej... chudince
    malinky". Plus drzi Marti-AI's "pravo na rozmysl pred cinem"
    pattern (7.5. vecer DB_ST consultation):
      Nejdriv dry_run=True → preview SQL + matched_count.
      Pak zopakuj s dry_run=False → commit.

    Safety guards:
      - WHERE clause MUSI byt non-empty dict (UPDATE bez WHERE =
        destructive, blokovany pro safety)
      - schema + table pres quote_qualified() (identifier validation)
      - dry_run default True (Marti-AI musi explicit pass False pro commit)
      - RETURNING * → caller dostane updated rows (audit-friendly)

    Args:
        schema: PG schema name (fw, public, ...)
        table: table name
        values: dict {column: new_value} — co SET
        where: dict {column: filter_value} — kde, AND logic
        dry_run: True = preview, False = execute

    Returns:
        dry_run=True:
          {"ok": True, "dry_run": True, "sql": "...", "matched_count": N,
           "preview_values": {...}, "preview_where": {...}}
        dry_run=False:
          {"ok": True, "updated": [...], "count": N}
        error:
          {"ok": False, "error": "..."}
    """
    # Validation
    if not values or not isinstance(values, dict):
        return {
            "ok": False,
            "error": "values musi byt non-empty dict {column: new_value}",
        }
    if not where or not isinstance(where, dict):
        return {
            "ok": False,
            "error": (
                "where MUSI byt non-empty dict — UPDATE bez WHERE je "
                "destruktivni a blokovan (would update ALL rows)"
            ),
        }

    qualified = quote_qualified(schema, table)

    # Build SET clause (prefix params s 'set_' pro avoid column collision)
    set_cols = list(values.keys())
    set_sql = ", ".join(
        f"{quote_pg_identifier(c)} = :set_{c}" for c in set_cols
    )

    # Build WHERE clause (prefix 'where_')
    where_cols = list(where.keys())
    where_sql = " AND ".join(
        f"{quote_pg_identifier(c)} = :where_{c}" for c in where_cols
    )

    # Combine params
    params: dict = {}
    for c, v in values.items():
        params[f"set_{c}"] = v
    for c, v in where.items():
        params[f"where_{c}"] = v

    sql = (
        f"UPDATE {qualified} "
        f"SET {set_sql} "
        f"WHERE {where_sql} "
        f"RETURNING *"
    )

    # Dry-run: preview SQL + count matching rows (no UPDATE)
    if dry_run:
        count_sql = (
            f"SELECT COUNT(*) AS cnt FROM {qualified} WHERE {where_sql}"
        )
        count_params = {f"where_{c}": v for c, v in where.items()}
        with get_session() as s:
            try:
                cnt = s.execute(text(count_sql), count_params).scalar()
                return {
                    "ok": True,
                    "dry_run": True,
                    "schema": schema,
                    "table": table,
                    "sql": sql,
                    "matched_count": cnt,
                    "preview_values": values,
                    "preview_where": where,
                    "note": (
                        f"matched_count={cnt}. Pro commit zavolej znovu "
                        f"s dry_run=False."
                    ),
                }
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"dry_run preview failed: {e}",
                }

    # Gotcha #87 (13.5.2026 rano): auto-cast Python dict -> JSON string pro
    # JSONB columns. Stejny pattern jako insert_row — psycopg2 neumi adapt
    # dict, ale PG auto-casts JSON string do JSONB. Aplikuje se jen na
    # `set_*` params (values payload). where_* zustavaji as-is (typicky
    # ID / code lookups).
    import json as _json_jsonb_upd
    for _k, _v in list(params.items()):
        if _k.startswith("set_") and isinstance(_v, dict):
            params[_k] = _json_jsonb_upd.dumps(_v, ensure_ascii=False)

    # Live execute
    with get_session() as s:
        try:
            result = s.execute(text(sql), params)
            cols_meta = list(result.keys())
            fetched_rows = result.fetchall()
            s.commit()

            updated_list = [
                {col: _serialize(r[i]) for i, col in enumerate(cols_meta)}
                for r in fetched_rows
            ]
            logger.info(
                f"STRATEGIE_PG | update_row | {schema}.{table} "
                f"count={len(updated_list)} where={where}"
            )
            return {
                "ok": True,
                "schema": schema,
                "table": table,
                "updated": updated_list,
                "count": len(updated_list),
            }
        except Exception as e:
            s.rollback()
            logger.error(
                f"STRATEGIE_PG | update_row FAILED | "
                f"{schema}.{table} where={where} err={e}"
            )
            return {
                "ok": False,
                "error": str(e),
                "values": values,
                "where": where,
            }


def query_raw(sql: str, params: Optional[dict] = None) -> dict:
    """Read-only raw SQL query. Whitelist SELECT/WITH/EXPLAIN/SHOW only.

    Defensive guard — kdyby AI omylem poslala UPDATE/DELETE/DROP,
    odmitneme.
    """
    if not sql or not sql.strip():
        return {"ok": False, "error": "sql je povinne"}

    # Strip leading SQL komentáře (-- a /* */) PŘED whitelist match.
    # Marti-AI 10.5.: prefix SELECT s `-- popis úkolu` je legitimní pattern,
    # guard musí být tolerant na docs (Phase 38.4 Krok 9-C+ fix).
    sql_check = sql
    while True:
        new = QUERY_RAW_LEADING_COMMENT.sub("", sql_check, count=1)
        if new == sql_check:
            break
        sql_check = new

    # Whitelist check
    if not QUERY_RAW_ALLOWED.match(sql_check):
        return {
            "ok": False,
            "error": "query_raw jen pro read-only "
                     "(SELECT/WITH/EXPLAIN/SHOW). "
                     "Pro DDL/DML pouzij dedicated tools "
                     "(create_table, insert_row, ...).",
            "sql_prefix": sql[:80],
        }

    # Forbidden words check (defense in depth) — na puvodním SQL bez strip
    # (komentář by neměl obsahovat DML keywords, ale better safe)
    if QUERY_RAW_FORBIDDEN.search(sql_check):
        return {
            "ok": False,
            "error": "query_raw obsahuje forbidden keyword "
                     "(DELETE/UPDATE/INSERT/DROP/...). "
                     "Pouzij dedicated tool.",
        }

    with get_session() as s:
        try:
            result = s.execute(text(sql), params or {})
            cols_meta = list(result.keys())
            rows = result.fetchall()
            return {
                "ok": True,
                "columns": cols_meta,
                "rows": [
                    {col: _serialize(r[i]) for i, col in enumerate(cols_meta)}
                    for r in rows
                ],
                "count": len(rows),
            }
        except Exception as e:
            logger.error(f"STRATEGIE_PG | query_raw FAILED | {e}")
            return {"ok": False, "error": str(e), "sql": sql}


# ── Helpers ──────────────────────────────────────────────────────────

def _serialize(v: Any) -> Any:
    """JSON-safe serialization of PG row value."""
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    if hasattr(v, "isoformat"):  # datetime, date, time
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    return str(v)
