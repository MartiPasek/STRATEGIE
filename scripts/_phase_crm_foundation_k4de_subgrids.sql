-- ============================================================
-- CRM Foundation Krok 4d + 4e (27.5.2026 večer) — 2 sub-gridy v Kontakt jádře
-- ============================================================
-- Per-master sub-gridy pro Kontakt jádro (Krok 5 wire-up later).
-- Marti's *„TAK TADY SE UKAZE NASE PRIPRAVENOST"* — test foundation
-- pro nested grid composition. Phase H+1/H+2/H+3 (24.-26.5.) drží.
--
-- 2 sub-gridy:
--   Krok 4d: crm_kontakt_akce_detail  (Centrála #40006) — Akce per kontakt
--   Krok 4e: crm_kontakt_osoby_detail (Centrála #40007) — Kontaktní údaje
--
-- operation_kind='select-detail' (Phase H+3, 26.5. ranní) — runner dispatch
-- per kind, :master_id filter v WHERE. URL test:
--   /api/v1/erp/data/<code>?master_id=1479&kind=select-detail
--
-- NO menu_node / core / comp_def — sub-gridy žijí UVNITŘ Kontakt jádra
-- (Krok 5). Žádný tree leaf, žádný standalone tab. Smoke test pres URL only.
--
-- Adaptace per sub-grid:
--   - :ID → :master_id (STRATEGIE convention pro nested grid)
--   - dbo.EC_* → st.CRM_* (preserved migration mapping)
--   - dbo.TabCisOrg preserved (Helios identity, ne-migrated)
--   - +TOP (:limit) defensive cap
--   - Drop DELETE statement (Centrála 1 housekeeping side effect — TODO maintenance trigger)
--   - Drop placeholder row UNION ALL (AG Grid handles empty state natively)
-- ============================================================

BEGIN;


-- ════════════════════════════════════════════════════════════════
-- KROK 4d: Akce sub-grid (Centrála #40006 adapted)
-- ════════════════════════════════════════════════════════════════
-- code: crm_kontakt_akce_detail
-- 3 JOINs: KontaktAkce + AkceCis + MailSablonyCis (vše st.*)
-- 31 sloupců (z placeholder UNION ALL preserved column list)

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_akce_detail',
$sql$SELECT TOP (:limit)
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
    KA.OdkazEditor,
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
WHERE KA.IDhlav = :master_id
ORDER BY KAC.Poradi ASC$sql$,
       2,
       'CRM Akce sub-grid (Centrála #40006) — per-master detail v Kontakt jádře. dbo→st, :ID→:master_id, drop DELETE+placeholder, +TOP (:limit).',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_akce_detail');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_akce_detail', 'CRM Akce (sub-grid v jádře)',
       'Per-master Akce sub-grid (Centrála #40006). Wire-up Kontakt jádro v Kroku 5.',
       'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_akce_detail');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akce_detail'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_akce_detail'),
       'select-detail', 'default', TRUE,
       'CRM Akce sub-grid per master_id (select-detail kind, Phase H+3)'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akce_detail')
      AND variant_code = 'default'
      AND operation_kind = 'select-detail'
);


-- ════════════════════════════════════════════════════════════════
-- KROK 4e: Kontaktní údaje sub-grid (Centrála #40007 adapted)
-- ════════════════════════════════════════════════════════════════
-- code: crm_kontakt_osoby_detail
-- UNION ALL v derived table: Typ=1 firma (IDakce=16) + Typ=2 osoby (IDakce=17)
-- 4 JOINs per branch: KontaktAkce + AkceCis + Kontakt + dbo.TabCisOrg
-- 13 sloupců output (Typ, FirmaOrPozice, Jmeno, Prijemni, Telefon, Mobil,
--                    Email, Web, LinkedIn, ID_E, ID, ID_LastAkce, IDakce)

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'crm_kontakt_osoby_detail',
$sql$SELECT TOP (:limit) *
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
    WHERE KA.IDhlav = :master_id and KA.IDakce = 16
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
    WHERE KA.IDhlav = :master_id and KA.IDakce = 17
) as X$sql$,
       2,
       'CRM Kontaktní údaje sub-grid (Centrála #40007) — Typ=1 firma (IDakce=16) + Typ=2 osoby (IDakce=17) UNION ALL. dbo→st, :ID→:master_id, dbo.TabCisOrg preserved.',
       'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'crm_kontakt_osoby_detail');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'crm_kontakt_osoby_detail', 'CRM Kontaktní údaje (sub-grid v jádře)',
       'Per-master Kontaktní údaje sub-grid (Centrála #40007). Typ=1 firma + Typ=2 osoby polymorfní rows. Wire-up Kontakt jádro v Kroku 5.',
       'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'crm_kontakt_osoby_detail');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_osoby_detail'),
       (SELECT id FROM fw.data_set    WHERE code = 'crm_kontakt_osoby_detail'),
       'select-detail', 'default', TRUE,
       'CRM Kontaktní údaje sub-grid per master_id (select-detail kind, Phase H+3)'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_osoby_detail')
      AND variant_code = 'default'
      AND operation_kind = 'select-detail'
);


