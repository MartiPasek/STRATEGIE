-- ============================================================
-- Phase SYSTEM NEW — Etapa 4: diag_log grid
-- ============================================================
-- Datum: 21.5.2026 vecer
-- Marti: „SUPER. FINGUJI... Jeste schazi DIAG LOG"
--
-- Po 5/5 security grids LIVE pridavam diag_log jako 6. polozku
-- v Security folder (sort_order=600).
--
-- Source: fw.diag_log (Phase 38.4 Krok 14g Etapa A, 16.5.2026,
-- audit RO append-only doctrine z 21.5. ranniho)
--
-- Pattern: identicky s Etapa 3 (SELECT * + WHERE NOT EXISTS guards).
-- DB connection: 1 (PostgreSQL strategie).
--
-- Spusteni v DBeaveru: highlight cely script + Alt+X
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  6. grid v Security: diag_log (z fw.diag_log)            ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.security_diag_log', 'Diag log', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    600,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_diag_log');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_diag_log', 'Diag log',
    'SYSTEM NEW diag_log: SELECT * z fw.diag_log (audit RO append-only)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.security_diag_log');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_diag_log')
WHERE code = 'system_new.security_diag_log' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_diag_log', 'Diag log',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_diag_log'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_security_diag_log');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_diag_log',
    'Security: Diag log',
    'SYSTEM NEW diag_log data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_diag_log');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_diag_log')
WHERE name = 'grid_system_new_security_diag_log' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_diag_log');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_diag_log',
    $sql$
SELECT *
FROM fw.diag_log
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW diag_log: SELECT * z fw.diag_log (Marti MVP raw, audit RO doctrine 21.5.)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_diag_log');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_diag_log'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_diag_log'),
    'select', 'default', TRUE,
    'SYSTEM NEW diag_log default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_diag_log')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_diag_log')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_diag_log' AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_core INT;
    v_compdef INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_menu    FROM fw.menu_node WHERE code = 'system_new.security_diag_log';
    SELECT COUNT(*) INTO v_core    FROM fw.core      WHERE code = 'system_new.security_diag_log';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def  WHERE name = 'grid_system_new_security_diag_log';
    SELECT COUNT(*) INTO v_ds      FROM fw.data_source WHERE code = 'system_new.security_diag_log';
    SELECT COUNT(*) INTO v_dset    FROM fw.data_set    WHERE code = 'system_new.security_diag_log';
    SELECT COUNT(*) INTO v_dso     FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code = 'system_new.security_diag_log';

    RAISE NOTICE '--- POST-CHECK diag_log ---';
    RAISE NOTICE 'menu_node=%, core=%, comp_def=%, data_source=%, data_set=%, data_source_op=%',
        v_menu, v_core, v_compdef, v_ds, v_dset, v_dso;

    IF v_menu = 1 AND v_core = 1 AND v_compdef = 1
       AND v_ds = 1 AND v_dset = 1 AND v_dso = 1 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: diag_log grid hotov. Smoke:';
        RAISE NOTICE '  1. Hard reload UI';
        RAISE NOTICE '  2. SYSTEM NEW → Security → Diag log';
        RAISE NOTICE '  3. Grid by mel zobrazit fw.diag_log rows';
        RAISE NOTICE '------';
    END IF;
END $$;

-- VERIFY: prehled vsech 6 security gridu pod SYSTEM NEW
SELECT
    code,
    label,
    sort_order,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.security_%' OR code = 'system_new.security'
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- Po commitu:
--   Hard reload UI → SYSTEM NEW → Security:
--     ├ Trusted devices    ✓
--     ├ STRATEGIE Users    ✓
--     ├ IP whitelists      ✓
--     ├ Magic invites      ✓
--     ├ Auth audit         ✓
--     └ Diag log           ← NEW
--
-- Security batch 6/6 complete v SYSTEM NEW. ✨
-- ============================================================
