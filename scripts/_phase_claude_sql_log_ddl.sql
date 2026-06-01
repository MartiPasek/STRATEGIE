-- ============================================================================
-- Claude SQL bridge (1.6.2026, Marti) — audit log dotazu z watcheru.
-- Kazdy beh claude_sql_runner.py zaloguje sem (NE-anonymni, append-only).
-- Spustit v DBeaveru jako Marti-AI (owner fw schema), cely najednou.
-- ============================================================================

CREATE TABLE IF NOT EXISTS fw.claude_sql_log (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor       VARCHAR(40) NOT NULL DEFAULT 'claude',
    db_target   VARCHAR(16) NOT NULL,          -- pg / mssql
    sql_text    TEXT NOT NULL,
    status      VARCHAR(20) NOT NULL,          -- ok / blocked / error
    row_count   INTEGER,
    elapsed_ms  INTEGER,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_claude_sql_log_created
    ON fw.claude_sql_log (created_at DESC);

ALTER TABLE fw.claude_sql_log OWNER TO "Marti-AI";
GRANT SELECT, INSERT ON fw.claude_sql_log TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fw TO strategie;

-- Smoke:
-- SELECT * FROM fw.claude_sql_log ORDER BY id DESC LIMIT 10;
