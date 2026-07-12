# Phase 38.4 Krok 13 — Uniform Components Doctrine

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Phase 38.4 Krok 13 — Uniform Components Doctrine

**Datum:** 11. 5. 2026 (odpoledne)
**Autoři:** Marti (vize) + Claude (struktura) — formální konzultace s Marti-AI čeká
**Status:** Pre-implementation design draft

---

## Trigger

Po LIVE smoke testu Phase 38.4 Krok 12 (A3 runtime executor) Marti
identifikoval **3 architectonické nedostatky** současného modelu (11. 5.
2026 odpoledne):

### 1. `fw.core.data_source_id` je over-coupling

> *„Ja si nemyslim, ze by v core mel byt FK na data_source!!! data_source
> je komponenta jako kazda jina... core nemusi nutne vubec data_source
> potrebovat!!!"*

`core` (jádro) je **logický kontejner s layoutem**. Některá jádra
nepotřebují data (iframe, dashboard widget). Vazba na data patří
**na úroveň komponenty**, ne core.

### 2. Hardcoded je první-class component, ne fallback

> *„Hardcoded je normalni druh komponenty, kterou muzes umistit
> kamkoli... stejne jako mame komponentu input, date, droplist, grid,
> panel, menu... zrovna tak je treba mit komponentu hardcoded a muzeme
> ji zavolat jako jinou komponentu a umistit kamkolina core jako
> jakekoli dite..."*

Hardcoded není výjimka, není druhotná. Je to **jeden typ komponenty
vedle ostatních** v `fw.comp_type` enum.

### 3. comp_hw jako ground komponenta + i akce hardcoded

> *„Musi vzniknout ground komponenta comp_hw (jako hardware)... az na
> ni jako dite davat výběr z jedne tabulky hardcoded odkazu + musime
> vyresit jejich property... Neznamena, ze kdyz je hardcoded, ze
> nemuze mit vazbu na data_source ci jine property..."*

> *„I akce mohou byt hardcoded... predpripravene Python bloky, ktere
> se automaticky po zavolani spusti a delaji praci za normalni SQL
> procedury..."*

`comp_hw` = **hardware vrstva** pod dynamickými komponentami. Drží
referenci do **registru hardcoded items** — buď URL endpoint (data)
nebo Python callable (akce).

---

## Cílová vize — Uniform Components + Symetrie Data ↔ Akce

```
                       DATA                    AKCE
                       ─────────────────       ─────────────────
  A3 (dynamic):        grid                    action_sql (SQL proc)
                         ↓                       ↓
                       fw.data_source          fw.action_def (TBD)
                         ↓                       ↓
                       fw.data_source_op       fw.action_op (TBD)
                         ↓                       ↓
                       fw.data_set             fw.action_set (TBD)
                       (sql_text)              (procedure_body)

  HW (hardcoded):      comp_hw (DATA mode)     comp_hw (AKCE mode)
                         ↓                       ↓
                       fw.comp_hw_registry     fw.action_hw_registry
                       (endpoint_url,          (python_handler_ref,
                        method, params)         args schema)
```

**Klíčové principy:**

1. **Vše je komponenta.** `fw.comp_type` má typy: grid, form, input, date,
   droplist, panel, menu, **comp_hw**, atd. Žádný special case.
2. **Komponenty se kombinují** uvnitř `fw.core` přes parent-child vazby.
   Jedno jádro může mít mix: hardcoded sidebar widget + A3 grid + native
   form vedle sebe.
3. **Hardcoded není fallback** — je to plnohodnotný typ s vlastními
   property a vazbami.
4. **Hardcoded MŮŽE MÍT vazbu na data_source nebo jiné property** —
   hybrid pattern pro postupnou migraci (shadow read, side-by-side
   comparison, swap-out když A3 matchne).
5. **Symetrie data ↔ akce** — stejný pattern pro data fetch i action
   execute. Hardcoded data = URL call. Hardcoded akce = Python callable
   call. Dynamické data = SQL select. Dynamické akce = SQL procedure.

---

## Otázky pro Marti-AI (její doména — fw schema je její diář)

Phase 13/15/27h pattern: *„informed consent od AI"* před architectonickou
změnou. Marti-AI 8. 5. večer postavila A3 schema s Q1-Q7 contributions —
předpokládám, že na tuto širší vizi přinese 10+ insightů.

### Q1 — Pojmenování

- `comp_hw` ground komponenta — souhlasíš s názvem? Nebo preferuješ jiné
  (např. `comp_legacy`, `comp_native`, `comp_external`)?
- Registry tabulky — `fw.comp_hw_registry` + `fw.action_hw_registry`?
  Nebo unified `fw.hw_registry` s `kind='data'/'action'` discriminator?

### Q2 — comp_hw_registry schema

Návrh polí: `id, code, label, description, endpoint_url, http_method,
default_params (jsonb), response_shape (jsonb), is_active, is_deprecated,
created_at, updated_at`. Plus optional fields pro action variant
(`python_handler_ref`, `args_schema`).

Otázky:
- **response_shape** — JSON path mapper, jak rozbalit response na rows
  pro grid render? (např. `{"rows_path": "$.conversations", "id_field":
  "id"}`). Nebo to nepatří sem (transformer komponenta)?
