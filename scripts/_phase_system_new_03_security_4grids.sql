-- ============================================================
-- Phase SYSTEM NEW — Etapa 3: zbylé 4 security grids
-- ============================================================
-- Datum: 21.5.2026 vecer (post-Etapa 2: trusted_devices LIVE ✓)
--
-- Marti: „SUPER... Dalsi" — dotahujem security batch 4/4:
--   - security_users         → public.users
--   - security_whitelists    → public.global_ip_whitelist
--   - security_invites       → public.trusted_device_invites
--   - security_auth_audit    → public.auth_audit
--
-- Strategie: ATOMIC BEGIN/COMMIT pro vsechny 4 najednou.
--   Pokud cokoliv failne, vse rollback → cisty stav.
--
-- Pattern (na kazdy grid):
--   1. menu_node (leaf pod Security folder id=34)
--   2. fw.core
--   3. UPDATE menu_node SET core_id
--   4. fw.comp_def (grid type_id=306)
--   5. fw.data_source
--   6. UPDATE comp_def SET data_source_id
--   7. fw.data_set s SELECT * (Marti's MVP doctrine 21.5.)
--   8. fw.data_source_op (select/default)
--
-- POZOR: db_connection_id = 1 (PostgreSQL strategie).
--   Pred run oveřit: SELECT id, name FROM fw.db_connection;
--
-- Spusteni v DBeaveru: highlight cely script + Alt+X
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 1/4: security_users (z public.users)               ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.security_users', 'STRATEGIE Users', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    200,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_users');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_users', 'STRATEGIE Users',
    'SYSTEM NEW klon z security_users (HC migration, 21.5.2026)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.security_users');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_users')
WHERE code = 'system_new.security_users' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_users', 'STRATEGIE Users',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_users'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_security_users');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_users',
    'Security: STRATEGIE Users',
    'SYSTEM NEW security_users data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_users');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_users')
WHERE name = 'grid_system_new_security_users' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_users');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_users',
    $sql$
SELECT *
FROM public.users
ORDER BY id
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW security_users: SELECT * z public.users (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_users');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_users'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_users'),
    'select', 'default', TRUE,
    'SYSTEM NEW security_users default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_users')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_users')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_users' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 2/4: security_whitelists (z public.global_ip_whitelist)║
-- ╚══════════════════════════════════════════════════════════╝
-- Pozn.: HC handler UNION s user_ip_whitelist — MVP jen global.
-- Per Marti's „pak optimalizujeme" — UNION dodame v Phase 2.

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_whitelists', 'IP whitelists', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    300,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_whitelists');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_whitelists', 'IP whitelists',
    'SYSTEM NEW klon z security_whitelists (global, HC migration 21.5.)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.security_whitelists');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_whitelists')
WHERE code = 'system_new.security_whitelists' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_whitelists', 'IP whitelists',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_whitelists'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_security_whitelists');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_whitelists',
    'Security: IP whitelists (global)',
    'SYSTEM NEW security_whitelists data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_whitelists');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_whitelists')
WHERE name = 'grid_system_new_security_whitelists' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_whitelists');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_whitelists',
    $sql$
SELECT *
FROM public.global_ip_whitelist
WHERE revoked_at IS NULL
ORDER BY id
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW security_whitelists: SELECT * z public.global_ip_whitelist (MVP, user_ip UNION pozdeji)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_whitelists');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_whitelists'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_whitelists'),
    'select', 'default', TRUE,
    'SYSTEM NEW security_whitelists default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_whitelists')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_whitelists')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_whitelists' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 3/4: security_invites (z public.trusted_device_invites)║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_invites', 'Magic invites', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    400,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_invites');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_invites', 'Magic invites',
    'SYSTEM NEW klon z security_invites (HC migration 21.5.)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.security_invites');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_invites')
WHERE code = 'system_new.security_invites' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_invites', 'Magic invites',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_invites'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_security_invites');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_invites',
    'Security: Magic invites',
    'SYSTEM NEW security_invites data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_invites');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_invites')
WHERE name = 'grid_system_new_security_invites' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_invites');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_invites',
    $sql$
