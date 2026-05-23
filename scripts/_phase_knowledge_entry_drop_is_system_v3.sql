-- ═══════════════════════════════════════════════════════════════════════
-- knowledge_entry #1 update v3 (21.5.2026 vecer):
-- APPEND warning sekce o fw.menu_node — sloupec `is_system` NEEXISTUJE.
-- Visibility ovladame pres `visibility_scope` text enum.
--
-- Trigger: Claude (21.5.) napsal Phase SYSTEM NEW migration script po
-- Marti-AI's navodu (Krok 1 INSERT INTO fw.menu_node s is_system).
-- DBeaver vratil: column "is_system" of relation "menu_node" does not exist.
-- Marti: "jo jeste jsme neopravili ten navod. Promin" — sem dochazi
-- aktualizace navodu pro pristi spusteni.
--
-- Pozn.: `fw.core` jeste neopraveno explicit pro INSERT v Krok 2 — staci
-- na to upozornit (layout_type uz mas v v2, plus connect to Krok 2 priklad).
--
-- Run: DBeaver strategie session jako "Marti-AI" (GRANT UPDATE z DDL).
--   Highlight cely soubor + Alt+X (atomic).
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE public.knowledge_entry
SET body_markdown = body_markdown || E'\n\n---\n\n'
        || E'## ⚠ fw.menu_node — `is_system` NEEXISTUJE (21.5.2026)\n\n'
        || E'**Marti-AI''s puvodni navod ma chybu — Krok 1 INSERT INTO fw.menu_node\n'
        || E'obsahuje `is_system` sloupec, ktery v schema NENI.**\n\n'
        || E'### Real schema fw.menu_node (potvrzeno z router.py + sprint_d_DDL):\n\n'
        || E'`id` (IDENTITY auto), `code`, `label`, `kind`, `parent_id`,\n'
        || E'`sort_order`, `status`, `visibility_scope`, `cislo_def`,\n'
        || E'`framework_jadro_id`, `special_handler`, `is_immutable`,\n'
        || E'`description_user`, `description_system`, `core_id`,\n'
        || E'`created_at` (DEFAULT), `created_by_id`, `created_by_text`,\n'
        || E'`updated_at` (trigger), `updated_by_id`, `updated_by_text`\n\n'
        || E'### Visibility — `visibility_scope` TEXT enum, ne `is_system` BOOLEAN:\n\n'
        || E'- `''parent_only''` — jen rodice (Marti, Ondra, Kristy, Jirka). System uzly.\n'
        || E'- `''tenant_member''` — vsichni v aktivnim tenantu.\n'
        || E'- `''public''` — public.\n'
        || E'- `NULL` — default = visible v System tree (parent-only audience).\n\n'
        || E'`_build_system_root_from_db` v router.py:8943 filtruje:\n'
        || E'`WHERE n.status = ''active'' AND (n.visibility_scope = ''parent_only'' OR n.visibility_scope IS NULL)`\n\n'
        || E'### Spravny INSERT priklad fw.menu_node (System uzel):\n\n'
        || E'```sql\n'
        || E'INSERT INTO fw.menu_node (\n'
        || E'    code, label, kind, parent_id, sort_order,\n'
        || E'    status, visibility_scope, is_immutable,\n'
        || E'    description_user,\n'
        || E'    created_by_id, created_by_text,\n'
        || E'    updated_by_id, updated_by_text\n'
        || E') VALUES (\n'
        || E'    ''system_new.muj_grid'',  -- code (dotted namespace)\n'
        || E'    ''Muj grid'',              -- label\n'
        || E'    ''form'',                  -- kind: ''folder''|''form''|''list''\n'
        || E'    <parent_id_or_NULL>,      -- parent_id (NULL = top-level)\n'
        || E'    100,                      -- sort_order\n'
        || E'    ''active'',                -- status\n'
        || E'    ''parent_only'',           -- visibility_scope (System uzel = rodice)\n'
        || E'    FALSE,                    -- is_immutable\n'
        || E'    ''Popis pro uzivatele'',   -- description_user\n'
        || E'    2, ''Marti-AI'',           -- created_by\n'
        || E'    2, ''Marti-AI''            -- updated_by\n'
        || E') RETURNING id;\n'
        || E'```\n\n'
        || E'**POZOR**: `id` je IDENTITY — NEVYPLNUJ.\n'
        || E'`core_id` zustane NULL pro folder/sub-folder. Pro leaf (`kind=''form''`)\n'
        || E'se nastavi UPDATE po vytvoreni fw.core (Krok 5 v puvodnim postupu).\n\n'
        || E'### Krok 1 v puvodnim postupu (oprava):\n\n'
        || E'**Stary INSERT obsahuje `is_system` — sloupec NEEXISTUJE.**\n'
        || E'Pouzivej INSERT priklad nahore. `visibility_scope=''parent_only''`\n'
        || E'zaridi viditelnost System uzlu jen pro rodice.\n\n'
        || E'### Souhrn vsech NOT NULL sloupcu po slim cleanup:\n\n'
        || E'| Tabulka | NOT NULL bez default |\n'
        || E'|---|---|\n'
        || E'| `fw.menu_node` | `code`, `label`, `kind`, `sort_order`, `status` (default ''active''), `created_by_text`, `updated_by_text` |\n'
        || E'| `fw.core` | `code`, `created_by_text`, `updated_by_text` |\n'
        || E'| `fw.comp_def` | `name`, `type_id`, `created_by_text`, `updated_by_text` |\n'
        || E'| `fw.data_source` | `name`, `version` |\n'
        || E'| `fw.data_set` | `sql_text`, `db_connection_id`, `version` |\n'
        || E'| `fw.data_source_op` | `data_source_id`, `data_set_id`, `operation_kind` |\n\n'
        || E'**Defensive workflow**: pred INSERT do nove tabulky vzdy `\\d fw.<table>`\n'
        || E'v DBeaveru — overit aktualni column list. Tatinkova `fw.core slim`\n'
        || E'a `fw.menu_node` cleanup zmen muzou byt mezi mou pameti a real DB.\n\n'
        || E'---\n\n'
        || E'*Doplneno 21.5.2026 po SYSTEM NEW migration trigger.\n'
        || E'Krok 1 INSERT fw.menu_node oprava — drop `is_system`, use `visibility_scope`.*'
    ,
    updated_at = NOW()
WHERE id = 1
  AND body_markdown NOT LIKE '%fw.menu_node — `is_system` NEEXISTUJE%';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY:
-- ════════════════════════════════════════════════════════════════════════
-- SELECT id, title, length(body_markdown) AS body_len,
--        body_markdown LIKE '%fw.menu_node — `is_system` NEEXISTUJE%' AS marker_added
-- FROM public.knowledge_entry WHERE id=1;
-- Expected: marker_added=TRUE, body_len ~ 11500 (po v2 ~9300 + ~2200)
