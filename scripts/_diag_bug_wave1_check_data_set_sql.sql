-- ============================================================
-- BUG AUDIT Wave 1 — check zbývající 2 bugy v fw.data_set
-- ============================================================
-- Z fw.diag_log:
--   Bug #1: framework_menu_nodes SQL referencuje sloupec, který už neexistuje
--   Bug #2: system_new.framework_menu_nodes SQL stejný problém
--
-- Task #313 dropla `fw.menu_node.code` (22.5. ráno).
-- Pokud data_set SQL ho stále referencuje → silent fail při execute.
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Najdi data_set rows pro framework_menu_nodes        ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    id,
    code,
    LEFT(sql_text, 500) AS sql_preview,
    LENGTH(sql_text) AS sql_length,
    updated_at
FROM fw.data_set
WHERE code IN ('framework_menu_nodes', 'system_new.framework_menu_nodes')
ORDER BY code;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: Najdi VŠECHNY data_set rows co referencují          ║
-- ║      fw.menu_node — zkontroluj jestli někde nezůstal     ║
-- ║      odkaz na dropped column 'code' nebo 'kind'          ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    id,
    code AS ds_code,
    CASE
        WHEN sql_text ~* '\mp\.code\M'    THEN 'PROBLEM: p.code'
        WHEN sql_text ~* '\mm\.code\M'    THEN 'PROBLEM: m.code'
        WHEN sql_text ~* '\mmn\.code\M'   THEN 'PROBLEM: mn.code'
        WHEN sql_text ~* 'menu_node\.code' THEN 'PROBLEM: menu_node.code'
        WHEN sql_text ~* '\mp\.kind\M'    THEN 'PROBLEM: p.kind'
        WHEN sql_text ~* '\mm\.kind\M'    THEN 'PROBLEM: m.kind'
        WHEN sql_text ~* '\mmn\.kind\M'   THEN 'PROBLEM: mn.kind'
        WHEN sql_text ~* 'menu_node\.kind' THEN 'PROBLEM: menu_node.kind'
        ELSE 'OK (no dropped col refs)'
    END AS verdict,
    LEFT(sql_text, 300) AS sql_preview
FROM fw.data_set
WHERE sql_text ILIKE '%fw.menu_node%'
   OR sql_text ILIKE '%menu_node%'
ORDER BY id;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q3: Verify current fw.menu_node columns                  ║
-- ║      (potvrď, že 'code' a 'kind' opravdu chybí)          ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'menu_node'
ORDER BY ordinal_position;
-- Expected: id, parent_id, label, sort_order, core_id, status, is_immutable,
--           description_user, description_system, audit columns
-- NOT EXPECTED: code, kind (Task #313 / #312)


-- ============================================================
-- INTERPRETACE:
--   Q1: Pokud sql_preview obsahuje 'p.code' nebo 'p.kind' → bug
--       confirmed, potřeba UPDATE.
--   Q2: Najde i ostatní data_set rows kde mohl zůstat ten samý
--       problém (preventivní sweep).
--   Q3: Confirms current schema state — že drop opravdu proběhl.
-- ============================================================
