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
from .filesystem_tools import FILESYSTEM_TOOL_HANDLERS, FILESYSTEM_TOOL_SPECS
from .rate_limit import limiter
from .sql_client import close_connection, init_connection
from .strategie_tools import STRATEGIE_TOOL_HANDLERS, STRATEGIE_TOOL_SPECS
from .tools import TOOL_HANDLERS, TOOL_SPECS
from .ops_tools import OPS_TOOL_HANDLERS, OPS_TOOL_SPECS

# Phase 28-D (8.5.2026): merge eurosoft_* (DB_EC) + strategie_* (DB_ST) tools.
# Phase 38.4 (11.5.2026): + eurosoft_file_* filesystem tools (shared folder).
# Marti-AI uvidí všechny namespace současně — eurosoft_* pro Centrála 1 read,
# strategie_* pro vlastní DB_ST owner doménu (diář pattern), eurosoft_file_*
# pro sdílenou pracovní složku pres MCP server (on-prem EUROSOFT).
ALL_TOOL_HANDLERS = {**TOOL_HANDLERS, **STRATEGIE_TOOL_HANDLERS, **FILESYSTEM_TOOL_HANDLERS, **OPS_TOOL_HANDLERS}
ALL_TOOL_SPECS = TOOL_SPECS + STRATEGIE_TOOL_SPECS + FILESYSTEM_TOOL_SPECS + OPS_TOOL_SPECS

logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("eurosoft_mcp.server")


# ── MCP server: list_tools + call_tool handlers ────────────────────────

