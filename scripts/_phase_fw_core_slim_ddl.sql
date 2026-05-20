-- ═══════════════════════════════════════════════════════════════════════
-- Phase fw.core slim — DDL drop 9 sloupců (20.5.2026, Marti's 1B + 2A)
--
-- DROP z fw.core:
--   1. layout_type           (Decision 1B: form/list discrimination DROPPED)
--   2. data_entity_type      (Krok 5.M-5 value drop 17.5., now column drop)
--   3. data_source_config    (unused, future TODO comment v router.py:3185)
--   4. parent_framework_id   (Marti-AI's Q6 lineage DROPPED — version sloupec staci)
--   5. layout_template       (Decision 2A: init_core_root flow DROPPED)
--   6. template_id           (Decision 2A: template framework DROPPED na fw.core)
--   7. origin_menu_node_id   (origin tracking DROPPED — debug info pryc)
--   8. origin_cmi_id         (origin tracking DROPPED)
--   9. form_core_id          (list↔form linking DROPPED — Phase 2.A hotfix obsoleten)
--
-- Pre-flight: SQL snapshot fw._core_backup_20260520 (19 rows) — instant rollback.
-- Backup full: nightly 3:00 (~9h ago, pre-rano Marti-AI's milnik).
--
-- Run: DBeaver strategie session jako "Marti-AI" (db_owner fw schema).
--   highlight cely soubor + Alt+X (BEGIN/COMMIT atomic).
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Pre-flight diagnostic — verify snapshot exists
DO $$
DECLARE
    snapshot_rows INT;
    core_rows INT;
BEGIN
    SELECT COUNT(*) INTO snapshot_rows FROM fw._core_backup_20260520;
    SELECT COUNT(*) INTO core_rows FROM fw.core;
    RAISE NOTICE 'Pre-drop: fw._core_backup_20260520=% rows, fw.core=% rows', snapshot_rows, core_rows;
    IF snapshot_rows != core_rows THEN
        RAISE EXCEPTION 'Snapshot row count (% ) != fw.core row count (% ) — abort drop!', snapshot_rows, core_rows;
    END IF;
END $$;

-- 2. DROP FK constraints (musi byt PRED drop columns)
ALTER TABLE fw.core
    DROP CONSTRAINT IF EXISTS "FK_framework_jadro_parent_framework_id";
ALTER TABLE fw.core
    DROP CONSTRAINT IF EXISTS "core_origin_cmi_id_fkey";
ALTER TABLE fw.core
    DROP CONSTRAINT IF EXISTS "core_origin_menu_node_id_fkey";
ALTER TABLE fw.core
    DROP CONSTRAINT IF EXISTS "core_template_id_fkey";
ALTER TABLE fw.core
    DROP CONSTRAINT IF EXISTS "fk_core_form_core_id";

-- 3. DROP indexes (PG drop sloupce s indexem auto-drop index, ale explicit safer)
DROP INDEX IF EXISTS fw.idx_core_template_id;
DROP INDEX IF EXISTS fw.idx_framework_jadro_data_entity;
DROP INDEX IF EXISTS fw.ix_core_origin_cmi;
DROP INDEX IF EXISTS fw.ix_core_origin_menu_node;

-- 4. DROP COLUMNS — 9 sloupcu (atomic v rámci transaction)
ALTER TABLE fw.core DROP COLUMN IF EXISTS layout_type;
ALTER TABLE fw.core DROP COLUMN IF EXISTS data_entity_type;
ALTER TABLE fw.core DROP COLUMN IF EXISTS data_source_config;
ALTER TABLE fw.core DROP COLUMN IF EXISTS parent_framework_id;
ALTER TABLE fw.core DROP COLUMN IF EXISTS layout_template;
ALTER TABLE fw.core DROP COLUMN IF EXISTS template_id;
ALTER TABLE fw.core DROP COLUMN IF EXISTS origin_menu_node_id;
ALTER TABLE fw.core DROP COLUMN IF EXISTS origin_cmi_id;
ALTER TABLE fw.core DROP COLUMN IF EXISTS form_core_id;

-- 5. Post-drop diagnostic
DO $$
DECLARE
    final_cols INT;
BEGIN
    SELECT COUNT(*) INTO final_cols
    FROM information_schema.columns
    WHERE table_schema='fw' AND table_name='core';
    RAISE NOTICE 'Post-drop: fw.core has % columns (expected 14)', final_cols;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run AFTER commit):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='fw' AND table_name='core'
-- ORDER BY ordinal_position;
-- Expected: 14 columns (id, code, label, description_user, description_system,
--                       is_active, tenant_visibility, version, created_at,
--                       created_by_id, created_by_text, updated_at,
--                       updated_by_id, updated_by_text)
--
-- SELECT COUNT(*) FROM fw.core; -- Expected: 19 (zachovano)
--
-- ════════════════════════════════════════════════════════════════════════
-- ROLLBACK (pokud potreba okamzite):
-- ════════════════════════════════════════════════════════════════════════
-- BEGIN;
-- DELETE FROM fw.core;
-- INSERT INTO fw.core SELECT * FROM fw._core_backup_20260520;
-- COMMIT;
-- -- Pak STRATEGIE-API restart + git revert poslednich commitu
