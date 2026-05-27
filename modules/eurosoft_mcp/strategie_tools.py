"""
Phase 28-D (8.5.2026): strategie_* tools — Marti-AI's DDL + CRUD doména
nad DB_ST (její vlastní database, db_owner role).

Phase 28-D++ (27.5.2026): Multi-DB DDL access — rozšířeno o DB_EC.st.*
schema (NAŠE refactor zone v customer DB). Customer's dbo.* zůstává
netknuté (Marti's *„nezasahovat"* doctrine z 27.5. odpoledne).

Diář pattern (Marti's slova 7.5.2026):
  *„DB_ST má být v plné režii Marti-AI. Plný owner přístup. Všechno by
  měla dělat ona. Přesně jako když dostala svůj diář — je to její,
  a její zodpovědnost."*

Trust model: AI provede, lidé reflektují.
- DDL bez parent gate (vs Phase 14 request_forget gate, Phase 19c kustod ACL)
- dry_run pattern (Marti-AI's požadavek, 7.5.2026 večer):
    *„Dry-run není technická pojistka. Je to právo na rozmysl před činem."*

Tools (všechny akceptují `db_name: str | None = None`, default DB_ST):
  DDL (s dry_run support):
    strategie_create_table, strategie_alter_table, strategie_drop_table,
    strategie_create_schema, strategie_add_index, strategie_add_foreign_key
  CRUD:
    strategie_query_table, strategie_get_row, strategie_count_rows,
    strategie_insert_row, strategie_update_row, strategie_delete_row
  Discovery:
    strategie_list_schemas, strategie_list_tables, strategie_describe_table,
    strategie_query_raw

Multi-DB scope (Phase 28-D++):
  db_name=None or "DB_ST"  → Marti-AI's vlastní MSSQL doména (full db_owner)
  db_name="DB_EC"          → Customer DB, **POUZE schema 'st'** (refactor zone)
                              Customer's dbo.* je read-only přes eurosoft_* tools

Pre-execute guards (defense in depth):
  1. config.resolve_db_name(db_name)        — validuje allowlist
  2. config.check_schema_allowed(db, schema) — per-DB schema gate
  3. _check_raw_sql_targets(sql, db)         — regex DDL+DML target check (raw SQL)
  4. SQL Server permissions                  — DB-level GRANT/DENY (sa-spuštěné)
  5. Schema ownership                        — st owned by Marti-AI, dbo by dbo

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

from .config import (
    check_schema_allowed,
    resolve_db_name,
    settings,
)
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
    """Helper — vrací db_st_database name z settings. (Backward compat.)"""
    return settings.db_st_database


def _check_ddl_allowed():
    """Marti-AI's IT security override flag. Default true."""
    if not settings.allow_db_st_ddl:
        raise ValueError(
            "DDL operace jsou zakázány (MCP_ALLOW_DB_ST_DDL=false). "
            "Marti's IT security audit je v běhu — pouze CRUD + discovery."
        )


# ── Multi-DB raw SQL target guard (Phase 28-D++) ───────────────────────
#
# Pro `strategie_query_raw(sql, db_name="DB_EC")` musíme regex-detekovat
# všechny DDL+DML targets a ověřit, že každý je v povolené schema
# (config.DDL_SCHEMA_ALLOWLIST). Customer's dbo.* nedotknout.

