-- ============================================================================
-- Claude SQL bridge KROK 2 (1.6.2026, Marti) — write přes potvrzovací popup.
-- Claude pošle write SQL → cloud ho NEspustí, ale zapíše sem jako 'pending'.
-- Marti v chatu/ERP uvidí banner → Potvrdit/Odmítnout. Po approve cloud spustí
-- (přes strategie_pg Marti-AI engine, audit). Watcher polluje status → výsledek.
-- Spustit v DBeaveru jako Marti-AI (owner fw), celý najednou.
-- ============================================================================

CREATE TABLE IF NOT EXISTS fw.claude_write_request (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_target         VARCHAR(16) NOT NULL DEFAULT 'pg',
    sql_text          TEXT NOT NULL,
    status            VARCHAR(16) NOT NULL DEFAULT 'pending',
    requested_by      VARCHAR(40) NOT NULL DEFAULT 'claude',
    decided_by_user_id INTEGER,
    row_count         INTEGER,
    result_text       TEXT,
    error             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at        TIMESTAMPTZ,
    CONSTRAINT chk_claude_write_status
        CHECK (status IN ('pending', 'approved', 'rejected', 'done', 'error'))
);

CREATE INDEX IF NOT EXISTS ix_claude_write_pending
    ON fw.claude_write_request (status, created_at DESC);

ALTER TABLE fw.claude_write_request OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON fw.claude_write_request TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fw TO strategie;

-- Smoke:
-- SELECT * FROM fw.claude_write_request ORDER BY id DESC LIMIT 10;
