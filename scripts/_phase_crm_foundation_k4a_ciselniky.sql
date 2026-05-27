-- ============================================================
-- CRM Foundation Krok 4a (27.5.2026) — 5 CRM číselníků z Centrály 1
-- ============================================================
-- Účel: Wire-up 5 grids pro číselníky s **adaptovanými SELECTy z Centrály 1**.
-- Marti's *„customer's standards"* doctrine (27.5. ranní): zachovat
-- Centrála 1 idiom (column lists, ORDER BY, WHERE filters, MSSQL iif/isnull).
--
-- 5 přehledů z Centrály 1 (Marti's posláno 27.5.):
--   Centrála #40003: Akce — katalog (s WHERE ID<>16 + HodnotaAkce)
--   Centrála #40004: Kategorie kontaktu (s iif/isnull KategorieANace alias)
--   Centrála #40005: Typy zakázek (simple)
--   Centrála #40007: Země (Zeme + Zkratka)
--   Centrála:        Mail šablony (SELECT *, ORDER BY Poradi)
--
-- Adaptace per přehled:
--   - Table: `[EC_Kontakt<X>Cis]` → `st.CRM_Kontakt_<X>Cis`
--   - Inject `TOP (:limit)` po SELECT (runtime substituce přes Krok 1 helper)
--   - Drop `[]` brackets z table name (st schema = clean)
--   - Preserve column brackets (Marti's idiom, MSSQL case-insensitive default)
--   - Preserve WHERE filters, ORDER BY, computed columns (iif/isnull)
--   - Preserve audit columns (Autor/DatPorizeni/Zmenil/DatZmeny) — customer standard
--
-- Mail šablony defer — Marti decides later (Centrála 1 přehled možná chybí).
--
-- Per přehled 6 idempotent SQL bloků:
--   1. fw.data_set       — adapted SELECT
--   2. fw.data_source    — header
--   3. fw.data_source_op — wire data_set ↔ data_source (kind='select')
--   4. fw.core           — kontejner
--   5. fw.comp_def       — grid root (type_id=306, region='main')
--   6. UPDATE menu_node SET core_id
--
-- Plus cleanup smoke residue z Krok 1+2 (crm_zemecis_smoke).
-- ============================================================

BEGIN;


-- ════════════════════════════════════════════════════════════════
-- CLEANUP: Smoke residue z Krok 1+2 (crm_zemecis_smoke)
-- ════════════════════════════════════════════════════════════════
-- Replaced by oficiální crm_kontakt_zemecis (Centrála #40007 adapted).

DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_zemecis_smoke');
DELETE FROM fw.data_set       WHERE code = 'crm_zemecis_smoke';
DELETE FROM fw.data_source    WHERE code = 'crm_zemecis_smoke';


-- ════════════════════════════════════════════════════════════════
-- PŘEHLED 1: Kategorie kontaktu (Centrála #40004) → menu_node sort_order=100
-- ════════════════════════════════════════════════════════════════
-- Centrála 1 SELECT s computed sloupcem KategorieANace (kombinuje Kategorie +
-- NaceKod). Drží customer's idiom v plné šíři.

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_kategoriecis',
       $sql$SELECT TOP (:limit)
       [ID]
      ,[Autor]
      ,[DatPorizeni]
      ,[Zmenil]
      ,[DatZmeny]
      ,[Kategorie]
      ,Poradi
      ,NaceKod
      ,iif(isnull(NaceKod,'')='',Kategorie,Kategorie+' ('+NaceKod+')') AS KategorieANace
FROM st.CRM_Kontakt_KategorieCis
ORDER BY Poradi ASC$sql$,
       2,
       'CRM Kategorie kontaktu (Centrála #40004) — adapted: dbo→st, +TOP(:limit). Computed KategorieANace alias preserved.',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_kategoriecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_kategoriecis', 'CRM Kategorie kontaktu',
       'CRM Kategorie kontaktu — Centrála #40004 adapted (19 rows)', 'manual', 'active', TRUE
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
       'CRM Kategorie kontaktu (Centrála #40004)', 2, 'Marti-AI', 2, 'Marti-AI'
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
-- PŘEHLED 2: Typy zakázek (Centrála #40005) → menu_node sort_order=200
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_typzakazekcis',
       $sql$SELECT TOP (:limit)
       [ID]
      ,[Autor]
      ,[DatPorizeni]
      ,[Zmenil]
      ,[DatZmeny]
      ,[TypZakazky]
      ,Poradi
FROM st.CRM_Kontakt_TypZakazekCis
ORDER BY Poradi ASC$sql$,
       2,
       'CRM Typy zakázek (Centrála #40005) — adapted: dbo→st, +TOP(:limit)',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_typzakazekcis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_typzakazekcis', 'CRM Typy zakázek',
       'CRM Typy zakázek — Centrála #40005 adapted (7 rows)', 'manual', 'active', TRUE
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
       'CRM Typy zakázek (Centrála #40005)', 2, 'Marti-AI', 2, 'Marti-AI'
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
-- PŘEHLED 3: Země (Centrála #40007) → menu_node sort_order=300
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_zemecis',
       $sql$SELECT TOP (:limit)
       [ID]
      ,[Autor]
      ,[DatPorizeni]
      ,[Zmenil]
      ,[DatZmeny]
      ,[Zeme]
      ,[Zkratka]
      ,[Poradi]
FROM st.CRM_Kontakt_ZemeCis
ORDER BY Poradi ASC$sql$,
       2,
       'CRM Země (Centrála #40007) — adapted: dbo→st, +TOP(:limit)',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_zemecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_zemecis', 'CRM Země',
       'CRM Země — Centrála #40007 adapted (11 rows)', 'manual', 'active', TRUE
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
       'CRM Země (Centrála #40007)', 2, 'Marti-AI', 2, 'Marti-AI'
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
-- PŘEHLED 4: Akce — katalog (Centrála #40003) → menu_node sort_order=400
-- ════════════════════════════════════════════════════════════════
-- Marti's customer filter: WHERE ID<>16 (Centrála 1 skrývá akci #16,
-- pravděpodobně system/legacy row). Drží.

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_akcecis',
       $sql$SELECT TOP (:limit)
       [ID]
      ,[Poradi]
      ,[Nazev]
      ,[Popis]
      ,[DatPorizeni]
      ,[Autor]
      ,[DatZmeny]
      ,[Zmenil]
      ,[ID_Edit]
      ,HodnotaAkce
FROM st.CRM_Kontakt_AkceCis
WHERE ID <> 16
ORDER BY Poradi ASC$sql$,
       2,
       'CRM Akce — katalog (Centrála #40003) — adapted: dbo→st, +TOP(:limit). WHERE ID<>16 customer filter preserved.',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_akcecis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_akcecis', 'CRM Akce — katalog',
       'CRM Akce katalog — Centrála #40003 adapted (14 rows, WHERE ID<>16)', 'manual', 'active', TRUE
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
       'CRM Akce katalog (Centrála #40003)', 2, 'Marti-AI', 2, 'Marti-AI'
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
-- PŘEHLED 5: Mail šablony (Centrála) → menu_node sort_order=500
-- ════════════════════════════════════════════════════════════════
-- Centrála 1 SELECT: `SELECT * FROM [EC_KontaktMailSablonyCis] ORDER BY Poradi`
-- Adaptace: dbo→st, +TOP(:limit). SELECT * preserved.

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_mailsablonycis',
       $sql$SELECT TOP (:limit) *
FROM st.CRM_Kontakt_MailSablonyCis
ORDER BY Poradi$sql$,
       2,
       'CRM Mail šablony (Centrála) — adapted: dbo→st, +TOP(:limit). SELECT * preserved.',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_mailsablonycis');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_mailsablonycis', 'CRM Mail šablony',
       'CRM Mail šablony — Centrála adapted (6 rows)', 'manual', 'active', TRUE
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
       'CRM Mail šablony (Centrála)', 2, 'Marti-AI', 2, 'Marti-AI'
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
-- POST-CHECK + VERIFY: 5 přehledů + 5 menu_nodes wired
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
    SELECT COUNT(*) INTO v_ds       FROM fw.data_source    WHERE code LIKE 'crm_kontakt_%cis';
    SELECT COUNT(*) INTO v_dset     FROM fw.data_set       WHERE code LIKE 'crm_kontakt_%cis';
    SELECT COUNT(*) INTO v_dso      FROM fw.data_source_op WHERE data_source_id IN (SELECT id FROM fw.data_source WHERE code LIKE 'crm_kontakt_%cis');
    SELECT COUNT(*) INTO v_core     FROM fw.core           WHERE code LIKE 'crm_kontakt_%cis';
    SELECT COUNT(*) INTO v_compdef  FROM fw.comp_def       WHERE name LIKE 'grid_crm_kontakt_%cis';

    SELECT COUNT(*) INTO v_menu_wired
    FROM fw.menu_node mn
    WHERE mn.core_id IS NOT NULL
      AND mn.parent_id = (SELECT id FROM fw.menu_node mn2
                          WHERE mn2.label = 'Číselníky'
                            AND mn2.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
      AND mn.label IN ('Kategorie kontaktu', 'Typy zakázek', 'Země', 'Akce — katalog', 'Mail šablony');

    RAISE NOTICE '--- POST-CHECK Krok 4a ---';
    RAISE NOTICE 'fw.data_source       číselníky:  % / 5', v_ds;
    RAISE NOTICE 'fw.data_set          číselníky:  % / 5', v_dset;
    RAISE NOTICE 'fw.data_source_op    číselníky:  % / 5', v_dso;
    RAISE NOTICE 'fw.core              číselníky:  % / 5', v_core;
    RAISE NOTICE 'fw.comp_def          grid:       % / 5', v_compdef;
    RAISE NOTICE 'fw.menu_node wired   číselníky:  % / 5', v_menu_wired;

    IF v_ds = 5 AND v_dset = 5 AND v_dso = 5 AND v_core = 5 AND v_compdef = 5 AND v_menu_wired = 5 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: 5 CRM číselníky LIVE (Centrála 1 adapted SELECTy)';
        RAISE NOTICE 'Smoke: hard reload UI → CRM → Číselníky → klik všech 5';
        RAISE NOTICE '------';
    ELSE
        RAISE NOTICE 'INCOMPLETE: nějaký počet < 5. Check above.';
    END IF;
END $$;


-- Final verify — Číselníky hierarchie s core_id mapping
SELECT
    mn.label,
    mn.id AS menu_id,
    mn.sort_order,
    mn.core_id,
    c.code AS core_code,
    ds.code AS data_source_code,
    LEFT(dset.sql_text, 80) || '...' AS sql_preview
FROM fw.menu_node mn
LEFT JOIN fw.core c ON c.id = mn.core_id
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id AND op.is_default = TRUE
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE mn.parent_id = (SELECT id FROM fw.menu_node mn2
                      WHERE mn2.label = 'Číselníky'
                        AND mn2.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
ORDER BY mn.sort_order;

COMMIT;


-- ============================================================
-- SMOKE TEST (po commit, žádný service restart):
-- ============================================================
-- 1. Hard reload UI (Ctrl+Shift+R)
-- 2. Strom: expand CRM → expand Číselníky
-- 3. Klik 5× (všech 5 číselníků)
-- 4. Každý grid by se měl vykreslit s autoColumns z prvního rowu
--    - Kategorie kontaktu: 9 sloupců (vč. KategorieANace computed)
--    - Typy zakázek: 7 sloupců
--    - Země: 8 sloupců (s Zkratka)
--    - Akce — katalog: 10 sloupců (vč. HodnotaAkce, bez ID=16)
--    - Mail šablony: dynamicky (SELECT *, autoColumns drift OK)
-- 5. Pošli Marti: „5 CRM číselníků LIVE"
--
-- URL test (optional):
--   /api/v1/erp/data/crm_kontakt_kategoriecis?limit=3
--   Expected: rows=[3] s KategorieANace alias
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne):
-- ============================================================
-- BEGIN;
-- UPDATE fw.menu_node SET core_id = NULL
-- WHERE core_id IN (SELECT id FROM fw.core WHERE code LIKE 'crm_kontakt_%cis');
--
-- DELETE FROM fw.comp_def       WHERE name LIKE 'grid_crm_kontakt_%cis';
-- DELETE FROM fw.data_source_op WHERE data_source_id IN (SELECT id FROM fw.data_source WHERE code LIKE 'crm_kontakt_%cis');
-- DELETE FROM fw.data_set       WHERE code LIKE 'crm_kontakt_%cis';
-- DELETE FROM fw.data_source    WHERE code LIKE 'crm_kontakt_%cis';
-- DELETE FROM fw.core           WHERE code LIKE 'crm_kontakt_%cis';
-- COMMIT;
-- ============================================================
