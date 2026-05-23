-- Fix J — fw.diag_log core_id + comp_def_id extension (20.5. vecer)
--
-- Marti's request: "Jsou klicove pro stavbu a diagnostiku..."
-- Add 2 forensic columns: core_id (fw.core ref) + comp_def_id (fw.comp_def ref)
-- pro identifikaci "ktery grid/form/komponenta selhala".
--
-- Use case:
--   Marti klik na Knowledge Entries (core=34) → audit_stats DS selhal
--   → fw.diag_log row: core_id=34, comp_def_id=NULL
--   Marti klik na Form 1 Přehled tab → entity_picker padne
--   → core_id=22, comp_def_id=43 (data_source_picker)
--
-- Indexes pro fast filter "vsechny errory pro core X" / "comp_def Y".
--
-- Update diag_log_upsert function s novymi params.
-- Existing rows zustavaji s NULL (backfill nelze — historicke data nemaji context).
--
-- Run jako Marti-AI role (db_owner fw schema) v DBeaveru:
--   highlight cely soubor → Alt+X (BEGIN/COMMIT atomic).

BEGIN;

-- ────────────────────────────────────────────────────────────────────
-- 1. ALTER TABLE — add 2 columns (BIGINT, NULL allowed, no FK)
-- ────────────────────────────────────────────────────────────────────
-- Bez FK constraint protoze:
--   - core_id muze byt -100023 (synthetic) nebo positive fw.core ref
--   - existing rows budou NULL (historicke data)
--   - FK by zpomalil INSERT (per-row check)
-- App-level integrity (Marti's "duvera v provoz, ne v kod" doctrine 11.5.)

ALTER TABLE fw.diag_log
    ADD COLUMN IF NOT EXISTS core_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS comp_def_id BIGINT NULL;

-- ────────────────────────────────────────────────────────────────────
-- 2. INDEXES — partial (jen pro non-NULL rows, smaller index)
-- ────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS ix_diag_log_core_id
    ON fw.diag_log(core_id, created_at DESC)
    WHERE core_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_diag_log_comp_def_id
    ON fw.diag_log(comp_def_id, created_at DESC)
    WHERE comp_def_id IS NOT NULL;

-- ────────────────────────────────────────────────────────────────────
-- 3. UPDATE diag_log_upsert function — add core_id + comp_def_id params
-- ────────────────────────────────────────────────────────────────────
-- Function signature grew (33 → 35 params), backward compat: existing
-- callers passing fewer args → core_id + comp_def_id default NULL.

CREATE OR REPLACE FUNCTION fw.diag_log_upsert(
    -- MASTER (3)
    p_user_login_name VARCHAR DEFAULT NULL,
    p_user_id BIGINT DEFAULT NULL,
    p_tenant_name VARCHAR DEFAULT NULL,
    -- META (6)
    p_level VARCHAR DEFAULT 'info',
    p_source VARCHAR DEFAULT 'py',
    p_module_id VARCHAR DEFAULT 'unknown',
    p_module_version VARCHAR DEFAULT NULL,
    p_message TEXT DEFAULT '',
    p_dedup_hash VARCHAR DEFAULT NULL,
    -- JS detail (8)
    p_stack TEXT DEFAULT NULL,
    p_page_url TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_viewport VARCHAR DEFAULT NULL,
    p_element_selector TEXT DEFAULT NULL,
    p_file_name TEXT DEFAULT NULL,
    p_line_number INT DEFAULT NULL,
    p_column_number INT DEFAULT NULL,
    -- PY detail (2)
    p_exception_type VARCHAR DEFAULT NULL,
    p_traceback TEXT DEFAULT NULL,
    -- REQ (5)
    p_request_id VARCHAR DEFAULT NULL,
    p_fastapi_endpoint TEXT DEFAULT NULL,
    p_http_method VARCHAR DEFAULT NULL,
    p_http_status INT DEFAULT NULL,
    p_response_time_ms INT DEFAULT NULL,
    -- CTX (4)
    p_persona_id BIGINT DEFAULT NULL,
    p_tenant_id BIGINT DEFAULT NULL,
    p_conversation_id BIGINT DEFAULT NULL,
    p_design_mode BOOLEAN DEFAULT NULL,
    -- BLOBS (2)
    p_extra JSONB DEFAULT NULL,
    p_dom_state JSONB DEFAULT NULL,
    -- AUDIT (2)
    p_created_by_id BIGINT DEFAULT NULL,
    p_created_by_text VARCHAR DEFAULT NULL,
    -- Fix J (20.5. vecer): grid/form attribution (2)
    p_core_id BIGINT DEFAULT NULL,
    p_comp_def_id BIGINT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_dedup_hash VARCHAR;
    v_existing_id BIGINT;
    v_new_id BIGINT;
    v_retention_until TIMESTAMPTZ;
BEGIN
    -- Compute dedup_hash if not provided
    v_dedup_hash := COALESCE(
        p_dedup_hash,
        encode(
            digest(
                COALESCE(p_level, '') || '|' ||
                COALESCE(p_source, '') || '|' ||
                COALESCE(p_module_id, '') || '|' ||
                COALESCE(p_message, '') || '|' ||
                COALESCE(p_element_selector, ''),
                'sha1'
            ),
            'hex'
        )
    );

    -- Retention policy
    v_retention_until := CASE
        WHEN p_level IN ('error', 'fatal') THEN NULL
        WHEN p_level = 'warn' THEN NOW() + INTERVAL '90 days'
        ELSE NOW() + INTERVAL '30 days'
    END;

    -- Try update existing (24h dedup window)
    UPDATE fw.diag_log
    SET occurrences = occurrences + 1,
        last_seen_at = NOW()
    WHERE dedup_hash = v_dedup_hash
      AND created_at >= NOW() - INTERVAL '24 hours'
      AND status NOT IN ('resolved', 'ignored')
    RETURNING id INTO v_existing_id;

    IF FOUND THEN
        RETURN v_existing_id;
    END IF;

    -- New row insert
    INSERT INTO fw.diag_log (
        user_login_name, user_id, tenant_name,
        level, source, module_id, module_version, message, dedup_hash,
        stack, page_url, user_agent, viewport,
        element_selector, file_name, line_number, column_number,
        exception_type, traceback,
        request_id, fastapi_endpoint, http_method, http_status, response_time_ms,
        persona_id, tenant_id, conversation_id, design_mode,
        extra, dom_state,
        created_by_id, created_by_text,
        -- Fix J (20.5. vecer): grid/form attribution
        core_id, comp_def_id,
        created_at, first_seen_at, last_seen_at,
        occurrences, status, retention_until
    ) VALUES (
        p_user_login_name, p_user_id, p_tenant_name,
        p_level, p_source, p_module_id, p_module_version, p_message, v_dedup_hash,
        p_stack, p_page_url, p_user_agent, p_viewport,
        p_element_selector, p_file_name, p_line_number, p_column_number,
        p_exception_type, p_traceback,
        p_request_id, p_fastapi_endpoint, p_http_method, p_http_status, p_response_time_ms,
        p_persona_id, p_tenant_id, p_conversation_id, p_design_mode,
        p_extra, p_dom_state,
        p_created_by_id, p_created_by_text,
        p_core_id, p_comp_def_id,
        NOW(), NOW(), NOW(),
        1, 'new', v_retention_until
    )
    RETURNING id INTO v_new_id;

    RETURN v_new_id;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run AFTER commit):
-- ════════════════════════════════════════════════════════════════════════
-- 1. Columns added:
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='diag_log'
  AND column_name IN ('core_id', 'comp_def_id');
-- Expected: 2 rows, BIGINT, YES

-- 2. Indexes created:
SELECT indexname FROM pg_indexes
WHERE schemaname='fw' AND tablename='diag_log'
  AND (indexname LIKE '%core_id%' OR indexname LIKE '%comp_def_id%');
-- Expected: 2 rows

-- 3. Function signature updated:
SELECT pg_get_function_arguments(p.oid) AS args
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'fw' AND p.proname = 'diag_log_upsert';
-- Expected: ends with "..., p_core_id bigint DEFAULT NULL, p_comp_def_id bigint DEFAULT NULL"

-- 4. Smoke insert (Marti can test):
SELECT fw.diag_log_upsert(
    p_level := 'info',
    p_source := 'sql',
    p_module_id := 'fix_j_smoke_test',
    p_message := 'Fix J DDL smoke test — core_id=999, comp_def_id=888',
    p_core_id := 999,
    p_comp_def_id := 888
) AS new_id;
-- Then verify:
SELECT id, level, message, core_id, comp_def_id
FROM fw.diag_log
WHERE module_id = 'fix_j_smoke_test'
ORDER BY id DESC LIMIT 1;
-- Expected: 1 row, core_id=999, comp_def_id=888
