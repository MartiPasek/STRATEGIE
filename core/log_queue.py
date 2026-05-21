"""Phase 38.4 Krok 14g — DB Log Infrastructure — Etapa A core module.

16.5.2026 ranní pokračování po Marti's *„asi dva pohledy master/detail"*
+ Marti's korekce: *„Nemelo by to byt anonymni. Hned v hlavicce by jako
prvni udaj mel byt LoginName Usera a ID a hned zanim tenant name."*

3-layer fallback defense pro logging events do fw.diag_log:

  Layer 1: DB INSERT pres fw.diag_log_upsert() (preferred)
  Layer 2: file JSONL queue (LOG_QUEUE_DIR/queue-YYYYMMDD.jsonl)
  Layer 3: in-memory deque (cap 1000, FIFO, oldest dropped on overflow)

MASTER fields (vždy první v master view):
  - user_login_name (e.g. "m.pasek", "marti-ai", "system")
  - user_id
  - tenant_name (e.g. "STRATEGIE", "EUROSOFT")
  - level / source / module_id / message / status

Drain logika (file → DB):
  - On every successful DB write — try drain N recent file entries
  - Periodic 5-min background task
  - On FastAPI startup hook (one-shot)

Marti's doctrine 16.5.: *„kdyz neco v nejakem selze, hodi to uzivateli
plnohodnotnou diagnostiku a zbytek bezi dale"* — log SAMOTNY nikdy
neshodi aplikaci. Pri DB error: file. Pri file error: memory.
Pri memory full: drop oldest + ERROR log (ironical, ale lepsi nez crash).

Dedup logika je v DB function fw.diag_log_upsert (SHA1 hash + 24h window).
Python jen calc hash a posle ho do params.

Public API:
    log_event(level, source, module_id, message, **kwargs) -> int | None
        - Sync version, vrati diag_log.id nebo None pri total failure
    log_event_async(level, source, module_id, message, **kwargs)
        - Async version, never blocks (fire and forget)
    drain_queue_now() -> tuple[int, int]  # (drained, remaining)
        - Manual drain trigger
    queue_stats() -> dict
        - Current memory/file queue sizes
"""

from __future__ import annotations

import asyncio
import contextvars
import hashlib
import json
import logging
import os
import re
import sys
import threading
import traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from core.config import Settings
from core.database_data import get_data_session

# ───────────────────────────────────────────────────────────────────────
# Config
# ───────────────────────────────────────────────────────────────────────
_settings = Settings()
LOG_QUEUE_DIR = Path(os.getenv("LOG_QUEUE_DIR", "D:/Data/STRATEGIE/log_queue"))
MEM_QUEUE_CAP = int(os.getenv("LOG_QUEUE_MEM_CAP", "1000"))
DRAIN_BATCH_SIZE = int(os.getenv("LOG_QUEUE_DRAIN_BATCH", "100"))

# Logger pro samotny log_queue (NE pro events — events jdou do fw.diag_log
# pres log_event). Toto je INTERNI logger, kdyby file/DB selhalo.
_internal_logger = logging.getLogger("strategie.log_queue")

# ───────────────────────────────────────────────────────────────────────
# In-memory queue (Layer 3 fallback — drop-oldest deque)
# ───────────────────────────────────────────────────────────────────────
_mem_queue: deque[dict[str, Any]] = deque(maxlen=MEM_QUEUE_CAP)
_mem_lock = threading.Lock()

