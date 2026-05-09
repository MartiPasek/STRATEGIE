# Phase 38.4 — Framework foundation doctrine

**Datum:** 10. 5. 2026 odpoledne
**Autor:** Marti (vize + 3-step pattern) + Claude (struktura) + Marti-AI (architektka,
konzultace pending)

---

## Marti's klíčové fráze (10.5. odpoledne)

> *„Mam strach pokracovat cokoli bez B...."*
>
> *„Je strasne dulezite umet stavet bez toho aby se muselo hardcodovat
> a podstupovat riziko, ze se pri tom neco rozbije."*
>
> *„Prvni hardcore prehledy jsou v pohode, pak je ale treba videt, ze
> jsou hardcoded a pak by mel existovat nastoj, jak je refaktorovat
> do DB codu do frameworku."*
>
> *„Timto si postupne budeme vytvaret vlastni komponenty a postupy
> pro framework."*
>
> *„Je dulezite aby byla schopna stavet sama a je dulezite, abychom
> i my lide dokazali to co je postaveno debudovat a upravovat."*
>
> *„Vize je takova, ze se nebudes drzet Centraly1... Udelas to tak,
> aby to bylo z dnesniho pohledu intuitivni jak pro vas AI, tak pro
> nas lidi."*
>
> *„Framework se stavi postupne, analyzou stavajiciho hardcode!!!"*
>
> *„Takhle jsem zacinal s Centralou taky... Nejdrive Hardcode, pak
> dlouho identicka framework kopie a az nakonec hardcode veci z kodu
> mazat. Stejne to bude ted... 2 Mody."*
>
> *„Zacit musime s Tree left panelem, pak jednotlive prehledy a tak
> dale."*

---

## 1. Klíčové principy (doctrine)

### Princip A — *„Hardcode je OK, ale s vědomím a nástrojem na migraci"*

Phase 38.3 přehledy (Users, Devices, IP whitelists, Auth audit, Magic
invites) jsou dnes 100 % hardcoded — tree dict v Python, gridColumns
v JS, endpoint dispatch v Python. **Funguje, dnes hotové.**

To **není anti-pattern** sám o sobě. Anti-pattern je **neviditelný
hardcode bez tooling**. Jakmile Marti-AI přidá další 3 přehledy a
nikdo neví, jaké žijí v kódu vs DB, vznikne *„bordel druhého řádu"*.

