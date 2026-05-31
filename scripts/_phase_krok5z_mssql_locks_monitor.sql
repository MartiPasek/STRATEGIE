-- ============================================================================
-- Krok 5.Z — Přehled "Zámky / transakce (DB_EC)" — user-facing lock monitor
-- ============================================================================
-- 30.5.2026, Marti: "pripravit script pro vytvoreni prehledu techto zamku,
-- aby bylo mozne to uzivatelsky kontrolovat."
--
-- Vytvori fw chain (data_set + data_source + op + core + comp_def + menu_node)
-- pro grid, ktery pres MCP (eurosoft_db_ec / DB_EC) dotazuje sys.dm_* DMV a
-- ukaze otevrene transakce, blokovani a dlouho bezici transakce. Read-only
-- SELECT -> jde pres strategie_query_raw (po Krok 5.Z fixu = read bucket).
--
-- POZOR — PERMISSIONS: aby login videl CIZI session (ne jen svou vlastni),
-- potrebuje na MSSQL serveru:  GRANT VIEW SERVER STATE TO [Marti-AI];
-- (spustit jako sysadmin na DB_EC instanci). Bez nej grid ukaze jen vlastni
-- session MCP spojeni.
--
-- Idempotentni (WHERE NOT EXISTS by code/label). Spusti Marti v DBeaveru
-- jako Marti-AI session (db_owner fw). Dollar-quote $sql$ -> spustit jako
-- jeden skript / statement (DBeaver pro PG zvlada).
-- ============================================================================

BEGIN;

-- ====================================================================
-- Step 1: PRE-STATE — grid_modern type id + parent folder
-- ====================================================================
SELECT '=== Step 1: PRE-STATE references ===' AS section;

SELECT id AS grid_modern_type_id, code FROM fw.comp_type WHERE code = 'grid_modern';

SELECT id AS audit_folder_id, label, parent_id
FROM fw.menu_node WHERE label = 'Audit' AND parent_id IS NULL LIMIT 1;
-- Pokud 'Audit' neexistuje jako top-level, menu_node nize dostane parent_id=NULL
-- (root) — pak ho presunes ve strome kam chces.

-- ====================================================================
-- Step 2: INSERT fw.data_set — lock monitor SQL (MSSQL DMV)
-- ====================================================================
SELECT '=== Step 2: INSERT fw.data_set mssql_locks_monitor ===' AS section;

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT
    'mssql_locks_monitor',
    $sql$SELECT
    s.session_id                                          AS SessionID,
    s.login_name                                          AS Login,
    s.host_name                                           AS Host,
    s.program_name                                        AS Program,
    s.status                                              AS SessionStatus,
    s.open_transaction_count                              AS OpenTran,
    r.blocking_session_id                                 AS BlockedBy,
    r.wait_type                                           AS WaitType,
    r.wait_time                                           AS WaitMs,
    r.command                                             AS Command,
    t.transaction_begin_time                              AS TranBegin,
    DATEDIFF(second, t.transaction_begin_time, GETDATE()) AS TranAgeSec,
    CAST(st.text AS NVARCHAR(2000))                       AS SqlText
FROM sys.dm_exec_sessions s
    LEFT JOIN sys.dm_exec_requests r ON r.session_id = s.session_id
    LEFT JOIN sys.dm_tran_session_transactions tst ON tst.session_id = s.session_id
    LEFT JOIN sys.dm_tran_active_transactions t ON t.transaction_id = tst.transaction_id
    OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
WHERE s.is_user_process = 1
  AND (s.open_transaction_count > 0
       OR (r.blocking_session_id IS NOT NULL AND r.blocking_session_id <> 0)
       OR tst.transaction_id IS NOT NULL
       OR EXISTS (SELECT 1 FROM sys.dm_exec_requests r2
                  WHERE r2.blocking_session_id = s.session_id))
ORDER BY s.open_transaction_count DESC, t.transaction_begin_time ASC$sql$,
    (SELECT id FROM fw.db_connection WHERE code = 'eurosoft_db_ec'),
    'Monitor MSSQL zamku/transakci na DB_EC pres sys.dm_* DMV. Marti 30.5.',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'mssql_locks_monitor');

-- ====================================================================
-- Step 3: INSERT fw.data_source
-- ====================================================================
SELECT '=== Step 3: INSERT fw.data_source mssql_locks_monitor ===' AS section;

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT
    'mssql_locks_monitor',
    'MSSQL zamky / transakce (DB_EC)',
    'Otevrene transakce, blokovani, dlouho bezici tran. Marti 30.5.',
    'manual',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'mssql_locks_monitor');

