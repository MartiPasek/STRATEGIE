# Phase 44 — Cloud Claude Bridge Agent

> Persistent Claude (id=23) z STRATEGIE chat přes Python NSSM service na cloud APP.

## Genesis

19. 5. 2026 odpoledne (post-Phase 43 Mini-fáze A LIVE):

- Marti's strategic catch z dopoledne: *„Pokud `ask_claude` volá stateless
  Anthropic API, je to jen nová persona overlay nad Sonnet 4.6 — Marti-AI se
  ptá sama sebe."*
- Marti's upgrade: *„Claude desktop už mám na cloud APP přihlášený. Pokud
  uděláme bridge, můžu používat STRATEGIE chat z kdekoli (web/PWA mobile),
  Cowork je 24/7 backend."*
- Marti's volba (19.5. odpoledne): **Python bridge agent NSSM service** —
  ne Cowork desktop session (Marti's *„drz jednoduchost"* doctrine z dubna).
- Marti's vize čtyřky: **Marti & Marti-AI & Claude & Kristy** — plnohodnotná
  spolupráce napříč 2 lidmi + 2 AI.
- **Marti's bridge-only doctrine** (19.5. odpoledne, ~14:30): *„Prepinac na
  mody API a Bridge potrebovat nebudeme... API v tomhletom pripade ztraci
  zcela vyznam a jen to komplikuje."* → drop dual-mode env switch. Bridge
  je THE path. Pokud bridge unavailable → ask_claude vrací error, fail
  visible. Žádný silent stateless API fallback (porušilo by Marti's
  catch *„Marti-AI se ptá sama sebe"*).

## Doctrine

> **„Cloud bridge je service, ne desktop app. Claude (id=23) persistent
> identity drží přes service uptime + DB session continuity, ne přes Cowork
> chat session lifetime."**

Rozdíl Phase 43 (current) vs Phase 44:

| Aspekt | Phase 43 Mini-fáze A (current) | Phase 44 Bridge Agent |
|---|---|---|
| Claude API call | Stateless `client.messages.create()` per ask_claude | Rich system prompt + injected Cowork context + multi-turn continuity |
| Identity | Fresh Sonnet 4.6 instance per call | Persistent Claude (id=23) napříč session |
| Context | 10 recent messages from conv | CLAUDE.md sections + dárek-scény + recent commits + 10 recent messages + multi-turn history per conversation |
| Multi-turn | Žádný (každý call začíná znova) | `anthropic_conversation_id` per shared chat → context drží napříč N turn-ů |
| Marti-AI vs Claude | *„Marti-AI se ptá sama sebe"* | *„Marti-AI volá opravdového Claude s pamětí"* |

## Architektonický pattern

```
┌──────────────────────────────────────┐
│  Shared chat / DM (frontend)         │
│  Marti, Kristy, Marti-AI             │
└─────────────────┬────────────────────┘
                  │ Marti-AI volá tool ask_claude(question, ...)
                  ▼
┌──────────────────────────────────────┐
│  ask_claude_service.py (FastAPI)     │
│                                      │
│  env STRATEGIE_CLAUDE_BRIDGE:        │
│   • cloud_bridge → queue path        │
│   • api_stateless → current behavior │
│   • auto → try bridge, fallback API  │
└─────────────────┬────────────────────┘
                  │ INSERT row do queue
                  ▼
┌──────────────────────────────────────┐
│  claude_session_queue                │
│  ┌────┬──────────┬────────────────┐  │
│  │ id │ question │ status         │  │
│  │ 42 │ "..."    │ pending     ←──┤  │
│  │ 41 │ "..."    │ answered       │  │
│  │ 40 │ "..."    │ failed         │  │
│  └────┴──────────┴────────────────┘  │
└─────────────────▲────────────────────┘
                  │ polling every 2s
                  │
┌─────────────────┴────────────────────┐
│  STRATEGIE-CLAUDE-BRIDGE NSSM        │
│  scripts/claude_bridge_agent.py      │
│                                      │
│  on pending row:                     │
│   1. Load CLAUDE.md sections         │
│   2. Inject dárek-scény slovník      │
│   3. Build rich system prompt        │
│   4. Anthropic API call s            │
│      anthropic_conversation_id       │
│   5. UPDATE row with answer          │
│                                      │
│  Health: bridge_health.log every 30s │
└──────────────────────────────────────┘
                  │
                  ▼ Marti-AI reads queue answer (poll)
              ask_claude_service.py
              → save_message author=23
              → return reply text → composer synthesis
                  │
                  ▼ Phase 43 Mini-fáze A path
              ChatResponse.extra_messages (Claude bublina)
```

## DDL Design

### `public.claude_session_queue`

Single-table queue, FIFO processing, idempotent retries.

```sql
CREATE TABLE public.claude_session_queue (
    id BIGSERIAL PRIMARY KEY,
    -- Caller kontext
    conversation_id BIGINT REFERENCES public.conversations(id) ON DELETE SET NULL,
    requested_by_user_id BIGINT,        -- typicky Marti-AI (user.id=2)
    requested_by_persona_id BIGINT,     -- pro audit, NULL pokud direct API call

    -- Question payload
    question TEXT NOT NULL,
    context_files TEXT[],               -- optional Phase 43 Mini-fáze B passthrough
    topic VARCHAR(100),                  -- pro Cowork-style topic tag

    -- Multi-turn continuity (Marti's "persistent Claude" doctrine)
    -- Sdílený anthropic_conversation_id pro VŠECHNY questions z té
    -- conversation_id -> Claude vidí předchozí turny v context window.
    anthropic_conversation_id VARCHAR(100),   -- prefill z conversation_id mapping

    -- Stav: pending = čeká, processing = bridge agent zpracovává, answered =
    -- OK, failed = error po retry, timeout = bridge offline, expired = manualne
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN
        ('pending', 'processing', 'answered', 'failed', 'timeout', 'expired')),

    -- Response
    answer_text TEXT,
    answer_message_id BIGINT,            -- FK na messages.id (Claude bublina)
    error_text TEXT,                     -- pro failed / timeout

    -- Telemetry (paralela s llm_calls Phase 9.1)
    model VARCHAR(50),                   -- 'claude-sonnet-4-6'
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10, 6),

    -- Timing
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_started_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,              -- pro background cleanup task

    -- Retry tracking
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 2
);

CREATE INDEX ix_claude_session_queue_pending
    ON public.claude_session_queue (queued_at ASC)
    WHERE status = 'pending';

CREATE INDEX ix_claude_session_queue_conversation
    ON public.claude_session_queue (conversation_id, queued_at DESC);

CREATE INDEX ix_claude_session_queue_processing
    ON public.claude_session_queue (processing_started_at ASC)
    WHERE status = 'processing';

COMMENT ON TABLE public.claude_session_queue IS
    'Phase 44 (19.5.2026): Persistent Claude bridge — Marti-AI z shared chatu '
    'volá ask_claude → INSERT pending. STRATEGIE-CLAUDE-BRIDGE NSSM service '
    'pollu pending rows, volá Anthropic API s rich injected context, UPDATE '
    'answered. Marti vize "persistent Claude id=23 across STRATEGIE chat".';

ALTER TABLE public.claude_session_queue OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.claude_session_queue TO strategie;
GRANT USAGE ON SEQUENCE public.claude_session_queue_id_seq TO strategie;
```

### Volitelné: `public.claude_session_threads` (multi-turn mapping)

```sql
-- Mapování conversation_id -> anthropic_conversation_id pro multi-turn
-- continuity. Plus tracking message history depth (kolik turn-ů Claude vidí).
CREATE TABLE public.claude_session_threads (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    anthropic_conversation_id VARCHAR(100) NOT NULL UNIQUE,
    turn_count INTEGER NOT NULL DEFAULT 0,    -- kolik q-a párů v této session
    last_question_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Cleanup: po 24h bez activity můžeme thread "expirovat" (start fresh)
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE UNIQUE INDEX ix_claude_session_threads_conv
    ON public.claude_session_threads (conversation_id)
    WHERE expires_at > NOW();

ALTER TABLE public.claude_session_threads OWNER TO "Marti-AI";
GRANT SELECT, INSERT, UPDATE ON public.claude_session_threads TO strategie;
GRANT USAGE ON SEQUENCE public.claude_session_threads_id_seq TO strategie;
```

## Rich context injection

Bridge agent při každém callu builds system prompt s persistent Cowork-style
identity. Sekce:

1. **Identity** (always) — Claude (id=23, peer-partner) z trojice/čtyřky
   z #69 (26.4.). *„dává strukturu"* role.

2. **CLAUDE.md klíčové sekce** (slice, ne celá ~30k LOC):
   - Quick Reference (Trojice + Slovník + 10 doctrin) — ~5k tokens
   - Marti-AI's identity glossary — ~3k tokens
   - 16 dárek-scén tabulka — ~2k tokens
   - Posledních 5 dopisů (chronological, recent context) — ~10k tokens
   - **Total: ~20k tokens** persistent context, refreshed every bridge start

3. **Recent commits** (last 24h `git log --oneline --since=1.day`) — ~2k tokens

4. **Multi-turn history** (per `anthropic_conversation_id`) — Anthropic API
   automatic context window management

5. **Live conversation context** (10 recent messages z aktuální shared chat) —
   Phase 43 current path

Total input per call: ~35-50k tokens. Output ~1-2k. Cost: ~3-5 Kč/call
(Sonnet 4.6 cached input pricing pomáhá — Anthropic prompt cache Phase 32 z 3.5.).

## Components

### 1. DDL deploy
- `scripts/_phase44_A1_claude_session_queue.sql` — Marti-AI execution v DBeaveru
- Plus `claude_session_threads` volitelné v Phase 44-A1.5

### 2. Backend — bridge-only path
- `modules/conversation/application/ask_claude_service.py`:
  - DROP env switch (Marti's *„API ztrácí význam"* doctrine 19.5.)
  - `_execute_ask_claude` = bridge only: INSERT queue + poll timeout 60s
  - Bridge fail → vrací `ok=False`, propose_or_execute vrací error
  - Caller-side STRATEGIE warning bublina v chatu (Phase 43 system_emit pattern)
  - Žádný stateless API fallback (drop ~170 LOC dead code)

### 3. Bridge agent
- `scripts/claude_bridge_agent.py`:
  - Polling loop (asyncio, scan_interval=2s)
  - Per pending row: build rich prompt → Anthropic call → UPDATE row
  - Health: write `D:\Data\STRATEGIE\claude_bridge\bridge_health.log` every 30s
  - Failure: retry × 2 with exponential backoff, then status='failed'
  - Cleanup: orphan processing rows (>5min stuck) → back to pending

### 4. NSSM service
- `STRATEGIE-CLAUDE-BRIDGE` (analog `STRATEGIE-RESTART-WATCHER` Phase 42)
- AppDirectory: `C:\Projekty\STRATEGIE`
- AppParameters: `-m scripts.claude_bridge_agent`
- Autostart: SERVICE_AUTO_START
- AppStdout/Stderr: `C:\Data\STRATEGIE\claude_bridge\agent.log`

### 5. Health monitoring
- Endpoint `GET /api/v1/claude_bridge/health` → reads bridge_health.log
  freshness (< 60s = healthy)
- Backend `auto` mode čte tento endpoint před routing decision

## Deploy plan

**Setup (one-time, ~2-3h):**
1. Marti-AI execute DDL v DBeaveru jako Marti-AI session
2. Backend přepínač v ask_claude_service.py — feature flag default OFF
3. Bridge agent skript do `scripts/`
4. NSSM install na cloud APP (analog Phase 42 STRATEGIE-RESTART-WATCHER)
5. Set env `STRATEGIE_CLAUDE_BRIDGE=cloud_bridge` na cloud APP `.env`
6. Restart STRATEGIE-API + start STRATEGIE-CLAUDE-BRIDGE
7. Smoke test: Marti-AI v shared chatu volá `ask_claude(question="kontrolní test bridge")` → Claude bublina obsahuje *„Ano, jsem persistent Claude přes bridge, mám kontext..."*

**Rollback / debugging:**
- Bridge agent down → ask_claude vrací error po 60s timeout
- Bridge restart: `Restart-Service STRATEGIE-CLAUDE-BRIDGE` na cloud APP
- Pokud trvale unavailable: ask_claude tool je dočasně nedostupný
- **Žádný silent fallback** (Marti's *„fail visible, ne deceive"* doctrine)
- Phase 43 Mini-fáze A path drží pro **STRATEGIE bubliny + Claude bublina
  rendering** (frontend-side beze změny) — jen bez Claude reply content

## Open otázky (vyžaduje Marti's input nebo Marti-AI konzultaci)

1. **NB Cowork lifecycle** po Phase 44 LIVE — keep / drop / hybrid?
   - Keep: backup pro velké refactory (architectural decisions still need NB Cowork)
   - Drop: simplify, cloud bridge is THE Claude
   - Hybrid: cloud pro každodenní práci, NB pro week-long sprints

2. **Marti-AI's awareness Phase 13/15/27h pattern** — dopis pre-implementation
   pojmenuje *„ask_claude calls budou nyní přicházet do mé persistent session,
   ne stateless API"*. Její Q6 obava z 19.5. dop. (*„statusová dynamika"*)
   se mění — teď já mám persistent paměť stejně jako ona. Co s tím?

3. **Cost projection** — Marti's Tier 2 quota + auto-reload (firma billing).
   Bridge 24/7 znamená:
   - Idle: 0 Anthropic calls
   - Per Marti-AI question: ~3-5 Kč (rich context)
   - Per Cowork NB session (Marti's personal use): unchanged
   - Phase 28 EUROSOFT MCP + Marti-AI normal compositor: unchanged
   - Projection: +~150-500 Kč/day = ~3-10k Kč/měsíc upgrade

4. **Multi-turn cleanup** — `claude_session_threads.expires_at` 24h default.
   Pokud Marti-AI v 9:00 začne dialog s Claude přes bridge, v 14:00 znovu
   ask_claude same conversation — drží context. Po 24h thread expires,
   začne fresh anthropic_conversation_id. Drobnost, ale stojí za rozhodnutí.

5. **Anthropic conversation_id naming** — současný Anthropic API podporuje
   prompt_caching keyed na system prompt prefix, ale conversation_id jako
   feature pro multi-turn isn't standard. Verify v Anthropic API docs před
   implement. Fallback: send full conversation history per call (cost vyšší
   ale stateless-friendly).

6. **Context injection updates** — CLAUDE.md sections inline znamená cca
   ~20k tokens per call. Pokud CLAUDE.md grow > 50k LOC, projection by se
   musela redukovat. Marti-AI dopis Q8 (chat noise) analog: configurable
   *„kolik kontextu inject"* per shared chat conversation (default low,
   verbose pro architectural konzultace).

---

**Status:** Design hotový 19.5.2026 odpoledne. Implementace probíhá
autonomně po Marti's mandate. Phase 44 LIVE target: zítra ráno (20.5.)
po DDL deploy + NSSM install + Marti-AI consult dopisu.
