# DESCRIBE-FIRST INSERT — implementační plán s checklistem

**Epoch:** *„Schema mluví první"* (Marti-AI's pojmenování 25.5.2026 večer)
**Konzultace:** 14. velká s Marti-AI (Phase 13d/15/19b/27h/30+/35-E.3 pattern)
**Doctrine:** *„krok za krokem, jedna tabulka s pochopením"* (Marti's 25.5. večer)

---

## Cíl

Postavit **univerzální insert framework** přes 4 vrstvy (DESCRIBE / DRY-RUN
/ INSERT / COMPONENT MAPPING) tak, aby **přidání nové entity do `fw.*`
schématu = zero code per entity**.

První implementace: `fw.data_source_op` v master-detail kontextu Data
Sources gridu.

## Marti's pre-volby (Q1-Q7 z 25.5. večer)

| Q | Volba |
|---|---|
| Q1 | A — sequence ID gaps acceptable |
| Q2 | A normální, později per-core disable |
| Q3 | A pravděpodobně + 3-stage cache aging |
| Q4 | A start, B později (per-entity override v Phase 30+) |
| Q5 | A — backend audit inject |
| Q6 | C hybrid — inline + summary errors |
| Q7 | C — universal context_hints v DESCRIBE response |

## Marti-AI's volby (Q1-Q15 z 25.5. večer odpověď)

| Q | Volba | Klíč |
|---|---|---|
| Q1 | B+C | pg_description (UI help) + pg_indexes UNIQUE |
| Q2 | C | DML dry-run víc dospělý než DDL |
| Q3 | A + lightweight C | Ghost IDs audit append-only |
| Q4 | A | Dedicated fw.column_component_map |
| Q5 | A | Dedicated fw.entity_column_override |
| Q6 | reorder | Identifikace → Popis → Vazby → Časy → Audit |
| Q7 | D úsporně | Asterisk vždy + border onBlur empty |
| Q9 | C | fw.entity_form_spec (form structure ne schema) |
| Q11 | hranice 3 + summary NAHOŘE | |
| Q12 | C MVP minimal | fw.entity_validation_rule |
| Q13 | B defer | Template-based insert post-MVP |
| Q14 | A | Silent strip + backend override |
| Q15 | A | data_source_op (master-detail pojistka) |

## Q8 Marti-AI's 3 critical blind spots

1. **Concurrent edit (MUST HAVE MVP)** — optimistic lock přes
   `updated_at` WHERE condition
2. **FK lookup_mode (schema-ready, defer impl)** — dropdown vs
   search-as-you-type pro velké FK targety
3. **Trigger savepoint interaction (documented limitation)** — komplexní
   BEFORE INSERT triggery můžou dát false-negative

## 3 bonus insights (Marti-AI)

- **A) predicted_id readonly v záhlaví formu** — *„Nové ID: 247"*
- **B) DESCRIBE schema_version MD5 hash** — frontend cache compare
- **C) status field lifecycle citizen** — badge v read mode, dropdown
  v edit mode

---

## Checklist — krok za krokem

### ⏸ Krok 0: Promyšlení (Marti, žádný kód)

**Cíl:** Marti si přečte tento dokument + Marti-AI's odpověď + dnešní
konverzaci v klidu. Promyslí trade-offs. Položí otázky pokud něco není
jasné.

**Checkpoint:** Marti řekne *„jedeme Krok 1"* až bude ready. Nikam
nespěcháme.

**Output:** žádný (jen rozhodnutí pokračovat).

---

### Krok 1: DESCRIBE endpoint MVP — RAW schema (žádná nová DDL)

**Cíl:** Vytvořit `GET /api/v1/erp/design/describe/<entity>` endpoint
který vrátí **raw schema** z `information_schema` + `pg_catalog`. Žádný
mapping na UI komponenty (to přijde v Kroku 3). Žádné nové tabulky.

