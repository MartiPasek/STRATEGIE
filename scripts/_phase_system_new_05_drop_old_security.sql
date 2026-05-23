-- ============================================================
-- Phase SYSTEM NEW — Etapa 5: DROP stará Security sekce
-- ============================================================
-- Datum: 21.5.2026 vecer
-- Marti: „SUPER, Muzes starou sekci Security zprovodit ze sveta"
--
-- Po LIVE 6/6 v SYSTEM NEW (Etapa 1-4): odstranit staré
-- fw.menu_node + fw.core + fw.comp_def + fw.data_source + fw.data_set
-- + fw.data_source_op rows pro security_* a diag_log_master.
--
-- ZACHOVAT (jen smazat ze stromu / framework):
--   - tabulky public.users, public.trusted_devices, public.global_ip_whitelist,
--     public.user_ip_whitelist, public.trusted_device_invites, public.auth_audit,
--     fw.diag_log — ŽÁDNÝ touch (data zustavaji, fw.* je jen UI definice)
--   - Python HC endpoint /api/v1/erp/system/security?mode=X — Phase 5/6
--     cleanup separately (drop z router.py kdykoliv pozdeji)
--
-- SMAZAT (UI definice v fw.*):
--   - menu_node: security folder + 6 child gridy (devices/users/whitelists/
--     invites/auth_audit/diag_log_master)
--   - core, comp_def, data_source, data_set, data_source_op pro same codes
--
-- POZOR: VŠECHNY system_new.* rows ZUSTAVAJI (NEW versions live).
--
-- FK-safe order (deletion cascade):
--   1. fw.data_source_op (FK na data_source + data_set)
--   2. fw.data_set
--   3. fw.data_source
--   4. fw.hw_registry (code-based reference na core, no FK)
--   5. fw.comp_def (FK na core)
--   6. fw.core
--   7. fw.menu_node (FK na core_id, nullable)
--
-- Safety: BEGIN/COMMIT atomic. Diagnostic NOTICE pred kazdym DELETE
-- ukaze pocet rows. Pokud chces ROLLBACK misto COMMIT, manually pres
-- ROLLBACK statement na konci.
--
-- Spusteni v DBeaveru: highlight cely script + Alt+X
-- ============================================================

BEGIN;

-- ============================================================
-- IDENTIFICATION: Codes co se budou mazat (NOT system_new.*)
-- ============================================================
-- security parent + 6 gridy (devices/users/whitelists/invites/
-- auth_audit/diag_log_master). Plus catch-all pro security_*
-- s code NOT LIKE 'system_new.%'.

-- ============================================================
-- DIAGNOSTIC: Co existuje pred DELETE?
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
    SELECT COUNT(*) INTO v_menu
    FROM fw.menu_node
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_core
    FROM fw.core
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_compdef
    FROM fw.comp_def cd
    JOIN fw.core c ON c.id = cd.core_id
    WHERE (c.code LIKE 'security%' OR c.code = 'diag_log_master')
      AND c.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_ds
    FROM fw.data_source
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dset
    FROM fw.data_set
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_dso
    FROM fw.data_source_op dso
    JOIN fw.data_source ds ON ds.id = dso.data_source_id
    WHERE (ds.code LIKE 'security%' OR ds.code = 'diag_log_master')
      AND ds.code NOT LIKE 'system_new.%';

    SELECT COUNT(*) INTO v_hw
    FROM fw.hw_registry
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%'
      AND is_active = TRUE;

    RAISE NOTICE '╔════ STARÁ Security — co se smaže ════╗';
    RAISE NOTICE '║ fw.menu_node        = % rows DELETE ║', v_menu;
    RAISE NOTICE '║ fw.core             = % rows DELETE ║', v_core;
    RAISE NOTICE '║ fw.comp_def         = % rows DELETE ║', v_compdef;
    RAISE NOTICE '║ fw.data_source      = % rows DELETE ║', v_ds;
    RAISE NOTICE '║ fw.data_set         = % rows DELETE ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op   = % rows DELETE ║', v_dso;
    RAISE NOTICE '║ fw.hw_registry      = % rows SOFT (is_active=FALSE) ║', v_hw;
    RAISE NOTICE '╚═══════════════════════════════════════╝';
    RAISE NOTICE 'Pozn.: hw_registry soft delete - audit RO doctrine zachova history.';
END $$;

-- ============================================================
-- LIST: konkrétně které rows (pre-delete inspection)
-- ============================================================