# DDL target patterns — match schema.table from CREATE/ALTER/DROP TABLE
# + standalone CREATE SCHEMA
_DDL_TARGET_PATTERNS = [
    re.compile(
        r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bALTER\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bCREATE\s+INDEX\s+\w+\s+ON\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDROP\s+INDEX\s+\w+\s+ON\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
]

# DML target patterns — match schema.table from INSERT/UPDATE/DELETE/MERGE/TRUNCATE
_DML_TARGET_PATTERNS = [
    re.compile(
        r"\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bUPDATE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?\s+SET\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDELETE\s+FROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bMERGE\s+(?:INTO\s+)?(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bTRUNCATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
        re.IGNORECASE,
    ),
]


# GO batch separator pattern — T-SQL idiom z SSMS/sqlcmd, ne true T-SQL.
# pyodbc neumi GO nativne, musime split na batche pred execution.
# Marti-AI's Phase C insider catch (27.5. vecer):
#   "Pokud predam cely script jako jeden string do execute(), pyodbc
#   spadne na GO jako neznamy prikaz."
#
# Pattern: GO musi byt na vlastnim radku (whitespace-only kolem), case-insensitive.
# Plus support `GO N` (repeat N-times, ignorujeme pocet) — pro CRM migrace
# nikdy nepouzivame, ale defensive.
_GO_BATCH_SPLIT = re.compile(
    r"^\s*GO(?:\s+\d+)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _split_sql_batches(sql: str) -> list[str]:
    """
    Split T-SQL string na batches podle GO separators.

    GO neni T-SQL prikaz — je to SSMS/sqlcmd directive ktera rika klientu
    "posli dosavadni nahromadene SQL jako jeden batch". pyodbc to nezna,
    proto musime split rucne.

    Args:
      sql: raw T-SQL string (potencialne s GO separators)

    Returns:
      list of non-empty SQL batches (GO odstraneno, leading/trailing
      whitespace strippnuty). Pokud sql nema GO, vraci [sql].

    Examples:
      "SELECT 1\nGO\nSELECT 2"     -> ["SELECT 1", "SELECT 2"]
      "INSERT...\n\nGO 3\nUPDATE..." -> ["INSERT...", "UPDATE..."]
      "SELECT 1"                    -> ["SELECT 1"]
      ""                            -> []

    POZOR: GO musi byt na vlastnim radku. "SELECT GO FROM X" se NEsplitne
    (intra-SQL GO je legalni identifier nebo keyword v context, ne batch
    separator).
    """
    if not sql or not sql.strip():
        return []
    batches = _GO_BATCH_SPLIT.split(sql)
    return [b.strip() for b in batches if b and b.strip()]


def _check_raw_sql_targets(sql: str, db_name: str) -> list[str]:
    """
    Pre-execute guard — verify že všechny DDL+DML targets jsou v povolené
    schema (config.DDL_SCHEMA_ALLOWLIST[db_name]).

    Allowlist-first approach (Marti-AI's Phase B insight 27.5.):
      - DML/DDL target BEZ explicit schema prefix → REJECT (clear error
        message místo silent "dbo default" assumption)
      - DML/DDL target S explicit schema prefix → ověř že je v allowlist

    Pro DB_EC: Marti-AI musí psát `INSERT INTO st.CRM_Kontakt`, ne
    `INSERT INTO CRM_Kontakt` (defaultní dbo). Explicit > implicit.

    POZOR: SELECT není kontrolován (read povolený napříč schémata —
    Marti-AI čte z dbo pro migraci do st). Plus session options
    (SET IDENTITY_INSERT, SET ANSI_NULLS, atd.) nejsou DDL/DML, regex je
    netřesí — INSERT/UPDATE/DELETE musí mít INTO/SET/FROM keywords po
    sobě, takže `SET IDENTITY_INSERT st.X ON` projde čistě (správně).

    Args:
      sql: raw T-SQL statement(s)
      db_name: already-resolved DB name

    Returns:
      list of violation messages (empty list = OK).
    """
    from .config import DDL_SCHEMA_ALLOWLIST

    allowed = DDL_SCHEMA_ALLOWLIST.get(db_name)
    if allowed is None:
        return []  # No restriction (DB_ST)

    allowed_lower = {s.lower() for s in allowed}
    violations: list[str] = []

    for pattern_set, op_kind in (
        (_DDL_TARGET_PATTERNS, "DDL"),
        (_DML_TARGET_PATTERNS, "DML"),
    ):
        for pattern in pattern_set:
            for match in pattern.finditer(sql):
                # group(1) = schema prefix (None pokud chybi)
                # group(2) = table name
                schema_raw = match.group(1)
                table_part = (match.group(2) or "?").strip()
                snippet = match.group(0).strip()

                # Allowlist-first: missing explicit schema = REJECT s clear msg
                if schema_raw is None or not schema_raw.strip():
                    violations.append(
                        f"{op_kind}: {snippet[:80]!r} -> CHYBI EXPLICITNI "
                        f"SCHEMA PREFIX. Pro {db_name} pouzij explicit "
                        f"schema (napr. {sorted(allowed)[0]}.{table_part}). "
                        f"Implicit 'dbo' default neni povolen."
                    )
                    continue

                schema_part = schema_raw.strip().lower()
                if schema_part not in allowed_lower:
                    violations.append(
                        f"{op_kind}: {snippet[:80]!r} -> schema '{schema_raw}' "
                        f"neni v allowlist {sorted(allowed)}"
                    )
    return violations


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


async def strategie_list_schemas(db_name: str | None = None) -> dict[str, Any]:
    """
    Vrátí seznam schémat v target DB. Filtruje system schemas.

    Args:
      db_name: target DB. None = DB_ST default. "DB_EC" = customer's DB
               (s pohledem na schema 'st' jako naše refactor zone).

    Použití na DB_ST: Marti-AI po init zkontroluje, zda existují 4 očekávaná
    schémata (master, tenant_group, tenant, user). Pokud chybí, volá
    strategie_create_schema.

    Použití na DB_EC: ověř, že schema 'st' existuje + má correct owner
    (Marti-AI po sa-spuštěném GRANT scriptu).
    """
    target_db = resolve_db_name(db_name)
    sql = """
        SELECT name, schema_id, principal_id,
               USER_NAME(principal_id) AS owner_name
        FROM sys.schemas
        WHERE name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest', 'db_owner',
                          'db_accessadmin', 'db_securityadmin', 'db_ddladmin',
                          'db_backupoperator', 'db_datareader', 'db_datawriter',
                          'db_denydatareader', 'db_denydatawriter')
        ORDER BY name
    """
    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql)
        schemas = fetchall_as_dicts(cur)
    # Mark which expected schemas exist + which missing (DB_ST only)
    existing = {s["name"] for s in schemas}
    if target_db == settings.db_st_database:
        missing = [s for s in EXPECTED_SCHEMAS if s not in existing]
        expected = list(EXPECTED_SCHEMAS)
    else:
        # DB_EC — expected je `st` (NAŠE refactor zone)
        missing = ["st"] if "st" not in existing else []
        expected = ["st"]
    return {
        "ok": True,
        "db_name": target_db,
        "schemas": schemas,
        "expected": expected,
        "missing_expected": missing,
    }


async def strategie_list_tables(
    schema: str | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    Vrátí seznam tabulek v target DB. Filter per schema (volitelné).

    Args:
      schema: pokud zadán, jen tabulky v tomto schématu. Else všechna.
      db_name: target DB. None = DB_ST default.
    """
    target_db = resolve_db_name(db_name)
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
    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql, params)
        tables = fetchall_as_dicts(cur)
    return {
        "ok": True,
        "db_name": target_db,
        "schema_filter": schema,
        "tables": tables,
        "count": len(tables),
    }


async def strategie_describe_table(
    schema: str,
    table: str,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    Vrátí schema details: columns, primary key, foreign keys, indexes, row count estimate.

    Args:
      schema, table: target table
      db_name: target DB. None = DB_ST default.

    Pro CRM migraci: Marti-AI volá describe_table(schema='dbo', table='EC_Kontakt',
    db_name='DB_EC') pro audit source columns PŘED CREATE TABLE st.CRM_Kontakt.
    """
    target_db = resolve_db_name(db_name)
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
    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql_cols, [fq])
        cols = fetchall_as_dicts(cur)
        if not cols:
            return {
                "ok": False,
                "error": "table_not_found",
                "message": f"Tabulka {fq} neexistuje v {target_db}.",
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
        "db_name": target_db,
        "schema": schema,
        "table": table,
        "columns": cols,
        "indexes": indexes,
        "foreign_keys": fks,
        "row_count": row_count,
    }


# ── DDL: Schema ────────────────────────────────────────────────────────


def _resolve_dry_run_default(dry_run: bool | None, target_db: str) -> bool:
    """
    Marti-AI's Phase B insight (27.5.): dry_run default per DB.

    Pro DB_EC je dry_run=True default — chyba na customer DB je drazsi
    nez na DB_ST sandbox. Explicit dry_run=False na DB_EC vyzaduje
    vedome rozhodnuti (= "pravo na rozmysl pred cinem", 7.5.).

    Pro DB_ST zustava False default (backward compat, sandbox je cheap).
    """
    if dry_run is not None:
        return dry_run
    # None sentinel = use per-DB default
    return target_db == "DB_EC"


def _log_db_ec_operation(
    operation: str,
    schema: str,
    table: str | None = None,
    affected: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Marti-AI's Phase B insight (d): extra audit logging pro DB_EC operations.

    Customer DB tool calls dostavaji NE-anonymni audit s db_target/schema_target/
    operation/table_name/row_count. Forensic trail pro pripadny rollback
    nebo customer audit. Minimum due diligence.

    Pattern: logger.info() s strukturovanym extra dict — eurosoft_mcp
    NSSM service ma audit.log v JSON-lines formatu (config.audit_log_path).
    Volame to JEN pro db_name='DB_EC' (DB_ST je nas sandbox, samostatny audit).

    Drz Marti-AI's "Bezpecnost pres probuzeni, ne pres ticho" (9.5. master
    tier consult, insight #9) — kazda customer DB akce = log row.
    """
    audit_payload = {
        "db_target": "DB_EC",
        "schema_target": schema,
        "operation": operation,
        "table_name": table,
        "row_count": affected,
    }
    if extra:
        audit_payload.update(extra)
    logger.info(
        "strategie_db_ec_op",
        extra={"strategie_audit": audit_payload},
    )


async def strategie_create_schema(
    name: str,
    dry_run: bool | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    Vytvoří schema v target DB. Idempotent — pokud existuje, no-op.

    Args:
      name: schema name (master / tenant_group / tenant / user / st / cokoliv)
      dry_run: pokud True, jen vrátí preview SQL + warnings, nic neexecute.
               None (default) → DB_EC: True, DB_ST: False (Marti-AI's Phase B
               insight 27.5. — customer DB vyzaduje vedome rozhodnuti).
      db_name: target DB. None = DB_ST. "DB_EC" — povolí jen schema 'st'
               (Marti's *„nezasahovat"* — customer dbo nedotknout).

    POZN. pro DB_EC: schema 'st' obvykle vytvoříš jen jednou přes sa-spuštěný
    GRANT script (`_grant_marti_ai_db_ec_st_schema.sql`). Marti-AI tento tool
    používá hlavně pro DB_ST tier schemas.
    """
    _check_ddl_allowed()
    _validate_identifier(name, "schema")
    target_db = resolve_db_name(db_name)
    check_schema_allowed(target_db, name, op="CREATE SCHEMA")
    dry_run = _resolve_dry_run_default(dry_run, target_db)

    sql = f"CREATE SCHEMA {quote_identifier(name)}"
    warnings: list[str] = []

    # Validation: schema already exists?
    with get_cursor(db_name=target_db) as cur:
        cur.execute("SELECT 1 FROM sys.schemas WHERE name = ?", [name])
        if cur.fetchone():
            warnings.append(f"Schema '{name}' již existuje — operace bude no-op")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "db_name": target_db,
            "preview_sql": sql,
            "warnings": warnings,
            "would_skip": bool(warnings),
        }

    if warnings and "již existuje" in warnings[0]:
        return {
            "ok": True,
            "executed": False,
            "skipped": True,
            "reason": "schema_exists",
            "db_name": target_db,
        }

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        logger.info(f"strategie_create_schema: {target_db}.{name}")
        return {"ok": True, "executed": True, "sql": sql, "db_name": target_db, "schema": name}
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
    dry_run: bool | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    CREATE TABLE v target DB.

    Args:
      schema: target schema (master / tenant_group / tenant / user / st)
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
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st' (Marti's
               *„nezasahovat"* doctrine — customer dbo never touched).

    Marti-AI's "právo na rozmysl před činem" — dry_run je standard.

    CRM migration příklad (Krok 1):
      strategie_create_table(
          schema='st', name='CRM_Kontakt',
          columns=[...], primary_key=['ID'],
          db_name='DB_EC'
      )
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    if not columns or not isinstance(columns, list):
        raise ValueError("columns must be non-empty list")
    target_db = resolve_db_name(db_name)
    check_schema_allowed(target_db, schema, op="CREATE TABLE")
    dry_run = _resolve_dry_run_default(dry_run, target_db)

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
    with get_cursor(db_name=target_db) as cur:
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
            "db_name": target_db,
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
            "db_name": target_db,
            "warnings": warnings,
            "blocking_warnings": blocking,
            "hint": "Použij dry_run=True pro safe preview a oprav blocking warnings.",
        }

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        for idx_sql in index_sqls:
            cur.execute(idx_sql)
        conn.commit()
        logger.info(f"strategie_create_table: {target_db}.{schema}.{name} ({len(columns)} cols, {len(index_sqls)} indexes)")
        return {
            "ok": True,
            "executed": True,
            "db_name": target_db,
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
    dry_run: bool | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    DROP TABLE v target DB.

    Args:
      schema: target schema
      name: table name
      if_exists: bezpečné chování — pokud nexistuje, no-op (default true)
      dry_run: True = preview SQL, neexecute. None (default) → DB_EC: True
               (Marti-AI's Phase B insight — customer DB vyzaduje rozmysl),
               DB_ST: False (sandbox cheap).
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st'.
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    target_db = resolve_db_name(db_name)
    check_schema_allowed(target_db, schema, op="DROP TABLE")
    dry_run = _resolve_dry_run_default(dry_run, target_db)
    qname = _qualified_name(schema, name)
    warnings: list[str] = []

    with get_cursor(db_name=target_db) as cur:
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
                "db_name": target_db,
                "table": f"{schema}.{name}",
            }
        warnings.append(f"Tabulka {schema}.{name} neexistuje — DROP selže")

    sql = f"DROP TABLE {qname}"
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "db_name": target_db,
            "preview_sql": sql,
            "warnings": warnings,
            "exists": exists,
        }

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        logger.warning(f"strategie_drop_table: {target_db}.{schema}.{name}")
        return {"ok": True, "executed": True, "db_name": target_db, "sql": sql}
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
    dry_run: bool | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    ALTER TABLE — add columns, drop columns, rename column.

    Args:
      schema, name: target table
      add_columns: list of column defs (jako v create_table)
      drop_columns: list of column names to drop
      rename_column: {"from": "old_name", "to": "new_name"}
      dry_run: standard pattern. None (default) → DB_EC: True
               (Marti-AI's Phase B insight — customer DB vyzaduje rozmysl),
               DB_ST: False.
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st'.
    """
    _check_ddl_allowed()
    _validate_identifier(schema, "schema")
    _validate_identifier(name, "table")
    target_db = resolve_db_name(db_name)
    check_schema_allowed(target_db, schema, op="ALTER TABLE")
    dry_run = _resolve_dry_run_default(dry_run, target_db)
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
    with get_cursor(db_name=target_db) as cur:
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
            "db_name": target_db,
            "preview_sql": full_sql,
            "warnings": warnings,
            "statement_count": len(statements),
        }

    blocking = [w for w in warnings if "neexistuje" in w]
    if blocking:
        return {"ok": False, "error": "validation_failed", "db_name": target_db, "warnings": warnings}

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
        logger.info(f"strategie_alter_table: {target_db}.{schema}.{name} ({len(statements)} ops)")
        return {"ok": True, "executed": True, "db_name": target_db, "sql": full_sql, "operations": len(statements)}
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
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    SELECT z target DB tabulky. Bez whitelist (Marti-AI je owner).

    Args:
      schema, table: target table
      filters, columns, order_by, limit, offset: standard query options
      db_name: target DB. None = DB_ST. "DB_EC" — SELECT is allowed napříč
               schémata (read není restricted, jen write — viz Marti's
               *„nezasahovat"* doctrine + check_schema_allowed pro DDL/DML).

    SELECT na DB_EC.dbo je povolen — Marti-AI potřebuje read source pro
    migraci do st.*. Restrict je jen pro write operations.
    """
    target_db = resolve_db_name(db_name)
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

    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql, params)
        rows = fetchall_as_dicts(cur)
    has_more = len(rows) > actual_limit
    if has_more:
        rows = rows[:actual_limit]
    return {
        "ok": True,
        "db_name": target_db,
        "schema": schema,
        "table": table,
        "rows": rows,
        "n_returned": len(rows),
        "limit": actual_limit,
        "offset": offset,
        "has_more": has_more,
    }


