-- ============================================================
-- DIAG: najdi parent_id pro kanárka v System tree
-- ============================================================
-- Cíl: zjistit kam patří kanárek (pod jaký system soudeček).
-- Preference: System → Diagnostika (kde už je diag_log grid)
--             fallback: System → Framework (kde už jsou ostatní system veci)
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Najdi system root + jeho děti                        ║
-- ╚══════════════════════════════════════════════════════════╝
WITH system_root AS (
    SELECT id, label, parent_id
    FROM fw.menu_node
    WHERE parent_id IS NULL
       OR label ILIKE '%system%'
)
SELECT
    mn.id,
    mn.parent_id,
    mn.label,
    mn.sort_order,
    mn.core_id,
    mn.status,
    (
        SELECT COUNT(*)
        FROM fw.menu_node child
        WHERE child.parent_id = mn.id
    ) AS child_count
FROM fw.menu_node mn
LEFT JOIN system_root sr ON sr.id = mn.parent_id OR mn.id = sr.id
WHERE sr.id IS NOT NULL
   OR mn.label ILIKE '%diag%'
   OR mn.label ILIKE '%framework%'
ORDER BY mn.parent_id NULLS FIRST, mn.sort_order, mn.label;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: Diag log node — kde sedí? (reference point)         ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    mn.id,
    mn.parent_id,
    mn.label,
    parent.label AS parent_label
FROM fw.menu_node mn
LEFT JOIN fw.menu_node parent ON parent.id = mn.parent_id
WHERE mn.label ILIKE '%diag%log%'
   OR mn.label ILIKE '%diagnostika%';

-- ============================================================
-- INTERPRETACE:
--   Q1: najdeme System tree strukturu
--   Q2: pokud diag_log má parent X, kanárek bude sibling pod X
-- ============================================================
