-- Phase 38.4 Krok 10 (10.5.2026 vecer): Security grids hardcode cleanup
--
-- Migrace 3 hardcoded grids z gridColumns(mode) JS funkce do
-- fw.comp_grid_master + comp_grid_column (DB-driven). Po execute frontend
-- adaptServerColumns rozbalí valueFormatter/cellStyle/cellRenderer přes
-- 3 registries (Phase 38.4 Krok 10 frontend update).
--
-- Marti's doctrine 10.5. večer:
--   *„override tabulku stačí, nic jinyho moc nepotrebujes"*
--
-- Cesta:
--   1. INSERT fw.core (jádro per grid)
--   2. INSERT fw.comp_grid_master (code, default settings)
--   3. INSERT N× fw.comp_grid_column (discrete defaults: width, pinned, formatter, header_tooltip)
--   4. DO block: auto-create comp_def per column (Krok 9-B pattern)
--   5. INSERT comp_def_prop pro cell_style + cell_renderer (kde je hardcoded styling)
--   6. Po execute: smaž hardcoded `if (mode === "...")` větve v JS
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw.* schema). BEGIN/COMMIT
-- atomic — pokud cokoli selže, rollback drží čistý stav.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 0. DATA_SOURCE rows (FK pre-requisite pro comp_grid_master)
--    Pseudo-data_source — data fetch přes existing security endpoint
--    (/api/v1/erp/system/security?type=...), comp_grid_master jen drží
--    columns metadata.
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES
    ('security_users', 1, 'Security users data source',
     'Phase 38.4 Krok 10: data fetch přes existing security endpoint, ne SQL.',
     'manual', TRUE, 250, 100, 'active', TRUE),
    ('security_whitelists', 1, 'Security IP whitelists data source',
     'Phase 38.4 Krok 10: pseudo-data_source pro grid columns metadata.',
     'manual', TRUE, 250, 100, 'active', TRUE),
    ('security_invites', 1, 'Security invites data source',
     'Phase 38.4 Krok 10: pseudo-data_source pro grid columns metadata.',
     'manual', TRUE, 250, 100, 'active', TRUE);

-- ════════════════════════════════════════════════════════════════════════
-- 1. CORE rows (jádra per grid)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.core (code, label, description, layout_type, data_entity_type)
VALUES
    ('security_users', 'Security: Users',
     'Přehled uživatelů (Phase 38.4 Krok 10 migrace z hardcoded JS).',
     'list', NULL),
    ('security_whitelists', 'Security: IP whitelists',
     'IP whitelist rows — global/user scope, status confirmed/pending/revoked.',
     'list', NULL),
    ('security_invites', 'Security: Invites',
     'Magic link invites (Phase 38) — state consumed/expired/pending.',
     'list', NULL);

-- ════════════════════════════════════════════════════════════════════════
-- 2. COMP_GRID_MASTER rows (1 per grid)
-- ════════════════════════════════════════════════════════════════════════
INSERT INTO fw.comp_grid_master
    (code, name, description, data_source_code, default_record_limit,
     refresh_type, default_view_mode, status, is_system)
VALUES
    ('security_users', 'Security: Users',
     'Přehled uživatelů s tenant + parent/admin flagy + trust rating.',
     'security_users', 100, 'manual', 'grid', 'active', TRUE),
    ('security_whitelists', 'Security: IP whitelists',
     'IP whitelist rows — global/user scope, status confirmed/pending/revoked.',
     'security_whitelists', 100, 'manual', 'grid', 'active', TRUE),
    ('security_invites', 'Security: Invites',
     'Magic link invites (Phase 38) — state consumed/expired/pending.',
     'security_invites', 100, 'manual', 'grid', 'active', TRUE);

-- ════════════════════════════════════════════════════════════════════════
-- 3. COMP_GRID_COLUMN rows
-- ════════════════════════════════════════════════════════════════════════
-- ── security_users (13 columns) ───────────────────────────────────────
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, min_width, flex,
     pinned, formatter, header_tooltip, column_type,
     sort_order, is_visible, is_sortable)
