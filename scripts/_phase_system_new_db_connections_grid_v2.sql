-- ============================================================
-- Phase SYSTEM NEW — DB Connections grid (Marti's 22.5.2026 v2)
-- ============================================================
-- v1 silently selhal — pouzival fw.menu_node.code + .kind (oba dropnute
-- Tasks #313 + #312 dnes rano). v2: lookup parent pres label+parent_id,
-- INSERT bez code/kind.
--
-- Schema reality (Marti's verify 22.5.):
--   fw.menu_node columns: id, label, parent_id, sort_order, status,
--     visibility_scope, is_immutable, description_user, created_at,
--     updated_at, core_id, created_by_id, created_by_text,
--     updated_by_id, updated_by_text, description_system
--   (NO code, NO kind!)
--
-- Lookup parent: SYSTEM NEW root = id=33 (no parent_id),
-- Framework folder = id=42 (parent_id=33, label='Framework').
--
-- Plus fw.core / fw.data_source / fw.data_set / fw.comp_def still have code
-- column — lookup pres code OK pro tyto tables.
-- ============================================================

BEGIN;

-- ─── 1. menu_node "DB Connections" pod Framework (id=42) ────────
-- Pozn.: fw.menu_node nema code ani kind columns (dropnute 22.5.).
-- Idempotence: WHERE NOT EXISTS pres label + parent_id.
INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'DB Connections',
    42,  -- Framework folder
    700,  -- pod Znalostní báze (sort_order=600)
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'DB Connections' AND parent_id = 42
);

-- ─── 2. fw.core (code still exists) ─────────────────────────────
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

-- ─── 6. UPDATE menu_node.core_id (lookup pres label+parent_id) ──
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.framework_db_connections')
WHERE label = 'DB Connections' AND parent_id = 42 AND core_id IS NULL;

-- ─── 7. fw.comp_def root komponenta (grid_modern type_id=306) ───
-- Marti's catch 22.5. "SCHAZI Tam comp_def — to je ta vrstva, kterou delame"
-- Plus Marti's 17.5. doctrine (Krok 5.P): "CORE = kontejner, data_source_id
-- patri na comp_def, nikoli na core". Tj. data_source_id MUSI byt zde
-- (na root comp_def), ne na fw.core (column tam jiz neexistuje).
--
-- Pattern: type 306 = grid_modern, region_slot='main', sort_order=100.
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
--
-- Expected: 1 row, vse vyplnene
--   menu_id NOT NULL, core_id NOT NULL, comp_def_id NOT NULL,
--   cd.data_source_id NOT NULL, ds_code = '...db_connections_list',
--   dataset_code = '...db_connections_list', db_connection_id = 1
