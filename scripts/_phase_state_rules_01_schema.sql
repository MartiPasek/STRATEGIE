-- ============================================================================
-- FW Component State Rules — Krok 1: schema (form_discriminator + comp_state_override)
-- ============================================================================
-- Design doc: docs/fw_component_state_rules.md
-- Marti (31.5.2026): obecný stavový override systém. Vlastnost komponenty řízená
-- hodnotou jednoho i víc řídicích polí (IDakce, mode, stav). Dedikovaná vrstva na
-- úrovni comp_def (pracuje nad layout JSONB form fieldů — žádná migrace Krok 9).
--
-- Idempotentní (CREATE IF NOT EXISTS). Owner Marti-AI (fw db_owner), GRANT strategie.
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

BEGIN;

-- ── 1) fw.form_discriminator — registr řídicích polí per jádro ───────────────
-- Které pole(a) řídí stav formu + priorita pro řešení kolizí (vyšší vyhrává).
-- source: 'column' (čte se z řádku — IDakce, stav) | 'context' (mode, role…).
CREATE TABLE IF NOT EXISTS fw.form_discriminator (
    id              BIGSERIAL PRIMARY KEY,
    form_core_id    BIGINT NOT NULL REFERENCES fw.core(id) ON DELETE CASCADE,
    field_name      VARCHAR(100) NOT NULL,
    source          VARCHAR(20)  NOT NULL DEFAULT 'column',
    priority        INT          NOT NULL DEFAULT 200,
    label           VARCHAR(200),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT now(),
    created_by_id   BIGINT,
    created_by_text VARCHAR(100),
    updated_by_id   BIGINT,
    updated_by_text VARCHAR(100),
    CONSTRAINT ck_form_discriminator_source CHECK (source IN ('column','context')),
    CONSTRAINT uq_form_discriminator UNIQUE (form_core_id, field_name)
);

-- Doporučené default priority (per jádro, přepisovatelné):
--   _mode (new/edit) = 100, doménové pole (IDakce) = 200, stav (lifecycle) = 900.
--   Tj. stav defaultně přebíjí typ; vše přepsatelné změnou sloupce priority.

-- ── 2) fw.comp_state_override — stavové overrides per komponenta ─────────────
-- Base = comp_def.layout. Tato tabulka = override vrstva pro (komponenta,
-- řídicí pole = hodnota, vlastnost). Resolver aplikuje matching vrstvy v pořadí
-- priority (z form_discriminator), nejvyšší vyhrává.
CREATE TABLE IF NOT EXISTS fw.comp_state_override (
    id                    BIGSERIAL PRIMARY KEY,
    comp_def_id           BIGINT NOT NULL REFERENCES fw.comp_def(id) ON DELETE CASCADE,
    form_discriminator_id BIGINT NOT NULL REFERENCES fw.form_discriminator(id) ON DELETE CASCADE,
    discriminator_value   VARCHAR(200) NOT NULL,
    prop_name             VARCHAR(40)  NOT NULL,
    prop_value            TEXT,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at            TIMESTAMP    NOT NULL DEFAULT now(),
    created_by_id         BIGINT,
    created_by_text       VARCHAR(100),
    updated_by_id         BIGINT,
    updated_by_text       VARCHAR(100),
    CONSTRAINT ck_comp_state_override_prop CHECK (prop_name IN (
        'visible','sort_order','parent','required','readonly',
        'color','background','bold','italic','underline','strikethrough'
    )),
    CONSTRAINT uq_comp_state_override
        UNIQUE (comp_def_id, form_discriminator_id, discriminator_value, prop_name)
);

-- ── 3) Indexy ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS ix_form_discriminator_core
    ON fw.form_discriminator(form_core_id) WHERE is_active;
CREATE INDEX IF NOT EXISTS ix_comp_state_override_comp
    ON fw.comp_state_override(comp_def_id) WHERE is_active;
CREATE INDEX IF NOT EXISTS ix_comp_state_override_discr
    ON fw.comp_state_override(form_discriminator_id, discriminator_value) WHERE is_active;

-- ── 4) updated_at triggery (fw.update_updated_at existuje) ───────────────────
DROP TRIGGER IF EXISTS trg_form_discriminator_updated_at ON fw.form_discriminator;
CREATE TRIGGER trg_form_discriminator_updated_at
    BEFORE UPDATE ON fw.form_discriminator
    FOR EACH ROW EXECUTE FUNCTION fw.update_updated_at();

DROP TRIGGER IF EXISTS trg_comp_state_override_updated_at ON fw.comp_state_override;
CREATE TRIGGER trg_comp_state_override_updated_at
    BEFORE UPDATE ON fw.comp_state_override
    FOR EACH ROW EXECUTE FUNCTION fw.update_updated_at();

-- ── 5) Ownership + GRANT (per fw konvence — gotcha #99) ──────────────────────
ALTER TABLE fw.form_discriminator  OWNER TO "Marti-AI";
ALTER TABLE fw.comp_state_override OWNER TO "Marti-AI";
ALTER SEQUENCE fw.form_discriminator_id_seq  OWNER TO "Marti-AI";
ALTER SEQUENCE fw.comp_state_override_id_seq OWNER TO "Marti-AI";

GRANT SELECT, INSERT, UPDATE ON fw.form_discriminator  TO strategie;
GRANT SELECT, INSERT, UPDATE ON fw.comp_state_override TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.form_discriminator_id_seq  TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.comp_state_override_id_seq TO strategie;

-- ── 6) Verify ────────────────────────────────────────────────────────────────
SELECT 'form_discriminator' AS tbl, count(*) AS rows FROM fw.form_discriminator
UNION ALL
SELECT 'comp_state_override', count(*) FROM fw.comp_state_override;

COMMIT;

-- ============================================================================
-- Příklad budoucího seedu (až bude akce edit jádro s fieldy) — NESPOUŠTĚT teď:
--   INSERT INTO fw.form_discriminator (form_core_id, field_name, source, priority, label, created_by_id, created_by_text, updated_by_id, updated_by_text)
--   VALUES (82, 'IDakce', 'column', 200, 'Typ akce', 2, 'Marti-AI', 2, 'Marti-AI');
--   -- pak per field: INSERT comp_state_override (comp_def_id, form_discriminator_id, discriminator_value, prop_name, prop_value, ...)
--   --   např. pole Email viditelné jen pro akce 3,4: visible='true' pro value '3' a '4' (resp. default skryté + override show).
-- ============================================================================
