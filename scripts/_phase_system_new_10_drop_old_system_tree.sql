-- ============================================================
-- Phase SYSTEM NEW — Etapa 10: DROP celý starý SYSTEM strom
-- ============================================================
-- Datum: 22.5.2026 ranní
-- Marti: „Hotovo... Muzes vycistit a pomazat celaj starej soudecek System"
--
-- Po Etapě 9 (Audit/Všechny konverzace LIVE v SYSTEM NEW) — všechny
-- migrace dokončené. Starý SYSTEM strom je dead weight.
--
-- Match pattern: `code LIKE 'system%' AND code NOT LIKE 'system_new%'`
--   Zachytí:
--     - 'system' (root folder)
--     - 'system.audit' + 4 children (tabs/audited/all/stats)
--     - cokoliv dalšího co tam ještě je
--   Vyloučí:
--     - 'system_new' + 'system_new.*' (SYSTEM NEW family)
--
-- DOCTRINE z 7c v2 (Marti's „Vsechno ostatni zustane"):
--   fw.core ZACHOVAT — některé cores jsou reused do system_new (Přehled
--   datasourců / Knowledge Entries / Znalostní báze přes 7c v2 reparent).
--   Jen orphan cores (no menu_node reference vůbec) lze cleanup později.
--
-- Cascade order (FK-safe):
--   1. data_source_op (FK na data_source + data_set)
--   2. comp_def (FK na core + data_source) — jen orphans, ne 7c v2 reused
--   3. data_set — jen orphans
--   4. data_source — jen orphans
--   5. hw_registry SOFT (audit RO doctrine Fix N)
--   6. fw.core ZACHOVAT (Marti 7c v2 doctrine)
--   7. menu_node (child leafs first, then parents)
--
-- Match strategy pro orphans:
--   - comp_def: WHERE core_id IN (cores wired ONLY to old SYSTEM)
--   - data_source / data_set: WHERE id IN (referenced by deleted comp_def)
--   - Identifikace „cores wired ONLY to old SYSTEM" = cores wired do
--     starého menu_node (LIKE 'system%') BUT NOT wired do system_new
--
-- Spusteni: DBeaver Alt+X
-- ============================================================

BEGIN;

-- ============================================================
-- PRE-DIAGNOSTIC: co se smaže
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_orphan_cores INT;
    v_compdef INT;
    v_dset INT;
    v_ds INT;
    v_dso INT;
    v_hw INT;
BEGIN
    -- Staré menu_nodes
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node
        WHERE code LIKE 'system%' AND code NOT LIKE 'system_new%';

    -- Cores wired JEN do starého menu_node (NE do system_new)
    SELECT COUNT(*) INTO v_orphan_cores FROM fw.core c
    WHERE EXISTS (
        SELECT 1 FROM fw.menu_node old_mn
        WHERE old_mn.core_id = c.id
          AND old_mn.code LIKE 'system%'
          AND old_mn.code NOT LIKE 'system_new%'
    )
    AND NOT EXISTS (
        SELECT 1 FROM fw.menu_node new_mn
        WHERE new_mn.core_id = c.id
          AND new_mn.code LIKE 'system_new%'
    );

    -- Comp_defs co odejdou (linked k orphan cores)
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def cd
    WHERE cd.core_id IN (
        SELECT c.id FROM fw.core c
        WHERE EXISTS (
            SELECT 1 FROM fw.menu_node old_mn
            WHERE old_mn.core_id = c.id
              AND old_mn.code LIKE 'system%'
              AND old_mn.code NOT LIKE 'system_new%'
        )
        AND NOT EXISTS (
            SELECT 1 FROM fw.menu_node new_mn
            WHERE new_mn.core_id = c.id
              AND new_mn.code LIKE 'system_new%'
        )
    );

    -- HW registry pro old audit/system codes
    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE (code LIKE 'audit_%' OR code LIKE 'system.%' OR code LIKE 'framework_%')
          AND code NOT LIKE 'system_new%'
          AND is_active = TRUE;

    RAISE NOTICE '╔════ STARÝ SYSTEM — co se smaže ════╗';
    RAISE NOTICE '║ fw.menu_node          = % rows DELETE             ║', v_menu;
    RAISE NOTICE '║ fw.core ORPHAN        = % rows (info — NEDELETE) ║', v_orphan_cores;
    RAISE NOTICE '║ fw.comp_def OPHAN     = % rows DELETE            ║', v_compdef;
    RAISE NOTICE '║ fw.hw_registry ACTIVE = % rows SOFT delete       ║', v_hw;
    RAISE NOTICE '╚════════════════════════════════════════════════════╝';
    RAISE NOTICE 'Pozn.: fw.core orphans NE-deletujem (Marti 7c v2 doctrine).';
    RAISE NOTICE 'Pokud chces orphan core cleanup, separate script později.';
END $$;

-- PRE-DELETE list menu_node
SELECT
    'PRE-DELETE menu_node' AS what,
    id::text,
    code,
    label,
    'parent=' || COALESCE(parent_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system%' AND code NOT LIKE 'system_new%'
ORDER BY sort_order, id;


-- ============================================================
-- STEP 1: DELETE fw.data_source_op (FK leafs)
-- ============================================================
-- Jen data_source_op referenced by orphan comp_defs.

DELETE FROM fw.data_source_op
WHERE data_source_id IN (
    SELECT DISTINCT cd.data_source_id FROM fw.comp_def cd
    WHERE cd.data_source_id IS NOT NULL
      AND cd.core_id IN (
          SELECT c.id FROM fw.core c
          WHERE EXISTS (
              SELECT 1 FROM fw.menu_node old_mn
              WHERE old_mn.core_id = c.id
                AND old_mn.code LIKE 'system%'
                AND old_mn.code NOT LIKE 'system_new%'
          )
          AND NOT EXISTS (
              SELECT 1 FROM fw.menu_node new_mn
              WHERE new_mn.core_id = c.id
                AND new_mn.code LIKE 'system_new%'
          )
      )
);

-- ============================================================
-- STEP 2: DELETE fw.comp_def (FK na core + data_source)
-- ============================================================

DELETE FROM fw.comp_def
WHERE core_id IN (
    SELECT c.id FROM fw.core c
    WHERE EXISTS (
        SELECT 1 FROM fw.menu_node old_mn
        WHERE old_mn.core_id = c.id
          AND old_mn.code LIKE 'system%'
          AND old_mn.code NOT LIKE 'system_new%'
    )
    AND NOT EXISTS (
        SELECT 1 FROM fw.menu_node new_mn
        WHERE new_mn.core_id = c.id
          AND new_mn.code LIKE 'system_new%'
    )
);

-- ============================================================
-- STEP 3: DELETE fw.data_set (orphans — ne referenced žádným data_source_op)
-- ============================================================
-- Po Step 1 cleanup data_source_op, data_set pro orphan flow je
-- bez reference. Identifikujeme pres dropped data_source codes
-- (audit_overview, system_audit, atd.).

DELETE FROM fw.data_set
WHERE id IN (
    SELECT ds.id FROM fw.data_set ds
    WHERE NOT EXISTS (
        SELECT 1 FROM fw.data_source_op dso WHERE dso.data_set_id = ds.id
    )
    AND ds.code IS NOT NULL
    AND (ds.code LIKE 'audit_%' OR ds.code LIKE 'system.audit%')
    AND ds.code NOT LIKE 'system_new%'
);

-- ============================================================
-- STEP 4: DELETE fw.data_source (orphans)
-- ============================================================

DELETE FROM fw.data_source
WHERE id IN (
    SELECT ds.id FROM fw.data_source ds
    WHERE NOT EXISTS (
        SELECT 1 FROM fw.comp_def cd WHERE cd.data_source_id = ds.id
    )
    AND NOT EXISTS (
        SELECT 1 FROM fw.data_source_op dso WHERE dso.data_source_id = ds.id
    )
    AND ds.code IS NOT NULL
    AND (ds.code LIKE 'audit_%' OR ds.code LIKE 'system.audit%')
    AND ds.code NOT LIKE 'system_new%'
);

-- ============================================================
-- STEP 5: SOFT DELETE fw.hw_registry (audit RO doctrine)
-- ============================================================

UPDATE fw.hw_registry
SET is_active = FALSE,
    shadow_mode = 'off',
    updated_at = NOW()
WHERE (code LIKE 'audit_%' OR code LIKE 'system.%')
  AND code NOT LIKE 'system_new%'
  AND (is_active = TRUE OR shadow_mode != 'off');

-- ============================================================
-- STEP 6: DELETE fw.menu_node (child leafs first, then parents)
-- ============================================================

-- Smazat všechny child leafs (system.audit.tabs/audited/all/stats + cokoliv)
DELETE FROM fw.menu_node
WHERE code LIKE 'system.%' AND code NOT LIKE 'system_new%';

-- Smazat root 'system' folder (po children pryc)
DELETE FROM fw.menu_node
WHERE code = 'system';


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_compdef INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
    v_hw INT;
    v_orphan_cores INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node
        WHERE code LIKE 'system%' AND code NOT LIKE 'system_new%';
    SELECT COUNT(*) INTO v_orphan_cores FROM fw.core c
        WHERE NOT EXISTS (
            SELECT 1 FROM fw.menu_node mn WHERE mn.core_id = c.id
        );
    SELECT COUNT(*) INTO v_hw FROM fw.hw_registry
        WHERE (code LIKE 'audit_%' OR code LIKE 'system.%')
          AND code NOT LIKE 'system_new%' AND is_active = TRUE;

    RAISE NOTICE '╔════ POST-DELETE ════╗';
    RAISE NOTICE '║ fw.menu_node old        = % rows (expected 0) ║', v_menu;
    RAISE NOTICE '║ fw.hw_registry ACTIVE   = % rows (expected 0) ║', v_hw;
    RAISE NOTICE '║ fw.core orphan (any)    = % rows (info)       ║', v_orphan_cores;
    RAISE NOTICE '╚════════════════════════════════════════════════╝';

    IF v_menu = 0 AND v_hw = 0 THEN
        RAISE NOTICE 'SUCCESS: Stara SYSTEM family pryc.';
        RAISE NOTICE 'Hard reload UI → SYSTEM strom zmizi.';
        RAISE NOTICE 'Zustane jen SYSTEM NEW (Security + Framework + Audit).';
        IF v_orphan_cores > 0 THEN
            RAISE NOTICE 'Pozn.: % orphan cores zustanou — Marti rozhodne separate cleanup.', v_orphan_cores;
        END IF;
    END IF;
END $$;

-- VERIFY: system_new tree zachovany
SELECT
    'SYSTEM NEW zachovano' AS what,
    code,
    label,
    sort_order
FROM fw.menu_node
WHERE code LIKE 'system_new%'
ORDER BY sort_order, id;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   Hard reload UI → sidebar tree:
--     ❌ SYSTEM (smazáno!)
--     ✓ SYSTEM NEW
--          ├── Security    (6 grids)
--          ├── Framework   (5 grids vč. reused cores)
--          └── Audit       (1 grid: Všechny konverzace)
--
-- DALSI CLEANUP (Marti rozhodne):
--   A) Python /system/audit-overview handler drop (lines 791-1117)
--      Plus /system/audit-conversation/* (lines 1118-1326)
--   B) Python /system/framework handler drop (lines 1343-1623)
--   C) erp_grid_dispatcher.js framework_* fallback drop
--   D) Orphan cores cleanup (po stable smoke)
-- ============================================================
