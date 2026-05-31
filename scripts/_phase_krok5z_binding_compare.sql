-- ============================================================================
-- Krok 5.Z (31.5.2026) — Binding compare: naše ds 52/53 vs Země ds 48
-- ============================================================================
-- Marti: "3 selecty pod sebou — 1) tri data_sourcy, 2) vsechny jejich OP,
-- 3) comp_def 3 radky k danym gridum."
--
-- ds 48 = Země (REFERENCE, funguje), ds 52 = Akce, ds 53 = Osoby (naše nové).
-- Gridy: 254 = Země grid root (ref), 373 = nested Akce, 372 = nested Osoby.
--
-- KLÍČ: Země má na ds 48 ops 'edit' + 'insert' s op_core_id=68 (edit form core).
-- Naše ds 52/53 mají jen select + select-detail, op_core_id NULL. → schází
-- edit/insert ops s op_core_id na edit form core.
--
-- READ-ONLY. Spusti Marti v DBeaveru.
-- ============================================================================

-- ── 1) TŘI DATA_SOURCE pod sebou ────────────────────────────────────────────
SELECT
    id          AS ds_id,
    code,
    name,
    refresh_type,
    status,
    CASE id WHEN 48 THEN 'ZEMĚ (reference)'
            WHEN 52 THEN 'Akce (naše)'
            WHEN 53 THEN 'Osoby (naše)' END AS role
FROM fw.data_source
WHERE id IN (48, 52, 53)
ORDER BY id;

-- ── 2) VŠECHNY OP těchto tří data_source ────────────────────────────────────
-- Tady uvidíš rozdíl: Země (48) má edit+insert+select, naše (52/53) jen
-- select+select-detail. op_core_id = vazba na jádro (Země 68, naše NULL).
SELECT
    op.data_source_id   AS ds_id,
    op.id               AS op_id,
    op.operation_kind,
    op.variant_code,
    op.is_default,
    op.core_id          AS op_core_id,       -- ← TADY je ta vazba (Země má, my ne)
    op.data_set_id,
    dset.code           AS data_set_code
FROM fw.data_source_op op
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE op.data_source_id IN (48, 52, 53)
ORDER BY op.data_source_id, op.operation_kind;

-- ── 3) COMP_DEF — 3 gridy (Země ref + naše 2 nested) ────────────────────────
SELECT
    cd.id               AS comp_def_id,
    cd.name,
    cd.core_id,
    cd.parent_comp_def_id,
    ct.code             AS type_code,
    cd.data_source_id   AS ds_id,
    cd.layout->>'data_source_code' AS ds_code,
    cd.layout->>'grid_core_id'     AS lay_grid_core_id,
    cd.layout->>'edit_core_id'     AS lay_edit_core_id,
    CASE cd.id WHEN 254 THEN 'ZEMĚ grid root (reference)'
               WHEN 373 THEN 'nested Akce (ve formu 72)'
               WHEN 372 THEN 'nested Osoby (ve formu 72)' END AS role
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE cd.id IN (254, 372, 373)
ORDER BY cd.data_source_id, cd.id;

-- ============================================================================
-- Co z toho vyčteme:
--   Q1: tři data_source vedle sebe (48 ref, 52/53 naše).
--   Q2: Země ds 48 má 'edit' + 'insert' (op_core_id=68) → CRUD vazba na OP.
--       Naše 52/53 mají jen select + select-detail (op_core_id NULL) → CHYBÍ.
--   Q3: Země grid 254 = list_root, vlastní core 59, žádný edit_core_id na gridu
--       (vazba je na OP, ne na gridu!). Naše nested 372/373 = core 72 (form),
--       žádné pointery — autonomní master-detail.
--
-- ZÁVĚR: vazba na jádro pro CRUD = data_source_op.core_id na edit/insert ops.
-- Pro Akce/Osoby doděláme edit + insert op na ds 52/53 s op_core_id na jejich
-- master core (79/80) — nebo na samostatný edit form core. To je další krok.
-- ============================================================================
