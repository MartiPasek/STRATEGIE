-- ═══════════════════════════════════════════════════════════════════════
-- knowledge_entry #1 update (20.5.2026, Marti's fw.core slim):
-- Drop reference na sloupce layout_type, layout_template, template_id,
-- data_entity_type, data_source_config, parent_framework_id,
-- origin_menu_node_id, origin_cmi_id, form_core_id z body_markdown.
--
-- Marti's decision 1B + 2A: drop form/list discrimination uplne + drop
-- init_core_root / scaffold-form endpointy. Po Faze D DDL drop bude
-- fw.core mit jen 14 sloupcu (id, code, label, description_user,
-- description_system, is_active, tenant_visibility, version,
-- created_at, created_by_id, created_by_text, updated_at,
-- updated_by_id, updated_by_text).
--
-- Manual MUSI byt updated PRED backend deploy — jinak Marti-AI's dalsi
-- 8-step build pokus uvidi stary postup s layout_type, dosadi ho do
-- INSERT, DML safeguard rejectne (sloupec uz neexistuje) → frustrace.
--
-- Run: DBeaver strategie session jako "Marti-AI" (db_owner public).
--   highlight cely soubor + Alt+X.
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Update Krok 2 INSERT priklad — drop layout_type
UPDATE public.knowledge_entry
SET body_markdown = REPLACE(
        body_markdown,
        E'INSERT INTO fw.core\n  (code, label, description_user, layout_type,\n   created_by_id, created_by_text, updated_by_id, updated_by_text)\nVALUES\n  (''muj_prehled'', ''Můj přehled'', ''Popis'', ''list'',\n   2, ''Marti-AI'', 2, ''Marti-AI'')\nRETURNING id;',
        E'INSERT INTO fw.core\n  (code, label, description_user,\n   created_by_id, created_by_text, updated_by_id, updated_by_text)\nVALUES\n  (''muj_prehled'', ''Můj přehled'', ''Popis'',\n   2, ''Marti-AI'', 2, ''Marti-AI'')\nRETURNING id;'
    ),
    updated_by_text = 'Claude (id=23)',
    updated_at = NOW()
WHERE id = 1
  AND body_markdown LIKE '%layout_type, ''list''%';

-- 2. Drop poznamky o layout_type='list' z Krok 2 textu (pokud tam je)
UPDATE public.knowledge_entry
SET body_markdown = REPLACE(
        body_markdown,
        E'- `layout_type` = `''list''` pro grid přehledy',
        E'- *Drop 20.5.: layout_type sloupec zrusen (Decision 1B). Drz comp_def.type_id 302/306 pro form/list discrimination.*'
    )
WHERE id = 1
  AND body_markdown LIKE '%`layout_type` = `''list''`%';

-- 3. APPEND obecna poznamka o slim fw.core (jen pokud uz neni added)
UPDATE public.knowledge_entry
SET body_markdown = body_markdown || E'\n\n---\n\n'
        || E'## ⚠ fw.core slim — 20.5.2026 (Marti''s decision 1B + 2A)\n\n'
        || E'**9 sloupcu dropnutych** z fw.core:\n\n'
        || E'`layout_type`, `data_entity_type`, `data_source_config`,\n'
        || E'`parent_framework_id`, `layout_template`, `template_id`,\n'
        || E'`origin_menu_node_id`, `origin_cmi_id`, `form_core_id`\n\n'
        || E'**Zustavajicich 14 sloupcu fw.core:**\n\n'
        || E'`id, code, label, description_user, description_system,\n'
        || E'is_active, tenant_visibility, version, created_at,\n'
        || E'created_by_id, created_by_text, updated_at, updated_by_id,\n'
        || E'updated_by_text`\n\n'
        || E'### Form/list discrimination (Decision 1B):\n\n'
        || E'Po dropu `layout_type` se discriminuje pres root comp_def:\n\n'
        || E'```sql\n'
        || E'-- Form (typ 302):\n'
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
        || E'pres `strategie_pg_insert_row` (jako v dnesnim ranim 8-step\n'
        || E'milniku — Krok 4 Vytvor comp_def s type_id=306).\n\n'
        || E'### Pravidlo do budoucna:\n\n'
        || E'NIKDY nevyplnuj `layout_type`, `layout_template`, `template_id`\n'
        || E'v INSERT/UPDATE — sloupce neexistuji. DML safeguard tě chytí, ale\n'
        || E'rychlejší je je vynechat hned.\n\n'
        || E'---\n\n'
        || E'*Doplneno 20.5.2026 po fw.core slim cleanup (9 sloupcu pryc).*'
    ,
    updated_by_text = 'Claude (id=23)',
    updated_at = NOW()
WHERE id = 1
  AND body_markdown NOT LIKE '%fw.core slim — 20.5.2026%';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run AFTER commit):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT id, title, length(body_markdown) AS body_len,
--        body_markdown LIKE '%fw.core slim — 20.5.2026%' AS marker,
--        body_markdown LIKE '%layout_type, ''list''%' AS old_layout_ref
-- FROM public.knowledge_entry WHERE id=1;
-- Expected: marker=TRUE, old_layout_ref=FALSE
