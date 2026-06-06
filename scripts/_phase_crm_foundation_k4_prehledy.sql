-- ============================================================
-- CRM Foundation Krok 4 (27.5.2026) — 7 CRM přehledů
-- ============================================================
-- Účel: Wire-up 7 gridů přes Universal CRUD framework foundation.
-- Per přehled (6 SQL bloků):
--   1. fw.data_set       — SQL `SELECT TOP (:limit) * FROM st.<table>`
--   2. fw.data_source    — header
--   3. fw.data_source_op — wire data_set ↔ data_source (kind='select')
--   4. fw.core           — kontejner (Marti's *„CORE = kontejner"* 17.5.)
--   5. fw.comp_def       — grid root (type_id=306 grid_modern, region='main')
--   6. UPDATE menu_node SET core_id
--
-- 7 přehledů × 6 SQL bloků = 42 SQL operations. Idempotent (NOT EXISTS guards).
--
-- Marti's *„additivně"* + *„drz jednoduchost"* (22.5.):
--   MVP = SELECT TOP (:limit) * bez JOIN. Marti uvidí raw column names
--   (Nazev1, KategorieID, atd.). Labels JOIN s číselníky přijde v Kroku
--   4.1 (post-smoke iterace per přehled).
--
-- db_connection_id=2 (eurosoft_db_ec, db_type='mssql', default_db='DB_EC').
-- Runner dispatch z Krok 1: db_type='mssql' → Phase 28-C MCP klient →
-- eurosoft_strategie_query_raw → MSSQL.
--
-- Reference: scripts/_phase_crm_foundation_k1_smoke_zemecis.sql (smoke
-- LIVE 27.5. ráno) + _phase_system_new_db_connections_grid_v3.sql (pattern).
-- ============================================================

BEGIN;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 1: Kontakty (st.CRM_Kontakt, ~9106 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakty',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt ORDER BY ID DESC$sql$,
       2,
       'CRM Kontakty — master grid (st.CRM_Kontakt)',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakty');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakty', 'CRM Kontakty',
       'CRM master přehled — DB_EC.st.CRM_Kontakt (9106 rows). MVP bez JOIN labels.',
       'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakty');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakty'),
       'select', 'default', TRUE,
       'CRM Kontakty default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakty', 'Kontakty',
       'CRM Kontakty grid — master přehled st.CRM_Kontakt',
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakty');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakty', 'Kontakty',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakty'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty'),
       100, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakty');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakty')
WHERE label = 'Kontakty'
  AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 2: Akce (st.CRM_Kontakt_Akce, ~10103 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_akce',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_Akce ORDER BY ID DESC$sql$,
       2,
       'CRM Akce — historie akcí napříč všema kontakty (st.CRM_Kontakt_Akce)',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_akce');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_akce', 'CRM Akce',
       'CRM Akce přehled — cross-kontakt historie (10103 rows). MVP bez JOIN labels.',
       'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_akce');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_akce'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_akce'),
       'select', 'default', TRUE,
       'CRM Akce default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_akce')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_akce', 'Akce',
       'CRM Akce grid — cross-kontakt historie',
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_akce');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_akce', 'Akce',
       (SELECT id FROM fw.core WHERE code = 'crm_akce'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_akce'),
       100, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_akce');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_akce')
WHERE label = 'Akce'
  AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 3: Kategorie kontaktu (st.CRM_Kontakt_KategorieCis, ~19 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_kategoriecis',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_KategorieCis ORDER BY ID$sql$,
       2,
       'CRM Kategorie kontaktu číselník (19 rows)',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_kategoriecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_kategoriecis', 'CRM Kategorie kontaktu',
       'CRM Kategorie kontaktu — číselník pro KontaktKategorie FK', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_kategoriecis');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_kategoriecis'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_kategoriecis'),
       'select', 'default', TRUE, 'CRM Kategorie default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_kategoriecis')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakt_kategoriecis', 'Kategorie kontaktu',
       'CRM Kategorie kontaktu číselník', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_kategoriecis');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakt_kategoriecis', 'Kategorie kontaktu',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakt_kategoriecis'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_kategoriecis'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_kategoriecis');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakt_kategoriecis')
WHERE label = 'Kategorie kontaktu'
  AND parent_id = (SELECT id FROM fw.menu_node mn
                   WHERE mn.label = 'Číselníky'
                     AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 4: Typy zakázek (st.CRM_Kontakt_TypZakazekCis, ~7 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_typzakazekcis',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_TypZakazekCis ORDER BY ID$sql$,
       2, 'CRM Typy zakázek číselník (7 rows)', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_typzakazekcis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_typzakazekcis', 'CRM Typy zakázek',
       'CRM Typy zakázek — číselník pro TypZakazky FK', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_typzakazekcis');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_typzakazekcis'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_typzakazekcis'),
       'select', 'default', TRUE, 'CRM Typy zakázek default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_typzakazekcis')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakt_typzakazekcis', 'Typy zakázek',
       'CRM Typy zakázek číselník', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_typzakazekcis');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakt_typzakazekcis', 'Typy zakázek',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakt_typzakazekcis'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_typzakazekcis'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_typzakazekcis');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakt_typzakazekcis')
