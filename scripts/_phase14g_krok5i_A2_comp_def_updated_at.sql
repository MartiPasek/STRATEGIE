-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F — Krok 5.I-A2 (16.5.2026 večer):
-- ALTER fw.comp_def ADD COLUMN updated_at + trigger + backfill
-- ════════════════════════════════════════════════════════════════════════
-- Marti's volba A z 16.5. večer:
--   "Jasne A, jinak si nabijeme cumec"
-- 19yr doctrine "consistency napriec fw" — fw.core, fw.menu_node,
-- fw.comp_def_prop_override všechny mají updated_at + trigger, fw.comp_def
-- jako jediná chyběla.
--
-- 3-step postup (kvůli backfill `updated_at = created_at` pro existing rows):
--   1. ADD COLUMN updated_at TIMESTAMPTZ (nullable, no default)
--   2. UPDATE existing rows: SET updated_at = created_at
--   3. ALTER NOT NULL + SET DEFAULT NOW()
--   4. CREATE TRIGGER (reuse existing fw.update_updated_at())
--
-- Po této migraci:
--   - design_patch_entity optimistic lock přes expected_updated_at funguje
--   - Krok 5.I-A SQLs (framework_comp_def_list_select + select_form)
--     referencují cd.updated_at — teď budou OK runtime
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. ADD COLUMN (nullable, no default — neproti backfill loss)
ALTER TABLE fw.comp_def
    ADD COLUMN updated_at TIMESTAMPTZ;

-- 2. Backfill — historical consistency (existing rows dostanou created_at)
UPDATE fw.comp_def
SET updated_at = created_at
WHERE updated_at IS NULL;

-- 3. NOT NULL + DEFAULT NOW() (constraint enforce pro budoucí INSERTs)
ALTER TABLE fw.comp_def
    ALTER COLUMN updated_at SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT NOW();

-- 4. Trigger BEFORE UPDATE — auto-set updated_at = NOW() při každém UPDATE
CREATE TRIGGER trg_comp_def_updated_at
    BEFORE UPDATE ON fw.comp_def
    FOR EACH ROW EXECUTE FUNCTION fw.update_updated_at();

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 1 — column existuje s NOT NULL + DEFAULT NOW()
-- ════════════════════════════════════════════════════════════════════════
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='comp_def' AND column_name='updated_at';
-- Expected: updated_at / timestamp with time zone / NO / now()

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 2 — trigger registrovaný
-- ════════════════════════════════════════════════════════════════════════
SELECT trigger_name, event_manipulation, action_timing, action_statement
FROM information_schema.triggers
WHERE event_object_schema='fw'
  AND event_object_table='comp_def'
  AND trigger_name='trg_comp_def_updated_at';
-- Expected: 1 row, BEFORE UPDATE, EXECUTE FUNCTION fw.update_updated_at()

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 3 — backfill OK (updated_at = created_at pro existing rows)
-- ════════════════════════════════════════════════════════════════════════
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE updated_at IS NOT NULL) AS with_updated_at,
    COUNT(*) FILTER (WHERE updated_at = created_at) AS matching_created_at
FROM fw.comp_def;
-- Expected: total = with_updated_at = matching_created_at (všechny synchronized)

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 4 — trigger funguje (smoke test, NON-DESTRUCTIVE — touch row id=37)
-- ════════════════════════════════════════════════════════════════════════
SELECT id, created_at, updated_at,
       updated_at = created_at AS still_in_sync_pre_touch
FROM fw.comp_def WHERE id = 37;

-- Touch — UPDATE bez change v hodnotách, jen aby trigger fire
UPDATE fw.comp_def SET data_source_id = data_source_id WHERE id = 37;

SELECT id, created_at, updated_at,
       updated_at > created_at AS trigger_fired_correctly
FROM fw.comp_def WHERE id = 37;
-- Expected: trigger_fired_correctly = true (updated_at posunuto na NOW())
