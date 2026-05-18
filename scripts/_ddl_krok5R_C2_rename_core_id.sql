-- Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer) — DDL pro Marti's DBeaver
-- Run as Marti-AI session (db_owner fw schema).
--
-- Marti's doctrine: "PREHLED CISLO MUSI UPLNE ZMIZET... Je dobre smazat
-- i vsechny ty sestavy z EUROSOFTU, ktere tam jsou integrovane..."
--
-- 4 kroky:
--   1) DELETE FROM erp_grid_layouts;  (clean slate, Marti's mandate)
--   2) ALTER TABLE erp_grid_layouts RENAME COLUMN prehled_cislo TO core_id;
--   3) Drop dead schema z dnesniho rana 5.R-C+1:
--      DROP TABLE fw.comp_grid_column CASCADE;
--      DROP TABLE fw.comp_grid_master CASCADE;
--   4) (volitelne) Verify final state.

-- ════════════════════════════════════════════════════════════════════════════
-- Step 1: Clean slate erp_grid_layouts (vsechny existing sestavy)
-- Marti's mandate "smazat i vsechny ty sestavy z EUROSOFTU"
-- ════════════════════════════════════════════════════════════════════════════

-- Volitelny backup pred delete (pokud Marti chce):
-- CREATE TABLE erp_grid_layouts_backup_5R_C2 AS SELECT * FROM erp_grid_layouts;
-- SELECT 'backed up rows: ' || COUNT(*) FROM erp_grid_layouts_backup_5R_C2;

DELETE FROM erp_grid_layouts;
-- (optional analog pro formatting rules pokud existuji)
-- DELETE FROM erp_grid_formatting_rule;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 2: Rename sloupec prehled_cislo → core_id
-- (Drop Centrala 1 reference, neutralni scope key)
-- ════════════════════════════════════════════════════════════════════════════

ALTER TABLE erp_grid_layouts RENAME COLUMN prehled_cislo TO core_id;

-- Drop existing indexy/constraints na prehled_cislo a recreate na core_id?
-- Postgres ALTER RENAME automaticky updatne foreign keys, partial indexes
-- (ux_default_per_scope, ux_personal_per_user_scope) — verify:

\d erp_grid_layouts;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 3: Drop dead schema z 5.R-C+1 (rano)
-- fw.comp_grid_master + fw.comp_grid_column tables — Marti-AI db_owner
-- Drop CASCADE = drop indexy + child fw.comp_grid_column FK
-- ════════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS fw.comp_grid_column CASCADE;
DROP TABLE IF EXISTS fw.comp_grid_master CASCADE;

-- Verify drop:
SELECT table_name
  FROM information_schema.tables
 WHERE table_schema = 'fw' AND table_name LIKE 'comp_grid_%';
-- Ocekavany vystup: 0 rows

-- ════════════════════════════════════════════════════════════════════════════
-- Step 4: Final verify
-- ════════════════════════════════════════════════════════════════════════════

-- erp_grid_layouts should have 0 rows + core_id column:
SELECT COUNT(*) AS row_count FROM erp_grid_layouts;
\d erp_grid_layouts;

-- ════════════════════════════════════════════════════════════════════════════
-- DONE. Run sequence:
--   1. SELECT-only audit (kolik rows zmizi):
--      SELECT COUNT(*), array_agg(DISTINCT prehled_cislo) FROM erp_grid_layouts;
--   2. (volitelny backup)
--   3. Execute step 1-4
--   4. Restart-Service STRATEGIE-API
-- ════════════════════════════════════════════════════════════════════════════
