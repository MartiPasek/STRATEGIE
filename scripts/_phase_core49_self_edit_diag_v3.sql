-- Diag v3 — komp_type schema + lookup existujících pagecontrol/tabsheet

-- 1. comp_type schema (NOT NULL sloupce pro INSERT)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'comp_type'
ORDER BY ordinal_position;

-- 2. comp_type — pagecontrol + tabsheet BEZ status filtru
SELECT id, code, label, status
FROM fw.comp_type
WHERE code IN ('pagecontrol', 'tabsheet', 'page_control', 'tab_sheet', 'tab')
   OR id IN (14, 15, 16, 17, 18);

-- 3. Existing comp_def pro core 49 (znovu pro doplnění layout JSONB plně)
SELECT
  id, parent_comp_def_id, type_id, name, caption, sort_order, is_active,
  layout
FROM fw.comp_def
WHERE core_id = 49
ORDER BY id;
