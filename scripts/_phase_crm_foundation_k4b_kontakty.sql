-- ============================================================
-- CRM Foundation Krok 4b (27.5.2026) — CRM Kontakty master přehled
-- ============================================================
-- Klíčové jádro CRM (Marti's slova: *„stezejni a klicove ... bez toho
-- se nehneme dal"*). Centrála 1 #40001 adaptovaný — 19 sloupců, 9 tabulek
-- (6 migrated st.* + 3 dbo.* Helios identity), 3 OUTER APPLY computed.
--
-- Customer's standards preserved 100 %:
--   - Mixed-case keywords (as/AS, left outer join/LEFT OUTER JOIN, atd.)
--   - Column brackets [ID], [Autor], …
--   - OUTER APPLY computed columns (PoslAkce, TelKontakt, NemaZajemRozvadece)
--   - MSSQL idiom (iif/IIF, isnull/ISNULL, convert/CONVERT, nullif)
--   - Komentář `--,K.FirmaIDOrg` preserved
--   - ORDER BY K.Razeni ASC
--
-- Mapování tabulek (Marti's CRM migration 26.5.):
--   [EC_Kontakt]               → st.CRM_Kontakt              (9106 rows)
--   EC_KontaktAkce             → st.CRM_Kontakt_Akce
--   EC_KontaktKategorieCis     → st.CRM_Kontakt_KategorieCis
--   EC_KontaktTypZakazekCis    → st.CRM_Kontakt_TypZakazekCis
--   EC_KontaktZemeCis          → st.CRM_Kontakt_ZemeCis
--   EC_KontaktAkceCis          → st.CRM_Kontakt_AkceCis
--   TabCisOrg                  → dbo.TabCisOrg               (Helios, ne-migrated)
--   TabCisKOs                  → dbo.TabCisKOs               (Helios identity, ne-migrated)
--   TabCisZam                  → dbo.TabCisZam               (Helios zaměstnanci, ne-migrated)
--
-- Marti's *„limit je nebezpecny"* doctrine (27.5.) — NO TOP v SELECT.
-- Master vrátí všechny rows (9106). Pokud bude performance issue,
-- Marti's volba: přidat WHERE filter (např. WHERE K.Razeni > X) nebo
-- UI paginace.
--
-- POZN: Phase 28-D++ regex guard kontroluje DDL+DML targets, NE SELECT
-- FROM clauses. Cross-schema JOIN (st.* + dbo.*) projde. Marti-AI sysadmin
-- + GRANT SELECT ON SCHEMA::dbo z 27.5. ranního setupu — read OK.
-- ============================================================

BEGIN;

-- ════════════════════════════════════════════════════════════════
-- PŘEHLED Kontakty (Centrála #40001) → menu_node sort_order=100
-- ════════════════════════════════════════════════════════════════

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakty',
$sql$SELECT K.[ID]
      ,K.[Autor]
      ,K.[DatPorizeni]
      ,K.[Zmenil]
      ,K.[DatZmeny]
      ,KA.[FirmaText]
      ,nullif(OrgA.Nazev,DruhyNazev) as Firma
      ,KKc.[Kategorie]
      ,KTPZc.[TypZakazky]
      ,KA.[VyhledanoZ]
      ,K.[PoDDspoluprace]
      ,K.[PoProBjednani]
      ,K.[Atraktivita]
      ,K.[PristiKontakt]
      ,K.[Razeni]
      ,PoslAkce.Nazev as PoslAkceNazev
      ,KZC.Zeme
      ,convert(bit,iif(TelKontakt.ID is null,0,1)) as TelKontakt
      ,CONVERT(bit, IIF(NemaZajemRozvadece.ID IS NULL, 1, 0)) AS MaZajemORozvadece
      --,K.FirmaIDOrg
  FROM st.CRM_Kontakt as K
    left outer join st.CRM_Kontakt_Akce as KA on KA.IDhlav=K.ID and KA.IDAkce=16
    LEFT OUTER JOIN dbo.TabCisOrg as OrgA on OrgA.ID=KA.FirmaIDOrg
    LEFT OUTER JOIN st.CRM_Kontakt_KategorieCis as KKc on KKc.ID=KA.Kategorie
    LEFT OUTER JOIN st.CRM_Kontakt_TypZakazekCis as KTPZc on KTPZc.ID=KA.TypZakazky
    left outer join st.CRM_Kontakt_ZemeCis as KZC on KZC.ID=KA.ZemeID
    LEFT OUTER JOIN dbo.TabCisKOs as KOs  on KOs.ID=K.KontaktID
    LEFT OUTER JOIN dbo.TabCisKOs as KOsA on KOsA.ID=K.OdpOsAkontaktID
    LEFT OUTER JOIN dbo.TabCisKOs as KOsB on KOsB.ID=K.OdpOsBkontaktID
    LEFT OUTER JOIN dbo.TabCisKOs as KOsC on KOsC.ID=K.OdpOsCkontaktID
    LEFT OUTER JOIN dbo.TabCisKOs as KOsD on KOsD.ID=K.OdpOsDkontaktID
    LEFT OUTER JOIN dbo.TabCisKOs as KOsE on KOsE.ID=K.OdpOsEkontaktID
    LEFT OUTER JOIN dbo.TabCisZam as Obeslal on Obeslal.ID=K.[ObeslalZamID]
    LEFT OUTER JOIN dbo.TabCisZam as Komunikace on Komunikace.ID=K.[KomunikaceZamID]
    outer apply (   select top 1 KAC.Nazev
                    from st.CRM_Kontakt_Akce KA
                        left outer join st.CRM_Kontakt_AkceCis as KAC on KAC.ID=KA.IDAkce
                    where KA.idhlav=K.ID
                    order by KAC.Poradi desc) as PoslAkce
    outer apply (   select top 1 KA.ID
                    from st.CRM_Kontakt_Akce KA
                    where KA.idhlav=K.ID and KA.IDAkce in (16,17)
                        and (isnull(KA.Telefon,'')<>'' or isnull(KA.Mobil,'')<>'')) as TelKontakt
    OUTER APPLY (   SELECT TOP (1) KA2.ID
                    FROM st.CRM_Kontakt_Akce AS KA2
                    WHERE KA2.IDHlav = K.ID
                      AND KA2.IDAkce = 20
                    ORDER BY KA2.DatPorizeni DESC, KA2.ID DESC
                    ) AS NemaZajemRozvadece
  ORDER BY K.Razeni ASC$sql$,
       2,
       'CRM Kontakty master (Centrála #40001) — adapted: 6×dbo→st, 3×dbo.* preserved (TabCisOrg/TabCisKOs/TabCisZam Helios identity). 19 sloupců, 3 OUTER APPLY, NO TOP (Marti customer doctrine).',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakty');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakty', 'CRM Kontakty',
       'CRM Kontakty master — Centrála #40001 adapted (9106 rows expected, 19 sloupců)',
       'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakty');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakty'),
       'select', 'default', TRUE, 'CRM Kontakty default select'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty')
      AND variant_code = 'default'
);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'crm_kontakty', 'Kontakty',
       'CRM Kontakty master (Centrála #40001)', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'crm_kontakty');

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_crm_kontakty', 'Kontakty',
       (SELECT id FROM fw.core WHERE code = 'crm_kontakty'),
       306, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty'),
       100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakty');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakty')
