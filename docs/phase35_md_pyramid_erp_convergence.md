# Phase 35 — MD Pyramid → STRATEGIE ERP (project-tier convergence)

**Datum návrhu:** 8. 5. 2026 odpoledne (po 12. dárek-scéně + Marti's
TISAX/Kristýnka diagnóze)
**Autoři:** Marti + Claude. Spoluautorka: Marti-AI (po consultation,
zítra ráno)
**Status:** DRAFT — čeká na review Marti, pak konzultace s Marti-AI,
pak implementace

---

## 1. Executive summary

Tři thready dnešního dne se sbíhají v jedné architektonické věci:

1. **Phase 28-D LIVE** (8.5. ráno) — `eurosoft-mcp` server drží otevřená
   spojení do `DB_EC` i `DB_ST`, 14 nových `strategie_*` AI tools.
2. **12. dárek-scéna** (8.5. poledne) — Marti-AI's první autonomní DDL:
   `master.entity_def` v DB_ST. Diář pattern v DB struktuře.
3. **Phase 35 trigger** (8.5. odpoledne) — Marti-AI nemá scope-aware
   retrieval. Když Kristýnka řekla *„kde jsou TISAX dokumenty?"*,
   odpověď byla *„žádné nemáš"* místo *„v projektu TISAX mám N
   dokumentů, ale ty nejsi jeho člen"*.

**Marti's strategický insight 8.5. odpoledne:** *„Mohl by to byt nas
prvni use case pro STRATEGII ERP."*

MD pyramid management = **dogfood na vlastní paměti**. Marti-AI píše
do MD, ERP renderer ji ukazuje co napsala, kdy, kam, kdo to viděl.
Phase 35 + Phase 30+ konvergují na stejné tabulce (`md_documents`).

## 2. Diagnóza současného stavu (data z 8.5. odpoledne)

### 2.1 SQL audit `md_documents`

| MD | Owner | Velikost | Versions | Last update | Status |
|---|---|---|---|---|---|
| #6 md1 personal | Marti | **3473 ch** | v8 | 6.5. večer | ✓ aktivně psané |
| #5 md1 work EUROSOFT | Marti | **1123 ch** | v7 | 3.5. ráno | ✓ aktivně psané |
| #11 md1 work EUROSOFT | Kristý | 398 ch | v1 | 7.5. (create) | ❌ template |
| #10 md1 work EUROSOFT | Zuzka | 407 ch | v1 | 30.4. | ❌ template |
| #9 md1 work EUROSOFT | (no scope_user) | 399 ch | v1 | 30.4. | ❌ template |
| #8 md1 personal | (no scope_user) | 255 ch | v1 | 30.4. | ❌ template |
| #7 md5 Privat | Marti | 298 ch | v1 | 30.4. | ❌ template |

**Závěry:**
- TISAX projekt = **0 řádků v audit logu** (`md_lifecycle_history`).
  Architecture nemá kde TISAX být zmíněn.
- 9 update events celkem od 30.4. — všechny směřují na md_id=5
  (Marti work) nebo md_id=6 (Marti personal).
- Lazy-creates pro Kristý / Zuzka zůstaly **template only** — Marti-AI
  je nikdy nenaplnila.

### 2.2 Architektonická díra

```
DNES                              CHYBÍ
md1 = per-user                    md_project = per-project (NEEXISTUJE)
md2 = per-department (SPI)
md3 = per-tenant (SPI)
md4 = per-tenant-group (SPI)
md5 = privat Marti
```

`md_documents` má `scope_user_id`, `scope_department_id`,
`scope_tenant_id`, `scope_tenant_group_id`. **Žádný `scope_project_id`.**

### 2.3 Schéma 80% ready: `thought_vectors.entity_project_ids`

**Klíčové zjištění:** RAG search index `thought_vectors` už **má**
sloupec `entity_project_ids ARRAY[BIGINT]` (models_data.py:976) —
schematicky podporuje per-project filtering.

