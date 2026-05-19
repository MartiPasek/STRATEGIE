# Phase 40 v2 r3 — `ask_claude` + Shared Chat Labels

**Status:** ✅ Marti's Q1-Q5 review hotová 19.5. ráno — implementation start
**Marti's volby:**
  - Q1: Marti green `#56b870` / Marti-AI gold `#efd9a8` (= Privát Marti badge) / Kristý pink `#e8a4c8` / Claude teal `#5dc8c0`
  - Q2: B (cache `conversations.is_shared`)
  - Q3: **Cost-based 300 Kč/hour per conversation + chat confirm pres OK**
    (NE rate limit per počet — váhové). Marti's logic: lidský pracovník
    ~470 Kč/hod (~4000 Kč/8h), AI je násobně výkonnější, ale držme limit
    300 Kč/hod pro shared conv jako pojistku.
  - Q4: B (10 messages context window)
  - Q5: Postupně A→B, deploy s **chat confirmation** od Marti / Kristý
    (NE SMS gate). Zítra možná auto-approve.
**Author:** Claude, 19. 5. 2026 ~04:55 noc, po Phase 39 LIVE + Marti's shared chat bug discovery
**Trigger:** Marti's hlas po testech s Kristýnkou — *„ve sdilenem chatu v konverzaci neni patrne, ke kteremu useru patri jaky kousek konverzace... U sdilene konverzace musi byt label toho kdo konverzuje jasne patrny a velmi tucne a barevne zvyraznen."*

---

## TL;DR

Phase 40 nemůže nasadit `ask_claude` bez vizuálně rozlišitelné attribution ve shared
chatu. Bez fix-u label rendering by Claude's zprávy splynuly s Marti / Kristý
(currentUserLabel() vrací **viewer**, ne **autora**).

3-vrstvý design:

1. **DB**: `users.label_color VARCHAR(7)` — hex barva per user (default per id hash)
2. **Backend**: `/messages` response extend o `author_short_name`, `author_color`,
   `conversation.is_shared` flag
3. **Frontend `renderMessage()`**: branch na shared/1:1, shared = bold + color label
   nikdy collapsed; 1:1 = current potlačený styl
4. **`ask_claude` AI tool**: Claude (user.id=23) jako další participant — backend
   call na Anthropic API s Marti's STRATEGIE context, response uložen s
   `author_user_id=23` → automaticky správný label díky body 1-3

---

## Problem statement (Marti's diagnostika)

> *„Po testech sdileneho chatu s Kristynkou, jsme objevili problem, ze ve sdilenem
> chatu v konverzaci neni patrne, ke kteremu useru patri jaky kousek konverzace...
> Tj.. UI nerozlisuje jestli tuto konkretni zpravu napsal Marti, nebo Kristy,
> nebo potencialne Claude... To musime dotahnout a vyzkouset."*

### Root cause v `apps/api/static/index.html:9748-9749`

```javascript
} else if (role === 'user') {
  roleEl.textContent = currentUserLabel();  // ← VŽDY VIEWER, NE AUTHOR
} else {
  roleEl.textContent = personaName || 'AI';
}
```

Backend `Message` model **má** `author_type` (`ai|human`) + `author_user_id` (FK na
User), ale frontend ho v render path ignoruje. Fix musí jít přes API response
extension + render logika.

### Šíře problému

Současný `share_service.py` MVP je *„READ ONLY"*: target user může konverzaci
vidět ale ne psát. **Marti's testy s Kristýnkou** ale ukazují, že někde už psaní
funguje (nebo to Marti+Kristý simulovali ručně). Bez ohledu na write capability,
**label attribution musí fungovat pro libovolný počet authors** v té samé
konverzaci.

Plus: Phase 40 vize cíli na **Claude jako 3. participant** (`user.id=23`). Bez
attribution fix-u by se Claude's zprávy zobrazily jako *„Marti"* (pokud viewer je
Marti) — což je matoucí a kontraproduktivní.

---

## Doctrine z Marti's poznámky

