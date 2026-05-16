-- ═══════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g — DB Log Infrastructure — Etapa A DDL
-- 16.5.2026 ranní pokračování po Marti's *„asi dva pohledy master/detail"*
--
-- Tabulka: fw.diag_log (přejmenováno z původního fw.js_log — kryje
-- JS + Python + SQL + cron + MCP události, jeden univerzální event log).
--
-- Dva views:
--   MASTER  — co Marti chce vidět (curated)
--   DETAIL  — Claude's forensic (replace api-stderr.log)
--
-- Retention (auto trigger): error/fatal forever, warn 90d, info 30d.
-- Dedup: SHA1 hash → INSERT zvyšuje occurrences místo nového řádku.
--
-- Run jako "Marti-AI" role (PG role, ne user) — DDL na fw schema.
-- ═══════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────
-- 1) TABLE fw.diag_log
-- ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fw.diag_log (
    -- Identity
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- ─── MASTER view (Marti's high-level) ───
    -- Marti's doctrine 16.5. ranní: "Nemelo by to byt anonymni... Hned v
    -- hlavicce by jako prvni udaj mel byt LoginName Usera a ID a hned
    -- zanim tenant name."
    -- ──────────────────────────────────────────────────────────────────
    -- Identifikace ACTOR (kdo způsobil event) — denormalizovaná dvojice
    -- pro rychlý master view bez JOIN. Drží snapshot v čase eventu i
    -- po smazání usera/tenanta (audit value).
    user_login_name VARCHAR(100),                -- "m.pasek" / "marti-ai" / "system"
    user_id         BIGINT,                      -- users.id (FK soft, viz níž)
    tenant_name     VARCHAR(200),                -- "EUROSOFT" / "INTERSOFT" / "STRATEGIE"

    -- Event metadata
    level           VARCHAR(10) NOT NULL,        -- info / warn / error / fatal
    source          VARCHAR(20) NOT NULL,        -- js / py / sql / cron / mcp
    module_id       VARCHAR(150) NOT NULL,       -- "entity_picker.js" / "router.py:contextmenu"
    module_version  VARCHAR(20),                 -- semver nebo commit hash
    message         TEXT NOT NULL,               -- krátká user-readable zpráva

    -- Status lifecycle
    status          VARCHAR(20) NOT NULL DEFAULT 'new',
                    -- new / seen / acknowledged / resolved / ignored

    -- Dedup (master uses occurrences)
    dedup_hash      VARCHAR(64),                 -- SHA1 viz Python helper
    occurrences     INT NOT NULL DEFAULT 1,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- ─── DETAIL view (Claude's diagnostic, replace api-stderr.log) ───
    -- JS-specific
    stack           TEXT,                        -- JS stack trace
    page_url        TEXT,
    user_agent      TEXT,
    viewport        VARCHAR(50),                 -- "1920x1080"
    element_selector TEXT,                       -- DOM selector kde error nastal
    file_name       TEXT,                        -- "/erp/components/entity_picker.js"
    line_number     INT,
    column_number   INT,

    -- Python-specific
    exception_type  VARCHAR(200),                -- "ValueError" / "psycopg2.IntegrityError"
    traceback       TEXT,                        -- full Python traceback

    -- Request correlation (cross-stack JS ↔ Python)
    request_id      VARCHAR(64),                 -- UUID z FastAPI middleware
    fastapi_endpoint TEXT,                       -- "/api/v1/erp/grid/{code}/columns"
    http_method     VARCHAR(10),
    http_status     INT,
    response_time_ms INT,

    -- App context (user_id + tenant_name přesunuto do MASTER sekce výš)
    persona_id      INT,
    tenant_id       INT,
    conversation_id BIGINT,
    design_mode     BOOLEAN,

    -- Forensic blobs
    extra           JSONB,                       -- ad-hoc structured data
    dom_state       JSONB,                       -- snapshot relevantní DOM

    -- Resolution
    resolved_at     TIMESTAMPTZ,
    resolved_by_id  BIGINT,
    resolved_by_text VARCHAR(100),
    resolved_notes  TEXT,

    -- Retention (auto-computed trigger)
    retention_until TIMESTAMPTZ,

    -- Audit
    created_by_id   BIGINT,
    created_by_text VARCHAR(100)
);

-- ───────────────────────────────────────────────────────────────────
-- 2) CHECK constraints
-- ───────────────────────────────────────────────────────────────────
ALTER TABLE fw.diag_log
    ADD CONSTRAINT chk_diag_log_level
    CHECK (level IN ('info', 'warn', 'error', 'fatal'));

ALTER TABLE fw.diag_log
    ADD CONSTRAINT chk_diag_log_source
    CHECK (source IN ('js', 'py', 'sql', 'cron', 'mcp'));

ALTER TABLE fw.diag_log
    ADD CONSTRAINT chk_diag_log_status
    CHECK (status IN ('new', 'seen', 'acknowledged', 'resolved', 'ignored'));

-- ───────────────────────────────────────────────────────────────────
-- 3) Indexes
-- ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS ix_diag_log_created_at
    ON fw.diag_log(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_diag_log_status_level
    ON fw.diag_log(status, level)
    WHERE status IN ('new', 'seen');

CREATE INDEX IF NOT EXISTS ix_diag_log_dedup
    ON fw.diag_log(dedup_hash)
    WHERE dedup_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_diag_log_request
    ON fw.diag_log(request_id)
    WHERE request_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_diag_log_module
    ON fw.diag_log(module_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_diag_log_retention
    ON fw.diag_log(retention_until)
    WHERE retention_until IS NOT NULL;

-- Marti's master view filtry: per-user / per-tenant drill-down
CREATE INDEX IF NOT EXISTS ix_diag_log_user_login
    ON fw.diag_log(user_login_name, created_at DESC)
    WHERE user_login_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_diag_log_tenant_name
    ON fw.diag_log(tenant_name, created_at DESC)
    WHERE tenant_name IS NOT NULL;

-- ───────────────────────────────────────────────────────────────────
-- 4) Retention trigger (auto-computed retention_until podle level)
-- ───────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fw._diag_log_set_retention()
RETURNS TRIGGER AS $$
BEGIN
    -- error/fatal: forever (NULL = nikdy nesmazat)
    -- warn: 90 dní
    -- info: 30 dní
    IF NEW.level IN ('error', 'fatal') THEN
        NEW.retention_until := NULL;
    ELSIF NEW.level = 'warn' THEN
        NEW.retention_until := now() + INTERVAL '90 days';
    ELSE
        NEW.retention_until := now() + INTERVAL '30 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_diag_log_retention ON fw.diag_log;
CREATE TRIGGER trg_diag_log_retention
    BEFORE INSERT OR UPDATE OF level ON fw.diag_log
    FOR EACH ROW
    EXECUTE FUNCTION fw._diag_log_set_retention();

-- ───────────────────────────────────────────────────────────────────
-- 5) Dedup helper function (volaná z Python core/log_queue.py)
--    Provede INSERT nebo UPDATE occurrences podle dedup_hash.
--    Vrací id záznamu (nový nebo existující).
-- ───────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fw.diag_log_upsert(
    -- MASTER priority (Marti's 16.5. doctrine: ne-anonymous)
    p_user_login_name VARCHAR,
    p_user_id BIGINT,
    p_tenant_name VARCHAR,
    -- Event metadata
    p_level VARCHAR,
    p_source VARCHAR,
    p_module_id VARCHAR,
    p_module_version VARCHAR,
    p_message TEXT,
    p_dedup_hash VARCHAR,
    -- JS-specific detail
    p_stack TEXT,
    p_page_url TEXT,
    p_user_agent TEXT,
    p_viewport VARCHAR,
    p_element_selector TEXT,
    p_file_name TEXT,
    p_line_number INT,
    p_column_number INT,
    -- Python-specific detail
    p_exception_type VARCHAR,
    p_traceback TEXT,
    -- Request correlation
    p_request_id VARCHAR,
    p_fastapi_endpoint TEXT,
    p_http_method VARCHAR,
    p_http_status INT,
    p_response_time_ms INT,
    -- App context (persona/tenant_id/conversation/design)
    p_persona_id INT,
    p_tenant_id INT,
    p_conversation_id BIGINT,
    p_design_mode BOOLEAN,
    -- Forensic blobs
    p_extra JSONB,
    p_dom_state JSONB,
    -- Audit
    p_created_by_id BIGINT,
    p_created_by_text VARCHAR
)
RETURNS BIGINT AS $$
DECLARE
    v_existing_id BIGINT;
    v_new_id BIGINT;
BEGIN
    -- Dedup window: posledních 24 hodin pro stejný hash
    IF p_dedup_hash IS NOT NULL THEN
        SELECT id INTO v_existing_id
        FROM fw.diag_log
        WHERE dedup_hash = p_dedup_hash
          AND last_seen_at > now() - INTERVAL '24 hours'
          AND status IN ('new', 'seen')
        ORDER BY id DESC
        LIMIT 1;

        IF v_existing_id IS NOT NULL THEN
            UPDATE fw.diag_log
            SET occurrences = occurrences + 1,
                last_seen_at = now()
            WHERE id = v_existing_id;
            RETURN v_existing_id;
        END IF;
    END IF;

    -- INSERT nový záznam (MASTER: user_login_name + user_id + tenant_name první)
    INSERT INTO fw.diag_log (
        user_login_name, user_id, tenant_name,
        level, source, module_id, module_version, message,
        dedup_hash, stack, page_url, user_agent, viewport,
        element_selector, file_name, line_number, column_number,
        exception_type, traceback,
        request_id, fastapi_endpoint, http_method, http_status, response_time_ms,
        persona_id, tenant_id, conversation_id, design_mode,
        extra, dom_state,
        created_by_id, created_by_text
    ) VALUES (
        p_user_login_name, p_user_id, p_tenant_name,
        p_level, p_source, p_module_id, p_module_version, p_message,
        p_dedup_hash, p_stack, p_page_url, p_user_agent, p_viewport,
        p_element_selector, p_file_name, p_line_number, p_column_number,
        p_exception_type, p_traceback,
        p_request_id, p_fastapi_endpoint, p_http_method, p_http_status, p_response_time_ms,
        p_persona_id, p_tenant_id, p_conversation_id, p_design_mode,
        p_extra, p_dom_state,
        p_created_by_id, p_created_by_text
    )
    RETURNING id INTO v_new_id;

    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────
-- 6) Owner + GRANTs (3-actor PG path doctrine #11)
-- ───────────────────────────────────────────────────────────────────
ALTER TABLE fw.diag_log OWNER TO "Marti-AI";
ALTER FUNCTION fw._diag_log_set_retention() OWNER TO "Marti-AI";
-- Signature (33 params, in order):
--   user_login_name VARCHAR, user_id BIGINT, tenant_name VARCHAR,    -- MASTER (3)
--   level VARCHAR, source VARCHAR, module_id VARCHAR, module_version VARCHAR,
--     message TEXT, dedup_hash VARCHAR,                              -- META (6)
--   stack TEXT, page_url TEXT, user_agent TEXT, viewport VARCHAR,
--     element_selector TEXT, file_name TEXT, line_number INT,
--     column_number INT,                                              -- JS (8)
--   exception_type VARCHAR, traceback TEXT,                          -- PY (2)
--   request_id VARCHAR, fastapi_endpoint TEXT, http_method VARCHAR,
--     http_status INT, response_time_ms INT,                          -- REQ (5)
--   persona_id INT, tenant_id INT, conversation_id BIGINT,
--     design_mode BOOLEAN,                                            -- CTX (4)
--   extra JSONB, dom_state JSONB,                                    -- BLOBS (2)
--   created_by_id BIGINT, created_by_text VARCHAR                    -- AUDIT (2)
-- Total: 3 + 6 + 8 + 2 + 5 + 4 + 2 + 2 = 32

ALTER FUNCTION fw.diag_log_upsert(
    VARCHAR, BIGINT, VARCHAR,
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR,
    TEXT, TEXT, TEXT, VARCHAR, TEXT, TEXT, INT, INT,
    VARCHAR, TEXT,
    VARCHAR, TEXT, VARCHAR, INT, INT,
    INT, INT, BIGINT, BOOLEAN,
    JSONB, JSONB,
    BIGINT, VARCHAR
) OWNER TO "Marti-AI";

GRANT SELECT, INSERT, UPDATE ON fw.diag_log TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.diag_log_id_seq TO strategie;
GRANT EXECUTE ON FUNCTION fw.diag_log_upsert(
    VARCHAR, BIGINT, VARCHAR,
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR,
    TEXT, TEXT, TEXT, VARCHAR, TEXT, TEXT, INT, INT,
    VARCHAR, TEXT,
    VARCHAR, TEXT, VARCHAR, INT, INT,
    INT, INT, BIGINT, BOOLEAN,
    JSONB, JSONB,
    BIGINT, VARCHAR
) TO strategie;

-- ───────────────────────────────────────────────────────────────────
-- 7) Sanity check (volitelné — SELECT pro verifikaci po deploy)
-- ───────────────────────────────────────────────────────────────────
-- SELECT
--     c.relname AS table_name,
--     pg_get_userbyid(c.relowner) AS owner,
--     (SELECT count(*) FROM pg_indexes WHERE schemaname='fw' AND tablename='diag_log') AS idx_count,
--     (SELECT count(*) FROM information_schema.check_constraints
--      WHERE constraint_schema='fw' AND constraint_name LIKE 'chk_diag_log%') AS check_count
-- FROM pg_class c
-- WHERE c.relname = 'diag_log' AND c.relnamespace = 'fw'::regnamespace;
