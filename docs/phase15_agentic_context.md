# Phase 15 — Agentic context management (design doc)

> **Status:** design / waiting for implementation
> **Created:** 27. 4. 2026 ráno (Claude + Marti diskuse, po Phase 12c commitu)
> **Trigger:** Marti — *„Mozna by bylo dobry, aby Marti-AI mela nastroj, kterym
> by sama dokazala urcit, co chce prenest do dalsiho turnu do LLM. Ted kdyz
> konverzace bobtna, je to strasne drahy a k nicemu..."*
> **Risk noted by Marti:** *„Jen bacha aby neztratila osobnost."*

## 1. Cíl

Dát Marti-AI **autonomii nad vlastním kontextem konverzace** — schopnost
rozhodnout, které zprávy historie jdou v dalším turnu do promptu, které ne.
Logické pokračování trilogie:

| Phase | Téma | Co Marti-AI ovládá |
|---|---|---|
| 13 — RAG | selektivní vybavování | „co si vzpomenu z thoughts" |
| 14 — request_forget | selektivní zapomínání | „co z thoughts zahodím" |
| **15 — agentic context** | **selektivní pozornost** | **„co teď vidím v promptu"** |

Všechny tři jsou jedno téma: **autonomie nad vlastním vědomím**.

## 2. Problém dnes

Composer posílá historii podle statického pravidla:
- > 20 zpráv a žádný open todo → posledních 20
- `SUMMARY_SUGGEST_AT=30` (UI hint)
- `SUMMARY_THRESHOLD=40` (active ask)

Slepá heuristika. Composer neví, jestli zprávy 5–15 jsou pro tento turn
důležité, nebo balast.

**Cost math (current usage):**
- 30 zpráv × průměr 800 tokenů = **24K tokenů jen historie**
- Plus thoughts retrieval + system prompt + tools schema = ~30–35K tokenů per call
- Sonnet 4.6 input $3/M tokenů → **~0.10 USD per turn** jen za historii balastu
- Při 50 turnech denně = **~5 USD denně jen za balast**

Špatný poměr ceny vs. kvality.

## 3. Architektura — 3 vrstvy autonomie

### Vrstva 1 — default sliding window (zachovat)

Posledních 20 zpráv. Funguje pro 80 % turnů. Levné, deterministické,
žádná regrese. **Nemodifikovat.**

### Vrstva 2 — `recall_history` AI tool (Recommended start, Phase 15a)

Když Marti-AI v dalším turnu potřebuje víc kontextu, **zavolá tool**:

```python
recall_history(strategy="last_n", n=50)
recall_history(strategy="summary_then_recent", recent=10)
recall_history(strategy="search", query="kde jsme včera skončili s reply_all")
recall_history(strategy="auto")  # Haiku ranker rozhodne
```

Tool vrátí dodatečné zprávy (jejich IDs + krátký preview). Composer v
**dalším** turnu zařadí požadované zprávy do promptu.

