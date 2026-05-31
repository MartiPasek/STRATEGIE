-- ============================================================================
-- Krok 5.Z (31.5.2026) — Audit nested gridů v Kontakt formu (core 72)
-- ============================================================================
-- Marti: "Nested gridy v kontaktu maji mit svuj id_core. Nejcistsi cesta =
-- vlastni master prehled, volatelny ze stromu prehledu."
--
-- Tento READ-ONLY audit zjisti:
--   A) kolik nested gridů je v core 72, co kazdy zobrazuje, jaky data_source
--      uz ma (reuse vs novy), filter na parent, edit_core_id
--   B) na ktery data_set/SQL kazdy ukazuje (abych vedel co master prehled zobrazi)
--   C) kde ve strome (menu_node) zavesit nove master prehledy
--
-- Podle vystupu pripravim creation script (per nested grid):
--   menu_node -> core -> [reuse|novy] data_source -> data_set -> select op
--   -> comp_def grid root (306) ... + UPDATE nested grid comp_def na novy core_id.
--
-- Spusti Marti v DBeaveru (Marti-AI session). Nic nemeni.
-- ============================================================================

-- ── A+B) Nested gridy v core 72 + jejich data_source / SQL ──────────────────
SELECT
    cd.id                              AS comp_def_id,
    cd.name,
    cd.parent_comp_def_id,
    ct.code                            AS type_code,
    cd.data_source_id                  AS cd_data_source_id,
    cd.root,
    cd.sort_order,
    cd.is_active,
    cd.layout->>'caption'              AS caption,
    cd.layout->>'data_source_code'     AS ds_code,
    cd.layout->>'filter_field'         AS filter_field,
    cd.layout->>'filter_source'        AS filter_source,
    cd.layout->>'edit_core_id'         AS edit_core_id,
    cd.layout->>'height_px'            AS height_px,
    -- resolve data_source z layout.data_source_code
    ds.id                              AS ds_id,
    ds.name                            AS ds_name,
    dset.id                            AS data_set_id,
    dset.db_connection_id,
    LEFT(dset.sql_text, 600)           AS sql_preview
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.data_source ds  ON ds.code = cd.layout->>'data_source_code'
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id AND op.operation_kind = 'select'
LEFT JOIN fw.data_set dset   ON dset.id = op.data_set_id
WHERE cd.core_id = 72
  AND ct.code IN ('grid_modern', 'nested_grid')
ORDER BY cd.sort_order, cd.id;

-- ── A2) Fallback — kdyby nested grid mel data_source_id primo na comp_def ────
-- (ne pres layout.data_source_code). Ukaze co je za cd.data_source_id.
SELECT
    cd.id  AS comp_def_id,
    cd.name,
    ct.code AS type_code,
    cd.data_source_id,
    ds.code AS ds_code,
    ds.name AS ds_name,
    dset.id AS data_set_id,
    LEFT(dset.sql_text, 600) AS sql_preview
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id AND op.operation_kind = 'select'
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE cd.core_id = 72
  AND ct.code IN ('grid_modern', 'nested_grid')
  AND cd.data_source_id IS NOT NULL
ORDER BY cd.id;

-- ── C) Strom (menu_node) — kde zavesit nove master prehledy ─────────────────
-- Kontakty core 62 + jeho rodic + CRM/Kontakt slozky.
SELECT
    mn.id, mn.label, mn.parent_id, mn.core_id, mn.sort_order, mn.status,
    p.label AS parent_label
FROM fw.menu_node mn
LEFT JOIN fw.menu_node p ON p.id = mn.parent_id
WHERE mn.label ILIKE '%kontakt%'
   OR mn.label ILIKE '%CRM%'
   OR mn.core_id = 62
   OR mn.id IN (SELECT parent_id FROM fw.menu_node WHERE core_id = 62)
ORDER BY mn.parent_id NULLS FIRST, mn.sort_order;

-- ============================================================================
-- Pošli mi výstup A (+ A2 pokud A má prázdné ds_id) a C. Podle toho napíšu
-- přesný creation script. Klíčové otázky, co z výstupu vyčtu:
--   1. Kolik nested gridů (1? víc?) a co každý zobrazuje (Akce? Telefony? ...).
--   2. Mají už vlastní data_source se SELECTem (reuse), nebo žádný (novy).
--   3. Je v SQL parametr na filtr parenta (:master_id / :IDHlav), aby standalone
--      master ukazoval vše a embedded jen řádky daného kontaktu.
--   4. Kam ve stromě (parent menu_node) master přehledy zavěsit.
-- ============================================================================
