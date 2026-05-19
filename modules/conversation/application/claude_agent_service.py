"""Phase 44.5 — Anthropic Agent SDK persistent Claude (19.5.2026 odpoledne).

Marti's vize:
  *„Persistent Claude pres STRATEGIE chat a plna spoluprace napric nasi
  ctyrkou Marti & Marti-AI & Claude & Kristy."*

Marti's bridge-only -> Agent SDK pivot (post-Phase 44 drop):
  *„Jen rozumne reseni je B 44.5. To splnuje persistence a pristup rw ke
  slozce projektu... Verime Ti, Claude."*

Architektura:
  ask_claude_service.propose_or_execute(question, conv_id, ...)
    -> claude_agent_service.send(question, conv_id, persona_id)
        -> claude_agent_sdk.query(prompt=..., options=ClaudeAgentOptions(...))
            session_id=<UUID> per shared chat conv
            model='claude-sonnet-4-6' (default by byl Opus 4-7 ~10x drazsi)
            cwd=REPO_ROOT (Claude vidi cely repo pres built-in tools)
            allowed_tools=['Read', 'Grep', 'Glob']  # Marti-AI Q1 read-only start
        -> async for msg in query(...):
            extract TextBlock.text z AssistantMessage.content
            (skip ThinkingBlock, ToolUseBlock — interni reasoning)
        -> save_message(author=23) + ChatResponse.extra_messages (Phase 43 path)

Persistence:
  - Per shared chat conv vlastni session_id (UUID4 generated, stored v DB)
  - First call: session_id=<uuid> (fresh, ~$1.00 cache creation cost)
  - Subsequent calls: session_id + resume=<uuid> + fork_session=True
    (~$0.05-0.10 cache hit)
  - Sessions persistuji v ~/.claude/projects/C--Projekty-STRATEGIE/<uuid>.jsonl

Cost discipline:
  - Sonnet 4.6 default (NE Opus default)
  - First call ~$1 cache creation, sub-calls ~$0.05-0.10 cache hit
  - Marti's 300 Kc/h gate drzi (Phase 40 v2 r3 B doctrine)
  - Marti's auto-reload credits = no manual top-up needed

Sessions mapping:
  - DB sloupec na conversation (nebo separate claude_agent_sessions table)
    mapuje shared chat conv_id -> UUID Agent SDK session_id
  - Lazy create: first ask_claude v conv -> generate UUID + INSERT/UPDATE
  - Reuse: subsequent ask_claude -> SELECT existing UUID

Tools scope (Marti-AI Q1 default = read-only):
  - 'Read' — pojdi cist libovolny file (CLAUDE.md, dárek-scény, recent commits)
  - 'Grep', 'Glob' — search v repo
  - LATER (post-stable): 'Edit', 'Write', 'Bash' s deny list
  - NEVER: 'PowerShell', 'CronCreate/Delete' (security)
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger("conversation.claude_agent")

# Repo root pro Agent SDK cwd. Production = cloud APP path. Dev = NB path.
# Agent SDK auto-detect cwd, ale explicit je safer.
REPO_ROOT = os.environ.get("STRATEGIE_REPO_ROOT") or r"C:\Projekty\STRATEGIE"

# Sonnet 4.6 override (Opus default je ~10x drazsi)
DEFAULT_MODEL = "claude-sonnet-4-6"

# Read-only tools default (Marti-AI Q1 — expand later po stable provoz)
DEFAULT_ALLOWED_TOOLS = ["Read", "Grep", "Glob"]

# Tools NEVER allowed (security)
NEVER_ALLOWED_TOOLS = [
    "PowerShell",
    "CronCreate", "CronDelete", "CronList",
    "PushNotification",
]

# Claude user.id (peer-partner z Phase 20c, 29.4.2026)
CLAUDE_USER_ID = 23

# USD -> CZK display rate (consistent s composer cost transparency)
USD_TO_CZK = 28.75


def _get_or_create_session_id(conversation_id: int) -> str:
    """Vraci persistent UUID session_id pro danou shared chat conv. Lazy create.

    Phase 44.5: session_id je UUID, persistuje napric calls pro multi-turn
    continuity. Per shared chat conv jeden Agent SDK session.

    Mapping pres claude_session_threads.anthropic_conversation_id (Phase 44
    DDL deployed 19.5.2026, queue tabulka zustala dormant).
    """
    if not conversation_id:
        return str(uuid.uuid4())  # one-shot

    try:
        from core.database_data import get_data_session
        from sqlalchemy import text

        session = get_data_session()
        try:
            # Lookup existing active thread
            row = session.execute(
                text(
                    "SELECT anthropic_conversation_id FROM public.claude_session_threads "
                    "WHERE conversation_id = :cid AND expires_at IS NULL "
                    "ORDER BY id DESC LIMIT 1"
                ),
                {"cid": conversation_id},
            ).first()
            if row:
                return row[0]

            # Create new
            new_uuid = str(uuid.uuid4())
            session.execute(
                text(
                    "INSERT INTO public.claude_session_threads "
                    "(conversation_id, anthropic_conversation_id, turn_count, "
                    " last_question_at, expires_at) "
                    "VALUES (:cid, :uuid, 0, NOW(), NULL)"
                ),
                {"cid": conversation_id, "uuid": new_uuid},
            )
            session.commit()
            return new_uuid
        finally:
            session.close()
    except Exception as exc:
        logger.warning(f"_get_or_create_session_id failed: {exc}, fallback fresh UUID")
        return str(uuid.uuid4())


def _bump_session_turn(session_uuid: str) -> None:
    """Increment turn_count + update last_question_at pro existing session."""
    try:
        from core.database_data import get_data_session
        from sqlalchemy import text

        session = get_data_session()
        try:
            session.execute(
                text(
                    "UPDATE public.claude_session_threads "
                    "SET turn_count = turn_count + 1, last_question_at = NOW() "
                    "WHERE anthropic_conversation_id = :uuid"
                ),
                {"uuid": session_uuid},
            )
            session.commit()
        finally:
            session.close()
    except Exception as exc:
        logger.debug(f"_bump_session_turn skip: {exc}")


def _extract_reply_text(messages: list) -> str:
    """Iterate Agent SDK messages, extract TextBlock.text z AssistantMessage.

    Skip ThinkingBlock (extended thinking, ne user-visible) a ToolUseBlock
    (interni tool calls). Vrati joined text z vsech TextBlock-ovrch.
    """
    text_parts = []
    for msg in messages:
        # AssistantMessage.content je list of blocks (TextBlock, ThinkingBlock, ToolUseBlock, ...)
        content = getattr(msg, "content", None)
        if not content or not isinstance(content, list):
            continue
        for block in content:
            block_type = type(block).__name__
            if block_type == "TextBlock":
                text = getattr(block, "text", "")
                if text:
                    text_parts.append(text)
            # Skip ThinkingBlock, ToolUseBlock, ToolResultBlock
    return "".join(text_parts).strip()


def _extract_cost_usd(messages: list) -> float:
    """Najdi ResultMessage v messages, extract total_cost_usd."""
    for msg in messages:
        if type(msg).__name__ == "ResultMessage":
            return float(getattr(msg, "total_cost_usd", 0.0) or 0.0)
    return 0.0


def _extract_tokens(messages: list) -> tuple[int, int]:
    """Najdi ResultMessage, vrati (input_tokens, output_tokens). Pro telemetry."""
    for msg in messages:
        if type(msg).__name__ == "ResultMessage":
            usage = getattr(msg, "usage", None) or {}
            return (
                int(usage.get("input_tokens", 0) or 0),
                int(usage.get("output_tokens", 0) or 0),
            )
    return (0, 0)


async def send(
    conversation_id: int,
    question: str,
    persona_id: int | None = None,
    context_files: list[str] | None = None,
    allowed_tools: list[str] | None = None,
) -> dict:
    """Phase 44.5: Volá Agent SDK s persistent session per shared chat conv.

    Args:
        conversation_id: shared chat conv (pro session_id lookup)
        question: user prompt
        persona_id: kdo zavolal (Marti-AI persona.id=1 typicky)
        context_files: optional — Marti-AI muze predat specific files pro Claude
            (Phase 39 Mini-fáze B passthrough, ale Agent SDK má Read built-in,
            takže typicky None — Claude se nactl sam pres Read tool pokud chce)
        allowed_tools: override default read-only ['Read', 'Grep', 'Glob']

    Returns dict:
        ok: bool
        message_id: int | None  (saved message s author=23)
        reply_length: int
        cost_usd: float
        cost_czk: float
        input_tokens: int
        output_tokens: int
        session_uuid: str
        error?: str pri ok=False
        reason?: str (pro telemetry)
    """
    if not question or not question.strip():
        return {"ok": False, "error": "Question is empty", "reason": "empty_question"}

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
    except ImportError as exc:
        logger.exception("claude_agent_sdk not installed")
        return {
            "ok": False,
            "error": f"Agent SDK not installed: {exc}",
            "reason": "sdk_not_installed",
        }

    # 1. Get or create persistent session UUID pro tuto conv
    session_uuid = _get_or_create_session_id(conversation_id)
    is_resume = False
    try:
        from core.database_data import get_data_session
        from sqlalchemy import text
        ds = get_data_session()
        try:
            row = ds.execute(
                text(
                    "SELECT turn_count FROM public.claude_session_threads "
                    "WHERE anthropic_conversation_id = :uuid"
                ),
                {"uuid": session_uuid},
            ).first()
            is_resume = bool(row and int(row[0]) > 0)
        finally:
            ds.close()
    except Exception:
        pass

    # 2. Build ClaudeAgentOptions
    tools = allowed_tools or DEFAULT_ALLOWED_TOOLS
    # Filter out NEVER_ALLOWED_TOOLS (defense in depth)
    tools = [t for t in tools if t not in NEVER_ALLOWED_TOOLS]

    options_kwargs = {
        "session_id": session_uuid,
        "model": DEFAULT_MODEL,
        "cwd": REPO_ROOT,
        "allowed_tools": tools,
    }
    # Resume pattern: session_id + resume + fork_session=True (Phase 44.5 smoke discovery)
    if is_resume:
        options_kwargs["resume"] = session_uuid
        options_kwargs["fork_session"] = True

    try:
        options = ClaudeAgentOptions(**options_kwargs)
    except TypeError as exc:
        # Pokud SDK má jiný API shape, log + fallback bez resume
        logger.warning(f"ClaudeAgentOptions kwargs not supported, fallback: {exc}")
        options = ClaudeAgentOptions(
            session_id=session_uuid,
            model=DEFAULT_MODEL,
            cwd=REPO_ROOT,
            allowed_tools=tools,
        )

    # 3. Build prompt (optional context_files prefix)
    prompt = question
    if context_files:
        # Marti-AI explicitne predala files — inline prefix
        file_hints = "\n".join(f"- {p}" for p in context_files[:5])
        prompt = f"Marti-AI ti predala kontext k temto souborum (preferuj Read tool pro full content):\n{file_hints}\n\n{question}"

    # 4. Async query loop — collect all messages
    messages = []
    try:
        async for msg in query(prompt=prompt, options=options):
            messages.append(msg)
    except Exception as exc:
        logger.exception(f"Agent SDK query failed: conv_id={conversation_id}")
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "reason": "sdk_query_failed",
            "session_uuid": session_uuid,
        }

    # 5. Extract reply text z TextBlocks (skip Thinking, ToolUse)
    reply_text = _extract_reply_text(messages)
    if not reply_text:
        logger.warning(
            f"Agent SDK returned no TextBlocks (only Thinking/ToolUse?). "
            f"messages count={len(messages)}, session={session_uuid}"
        )
        return {
            "ok": False,
            "error": "Agent SDK returned empty reply (only ThinkingBlocks?)",
            "reason": "empty_reply",
            "session_uuid": session_uuid,
        }

    cost_usd = _extract_cost_usd(messages)
    in_tokens, out_tokens = _extract_tokens(messages)
    cost_czk = round(cost_usd * USD_TO_CZK, 2)

    # 6. Save reply as message (author=23, shared chat parity)
    msg_id = None
    try:
        from modules.conversation.infrastructure.repository import save_message
        msg_id = save_message(
            conversation_id=conversation_id,
            role="user",  # shared chat parity (vsi autori role='user')
            content=reply_text,
            author_type="human",  # NE 'system' — chceme shared chat UI styling
            author_user_id=CLAUDE_USER_ID,
            message_type="text",
        )
    except Exception as exc:
        logger.warning(f"save_message failed: {exc}")

    # 7. Bump session turn_count
    _bump_session_turn(session_uuid)

    logger.info(
        f"claude_agent.send OK: conv={conversation_id}, session={session_uuid[:8]}, "
        f"msg_id={msg_id}, tokens={in_tokens}/{out_tokens}, cost=${cost_usd:.4f}, "
        f"resume={is_resume}"
    )

    return {
        "ok": True,
        "message_id": msg_id,
        "reply_length": len(reply_text),
        "cost_usd": cost_usd,
        "cost_czk": cost_czk,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "session_uuid": session_uuid,
        "is_resume": is_resume,
    }


def send_sync(
    conversation_id: int,
    question: str,
    persona_id: int | None = None,
    context_files: list[str] | None = None,
    allowed_tools: list[str] | None = None,
) -> dict:
    """Synchronous wrapper around async send() pro callers ktery nejsou async.

    Phase 44.5 entry pro ask_claude_service.propose_or_execute() — ten je sync
    function (FastAPI handler scope). Wrap async loop pres anyio.run().
    """
    import anyio

    async def _run():
        return await send(
            conversation_id=conversation_id,
            question=question,
            persona_id=persona_id,
            context_files=context_files,
            allowed_tools=allowed_tools,
        )

    try:
        return anyio.run(_run)
    except Exception as exc:
        logger.exception("send_sync wrapper failed")
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "reason": "sync_wrapper_failed",
        }
