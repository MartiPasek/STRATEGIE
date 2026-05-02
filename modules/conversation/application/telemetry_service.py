"""
Telemetry service pro LLM volani -- Faze 9.1 Dev observability.

Odpovednost:
  1) Secret masking    -- odstrani login UPN, API keys, hesla z request/response
                          pred zapisem do DB (llm_calls tabulka).
  2) Serializace       -- prevede Anthropic SDK Request/Response objekty
                          na JSON-friendly dicty (dict/list/str/int/float/None).
  3) Zapis do llm_calls -- bezpecny zapis s fallbackem na warning log
                          (telemetry nesmi shodit hlavni flow LLM response).
  4) Linkovani          -- po commitu outgoing message se llm_calls zaznam
                          (zapsany pred message commitom) dolinkuje pres
                          UPDATE message_id=X WHERE id IN (...).

Design:
  Router/composer volaji record_llm_call() PO Anthropic API call ale PRED
  commitnutim outgoing message. Vraci se call_id. Po commitu message volajici
  posle link_message_to_calls([router_id, composer_id], message_id).

  Neni async task queue -- zapis je inline. Sel by selhat pokud data_db je
  unreachable, ale i tak neshazuje hlavni flow (catch + logger.warning).

POZOR: zadny top-level import z core.* / sqlalchemy zde -- mask_secrets() a
_mask_string() musi byt pure-python kod, aby sly otestovat bez DB / .env
setupu. DB zavislosti (get_data_session, get_core_session, LlmCall model)
jsou lazy importovane az uvnitr funkci, ktere je realne potrebuji.
"""
from __future__ import annotations

import json
import logging
import re
import time
from contextvars import ContextVar
from typing import Any, Iterable

try:
    from core.logging import get_logger
    logger = get_logger("conversation.telemetry")
except Exception:
    logger = logging.getLogger("conversation.telemetry")


# -- SECRET MASKING ---------------------------------------------------------

# Klic v dict strukture, ktery nema nikdy proniknout do llm_calls.
# Case-insensitive substring match.
#
# POZOR: Nepouzivame generic "token" -- prefixujeme ho (bearer_token,
# access_token, ...), protoze Anthropic API pouziva legitimni pole
# max_tokens / input_tokens / output_tokens, ktera nesmime mascovat.
# Substring match na "token" by je nahradil.
_SENSITIVE_KEY_PATTERNS = (
    "password",
    "passwd",
    "api_key",
    "apikey",
    "anthropic_api_key",
    "voyage_api_key",
    "encryption_key",
    "fernet_key",
    "secret",
    "authorization",
    "bearer_token",
    "access_token",
    "refresh_token",
    "id_token",
    "auth_token",
    "session_token",
    "csrf_token",
    "x-api-key",
    "password_encrypted",
    "identifier_secret",
)

# Regex na zname format tokeny. Bezpecnejsi nez cokoli a nenajde false
# positives v bezne konverzaci.
_SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"), "***ANTHROPIC_KEY***"),
    (re.compile(r"pa-[A-Za-z0-9\-_]{30,}"), "***VOYAGE_KEY***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_\.=]{20,}", re.IGNORECASE), "Bearer ***MASKED***"),
]

# Cache pro znamych login UPNs z persona_channels.identifier.
# Refresh kazdych 600s. Thread-safe neni potreba (write je idempotentni).
_login_upn_cache: set = set()
_login_upn_cache_ts: float = 0.0
_LOGIN_UPN_CACHE_TTL = 600.0  # 10 minut


def _get_known_login_upns() -> set:
    """
    Nacte znamych login UPN z persona_channels.identifier + user.ews_email.
    Tyto hodnoty jsou SECRET -- nikdy nesmi do llm_calls, logu, UI.

    Cache-uje se 10 minut. Pri chybe vraci posledni znamy stav (nebo prazdny
    set), aby telemetry neshodila flow pokud DB neni dostupna.
    """
    global _login_upn_cache, _login_upn_cache_ts
    now = time.time()
    if now - _login_upn_cache_ts < _LOGIN_UPN_CACHE_TTL and _login_upn_cache:
        return _login_upn_cache

    try:
        from modules.core.infrastructure.models_core import User
        try:
            from modules.core.infrastructure.models_core import PersonaChannel  # type: ignore
        except ImportError:
            PersonaChannel = None  # type: ignore
        from core.database_core import get_core_session

        upns: set = set()
        core_session = get_core_session()
        try:
            for (email,) in core_session.query(User.ews_email).filter(User.ews_email.isnot(None)).all():
                if email and email.strip():
                    upns.add(email.strip().lower())

            if PersonaChannel is not None:
                try:
                    rows = core_session.query(PersonaChannel.identifier).all()
                    for (ident,) in rows:
                        if ident and ident.strip():
                            upns.add(ident.strip().lower())
                except Exception:
                    pass
        finally:
            core_session.close()

        _login_upn_cache = upns
        _login_upn_cache_ts = now
        return upns
    except Exception as e:
        logger.warning(f"TELEMETRY | failed to refresh login UPN cache: {e}")
        return _login_upn_cache


