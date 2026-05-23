-- ============================================================
-- Phase SYSTEM NEW — Etapa 1: Root + security_devices klon
-- ============================================================
-- Datum:  21.5.2026 (večer, post-seminář)
-- Autor:  Claude (id=23) per Marti-AI's 8-step návod
-- Rozhodnutí Marti:
--   1A — SYSTEM NEW jako top-level sibling SYSTEM (parent_id=NULL)
--   2B — dotted namespace codes (system_new.security_devices)
--   3A — clone fw.data_source + fw.data_set (NEW rows, NE reuse)
-- ============================================================
-- Cíl:
--   1. Vytvořit nový top-level soudeček SYSTEM NEW
--   2. Vytvořit podsložku Security pod SYSTEM NEW
--   3. Vytvořit první FW grid security_devices jako KLON
--      existujícího HC endpointu /system/security?mode=devices
--
-- Strategický plán (Marti's *„zbavit se hardcoded"* doctrine, 11.5.):
--   - SYSTEM NEW = paralelní větev se 100% FW duplikáty
--   - Po validaci všech 5 security gridů side-by-side: pokračovat A3 + HC
--   - Po všech FW LIVE: smazat originály + cleanup Python kódu
--   - „create-new-verify-delete-old" safe migration pattern
-- ============================================================
-- Spuštění v DBeaveru:
--   1. Connection: PostgreSQL data_db jako Marti-AI (db_owner fw)
--   2. Highlight celý script + Alt+X (Run All)
--   3. Verify NOTICE messages (Pre-check + diagnostika)
--   4. Verify final SELECT (8 rows: root + folder + leaf + core + comp_def + ds + dset + dso)
--   5. Pokud OK → COMMIT (automatic na konci)
--   6. Pokud ne → ROLLBACK; (manualně)
--
-- Rollback (pokud cokoli failne):
--   ROLLBACK;
--   Nebo (po commitu):
--     DELETE FROM fw.data_source_op WHERE data_source_id IN
--       (SELECT id FROM fw.data_source WHERE code LIKE 'system_new.%');
--     DELETE FROM fw.data_set WHERE code LIKE 'system_new.%';
--     DELETE FROM fw.data_source WHERE code LIKE 'system_new.%';
--     DELETE FROM fw.comp_def WHERE name LIKE 'grid_system_new_%';
--     DELETE FROM fw.core WHERE code LIKE 'system_new.%';
--     DELETE FROM fw.menu_node WHERE code LIKE 'system_new.%' OR code = 'system_new';
-- ============================================================

BEGIN;

-- ============================================================
-- PRE-CHECK: Diagnostika existujícího stavu
-- ============================================================
-- Step 7+9 klonují z původního security_devices.
-- Pokud original neexistuje v fw.data_source/data_set, klon vrátí 0 rows
-- a Marti musí dodat SQL inline (viz NOTICE výstup).

DO $$
DECLARE
    v_ds_orig_count INT;
    v_dset_orig_count INT;
    v_ds_orig_sql TEXT;
BEGIN
    SELECT COUNT(*) INTO v_ds_orig_count
    FROM fw.data_source
    WHERE code = 'security_devices' AND status = 'active';

    SELECT COUNT(*) INTO v_dset_orig_count
    FROM fw.data_set
    WHERE code = 'security_devices' AND status = 'active';

    RAISE NOTICE '--- PRE-CHECK ---';
    RAISE NOTICE 'fw.data_source rows pro code=''security_devices'' (active): %', v_ds_orig_count;
    RAISE NOTICE 'fw.data_set    rows pro code=''security_devices'' (active): %', v_dset_orig_count;

    IF v_dset_orig_count > 0 THEN
        SELECT LEFT(sql_text, 100) INTO v_ds_orig_sql
        FROM fw.data_set
        WHERE code = 'security_devices' AND status = 'active'
        LIMIT 1;
        RAISE NOTICE 'fw.data_set sql_text preview: %...', v_ds_orig_sql;
    END IF;

    IF v_ds_orig_count = 0 OR v_dset_orig_count = 0 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'POZOR: Original data_source/data_set pro security_devices neexistuje (nebo neactive).';
        RAISE NOTICE 'Script vytvori strukturu (menu_node, core, comp_def),';
        RAISE NOTICE 'ale data_source + data_set + data_source_op se NEZALOZI (klon prazdny).';
        RAISE NOTICE 'Pro dotazeni FW gridu doplnit SQL inline (Marti dodá z HC handleru).';
        RAISE NOTICE 'Soubor: modules/erp/api/router.py, hledat /system/security mode=devices';
        RAISE NOTICE '------';
    END IF;
END $$;

-- ============================================================
-- STEP 1: SYSTEM NEW root (parent_id=NULL, top-level sibling)
-- ============================================================

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new', 'SYSTEM NEW', 'folder', NULL, 9999,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new'
);

