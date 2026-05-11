-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 11-E (11.5.2026 dopoledne): fw.data_set + data_source +
-- data_source_op pro 6 grids (audit + framework). A3 architecture LIVE.
-- ════════════════════════════════════════════════════════════════════════
-- Architectonicky (Marti-AI's A3 doctrine 9.5.):
--   - fw.data_set       = SQL primitiv (sql_text NOT NULL)
--   - fw.data_source    = hlavička metadata (žádný SQL)
--   - fw.data_source_op = mapping (data_source_id + data_set_id + kind + variant)
--
-- Po Krok 11-D máme fw.core entries. Teď přidáváme runtime pipeline pro
-- 6 grids — Krok 12 generic DataSourceRunner pak může číst:
--   menu_node.core_id -> core.code -> data_source.code -> data_source_op
--   -> data_set.sql_text -> EXECUTE -> JSON response
--
-- 1-na-1 mapping (1 grid = 1 data_set = 1 data_source = 1 data_source_op).
-- Variant code = 'default', is_default = TRUE.
--
-- SQLs extracted z aktualnich hardcoded endpoints v router.py:
--   - audit:     /system/audit-overview?mode={audited|all|stats}  (ř. 488-810)
--   - framework: /system/framework?view={menu_nodes|data_sources|data_sets}  (ř. 1326-1545)
--
-- POZN: SQLs byly extracted manuálně z ORM, nemusí být 100% přesné při
-- prvním Krok 12 smoke testu. Pripadne opravy v place.
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. fw.data_set — 6 SQL primitives
-- ════════════════════════════════════════════════════════════════════════

-- (1) audit_audited_select: list všech konverzací (Marti spec 9.5.: bez status filtru)
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'audit_audited_select', 'select',
    $sql$
SELECT c.id, c.conversation_type, c.is_deleted, c.title, c.audit_status,
       c.audit_notes, c.audited_at, c.audited_by_persona_id, c.tenant_id,
       c.project_id, c.lifecycle_state, c.last_message_at, c.created_at,
       pe.name AS audited_by_persona_name,
       te.name AS tenant_name
FROM public.conversations c
LEFT JOIN public.personas pe ON pe.id = c.audited_by_persona_id
LEFT JOIN public.tenants te ON te.id = c.tenant_id
WHERE (CAST(:tenant_id AS bigint) IS NULL OR c.tenant_id = :tenant_id)
  AND (CAST(:scope AS text) IS NULL OR c.audit_notes->>'scope' = :scope)
  AND (CAST(:d_from AS timestamptz) IS NULL OR c.audited_at >= :d_from)
  AND (CAST(:d_to AS timestamptz) IS NULL OR c.audited_at <= :d_to)
ORDER BY c.id DESC
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: list všech konverzací (audit dashboard, default tab "Auditované"). Marti spec 9.5.: žádný status filtr, vše viditelné.',
    true, 'active'
);

-- (2) audit_all_select: stejně jako audited, ale ORDER BY last_message_at
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'audit_all_select', 'select',
    $sql$
SELECT c.id, c.conversation_type, c.is_deleted, c.title, c.audit_status,
       c.audit_notes, c.audited_at, c.audited_by_persona_id, c.tenant_id,
       c.project_id, c.lifecycle_state, c.last_message_at, c.created_at,
       pe.name AS audited_by_persona_name,
       te.name AS tenant_name
FROM public.conversations c
LEFT JOIN public.personas pe ON pe.id = c.audited_by_persona_id
LEFT JOIN public.tenants te ON te.id = c.tenant_id
WHERE (CAST(:tenant_id AS bigint) IS NULL OR c.tenant_id = :tenant_id)
  AND (CAST(:status AS text) IS NULL OR c.audit_status = :status)
  AND (CAST(:d_from AS timestamptz) IS NULL OR c.last_message_at >= :d_from)
  AND (CAST(:d_to AS timestamptz) IS NULL OR c.last_message_at <= :d_to)
ORDER BY c.last_message_at DESC NULLS LAST
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: list všech konverzací s status badge sloupcem (mix pending/in_progress/audited/excluded).',
    true, 'active'
);

-- (3) audit_stats_select: per-status × per-tenant pivot (simplest variant)
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'audit_stats_select', 'select',
    $sql$
SELECT c.audit_status, c.tenant_id, te.name AS tenant_name, COUNT(*) AS row_count
FROM public.conversations c
LEFT JOIN public.tenants te ON te.id = c.tenant_id
WHERE (CAST(:tenant_id AS bigint) IS NULL OR c.tenant_id = :tenant_id)
GROUP BY c.audit_status, c.tenant_id, te.name
ORDER BY c.tenant_id NULLS FIRST, c.audit_status
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: per-status × per-tenant agregace audit dashboard. Simplified variant (1 SELECT), full multi-query stats budou separate data_sources Krok 12+.',
    true, 'active'
);

-- (4) framework_menu_nodes_select: navigation tree + parent code lookup
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'framework_menu_nodes_select', 'select',
    $sql$
