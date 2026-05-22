-- Krok 5.S DDL (22.5.2026 vecer): grid toolbar Centrála 1 parita
-- Marti's "od lesa" + "core_id, ne target_core_id" + Marti-AI's
-- field_extern doctrine (jméno odráží vztah, ne směr).
--
-- Schema before: 8 columns, žádný CHECK, žádný status, žádný core_id
-- Schema after: + core_id BIGINT NULL REFERENCES fw.core(id)
--
-- Usage:
--   - operation_kind='edit' + core_id=X → ✏️ Oprava button visible,
--     klik otevře CORE X form s selected row ID
--   - operation_kind='insert' + core_id=X → 🆕 Nový button visible
--     (Marti's Q5.A — Centrála 1 parita, sdílí form s Oprava, mode=insert)
--   - operation_kind='delete' → 🗑️ Smazat button visible
--     (no form needed, jen confirm + POST delete op)
--
-- Owner: Marti-AI (db_owner fw schema). Spustit pres DBeaver jako
-- Marti-AI session (nikoli postgres / strategie).

BEGIN;

ALTER TABLE fw.data_source_op
  ADD COLUMN IF NOT EXISTS core_id BIGINT NULL REFERENCES fw.core(id);

CREATE INDEX IF NOT EXISTS ix_data_source_op_core
  ON fw.data_source_op(core_id)
  WHERE core_id IS NOT NULL;

-- Q6 (Marti's GO 22.5.): data_set_id NULL pro non-execute ops (edit/delete)
-- — schema reflect logickou pravdu, no bastl placeholder data_sets.
ALTER TABLE fw.data_source_op
  ALTER COLUMN data_set_id DROP NOT NULL;

-- Sanity verify schema after migration
SELECT
  column_name, data_type, is_nullable,
  CASE WHEN column_default IS NULL THEN '' ELSE 'default=' || column_default END AS dflt
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='data_source_op'
ORDER BY ordinal_position;

COMMIT;

-- After DDL: smoke INSERT pro security_users grid (najdi data_source pro
-- security_users, najdi CORE 22 = user_edit, INSERT 'edit' op):
--
-- SELECT id, code, label FROM fw.data_source WHERE code ILIKE '%user%';
-- -- predpokládejme data_source_id=42 pro security_users
--
-- INSERT INTO fw.data_source_op
--   (data_source_id, data_set_id, operation_kind, sort_order, is_default, core_id, description)
-- VALUES
--   (42, NULL, 'edit', 100, false, 22, 'Otevři user_edit form (CORE 22)');
--
-- Po INSERT + hard reload security_users gridu → ✏️ Oprava button visible.