-- ============================================================
-- STEP 2: Security sub-folder pod SYSTEM NEW
-- ============================================================
-- Label „Security" identický s originálem (Marti's „identicka kopie")

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.security', 'Security', 'folder',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new'),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security'
);

-- ============================================================
-- STEP 3: security_devices menu_node (leaf, kind='form')
-- ============================================================
-- core_id se nastaví v STEP 5 (po vytvoření core)

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.security_devices', 'Trusted devices', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_devices'
);

-- ============================================================
-- STEP 4: security_devices fw.core (layout_type='list')
-- ============================================================

-- Pozn.: fw.core po Krok 5.P slim (17.5. večer + task #257):
--   layout_type, template_id, layout_template DROPPED — patří na fw.comp_def
--   (form root). fw.core je pure „kontejner" (Marti's doctrine).
INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.security_devices', 'Trusted devices',
    'SYSTEM NEW klon z security_devices (HC migration, 21.5.2026)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.core WHERE code = 'system_new.security_devices'
);

-- ============================================================
-- STEP 5: UPDATE menu_node SET core_id = nový core.id
-- ============================================================

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_devices')
WHERE code = 'system_new.security_devices'
  AND core_id IS NULL;

-- ============================================================
-- STEP 6: security_devices fw.comp_def (grid type_id=306, region 'main')
-- ============================================================
-- data_source_id se nastaví v STEP 8 (po vytvoření data_source)

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_devices',
    'Trusted devices',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_devices'),
    306,  -- list grid
    'main',
    100,
    TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.comp_def
    WHERE name = 'grid_system_new_security_devices'
);

-- ============================================================
-- STEP 7: KLON fw.data_source z původního 'security_devices'
-- ============================================================
-- Marti's 3A: NEW row, ne reuse. SELECT FROM existing, INSERT s novým code.

-- Pozn.: fw.data_source nema audit fields (per sprint_d_DDL pattern z 17.5.).
-- Ma `is_system` BOOLEAN (na rozdil od fw.menu_node, ktery ho dropnul).
INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_devices',
    name,
    COALESCE(description, '') || ' (SYSTEM NEW klon z security_devices, 21.5.2026)',
    refresh_type,
    'active',
    TRUE
FROM fw.data_source
WHERE code = 'security_devices'
  AND status = 'active'
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source
      WHERE code = 'system_new.security_devices'
  )
LIMIT 1;

-- ============================================================
-- STEP 8: UPDATE comp_def SET data_source_id = nový data_source.id
-- ============================================================
-- Pokud klon v STEP 7 nezalozil row (orig neexistuje), data_source_id zustane NULL.

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_devices')
WHERE name = 'grid_system_new_security_devices'
  AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_devices');

-- ============================================================
-- STEP 9: KLON fw.data_set z původního (SQL text)
-- ============================================================
-- Klíčový krok — kopíruje sql_text (definice gridu) + db_connection_id.

-- Pozn.: fw.data_set bez audit fields, bez `kind` (Krok 5.L-D z 17.5. dropnul),
-- ma `is_system` BOOLEAN, `parameters` JSONB (nullable, defaults).
INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_devices',
    sql_text,
    db_connection_id,
    COALESCE(description, '') || ' (SYSTEM NEW klon z security_devices, 21.5.2026)',
    'active',
    TRUE
FROM fw.data_set
WHERE code = 'security_devices'
  AND status = 'active'
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_set
      WHERE code = 'system_new.security_devices'
  )
LIMIT 1;

-- ============================================================
-- STEP 10: fw.data_source_op (select default)
-- ============================================================
-- Pouze pokud STEP 7+9 obě uspěly (jinak FK NULL → bypass přes EXISTS guard).

-- Pozn.: fw.data_source_op bez audit fields (per 5.I-A pattern).
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
    'SYSTEM NEW klon z security_devices, 21.5.2026'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_devices')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_devices')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_devices'
        AND dso.operation_kind = 'select'
        AND dso.variant_code = 'default'
  );

-- ============================================================
-- POST-CHECK: Diagnostika výsledného stavu
-- ============================================================

DO $$
DECLARE
    v_ds_new_count INT;
    v_dset_new_count INT;
    v_dso_new_count INT;
