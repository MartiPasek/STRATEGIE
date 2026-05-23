-- ============================================================
-- Phase SYSTEM NEW — Etapa 7b: Framework data_sources grid
-- ============================================================
-- Datum: 21.5.2026 vecer (po Etapa 7 LIVE — DataSets + Definice)
-- Marti: „Aktivni a + Datovy zdroj" — chce 3. grid v SYSTEM NEW
-- Framework: Datové zdroje (z fw.data_source).
--
-- „Pozor jsou tam dve pilulky..." (Marti's catch) = ★ Aktivní + Vše
-- filter pills nad starym gridem (Sprint A 17.5.). Stejne UI features
-- v SYSTEM NEW grid pres frontend status filter widget (automatically
-- detected per status sloupec v data — ErpDataGrid Sprint A pattern).
--
-- Plus „+ Nový datový zdroj" button = ErpDataGrid Sprint D+ widget
-- (automatic on grids with insert variant_code op definition — pridame
-- pozdeji nebo dynamic z fw.data_source_op).
--
-- Tento script: jen create FW chain (8 INSERTs). Po smoke → Etapa 8
-- drop celou starou Framework (3 grids + folder + duplicates).
--
-- POZOR db_connection_id=1.
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 3/3: Datové zdroje (z fw.data_source)              ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sources', 'Datové zdroje', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    300,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_data_sources');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sources', 'Datové zdroje',
    'SYSTEM NEW Datové zdroje: SELECT * z fw.data_source (Marti MVP raw)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_data_sources');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sources')
WHERE code = 'system_new.framework_data_sources' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_data_sources', 'Datové zdroje',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sources'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_data_sources');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_data_sources',
    'Framework: Datové zdroje',
    'SYSTEM NEW data_sources data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sources')
WHERE name = 'grid_system_new_framework_data_sources' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_data_sources',
    $sql$
SELECT *
FROM fw.data_source
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW data_sources: SELECT * z fw.data_source (status filter pres UI pills)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_data_sources');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sources'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_data_sources'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_data_sources default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_data_sources')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_data_sources' AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE code = 'system_new.framework_data_sources';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE code = 'system_new.framework_data_sources';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.framework_data_sources';

    RAISE NOTICE '--- POST-CHECK Framework data_sources ---';
    RAISE NOTICE 'data_source=%, data_set=%, data_source_op=%', v_ds, v_dset, v_dso;

    IF v_ds = 1 AND v_dset = 1 AND v_dso = 1 THEN
        RAISE NOTICE 'SUCCESS: Framework 3/3 hotov.';
        RAISE NOTICE 'Hard reload UI → SYSTEM NEW → Framework:';
        RAISE NOTICE '  ├── DataSets                  (Etapa 7)';
        RAISE NOTICE '  ├── Definice levého stromu    (Etapa 7)';
        RAISE NOTICE '  └── Datové zdroje             (Etapa 7b) ← NEW';
        RAISE NOTICE '';
        RAISE NOTICE 'Pills + Nový button: ErpDataGrid Sprint A + D+ widgets';
        RAISE NOTICE 'detekuji status column + insert op automaticky.';
        RAISE NOTICE 'Pokud chybí, je to JS hardcoded toggle — fix separately.';
    END IF;
END $$;

-- VERIFY: all 4 system_new.framework rows
SELECT
    code,
    label,
    sort_order,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.framework%'
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   1. Hard reload UI
--   2. SYSTEM NEW → Framework → klik na „Datové zdroje"
--   3. Verify:
--      a) Grid zobrazi data (vsechny fw.data_source rows, vc. system_new.*)
--      b) Filter pills Aktivní/Archivované/Vše = pojistka kolik UI komponent
--         detekuje status column automaticky
--      c) „+ Nový datový zdroj" button = pojistka jestli detekuje insert op
--
--   POKUD pills nebo button chybí v novem gridu:
--      - To je JS hardcoded podpora pro stary HC code path
--      - Fix separately (drobnost — extract toggle do per-grid metadata)
--      - Marti rozhodne kdy
--
--   POZOR: V grid uvidíš self-reference (system_new.framework_data_sources
--   row mezi vsemi ostatnimi fw.data_source rows) — to je correct,
--   sebepopis konsistentnost. Pokud nechces, pridej WHERE filter pozdeji.
--
-- DALSI:
--   Po smoke OK → spustit Etapu 8 (drop stare Framework 3 grids + folder
--   + duplicates). Po Etape 8 + reload = stara SYSTEM > Framework pryc.
-- ============================================================