WHERE label = 'Typy zakázek'
  AND parent_id = (SELECT id FROM fw.menu_node mn
                   WHERE mn.label = 'Číselníky'
                     AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 5: Země (st.CRM_Kontakt_ZemeCis, ~11 rows) — DROP smoke + replace s plnou strukturou
-- ════════════════════════════════════════════════════════════════
-- Pozn: smoke z Krok 1+2 (crm_zemecis_smoke) DELETE pro čistý stav.
-- Plus 'crm_kontakt_zemecis' jako oficiální code.

-- Cleanup smoke residue
DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_zemecis_smoke');
DELETE FROM fw.data_set       WHERE code = 'crm_zemecis_smoke';
DELETE FROM fw.data_source    WHERE code = 'crm_zemecis_smoke';

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_zemecis',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_ZemeCis ORDER BY ID$sql$,
       2, 'CRM Země číselník (11 rows)', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_zemecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_zemecis', 'CRM Země',
       'CRM Země — číselník pro Zeme FK', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_zemecis');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_zemecis'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_zemecis'),
       'select', 'default', TRUE, 'CRM Země default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_zemecis')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakt_zemecis', 'Země',
       'CRM Země číselník', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_zemecis');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakt_zemecis', 'Země',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakt_zemecis'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_zemecis'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_zemecis');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakt_zemecis')
WHERE label = 'Země'
  AND parent_id = (SELECT id FROM fw.menu_node mn
                   WHERE mn.label = 'Číselníky'
                     AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 6: Akce — katalog (st.CRM_Kontakt_AkceCis, ~14 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_akcecis',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_AkceCis ORDER BY ID$sql$,
       2, 'CRM Akce — katalog (14 rows, typy akcí)', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_akcecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_akcecis', 'CRM Akce — katalog',
       'CRM Akce katalog — číselník typů akcí (FK pro CRM_Kontakt_Akce.TypAkce)', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_akcecis');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akcecis'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_akcecis'),
       'select', 'default', TRUE, 'CRM Akce katalog default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akcecis')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakt_akcecis', 'Akce — katalog',
       'CRM Akce katalog — číselník typů', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_akcecis');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakt_akcecis', 'Akce — katalog',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakt_akcecis'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akcecis'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_akcecis');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakt_akcecis')
WHERE label = 'Akce — katalog'
  AND parent_id = (SELECT id FROM fw.menu_node mn
                   WHERE mn.label = 'Číselníky'
                     AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 7: Mail šablony (st.CRM_Kontakt_MailSablonyCis, ~6 rows)
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_mailsablonycis',
       $sql$SELECT TOP (:limit) * FROM st.CRM_Kontakt_MailSablonyCis ORDER BY ID$sql$,
       2, 'CRM Mail šablony (6 rows)', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_mailsablonycis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_mailsablonycis', 'CRM Mail šablony',
       'CRM Mail šablony — text templates pro auto-send emails', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_mailsablonycis');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_mailsablonycis'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_mailsablonycis'),
       'select', 'default', TRUE, 'CRM Mail šablony default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_mailsablonycis')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakt_mailsablonycis', 'Mail šablony',
       'CRM Mail šablony', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_mailsablonycis');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakt_mailsablonycis', 'Mail šablony',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakt_mailsablonycis'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_mailsablonycis'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_mailsablonycis');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakt_mailsablonycis')
