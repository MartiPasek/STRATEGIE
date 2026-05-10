-- Phase 38.4 Krok 8 (10.5.2026 dopoledne): master.grid_column_meta
--
-- Centrála 1 pattern *„grid columns z DataSource"* — UI metadata pro
-- AG Grid columnDefs (label, default_width, pinned, formatter,
-- cell_style_rules) per column, per data_source.
--
-- Marti's korekce 10.5.: stavba ERP patří do master.*, ne public.
-- Diář pattern doctrine (Phase 30+ z 7.5. večer): master.* = framework,
-- Marti-AI je owner. Konzultace zatim přeskočena (jasné volby), ale
-- pokud později Marti-AI navrhne improvement, integrujeme.
--
-- Pattern (Marti's volby 10.5.):
--   1. Per-grid row (per data_source_code)
--   2. columns_meta JSONB obsahuje VŠECHNY sloupce daného gridu
--   3. struktura: {column_name: {label, default_width, pinned,
--      formatter, cell_style_rules, header_tooltip, column_order}}
--
-- FK na master.data_source.code (ve stejném schema, enforced).
--
-- Spustit jako Marti-AI login (db_owner master.* schema) přes:
--   - DBeaver SQL Editor
--   - NEBO Marti-AI chat: strategie_pg_create_table(...)

CREATE TABLE IF NOT EXISTS master.grid_column_meta (
    id SERIAL PRIMARY KEY,
    data_source_code VARCHAR(255) NOT NULL UNIQUE,
    columns_meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    default_record_limit INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- FK loose: master.data_source může mít víc verzí (UNIQUE code+version),
    -- tady stačí code (latest active). Pokud Marti-AI v budoucnu chce
    -- per-version meta, ALTER TABLE + version column.
    CONSTRAINT fk_grid_column_meta_data_source
        FOREIGN KEY (data_source_code)
        REFERENCES master.data_source (code)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_grid_column_meta_code
    ON master.grid_column_meta (data_source_code);

-- Comment pro dokumentaci
COMMENT ON TABLE master.grid_column_meta IS
    'Phase 38.4 Krok 8: per-grid UI column metadata (label, width, pinned, formatter). FK na master.data_source.code. Public app process (strategie role) má jen SELECT — DDL/INSERT/UPDATE patří Marti-AI.';

COMMENT ON COLUMN master.grid_column_meta.columns_meta IS
    'JSONB: {column_name: {label, default_width, pinned, formatter, cell_style_rules, header_tooltip, column_order}}';

-- GRANT pro strategie role (API process) — read-only
GRANT SELECT ON master.grid_column_meta TO strategie;
GRANT USAGE, SELECT ON SEQUENCE master.grid_column_meta_id_seq TO strategie;
