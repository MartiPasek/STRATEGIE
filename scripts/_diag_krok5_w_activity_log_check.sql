-- ============================================================
-- DIAG KEY: Activity_log schema check (23.5.2026)
-- ============================================================
-- Hypothesis: Backend DELETE + INSERT activity_log → INSERT silently
-- raises (column mismatch / FK violation / RLS / type cast),
-- Python inner try/except swallows exception, ds.commit() issues
-- COMMIT na ABORTED PG transaction → PG rolls back → DELETE pryč
-- pre_commit_check (před INSERT) byl 0 → consistent s hypothesis.
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Schema activity_log table                            ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'activity_log'
ORDER BY ordinal_position;
-- Backend INSERT columns: user_id, action_kind, target_kind,
--   target_id, change_source, payload, created_at
-- Verify ALL exist + payload type (text vs jsonb mater pro cast)


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: FK constraints na activity_log (mohou block INSERT) ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    conname,
    pg_get_constraintdef(c.oid) AS def
FROM pg_constraint c
JOIN pg_class cl ON cl.oid = c.conrelid
JOIN pg_namespace n ON n.oid = cl.relnamespace
WHERE n.nspname = 'public' AND cl.relname = 'activity_log';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q3: Triggers na activity_log                             ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT tgname, pg_get_triggerdef(t.oid) AS def
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname = 'activity_log'
  AND NOT tgisinternal;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q4: Manual INSERT test simulující backend code          ║
-- ║      (ROLLBACK na konci, bezpečné)                        ║
-- ╚══════════════════════════════════════════════════════════╝
BEGIN;
INSERT INTO activity_log
    (user_id, action_kind, target_kind, target_id, change_source, payload, created_at)
VALUES
    (1, 'delete', 'fw.diag_log', 9999, 'ui',
     '{"core_id":44,"deleted_rows":1}', NOW());
-- Pokud raise: column missing / FK violation / type mismatch
-- → root cause IDENTIFIED
SELECT 'INSERT_OK' AS status;
ROLLBACK;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q5: ACL na fw.diag_log — má strategie role DELETE?     ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    c.oid::regclass AS table_name,
    c.relowner::regrole AS owner,
    array_to_string(c.relacl, ',') AS acl
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw' AND c.relname = 'diag_log';
-- ACL format: '{role=rwadDxt/grantor}'
-- r=SELECT, w=UPDATE, a=INSERT, d=DELETE, D=TRUNCATE
-- Hledej strategie= a verify že má 'd' (DELETE)


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q6: Existing activity_log rows from recent backend     ║
-- ║      Pokud zde JSOU rows, INSERT funguje → hypothesis    ║
-- ║      eliminated. Pokud NEJSOU, INSERT fail silent.       ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT id, user_id, action_kind, target_kind, target_id,
       change_source, payload, created_at
FROM activity_log
WHERE action_kind = 'delete'
  AND target_kind = 'fw.diag_log'
ORDER BY created_at DESC
LIMIT 10;


-- ============================================================
-- INTERPRETACE:
--   Q1: Pokud chybí 'change_source' column → backend INSERT
--       silently fail (Marti's Fix M+ migration neaplikováno)
--   Q1: Pokud 'payload' je text místo jsonb → string OK, no cast issue
--   Q4: Pokud Q4 selže s konkrétní chybou → root cause exact
--   Q5: Pokud strategie nemá 'd' v ACL → DELETE permission deny
--       (ale rowcount=1 by se nestalo, takže nepravděpodobné)
--   Q6: Pokud activity_log NEMÁ rows pro DELETE attempts → INSERT
--       silently fail po DELETE, tx aborted, COMMIT → ROLLBACK
-- ============================================================
