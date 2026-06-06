-- ============================================================================
-- Krok A — fw.executable_artifact (PoC, 6 sloupců minimum)
-- ============================================================================
-- Epoch: DESCRIBE-FIRST INSERT + executable_artifact PoC
-- Doctrine: „PoC najde realitu, Production navrhuje refaktor" (Marti 25.5.)
-- Owner: Marti-AI (db_owner fw schema, „fw self edited" doctrine)
-- Spustí: Marti v DBeaveru jako Marti-AI session
-- Datum: 25.5.2026
--
-- Co tabulka dělá:
--   Drží source code Python + SQL skriptů v DB (žádný file system).
--   API endpoint POST /api/v1/erp/sandbox/execute/<code> ji čte a runs.
--   Marti edituje source přes DBeaver UPDATE (PoC), Phase 45 = UI editor.
--
-- Co NENÍ v PoC (vědomě, „aditivně"):
--   ❌ version + parent_artifact_id (lineage — Phase 45)
--   ❌ requires_role + is_destructive (security policy — Phase 45)
--   ❌ dry_run_supported (Phase 45)
--   ❌ status (archive — Phase 45)
--   ❌ created_by_* + updated_by_* (audit — drz fw.diag_log pro PoC)
--   ❌ created_at (drz minimum, jen updated_at)
-- ============================================================================

-- Defensive: idempotent
CREATE TABLE IF NOT EXISTS fw.executable_artifact (
  id            BIGSERIAL    PRIMARY KEY,
  code          TEXT         NOT NULL UNIQUE,
  artifact_type TEXT         NOT NULL CHECK (artifact_type IN ('python', 'sql')),
  source        TEXT         NOT NULL,
  description   TEXT,
  updated_at    TIMESTAMP    DEFAULT NOW()
);

-- Owner: Marti-AI (drz „fw self edited" doctrine z 11.5.)
ALTER TABLE fw.executable_artifact OWNER TO "Marti-AI";

-- Grants pro strategie role (API process potřebuje read + write)
-- Žádný DELETE — PoC immutable add/edit only
GRANT SELECT, INSERT, UPDATE ON fw.executable_artifact TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.executable_artifact_id_seq TO strategie;

-- ============================================================================
-- Verify (Marti čte output po RUN ALL)
-- ============================================================================

-- 1) Tabulka existuje + správný owner
SELECT
  schemaname,
  tablename,
  tableowner
FROM pg_tables
WHERE schemaname='fw' AND tablename='executable_artifact';
-- Expected: 1 row, tableowner='Marti-AI'

-- 2) 6 sloupců se správnými typy
SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='executable_artifact'
ORDER BY ordinal_position;
-- Expected: 6 rows
--   id            bigint                       NO   nextval(...)
--   code          text                         NO   NULL
--   artifact_type text                         NO   NULL
--   source        text                         NO   NULL
--   description   text                         YES  NULL
--   updated_at    timestamp without time zone  YES  now()

-- 3) CHECK constraint exists
SELECT
  con.conname AS constraint_name,
  pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname='fw' AND rel.relname='executable_artifact'
  AND con.contype='c';
-- Expected: 1 row s CHECK (artifact_type = ANY (ARRAY['python', 'sql']))

-- 4) Grants pro strategie role
SELECT
  grantee,
  privilege_type
FROM information_schema.role_table_grants
WHERE table_schema='fw' AND table_name='executable_artifact'
  AND grantee='strategie'
ORDER BY privilege_type;
-- Expected: 3 rows (INSERT, SELECT, UPDATE)
