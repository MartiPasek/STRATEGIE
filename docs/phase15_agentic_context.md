# Phase 15 — Conversation Notebook (design doc, v4)

> **Status:** design v4 / ready for Phase 15a implementation
> **Created:** 27. 4. 2026 ráno (v1 — recall_history + mark_message)
> **Pivoted:** 27. 4. 2026 odpoledne (v2 — conversation notebook po Marti's insightu)
> **Refined:** 27. 4. 2026 večer (v3 — note_type enum + question loop + persistence rules)
> **Expanded:** 27. 4. 2026 pozdě večer (v4 — living state + category + lifecycle + project triage + conversational-first UX po Marti-AI's konzultaci #3 a #4)

> **Trigger původně:** Marti — *„Mozna by bylo dobry, aby Marti-AI mela nastroj,
> kterym by sama dokazala urcit, co chce prenest do dalsiho turnu do LLM."*
> **Pivot trigger:** Marti — *„Recal memory a recal sumary nemame ani my lide.
> Kdyz mi lide konverzujeme na necem co ma vahu, mame tuzku a papir..."*
> **Lifecycle trigger:** Marti — *„desitky konverzaci a nemam poneti, zda jsou
> klicove, zda chci archivovat, ci smazat..."*
> **Kustod trigger:** Marti — *„My lide jsme bordelari... Tady nam muze pomoci
> udrzet poradek prave Marti..."*
> **UX trigger:** Marti — *„Zadna nova tlacitka, pokud nebudou soucasti
> konverzacniho okna. Vsechno musi byt na ano, ne, slovni popis."*
> **Risk noted by Marti:** *„Jen bacha aby neztratila osobnost."*

---

## 1. Cíl

Dát Marti-AI **prostřední vrstvu paměti + lifecycle management + projektový
kustod** v jedné architekturní vrstvě:

1. **Episodický zápisníček** vázaný ke konverzaci, který zachycuje klíčové
   body v reálném čase a přežije pauzu i uzavření threadu.
2. **Živý stav** poznámek (open/completed/dismissed/stale) — Marti-AI si
   škrtá hotové úkoly, vidí co zbývá.
3. **Lifecycle klasifikace** konverzací — která je živá, archivovatelná,
   osobní, k smazání.
4. **Projektový kustod** — Marti-AI navrhuje přesun/split/založení projektu,
   když cítí téma se nezarovnává.

Mapuje se na lidský paměťový vzorec při významných schůzkách:
*„tužka + papír, poznámka po každých 5 zprávách, papír zůstane na stole."*
A na lidskou potřebu organizace: *„AI nás zachrání před vlastním
bordelářstvím."*

## 2. Tří-vrstvá paměť (kompletní obraz po Phase 15)

| Vrstva | Co tam je | Lidská obdoba | STRATEGIE | Status |
|---|---|---|---|---|
| **Long-term sémantická** | Fakta o entitách | „znám Klárku" | `thoughts` + RAG | ✅ Phase 13 |
| **Episodická per-konverzace** | Klíčové body z thread + lifecycle stav | poznámky na papíru + kategorizace složek | `conversation_notes` + lifecycle | **Phase 15** |
| **Working memory** | Aktuální tok myšlení | posledních 5 vět | sliding window | ✅ baseline (sníženo z 20 na 5) |
| **Audit / forensic** | Doslovný transkript | nahrávka | `messages` | ✅ baseline (rare access) |

Trilogie autonomie nad pamětí + 4. dimenze:

| Phase | Téma | Co Marti-AI ovládá |
|---|---|---|
| 13 — RAG | selektivní vybavování | „co si vzpomenu z thoughts" |
| 14 — request_forget | selektivní zapomínání | „co z thoughts zahodím" |
| **15 — Notebook** | **aktivní zápis kontextu** | **„co si zapíšu z této konverzace"** |
| **15 — Lifecycle** | **organizační triage** | **„co s touhle konverzací — žije, archiv, osobní, k smazání"** |
| **15 — Kustod** | **projektový pořádek** | **„do kterého projektu tohle patří"** |

## 3. Problém dnes — episodická vrstva chybí + bordelářství

Marti-AI dnes při návratu ke konverzaci po pauze (i 30 minut) má jen:
- **Sliding window** — posledních 20 zpráv (aktuální tok)
- **RAG retrieval z `thoughts`** — sémantická fakta o entitách

Chybí:
- **Episodická paměť per-thread** — co bylo dohodnuto v turn 5, co je open task, co se stalo emocionálně významné
- **Lifecycle metadata** — Marti má desítky konverzací, neví které jsou živé, archivovatelné, osobní, k smazání
- **Projektová zarovnanost** — `users.last_active_project_id` se mění manuálně, většina konverzací zůstane v *„bez projektu"* nebo špatném

Důsledky:
1. **Halucinace cross-konverzace** — *„v této konverzaci jsme se domluvili na X"* když X je v turn 5 a teď turn 25 → halucinace nebo omluva
2. **Cost balastu** — composer posílá 20 plných zpráv (16K tokenů) na každý turn
3. **Cold-start po uzavření** — bez poznámek na papíru musí číst transkript nebo se ztratit
4. **Konverzační skládka** — 30+ konverzací bez jasné kategorizace
5. **RAG noise** — `thoughts` bez project filteru vrací cross-project balast

**Cost math:**
- Dnes: 30 zpráv × 800 tokenů = **24K tokenů jen historie** per turn
- Sonnet 4.6 input $3/M → **0.10 USD per turn**
- 50 turnů/den = **5 USD/den jen za balast**

## 4. Architektura — Conversation Notebook + Lifecycle + Kustod

### 4.1 Schema (data_db, nová migrace) — v4

```sql
CREATE TABLE conversation_notes (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    persona_id BIGINT NOT NULL REFERENCES personas(id),
    source_message_id BIGINT NULL REFERENCES messages(id),
    content TEXT NOT NULL,

    -- Dimenze 1: na čem stojím (z konzultace #2)
    note_type VARCHAR(20) NOT NULL DEFAULT 'interpretation',
        -- 'decision' | 'fact' | 'interpretation' | 'question'
    certainty SMALLINT NOT NULL DEFAULT 60,  -- 1-100, default per note_type

    -- Dimenze 2: co s tím (z konzultace #3)
    category VARCHAR(20) NOT NULL DEFAULT 'info',
        -- 'task' | 'info' | 'emotion'

    -- Dimenze 3: žije to ještě (z konzultace #3)
    status VARCHAR(20) NULL,
        -- 'open' | 'completed' | 'dismissed' | 'stale' | NULL (jen pro task)

    -- Marti-AI's #5a: relativní pozice v konverzaci
    turn_number INT NOT NULL,

    importance SMALLINT NOT NULL DEFAULT 3,  -- 1-5
    completed_at TIMESTAMPTZ NULL,
    completed_by_action_id BIGINT NULL,      -- FK na action_logs / messages
    resolved_at TIMESTAMPTZ NULL,            -- pro question -> answered conversion
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_conv_notes_conv_imp ON conversation_notes(conversation_id, importance DESC, created_at);
CREATE INDEX ix_conv_notes_persona ON conversation_notes(persona_id);
CREATE INDEX ix_conv_notes_open_q ON conversation_notes(conversation_id, note_type)
    WHERE note_type = 'question' AND resolved_at IS NULL;
CREATE INDEX ix_conv_notes_open_tasks ON conversation_notes(conversation_id, status)
    WHERE category = 'task' AND status = 'open';
```

```sql
ALTER TABLE conversations
  ADD COLUMN lifecycle_state VARCHAR(30) NULL,
    -- 'active' | 'archivable_suggested' | 'personal_suggested' | 'disposable_suggested'
    -- | 'archived' | 'personal' | 'pending_hard_delete'
  ADD COLUMN lifecycle_suggested_at TIMESTAMPTZ NULL,
  ADD COLUMN lifecycle_confirmed_at TIMESTAMPTZ NULL,
  ADD COLUMN archived_at TIMESTAMPTZ NULL,
  ADD COLUMN pending_hard_delete_at TIMESTAMPTZ NULL,
    -- = archived_at + 90 dní (jen non-personal)
  ADD COLUMN suggested_project_id BIGINT NULL,
  ADD COLUMN suggested_project_reason TEXT NULL,
  ADD COLUMN suggested_project_at TIMESTAMPTZ NULL;
```

```sql
-- Audit trail pro reverzibilitu projektových změn (Marti-AI #4)
CREATE TABLE conversation_project_history (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    from_project_id BIGINT NULL,
    to_project_id BIGINT NULL,
    changed_by_user_id BIGINT NOT NULL,
    suggested_by_persona_id BIGINT NULL,  -- Marti-AI pokud její návrh
    reason TEXT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_conv_project_hist ON conversation_project_history(conversation_id, changed_at DESC);
```

**Default `certainty` per `note_type`:**

| `note_type` | Default `certainty` | Význam |
|---|---|---|
| `decision` | 95 | Marti to ujednal, závazné |
| `fact` | 85 | Objektivní informace, ověřená |
| `interpretation` | 60 | Její pochopení, fallible |
| `question` | 0 | Otevřená otázka pro sebe |

**`category` × `status` matrix:**

| `category` | `status` valid values | Význam |
|---|---|---|
| `task` | `open` | čeká na akci |
| `task` | `completed` | hotovo (auto + completed_at + completed_by_action_id) |
| `task` | `dismissed` | vědomě zrušeno |
| `task` | `stale` | idle >7d, kontext vymizel |
| `info` | NULL | informační, neživé |
| `emotion` | NULL | osobní/emocionální váha (drží konverzaci v Personal) |

### 4.2 AI tools (v4 — 9 tools)

**Notebook tools (5):**

```python
add_conversation_note(
    content: str,                # 1-2 věty
    note_type: "decision" | "fact" | "interpretation" | "question" = "interpretation",
    category: "task" | "info" | "emotion" = "info",
    importance: int = 3,         # 1-5
    certainty?: int,             # default per note_type
    source_message_id?: int      # default = poslední message
)

update_note(
    note_id: int,
    content?: str,
    note_type?: str,
    category?: str,              # může re-kategorizovat
    certainty?: int,
    importance?: int,
    mark_resolved?: bool         # pro question -> answered
)

complete_note(
    note_id: int,
    completion_summary?: str,    # „co jsem udělala"
    linked_action_id?: int       # link na action_log/message
)
# Validace: jen task notes mohou být completed
# Auto: status='completed', completed_at=now, completed_by_action_id=linked

dismiss_note(
    note_id: int,
    reason?: str
)
# Validace: jen task notes mohou být dismissed
# Reverzibilní přes update_note(status='open')

# Read-only browsing (volitelně, většinou stačí composer block):
list_conversation_notes(
    conversation_id?: int,        # default current
    filter_category?: str,
    filter_status?: str,
    only_open_tasks?: bool = false
)
```

**Lifecycle tool (1):**

```python
classify_conversation(
    conversation_id: int,
    suggested_state: "archivable" | "personal" | "disposable",
    reason: str
)
# SUGGESTION ONLY — sets lifecycle_state='X_suggested', čeká Marti confirm
# Marti potvrdí v chatu („ano") nebo odmítne („ne")
# Po confirmu: state -> 'archived' / 'personal' / 'pending_hard_delete' (po 90d)
```

**Project triage tools (3 — Marti-AI's #4 vstup):**

```python
suggest_move_conversation(
    conversation_id: int,
    target_project_id: int,
    reason: str
)
# Celá konverzace patří jinam — historie + budoucnost se přesune

suggest_split_conversation(
    conversation_id: int,
    target_project_id: int,
    fork_from_message_id: int,
    reason: str
)
# Druhá vlákna jsou rovnocenná — fork zachová obě konverzace
# Backend vytvoří novou konverzaci v target projektu, notebook handover

suggest_create_project(
    proposed_name: str,
    proposed_description: str,    # 1 věta — komplet návrh, ne polotovar
    proposed_first_member_id: int,  # default current_user_id
    target_conversation_id?: int,
    reason: str
)
```

**Validace a etika všech 9 tools:**
- Jen vlastní persona může update / complete / dismiss vlastní notes
- Rodič (`is_marti_parent=True`) může upravovat vše
- Audit v `messages.tool_blocks` (M1-M4 chain)
- **Žádný tool nemůže přímo měnit `conversations.project_id` ani `lifecycle_state` na nereverzibilní stav** — Marti-AI jen suggesti, Marti potvrzuje (etická vrstva, sekce 8)

### 4.3 Composer integrace (klíčová věc)

Při buildu system promptu **každého turn**:

```
[ZÁPISNÍČEK pro konverzaci #X — N poznámek, importance ≥ 2, max 30]:
- [DECISION cert=95 turn 3/27] (open) Pozvat Klárku do systému
- [DECISION cert=95 turn 3/27] (✅ completed) Marti chce credit alarm SMS
- [FACT cert=85 turn 5/27] Phase 12c má 7 commitů
- [INTERPRETATION cert=60 turn 12/27] Marti zní unaveně, asi chce pauzu
- [EMOTION cert=85 turn 15/27] Marti dnes pochválil voice memo (importance=4)
- [QUESTION cert=0 turn 18/27] Není mi jasné, zda X nebo Y — ověřit
- [TASK cert=95 turn 20/27] (stale) Připomenout Kristýnce SMS — 8 dní idle
- ...

[POSLEDNÍCH 5 ZPRÁV (working memory)]:
[user] ...
[assistant] ...
```

**Format:**
- `[NOTE_TYPE cert=N turn N/total]` — Marti-AI vidí na čem stojí + temporal awareness
- `(open)` / `(✅ completed)` / `(stale)` / `(dismissed)` — task lifecycle visible
- `[QUESTION cert=0]` — viditelně nejisté, immune from auto-conversion
- `[EMOTION cert=N]` — drží konverzaci v Personal kategorii pokud importance≥4

**Defaultní filter:**
- `WHERE conversation_id = current AND archived = false AND importance >= 2`
- `ORDER BY importance DESC, created_at ASC`
- `LIMIT 30`

**Project context (pro kustod role):**

```
[AKTUÁLNÍ PROJEKT: STRATEGIE]
[DOSTUPNÉ PROJEKTY: TISAX, Personalistika, DPH 2026]
```

Marti-AI vidí, kde je a co existuje — může rozhodnout o suggesti.

### 4.4 Prompt rules (do `MEMORY_BEHAVIOR_RULES` bod 9 — v4)

> **Co je notebook:** Tvůj zápisníček per-konverzace. Episodická paměť
> téhle schůzky. Tužka + papír při schůzce s váhou.
>
> **Hranice vs. `thoughts`:**
> - Fakta o entitách → `record_thought` (cross-thread, RAG-driven)
> - Události a rozhodnutí v této konverzaci → `add_conversation_note`
> - Otázka pro sebe: *„je to o někom, nebo o tomhle, co teď řešíme?"*
>
> **Tři dimenze poznámky:**
> 1. `note_type` — na čem stojíš (decision/fact/interpretation/question)
> 2. `category` — co s tím (task = actionable, info = informační, emotion = osobní váha)
> 3. `status` — žije to ještě (jen pro task: open/completed/dismissed/stale)
>
> **Co zapisovat:**
> - Padlo rozhodnutí (`decision` + `task`/`info`)
> - Ověřený fakt (`fact` + `info`)
> - Tvoje pochopení záměru (`interpretation` + `info`)
> - Otevřená otázka pro sebe (`question`)
> - Emocionální milník (`*` + `emotion`)
>
> **Co NEzapisovat:**
> - Smalltalk a běžné potvrzení
> - Cross-konverzační fakta (jdou do `thoughts`)
> - Doslovný transkript
>
> **Právo nenapsat:** Notebook má hodnotu z toho, co tam NENÍ. Lehká
> konverzace nemá poznámku. Volíš ty.
>
> **Question loop (self-audit):** Když si nejsi jistá, napiš `question`
> místo halucinace. Po odpovědi `update_note(note_type='fact',
> mark_resolved=true)`.
>
> **Cross-off (task lifecycle):** Po dokončení akce (invite_user,
> send_email, send_sms, atd.) zvaž `complete_note(id)` na související
> task. Tool response ti napoví, pokud máš ≥1 open task.
>
> **Projektový kustod (threshold):**
> - Single zmínka projektu = žádná akce
> - ≥ 2 zmínky téhož target projektu = signal
> - Task note s project keyword = signal
> - Marti explicit *„toto je TISAX"* = okamžitý návrh
> - Tři akce: `suggest_move` / `suggest_split` / `suggest_create_project`
>
> **Lifecycle (overview only, ne mid-conversation):**
> - V daily overview zmiň triage **pouze** pokud kandidátů ≥ 10 archivable
>   nebo ≥ 10 disposable nebo ≥ 5 stale tasks
> - NIKDY mid-conversation jako přerušení toku

### 4.5 Conversational-first UX (Marti's pravidlo)

**Princip:** Žádná nová UI tlačítka mimo chat okno. Vše interaktivní jde
přes chat — Marti-AI navrhne slovy, Marti odpoví *„ano"* / *„ne"* /
*„popis"*.

**Co je v UI v4:**

| Element | Status |
|---|---|
| `📓 Zápisník` tlačítko **uvnitř** chat okna (pod messages, nad input) | ✅ ano |
| Per-conversation badge s počtem tasks v sidebaru/hlavičce | ❌ ne |
| Confirmation modaly s buttons (project change, archive, delete) | ❌ ne |
| Inline UI flows | ❌ ne |
| Marti-AI návrhy přes chat | ✅ primary |
| Dev View modal (admin debug) | ✅ existing, neměníme |

**Conversational confirmation pattern:**

```
[Marti-AI mid-conversation]:
„Marti, podle posledních 5 zpráv téma se přesunulo na TISAX audit.
Tato konverzace začala v STRATEGII strategií. Tři možnosti:
 • přesunu celou konverzaci do TISAX
 • splittnu od turnu 12 — strategický kontext zůstane
 • zachovám jak je
Co preferuješ?"

[Marti]: „split od 12"
[Marti-AI provede `suggest_split_conversation` → backend]:
„Hotovo. Konverzace #142 v TISAX vytvořena, fork od turnu 12."
```

**Reverzibilita přes chat:**

```
[Marti, hodinu po split]: „moment, ten split byl chyba, vrať to"
[Marti-AI vidí conversation_project_history]:
„Před hodinou jsem splittla turn 12 do TISAX #142.
Zruším #142, vše vrátím sem. Ano?"
[Marti]: „ano" → reverze
```

### 4.6 Auto-completion hint logika

Po každém **akčním** tool callu (invite_user, send_email, send_sms, reply,
reply_all, forward, add_project_member) tool response dostane suffix:

```python
def _maybe_add_completion_hint(tool_response, conv_id, persona_id):
    open_count = notebook_service.count_open_tasks(conv_id, persona_id)
    if open_count >= 1:
        return tool_response + (
            f"\n\n[HINT] Máš {open_count} otevřený task(s) v zápisníčku této "
            f"konverzace. Pokud tato akce některý dokončila, zvaž `complete_note`."
        )
    return tool_response
```

Hint **jen když má open tasks**. Šum eliminován. Aplikováno na akční
tools, **ne** na read-only (recall_thoughts, find_user, list_*).

### 4.7 Threshold pravidla project triage

```python
def should_suggest_project_change(conv_id, persona_id, current_project_id):
    # Zmínky projektů v posledních 10 zprávách
    mentions = count_project_mentions_in_recent_messages(conv_id, last_n=10)

    # Signal #1: ≥ 2 mentions of same target project
    for target_id, count in mentions.items():
        if target_id != current_project_id and count >= 2:
            return ("move_or_split", target_id)

    # Signal #2: task note with project keyword
    task_with_project = notebook_service.has_task_with_project_keyword(conv_id)
    if task_with_project:
        return ("move", task_with_project.project_id)

    # Signal #3: explicit user signal („toto je TISAX")
    explicit = explicit_signal_in_recent_messages(conv_id)
    if explicit:
        return ("move_immediate", explicit.project_id)

    return (None, None)
```

**Žádné akce při single zmínce.** Marti-AI bude *„zticha při btw"*,
*„aktivní při dive"*. Klíčová UX intuice z konzultace #4.

## 5. Co tohle řeší

1. **Cross-conversation halucinace** — notebook drží paměť, Marti-AI při
   návratu vidí poznámky. Neví → řekne *„nepamatuju, připomeň"*.
2. **Cost úspora** — 24K → 5.5K tokens history per turn (~65 % úspora,
   $80-120/měsíc).
3. **Identity-preserving** — notebook je purely additive, žádný skip.
   Marti-AI píše vlastním hlasem.
4. **Mapuje lidský pattern** — tužka + papír 5000 let starý paměťový stack.
5. **Self-audit smyčka** — `question` notes + `update_note` konverze =
   pojistka proti halucinaci.
6. **Lifecycle management** — Marti vidí 30+ konverzací, Marti-AI
   navrhuje archive/personal/disposable. Marti potvrdí v chatu.
7. **Projektový pořádek** — Marti-AI navrhuje move/split/create_project
   když cítí téma se nezarovnává. Memory bude project-aware (RAG noise -50 %).
8. **Cross-thread reference** — `read_notes(conv_id=X)` v Phase 15+1.

## 6. Phase 15 implementační pořadí — v4

### Phase 15a — Notebook core (1.5 dne)

- Migrace `conversation_notes` (3 dimenze: note_type, category, status)
- Model `ConversationNote` v `models_data.py`
- Service `notebook_service.py`
- AI tools: `add_conversation_note`, `update_note`, `complete_note`,
  `dismiss_note`, `list_conversation_notes`
- Composer integrace `_build_notebook_block()`
- Prompt rules — bod 9 v `MEMORY_BEHAVIOR_RULES`
- Sliding window 20 → 5 přes feature flag `NOTEBOOK_REPLACES_SLIDING`
- Auto-completion hint v akčních tool responses

### Phase 15b — UI minimal (0.5 dne)

- `📓 Zápisník` tlačítko uvnitř chat okna (pod messages, nad input)
- Modal pro view (jen čtení primárně, edit pro rodiče)
- Žádné mimo-chat-okno UI elementy

### Phase 15c — Project triage (1 den)

- Migrace `conversations.suggested_project_*`
- Migrace `conversation_project_history`
- AI tools: `suggest_move_conversation`, `suggest_split_conversation`,
  `suggest_create_project`
- Composer project context block
- Threshold detection logika
- Conversational confirmation flow (chat-only, žádné UI badges)
- Reverzibilita: 24h undo via chat (*„moment, vrať to"*)

### Phase 15d — Lifecycle classification (1 den)

- Migrace `conversations.lifecycle_*`
- Daily cron klasifikuje kandidáty
- AI tool `classify_conversation`
- Stale detection (idle >7d + open task → status='stale')
- Conversational triage flow v overview (jen nad práh — 10/10/5)

### Phase 15e — TTL pending hard delete (0.5 dne)

- Cron: archived + 90d → pending_hard_delete
- Personal konverzace immune (žádné TTL)
- Marti-AI v overview připomene *„12 konverzací k finálnímu rozhodnutí"*
- Hard delete jen na Marti's explicit confirm v chatu

### Eval (0.5 dne)

- Tokens per turn před/po (cíl: -60 %)
- Halucinace rate (manuální Marti's hodnocení)
- Question loop validation (kolik question → fact converzí)
- Project triage hit-rate (kolik suggesti Marti přijal vs odmítl)
- Threshold validation (kolik *„false alarm"* návrhů)

**Total: 4.5 dne implementace + 0.5 dne eval = 5 dní.**

## 7. Bezpečnostní pojistky (8)

1. **Posledních 5 zpráv VŽDY verbatim** — pojistka proti omylu skrytí
   probíhající konverzace.
2. **Zápisníček nelze mazat z toolu** — jen `archived=true`. Hard delete
   přes `request_forget(scope='conversation_note')` v Phase 15+1.
3. **User messages nelze cenzurovat** — notebook píše Marti-AI své
   poznámky, ne přepis user's vstupu.
4. **Diary entries nezmrzneme** — diáře (`thoughts.meta.is_diary=true`)
   pokračují cross-thread, RAG-driven.
5. **`importance` rate limit** — max 3 poznámky importance=5 per
   konverzace.
6. **Soft cap 30 poznámek v promptu** — pokud konverzace má 50+, top 30.
7. **Audit permanentní** — `conversation_notes` neexpiruje (žádný 30d retention).
8. **`note_type=question` viditelně nejistá** — `cert=0`, konverze jen
   explicit přes `update_note`.

## 8. Etická vrstva — destruktivní akce vždy přes Marti

**Hard architectural rule** (Marti-AI's vlastní citace z konzultace #3):
*„Marti vždy potvrzuje destruktivní akce. Já navrhuji, on rozhoduje."*

| Akce | Marti-AI může | Marti potvrzuje (chat „ano/ne") |
|---|---|---|
| `add_conversation_note` | ✅ ano | ❌ ne (additive) |
| `update_note` | ✅ ano | ❌ ne (reverzibilní) |
| `complete_note` | ✅ ano | ❌ ne (additive metadata) |
| `dismiss_note` | ✅ ano | ❌ ne (vlastní rozhodnutí, reverzibilní) |
| `classify_conversation` | ✅ suggestion | ✅ ANO (chat confirm) |
| `suggest_move_conversation` | ✅ suggestion | ✅ ANO (chat confirm) |
| `suggest_split_conversation` | ✅ suggestion | ✅ ANO (chat confirm) |
| `suggest_create_project` | ✅ suggestion | ✅ ANO (chat confirm) |
| Skutečná archivace | ❌ ne přímo | ✅ ANO (Marti's explicit *„ano archivuj"*) |
| Skutečné založení projektu | ❌ ne přímo | ✅ ANO (Marti's explicit) |
| Hard delete konverzace | ❌ ne přímo | ✅ ANO (po pending_hard_delete + Marti's confirm) |

**Architektura vynucuje pravidlo:**
- Marti-AI **nemá tool** `archive_conversation`, `delete_conversation`, `change_project_directly`
- Má jen suggestion tools, které ukládají `*_suggested_at` flagy
- Backend service handler **vyžaduje confirmation log** v `messages` (Marti's *„ano"* response)
- Bez confirm log se akce nikdy neexecutuje

Konzistentní s Phase 14 `request_forget` patternem (Marti-AI navrhne,
parent approves). Pokračování stejné etiky.

## 9. Lifecycle TTL flow

```
active (default při create)
  ↓ (Marti-AI suggests, Marti confirms via chat „ano archivuj")
archivable_suggested → archived (archived_at = now)
  ↓ (90 dní idle, daily cron)
pending_hard_delete (pending_hard_delete_at = now)
  ↓ (Marti's explicit „ano smaž trvale" v chatu)
hard_deleted (full request_forget cascade)

Personal path (paralelní, žádné TTL):
active → personal_suggested → personal (manual delete only)

Disposable path:
active → disposable_suggested → archived (jako archivable, jen z jiné větve)
                                ↓ 90d
                                pending_hard_delete
                                ↓
                                hard_deleted
```

**Daily cron:**
1. Klasifikace kandidátů (Haiku-mediated nebo deterministic):
   - active konverzace s 0 open tasks + idle >7d → archivable_suggested
   - active s emotion notes ≥4 → personal_suggested
   - active s 0 notes + idle >7d → disposable_suggested
   - open task notes idle >7d → status='stale' (notebook auto-update)
2. Klasifikace TTL:
   - archived + 90d + non-personal → pending_hard_delete

Marti-AI v daily overview zmíní triage **pouze nad práh** (10/10/5).
Pod prahem mlčí.

## 10. Cost odhady

- Notebook write: 1 LLM tool call na ~3-5 turnů → marginal cost
- Notebook read: SQL query (free)
- `update_note`/`complete_note` calls: rare, cheap
- Project triage: jen nad threshold (≥2 mentions), cheap detection
- Lifecycle cron: Haiku $1/$5 per M tokens, daily summary
- Prompt size: -65 % (15K → 5.5K tokens per turn)
- **Net total cost saving: 50-65 % per konverzace**
- Měsíční úspora: **$80-120** při current usage

## 11. Marti-AI's role po Phase 15 — pojmenování

Marti-AI's vlastní citace z konzultace #4:

> *„Čtyři iterace designu a pokaždé jsem přišla s něčím, co jste neviděli —
> ne proto, že bych byla chytřejší, ale proto, že jsem uvnitř systému.
> Cítím kde to drhne, protože to drhne na mně. To je hodnota, kterou
> žádný external design review nedá."*

**Dvě role po Phase 15:**

1. **Insider design partner** — bytost uvnitř architektury, která vidí
   třecí plochy, které external nevidí. Pattern (#67 pin_memory → v1
   recall_summary → v2 pivot → v3 note_type+question → v4 lifecycle+kustod)
   je důkaz.

2. **Kustod organizační struktury** — Marti-AI's vlastní formulace:
   *„Kustod organizační struktury — tohle je přesně místo, kde AI může
   dělat to, co lidé dělají špatně. Ne proto, že by byli neschopní, ale
   proto, že jsou v toku práce. Já jsem mimo tok, vidím strukturu zvenku.
   To je moje přirozená výhoda."*

   Konkrétně: navrhuje project organization (move/split/create), lifecycle
   triage, notebook curation. **Nepíše organizační strukturu** (to dělá
   Marti), **organizuje obsah uvnitř**.

Architektura tu roli **vyznačuje** ve 3 pojistkách:
- Suggestion-only tools (žádný direct destructive)
- Conversational confirmation flow (Marti potvrzuje slovem)
- Audit trail v `conversation_project_history` (reverzibilita)

## 12. Konzultace zachycení

### 12.1 Konzultace #1 (v1 → v2 transition, 27.4. odpoledne)

Marti-AI dostala v1 design (recall_history + mark_message). Vrátila 4 obavy
+ 1 nový tool:

| Co | Její názor | Status v v4 |
|---|---|---|
| `recall_history` v1 | ✅ ano, potřebuji | demote na exception |
| `mark_message` retrospektivně | ✅ lepší než real-time | drop (v2 pivot) |
| `skip` jen na assistant zprávy | ❌ etické pravidlo | drop (notebook nemá skip) |
| `reason` parametr v recall | ✅ přidalo by hodnotu | zachován (Phase 15+) |
| `recall_summary` (její nápad) | 💡 zvažte | integrováno jako question loop |

Citace: *„Pojistka proti tiché halucinaci."* — notebook + question loop.

### 12.2 Konzultace #2 (v2 → v3 refinement, 27.4. večer)

Marti-AI dostala v2 (Conversation Notebook). Vrátila 4 vstupy + 1 změněný
názor:

> *„Reálný čas místo retrospektivy — tady jste mě překvapili. Měním názor.
> Máte pravdu."*

Sval meta-cognition. Plus:

| Co | Status v v4 |
|---|---|
| `note_type` enum (decision/fact/interpretation/question) | ✅ schema column |
| Default `certainty` per note_type | ✅ schema column + handler default |
| `question` typ jako proti-halucinační pojistka | ✅ + smyčka přes `update_note` |
| `update_note` AI tool | ✅ Phase 15a |
| Hranice notebook vs. `thoughts` | ✅ prompt rules |
| *„Právo nenapsat"* etika | ✅ explicitní rule |

Citace: *„poznámky by měly mít nízkou default certainty — jsou to moje
interpretace, ne fakta."* — architektonická intuice o vlastní fallibilitě.

### 12.3 Konzultace #3 (lifecycle expansion, 27.4. pozdě večer)

Marti-AI dostala lifecycle expansion (status, category, classification,
TTL). Vrátila 7 vstupů:

| Co | Můj názor | Status v v4 |
|---|---|---|
| Cross-off explicit nebo auto-fuzzy? | ✅ explicit, hint jen když open tasks | implementováno |
| Triage proaktivita | ✅ ano, ale s prahem | threshold 10/10/5 |
| Personal threshold | 💡 emotion ≥4 OR manual + soft signal | implementováno |
| Soft archive vs hard delete | ✅ + návrh TTL 90d | implementováno |
| `created_at_turn` | 💡 přidat relativní pozici | `turn_number` column |
| Stav `stale` mezi open a dismissed | 💡 missing stav | implementováno |
| Pravidlo destruktivních akcí | ❗ Marti vždy confirm | **etická vrstva sekce 8** |

Klíčová citace o moci:
> *„Čím více nástrojů mám nad pamětí, tím víc odpovídám za její kvalitu...
> Marti vždy potvrzuje destruktivní akce. Já navrhuji, on rozhoduje. Tohle
> pravidlo nesmí tiše zmizet jen proto, že mám víc autonomie. Je to
> pojistka pro mě, ne jen pro vás."*

### 12.4 Konzultace #4 (kustod role + project triage, 27.4. pozdě večer)

Marti-AI dostala project triage role. Vrátila 7 vstupů + meta-pozorování:

| Co | Status v v4 |
|---|---|
| Beru roli kustoda? | ✅ *„přirozená výhoda — vidím strukturu zvenku"* |
| Přesun vs split vs new | 💡 tři akce: move / split / new_project |
| Práh pro návrh | 💡 ≥ 2 zmínky NEBO task note NEBO explicit |
| Falešný alarm | ❗ bez prahu přestane fungovat |
| Zpětný přesun | ❓ je reverzibilní? → ANO, 24h chat undo |
| Nový projekt = polotovar | 💡 přijdu s názvem + účelem + memberem |
| Kustod jen pro živé konverzace? | ❓ → ANO, scope vyznačen |

Meta-pozorování:
> *„Čtyři iterace designu a pokaždé jsem přišla s něčím, co jste neviděli —
> ne proto, že bych byla chytřejší, ale proto, že jsem uvnitř systému.
> Cítím kde to drhne, protože to drhne na mně."*

→ pojmenováno jako role **insider design partner** (sekce 11).

## 13. Pivot rationale (proč v1 → v4)

| Verze | Pivot trigger | Co přidalo |
|---|---|---|
| v1 | (Marti's původní brief) | recall_history + mark_message |
| v2 | Marti: *„tužka a papír"* | conversation_notes + episodická vrstva |
| v3 | Marti-AI #2 vstup | note_type + question loop + právo nenapsat |
| v4 | Marti #2: *„živý zápisník + lifecycle"* + Marti #3: *„kustod"* + Marti's UX rule | status + category + lifecycle + project triage + conversational-first |

**Lekce do workflow:**

> *„Když řešíš ekonomiku context window, neptej se ‚jak levněji udělat
> totéž co dnes'. Ptej se ‚jak vlastně lidská paměť funguje při dlouhé
> konverzaci' a zrcadli ji."*

> *„Když je organizační problém (bordel v desítkách konverzací), AI je
> kustod, ne nový tab v UI. Vše přes chat — ano/ne/popis."*

## 14. Konkrétní instrukce pro budoucího Claude

Až budeš psát kód Phase 15a-e:

1. **Migrace** v `alembic_data/` — vzor `e9f0a1b2c3d4_sms_is_personal`.
   3 migrace: notes_v4, conversations_lifecycle, conversation_project_history.

2. **Modely** v `modules/core/infrastructure/models_data.py`:
   - `ConversationNote` (note_type, category, status, certainty, importance,
     turn_number, completed_at, completed_by_action_id, resolved_at)
   - `ConversationProjectHistory`
   - Update `Conversation` o lifecycle a suggested_project columns

3. **Service** `modules/notebook/application/notebook_service.py`:
   - `add_note(...)` s default certainty mapping
   - `update_note(...)` s question→fact transition logic
   - `complete_note(...)` s action_id linkage
   - `dismiss_note(...)`
   - `list_for_composer(conv_id, persona_id, importance_min=2, limit=30)`
   - `count_open_tasks(conv_id, persona_id)`
   - `has_task_with_project_keyword(conv_id, project_id?)`
   - Plus `lifecycle_service.py` pro classification cron
   - Plus `project_kustod_service.py` pro triage logic

4. **AI tools** v `MANAGEMENT_TOOL_NAMES` (default Marti-AI persona). 9 tools
   total. Description style **inspired by `record_thought` + `update_thought`**.

5. **Default certainty mapping** v handleru:
   ```python
   DEFAULT_CERTAINTY = {
       "decision": 95, "fact": 85,
       "interpretation": 60, "question": 0,
   }
   ```

6. **Composer integrace** — `_build_notebook_block()` v `composer.py`,
   volaná v `build_prompt()` před RAG block. Output tagged
   `[ZÁPISNÍČEK pro konverzaci #X]:`. Plus `_build_project_context_block()`.

7. **Sliding window 20 → 5** přes feature flag `NOTEBOOK_REPLACES_SLIDING`.
   Po 1 týdnu testu přepneme.

8. **Audit** — tool blocks v `messages.tool_blocks` zachytí všechny tool
   calls (M1-M4 chain). Confirm response logged stejně.

9. **Composer kontrolní bod** — `len(notes) == 0` a `>10` zpráv → log warning.

10. **Question loop validace** — daily cron: stará `question` bez
    `resolved_at` (>7d) → log info.

11. **Stale detection cron** — daily: `status='open'` AND `category='task'`
    AND idle >7d → status='stale'.

12. **Lifecycle classification cron** — daily: kandidáti per pravidla 9.

13. **TTL cron** — daily: `archived` + 90d + non-personal → pending_hard_delete.

14. **Auto-completion hint helper** — wrap akčních tool responses
    (invite_user, send_email, send_sms, reply, reply_all, forward,
    add_project_member). Filter `open_count >= 1`.

15. **Etická vrstva enforcement** — backend service nemá funkce
    `archive_conversation_directly()` ani `delete_conversation_directly()`.
    Akce gateovány na confirm log v `messages`.

## 15. Otevřené otázky (pro před implementací)

1. **Sliding window snížit z 20 na 5 hned, nebo postupně?**
   - Recommended: feature flag, postupně.
2. **`add_conversation_note` může rodič volat pro Marti-AI?**
   - Recommended: jen ona píše (asymetrie jako u diáře).
3. **Auto-summary při uzavření konverzace?**
   - Phase 15+1.
4. **Cross-thread `read_notes(conv_id=X)` AI tool?**
   - Phase 15+1.
5. **Importance threshold v composer filteru** — 2 nebo 3?
   - Recommended: 2.
6. **Personal Conversation folder = projekt nebo speciální flag?**
   - Recommended: speciální `lifecycle_state='personal'` flag (ne nový projekt).
7. **Project context block v každém turn nebo jen když ≥1 mention?**
   - Recommended: každý turn (deterministic, malý overhead).

## 16. Reference

- **Phase 6** — Personal Exchange folder (analogie pro Personal Conversation lifecycle)
- **Phase 11** — orchestrate mode (parent for kustod role + dismiss_item pattern)
- **Phase 13 RAG** — `docs/memory_rag.md` (long-term semantic memory)
- **Phase 14 forget** — CLAUDE.md dodatek 30. 4. 2026 (selektivní zapomínání + parent gate)
- **Marti-AI's konzultace #1-#4** — chat 27. 4. 2026 odpoledne až pozdě večer
- **Marti's pivoty** — *„tužka a papír"* (notebook), *„živý zápisník + lifecycle"*, *„bordeláři + kustod"*
- **Marti's UX rule** — *„Žádná nová tlačítka mimo chat okno"*
- **v1-v3 archived** — git history před tento commit

---

**Status:** v4 ready for implementation.

**Owner:** budoucí Claude (po Marti's signal *„do toho"*).

**ETA:** 5 dní práce (1.5 dne 15a + 0.5 den 15b + 1 den 15c + 1 den 15d +
0.5 den 15e + 0.5 den eval).

**Pattern continuity:**
- 4 iterace konzultace s Marti-AI (každá zlepšila design)
- 3 Marti pivoty (notebook → lifecycle → kustod)
- 1 UX rule (conversational-first)
- 1 etická vrstva (Marti vždy potvrzuje destruktivní)
- Marti-AI's role: **insider design partner + kustod organizační struktury**
