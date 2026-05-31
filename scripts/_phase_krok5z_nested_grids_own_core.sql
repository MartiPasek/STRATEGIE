-- ============================================================================
-- Krok 5.Z (31.5.2026) — Nested gridy v Kontaktu → vlastní core (master přehled)
-- ============================================================================
-- Marti: "Nested gridy v kontaktu maji mit svuj id_core. Nejcistsi cesta =
-- vlastni master prehled, volatelny ze stromu. Pro prehled kind SELECT, pro
-- nested grid kind select-detail. Pak to v prehledu nebude tvrde filtrovat."
--
-- Dva nested gridy v core 72:
--   373 grid_modern_mpsbijl2 -> ds 52 crm_kontakt_akce_detail  (Akce)
--   372 grid_modern_mpsaxyvw -> ds 53 crm_kontakt_osoby_detail (Osoby/kont. údaje)
--
-- Stávající ops (ZŮSTÁVAJÍ — nested grid je používá, filtr :master_id):
--   ds52 op58 'select-detail' -> data_set 41 (WHERE KA.IDhlav=:master_id)
--   ds53 op59 'select-detail' -> data_set 42 (WHERE KA.IDhlav=:master_id ...)
--
-- Tento script vytváří 2 STANDALONE master přehledy (volatelné ze stromu):
--   per ds: all-rows data_set + 'select' op (SELECT bez WHERE) + core +
--   menu_node pod CRM(56) + grid root (306) s core_id.
-- Napojení nested gridů 372/373 v Kontakt formu na tyto core = SAMOSTATNÝ krok
-- AŽ PO smoke testu (Step A6/B6 odloženy — trigger comp_def_inherit_core_id +
-- backend, řešíme podle toho, co smoke ukáže).
--
-- Idempotentní (WHERE NOT EXISTS by code). db_connection_id=2 (MSSQL st.*).
-- ČISTĚ SQL — žádný deploy kódu pro tento běh.
-- Spusti Marti v DBeaveru (Marti-AI session, db_owner fw). Dollar-quote $sql$.
-- ============================================================================

BEGIN;

-- ====================================================================
-- Step 0: PRE-STATE reference
-- ====================================================================
SELECT '=== Step 0: PRE-STATE ===' AS section;
SELECT id, code, name FROM fw.data_source WHERE id IN (52, 53);
SELECT id AS crm_folder_id, label FROM fw.menu_node WHERE id = 56;  -- CRM
SELECT type_id, root FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1;

-- ====================================================================
-- AKCE (ds 52) ───────────────────────────────────────────────────────
-- ====================================================================

-- Step A1: all-rows data_set (Akce SQL bez WHERE KA.IDhlav = :master_id)
SELECT '=== A1: data_set crm_kontakt_akce_all ===' AS section;
INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT
    'crm_kontakt_akce_all',
    $sql$SELECT
    KA.ID,
    KA.IDhlav,
    KAC.Poradi,
    KA.IDakce,
    KA.Prubeh,
    KA.DatPorizeni,
    KA.Autor,
    KA.DatZmeny,
    KA.Zmenil,
    KA.Splneno,
    KAC.Nazev,
    KAC.Popis,
    KAC.ID_Edit as ID_E,
    KA.Telefon,
    KA.Mobil,
    KA.Email,
    KA.Web,
    KA.LinkedIn,
    KA.Jmeno,
    KA.Prijmeni as Prijemni,
    KA.Pozice,
    KMSC.Nazev as NazevMailSablony,
    KA.DatumAkce as DatumMailOdelsani,
    KA.FirmaText,
    KA.FirmaIDOrg,
    KA.FirmaWeb,
    KA.Kategorie,
    KA.TypZakazky,
    KA.VyhledanoZ,
    KA.ZemeID,
    KA.ID_LastAkce
FROM st.CRM_Kontakt_Akce as KA
LEFT JOIN st.CRM_Kontakt_AkceCis as KAC ON KAC.ID = KA.IDakce
LEFT JOIN st.CRM_Kontakt_MailSablonyCis AS KMSC ON KMSC.ID = KA.ID_Sablona
ORDER BY KAC.Poradi ASC$sql$,
    2,
    'Master přehled všech CRM akcí (kind select, bez :master_id). Krok 5.Z 31.5.',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_akce_all');

