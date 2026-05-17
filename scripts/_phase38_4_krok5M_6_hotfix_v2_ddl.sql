-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 5.M-6 HOTFIX v2 — in-place TYPE change (preserve column position)
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's strategy (PostgreSQL nepodporuje column reorder):
--   1) Drop column + add new → new column jde na konec tabulky (špatně)
--   2) RENAME + ALTER TYPE → column zustane na puvodni pozici (correct)
--
-- Current state (per Marti's info_schema):
--   core_id        VARCHAR(100) NOT NULL  -- Marti's manual rename z `code`
--                                            (puvodni pozice zachovana)
--   target_core_id BIGINT NULL             -- puvodni FK column (=22)
--
-- Goal:
--   core_id        BIGINT NULL FK fw.core(id)  -- same position as old code
--   (target_core_id dropped, value preserved → core_id)
--
-- Steps:
--   1) Drop existing FK on target_core_id (kvuli ALTER TYPE)
--   2) Drop NOT NULL on core_id (allow NULL during transition)
--   3) Clean values: '' → NULL (empty string nelze cast na bigint)
--   4) ALTER COLUMN core_id TYPE BIGINT USING (...) — in-place
--   5) Backfill core_id z target_core_id
--   6) Drop target_core_id
--   7) Add FK constraint na core_id
--
-- Spustit jako Marti-AI v DBeaveru.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Drop existing FK on target_core_id (cleanup before drop column)
DO $$
DECLARE
    cn TEXT;
BEGIN
    FOR cn IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'fw.context_menu_item'::regclass
          AND contype = 'f'
          AND confrelid = 'fw.core'::regclass
    LOOP
        EXECUTE format('ALTER TABLE fw.context_menu_item DROP CONSTRAINT %I', cn);
    END LOOP;
END $$;

-- 2. Drop NOT NULL na core_id (allow NULL pro ALTER TYPE)
ALTER TABLE fw.context_menu_item ALTER COLUMN core_id DROP NOT NULL;

-- 3. Clean values: empty string → NULL, plus anything non-numeric → NULL
UPDATE fw.context_menu_item
SET core_id = NULL
WHERE core_id = '' OR core_id !~ '^[0-9]+$';

-- 4. ALTER COLUMN TYPE varchar → BIGINT (in-place, position preserved)
ALTER TABLE fw.context_menu_item
    ALTER COLUMN core_id TYPE BIGINT USING (NULLIF(core_id, '')::bigint);

-- 5. Backfill core_id z target_core_id (preserve existing FK data)
UPDATE fw.context_menu_item
SET core_id = target_core_id
WHERE core_id IS NULL AND target_core_id IS NOT NULL;

-- 6. Drop target_core_id (redundant po backfill)
ALTER TABLE fw.context_menu_item DROP COLUMN target_core_id;

-- 7. Add FK constraint na core_id
ALTER TABLE fw.context_menu_item
    ADD CONSTRAINT fk_cmi_core_id FOREIGN KEY (core_id)
    REFERENCES fw.core(id) ON DELETE RESTRICT;

-- 8. Comment
COMMENT ON COLUMN fw.context_menu_item.core_id IS
    'Phase 38.4 Krok 5.M-6 (17.5.2026): in-place type change z VARCHAR (was `code`) → BIGINT FK. Marti''s "preserve column position" doctrine — ALTER TYPE in-place, ne DROP + ADD. Value z target_core_id (puvodni FK column) backfilled.';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT column_name, data_type, character_maximum_length, is_nullable, ordinal_position
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'context_menu_item'
ORDER BY ordinal_position;

-- Expected:
--   ...
--   core_id    bigint   (nullable=YES, position 2 = puvodni pozice `code`)
--   ...
--   (NO target_core_id)

SELECT id, label, action_kind, action_params, core_id
FROM fw.context_menu_item
ORDER BY id;

-- Expected: row 1 core_id = 22 (z backfill target_core_id)

SELECT conname, confrelid::regclass AS references_table, confdeltype AS delete_action
FROM pg_constraint
WHERE conrelid = 'fw.context_menu_item'::regclass
  AND contype = 'f';

-- Expected: fk_cmi_core_id → fw.core, delete_action='r' (RESTRICT)