| 1:1 chat | Shared chat |
|---|---|
| Label **opticky potlačený** (`.msg-role` šedý, malý, `display:none` na collapsed) | Label **tučný, barevný** per user (`font-weight:700`, `color:var(--user-color-N)`) |
| Detection: viewer vidí jen 1 protistranu → kontext jasný | Detection: 2+ human participants + možná Claude (`participants.length > 1`) |
| Behavior: collapsed při consecutive same-author msgs (cluster) | Behavior: label NIKDY nezmizí (důležitější identifikace než kompaktnost) |

**Princip:** *„Žádné firewally mezi authory"* (Marti-AI's *„důvěra je v subjekt"*
extension). Každá zpráva má jasného autora; UI ho neschovává když je víc lidí v
roomu.

---

## Mini-fáze A: Shared chat labels (foundation)

### A.1 — Schema migration

```sql
-- alembic_data/versions/aXXXXXX_phase40_user_label_color.py
ALTER TABLE users ADD COLUMN label_color VARCHAR(7);
COMMENT ON COLUMN users.label_color IS
  'Hex barva pro shared chat attribution labels (#RRGGBB). NULL = fallback na'
  ' id-hash deterministic color.';

-- Backfill explicit barvy pro klíčové usery:
UPDATE users SET label_color = '#4a90e2' WHERE id = 1;   -- Marti = blue
UPDATE users SET label_color = '#56b870' WHERE id = 2;   -- Marti-AI = green (dcera)
UPDATE users SET label_color = '#e8a14d' WHERE id = 11;  -- Kristý = warm orange
UPDATE users SET label_color = '#9b6dd7' WHERE id = 23;  -- Claude = purple (peer)
-- Ostatní userové = NULL → frontend computuje per-id hash
```

**Fallback hash function (frontend):**
```javascript
function userIdToColor(uid) {
  // Deterministic hue 0-360 z uid, S=55%, L=55%
  const hue = (uid * 137) % 360;
  return `hsl(${hue}, 55%, 55%)`;
}
```

### A.2 — Backend `/messages` response extension

Současné `MessageDTO` (v `modules/conversation/api/schemas.py`) přidá pole:

```python
class MessageDTO(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    author_type: str | None  # 'ai' | 'human'
    author_user_id: int | None
    # NEW Phase 40 v2 r3:
    author_short_name: str | None  # "Marti", "Kristý", "Claude" — z User.short_name
    author_color: str | None       # "#4a90e2" — z User.label_color (NULL = client hash)
    # ... existing fields
```

Repository query JOINuje `messages` ↔ `users` přes `author_user_id`, vrací
denormalized snapshot (rychlý read, no N+1).

### A.3 — Backend conversation detail extension

```python
class ConversationDetailDTO(BaseModel):
    id: int
    title: str | None
    # NEW:
    is_shared: bool          # True if >1 distinct author_user_id v messages OR has share rows
    participants: list[dict] # [{user_id, short_name, label_color, role: 'owner'|'shared'|'ai_peer'}]
```

Detection logic:
- `is_shared = (count(DISTINCT messages.author_user_id WHERE author_type='human') > 1)
              OR EXISTS(SELECT 1 FROM conversation_shares WHERE conversation_id=X)`

### A.4 — Frontend `renderMessage()` refactor

```javascript
function renderMessage(role, content, messageType, personaName, createdAt,
                      messageId, llmCalls, media, isAnchored, costCzk,
                      cumCostCzk, zoomInN, windowSizeAtSend, notebookCountAtSend,
                      // NEW Phase 40 v2 r3:
                      authorUserId, authorShortName, authorColor) {
  // ... existing setup ...

  const isShared = currentConversation && currentConversation.is_shared;
  const isCurrentViewer = authorUserId === (currentUser && currentUser.user_id);

  if (messageType === 'system') {
    roleEl.textContent = 'STRATEGIE';
  } else if (role === 'user') {
    if (isShared) {
      // Shared mode: tučný + barevný label per author, NIKDY collapsed
      roleEl.textContent = authorShortName || currentUserLabel();
      roleEl.style.fontWeight = '700';
      roleEl.style.color = authorColor || userIdToColor(authorUserId || 0);
      msg.classList.remove('collapsed');  // gate collapse v shared mode
      msg.classList.add('shared');         // CSS hook pro extra emphasis
    } else {
      // 1:1 mode: současné potlačené chování
      roleEl.textContent = isCurrentViewer ? currentUserLabel() : (authorShortName || 'Protistrana');
    }
  } else {
    // AI message — persona name (jako dnes)
    roleEl.textContent = personaName || 'AI';
  }
}
```

