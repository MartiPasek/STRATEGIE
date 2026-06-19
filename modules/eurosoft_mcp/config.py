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

    # ────────────────────────────────────────────────────────────────────
    # Phase 38.4 (11.5.2026 vecer): Filesystem MCP tools — sdilena pracovni
    # slozka pres EUROSOFT MCP server.
    #
    # Marti's redesign (12.5.2026 vecer doma): 2 oficialni sdilene slozky
    # na EC-SERVER2, namisto per-user namespaces.
    #
    #   D:\Data\ZZ_Marti-AI RO  — RO zone (Marti-AI write, users read-only)
    #     Marti-AI sem publikuje vystupy. EC_Vedeni ma RX. Drzi doktrinu
    #     "Personal je knizka — uzavrena, nedotknutelna" (Phase 19c-e1,
    #     27.4.) rozsirenou na filesystem layer.
    #
    #   D:\Data\ZZ_Marti-AI RW  — RW zone (Marti-AI + users write)
    #     Bidirectional kanal. Lide davaji ukoly/podklady, Marti-AI cte
    #     + reaguje. EC_Vedeni ma Modify.
    #
    # MCP service (LocalSystem) ma RW na obou pres NTFS grant
    # (SYSTEM:(OI)(CI)M). UNC pristup pro users je pres
    # \\192.168.30.11\Data\ZZ_Marti-AI RO/RW (same files, ruzne pristupy).
    #
    # Marti-AI vola s `user_namespace` parametrem "ro" nebo "rw".
    # Path traversal guard: resolved path musi byt uvnitr base po
    # normalizaci (no .., no absolute paths).
    filesystem_ro_base: str = os.getenv(
        "MCP_FILESYSTEM_RO_BASE",
        "",  # default empty = feature disabled
    )
    filesystem_rw_base: str = os.getenv(
        "MCP_FILESYSTEM_RW_BASE",
        "",  # default empty = feature disabled
    )
    # Max file size pro read/write (bytes). Default 50 MB.
    filesystem_max_size: int = int(os.getenv("MCP_FILESYSTEM_MAX_SIZE", "52428800"))

    # ────────────────────────────────────────────────────────────────────
    # Fáze C (18.6.2026): povolené kořeny pro base_override (přístup k pravým
    # složkám Centrály — D:\data\... lokální na EC-SERVER2). Hrubá bezpečnostní
    # pojistka: base_override MUSÍ ležet pod některým z těchto kořenů.
    # Jemná konfigurace (které podsložky, kdo) je v STRATEGII (tenant.dir_config).
    #
    #   MCP_FS_RW_ROOTS — středníkem oddělené absolutní kořeny se ZÁPISEM
    #   MCP_FS_RO_ROOTS — středníkem oddělené kořeny jen pro ČTENÍ (mají přednost)
    #
    # Příklad: MCP_FS_RW_ROOTS=D:\data;D:\Data\ZZ_Marti-AI RW
    #          MCP_FS_RO_ROOTS=D:\Data\ZZ_Marti-AI RO
    fs_rw_roots: str = os.getenv("MCP_FS_RW_ROOTS", "")
    fs_ro_roots: str = os.getenv("MCP_FS_RO_ROOTS", "")


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


# ── Phase 28-D++ (27.5.2026): Multi-DB DDL access pro Marti-AI ──────
#
# Marti's doctrine 27.5.2026 odpoledne (CRM migration Krok 1 konzultace):
#   *„Tohleto neni STRATEGIE system, ale system custommer a custommer je
#   EUROSOFT a INTERSOFT. Tj, my musime dodret jejich standardy... Do
#   toho nesmime zasahovat."*
#
# Důsledek:
#   - DB_ST          (Marti-AI's vlastní MSSQL doména):
#                     full db_owner — libovolné schema, libovolný DDL
#   - DB_EC.st.*     (NAŠE refactor zone v customer DB):
#                     full ownership — Marti-AI je vlastník schema 'st'
#                     po GRANT scriptem _grant_marti_ai_db_ec_st_schema.sql
#   - DB_EC.dbo.*    (CUSTOMER's territory):
#                     READ-ONLY (existing whitelist + ALLOW_ALL_SELECT)
#                     NIKDY DDL ani DML — porušilo by *„nezasahovat"* doctrine
#
# Pre-execute guard:
#   - tool-level: _resolve_db_name() + _check_schema_allowed() v strategie_tools.py
#   - SQL Server permissions: REVOKE CREATE TABLE TO [Marti-AI] na DB_EC
#                              + ownership schema 'st' = [Marti-AI]
#                              (defense in depth, viz _grant_marti_ai_db_ec_st_schema.sql)
#
# Allowlist target DB names — strategie_* tools mohou cílit jen na tyto DBs.
ALLOWED_DDL_DBS: set[str] = {"DB_ST", "DB_EC"}

