-- Phase 38.4 Krok 8 (10.5.2026 dopoledne): master grid framework
--
-- Centrála 1 pattern *„grid columns z DataSource"* + universal action mechanism
-- (system_action sdílený napříč grid / column / popup_menu / jadro).
--
-- 10 tabulek v master schema:
--   1. system_action_parent_registry  (polymorphism documentation)
--   2. grid_master                    (hlavička grid + 5 patterns + audit)
--   3. grid_column                    (sloupce, detail)
--   4. grid_layout_part               (header/footer/filter_row/toolbar)
--   5. grid_filter                    (predefined Záložkový přehled)
--   6. grid_format_rule               (conditional formatting)
--   7. grid_setting                   (generic key-value)
--   8. system_action                  (universal akce + 5 patterns + RLO chain)
--   9. system_action_param            (parameters)
--  10. system_action_stat             (write hot path izolovaný)
--
-- Plus: 2 trigger functions + 3 triggery (selektivní config_version increment
--       + updated_at auto-bump), 4 seed rows pro registry, GRANT pro strategie.
--
-- Marti-AI's konzultace přes 6 iterací (10.5.2026 ráno-dopoledne):
--   - Master+detail relacionální struktura (NE JSONB blob)
--   - Polymorphism + registry tabulka (NE multi-FK ani polymorphism without registry)
--   - Single TEXT default_value + closed CHECK na param_type
--   - system_action_stat separátní (write hot path izolovaný)
--   - parent_action_id self-ref + requires_prev_result tristate ('true'/'false'/'always')
--   - required_role + visible_condition_json (role-based + data-based visibility)
--   - 5 patterns napříč grid_master + system_action: tenant_id, is_system,
--     is_immutable, status, guid (ne na detail tabulky — kaskáda od master)
--   - Audit: created_by/updated_by INTEGER NULL (loose link, audit survival)
--   - View_mode: ('grid'/'list'/'card') CHECK
--
-- Marti's korekce 10.5.: stavba ERP patří do master.* (NE public)
-- Marti's pivot 10.5.: actions universal (NE grid-only duplicate)
-- Marti's volba: config_version rename (clarity vs data_source_version)
--
-- Spustit jako Marti-AI login (db_owner master.* schema) přes:
--   - DBeaver SQL Editor (Run All ve v jedné transakci)
--
-- Atomický transaction — Marti-AI's volba: pokud cokoli selže, rollback drží
-- čistý stav.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 0. POJISTKA — strategie role existence (P3 z Marti-AI's review)
-- ════════════════════════════════════════════════════════════════════════
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'strategie') THEN
        CREATE ROLE strategie;
    END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 1. REGISTRY — polymorphism documentation
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.system_action_parent_registry (
    parent_type VARCHAR(50) PRIMARY KEY,
    schema_name VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE master.system_action_parent_registry IS
    'Phase 38.4 Krok 8: parent_type → table mapping pro polymorphism. Marti-AI''s pojistka místo FK constraint. Přidání nové komponenty = INSERT, ne ALTER.';

-- ════════════════════════════════════════════════════════════════════════
-- 2. GRID MASTER — hlavička grid (5 patterns + audit + config_version)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_master (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(64) NOT NULL,
    config_version SMALLINT NOT NULL DEFAULT 1,
    name VARCHAR(255),
    description TEXT,
    -- FK na master.data_source (composite (code, version))
    data_source_code VARCHAR(64) NOT NULL,
    data_source_version INTEGER NOT NULL DEFAULT 1,
    -- Grid behavior
    default_record_limit INTEGER,
    refresh_type VARCHAR(50),
    default_sort_column VARCHAR(100),
    default_sort_direction VARCHAR(4) CHECK (default_sort_direction IN ('asc', 'desc')),
    default_view_mode VARCHAR(20) CHECK (default_view_mode IN ('grid', 'list', 'card')),
    -- Patterns (Marti-AI's 5. iter matice)
    tenant_id INTEGER,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_immutable BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(16) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'archived', 'deprecated')),
    guid UUID NOT NULL DEFAULT gen_random_uuid(),
    -- Audit
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Constraints
    CONSTRAINT uq_grid_master_code_config_version UNIQUE (code, config_version),
    CONSTRAINT uq_grid_master_guid UNIQUE (guid),
    CONSTRAINT fk_grid_master_data_source
        FOREIGN KEY (data_source_code, data_source_version)
        REFERENCES master.data_source (code, version) ON UPDATE CASCADE
);

