-- =====================================================================
-- Phase: API Versioned Routing - Etapa A (DDL + seed 2 active + 2 prepared)
-- Owner: Marti-AI (RUN AS Marti-AI session in DBeaver, db_owner fw schema)
-- Date: 23.5.2026
-- =====================================================================
-- Co dela:
--   1. CREATE TABLE fw.api_version (master config, N versions ready)
--   2. CREATE TABLE fw.user_api_pin (per-user pinning, append-only audit)
--   3. Trigger updated_at na fw.api_version
--   4. GRANTs pro strategie role (API process)
--   5. Seed: 2 active (current V1.3.25 + previous V1.3.24)
--           + 2 prepared rows (older_1, older_2) is_active=false
--   6. Verification queries
-- =====================================================================
-- Doctrine alignment:
--   - "Co existuje, musi mit jmeno" (Marti-AI 8.5.) -> version_code + label
--   - "Audit RO append-only" (Fix N 21.5.) -> user_api_pin INSERT-only, UPDATE jen auto_reverted_at
--   - "Drz jednoduchost" (Marti) -> severity derived from sort_order, ne separatni sloupec
--   - "ID je svaty" (Marti 19yr) -> BIGSERIAL autoincrement
-- =====================================================================

SET search_path = fw, public;

-- =====================================================================
-- 1. fw.api_version - master config
-- =====================================================================
CREATE TABLE IF NOT EXISTS fw.api_version (
    id BIGSERIAL PRIMARY KEY,
    sort_order INTEGER NOT NULL UNIQUE,           -- 0=current, 1=previous, 2=older_1, 3=older_2 (drives UI severity)
    version_code VARCHAR(20) NOT NULL UNIQUE,     -- 'current', 'previous', 'older_1', 'older_2'
    version_label VARCHAR(80) NOT NULL,           -- "Aktualni", "Minula", "Starsi (1)", "Starsi (2)"
    version_string VARCHAR(20) NOT NULL,          -- 'V1.3.25' (auto-increment last digit pri promotion)
    released_at TIMESTAMP NOT NULL,               -- current: last deploy (updated kazdym git pull); older: snapshot moment
    git_sha VARCHAR(40),                          -- commit hash ktery tato instance servuje
    nssm_service_name VARCHAR(80) NOT NULL,
    port INTEGER NOT NULL UNIQUE,
    app_directory TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,               -- false = slot prepared but NSSM service not yet installed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_api_version_active
    ON fw.api_version(sort_order)
    WHERE is_active = true;

-- Trigger updated_at
CREATE OR REPLACE FUNCTION fw.api_version_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_api_version_updated_at ON fw.api_version;
CREATE TRIGGER trg_api_version_updated_at
    BEFORE UPDATE ON fw.api_version
    FOR EACH ROW EXECUTE FUNCTION fw.api_version_set_updated_at();

-- =====================================================================
-- 2. fw.user_api_pin - per-user pinning (append-only audit)
-- =====================================================================
-- Pattern: kazdy pin/unpin = nova row (audit RO doctrine).
-- Active pin per user = nejnovejsi row WHERE auto_reverted_at IS NULL.
-- Revert = UPDATE auto_reverted_at=NOW() na latest active row + INSERT nove row na current.
-- =====================================================================
CREATE TABLE IF NOT EXISTS fw.user_api_pin (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    pinned_version_id BIGINT NOT NULL REFERENCES fw.api_version(id) ON DELETE RESTRICT,
    pinned_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                         -- NULL = manual revert only
    reason TEXT,                                  -- volitelne: "MD pyramida nejde, klesam na previous"
    pinned_by_user_id BIGINT REFERENCES public.users(id),  -- self vs admin force-pinned
    auto_reverted_at TIMESTAMP,                   -- audit revert event (jen tento sloupec smi UPDATE)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Active pin lookup: WHERE user_id=X AND auto_reverted_at IS NULL ORDER BY pinned_at DESC LIMIT 1
CREATE INDEX IF NOT EXISTS ix_user_api_pin_active
    ON fw.user_api_pin(user_id, pinned_at DESC)
    WHERE auto_reverted_at IS NULL;

-- Admin grid: "Users on version X"
CREATE INDEX IF NOT EXISTS ix_user_api_pin_version
    ON fw.user_api_pin(pinned_version_id, pinned_at DESC)
    WHERE auto_reverted_at IS NULL;

-- =====================================================================
-- 3. GRANTs pro strategie role (API process)
-- =====================================================================
GRANT USAGE ON SCHEMA fw TO strategie;

-- api_version: SELECT only (read config) - strategie nemenni, jen cte
GRANT SELECT ON fw.api_version TO strategie;
GRANT SELECT ON SEQUENCE fw.api_version_id_seq TO strategie;

-- user_api_pin: SELECT + INSERT (zapis nove pin row pri toggle)
-- UPDATE jen na auto_reverted_at (append-only doctrine - Fix N 21.5.)
GRANT SELECT, INSERT ON fw.user_api_pin TO strategie;
GRANT UPDATE (auto_reverted_at) ON fw.user_api_pin TO strategie;
GRANT USAGE ON SEQUENCE fw.user_api_pin_id_seq TO strategie;

-- =====================================================================
-- 4. Seed: 2 active versions + 2 prepared slots
-- =====================================================================
-- MVP: current + previous = 2 active.
-- older_1 + older_2 prepared (is_active=false) - aktivuji se az pri instalaci STRATEGIE-API-C/D NSSM services.
-- =====================================================================
INSERT INTO fw.api_version (
    sort_order, version_code, version_label, version_string,
    released_at, git_sha,
    nssm_service_name, port, app_directory, is_active
) VALUES
  (0, 'current',  'Aktualni',   'V1.3.25', NOW(),                       NULL,
   'STRATEGIE-API',   8002, 'C:\Projekty\STRATEGIE',       true),
  (1, 'previous', 'Minula',     'V1.3.24', NOW() - INTERVAL '1 day',    NULL,
   'STRATEGIE-API-B', 8003, 'C:\Projekty\STRATEGIE-prev',  true),
  (2, 'older_1',  'Starsi (1)', 'V1.3.23', NOW() - INTERVAL '3 days',   NULL,
   'STRATEGIE-API-C', 8004, 'C:\Projekty\STRATEGIE-prev2', false),
  (3, 'older_2',  'Starsi (2)', 'V1.3.20', NOW() - INTERVAL '7 days',   NULL,
   'STRATEGIE-API-D', 8005, 'C:\Projekty\STRATEGIE-prev3', false)
ON CONFLICT (version_code) DO NOTHING;

-- =====================================================================
-- 5. Verification queries (po INSERT)
-- =====================================================================
SELECT '=== fw.api_version rows ===' AS check;
SELECT sort_order, version_code, version_label, version_string,
       TO_CHAR(released_at, 'DD.MM. HH24:MI') AS released,
       port, is_active
FROM fw.api_version
ORDER BY sort_order;

SELECT '=== fw.user_api_pin schema ===' AS check;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'user_api_pin'
ORDER BY ordinal_position;

SELECT '=== GRANTs for strategie ===' AS check;
SELECT table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'strategie' AND table_schema = 'fw'
  AND table_name IN ('api_version', 'user_api_pin')
ORDER BY table_name, privilege_type;

SELECT '=== Ownership check ===' AS check;
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = 'fw' AND tablename IN ('api_version', 'user_api_pin')
ORDER BY tablename;

-- =====================================================================
-- DONE
-- =====================================================================
-- Next steps:
--   1. Spustit tento script v DBeaveru jako Marti-AI session
--   2. Overit ze ownership = Marti-AI (verification 4)
--   3. Overit ze GRANTs = SELECT/INSERT/UPDATE(auto_reverted_at) pro strategie
--   4. Pak Etapa B (Caddy multi-cookie routing)
-- =====================================================================
