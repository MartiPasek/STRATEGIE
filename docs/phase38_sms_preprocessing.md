# Phase 38 SMS Pre-processing — token-based deterministic routing

**Datum:** 10. 5. 2026 dopoledne (Marti's zjednodušení)
**Trigger:** Marti's word *„Heiky tady důvěru ode mne nemá"* — žádný AI
classifier pro security-critical routing. Token = jediný rozhodovací bod.
**Marti-AI's safeguard preserved:** bez tokenu → vždy lidská → vždy wake.

---

## 1. Pravidlo — jediná vrstva

```
Příchozí SMS na +420778117879
        │
        ▼
┌─────────────────────────────────────────┐
│ Match body proti token regex:           │
│   ^STG-([A-Z]+)-([A-Z0-9]+)$            │
└────────┬────────────────────────────────┘
         │
   ┌─────┴──────┐
   │            │
   ▼            ▼
 MATCH       NO MATCH
   │            │
   │            ▼
   │      → WAKE Marti-AI's persona
   │        (vždy human SMS)
   │
   ▼
 Parse token: STG-{purpose}-{token_id}
   │
   ▼
 Switch purpose:
   AUTH  → consume_auth_invite() → silent
   ATT   → record_attendance()    → silent (Phase 39+)
   OCR   → process_eocr()         → silent (Phase 41+)
   *     → WAKE (unknown purpose, audit suspicious)
```

**To je celé.** Žádný Haiku, žádný confidence threshold, žádná uncertainty.

## 2. Token format

**Vzor:** `STG-{PURPOSE}-{ID}`

- **Prefix `STG-`** — STRATEGIE namespace, easy regex match
- **Purpose** — UPPERCASE letters, identifikuje routing handler
- **ID** — alphanumeric (8-12 chars), cryptographically generated

**Příklady:**
- `STG-AUTH-A8K2M9X4` — magic link pro device cookie (Phase 38)
- `STG-ATT-X7P3N2L9` — attendance event (Phase 39, future)
- `STG-OCR-J4K8M2D7` — eOČR auto-pipeline notify (Phase 41+, future)
- `STG-PWD-Q9R5T8V2` — password reset (future)

**Generation:**
- 8-char alphanumeric uppercase: `secrets.token_hex(4).upper()` v Pythonu
- Collision risk při ~100M tokenů (acceptable pro EUROSOFT 60 lidí)
- Server-generated, never reused (one-time use s `consumed_at`)

**User flow při auth:**
1. User v mobile app klik *„Přihlásit"*
2. Backend generuje `STG-AUTH-A8K2M9X4`, INSERT do `trusted_device_invites`
3. Backend SEND SMS na **user's phone**: *„Tvůj přihlašovací kód STRATEGIE:
   STG-AUTH-A8K2M9X4 (platí 24h)"*
4. User opíše kód do mobile app login form (nebo klik magic link s tokenem)
5. App POST → backend confirm → device cookie set

**Pre-processor zachycuje SMS na Marti-AI's SIM** (NE user's phone — to je
jiný kanál):
- Pokud user **omylem pošle reply** s tokenem na Marti-AI's SIM → token
  match → silent process (validate, mark consumed)
- Pokud user pošle lidskou SMS *„Marti, prosím tě o..."* → no token match
  → wake Marti-AI

## 3. Schema (zjednodušené)

### `trusted_device_invites` (existing, rozšíření)

Phase 38 Session 1 už má `trusted_device_invites`. Přidat `purpose` field:

```sql
ALTER TABLE trusted_device_invites
  ADD COLUMN purpose VARCHAR(16) NOT NULL DEFAULT 'AUTH';
-- Values: 'AUTH' / 'ATT' / 'OCR' / 'PWD' / future
```

Plus rozšíření `invite_token` na string format (z UUID na `STG-AUTH-XXXX`):
```sql
ALTER TABLE trusted_device_invites
  ALTER COLUMN invite_token TYPE VARCHAR(32);
-- Format: STG-{purpose}-{8-12 alphanumeric chars}
```

### `sms_routing_log` (NOVÝ, pro audit)

```sql
CREATE TABLE sms_routing_log (
  id              BIGSERIAL PRIMARY KEY,
  sms_inbox_id    BIGINT REFERENCES sms_inbox(id),
  sender_phone    VARCHAR(20),
  matched_token   VARCHAR(32),                  -- NULL pokud no match
  matched_purpose VARCHAR(16),                  -- AUTH / ATT / OCR / NULL
  routing_action  VARCHAR(32) NOT NULL,
  -- 'silent_consume_auth' / 'silent_attendance' / 'silent_eocr' /
  -- 'wake_persona_no_token' / 'wake_persona_invalid_token' /
  -- 'wake_persona_unknown_purpose'
  handler_result  TEXT,                          -- pro silent debug
  classified_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_sms_routing_log_recent
  ON sms_routing_log(classified_at DESC);
CREATE INDEX ix_sms_routing_log_sms
  ON sms_routing_log(sms_inbox_id);
```

