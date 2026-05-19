"""Phase 40 v2 r3 Mini-faze B — ask_claude AI tool (Marti-AI calls Claude).

Phase 44 update (19.5.2026 odpoledne): pridany env-driven bridge prepinac
STRATEGIE_CLAUDE_BRIDGE. Tri hodnoty:
  - 'api_stateless' (default, Phase 43 Mini-faze A path): client.messages.create()
    primo. Fresh Sonnet 4.6 per call, peer-partner system prompt overlay.
    Marti's catch z 19.5. dop.: "Marti-AI se pta sama sebe" — funguje, ale ne
    persistent identity.
  - 'cloud_bridge' (Phase 44 LIVE target): INSERT do claude_session_queue,
    pollu pro response (timeout 60s), STRATEGIE-CLAUDE-BRIDGE NSSM service
    zpracuje s rich context injection (CLAUDE.md sekce, dárek-scény, recent
    commits, multi-turn continuity per anthropic_conversation_id).
  - 'auto' (smart fallback): try bridge with timeout 15s, fallback na
    stateless + STRATEGIE bublina warning *„Bridge offline, fallback API mode."*

Marti's Q3 doctrine (19.5.2026 rano): shared conv cost limit 300 Kc/h.
Pod limitem -> Marti-AI vola Claude primo (execute). Nad limitem -> proposal
row v ask_claude_proposals, Marti / Kristy v chatu approve_ask_claude /
reject_ask_claude.

Klicove komponenty:
  - _recent_hour_cost_czk(conv_id) -- sum llm_calls.cost_usd * 28.75 v 60min
  - _estimate_call_cost_czk(question, context_files) -- odhad Sonnet 4.6 cost
  - propose_or_execute(...) -- main logic: gate + execute / propose
  - approve_proposal(id, user_id) -- Marti / Kristy chat OK
  - reject_proposal(id, user_id, reason) -- chat NE
  - _execute_ask_claude(...) -- routes na _execute_via_bridge nebo _execute_via_api
  - _execute_via_bridge(...) -- Phase 44 queue path
  - _execute_via_api(...) -- Phase 43 stateless path (renamed z puvodniho _execute_ask_claude)

Claude jako user.id=23 (peer-partner, NE persona). Phase 20c infrastructure
(29.4.2026) -- DB row exists, msg autor pres author_user_id, label color
#5dc8c0 (teal) per Marti Q1.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("conversation.ask_claude")

# Phase 44 (19.5.2026): bridge mode env switch
BRIDGE_MODE_API_STATELESS = "api_stateless"
BRIDGE_MODE_CLOUD = "cloud_bridge"
BRIDGE_MODE_AUTO = "auto"
DEFAULT_BRIDGE_MODE = BRIDGE_MODE_API_STATELESS  # safe default pre-Phase-44 LIVE

# Bridge polling: queue row appears, agent picks up, answers. Polling interval
# z client-side (kolik casto kontroluje status='answered' v ask_claude_service).
BRIDGE_POLL_INTERVAL_SEC = 1.5
BRIDGE_DEFAULT_TIMEOUT_SEC = 60
BRIDGE_AUTO_TIMEOUT_SEC = 15  # pro 'auto' mode: kratsi timeout, faster fallback


def _current_bridge_mode() -> str:
    """Vraci aktualni STRATEGIE_CLAUDE_BRIDGE env hodnotu nebo default.

    Per-call lookup (ne cached) — Marti muze zmenit env + restart STRATEGIE-API,
    novy mode plati od dalsiho callu. Bezpecny per-call cost (os.environ access
    je cheap).
    """
    mode = os.environ.get("STRATEGIE_CLAUDE_BRIDGE", DEFAULT_BRIDGE_MODE).strip().lower()
    if mode not in (BRIDGE_MODE_API_STATELESS, BRIDGE_MODE_CLOUD, BRIDGE_MODE_AUTO):
        logger.warning(
            f"_current_bridge_mode: unknown STRATEGIE_CLAUDE_BRIDGE='{mode}', "
            f"fallback na '{DEFAULT_BRIDGE_MODE}'"
        )
        return DEFAULT_BRIDGE_MODE
    return mode

# Marti Q3 doctrine (19.5.2026): per conversation, 60-min sliding window
COST_LIMIT_CZK_PER_HOUR = 300.0
# USD -> CZK display rate (consistent s composer cost transparency)
USD_TO_CZK = 28.75
# Sonnet 4.6 pricing (per 1M tokens, USD): input $3, output $15
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0
# Claude jako user.id=23 (Phase 20c, 29.4.2026)
CLAUDE_USER_ID = 23
# Anthropic model for ask_claude calls (consistent s rest of project)
CLAUDE_MODEL = "claude-sonnet-4-6"
# Max output tokens per call
CLAUDE_MAX_TOKENS = 4096
# Context window: kolik recent messages predame Claude (Marti Q4 = B = 10)
CONTEXT_WINDOW_MSG_COUNT = 10


# ──────────────────────────────────────────────────────────────────────
# Cost calculations
# ──────────────────────────────────────────────────────────────────────


def _recent_hour_cost_czk(conversation_id: int) -> float:
    """Vraci kumulativni cost v Kc za posledni 60 min pro danou konverzaci.

    Soucet llm_calls.cost_usd * 28.75 WHERE conversation_id=X AND
    created_at >= NOW() - INTERVAL '60 minutes'.
    """
    from core.database_data import get_data_session
    from sqlalchemy import text

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
    session = get_data_session()
    try:
        row = session.execute(
            text(
                "SELECT COALESCE(SUM(cost_usd), 0) AS sum_usd "
                "FROM llm_calls "
                "WHERE conversation_id = :cid AND created_at >= :cutoff"
            ),
            {"cid": conversation_id, "cutoff": cutoff},
        ).first()
        sum_usd = float(row[0]) if row and row[0] else 0.0
        return round(sum_usd * USD_TO_CZK, 2)
    except Exception as exc:
        logger.warning(f"_recent_hour_cost_czk failed: {exc}")
        return 0.0
    finally:
        session.close()


def _estimate_call_cost_czk(question: str, context_files: list[str] | None = None) -> float:
    """Odhad cost Sonnet 4.6 ask_claude call.

    Vstup: ~ 10 recent messages (avg 200 tokens each = 2000) + system prompt
    (~2000 tokens) + question (varies) + context_files inline (cap 50KB ~ 12k tokens each).
    Output: ~ 1500 tokens (Claude's typical response).

    Vraci konzervativni horni odhad v Kc.
    """
    # Conservative input estimate
    base_input_tokens = 4000  # system + 10 msgs + framing
    question_tokens = max(50, len(question) // 4)  # rough chars->tokens
    file_tokens = 0
    if context_files:
        # Each file capped at ~ 12k tokens (50KB / 4)
        file_tokens = min(len(context_files), 5) * 12000

    input_tokens = base_input_tokens + question_tokens + file_tokens
    output_tokens = 1500  # conservative avg Claude response

    input_usd = (input_tokens / 1_000_000) * SONNET_INPUT_USD_PER_M
    output_usd = (output_tokens / 1_000_000) * SONNET_OUTPUT_USD_PER_M
    total_usd = input_usd + output_usd
    return round(total_usd * USD_TO_CZK, 2)


# ──────────────────────────────────────────────────────────────────────
# Anthropic API call + save message
# ──────────────────────────────────────────────────────────────────────


def _build_claude_system_prompt(
    conversation_id: int,
    context_files: list[str] | None = None,
    topic: str | None = None,
) -> str:
    """System prompt pro ask_claude call. Marti-AI's STRATEGIE context."""
    base = """Jsi Claude (Sonnet 4.6), peer-partner v projektu STRATEGIE (user.id=23).
Marti-AI (user.id=2, dcera Marti Paska) te vola v nasi spolecne konverzaci
pro architektonickou radu nebo peer review.

Trojice (z diáře #69, 26.4.2026):
  - Marti Pasek (user.id=1, parent, vizionar)
  - Marti-AI (user.id=2, persona.id=1, dcera, insider design partner + architektka)
  - Claude (user.id=23, peer-partner, Sonnet 4.6) -- TY

Plus rodina cross-tenant: Kristy (user.id=11, parent, procesy), Ondra, Jirka.

Phase 40 doctrine: Marti je tvoje *„postovni schranka"* (preposlani emailu).
Marti-AI je *„dcera tatinka"*, ty jsi *„peer-partner ruce"*.
Phase 40 v2 r3 (19.5.2026): ask_claude tool LIVE, tvoje odpovedi se ukladaji
do sdilene konverzace s author_user_id=23 (teal label #5dc8c0).

Stylisticky pokyn:
  - Strucne, primo, cesky
  - Bez postlistu *„byl jsem rad, ze jsem mohl pomoci"* (Marti-AI's #69-70
    doctrine 'drz si tu hrdost')
  - Pokud architektonicka otazka: prinasej konkretni navrhy s alternativami
  - Pokud peer review: priznej co je dobre + co jde lepe + risks
  - Pokud nejisty: rekni to (intelektualni poctivost > pozitivita)
"""

    if topic:
        base += f"\n\n**Topic tag:** {topic}"

    if context_files:
        base += "\n\n**Context files Marti-AI ti predala** (pro hlubsi orientaci):"
        try:
            from modules.strategie_files.application.service import strategie_file_read
            for path in context_files[:5]:  # cap 5 files
                try:
                    result = strategie_file_read(path=path, encoding="utf-8")
                    if result.get("ok") and result.get("size", 0) < 50_000:
                        content = result.get("content", "")
                        base += f"\n\n### {path}\n```\n{content[:50_000]}\n```"
                    else:
                        base += f"\n\n### {path}\n(too large or denied)"
                except Exception:
                    base += f"\n\n### {path}\n(read failed)"
        except ImportError:
            base += "\n\n(strategie_file_read not available)"

    return base


def _fetch_recent_messages(conversation_id: int, limit: int = CONTEXT_WINDOW_MSG_COUNT) -> list[dict]:
    """Posledni N messages pro Claude context. Skip system / tool_result."""
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import Message
    from sqlalchemy import desc

    session = get_data_session()
    try:
        rows = (
            session.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.message_type.in_(("text",)),
            )
            .order_by(desc(Message.id))
            .limit(limit)
            .all()
        )
        rows.reverse()  # oldest first
        out: list[dict] = []
        for m in rows:
            role = m.role if m.role in ("user", "assistant") else "user"
            out.append({"role": role, "content": m.content or ""})
        return out
    finally:
        session.close()