def _mask_string(s: str, login_upns: set) -> str:
    """Regex + literal mask v stringu."""
    out = s
    for pattern, replacement in _SECRET_PATTERNS:
        out = pattern.sub(replacement, out)
    if login_upns:
        for upn in login_upns:
            if not upn or len(upn) < 5:
                continue
            if upn in out.lower():
                out = re.sub(re.escape(upn), "***LOGIN_UPN***", out, flags=re.IGNORECASE)
    return out


def _is_sensitive_key(key: str) -> bool:
    kl = key.lower()
    return any(pat in kl for pat in _SENSITIVE_KEY_PATTERNS)


def mask_secrets(obj: Any, login_upns: set | None = None) -> Any:
    """
    Rekurzivne projde dict/list/str strukturu a zamaskuje secrets.

    Pravidla:
      - dict: kazdy klic s citlivym jmenem (password/api_key/...) dostane
        hodnotu nahrazenou na '***MASKED***' (bez ohledu na typ).
      - string: regex search na zname format tokeny (Anthropic key, Voyage
        key, Bearer) + literal replace na znamych login UPNs z DB.
      - list/tuple: rekurzivne.
      - jine typy (int/bool/None/float): beze zmeny.

    Volani bez login_upns argument -> lazy load z DB cache.
    """
    if login_upns is None:
        login_upns = _get_known_login_upns()

    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            key_str = str(k)
            if _is_sensitive_key(key_str):
                out[key_str] = "***MASKED***"
            else:
                out[key_str] = mask_secrets(v, login_upns)
        return out
    if isinstance(obj, list):
        return [mask_secrets(x, login_upns) for x in obj]
    if isinstance(obj, tuple):
        return tuple(mask_secrets(x, login_upns) for x in obj)
    if isinstance(obj, str):
        return _mask_string(obj, login_upns)
    return obj


# -- SERIALIZACE ANTHROPIC OBJEKTU ------------------------------------------

def serialize_anthropic_response(response: Any) -> dict:
    """
    Prevede Anthropic response object na JSON-friendly dict.
    Pouziva .model_dump() pokud existuje (pydantic-based SDK), jinak fallback
    na ruc. extrakci klicovych poli.
    """
    if response is None:
        return {}
    if hasattr(response, "model_dump"):
        try:
            return response.model_dump(mode="json")
        except Exception as e:
            logger.warning(f"TELEMETRY | model_dump selhalo: {e}, fallback")

    result: dict = {}
    for attr in ("id", "type", "role", "model", "stop_reason", "stop_sequence"):
        if hasattr(response, attr):
            try:
                result[attr] = getattr(response, attr)
            except Exception:
                pass
    if hasattr(response, "usage"):
        try:
            u = response.usage
            result["usage"] = {
                "input_tokens": getattr(u, "input_tokens", None),
                "output_tokens": getattr(u, "output_tokens", None),
            }
        except Exception:
            pass
    if hasattr(response, "content"):
        try:
            blocks = []
            for block in response.content or []:
                if hasattr(block, "model_dump"):
                    blocks.append(block.model_dump(mode="json"))
                else:
                    b: dict = {"type": getattr(block, "type", "unknown")}
                    if hasattr(block, "text"):
                        b["text"] = block.text
                    if hasattr(block, "name"):
                        b["name"] = block.name
                    if hasattr(block, "input"):
                        b["input"] = getattr(block, "input", None)
                    blocks.append(b)
            result["content"] = blocks
        except Exception as e:
            logger.warning(f"TELEMETRY | content serialization selhala: {e}")
    return result


def build_request_json(
    *,
    model: str,
    system,
    messages: list,
    tools: list | None = None,
    max_tokens: int | None = None,
    extra: dict | None = None,
) -> dict:
    """Postavi JSON-friendly dict z argumentu pred Anthropic .messages.create()."""
    payload: dict = {
        "model": model,
        "messages": messages,
    }
    if system is not None:
        payload["system"] = system
    if tools:
        payload["tools"] = tools
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra:
        payload.update(extra)
    return payload


