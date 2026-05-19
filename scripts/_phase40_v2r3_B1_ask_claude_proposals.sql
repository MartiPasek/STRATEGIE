-- Phase 40 v2 r3 — Mini-faze B.1 (19.5.2026 dopoledne)
-- DDL: ask_claude_proposals — pending approval pro cost-based gate
--
-- Marti's Q3 doctrine: lidska hodinova sazba ~470 Kc/h, AI nasobne vykonnejsi,
-- ale shared conv limit 300 Kc/h. Pri prekroceni: Marti-AI navrhne ask_claude
-- (proposal row), Marti / Kristy v chatu odpovi OK / NE pres approve_ask_claude
-- / reject_ask_claude AI tools. Phase 42 deferred: zitra zkusime auto-approve.
--
-- Spusteni: DBeaver jako Marti-AI (db_owner public).

BEGIN;

CREATE TABLE IF NOT EXISTS public.ask_claude_proposals (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    -- Marti-AI's request
    question TEXT NOT NULL,
    context_files JSONB DEFAULT '[]'::jsonb,
    topic VARCHAR(80),
    -- Cost estimate (model: Sonnet 4.6, ~10 messages context, ~4k output)
    estimated_cost_czk NUMERIC(10, 2) DEFAULT 0,
    -- Cumulative cost v predchozich 60 min (proc tento proposal vznikl)
    cumulative_hour_cost_czk NUMERIC(10, 2) DEFAULT 0,
    -- Stav: pending = ceka na approve/reject, approved = executed, rejected = canceled
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'executed', 'expired')),
    -- Kdo navrhl (typicky Marti-AI persona.id=1 = user_id=2)
    proposed_by_user_id BIGINT,
    proposed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Kdo rozhodl
    decided_by_user_id BIGINT,
    decided_at TIMESTAMPTZ,
    decision_reason TEXT,
    -- Pokud approved + executed, link na vyslednou Claude message v conversations
    response_msg_id BIGINT,
    response_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_ask_claude_proposals_conv_status
  ON public.ask_claude_proposals (conversation_id, status, proposed_at DESC);

CREATE INDEX IF NOT EXISTS ix_ask_claude_proposals_pending
  ON public.ask_claude_proposals (conversation_id)
  WHERE status = 'pending';

COMMENT ON TABLE public.ask_claude_proposals IS
  'Phase 40 v2 r3 Mini-faze B (19.5.2026): cost-based gate pro ask_claude AI tool. '
  'Marti Q3 doctrine: shared conv limit 300 Kc/h. Pri prekroceni Marti-AI navrhne, '
  'Marti / Kristy approve_ask_claude(proposal_id) v chatu. Pod limitem Marti-AI '
  'execute primo (status=executed pri zapisu).';

-- Ownership Marti-AI (db_owner public per Phase 38.4 GRANT C)
ALTER TABLE public.ask_claude_proposals OWNER TO "Marti-AI";

-- Strategie user (API process) potrebuje SELECT/INSERT/UPDATE
GRANT SELECT, INSERT, UPDATE ON public.ask_claude_proposals TO strategie;
GRANT USAGE ON SEQUENCE public.ask_claude_proposals_id_seq TO strategie;

-- Verify
SELECT
  table_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'ask_claude_proposals'
ORDER BY ordinal_position;

COMMIT;
