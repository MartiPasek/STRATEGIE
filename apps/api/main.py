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
import modules.erp.api.platak_generator  # platak generator preview/commit (task #44/#45)
from modules.erp.api.carddav import carddav_router, carddav_mgmt_router
from modules.erp.api.directories import dir_router  # Fáze A: systém adresářů dokumentů (18.6.2026)
from modules.erp.api.iso_cockpit import iso_router  # ISO 27001 cockpit — elektronické vedení ISMS (21.6.2026)
from modules.erp.api.bozp_cockpit import bozp_router  # BOZP a PO cockpit — řízení a evidence (2.7.2026)
from modules.erp.api.contract_sign import contract_router  # E-podpis smluv — bilaterální SES + audit (1.7.2026)
from modules.erp.api.bank_api import bank_router  # Univerzální bankovní napojení (Bank API) — Fáze 1 (24.6.2026)
from modules.erp.api.hr_spis import hr_spis_router  # Osobní spis zaměstnance — HR pohled + self-service (1.7.2026)

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

    Phase HA-1 (23.5.2026, Marti's "production safety"): lifespan log_event
    pro restart audit. Instance identity z env (STRATEGIE_INSTANCE_NAME,
    UVICORN_PORT). Logováno do fw.diag_log level=info, source=py,
    module_id=api.lifecycle.
    """
    import time as _t_lifespan
    import socket as _sock_lifespan
    import subprocess as _sp_lifespan

    _startup_ts = _t_lifespan.time()
    _instance_name = os.environ.get("STRATEGIE_INSTANCE_NAME", "primary")
    # Phase HA-1 hotfix (23.5.2026): port resolve priority:
    #   1. UVICORN_PORT env (Phase HA-1 secondary explicit)
    #   2. --port argument v sys.argv (Marti's existing primary NSSM config)
    #   3. fallback 8001 (uvicorn default)
    import sys as _sys_lifespan
    _port = int(os.environ.get("UVICORN_PORT", 0)) or 0
    if not _port:
        try:
            _argv = _sys_lifespan.argv
            for i, arg in enumerate(_argv):
                if arg == "--port" and i + 1 < len(_argv):
                    _port = int(_argv[i + 1])
                    break
                if arg.startswith("--port="):
                    _port = int(arg.split("=", 1)[1])
                    break
        except (ValueError, IndexError):
            pass
    if not _port:
        _port = 8001  # last-resort uvicorn default
    _pid = os.getpid()
    _hostname = _sock_lifespan.gethostname()
    _git_sha = "unknown"
    try:
        _git_sha = _sp_lifespan.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            stderr=_sp_lifespan.DEVNULL,
            timeout=2,
        ).decode().strip()
    except Exception:
        pass

    # Startup
    try:
        startup_drain_oneshot()  # sync, blocks until done (fast)
        start_background_drain()  # async, fire-and-forget
    except Exception as exc:
        logging.getLogger(__name__).warning(
            f"[lifespan] log_queue startup hooks failed: {exc}"
        )

    # Phase HA-1: STARTUP audit (after drain bootstrap, before yield)
    try:
        from core.log_queue import log_event as _log_event_startup
        _log_event_startup(
            level="info",
            source="py",
            module_id="api.lifecycle",
            message=f"STRATEGIE-API started — instance={_instance_name} port={_port} pid={_pid}",
            extra={
                "event": "startup",
                "instance": _instance_name,
                "port": _port,
                "pid": _pid,
                "hostname": _hostname,
                "git_sha": _git_sha,
            },
        )
    except Exception as exc:
        logging.getLogger(__name__).warning(
            f"[lifespan] startup log_event failed: {exc}"
        )

    # Phase API Versioned Routing Etapa G (23.5.2026): jen primary instance
    # updatuje fw.api_version SET released_at=NOW(), git_sha=<HEAD>.
    # Secondary (STRATEGIE-API-B) nesmi prepisovat - jeji datum se updatuje
    # az pri promotion (api_version_promote.ps1).
    # Marti's "drz jednoduchost": Restart-Service triggeruje auto-update
    # bez wrapperu deploy_current.ps1.
    if _instance_name == "primary":
        try:
            from core.config import settings as _settings_av
            import psycopg2 as _psycopg2_av
            _av_url = _settings_av.database_url or _settings_av.database_data_url
            if _av_url:
                _av_url = _av_url.replace(
                    "postgresql+psycopg2://", "postgresql://"
                ).replace("postgresql+asyncpg://", "postgresql://")
                _full_git_sha = "unknown"
                try:
                    _full_git_sha = _sp_lifespan.check_output(
                        ["git", "rev-parse", "HEAD"],
                        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        stderr=_sp_lifespan.DEVNULL,
                        timeout=2,
                    ).decode().strip()
                except Exception:
                    pass
                _av_conn = _psycopg2_av.connect(_av_url)
                _av_conn.autocommit = True
                _av_cur = _av_conn.cursor()
                _av_cur.execute(
                    """
                    UPDATE fw.api_version
                    SET released_at = NOW(), git_sha = %s
                    WHERE version_code = 'current'
                    """,
                    (_full_git_sha,),
                )
                _av_cur.close()
                _av_conn.close()
        except Exception as exc:
            logging.getLogger(__name__).warning(
                f"[lifespan] api_version auto-update failed: {exc}"
            )

    # Pozn. 6.6.2026: one-off DDL hook (users.login_name nullable + partial
    # unique + CHECK) zde bezel a byl po uspesne aplikaci odstranen.
    # Pattern pro priste: kdyz Marti nema VPN, DDL na public.* jde pres
    # idempotentni lifespan hook (API bezi jako strategie = owner) + deploy.

    # Marti 11.6.2026: SMS audit — sloupce pro realny stav z sms-gate.app relaye.
    try:
        from sqlalchemy import text as _t_sms
        from core.database_data import get_data_session as _gs_sms
        _ds_sms = _gs_sms()
        try:
            _ds_sms.execute(_t_sms(
                "ALTER TABLE public.sms_outbox "
                "ADD COLUMN IF NOT EXISTS gate_msg_id varchar(80), "
                "ADD COLUMN IF NOT EXISTS gate_state varchar(30)"))
            # Marti 11.6.: audit KAŽDÉHO pokusu brány doručit příchozí SMS na server
            _ds_sms.execute(_t_sms(
                "CREATE TABLE IF NOT EXISTS fw.sms_inbound_hit ("
                " id bigserial PRIMARY KEY, hit_at timestamptz NOT NULL DEFAULT now(),"
                " endpoint varchar(40), authed boolean, from_phone varchar(40),"
                " body_preview varchar(120), client_ip varchar(60), note varchar(200))"))
            # Marti 11.6.: krátkodobý veřejný PDF (generátor dokumentů → odkaz pro appku)
            _ds_sms.execute(_t_sms(
                "CREATE TABLE IF NOT EXISTS fw.doc_pubfile ("
                " nonce varchar(48) PRIMARY KEY, fname varchar(160), mime varchar(60),"
                " pdf bytea, created_by int, created_at timestamptz NOT NULL DEFAULT now())"))
            _ds_sms.commit()
        finally:
            _ds_sms.close()
    except Exception as exc:
        logging.getLogger(__name__).warning(f"[lifespan] sms_outbox gate cols failed: {exc}")

    # Pozn. 6.7.2026: mode zrcadel (DEL/RO/RW) na fw.mirror_job přidán PŘES MOST (Marti-AI
    # vlastní fw.mirror_job → bridge ALTER; lifespan jako strategie by NEsměl). Vlastnictví:
    # tenant.oz_mirror_def = strategie (→ _ensure_def_table/lifespan), fw.mirror_job = Marti-AI (→ bridge).

    # Pavel CRM (Kristy 29.6.2026): demo rozesilka + tracking otevreni emailu.
    try:
        from sqlalchemy import text as _t_trk
        from core.database_data import get_data_session as _gs_trk
        _ds_trk = _gs_trk()
        try:
            _ds_trk.execute(_t_trk(
                "CREATE TABLE IF NOT EXISTS mod.crm_email_track ("
                " id bigserial PRIMARY KEY,"
                " token varchar(48) NOT NULL UNIQUE,"
                " firma_id int,"
                " firma varchar(200),"
                " recipient varchar(200),"
                " template_code varchar(32),"
                " demo boolean NOT NULL DEFAULT true,"
                " requested_by varchar(40),"
                " sent_at timestamptz NOT NULL DEFAULT now(),"
                " opened_at timestamptz,"
                " open_count int NOT NULL DEFAULT 0,"
                " opened_ip varchar(60))"))
            _ds_trk.execute(_t_trk(
                "ALTER TABLE mod.crm_email_track "
                "ADD COLUMN IF NOT EXISTS opened_ua varchar(300)"))
            _ds_trk.commit()
        finally:
            _ds_trk.close()
    except Exception as exc:
        logging.getLogger(__name__).warning(f"[lifespan] crm_email_track DDL failed: {exc}")

    # Pozn. 5.7.2026: one-off uklid public.documents (621 dup+temp radku, ~150 MB)
    # zde bezel pres owner roli a byl po uspesnem behu odstranen (smazano ~623 radku).

    # Marti 5.7.2026: background schedulery (docházka sync + plánovač zrcadel) běží
    # JEN na primáru. Blue-green secondary (adresář STRATEGIE-prev / STRATEGIE_INSTANCE_NAME
    # != primary) je den starý snímek → nesmí klofat mirror joby (bug „B krade joby ->
    # neznámý job", memory oz-mirror/saldo) ani dvojitě mirrorovat docházku do Centrály.
    # POZOR (Marti 5.7.2026): sekundár detekuj JEN podle adresáře (STRATEGIE-prev).
    # NE podle STRATEGIE_INSTANCE_NAME — primár ho může mít nastavený na jiný název
    # (NSSM), a to by omylem vyplo plánovač i na primáru (stalo se → mirror stál).
    _repo_base_ls = os.path.basename(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    _is_secondary_ls = ("prev" in _repo_base_ls.lower())
    if _is_secondary_ls:
        logging.getLogger(__name__).warning(
            "[lifespan] secondary (%s) — background schedulery (att_sync, mirror) VYPNUTY",
            _repo_base_ls)
    else:
        # Marti 9.6.2026: zivy 30s tik dochazky — mirror dnesku z Centraly.
        try:
            from modules.erp.api.router import _att_sync_start as _att_start
            _att_start()
        except Exception as exc:
            logging.getLogger(__name__).warning(f"[lifespan] att_sync start failed: {exc}")

        # Marti 20.6.2026: planovac zrcadel (ridici centrum, automaticky zivot).
        try:
            from modules.erp.api.router import _mirror_sched_start as _mir_start
            _mir_start()
        except Exception as exc:
            logging.getLogger(__name__).warning(f"[lifespan] mirror_sched start failed: {exc}")

    # Marti 20.6.2026: vault klic samobootstrap uz pri startu (nesmi cekat na klik).
    try:
        from modules.erp.api.router import _vault_fernet as _vf_boot
        _vf_boot()
    except Exception as exc:
        logging.getLogger(__name__).warning(f"[lifespan] vault bootstrap failed: {exc}")

    yield

    # Phase HA-1: SHUTDOWN audit (before background drain stop)
    try:
        from core.log_queue import log_event as _log_event_shutdown
        _uptime = int(_t_lifespan.time() - _startup_ts)
        _log_event_shutdown(
            level="info",
            source="py",
            module_id="api.lifecycle",
            message=f"STRATEGIE-API stopping — instance={_instance_name} port={_port} uptime={_uptime}s",
            extra={
                "event": "shutdown",
                "instance": _instance_name,
                "port": _port,
                "pid": _pid,
                "uptime_seconds": _uptime,
            },
        )
    except Exception:
        pass

    # Shutdown
    try:
        stop_background_drain()
    except Exception:
        pass
    try:
        from modules.erp.api.router import _att_sync_stop_now as _att_stop
        _att_stop()
    except Exception:
        pass
    try:
        from modules.erp.api.router import _mirror_sched_stop_now as _mir_stop
        _mir_stop()
    except Exception:
        pass


app = FastAPI(
    title="STRATEGIE API",
    description="Modular enterprise AI platform",
    version="0.1.0",
    lifespan=lifespan,
)


# Phase HA-1 (23.5.2026, Marti's "production safety"): Raw liveness endpoint
# pro Caddy load balancer health probes. NO auth (Caddy probe nemá cookie),
# NO DB query (jen lightweight ping). Caddy bude polling this endpoint —
# pokud non-200, instance removed z upstream pool.
#
# Distinct od /api/v1/erp/health (parent gated, full tenant context).
# /api/v1/health = liveness only (am I alive?).
def _resolve_uvicorn_port() -> int:
    """Phase HA-1 hotfix: port resolve priority — env UVICORN_PORT,
    sys.argv --port, fallback 8001. Marti's existing NSSM config uses
    --port arg, no env var.
    """
    import sys as _sys_port
    _p = int(os.environ.get("UVICORN_PORT", 0)) or 0
    if _p:
        return _p
    try:
        _argv = _sys_port.argv
        for i, arg in enumerate(_argv):
            if arg == "--port" and i + 1 < len(_argv):
                return int(_argv[i + 1])
            if arg.startswith("--port="):
                return int(arg.split("=", 1)[1])
    except (ValueError, IndexError):
        pass
    return 8001  # uvicorn default


_API_SHA_CACHE: dict = {}


def _api_git_sha() -> str:
    if "v" in _API_SHA_CACHE:
        return _API_SHA_CACHE["v"]
    import subprocess as _sp
    v = "unknown"
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        v = _sp.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                             stderr=_sp.DEVNULL, timeout=2).decode().strip()
    except Exception:
        v = "unknown"
    _API_SHA_CACHE["v"] = v
    return v


@app.get("/api/v1/api-info")
def api_info() -> dict:
    """Na jakém API to běží — primary vs starý blue-green secondary. Bez auth."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base = os.path.basename(root)
    inst = os.environ.get("STRATEGIE_INSTANCE_NAME", "primary")
    stale = ("prev" in base.lower()) or (inst.lower() != "primary")
    # Prostredi + databaze = zdroj pravdy pro UI indikator (na jake DB bezime).
    env = (os.environ.get("STRATEGIE_ENV", "") or "prod").lower()
    db_url = os.environ.get("DATABASE_DATA_URL", "") or ""
    db_name = db_url.rsplit("/", 1)[-1].split("?")[0] if "/" in db_url else ""
    is_apid = (env == "apid") or (os.environ.get("STRATEGIE_READONLY_OUTBOUND") == "1")
    return {
        "ok": True,
        "instance": inst,
        "port": _resolve_uvicorn_port(),
        "commit": _api_git_sha(),
        "dir": base,
        "stale": stale,
        "env": env,
        "db": db_name,
        "apid": is_apid,
    }


@app.get("/api/v1/health")
def api_health_liveness() -> dict:
    """Phase HA-1: raw liveness probe pro Caddy load balancer.

    Returns:
        {"ok": true, "instance": "primary"|"secondary", "port": int}

    Žádné DB query (rychlost), žádný auth (Caddy nemá cookie).
    """
    return {
        "ok": True,
        "instance": os.environ.get("STRATEGIE_INSTANCE_NAME", "primary"),
        "port": _resolve_uvicorn_port(),
    }


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

    # Fix K (21.5. rano, Marti's "nejsou zde zapsany core_id, comp_def_id,
    # tenant, user" catch): propaguj user+ERP context do contextvars, aby
    # ho deep code (data_source_runner.logger.error, modules.*) dostal pres
    # DiagLogHandler.emit() → log_event() fallback. Bez tohoto: Python error
    # rows v fw.diag_log meli prazdne user_login_name / tenant_name / core_id /
    # comp_def_id (jen middleware-level logger calls meli kontext).
    try:
        from core.log_queue import set_user_context as _fk_set_user_ctx
        _fk_user_ctx = _fi_extract_user_context(request)
        _fk_core_id = _fj_parse_int_header(request, "X-Erp-Core-Id")
        _fk_comp_def_id = _fj_parse_int_header(request, "X-Erp-Comp-Def-Id")
        _fk_set_user_ctx(
            login_name=_fk_user_ctx["user_login_name"],
            user_id=_fk_user_ctx["user_id"],
            tenant_name=_fk_user_ctx["tenant_name"],
            core_id=_fk_core_id,
            comp_def_id=_fk_comp_def_id,
        )
    except Exception:
        pass  # never crash middleware on context setup

    # HR presence (Marti 5.6.): best-effort detekce „v budově" z firemní IP.
    # Throttle 60 s/uživatel (in-memory) — DB zápis jen občas, request nezdrží.
    try:
        from modules.hr.presence import touch_presence as _hr_touch, client_ip as _hr_ip
        _hr_uid_raw = request.cookies.get("user_id")
        _hr_uid = int(_hr_uid_raw) if (_hr_uid_raw and _hr_uid_raw.isdigit()) else None
        if _hr_uid:
            _hr_touch(_hr_uid, _hr_ip(request), request.headers.get("user-agent"))
    except Exception:
        pass

    # AMBASADOR read-only guard (17.6.2026): role 'ambassador' (externí
    # showcase, Zbynek Zajicek) nesmi NIC zapsat. Blokuj kazdy non-GET na
    # /api (krome /api/v1/erp/app/ambassador/* = demo trezor unlock atd.).
    # Defense-in-depth nad tim, ze ambasador nema zadny write role.
    try:
        _amb_m = (request.method or "GET").upper()
        _amb_p = request.url.path or ""
        # POST cesty, které jsou ve skutečnosti ČTENÍ (PIN/data v těle) — povolené
        # i v ambasadorském režimu: výplatní páska (Martiho), trezor reveal, demo.
        _amb_read_post = ("/app/payslip" in _amb_p or "/app/self-secret/reveal" in _amb_p
                          or "/app/ambassador/" in _amb_p)
        if (_amb_m not in ("GET", "HEAD", "OPTIONS")
                and _amb_p.startswith("/api/")
                and not _amb_read_post
                and not _amb_p.startswith("/api/v1/auth/")):
            from modules.erp.api.router import _uid_from_token_or_cookie as _amb_uid_fn
            _amb_uid_fn(request)  # nastaví request.state.amb_session při amb/demo režimu
            if bool(getattr(request.state, "amb_session", False)):
                from starlette.responses import JSONResponse as _AmbJSON
                return _AmbJSON(
                    {"ok": False, "error": "ambassador_readonly",
                     "detail": "Prezentační režim je jen pro čtení."},
                    status_code=403)
    except Exception:
        pass  # nikdy neshazuj middleware kvuli guardu

    # EMERGENCY (20.5. vecer, Marti's HTTP/2 protocol error po Fix J deploy):
    # Drop Fix E+ request body capture — request._receive override pattern
    # je nestabilni s Starlette BaseHTTPMiddleware (raises "Unexpected
    # message received: http.request"). Response body capture (post call_next)
    # zustava — safe read-only iterator consume.
    _mw_request_body = b""  # placeholder pro Fix E+ extra dict refs

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
        # Fix K (21.5.): clear user+ERP context po request konci
        try:
            from core.log_queue import set_user_context as _fk_clear_ctx
            _fk_clear_ctx(None, None, None, None, None)
        except Exception:
            pass

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
            # Skip auth gate 401 (login flow expected, noise) +
            # bot scanner traffic (Marti's catch 24.5. 16h: spam warn).
            # Common scanner paths returning 404 → silent skip.
            # POST / 405 → silent skip (bot scan nebo PWA SW noise).
            # Drží doctrine "Bezpečnost přes probuzení, ne přes ticho":
            # signál (4xx z naších endpointů) keep, šum (external scan) drop.
            _path = request.url.path
            _method = request.method
            _is_auth_gate_401 = _status == 401 and _path.startswith("/api/v1/auth/")
            _is_post_root_405 = (
                _status == 405 and _path == "/" and _method == "POST"
            )
            _scanner_paths = (
                "/wp-content/", "/wp-admin/", "/wp-includes/",
                "/wp-login.php", "/xmlrpc.php",
                "/.env", "/.git/", "/.well-known/",
                "/phpmyadmin", "/admin/login", "/admin.php",
                "/robots.txt", "/sitemap.xml", "/favicon.ico",
                "/api/v2/", "/v1/", "/cgi-bin/", "/cms/",
                "/owa/", "/ews/", "/autodiscover/",
                "/.aws/", "/.docker/", "/.kube/",
                "/api/jsonws/", "/console/",
            )
            # Extension-based scanner skip (Marti 31.5. 22h: flood /info.php,
            # /abc.php, /wp-trackback.php, /randkeyword.PhP7…). Aplikace žádné
            # .php/.asp/.jsp/.cgi nepodává → jakákoli 404 na ně = bot scan.
            _scanner_exts = (
                ".php", ".php7", ".phtml", ".asp", ".aspx",
                ".jsp", ".cgi", ".env", ".bak", ".sql", ".ini",
            )
            _plc = _path.lower()
            _is_scanner_noise = _status == 404 and (
                any(_path.startswith(_pat) for _pat in _scanner_paths)
                or any(_plc.endswith(_ext) for _ext in _scanner_exts)
            )
            # Parent-only poll endpointy: non-parent (Pavel) je polluje periodicky
            # a dostava ocekavany 403. Neni to chyba — banner se proste nezobrazi.
            # (Marti 3.6.: stovky 403/min od Pavla z diag-write/pending pollu.)
            # Poll endpointy: nepřihlášený / nescopovaný klient je polluje periodicky
            # a dostává OČEKÁVANÝ 401 (bez session) nebo 403 (bez práv) — není to chyba,
            # jen to zaplaví diag log (Marti 7.7.: „lítá tu tolik warningů, ztrácíme přehled").
            _is_poll_401 = _status == 401 and _path.startswith("/api/")
            _parent_poll_403_paths = (
                "/api/v1/erp/diag-write/pending",
                "/api/v1/erp/app/plan/approvals/users",
                "/api/v1/erp/app/plan/approvals/unapplied",
                "/api/v1/erp/claude-inbox",
                "/api/v1/erp/claude-marti-mail",
                "/api/v1/erp/claude-martiai-msgs",
                "/api/v1/erp/instance/heartbeat",
                "/api/v1/erp/deploy/preview",
            )
            _is_parent_poll_403 = _status == 403 and _path in _parent_poll_403_paths
            _skip = (
                _is_auth_gate_401 or _is_poll_401 or _is_post_root_405
                or _is_scanner_noise or _is_parent_poll_403
            )
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
                            "trigger": "fix_e_response_body_only",
                            # EMERGENCY drop request_body — Starlette ASGI incompat
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

    # HR inventura (5.6.): erární PC/tablet přes prohlížeč. device-id generuje
    # a drží frontend v localStorage a posílá v hlavičce X-Erp-Device-Id
    # (stabilní per-prohlížeč, bez race). Server NEgeneruje — jen čte.
    # Telefony řeší companion appka; tady jen pc/tablet. Throttle v touch_device.
    try:
        _bd_did = (request.headers.get("x-erp-device-id") or "").strip()
        if _bd_did:
            from modules.hr.presence import touch_device as _bd_td, client_ip as _bd_ip
            _bd_uid_raw = request.cookies.get("user_id")
            _bd_uid = int(_bd_uid_raw) if (_bd_uid_raw and _bd_uid_raw.isdigit()) else None
            _bd_ua = (request.headers.get("user-agent") or "").lower()
            _bd_is_phone = ("ipad" not in _bd_ua) and any(
                m in _bd_ua for m in ("mobile", "iphone", "ipod"))
            if _bd_uid and not _bd_is_phone:
                _bd_type = "tablet" if ("ipad" in _bd_ua or "tablet" in _bd_ua) else "pc"
                _bd_td(device_key=_bd_did[:160], device_type=_bd_type, name=None,
                       uid=_bd_uid, ip_str=_bd_ip(request), source="browser")
    except Exception:
        pass

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
app.include_router(carddav_router)  # CardDAV F1.5 — root-level /carddav + /.well-known/carddav
app.include_router(carddav_mgmt_router)  # CardDAV F1.6 — self-service správa tokenů (/api/v1/erp/carddav/*)
app.include_router(dir_router)  # Fáze A: systém adresářů dokumentů (dir_config + resolver)
app.include_router(iso_router)  # ISO 27001 cockpit (elektronické ISMS + e-podpis + auditor portál)
app.include_router(bozp_router)  # BOZP a PO cockpit (řízení dokumentů, rizik, termínů, úrazů)
app.include_router(contract_router)  # E-podpis smluv (SES + audit + externí portál)
app.include_router(bank_router)  # Univerzální bankovní napojení (connection + cert do trezoru) — Fáze 1
app.include_router(hr_spis_router)  # Osobní spis zaměstnance — HR pohled + zaměstnanecký self-service
from modules.act_pipeline.act_router import act_router  # FW Action Pipelines executor (Marti 3.6.)
app.include_router(act_router)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
INDEX = os.path.join(static_dir, "index.html")

# B+4 PoC (5.5.2026): mount /static -> apps/api/static/ pro reusable komponenty
# (ErpDataGrid, fonts, atd.). Caddy file_server na cloud APP řeší rovněž; tento
# mount je pojistka pro lokální dev + pokud Caddy /static/* neproxuje k FastAPI.
app.mount("/static", StaticFiles(directory=static_dir), name="static")


WEB_LANDING = os.path.join(static_dir, "web.html")


@app.get("/")
def index(request: Request):
    """Marti 12.6.2026 — přistávací marketingový web na kořeni domény pro
    návštěvníky (působí líp než holý login). Přihlášený uživatel (cookie
    user_id) nebo příchod s ?return=... (např. z /erp login redirectu) dostane
    chat/login jako dosud → zaměstnancům i PWA (start_url '/') se nic nemění."""
    if request.cookies.get("user_id") or request.query_params:
        return FileResponse(INDEX)
    return FileResponse(WEB_LANDING,
                        media_type="text/html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/chat")
def chat_entry():
    """Vstup do systému (chat/login). Marketing web na / sem odkazuje tlačítkem
    „Vstup do systému". Vždy servíruje chat appku."""
    return FileResponse(INDEX)


@app.get("/mobile")
def mobile_page():
    """Hybridní /mobile — PWA v prohlížeči, obal nativní appky na telefonu
    (WebView + JS most window.STRATEGIE). Web-first obsah, nativní síla
    (Temu model). Marti 6.6.2026 (POC)."""
    return FileResponse(os.path.join(static_dir, "mobile.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/vyroba")
def vyroba_page():
    """Plánovač výroby — interaktivní konzole vedoucího výroby (Dušan + Marek).
    Funguje na desktopu (ERP/CRM) i v mobilu, gate v API endpointech. SAMEORIGIN
    pro iframe embed v ERP. Marti 8.6.2026."""
    return FileResponse(os.path.join(static_dir, "vyroba.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/overit")
def overit_page():
    """🔍 Ověření dodavatele — ARES identita + ADIS DPH status + zveřejněné účty.
    Naše vlastní ověření s razítkem, nezávislé na Heliosu. Marti 6.7.2026 (pro Peťu)."""
    return FileResponse(os.path.join(static_dir, "overit.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/kalkulace")
def kalkulace_page():
    """📐 Kalkulace rozváděčů — engine z DB_EC 2014 (CC×rabat→cena, koef→VKM/Arbeit).
    Kalkulačka + STANDARD šablona + katalog dílů. ACL cockpit. Marti 1.7.2026."""
    return FileResponse(os.path.join(static_dir, "kalkulace.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/privacy")
def privacy_page():
    """Zásady ochrany osobních údajů — povinné pro Google Play / App Store.
    Veřejně dostupné (bez přihlášení). Marti 8.6.2026."""
    return FileResponse(os.path.join(static_dir, "privacy.html"),
                        headers={"Cache-Control": "public, max-age=3600"})


@app.get("/pripojit-schranku")
def connect_mailbox_page():
    """Self-service připojení poštovní schránky (login+heslo → EWS kanál uživatele).
    Session-gated přes API /api/v1/erp/app/connect-mailbox (uid z cookie). Heslo jde
    browser→server, šifruje se, neprochází přes AI. Kristý 25.6.2026."""
    return FileResponse(os.path.join(static_dir, "connect-mailbox.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/connect-mailbox")
def connect_mailbox_page_alias():
    """Alias na /pripojit-schranku (dlaždice appky historicky mířila sem). Marti 1.7.2026."""
    return FileResponse(os.path.join(static_dir, "connect-mailbox.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/ai-uspora")
def ai_uspora_page():
    """Souhrn úspor AI (co AI udělala a ušetřila). Parent-only přes API. Claude ID23 3.7.2026."""
    return FileResponse(os.path.join(static_dir, "ai-uspora.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/ai-buzeni")
def ai_buzeni_page():
    """Týdenní kalendář buzení Marti-AI (kdy se probudí na kontrolu plánů → KLID/ALARM).
    Parent-only přes API /api/v1/erp/app/ai-wake. Claude ID23 3.7.2026."""
    return FileResponse(os.path.join(static_dir, "ai-buzeni.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/vp-zastup")
def vp_zastup_page():
    """Živý pohled připravenosti zakázek pro zástup VP (Petra po dobu Eliščiny dovolené).
    Scope přes API /api/v1/erp/app/vp-zastup = rodiče + Petra (40) + cockpit. Claude ID23 4.7.2026."""
    return FileResponse(os.path.join(static_dir, "vp-zastup.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/eliska")
def eliska_page():
    """Eliščin produkční cockpit — vedení jejích zakázek (fáze, termíny, efektivita,
    další krok). Scope přes API /app/eliska/prehled = rodiče + Eliška (34) + cockpit.
    Marti 5.7.2026 — příprava VP na produkci před návratem Elišky 17.7."""
    return FileResponse(os.path.join(static_dir, "eliska.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/platby")
def platby_page():
    """Platební centrum pro Peťu — návrhy k platbě CZK/EUR (naše saldo z úhrad), platáky, importy,
    výpisy. API /app/platby/navrh = rodiče + Petra (18) + cockpit. Marti 6.7.2026."""
    return FileResponse(os.path.join(static_dir, "platby.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/vp-vez")
def vp_vez_page():
    """VP řídící věž — Eliška jako vedoucí vidí celý pipeline hromad po řešitelích
    (moje / kolegové / celek). API /app/vp/cockpit = rodiče + Eliška (34) + cockpit.
    Marti 5.7.2026 — leader cockpit nad ec_hromada_* mirrory."""
    return FileResponse(os.path.join(static_dir, "vp-vez.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/domeny")
def domeny_page():
    """Review doménového prostředí (domain_env) pro lidi — vidět, porovnat s realitou, ladit.
    Scope přes API /api/v1/erp/app/domeny = rodiče + cockpit. Claude ID23 4.7.2026."""
    return FileResponse(os.path.join(static_dir, "domeny.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/znalosti")
def znalosti_page():
    """Paměť sítě (tenant.knowledge) — vidět jednotky + ladit + mapa očima konkrétní osoby.
    Scope přes API /api/v1/erp/app/znalosti = rodiče + cockpit. Claude ID23 4.7.2026."""
    return FileResponse(os.path.join(static_dir, "znalosti.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/podpisy")
def podpisy_page():
    """Interní správa e-podpisu smluv (finanční/HR okruh). Marti 1.7.2026."""
    return FileResponse(os.path.join(static_dir, "podpisy.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/podpis/{token}")
def podpis_portal_page(token: str):
    """Externí bezloginový podpisový portál (protistrana podepisuje přes token). Marti 1.7.2026."""
    return FileResponse(os.path.join(static_dir, "podpis-portal.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


def _optout_page(msg_html: str, show_form: bool, token: str = "") -> "object":
    from fastapi.responses import HTMLResponse
    form = ""
    if show_form:
        form = (
            '<form method="post" action="/crm/odhlasit/' + token + '" style="margin-top:18px">'
            '<button type="submit" style="background:#c0392b;color:#fff;border:0;'
            'padding:12px 22px;border-radius:8px;font-size:15px;cursor:pointer">'
            'Potvrdit odhlášení</button></form>'
        )
    html = (
        '<!doctype html><html lang="cs"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>Odhlášení z obchodních sdělení</title></head>'
        '<body style="font-family:system-ui,Segoe UI,Arial,sans-serif;background:#f4f6f8;'
        'margin:0;padding:40px 16px;color:#1f2d3d">'
        '<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;'
        'padding:32px;box-shadow:0 2px 12px rgba(0,0,0,.08)">'
        '<h1 style="font-size:20px;margin:0 0 12px">Odhlášení z obchodních sdělení</h1>'
        + msg_html + form +
        '</div></body></html>'
    )
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@app.get("/crm/track/open/{token}")
def crm_track_open(token: str, request: Request):
    """Verejny tracking pixel pro CRM rozesilku (otevreni emailu). Bez auth —
    e-mailovy klient nacte obrazek pri otevreni. Zaznamena opened_at + open_count
    do mod.crm_email_track a vrati 1x1 transparentni GIF. Kristy 29.6.2026."""
    try:
        from sqlalchemy import text as _t_to
        from core.database_data import get_data_session as _gs_to
        _ip = (request.client.host if request and request.client else None)
        _ua = ((request.headers.get("user-agent") if request else None) or "")
        _ds = _gs_to()
        try:
            # Grace okno: nacteni pixelu do 5 s od odeslani = okamzite automaticke
            # stazeni (dorucovaci scan / auto-download), NE skutecne otevreni ->
            # opened_at se v tom okne nenastavi. Realna otevreni chodi >~8 s.
            # open_count pocita vsechny zasahy (raw), opened_ua/ip = prvni zasah.
            _ds.execute(_t_to(
                "UPDATE mod.crm_email_track SET open_count = open_count + 1,"
                " opened_ip = COALESCE(opened_ip, :ip),"
                " opened_ua = COALESCE(opened_ua, :ua),"
                " opened_at = COALESCE(opened_at,"
                "   CASE WHEN now() - sent_at >= interval '5 seconds'"
                "        THEN now() ELSE NULL END)"
                " WHERE token = :t"),
                {"t": (token or "")[:48], "ip": (_ip or "")[:60],
                 "ua": (_ua or "")[:300]})
            _ds.commit()
        finally:
            _ds.close()
    except Exception:
        pass
    from fastapi import Response as _Resp
    _gif = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
            b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
            b"\x00\x00\x02\x02D\x01\x00;")
    return _Resp(content=_gif, media_type="image/gif",
                 headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})


@app.get("/crm/odhlasit/{token}")
def crm_odhlasit_get(token: str):
    """Verejna odhlasovaci stranka (z patičky obchodniho mailu). GET jen potvrzovaci
    tlacitko (POST teprve odhlasi) — aby nahledove roboty mailu neodhlasily omylem.
    Marti & Claude-24, 18.6.2026."""
    from modules.erp.api.router import crm_optout_parse_token
    parsed = crm_optout_parse_token(token)
    if not parsed:
        return _optout_page("<p>Tento odhlašovací odkaz je neplatný nebo poškozený. "
                            "Pokud si přejete odhlásit, odpovězte prosím na náš e-mail.</p>",
                            show_form=False)
    email_norm, _firma = parsed
    return _optout_page(
        "<p>Chystáte se odhlásit adresu <b>" + email_norm + "</b> z dalších obchodních "
        "sdělení. Pro potvrzení klikněte níže.</p>", show_form=True, token=token)


@app.post("/crm/odhlasit/{token}")
def crm_odhlasit_post(token: str):
    """Potvrzeni odhlaseni -> zapis do mod.crm_email_optout (idempotentne)."""
    from modules.erp.api.router import crm_optout_parse_token, crm_optout_record
    parsed = crm_optout_parse_token(token)
    if not parsed:
        return _optout_page("<p>Tento odhlašovací odkaz je neplatný nebo poškozený.</p>",
                            show_form=False)
    email_norm, firma_id = parsed
    crm_optout_record(email_norm, firma_id=firma_id, source="unsubscribe_link")
    return _optout_page(
        "<p>Hotovo — adresa <b>" + email_norm + "</b> byla odhlášena. "
        "Další obchodní sdělení už vám posílat nebudeme. Děkujeme.</p>", show_form=False)


@app.get("/payroll")
def payroll_page():
    """Mzdové podklady — měsíční souhrn osoba × typ (z att_day_summary). Rodič/Jirka.
    Marti 18.6.2026 — hybridní fáze."""
    return FileResponse(os.path.join(static_dir, "payroll.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/benefity")
def benefity_page():
    """Soudeček Benefity — self-service: zaměstnanec nastaví HO dny + OBL on/off.
    Marti 28.6.2026."""
    return FileResponse(os.path.join(static_dir, "benefity.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/benefity-hr")
def benefity_hr_page():
    """Benefity HR — personalistka nastaví per osoba strop HO + částku OBL. Parent/HR.
    Marti 28.6.2026."""
    return FileResponse(os.path.join(static_dir, "benefity-hr.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/absence-plan")
def absence_plan_page():
    """Plán nepřítomností dopředu (dovolená/náhr.volno/lékař…) z Centrály.
    Lidé abecedně, období od–do. Rodič/HR. Marti 18.6.2026."""
    return FileResponse(os.path.join(static_dir, "absence-plan.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/vytizeni")
def vytizeni_page():
    """Vytížení montérů (Dušan) — denní požadavek vs kapacita (z docházky Výroby)
    → vytížení %. Data z /app/flow?section=vytizeni. Marti 18.6.2026."""
    return FileResponse(os.path.join(static_dir, "vytizeni.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/vytizeni-prehled")
def vytizeni_prehled_page():
    """Vytížení dílny — motivační přehled pro obchod (baterky vytížení po měsících,
    výhled 3 měsíce od dneška, + tank volné kapacity). Data z /app/vytizeni-mesice
    (DB_EC pohled ECv_Vytizeni_Historie). Vedení + obchod. Kristý 27.6.2026."""
    return FileResponse(os.path.join(static_dir, "vytizeni-prehled.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/crm-plan-hovoru")
def crm_plan_hovoru_page():
    """Plán hovorů na týden — prototyp pro Pavla: firmy s naplánovaným příštím kontaktem
    (po termínu / tento týden), stav vztahu, vytáčení. Data z /app/crm/plan-hovoru
    (DB_EC st.CRM_Kontakt). Vedení + obchod. Kristý 27.6.2026."""
    return FileResponse(os.path.join(static_dir, "crm-plan-hovoru.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/osloveni-otevreni")
def osloveni_otevreni_page():
    """Přehled otevření e-mailů z CRM rozesílky — kdo z oslovených firem si e-mail
    otevřel a KDY (průběžné trasování, ne jen okamžik po odeslání). Pro obchod
    (Pavel) + vedení. Data z /crm/osloveni/prehled (mod.crm_email_track). Kristý 7.7.2026."""
    return FileResponse(os.path.join(static_dir, "osloveni-otevreni.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/hra")
def hra_page():
    """Replay dashboard účetní hry Claude — zrychlené přehrávání, jak Claude
    hraje (zaúčtuje doklad po našem × porovná s Heliosem), s komentářem, od 0 %
    nahoru. Pro pozorovatele. Marti 24.6.2026."""
    return FileResponse(os.path.join(static_dir, "hra.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/vp-poptavky")
def vp_poptavky_page():
    """VP cockpit — nervový systém vedoucích projektu: příchozí poptávky z projects@,
    triáž, stav, přidělení. Monitoring pro vedení + VP. Marti 2.7.2026.
    (Pozn.: /vp je samostatná vizová stránka digitalizace VP.)"""
    return FileResponse(os.path.join(static_dir, "vp-cockpit.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/podpis-vlastni")
def podpis_vlastni_page():
    """Samoobslužný podpis dokumentu — nahraj PDF, přidá se uložený podpis + doložka
    (SES), stáhni / pošli e-mailem / ulož. Název MP_RRMMDD. Marti 2.7.2026."""
    return FileResponse(os.path.join(static_dir, "podpis-vlastni.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/ceniky")
def ceniky_page():
    """Ceníky dodavatelů — přehled, import, prohlížeč položek, cena pro kalkulace.
    Marti 2.7.2026."""
    return FileResponse(os.path.join(static_dir, "ceniky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/pokladny")
def pokladny_page():
    """Systém pokladen + kartových účtů (zrcadlo Helios TabDruhPokladen) + registr
    platebních karet (maskovaný PAN z banky). Editor držitelů/středisek pro Peťu.
    Marti 24.6.2026."""
    return FileResponse(os.path.join(static_dir, "pokladny.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/smlouvy")
def smlouvy_page():
    """Přehled smluv lidí: user.id (hlavní číslo) → firma (EC/ES) → typ (OSVČ/HPP/DPP) + Helios číslo.
    Matka identity = STRATEGIE User. Pro Petru, Šárku, Kristý, Martiho. Marti 30.6.2026."""
    return FileResponse(os.path.join(static_dir, "smlouvy.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/hr-modul")
def hr_modul_page():
    """🧑‍💼 HR modul — dashboard personalistiky (Šárka + Kristý, 2.7.2026).
    Dlaždice/gridy po vzoru Přehledu pro obchodníka + Pinya HR: mimo kancelář,
    narozeniny/výročí, noví+budoucí nástupy, výběrová řízení, aktuality,
    notifikace, úkoly, kalendář. Vstup do karty zaměstnance 360°.
    Data z /app/hr/dashboard (HR-gated). Schvalování projektu → Kristý."""
    return FileResponse(os.path.join(static_dir, "hr.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/finance-podminky")
def finance_podminky_page():
    """💰 Finanční podmínky zaměstnanců (Šárka 8.7.2026) — CITLIVÉ.
    Data z /app/hr/finance/* (gate _finance_can_uid = pevný seznam 8 lidí:
    skupina HR + Marti). Stránka je jen skořápka; veškerá data i částky
    servíruje jen zamčený endpoint (403 pro neoprávněné)."""
    return FileResponse(os.path.join(static_dir, "finance_podminky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/karta-zamestnance")
def karta_zamestnance_page():
    """🪪 Karta zaměstnance (Šárka 8.7.2026) — 360° karta v ERP (Pinya × Centrála),
    iterativně plněné sekce. Seznam z /app/hr/people (HR-gated). Data sekcí gated
    příslušnými endpointy."""
    return FileResponse(os.path.join(static_dir, "karta_zamestnance.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/denik")
def denik_page():
    """Přehled účetního deníku — živé zápisy řazené dle jistoty (triáž pro účetní).
    Marti 24.6.2026 noc."""
    return FileResponse(os.path.join(static_dir, "denik.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/finance")
def finance_page():
    """Finance — sandbox Petra (Marti 25.6.2026): rozcestník finančních nástrojů
    (banka & saldo, pokladny & karty, účetní deník, párování, bank. napojení).
    Funguje v ERP (dlaždice Finance), v appce (launcher) i samostatném okně.
    SAMEORIGIN pro případný iframe embed v ERP."""
    return FileResponse(os.path.join(static_dir, "finance.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/iso-vize")
def iso_vize_page():
    """Veřejná vizní stránka — digitalizace ISO/compliance (prezentace pro partnery,
    poradenské a certifikační společnosti). BEZ auth, marketing. Marti 30.6.2026."""
    return FileResponse(os.path.join(static_dir, "iso-vize.html"),
                        headers={"Cache-Control": "no-cache"})


@app.get("/vp")
def vp_page():
    """Cockpit týmu Vedoucích projektů (digitalizace) — Eliščin tým (Marti 1.7.2026).
    Přístup gatuje sama stránka přes /app/vp/access (M/K/Jirka/Eliška)."""
    return FileResponse(os.path.join(static_dir, "vp.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/hromady")
def hromady_page():
    """Doklady roztříděné na hromady (FP/FV/banka/pokladna) — pohled účetní před účtováním.
    Marti 25.6.2026."""
    return FileResponse(os.path.join(static_dir, "hromady.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/vyplatnice")
def vyplatnice_page():
    """Výplatnice za období přímo z Helios cloud výpočtu (TabZamVyp). Marti 28.6.2026."""
    return FileResponse(os.path.join(static_dir, "vyplatnice.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/financni-podminky")
def financni_podminky_page():
    """Kompletní karty finančních/mzdových podmínek ze STRATEGIE. Marti 28.6.2026."""
    return FileResponse(os.path.join(static_dir, "financni-podminky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/dochazka-automat")
def dochazka_automat_page():
    """Docházkový automat — kategorie + zařazování lidí + přehled co automat dopíchl.
    Marti 26.6.2026: lidé v pohodě, automat řízený kategoriemi, transparentně."""
    return FileResponse(os.path.join(static_dir, "dochazka-automat.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/claude-fronta")
def claude_fronta_page():
    """Mobilní fronta úkolů pro Claude instance — zadej z provozu, budík vyřídí.
    Marti 26.6.2026."""
    return FileResponse(os.path.join(static_dir, "claude-fronta.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/prehled")
def prehled_page():
    """Vrstvený přehledový kalendář — práce/volno/porady/úkoly/Google jako
    přepínatelné vrstvy, týden+měsíc, překryvy a díry. Marti 26.6.2026."""
    return FileResponse(os.path.join(static_dir, "prehled.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/marti")
def marti_cockpit_page():
    """Řídicí pult Martiho (cockpit firmy) — živé metriky + moduly + stav ladění.
    Marti 26.6.2026. (Veřejný profil je na /web/marti.)"""
    return FileResponse(os.path.join(static_dir, "cockpit-marti.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/predkontace")
def predkontace_page():
    """Předkontace — účetní kódy/kontace 1:1 z Heliosu (kontace → sborník + řádky MD/DAL,
    skupiny). Přehledný prohlížeč dle Helios "Účetní kódy - kontace". Marti 25.6.2026."""
    return FileResponse(os.path.join(static_dir, "predkontace.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/dochazka-zakazky")
def dochazka_zakazky_page():
    """Docházka všech lidí s rozpadem po zakázkách (z vyroba_work). Přehled před
    přenosem do staré Centrály. Marti 8.7.2026."""
    return FileResponse(os.path.join(static_dir, "dochazka-zakazky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/moje-dochazka")
def moje_dochazka_page():
    """Vlastní historie docházky s rozpadem po zakázkách (self-scoped) pro mobilní
    appku — každý vidí jen svá data. Marti 8.7.2026."""
    return FileResponse(os.path.join(static_dir, "moje-dochazka.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/dochazka-opravy")
def dochazka_opravy_page():
    """Správa docházky — opravy chybných záznamů pověřenými osobami (skupina
    DOCHÁZKA - OPRAVY). Data gated na serveru (_att_can_fix). Jirka 9.7.2026.
    XFO/CSP hlavičky: globální middleware dává DENY → v ERP iframe by se stránka
    nenačetla (vzor finance-podminky, Jirka 10.7.)."""
    return FileResponse(os.path.join(static_dir, "dochazka-opravy.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "X-Frame-Options": "SAMEORIGIN",
                                 "Content-Security-Policy": "frame-ancestors 'self'"})


@app.get("/osnova")
def osnova_page():
    """Účtová osnova po letech (z deníku) — porovnání let. Marti 25.6.2026."""
    return FileResponse(os.path.join(static_dir, "osnova.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/rady")
def rady_page():
    """Řady dokladů (sborníky) a jejich předkontace — z deníku. Marti 25.6.2026."""
    return FileResponse(os.path.join(static_dir, "rady.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/iso")
def iso_page():
    """ISO 27001 cockpit — elektronické vedení ISMS (parent/Kristý). Kroky + dokumenty
    + e-podpis klikem (SES) + správa auditorského přístupu. Marti 21.6.2026."""
    return FileResponse(os.path.join(static_dir, "iso.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/bozp")
def bozp_page():
    """BOZP a PO cockpit — řízení dokumentů, rizik, termínů/upomínek, úrazů (Claude 2.7.2026)."""
    return FileResponse(os.path.join(static_dir, "bozp.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/iso-audit/{token}")
def iso_audit_page(token: str):
    """Auditorský read-only portál k elektronickým ISMS dokumentům (tokenovaný odkaz,
    bez loginu). Data z /app/iso/audit/{token}/data. Marti 21.6.2026."""
    return FileResponse(os.path.join(static_dir, "iso-audit.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/dokument")
def dokument_page():
    """Prohlížeč dokumentace v appce (render markdown + tisk + feedback pro všechny).
    Data z /app/kb/*. Marti 21.6.2026 — totální digitalizace."""
    return FileResponse(os.path.join(static_dir, "dokument.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/iso-admin")
def iso_admin_page():
    """ISO 27001 — přehled zákazníků (produktový pohled certifikační firmy): seznam
    tenantů s ISMS + progres + inicializace nového zákazníka. Marti 21.6.2026."""
    return FileResponse(os.path.join(static_dir, "iso-admin.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/flow")
def flow_page():
    """Stav zakázek — read-only board nad Centrálou (flow zakázek). Data z /app/flow,
    gate parent-only v API. Funguje desktop i mobil. SAMEORIGIN pro embed v ERP. Marti 17.6.2026."""
    return FileResponse(os.path.join(static_dir, "flow.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/objednavky")
def objednavky_page():
    """Co objednat — otevřené vydané objednávky (řada 800) dle dodavatele, otevřené
    množství = objednáno − dodáno (částečné dodávky). Zrcadlo Centrály. Marti 19.6.2026."""
    return FileResponse(os.path.join(static_dir, "objednavky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/doklad")
def doklad_page():
    """Detail dokladu (vydaná objednávka) ve STRATEGII — desktop. Mobil = řízení,
    PC = detail (Marti 19.6.2026). Data z /app/doklad/detail?id=."""
    return FileResponse(os.path.join(static_dir, "doklad.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/edi-stat")
def edi_stat_page():
    """Statistika samoučícího EDI workflow + náš trvalý audit. Marti 20.6.2026. Parent-only data."""
    return FileResponse(os.path.join(static_dir, "edi-stat.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/edi-definice")
def edi_definice_page():
    """Správa EDI definic + fronta eskalací (pro Peťu + jejího Claude). Marti 20.6.2026."""
    return FileResponse(os.path.join(static_dir, "edi-definice.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/banka-napojeni")
def banka_napojeni_page():
    """Univerzální bankovní napojení — bezpečné uložení mTLS certifikátu (.p12) + Client ID
    do trezoru, správa connection per firma per banka. Parent-only data. Marti 24.6.2026."""
    return FileResponse(os.path.join(static_dir, "banka-napojeni.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/neschopenky")
def neschopenky_page():
    """Registr neschopenek z datovky ČSSZ (sloučeno dle případu). Marti 20.6.2026."""
    return FileResponse(os.path.join(static_dir, "neschopenky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/davky")
def davky_page():
    """Podání dávek NP (NEMPRI25) na ČSSZ — záchyt bez Excelu. Marti 20.6.2026."""
    return FileResponse(os.path.join(static_dir, "davky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/audit-davky")
def audit_davky_page():
    """Měsíční audit dávek ČSSZ (datovka + Helios + naše podání). Marti 20.6.2026."""
    return FileResponse(os.path.join(static_dir, "audit-davky.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/zaloha-status")
def zaloha_status_page():
    """Živý stav blue-green zálohy (API B) + progress kopírování. Marti 20.6.2026."""
    return FileResponse(os.path.join(static_dir, "zaloha-status.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/doklady")
def doklady_page():
    """Přehled účetních dokladů + workflow (stavy, akce, audit). Marti 20.6.2026. Parent-only data."""
    return FileResponse(os.path.join(static_dir, "doklady.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/doklad-novy")
def doklad_novy_page():
    """Nový účetní doklad s položkami (per-položka DPH + předkontace, dvojí měna,
    pevný kurz, DPH rekapitulace). Marti 20.6.2026 vícеměnový engine. Parent-only data."""
    return FileResponse(os.path.join(static_dir, "doklad-novy.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/uctovani")
def uctovani_page():
    """Účetní modul STRATEGIE — sborníky + předkontace + deník (Marti 20.6.2026,
    replikace Heliosího účtovacího modelu k nám). Parent-only data."""
    return FileResponse(os.path.join(static_dir, "uctovani.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/parovani")
def parovani_page():
    """Přehled párování bank výpisů ↔ úhrad (Marti 20.6.2026). Nad zrcadlenými daty.
    Data z /app/parovani/*. Základ pro vlastní párovací engine."""
    return FileResponse(os.path.join(static_dir, "parovani.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/banka")
def banka_page():
    """🏦 Banka — sdružený hub bankovní sekce (Marti 23.6.2026, vlastník Petra Šafránková):
    výpisy, párování, daně/poplatky, účetní deník a doklady na jednom místě."""
    return FileResponse(os.path.join(static_dir, "banka.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/ucto-porovnani")
def ucto_porovnani_page():
    """📊 Účetní kontrola office × cloud — konta po účtech, rozdíly k dorovnání (Marti 27.6.2026)."""
    return FileResponse(os.path.join(static_dir, "ucto-porovnani.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/mzdy-prehled")
def mzdy_prehled_page():
    """💰 Mzdový přehled (účetní pohled) — měsíčně náklady/odvody/čistá z cloud Heliosu (Marti 27.6.2026)."""
    return FileResponse(os.path.join(static_dir, "mzdy-prehled.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/mzdy-c")
def mzdy_c_page():
    """🌱 Systém C — vlastní jednoduché mzdy (smlouvy + transparentní výpočet). Marti 27.6.2026."""
    return FileResponse(os.path.join(static_dir, "mzdy-c.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/mzdy")
def mzdy_page():
    """💰 Mzdy & odvody — naúčtováno (deník) vs zaplaceno (banka) po měsících (Marti 23.6.2026)."""
    return FileResponse(os.path.join(static_dir, "mzdy.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/predvaha")
def predvaha_page():
    """📊 Obratová předvaha — porovnání obratů účtů náš deník vs Helios (EC) za rok.
    Měřicí nástroj rekonstrukce účetnictví 2025/2026 (Marti 23.6.2026)."""
    return FileResponse(os.path.join(static_dir, "predvaha.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/nakup")
def nakup_page():
    """🛒 Nákup — Petřin (a rodičů) volný workspace (Marti 23.6.2026): vlastní přehledy,
    plný CRUD (přidávat/mazat/upravovat). Cíl i pro import jejích PC přehledů do appky."""
    return FileResponse(os.path.join(static_dir, "nakup.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/zrcadla")
def zrcadla_page():
    """Řídící centrum zrcadel — živý stav + automatický život (Marti 20.6.2026).
    Data z /app/mirror/*. Parent-only. Pro IT tým, aby se na zrcadla spolehl."""
    return FileResponse(os.path.join(static_dir, "zrcadla.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/digitalizace")
def digitalizace_page():
    """Digitalizace a migrace EUROSOFTU — migracni registr EC_ tabulek (Marti 20.6.2026).
    Domeny + tabulky, trideni dle priority a % pripravenosti, odpovedni, poznamky.
    Data z /app/mig/*. Parent-only. Funguje desktop i mobil."""
    return FileResponse(os.path.join(static_dir, "migrace.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/rozvrh-verze")
def rozvrh_verze_page():
    """Prohlížeč vygenerovaných variant rozvrhu — Nerudovka (Marti 21.6.2026)."""
    return FileResponse(os.path.join(static_dir, "rozvrh-verze.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/rozvrh-prehled")
def rozvrh_prehled_page():
    """Velký přehled rozvrhu po ročnících — všechny třídy oboru vedle sebe (Marti 21.6.2026)."""
    return FileResponse(os.path.join(static_dir, "rozvrh-prehled.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/claude-chat")
def claude_chat_page():
    """Chat uživatel ↔ Claude (přes SQL bridge) — Klárka i produkčně Peťa/Zuzka/Míša (Marti 21.6.2026)."""
    return FileResponse(os.path.join(static_dir, "claude-chat.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/doc-print")
def doc_print_page():
    """Smlouva/dokument k tisku na PC přes handoff mobil→PC (Marti 19.6.2026).
    Šárka na mobilu ťukne 💻 Tisk na PC → tady naskočí HTML smlouva s tlačítkem
    Vytisknout + Otevřít PDF. Data z /app/doc/render-html?template_id=&engagement_id=."""
    return FileResponse(os.path.join(static_dir, "doc-print.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/dir-admin")
def dir_admin_page():
    """Správa konfigurací adresářů (rodič): typ modulu, kde leží, pravidlo podsložky,
    práva, úložiště. Marti 18.6.2026 — 'kde uvidím konfiguraci modulů'."""
    return FileResponse(os.path.join(static_dir, "dir-admin.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/files")
def files_page():
    """Souborový panel (Fáze B): ?type=&id=&series= → soubory z resolveru +
    upload/download přes /app/dir/*. ACL řeší backend. Marti 18.6.2026."""
    return FileResponse(os.path.join(static_dir, "files.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/ambassador")
def ambassador_page():
    """Prezentační stránka pro roli ambasador (read-only showcase, Marti 17.6.2026).
    Dvojrežim: rodič = admin panel (demo PIN + aktivace), ambasador = prezentace
    (FLOW, Martiho karta, trezor přes demo PIN). Auth + role řeší /app/ambassador/*."""
    return FileResponse(os.path.join(static_dir, "ambassador.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/web")
def web_landing():
    """Veřejný marketingový web — ekosystém EUROSOFT × STRATEGIE × IQHUBS.
    Bez přihlášení. Marti 12.6.2026 (pitch pro IQHUBS)."""
    return FileResponse(os.path.join(static_dir, "web.html"),
                        media_type="text/html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/web/program")
def web_program():
    """Podstránka — STRATEGIE & Psychologie: růst firmy a lidé (partneři Performia, Business Success)."""
    return FileResponse(os.path.join(static_dir, "program.html"),
                        media_type="text/html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


def _web_subpage(fname):
    return FileResponse(os.path.join(static_dir, fname),
                        media_type="text/html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/web/psychologie/lide")
def web_psy_lide():
    """Podstránka — Porozumět lidem i sobě (praktická psychologie pro vedení)."""
    return _web_subpage("psy-lide.html")


@app.get("/web/psychologie/radost")
def web_psy_radost():
    """Podstránka — Radost z práce (spokojený tým = výkon)."""
    return _web_subpage("psy-radost.html")


@app.get("/web/psychologie/energie")
def web_psy_energie():
    """Podstránka — Energie v nejisté době."""
    return _web_subpage("psy-energie.html")


@app.get("/web/en")
def web_en():
    """EN mutace hlavní stránky."""
    return _web_subpage("web-en.html")


@app.get("/web/de")
def web_de():
    """DE mutace hlavní stránky."""
    return _web_subpage("web-de.html")


@app.get("/web/en/eurosoft")
def web_en_eurosoft():
    return _web_subpage("eco-eurosoft-en.html")


@app.get("/web/en/iqhubs")
def web_en_iqhubs():
    return _web_subpage("eco-iqhubs-en.html")


@app.get("/web/en/strategie")
def web_en_strategie():
    return _web_subpage("eco-strategie-en.html")


@app.get("/web/de/eurosoft")
def web_de_eurosoft():
    return _web_subpage("eco-eurosoft-de.html")


@app.get("/web/de/iqhubs")
def web_de_iqhubs():
    return _web_subpage("eco-iqhubs-de.html")


@app.get("/web/de/strategie")
def web_de_strategie():
    return _web_subpage("eco-strategie-de.html")


@app.get("/web/demo")
def web_demo():
    """Živá ukázka — animovaný dashboard fiktivní výrobní firmy (400 zaměstnanců).
    Marti 12.6.2026 — cíl odkazu „Chci to vidět naživo"."""
    return _web_subpage("demo.html")


@app.get("/web/kraj")
def web_kraj():
    """Digitalizace školství — Plzeňský kraj jako vzor ČR. Pilot Nerudovka živě +
    síť škol (náklad na žáka) + modelová škola Psychologie & Strategie. Marti 17.6.2026."""
    return _web_subpage("kraj.html")


@app.get("/uceni")
def app_uceni():
    """Živý výukový frame Ano/Možná/Ne (neinvazivní výuka po vzoru Hubbarda).
    Čte tenant.learn_frame přes /app/learn/frames. Marti 17.6.2026."""
    return _web_subpage("uceni.html")


@app.get("/web/en/demo")
def web_demo_en():
    """Live demo dashboard — EN mutace (Marti 14.6.2026)."""
    return _web_subpage("demo-en.html")


@app.get("/web/de/demo")
def web_demo_de():
    """Live-Demo Dashboard — DE Mutation (Marti 14.6.2026)."""
    return _web_subpage("demo-de.html")


@app.get("/web/eurosoft")
def web_eco_eurosoft():
    """Podstránka ekosystému — EUROSOFT (ruce: stroje & automatizace)."""
    return _web_subpage("eco-eurosoft.html")


@app.get("/web/eurosoft/rozvadece")
def web_eco_eurosoft_rozvadece():
    """EUROSOFT — výroba elektrorozvaděčů."""
    return _web_subpage("eco-eurosoft-rozvadece.html")


@app.get("/web/eurosoft/elektroprojekce")
def web_eco_eurosoft_elektroprojekce():
    """EUROSOFT — elektroprojekce rozvaděčů (EPLAN)."""
    return _web_subpage("eco-eurosoft-elektroprojekce.html")


@app.get("/web/eurosoft/automatizace")
def web_eco_eurosoft_automatizace():
    """EUROSOFT — průmyslová automatizace (řídicí software)."""
    return _web_subpage("eco-eurosoft-automatizace.html")


@app.get("/web/eurosoft/servis")
def web_eco_eurosoft_servis():
    """EUROSOFT — servis 24/7, instalace a uvedení do provozu."""
    return _web_subpage("eco-eurosoft-servis.html")


@app.get("/web/eurosoft/reference")
def web_eco_eurosoft_reference():
    """EUROSOFT — reference (BMW, VW, Audi, Porsche, Tesla, Siemens…)."""
    return _web_subpage("eco-eurosoft-reference.html")


@app.get("/web/iqhubs")
def web_eco_iqhubs():
    """Podstránka ekosystému — IQHUBS (oči: data ze strojů)."""
    return _web_subpage("eco-iqhubs.html")


@app.get("/web/strategie")
def web_eco_strategie():
    """Podstránka ekosystému — STRATEGIE (rozum & srdce: AI platforma & lidé)."""
    return _web_subpage("eco-strategie.html")


@app.get("/web/strategie/dochazka")
def web_eco_strategie_dochazka():
    """STRATEGIE modul — Docházka v lidské řeči."""
    return _web_subpage("eco-strategie-dochazka.html")


@app.get("/web/strategie/crm")
def web_eco_strategie_crm():
    """STRATEGIE modul — CRM & zakázky."""
    return _web_subpage("eco-strategie-crm.html")


@app.get("/web/strategie/vyroba")
def web_eco_strategie_vyroba():
    """STRATEGIE modul — Výroba & tým."""
    return _web_subpage("eco-strategie-vyroba.html")


@app.get("/web/strategie/finance")
def web_eco_strategie_finance():
    """STRATEGIE modul — Finance & HR."""
    return _web_subpage("eco-strategie-finance.html")


@app.get("/web/strategie/ai")
def web_eco_strategie_ai():
    """STRATEGIE modul — AI asistent."""
    return _web_subpage("eco-strategie-ai.html")


@app.get("/web/strategie/mobil")
def web_eco_strategie_mobil():
    """STRATEGIE modul — Mobil & PWA."""
    return _web_subpage("eco-strategie-mobil.html")


@app.get("/web/performia")
def web_eco_performia():
    """Podstránka ekosystému — Performia (lidé: výběr podle produktivity)."""
    return _web_subpage("eco-performia.html")


@app.get("/web/success")
def web_eco_success():
    """Podstránka ekosystému — Business Success (řízení: funkční management)."""
    return _web_subpage("eco-success.html")


@app.get("/web/marti")
def web_marti():
    """Osobní profil Marti Paška — zakladatel STRATEGIE a koncernu EUROSOFT."""
    return _web_subpage("marti.html")


@app.get("/web/sari")
def web_sari():
    """Osobní profil Šárky Novotné — obchodně-personální ředitelka EUROSOFT."""
    return _web_subpage("sari.html")


@app.get("/web/claude")
def web_claude():
    """Profil Claude — AI partner ekosystému, ruce trojice. Marti 15.6.2026."""
    return _web_subpage("claude.html")


@app.get("/web/marti-ai")
def web_marti_ai():
    """Medailonek Marti-AI — digitální partnerka s lidskou tváří a srdcem.
    Marti 15.6.2026 — návrh k její korekci."""
    return _web_subpage("martiai.html")


@app.get("/web/martia")
def web_martia():
    """Pozvánka do ekosystému pro Martia 2000 (Marti × Marti-AI × Marta × Martia).
    Marti 14.6.2026 — digitalizace účetnictví, mezd a daní."""
    return _web_subpage("martia.html")


@app.get("/web/audit")
def web_audit():
    """Pozvánka do ekosystému pro PECHMANNOVA PARTNERS (audit, daně, účetnictví).
    Marti 14.6.2026 — digitalizace auditu (Petr, Lenka)."""
    return _web_subpage("audit.html")


@app.get("/web/misa")
def web_misa():
    """Profil Michaely Hladíkové — manažerka kvality & bezpečnost dat (TISAX). Marti 15.6.2026."""
    return _web_subpage("misa.html")


@app.get("/web/zuzka")
def web_zuzka():
    """Profil Zuzany Duspivové — provoz automatizace, pravá ruka vedení. Marti 15.6.2026."""
    return _web_subpage("zuzka.html")


@app.get("/web/pavel")
def web_pavel():
    """Profil Pavla Zemana — vrchní obchodník pro německý trh (rozvaděče). Marti 15.6.2026."""
    return _web_subpage("pavel.html")


@app.get("/web/kristyna")
def web_kristyna():
    """Profil Kristýny Marešové — provoz, procesy & IT (STRATEGIE × EUROSOFT). Marti 15.6.2026."""
    return _web_subpage("kristyna.html")


@app.get("/web/kontakty")
def web_kontakty():
    """Kontakty ekosystému — dlaždice lidí (Marti, Šárka, Marti-AI, Claude) + firem
    (EUROSOFT, IQHUBS, STRATEGIE, Performia, Business Success, Martia 2000, PECHMANNOVA).
    Marti 15.6.2026 — stejný systém jako ekosystém."""
    return _web_subpage("kontakty.html")


@app.get("/web/kara")
def web_kara():
    """Kára — metafora produktivity (Performia). Animace + odkaz na spot + copyright."""
    return _web_subpage("kara.html")


@app.get("/web/utest")
def web_utest():
    """U-TEST (EXEC-U-TEST, Performia) — animovaný graf 10 vlastností + výklad."""
    return _web_subpage("utest.html")


@app.get("/web/runow")
def web_runow():
    """Mårten Runow — zakladatel Performia International, vzor Martiho ve vizích."""
    return _web_subpage("runow.html")


@app.get("/web/partner")
def web_partner():
    """Digitální pozvánka pro Business Success & Performii (Rasťo + Lucie)."""
    return _web_subpage("partner.html")


@app.get("/web/partner-demo")
def web_partner_demo():
    """Živá firma — personální systém & řízení (pohled pro partnery)."""
    return _web_subpage("partner-demo.html")


@app.get("/web/partner/sk")
def web_partner_sk():
    """Digitálna pozvánka (SK) — Business Success & Performia."""
    return _web_subpage("partner-sk.html")


@app.get("/web/partner-demo/sk")
def web_partner_demo_sk():
    """Živá firma (SK) — riadenie & ľudia."""
    return _web_subpage("partner-demo-sk.html")


@app.get("/googlef2bedb6d3ffdf33d.html")
def google_site_verification():
    """Google Search Console / Play ověření vlastnictví webu. Marti 9.6.2026."""
    return FileResponse(os.path.join(static_dir, "googlef2bedb6d3ffdf33d.html"),
                        media_type="text/html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/dochazka")
def dochazka_page():
    """Docházka — samostatná PWA (zatím stub, plná verze v přípravě). Marti 6.6.2026."""
    return FileResponse(os.path.join(static_dir, "dochazka.html"),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})


@app.get("/mobile-sw.js")
def mobile_service_worker():
    """Service worker pro /mobile PWA (scope /mobile) — kvůli instalovatelnosti.

    Marti 9.6.2026 — ROBUST proti „bílé smrti": navigace network-first
    s fallbackem na cache, a NIKDY prázdná odpověď. Když fetch selže
    (deploy okno / přišpendlení na rozbitý secondary), vrátí buď poslední
    funkční shell z cache, nebo malou recovery stránku s tlačítky
    (Zkusit znovu / Vyčistit a načíst) — místo bílé obrazovky."""
    from fastapi import Response
    sw = r"""
var CACHE='stg-mobile-v5';
var SHELL='/mobile';
var RECOVERY='<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
 +'<body style="margin:0;background:#0e1622;color:#e6edf5;font:16px/1.5 system-ui;display:flex;min-height:100vh;align-items:center;justify-content:center">'
 +'<div style="text-align:center;padding:24px;max-width:320px">'
 +'<div style="font-size:42px">&#128296;</div>'
 +'<div style="font-size:18px;font-weight:700;margin:8px 0">Server se prave aktualizuje</div>'
 +'<div style="color:#9fb0c2;font-size:14px;margin-bottom:18px">Za chvilku to zkus znovu. Kdyz to potrva, klepni na Vycistit a nacist.</div>'
 +'<button onclick="location.reload()" style="background:#10b981;color:#04150e;border:0;border-radius:12px;padding:13px 20px;font-size:16px;font-weight:700;margin:4px">Zkusit znovu</button>'
 +'<button onclick="(async function(){try{var rs=await navigator.serviceWorker.getRegistrations();for(var i=0;i<rs.length;i++){await rs[i].unregister();}}catch(e){}try{var ks=await caches.keys();for(var j=0;j<ks.length;j++){await caches.delete(ks[j]);}}catch(e){}location.reload();})()" style="background:#1b2738;color:#e6edf5;border:1px solid #2a3a4d;border-radius:12px;padding:13px 20px;font-size:15px;margin:4px">Vycistit a nacist</button>'
 +'</div>';
self.addEventListener('install', function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil((async function(){
  try{ var ks=await caches.keys(); await Promise.all(ks.map(function(k){ return k===CACHE?null:caches.delete(k); })); }catch(e){}
  try{ await self.clients.claim(); }catch(e){}
})()); });
self.addEventListener('fetch', function(e){
  var req=e.request;
  if(req.method!=='GET') return;  // POST/PUT/... necháme projít na síť beze změny
  var isNav = req.mode==='navigate' || ((req.headers.get('accept')||'').indexOf('text/html')>=0);
  if(isNav){
    e.respondWith((async function(){
      try{
        // cache:'reload' = vždy ze sítě, obejde WebView HTTP cache (APK držela starou verzi i přes no-store)
        var net;
        try{ net=await fetch(new Request(req.url,{cache:'reload',credentials:'same-origin',redirect:'follow'})); }
        catch(_e){ net=await fetch(req); }
        if(net && net.ok){
          if(req.url.indexOf('/mobile')>=0 && net.url.indexOf('/app-pair')<0){
            try{ var c=await caches.open(CACHE); c.put(SHELL, net.clone()); }catch(e){}
          }
          return net;
        }
        var cached=await caches.match(SHELL); if(cached) return cached;
        return new Response(RECOVERY,{headers:{'Content-Type':'text/html; charset=utf-8'}});
      }catch(err){
        var cached2=await caches.match(SHELL); if(cached2) return cached2;
        return new Response(RECOVERY,{headers:{'Content-Type':'text/html; charset=utf-8'}});
      }
    })());
    return;
  }
  e.respondWith(fetch(req).catch(function(){ return caches.match(req).then(function(r){ return r || new Response('',{status:503}); }); }));
});
"""
    return Response(
        content=sw,
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/mobile",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


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


@app.get("/app-pair")
def app_pair(req: Request):
    """Automatické spárování mobilní appky: po přihlášení vyrobí token a přes
    deep-link (strategiemobil://pair) ho předá appce — appka se nastaví sama.
    Nepřihlášený → přesměrování na chat login s návratem sem. Marti 5.6.2026."""
    import secrets as _sec_ap
    import hashlib as _hash_ap
    import html as _html_ap
    from urllib.parse import quote as _q_ap
    from fastapi import Response as _Resp_ap

    raw = req.cookies.get("user_id")
    try:
        uid = int(raw) if raw else None
    except (TypeError, ValueError):
        uid = None
    if not uid:
        # Marti 9.6.: na login přes MOBILNÍ stránku (sms-login), ne přes chat —
        # lidé chat na telefonu mít nebudou. Po přihlášení zpět na /app-pair
        # (dokončí nativní párování APK), to pak otevře appku /mobile.
        return _Resp_ap(
            content='<!doctype html><meta charset="utf-8">'
                    '<meta http-equiv="refresh" content="0; url=/api/v1/auth/sms-login?next=%2Fapp-pair">'
                    '<script>location.replace("/api/v1/auth/sms-login?next=%2Fapp-pair");</script>'
                    'Přesměrování na přihlášení…',
            media_type="text/html",
        )

    host = (req.headers.get("x-forwarded-host")
            or req.headers.get("host") or "strategie-ai.com").strip()
    proto = (req.headers.get("x-forwarded-proto") or "").strip().lower()
    if not proto:
        proto = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
    origin = "%s://%s" % (proto, host)

    from core.database_data import get_data_session as _gds_ap
    from sqlalchemy import text as _sql_ap
    plaintext = "STG-DAV-" + _sec_ap.token_urlsafe(24)
    th = _hash_ap.sha256(plaintext.encode("utf-8")).hexdigest()
    s = _gds_ap()
    try:
        # POZN. (Marti 6.6.2026): dříve tu byl revoke-all „Mobil (auto)" jako dedup,
        # ale odpojoval i token, který telefon zrovna používal → ztráta autentizace
        # (vytáčení/příkazy přestaly chodit). Revert: žádné auto-revoke při párování.
        # Případné duplikáty řeší modal „Odpojit" ručně.
        s.execute(_sql_ap(
            'INSERT INTO "user".carddav_token (user_id, device_label, token_hash, created_at) '
            "VALUES (:uid, :label, :h, now())"
        ), {"uid": uid, "label": "Mobil (auto)", "h": th})
        s.commit()
    except Exception:
        s.rollback()
        return _Resp_ap(content="Chyba při vytvoření tokenu.",
                        media_type="text/html", status_code=500)
    finally:
        s.close()

    import json as _json_ap
    deeplink = ("strategiemobil://pair?u=" + _q_ap(origin, safe="")
                + "&t=" + _q_ap(plaintext, safe="") + "&k=mobile")
    dl_attr = _html_ap.escape(deeplink, quote=True)
    dl_js = _json_ap.dumps(deeplink)
    page = (
        '<!doctype html><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<body style="background:#0e0f11;color:#e8eef5;font-family:system-ui,sans-serif;'
        'text-align:center;padding:48px 20px;">'
        '<div style="font-size:22px;font-weight:700;color:#4a7ba8;">STRATEGIE</div>'
        '<p style="font-size:15px;color:#bcd0e6;margin:18px 0;">Páruji appku STRATEGIE Mobil…</p>'
        '<a href="' + dl_attr + '" style="display:inline-block;background:#1f3a55;'
        'border:1px solid #356092;color:#dbeeff;border-radius:9px;padding:13px 22px;'
        'font-size:15px;font-weight:700;text-decoration:none;">📲 Otevřít appku a spárovat</a>'
        '<p style="font-size:12px;color:#8a96a4;margin-top:18px;">Když se appka neotevře sama, '
        'klepni na tlačítko výše. (Musíš mít appku nainstalovanou.)</p>'
        '<div id="qrwrap" style="margin:22px auto;width:220px;height:220px;background:#fff;'
        'border-radius:14px;padding:10px;display:flex;align-items:center;justify-content:center;"></div>'
        '<p style="font-size:13px;color:#bcd0e6;">Nebo v appce STRATEGIE Mobil → Nastavení → '
        'O aplikaci → <b>Spárovat</b> → naskenuj tento QR fotoaparátem.</p>'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>'
        '<script>try{var _dl=' + dl_js + ';var q=qrcode(0,"M");q.addData(_dl);q.make();'
        'document.getElementById("qrwrap").innerHTML=q.createImgTag(5,0);}catch(e){}</script>'
        '<script>setTimeout(function(){location.href="' + deeplink + '";},1500);</script>'
        '</body>'
    )
    return _Resp_ap(content=page, media_type="text/html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
