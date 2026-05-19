-- ═══════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g — Etapa D v2 (19.5.2026 vecer)
--
-- Cíl: System view "JS audit log" — grid v System tree, real-time
-- visibility pro Marti-AI + Kristý + Marti, pre-pátek CRM stavba.
--
-- v2 (refactor z 16.5. ranní v1):
--   - DROP fw.comp_grid_master + fw.comp_grid_column INSERTs
--     (Krok 5.R-C+3 z 18.5. tyto tabulky dropnul, sjednocené do
--      fw.comp_grid + layout_json JSONB)
--   - Frontend autoColumns z DataSource response (Krok 5.R-C+5,
--     "nativne, ne tabulky" doctrine z 18.5.) → columns generated
--     dynamically z prvni row events[0]
--   - Custom labels/widths se ulozi later pres "Uložit sestavu" UI pattern
--     (Krok 5.R-C+1, user-driven layout)
--
-- 4 inserts:
--   1. fw.data_source — endpoint binding (delegate via hw_registry)
--   2. fw.core — kontejner s label
--   3. fw.hw_registry — endpoint URL + response_hint (rows_path='$.events')
--   4. fw.menu_node — sidebar tree node pod Security parent
--
-- Run: psql -h 10.200.188.12 -U "Marti-AI" -d data_db -f tento_soubor.sql
--      nebo DBeaver Marti-AI session, highlight celý soubor + Alt+X
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- ────────────────────────────────────────────────────────────────────────
-- 1. DATA_SOURCE (pseudo — data fetch pres diag-log/events endpoint)
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES
    ('diag_log_master', 1, 'Diag log master',
     'Phase 38.4 Krok 14g Etapa D v2: data fetch přes diag-log/events?view=master endpoint. autoColumns from response.',
     'manual', TRUE, 250, 500, 'active', TRUE)
ON CONFLICT (code, version) DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────
-- 2. CORE (kontejner pro grid)
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.core (code, label, description_user, layout_type)
VALUES
    ('diag_log_master', 'Diag log (master)',
     'JS+Python audit log master view — kdo + co + když (Marti''s NE-anonymous doctrine 16.5.).',
     'list')
ON CONFLICT (code) DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────
-- 3. HW_REGISTRY (endpoint binding)
--    response_hint.rows_path "$.events" — diag-log/events vraci
--    {ok, total, events: [...]} (NE rows).
--    Frontend erp_grid_dispatcher.js detects "events" key automaticky
--    (line 109: dd.rows || dd.events || dd.conversations).
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO fw.hw_registry
    (code, label, description, kind,
     endpoint_url, http_method, response_hint,
     shadow_mode, is_active, version)
VALUES
    ('diag_log_master', 'Diag log: Master view',
     'JS+Py audit log master view — Marti''s NE-anonymous doctrine. Phase 38.4 Krok 14g Etapa D v2.',
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
-- 4. MENU_NODE (sidebar tree item pod Security parent — sibling
--    pattern z security_audit / users)
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

    -- Next sort_order v parent scope
    SELECT COALESCE(MAX(sort_order), 0) + 10 INTO v_next_sort
    FROM fw.menu_node
    WHERE COALESCE(parent_id, 0) = COALESCE(v_security_parent_id, 0);

    INSERT INTO fw.menu_node
        (code, label, kind, parent_id, sort_order, core_id, is_immutable, status,
         description_user)
    VALUES
        ('diag_log_master', 'Diag log', 'list', v_security_parent_id,
         v_next_sort, v_core_id, FALSE, 'active',
         'JS + Python audit log (Phase 38.4 Krok 14g Etapa D v2). Master view: kdo + co + když. Real-time vidět errory napříč JS+Py+SQL.')
    ON CONFLICT (code) DO UPDATE SET
        label = EXCLUDED.label,
        kind = EXCLUDED.kind,
        core_id = EXCLUDED.core_id,
        status = EXCLUDED.status,
        description_user = EXCLUDED.description_user;

    RAISE NOTICE 'menu_node "diag_log_master" inserted/updated — parent_id=%, core_id=%, sort_order=%',
        v_security_parent_id, v_core_id, v_next_sort;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run after deploy):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT
--     (SELECT count(*) FROM fw.data_source WHERE code='diag_log_master') AS ds,
--     (SELECT count(*) FROM fw.core        WHERE code='diag_log_master') AS core,
--     (SELECT count(*) FROM fw.hw_registry WHERE code='diag_log_master') AS hw,
--     (SELECT count(*) FROM fw.menu_node   WHERE code='diag_log_master') AS menu;
-- Expected: ds=1, core=1, hw=1, menu=1

-- ════════════════════════════════════════════════════════════════════════
-- SMOKE TEST (po deploy):
-- ════════════════════════════════════════════════════════════════════════
-- 1. Hard reload UI (Ctrl+Shift+R)
-- 2. Pravý sidebar → System tree → Security → "Diag log"
-- 3. Klik → grid se otevře s autoColumns z events[0] response
-- 4. Default sort: created_at DESC (z backend ORDER BY)
-- 5. Vidět real-time errory z posledních 24h (parent gate — jen rodina)
--
-- Pokud sloupce vypadají bordel (raw camelCase, špatné widths):
--   → Klik "Uložit sestavu" v gridu (Krok 5.R-C+1 user-driven layout)
--   → Custom column labels/widths se uloží do fw.comp_grid layout_json
