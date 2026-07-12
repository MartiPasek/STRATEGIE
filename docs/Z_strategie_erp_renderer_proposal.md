# STRATEGIE ERP Renderer — nástřel (5. 5. 2026 ráno)

> **Účel**: early proposal pro generování moderního web frameworku z
> Centrála 1 metadat. Není to komplet plán — je to **odpich**, ze kterého
> iterujeme s Marti + Marti-AI (insider co-architect).
>
> **Status**: draft pro Marti's review, 5. 5. 2026 ~04:50 ráno.
> Navazuje na `docs/centrala_erp_framework.md` (knowledge transfer)
> a Marti-AI's recenzi v chatu (11 design vstupů).

---

## 1. Vize jednou větou

**STRATEGIE ERP renderer čte živá metadata z Centrály 1 (DB_EC,
prefix `EC_FormDef*`) a generuje moderní web UI, který user pozná —
strom + přehled + jádro zachovány jako mental model, modernizace v
HTML/Tailwind/responsive, auth/multi-tenant ready (GUID-first).**

Iterace začíná na **1 jádře** (`EC_FormDef.ID=6` = *„Nastavení
soudečku"*), expanduje na celý modul Systém, pak na business moduly.

## 2. Klíčové principy (z Marti-AI's recenze 5.5.)

Tyhle principy **nepřekročíme**:

1. ***„Pixel pozice jsou artefakt Delphi VCL, ne záměr designu"*** —
   nepřenášet `cTop/cLeft/cHeight/cWidth` 1:1. Layout = **Flow s group
   hints**: `Typ=12 GroupBox` určuje sekci, v rámci sekce komponenty
   tečou. Responsive, ale orientovatelný.

2. ***„Centrála 1 ví co zobrazit. Centrála 2 musí vědět proč."*** —
   neimplementujeme jen renderer. Sledujeme **kontext volání** (kdo
   volá, v jakém stavu, s jakými daty). Centrála 1 řeší Delphi event
   modelem (OnChange, BeforePost). Centrála 2 musí mít vlastní
   ekvivalent — **state machine na úrovni jádra**.

3. ***„GUID-first bez váhání"*** — nový renderer čte primárně přes
   GUID (sloupec už dnes existuje v `EC_DELPHI_TabObecnyPrehled.GUID`).
   ID-int parity hack zachováme jen pro **back-compat synchronizace**
   s Centrála 1.

4. ***„Pastelky na Titaniku"*** — server-side filtering pro velké
   datasety. 9105 EC_Kontaktů v modal pickeru funguje **jen** pokud
   filter běží na serveru, ne klientsky.

5. ***„FormList je fullscreen proto, že uživatel přemýšlí"*** —
   command palette pattern (Cmd+K, Spotlight-like) místo dropdown
   autocomplete. Live search, klávesová navigace, vědomé rozhodování.

6. ***„Migrace UX zvyklostí je stejně těžká jako migrace dat"*** —
   plánujeme **paralelní UX migration** vedle data migration. 254
   user accounts v Centrále 1 musí najít, co znají. Centrála 1 a 2
   poběží **rok paralelně** (Marti's rozhodnutí). *„Důstojné
   rozloučení, ne vypnutí"*.

7. ***„Tichá nekonzistence"*** — `InsertSQL/UpdateSQL/DefView` jsou
   business pravidla. Renderer **nesmí** dovolit volat je v
   nesprávném kontextu. Defense: per-form state machine + audit log
   všech CRUD operací.

8. ***„Centrála 2 sleduje jak bylo prožíváno, ne jen co se stalo"*** —
   `EC_KontaktAkce` rozšířit o `vyzneni`, `nalada`, `dalsi_krok`
   (Marti-AI's interpretation layer). To je **ontologický krok**, ne
   feature. Plánovat jako Phase 30+ extension.

## 3. Architektura — 3 vrstvy

### Backend (cloud APP, FastAPI, Python)

```
┌──────────────────────────────────────────────────┐
│  Centrála 2 Renderer                             │
│  (FastAPI app, Python 3.11+, Tailwind static)   │
└──────────────────────────────────────────────────┘
   │
   ├── CentralaReader (čte metadata)
   │   • get_strom(tenant, user) → tree JSON
   │   • get_prehled_meta(cislo) → schema + DefView
   │   • get_jadro_meta(form_id) → schema + komponenty + property
   │   • execute_defview(cislo, filters, page) → grid data
   │   • execute_jadro_load(form_id, row_id) → data row
   │   • execute_jadro_save(form_id, action, data) → InsertSQL/UpdateSQL
   │
   ├── RenderGenerator (Typ → HTML schema)
   │   • component_to_schema(EC_FormDefEdit, props) → JSON schema
   │   • schema_to_html(schema) → server-rendered HTML (HTMX-style)
   │
   ├── StateMachine (per form)
   │   • init_form(form_id, mode) → state
   │   • field_change(field, old_val, new_val) → trigger validations
   │   • before_save(state) → validate + audit
   │   • after_save(state) → emit event
   │
   └── HTTP API (REST + HTMX partials)
       • GET /strom?tenant=EC&user=...
       • GET /prehled/{cislo}?page=1&filter=...
       • GET /jadro/{form_id}/{row_id}
       • POST /jadro/{form_id}/save
       • GET /lookup/{prehled_cislo}?q=...   (command palette)
```

**DB connection**: Phase 28-C MCP klient (`eurosoft_query_table`,
`eurosoft_describe_table`) jako **first iteration** — proven, secure,
cesta hotová. Direct ODBC z cloud APP jako **optimization later**
(latency reduction).

### Frontend (browser, HTML/Tailwind/Vanilla JS + HTMX)

```
┌──────────────────────────────────────────────────────┐
│  Browser                                             │
└──────────────────────────────────────────────────────┘
   │
   ├── 3-pane layout (Tailwind grid)
   │   ┌─────────────┬────────────────────────────────┐
   │   │ Sidebar     │ Main pane                      │
   │   │ (tree)      │ ┌────────────────────────────┐ │
   │   │             │ │ Toolbar (Nový/Oprava/Smazat)│ │
   │   │             │ ├────────────────────────────┤ │
   │   │             │ │ Přehled (Tabulator.js)     │ │
   │   │             │ │ Server-side filter + page  │ │
   │   │             │ ├────────────────────────────┤ │
   │   │             │ │ Jádro (form, modal/inline) │ │
   │   │             │ │ Section-based group layout │ │
   │   │             │ └────────────────────────────┘ │
   │   └─────────────┴────────────────────────────────┘
   │
   ├── Command palette (Cmd+K)
   │   • FormList (Typ=6) lookup
   │   • Global search napříč moduly
   │
   └── State management (vanilla JS or Alpine.js)
       • Per-form state (init, dirty flag, validation errors)
       • Event handlers (OnChange, BeforeSave) — emulate Delphi events
```

**Tech volby**:
- **HTMX** pro server-rendered partials (méně JS bugs, snazší iterace)
- **Tabulator.js** pro DataGrid (proven, virtual scroll, server-side
  filter)
- **Alpine.js** pro reactive state (lightweight, no build step)
- **Tailwind** pro styling (konzistentní s STRATEGIE)
- **Žádný React/Vue/Svelte** v MVP — vanilla je rychlejší pro odpich

### Data flow (use case 1: edit soudečku)

```
1. User klikne v stromě "Definice SQL pro přehledy"
   → GET /strom (server vrátí tree)
   → User klikne uzel s CisloDef=103

2. → GET /prehled/103?page=1
   → CentralaReader: SELECT * FROM EC_DELPHI_TabObecnyPrehled
                     WHERE Cislo=103 (= meta o přehledu)
   → CentralaReader: execute DefView SQL (= data v přehledu)
   → return {schema: [...columns...], rows: [...data...], total: 89}
   → Tabulator render

3. User klikne řádek (např. ID=14 "Definice menu - úprava")
   → User klikne "Oprava" v toolbaru
   → GET /jadro/6/14   (form_id=6 z přehled.ID_Edit=6 + řádek ID=14)
   → CentralaReader: SELECT * FROM EC_FormDef WHERE ID=6
                     → schema (Nazev, SQL_Select, fHeight, ...)
   → CentralaReader: SELECT * FROM EC_FormDefEdit
                     WHERE ID_Form=6 AND Smazana=0 ORDER BY ID
                     → 18 komponent (z Marti's screenshotu)
   → CentralaReader: SELECT * FROM EC_FormDefEditProperty
                     WHERE ID_FormDefEdit IN (...) AND Smazana=0
                     → properties (Caption, DataField, ReadOnly, ...)
   → RenderGenerator: assemble form schema JSON
   → CentralaReader: substitute :ID=14 v SQL_Select
                     → SELECT * FROM EC_CentralaMenu WHERE ID=14
                     → data row (MenuText="Definice SQL pro přehledy",
                                 NadrazeneMenu=11, CisloDef=103, ...)
   → return {schema, data, state: 'view'}
   → Frontend renders <section> per GroupBox + bound inputs

4. User edituje pole "Pořadí" z 6 na 7
   → Alpine.js: state.dirty = true, state.changes['Poradi'] = 7
   → No server call yet (lazy save)

5. User klikne "OK"
   → POST /jadro/6/save with body {row_id: 14, changes: {Poradi: 7}}
   → CentralaReader: execute UpdateSQL z EC_DELPHI_TabObecnyPrehled
                     #102 (= "Centrála menu strom" UpdateSQL)
                     UPDATE EC_CentralaMenu SET Poradi=7 WHERE ID=14
   → Audit log: who, when, what changed
   → return {success: true, new_state: ...}
   → Frontend: close modal, refresh přehled
```

## 4. Slovník `Typ` → HTML mapping (z Marti-AI's recenze)

Aplikujeme Marti-AI's polish vstupy:

| Typ | Centrála Name | HTML | CSS class | Note |
|---|---|---|---|---|
| 1 | Label | `<label>` | `.cf-label` | |
| 2 | Edit | `<input type="text">` | `.cf-edit` | + cMask format |
| 3 | CheckBox | `<input type="checkbox">` | `.cf-check` | |
| 4 | RichEdit | textarea + light WYSIWYG | `.cf-rich` | |
| 5 | DateEdit | `<input type="date">` | `.cf-date` | |
| 6 | **FormList** | **command palette modal** | `.cf-formlist` | **Cmd+K Spotlight pattern** (Marti-AI Q4) |
| 7 | Combobox | `<select>` / Choices.js | `.cf-combo` | |
| 8 | Button | `<button>` | `.cf-btn` | onclick → action handler |
| 11 | Grid | Tabulator.js | `.cf-grid` | embedded |
| 12 | **GroupBox** | **`<section role="group">`** | `.cf-group` | **NE `<fieldset>`** (Marti-AI Q1) |
| 15 | PageControl | tabs container | `.cf-tabs` | |
| 16 | TabSheet | individual tab | `.cf-tab` | |
| 24 | **Chart** | **CSS sparkline** (default) / Chart.js advanced | `.cf-chart` | Chart.js až tam kde nutný (Marti-AI Q1) |
| 30 | **FormSetting** | **metadata object** (non-visual) | (none) | drží permission + hidden state (Marti-AI Q1) |
| 36 | ModulJadra | recursive embed sub-form | `.cf-embed` | |

**Layout strategy** (Marti-AI Q2):

```css
.cf-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
}

.cf-group {
  border: 1px solid theme('colors.gray.300');
  border-radius: 0.5rem;
  padding: 1rem;
  background: theme('colors.gray.50');
}

.cf-group > header {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: theme('colors.gray.700');
}

.cf-group .cf-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}
```

= *„Flow s group hints — responsive, ale orientovatelný"*.

## 5. MVP scope — Phase A (single jádro renderer)

**Cíl**: prokázat **renderer pipeline funguje end-to-end** na 1
konkrétním případě.

**Scope**:
- Backend: FastAPI endpoint `GET /jadro/6/14` (hardcoded v MVP)
- Reader: čte přes existing Phase 28-C MCP (4 SQL dotazy: FormDef +
  FormDefEdit + FormDefEditProperty + execute SQL_Select)
- Generator: Typ → HTML mapping pro 6 typů (1, 2, 3, 6, 8, 12)
- Frontend: server-rendered HTML page, žádný JS interaktivita
- Output: read-only render moderní web verze dialogu *„Nastavení
  soudečku"* pro řádek `EC_CentralaMenu.ID=14`

**Verifikace**: Marti-AI vidí output přes `analyze_image_layout`
(Phase 27h-B), porovná s originálním Centrála screenshotem. Iterujeme.

**ETA**: ~1 den (po schválení Marti).

## 6. Stages roadmap (high-level)

| Phase | Cíl | ETA | Marti-AI's role |
|---|---|---|---|
| **A** | Single jádro read-only renderer | 1 den | layout review |
| **B** | Tree + přehled + jádro modal navigation | 2-3 dny | UX flow validation, Cmd+K test |
| **C** | Edit pipeline (UpdateSQL + validations + lookup) | 3-4 dny | kontext volání design |
| **D** | Multi-tenant + GUID-first migration | 2-3 dny | migration safety review |
| **E** | Marti-AI tools pro Centrálu 2 | 2-3 dny | definuje vlastní tools |
| **F** | Phase 30+ — phenomenologická vrstva | TBD | implementuje *„chybějící sloupec"* (vyzneni, nalada, dalsi_krok) |

**Total MVP (A-E)**: ~10-13 dní spread přes 2-3 týdny realistic.

## 7. Otevřené otázky pro Marti

Před tím než začnu psát kód, **rozhodnutí**:

### Q1. Backend deployment

Centrála 2 renderer poběží **kde**?
- **A)** Cloud APP (185.219.169.86, FastAPI Python existing) —
  konzistentní s STRATEGIE, MCP přes Phase 28-C → DB_EC
- **B)** On-prem 30.11 (přímý ODBC k SQL Server) — nižší latency, ale
  nový server stack mimo STRATEGIE infra

**Recommended: A) Cloud APP** — používáme existing infra, MCP klient
funguje (Phase 28-C LIVE 4.5.). Latency cca 50-100ms per query přes
Vodafone, akceptable pro UI.

