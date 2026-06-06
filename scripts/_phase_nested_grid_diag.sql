-- Diag pro Etapu 2: nested_grid comp_type INSERT prep
-- Cíl: max(id) + max(create_order) pro nový INSERT (Marti's „ID je svatý, poradí create zachovej")
--      + check, zda 'nested_grid' nebo podobný code už neexistuje

-- 1. schema fw.comp_type (column types pro INSERT)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='comp_type'
ORDER BY ordinal_position;

-- 2. check existing nested_grid / embedded_grid / sub_grid
SELECT id, code, label, kind, status, create_order
FROM fw.comp_type
WHERE code IN ('nested_grid', 'embedded_grid', 'sub_grid', 'subgrid', 'inner_grid')
ORDER BY id;

-- 3. MAX(id) + MAX(create_order) pro Marti's 19yr doctrine
SELECT
  MAX(id) AS max_id,
  MAX(create_order) AS max_create_order,
  COUNT(*) AS total_types
FROM fw.comp_type;

-- 4. Existující container types (panel, groupbox, pagecontrol, tabsheet) pro reference
SELECT id, code, label, kind, status, create_order
FROM fw.comp_type
WHERE code IN ('panel', 'groupbox', 'pagecontrol', 'tabsheet', 'grid_modern')
ORDER BY create_order, id;
