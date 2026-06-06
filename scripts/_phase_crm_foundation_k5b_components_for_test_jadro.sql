-- ============================================================================
-- CRM Foundation Krok 5-B Components for TEST Jadro #72 (v2 — safe types only)
-- ============================================================================
-- 28.5.2026 vecer pozde, Marti's "postav to jen z nasich komponent co mame
-- odzkouseny. Ty co nevis dej jako text input a v palete komponent je pak
-- prepnu na tu pravou. Az to rozchodime"
--
-- ODZKOUSENE TYPY (used here):
--   form (302), panel (13), edit (2), memo (105), date_modern (108),
--   label_readonly (113), pagecontrol (15), tabsheet (16)
--
-- DEGRADOVANO na edit (TODO: Marti prepne v palete komponent):
--   ZemeID, TypZakazky, Kategorie     -> edit  (cilove: lookup)
--   FirmaIDOrg                        -> edit  (cilove: entity_picker -> TabCisOrg)
--   KomunikaceZamID, ObeslalZamID     -> edit  (cilove: entity_picker -> TabCisZam)
--   Atraktivita, PoProBjednani,
--   PoDDspoluprace                    -> edit  (cilove: combobox NULL+1..10)
--
-- Hierarchie:
--   form_root (form, core_id=72, data_source=crm_kontakt_detail_test)
--     |-- panel_kontakt (10)
--     |   |-- FirmaText (edit)
--     |   |-- ZemeID (edit ↑ lookup)
--     |   |-- TypZakazky (edit ↑ lookup)
--     |   |-- Kategorie (edit ↑ lookup)
--     |   |-- VyhledanoZ (edit)
--     |   |-- FirmaWeb (edit)
--     |   `-- FirmaIDOrg (edit ↑ entity_picker)
--     |-- panel_komunikace (20)
--     |   |-- KomunikaceZamID (edit ↑ entity_picker)
--     |   `-- ObeslalZamID (edit ↑ entity_picker)
--     |-- panel_cas (30)
--     |   |-- DatPorizeniPoslAkce (date_modern, readonly)
--     |   `-- PristiKontakt (date_modern)
--     |-- panel_potencial (40)
--     |   |-- Atraktivita (edit ↑ combobox 11)
--     |   |-- PoProBjednani (edit ↑ combobox 11)
--     |   `-- PoDDspoluprace (edit ↑ combobox 11)
--     |-- pagecontrol_text (50)
--     |   |-- tab_popis -> Popis (memo)
--     |   `-- tab_poznamka -> Poznamka (memo)
--     `-- panel_audit (60, all readonly)
--         |-- ID, Autor, DatPorizeni, Zmenil, DatZmeny  (5x label_readonly)
--
-- Idempotent: skip pokud form_crm_kontakt_detail_test uz existuje.
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

