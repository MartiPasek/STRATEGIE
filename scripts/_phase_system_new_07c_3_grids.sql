-- ============================================================
-- Phase SYSTEM NEW — Etapa 7c: 3 grids replicate
-- ============================================================
-- Datum: 21.5.2026 vecer (po Etapa 8 LIVE — stara Framework pryc)
-- Marti vybral 3 z 4 (bez „Datové zdroje" / Etapa 7b deferred):
--   - Přehled datasourců     → SELECT z fw.data_source + LEFT JOIN agg ops
--   - Knowledge Entries      → SELECT * z public.knowledge_entry
--   - Znalostní báze         → SELECT * z public.knowledge_topic
--
-- Pattern: identicky s Etapa 7 (8 INSERTs per grid, atomic BEGIN/COMMIT).
-- POZOR db_connection_id=1.
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 1/3: Přehled datasourců (z fw.data_source + agg)   ║
-- ╚══════════════════════════════════════════════════════════╝
-- Originální HC handler dělal LEFT JOIN GROUP BY na fw.data_source_op
-- (line 1383-1399 v router.py) — enriched view s op counts a kinds list.
-- MVP: zachovat ten pattern (na rozdíl od `Datové zdroje` který Marti
-- skipnul — ten by byl pure SELECT *).

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sources_overview', 'Přehled datasourců', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    400,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_data_sources_overview');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sources_overview', 'Přehled datasourců',
    'SYSTEM NEW Přehled datasourců: fw.data_source + LEFT JOIN GROUP BY ops aggregate',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_data_sources_overview');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sources_overview')
WHERE code = 'system_new.framework_data_sources_overview' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_data_sources_overview', 'Přehled datasourců',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_sources_overview'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_data_sources_overview');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_data_sources_overview',
    'Framework: Přehled datasourců',
    'SYSTEM NEW data_sources_overview data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview')
WHERE name = 'grid_system_new_framework_data_sources_overview' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_data_sources_overview',
    $sql$
SELECT
    s.*,
    COALESCE(op.cnt, 0) AS operation_count,
    op.kinds AS operation_kinds
FROM fw.data_source s
LEFT JOIN (
    SELECT
        data_source_id,
        COUNT(*) AS cnt,
        STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
    FROM fw.data_source_op
    GROUP BY data_source_id
) op ON op.data_source_id = s.id
ORDER BY s.id
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW Přehled datasourců: enriched view s op counts (zachovava HC pattern)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_data_sources_overview');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_data_sources_overview'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_data_sources_overview default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_data_sources_overview')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_data_sources_overview' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 2/3: Knowledge Entries (z public.knowledge_entry)  ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_entries', 'Knowledge Entries', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    500,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_knowledge_entries');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_entries', 'Knowledge Entries',
    'SYSTEM NEW Knowledge Entries: SELECT * z public.knowledge_entry',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_knowledge_entries');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_knowledge_entries')
WHERE code = 'system_new.framework_knowledge_entries' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_knowledge_entries', 'Knowledge Entries',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_knowledge_entries'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_knowledge_entries');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_knowledge_entries',
    'Framework: Knowledge Entries',
    'SYSTEM NEW knowledge_entries data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_entries');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_knowledge_entries')
WHERE name = 'grid_system_new_framework_knowledge_entries' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_entries');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_knowledge_entries',
    $sql$
SELECT *
FROM public.knowledge_entry
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW Knowledge Entries: SELECT * z public.knowledge_entry (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_knowledge_entries');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_knowledge_entries'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_knowledge_entries'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_knowledge_entries default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_entries')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_knowledge_entries')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_knowledge_entries' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 3/3: Znalostní báze (z public.knowledge_topic)     ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_topics', 'Znalostní báze', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    600,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_knowledge_topics');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_topics', 'Znalostní báze',
    'SYSTEM NEW Znalostní báze: SELECT * z public.knowledge_topic',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_knowledge_topics');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_knowledge_topics')
WHERE code = 'system_new.framework_knowledge_topics' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_knowledge_topics', 'Znalostní báze',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_knowledge_topics'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_knowledge_topics');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_knowledge_topics',
    'Framework: Znalostní báze',
    'SYSTEM NEW knowledge_topics data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_topics');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_knowledge_topics')
WHERE name = 'grid_system_new_framework_knowledge_topics' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_topics');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_knowledge_topics',
    $sql$
SELECT *
FROM public.knowledge_topic
ORDER BY id
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW Znalostní báze: SELECT * z public.knowledge_topic (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_knowledge_topics');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_knowledge_topics'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_knowledge_topics'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_knowledge_topics default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_knowledge_topics')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_knowledge_topics')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_knowledge_topics' AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system_new.framework%';

    RAISE NOTICE '╔════ POST-CHECK Framework (5/5 expected) ════╗';
    RAISE NOTICE '║ menu_node       = % (folder + 4 grids = 5)   ║', v_menu;
    RAISE NOTICE '║ data_source     = % (4 grids)               ║', v_ds;
    RAISE NOTICE '║ data_set        = % (4)                     ║', v_dset;
    RAISE NOTICE '║ data_source_op  = % (4)                     ║', v_dso;
    RAISE NOTICE '╚══════════════════════════════════════════════╝';

    IF v_menu >= 5 AND v_ds >= 4 AND v_dset >= 4 AND v_dso >= 4 THEN
        RAISE NOTICE 'SUCCESS: SYSTEM NEW Framework kompletni 4/4 grids:';
        RAISE NOTICE '  ├── DataSets                 (Etapa 7)';
        RAISE NOTICE '  ├── Definice levého stromu   (Etapa 7)';
        RAISE NOTICE '  ├── Přehled datasourců       (Etapa 7c) ← NEW';
        RAISE NOTICE '  ├── Knowledge Entries        (Etapa 7c) ← NEW';
        RAISE NOTICE '  └── Znalostní báze           (Etapa 7c) ← NEW';
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
--   Hard reload → SYSTEM NEW → Framework → 5 polozek
--   (folder + 4 grids: DataSets/Definice/Přehled datasourců/Knowledge/Znalostní)
--
--   Marti's NOTE: Datové zdroje (system_new.framework_data_sources)
--   Etapa 7b NEBYLA spustena — Marti's volba. Pokud zmeni:
--   spustit `_phase_system_new_07b_framework_data_sources.sql`.
-- ============================================================