CREATE INDEX idx_grid_master_tenant ON master.grid_master (tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_grid_master_status ON master.grid_master (status) WHERE status = 'active';

COMMENT ON TABLE master.grid_master IS
    'Phase 38.4 Krok 8: hlavička grid framework. config_version pro cache invalidation (selektivní trigger). 5 patterns (tenant/system/immutable/status/guid) napříč master.';

-- ════════════════════════════════════════════════════════════════════════
-- 3. GRID COLUMN — detail (žádné patterns kromě FK)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_column (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grid_master_id INTEGER NOT NULL REFERENCES master.grid_master(id) ON DELETE CASCADE,
    column_name VARCHAR(100) NOT NULL,
    label VARCHAR(255),
    default_width SMALLINT,
    min_width SMALLINT,
    flex SMALLINT,
    pinned VARCHAR(10) CHECK (pinned IN ('left', 'right')),
    formatter VARCHAR(50),
    header_tooltip TEXT,
    column_type VARCHAR(50),
    sort_order SMALLINT,
    is_visible BOOLEAN DEFAULT TRUE,
    is_sortable BOOLEAN DEFAULT TRUE,
    visible_roles JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_grid_column_master_name UNIQUE (grid_master_id, column_name)
);

CREATE INDEX idx_grid_column_master_id ON master.grid_column (grid_master_id);

COMMENT ON COLUMN master.grid_column.visible_roles IS
    'Array of role codes, e.g. ["admin","supervisor"]. NULL = visible to all.';

-- ════════════════════════════════════════════════════════════════════════
-- 4. GRID LAYOUT PART — header/footer/filter_row/toolbar (open enum)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_layout_part (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grid_master_id INTEGER NOT NULL REFERENCES master.grid_master(id) ON DELETE CASCADE,
    part_type VARCHAR(50) NOT NULL,
    is_visible BOOLEAN DEFAULT TRUE,
    sort_order SMALLINT,
    settings JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN master.grid_layout_part.part_type IS
    'Open enum: header / footer / filter_row / toolbar / sidebar / status_bar / context_menu / ...';

-- ════════════════════════════════════════════════════════════════════════
-- 5. GRID FILTER — predefined (Záložkový přehled)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_filter (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grid_master_id INTEGER NOT NULL REFERENCES master.grid_master(id) ON DELETE CASCADE,
    filter_name VARCHAR(255) NOT NULL,
    filter_json JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    role_scope VARCHAR(50),
    sort_order SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_grid_filter_master_name UNIQUE (grid_master_id, filter_name)
);

COMMENT ON COLUMN master.grid_filter.filter_json IS
    'AG Grid filter model — opaque blob (column → operator → value). Role scope NULL = visible to all.';

-- ════════════════════════════════════════════════════════════════════════
-- 6. GRID FORMAT RULE — conditional formatting (B+10+ doctrine)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_format_rule (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grid_master_id INTEGER NOT NULL REFERENCES master.grid_master(id) ON DELETE CASCADE,
    column_name VARCHAR(100) NOT NULL,
    condition_op VARCHAR(20) NOT NULL,
    condition_value TEXT,
    text_color VARCHAR(20),
    background_color VARCHAR(20),
    font_weight VARCHAR(10),
    sort_order SMALLINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════════════
-- 7. GRID SETTING — generic key-value (auto_refresh, row_height, ...)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.grid_setting (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grid_master_id INTEGER NOT NULL REFERENCES master.grid_master(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_grid_setting_master_key UNIQUE (grid_master_id, setting_key)
);

-- ════════════════════════════════════════════════════════════════════════
-- 8. SYSTEM ACTION — universal mechanism (Centrála 1 refactor)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.system_action (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    -- Polymorphism (registry-validated parent_type)
    parent_type VARCHAR(50) NOT NULL
        REFERENCES master.system_action_parent_registry(parent_type),
    parent_id INTEGER NOT NULL,
    -- Sequence chain (Marti-AI's blind spot A) + RLO IF/ELSE (tatínek)
    parent_action_id INTEGER REFERENCES master.system_action(id) ON DELETE CASCADE,
    requires_prev_result VARCHAR(20) NOT NULL DEFAULT 'always'
        CHECK (requires_prev_result IN ('true', 'false', 'always')),
    -- Behavior
    action_handler VARCHAR(100) NOT NULL,
    sort_order SMALLINT,
    is_visible BOOLEAN DEFAULT TRUE,
    visible_condition_json JSONB,
    required_role VARCHAR(100),
    -- Patterns
    tenant_id INTEGER,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_immutable BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(16) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'archived', 'deprecated')),
    guid UUID NOT NULL DEFAULT gen_random_uuid(),
    -- Audit
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Constraints
    CONSTRAINT uq_system_action_code_per_parent UNIQUE (parent_type, parent_id, code),
    CONSTRAINT uq_system_action_guid UNIQUE (guid)
);

CREATE INDEX idx_system_action_parent ON master.system_action (parent_type, parent_id);
CREATE INDEX idx_system_action_chain ON master.system_action (parent_action_id)
    WHERE parent_action_id IS NOT NULL;
CREATE INDEX idx_system_action_tenant ON master.system_action (tenant_id)
    WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_system_action_status ON master.system_action (status)
    WHERE status = 'active';

COMMENT ON TABLE master.system_action IS
    'Phase 38.4 Krok 8: universal action mechanism. Replaces Centrála 1 multi-FK pattern (ID_Komponenty/ID_PopupMenu/ID_Soudecku/ID_Formulare/Číslo Přehledu) by polymorphism + registry validation.';

COMMENT ON COLUMN master.system_action.visible_condition_json IS
    'JSONB condition for runtime visibility based on row data, e.g. {"field":"status","op":"eq","value":"draft"}. NULL = always visible.';

COMMENT ON COLUMN master.system_action.requires_prev_result IS
    'Sequence chain control (Centrála 1 ReakceNaRLO refactor): "true"=run if parent_action returned TRUE, "false"=run if FALSE, "always"=run regardless. Only meaningful when parent_action_id IS NOT NULL.';

-- ════════════════════════════════════════════════════════════════════════
-- 9. SYSTEM ACTION PARAM — parameters (single TEXT + closed CHECK)
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.system_action_param (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    action_id INTEGER NOT NULL REFERENCES master.system_action(id) ON DELETE CASCADE,
    param_name VARCHAR(100) NOT NULL,
    param_type VARCHAR(20) NOT NULL
        CHECK (param_type IN ('int', 'text', 'date', 'bool', 'sql_fragment', 'json')),
    default_value TEXT,
    condition_json JSONB,
    description TEXT,
    sort_order SMALLINT,
    CONSTRAINT uq_action_param_name UNIQUE (action_id, param_name)
);

-- ════════════════════════════════════════════════════════════════════════
-- 10. SYSTEM ACTION STAT — write hot path izolovaný
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE master.system_action_stat (
    action_id INTEGER PRIMARY KEY REFERENCES master.system_action(id) ON DELETE CASCADE,
    exec_count BIGINT NOT NULL DEFAULT 0,
    first_exec_at TIMESTAMPTZ,
    last_exec_at TIMESTAMPTZ,
    last_exec_user VARCHAR(100)
);

COMMENT ON TABLE master.system_action_stat IS
    'Write hot path izolovaný od config (system_action). Exec stats + last_exec_user pro debugging audit.';

-- ════════════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ════════════════════════════════════════════════════════════════════════

-- Selektivní config_version trigger (Marti-AI's volba A)
CREATE OR REPLACE FUNCTION master.bump_grid_master_config_version()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.default_record_limit IS DISTINCT FROM OLD.default_record_limit
        OR NEW.data_source_code IS DISTINCT FROM OLD.data_source_code
        OR NEW.data_source_version IS DISTINCT FROM OLD.data_source_version
        OR NEW.refresh_type IS DISTINCT FROM OLD.refresh_type
        OR NEW.default_sort_column IS DISTINCT FROM OLD.default_sort_column
        OR NEW.default_sort_direction IS DISTINCT FROM OLD.default_sort_direction
        OR NEW.default_view_mode IS DISTINCT FROM OLD.default_view_mode
        OR NEW.status IS DISTINCT FROM OLD.status) THEN
        NEW.config_version := OLD.config_version + 1;
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_grid_master_config_version
    BEFORE UPDATE ON master.grid_master
    FOR EACH ROW EXECUTE FUNCTION master.bump_grid_master_config_version();

-- Generic updated_at trigger (Marti-AI's Q7 pattern z 9.5.)
CREATE OR REPLACE FUNCTION master.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_grid_column_updated_at
    BEFORE UPDATE ON master.grid_column
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at();

CREATE TRIGGER trg_system_action_updated_at
    BEFORE UPDATE ON master.system_action
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at();

-- ════════════════════════════════════════════════════════════════════════
-- SEED — registry (4 default parent_types)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO master.system_action_parent_registry VALUES
    ('grid_master', 'master', 'grid_master', 'AG Grid definice (přehled)'),
    ('grid_column', 'master', 'grid_column', 'Grid sloupec (cell-level akce)'),
    ('popup_menu', 'master', 'menu_node', 'Popup menu group'),
    ('jadro', 'master', 'framework_jadro', 'ERP form/jádro');

-- ════════════════════════════════════════════════════════════════════════
-- GRANTS — strategie role (API process) read-only
-- ════════════════════════════════════════════════════════════════════════
GRANT SELECT ON ALL TABLES IN SCHEMA master TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA master TO strategie;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti-AI" IN SCHEMA master
    GRANT SELECT ON TABLES TO strategie;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti-AI" IN SCHEMA master
    GRANT USAGE, SELECT ON SEQUENCES TO strategie;

-- ════════════════════════════════════════════════════════════════════════
-- COMMIT
-- ════════════════════════════════════════════════════════════════════════
COMMIT;

-- Sanity check po execute (paste do dalšího SQL window):
-- SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'master'
--   ORDER BY table_name;
-- Expected: 9 puvodních + 10 novych = 19 tabulek (data_set, data_source,
-- data_source_operation, entity_def, framework_jadro, framework_komponenta,
-- framework_property, grid_column, grid_filter, grid_format_rule,
-- grid_layout_part, grid_master, grid_setting, komponenta_typ, menu_node,
-- system_action, system_action_param, system_action_parent_registry,
-- system_action_stat).
