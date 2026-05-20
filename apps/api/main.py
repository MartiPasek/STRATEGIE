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
# Fix I (20.5. vecer, Marti's "NE-anonymous py rows" catch):
# middleware lookup user_login_name + tenant_name z cookie 'user_id'.
# LRU cache pro performance (1 DB query per unique user_id).
from functools import lru_cache as _lru_cache_fi


@_lru_cache_fi(maxsize=100)
def _fi_user_context(user_id: int) -> tuple[str | None, int | None, str | None]:
    """Lookup (login_name, tenant_id, tenant_name) pro user_id z cookie.

    Returns (None, None, None) pri ANY chybe — middleware nikdy nepadne.
    Cached napric requesty (max 100 unique users).
    """
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            u = cs.query(User).filter(User.id == user_id).one_or_none()
            if not u:
                return (None, None, None)
            login = (
                getattr(u, "short_name", None)
                or getattr(u, "first_name", None)
                or f"#{u.id}"
            )
            tenant_id = getattr(u, "last_active_tenant_id", None)
            tenant_name = None
            if tenant_id:
                from modules.core.infrastructure.models_core import Tenant
                t = cs.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
                if t:
                    tenant_name = (
                        getattr(t, "tenant_code", None)
                        or getattr(t, "name", None)
                    )
            return (login, tenant_id, tenant_name)
        finally:
            cs.close()
    except Exception:
        return (None, None, None)


def _fj_parse_int_header(request: Request, name: str) -> int | None:
    """Fix J (20.5. vecer): parse X-Erp-Core-Id / X-Erp-Comp-Def-Id headers.

    Frontend posila per-fetch context z window._erpActiveCoreId / _erpActiveCompDefId.
    Returns None pri ANY chybe (header missing, not int, etc.).
    """
    try:
        raw = request.headers.get(name)
        if not raw:
            return None
        return int(raw)
    except Exception:
        return None