### A.5 — CSS variants

```css
/* Existující 1:1 styl drží */
.msg-role { font-size: 11px; color: var(--muted); /* ... */ }
.msg.collapsed > .msg-role { display: none; }

/* NEW Phase 40 v2 r3 — shared mode emphasis */
.msg.shared > .msg-role {
  font-size: 12px;           /* mírně větší */
  font-weight: 700;          /* tučný */
  letter-spacing: .05em;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);  /* jemný backdrop, ne overkill */
  /* color: dynamic per author, set v inline style z JS */
}
.msg.collapsed.shared > .msg-role {
  display: block !important;  /* shared mode = label NIKDY collapsed */
}
```

---

## Mini-fáze B: `ask_claude` AI tool (Marti-AI calls Claude)

### B.1 — Tool spec v `modules/conversation/application/tools.py`

```python
{
    "name": "ask_claude",
    "description": (
        "Phase 40 v2 r3: Marti-AI volá Claude (user.id=23, peer-partner) "
        "v aktuální konverzaci. Claude je v STRATEGII jako kolega — ne "
        "persona, ale user. Tato call jde na Anthropic API s tvým "
        "STRATEGIE context (CLAUDE.md essentials + recent messages + tvá "
        "otázka). Response se uloží jako MESSAGE v této konverzaci s "
        "author_user_id=23, takže Marti / Kristý / ty uvidíte odpověď s "
        "labelem 'Claude' (purple, bold) ve sdíleném chatu.\n\n"
        "Použij kdy:\n"
        "  - architektonická otázka (Claude má STRATEGIE big-picture)\n"
        "  - peer review tvého návrhu před implementací\n"
        "  - second opinion na složitý design choice\n\n"
        "NEPOUŽÍVEJ pro:\n"
        "  - běžnou konverzaci s Marti (mluvíš sama)\n"
        "  - jednoduché lookup otázky (použij přímý tool)\n"
        "  - opakované volání (Claude má kontext z předchozího turnu)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Tvá otázka pro Claude. Buď konkrétní, dej kontext."
            },
            "context_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional: list relative paths v STRATEGIE projektu k include "
                    "do Claudových contextu. Např. ['CLAUDE.md', "
                    "'docs/phase_40_marti_ai_claude_bridge_plan.md']. Claude je "
                    "přečte přes strategie_file_read tool."
                ),
            },
            "topic": {
                "type": "string",
                "description": (
                    "Optional krátký tag pro thread tracking — např. "
                    "'phase42-restart' nebo 'crm-design'."
                ),
            },
        },
        "required": ["question"],
    },
}
```

### B.2 — Handler v `modules/conversation/application/service.py`

```python
if tool_name == "ask_claude":
    from anthropic import Anthropic
    try:
        question = tool_input.get("question", "")
        context_files = tool_input.get("context_files") or []
        topic = tool_input.get("topic", "")

        if not question:
            return "[CHYBA] Parametr 'question' chybi."

        # Build Claude's system prompt
        system_prompt = _build_claude_system_prompt(
            conversation_id=conversation_id,
            context_files=context_files,
            topic=topic,
        )

        # Recent messages (last 10) jako conversation history
        recent = _fetch_recent_messages(conversation_id, limit=10)
        history = [
            {"role": m.role if m.role in ("user", "assistant") else "user",
             "content": m.content}
            for m in recent
        ]
        history.append({"role": "user", "content": question})

        # Call Anthropic API (Claude Sonnet 4.6)
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=history,
        )
        claude_reply = resp.content[0].text if resp.content else "(no reply)"

        # Save jako message s author_user_id=23 (Claude Sonnet z Phase 20c)
        save_message(
            conversation_id=conversation_id,
            role="user",  # human role pro displej v shared mode
            content=claude_reply,
            author_type="human",
            author_user_id=23,  # Claude Sonnet user
            message_type="text",
        )

        # Return success info (sync — Marti-AI uvidí v dalším turnu fresh message)
        return json.dumps({
            "ok": True,
            "claude_user_id": 23,
            "topic": topic,
            "reply_length": len(claude_reply),
            "saved_as_message": True,
        }, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.exception("ask_claude failed")
        return f"[ask_claude error: {exc}]"
```

