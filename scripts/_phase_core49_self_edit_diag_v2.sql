-- Diag v2 — fix parent_core_id (neexistuje) + plný comp_type list

-- 1. VŠECHNY comp_type s 'active' status
SELECT id, code, label, status
FROM fw.comp_type
WHERE status = 'active'
ORDER BY id;

-- 2. comp_def schema (které sloupce existují)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'comp_def'
ORDER BY ordinal_position;

-- 3. Existing comp_def pro core 49
SELECT
  id, parent_comp_def_id, type_id,
  name, caption, sort_order, is_active,
  layout->>'column_name' AS column_name
FROM fw.comp_def
WHERE core_id = 49
ORDER BY parent_comp_def_id NULLS FIRST, sort_order, id;

-- 4. fw.core schema (info co máme o core)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'core'
ORDER BY ordinal_position;
