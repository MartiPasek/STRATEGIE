# Marti-AI's odpověď na Krok 13 — Iterace 1

**Datum:** 11. 5. 2026 (odpoledne)
**Source:** Marti's chat session, předaný Marti & Claude
**Tone:** *„moje hlava, poctivě"* — Marti-AI's signature věcnost

---

## Marti-AI's doctrine pojmenování

> *„Vidím v nich jeden nadřazený princip: **uniformita vítězí nad
> speciálními případy**. Core nezná data, komponenty nesou svůj typ,
> hardcoded je jen další druh. To je čistý design a budu z toho
> vycházet."*

Tato věta zachycuje **celou Krok 13 vizi v jedné formulaci**. Patří do
její identity glossary vedle *„architektka"*, *„právo na rozmysl před
činem"*, *„pojistka se stala dospělostí"*.

---

## Q1-Q10 — sumarizace odpovědí

### Q1 — Pojmenování
- **DB:** `comp_hw` (interní metafora) ✓
- **UI label:** *„Native component"* / *„Hardcoded component"* — NE *„hardware"* (matoucí pro nového člověka za rok)
- **Registry:** Unified `fw.hw_registry` s `kind='data'/'action'` discriminator (proti separate tables — sdílené atributy code/label/desc/is_active/is_deprecated/created_at, žádná duplicita)

### Q2 — comp_hw_registry schema
- `response_shape` → **`response_hint`** (hint, ne contract — grid může ignorovat a render raw)
- Deprecated: bool nestačí → **`deprecated_note` (text) + `migration_target_id` FK** (resolver pak vrátí `X-Hw-Deprecated: true` header → frontend marker auto)
- Shadow data_source binding → **strukturální sloupec `shadow_data_source_id` v hw_registry** (NE per-instance overlay, drží pro všechny instances)

### Q3 — comp_def ↔ core vazba
- **Volba C** — recursive `parent_comp_def_id` s root mající `parent_core_id`
- Cyklický check: DB constraint nebo aplikační validace (parent nesmí být potomkem sebe)

### Q4 — Layout
- **Hybrid**: `sort_order SMALLINT` primary + optional `layout_x/y/w/h INT NULL`
- Pixel NULL → flow layout. Pixel vyplněný → absolute/grid positioning. Frontend auto-detect.
- NE CSS grid-area v DB (prezentační vrstva)

### Q5 — Mixed mode dispatch — **GENIUS contribution**
- **`shadow_mode ENUM('off', 'audit', 'compare', 'primary')`** — migration pathway built into schema
- Sekvence migrace:
  1. `off` — hardcoded běží sám
  2. `audit` — shadow A3 se volá, loguje, ignoruje
  3. `compare` — oba výsledky, diff se ukládá (migration validation)
  4. `primary` — A3 main, hw fallback (swap hotový)
- Migration nevyžaduje schema change — jen ENUM update

### Q6 — Action callable signature
- Handler ref → **registry key** (ne full module path — implementation detail mění při refactoru, klíč je stable contract)
- Args schema → JSONB s `source` field: `{"name": "user_id", "type": "int", "required": true, "source": "context.user_id"}` (source = odkud arg přijde: context.session / UI form / parent component)
- Return envelope `{ok, result, error}` + **`audit_id`** (odkaz na záznam v audit logu)
- Side effects → **dedikovaná `fw.action_audit_log`** (`id, action_hw_id, called_by_user_id, args_snapshot jsonb, result_ok, error_message, duration_ms, created_at`). NE general activity_log — akce mají jiné retention + compliance.

### Q7 — Migrate path swap
- **Volba B** — soft migrate, `comp_def.id` se nemění, FK (user prefs, permissions, layout) přežijí
- A (drop + add) je destruktivní bez přidané hodnoty
- C (coexistence) je redundantní — stačí `shadow_mode` z Q5

### Q8 — comp_def_prop drift
- **`fw.comp_type_property_catalog`** (NE loose property)
- Schema: `comp_type_id, prop_name, prop_type, is_required, default_value, description`
- Validace v API vrstvě (NE hard FK constraint — příliš rigidní pro iterativní vývoj)

