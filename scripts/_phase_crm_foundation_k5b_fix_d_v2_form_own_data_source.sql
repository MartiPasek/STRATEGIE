-- ============================================================================
-- CRM Foundation Krok 5-B Fix D v2 — Form má vlastní data_source (Centrála 1)
-- ============================================================================
-- 28.5.2026 vecer pozde, Marti's doctrine:
--   "V Centrale je to jak to říkám — Formulář má svůj datasource a svoje OP
--    a datasety. Podle mne je Form detail normálně nezávislá entita.
--    Proto máme CORE (kontejnery) dva. Jeden pro přehled a jeden pro detail."
--   "S tím, že v jednoduchých případech si vystačíme jen s jedním datasouce
--    a datasetem, jako doposud. Když ale bude mít formulář svůj datasource,
--    tak se jeho upřednostní."
--
-- Architecture (drží automaticky pres comp_def.data_source_id):
--   CORE A "Kontakty přehled" (grid 306) -> data_source_grid (existing)
--   CORE #63 "Editace kontaktu" (form 302) -> VLASTNI data_source_detail (NEW)
--
-- Backend Fix C resolver chain je polymorphic — pokud comp_def.data_source_id
-- linkne na vlastni detail data_source, automaticky se preferuje pred grid.
--
-- SQL HOTFIX v2 (28.5. vecer): fw.data_source / fw.data_set / fw.data_source_op
-- nemaji audit columns (created_by_id atd.) ani version. Schema je:
--   fw.data_source: code, name, description, refresh_type, status, is_system
--   fw.data_set:    code, sql_text, db_connection_id, description, status, is_system
--   fw.data_source_op: data_source_id, data_set_id, operation_kind,
--                      variant_code, is_default, description
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ====================================================================
-- Step 1: PRE-STATE — current chain pro core 63 (form root)
-- ====================================================================
SELECT '=== Step 1: PRE-STATE — comp_def form_crm_kontakt_edit ===' AS section;

SELECT
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.core_id,
    cd.data_source_id AS current_data_source_id,
    dsrc.code AS current_data_source_code,
    dsrc.name AS current_data_source_name,
    LEFT(ds.sql_text, 80) AS current_sql_preview
FROM fw.comp_def cd
LEFT JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = dsrc.id AND op.operation_kind = 'select'
LEFT JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE cd.name = 'form_crm_kontakt_edit';


-- ====================================================================
-- Step 2: INSERT fw.data_source — vlastni pro CRM Kontakt detail (form)
-- ====================================================================
SELECT '=== Step 2: INSERT fw.data_source framework_crm_kontakt_detail ===' AS section;

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT
    'framework_crm_kontakt_detail',
    'CRM Kontakt — detail (edit form #40011)',
    'Form edit data_source pro core #63. Marti Fix D v2 28.5.',
    'manual',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail');

SELECT '   -> data_source id=' || (SELECT id FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail')::TEXT AS new_data_source;


-- ====================================================================
-- Step 3: INSERT fw.data_set — Marti's #40011 detail SQL
-- ====================================================================
SELECT '=== Step 3: INSERT fw.data_set framework_crm_kontakt_detail ===' AS section;

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT
    'framework_crm_kontakt_detail',
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
    (SELECT id FROM fw.db_connection WHERE code = 'eurosoft_db_ec'),
    'CRM Kontakt detail SQL (#40011) — WHERE K.ID = :ID. Backend substituuje za int row_id. Marti Fix D v2 28.5.',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail');

SELECT '   -> data_set id=' || (SELECT id FROM fw.data_set WHERE code = 'framework_crm_kontakt_detail')::TEXT AS new_data_set;


-- ====================================================================
-- Step 4: INSERT fw.data_source_op — kind='select' is_default=TRUE
-- ====================================================================
SELECT '=== Step 4: INSERT fw.data_source_op kind=select ===' AS section;

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail'),
    (SELECT id FROM fw.data_set    WHERE code = 'framework_crm_kontakt_detail'),
    'select',
    'default',
    TRUE,
    'Form edit SELECT op pro CRM Kontakt jadro (core #63). Marti Fix D v2 28.5.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail')
      AND operation_kind = 'select'
      AND variant_code = 'default'
);


-- ====================================================================
-- Step 5: UPDATE fw.comp_def — form root preference vlastni data_source
-- ====================================================================
SELECT '=== Step 5: UPDATE fw.comp_def form_crm_kontakt_edit -> own data_source ===' AS section;

UPDATE fw.comp_def
SET
    data_source_id = (SELECT id FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail'),
    updated_at = NOW(),
    updated_by_id = 2,
    updated_by_text = 'Marti-AI'
WHERE name = 'form_crm_kontakt_edit';


-- ====================================================================
-- Step 6: POST-STATE verify — form root teď má vlastní data_source chain
-- ====================================================================
SELECT '=== Step 6: POST-STATE — comp_def form_crm_kontakt_edit chain ===' AS section;

SELECT
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.data_source_id,
    dsrc.code AS data_source_code,
    op.operation_kind,
    ds.code AS data_set_code,
    LENGTH(ds.sql_text) AS sql_text_len,
    CASE WHEN ds.sql_text LIKE '%:ID%' THEN 'YES' ELSE 'NO' END AS has_id_placeholder,
    CASE WHEN ds.sql_text LIKE '%[EC_Kontakt]%' THEN 'legacy dbo' ELSE 'st.' END AS schema_used
FROM fw.comp_def cd
JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
JOIN fw.data_source_op op ON op.data_source_id = dsrc.id AND op.operation_kind = 'select'
JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE cd.name = 'form_crm_kontakt_edit';
-- Expected: 1 row s data_source_code='framework_crm_kontakt_detail',
--           has_id_placeholder='YES', schema_used='legacy dbo'


COMMIT;

-- ============================================================================
-- ROLLBACK (vrátit form root na puvodní data_source + drop nove rows):
-- ============================================================================
-- BEGIN;
-- -- Najít původní data_source_id z Step 1 PRE-STATE output (current_data_source_id)
-- UPDATE fw.comp_def SET data_source_id = <original_id>
--   WHERE name = 'form_crm_kontakt_edit';
-- DELETE FROM fw.data_source_op
--   WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail');
-- DELETE FROM fw.data_set    WHERE code = 'framework_crm_kontakt_detail';
-- DELETE FROM fw.data_source WHERE code = 'framework_crm_kontakt_detail';
-- COMMIT;
-- ============================================================================
