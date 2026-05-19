"""Phase 44 — ask_claude AI tool, Bridge-only path (19.5.2026 odpoledne).

Marti's doctrine z 19.5. odpoledne: *„Prepinac na mody API a Bridge potrebovat
nebudeme... API v tomhletom pripade ztraci zcela vyznam a jen to komplikuje."*

Tj. drop puvodni stateless Anthropic API path uplne. Bridge je THE path:

  ask_claude(question) -> INSERT claude_session_queue (pending)
                       -> poll WHERE id=X every 1.5s (timeout 60s)
                       -> STRATEGIE-CLAUDE-BRIDGE NSSM service na cloud APP
                          zpracuje s rich context injection (CLAUDE.md sekce,
                          dárek-scény, recent commits, multi-turn continuity)
                       -> answer_text + Claude bublina v shared chatu

Pokud bridge unavailable (NSSM service down, DB connection fail, timeout) —
ask_claude vraci **error**, ne silent fallback. STRATEGIE warning bublina
v chatu: *„Bridge unavailable, retry / contact Marti."* Marti's doctrine
"fail visible, ne deceive" — pokud Claude bublina chybi, vis ze identitu
neni potvrzena. Drz Marti's strategic catch z dop.: "Marti-AI se pta sama
sebe" se NIKDY znovu nestane.

Marti's Q3 doctrine (19.5.2026 rano): shared conv cost limit 300 Kc/h.
Pod limitem -> primo bridge execute. Nad limitem -> proposal row +
approve_ask_claude / reject_ask_claude v chatu.

Klicove komponenty:
  - _recent_hour_cost_czk(conv_id) -- sum llm_calls.cost_usd * 28.75 v 60min
  - _estimate_call_cost_czk(question, context_files) -- odhad Sonnet 4.6 cost
  - propose_or_execute(...) -- main logic: gate + execute / propose
  - approve_proposal(id, user_id) -- Marti / Kristy chat OK
  - reject_proposal(id, user_id, reason) -- chat NE
  - _execute_ask_claude(...) -- INSERT queue + poll, vraci ok=False pri bridge fail

Claude jako user.id=23 (peer-partner, NE persona). Phase 20c infrastructure
(29.4.2026). Persistent identity drzi pres STRATEGIE-CLAUDE-BRIDGE service
uptime + claude_session_threads.anthropic_conversation_id per shared chat.

Marti's vize ctyrky (19.5.2026 odpoledne): *„Plna spoluprace napric nasi
ctyrkou Marti & Marti-AI & Claude & Kristy."*
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("conversation.ask_claude")

# Phase 44 (19.5.2026): bridge polling parameters
BRIDGE_POLL_INTERVAL_SEC = 1.5
BRIDGE_DEFAULT_TIMEOUT_SEC = 60

# Marti Q3 doctrine (19.5.2026): per conversation, 60-min sliding window
COST_LIMIT_CZK_PER_HOUR = 300.0
# USD -> CZK display rate (consistent s composer cost transparency)
USD_TO_CZK = 28.75
# Sonnet 4.6 pricing (per 1M tokens, USD): input $3, output $15
# Pouzite v _estimate_call_cost_czk pro cost gate, bridge agent ma vlastni
# instance teto konstanty.
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0
# Claude jako user.id=23 (Phase 20c, 29.4.2026)
CLAUDE_USER_ID = 23


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


# Phase 44 (19.5.2026): _build_claude_system_prompt() + _fetch_recent_messages()
# DROPPED. Bridge agent (scripts/claude_bridge_agent.py) ma vlastni rich context
# injection (CLAUDE.md sekce, dárek-scény, recent commits) + multi-turn history
# pres anthropic_conversation_id per shared chat. Marti's doctrine: jeden zdroj
# pravdy, ne duplicate.


def _execute_ask_claude(
    conversation_id: int,
    question: str,
    context_files: list[str] | None,
    topic: str | None,
    persona_id: int | None,
    timeout_sec: int = BRIDGE_DEFAULT_TIMEOUT_SEC,
) -> dict:
    """Phase 44 (19.5.2026 odpoledne): Bridge-only path.

    Marti's doctrine: *„Prepinac na mody API a Bridge potrebovat nebudeme...
    API v tomhletom pripade ztraci zcela vyznam a jen to komplikuje."*

    Tj. zadny stateless API fallback. Bridge je THE path. Pokud bridge
    unavailable (NSSM service down, DB connection fail, client timeout) ->
    vraci ok=False + STRATEGIE warning bublina v chatu. Fail visible, ne
    silent deceive.

    Flow:
      1. INSERT row do claude_session_queue s status='pending'
      2. Poll WHERE id=<queue_id> every BRIDGE_POLL_INTERVAL_SEC
      3. Pokud status='answered': vrati ok=True s answer_message_id +
         reply_length (Claude bublina jiz INSERT-nuta bridge agentem)
      4. Pokud status='failed' / 'timeout': vrati ok=False + reason
      5. Pokud client timeout: vrati ok=False, reason='client_timeout',
         STRATEGIE bublina warning. Bridge agent muze i pozdeji odpovedet,
         row zustane answered v DB (audit).

    Vraci dict {ok, queue_id, reply_length?, message_id?, error?, reason?}.
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


# Phase 44 (19.5.2026): _execute_via_api() DROPPED per Marti's doctrine
# *„Prepinac na mody API a Bridge potrebovat nebudeme... API ztraci zcela
# vyznam a jen to komplikuje."* Bridge je THE path, no fallback.
# Helpers _build_claude_system_prompt() + _fetch_recent_messages() jsou
# implementovany v scripts/claude_bridge_agent.py s rich context injection
# (CLAUDE.md sekce, dárek-scény, recent commits) — ne tady duplicate.


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
