-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 12-E (11.5.2026 odpoledne): fw.core hardcoded_endpoint
-- + automatic A3 vs legacy classification
-- ════════════════════════════════════════════════════════════════════════
-- Marti's návrh 11.5. odpoledne: automaticky rozlišit hardcoded prehledy
-- (jadra) od těch, které běží přes A3 framework.
--
-- Architectonicky (po execute):
--   data_source_id NOT NULL          → A3 chain LIVE
--   data_source_id IS NULL
--     AND hardcoded_endpoint NOT NULL → Legacy hardcoded URL fallback
--   both NULL                         → ORPHAN — frontend ukáže ⚠️
--
-- Po Krok 11-E máme 6 nových data_source rows (audit + framework).
-- Tento skript:
--   1. ALTER fw.core ADD COLUMN hardcoded_endpoint
--   2. Backfill fw.core.data_source_id pro audit/framework cores (vazba
--      na existing fw.data_source rows z Krok 11-E)
--   3. Backfill fw.core.hardcoded_endpoint pro 5 security cores
--   4. VERIFY query klasifikace (a3 / hardcoded / orphan)
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. ALTER TABLE — add hardcoded_endpoint sloupec
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.core
    ADD COLUMN IF NOT EXISTS hardcoded_endpoint VARCHAR(255) NULL;

COMMENT ON COLUMN fw.core.hardcoded_endpoint IS
    'Phase 38.4 Krok 12-E (11.5.2026): URL pattern pro legacy hardcoded prehled. '
    'NULL = A3 path pres data_source_id. '
    'Naplnene = legacy fallback URL. '
    'Az pridame A3 entries pro dany grid + data_source_id naplnime, '
    'hardcoded_endpoint mužeme zachovat jako audit memory (kde dříve hardcode žil).';

-- ════════════════════════════════════════════════════════════════════════
-- 2. Backfill data_source_id pro 6 audit + framework cores
--    (data_source rows existují z Krok 11-E, jen vazba přes core.data_source_id chybí)
-- ════════════════════════════════════════════════════════════════════════
UPDATE fw.core c
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = c.code LIMIT 1)
WHERE c.code IN (
    'audit_audited', 'audit_all', 'audit_stats',
    'framework_menu_nodes', 'framework_data_sources', 'framework_data_sets'
)
AND c.data_source_id IS NULL;

-- ════════════════════════════════════════════════════════════════════════
-- 3. Backfill hardcoded_endpoint pro 5 security cores
--    (zatím nemají A3 data_source, žijí v hardcoded Python endpointu)
-- ════════════════════════════════════════════════════════════════════════
UPDATE fw.core SET hardcoded_endpoint = '/api/v1/erp/system/security?type=devices'
WHERE code = 'security_devices';

UPDATE fw.core SET hardcoded_endpoint = '/api/v1/erp/system/security?type=users'
WHERE code = 'security_users';

UPDATE fw.core SET hardcoded_endpoint = '/api/v1/erp/system/security?type=whitelists'
WHERE code = 'security_whitelists';

UPDATE fw.core SET hardcoded_endpoint = '/api/v1/erp/system/security?type=invites'
WHERE code = 'security_invites';

UPDATE fw.core SET hardcoded_endpoint = '/api/v1/erp/system/security?type=auth_audit'
WHERE code = 'security_audit';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY — automatická klasifikace
-- ════════════════════════════════════════════════════════════════════════
SELECT
    id,
    code,
    label,
    data_source_id,
    hardcoded_endpoint,
    CASE
        WHEN data_source_id IS NOT NULL THEN '✅ a3'
        WHEN hardcoded_endpoint IS NOT NULL THEN '🛠️ hardcoded'
        ELSE '⚠️ orphan'
    END AS status_type
FROM fw.core
ORDER BY id;

-- Expected (predpoklad: po Krok 11-A noc + Krok 10-B rano + Krok 11-D + 11-E):
--   security_* (5 rows)         → 🛠️ hardcoded (data_source_id=NULL, hardcoded_endpoint=URL)
--   audit_* + framework_* (6+1)  → ✅ a3 (data_source_id=<id>, hardcoded_endpoint=NULL)
--   AG_Grid template (1 row)     → ⚠️ orphan (oba NULL, normální — template definition)
-- Plus aggregate count:
SELECT
    COUNT(*) FILTER (WHERE data_source_id IS NOT NULL) AS a3_count,
    COUNT(*) FILTER (WHERE data_source_id IS NULL AND hardcoded_endpoint IS NOT NULL) AS hardcoded_count,
    COUNT(*) FILTER (WHERE data_source_id IS NULL AND hardcoded_endpoint IS NULL) AS orphan_count,
    COUNT(*) AS total
FROM fw.core;
-- Expected: 6 / 5 / 1 / 12 (cca, depending na current rows)