BEGIN
    SELECT COUNT(*) INTO v_ds_new_count
    FROM fw.data_source WHERE code = 'system_new.security_devices';

    SELECT COUNT(*) INTO v_dset_new_count
    FROM fw.data_set WHERE code = 'system_new.security_devices';

    SELECT COUNT(*) INTO v_dso_new_count
    FROM fw.data_source_op dso
    JOIN fw.data_source ds ON ds.id = dso.data_source_id
    WHERE ds.code = 'system_new.security_devices';

    RAISE NOTICE '--- POST-CHECK ---';
    RAISE NOTICE 'fw.data_source     pro system_new.security_devices: %', v_ds_new_count;
    RAISE NOTICE 'fw.data_set        pro system_new.security_devices: %', v_dset_new_count;
    RAISE NOTICE 'fw.data_source_op  pro system_new.security_devices: %', v_dso_new_count;

    IF v_ds_new_count = 1 AND v_dset_new_count = 1 AND v_dso_new_count = 1 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: FW grid system_new.security_devices kompletni.';
        RAISE NOTICE 'Smoke: hard reload UI + klik SYSTEM NEW → Security → Trusted devices';
        RAISE NOTICE '------';
    ELSIF v_ds_new_count = 0 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'INCOMPLETE: data_source klon vrátil 0 rows (orig security_devices neexistuje).';
        RAISE NOTICE 'Strukura (menu_node + core + comp_def) je založena.';
        RAISE NOTICE 'TODO: Marti dodat SQL inline pro data_set, pak retry STEP 7+8+9+10.';
        RAISE NOTICE '------';
    END IF;
END $$;

-- ============================================================
-- VERIFY: Final state (řazené podle hierarchie)
-- ============================================================

SELECT
    '1. menu_node SYSTEM NEW root' AS what,
    id::text,
    code,
    label,
    parent_id::text AS parent_id,
    core_id::text AS core_id
FROM fw.menu_node WHERE code = 'system_new'

UNION ALL

SELECT
    '2. menu_node Security folder' AS what,
    id::text, code, label, parent_id::text, core_id::text
FROM fw.menu_node WHERE code = 'system_new.security'

UNION ALL

SELECT
    '3. menu_node Trusted devices leaf' AS what,
    id::text, code, label, parent_id::text, core_id::text
FROM fw.menu_node WHERE code = 'system_new.security_devices'

UNION ALL

SELECT
    '4. core security_devices' AS what,
    id::text, code, label, description_user, NULL
FROM fw.core WHERE code = 'system_new.security_devices'

UNION ALL

SELECT
    '5. comp_def grid' AS what,
    id::text, name, caption, 'core_id=' || core_id::text, 'ds_id=' || COALESCE(data_source_id::text, 'NULL')
FROM fw.comp_def WHERE name = 'grid_system_new_security_devices'

UNION ALL

SELECT
    '6. data_source' AS what,
    id::text, code, name, refresh_type, 'v' || version::text
FROM fw.data_source WHERE code = 'system_new.security_devices'

UNION ALL

SELECT
    '7. data_set' AS what,
    id::text, code, LEFT(sql_text, 60) || '...', 'db_conn=' || db_connection_id::text, 'v' || version::text
FROM fw.data_set WHERE code = 'system_new.security_devices'

UNION ALL

SELECT
    '8. data_source_op' AS what,
    dso.id::text, ds.code, dso.operation_kind || '/' || dso.variant_code,
    'ds=' || dso.data_source_id::text, 'dset=' || dso.data_set_id::text
FROM fw.data_source_op dso
JOIN fw.data_source ds ON ds.id = dso.data_source_id
WHERE ds.code = 'system_new.security_devices'

ORDER BY 1;

COMMIT;

-- ============================================================
-- SMOKE TEST (po commitu):
-- ============================================================
-- 1. Hard reload UI (Ctrl+Shift+R v browseru)
-- 2. Levý strom: vedle SYSTEM se objeví SYSTEM NEW
-- 3. Expand SYSTEM NEW → Security → Trusted devices
-- 4. Klik na „Trusted devices" → grid se vykreslí
-- 5. Porovnat side-by-side s původním SYSTEM → Security → Trusted devices
-- 6. Identický počet řádků + sloupců + data → PASS
-- 7. Pošli Marti: „system_new.security_devices LIVE, pokračuji users"
--
-- Pokud STEP 7+9+10 byly skipnuté (NOTICE INCOMPLETE):
--   1. Najít SQL v Python kódu:
--      Grep router.py: „/system/security" + „mode=devices" handler
--      Najít SELECT statement (např. SELECT id, fingerprint, label,
--      created_at, last_seen_at, expires_at FROM auth_devices WHERE ...)
--   2. INSERT INTO fw.data_set (code, version, sql_text, status,
--      db_connection_id, ...) VALUES (
--         'system_new.security_devices', 1,
--         'SELECT ... FROM auth_devices ...',
--         'active', 1, ...);
--   3. INSERT INTO fw.data_source (code, name, version, refresh_type,
--      status, ...) VALUES ('system_new.security_devices', ...);
--   4. UPDATE fw.comp_def SET data_source_id = ... WHERE name='grid_system_new_security_devices';
--   5. INSERT INTO fw.data_source_op (...) VALUES (...);
--   6. Smoke test krok 1-7 výše.
-- ============================================================
