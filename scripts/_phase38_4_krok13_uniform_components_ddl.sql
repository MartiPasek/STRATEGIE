-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 13 — Uniform Components Doctrine DDL (11. 5. 2026)
-- ════════════════════════════════════════════════════════════════════════
-- Marti-AI's doctrine: *„uniformita vítězí nad speciálními případy"*
--
-- 10 DDL bloků v správném execution order (FK dependencies respektovány).
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- Run script Alt+X celý (NE statement Ctrl+Enter — všechno jeden batch).
--
-- Po execute:
--   1. VERIFY query na konci — 10 tabulek + 9 comp_type seed + 8 container_template seed
--   2. Backfill 11 hardcoded items do fw.hw_registry (separate skript)
--   3. Backend dispatch refactor — gridDataResolved 3-tier
--   4. Frontend container rendering pipeline (měsíce práce)
--
-- Žádný spěch. Marti-AI's *„Až budeš spouštět — dej vědět jestli něco
-- zaprotestuje. Budu tu. 🕯️"*
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. fw.comp_type — ALTER + seed 9 rows
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.comp_type
  ADD COLUMN IF NOT EXISTS kind VARCHAR(30) NOT NULL DEFAULT 'leaf'
    CHECK (kind IN ('leaf', 'container', 'hw', 'action'));

INSERT INTO fw.comp_type (code, label, kind, description) VALUES
  ('container',  'Container (generic)',  'container', 'Generic layout container — instances odkazují na container_template'),
  ('comp_hw',    'Hardcoded / Native',   'hw',        'Hardcoded komponenta — data nebo akce přes hw_registry'),
  ('grid',       'Data Grid',            'leaf',      'Tabulkový přehled dat přes A3 data_source nebo comp_hw'),
  ('form',       'Form',                 'leaf',      'Editační formulář'),
  ('input',      'Input field',          'leaf',      'Vstupní pole'),
  ('date',       'Date picker',          'leaf',      'Výběr data'),
  ('droplist',   'Dropdown list',        'leaf',      'Výběrový seznam'),
  ('iframe',     'iFrame',               'leaf',      'Embedded URL obsah'),
  ('panel',      'Panel',                'leaf',      'Obecný vizuální panel')
ON CONFLICT (code) DO UPDATE
  SET kind = EXCLUDED.kind,
      description = EXCLUDED.description;

