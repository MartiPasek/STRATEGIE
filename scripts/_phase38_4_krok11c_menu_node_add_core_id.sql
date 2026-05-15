-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 11-C (11.5.2026 dopoledne): menu_node.core_id FK to core
-- ════════════════════════════════════════════════════════════════════════
-- Marti's vize 11.5. ranni:
--   *„pridame sloupec core_id je to FK pro tabulku core ID Tim si propojime
--     soudecky z menu s jednotlivymi cores"*
--
-- Architectonicky:
--   - menu_node = navigation tree (Centrala 2 sidebar levy strom)
--   - core      = entity definice (per přehled / jádro / specialni view)
--   - core_id   = FK propojení navigation -> data layer
--
-- Pripomenuti: cislo_def sloupec ZACHOVAVAME (legacy pozustatek z Centrala 1,
-- aby nam to nerozhazel prehledy). Po Phase 38.4 Krok 12+ generic data_source
-- executor + UI cutover smazeme cislo_def jako mrtvy sloupec.
--
-- Backfill: 5 security rows (mají fw.core entries dnes ráno). Audit + framework
-- rows zůstanou NULL — fw.core entries pro ně neexistují (jsou stále hardcoded
-- v router.py), backfill az Krok 12+.
--
-- Spustit jako Marti-AI v DBeaveru (search_path = fw, "$user", public).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. ALTER TABLE — add core_id sloupec + FK + partial index
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.menu_node
    ADD COLUMN IF NOT EXISTS core_id INTEGER NULL;

ALTER TABLE fw.menu_node
    ADD CONSTRAINT fk_menu_node_core_id
        FOREIGN KEY (core_id) REFERENCES fw.core(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_menu_node_core_id
    ON fw.menu_node(core_id)
    WHERE core_id IS NOT NULL;

COMMENT ON COLUMN fw.menu_node.core_id IS
    'Phase 38.4 Krok 11-C (11.5.2026): FK na fw.core. NULL pro folders/iframe/'
    'special. NULL == legacy hardcoded view bez core entry (audit_*, framework_*).';

-- ════════════════════════════════════════════════════════════════════════
-- 2. Backfill — 5 security rows
-- ════════════════════════════════════════════════════════════════════════
-- security_users (row 7) -> fw.core.code='security_users' (Krok 10)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'security_users' LIMIT 1)
WHERE code = 'system.security.users';

-- security_devices (row 8) -> fw.core.code='security_devices' (Krok 8 starsi)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'security_devices' LIMIT 1)
WHERE code = 'system.security.devices';

-- security_whitelists (row 9) -> fw.core.code='security_whitelists' (Krok 10)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'security_whitelists' LIMIT 1)
WHERE code = 'system.security.whitelists';

-- security_audit (row 10) -> fw.core.code='security_audit' (Krok 10-B dnesni rano)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'security_audit' LIMIT 1)
WHERE code = 'system.security.audit';

-- security_invites (row 11) -> fw.core.code='security_invites' (Krok 10)
UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'security_invites' LIMIT 1)
WHERE code = 'system.security.invites';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
-- Co bychom meli videt:
--   - 5 rows s core_id NOT NULL (security_*)
--   - 10 rows s core_id IS NULL (folders + iframe + audit_* + framework_*)
--   - cislo_def zustava beze zmeny

SELECT
    (SELECT COUNT(*) FROM fw.menu_node WHERE core_id IS NOT NULL) AS rows_with_core,
    (SELECT COUNT(*) FROM fw.menu_node WHERE core_id IS NULL) AS rows_without_core,
    (SELECT COUNT(*) FROM fw.menu_node) AS total_rows;
-- Expected: 5 / 10 / 15

-- Detail per row pro lidske oko
SELECT
    n.id AS menu_id,
    n.code AS menu_code,
    n.label,
    n.kind,
    n.cislo_def AS cislo_def_legacy,
    n.core_id,
    c.code AS core_code
FROM fw.menu_node n
LEFT JOIN fw.core c ON c.id = n.core_id
ORDER BY n.id;
-- Expected:
--   Rows 1, 2, 6, 12         -> core_id NULL (folders + iframe)
--   Rows 3, 4, 5             -> core_id NULL (audit_* — fw.core neexistuje yet)
--   Rows 7, 8, 9, 10, 11     -> core_id NOT NULL (security_*, vidime core.code v poslednim sloupci)
--   Rows 13, 14, 15          -> core_id NULL (framework_* — fw.core neexistuje yet)