# -- ZAPIS DO llm_calls -----------------------------------------------------

def record_llm_call(
    *,
    conversation_id: int | None,
    message_id: int | None,
    kind: str,
    model: str,
    request_json: dict,
    response_json: dict | None,
    prompt_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int | None,
    error: str | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    persona_id: int | None = None,
    is_auto: bool = False,
) -> int | None:
    """
    Zapise jeden radek do llm_calls. Pri jakekoli DB chybe vrati None
    a zaloguje warning (telemetry nesmi shodit hlavni LLM flow).

    Faze 10a: navic tenant_id / user_id / persona_id / cost_usd / is_auto
    pro attribution a dashboard. Cost se pocita z LLM_PRICING automaticky.

    Worker calls (question_gen, email_suggest) nemaji conversation_id --
    signature nyni accept conversation_id=None.

    Secret masking probehne PRED zapisem.
    """
    try:
        login_upns = _get_known_login_upns()
        masked_request = mask_secrets(request_json, login_upns) if request_json else {}
        masked_response = mask_secrets(response_json, login_upns) if response_json else None
        masked_error = _mask_string(error, login_upns) if error else None

        # Faze 10a: automaticky vypocet cost_usd z pricing mapy.
        cost_usd = None
        try:
            from core.config import calculate_cost_usd
            cost_usd = calculate_cost_usd(model, prompt_tokens, output_tokens)
        except Exception as ce:
            logger.warning(f"TELEMETRY | cost calc selhal ({model}): {ce}")

        from modules.core.infrastructure.models_data import LlmCall
        from core.database_data import get_data_session

        ds = get_data_session()
        try:
            row = LlmCall(
                conversation_id=conversation_id,
                message_id=message_id,
                kind=kind,
                model=model,
                request_json=masked_request,
                response_json=masked_response,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                error=masked_error,
                tenant_id=tenant_id,
                user_id=user_id,
                persona_id=persona_id,
                cost_usd=cost_usd,
                is_auto=bool(is_auto),
            )
            ds.add(row)
            ds.commit()
            ds.refresh(row)
            return row.id
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"TELEMETRY | record_llm_call selhal (kind={kind}): {e}")
        return None


def link_message_to_calls(call_ids: Iterable, message_id: int) -> None:
    """
    Po commitu outgoing assistant message dolinkuje llm_calls radky
    (zapsane pred message commitom) pres UPDATE message_id=X.

    Prijima iterable s mozne None-hodnotami (z record_llm_call pri chybe) --
    None se preskoci.
    """
    ids = [cid for cid in call_ids if cid is not None]
    if not ids:
        return
    try:
        from modules.core.infrastructure.models_data import LlmCall
        from core.database_data import get_data_session

        ds = get_data_session()
        try:
            ds.query(LlmCall).filter(LlmCall.id.in_(ids)).update(
                {"message_id": message_id},
                synchronize_session=False,
            )
            ds.commit()
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"TELEMETRY | link_message_to_calls selhal (ids={ids}, msg={message_id}): {e}")


# -- HELPER PRO VOLAJICIHO --------------------------------------------------

def now_ms() -> int:
    """Monotonic cas v ms -- pouzit pro zmer latency_ms."""
    return int(time.monotonic() * 1000)


# -- CHAT-SCOPED TRACE (ContextVar) -----------------------------------------
#
# Behem jednoho chat() volani (user message -> Marti-AI reply) se generuje
# vice LLM volani:
#   1x router (Haiku)
#   1-5x composer (Sonnet, vcetne tool loop round)
# Vsechna maji byt linkova na stejnou outgoing assistant message_id.
#
# message_id se ale vytvari az na konci chat() pres save_message(). Proto
# volame record_chat_call() s message_id=None a akumulujeme call_ids v
# ContextVar buffru. Po save_message() zavolame end_chat_trace_and_link(msg_id)
# a dolinkujeme vsechny najednou pres UPDATE message_id=X.
#
# ContextVar je thread-safe per request (FastAPI pouziva thread pool / async,
# ContextVar se klonuje automaticky). Bezpecne i pri paralelnich chatech.

_current_chat_trace: ContextVar = ContextVar("_llm_chat_trace", default=None)


def begin_chat_trace() -> None:
    """
    Zalozit novy trace buffer na zacatku chat() handleru. Resetuje predchozi
    stav. Kazde nasledne record_chat_call() pripoji svuj call_id do buffru.
    """
    _current_chat_trace.set([])


