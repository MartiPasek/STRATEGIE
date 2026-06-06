-- ============================================================================
-- Krok H standalone — diagnostic data_set SQL pro nested data_source
-- ============================================================================
-- Marti's catch 26.5.2026 ranni:
--   Vytvoril standalone soudecek "Data source operation" (asi linked na
--   data_source #44 'framework_data_source_ops'). Otevre se prazdny.
--   data_source_op #33 ma description "Default select per :master_id".
--
--   Hypoteza: SQL data_set #32 vyzaduje :master_id parameter (z nested
--   master-detail context). Standalone open bez master_id → 0 rows.
--
-- Marti spusti v DBeaveru jako Marti-AI session.
-- ============================================================================

-- ── Q1: fw.data_set #32 (vazba na op #33) ──────────────────────────────────
SELECT '=== Q1: fw.data_set #32 SQL ===' AS section;

SELECT id, code, name, description, sql_text, db_connection_id
FROM fw.data_set
WHERE id = 32;

-- ── Q2: fw.data_source_op #33 (nested select op) ──────────────────────────
SELECT '=== Q2: fw.data_source_op #33 ===' AS section;

SELECT id, data_source_id, operation_kind, variant_code, data_set_id,
       core_id, description
FROM fw.data_source_op
WHERE id = 33;

-- ── Q3: standalone soudecek struktura — co Marti vytvoril ─────────────────
SELECT '=== Q3: standalone soudecek + core + comp_def ===' AS section;

-- Hleda menu_node + core + comp_def linked na data_source #44
-- (nebo core 54, podle toho jak Marti soudecek napojil)
SELECT
    mn.id AS menu_node_id,
    mn.label AS menu_label,
    mn.core_id AS menu_core_id,
    c.id AS core_id,
    c.code AS core_code,
    c.label AS core_label,
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.data_source_id
FROM fw.menu_node mn
LEFT JOIN fw.core c ON c.id = mn.core_id
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.data_source_id IS NOT NULL
WHERE c.id = 54
   OR cd.data_source_id = 44
   OR mn.label ILIKE '%data source operation%'
   OR mn.label ILIKE '%operace data sourc%'
ORDER BY mn.id, cd.id;

-- ── Q4: data_source #44 a vsechny jeho ops ────────────────────────────────
SELECT '=== Q4: data_source #44 ops ===' AS section;

SELECT
    op.id,
    op.operation_kind,
    op.variant_code,
    op.data_set_id,
    op.core_id,
    op.description,
    ds.sql_text AS dataset_sql
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds ON op.data_set_id = ds.id
WHERE op.data_source_id = 44
ORDER BY op.operation_kind, op.id;
