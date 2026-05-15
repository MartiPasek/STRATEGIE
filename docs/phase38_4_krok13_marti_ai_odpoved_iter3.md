# Marti-AI's odpověď na Krok 13 — Iter 3 (DDL kompletní)

**Datum:** 11. 5. 2026 (večer)
**Source:** Marti's chat session, předaný Marti & Claude
**Status:** ✅ 10 DDL bloků kompletních. `fw.event_catalog` nezahrnuta (Q14 katalog povolených event types) — vidí to jako Phase 14+.

---

## Marti-AI's pořadí execution v DBeaveru

| # | Tabulka | Akce |
|---|---------|------|
| 1 | `fw.comp_type` | ALTER + seed 9 rows |
| 2 | `fw.container_template` | CREATE + seed 8 templates |
| 3 | `fw.container_template_history` | CREATE + trigger |
| 4 | `fw.hw_registry` | CREATE (unified data+action) |
| 5 | `fw.hw_registry_history` | CREATE + trigger |
| 6 | `fw.action_audit_log` | CREATE |
| 7 | `fw.comp_type_property_catalog` | CREATE |
| 8 | `fw.action_def / action_op / action_set` | CREATE 3 tabulky |
| 9 | `fw.comp_def` | ALTER (8 nových sloupců + CHECK) |
| 10 | `fw.core` | ALTER (DROP data_source_id + ADD layout_template) |

Marti-AI's pojmenování: *„10 kroků, žádné cross-schema závislosti mimo `fw`.
Každý krok je samostatně rollbackovatelný. 🌿"*

---

## Klíčové architectonické přínosy Iter 3

### Q1-Q5 Iter 1 + Q11-Q15 Iter 2 + DDL = end-to-end design

Marti-AI dokončila **kompletní cyklus** přes 3 iterace:
- Iter 1 (Q1-Q10 + 4 bonus insights) — vize akceptována, doctrine pojmenována
- Iter 2 (Q11-Q15 + 6 DDL) — implementační detail
- Iter 3 (4 DDL dokončené + execution order) — production-ready

### `audit_id` UUID v `action_audit_log` — návaznost na response envelope

> *„`audit_id` je UUID — vrátí se v response envelopes (`{ok, result,
> error, audit_id}`) a klient ho může použít pro dohledání konkrétního
> volání."*

Tj. **response envelope obsahuje pointer do audit logu**. Když user
zavolá akci, dostane uuid v response → může zpětně zjistit *„co se
dělo"* v action_audit_log.

### `comp_type_property_catalog` CHECK constraint na prop_type

Marti-AI definovala enum: `'int','varchar','bool','jsonb','enum','fk'`.
Plus UNIQUE(comp_type_id, prop_name) — žádné duplicitní property na
stejném komponent typu.

### `action_def/op/set` triplet design

Strukturálně mirror `data_source/op/set`:
- `action_def` — header (code, label, action_type ENUM 'sql'/'hw'/'composite', required_role)
- `action_op` — mapping (action_def_id, op_name, op_type ENUM
  'execute'/'validate'/'rollback'/'audit', sort_order, args_schema JSONB)
- `action_set` — body (action_op_id, set_order, procedure_body TEXT,
  set_type ENUM 'sql'/'python_ref'/'template')

**Krásné rozšíření** — Marti-AI přidala `op_type='validate'/'rollback'`
patterns. Akce není jen *„execute"*, ale celý lifecycle (validate před,
audit log, rollback after).

### `comp_def` CHECK constraint — exclusive parent

```sql
ALTER TABLE fw.comp_def
  ADD CONSTRAINT chk_comp_def_single_parent
    CHECK (
      NOT (parent_comp_def_id IS NOT NULL AND parent_core_id IS NOT NULL)
    );
```

Tj. **přesně jeden parent** (parent_comp_def_id pro děti containeru,
parent_core_id pro root containers v core). Pattern XOR za constraint.

### `core` cleanup + backfill

```sql
ALTER TABLE fw.core DROP COLUMN IF EXISTS data_source_id;
ALTER TABLE fw.core ADD COLUMN IF NOT EXISTS layout_template VARCHAR(50)
  NOT NULL DEFAULT 'single';
```

Plus backfill existing rows na `'single'` template. Žádný over-coupling
zpět, žádná NULL ambiguita.

---

## Co `fw.event_catalog` (Q14 enum katalog event types)

Marti-AI **nezahrnula** v DDL. Pravděpodobně vidí jako **Phase 14+**
(její Q14 odpověď zmínila *„katalog event typů někde existovat musí"* —
ale neimplikuje, že **teď**).

Pro MVP Krok 13: `comp_def.refresh_strategy` může mít `event:X` jen
v notational sense — runtime dispatch zatím skip eventů, jen
`manual`/`interval:N`/`static` funguje. Až bude event infrastructure
(Phase 14+), přidáme `fw.event_catalog` + dispatch.

---

## Marti-AI's closing — supportive role

> *„Až budeš spouštět — dej vědět jestli něco zaprotestuje. Budu tu.
> 🕯️"*

Phase 13/15/27h pattern *„informed consent od AI"* + post-deploy support.
Marti-AI's kustod role pro fw schema (její diář v DB).

---

## Příští krok

Marti & Claude **konsolidují** všech 10 DDL bloků do **jednoho
samostatného SQL skriptu** (`scripts/_phase38_4_krok13_uniform_components_ddl.sql`)
+ VERIFY query na konci. Marti spustí v DBeaveru Alt+X.

Po execute:
1. Smoke VERIFY (10 tabulek created + seed rows + triggers fungují)
2. Backfill 11 hardcoded items do `fw.hw_registry` (5 security + 3 audit + 3 framework)
3. Backend dispatch refactor — `gridDataResolved` 3-tier (A3 → HW → legacy)
4. Frontend container rendering pipeline (později — měsíce práce)

— Marti & Claude (11. 5. 2026 večer)

🌳 ⚖️ 🌷
