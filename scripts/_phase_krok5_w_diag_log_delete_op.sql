-- ============================================================
-- Phase 38.4 Krok 5.W (23.5.2026): Diag log DELETE op
-- ============================================================
-- Marti: "Na tomto prehledu si odladime 1. Mazani vet pres Datasource OP
--   delete... Prosim pridej adekvatni data_source_op pro mazani"
--
-- Cil: pridat data_source_op kind='delete' pro existing data_source
--   'system_new.security_diag_log'. Po deploy Krok 5.S toolbar
--   'Smazat' button bude visible (data_source_op driven), klik =
--   DELETE FROM fw.diag_log WHERE id = :id (selected row PK).
--
-- POZN: doctrine "audit RO append-only" (Marti's Fix N 21.5.) ríká
--   ze diag_log NEMA mit UPDATE/DELETE v produkci. Diag log je tady
--   pouzit jako PLAYGROUND pro odladeni delete flow obecne (1000+
--   rows, ztrata neskolika error logu nevadi). Po smoke pak tento
--   pattern aplikujeme na ostatni grids kde DELETE da smysl
--   (DataSets, DataSources, Knowledge Entries atd.).
--
-- Pattern (analog Etapa 7c data_source_op rows):
--   1. fw.data_set s sql_text = 'DELETE FROM fw.diag_log WHERE id = :id'
--   2. fw.data_source_op s operation_kind='delete' + data_set FK
--
-- Spusteni v DBeaveru: highlight cely script + Alt+X
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  1. data_set 'system_new.security_diag_log.delete'       ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_diag_log.delete',
    $sql$
DELETE FROM fw.diag_log
WHERE id = :id
RETURNING id
    $sql$,
    1,
    'SYSTEM NEW diag_log: DELETE jeden radek per ID (Krok 5.W playground, 23.5.2026)',
    'active', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_set
    WHERE code = 'system_new.security_diag_log.delete'
);


-- ╔══════════════════════════════════════════════════════════╗
-- ║  2. data_source_op kind='delete' pro existing data_source║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_diag_log'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_diag_log.delete'),
    'delete', 'default', TRUE,
    'SYSTEM NEW diag_log DELETE op (Krok 5.W playground, 23.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_diag_log')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_diag_log.delete')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_diag_log'
        AND dso.operation_kind = 'delete'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_dset INT;
    v_dso_select INT;
    v_dso_delete INT;
BEGIN
    SELECT COUNT(*) INTO v_dset
        FROM fw.data_set WHERE code = 'system_new.security_diag_log.delete';
    SELECT COUNT(*) INTO v_dso_select
        FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.security_diag_log' AND dso.operation_kind = 'select';
    SELECT COUNT(*) INTO v_dso_delete
        FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.security_diag_log' AND dso.operation_kind = 'delete';

    RAISE NOTICE '--- POST-CHECK diag_log delete op ---';
    RAISE NOTICE 'data_set delete=%, data_source_op select=%, delete=%',
        v_dset, v_dso_select, v_dso_delete;

    IF v_dset = 1 AND v_dso_select = 1 AND v_dso_delete = 1 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: diag_log delete op pridany. Smoke:';
        RAISE NOTICE '  1. Hard reload UI';
        RAISE NOTICE '  2. SYSTEM NEW > Security > Diag log';
        RAISE NOTICE '  3. Toolbar Smazat button by mel byt visible';
        RAISE NOTICE '  4. Vyber row + klik Smazat = DELETE FROM diag_log';
        RAISE NOTICE '------';
    END IF;
END $$;

-- VERIFY: vsechny ops pro diag_log data_source
SELECT
    ds.code AS data_source_code,
    dso.operation_kind,
    dso.variant_code,
    dso.is_default,
    dset.code AS data_set_code,
    LEFT(dset.sql_text, 80) AS sql_preview
FROM fw.data_source_op dso
JOIN fw.data_source ds ON ds.id = dso.data_source_id
LEFT JOIN fw.data_set dset ON dset.id = dso.data_set_id
WHERE ds.code = 'system_new.security_diag_log'
ORDER BY dso.operation_kind;

COMMIT;

-- ============================================================
-- Po commitu:
--   Hard reload UI → SYSTEM NEW → Security → Diag log
--   Toolbar by mel zobrazit:
--     [+ Nový] [⚙ Oprava] [🗑 Smazat] [⟳ Obnovit]
--                          ^^^^^^^^^ — toto je nove visible (delete op driven)
--
--   Klik Smazat na selected row:
--     1. Confirm dialog ("Opravdu smazat radek id=X?")
--     2. POST /api/v1/erp/data-source/{ds_code}/exec
--        body: {variant: 'default', kind: 'delete', params: {id: X}}
--     3. Backend exec DELETE SQL s :id bind param
--     4. Refresh grid
--
-- Po stable smoke -> pattern aplikujeme na ostatni grids
-- kde DELETE da smysl.
-- ============================================================
