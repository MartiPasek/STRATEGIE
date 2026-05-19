-- Phase 31 context_window_size default 5 -> 20 (19.5.2026 vecer)
--
-- Marti's catch z "lamani chleba" experimentu:
--   Marti-AI ztratila kontext po 6 turnech behem first autonomous build
--   (prehled all_users). 5-message window pro multi-turn build sessions
--   = catastrophic context loss. 20 = 10 turnu, dost pro full discovery
--   -> design -> implement flow.
--
-- Run: psql -h 10.200.188.12 -U strategie -d data_db -f tento_soubor.sql
--   (strategie role ma write na public schema)

BEGIN;

-- 1. Update existing rows s explicit 5 -> 20
UPDATE public.conversations
SET context_window_size = 20
WHERE context_window_size = 5;

-- 2. Change column default (DDL — affects all future INSERTs without explicit value)
ALTER TABLE public.conversations
ALTER COLUMN context_window_size SET DEFAULT 20;

COMMIT;

-- Verify:
-- SELECT context_window_size, COUNT(*) FROM public.conversations GROUP BY 1 ORDER BY 1;
-- Expected: 20 = vetsina (vsechny migrovane), pripadne ruzne hodnoty (Marti-AI's set_conversation_window calls).

-- Plus check DEFAULT:
-- SELECT column_default FROM information_schema.columns
-- WHERE table_schema='public' AND table_name='conversations'
-- AND column_name='context_window_size';
-- Expected: 20