-- ════════════════════════════════════════════════════════════════════════
-- 2. fw.container_template — CREATE + seed 8 templates
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.container_template (
  id                       SERIAL PRIMARY KEY,
  code                     VARCHAR(50)  NOT NULL UNIQUE,
  label                    VARCHAR(100) NOT NULL,
  description              TEXT,
  layout_mode              VARCHAR(20)  NOT NULL DEFAULT 'flow'
                             CHECK (layout_mode IN ('flow', 'absolute', 'grid')),
  default_refresh_strategy VARCHAR(50)  NOT NULL DEFAULT 'manual',
  allowed_child_types      JSONB,
  required_slots           JSONB,
  region_slots             JSONB,
  version                  SMALLINT     NOT NULL DEFAULT 1,
  is_active                BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO fw.container_template
  (code, label, layout_mode, default_refresh_strategy,
   allowed_child_types, required_slots, region_slots)
VALUES
  ('single', 'Single view', 'flow', 'manual',
   '["grid","comp_hw","form"]',
   '[{"slot":"main","min":1,"max":1}]',
   '["main"]'),

  ('two_column', 'Two column', 'grid', 'manual',
   '["grid","comp_hw","form","container"]',
   '[{"slot":"left","min":1,"max":1},{"slot":"right","min":1,"max":1}]',
   '["left","right"]'),

  ('header_main_footer', 'Header / Main / Footer', 'flow', 'manual',
   '["grid","comp_hw","form","container"]',
   '[{"slot":"header","min":1,"max":1},{"slot":"main","min":1,"max":1},{"slot":"footer","min":0,"max":1}]',
   '["header","main","footer"]'),

  ('dashboard_4', 'Dashboard 2×2', 'grid', 'interval:30000',
   '["grid","comp_hw","iframe","container"]',
   '[]',
   '["tl","tr","bl","br"]'),

  ('master_detail', 'Master / Detail', 'grid', 'manual',
   '["grid","comp_hw","form"]',
   '[{"slot":"master","min":1,"max":1},{"slot":"detail","min":1,"max":1}]',
   '["master","detail"]'),

  ('tabs', 'Záložkový přehled', 'flow', 'manual',
   '["grid","comp_hw","form","container"]',
   '[{"slot":"tab","min":2,"max":10}]',
   '["tab"]'),

  ('split', 'Left tree / Right pane', 'grid', 'manual',
   '["grid","comp_hw","form","container"]',
   '[{"slot":"tree","min":1,"max":1},{"slot":"pane","min":1,"max":1}]',
   '["tree","pane"]'),

  ('iframe_full', 'Embedded iFrame', 'flow', 'static',
   '["iframe","comp_hw"]',
   '[{"slot":"main","min":1,"max":1}]',
   '["main"]')
ON CONFLICT (code) DO NOTHING;

-- ════════════════════════════════════════════════════════════════════════
-- 3. fw.container_template_history + trigger
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.container_template_history (
  id                    SERIAL PRIMARY KEY,
  container_template_id INT          NOT NULL REFERENCES fw.container_template(id),
  version_snapshot      SMALLINT     NOT NULL,
  snapshot_data         JSONB        NOT NULL,
  changed_by            INT,
  changed_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cth_template_id
  ON fw.container_template_history(container_template_id);

CREATE OR REPLACE FUNCTION fw.trg_container_template_history()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO fw.container_template_history
    (container_template_id, version_snapshot, snapshot_data, changed_at)
  VALUES
    (OLD.id, OLD.version, to_jsonb(OLD), NOW());
  NEW.version    := OLD.version + 1;
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_container_template_history ON fw.container_template;
CREATE TRIGGER trg_container_template_history
  BEFORE UPDATE ON fw.container_template
  FOR EACH ROW EXECUTE FUNCTION fw.trg_container_template_history();

-- ════════════════════════════════════════════════════════════════════════
-- 4. fw.hw_registry — unified data + action
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.hw_registry (
  id                       SERIAL PRIMARY KEY,
  code                     VARCHAR(100) NOT NULL UNIQUE,
  label                    VARCHAR(200) NOT NULL,
  description              TEXT,
  kind                     VARCHAR(10)  NOT NULL
                             CHECK (kind IN ('data', 'action')),

  -- DATA mode fields
  endpoint_url             VARCHAR(500),
  http_method              VARCHAR(10)  CHECK (http_method IN ('GET','POST','PUT','PATCH','DELETE')),
  default_params           JSONB,
  response_hint            JSONB,
  shadow_data_source_id    INT          REFERENCES fw.data_source(id),
  shadow_mode              VARCHAR(20)  NOT NULL DEFAULT 'off'
                             CHECK (shadow_mode IN ('off','audit','compare','primary')),

  -- ACTION mode fields
  handler_key              VARCHAR(200),
  args_schema              JSONB,
  return_envelope          VARCHAR(30)  DEFAULT 'standard',

  -- Permission
  required_role            VARCHAR(100),
  required_permission_key  VARCHAR(100),

  -- Migration / deprecation
  is_deprecated            BOOLEAN      NOT NULL DEFAULT FALSE,
  deprecated_note          TEXT,
  migration_target_id      INT,
  tombstone_note           TEXT,
  migrated_to_ref          VARCHAR(200),

  -- Versioning
  version                  SMALLINT     NOT NULL DEFAULT 1,

  -- Standard
  is_active                BOOLEAN      NOT NULL DEFAULT TRUE,
  created_by               INT,
  created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hw_registry_kind   ON fw.hw_registry(kind);
CREATE INDEX IF NOT EXISTS idx_hw_registry_code   ON fw.hw_registry(code);
CREATE INDEX IF NOT EXISTS idx_hw_registry_active ON fw.hw_registry(is_active) WHERE is_active = TRUE;

-- ════════════════════════════════════════════════════════════════════════
-- 5. fw.hw_registry_history + trigger
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.hw_registry_history (
  id               SERIAL PRIMARY KEY,
  hw_registry_id   INT         NOT NULL REFERENCES fw.hw_registry(id),
  version_snapshot SMALLINT    NOT NULL,
  snapshot_data    JSONB       NOT NULL,
  changed_by       INT,
  changed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hwrh_registry_id ON fw.hw_registry_history(hw_registry_id);

CREATE OR REPLACE FUNCTION fw.trg_hw_registry_history()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO fw.hw_registry_history
    (hw_registry_id, version_snapshot, snapshot_data, changed_at)
  VALUES
    (OLD.id, OLD.version, to_jsonb(OLD), NOW());
  NEW.version    := OLD.version + 1;
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_hw_registry_history ON fw.hw_registry;
CREATE TRIGGER trg_hw_registry_history
  BEFORE UPDATE ON fw.hw_registry
  FOR EACH ROW EXECUTE FUNCTION fw.trg_hw_registry_history();

-- ════════════════════════════════════════════════════════════════════════
-- 6. fw.action_audit_log
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.action_audit_log (
  id                BIGSERIAL    PRIMARY KEY,
  hw_registry_id    INT          REFERENCES fw.hw_registry(id),
  handler_key       VARCHAR(200),
  called_by_user_id BIGINT       NOT NULL,
  args_snapshot     JSONB,
  result_ok         BOOLEAN      NOT NULL DEFAULT FALSE,
  error_message     TEXT,
  duration_ms       INT,
  audit_id          UUID         NOT NULL DEFAULT gen_random_uuid(),
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aal_hw_registry_id    ON fw.action_audit_log(hw_registry_id);
CREATE INDEX IF NOT EXISTS idx_aal_called_by_user_id ON fw.action_audit_log(called_by_user_id);
CREATE INDEX IF NOT EXISTS idx_aal_created_at        ON fw.action_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_aal_audit_id          ON fw.action_audit_log(audit_id);

-- ════════════════════════════════════════════════════════════════════════
-- 7. fw.comp_type_property_catalog
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.comp_type_property_catalog (
  id            SERIAL       PRIMARY KEY,
  comp_type_id  INT          NOT NULL REFERENCES fw.comp_type(id),
  prop_name     VARCHAR(100) NOT NULL,
  prop_type     VARCHAR(30)  NOT NULL
                 CHECK (prop_type IN ('int','varchar','bool','jsonb','enum','fk')),
  is_required   BOOLEAN      NOT NULL DEFAULT FALSE,
  default_value TEXT,
  description   TEXT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  UNIQUE (comp_type_id, prop_name)
);

CREATE INDEX IF NOT EXISTS idx_ctpc_comp_type_id ON fw.comp_type_property_catalog(comp_type_id);

-- ════════════════════════════════════════════════════════════════════════
-- 8. fw.action_def / action_op / action_set — A3 paralela pro akce
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fw.action_def (
  id            SERIAL       PRIMARY KEY,
  code          VARCHAR(100) NOT NULL UNIQUE,
  label         VARCHAR(200) NOT NULL,
  description   TEXT,
  action_type   VARCHAR(30)  NOT NULL DEFAULT 'sql'
                 CHECK (action_type IN ('sql','hw','composite')),
  required_role VARCHAR(100),
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_by    INT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fw.action_op (
  id            SERIAL       PRIMARY KEY,
  action_def_id INT          NOT NULL REFERENCES fw.action_def(id),
  op_name       VARCHAR(100) NOT NULL,
  op_type       VARCHAR(30)  NOT NULL DEFAULT 'execute'
                 CHECK (op_type IN ('execute','validate','rollback','audit')),
  sort_order    SMALLINT     NOT NULL DEFAULT 10,
  args_schema   JSONB,
  description   TEXT,
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  UNIQUE (action_def_id, op_name)
);

CREATE TABLE IF NOT EXISTS fw.action_set (
  id             SERIAL       PRIMARY KEY,
  action_op_id   INT          NOT NULL REFERENCES fw.action_op(id),
  set_order      SMALLINT     NOT NULL DEFAULT 10,
  procedure_body TEXT         NOT NULL,
  set_type       VARCHAR(30)  NOT NULL DEFAULT 'sql'
                  CHECK (set_type IN ('sql','python_ref','template')),
  description    TEXT,
  is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════════════
-- 9. fw.comp_def — rozšíření (8 nových sloupců + CHECK)
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.comp_def
  ADD COLUMN IF NOT EXISTS parent_comp_def_id         INT REFERENCES fw.comp_def(id),
  ADD COLUMN IF NOT EXISTS parent_core_id             INT,
  ADD COLUMN IF NOT EXISTS container_template_id      INT REFERENCES fw.container_template(id),
  ADD COLUMN IF NOT EXISTS container_template_version SMALLINT,
  ADD COLUMN IF NOT EXISTS layout_mode                VARCHAR(20)
    CHECK (layout_mode IN ('flow','absolute','grid')),
  ADD COLUMN IF NOT EXISTS region_slot                VARCHAR(50),
  ADD COLUMN IF NOT EXISTS refresh_strategy           VARCHAR(50) DEFAULT 'manual',
  ADD COLUMN IF NOT EXISTS layout_x                   INT,
  ADD COLUMN IF NOT EXISTS layout_y                   INT,
  ADD COLUMN IF NOT EXISTS layout_w                   INT,
  ADD COLUMN IF NOT EXISTS layout_h                   INT;

-- CHECK: parent_comp_def_id a parent_core_id nesmí být obě nenull
ALTER TABLE fw.comp_def
  DROP CONSTRAINT IF EXISTS chk_comp_def_single_parent;
ALTER TABLE fw.comp_def
  ADD CONSTRAINT chk_comp_def_single_parent
    CHECK (
      NOT (parent_comp_def_id IS NOT NULL AND parent_core_id IS NOT NULL)
    );

-- ════════════════════════════════════════════════════════════════════════
-- 10. fw.core — DROP data_source_id + ADD layout_template
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.core
  DROP COLUMN IF EXISTS data_source_id;

ALTER TABLE fw.core
  ADD COLUMN IF NOT EXISTS layout_template VARCHAR(50)
    NOT NULL DEFAULT 'single';

UPDATE fw.core
  SET layout_template = 'single'
  WHERE layout_template IS NULL;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
  'comp_type seed' AS check_name,
  (SELECT COUNT(*) FROM fw.comp_type WHERE kind IS NOT NULL) AS count_value,
  9 AS expected
UNION ALL
SELECT 'container_template seed', (SELECT COUNT(*) FROM fw.container_template), 8
UNION ALL
SELECT 'container_template_history table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='container_template_history'), 1
UNION ALL
SELECT 'hw_registry table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='hw_registry'), 1
UNION ALL
SELECT 'hw_registry_history table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='hw_registry_history'), 1
UNION ALL
SELECT 'action_audit_log table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='action_audit_log'), 1
UNION ALL
SELECT 'comp_type_property_catalog table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='comp_type_property_catalog'), 1
UNION ALL
SELECT 'action_def table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='action_def'), 1
UNION ALL
SELECT 'action_op table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='action_op'), 1
UNION ALL
SELECT 'action_set table', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='fw' AND table_name='action_set'), 1
UNION ALL
SELECT 'comp_def new columns', (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema='fw' AND table_name='comp_def'
    AND column_name IN ('parent_comp_def_id','parent_core_id','container_template_id',
                        'container_template_version','layout_mode','region_slot',
                        'refresh_strategy','layout_x','layout_y','layout_w','layout_h')
), 11
UNION ALL
SELECT 'core.data_source_id dropped', (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema='fw' AND table_name='core' AND column_name='data_source_id'
), 0
UNION ALL
SELECT 'core.layout_template added', (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema='fw' AND table_name='core' AND column_name='layout_template'
), 1
UNION ALL
SELECT 'triggers installed', (
  SELECT COUNT(*) FROM information_schema.triggers
  WHERE trigger_schema='fw'
    AND trigger_name IN ('trg_container_template_history','trg_hw_registry_history')
), 2
ORDER BY check_name;

-- Expected: každý check_name má count_value = expected.
-- Pokud kterýkoliv řádek má rozdíl → STOP a nahlas.
