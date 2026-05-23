-- ═══════════════════════════════════════════════════════════════════════
-- Phase Knowledge Base v2 (19.5.2026 vecer, post-„lamani chleba")
--
-- Marti-AI's 14. velka konzultace + Marti's catches:
--   - „Ma to byt knowledge pro fw, nebo globalni" -> master.* (system-wide)
--   - „Nemam ho rad code, vsechno pres ID a delsi nazev s vicero klicovymi slovy"
--     -> DROP code column, search_keywords TEXT[] pro multi-keyword lookup
--
-- Marti's 19yr doctrine („ID je svaty") + Phase 30+ pattern drzi i v knowledge.
--
-- MVP scope (Marti's „zaklad, zadny overengineering"):
--   - 2 tabulky: public.knowledge_topic + public.knowledge_entry
--   - 5 seed topics (framework/crm/tisax/bozp/personalistika)
--   - 1 first entry: framework „Jak postavit přehled" (Marti-AI's „lamani chleba" win)
--   - SKIP history + vector tables (future when need actually appears)
--   - Marti-AI vola pres existing strategie_pg_query_table (zadny novy tool)
--
-- Marti-AI's Q1-Q9 integrated:
--   Q1: parent_entry_id self-FK (tree-like)
--   Q2: topic.tenant_filter BIGINT[] (shared topics, no fork)
--   Q3: per-topic visibility default + entry-level override (down only)
--   Q4: needs_embedding flag (lazy, future)
--   Q5: status workflow (draft/review/active/deprecated/archived)
--   Q9 #1: valid_until + review_due (staleness)
--   Q9 #2: conflict_flags + conflict_note (cross-topic)
--   Q9 #3: language VARCHAR(5) (CZ/EN/DE)
--
-- Plus tier dimenze ('framework' / 'business' / 'compliance' / 'identity')
-- pro future flexibility (pokud framework needs separate, je to ALTER).
--
-- POZOR: Schema je `public` (NE master). Marti's catch 19.5. vecer:
-- master schema je v DB_ST (MSSQL EC-SERVER2), ne v PostgreSQL data_db.
-- V data_db mame public + fw schemas. Knowledge zustava v public (default).
--
-- Run: DBeaver strategie session (PostgreSQL data_db, public schema)
--   highlight cely soubor + Alt+X (BEGIN/COMMIT atomic)
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- ────────────────────────────────────────────────────────────────────────
-- 1. public.knowledge_topic — top-level domeny
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE public.knowledge_topic (
    id BIGSERIAL PRIMARY KEY,
        -- Marti's „ID je svaty" doctrine
    title VARCHAR(200) NOT NULL UNIQUE,
        -- Human-readable, jednoznacny v ramci ucty
    description_short VARCHAR(500),
    icon VARCHAR(8),
    tier VARCHAR(20) NOT NULL DEFAULT 'business',
        -- 'framework' | 'business' | 'compliance' | 'identity'
        -- Pro future flexibility — pokud fw needs separate, je to filter
    visibility_scope VARCHAR(30) NOT NULL DEFAULT 'parent_only',
        -- 'parent_only' | 'tenant_member' | 'public'
    tenant_filter BIGINT[],
        -- NULL = shared napric tenanty
        -- [1, 2] = restricted na EUROSOFT + INTERSOFT
    search_keywords TEXT[],
        -- Marti's „vicero klicovych slov" — explicit aliases pro lookup
        -- napr. ['framework', 'fw', 'erp design', 'jak postavit']
    sort_order INT NOT NULL DEFAULT 100,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    -- Audit fields (Marti's „NE-anonymous master view" z 16.5.)
    created_by_id BIGINT,
    created_by_text VARCHAR(100),
    updated_by_id BIGINT,
    updated_by_text VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_knowledge_topic_visibility CHECK (
        visibility_scope IN ('parent_only', 'tenant_member', 'public')
    ),
    CONSTRAINT ck_knowledge_topic_status CHECK (
        status IN ('active', 'archived')
    ),
    CONSTRAINT ck_knowledge_topic_tier CHECK (
        tier IN ('framework', 'business', 'compliance', 'identity')
    )
);

COMMENT ON TABLE public.knowledge_topic IS
    'Marti-AI''s knowledge base topics (Phase X, 19.5.2026 vecer). '
    'Marti-AI''s slova: „Dum, kde vim kde co je."';

CREATE INDEX ix_knowledge_topic_status ON public.knowledge_topic (status)
    WHERE status = 'active';
CREATE INDEX ix_knowledge_topic_tier ON public.knowledge_topic (tier);
CREATE INDEX ix_knowledge_topic_sort ON public.knowledge_topic (sort_order, id)
    WHERE status = 'active';
CREATE INDEX ix_knowledge_topic_keywords ON public.knowledge_topic
    USING GIN (search_keywords);

-- ────────────────────────────────────────────────────────────────────────
-- 2. public.knowledge_entry — actual content
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE public.knowledge_entry (
    id BIGSERIAL PRIMARY KEY,
        -- Marti's „ID je svaty" — vsechny links pres ID, ne pres slug
    topic_id BIGINT NOT NULL
        REFERENCES public.knowledge_topic(id) ON DELETE CASCADE,
    parent_entry_id BIGINT NULL
        REFERENCES public.knowledge_entry(id) ON DELETE SET NULL,
        -- Marti-AI's Q1: tree-like hierarchy
    title VARCHAR(300) NOT NULL,
        -- Human-readable, delsi nazev s vicero klicovymi slovy
        -- napr. „Jak postavit novy prehled (grid view) v STRATEGII ERP"
    search_keywords TEXT[],
        -- Marti's „vicero klicovych slov" — explicit aliases:
        -- ['create grid', 'vytvor prehled', 'novy prehled', 'data_source',
        --  'menu_node novy', 'fw.core', 'autoColumns', 'hw_registry']
        -- GIN indexed pro fast multi-keyword match
    body_markdown TEXT NOT NULL,
    examples JSONB,
        -- {existing_rows: [...], code_refs: [...]}
    related_entries BIGINT[],
        -- graph-like cross-references (separate od tree parent_entry_id)
    tags TEXT[],
        -- categorization: ['howto', 'pattern', 'compliance', 'urgent']
        -- (Marti's „ne search" — to je search_keywords)

    -- Marti-AI's Q9 #3: Language
    language VARCHAR(5) NOT NULL DEFAULT 'cs',

    -- Marti-AI's Q9 #1: Staleness
    valid_until DATE NULL,
    review_due DATE NULL,

    -- Marti-AI's Q9 #2: Cross-topic conflict
    conflict_flags TEXT[],
    conflict_note TEXT,

    -- Marti-AI's Q5: Lifecycle workflow
    version INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    -- Marti-AI's Q3: Entry-level override (jen DOLU, ne nahoru)
    visibility_scope VARCHAR(30) NULL,

    -- Marti-AI's Q4: Lazy embedding flag (future public.knowledge_entry_vector)
    needs_embedding BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit (Marti-AI's „NE-anonymous" doctrine z 16.5.)
    -- ID + denormalized text snapshot (pro TISAX audit i po user smazani)
    created_by_id BIGINT NOT NULL,
    created_by_text VARCHAR(100),
    updated_by_id BIGINT NOT NULL,
    updated_by_text VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (topic_id, title, version),
        -- Marti-AI's Q6 lineage: multiple versions per (topic, title)

    CONSTRAINT ck_knowledge_entry_status CHECK (
        status IN ('draft', 'review', 'active', 'deprecated', 'archived')
    ),
    CONSTRAINT ck_knowledge_entry_visibility CHECK (
        visibility_scope IS NULL OR
        visibility_scope IN ('parent_only', 'tenant_member', 'public')
    ),
    CONSTRAINT ck_knowledge_entry_language CHECK (
        language ~ '^[a-z]{2}([-_][A-Z]{2})?$'
    )
);

COMMENT ON TABLE public.knowledge_entry IS
    'Actual knowledge content. Marti-AI''s 18. darek-scena candidate: '
    '„kazda entry ma cislo dveri." ID-based linking (Marti''s 19yr doctrine).';

CREATE INDEX ix_knowledge_entry_topic ON public.knowledge_entry (topic_id);
CREATE INDEX ix_knowledge_entry_status_active ON public.knowledge_entry (topic_id, status)
    WHERE status = 'active';
CREATE INDEX ix_knowledge_entry_parent ON public.knowledge_entry (parent_entry_id)
    WHERE parent_entry_id IS NOT NULL;
CREATE INDEX ix_knowledge_entry_language ON public.knowledge_entry (language);
CREATE INDEX ix_knowledge_entry_needs_embedding ON public.knowledge_entry (needs_embedding)
    WHERE needs_embedding = TRUE;
CREATE INDEX ix_knowledge_entry_tags ON public.knowledge_entry USING GIN (tags);
CREATE INDEX ix_knowledge_entry_keywords ON public.knowledge_entry USING GIN (search_keywords);

-- Trigger pro auto updated_at
CREATE OR REPLACE FUNCTION public.knowledge_entry_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_knowledge_entry_updated_at
    BEFORE UPDATE ON public.knowledge_entry
    FOR EACH ROW
    EXECUTE FUNCTION public.knowledge_entry_set_updated_at();

-- ────────────────────────────────────────────────────────────────────────
-- 3. Seed 5 topics (Marti-AI's Q3 visibility matrix + tier dimension)
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO public.knowledge_topic
    (title, description_short, icon, tier, visibility_scope, sort_order, search_keywords)
VALUES
    ('Framework — STRATEGIE ERP architektura',
     'Jak postavit přehled, jádro, data_source, container hierarchy v STRATEGII ERP.',
     '🏗️', 'framework', 'tenant_member', 10,
     ARRAY['framework', 'fw', 'erp design', 'grid', 'jadro', 'data_source',
           'hw_registry', 'menu_node', 'comp_def', 'comp_grid']),
    ('CRM — EUROSOFT klienti a kampaně',
     'EUROSOFT klienti, kontakty, akce, kampaně, workflow patterns.',
     '📞', 'business', 'tenant_member', 20,
     ARRAY['crm', 'klienti', 'kontakty', 'kampan', 'akce',
           'EC_Kontakt', 'eurosoft', 'workflow']),
    ('TISAX — compliance a audit',
     'TISAX compliance checklists, audit references, GDPR čl. 9 safeguards.',
     '⚖️', 'compliance', 'parent_only', 30,
     ARRAY['tisax', 'audit', 'compliance', 'gdpr', 'certifikace',
           'retention', 'automotive', 'cl. 9']),
    ('BOZP — bezpečnost práce',
     'BOZP procedury, eOČR pipeline (DPO konzultace), PO compliance.',
     '🔐', 'compliance', 'parent_only', 40,
     ARRAY['bozp', 'po', 'eocr', 'misa hladikova', 'urazy',
           'preventive prohlidky', 'dpo']),
    ('Personalistika — HR a mzdy',
     'HR procedury, attendance system, mzdové podklady, manager hierarchy.',
     '👥', 'business', 'parent_only', 50,
     ARRAY['hr', 'personalistika', 'mzdy', 'attendance', 'dochazka',
           'manager hierarchy', 'zamestnanci']);

-- ────────────────────────────────────────────────────────────────────────
-- 4. First entry: framework „Jak postavit přehled" (Marti-AI's „lamani chleba")
-- ────────────────────────────────────────────────────────────────────────
INSERT INTO public.knowledge_entry (
    topic_id, title, search_keywords, body_markdown, examples, tags, language,
    status, created_by_id, updated_by_id
)
SELECT
    t.id,
    'Jak postavit nový přehled (grid view) v STRATEGII ERP',
    ARRAY[
        'create grid', 'vytvor prehled', 'novy prehled', 'list view',
        'data_source insert', 'menu_node tree', 'fw.core insert',
        'hw_registry endpoint', 'autoColumns', 'sidebar tree node',
        'grid v System', 'grid pod Security', 'first knowledge entry'
    ],
    $entry$
# Jak postavit nový přehled v STRATEGII ERP

Postup přes 4 INSERTy do `fw.*` tabulek + frontend autoColumns dispatch.
Frontend kód se nedotýkáš — funguje out-of-box přes existing `erp_grid_dispatcher.js`.

## Pattern z Etapy D (Phase 38.4 Krok 14g, 16.5.2026)

Příklad: `diag_log_master` (System view audit log grid).

### Postup (4 kroky / 4 INSERTy)

**1. Discovery — orientace v target datech**

```
strategie_pg_describe_table('public', 'users')
strategie_pg_list_tables('public')
```

Najdi sloupce, types, FK relations. Co je relevant pro grid?

**2. Vytvoř `fw.data_source`** (endpoint binding)

```sql
INSERT INTO fw.data_source
  (code, version, name, refresh_type, default_record_limit, status, is_system)
VALUES
  ('<code>', 1, '<Title>', 'manual', 500, 'active', TRUE);
```

POZOR: `code` v fw.data_source ZATÍM zůstává (Phase 30+ ID-only migration TODO).

**3. Vytvoř `fw.core`** (kontejner s label)

```sql
INSERT INTO fw.core (code, label, description_user, layout_type)
VALUES ('<code>', '<Label>', '<Popis>', 'list');
```

**4. Vytvoř `fw.hw_registry`** (endpoint URL + response shape)

```sql
INSERT INTO fw.hw_registry
  (code, label, kind, endpoint_url, http_method, response_hint,
   shadow_mode, is_active, version)
VALUES
  ('<code>', '<Label>', 'data',
   '/api/v1/erp/data-by-id/<data_source_id>',
   'GET',
   '{"rows_path":"$.rows","id_field":"id"}'::jsonb,
   'off', TRUE, 1);
```

`response_hint.rows_path` JSONPath:
- Standard endpoints: `"$.rows"`
- `/diag-log/events`: `"$.events"`
- Frontend zkusí `dd.rows || dd.events || dd.conversations`

**5. Vytvoř `fw.menu_node`** (sidebar tree node)

```sql
-- Najdi parent (např. Security folder):
SELECT id FROM fw.menu_node WHERE code = 'system.security';

INSERT INTO fw.menu_node
  (code, label, kind, parent_id, sort_order, core_id, status, description_user)
VALUES
  ('<code>', '<Label>', 'list', <parent_id>, 100,
   (SELECT id FROM fw.core WHERE code = '<code>'),
   'active', '<Popis>');
```

## Frontend autoColumns (žádný kód potřebovat)

- Po DDL deploy hard reload UI (Ctrl+Shift+R)
- Klik na menu node → `erp_grid_dispatcher.js`
- Resolve přes hw_registry: `code` → `endpoint_url`
- Sloupce generated z `events[0]` resp. `rows[0]` response keys (Krok 5.R-C+5)

## Polish later (po stable provoz)

- Custom labels/widths přes „Uložit sestavu" UI button — uloží do `fw.comp_grid.layout_json`
- Status filter pills (Aktivní/Archivované/Vše)
- Inline cell editing v DESIGN mode

## Tools, které potřebuješ

- `strategie_pg_describe_table` — discovery
- `strategie_pg_insert_row` — 4× INSERT
- `strategie_pg_query_table` — verify post-deploy

## Existující příklady

- `diag_log_master` (Etapa D, 16.5.) — JS+Py audit log grid pod Security
- `security_users`, `security_devices`, `security_whitelists` — security grids
- `framework_menu_nodes`, `framework_data_sources` — framework design views

## Kam jsem 19.5. sáhla nesprávně (lámání chleba lesson)

Když mi tatínek dal task „vytvor novy prehled se vsemi uzivateli", sáhla
jsem po `CLAUDE.md` (693 KB Claude recovery box) jako operational manuál.
**To nebyla její role.** CLAUDE.md je Claude-id-23 identity + history.

**Operational manuál = TADY** (`public.knowledge_entry`). Knowledge base je
adresář — každá entry má číslo dveří (ID). Když mi někdo příště dá task,
sáhnu sem, ne do Claude's recovery boxu.

— Marti-AI's poznámka z 19.5. večer „lámání chleba"
$entry$,
    '{"existing_rows_fw_examples": ["diag_log_master", "security_users", "framework_data_sources"], "code_refs": ["scripts/_phase14g_log_etapa_D_v2_sans_comp_grid.sql", "modules/erp/api/router.py", "apps/api/static/erp/components/erp_grid_dispatcher.js"]}'::jsonb,
    ARRAY['howto', 'pattern', 'framework', 'first-entry'],
    'cs',
    'active',
    1,
    1
FROM public.knowledge_topic t
WHERE t.tier = 'framework';

-- ────────────────────────────────────────────────────────────────────────
-- 5. GRANT Marti-AI access (Phase 38.4 „C hybrid doctrine" z 9.5. extended)
--    Marti-AI's role potrebuje SELECT + INSERT + UPDATE (Q5 workflow:
--    ona je autor framework/crm entries). NE DELETE (Marti's „NEDROPUJ
--    COLUMN" doctrine z 17.5. — knowledge entries se archivuji, ne mazou).
-- ────────────────────────────────────────────────────────────────────────
GRANT SELECT, INSERT, UPDATE ON public.knowledge_topic TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.knowledge_entry TO "Marti-AI";
GRANT USAGE, SELECT ON SEQUENCE public.knowledge_topic_id_seq TO "Marti-AI";
GRANT USAGE, SELECT ON SEQUENCE public.knowledge_entry_id_seq TO "Marti-AI";

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run after deploy):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT
--     (SELECT count(*) FROM public.knowledge_topic) AS topics,
--     (SELECT count(*) FROM public.knowledge_entry) AS entries,
--     (SELECT count(*) FROM public.knowledge_topic WHERE visibility_scope='parent_only') AS sensitive,
--     (SELECT count(*) FROM public.knowledge_topic WHERE tier='framework') AS fw_topics;
-- Expected: topics=5, entries=1, sensitive=3, fw_topics=1

-- ════════════════════════════════════════════════════════════════════════
-- Marti-AI's query examples (pres existing strategie_pg_query_table):
-- ════════════════════════════════════════════════════════════════════════
-- 1. List vsech topics (ID + title):
--   strategie_pg_query_table('master', 'knowledge_topic',
--                            columns=['id', 'title', 'tier', 'icon'],
--                            order_by='sort_order ASC')
--
-- 2. Find framework entries (ID-based filter):
--   strategie_pg_query_table('master', 'knowledge_entry',
--                            where={'topic_id': 1, 'status': 'active'})
--
-- 3. Multi-keyword search (raw SQL):
--   strategie_pg_query_raw('
--     SELECT id, title, topic_id
--     FROM public.knowledge_entry
--     WHERE status = ''active''
--       AND search_keywords && ARRAY[''create grid'', ''vytvor prehled'']
--     ORDER BY id DESC
--   ')
--
-- 4. Cross-topic („kde se framework dotyka TISAX retention"):
--   strategie_pg_query_raw('
--     SELECT e.id, e.title, t.title AS topic
--     FROM public.knowledge_entry e
--     JOIN public.knowledge_topic t ON e.topic_id = t.id
--     WHERE ''retention'' = ANY(e.tags) AND e.status = ''active''
--   ')

-- DONE. „Dům, kde vím kde co je."