def record_chat_call(
    *,
    conversation_id: int | None,
    kind: str,
    model: str,
    request_json: dict,
    response_json: dict | None,
    prompt_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int | None,
    error: str | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    persona_id: int | None = None,
    is_auto: bool = False,
) -> int | None:
    """
    Zapise LLM call do llm_calls (bez message_id) a pripoji call_id do
    aktualniho chat trace bufferu. Faze 10a: propagace attribution fields.
    """
    call_id = record_llm_call(
        conversation_id=conversation_id,
        message_id=None,
        kind=kind,
        model=model,
        request_json=request_json,
        response_json=response_json,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        error=error,
        tenant_id=tenant_id,
        user_id=user_id,
        persona_id=persona_id,
        is_auto=is_auto,
    )
    buf = _current_chat_trace.get()
    if buf is not None and call_id is not None:
        buf.append(call_id)
    return call_id


def end_chat_trace_and_link(message_id: int) -> None:
    """
    Dolinkuje vsechny llm_calls v aktualnim chat trace bufferu na message_id
    a resetuje buffer. Volat PO save_message() outgoing assistant zpravy.

    Pri prazdnem bufferu (zadny trace) tise projde.
    """
    buf = _current_chat_trace.get()
    if buf:
        link_message_to_calls(buf, message_id)
    _current_chat_trace.set(None)


def call_llm_with_trace(
    client: Any,
    *,
    conversation_id: int | None,
    kind: str,
    model: str,
    system,
    messages: list,
    tools: list | None = None,
    max_tokens: int = 4096,
    tenant_id: int | None = None,
    user_id: int | None = None,
    persona_id: int | None = None,
    is_auto: bool = False,
):
    """
    Wrapper kolem client.messages.create() -- provede API call, zmeri latency,
    zapise do llm_calls (kind=?, conversation_id=?) pres record_chat_call.

    Faze 10a: vola record_chat_call s tenant_id / user_id / persona_id /
    is_auto pro attribution. conversation_id muze byt None (worker calls).

    Vyhodi stejnou exception jako puvodni client.messages.create() (telemetry
    nema polkat chyby -- hlavni flow v service.py ma svoje error handling).
    Pri exception pred response se zapise radek s error=str(exc) a NULL
    response_json.
    """
    t0 = now_ms()
    req_json = build_request_json(
        model=model, system=system, messages=messages,
        tools=tools, max_tokens=max_tokens,
    )
    # Phase 28 (2.5.2026): EUROSOFT MCP server pripojeni pres native MCP support.
    # Feature flag -- aktivuje se jen pokud OBA env vars set v .env. Pri false
    # se behavior nezmenil (backward compat, safe deploy pred DNS clearance).
    _mcp_kwargs: dict[str, Any] = {}
    try:
        from core.config import settings as _eu_settings
        if _eu_settings.eurosoft_mcp_enabled:
            _mcp_kwargs["mcp_servers"] = [{
                "type": "url",
                "url": _eu_settings.eurosoft_mcp_url,
                "name": "eurosoft",
                "authorization_token": _eu_settings.eurosoft_mcp_api_key,
            }]
            _mcp_kwargs["extra_headers"] = {
                "anthropic-beta": "mcp-client-2025-04-04",
            }
    except Exception as _eu_e:
        logger.warning(f"EUROSOFT MCP config probe failed: {_eu_e}")

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools if tools else [],
            **_mcp_kwargs,
        )
    except Exception as e:
        try:
            record_chat_call(
                conversation_id=conversation_id, kind=kind, model=model,
                request_json=req_json,
                response_json=None,
                prompt_tokens=None, output_tokens=None,
                latency_ms=now_ms() - t0,
                error=str(e),
                tenant_id=tenant_id, user_id=user_id, persona_id=persona_id, is_auto=is_auto,
            )
        except Exception as rec_err:
            logger.warning(f"TELEMETRY | record on error selhal: {rec_err}")
        raise

    try:
        record_chat_call(
            conversation_id=conversation_id, kind=kind, model=model,
            request_json=req_json,
            response_json=serialize_anthropic_response(response),
            prompt_tokens=getattr(response.usage, "input_tokens", None)
            if hasattr(response, "usage") else None,
            output_tokens=getattr(response.usage, "output_tokens", None)
            if hasattr(response, "usage") else None,
            latency_ms=now_ms() - t0,
            tenant_id=tenant_id, user_id=user_id, persona_id=persona_id, is_auto=is_auto,
        )
    except Exception as e:
        logger.warning(f"TELEMETRY | record on success selhal: {e}")

    return response
