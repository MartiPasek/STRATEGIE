-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.M (17.5.2026):
-- UPDATE fw.data_set framework_data_sets_select.sql_text
-- ════════════════════════════════════════════════════════════════════════
-- Po Krok 5.M ALTER fw.data_set:
--   - SLOUPEC db_connection (VARCHAR) DROPPED
--   - NOVÝ SLOUPEC db_connection_id (BIGINT FK)
--
-- Současný sql_text `SELECT * FROM fw.data_set` po ALTER vrací
-- db_connection_id (BIGINT) místo db_connection (string code).
-- Grid framework_data_sets má `field: "db_connection"` (od Krok 5.L-D),
-- který je teď prázdný → cosmetic empty cell.
--
-- Fix: JOIN fw.db_connection + alias `dc.code AS db_connection`.
-- Plus přidat db_connection_id (FK) a db_connection_label pro budoucí UI.
--
-- Marti's pattern z 17.5. večer — backward compat strategy: backend
-- aliasuje `dc.code AS db_connection`, frontend grid + DesignDataSetEditor
-- zatím beze změny, refactor optgroup později.
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.data_set
SET sql_text = $sql$
SELECT ds.*,
       dc.default_db AS db_connection,
       dc.code       AS db_connection_code,
       dc.label      AS db_connection_label
FROM fw.data_set ds
LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
ORDER BY ds.id
LIMIT :limit
$sql$
WHERE code = 'framework_data_sets_select';

-- VERIFY 1 row updated
DO $$
DECLARE
    updated_count INT;
BEGIN
    SELECT COUNT(*) INTO updated_count FROM fw.data_set
    WHERE code = 'framework_data_sets_select'
      AND sql_text LIKE '%dc.default_db AS db_connection%';
    IF updated_count != 1 THEN
        RAISE EXCEPTION 'Expected 1 row updated, got %', updated_count;
    END IF;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT id, code, LEFT(sql_text, 200) AS sql_preview
FROM fw.data_set
WHERE code = 'framework_data_sets_select';
-- Expected: sql_preview obsahuje "LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id"

-- Test runtime: spustit SQL ručně + ověřit že vrací db_connection string
SELECT ds.id, ds.code, ds.db_connection_id,
       dc.default_db AS db_connection,
       dc.code       AS db_connection_code,
       dc.label      AS db_connection_label
FROM fw.data_set ds
LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
ORDER BY ds.id
LIMIT 20;
-- Expected: 13 rows, db_connection vyplněno:
--   12× 'data_db'  → db_connection_code='strategie_pg'   (rows 1-11, 13)
--    1× 'DB_EC'    → db_connection_code='eurosoft_db_ec' (row 12)
