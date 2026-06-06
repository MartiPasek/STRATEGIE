-- ============================================================================
-- CRM Foundation Krok 5-B — Kontakt edit form ZÁKLADNÍ FIELDY
-- 28.5.2026 vecer pozde, Marti's "zakladni fieldy, pak slozitejsi"
-- ============================================================================
-- Predpoklad: Krok 5-A v2 skeleton LIVE (form_crm_kontakt_edit + 2 nested grids).
-- Core 63 = "Editace kontaktu" (st.CRM_Kontakt master).
--
-- Pridava 4 panely (children of form_root) + 16 fields.
-- Skip slozitejsi: Kategorie/TypZakazky/Atraktivita/ZemeID/FK lookups (PoDDspoluprace
-- atd.) — prijdou v Krok 5-C az probereme dropdown lookup pattern.
--
-- Pattern (Marti's "fw self edited" doctrine, Krok 13 Uniform Components 11.5.):
--   - Panely jsou children of form_root, type='panel' (Delphi 13)
--   - Fields jsou children of panely, type='edit'/'memo'/'date_modern'/'label_readonly'
--   - Audit fields (RO) v separatnim panelu — Centrala 1 pattern
--   - column_name v layout JSONB = MSSQL column name (PascalCase)
--   - max_length z st.CRM_Kontakt CREATE TABLE (Krok 1 migration script)
--
-- CHK constraint chk_comp_def_single_parent: child comp_def MA parent_comp_def_id
-- + core_id=NULL. Pojistka proti dual-parent (Krok 13 doctrine).
--
-- Smoke (po deploy):
--   Marti otevre Kontakty grid → Oprava Belgie ID=1479 → modal s 4 panely + 2 nested
--   gridy. Edit Popis → klik OK → ověř audit autofill (Zmenil="Martin", DatZmeny=NOW)
--   pres get_row.
-- ============================================================================

BEGIN;

-- ════════════════════════════════════════════════════════════════
-- Pre-flight: ověř skeleton (form_root + 2 nested grids) LIVE
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    v_form_root_id BIGINT;
    v_existing_panels INT;
BEGIN
    SELECT id INTO v_form_root_id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit';
    IF v_form_root_id IS NULL THEN
        RAISE EXCEPTION 'PREREQ FAIL: form_crm_kontakt_edit neexistuje. Deploy Krok 5-A v2 skeleton first.';
    END IF;

    SELECT COUNT(*) INTO v_existing_panels
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.parent_comp_def_id = v_form_root_id
      AND ct.code = 'panel';

    IF v_existing_panels > 0 THEN
        RAISE NOTICE 'NOTE: % panel(s) uz existuje pod form_root — script je idempotent (skip duplicates).', v_existing_panels;
    END IF;

    RAISE NOTICE 'Pre-flight OK: form_root id=%', v_form_root_id;
END $$;


-- ════════════════════════════════════════════════════════════════
-- 1. PANEL IDENTIFIKACE — Firma, Kontakt, Země (3 fields)
-- ════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'panel_kontakt_identifikace', 'Identifikace',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       (SELECT id FROM fw.comp_type WHERE code = 'panel'),
       'main', 110, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'panel_kontakt_identifikace');

-- Field: FirmaText
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_FirmaText', 'Firma',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_identifikace'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 10, TRUE,
       jsonb_build_object('column_name', 'FirmaText', 'max_length', 256),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_FirmaText');

-- Field: KontaktText
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_KontaktText', 'Kontaktní osoba',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_identifikace'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 20, TRUE,
       jsonb_build_object('column_name', 'KontaktText', 'max_length', 256),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_KontaktText');

-- Field: Zeme (denormalized text — ZemeID FK lookup later v Krok 5-C)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_Zeme', 'Země',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_identifikace'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 30, TRUE,
       jsonb_build_object('column_name', 'Zeme', 'max_length', 128),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_Zeme');