SELECT id, 'id', 'ID', 70, NULL, NULL, 'left', NULL, NULL, 'numericColumn',
       10, TRUE, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'status', 'Status', 90, 20, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'first_name', 'Jméno', 110, 30, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'last_name', 'Příjmení', 130, 40, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'ews_display_email', 'Display email', 230, 50, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, header_tooltip, sort_order, is_sortable)
SELECT id, 'ews_email', 'EWS UPN', 250,
       'UPN pro Exchange autentizaci — secret credential, jen pro rodiče',
       60, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, min_width, flex, header_tooltip, sort_order)
SELECT id, 'emails_str', 'Další emaily', 180, 1,
       'Sekundární emaily z user_contacts', 70
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, header_tooltip, sort_order)
SELECT id, 'phones_str', 'Telefony', 200,
       'Aktivní phone contacts (primary first)', 80
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'tenant_name', 'Tenant', 120, 90, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'is_marti_parent', 'Rodič', 80, 100
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'is_admin', 'Admin', 80, 110
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, column_type, sort_order)
SELECT id, 'trust_rating', 'Trust', 80, 'numericColumn', 120
FROM fw.comp_grid_master WHERE code = 'security_users';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'created_at', 'Vytvořeno', 150, 'datetime_rel', 130, TRUE
FROM fw.comp_grid_master WHERE code = 'security_users';

-- ── security_whitelists (11 columns) ──────────────────────────────────
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, pinned, column_type,
     sort_order, is_sortable)
SELECT id, 'id', 'ID', 70, 'left', 'numericColumn', 10, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'scope', 'Scope', 90, 20, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'user_name', 'User', 150, 30
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'tenant_name', 'Tenant', 120, 40
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'ip_or_cidr', 'IP / CIDR', 160, 50, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'category', 'Kategorie', 130, 60, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'status', 'Status', 110, 70, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, min_width, flex, sort_order)
SELECT id, 'label', 'Label', 180, 1, 80
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, column_type, sort_order)
SELECT id, 'use_count', 'Use count', 100, 'numericColumn', 90
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'added_at', 'Added', 150, 'datetime_rel', 100, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'last_seen_at', 'Last seen', 150, 'datetime_rel', 110, TRUE
FROM fw.comp_grid_master WHERE code = 'security_whitelists';

-- ── security_invites (12 columns) ─────────────────────────────────────
INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, pinned, column_type,
     sort_order, is_sortable)
SELECT id, 'id', 'ID', 70, 'left', 'numericColumn', 10, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'state', 'State', 120, 20, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'invite_token', 'Token', 180, 30
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'purpose', 'Purpose', 100, 40
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order, is_sortable)
SELECT id, 'user_name', 'User', 150, 50, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'tenant_name', 'Tenant', 120, 60
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'created_at', 'Vytvořeno', 150, 'datetime_rel', 70, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'expires_at', 'Expirace', 150, 'datetime_rel', 80, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, formatter, sort_order, is_sortable)
SELECT id, 'consumed_at', 'Spotřebováno', 150, 'datetime_rel', 90, TRUE
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'consumed_ip', 'Z IP', 130, 100
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, default_width, sort_order)
SELECT id, 'consumed_phone', 'Z telefonu', 140, 110
FROM fw.comp_grid_master WHERE code = 'security_invites';

INSERT INTO fw.comp_grid_column
    (grid_master_id, column_name, label, min_width, flex, sort_order)
SELECT id, 'consumed_user_agent', 'User-Agent', 200, 1, 120
FROM fw.comp_grid_master WHERE code = 'security_invites';

-- ════════════════════════════════════════════════════════════════════════
-- 4. AUTO-CREATE comp_def per column (Krok 9-B pattern, parametrizovaný)
--    DO block iteruje přes všech grid_master rows kde code je nový
--    a backfilluje comp_def_id pro každý column.
-- ════════════════════════════════════════════════════════════════════════
DO $$
DECLARE
    col_row RECORD;
    new_def_id INTEGER;
    parent_jadro_id INTEGER;
