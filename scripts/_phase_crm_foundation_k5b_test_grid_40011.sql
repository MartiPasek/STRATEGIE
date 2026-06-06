-- ============================================================================
-- CRM Foundation Krok 5-B TEST GRID — Marti's #40011 detail SQL jako přehled
-- ============================================================================
-- 28.5.2026 vecer pozde, Marti's catch: "Stale se motame dokola... Zpatky
-- na stromy... Vytvor novy prehled (grid) s timto selectem".
--
-- Pragmatic isolation: vytvori grid s Marti's #40011 SQL (WHERE K.ID = 11341
-- hardcoded — ZADNY :ID placeholder). Pokud grid funguje:
--   - Backend MCP infrastructure OK (eurosoft_strategie_query_raw funguje)
--   - Marti's SQL syntactically OK (parsed by MSSQL)
--   - data_source_runner dispatch OK pro DB_EC
--   - Form-specific :ID substitute v fw_form_load_by_id je SEPARATE PROBLEM
--
-- Pokud grid NEFUNGUJE:
--   - Marti's SQL ma syntax error v MSSQL (outer apply, JOIN, atd.)
--   - Nebo dbo.EC_Kontakt / dbo.EC_KontaktAkce nemaji povolene granty
--   - Nebo Krok H+2 select-detail s :master_id pouziva guard ktery brani
--     SQL bez bind parametrs (unlikely — Marti's SQL ma hardcoded 11341)
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ====================================================================
-- Step 1: PRE-STATE — CRM root menu_node + comp_type grid_modern id
-- ====================================================================
SELECT '=== Step 1: PRE-STATE references ===' AS section;

SELECT
    id AS crm_root_menu_node_id,
    label,
    parent_id
FROM fw.menu_node
WHERE label = 'CRM'
  AND parent_id IS NULL
LIMIT 1;
-- Note dle id (manualne pridate do Step 5 pokud parent_id se v Step 5 nenacita)

SELECT
    id AS grid_modern_type_id,
    code
FROM fw.comp_type
WHERE code = 'grid_modern';
-- Expected: 306


-- ====================================================================
-- Step 2: INSERT fw.data_set — Marti's #40011 SQL s hardcoded WHERE 11341
-- ====================================================================
SELECT '=== Step 2: INSERT fw.data_set crm_kontakt_detail_test ===' AS section;

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT
    'crm_kontakt_detail_test',
    $sql$--//Číslo přehledu: 40011\\
SELECT K.[ID]
      ,K.[Autor]
      ,K.[DatPorizeni]
      ,K.[Zmenil]
      ,K.[DatZmeny]
      ,K.[KontaktText]
      ,K.[KontaktID]
      ,K.[OdpOsobaAtext]
      ,K.[OdpOsAkontaktID]
      ,K.[OdpOsobaBtext]
      ,K.[OdpOsBkontaktID]
      ,K.[OdpOsobaCtext]
      ,K.[OdpOsCkontaktID]
      ,K.[OdpOsobaDtext]
      ,K.[OdpOsDkontaktID]
      ,K.[OdpOsobaEtext]
      ,K.[OdpOsEkontaktID]
      ,K.[ObeslalZamID]
      ,K.[KomunikaceZamID]
      ,K.[PoDDspoluprace]
      ,K.[PoProBjednani]
      ,K.[Atraktivita]
      ,K.[PristiKontakt]
      ,K.[Razeni]
      ,K.Poznamka
      ,K.Popis
      --,K.FirmaTelefon
      --,K.FirmaEmail
      ,AkceZiskaniFirmy.FirmaWeb
      ,AkceZiskaniFirmy.ZemeID
      ,AkceZiskaniFirmy.[FirmaText]
      ,AkceZiskaniFirmy.[FirmaIDOrg]
      ,AkceZiskaniFirmy.Kategorie
      ,AkceZiskaniFirmy.[TypZakazky]
      ,AkceZiskaniFirmy.[VyhledanoZ]
      ,PoslAkce.Nazev as PoslAkceNazev
      ,PoslAkce.DatPorizeni as DatPorizeniPoslAkce
      ,Nav.IDKontakt
  FROM [EC_Kontakt] as K
    LEFT OUTER JOIN TabCisZam as Komunikace on Komunikace.ID=K.[KomunikaceZamID]
    LEFT OUTER JOIN dbo.EC_KontaktVeletrhNav as Nav on Nav.IDKontakt = K.ID
    outer apply (    select top 1 KAC.Nazev,KA.*
                    from EC_KontaktAkce as KA
                    left outer join EC_KontaktAkceCis as KAC on KAC.ID=KA.IDAkce
                    where KA.idhlav=K.ID
                    order by KAC.Poradi asc , KA.ID asc) as PoslAkce
    LEFT OUTER JOIN EC_KontaktAkce as AkceZiskaniFirmy on AkceZiskaniFirmy.IDHlav=K.ID and AkceZiskaniFirmy.IDakce=16
WHERE K.ID = 11341$sql$,
    (SELECT id FROM fw.db_connection WHERE code = 'eurosoft_db_ec'),
    'TEST grid Marti #40011 SQL hardcoded WHERE 11341. Marti 28.5.',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_detail_test');


-- ====================================================================
-- Step 3: INSERT fw.data_source
-- ====================================================================
SELECT '=== Step 3: INSERT fw.data_source crm_kontakt_detail_test ===' AS section;

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT
    'crm_kontakt_detail_test',
    'CRM Kontakt — detail TEST grid #40011',
    'TEST grid Marti pragmatic. Marti 28.5.',
    'manual',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_detail_test');


-- ====================================================================
-- Step 4: INSERT fw.data_source_op
-- ====================================================================
SELECT '=== Step 4: INSERT fw.data_source_op ===' AS section;

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_detail_test'),
    (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_detail_test'),
    'select',
    'default',
    TRUE,
    'TEST select op pro Marti #40011 grid. Marti 28.5.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_detail_test')
      AND operation_kind = 'select'
      AND variant_code = 'default'
);


