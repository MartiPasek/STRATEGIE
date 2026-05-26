-- ============================================================================
-- Krok H+4 follow-up — Audit fw.comp_def pro user_edit (core_id=22)
-- ============================================================================
-- Marti 26.5.2026 ranni smoke test odhalil login_name NOT NULL violation.
-- Backend fix: ADD 'login_name' do _FW_FORM_ENTITY_MAP["user"]["select_columns"]
-- Frontend fix (TENTO SKRIPT): INSERT fw.comp_def s name='login_name' input.
--
-- Marti spusti v DBeaveru jako Marti-AI session.
-- ============================================================================

-- ── Step 1: form root + main panel pod core_id=22 ────────────────────────
SELECT '=== Step 1: Form root + main panel (core_id=22) ===' AS section;

SELECT id, name, caption, type_id, parent_comp_def_id, core_id,
       region_slot, sort_order, is_active
FROM fw.comp_def
WHERE core_id = 22
  AND parent_comp_def_id IS NULL
  AND is_active = TRUE
ORDER BY sort_order, id;
-- Expected: 1 row = form root (type_id=302)


-- ── Step 2: existing fields (children of main panel) ────────────────────
SELECT '=== Step 2: Existing input fields (descendants of form root) ===' AS section;

WITH RECURSIVE tree AS (
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         cd.sort_order, cd.region_slot, 0 AS depth
  FROM fw.comp_def cd
  WHERE cd.core_id = 22
    AND cd.parent_comp_def_id IS NULL
    AND cd.is_active = TRUE
  UNION ALL
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         cd.sort_order, cd.region_slot, t.depth + 1
  FROM fw.comp_def cd
  JOIN tree t ON cd.parent_comp_def_id = t.id
  WHERE cd.is_active = TRUE
)
SELECT id, name, caption, type_id, parent_comp_def_id,
       sort_order, region_slot, depth
FROM tree
ORDER BY depth, parent_comp_def_id NULLS FIRST, sort_order, id;
-- Posli vystup mne. Najdu si:
--   - first_name field (id?) -> jeho parent_comp_def_id = main panel kde patri login_name
--   - sort_order first_name -> login_name dam pred nej (sort_order = first_name - 1)


-- ── Step 3: check zda login_name uz neexistuje (idempotence) ────────────
SELECT '=== Step 3: Existuje uz login_name field? ===' AS section;

WITH RECURSIVE tree AS (
  SELECT id, name, parent_comp_def_id
  FROM fw.comp_def
  WHERE core_id = 22 AND parent_comp_def_id IS NULL AND is_active = TRUE
  UNION ALL
  SELECT cd.id, cd.name, cd.parent_comp_def_id
  FROM fw.comp_def cd JOIN tree t ON cd.parent_comp_def_id = t.id
  WHERE cd.is_active = TRUE
)
SELECT id, name FROM tree WHERE name = 'login_name';
-- Expected: 0 rows (nemam co addovat) -> pokracovat. Pokud 1 row, skip INSERT.


-- ── Step 4: comp_type id pro 'input' field ──────────────────────────────
SELECT '=== Step 4: comp_type input id ===' AS section;

SELECT id, code, label, kind
FROM fw.comp_type
WHERE code IN ('input', 'edit', 'text_input')
  AND is_active = TRUE
ORDER BY id;
-- Expected: 1 row (asi id=1 'edit' nebo id=100 'input' — pouzij ten co maji
-- existing first_name/last_name fields v Step 2 vystupu).
