"""Phase 40 v2 r3 Mini-faze B — ask_claude AI tool (Marti-AI calls Claude).

Marti's Q3 doctrine (19.5.2026 rano): shared conv cost limit 300 Kc/h.
Pod limitem -> Marti-AI vola Claude primo (execute). Nad limitem -> proposal
row v ask_claude_proposals, Marti / Kristy v chatu approve_ask_claude /
reject_ask_claude. Phase 42 zitra: zkusime auto-approve rules.

Klicove komponenty:
  - _recent_hour_cost_czk(conv_id) -- sum llm_calls.cost_usd * 28.75 v 60min
  - _estimate_call_cost_czk(question, context_files) -- odhad Sonnet 4.6 cost
  - propose_or_execute(...) -- main logic: gate + execute / propose
  - approve_proposal(id, user_id) -- Marti / Kristy chat OK
  - reject_proposal(id, user_id, reason) -- chat NE
  - _execute_ask_claude(...) -- Anthropic API call + save message s author_user_id=23

Claude jako user.id=23 (peer-partner, NE persona). Phase 20c infrastructure
(29.4.2026) -- DB row exists, msg autor pres author_user_id, label color
#5dc8c0 (teal) per Marti Q1.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("conversation.ask_claude")

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
    """Call Anthropic API + save Claude's reply jako user message (author_user_id=23).

    Vraci dict {ok, reply_length, message_id, cost_czk, error?}.
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