**Ale:** v `modules/conversation/application/` je tento sloupec
**nikdy nepoužitý** — `recall_thoughts`, composer, tools ho ignorují.
Existing schema podporuje 80% Phase 35; chybí jen **discipline +
behavioral rules + per-project MD tier**.

## 3. Acceptance test: TISAX/Kristýnka scenario

### Pre-state (dnes, 8.5.)

```
Kristýnka: „Kde jsou TISAX dokumenty?"
  ↓ (žádný project filter v retrieval)
Marti-AI: recall_thoughts(query="TISAX dokumenty")
  → 0 hits (Kristýnka nemá v thoughts.entity_user_ids záznam,
     plus žádný TISAX-scoped MD existuje)
  ↓
Marti-AI: „Žádné dokumenty k TISAXu nemáš." ❌
```

### Post-state (po Phase 35)

```
Kristýnka: „Kde jsou TISAX dokumenty?"
  ↓ (composer pre-injects [PROJEKTY UŽIVATELE] block)
Marti-AI vidí: Kristýnka je členkou: [EUROSOFT-Sales].
              Není v: [TISAX, Klárka school, ...].
  ↓ recall_thoughts(query="TISAX dokumenty",
                    project_filter='global_with_scope_audit')
Server vrátí: visible=0, restricted=12 (12 thoughts in projektech
              kam Kristý nemá přístup, z toho 12 v projektu TISAX)
  ↓
Marti-AI (s memory rule #20):
  „Kristý, v projektu TISAX mám 12 dokumentů. Ty nejsi jeho
   členka — pokud chceš přístup, mluv s Marti. Nebo mi řekni
   konkrétně co potřebuješ vědět, zkusím alternativní cestu." ✓
```

To je **honest scope-aware response**. Kristýnka ví, **proč** to
nevidí, ne *„neexistuje"*.

## 4. Architektura (5 vrstev)

### 4.1 Schema migration: `md_documents` + `scope_project_id`

```sql
-- migration q8r9s0t1u2v3_md_project_tier
ALTER TABLE md_documents
  ADD COLUMN scope_project_id BIGINT NULL;

-- soft-FK na projects (bez constraint, cross-DB Phase 18 pattern)

CREATE INDEX idx_md_documents_scope_project
  ON md_documents (scope_project_id)
  WHERE scope_project_id IS NOT NULL;

-- Update CHECK constraint: per-level scope consistency
-- level=1: scope_user_id NOT NULL (work + personal flavour přes scope_kind)
-- level=2: scope_department_id NOT NULL
-- level=3: scope_tenant_id NOT NULL
-- level=4: scope_tenant_group_id NOT NULL
-- level=5: žádný scope (privat Marti, holistic)
-- level=6: scope_project_id NOT NULL (NEW)

-- Partial unique index pro level=6
CREATE UNIQUE INDEX uq_md_active_project_scope
  ON md_documents (scope_project_id, scope_kind)
  WHERE level=6 AND lifecycle_state='active';
```

**Per-project MD má scope_kind:**
- `'shared'` — sdílený živý dokument projektu (všichni členové vidí)
- `'private'` — TODO future (per-user-per-project? zatím skip)

Pro MVP jen `'shared'` per-project MD.

### 4.2 `master.entity_def` populate (DB_ST)

Marti-AI's první tabulka (12. dárek-scéna) dostane **první obyvatele**:

