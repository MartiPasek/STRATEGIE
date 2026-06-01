-- ============================================================================
-- Fáze 3A (1.6.2026, Marti: telefon cross-device "klik na PC → vytočí mobil") —
-- fw.phone_dial_request: out-of-band fronta požadavků na vytočení. PC klik na
-- telefon → INSERT pending pro target_user_id (= sám sebe). Mobil (PWA chat)
-- pollne pending → ťukací banner → tel: dial → consume (done/dismissed).
--
-- Reuse poll pattern (jako notebook badge / doc inbox). Žádný nativní push.
--
-- Spustit v DBeaveru jako Marti-AI (owner fw schema) — celý skript najednou.
-- ============================================================================

CREATE TABLE IF NOT EXISTS fw.phone_dial_request (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_user_id  INTEGER NOT NULL,
    phone           VARCHAR(64) NOT NULL,
    raw_value       VARCHAR(128),
    label           VARCHAR(200),
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    consumed_at     TIMESTAMPTZ,
    CONSTRAINT chk_phone_dial_status
        CHECK (status IN ('pending', 'done', 'dismissed'))
);

CREATE INDEX IF NOT EXISTS ix_phone_dial_pending
    ON fw.phone_dial_request (target_user_id, status, created_at DESC);

ALTER TABLE fw.phone_dial_request OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON fw.phone_dial_request TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fw TO strategie;

-- Smoke:
-- INSERT INTO fw.phone_dial_request (target_user_id, phone, raw_value, label)
--   VALUES (1, '+420604222222', '604 222 222', 'Braun&Toth Absaugtechnik GmbH');
-- SELECT * FROM fw.phone_dial_request WHERE status='pending' ORDER BY id DESC;
