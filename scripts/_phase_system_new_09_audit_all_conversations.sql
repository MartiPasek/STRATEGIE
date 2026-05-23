-- ============================================================
-- Phase SYSTEM NEW — Etapa 9: Audit folder + Všechny konverzace
-- ============================================================
-- Datum: 22.5.2026 ranní (po pauze, Marti's „Dobre rano")
-- Marti: „Zbyva nam soudecek Vsechny konverzace k migraci... Pojd"
--
-- Strategie:
--   SYSTEM NEW
--     ├── Security    (Etapa 1-4)
--     ├── Framework   (Etapa 7+7c, 5/5 grids)
--     └── Audit       (Etapa 9 NEW) ← sort=300
--          └── Všechny konverzace   (full chain create, SELECT * z public.conversations)
--
-- Pattern: full chain (8 INSERTs/UPDATEs) — pro audit_overview mode='all'
-- HC handler nikdy nemigroval na FW chain, takže existing core neexistuje.
-- Marti's MVP raw doctrine: SELECT * FROM public.conversations.
--
-- TODO Etapa 9+1: další audit grids (Auditované konverzace, Přehled auditu,
-- Záložkový přehled) — paralelně k tomuto patternu, až Marti řekne.
--
-- POZOR db_connection_id=1.
-- Spusteni: DBeaver Alt+X.
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Audit folder pod SYSTEM NEW                             ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.audit', 'Audit', 'folder',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new'),
    300,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.audit');


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid: Všechny konverzace (z public.conversations)       ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.audit_all_conversations', 'Všechny konverzace', 'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.audit'),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.menu_node WHERE code = 'system_new.audit_all_conversations');

INSERT INTO fw.core (
    code, label, description_user,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'system_new.audit_all_conversations', 'Všechny konverzace',
    'SYSTEM NEW Všechny konverzace: SELECT * z public.conversations (Marti MVP raw)',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.core WHERE code = 'system_new.audit_all_conversations');

UPDATE fw.menu_node
SET core_id = (SELECT id FROM fw.core WHERE code = 'system_new.audit_all_conversations')
WHERE code = 'system_new.audit_all_conversations' AND core_id IS NULL;

INSERT INTO fw.comp_def (
    name, caption, core_id, type_id, region_slot,
    sort_order, is_active,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'grid_system_new_audit_all_conversations', 'Všechny konverzace',
    (SELECT id FROM fw.core WHERE code = 'system_new.audit_all_conversations'),
    306, 'main', 100, TRUE,
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (SELECT 1 FROM fw.comp_def WHERE name = 'grid_system_new_audit_all_conversations');

INSERT INTO fw.data_source (
    code, name, description, refresh_type, status, is_system
)
SELECT
    'system_new.audit_all_conversations',
    'Audit: Všechny konverzace',
    'SYSTEM NEW audit_all_conversations data source (22.5.2026)',
    'manual', 'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.audit_all_conversations');

UPDATE fw.comp_def
SET data_source_id = (SELECT id FROM fw.data_source WHERE code = 'system_new.audit_all_conversations')
WHERE name = 'grid_system_new_audit_all_conversations' AND data_source_id IS NULL
  AND EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.audit_all_conversations');

INSERT INTO fw.data_set (
    code, sql_text, db_connection_id, description, status, is_system
)
SELECT
    'system_new.audit_all_conversations',
    $sql$
SELECT *
FROM public.conversations
ORDER BY last_message_at DESC NULLS LAST, id DESC
LIMIT 1000
    $sql$,
    1,
    'SYSTEM NEW Všechny konverzace: SELECT * z public.conversations (Marti MVP raw, ORDER BY last_message_at DESC)',
    'active', TRUE
WHERE NOT EXISTS (SELECT 1 FROM fw.data_set WHERE code = 'system_new.audit_all_conversations');

INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    variant_code, is_default, description
)
SELECT
    (SELECT id FROM fw.data_source WHERE code = 'system_new.audit_all_conversations'),
    (SELECT id FROM fw.data_set    WHERE code = 'system_new.audit_all_conversations'),
    'select', 'default', TRUE,
    'SYSTEM NEW audit_all_conversations default select (22.5.2026)'
WHERE EXISTS (SELECT 1 FROM fw.data_source WHERE code = 'system_new.audit_all_conversations')
  AND EXISTS (SELECT 1 FROM fw.data_set    WHERE code = 'system_new.audit_all_conversations')
  AND NOT EXISTS (
      SELECT 1 FROM fw.data_source_op dso
      JOIN fw.data_source ds ON ds.id = dso.data_source_id
      WHERE ds.code = 'system_new.audit_all_conversations' AND dso.operation_kind = 'select'
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
    SELECT COUNT(*) INTO v_menu FROM fw.menu_node WHERE code LIKE 'system_new.audit%';
    SELECT COUNT(*) INTO v_core FROM fw.core WHERE code LIKE 'system_new.audit%';
    SELECT COUNT(*) INTO v_compdef FROM fw.comp_def WHERE name LIKE 'grid_system_new_audit%';
    SELECT COUNT(*) INTO v_ds FROM fw.data_source WHERE code LIKE 'system_new.audit%';
    SELECT COUNT(*) INTO v_dset FROM fw.data_set WHERE code LIKE 'system_new.audit%';
    SELECT COUNT(*) INTO v_dso FROM fw.data_source_op dso
        JOIN fw.data_source ds ON ds.id = dso.data_source_id
        WHERE ds.code LIKE 'system_new.audit%';

    RAISE NOTICE '╔════ POST-CHECK Audit ════╗';
    RAISE NOTICE '║ menu_node       = % (folder + 1 grid = 2) ║', v_menu;
    RAISE NOTICE '║ core            = % (1)                   ║', v_core;
    RAISE NOTICE '║ comp_def        = % (1)                   ║', v_compdef;
    RAISE NOTICE '║ data_source     = % (1)                   ║', v_ds;
    RAISE NOTICE '║ data_set        = % (1)                   ║', v_dset;
    RAISE NOTICE '║ data_source_op  = % (1)                   ║', v_dso;
    RAISE NOTICE '╚═══════════════════════════════════════════╝';

    IF v_menu >= 2 AND v_core >= 1 AND v_dset >= 1 AND v_dso >= 1 THEN
        RAISE NOTICE 'SUCCESS: SYSTEM NEW Audit > Všechny konverzace hotov.';
        RAISE NOTICE 'Hard reload UI → SYSTEM NEW → Audit → Všechny konverzace';
    END IF;
END $$;

SELECT
    code,
    label,
    sort_order,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.audit%'
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   Hard reload UI → SYSTEM NEW:
--     ├── Security
--     ├── Framework
--     └── Audit
--          └── Všechny konverzace   ← NEW (1000 conversations max)
--
-- TODO další etapy pro audit family (až Marti řekne):
--   - Auditované konverzace (audited mode, asi WHERE audit_status filter)
--   - Přehled auditu (stats mode, agregace per-persona × month)
--   - Záložkový přehled (tabs mode, vícezáložková kompozice)
-- ============================================================
