-- ============================================================
-- Phase SYSTEM NEW — DB Connections grid v3 (Marti's 22.5.2026)
-- ============================================================
-- v3: Schema fixes per Marti's catches:
--   - fw.menu_node nema code ani kind (Tasks #313+#312 dropped 22.5.)
--   - fw.data_source nema kind, ma refresh_type
--   - fw.data_set nema version, ma kolony per 7c pattern
--   - fw.data_source_op ma operation_kind + variant_code + is_default
--
-- Reference: scripts/_phase_system_new_07c_3_grids.sql (working pattern z 21.5.).
-- ============================================================

BEGIN;

-- ─── 1. menu_node "DB Connections" pod Framework (id=42) ────────
INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'DB Connections',
    42,  -- Framework folder
    700,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'DB Connections' AND parent_id = 42
);

-- ─── 2. fw.core ─────────────────────────────────────────────────
INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_db_connections', 'DB Connections',
    'SYSTEM NEW DB Connections grid: SELECT * FROM fw.db_connection (+ tenant join)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.framework_db_connections');

-- ─── 3. fw.data_source (pattern z Etapa 7c) ─────────────────────
INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_db_connections_list',
    'Framework: DB Connections',
    'SYSTEM NEW db_connections list — SELECT z fw.db_connection + LEFT JOIN public.tenants',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list');

-- ─── 4. fw.data_set (pattern z Etapa 7c) ────────────────────────
INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_db_connections_list',
    $sql$
SELECT dc.id, dc.code, dc.label,
       dc.tenant_id, t.tenant_code, t.tenant_name,
       dc.db_type, dc.host, dc.port, dc.default_db,
       dc.scope_databases,
       dc.is_active, dc.sort_order, dc.description, dc.status,
       dc.created_at, dc.updated_at
FROM fw.db_connection dc
LEFT JOIN public.tenants t ON t.id = dc.tenant_id
WHERE dc.status = 'active'
ORDER BY dc.sort_order ASC, dc.code ASC
$sql$,
    1,  -- db_connection_id = 1 (strategie database)
    'SYSTEM NEW DB Connections — fw.db_connection + tenant info',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_db_connections_list');

-- ─── 5. fw.data_source_op (pattern z Etapa 7c) ──────────────────
INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_db_connections_list'),
    'select', 'default', TRUE,
    'SYSTEM NEW framework_db_connections default select (22.5.2026)'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list')
      AND variant_code = 'default'
);

-- ─── 6. UPDATE menu_node.core_id ─────────────────────────────────
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_db_connections')
WHERE label = 'DB Connections' AND parent_id = 42 AND core_id IS NULL;

-- ─── 7. fw.comp_def root komponenta (grid_modern type_id=306) ───
-- Marti's doctrine: data_source_id JE NA comp_def (NE na core).
-- Pattern z 7c: type 306 = grid_modern, region_slot='main', sort_order=100.
INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    data_source_id, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_framework_db_connections', 'DB Connections',
    (SELECT id FROM fw.core WHERE code = 'system_new.framework_db_connections'),
    306, 'main',
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list'),
    100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_framework_db_connections');

COMMIT;

-- ============================================================
-- VERIFY (run separately):
-- ============================================================
-- SELECT
--     mn.id AS menu_id, mn.label,
--     c.id AS core_id, c.code AS core_code,
--     cd.id AS comp_def_id, cd.name, cd.data_source_id,
--     ds.code AS ds_code,
--     dset.code AS dataset_code, dset.db_connection_id
-- FROM fw.menu_node mn
-- LEFT JOIN fw.core c ON c.id = mn.core_id
-- LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
-- LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
-- LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
-- LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
-- WHERE mn.label = 'DB Connections' AND mn.parent_id = 42;
