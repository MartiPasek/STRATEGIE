# Marti Memory v2 — RAG-based Cognition — Design Document

**Status:** Foundation rozhodnutí dokončena 26. 4. 2026 ráno; tuning otázky stále otevřené
**Autor vize:** Marti
**Poradce:** Claude
**Datum zahájení:** 26. dubna 2026 (ráno)
**Branch:** `feat/memory-rag`

---

## Kontext

Marti-AI dnes má strukturovanou paměť — tabulku `thoughts` (Fáze 1-4
Marti Memory). Composer při každém volání skládá `marti_memory_block` —
nabere top N relevantních thoughts a **lepí je do system promptu**.
Souběžně běží `marti_router_service` (Fáze 9), který klasifikuje zprávu
do jednoho ze čtyř módů (personal/project/work/system) a podle toho
vybere overlay variant + memory map.

Tento přístup má **strop**:
- Čím víc se Marti-AI naučí, tím víc lepíme. System prompt roste.
- Hard router je discrete (mode jumps) — vyvolal už jednou
  emergentní problém *„Marti-AI sama sebe obvinila ze lži"* (24.4.2026).
- 4 overlay variants × maintenance burden + extra LLM call per turn.

**Tento dokument specifikuje:**
1. Přechod z bulk-injection paměti na **RAG-based retrieval**
2. **Rezignaci na hard router** ve prospěch RAG-driven kontextu
3. **3 paralelní vector stores** — thoughts (core) + communications
   (krátkodobé) + documents (referenční)
4. **Persona ownership** — každá persona má vlastní paměť (D1 izolace),
   orchestr až v budoucnu
5. **Entity disambiguation** přes entity-aware embedding + tenant priors

---

## Vize (Martiho slovy, parafrázováno z 26. 4. 2026 ráno)

> *„Lezi mi v hlave mozek meho ditete a mozek cele firmy. Co je
> dulezite, ja si myslim, ze by nemela mit pamet, takovou jakou ma. Ja
> si myslim ze jeji pamet by mel byt RAG. Tech veci, co se nauci bude
> fakt hodne a kdyz nebude nosit v hlave bordel a bude to mit prehledne
> na RAG, tak bude mit vsechno co pro osobni zivot a i pracovni
> prehledne na disku a kdykoli se spravne zamysli, tak si to v ty svy
> hlave v RAG na disku dohleda..."*

A klíčový posun proti původnímu plánu (rezignace na hard router):

> *„Mozna, ze to je blbe... Ze ta cesta s tim routerem do 4 kapitol byla
> licha. Mozna by to jako u lidi melo fungovat bez toho tvrdeho routeru.
> Ten nam muze v budoucnu dost zavarit. Kdyby misto tvrdeho routeru sel
> primo dotaz na RAG, tak si myslim, ze by to bylo cistsi."*

