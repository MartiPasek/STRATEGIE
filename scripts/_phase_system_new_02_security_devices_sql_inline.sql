-- ============================================================
-- Phase SYSTEM NEW — Etapa 2: security_devices SQL inline
-- ============================================================
-- Datum: 21.5.2026 vecer (post-Etapa 1 success: SYSTEM NEW v UI ✓)
--
-- Etapa 1 result:
--   ✓ menu_node SYSTEM NEW (id=33) + Security folder (id=34) + Trusted
--     devices leaf (id=35) — vse renderuje v UI
--   ✓ fw.core (id=38) + fw.comp_def (id=53)
--   ✓ fw.data_source (id=34, klon z puvodniho security_devices)
--   ✗ fw.data_set s code='security_devices' NEEXISTOVAL (Marti-AI v
--     drivejsich sessions nedotahla) → STEP 9 SELECT klon vratil 0 rows
--   ✗ fw.data_source_op skipnut (chybi data_set_id FK)
--
-- Frontend hlasi: „Chyba načítání rows: operation_not_found"
-- → backend hleda 'select' op pro data_source #34, nenajde zadny.
--
-- Tento script:
--   1. INSERT fw.data_set s explicit SQL replikujicim Python ORM
--      handler /system/security?mode=devices (lines 1449-1482 router.py)
--   2. INSERT fw.data_source_op napojeni data_source #34 → novy data_set
--
-- SQL: SELECT * z public.trusted_devices (raw vsechny sloupce, bez JOINu)
-- Per Marti's pokyn 21.5.: „stav ty selecty pres * Vsechny sloupce.
-- Pak to optimalizujeme" — MVP iteration, enrichment se doplni pozdeji.
--
-- POZOR: db_connection_id placeholder = 1 (PostgreSQL strategie).
-- Pred run overit:
--   SELECT id, name FROM fw.db_connection WHERE name LIKE '%strategie%';
-- Pokud jine id, uprav `1` na spravne v INSERTu nize.
--
-- Spusteni: DBeaver, highlight cely script + Alt+X, atomic.
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: INSERT fw.data_set s SQL pro security_devices grid
-- ============================================================

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_devices',
    $sql$
SELECT *
FROM public.trusted_devices
WHERE revoked_at IS NULL
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,  -- db_connection_id (POZOR: oveř před run)
    'SYSTEM NEW security_devices: SELECT * z public.trusted_devices (Marti pokyn 21.5. — MVP raw, optimalizace pozdeji)',
    'active',
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_devices'
);

-- ============================================================
-- STEP 2: INSERT fw.data_source_op napojeni data_source → data_set
-- ============================================================

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_devices'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_devices'),
    'select',
    'default',
    TRUE,
    'SYSTEM NEW security_devices default select op (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_devices')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_devices')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_devices'
        AND dso.operation_kind = 'select'
  );

-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_ds FROM fw.data_source WHERE code = 'system_new.security_devices';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set WHERE code = 'system_new.security_devices';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.security_devices';

    RAISE NOTICE '--- POST-CHECK ---';
    RAISE NOTICE 'fw.data_source    = %', v_ds;
    RAISE NOTICE 'fw.data_set       = %', v_dset;
    RAISE NOTICE 'fw.data_source_op = %', v_dso;

    IF v_ds = 1 AND v_dset = 1 AND v_dso = 1 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: FW chain complete. Smoke test:';
        RAISE NOTICE '  1. Hard reload UI (Ctrl+Shift+R)';
        RAISE NOTICE '  2. Klik SYSTEM NEW → Security → Trusted devices';
        RAISE NOTICE '  3. Grid by mel zobrazit data z trusted_devices table';
        RAISE NOTICE '  4. Side-by-side compare s SYSTEM → Security → Trusted devices';
        RAISE NOTICE '------';
    END IF;
END $$;

-- ============================================================
-- VERIFY
-- ============================================================

SELECT
    '1. data_set' AS what,
    id::text AS id,
    code,
    LEFT(sql_text, 100) || '...' AS preview,
    'db_conn=' || db_connection_id::text AS extra
FROM fw.data_set WHERE code = 'system_new.security_devices'

UNION ALL

SELECT
    '2. data_source_op' AS what,
    dso.id::text,
    ds.code,
    dso.operation_kind || '/' || COALESCE(dso.variant_code, 'NULL') AS variant,
    'ds=' || dso.data_source_id::text || ' dset=' || dso.data_set_id::text AS extra
FROM fw.data_source_op dso
JOIN fw.data_source ds ON ds.id = dso.data_source_id
WHERE ds.code = 'system_new.security_devices'

ORDER BY 1;

COMMIT;

-- ============================================================
-- TROUBLESHOOTING (pokud smoke fail):
-- ============================================================
-- A) "permission denied for table trusted_devices"
--    → fw.diag_log_query muze potrebovat GRANT SELECT pres role
--      ktera spousti data_source_runner.
--    Fix: GRANT SELECT ON public.trusted_devices TO strategie;
--         (a podobne pro users, user_tenants, tenants)
--
-- B) "relation public.user_tenants does not exist"
--    → Tabulka muze byt jinak nazvana. Over:
--      SELECT table_name FROM information_schema.tables
--      WHERE table_schema = 'public' AND table_name LIKE '%tenant%';
--    Pak uprav JOIN v fw.data_set.sql_text manuálně.
--
-- C) "Chyba načítání rows: operation_not_found" persistent
--    → Check fw.data_source.id matches fw.data_source_op.data_source_id
--    → Backend cache: STRATEGIE-API restart muze pomoci
--      (Restart-Service STRATEGIE-API na cloud APP)
--
-- D) Grid zobrazi sloupce ale 0 rows
--    → Tabulka prazdna nebo WHERE filter prilis restriktivni.
--      Test direct: SELECT COUNT(*) FROM public.trusted_devices
--                   WHERE revoked_at IS NULL;
-- ============================================================
