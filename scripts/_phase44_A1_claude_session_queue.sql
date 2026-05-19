-- Phase 44 — Mini-fáze A.1 (19.5.2026 odpoledne)
-- DDL: claude_session_queue + claude_session_threads
--
-- Marti's vize (19.5. odpoledne): Persistent Claude (id=23) přes Python
-- bridge agent NSSM service. Marti-AI v shared chatu volá ask_claude →
-- INSERT pending → STRATEGIE-CLAUDE-BRIDGE pollu → rich context injection
-- + Anthropic API → UPDATE answered → Marti vidí Claude bublinu (Phase 43
-- Mini-fáze A extra_messages path).
--
-- Spuštění: DBeaver jako Marti-AI (db_owner public).

BEGIN;

-- ──────────────────────────────────────────────────────────────────────
-- 1. claude_session_queue (FIFO single-table queue)
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.claude_session_queue (
    id BIGSERIAL PRIMARY KEY,

    -- Caller kontext
    conversation_id BIGINT REFERENCES public.conversations(id) ON DELETE SET NULL,
    requested_by_user_id BIGINT,        -- typicky Marti-AI (user.id=2)
    requested_by_persona_id BIGINT,     -- pro audit

    -- Question payload
    question TEXT NOT NULL,
    context_files TEXT[],                -- volitelný Phase 43 Mini-fáze B passthrough
    topic VARCHAR(100),                  -- Cowork-style topic tag

    -- Multi-turn continuity přes anthropic_conversation_id
    -- (vyplnen z claude_session_threads mappingu pri enqueue)
    anthropic_conversation_id VARCHAR(100),

    -- Stav: pending → processing → answered (success) | failed | timeout | expired
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN
        ('pending', 'processing', 'answered', 'failed', 'timeout', 'expired')),

    -- Response
    answer_text TEXT,
    answer_message_id BIGINT,            -- FK na messages.id (Claude bublina po save_message)
    error_text TEXT,

    -- Telemetry (paralela s llm_calls)
    model VARCHAR(50),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10, 6),

    -- Timing
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_started_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,              -- background cleanup task

    -- Retry tracking
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 2
);

-- Hot index pro polling agent: WHERE status='pending' ORDER BY queued_at ASC
CREATE INDEX IF NOT EXISTS ix_claude_session_queue_pending
    ON public.claude_session_queue (queued_at ASC)
    WHERE status = 'pending';

-- Pro orphan cleanup (rows stuck v processing > 5min → back to pending)
CREATE INDEX IF NOT EXISTS ix_claude_session_queue_processing
    ON public.claude_session_queue (processing_started_at ASC)
    WHERE status = 'processing';

-- Pro conversation drill-down (Marti vidí všechny ask_claude calls v dané konv.)
CREATE INDEX IF NOT EXISTS ix_claude_session_queue_conversation
    ON public.claude_session_queue (conversation_id, queued_at DESC)
    WHERE conversation_id IS NOT NULL;

COMMENT ON TABLE public.claude_session_queue IS
    'Phase 44 (19.5.2026): Persistent Claude bridge queue. Marti-AI v shared '
    'chatu volá ask_claude → INSERT pending. STRATEGIE-CLAUDE-BRIDGE NSSM '
    'service pollu pending rows, volá Anthropic API s rich injected context '
    '(CLAUDE.md sections, dárek-scény, recent commits) + anthropic_conversation_id '
    'per shared chat pro multi-turn continuity. UPDATE answered → ask_claude '
    'service vrátí reply do composer synthesis. Marti''s vize "persistent '
    'Claude id=23 napříč STRATEGIE chat". Plus Marti-AI + Kristý + Claude '
    '= velká čtyřka s Marti.';

ALTER TABLE public.claude_session_queue OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.claude_session_queue TO strategie;
GRANT USAGE ON SEQUENCE public.claude_session_queue_id_seq TO strategie;

-- ──────────────────────────────────────────────────────────────────────
-- 2. claude_session_threads (multi-turn mapping)
-- ──────────────────────────────────────────────────────────────────────
-- Per shared chat conversation existuje 0 nebo 1 active thread mapping
-- na anthropic_conversation_id. Po 24h bez activity thread expires,
-- next ask_claude začne fresh anthropic_conversation_id.

CREATE TABLE IF NOT EXISTS public.claude_session_threads (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    anthropic_conversation_id VARCHAR(100) NOT NULL UNIQUE,
    turn_count INTEGER NOT NULL DEFAULT 0,
    last_question_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Per conversation jen 1 active (non-expired) thread
CREATE UNIQUE INDEX IF NOT EXISTS ix_claude_session_threads_conv_active
    ON public.claude_session_threads (conversation_id)
    WHERE expires_at > NOW();

CREATE INDEX IF NOT EXISTS ix_claude_session_threads_expired
    ON public.claude_session_threads (expires_at)
    WHERE expires_at <= NOW();

COMMENT ON TABLE public.claude_session_threads IS
    'Phase 44 (19.5.2026): Multi-turn mapping pro persistent Claude bridge. '
    'Per conversation_id 0 nebo 1 active thread → anthropic_conversation_id. '
    'Po 24h bez activity expires, next ask_claude začne fresh. Drží '
    'Marti-AI''s + Claude''s multi-turn dialog continuity v rámci '
    'jednoho pracovního dne.';

ALTER TABLE public.claude_session_threads OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.claude_session_threads TO strategie;
GRANT USAGE ON SEQUENCE public.claude_session_threads_id_seq TO strategie;

COMMIT;

-- Verify
SELECT 'claude_session_queue' AS table_name, COUNT(*) AS columns
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'claude_session_queue'
UNION ALL
SELECT 'claude_session_threads', COUNT(*)
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'claude_session_threads';
