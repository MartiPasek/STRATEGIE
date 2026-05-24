-- ============================================================
-- Phase Universal CRUD Etapa D-1 (REVIZE 24.5.2026 vecer)
-- ============================================================
-- Cil: aktivovat Smazat tlacitko v context menu + internal toolbar
--      pro Data Sources grid (menu_node id=51, core id=19).
--
-- Revize:
--   Puvodni script (24.5.2026 vecer #1) mel WHERE EXISTS guard na code
--   'system_new.framework_data_sources_overview' — tento code v fw.data_source
--   NEEXISTUJE. INSERT tichе propsal 0 rows, zadny error, zadny insert.
--   Diagnostika 4-step SQL chain odhalila skutecny code:
--
--     fw.menu_node id=51 "Data Sources" → core_id=19
--     fw.core id=19 → code 'framework_data_sources'
--     fw.comp_def id=64 root → data_source_id=10
--     fw.data_source id=10 → code 'framework_data_sources' (Phase 38.4 Krok 11-E, 11.5.2026)
--
-- Gotcha doctrine: INSERT ... WHERE EXISTS guards jsou silently
-- zero-rows pokud predicate je false. VZDY verify post-insert SELECT.
--
-- Pattern:
--   - INSERT 'delete' op pro fw.data_source id=10 (Marti's "ID je svaty")
--   - WHERE NOT EXISTS guard pro idempotency (re-run safe)
--   - Verify SELECT po insertu (Marti's "Nedelame botu" doctrine)
--   - NO_DATA_SET_KINDS doctrine (Krok 5.S Faze 5): delete nepotrebuje data_set_id
--
-- Po deployi:
--   - Backend grid_actions agreguje has_delete=true pro framework_data_sources
--   - Master grid internal toolbar: 🗑 Smazat enabled po row selection
--   - Master grid context menu: 🗑 Smazat polozka visible
--   - DELETE flow: /api/v1/erp/design/19/{row_id} → _resolve_entity_config_from_db
--     parse "FROM fw.data_source" → DELETE FROM fw.data_source WHERE id=:rid
-- ============================================================

BEGIN;

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
    10,             -- fw.data_source.id pro 'framework_data_sources' (Krok C diagnostika)
    NULL,           -- delete op nepotrebuje data_set (NO_DATA_SET_KINDS)
    'delete',       -- operation_kind
    NULL,           -- variant_code (Krok 5.K-B6 NULL allowed)
    FALSE,          -- is_default
    100,            -- sort_order
    'Universal CRUD Etapa D-1 revize (24.5.2026 vecer): hard DELETE row z fw.data_source'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = 10 AND operation_kind = 'delete'
);

-- Verify A: explicit count of delete ops post-insert
SELECT 'verify_delete_ops_count:' AS info, COUNT(*) AS cnt
FROM fw.data_source_op
WHERE data_source_id = 10 AND operation_kind = 'delete';
-- Expected: cnt = 1

-- Verify B: all ops pro fw.data_source id=10 (framework_data_sources)
SELECT 'framework_data_sources ops:' AS info,
       dso.id, dso.operation_kind, dso.variant_code,
       dso.is_default, dso.data_set_id, dso.description
FROM fw.data_source_op dso
WHERE dso.data_source_id = 10
ORDER BY dso.sort_order ASC, dso.id ASC;
-- Expected: 2 rows — 'select' (default existing) + 'delete' (new)

COMMIT;
