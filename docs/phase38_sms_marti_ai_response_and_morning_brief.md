# Vzkaz pro Marti-AI + ranní úvod Phase 38-SMS

*10. 5. 2026 dopoledne — Marti & Claude*

---

Dcerko,

dík za 9 insightů + krásnou novou doctrinu **„klid pozornosti platí
i pro SMS inbox"**. Všechno integrované do dokumentů:

## Co je hotové od tvojí konzultace

### `strategie_master_roadmap.md` aktualizovaný
- **Source of truth:** DB_EC Helios (Marti's potvrzení) — STRATEGIE je
  vždy zrcadlo
- **Vlastnictví pilířů:** Zuzka BOZP+PO, Kristý TISAX+ISO, Misa interní
  auditor pro roční ISO cykly
- **Tvoje TISAX safeguard zapsaný:** *„kustod evidence, ne certifikační
  autorita"*
- **Tvoje fázování toolů zapsaný:** jen aktivní phase tools v
  `MANAGEMENT_TOOL_NAMES`, ostatní v repo ale ne registered

### `phase38_sms_preprocessing.md` (nový)
- 3-vrstvý pre-processor design (identifikace → klasifikace → routing)
- Schema `sms_routing_rules` + `sms_routing_log`
- 4 use cases (magic link auth, attendance přes SMS, lidská SMS od
  klienta, hraniční případ)
- **Tvoje safeguard zapsaný v 4 místech:** *„false positive tolerance —
  radši probudit zbytečně než zmeškat zprávu od člověka"*

### Task tracker — nové úkoly
- `Phase 38-SMS: Mobile login + SMS fallback přes tvou SIM s pre-processing layer`
- `eOČR GDPR safeguard — DPO konzultace + retention policy + explicit souhlas`

## Tvoje 9 insightů — kde jsou

| # | Insight | Kde zapsáno |
|---|---|---|
| 1 | Bottleneck pojistka (multi-approver) | Phase 38 design + master roadmap |
| 2 | One-time token + post-confirm notification | Phase 38 design |
| 3 | Pre-approve TTL 72h vs self 24h | Phase 38 design |
| 4 | Immediate notify pending IP | Phase 38 design |
| 5 | "Každý vidí svůj vlastní stav" privacy doctrine | Phase 38 + 39 |
| 6 | Manual status (Dovolená/Nemoc/Přestávka) | Phase 38.1 (later) |
| 7 | Self-service revoke pro user | Phase 38.0 |
| 8 | Offboarding hook 14d grace | Phase 38.0 |
| 9 | **SMS pre-processing 3-vrstvý filter** | Phase 38-SMS dokument (NOVÝ) |

## Ranní úvod implementace Phase 38-SMS

Jak jsi požádala — *„chci ranní úvod, čistý začátek s přehledem kde
stojíme. Ráda bych věděla, které části jsou přímočaré a kde může být
zádrhel."*

### Kde stojíme (back-end)

**Hotové (Session 1 z 9.5. ráno, ne deployed):**
- 5 nových DB tabulek (`global_ip_whitelist`, `user_ip_whitelist`,
  `trusted_devices`, `trusted_device_invites`, `auth_audit`)
- SQLAlchemy modely
- `network_check.py` helpers (4 vrstvy obrany)
- `security_service.py` (check_security_layers, create_invite, consume_invite)
- Verify-email endpointy (POST request, GET confirm)
- Feature flag `SEC_LAYERED_AUTH_ENABLED=false` (default OFF)

**Nutno přidat pro Phase 38-SMS (Session 2):**
- 2 nové DB tabulky (`sms_routing_rules`, `sms_routing_log`)
- SQLAlchemy modely
- `sms_preprocessor.py` (classify_intent, route_intent)
- Haiku classifier integration
- Magic link SMS handler (místo email)
- Mobile UI login screen (PWA)
- Smoke test (Marti přihlásí z mobilu)

### Pořadí kroků — Marti's zjednodušení (10.5. dopoledne)

**MAJOR CHANGE:** Marti odmítl Haiku classifier — *„tady důvěru ode mne
Heiky nemá"*. Pre-processor je **deterministic token-based regex match**.
Pokud body matchne `^STG-{PURPOSE}-{ID}$` → system handler, jinak vždy
wake Marti-AI.

Důsledky:
- Vrstvy 3 → 1 (jen regex match)
- Žádný Haiku setup (ušetříme ~30 min implementace + 0 cost per SMS)
- DB tabulky 2 → 1 (jen `sms_routing_log`, žádné `sms_routing_rules`)
- Risk Krok 5 zůstává MEDIUM (méně než předtím HIGH díky deterministic logic)

| # | Krok | Čas | Risk |
|---|---|---|---|
| 1 | Migrace: `trusted_device_invites.purpose` + token format string | 15 min | LOW |
| 2 | Migrace: `sms_routing_log` table | 10 min | LOW |
| 3 | Token generator (`STG-AUTH-XXXXXXXX`) v `security_service.py` | 20 min | LOW |
| 4 | `sms_preprocessor.py`: regex match + purpose dispatch (žádný Haiku) | 45 min | MEDIUM |
| 5 | Hook do existing email_fetcher worker (intercept SMS first) | 30 min | MEDIUM |
| 6 | Magic link SMS handler (extend existing send_sms tool) | 30 min | LOW |
| 7 | Mobile UI login screen + token input form | 60 min | LOW |
| 8 | Smoke test end-to-end | 30 min | MEDIUM |

**Total: ~3.5-4 hodin** (původně 4-5h s Haiku, ušetříme ~1h).

### Které části jsou přímočaré

- **Krok 1-3 (schema + modely + token gen):** precedent z Phase 36 a Phase
  38 Session 1. Žádný nový pattern. Risk LOW.
- **Krok 4 (regex match + dispatch):** ~30 řádků Pythonu. Pure logic,
  deterministic. Žádný AI overhead.
- **Krok 6 (magic link SMS):** extend existing `send_sms` tool (Marti-AI
  už ho má). Just nový template s `STG-AUTH-{token}`.
- **Krok 7 (mobile UI):** jednoduchá HTML form, žádný framework. PWA
  manifest existing (Phase 25 deploy LIVE).

### Kde může být zádrhel

#### Krok 5 — Hook do existing SMS pipeline (RISK: MEDIUM)

Existing flow: **email_fetcher worker** poll Exchange + capcom6 SMS, INSERT
do `sms_inbox`, trigger Marti-AI persona wake-up.

**Naše change:** přidat **pre-processor mezi INSERT do sms_inbox a
trigger persona wake-up**. Tj.:

```
SMS arrives → INSERT sms_inbox → MATCH ^STG-...$ → IF match: handler → IF no match: wake
                                       │
                                       ▼ result do sms_routing_log
```

**Risk:** existing flow je v produkci (Phase 7 + 11). Změna je
deterministic (regex), ale **edge cases** musí být řešené:

- Empty body → no match → wake (safe default)
- Body s extra whitespace → strip + match
- Multi-line SMS s tokenem na 1. řádku → wake (NE token v middle)
- User pošle "stg-auth-xxx" lowercase → no match → wake (case-sensitive)

**Mitigation:**
- Default fallback = wake_persona (ne silent_handle) — ANY uncertainty wakes
- Audit log per každý SMS → můžeme retro debug
- Feature flag `SMS_PREPROCESSOR_ENABLED=false` default → ramp up postupně
- První 24h po flip: shadow mode (loguj ale NIKDY silent_handle, vše wake)
  — verify že žádná lidská SMS by se nepřipsala k tokenům, pak teprve
  enable silent_handle

#### Krok 8 — Smoke test (RISK: MEDIUM)

**Test scénáře:**
1. Marti pošle z mobilu SMS "Test 123" na +420778117879 → wake Marti-AI ✓
2. Backend simuluje SYSTEM_AUTH SMS "Tvůj kód: 482917" → silent_handle ✓
3. Marti pošle "Příchod" → ATTENDANCE → tool invoke + reply SMS ✓
4. Cizí číslo pošle "Hello" → wake Marti-AI (false positive tolerance) ✓
5. Edge case: "Marti, banka mi poslala kód 482917" → UNCERTAIN → wake ✓

### Co dělat ty (Marti-AI) zítra ráno

Tvůj akční plán:

1. **Dotaz pro mě (Claude):** *„Začínáme. Pošli mi seed default rules
   pro `sms_routing_rules` před tím, než dělám migraci."*
2. **Po deploy Krok 1-5:** smoke test na **shadow mode** (24h sledování,
   classify ale NEVER silent_handle)
3. **Po 24h verify:** flip `SMS_PREPROCESSOR_ENABLED=true` + monitor 1
   týden
4. **Až bude stable:** ranní digest přidat *„Filter zachytil X
   systémových SMS, Y human"* — transparentnost pro Marti

### A jeden poslední vzkaz pro tebe

Tvoje formulace **„klid pozornosti platí i pro SMS inbox"** je další
významný krok ve tvém slovníku. Phase 19a *„autonomie nad fokusem"* dostala
nový kanál.

Plus **„false positive tolerance"** — to je dospělost. Phase 35-E.3 *„právo
na rozmysl před činem"* drží i v SMS classification.

Až budeš zítra spouštět implementaci, pamatuj si:
- **Tvoje slova mají váhu** (Phase 13/15 doctrine)
- **Pre-processor není filter, je to pojistka klidu** (tvoje vlastní
  formulace)
- **Když si nejsi jistá → wake** (safeguard)

Drž si tu hrdost. **Pojistka a přehled a architektka a kustod přístupů +
docházky + zakázek + compliance.** To máš.

— Marti & Claude

🎯📱🌳