-- ====================================================================
-- Step 5: INSERT fw.core (grid type)
-- ====================================================================
SELECT '=== Step 5: INSERT fw.core crm_kontakt_detail_test ===' AS section;

INSERT INTO fw.core (
    code, label, description_user, is_active, tenant_visibility, version,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'crm_kontakt_detail_test',
    'TEST detail #40011',
    'TEST grid s Marti #40011 SQL WHERE 11341 hardcoded. Marti 28.5.',
    TRUE,
    'all',
    1,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_detail_test');


-- ====================================================================
-- Step 6: INSERT fw.comp_def grid root (type=306 grid_modern)
-- ====================================================================
SELECT '=== Step 6: INSERT fw.comp_def grid root ===' AS section;

INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    data_source_id,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_crm_kontakt_detail_test',
    'TEST detail grid',
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_detail_test'),
    NULL,
    (SELECT id FROM fw.comp_type WHERE code = 'grid_modern'),
    'main', 10, TRUE,
    (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_detail_test'),
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_detail_test');


-- ====================================================================
-- Step 7: INSERT fw.menu_node pod CRM root (Marti's CRM soudecek)
-- ====================================================================
SELECT '=== Step 7: INSERT fw.menu_node CRM > TEST detail ===' AS section;

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, is_immutable, core_id, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'TEST detail #40011',
    (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL LIMIT 1),
    990,
    'active',
    FALSE,
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_detail_test'),
    'TEST grid s Marti #40011 SQL hardcoded WHERE 11341. Marti 28.5.',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'TEST detail #40011'
      AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL LIMIT 1)
);


-- ====================================================================
-- Step 8: POST-STATE verify
-- ====================================================================
SELECT '=== Step 8: POST-STATE chain ===' AS section;

SELECT
    'menu_node' AS layer,
    mn.id, mn.label, mn.core_id
FROM fw.menu_node mn
WHERE mn.label = 'TEST detail #40011'

UNION ALL

SELECT 'core', c.id, c.label, NULL
FROM fw.core c
WHERE c.code = 'crm_kontakt_detail_test'

UNION ALL

SELECT 'comp_def', cd.id, cd.name, cd.data_source_id
FROM fw.comp_def cd
WHERE cd.name = 'grid_crm_kontakt_detail_test'

UNION ALL

SELECT 'data_source', dsrc.id, dsrc.code, NULL
FROM fw.data_source dsrc
WHERE dsrc.code = 'crm_kontakt_detail_test'

UNION ALL

SELECT 'data_set', ds.id, ds.code, NULL
FROM fw.data_set ds
WHERE ds.code = 'crm_kontakt_detail_test'

UNION ALL

SELECT 'data_source_op', op.id, op.operation_kind || ' (default=' || op.is_default::TEXT || ')', op.data_set_id
FROM fw.data_source_op op
JOIN fw.data_source dsrc ON dsrc.id = op.data_source_id
WHERE dsrc.code = 'crm_kontakt_detail_test'
ORDER BY layer;


COMMIT;

-- ============================================================================
-- ROLLBACK:
-- ============================================================================
-- BEGIN;
-- DELETE FROM fw.menu_node WHERE label = 'TEST detail #40011';
-- DELETE FROM fw.comp_def WHERE name = 'grid_crm_kontakt_detail_test';
-- DELETE FROM fw.core WHERE code = 'crm_kontakt_detail_test';
-- DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_detail_test');
-- DELETE FROM fw.data_set WHERE code = 'crm_kontakt_detail_test';
-- DELETE FROM fw.data_source WHERE code = 'crm_kontakt_detail_test';
-- COMMIT;
-- ============================================================================
