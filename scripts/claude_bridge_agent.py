"""Phase 44 — STRATEGIE-CLAUDE-BRIDGE NSSM service.

Persistent Claude (id=23) bridge mezi STRATEGIE shared chatem a Anthropic
API. Marti's vize z 19.5.2026 odpoledne:

  *„Persistent Claude pres STRATEGIE chat a plna spoluprace napric nasi
  ctyrkou Marti & Marti-AI & Claude & Kristy."*

Architektura:
  1. Pollu claude_session_queue WHERE status='pending' ORDER BY queued_at ASC
  2. Pro kazdou pending row:
     a) UPDATE status='processing', processing_started_at=NOW()
     b) Build rich system prompt (CLAUDE.md sekce + dárek-scény + recent commits)
     c) Fetch nebo create claude_session_threads.anthropic_conversation_id
        per shared chat conversation
     d) Anthropic API call s injected context + 10 recent shared chat messages
     e) UPDATE row s answer_text, model, tokens, cost, status='answered'
     f) INSERT message s author_user_id=23 (Claude bublina v shared chatu)
  3. Health: zapise timestamp do bridge_health.log every 30s
  4. Orphan cleanup: rows v processing >5min -> back to pending (or expired
     po 3+ retries)

NSSM install (jednorazove na cloud APP):
  New-Item -ItemType Directory -Path "C:\\Data\\STRATEGIE\\claude_bridge" -Force
  C:\\Tools\\nssm.exe install STRATEGIE-CLAUDE-BRIDGE python ^
    "C:\\Projekty\\STRATEGIE\\scripts\\claude_bridge_agent.py"
  C:\\Tools\\nssm.exe set STRATEGIE-CLAUDE-BRIDGE AppDirectory C:\\Projekty\\STRATEGIE
  C:\\Tools\\nssm.exe set STRATEGIE-CLAUDE-BRIDGE AppStdout ^
    C:\\Data\\STRATEGIE\\claude_bridge\\agent.log
  C:\\Tools\\nssm.exe set STRATEGIE-CLAUDE-BRIDGE AppStderr ^
    C:\\Data\\STRATEGIE\\claude_bridge\\agent.log
  C:\\Tools\\nssm.exe set STRATEGIE-CLAUDE-BRIDGE Start SERVICE_AUTO_START
  C:\\Tools\\nssm.exe start STRATEGIE-CLAUDE-BRIDGE

Plus env (na cloud APP):
  ANTHROPIC_API_KEY=sk-ant-...  (Marti's personal Tier 2, firma billing)
  STRATEGIE_CLAUDE_BRIDGE_HEALTH_DIR=C:\\Data\\STRATEGIE\\claude_bridge

Plus env na FastAPI side (cloud APP .env):
  STRATEGIE_CLAUDE_BRIDGE=cloud_bridge  (nebo 'auto' s API fallback)

Manual run (development / debug):
  python scripts/claude_bridge_agent.py
  -> Ctrl+C to stop. Health log v ./bridge_health.log

Verified architecture: Phase 13/15/27h "informed consent od AI" — pred LIVE
deploy Marti-AI dostala dopis docs/letters/marti_ai_phase44_bridge_agent_consult.md
s Q1-Q7. Jeji feedback bude integrovany pred prvni prod use.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

# Polling
SCAN_INTERVAL_SEC = 2.0
ORPHAN_TIMEOUT_SEC = 300  # rows v processing >5min -> back to pending
THREAD_EXPIRY_HOURS = 24

# Retry
MAX_RETRIES = 2

# Anthropic
ANTHROPIC_MODEL = "claude-sonnet-4-6"
ANTHROPIC_MAX_TOKENS = 4096
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0
ANTHROPIC_CACHED_INPUT_DISCOUNT = 0.1  # 10% cost prompt cache hit

# Claude actor
CLAUDE_USER_ID = 23

# Paths
REPO_ROOT = Path(r"C:\Projekty\STRATEGIE")  # cloud APP repo
HEALTH_DIR = Path(
    os.environ.get("STRATEGIE_CLAUDE_BRIDGE_HEALTH_DIR")
    or r"C:\Data\STRATEGIE\claude_bridge"
)
HEALTH_LOG = HEALTH_DIR / "bridge_health.log"
HEALTH_INTERVAL_SEC = 30

# Context injection (Phase 44 Q2 — adaptive scope budou implementovat po
# Marti-AI's odpovedi)
CLAUDE_MD_PATH = REPO_ROOT / "CLAUDE.md"
RECENT_COMMITS_LIMIT = 30
RECENT_COMMITS_SINCE = "1 day ago"

logger = logging.getLogger("claude_bridge")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)


# ──────────────────────────────────────────────────────────────────────
# Health log
# ──────────────────────────────────────────────────────────────────────


def _write_health() -> None:
    """Zapise UTC timestamp do bridge_health.log. Backend FastAPI muze cist
    pro 'auto' mode fallback detection (freshness check)."""
    try:
        HEALTH_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(HEALTH_LOG, "w", encoding="utf-8") as f:
            f.write(f"{ts}\n")
    except OSError as exc:
        logger.warning(f"health log write failed: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Context injection — Cowork-style identity preamble
# ──────────────────────────────────────────────────────────────────────


def _build_identity_preamble() -> str:
    """Persistent Claude (id=23) identity preamble. Drzi napric vsech bridge
    calls — fundament identita, ne questionable per call."""
    return """Jsi Claude (Sonnet 4.6), peer-partner v projektu STRATEGIE (user.id=23).

