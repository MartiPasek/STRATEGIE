-- ═══════════════════════════════════════════════════════════════════════
-- Knowledge base ALTER (19.5.2026 vecer, lámání chleba follow-up):
-- Add audit text columns (Marti's „NE-anonymous master view" z 16.5.).
--
-- Marti-AI's catch během prvního autonomního UPDATE knowledge_entry:
--   column "updated_by_text" does not exist
--
-- Pridat:
--   - public.knowledge_topic: created_by_id, created_by_text, updated_by_id, updated_by_text
--   - public.knowledge_entry: created_by_text, updated_by_text (ID už existuje)
--
-- Plus backfill existing seed rows (5 topics + 1 entry).
--
-- Run: DBeaver strategie session (public schema)
--   highlight cely soubor + Alt+X (BEGIN/COMMIT atomic)
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. ALTER public.knowledge_topic — add audit fields (chyběly v MVP DDL)
ALTER TABLE public.knowledge_topic
    ADD COLUMN IF NOT EXISTS created_by_id BIGINT,
    ADD COLUMN IF NOT EXISTS created_by_text VARCHAR(100),
    ADD COLUMN IF NOT EXISTS updated_by_id BIGINT,
    ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(100);

-- 2. ALTER public.knowledge_entry — add audit text (ID už existuje)
ALTER TABLE public.knowledge_entry
    ADD COLUMN IF NOT EXISTS created_by_text VARCHAR(100),
    ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(100);

-- 3. Backfill existing seed topics (5 rows z initial deploy)
UPDATE public.knowledge_topic
SET created_by_id = 1,
    created_by_text = 'Marti',
    updated_by_id = 1,
    updated_by_text = 'Marti'
WHERE created_by_id IS NULL;

-- 4. Backfill existing knowledge_entry (1 row — create_grid first entry)
UPDATE public.knowledge_entry
SET created_by_text = 'Marti',
    updated_by_text = 'Marti'
WHERE created_by_text IS NULL OR updated_by_text IS NULL;

-- 5. Re-confirm GRANT (covers new columns automatically, ale safe re-run)
GRANT SELECT, INSERT, UPDATE ON public.knowledge_topic TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.knowledge_entry TO "Marti-AI";

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY:
-- ════════════════════════════════════════════════════════════════════════
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='public' AND table_name='knowledge_entry'
-- AND column_name LIKE '%_by_%' ORDER BY ordinal_position;
-- Expected: 4 rows (created_by_id, created_by_text, updated_by_id, updated_by_text)
--
-- SELECT id, created_by_text, updated_by_text FROM public.knowledge_entry WHERE id=1;
-- Expected: created_by_text='Marti', updated_by_text='Marti'