def _fi_extract_user_context(request: Request) -> dict[str, object | None]:
    """Extract user identity z request cookie. Vraci dict pro log_event kwargs.

    Skip pokud cookie chybi (anonymous request, login flow, etc.).
    """
    try:
        uid_str = request.cookies.get("user_id")
        if not uid_str:
            return {"user_id": None, "user_login_name": None,
                    "tenant_id": None, "tenant_name": None}
        uid = int(uid_str)
        login, tid, tname = _fi_user_context(uid)
        return {
            "user_id": uid,
            "user_login_name": login,
            "tenant_id": tid,
            "tenant_name": tname,
        }
    except Exception:
        return {"user_id": None, "user_login_name": None,
                "tenant_id": None, "tenant_name": None}


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.state.request_id = request_id
    set_request_id(request_id)

    # Fix E+ (20.5. vecer): capture request body PRED call_next + replay
    # receive() aby handler mohl re-read.
    _mw_request_body = b""
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            _mw_request_body = await request.body()
            async def _mw_receive():
                return {
                    "type": "http.request",
                    "body": _mw_request_body,
                    "more_body": False,
                }
            request._receive = _mw_receive
        except Exception:
            _mw_request_body = b"<body read failed>"

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
            _fi_ctx = _fi_extract_user_context(request)
            # Fix J (20.5. vecer): read X-Erp-Core-Id + X-Erp-Comp-Def-Id headers
            _fj_core_id = _fj_parse_int_header(request, "X-Erp-Core-Id")
            _fj_comp_def_id = _fj_parse_int_header(request, "X-Erp-Comp-Def-Id")
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
                # Fix I — NE-anonymous py rows (Marti's doctrine 16.5.):
                user_login_name=_fi_ctx["user_login_name"],
                user_id=_fi_ctx["user_id"],
                tenant_name=_fi_ctx["tenant_name"],
                tenant_id=_fi_ctx["tenant_id"],
                # Fix J (20.5. vecer): grid/form attribution z headers
                core_id=_fj_core_id,
                comp_def_id=_fj_comp_def_id,
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

    # Fix E+ — capture response body pro 4xx/5xx (rebuild Response).
    _mw_response_body_preview = ""
    _mw_response_body_size = 0
    try:
        _status_pre = getattr(response, "status_code", 0) or 0
        if _status_pre >= 400 and hasattr(response, "body_iterator"):
            _mw_response_chunks = []
            _mw_acc_size = 0
            async for _chunk in response.body_iterator:
                _mw_response_chunks.append(_chunk)
                _mw_acc_size += len(_chunk)
                if _mw_acc_size > 20000:
                    break
            _mw_response_bytes = b"".join(_mw_response_chunks)
            _mw_response_body_size = len(_mw_response_bytes)
            try:
                _mw_response_body_preview = _mw_response_bytes[:5000].decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                _mw_response_body_preview = "<decode failed>"
            from starlette.responses import Response as _MwResponse
            response = _MwResponse(
                content=_mw_response_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
    except Exception:
        pass

    # Fix E (20.5. vecer, extends Fix C): 4xx+5xx response logger.
    # Controlled responses (FastAPI Pydantic 422, sql_execute_failed
    # JSONResponse(500), 404 stub) procházejí jako successful response
    # nikoli Exception → Fix C je nechytl. Tady checkneme status_code
    # po call_next a logujeme každý non-2xx (skip auth gate noise).
    try:
        _status = getattr(response, "status_code", 0) or 0
        if _status >= 400:
            # Skip auth gate 401 (login flow expected, noise)
            _path = request.url.path
            _skip = _status == 401 and _path.startswith("/api/v1/auth/")
            if not _skip:
                try:
                    from core.log_queue import log_event as _log_event_fe
                    _fi_ctx_e = _fi_extract_user_context(request)
                    # Fix J (20.5. vecer): read X-Erp-Core-Id headers
                    _fj_core_e = _fj_parse_int_header(request, "X-Erp-Core-Id")
                    _fj_comp_e = _fj_parse_int_header(request, "X-Erp-Comp-Def-Id")
                    _log_event_fe(
                        level="error" if _status >= 500 else "warn",
                        source="py",
                        module_id=f"middleware:{_path}",
                        message=(
                            f"HTTP {_status} response from "
                            f"{request.method} {_path}"
                        ),
                        request_id=request_id,
                        fastapi_endpoint=_path,
                        http_method=request.method,
                        http_status=_status,
                        # Fix I — NE-anonymous py rows (Marti's doctrine 16.5.):
                        user_login_name=_fi_ctx_e["user_login_name"],
                        user_id=_fi_ctx_e["user_id"],
                        tenant_name=_fi_ctx_e["tenant_name"],
                        tenant_id=_fi_ctx_e["tenant_id"],
                        # Fix J (20.5. vecer): grid/form attribution z headers
                        core_id=_fj_core_e,
                        comp_def_id=_fj_comp_e,
                        extra={
                            "url_query": str(request.url.query)[:500],
                            "client_host": (
                                request.client.host if request.client else None
                            ),
                            "response_status": _status,
                            "trigger": "fix_e_plus_body_capture",
                            "request_body_preview": (
                                _mw_request_body[:5000].decode("utf-8", errors="replace")
                                if _mw_request_body else ""
                            ),
                            "request_body_size": len(_mw_request_body or b""),
                            "response_body_preview": _mw_response_body_preview,
                            "response_body_size": _mw_response_body_size,
                        },
                    )
                except Exception:
                    import sys as _sys_fe
                    import traceback as _tb_fe
                    try:
                        _sys_fe.stderr.write(
                            f"[Fix E middleware] log_event failed: "
                            f"{_tb_fe.format_exc()}\n"
                        )
                    except Exception:
                        pass
    except Exception:
        pass  # never crash middleware

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