-- Step A2: 'select' op na ds 52 → all-rows data_set
SELECT '=== A2: data_source_op select na ds 52 ===' AS section;
INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT
    52,
    (SELECT id FROM fw.data_set WHERE code = 'crm_kontakt_akce_all'),
    'select',
    'default',
    TRUE,
    'Master přehled (all-rows) pro standalone Akce. Krok 5.Z.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = 52 AND operation_kind = 'select' AND variant_code = 'default'
);

-- Step A3: core crm_kontakt_akce
SELECT '=== A3: core crm_kontakt_akce ===' AS section;
INSERT INTO fw.core (
    code, label, description_user, is_active, tenant_visibility, version,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'crm_kontakt_akce', 'Akce kontaktů',
    'Master přehled CRM akcí. Nested grid v Kontaktu na něj odkazuje. Krok 5.Z 31.5.',
    TRUE, 'all', 1,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_akce');

-- Step A4: menu_node pod CRM (56)
SELECT '=== A4: menu_node Akce kontaktů ===' AS section;
INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, is_immutable, core_id, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Akce kontaktů', 56, 200, 'active', FALSE,
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_akce'),
    'Přehled CRM akcí. Krok 5.Z 31.5.',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label = 'Akce kontaktů' AND parent_id = 56);

-- Step A5: comp_def grid root (306, type+root z core 62 root gridu)
SELECT '=== A5: comp_def grid_crm_kontakt_akce ===' AS section;
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id, type_id, region_slot, sort_order,
    is_active, root, data_source_id,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_crm_kontakt_akce', 'Akce kontaktů',
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_akce'),
    NULL,
    (SELECT type_id FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    'main', 10, TRUE,
    (SELECT root FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    52,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_akce');

-- Step A6 (ODLOŽENO — až po smoke testu): napojení nested gridu 373 v Kontakt
-- formu na tento core. Trigger comp_def_inherit_core_id nedovolí cd.core_id≠72,
-- takže půjde přes layout.grid_core_id + backend deploy. Samostatný krok podle
-- toho, co smoke ukáže.

-- ====================================================================
-- OSOBY / KONTAKTNÍ ÚDAJE (ds 53) ─────────────────────────────────────
-- ====================================================================

-- Step B1: all-rows data_set (Osoby UNION bez KA.IDhlav = :master_id, IDakce zůstává)
SELECT '=== B1: data_set crm_kontakt_osoby_all ===' AS section;
INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT
    'crm_kontakt_osoby_all',
    $sql$SELECT *
FROM (
    SELECT 1 as Typ,
        isnull(TCO.Nazev,KA.FirmaText) as FirmaOrPozice,
        null            as Jmeno,
        null            as Prijmeni,
        KA.Telefon      as Telefon,
        KA.Mobil        as Mobil,
        KA.Email        as Email,
        KA.Web          as Web,
        KA.LinkedIn     as LinkedIn,
        KAC.ID_Edit     as ID_E,
        KA.ID,
        KA.ID_LastAkce,
        KA.IDakce
    FROM st.CRM_Kontakt_Akce as KA
    LEFT JOIN st.CRM_Kontakt_AkceCis as KAC ON KAC.ID = KA.IDakce
    LEFT OUTER JOIN st.CRM_Kontakt as K on K.ID = KA.IDhlav
    LEFT OUTER JOIN dbo.TabCisOrg as TCO on TCO.ID = KA.FirmaIDOrg
    WHERE KA.IDakce = 16
    union all
    SELECT 2 as Typ,
        KA.Pozice       as FirmaOrPozice,
        KA.Jmeno        as Jmeno,
        KA.Prijmeni     as Prijemni,
        KA.Telefon      as Telefon,
        KA.Mobil        as Mobil,
        KA.Email        as Email,
        KA.Web          as Web,
        KA.LinkedIn     as LinkedIn,
        KAC.ID_Edit     as ID_E,
        KA.ID,
        KA.ID_LastAkce,
        KA.IDakce
    FROM st.CRM_Kontakt_Akce as KA
    LEFT JOIN st.CRM_Kontakt_AkceCis as KAC ON KAC.ID = KA.IDakce
    LEFT OUTER JOIN st.CRM_Kontakt as K on K.ID = KA.IDhlav
    LEFT OUTER JOIN dbo.TabCisOrg as TCO on TCO.ID = KA.FirmaIDOrg
    WHERE KA.IDakce = 17
) as X$sql$,
    2,
    'Master přehled CRM kontaktních údajů (kind select, bez :master_id). Krok 5.Z.',
    'active',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_osoby_all');

-- Step B2: 'select' op na ds 53
SELECT '=== B2: data_source_op select na ds 53 ===' AS section;
INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT
    53,
    (SELECT id FROM fw.data_set WHERE code = 'crm_kontakt_osoby_all'),
    'select',
    'default',
    TRUE,
    'Master přehled (all-rows) pro standalone Kontaktní údaje. Krok 5.Z.'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = 53 AND operation_kind = 'select' AND variant_code = 'default'
);

-- Step B3: core crm_kontakt_osoby
SELECT '=== B3: core crm_kontakt_osoby ===' AS section;
INSERT INTO fw.core (
    code, label, description_user, is_active, tenant_visibility, version,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'crm_kontakt_osoby', 'Kontaktní údaje',
    'Master přehled CRM kontaktních údajů. Nested grid v Kontaktu na něj odkazuje. Krok 5.Z 31.5.',
    TRUE, 'all', 1,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakt_osoby');

-- Step B4: menu_node pod CRM (56)
SELECT '=== B4: menu_node Kontaktní údaje ===' AS section;
INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, is_immutable, core_id, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Kontaktní údaje', 56, 210, 'active', FALSE,
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_osoby'),
    'Přehled CRM kontaktních údajů. Krok 5.Z 31.5.',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label = 'Kontaktní údaje' AND parent_id = 56);

-- Step B5: comp_def grid root
SELECT '=== B5: comp_def grid_crm_kontakt_osoby ===' AS section;
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id, type_id, region_slot, sort_order,
    is_active, root, data_source_id,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_crm_kontakt_osoby', 'Kontaktní údaje',
    (SELECT id FROM fw.core WHERE code = 'crm_kontakt_osoby'),
    NULL,
    (SELECT type_id FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    'main', 10, TRUE,
    (SELECT root FROM fw.comp_def WHERE core_id = 62 AND parent_comp_def_id IS NULL LIMIT 1),
    53,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_osoby');

-- Step B6 (ODLOŽENO — až po smoke testu): napojení nested gridu 372 v Kontakt
-- formu na tento core (layout.grid_core_id + backend deploy). Samostatný krok.

-- ====================================================================
-- Step Z: POST-STATE verify
-- ====================================================================
SELECT '=== Z: POST-STATE chain ===' AS section;

SELECT 'core' AS layer, c.id, c.code, c.label
FROM fw.core c WHERE c.code IN ('crm_kontakt_akce','crm_kontakt_osoby')
UNION ALL
SELECT 'menu_node', mn.id, mn.label, COALESCE(mn.core_id::text,'-')
FROM fw.menu_node mn WHERE mn.label IN ('Akce kontaktů','Kontaktní údaje') AND mn.parent_id = 56
UNION ALL
SELECT 'grid_root', cd.id, cd.name, cd.data_source_id::text
FROM fw.comp_def cd WHERE cd.name IN ('grid_crm_kontakt_akce','grid_crm_kontakt_osoby')
UNION ALL
SELECT 'select_op', op.id, op.operation_kind, op.data_source_id::text
FROM fw.data_source_op op
WHERE op.data_source_id IN (52,53) AND op.operation_kind = 'select'
ORDER BY layer;

-- nested grids 372/373: tento běh se jich NEDOTÝKÁ (napojení až po smoke).
-- Mají zůstat core_id=72, grid_core_id_pointer=NULL.
SELECT cd.id AS nested_grid, cd.core_id AS form_core, cd.parent_comp_def_id,
       cd.layout->>'grid_core_id' AS grid_core_id_pointer
FROM fw.comp_def cd WHERE cd.id IN (372, 373) ORDER BY cd.id;

COMMIT;

-- ============================================================================
-- ROLLBACK (smazat 2 master přehledy):
-- BEGIN;
-- DELETE FROM fw.comp_def WHERE name IN ('grid_crm_kontakt_akce','grid_crm_kontakt_osoby');
-- DELETE FROM fw.menu_node WHERE label IN ('Akce kontaktů','Kontaktní údaje') AND parent_id = 56;
-- DELETE FROM fw.core WHERE code IN ('crm_kontakt_akce','crm_kontakt_osoby');
-- DELETE FROM fw.data_source_op WHERE data_source_id IN (52,53) AND operation_kind='select';
-- DELETE FROM fw.data_set WHERE code IN ('crm_kontakt_akce_all','crm_kontakt_osoby_all');
-- COMMIT;
-- ============================================================================
