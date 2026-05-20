from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
import logging
import os
import uuid

from core.config import settings
from core.logging import setup_logging
# Phase 38.4 Krok 14g Etapa A (16.5.2026) — DB Log Infrastructure
from core.log_queue import (
    DiagLogHandler,
    set_request_id,
    start_background_drain,
    startup_drain_oneshot,
    stop_background_drain,
)
from modules.ai_processing.api.router import router as ai_processing_router
from modules.conversation.api.router import router as conversation_router
from modules.conversation.api.dm_router import router as dm_router
from modules.auth.api.router import router as auth_router
from modules.memory.api.router import router as memory_router
from modules.projects.api.router import router as projects_router
from modules.personas.api.router import router as personas_router
from modules.rag.api.router import router as rag_router
from modules.audit.api.router import router as audit_router
from modules.notifications.api.sms_gateway_router import router as sms_gateway_router
from modules.notifications.api.sms_ui_router import router as sms_ui_router
from modules.notifications.api.email_router import router as email_router
from modules.notifications.api.email_ui_router import router as email_ui_router
from modules.notifications.api.notifications_router import router as notifications_router
from modules.notifications.api.consent_router import router as consent_router
from modules.tasks.api.router import router as tasks_router
from modules.thoughts.api.router import router as thoughts_router
from modules.thoughts.api.questions_router import router as marti_questions_router
from modules.admin.api.router import router as admin_router
from modules.notebook.api.router import router as notebook_router
from modules.media.api.router import router as media_router
from modules.md_pyramid.api.router import router as md_pyramid_router
# Phase A (5.5.2026) — STRATEGIE ERP renderer (read-only Centrála 1 jádra)
from modules.erp.api.router import router as erp_router, api_router as erp_api_router

setup_logging()

