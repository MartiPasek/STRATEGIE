-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.J-B2 (16.5.2026 ~23:55):
-- INSERT pagecontrol + 2 tabsheets jako new parents nad existing
-- 3 entity_pickery v core_design form (core_id=30)
-- ════════════════════════════════════════════════════════════════════════
-- Marti's vize: "page control jako standardni fw componentu". Z Form 1
-- styl (DesignSoudecekCoreForm má ErpPageControl s tabs "Přehled" +
-- "Smazat později") → přenést do DesignFwForm jako fw.comp_def hierarchy.
--
-- BEFORE structure:
--   form_root (id=37, type=302) — children:
--     ├── soudecek_picker (id=41, type=310)
--     ├── prehled_picker  (id=42, type=310)
--     └── data_source_picker (id=43, type=310)
--
-- AFTER structure:
--   form_root (id=37, type=302) — children:
--     └── main_pagecontrol (NEW, type=15) — children:
--         ├── tab_prehled (NEW, type=16) — children:
--         │   ├── soudecek_picker (id=41, re-parented)
--         │   ├── prehled_picker  (id=42, re-parented)
--         │   └── data_source_picker (id=43, re-parented)
--         └── tab_smazat_pozdeji (NEW, type=16) — empty (placeholder)
--
-- Frontend renderer (Krok 5.J-B2 already deployed) automaticky podporuje
-- pagecontrol + tabsheet via _renderComponentTree CONTAINER_CODES extension.
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. Verify fw.comp_type pagecontrol + tabsheet existují (z Krok 13 Delphi compat)
-- ════════════════════════════════════════════════════════════════════════
DO $$
DECLARE
    pc_count INT;
    ts_count INT;
BEGIN
    SELECT COUNT(*) INTO pc_count FROM fw.comp_type WHERE code = 'pagecontrol';
    SELECT COUNT(*) INTO ts_count FROM fw.comp_type WHERE code = 'tabsheet';
    IF pc_count = 0 OR ts_count = 0 THEN
        RAISE EXCEPTION 'fw.comp_type "pagecontrol" or "tabsheet" missing — Krok 13 Delphi compat seedem incomplete?';
    END IF;
    RAISE NOTICE 'comp_type pagecontrol + tabsheet exist (OK)';
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 2. INSERT pagecontrol jako child form_root (id=37)
--    sort_order=5 — pred existing pickery (kteří měli 10/20/30)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_def (
    parent_core_id, parent_comp_def_id, type_id,
    name, caption, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    NULL::bigint, 37, ct.id,
    'main_pagecontrol', '', 'main', 5, true,
    '{}'::jsonb,
    1, 'Marti', 1, 'Marti'
FROM fw.comp_type ct
WHERE ct.code = 'pagecontrol';

-- ════════════════════════════════════════════════════════════════════════
-- 3. INSERT 2 tabsheets jako children pagecontrol
-- ════════════════════════════════════════════════════════════════════════
WITH pc AS (
    SELECT id FROM fw.comp_def
    WHERE parent_comp_def_id = 37
      AND type_id = (SELECT id FROM fw.comp_type WHERE code = 'pagecontrol')
      AND name = 'main_pagecontrol'
    ORDER BY id DESC LIMIT 1
)
INSERT INTO fw.comp_def (
    parent_core_id, parent_comp_def_id, type_id,
    name, caption, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT NULL::bigint, pc.id, ct.id, v.name, v.caption, 'main', v.sort_order, true,
       '{}'::jsonb, 1, 'Marti', 1, 'Marti'
FROM pc
CROSS JOIN fw.comp_type ct
CROSS JOIN (VALUES
    ('tab_prehled', 'Přehled', 10),
    ('tab_smazat_pozdeji', 'Smazat později', 20)
) AS v(name, caption, sort_order)
WHERE ct.code = 'tabsheet';

-- ════════════════════════════════════════════════════════════════════════
-- 4. Re-parent existing 3 entity_pickery (ids 41, 42, 43) z form_root (37)
--    do tab_prehled (new tabsheet)
-- ════════════════════════════════════════════════════════════════════════
WITH ts AS (
    SELECT id FROM fw.comp_def
    WHERE parent_comp_def_id IN (
        SELECT id FROM fw.comp_def
        WHERE parent_comp_def_id = 37
          AND type_id = (SELECT id FROM fw.comp_type WHERE code = 'pagecontrol')
          AND name = 'main_pagecontrol'
    )
    AND name = 'tab_prehled'
    ORDER BY id DESC LIMIT 1
)
UPDATE fw.comp_def
SET parent_comp_def_id = (SELECT id FROM ts),
    updated_at = NOW(),
    updated_by_id = 1,
    updated_by_text = 'Marti'
WHERE id IN (41, 42, 43);

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY 1 — full tree pro core_id=30
-- ════════════════════════════════════════════════════════════════════════
WITH RECURSIVE tree AS (
    SELECT cd.id, cd.name, cd.caption, cd.parent_comp_def_id, cd.parent_core_id,
           cd.sort_order, ct.code AS type_code, 0 AS depth
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.parent_core_id = 30 AND cd.parent_comp_def_id IS NULL
      AND cd.is_active = true
    UNION ALL
    SELECT cd.id, cd.name, cd.caption, cd.parent_comp_def_id, cd.parent_core_id,
           cd.sort_order, ct.code AS type_code, t.depth + 1
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    JOIN tree t ON cd.parent_comp_def_id = t.id
    WHERE cd.is_active = true
)
SELECT REPEAT('  ', depth) || '#' || id || ' ' || type_code || ' "' || COALESCE(caption, name) || '"' AS tree_node,
       sort_order
FROM tree
ORDER BY depth, sort_order;
-- Expected:
--   #37 form (form_root)
--     #<new_pc_id> pagecontrol (main_pagecontrol)        sort=5
--       #<new_ts1_id> tabsheet "Přehled"                  sort=10
--         #41 entity_picker (soudecek_picker)
--         #42 entity_picker (prehled_picker)
--         #43 entity_picker (data_source_picker)
--       #<new_ts2_id> tabsheet "Smazat později"           sort=20