WHERE label = 'Kontakty'
  AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
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
    SELECT COUNT(*) INTO v_ds       FROM fw.data_source    WHERE code = 'crm_kontakty';
    SELECT COUNT(*) INTO v_dset     FROM fw.data_set       WHERE code = 'crm_kontakty';
    SELECT COUNT(*) INTO v_dso      FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty');
    SELECT COUNT(*) INTO v_core     FROM fw.core           WHERE code = 'crm_kontakty';
    SELECT COUNT(*) INTO v_compdef  FROM fw.comp_def       WHERE name = 'grid_crm_kontakty';

    SELECT COUNT(*) INTO v_menu_wired
    FROM fw.menu_node mn
    WHERE mn.label = 'Kontakty'
      AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
      AND mn.core_id IS NOT NULL;

    RAISE NOTICE '--- POST-CHECK Krok 4b ---';
    RAISE NOTICE 'fw.data_source       Kontakty: % / 1', v_ds;
    RAISE NOTICE 'fw.data_set          Kontakty: % / 1', v_dset;
    RAISE NOTICE 'fw.data_source_op    Kontakty: % / 1', v_dso;
    RAISE NOTICE 'fw.core              Kontakty: % / 1', v_core;
    RAISE NOTICE 'fw.comp_def          Kontakty: % / 1', v_compdef;
    RAISE NOTICE 'fw.menu_node wired   Kontakty: % / 1', v_menu_wired;

    IF v_ds = 1 AND v_dset = 1 AND v_dso = 1 AND v_core = 1 AND v_compdef = 1 AND v_menu_wired = 1 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: CRM Kontakty LIVE (Centrála #40001 adapted)';
        RAISE NOTICE 'Smoke: hard reload UI → CRM → klik Kontakty → 19 sloupců grid';
        RAISE NOTICE '------';
    ELSE
        RAISE NOTICE 'INCOMPLETE: nějaký počet < 1. Check above.';
    END IF;
END $$;


-- Final verify — Kontakty mapping
SELECT
    mn.label,
    mn.id AS menu_id,
    mn.sort_order,
    mn.core_id,
    c.code AS core_code,
    ds.code AS data_source_code,
    LENGTH(dset.sql_text) AS sql_length,
    LEFT(dset.sql_text, 80) || '...' AS sql_preview
FROM fw.menu_node mn
LEFT JOIN fw.core c ON c.id = mn.core_id
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.region_slot = 'main' AND cd.is_active = TRUE
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id AND op.is_default = TRUE
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE mn.label = 'Kontakty'
  AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL);