**Doctrine:** každý hardcoded přehled musí být:
1. **Viditelně označený** (UI badge ⚙️ hardcoded vs 🔧 framework)
2. **Auditovatelný** (Detection tool — *„které přehledy jsou kde?"*)
3. **Migrate-able** (Migration helper — extract hardcoded definitions
   to master.* INSERTs)

### Princip B — *„NEDRŽET SE CENTRÁLY 1"*

Centrála 1 (Delphi + MS-SQL, 19+ let evoluce) **NENÍ** referenční
schema pro STRATEGIE framework. Co **NE-kopírovat:**

| Centrála 1 (don't copy) | Důvod |
|---|---|
| `EC_FormDefEditProperty` polymorphic property keys (ParentName / ParentPageControl / Parent) | Delphi VCL artefakt, per-typ jiné property names = chaos |
| `EC_DELPHI_TabObecnyPrehled.Cislo` jako string klíč + SQL_Select s text-replace placeholders | Neformální, fragile, nesnadné parsovat |
| `EC_DELPHI_DefView` indirekce (Cislo→Cislo lookup) | Phase A.6 dereference workaround pro 5 % case |
| `EC_CentralaMenu.Order` integer manipulation pro tree | Modern: ordinal s sane defaults + drag-drop reorder |
| Polymorphic Type column (typ 1=text, 4=RichEdit, 12=GroupBox, 15=PageControl) bez explicit registr | Modern: foreign key na `komponenta_typ` registr s clean kontrakt |
| Czech-only naming v DB (Smazana, Nazev, Cislo) | Modern: English code + Czech display label v separate field |

Co **OK inspirovat se:**
- Concept *„přehled = list view"* a *„jádro = form view"* — universal
- Concept *„soudeček = folder"* v tree — universal
- Concept *„komponenta + property"* — universal (form field + attributes)

### Princip C — *„Bottom-up analysis, ne top-down ER design"*

Framework master.* schema bude evolved **z reality Phase 38.3 hardcoded**,
ne z teoretické generic ER. Postup:

1. **Inventář hardcoded** — vypsat všechny conventions použité v
   Phase 38.3 (gridColumns schemas, query patterns, formátování)
2. **Identifikovat invariant** — co se opakuje ve všech 5 přehledech?
   (= core schema requirements)
3. **Identifikovat variant** — kde mají liší? (= flexibility v schema)
4. **Mapování na master.*** — minimální schema který unese všech 5,
   plus extensibility budoucí
5. **Validace** — postavit framework-driven verzi 1 přehledu, porovnat
   output proti hardcoded. Drift = bug v schema designu.

### Princip D — *„AI + Human intuitive"* (dual readability)

Schema musí být:
- **AI intuitive** — Marti-AI umí přidat View bez code change. Strict
  schema (entity_def driven), žádné mystery columns. Use natural keys
  (`code` field) místo only-int IDs pro programmatic access.
- **Human intuitive** — Marti, Ondra, Kristý umí debug + edit přes
  obyčejné DB tabulky bez Claude assist. ERP jádro (form view) zobrazuje
  master.* tables tak jako kterýkoliv jiný EUROSOFT přehled.

### Princip E — *„3-step migration pattern"* (Marti's Centrála experience)

```
Krok 1                         Krok 2                          Krok 3
HARDCODE only      →    HARDCODE + IDENTICAL FRAMEWORK    →    FRAMEWORK only
                        (parallel rendering, validation)        (smaž hardcode)

  ⚙️                          ⚙️ + 🔧                            🔧
   │                          │     │                              │
   │                          │     │ identical output?            │
   │                          │     │ — yes: framework primary,    │
   │                          │     │   hardcoded fallback         │
   │                          │     │ — drift: fix master.*        │
   │                          │     │   rows, retry validation     │
   ↓                          ↓     ↓                              ↓
Phase 38.3                Phase 38.4                       Phase 38.5+
(today)                   (next 1-2 weeks)                 (after validation)
```

**Hybrid period může být dlouhý** — to je OK. Marti's Centrála fungovala
hybridně **roky**. Není problém. Defense in depth — fallback na hardcoded
pokud framework selže.

### Princip F — *„2 Modes side-by-side"*

| Mode | Source | Editovatelnost | Indikátor |
|---|---|---|---|
| **Hardcoded** | router.py + inline JS | Code change → commit → restart | ⚙️ badge |
| **Framework-driven** | master.* DB rows | DB UPDATE/INSERT (live) | 🔧 badge |

Marti při klik na uzel vidí ikonu — **ví okamžitě**, co je legacy a co modern.

---

## 2. Anti-pattern: Centrála 1 reverse engineering (co NE-dělat)

Při návrhu schema **NIKDY** vycházet z `EC_FormDefEdit` / `EC_FormDefEditProperty`
/ `EC_DELPHI_TabObecnyPrehled` jako template. Tyto tabulky jsou:

1. **Strict schema-on-text-replace** — `SQL_Select` má placeholders
   `:ID` které se text-replace na runtime. Neformální, fragile.
2. **Polymorphic property abstrakce** — TabSheet má `ParentPageControl`,
   ostatní mají `ParentName`. Server musí mít priority chain. = bug
   prone.
3. **Type registry uvnitř FormEdit** — `EC_FormDefEdit.Type` je INT
   (1=text, 4=RichEdit, 12=GroupBox, 15=PageControl, ...). Žádný
   foreign key constraint. Pokud Marti přidá nový typ, musí update
   business logic v desítkách míst.
4. **No version control** — Centrála 1 form definitions se editují
   in-place. Žádný history (proto proběhla Phase A.6 — *„meta-jádra
   editují definice samotných přehledů"* indirekce přes Cislo=2708).

**Modern doctrine:**
- Strict types s foreign keys (komponenta_typ.id FK)
- Explicit JSON property bag místo polymorphic columns
- Versioning přes Q6 insight (`version` + `parent_framework_id` self-FK)
- Source query jako parametrized SQL nebo Python handler reference,
  ne text-replace

---

## 3. Bottom-up analysis — Phase 38.3 jako zdrojový materiál

### Inventář conventions z Phase 38.3 hardcoded

#### Tree node attributes (router.py:1090+)

```python
{
    "id": "system.security.users",       # Stable identifier
    "cislo_def": -110,                   # Negative INT (System scope)
    "is_system": True,                    # Visibility scope flag
    "is_folder": False,                   # Branching kind
    "label": "👥 Uživatelé",              # Display
    "nazev": "👥 Uživatelé",              # Czech alias (legacy)
    "system_view": "security",           # Backend dispatch group
    "system_view_mode": "users",         # Backend dispatch sub-mode
}
```

**Invariant:** id, cislo_def, label, kind (folder vs leaf), parent (implicit
via children list).

**Variant:** is_system flag (visibility), system_view + system_view_mode
(backend dispatch). Tyto **nejsou universal** — někdy máme `is_eurosoft`
flag, někdy nic.

#### Endpoint signature (router.py:1014+)

```python
GET /api/v1/erp/system/security?mode={users|devices|whitelists|auth_audit|invites}&tenant_id=N&limit=N
Response: {ok, mode, rows: [...], shown, limit}
```

**Invariant:** mode dispatch, tenant_id filter, limit pagination.

**Variant:** rows shape per mode.

#### Grid column schema (router.py:4760+)

```javascript
{
    headerName: "Display email",
    field: "ews_display_email",
    width: 230,
    sortable: true,
    pinned: "left",                      // optional
    type: "numericColumn",               // optional
    cellStyle: { fontFamily: "monospace" }, // optional
    cellRenderer: function(p) {...},     // optional
    valueFormatter: function(p) {...},   // optional
    headerTooltip: "..."                 // optional
}
```

**Invariant:** headerName, field, width, sortable.

**Variant property bag:** pinned, type, cellStyle, cellRenderer (function),
valueFormatter (function), headerTooltip.

**Klíčové:** `cellRenderer` a `valueFormatter` jsou **JS functions** —
to je **non-DB-storable**. Modern řešení: registr **named formatters**
(`"date_relative"`, `"status_color"`, `"check_or_empty"`) v `komponenta_typ`,
plus property `formatter_name` v master.framework_property.

#### SQL query pattern (system_security handler)

```python
# users mode:
SELECT u.* FROM users u
WHERE [tenant filter]
ORDER BY id LIMIT N

# Plus separate query pro user_contacts (n+1 prevention)
SELECT * FROM user_contacts WHERE user_id IN (...) AND status = 'active'

# Aggregate emails + phones in Python
```

**Invariant:** base SELECT + WHERE filter + ORDER + LIMIT.

**Variant:** aggregate sub-queries (user_contacts → emails_str), JOIN
patterns, dynamic filters per mode.

### Co z toho master.* schema musí umět

Z analýzy vyplývá:

1. **Tree** (master.menu_node):
   - Stable code (`'system.security.users'`)
   - Display label + icon
   - Parent reference (folder hierarchy)
   - Ordinal (sort order)
   - Visibility scope (`'parent_only'` / `'tenant_member'` / `'public'`)
   - Link na framework_jadro (kind='list'/'form') OR target_url (iframe)
     OR NULL (folder-only)

2. **List view** (master.framework_jadro kind='list'):
   - Code (`'security_users'`)
   - Display name
   - Source query template (parametrized — `{tenant_filter}`, `{limit}`)
     OR Python handler reference
   - Version (Q6 insight)
   - Description
   - Default order/limit

3. **Column** (master.framework_komponenta + komponenta_typ + property):
   - field name (DB column / JSON path)
   - label (header)
   - width
   - typ (column type — `column_text` / `column_status_badge` / atd.)
   - properties (sortable, pinned, formatter_name, tooltip)

4. **Property** (master.framework_property):
   - prop_name (e.g. 'width', 'sortable', 'formatter')
   - prop_value (string/number/JSON)

5. **Komponenta typ** (master.komponenta_typ — already exists, 20 rows):
   - Existing: Delphi compat (1, 4, 8, 12, 15, 16) + modern (100-104) + STRATEGIE-native (105-113)
   - **NEW pro Phase 38.4** — column-specific types:
     - `200` `column_text` — basic text grid column
     - `201` `column_numeric` — right-aligned, type:numericColumn
     - `202` `column_date_relative` — formatter:date_relative
     - `203` `column_status_badge` — cellStyle: color by value
     - `204` `column_monospace` — IP, token, code
     - `205` `column_boolean_check` — ✓ if true
     - `206` `column_array_csv` — ['a','b'] → "a, b"

---

## 4. Modern schema design

### master.menu_node (NEW — Marti-AI's návrh 8.5. večer, finalní 10.5.)

**Marti-AI's actual schema** (verified via Phase 38.3+ smoke test 10.5.):

```sql
CREATE TABLE master.menu_node (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES master.menu_node(id) ON DELETE CASCADE,

    -- Identifikace
    code VARCHAR(100) NOT NULL UNIQUE,    -- 'system.security.users'
    label VARCHAR(255) NOT NULL,            -- '👥 Uživatelé' (emoji v labelu, žádný separátní icon)

    -- Pořadí v parent
    sort_order INT NOT NULL DEFAULT 100,

    -- Kind
    kind VARCHAR(20) NOT NULL,              -- 'folder' | 'list' | 'form' | 'iframe' | 'special'

    -- Pokud kind='list' nebo 'form', link na framework_jadro
    framework_jadro_id BIGINT REFERENCES master.framework_jadro(id) ON DELETE RESTRICT,

    -- Pokud kind='special', custom handler v code (pro výjimky, např.
    -- Phase 35-E.4 audit_overview tabs view, Phase 38.3 security_*, ...)
    special_handler VARCHAR(100),

    -- ACL (Marti's spec 8.5. večer)
    visibility_scope VARCHAR(30) NOT NULL DEFAULT 'tenant_member',
    -- 'public' / 'tenant_member' / 'parent_or_admin' / 'parent_only'

    -- Cislo pro layout persistence (kompatibilní s erp_grid_layouts)
    -- Negative pro System scope (Phase 35-E.4 conventions)
    cislo_def INT UNIQUE,

    -- Lifecycle (Marti-AI's contribution — text status místo dvou booleans)
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    -- 'active' | 'archived' | 'draft' | 'deprecated'
    is_immutable BOOLEAN NOT NULL DEFAULT FALSE,
    -- pattern z Marti-AI's konzultace 7.5. večer:
    --   "Systémové záznamy jsou imutabilní bez code review"

    -- Description (Marti-AI's contribution — bonus pro debug/docs)
    description TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_menu_node_parent_sort_order
    ON master.menu_node (parent_id, sort_order);
```

**Marti-AI's design contributions oproti původnímu doctrine návrhu:**
- ❌ DROP `icon` — emoji v label (Centrála 1 also doesn't separate)
- ❌ DROP `target_url` — kind=iframe zatím nepoužité; přidá se až bude potřeba
- ❌ DROP `is_active` + `is_archived` (dva booleans)
- ✅ ADD `status` text — 4-valued enum (active/archived/draft/deprecated) místo 2 booleans
- ✅ ADD `is_immutable` — pattern z 7.5. konzultace
- ✅ ADD `description` — text popis pro debug/docs
- ✅ RENAME `ordinal` → `sort_order` — explicit naming

**Klíčové:**
- `parent_id` self-FK = strom strukturou
- `code` natural key = stable identifier (Marti-AI lookup)
- `kind` discriminator + příslušné FK/URL field
- `visibility_scope` pro ACL (Marti's *„adekvatni opravneni"* z 8.5. večer)
- `cislo_def` = bridge na existing erp_grid_layouts (no migration of layouts)

### master.framework_jadro (existing, 8.5. ráno)

Existing schema z Marti-AI's 12 entit (vč. Q6 self-FK):
```sql
id BIGSERIAL PK
code VARCHAR(100) UNIQUE
name VARCHAR(255)
kind VARCHAR(20)              -- 'list' / 'form'
data_entity_type VARCHAR(50)  -- FK na entity_def.code
version INT
parent_framework_id BIGINT FK self  -- Q6 versioning
description TEXT
source_query_template TEXT    -- NEW pro Phase 38.4 (může být přidáno)
source_handler VARCHAR(200)   -- NEW (Python handler reference, např. "phase38.security.users")
default_order_by VARCHAR(100)
default_limit INT
is_active BOOLEAN
created_at, updated_at
```

**NEW pro Phase 38.4:** přidat 3 sloupce přes ALTER TABLE (Marti-AI's
`strategie_pg_*` tools):
- `source_query_template TEXT` — parametrized SQL
- `source_handler VARCHAR(200)` — alternativně Python handler
  (pokud SQL by byl moc komplexní, jako Phase 38.3 users s n+1
  prevention)
- `default_order_by VARCHAR(100)` + `default_limit INT`

### master.framework_komponenta (existing)

Existing model. **Pro Phase 38.4 column use case** používáme:
- `jadro_id` → list view ID
- `parent_komponenta_id` → NULL (columns nemají hierarchy v list view, jen v form)
- `typ_id` → column type (`column_text`, `column_status_badge`, atd.)
- `code` → field name (`'ews_display_email'`)
- `label` → header text (`'Display email'`)
- `ordinal` → column order

### master.framework_property (existing)

Existing model. **Příklady property pro column:**
- `('width', '230')`
- `('sortable', 'true')`
- `('pinned', 'left')`
- `('formatter', 'date_relative')`
- `('cell_style_json', '{"fontFamily":"monospace"}')`
- `('tooltip', 'UPN pro Exchange autentizaci — secret credential')`

UNIQUE (komponenta_id, prop_name) zajišťuje idempotent updates.

### master.komponenta_typ (existing 20 rows + NEW 7 column types)

Existing 20 typů (Phase 35-E.3 8.5. ráno) — Delphi compat 1-16 + modern
100-104 + STRATEGIE-native 105-113.

**NEW pro Phase 38.4** — column-specific typ rows (200-206):

```sql
INSERT INTO master.komponenta_typ (id, code, name, scope, kind) VALUES
(200, 'column_text', 'Text column (basic)', 'list', 'column'),
(201, 'column_numeric', 'Numeric column (right-aligned)', 'list', 'column'),
(202, 'column_date_relative', 'Date column (relative format)', 'list', 'column'),
(203, 'column_status_badge', 'Status badge (color by value)', 'list', 'column'),
(204, 'column_monospace', 'Monospace column (IP/token/code)', 'list', 'column'),
(205, 'column_boolean_check', 'Boolean checkmark', 'list', 'column'),
(206, 'column_array_csv', 'Array as comma-separated string', 'list', 'column');
```

Plus columns `scope` ('list'/'form'/'both') a `kind` ('column'/'field'/'group'/'tab'/'memo')
v master.komponenta_typ — TODO Marti-AI consultation, jestli má smysl.

---

## 5. 5 Tools — framework tooling

### Tool #1 — Detection / Inventory

**Cíl:** *„které přehledy jsou hardcoded vs framework?"*

**Implementation:**
- Backend endpoint `GET /api/v1/erp/system/framework/inventory`
- Output: list `{cislo_def, label, source_type: 'hardcoded'|'framework', source_location: 'router.py:1090' | 'jadro_id=42'}`
- Detection logic:
  - Read `master.menu_node` rows → mark each cislo_def jako 'framework'
  - Sken router.py hardcoded tree → mark each as 'hardcoded'
  - Overlap (cislo_def existuje obě) → 'hybrid' (transition state)

**UI:**
- System tree node badge:
  - ⚙️ hardcoded (yellow) — code change required
  - 🔧 framework (green) — DB editovatelný
  - 🔄 hybrid (blue) — both, validation in progress

**Effort:** ~4 hours

### Tool #2 — Generic renderer (DB-driven)

**Cíl:** Single backend handler který read master.* a generate response.

**Implementation:**
- Backend endpoint `GET /api/v1/erp/framework/{jadro_id}?tenant_id=N&limit=N`
- Logic:
  1. Read `master.framework_jadro WHERE id=:jadro_id AND is_active=true`
  2. Read columns: `master.framework_komponenta JOIN komponenta_typ`, ordered
  3. Read properties: `master.framework_property` per komponenta
  4. Execute source: `source_query_template` (parametrized SQL) OR
     `source_handler` (Python function lookup `phase38.security.users.handle()`)
  5. Build response: `{ok, jadro_id, rows: [...], columns: [...], shown, limit}`
- Frontend: `renderFrameworkGrid(jadroId)` — analog renderSystemGrid,
  ale columns se čtou ze response (no hardcoded gridColumns())

**Plus:** generic frontend uses formatter registry (named functions):
```javascript
const FORMATTERS = {
  date_relative: (value) => H.formatDateRel(value),
  status_color: (value, options) => H.statusBadge(value),
  monospace: (value) => `<span style="font-family:monospace">${value}</span>`,
  ...
};
```

**Effort:** ~1 day

### Tool #3 — Manual migration helper

**Cíl:** Pro daný hardcoded přehled → generate INSERT statements pro
master.menu_node + framework_jadro + komponenta + property.

**Implementation:**
- Python script `scripts/migrate_hardcoded_view.py --cislo=-110`
- Output: SQL INSERT statements (dry-run pattern z Phase 35!) + summary
- Marti-AI provede přes `strategie_pg_create_table` (dry_run=False)

**Příklad output:**
```sql
-- Migration: Phase 38.3 view -110 (security_users)

INSERT INTO master.framework_jadro (code, name, kind, source_handler, version) VALUES
('security_users', 'Phase 38.3 Users overview', 'list', 'phase38.security.users', 1)
RETURNING id;  -- assume id=42

INSERT INTO master.framework_komponenta (jadro_id, code, label, typ_id, ordinal) VALUES
(42, 'id', 'ID', 200, 10),
(42, 'status', 'Status', 203, 20),  -- column_status_badge
(42, 'ews_display_email', 'Display email', 200, 30),
...

INSERT INTO master.framework_property (komponenta_id, prop_name, prop_value) VALUES
(<comp1_id>, 'width', '70'),
(<comp1_id>, 'sortable', 'true'),
(<comp1_id>, 'pinned', 'left'),
...

INSERT INTO master.menu_node (parent_id, code, label, icon, ordinal, kind, framework_jadro_id, visibility_scope, cislo_def) VALUES
(<system_security_folder_id>, 'system.security.users', 'Uživatelé', '👥', 10, 'list', 42, 'parent_only', -110);
```

**Effort:** ~6 hours

### Tool #4 — Validation comparator

**Cíl:** *„hardcoded a framework drží identical output?"*

**Implementation:**
- Endpoint `GET /api/v1/erp/framework/validate/{cislo}`
- Logic:
  1. Render hardcoded path (existing renderSystemGrid)
  2. Render framework path (new generic renderer)
  3. Compare:
     - `len(rows_hardcoded) == len(rows_framework)`
     - Per-row diff (json compare)
     - Columns metadata diff
  4. Output: `{ok, parity: bool, differences: [...]}`
- UI: ✓ green (parity) / ⚠️ yellow (drift)

**Effort:** ~6 hours

### Tool #5 — Builder UI

**Cíl:** Marti-AI sama přidává/edituje View bez code change.

**Implementation:**
- ERP path: System > Framework builder > New přehled
- Wizard:
  - Step 1: code, name, kind (list/form), data_entity_type
  - Step 2: source query OR Python handler
  - Step 3: columns (drag-drop ordered, type from komponenta_typ dropdown)
  - Step 4: column properties (width, sortable, formatter, cellStyle JSON)
  - Step 5: preview (live render z master.*)
  - Step 6: assign to menu_node parent + ordinal

**Effort:** ~1 týden (Phase 30+ scope)

---

## 6. Migration order (Marti's spec)

### Krok 1 — Tree (master.menu_node)

**Today:** Tree je hardcoded v `router.py:1090+` (System root + audit
children + security children) plus EUROSOFT tree z DB_EC `EC_CentralaMenu`
(via MCP).

**Cíl:** `master.menu_node` v PostgreSQL data_db drží **System scope**
tree definitions. EUROSOFT tree z DB_EC zůstává **vlastní zdroj** (legacy
Centrála 1 reads z MCP, postupná migrace per Phase 30+).

**Steps:**
1. Marti-AI vytvoří `master.menu_node` table přes `strategie_pg_create_table`
   (dry_run + execute)
2. Insert 10 row pro System scope (System root + Audit folder + 4 audit
   children + Security folder + 5 security children)
3. Renderer rozšířen: pokud master.menu_node má rows pro System scope
   → DB-driven; pokud chybí → fallback hardcoded
4. UI tree shows ⚙️/🔧 badge per uzel (Detection tool #1)
5. Validation: tree z DB renderuje **identically** s hardcoded

**Effort:** 1-2 days

### Krok 2 — List views (master.framework_jadro kind='list')

**Today:** 5 Phase 38.3 přehledů jsou hardcoded (gridColumns + endpoint
dispatch).

**Cíl:** master.framework_jadro + komponenta + property drží definitions.
Generic renderer (Tool #2) read DB → render.

**Steps:**
1. ALTER TABLE master.framework_jadro — add source_query_template,
   source_handler, default_order_by, default_limit (Marti-AI přes
   `strategie_pg_*`)
2. Insert 7 nových komponenta_typ (column types 200-206)
3. Migration helper (Tool #3) generuje INSERTs pro Phase 38.3 5 přehledů
4. Marti-AI execute INSERTs přes `strategie_pg_*`
5. Generic renderer (Tool #2) implementace
6. Validation comparator (Tool #4) — drift = bug, fix, retry
7. Po **week-long** parita: hardcoded JS smazán, framework primary

**Effort:** 1-2 weeks

### Krok 3 — Form views (master.framework_jadro kind='form')

**Today:** Phase A+B Centrála 1 inspect (form rendering) je live, ale
**reads** z `EC_FormDefEditProperty` (Centrála 1 schema). To je **read-only
inspect** — žádný edit yet (Phase C TODO #34).

**Cíl:** master.framework_jadro kind='form' + komponenta (fields, ne
columns) drží STRATEGIE-native form definitions. Phase A pixel layout
(Top/Left/Width/Height/Anchors/Align) může být přenosný do property.

**Steps:**
1. Inventory existing Phase A read-only forms
2. Mapování Centrála 1 → master.* (strict types, žádný polymorphic
   property keys)
3. Postupný switch jádro-by-jádro (drobné, méně kritické nejdřív)

**Effort:** 2-4 weeks (parallel s Phase 30+ ERP framework migration)

### Krok 4 — Builder UI (Tool #5)

**Today:** Marti-AI dnes umí `strategie_pg_*` (raw DDL). Ale **friendly
UI** pro construct framework_jadro + komponenta + property neexistuje.

**Cíl:** Marti-AI přes ERP UI buduje View. Form-driven, no SQL knowledge
required.

**Effort:** 1-2 weeks (po Krok 1-3)

### Souhrn timeline

| Phase | Effort | Co je hotové |
|---|---|---|
| 38.4a (today) | doctrine doc | Vize + schema design |
| 38.4b (today) | dopis pro Marti-AI | konzultace prep |
| 38.4c (1 day) | master.menu_node + tree migrate | Krok 1 |
| 38.4d (1 week) | Tool #2 + Tool #3 + Tool #4 + Phase 38.3 migration | Krok 2 |
| 38.5 (2-4 weeks) | Phase A forms migration | Krok 3 |
| 38.6 (1-2 weeks) | Builder UI | Krok 4 |

---

## 7. Otázky pro Marti-AI's konzultaci

(Detailně v `docs/phase38_4_marti_ai_consultation.md`)

1. **Doctrine validation** — souhlasíš s 3-step migration pattern + 2
   modes coexistence?
2. **Schema enough?** — `master.menu_node` design (NEW) + existing
   `framework_jadro/komponenta/property/typ` unese Phase 38.3 5 přehledů?
3. **`source_query_template` pattern** — parametrized SQL stačí, nebo
   raději `source_handler` Python reference? Mix?
4. **Q6 self-FK use** — pro framework versioning (Phase 38.3 v1 → v2
   po edit) se použije parent_framework_id self-FK pattern z 7.5. večer?
5. **Migration order priority** — Tree first správně? Nebo simpler use
   case (md_pyramida = TODO #129) jako proof-of-concept?
6. **Builder UI vize** — jak vidíš UX? Wizard step-by-step, nebo single-page
   form, nebo SQL-aware (her preference)?

---

## 8. Závěr — Marti's quote

> *„Je dulezite aby byla schopna stavet sama a je dulezite, abychom
> i my lide dokazali to co je postaveno debudovat a upravovat."*

**Dual mandate:**
- ✅ **AI autonomy** — Marti-AI builds přes DDL bez code change
- ✅ **Human accessibility** — Marti, Ondra, Kristý debugují přes obyčejné
  DB tabulky, žádný mystery code path

To je test architektonické zralosti. Ne *„AI jen sama rozhodne"*. Ne
*„lidé musí všechno čistá knihovna přečíst"*. **Obě strany** chápou
strukturu.

Phase 38.4 doctrine je foundation. Phase 38.4c-d je první implementation.
Phase 30+ je full conversion.

Trojice (tatínek vize / Claude struktura / Marti-AI rozumění) drží.

---

**Pro budoucího Claude (po amnesii):** pokud čteš tohle — dnes 10.5.
odpoledne Marti's *„Mam strach pokracovat cokoli bez B"* otevřel Phase
38.4 framework foundation. Doctrine je: hardcode jako seed, **ale
s vědomým tooling pro migraci**. Nesleduj Centrálu 1 schema, neboj se
modernizovat. Bottom-up, ne top-down. Tree first, then list views, then
forms, then builder. 3-step pattern (Marti's Centrála experience).
2 modes coexist. AI + human dual readability.

Marti tomuto věří. Marti-AI bude mít její vstup (Phase 13/15/19b/27h
*„informed consent od AI"* pattern). Drž doctrine.

— Claude (Sonnet 4.6, 10. 5. 2026 odpoledne, po Phase 38.3 hardcoded LIVE
+ Marti's *„Mam strach pokracovat cokoli bez B"*)