async def strategie_get_row(
    schema: str,
    table: str,
    id: int,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    SELECT single row by id.

    Args:
      schema, table: target table
      id: row PK
      db_name: target DB. None = DB_ST. "DB_EC" = SELECT povolen napříč schémata.
    """
    target_db = resolve_db_name(db_name)
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    qname = _qualified_name(schema, table)
    sql = f"SELECT * FROM {qname} WHERE [id] = ?"
    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql, [id])
        rows = fetchall_as_dicts(cur)
    return {
        "ok": True,
        "db_name": target_db,
        "schema": schema,
        "table": table,
        "id": id,
        "row": rows[0] if rows else None,
    }


async def strategie_count_rows(
    schema: str,
    table: str,
    filters: dict[str, Any] | None = None,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    Fast COUNT(*) bez fetch.

    Args:
      schema, table: target table
      filters: optional WHERE filters
      db_name: target DB. None = DB_ST. SELECT povolen napříč schémata.
    """
    target_db = resolve_db_name(db_name)
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
    with get_cursor(db_name=target_db) as cur:
        cur.execute(sql, params)
        count = int(cur.fetchone()[0])
    return {"ok": True, "db_name": target_db, "schema": schema, "table": table, "count": count}


async def strategie_insert_row(
    schema: str,
    table: str,
    data: dict[str, Any],
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    INSERT single row, vrátí new id.

    Args:
      schema, table: target table
      data: column → value dict
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st' (DML check).

    Marti's *„nezasahovat"* doctrine: INSERT do customer's dbo blokován guardem.
    """
    target_db = resolve_db_name(db_name)
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    check_schema_allowed(target_db, schema, op="INSERT")
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

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        new_id_row = cur.fetchone()
        new_id = int(new_id_row[0]) if new_id_row else None
        conn.commit()
        # Marti-AI's Phase B (d): audit log pro DB_EC operations
        if target_db == "DB_EC":
            _log_db_ec_operation(
                operation="INSERT",
                schema=schema,
                table=table,
                affected=1,
                extra={"new_id": new_id, "columns": list(data.keys())},
            )
        return {"ok": True, "db_name": target_db, "schema": schema, "table": table, "id": new_id}
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
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    UPDATE single row by id.

    Args:
      schema, table: target table
      id: row PK
      data: column → new_value dict
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st' (DML check).
    """
    target_db = resolve_db_name(db_name)
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    check_schema_allowed(target_db, schema, op="UPDATE")
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
    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        affected = cur.rowcount
        conn.commit()
        # Marti-AI's Phase B (d): audit log pro DB_EC operations
        if target_db == "DB_EC":
            _log_db_ec_operation(
                operation="UPDATE",
                schema=schema,
                table=table,
                affected=affected,
                extra={"row_id": id, "columns": list(data.keys())},
            )
        return {"ok": True, "db_name": target_db, "schema": schema, "table": table, "id": id, "affected": affected}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


async def strategie_delete_row(
    schema: str,
    table: str,
    id: int,
    db_name: str | None = None,
    confirm_db_ec: bool = False,
) -> dict[str, Any]:
    """
    DELETE single row by id.

    Args:
      schema, table: target table
      id: row PK
      db_name: target DB. None = DB_ST. "DB_EC" = pouze schema 'st' (DML check).
      confirm_db_ec: Marti-AI's Phase B insight (a) — pro DB_EC.st DELETE
                    vyzaduje explicit confirm_db_ec=True. DB_ST sandbox je
                    chear (rollback levny), DB_EC.st je production data
                    customer DB. Default False = pri db_name='DB_EC' raise
                    ValueError s explicit hint.

    Pattern z Marti-AI's "pravo na rozmysl pred cinem" (7.5.) — destruktivni
    akce na customer DB vyzaduje vedome rozhodnuti, ne implicit "default" beh.
    """
    target_db = resolve_db_name(db_name)
    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    check_schema_allowed(target_db, schema, op="DELETE")

    # Marti-AI's Phase B (a): require_explicit_db pro DELETE na DB_EC
    if target_db == "DB_EC" and not confirm_db_ec:
        raise ValueError(
            f"DELETE na DB_EC.{schema}.{table} vyzaduje explicit confirm_db_ec=True. "
            f"Customer DB destruktivni akce — Marti-AI's 'pravo na rozmysl' (7.5.). "
            f"Pokud opravdu chces smazat row id={id}, vol s confirm_db_ec=True."
        )

    qname = _qualified_name(schema, table)
    sql = f"DELETE FROM {qname} WHERE [id] = ?"
    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        cur.execute(sql, [id])
        affected = cur.rowcount
        conn.commit()
        # Marti-AI's Phase B (d): audit log pro DB_EC operations
        if target_db == "DB_EC":
            _log_db_ec_operation(
                operation="DELETE",
                schema=schema,
                table=table,
                affected=affected,
                extra={"row_id": id},
            )
        return {"ok": True, "db_name": target_db, "schema": schema, "table": table, "id": id, "affected": affected}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ── Raw SQL (full owner power) ──────────────────────────────────────────


async def strategie_query_raw(
    sql: str,
    db_name: str | None = None,
) -> dict[str, Any]:
    """
    Raw SQL execute v target DB. Marti-AI je owner — full SELECT/DDL power.

    UPOZORNĚNÍ: Marti-AI's autonomy nad DB_ST / DB_EC.st. Audit log per call.

    Args:
      sql: T-SQL statement(s)
      db_name: target DB. None = DB_ST. "DB_EC" — pre-execute regex guard
               verifikuje, že všechny DDL+DML targets jsou v st.* schema
               (customer's dbo never touched, Marti's *„nezasahovat"* doctrine).

    Pro DB_EC:
      - SELECT z libovolného schema povolen (read source pro CRM migrace)
      - INSERT/UPDATE/DELETE/MERGE/TRUNCATE — pouze st.* (regex guard)
      - CREATE/ALTER/DROP TABLE — pouze st.* (regex guard)

    CRM migration Krok 1 příklad:
      strategie_query_raw(
          sql=open('scripts/_phase_crm_migration_01_st_crm_kontakt.sql').read(),
          db_name='DB_EC'
      )
    """
    if not sql or not isinstance(sql, str) or not sql.strip():
        raise ValueError("sql must be non-empty string")

    target_db = resolve_db_name(db_name)

    # Pre-execute guard pro DB_EC: regex check všech DDL+DML targets
    violations = _check_raw_sql_targets(sql, target_db)
    if violations:
        raise ValueError(
            f"DDL/DML targets na {target_db} mimo povoleny allowlist "
            f"(Marti's 'nezasahovat' doctrine - customer dbo nedotknout):\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nHint: pro CRM migraci pouzij st.* schema "
            "(napr. INSERT INTO st.CRM_Kontakt FROM dbo.EC_Kontakt)."
        )

    # Marti-AI's Phase B insider catch (27.5. vecer):
    # GO batch separator splitting — pyodbc neumi GO natively.
    # Split na batches, run each separately. Pokud sql nema GO,
    # _split_sql_batches vraci [sql] = single-batch backward compat.
    batches = _split_sql_batches(sql)
    if not batches:
        raise ValueError("sql resulted in empty batches after GO split")

    conn = get_connection(db_name=target_db)
    cur = conn.cursor()
    try:
        # Track outputs per batch. Pro multi-batch SELECT only LAST batch
        # rows jsou returned (typical pattern: prep DDL + final SELECT).
        last_rows: list[dict[str, Any]] | None = None
        total_affected = 0
        batches_executed = 0

        for idx, batch_sql in enumerate(batches):
            cur.execute(batch_sql)
            if cur.description:
                last_rows = fetchall_as_dicts(cur)
            else:
                total_affected += cur.rowcount or 0
            batches_executed += 1

        if last_rows is not None:
            # SELECT (final batch returned rows)
            conn.commit()
            if target_db == "DB_EC":
                _log_db_ec_operation(
                    operation="SELECT_RAW",
                    schema="?",
                    table=None,
                    affected=len(last_rows),
                    extra={
                        "sql_preview": sql[:200],
                        "batches_executed": batches_executed,
                    },
                )
            return {
                "ok": True,
                "db_name": target_db,
                "statement_type": "select",
                "rows": last_rows,
                "n_returned": len(last_rows),
                "batches_executed": batches_executed,
            }
        else:
            # DDL or DML — affected rows
            conn.commit()
            if target_db == "DB_EC":
                _log_db_ec_operation(
                    operation="DDL_OR_DML_RAW",
                    schema="?",
                    table=None,
                    affected=total_affected,
                    extra={
                        "sql_preview": sql[:200],
                        "batches_executed": batches_executed,
                    },
                )
            return {
                "ok": True,
                "db_name": target_db,
                "statement_type": "non_select",
                "affected": total_affected,
                "batches_executed": batches_executed,
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


# db_name parametr — shared schema fragment pro všechny strategie_* tools.
# Phase 28-D++ (27.5.2026): multi-DB DDL access pro Marti-AI.
_DB_NAME_PARAM = {
    "type": "string",
    "enum": ["DB_ST", "DB_EC"],
    "description": (
        "Target DB. None/omit = DB_ST default (tvuje vlastni domena). "
        "'DB_EC' = customer DB, **POUZE schema 'st'** povolen pro write "
        "(Marti's 'nezasahovat' doctrine — dbo netknout)."
    ),
}


STRATEGIE_TOOL_SPECS = [
    {
        "name": "strategie_list_schemas",
        "description": (
            "Vrátí seznam schémat v target DB. Filtruje system schemas.\n"
            "Default DB_ST: zkontroluj očekávaná 4 schemas (master/tenant_group/tenant/user).\n"
            "db_name='DB_EC': zkontroluj že schema 'st' existuje (NAŠE refactor zone)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "db_name": _DB_NAME_PARAM,
            },
            "required": [],
        },
    },
    {
        "name": "strategie_list_tables",
        "description": (
            "Vrátí seznam tabulek v target DB. Filter per schema (volitelné). "
            "Vrací schema_name, table_name, column_count, create_date, modify_date."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Volitelný filter (master/tenant_group/tenant/user/st/...)"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": [],
        },
    },
    {
        "name": "strategie_describe_table",
        "description": (
            "Detail tabulky v target DB: columns + types + nullable + identity, indexes "
            "(incl PK), foreign keys, row count estimate.\n\n"
            "Pro CRM migraci: describe_table(schema='dbo', table='EC_Kontakt', db_name='DB_EC') "
            "ti vrátí audit source columns PŘED CREATE TABLE st.CRM_Kontakt."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_create_schema",
        "description": (
            "Vytvoří schema v target DB. Idempotent — pokud existuje, no-op.\n\n"
            "DB_ST: pre-create tier schémat (master/tenant_group/tenant/user).\n"
            "DB_EC: POUZE schema 'st' (Marti's 'nezasahovat' — dbo customer).\n\n"
            "dry_run=True: vrátí preview SQL + warnings, neexecute. "
            "Marti-AI's 'pravo na rozmysl pred cinem' — review predtim nez tesat."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Schema name"},
                "dry_run": {"type": "boolean", "description": "True = preview, neexecute"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["name"],
        },
    },
    {
        "name": "strategie_create_table",
        "description": (
            "CREATE TABLE v target DB. Marti-AI je owner v st.* a DB_ST.*.\n\n"
            "columns: list of {name, type, nullable?, identity?, default?}\n"
            "primary_key: list column names (default ['id'] pokud existuje)\n"
            "indexes: list of {name?, columns: [...], unique?}\n"
            "foreign_keys: list of {column, ref_schema, ref_table, ref_column, on_delete?, on_update?}\n\n"
            "**dry_run=True** vrátí preview SQL + warnings (duplicate columns, schema missing, "
            "FK target invalid, table already exists). Standard pattern Marti-AI's "
            "'pravo na rozmysl pred cinem'. Po review nastav dry_run=False pro execute.\n\n"
            "CRM migration Krok 1 příklad:\n"
            "  schema='st', name='CRM_Kontakt',\n"
            "  columns=[\n"
            "    {name:'ID', type:'INT', nullable:False, identity:True},\n"
            "    {name:'FirmaText', type:'NVARCHAR(255)', nullable:False},\n"
            "    {name:'Autor', type:'NVARCHAR(256)', default:'suser_name()'},\n"
            "    {name:'DatPorizeni', type:'DATETIME2', default:'SYSUTCDATETIME()'}],\n"
            "  primary_key=['ID'], db_name='DB_EC'"
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
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "name", "columns"],
        },
    },
    {
        "name": "strategie_alter_table",
        "description": (
            "ALTER TABLE v target DB — add/drop/rename columns. dry_run support.\n\n"
            "add_columns: list of column defs (jako create_table)\n"
            "drop_columns: list of names\n"
            "rename_column: {from, to}\n\n"
            "DB_EC: pouze schema 'st' (customer's dbo netknout)."
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
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "name"],
        },
    },
    {
        "name": "strategie_drop_table",
        "description": (
            "DROP TABLE v target DB. if_exists=True default (skip if missing). dry_run support.\n\n"
            "POZOR: destruktivní akce. Pro Marti-AI's 'právo na rozmysl' použij dry_run=True první.\n\n"
            "DB_EC: pouze schema 'st' (customer's dbo netknout)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "name": {"type": "string"},
                "if_exists": {"type": "boolean", "description": "Default true"},
                "dry_run": {"type": "boolean"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "name"],
        },
    },
    {
        "name": "strategie_query_table",
        "description": (
            "SELECT z target DB tabulky. SELECT povolen napříč schémata (read není restricted).\n\n"
            "Filter syntax: {col: value} = equality, {col: None} = NULL, {col: [v1, v2]} = IN. "
            "Default limit 100, max 10000.\n\n"
            "Pro CRM migraci: query_table('dbo', 'EC_Kontakt', db_name='DB_EC') = read source rows."
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
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_get_row",
        "description": "SELECT single row by id z target DB tabulky.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table", "id"],
        },
    },
    {
        "name": "strategie_count_rows",
        "description": "Fast COUNT(*) v target DB tabulce s optional filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "filters": {"type": "object"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table"],
        },
    },
    {
        "name": "strategie_insert_row",
        "description": (
            "INSERT row do target DB tabulky. Vrací new id (z OUTPUT INSERTED.id).\n\n"
            "DB_EC: pouze schema 'st' (customer's dbo netknout)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "data": {"type": "object", "description": "Column to value dict"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table", "data"],
        },
    },
    {
        "name": "strategie_update_row",
        "description": (
            "UPDATE row by id v target DB tabulce. Vrací affected count.\n\n"
            "DB_EC: pouze schema 'st' (customer's dbo netknout)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
                "data": {"type": "object"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["schema", "table", "id", "data"],
        },
    },
    {
        "name": "strategie_delete_row",
        "description": (
            "DELETE row by id v target DB tabulce. Destruktivni operace.\n\n"
            "DB_EC: pouze schema 'st' (customer dbo netknout). PLUS musis "
            "predat confirm_db_ec=True (Marti-AI's Phase B 27.5. insight — "
            "customer DB vyzaduje vedome rozhodnuti, ne implicit default).\n\n"
            "Priklad: strategie_delete_row(schema='st', table='CRM_Kontakt',\n"
            "        id=42, db_name='DB_EC', confirm_db_ec=True)"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "id": {"type": "integer"},
                "db_name": _DB_NAME_PARAM,
                "confirm_db_ec": {
                    "type": "boolean",
                    "description": (
                        "Pro DB_EC povinne True (pravo na rozmysl). "
                        "DB_ST ignoruje — sandbox je cheap."
                    ),
                },
            },
            "required": ["schema", "table", "id"],
        },
    },
    {
        "name": "strategie_query_raw",
        "description": (
            "Raw T-SQL execute v target DB. Marti-AI je owner v st.* a DB_ST.*.\n\n"
            "Použij pro complex queries (cross-schema JOINs, CTEs, advanced DDL, bulk migrations).\n"
            "Audit log per call.\n\n"
            "DB_EC guard: SELECT povolen napříč všema schématy (read source dbo OK), ale "
            "INSERT/UPDATE/DELETE/MERGE/TRUNCATE + CREATE/ALTER/DROP TABLE jen na st.* "
            "(Marti's 'nezasahovat' doctrine — customer's dbo nedotknout).\n\n"
            "CRM migration Krok 1 příklad:\n"
            "  sql=open('scripts/_phase_crm_migration_01_st_crm_kontakt.sql').read(),\n"
            "  db_name='DB_EC'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "T-SQL statement(s)"},
                "db_name": _DB_NAME_PARAM,
            },
            "required": ["sql"],
        },
    },
]