-- ════════════════════════════════════════════════════════════════
-- 2. PANEL KONTAKTY — Telefon, Email, Web (3 fields)
-- ════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'panel_kontakt_kontakty', 'Kontakty',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       (SELECT id FROM fw.comp_type WHERE code = 'panel'),
       'main', 120, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'panel_kontakt_kontakty');

-- Field: FirmaTelefon
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_FirmaTelefon', 'Telefon',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_kontakty'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 10, TRUE,
       jsonb_build_object('column_name', 'FirmaTelefon', 'max_length', 60),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_FirmaTelefon');

-- Field: FirmaEmail
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_FirmaEmail', 'Email',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_kontakty'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 20, TRUE,
       jsonb_build_object('column_name', 'FirmaEmail', 'max_length', 256),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_FirmaEmail');

-- Field: FirmaWeb
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_FirmaWeb', 'Web',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_kontakty'),
       (SELECT id FROM fw.comp_type WHERE code = 'edit'),
       'main', 30, TRUE,
       jsonb_build_object('column_name', 'FirmaWeb', 'max_length', 1000),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_FirmaWeb');


-- ════════════════════════════════════════════════════════════════
-- 3. PANEL CRM — PristiKontakt, Popis, Poznamka, VyhledanoZ (4 fields)
-- ════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'panel_kontakt_crm', 'CRM data',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       (SELECT id FROM fw.comp_type WHERE code = 'panel'),
       'main', 130, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'panel_kontakt_crm');

-- Field: PristiKontakt (date)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_PristiKontakt', 'Příští kontakt',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_crm'),
       (SELECT id FROM fw.comp_type WHERE code = 'date_modern'),
       'main', 10, TRUE,
       jsonb_build_object('column_name', 'PristiKontakt'),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_PristiKontakt');

-- Field: Popis (memo, NVARCHAR MAX)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_Popis', 'Popis',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_crm'),
       (SELECT id FROM fw.comp_type WHERE code = 'memo'),
       'main', 20, TRUE,
       jsonb_build_object('column_name', 'Popis', 'rows', 4),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_Popis');

-- Field: Poznamka (memo, 1000)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_Poznamka', 'Poznámka',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_crm'),
       (SELECT id FROM fw.comp_type WHERE code = 'memo'),
       'main', 30, TRUE,
       jsonb_build_object('column_name', 'Poznamka', 'max_length', 1000, 'rows', 3),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_Poznamka');

-- Field: VyhledanoZ (memo, 1000)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_VyhledanoZ', 'Vyhledáno z',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_crm'),
       (SELECT id FROM fw.comp_type WHERE code = 'memo'),
       'main', 40, TRUE,
       jsonb_build_object('column_name', 'VyhledanoZ', 'max_length', 1000, 'rows', 2),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_VyhledanoZ');


-- ════════════════════════════════════════════════════════════════
-- 4. PANEL AUDIT (RO) — ID, Autor, DatPorizeni, Zmenil, DatZmeny
-- ════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'panel_kontakt_audit', 'Audit',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       (SELECT id FROM fw.comp_type WHERE code = 'panel'),
       'main', 140, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'panel_kontakt_audit');

-- Field: ID (RO)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_audit_ID', 'ID',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit'),
       (SELECT id FROM fw.comp_type WHERE code = 'label_readonly'),
       'main', 10, TRUE,
       jsonb_build_object('column_name', 'ID', 'mono', true),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_audit_ID');

-- Field: Autor (RO)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_audit_Autor', 'Pořídil',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit'),
       (SELECT id FROM fw.comp_type WHERE code = 'label_readonly'),
       'main', 20, TRUE,
       jsonb_build_object('column_name', 'Autor'),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_audit_Autor');

-- Field: DatPorizeni (RO)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_audit_DatPorizeni', 'Datum pořízení',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit'),
       (SELECT id FROM fw.comp_type WHERE code = 'label_readonly'),
       'main', 30, TRUE,
       jsonb_build_object('column_name', 'DatPorizeni'),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_audit_DatPorizeni');