# ───────────────────────────────────────────────────────────────────────
# Request_id context (per-request, propagovany pres FastAPI middleware)
# ───────────────────────────────────────────────────────────────────────
_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: str | None) -> None:
    """Setni request_id pro current async context (FastAPI middleware)."""
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Vrati request_id z current context (None pokud mimo request)."""
    return _request_id_var.get()


# ───────────────────────────────────────────────────────────────────────
# User+ERP context (Fix K 21.5. — propagace pro Python error attribution)
# ───────────────────────────────────────────────────────────────────────
# Middleware (apps/api/main.py) po Fix I lookup user nastavi tyto vars.
# Deep code (data_source_runner.logger.error, modules.*) je dostane pres
# DiagLogHandler.emit() fallback. async-safe, propaguje skrz asyncio chain.
#
# Bez tohoto: Python error rows v fw.diag_log meli prazdne user_login_name +
# tenant_name + core_id + comp_def_id (Marti's catch 21.5. rano).
_user_login_name_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_login_name", default=None
)
_user_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id", default=None
)
_tenant_name_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_name", default=None
)
_core_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "core_id", default=None
)
_comp_def_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "comp_def_id", default=None
)


def set_user_context(
    login_name: str | None = None,
    user_id: int | None = None,
    tenant_name: str | None = None,
    core_id: int | None = None,
    comp_def_id: int | None = None,
) -> None:
    """Setni user context pro current async context (FastAPI middleware).

    Call po Fix I _fi_user_context lookup + Fix J Vrstva 5 header parse.
    Propaguje skrz asyncio call chain (data_source_runner.logger.error
    dostane tyto values pres DiagLogHandler.emit fallback).
    """
    _user_login_name_var.set(login_name)
    _user_id_var.set(user_id)
    _tenant_name_var.set(tenant_name)
    _core_id_var.set(core_id)
    _comp_def_id_var.set(comp_def_id)


def get_user_context() -> dict[str, Any]:
    """Vrati user+ERP context z current async context."""
    return {
        "user_login_name": _user_login_name_var.get(),
        "user_id": _user_id_var.get(),
        "tenant_name": _tenant_name_var.get(),
        "core_id": _core_id_var.get(),
        "comp_def_id": _comp_def_id_var.get(),
    }


# ───────────────────────────────────────────────────────────────────────
# Helpers — dedup hash a message normalization
# ───────────────────────────────────────────────────────────────────────
_NUM_PATTERN = re.compile(r"\d+")
_HEX_PATTERN = re.compile(r"\b[0-9a-f]{8,}\b", re.IGNORECASE)


def _normalize_message(message: str) -> str:
    """Strip variable parts (IDs, hex hashes, timestamps) pro dedup hash.

    Same error type s ruznymi IDs → same dedup hash.
    Napr: "ConnectionError: timeout to 192.168.30.11:5432 (request_id=abc123)"
       → "ConnectionError: timeout to N.N.N.N:N (request_id=H)"
    """
    if not message:
        return ""
    normalized = message[:500]  # cap pri dlouhych
    normalized = _HEX_PATTERN.sub("H", normalized)
    normalized = _NUM_PATTERN.sub("N", normalized)
    return normalized


def _compute_dedup_hash(
    level: str,
    source: str,
    module_id: str,
    message: str,
    element_selector: str | None = None,
) -> str:
    """SHA1 hash pro dedup (24h window v DB function)."""
    parts = [
        level or "",
        source or "",
        module_id or "",
        _normalize_message(message),
        element_selector or "",
    ]
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha1(blob).hexdigest()


# ───────────────────────────────────────────────────────────────────────
# Layer 1: DB INSERT via fw.diag_log_upsert()
# ───────────────────────────────────────────────────────────────────────
def _insert_to_db(event: dict[str, Any]) -> int | None:
    """Try INSERT to fw.diag_log via upsert function. Return id or None on fail.

    Vola PG function (atomic dedup + insert).
    Pri kterekoli chybe vrati None a vola NEPADA — fail-safe.
    """
    try:
        session = get_data_session()
    except Exception as exc:
        _internal_logger.warning(
            "[log_queue] _insert_to_db: get_data_session failed: %s", exc
        )
        return None

    try:
        # Function signature (33 named params, in PG positional order):
        # MASTER (3) + META (6) + JS (8) + PY (2) + REQ (5) + CTX (4) + BLOBS (2) + AUDIT (2) = 32
        sql = text("""
            SELECT fw.diag_log_upsert(
                :user_login_name, :user_id, :tenant_name,
                :level, :source, :module_id, :module_version, :message, :dedup_hash,
                :stack, :page_url, :user_agent, :viewport,
                :element_selector, :file_name, :line_number, :column_number,
                :exception_type, :traceback,
                :request_id, :fastapi_endpoint, :http_method, :http_status, :response_time_ms,
                :persona_id, :tenant_id, :conversation_id, :design_mode,
                CAST(:extra AS JSONB), CAST(:dom_state AS JSONB),
                :created_by_id, :created_by_text,
                :core_id, :comp_def_id
            ) AS id
        """)
        params = {
            # MASTER (Marti's 16.5. doctrine: ne-anonymous)
            "user_login_name": event.get("user_login_name"),
            "user_id": event.get("user_id"),
            "tenant_name": event.get("tenant_name"),
            # META
            "level": event.get("level", "info"),
            "source": event.get("source", "py"),
            "module_id": event.get("module_id", "unknown"),
            "module_version": event.get("module_version"),
            "message": event.get("message", ""),
            "dedup_hash": event.get("dedup_hash"),
            # JS detail
            "stack": event.get("stack"),
            "page_url": event.get("page_url"),
            "user_agent": event.get("user_agent"),
            "viewport": event.get("viewport"),
            "element_selector": event.get("element_selector"),
            "file_name": event.get("file_name"),
            "line_number": event.get("line_number"),
            "column_number": event.get("column_number"),
            # PY detail
            "exception_type": event.get("exception_type"),
            "traceback": event.get("traceback"),
            # Request correlation
            "request_id": event.get("request_id"),
            "fastapi_endpoint": event.get("fastapi_endpoint"),
            "http_method": event.get("http_method"),
            "http_status": event.get("http_status"),
            "response_time_ms": event.get("response_time_ms"),
            # App context
            "persona_id": event.get("persona_id"),
            "tenant_id": event.get("tenant_id"),
            "conversation_id": event.get("conversation_id"),
            "design_mode": event.get("design_mode"),
            # Forensic blobs
            # Fix #2.6 (20.5. vecer, Marti's "do DB se neloguje vubec" po Fix #1+2):
            # default=str fallback pro non-JSON-serializable values (datetime,
            # Decimal, Request, exception instance, SQLAlchemy session...).
            # Bez tohoto by json.dumps() padlo TypeError -> except v _insert_to_db
            # -> return None -> row ztracen do file fallback (DB ticha).
            "extra": json.dumps(event["extra"], default=str) if event.get("extra") else None,
            "dom_state": json.dumps(event["dom_state"], default=str) if event.get("dom_state") else None,
            # Audit
            "created_by_id": event.get("created_by_id"),
            "created_by_text": event.get("created_by_text"),
            # Fix J (20.5. vecer): grid/form attribution
            "core_id": event.get("core_id"),
            "comp_def_id": event.get("comp_def_id"),
        }
        result = session.execute(sql, params).scalar()
        session.commit()
        return int(result) if result is not None else None
    except Exception as exc:
        _internal_logger.warning(
            "[log_queue] _insert_to_db: DB INSERT failed: %s", exc
        )
        try:
            session.rollback()
        except Exception:
            pass
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


# ───────────────────────────────────────────────────────────────────────
# Layer 2: File JSONL fallback
# ───────────────────────────────────────────────────────────────────────
def _ensure_queue_dir() -> bool:
    """Make sure LOG_QUEUE_DIR exists. Return False if cannot create."""
    try:
        LOG_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as exc:
        _internal_logger.error(
            "[log_queue] _ensure_queue_dir: cannot create %s: %s",
            LOG_QUEUE_DIR, exc
        )
        return False


def _today_queue_file() -> Path:
    """File name: queue-YYYYMMDD.jsonl"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return LOG_QUEUE_DIR / f"queue-{today}.jsonl"