SELECT
    'PRE-DELETE menu_node' AS what,
    id::text AS id,
    code,
    label,
    'parent=' || COALESCE(parent_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE (code LIKE 'security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%'
ORDER BY sort_order, id;


-- ============================================================
-- STEP 1: DELETE fw.data_source_op (FK leafs)
-- ============================================================

DELETE FROM fw.data_source_op
WHERE data_source_id IN (
    SELECT id FROM fw.data_source
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 2: DELETE fw.data_set
-- ============================================================

DELETE FROM fw.data_set
WHERE (code LIKE 'security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 3: DELETE fw.data_source
-- ============================================================

DELETE FROM fw.data_source
WHERE (code LIKE 'security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 4: SOFT DELETE fw.hw_registry (audit RO doctrine)
-- ============================================================
-- HW registry ma fw.hw_registry_history FK constraint (audit RO append-only,
-- Marti's Fix N doctrine 21.5. ranni). Hard DELETE porusi audit chain.
-- Reseni: UPDATE is_active=FALSE + shadow_mode='off' → row v DB zustane
-- pro audit, ale dispatcher uz ji nepouzije (frontend tree neukaze).

UPDATE fw.hw_registry
SET is_active = FALSE,
    shadow_mode = 'off',
    updated_at = NOW()
WHERE (code LIKE 'security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%'
  AND (is_active = TRUE OR shadow_mode != 'off');

-- ============================================================
-- STEP 5: DELETE fw.comp_def (FK na core)
-- ============================================================

DELETE FROM fw.comp_def
WHERE core_id IN (
    SELECT id FROM fw.core
    WHERE (code LIKE 'security%' OR code = 'diag_log_master')
      AND code NOT LIKE 'system_new.%'
);

-- ============================================================
-- STEP 6: DELETE fw.core
-- ============================================================

DELETE FROM fw.core
WHERE (code LIKE 'security%' OR code = 'diag_log_master')
  AND code NOT LIKE 'system_new.%';

-- ============================================================
-- STEP 7: DELETE fw.menu_node (LAST — FK na core_id nullable)
-- ============================================================
-- Order: child leafs first (DELETE depth-first via parent_id check),
-- pak parent 'security' folder.

-- Smazat child leafs (6 grids + cokoliv navic)
DELETE FROM fw.menu_node
WHERE parent_id = (SELECT id FROM fw.menu_node WHERE code = 'security' AND code NOT LIKE 'system_new.%')
   OR (
       (code LIKE 'security%' OR code = 'diag_log_master')
       AND code NOT LIKE 'system_new.%'
       AND code != 'security'  -- parent zatim necham
   );

-- Smazat parent 'security' folder (uz prazdny po child cleanup)
DELETE FROM fw.menu_node
WHERE code = 'security' AND code NOT LIKE 'system_new.%';


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
        WHERE (code LIKE 'security%' OR code = 'diag_log_master') AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_core FROM fw.core
        WHERE (code LIKE 'security%' OR code = 'diag_log_master') AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd JOIN fw.core c ON c.id = cd.core_id
        WHERE (c.code LIKE 'security%' OR c.code = 'diag_log_master') AND c.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source
        WHERE (code LIKE 'security%' OR code = 'diag_log_master') AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE (code LIKE 'security%' OR code = 'diag_log_master') AND code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE (ds.code LIKE 'security%' OR ds.code = 'diag_log_master') AND ds.code NOT LIKE 'system_new.%';
    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE (code LIKE 'security%' OR code = 'diag_log_master')
          AND code NOT LIKE 'system_new.%'
          AND is_active = TRUE;

    RAISE NOTICE '╔════ POST-DELETE (expected vse 0) ════╗';
    RAISE NOTICE '║ fw.menu_node        = % rows ║', v_menu;
    RAISE NOTICE '║ fw.core             = % rows ║', v_core;
    RAISE NOTICE '║ fw.comp_def         = % rows ║', v_compdef;
    RAISE NOTICE '║ fw.data_source      = % rows ║', v_ds;
    RAISE NOTICE '║ fw.data_set         = % rows ║', v_dset;
    RAISE NOTICE '║ fw.data_source_op   = % rows ║', v_dso;
    RAISE NOTICE '║ fw.hw_registry ACTIVE = % rows ║', v_hw;
    RAISE NOTICE '╚═══════════════════════════════════════╝';

    IF v_menu = 0 AND v_core = 0 AND v_compdef = 0
       AND v_ds = 0 AND v_dset = 0 AND v_dso = 0 AND v_hw = 0 THEN
        RAISE NOTICE 'SUCCESS: Stara Security sekce zprovozena.';
        RAISE NOTICE 'COMMIT (default) nebo ROLLBACK (manualne pokud chces undo).';
    ELSE
        RAISE NOTICE 'POZOR: nejake rows zustaly. Inspect manualne pred COMMIT.';
    END IF;
END $$;

-- ============================================================
-- VERIFY: system_new.* zustava neporusen
-- ============================================================

SELECT
    'SYSTEM NEW zachovano' AS what,
    code,
    label,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new%'
ORDER BY sort_order, id;

-- ============================================================
-- COMMIT na konci. Pokud nechces, manually:
--   ROLLBACK;
-- na konci scriptu nahradí COMMIT.
-- ============================================================

COMMIT;

-- ============================================================
-- PO COMMITU:
--   1. Hard reload UI (Ctrl+Shift+R)
--   2. Levý strom: stara Security pod SYSTEM by mela zmizet
--   3. SYSTEM NEW → Security → 6 gridu zustava ✓
--
-- TODO Phase 5/6 (post-cleanup): drop Python /system/security
-- endpoint v router.py (+ related ORM imports). Zatim staci, ze
-- nikdo na nej z UI neklika.
-- ============================================================