-- ════════════════════════════════════════════════════════════════
-- POST-CHECK + VERIFY
-- ════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_ds   FROM fw.data_source    WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail');
    SELECT COUNT(*) INTO v_dset FROM fw.data_set       WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail');
    SELECT COUNT(*) INTO v_dso  FROM fw.data_source_op WHERE data_source_id IN (SELECT id FROM fw.data_source WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail'))
                                                         AND operation_kind = 'select-detail';

    RAISE NOTICE '--- POST-CHECK Krok 4d+4e ---';
    RAISE NOTICE 'fw.data_source       sub-gridy: % / 2', v_ds;
    RAISE NOTICE 'fw.data_set          sub-gridy: % / 2', v_dset;
    RAISE NOTICE 'fw.data_source_op    select-detail: % / 2', v_dso;

    IF v_ds = 2 AND v_dset = 2 AND v_dso = 2 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: 2 sub-gridy LIVE (Centrála #40006 + #40007 adapted)';
        RAISE NOTICE '------';
        RAISE NOTICE 'SMOKE TEST URL (vyber kontakt z Marti screenshot, např. master_id=1479):';
        RAISE NOTICE '  /api/v1/erp/data/crm_kontakt_akce_detail?master_id=1479&kind=select-detail';
        RAISE NOTICE '    Expected: rows[N] z st.CRM_Kontakt_Akce filtrované IDhlav=1479';
        RAISE NOTICE '  /api/v1/erp/data/crm_kontakt_osoby_detail?master_id=1479&kind=select-detail';
        RAISE NOTICE '    Expected: rows[N] s Typ=1 firma + Typ=2 osoby (IDakce 16/17)';
        RAISE NOTICE '------';
        RAISE NOTICE 'Wire-up do Kontakt jádra přijde v Kroku 5 (nested grid v jádře).';
    ELSE
        RAISE NOTICE 'INCOMPLETE: nějaký počet < 2. Check above.';
    END IF;
END $$;


-- Final verify — data_source rows + kind mapping
SELECT
    ds.code AS data_source_code,
    ds.name,
    op.operation_kind,
    op.variant_code,
    dset.id AS data_set_id,
    LEFT(dset.sql_text, 80) || '...' AS sql_preview,
    LENGTH(dset.sql_text) AS sql_length
FROM fw.data_source ds
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE ds.code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail')
ORDER BY ds.code;

COMMIT;


-- ============================================================
-- SMOKE TEST (žádný service restart potřeba):
-- ============================================================
-- 1. Vybrat libovolný kontakt ID z Marti screenshot (např. master_id=1479)
-- 2. URL test #1 (Akce sub-grid):
--    /api/v1/erp/data/crm_kontakt_akce_detail?master_id=1479&kind=select-detail
--    Expected JSON:
--      "ok": true
--      "rows": [N], kde N = počet Akce pro kontakt 1479 (z Marti screenshotu 6)
--      "execution_path": "mcp_mssql"
--      "operation": {"kind": "select-detail", ...}
--
-- 3. URL test #2 (Kontaktní údaje sub-grid):
--    /api/v1/erp/data/crm_kontakt_osoby_detail?master_id=1479&kind=select-detail
--    Expected JSON:
--      "rows": [
--        {"Typ": 1, "FirmaOrPozice": "Braun&Toth Absaugtechnik GmbH", "Jmeno": null,
--         "Prijmeni": null, "Email": "info@braunundtoth.de", "Telefon": "+49 9371 97320", ...},
--        {"Typ": 2, "FirmaOrPozice": null, "Jmeno": "Christoph", "Prijmeni": "Hoffmann",
--         "Email": null, "Telefon": null, ...}
--      ]
--    Match Marti screenshot Kontaktní údaje grid (2 rows v jádře #1479).
--
-- 4. Pokud oba projdou → Krok 5 (Kontakt jádro) bude wire-up nested grids
--    na tyto data_sources přes :master_id z parent row.ID.
--
-- 5. Pošli Marti: „2 sub-gridy LIVE — master_id=1479 verify match screenshot"
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne):
-- ============================================================
-- BEGIN;
-- DELETE FROM fw.data_source_op WHERE data_source_id IN
--   (SELECT id FROM fw.data_source WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail'));
-- DELETE FROM fw.data_set       WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail');
-- DELETE FROM fw.data_source    WHERE code IN ('crm_kontakt_akce_detail', 'crm_kontakt_osoby_detail');
-- COMMIT;
-- ============================================================


-- ============================================================
-- TODO post-smoke:
-- ============================================================
-- 1. Maintenance trigger pro orphan cleanup (Centrála 1 DELETE side effect):
--    CREATE TRIGGER trg_st_crm_kontakt_akce_cleanup_orphan
--    ON st.CRM_Kontakt_Akce AFTER INSERT, UPDATE
--    AS BEGIN
--        DELETE FROM st.CRM_Kontakt_Akce WHERE IDakce IS NULL;
--    END
--    (Nebo separate scheduled task v Phase 39+ maintenance).
--
-- 2. Krok 5 wire-up: v Kontakt jádře (fw.core 'crm_kontakt_edit'),
--    2× fw.comp_def type 110 nested_grid s data_source_id pointing
--    na crm_kontakt_akce_detail + crm_kontakt_osoby_detail.
--    Plus :master_id substituce z parent row.ID v runtime.
-- ============================================================
