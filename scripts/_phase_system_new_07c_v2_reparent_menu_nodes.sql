-- ============================================================
-- Phase SYSTEM NEW — Etapa 7c v2: REPARENT menu_node (NO duplicate)
-- ============================================================
-- Datum: 21.5.2026 vecer
-- Marti: „Ty se prenesou jen upravou menu node... Vsechno ostatni
--          zustane... Neni potreba prehledy duplikovat"
--
-- Etapa 8 smazala stara menu_node (parent_id = stara system.framework
-- folder). Ale fw.core + fw.comp_def + fw.data_source + fw.data_set
-- + fw.data_source_op pro Prehled datasourcu / Knowledge Entries /
-- Znalostni baze JSOU STALE V DB — jejich codes nezacinaji
-- 'system.framework.' patternem, takze Etapa 8 je nedotkla.
--
-- Tento script:
--   1. DIAGNOSTIC: najit existing fw.core rows pro 3 grids
--   2. INSERT 3 nove menu_node rows s parent=system_new.framework
--      a core_id=found (REUSE existing core stack)
--
-- VYHODA reuse: zachova vsechny grid settings, columns, layouts,
-- data_source_op variants. Marti's UI sestavy/pravidla zustanou.
--
-- POZOR: pokud DIAGNOSTIC vrati 0 rows pro nektery grid, existing
-- core neexistuje (asi Marti's Etapa 8 to vse smazala). Pak budeme
-- muset vrátit puvodni Etapa 7c approach (full chain create).
--
-- Spusteni: DBeaver Alt+X
-- ============================================================

BEGIN;

-- ============================================================
-- DIAGNOSTIC: najit existing fw.core kandidaty
-- ============================================================

DO $$
DECLARE
    v_ds_count INT;
    v_kn_e_count INT;
    v_kn_t_count INT;
BEGIN
    SELECT COUNT(*) INTO v_ds_count FROM fw.core
        WHERE code LIKE '%data_sources_overview%'
           OR code LIKE '%datasource%overview%'
           OR label LIKE 'Přehled datasourc%';
    SELECT COUNT(*) INTO v_kn_e_count FROM fw.core
        WHERE code LIKE '%knowledge_entr%' OR label LIKE 'Knowledge Entr%';
    SELECT COUNT(*) INTO v_kn_t_count FROM fw.core
        WHERE code LIKE '%knowledge_topic%' OR label LIKE 'Znalostn%';

    RAISE NOTICE '╔════ DIAGNOSTIC: existing cores ════╗';
    RAISE NOTICE '║ Přehled datasourců = % cores ║', v_ds_count;
    RAISE NOTICE '║ Knowledge Entries  = % cores ║', v_kn_e_count;
    RAISE NOTICE '║ Znalostní báze     = % cores ║', v_kn_t_count;
    RAISE NOTICE '╚════════════════════════════════╝';
END $$;

-- List explicit kandidati
SELECT
    'EXISTING core kandidat' AS what,
    id::text AS id,
    code,
    label,
    'description=' || COALESCE(LEFT(description_user, 50), 'NULL') AS info
FROM fw.core
WHERE code LIKE '%data_sources_overview%'
   OR code LIKE '%datasource%overview%'
   OR code LIKE '%knowledge_entr%'
   OR code LIKE '%knowledge_topic%'
   OR label LIKE 'Přehled datasourc%'
   OR label LIKE 'Knowledge Entr%'
   OR label LIKE 'Znalostn%'
ORDER BY id;


-- ============================================================
-- INSERT 3 menu_node rows (REPARENT pres new menu_node entry)
-- ============================================================
-- Strategie: INSERT s core_id=(SELECT ... FROM fw.core WHERE ...)
-- — pokud SELECT vrati NULL (core neexistuje), core_id=NULL → menu_node
-- bude vytvoreny ale leaf bez attached core. To Marti opravi manualne
-- nebo spustime full chain create scrript.

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 1/3: Přehled datasourců                            ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    core_id,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_data_sources_overview',
    'Přehled datasourců',
    'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    400,
    'active', 'parent_only',
    (SELECT id FROM fw.core
     WHERE code LIKE '%data_sources_overview%' OR code LIKE '%datasource%overview%'
        OR label LIKE 'Přehled datasourc%'
     ORDER BY id LIMIT 1),
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_data_sources_overview'
);

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 2/3: Knowledge Entries                             ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    core_id,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_entries',
    'Knowledge Entries',
    'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    500,
    'active', 'parent_only',
    (SELECT id FROM fw.core
     WHERE code LIKE '%knowledge_entr%' OR label LIKE 'Knowledge Entr%'
     ORDER BY id LIMIT 1),
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_knowledge_entries'
);

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Grid 3/3: Znalostní báze                                ║
-- ╚══════════════════════════════════════════════════════════╝