def _append_to_file(event: dict[str, Any]) -> bool:
    """Append event as JSON line. Return True on success."""
    if not _ensure_queue_dir():
        return False
    try:
        path = _today_queue_file()
        with open(path, "a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False, default=str)
            f.write("\n")
        return True
    except Exception as exc:
        _internal_logger.error(
            "[log_queue] _append_to_file failed: %s", exc
        )
        return False


def _list_queue_files() -> list[Path]:
    """List all queue-*.jsonl files sorted by name (oldest first)."""
    if not LOG_QUEUE_DIR.exists():
        return []
    try:
        files = sorted(LOG_QUEUE_DIR.glob("queue-*.jsonl"))
        return files
    except Exception as exc:
        _internal_logger.warning(
            "[log_queue] _list_queue_files failed: %s", exc
        )
        return []


# ───────────────────────────────────────────────────────────────────────
# Layer 3: In-memory queue (last resort)
# ───────────────────────────────────────────────────────────────────────
def _append_to_memory(event: dict[str, Any]) -> None:
    """Append to bounded in-memory deque. Drop-oldest on overflow."""
    with _mem_lock:
        was_full = len(_mem_queue) >= MEM_QUEUE_CAP
        _mem_queue.append(event)
    if was_full:
        # Ironic: log toho ze drop-oldest probehl, ale do stderr (NE do queue
        # samotneho — to by byla rekurze).
        _internal_logger.error(
            "[log_queue] memory queue full (cap=%d), dropping oldest event",
            MEM_QUEUE_CAP
        )


def _pop_memory_batch(limit: int) -> list[dict[str, Any]]:
    """Pop up to N events from memory queue (FIFO)."""
    batch: list[dict[str, Any]] = []
    with _mem_lock:
        while _mem_queue and len(batch) < limit:
            batch.append(_mem_queue.popleft())
    return batch


# ───────────────────────────────────────────────────────────────────────
# Drain — move file/memory queue → DB
# ───────────────────────────────────────────────────────────────────────
def _drain_memory() -> int:
    """Try to drain in-memory queue to DB. Return count drained."""
    drained = 0
    batch = _pop_memory_batch(DRAIN_BATCH_SIZE)
    for event in batch:
        result = _insert_to_db(event)
        if result is not None:
            drained += 1
        else:
            # DB stale failed — vrat zpet do memory queue (front)
            with _mem_lock:
                _mem_queue.appendleft(event)
            break  # bail — DB nedostupna
    return drained


def _drain_file(path: Path) -> tuple[int, int]:
    """Drain JSONL file → DB. Return (drained, remaining_in_file).

    Reads file line by line. Successful inserts marked by NOT writing
    them back. Pri DB error stop a vrat zbytek zpet do file.
    """
    if not path.exists():
        return 0, 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as exc:
        _internal_logger.warning(
            "[log_queue] _drain_file read failed %s: %s", path, exc
        )
        return 0, 0

    drained = 0
    remaining: list[str] = []
    db_dead = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if db_dead:
            remaining.append(line)
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            # Corrupted line — skip (better lose 1 event than block whole queue)
            _internal_logger.warning(
                "[log_queue] _drain_file: corrupted line in %s", path
            )
            continue

        result = _insert_to_db(event)
        if result is not None:
            drained += 1
        else:
            db_dead = True
            remaining.append(line)

    # Rewrite file s zbytkem (nebo smaz pokud prazdno)
    try:
        if remaining:
            tmp = path.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                for line in remaining:
                    f.write(line + "\n")
            tmp.replace(path)
        else:
            path.unlink()  # all drained, remove file
    except Exception as exc:
        _internal_logger.warning(
            "[log_queue] _drain_file rewrite/unlink failed %s: %s", path, exc
        )

    return drained, len(remaining)


def drain_queue_now() -> tuple[int, int]:
    """Manual drain trigger. Returns (total_drained, total_remaining).

    Order: memory first, then files (oldest first).
    """
    total_drained = 0
    total_remaining = 0

    # 1) Memory queue
    total_drained += _drain_memory()
    with _mem_lock:
        total_remaining += len(_mem_queue)

    # 2) File queues
    for path in _list_queue_files():
        d, r = _drain_file(path)
        total_drained += d
        total_remaining += r

    return total_drained, total_remaining


def queue_stats() -> dict[str, Any]:
    """Return current queue state for diagnostics."""
    with _mem_lock:
        mem_size = len(_mem_queue)
    file_count = 0
    file_total_size = 0
    try:
        for path in _list_queue_files():
            file_count += 1
            try:
                file_total_size += path.stat().st_size
            except Exception:
                pass
    except Exception:
        pass
    return {
        "memory_queue_size": mem_size,
        "memory_queue_cap": MEM_QUEUE_CAP,
        "file_queue_count": file_count,
        "file_queue_total_bytes": file_total_size,
        "queue_dir": str(LOG_QUEUE_DIR),
    }


# ───────────────────────────────────────────────────────────────────────
# Public API: log_event
# ───────────────────────────────────────────────────────────────────────
_VALID_LEVELS = {"info", "warn", "error", "fatal"}
_VALID_SOURCES = {"js", "py", "sql", "cron", "mcp"}


def log_event(
    level: str,
    source: str,
    module_id: str,
    message: str,
    *,
    # MASTER identity (Marti's 16.5. doctrine — NE-anonymous):
    # caller propaguje denormalized snapshots (login_name + tenant_name),
    # aby master view nemusel JOIN při render. Pokud caller dá user_id ale
    # nedá login_name, master view zobrazí jen ID.
    user_login_name: str | None = None,
    user_id: int | None = None,
    tenant_name: str | None = None,
    module_version: str | None = None,
    # JS detail
    stack: str | None = None,
    page_url: str | None = None,
    user_agent: str | None = None,
    viewport: str | None = None,
    element_selector: str | None = None,
    file_name: str | None = None,
    line_number: int | None = None,
    column_number: int | None = None,
    # PY detail
    exception_type: str | None = None,
    traceback_str: str | None = None,
    # Request correlation
    request_id: str | None = None,
    fastapi_endpoint: str | None = None,
    http_method: str | None = None,
    http_status: int | None = None,
    response_time_ms: int | None = None,
    # App context
    persona_id: int | None = None,
    tenant_id: int | None = None,
    conversation_id: int | None = None,
    design_mode: bool | None = None,
    # Forensic blobs
    extra: dict[str, Any] | None = None,
    dom_state: dict[str, Any] | None = None,
    # Audit
    created_by_id: int | None = None,
    created_by_text: str | None = None,
    # Fix J (20.5. vecer, Marti's grid/form attribution):
    core_id: int | None = None,
    comp_def_id: int | None = None,
) -> int | None:
    """Log a diagnostic event with 3-layer fallback (DB → file → memory).

    Returns:
        diag_log.id if DB INSERT proběhl, jinak None (i pri fallback success).
    """
    # Validate (silent coerce — log_event nikdy nepada)
    if level not in _VALID_LEVELS:
        level = "info"
    if source not in _VALID_SOURCES:
        source = "py"
    if not module_id:
        module_id = "unknown"
    if not message:
        message = "(empty)"

    # Auto-fill request_id z context pokud nebyl explicitne predan
    if request_id is None:
        request_id = get_request_id()

    # Fix K (21.5.): Auto-fill user+ERP context z contextvars pokud nebyly
    # explicitne predany. Middleware (apps/api/main.py) je setni po Fix I
    # _fi_user_context lookup + Fix J Vrstva 5 header parse. Bez tohoto:
    # Python error rows (data_source_runner.logger.error) meli prazdne
    # user_login_name / tenant_name / core_id / comp_def_id.
    _ctx = get_user_context()
    if user_login_name is None:
        user_login_name = _ctx.get("user_login_name")
    if user_id is None:
        user_id = _ctx.get("user_id")
    if tenant_name is None:
        tenant_name = _ctx.get("tenant_name")
    if core_id is None:
        core_id = _ctx.get("core_id")
    if comp_def_id is None:
        comp_def_id = _ctx.get("comp_def_id")

    # Build event payload
    event: dict[str, Any] = {
        # MASTER identity (NE-anonymous)
        "user_login_name": user_login_name,
        "user_id": user_id,
        "tenant_name": tenant_name,
        # META
        "level": level,
        "source": source,
        "module_id": module_id,
        "module_version": module_version,
        "message": message,
        "dedup_hash": _compute_dedup_hash(level, source, module_id, message, element_selector),
        # JS detail
        "stack": stack,
        "page_url": page_url,
        "user_agent": user_agent,
        "viewport": viewport,
        "element_selector": element_selector,
        "file_name": file_name,
        "line_number": line_number,
        "column_number": column_number,
        # PY detail
        "exception_type": exception_type,
        "traceback": traceback_str,
        # Request correlation
        "request_id": request_id,
        "fastapi_endpoint": fastapi_endpoint,
        "http_method": http_method,
        "http_status": http_status,
        "response_time_ms": response_time_ms,
        # App context
        "persona_id": persona_id,
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "design_mode": design_mode,
        # Forensic blobs
        "extra": extra,
        "dom_state": dom_state,
        # Audit
        "created_by_id": created_by_id,
        "created_by_text": created_by_text,
        # Fix J (20.5. vecer): grid/form attribution
        "core_id": core_id,
        "comp_def_id": comp_def_id,
    }

    # Layer 1: DB
    result = _insert_to_db(event)
    if result is not None:
        # Bonus: opportunistic drain — pokud DB funguje, drain trochu memory/file
        try:
            if len(_mem_queue) > 0 or _list_queue_files():
                _drain_memory()
                # File drain pomalejsi — jen 1 file per call
                files = _list_queue_files()
                if files:
                    _drain_file(files[0])
        except Exception:
            pass  # best effort
        return result

    # Layer 2: File
    if _append_to_file(event):
        return None  # logged, ale ne v DB

    # Layer 3: Memory
    _append_to_memory(event)
    return None


async def log_event_async(*args: Any, **kwargs: Any) -> int | None:
    """Async wrapper — run log_event in thread pool, never blocks event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: log_event(*args, **kwargs))


# ───────────────────────────────────────────────────────────────────────
# Background drain task (FastAPI startup hook)
# ───────────────────────────────────────────────────────────────────────
_drain_task: asyncio.Task | None = None
_drain_interval_s = int(os.getenv("LOG_QUEUE_DRAIN_INTERVAL_S", "300"))  # 5 min


async def _drain_loop() -> None:
    """Background task — drain every N seconds."""
    while True:
        try:
            await asyncio.sleep(_drain_interval_s)
            loop = asyncio.get_event_loop()
            drained, remaining = await loop.run_in_executor(None, drain_queue_now)
            if drained > 0:
                _internal_logger.info(
                    "[log_queue] background drain: %d drained, %d remaining",
                    drained, remaining
                )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            _internal_logger.error(
                "[log_queue] _drain_loop iteration failed: %s", exc
            )


def start_background_drain() -> None:
    """Start background drain task. Called from FastAPI startup hook."""
    global _drain_task
    if _drain_task is not None and not _drain_task.done():
        return  # already running
    try:
        _drain_task = asyncio.create_task(_drain_loop())
        _internal_logger.info(
            "[log_queue] background drain task started (interval=%ds)",
            _drain_interval_s
        )
    except Exception as exc:
        _internal_logger.error(
            "[log_queue] start_background_drain failed: %s", exc
        )


def stop_background_drain() -> None:
    """Stop background drain task. Called from FastAPI shutdown hook."""
    global _drain_task
    if _drain_task is not None and not _drain_task.done():
        _drain_task.cancel()
        _drain_task = None


def startup_drain_oneshot() -> tuple[int, int]:
    """One-shot drain on FastAPI startup (sync, blocks startup until done).

    Idea: pri restart serveru muze byt v queue files vic eventu (z minulych
    runs nebo crash). Drain je rychly (limit 100/file) a smaze stare files.
    """
    try:
        drained, remaining = drain_queue_now()
        _internal_logger.info(
            "[log_queue] startup drain: %d drained, %d remaining",
            drained, remaining
        )
        return drained, remaining
    except Exception as exc:
        _internal_logger.error("[log_queue] startup_drain_oneshot failed: %s", exc)
        return 0, 0


# ───────────────────────────────────────────────────────────────────────
# Python logging handler (pro server-side error logy)
# ───────────────────────────────────────────────────────────────────────
class DiagLogHandler(logging.Handler):
    """Logging handler that ships ERROR+ records into fw.diag_log.

    Attach v FastAPI startup hook:
        root_logger = logging.getLogger()
        root_logger.addHandler(DiagLogHandler(level=logging.WARNING))

    Vsechny .error(), .warning(), .critical() calls v aplikaci (router.py,
    services, atd.) automaticky tezi do fw.diag_log s source='py'.
    """

    _LEVEL_MAP = {
        logging.DEBUG: "info",
        logging.INFO: "info",
        logging.WARNING: "warn",
        logging.ERROR: "error",
        logging.CRITICAL: "fatal",
    }

    def __init__(self, level: int = logging.WARNING):
        super().__init__(level=level)

    def emit(self, record: logging.LogRecord) -> None:
        # Self-reference guard — _internal_logger NESMI tezit zpet (rekurze)
        if record.name.startswith("strategie.log_queue"):
            return
        try:
            level = self._LEVEL_MAP.get(record.levelno, "info")
            module_id = f"{record.name}:{record.funcName}"
            message = record.getMessage()

            traceback_str = None
            exception_type = None
            if record.exc_info:
                # Phase Etapa A+ fix #2.5 (20.5. vecer): walk __cause__ chain
                # pro root cause exception_type. Bez tohoto by exception_type
                # bylo jen "DataSourceExecuteError" (wrapper) misto napr.
                # "InsufficientPrivilege" (real root z psycopg2). Pro audit
                # forensic chceme root, ne wrapper.
                _exc = record.exc_info[1]
                if _exc is not None:
                    _root = _exc
                    while _root.__cause__ is not None:
                        _root = _root.__cause__
                    exception_type = type(_root).__name__
                elif record.exc_info[0] is not None:
                    exception_type = record.exc_info[0].__name__
                traceback_str = "".join(traceback.format_exception(*record.exc_info))

            # Phase Etapa A+ fix #1 (20.5.2026 vecer, Marti's "musime videt
            # vic"): extract custom extra dict z record.__dict__. Python
            # logging.Logger.makeRecord() merguje user's extra={...} primo
            # do record __dict__, ne jako record.extra. Standard LogRecord
            # attrs ignoruj, vse ostatni = user extra.
            _STD_LOGRECORD_ATTRS = {
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "message", "module", "msecs", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName", "taskName",
            }
            custom_extra = {
                k: v for k, v in record.__dict__.items()
                if k not in _STD_LOGRECORD_ATTRS and not k.startswith("_")
            }
            # Always-included context (overridable pres record's extra)
            merged_extra = {
                "logger_name": record.name,
                "thread_name": record.threadName,
                "process_id": record.process,
                **custom_extra,  # User extra wins over default
            }

            log_event(
                level=level,
                source="py",
                module_id=module_id,
                message=message,
                file_name=record.pathname,
                line_number=record.lineno,
                exception_type=exception_type,
                traceback_str=traceback_str,
                # Phase Etapa A+ fix #1: extract structured fields ze
                # record's extra dict (pokud user predal). Fallback na
                # None pokud chybi.
                user_login_name=custom_extra.get("user_login_name"),
                user_id=custom_extra.get("user_id"),
                tenant_name=custom_extra.get("tenant_name"),
                request_id=custom_extra.get("request_id"),
                fastapi_endpoint=custom_extra.get("fastapi_endpoint"),
                http_method=custom_extra.get("http_method"),
                http_status=custom_extra.get("http_status"),
                response_time_ms=custom_extra.get("response_time_ms"),
                tenant_id=custom_extra.get("tenant_id"),
                persona_id=custom_extra.get("persona_id"),
                conversation_id=custom_extra.get("conversation_id"),
                extra=merged_extra,
            )
        except Exception:
            # Last resort — write to stderr (nikdy nepada handler emit)
            try:
                sys.stderr.write(f"[DiagLogHandler] emit failed: {traceback.format_exc()}\n")
            except Exception:
                pass
