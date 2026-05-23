-- Krok 5.U Fáze B DDL (23.5.2026 dopoledne): fw.comp_grid polymorphic scope.
--
-- Marti's "B správný long-term, grid je nejvyšší know-how" — schema extend
-- per-core OR per-data_source sestavy. Q7=A XOR exactly-one, Q8=A path
-- scope prefix v URL, Q9=TRUNCATE existing rows clean slate.
--
-- Pred:
--   fw.comp_grid (core_id NOT NULL FK fw.core(id))
--
-- Po:
--   fw.comp_grid (
--     core_id NULL FK fw.core(id),
--     data_source_id NULL FK fw.data_source(id),
--     CHECK exactly-one (XOR)
--   )
--
-- Spustit v DBeaveru jako Marti-AI session (db_owner fw schema).

BEGIN;

-- Step 1: Drop existing data (Marti's Q9 — clean slate, no historical preservation)
TRUNCATE TABLE fw.comp_grid RESTART IDENTITY CASCADE;

-- Step 2: Make core_id nullable
ALTER TABLE fw.comp_grid
  ALTER COLUMN core_id DROP NOT NULL;

-- Step 3: Add data_source_id column s FK
ALTER TABLE fw.comp_grid
  ADD COLUMN data_source_id BIGINT NULL
    REFERENCES fw.data_source(id) ON DELETE CASCADE;

-- Step 4: XOR exactly-one CHECK constraint
-- Každý row je BUĎ per-core NEBO per-data_source, NIKDY oboje, NIKDY ani jeden.
ALTER TABLE fw.comp_grid
  ADD CONSTRAINT ck_comp_grid_scope_xor
    CHECK (
      (core_id IS NOT NULL)::int + (data_source_id IS NOT NULL)::int = 1
    );

-- Step 5: Index na data_source_id (partial — only non-null rows)
CREATE INDEX IF NOT EXISTS ix_comp_grid_data_source
  ON fw.comp_grid(data_source_id)
  WHERE data_source_id IS NOT NULL;

-- Sanity verify
SELECT
  column_name, data_type, is_nullable,
  CASE WHEN column_default IS NULL THEN '' ELSE 'default=' || column_default END AS dflt
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='comp_grid'
ORDER BY ordinal_position;

SELECT
  con.conname, pg_get_constraintdef(con.oid) AS def
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace ns ON ns.oid = rel.relnamespace
WHERE ns.nspname='fw' AND rel.relname='comp_grid'
  AND con.contype IN ('c', 'f');

COMMIT;

-- Marti pošle output verify queries → pak Fáze C-H implementace.