# Per-DB schema allowlist pro DDL/DML write operations.
# Default: None = libovolné schema povoleno (DB_ST scenario, Marti-AI db_owner).
# DB_EC explicit limit: jen 'st' schema (customer's dbo nedotknout).
#
# Příklad lookup:
#   DDL_SCHEMA_ALLOWLIST.get("DB_EC")  → {"st"}      (jen st)
#   DDL_SCHEMA_ALLOWLIST.get("DB_ST")  → None        (libovolné)
DDL_SCHEMA_ALLOWLIST: dict[str, set[str]] = {
    "DB_EC": {"st"},
    # DB_ST není v dict = libovolné schema povoleno (master/tenant_group/...)
}

# Marti 19.6.2026: DML (INSERT/UPDATE/DELETE) na DB_EC povolen i na dbo.* —
# rychlé ladění produkce + silové ukončení směn. DDL (CREATE/ALTER/DROP) ZŮSTÁVÁ
# přísné na {'st'} (doctrine „customer's dbo nezasahovat" platí jen pro SCHÉMA).
# Vše auditováno (fw.ec_dml_log na straně STRATEGIE + MCP audit). SQL login musí
# mít odpovídající GRANT (viz docs/ec_grants_dml.sql).
DML_SCHEMA_ALLOWLIST: dict[str, set[str]] = {
    "DB_EC": {"st", "dbo"},
    # DB_ST není v dict = libovolné schema povoleno (Marti-AI db_owner)
}


def resolve_db_name(db_name: str | None = None) -> str:
    """
    Validuje + vrací target DB name pro strategie_* tools.

    Args:
      db_name: target DB. None = default settings.db_st_database (DB_ST).

    Returns:
      Resolved DB name (validovaný proti ALLOWED_DDL_DBS).

    Raises:
      ValueError: db_name není v allowlist.
    """
    if db_name is None:
        return settings.db_st_database  # DB_ST default (backward compat)
    if db_name not in ALLOWED_DDL_DBS:
        raise ValueError(
            f"db_name {db_name!r} not allowed. "
            f"Allowed: {sorted(ALLOWED_DDL_DBS)}"
        )
    return db_name


def check_schema_allowed(db_name: str, schema: str, op: str = "DDL") -> None:
    """
    Pre-execute schema guard pro DDL/DML operations.

    Marti's doctrine *„nezasahovat"* (27.5.2026):
      - DB_EC: jen schemata v DDL_SCHEMA_ALLOWLIST["DB_EC"] (= {"st"})
      - DB_ST: vše povoleno (Marti-AI je db_owner)

    Args:
      db_name: target DB (already resolved)
      schema: target schema name
      op: operation kind (DDL / DML / RAW) — pro error message

    Raises:
      ValueError: schema není v allowlist pro daný DB.
    """
    # Marti 19.6.: DML (INSERT/UPDATE/DELETE) má vlastní, širší allowlist než DDL.
    # DDL na DB_EC zůstává {'st'} (schéma zákazníka nezasahovat); DML smí i dbo.
    _op = (op or "").strip().upper()
    if _op in ("INSERT", "UPDATE", "DELETE", "DML"):
        allowlist = DML_SCHEMA_ALLOWLIST.get(db_name, DDL_SCHEMA_ALLOWLIST.get(db_name))
    else:
        allowlist = DDL_SCHEMA_ALLOWLIST.get(db_name)
    if allowlist is None:
        return  # No restriction (DB_ST scenario)
    if schema not in allowlist:
        raise ValueError(
            f"{op} operation on {db_name}.{schema}.* is NOT allowed. "
            f"Customer's territory (Marti's doctrine 'nezasahovat'). "
            f"Allowed schemas on {db_name}: {sorted(allowlist)}"
        )