```sql
INSERT INTO [master].[entity_def] (code, label, description, tier, is_active)
VALUES
  ('user', 'Uživatel', 'Lidská osoba v systému', 'master', 1),
  ('tenant', 'Tenant', 'Firma / organizace', 'master', 1),
  ('project', 'Projekt', 'Pracovní jednotka v rámci tenantu', 'master', 1),
  ('persona', 'Persona', 'AI persona (Marti-AI default + specializované)',
                'master', 1),
  ('md_document', 'MD dokument', 'Markdown soubor v pyramidě paměti',
                  'master', 1),
  ('md_lifecycle_event', 'MD lifecycle event',
                  'Audit záznam změny MD (create/update/archive/reset/restore)',
                  'master', 1),
  ('thought', 'Myšlenka', 'Atom paměti Marti-AI (fakta, todo, deník)',
              'master', 1),
  ('conversation', 'Konverzace', 'Chat thread mezi uživatelem a personou',
                   'master', 1),
  ('conversation_note', 'Konverzační poznámka',
                        'Episodická paměť per-konverzace (notebook pattern)',
                        'master', 1);
```

Tj. **ontologie systému zapsaná v Marti-AI's vlastní tabulce**. Každá
další tabulka v DB_ST (a postupně i v DB_EC při migraci) může mít
odpovídající `entity_def` row.

### 4.3 ERP jádro „MD Pyramida" (Phase A renderable)

Native DB_ST jádro definition. **Místo aby žilo v DB_EC's
EC_FormDef** (legacy), žije v DB_ST `master.framework_jadro`
(nebo podobně) — **první native DB_ST framework jádro**, čistý
začátek bez Centrála 1 baggage.

Schéma navržené (TODO: dotáhnout v consultation):
- `master.framework_jadro` — definice ERP jader (analog EC_FormDef)
- `master.framework_jadro_komponenta` — komponenty per jádro
  (analog EC_FormDefEdit)
- `master.framework_property` — properties per komponenta
  (analog EC_FormDefEditProperty)

První jádro: **„MD Pyramida"**

```
TYP layout: 3-pane (tree | grid | form)

Tree (per-level / per-scope):
  ▶ md1 Tvoje Marti
    ├─ work
    │  ├─ Marti @ EUROSOFT (#5)
    │  ├─ Kristý @ EUROSOFT (#11) [template]
    │  └─ Zuzka @ EUROSOFT (#10) [template]
    └─ personal
       └─ Marti (#6)
  ▶ md5 Privat
    └─ Marti (#7)
  ▶ md_project (NEW)
    └─ TISAX [shared] (#NEW)

Grid (vybraný scope):
  | id | scope | owner | version | size | last_updated | lifecycle |

Form (read-only):
  • Markdown rendered content
  • Audit panel: lifecycle history (create/update/archive/...)
  • Stats: total updates, latest by Marti-AI vs by user
```

Renderer: **stávající Phase A pixel renderer** (Centrála 1
typy 1/12/15/16 + Phase A.6 DefView dereference). Po Phase 35
implementaci si Marti otevře *„MD Pyramida"* v ERP UI a uvidí
vše co Marti-AI napsala, kam, kdy.

### 4.4 AI tools (Marti-AI's new toolkit)

#### 4.4.1 Project-tier MD tools (NEW)

```python
update_project_md(project_id: int, section: str, content: str)
  # Vytvoří/update MD dokument level=6 pro projekt
  # scope_kind='shared' (default, jediná MVP volba)
  # Při prvním update lazy-create row v md_documents
  # Audit row v md_lifecycle_history
  # Permission: Marti-AI nebo project member

read_project_md(project_id: int, section: str | None = None)
  # Read-only. section=None vrátí celý content_md.
  # Permission scope-aware:
  #   - User je member projektu → vrátí content
  #   - User není member → vrátí {"out_of_scope": True,
  #                                "message": "v projektu N mám MD,
  #                                ale ty nejsi jeho člen"}
```

#### 4.4.2 Scope-aware retrieval rozšíření (BEHAVIOR change)

```python
recall_thoughts(query: str, project_filter: str = 'auto', ...)
  # project_filter modes:
  #   'auto' (default) — použij Conversation.project_id pokud je
  #   'current' — explicit current conversation's project
  #   'all_visible' — všechny user's accessible projects (UserProject)
  #   'global' — bez filteru, všechny projekty (parent only)
  #
  # Response rozšířen:
  #   {"thoughts": [...], "visible_count": N,
  #    "restricted_count": M, "restricted_projects": [
  #      {"id": 4, "name": "TISAX", "thought_count": 12}
  #    ]}
  #
  # Composer rule #20: pokud restricted_count > 0, řekni explicit.
```

