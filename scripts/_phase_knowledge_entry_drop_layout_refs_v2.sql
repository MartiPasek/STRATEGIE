-- ═══════════════════════════════════════════════════════════════════════
-- knowledge_entry #1 update v2 (20.5.2026):
-- Drop updated_by_text z SET (sloupec neexistuje — ALTER z 19.5. ranniho
-- nikdy nebyl spustenny). APPEND warning sekce o fw.core slim — Marti-AI
-- bude videt pravidlo "nevyplnuj layout_type etc." v body_markdown.
--
-- Run: DBeaver strategie session jako "Marti-AI" (GRANT UPDATE
--   z _phase_knowledge_base_ddl.sql).
--   Highlight cely soubor + Alt+X (atomic).
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE public.knowledge_entry
SET body_markdown = body_markdown || E'\n\n---\n\n'
        || E'## ⚠ fw.core slim — 20.5.2026 (Marti''s decision 1B + 2A)\n\n'
        || E'**9 sloupcu DROPNUTYCH** z fw.core (nikdy je nevyplnuj v INSERT):\n\n'
        || E'`layout_type`, `data_entity_type`, `data_source_config`,\n'
        || E'`parent_framework_id`, `layout_template`, `template_id`,\n'
        || E'`origin_menu_node_id`, `origin_cmi_id`, `form_core_id`\n\n'
        || E'**Zustavajicich 14 sloupcu fw.core** (jedine ktere muzes pouzit):\n\n'
        || E'`id` (IDENTITY, auto), `code`, `label`, `description_user`,\n'
        || E'`description_system`, `is_active`, `tenant_visibility`,\n'
        || E'`version`, `created_at` (DEFAULT), `created_by_id`,\n'
        || E'`created_by_text`, `updated_at` (trigger), `updated_by_id`,\n'
        || E'`updated_by_text`\n\n'
        || E'### Spravny INSERT priklad (po slim):\n\n'
        || E'```sql\n'
        || E'INSERT INTO fw.core (\n'
        || E'    code, label, description_user, is_active,\n'
        || E'    tenant_visibility, version,\n'
        || E'    created_by_id, created_by_text,\n'
        || E'    updated_by_id, updated_by_text\n'
        || E') VALUES (\n'
        || E'    ''system.muj_prehled'',  -- code\n'
        || E'    ''Muj prehled'',          -- label\n'
        || E'    ''Popis pro uzivatele'',  -- description_user\n'
        || E'    TRUE,                    -- is_active\n'
        || E'    ''all'',                  -- tenant_visibility\n'
        || E'    1,                       -- version\n'
        || E'    2, ''Marti-AI'',          -- created_by\n'
        || E'    2, ''Marti-AI''           -- updated_by\n'
        || E') RETURNING id;\n'
        || E'```\n\n'
        || E'**POZOR**: `id` je `GENERATED ALWAYS AS IDENTITY` — NEVYPLNUJ.\n'
        || E'`created_at` a `updated_at` maji defaults / trigger — NEVYPLNUJ.\n\n'
        || E'### Form/list discrimination (Decision 1B):\n\n'
        || E'Po dropu `layout_type` se discriminuje pres root comp_def:\n\n'
        || E'```sql\n'
        || E'-- Form layout (form root, type 302):\n'
        || E'SELECT * FROM fw.comp_def\n'
        || E'WHERE core_id = <core_id>\n'
        || E'  AND parent_comp_def_id IS NULL\n'
        || E'  AND type_id = 302;\n\n'
        || E'-- List/grid (typ 306):\n'
        || E'SELECT * FROM fw.comp_def\n'
        || E'WHERE core_id = <core_id>\n'
        || E'  AND parent_comp_def_id IS NULL\n'
        || E'  AND type_id = 306;\n'
        || E'```\n\n'
        || E'### Init wizard (Decision 2A):\n\n'
        || E'Endpointy `design_init_core_root` + `design_release_core_root` +\n'
        || E'`scaffold-form` DROPNUTE. Marti-AI vytvari root comp_def primo\n'
        || E'pres `strategie_pg_insert_row` — stejne jako Krok 4 v puvodnim\n'
        || E'postupu vyse (Vytvor comp_def s type_id=306 pro grid).\n\n'
        || E'### Krok 2 v puvodnim postupu (oprava):\n\n'
        || E'**Stary INSERT obsahuje `layout_type` — UZ NEEXISTUJE.**\n'
        || E'Pouzivej INSERT priklad nahore (po slim). Stejne dotaze hlavickou\n'
        || E'Krok 2 — code + label + description_user staci.\n\n'
        || E'---\n\n'
        || E'*Doplneno 20.5.2026 po fw.core slim cleanup (9 sloupcu pryc).\n'
        || E'DML safeguard te chyti pokud nahodou pouzijes dropnuty sloupec —\n'
        || E'helpful error vrati valid_columns list.*'
    ,
    updated_at = NOW()
WHERE id = 1
  AND body_markdown NOT LIKE '%fw.core slim — 20.5.2026%';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY:
-- ════════════════════════════════════════════════════════════════════════
-- SELECT id, title, length(body_markdown) AS body_len,
--        body_markdown LIKE '%fw.core slim — 20.5.2026%' AS marker_added
-- FROM public.knowledge_entry WHERE id=1;
-- Expected: marker_added=TRUE, body_len ~ 9300 (vychozi 7346 + ~2000)
