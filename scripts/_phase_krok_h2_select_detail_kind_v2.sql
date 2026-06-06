-- ============================================================================
-- Krok H+2 v2 — Polymorphic operation_kind: select + select-detail
-- ============================================================================
-- Marti's plan 26.5.2026 ranni + schema introspection clarified:
--   Q1=A operation_kind='select-detail' (s pomlckou)
--   Q2=A Rename existing op #33 + INSERT new op 'select' bez :master_id
--   Q3+Q4 deferred — "drz minimum, zkontrolovat co bezi"
--
-- v2 fixes (po data_set introspection):
--   - DROP 'name' column (neexistuje)
--   - Keep jen: code, description, sql_text, db_connection_id, version,
--     parameters, status, is_system, is_immutable, created_by/updated_by
--   - Pattern mirror existing #32 (Marti's data_set audit pattern: NULL by)
--
-- Cil:
--   data_source #44 (framework_data_source_ops):
--     - op kind='select'        → SQL bez :master_id (standalone, vsechny ops)
--     - op kind='select-detail' → SQL s :master_id  (per-master, M-D nested)
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ── Step 1: Pre-state (skip diag — known z prev SELECT) ───────────────────
SELECT '=== Step 1: PRE-STATE ===' AS section;

SELECT op.id, op.operation_kind, op.data_set_id, op.description
FROM fw.data_source_op op
WHERE op.data_source_id = 44
ORDER BY op.id;
-- Expected: 1 row (op #33, kind='select', data_set_id=32)


-- ── Step 2: RENAME op #33 → kind='select-detail' ──────────────────────────
SELECT '=== Step 2: RENAME op #33 → select-detail ===' AS section;

UPDATE fw.data_source_op
SET operation_kind = 'select-detail',
    description    = 'Per-master detail (M-D vazba). SQL filter WHERE data_source_id = :master_id.'
WHERE id = 33;


-- ── Step 3: INSERT new data_set (standalone, no :master_id filter) ────────
SELECT '=== Step 3: INSERT new data_set (standalone) ===' AS section;

INSERT INTO fw.data_set (
    code,
    version,
    description,
    sql_text,
    parameters,
    is_system,
    is_immutable,
    status,
    db_connection_id,
    created_by,
    updated_by
)
SELECT
    'system_new.framework_data_source_ops_all',
    1,
    'Standalone overview vsech ops napric vsemi data_sources (bez :master_id).',
    $$SELECT
    op.id,
    op.data_source_id,
    op.variant_code,
    op.operation_kind,
    op.sort_order,
    op.is_default,
    op.description,
    op.core_id          AS op_core_id,
    ds.id               AS data_set_id,
    ds.code             AS data_set_code,
    ds.description      AS data_set_description,
    ds.status           AS data_set_status,
    dc.code             AS db_connection_code,
    dc.default_db       AS db_connection,
    src.code            AS data_source_code,
    src.name            AS data_source_name
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds        ON ds.id = op.data_set_id
LEFT JOIN fw.db_connection dc   ON dc.id = ds.db_connection_id
LEFT JOIN fw.data_source src    ON src.id = op.data_source_id
ORDER BY op.data_source_id, op.sort_order ASC, op.id ASC$$,
    NULL,           -- parameters
    TRUE,           -- is_system (mirror #32)
    FALSE,          -- is_immutable
    'active',
    1,              -- db_connection_id (inherit z #32 = data_db)
    NULL,           -- created_by (mirror #32 NULL pattern)
    NULL            -- updated_by
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_set
    WHERE code = 'system_new.framework_data_source_ops_all'
)
RETURNING id, code, status;


-- ── Step 4: INSERT new op kind='select' linked na novy data_set ───────────
SELECT '=== Step 4: INSERT new op kind=select (standalone) ===' AS section;

INSERT INTO fw.data_source_op (
    data_source_id,
    operation_kind,
    variant_code,
    data_set_id,
    is_default,
    sort_order,
    description
)
SELECT
    44,
    'select',
    'default',
    (SELECT id FROM fw.data_set WHERE code = 'system_new.framework_data_source_ops_all'),
    TRUE,
    0,
    'Standalone overview vsech ops (bez :master_id). Pouzito kdyz soudecek otevren samostatne.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = 44 AND operation_kind = 'select'
)
RETURNING id, operation_kind, data_set_id;


-- ── Step 5: POST-STATE verify ─────────────────────────────────────────────
SELECT '=== Step 5: POST-STATE ===' AS section;

SELECT
    op.id AS op_id,
    op.operation_kind,
    op.data_set_id,
    op.is_default,
    op.description,
    ds.code AS data_set_code,
    CASE WHEN ds.sql_text ILIKE '%:master_id%' THEN 'YES' ELSE 'no' END AS has_master_id_filter,
    LENGTH(ds.sql_text) AS sql_chars
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE op.data_source_id = 44
ORDER BY op.operation_kind;
-- Expected: 2 rows:
--   op_id=33    kind=select-detail  has_master_id_filter=YES  (data_set #32)
--   op_id=NEW   kind=select         has_master_id_filter=no   (data_set NEW)

COMMIT;


-- ── Step 6: Smoke test plan po hard reload ────────────────────────────────
SELECT '=== Step 6: SMOKE TEST PLAN ===' AS section,
       '1. Standalone soudecek "Data source operation" → MELO BY: vsechny ops vsech data_sources' AS test_1,
       '2. Master-detail expand v Data Sources gridu (row #44) → UVIDIME: regression?'             AS test_2,
       '3. Outer Data Sources grid → beze zmeny'                                                    AS test_3,
       '4. CRUD context menu outer → beze zmeny'                                                    AS test_4;
