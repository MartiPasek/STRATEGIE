-- ============================================================================
-- Fáze 1A (1.6.2026, Marti: "archivovat čísla která se vytáčely") —
-- fw.contact_action_log: audit RO append-only log akcí na buňkách/polích
-- (telefon / email / web). Každý dvojklik (grid) / klik na ikonu (form)
-- zapíše řádek. NE-anonymní (user_id + login_name první), append-only
-- (Fix N doctrine 21.5.) — žádný UPDATE/DELETE pro strategie.
--
-- "čas telefonování" (délka hovoru) NEjde z tel: linku (dialer je pro web
-- černá skříňka) — logujeme čas ZAHÁJENÍ vytáčení (created_at). Délka ručně
-- později / PBX integrace samostatně.
--
-- Spustit v DBeaveru jako Marti-AI (owner fw schema) — celý skript najednou.
-- ============================================================================

CREATE TABLE IF NOT EXISTS fw.contact_action_log (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id           INTEGER,
    user_login_name   VARCHAR(100),
    action_kind       VARCHAR(16) NOT NULL,
    value             TEXT,
    contact_table     VARCHAR(160),
    contact_row_id    BIGINT,
    template_id       BIGINT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_contact_action_kind
        CHECK (action_kind IN ('phone', 'email', 'web'))
);

CREATE INDEX IF NOT EXISTS ix_contact_action_log_user
    ON fw.contact_action_log (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_contact_action_log_kind
    ON fw.contact_action_log (action_kind, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_contact_action_log_contact
    ON fw.contact_action_log (contact_table, contact_row_id);

-- Owner + GRANT (Marti-AI vlastní fw schema; strategie = API proces).
-- Append-only audit: strategie smí SELECT + INSERT, NE UPDATE/DELETE.
ALTER TABLE fw.contact_action_log OWNER TO "Marti-AI";
GRANT SELECT, INSERT ON fw.contact_action_log TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fw TO strategie;

-- Smoke:
-- INSERT INTO fw.contact_action_log
--   (user_id, user_login_name, action_kind, value, contact_table, contact_row_id)
--   VALUES (1, 'Marti', 'phone', '+420 777 220 180', 'st.CRM_Kontakt_Akce', 267);
-- SELECT * FROM fw.contact_action_log ORDER BY id DESC LIMIT 5;