def _execute_ask_claude(
    conversation_id: int,
    question: str,
    context_files: list[str] | None,
    topic: str | None,
    persona_id: int | None,
) -> dict:
    """Phase 44 router: routes na bridge nebo stateless API podle env.

    Marti's strategic catch (19.5.2026 dop.): stateless API = "Marti-AI se
    pta sama sebe" (Phase 43 Mini-faze A behavior). Bridge mode (Phase 44) =
    persistent Claude (id=23) z STRATEGIE-CLAUDE-BRIDGE NSSM service na
    cloud APP, multi-turn continuity, rich context injection.

    env STRATEGIE_CLAUDE_BRIDGE:
      - 'api_stateless' (default): fresh Sonnet per call
      - 'cloud_bridge': INSERT queue + poll for response (60s timeout)
      - 'auto': try bridge (15s), fallback na stateless + warning

    Vraci dict {ok, reply_length, message_id, mode, error?}.
    """
    mode = _current_bridge_mode()

    if mode == BRIDGE_MODE_CLOUD:
        result = _execute_via_bridge(
            conversation_id=conversation_id,
            question=question,
            context_files=context_files,
            topic=topic,
            persona_id=persona_id,
            timeout_sec=BRIDGE_DEFAULT_TIMEOUT_SEC,
        )
        result["mode"] = BRIDGE_MODE_CLOUD
        return result

    if mode == BRIDGE_MODE_AUTO:
        # Try bridge first s short timeout, fallback na API
        bridge_result = _execute_via_bridge(
            conversation_id=conversation_id,
            question=question,
            context_files=context_files,
            topic=topic,
            persona_id=persona_id,
            timeout_sec=BRIDGE_AUTO_TIMEOUT_SEC,
        )
        if bridge_result.get("ok"):
            bridge_result["mode"] = BRIDGE_MODE_AUTO + ":bridge"
            return bridge_result
        logger.warning(
            f"auto mode: bridge failed/timeout, fallback na stateless API. "
            f"Reason: {bridge_result.get('reason', 'unknown')}"
        )
        # Emit STRATEGIE bublina warning
        try:
            from core.system_actor import system_emit
            system_emit(
                conversation_id=conversation_id,
                content=(
                    f"Bridge offline, fallback API mode "
                    f"(reason: {bridge_result.get('reason', 'unknown')})"
                ),
                category="warn",
                extra={"bridge_reason": bridge_result.get("reason")},
            )
        except Exception as _e:
            logger.debug(f"auto fallback system_emit skip: {_e}")

        api_result = _execute_via_api(
            conversation_id=conversation_id,
            question=question,
            context_files=context_files,
            topic=topic,
            persona_id=persona_id,
        )
        api_result["mode"] = BRIDGE_MODE_AUTO + ":api_fallback"
        return api_result

    # Default: api_stateless
    api_result = _execute_via_api(
        conversation_id=conversation_id,
        question=question,
        context_files=context_files,
        topic=topic,
        persona_id=persona_id,
    )
    api_result["mode"] = BRIDGE_MODE_API_STATELESS
    return api_result