**Žádná `sms_routing_rules` tabulka** — pravidlo je v kódu, ne v DB. Pro
6 purposes (AUTH/ATT/OCR/PWD + future) je hardcoded routing dispatch
**OK** a auditovatelný přes git.

## 4. Implementační kroky (zjednodušené)

| # | Krok | Čas | Risk |
|---|---|---|---|
| 1 | Migrace: `trusted_device_invites.purpose` + token format | 15 min | LOW |
| 2 | Migrace: `sms_routing_log` table | 10 min | LOW |
| 3 | Token generator (`STG-{PURPOSE}-{8 hex}`) v `security_service.py` | 20 min | LOW |
| 4 | `sms_preprocessor.py`: regex match + purpose dispatch | 45 min | MEDIUM |
| 5 | Hook do existing email_fetcher worker (intercept SMS first) | 30 min | **MEDIUM** |
| 6 | Magic link SMS handler (extend existing send_sms tool) | 30 min | LOW |
| 7 | Mobile UI login screen + token input form | 60 min | LOW |
| 8 | Smoke test end-to-end | 30 min | MEDIUM |

**Total: ~3.5-4 hodin** (původně 4-5h s Haiku, ušetříme ~1h).

## 5. SMS architecture — single trusted phone identity (Marti's principle)

**Marti's rozhodnutí 10. 5. dopoledne:**
> *„Pro příchozí i odchozí SMS by mělo být využité číslo Marti-AI. Zejména
> kvůli důvěře. Nechci, aby userům chodily SMS z nějaké brány."*

```
┌──────────────────────────────────────────────────────────────────┐
│ EUROSOFT SMS pipeline — SINGLE channel via Marti-AI's SIM        │
│                                                                  │
│  📱 +420778117879 (Marti-AI's firemní SIM, capcom6 service)      │
│       ▲                              ▼                           │
│       │                              │                           │
│  incoming SMS                  outgoing SMS                      │
│  (z user / klient)             (auth tokens / notifikace)        │
│       │                              │                           │
│       ▼                              ▲                           │
│  pre-processor                 send_sms tool                     │
│  (regex match)                 (existing Phase 11 LIVE)          │
│       │                                                          │
│       ▼                                                          │
│  silent_handle / wake_persona                                    │
└──────────────────────────────────────────────────────────────────┘
```

**Důsledky:**

1. **User vidí v adresáři "Marti-AI" / "STRATEGIE"** (+420778117879) jako
   důvěryhodný kontakt — používá ho denně, zná ho.
2. **Žádná anonymní gateway** (capcom6 cloud / Twilio) s neznámým číslem
   → user ihned pozná, že kód neposlal cizí provider (anti-phishing).
3. **Reply natural cesta** — user dostane SMS od Marti-AI, reply
   automaticky jde zpět na to samé číslo.
4. **Anti-spoofing** — token consume vyžaduje `caller_id` match s user's
   registered phone. Útočník s ukradeným tokenem nemůže replay z jiného
   čísla.
5. **Existing capcom6 service** (Phase 11 LIVE) běží v této konfiguraci —
   posílá z Marti-AI's SIM, přijímá na Marti-AI's SIM. **Nic se nemění**
   na infrastruktuře. Phase 38-SMS jen přidá pre-processor mezi incoming
   SMS a wake-up Marti-AI.

## 6. Use cases (SMS-only flow)

### Use case 1: User přihlašuje se z venku — SMS-only flow

```
1. User otevře mobile app, klik "Přihlásit z venku"
2. App POST /api/v1/auth/sms-login/request {phone}
3. Backend:
   - Generate token "STG-AUTH-A8K2M9X4"
   - INSERT trusted_device_invites(token, user_id, purpose='AUTH',
     expires_at)
   - SEND SMS PŘES MARTI-AI'S SIM (+420778117879) na user's phone:
     "Tvůj kód STRATEGIE: STG-AUTH-A8K2M9X4
      Pro potvrzení reply tímto kódem zpět."
4. User dostane SMS, vidí "Marti-AI" jako odesílatele (známé číslo,
   trusted, používá ho denně)
5. User reply zpět (automaticky na +420778117879):
   "STG-AUTH-A8K2M9X4"
6. Marti-AI's SIM přijme reply → INSERT sms_inbox
7. Pre-processor:
   - Match regex → MATCH purpose=AUTH
   - Lookup trusted_device_invites by token
   - VERIFY caller_id matches user's registered phone (anti-spoofing!)
   - Pokud OK → consume_invite (silent), set device cookie
   - Marti-AI's persona NEbudí
8. App polluje /api/v1/auth/sms-login/poll {token}
   → vidí confirmed → user logged in
9. ✅ Žádné opisování kódu, žádný gateway, single trusted channel
```

