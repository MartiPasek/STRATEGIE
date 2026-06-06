-- ============================================================
-- HR Presence board — „Kdo je v budově" (Marti 5.6.2026)
-- Vzor: _phase_system_new_db_connections_grid_v3.sql (proven 22.5.)
-- Jednoduché SQL (ASCII aliasy, žádné to_char/EXTRACT/diakritika)
-- — komplexní SQL pod strategie rolí dřív vracelo 0 řádků.
-- ============================================================
BEGIN;

-- 1. Folder „👥 Docházka" pod System (33)
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT '👥 Docházka', 33, 260, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label = '👥 Docházka' AND parent_id = 33);

-- 2. Grid menu_node „Kdo je v budově" pod Docházkou
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Kdo je v budově',
    (SELECT id FROM fw.menu_node WHERE label = '👥 Docházka' AND parent_id = 33),
    100, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label = 'Kdo je v budově');

-- 3. core
INSERT INTO fw.core (code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_presence_board', 'Kdo je v budově',
    'HR presence board — aktuální stav lidí (v budově / online / offline) z fw.hr_presence',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.hr_presence_board');

-- 4. data_source
INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_presence_board_list', 'HR: Kdo je v budově',
    'fw.hr_presence + jméno z public.users', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.hr_presence_board_list');

-- 5. data_set (jednoduché SQL)
INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_presence_board_list',
$sql$
SELECT
  p.user_id,
  COALESCE(u.short_name, u.login_name) AS clovek,
  CASE
    WHEN p.in_building AND p.last_seen_at > now() - interval '12 minutes' THEN 'V budove'
    WHEN p.last_seen_at > now() - interval '12 minutes' THEN 'Online (mimo budovu)'
    ELSE 'Offline'
  END AS stav,
  p.source AS zdroj,
  p.last_seen_at AS naposledy
FROM fw.hr_presence p
LEFT JOIN public.users u ON u.id = p.user_id
ORDER BY (p.last_seen_at > now() - interval '12 minutes') DESC, p.last_seen_at DESC NULLS LAST
$sql$,
    1, 'HR presence board', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.hr_presence_board_list');

-- 6. data_source_op select default
INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.hr_presence_board_list'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.hr_presence_board_list'),
    'select', 'default', TRUE, 'HR presence board default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.hr_presence_board_list')
      AND variant_code = 'default');

-- 7. UPDATE menu_node.core_id
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.hr_presence_board')
WHERE label = 'Kdo je v budově' AND core_id IS NULL;

-- 8. comp_def grid_modern (306) — root=1 (XOR chk_comp_def_single_parent)
INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, root,
    data_source_id, sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_system_new_hr_presence_board', 'Kdo je v budově',
    (SELECT id FROM fw.core WHERE code = 'system_new.hr_presence_board'),
    306, 'main', 1,
    (SELECT id FROM fw.data_source WHERE code = 'system_new.hr_presence_board_list'),
    100, TRUE, 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_hr_presence_board');

COMMIT;
