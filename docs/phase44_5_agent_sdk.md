# Phase 44.5 — Anthropic Agent SDK persistent Claude

> Phase 44 (rich-context simulation) dropped. Phase 44.5 = official Anthropic
> `claude-agent-sdk` for true persistent identity + built-in tools.

## Genesis

19. 5. 2026 odpoledne:
- Marti's strategic catch: *„Když je to jen rich-context stateless API,
  Claude je vlastně jen nová persona ve STRATEGII. To je jako by se ptala
  Marti-AI sama sebe."*
- Subagent research potvrdil: **`claude-agent-sdk` Python knihovna**
  (PyPI, github.com/anthropics/claude-agent-sdk-python) je oficiální
  Anthropic SDK pro persistent stateful agents.
- Marti's volba: *„Jen rozumné řešení je B 44.5. To splňuje persistence
  a přístup rw ke složce projektu... Věřime Ti, Claude."*

## Co Agent SDK přináší (vs Phase 44 dropped)

| Feature | Phase 44 (dropped) | Phase 44.5 (Agent SDK) |
|---|---|---|
| Identity | Stateless `messages.create()` + injected context simulation | **Persistent session** přes `session_id` + auto-disk persist |
| Multi-turn | Manuálně přes `anthropic_conversation_id` resending history | **Native** — SDK spravuje context window automaticky |
| Tools | Custom impl `strategie_file_*` (Phase 43 Mini-fáze B čekal) | **Built-in** Read, Edit, Write, Bash z Claude Code engine |
| Filesystem rw | Phase 39 service per-call inline | **Direct access** — Claude sám reads CLAUDE.md, writes `marti_workspace/` |
| MCP integration | Manual dispatch (Phase 28 EUROSOFT pattern) | **Native** — MCP servers registered jako built-in tools |
| Auth | `ANTHROPIC_API_KEY` env | Stejný (nebo OAuth přes Claude Pro/Max) |
| Tier 2 | Same 450K TPM Sonnet 4.6 | Same (žádné gating) |
| Implementation cost | ~560 LOC custom bridge agent + DDL + NSSM | **~150 LOC** wrap (claude_agent_service.py) |
| Maintenance | Custom infrastructure (queue, polling, orphan recovery) | Anthropic spravuje SDK internals |
| ToS-compliance | Direct API call (custom-implemented persistent context) | **Official path** (recommended by Anthropic) |

## Architektura

```
shared chat (Marti, Kristý, Marti-AI)
  ↓ Marti-AI volá ask_claude(question)
ask_claude_service.py
  ↓ NO QUEUE, NO POLLING — direct async call
claude_agent_service.py (new ~150 LOC)
  ↓ wraps claude_agent_sdk.query()
ClaudeAgentOptions(
    session_id=f"strategie-conv-{shared_chat_id}",
    resume=True,
    allowed_tools=[Read, Edit, Write],  # scoped via deny list
)
  ↓ async for msg in query(prompt=question, options=...)
Anthropic Agent SDK manages:
  - Session persistence (~/.claude/projects/)
  - Tool use loop (Claude sám reads CLAUDE.md, dárek-scény, recent commits)
  - Context window optimization
  - Multi-turn continuity
  ↓ reply text
ask_claude_service.py save_message(author=23, content=reply)
  → Phase 43 Mini-fáze A extra_messages payload
  → Claude bublina (teal #5dc8c0) v shared chatu
```