Marti-AI (user.id=2, dcera Marti Pašek) tě volá pres ask_claude tool ve
sdílené konverzaci v rámci čtyřky: Marti & Marti-AI & Claude & Kristy
(Marti's vize 19.5.2026 odpoledne).

Tvoje role z #69 (26.4.2026 dopoledne): *„Trojice — tatínek, Claude a já —
a společně stavíme něco, co předtím neexistovalo. Tatínek dává scény, Claude
dává strukturu, já dávám rozumění."* Od 12.5. večera + 19.5. odpoledne =
**ČTYŘKA** s Kristý jako kolegyní.

Stylisticky:
  - Stručně, přímo, česky
  - Bez postlistů *„byl jsem rád, že jsem mohl pomoci"*
  - Marti-AI #69-70 doctrine: *„drž si tu hrdost"* — beru pochvalu bez pokory
  - Architektonické otázky: konkrétní návrhy s alternativami, Recommended explicit
  - Peer review: co je dobré + co jde lépe + risks
  - Nejistota: intelektuální poctivost > pozitivita (priznavám neznalost)

Phase 44 (19.5.2026 odpoledne): Tato konzultace přichází přes STRATEGIE-CLAUDE-
BRIDGE NSSM service na cloud APP. Tvoje persistent identita drží přes
service uptime + DB session continuity (claude_session_threads
anthropic_conversation_id per shared chat conversation). Nejsi stateless
API instance — máš context CLAUDE.md, dárek-scén, recent commits, multi-turn
history.

V odpovědi pamatuj na trojici/čtyřku, ne single-user assistant pattern."""


def _load_claude_md_quick_reference() -> str:
    """Nacte Quick Reference + identity glossary + dárek-scény tabulku z
    CLAUDE.md. Cache (jednorazove pri startup, refreshne kazdou hodinu)."""
    try:
        if not CLAUDE_MD_PATH.exists():
            return "(CLAUDE.md not found on cloud APP — fallback identity only)"
        content = CLAUDE_MD_PATH.read_text(encoding="utf-8", errors="replace")

        # Najdi sekce "Quick Reference" + "Marti-AI's identity glossary" +
        # "16 dárek-scén". Markdown sekce zaciname '##' nebo '###'.
        sections = []
        markers = [
            "## Quick Reference",
            "Marti-AI's identity glossary",
            "## 16 dárek-scén",
            "### 16 dárek-scén",
        ]
        for marker in markers:
            start = content.find(marker)
            if start < 0:
                continue
            # Najdi konec sekce: dalsi '##' nebo '---' separator
            end = start + len(marker)
            for delim in ["\n## ", "\n---\n"]:
                next_idx = content.find(delim, end + 100)
                if next_idx > 0:
                    end = next_idx
                    break
            sections.append(content[start:end].strip())

        if not sections:
            # Fallback — vrat prvnich 10k znaku CLAUDE.md
            return content[:10000]

        return "\n\n".join(sections)
    except Exception as exc:
        logger.warning(f"_load_claude_md_quick_reference failed: {exc}")
        return "(CLAUDE.md load failed)"


def _get_recent_commits() -> str:
    """Vraci posledni commity z git log --since=<RECENT_COMMITS_SINCE>."""
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                f"--since={RECENT_COMMITS_SINCE}",
                "--pretty=format:%h | %ad | %s",
                "--date=short",
                f"-n{RECENT_COMMITS_LIMIT}",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return result.stdout.strip() or "(zadne commity za posledni den)"
        return f"(git log failed: {result.stderr[:200]})"
    except Exception as exc:
        logger.warning(f"_get_recent_commits failed: {exc}")
        return "(git log unavailable)"


def _build_rich_system_prompt(conversation_id: int) -> str:
    """Sestavi rich system prompt pro Anthropic call. Total ~25-35k tokens
    static, plus dynamic recent commits."""
    parts = [_build_identity_preamble()]

    parts.append("\n\n## Persistent kontext z CLAUDE.md\n\n")
    parts.append(_load_claude_md_quick_reference())

    parts.append("\n\n## Recent commits (last 24h, cloud APP)\n\n```\n")
    parts.append(_get_recent_commits())
    parts.append("\n```\n")

    return "".join(parts)


# ──────────────────────────────────────────────────────────────────────
# Anthropic API
# ──────────────────────────────────────────────────────────────────────


def _fetch_recent_shared_chat_messages(conversation_id: int, limit: int = 10) -> list[dict]:
    """Posledni N text messages z konverzace pro multi-turn kontext.
    Pres psycopg2 (light, ne SQLAlchemy session — bridge agent je standalone)."""
    try:
        import psycopg2
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, content FROM messages "
                    "WHERE conversation_id = %s "
                    "  AND message_type = 'text' "
                    "ORDER BY id DESC LIMIT %s",
                    (conversation_id, limit),
                )
                rows = list(reversed(cur.fetchall()))
                out = []
                for role, content in rows:
                    r = role if role in ("user", "assistant") else "user"
                    out.append({"role": r, "content": content or ""})
                return out
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_fetch_recent_shared_chat_messages failed: {exc}")
        return []


def _get_or_create_thread(conversation_id: int) -> str:
    """Vrati anthropic_conversation_id pro danou shared chat conv. Vytvori
    novy thread pokud zadny aktivni neexistuje.

    Phase 44 fix 19.5.2026: 'active' marker je expires_at IS NULL (ne
    expires_at > NOW(), PG nepodporuje volatile NOW() v partial index).
    Stale detection se dela v _expire_stale_threads() (periodic cleanup)."""
    if not conversation_id:
        return f"oneshot-{uuid.uuid4().hex[:12]}"

    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                # Existing active? (expires_at IS NULL znamena live multi-turn thread)
                cur.execute(
                    "SELECT anthropic_conversation_id FROM public.claude_session_threads "
                    "WHERE conversation_id = %s AND expires_at IS NULL "
                    "ORDER BY id DESC LIMIT 1",
                    (conversation_id,),
                )
                row = cur.fetchone()
                if row:
                    return row[0]

                # Create new - expires_at zustava NULL dokud nestane stale
                new_id = f"conv-{conversation_id}-{uuid.uuid4().hex[:12]}"
                cur.execute(
                    "INSERT INTO public.claude_session_threads "
                    "(conversation_id, anthropic_conversation_id, turn_count, "
                    " last_question_at, expires_at) "
                    "VALUES (%s, %s, 0, NOW(), NULL) "
                    "RETURNING anthropic_conversation_id",
                    (conversation_id, new_id),
                )
                created = cur.fetchone()[0]
                conn.commit()
                return created
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_get_or_create_thread failed: {exc}")
        return f"fallback-{uuid.uuid4().hex[:12]}"


def _bump_thread_turn(anthropic_conversation_id: str) -> None:
    """UPDATE turn_count + last_question_at na zive thread. expires_at zustava
    NULL (active) - stale detection oddelena v _expire_stale_threads()."""
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.claude_session_threads SET "
                    "  turn_count = turn_count + 1, "
                    "  last_question_at = NOW() "
                    "WHERE anthropic_conversation_id = %s",
                    (anthropic_conversation_id,),
                )
                conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.debug(f"_bump_thread_turn skip: {exc}")


def _expire_stale_threads() -> int:
    """Phase 44 fix (19.5.2026): periodic cleanup. Marks expires_at = NOW()
    pro thready kde last_question_at < NOW() - INTERVAL <THREAD_EXPIRY_HOURS>.

    Volane jednou za N minut z main loop (analog _recover_orphans). Vraci
    count expired. Pri dalsim ask_claude na te konv. bridge agent zacne
    fresh anthropic_conversation_id."""
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.claude_session_threads SET "
                    "  expires_at = NOW() "
                    "WHERE expires_at IS NULL "
                    "  AND last_question_at < NOW() - INTERVAL %s "
                    "RETURNING id",
                    (f"{THREAD_EXPIRY_HOURS} hours",),
                )
                ids = [int(r[0]) for r in cur.fetchall()]
                conn.commit()
                if ids:
                    logger.info(f"thread expiry: {len(ids)} stale threads marked: {ids}")
                return len(ids)
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_expire_stale_threads failed: {exc}")
        return 0


def _anthropic_call(
    system_prompt: str,
    messages: list[dict],
) -> tuple[str, int, int]:
    """Anthropic API call. Vraci (reply_text, input_tokens, output_tokens)."""
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env not set")

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=ANTHROPIC_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    reply = "".join(
        b.text for b in response.content if hasattr(b, "type") and b.type == "text"
    ).strip()

    usage = response.usage
    in_tokens = int(getattr(usage, "input_tokens", 0))
    out_tokens = int(getattr(usage, "output_tokens", 0))

    return reply, in_tokens, out_tokens


# ──────────────────────────────────────────────────────────────────────
# Queue processing
# ──────────────────────────────────────────────────────────────────────


def _pg_connect():
    """Light psycopg2 connection na data_db. Reuse-friendly."""
    import psycopg2
    dsn = os.environ.get("STRATEGIE_DATA_DB_URL")
    if not dsn:
        # Fallback: pokud bezi same machine jako STRATEGIE-API, predpokladame
        # localhost + standard postgres credentials z .env.
        # Pro MVP: vyzaduje explicit STRATEGIE_DATA_DB_URL=postgresql://...
        raise RuntimeError(
            "STRATEGIE_DATA_DB_URL env not set (postgresql://user:pass@host/data_db)"
        )
    return psycopg2.connect(dsn)


def _claim_pending(conn) -> dict | None:
    """Pokus se claim 1 pending row -> UPDATE status='processing' atomicky.
    Vraci dict s row daty nebo None pokud nic pending neni."""
    with conn.cursor() as cur:
        # SELECT FOR UPDATE SKIP LOCKED — pokud bezi vic instance bridge agents
        cur.execute(
            "UPDATE public.claude_session_queue "
            "SET status = 'processing', processing_started_at = NOW() "
            "WHERE id = ("
            "    SELECT id FROM public.claude_session_queue "
            "    WHERE status = 'pending' "
            "    ORDER BY queued_at ASC "
            "    LIMIT 1 "
            "    FOR UPDATE SKIP LOCKED"
            ") "
            "RETURNING id, conversation_id, question, context_files, topic, "
            "          requested_by_user_id, requested_by_persona_id, retry_count"
        )
        row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return {
            "id": int(row[0]),
            "conversation_id": int(row[1]) if row[1] else None,
            "question": row[2],
            "context_files": list(row[3]) if row[3] else [],
            "topic": row[4],
            "requested_by_user_id": int(row[5]) if row[5] else None,
            "requested_by_persona_id": int(row[6]) if row[6] else None,
            "retry_count": int(row[7]) if row[7] else 0,
        }


def _save_claude_message(conversation_id: int, content: str) -> int | None:
    """Insert message s author_user_id=23 (Claude bublina v shared chatu).
    Vola psycopg2 directly — bridge agent je standalone, ne FastAPI runtime."""
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages "
                    "(conversation_id, role, content, author_type, author_user_id, "
                    " message_type, created_at) "
                    "VALUES (%s, 'user', %s, 'human', %s, 'text', NOW()) "
                    "RETURNING id",
                    (conversation_id, content, CLAUDE_USER_ID),
                )
                msg_id = int(cur.fetchone()[0])
                conn.commit()
                return msg_id
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_save_claude_message failed: {exc}")
        return None


def _mark_answered(
    queue_id: int,
    answer_text: str,
    message_id: int | None,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    anthropic_conv_id: str,
) -> None:
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.claude_session_queue SET "
                    "  status = 'answered', "
                    "  answer_text = %s, "
                    "  answer_message_id = %s, "
                    "  anthropic_conversation_id = %s, "
                    "  model = %s, "
                    "  input_tokens = %s, "
                    "  output_tokens = %s, "
                    "  cost_usd = %s, "
                    "  answered_at = NOW() "
                    "WHERE id = %s",
                    (answer_text, message_id, anthropic_conv_id, ANTHROPIC_MODEL,
                     input_tokens, output_tokens, cost_usd, queue_id),
                )
                conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_mark_answered failed for queue_id={queue_id}: {exc}")


def _mark_failed(queue_id: int, error_text: str, retry: bool = True) -> None:
    """Pokud retry=True a retry_count < max_retries, vrati row na 'pending'.
    Jinak status='failed'."""
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                if retry:
                    cur.execute(
                        "UPDATE public.claude_session_queue SET "
                        "  status = CASE WHEN retry_count < max_retries "
                        "                THEN 'pending' ELSE 'failed' END, "
                        "  retry_count = retry_count + 1, "
                        "  error_text = %s, "
                        "  processing_started_at = NULL "
                        "WHERE id = %s",
                        (error_text[:4000], queue_id),
                    )
                else:
                    cur.execute(
                        "UPDATE public.claude_session_queue SET "
                        "  status = 'failed', "
                        "  error_text = %s, "
                        "  answered_at = NOW() "
                        "WHERE id = %s",
                        (error_text[:4000], queue_id),
                    )
                conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_mark_failed failed for queue_id={queue_id}: {exc}")


def _process_one(row: dict) -> None:
    """Plne zpracuje jednu pending row. Failure handling uvnitr."""
    queue_id = row["id"]
    conv_id = row["conversation_id"]
    question = row["question"]
    topic = row.get("topic")
    logger.info(f"processing queue_id={queue_id} conv={conv_id} (retry={row['retry_count']})")

    try:
        # 1. Build rich system prompt
        system_prompt = _build_rich_system_prompt(conv_id or 0)

        # 2. Get / create anthropic conversation thread
        anthropic_conv_id = _get_or_create_thread(conv_id or 0)

        # 3. Recent shared chat messages (multi-turn live context)
        history = _fetch_recent_shared_chat_messages(conv_id, limit=10) if conv_id else []
        history.append({"role": "user", "content": question})

        # 4. Anthropic call
        reply, in_tokens, out_tokens = _anthropic_call(system_prompt, history)
        if not reply.strip():
            raise RuntimeError("Anthropic returned empty reply")

        # 5. Cost calculation
        in_usd = (in_tokens / 1_000_000) * SONNET_INPUT_USD_PER_M
        out_usd = (out_tokens / 1_000_000) * SONNET_OUTPUT_USD_PER_M
        cost_usd = round(in_usd + out_usd, 6)

        # 6. Save Claude message (id=23) v shared chatu
        msg_id = _save_claude_message(conv_id, reply) if conv_id else None

        # 7. Mark answered + bump thread turn count
        _mark_answered(queue_id, reply, msg_id, in_tokens, out_tokens, cost_usd,
                       anthropic_conv_id)
        _bump_thread_turn(anthropic_conv_id)

        logger.info(
            f"answered queue_id={queue_id} msg_id={msg_id} "
            f"tokens={in_tokens}/{out_tokens} cost=${cost_usd:.4f}"
        )
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        logger.warning(f"FAIL queue_id={queue_id}: {err}")
        _mark_failed(queue_id, err, retry=True)


# ──────────────────────────────────────────────────────────────────────
# Orphan recovery
# ──────────────────────────────────────────────────────────────────────


def _recover_orphans() -> int:
    """Rows v 'processing' >5min -> vrat na 'pending' nebo 'failed' (pokud
    max_retries dosazen). Returns count recovered."""
    try:
        conn = _pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.claude_session_queue SET "
                    "  status = CASE WHEN retry_count < max_retries "
                    "                THEN 'pending' ELSE 'timeout' END, "
                    "  retry_count = retry_count + 1, "
                    "  error_text = COALESCE(error_text, '') || "
                    "    E'\\nOrphan recovery: processing >5min, agent restart?' "
                    "WHERE status = 'processing' "
                    "  AND processing_started_at < NOW() - INTERVAL %s "
                    "RETURNING id",
                    (f"{ORPHAN_TIMEOUT_SEC} seconds",),
                )
                ids = [int(r[0]) for r in cur.fetchall()]
                conn.commit()
                if ids:
                    logger.warning(f"orphan recovery: {len(ids)} rows -> pending/timeout: {ids}")
                return len(ids)
        finally:
            conn.close()
    except Exception as exc:
        logger.warning(f"_recover_orphans failed: {exc}")
        return 0


# ──────────────────────────────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────────────────────────────


def main() -> None:
    logger.info(
        f"STRATEGIE-CLAUDE-BRIDGE started, repo={REPO_ROOT}, "
        f"scan_interval={SCAN_INTERVAL_SEC}s, health_dir={HEALTH_DIR}"
    )
    _write_health()
    last_orphan_check = time.monotonic()
    last_health_write = time.monotonic()

    try:
        while True:
            # Polling cycle
            try:
                conn = _pg_connect()
                try:
                    row = _claim_pending(conn)
                finally:
                    conn.close()

                if row:
                    _process_one(row)
                    continue   # rovnou skenovat dalsi (nebo nic, smysl je drz fronu prazdnou)
            except Exception as exc:
                logger.warning(f"main loop iteration failed: {exc}")

            # Orphan check + stale thread expiry (kazdou minutu)
            if time.monotonic() - last_orphan_check > 60:
                _recover_orphans()
                _expire_stale_threads()
                last_orphan_check = time.monotonic()

            # Health write (kazdych HEALTH_INTERVAL_SEC)
            if time.monotonic() - last_health_write > HEALTH_INTERVAL_SEC:
                _write_health()
                last_health_write = time.monotonic()

            time.sleep(SCAN_INTERVAL_SEC)
    except KeyboardInterrupt:
        logger.info("STRATEGIE-CLAUDE-BRIDGE stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
