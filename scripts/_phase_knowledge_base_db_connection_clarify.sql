-- ═══════════════════════════════════════════════════════════════════════
-- knowledge_entry clarify (19.5.2026 vecer, Marti's request):
-- Marti-AI opakovane vola SELECT name FROM fw.db_connection → fail.
-- Skutecne sloupce: id, code, label, db_type, default_db, host, ...
-- (NE 'name'). Marti-AI si vymysli column name z analogie jinych tabulek.
--
-- Knowledge_entry #1 ('Jak postavit novy prehled') zminuje
-- `db_connection_id` ale nedava EXPLICIT lookup query → AI persona
-- pristup-and-improvize.
--
-- Fix: APPEND varovny block na konec body_markdown s explicit schema
-- + lookup query. Idempotent (preskoci pokud uz appended).
--
-- Run: DBeaver jako "Marti-AI" session (db_owner public neni, ale ma
--   GRANT UPDATE z _phase_knowledge_base_alter_audit_text.sql).
--   Highlight cely soubor + Alt+X.
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE public.knowledge_entry
SET
    body_markdown = body_markdown || E'\n\n---\n\n'
        || E'## ⚠ fw.db_connection — kriticka poznamka (19.5.2026)\n\n'
        || E'**Sloupec `name` NEEXISTUJE.** Pokud volas\n'
        || E'`SELECT name FROM fw.db_connection`, dostanes UndefinedColumn.\n\n'
        || E'### Skutecne sloupce fw.db_connection:\n\n'
        || E'| Sloupec | Typ | Pouziti |\n'
        || E'|---|---|---|\n'
        || E'| `id` | BIGINT PK | FK target pro `fw.data_set.db_connection_id` |\n'
        || E'| `code` | VARCHAR(50) UNIQUE | masinove jmeno (`strategie_pg`, `dbo`, `st`) |\n'
        || E'| `label` | VARCHAR(200) | **human label — TADY je „nazev"** |\n'
        || E'| `db_type` | VARCHAR(20) | `mssql` / `postgres` |\n'
        || E'| `default_db` | VARCHAR(100) | `data_db` / `DB_EC` / NULL |\n'
        || E'| `host` | VARCHAR(255) | `10.200.188.12` / `192.168.30.11` / NULL |\n'
        || E'| `port` | INT | 5432 / 1433 / NULL |\n'
        || E'| `is_active` | BOOLEAN | filter v lookup |\n'
        || E'| `sort_order` | INT | razeni v UI |\n\n'
        || E'### Standardni lookup query (pred krokem 6 / data_set INSERT):\n\n'
        || E'```sql\n'
        || E'SELECT id, code, label, db_type, default_db, host\n'
        || E'FROM fw.db_connection\n'
        || E'WHERE is_active = TRUE\n'
        || E'ORDER BY sort_order;\n'
        || E'```\n\n'
        || E'### Mapovani „semantic" → column:\n\n'
        || E'- *„jmeno konexe"*, *„nazev DB"* → `label`, NE `name`\n'
        || E'- *„technicky kod"*, *„machine code"* → `code`\n'
        || E'- *„ktera DB se ma default pouzit"* → `default_db`\n\n'
        || E'### Pro STRATEGIE PostgreSQL:\n\n'
        || E'```sql\n'
        || E'-- typicky vysledek: id=1, code=''strategie_pg'',\n'
        || E'-- label=''STRATEGIE PostgreSQL'', db_type=''postgres'',\n'
        || E'-- default_db=''data_db''\n'
        || E'-- → pouzij db_connection_id=1 v fw.data_set INSERT\n'
        || E'```\n\n'
        || E'---\n\n'
        || E'*Doplneno 19.5.2026 vecer po Marti-AI''s opakujici se chyba.\n'
        || E'Pravidlo: NIKDY si nevymyslej column name z analogie — vzdy nejdrive\n'
        || E'`strategie_pg_describe_table(''fw'', ''db_connection'')` pokud nevis.\n*'
    ,
    updated_by_text = 'Claude (id=23)',
    updated_at = NOW()
WHERE id = 1
  AND body_markdown NOT LIKE '%fw.db_connection — kriticka poznamka%';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY:
-- ════════════════════════════════════════════════════════════════════════
-- SELECT id, title, length(body_markdown) AS body_len,
--        substring(body_markdown FROM '⚠ fw\.db_connection.{0,80}') AS marker_found
-- FROM public.knowledge_entry WHERE id=1;
-- Expected: marker_found NOT NULL → append uspesny.
--
-- Re-run: idempotent (NOT LIKE check zabrani duplicate append).