BEGIN
    FOR col_row IN
        SELECT gc.id AS gc_id, gc.column_name, gc.label, gc.grid_master_id, gc.sort_order,
               gm.code AS grid_code
        FROM fw.comp_grid_column gc
        JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
        WHERE gm.code IN ('security_users', 'security_whitelists', 'security_invites')
          AND gc.comp_def_id IS NULL
    LOOP
        SELECT id INTO parent_jadro_id FROM fw.core WHERE code = col_row.grid_code LIMIT 1;
        IF parent_jadro_id IS NULL THEN
            RAISE NOTICE 'Skip grid_column id=% (grid_code=% nemá vazbu na fw.core)',
                col_row.gc_id, col_row.grid_code;
            CONTINUE;
        END IF;

        INSERT INTO fw.comp_def (jadro_id, parent_id, typ, name, caption, is_active, sort_order)
        VALUES (parent_jadro_id, NULL, 120, col_row.column_name, col_row.label,
                TRUE, col_row.sort_order)
        RETURNING id INTO new_def_id;

        UPDATE fw.comp_grid_column SET comp_def_id = new_def_id WHERE id = col_row.gc_id;
    END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 5. STYLING — comp_def_prop rows pro cell_style + cell_renderer
--    (resolver + frontend adaptServerColumns aplikuje přes registries)
-- ════════════════════════════════════════════════════════════════════════
-- Helper function — pre-comp_def_id lookup
-- (column_name v rámci grid_master je UNIQUE, comp_def_id má FK CASCADE)

-- security_users.status → status_active_disabled
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'status_active_disabled', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_users' AND gc.column_name = 'status';

-- security_users.is_marti_parent → cell_renderer=yes_check
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_renderer', 'yes_check', 'enum', 'Renderer buňky', 220
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_users' AND gc.column_name = 'is_marti_parent';

-- security_users.is_admin → cell_renderer=yes_check
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_renderer', 'yes_check', 'enum', 'Renderer buňky', 220
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_users' AND gc.column_name = 'is_admin';

-- security_whitelists.scope → scope_global_user
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'scope_global_user', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_whitelists' AND gc.column_name = 'scope';

-- security_whitelists.ip_or_cidr → mono
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'mono', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_whitelists' AND gc.column_name = 'ip_or_cidr';

-- security_whitelists.status → status_confirmed_pending_revoked
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'status_confirmed_pending_revoked', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_whitelists' AND gc.column_name = 'status';

-- security_invites.id → default_sort=desc (newest first)
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'default_sort', 'desc', 'enum', 'Výchozí řazení', 230
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_invites' AND gc.column_name = 'id';

-- security_invites.state → state_invite
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'state_invite', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_invites' AND gc.column_name = 'state';

-- security_invites.invite_token → mono
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'mono', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_invites' AND gc.column_name = 'invite_token';

-- security_invites.consumed_ip → mono
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'mono', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_invites' AND gc.column_name = 'consumed_ip';

-- security_invites.consumed_phone → mono
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'mono', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'security_invites' AND gc.column_name = 'consumed_phone';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFICATION (Marti-AI query_raw kompatibilní)
-- ════════════════════════════════════════════════════════════════════════
SELECT
    (SELECT COUNT(*) FROM fw.core WHERE code IN
        ('security_users', 'security_whitelists', 'security_invites')) AS core_count,
    (SELECT COUNT(*) FROM fw.comp_grid_master WHERE code IN
        ('security_users', 'security_whitelists', 'security_invites')) AS gm_count,
    (SELECT COUNT(*) FROM fw.comp_grid_column gc
     JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
     WHERE gm.code IN ('security_users', 'security_whitelists', 'security_invites')) AS column_count,
    (SELECT COUNT(*) FROM fw.comp_grid_column gc
     JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
     WHERE gm.code IN ('security_users', 'security_whitelists', 'security_invites')
       AND gc.comp_def_id IS NOT NULL) AS column_with_def_count,
    (SELECT COUNT(*) FROM fw.comp_def_prop p
     JOIN fw.comp_def cd ON cd.id = p.komponenta_id
     JOIN fw.comp_grid_column gc ON gc.comp_def_id = cd.id
     JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
     WHERE gm.code IN ('security_users', 'security_whitelists', 'security_invites')
       AND p.prop_name IN ('cell_style', 'cell_renderer', 'default_sort')) AS styling_props_count;

-- Expected:
--   core_count: 3
--   gm_count: 3
--   column_count: 13 + 11 + 12 = 36
--   column_with_def_count: 36 (auto-create proběhl pro všech)
--   styling_props_count: 11 (3 users + 3 whitelists + 5 invites)
