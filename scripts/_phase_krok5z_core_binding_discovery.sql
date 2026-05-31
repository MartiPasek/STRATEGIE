-- ============================================================================
-- Krok 5.Z (31.5.2026) — Discovery: kde se nested grid chytí na master core
-- ============================================================================
-- Marti: "Master-detail funguje autonomne bez core_id (spravne). Pojd udelat
-- select, ze ktereho uvidime kde se chytit na nase core id — kde je, nebo
-- naopak schazi patricna vazba."
--
-- Nested gridy: 372 (osoby→ds53), 373 (akce→ds52). Form core 72.
-- Master prehledy: crm_kontakt_akce (grid root na ds52), crm_kontakt_osoby
-- (grid root na ds53). Vytvořené předchozím scriptem.
--
-- READ-ONLY. Spusti Marti v DBeaveru.
-- ============================================================================

-- ── 1) NESTED GRID ↔ MASTER CORE přes sdílený data_source ───────────────────
-- Přirozená spojka = data_source_id. Nested grid i master grid root ukazují na
-- TÝŽ data_source. Ukáže: která master core sdílí ds s nested gridem + jaké
-- explicitní pointery na gridu jsou (teď prázdné = schází vazba).
SELECT
    ng.id               AS nested_grid_id,
    ng.name             AS nested_grid,
    ng.core_id          AS form_core,            -- 72 (trigger-locked)
    ng.data_source_id   AS ds_id,                -- SPOJKA 52/53
    ng.layout->>'data_source_code' AS ds_code,
    ng.layout->>'grid_core_id'     AS lay_grid_core_id,   -- NULL = schází
    ng.layout->>'edit_core_id'     AS lay_edit_core_id,   -- NULL = schází
    '→'                 AS spojka,
    mroot.id            AS master_grid_root_id,
    mroot.core_id       AS master_core_id,       -- KAM se chytit
    mc.code             AS master_core_code,
    mc.label            AS master_core_label
FROM fw.comp_def ng
LEFT JOIN fw.comp_def mroot
       ON mroot.data_source_id = ng.data_source_id
      AND mroot.parent_comp_def_id IS NULL
      AND mroot.is_active = true
LEFT JOIN fw.core mc ON mc.id = mroot.core_id
WHERE ng.id IN (372, 373)
ORDER BY ng.id;

-- ── 2) DATA_SOURCE_OP landscape pro 52/53 — kde sedí core na úrovni op ───────
-- Ukáže select (master) vs select-detail (nested) + jestli op nese core_id
-- (op_core_id) — to je alternativní místo, kam vazbu uložit.
SELECT
    op.data_source_id   AS ds_id,
    op.id               AS op_id,
    op.operation_kind,
    op.variant_code,
    op.is_default,
    op.core_id          AS op_core_id,           -- NULL? = tady vazba není
    op.data_set_id,
    dset.code           AS data_set_code
FROM fw.data_source_op op
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE op.data_source_id IN (52, 53)
ORDER BY op.data_source_id, op.operation_kind;

-- ── 3) MASTER CORE chain — co všechno na nové core visí ──────────────────────
SELECT
    c.id                AS master_core_id,
    c.code,
    c.label,
    mn.id               AS menu_node_id,
    cd.id               AS grid_root_id,
    cd.data_source_id   AS grid_ds_id,
    (SELECT string_agg(operation_kind, ', ' ORDER BY operation_kind)
       FROM fw.data_source_op WHERE data_source_id = cd.data_source_id) AS ds_ops
FROM fw.core c
LEFT JOIN fw.menu_node mn ON mn.core_id = c.id
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.parent_comp_def_id IS NULL
WHERE c.code IN ('crm_kontakt_akce', 'crm_kontakt_osoby')
ORDER BY c.code;

-- ── 4) REFERENCE: ZEMĚ (ID 59) — jak vypadá SPRÁVNĚ provázaný přehled ────────
-- Marti: porovnat správné provázání Země vs co u CRM nested gridů schází.
-- 59 může být menu_node nebo core → nejdřív resolve.
SELECT 'co je ID 59' AS info, 'menu_node' AS typ, id, label, parent_id, core_id
FROM fw.menu_node WHERE id = 59
UNION ALL
SELECT 'co je ID 59', 'core', id, label, NULL, NULL
FROM fw.core WHERE id = 59;

-- 4a) Země — VŠECHNY comp_defy jejího core + binding pointery (grid root + nested)
--     Porovnej s Q1: má Země nested grid? Nese edit_core_id / grid_core_id?
SELECT
    cd.id               AS comp_def_id,
    cd.name,
    cd.core_id,
    cd.parent_comp_def_id,
    ct.code             AS type_code,
    cd.data_source_id,
    cd.layout->>'data_source_code' AS ds_code,
    cd.layout->>'grid_core_id'     AS lay_grid_core_id,
    cd.layout->>'edit_core_id'     AS lay_edit_core_id,
    cd.layout->>'filter_source'    AS filter_source
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE cd.core_id = COALESCE(
        (SELECT core_id FROM fw.menu_node WHERE id = 59),
        (SELECT id FROM fw.core WHERE id = 59)
    )
ORDER BY cd.parent_comp_def_id NULLS FIRST, cd.sort_order, cd.id;

-- 4b) Země — data_source ops (kinds + op_core_id) pro porovnání s Q2
SELECT DISTINCT
    ds.id               AS ds_id,
    ds.code,
    op.operation_kind,
    op.core_id          AS op_core_id,
    op.data_set_id
FROM fw.comp_def cd
JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
WHERE cd.core_id = COALESCE(
        (SELECT core_id FROM fw.menu_node WHERE id = 59),
        (SELECT id FROM fw.core WHERE id = 59)
    )
ORDER BY ds.id, op.operation_kind;

-- ============================================================================
-- Interpretace:
--   Q1: form_core=72 (trigger), lay_grid/edit_core_id=NULL → na gridu žádná
--       explicitní vazba. Ale ds_id == master grid root data_source → SPOJKA
--       JE přes data_source_id. master_core_id = kam se chytit.
--   Q2: op_core_id NULL → vazba není ani na op úrovni.
--   Q3: master core má menu_node + grid root + ds s ops (select + select-detail).
--   Q4 (ZEMĚ reference): jak je SPRÁVNĚ provázaný funkční přehled. Porovnej
--       4a (binding pointery, nested grid?) + 4b (op kinds + op_core_id) s Q1/Q2.
--       To ukáže, jakou vazbu Země má a naše CRM gridy zatím ne.
--
-- Závěr (k rozhodnutí): nested grid → master core lze odvodit RUNTIME přes
-- shared data_source_id (žádná nová data, žádný trigger). Alternativa: uložit
-- explicit (op_core_id NEBO layout pointer). Q1-Q4 ukáže, co dává smysl podle
-- toho, jak to má provázané Země.
-- ============================================================================
