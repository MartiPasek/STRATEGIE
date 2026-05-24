-- ============================================================
-- Phase Master-Detail: FW chain pro data_source_op nested grid
-- ============================================================
-- Datum: 24.5.2026 vecer
-- Cil: Drop HW (hardcoded /design/fw-data-source/{id}/operations
--      + autoColumns v custom rendereru). Postavit fw.data_source
--      + fw.data_set + fw.data_source_op chain.
--
-- Benefit: layoutKey = "ds_<NEW_ID>" (validní format) → nested grid
--          dostane nativní persistence sloupců (fw.comp_grid) bez
--          potřeby nové tabulky nebo backend validator extension.
--
-- Marti's doctrine "fw self edited" (11.5.) — vše skrz fw infra,
-- nehardcodovat.
--
-- Co NEpotřebujeme (= rozdíl proti standardnímu gridu z Etapa 7b):
--   - menu_node (detail grid není v sidebar tree)
--   - core (není to standalone view, je inside-master)
--   - comp_def (custom renderer ho vytváří dynamicky runtime)
--
-- Co potřebujeme (3 INSERTs):
--   1. fw.data_set — SQL s :master_id bind param
--   2. fw.data_source — code='system_new.framework_data_source_ops'
--   3. fw.data_source_op — default select op (data_set_id=NEW)
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  1/3 fw.data_set — parametrized SELECT                   ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.framework_data_source_ops',
    $sql$
SELECT
    op.id,
    op.variant_code,
    op.operation_kind,
    op.sort_order,
    op.is_default,
    op.description,
    ds.id           AS data_set_id,
    ds.code         AS data_set_code,
    ds.description  AS data_set_description,
    ds.status       AS data_set_status,
    dc.code         AS db_connection_code,
    dc.default_db   AS db_connection
FROM fw.data_source_op op
LEFT JOIN fw.data_set ds        ON ds.id = op.data_set_id
LEFT JOIN fw.db_connection dc   ON dc.id = ds.db_connection_id
WHERE op.data_source_id = :master_id
ORDER BY op.sort_order ASC, op.id ASC
    $sql$,
    1,  -- db_connection_id (data_db / strategie_pg)
    'Master-detail: operations per data_source (param :master_id)',
    'active', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_set
    WHERE code = 'system_new.framework_data_source_ops'
);


-- ╔══════════════════════════════════════════════════════════╗
-- ║  2/3 fw.data_source — code + metadata                    ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.framework_data_source_ops',
    'Framework: Data Source Operations (per master)',
    'Master-detail: data_source_op rows per master data_source.id',
    'on_focus', 'active', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source
    WHERE code = 'system_new.framework_data_source_ops'
);


-- ╔══════════════════════════════════════════════════════════╗
-- ║  3/3 fw.data_source_op — default select                  ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.framework_data_source_ops'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.framework_data_source_ops'),
    'select', 'default', TRUE,
    'Default select per :master_id'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.framework_data_source_ops')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.framework_data_source_ops')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.framework_data_source_ops'
        AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK + return NEW data_source.id pro layoutKey
-- ============================================================

DO $$
DECLARE
    v_ds INT;
    v_dset INT;
    v_dso INT;
    v_ds_id INT;
BEGIN
    SELECT COUNT(*), MAX(id) INTO v_ds, v_ds_id
        FROM fw.data_source
        WHERE code = 'system_new.framework_data_source_ops';

    SELECT COUNT(*) INTO v_dset FROM fw.data_set
        WHERE code = 'system_new.framework_data_source_ops';

    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.framework_data_source_ops';

    RAISE NOTICE '--- POST-CHECK Master-Detail data_source_ops FW chain ---';
    RAISE NOTICE 'data_source=% (id=%), data_set=%, data_source_op=%',
        v_ds, v_ds_id, v_dset, v_dso;

    IF v_ds = 1 AND v_dset = 1 AND v_dso = 1 THEN
        RAISE NOTICE '';
        RAISE NOTICE 'SUCCESS: FW chain ready.';
        RAISE NOTICE '';
        RAISE NOTICE 'NEXT STEPS:';
        RAISE NOTICE '  1. Frontend custom renderer (data_source_op_detail.js):';
        RAISE NOTICE '     - fetch URL → /api/v1/erp/data/system_new.framework_data_source_ops?master_id=<X>';
        RAISE NOTICE '     - nested ErpDataGrid layoutKey = "ds_%"', v_ds_id;
        RAISE NOTICE '     - autoLoadDefault = true (persistence funguje!)';
        RAISE NOTICE '  2. Backend cleanup:';
        RAISE NOTICE '     - drop /design/fw-data-source/{id}/operations endpoint';
        RAISE NOTICE '  3. Smoke: hard reload, expand master row, sortuj/hide/resize sloupce,';
        RAISE NOTICE '     uloz sestavu, reload, ověř persistence';
    END IF;
END $$;

-- VERIFY: return data_source.id pro layoutKey hardcode v rendereru
SELECT
    id AS data_source_id,
    code,
    name,
    status,
    'layoutKey = ds_' || id::text AS frontend_layout_key
FROM fw.data_source
WHERE code = 'system_new.framework_data_source_ops';

COMMIT;

-- ============================================================
-- PO COMMITU:
--   Vrať mi výsledek SELECT (data_source.id) — potřebuji ho pro
--   hardcode v custom rendereru jako layoutKey "ds_<ID>".
--
--   Pak udělám:
--   - Update data_source_op_detail.js (fetch + layoutKey + autoLoad)
--   - Drop /design/fw-data-source/{id}/operations z router.py (~30 řádků)
--   - Commit + push + cloud APP pull + restart + hard reload
--   - Smoke: persistence sloupců + filters + formatting rules
-- ============================================================
