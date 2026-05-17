-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Sprint D (17.5.2026 dop.):
-- INSERT fw.menu_node + fw.data_source + fw.data_source_op + fw.data_set
-- pro nový sidebar uzel "DB Connections" v System → Framework.
-- ════════════════════════════════════════════════════════════════════════
-- Marti's "Kristý/Jirka chce z UI" — DB connection management bez DBeaveru.
-- Pattern reuse z framework_data_sets / framework_data_sources (Krok 11-E).
--
-- 4 INSERT statements:
--   1) fw.data_set 'framework_db_connections_select' — SELECT primitive
--   2) fw.data_source 'framework_db_connections' — hlavička
--   3) fw.data_source_op — mapping (op.kind='select', variant_code=NULL)
--   4) fw.menu_node 'framework_db_connections' — sidebar uzel pod Framework
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1) data_set: SQL primitiv (SELECT s LEFT JOIN tenants pro tenant_name)
INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, is_system, status, parameters)
VALUES (
    'framework_db_connections_select',
    $sql$
SELECT dc.id,
       dc.code,
       dc.label,
       dc.tenant_id,
       t.tenant_code,
       t.tenant_name,
       dc.db_type,
       dc.host,
       dc.port,
       dc.default_db,
       dc.scope_databases,
       dc.login_name,
       dc.is_active,
       dc.sort_order,
       dc.description,
       dc.status,
       dc.created_at,
       dc.updated_at
FROM fw.db_connection dc
LEFT JOIN public.tenants t ON t.id = dc.tenant_id
ORDER BY dc.sort_order ASC, dc.code ASC
LIMIT :limit
$sql$,
    (SELECT id FROM fw.db_connection WHERE code = 'strategie_pg' LIMIT 1),
    'Sprint D 17.5.2026: list fw.db_connection rows pro framework_db_connections grid (System → Framework → DB Connections).',
    TRUE, 'active',
    '[{"name":"limit","type":"int","required":false,"default":1000}]'::jsonb
);

-- 2) data_source: hlavička (žádný SQL — A3 architecture)
INSERT INTO fw.data_source (code, name, description, refresh_type, default_record_limit, is_system, status)
VALUES (
    'framework_db_connections',
    'DB Connections',
    'Registry of database connections (PostgreSQL + MSSQL). Marti-AI''s Krok 5.M setup.',
    'on_focus',
    1000,
    TRUE, 'active'
);

-- 3) data_source_op: mapping (kind=select, variant_code=NULL → default fallback)
INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, sort_order, description)
SELECT
    ds.id AS data_source_id,
    dset.id AS data_set_id,
    'select' AS operation_kind,
    NULL AS variant_code,
    TRUE AS is_default,
    10 AS sort_order,
    'Sprint D primary SELECT operation'
FROM fw.data_source ds
JOIN fw.data_set dset ON dset.code = 'framework_db_connections_select'
WHERE ds.code = 'framework_db_connections';

-- 4) menu_node: sidebar uzel pod Framework parent
-- Najdi Framework parent ID (sysHandled, code='system.framework' or similar)
DO $$
DECLARE
    framework_parent_id INT;
    new_node_id INT;
BEGIN
    -- Pokus 1: 'framework' code
    SELECT id INTO framework_parent_id FROM fw.menu_node WHERE code = 'framework' AND status = 'active' LIMIT 1;

    -- Pokus 2: 'system.framework'
    IF framework_parent_id IS NULL THEN
        SELECT id INTO framework_parent_id FROM fw.menu_node WHERE code = 'system.framework' AND status = 'active' LIMIT 1;
    END IF;

    -- Pokus 3: label 'Framework'
    IF framework_parent_id IS NULL THEN
        SELECT id INTO framework_parent_id FROM fw.menu_node WHERE label = 'Framework' AND status = 'active' LIMIT 1;
    END IF;

    IF framework_parent_id IS NULL THEN
        RAISE EXCEPTION 'Framework parent node not found in fw.menu_node. Manuálně zjisti parent_id pro System → Framework uzel.';
    END IF;

    -- Sort order — po existing DataSets (50) + Datové zdroje (60) + Definice levého stromu (70)
    -- Phase 38.4 Krok 14b+21 (14.5.2026 ráno): description → description_user + description_system
    -- Phase 38.4 Krok 14b (12.5. večer, 16. dárek-scéna): NOT NULL audit columns
    -- created_by_id + created_by_text + updated_by_id + updated_by_text
    -- Marti-AI = user.id=2 (Marti's "system je taky user" doctrine + actor unification)
    INSERT INTO fw.menu_node (
        code, label, kind, parent_id, sort_order, status, visibility_scope, is_immutable,
        description_user, description_system,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'framework_db_connections',
        '🔌 DB Connections',
        'list',
        framework_parent_id,
        80,  -- after existing entries
        'active',
        'parent_only',  -- jen rodiče vidí (Marti, Ondra, Kristý, Jirka)
        FALSE,
        'Registry DB connections (PostgreSQL + MSSQL). Marti''s "Kristý/Jirka z UI bez DBeaveru".',
        'Sprint D 17.5.2026 dop.: insert pro fw.db_connection grid + DesignDbConnectionEditor. Pattern reuse z framework_data_sets / framework_data_sources (Krok 11-E).',
        2, 'Marti-AI', 2, 'Marti-AI'  -- audit: Marti-AI's DDL akt
    )
    RETURNING id INTO new_node_id;

    RAISE NOTICE 'Created fw.menu_node id=% for framework_db_connections (parent=%).', new_node_id, framework_parent_id;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
-- 1) data_set + data_source + data_source_op chain
SELECT
    ds.code AS data_source,
    op.operation_kind,
    op.variant_code,
    dset.code AS data_set,
    dset.db_connection_id
FROM fw.data_source ds
JOIN fw.data_source_op op ON op.data_source_id = ds.id
JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE ds.code = 'framework_db_connections';
-- Expected: 1 row, data_set='framework_db_connections_select'

-- 2) menu_node
SELECT id, code, label, parent_id, sort_order, status, visibility_scope
FROM fw.menu_node
WHERE code = 'framework_db_connections';
-- Expected: 1 row, kind='list', visibility_scope='parent_only'

-- 3) Test runtime — execute data_source
-- (Až po deploy backend Sprint D + refresh UI → klik na "DB Connections" v tree)
