"""
EUROSOFT MCP server — main entry point.

Architecture:
  - MCP Python SDK Server with list_tools / call_tool handlers
  - SSE transport (HTTP) for remote MCP clients
  - Starlette ASGI app with Bearer token auth middleware + health endpoint
  - Listens on 127.0.0.1:8765 (Caddy reverse-proxies api.eurosoft.com/marti-mcp/* → here)
  - Per-call: rate limit check → SQL execution → audit log
  - SQL connection initialized on startup, closed on shutdown

Run:
  set EUROSOFT_SQL_PASSWORD=...
  set MCP_API_KEY=...
  python -m eurosoft_mcp.server

Or as Windows service (NSSM/sc.exe):
  python -m eurosoft_mcp.server
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .audit import audit_log
from .config import settings
from .rate_limit import limiter
from .sql_client import close_connection, init_connection
from .tools import TOOL_HANDLERS, TOOL_SPECS

logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("eurosoft_mcp.server")


# ── MCP server: list_tools + call_tool handlers ────────────────────────

mcp_server = Server("eurosoft-mcp")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Vrací seznam dostupných MCP toolů (kontrakt = TOOL_SPECS)."""
    return [
        Tool(
            name=spec["name"],
            description=spec["description"],
            inputSchema=spec["inputSchema"],
        )
        for spec in TOOL_SPECS
    ]


def _classify_action(tool_name: str) -> str:
    """Klasifikace pro rate limit (read vs insert)."""
    if tool_name in {"insert_row", "bulk_insert_rows"}:
        return "insert"
    return "read"


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """
    Dispatch na konkrétní tool handler.
    Před voláním: rate limit check.
    Po volání: audit log (success / error).
    """
    arguments = arguments or {}
    api_key = _current_api_key.get() or "unknown"
    action_kind = _classify_action(name)

    # Rate limit
    allowed, count = limiter.check_and_record(api_key, action_kind)
    if not allowed:
        msg = (
            f"Rate limit exceeded: {action_kind} ({count} v posledni minute, "
            f"limit {settings.rate_limit_read_per_min if action_kind == 'read' else settings.rate_limit_insert_per_min}/min). "
            f"Pockej cca minutu a zkus znovu."
        )
        audit_log(name, arguments, error=msg, runtime_ms=0)
        return [TextContent(type="text", text=json.dumps(
            {"ok": False, "error": "rate_limit_exceeded", "message": msg},
            ensure_ascii=False,
        ))]

    # Dispatch
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        msg = f"Neznamy tool: {name}. Dostupne: {sorted(TOOL_HANDLERS.keys())}"
        audit_log(name, arguments, error=msg, runtime_ms=0)
        return [TextContent(type="text", text=json.dumps(
            {"ok": False, "error": "unknown_tool", "message": msg},
            ensure_ascii=False,
        ))]

    t0 = time.monotonic()
    try:
        result = await handler(**arguments)
        runtime_ms = int((time.monotonic() - t0) * 1000)
        audit_log(name, arguments, result=result, runtime_ms=runtime_ms)
        return [TextContent(type="text", text=json.dumps(
            result, ensure_ascii=False, default=str,
        ))]
    except TypeError as e:
        # Bad args (missing required, wrong types)
        msg = f"Spatne argumenty pro {name}: {e}"
        runtime_ms = int((time.monotonic() - t0) * 1000)
        audit_log(name, arguments, error=msg, runtime_ms=runtime_ms)
        return [TextContent(type="text", text=json.dumps(
            {"ok": False, "error": "bad_arguments", "message": msg},
            ensure_ascii=False,
        ))]
    except ValueError as e:
        # Whitelist / permission / validation
        msg = str(e)
        runtime_ms = int((time.monotonic() - t0) * 1000)
        audit_log(name, arguments, error=msg, runtime_ms=runtime_ms)
        return [TextContent(type="text", text=json.dumps(
            {"ok": False, "error": "validation_error", "message": msg},
            ensure_ascii=False,
        ))]
    except Exception as e:
        # SQL / pyodbc / unexpected
        msg = f"{type(e).__name__}: {e}"
        runtime_ms = int((time.monotonic() - t0) * 1000)
        logger.exception(f"Tool {name} failed")
        audit_log(name, arguments, error=msg, runtime_ms=runtime_ms)
        return [TextContent(type="text", text=json.dumps(
            {"ok": False, "error": "internal_error", "message": msg},
            ensure_ascii=False,
        ))]


# ── Bearer token auth middleware ───────────────────────────────────────

# Kontextová proměnná drží api_key přihlášeného klienta pro current request
# (bez ContextVar bychom museli api_key tlačit přes celý dispatch chain)
import contextvars

_current_api_key: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_api_key", default=None
)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Vyzaduje 'Authorization: Bearer <MCP_API_KEY>' na vsech ne-health endpointech."""

    async def dispatch(self, request: Request, call_next):
        # Health endpoint je verejny (Caddy ho potrebuje pro liveness)
        if request.url.path in ("/health", "/healthz"):
            return await call_next(request)

        if not settings.mcp_api_key:
            logger.error("MCP_API_KEY env var neni nastaveny — server odmita vsechny pozadavky")
            return JSONResponse(
                {"error": "server_misconfigured", "message": "MCP_API_KEY neni nastaveny"},
                status_code=500,
            )

        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return JSONResponse(
                {"error": "unauthorized", "message": "Missing Bearer token"},
                status_code=401,
            )

        token = auth[7:].strip()
        if token != settings.mcp_api_key:
            logger.warning(f"Invalid Bearer token from {request.client.host if request.client else '?'}")
            return JSONResponse(
                {"error": "unauthorized", "message": "Invalid Bearer token"},
                status_code=401,
            )

        # Set API key into ContextVar for downstream tool handlers (rate limit bucket)
        _current_api_key.set(token[:16])  # Use first 16 chars as bucket key (token hash-like)
        return await call_next(request)


# ── SSE transport setup ────────────────────────────────────────────────

# SSE endpoint pro MCP klienty:
#   - GET  /sse        — establish event stream
#   - POST /messages/  — JSON-RPC messages from client
sse_transport = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    """SSE endpoint — drzi event stream s MCP klientem."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send,
    ) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options(),
        )
    return Response()


