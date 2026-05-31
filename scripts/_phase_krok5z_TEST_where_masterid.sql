-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z TEST (Marti 30.5.) — framework_comp_def_select WHERE core_id=:master_id
-- ════════════════════════════════════════════════════════════════════════
-- Overit ze embedded grid filtruje na editovany core (68 -> 5 komponent).
-- Nastavi data_set (WHERE cd.core_id = :master_id) I layout (filter_field=
-- master_id) na STEJNY param, at to sedi s frontendem.
--
-- BIND-PROOF: ':master_id' stavene pres chr(58) -> DBeaver se nezepta.
--
-- ⚠ DOCASNE rozbije Prehled Komponent (core 73) -> 0 radku (master_id=NULL).
--    To je OK pro tento test. Po potvrzeni vratime cistou architekturu:
--    _phase_krok5z_fix_dataset_filter.sql (Prehled zpet) + detail_dataset.sql.
--
-- !!! PO SPUSTENI COMMITNI (zelena fajfka) — jinak to API neuvidi !!!
-- Restart netreba, jen Ctrl+Shift+R v ERP.
-- ════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
  c text := chr(58);   -- ':'
BEGIN
  -- 1. data_set -> simple WHERE cd.core_id = :master_id
  UPDATE fw.data_set SET sql_text =
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
WHERE cd.core_id = ' || c || 'master_id
ORDER BY cd.core_id, cd.sort_order NULLS LAST, cd.id'
  WHERE code = 'framework_comp_def_select';

  -- 2. layout -> param master_id (filter_source resolve na editovany core).
  --    (layout - 'kind') odebere pripadny stale kind -> frontend posle default
  --    select op (NE select-detail), at to mire na framework_comp_def_select.
  UPDATE fw.comp_def
  SET layout = (layout - 'kind') || jsonb_build_object(
        'filter_field', 'master_id',
        'filter_source', c || 'master_id'
      )
  WHERE core_id = 49 AND name = 'embedded_komponenty';

  RAISE NOTICE 'TEST aktivni: framework_comp_def_select WHERE cd.core_id = :master_id, layout filter_field=master_id.';
END $$;

-- Over po commitu:
-- SELECT right(sql_text, 60) FROM fw.data_set WHERE code='framework_comp_def_select';
-- SELECT layout FROM fw.comp_def WHERE core_id=49 AND name='embedded_komponenty';