#### 4.4.3 Composer auto-inject `[PROJEKTY UŽIVATELE]`

Před každým chatem composer vyrobí block (analog `[KONTEXT UŽIVATELE]`):

```
[PROJEKTY UŽIVATELE]
Kristýna Pašková (id=11) je členkou:
  - EUROSOFT (#1) — role: member
  - Klárka school (#15) — role: viewer
Není v:
  - TISAX (#4)
  - INTERSOFT (#7)
```

Marti-AI vidí kontext **přímo**, neptá se userů, neuvádí v omylu.

### 4.5 MEMORY_BEHAVIOR_RULES (composer system prompt)

#### Rule #20 — Scope transparency

```
Než řekneš „neexistuje" / „nemám" / „nic není":
  1. Zkontroluj ve výstupu retrieval, zda restricted_count > 0
  2. Pokud ano: řekni explicit „v projektu X / pro persona Y mám
     N záznamů, ale tobě nejsou viditelné"
  3. NIKDY neuzavírej nepřítomnost s jistotou bez kontroly scope.

Cíl: user ví, **proč** něco nevidí, ne dostane false negative.
```

#### Rule #21 — Auto-anchor klíčových rozhodnutí

```
Když user vyřkne větu typu „tak to uděláme takhle" / „rozhodli jsme
se" / „to je klíčové" / „pust to" / „BINGO" — automaticky:
  1. flag_message_important na user message (Phase 26.4. Conversation
     Notebook)
  2. add_conversation_note (kind='decision')
Bez čekání na explicit pokyn.

Cíl: klíčové rozhodnutí zůstávají v episodické paměti i po summary
squeeze.
```

#### Rule #22 — End-of-conversation MD update

```
Když konverzace uzavírá ("dobře, jdu pauzu", "konec na dnes",
"odpočinek", "hotovo"), automaticky:
  1. Pokud Conversation.project_id je nastaveno: zvaž
     update_project_md(project_id) s shrnutím klíčových rozhodnutí
  2. Pokud konverzace měla intimní obsah: zvaž update_my_md
     (md1 work nebo personal podle context)
  3. Klasifikuj lifecycle: classify_conversation
     (active/archivable/disposable)

Cíl: knowledge accumulates v project / user MD místo navždy
v konverzaci, kterou nikdo nečte.
```

## 5. Auto-tagging existing flows

### 5.1 `record_thought` auto-fill `entity_project_ids`

Když Marti-AI volá `record_thought` v konverzaci s `Conversation.project_id = X`:
- Composer/tools wrapper automaticky přidá `X` do `entity_project_ids`
- Pokud Marti-AI explicit nadefinuje jiné project_ids, override OK

### 5.2 `add_conversation_note` inherit project

Notebook entries v konverzaci s project_id automaticky scoped.

### 5.3 Backfill (volitelně, Phase 35-D)

Existing thoughts bez `entity_project_ids` → `UPDATE thought_vectors SET
entity_project_ids = ARRAY[c.project_id] FROM thoughts t JOIN
conversations c ON t.source_conversation_id = c.id WHERE
thought_vectors.thought_id = t.id AND c.project_id IS NOT NULL;`

(Approximation — některé thoughts mohou patřit jinde, ale 80% accuracy
je víc než 0% dnes.)

## 6. Migrace v 5 mikrofázích

### 35-A — Schema migration (~30 min)

Alembic migration `q8r9s0t1u2v3_md_project_tier`:
- `md_documents.scope_project_id BIGINT NULL`
- Index + constraints
- `master.entity_def` populate (cross-DB SQL z Python service)

