"""
pyodbc connection wrapper for EUROSOFT MCP server.

Single shared connection (autoreconnect on failure). Cursor-per-call.
SQL Server is on 192.168.30.11\\SQLEXPRESS2017, accessed as Marti-AI
SQL login (read on whitelist + insert on EC_KontaktAkce).
"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Generator

import pyodbc

from .config import settings

logger = logging.getLogger("eurosoft_mcp.sql")


_connection: pyodbc.Connection | None = None
_lock = threading.Lock()


def _build_connection_string() -> str:
    return (
        f"DRIVER={{{settings.sql_driver}}};"
        f"SERVER={settings.sql_server};"
        f"DATABASE={settings.sql_database};"
        f"UID={settings.sql_user};"
        f"PWD={settings.sql_password};"
        f"TrustServerCertificate=Yes;"
        f"Connection Timeout={settings.sql_timeout_s};"
    )


def init_connection() -> pyodbc.Connection:
    """Initialize / reinitialize the global SQL connection."""
    global _connection
    with _lock:
        if _connection is not None:
            try:
                _connection.close()
            except Exception:
                pass
        if not settings.sql_password:
            raise RuntimeError(
                "EUROSOFT_SQL_PASSWORD env var is not set. "
                "Cannot connect to SQL Server."
            )
        logger.info(
            f"Connecting to SQL Server: {settings.sql_server} / "
            f"{settings.sql_database} as {settings.sql_user}"
        )
        _connection = pyodbc.connect(
            _build_connection_string(),
            autocommit=False,
        )
        # Test query
        cur = _connection.cursor()
        cur.execute("SELECT @@VERSION")
        version = cur.fetchone()[0]
        cur.close()
        logger.info(f"Connected. SQL Server version: {version[:80]}...")
    return _connection


def close_connection() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            try:
                _connection.close()
            except Exception:
                pass
            _connection = None


@contextmanager
def get_cursor(retry_on_disconnect: bool = True) -> Generator[pyodbc.Cursor, None, None]:
    """Yield a cursor, with automatic reconnect on connection loss."""
    global _connection
    if _connection is None:
        init_connection()

    try:
        cur = _connection.cursor()
    except (pyodbc.Error, AttributeError) as e:
        if retry_on_disconnect:
            logger.warning(f"Cursor creation failed ({e}), reconnecting...")
            init_connection()
            cur = _connection.cursor()
        else:
            raise

    try:
        yield cur
    finally:
        try:
            cur.close()
        except Exception:
            pass


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
