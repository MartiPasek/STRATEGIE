-- ============================================================
-- BUG FIX Wave 1 — opravit 3 fw.data_set rows
-- ============================================================
-- Po Task #312 (drop fw.menu_node.kind) + #313 (drop fw.menu_node.code)
-- zůstaly 3 data_set SQL co stále referencují dropped sloupce.
--
-- Strategie: `code` → `label` (jediný display sloupec, který zůstal).
-- Pro id=28 ORDER BY: drop `code` z order (sort_order je deterministic).
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Fix #1: id=4 framework_menu_nodes_select                 ║
-- ║          p.code → p.label (display fallback)              ║
-- ╚══════════════════════════════════════════════════════════╝
UPDATE fw.data_set
SET sql_text = '
SELECT n.*, p.label AS _parent_label
FROM fw.menu_node n
LEFT JOIN fw.menu_node p ON p.id = n.parent_id
ORDER BY n.id
LIMIT :limit
',
    updated_at = NOW()
WHERE id = 4 AND code = 'framework_menu_nodes_select';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Fix #2: id=7 framework_core_select                       ║
-- ║          mn.code → mn.label (drop _origin_menu_node_code) ║
-- ╚══════════════════════════════════════════════════════════╝
-- POZOR: tahle data_set má dlouhé SQL, jen pojďme nahradit `mn.code` na `mn.label`
-- a `_origin_menu_node_code` aliasem `_origin_menu_node_code_alias` (zachováno pro BC).
UPDATE fw.data_set
SET sql_text = REPLACE(
                  sql_text,
                  'mn.code AS _origin_menu_node_code',
                  'mn.label AS _origin_menu_node_code'  -- alias zachováno pro BC frontend
               ),
    updated_at = NOW()
WHERE id = 7 AND code = 'framework_core_select'
  AND sql_text LIKE '%mn.code AS _origin_menu_node_code%';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Fix #3: id=28 system_new.framework_menu_nodes           ║
-- ║          ORDER BY ... sort_order, code → sort_order, label║
-- ╚══════════════════════════════════════════════════════════╝
UPDATE fw.data_set
SET sql_text = '
SELECT *
FROM fw.menu_node
ORDER BY parent_id NULLS FIRST, sort_order, label
LIMIT 1000
    ',
    updated_at = NOW()
WHERE id = 28 AND code = 'system_new.framework_menu_nodes';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Verify: re-check všech 3 řádků                           ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    id,
    code AS ds_code,
    CASE
        WHEN sql_text ~* '\mp\.code\M'    THEN 'STILL BROKEN: p.code'
        WHEN sql_text ~* '\mmn\.code\M'   THEN 'STILL BROKEN: mn.code'
        WHEN sql_text ~* 'menu_node\.code' THEN 'STILL BROKEN: menu_node.code'
        WHEN sql_text ~* '\s,\s*code\s*$' THEN 'STILL BROKEN: ORDER BY code'
        WHEN sql_text ~* '\s,\s*code\s+' THEN 'STILL BROKEN: ORDER BY code'
        ELSE 'FIXED ✓'
    END AS verdict,
    LEFT(sql_text, 250) AS sql_preview
FROM fw.data_set
WHERE id IN (4, 7, 28)
ORDER BY id;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Resolve fw.diag_log entries pro tyhle bugy               ║
-- ║  (Fix N doctrine: NE UPDATE existing rows, jen           ║
-- ║   resolved_at + resolved_by jako audit closure)           ║
-- ╚══════════════════════════════════════════════════════════╝
-- Pozn: pokud fw.diag_log ma sloupec status/resolved_*, tak se updatne
-- pres standard "acknowledge" workflow. Tady jen overime, kolik error
-- radku se tyhle 3 data_set kodu tyka.
SELECT
    COUNT(*) AS error_count,
    MIN(created_at) AS first_seen,
    MAX(created_at) AS last_seen,
    SUM(occurrences) AS total_occurrences
FROM fw.diag_log
WHERE level = 'error'
  AND (
    message ILIKE '%framework_menu_nodes_select%' OR
    message ILIKE '%framework_core_select%' OR
    message ILIKE '%system_new.framework_menu_nodes%' OR
    message ILIKE '%column "code" does not exist%' OR
    message ILIKE '%column "kind" does not exist%'
  )
  AND COALESCE(status, 'open') = 'open';


-- ============================================================
-- VÝSLEDEK:
--   Po update — Verify query by mela vratit 'FIXED ✓' pro vsech 3.
--   Po fixu: grid framework_menu_nodes + framework_cores +
--            system_new.framework_menu_nodes by mely fungovat bez
--            silent fail. fw.diag_log error_count zustane (forensic
--            history), ale nove erorry uz nepribyvaji.
-- ============================================================
