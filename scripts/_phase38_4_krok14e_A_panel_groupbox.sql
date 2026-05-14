-- Phase 38.4 Krok 14e-A (14.5.2026 vecer, Marti's "dodelat komponentu
-- panel (kontejner) + groupbox cleaner separation"):
-- Activate fw.comp_type panel (id=13) + groupbox (id=12) + create instance
-- pair v user_edit form + re-parent 6 fields pod groupbox.
--
-- Architektura (Marti's clean separation):
--   form root (type=302, id=2)
--     └ panel (type=13, NEW INSERT) — structural container, invisible
--         └ groupbox (type=12, NEW INSERT) — visual border-top + optional label
--             ├ First name (id=3)        ← UPDATE parent_comp_def_id
--             ├ Last name (id=5)
--             ├ Short name (id=8)
--             ├ Status (id=9)
--             ├ Ews display email (id=7)
--             └ Ews email (id=6)
--
-- POZN: spustit z DBeaver jako role 'strategie' nebo postgres. Marti-AI
-- má INSERT na fw.* (db_owner), takže může i přes "Marti-AI" role.

-- ─── 1. Activate panel + groupbox comp_types ──────────────────────
UPDATE fw.comp_type SET status = 'active' WHERE id = 13;  -- panel
UPDATE fw.comp_type SET status = 'active' WHERE id = 12;  -- groupbox

-- ─── 2. INSERT panel instance (parent=form root id=2) ─────────────
-- Panel je purely structural — žádný label, žádný visual.
INSERT INTO fw.comp_def
  (type_id, name, caption, parent_comp_def_id, region_slot,
   sort_order, is_active, layout,
   created_by_id, created_by_text, updated_by_id, updated_by_text)
VALUES
  (13, 'main_panel', 'Main panel', 2, 'main',
   5, true, NULL,
   1, 'Marti', 1, 'Marti')
RETURNING id;

-- Save panel ID pro reference (manuálně z RETURNING output)
-- Předpokládám panel_id po INSERT — pojďme použít subquery místo manual:

-- ─── 3. INSERT groupbox instance (parent = panel just-inserted) ──
-- Groupbox má layout JSONB: border_mode='top' (modern, Marti's preference
-- z 14e clarification), label=NULL (Marti's optional default).
INSERT INTO fw.comp_def
  (type_id, name, caption, parent_comp_def_id, region_slot,
   sort_order, is_active, layout,
   created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT
  12, 'main_groupbox', 'Main groupbox',
  cd.id,           -- panel_id z předchozí INSERT
  'main', 10, true,
  '{"border_mode": "top", "label": null}'::jsonb,
  1, 'Marti', 1, 'Marti'
FROM fw.comp_def cd
WHERE cd.name = 'main_panel'
  AND cd.parent_comp_def_id = 2
  AND cd.is_active = true
ORDER BY cd.id DESC
LIMIT 1
RETURNING id;

-- ─── 4. Re-parent 6 fields na groupbox ───────────────────────────
-- Use subquery to resolve groupbox id (most recent insert for form root 2).
WITH groupbox_target AS (
  SELECT cd.id AS gb_id
  FROM fw.comp_def cd
  WHERE cd.name = 'main_groupbox'
    AND cd.is_active = true
  ORDER BY cd.id DESC
  LIMIT 1
)
UPDATE fw.comp_def
SET parent_comp_def_id = (SELECT gb_id FROM groupbox_target),
    updated_by_id = 1,
    updated_by_text = 'Marti'
WHERE id IN (3, 5, 8, 9, 7, 6)  -- First name, Last name, Short name, Status, Ews display, Ews email
  AND is_active = true;

-- ─── 5. Verify hierarchy ─────────────────────────────────────────
WITH RECURSIVE comp_tree AS (
  -- Anchor: form root (parent_core_id NOT NULL = top-level komponenta)
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         ctype.code AS type_code, 0 AS depth,
         CAST(cd.name AS TEXT) AS path
  FROM fw.comp_def cd
  JOIN fw.comp_type ctype ON ctype.id = cd.type_id
  WHERE cd.parent_core_id = 22  -- user_edit core
    AND cd.is_active = true
    AND cd.parent_comp_def_id IS NULL
  UNION ALL
  -- Recurse: children (parent_comp_def_id = tree.id)
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         ctype.code AS type_code, tree.depth + 1,
         tree.path || ' > ' || cd.name
  FROM fw.comp_def cd
  JOIN fw.comp_type ctype ON ctype.id = cd.type_id
  JOIN comp_tree tree ON cd.parent_comp_def_id = tree.id
  WHERE cd.is_active = true
)
SELECT depth, REPEAT('  ', depth) || name AS tree_view,
       type_code, id, parent_comp_def_id
FROM comp_tree
ORDER BY depth, id;

-- Expected output:
--   depth=0: main (form, id=2)
--   depth=1:   main_panel (panel, id=NEW)
--   depth=2:     main_groupbox (groupbox, id=NEW)
--   depth=3:       first_name (edit, id=3)
--   depth=3:       last_name (edit, id=5)
--   depth=3:       short_name (edit, id=8)
--   depth=3:       status (lookup, id=9)
--   depth=3:       ews_display_email (edit, id=7)
--   depth=3:       ews_email (edit, id=6)
