-- ============================================================
-- Modul HR Docházka — 5 ERP gridů pod "👥 Docházka" (menu_node id=94)
-- Claude (id=23), 6. 6. 2026. Vzor: _phase_system_new_db_connections_grid_v3.sql
-- + root=1 na comp_def (Fix #11). tenant 2 (EUROSOFT). db_connection_id=1.
-- Pozn.: casy skladane pres concat se znakem dvojtecky (NE format s dvojteckou),
--        aby SQLAlchemy text() nebral retezec za dvojteckou jako bind param.
-- Idempotentní (NOT EXISTS guardy). Bez BEGIN/COMMIT (write-cesta commitne sama).
-- ============================================================

-- ╔══ GRID 1 — Záznamy docházky (sort 200) ══════════════════╗
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Záznamy docházky', 94, 200, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label='Záznamy docházky' AND parent_id=94);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_att_entries', 'Záznamy docházky', 'HR docházka — všechny záznamy', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code='system_new.hr_att_entries');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_att_entries_list', 'HR: Záznamy docházky', 'att_entry + employee + type', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code='system_new.hr_att_entries_list');

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_att_entries_list', $sql$
SELECT e.id,
       to_char(e.entry_date,'YYYY-MM-DD') AS datum,
       em.cislo_zam,
       COALESCE(em.full_name,'Zam '||em.cislo_zam) AS zamestnanec,
       et.label AS typ,
       et.category AS kategorie,
       e.project_ref AS zakazka,
       to_char(e.started_at,'HH24')||':'||to_char(e.started_at,'MI') AS "od",
       to_char(e.ended_at,'HH24')||':'||to_char(e.ended_at,'MI') AS "do",
       e.hours AS hodiny,
       e.break_minutes AS pauza_min,
       e.status AS stav,
       e.source AS zdroj
FROM tenant.att_entry e
JOIN tenant.att_employee em ON em.id=e.employee_id
JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
WHERE e.tenant_id=2
ORDER BY e.entry_date DESC, e.id DESC
$sql$, 1, 'HR docházka — záznamy', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code='system_new.hr_att_entries_list');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_entries_list'),
       (SELECT id FROM fw.data_set WHERE code='system_new.hr_att_entries_list'),
       'select', 'default', TRUE, 'HR att_entries default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id=(SELECT id FROM fw.data_source WHERE code='system_new.hr_att_entries_list') AND variant_code='default');

UPDATE fw.menu_node SET core_id=(SELECT id FROM fw.core WHERE code='system_new.hr_att_entries')
WHERE label='Záznamy docházky' AND parent_id=94 AND core_id IS NULL;

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, root,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_hr_att_entries', 'Záznamy docházky',
       (SELECT id FROM fw.core WHERE code='system_new.hr_att_entries'), 306, 'main',
       (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_entries_list'), 100, TRUE, 1,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name='grid_hr_att_entries');

-- ╔══ GRID 2 — Měsíční přehled per zaměstnanec (sort 210) ════╗
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Měsíční přehled', 94, 210, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label='Měsíční přehled' AND parent_id=94);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_att_monthly', 'Měsíční přehled', 'HR docházka — měsíční souhrn per zaměstnanec', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code='system_new.hr_att_monthly');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_att_monthly_list', 'HR: Měsíční přehled', 'měsíční souhrn', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code='system_new.hr_att_monthly_list');

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_att_monthly_list', $sql$
SELECT em.cislo_zam,
       COALESCE(em.full_name,'Zam '||em.cislo_zam) AS zamestnanec,
       to_char(e.entry_date,'YYYY-MM') AS mesic,
       round(sum(CASE WHEN et.category='presence' THEN e.hours ELSE 0 END)::numeric,1) AS odpracovano,
       round(sum(CASE WHEN et.category<>'presence' THEN e.hours ELSE 0 END)::numeric,1) AS nepritomnost,
       count(*) AS zaznamu
FROM tenant.att_entry e
JOIN tenant.att_employee em ON em.id=e.employee_id
JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
WHERE e.tenant_id=2
GROUP BY em.cislo_zam, em.full_name, to_char(e.entry_date,'YYYY-MM')
ORDER BY mesic DESC, em.cislo_zam
$sql$, 1, 'HR docházka — měsíční přehled', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code='system_new.hr_att_monthly_list');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_monthly_list'),
       (SELECT id FROM fw.data_set WHERE code='system_new.hr_att_monthly_list'),
       'select', 'default', TRUE, 'HR att_monthly default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id=(SELECT id FROM fw.data_source WHERE code='system_new.hr_att_monthly_list') AND variant_code='default');

UPDATE fw.menu_node SET core_id=(SELECT id FROM fw.core WHERE code='system_new.hr_att_monthly')
WHERE label='Měsíční přehled' AND parent_id=94 AND core_id IS NULL;

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, root,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_hr_att_monthly', 'Měsíční přehled',
       (SELECT id FROM fw.core WHERE code='system_new.hr_att_monthly'), 306, 'main',
       (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_monthly_list'), 100, TRUE, 1,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name='grid_hr_att_monthly');

-- ╔══ GRID 3 — Zaměstnanci (sort 220) ═══════════════════════╗
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Zaměstnanci', 94, 220, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label='Zaměstnanci' AND parent_id=94);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_att_employees', 'Zaměstnanci', 'HR docházka — zaměstnanci', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code='system_new.hr_att_employees');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_att_employees_list', 'HR: Zaměstnanci', 'att_employee', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code='system_new.hr_att_employees_list');

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_att_employees_list', $sql$
SELECT id, cislo_zam, full_name, user_id, is_active,
       to_char(created_at,'YYYY-MM-DD HH24')||':'||to_char(created_at,'MI') AS zalozeno
