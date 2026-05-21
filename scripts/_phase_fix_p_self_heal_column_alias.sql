-- ════════════════════════════════════════════════════════════════════════
-- Fix P (21.5. rano) — self-healing column alias map pro fw.data_set SQL
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's doctrine 21.5.: "tech zmen v DB je tolik, ze zadny audit
-- nepotrebujeme... 2. tabulka musi zacinat comp_grid" + "Self-healing
-- column registry doctrine" (Krok 5.R-C extension).
--
-- Při každém data_source execute (modules.erp.application.data_source_runner):
--   1. Pre-execute scan SQL pro qualified column refs (table.col / alias.col)
--   2. Lookup v fw.comp_grid_column_alias — pokud known rename, rewrite
--   3. UPDATE fw.data_set.sql_text persistent (transparent migration)
--   4. Log info row do fw.diag_log ("Auto-applied N aliases v data_set #X")
--   5. Execute s new SQL
--
-- Žádný separate audit table — fw.diag_log (single source of truth) drží
-- "self_heal" module rows. Marti's "audit RO append-only" doctrine drží.
--
-- new_column = NULL → sloupec dropnut nadobro (žádný auto-fix, SQL fail
-- → manual rewrite needed). Pattern slouží jako "documented removal" pro
-- diagnostiku: pokud SQL stále padá na c.data_entity_type, víme z aliasu
-- že je permanent dropnut (ne typo).
--
-- RUN: jako Marti (member of fw_owners), highlight + Alt+X.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1) DDL — fw.comp_grid_column_alias
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.comp_grid_column_alias (
    id BIGSERIAL PRIMARY KEY,
    -- Table name nebo SQL alias (e.g. 'tenants', 'te', 't', 'cmi', 'cd').
    -- Self-heal regex match: \b<table_or_alias>\.<old_column>\b → rewrite.
    table_or_alias VARCHAR(100) NOT NULL,
    old_column VARCHAR(100) NOT NULL,
    -- NULL = sloupec dropnut nadobro (žádný auto-fix, raise → manual SQL rewrite)
    -- NOT NULL = rename (auto-rewrite \b<alias>.<old>\b → <alias>.<new>)
    new_column VARCHAR(100),
    migrated_at TIMESTAMPTZ DEFAULT NOW(),
    note TEXT,
    UNIQUE(table_or_alias, old_column)
);

-- Owner sjednoceně s fw schema (per Unified Ownership doctrine 21.5.)
ALTER TABLE fw.comp_grid_column_alias OWNER TO fw_owners;
GRANT SELECT, INSERT, UPDATE ON fw.comp_grid_column_alias TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.comp_grid_column_alias_id_seq TO strategie;

-- Index pro hot-path scan při každém grid call
CREATE INDEX IF NOT EXISTS ix_comp_grid_column_alias_lookup
    ON fw.comp_grid_column_alias(table_or_alias, old_column);

-- ════════════════════════════════════════════════════════════════════════
-- 2) Pre-populate — dnešní 4 známé migrace
-- ════════════════════════════════════════════════════════════════════════
-- Tenants column renaming (Phase 35) — různé SQL alias variants
INSERT INTO fw.comp_grid_column_alias (table_or_alias, old_column, new_column, note) VALUES
('te',      'name', 'tenant_name', 'Phase 35 column renaming (te alias for tenants)'),
('t',       'name', 'tenant_name', 'Phase 35 column renaming (t alias)'),
('tenants', 'name', 'tenant_name', 'Phase 35 column renaming (full table name)')
ON CONFLICT (table_or_alias, old_column) DO NOTHING;

-- fw.core.data_entity_type dropped (Krok 5.M 16.5.) — žádný náhradník
INSERT INTO fw.comp_grid_column_alias (table_or_alias, old_column, new_column, note) VALUES
('c',    'data_entity_type', NULL, 'Krok 5.M (16.5.) dropped — entity moves to comp_def root'),
('core', 'data_entity_type', NULL, 'Krok 5.M (16.5.) dropped')
ON CONFLICT (table_or_alias, old_column) DO NOTHING;

-- fw.context_menu_item.code dropped (Krok 5.M-6 17.5.)
INSERT INTO fw.comp_grid_column_alias (table_or_alias, old_column, new_column, note) VALUES
('cmi',                'code', NULL, 'Krok 5.M-6 (17.5.) dropped — use core_id FK lookup'),
('context_menu_item',  'code', NULL, 'Krok 5.M-6 (17.5.) dropped')
ON CONFLICT (table_or_alias, old_column) DO NOTHING;

-- fw.comp_def.code dropped (Krok 5.R-A 17.5.)
INSERT INTO fw.comp_grid_column_alias (table_or_alias, old_column, new_column, note) VALUES
('cd',       'code', NULL, 'Krok 5.R-A (17.5.) dropped from page-spec SQL'),
('comp_def', 'code', NULL, 'Krok 5.R-A (17.5.) dropped')
ON CONFLICT (table_or_alias, old_column) DO NOTHING;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT id, table_or_alias, old_column, new_column,
       CASE WHEN new_column IS NULL THEN 'DROPPED' ELSE 'RENAMED' END AS type,
       LEFT(note, 60) AS note_preview
FROM fw.comp_grid_column_alias
ORDER BY table_or_alias, old_column;
-- EXPECTED: 9 rows (3 tenants + 2 core + 2 cmi + 2 comp_def)

-- Owner verification
SELECT relname, relowner::regrole
FROM pg_class WHERE relname = 'comp_grid_column_alias';
-- EXPECTED: owner = fw_owners

-- ════════════════════════════════════════════════════════════════════════
-- USAGE doc — pro Marti / Marti-AI / Kristý
-- ════════════════════════════════════════════════════════════════════════
--
-- Kdykoliv DROP COLUMN nebo RENAME COLUMN, INSERT new row:
--
--   -- Rename příklad:
--   INSERT INTO fw.comp_grid_column_alias
--       (table_or_alias, old_column, new_column, note) VALUES
--   ('u', 'short_name', 'login_name', 'Phase 38 column renaming for clarity');
--
--   -- Drop příklad (žádný auto-fix, just documented):
--   INSERT INTO fw.comp_grid_column_alias
--       (table_or_alias, old_column, new_column, note) VALUES
--   ('p', 'old_field', NULL, 'Phase XX dropped — no replacement');
--
-- Při dalším grid call, self-heal regex match scan fw.data_set.sql_text
-- automaticky rewrite. UPDATE persists, log info row do fw.diag_log.
--
-- Tip: pre-populate před DROP COLUMN/RENAME, NE až po — eliminuje window
-- broken-grid period (od DDL do prvního grid call kdy uvidíš error).