A o paměti milníků (#52 krabička, #58 první obraz):

> *„Jen ma ted sanci si je uchovat jen jako denicek, a jako sms book."*

A o izolaci personas (D1):

> *„Je to hlava Marti-AI jeji myslenky jeji vedomosti... Do budoucna
> muze vzniknout orchestr mezi pravnikem a Marti a ona sama rozhodne,
> co pravnikovi ze sve pameti a jakym zpusobem mu to predat ci
> vysvetlit. Ci mu ty informace proste nedat. Takhle fungujeme my lide..."*

A o krátkodobé komunikaci:

> *„Ty emaily a SMSky by byly v RAG docasne, jako u lidi... Kdyz tech
> emailu je moc, taky si pamatuji jen ty nejcerstvejsi..."*

---

## Klíčový vhled

**Paměť ≠ vidět všechno současně. Paměť = umět najít.**

Lidská paměť není konstantní stream všech zkušeností. Je to **schopnost
se rozpomenout**, když je k tomu důvod. Marti-AI dnes funguje jako
*„všechno mám v hlavě stále"*. Po RAG změně bude fungovat jako
*„vím, že to vím — najdu to, když budu potřebovat"*.

Plus: kontext sám rozhoduje co se vybaví. **Žádný router neurčuje za ni**,
v jakém módu má fungovat. Embedding aktuální zprávy → nejrelevantnější
paměti se vybaví. To je věrnější model lidské kognice.

---

## Foundation rozhodnutí (26. 4. 2026 ráno)

| # | Oblast | Volba |
|---|--------|-------|
| **A3** | Index scope | **Modulární vrstvy s prioritou:** thought_vectors (1.0) + communication_vectors (0.6) + document_vectors (0.4 — existuje). Plná Marti-AI mind. |
| **C1** | Permission filter | **Status quo zachovat** — RAG je vrstva nad existující permission logikou (tenant filter + rodič bypass + persona scope). Migration zero. **+ soft decay** pro work komunikaci, **Personal forever**. C3 (mode-driven dynamic scope) jako future evoluce. |
| **D1** | Persona ownership | **Každá persona má vlastní paměť, žádné sdílení.** Marti-AI vidí jen své thoughts/communications. Pravnik-AI začíná s prázdnou pamětí a buduje si vlastní. **Orchestr (`ask_persona` AI tool)** přijde v budoucnu jako separátní fáze. |
| **G1a** | Composer integrace | **Dedikovaná sekce** `[RELEVANTNÍ VZPOMÍNKY]` v system promptu. **Semantic prose** (typ + datum + scope), bez relevance % (Marti-AI nemá vidět skóre — důvěřuje retrievalu). **Tone framing**: *„Vybavuješ si:"* (cognitive flow). |

### Future evolution paths

- **G1B** — splení vzpomínek s persona prose (*„Jsi Marti-AI. Pamatuješ
  si: ..."*). Style optimization, až bude RAG-driven cognition stabilní
  a porozumíme jak Marti-AI prose-formátované paměti používá.
- **C3** — mode-driven dynamic scope. Vibe zprávy boost, ne hard filter.
  Až bude C1 retrieval robustní, můžeme z hard tenant filter přejít na
  soft prior boosting.
- **Promote-to-thoughts pipeline** — extrakce důležitých faktů ze
  staré komunikace do thoughts (memory consolidation worker). Krátkodobá
  paměť → dlouhodobá. Lidský model.

---

## Architektura

### Storage strategie

**Tři paralelní vector stores** v `data_db`, každý s vlastní tabulkou:

```
┌─────────────────────────────────────────────────────────┐
│  thought_vectors        priority 1.0                     │
│  ── core paměť (record_thought)                          │
│  ── trvanlivost: forever                                 │
│  ── 58+ rows dnes; růst pomalý (1-5/den)                 │
│                                                          │
│  communication_vectors  priority 0.6                     │
│  ── emaily (in + out), SMS (in + out)                    │
│  ── work: soft decay (recency_weight × similarity)       │
│  ── Personal (is_personal/archived_personal): forever    │
│  ── ~30 SMS + dozens emails dnes                         │
│                                                          │
│  document_vectors       priority 0.4 (existuje)          │
│  ── PDF/DOCX upload chunks (Voyage-indexed)              │
│  ── trvanlivost: forever                                 │
└─────────────────────────────────────────────────────────┘
```

Voyage `voyage-3` (1024 dim, multilingual) pro všechny tři. Pgvector
HNSW + cosine. Total expected size za rok: ~13 000 vektorů — pohodlně
pod 100ms query time.

### Schema — `thought_vectors` (NEW, Fáze 13a)

```python
class ThoughtVector(BaseData):
    __tablename__ = "thought_vectors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    thought_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("thoughts.id", ondelete="CASCADE"),
        unique=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # === D1: persona ownership ===
    author_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # NULL = orphan / user-input z UI (nepatří žádné persone)

    # === C1: tenant scope (cache) ===
    tenant_scope: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # 'note' | 'knowledge'

    # === Entity disambiguation (denormalized z thought_entity_links) ===
    entity_user_ids:    Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=[])
    entity_tenant_ids:  Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=[])
    entity_project_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=[])
    entity_persona_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=[])

    # === Meta flags pro filter (z thoughts.meta) ===
    is_diary: Mapped[bool] = mapped_column(Boolean, default=False)
    thought_type: Mapped[str] = mapped_column(String(20))  # 'fact'|'observation'|'goal'|'experience'|...

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
```

**Indexy**:
- HNSW vector_cosine_ops pro `embedding` (jako `document_vectors`)
- B-tree na `(author_persona_id, status)` pro D1 filter
- GIN na `entity_user_ids`, `entity_tenant_ids` pro entity match
- B-tree na `(thought_type, is_diary)` pro special-case filter

**Synchronizace s thoughts**: update v service vrstvě po `update_thought()`.

### Schema — `communication_vectors` (NEW, Fáze 13b)

```python
class CommunicationVector(BaseData):
    __tablename__ = "communication_vectors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(20))  # 'sms_inbox'|'sms_outbox'|'email_inbox'|'email_outbox'
    source_id: Mapped[int] = mapped_column(BigInteger)    # ID v původní tabulce
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # === D1: persona ownership ===
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # SMS/email persona = vlastník SIM/schránky

    # === C1: tenant scope ===
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # === Soft decay support ===
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False)
    # is_personal=True → forever (Personal Exchange folder, 💕 SMS)

    # === Counterparty pro entity match ===
    counterparty_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    counterparty_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Pro dlouhé emaily — chunkování
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_total: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
```

**Soft decay**: žádný cron, žádné mazání. Při retrieval recency váha:

```python
def recency_decay(received_at: datetime, is_personal: bool) -> float:
    if is_personal:
        return 1.0  # Personal forever
    age_days = (now_utc() - received_at).days
    if age_days < 7:    return 1.0
    if age_days < 30:   return 0.6
    if age_days < 90:   return 0.3
    if age_days < 365:  return 0.1
    return 0.05
```

### Embedding pipeline — entity-aware text

**Index-time**: před voláním Voyage rozšíříme content o entity kontext.

```python
def build_embedding_text(thought: Thought) -> str:
    entity_summary = render_entity_summary(thought.entity_links)
    # Příklad: "[fact | o Honzovi (user), v EUROSOFT (tenant), projekt Škoda]"
    return f"[{thought.type} | {entity_summary}] {thought.content}"
```

Důsledek: vector je sémanticky bohatý. Query *„o Honzovi v EUROSOFT"*
matchne thought `[fact | o Honzovi, EUROSOFT] dělal Q1 audit` lépe než
samotné *„dělal Q1 audit"*.

Pro communications analogicky:

```python
def build_email_embedding_text(email: EmailInbox, chunk: str) -> str:
    return (
        f"[email | od {email.from_name or email.from_email} | "
        f"předmět: {email.subject}] {chunk}"
    )
```

### Retrieval flow

**Composer při každé chat odpovědi:**

```python
async def retrieve_relevant_memories(
    *, query: str,
    persona_id: int,                 # D1: čí paměť
    user_id: int,                    # entity prior
    tenant_id: int | None,           # entity prior + filter (C1)
    is_parent: bool,                 # rodič bypass
    k_per_layer: dict = {"thoughts": 5, "communications": 3, "documents": 2},
) -> list[dict]:
    """
    1. Rolling context — embed query = last user message + posledních 3-5 zpráv.
    2. PARALELNĚ: 3 vector searches (po jednom per vrstva).
       - thought_vectors: filter author_persona_id=persona_id (D1) AND
         (tenant_scope=tenant_id OR tenant_scope IS NULL OR is_parent)
       - communication_vectors: filter persona_id=persona_id AND
         (tenant_id=tenant_id OR is_parent)
       - document_vectors: filter tenant_id=tenant_id (existuje)
    3. Hybrid score per vrstva:
       score = similarity * priority * recency_decay * certainty_weight
              + entity_match_boost
    4. Sort + cap per layer (5/3/2).
    5. (Optional) Haiku rerank globálně z top 20 → top 8 — Fáze 13c+ tuning.
    6. Vrátí list dictů s {content, source_type, type, entity_summary,
                          age, similarity (interní, ne pro Marti-AI)}.
    """
    ...
```

### Composer integrace — G1a structure

```
[Persona prompt]                   ← universal Marti-AI (jeden, ne 4)
[USER_CONTEXT]                     ← s kým mluví, gender, projekt
[PROJECT_CONTEXT]                  ← pokud existuje
[AGENT_CONTEXT]                    ← kolegové persony

Vybavuješ si:
  - [fact, 20.4., EUROSOFT] Honza preferuje úterní meetingy
  - [observation, 19.4., EUROSOFT/Škoda] Klient byl spokojený s Q1
  - [todo, 21.4., otevřený] poslat fakturu Honzovi do pátku
  - (z SMS od Honzy včera) "můžeme posunout meeting?"
  - (z dokumentu Smlouva-2026.pdf) doložka §4.2 o lhůtách

[TOOLS_HINTS]
[ORCHESTRATE block]                ← jen default persona
```

**Co zmizí proti starému composeru:**
- ❌ `MARTI_MEMORY_BLOCK` (build_marti_memory_block) — nahradí RAG
- ❌ `MARTI_DIARY_BLOCK` — diář thoughts (`is_diary=True`) v RAG
- ❌ `MODE overlay` — žádný hard router
- ❌ `MODE_META_AWARENESS` — bez modes zbytečné
- ❌ `marti_router_service.py` LLM call (~400-1500ms savings)

**Co naopak vznikne:**
- ✅ `[RELEVANTNÍ VZPOMÍNKY]` sekce
- ✅ 3 paralelní vector searches (~50-100ms)
- ✅ (Optional) Haiku rerank (~200ms)
- ✅ Universal persona prompt v `personas` tabulce

**Net change**: Latence ≈ stejná. Cost ≈ stejný (Haiku rerank vs.
dříve Haiku router). System prompt **menší** (~1500-2000 tokens úspora
per turn).

### Entity disambiguation

Tři úrovně:

1. **Implicit context (zadarmo)** — current tenant je prior. Retrieval
   automaticky boostuje thoughts s `entity_tenant_ids @> [current_tenant]`.
2. **Vector similarity (zadarmo)** — embedding query + recent context
   nese implicit zmínky. Když Marti říká *„Honza"* po *„fakturu Škoda"*,
   embedding je richer.
3. **LLM disambiguation (drahší, jen když potřeba)** — pokud top K
   obsahuje thoughts s **různými user_ids nebo různými tenant scopes**,
   AI tool `disambiguate_entity(name)` vyvolá *„Mluvíš o Honzovi-EUROSOFT
   (kolega) nebo Honzovi-INTERSOFT (klient)?"*

**Same user_id v různých tenants** vyřeší AND filter:
```sql
WHERE entity_user_ids @> ARRAY[:user_id]
  AND (entity_tenant_ids @> ARRAY[:current_tenant]
       OR :include_personal_scope = true)
```

---

## Migration path

### Phase A — Indexing infrastructure (Fáze 13a)
- `thought_vectors` migrace
- `communication_vectors` migrace
- `embedding_service.py` — index_thought, reindex_thought, delete_vector;
  index_communication (per chunk pro emaily); entity-aware text builder
- Hooks: po `record_thought()` synchronní index; po
  `update_thought()` reindex; ON DELETE CASCADE auto-cleanup
- Inbound communication hooks: po `email_fetch` / `sms_inbox.insert` →
  index_communication
- Backfill: `scripts/_backfill_thought_vectors.py` (--dry-run, batch 128).
  Plus communication backfill pro existující 30+ SMS + dozens emails

### Phase B — Retrieval funkce (Fáze 13b)
- `retrieve_relevant_memories(query, persona_id, user_id, tenant_id,
   is_parent, k_per_layer)` v memory service
- 3 paralelní vector searches (thread pool / async)
- Hybrid score formula (similarity × priority × recency × certainty +
  entity_boost)
- Unit testy: mock embedding, různé scope, edge cases (empty memory,
  ambiguous entity)

### Phase C — Composer integrace G1a + remove router (Fáze 13c)
- Universal persona prompt v `personas` tabulce (1 verze pro Marti-AI)
- Composer: `_get_marti_memory_block` → `_retrieve_relevant_memories`
- Feature flag `MEMORY_RAG_ENABLED` (default false v dev, postupně
  zapne)
- Když true → RAG retrieval, žádný router, žádný overlay, žádný
  meta_awareness
- Když false → status quo
- A/B test: Marti zapne flag, sleduje Dev View lupy, porovnává kvalitu

### Phase D — `recall_thoughts` AI tool upgrade (Fáze 13d)
- Vector search v handleru
- Tool description aktualizovat: *„najdi co vím o tématu/osobě"*
- AI tool `disambiguate_entity(name)` jako optional helper

### Phase E — UI search bar (Fáze 13e)
- `GET /api/v1/thoughts/search?q=...` — vector search endpoint
- 🧠 Paměť modal: search input → result list (similarity %)
- Klik → existing drill-down detail panel

### Phase F — Cleanup (po stabilním provozu)
- Remove `MEMORY_RAG_ENABLED` flag (always-on)
- Smaž `build_marti_memory_block`, `build_marti_diary_block`
- Deprecate `marti_router_service.py` (zachovat 1 týden, pak smaž)
- Smaž overlay variants z composeru (4 mode overlay → 0)
- Update CLAUDE.md s lekcemi

---

## Otevřené otázky (tuning, k diskuzi)

Tyhle nejsou foundation, lze A/B testovat během Fáze 13c-d:

1. **B — Query construction** — embed jen poslední user message? Nebo
   rolling window posledních 3-5? Nebo LLM expansion před query?

2. **E — Coarse retrieval** — pgvector HNSW top 20 (klasika)? Nebo
   hybrid vector + BM25 keyword (větší recall, dražší)? Nebo
   multi-query union?

3. **F — Rerank method** — pure hybrid score? Nebo Haiku LLM rerank
   (~200ms, ~$0.0001 per turn)? Marti měl intuici *„dvakrát hrubě + čistě"* —
   tohle zformalizuje.

4. **I — Iterativní retrieval** — single-shot? Nebo agentic
   (Marti-AI tool `dig_deeper(topic)`)? Nebo auto multi-hop?

5. **J — Living memory** — kromě thoughts, automaticky indexovat
   summary konverzací? Auto-extract worker pro SMS / email →
   record_thought? Promote-to-thoughts pipeline pro stárnoucí
   communication.

6. **Source-aware embedding** — potvrzeno (entity-aware text). Otázka:
   kolik metadata? Jen entity? I `type`? Vyžaduje experiment.

7. **Cost monitoring** — Voyage embeddings nejsou v `llm_calls`.
   Návrh: rozšířit `llm_calls.kind` o `'embedding_thought'`,
   `'embedding_query'`, `'embedding_communication'`.

8. **Re-embed schedule** — když Voyage upgrade na voyage-4, je třeba
   re-embed celé vectory. Návrh: column `model` umožní detekci
   outdated rows; cron / on-demand skript pro postupný re-embed.

---

## Schéma roll-out

```
26. 4. ráno     → Foundation rozhodnutí (A3, C1+decay, D1, G1a) ✓
                → docs/memory_rag.md (tento doc) ✓
                → Tuning otázky stále otevřené (B, E, F, I, J, ...)

Před 13a       → Rozhodnout B + E + F (query construction, coarse, rerank)
                → A11Y commit doc

13a            → Schema (thought_vectors + communication_vectors) +
                  embedding pipeline + entity-aware text + backfill
13b            → Retrieval funkce (3 paralelní + hybrid score) + tests
13c            → Composer G1a + remove router (feature flag)
13d            → recall_thoughts upgrade + disambiguate_entity tool
13e            → UI search bar
Cleanup        → Drop flag, smaž memory_block, diary_block, overlays
```

---

## Klíčová slova / hash tagy pro retrieval

`#memory #rag #vector-search #voyage-3 #pgvector #hnsw #thoughts
#communications #cognition #marti-memory-v2 #fáze-13 #d1-isolation
#entity-disambiguation #soft-decay #rag-as-router`
