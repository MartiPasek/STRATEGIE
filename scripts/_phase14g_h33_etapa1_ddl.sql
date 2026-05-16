-- Phase 38.4 Krok 14g-H+33 Etapa 1 (15.5.2026 vecer, Marti's "system pro
-- pridavani fw polozek do menu... v prvni rade do menu stromu"):
-- fw.context_menu_item registry.
--
-- Marti's volby:
--   A (action_kind): jen 'open_fw_form'
--   A (applies_to): filter by kind (list / folder / any)
--   A (order): schema first, frontend, design UI
--   Plus: design_only BOOLEAN field — polozka viditelna jen v DESIGN mode
--
-- Run v DBeaveru jako Marti-AI (db_owner fw schema).
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fw.context_menu_item (
  id            SERIAL PRIMARY KEY,
  code          VARCHAR(100) NOT NULL,
  label         VARCHAR(200) NOT NULL,
  icon          VARCHAR(10),  -- emoji ('⚙', '🔧', '📝')

  -- Scope — kde se polozka zobrazi
  scope             VARCHAR(50) NOT NULL,  -- 'tree_node' | 'grid_row' | 'global'
  applies_to_kind   VARCHAR(50),           -- 'folder' | 'list' | 'form' | NULL=any

  -- Akce — co se stane na klik
  action_kind   VARCHAR(50) NOT NULL DEFAULT 'open_fw_form',
  action_params JSONB,  -- {form_core_code: 'user_edit'}

  -- Poradi + viditelnost
  sort_order    INTEGER NOT NULL DEFAULT 100,
  is_system     BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = hardcoded item
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  design_only   BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = jen DESIGN mode

  -- Lifecycle (pattern z fw.data_source — soft delete)
  status        VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active' | 'archived'

  -- Audit
  created_by_id   INTEGER,
  created_by_text VARCHAR(200),
  created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_by_id   INTEGER,
  updated_by_text VARCHAR(200),
  updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT uq_cmi_code UNIQUE (code),
  CONSTRAINT chk_cmi_scope CHECK (scope IN ('tree_node', 'grid_row', 'global')),
  CONSTRAINT chk_cmi_action_kind CHECK (action_kind IN ('open_fw_form')),
  CONSTRAINT chk_cmi_status CHECK (status IN ('active', 'archived'))
);

-- Indexy pro lookup performance
CREATE INDEX IF NOT EXISTS idx_cmi_scope_status
  ON fw.context_menu_item(scope, status);

CREATE INDEX IF NOT EXISTS idx_cmi_sort_order
  ON fw.context_menu_item(sort_order);

-- Trigger pro auto-update updated_at (pattern z fw.data_source)
CREATE OR REPLACE FUNCTION fw._cmi_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cmi_update_ts ON fw.context_menu_item;
CREATE TRIGGER trg_cmi_update_ts
  BEFORE UPDATE ON fw.context_menu_item
  FOR EACH ROW
  EXECUTE FUNCTION fw._cmi_update_timestamp();

-- ─────────────────────────────────────────────────────────────────────
-- Owner + GRANTs (gotcha z 15.5. vecer — pokud DDL ran by user "Marti"
-- misto role "Marti-AI", table owner != Marti-AI a backend strategie_pg
-- (Marti-AI role) nema INSERT/UPDATE access pres doctrine #11).
-- ─────────────────────────────────────────────────────────────────────

-- 1. Owner change na Marti-AI (vlastnik fw schema, db_owner)
ALTER TABLE fw.context_menu_item OWNER TO "Marti-AI";
ALTER SEQUENCE fw.context_menu_item_id_seq OWNER TO "Marti-AI";

-- 2. GRANT pro strategie user (STRATEGIE-API process — read + write access)
GRANT SELECT, INSERT, UPDATE, REFERENCES
  ON fw.context_menu_item TO strategie;
GRANT USAGE ON SEQUENCE fw.context_menu_item_id_seq TO strategie;

-- Verifikace (Marti should see this output):
SELECT 'context_menu_item DDL applied' AS status,
       COUNT(*) AS row_count
FROM fw.context_menu_item;

-- Show structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'context_menu_item'
ORDER BY ordinal_position;