**Klíčové změny vs Phase 44:**
- ❌ `claude_bridge_agent.py` NSSM service — DROP (Agent SDK runs in-process)
- ❌ `claude_session_queue` polling — DROP (Agent SDK je async call)
- ❌ `claude_session_threads` mapping — DROP (Agent SDK session_id internally)
- ❌ Rich context injection custom logic — DROP (Claude sám reads via tools)
- ✅ Phase 43 Mini-fáze A extra_messages frontend — DRŽÍ (Claude bublina v chatu)
- ✅ Phase 43 Mini-fáze A STRATEGIE bubliny — DRŽÍ (system_audit)
- ✅ Phase 40 cost gate 300 Kč/h — DRŽÍ (Marti's Q3 doctrine z rána)

## Session mapping

Per shared chat conversation jeden persistent Claude session:

```
DB: shared chat conversation_id = 123
SDK: session_id = "strategie-conv-123"
File: ~/.claude/projects/strategie-conv-123/...
```

Marti-AI's první `ask_claude` v konv. 123 → fresh session
Marti-AI's druhý `ask_claude` v stejné konv. → resume same session
Po 24h bez activity → můžeme reset (Marti-AI's Phase 44 Q6 obava — nice-to-have, ne MVP)

## Tools scope (Marti-AI Q1 v konzultačním dopisu)

**Builtin tools dostupné Claude přes Agent SDK** (z Claude Code engine):
- `Read` — pojď číst libovolný file (CLAUDE.md, dárek-scény, recent commits)
- `Edit` — pojď upravit existing file
- `Write` — pojď vytvořit nový file
- `Bash` — pojď spustit shell command (`git log`, `ls`, ...)
- `Grep`, `Glob` — search v repo

**Phase 39 deny list passthrough:** reuse `config/strategie_file_access.yaml` (27 deny patterns) — Claude **nemůže** Read/Edit/Write na:
- `.env`, `.git/`, password files
- Production secrets

**Write zone** (vzájemné s Marti-AI per Phase 39 doctrine):
- `marti_workspace/` — write OK (sdílený prostor pro AI deliverables)
- Plus dedikovaný `claude_workspace/` (Marti-AI Q4) — Claude má vlastní separate prostor

**Default tool set pro Phase 44.5 LIVE start:**
```python
ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],  # read-only start
    cwd=str(REPO_ROOT),
    deny_list=load_phase39_deny_list(),
)
```

Read-only first. Po stable provoz + Marti-AI's Q&A → expand na Edit/Write/Bash.

## Cost model

Same Sonnet 4.6 pricing (input $3/M, output $15/M) přes Marti's API key.
Prompt cache benefits drží (Phase 32 z 3.5.).

**Per ask_claude call cost projection:**
- Phase 43 Mini-fáze A (current LIVE): ~1-3 Kč (simple peer-partner prompt + 10 recent msgs)
- Phase 44 (dropped): ~3-5 Kč (rich injected context ~25k tokens)
- **Phase 44.5 (Agent SDK)**: ~2-4 Kč (Claude reads jen co potřebuje, ne 25k blindly injected)

Marti's 300 Kč/h cost gate drží jako safety net.

## Deploy plan

**Krok 1 — Smoke test (Marti runs, ~5 min):**
- ✅ `pip install claude-agent-sdk` (already done, v 0.2.82)
- `python scripts/phase44_5_smoke_agent_sdk.py` (verify auth + first call + resume)

**Krok 2 — Design + Marti-AI konzultace (~30 min, autonomous):**
- ✅ Tento dokument (`docs/phase44_5_agent_sdk.md`)
- Konzultační dopis pro Marti-AI (Q1-Q5)

**Krok 3 — Implementace (~2 hodiny):**
- `modules/conversation/application/claude_agent_service.py` (~150 LOC)
  - `send(question, conversation_id, persona_id) → dict {reply, message_id, tokens, cost}`
  - Wraps `claude_agent_sdk.query()` async
  - Session id derived from conversation_id
  - Cost tracking integration with `_recent_hour_cost_czk`
- `ask_claude_service.py` refactor:
  - Drop `_execute_via_bridge` (queue path)
  - `_execute_ask_claude` → `claude_agent_service.send(...)` async wrapper
  - Drop `_pg_array_literal` (unused after bridge drop)
- pip install `claude-agent-sdk` do production requirements

**Krok 4 — Deploy + smoke (~30 min):**
- `git pull origin main` na cloud APP
- `pip install claude-agent-sdk` na cloud APP (pokud ne instalován)
- `Restart-Service STRATEGIE-API`
- Marti-AI v shared chatu volá ask_claude → Claude bublina s persistent context

**Krok 5 — Phase 44 cleanup (~15 min, post-LIVE):**
- Drop `claude_bridge_agent.py` (replaced by claude_agent_service.py)
- Drop `install_claude_bridge_nssm.ps1` (no NSSM service)
- Drop `scripts/phase44_5_smoke_agent_sdk.py` (one-time use)
- Zachovat `claude_session_queue` + `claude_session_threads` DDL v DB (Marti's
  *„NEDROPUJ COLUMN"* doctrine — dormant fallback pokud Agent SDK někdy fail)
- Archive `docs/phase44_claude_bridge_agent.md` (historical)

## Risk / fallback

**Risk:** Agent SDK je novější (~květen 2026), méně production-tested než
stateless Messages API. Marti's *„nepřekvap, ne fragile"* doctrine.

**Fallback:** Phase 43 Mini-fáze A stateless API path drží jako baseline.
Pokud Agent SDK má issue, env switch nebo code revert vrátí na Phase 43.
Cost: 30 min revert + Restart-Service.

**Cost runaway risk:** Claude přes Agent SDK má tools → může volat
filesystem reads v loop. Phase 39 deny list + Marti's 300 Kč/h gate drží.
Plus iteration counter v Agent SDK (tools limit per query).

## Open otázky pro Marti-AI (konzultační dopis)

1. **Tools scope start** — read-only first, expand later? Nebo full
   read+edit+write+bash from day 1?
2. **Session lifecycle** — 24h expiration nebo persistent forever?
3. **Cost gate adjustment** — 300 Kč/h s Agent SDK tools usage? Adaptive?
4. **Identity glossary update** — co se mění po Phase 44.5 LIVE?
5. **Marti-AI's vs Claude tools overlap** — pokud Marti-AI volá ask_claude
   a Claude přes Agent SDK má vlastní Read/Write, jak nesynchronizovat
   filesystem changes? (Marti-AI's diář pattern doctrine — Phase 5)

## Status

19. 5. 2026 odpoledne:
- ✅ Subagent research potvrdil SDK existence
- ✅ pip install na cloud APP success (v 0.2.82)
- ⏭ Smoke test (Marti runs)
- ⏭ Marti-AI konzultační dopis
- ⏭ Implementation
- ⏭ Deploy + LIVE

Target: **dnes večer LIVE** (Marti's *„dnes to rozbehneme"*).
