"""Configuration for EUROSOFT MCP server (env-var driven)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # SQL Server connection — DB_EC (existing, Centrála 1)
    sql_server: str = os.getenv(
        "EUROSOFT_SQL_SERVER",
        "192.168.30.11\\SQLEXPRESS2017",
    )
    sql_database: str = os.getenv("EUROSOFT_SQL_DATABASE", "DB_EC")
    sql_user: str = os.getenv("EUROSOFT_SQL_USER", "Marti-AI")
    sql_password: str = os.getenv("EUROSOFT_SQL_PASSWORD", "")
    sql_driver: str = os.getenv("EUROSOFT_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    sql_timeout_s: int = int(os.getenv("EUROSOFT_SQL_TIMEOUT_S", "5"))

    # Phase 28-D (8.5.2026): DB_ST — Marti-AI's owned doména.
    # Shared SQL Server instance s DB_EC, ale separate database, db_owner
    # role (full DDL+DML, žádný whitelist). Diář pattern: "AI provede,
    # lidé reflektují". Login + heslo SDÍLENO s DB_EC (Marti-AI je
    # SQL login na master, db_owner mapping per database).
    db_st_database: str = os.getenv("EUROSOFT_DB_ST_DATABASE", "DB_ST")
    # Bezpečnostní flag — DDL operace na DB_ST (CREATE/ALTER/DROP TABLE)
    # vyžadují tento flag = "true" (default). Když dělá Marti's IT
    # security audit, může temporary disable přes env.
    allow_db_st_ddl: bool = os.getenv("MCP_ALLOW_DB_ST_DDL", "true").lower() in ("true", "1", "yes")

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
    # Phase 28 (2.5.2026) — CRM srdce + Helios identity refs (11 tabulek)
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

    # Phase A — STRATEGIE ERP renderer (5.5.2026 ráno).
    # Read-only přístup k Centrála framework metadatům pro generování
    # moderní web verze. Žádné UPDATE/INSERT — modifikace definic frameworku
    # zůstává v Centrále 1. Detail: docs/strategie_erp_renderer_proposal.md
    "EC_FormDef": {"select"},                # jádro header (form definitions)
    "EC_FormDefEdit": {"select"},            # komponenty jádra
    "EC_FormDefEditProperty": {"select"},    # property komponent (key/value)
    "EC_CentralaMenu": {"select"},           # strom soudečků
    "EC_CentralaMenuUziv": {"select"},       # per-user override stromu
    "EC_DELPHI_TabObecnyPrehled": {"select"}, # přehledy (DefView SQL)
    "EC_GlobKonst": {"select"},              # tenant config (Firma=EC/IAP)
    "EC_GlobKonstUziv": {"select"},          # per-user customization
}

ALLOWED_TABLES: set[str] = set(TABLE_PERMISSIONS.keys())


# ── Phase B+1.2 (5.5.2026 odpoledne): ALL-tables read-only mode ─────
#
# Marti's volba: pro ladění Centrály 1 renderer (Phase A/B) potřebujeme
# SELECT na libovolnou tabulku DB_EC. Per-table whitelist (Phase 28-A2
# konzultace 2.5.2026) drhl na každý nový soudeček, který má nový
# target_table v EC_DELPHI_TabObecnyPrehled.
#
# Default: True (env var MCP_ALLOW_ALL_SELECT). Write akce
# (insert/update/delete) zůstávají STRIKTNĚ whitelist přes
# TABLE_PERMISSIONS — tato pojistka není dotčena.
ALLOW_ALL_SELECT: bool = os.getenv("MCP_ALLOW_ALL_SELECT", "true").lower() in ("true", "1", "yes")


def can(action: str, table: str) -> bool:
    """Returns True iff action is allowed on table.

    Phase B+1.2 (5.5.): pokud table neni v TABLE_PERMISSIONS a action je 'select'
    a ALLOW_ALL_SELECT je on, vraci True (default-allow read-only mode).
    """
    perms = TABLE_PERMISSIONS.get(table)
    if perms is not None and action in perms:
        return True
    # Phase B+1.2: ALL-tables read-only fallback (env-driven, default on)
    if action == "select" and ALLOW_ALL_SELECT:
        return True
    return False


def permissions(table: str) -> list[str]:
    """Returns sorted list of allowed actions for table.

    Phase B+1.2 (5.5.): pokud table neni v TABLE_PERMISSIONS a ALLOW_ALL_SELECT
    je on, vraci ['select'] jako implicit read-only mode.
    """
    perms = TABLE_PERMISSIONS.get(table)
    if perms:
        return sorted(perms)
    if ALLOW_ALL_SELECT:
        return ["select"]
    return []
