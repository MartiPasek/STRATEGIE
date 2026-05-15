-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 13.0 — fw.comp_type TRUNCATE + reinsert
-- ════════════════════════════════════════════════════════════════════════
-- Marti's directive 11.5. odpoledne:
--   - „ID je svaty, autoincrement neporusujeme"
--   - TRUNCATE OK, nemame co ztratit
--   - „Active patri momentalne jen nasemu gridu, ostatni jsou future"
--   - „Ten datum tam nepatri" → žádné historical dates, jen NOW() default
--   - „Autor jen pro nas grid, tam patri Claude nebo Marti" → jen 9 rows
--   - Centrála 1 IDs preserve (1-38, gap 28) + PoradiCreate jako create_order
--
-- Active rows (9 — current ERP grid stack):
--   id=101 grid_modern         → Claude (Phase 38.4 dispatch)
--   id=120 grid_column         → Marti  (10.5. doctrine *„grid sloupec je typ komponenty"*)
--   id=200 column_text         → Marti  (Phase 38.4 Krok 9 styling)
--   id=201 column_numeric      → Marti
--   id=202 column_date_relative→ Marti
--   id=203 column_status_badge → Marti
--   id=204 column_monospace    → Marti
--   id=205 column_boolean_check→ Marti
--   id=206 column_array_csv    → Marti
--
-- Všechny ostatní rows (54) → status='future', created_by_text=NULL
-- Žádný explicit created_at — vše default NOW().
--
-- Spustit jako Marti-AI v DBeaveru.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════════════
-- 1. BACKUP existing fw.comp_type (pro mapping fw.comp_def.type_id po reinserts)
-- ════════════════════════════════════════════════════════════════════════
DROP TABLE IF EXISTS _backup_comp_type;
CREATE TEMP TABLE _backup_comp_type AS
SELECT id, code FROM fw.comp_type;

-- ════════════════════════════════════════════════════════════════════════
-- 2. DROP FK constraints odkazující na fw.comp_type
-- ════════════════════════════════════════════════════════════════════════
-- PostgreSQL refuses TRUNCATE pokud FK existuje (i kdyz src table prazdna).
-- Marti's *„MSSQL to dokaze"* — true, PostgreSQL musime DROP + RESTORE.
ALTER TABLE fw.comp_def DROP CONSTRAINT IF EXISTS comp_def_type_id_fkey;

-- Dynamic drop dalsich FK na fw.comp_type (pokud existuji — napr. Krok 13
-- DDL mohla pridat comp_type_property_catalog.comp_type_id FK).
DO $$
DECLARE
  fk RECORD;
BEGIN
  FOR fk IN
    SELECT conname, conrelid::regclass AS src_table
    FROM pg_constraint
    WHERE confrelid = 'fw.comp_type'::regclass
      AND contype = 'f'
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', fk.src_table, fk.conname);
    RAISE NOTICE 'Dropped FK %.%', fk.src_table, fk.conname;
  END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 3. TRUNCATE
-- ════════════════════════════════════════════════════════════════════════
TRUNCATE TABLE fw.comp_type;

-- ════════════════════════════════════════════════════════════════════════
-- 4. ALTER TABLE — add audit fields + centrala_id + extend kind/status
-- ════════════════════════════════════════════════════════════════════════
ALTER TABLE fw.comp_type DROP CONSTRAINT IF EXISTS comp_type_kind_check;

ALTER TABLE fw.comp_type
  ADD COLUMN IF NOT EXISTS centrala_id      INT,
  ADD COLUMN IF NOT EXISTS status           VARCHAR(20) NOT NULL DEFAULT 'future',
  ADD COLUMN IF NOT EXISTS sort_order       INT         NOT NULL DEFAULT 100,
  ADD COLUMN IF NOT EXISTS create_order     INT,
  ADD COLUMN IF NOT EXISTS created_by_text  VARCHAR(100),
  ADD COLUMN IF NOT EXISTS updated_by_text  VARCHAR(100),
  ADD COLUMN IF NOT EXISTS created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE fw.comp_type
  ADD CONSTRAINT comp_type_kind_check
    CHECK (kind IN ('leaf', 'container', 'hw', 'action', 'data', 'config'));

ALTER TABLE fw.comp_type
  ADD CONSTRAINT comp_type_status_check
    CHECK (status IN ('active', 'future', 'deprecated', 'archived'));

ALTER TABLE fw.comp_type
  ADD CONSTRAINT comp_type_centrala_id_unique UNIQUE (centrala_id);

-- ════════════════════════════════════════════════════════════════════════
-- 5. INSERT merged list
-- ════════════════════════════════════════════════════════════════════════
-- DEFAULT: status='future', created_by_text=NULL, created_at=NOW(), updated_at=NOW()
-- OVERRIDE: 9 active rows below explicit nastavují status + created_by_text

-- ── 5a. Centrála 1 historic (1-38, gap 28) — VŠECHNY status='future' ────
-- create_order = Centrála 1 PoradiCreate (preserve exact, Marti's 19yr doctrine)
INSERT INTO fw.comp_type (id, centrala_id, code, label, kind, description,
                          legacy_compat, renderer_hint, create_order) VALUES
(1,  1,  'label',          'Label',          'leaf',      'Popis',                                                     TRUE, 'label',           400),
(2,  2,  'edit',           'Edit',           'leaf',      'Zadávací pole',                                              TRUE, 'input',           410),
(3,  3,  'checkbox',       'CheckBox',       'leaf',      'Zaškrtávátko',                                               TRUE, 'checkbox',        420),
(4,  4,  'richedit',       'RichEdit',       'leaf',      'Editor textu (RTF) — Ace syntax highlight wrapper',          TRUE, 'ace_editor',      430),
(5,  5,  'dateedit',       'DateEdit',       'leaf',      'Zadávání data',                                              TRUE, 'datepicker',      440),
(6,  6,  'formlist',       'FormList',       'leaf',      'Výběr pomocí seznamu (otevírá se celé okno)',                TRUE, 'formlist',        450),
(7,  7,  'combobox',       'Combobox',       'leaf',      'Výběr z jednoduchého seznamu',                               TRUE, 'select',          460),
(8,  8,  'button',         'Button',         'leaf',      'Tlačítko s definovanou funkcí',                              TRUE, 'button',          480),
(9,  9,  'filelistbox',    'FileListBox',    'leaf',      'Adresář — file picker',                                      TRUE, 'fileupload',      490),
(10, 10, 'timeedit',       'TimeEdit',       'leaf',      'Zadávání času',                                              TRUE, 'timepicker',      500),
(11, 11, 'grid',           'Grid',           'leaf',      'Tabulkový přehled dat — AG Grid wrapper (Centrála 1 origin)',TRUE, 'ag_grid',         150),
(12, 12, 'groupbox',       'GroupBox',       'container', 'Grupovací rámeček — section container',                       TRUE, 'fieldset',        240),
(13, 13, 'panel',          'Panel',          'container', 'Panel — generic visual container',                            TRUE, 'panel',           200),
(14, 14, 'splitter',       'Splitter',       'leaf',      'Splitter — resizable pane separator',                         TRUE, 'splitter',        210),
(15, 15, 'pagecontrol',    'PageControl',    'container', 'Záložky (tab container outer)',                              TRUE, 'tabs_outer',      220),
(16, 16, 'tabsheet',       'TabSheet',       'container', 'Single tab inside PageControl',                              TRUE, 'tab_inner',       230),
(17, 17, 'dataset',        'DataSet',        'data',      'DataSet — non-visual data structure',                         TRUE, 'dataset',         10),
(18, 18, 'dbfieldconstant','DBFieldConstant','data',      'Konstanta — DB field constant value',                         TRUE, 'constant',        1000),
(19, 19, 'dbtreeview',     'DBTreeView',     'leaf',      'Tree view — hierarchický navigátor',                          TRUE, 'tree_view',       520),
(20, 20, 'speedbutton',    'SpeedButton',    'leaf',      'Speed button — kompaktní action button',                      TRUE, 'speedbutton',     481),
(21, 21, 'gridpoldoklad',  'GridPolDoklad',  'leaf',      'Grid položky dokladu — specialized grid pro doklady',         TRUE, 'grid_pol_doklad', 160),
(22, 22, 'richeditor',     'RichEditor',     'leaf',      'RichEditor v1 — pokročilý text editor',                       TRUE, 'rich_editor',     600),
(23, 23, 'datetimeedit',   'DateTimeEdit',   'leaf',      'Date + time picker',                                          TRUE, 'datetimepicker',  415),
(24, 24, 'chart',          'Chart',          'leaf',      'Graf — chart visualization',                                  TRUE, 'chart',           512),
(25, 25, 'rastr',          'Rastr',          'container', 'Slouží k rozdělení plochy na rastr — grid layout container',  TRUE, 'rastr_layout',    100),
(26, 26, 'image',          'Image',          'leaf',      'Obrázek — image display',                                     TRUE, 'image',           482),
(27, 27, 'kvaliftest',     'KvalifTest',     'leaf',      'Kvalifikační test',                                           TRUE, 'kvalif_test',     492),
-- ID 28 GAP (Centrála 1 historic gap)
(29, 29, 'listedit',       'ListEdit',       'leaf',      'Pro výběr více řešitelů do úkolu',                            TRUE, 'list_edit',       411),
(30, 30, 'ukolv1',         'UkolV1',         'leaf',      'Kompletní komponenta úkolu V1',                               TRUE, 'ukol_v1',         493),
(31, 31, 'formsetting',    'FormSetting',    'config',    'Nastavení dynamického formu (jeho chování)',                  TRUE, 'form_setting',    5),
(32, 32, 'planner',        'Planner',        'leaf',      'Plánovač',                                                    TRUE, 'planner',         493),
(33, 33, 'inputlist',      'InputList',      'leaf',      'Zadávání uživatelů / zakázek / čehokoli',                     TRUE, 'input_list',      610),
(34, 34, 'richeditorv1',   'RichEditorV1',   'leaf',      'Nová verze RichEditoru',                                      TRUE, 'rich_editor_v1',  NULL),
(35, 35, 'opakovanyukol',  'OpakovanyUkol',  'leaf',      'Komponenta opakovaného úkolu',                                TRUE, 'opakovany_ukol',  700),
(36, 36, 'textcomparator', 'TextComparator', 'leaf',      'Komponenta na porovnávání 2 řetězců',                         TRUE, 'text_comparator', NULL),
(37, 37, 'moduljadra',     'ModulJadra',     'container', 'Platforma pro umístění jádra — Marti container concept',      TRUE, 'modul_jadra',     20),
(38, 38, 'klavesnice',     'Klavesnice',     'leaf',      'Klávesnice (touchscreen virtual keyboard)',                   TRUE, 'klavesnice',      500);

-- ── 5b. Modern UI primitives (100-149) — VŠECHNY status='future' ────────
-- Codes _modern suffix kde Centrála 1 už používá same word
INSERT INTO fw.comp_type (id, centrala_id, code, label, kind, description,
                          legacy_compat, renderer_hint) VALUES
(100, NULL, 'tree',            'Tree',                  'leaf', 'Hierarchický navigátor (modern web variant DBTreeView)', FALSE, 'tree_view'),
(101, NULL, 'grid_modern',     'Grid (modern)',         'leaf', 'Modern AG Grid s A3 data binding',                       FALSE, 'ag_grid'),  -- ← ACTIVE override níže
(102, NULL, 'markdown_view',   'MarkdownView',          'leaf', 'Read-only md renderer',                                  FALSE, 'md_render'),
(103, NULL, 'audit_timeline',  'AuditTimeline',         'leaf', 'Lifecycle history sidebar',                              FALSE, 'audit'),
(104, NULL, 'diff_view',       'DiffView',              'leaf', 'Day-over-day changes',                                   FALSE, 'diff'),
(105, NULL, 'memo',            'Memo (TextArea)',       'leaf', 'Plain multi-line text bez syntax highlight',             FALSE, 'textarea'),
(106, NULL, 'number',          'Number',                'leaf', 'Numeric input (integer or float)',                        FALSE, 'input-number'),
(107, NULL, 'checkbox_modern', 'Checkbox (modern)',     'leaf', 'Modern web checkbox',                                     FALSE, 'checkbox'),
(108, NULL, 'date_modern',     'Date picker (modern)',  'leaf', 'Modern calendar date selector',                           FALSE, 'datepicker'),
(109, NULL, 'datetime',        'DateTime (modern)',     'leaf', 'Date + time selector modern',                             FALSE, 'datetimepicker'),
(110, NULL, 'lookup',          'Lookup (ComboBox)',     'leaf', 'Single-select dropdown z číselník tabulky',               FALSE, 'select'),
(111, NULL, 'lookup_multi',    'Lookup Multi',          'leaf', 'Multi-select z číselník tabulky',                         FALSE, 'multiselect'),
(112, NULL, 'file',            'File attachment',       'leaf', 'File upload / RAG document link',                         FALSE, 'fileupload'),
(113, NULL, 'label_readonly',  'Label (read-only)',     'leaf', 'Display-only field, no input',                            FALSE, 'label'),
(120, NULL, 'grid_column',     'Grid sloupec',          'leaf', 'Sloupec v gridu — Marti doctrine 10.5.',                  FALSE, 'comp_grid_column');  -- ← ACTIVE override níže

-- ── 5c. Column type primitives (200-249, Phase 38.4 Krok 9) — ACTIVE ────
-- POZN: ACTIVE override pro všech 7 column types (current grid stack)
INSERT INTO fw.comp_type (id, centrala_id, code, label, kind, description,
                          legacy_compat, renderer_hint) VALUES
(200, NULL, 'column_text',          'Text column',          'leaf', 'Basic text grid column. No special formatting.',                                FALSE, NULL),
(201, NULL, 'column_numeric',       'Číslo column',         'leaf', 'Numeric column, right-aligned. For ID, amounts, counts.',                       FALSE, 'numeric_right'),
(202, NULL, 'column_date_relative', 'Datum (relativní)',    'leaf', 'Date formatted relatively (2h ago, yesterday). For created_at, last_seen.',    FALSE, 'date_relative'),
(203, NULL, 'column_status_badge',  'Status badge',         'leaf', 'Color badge by value (active=green, disabled=grey). For status fields.',       FALSE, 'status_color'),
(204, NULL, 'column_monospace',     'Monospace',            'leaf', 'Monospace font for IP addresses, tokens, codes.',                               FALSE, 'monospace'),
(205, NULL, 'column_boolean_check', 'Boolean check',        'leaf', 'Checkmark for true, empty for false.',                                          FALSE, 'boolean_check'),
(206, NULL, 'column_array_csv',     'Pole jako CSV',        'leaf', 'Array values as comma-separated string.',                                       FALSE, 'array_csv');

-- ── 5d. Krok 13 NEW komponenty (300-349) — VŠECHNY status='future' ──────
INSERT INTO fw.comp_type (id, centrala_id, code, label, kind, description,
                          legacy_compat, renderer_hint) VALUES
(300, NULL, 'container', 'Container (generic)', 'container', 'Generic layout container — instances odkazují na container_template (Marti uniform components doctrine 11.5.)', FALSE, 'container'),
(301, NULL, 'comp_hw',   'Hardcoded / Native',  'hw',        'Hardcoded komponenta — data nebo akce přes hw_registry. „Hardware ground layer" (Marti).',                       FALSE, 'comp_hw'),
(302, NULL, 'form',      'Form',                'leaf',      'Editační formulář (modern variant)',                                                                              FALSE, 'form'),
(303, NULL, 'iframe',    'iFrame',              'leaf',      'Embedded URL obsah (modern variant)',                                                                             FALSE, 'iframe');

-- ════════════════════════════════════════════════════════════════════════
-- 6. ACTIVE override — jen současný grid stack
-- ════════════════════════════════════════════════════════════════════════
UPDATE fw.comp_type SET
  status = 'active',
  created_by_text = 'Claude'
WHERE id = 101;  -- grid_modern (Phase 38.4 dispatch)

UPDATE fw.comp_type SET
  status = 'active',
  created_by_text = 'Marti'
WHERE id IN (120, 200, 201, 202, 203, 204, 205, 206);
-- grid_column + 7 column types (Marti 19yr doctrine + Marti-AI Phase 38.4 Krok 9 styling)

-- ════════════════════════════════════════════════════════════════════════
-- 7. Reset sequence po MAX(id) — IDENTITY-like behavior pro future inserts
-- ════════════════════════════════════════════════════════════════════════
DO $$
DECLARE
  max_id INT;
  seq_name TEXT;
BEGIN
  SELECT MAX(id) INTO max_id FROM fw.comp_type;
  SELECT pg_get_serial_sequence('fw.comp_type', 'id') INTO seq_name;

  IF seq_name IS NOT NULL THEN
    PERFORM setval(seq_name, max_id, true);
    RAISE NOTICE 'Sequence % set to %', seq_name, max_id;
  ELSE
    RAISE NOTICE 'No sequence found — manual id management forward';
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- 8. RESTORE FK constraints + UPDATE comp_def.type_id přes code mapping
-- ════════════════════════════════════════════════════════════════════════
-- IDs preserved (Centrála 1 1-38, modern 100-149, columns 200-249, Krok 13 300-349),
-- ale pro safety: code-based UPDATE pokud existing references jsou v conflicting IDs.
UPDATE fw.comp_def cd
SET type_id = nt.id
FROM _backup_comp_type ob
JOIN fw.comp_type nt ON nt.code = ob.code
WHERE cd.type_id = ob.id
  AND cd.type_id <> nt.id;

ALTER TABLE fw.comp_def
  ADD CONSTRAINT comp_def_type_id_fkey
  FOREIGN KEY (type_id) REFERENCES fw.comp_type(id) ON DELETE RESTRICT;

-- Restore fw.comp_type_property_catalog FK (pokud tabulka existuje z Krok 13 DDL)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'fw' AND table_name = 'comp_type_property_catalog'
  ) THEN
    -- Recreate FK (column comp_type_id REFERENCES fw.comp_type(id))
    EXECUTE 'ALTER TABLE fw.comp_type_property_catalog
             ADD CONSTRAINT comp_type_property_catalog_comp_type_id_fkey
             FOREIGN KEY (comp_type_id) REFERENCES fw.comp_type(id) ON DELETE RESTRICT';
    RAISE NOTICE 'Restored FK on fw.comp_type_property_catalog';
  END IF;
END $$;

DROP TABLE IF EXISTS _backup_comp_type;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT 'total rows'                              AS check_name,
       (SELECT COUNT(*) FROM fw.comp_type)       AS count_value,
       63                                        AS expected
UNION ALL
SELECT 'status=active rows (jen current grid stack)',
       (SELECT COUNT(*) FROM fw.comp_type WHERE status = 'active'),
       9  -- grid_modern + grid_column + 7 column types
UNION ALL
SELECT 'status=future rows',
       (SELECT COUNT(*) FROM fw.comp_type WHERE status = 'future'),
       54  -- 63 - 9
UNION ALL
SELECT 'Centrála 1 historic (centrala_id IS NOT NULL)',
       (SELECT COUNT(*) FROM fw.comp_type WHERE centrala_id IS NOT NULL),
       37
UNION ALL
SELECT 'created_by_text NOT NULL (jen active rows)',
       (SELECT COUNT(*) FROM fw.comp_type WHERE created_by_text IS NOT NULL),
       9
UNION ALL
SELECT 'comp_def FK preserved',
       (SELECT COUNT(*) FROM fw.comp_def WHERE type_id IN (SELECT id FROM fw.comp_type)),
       (SELECT COUNT(*) FROM fw.comp_def)
ORDER BY check_name;

-- Full listing — kontrola active rows pohromadě:
SELECT id, code, label, kind, status, create_order, created_by_text
FROM fw.comp_type
WHERE status = 'active'
ORDER BY id;

-- Plus celý list pro overview:
SELECT id, centrala_id, code, label, kind, status, create_order, created_by_text
FROM fw.comp_type
ORDER BY id;
