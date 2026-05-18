-- Phase 38.4 Krok 5.R-C+10 (18.5.2026 vecer pozde): rename fw.comp_def
-- parent_core_id → core_id + UNIQUE constraint.
--
-- Marti's doctrine: prevence proti save flow chybe ktera prepisuje
-- core_id picker komponenty (root association) hodnotou z user picku.
-- Aktualne fw.comp_def ma 3 root rows (parent_core_id IN (22, 30, 23)),
-- zadne duplicity.
--
-- Spustit jako member of fw_owners (Marti nebo Marti-AI) v DBeaveru.
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 0: HOTFIX (18.5.2026 vecer pozde) — DELETE orphan prototype
-- ════════════════════════════════════════════════════════════════════════════
-- comp_def id=1 (AG_Grid prototype) z Krok 13 epoch (10.5.2026): BOTH parent
-- fields NULL → CHECK constraint violation. Marti confirmed: "Ne, nikde nic"
-- (zero FK references na id=1). AG_Grid registrace patri do fw.comp_type
-- id=11, ne do fw.comp_def. Cleanup pred ADD CONSTRAINT.

DELETE FROM fw.comp_def WHERE id = 1;
-- expected: DELETE 1

-- ════════════════════════════════════════════════════════════════════════════
-- Step 1: Audit pre-rename — confirm zadne duplicity v parent_core_id
-- ════════════════════════════════════════════════════════════════════════════

-- Expected: 0 rows (pokud > 0, NUTNE cleanup pred UNIQUE constraint)
SELECT parent_core_id, COUNT(*) AS cnt
  FROM fw.comp_def
 WHERE parent_core_id IS NOT NULL
 GROUP BY parent_core_id
HAVING COUNT(*) > 1;

-- Snapshot pre-rename stavu (Marti's audit reference):
SELECT id, name, type_id, parent_core_id, parent_comp_def_id, is_active
  FROM fw.comp_def
 WHERE parent_core_id IS NOT NULL
 ORDER BY parent_core_id, id;
-- expected: 3 rows (core 22, 30, 23)

-- Post-DELETE counters (sanity):
SELECT
  COUNT(*) FILTER (WHERE parent_core_id IS NOT NULL AND parent_comp_def_id IS NULL) AS root_ok,
  COUNT(*) FILTER (WHERE parent_core_id IS NULL AND parent_comp_def_id IS NOT NULL) AS child_ok,
  COUNT(*) FILTER (WHERE parent_core_id IS NOT NULL AND parent_comp_def_id IS NOT NULL) AS dual_violation,
  COUNT(*) FILTER (WHERE parent_core_id IS NULL AND parent_comp_def_id IS NULL) AS orphan_violation,
  COUNT(*) AS total
FROM fw.comp_def;
-- expected: root_ok=3, child_ok=38, dual=0, orphan=0, total=41

-- ════════════════════════════════════════════════════════════════════════════
-- Step 2: RENAME COLUMN parent_core_id → core_id
-- ════════════════════════════════════════════════════════════════════════════

ALTER TABLE fw.comp_def RENAME COLUMN parent_core_id TO core_id;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 3: Update CHECK constraint (drop + add s novym field name)
-- ════════════════════════════════════════════════════════════════════════════

ALTER TABLE fw.comp_def DROP CONSTRAINT IF EXISTS chk_comp_def_single_parent;

ALTER TABLE fw.comp_def ADD CONSTRAINT chk_comp_def_single_parent
    CHECK (
        (core_id IS NOT NULL AND parent_comp_def_id IS NULL)
     OR (core_id IS NULL AND parent_comp_def_id IS NOT NULL)
    );

-- ════════════════════════════════════════════════════════════════════════════
-- Step 4: UNIQUE partial index — 1 root component per fw.core (1:1)
-- NULL allowed pro child rows (parent_comp_def_id set, core_id NULL)
-- ════════════════════════════════════════════════════════════════════════════

CREATE UNIQUE INDEX ux_comp_def_core_id_unique
    ON fw.comp_def (core_id)
    WHERE core_id IS NOT NULL;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Verify final state
-- ════════════════════════════════════════════════════════════════════════════

-- Confirm column renamed
SELECT column_name FROM information_schema.columns
 WHERE table_schema = 'fw' AND table_name = 'comp_def'
   AND column_name IN ('core_id', 'parent_core_id');
-- expected: 1 row (core_id)

-- Confirm CHECK constraint
SELECT con.conname, pg_get_constraintdef(con.oid)
  FROM pg_constraint con
  JOIN pg_class cl ON con.conrelid = cl.oid
  JOIN pg_namespace ns ON cl.relnamespace = ns.oid
 WHERE ns.nspname = 'fw' AND cl.relname = 'comp_def'
   AND con.conname = 'chk_comp_def_single_parent';
-- expected: 1 row, definition uses "core_id" (ne parent_core_id)

-- Confirm UNIQUE index
SELECT indexname, indexdef FROM pg_indexes
 WHERE schemaname = 'fw' AND tablename = 'comp_def'
   AND indexname = 'ux_comp_def_core_id_unique';
-- expected: 1 row

-- Data integrity check (3 root rows pres core_id 22, 30, 23):
SELECT id, name, type_id, core_id, parent_comp_def_id, is_active
  FROM fw.comp_def
 WHERE core_id IS NOT NULL
 ORDER BY core_id, id;
-- expected: 3 rows

-- ════════════════════════════════════════════════════════════════════════════
-- Next: deploy code rename via apply script
-- (router.py: 20 refs parent_core_id → core_id)
-- ════════════════════════════════════════════════════════════════════════════
