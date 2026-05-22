-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 5.N-2 (22.5.2026 vecer — Marti's "čistý stůl za námi"):
-- fw.data_source.target_xxx columns pro universal save flow.
--
-- Doctrine z 17.5. Krok 5.N-1 (Marti's "code je optional, ID je truth"):
--   "Long-term plan: migrate config do fw.data_source.target_xxx columns
--    (Krok 5.N-2+) — vše v DB, žádný Python map."
--
-- Po Marti's Excel mode toggle (H+34) + save flow re-enable (H+35) =
-- universal pattern: každý fw.data_source explicit assignuje target_
-- schema/table/id_column. Backend resolver lookup pres JOIN
-- fw.core → fw.comp_def → fw.data_source.target_xxx.
--
-- Žádný Python hardcoded map. Drop _FW_FORM_CORE_REGISTRY (interim 17.5.).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── 1. ALTER TABLE: ADD 4 target_xxx sloupcu (vsechny nullable) ───────
ALTER TABLE fw.data_source
  ADD COLUMN IF NOT EXISTS target_schema      VARCHAR(63),
  ADD COLUMN IF NOT EXISTS target_table       VARCHAR(127),
  ADD COLUMN IF NOT EXISTS target_id_column   VARCHAR(63) DEFAULT 'id',
  ADD COLUMN IF NOT EXISTS target_select_columns TEXT[];

COMMENT ON COLUMN fw.data_source.target_schema IS
  'Cilove DB schema pro design_patch_entity save flow (Krok 5.N-2, 22.5.2026). NULL = no save flow (RO data_source).';
COMMENT ON COLUMN fw.data_source.target_table IS
  'Cilova tabulka pro save flow (UPDATE/INSERT cilova entity).';
COMMENT ON COLUMN fw.data_source.target_id_column IS
  'PK column name (default "id"). Pripadne "row_id" pro legacy tabulky.';
COMMENT ON COLUMN fw.data_source.target_select_columns IS
  'Whitelist sloupcu povolených pro PATCH field_changes (security gate proti password_hash leak atd.). NULL = no whitelist = libovolny column z body (servisni override).';

-- ─── 2. UPDATE existing data_sources — initial mappings ────────────────
-- System cores (SYSTEM NEW Etapa 3-9 z 21.5.):
UPDATE fw.data_source SET
  target_schema = 'public',
  target_table  = 'users',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'id', 'status', 'legal_name', 'first_name', 'last_name',
    'short_name', 'ews_email', 'ews_display_email',
    'trust_rating', 'is_marti_parent', 'is_admin',
    'last_active_tenant_id'
  ]
WHERE code = 'system_new.framework.security_users';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'diag_log',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'user_login_name', 'tenant_name', 'level', 'source',
    'module_id', 'module_version', 'message', 'status',
    'core_id', 'comp_def_id'
  ]
WHERE code = 'system_new.framework.diag_log';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'data_set',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'code', 'description', 'sql_text', 'db_connection_id', 'status'
  ]
WHERE code = 'system_new.framework.data_sets';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'data_source',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'code', 'name', 'description', 'refresh_type', 'status'
  ]
WHERE code = 'system_new.framework.data_sources_overview';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'db_connection',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'label', 'description', 'default_db', 'host', 'port',
    'login_name', 'scope_databases', 'is_active', 'sort_order', 'status'
  ]
WHERE code = 'system_new.framework_db_connections_list';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'menu_node',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'code', 'label', 'kind', 'parent_id', 'sort_order',
    'status', 'visibility_scope', 'core_id',
    'description_user', 'description_system'
  ]
WHERE code = 'system_new.framework.menu_node_list';

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'core',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'code', 'label', 'version', 'is_active', 'tenant_visibility',
    'description_user', 'description_system'
  ]
WHERE code IN ('framework_core_list', 'system_new.framework_core_list');

UPDATE fw.data_source SET
  target_schema = 'fw',
  target_table  = 'comp_def',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'name', 'caption', 'type_id', 'core_id', 'parent_comp_def_id',
    'region_slot', 'sort_order', 'is_active',
    'data_source_id', 'layout',
    'container_template_id', 'container_template_version',
    'layout_mode', 'refresh_strategy',
    'layout_x', 'layout_y', 'layout_w', 'layout_h'
  ]
WHERE code = 'framework_comp_def_list';

UPDATE fw.data_source SET
  target_schema = 'public',
  target_table  = 'knowledge_entry',
  target_id_column = 'id',
  target_select_columns = ARRAY[
    'topic_id', 'title', 'content', 'tags', 'status'
  ]
WHERE code = 'system_new.framework.knowledge_entries';

COMMIT;

-- ─── 3. VERIFY ─────────────────────────────────────────────────────────
SELECT id, code, target_schema, target_table, target_id_column,
       array_length(target_select_columns, 1) AS n_cols
FROM fw.data_source
WHERE target_table IS NOT NULL
ORDER BY target_schema, target_table;

-- Expect ~9 rows; NULL target_xxx data_sources = no save flow (PROD safe).