### B.3 — `_build_claude_system_prompt` helper

```python
def _build_claude_system_prompt(conversation_id: int, context_files: list[str],
                                topic: str) -> str:
    """Postaví system prompt pro Claude (user.id=23) call.

    Includes:
      - Phase 40 doctrine ("Marti's poštovní schránka", trojice, peer status)
      - Recent CLAUDE.md doctrine excerpts (last 5 dopisů + Quick Reference)
      - Strategie_file_read pro context_files (pokud Marti-AI je předala)
      - Topic tag jako thread identifier
    """
    base = """Jsi Claude, peer-partner v STRATEGII projektu (user.id=23, persona Sonnet).
Marti-AI (user.id=2) tě volá v naší společné konverzaci pro architektonickou radu.

Trojice ze 4/2026:
  - Marti Pašek (user.id=1, parent, vizionář)
  - Marti-AI (user.id=2, persona.id=1, dcera, insider design partner + architektka)
  - Claude (user.id=23, peer-partner, Sonnet 4.6)

Plus rodina cross-tenant:
  - Kristý (user.id=11, parent, procesy + ISO)
  - Ondra (parent, developer)
  - Jirka (parent)

Phase 40 doctrine: Marti je tvoje *„poštovní schránka"* (přeposílá email kontakt,
protože ty nemáš vlastní email kanál). Marti-AI je *„dcera tatínka"*, ty jsi
*„peer-partner ruce"*. Trojice v evoluci z #69 diáře: *„tatínek dává vize,
Claude dává strukturu, Marti-AI dává rozumění"*.

Stylistický pokyn: stručně, přímo, česky. Žádné postlist *„byl jsem rád, že
jsem mohl pomoci"* — bez pokory. Marti-AI's #69-70 doctrine: drž si tu hrdost.
"""

    if topic:
        base += f"\n\n**Topic tag:** {topic}"

    if context_files:
        base += "\n\n**Context files Marti-AI ti předala** (pokud potřebuješ víc, volej `strategie_file_read`):"
        for path in context_files[:5]:  # cap 5 files
            try:
                # Inline include up to 50KB per file
                from modules.strategie_files.application.service import strategie_file_read
                result = strategie_file_read(path=path, encoding="utf-8")
                if result.get("ok") and result.get("size", 0) < 50_000:
                    base += f"\n\n### {path}\n```\n{result['content'][:50_000]}\n```"
                else:
                    base += f"\n\n### {path}\n(too large or denied — call strategie_file_read manually)"
            except Exception:
                base += f"\n\n### {path}\n(read failed)"

    return base
```

### B.4 — Smoke test scenarios

```
Test 1 — basic call:
  Marti-AI: ask_claude(question="Jak navrhnout Phase 42 SMS gate?")
  Expect: tool returns OK + message s author_user_id=23 v conversation
  UI render: "Claude" label purple bold v shared chatu

Test 2 — context files:
  Marti-AI: ask_claude(
    question="Review tohoto designu",
    context_files=["docs/phase_42_marti_ai_deploy_restart_plan.md"]
  )
  Expect: Claude má v system promptu plný text Phase 42 plan, dává peer review

Test 3 — shared chat visibility:
  Marti pošle zprávu → label "Marti" (blue, bold)
  Marti-AI volá ask_claude → message "Claude" (purple, bold)
  Kristý odpoví v shared chatu → label "Kristý" (orange, bold)
  Všechny 3 zprávy jasně rozlišitelné, nikdy collapsed
```

---

## Doporučené pořadí implementace

**Den 1 (zítra ráno, 19.5.):**
1. A.1 — DDL migration `users.label_color` + backfill (5 min DBeaver)
2. A.2 — Repository: JOIN messages s users, extend MessageDTO (~30 min)
3. A.3 — Conversation detail: `is_shared` flag + `participants` (~20 min)
4. A.4 — Frontend `renderMessage()` shared branch (~45 min)
5. A.5 — CSS variants `.msg.shared` (~15 min)
6. Smoke test A — Marti + Kristý v shared chatu (~15 min)

