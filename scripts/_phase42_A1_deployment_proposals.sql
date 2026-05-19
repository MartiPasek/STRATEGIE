-- Phase 42 — Mini-faze A.1 (19.5.2026 dopoledne)
-- DDL: deployment_proposals — Marti-AI navrhne git pull + restart, Marti / Kristy
-- v chatu approve_deployment / reject_deployment.
--
-- Marti's Q5 doctrine (19.5.2026 rano): Deploy s potvrzenim Marti / Kristy
-- v chatu pres OK. Zitra mozna auto-approve.
--
-- Workflow:
--   1. Marti-AI vola propose_deployment(commit_sha, description)
--   2. Backend overi git status (clean, na main, mergeable), vytvori proposal row
--   3. Marti / Kristy v chatu: approve_deployment(proposal_id)
--      OR reject_deployment(proposal_id, reason)
--   4. Pri approve: git pull origin main + dotkne marker_file ->
--      NSSM watchdog (nebo external monitor) detekuje change, restartne STRATEGIE-API
--   5. After restart: proposal status='deployed', restart_at = NOW()
--
-- Spusteni: DBeaver jako Marti-AI (db_owner public).

BEGIN;

CREATE TABLE IF NOT EXISTS public.deployment_proposals (
    id BIGSERIAL PRIMARY KEY,
    -- Marti-AI's navrh
    description TEXT NOT NULL,
    commit_sha VARCHAR(40),      -- target commit (origin/main HEAD)
    commit_message TEXT,          -- prvni radek commit zpravy
    files_changed INTEGER,        -- count zmen v diffu (sanity)
    -- Conversation kontext (pro audit)
    conversation_id BIGINT REFERENCES public.conversations(id) ON DELETE SET NULL,
    -- Stav: pending = ceka, approved = OK, rejected = NE, deployed = pull+restart OK,
    --       failed = pull nebo restart selhal
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'deploying', 'deployed', 'failed', 'expired')),
    -- Kdo navrhl (Marti-AI = user.id=2)
    proposed_by_user_id BIGINT,
    proposed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Kdo rozhodl
    decided_by_user_id BIGINT,
    decided_at TIMESTAMPTZ,
    decision_reason TEXT,
    -- Deploy execution
    deploy_started_at TIMESTAMPTZ,
    deploy_completed_at TIMESTAMPTZ,
    deploy_output TEXT,            -- git pull + restart log (truncated 4 KB)
    deploy_error TEXT,             -- failure detail
    -- Marker file path (touch -> NSSM watchdog reaguje)
    restart_marker_file VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS ix_deployment_proposals_status_proposed
  ON public.deployment_proposals (status, proposed_at DESC);

CREATE INDEX IF NOT EXISTS ix_deployment_proposals_pending
  ON public.deployment_proposals (id)
  WHERE status = 'pending';

COMMENT ON TABLE public.deployment_proposals IS
  'Phase 42 (19.5.2026): Marti-AI''s deploy autonomy. Marti-AI navrhne git pull '
  '+ restart, Marti / Kristy v chatu approve_deployment(proposal_id) pres OK. '
  'Po approve backend volá git pull origin main + touch marker_file -> NSSM '
  'watchdog detekuje change a graceful restartne STRATEGIE-API. '
  'Marti odjizdi Praha 20.-21.5., Kristy s Marti-AI zustavaji autonomni.';

ALTER TABLE public.deployment_proposals OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.deployment_proposals TO strategie;
GRANT USAGE ON SEQUENCE public.deployment_proposals_id_seq TO strategie;

-- Verify
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'deployment_proposals'
ORDER BY ordinal_position;

COMMIT;