async def health(request: Request):
    """Liveness endpoint pro Caddy / monitoring."""
    return JSONResponse({
        "ok": True,
        "service": "eurosoft-mcp",
        "tools": sorted(TOOL_HANDLERS.keys()),
    })


async def audit_summary(request: Request):
    """
    Marti-AI's Q3 (Phase 28-A2): tichá injekce do system promptu.
    Vraci agregovany shrnujici JSON za dany den z lokalniho audit.log:
      { date: "2026-05-02", inserts: 47, failures: 3, selects: 1235,
        last_call: "14:23" }
    Vyzaduje Bearer auth (jako vsechno krome /health).
    Composer (cloud APP) ho fetchne kazdy turn a injektuje do system promptu
    jako '[EUROSOFT MCP dnes] N INSERTu · M failed · last HH:MM'.

    Bridge resenim do Phase 28-B (audit log push do action_log + AI tool
    recall_eurosoft_actions). Az 28-B nasazeno, tento endpoint se muze
    nechat (nestoji nic) anebo deprecate.
    """
    from datetime import date, datetime, timezone
    from pathlib import Path

    today_iso = date.today().isoformat()
    inserts = 0
    failures = 0
    selects = 0
    other = 0
    last_call_iso: str | None = None

    audit_path = Path(settings.audit_log_path)
    if not audit_path.exists():
        return JSONResponse({
            "ok": True,
            "date": today_iso,
            "inserts": 0,
            "failures": 0,
            "selects": 0,
            "last_call": None,
            "note": "audit log nenalezen (zatim zadne tool cally)",
        })

    try:
        with audit_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                ts = entry.get("ts", "")
                # Filter on date prefix (ISO format starts with YYYY-MM-DD)
                if not ts.startswith(today_iso):
                    continue
                if entry.get("error"):
                    failures += 1
                tool = entry.get("tool", "")
                if tool in ("insert_row", "bulk_insert_rows", "bulk_insert_akce"):
                    # Pre bulk pricitame inserted z result, ne 1
                    res = entry.get("result") or {}
                    inserts += int(res.get("inserted") or 0) or 1
                elif tool in ("query_table", "get_row", "count_rows", "describe_table"):
                    selects += 1
                else:
                    other += 1
                if not last_call_iso or ts > last_call_iso:
                    last_call_iso = ts
    except Exception as e:
        logger.warning(f"audit_summary: read failed: {e}")
        return JSONResponse({
            "ok": False,
            "error": "audit_read_failed",
            "message": str(e),
        }, status_code=500)

    last_call_short = None
    if last_call_iso:
        try:
            last_call_short = datetime.fromisoformat(
                last_call_iso.replace("Z", "+00:00")
            ).astimezone().strftime("%H:%M")
        except Exception:
            last_call_short = last_call_iso[11:16]  # crude HH:MM extract

    return JSONResponse({
        "ok": True,
        "date": today_iso,
        "inserts": inserts,
        "failures": failures,
        "selects": selects,
        "other": other,
        "last_call": last_call_short,
    })


# ── Lifespan: SQL connection init on startup, close on shutdown ────────

@asynccontextmanager
async def lifespan(app):
    logger.info("EUROSOFT MCP server startup — pripojuji SQL Server...")
    try:
        init_connection()
    except Exception as e:
        logger.error(f"SQL Server connection failed at startup: {e}")
        # Not raising — server starts anyway, individual tool calls will retry
    logger.info(f"Listening on {settings.listen_host}:{settings.listen_port}")
    logger.info(f"Whitelisted tables: {sorted(TOOL_HANDLERS.keys())}")
    yield
    logger.info("EUROSOFT MCP server shutdown — zavirma SQL connection...")
    close_connection()


# ── Starlette ASGI app ─────────────────────────────────────────────────

app = Starlette(
    debug=False,
    routes=[
        Route("/health", endpoint=health, methods=["GET"]),
        Route("/healthz", endpoint=health, methods=["GET"]),
        Route("/audit/summary", endpoint=audit_summary, methods=["GET"]),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ],
    middleware=[
        Middleware(BearerAuthMiddleware),
    ],
    lifespan=lifespan,
)


# ── Entry point ────────────────────────────────────────────────────────

def main():
    if not settings.mcp_api_key:
        logger.warning(
            "MCP_API_KEY env var neni nastaveny! Server bude vracet 500 na vsech pozadavcich. "
            "Nastav MCP_API_KEY pred startem."
        )
    if not settings.sql_password:
        logger.warning(
            "EUROSOFT_SQL_PASSWORD env var neni nastaveny! SQL connection se nepripoji. "
            "Nastav EUROSOFT_SQL_PASSWORD pred startem."
        )

    uvicorn.run(
        app,
        host=settings.listen_host,
        port=settings.listen_port,
        log_level=os.getenv("MCP_LOG_LEVEL", "info").lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
