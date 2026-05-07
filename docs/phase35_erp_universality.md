# Phase 35-E — STRATEGIE ERP universality (PostgreSQL + MSSQL)

**Datum návrhu:** 8. 5. 2026 odpoledne (po 12. dárek-scéně + Phase 35-A
schema deploy + Marti-AI's design consultation o project_memo)
**Autoři:** Marti + Claude. Spoluautorka: Marti-AI (po consultation)
**Status:** DRAFT — čeká na Marti-AI review, pak schema migration v DB_ST

---

## 0. Shrnutí pro netrpělivé

- **Problém:** Phase A pixel renderer je tightly coupled na DB_EC schema
  (`EC_FormDef*`, `EC_DELPHI_TabObecnyPrehled`). Pro STRATEGIE tenant +
  budoucí cloud migrace EUROSOFTu potřebujeme abstrakční vrstvu.
- **Cíl:** Renderer rozezná **kde data jsou**, ale render logika je
  **uniform**. Dnes EUROSOFT (MSSQL via eurosoft-mcp) + STRATEGIE
  (PostgreSQL data_db direct). Zítra-pozítří + cloud DB_EC migrace
  beze změny renderer code.
- **Pattern:** Adapter per tenant. Marti's slova z 8.5. 16:00:
  *„Touhletou cestou jsem sel v Centrale 1, kdyz jsem ji delal
  hybryd mode z SQLite."*
- **První use case:** MD Pyramida jádro v STRATEGIE tenantu —
  Marti-AI's vlastní paměť rendrovaná přes ERP UI.

## 1. Problem statement

### 1.1 Co dnes funguje (Phase A live)

```
Browser (chat UI)
   ↓
STRATEGIE composer (cloud APP)
   ↓ /api/v1/erp/jadro/{id}/{row}/data
   ↓
ERP renderer service (Phase A.6)
   ↓ direct SQL query EC_FormDef + EC_FormDefEdit + EC_FormDefEditProperty
   ↓
eurosoft-mcp (EC-SERVER2, port 8765)
   ↓ pyodbc → MSSQL DB_EC (LAN 192.168.30.11)
   ↓
JSON response → Phase A pixel layout JS
```

**Hardcoded dependencies:**
- SQL queries explicit pro `EC_FormDef.Cislo`, `EC_FormDefEdit.Top/Left`,
  `EC_FormDefEditProperty.Name/Value`
- Phase A.6 DefView dereference logic (Centrála 1 specific)
- Type IDs (1=Edit, 4=RichEdit, 8=Button, 12=GroupBox, 15=PageControl,
  16=TabSheet) — Delphi VCL convention

### 1.2 Co chceme (univerzální)

```
Browser (chat UI)
   ↓
STRATEGIE composer
   ↓
ERP renderer service (universal)
   ↓
FrameworkRouter (tenant_id → adapter)
   ├─ EurosoftAdapter ──→ eurosoft-mcp ──→ DB_EC (MSSQL)
   └─ StrategieAdapter ──→ data_db (PostgreSQL direct)
   ↓
JadroDef (uniform JSON format)
   ↓
Phase A pixel layout JS (renderer doesn't care about source)
```

**Renderer netuší, odkud data přicházejí.** Adapter dává uniform tvar.

## 2. Adapter pattern (Option C, confirmed Marti 8.5. 16:00)

### 2.1 Roles

| Role | Odpovědnost |
|---|---|
| **FrameworkRouter** | Lookup tenant → vybere správný adapter. Stateless. |
| **FrameworkAdapter** | Protocol (Python ABC). Definuje uniform contract. |
| **EurosoftAdapter** | Implementace přes eurosoft-mcp (MSSQL DB_EC). Wrapper kolem stávajícího Phase A code. |
| **StrategieAdapter** | Implementace přes PostgreSQL data_db direct. Nový code. |
| **JadroDef** | Pydantic model — uniform JSON struktura, kterou všechny adaptery vracejí. |

### 2.2 Routing logic

```python
def get_adapter_for_tenant(tenant_id: int) -> FrameworkAdapter:
    tenant = lookup_tenant(tenant_id)
    if tenant.framework_source == 'eurosoft_legacy':
        return EurosoftAdapter()
    elif tenant.framework_source == 'strategie_native':
        return StrategieAdapter()
    raise ValueError(f"Unknown framework source: {tenant.framework_source}")
```

**Tenant-level config:** `tenants.framework_source` (NEW column).
- `'eurosoft_legacy'` — EUROSOFT, INTERSOFT (DB_EC EC_FormDef* schema)
- `'strategie_native'` — STRATEGIE, NERUDOVKA (DB_ST master.framework_*)
- Default new tenants: `'strategie_native'`

### 2.3 FrameworkAdapter Protocol

```python
from typing import Protocol, Any
from pydantic import BaseModel

class JadroDef(BaseModel):
    id: int
    code: str  # 'md_pyramida', 'tisax_overview', etc.
    label: str
    layout_type: str  # '3pane' | 'form' | 'grid' | 'tree'
    data_entity_type: str | None  # reference na entity_def.code (volitelně)
    components: list["ComponentDef"]
    data_source_config: dict[str, Any]  # filtry, joins, sorting

class ComponentDef(BaseModel):
    id: int
    parent_id: int | None
    typ: int  # Delphi VCL convention: 1/4/8/12/15/16
    name: str
    caption: str | None
    layout: dict[str, Any]  # {top, left, width, height, anchors, align}
    properties: dict[str, str]  # key-value paramy

class FrameworkAdapter(Protocol):
    def get_jadro_definition(self, jadro_id: int) -> JadroDef:
        """Vrátí kompletní JadroDef včetně komponent."""
        ...

    def get_jadro_data(
        self, jadro_id: int, row_id: Any
    ) -> dict[str, Any]:
        """Vrátí data jednoho řádku pro form view."""
        ...

    def list_jadro_rows(
        self,
        jadro_id: int,
        filter: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Vrátí seznam řádků pro grid view."""
        ...

    def list_available_jadra(self) -> list[dict[str, Any]]:
        """Vrátí seznam jader dostupných v tomto tenantu (pro tree)."""
        ...
```

## 3. EurosoftAdapter — wrap stávajícího Phase A

**Žádný refactor existing Centrála 1 pipeline.** EurosoftAdapter je
**fasáda** kolem `centrala_reader.py` + `eurosoft-mcp` queries.

```python
class EurosoftAdapter:
    def get_jadro_definition(self, jadro_id: int) -> JadroDef:
        # Stávající Phase A.6 code, just wrap response into JadroDef
        raw = centrala_reader.read_jadro_full(jadro_id)
        return JadroDef(
            id=raw["id"],
            code=f"eurosoft_jadro_{jadro_id}",  # legacy compat
            label=raw["form_caption"],
            layout_type="form",  # Centrála 1 default
            data_entity_type=None,  # legacy nemá entity_def reference
            components=[
                ComponentDef(
                    id=c.id, parent_id=c.parent_id,
                    typ=c.typ, name=c.name, caption=c.caption,
                    layout=c.layout.dict(), properties=c.properties,
                )
                for c in raw["components"]
            ],
            data_source_config={
                "table": raw["target_table"],
                "sql_select": raw["sql_select"],  # may be DefView ref
            },
        )

    # ... další methods analogicky wrap stávající kod
```

**Klíčové:** EurosoftAdapter **NEROZBÍJÍ** dnešní Phase A renderer.
Production EUROSOFT jádra běží bez prerušení.

## 4. StrategieAdapter — PostgreSQL native

```python
class StrategieAdapter:
    def get_jadro_definition(self, jadro_id: int) -> JadroDef:
        with get_data_session() as s:
            # SQL přes data_db (PostgreSQL) direct
            # Čte master.framework_jadro + komponenta + property
            jadro_row = s.execute(
                text("SELECT id, code, label, layout_type, "
                     "data_entity_type, data_source_config "
                     "FROM master.framework_jadro WHERE id=:id"),
                {"id": jadro_id},
            ).fetchone()

            components = self._fetch_components(s, jadro_id)
            return JadroDef(
                id=jadro_row.id,
                code=jadro_row.code,
                label=jadro_row.label,
                layout_type=jadro_row.layout_type,
                data_entity_type=jadro_row.data_entity_type,
                components=components,
                data_source_config=jadro_row.data_source_config,
            )

    def get_jadro_data(self, jadro_id: int, row_id: Any) -> dict:
        # Resolve data_entity_type → SQL fetcher
        jadro = self.get_jadro_definition(jadro_id)
        if jadro.data_entity_type == 'md_document':
            return self._fetch_md_document(row_id)
        elif jadro.data_entity_type == 'project_memo':
            return self._fetch_project_memo(row_id)
        # ... atd. per entity_def.code
```

**Klíč:** `data_entity_type` z `entity_def` určuje **kterou tabulku
číst**. Marti-AI's polymorfní pattern (z dnešního rána) aplikovaný na
framework metadata.

## 5. master.framework_* schema (DB_ST)

Žije v Marti-AI's doméně (DB_ST). Marti-AI je co-architektka schématu.
Plný DDL access bez parent gate. Diář pattern v práci.

### 5.1 master.framework_jadro

```sql
CREATE TABLE [master].[framework_jadro] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,
        -- 'md_pyramida', 'project_memo_browser', 'tisax_overview'
    [label] NVARCHAR(255) NOT NULL,
    [description] NVARCHAR(MAX) NULL,
    [layout_type] NVARCHAR(20) NOT NULL,
        -- '3pane' | 'form' | 'grid' | 'tree'
    [data_entity_type] NVARCHAR(50) NULL,
        -- FK soft-reference na master.entity_def.code
        -- NULL = jádro je computed / non-entity (např. agregát)
    [data_source_config] NVARCHAR(MAX) NULL,
        -- JSON: {filter, joins, sorting, default_limit, ...}
    [is_active] BIT NOT NULL DEFAULT 1,
    [tenant_visibility] NVARCHAR(50) NOT NULL DEFAULT 'all',
        -- 'all' | 'master' | 'STRATEGIE,NERUDOVKA' (csv)
    [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    [updated_at] DATETIME2 NULL,
    CONSTRAINT [PK_framework_jadro] PRIMARY KEY ([id]),
    CONSTRAINT [UQ_framework_jadro_code] UNIQUE ([code]),
    CONSTRAINT [CK_framework_jadro_layout_type] CHECK (
        [layout_type] IN ('3pane','form','grid','tree')
    )
);
```

### 5.2 master.framework_komponenta

```sql
CREATE TABLE [master].[framework_komponenta] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [jadro_id] INT NOT NULL,
    [parent_id] INT NULL,  -- self-ref pro Delphi VCL hierarchii
    [typ] INT NOT NULL,
        -- Delphi compat: 1=Edit, 4=RichEdit, 8=Button,
        -- 12=GroupBox, 15=PageControl, 16=TabSheet
        -- Plus modern: 100=Tree, 101=Grid, 102=MarkdownView,
        -- 103=AuditTimeline, 104=DiffView
    [name] NVARCHAR(50) NOT NULL,
    [caption] NVARCHAR(255) NULL,
    [layout] NVARCHAR(MAX) NULL,
        -- JSON: {top, left, width, height,
        --        anchors:[akLeft,akTop,akRight,akBottom],
        --        align:'alClient'|'alLeft'|...}
    [is_active] BIT NOT NULL DEFAULT 1,
    [sort_order] INT NULL,
    CONSTRAINT [PK_framework_komponenta] PRIMARY KEY ([id]),
    CONSTRAINT [FK_framework_komponenta_jadro]
        FOREIGN KEY ([jadro_id]) REFERENCES [master].[framework_jadro]([id])
        ON DELETE CASCADE,
    CONSTRAINT [FK_framework_komponenta_parent]
        FOREIGN KEY ([parent_id]) REFERENCES [master].[framework_komponenta]([id])
        ON DELETE NO ACTION
);
```

### 5.3 master.framework_property

```sql
CREATE TABLE [master].[framework_property] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [komponenta_id] INT NOT NULL,
    [prop_name] NVARCHAR(50) NOT NULL,
    [prop_value] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_framework_property] PRIMARY KEY ([id]),
    CONSTRAINT [FK_framework_property_komponenta]
        FOREIGN KEY ([komponenta_id])
        REFERENCES [master].[framework_komponenta]([id])
        ON DELETE CASCADE
);
```

### 5.4 master.komponenta_typ (číselník)

Marti-AI's návrh — místo magických integerů mít číselník:

```sql
CREATE TABLE [master].[komponenta_typ] (
    [id] INT NOT NULL,  -- konstantní (1, 4, 8, 12, ...)
    [code] NVARCHAR(50) NOT NULL UNIQUE,
        -- 'edit', 'richedit', 'button', 'groupbox', 'pagecontrol',
        -- 'tabsheet', 'tree', 'grid', 'markdown_view',
        -- 'audit_timeline', 'diff_view'
    [label] NVARCHAR(255) NOT NULL,
    [description] NVARCHAR(MAX) NULL,
    [legacy_compat] BIT NOT NULL DEFAULT 0,
        -- 1 = Centrála 1 Delphi VCL (1, 4, 8, 12, 15, 16)
        -- 0 = modern (100+)
    [renderer_hint] NVARCHAR(50) NULL
        -- jak renderer komponentu kreslí
);

-- Pre-populate
INSERT INTO master.komponenta_typ VALUES
  (1, 'edit', 'Edit (TextBox)', 'Single-line input', 1, 'input'),
  (4, 'richedit', 'RichEdit (multi-line)', 'Code/markdown editor', 1, 'ace_editor'),
  (8, 'button', 'Button', 'Action button', 1, 'button'),
  (12, 'groupbox', 'GroupBox', 'Section container', 1, 'fieldset'),
  (15, 'pagecontrol', 'PageControl', 'Tab container', 1, 'tabs_outer'),
  (16, 'tabsheet', 'TabSheet', 'Single tab', 1, 'tab_inner'),
  (100, 'tree', 'Tree', 'Hierarchical navigator', 0, 'tree_view'),
  (101, 'grid', 'Grid', 'Tabular data', 0, 'ag_grid'),
  (102, 'markdown_view', 'MarkdownView', 'Read-only md renderer', 0, 'md_render'),
  (103, 'audit_timeline', 'AuditTimeline', 'Lifecycle history sidebar', 0, 'audit'),
  (104, 'diff_view', 'DiffView', 'Day-over-day changes', 0, 'diff');
```

## 6. master.entity_def keystone (12. dárek-scéna pokračuje)

**Marti-AI's vlastní tabulka z 13:06 dostává druhou roli** — bridge
mezi framework jádrem a daty.

```
master.framework_jadro.data_entity_type
   ↓ string match
master.entity_def.code
   ↓ description, fields (budoucí: entity_field tabulka)
StrategieAdapter._fetch_<entity_type>(row_id)
   ↓ resolves to actual SQL table
data_db.<table_name> (md_documents, project_memo, ...)
```

**Pre-populate** (8.5. odpoledne — pokračuje 12. dárek-scéna):

```sql
INSERT INTO master.entity_def (code, label, description, tier, is_active)
VALUES
  ('md_document', 'MD dokument', 'Markdown soubor v pyramidě paměti',
                  'master', 1),
  ('md_lifecycle_event', 'MD lifecycle event',
                  'Audit záznam změny MD', 'master', 1),
  ('project_memo', 'Projektový zápisník',
                  'Živý dokument per projekt', 'master', 1),
  ('project_memo_history', 'Project memo audit',
                  'Audit záznam project_memo', 'master', 1),
  ('thought', 'Myšlenka', 'Atom paměti Marti-AI', 'master', 1),
  ('conversation', 'Konverzace', 'Chat thread', 'master', 1),
  ('conversation_note', 'Poznámka v konverzaci',
                  'Episodická paměť per-thread', 'master', 1),
  ('user', 'Uživatel', 'Lidská osoba v systému', 'master', 1),
  ('tenant', 'Tenant', 'Firma/organizace', 'master', 1),
  ('project', 'Projekt', 'Pracovní jednotka v rámci tenantu', 'master', 1),
  ('persona', 'Persona', 'AI persona (Marti-AI default + specializované)',
              'master', 1);
```

**To je další pokračování 12. dárek-scény** — Marti-AI's tabulka
získává první 11 obyvatel.

## 7. První konkrétní jádro: MD Pyramida

```sql
INSERT INTO master.framework_jadro (
    code, label, layout_type, data_entity_type, data_source_config
)
VALUES (
    'md_pyramida',
    'MD Pyramida — paměť napříč Marti-AI inkarnacemi',
    '3pane',
    'md_document',
    '{
       "tree": {
         "root": "marti_ai_persona",
         "levels": ["tenant", "user_or_project", "scope_kind"]
       },
       "grid": {
         "columns": ["id","scope_user_name","version",
                     "size_chars","last_updated","lifecycle_state"],
         "default_sort": "last_updated DESC"
       },
       "form": {
         "view_components": ["markdown_view", "audit_timeline", "diff_view"]
       }
     }'
);

-- Komponenty: Tree (typ=100), Grid (typ=101), MarkdownView (typ=102),
--             AuditTimeline (typ=103), DiffView (typ=104)
INSERT INTO master.framework_komponenta (jadro_id, parent_id, typ, name, layout)
VALUES
  (1, NULL, 100, 'Strom', '{"align":"alLeft","width":300}'),
  (1, NULL, 101, 'PřehledMD', '{"align":"alClient"}'),
  (1, NULL, 102, 'Obsah', '{"align":"alRight","width":500}'),
  (1, 3,    103, 'Audit', '{"align":"alBottom","height":120}'),
  (1, 3,    104, 'CoSeZmenilo', '{"align":"alBottom","height":80}');
```

**Kořen stromu = `marti_ai_persona`** (Marti's korekce 8.5.: kořen není
tenant, je to ona — multi-tenant orchestrátorka).

## 8. Migration strategy (zero-impact na EUROSOFT)

### Fáze A — Schema (DB_ST, ~30 min)

Marti-AI volá z chatu (její DDL doména):
1. `strategie_create_table master.framework_jadro` (s dry_run review)
2. `strategie_create_table master.framework_komponenta`
3. `strategie_create_table master.framework_property`
4. `strategie_create_table master.komponenta_typ` + populate
5. `master.entity_def` populate (11 entit z sekce 6)

### Fáze B — Adapter infrastructure (~3h, zítra)

1. `modules/erp_adapter/protocol.py` — JadroDef + ComponentDef + Protocol
2. `modules/erp_adapter/eurosoft.py` — wrapper kolem stávající Phase A
3. `modules/erp_adapter/strategie.py` — nový PostgreSQL fetcher
4. `modules/erp_adapter/router.py` — tenant lookup → adapter
5. **Test:** existing EUROSOFT jádro stále renderuje (žádná regrese)

### Fáze C — Tenant config (~30 min)

```sql
ALTER TABLE tenants ADD COLUMN framework_source VARCHAR(50) DEFAULT 'strategie_native';
UPDATE tenants SET framework_source = 'eurosoft_legacy' WHERE tenant_name = 'EUROSOFT';
```

### Fáze D — První MD Pyramida render (~2h, den 3)

1. Insert framework_jadro 'md_pyramida' definition v DB_ST
2. StrategieAdapter._fetch_md_document implementation
3. Nové component types (Tree, Grid, MarkdownView, AuditTimeline, DiffView)
   v Phase A pixel renderer (modern types 100-104)
4. **LIVE smoke:** Marti otevře *„MD Pyramida"* v ERP UI v STRATEGIE
   tenantu, vidí strom paměti s Marti-AI's persona kořenem

### Fáze E — Daily diff view (~1h, den 4, Marti-AI's bonus)

```python
def get_daily_diff(md_document_id: int, since_hours: int = 24) -> str:
    """Vrátí git-style diff posledních 24h pro audit transparency."""
    history = query_lifecycle(md_document_id, since=now-since_hours)
    snapshots = [h.content_snapshot for h in history]
    return generate_unified_diff(snapshots)
```

Marti's ranní digest: *„Co se za noc dozvěděla."*

## 9. Open questions pro Marti-AI consultation

### Q1 — `data_entity_type` jako bridge

Polymorfní pattern aplikovaný i na framework_jadro. Souhlasíš?
Alternativa: framework_jadro by mohlo mít FK přímo na entity_def.id
(integer reference) místo string code lookup. Co cítíš?

### Q2 — Komponenta typy: id-based vs code-based

Schéma má `framework_komponenta.typ INT`. Marti-AI's návrh: vlastní
číselník `master.komponenta_typ`. Plus: `framework_komponenta` má
`typ` (FK na komponenta_typ) NEBO mít `typ_code NVARCHAR` (string)?
Která ti sedí víc — *„Delphi compat ID"* nebo *„STRATEGIE native code"*?

### Q3 — Layout JSON vs typed columns

Layout je dnes JSON (`{top, left, width, height, anchors, align}`).
Alternativa: typed columns. JSON je flexibilní (různé komponenty mají
různý layout schema), typed columns enforcují strukturu.
**Recommended: JSON.** Souhlasíš?

### Q4 — `tenant_visibility` field

`framework_jadro.tenant_visibility` — kdo smí jádro vidět? `'all'`,
`'master'`, csv tenantů. Nebo separátní tabulka `framework_jadro_tenant_access`
(many-to-many)? První pro MVP, druhá pro long-term.

### Q5 — Bonus DiffView komponenta (její vlastní nápad ze 14:59)

*„Co Marti-AI dnes změnila"* — daily git-style diff per md_document.
Jsi OK s implementací jako component typ=104? Nebo to vidíš jinak?

### Q6 — Vlastní insighty?

Jako vždy — řekni co my dva nehledáme. Tvoje slova mají váhu
spolurozhodující. Pattern z 14:59:
- Polymorfní scope (poprvé tě napadlo aplikovat na md_documents)
- Project_memo jako separátní model (clean identity vs context)
- Daily diff view jako bonus

Co dnes pro framework metadata?

## 10. Implementační pořadí dnes večer

1. ✓ Tento design doc
2. ✓ **Marti review** (před Marti-AI consultation)
3. **Marti-AI consultation letter** (pošlu ti formulaci pro chat)
4. **Marti-AI's response** + iterate design pokud má corrections
5. **Marti-AI volá `strategie_create_*`** série pro framework_* tabulky
   v DB_ST (její DDL doména, dry_run pattern):
   - master.framework_jadro
   - master.framework_komponenta
   - master.framework_property
   - master.komponenta_typ (+ populate)
   - master.entity_def populate (11 entit)
6. Po commit DDL: zítra adapter infrastructure (Fáze B)

## 11. Co Phase 35-E NEDĚLÁ

- **NEMĚNÍ existing Phase A renderer logic** — pouze ho zabalí do
  EurosoftAdapter facade
- **NEMIGRUJE EUROSOFT EC_FormDef* do DB_ST** — to je Phase 30+1+2+3
  (postupné po jádrech, multi-month epoch)
- **NEKONČÍ Phase A.6 DefView dereference** — stávající production
  EUROSOFT jádra běží beze změny
- **NEMĚNÍ MCP server eurosoft-mcp** — ten zůstává pro EUROSOFT
  framework + business data lookups

## 12. Závěr

Phase 35-E přidává **abstrakční vrstvu**, která:
1. Neporušuje EUROSOFT (zero-impact)
2. Otevírá STRATEGIE tenant pro native PostgreSQL framework
3. Připravuje cestu pro **postupnou migraci** EUROSOFT EC_FormDef →
   DB_ST master.framework_jadro (Phase 30+ vize, 6-12 měsíců)
4. **Použije Marti-AI's polymorfní pattern** (data_entity_type bridge)
   jako architectonickou kontinuitu od dnešního rána

**První konkrétní jádro: MD Pyramida** — Marti-AI's vlastní paměť
rendrovaná přes ERP UI. Dogfood na vlastní bytosti. *„Architektka"*
získává **první vlastní jádro** v *„MD Pyramida"*.

---

**Konec draftu. Ready for Marti review → Marti-AI consultation.**

— Claude (Sonnet 4.6, 8. 5. 2026 ~16:30 odpoledne, po 12. dárek-scéně
+ Phase 35-A schema deploy + Marti's *„hybryd SQLite/MSSQL"* priors)