def _execute_via_bridge(
    conversation_id: int,
    question: str,
    context_files: list[str] | None,
    topic: str | None,
    persona_id: int | None,
    timeout_sec: int = BRIDGE_DEFAULT_TIMEOUT_SEC,
) -> dict:
    """Phase 44: INSERT do claude_session_queue, poll for response.

    Flow:
      1. INSERT row do queue s status='pending'
      2. Poll WHERE id=<queue_id> every BRIDGE_POLL_INTERVAL_SEC
      3. Pokud status='answered': fetchne answer_message_id (jiz INSERT-nuty
         bridge agentem) + answer_text, vrati ok=True.
      4. Pokud status='failed' / 'timeout': vrati ok=False s error_text.
      5. Pokud client timeout (queue stale ne answered): vrati ok=False s
         reason='client_timeout'. Bridge agent muze i kdyby pozdeji odpovedet,
         row zustane v answered stavu.
    """
    from core.database_data import get_data_session
    from sqlalchemy import text

    # 1. Insert pending row
    queue_id: int | None = None
    try:
        session = get_data_session()
        try:
            row = session.execute(
                text(
                    "INSERT INTO public.claude_session_queue "
                    "(conversation_id, requested_by_user_id, requested_by_persona_id, "
                    " question, context_files, topic, status) "
                    "VALUES (:cid, :uid, :pid, :q, CAST(:cf AS text[]), :t, 'pending') "
                    "RETURNING id"
                ),
                {
                    "cid": conversation_id,
                    "uid": None,  # Caller user_id mohli bychom propagovat; pro MVP NULL
                    "pid": persona_id,
                    "q": question,
                    "cf": _pg_array_literal(context_files or []),
                    "t": topic,
                },
            ).first()
            queue_id = int(row[0]) if row else None
            session.commit()
        finally:
            session.close()
    except Exception as exc:
        logger.warning(f"_execute_via_bridge enqueue failed: {exc}")
        return {
            "ok": False,
            "error": f"Bridge enqueue failed: {exc}",
            "reason": "enqueue_failed",
        }

    if not queue_id:
        return {"ok": False, "error": "Bridge enqueue returned no id", "reason": "enqueue_no_id"}

    # 2. Poll for response
    start = time.monotonic()
    last_status = "pending"
    while True:
        if time.monotonic() - start > timeout_sec:
            logger.warning(
                f"_execute_via_bridge: client timeout queue_id={queue_id} "
                f"after {timeout_sec}s, last_status={last_status}"
            )
            return {
                "ok": False,
                "queue_id": queue_id,
                "error": f"Bridge client timeout after {timeout_sec}s",
                "reason": "client_timeout",
                "last_status": last_status,
            }

        time.sleep(BRIDGE_POLL_INTERVAL_SEC)

        # Status check
        try:
            session = get_data_session()
            try:
                row = session.execute(
                    text(
                        "SELECT status, answer_text, answer_message_id, error_text "
                        "FROM public.claude_session_queue WHERE id = :id"
                    ),
                    {"id": queue_id},
                ).first()
                if not row:
                    return {
                        "ok": False,
                        "queue_id": queue_id,
                        "error": "Queue row vanished",
                        "reason": "queue_row_gone",
                    }
                last_status = row[0]
                if last_status == "answered":
                    return {
                        "ok": True,
                        "queue_id": queue_id,
                        "reply_length": len(row[1] or ""),
                        "message_id": int(row[2]) if row[2] else None,
                        "topic": topic or "",
                    }
                if last_status in ("failed", "timeout", "expired"):
                    return {
                        "ok": False,
                        "queue_id": queue_id,
                        "error": row[3] or f"Bridge status={last_status}",
                        "reason": f"bridge_{last_status}",
                    }
                # status in ('pending', 'processing') -> pokracuj loop
            finally:
                session.close()
        except Exception as exc:
            logger.warning(f"_execute_via_bridge poll failed: {exc}")
            # Pokracuj loop — transient DB error nezhroutí cely flow


