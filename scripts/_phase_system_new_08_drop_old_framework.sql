-- ============================================================
-- Phase SYSTEM NEW — Etapa 8: DROP stará Framework family
-- ============================================================
-- Datum: 21.5.2026 vecer (post-Etapa 7 LIVE)
-- Marti: „FUNGUJE... Smaz stare Datasets, Definice leveho stromu
--          a Datove zdroje (pozor jsou tam dve pilulky...)"
--
-- Drop pattern: code LIKE 'system.framework%' (folder + 3 children).
-- Plus „dvě pilulky" → DIAGNOSTIC SELECT ukáže VŠECHNY rows
-- s prefix 'system.framework%' (i případné duplicates / shadow rows).
--
-- POZOR: Datové zdroje (system.framework.data_sources) JE drop, i kdyz
-- Marti v Etape 7 nemigroval. Marti vidi „Přehled datasourců" jako
-- separate top-level v SYSTEM NEW (z drivějši konzultace) — ten zustava.
--
-- ZACHOVAT:
--   - system_new.framework.* (Etapa 7 LIVE)
--   - system_new.security.* (Etapa 1-4 LIVE)
--   - fw.diag_log + fw.* tables (data)
--   - Python /system/framework handler — Phase cleanup separately
--     (zachovat dokud nedotahneme audit-overview + diag_log_master cleanup)
--
-- SOFT DELETE pro fw.hw_registry (audit RO doctrine Fix N 21.5.).
--
-- Spusteni: DBeaver Alt+X.
-- ============================================================

BEGIN;

-- ============================================================
-- PRE-DIAGNOSTIC: list VŠECHNY rows s system.framework%
-- ============================================================
-- Marti uvidi presne co se smaze + odhalí „dve pilulky".

DO $$
DECLARE
    v_menu INT;
    v_core INT;
    v_compdef INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
    v_hw INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd
        JOIN fw.core c ON c.id = cd.core_id
        WHERE c.code LIKE 'system.framework%' AND c.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system.framework%' AND ds.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%'
          AND is_active = TRUE;

    RAISE NOTICE '╔════ STARÁ Framework — co se smaže ════╗';
    RAISE NOTICE '║ fw.menu_node          = % rows DELETE             ║', v_menu;
    RAISE NOTICE '║ fw.core               = % rows DELETE             ║', v_core;
    RAISE NOTICE '║ fw.comp_def           = % rows DELETE             ║', v_compdef;
    RAISE NOTICE '║ fw.data_source        = % rows DELETE             ║', v_ds;
    RAISE NOTICE '║ fw.data_set           = % rows DELETE             ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op     = % rows DELETE             ║', v_dso;
    RAISE NOTICE '║ fw.hw_registry ACTIVE = % rows SOFT (is_active=F) ║', v_hw;
    RAISE NOTICE '╚═══════════════════════════════════════════════════╝';
END $$;