# Phase 38.4 Krok 14g Etapa A (16.5.2026): attach DiagLogHandler na root logger.
# Vsechny .error()/.warning() across modules tezi do fw.diag_log (source='py').
# Self-reference guard je inside handler.emit (skip strategie.log_queue logger).
_diag_handler = DiagLogHandler(level=logging.WARNING)
logging.getLogger().addHandler(_diag_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Phase 38.4 Krok 14g Etapa A: startup drain + background task.

    Startup:
      - Drain queued JSONL files (z minulych runs / crash recovery).
      - Spawn background task: drain every 5 min.
    Shutdown:
      - Cancel background task + final drain attempt.
    """
    # Startup
    try:
        startup_drain_oneshot()  # sync, blocks until done (fast)
        start_background_drain()  # async, fire-and-forget
    except Exception as exc:
        logging.getLogger(__name__).warning(
            f"[lifespan] log_queue startup hooks failed: {exc}"
        )
    yield
    # Shutdown
    try:
        stop_background_drain()
    except Exception:
        pass


app = FastAPI(
    title="STRATEGIE API",
    description="Modular enterprise AI platform",
    version="0.1.0",
    lifespan=lifespan,
)


# Phase 38.4 Krok 14g Etapa A (16.5.2026): request_id middleware.
# UUID per request, set request.state.request_id + context var pro log_queue,
# add X-Request-Id response header. Frontend JS fetch reads header pro
# correlation s backend log entries.
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.state.request_id = request_id
    set_request_id(request_id)
    response = None
    try:
        response = await call_next(request)
    except Exception as _mw_exc:
        # Fix C (20.5. vecer, Marti's "NIC SE NELOGUJE" diagnostika):
        # globalni exception catch + direct log_event() bypass Python logger
        # machinery. Garantuje ze KAZDA uncaught exception → fw.diag_log row,
        # nezavisle na DiagLogHandler attach state (uvicorn dictConfig moze
        # reset root handlers post setup_logging).
        try:
            import traceback as _tb_mw
            from core.log_queue import log_event as _log_event_mw
            # Walk __cause__ chain pro root cause (analog Fix #2.5 v emit)
            _root_mw = _mw_exc
            while getattr(_root_mw, "__cause__", None) is not None:
                _root_mw = _root_mw.__cause__
            _log_event_mw(
                level="error",
                source="py",
                module_id=f"middleware:{request.url.path}",
                message=(
                    f"Uncaught exception {type(_root_mw).__name__}: "
                    f"{str(_root_mw)[:300]}"
                ),
                exception_type=type(_root_mw).__name__,
                traceback_str=_tb_mw.format_exc(),
                request_id=request_id,
                fastapi_endpoint=request.url.path,
                http_method=request.method,
                http_status=500,
                extra={
                    "wrapper_exception_type": type(_mw_exc).__name__,
                    "wrapper_exception_str": str(_mw_exc)[:500],
                    "root_exception_type": type(_root_mw).__name__,
                    "root_exception_str": str(_root_mw)[:500],
                    "url_query": str(request.url.query)[:500],
                    "client_host": request.client.host if request.client else None,
                },
            )
        except Exception:
            # Last resort — never crash middleware
            import sys as _sys_mw
            import traceback as _tb_inner
            try:
                _sys_mw.stderr.write(
                    f"[Fix C middleware] log_event failed: "
                    f"{_tb_inner.format_exc()}\n"
                )
            except Exception:
                pass
        # Re-raise so starlette returns 500 to client
        raise
    finally:
        set_request_id(None)
    try:
        response.headers["X-Request-Id"] = request_id
    except Exception:
        pass
    return response

# Trusted hosts -- ochrana proti Host header attack. V production tam musi
# byt jen app.strategie-system.com. V dev puštíme localhost varianty.
# Hodnoty z env var APP_TRUSTED_HOSTS (comma-separated).
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts_list,
)

app.include_router(ai_processing_router)
app.include_router(conversation_router)
app.include_router(dm_router)
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(projects_router)
app.include_router(personas_router)
app.include_router(rag_router)
app.include_router(audit_router)
app.include_router(sms_gateway_router)
app.include_router(sms_ui_router)
app.include_router(email_router)
app.include_router(email_ui_router)
app.include_router(notifications_router)
app.include_router(consent_router)
app.include_router(tasks_router)
app.include_router(thoughts_router)
app.include_router(notebook_router)
app.include_router(marti_questions_router)
app.include_router(admin_router)
app.include_router(media_router)
app.include_router(md_pyramid_router)  # Phase 24-F UI Pyramida Browser
# Phase A — STRATEGIE ERP (5.5.2026): /erp/* HTML + /api/v1/erp/* JSON
app.include_router(erp_router)
app.include_router(erp_api_router)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
INDEX = os.path.join(static_dir, "index.html")

# B+4 PoC (5.5.2026): mount /static -> apps/api/static/ pro reusable komponenty
# (ErpDataGrid, fonts, atd.). Caddy file_server na cloud APP řeší rovněž; tento
# mount je pojistka pro lokální dev + pokud Caddy /static/* neproxuje k FastAPI.
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(INDEX)


@app.get("/sw.js")
def core_service_worker():
    """B+10+++++ (6.5.2026 odpoledne): Service Worker pro core STRATEGIE
    chat. Served z root /sw.js (ne /static/sw.js) aby scope = /.
    Bez SW Chrome nabídne jen "Přidat na plochu" (bookmark) místo
    "Nainstalovat aplikaci" (standalone PWA bez chromu)."""
    from fastapi import Response
    sw_path = os.path.join(static_dir, "sw.js")
    try:
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = "// SW file not found"
    return Response(
        content=content,
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@app.get("/invite/{token}")
def invite_page(token: str):
    """Pozvánkový link — vrátí stejný index.html, JS se postará o přijetí."""
    return FileResponse(INDEX)


@app.get("/reset/{token}")
def reset_page(token: str):
    """Password reset link — vrátí index.html, JS si token z URL vezme sám."""
    return FileResponse(INDEX)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
