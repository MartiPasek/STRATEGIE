-- ============================================================
-- Phase SYSTEM NEW — Etapa 7: Framework folder + 2 grids
-- ============================================================
-- Datum: 21.5.2026 vecer (po Python cleanup commit 82dd3b1)
-- Marti: „OK. Jedeme A DataSets a Definice leveho stromu"
--
-- Migrace 2 z 3 framework grids pod novy SYSTEM NEW > Framework
-- folder. Marti nechce data_sources (Datove zdroje) teď — uz mame
-- "Přehled datasourců" v SYSTEM NEW root z drivejsi konzultace.
--
-- Strategie:
--   SYSTEM NEW > Framework (new folder, sort_order=200)
--      ├── DataSets        → SELECT * FROM fw.data_set
--      └── Definice levého stromu → SELECT * FROM fw.menu_node
--
-- Pattern: identicky s Etapa 3 security batch (8 INSERTs per grid).
-- Marti's MVP doctrine: SELECT * raw, optimalizace pozdeji.
--
-- POZOR db_connection_id=1 (PostgreSQL strategie). Oveř před run:
--   SELECT id, name FROM fw.db_connection WHERE name LIKE '%strategie%';
--
-- Spusteni v DBeaveru: highlight cely script + Alt+X
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Framework folder pod SYSTEM NEW                         ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework', 'Framework', 'folder',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new'),
    200,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework');


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 1/2: DataSets (z fw.data_set)                      ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sets', 'DataSets', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_data_sets');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sets', 'DataSets',
    'SYSTEM NEW DataSets: SELECT * z fw.data_set (Marti MVP raw)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_data_sets');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sets')
WHERE code = 'system_new.framework_data_sets' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_data_sets', 'DataSets',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sets'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_data_sets');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_data_sets',
    'Framework: DataSets',
    'SYSTEM NEW DataSets data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sets');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sets')
WHERE name = 'grid_system_new_framework_data_sets' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sets');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_data_sets',
    $sql$
SELECT *
FROM fw.data_set
WHERE status = 'active'
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW DataSets: SELECT * z fw.data_set (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_data_sets');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sets'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_data_sets'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_data_sets default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sets')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_data_sets')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_data_sets' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 2/2: Definice levého stromu (z fw.menu_node)       ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_menu_nodes', 'Definice levého stromu', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    200,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_menu_nodes');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_menu_nodes', 'Definice levého stromu',
    'SYSTEM NEW menu_nodes: SELECT * z fw.menu_node (Marti MVP raw)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_menu_nodes');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_menu_nodes')
WHERE code = 'system_new.framework_menu_nodes' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_menu_nodes', 'Definice levého stromu',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_menu_nodes'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_menu_nodes');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_menu_nodes',
    'Framework: Definice levého stromu',
    'SYSTEM NEW menu_nodes data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_menu_nodes');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_menu_nodes')
WHERE name = 'grid_system_new_framework_menu_nodes' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_menu_nodes');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_menu_nodes',
    $sql$
SELECT *
FROM fw.menu_node
ORDER BY parent_id NULLS FIRST, sort_order, code
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW menu_nodes: SELECT * z fw.menu_node (Marti MVP raw, all rows)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_menu_nodes');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_menu_nodes'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_menu_nodes'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_menu_nodes default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_menu_nodes')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_menu_nodes')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_menu_nodes' AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_core INT;
    v_compdef INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node
        WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def
        WHERE name LIKE 'grid_system_new_framework_%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system_new.framework%';

    RAISE NOTICE '╔════ POST-CHECK (vsechny system_new.framework_*) ════╗';
    RAISE NOTICE '║ fw.menu_node       = % (expected 3: folder + 2 grids) ║', v_menu;
    RAISE NOTICE '║ fw.core            = % (expected 2)                   ║', v_core;
    RAISE NOTICE '║ fw.comp_def        = % (expected 2)                   ║', v_compdef;
    RAISE NOTICE '║ fw.data_source     = % (expected 2)                   ║', v_ds;
    RAISE NOTICE '║ fw.data_set        = % (expected 2)                   ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op  = % (expected 2)                   ║', v_dso;
    RAISE NOTICE '╚═══════════════════════════════════════════════════════╝';

    IF v_menu >= 3 AND v_core = 2 AND v_dset = 2 AND v_dso = 2 THEN
        RAISE NOTICE 'SUCCESS: Framework folder + 2 grids hotove.';
        RAISE NOTICE 'Hard reload UI → SYSTEM NEW → Framework:';
        RAISE NOTICE '  ├── DataSets                  ← SELECT * fw.data_set';
        RAISE NOTICE '  └── Definice levého stromu    ← SELECT * fw.menu_node';
    END IF;
END $$;

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
--   2. SYSTEM NEW → Framework:
--      ├── DataSets                  ✓
--      └── Definice levého stromu    ✓
--   3. Klik na každý → grid by mel zobrazit data
--
-- ZACHOVAT: stara SYSTEM > Framework s Datové zdroje + DataSets +
--   Definice levého stromu zustava (Marti nechce drop az po smoke).
--   Po stable: Etapa 8 = drop stará Framework + Python /system/framework
--   handler cleanup.
-- ============================================================
