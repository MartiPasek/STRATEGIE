-- Diag query před self-edit skriptem.
-- Marti spustí, pošle výstup, pak finální skript.

-- 1. comp_type IDs co potřebujeme (form, pagecontrol, tabsheet, panel/groupbox, edit, memo, checkbox, dropdown)
SELECT id, code, label, status
FROM fw.comp_type
WHERE status = 'active'
  AND code IN (
    'form', 'pagecontrol', 'tabsheet', 'panel', 'groupbox',
    'edit', 'edit_modern', 'memo', 'checkbox_modern', 'dropdown', 'lookup', 'combobox',
    'date_modern', 'number'
  )
ORDER BY id;

-- 2. Existing comp_def pro core 49 (struktura formu)
SELECT
  id, parent_comp_def_id, parent_core_id, type_id,
  name, caption, sort_order, is_active,
  layout->>'column_name' AS column_name
FROM fw.comp_def
WHERE core_id = 49
ORDER BY parent_comp_def_id NULLS FIRST, sort_order, id;

-- 3. fw.core sloupce (informace co máme o core)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'core'
ORDER BY ordinal_position;