FROM tenant.att_employee
WHERE tenant_id=2
ORDER BY cislo_zam
$sql$, 1, 'HR docházka — zaměstnanci', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code='system_new.hr_att_employees_list');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_employees_list'),
       (SELECT id FROM fw.data_set WHERE code='system_new.hr_att_employees_list'),
       'select', 'default', TRUE, 'HR att_employees default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id=(SELECT id FROM fw.data_source WHERE code='system_new.hr_att_employees_list') AND variant_code='default');

UPDATE fw.menu_node SET core_id=(SELECT id FROM fw.core WHERE code='system_new.hr_att_employees')
WHERE label='Zaměstnanci' AND parent_id=94 AND core_id IS NULL;

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, root,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_hr_att_employees', 'Zaměstnanci',
       (SELECT id FROM fw.core WHERE code='system_new.hr_att_employees'), 306, 'main',
       (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_employees_list'), 100, TRUE, 1,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name='grid_hr_att_employees');

-- ╔══ GRID 4 — Typy záznamu (číselník, sort 230) ════════════╗
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Typy záznamu', 94, 230, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label='Typy záznamu' AND parent_id=94);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_att_types', 'Typy záznamu', 'HR docházka — číselník typů záznamu', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code='system_new.hr_att_types');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_att_types_list', 'HR: Typy záznamu', 'att_entry_type', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code='system_new.hr_att_types_list');

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_att_types_list', $sql$
SELECT id, code, label, category, is_paid, affects_balance, requires_approval, is_active
FROM tenant.att_entry_type
WHERE tenant_id=2
ORDER BY id
$sql$, 1, 'HR docházka — typy záznamu', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code='system_new.hr_att_types_list');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_types_list'),
       (SELECT id FROM fw.data_set WHERE code='system_new.hr_att_types_list'),
       'select', 'default', TRUE, 'HR att_types default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id=(SELECT id FROM fw.data_source WHERE code='system_new.hr_att_types_list') AND variant_code='default');

UPDATE fw.menu_node SET core_id=(SELECT id FROM fw.core WHERE code='system_new.hr_att_types')
WHERE label='Typy záznamu' AND parent_id=94 AND core_id IS NULL;

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, root,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_hr_att_types', 'Typy záznamu',
       (SELECT id FROM fw.core WHERE code='system_new.hr_att_types'), 306, 'main',
       (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_types_list'), 100, TRUE, 1,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name='grid_hr_att_types');

-- ╔══ GRID 5 — Měsíční zůstatky (sort 240) ══════════════════╗
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'Měsíční zůstatky', 94, 240, 'active', 'parent_only', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE label='Měsíční zůstatky' AND parent_id=94);

INSERT INTO fw.core (code, label, description_user, created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'system_new.hr_att_balances', 'Měsíční zůstatky', 'HR docházka — měsíční zůstatky (zatím prázdné)', 2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code='system_new.hr_att_balances');

INSERT INTO fw.data_source (code, name, description, refresh_type, status, is_system)
SELECT 'system_new.hr_att_balances_list', 'HR: Měsíční zůstatky', 'att_balance', 'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code='system_new.hr_att_balances_list');

INSERT INTO fw.data_set (code, sql_text, db_connection_id, description, status, is_system)
SELECT 'system_new.hr_att_balances_list', $sql$
SELECT b.id, em.cislo_zam, COALESCE(em.full_name,'') AS zamestnanec,
       b.period_year AS rok, b.period_month AS mesic,
       b.worked_hours, b.overtime_hours, b.vacation_days, b.sick_days, b.planned_hours
FROM tenant.att_balance b
JOIN tenant.att_employee em ON em.id=b.employee_id
WHERE b.tenant_id=2
ORDER BY b.period_year DESC, b.period_month DESC, em.cislo_zam
$sql$, 1, 'HR docházka — měsíční zůstatky', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code='system_new.hr_att_balances_list');

INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, is_default, description)
SELECT (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_balances_list'),
       (SELECT id FROM fw.data_set WHERE code='system_new.hr_att_balances_list'),
       'select', 'default', TRUE, 'HR att_balances default select'
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source_op
    WHERE data_source_id=(SELECT id FROM fw.data_source WHERE code='system_new.hr_att_balances_list') AND variant_code='default');

UPDATE fw.menu_node SET core_id=(SELECT id FROM fw.core WHERE code='system_new.hr_att_balances')
WHERE label='Měsíční zůstatky' AND parent_id=94 AND core_id IS NULL;

INSERT INTO fw.comp_def (name, caption, core_id, type_id, region_slot, data_source_id, sort_order, is_active, root,
    created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 'grid_hr_att_balances', 'Měsíční zůstatky',
       (SELECT id FROM fw.core WHERE code='system_new.hr_att_balances'), 306, 'main',
       (SELECT id FROM fw.data_source WHERE code='system_new.hr_att_balances_list'), 100, TRUE, 1,
       2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name='grid_hr_att_balances');
