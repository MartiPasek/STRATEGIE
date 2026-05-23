-- ============================================================
-- Phase SYSTEM NEW — DB Connections grid (Marti's 22.5.2026:
-- "Nemame soudecek DB connection")
-- ============================================================
-- Vytvori soudecek "DB Connections" pod Framework folder v System tree.
-- Pattern identicky s Etapa 7c (Knowledge Entries / Datové sady / atd.):
--   8 INSERTs atomic v BEGIN/COMMIT:
--     1. fw.menu_node            (soudecek "DB Connections")
--     2. fw.core                 (grid kontejner)
--     3. fw.data_source          (lookup do fw.db_connection)
--     4. fw.data_set             (SQL primitive)
--     5. fw.data_source_op       (variant_code='select_list')
--     6. UPDATE menu_node.core_id
--     7. UPDATE core.data_source_id
--     8. fw.context_menu_item    (dvojklik → DesignDbConnectionEditor)
--
-- Po deploy: System tree → Framework → DB Connections grid + dvojklik row
-- otevre editor (pres existing Sprint D wire-up).
-- ============================================================

BEGIN;

-- ─── 1. menu_node ──────────────────────────────────────────────
INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_db_connections', 'DB Connections', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    500,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_db_connections');

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

-- ─── 3. fw.data_source ──────────────────────────────────────────
INSERT INTO fw.data_source (
    code, version, description, kind, is_system, status,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_db_connections_list', 1,
    'SYSTEM NEW DB Connections list — SELECT z fw.db_connection + LEFT JOIN public.tenants',
    'sql', TRUE, 'active',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list');

-- ─── 4. fw.data_set ─────────────────────────────────────────────
INSERT INTO fw.data_set (
    code, version, description, sql_text,
    db_connection_id, is_system, status,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_db_connections_list', 1,
    'SYSTEM NEW DB Connections — fw.db_connection + tenant info',
    'SELECT dc.id, dc.code, dc.label,
            dc.tenant_id, t.tenant_code, t.tenant_name,
            dc.db_type, dc.host, dc.port, dc.default_db,
            dc.scope_databases,
            dc.is_active, dc.sort_order, dc.description, dc.status,
            dc.created_at, dc.updated_at
     FROM fw.db_connection dc
     LEFT JOIN public.tenants t ON t.id = dc.tenant_id
     WHERE dc.status = ''active''
     ORDER BY dc.sort_order ASC, dc.code ASC',
    1, TRUE, 'active',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.framework_db_connections_list');

-- ─── 5. fw.data_source_op (link data_source → data_set) ─────────
INSERT INTO fw.data_source_op (
    data_source_id, variant_code, data_set_id, sort_order,
    is_system, status,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list'),
    'select_list',
    (SELECT id FROM fw.data_set WHERE code = 'system_new.framework_db_connections_list'),
    1,
    TRUE, 'active',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_db_connections_list')
      AND variant_code = 'select_list'
);

-- ─── 6. UPDATE menu_node.core_id ─────────────────────────────────
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_db_connections')
WHERE code = 'system_new.framework_db_connections' AND core_id IS NULL;

-- ─── 7. fw.comp_def root komponenta (grid_modern type_id=306) ────
-- Marti's catch 22.5. "SCHAZI Tam comp_def — to je ta vrstva, kterou delame"
-- Plus Marti's 17.5. doctrine (Krok 5.P): "CORE = kontejner, data_source_id
-- patri na comp_def, nikoli na core". Tj. data_source_id MUSI byt zde
-- (na root comp_def), ne na fw.core (column tam jiz neexistuje).
--
-- Pattern: type 306 = grid_modern, region_slot='main', sort_order=100,
-- core_id → DB Connections core, data_source_id → DB Connections list.
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

-- ─── 8. context_menu_item (dvojklik row → DesignDbConnectionEditor) ─
-- Pattern z Sprint D — dvojklik na grid row otevre power tool.
-- action_kind='open_power_tool' nebo 'open_fw_form' s coreCode='db_connection_editor'.
-- Frontend dispatcher (fw_form_dispatcher.js) routuje na class.
INSERT INTO fw.context_menu_item (
    code, label, icon,
    scope, applies_to_kind,
    action_kind, action_params,
    sort_order, is_system, is_active, design_only, status,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'open_db_connection_editor', 'Otevřít editor', '📝',
    'grid_row', NULL,
    'open_fw_form',
    '{"coreCode": "db_connection_editor", "rowId": "$row_id"}'::jsonb,
    1, TRUE, TRUE, FALSE, 'active',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.context_menu_item
    WHERE code = 'open_db_connection_editor'
);

COMMIT;

-- ============================================================
-- VERIFY (run separately po COMMIT):
-- ============================================================
-- Phase 22.5 fix Marti's catch: data_source_id zive na fw.comp_def
-- (root grid komponenta), NE na fw.core (column tam dropnuty Krok 5.P 17.5.).
-- Join chain: menu_node → core → comp_def (region_slot='main') → data_source.
--
-- SELECT mn.id AS menu_id, mn.label AS menu_label,
--        c.id AS core_id, c.code AS core_code,
--        cd.id AS comp_def_id, cd.name AS comp_def_name, cd.type_id, cd.region_slot,
--        ds.id AS ds_id, ds.code AS ds_code,
--        op.variant_code,
--        dset.code AS dataset_code, dset.db_connection_id
-- FROM fw.menu_node mn
-- LEFT JOIN fw.core c ON c.id = mn.core_id
-- LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
-- LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
-- LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
-- LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
-- WHERE mn.code = 'system_new.framework_db_connections';
--
-- Expected: 1 row, vsechno vyplnene, comp_def_id NOT NULL,
-- comp_def.data_source_id → DB Connections list,
-- dataset_code = 'system_new.framework_db_connections_list',
-- db_connection_id = 1.