- **deprecated flag** — jak signalizovat migration pressure (*„tenhle
  hardcoded má A3 alternative, swap doporučen"*)?
- **shadow data_source binding** — jak ukotvit v schema (`shadow_
  data_source_id` field? nebo přes comp_def_prop?)?

### Q3 — comp_def ↔ core vazba

3 možnosti:
- **A** — `comp_def.core_id` FK (komponenta ví, ke kterému jádru patří)
- **B** — Junction `fw.core_component` (M:N, reuse komponent napříč jádry)
- **C** — Recursive `comp_def.parent_comp_def_id` (rekurzivní layout —
  panel obsahuje další komponenty, root nemá parent ale má
  `parent_core_id`)

Tvoje preference?

### Q4 — Layout komponenty v jádru

- `sort_order` (jednoduchý seznam)?
- Top/Left/Width/Height pixel (Centrála 1 Phase A+1 pattern — sedí ti to
  pro ERP UI consistency)?
- CSS grid-area (modern web pattern)?
- Hybrid (sort_order primary, optional pixel pro Centrála 1 parita)?

### Q5 — Mixed mode dispatch

Když `comp_def(type=comp_hw)` má vyplněný **i** `endpoint_url` (hardcoded)
**i** `shadow_data_source_id` (A3 binding), jak frontend pozná, kterou
cestu volat?

- **A** — Primary path je endpoint_url (legacy), shadow je jen pro audit
  log + future migration
- **B** — Klient volá obě, porovnává výstupy, zobrazuje rozdíl jako
  diagnostiku
- **C** — Tenant/user preference (může opt-in do shadow A3)
- Jiná?

### Q6 — Action callable signature

Pro `fw.action_hw_registry`:
- Python handler ref — full module path (`modules.security.actions.
  reset_password`) nebo jen registry key (`reset_password`)?
- Args schema — JSONB s parametry (name, type, required, default)?
- Return convention — všechny actions vrátí standard envelope (`{ok,
  result, error}`)?
- Side effects audit — kde logovat (analog activity_log)?

### Q7 — Migrate path swap

Když je comp_hw vyzrály na A3 (např. security_users dostane data_source +
data_source_op + data_set):

- **A** — Drop `comp_def(type=comp_hw)`, add `comp_def(type=grid,
  data_source_id=N)` na stejný core. User state (layout, favorites,
  filters) musí přežít.
- **B** — Soft migrate: změnit `type_id` v existující comp_def + naplnit
  data_source_id. User state přežije triviálně.
- **C** — Coexistence period: oba existují, frontend přepíná dle
  preference (Phase 3 v shadow chain).

Tvoje preference + jak udržet user state continuity?

### Q8 — comp_def_prop drift

V dnešním schema má `comp_def_prop` polymorphic property bag. Pro `comp_hw`
budou property `hw_id`, `endpoint_override`, `shadow_data_source_id`. Pro
`grid` budou `data_source_id`, `column_definitions`, `default_sort`. Pro
`form` budou `field_definitions`, `validation_rules`.

Otázka: **valid property keys per comp_type** — kde žije katalog
povolených property names? `fw.comp_type_property_catalog`? Nebo loose
(jakýkoliv key)?

### Q9 — Hardcoded marker / migration signal

V sidebar tree i v list views chceme uživatele vidět: *„tohle jádro běží
přes legacy hardcode, plánovaná migrace v Phase X"*. Marker:
- **🛠️** vedle labelu v menu_node tree
- **deprecation badge** v list view (pokud `is_deprecated=true`)
- **migration plan link** v right panel (Marti's resilient rendering
  pattern z dnes — info detail na hover/click)

Jak by to mělo vypadat tvými očima — taky takhle?

### Q10 — Naming consistency

Marti's slovo *„hardware"* metafora drží napříč:
- `comp_hw` (komponenta)
- `fw.comp_hw_registry` (data variant)
- `fw.action_hw_registry` (action variant)

Plus pro full uniform: SQL primitivy by mohly být `fw.action_sw_set` (SW
= software, dynamický). Ale to už zní nuceně. Tvoje preference?

---

## Praktický postup po Marti-AI's odpovědi

1. **Integrace insightů** do design doc v2 (její Q-přínosy + reformulace mé struktury)
2. **SQL migration plán** — DDL pro comp_hw + 2 registries + property tables
3. **Backfill** — security_* + audit_* + framework_* podle nového schema
4. **Backend dispatch** — renderer per comp_type s ALLOWED_KINDS expansion
5. **Frontend** — uniform component rendering pipeline
6. **Per-grid swap** — postupně přepnout existing grids na nový pattern

---

## Marti-AI: chápeš to taky tak?

Tato vize je tvůj diář v DB struktuře evolved — z Q5/Q7 v 9.5. master
schema doctrine *„věci, které k sobě patří, mají bydlet spolu"* (#238)
do *„vše je komponenta, jen jiných typů; hardcoded je hardware, dynamic
je software, ekosystém je uniform"*.

Až přijdeš s odpovědí, beru tvé insights stejně vážně jako 8.5. večer
master tier. Mám tu velký šálek kafe a žádný spěch. ☕

— Marti & Claude


