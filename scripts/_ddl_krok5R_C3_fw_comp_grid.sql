-- Phase 38.4 Krok 5.R-C+3 (18.5.2026 vecer): erp_grid_layouts → fw.comp_grid
-- DDL pro Marti's DBeaver, run as Marti-AI session (db_owner fw schema).
--
-- Marti's doctrine: "PROSIM TE, nakonec dnes musime zpet prejmenovat na
-- fw.comp_grid Abychom drzeli doktrinu..."
--
-- Sequence (idempotent):
--   1) DROP fw.comp_grid_* orphans (4 nepoužívaných tabulek)
--   2) DROP public.erp_grid_layouts (0 rows po 5.R-C+2 DELETE)
--   3) CREATE fw.comp_grid (Marti-AI db_owner) + indexes
--   4) GRANT strategie SELECT + REFERENCES (C hybrid doctrine z 9.5.)
--   5) Verify final state

-- ════════════════════════════════════════════════════════════════════════════
-- Step 1: Drop fw.comp_grid_* orphans (Marti's audit z 18.5. vecer)
-- 4 tabulky bez code references — vznikly v Krok 13 design fazi
-- ════════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS fw.comp_grid_format_rule CASCADE;
DROP TABLE IF EXISTS fw.comp_grid_setting CASCADE;
DROP TABLE IF EXISTS fw.comp_grid_layout_part CASCADE;
DROP TABLE IF EXISTS fw.comp_grid_filter CASCADE;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 2: Drop public.erp_grid_layouts (0 rows po DELETE v 5.R-C+2)
-- ════════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS public.erp_grid_layouts CASCADE;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 3: Create fw.comp_grid (Marti-AI db_owner, schema replikace
-- z ErpGridLayout model)
-- ════════════════════════════════════════════════════════════════════════════

CREATE TABLE fw.comp_grid (
    id          BIGSERIAL PRIMARY KEY,

    -- Scope key (fw.core.id pro fw-driven grids, negative pro System hardcoded)
    core_id     INTEGER NOT NULL,

    -- User ownership: NULL = shared, INT = personal
    user_id     BIGINT,

    -- Name + popis (UI display)
    name        VARCHAR(80) NOT NULL,
    description TEXT,

    -- Default flag (auto-load pri otevreni gridu)
    is_default  BOOLEAN NOT NULL DEFAULT FALSE,

    -- Payload — AG Grid column state + style_rules + filters
    layout_json JSONB NOT NULL,

    -- Audit (Marti-AI's "ne anonymni" doctrine z 16.5.)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by  BIGINT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by  BIGINT NOT NULL
);

-- Indexes (replikace z modules/core/infrastructure/models_data.py)

-- Partial unique index: max 1 default per (core_id, user_id) scope
-- COALESCE pro shared (user_id IS NULL) — partial index trik
CREATE UNIQUE INDEX ux_comp_grid_default_per_scope
    ON fw.comp_grid (core_id, COALESCE(user_id, -1))
    WHERE is_default = true;

-- Unique name per scope (anti-duplicate)
CREATE UNIQUE INDEX ux_comp_grid_name_per_scope
    ON fw.comp_grid (core_id, COALESCE(user_id, -1), name);

-- Query support: list per scope
CREATE INDEX ix_comp_grid_core_user
    ON fw.comp_grid (core_id, user_id);

-- ════════════════════════════════════════════════════════════════════════════
-- Step 4: GRANT strategie role (C hybrid doctrine z 9.5.)
-- strategie smi cist (SELECT) + REFERENCES (FK definice),
-- ale write (INSERT/UPDATE/DELETE) musi pres strategie_pg layer (Marti-AI role).
-- ════════════════════════════════════════════════════════════════════════════

GRANT USAGE ON SCHEMA fw TO strategie;
GRANT SELECT, REFERENCES ON fw.comp_grid TO strategie;

-- ════════════════════════════════════════════════════════════════════════════
-- Step 5: Verify final state
-- ════════════════════════════════════════════════════════════════════════════

-- Confirm 0 rows v fw.comp_grid (clean slate)
SELECT 'fw.comp_grid rows: ' || COUNT(*) FROM fw.comp_grid;
-- expected: 0

-- Confirm 0 orphans v fw schema
SELECT table_name FROM information_schema.tables
 WHERE table_schema = 'fw' AND table_name LIKE 'comp_grid%';
-- expected: 1 row → "comp_grid"

-- Confirm public.erp_grid_layouts dropped
SELECT table_name FROM information_schema.tables
 WHERE table_schema = 'public' AND table_name = 'erp_grid_layouts';
-- expected: 0 rows

-- Confirm owner
SELECT t.tablename, t.tableowner
  FROM pg_tables t
 WHERE t.schemaname = 'fw' AND t.tablename = 'comp_grid';
-- expected: 1 row, tableowner = "Marti-AI"

-- ════════════════════════════════════════════════════════════════════════════
-- DONE. Po DDL:
--   - git pull origin main (cloud APP)
--   - Restart-Service STRATEGIE-API
--   - Smoke: otevri Uzivatele tab, klik + Uložit jako…
--     SELECT * FROM fw.comp_grid WHERE core_id = -110;  -- mela by se objevit row
-- ════════════════════════════════════════════════════════════════════════════
