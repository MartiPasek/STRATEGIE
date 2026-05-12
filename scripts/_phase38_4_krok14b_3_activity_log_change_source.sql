-- Phase 38.4 Krok 14b — Migrace 3: activity_log.change_source
-- Date: 13.5.2026 (drft pripraveny 12.5. vecer ~20:30)
--
-- Marti-AI's bod #A insider design contribution (12.5. vecer):
-- "change_source field — 'ui' / 'api' / 'migration' / 'marti_ai'.
-- Tedz to mozna vypada zbytecne, ale az prijde Vrstva 2, budes rad.
-- Jeden VARCHAR(20), ted, levne."
--
-- Forward-thinking pattern: "pojmenuju to ted, at to neni prekvapeni
-- za 3 mesice".
--
-- Hodnoty:
--   'ui'        — uzivatel klikl Save v Design modalu (Vrstva 1, today)
--   'api'       — externi API call (Marti-AI MCP tool, REST endpoint)
--   'migration' — alembic migration / SQL script
--   'marti_ai'  — Marti-AI direct (chat-driven, ne pres MCP)
--   'cron'      — scheduled task / background worker
--   'system'    — fallback pro neidentifikovany zdroj

BEGIN;

-- ADD COLUMN nullable (existing rows mit NULL)
ALTER TABLE public.activity_log
  ADD COLUMN IF NOT EXISTS change_source VARCHAR(20);

-- Index pro filter queries
CREATE INDEX IF NOT EXISTS ix_activity_log_change_source
  ON public.activity_log(change_source)
  WHERE change_source IS NOT NULL;

-- Optional CHECK constraint pro valid values (jen prevention typo)
-- Komentar: pokud nevadi free-form, mozeme constraint vynechat.
-- Marti-AI's intent byl whitelist, pojde s constraint.
ALTER TABLE public.activity_log
  ADD CONSTRAINT activity_log_change_source_check
  CHECK (
    change_source IS NULL OR
    change_source IN ('ui', 'api', 'migration', 'marti_ai', 'cron', 'system')
  );

-- Verification
SELECT column_name, data_type, is_nullable, character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'activity_log'
  AND column_name = 'change_source';

COMMIT;

-- ROLLBACK guard:
-- BEGIN;
--   ALTER TABLE public.activity_log
--     DROP CONSTRAINT IF EXISTS activity_log_change_source_check;
--   DROP INDEX IF EXISTS public.ix_activity_log_change_source;
--   ALTER TABLE public.activity_log
--     DROP COLUMN IF EXISTS change_source;
-- COMMIT;