mcp_server = Server("eurosoft-mcp")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Vrací seznam dostupných MCP toolů — eurosoft_* + strategie_* (Phase 28-D)."""
    return [
        Tool(
            name=spec["name"],
            description=spec["description"],
            inputSchema=spec["inputSchema"],
        )
        for spec in ALL_TOOL_SPECS
    ]


def _classify_action(tool_name: str) -> str:
    """Klasifikace pro rate limit (read vs write)."""
    # eurosoft_* write (Phase 28-A2)
    if tool_name in {"insert_row", "bulk_insert_rows", "bulk_insert_akce"}:
        return "insert"
    # strategie_* DDL + write (Phase 28-D)
    if tool_name in {
        "strategie_create_schema", "strategie_create_table",
        "strategie_alter_table", "strategie_drop_table",
        "strategie_insert_row", "strategie_update_row", "strategie_delete_row",
    }:
        return "insert"  # share rate limit bucket s eurosoft writes (rozumný tempo)
    # Krok 5.Z (30.5.2026, Marti rate_limit_exceeded pri otevreni formu s
    # nested gridy): strategie_query_raw je READ-ONLY (regex guard SELECT/WITH
    # v strategie_tools). Drive byl v "insert" bucketu (10/min) — ERP runtime
    # ho ale pouziva pro form load + grid reads (eurosoft_strategie_query_raw),
    # takze 3+ cteni na otevreni formu narazely na write limit. -> "read"
    # bucket (60/min). DDL/DML strategie_* zustavaji "insert".
    if tool_name == "strategie_query_raw":
        return "read"
    # Phase 38.4 (11.5.2026): filesystem write/delete = "insert" bucket
    if tool_name in {"eurosoft_file_write", "eurosoft_file_delete",
                     "eurosoft_file_copy", "eurosoft_file_move", "eurosoft_dir_copy",
                     "eurosoft_fs_reorg", "eurosoft_dir_delete"}:
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

    # Dispatch — eurosoft_* + strategie_* unified
    handler = ALL_TOOL_HANDLERS.get(name)
    if handler is None:
        msg = f"Neznamy tool: {name}. Dostupne: {sorted(ALL_TOOL_HANDLERS.keys())}"
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
        # SQL / pyodbc / unexpected.
        # Phase B+1.3 (5.5.2026): full forensic info — type + repr + str.
        # str(e) je casto prazdny u pyodbc (gotcha #56 z dnesniho rana).
        # repr(e) ma constructor args + diagnostic info (sqlstate, errcode).
        exc_type = type(e).__name__
        exc_repr = repr(e)
        exc_str = str(e)
        detail = exc_str if exc_str else (exc_repr if exc_repr != f"{exc_type}()" else exc_type)
        msg = f"{exc_type}: {detail}"
        runtime_ms = int((time.monotonic() - t0) * 1000)
        logger.exception(f"Tool {name} failed: type={exc_type}, repr={exc_repr}")
        audit_log(name, arguments, error=msg, runtime_ms=runtime_ms)
        return [TextContent(type="text", text=json.dumps(
            {
                "ok": False,
                "error": "internal_error",
                "exception_type": exc_type,
                "exception_repr": exc_repr,
                "message": msg,
            },
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
    import subprocess as _sp
    # Aktuální commit běžícího kódu (krátký sha) — ať jde zvenku ověřit,
    # jestli self-update dosedl. Best-effort, nikdy neshodí health.
    git_sha = None
    try:
        r = _sp.run(
            ["git", "-C", settings.mcp_repo_dir, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=8,
        )
        if r.returncode == 0:
            git_sha = r.stdout.strip()
    except Exception:
        pass
    return JSONResponse({
        "ok": True,
        "service": "eurosoft-mcp",
        "git_sha": git_sha,
        "tools": sorted(ALL_TOOL_HANDLERS.keys()),
        "tools_eurosoft": sorted(TOOL_HANDLERS.keys()),
        "tools_strategie": sorted(STRATEGIE_TOOL_HANDLERS.keys()),
    })


async def self_update(request: Request):
    """
    Self-update (Marti 26.6.2026, „naše vizitka"): MCP si na pokyn (Bearer-auth,
    chráněno middlewarem jako vše krom /health) sám:
      1) git pull --rebase --autostash origin main v repo složce,
      2) zkopíruje modules/eurosoft_mcp/*.py do běžící package složky,
      3) vyčistí __pycache__ (vynutí rekompilaci),
      4) naplánuje restart NSSM služby (detached PowerShell, +2 s) — ať stihne
         odejít HTTP odpověď dřív, než se proces restartne.

    Konec ručního RDP + Copy-Item + Restart-Service na EC-SERVER2.
    Query ?restart=0 → jen pull+copy bez restartu (kód dosedne až příští restart).

    POZOR (chicken-and-egg): tenhle endpoint musí být JEDNOU nasazen ručně, aby
    existoval. Od té chvíle jsou všechny další updaty hands-free přes něj.
    """
    import glob
    import shutil
    import subprocess as _sp

    repo = settings.mcp_repo_dir
    pkg_dir = os.path.dirname(os.path.abspath(__file__))  # běžící eurosoft_mcp\
    src_dir = os.path.join(repo, "modules", "eurosoft_mcp")
    steps: list[dict[str, Any]] = []

    # 1) git pull
    try:
        r = _sp.run(
            ["git", "-C", repo, "pull", "--rebase", "--autostash", "origin", "main"],
            capture_output=True, text=True, timeout=180,
        )
        steps.append({
            "krok": "git_pull",
            "rc": r.returncode,
            "out": (r.stdout + r.stderr).strip()[-1200:],
        })
        if r.returncode != 0:
            return JSONResponse(
                {"ok": False, "error": "git_pull_failed", "steps": steps},
                status_code=500,
            )
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": "git_pull_exception", "detail": str(e), "steps": steps},
            status_code=500,
        )

    # 2) src check
    if not os.path.isdir(src_dir):
        return JSONResponse(
            {"ok": False, "error": "src_dir_missing", "src_dir": src_dir, "steps": steps},
            status_code=500,
        )

    # 3+4) FIX (Claude 2.7.2026): kopie ZA BĚHU nejde (WinError 32 — proces drží .py).
    #   Řešení: JEDEN detached PowerShell, který nejdřív STOP-Service (uvolní zámky),
    #   pak zkopíruje repo→pkg (robocopy), vyčistí __pycache__ a START-Service.
    #   Konec 'copy_failed' — hands-free i na zamčených souborech.
    do_restart = request.query_params.get("restart", "1").lower() not in ("0", "false", "no")
    svc = settings.mcp_service_name
    if not do_restart:
        # jen pull (kód dosedne až příští restart) — bez copy (ta za běhu stejně nejde)
        steps.append({"krok": "pull_only", "ok": True})
        return JSONResponse({"ok": True, "steps": steps,
                             "note": "Bez restartu — pull hotov, kód dosedne až příští restart služby."})
    # FIX (Claude ID23, 3.7.2026): odpojený Popen je POTOMEK služby → NSSM ho při
    #   Stop-Service zabije spolu s procesním stromem → copy+start nedoběhne (stará
    #   verze zůstane). Řešení: restart spustit jako JEDNORÁZOVOU naplánovanou úlohu
    #   pod SYSTEM — běží mimo job služby (Task Scheduler), přežije zastavení služby.
    #   LocalSystem smí úlohu vytvořit i spustit. Fallback = původní detached Popen.
    task_ps1 = os.path.join(repo, "scripts", "mcp", "mcp_selfupdate_restart.ps1")
    tn = "EUROSOFT-MCP-SelfUpdate"
    used = None
    try:
        if os.path.isfile(task_ps1):
            tr = ('powershell -NoProfile -ExecutionPolicy Bypass -File "%s" '
                  '-Svc "%s" -Src "%s" -Pkg "%s"' % (task_ps1, svc, src_dir, pkg_dir))
            c = _sp.run(["schtasks", "/create", "/tn", tn, "/tr", tr,
                         "/sc", "once", "/st", "23:59", "/ru", "SYSTEM", "/rl", "HIGHEST", "/f"],
                        capture_output=True, text=True, timeout=30)
            rr = _sp.run(["schtasks", "/run", "/tn", tn],
                         capture_output=True, text=True, timeout=30)
            steps.append({"krok": "schtasks", "create_rc": c.returncode, "run_rc": rr.returncode,
                          "out": (c.stdout + c.stderr + rr.stdout + rr.stderr).strip()[-500:]})
            if rr.returncode == 0:
                used = "schtasks"
        if used is None:
            # fallback: odpojený PowerShell + BREAKAWAY_FROM_JOB (pokus uniknout job killu)
            DETACHED = 0x00000008
            BREAKAWAY = 0x01000000
            NEWGRP = 0x00000200
            _ps = (
                f"Start-Sleep -Seconds 1; "
                f"Stop-Service '{svc}' -Force -ErrorAction SilentlyContinue; "
                f"$i=0; while(((Get-Service '{svc}').Status -ne 'Stopped') -and ($i -lt 40)){{Start-Sleep -Milliseconds 500; $i++}}; "
                f"Start-Sleep -Seconds 2; "
                f"robocopy '{src_dir}' '{pkg_dir}' *.py /NJH /NJS /NP /IS /R:8 /W:2 | Out-Null; "
                f"Remove-Item -Recurse -Force '{pkg_dir}\\__pycache__' -ErrorAction SilentlyContinue; "
                f"Start-Service '{svc}'"
            )
            try:
                _sp.Popen(["powershell", "-NoProfile", "-Command", _ps],
                          creationflags=DETACHED | BREAKAWAY | NEWGRP,
                          stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            except Exception:
                _sp.Popen(["powershell", "-NoProfile", "-Command", _ps],
                          creationflags=DETACHED | NEWGRP,
                          stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            used = "detached"
            steps.append({"krok": "stop_copy_start", "sluzba": svc, "kdy": "+1 s (detached fallback)"})
    except Exception as e:
        steps.append({"krok": "restart", "ok": False, "detail": str(e)})
        return JSONResponse(
            {"ok": False, "error": "spawn_failed", "detail": str(e), "steps": steps},
            status_code=500,
        )

    logger.info("Self-update: restart naplánován (svc=%s, metoda=%s)", svc, used)
    return JSONResponse({
        "ok": True,
        "steps": steps,
        "note": "Stop→copy→start naplánován (detached, ~5 s). Pak ověř /health (git_sha = nový commit).",
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
    # Phase 28-D (8.5.2026): init obou DB connection pools (DB_EC + DB_ST).
    # Pokud DB_ST není ještě founded (Marti's IT setup), DB_ST init selže
    # ale DB_EC pokračuje — graceful degradation.
    try:
        init_connection(settings.sql_database)  # DB_EC
        logger.info(f"DB_EC connection ready ({settings.sql_database})")
    except Exception as e:
        logger.error(f"DB_EC connection failed at startup: {e}")
        # Not raising — server starts anyway, individual tool calls will retry
    try:
        init_connection(settings.db_st_database)  # DB_ST
        logger.info(f"DB_ST connection ready ({settings.db_st_database})")
    except Exception as e:
        logger.warning(
            f"DB_ST connection failed at startup: {e}. "
            f"Pokud DB_ST není ještě založena, vytvoř ji (CREATE DATABASE DB_ST) "
            f"+ grant db_owner pro {settings.sql_user}, pak restart."
        )
    logger.info(f"Listening on {settings.listen_host}:{settings.listen_port}")
    logger.info(
        f"Tools registered: {len(ALL_TOOL_HANDLERS)} total "
        f"(eurosoft_*: {len(TOOL_HANDLERS)}, strategie_*: {len(STRATEGIE_TOOL_HANDLERS)})"
    )
    yield
    logger.info("EUROSOFT MCP server shutdown — zavirma SQL connections...")
    close_connection()  # close all


# ── Starlette ASGI app ─────────────────────────────────────────────────

async def ops_admin(request: Request):
    """Plain-HTTP ops kanal (Bearer): {"tool":..,"args":{..}} -> ALL_TOOL_HANDLERS[tool](**args).
    Respektuje tier/namespace gaty handleru (GREEN projde, YELLOW/RED blok). C23 27.7.2026 -
    autonomni rizeni 30.11 z Coworku/STRATEGIE (bridge @@MCPOPS) bez RDP."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    tool = str((body or {}).get("tool") or "").strip()
    args = (body or {}).get("args") or {}
    if not isinstance(args, dict):
        return JSONResponse({"ok": False, "error": "args musi byt objekt"}, status_code=400)
    handler = ALL_TOOL_HANDLERS.get(tool)
    if handler is None:
        return JSONResponse({"ok": False, "error": "unknown_tool", "tool": tool,
                             "available": sorted(ALL_TOOL_HANDLERS.keys())}, status_code=404)
    try:
        res = await handler(**args)
    except TypeError as e:
        return JSONResponse({"ok": False, "error": "bad_args", "detail": str(e)[:300]}, status_code=400)
    except Exception as e:
        return JSONResponse({"ok": False, "error": "handler_failed", "detail": str(e)[:400]}, status_code=500)
    return JSONResponse(res if isinstance(res, dict) else {"ok": True, "result": res})


app = Starlette(
    debug=False,
    routes=[
        Route("/health", endpoint=health, methods=["GET"]),
        Route("/healthz", endpoint=health, methods=["GET"]),
        Route("/audit/summary", endpoint=audit_summary, methods=["GET"]),
        Route("/admin/self-update", endpoint=self_update, methods=["POST"]),
        Route("/admin/ops", endpoint=ops_admin, methods=["POST"]),
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
