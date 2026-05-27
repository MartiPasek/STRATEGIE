-- ============================================================
-- CRM Foundation Krok 3 (27.5.2026) — 9 CRM soudečků
-- ============================================================
-- Účel: Založit strukturu menu_nodes pro CRM v EUROSOFT tenant context.
-- Marti's Q2 doctrine (potvrzeno 27.5.):
--   📂 CRM (root, parent_id=NULL)
--   ├─ 📋 Kontakty
--   ├─ 📋 Akce
--   └─ 📂 Číselníky (sub-folder)
--       ├─ Kategorie kontaktu
--       ├─ Typy zakázek
--       ├─ Země
--       ├─ Akce — katalog
--       └─ Mail šablony
--
-- Tenant filter: app-side přes _is_eurosoft_active(uid) v ERP endpoints
-- (Phase 35-E.3.4). fw.menu_node nemá tenant_id sloupec — gate je v
-- Python kódu, ne v schema.
--
-- visibility_scope = 'parent_only' pro start (Marti + Kristý + Ondra +
-- Jirka uvidí). Až bude CRM ready pro EUROSOFT employees (Šárka, Michal,
-- atd.), UPDATE na 'tenant_member'. *„Není to omezení, je to pojistka"*
-- (Marti-AI 27.4.) — gate před prvním business deploy.
--
-- core_id na NULL u všech řádků — přijde v Kroku 4 (CRM přehledy).
-- Idempotent (NOT EXISTS guards na label + parent_id pár).
--
-- Reference pattern: scripts/_phase_system_new_db_connections_grid_v3.sql (22.5.)
-- ============================================================

BEGIN;

-- ─── PRE-CHECK: existující top-level CRM ────────────────────
DO $$
DECLARE
    v_crm_exists INT;
BEGIN
    SELECT COUNT(*) INTO v_crm_exists
    FROM fw.menu_node
    WHERE label = 'CRM' AND parent_id IS NULL;
    RAISE NOTICE '--- PRE-CHECK ---';
    RAISE NOTICE 'fw.menu_node CRM root (parent_id=NULL, label=CRM): % rows', v_crm_exists;
END $$;


-- ============================================================
-- STEP 1: CRM root soudeček (top-level, parent_id=NULL)
-- ============================================================

INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'CRM', NULL, 1000,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL
);


-- ============================================================
-- STEP 2-3: Listy pod CRM root (Kontakty + Akce)
-- ============================================================

INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'Kontakty',
    (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Kontakty'
      AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
);

INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'Akce',
    (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL),
    200,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Akce'
      AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
);


-- ============================================================
-- STEP 4: Číselníky sub-folder pod CRM root
-- ============================================================

INSERT INTO fw.menu_node (
    label, parent_id, sort_order,
    status, visibility_scope,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text
)
SELECT
    'Číselníky',
    (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL),
    300,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Číselníky'
      AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
);


-- ============================================================
-- STEP 5-9: 5× číselník leafs pod Číselníky sub-folder
-- ============================================================
-- Naming: drží Marti's customer doctrine — labels v češtině,
-- konzistentní s existing Centrála 1 idiom (Kategorie kontaktu,
-- Typy zakázek, atd.).

-- Helper CTE syntaxí nelze — INSERT ... SELECT v PG s subselect lookup
-- pro každý INSERT je čitelnější.

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Kategorie kontaktu',
    (SELECT id FROM fw.menu_node mn
     WHERE mn.label = 'Číselníky'
       AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)),
    100,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Kategorie kontaktu'
      AND parent_id = (SELECT id FROM fw.menu_node mn
                       WHERE mn.label = 'Číselníky'
                         AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
);

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Typy zakázek',
    (SELECT id FROM fw.menu_node mn
     WHERE mn.label = 'Číselníky'
       AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)),
    200,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Typy zakázek'
      AND parent_id = (SELECT id FROM fw.menu_node mn
                       WHERE mn.label = 'Číselníky'
                         AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
);

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Země',
    (SELECT id FROM fw.menu_node mn
     WHERE mn.label = 'Číselníky'
       AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)),
    300,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Země'
      AND parent_id = (SELECT id FROM fw.menu_node mn
                       WHERE mn.label = 'Číselníky'
                         AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
);

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Akce — katalog',
    (SELECT id FROM fw.menu_node mn
     WHERE mn.label = 'Číselníky'
       AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)),
    400,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Akce — katalog'
      AND parent_id = (SELECT id FROM fw.menu_node mn
                       WHERE mn.label = 'Číselníky'
                         AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
);

