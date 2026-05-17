-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 11-D (11.5.2026 dopoledne): fw.core entries pro audit + framework
-- ════════════════════════════════════════════════════════════════════════
-- Po Kroku 11-C (menu_node.core_id FK LIVE) zbylo 6 menu_node rows
-- bez core entry (kind='list' + 'special'):
--   - audit_audited / audit_all / audit_stats (rows 3-5)
--   - framework_menu_nodes / framework_data_sources / framework_data_sets (rows 13-15)
--
-- Vytvarime 6 fw.core entries + backfill menu_node.core_id.
-- Pak ratio bude 11 with core / 4 without (3 folders + 1 iframe) / 15 total.
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. INSERT 6 fw.core rows
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.core (code, label, description, layout_type)
VALUES
    -- Audit dashboard views (Phase 35-E.4)
    ('audit_audited', 'Audit: Auditované konverzace',
     'Phase 35-E.4 (9.5.): list view auditovaných konverzací (audit_status=audited). Audit má váhu uzavření (Marti Q3 A 9.5.).',
     'list'),
    ('audit_all', 'Audit: Všechny konverzace',
     'Phase 35-E.4 (9.5.): list view všech konverzací (pending/in_progress/audited/excluded mix). Status badge sloupec viditelný.',
     'list'),
    ('audit_stats', 'Audit: Přehled statistik',
     'Phase 35-E.4 (9.5.): agregace per-persona × per-month buckets. Per-status counts, per-tenant audited, per-scope.',
     'list'),

    -- Framework definice views (Phase 38.3+ / 38.4 Krok 6+)
    ('framework_menu_nodes', 'Framework: Definice levého stromu',
     'Phase 38.3+ (10.5.): fw.menu_node read-only editor — list navigation tree nodes.',
     'list'),
    ('framework_data_sources', 'Framework: Datové zdroje',
     'Phase 38.4 Krok 6+ (9.5.): fw.data_source list view (read-only) — hlavičky data sources s child operations agg.',
     'list'),
    ('framework_data_sets', 'Framework: DataSets',
     'Phase 38.4 Krok 6+ (9.5.): fw.data_set list view (read-only) — low-level SQL primitives, recursive (self-bootstrapping).',
     'list');

-- ════════════════════════════════════════════════════════════════════════
-- 2. Backfill menu_node.core_id pro 6 rows
-- ════════════════════════════════════════════════════════════════════════
-- Audit rows (system.audit.audited / all / stats)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'audit_audited' LIMIT 1)
WHERE code = 'system.audit.audited';

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'audit_all' LIMIT 1)
WHERE code = 'system.audit.all';

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'audit_stats' LIMIT 1)
WHERE code = 'system.audit.stats';

-- Framework rows (system.framework.menu_nodes / data_sources / data_sets)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'framework_menu_nodes' LIMIT 1)
WHERE code = 'system.framework.menu_nodes';

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'framework_data_sources' LIMIT 1)
WHERE code = 'system.framework.data_sources';

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'framework_data_sets' LIMIT 1)
WHERE code = 'system.framework.data_sets';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.menu_node WHERE core_id IS NOT NULL) AS rows_with_core,
    (SELECT COUNT(*) FROM fw.menu_node WHERE core_id IS NULL) AS rows_without_core,
    (SELECT COUNT(*) FROM fw.menu_node) AS total_rows,
    (SELECT COUNT(*) FROM fw.core) AS total_cores;
-- Expected: 11 / 4 / 15 / (předchozí + 6)
--   4 NULL = rows 1 (📦 SYSTEM folder), 2 (🗂️ Záložkový přehled iframe),
--            6 (📁 Security folder), 12 (🏗️ Framework folder)

-- Detail per row pro kontrolu (mělo by být 11 řádků s core_code !== NULL)
SELECT
    n.id AS menu_id,
    n.code AS menu_code,
    n.label,
    n.kind,
    n.cislo_def AS cislo_def_legacy,
    n.core_id,
    c.code AS core_code
FROM fw.menu_node n
LEFT JOIN fw.core c ON c.id = n.core_id
ORDER BY n.id;
-- Expected zbylé NULL pouze na rows: 1, 2, 6, 12 (= folders + iframe)
