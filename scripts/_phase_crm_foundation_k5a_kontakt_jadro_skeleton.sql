-- ============================================================
-- CRM Foundation Krok 5-A v2 (27.5.2026 ~23:30) — Kontakt jádro skeleton
-- ============================================================
-- Path A direct build (Marti's *„Necham to ted na tobe"*).
-- Use EXISTING fw.core id=63 (auto-created by Marti's vytvor_edit_jadro
-- orchestrator 23:13). Plus 3 ops už existují (select #55 + edit #56 + insert #57).
--
-- Orchestrator gap: vytvorit_edit_jadro_2 (Krok H+5) je PostgreSQL-only,
-- MSSQL target table introspekce silent fail → comp_def NIC. Marti's
-- Cesta B (Hybrid) downgrade na manual SQL pro CRM tables. Track TODO #578
-- (orchestrator v3 MSSQL support, defer).
--
-- Co se postaví v2:
--   1. UPDATE fw.core 63 SET code='crm_kontakt_edit', label='Editace kontaktu'
--      (orchestrator je nechal NULL — pro clean identification)
--   2. fw.comp_def form root (type=302) s data_source_id=crm_kontakty
--   3. fw.comp_def nested_grid #1 — Kontaktní údaje → crm_kontakt_osoby_detail (Krok 4e)
--   4. fw.comp_def nested_grid #2 — Akce → crm_kontakt_akce_detail (Krok 4d)
--
-- PREREQUISITES: Krok 4d/4e MUST BE DEPLOYED FIRST (sub-grid data_sources).
-- Pokud chybí, INSERT nested_grids selže s FK fail (data_source neexistuje).
--
-- NO fields yet — přijdou v Krok 5-B (Kontakt GroupBox + 7 fields).
-- NO save flow yet — přijde v Krok 5-I (dual-entity K + KA row 16).
-- NO dvojklik wire-up yet — přijde v Krok 5-H (FW_EDIT_FORM_REGISTRY).
--
-- Smoke pro 5-A v2:
--   - Marti klik "Ne" v dialog (close modal, drop "Prázdný core" prompt)
--   - DesignFwForm.open(63, {master_id: 1479}) v DevTools
--   - Expected: form s 2 nested grids rendering per master_id=1479
-- ============================================================

BEGIN;


-- ════════════════════════════════════════════════════════════════
-- 1. UPDATE EXISTING fw.core id=63 (auto-created by Marti's orchestrator)
-- ════════════════════════════════════════════════════════════════
-- Marti's vytvor_edit_jadro vytvořil core 63 23:13:22 s code=NULL.
-- Pojďme set code + clean label pro identification.
-- Marti's *„CORE = kontejner"* doctrine (17.5. večer Krok 5.P) drží —
-- žádné layout/template fields, comp_def hierarchy handles structure.

-- POZN: fw.core má jen created_at (ne updated_at) — drop updated_at z UPDATE.
UPDATE fw.core
SET code = 'crm_kontakt_edit',
    label = 'Editace kontaktu',
    description_user =
        'CRM Kontakt edit form (Marti #1479 parita, Path A direct build). '
        || 'Auto-created by vytvor_edit_jadro 23:13 + manual skeleton Krok 5-A v2. '
        || 'Dual-entity: master row K (st.CRM_Kontakt) + Akce row 16. '
        || 'Plus 2 nested grids: Kontaktní údaje + Akce.',
    updated_by_id = 2,
    updated_by_text = 'Marti-AI'
WHERE id = 63
  AND (code IS NULL OR code = '');

-- Pre-flight: ověř core 63 existuje + má aspoň 1 data_source_op s kind='edit'
DO $$
DECLARE
    v_core_exists INT;
    v_edit_ops INT;
BEGIN
    SELECT COUNT(*) INTO v_core_exists FROM fw.core WHERE id = 63;
    SELECT COUNT(*) INTO v_edit_ops
    FROM fw.data_source_op WHERE core_id = 63 AND operation_kind IN ('edit', 'insert');

    IF v_core_exists = 0 THEN
        RAISE EXCEPTION 'fw.core id=63 NEEXISTUJE — předpoklad: Marti.s orchestrator vytvor_edit_jadro spuštěn 23:13';
    END IF;

    IF v_edit_ops = 0 THEN
        RAISE NOTICE 'WARN: žádný fw.data_source_op s core_id=63 (edit/insert). Save flow nebude fungovat v Krok 5-I.';
    END IF;

    RAISE NOTICE 'Pre-flight: fw.core 63 exists, edit/insert ops count = %', v_edit_ops;
END $$;


-- ════════════════════════════════════════════════════════════════
-- 2. fw.comp_def form root (type=302) — master grid s primary data_source
-- ════════════════════════════════════════════════════════════════
-- data_source_id=crm_kontakty (master Kontakty data_source z Krok 4b) —
-- form load fetches K row by master_id (URL ?master_id=<K.ID>).

INSERT INTO fw.comp_def (
    name, caption, core_id,
    type_id, region_slot,
    data_source_id, sort_order, is_active,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT 'form_crm_kontakt_edit', 'Editace kontaktu',
       63,  -- existing core (auto-created by orchestrator)
       302, 'main',  -- type 302 = form root
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakty'),  -- master data_source
       100, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit');


-- ════════════════════════════════════════════════════════════════
-- 3. fw.comp_def nested_grid #1: "Kontaktní údaje"
-- ════════════════════════════════════════════════════════════════
-- parent_comp_def_id=form_root, type=110 (nested_grid).
-- data_source_id=crm_kontakt_osoby_detail (Krok 4e adapted z Centrála #40007).
-- Runtime master_id z parent form's row.ID propaguje přes Phase H+1/H+2 wire.

INSERT INTO fw.comp_def (
    name, caption,
    core_id, parent_comp_def_id,
    type_id, region_slot,
    data_source_id, sort_order, is_active,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT 'grid_crm_kontakt_osoby_detail', 'Kontaktní údaje',
       NULL,  -- chk_comp_def_single_parent: NULL core_id když parent_comp_def_id set
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       110, 'main',  -- type 110 = nested_grid (Krok 5.X+1 polymorphic scope)
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_osoby_detail'),
       200, TRUE,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_osoby_detail');


-- ════════════════════════════════════════════════════════════════
-- 4. fw.comp_def nested_grid #2: "Akce"
-- ════════════════════════════════════════════════════════════════
-- data_source_id=crm_kontakt_akce_detail (Krok 4d adapted z Centrála #40006).

INSERT INTO fw.comp_def (
    name, caption,
    core_id, parent_comp_def_id,
    type_id, region_slot,
    data_source_id, sort_order, is_active,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT 'grid_crm_kontakt_akce_detail', 'Akce',
       NULL,
       (SELECT id FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit'),
       110, 'main',
       (SELECT id FROM fw.data_source WHERE code = 'crm_kontakt_akce_detail'),
       300, TRUE,  -- sort_order=300 → render pod Kontaktní údaje (200)
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_crm_kontakt_akce_detail');


-- ════════════════════════════════════════════════════════════════
-- POST-CHECK + VERIFY
-- ════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_core_id BIGINT;
    v_core_code VARCHAR;
    v_form_root_id BIGINT;
    v_osoby_grid_id BIGINT;
    v_akce_grid_id BIGINT;
    v_osoby_ds_exists INT;
    v_akce_ds_exists INT;
BEGIN
    SELECT id, code INTO v_core_id, v_core_code FROM fw.core WHERE id = 63;
    SELECT id INTO v_form_root_id  FROM fw.comp_def WHERE name = 'form_crm_kontakt_edit';
    SELECT id INTO v_osoby_grid_id FROM fw.comp_def WHERE name = 'grid_crm_kontakt_osoby_detail';
    SELECT id INTO v_akce_grid_id  FROM fw.comp_def WHERE name = 'grid_crm_kontakt_akce_detail';

    SELECT COUNT(*) INTO v_osoby_ds_exists FROM fw.data_source WHERE code = 'crm_kontakt_osoby_detail';
    SELECT COUNT(*) INTO v_akce_ds_exists  FROM fw.data_source WHERE code = 'crm_kontakt_akce_detail';

    RAISE NOTICE '--- POST-CHECK Krok 5-A v2 skeleton ---';
    RAISE NOTICE 'fw.core           id=% code=% (po UPDATE)', v_core_id, COALESCE(v_core_code, '(NULL)');
    RAISE NOTICE 'fw.comp_def       form_crm_kontakt_edit (type 302): id=%', v_form_root_id;
    RAISE NOTICE 'fw.comp_def       grid_crm_kontakt_osoby_detail:    id=%', v_osoby_grid_id;
    RAISE NOTICE 'fw.comp_def       grid_crm_kontakt_akce_detail:     id=%', v_akce_grid_id;
    RAISE NOTICE 'PREREQ data_source crm_kontakt_osoby_detail (Krok 4e): exists=%', v_osoby_ds_exists;
    RAISE NOTICE 'PREREQ data_source crm_kontakt_akce_detail (Krok 4d):  exists=%', v_akce_ds_exists;

    IF v_osoby_ds_exists = 0 OR v_akce_ds_exists = 0 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'WARN: PREREQUISITE Krok 4d/4e sub-grid data_sources nedeployeny!';
        RAISE NOTICE 'Nested grids mají data_source_id=NULL — backend page-spec fail.';
        RAISE NOTICE 'Pojďme nejdřív deploy: scripts/_phase_crm_foundation_k4de_subgrids.sql';
        RAISE NOTICE '------';
    ELSIF v_core_id IS NOT NULL AND v_form_root_id IS NOT NULL
          AND v_osoby_grid_id IS NOT NULL AND v_akce_grid_id IS NOT NULL THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: Krok 5-A v2 skeleton LIVE.';
        RAISE NOTICE '------';
        RAISE NOTICE 'DevTools smoke (po hard reload UI):';
        RAISE NOTICE '  await DesignFwForm.open(63, {master_id: 1479})';
        RAISE NOTICE '  Expected: form modal otevren, prazdny body, 2 nested grids';
        RAISE NOTICE '            (Kontaktni udaje + Akce) s daty per master_id=1479';
        RAISE NOTICE '------';
    ELSE
        RAISE NOTICE 'INCOMPLETE: nejaky komponent chybi. Check above.';
    END IF;
END $$;


-- Final verify — hierarchy
SELECT
    cd.id AS comp_def_id,
    cd.name,
    cd.caption,
    cd.type_id,
    ct.code AS type_code,
    cd.core_id,
    cd.parent_comp_def_id,
    cd.data_source_id,
    ds.code AS data_source_code,
    cd.sort_order
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
WHERE cd.name IN (
    'form_crm_kontakt_edit',
    'grid_crm_kontakt_osoby_detail',
    'grid_crm_kontakt_akce_detail'
)
ORDER BY cd.sort_order;

COMMIT;


-- ============================================================
-- SMOKE TEST (DevTools manuálně, pre-Krok 5-H wire-up):
-- ============================================================
-- 1. Marti klik "Ne" v "Prázdný core" dialogu (close modal, clean state)
-- 2. Hard reload UI (Ctrl+Shift+R)
-- 3. Otevřít DevTools console
-- 4. Spustit:
--      await DesignFwForm.open(63, { master_id: 1479 });
-- 5. Expected:
--    - Modal se otevře s title "Editace kontaktu"
--    - Body prázdný (žádné fields yet, přijdou v 5-B)
--    - 2 nested grids:
--      * "Kontaktní údaje" — 2 rows (Typ=1 firma + Typ=2 osoba per Marti screenshot)
--      * "Akce" — 6 rows (Centrála 1479 mělo 6 Akce per screenshot)
--    - Footer: prázdný (Storno/OK přijde v 5-F)
-- 6. Pokud render OK → foundation drží, pokračujeme 5-B (GroupBox Kontakt + fields)
-- 7. Pokud render fail → diagnose v fw.diag_log per Marti's pattern
--
-- ALTERNATIVA dvojklik test (existing erp_grid_actions infrastructure):
--   Marti dvojklik na Kontakty grid row (např. ID=1479) → backend
--   page-spec fetch → DesignFwForm.open(63, {master_id: 1479}). Funguje
--   pokud erp_grid_actions FW_EDIT_FORM_REGISTRY{crm_kontakty: 63} je
--   already registered (orchestrator vytvor_edit_jadro to mohl udělat).
--   Pokud ne → DevTools manuál, Krok 5-H wire-up later.
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne — NE-mazat core 63, jen comp_def):
-- ============================================================
-- BEGIN;
-- DELETE FROM fw.comp_def WHERE name IN (
--     'form_crm_kontakt_edit',
--     'grid_crm_kontakt_osoby_detail',
--     'grid_crm_kontakt_akce_detail'
-- );
-- -- Optional: revert UPDATE fw.core 63 zpět na NULL code
-- UPDATE fw.core SET code = NULL, label = 'Editace: Kontakty'
-- WHERE id = 63;
-- COMMIT;
-- POZN: Core 63 NE-mazat — Marti's orchestrator + 3 ops by orphan.
-- ============================================================