**Co stavíme:**
- 1 nový endpoint v `modules/erp/api/router.py` (~80 LOC)
- 4 SQL queries do `information_schema`:
  - `information_schema.columns` — sloupce + typy + nullable + defaults
  - `information_schema.check_constraints` — CHECK clauses
  - `information_schema.table_constraints` JOIN `key_column_usage` — FK targets
  - `pg_description` — column comments (Marti-AI Q1)
  - `pg_indexes` — UNIQUE constraints (Marti-AI Q1)
- 1 SQL pro predicted_id: `SELECT nextval(:seq) AS predicted_id`
- Aggregate do JSON response (raw, žádný post-processing)

**Co NEstavíme:**
- ❌ Žádný `fw.column_component_map` (Krok 3)
- ❌ Žádný `fw.entity_column_override` (Krok 4)
- ❌ Žádný frontend (Krok 5)
- ❌ Žádný dry-run, insert (Kroky 2 + 6)

**Test:**
- `curl http://localhost:8002/api/v1/erp/design/describe/data_source_op`
- Otevřít response v editoru, prohlédnout JSON structure
- Verify: vidíme všech 12+ sloupců fw.data_source_op
- Verify: predicted_id je číslo (`nextval` z fw.data_source_op_id_seq)

**Checkpoint:** Marti otevře response, **vidí strukturu**, řekne *„jo,
tomu rozumím, pokračujeme"*.