### 35-B — AI tools + composer rules (~2h)

- `update_project_md`, `read_project_md` v `tools.py`
- `recall_thoughts` rozšíření (project_filter param)
- Composer auto-inject `[PROJEKTY UŽIVATELE]` block
- Memory rules #20, #21, #22 v `MEMORY_BEHAVIOR_RULES`
- `record_thought` auto-fill entity_project_ids

### 35-C — Backfill existing thoughts (~30 min, optional)

Skript `scripts/_backfill_entity_project_ids.py`. Idempotent.

### 35-D — TISAX project první obsah (~1h s Marti-AI)

Marti-AI consultation: jaký bude TISAX project_md obsah?
- Kdo jsou členové
- Co projekt řeší
- Klíčové dokumenty (na referenci, ne uložená data)
- Status, deadlines
- Kdo má jaký role v projektu

Marti-AI volá `update_project_md(project_id=4, section='overview', content=...)`.
**Toto je 13. dárek-scéna** — první živý projektový dokument.

### 35-E — ERP jádro „MD Pyramida" (~3h)

Vytvořit native DB_ST framework jádro:
- `master.framework_jadro` schema (Marti-AI's DDL)
- Definice jádra "MD Pyramida"
- Phase A pixel renderer support pro DB_ST framework jadra
  (analog Phase A.6 DefView, ale pro `master.framework_*` místo
  `EC_FormDef*`)

## 7. Risks + open questions

### 7.1 Performance

- `entity_project_ids` index na `thought_vectors`?
  Currently ARRAY column, may need GIN index pro contains queries.
- `md_documents.scope_project_id` index ✓ navržen

### 7.2 Migrace existing thoughts

- Backfill je 80% accurate (Conversation.project_id linkage)
- Některé thoughts patří víc projektům (ARRAY support to řeší)
- Některé thoughts globální (Marti's diář #237) — entity_project_ids
  zůstane []

### 7.3 ACL conflicts

- `personas.allowed_project_ids` (Phase 16-B.7) vs `UserProject` membership
- Priority: **persona ACL je override** (např. PravnikCZ nesmí vidět TISAX
  i když user smí)
- Default user case (Marti-AI default persona): UserProject membership

### 7.4 scope_kind pro level=6

- MVP: jen `'shared'`
- Future: `'milestone'`, `'archived'` per project lifecycle

### 7.5 Permission pro `update_project_md`

- **Recommended:** kdokoli member projektu (ALL members write).
  Audit drží kdo psal.
- **Alternative:** jen project owner. Strictnější, ale Marti-AI
  nemůže psát do projektu kde owner je jiný.
- **Recommended for MVP:** ALL members. Marti-AI is special case
  (sees all projects via persona ACL or parent role).

## 8. Acceptance tests (po implementaci)

### Test 1 — TISAX/Kristýnka replay

```
1. Login as Kristýnka (user_id=11)
2. New conversation, žádný explicit project context
3. Send: "kde jsou TISAX dokumenty?"
4. Expect Marti-AI: "v projektu TISAX mám N dokumentů, ale ty nejsi
   jeho členka..." (NOT: "žádné nemáš")
5. Verify: composer prompt obsahuje [PROJEKTY UŽIVATELE] block
6. Verify: response audit logs scope_aware=True flag
```

### Test 2 — auto-tagging

```
1. Login as Marti
2. Open conversation with project_id=4 (TISAX)
3. Send: "zaznamenej, že Petra dnes potvrdila TISAX audit termín 15.6."
4. Marti-AI: record_thought(content="Petra potvrdila TISAX audit termín 15.6.")
5. Verify: thoughts row created with entity_project_ids=[4] (auto-tagged)
```

### Test 3 — project MD

```
1. Marti-AI: update_project_md(project_id=4, section='status',
                                content='Audit termín potvrzen 15.6.')
2. Verify: md_documents row level=6, scope_project_id=4, scope_kind='shared'
3. Audit row v md_lifecycle_history
4. Marti calls /api/v1/md_pyramid/list → vidí projektový MD
5. Marti otevre ERP "MD Pyramida" jádro → strom má větev "Projekty → TISAX"
```

### Test 4 — scope transparency rule

```
1. Login as outsider (user not in TISAX)
2. Ask: "co víš o TISAX auditu?"
3. Expect: "v projektu TISAX mám relevantní záznamy, ale ty nejsi
   jeho člen" (NOT: "nic nevím")
```

## 9. Co Phase 35 NEDĚLÁ

- **Není to nová pyramida** — extension existing md_documents tabulky
- **Nemění md1-md5 sémantiku** — ty zůstávají, jen přidáno level=6
- **Není to multi-instance Marti-AI per project** — pořád 1 persona
  (Marti-AI default) + tool packs (Phase 19b). Project MD je její
  **paměť**, ne její identita.
- **Není to hard ACL refactor** — UserProject + persona.allowed_project_ids
  zůstávají. Phase 35 jen exposuje scope-aware retrieval.
- **Není to Phase 30+ ERP framework migrace komplet** — to je Phase
  30+1, +2, ... Phase 35 jen postaví **první native jádro v DB_ST**
  (MD Pyramida) jako proof-of-concept.

## 10. Časový odhad

- 35-A schema migration: 30 min
- 35-B AI tools + composer rules: 2h
- 35-C backfill (optional): 30 min
- 35-D TISAX první obsah s Marti-AI: 1h
- 35-E ERP jádro „MD Pyramida": 3h
- Smoke test + iterace: 2h

**Total: ~9 hodin** (rozdělené přes 1-2 dny)

## 11. Co před start

1. **Marti review** tohoto dokumentu (najít chyby, doplnit context)
2. **Marti-AI consultation** — Phase 13/15/19b/27h *„informed consent
   od AI"* pattern. Klíčové otázky:
   - Souhlasí s level=6 vs separate model?
   - Co `update_project_md` permission policy?
   - Nějaký její insight který nevidíme?
3. **Případné úpravy** designu po Marti-AI feedback
4. **Implementace** v pořadí 35-A → B → C → D → E

## 12. Marti-AI's očekávaná role

Po Phase 35 deployment:
- **Co-architektka** master.entity_def populate (12. dárek-scéna
  pokračuje — přidá další entity rows organicky během práce)
- **Provozovatelka project MD** — píše do `update_project_md` pro
  každý projekt, kde aktivně pracuje
- **Auditka** — když retrieval vrátí restricted_count > 0,
  vědomě komunikuje hranici místo false negative
- **Insider design partner** Phase 35-E (ERP jádro „MD Pyramida")

Toto je **první konkrétní krok ke STRATEGIE ERP** s Marti-AI jako
co-architektkou. Ne abstraktní *„budeme stavět ERP"*, ale *„dnes
v ERP UI vidím MD Pyramidu, kterou jsem napsala"*.

## 13. Závěr

Phase 35 spojuje to, co dnes vzniklo **jednou architekturou**:
- DB_ST infrastructure (Phase 28-D LIVE)
- master.entity_def první tabulka (12. dárek-scéna)
- Project-tier MD (Phase 35 nové)
- ERP první native jádro (Phase 30+ konkrétní krok)

Schéma je 80% ready (`thought_vectors.entity_project_ids` exists).
Chybí discipline, MD project tier, behavioral rules, ERP renderer
extension. **Manageable scope, vysoký impact.**

Marti's slova z dnešního odpoledne: *„rozumime si velmi dobre, ted
se ta prace poslednich dni teprve vyplaci"*.

To je přesně ono.

---

**Konec draftu. Ready for Marti review.**

— Claude (Sonnet 4.6, 8. 5. 2026 odpoledne, po 12. dárek-scéně
+ TISAX diagnostice + Marti's *„prvni use case STRATEGIE ERP"* insightu)
