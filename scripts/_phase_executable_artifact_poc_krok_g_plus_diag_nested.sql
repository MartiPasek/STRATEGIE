-- ============================================================================
-- Krok G+ DIAGNOSTIC — nested detail grid (Data Sources → Operace data sourcu)
-- ============================================================================
-- Marti's Q1: "Je mozne, ze nested grid chodi i bez kontejneru (bez core).
--              Musime to overit."
-- Marti's Q2: Pokud nested NEMA vlastni fw.core → chceme to napravit.
-- Marti's Q3: CRUD aktivace by mela byt automaticka pokud nested ma fw.core
--              + ops kind edit/insert.
--
-- Tento skript ZNATELNE diagnostikuje stav DB. Marti spusti v DBeaveru,
-- posli mi vystup (copy-paste), pak se rozhodneme strategy.
--
-- Marti spusti v DBeaveru jako Marti-AI session.
-- ============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1: Existuje fw.core pro 'framework_data_source_ops' (= nested grid)?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
  '=== Q1: fw.core pro nested ===' AS check_section;

SELECT
  id,
  code,
  label,
  description_user,
  is_active,
  created_at
FROM fw.core
WHERE code ILIKE '%framework_data_source_op%'
   OR code ILIKE '%data_source_op%'
   OR label ILIKE '%operace data sourc%'
   OR label ILIKE '%data source op%'
ORDER BY id;
-- Expected: zadne rows = nested NEMA vlastni fw.core (Scenario B)
-- Pokud rows = nested MA vlastni fw.core (Scenario A) → pisem misto toho fix
-- drop-up menu wire-up

-- ─────────────────────────────────────────────────────────────────────────────
-- Q2: Komponenty (comp_def) s data_source_id=44 (Framework: Data Source Operations)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
  '=== Q2: comp_def pro nested data_source ===' AS check_section;

SELECT
  id,
  core_id,
  name,
  caption,
  data_source_id,
  type_id,
  parent_comp_def_id,
  region_slot,
  is_active
FROM fw.comp_def
WHERE data_source_id = 44
   OR name ILIKE '%framework_data_source_op%'
ORDER BY id;
-- Expected: vidime ktery core_id se k tomu vaze (pokud vubec)

-- ─────────────────────────────────────────────────────────────────────────────
-- Q3: Existing ops pro data_source #44 (Framework: Data Source Operations)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
  '=== Q3: data_source_op pro #44 ===' AS check_section;

SELECT
  id,
  operation_kind,
  variant_code,
  core_id,
  data_set_id,
  description
FROM fw.data_source_op
WHERE data_source_id = 44
ORDER BY operation_kind, id;
-- Expected: minimalne select op pro fetch detail rows

-- ─────────────────────────────────────────────────────────────────────────────
-- Q4: Jak je nested wire-uped v master? (data_source #39 = Diag log)
--     Hleda se comp_def, kde layout obsahuje master-detail config
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
  '=== Q4: master-detail wire-up v Diag log? ===' AS check_section;

SELECT
  cd.id,
  cd.core_id,
  cd.name,
  cd.caption,
  cd.data_source_id,
  cd.type_id,
  ct.code AS type_code,
  -- Hleda master-detail v layout JSONB
  cd.layout->>'master_detail' AS layout_master_detail,
  cd.layout->>'detail_data_source_id' AS detail_ds_id,
  cd.layout AS layout_full
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON cd.type_id = ct.id
WHERE cd.data_source_id IN (35, 39)  -- Diag log + STRATEGIE Users data sources
ORDER BY cd.id;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q5: Souhrn — fw.data_source #44 vs #39 vs #35
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
  '=== Q5: data_source summary ===' AS check_section;

SELECT
  ds.id,
  ds.code,
  ds.name,
  ds.status,
  ds.is_system,
  (
    SELECT COUNT(*) FROM fw.data_source_op op
    WHERE op.data_source_id = ds.id
  ) AS ops_count,
  (
    SELECT STRING_AGG(op.operation_kind, ', ' ORDER BY op.operation_kind)
    FROM fw.data_source_op op
    WHERE op.data_source_id = ds.id
  ) AS ops_kinds,
  (
    SELECT COUNT(*) FROM fw.comp_def cd
    WHERE cd.data_source_id = ds.id
  ) AS comp_defs_count
FROM fw.data_source ds
WHERE ds.id IN (35, 39, 44)
ORDER BY ds.id;
