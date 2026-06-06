-- ============================================================================
-- Krok G+ CLEANUP — junk fw.core #50 + ops #38, #39 (z buggy smoke 25.5. 22:00)
-- ============================================================================
-- Marti's volba A (destruktivni):
--   - Drop fw.core #50 (label "Operace data sourcu #35" linked to Diag log #39 ops)
--   - Drop fw.data_source_op #38 (edit, data_source_id=39)
--   - Drop fw.data_source_op #39 (insert, data_source_id=39)
--
-- Po cleanup Diag log se vrati do EDIT NEEXISTUJE state.
-- Pristi orchestrator klik z Diag log gridu (po G++ defensive deploy)
-- vytvori spravne s label "Editace: Diag log".
--
-- Transaction wrap pro atomic delete (rollback if anything fails).
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ── Step 1: Verify pre-state ────────────────────────────────────────────────
-- (Tyhle SELECTy jsou jen pro Marti's visibility, nemodifikuji nic.)
\echo '=== PRE-STATE: ops s core_id=50 ==='
SELECT id, data_source_id, operation_kind, core_id, description
FROM fw.data_source_op
WHERE core_id = 50
ORDER BY id;
-- Expected: 2 rows (#38 edit + #39 insert)

\echo '=== PRE-STATE: fw.core #50 ==='
SELECT id, code, label, description_user
FROM fw.core
WHERE id = 50;
-- Expected: 1 row, code=NULL, label='Editace: Operace data sourcu #35'

-- ── Step 2: DELETE ops first (FK dependency on fw.core) ─────────────────────
DELETE FROM fw.data_source_op WHERE id IN (38, 39);
-- Expected: DELETE 2

-- ── Step 3: DELETE fw.core ──────────────────────────────────────────────────
DELETE FROM fw.core WHERE id = 50;
-- Expected: DELETE 1

-- ── Step 4: Verify post-state ───────────────────────────────────────────────
\echo '=== POST-STATE: ops pro data_source_id=39 (Diag log) ==='
SELECT id, operation_kind, variant_code, core_id, description
FROM fw.data_source_op
WHERE data_source_id = 39
ORDER BY id;
-- Expected: jen #21 select (puvodni op zustava)

\echo '=== POST-STATE: fw.core #50 ==='
SELECT id, label FROM fw.core WHERE id = 50;
-- Expected: 0 rows

\echo '=== POST-STATE: hleda jakekoliv stale junk cores z 25.5. ==='
SELECT id, code, label, created_at
FROM fw.core
WHERE description_user ILIKE '%Auto-vytvoreno orchestratorem%'
   OR description_user ILIKE '%vytvor_edit_jadro%'
ORDER BY id;
-- Expected: 0 rows (zadne dalsi junk)

COMMIT;

\echo '=== CLEANUP DONE ==='
\echo 'Diag log je teď v EDIT NEEXISTUJE state. Pristi orchestrator klik vytvori spravne.'
