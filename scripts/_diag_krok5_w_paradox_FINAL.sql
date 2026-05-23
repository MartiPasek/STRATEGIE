-- ============================================================
-- DIAG FINAL: Krok 5.W paradox (23.5.2026)
-- ============================================================
-- DBeaver DELETE+COMMIT persists ✓
-- Backend DELETE+COMMIT NEpersists, fresh ds2 vidí row
-- Same host/db/user, different PIDs (pool reuse), tx_post=null (commit ok)
--
-- Last hypothesis hunt:
--   A) fw.diag_log je VIEW (relkind='v') — UNION nad jinou tabulkou
--   B) Multiple physical fw.diag_log tables (schema collision)
--   C) ds backend connects k JINÉ db než my think (verify napřímo)
--   D) Row se re-inserts MEZI commit a fresh select (background process)
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Definitivní table type check                         ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    c.oid::regclass AS qualified_name,
    c.relkind,
    CASE c.relkind
        WHEN 'r' THEN 'ordinary TABLE'
        WHEN 'v' THEN 'VIEW (this is the smoking gun if view)'
        WHEN 'm' THEN 'materialized view'
        WHEN 'p' THEN 'partitioned table'
        WHEN 'f' THEN 'foreign table'
        ELSE 'other: ' || c.relkind
    END AS type_interpretation,
    n.nspname AS schema_name,
    c.relname AS table_name,
    c.reloptions AS table_options
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw' AND c.relname = 'diag_log';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: Je tam VÍCE objektů s názvem 'diag_log'?             ║
-- ║      Schema collision check                               ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    n.nspname AS schema_name,
    c.relname AS object_name,
    c.relkind,
    c.oid::regclass AS qualified_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relname = 'diag_log'
ORDER BY n.nspname;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q3: Pokud Q1 ukáže view, get definition                  ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT pg_get_viewdef('fw.diag_log'::regclass, true) AS view_def;
-- pokud table → error: not a view (ignore)


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q4: Pokud existuje "INSTEAD OF DELETE" trigger na view  ║
-- ║      — ten by mohl re-create row                          ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    tgname AS trigger_name,
    tgtype,
    pg_get_triggerdef(t.oid) AS def
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw'
  AND c.relname = 'diag_log'
  AND (tgtype & 1)::boolean = true;  -- INSTEAD OF triggers


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q5: Background workers / connections v PG                ║
-- ║      Kolik connections drží strategie role + pid          ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    pid,
    application_name,
    state,
    backend_start,
    xact_start,
    query_start,
    LEFT(query, 100) AS recent_query
FROM pg_stat_activity
WHERE usename = 'strategie'
ORDER BY backend_start DESC;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q6: Count fw.diag_log + verify row 1750 (or whatever     ║
-- ║      Marti right now tries to delete)                     ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT COUNT(*) AS total FROM fw.diag_log;
SELECT id, created_at, message FROM fw.diag_log WHERE id = 1750;
-- Po Marti's last DELETE → row 1750 by měla být PRYČ.
-- Pokud vidíš row → backend's DELETE skutečně neperzistuje.


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q7: Confirm DBeaver session = SAME database              ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    current_database() AS db,
    current_user AS pg_user,
    session_user AS session_role,
    inet_server_addr()::text AS host,
    inet_server_port() AS port,
    pg_backend_pid() AS my_pid;
-- Marti's DBeaver result MUSÍ být db=data_db host=10.200.188.12 port=5432
-- Pokud jinak → DBeaver vidí jinou DB než backend


-- ============================================================
-- DALŠÍ DIAG na cloud APP (PowerShell):
--   Get-Process python* | Select-Object Id, ProcessName, StartTime
--   = kolik Python procesů běží? Pokud > 1, multi-worker setup
-- ============================================================
