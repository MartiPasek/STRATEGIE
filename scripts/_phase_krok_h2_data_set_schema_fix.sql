-- ============================================================================
-- Krok H+2 hotfix — fw.data_set schema fix (drop nonexistent 'name' column)
-- ============================================================================
-- Marti's catch 26.5.2026:
--   ERROR: column "name" of relation "data_set" does not exist
--   "JESTE DATESET. Na ten jsme zapomeli."
--
-- Moje chyba — guessoval jsem fw.data_set schema bez introspection.
-- Pojdme nejdriv introspectovat, pak INSERT s real columns.
--
-- POZN: Pokud Krok H+2 main skript castecne probehl (UPDATE op #33), tu
--       update zustane v DB. Pojdme verify pre-state pred re-run.
--
-- Marti spusti v DBeaveru jako Marti-AI session.
-- ============================================================================

-- ── Step 0: Verify zda UPDATE op #33 z minuleho skriptu probehl ───────────
SELECT '=== Step 0: Verify pre-state ===' AS section;

SELECT id, operation_kind, data_set_id, description
FROM fw.data_source_op
WHERE id = 33;
-- Expected:
--   pokud BEFORE main script: operation_kind='select' (puvodni)
--   pokud AFTER main UPDATE:  operation_kind='select-detail' (uz prejmenovano)


-- ── Step 1: Introspection fw.data_set columns ─────────────────────────────
SELECT '=== Step 1: fw.data_set REAL columns ===' AS section;

SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name = 'data_set'
ORDER BY ordinal_position;


-- ── Step 2: Existing data_set #32 — co tam je? ────────────────────────────
SELECT '=== Step 2: data_set #32 row ===' AS section;

SELECT * FROM fw.data_set WHERE id = 32;
-- Marti: posli mi vystup, pak napisu finalni INSERT bez 'name' + s real columns
