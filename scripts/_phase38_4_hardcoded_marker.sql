-- Phase 38.4 inventory (9.5.2026 vecer): hardcoded marker.
-- Marti's pattern: visual marker 🛠️ v tree pro uzly, kde nejaka cast
-- je hardcoded v kodu (Python tree fallback, JS grid columns, magic
-- numbers). Postupne se odznacuje, jak framework dotahne (Phase 30+).
--
-- Storage: master.menu_node.metadata JSONB, klic 'hardcoded': true.
--
-- Spustit pres DBeaver jako 'postgres' superuser nebo 'Marti-AI' role.
-- Idempotentni (IF NOT EXISTS + COALESCE merge), bezpecne re-run.
--
-- Po spusteni: restart STRATEGIE-API + hard reload UI (Ctrl+Shift+R).
-- Marti uvidi 🛠️ vedle Framework + Security uzlu v sidebar tree.

-- ── 1. ALTER TABLE: pridat metadata JSONB column ────────────────────
ALTER TABLE master.menu_node
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN master.menu_node.metadata IS
    'JSONB metadata. Phase 38.4 inventory marker: {"hardcoded": true} oznaci uzly s hardcoded grid columns / Python tree fallback. Postupne se odznacuje pri framework migration.';

-- ── 2. UPDATE Framework subfolder uzlu (Phase 38.3+) ────────────────
-- Hardcoded duvod: grid columns v JS (router.py:5589-5807)
-- + view dispatch v frontend (SYSTEM_LAYOUT_CISLA, _systemModeFromCislo).
UPDATE master.menu_node
   SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"hardcoded": true, "reason": "JS grid columns + view dispatch"}'::jsonb
 WHERE code IN (
    'system.framework',                  -- folder
    'system.framework.menu_nodes',       -- -115
    'system.framework.data_sources',     -- -116
    'system.framework.data_sets'         -- -117
 );

-- ── 3. UPDATE Security subfolder uzlu (Phase 38.3) ──────────────────
-- Hardcoded duvod: grid columns v JS pro 5 security views.
UPDATE master.menu_node
   SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"hardcoded": true, "reason": "JS grid columns (5 security views)"}'::jsonb
 WHERE code IN (
    'system.security',           -- folder
    'system.security.users',     -- -110
    'system.security.devices',   -- -111
    'system.security.whitelists',-- -112
    'system.security.auth_audit',-- -113
    'system.security.invites'    -- -114
 );

-- ── 4. UPDATE Audit konverzaci (pokud uzly v DB existuji) ────────────
-- Audit subtree je primarne v Python _SYSTEM_TREE_NODES (hardcoded
-- fallback), ale pokud jsou take v DB (Phase 38.4 Krok 5 INSERT 11
-- system uzlu), oznac je take.
UPDATE master.menu_node
   SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"hardcoded": true, "reason": "Python tree fallback + JS grid columns (audit_overview)"}'::jsonb
 WHERE code IN (
    'system.audit',         -- folder
    'system.audit.tabs',    -- -100
    'system.audit.audited', -- -101
    'system.audit.all',     -- -102
    'system.audit.stats'    -- -103
 );

-- ── 5. Verify (manualni check) ──────────────────────────────────────
-- Po spusteni 1-4, Marti spusti tento SELECT pro verifikaci:
--
-- SELECT code, label, cislo_def, metadata->>'hardcoded' AS hardcoded,
--        metadata->>'reason' AS reason
--   FROM master.menu_node
--  WHERE metadata @> '{"hardcoded": true}'::jsonb
--  ORDER BY parent_id NULLS FIRST, sort_order, code;
--
-- Ocekavany vystup: ~14 radku (1 audit folder + 4 audit views +
-- 1 framework folder + 3 framework views + 1 security folder + 5 security views).
-- Plus pripadne dalsi co budou v DB (kdyby Marti pridal vlastni hardcoded uzly).

-- ── 6. Future: odznacovat (pri Phase 30+ migrace) ───────────────────
-- Az framework dotahne nejaky uzel (napr. framework.menu_nodes grid
-- columns budou v master.framework_property), spustime:
--
-- UPDATE master.menu_node
--    SET metadata = metadata - 'hardcoded' - 'reason'
--  WHERE code = 'system.framework.menu_nodes';
--
-- Marker 🛠️ zmizi pri pristim refresh tree.