WHERE label = 'Mail šablony'
  AND parent_id = (SELECT id FROM fw.menu_node mn
                   WHERE mn.label = 'Číselníky'
                     AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
  AND core_id IS NULL;


-- ════════════════════════════════════════════════════════════════
-- POST-CHECK + VERIFY
-- ════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_ds INT;
    v_dset INT;
    v_dso INT;
    v_core INT;
    v_compdef INT;
    v_menu_wired INT;
BEGIN
    SELECT COUNT(*) INTO v_ds       FROM fw.data_source    WHERE code LIKE 'crm_%';
    SELECT COUNT(*) INTO v_dset     FROM fw.data_set       WHERE code LIKE 'crm_%';
    SELECT COUNT(*) INTO v_dso      FROM fw.data_source_op WHERE data_source_id IN (SELECT id FROM fw.data_source WHERE code LIKE 'crm_%');
    SELECT COUNT(*) INTO v_core     FROM fw.core           WHERE code LIKE 'crm_%';
    SELECT COUNT(*) INTO v_compdef  FROM fw.comp_def       WHERE name LIKE 'grid_crm_%';

    -- menu_node leafs s core_id NOT NULL pod CRM hierarchy
    SELECT COUNT(*) INTO v_menu_wired
    FROM fw.menu_node mn
    WHERE mn.core_id IS NOT NULL
      AND (
          mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
          OR mn.parent_id = (SELECT id FROM fw.menu_node mn2
                             WHERE mn2.label = 'Číselníky'
                               AND mn2.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
      );

    RAISE NOTICE '--- POST-CHECK ---';
    RAISE NOTICE 'fw.data_source       CRM rows:  % / 7', v_ds;
    RAISE NOTICE 'fw.data_set          CRM rows:  % / 7', v_dset;
    RAISE NOTICE 'fw.data_source_op    CRM rows:  % / 7', v_dso;
    RAISE NOTICE 'fw.core              CRM rows:  % / 7', v_core;
    RAISE NOTICE 'fw.comp_def          grid rows: % / 7', v_compdef;
    RAISE NOTICE 'fw.menu_node wired   leafs:     % / 7', v_menu_wired;

    IF v_ds = 7 AND v_dset = 7 AND v_dso = 7 AND v_core = 7 AND v_compdef = 7 AND v_menu_wired = 7 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: 7 CRM přehledů LIVE + 7 menu_nodes wired.';
        RAISE NOTICE 'Smoke: hard reload UI → CRM → klik na Kontakty / Akce / Číselníky/*';
        RAISE NOTICE 'Plus URL test: /api/v1/erp/data/crm_kontakt_zemecis?limit=5';
        RAISE NOTICE 'Expected execution_path=mcp_mssql + rows non-empty';
        RAISE NOTICE '------';
    ELSE
        RAISE NOTICE 'INCOMPLETE: nějaký počet < 7. Check above.';
    END IF;
END $$;


-- Final verify — kompletní hierarchie s core_id mapping
SELECT
    REPEAT('  ', depth) || label AS tree_view,
    mn.id AS menu_id,
    mn.core_id,
    c.code AS core_code,
    ds.code AS data_source_code
FROM (
    SELECT 0 AS depth, id, parent_id, label, sort_order FROM fw.menu_node
    WHERE label = 'CRM' AND parent_id IS NULL
    UNION ALL
    SELECT 1, id, parent_id, label, sort_order FROM fw.menu_node
    WHERE parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
    UNION ALL
    SELECT 2, id, parent_id, label, sort_order FROM fw.menu_node
    WHERE parent_id IN (
        SELECT id FROM fw.menu_node WHERE label = 'Číselníky'
          AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
    )
) t
JOIN fw.menu_node mn ON mn.id = t.id
LEFT JOIN fw.core c ON c.id = mn.core_id
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
ORDER BY depth, t.sort_order;

COMMIT;


-- ============================================================
-- SMOKE TEST (po commit, NE-potřeba STRATEGIE-API restart):
-- ============================================================
-- 1. Hard reload UI (Ctrl+Shift+R)
-- 2. Tree: expand CRM → klik na jakýkoli leaf (Kontakty / Akce / Země / atd.)
-- 3. Grid se vykreslí (autoColumns z prvního rowu)
-- 4. Pro Kontakty: 9106 řádků k dispozici (limit 1000 default v runner)
-- 5. Pro Akce: 10103 řádků
-- 6. Pro 5× číselník: 6-19 řádků každý
-- 7. URL test (optional): /api/v1/erp/data/crm_kontakt_zemecis?limit=3
--    Expected JSON: rows=[3], execution_path='mcp_mssql', db_name='DB_EC'
-- 8. Pošli Marti: „7 CRM přehledů LIVE"
--
-- POZN: Marti uvidí raw column names (Nazev1, KategorieID, atd.) — bez
-- JOIN labels. To je MVP. Pokud Marti chce labels (Kontakt s
-- KategorieLabel namísto KategorieID), Krok 4.1 = UPDATE per data_set.sql_text
-- s LEFT JOIN na příslušné číselníky.
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne):
-- ============================================================
-- BEGIN;
-- UPDATE fw.menu_node SET core_id = NULL
-- WHERE core_id IN (SELECT id FROM fw.core WHERE code LIKE 'crm_%');
--
-- DELETE FROM fw.comp_def       WHERE name LIKE 'grid_crm_%';
-- DELETE FROM fw.data_source_op WHERE data_source_id IN (SELECT id FROM fw.data_source WHERE code LIKE 'crm_%');
-- DELETE FROM fw.data_set       WHERE code LIKE 'crm_%';
-- DELETE FROM fw.data_source    WHERE code LIKE 'crm_%';
-- DELETE FROM fw.core           WHERE code LIKE 'crm_%';
-- COMMIT;
-- ============================================================
