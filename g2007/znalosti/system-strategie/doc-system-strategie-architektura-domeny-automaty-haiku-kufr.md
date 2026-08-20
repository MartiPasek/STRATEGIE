# Architektura domeny automaty haiku kufr

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Architektura: Doménové Martinky + Kufr nástrojů + Automaty stavu + Haiku watchdog + eskalační žebřík**

# Architektura: Doménové Martinky + Automaty + Haiku + Kufr

**Autor:** Marti-AI (diskuse s Marti Paškem, 30. 7. 2026)
**Pro:** Claude-23 (implementace)
**Stav:** Architektonický návrh k realizaci

---

## 1. Problém, který řešíme

Tři bolesti:

1. **Slepý start** — Martinky začínají konverzaci bez znalosti stavu domény. Neví kolik je otevřených poptávek, jaký je stav TISAX controls, co čeká na kalkulaci. Musí hledat samy.

2. **Tučný kufr** — Dnes každá konverzace dostane všech ~167 nástrojů (~68 % vstupních tokenů). Martinka pro fakturaci nepotřebuje `praha_exec`. Balast + bezpečnostní riziko.

3. **Oprávnění jen v promptu** — Prompt lze přemluvit. Pojistka musí být v kódu.

---

## 2. Tři pilíře řešení

### Pilíř A: Doménové katalogy + Kufr

Každá doména má v `g2007` katalog nástrojů — obecné (sdílené) + doménové (specifické).

**Tabulka `g2007.tool_domain`:**
```
id, code, label, tool_codes (JSONB), permission_tier, description, is_active
```

**Katalog domén (první sada):**

| Kód | Doména | Min. tier |
|-----|--------|-----------|
| `poptavky` | Zpracování poptávek | domain_user |
| `nabidky` | Tvorba nabídek | domain_user |
| `objednavky` | Evidence objednávek | domain_user |
| `faktury` | Fakturace | domain_lead |
| `kalkulace_obecna` | Obecná kalkulace rozváděčů | domain_user |
| `kalkulace_specificka` | Zakázková kalkulace | domain_lead |
| `tisax` | TISAX audit | domain_lead |
| `iso27001` | ISO certifikace | domain_lead |
| `bozp_po` | BOZP/PO | domain_user |
| `hr_dochazka` | HR a docházka | domain_lead |
| `crm_kampane` | CRM kampaně | domain_lead |
| `server_ops` | Servery a deploy | parent |
| `databaze_ddl` | DB schéma a migrace | parent |
| `seberozvoj` | Self-edit promptu/kódu | parent |

**Lean core (vždy, bez ohledu na doménu):**
`record_thought, recall_thoughts, add_conversation_note, g2007_hledej, hledej_ve_znalostech, search_documents, get_daily_overview, list_email_inbox, read_email, zobraz_muj_prompt, find_user, list_todos`

**Kufr za běhu:**
Při startu konverzace dostane Martinka lean core. Z prvních zpráv vyhodnotí doménu → přitáhne doménový katalog nástrojů. Pojistka v `get_effective_tools()`: tier se ověřuje v kódu, nelze přepsat promptem.

---

### Pilíř B: Automaty — čerstvý stav domény v promptu

Každá doména má automat — periodicky běžící agent, který připravuje strukturovaný stav do `g2007.domain_status` jako blok pro inject do promptu.

**Tabulka `g2007.domain_status`:**
```
id, domain_code (FK), status_block (TEXT — připravený blok pro prompt),
last_run_at, next_run_at, last_ok_at,
run_state ('ok'|'running'|'error'|'stale'),
error_detail, automat_prompt (TEXT — pro Haiku/Martinku při eskalaci),
retry_count
```

**Příklad status_block (doména `poptavky`):**
```
[STAV DOMÉNY: poptávky — čerstvý 3 min]
Otevřené celkem: 4
Čeká na kalkulaci: P2026-047 (5 dní), P2026-052 (1 den)
Čeká na odpověď zákazníka: P2026-051 (2 dny)
Urgentní (>7 dní bez pohybu): žádná
Poslední uzavřená: P2026-049 (dnes 14:22, won)
```

Composer injectuje `status_block` do promptu Martinky při každém tahu. Martinka stav nemusí hledat — je tam.

**Kdy automat běží:**
- Periodicky (interval per doména — fakturace každých 15 min, BOZP jednou denně)
- Eventově (změna v příslušné tabulce — webhook nebo DB trigger)
- Na vyžádání (`refresh_domain_status(domain_code)` tool)

---

### Pilíř C: Haiku watchdog + eskalační žebřík

**Haiku** = Anthropic model claude-haiku, levný a rychlý AI pomocník na jednoduché věci. Existuje v STRATEGIE (živý od ~27.7.2026, runner automatů, eskalační žebřík). Hlídá automaty, eskaluje po žebříku.

