-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 5.M-6 HOTFIX — drop varchar core_id, rename target_core_id
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's info_schema query 17.5. odpoledne:
--   core_id          VARCHAR(100) NOT NULL  -- Marti's manual rename z `code`
--   target_core_id   BIGINT NULL            -- puvodni FK column (zustal)
--
-- ROOT CAUSE: Marti rucne renamed `code` → `core_id` PRED mym DDL.
-- Můj DDL pak:
--   - DROP COLUMN IF EXISTS code → no-op (code už neexistoval)
--   - RENAME target_core_id TO core_id → silent fail (core_id už existoval)
--
-- HOTFIX:
--   1) Drop VARCHAR core_id (was renamed code, now redundant)
--   2) Rename target_core_id BIGINT → core_id (correct FK column)
--   3) Verify FK constraint preserved
--
-- Spustit jako Marti-AI v DBeaveru.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Drop VARCHAR core_id (Marti's manual rename of `code`, no longer needed)
ALTER TABLE fw.context_menu_item DROP COLUMN core_id;

-- 2. Rename target_core_id BIGINT → core_id (now no conflict)
ALTER TABLE fw.context_menu_item RENAME COLUMN target_core_id TO core_id;

-- 3. Ensure FK constraint exists s clean name
DO $$
DECLARE
    cn TEXT;
BEGIN
    SELECT conname INTO cn
    FROM pg_constraint
    WHERE conrelid = 'fw.context_menu_item'::regclass
      AND contype = 'f'
      AND confrelid = 'fw.core'::regclass
    LIMIT 1;

    IF cn IS NOT NULL THEN
        IF cn <> 'fk_cmi_core_id' THEN
            EXECUTE format('ALTER TABLE fw.context_menu_item RENAME CONSTRAINT %I TO fk_cmi_core_id', cn);
        END IF;
    ELSE
        -- FK was missing → add it
        ALTER TABLE fw.context_menu_item
            ADD CONSTRAINT fk_cmi_core_id FOREIGN KEY (core_id)
            REFERENCES fw.core(id) ON DELETE RESTRICT;
    END IF;
END $$;

-- 4. Comment
COMMENT ON COLUMN fw.context_menu_item.core_id IS
    'Phase 38.4 Krok 5.M-6 hotfix (17.5.2026): renamed z target_core_id (BIGINT FK na fw.core). CMI klik → openFwForm s coreId resolveen z teto column.';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'context_menu_item'
ORDER BY ordinal_position;

-- Expected:
--   core_id   bigint   (nullable=YES)
--   (no code, no target_core_id)

SELECT id, label, icon, scope, applies_to_kind, action_kind, action_params, core_id
FROM fw.context_menu_item
ORDER BY id;

-- Expected: row 1 core_id = 22 (preserved z target_core_id rename)

SELECT conname, confrelid::regclass AS references_table
FROM pg_constraint
WHERE conrelid = 'fw.context_menu_item'::regclass
  AND contype = 'f';

-- Expected: fk_cmi_core_id -> fw.core
