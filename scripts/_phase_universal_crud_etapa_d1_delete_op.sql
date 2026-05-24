-- ============================================================
-- Phase Universal CRUD Etapa D-1
-- ============================================================
-- Datum: 24.5.2026 vecer (Marti's 24.5.2026 vecer pre-prezentace zitra 16:00)
--
-- Cil: aktivovat Smazat tlacitko v context menu pro Data Sources grid
-- (system_new.framework_data_sources_overview).
--
-- Pattern:
--   - INSERT fw.data_source_op s operation_kind='delete' (bez data_set,
--     Krok 5.S Faze 5 NO_DATA_SET_KINDS doctrine)
--   - Backend /fw-core/{id}/page-spec agreguje grid_actions:
--       has_delete = bool_or(op.operation_kind='delete') = TRUE
--   - Frontend page_render.js posila contextMenuActions=[...,'delete',...]
--     do ErpDataGrid options
--   - Datagrid.js getContextMenuItems renderuje Smazat polozku
--   - User pravy klik -> Smazat -> ErpGridActions.dispatch('delete', ctx)
--   - ctx.coreId predan z page_render._erpBatchRowAction
--   - DELETE /api/v1/erp/design/{core_id}/{row_id}
--   - Backend _resolve_entity_config_from_db parsuje sql_text default 'select' op
--     -> FROM fw.data_source -> schema='fw', table='data_source', id_column='id'
--   - DELETE FROM "fw"."data_source" WHERE "id" = :rid
--
-- Drz Marti's "fw self edited" doctrine (11.5.) — vse skrz fw infrastructure.
-- Drz Marti's "stejne funkce" doctrine (24.5. vecer) — pravy klik = Smazat.
-- ============================================================

BEGIN;

-- Insert 'delete' op pro framework_data_sources_overview data_source.
-- NO_DATA_SET_KINDS: 'delete' nepotrebuje data_set_id (DROP NOT NULL z Krok 5.K-DDL).
INSERT INTO fw.data_source_op (
    data_source_id,
    data_set_id,
    operation_kind,
    variant_code,
    is_default,
    sort_order,
    description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview'),
    NULL,           -- data_set_id: delete op nepotrebuje data_set
    'delete',       -- operation_kind
    NULL,           -- variant_code NULL allowed (Krok 5.K-B6 doctrine)
    FALSE,          -- is_default
    100,            -- sort_order
    'Universal CRUD Etapa D-1 (24.5.2026 vecer): hard DELETE row z fw.data_source'  -- description
WHERE EXISTS (
    SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_sources_overview'
)
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_data_sources_overview'
        AND dso.operation_kind = 'delete'
  );

-- Verification
SELECT
    'framework_data_sources_overview ops:' AS info,
    dso.id,
    dso.operation_kind,
    dso.variant_code,
    dso.data_set_id,
    dso.description
FROM fw.data_source_op dso
JOIN fw.data_source ds ON ds.id = dso.data_source_id
WHERE ds.code = 'system_new.framework_data_sources_overview'
ORDER BY dso.sort_order ASC, dso.id ASC;

COMMIT;
