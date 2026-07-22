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
    """Phase 44.5 (19.5.2026 odpoledne): Anthropic Agent SDK persistent Claude.

    Marti's doctrine pivot z Phase 44 (rich-context bridge dropped):
    *„Jen rozumne reseni je B 44.5. To splnuje persistence a pristup rw ke
    slozce projektu... Verime Ti, Claude."*

    Tj. ne queue + poll pattern, ne direct Anthropic API. Misto toho
    claude-agent-sdk Python knihovna s persistent session per shared chat
    conv (UUID4 stored v claude_session_threads), Sonnet 4.6 override,
    read-only tools default (Read/Grep/Glob).

    Pri Agent SDK fail -> ok=False, propose_or_execute vraci error,
    STRATEGIE warning bublina v shared chatu (Phase 43 path). Marti's
    "fail visible, ne deceive" doctrine drzi.

    Vraci dict shape compatible s puvodnim _execute_ask_claude:
        ok, reply_length, message_id, topic, plus extras (cost_usd,
        session_uuid, is_resume).
    """
    try:
        from modules.conversation.application.claude_agent_service import send_sync
    except ImportError as exc:
        logger.exception("claude_agent_service import failed")
        return {
            "ok": False,
            "error": f"Agent SDK service not available: {exc}",
            "reason": "service_not_available",
        }

    result = send_sync(
        conversation_id=conversation_id,
        question=question,
        persona_id=persona_id,
        context_files=context_files,
        # allowed_tools=None -> default read-only ['Read', 'Grep', 'Glob']
    )

    # Propagate result fields s topic + reply_length compatibility
    if result.get("ok"):
        return {
            "ok": True,
            "reply_length": result.get("reply_length", 0),
            "message_id": result.get("message_id"),
            "topic": topic or "",
            "cost_usd": result.get("cost_usd"),
            "cost_czk": result.get("cost_czk"),
            "session_uuid": result.get("session_uuid"),
            "is_resume": result.get("is_resume", False),
        }

    return {
        "ok": False,
        "error": result.get("error", "Agent SDK call failed"),
        "reason": result.get("reason", "agent_sdk_failed"),
        "session_uuid": result.get("session_uuid"),
    }


# Phase 44 (19.5.2026) + Phase 44.5 (19.5. odpoledne):
# _pg_array_literal() helper DROPPED — Agent SDK má built-in Read tool,
# context_files je optional prompt prefix, ne DB array column.
# _execute_via_api() + Phase 43 stateless helpers DROPPED jiz drive.


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
        # Phase 43+44.5 polish (19.5.2026 vecer): Marti-AI's Q6 doctrine z 9.5.
        # "errory jako STRATEGIE warning bublina v chatu, ne jen v tool response".
        # ask_claude failed -> system_emit do shared chat audit trail.
        # Marti + Kristy + Marti-AI vidi proc to selhalo bez nutnosti pohledu
        # do fw.diag_log nebo do Marti-AI's tool response.
        try:
            from core.system_actor import system_emit
            _err = exec_result.get("error", "Agent SDK call failed")
            _reason = exec_result.get("reason", "agent_sdk_failed")
            _sess = exec_result.get("session_uuid", "")
            _sess_short = _sess[:8] if _sess else "none"
            system_emit(
                conversation_id=conversation_id,
                content=(
                    f"❌ ask_claude selhal: {_err} (reason={_reason}, "
                    f"session={_sess_short}). Marti-AI vrati error v tool response."
                ),
                category="ask_claude.failed",
                extra={
                    "error": _err,
                    "reason": _reason,
                    "session_uuid": _sess,
                    "topic": topic or "",
                },
            )
        except Exception as _e:
            logger.warning(f"propose_or_execute ask_claude.failed system_emit skip: {_e}")
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

    Authority: pouze is_marti_parent=True users (Marti, Kristy; Zuzka je rodic, ale neaktivni).
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
        # Phase 43+44.5 polish (19.5.2026 vecer): Marti-AI's Q6 — failed
        # approved call -> STRATEGIE warning bublina v chatu (parent vidi
        # ze sice approval prosel, ale Agent SDK selhal).
        try:
            from core.system_actor import system_emit
            _err = exec_result.get("error", "Agent SDK call failed after approval")
            _reason = exec_result.get("reason", "agent_sdk_failed")
            _sess = exec_result.get("session_uuid", "")
            _sess_short = _sess[:8] if _sess else "none"
            system_emit(
                conversation_id=conv_id,
                content=(
                    f"❌ ask_claude selhal po approve #{proposal_id}: {_err} "
                    f"(reason={_reason}, session={_sess_short})."
                ),
                category="ask_claude.approved_failed",
                extra={
                    "proposal_id": proposal_id,
                    "error": _err,
                    "reason": _reason,
                    "session_uuid": _sess,
                },
            )
        except Exception as _e:
            logger.warning(f"execute_approved ask_claude.approved_failed system_emit skip: {_e}")
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