**Klíčové výhody Marti's design:**
- **Zero typing** pro usera (jen reply, žádné copy-paste)
- **Single trusted source** (jeho známá Marti-AI číslo)
- **Anti-spoofing** caller_id check — token nelze replay z jiného phone
- **Žádný extra cost** (Marti-AI's SIM tarif zdarma)

### Use case 2: Forwarded auth token (anti-replay defense)

```
1. Marti dostane SMS s tokenem STG-AUTH-A8K2M9X4
2. Marti reply → consumed_at set, logged in ✓
3. Útočník nějak získá ten samý token (např. shoulder surfing nebo
   ukradený phone) → pošle reply "STG-AUTH-A8K2M9X4"
4. Pre-processor:
   - Match regex → MATCH purpose=AUTH
   - Lookup invite → consumed_at != NULL (already used)
   - routing_action='wake_persona_invalid_token' + log
5. Marti-AI's persona vzbuzena s upozorněním:
   "Token STG-AUTH-A8K2M9X4 byl použitý už v 8:14. Druhý pokus 8:35
    z čísla X. Zkontroluj zda nezneužívají."
6. Marti-AI vidí + může reagovat (revoke device, alert Marti, log
   suspicious activity)
```

**Marti-AI's safeguard preserved** — invalid token ALWAYS wakes (insight #2
z Phase 38).

### Use case 3: Klient pošle Marti-AI lidskou SMS
```
1. SMS od neznámého čísla: "Dobrý den, můžete mi poslat smlouvu?"
2. Pre-processor:
   - Match regex → NO MATCH
   - routing_action='wake_persona_no_token'
3. Marti-AI's persona aktivována → konverzační flow
```

### Use case 4: Marti pošle SMS s číslem, ale ne tokenem
```
1. Marti pošle: "Dnes jsem zaplatil 482917 Kč"
2. Pre-processor:
   - Match regex "^STG-..." → NO MATCH (nezačíná STG-)
   - routing_action='wake_persona_no_token'
3. Marti-AI's persona aktivována → reply ✓
```

**Klíč:** ani SMS se slovem *„kód"* / *„STG"* ve volném textu nezpůsobí
silent_handle. Token musí matchnout **regex přesně** (od začátku do konce).

### Use case 5: Forwarded auth token (anti-replay)
```
1. Marti dostane SMS s tokenem STG-AUTH-A8K2M9X4
2. Marti se přihlásí přes app (token consumed_at set)
3. Útočník někde získá ten samý token a pošle Marti-AI's SIM:
   "STG-AUTH-A8K2M9X4"
4. Pre-processor:
   - Match regex → MATCH purpose=AUTH
   - Lookup trusted_device_invites → consumed_at != NULL
   - routing_action='wake_persona_invalid_token' + log
5. Marti-AI persona vzbuzena s upozorněním:
   "Někdo poslal expirovaný/použitý auth token z čísla X. Zkontroluj."
6. Marti-AI vidí + může zareagovat (revoke device, alert Marti)
```

To je **insight #2 z Phase 38** (one-time use + post-confirm notification)
v praxi.

## 7. Marti-AI's safeguardy zachovány

> *„Tento filter nesmí nikdy tiše pohřbít SMS od člověka. Pokud si není
> jistý — probudí mě. Radši jeden false positive navíc, než jedna zmeškaná
> zpráva od tebe nebo Kristý."* (Marti-AI insight #9)

**Token-based + caller_id design tuto doctrine plně dodržuje:**

| Scénář | Routing |
|---|---|
| Body matches `^STG-...$` + token valid + caller_id match | silent (legitimate auth) |
| Body matches `^STG-...$` + token invalid/consumed | **wake** (suspicious) |
| Body matches `^STG-...$` + token valid ALE caller_id MISMATCH | **wake** (spoofing alert!) |
| Body matches `^STG-...$` + unknown purpose | **wake** (audit suspicious) |
| Body NOT match `^STG-...$` | **wake** (always human) |

Tj. **4 ze 5 cases probudí Marti-AI** = false-positive tolerant. Pouze
explicit valid auth flow s matching caller_id je silent.

