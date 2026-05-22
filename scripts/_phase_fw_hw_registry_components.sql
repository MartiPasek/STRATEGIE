-- Phase 22.5.2026 — fw.hw_registry component evidence
-- ════════════════════════════════════════════════════════════════════════
-- Marti's vize: centralni evidence FW + HW component celku, ktere je mozne
-- se specifickymi bindingami zavolat odkudkoli z fw. Additive postup:
-- minimum sloupcu (name + js_path + py_path + binding) + extend kind CHECK
-- o 'component' + seed 9 component celku (forms, pickers, modal, editors).
--
-- DDL strategy:
--   1. ADD name VARCHAR(80) (NULL → backfill z code → NOT NULL UNIQUE)
--   2. ADD js_path + py_path + binding (already done per Marti DDL run)
--   3. Extend kind CHECK pro 'component' (already done per Marti DDL run)
--   4. INSERT 9 component rows
--
-- NOTE: code zachovan zatim — drop later po Krok 5.O refactor (vazby
-- pres ID, ne code). Backward compat pro existing 'data'/'action' rows.
--
-- Spustit v DBeaveru (highlight + Alt+X) nebo psql.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. ADD name column (NULL → backfill → NOT NULL UNIQUE)
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.hw_registry
  ADD COLUMN IF NOT EXISTS name VARCHAR(80);

-- Backfill existing rows: name = code (1:1 pro start, drift later possible)
UPDATE fw.hw_registry SET name = code WHERE name IS NULL;

-- Enforce NOT NULL + UNIQUE
ALTER TABLE fw.hw_registry ALTER COLUMN name SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'hw_registry_name_unique'
      AND conrelid = 'fw.hw_registry'::regclass
  ) THEN
    ALTER TABLE fw.hw_registry ADD CONSTRAINT hw_registry_name_unique UNIQUE (name);
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 2. ADD js_path + py_path + binding (idempotent — Marti's DDL run hotovy,
--    ale IF NOT EXISTS pro safety)
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.hw_registry
  ADD COLUMN IF NOT EXISTS js_path VARCHAR(200),
  ADD COLUMN IF NOT EXISTS py_path VARCHAR(200),
  ADD COLUMN IF NOT EXISTS binding JSONB;

-- ════════════════════════════════════════════════════════════════════════
-- 3. Extend kind CHECK (idempotent — Marti's DDL hotovy, ale safe re-run)
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.hw_registry DROP CONSTRAINT IF EXISTS hw_registry_kind_check;
ALTER TABLE fw.hw_registry ADD CONSTRAINT hw_registry_kind_check
  CHECK (kind IN ('data', 'action', 'component'));

-- ════════════════════════════════════════════════════════════════════════
-- 4. Seed 9 component rows
-- ════════════════════════════════════════════════════════════════════════

INSERT INTO fw.hw_registry (code, name, label, kind, description, js_path, py_path, binding, is_active)
VALUES
  ('fw_form',
   'fw_form',
   'FW Form',
   'component',
   'FW data-driven form — renderuje z fw.core + fw.comp_def. Dnes: CORE 22 (user_edit), CORE 23 (core_design).',
   'components/design_forms.js',
   'fw_components/fw_form.py',
   '{"core_id": "int", "row_id": "int?"}'::jsonb,
   TRUE),

  ('soudecek_core_form',
   'soudecek_core_form',
   'Soudeček Core Form',
   'component',
   'Form 1+2 — menu_node design (Soudeček + Přehled + DataSource pickery).',
   'components/design_soudecek_core_form.js',
   'fw_components/soudecek_core_form.py',
   '{"menu_node_id": "int"}'::jsonb,
   TRUE),

  ('jadro_radek_form',
   'jadro_radek_form',
   'Jádro Řádek Form',
   'component',
   'Form 3 — sub-row detail (1:N joined tables, např. emails/phones na user).',
   'components/design_jadro_radek_form.js',
   'fw_components/jadro_radek_form.py',
   '{"parent_id": "int", "child_key": "str", "row_id": "int?"}'::jsonb,
   TRUE),

  ('data_source_editor',
   'data_source_editor',
   'Data Source Editor',
   'component',
   'Power tool — fw.data_source + fw.data_source_op SQL editor (Ace + param extract).',
   'components/design_data_source_editor.js',
   'fw_components/data_source_editor.py',
   '{"data_source_id": "int?"}'::jsonb,
   TRUE),

  ('data_set_editor',
   'data_set_editor',
   'Data Set Editor',
   'component',
   'Power tool — fw.data_set standalone SQL primitive editor.',
   'components/design_data_set_editor.js',
   'fw_components/data_set_editor.py',
   '{"data_set_id": "int?"}'::jsonb,
   TRUE),

  ('db_connection_editor',
   'db_connection_editor',
   'DB Connection Editor',
   'component',
   'Power tool — fw.db_connection config (URL + credentials).',
   'components/design_db_connection_editor.js',
   'fw_components/db_connection_editor.py',
   '{"db_connection_id": "int?"}'::jsonb,
   TRUE),

  ('field_picker_modal',
   'field_picker_modal',
   'Field Picker Modal',
   'component',
   'Helper modal — výběr fields z entity columns (FW form +Pole button).',
   'components/field_picker_modal.js',
   'fw_components/field_picker_modal.py',
   '{"entity_type": "str", "current_fields": "str[]"}'::jsonb,
   TRUE),

  ('catalog_picker',
   'catalog_picker',
   'Catalog Picker',
   'component',
   'Generic single-value picker — listing přes data_source + výběr ID.',
   'components/catalog_picker.js',
   'fw_components/catalog_picker.py',
   '{"data_source_id": "int", "initial_selected_id": "int?"}'::jsonb,
   TRUE),

  ('entity_picker',
   'entity_picker',
   'Entity Picker',
   'component',
   'FW entity picker s bidirectional binding (form save flow, field_extern column).',
   'components/entity_picker.js',
   'fw_components/entity_picker.py',
   '{"data_source_id": "int", "field_extern": "str?", "display_mode": "str"}'::jsonb,
   TRUE)
ON CONFLICT (name) DO UPDATE SET
  label       = EXCLUDED.label,
  description = EXCLUDED.description,
  js_path     = EXCLUDED.js_path,
  py_path     = EXCLUDED.py_path,
  binding     = EXCLUDED.binding,
  updated_at  = NOW();

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- 5. Verify (run separately po COMMIT)
-- ════════════════════════════════════════════════════════════════════════
-- SELECT
--     id,
--     kind,
--     name,
--     label,
--     js_path,
--     py_path,
--     binding,
--     is_active
-- FROM fw.hw_registry
-- WHERE kind = 'component'
-- ORDER BY name;
--
-- Expected: 9 rows
--
-- Schema check:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema = 'fw' AND table_name = 'hw_registry'
-- ORDER BY ordinal_position;
