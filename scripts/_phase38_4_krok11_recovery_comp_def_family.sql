-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 11 RECOVERY (11.5.2026 ~03:00 ráno)
-- ════════════════════════════════════════════════════════════════════════
-- Marti's noční DROP comp_def family bylo *„unahleni"* — recovery z:
--   1. Marti-AI chat log 10.5. 16:48-18:02 (schemy comp_def_prop + override)
--   2. Marti's DBeaver screenshot 10.5. večer (comp_def schema post-refactor)
--   3. Marti's tonight refactor (DROP jadro_id, RENAME typ → type_id, FK na comp_type)
--
-- Recovery option A — schema only + 1 Marti's AG_Grid row v comp_def.
-- Smoke test data (comp_def_prop id=1, override id=1) ne-recreated, protože
-- referují comp_def id=2 (security_devices 'user_name' column), který byl
-- auto-create přes Krok 9-B DO block — recreate vyžaduje plný re-link s
-- comp_grid_column (ALTER ADD comp_def_id + 47 backfill rows). Skip.
--
-- Spustit jako Marti-AI v DBeaveru s search_path = fw (Marti's fix dnes).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. fw.comp_def — TYPE-LEVEL component template registry
-- ════════════════════════════════════════════════════════════════════════
-- Marti's tonight refactor: žádný jadro_id, type_id FK na comp_type.
CREATE TABLE fw.comp_def (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_id INTEGER REFERENCES fw.comp_def(id),
    type_id INTEGER NOT NULL REFERENCES fw.comp_type(id),
    name VARCHAR(50) NOT NULL,
    caption VARCHAR(255),
    layout JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comp_def_type ON fw.comp_def(type_id);
CREATE INDEX idx_comp_def_parent ON fw.comp_def(parent_id)
    WHERE parent_id IS NOT NULL;

-- Marti's first row — AG_Grid template (id=1, type_id=101)
INSERT INTO fw.comp_def (id, type_id, name, caption, is_active)
OVERRIDING SYSTEM VALUE
VALUES (1, 101, 'AG_Grid', 'AG_Grid define component', TRUE);

SELECT setval('fw.comp_def_id_seq', 1, TRUE);

-- ════════════════════════════════════════════════════════════════════════
-- 2. fw.comp_def_prop — properties pro comp_def templates
-- ════════════════════════════════════════════════════════════════════════
-- Schema z Marti-AI's chat 10.5. 17:43:
--   id INT, komponenta_id INT NOT NULL, prop_name VARCHAR NOT NULL,
--   prop_value TEXT NULL, created_at TIMESTAMPTZ NOT NULL,
--   is_active BOOL, prop_type VARCHAR(20), created_by INT,
--   updated_at TIMESTAMPTZ, display_order SMALLINT, label VARCHAR(255)
CREATE TABLE fw.comp_def_prop (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    komponenta_id INTEGER NOT NULL REFERENCES fw.comp_def(id) ON DELETE CASCADE,
    prop_name VARCHAR(50) NOT NULL,
    prop_value TEXT,
    prop_type VARCHAR(20),
    label VARCHAR(255),
    display_order SMALLINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_comp_def_prop_kompo_name UNIQUE (komponenta_id, prop_name),
    CONSTRAINT ck_comp_def_prop_type CHECK (
        prop_type IS NULL OR prop_type IN
        ('string', 'int', 'bool', 'json', 'date', 'color', 'enum')
    )
);

CREATE INDEX idx_comp_def_prop_komponenta ON fw.comp_def_prop(komponenta_id);
CREATE INDEX idx_comp_def_prop_display_order ON fw.comp_def_prop
    (komponenta_id, display_order)
    WHERE is_active = TRUE;

-- Triggers — Marti-AI's Q5/Q7 9-iter doctrine
CREATE OR REPLACE FUNCTION fw.prevent_prop_name_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.prop_name IS DISTINCT FROM OLD.prop_name THEN
        RAISE EXCEPTION 'comp_def_prop.prop_name je immutable po insertu '
                        '(Marti-AI Q5 9.iter 10.5.). Změna display labelu '
                        'jde přes label sloupec, ne prop_name.';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_comp_def_prop_name_immutable
    BEFORE UPDATE ON fw.comp_def_prop
    FOR EACH ROW EXECUTE FUNCTION fw.prevent_prop_name_update();

CREATE TRIGGER trg_comp_def_prop_updated_at
    BEFORE UPDATE ON fw.comp_def_prop
    FOR EACH ROW EXECUTE FUNCTION fw.update_updated_at();

-- ════════════════════════════════════════════════════════════════════════
-- 3. fw.comp_def_prop_override — 4-tier scope override
-- ════════════════════════════════════════════════════════════════════════
-- Schema z Marti-AI's chat 10.5. 17:43:
--   id INT, comp_def_prop_id INT NOT NULL, tenant_group_id BIGINT,
--   tenant_id BIGINT, user_id BIGINT, override_value TEXT NOT NULL,
--   is_active BOOL, created_by INT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
CREATE TABLE fw.comp_def_prop_override (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    comp_def_prop_id INTEGER NOT NULL
        REFERENCES fw.comp_def_prop(id) ON DELETE CASCADE,
    tenant_group_id BIGINT,
    tenant_id BIGINT,
    user_id BIGINT,
    override_value TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_override_single_scope CHECK (
        (CASE WHEN tenant_group_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN tenant_id IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) = 1
    ),
    CONSTRAINT uq_override_group UNIQUE NULLS NOT DISTINCT
        (comp_def_prop_id, tenant_group_id),
    CONSTRAINT uq_override_tenant UNIQUE NULLS NOT DISTINCT
        (comp_def_prop_id, tenant_id),
    CONSTRAINT uq_override_user UNIQUE NULLS NOT DISTINCT
        (comp_def_prop_id, user_id),
    -- FK CASCADE na public refs (Phase 38.4 Krok 9-A doctrine)
    CONSTRAINT fk_cdpo_tenant
        FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_cdpo_user
        FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_cdpo_group ON fw.comp_def_prop_override (tenant_group_id)
    WHERE tenant_group_id IS NOT NULL;
CREATE INDEX idx_cdpo_tenant ON fw.comp_def_prop_override (tenant_id)
    WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_cdpo_user ON fw.comp_def_prop_override (user_id)
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_cdpo_active ON fw.comp_def_prop_override (comp_def_prop_id)
    WHERE is_active = TRUE;

CREATE TRIGGER trg_cdpo_updated_at
    BEFORE UPDATE ON fw.comp_def_prop_override
    FOR EACH ROW EXECUTE FUNCTION fw.update_updated_at();

-- ════════════════════════════════════════════════════════════════════════
-- 4. GRANTs pro strategie role (API process)
-- ════════════════════════════════════════════════════════════════════════
GRANT SELECT, INSERT, UPDATE, DELETE ON fw.comp_def TO strategie;
GRANT SELECT, INSERT, UPDATE, DELETE ON fw.comp_def_prop TO strategie;
GRANT SELECT, INSERT, UPDATE, DELETE ON fw.comp_def_prop_override TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.comp_def_id_seq TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.comp_def_prop_id_seq TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.comp_def_prop_override_id_seq TO strategie;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.comp_def) AS comp_def_count,
    (SELECT COUNT(*) FROM fw.comp_def_prop) AS comp_def_prop_count,
    (SELECT COUNT(*) FROM fw.comp_def_prop_override) AS override_count,
    (SELECT id FROM fw.comp_def WHERE id = 1) AS marti_first_row_id,
    (SELECT type_id FROM fw.comp_def WHERE id = 1) AS marti_first_row_type;
-- Expected:
--   comp_def_count: 1 (jen Marti's AG_Grid row id=1)
--   comp_def_prop_count: 0
--   override_count: 0
--   marti_first_row_id: 1
--   marti_first_row_type: 101