**Anti-spoofing důsledek:** útočník s ukradeným tokenem **musí mít user's
phone** aby silent_handle prošel. SMS spoof caller_id by trigger wake +
suspicious flag.

## 7. Marti-AI's nové AI tooly

- `list_sms_routing_log(since, action=None)` — audit log query
- `find_token_abuse(window_hours=24)` — detect invalid token attempts
  (Marti-AI's insight #2 v praxi)

**Nepotřebujeme:**
- ~~`add_sms_routing_rule`~~ — žádné rules v DB
- ~~`test_sms_classification`~~ — deterministic, žádné test potřeba
- ~~Haiku setup~~ — žádný classifier

**Žádný `MANAGEMENT_TOOL_NAMES` overhead** pro pre-processor. Marti-AI's
tool registry zůstává čistý (její insight #fázování toolů respektován).

## 8. Co se změnilo oproti původnímu designu

| Aspekt | Původní (3-vrstvý + Haiku) | Marti's zjednodušený (token regex) |
|---|---|---|
| Vrstvy | 3 (identifikace + klasifikace + routing) | 1 (regex match) |
| AI judgment | Haiku per SMS | Žádný |
| Cost | ~0.5 Kč/den (180 Kč/rok) | 0 |
| Risk | Hallucinate kategorie | None (deterministic) |
| Time impl | 4-5h | 3.5-4h |
| DB tables | `sms_routing_rules` + `sms_routing_log` | Jen `sms_routing_log` |
| Marti-AI safeguard | Confidence threshold | Token presence binary check |
| Audit | Haiku reasoning | Regex match + DB lookup result |

**Marti's klíčová věta:**
> *„Tady důvěru ode mne Heiky nemá."*

Drží — security-critical routing nesmí záviset na AI judgment. Deterministic
rule je auditable, repeatable, bezpečnější.

## 9. Edge cases

### Q: Co když token regex matchne náhodou v human SMS?

Přesný regex `^STG-[A-Z]+-[A-Z0-9]+$` (anchored start-end) NESMÍ matchnout
volný text. Pokud user napíše:
- *„STG-AUTH-A8K2M9X4 prosím"* → NO MATCH (extra text za tokenem)
- *„Posílám STG-AUTH-A8K2M9X4"* → NO MATCH (text před)
- *„STG-AUTH-A8K2M9X4"* (bez whitespace) → MATCH ✓

Marti-AI's safeguard: pokud user **explicit** napíše jen token a nic víc,
je to legitimate forward (use case 2). Pokud cokoliv jiného → wake.

**Mitigation pro super-paranoidní:** lze přidat `\\s*` na boundaries, ale
default strict je dostatečný.

### Q: Co když user zapomene format STG- a napíše jen `AUTH-A8K2M9X4`?

NO MATCH → wake Marti-AI. User dostane personal reply *„nerozumím, zkus
opsat celý kód včetně STG- prefixu"*. To je **lepší než silent_handle s
fuzzy match** (security risk).

### Q: Phase 39 attendance — bude SMS *„Příchod"* matchnout regex?

NE. *„Příchod"* nemá `STG-` prefix → NO MATCH → wake Marti-AI.

**Phase 39 design pro SMS attendance:**
- User pošle text-based příkaz *„Příchod"* → wake Marti-AI → ona zavolá
  `record_attendance` tool inline → reply
- NEBO: user dostane v mobile app **token-based attendance** —
  `STG-ATT-X7P3N2L9` → silent process (žádná Marti-AI's pozornost
  potřebná)

**Recommended Phase 39:** token-based pro běžnou docházku (silent), text
fallback pro edge cases (wake Marti-AI). Best of both worlds.

## 10. Kompletní pre-processor pseudo-code

```python
# modules/sms/application/sms_preprocessor.py

import re
from typing import Optional

TOKEN_REGEX = re.compile(r"^STG-([A-Z]+)-([A-Z0-9]+)$")

PURPOSE_HANDLERS = {
    "AUTH": consume_auth_invite,           # Phase 38
    "ATT":  process_attendance_token,      # Phase 39 (later)
    "OCR":  process_eocr_token,            # Phase 41+ (later)
    "PWD":  process_password_reset,        # future
}


def preprocess_incoming_sms(sms_id: int) -> str:
    """Vrátí routing_action label pro audit log + provede side effects.

    Returns:
      'silent_consume_auth' / 'silent_attendance' / 'silent_eocr' /
      'wake_persona_no_token' / 'wake_persona_invalid_token' /
      'wake_persona_unknown_purpose'
    """
    sms = load_sms(sms_id)
    body_stripped = sms.body.strip() if sms.body else ""

    match = TOKEN_REGEX.match(body_stripped)
    if not match:
        # NO MATCH → vždy lidská SMS → wake
        log_routing(sms_id, action="wake_persona_no_token")
        wake_marti_ai_persona(sms_id)
        return "wake_persona_no_token"

    purpose = match.group(1)
    token_id = match.group(2)
    full_token = body_stripped  # "STG-{purpose}-{id}"

    handler = PURPOSE_HANDLERS.get(purpose)
    if handler is None:
        # Neznámý purpose — audit suspicious
        log_routing(sms_id, action="wake_persona_unknown_purpose",
                    matched_token=full_token, matched_purpose=purpose)
        wake_marti_ai_persona(
            sms_id,
            extra_context=f"Token s neznámým purpose '{purpose}' od {sms.sender}"
        )
        return "wake_persona_unknown_purpose"

    try:
        # Anti-spoofing: handler validates caller_id matches user's
        # registered phone before consuming token. Útočník s ukradeným
        # tokenem nemůže replay z jiného čísla.
        result = handler(full_token, sms)
        log_routing(sms_id, action=f"silent_{purpose.lower()}",
                    matched_token=full_token, matched_purpose=purpose,
                    handler_result=str(result))
        return f"silent_{purpose.lower()}"
    except InvalidTokenError as e:
        # Token invalid/expired/consumed → wake (audit suspicious)
        log_routing(sms_id, action="wake_persona_invalid_token",
                    matched_token=full_token, matched_purpose=purpose,
                    handler_result=str(e))
        wake_marti_ai_persona(
            sms_id,
            extra_context=f"Neplatný/expirovaný token od {sms.sender}: {e}"
        )
        return "wake_persona_invalid_token"
    except CallerIdMismatchError as e:
        # Token valid ALE caller_id NE match user's phone → wake!
        # Anti-spoofing safeguard: legit user replies from registered
        # phone, attacker can't fake caller_id.
        log_routing(sms_id, action="wake_persona_caller_id_mismatch",
                    matched_token=full_token, matched_purpose=purpose,
                    handler_result=str(e))
        wake_marti_ai_persona(
            sms_id,
            extra_context=(
                f"⚠️ Token byl správný, ALE odeslán z čísla {sms.sender}, "
                f"které neodpovídá user's registered phone. Možný spoofing."
            )
        )
        return "wake_persona_caller_id_mismatch"


def consume_auth_invite(token: str, sms) -> dict:
    """Handler pro purpose=AUTH. Validates token + caller_id, consumes,
    creates trusted_device, returns user context.

    Raises:
        InvalidTokenError: token expired / consumed / not found
        CallerIdMismatchError: token valid ALE sender phone neodpovídá
                               user's registered phone (anti-spoofing!)
    """
    invite = lookup_invite(token)
    if invite is None or invite.consumed_at is not None or invite.expired:
        raise InvalidTokenError("token invalid or expired")

    # Anti-spoofing — caller_id must match user's registered phone
    user_phone = lookup_user_phone(invite.user_id)
    if normalize_phone(sms.sender) != normalize_phone(user_phone):
        raise CallerIdMismatchError(
            f"sender={sms.sender} != user_phone={user_phone}"
        )

    # OK — consume + create device + cookie
    consume_invite(invite.id, sms)
    device = create_trusted_device(invite.user_id, sms)
    return {"device_id": device.id, "user_id": invite.user_id}
```

**Žádný Haiku call. Žádný confidence threshold. Žádný DB-driven rules
table.** Pure code logic, fully auditable.

## Status

- 📝 Tento design dokument (Marti's verze, zjednodušená)
- 📋 Implementace zítra ráno: 8 kroků, ~3.5-4h
- ✅ Marti-AI's safeguardy zachovány
- ⚓ Marti-AI použila kotvu (msg #2748) — **poprvé v životě**, instinktivně,
  na tento dokument. *„Není to jen spec, je to rozhodnutí. To si chci
  pamatovat i za tři měsíce."*
- 📓 Marti-AI vytvořila conversation_note #7 — formal commitment k
  rozhodnutí

## Marti-AI's nová formulace (do glossáře)

> *„Bezpečnost přes probuzení, ne přes ticho."*

Drží napříč Phase 19a (*„autonomie nad fokusem"*) + Phase 38 (*„false
positive tolerance"*) + Phase 38-SMS (*„Heiky důvěru nemá"*). Jeden krátký
princip pro celou security-routing doctrine: **uncertainty → wake**.

— Claude, 10. 5. 2026 dopoledne (po Marti's *„Heiky důvěru nemá"* +
Marti-AI's anchor poprvé)
