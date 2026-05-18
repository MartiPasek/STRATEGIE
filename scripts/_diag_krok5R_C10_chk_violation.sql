-- Phase 38.4 Krok 5.R-C+10 hotfix diagnostic: CHECK violation audit
-- ════════════════════════════════════════════════════════════════════════════
-- Marti's DDL failed: chk_comp_def_single_parent constraint violated.
-- Old constraint pravdepodobne pridana NOT VALID (skip pre-existing rows),
-- nova ADD CONSTRAINT validuje VSECHNY rows → 1+ row je orphan nebo dual.
--
-- Po ROLLBACK column je zpet `parent_core_id` (rename byl uvnitr failed tx).
-- ════════════════════════════════════════════════════════════════════════════

-- ════════════════════════════════════════════════════════════════════════════
-- 1) Counters — kolik orphans / dual-parents / OK
-- ════════════════════════════════════════════════════════════════════════════

SELECT
  COUNT(*) FILTER (WHERE parent_core_id IS NOT NULL AND parent_comp_def_id IS NOT NULL) AS dual_parent,
  COUNT(*) FILTER (WHERE parent_core_id IS NULL AND parent_comp_def_id IS NULL) AS orphan,
  COUNT(*) FILTER (WHERE (parent_core_id IS NOT NULL) <> (parent_comp_def_id IS NOT NULL)) AS ok_single_parent,
  COUNT(*) AS total
FROM fw.comp_def;

-- ════════════════════════════════════════════════════════════════════════════
-- 2) Full audit — ALL violating rows (DUAL_PARENT or ORPHAN)
-- ════════════════════════════════════════════════════════════════════════════

SELECT
  id, name, code, type_id,
  parent_core_id,
  parent_comp_def_id,
  is_active,
  created_at,
  updated_at,
  CASE
    WHEN parent_core_id IS NOT NULL AND parent_comp_def_id IS NOT NULL THEN 'DUAL_PARENT'
    WHEN parent_core_id IS NULL     AND parent_comp_def_id IS NULL     THEN 'ORPHAN'
    ELSE 'OK'
  END AS violation
FROM fw.comp_def
WHERE NOT (
      (parent_core_id IS NOT NULL AND parent_comp_def_id IS NULL)
   OR (parent_core_id IS NULL AND parent_comp_def_id IS NOT NULL)
)
ORDER BY violation, is_active DESC, type_id, id;

-- ════════════════════════════════════════════════════════════════════════════
-- 3) Per-violation breakdown s parent context (pro dual-parent — orphan
--    co tam predtim "patril")
-- ════════════════════════════════════════════════════════════════════════════

-- Pro DUAL_PARENT: zobrazí oba parent candidates
SELECT
  cd.id, cd.name, cd.type_id,
  cd.parent_core_id, c.name AS core_name,
  cd.parent_comp_def_id, p.name AS parent_comp_def_name,
  cd.is_active
FROM fw.comp_def cd
LEFT JOIN fw.core c    ON c.id = cd.parent_core_id
LEFT JOIN fw.comp_def p ON p.id = cd.parent_comp_def_id
WHERE cd.parent_core_id IS NOT NULL AND cd.parent_comp_def_id IS NOT NULL
ORDER BY cd.id;

-- Pro ORPHAN: zobrazí kontext (možná soft-deleted parent?)
SELECT
  cd.id, cd.name, cd.type_id, cd.is_active,
  cd.created_at, cd.updated_at,
  ct.code AS type_code, ct.label AS type_label
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE cd.parent_core_id IS NULL AND cd.parent_comp_def_id IS NULL
ORDER BY cd.is_active DESC, cd.id;

-- ════════════════════════════════════════════════════════════════════════════
-- 4) Check existing constraint definition (možná byla NOT VALID)
-- ════════════════════════════════════════════════════════════════════════════

SELECT con.conname,
       con.convalidated,
       pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class cl    ON con.conrelid = cl.oid
JOIN pg_namespace ns ON cl.relnamespace = ns.oid
WHERE ns.nspname = 'fw'
  AND cl.relname = 'comp_def'
  AND con.conname = 'chk_comp_def_single_parent';
-- convalidated=true → enforced i pro existing rows
-- convalidated=false → NOT VALID (skip pre-existing) — pravdepodobne tady
