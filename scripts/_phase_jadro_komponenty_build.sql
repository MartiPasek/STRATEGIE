-- Etapa 1: Jádro „Komponenty" (grid nad fw.comp_def) pod Framework (parent_id=42).
-- Cíl: launcher target pro tab „Komponenty" v Core setting (core 49) + reusable list view.
--
-- Schema notes (z 30.5.2026 diag):
--   - fw.menu_node: status='active', visibility_scope='tenant_member', is_immutable=false
--   - fw.core: drafted-tolerant (code/label nullable), audit created_by_id/_text
--   - fw.data_source: audit created_by/updated_by (integer, NE _id/_text), guid uuid required, name (NE label)
--   - fw.data_set: audit created_by/updated_by (integer), db_connection_id NOT NULL
--   - fw.data_source_op: is_default (NE is_active), data_set_id nullable (Krok 5.S Fáze 5 NO_DATA_SET_KINDS)
--   - fw.comp_def: core_id NOT NULL, root smallint flag (1=root), audit _id/_text full
--   - PG db_connection: id=1 ('strategie_pg', db_type='postgres')

BEGIN;

DO $$
DECLARE
  -- comp_type lookups (status-agnostic — Marti's „máme to" z Core setting build)
  v_grid_modern_type INT;
  v_grid_column_type INT;

  -- Anchors
  v_framework_parent_id INT := 42;
  v_db_connection_id INT := 1;     -- strategie_pg (PostgreSQL)
  v_tenant_id INT := 1;            -- STRATEGIE
  v_marti_user_id INT := 1;        -- Marti

  -- Inserted IDs
  v_menu_node_id INT;
  v_core_id INT;
  v_data_source_id INT;
  v_data_set_id INT;
  v_data_source_op_id INT;
  v_comp_def_root_id INT;
BEGIN
  -- ─── 1. Lookups comp_type (status-agnostic) ──────────────────────────
  SELECT id INTO v_grid_modern_type FROM fw.comp_type WHERE code = 'grid_modern' LIMIT 1;
  IF v_grid_modern_type IS NULL THEN
    RAISE EXCEPTION 'comp_type grid_modern NENALEZEN.';
  END IF;

  SELECT id INTO v_grid_column_type FROM fw.comp_type WHERE code = 'grid_column' LIMIT 1;
  IF v_grid_column_type IS NULL THEN
    RAISE EXCEPTION 'comp_type grid_column NENALEZEN.';
  END IF;

  RAISE NOTICE 'Type IDs — grid_modern=%, grid_column=%', v_grid_modern_type, v_grid_column_type;

  -- ─── 2. menu_node pod Framework ──────────────────────────────────────
  INSERT INTO fw.menu_node (
    parent_id, label, sort_order, status, visibility_scope, is_immutable,
    description_user, description_system,
    created_by_id, created_by_text, updated_by_id, updated_by_text
  ) VALUES (
    v_framework_parent_id, 'Komponenty', 70, 'active', 'tenant_member', false,
    'Přehled všech fw komponent napříč jádry. Filtrovatelný per core_id.',
    'Grid nad fw.comp_def s lookup na fw.comp_type pro label sloupce „Typ". launcher target pro Core setting tab „Komponenty".',
    v_marti_user_id, 'Marti', v_marti_user_id, 'Marti'
  ) RETURNING id INTO v_menu_node_id;
  RAISE NOTICE 'menu_node id=%', v_menu_node_id;

  -- ─── 3. core (kontejner) ─────────────────────────────────────────────
  INSERT INTO fw.core (
    code, label, description_user, is_active, tenant_visibility, version,
    created_by_id, created_by_text, updated_by_id, updated_by_text
  ) VALUES (
    'framework_comp_def_overview', 'Komponenty',
    'Listing fw.comp_def — všechny komponenty napříč jádry. Filter per core_id.',
    true, 'all', 1,
    v_marti_user_id, 'Marti', v_marti_user_id, 'Marti'
  ) RETURNING id INTO v_core_id;
  RAISE NOTICE 'core id=%', v_core_id;

  -- ─── 4. Propojení menu_node → core ───────────────────────────────────
  UPDATE fw.menu_node SET core_id = v_core_id WHERE id = v_menu_node_id;

  -- ─── 5. data_set (SELECT SQL with :filter_core_id parameter) ─────────
  INSERT INTO fw.data_set (
    code, version, description, sql_text, parameters,
    tenant_id, is_system, is_immutable, status,
    db_connection_id, created_by, updated_by
  ) VALUES (
    'framework_comp_def_select', 1,
    'SELECT komponenty s lookup na comp_type label, optional filter per core_id.',
    $sql$SELECT
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
WHERE (CAST(:filter_core_id AS int) IS NULL OR cd.core_id = :filter_core_id)
ORDER BY cd.core_id, cd.sort_order NULLS LAST, cd.id$sql$,
    '{"filter_core_id": null}'::jsonb,
    v_tenant_id, false, false, 'active',
    v_db_connection_id, v_marti_user_id, v_marti_user_id
  ) RETURNING id INTO v_data_set_id;
  RAISE NOTICE 'data_set id=%', v_data_set_id;

  -- ─── 6. data_source ──────────────────────────────────────────────────
  INSERT INTO fw.data_source (
    code, version, name, description, refresh_type,
    row_memory, filter_delay_ms, default_record_limit,
    is_system, is_immutable, status,
    guid, tenant_id,
    created_by, updated_by
  ) VALUES (
    'framework_comp_def_overview', 1, 'Komponenty (přehled)',
    'Uniform listing fw.comp_def s lookup na comp_type. Filter per core_id.',
    'manual', false, 300, 200,
    false, false, 'active',
    gen_random_uuid(), v_tenant_id,
    v_marti_user_id, v_marti_user_id
  ) RETURNING id INTO v_data_source_id;
  RAISE NOTICE 'data_source id=%', v_data_source_id;

  -- ─── 7. data_source_op (select kind, is_default=true) ────────────────
  INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind, sort_order, is_default,
    description
  ) VALUES (
    v_data_source_id, v_data_set_id, 'select', 0, true,
    'Default SELECT operace pro listing s lookup na comp_type.'
  ) RETURNING id INTO v_data_source_op_id;
  RAISE NOTICE 'data_source_op id=%', v_data_source_op_id;

  -- ─── 8. comp_def root (grid_modern, root=1) ──────────────────────────
  INSERT INTO fw.comp_def (
    core_id, parent_comp_def_id, type_id, name, caption,
    data_source_id, sort_order, is_active, root,
    layout, created_by_text, updated_by_text
  ) VALUES (
    v_core_id, NULL, v_grid_modern_type, 'grid_root', 'Komponenty',
    v_data_source_id, 0, true, 1,
    '{}'::jsonb,
    'Marti', 'Marti'
  ) RETURNING id INTO v_comp_def_root_id;
  RAISE NOTICE 'comp_def root id=%', v_comp_def_root_id;

  -- ─── 9. grid columns (~14 sloupců s layout.column_name mapping) ──────
  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, layout, created_by_text, updated_by_text)
  VALUES
    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_id', 'ID',
     10, true,
     jsonb_build_object('column_name', 'id', 'width', 70, 'type', 'number', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_core_id', 'Core',
     20, true,
     jsonb_build_object('column_name', 'core_id', 'width', 70, 'type', 'number', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_parent', 'Parent',
     30, true,
     jsonb_build_object('column_name', 'parent_comp_def_id', 'width', 80, 'type', 'number', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_root', 'Root',
     40, true,
     jsonb_build_object('column_name', 'root', 'width', 60, 'type', 'number', 'sortable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_type_label', 'Typ',
     50, true,
     jsonb_build_object('column_name', 'type_label', 'width', 140, 'type', 'text', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_name', 'Název',
     60, true,
     jsonb_build_object('column_name', 'name', 'width', 200, 'type', 'text', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_caption', 'Caption',
     70, true,
     jsonb_build_object('column_name', 'caption', 'width', 220, 'type', 'text', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_sort_order', 'Poradí',
     80, true,
     jsonb_build_object('column_name', 'sort_order', 'width', 80, 'type', 'number', 'sortable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_is_active', 'Aktivní',
     90, true,
     jsonb_build_object('column_name', 'is_active', 'width', 80, 'type', 'boolean', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_data_source', 'Data Source',
     100, true,
     jsonb_build_object('column_name', 'data_source_id', 'width', 100, 'type', 'number', 'sortable', true, 'filterable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_layout_mode', 'Layout',
     110, true,
     jsonb_build_object('column_name', 'layout_mode', 'width', 110, 'type', 'text', 'sortable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_updated_at', 'Upraveno',
     120, true,
     jsonb_build_object('column_name', 'updated_at', 'width', 160, 'type', 'datetime', 'sortable', true),
     'Marti', 'Marti'),

    (v_core_id, v_comp_def_root_id, v_grid_column_type, 'col_updated_by', 'Upravil',
     130, true,
     jsonb_build_object('column_name', 'updated_by_text', 'width', 130, 'type', 'text', 'sortable', true, 'filterable', true),
     'Marti', 'Marti');

  RAISE NOTICE '14 grid columns vytvořeno pod comp_def root #%', v_comp_def_root_id;

  RAISE NOTICE '====================================================';
  RAISE NOTICE 'DONE. Hard reload (Ctrl+Shift+R) → levý strom Framework → Komponenty';
  RAISE NOTICE 'Mělo by se zobrazit grid se VŠEMI fw.comp_def řádky.';
  RAISE NOTICE 'Filter pre-fill ?filter_core_id=49 → jen komponenty core 49.';
  RAISE NOTICE '====================================================';
END $$;

COMMIT;
