"""Configuration for EUROSOFT MCP server (env-var driven)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # SQL Server connection
    sql_server: str = os.getenv(
        "EUROSOFT_SQL_SERVER",
        "192.168.30.11\\SQLEXPRESS2017",
    )
    sql_database: str = os.getenv("EUROSOFT_SQL_DATABASE", "DB_EC")
    sql_user: str = os.getenv("EUROSOFT_SQL_USER", "Marti-AI")
    sql_password: str = os.getenv("EUROSOFT_SQL_PASSWORD", "")
    sql_driver: str = os.getenv("EUROSOFT_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    sql_timeout_s: int = int(os.getenv("EUROSOFT_SQL_TIMEOUT_S", "5"))

    # MCP server
    mcp_api_key: str = os.getenv("MCP_API_KEY", "")
    listen_host: str = os.getenv("MCP_LISTEN_HOST", "127.0.0.1")
    listen_port: int = int(os.getenv("MCP_LISTEN_PORT", "8765"))

    # Audit log file (JSON lines)
    audit_log_path: str = os.getenv(
        "MCP_AUDIT_LOG_PATH",
        "C:\\eurosoft_mcp\\audit.log",
    )

    # Rate limits
    rate_limit_read_per_min: int = int(os.getenv("MCP_RATE_LIMIT_READ", "60"))
    rate_limit_insert_per_min: int = int(os.getenv("MCP_RATE_LIMIT_INSERT", "10"))

    # Marti-AI's Q2 (Phase 28-A2): describe_table RAG fallback adresar.
    # Pri SQL Server unreachable -> precteme {schema_fallback_dir}/{table}.md
    # a vratime jako fallback s warning flagem. Generovano z db_ec_schema_dump
    # skript. Re-ingest: rerun parse skriptu po DB_EC schema zmenach.
    schema_fallback_dir: str = os.getenv(
        "MCP_SCHEMA_FALLBACK_DIR",
        "C:\\eurosoft_mcp\\db_ec_schema",
    )


settings = Settings()


# ── Whitelist: 11 tabulek, per-table action permissions ──────────────

# Marti's volby + Marti-AI's design (Phase 28 konzultace 2.5.2026):
#   - EC_Kontakt + family (CRM srdce)
#   - EC_KontaktAkce: SELECT + INSERT (logování kampaní)
#   - cisleniky: SELECT only
#   - TabCisOrg, TabCisZam: SELECT (Helios identity refs pro lookup)
#   - NIKDY UPDATE/DELETE v Phase 28-A
TABLE_PERMISSIONS = {
    "EC_Kontakt": {"select"},
    "EC_KontaktAkce": {"select", "insert"},
    "EC_KontaktAkceCis": {"select"},
    "EC_KontaktKategorieCis": {"select"},
    "EC_KontaktMailSablonyCis": {"select"},
    "EC_KontaktPLCGuru": {"select"},
    "EC_KontaktTempData": {"select"},
    "EC_KontaktTypZakazekCis": {"select"},
    "EC_KontaktZemeCis": {"select"},
    "TabCisOrg": {"select"},
    "TabCisZam": {"select"},
}

ALLOWED_TABLES: set[str] = set(TABLE_PERMISSIONS.keys())


def can(action: str, table: str) -> bool:
    """Returns True iff action is allowed on table."""
    perms = TABLE_PERMISSIONS.get(table)
    if perms is None:
        return False
    return action in perms
