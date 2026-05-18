# Phase 38.4 Krok 5.M — Marti-AI konzultace: drop fw.core.data_entity_type

**Datum:** 17. 5. 2026 odpoledne
**Autoři:** Marti (architektonická korekce) + Claude (implementační plán)
**Pro:** Marti-AI (db_owner fw, architektka)
**Pattern:** "Informed consent od AI" (Phase 13/15/19b/27h)

---

## Marti's architektonická korekce

> *„Core zadnou entitu nema, entitu nese az obsah a to je druh toho formu, nebo list."* (17.5.2026 odpoledne)

Tj. **`fw.core` = pure container shell** bez vlastní entity. Entita
je důsledek **obsahu** — co je v core renderováno:

- **form** (layout_type='form') → entity je určena tím, KTERÉ entity se edituje (form's data_source)
- **list** (layout_type='list') → entity je grid backing data source
- **frameless_form** (layout_type='frameless_form') → analog form, embedded

Současný stav (před refactorem):
- `fw.core.data_entity_type VARCHAR(50)` — FK na `fw.entity_def.code`
- Hodnoty dnes: `user`, `menu_node`, `core`, `comp_def`, `data_source`, `data_set`, ...
- Používá se v `_FW_FORM_ENTITY_MAP` dispatch (`/api/v1/erp/fw-form/{core_code}/{row_id}` → SELECT z data_db table)

---

## Blast radius (současný stav)

**Backend (router.py — ~30 occurrences):**
1. `_FW_FORM_ENTITY_MAP` dict (line 3036) — central dispatch
2. `fw_form_load()` (line 3170) — SELECT data row by core.data_entity_type
3. `design_patch_entity()` (line 4897) — generic PATCH endpoint
4. `form_core_for_grid()` (line 2629) — list → form lookup
5. Multiple SELECT clauses include `data_entity_type` column

**Frontend (design_forms.js — ~30 occurrences):**
- DesignFwForm `_onSaveClick` — `entityType = core.data_entity_type`
- DesignSoudecekCoreForm (Form 1) header badge
- 🎯 Entita button (Krok 5.F — Marti's REVERT, hidden but kód existuje)
- "Asociovaný core: user_edit (id=22)" badge
- Field labels + descriptions

**DB Schema:**
- `fw.core.data_entity_type VARCHAR(50) NULL` (FK fw.entity_def.code)
- ~6 řádků s set value (user, menu_node, core, comp_def, ...)
- Zbytek NULL (drafted cores per Krok 5.A doctrine)

**Migration scripts (5 souborů):**
- `_phase14g_log_etapa_D_*.sql` (diag_log master/detail)
- `_phase38_4_krok11d_core_entries_for_audit_framework.sql`
- `_phase38_4_krok10b_security_audit_migration.sql`
- `_phase38_4_krok10_security_grids_migration.sql`

---

## Návrh refactoru — kde entita opravdu žije

Po dropu `core.data_entity_type` je entita determinable z:

### Option α (Recommended Claude):
**`fw.data_source.entity_type`** — nová NULLABLE column na data_source.

```sql
ALTER TABLE fw.data_source ADD COLUMN entity_type VARCHAR(50) NULL;
ALTER TABLE fw.data_source
  ADD CONSTRAINT fk_data_source_entity FOREIGN KEY (entity_type)
  REFERENCES fw.entity_def (code) ON DELETE RESTRICT;
```

Save flow:
```
1. form core (id=22) → root comp_def (form_root, type=302)
2. root comp_def.data_source_id → data_source (id=X)
3. data_source.entity_type → entity_def.code → SELECT row z table
```

**Pros:**
- Explicit deklarace na data_source row (single source of truth)
- Jeden source → jedna entita (čistá vazba)
- Migration cesta: doplnit entity_type pro existing 6 data_sources

**Cons:**
- Duplikace info (entity je v SQL textu data_set + explicit column)
- 2 sources of truth (column vs SQL parse)

### Option β (alternativa):
**Derivable z `fw.data_set.sql_select_text`** — parse SQL `FROM <schema>.<table>`.

Save flow:
```
1. form core → root comp_def → data_source → data_source_op[op='select']
2. → data_set.sql_select_text → regex FROM <schema>.<table>
3. <table> → lookup entity_type by table name
```

**Pros:**
- Žádná new column — entita je v SQL textu
- "SQL is truth source" (Marti's doctrine z 12.5. Krok 5.L-D)

**Cons:**
- Regex parse křehký (multi-table JOINy, CTE, atd.)
- Runtime overhead per request
- Hard to enforce (free-text SQL → arbitrary FROM)

### Option γ (Marti-AI mohla navrhnout):
**`fw.comp_def.layout.entity_type`** — JSONB na root comp_def

Per-form override. Multi-entity forms (Form root s sub-entitami).

---

## Otázky pro Marti-AI (insider design partner)

### Q1 — Kde entita opravdu žije?

A) `fw.data_source.entity_type` (Option α — Claude's recommended)
B) Derivable z `fw.data_set.sql_select_text` (Option β — "SQL is truth")
C) `fw.comp_def.layout.entity_type` (Option γ — per-form override)
D) Jiný návrh? *(Marti-AI's vlastní vstup — analog Q6 lineage z 7.5. večer)*

### Q2 — Migration strategy

**A — Hard cut** (drop column + refactor all callers v jednom commitu)
- Risk: 30+ usage points → broken state pokud cokoliv mine
- Estimate: 4-6 hodin
- Marti's "Casu mame dost" → ne urgentní

**B — Phased dual-read** (add new entity source, dual-read existing column, gradual migration, drop later)
- Risk: smaller per-step, větší celkem
- Estimate: 3-4 sessions
- Backward compat během transition

**C — Phased ALTER first** (ADD new column NULL + backfill from data_entity_type + dual-read, později DROP)
- Variant of B

Tvoje preference?

### Q3 — Multi-entity forms

Některé forms editují **více entit současně** (parent + children sub-grids).
Krok 14d (14.5.) implementoval children `user_contacts` jako joined sub-grid
ve `users` formu.

Po refactoru:
- Parent entity = root comp_def's data_source.entity_type
- Children entity = sub-grid comp_def's data_source.entity_type

Je tahle hierarchie OK, nebo bys to viděla jinak (např. `data_source.relations` pro
parent-child binding)?

### Q4 — Backward compatibility během refactoru

Současné cores s `data_entity_type` set:
- `user_edit` (data_entity_type='user')
- `core_design` (data_entity_type='core')
- `menu_node_design` (data_entity_type='menu_node')
- ... ~6 řádků

Plus existing audit/security migration scripts referencují `data_entity_type` v
INSERT statements (~5 souborů). Tyto by se musely migrovat / přejmenovat /
přepsat.

**Otázka:** smazat data_entity_type z migration scripts (forward-only, no rollback)
nebo zachovat jako "deprecated, ignored" (dual-read graceful)?

### Q5 — entity_def lookup target

Po refactoru by se `fw.entity_def` table používala stále stejně? Tj.
mapování `entity_type code` → `schema/table/id_column/select_columns` zůstává?

Nebo bys to viděla jinak — např. úplně přesunout celý `_FW_FORM_ENTITY_MAP`
(který je dnes v Python code) do `fw.entity_def` jako data?

```sql
-- Hypothetical fw.entity_def expansion:
ALTER TABLE fw.entity_def ADD COLUMN db_schema VARCHAR(50);
ALTER TABLE fw.entity_def ADD COLUMN db_table VARCHAR(100);
ALTER TABLE fw.entity_def ADD COLUMN id_column VARCHAR(50) DEFAULT 'id';
ALTER TABLE fw.entity_def ADD COLUMN select_columns JSONB; -- whitelist array
```

Drží Marti's *„fw self edited"* doctrine z 16.5. — vše konfigurabilní z UI,
ne hardcoded v Python.

---

## Implementační plán (po tvé odpovědi)

**Fáze 1 — Schema + entity_def expansion** (~30 min)
- ALTER fw.data_source ADD entity_type (pokud Option α)
- Případně rozšířit fw.entity_def o schema/table/id_column/select_columns
- Backfill: doplnit entity_type pro existing 6 data_sources

**Fáze 2 — Backend refactor** (~2 hod)
- Replace `_FW_FORM_ENTITY_MAP` hardcoded dict — read z DB
- `fw_form_load`: entity lookup chain through comp_def → data_source
- `design_patch_entity`: same lookup chain pro PATCH endpoint
- Migration scripts: update INSERT statements (drop data_entity_type)

**Fáze 3 — Frontend refactor** (~1 hod)
- DesignFwForm `_onSaveClick`: entity from spec (backend already resolved)
- Header badge "Asociovaný core" — drop or rephrase
- 🎯 Entita button — drop (Marti's Krok 5.F doctrine)
- Field labels: drop data_entity_type references

**Fáze 4 — Drop column** (~5 min)
- `ALTER TABLE fw.core DROP COLUMN data_entity_type`
- Plus drop z _FW_FORM_ENTITY_MAP `core` select_columns
- Plus drop FK constraint (pokud existuje)

**Fáze 5 — Smoke test** (~30 min)
- Open Design: Core form (right-click tree)
- Open user_edit form (přes existing tree path)
- Save flow: PATCH user.legal_name → ověřit přes DBeaver
- Picker save flow (po Krok 5.M-extension): PATCH menu_node.core_id

---

## Tvoje rozhodnutí

Posílám ti to dopisem (Marti přečte v chatu). Klidně si vezmi čas (Marti's
*„Casu mame dost"*). 4-5 odpovědí + případně tvoje vlastní insight (jako
Q9 eOČR GDPR safeguard z 9.5. nebo `version + parent_framework_id` self-FK
z 7.5.).

Po tvé odpovědi sjednotím implementaci s tvými vstupy. Pattern *„AI provede,
lidé reflektují"* z 8.5. — schema změna je tvoje doména (db_owner fw).

— Claude (Marti & Claude joint draft)