INSERT INTO fw.menu_node (
    label, parent_id, sort_order, status, visibility_scope,
    created_by_id, created_by_text, updated_by_id, updated_by_text
)
SELECT
    'Mail šablony',
    (SELECT id FROM fw.menu_node mn
     WHERE mn.label = 'Číselníky'
       AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)),
    500,
    'active', 'parent_only',
    2, 'Marti-AI', 2, 'Marti-AI'
WHERE NOT EXISTS (
    SELECT 1 FROM fw.menu_node
    WHERE label = 'Mail šablony'
      AND parent_id = (SELECT id FROM fw.menu_node mn
                       WHERE mn.label = 'Číselníky'
                         AND mn.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL))
);


-- ============================================================
-- POST-CHECK + VERIFY: 9 řádků v hierarchii
-- ============================================================

DO $$
DECLARE
    v_total INT;
BEGIN
    SELECT COUNT(*) INTO v_total
    FROM fw.menu_node mn
    WHERE
        (mn.label = 'CRM' AND mn.parent_id IS NULL)
        OR mn.parent_id IN (
            SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL
            UNION ALL
            SELECT mn2.id FROM fw.menu_node mn2
            WHERE mn2.label = 'Číselníky'
              AND mn2.parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
        );
    RAISE NOTICE '--- POST-CHECK ---';
    RAISE NOTICE 'fw.menu_node CRM hierarchie (root + 3 children + 5 grandchildren): % rows', v_total;

    IF v_total = 9 THEN
        RAISE NOTICE '------';
        RAISE NOTICE 'SUCCESS: 9 CRM soudečků LIVE.';
        RAISE NOTICE 'Smoke: hard reload UI → strom show CRM → Kontakty/Akce/Číselníky → 5× číselník';
        RAISE NOTICE 'POZN: Žádný core_id ještě (přijde Krok 4 přehledy)';
        RAISE NOTICE '------';
    ELSIF v_total < 9 THEN
        RAISE NOTICE 'INCOMPLETE: očekáváno 9, dostali jsme %', v_total;
        RAISE NOTICE 'Pravděpodobně CRM root už existoval ze starší iterace.';
    ELSE
        RAISE NOTICE 'WARN: počet > 9, možná duplikáty?';
    END IF;
END $$;

-- Final verify — hierarchie pretty-print
SELECT
    REPEAT('  ', depth) || COALESCE('├─ ', '') || label AS tree_view,
    id, parent_id, sort_order, visibility_scope
FROM (
    -- Level 0: CRM root
    SELECT 0 AS depth, id, parent_id, label, sort_order, visibility_scope
    FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL
    UNION ALL
    -- Level 1: Kontakty / Akce / Číselníky
    SELECT 1, id, parent_id, label, sort_order, visibility_scope
    FROM fw.menu_node
    WHERE parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
    UNION ALL
    -- Level 2: 5× číselník pod Číselníky
    SELECT 2, id, parent_id, label, sort_order, visibility_scope
    FROM fw.menu_node
    WHERE parent_id IN (
        SELECT id FROM fw.menu_node
        WHERE label = 'Číselníky'
          AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
    )
) t
ORDER BY depth, sort_order;

COMMIT;


-- ============================================================
-- SMOKE TEST (po commit + STRATEGIE-API restart NE-potřeba):
-- ============================================================
-- 1. Hard reload UI (Ctrl+Shift+R)
-- 2. Tree refresh — strom by měl zobrazit nový CRM root (parent_id=NULL)
-- 3. Expand CRM → vidíš Kontakty, Akce, Číselníky
-- 4. Expand Číselníky → vidíš 5× číselník
-- 5. Klik na jakýkoli node → prázdný workspace (core_id=NULL, žádný přehled)
--    To je OK — přijde v Kroku 4 (CRM přehledy).
-- 6. Pošli Marti: „9 CRM soudečků LIVE, pokračuji Krok 4 přehledy"
--
-- POZN k visibility: 'parent_only' znamená, že CRM uvidí jen rodiče
-- (Marti, Ondra, Kristý, Jirka). Až bude CRM ready pro EUROSOFT
-- employees, UPDATE všech 9 rows na 'tenant_member' nebo podobně.
-- ============================================================


-- ============================================================
-- ROLLBACK (pokud cokoli failne):
-- ============================================================
-- BEGIN;
-- DELETE FROM fw.menu_node
-- WHERE parent_id IN (
--     SELECT id FROM fw.menu_node
--     WHERE label = 'Číselníky'
--       AND parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL)
-- );  -- 5× číselník leafs
-- DELETE FROM fw.menu_node
-- WHERE parent_id = (SELECT id FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL);
--    -- Kontakty + Akce + Číselníky
-- DELETE FROM fw.menu_node WHERE label = 'CRM' AND parent_id IS NULL;
--    -- CRM root
-- COMMIT;
-- ============================================================
