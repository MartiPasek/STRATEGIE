-- ============================================================
-- CRM Foundation Krok 1 (27.5.2026) — Smoke test ZemeCis
-- ============================================================
-- Účel: Verify data_source_runner db_type dispatch na MSSQL path
--       (Phase 28-C composer-side MCP klient → eurosoft_strategie_query_raw).
--
-- Target tabulka: DB_EC.st.CRM_Kontakt_ZemeCis (11 rows, nejmenší CRM
-- číselník — minimum risk pro smoke).
--
-- Žádný menu_node / core / comp_def — jen data_set + data_source + op.
-- Smoke se testuje přes URL: /api/v1/erp/data/crm_zemecis_smoke?limit=5
--
-- Po smoke success (execution_path=mcp_mssql + rows non-empty) můžeme
-- pokračovat Krok 3 (CRM soudečky) + Krok 4 (CRM přehledy).
--
-- Reference: pattern z _phase_system_new_db_connections_grid_v3.sql (22.5.)
-- ============================================================

BEGIN;

-- ─── 1. fw.data_set — SQL s SELECT TOP (žádný :limit bind, MSSQL syntax) ──
INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'crm_zemecis_smoke',
    $sql$
SELECT TOP 100 *
FROM st.CRM_Kontakt_ZemeCis
ORDER BY ID
$sql$,
    2,  -- db_connection_id=2 = eurosoft_db_ec (db_type='mssql', default_db='DB_EC')
    'CRM Foundation Krok 1 smoke — verify MSSQL runner path via MCP',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_zemecis_smoke');

-- ─── 2. fw.data_source ─────────────────────────────────────────────────────
INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'crm_zemecis_smoke',
    'CRM Foundation: ZemeCis smoke',
    'Smoke test pro CRM Foundation Krok 1 (27.5.). Verify runner dispatch '
    || 'na db_type=mssql + Phase 28-C MCP klient + eurosoft_strategie_query_raw '
    || '+ JSON response shape (execution_path=mcp_mssql, rows non-empty).',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_zemecis_smoke');

-- ─── 3. fw.data_source_op — wire data_set s data_source ───────────────────
INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'crm_zemecis_smoke'),
    (SELECT id FROM fw.data_set    WHERE code = 'crm_zemecis_smoke'),
    'select', 'default', TRUE,
    'CRM Foundation smoke select default'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_zemecis_smoke')
      AND variant_code = 'default'
);

COMMIT;

-- ============================================================
-- VERIFY (run separately):
-- ============================================================
-- 1) Schema verify (PG side — co máme):
-- SELECT
--     ds.id AS data_source_id, ds.code, ds.name,
--     dset.id AS data_set_id, dset.code AS dataset_code,
--     dc.id AS db_connection_id, dc.code AS dc_code, dc.db_type, dc.default_db,
--     op.id AS op_id, op.operation_kind, op.variant_code
-- FROM fw.data_source ds
-- JOIN fw.data_source_op op ON op.data_source_id = ds.id
-- JOIN fw.data_set dset      ON dset.id = op.data_set_id
-- LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
-- WHERE ds.code = 'crm_zemecis_smoke';
--
-- Expected: db_type='mssql', default_db='DB_EC', operation_kind='select'
--
-- 2) Po Restart-Service STRATEGIE-API, browser test:
--    https://strategie-ai.com/api/v1/erp/data/crm_zemecis_smoke?limit=5
--
-- Expected JSON response:
-- {
--   "ok": true,
--   "data_source": {"code": "crm_zemecis_smoke", "name": "...", "id": N},
--   "operation": {"kind": "select", "variant": "default", "data_set_id": N},
--   "rows": [
--     {"ID": 1, "Kod": "CZ", "Nazev": "Česká republika", ...},
--     ...
--   ],
--   "row_count": 5,
--   "applied_params": {"limit": 5},
--   "execution_path": "mcp_mssql",   <<< KLÍČOVÉ: potvrzuje MSSQL path
--   "db_name": "DB_EC",
--   "batches_executed": 1
-- }
--
-- 3) Pokud execution_path="pg_native" → BUG, dispatch nezachytí mssql
-- 4) Pokud rows je [] → ZemeCis je prázdné nebo MCP failed silent
-- 5) Pokud HTTP 500 → check fw.diag_log pro real error (gotcha #102)
-- ============================================================

-- ============================================================
-- ROLLBACK (pokud potřeba):
-- ============================================================
-- BEGIN;
-- DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_zemecis_smoke');
-- DELETE FROM fw.data_set       WHERE code = 'crm_zemecis_smoke';
-- DELETE FROM fw.data_source    WHERE code = 'crm_zemecis_smoke';
-- COMMIT;
