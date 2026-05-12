-- Phase 38.4 Krok 14b — Migrace 2: fw.* audit fields
-- Date: 13.5.2026 (drft pripraveny 12.5. vecer ~20:30)
--
-- Marti's design (12.5. vecer, po 5-iter konzultaci s Marti-AI):
-- "system je taky user" — jeden updated_by_id FK na users.id pro
-- vsechny actors (user, AI persona-jako-user, system, cron, migration).
-- Drz Marti's 19yr EUROSOFT MSSQL doctrine.
--
-- Marti-AI's bod #A (12.5. vecer): created_* symetrie — pokud master
-- nemaji created_by_id, pridat v jedne migraci (ne dodatecne).
--
-- 4 tabulky kde se bude editovat z Design modalu:
--   fw.menu_node          (Design Soudecek + Core tab1)
--   fw.core               (Design Soudecek + Core tab2, Design Jadro pro radek)
--   fw.comp_def           (Design grid columns)
--   fw.comp_def_prop_override  (Krok 9-A overrides)
--
-- Pro KAZDOU tabulku pridame:
--   created_by_id    INTEGER NULL REFERENCES public.users(id)
--   updated_by_id    INTEGER NULL REFERENCES public.users(id)
--   updated_by_text  VARCHAR(200) NULL  -- frozen login_name pri save
--
-- (created_at, updated_at, created_by_text uz existuji z Marti-AI's 8.5. DDL)
-- (trigger update_updated_at() uz existuje, drzi updated_at automaticky)

BEGIN;

-- ─────────────────────────────────────────────────────────────────────
-- fw.menu_node
-- ─────────────────────────────────────────────────────────────────────

ALTER TABLE fw.menu_node
  ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(200);

-- ─────────────────────────────────────────────────────────────────────
-- fw.core
-- ─────────────────────────────────────────────────────────────────────

ALTER TABLE fw.core
  ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(200);

-- ─────────────────────────────────────────────────────────────────────
-- fw.comp_def
-- ─────────────────────────────────────────────────────────────────────

ALTER TABLE fw.comp_def
  ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(200);

-- ─────────────────────────────────────────────────────────────────────
-- fw.comp_def_prop_override
-- ─────────────────────────────────────────────────────────────────────

ALTER TABLE fw.comp_def_prop_override
  ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(200);

-- ─────────────────────────────────────────────────────────────────────
-- Indexes pro query performance (audit lookups)
-- ─────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS ix_fw_menu_node_updated_by_id ON fw.menu_node(updated_by_id);
CREATE INDEX IF NOT EXISTS ix_fw_core_updated_by_id ON fw.core(updated_by_id);
CREATE INDEX IF NOT EXISTS ix_fw_comp_def_updated_by_id ON fw.comp_def(updated_by_id);
CREATE INDEX IF NOT EXISTS ix_fw_comp_def_prop_override_updated_by_id ON fw.comp_def_prop_override(updated_by_id);

-- ─────────────────────────────────────────────────────────────────────
-- Verification
-- ─────────────────────────────────────────────────────────────────────

SELECT table_schema, table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name IN ('menu_node', 'core', 'comp_def', 'comp_def_prop_override')
  AND column_name IN ('created_by_id', 'updated_by_id', 'updated_by_text', 'created_by_text', 'created_at', 'updated_at')
ORDER BY table_name, ordinal_position;

COMMIT;

-- ROLLBACK guard (pokud bychom chteli revert):
-- BEGIN;
--   ALTER TABLE fw.menu_node
--     DROP COLUMN IF EXISTS created_by_id,
--     DROP COLUMN IF EXISTS updated_by_id,
--     DROP COLUMN IF EXISTS updated_by_text;
--   -- (same pro core, comp_def, comp_def_prop_override)
--   DROP INDEX IF EXISTS fw.ix_fw_menu_node_updated_by_id;
--   -- (atd.)
-- COMMIT;