INSERT INTO fw.menu_node (
    code, label, kind, parent_id, sort_order,
    status, visibility_scope,
    core_id,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'system_new.framework_knowledge_topics',
    'Znalostní báze',
    'form',
    (SELECT id FROM fw.menu_node WHERE code = 'system_new.framework'),
    600,
    'active', 'parent_only',
    (SELECT id FROM fw.core
     WHERE code LIKE '%knowledge_topic%' OR label LIKE 'Znalostn%'
     ORDER BY id LIMIT 1),
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE code = 'system_new.framework_knowledge_topics'
);


-- ============================================================
-- POST-CHECK
-- ============================================================

DO $$
DECLARE
    v_total INT;
    v_with_core INT;
    v_without_core INT;
BEGIN
    SELECT COUNT(*) INTO v_total FROM fw.menu_node WHERE code LIKE 'system_new.framework%';
    SELECT COUNT(*) INTO v_with_core FROM fw.menu_node
        WHERE code LIKE 'system_new.framework%' AND core_id IS NOT NULL;
    SELECT COUNT(*) INTO v_without_core FROM fw.menu_node
        WHERE code LIKE 'system_new.framework%' AND core_id IS NULL
          AND kind = 'form';  -- jen form leafs (folder ma core_id NULL by design)

    RAISE NOTICE '╔════ POST-CHECK ════╗';
    RAISE NOTICE '║ Framework rows total          = % ║', v_total;
    RAISE NOTICE '║ s core_id (wired)             = % ║', v_with_core;
    RAISE NOTICE '║ form leafs bez core_id (NULL) = % ║', v_without_core;
    RAISE NOTICE '╚═════════════════════╝';

    IF v_without_core > 0 THEN
        RAISE NOTICE 'POZOR: % form leafs ma core_id=NULL — existing core nenalezen.', v_without_core;
        RAISE NOTICE 'Marti: zkontroluj VERIFY list + bud upravit code WHERE pattern,';
        RAISE NOTICE 'nebo spustit Etapa 7c v1 (full chain create) pro chybejici.';
    ELSE
        RAISE NOTICE 'SUCCESS: vsechny form leafs maji core_id wired.';
        RAISE NOTICE 'Hard reload UI → Framework → 5 polozek live.';
    END IF;
END $$;

SELECT
    code,
    label,
    sort_order,
    'core_id=' || COALESCE(core_id::text, 'NULL') AS info
FROM fw.menu_node
WHERE code LIKE 'system_new.framework%'
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- PO COMMITU:
--   Hard reload UI → SYSTEM NEW → Framework:
--     ├── DataSets                 (Etapa 7)
--     ├── Definice levého stromu   (Etapa 7)
--     ├── Přehled datasourců       (Etapa 7c v2) ← REUSED core
--     ├── Knowledge Entries        (Etapa 7c v2) ← REUSED core
--     └── Znalostní báze           (Etapa 7c v2) ← REUSED core
--
-- POKUD nektery grid ma „nelze nacist" error:
--   - core_id je NULL (existing core nenalezen)
--   - Najit manualne: SELECT * FROM fw.core ORDER BY id DESC LIMIT 20
--   - UPDATE fw.menu_node SET core_id = <id> WHERE code = '<system_new.framework_X>'
-- ============================================================
