-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 5.M-6 — fw.context_menu_item schema refactor (17.5.2026)
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's request 17.5. večer:
--   "Smazal jsem ze sloupecku code to co tam bylo... Ted je treba
--    sloupecek field code prejmenovat na core_id a udelat jej jako FK..."
--
-- INTENT (Claude's interpretation): drop string `code` identifier (no longer
-- needed — CMI identified by id + label), rename existing target_core_id
-- to cleaner `core_id`. ONE FK column to fw.core, no duplicate.
--
-- Pre-state (current):
--   code               VARCHAR (Marti cleared all values, no longer needed)
--   target_core_id     BIGINT FK fw.core(id) ON DELETE RESTRICT
--
-- Post-state (after refactor):
--   core_id            BIGINT FK fw.core(id) ON DELETE RESTRICT
--   (code column dropped)
--
-- Spustit jako Marti-AI v DBeaveru (fw schema = Marti-AI's owned).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. DROP code column (Marti cleared values, no longer needed)
ALTER TABLE fw.context_menu_item DROP COLUMN IF EXISTS code;

-- 2. RENAME target_core_id → core_id (cleaner name)
ALTER TABLE fw.context_menu_item RENAME COLUMN target_core_id TO core_id;

-- 3. Rename FK constraint (PostgreSQL keeps original constraint, just rename
--    for clarity — find existing constraint name first)
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
        EXECUTE format('ALTER TABLE fw.context_menu_item RENAME CONSTRAINT %I TO fk_cmi_core_id', cn);
    ELSE
        -- FK didn't exist (rare) — add it
        ALTER TABLE fw.context_menu_item
            ADD CONSTRAINT fk_cmi_core_id FOREIGN KEY (core_id)
            REFERENCES fw.core(id) ON DELETE RESTRICT;
    END IF;
END $$;

-- 4. Comment (audit trail)
COMMENT ON COLUMN fw.context_menu_item.core_id IS
    'Phase 38.4 Krok 5.M-6 (17.5.2026): renamed z target_core_id. FK na fw.core(id) ON DELETE RESTRICT. CMI klik → openFwForm s coreId resolveen z teto column.';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
\d fw.context_menu_item;

SELECT id, label, icon, scope, applies_to_kind, action_kind, action_params, core_id
FROM fw.context_menu_item
ORDER BY id;

-- Verify FK constraint
SELECT conname, confrelid::regclass AS references
FROM pg_constraint
WHERE conrelid = 'fw.context_menu_item'::regclass
  AND contype = 'f';
