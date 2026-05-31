-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z DIAG (Marti 30.5.) — zadny WHERE, LIMIT 4. Overit ze grid hita
-- TENTO data_set (framework_comp_def_select) a ze se UPDATE vubec aplikuje.
-- ════════════════════════════════════════════════════════════════════════
-- Zadne ':' -> zadny DBeaver bind dialog. Prosty UPDATE (ne DO blok).
--
-- POSTUP:
--   1. Spust tento UPDATE (Ctrl+Enter na tom radku, nebo Alt+X cely soubor).
--   2. !!! COMMIT !!! Pokud ma tvuj DBeaver auto-commit OFF, musis rucne
--      commitnout (zelena fajfka / Ctrl+Shift+Enter), jinak to API neuvidi.
--   3. ZADNY restart netreba (runner cte data_set cerstve kazde volani).
--   4. V ERP Ctrl+Shift+R -> Core setting -> Vazby.
--
-- VYSLEDEK:
--   - Grid ukaze PRESNE 4 radky -> jsme na spravnem data_setu + UPDATE
--     se aplikuje. Problem byl jen WHERE/:param. Pokracujeme spravnou opravou.
--   - Grid ukaze 294 / error / 0 -> UPDATE se NEaplikuje (commit?) NEBO grid
--     cte jiny data_set. Pak resime to.
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.data_set
SET sql_text =
'SELECT
  cd.id,
  cd.core_id,
  cd.parent_comp_def_id,
  cd.type_id,
  ct.code AS type_code,
  COALESCE(ct.label, ct.code) AS type_label,
  cd.name,
  cd.caption,
  cd.sort_order,
  cd.is_active,
  cd.root,
  cd.data_source_id,
  cd.layout_mode,
  cd.region_slot,
  cd.created_at,
  cd.updated_at,
  cd.created_by_text,
  cd.updated_by_text
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
ORDER BY cd.core_id, cd.sort_order NULLS LAST, cd.id
LIMIT 4'
WHERE code = 'framework_comp_def_select';

-- Po behu over (cti zpet co je realne ulozeno):
-- SELECT id, code, right(sql_text, 40) AS konec FROM fw.data_set WHERE code='framework_comp_def_select';
