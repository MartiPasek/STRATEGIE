-- ============================================================================
-- Krok H+2 — Polymorphic operation_kind: select + select-detail
-- ============================================================================
-- Marti's plan 26.5.2026 ranni:
--   Q1=A operation_kind='select-detail' (s pomlckou — UI display friendly)
--   Q2=A Rename existing op #33 (kind=select s :master_id) na 'select-detail'
--        Plus vytvorit novy op kind='select' bez :master_id (standalone)
--   Q3+Q4 deferred — Marti's "drz minimum + zkontrolovat co bezi a co nebezi"
--
-- Cil:
--   data_source #44 (framework_data_source_ops) bude mit DVA select-ish ops:
--     - kind='select'        → SQL bez :master_id (= standalone, vsechny ops)
--     - kind='select-detail' → SQL s :master_id  (= per-master, M-D nested)
--
-- Marti's doctrine "uniformita vitezi nad specialnimi pripady" (11.5. Krok 13):
--   Misto druheho data_source (Variant B z #533) = jeden data_source + polymorphic
--   operation_kind enum extension.
--
-- POZN: Tato changes NE-update backend dispatch (Q3) ani frontend wire-up (Q4).
--       Backend pravdepodobne default-uje na kind='select' → standalone SQL bez
--       :master_id → nested grid dostane VSECHNY ops (ne per-master).
--       Marti to chce explicit vidi — pak Q3+Q4 v dalsi iteraci.
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ── Step 1: Pre-state — fw.data_source #44 + ops + data_sets ──────────────
SELECT '=== Step 1: PRE-STATE ===' AS section;

SELECT
    op.id AS op_id,
    op.operation_kind,
    op.variant_code,
    op.data_set_id,
    op.is_default,
    op.description,
    ds.code AS data_set_code,
    ds.db_connection_id
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE op.data_source_id = 44
ORDER BY op.id;
-- Expected: 1 row (op #33, kind=select, data_set_id=32)

-- ── Step 2: Rename existing op #33 → 'select-detail' ──────────────────────
SELECT '=== Step 2: RENAME op #33 → select-detail ===' AS section;

UPDATE fw.data_source_op
SET operation_kind = 'select-detail',
    description    = 'Per-master detail (M-D vazba). SQL filter WHERE data_source_id = :master_id.'
WHERE id = 33;
-- Expected: UPDATE 1


-- ── Step 3: Vytvor novy data_set bez :master_id filter (standalone) ────────
SELECT '=== Step 3: INSERT new data_set (standalone, no :master_id) ===' AS section;

INSERT INTO fw.data_set (
    code,
    name,
    description,
    sql_text,
    db_connection_id,
    status,
    created_by,
    updated_by
)
SELECT
    'system_new.framework_data_source_ops_all',
    'Framework: Data Source Operations (vsechny)',
    'Standalone overview vsech ops napric vsemi data_sources. Pouzito kdyz '
        || 'kontext :master_id chybi (= soudecek otevren samostatne).',
    $$SELECT
    op.id,
    op.variant_code,
    op.operation_kind,
    op.sort_order,
    op.is_default,
    op.description,
    op.data_source_id,
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
    -- db_connection_id same jako existing data_set #32 (= data_db)
    (SELECT db_connection_id FROM fw.data_set WHERE id = 32),
    'active',
    2,
    2
RETURNING id, code, name;
-- Expected: 1 row → :new_data_set_id


-- ── Step 4: Vytvor novy op kind='select' linked na novy data_set ──────────
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
    'Standalone overview vsech ops (bez :master_id filter). Pouzito kdyz '
        || 'soudecek otevren samostatne v System tree.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = 44 AND operation_kind = 'select'
)
RETURNING id, operation_kind, data_set_id;
-- Expected: 1 row → :new_op_id


-- ── Step 5: POST-STATE verify ─────────────────────────────────────────────
SELECT '=== Step 5: POST-STATE ===' AS section;

SELECT
    op.id AS op_id,
    op.operation_kind,
    op.data_set_id,
    op.is_default,
    op.description,
    ds.code AS data_set_code,
    LENGTH(ds.sql_text) AS sql_chars,
    CASE WHEN ds.sql_text ILIKE '%:master_id%' THEN 'YES' ELSE 'no' END AS has_master_id_filter
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE op.data_source_id = 44
ORDER BY op.operation_kind;
-- Expected: 2 rows:
--   op_id=33  kind=select-detail  has_master_id_filter=YES (data_set #32 unchanged)
--   op_id=NEW kind=select         has_master_id_filter=no  (data_set #NEW)


-- ── Step 6: Smoke instructions ────────────────────────────────────────────
SELECT '=== Step 6: SMOKE TEST PLAN ===' AS section,
       '4 use cases k overeni po hard reload:'                              AS instruction_1,
       '1. Standalone soudecek "Data source operation" v System tree'      AS test_1,
       '   → MELO BY: zobrazit vsechny ops (driv prazdno!)'                AS expected_1,
       '   → backend default kind=select → standalone SQL bez :master_id'  AS reason_1,
       '2. Master-detail expand v Data Sources gridu (row #44)'            AS test_2,
       '   → CO BUDE: nested grid behavior — default kind=select?'         AS expected_2,
       '   → pravdepodobne: vrati VSECHNY ops (regression vs predtim)'     AS warning_2,
       '   → Q3+Q4 v dalsi iteraci: backend dispatch ?kind=select-detail'  AS fix_2,
       '3. Outer Data Sources grid'                                         AS test_3,
       '   → beze zmeny (master neni dotcen)'                              AS expected_3,
       '4. CRUD context menu v outer Data Sources'                          AS test_4,
       '   → beze zmeny (master neni dotcen)'                              AS expected_4;

COMMIT;