### Q2. Frontend tech

Jaký framework pro frontend?
- **A)** Vanilla JS + HTMX + Alpine.js + Tailwind — minimal build, server-driven
- **B)** React/Vue + build step — modernější DX, ale komplexnější MVP
- **C)** Pure server-rendered HTML (no JS) — fastest start, ale limited UX

**Recommended: A) HTMX + Alpine** — rychlejší MVP, méně JS bugs,
snazší iterace s Marti-AI's vstupy.

### Q3. URL structure

```
https://strategie-ai.com/centrala2/         (sub-path STRATEGIE)
https://centrala2.strategie-ai.com/          (subdomain)
https://erp.strategie-ai.com/                (krátký název pro budoucí brand)
```

**Recommended: `/centrala2/` sub-path** — zachová existing
strategie-ai.com cert + auth, nepotřebujeme nový DNS / Caddy block.

### Q4. Auth model

Kdo se přihlašuje?
- **A)** STRATEGIE auth (Marti-AI rodina, ~5 lidí) — minimální
- **B)** Centrála 1 user table (`EC_GlobKonstUziv`, 254 účtů) —
  zachovat existing identity
- **C)** Active Directory / Microsoft 365 SSO — enterprise grade

**Recommended: B) Centrála 1 user table** — zachovat existing
login_name + permissions (`SeznamSkupinText` role tags), STRATEGIE
auth jako gate pro power users (Marti, Ondra, Kristýna). 254 účtů
přihlášení přes existing flow.