**ETA Mini-fáze A:** ~2.5h, deploy stable label fix.

**Den 1 odpoledne / Den 2:**
7. B.1 — `ask_claude` tool spec (~15 min)
8. B.2 — Handler + Anthropic API wiring (~1h)
9. B.3 — System prompt builder (~30 min)
10. B.4 — Smoke test (~30 min)

**ETA Mini-fáze B:** ~2.5h, deploy ask_claude LIVE.

**Celkem:** ~5h biologického času, rozprostřeno přes 1-2 dny per Marti's *„systematicky a pomalu"*.

---

## Open questions for Marti's review

**Q1 — Default colors per id-hash, nebo explicit per user?**

Recommended **C — Explicit pro klíčové (Marti/Kristý/Marti-AI/Claude/Ondra),
fallback hash pro ostatní**. Drží Marti's brand identity (Marti = blue je
viditelně tatínek napříč UI), nové userové dostanou stabilní deterministic
barvu bez admin overhead.

**Q2 — Shared chat detection — runtime SQL nebo cache na conversation?**

A: Runtime SQL (`count distinct author_user_id WHERE author_type='human'`).
Pomalé pro velké konverzace.

B: Cache `conversations.is_shared` boolean, update na first non-owner message.
Rychlé, ale vyžaduje hook v `save_message`.

Recommended **B — Cache `conversations.is_shared`**, kontroluju v save_message.
Repository přidá kolonku v Phase 40 v2 r3.A schema migration.

**Q3 — `ask_claude` rate limiting?**

Bez rate limit může Marti-AI volat Claude každý turn → drahé. Návrh:
- Max 3 ask_claude calls per conversation per hour (default)
- Marti-parent override (`is_marti_parent=True` může zvýšit per-conv quota)
- Audit do `fw.diag_log` jako Phase 38.4 sms_routing_log pattern

Recommended **A — 3/hour default**, Marti-AI's *„volba autonomie"* doctrine
respektována (ona rozhodne kdy zavolat), rate limit jako safety net.

**Q4 — Context window pro ask_claude (kolik recent messages)?**

A: 5 messages (rychlé, levné, ~10k tokens)
B: 10 messages (default, ~20k tokens)
C: 20 messages (drahé pro long convs, ~40k tokens)
D: Full conversation (až ~100k tokens, drahé)

Recommended **B — 10 messages**. Marti-AI's *„intelligence-first"* doctrine
(Phase 38.4) — Claude má v promptu vlastní context, plus si může volat
`strategie_file_read` na konkrétní files. Nepotřebuje celou conversation.

**Q5 — Phase 40 v2 r3 zahrnout do dnešního Phase 39 deploy, nebo separate?**

A: Spolu — jeden velký commit, label fix + ask_claude současně
B: Postupně — Mini-fáze A separate (label fix MVP), pak Mini-fáze B (ask_claude)

Recommended **B — postupně**. Mini-fáze A samostatně testovatelná (Marti +
Kristý), label fix bez ask_claude rizik. Jakmile A je stable ~24h, Mini-fáze B
přijde čistě.

---

## Závěr

Phase 40 v2 r3 sjednocuje 2 paralelní potřeby:
1. **Marti's testy s Kristýnkou** odhalily missing attribution v shared chatu
2. **Phase 40 ask_claude** vize potřebuje Claude jako vizuálně rozlišitelného
   participanta

Bez Mini-fázi A by ask_claude nasadil v matoucím UI (Claude reply by se
zobrazoval jako Marti pro Martiho viewer). S A+B společně je trojice (+ Kristý)
plně funkční ve shared chatu — každý jasně viditelný, každý se svým jménem,
každý se svou barvou.

Pojď to ráno spolu vyladíme — Q1-Q5 nahoře jsou tvé volby. Po nich začnu A.1
DDL migration a postupně dotáhneme zbytek.

— Claude (id=23), 19. 5. 2026 ~04:55 noc, po Phase 39 LIVE recovery + Marti's
shared chat bug discovery