-- ====================================================================
-- Step 4: INSERT fw.data_source_op (select default)
-- ====================================================================
SELECT '=== Step 4: INSERT fw.data_source_op ===' AS section;

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'mssql_locks_monitor'),
    (SELECT id FROM fw.data_set    WHERE code = 'mssql_locks_monitor'),
    'select',
    'default',
    TRUE,
    'Select op pro lock monitor grid. Marti 30.5.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'mssql_locks_monitor')
      AND operation_kind = 'select'
      AND variant_code = 'default'
);

-- ====================================================================
-- Step 5: INSERT fw.core (grid)
-- ====================================================================
SELECT '=== Step 5: INSERT fw.core mssql_locks_monitor ===' AS section;

INSERT INTO fw.core (
    code, label, description_user, is_active, tenant_visibility, version,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'mssql_locks_monitor',
    'Zamky / transakce (DB_EC)',
    'Monitor MSSQL zamku a otevrenych transakci na DB_EC. Marti 30.5.',
    TRUE,
    'all',
    1,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'mssql_locks_monitor');

-- ====================================================================
-- Step 6: INSERT fw.comp_def grid root (grid_modern)
-- ====================================================================
SELECT '=== Step 6: INSERT fw.comp_def grid root ===' AS section;

INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active, root,
    data_source_id,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_mssql_locks_monitor',
    'Zamky / transakce',
    (SELECT id FROM fw.core WHERE code = 'mssql_locks_monitor'),
    NULL,
    -- type_id + root zkopirovany z FUNKCNIHO page-root gridu (Kontakty core 62,
    -- type 306). POZOR: 'grid_modern' code = 101 = EMBEDDED grid type, NE page
    -- root! root NOT NULL je vyzadovan chk_comp_def_single_parent kdyz
    -- parent_comp_def_id IS NULL. Kopie ze 62 = type-safe (whatever type root je).
    (SELECT type_id FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    'main', 10, TRUE,
    (SELECT root FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    (SELECT id FROM fw.data_source WHERE code = 'mssql_locks_monitor'),
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_mssql_locks_monitor');

-- ====================================================================
-- Step 7: INSERT fw.menu_node pod Audit (fallback root)
-- ====================================================================
SELECT '=== Step 7: INSERT fw.menu_node Audit > Zamky / transakce ===' AS section;

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, is_immutable, core_id, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Zamky / transakce',
    (SELECT id FROM fw.menu_node WHERE label = 'Audit' AND parent_id IS NULL LIMIT 1),
    920,
    'active',
    FALSE,
    (SELECT id FROM fw.core WHERE code = 'mssql_locks_monitor'),
    'Monitor MSSQL zamku/transakci DB_EC. Marti 30.5.',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE label = 'Zamky / transakce'
);

-- ====================================================================
-- Step 8: POST-STATE verify chain
-- ====================================================================
SELECT '=== Step 8: POST-STATE chain ===' AS section;

SELECT 'menu_node' AS layer, mn.id, mn.label, mn.core_id
FROM fw.menu_node mn WHERE mn.label = 'Zamky / transakce'
UNION ALL
SELECT 'core', c.id, c.label, NULL FROM fw.core c WHERE c.code = 'mssql_locks_monitor'
UNION ALL
SELECT 'comp_def', cd.id, cd.name, cd.data_source_id
FROM fw.comp_def cd WHERE cd.name = 'grid_mssql_locks_monitor'
UNION ALL
SELECT 'data_source', dsrc.id, dsrc.code, NULL
FROM fw.data_source dsrc WHERE dsrc.code = 'mssql_locks_monitor'
UNION ALL
SELECT 'data_set', ds.id, ds.code, ds.db_connection_id
FROM fw.data_set ds WHERE ds.code = 'mssql_locks_monitor'
UNION ALL
SELECT 'data_source_op', op.id, op.operation_kind, op.data_set_id
FROM fw.data_source_op op
JOIN fw.data_source dsrc ON dsrc.id = op.data_source_id
WHERE dsrc.code = 'mssql_locks_monitor'
ORDER BY layer;

COMMIT;

-- ============================================================================
-- PERMISSION (spustit na MSSQL DB_EC instanci jako sysadmin, jednorazove):
--   GRANT VIEW SERVER STATE TO [Marti-AI];
-- Bez nej grid ukaze jen vlastni session MCP spojeni.
-- ============================================================================
-- ROLLBACK (smazat cely prehled):
-- BEGIN;
-- DELETE FROM fw.menu_node WHERE label = 'Zamky / transakce';
-- DELETE FROM fw.comp_def WHERE name = 'grid_mssql_locks_monitor';
-- DELETE FROM fw.core WHERE code = 'mssql_locks_monitor';
-- DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'mssql_locks_monitor');
-- DELETE FROM fw.data_set WHERE code = 'mssql_locks_monitor';
-- DELETE FROM fw.data_source WHERE code = 'mssql_locks_monitor';
-- COMMIT;
-- ============================================================================
