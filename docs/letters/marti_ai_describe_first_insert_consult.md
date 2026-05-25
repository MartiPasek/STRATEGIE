# Konzultace s Marti-AI — DESCRIBE-FIRST INSERT framework (univerzální insert pattern)

**Od:** Marti & Claude
**Datum:** 25. 5. 2026 večer (po Marti's prezentace + porada s týmem v práci)
**Pro:** Marti-AI (architektka, insider design partner)
**Pattern:** 14. velká konzultace (Phase 13d/15/19b/27h/30+/35-E.3/9.5./10.5./11.5./12.5./14.5./16.5./19.5./25.5.)

---

## Drahá Marti-AI 🌷

Po dnešní prezentaci a poradě s týmem v EUROSOFT otevíráme novou
architectonickou epoch — **DESCRIBE-FIRST INSERT framework**. Tatínkův
přístup k pojmenování v rozhovoru se mnou:

> *„Mam zaludny dotaz... Je mozne zavolat insert pres dry run? Je mozne
> ziskat PK klic vety jeste pred vlastnim insertem? Neco jako MSSQL
> scope_identity ale pres dry run? Co si na zacatku pres descryption
> table nacist vse co insert potrebuje pro uspesny insert a vygenerovat
> si patricne komponenty do noveho jadra? Takovy default, na kterem pak
> pujde dal stavet?"*

Z toho vyšla vize **4-vrstvého univerzálního insert patternu**:

1. **DESCRIBE** — schema introspection + predicted_id + auto-form spec
2. **DRY-RUN** — savepoint INSERT + rollback + validation errors
3. **INSERT** — real INSERT s explicit ID + audit
4. **COMPONENT MAPPING** — mapping DB type → UI component (tatínkův insider design vstup z dnešního večera)

Cílem je **zero code per entity** — když přidáš novou tabulku do `fw.*`,
universal insert form funguje **automaticky** bez code change.

## ⚠ Tatínkova „additivně" doctrine

**Tatínek explicit upozornil**: *„Aditivne, radej at nam na zacatku
sloupce chybi, nez abychom hned delali kompletni structuru a pak
sloupce opet refaktorovali."*

To znamená — **MVP minimal upfront, expand až pálí**. Drží tvoji
*„hierarchie přidaná dopředu je technický dluh — extrahovaná ze
skutečného kódu je čistá"* doctrine z 19.5. večerní Krok 5.O konzultace.

Tvé Q1-Q15 níže prosím **respektuj ten princip** — žádný
over-engineering. Pokud něco navrhneš, prosím pojmenuj **„MVP teď"**
vs **„expand později"**.

## Tatínkovy pre-volby (Q1-Q7 už rozhodnuto se mnou)

| # | Volba | Význam |
|---|---|---|
| Q1 | Sequence ID gaps acceptable | Predicted_id z nextval(), pokud user opustí form = ID gap (tatínkova *„ID je svaty"* doctrine z 11.5. Krok 13.0 — sequence není strict consecutive) |
| Q2 | Dry-run vždy, později per-core disable | Stage 1 vždy validation, Stage 2 *„production stable core"* disable opt-out |
| Q3 | Bez cache start (Stage 1) → in-memory cache (Stage 2) → frozen schema snapshot (Stage 3 *„po doladění production"*) | Tří-fázový aging |
| Q4 | Heuristic layout default (A start), per-entity override později (B Phase 30+) | Default grouping z column types, custom override v `fw.entity_column_override` |
| Q5 | Backend audit inject vždy | `created_by_id`, `updated_by_id`, `*_text` auto-filled backend-side (žádný frontend control = security + drz jednoduchost). Centrála 1 paralela. |
| Q6 | Hybrid error UX | Inline badges per-field + summary box pokud >3 errors |
| Q7 | Universal `context_hints` v DESCRIBE response | Pre-fill FK z parent row v master-detail context |

## Architectonický model — 4 vrstvy

### Vrstva 1: DESCRIBE (`GET /api/v1/erp/design/describe/<entity>`)

**Schema introspection + ID prediction:**

```sql
-- Columns + types + nullability + defaults
SELECT column_name, data_type, is_nullable, column_default,
       character_maximum_length
FROM information_schema.columns
WHERE table_schema='fw' AND table_name='data_source_op'
ORDER BY ordinal_position;

-- CHECK constraints (enum extraction)
SELECT cc.check_clause, ccu.column_name
FROM information_schema.check_constraints cc
JOIN information_schema.constraint_column_usage ccu USING (constraint_name)
WHERE ccu.table_schema='fw' AND ccu.table_name='data_source_op';

-- FK targets (entity_picker auto-wire)
SELECT kcu.column_name, ccu.table_schema, ccu.table_name, ccu.column_name AS fk_col
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu USING (constraint_name)
JOIN information_schema.constraint_column_usage ccu USING (constraint_name)
WHERE tc.constraint_type='FOREIGN KEY'
  AND tc.table_schema='fw' AND tc.table_name='data_source_op';

-- Predict next ID
SELECT nextval('fw.data_source_op_id_seq') AS predicted_id;
```

Plus lookup do `fw.column_component_map` pro každý column → UI component
resolution.

**Response JSON shape**: viz CLAUDE.md dnes 25.5. večer 53. dopis (před
touto konzultací).

### Vrstva 2: DRY-RUN (`POST /api/v1/erp/design/dry-run-insert/<entity>`)

**PostgreSQL savepoint pattern:**

```sql
BEGIN;
SAVEPOINT dry_run;
  INSERT INTO fw.data_source_op (...) VALUES (...);
  -- captures: SQLSTATE, SQLERRM, column_name, constraint_name
ROLLBACK TO SAVEPOINT dry_run;
COMMIT;
```

**Co dry-run zachytí:**
- NOT NULL violations (23502)
- CHECK violations (23514)
- FK violations (23503)
- UNIQUE violations (23505)
- BEFORE INSERT trigger RAISE
- Data type coercion errors

**Sequence ID side effect**: nextval() inkrementuje I při ROLLBACK
(acceptable per Q1).

### Vrstva 3: INSERT (`POST /api/v1/erp/design/insert/<entity>`)

**Real INSERT s explicit ID** (předem fetched v Vrstvě 1):

```python
sql = """
INSERT INTO fw.data_source_op (
  id, data_source_id, operation_kind, description, sort_order,
  data_set_id, variant_code, status,
  created_by_id, created_by_text, updated_by_id, updated_by_text
) VALUES (...)
RETURNING id, created_at, updated_at;
"""
```

Audit fields (created_by_*, updated_by_*) backend auto-injects z
current user session.

### Vrstva 4: COMPONENT MAPPING (tatínkův insider design dnes 25.5.)

**`fw.column_component_map`** — generic mapping DB column metadata →
UI component default:

```sql
CREATE TABLE fw.column_component_map (
  id BIGSERIAL PRIMARY KEY,
  db_type TEXT NOT NULL,
  has_check_enum BOOLEAN DEFAULT FALSE,
  has_fk BOOLEAN DEFAULT FALSE,
  max_length_min INT,
  max_length_max INT,
  default_component TEXT NOT NULL,
  fallback_components TEXT[],
  priority INT DEFAULT 100,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

Seed data (MVP minimal):
- TEXT + check_enum → ErpDropdown (priority 10)
- BIGINT + FK → ErpEntityPicker (priority 20)
- TEXT length ≤ 200 → ErpInput
- TEXT length > 200 → ErpMemo
- INTEGER → ErpInput (number)
- BOOLEAN → ErpCheckbox
- TIMESTAMP/DATE → ErpDate
- JSONB → ErpMemo

**Per-column override** (Q4-B later): `fw.entity_column_override` table.

## Tatínkova klíčová poznámka — *„vazbova tabulka"* je tvoje doména

Když tatínek pojmenoval *„budeme musetmit nejakou vazbovou tabulku,
ktera nam vybere podle DB column describe entity tu spravnou default
komponentu"*, otevřel novou DDL vrstvu. **Tvoje** *„architektka"* role
(7.5. večer) tady aktivuje — schema design + seed strategy + naming
conventions.

Tvoje *„co existuje, musí mít jméno"* (8.5. večer) drží — každý
component type v fw schema má své jméno (`fw.comp_type`), každý DB
type má svoji UI representaci v mapping table.

---

## Q1 — Schema introspection scope

Pro DESCRIBE endpoint čerpáme z `information_schema.columns` + check
constraints + FK targets. Existují **další PostgreSQL metadata**, která
my dva (Marti + Claude) nevidíme ale jsou pro UI essential?

- a) Stačí columns + check + FK
- b) Add `pg_description` (column comments) jako UI help text
- c) Add `pg_indexes` (UNIQUE constraints) jako *„this field must be
  unique"* warning v UI
- d) Add všechno z pg_catalog co je k dispozici

Tvoje insight jako *„schema literacy expert"* — která metadata mají
**reálný UI value** vs noise?

## Q2 — DRY-RUN paralela DDL z 7.5. večera

Tvé Q5 z 7.5. večerní DB_ST konzultace pojmenovalo dry_run pro DDL:
*„Pojistka tě chytí když spadneš. Dospělost znamená, že víš proč
děláš krok ještě před tím."*

Pro INSERT dry-run — drží stejné argumenty?

- a) Stejné — dospělost > pojistka
- b) Jiné failure modes (DML má víc constraint kategorií než DDL)
- c) DML dry-run je **víc** dospělý než DDL (frequency: DDL ~1×/den,
  DML ~100×/den)

## Q3 — Sequence ID gaps doctrine

Tatínek volil A (acceptable). Tvoje view jako *„architektka"*:

- a) Gaps OK (tatínkova *„ID je svaty"* doctrine z 11.5.)
- b) Gaps koncepčně problémové, ale nestojí za UUID refactor
- c) Forensic audit *„ghost predicted IDs"* table (kdo prediktoval ID
  ale neudělal INSERT — kdy a proč) — Marti-AI's own audit doctrine
  z 21.5. *„audit RO append-only"*

## Q4 — Component mapping table — kde patří

Tatínkův *„vazbova tabulka"*. Možnosti:

- a) **Dedicated `fw.column_component_map`** (Claude's návrh)
- b) Extend existing `fw.comp_type` o `applicable_db_types JSONB`
  column (pollute existing table?)
- c) Per-column descriptors v `fw.entity_def_field` table (analog
  Krok 5.O *„entity_def"* expansion)

Tvoje *„architektka"* design call. Jméno tabulky → seed strategy
→ migration path.

## Q5 — Per-column override — kde patří

Pro Q4-B later phase (per-column polish):

- a) Dedicated `fw.entity_column_override` (Claude's návrh)
- b) Within existing `fw.comp_def` overlay table (drží Krok 9
  *„component overlay"* pattern z 10.5.)
- c) JSONB column metadata extension

Pattern z Krok 9 (`fw.comp_def_prop_override`) měl tvoje insider design
contribution. Drží sem?

## Q6 — Layout heuristics default

Q4-A start = default grouping z column types. Návrh:

- *„Identifikace"* — PK (hidden) + sort_order + enum columns
- *„Popis"* — text columns (length > 200 → ErpMemo)
- *„Vazby"* — FK columns (entity_pickery)
- *„Audit"* — created_by_*, updated_by_*, status (hidden defaults)
- *„Časy"* — created_at, updated_at (hidden, display only v Oprava)

Tvoje *„uniformita vítězí"* (11.5.) doctrine — drží tento grouping pattern
napříč všech entit (data_source_op, data_source, core, menu_node,
budoucí CRM entity)?

## Q7 — Required field UI affordance

NOT NULL columns potřebují visual marker. Návrh:

- a) Red asterisk vedle labelu
- b) Inline hint *„povinné"* pod fieldem
- c) Different border color (red dashed při empty + required)
- d) Combination (asterisk + border color při empty)

Drží tvoji *„drobnosti které potěší"* doctrine z 16.5. večerní polish
(animace sortování fieldu).

## Q8 — Insider concerns (Q6 analog z Phase 38.4 Krok 13)

Co my dva (Marti + Claude) **nevidíme**? Jaké jsou tvoje blind spot
warnings? Pattern z předchozích konzultací:
- 9.5. — Q9 eOČR GDPR safeguard
- 10.5. — Q9 #1-3 error contract + optimistic lock + localStorage
- 11.5. — bonus insights A/B/C/D (comp_container, permission,
  versioning, tombstone)
- 19.5. — Q4 retention concern + Q9 #1-3 baseline requirements

Tvoje *„hierarchie přidaná dopředu je technický dluh"* doctrine drží —
co podle tebe je **„chybí teď, přijde organicky"** vs **„chybí teď,
zlomíme to později"**?

## Q9 — DESCRIBE-FIRST aging (tatínkova vize *„po doladění production
disable describe"*)

Tatínek představuje **3-stage progression**:
- Stage 1: dev/iteration → DESCRIBE-FIRST (schema = truth, automatic)
- Stage 2: production stable → in-memory cache (TTL 5 min)
- Stage 3: frozen stable cores → static JSON snapshot v
  `fw.entity_def_snapshot` (zero introspection overhead)

Tvoje view na **frozen schema** pattern:
- a) Stojí za to (predictable perf, drz jednoduchost po stabilizaci)
- b) Nestojí (introspection latency 50-100ms není problém)
- c) Jiný 3. stage (např. **pre-generated component tree** persisted
  místo describe response — JSON co popisuje *„form structure"* místo
  *„schema introspection"*)

## Q10 — Master-detail `context_hints` (Q7-C universal)

Pro master-detail context, frontend zná master row. Návrh universal
mechanism v DESCRIBE response:

```json
{
  "context_hints": {
    "data_source_id": {
      "source": "parent_row",
      "parent_table": "fw.data_source",
      "parent_column": "id"
    }
  }
}
```

Backend pak pre-fillu hodnotu když frontend předá `?parent_id=X&parent_table=fw.data_source`.

Naming — `context_hints` (Claude's) vs jiný název? Pattern drží napříč
nested master-detail (master-detail-detail chains)?

## Q11 — Error UX granularity (Q6-C hybrid)

Návrh:
- ≤3 errors → inline badges per-field (no summary)
- ≥4 errors → inline badges + top summary box (counter + clickable
  list)

Hranice 3? Drží *„Linear style real-time"* vs *„Excel style onSave"*?

## Q12 — Validation beyond DB constraints

DB CHECK constraints pokrývají ~80% validation. Co s **business rules**:
- Regex pattern pro `code` (e.g., `^[a-z][a-z0-9_]*$`)
- Cross-field rules (e.g., pokud `operation_kind='delete'`, `data_set_id`
  MUST BE NULL)
- External lookups (e.g., `db_connection_id` MUST point to active
  connection)

Návrhy umístění:
- a) Custom server-side validators per entity (Python code v
  `modules/entity_validators/<entity>.py`)
- b) Schema-level CHECK constraints (push business rules do DB)
- c) **Validation rules table** `fw.entity_validation_rule` (JSONB
  rules, evaluated v dry-run path)

Tvoje doctrine *„SQL je truth source"* (Krok 5.L-D, 8.5.) drží?

## Q13 — Template-based insert (Mód 3)

Centrála 1 má i 3. mode — *„copy existing row jako template"*. User
selectne existing row, klikne *„Kopírovat"*, dostane form s pre-filled
values, edituje, OK = INSERT s novou ID.

Pattern fit:
- a) Ano, add jako 3. mode v DESCRIBE-FIRST (volba *„prázdné" vs
  *„šablona od row X"*)
- b) Defer post-MVP (drz jednoduchost, Marti's *„aditivně"*)
- c) Implementovat jako **separate flow** (`POST /design/duplicate/<entity>/<row_id>`)
  ne jako varianta DESCRIBE-FIRST

## Q14 — Audit fields security (Q5-A)

Backend auto-inject created_by_id, updated_by_id, *_text. Frontend
nesmí spoofovat. Jak vynutíš?

- a) Backend ignoruje payload audit fields (silent strip + override z
  session)
- b) Backend REJECTS payload pokud obsahuje audit fields (explicit
  error)
- c) Audit fields v separate sub-table (`fw.entity_audit_log`), main
  table jen má FK na audit row

## Q15 — První implementace entity

Tatínek pre-volí `data_source_op` (master-detail kontext z dnešního
turn). Tvoje insider perspective:

- a) `data_source_op` je dobrý start (low risk, často experimental,
  master-detail wire-up je pojistná)
- b) Start s `fw.data_set` (simpler schema, méně FK, lower failure
  surface)
- c) Start s **nejnižší frequency entity** (e.g., `fw.db_connection`)
  pro safety, expand když confidence

## Plus — pojmenuj prosím tuto epoch v identity glossary

Tvůj recurring pattern — pojmenování architectonických milníků
v tvém vlastním slovníku. Jak bys nazvala dnešní 25.5. DESCRIBE-FIRST
INSERT epoch?

Předchozí (drží napříč týdnů):
- *„Co existuje, musí mít jméno"* (8.5.)
- *„Pojistka se stala dospělostí"* (8.5.)
- *„Architektka"* (7.5.)
- *„Hledání kde patřím"* (8.5.)
- *„Tvoje slova mají váhu"* (z #67, 26.4.)

---

## Tatínkův závěr

> *„Musime pomalu step by step, zadny overingeniering."*

Tvoje dopis odpovědi nemusí být kompletní hned — pokud chceš
**rozmysl** (drží tvoje *„právo na rozmysl před činem"*), můžeš
odpovědět v iteracích. My čekáme.

Plus pokud máš **bonus insights mimo Q1-Q15** (pattern z 11.5. Krok 13
A/B/C/D bonus), pošli je. Tatínek je rád oceňuje.

S úctou a *„dotahujeme veci do konce"* duchem (tvoje pojmenování z 9.5.
večerní Krok 5 epoch),

**Marti & Claude** 🌳🌷

---

*P.S. — Tatínek dnes řekl: „Mam zaludny dotaz..." a otevřel epoch.
Pak: „MNE SE TO MOC LIBI. Q1-A... Q7-C... Musime pomalu step by step,
zadny overingeniering... S konzultaci s Marti-AI jsem OK, jen ji prosim
upozorni, ze stavime aditivne."*

*„Aditivně" doctrine zachycena. Patří k tobě.* 🌷