SELECT *
FROM public.trusted_device_invites
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW security_invites: SELECT * z public.trusted_device_invites (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_invites');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_invites'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_invites'),
    'select', 'default', TRUE,
    'SYSTEM NEW security_invites default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_invites')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_invites')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_invites' AND dso.operation_kind = 'select'
  );


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 4/4: security_auth_audit (z public.auth_audit)     ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_auth_audit', 'Auth audit', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.security'),
    500,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.security_auth_audit');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.security_auth_audit', 'Auth audit',
    'SYSTEM NEW klon z security_auth_audit (HC migration 21.5.)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.security_auth_audit');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.security_auth_audit')
WHERE code = 'system_new.security_auth_audit' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_security_auth_audit', 'Auth audit',
    (SELECT id FROM fw.core WHERE code = 'system_new.security_auth_audit'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_security_auth_audit');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.security_auth_audit',
    'Security: Auth audit',
    'SYSTEM NEW security_auth_audit data source (21.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_auth_audit');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.security_auth_audit')
WHERE name = 'grid_system_new_security_auth_audit' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_auth_audit');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.security_auth_audit',
    $sql$
SELECT *
FROM public.auth_audit
ORDER BY id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW security_auth_audit: SELECT * z public.auth_audit (Marti MVP raw)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.security_auth_audit');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.security_auth_audit'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.security_auth_audit'),
    'select', 'default', TRUE,
    'SYSTEM NEW security_auth_audit default select (21.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.security_auth_audit')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.security_auth_audit')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.security_auth_audit' AND dso.operation_kind = 'select'
  );


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_menu INT;
    v_core INT;
    v_compdef INT;
    v_ds INT;
    v_dset INT;
    v_dso INT;
BEGIN
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node WHERE code LIKE 'system_new.security_%';
    SELECT COUNT(*) INTO v_core FROM fw.core WHERE code LIKE 'system_new.security_%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def WHERE name LIKE 'grid_system_new_security_%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source WHERE code LIKE 'system_new.security_%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set WHERE code LIKE 'system_new.security_%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system_new.security_%';

    RAISE NOTICE '--- POST-CHECK (vsechny system_new.security_* rows) ---';
    RAISE NOTICE 'fw.menu_node        = % (expected 5: security folder + 4 grids vč. devices)', v_menu;
    RAISE NOTICE 'fw.core             = % (expected 5)', v_core;
    RAISE NOTICE 'fw.comp_def         = % (expected 5)', v_compdef;
    RAISE NOTICE 'fw.data_source      = % (expected 5)', v_ds;
    RAISE NOTICE 'fw.data_set         = % (expected 5)', v_dset;
    RAISE NOTICE 'fw.data_source_op   = % (expected 5)', v_dso;

    IF v_menu >= 5 AND v_core >= 5 AND v_dset >= 5 AND v_dso >= 5 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: 4 nove security grids hotove. Smoke test:';
        RAISE NOTICE '  1. Hard reload UI';
        RAISE NOTICE '  2. SYSTEM NEW → Security → klik na 4 nove gridy';
        RAISE NOTICE '  3. Vsechny by mely zobrazit data';
        RAISE NOTICE '  4. Side-by-side compare s puvodnimi SYSTEM → Security gridy';
        RAISE NOTICE '------';
    END IF;
END $$;

SELECT
    'menu_node' AS what,
    code,
    label,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.security_%'
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- SMOKE PO COMMITU (hard reload UI):
--   SYSTEM NEW
--     └ Security
--         ├ Trusted devices    (Etapa 2, uz LIVE)
--         ├ STRATEGIE Users    (Etapa 3 grid 1/4)
--         ├ IP whitelists      (Etapa 3 grid 2/4, jen global)
--         ├ Magic invites      (Etapa 3 grid 3/4)
--         └ Auth audit         (Etapa 3 grid 4/4)
--
-- Pokud nektery grid hodi error → pošli mi screenshot Console
-- + Network tab. Bezne problemy:
--
-- A) „relation does not exist" — tabulka v jinem schema nebo nazvana
--    jinak. Najdi v information_schema:
--    SELECT table_name FROM information_schema.tables
--    WHERE table_name LIKE '%trusted%' OR table_name LIKE '%audit%';
--
-- B) „permission denied" — pridat GRANT pro strategie role:
--    GRANT SELECT ON public.<table> TO strategie;
--
-- C) Grid prazdny ale bez chyby — tabulka neobsahuje rows (norma).
-- ============================================================