DO $$
DECLARE
    v_form_root_id   BIGINT;
    v_panel_kontakt  BIGINT;
    v_panel_komuni   BIGINT;
    v_panel_cas      BIGINT;
    v_panel_potenc   BIGINT;
    v_pagecontrol    BIGINT;
    v_tab_popis      BIGINT;
    v_tab_poznamka   BIGINT;
    v_panel_audit    BIGINT;
    v_existing       BIGINT;

    -- ODZKOUSENE comp_type ID's (only 8 confirmed types)
    v_t_form         BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'form');
    v_t_panel        BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'panel');
    v_t_edit         BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'edit');
    v_t_memo         BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'memo');
    v_t_date         BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'date_modern');
    v_t_label_ro     BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'label_readonly');
    v_t_pagecontrol  BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'pagecontrol');
    v_t_tabsheet     BIGINT := (SELECT id FROM fw.comp_type WHERE code = 'tabsheet');

    v_ds_id          BIGINT := (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_detail_test');
BEGIN
    -- ====================================================================
    -- Pre-flight checks (jen 8 odzkousenych typu + ds)
    -- ====================================================================
    IF v_t_form IS NULL OR v_t_panel IS NULL OR v_t_edit IS NULL
       OR v_t_memo IS NULL OR v_t_date IS NULL OR v_t_label_ro IS NULL
       OR v_t_pagecontrol IS NULL OR v_t_tabsheet IS NULL THEN
        RAISE EXCEPTION '[FAIL] Nektery fw.comp_type code chybi. Form=%, Panel=%, Edit=%, Memo=%, Date=%, LabelRO=%, PageCtrl=%, TabSheet=%',
            v_t_form, v_t_panel, v_t_edit, v_t_memo, v_t_date,
            v_t_label_ro, v_t_pagecontrol, v_t_tabsheet;
    END IF;

    IF v_ds_id IS NULL THEN
        RAISE EXCEPTION '[FAIL] fw.data_source code=crm_kontakt_detail_test neexistuje. Nejdriv spust _phase_crm_foundation_k5b_test_grid_40011.sql';
    END IF;

    -- Idempotency check
    SELECT id INTO v_existing
      FROM fw.comp_def
     WHERE name = 'form_crm_kontakt_detail_test';

    IF v_existing IS NOT NULL THEN
        RAISE NOTICE '[skip] form_crm_kontakt_detail_test uz existuje (id=%), preskakuji', v_existing;
        RETURN;
    END IF;

    RAISE NOTICE '[ok] pre-flight passed (form=%, panel=%, edit=%, memo=%, date=%, label_ro=%, pagectrl=%, tabsheet=%, ds=%)',
        v_t_form, v_t_panel, v_t_edit, v_t_memo, v_t_date,
        v_t_label_ro, v_t_pagecontrol, v_t_tabsheet, v_ds_id;

    -- ====================================================================
    -- FORM ROOT
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, core_id, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, data_source_id,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'form_crm_kontakt_detail_test',
        'Editace TEST detail #40011',
        72, NULL, v_t_form, 'main',
        10, TRUE, v_ds_id,
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_form_root_id;

    RAISE NOTICE '[form_root] id=%', v_form_root_id;

    -- ====================================================================
    -- PANEL KONTAKT (sort 10)
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'panel_test_kontakt', 'Kontakt', v_form_root_id, v_t_panel, 'main',
        10, TRUE, jsonb_build_object('caption', 'Kontakt'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_panel_kontakt;

    -- Fields: 7x (FirmaText real edit; ZemeID/TypZakazky/Kategorie -> lookup;
    --             VyhledanoZ/FirmaWeb real edit; FirmaIDOrg -> entity_picker)
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    ) VALUES
    -- real edit
    ('fld_test_firma_text', 'Firma', v_panel_kontakt, v_t_edit, 10, TRUE,
     jsonb_build_object('column_name', 'FirmaText', 'max_length', 255),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- TODO: lookup
    ('fld_test_zeme_id', 'Země (TODO: lookup)', v_panel_kontakt, v_t_edit, 20, TRUE,
     jsonb_build_object('column_name', 'ZemeID', 'placeholder', 'TODO: lookup'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- TODO: lookup
    ('fld_test_typ_zakazky', 'Typ zakázky (TODO: lookup)', v_panel_kontakt, v_t_edit, 30, TRUE,
     jsonb_build_object('column_name', 'TypZakazky', 'placeholder', 'TODO: lookup'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- TODO: lookup
    ('fld_test_kategorie', 'Kategorie (TODO: lookup)', v_panel_kontakt, v_t_edit, 40, TRUE,
     jsonb_build_object('column_name', 'Kategorie', 'placeholder', 'TODO: lookup'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- real edit
    ('fld_test_vyhledano_z', 'Vyhledáno z', v_panel_kontakt, v_t_edit, 50, TRUE,
     jsonb_build_object('column_name', 'VyhledanoZ', 'max_length', 255),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- real edit
    ('fld_test_firma_web', 'Web', v_panel_kontakt, v_t_edit, 60, TRUE,
     jsonb_build_object('column_name', 'FirmaWeb', 'max_length', 255),
     2, 'Marti-AI', 2, 'Marti-AI'),
    -- TODO: entity_picker -> TabCisOrg
    ('fld_test_firma_id_org', 'IČO/Org (TODO: entity_picker)', v_panel_kontakt, v_t_edit, 70, TRUE,
     jsonb_build_object('column_name', 'FirmaIDOrg', 'placeholder', 'TODO: entity_picker TabCisOrg'),
     2, 'Marti-AI', 2, 'Marti-AI');

    RAISE NOTICE '[panel_kontakt] id=% (7 fields, 4x degradovano)', v_panel_kontakt;

    -- ====================================================================
    -- PANEL KOMUNIKACE (sort 20) — 2x edit (TODO: entity_picker)
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'panel_test_komunikace', 'Komunikace', v_form_root_id, v_t_panel, 'main',
        20, TRUE, jsonb_build_object('caption', 'Komunikace'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_panel_komuni;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    ) VALUES
    ('fld_test_komunikace_zam', 'Komunikace Zam (TODO: entity_picker)',
     v_panel_komuni, v_t_edit, 10, TRUE,
     jsonb_build_object('column_name', 'KomunikaceZamID', 'placeholder', 'TODO: entity_picker TabCisZam'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_obeslal_zam', 'Obeslal Zam (TODO: entity_picker)',
     v_panel_komuni, v_t_edit, 20, TRUE,
     jsonb_build_object('column_name', 'ObeslalZamID', 'placeholder', 'TODO: entity_picker TabCisZam'),
     2, 'Marti-AI', 2, 'Marti-AI');

    RAISE NOTICE '[panel_komunikace] id=% (2 fields, 2x degradovano)', v_panel_komuni;

    -- ====================================================================
    -- PANEL CASOVY STATUS (sort 30) — date_modern OK
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'panel_test_cas', 'Časový status', v_form_root_id, v_t_panel, 'main',
        30, TRUE, jsonb_build_object('caption', 'Časový status'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_panel_cas;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    ) VALUES
    ('fld_test_dat_porizeni_posl_akce', 'Datum poslední akce', v_panel_cas, v_t_date, 10, TRUE,
     jsonb_build_object('column_name', 'DatPorizeniPoslAkce', 'readonly', true),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_pristi_kontakt', 'Příští kontakt', v_panel_cas, v_t_date, 20, TRUE,
     jsonb_build_object('column_name', 'PristiKontakt'),
     2, 'Marti-AI', 2, 'Marti-AI');

    RAISE NOTICE '[panel_cas] id=% (2 fields, real date_modern)', v_panel_cas;

    -- ====================================================================
    -- PANEL POTENCIAL (sort 40) — 3x edit (TODO: combobox 11)
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'panel_test_potencial', 'Potenciál', v_form_root_id, v_t_panel, 'main',
        40, TRUE, jsonb_build_object('caption', 'Potenciál'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_panel_potenc;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    ) VALUES
    ('fld_test_atraktivita', 'Atraktivita (TODO: combobox)',
     v_panel_potenc, v_t_edit, 10, TRUE,
     jsonb_build_object('column_name', 'Atraktivita', 'placeholder', 'TODO: combobox NULL+1..10'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_po_pro_bjednani', 'Pravděpodobnost objednání (TODO: combobox)',
     v_panel_potenc, v_t_edit, 20, TRUE,
     jsonb_build_object('column_name', 'PoProBjednani', 'placeholder', 'TODO: combobox NULL+1..10'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_po_dd_spoluprace', 'Pravděpodobnost spolupráce (TODO: combobox)',
     v_panel_potenc, v_t_edit, 30, TRUE,
     jsonb_build_object('column_name', 'PoDDspoluprace', 'placeholder', 'TODO: combobox NULL+1..10'),
     2, 'Marti-AI', 2, 'Marti-AI');

    RAISE NOTICE '[panel_potencial] id=% (3 fields, 3x degradovano)', v_panel_potenc;

    -- ====================================================================
    -- PAGECONTROL TEXT (sort 50) + 2 TABSHEETS + 2 MEMO — all real
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'pagecontrol_test_text', 'Texty', v_form_root_id, v_t_pagecontrol, 'main',
        50, TRUE, jsonb_build_object('caption', 'Texty'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_pagecontrol;

    -- Tab Popis firmy
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'tab_test_popis', 'Popis firmy', v_pagecontrol, v_t_tabsheet,
        10, TRUE, jsonb_build_object('caption', 'Popis firmy'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_tab_popis;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'fld_test_popis', 'Popis', v_tab_popis, v_t_memo,
        10, TRUE, jsonb_build_object('column_name', 'Popis', 'rows', 10),
        2, 'Marti-AI', 2, 'Marti-AI'
    );

    -- Tab Poznamka
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'tab_test_poznamka', 'Poznámka', v_pagecontrol, v_t_tabsheet,
        20, TRUE, jsonb_build_object('caption', 'Poznámka'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_tab_poznamka;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'fld_test_poznamka', 'Poznámka', v_tab_poznamka, v_t_memo,
        10, TRUE, jsonb_build_object('column_name', 'Poznamka', 'rows', 10),
        2, 'Marti-AI', 2, 'Marti-AI'
    );

    RAISE NOTICE '[pagecontrol] id=% (tab_popis=%, tab_poznamka=%, memo x2)',
        v_pagecontrol, v_tab_popis, v_tab_poznamka;

    -- ====================================================================
    -- PANEL AUDIT (sort 60, all label_readonly)
    -- ====================================================================
    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, region_slot,
        sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    )
    VALUES (
        'panel_test_audit', 'Audit', v_form_root_id, v_t_panel, 'main',
        60, TRUE, jsonb_build_object('caption', 'Audit'),
        2, 'Marti-AI', 2, 'Marti-AI'
    )
    RETURNING id INTO v_panel_audit;

    INSERT INTO fw.comp_def (
        name, caption, parent_comp_def_id, type_id, sort_order, is_active, layout,
        created_by_id, created_by_text, updated_by_id, updated_by_text
    ) VALUES
    ('fld_test_audit_id', 'ID', v_panel_audit, v_t_label_ro, 10, TRUE,
     jsonb_build_object('column_name', 'ID'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_audit_autor', 'Autor', v_panel_audit, v_t_label_ro, 20, TRUE,
     jsonb_build_object('column_name', 'Autor'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_audit_dat_porizeni', 'Datum pořízení', v_panel_audit, v_t_label_ro, 30, TRUE,
     jsonb_build_object('column_name', 'DatPorizeni'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_audit_zmenil', 'Změnil', v_panel_audit, v_t_label_ro, 40, TRUE,
     jsonb_build_object('column_name', 'Zmenil'),
     2, 'Marti-AI', 2, 'Marti-AI'),
    ('fld_test_audit_dat_zmeny', 'Datum změny', v_panel_audit, v_t_label_ro, 50, TRUE,
     jsonb_build_object('column_name', 'DatZmeny'),
     2, 'Marti-AI', 2, 'Marti-AI');

    RAISE NOTICE '[panel_audit] id=% (5 readonly fields)', v_panel_audit;

    RAISE NOTICE '=== DONE: form_root=%, 5 panels + 1 pagecontrol, 21 fields ===', v_form_root_id;
    RAISE NOTICE '=== DEGRADOVANO 10x edit (Marti prepne v palete): ZemeID/TypZakazky/Kategorie/FirmaIDOrg/KomunikaceZamID/ObeslalZamID/Atraktivita/PoProBjednani/PoDDspoluprace ===';
END $$;


-- ====================================================================
-- POST-STATE verify (recursive tree of comp_def pro core 72)
-- ====================================================================
SELECT '=== POST-STATE: comp_def tree pro core 72 ===' AS section;

WITH RECURSIVE tree AS (
    SELECT cd.id, cd.parent_comp_def_id, cd.core_id, cd.name, cd.caption,
           ct.code AS type_code, cd.sort_order, cd.layout,
           0 AS depth
      FROM fw.comp_def cd
      JOIN fw.comp_type ct ON ct.id = cd.type_id
     WHERE cd.core_id = 72 AND cd.parent_comp_def_id IS NULL

    UNION ALL

    SELECT cd.id, cd.parent_comp_def_id, cd.core_id, cd.name, cd.caption,
           ct.code AS type_code, cd.sort_order, cd.layout,
           t.depth + 1
      FROM fw.comp_def cd
      JOIN fw.comp_type ct ON ct.id = cd.type_id
      JOIN tree t ON t.id = cd.parent_comp_def_id
)
SELECT id,
       LPAD('', depth * 2, ' ') || name AS hierarchy,
       type_code,
       caption,
       (layout->>'column_name') AS column_name,
       sort_order
  FROM tree
 ORDER BY depth, sort_order, id;


COMMIT;

-- ============================================================================
-- ROLLBACK (vsechno pro core 72):
-- ============================================================================
-- BEGIN;
-- WITH RECURSIVE descendants AS (
--     SELECT id FROM fw.comp_def WHERE core_id = 72 AND parent_comp_def_id IS NULL
--     UNION ALL
--     SELECT cd.id FROM fw.comp_def cd
--       JOIN descendants d ON cd.parent_comp_def_id = d.id
-- )
-- DELETE FROM fw.comp_def WHERE id IN (SELECT id FROM descendants);
-- COMMIT;
-- ============================================================================