-- Field: Zmenil (RO)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_audit_Zmenil', 'Změnil',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit'),
       (SELECT id FROM fw.comp_type WHERE code = 'label_readonly'),
       'main', 40, TRUE,
       jsonb_build_object('column_name', 'Zmenil'),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_audit_Zmenil');

-- Field: DatZmeny (RO)
INSERT INTO fw.comp_def (
    name, caption, core_id, parent_comp_def_id,
    type_id, region_slot, sort_order, is_active,
    layout,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT 'field_kontakt_audit_DatZmeny', 'Datum změny',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit'),
       (SELECT id FROM fw.comp_type WHERE code = 'label_readonly'),
       'main', 50, TRUE,
       jsonb_build_object('column_name', 'DatZmeny'),
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'field_kontakt_audit_DatZmeny');


-- ════════════════════════════════════════════════════════════════
-- POST-CHECK
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    v_form_root_id BIGINT;
    v_panels_count INT;
    v_fields_count INT;
    v_audit_fields_count INT;
BEGIN
    SELECT id INTO v_form_root_id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit';

    SELECT COUNT(*) INTO v_panels_count
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.parent_comp_def_id = v_form_root_id
      AND ct.code = 'panel';

    SELECT COUNT(*) INTO v_fields_count
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.parent_comp_def_id IN (
        SELECT id FROM fw.comp_def
        WHERE name IN ('panel_kontakt_identifikace', 'panel_kontakt_kontakty', 'panel_kontakt_crm')
    )
      AND ct.code IN ('edit', 'memo', 'date_modern');

    SELECT COUNT(*) INTO v_audit_fields_count
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.parent_comp_def_id = (SELECT id FROM fw.comp_def WHERE name = 'panel_kontakt_audit')
      AND ct.code = 'label_readonly';

    RAISE NOTICE '--- POST-CHECK Krok 5-B ---';
    RAISE NOTICE 'Panels under form_root:   % (expected 4: Identifikace, Kontakty, CRM, Audit)', v_panels_count;
    RAISE NOTICE 'Editable fields (3 pan.): % (expected 10)', v_fields_count;
    RAISE NOTICE 'RO audit fields:          % (expected 5)', v_audit_fields_count;

    IF v_panels_count = 4 AND v_fields_count = 10 AND v_audit_fields_count = 5 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: Krok 5-B basic fields LIVE.';
        RAISE NOTICE 'Smoke: Marti Kontakty grid → Oprava Belgie ID=1479 → modal s 4 panely';
        RAISE NOTICE '       + 2 nested grids (Kontaktní údaje + Akce).';
        RAISE NOTICE '------';
    ELSE
        RAISE NOTICE 'INCOMPLETE: panel count or field count mismatch — check above.';
    END IF;
END $$;


-- Final verify — full form hierarchy
SELECT
    cd.id,
    cd.name,
    cd.caption,
    ct.code AS type_code,
    cd.parent_comp_def_id,
    parent.name AS parent_name,
    cd.sort_order,
    cd.layout->>'column_name' AS column_name
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.comp_def parent ON parent.id = cd.parent_comp_def_id
WHERE cd.core_id = 63
   OR cd.parent_comp_def_id IN (
        SELECT id FROM fw.comp_def WHERE core_id = 63
            OR parent_comp_def_id IN (SELECT id FROM fw.comp_def WHERE core_id = 63)
   )
ORDER BY
    COALESCE(cd.core_id, 0) DESC,  -- form_root first (core_id=63)
    parent.sort_order NULLS FIRST,
    cd.sort_order;

COMMIT;


-- ============================================================================
-- ROLLBACK (drop fields + panels, ne form_root):
-- ============================================================================
-- BEGIN;
-- DELETE FROM fw.comp_def
-- WHERE name LIKE 'field_kontakt_%'
--    OR name IN ('panel_kontakt_identifikace', 'panel_kontakt_kontakty',
--                'panel_kontakt_crm', 'panel_kontakt_audit');
-- COMMIT;
-- ============================================================================
