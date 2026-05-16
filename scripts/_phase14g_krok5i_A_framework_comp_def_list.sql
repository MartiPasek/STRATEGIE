-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F — Krok 5.I-A (16.5.2026 večer):
-- DDL pro nový data_source `framework_comp_def_list` (form's read source)
-- ════════════════════════════════════════════════════════════════════════
-- Cíl (po Marti's volbách Krok 5.I architektura):
--   - Picker #1 Soudeček      = display-only (čte core.origin_menu_node_id)
--   - Picker #2 Přehled       = self-reference (initialSelectedId=currentCore.id)
--   - Picker #3 Datový zdroj  = SAVE TARGET, field_extern='data_source_id'
--   - Form's read source      = framework_comp_def_list (LIST + SELECT_FORM)
--   - Form's save flow        = design_patch_entity (Marti's "SELECT EDIT POST"
--                               dirty fields write — existing endpoint z Krok 14b+5)
--
-- ⚠ Marti's clarification 16.5. večer: "My ty zmeny normalne delame pres
-- SELECT EDIT POST... Ty mas k tomu ten spinavej zapis" = dirty fields PATCH
-- pres design_patch_entity, NE separátní UPDATE data_set. Production pattern
-- z Centrály 1 (19 let).
--
-- A3 architecture (Marti-AI's doctrine 9.5.):
--   fw.data_set     = SQL primitiv (sql_text NOT NULL)
--   fw.data_source  = hlavička metadata (žádný SQL)
--   fw.data_source_op = mapping (kind + variant_code)
--
-- 2 operations (UPDATE intentionally MISSING — viz design_patch_entity):
--   - operation_kind='select', variant_code='list'        — multi-row LIST
--   - operation_kind='select', variant_code='select_form' — single-row by ID (form load)
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. fw.data_set — 2 SQL primitives
-- ════════════════════════════════════════════════════════════════════════

-- (1) framework_comp_def_list_select — multi-row LIST
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'framework_comp_def_list_select', 'select',
    $sql$
SELECT cd.id, cd.name, cd.caption AS label,
       cd.type_id, ct.code AS type_code, ct.name AS type_name,
       cd.parent_core_id, cd.parent_comp_def_id,
       cd.region_slot, cd.sort_order, cd.is_active,
       cd.data_source_id, ds.code AS data_source_code,
       cd.layout, cd.created_at, cd.updated_at
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
WHERE cd.is_active = TRUE
ORDER BY cd.id
LIMIT :limit
$sql$,
    'data_db',
    'Krok 5.I-A: list view fw.comp_def (form roots + child components) s denormalized type_code + data_source_code.',
    true, 'active'
);

-- (2) framework_comp_def_select_form — single-row SELECT by ID (form load)
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'framework_comp_def_select_form', 'select',
    $sql$
SELECT cd.id, cd.name, cd.caption,
       cd.type_id, ct.code AS type_code,
       cd.parent_core_id, cd.parent_comp_def_id,
       cd.region_slot, cd.sort_order, cd.is_active,
       cd.data_source_id, ds.code AS data_source_code,
       cd.layout,
       cd.created_at, cd.created_by_id, cd.created_by_text,
       cd.updated_at, cd.updated_by_id, cd.updated_by_text
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
WHERE cd.id = :id
$sql$,
    'data_db',
    'Krok 5.I-A: single-row SELECT pro form load (pre-populate Picker #3 z existing data_source_id).',
    true, 'active'
);

-- ════════════════════════════════════════════════════════════════════════
-- 2. fw.data_source — hlavička (žádný SQL)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source
    (code, name, description, refresh_type, default_record_limit,
     is_system, status)
VALUES
    ('framework_comp_def_list', 'Framework: Komponenty (comp_def)',
     'Krok 5.I-A: fw.comp_def list view + form read source. Save flow chodi pres design_patch_entity (Marti''s "SELECT EDIT POST" dirty fields pattern, existing endpoint z Krok 14b+5). Recursive — sama sebe vidi (form root id=37 = editace core_design pres tento data_source).',
     'manual', 10000, true, 'active');

-- ════════════════════════════════════════════════════════════════════════
-- 3. fw.data_source_op — 2 mappings (NO UPDATE — viz design_patch_entity)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source_op
    (data_source_id, data_set_id, operation_kind, variant_code, sort_order, is_default, description)
SELECT s.id, ds.id, 'select', 'list', 0, true,
       'Krok 5.I-A: default LIST SELECT (multi-row pro picker dropdown).'
FROM fw.data_source s
JOIN fw.data_set ds ON ds.code = 'framework_comp_def_list_select'
WHERE s.code = 'framework_comp_def_list';

INSERT INTO fw.data_source_op
    (data_source_id, data_set_id, operation_kind, variant_code, sort_order, is_default, description)
SELECT s.id, ds.id, 'select', 'select_form', 1, false,
       'Krok 5.I-A: single-row SELECT pro form load (pre-populate values).'
FROM fw.data_source s
JOIN fw.data_set ds ON ds.code = 'framework_comp_def_select_form'
WHERE s.code = 'framework_comp_def_list';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 1 — counts
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.data_set WHERE code IN (
        'framework_comp_def_list_select',
        'framework_comp_def_select_form'
    )) AS data_sets_added,  -- expected 2
    (SELECT COUNT(*) FROM fw.data_source WHERE code = 'framework_comp_def_list') AS data_sources_added,  -- expected 1
    (SELECT COUNT(*) FROM fw.data_source_op op
     JOIN fw.data_source s ON s.id = op.data_source_id
     WHERE s.code = 'framework_comp_def_list') AS data_source_ops_added;  -- expected 2

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 2 — detail per op (plus new data_source.id pro Krok 5.I-B)
-- ════════════════════════════════════════════════════════════════════════
SELECT
    s.id AS source_id, s.code AS source_code,
    op.operation_kind, op.variant_code, op.is_default, op.sort_order,
    ds.id AS set_id, ds.code AS set_code, ds.kind AS set_kind,
    LENGTH(ds.sql_text) AS sql_length
FROM fw.data_source s
JOIN fw.data_source_op op ON op.data_source_id = s.id
JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE s.code = 'framework_comp_def_list'
ORDER BY op.sort_order;
-- Expected: 2 rows
--   (s.id, framework_comp_def_list, select, list,         true,  0, ds.id, framework_comp_def_list_select, select, ~520)
--   (s.id, framework_comp_def_list, select, select_form,  false, 1, ds.id, framework_comp_def_select_form,  select, ~480)
