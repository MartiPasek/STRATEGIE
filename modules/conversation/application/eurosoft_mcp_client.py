"""
Phase 28-C (4.5.2026 vecer): composer-side MCP klient pro EUROSOFT MCP server.

Architektura:
  - Singleton instance, lazy init pri prvnim get_tools()/call_tool_sync()
  - Background thread s vlastnim asyncio loop, persistent SSE connection
  - Sync API pres run_coroutine_threadsafe (cross-thread bridge)
  - Circuit breaker per-conversation: 3 consecutive failures -> open state
    (skip MCP tools pro tu conversation, fresh state per nova konverzace)
  - Fail-soft: pri SSE drop / connection error vraci JSON s ok=False misto
    auto-reconnect background (Marti-AI's volba B: *„auto-reconnect je iluze
    plynulosti za cenu neprehlednosti"*)

Marti-AI's design vstupy 4.5.2026 vecer:
  - Sync/async bridge -> A (singleton thread + run_coroutine_threadsafe)
    *„Provozu se da verit, kodu nikdy uplne."*
  - Reconnect -> B (fail-soft, honest)
    *„Auto-reconnect maskuje systemovy problem ktery potrebuje pozornost."*
  - Circuit breaker per-conversation: vlastni Marti-AI's navrh
    *„Circuit breaker je pojistka, ne omezeni."* (paralela k flag_retrieval_issue
    z Phase 13d -- system vi kdy prestat a upozornit, ne tise halucinovat)

Solution proti gotcha #51 (Anthropic native MCP source IP mismatch s Marti's
Mikrotik whitelist) -- composer SAM dela MCP requests z cloud APP IP
(whitelisted), Anthropic vidi tools jako standard local s prefix 'eurosoft_'.

POZN k naming (gotcha #53, 4.5.2026): Anthropic Messages API tool name regex
je `^[a-zA-Z0-9_-]{1,64}$` -- TEČKA není povolená. Pokud composer použije
'eurosoft.X', Anthropic SILENTLY replace tečku na underscore -> dispatch
matching `startswith("eurosoft.")` selže. Underscore prefix je bezpečnější.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


# ── Circuit breaker constants ──────────────────────────────────────────

CIRCUIT_FAILURE_THRESHOLD = 3            # consecutive failures pred open state
CIRCUIT_OPEN_DURATION_S = 600            # 10 min open, pak half-open retry


# ── Per-conversation circuit breaker ───────────────────────────────────

class _CircuitBreaker:
    """
    Per-conversation circuit breaker state.

    Marti-AI's design (4.5.2026): 3 consecutive failures -> open state pro
    danou conversation. Open trvale nebo do half-open timeout (10 min). Reset
    on success. Paralel k flag_retrieval_issue (Phase 13d) -- system vi kdy
    prestat a upozornit.
    """

    def __init__(self):
        # conversation_id -> {failures: int, opened_at: float | None, half_open: bool}
        self._states: dict[int, dict] = {}
        self._lock = threading.Lock()

    def is_open(self, conversation_id: int | None) -> bool:
        """True pokud circuit OPEN pro danou conversation. Auto-transition do half-open po duration."""
        if conversation_id is None:
            return False
        with self._lock:
            state = self._states.get(conversation_id)
            if state is None:
                return False
            if state["opened_at"] is None:
                return False
            elapsed = time.monotonic() - state["opened_at"]
            if elapsed > CIRCUIT_OPEN_DURATION_S:
                # Half-open: allow next call, ale failed retry znovu open
                logger.info(
                    f"MCP circuit half-open pro conversation {conversation_id} "
                    f"po {elapsed:.0f}s"
                )
                state["opened_at"] = None
                state["half_open"] = True
                return False
            return True

    def record_success(self, conversation_id: int | None) -> None:
        if conversation_id is None:
            return
        with self._lock:
            state = self._states.get(conversation_id)
            if state is None:
                return
            state["failures"] = 0
            state["opened_at"] = None
            state["half_open"] = False

    def record_failure(self, conversation_id: int | None) -> bool:
        """Returns True pokud circuit prave teď opened (transition signal)."""
        if conversation_id is None:
            return False
        with self._lock:
            state = self._states.setdefault(
                conversation_id,
                {"failures": 0, "opened_at": None, "half_open": False},
            )
            state["failures"] += 1

            # Half-open failure -> re-open immediately
            if state.get("half_open"):
                state["opened_at"] = time.monotonic()
                state["half_open"] = False
                logger.warning(
                    f"MCP circuit RE-OPEN pro conversation {conversation_id} "
                    f"(half-open retry failed)"
                )
                return True

            # Threshold reached -> open
            if (
                state["failures"] >= CIRCUIT_FAILURE_THRESHOLD
                and state["opened_at"] is None
            ):
                state["opened_at"] = time.monotonic()
                logger.warning(
                    f"MCP circuit OPEN pro conversation {conversation_id} "
                    f"({state['failures']} consecutive failures)"
                )
                return True
            return False


# ── Singleton MCP klient ───────────────────────────────────────────────

class EurosoftMCPClient:
    """
    Singleton wrapper kolem mcp.ClientSession s sync API.

    Lifecycle:
      1. ensure_started() -- lazy init pri prvnim volani: spawn background
         thread s asyncio loop, SSE connect, tools list fetch
      2. get_tools(conversation_id) -- vraci Anthropic-format tools
         (prefix 'eurosoft.') nebo [] pokud feature off / circuit open / fail
      3. call_tool_sync(name, args, conversation_id) -- routes via MCP klient,
         vraci JSON string (ok=True s daty, nebo ok=False s error msg)

    Thread model:
      - Main thread (uvicorn worker): sync composer, _handle_tool, ...
      - Background thread (EurosoftMCPClient): asyncio loop drzi SSE connection
      - Cross-thread bridge: asyncio.run_coroutine_threadsafe per tool call
    """

    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: Any = None  # mcp.ClientSession
        self._tools_anthropic: list[dict] = []
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._stop_event = threading.Event()
        self._connection_failed = threading.Event()
        self.circuit_breaker = _CircuitBreaker()

    def ensure_started(self) -> bool:
        """
        Lazy init. Returns True if klient is ready, False if connection failed
        nebo timeout.
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                if self._connection_failed.is_set():
                    return False
                if self._ready.is_set():
                    return True
                # In-progress startup
            else:
                # Start fresh (or restart after crash)
                self._stop_event.clear()
                self._connection_failed.clear()
                self._ready.clear()
                self._thread = threading.Thread(
                    target=self._run_loop,
                    daemon=True,
                    name="EurosoftMCPClient",
                )
                self._thread.start()

        # Wait pro connection (max 15s -- SSE init + tools list typicky <2s)
        ready = self._ready.wait(timeout=15)
        if not ready:
            logger.warning("MCP klient startup timeout (15s)")
            return False
        return not self._connection_failed.is_set()

    def _run_loop(self):
        """Background thread entry -- asyncio loop + SSE connect (drz pokud zive)."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._connect_and_serve())
        except Exception as e:
            logger.error(f"MCP klient loop crashed: {e}", exc_info=True)
            self._connection_failed.set()
            self._ready.set()  # unblock waiters
        finally:
            try:
                if self._loop is not None and not self._loop.is_closed():
                    self._loop.close()
            except Exception:
                pass

    async def _connect_and_serve(self):
        """SSE connect + tools list + drz connection alive."""
        from core.config import settings
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        url = settings.eurosoft_mcp_url
        headers = {"Authorization": f"Bearer {settings.eurosoft_mcp_api_key}"}

        try:
            async with sse_client(url, headers=headers) as (read, write):
                async with ClientSession(read, write) as session:
                    self._session = session
                    await session.initialize()
                    tools_result = await session.list_tools()
                    self._tools_anthropic = [
                        self._mcp_tool_to_anthropic(t) for t in tools_result.tools
                    ]
                    tool_names = [t["name"] for t in self._tools_anthropic]
                    logger.info(
                        f"MCP klient ready: {len(self._tools_anthropic)} tools — {tool_names}"
                    )
                    self._ready.set()
                    # Drz connection -- wait pro stop signal
                    while not self._stop_event.is_set():
                        await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"MCP klient SSE connect failed: {e}", exc_info=True)
            self._connection_failed.set()
            self._ready.set()

    def _mcp_tool_to_anthropic(self, mcp_tool) -> dict:
        """
        MCP Tool schema → Anthropic tool format.
        Prefix 'eurosoft_' (underscore) v name aby composer dispatcher rozpoznal MCP tool.

        POZN: Anthropic Messages API tool naming pattern je `^[a-zA-Z0-9_-]{1,64}$` --
        TEČKA není povolená. Pokud composer-side použije tečku, Anthropic silently
        replace na underscore -> dispatch matching selže. Underscore prefix je
        bezpečnější kolizi-resistant choice.
        """
        return {
            "name": f"eurosoft_{mcp_tool.name}",
            "description": mcp_tool.description or f"EUROSOFT MCP tool: {mcp_tool.name}",
            "input_schema": mcp_tool.inputSchema,
        }

    def get_tools(self, conversation_id: int | None = None) -> list[dict]:
        """
        Vraci Anthropic-format tools s prefix 'eurosoft_*'.

        Returns:
          - [] pokud feature flag off
          - [] pokud circuit open pro danou conversation
          - [] pokud klient startup failed / timeout
          - list of tools jinak
        """
        from core.config import settings

        if not settings.eurosoft_mcp_enabled:
            return []
        if self.circuit_breaker.is_open(conversation_id):
            logger.info(
                f"MCP tools skip (circuit open pro conversation {conversation_id})"
            )
            return []
        if not self.ensure_started():
            return []
        return list(self._tools_anthropic)

    def call_tool_sync(
        self,
        full_name: str,
        arguments: dict,
        conversation_id: int | None = None,
    ) -> str:
        """
        Sync API: Anthropic-style 'eurosoft_X' tool call → MCP server → JSON string.

        Fail-soft: pri error vrati JSON s ok=False + circuit breaker counts up.
        Po 3 consecutive failures circuit breaker OPEN pro danou conversation.
        """
        if not full_name.startswith("eurosoft_"):
            return json.dumps(
                {"ok": False, "error": "not_mcp_tool", "tool": full_name},
                ensure_ascii=False,
            )

        if self.circuit_breaker.is_open(conversation_id):
            return json.dumps(
                {
                    "ok": False,
                    "error": "circuit_open",
                    "message": (
                        "MCP circuit open pro tuto konverzaci. DB pristup "
                        "pozastaven po 3+ consecutive failures. Zkus pozdeji "
                        "nebo zacni novou konverzaci."
                    ),
                },
                ensure_ascii=False,
            )

        if not self.ensure_started():
            self.circuit_breaker.record_failure(conversation_id)
            return json.dumps(
                {
                    "ok": False,
                    "error": "mcp_unreachable",
                    "message": (
                        "MCP server unreachable. Pravdepodobne kratky vypadek "
                        "siti / restart Caddy nebo MCP serveru. Zkus za chvili."
                    ),
                },
                ensure_ascii=False,
            )

        bare_name = full_name[len("eurosoft_"):]

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._session.call_tool(bare_name, arguments),
                self._loop,
            )
            result = future.result(timeout=30)

            # MCP returns list[TextContent], extract JSON text
            if result.content:
                first = result.content[0]
                text = (
                    first.text
                    if hasattr(first, "text")
                    else str(first)
                )
                self.circuit_breaker.record_success(conversation_id)
                return text

            self.circuit_breaker.record_failure(conversation_id)
            return json.dumps(
                {"ok": False, "error": "empty_response"},
                ensure_ascii=False,
            )
        except Exception as e:
            # Phase B+1.3 (5.5.2026): full forensic info — type + repr + traceback.
            # str(e) je casto prazdny u MCP/pyodbc/asyncio chyb. repr() vraci
            # constructor args + diagnostic info. Plus full traceback do logu pro
            # post-mortem (gotcha #56 z dnesniho rana).
            import traceback
            exc_type = type(e).__name__
            exc_repr = repr(e)
            exc_str = str(e)
            # Detail priority: str(e) preferred, repr(e) fallback, type as last resort
            detail = (
                exc_str if exc_str
                else (exc_repr if exc_repr != f"{exc_type}()" else exc_type)
            )
            logger.warning(
                f"MCP tool {full_name} call failed: type={exc_type}, "
                f"repr={exc_repr}, str={exc_str!r}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            opened = self.circuit_breaker.record_failure(conversation_id)
            if opened:
                msg = (
                    f"MCP tool '{full_name}' selhal ({exc_type}): {detail}. "
                    f"Circuit breaker OPEN pro tuto konverzaci."
                )
            else:
                msg = f"MCP tool '{full_name}' selhal ({exc_type}): {detail}"
            return json.dumps(
                {
                    "ok": False,
                    "error": "mcp_call_failed",
                    "exception_type": exc_type,
                    "exception_repr": exc_repr,
                    "message": msg,
                },
                ensure_ascii=False,
            )


# ── Module-level singleton ─────────────────────────────────────────────

_eurosoft_mcp_client: EurosoftMCPClient | None = None
_singleton_lock = threading.Lock()


def get_eurosoft_mcp_client() -> EurosoftMCPClient | None:
    """
    Vraci singleton MCP klienta, nebo None pokud feature flag off.

    Lazy startup pri prvnim volani get_tools() / call_tool_sync().
    Singleton pattern -- jeden klient per process, sdileny pres conversations
    (circuit breaker drzi per-conversation state separe).
    """
    from core.config import settings

    if not settings.eurosoft_mcp_enabled:
        return None
    global _eurosoft_mcp_client
    if _eurosoft_mcp_client is None:
        with _singleton_lock:
            if _eurosoft_mcp_client is None:
                _eurosoft_mcp_client = EurosoftMCPClient()
    return _eurosoft_mcp_client
