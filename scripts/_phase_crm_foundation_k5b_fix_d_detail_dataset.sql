-- ============================================================================
-- CRM Foundation Krok 5-B Fix D — Detail dataset pro CRM Kontakt edit form
-- ============================================================================
-- 28.5.2026 vecer pozde, Marti's catch po Fix C deploy:
--   "Ted ctes data jen z datasetu prehled do jadra. To je v mnoha pripadech
--    OK. V tomto pripade ale musime mit datasety dva... Jeden pro prehled
--    a jeden pro detail."
--
-- Reuse Krok H+2/H+3 pattern (operation_kind='select-detail' existing LIVE):
--   data_source #X pro core 63 ma DVA select-ish ops:
--     - kind='select'        -> Centrala 1 grid SELECT s JOINs (FirmaText,
--                               Firma, Kategorie, PoslAkceNazev, TelKontakt,
--                               MaZajemORozvadece, ZemeID -> ZemeCis lookup)
--     - kind='select-detail' -> Marti's NEW SQL pro edit form (vetsi field set
--                               vc. Razeni, OdpOsoba*, Nav, Komunikace, atd.)
--                               s embedded WHERE K.ID = :ID single-row filter
--
-- Backend (Krok 5-B Fix D apply script) refactor _resolve_entity_config_from_db
-- s prefer_kind parameter — fw_form_load_by_id (edit form) preferuje
-- 'select-detail', fallback na 'select' pokud detail neexistuje.
--
-- Plus Marti's SQL pouziva legacy schema (dbo.EC_Kontakt + dbo.EC_KontaktAkce +
-- :ID bind placeholder). Backend bude substituovat :ID za int(row_id) pred
-- dispatch (pyodbc nepodporuje :named, jen ?).
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ====================================================================
-- Step 1: PRE-STATE — najit data_source_id pro core 63
-- ====================================================================
SELECT '=== Step 1: PRE-STATE — chain pro core 63 ===' AS section;

SELECT
    c.id AS core_id,
    c.code AS core_code,
    c.label AS core_label,
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.data_source_id,
    dsrc.code AS data_source_code,
    dsrc.name AS data_source_name,
    op.id AS op_id,
    op.operation_kind,
    op.data_set_id,
    ds.code AS data_set_code,
    LEFT(ds.sql_text, 80) AS sql_text_preview
FROM fw.core c
JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = dsrc.id
LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE c.id = 63
ORDER BY op.id;
-- Expected: 1 row s op.operation_kind='select', data_set_id=X, sql_text='SELECT K.[ID] ... FROM st.CRM_Kontakt'


-- ====================================================================
-- Step 2: INSERT fw.data_set — Marti's CRM Kontakt detail SQL (40011)
-- ====================================================================
SELECT '=== Step 2: INSERT fw.data_set framework_crm_kontakt_detail ===' AS section;

INSERT INTO fw.data_set (
    code,
    version,
    name,
    description,
    db_connection_id,
    sql_text,
    status,
    is_system,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'framework_crm_kontakt_detail',
    1,
    'CRM Kontakt — detail (edit form, Centrala 1 #40011)',
    'Detail SELECT pro edit form CRM Kontakt jadra. Bere Centrala 1 dbo.EC_Kontakt + outer apply PoslAkce + LEFT JOIN AkceZiskaniFirmy IDAkce=16 + Nav + Komunikace. Embedded WHERE K.ID = :ID single-row filter (backend substituuje za int row_id pred dispatch). Marti''s Krok 5-B Fix D 28.5.2026 vecer.',
    (SELECT id FROM fw.db_connection WHERE code = 'eurosoft_db_ec'),  -- DB_EC
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
WHERE K.ID = :ID$sql$,
    'active',
    TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail');

SELECT '   -> data_set id=' || (SELECT id FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail')::TEXT AS new_data_set;


-- ====================================================================
-- Step 3: INSERT fw.data_source_op — select-detail op pro core 63 chain
-- ====================================================================
SELECT '=== Step 3: INSERT fw.data_source_op kind=select-detail ===' AS section;

INSERT INTO fw.data_source_op (
    data_source_id,
    operation_kind,
    variant_code,
    data_set_id,
    is_default,
    description,
    status,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    cd.data_source_id,  -- z core 63 chain (Step 1)
    'select-detail',
    NULL,  -- variant_code (Marti's "drop variant_code z UI" doctrine z 19.5.)
    (SELECT id FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail'),
    FALSE,  -- not default (default je 'select' kind pro list view)
    'Edit form SELECT pro CRM Kontakt jadro (#63). Bere Centrala 1 dbo.EC_Kontakt + outer apply PoslAkce + LEFT JOIN AkceZiskaniFirmy IDAkce=16. Backend volat s prefer_kind=''select-detail''.',
    'active',
    2, 'Marti-AI', 2, 'Marti-AI'
FROM fw.core c
JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
WHERE c.id = 63
  AND cd.data_source_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM fw.data_source_op op
    WHERE op.data_source_id = cd.data_source_id
      AND op.operation_kind = 'select-detail'
      AND op.data_set_id = (SELECT id FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail')
  );


-- ====================================================================
-- Step 4: POST-STATE — verify select + select-detail oba existuji
-- ====================================================================
SELECT '=== Step 4: POST-STATE — chain pro core 63 (expected 2 rows: select + select-detail) ===' AS section;

SELECT
    op.id AS op_id,
    op.operation_kind,
    op.data_set_id,
    ds.code AS data_set_code,
    LENGTH(ds.sql_text) AS sql_text_len,
    CASE WHEN ds.sql_text LIKE '%:ID%' THEN 'YES' ELSE 'NO' END AS has_id_placeholder,
    op.is_default,
    op.status
FROM fw.core c
JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
JOIN fw.data_source_op op ON op.data_source_id = dsrc.id
JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE c.id = 63
ORDER BY
    CASE op.operation_kind WHEN 'select-detail' THEN 1 WHEN 'select' THEN 2 ELSE 3 END,
    op.id;


COMMIT;

-- ============================================================================
-- ROLLBACK (drop detail data_set + op, ponecha grid select):
-- ============================================================================
-- BEGIN;
-- DELETE FROM fw.data_source_op
--   WHERE operation_kind = 'select-detail'
--     AND data_set_id = (SELECT id FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail');
-- DELETE FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail';
-- COMMIT;
-- ============================================================================