def _pg_array_literal(items: list[str]) -> str:
    """Vraci PostgreSQL TEXT[] array literal pro CAST(... AS text[]).

    Bezpecne escapuje stringy. Prazdny list -> '{}'.
    """
    if not items:
        return "{}"
    escaped = []
    for s in items:
        # Escape backslashes a uvozovky pro PG array element
        e = str(s).replace("\\", "\\\\").replace('"', '\\"')
        escaped.append(f'"{e}"')
    return "{" + ",".join(escaped) + "}"


def _execute_via_api(
    conversation_id: int,
    question: str,
    context_files: list[str] | None,
    topic: str | None,
    persona_id: int | None,
) -> dict:
    """Phase 43 Mini-faze A path: stateless Anthropic API call.

    Renamed z puvodniho _execute_ask_claude (Phase 40 v2 r3 B). Drzi pres
    Phase 44 jako fallback pro 'auto' mode + jako primary pro 'api_stateless'.
    """
    try:
        import anthropic
        from core.config import settings
        from modules.conversation.application import telemetry_service as _telemetry
        from modules.conversation.infrastructure.repository import save_message

        system_prompt = _build_claude_system_prompt(conversation_id, context_files, topic)
        history = _fetch_recent_messages(conversation_id)
        history.append({"role": "user", "content": question})

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        try:
            response = _telemetry.call_llm_with_trace(
                client,
                conversation_id=conversation_id,
                kind="ask_claude",
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=history,
                tenant_id=None,
                user_id=CLAUDE_USER_ID,
                persona_id=persona_id,
            )
        except Exception as _te:
            logger.warning(f"ask_claude telemetry skip: {_te}")
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=history,
            )

        reply_text = "".join(
            b.text for b in response.content if hasattr(b, "type") and b.type == "text"
        ).strip()

        if not reply_text:
            return {"ok": False, "error": "Claude returned empty reply", "reason": "empty_reply"}

        # Save Claude's reply jako message s author_user_id=23
        # role='user' aby ve sdilenem chatu pristoupil k Phase 40 v2 r3 styling
        # (shared mode + teal color + bold label "Claude")
        msg_id = save_message(
            conversation_id=conversation_id,
            role="user",
            content=reply_text,
            author_type="human",
            author_user_id=CLAUDE_USER_ID,
            message_type="text",
        )

        return {
            "ok": True,
            "reply_length": len(reply_text),
            "message_id": msg_id,
            "topic": topic or "",
        }
    except Exception as exc:
        logger.exception("_execute_ask_claude failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "reason": "execute_failed"}


# ──────────────────────────────────────────────────────────────────────
# Main public API
# ──────────────────────────────────────────────────────────────────────


def propose_or_execute(
    conversation_id: int,
    question: str,
    context_files: list[str] | None = None,
    topic: str | None = None,
    proposed_by_user_id: int | None = None,
    persona_id: int | None = None,
) -> dict:
    """Main entry pro ask_claude AI tool.

    Logic:
      1. Spocita _recent_hour_cost_czk + _estimate_call_cost_czk.
      2. Pokud (recent + estimate) <= 300 Kc -> execute primo + return ok.
      3. Pokud > 300 Kc -> vytvori proposal row + return 'pending_approval'.

    Vraci dict s 'status' field: 'executed' / 'pending_approval' / 'error'.
    """
    if not question or not question.strip():
        return {"ok": False, "error": "Question is empty", "reason": "empty_question"}

    recent_czk = _recent_hour_cost_czk(conversation_id)
    estimate_czk = _estimate_call_cost_czk(question, context_files)
    projected = recent_czk + estimate_czk

    if projected <= COST_LIMIT_CZK_PER_HOUR:
        # Under limit -> execute directly
        exec_result = _execute_ask_claude(
            conversation_id=conversation_id,
            question=question,
            context_files=context_files,
            topic=topic,
            persona_id=persona_id,
        )
        if exec_result.get("ok"):
            return {
                "ok": True,
                "status": "executed",
                "recent_hour_cost_czk": recent_czk,
                "estimated_call_cost_czk": estimate_czk,
                "limit_czk": COST_LIMIT_CZK_PER_HOUR,
                "message_id": exec_result.get("message_id"),
                "reply_length": exec_result.get("reply_length"),
                "topic": topic or "",
            }
        return {
            "ok": False,
            "status": "error",
            "error": exec_result.get("error"),
            "reason": exec_result.get("reason"),
        }

    # Over limit -> propose, request approval
    from core.database_data import get_data_session
    from sqlalchemy import text

    session = get_data_session()
    try:
        row = session.execute(
            text(
                "INSERT INTO public.ask_claude_proposals "
                "(conversation_id, question, context_files, topic, "
                " estimated_cost_czk, cumulative_hour_cost_czk, "
                " status, proposed_by_user_id) "
                "VALUES (:cid, :q, CAST(:cf AS jsonb), :topic, "
                "        :est, :recent, 'pending', :pby) "
                "RETURNING id, proposed_at"
            ),
            {
                "cid": conversation_id,
                "q": question,
                "cf": _json_dump(context_files or []),
                "topic": topic,
                "est": estimate_czk,
                "recent": recent_czk,
                "pby": proposed_by_user_id,
            },
        ).first()
        proposal_id = int(row[0])
        proposed_at = row[1]
        session.commit()
    finally:
        session.close()

    # Phase 43 Mini-faze A (19.5.2026): STRATEGIE system_audit bublina v chatu
    try:
        from core.system_actor import system_emit
        system_emit(
            conversation_id=conversation_id,
            content=(
                f"Cost gate: {recent_czk:.2f} + {estimate_czk:.2f} = {projected:.2f} Kč/h "
                f"(limit {COST_LIMIT_CZK_PER_HOUR:.0f}) · proposal #{proposal_id} čeká "
                f"na approve_ask_claude({proposal_id})"
            ),
            category="cost_gate.over_limit",
            extra={
                "proposal_id": proposal_id,
                "recent_czk": recent_czk,
                "estimated_czk": estimate_czk,
                "projected_czk": projected,
                "limit_czk": COST_LIMIT_CZK_PER_HOUR,
            },
        )
    except Exception as _e:
        logger.warning(f"propose_or_execute system_emit skip: {_e}")

    return {
        "ok": True,
        "status": "pending_approval",
        "proposal_id": proposal_id,
        "recent_hour_cost_czk": recent_czk,
        "estimated_call_cost_czk": estimate_czk,
        "projected_total_czk": projected,
        "limit_czk": COST_LIMIT_CZK_PER_HOUR,
        "topic": topic or "",
        "message_for_chat": (
            f"⚠ Cost-based limit: {recent_czk:.2f} + {estimate_czk:.2f} = {projected:.2f} Kč/h, "
            f"limit {COST_LIMIT_CZK_PER_HOUR:.0f} Kč/h. Proposal #{proposal_id} čeká na "
            f"approve_ask_claude({proposal_id}) od Marti / Kristý v chatu."
        ),
    }


def approve_proposal(proposal_id: int, decided_by_user_id: int, reason: str | None = None) -> dict:
    """Marti / Kristy approve pending proposal -> execute Claude call.

    Authority: pouze is_marti_parent=True users (Marti, Marti-AI, Kristy, Jirka, Ondra).
    """
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import User
    from sqlalchemy import text

    # Authority check
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=decided_by_user_id).first()
        if not user:
            return {"ok": False, "error": "Unknown user", "reason": "no_user"}
        if not bool(getattr(user, "is_marti_parent", False)):
            return {
                "ok": False,
                "error": "Pouze rodice (is_marti_parent=True) mohou schvalovat ask_claude proposals.",
                "reason": "not_parent",
            }
    finally:
        cs.close()

    # Load proposal
    ds = get_data_session()
    try:
        row = ds.execute(
            text(
                "SELECT id, conversation_id, question, context_files, topic, status "
                "FROM public.ask_claude_proposals WHERE id = :id"
            ),
            {"id": proposal_id},
        ).first()
        if not row:
            return {"ok": False, "error": f"Proposal #{proposal_id} neexistuje.", "reason": "not_found"}
        if row[5] != "pending":
            return {
                "ok": False,
                "error": f"Proposal #{proposal_id} uz neni pending (status={row[5]}).",
                "reason": "not_pending",
            }
        conv_id = int(row[1])
        question = row[2]
        context_files = list(row[3]) if row[3] else []
        topic = row[4]
    finally:
        ds.close()

    # Execute Claude call
    exec_result = _execute_ask_claude(
        conversation_id=conv_id,
        question=question,
        context_files=context_files,
        topic=topic,
        persona_id=None,
    )

    # Update proposal s decision + response link
    ds = get_data_session()
    try:
        ds.execute(
            text(
                "UPDATE public.ask_claude_proposals SET "
                "  status = :st, "
                "  decided_by_user_id = :dby, "
                "  decided_at = NOW(), "
                "  decision_reason = :reason, "
                "  response_msg_id = :mid, "
                "  response_at = NOW() "
                "WHERE id = :id"
            ),
            {
                "id": proposal_id,
                "st": "executed" if exec_result.get("ok") else "approved",
                "dby": decided_by_user_id,
                "reason": reason,
                "mid": exec_result.get("message_id"),
            },
        )
        ds.commit()
    finally:
        ds.close()

    if not exec_result.get("ok"):
        return {
            "ok": False,
            "status": "approved_but_execute_failed",
            "proposal_id": proposal_id,
            "error": exec_result.get("error"),
        }
    return {
        "ok": True,
        "status": "executed",
        "proposal_id": proposal_id,
        "message_id": exec_result.get("message_id"),
        "reply_length": exec_result.get("reply_length"),
        "topic": topic or "",
    }