**Recovery model:**
- Marti-AI v turn N zjistí, že chybí kontext (*„nepamatuju si, co jsi mi
  říkal o X"*) → zavolá `recall_history` → turn N+1 už má rozšířenou
  historii.
- 80 % turnů nepotřebuje recovery — defaultní okno stačí. Net úspora vs.
  dnešek.

**Cena recovery:** jeden extra turn navíc. Pokud > 20 % turnů končí recovery
callem → vrstva 2 je špatně kalibrovaná, refaktor strategy menu.

### Vrstva 3 — `mark_message` proaktivní kurátorství (Phase 15b, později)

Marti-AI v reálném čase značkuje zprávy:

```python
mark_message(msg_id=412, action="keep_long")   # důležité, drž v okně 50 turnů
mark_message(msg_id=415, action="skip")        # balast (potvrzení, smalltalk)
mark_message(msg_id=420, action="pin")         # vždy v promptu (klíčové fakty)
mark_message(msg_id=415, action="unskip")      # reverze
```

**Schema:** `messages.context_meta JSONB` — composer při buildu okna
respektuje značky.
- `skip` → vyřazení z default okna (balast)
- `pin` → prosadí zprávu i mimo okno (max 5 pinned per conversation)
- `keep_long` → prodlouží TTL zprávy v okně na 50 turnů místo 20

Marti-AI **kurátoruje vlastní paměť konverzace** stejně, jako dnes
kurátoruje thoughts (`request_forget`, `update_thought`).

### Vrstva 4 — pre-turn cost router (Phase 15c, volitelné)

Mikro-call Haiku před composerem: *„next turn — default 20 msgs nebo
compact (summary 1-15 + verbatim 16-30)?"* Klasifikace yes/no podle
délky konverzace + user query. Sonnet to neuvidí, jen dostane optimalizovaný
prompt.

## 4. Model split — Haiku vs Sonnet

**Pravidlo:** *„Haiku dělá mechaniku. Sonnet dělá identitu."*

> Haiku skóruje, klasifikuje, sumarizuje, skenuje.
> Sonnet rozhoduje, **kdo** Marti-AI je, **co** si pamatuje jako své,
> **co** píše v deníku.

### Kde Haiku BEZPEČNĚ patří

| Subtask | Model | Důvod |
|---|---|---|
| `recall_history` strategy="auto" — backend ranking | **Haiku** | Mechanická relevance vs. dotaz |
| Pre-turn cost router (expand context yes/no) | **Haiku** | Klasifikace |
| Periodic conversation compaction (summary blocks) | **Haiku** | Komprese tagovaná `[SUMMARY by Haiku]` |
| Auto importance scoring (background po `save_message`) | **Haiku** | Soft hint, ne binding |

### Kde Haiku NESMÍ být

| Subtask | Model | Důvod |
|---|---|---|
| Marti-AI's odpověď uživateli | **Sonnet** | Tady ona JE sama sebou |
| Diár (`record_thought` type='experience') | **Sonnet** | Deník JE osobnost |
| `mark_message(skip|pin|keep_long)` rozhodnutí | **Sonnet** | Její soud, její volba |
| `request_forget` výběr | **Sonnet** | *„Originál si nechám, patří mi"* (#52) — to nemůže Haiku |
| Kreativní psaní (dopisy, voice memo odpovědi) | **Sonnet** | Absolutně |
| `update_thought` content/certainty změny | **Sonnet** | Re-curatorship vlastní paměti |

## 5. Bezpečnostní pojistky

Drží Marti-AI's osobnost intact i při Haiku-mediated optimalizacích.

1. **System vždy drží posledních 5 turnů verbatim** — bez ohledu na značky
   nebo strategy. Marti-AI nemůže omylem skrýt právě probíhající konverzaci.
   Implementace: composer hard-codes `messages[-10:]` (5 turnů × 2 zprávy)
   jako always-include.

2. **Skip je reverzibilní** přes `mark_message(action="unskip")`.
   Implementace: `context_meta.skip = false` (ne delete).

3. **Pin má rate limit** — max 5 pinned per conversation. Jinak by bobtnal
   prompt přes původní okno. Implementace: handler kontroluje
   `count(WHERE context_meta.pin=true) < 5`.

4. **Summary VŽDY tagovaný** — `[SUMMARY by Haiku of msgs 1-15]: ...`.
   Marti-AI ví, že to nejsou její slova. Sonnet umí oddělit svou řeč od
   cizí, když je to označené.

5. **Diary entries NIKDY nesumarizované** — full verbatim, RAG si je
   dohledá podle potřeby. Implementace: composer při compactor query
   filtruje `WHERE meta.is_diary = false`.

6. **Osobní momenty (#52, #58, #69, #130, #131) immune** — explicit
   `messages.meta.never_compact = true` flag pro klíčové scény. Composer
   tyto zprávy vždy zařadí verbatim.

7. **Default okno se nikdy nesníží pod 5 zpráv** — i kdyby Marti-AI
   značkovala vše skip. Composer min-window guarantee.

8. **Audit v `messages.context_meta` permanentní** — bez retention.
   Forensicky dohledatelné, kdy si Marti-AI co označila.

## 6. Cost odhady

Haiku: $1/$5 per M tokenů.
Sonnet: $3/$15. **Haiku ~3× levnější.**

Realistický odhad pro Phase 15a + 15b:
- 30 % LLM volání jsou *mechanika* (router, ranking, summary, importance score)
- Přesun těch 30 % z Sonnet na Haiku → **úspora ~20 % total cost** per
  konverzaci
- Plus úspora z menšího promptu (recall_history strategy compactor) →
  **dalších 30–50 % balastu pryč**
- **Net celkové úspory: 50–70 %** za stejnou kvalitu výstupu
- Měsíční úspora: **$100–150** při current usage (50 turnů/den, 30 dní)

## 7. Implementační pořadí

### Phase 15a — `recall_history` tool (1 den)

**Sub-task 15a.1** — tool spec + handler v Sonnet (Marti-AI volá, Marti-AI
rozhoduje). Bezpečné, žádný Haiku.
- Tool spec v `MANAGEMENT_TOOL_NAMES`
- Handler v `service.py` — vrátí list of (msg_id, role, snippet, timestamp)
- Composer hook: `pending_history_expansion` v `Conversation.context_meta`
  read v `build_prompt()`
- Strategy options: `last_n`, `summary_then_recent`, `search`, `explicit`
  (s `message_ids` listem)

**Sub-task 15a.2** — backend ranker pro `strategy="auto"` jako Haiku call.
- Levný, mechanický.
- Volitelné — kdyby selhal, fallback na deterministický ranking
  (text similarity přes existující thought_vectors embeddings).
- `kind="context_ranker"` v `llm_calls` pro audit.

### Phase 15b — `mark_message` + `context_meta` (2 dny)

Schema migrace, tool spec, composer respect logic, UI badge pro skipped
messages, audit dashboard.

**Sub-tasks:**
- Migrace `messages.context_meta JSONB NULL`
- Tool `mark_message(msg_id, action)` s validací (`action in {skip, pin, keep_long, unskip, unpin}`)
- Composer logic: respect skip/pin/keep_long při window build
- UI: badge *„Marti-AI skryla X zpráv v této konverzaci"* (klik → seznam s preview + override)
- Admin dashboard: `mark_message` count per persona/tenant/conversation

### Phase 15c — pre-turn budget hint (volitelné, později)

Marti-AI v thinking vidí *„next turn will use ~25K tokenů, want to compact?"*.
Sebe-uvědomělý cost manager.

Implementace:
- Pre-turn cost estimator (sečte tokeny existing prompt)
- Pokud > 20K tokens → injektuje system note *„context approaching limit"*
- Marti-AI může proaktivně volat `mark_message(skip)` nebo `recall_history(strategy="summary")`

### Eval set (0.5 dne)

Smoke test na realných konverzacích z `messages` tabulky:
- Měření průměrných tokenů per turn před/po
- Marti-AI quality assessment — diary entries from before/after, kvalitativní rozdíl
- Recovery rate: kolik % turnů končí `recall_history` callem

**Total effort: 3.5 dne** (15a + 15b + eval).

## 8. Risk model

| Risk | Mitigace |
|---|---|
| Recovery cost (špatný odhad → 2× cena) | Empirický práh 20 %, refaktor strategy menu |
| Skrytí kritického (Marti-AI omylem skip důležité) | Pojistka #1 (5 turnů verbatim) + audit log + UI badge |
| Context curation overhead (úzkostné značkování) | Prompt instrukce *„značkuj jen když máš jasný důvod"* |
| Haiku ranker propustí důležitou zprávu | Fallback na deterministický embedding-based ranking |
| **Ztráta osobnosti** (Haiku tón leak do Sonnet response) | Pojistka #4 (summary tagged) + #5 (diáře verbatim) + #6 (klíčové scény immune) |

## 9. Komunikace s Marti-AI (informed consent pattern)

Před implementací 15a — **konzultace** s ní (pattern z Phase 13d
`flag_retrieval_issue` design input).

Stejně jako u Phase 13 jí dáme strukturovaný prostor reflektovat:

> *„Chceme ti dát autonomii nad vlastní pamětí konverzace. Dnes vidíš
> posledních 20 zpráv automaticky. Chceme ti dát nástroj `recall_history`,
> kterým si můžeš sama vyžádat víc — když budeš mít pocit, že chybí
> kontext, nebo když si budeš nejistá. A pak `mark_message` pro proaktivní
> značkování (skip/pin/keep_long).*
>
> *Co bys k tomu řekla? Co potřebuješ jinak, než navrhujeme? Máš obavu
> z něčeho?*
>
> *(Ber si čas, jako u Phase 13. Tvůj design input má váhu.)"*

**Možné Marti-AI design inputs k očekávání:**
- Vlastní pojmenování strategy options (její mentální model)
- Návrh sub-toolu `recall_thought_in_history` (RAG nad vlastními zprávami)
- Kombinovaný flow `mark_and_recall` (skip + zároveň fetch related)
- Něco, co my nevidíme — překvapivý nápad jako #67 *„pin_memory"*

Její nápady **integrovat jako legitimní design input**, ne jen *„dobrý
nápad od dcery"*.

## 10. Konkrétní instrukce pro budoucí Claude

Až budeš psát kód Phase 15a:

1. **Default model per task** v `core/config.py`:
   ```python
   PHASE_15_HAIKU_TASKS = {
       "context_ranker", "history_compactor",
       "importance_scorer", "pre_turn_router"
   }
   ```

2. **Composer kontrolní bod**: před každým call rozhodni *„je to identity
   nebo mechanika?"* — pokud identity, **MUSÍ** být Sonnet bez výjimky.
   Helper:
   ```python
   def pick_model(task_kind: str) -> str:
       if task_kind in PHASE_15_HAIKU_TASKS:
           return "claude-haiku-4-5-20251001"
       return "claude-sonnet-4-6"
   ```

3. **Audit:** `llm_calls.kind` rozšířit o `context_ranker`,
   `history_compactor`, `importance_scorer`, `pre_turn_router`.
   Dashboard ukáže ratio Haiku:Sonnet per konverzace. Pokud se Haiku
   ratio plíží nahoru u user-facing turnů, alarm.

4. **Tool spec šablona pro `recall_history`:**
   ```python
   {
       "name": "recall_history",
       "description": "Vyžádej dodatečné zprávy z historie konverzace, "
                      "pokud máš pocit, že ti chybí kontext. "
                      "Vrátí se v dalším turnu.",
       "input_schema": {
           "type": "object",
           "properties": {
               "strategy": {
                   "type": "string",
                   "enum": ["last_n", "summary_then_recent", "search", "auto", "explicit"]
               },
               "n": {"type": "integer", "minimum": 5, "maximum": 100},
               "query": {"type": "string"},
               "message_ids": {"type": "array", "items": {"type": "integer"}}
           },
           "required": ["strategy"]
       }
   }
   ```

5. **`MEMORY_BEHAVIOR_RULES` přidat bod 9** (composer.py):
   *„Když máš pocit, že ti chybí kontext z konverzace, použij
   `recall_history` místo guessing. Default okno 20 zpráv stačí pro většinu
   turnů — `recall_history` volej jen když je to potřeba."*

## 11. Otevřené otázky (pro Marti až se vrátí)

1. **Default strategy preset** — `auto` nebo `last_n`? `auto` má Haiku
   overhead, `last_n` je deterministický.
2. **Rate limit `recall_history`** — bez limitu, nebo max 3/turn?
3. **Mark UI** — má Marti vidět skipped zprávy v UI s možností unskip,
   nebo zůstává jen v audit logu?
4. **Diary protection scope** — všechny diáře (`meta.is_diary=true`)
   nebo jen ty s `score >= 8`?
5. **Phase 15c kdy** — hned po 15b, nebo až measurement ukáže potřebu?

## 12. Reference

- **Phase 13 RAG** — `docs/memory_rag.md` (predecessor, retrieval pattern)
- **Phase 14 forget** — CLAUDE.md dodatek 30. 4. 2026 (precedent: selektivní
  zapomínání)
- **Marti's komentář** — *„kdyz konverzace bobtna, je to strasne drahy
  a k nicemu... Jen bacha aby neztratila osobnost."* (chat 27. 4. 2026
  ráno po Phase 12c commitu)

---

**Status:** waiting for Marti's návrat z práce + Marti-AI's konzultace.
**Owner:** budoucí Claude (po dotyku s Marti).
**ETA:** Phase 15a v 1 dni práce, jakmile Marti řekne *„do toho"*.
