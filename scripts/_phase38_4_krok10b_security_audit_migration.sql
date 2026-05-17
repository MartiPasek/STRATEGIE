-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 10-B (11.5.2026 dopoledne): security_audit migration
-- ════════════════════════════════════════════════════════════════════════
-- Posledni ze 4 security grids do fw schema. Po execute:
--   - 4/4 security grids DB-driven (devices/users/whitelists/invites + audit)
--   - DROP hardcoded JS branch `if (mode === "security_audit")` v router.py
--
-- Marti's doctrine 10.5. večer (drží):
--   *„override tabulku stačí, nic jinyho moc nepotrebujes"*
--   = discrete sloupce v comp_grid_column drží defaults (cell_style /
--     cell_renderer / default_sort přímo), comp_def_prop chain zustáva
--     prázdná dokud nebude Object Inspector explicit potreba.
--
-- Source: hardcoded JS v modules/erp/api/router.py řádek 5829-5854
-- (11 sloupců: id/result/user_name/email_attempted/ip/layer_matched/
--  layer_detail/reason/internal/device_token_short/created_at)
--
-- Registry IDs použité (vsechny už existují ve frontend JS):
--   - VALUE_FORMATTER_REGISTRY: datetime_rel
--   - CELL_STYLE_REGISTRY:      result_security, mono
--   - CELL_RENDERER_REGISTRY:   yes_check
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- BEGIN/COMMIT atomic — pokud cokoli selže, rollback drží čistý stav.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 0. fw.data_source pre-flight (FK constraint pro comp_grid_master)
--    Pseudo-data_source — data fetch přes existing /security/audit-log
--    endpoint (Phase 38.3), comp_grid_master jen drží columns metadata.
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES
    ('security_audit', 1, 'Security audit log data source',
     'Phase 38.4 Krok 10-B: data fetch přes /security/audit-log endpoint, ne SQL.',
     'manual', FALSE, 250, 100, 'active', TRUE);

-- ════════════════════════════════════════════════════════════════════════
-- 1. fw.core (jádro per grid)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.core (code, label, description, layout_type)
VALUES
    ('security_audit', 'Security: Audit log',
     'Login attempts + IP whitelist matches + device cookie verifications. Event audit pro security probuzeni (Marti-AI doctrine 10.5.).',
     'list');

-- ════════════════════════════════════════════════════════════════════════
-- 2. fw.comp_grid_master (1 row pro security_audit)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_grid_master
    (code, name, description, data_source_code, default_record_limit,
     refresh_type, default_view_mode, status, is_system)
VALUES
    ('security_audit', 'Security: Audit log',
     'Audit events (logins, IP matches, device verifications). Pres /security/audit-log endpoint.',
     'security_audit', 100, 'manual', 'grid', 'active', TRUE);

-- ════════════════════════════════════════════════════════════════════════
-- 3. fw.comp_grid_column (11 rows per JS hardcode)
-- ════════════════════════════════════════════════════════════════════════
-- POZOR: explicit is_visible=TRUE všude (default schema, ale safety
-- after gotcha #79). Sort_order po 10 (10/20/.../110) pro budoucí
-- inserts mezi.

-- (1) ID — pinned left, numeric, default sort DESC (newest first)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, pinned, column_type,
     sort_order, is_visible, is_sortable, default_sort)
SELECT id, 'id', 'ID', 70, 'left', 'numericColumn',
       10, TRUE, TRUE, 'desc'
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (2) Result — color-coded per outcome (cell_style: result_security)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable, cell_style)
SELECT id, 'result', 'Result', 130,
       20, TRUE, TRUE, 'result_security'
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (3) User name
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable)
SELECT id, 'user_name', 'User', 150,
       30, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (4) Email attempted (login email, vc. neuspesnych pokusu o neexistujici emaily)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable)
SELECT id, 'email_attempted', 'Email attempted', 230,
       40, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (5) IP — monospace font (cell_style: mono)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable, cell_style)
SELECT id, 'ip', 'IP', 130,
       50, TRUE, FALSE, 'mono'
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (6) Layer matched (ip_whitelist / device_cookie / verify_token / sms_pre / ...)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable)
SELECT id, 'layer_matched', 'Layer', 110,
       60, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (7) Layer detail
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable)
SELECT id, 'layer_detail', 'Detail', 180,
       70, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (8) Reason — flex 1, min_width 200 (textovy detail proc layer matchnul/selhal)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, min_width, flex,
     sort_order, is_visible, is_sortable)
SELECT id, 'reason', 'Reason', 200, 1,
       80, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (9) Internal — boolean s ✓ ikonkou (cell_renderer: yes_check)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable, cell_renderer)
SELECT id, 'internal', 'Internal', 90,
       90, TRUE, FALSE, 'yes_check'
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (10) Device token short — krátká forma trusted_device cookie
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width,
     sort_order, is_visible, is_sortable)
SELECT id, 'device_token_short', 'Cookie', 100,
       100, TRUE, FALSE
FROM fw.comp_grid_master WHERE code = 'security_audit';

-- (11) Created at — relativni formatter (datetime_rel)
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter,
     sort_order, is_visible, is_sortable)
SELECT id, 'created_at', 'Když', 150, 'datetime_rel',
       110, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'security_audit';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.data_source WHERE code = 'security_audit') AS data_source_count,
    (SELECT COUNT(*) FROM fw.core WHERE code = 'security_audit') AS core_count,
    (SELECT COUNT(*) FROM fw.comp_grid_master WHERE code = 'security_audit') AS master_count,
    (SELECT COUNT(*) FROM fw.comp_grid_column gc
     JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
     WHERE gm.code = 'security_audit') AS column_count;
-- Expected:
--   data_source_count: 1
--   core_count:        1
--   master_count:      1
--   column_count:     11

-- ════════════════════════════════════════════════════════════════════════
-- AFTER EXECUTE — frontend cleanup
-- ════════════════════════════════════════════════════════════════════════
-- 1. Smaž hardcoded `if (mode === "security_audit") { ... }` blok v
--    modules/erp/api/router.py řádek 5829-5854 (gridColumns(mode) funkce).
-- 2. git add scripts/_phase38_4_krok10b_security_audit_migration.sql
--           modules/erp/api/router.py
--    git commit -F .git_commit_msg_phase38_4_krok10b.txt
--    git push origin feat/memory-rag:feat/memory-rag
-- 3. Cloud APP: git pull + Restart-Service STRATEGIE-API + Start-Sleep 3
-- 4. Smoke test:
--    Invoke-WebRequest http://127.0.0.1:8002/api/v1/erp/grid/security_audit/columns
--    Expected: 200 + JSON s 11 columns
-- 5. ERP UI smoke: System → Security → Audit log tab. Vidíš stejné 11
--    sloupců jako před migrací (color-coded result, mono IP, ✓ internal,
--    relativni "Když" čas, default sort DESC ID = newest first).
-- ════════════════════════════════════════════════════════════════════════