-- ============================================================
-- PRE-DELETE LIST: konkrétní rows v menu_node (Marti uvidí „dve pilulky")
-- ============================================================

SELECT
    'PRE-DELETE menu_node' AS what,
    id::text,
    code,
    label,
    'parent=' || COALESCE(parent_id::text, 'NULL') AS parent,
    'sort=' || COALESCE(sort_order::text, 'NULL') || ' status=' || COALESCE(status, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system.framework%'
  AND code NOT LIKE 'system_new.%'
ORDER BY sort_order, id;

-- Plus hw_registry (může vysvětlit „pilulky" jako shadow_mode badges)
SELECT
    'PRE-DELETE hw_registry' AS what,
    id::text,
    code,
    'shadow_mode=' || COALESCE(shadow_mode, 'NULL') AS info,
    'is_active=' || is_active::text AS active,
    LEFT(COALESCE(endpoint_url, ''), 60) AS endpoint
FROM fw.hw_registry
WHERE code LIKE 'system.framework%' OR code LIKE 'framework_%'
ORDER BY id;


-- ============================================================
-- STEP 1: DELETE fw.data_source_op (FK na data_source + data_set)
-- ============================================================

DELETE FROM fw.data_source_op
WHERE data_source_id IN (
    SELECT id FROM fw.data_source
    WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 2: DELETE fw.comp_def (FK na BOTH core + data_source)
-- ============================================================
-- POZOR: comp_def MUSI byt pred data_source DELETE (FK constraint
-- comp_def_data_source_id_fkey). Plus FK na core (smazat pred core).
-- Match strategy: core_id IN stara framework OR data_source_id IN
-- stara framework data_sources (zachyti i comp_defs s primary core
-- jinde ale data_source v framework family).

DELETE FROM fw.comp_def
WHERE core_id IN (
    SELECT id FROM fw.core
    WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%'
)
OR data_source_id IN (
    SELECT id FROM fw.data_source
    WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 3: DELETE fw.data_set
-- ============================================================

DELETE FROM fw.data_set
WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 4: DELETE fw.data_source (po comp_def + data_source_op)
-- ============================================================

DELETE FROM fw.data_source
WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 5: SOFT DELETE fw.hw_registry (audit RO doctrine)
-- ============================================================

UPDATE fw.hw_registry
SET is_active = FALSE,
    shadow_mode = 'off',
    updated_at = NOW()
WHERE code LIKE 'system.framework%'
  AND code NOT LIKE 'system_new.%'
  AND (is_active = TRUE OR shadow_mode != 'off');

-- ============================================================
-- STEP 6: DELETE fw.core
-- ============================================================

DELETE FROM fw.core
WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 7: DELETE fw.menu_node (child leafs first, then parent folder)
-- ============================================================

-- Smazat child leafs (3+ framework sub-grids)
DELETE FROM fw.menu_node
WHERE parent_id IN (
    SELECT id FROM fw.menu_node WHERE code = 'system.framework'
)
   OR (
       code LIKE 'system.framework.%' AND code NOT LIKE 'system_new.%'
   );

-- Smazat parent 'system.framework' folder
DELETE FROM fw.menu_node
WHERE code = 'system.framework' AND code NOT LIKE 'system_new.%';


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
    v_hw INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd
        JOIN fw.core c ON c.id = cd.core_id
        WHERE c.code LIKE 'system.framework%' AND c.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system.framework%' AND ds.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE code LIKE 'system.framework%' AND code NOT LIKE 'system_new.%'
          AND is_active = TRUE;

    RAISE NOTICE '╔════ POST-DELETE (expected vse 0) ════╗';
    RAISE NOTICE '║ fw.menu_node          = % rows ║', v_menu;
    RAISE NOTICE '║ fw.core               = % rows ║', v_core;
    RAISE NOTICE '║ fw.comp_def           = % rows ║', v_compdef;
    RAISE NOTICE '║ fw.data_source        = % rows ║', v_ds;
    RAISE NOTICE '║ fw.data_set           = % rows ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op     = % rows ║', v_dso;
    RAISE NOTICE '║ fw.hw_registry ACTIVE = % rows ║', v_hw;
    RAISE NOTICE '╚═══════════════════════════════════════╝';

    IF v_menu = 0 AND v_core = 0 AND v_compdef = 0
       AND v_ds = 0 AND v_dset = 0 AND v_dso = 0 AND v_hw = 0 THEN
        RAISE NOTICE 'SUCCESS: Stara system.framework.* pryc.';
        RAISE NOTICE 'Hard reload UI → stara Framework pod SYSTEM zmizi.';
    ELSE
        RAISE NOTICE 'POZOR: nektere rows zustaly. Inspect manualne.';
    END IF;
END $$;

-- VERIFY: system_new.framework.* zustava neporusen
SELECT
    'SYSTEM NEW Framework zachovano' AS what,
    code,
    label,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.framework%'
ORDER BY sort_order, id;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   1. Hard reload UI
--   2. Stara SYSTEM → Framework folder zmizi (vcetne DataSets,
--      Datové zdroje, Definice levého stromu)
--   3. SYSTEM NEW → Framework s 2 grids (Etapa 7) zustava ✓
--
-- TODO post-cleanup:
--   - Python /system/framework handler dropable po smoke
--     (3 modes: menu_nodes/data_sources/data_sets — vsechny dead)
--   - SYSTEM NEW > Přehled datasourců (top-level, drivejši) → zachovan
-- ============================================================