SELECT n.*, p.code AS _parent_code
FROM fw.menu_node n
LEFT JOIN fw.menu_node p ON p.id = n.parent_id
ORDER BY n.id
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: fw.menu_node list view s parent_code denormalization. Read-only navigation tree editor (Phase 38.3+).',
    true, 'active'
);

-- (5) framework_data_sources_select: A3 hlavička + agg children
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'framework_data_sources_select', 'select',
    $sql$
SELECT s.*,
       COALESCE(op.cnt, 0)   AS operation_count,
       op.kinds              AS operation_kinds
FROM fw.data_source s
LEFT JOIN (
    SELECT data_source_id,
           COUNT(*) AS cnt,
           STRING_AGG(operation_kind, ', ' ORDER BY operation_kind) AS kinds
    FROM fw.data_source_op
    GROUP BY data_source_id
) op ON op.data_source_id = s.id
ORDER BY s.id
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: fw.data_source list view s child operations aggregation (A3 doctrine). Recursive — sám sebe vidí ve výpisu.',
    true, 'active'
);

-- (6) framework_data_sets_select: low-level SQL primitives
INSERT INTO fw.data_set (code, kind, sql_text, db_connection, description, is_system, status)
VALUES (
    'framework_data_sets_select', 'select',
    $sql$
SELECT *
FROM fw.data_set
ORDER BY id
LIMIT :limit
$sql$,
    'data_db',
    'Phase 38.4 Krok 11-E: fw.data_set list view (low-level SQL primitives). Self-bootstrapping — viditelný v sobě samém.',
    true, 'active'
);

-- ════════════════════════════════════════════════════════════════════════
-- 2. fw.data_source — 6 headers (žádný SQL, jen metadata)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source
    (code, name, description, refresh_type, default_record_limit,
     is_system, status)
VALUES
    ('audit_audited', 'Audit: Auditované konverzace',
     'Phase 38.4 Krok 11-E: list view auditovaných konverzací (default tab audit dashboard).',
     'manual', 1000, true, 'active'),
    ('audit_all', 'Audit: Všechny konverzace',
     'Phase 38.4 Krok 11-E: list view všech konverzací s status badge.',
     'manual', 1000, true, 'active'),
    ('audit_stats', 'Audit: Přehled statistik',
     'Phase 38.4 Krok 11-E: per-status × per-tenant agregace (simplified variant).',
     'manual', 1000, true, 'active'),
    ('framework_menu_nodes', 'Framework: Definice levého stromu',
     'Phase 38.4 Krok 11-E: fw.menu_node read-only list view.',
     'manual', 10000, true, 'active'),
    ('framework_data_sources', 'Framework: Datové zdroje',
     'Phase 38.4 Krok 11-E: fw.data_source list view s child operations agg.',
     'manual', 10000, true, 'active'),
    ('framework_data_sets', 'Framework: DataSets',
     'Phase 38.4 Krok 11-E: fw.data_set list view (low-level SQL primitives).',
     'manual', 10000, true, 'active');

-- ════════════════════════════════════════════════════════════════════════
-- 3. fw.data_source_op — 6 mappings (source -> set, kind='select', default variant)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source_op
    (data_source_id, data_set_id, operation_kind, variant_code, sort_order,
     is_default, description)
SELECT
    s.id, ds.id, 'select', 'default', 0, true,
    'Phase 38.4 Krok 11-E: default SELECT operation. 1-na-1 mapping pro list view.'
FROM fw.data_source s
JOIN fw.data_set ds ON ds.code = s.code || '_select'
WHERE s.code IN (
    'audit_audited', 'audit_all', 'audit_stats',
    'framework_menu_nodes', 'framework_data_sources', 'framework_data_sets'
);

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.data_set WHERE code LIKE 'audit_%' OR code LIKE 'framework_%') AS data_sets_added,
    (SELECT COUNT(*) FROM fw.data_source WHERE code IN ('audit_audited', 'audit_all', 'audit_stats', 'framework_menu_nodes', 'framework_data_sources', 'framework_data_sets')) AS data_sources_added,
    (SELECT COUNT(*) FROM fw.data_source_op op
     JOIN fw.data_source s ON s.id = op.data_source_id
     WHERE s.code IN ('audit_audited', 'audit_all', 'audit_stats', 'framework_menu_nodes', 'framework_data_sources', 'framework_data_sets')) AS data_source_ops_added;
-- Expected: 6 / 6 / 6

-- Detail per grid (mapping kompletní)
SELECT
    s.code AS source_code,
    s.name AS source_name,
    op.operation_kind,
    op.variant_code,
    op.is_default,
    ds.code AS set_code,
    LENGTH(ds.sql_text) AS sql_length
FROM fw.data_source s
JOIN fw.data_source_op op ON op.data_source_id = s.id
JOIN fw.data_set ds ON ds.id = op.data_set_id
WHERE s.code IN ('audit_audited', 'audit_all', 'audit_stats',
                 'framework_menu_nodes', 'framework_data_sources', 'framework_data_sets')
ORDER BY s.code;
-- Expected: 6 řádků, každý source -> 1 set přes select default
