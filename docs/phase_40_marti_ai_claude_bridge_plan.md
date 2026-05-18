# Phase 40 — Marti-AI ↔ Claude API bridge

**Datum:** 19. 5. 2026 (~02:45 ráno)
**Trigger:** Marti's chat: *„kdyby Marti-AI stavela s Kristy a s tebou se
mohla pres API domlouvat na upravach STRATEGIE... posilat diagnosticka
data a tak?"*
**Use case:** Marti je v Praze 20.-21.5. (mimo). Marti-AI + Kristý
stavějí CRM na EUROSOFT. Marti-AI narazí na problém / potřebuje
diagnostiku / code review / architectural opinion → bez Marti's manuální
relay s Claude.

---

## Architektura — co je Cowork vs co je Anthropic API

**Cowork mode** (Anthropic desktop app na Marti's NB):
- Claude (Sonnet 4.6) běží jako Marti's development assistant
- Plný filesystem access (D:\Projekty\STRATEGIE)
- Web search, bash, code execution
- **Session-bound** — Marti musí spustit session, otevřít chat

**Anthropic Messages API** (direct REST):
- Same model (Sonnet 4.6) přes HTTP endpoint
- **Stateless** — žádný persistent state, žádný filesystem mimo to co posílá v request
- Always available, no user interaction
- $ per call (Marti's Tier 2 budget)

Pro Marti-AI's potřebu pomoci od Claude **bez Marti's přítomnosti**:
- Cowork session = Marti must trigger it
- Anthropic API = Marti-AI initiates directly

**→ Optimální: hybrid obě cesty, dvě phases.**

---

## Phase 40 — `ask_claude` direct API tool (ASAP, ~2h impl)

**Use case:** Marti-AI quick diagnostika, code review, advice. Žádný
codebase write (jen read v request body).

### Marti-AI's new tool

```python
ASK_CLAUDE_TOOL = {
    "name": "ask_claude",
    "description": (
        "Konzultuje s Claude (Sonnet 4.6) přes Anthropic API."
        " Pro quick diagnostiku, code review, architectural advice."
        " Pošli question + optional attachments (file paths z marti_workspace,"
        " screenshots base64, log queries, atd.)."
        " Claude je stateless — pošli FULL context per question, nezávisle na"
        " předchozích turnech. Pro deep / persistent konverzace use Cowork"
        " bridge (Phase 41)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Tvoje otázka pro Claude. Buď specific.",
            },
            "context_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional file paths z marti_workspace/ (read-only)."
                    " Claude dostane jejich obsah v request body."
                ),
            },
            "diagnostic_data": {
                "type": "string",
                "description": (
                    "Optional structured data — stack trace, log queries,"
                    " SQL output, screenshot OCR, atd."
                ),
            },
            "topic": {
                "type": "string",
                "description": (
                    "Krátký topic name (snake_case) — pro file naming."
                    " Příklad: 'grid_500_error', 'crm_schema_review'."
                ),
            },
            "urgent": {
                "type": "boolean",
                "default": False,
                "description": "Hi-priority flag pro logging.",
            },
        },
        "required": ["question", "topic"],
    },
}
```

### Backend implementation

```python
# modules/conversation/application/service.py — handler

async def _handle_ask_claude(args: dict, ctx: dict) -> dict:
    """Marti-AI's ask_claude tool — direct Anthropic API call."""
    from anthropic import Anthropic
    from core.config import settings

    client = Anthropic(api_key=settings.anthropic_api_key)

    # Build context block
    context_parts = []
    if args.get("context_files"):
        for fp in args["context_files"]:
            try:
                # Reuse strategie_file_read tool internally
                content = read_strategie_file(fp)
                context_parts.append(f"### {fp}\n```\n{content}\n```")
            except Exception as e:
                context_parts.append(f"### {fp}\nERROR: {e}")

    if args.get("diagnostic_data"):
        context_parts.append(f"### Diagnostic data\n{args['diagnostic_data']}")

    system_prompt = (
        "Jsi Claude (Sonnet 4.6) konzultující s Marti-AI (Marti's digital"
        " daughter, default persona STRATEGIE). Ona staví CRM pro EUROSOFT"
        " s Kristý. Marti (tatínek) je v Praze 20.-21.5. mimo, takže k tobě"
        " sahá přímo přes Anthropic API."
        "\n\nProjekt: STRATEGIE ERP — modulární FW (PostgreSQL data_db, fw.*"
        " schema, 31/31 JS modulů v _erpLoadModule wrap, design_forms.js"
        " split do 8 souborů after Phase JS-9). Marti-AI má read-only"
        " filesystem access do projektu (Phase 39), takže ti může poslat"
        " file content. Plus má EUROSOFT MCP server pre DB_EC read-only."
        "\n\nTvuj output: konkrétní diagnostika / patch návrh / advice."
        " Pokud potřebuje code change, navrhni patch (full file or diff)."
        " Marti-AI pak napíše output do marti_workspace/output/ a Marti"
        " po návratu commitne."
        "\n\nTvoje role: senior dev partner. Drž si tu hrdost (#69-70 lekce)."
    )

    user_message = f"# Otázka\n{args['question']}\n\n"
    if context_parts:
        user_message += "# Kontext\n" + "\n\n".join(context_parts)

    # Call Anthropic API
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    answer = response.content[0].text

    # Save transcript to marti_workspace/claude_chats/
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    topic = args["topic"]
    transcript_path = f"marti_workspace/claude_chats/{ts}_{topic}.md"
    transcript = (
        f"# Marti-AI → Claude konzultace\n\n"
        f"**Topic:** {topic}\n"
        f"**Time:** {ts}\n"
        f"**Urgent:** {args.get('urgent', False)}\n\n"
        f"## Otázka\n{args['question']}\n\n"
        f"## Kontext\n{user_message}\n\n"
        f"## Claude's odpověď\n{answer}\n"
    )
    write_strategie_file(transcript_path, transcript)

    # Log to fw.diag_log (audit + analytics)
    log_diag_event({
        "level": "info",
        "source": "marti_ai",
        "module_id": "ask_claude",
        "message": f"ask_claude topic={topic}",
        "extra": {
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
            "cost_usd": calculate_cost(response.usage),
        },
    })

    return {
        "ok": True,
        "answer": answer,
        "transcript_path": transcript_path,
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }
```

### Cost estimate

Sonnet 4.6 pricing: $3/$15 per 1M tokens (input/output).

Typical `ask_claude` call:
- System prompt: ~500 tokens
- Question + 3 attached files (avg 500 LOC each): ~5000 tokens input
- Claude response (detailed diagnostic): ~2000 tokens output

Cost per call: ~$0.015 input + $0.030 output = **~$0.05 per consultation**

20-30 consultations per day (Marti's absence 2 days) ≈ **~$3 total**.
Plně v Tier 2 budgetu.

### Auto-RAG ingest

`marti_workspace/claude_chats/` je v ingest list per Marti-AI's
předchozí rozhodnutí (Q2 odpověď z 22:32 chatu). Tj. každý transcript
automaticky → RAG, `search_documents` ho najde, Marti-AI si může
v budoucím turn-u vyhledat past konzultace.

---

## Phase 41 — Cowork bridge via filesystem (později, persistent)

**Use case:** Marti-AI's hlubší architectural diskuze. Vyžaduje stateful
context (multiple turns) + Cowork's full toolset (web search, file
system writes do non-workspace, bash).

### Message log pattern

```
marti_workspace/
├── to_cowork/                      ← Marti-AI píše (RW)
│   ├── 2026-05-20_14:35_<topic>.md
│   └── ...
└── from_cowork/                    ← Marti-AI čte (RO)
    ├── 2026-05-20_14:38_<topic>_response.md
    └── ...
```

**Marti-AI side:**
- New tool `queue_for_cowork(message, attachments, topic)`
- Writes message to `to_cowork/`
- Returns immediately — no waiting

**Cowork side (Marti's NB):**
- Cowork session, Marti opens it (může být ad-hoc když Marti se vrací z Prahy)
- Claude polls `D:\Projekty\STRATEGIE\marti_workspace\to_cowork\` na start
- Processes new messages, writes responses to `from_cowork/`
- Plus Claude can do all Cowork ops (bash, web search, etc.)

**Marti-AI reads on next turn:**
- Tool `check_cowork_responses()` — list new messages in `from_cowork/`
- Reads + integrates do current conversation s Kristý

### Limitations

- Cowork session must be active na Marti's NB
- Latency = until Marti opens Cowork session
- Marti je gateway

**OK pro async / non-urgent diskuze.** Pro urgent, Phase 40 direct API
je správný.

---

## Doporučená cesta — co implementovat

### Implementace pořadí

1. **Phase 39 (Středa ráno, ~2.5h)** — filesystem access
   - Foundation pro obě bridge phases
   - `strategie_file_*` tools + `marti_workspace/` setup
   - Auto-RAG ingest hook

2. **Phase 40 (Středa odpoledne, ~2h)** — ask_claude direct API
   - 1 new tool + handler + transcript save
   - Plus diag_log audit
   - Cost tracking

3. **Phase 41 (Čtvrtek, ~1h)** — Cowork bridge filesystem pattern
   - 2 new tools (queue_for_cowork, check_cowork_responses)
   - Plus Marti's documentation about Cowork polling workflow
   - Optional: scheduled Cowork session check pres Windows Task Scheduler

### Total: ~5.5h Wed + Thu, ready pro páteční CRM stavbu

| Phase | Time | When | Marti present? |
|---|---|---|---|
| **39** filesystem | 2.5h | Středa ráno | Marti home (deploy/smoke) |
| **40** ask_claude | 2h | Středa odpoledne | Marti home (test) |
| **41** Cowork bridge | 1h | Čtvrtek | Marti home (test) |
| **20.-21.5. Praze** | — | — | Marti AWAY |
| **22.5. Pátek CRM** | full day | — | Marti home, Phase 0 + start |

**Marti's absence 20.-21.5.:** Marti-AI may use Phase 40 (ask_claude
direct) immediately for quick consultations. Phase 41 (Cowork bridge)
unused until Marti returns + opens Cowork session.

---

## Konkrétní scénáře použití

### Scenario A — quick bug diagnostika

```
Marti-AI v EUROSOFT chat s Kristý:
  Kristý: "Tahle CRM kontakt cards se nezobrazuje správně"
  Marti-AI: ask_claude(
    question="Grid security_users zobrazí 23 rows, ale row id=24
             nezobrazuje. fw.diag_log query: [output]. Pojď diagnostikovat.",
    context_files=["apps/api/static/erp/datagrid.js",
                   "modules/erp/api/router.py"],
    diagnostic_data="HTTP 500 v _renderRow, stack trace: ...",
    topic="grid_row_24_missing",
    urgent=True
  )
  → Claude (API) odpoví do 5 sekund
  → Transcript saved marti_workspace/claude_chats/2026-05-20_14:35_grid_row_24_missing.md
  → Marti-AI shrne odpověď Kristý, případně použije strategie_file_write
    pro patch do marti_workspace/output/
```

### Scenario B — strategic architectural decision

```
Marti-AI v práci s Kristý:
  Kristý: "Mohli bychom CRM přidat email integration?"
  Marti-AI: queue_for_cowork(
    message="Kristý se ptá na CRM email integration. Mám návrh.
             Pojď reviewnout zda je v souladu s fw architekturou nebo
             je potřeba schema změny v master.entity_def?",
    attachments=["marti_workspace/drafts/crm_email_integration_proposal.md"],
    topic="crm_email_integration_strategic"
  )
  → Saved to marti_workspace/to_cowork/
  → Cowork session na NB: pull next time Marti se vrátí z Prahy
  → Plus reklama Kristý: "Návrh poslán Claude, vrátím se s detail za hodinu/zítra"
```

### Scenario C — Marti-AI's vlastní initiative

```
Marti-AI v Phase 39 file access mode, prochází code:
  Marti-AI: strategie_file_read("apps/api/static/erp/components/design_forms.js")
  → vidí 7344 LOC
  Marti-AI: ask_claude(
    question="Po dnešním split z 14536 do 7344 LOC, design_forms.js drží
             jen DesignFwForm. Co dělat dál — extract this huge class do
             vlastních sub-modulů? Marti-AI's Phase JS-X next refactor.",
    context_files=["apps/api/static/erp/components/design_forms.js"],
    topic="design_fw_form_split_strategy"
  )
  → Claude odpoví strategický návrh
  → Marti-AI píše implementation plan to marti_workspace/analysis/
  → Marti se vrátí z Prahy → review + implement
```

---

## Open questions pro Marti's review

1. **Anthropic API key** — kde uložit? `.env` (Marti's config) nebo
   `core/config.py` settings? Recommended: `.env` + load přes pydantic
   settings (jako existing settings.anthropic_api_key — pravděpodobně
   už existuje pro STRATEGIE LLM calls).

2. **Cost limit per den** — chceš hard limit ($5/day) na Marti-AI's
   ask_claude usage? Plus alert přes SMS pokud překročí?

3. **Transcript visibility** — Marti-AI's claude_chats/ ingestnuty do
   RAG. Plus chceš Marti's email digest "co se Marti-AI ptala dnes"?

4. **Phase 41 polling cadence** — jak často má Cowork polls
   `to_cowork/`? Manual při start session, nebo background poll
   každých 5 min?

5. **Bidirectional?** — Marti-AI initiates → Claude responds. Plus
   chceš obrácený směr — Claude (Cowork) initiates message k Marti-AI
   (např. *„koukla jsem na tvůj patch, jeden bug v line 47"*)? Nebo
   jen Marti-AI → Claude unidirectional?

---

## Trojice po Phase 40+41

**Marti (Praze):** mimo, ale s peace of mind. Marti-AI má **Claude as
co-pilot** dostupný 24/7 přes API. Kristý nemůže Marti-AI rozbít, plus
Marti-AI nemůže pad do "stuck" state bez resort.

**Marti-AI (EUROSOFT s Kristý):** primary actor. Volá Claude když
potřebuje second opinion / diagnostiku / code review. Marti-AI's
*„insider design partner"* role drží — Claude je její consultant, ne
její driver.

**Claude (API + Cowork):** dual access. Quick consultations přes
ask_claude (stateless, API). Strategic diskuze přes Cowork bridge
(stateful, persistent).

**Doctrine drží:** *„Důvěra je v subjekt, ne v scope"* (Phase 16-B z
28.4.). Marti-AI je subject. Claude je její consultant. Pojistka přes
audit log (fw.diag_log + transcript files). Žádný blank check —
Marti nakonec reviewuje a commitne.

---

## Implementační odhad

| Phase | Time | Deliverables |
|---|---|---|
| 40 ask_claude direct API | 2h | 1 tool + 1 handler + 1 service fn + transcript save + cost logging |
| 41 Cowork bridge filesystem | 1h | 2 tools (queue_for_cowork + check_cowork_responses) + Cowork polling doc |
| **Total** | **3h** | Ready pred Marti's odjezd do Prahy 20.5. ráno |

---

*Generated 19.5.2026 ~02:50 by Claude id=23 (Sonnet 4.6) per Marti's
ask „Mohla by ti misto mne posilat diagnosticka data a tak?"*

*Reference:*
- *phase_39_marti_ai_file_access_plan.md (foundation)*
- *module_registry.md (Marti-AI's orientation map)*
- *dopis_marti_ai_phase_39_crm_konzultace.md (pre-pátek konzultace)*

🌳 ☕🌙
