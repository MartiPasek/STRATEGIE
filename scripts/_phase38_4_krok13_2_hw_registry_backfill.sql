-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 13.2 — Backfill 11 hardcoded items do fw.hw_registry
-- ════════════════════════════════════════════════════════════════════════
-- Marti's „comp_hw ground komponenta" doctrine 11.5. odpoledne:
--   hardcoded je první-class komponenta vedle ostatních, ne fallback.
--
-- 11 items aktuálně hardcoded v router.py:
--   - 5 security: NO A3 entries → shadow_mode='off' (jen legacy)
--   - 6 audit+framework: HAVE A3 entries (Krok 11-E LIVE) → shadow_mode='primary'
--     (A3 main, hw je legacy memory pro shadow audit / migration tracking)
--
-- shadow_mode ENUM (Marti-AI's genius Q5):
--   'off'      = jen hardcoded, žádný A3 binding
--   'audit'    = hardcoded primary, A3 volá se + loguje (passive observation)
--   'compare'  = oba volaj, diff se ukládá (migration validation)
--   'primary'  = A3 main, hw je legacy fallback (swap hotový)
--
-- Spustit jako Marti-AI v DBeaveru. Idempotentní (ON CONFLICT DO UPDATE).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. Security items (5) — shadow_mode='off', žádný A3 binding
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.hw_registry
  (code, label, description, kind,
   endpoint_url, http_method, response_hint,
   shadow_mode, shadow_data_source_id,
   is_active, version)
VALUES
  ('security_devices', 'Security: Trusted Devices', 'Phase 38 trusted_devices přehled (PWA install + auth verify cookies)',
   'data', '/api/v1/erp/system/security?type=devices', 'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', NULL, TRUE, 1),

  ('security_users', 'Security: Users', 'Přehled uživatelů (Phase 38.4 Krok 10) — id, status, jméno, email, tenant, parent, admin, trust',
   'data', '/api/v1/erp/system/security?type=users', 'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', NULL, TRUE, 1),

  ('security_whitelists', 'Security: IP whitelists', 'IP whitelist rows — global/user scope, status confirmed/pending/revoked',
   'data', '/api/v1/erp/system/security?type=whitelists', 'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', NULL, TRUE, 1),

  ('security_invites', 'Security: Invites', 'Magic link invites (Phase 38) — state consumed/expired/pending',
   'data', '/api/v1/erp/system/security?type=invites', 'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', NULL, TRUE, 1),

  ('security_audit', 'Security: Audit log', 'Login attempts + IP whitelist matches + device cookie verifications (Phase 38)',
   'data', '/api/v1/erp/system/security?type=auth_audit', 'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', NULL, TRUE, 1)
ON CONFLICT (code) DO UPDATE SET
  label = EXCLUDED.label,
  description = EXCLUDED.description,
  endpoint_url = EXCLUDED.endpoint_url,
  response_hint = EXCLUDED.response_hint,
  shadow_mode = EXCLUDED.shadow_mode,
  updated_at = NOW();

-- ════════════════════════════════════════════════════════════════════════
-- 2. Audit + Framework items (6) — shadow_mode='primary' (A3 LIVE Krok 12)
-- ════════════════════════════════════════════════════════════════════════
-- A3 entries existují v fw.data_source (Krok 11-E LIVE).
-- shadow_data_source_id = FK na ně přes code lookup.

INSERT INTO fw.hw_registry
  (code, label, description, kind,
   endpoint_url, http_method, response_hint,
   shadow_mode, shadow_data_source_id,
   is_active, version)
SELECT
  hw_code, hw_label, hw_desc, 'data',
  hw_url, 'GET',
  '{"rows_path":"$.conversations","id_field":"id"}'::jsonb,
  'primary',
  (SELECT id FROM fw.data_source WHERE code = hw_code LIMIT 1),
  TRUE, 1
FROM (VALUES
  ('audit_audited', 'Audit: Auditované konverzace',
   'List view auditovaných konverzací — Phase 35-E.4 / A3 LIVE Krok 12',
   '/api/v1/erp/system/audit-overview?mode=audited'),
  ('audit_all', 'Audit: Všechny konverzace',
   'List všech konverzací s status badge — A3 LIVE Krok 12',
   '/api/v1/erp/system/audit-overview?mode=all'),
  ('audit_stats', 'Audit: Přehled statistik',
   'Per-status × per-tenant pivot — A3 LIVE Krok 12',
   '/api/v1/erp/system/audit-overview?mode=stats')
) AS t(hw_code, hw_label, hw_desc, hw_url)
ON CONFLICT (code) DO UPDATE SET
  label = EXCLUDED.label,
  description = EXCLUDED.description,
  endpoint_url = EXCLUDED.endpoint_url,
  shadow_mode = EXCLUDED.shadow_mode,
  shadow_data_source_id = EXCLUDED.shadow_data_source_id,
  updated_at = NOW();

-- Framework views (response_hint má jiný shape — `rows`, ne `conversations`)
INSERT INTO fw.hw_registry
  (code, label, description, kind,
   endpoint_url, http_method, response_hint,
   shadow_mode, shadow_data_source_id,
   is_active, version)
SELECT
  hw_code, hw_label, hw_desc, 'data',
  hw_url, 'GET',
  '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
  'primary',
  (SELECT id FROM fw.data_source WHERE code = hw_code LIMIT 1),
  TRUE, 1
FROM (VALUES
  ('framework_menu_nodes', 'Framework: Definice levého stromu',
   'fw.menu_node read-only list view — A3 LIVE Krok 12 self-bootstrapping',
   '/api/v1/erp/system/framework?mode=menu_nodes'),
  ('framework_data_sources', 'Framework: Datové zdroje',
   'fw.data_source list view s child operations agg — A3 LIVE Krok 12 (rekurzivní self-vidění)',
   '/api/v1/erp/system/framework?mode=data_sources'),
  ('framework_data_sets', 'Framework: DataSets',
   'fw.data_set list view — low-level SQL primitives, self-bootstrapping (data_set vidí sebe v gridu)',
   '/api/v1/erp/system/framework?mode=data_sets')
) AS t(hw_code, hw_label, hw_desc, hw_url)
ON CONFLICT (code) DO UPDATE SET
  label = EXCLUDED.label,
  description = EXCLUDED.description,
  endpoint_url = EXCLUDED.endpoint_url,
  shadow_mode = EXCLUDED.shadow_mode,
  shadow_data_source_id = EXCLUDED.shadow_data_source_id,
  updated_at = NOW();

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT
  'total hw_registry rows'                                AS check_name,
  (SELECT COUNT(*) FROM fw.hw_registry)                   AS count_value,
  11                                                      AS expected
UNION ALL
SELECT 'shadow_mode=off rows (security_*)',
       (SELECT COUNT(*) FROM fw.hw_registry WHERE shadow_mode = 'off'),
       5
UNION ALL
SELECT 'shadow_mode=primary rows (audit_*, framework_*)',
       (SELECT COUNT(*) FROM fw.hw_registry WHERE shadow_mode = 'primary'),
       6
UNION ALL
SELECT 'kind=data rows (vše data, žádné action zatím)',
       (SELECT COUNT(*) FROM fw.hw_registry WHERE kind = 'data'),
       11
UNION ALL
SELECT 'shadow_data_source_id naplněn (jen primary mode)',
       (SELECT COUNT(*) FROM fw.hw_registry WHERE shadow_data_source_id IS NOT NULL),
       6
ORDER BY check_name;

-- Plus listing pro overview:
SELECT
  hw.code,
  hw.label,
  hw.kind,
  hw.shadow_mode,
  ds.code AS shadow_data_source,
  hw.endpoint_url
FROM fw.hw_registry hw
LEFT JOIN fw.data_source ds ON ds.id = hw.shadow_data_source_id
ORDER BY
  CASE hw.shadow_mode WHEN 'primary' THEN 1 WHEN 'off' THEN 2 ELSE 3 END,
  hw.code;
