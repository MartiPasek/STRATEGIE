-- Fix M (21.5. rano) — extend dedup exclusion list o 'acknowledged'
--
-- Marti's catch po acknowledged → ne-skip: dedup function WHERE status NOT IN
-- ('resolved', 'ignored'). 'acknowledged' není v listu → dedup pořád hit i po
-- UI "marked as acknowledged". Sémantika: acknowledged = user seen, ale chce
-- sběr dalších instances. Fix: ALTER funkci s rozšířeným exclusion listem.
--
-- RUN: jako Marti (uppercase, owner overload 2) NEBO member of fw_owners.
--   highlight celý soubor + Alt+X (atomic).

BEGIN;

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
    -- Fix J (2): grid/form attribution
    p_core_id BIGINT DEFAULT NULL,
    p_comp_def_id BIGINT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
-- Diag log fix #4 (20.5.): SET search_path resolve digest() z pgcrypto
SET search_path = pgcrypto, public, fw, pg_catalog
AS $$
DECLARE
    v_dedup_hash VARCHAR;
    v_existing_id BIGINT;
    v_new_id BIGINT;
    v_retention_until TIMESTAMPTZ;
BEGIN
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

    v_retention_until := CASE
        WHEN p_level IN ('error', 'fatal') THEN NULL
        WHEN p_level = 'warn' THEN NOW() + INTERVAL '90 days'
        ELSE NOW() + INTERVAL '30 days'
    END;

    -- Fix M (21.5.): extend exclusion o 'acknowledged'. Sémantika: user
    -- viděl, ale chce sběr dalších instances. 'resolved'/'ignored' = closed.
    UPDATE fw.diag_log
    SET occurrences = occurrences + 1,
        last_seen_at = NOW(),
        -- Fix M+ (21.5.): propagate latest attribution pokud existing row
        -- má NULL. Doctrine: "když poprvé padla anonymně a podruhé už víme
        -- kdo, opravit." Bez tohoto pre-Fix-K rows zůstanou NULL forever.
        user_login_name = COALESCE(user_login_name, p_user_login_name),
        user_id = COALESCE(user_id, p_user_id),
        tenant_name = COALESCE(tenant_name, p_tenant_name),
        core_id = COALESCE(core_id, p_core_id),
        comp_def_id = COALESCE(comp_def_id, p_comp_def_id)
    WHERE dedup_hash = v_dedup_hash
      AND created_at >= NOW() - INTERVAL '24 hours'
      AND status NOT IN ('resolved', 'ignored', 'acknowledged')
    RETURNING id INTO v_existing_id;

    IF FOUND THEN
        RETURN v_existing_id;
    END IF;

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

-- ════════════════════════════════════════════════════════════════════
-- Verify
-- ════════════════════════════════════════════════════════════════════

-- V1: Function signature + config
SELECT p.oid::regprocedure AS sig, proowner::regrole, prosecdef, proconfig
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='fw' AND p.proname='diag_log_upsert';
-- EXPECTED: 1 row, proconfig={search_path=pgcrypto, public, fw, pg_catalog}

-- V2: Smoke — call as strategie, simulate "acknowledged exclusion teď works"
-- Marti označí row jako 'acknowledged' v UI, další chyba se stejným hashem
-- vytvoří NEW row (ne dedup hit do acknowledged-ed).

-- V3: Trigger error znovu z UI → po Fix L (frontend fetch wrapper) bude
-- nový row mít core_id + comp_def_id. Plus Fix M+ propagate fixne starý
-- row attribution (#235 by se updatla na Marti/1/STRATEGIE pokud triggerujem
-- bez acknowledged statusem).
