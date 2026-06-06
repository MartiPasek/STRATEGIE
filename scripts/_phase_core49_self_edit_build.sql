-- Phase Core 49 self-edit (30.5.2026 ranní): postavit page control s 5 záložkami.
-- Marti's instrukce: "do prvni tej informace, ktery o danem core mas"
--
-- Plán:
--   root #154 (form 302)  ← zachováno
--     └─ main_pagecontrol  (NEW)
--         ├─ tab_zakladni     "Základní"       → panel + 6 info fields o core
--         ├─ tab_audit        "Audit"           → panel + 4 audit fields (Created/Updated)
--         ├─ tab_vazby        "Vazby"           → prázdné (placeholder)
--         ├─ tab_pokrocile    "Pokročilé"       → prázdné (placeholder)
--         └─ tab_raw          "Raw"             → prázdné (placeholder)
--
-- Save flow (Fix #15 column_name resolve) zachová mapping field.layout.column_name → fw.core sloupec.

BEGIN;

DO $$
DECLARE
  -- comp_type lookups (existují, jen mimo 'active' filter)
  v_pc_type INT;        -- pagecontrol
  v_ts_type INT;        -- tabsheet
  v_panel_type INT := 13;   -- panel (z aktivních)
  v_edit_type  INT := 2;    -- edit (z aktivních)
  v_checkbox_type INT;      -- best-effort lookup, fallback edit
  v_memo_type INT;          -- best-effort lookup, fallback edit

  -- Anchor IDs
  v_root_id INT := 154;     -- existing fw.core 49 root form (type 302)

  -- Inserted IDs
  v_pc_id INT;
  v_t1 INT; v_t2 INT; v_t3 INT; v_t4 INT; v_t5 INT;
  v_p1 INT; v_p2 INT;
BEGIN
  -- 1. Lookup pagecontrol + tabsheet by code (status-agnostic — Marti's "máme to")
  SELECT id INTO v_pc_type FROM fw.comp_type WHERE code = 'pagecontrol' LIMIT 1;
  IF v_pc_type IS NULL THEN
    RAISE EXCEPTION 'comp_type pagecontrol NENALEZEN. Marti, pošli mi jeho id nebo dovol INSERT.';
  END IF;

  SELECT id INTO v_ts_type FROM fw.comp_type WHERE code = 'tabsheet' LIMIT 1;
  IF v_ts_type IS NULL THEN
    RAISE EXCEPTION 'comp_type tabsheet NENALEZEN. Marti, pošli mi jeho id nebo dovol INSERT.';
  END IF;

  -- 2. Best-effort lookup checkbox + memo (existing rows used 107 + 105)
  SELECT id INTO v_checkbox_type FROM fw.comp_type
    WHERE code IN ('checkbox', 'checkbox_modern', 'boolean') ORDER BY id LIMIT 1;
  IF v_checkbox_type IS NULL THEN v_checkbox_type := v_edit_type; END IF;

  SELECT id INTO v_memo_type FROM fw.comp_type
    WHERE code IN ('memo', 'memo_modern', 'textarea') ORDER BY id LIMIT 1;
  IF v_memo_type IS NULL THEN v_memo_type := v_edit_type; END IF;

  RAISE NOTICE 'Type IDs — pagecontrol=%, tabsheet=%, panel=%, edit=%, checkbox=%, memo=%',
               v_pc_type, v_ts_type, v_panel_type, v_edit_type, v_checkbox_type, v_memo_type;

  -- 3. Verify root #154 still exists
  IF NOT EXISTS (
    SELECT 1 FROM fw.comp_def WHERE id = v_root_id AND core_id = 49 AND type_id = 302
  ) THEN
    RAISE EXCEPTION 'root comp_def #154 missing nebo má jiný type. Halt.';
  END IF;

  -- 4. DROP existing children of root #154 (clean slate)
  DELETE FROM fw.comp_def WHERE core_id = 49 AND id != v_root_id;
  RAISE NOTICE 'Deleted existing children of root #154 (core 49).';

  -- 5. Page control (child of root)
  INSERT INTO fw.comp_def (
    core_id, parent_comp_def_id, type_id, name, caption,
    sort_order, is_active, created_by_text, updated_by_text
  ) VALUES (
    49, v_root_id, v_pc_type, 'main_pagecontrol', NULL,
    0, true, 'Claude', 'Claude'
  ) RETURNING id INTO v_pc_id;
  RAISE NOTICE 'Page control id=%', v_pc_id;

  -- 6. Five tabsheets (children of pagecontrol)
  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_pc_id, v_ts_type, 'tab_zakladni', 'Základní', 10, true, 'Claude', 'Claude') RETURNING id INTO v_t1;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_pc_id, v_ts_type, 'tab_audit', 'Audit', 20, true, 'Claude', 'Claude') RETURNING id INTO v_t2;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_pc_id, v_ts_type, 'tab_vazby', 'Vazby', 30, true, 'Claude', 'Claude') RETURNING id INTO v_t3;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_pc_id, v_ts_type, 'tab_pokrocile', 'Pokročilé', 40, true, 'Claude', 'Claude') RETURNING id INTO v_t4;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_pc_id, v_ts_type, 'tab_raw', 'Raw', 50, true, 'Claude', 'Claude') RETURNING id INTO v_t5;

  RAISE NOTICE 'Tabsheets: zakladni=%, audit=%, vazby=%, pokrocile=%, raw=%', v_t1, v_t2, v_t3, v_t4, v_t5;

  -- 7. Tab 1 "Základní" — panel + 6 info fields o core
  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_t1, v_panel_type, 'tab1_panel', NULL, 0, true, 'Claude', 'Claude') RETURNING id INTO v_p1;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, layout, sort_order, is_active, created_by_text, updated_by_text)
  VALUES
    (49, v_p1, v_edit_type,     'code',              'Code',
     jsonb_build_object('column_name', 'code'),                                10, true, 'Claude', 'Claude'),
    (49, v_p1, v_edit_type,     'label',             'Label',
     jsonb_build_object('column_name', 'label'),                               20, true, 'Claude', 'Claude'),
    (49, v_p1, v_memo_type,     'description_user',  'Popis (uživatel)',
     jsonb_build_object('column_name', 'description_user'),                    30, true, 'Claude', 'Claude'),
    (49, v_p1, v_checkbox_type, 'is_active',         'Aktivní',
     jsonb_build_object('column_name', 'is_active'),                           40, true, 'Claude', 'Claude'),
    (49, v_p1, v_edit_type,     'tenant_visibility', 'Tenant visibility',
     jsonb_build_object('column_name', 'tenant_visibility'),                   50, true, 'Claude', 'Claude'),
    (49, v_p1, v_edit_type,     'version',           'Verze',
     jsonb_build_object('column_name', 'version'),                             60, true, 'Claude', 'Claude');

  RAISE NOTICE 'Tab 1 panel + 6 info fields created (panel id=%)', v_p1;

  -- 8. Tab 2 "Audit" — panel + 4 audit fields (readonly)
  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, sort_order, is_active, created_by_text, updated_by_text)
  VALUES (49, v_t2, v_panel_type, 'tab2_panel', NULL, 0, true, 'Claude', 'Claude') RETURNING id INTO v_p2;

  INSERT INTO fw.comp_def (core_id, parent_comp_def_id, type_id, name, caption, layout, sort_order, is_active, created_by_text, updated_by_text)
  VALUES
    (49, v_p2, v_edit_type, 'created_at',      'Vytvořeno',
     jsonb_build_object('column_name', 'created_at',      'readonly', true), 10, true, 'Claude', 'Claude'),
    (49, v_p2, v_edit_type, 'created_by_text', 'Vytvořeno kým',
     jsonb_build_object('column_name', 'created_by_text', 'readonly', true), 20, true, 'Claude', 'Claude'),
    (49, v_p2, v_edit_type, 'updated_at',      'Upraveno',
     jsonb_build_object('column_name', 'updated_at',      'readonly', true), 30, true, 'Claude', 'Claude'),
    (49, v_p2, v_edit_type, 'updated_by_text', 'Upraveno kým',
     jsonb_build_object('column_name', 'updated_by_text', 'readonly', true), 40, true, 'Claude', 'Claude');

  RAISE NOTICE 'Tab 2 panel + 4 audit fields created (panel id=%)', v_p2;

  -- Tabs 3-5 zůstávají prázdné (placeholder pro budoucí rozšíření)
  RAISE NOTICE 'Tabs Vazby, Pokročilé, Raw zůstávají prázdné (placeholder).';

  RAISE NOTICE '====================================================';
  RAISE NOTICE 'DONE. Hard reload (Ctrl+Shift+R) → Editace: Země form pill → ⚙️ Core setting';
  RAISE NOTICE 'Uvidíš form 49 s 5 záložkami, na první: Code, Label, Popis, Aktivní, Tenant visibility, Verze.';
  RAISE NOTICE '====================================================';
END $$;

COMMIT;
