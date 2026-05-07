"""
pyodbc connection wrapper for EUROSOFT MCP server.

Phase 28-D (8.5.2026): multi-DB connection pool.
Současná instance (DB_EC default + DB_ST nový pool) sdílí SQL Server
192.168.30.11\\SQLEXPRESS2017 a Marti-AI SQL login. Per-DB credentials
v config (db_st_database). Marti-AI je db_owner na DB_ST (full DDL+DML),
db_datareader+EC_KontaktAkce write na DB_EC (Phase 28-A2 whitelist).

Connection pool dictionary — keyed by db_name:
    "DB_EC" -> pyodbc.Connection (existing)
    "DB_ST" -> pyodbc.Connection (Phase 28-D)
Both autocommit=False (DDL operations Marti-AI volá s explicit COMMIT
v handler).
"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Generator

import pyodbc

from .config import settings

logger = logging.getLogger("eurosoft_mcp.sql")


# Connection pool — db_name -> pyodbc.Connection
_connections: dict[str, pyodbc.Connection] = {}
_lock = threading.Lock()


def _build_connection_string(db_name: str | None = None) -> str:
    """Build connection string. Pokud db_name None, použije settings.sql_database (DB_EC default)."""
    target_db = db_name or settings.sql_database
    return (
        f"DRIVER={{{settings.sql_driver}}};"
        f"SERVER={settings.sql_server};"
        f"DATABASE={target_db};"
        f"UID={settings.sql_user};"
        f"PWD={settings.sql_password};"
        f"TrustServerCertificate=Yes;"
        f"Connection Timeout={settings.sql_timeout_s};"
    )


def init_connection(db_name: str | None = None) -> pyodbc.Connection:
    """
    Initialize / reinitialize connection pro daný db_name.
    Default = settings.sql_database (DB_EC).
    """
    target_db = db_name or settings.sql_database
    with _lock:
        # Close existing if any (reinit)
        existing = _connections.get(target_db)
        if existing is not None:
            try:
                existing.close()
            except Exception:
                pass
            _connections.pop(target_db, None)

        if not settings.sql_password:
            raise RuntimeError(
                "EUROSOFT_SQL_PASSWORD env var is not set. "
                "Cannot connect to SQL Server."
            )
        logger.info(
            f"Connecting to SQL Server: {settings.sql_server} / "
            f"{target_db} as {settings.sql_user}"
        )
        conn = pyodbc.connect(
            _build_connection_string(target_db),
            autocommit=False,
        )
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT @@VERSION, DB_NAME()")
        row = cur.fetchone()
        version = row[0]
        actual_db = row[1]
        cur.close()
        logger.info(
            f"Connected. SQL Server: {version[:80]}... "
            f"Active database: {actual_db}"
        )
        _connections[target_db] = conn
    return conn


def close_connection(db_name: str | None = None) -> None:
    """Close connection pro daný db_name (nebo všechna pokud None)."""
    with _lock:
        if db_name is None:
            # Close all
            for name, conn in list(_connections.items()):
                try:
                    conn.close()
                except Exception:
                    pass
            _connections.clear()
            logger.info("All SQL connections closed.")
        else:
            conn = _connections.pop(db_name, None)
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                logger.info(f"SQL connection closed: {db_name}")


@contextmanager
def get_cursor(
    db_name: str | None = None,
    retry_on_disconnect: bool = True,
) -> Generator[pyodbc.Cursor, None, None]:
    """
    Yield a cursor pro daný db_name (default DB_EC).
    Automatic reconnect on connection loss.
    """
    target_db = db_name or settings.sql_database
    conn = _connections.get(target_db)
    if conn is None:
        conn = init_connection(target_db)

    try:
        cur = conn.cursor()
    except (pyodbc.Error, AttributeError) as e:
        if retry_on_disconnect:
            logger.warning(
                f"Cursor creation failed for {target_db} ({e}), reconnecting..."
            )
            conn = init_connection(target_db)
            cur = conn.cursor()
        else:
            raise

    try:
        yield cur
    finally:
        try:
            cur.close()
        except Exception:
            pass


def get_connection(db_name: str | None = None) -> pyodbc.Connection:
    """
    Direct connection access pro DDL operations co potřebují commit/rollback
    explicit (strategie_* tools v Phase 28-D). Auto-init pokud chybí.
    """
    target_db = db_name or settings.sql_database
    conn = _connections.get(target_db)
    if conn is None:
        conn = init_connection(target_db)
    return conn


def quote_identifier(name: str) -> str:
    """SQL Server identifier quoting via brackets. Defends against injection
    on identifier slot (table/column names)."""
    if not name or not isinstance(name, str):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    # SQL Server identifiers: brackets-quoted, escape internal ] as ]]
    return "[" + name.replace("]", "]]") + "]"


def fetchall_as_dicts(cursor: pyodbc.Cursor) -> list[dict[str, Any]]:
    """Vrátí všechny řádky jako list of dicts (column_name → value)."""
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out = []
    for r in rows:
        d = {}
        for i, col in enumerate(cols):
            v = r[i]
            # Convert non-JSON-serializable types
            if hasattr(v, "isoformat"):  # datetime, date
                d[col] = v.isoformat()
            elif isinstance(v, (bytes, bytearray)):
                d[col] = v.hex()  # binary as hex string
            elif isinstance(v, (int, float, str, bool, type(None))):
                d[col] = v
            else:
                d[col] = str(v)  # fallback (Decimal, UUID, atd.)
        out.append(d)
    return out
