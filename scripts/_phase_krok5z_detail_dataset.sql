-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — detail data_set pro embedded grid (BIND-PROOF, bez : dialogu)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "Do toho selectu patri jen jednoduse WHERE cd.core_id = 68,
-- kde 68 nahradis promenou ve formulari." + "datasource/dataset na core detailu."
--
-- ARCHITEKTURA (master-detail konvence, jako data_source_op_detail.js):
--   - framework_comp_def_select (existing) = PREHLED Komponenty (core 73)
--   - framework_comp_def_detail (NEW)      = DETAIL (embedded grid core 49 Vazby):
--       simple "WHERE cd.core_id = :master_id"
--   - novy data_source_op kind='select-detail' na framework_comp_def_overview
--   - embedded grid fetchuje ?master_id=X&kind=select-detail
--
-- BIND-PROOF: vsechny ':master_id' stavime pres chr(58) (=dvojtecka), takze
-- DBeaver nevidi ':master_id' literalne a NEZEPTA se (gotcha #111 obejito).
-- ════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
  c text := chr(58);   -- ':'
  v_data_source_id INT;
  v_tenant_id INT;
  v_db_conn_id INT;
  v_created_by INT;
  v_detail_data_set_id INT;
  v_existing_ds INT;
  v_existing_op INT;
  v_detail_sql text;
BEGIN
  -- 1. Existing data_source + tenant
  SELECT id, tenant_id INTO v_data_source_id, v_tenant_id
  FROM fw.data_source WHERE code = 'framework_comp_def_overview' LIMIT 1;
  IF v_data_source_id IS NULL THEN
    RAISE EXCEPTION 'data_source framework_comp_def_overview NENALEZEN. Spustil jsi _phase_jadro_komponenty_build.sql?';
  END IF;

  -- 2. Reuse db_connection + created_by z existujiciho select data_setu
  SELECT db_connection_id, created_by INTO v_db_conn_id, v_created_by
  FROM fw.data_set WHERE code = 'framework_comp_def_select' LIMIT 1;

  -- 3. Detail data_set sql_text (simple :master_id filter, stavene pres chr(58))
  v_detail_sql :=
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
ORDER BY cd.core_id, cd.sort_order NULLS LAST, cd.id';

  -- 4. Insert/reuse detail data_set (idempotentni)
  SELECT id INTO v_existing_ds FROM fw.data_set WHERE code = 'framework_comp_def_detail' LIMIT 1;
  IF v_existing_ds IS NOT NULL THEN
    v_detail_data_set_id := v_existing_ds;
    UPDATE fw.data_set SET sql_text = v_detail_sql WHERE id = v_existing_ds;
    RAISE NOTICE 'data_set framework_comp_def_detail uz existuje (id=%) — sql_text refreshed.', v_existing_ds;
  ELSE
    INSERT INTO fw.data_set (
      code, version, description, sql_text, parameters,
      tenant_id, is_system, is_immutable, status,
      db_connection_id, created_by, updated_by
    ) VALUES (
      'framework_comp_def_detail', 1,
      'Komponenty EDITOVANEHO core (embedded grid v Core setting Vazby). Simple master_id filter (master-detail konvence).',
      v_detail_sql,
      ('{"master_id": null}')::jsonb,
      v_tenant_id, false, false, 'active',
      v_db_conn_id, v_created_by, v_created_by
    ) RETURNING id INTO v_detail_data_set_id;
    RAISE NOTICE 'data_set framework_comp_def_detail id=%', v_detail_data_set_id;
  END IF;

  -- 5. data_source_op kind='select-detail' (idempotentni)
  SELECT id INTO v_existing_op FROM fw.data_source_op
  WHERE data_source_id = v_data_source_id AND operation_kind = 'select-detail' LIMIT 1;
  IF v_existing_op IS NOT NULL THEN
    UPDATE fw.data_source_op SET data_set_id = v_detail_data_set_id WHERE id = v_existing_op;
    RAISE NOTICE 'select-detail op uz existuje (id=%) — data_set_id refreshed.', v_existing_op;
  ELSE
    INSERT INTO fw.data_source_op (
      data_source_id, data_set_id, operation_kind, sort_order, is_default, description
    ) VALUES (
      v_data_source_id, v_detail_data_set_id, 'select-detail', 1, false,
      'Per-master detail (embedded grid) — komponenty editovaneho core.'
    );
    RAISE NOTICE 'data_source_op select-detail vlozen na data_source #%.', v_data_source_id;
  END IF;

  -- 6. Prepni embedded_komponenty layout na master-detail konvenci
  --    (filter_source ':master_id' stavene pres chr(58))
  UPDATE fw.comp_def
  SET layout = layout
        || jsonb_build_object(
             'filter_field', 'master_id',
             'filter_source', c || 'master_id',
             'kind', 'select-detail'
           )
  WHERE core_id = 49 AND name = 'embedded_komponenty';
  RAISE NOTICE 'embedded_komponenty layout -> master_id + kind=select-detail.';
END $$;

-- ── Verify (spust po behu) ───────────────────────────────────────────────
-- SELECT operation_kind, data_set_id FROM fw.data_source_op
--   WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code='framework_comp_def_overview');
-- SELECT sql_text FROM fw.data_set WHERE code='framework_comp_def_detail';
-- SELECT layout FROM fw.comp_def WHERE core_id=49 AND name='embedded_komponenty';