COMMIT;


-- ============================================================
-- SMOKE TEST (po commit, žádný service restart):
-- ============================================================
-- 1. Hard reload UI (Ctrl+Shift+R)
-- 2. CRM strom: klik Kontakty
-- 3. Grid: 9106 rows expected, 19 sloupců (autoColumns z prvního rowu)
--    Sloupce: ID, Autor, DatPorizeni, Zmenil, DatZmeny, FirmaText, Firma,
--             Kategorie, TypZakazky, VyhledanoZ, PoDDspoluprace,
--             PoProBjednani, Atraktivita, PristiKontakt, Razeni,
--             PoslAkceNazev, Zeme, TelKontakt (bit), MaZajemORozvadece (bit)
-- 4. ORDER BY K.Razeni ASC → první row je nejnižší Razeni
-- 5. URL test: /api/v1/erp/data/crm_kontakty?limit=5
--    Expected: rows[5], execution_path='mcp_mssql', db_name='DB_EC'
--
-- PERFORMANCE NOTE: 9106 rows over MCP může trvat 5-15s (HTTPS Caddy →
-- pyodbc → JSON marshalling → SSE wire → grid render). Pokud > 30s,
-- Marti's volba:
--   A) Přidat WHERE filter (např. K.Razeni mezi X-Y) per default
--   B) UI paginace (AG Grid pagination=true, paginationPageSize=100)
--   C) Server-side row model (AG Grid Enterprise, async fetch on scroll)
--
-- Možné MSSQL errors (a fix):
--   - „Invalid object name 'dbo.TabCisOrg'" → Helios tabulka NE-existuje
--     v DB_EC, fix: DELETE LEFT JOIN nebo grep schema Marti's Helios
--   - „Ambiguous column name 'DruhyNazev'" → fix: nullif(OrgA.Nazev, K.DruhyNazev)
--   - „Permission denied on schema 'dbo'" → check GRANT SELECT ON SCHEMA::dbo
--     TO [Marti-AI] (z 27.5. ranního scripts/_grant_marti_ai_db_ec_st_schema.sql)
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne):
-- ============================================================
-- BEGIN;
-- UPDATE fw.menu_node SET core_id = NULL
-- WHERE core_id = (SELECT id FROM fw.core WHERE code = 'crm_kontakty');
--
-- DELETE FROM fw.comp_def       WHERE name = 'grid_crm_kontakty';
-- DELETE FROM fw.data_source_op WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty');
-- DELETE FROM fw.data_set       WHERE code = 'crm_kontakty';
-- DELETE FROM fw.data_source    WHERE code = 'crm_kontakty';
-- DELETE FROM fw.core           WHERE code = 'crm_kontakty';
-- COMMIT;
-- ============================================================