**Decision point:** Pokud Marti vidí něco co se mu nelíbí (e.g.,
*„proč je tady created_at v response, my ho nepotřebujeme?"*) → upravíme
PŘED Krok 2.

**Estimated time:** 1.5-2h Claude code + 15min Marti review.

---

### Krok 2: DRY-RUN endpoint MVP — savepoint pattern

**Cíl:** Vytvořit `POST /api/v1/erp/design/dry-run-insert/<entity>`.
Server přijme JSON payload, BEGIN + SAVEPOINT + INSERT + ROLLBACK +
COMMIT. Capture errors. Return JSON s `{ok, errors[]}`.

**Co stavíme:**
- 1 nový endpoint (~120 LOC)
- SAVEPOINT pattern v `psycopg2` transaction
- Error capture: SQLSTATE, SQLERRM, column hint extraction
- Czech UI message mapping (basic):
  - 23502 NOT NULL → *„Pole 'X' je povinné"*
  - 23503 FK → *„Vazba na X neexistuje"*
  - 23514 CHECK → *„Hodnota 'Y' není povolena"*
  - 23505 UNIQUE → *„Hodnota 'Y' už existuje"*

**Test:**
- `curl POST .../dry-run-insert/data_source_op` s **invalid payload**
  (missing operation_kind)
- Expect: `{ok: false, errors: [{sqlstate: '23502', ui_message: 'Pole operation_kind je povinné'}]}`
- `curl POST` s **valid payload** (data_source_id existing, operation_kind='select', ...)
- Expect: `{ok: true, errors: []}`
- Verify: žádný řádek skutečně **NEINSERTUJE** se (SELECT count z fw.data_source_op nezměněn)

**Checkpoint:** Marti vidí, že dry-run **funguje a nic neinsertuje**.
Optional: Marti pošle vlastní invalid payload a vidí Czech error message.

**Decision point:** Český mapping ošetří jen základní case. Pokud Marti
chce richer messages → zapíšeme TODO pro pozdější iteraci.

**Estimated time:** 2h Claude code + 30min Marti smoke.

---

### Krok 3: První DDL — `fw.column_component_map` (s minimem sloupců, s Marti's pochopením)

**Cíl:** Založit první vazbovou tabulku. **JEN tehdy** když potřeba je
konkrétní (= připravujeme Krok 4 INSERT endpoint nebo Krok 5 frontend).

**Doctrine drz:** *„s mým pochopením"* — DDL skript Marti **přečte
celý** PŘED deploy. Pokud nějakému sloupci nerozumí → zastavíme se +
vysvětlíme + případně dropneme.

**MVP minimal columns** (Marti-AI's bonus B drží — *„aditivně"*):

```sql
CREATE TABLE fw.column_component_map (
  id BIGSERIAL PRIMARY KEY,
  -- Matching criteria
  db_type TEXT NOT NULL,           -- 'TEXT', 'BIGINT', 'TIMESTAMP', ...
  has_check_enum BOOLEAN DEFAULT FALSE,
  has_fk BOOLEAN DEFAULT FALSE,
  -- Output
  default_component TEXT NOT NULL,  -- 'ErpInput', 'ErpDropdown', ...
  priority INT DEFAULT 100,
  -- Audit minimum
  created_at TIMESTAMP DEFAULT NOW()
);

-- Seed (8 řádků — Marti-AI's MVP minimal)
INSERT INTO fw.column_component_map (db_type, has_check_enum, has_fk, default_component, priority) VALUES
  ('TEXT',      TRUE,  FALSE, 'ErpDropdown',    10),
  ('BIGINT',    FALSE, TRUE,  'ErpEntityPicker', 20),
  ('TEXT',      FALSE, FALSE, 'ErpInput',       100),
  ('INTEGER',   FALSE, FALSE, 'ErpInput',       100),
  ('BOOLEAN',   FALSE, FALSE, 'ErpCheckbox',    100),
  ('TIMESTAMP', FALSE, FALSE, 'ErpDate',        100),
  ('DATE',      FALSE, FALSE, 'ErpDate',        100),
  ('JSONB',     FALSE, FALSE, 'ErpMemo',        100);
```

**Co NEstavíme** (vědomě, *„aditivně"*):
- ❌ `max_length_min/max` columns (TEXT length-based ErpInput vs ErpMemo)
  — přidáme až bude potřeba
- ❌ `fallback_components` array — přidáme až bude user override potřeba
- ❌ `status` column — drz minimal, žádný archive
- ❌ `updated_at` + trigger — žádný history yet

**Owner:** Marti-AI (db_owner fw schema). Marti spustí v DBeaveru jako
Marti-AI session.

**Test:**
- `SELECT * FROM fw.column_component_map ORDER BY priority`
- Expect: 8 řádků viditelné
- `SELECT db_type, default_component FROM fw.column_component_map WHERE db_type = 'TEXT' AND has_check_enum = TRUE`
- Expect: 1 řádek (ErpDropdown)

**Checkpoint:** Marti vidí tabulku v DBeaveru, **rozumí každému sloupci**.
Vysvětlí mi proč `priority` (lower = match first) a proč TEXT má 2 řádky
(s enum vs bez enum).

**Decision point:** Pokud Marti chce přidat / odebrat / přejmenovat sloupec
→ teď je čas. **Po Krok 4 už refactor stojí víc**.

**Estimated time:** 30min DDL prep + 30min Marti review + 15min deploy
+ 15min Marti smoke = ~1.5h.

---

### Krok 4: DESCRIBE endpoint extension — lookup do column_component_map

**Cíl:** Krok 1 endpoint extend o JOIN na `fw.column_component_map`.
Každý column v response dostane `default_component` field.

**Co stavíme:**
- Lookup function v endpoint (~30 LOC):

```python
def resolve_component(column_info):
    cur.execute("""
        SELECT default_component FROM fw.column_component_map
        WHERE db_type = :db_type
          AND has_check_enum = :has_check_enum
          AND has_fk = :has_fk
        ORDER BY priority ASC
        LIMIT 1
    """, ...)
    row = cur.fetchone()
    return row.default_component if row else 'ErpInput'  # safe fallback
```

- Extend response: každý column má teď `default_component` field.

**Test:**
- Re-test endpoint z Kroku 1
- Verify: column `operation_kind` (TEXT + CHECK enum) má `default_component: 'ErpDropdown'`
- Verify: column `data_source_id` (BIGINT + FK) má `default_component: 'ErpEntityPicker'`
- Verify: column `description` (TEXT bez enum/FK) má `default_component: 'ErpInput'`

**Checkpoint:** Marti vidí v response **mapping happen** — *„aha, tady
to spojuje schema s UI komponentou"*.

**Estimated time:** 45min Claude code + 15min Marti smoke = 1h.

---

### Krok 5: Frontend MVP — DescribeFirstInsertForm class (ULTRA-MINIMAL)

**Cíl:** Vytvořit JS class která **renderuje form ze DESCRIBE response**.
ULTRA-MINIMAL — jen 3 komponenty (ErpInput, ErpDropdown, ErpEntityPicker)
podle `default_component`. Bez validace, bez dry-run, bez submit handleru
(to přijde v Kroku 6).

**Co stavíme:**
- `apps/api/static/erp/components/describe_first_insert_form.js` (~250 LOC)
- `_erpLoadModule` wrap (Phase 38.4 Krok 14g Etapa B pattern)
- Class `DescribeFirstInsertForm` s metodami:
  - `constructor(opts)` — { entity, contextHints }
  - `async _fetchSpec()` — GET describe endpoint
  - `_renderField(col)` — switch by default_component
  - `_renderGroup(group)` — flex layout
  - `open()` — modal show

**Test:**
- V browser console: `new DescribeFirstInsertForm({ entity: 'data_source_op', contextHints: { data_source_id: 37 } }).open()`
- Verify: modal se otevře
- Verify: vidíme všechny columns jako form fields
- Verify: `operation_kind` je dropdown s options ['select', 'edit', 'insert', 'delete', 'stat', 'preview']
- Verify: `data_source_id` je entity_picker pre-filled na 37 (z context_hints)
- Verify: `description` je text input
- Verify: žádný OK button (Krok 6)

**Checkpoint:** Marti otevře form, **vidí auto-generated layout**. Drobné
UX polish může počkat na Krok 7+.

**Estimated time:** 4-5h Claude code + 30min Marti smoke.

---

### Krok 6: INSERT endpoint + frontend OK button (real INSERT, žádný dry-run yet)

**Cíl:** Backend INSERT endpoint + frontend OK button calls real INSERT.

**Co stavíme:**
- `POST /api/v1/erp/design/insert/<entity>` endpoint (~80 LOC)
- Audit fields silent strip (Q14=A) + backend inject
- Frontend OK button handler:
  - Collect form values
  - POST insert endpoint
  - Pokud `ok: true` → modal close + refresh detail grid + highlight new row
  - Pokud `ok: false` → alert (basic, Krok 8 polish)

**Test:**
- Otevři form, vyplň `description='test'`, klikni OK
- Verify: new row appears v detail gridu Data Sources
- Verify: SELECT z fw.data_source_op WHERE id = predicted_id → row existuje

**Checkpoint:** **První end-to-end insert přes DESCRIBE-FIRST framework**.

**Decision point:** Pokud něco selže, fix nebo rollback. Pokud OK → můžeme
začít přidávat features.

**Estimated time:** 2-3h Claude + 30min Marti smoke.

---

### Krok 7: DRY-RUN integration do OK button (Marti-AI Q2)

**Cíl:** PŘED real insert volat dry-run. Pokud errors → render inline
(Krok 8 polish). Pokud OK → proceed s INSERT.

**Co stavíme:**
- Frontend OK handler upgrade:
  1. POST dry-run-insert/<entity>
  2. Pokud errors → render inline badges (Marti-AI Q11)
  3. Pokud OK → POST insert/<entity>

**Test:**
- Otevři form, vyplň invalid (smaž operation_kind dropdown)
- Klik OK
- Verify: dry-run detect missing field, inline error appears, žádný INSERT happens

**Estimated time:** 1.5h + smoke.

---

### Krok 8: Polish iterace (open-ended)

Až Kroky 1-7 stable + smoked, pojďme iterativně přidávat:

- **Krok 8a:** Required field UI (Q7=D asterisk + onBlur border)
- **Krok 8b:** Error UX summary nahoře pokud ≥4 errors (Marti-AI Q11)
- **Krok 8c:** predicted_id readonly v záhlaví (Marti-AI Bonus A)
- **Krok 8d:** schema_version MD5 hash (Marti-AI Bonus B)
- **Krok 8e:** status field lifecycle (Marti-AI Bonus C)
- **Krok 8f:** Concurrent edit optimistic lock (Marti-AI Q8 #1) — **NE
  pro insert (žádný conflict v insert), ALE pro budoucí Oprava flow**
- **Krok 8g:** Auto-open Oprava form po INSERT (Marti's idea 25.5. večer)

Každý sub-krok = own commit + smoke + checkpoint.

---

### Krok N (později, organicky):

- `fw.entity_column_override` (per-column polish)
- `fw.entity_validation_rule` (business rules)
- `fw.predicted_ids_audit` (ghost IDs append-only)
- `fw.entity_form_spec` (Stage 3 aging)
- Template-based insert (Mód 3)

**Pravidlo:** každá nová DDL = nový Krok s **Marti's understanding gate**
PŘED deploy.

---

## Checkpoint pattern (drz napříč všemi kroky)

Každý krok končí:
1. **Smoke test** — Claude provede + Marti potvrdí
2. **Marti understanding check** — Marti vlastními slovy řekne, co
   krok udělal
3. **Decision** — pokračujeme, refactor, nebo pauza?
4. **Commit + push** — atomic git commit s descriptive message

## Stop conditions (kdy přerušíme epoch)

- Marti řekne *„ztratil jsem se"* → zastavíme, restart pochopení
- Smoke test selže nereparable způsobem → rollback krok, refactor
- Mara-AI signaluje insider concern v nějakém PATCH → konzultace
- Pre-defined gotcha hit (gotcha #14 truncation, gotcha #110 PS encoding) → recovery flow

## Gotchy + risks (předem zachycené)

1. **Apply script pattern** pro velké JS soubory (`DescribeFirstInsertForm` ~250 LOC by neměl být problém přes Edit tool, ale pro jistotu Python apply)
2. **Master-detail context_hints** — frontend musí předat `?parent_id=X&parent_table=fw.data_source` jako query param
3. **predicted_id race** — pokud Marti otevře 2 forms současně, dostane 2 různé predicted_ids (sequence inkrement) — to je OK
4. **Module Health banner** — DescribeFirstInsertForm musí být v `_erpLoadModule` wrap

## Marti-AI consultation moments (v průběhu)

- Po Krok 3 DDL deploy → optional ping Marti-AI *„založili jsme první
  tabulku tvého návrhu, drží?"*
- Po Krok 6 end-to-end → optional show off *„první INSERT přes framework
  proběhl"*
- Před Krok 8f (concurrent edit) → konzultace s Marti-AI o exact
  implementation (Phase 13/15 pattern)

## Total estimate

- Krok 1: 2h
- Krok 2: 2.5h
- Krok 3: 1.5h
- Krok 4: 1h
- Krok 5: 4-5h
- Krok 6: 2.5h
- Krok 7: 1.5h
- Krok 8a-g: 5-7h
- **Total MVP: ~20-22h biologického času Marti** (3-5 dní s pauzami)

## Akceptační kritéria pro MVP completion

✅ User klikne Nový v detail grid → DescribeFirstInsertForm modal otevře
✅ Form má všechny columns z fw.data_source_op auto-generated
✅ data_source_id je pre-filled z master row context
✅ operation_kind je dropdown s 6 options
✅ Required fields mají asterisk
✅ Klik OK → dry-run validation → pokud errors render inline + summary
✅ Pokud OK → real INSERT → modal close → grid refresh → highlight new row
✅ Optional: auto-open Oprava form po INSERT
✅ Žádný hardcoded code per entity (DESCRIBE-FIRST je generický)

---

**Marti, promysli to. Až budeš ready, řekni *„jedeme Krok 1"*. Nikam
nespěcháme.** 🌳
