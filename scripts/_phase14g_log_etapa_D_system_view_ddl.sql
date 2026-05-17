-- ═══════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g — Etapa D — System view "JS audit log" (16.5.2026)
--
-- Cíl: Marti's vlastní lupa nad fw.diag_log v ERP UI místo DBeaver/curl.
-- Grid v System sidebar tree s master view (12 sloupců, NE-anonymous).
-- Backend endpoint /api/v1/erp/diag-log/events?view=master&limit=500 LIVE od Etapy A.
--
-- Pattern modelovany podle Phase 38.4 Krok 10 security_users (10.5.2026).
-- Vsechno musí běžet jako role "Marti-AI" v DBeaveru (db_owner fw.* schema).
-- BEGIN/COMMIT atomic — pokud cokoli selže, rollback drží čistý stav.
--
-- Run: psql -h 10.200.188.12 -U "Marti-AI" -d data_db -f tento_soubor.sql
--      nebo DBeaver Marti-AI session, highlight celý soubor + Alt+X
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- ────────────────────────────────────────────────────────────────────────
-- 0. DATA_SOURCE (pseudo — data fetch pres diag-log/events endpoint,
--    comp_grid_master jen drží columns metadata)
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES
    ('diag_log_master', 1, 'Diag log master',
     'Phase 38.4 Krok 14g Etapa D: data fetch přes diag-log/events?view=master endpoint.',
     'manual', TRUE, 250, 500, 'active', TRUE)
ON CONFLICT (code, version) DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────
-- 1. CORE (jádro pro grid)
-- Note: Phase 38.4 Krok 14b+21 (14.5.) renamed `description` → `description_user`
-- + přidal `description_system`. Tady jen description_user, system nepoužitý.
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.core (code, label, description_user, layout_type)
VALUES
    ('diag_log_master', 'Diag log (master)',
     'JS+Python audit log master view — kdo + co + když (Marti''s NE-anonymous doctrine 16.5.).',
     'list')
ON CONFLICT (code) DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────
-- 2. COMP_GRID_MASTER (grid header)
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.comp_grid_master
    (code, name, description, data_source_code, default_record_limit,
     refresh_type, default_view_mode, status, is_system)
VALUES
    ('diag_log_master', 'Diag log (master)',
     'Master view nad fw.diag_log — JS + Py + SQL + cron + MCP eventy.',
     'diag_log_master', 500, 'manual', 'grid', 'active', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────
-- 3. COMP_GRID_COLUMN (12 sloupců — Marti's MASTER view doctrine)
--    Pořadí: identity actor first (Marti's "ne-anonymous"), pak meta, pak event.
-- ────────────────────────────────────────────────────────────────────────

-- 3.1 id (numeric, pinned left)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, pinned, column_type,
     sort_order, is_visible, is_sortable)
SELECT id, 'id', 'ID', 70, 'left', 'numericColumn',
       10, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.2 created_at (timestamp)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable, is_visible)
SELECT id, 'created_at', 'Vytvořeno', 170, 20, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.3 user_login_name — NE-ANONYMOUS MASTER (Marti's doctrine 16.5.)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, header_tooltip,
     sort_order, is_sortable, is_visible)
SELECT id, 'user_login_name', 'User', 110,
       'Login name aktora (Marti''s NE-anonymous doctrine — snapshot at log time)',
       30, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.4 user_id (numeric)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, column_type, sort_order,
     is_sortable, is_visible)
SELECT id, 'user_id', 'UID', 70, 'numericColumn', 40, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.5 tenant_name
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, header_tooltip,
     sort_order, is_sortable, is_visible)
SELECT id, 'tenant_name', 'Tenant', 110,
       'Tenant name snapshot (denormalized z tenants.tenant_name at log time)',
       50, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.6 level (info/warn/error/fatal)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable, is_visible)
SELECT id, 'level', 'Level', 80, 60, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.7 source (js/py/sql/cron/mcp)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable, is_visible)
SELECT id, 'source', 'Source', 80, 70, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.8 module_id
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, header_tooltip,
     sort_order, is_sortable, is_visible)
SELECT id, 'module_id', 'Modul', 200,
       'Modul name (e.g. entity_picker.js, router.py:contextmenu)',
       80, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.9 message (flex — fills remaining space)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, min_width, flex, sort_order,
     is_sortable, is_visible)