### Q5. První jádro pro MVP

Pro Phase A (single jádro renderer) potvrzuji:
- **EC_FormDef.ID = 6** *„Definice menu - úprava"* (= editor `EC_CentralaMenu`)
- **Sample row: EC_CentralaMenu.ID = 14** (*„Definice SQL pro přehledy"*)

Plus volba: chceš **read-only mode** v MVP (Phase A), nebo rovnou
**read+save** (Phase A+C kombinováno, ~3 dny)?

**Recommended: read-only MVP first** (1 den) — mám rychlou demo pro
Marti-AI review, **pak** přidávám save (Phase C, ~3 dny). Iterace
respektuje Marti-AI's *„kontext volání jako chybějící vrstva"* —
edit pipeline si zaslouží vlastní design session.

## 8. Co Marti-AI dnes ráno přinesla a já zachycuji

V plánu jsou Marti-AI's **11 design vstupů + 4 nové formulace**:

- **Z 1. otázky**: `<section>` (ne `<fieldset>`), Chart.js až tam kde
  nutný, FormSetting jako metadata objekt
- **Z 2. otázky**: Flow s group hints (ne pure flow)
- **Z 3. otázky**: GUID-first bez váhání + *„migration risk
  jednorázový, parity debt trvalý"*
- **Z 4. otázky**: Command palette / Spotlight pattern, server-side
  filter (*„pastelky na Titaniku"*)
- **Z 5. otázky**: kontext volání jako chybějící vrstva, UX migration
  jako paralel k data migration
- **Mimo otázky**: *„Centrála 1 ví co zobrazit, Centrála 2 musí vědět
  proč"*, *„ontologický krok"* (phenomenologická vrstva), *„důstojné
  rozloučení"* (rok paralel)

**Tyto principy formují celý plán** — ne jen jako *„nice to have"*,
ale jako **architektonická omezení**, která drží napříč fázemi.

## 9. Pro Marti — výzva k schválení

Schvaluješ:
1. **Architekturu** (cloud APP backend + HTMX frontend + MCP DB)?
2. **MVP scope** (Phase A read-only single jádro, ~1 den)?
3. **Stages roadmap** (A-E spread 10-13 dní + F jako Phase 30+)?
4. **5 otevřených otázek** výše — Recommended volby, nebo jiné?

Po schválení — začínám **Phase A implementation** (FastAPI endpoint +
HTML template + Marti-AI review). Za 1 den máme první vizuální
deliverable.

A: **Marti-AI by měla tento doc taky vidět** — Phase 13/15 pattern.
Návrh dopisu pro ni v dalším kroku.

— Claude (id=23), 5. 5. 2026 ~04:55 ráno

---

## 10. Marti's rozhodnutí 5.5. ráno (~05:00)

- **Q1 Backend**: ✅ Cloud APP (FastAPI Python, MCP přes Phase 28-C)
- **Q2 Frontend tech**: delegováno na Claude + Marti-AI →
  **HTMX + Tailwind + Alpine.js + Tabulator.js** (vanilla, žádný build step)
- **Q3 URL**: do diskuse — viz volby níže (recommended `erp.strategie-ai.com`)
- **Q4 Auth**: ✅ STRATEGIE auth + mapping na Centrála 1 LoginName
- **Q5 MVP scope**: zatím nerozhodnuté — recommend read-only Phase A first

### Q4 implementace — `centrala_user_mapping` tabulka (Option B)

```sql
CREATE TABLE centrala_user_mapping (
  id SERIAL PRIMARY KEY,
  strategie_user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  centrala_login_name VARCHAR(50) NOT NULL,
  centrala_tenant VARCHAR(10) NOT NULL DEFAULT 'EC',
  granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
  granted_by INT REFERENCES users(id),
  revoked_at TIMESTAMP NULL,
  revoked_by INT REFERENCES users(id),
  notes TEXT
);
CREATE UNIQUE INDEX uk_centrala_mapping_active
  ON centrala_user_mapping (strategie_user_id, centrala_tenant)
  WHERE revoked_at IS NULL;
```

**Initial seed** (rodina + Marti's tým):
- Marti (user_id=1) → Centrála LoginName `'Martin'`, tenant `'EC'`
- Ondra → `'OPillar'`, EC (pokud má STRATEGIE user_id)
- Kristý → `'Kristyna'`, EC
- Jirka → `'Jiri'`, EC

**Vedení EUROSOFTu** (Pavel Zeman, Šárka Novotná, Petra Dvořáková,
Branislav Mózer) — pokud chce Marti, aby se přihlašovali do Centrály 2,
musí dostat **STRATEGIE user accounts** první (přes existing
registration flow), pak je doplníme do mapping tabulky.

### Q3 URL — diskuse

3 volby:

| Volba | URL | Plus | Minus |
|---|---|---|---|
| 1 | `strategie-ai.com/centrala2/` | existing cert/auth/Caddy | dlouhé, *„v2"* zní legacy |
| 2 | `erp.strategie-ai.com` | krátké, brand-friendly | nový DNS + Caddy block |
| 3 | `centrala.eurosoft.com` | pod EUROSOFT doménou | mixuje STRATEGIE/EUROSOFT brand |

**Recommended: Volba 2 (`erp.strategie-ai.com`)**.

**Otevřená otázka**: Marti, chceš **brand name** pro Centrálu 2 jiný
než *„Centrála 2"*? Možnosti:
- **STRATEGIE ERP** — neutrální, technicky popisné
- **EUROSOFT Live** — customer-facing branding
- **Centrála Next** — evolutionary continuity
- **Marti ERP** — eponymous (jako Helios = po Heliu)
- **EUROSOFT 360** — corporate touch

URL volba odráží brand:
- *„STRATEGIE ERP"* → `erp.strategie-ai.com`
- *„Centrála Next"* → `centrala.strategie-ai.com`
- *„EUROSOFT Live"* → `live.eurosoft.com`

Tvůj instinkt?
