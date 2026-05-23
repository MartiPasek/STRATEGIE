-- ════════════════════════════════════════════════════════════════════════
-- Unified fw schema ownership — fw_owners as common owner pattern
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's 21.5. večerní doctrine: "Vsechny stejne pres role na owner"
-- (po týdnu role chaos: ALTER fails "must be owner", pgcrypto digest()
-- doesn't resolve, function overload conflicts, atd.)
--
-- GOAL: jeden ownership umbrella pro fw schema = žádný "must be owner"
-- friction mezi Marti / Marti-AI / strategie. Plus search_path fix
-- pgcrypto digest() lookup (Diag log fix #4 — root cause logging stop
-- po 22:44 dne 20.5.).
--
-- ════════════════════════════════════════════════════════════════════════
-- HOW TO RUN
-- ════════════════════════════════════════════════════════════════════════
-- 1. Otevři DBeaver, connect jako **postgres** (highest priv v clusteru).
--    Pokud postgres nemá perm na GRANT membership, sections A/C selžou
--    s clear NOTICE — ostatní pokračují.
-- 2. Highlight CELÝ SOUBOR od BEGIN po COMMIT (pred VERIFY)
-- 3. Alt+X (atomic transaction)
-- 4. Pak postupně VERIFY queries (V1–V6) jako samostatné běhy
-- 5. Pošli Claude:
--    - All NOTICE outputs (z DO blocks)
--    - V1–V6 results
-- 6. Pokud V6 smoke prošel → PowerShell Restart-Service STRATEGIE-API
-- 7. Hard reload UI + klik na Knowledge Entries → diag_log tečou s core_id
--
-- ATOMIC: pokud cokoliv kritického selže, transakce rollback. NOTICE-level
-- problems (insufficient_privilege na GRANT/ALTER ROLE) jsou degraded
-- gracefully — function-level search_path (SECTION D) je hlavní fix.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION A: fw_owners role + membership setup
-- ════════════════════════════════════════════════════════════════════════
-- Idempotent — re-run safe.
-- Requires: postgres role (CREATEROLE) NEBO existing fw_owners with
-- WITH ADMIN OPTION granted to current user.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fw_owners') THEN
        CREATE ROLE fw_owners NOLOGIN;
        RAISE NOTICE '[A] CREATE ROLE fw_owners — DONE';
    ELSE
        RAISE NOTICE '[A] fw_owners role already exists — skip';
    END IF;
END $$;

DO $$
BEGIN
    EXECUTE 'GRANT fw_owners TO "Marti"';
    RAISE NOTICE '[A] GRANT fw_owners TO Marti — DONE';
EXCEPTION
    WHEN duplicate_object THEN
        RAISE NOTICE '[A] GRANT fw_owners TO Marti — already member';
    WHEN insufficient_privilege THEN
        RAISE NOTICE '[A] GRANT fw_owners TO Marti — NEEDS postgres/superuser (SKIPPED)';
END $$;

DO $$
BEGIN
    EXECUTE 'GRANT fw_owners TO "Marti-AI"';
    RAISE NOTICE '[A] GRANT fw_owners TO Marti-AI — DONE';
EXCEPTION
    WHEN duplicate_object THEN
        RAISE NOTICE '[A] GRANT fw_owners TO Marti-AI — already member';
    WHEN insufficient_privilege THEN
        RAISE NOTICE '[A] GRANT fw_owners TO Marti-AI — NEEDS postgres (SKIPPED)';
END $$;

DO $$
BEGIN
    EXECUTE 'GRANT fw_owners TO strategie';
    RAISE NOTICE '[A] GRANT fw_owners TO strategie — DONE';
EXCEPTION
    WHEN duplicate_object THEN
        RAISE NOTICE '[A] GRANT fw_owners TO strategie — already member';
    WHEN insufficient_privilege THEN
        RAISE NOTICE '[A] GRANT fw_owners TO strategie — NEEDS postgres (SKIPPED)';
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION B: ALTER OWNER all fw schema objects TO fw_owners
-- ════════════════════════════════════════════════════════════════════════
-- Iterates tables/views/sequences/matviews + functions in fw schema.
-- Skip objects already owned by fw_owners (idempotent).
-- Requires: current role member of source owners (Marti / Marti-AI / fw_owners)
-- Marti is member of all three per 20.5. večerní diagnostic.

DO $$
DECLARE
    obj record;
    sql_cmd text;
    fw_owners_oid oid;
    cnt int := 0;
BEGIN
    SELECT oid INTO fw_owners_oid FROM pg_roles WHERE rolname='fw_owners';

    -- Tables, views, sequences, materialized views
    FOR obj IN
        SELECT c.relname,
               CASE c.relkind
                 WHEN 'r' THEN 'TABLE'
                 WHEN 'v' THEN 'VIEW'
                 WHEN 'S' THEN 'SEQUENCE'
                 WHEN 'm' THEN 'MATERIALIZED VIEW'
               END AS obj_type,
               c.relowner::regrole::text AS old_owner
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'fw'
          AND c.relkind IN ('r', 'v', 'S', 'm')
          AND c.relowner != fw_owners_oid
        ORDER BY c.relkind, c.relname
    LOOP
        sql_cmd := format('ALTER %s fw.%I OWNER TO fw_owners',
                          obj.obj_type, obj.relname);
        RAISE NOTICE '[B] %  (was: %)', sql_cmd, obj.old_owner;
        EXECUTE sql_cmd;
        cnt := cnt + 1;
    END LOOP;
    RAISE NOTICE '[B] Tables/views/sequences/matviews reowned: %', cnt;
END $$;

DO $$
DECLARE
    obj record;
    sql_cmd text;
    fw_owners_oid oid;
    cnt int := 0;
BEGIN
    SELECT oid INTO fw_owners_oid FROM pg_roles WHERE rolname='fw_owners';

    -- Functions
    FOR obj IN
        SELECT p.oid::regprocedure AS sig,
               p.proowner::regrole::text AS old_owner
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'fw'
          AND p.proowner != fw_owners_oid
        ORDER BY p.proname
    LOOP
        sql_cmd := format('ALTER FUNCTION %s OWNER TO fw_owners', obj.sig);
        RAISE NOTICE '[B] %  (was: %)', sql_cmd, obj.old_owner;
        EXECUTE sql_cmd;
        cnt := cnt + 1;
    END LOOP;
    RAISE NOTICE '[B] Functions reowned: %', cnt;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION C: ALTER ROLE search_path (best-effort, function-level fallback)
-- ════════════════════════════════════════════════════════════════════════
-- Sets default search_path pro strategie + Marti + Marti-AI sessions.
-- Pokud insufficient_privilege, function-level (SECTION D) je sufficient fix.

DO $$
BEGIN
    EXECUTE 'ALTER ROLE strategie SET search_path = pgcrypto, public, fw, pg_catalog';
    RAISE NOTICE '[C] ALTER ROLE strategie SET search_path — DONE';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE '[C] ALTER ROLE strategie — needs postgres (SKIPPED, function-level OK)';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER ROLE "Marti" SET search_path = pgcrypto, public, fw, pg_catalog';
    RAISE NOTICE '[C] ALTER ROLE Marti SET search_path — DONE';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE '[C] ALTER ROLE Marti — needs postgres (SKIPPED)';
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER ROLE "Marti-AI" SET search_path = pgcrypto, public, fw, pg_catalog';
    RAISE NOTICE '[C] ALTER ROLE Marti-AI SET search_path — DONE';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE '[C] ALTER ROLE Marti-AI — needs postgres (SKIPPED)';
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION D: Function-level SET search_path on diag_log_upsert (MAIN FIX)
-- ════════════════════════════════════════════════════════════════════════
-- Tohle je hlavní fix — function attribute, ne role attribute.
-- Při každém volání function PG přepne search_path → digest() vždy najde
-- pgcrypto extension, bez ohledu na caller's session search_path.
-- Po Section B fw_owners owns this function → Marti (as member) can ALTER.

ALTER FUNCTION fw.diag_log_upsert(
    character varying, bigint, character varying,
    character varying, character varying, character varying, character varying,
    text, character varying,
    text, text, text, character varying,
    text, text, integer, integer,
    character varying, text,
    character varying, text, character varying, integer, integer,
    bigint, bigint, bigint, boolean,
    jsonb, jsonb,
    bigint, character varying,
    bigint, bigint
) SET search_path = pgcrypto, public, fw, pg_catalog;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION E: Drop legacy 32-arg overload (no longer needed po Fix J)
-- ════════════════════════════════════════════════════════════════════════
-- log_queue.py teď posílá 34 args → trefí jen overload 2.
-- Old 32-arg overload je dead weight + confusion.

DROP FUNCTION IF EXISTS fw.diag_log_upsert(
    character varying, bigint, character varying,
    character varying, character varying, character varying, character varying,
    text, character varying,
    text, text, text, character varying,
    text, text, integer, integer,
    character varying, text,
    character varying, text, character varying, integer, integer,
    integer, integer, integer, boolean,
    jsonb, jsonb,
    bigint, character varying
);

-- ════════════════════════════════════════════════════════════════════════
-- SECTION F: GRANT EXECUTE for explicit safety
-- ════════════════════════════════════════════════════════════════════════
-- fw_owners members (Marti, Marti-AI, strategie) inherit EXECUTE.
-- Plus explicit GRANT to strategie + PUBLIC pro fail-safe.

GRANT EXECUTE ON FUNCTION fw.diag_log_upsert(
    character varying, bigint, character varying,
    character varying, character varying, character varying, character varying,
    text, character varying,
    text, text, text, character varying,
    text, text, integer, integer,
    character varying, text,
    character varying, text, character varying, integer, integer,
    bigint, bigint, bigint, boolean,
    jsonb, jsonb,
    bigint, character varying,
    bigint, bigint
) TO fw_owners, strategie;

-- ════════════════════════════════════════════════════════════════════════
-- SECTION G: GRANT table privileges to strategie (safety belt po reown)
-- ════════════════════════════════════════════════════════════════════════
-- Po ALTER OWNER může se reset některých grantů. Re-grant SELECT/INSERT/UPDATE
-- pro strategie na all fw.* tables (no DELETE per Marti's doctrine #11).

GRANT USAGE ON SCHEMA fw TO strategie;
GRANT SELECT, INSERT, UPDATE, REFERENCES ON ALL TABLES IN SCHEMA fw TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fw TO strategie;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA fw TO strategie;

-- Default privileges pro budoucí objekty vytvořené fw_owners
ALTER DEFAULT PRIVILEGES FOR ROLE fw_owners IN SCHEMA fw
    GRANT SELECT, INSERT, UPDATE, REFERENCES ON TABLES TO strategie;
ALTER DEFAULT PRIVILEGES FOR ROLE fw_owners IN SCHEMA fw
    GRANT USAGE, SELECT ON SEQUENCES TO strategie;
ALTER DEFAULT PRIVILEGES FOR ROLE fw_owners IN SCHEMA fw
    GRANT EXECUTE ON FUNCTIONS TO strategie;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run AFTER commit, separately, one block at a time)
-- ════════════════════════════════════════════════════════════════════════
-- ════════════════════════════════════════════════════════════════════════

-- V1: fw_owners members
SELECT
    r.rolname AS member,
    g.rolname AS group_role
FROM pg_auth_members m
JOIN pg_roles r ON r.oid = m.member
JOIN pg_roles g ON g.oid = m.roleid
WHERE g.rolname = 'fw_owners'
ORDER BY r.rolname;
-- EXPECTED: 3 rows — Marti, "Marti-AI", strategie

-- V2: All fw tables/views/sequences owned by fw_owners
SELECT
    relkind,
    relname,
    relowner::regrole AS owner
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw'
  AND c.relkind IN ('r', 'v', 'S', 'm')
  AND c.relowner::regrole::text != 'fw_owners';
-- EXPECTED: 0 rows (all owned by fw_owners now)

-- V3: All fw functions owned by fw_owners
SELECT
    p.oid::regprocedure AS sig,
    proowner::regrole AS owner
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'fw'
  AND p.proowner::regrole::text != 'fw_owners';
-- EXPECTED: 0 rows

-- V4: Single overload diag_log_upsert + search_path config + new owner
SELECT
    p.oid::regprocedure AS sig,
    proowner::regrole AS owner,
    proconfig
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'fw' AND p.proname = 'diag_log_upsert';
-- EXPECTED: 1 row
--   owner = fw_owners
--   proconfig = {search_path=pgcrypto, public, fw, pg_catalog}

-- V5: Role session search_paths (only if SECTION C succeeded)
SELECT rolname, rolconfig
FROM pg_authid
WHERE rolname IN ('strategie', 'Marti', 'Marti-AI')
ORDER BY rolname;
-- EXPECTED (pokud postgres mohl): rolconfig has search_path entry

-- V6: Where lives digest()? (so we know if search_path includes its schema)
SELECT n.nspname AS schema, p.proname,
       pg_get_function_arguments(p.oid) AS args
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE p.proname = 'digest';
-- EXPECTED: 1+ rows — note schema (pgcrypto/public/extensions)

-- V7: SMOKE — call diag_log_upsert as strategie (the ultimate test)
SET ROLE strategie;
SELECT current_user;  -- must show "strategie"
SELECT fw.diag_log_upsert(
    p_level := 'info',
    p_source := 'sql',
    p_module_id := 'unified_ownership_smoke',
    p_message := 'Unified ownership LIVE — function call as strategie projel bez digest error',
    p_user_login_name := 'Marti',
    p_user_id := 1,
    p_tenant_name := 'STRATEGIE',
    p_core_id := 22,
    p_comp_def_id := NULL
) AS new_id;
RESET ROLE;

SELECT id, level, source, module_id, message, core_id, created_at
FROM fw.diag_log
WHERE module_id = 'unified_ownership_smoke'
ORDER BY id DESC LIMIT 1;
-- EXPECTED: 1 row, core_id=22, new_id ≥ 232
-- POKUD CHYBA "digest does not exist" → V6 ukáže schema → uprav search_path
-- (např. když digest() je v 'extensions', uprav search_path na 'extensions, pgcrypto, public, fw, pg_catalog')

-- ════════════════════════════════════════════════════════════════════════
-- POST-DEPLOY (PowerShell na cloud APP)
-- ════════════════════════════════════════════════════════════════════════
--
--   Restart-Service STRATEGIE-API
--   Start-Sleep -Seconds 3
--
-- Pak browser:
--   Hard reload (Ctrl+Shift+R)
--   Klik na Knowledge Entries v stromě
--   → core_id=34 v console
--   → POST /diag-log/event do fw.diag_log
--
-- Verify za 30 sec:
--   SELECT id, level, source, module_id, message, core_id, comp_def_id, created_at
--   FROM fw.diag_log
--   WHERE created_at >= NOW() - INTERVAL '2 minutes'
--   ORDER BY id DESC LIMIT 10;
--   EXPECTED: new rows tečou, core_id=34 (Knowledge Entries)
--
-- ════════════════════════════════════════════════════════════════════════