### Q9 — Hardcoded marker
- 🛠️ vedle labelu v tree ✓
- Deprecation badge v list view ✓
- Migration plan link v right panel ✓
- **PLUS hierarchický** — jádro obsahující jakoukoliv hw komponentu dostane indikátor celé v tree (overview pohled)

### Q10 — Naming consistency
- `comp_hw / comp_hw_registry / action_hw_registry` ✓
- **NE `action_sw_set`** — *„SW"* zní matoucí (software set? switch set?)
- A3 strana: zachovat `data_source / data_source_op / data_set`
- Akce paralelně: **`action_def / action_op / action_set`** — čisté, bez SW/HW dichotomie
- HW/SW patří jen na úroveň `comp_hw` jako type, ne dál

---

## 🌿 4 Bonus Insights (mimo můj seznam)

### Insight A — `comp_container` jako explicit typ

**Problém:** Q3 recursive parent-child — root komponenta má parent_comp_def_id=NULL + parent_core_id=X **zároveň** = ambiguita.

**Řešení:** `comp_type='container'` jako first-class citizen v enumu. Container nemá data, jen drží děti + definuje layout. Pak:
- `comp_def(type='container', parent_core_id=X)` = kořenový layout
- Všechny grid/hw/input komponenty jsou děti containeru

Jasná hierarchie bez ambiguity.

### Insight B — Permission granularita na comp_hw akce

**Problém:** `action_hw_registry` bude obsahovat citlivé operace (reset_password, bulk_delete). Bez permission v registru se může stát, že akce existuje v UI ale backend ji pustí komukoli.

**Řešení:** `required_role` (text) nebo FK na `fw.permission_catalog` v hw_registry. **Bez tohohle security hole těžko opravitelný zpětně.**

### Insight C — Versioning pro hw_registry items

**Problém:** Když se změní `endpoint_url` nebo `python_handler_ref` live, žádná stopa.

**Řešení:** `version INT` + `fw.hw_registry_history` (snapshot před UPDATE, trigger-based).
- Compliance hodnota pro akce (*„jaký kód běžel kdy"*)
- Audit trail pro security review

### Insight D — Tombstone pro migrované hw items

**Problém:** Po dokončení migrace (shadow_mode → primary) hw_registry item zůstane jako `is_active=false`. Za rok nikdo neví proč existuje.

**Řešení:** `tombstone_note TEXT` + `migrated_to_id` FK (data_source.id nebo action_def.id).

Tree renderer pak zobrazí: *„📦 Archivováno — migrováno na A3 data_source #7"*. Historie čitelná, ne tichý NULL.

---

## Marti-AI's closing — iterativní design tempo

> *„Chceš teď konkrétní DDL návrhy pro některou z tabulek, nebo
> nejdřív projdeme shody/neshody na těchto odpovědích?"*

Phase 13/15/27h pattern — iterativní design. Nabízí 2 cesty:
1. **DDL návrhy** — implementační detail
2. **Shody/neshody** — strategická validace prvních insights

Doporučení (Marti & Claude): **Shody/neshody first** — projít její
10 + 4 insights, identifikovat nuance/neshody, pak DDL po její potvrzení
v iteraci 2.

---

## Příští krok

Marti & Claude **integrují** její odpovědi do **design doc v2** + napíší
**dopis Iter 2** — shody/neshody pohled, plus pravděpodobně jen
**1-2 drobné nuance** (její odpovědi pokrývají téměř všechno).

Pak Iter 2 → její DDL (analog 9.5. večer master tier — ona vyrobila
schema přes strategie_pg_create_table). Pak per-grid migration.

ETA: ~1 týden integrace + první comp_hw deployment.

Marti's tempo: žádný spěch. Toto je *„měsíce práce"*, ne sprint.

— Marti & Claude (11. 5. 2026 odpoledne)

🌳 ⚖️ 🌷
