-- Diag: ověřit, zda jádro Komponenty + menu_node byly INSERTed z předchozího běhu
-- a proč „Komponenty" nesvítí v levém stromu Framework.

-- 1. menu_node „Komponenty"
SELECT id, label, parent_id, status, visibility_scope, is_immutable, core_id, sort_order
FROM fw.menu_node
WHERE label = 'Komponenty';

-- 2. fw.core
SELECT id, code, label, is_active, tenant_visibility, version
FROM fw.core
WHERE code = 'framework_comp_def_overview';

-- 3. Connection menu_node ↔ core (LEFT JOIN check)
SELECT mn.id AS menu_node_id, mn.label, mn.parent_id, mn.status, mn.core_id,
       c.id AS core_check_id, c.label AS core_label, c.is_active
FROM fw.menu_node mn
LEFT JOIN fw.core c ON c.id = mn.core_id
WHERE mn.label = 'Komponenty';

-- 4. Framework parent + sourozenci (vidíme, kam by se Komponenty zařadily)
SELECT id, label, sort_order, status, core_id
FROM fw.menu_node
WHERE parent_id = 42
ORDER BY sort_order, id;

-- 5. data_source + data_set + op connect ověření
SELECT
  ds.id AS data_source_id, ds.code, ds.status AS ds_status,
  op.id AS op_id, op.operation_kind, op.is_default,
  dset.id AS data_set_id, dset.code AS data_set_code, dset.status AS dset_status,
  dset.db_connection_id
FROM fw.data_source ds
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE ds.code = 'framework_comp_def_overview';

-- 6. comp_def root + columns count
SELECT
  cd.id AS root_id, cd.name, cd.caption, cd.type_id, cd.data_source_id, cd.root,
  (SELECT COUNT(*) FROM fw.comp_def cc WHERE cc.parent_comp_def_id = cd.id) AS column_count
FROM fw.comp_def cd
JOIN fw.core c ON c.id = cd.core_id
WHERE c.code = 'framework_comp_def_overview'
  AND cd.parent_comp_def_id IS NULL;
