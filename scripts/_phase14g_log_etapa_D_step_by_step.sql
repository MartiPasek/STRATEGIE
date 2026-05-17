-- ═══════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa D — STEP BY STEP (16.5.2026)
--
-- Marti's instrukce: "Musime postupne". BEGIN/COMMIT zahozen — každý
-- statement běží samostatně, ON CONFLICT idempotent (re-run safe).
--
-- Postup v DBeaveru jako Marti-AI:
--   1. Spusť KROK 1 — highlight + Alt+X. Verify SELECT zkontroluje.
--   2. Pokud OK, KROK 2. Atd.
--   3. Pokud ERROR → STOP, pošli mi traceback.
-- ═══════════════════════════════════════════════════════════════════════


-- ─────────────────────────────────────────────────────────────
-- KROK 0: Schema diagnostika — co tabulky skutečně mají
-- ─────────────────────────────────────────────────────────────
-- Spusť toto NEJDŘÍV, pošli mi output. Pokud sloupce sedí
-- s SQL níž, jdeme dál. Pokud ne, fix per case.
SELECT
    'fw.data_source' AS tbl,
    array_agg(column_name ORDER BY ordinal_position) AS cols
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='data_source'
UNION ALL
SELECT 'fw.core',
    array_agg(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='core'
UNION ALL
SELECT 'fw.comp_grid_master',
    array_agg(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='comp_grid_master'
UNION ALL
SELECT 'fw.comp_grid_column',
    array_agg(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='comp_grid_column'
UNION ALL
SELECT 'fw.hw_registry',
    array_agg(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='hw_registry'
UNION ALL
SELECT 'fw.menu_node',
    array_agg(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='menu_node';


-- ─────────────────────────────────────────────────────────────
-- KROK 1: fw.data_source (pseudo, endpoint-backed)
-- ─────────────────────────────────────────────────────────────
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES
    ('diag_log_master', 1, 'Diag log master',
     'Phase 38.4 Krok 14g Etapa D: data fetch přes diag-log/events endpoint.',
     'manual', TRUE, 250, 500, 'active', TRUE)
ON CONFLICT (code, version) DO NOTHING;

-- Verify krok 1
SELECT count(*) AS step1_data_source FROM fw.data_source WHERE code='diag_log_master';
-- Expected: 1


-- ─────────────────────────────────────────────────────────────
-- KROK 2: fw.core (description_user post-Krok 14b+21 rename)
-- ─────────────────────────────────────────────────────────────
INSERT INTO fw.core (code, label, description_user, layout_type, data_entity_type)
VALUES
    ('diag_log_master', 'Diag log (master)',
     'JS+Python audit log master view — Marti''s NE-anonymous doctrine 16.5.',
     'list', NULL)
ON CONFLICT (code) DO NOTHING;

-- Verify krok 2
SELECT count(*) AS step2_core FROM fw.core WHERE code='diag_log_master';
-- Expected: 1


-- ─────────────────────────────────────────────────────────────
-- KROK 3: fw.comp_grid_master (grid header)
-- ─────────────────────────────────────────────────────────────
INSERT INTO fw.comp_grid_master
    (code, name, description, data_source_code, default_record_limit,
     refresh_type, default_view_mode, status, is_system)
VALUES
    ('diag_log_master', 'Diag log (master)',
     'Master view nad fw.diag_log — JS + Py + SQL + cron + MCP eventy.',
     'diag_log_master', 500, 'manual', 'grid', 'active', TRUE)
ON CONFLICT (code) DO NOTHING;

-- Verify krok 3
SELECT count(*) AS step3_grid_master FROM fw.comp_grid_master WHERE code='diag_log_master';
-- Expected: 1


-- ─────────────────────────────────────────────────────────────
-- KROK 4: fw.comp_grid_column (12 sloupců) — VŠECH 12 NAJEDNOU
-- ON CONFLICT NEEXISTUJE pro tuto tabulku (composite UNIQUE),
-- proto check IF NOT EXISTS pres NOT EXISTS subquery.
-- ─────────────────────────────────────────────────────────────
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, pinned, column_type,
     min_width, flex, header_tooltip, sort_order, is_visible, is_sortable)
SELECT gm.id, c.column_name, c.label, c.default_width, c.pinned, c.column_type,
       c.min_width, c.flex, c.header_tooltip, c.sort_order, TRUE, TRUE
FROM fw.comp_grid_master gm
CROSS JOIN (VALUES
    ('id',              'ID',         70,  'left', 'numericColumn',  NULL, NULL, NULL,
        10),
    ('created_at',      'Vytvořeno', 170,  NULL,   NULL,             NULL, NULL, NULL,
        20),
    ('user_login_name', 'User',      110,  NULL,   NULL,             NULL, NULL,
        'Login name aktora (Marti''s NE-anonymous doctrine — snapshot at log time)',
        30),
    ('user_id',         'UID',        70,  NULL,   'numericColumn',  NULL, NULL, NULL,
        40),
    ('tenant_name',     'Tenant',    110,  NULL,   NULL,             NULL, NULL,
        'Tenant name snapshot (denormalized z tenants.tenant_name at log time)',
        50),
    ('level',           'Level',      80,  NULL,   NULL,             NULL, NULL, NULL,
        60),
    ('source',          'Source',     80,  NULL,   NULL,             NULL, NULL, NULL,
        70),
    ('module_id',       'Modul',     200,  NULL,   NULL,             NULL, NULL,
        'Modul name (e.g. entity_picker.js, router.py:contextmenu)',
        80),
    ('message',         'Zpráva',    NULL, NULL,   NULL,             300, 1, NULL,
        90),
    ('status',          'Status',    100,  NULL,   NULL,             NULL, NULL, NULL,
        100),
    ('occurrences',     '#',          60,  NULL,   'numericColumn',  NULL, NULL,
        'Počet opakování v 24h dedup window (SHA1 hash match)',
        110),
    ('last_seen_at',    'Naposled',  170,  NULL,   NULL,             NULL, NULL, NULL,
        120)
) AS c(column_name, label, default_width, pinned, column_type,
       min_width, flex, header_tooltip, sort_order)
WHERE gm.code = 'diag_log_master'
  AND NOT EXISTS (
      SELECT 1 FROM fw.comp_grid_column ex
      WHERE ex.grid_master_id = gm.id AND ex.column_name = c.column_name
  );

-- Verify krok 4
SELECT count(*) AS step4_columns
FROM fw.comp_grid_column
WHERE grid_master_id = (SELECT id FROM fw.comp_grid_master WHERE code='diag_log_master');
-- Expected: 12


-- ─────────────────────────────────────────────────────────────
-- KROK 5: fw.hw_registry (endpoint binding)
-- ─────────────────────────────────────────────────────────────
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

-- Verify krok 5
SELECT count(*) AS step5_hw_registry FROM fw.hw_registry WHERE code='diag_log_master';
-- Expected: 1


-- ─────────────────────────────────────────────────────────────
-- KROK 6: Najdi Security parent (jen SELECT pro verify, žádný INSERT)
-- ─────────────────────────────────────────────────────────────
-- Pošli mi output — abychom věděli kam menu_node patří.
SELECT id, code, label, kind, parent_id, sort_order
FROM fw.menu_node
WHERE code = 'security'
   OR (kind = 'folder' AND label ILIKE '%security%')
   OR (kind = 'folder' AND label ILIKE '%audit%')
ORDER BY id
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- KROK 7: fw.menu_node (sidebar tree item)
-- POZOR: parent_id_value zadej RUČNĚ podle outputu z KROK 6.
-- Pokud parent='security' má id=42, nahrad ":parent_id_value" → 42.
-- Pokud parent neexistuje, nastav NULL (top-level).
-- ─────────────────────────────────────────────────────────────
-- TEMPLATE — nezpouštěj direct, edit parent_id nejdřív:
/*
INSERT INTO fw.menu_node
    (code, label, kind, parent_id, sort_order, core_id, is_immutable, status,
     description_user)
SELECT
    'diag_log_master', 'Diag log', 'list',
    NULL,  -- <<<< NAHRAD parent_id (z KROK 6 SELECT) nebo NULL
    (SELECT COALESCE(MAX(sort_order), 0) + 10
     FROM fw.menu_node
     WHERE COALESCE(parent_id, 0) = COALESCE(NULL, 0)),  -- <<<< stejný parent_id
    c.id,
    FALSE, 'active',
    'JS + Python audit log (Phase 38.4 Krok 14g Etapa D). Master view: kdo + co + když.'
FROM fw.core c
WHERE c.code = 'diag_log_master'
ON CONFLICT (code) DO UPDATE SET
    label = EXCLUDED.label,
    kind = EXCLUDED.kind,
    core_id = EXCLUDED.core_id,
    status = EXCLUDED.status,
    description_user = EXCLUDED.description_user;
*/

-- Verify krok 7 (po insert):
-- SELECT id, code, label, parent_id, core_id, sort_order
-- FROM fw.menu_node WHERE code='diag_log_master';


-- ─────────────────────────────────────────────────────────────
-- FINAL VERIFY (po všech krocích):
-- ─────────────────────────────────────────────────────────────
SELECT
    (SELECT count(*) FROM fw.data_source     WHERE code='diag_log_master') AS ds,
    (SELECT count(*) FROM fw.core            WHERE code='diag_log_master') AS core,
    (SELECT count(*) FROM fw.comp_grid_master WHERE code='diag_log_master') AS gm,
    (SELECT count(*) FROM fw.comp_grid_column
     WHERE grid_master_id = (SELECT id FROM fw.comp_grid_master WHERE code='diag_log_master')
    ) AS cols,
    (SELECT count(*) FROM fw.hw_registry     WHERE code='diag_log_master') AS hw,
    (SELECT count(*) FROM fw.menu_node       WHERE code='diag_log_master') AS mn;
-- Expected: 1 / 1 / 1 / 12 / 1 / 1