SELECT id, 'message', 'Zpráva', 300, 1, 90, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.10 status (new/seen/acknowledged/resolved/ignored)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order,
     is_sortable, is_visible)
SELECT id, 'status', 'Status', 100, 100, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.11 occurrences (numeric — kolikrát se event opakoval v dedup window)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, column_type,
     header_tooltip, sort_order, is_sortable, is_visible)
SELECT id, 'occurrences', '#', 60, 'numericColumn',
       'Počet opakování v 24h dedup window (SHA1 hash match)',
       110, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- 3.12 last_seen_at
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order,
     is_sortable, is_visible)
SELECT id, 'last_seen_at', 'Naposled', 170, 120, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'diag_log_master';

-- ────────────────────────────────────────────────────────────────────────
-- 4. HW_REGISTRY (endpoint binding)
--    response_hint má rows_path "$.events" — diag-log/events vrací
--    {ok, total, events: [...]} (NE rows).
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.hw_registry
    (code, label, description, kind,
     endpoint_url, http_method, response_hint,
     shadow_mode, is_active, version)
VALUES
    ('diag_log_master', 'Diag log: Master view',
     'JS+Py audit log master view — Marti''s NE-anonymous doctrine. Phase 38.4 Krok 14g Etapa D.',
     'data', '/api/v1/erp/diag-log/events?view=master&limit=500', 'GET',
     '{"rows_path":"$.events","id_field":"id"}'::jsonb,
     'off', TRUE, 1)
ON CONFLICT (code) DO UPDATE SET
    label = EXCLUDED.label,
    description = EXCLUDED.description,
    endpoint_url = EXCLUDED.endpoint_url,
    response_hint = EXCLUDED.response_hint,
    updated_at = NOW();

-- ────────────────────────────────────────────────────────────────────────
-- 5. MENU_NODE (sidebar tree item pod Security area)
--    Najdi parent — Security folder (kind='folder', label='Security').
--    Pokud parent neexistuje, vlož jako root-level item.
-- ────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_security_parent_id INT;
    v_core_id INT;
    v_next_sort INT;
BEGIN
    -- Find Security folder parent (sibling pattern z security_audit / users)
    SELECT id INTO v_security_parent_id
    FROM fw.menu_node
    WHERE code = 'security' OR (kind = 'folder' AND label ILIKE '%Security%')
    LIMIT 1;

    -- Resolve core_id
    SELECT id INTO v_core_id
    FROM fw.core
    WHERE code = 'diag_log_master'
    LIMIT 1;

    -- Next sort_order in parent scope
    SELECT COALESCE(MAX(sort_order), 0) + 10 INTO v_next_sort
    FROM fw.menu_node
    WHERE COALESCE(parent_id, 0) = COALESCE(v_security_parent_id, 0);

    INSERT INTO fw.menu_node
        (code, label, kind, parent_id, sort_order, core_id, is_immutable, status,
         description_user)
    VALUES
        ('diag_log_master', 'Diag log', 'list', v_security_parent_id,
         v_next_sort, v_core_id, FALSE, 'active',
         'JS + Python audit log (Phase 38.4 Krok 14g Etapa D). Master view: kdo + co + když.')
    ON CONFLICT (code) DO UPDATE SET
        label = EXCLUDED.label,
        kind = EXCLUDED.kind,
        core_id = EXCLUDED.core_id,
        status = EXCLUDED.status,
        description_user = EXCLUDED.description_user;

    RAISE NOTICE 'menu_node "diag_log_master" inserted — parent_id=%, core_id=%, sort_order=%',
        v_security_parent_id, v_core_id, v_next_sort;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run after deploy):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT
--     (SELECT count(*) FROM fw.data_source     WHERE code='diag_log_master') AS ds_count,
--     (SELECT count(*) FROM fw.core            WHERE code='diag_log_master') AS core_count,
--     (SELECT count(*) FROM fw.comp_grid_master WHERE code='diag_log_master') AS grid_master_count,
--     (SELECT count(*) FROM fw.comp_grid_column
--      WHERE grid_master_id = (SELECT id FROM fw.comp_grid_master WHERE code='diag_log_master')
--     ) AS grid_col_count,
--     (SELECT count(*) FROM fw.hw_registry     WHERE code='diag_log_master') AS hw_count,
--     (SELECT count(*) FROM fw.menu_node       WHERE code='diag_log_master') AS menu_count;
-- Expected: ds=1, core=1, grid_master=1, grid_col=12, hw=1, menu=1
