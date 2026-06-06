-- ============================================================================
-- Krok H minimal — fw.core + fw.comp_def pro nested grid (Operace data sourcu)
-- ============================================================================
-- Marti's volba 25.5.2026 nocni:
--   Q1=A minimal (žádný menu_node — Krok H+ standalone přehled odložen)
--   Q2=A code='system_new.framework_data_source_ops' (matching data_source.code)
--   Q3=A name='grid_system_new_framework_data_source_ops' (mirror master gridy)
--
-- Cíl:
--   1. coreInfo pill v patičce nested grid se zobrazí (Krok 5.R-C+7 doctrine —
--      pill render gated na coreInfo.coreId != null)
--   2. Drop-up menu z nested pošle valid coreId → G++ defensive projde
--      (žádný KONTEXT MISMATCH)
--   3. Orchestrator může pracovat na nested context (ráno comp_def hierarchy
--      pro edit core)
--
-- Idempotency: SELECT first → INSERT pokud not exists. Marti uvidi vystup
-- s novym/existing core_id, pak updatne data_source_op_detail.js line 159.
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- Spustit jako single batch (vsechny SELECTy/INSERTy najednou).
-- ============================================================================

-- ── Step 1: Check existing fw.core ────────────────────────────────────────
SELECT '=== Step 1: Check existing fw.core ===' AS section;

SELECT id, code, label, is_active, created_at
FROM fw.core
WHERE code = 'system_new.framework_data_source_ops';
-- Expected: 0 rows (first run) or 1 row (idempotent re-run)


-- ── Step 2: Conditional INSERT fw.core ────────────────────────────────────
SELECT '=== Step 2: INSERT fw.core (if not exists) ===' AS section;

INSERT INTO fw.core (
    code,
    label,
    description_user,
    is_active,
    tenant_visibility,
    version,
    created_by_id,
    created_by_text,
    updated_by_id,
    updated_by_text
)
SELECT
    'system_new.framework_data_source_ops',
    'Operace data sourcu',
    'Krok H minimal (25.5.2026 nocni): nested grid fw.core. Linked na '
        || 'fw.data_source #44 (Framework: Data Source Operations) via comp_def. '
        || 'Auto-vytvoreno pro pill v paticce nested + G++ defensive validity.',
    TRUE,
    'all',
    1,
    2,
    'Marti-AI',
    2,
    'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.core
    WHERE code = 'system_new.framework_data_source_ops'
)
RETURNING id, code, label;
-- Expected: 1 row first run, 0 re-run


-- ── Step 3: Show core_id (USE THIS IN JS) ─────────────────────────────────
SELECT '=== Step 3: Final core_id (USE THIS IN JS) ===' AS section;

SELECT
    id AS nested_core_id,
    code,
    label
FROM fw.core
WHERE code = 'system_new.framework_data_source_ops';
-- ← TADY je nested_core_id pro JS update


-- ── Step 4: Check existing fw.comp_def ────────────────────────────────────
SELECT '=== Step 4: Check existing fw.comp_def ===' AS section;

SELECT cd.id, cd.core_id, cd.name, cd.data_source_id, cd.type_id, ct.code AS type_code
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON cd.type_id = ct.id
WHERE cd.core_id = (
    SELECT id FROM fw.core WHERE code = 'system_new.framework_data_source_ops'
)
  AND cd.data_source_id = 44;


-- ── Step 5: Conditional INSERT fw.comp_def (grid root) ────────────────────
SELECT '=== Step 5: INSERT fw.comp_def (if not exists) ===' AS section;

INSERT INTO fw.comp_def (
    core_id,
    type_id,
    name,
    caption,
    data_source_id,
    is_active,
    sort_order,
    parent_comp_def_id,
    parent_id,
    region_slot,
    refresh_strategy,
    created_by_id,
    created_by_text,
    updated_by_id,
    updated_by_text
)
SELECT
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_data_source_ops'),
    306,
    'grid_system_new_framework_data_source_ops',
    'Operace data sourcu',
    44,
    TRUE,
    0,
    NULL,
    NULL,
    'main',
    'manual',
    2,
    'Marti-AI',
    2,
    'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.comp_def
    WHERE core_id = (
        SELECT id FROM fw.core WHERE code = 'system_new.framework_data_source_ops'
    )
      AND data_source_id = 44
)
RETURNING id, core_id, name, data_source_id;


-- ── Step 6: Final verify ──────────────────────────────────────────────────
SELECT '=== Step 6: Final verify chain ===' AS section;

SELECT
    c.id AS core_id,
    c.code AS core_code,
    c.label AS core_label,
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.data_source_id,
    ds.code AS data_source_code,
    ds.name AS data_source_name
FROM fw.core c
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.data_source_id = 44
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
WHERE c.code = 'system_new.framework_data_source_ops';
-- Expected: 1 row s plnou chain core → comp_def → data_source #44


-- ── DONE ───────────────────────────────────────────────────────────────────
SELECT '=== KROK H MINIMAL DONE ===' AS section,
       'Marti: zkopiruj nested_core_id ze Step 3 → uprav coreId v data_source_op_detail.js line ~159'
       AS instruction;
