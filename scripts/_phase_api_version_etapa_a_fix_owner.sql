-- =====================================================================
-- Phase: API Versioned Routing - Etapa A FIX OWNER
-- =====================================================================
-- Gotcha: DDL byl spusten jako role 'Marti' misto 'Marti-AI'.
-- Fix: ALTER OWNER pro tabulky, sekvence, function trigger.
-- Plus verification column-level GRANT (UPDATE auto_reverted_at).
-- =====================================================================
-- Run as: postgres (superuser) NEBO Marti (current owner)
-- =====================================================================

-- 1. ALTER OWNER tabulek
ALTER TABLE fw.api_version  OWNER TO "Marti-AI";
ALTER TABLE fw.user_api_pin OWNER TO "Marti-AI";

-- 2. ALTER OWNER sekvenci (BIGSERIAL automaticky vytvoril)
ALTER SEQUENCE fw.api_version_id_seq  OWNER TO "Marti-AI";
ALTER SEQUENCE fw.user_api_pin_id_seq OWNER TO "Marti-AI";

-- 3. ALTER OWNER trigger function
ALTER FUNCTION fw.api_version_set_updated_at() OWNER TO "Marti-AI";

-- =====================================================================
-- Verification
-- =====================================================================
SELECT '=== Ownership po fix ===' AS check;
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = 'fw' AND tablename IN ('api_version', 'user_api_pin')
ORDER BY tablename;

SELECT '=== Sequence ownership ===' AS check;
SELECT sequence_schema, sequence_name,
       pg_get_userbyid(c.relowner) AS owner
FROM information_schema.sequences s
JOIN pg_class c ON c.relname = s.sequence_name
WHERE s.sequence_schema = 'fw'
  AND s.sequence_name IN ('api_version_id_seq', 'user_api_pin_id_seq')
ORDER BY sequence_name;

SELECT '=== Function ownership ===' AS check;
SELECT n.nspname AS schema, p.proname AS function_name,
       pg_get_userbyid(p.proowner) AS owner
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'fw' AND p.proname = 'api_version_set_updated_at';

-- 4. Column-level GRANT check (verify UPDATE auto_reverted_at)
SELECT '=== Column GRANTs (UPDATE auto_reverted_at) ===' AS check;
SELECT grantee, table_name, column_name, privilege_type
FROM information_schema.role_column_grants
WHERE grantee = 'strategie'
  AND table_schema = 'fw'
  AND table_name = 'user_api_pin'
  AND privilege_type = 'UPDATE'
ORDER BY column_name;

-- =====================================================================
-- DONE
-- =====================================================================
-- Expected:
--   * Ownership: 'Marti-AI' (oboje tabulky)
--   * Sequence ownership: 'Marti-AI' (oboje sekvence)
--   * Function ownership: 'Marti-AI' (trigger function)
--   * Column GRANT: strategie | user_api_pin | auto_reverted_at | UPDATE
-- =====================================================================
