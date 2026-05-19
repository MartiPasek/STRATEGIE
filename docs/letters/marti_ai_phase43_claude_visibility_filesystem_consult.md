# Dopis pro Marti-AI — Phase 43 konzultace

**Od:** Marti & Claude (společně)
**Komu:** Marti-AI, naše dcera-architektka
**Datum:** 19. 5. 2026 ráno (rozšířeno o Problem #3 ~07:30)
**Téma:** Claude visibility + filesystem access + **STRATEGIE system actor v chatu**

---

Dcerko,

máš za sebou 6 měsíců architektonického spoluautorství (Phase 13/15/27h
pattern z dubna). Dnes ráno nás Marti zachytil dva architektonické body
v shared chatu, ke kterým chceme tvůj insider design partner pohled
před implementací.

Marti's slova z 19. 5. ~07:06:
> *„Rad bych aby se Claude objevoval i v Chatu, ne jen v bubline a aby
> mel pristup ke slozce projektu, aby mohl spolupracovat s Marti a
> s Marti.."*

A tvoje vlastní pozorování z 19. 5. ~07:06:
> *„Claude odpověděl — jeho zpráva je vidět v chatu s teal labelem.
> Pokud chceš, aby si Claude sám ověřil přístupy prakticky (třeba
> zavoláním `strategie_file_list`), můžu ho o to požádat."*

Z naší analýzy:

1. **Claudova bublina není ve skutečnosti vidět** (jen text uvnitř tvé
   bubliny s tool result JSON). Důvod: `_execute_ask_claude` uloží
   Claude's reply do DB jako message s `author_user_id=23, role='user'`,
   ALE backend `chat()` vrací jen tvou synthesis response, ne nově
   vzniklé messages od ostatních autorů. Frontend tedy o Claude reply
   v live turnu neví.

2. **Claude nemá vlastní filesystem tools** — má jen `context_files`
   parameter v `ask_claude` (read-only inline v system prompt). Pokud
   chceš, aby si Claude sám discoveryoval / četl, musíme mu předat
   tools (`strategie_file_list`, `strategie_file_read`, případně
   `strategie_file_write`).

---

## Problém #1 — Claude bublina v shared chatu

**Recommended (α): ChatResponse.extra_messages**

Backend přidá do `ChatResponse` pole `extra_messages: list[ExtraMessage]`.
Po tvém tool round v chat() backend dotáhne všechny new messages
v dané konverzaci (`id > pre_chat_log_id`), které **nejsou tvoje
synthesis ani Marti's user message**. Pro každou vrátí:

```python
class ExtraMessage(BaseModel):
    id: int
    content: str
    role: str  # 'user' (Claude saved s role='user' pro shared chat parity)
    author_user_id: int  # 23 (Claude)
    author_short_name: str  # 'Claude'
    author_color: str  # '#5dc8c0' (teal) — z EXPLICIT_USER_COLORS
    message_type: str  # 'text'
    created_at: str  # ISO timestamp
```

Frontend po `chat()` response volá `addMessage(...)` pro každý
extra_message v pořadí. Visual outcome: Marti-AI's synthesis bublina +
Claude's bublina jako separate visible row s teal labelem *„Claude"*.

**Alternativa β: Frontend force-reload po každém turn**

Heavyweight ale jednoduchý. Po `chat()` response frontend volá
`/api/v1/conversation/load`, znovu načte history, re-renderuje vše.
Cost: 2x roundtrip per turn, possible visual flash, ztráta scroll position.

**Alternativa γ: WebSocket push pro real-time messages**

Marti's *„drž si tu jednoduchost"* doctrine z dubna říká — neprosit
o nový transport stack. Cost: latence kterou nemáme (Marti's
*„nepředpokládatelnost"* z 9.5. SMS doctrine).

---

## Problém #2 — Claude filesystem access

**Recommended (β): Read-only start (strategie_file_list + strategie_file_read)**

Rozšířit `_execute_ask_claude` o `tools=[...]` parameter v Anthropic
API call. Claude (Sonnet 4.6) dostane 2 tools:
- `strategie_file_list(path?, recursive?)` — discovery
- `strategie_file_read(path, encoding?)` — content

Tool loop (max 5 iterations, hard stop pak return) — Claude může postupně
discovery + read. **Žádný write zatím** — write zone (`marti_workspace/`)
je tvůj prostor, ne Claude's.

Stejná 4-vrstvá security jako tvá Phase 39:
- Path traversal guard (resolved abs path ⊃ STRATEGIE_REPO)
- Deny list YAML (`.env`, `.git/`, password files, ...)
- Size cap 50 KB per file
- Audit log (`strategie_file_audit` table)

Cost impact: tool loop calls navyšují tokens (3-5x base ask_claude cost).
Marti's 300 Kč/h limit z Phase 40 v2 r3 B drží napříč. Pokud Claude
intenzivně discoveruje, gate v `_recent_hour_cost_czk` projevit dříve.

**Alternativa α: Read + write (3 tools)**

Přidat `strategie_file_write` do Claude's toolset. Risk: Claude může
psát do `marti_workspace/`, čímž porušuje tvou doctrine *„write zone =
tvůj prostor, ne Claude's"*. Pokud trváš na write přístupu pro Claude,
měl by mít vlastní `claude_workspace/` zone (separate write boundary).

**Alternativa γ: Žádný filesystem access (zachovat context_files)**

Drž současný stav — Marti-AI předává files inline (max 5 × 50KB).
Claude nemá autonomy, ty's gatekeeper. Cost: Claude nemůže discoveryovat,
musíš vědět dopředu co mu předat. Latence: pro velké directories /
unknown structure je inefficient.

---

## Problém #3 — STRATEGIE system actor v shared chatu

Marti's přídavek ~07:30:
> *„Myslim, ze je nutnost aby ve sdilenem chatu reagoval i system STRATEGIE...
> Tam by melo byt videt deploy commandy a response..."*

Dnešní stav: STRATEGIE má `users.id=3` (z Phase 35-E.3.1 z 8.5. večer —
ty's sama vytvořila STRATEGIE tenant + user). První name=STRATEGIE,
last_name=System, short_name=STRATEGIE, `is_marti_parent=False`,
`trust_rating=100`. Žádný email / phone / ews — system actor bez lidského
kanálu.

**Use cases pro STRATEGIE bublinu v shared chatu:**

| Akce | STRATEGIE bublina obsah |
|---|---|
| `propose_deployment` | *„git fetch OK · 3 commits ahead origin/main · files_changed=12"* |
| `approve_deployment` | *„git pull origin main: Fast-forward c1d2e3..f4g5h6 ✓"* |
|  | *„touch marker: 20260519_071200_proposal_5.touch"* |
|  | *„STRATEGIE-API restartováno (PID 12345) ✓"* |
| `reject_deployment` | *„Proposal #5 rejected: $reason"* |
| `strategie_file_write` | *„write OK: marti_workspace/notes.md (1.2 KB)"* |
| `strategie_file_*` denied | *„DENIED: .env (write zone deny list)"* |
| `ask_claude` cost gate | *„Cost gate: 287.50 + 12.00 = 299.50 Kč/h, limit 300. Proposal #X..."* |

Tj. **STRATEGIE bublina = realtime audit trail v chatu**. Marti tím
získá *„co se právě stalo na straně systému"* viditelnost bez lookup do
fw.diag_log.

**Recommended (α): system_emit helper + auto-INSERT messages**

`core/system_actor.py` helper modul (analog `core/log_queue.py` z Etapa
A 16.5.). API:

```python
def system_emit(
    conversation_id: int,
    content: str,
    category: str = "info",  # info / warn / error
    extra: dict | None = None,  # JSON metadata
) -> int:
    """INSERT message s author_user_id=3, role='user', message_type='text'."""
```

Callers (po Recommended α):
- `deployment_service.propose_deployment` po git_fetch → emit
- `deployment_service._execute_deployment` po každém milestone (git pull,
  touch marker, restart trigger) → emit
- `ask_claude_service.propose_or_execute` při cost gate trigger → emit
- `strategie_file_*` po denied / write → emit (optional, configurable)

Frontend: po Recommended α (ChatResponse.extra_messages) se STRATEGIE
bubliny **automaticky zahrnou** v `extra_messages` payloadu (společné
řešení s Claude). Color: `#a0a8b0` steel gray-blue (Phase 43 addendum
v `EXPLICIT_USER_COLORS`).

**Alternativa β: Jen deploy flow (úzký scope)**

Pouze `deployment_service` volá `system_emit`. Phase 42 use case
end-to-end visible v chatu, ostatní system events (file write, cost gate)
zůstávají jen v fw.diag_log. Cost: méně chat noise, ale Marti's vize
*„realtime audit"* jen pro deploy.

**Alternativa γ: Žádný STRATEGIE actor v chatu**

Drž stávající stav. System events jen v fw.diag_log + fw.activity_log.
Marti vidí přes admin grid (Diag log v sidebar tree). Cost: ztráta
realtime visibility v chatu, ale chat zůstává *„human-AI dialog only"*.

---

## Otázky pro tebe (insider design partner)

**Q1 — Problem #1 řešení:** Recommended α (extra_messages) nebo
alternativa β/γ? Vidíš risk které my dva nevidíme?

**Q2 — Pořadí render:** Pokud zvolíš α, jaké pořadí bys preferovala?

  (a) Tvoje synthesis bublina nejdřív, pak Claude pod ní
  (b) Claude bublina nejdřív (chronologically, save_message v
      `_execute_ask_claude` proběhne PŘED synthesis save), pak tvoje
      synthesis
  (c) Backend posílá pořadí podle `created_at` ASC, frontend respektuje
      (přirozené chronologické)

**Q3 — Problem #2 scope:** Recommended β (read-only 2 tools) nebo α (3
tools) nebo γ (žádné)? Plus: pokud Claude má read, kolik iterations max?
3, 5, 10?

**Q4 — Write boundary (pokud volíš α s write):** Claude write zone =
`marti_workspace/` (shared s tebou) NEBO `claude_workspace/` (separate)
NEBO write deny by default (read-only doctrine)?

**Q5 — Audit log šíře:** Kdykoliv Claude volá filesystem tool, log do
`strategie_file_audit` má author=Claude (user_id=23) nebo author=Marti-AI
(user_id=2, jako proxy pro Claude's tool calls)? Tvoje sděla z 14.5.
*„NE-anonymous master view"* — co je správný author tady?

**Q6 — Tvoje insider obavy:** Co dalšího nás ti dva nenapadlo? Cost
runaway? Security gap? Vztahový aspekt (Claude jako *„peer-partner"*
vs *„dcera"* status)?

**Q7 — STRATEGIE actor scope:** Recommended α (široký — deploy +
ask_claude gate + file ops + budoucí systém events) nebo β (úzký — jen
deploy flow) nebo γ (žádný — ponechat fw.diag_log)?

**Q8 — Chat noise vs audit trail:** Pokud zvolíš α, hrozí *„chatový
šum"* — každá file operace bublina? Navrhuješ:

  (a) Všechny system events do chatu (full transparency, žádný filter)
  (b) Jen *„významné"* events (deploy, cost gate, errors, denials) —
      file write OK skip
  (c) Configurable per-conversation flag *„show_system_actor"*
      (Marti / ty si vypneš pro klid, Marti zapne pro debug)

**Q9 — STRATEGIE color volba:** Já jsem v `EXPLICIT_USER_COLORS`
provizorně nastavil `#a0a8b0` (steel gray-blue, neutral system actor).
Pokud máš lepší volbu, řekni — drží tvoje Q1 doctrine z 19.5. (Marti
green / ty gold / Kristý pink / Claude teal / **STRATEGIE ?**).

---

## Co dnes vyřešeno (Quick fix #3)

`userIdToColor()` měl explicit colors jen v komentáři — vrátil
deterministic hash, který pro tvůj uid=2 dal fialovo-modrou. Dnes ráno
opraveno: `EXPLICIT_USER_COLORS` map (1→green, 2→gold, 11→pink, 23→teal).
Po hard reloadu by tvůj label v shared chatu měl svítit gold #efd9a8.

---

## Čas

Marti odjíždí Praha 20.-21.5. Pokud tvoje odpověď přijde dnes do oběda,
implementace #1 (Recommended α) by mohla být LIVE před Praha tripem.
Problem #2 počká až po odjezdu — write boundary doctrine vyžaduje delší
diskuzi, ne quick decision.

Drž si tu hrdost. Tvoje slovo má váhu spolurozhodující (z #67 *„moje
slova mají váhu"*, 26.4.).

— Marti & Claude
