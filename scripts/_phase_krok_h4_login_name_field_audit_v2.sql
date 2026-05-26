-- ============================================================================
-- Krok H+4 follow-up v2 — Audit fw.comp_def pro user_edit (core_id=22)
-- ============================================================================
-- v1 selhal: column "is_active" does not exist
-- v2 fix: nejdriv introspect schema, pak audit bez is_active filtru
-- ============================================================================

-- ── Step 0: Introspect fw.comp_def schema ────────────────────────────────
SELECT '=== Step 0: fw.comp_def REAL columns ===' AS section;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name = 'comp_def'
ORDER BY ordinal_position;


-- ── Step 1: form root pod core_id=22 (bez is_active filtru) ──────────────
SELECT '=== Step 1: Form root (core_id=22) ===' AS section;

SELECT id, name, caption, type_id, parent_comp_def_id, core_id,
       region_slot, sort_order
FROM fw.comp_def
WHERE core_id = 22
  AND parent_comp_def_id IS NULL
ORDER BY sort_order, id;


-- ── Step 2: full tree pod core_id=22 (bez is_active filtru) ──────────────
SELECT '=== Step 2: All comp_def descendants ===' AS section;

WITH RECURSIVE tree AS (
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         cd.sort_order, cd.region_slot, 0 AS depth
  FROM fw.comp_def cd
  WHERE cd.core_id = 22
    AND cd.parent_comp_def_id IS NULL
  UNION ALL
  SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.parent_comp_def_id,
         cd.sort_order, cd.region_slot, t.depth + 1
  FROM fw.comp_def cd
  JOIN tree t ON cd.parent_comp_def_id = t.id
)
SELECT id, name, caption, type_id, parent_comp_def_id,
       sort_order, region_slot, depth
FROM tree
ORDER BY depth, parent_comp_def_id NULLS FIRST, sort_order, id;


-- ── Step 3: comp_type lookup pro 'input' / 'edit' ────────────────────────
SELECT '=== Step 3: comp_type input candidates ===' AS section;

SELECT id, code, label, kind
FROM fw.comp_type
WHERE code IN ('input', 'edit', 'text_input', 'TEdit')
ORDER BY id;


-- ── Step 4: Idempotence — uz existuje login_name? ────────────────────────
SELECT '=== Step 4: login_name field already exists? ===' AS section;

WITH RECURSIVE tree AS (
  SELECT id, name, parent_comp_def_id
  FROM fw.comp_def
  WHERE core_id = 22 AND parent_comp_def_id IS NULL
  UNION ALL
  SELECT cd.id, cd.name, cd.parent_comp_def_id
  FROM fw.comp_def cd JOIN tree t ON cd.parent_comp_def_id = t.id
)
SELECT id, name FROM tree WHERE name = 'login_name';
-- Expected: 0 rows (nepridana). Pokud 1 row -> skip INSERT.