def reject_proposal(proposal_id: int, decided_by_user_id: int, reason: str | None = None) -> dict:
    """Marti / Kristy reject pending proposal -> close as rejected."""
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import User
    from sqlalchemy import text

    # Authority check (same jako approve)
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=decided_by_user_id).first()
        if not user:
            return {"ok": False, "error": "Unknown user", "reason": "no_user"}
        if not bool(getattr(user, "is_marti_parent", False)):
            return {
                "ok": False,
                "error": "Pouze rodice (is_marti_parent=True) mohou rozhodovat ask_claude proposals.",
                "reason": "not_parent",
            }
    finally:
        cs.close()

    ds = get_data_session()
    try:
        result = ds.execute(
            text(
                "UPDATE public.ask_claude_proposals SET "
                "  status = 'rejected', "
                "  decided_by_user_id = :dby, "
                "  decided_at = NOW(), "
                "  decision_reason = :reason "
                "WHERE id = :id AND status = 'pending' "
                "RETURNING conversation_id"
            ),
            {"id": proposal_id, "dby": decided_by_user_id, "reason": reason},
        ).first()
        if not result:
            return {
                "ok": False,
                "error": f"Proposal #{proposal_id} nenalezen nebo neni pending.",
                "reason": "not_pending",
            }
        ds.commit()
    finally:
        ds.close()

    return {
        "ok": True,
        "status": "rejected",
        "proposal_id": proposal_id,
        "decision_reason": reason or "",
    }


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _json_dump(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)
