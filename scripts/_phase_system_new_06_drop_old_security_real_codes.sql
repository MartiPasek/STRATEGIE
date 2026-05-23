-- ============================================================
-- Phase SYSTEM NEW — Etapa 6: DROP stará Security (REAL codes)
-- ============================================================
-- Datum: 21.5.2026 vecer
-- Marti's catch: „To uz jsem delal minule" + screenshot ukazal
-- starou Security pod SYSTEM stale visible v sidebaru.
--
-- ROOT CAUSE: Etapa 5 pouzila pattern 'security%' / 'diag_log_master'
-- ale real codes jsou s tecka prefix:
--   - system.security                    (folder)
--   - system.security.users
--   - system.security.devices
--   - system.security.whitelists
--   - system.security.invites
--   - system.security.audit  NEBO  system.security.auth_audit
--   - diag_log_master                    (separate)
--
-- Etapa 5 vratila „0 expected 0" jako FALSE POSITIVE SUCCESS —
-- 0 rows matchovalo, 0 se smazalo. DB stale obsahuje stare rows.
--
-- Tento script:
--   - Pattern: code LIKE 'system.security%' (folder + 5 children)
--   - Plus: code = 'diag_log_master'
--   - Safety guard: NOT LIKE 'system_new.%' (nelogicke ale safe)
--   - Hw_registry soft delete (audit RO doctrine Fix N)
--
-- ZACHOVAT:
--   - public.* tables (data) — neporušené
--   - Python /system/security HC endpoint — Phase 5/6 separately
--   - system.audit.* (zachovat — Marti rekl jen Security)
--
-- Spusteni: DBeaver Alt+X.
-- ============================================================

BEGIN;

-- ============================================================
-- PRE-DIAGNOSTIC: ukáž real rows v DB
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
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd
        JOIN fw.core c ON c.id = cd.core_id
        WHERE (c.code LIKE 'system.security%' OR c.code = 'diag_log_master')
          AND c.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE (ds.code LIKE 'system.security%' OR ds.code = 'diag_log_master')
          AND ds.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%'
          AND is_active = TRUE;

    RAISE NOTICE '╔════ PRE-DELETE (real codes system.security.*) ════╗';
    RAISE NOTICE '║ fw.menu_node          = % rows DELETE              ║', v_menu;
    RAISE NOTICE '║ fw.core               = % rows DELETE              ║', v_core;
    RAISE NOTICE '║ fw.comp_def           = % rows DELETE              ║', v_compdef;
    RAISE NOTICE '║ fw.data_source        = % rows DELETE              ║', v_ds;
    RAISE NOTICE '║ fw.data_set           = % rows DELETE              ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op     = % rows DELETE              ║', v_dso;
    RAISE NOTICE '║ fw.hw_registry ACTIVE = % rows SOFT (is_active=F)  ║', v_hw;
    RAISE NOTICE '╚════════════════════════════════════════════════════╝';
END $$;

-- PRE-DELETE list co konkretne pujde
SELECT
    'PRE-DELETE menu_node' AS what,
    id::text,
    code,
    label,
    'parent=' || COALESCE(parent_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%'
ORDER BY sort_order, id;


-- ============================================================
-- STEP 1: DELETE fw.data_source_op (FK leafs)
-- ============================================================

DELETE FROM fw.data_source_op
WHERE data_source_id IN (
    SELECT id FROM fw.data_source
    WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 2: DELETE fw.data_set
-- ============================================================

DELETE FROM fw.data_set
WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 3: DELETE fw.data_source
-- ============================================================

DELETE FROM fw.data_source
WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 4: SOFT DELETE fw.hw_registry (audit RO doctrine)
-- ============================================================

UPDATE fw.hw_registry
SET is_active = FALSE,
    shadow_mode = 'off',
    updated_at = NOW()
WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%'
  AND (is_active = TRUE OR shadow_mode != 'off');

-- ============================================================
-- STEP 5: DELETE fw.comp_def (FK na core)
-- ============================================================

DELETE FROM fw.comp_def
WHERE core_id IN (
    SELECT id FROM fw.core
    WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 6: DELETE fw.core
-- ============================================================

DELETE FROM fw.core
WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 7: DELETE fw.menu_node (child leafs first, then parent folder)
-- ============================================================

-- Smazat child leafs (4-5 security sub-grids + diag_log_master)
DELETE FROM fw.menu_node
WHERE parent_id IN (
    SELECT id FROM fw.menu_node WHERE code = 'system.security' AND code NOT LIKE 'system_new.%'
)
   OR (
       code LIKE 'system.security.%'
       AND code NOT LIKE 'system_new.%'
   )
   OR code = 'diag_log_master';

-- Smazat parent 'system.security' folder
DELETE FROM fw.menu_node
WHERE code = 'system.security' AND code NOT LIKE 'system_new.%';


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
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd
        JOIN fw.core c ON c.id = cd.core_id
        WHERE (c.code LIKE 'system.security%' OR c.code = 'diag_log_master')
          AND c.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE (ds.code LIKE 'system.security%' OR ds.code = 'diag_log_master')
          AND ds.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE (code LIKE 'system.security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%'
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
        RAISE NOTICE 'SUCCESS: Stara system.security.* + diag_log_master pryc.';
        RAISE NOTICE 'Hard reload UI → stara Security pod SYSTEM zmizi.';
    ELSE
        RAISE NOTICE 'POZOR: nektere rows zustaly. Inspect manualne.';
    END IF;
END $$;

-- VERIFY: system_new.* zustava neporusen
SELECT
    'SYSTEM NEW zachovano' AS what,
    code,
    label,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new%'
ORDER BY sort_order, id;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   1. Hard reload UI
--   2. Stara Security pod SYSTEM → pryc
--   3. Stary Diag log (s 400 errorem) → pryc
--   4. SYSTEM NEW → Security s 6 grids → zustava ✓
--
-- POKUD STARÁ SECURITY STÁLE VIDET PO COMMIT:
--   - Tj. JS bundle cache nebo hardcoded fallback v lefttree.js
--   - Pošli mi info, hledame dál v frontend kodu
-- ============================================================