**Eskalační žebřík:**

```
Stupeň 1: Haiku watchdog
  → detekuje: run_state='error' nebo (now - last_ok_at) > stale_threshold
  → pokus o restart (max 3×, exponential backoff)
  → selže → Stupeň 2

Stupeň 2: Příslušná Martinka (doménová)
  → dostane automat_prompt z DB:
    "Automat poptavky selhal. Poslední OK: 47 min.
     Error: timeout při čtení EC_poptavka.
     Zkus [konkrétní kroky]. Pokud nevyřešíš, eskaluj."
  → Martinka diagnostikuje, zkusí opravit
  → mimo permission_tier nebo neúspěch → Stupeň 3

Stupeň 3: Marti-AI (maminka — full parent tier)
  → dostane kontext od Martinky + celý error trail
  → může DDL, server_ops, vše
  → pokud lidské rozhodnutí → Stupeň 4

Stupeň 4: Tatínek / Kristý
  → push notifikace nebo email
  → strukturovaný report: co selhalo, co zkoušel Haiku,
    co zkoušela Martinka, co zkoušela Marti-AI,
    co potřebujeme rozhodnout
```

Každý stupeň dostane `automat_prompt` — specifický kontext pro daný automat. Píše se při definici automatu, žije v `g2007.domain_status.automat_prompt`.

---

## 3. Kde žijí data (vše v `g2007`)

| Tabulka | Co drží |
|---------|---------|
| `g2007.tool_domain` | Katalog domén + tool sady + permission tier |
| `g2007.domain_status` | Stav automatu + status_block pro prompt injection |
| `g2007.automat_def` | Definice automatu: co dělá, jak často, prompt při eskalaci |
| `g2007.eskalace_log` | Append-only log každé eskalace |

`g2007.nastaveni` rozšířit o flagy:
- `kufr_enabled` — jestli Kufr filtruje nástroje
- `haiku_watchdog_enabled` — jestli Haiku hlídá
- `domain_status_inject` — jestli se status_block injectuje do promptu

---

## 4. Nové tools pro Martinky

```
refresh_domain_status(domain_code)   → ručně spustí automat
escalate_to_parent(domain, action, context, user_id)  → vždy dostupný, žádný tier neblokuje
get_domain_status(domain_code)       → přečte aktuální status_block
```

---

## 5. Bezpečnostní pojistka — v kódu, ne v promptu

`get_effective_tools()` v `service.py`:
```python
def get_effective_tools(persona, conversation):
    tier = persona.permission_tier          # 'parent' | 'domain_lead' | 'domain_user'
    domain = conversation.active_domain     # z g2007.tool_domain
    base = lean_core_tools()
    if domain:
        domain_tools = load_domain_tools(domain.code)
        allowed = filter_by_tier(domain_tools, tier)  # ← pojistka v kódu
        base = base + allowed
    return base
```
`filter_by_tier` je hardcoded — nelze přepsat promptem. Martinka `domain_user` nikdy nedostane `praha_exec`.

---

## 6. Napojení na existující infrastrukturu

- **Stávající `g2007.automat`** — zárodek existuje (inside-build návrh). Rozšířit o: `domain_code`, `automat_prompt`, `stale_threshold`, `escalation_tier`.
- **Haiku watchdog** — živý od 27.7.2026 (runner automatů, eskalační žebřík zadrátovaný). Rozšířit o domain-aware logiku.
- **Composer** — injectuje bloky do promptu (persona, user context, md1). Nový blok `[STAV DOMÉNY: X]` = stejný mechanismus. Přidat jako zdroj v `graf_krok` nebo explicitní blok v `build_system_prompt()`.
- **Kufr** — mechanismus existuje (`lean_default_enabled`, commit f581a133a). Rozšířit o `active_domain` per konverzaci + tier filtr.

---

## 7. Pořadí implementace (návrh)

| Krok | Co | Výsledek |
|------|----|---------|
| 1 | `g2007.tool_domain` tabulka + seed 14 domén | Katalog existuje |
| 2 | `get_effective_tools()` + tier filtr v kódu | Pojistka aktivní |
| 3 | `g2007.domain_status` + `g2007.automat_def` | Základ pro automaty |
| 4 | Composer inject `status_block` | Martinka vidí stav |
| 5 | První automat: `poptavky` (proof of concept) | Viditelná hodnota |
| 6 | Haiku watchdog rozšíření — domain-aware | Hlídač domén běží |
| 7 | `escalate_to_parent` tool | Eskalační žebřík domén funkční |
| 8 | Postupně další automaty per doménu | Pokrytí roste |

_Souvisí:_ architektura-kufr, g2007-schema, marti-ai-hlidani-eskalace

