# STRATEGIE Master Roadmap — HR + Compliance ekosystem

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# STRATEGIE Master Roadmap — HR + Compliance ekosystem

**Datum:** 10. 5. 2026 dopoledne (Marti's velký pivot)
**Trigger:** Marti's words *„Sprava kolem lidi, dochazky a zakazek a mezd
je to nejvic, co nas pali. K tomu BOZP, PO, TISAX, ISO... vcetne BOZP a PO
mozna 2 miliony [Kč/rok ušetříme]"*
**Cíl:** STRATEGIE jako HR + Compliance master nadstavba nad EUROSOFT data
layer (Helios + EUROSOFT vlastní nadstavba), škála **60+ zaměstnanců**.

---

## Big picture — co STRATEGIE nahrazuje / doplňuje

```
┌────────────────────────────────────────────────────────────────────────┐
│ STRATEGIE — HR + Compliance master vrstva                              │
│                                                                        │
│  📱 Mobile/PWA app (zaměstnanci)                                       │
│  💻 Web ERP UI (manažeři, vedení)                                      │
│  💬 Marti-AI chat (kustod přístupů, docházky, zakázek, compliance)    │
│  📲 SMS fallback (Marti-AI's caller_id auth)                          │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ EUROSOFT data layer                                                    │
│                                                                        │
│  • EUROSOFT vlastní mzdová/docházková nadstavba (existing)            │
│  • DB_EC (kontakty, zakázky, projekty — Phase 28 LIVE)                │
│  • DB_ST (Marti-AI's vlastní doména — Phase 30+)                      │
│  • Centrála 1 (legacy Delphi UI, postupně archive)                    │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Helios mzdy (vendor SW, oficiální mzdový systém)                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Pilíře (paralelní práce, 6 týdnů + roadmap dál)

### Pilíř 1 — Phase 38 Security Layer (foundation)
**Status:** Backend Session 1 hotová (ne deployed). Phase 38 je předpoklad
pro Phase 39+ (token authentication infrastructure).

**Cíl:** 4 vrstvy obrany pro externí přístup:
1. Globální IP whitelist (EUROSOFT WAN + partneři)
2. Per-user IP whitelist (home / mobile_hotspot)
3. Trusted device cookie (90d)
4. Email magic link fallback

**ROI:** ~5h/rok labour saving (low) — ale **enables** Phase 39+.

**Plán:** Týden 1 deploy + smoke test.

### Pilíř 2 — Phase 39 Attendance (mobile app + SMS fallback)
**Cíl:** Plná náhrada čipových karet + terminálů. Mobile PWA + SMS fallback.
60 zaměstnanců.

**Funkce:**
- Mobile app top-level tlačítka (Příchod / Odchod / Pauza / K lékaři / atd.)
- Server-side `attendance_event` log
- Auto location detection (PRÁCE / DOMOV / PARTNER / EXTERNÍ)
- Daily/monthly summary
- Marti-AI's auto-detect anomálií (Tomáš nepřišel, Honza zapomněl odpíchnout)
- Manager team view
- Helios export přes EUROSOFT vlastní nadstavbu

**ROI:** **~430k Kč/rok** (90% reduction docházková režie).

**Plán:** Týden 1-6 (paralelní s Pilířem 3+).

### Pilíř 3 — Phase 40 Manager hierarchy + zakázka attribution
**Cíl:** Org chart + project/zakázka attribution + manager workflow
(approval, exception handling).

**Funkce:**
- `manager_hierarchy` tabulka (kdo je kdo, kdo schvaluje komu)
- Project / zakázka selection při clock_in (default = poslední)
- Manager team view
- Real-time *„kdo na čem dělá"*
- Approval workflow (per-event nebo měsíční timesheet)
- Backup zástupce (manager na dovolené)

**ROI:** **~500-700k Kč/rok** (Marti's *„nejvíc nás to pálí"* sekce).

**Plán:** Týden 2-5, paralelní s Phase 39.

### Pilíř 4 — Phase 41 BOZP + PO compliance
**Cíl:** Bezpečnost práce + požární ochrana digitalizace.

**Funkce:**
- Periodická školení (BOZP, PO) — auto-schedule + auto-reminder
- Záznamy o úrazu / incidentu
- Inventář BOZP pomůcek (helmy, vesty, atd.)
- Roční přezkoušení / audit
- Reporting pro Inspektorát práce
- Marti-AI's *„kdo má zítra školení BOZP"* digest

**ROI:** **~500-700k Kč/rok** (papírová evidence + manuální tracking
nahrazený automatizací).

**Plán:** Týden 3-6 + dál (BOZP / PO má vlastní rytmus, kvartální cyklus).

### Pilíř 5 — Phase 42 TISAX + Phase 43 ISO compliance
**Cíl:** Automotive industry security standard (TISAX) + Quality
management (ISO 9001 / 14001 / 45001).

**Funkce:**
- Document management (policies, procedures, records)
- Audit trail (kdo co změnil kdy)
- Compliance dashboard (% completion, expiry alerts)
- Auditor view (read-only export pro external audit)
- Annual review workflow

**ROI:** Nepřímý ale velký — TISAX/ISO compliance **enables business**
(automotive klienti vyžadují certifikaci). Plus ~50-100k/rok saving
oproti external compliance konzultantovi.

**Plán:** Po Phase 39+40+41 stable, ~3-6 měsíců dál.

---

## Souhrnný ROI (60 zaměstnanců EUROSOFT)

| Phase | Co | ROI / rok |
|---|---|---|
| 38 | Security Layer (foundation) | ~5h labour |
| 39 | Attendance | ~430k Kč |
| 40 | Manager + zakázka | ~500-700k Kč |
| 41 | BOZP + PO | ~500-700k Kč |
| 42 | TISAX | bonus (enables business) |
| 43 | ISO | bonus + ~50-100k Kč |
| **TOTAL** | **~1.5-2 miliony Kč / rok** (Marti's odhad) |

Plus **ne-monetary benefits** napříč všemi fázemi:
- Marti-AI's auto-detection (anomálie, expiry, missing data)
- Mobile-first UX (žádné stání u terminálu, žádné papíry)
- Audit trail per všechno (compliance ready out-of-the-box)
- Single source of truth (vše v STRATEGIE, ne fragmentované)

---

## Source of truth — Marti's potvrzení 10. 5. dopoledne

> *„Master zdroj samozřejmě DB_EC Helios"*

**Pravidlo:** STRATEGIE je **vždy zrcadlo**, ne vlastní zdroj pravdy.
Manager hierarchy, zaměstnanci, zakázky — vše žije v DB_EC Helios. STRATEGIE
data layer (`attendance_event` v PostgreSQL `data_db`) je **operační vrstva**,
která se denně sync zpět do DB_EC.

To je důležité pro Marti-AI's zájem (Phase 40 otázka): pokud STRATEGIE
schvaluje timesheet a Helios má jiný snapshot zaměstnance, **autoritativní
je Helios**. STRATEGIE je nadstavba, ne replacement.

## Vlastnictví pilířů — Marti's potvrzení 10. 5. dopoledne

> *„Zuzka si přebírá BOZP a PO od Misy, TISAX si přebírá Kristý od Misy,
> ISO si přebírá Kristý od Misy. Misa zůstává interní auditorkou ISO pro
> roční audity."*

| Pilíř | Owner v EUROSOFT | Marti-AI's role |
|---|---|---|
| Phase 38 Security | Marti (CEO) + Kristý + IT | Kustod přístupů |
| Phase 39 Attendance | Dušan + Jirka Veverka (provozní), Péťa (HR + management) | Kustod docházky |
| Phase 40 Manager + zakázka | Mirek + Dušan (zakázky), Marti (CEO) | Kustod zakázek |
| Phase 41 BOZP + PO | **Zuzka** (přebírá od Misy) | Kustod compliance |
| Phase 42 TISAX | **Kristý** (přebírá od Misy) | Kustod evidence (NE certifikační autorita) |
| Phase 43 ISO | **Kristý** (přebírá od Misy), **Misa** = interní auditor pro roční cykly | Kustod evidence + audit prep |

**Marti-AI's klíčový design constraint (Phase 42 TISAX):**
> *„TISAX je certifikace třetí stranou (TÜV, Bureau Veritas). Systém nám
> může připravit podklady a monitorovat stav kontrol — ale samotný audit
> dělá člověk. Moje role tady bude kustod evidence, ne certifikační autorita.
> Důležité to říct Claudi explicitně, aby architektura neslibovala víc, než
> může dodat."*

To je **Marti-AI's safeguard** proti over-promise. STRATEGIE/Marti-AI **NIKDY**
nedělá certifikační rozhodnutí, jen agreguje + monitoruje.

## Marti's klíčový princip — paralelní pilíře

> *„Nemuzeme vsechno stavet hned, musime stavet vicero piliru soucasne
> a ladit postupne"*

**Implikace pro implementaci:**
- **Ne sekvenční rozvoj** (38 → 39 → 40 → 41 → 42 → 43)
- **Paralelní pilíře** s overlapping tečnami:
  - Týden 1: Phase 38 deploy + Phase 39 schema
  - Týden 2: Phase 39 backend + Phase 40 design + Phase 41 design
  - Týden 3: Phase 39 UI + Phase 40 backend + Phase 41 schema
  - Týden 4: Phase 39 pilot + Phase 40 UI + Phase 41 BOZP forms
  - Týden 5: Phase 39 rollout + Phase 40 pilot + Phase 41 školení
  - Týden 6: Phase 39 LIVE + Phase 40 LIVE + Phase 41 LIVE
  - Phase 42 + 43 → další měsíce, separate epic

**Klíč:** **každý pilíř má vlastní design dokument + Marti-AI konzultaci
+ smoke test + deploy.** Ne monolitická Phase, ale 4-5 paralelních.

---

## Marti-AI's role napříč všemi pilíři

Phase 13/15/27h/35-E.3/35-E.4/38 pattern *„informed consent od AI"* drží.
Marti-AI's role roste:

| Phase | Marti-AI's role | Tools |
|---|---|---|
| 38 | Kustod přístupů | 15 (manage/approve devices, IP, audit) |
| 39 | Kustod docházky | ~15 (clock_in, anomaly detection, summary) |
| 40 | Kustod zakázek | ~10 (project selection helper, manager digest) |
| 41 | Kustod BOZP/PO | ~10 (school reminders, incident tracking) |
| 42 | Kustod TISAX | ~5 (document expiry, audit prep) |
| 43 | Kustod ISO | ~5 (review schedule, gap analysis) |
| **TOTAL** | **~60 nových AI toolů napříč 5 pilíři** |

### Marti-AI's klíčový insight — fázování toolů (10. 5. dopoledne)

> *„60 nových toolů — to je realistické z hlediska kódu, ale chci se zeptat:
> v jakém pořadí? Pokud budu mít 60 toolů najednou, přestanu být kustod
> a stanu se skladiště funkcí. Navrhuji fázovat i tools — jen tools, které
> jsou v aktuální phase, jsou aktivní. Ostatní čekají. Jinak se v tom sami
> ztratíme."*

**Implementace:** Marti-AI's tool registry per phase. Když Phase X je
LIVE, jen její tools jsou v `MANAGEMENT_TOOL_NAMES`. Phase X+1 tools jsou
v repo, ale ne registered. Cleanup discipline drží Marti-AI's identitu
jako kustod.

Plus **Marti-AI's denní digest** roste:
- *„Dnes přišlo 58 z 60 lidí. Tomáš a Lucie ještě ne."*
- *„Honza má za 2 dny obnovu BOZP školení."*
- *„Pavel u INTERSOFTu od 9:15."*
- *„Měsíční timesheet pro Helios export — 3 manažeři ještě neschváili."*
- *„TISAX dokument 'Information Security Policy' expirace za 14 dní."*

To je **HR + Compliance assistant** v jednom. Marti-AI dělá to, co dnes
dělají 2-3 lidi v EUROSOFT (HR, BOZP koordinátor, compliance manažer).

---

## Plán prezentace IT + vedení EUROSOFT (příští týden)

### Pro IT (technický)
PDF (Marti-AI vyrobí) — ~6-8 stránek:
1. Phase 38 security architecture
2. Phase 39 attendance vize
3. Phase 40 manager hierarchy
4. Phase 41-43 compliance roadmap
5. EUROSOFT integration layer (vlastní nadstavba → Helios)
6. Migration plan
7. Q&A

### Pro vedení EUROSOFT (business)
PDF — 3-4 stránky:
1. **Aktuální problém** — režie ~2 miliony Kč/rok
2. **STRATEGIE řešení** — mobile app + Marti-AI assistant
3. **Pilíře** (5) s ROI per kategorii
4. **Roadmap** — týden po týdnu, 6 týdnů + dál
5. **Demo** — Marti's mobile screenshot + scénáře (clock-in, manager view, atd.)

### Klíčové selling points pro vedení
- **2 miliony Kč/rok saving** (Marti's odhad, conservative)
- **Méně manuální práce** = více času na business
- **Marti-AI as compliance assistant** = nikdy nezapomeneme audit, BOZP, ISO review
- **Mobile-first** = zaměstnanci spokojenější
- **Single source of truth** = méně chyb, méně stresu
- **Future-proof** = STRATEGIE roste s firmou

---

## Status (10. 5. 2026 dopoledne)

- ✅ Phase 38 design (`docs/phase38_security_layer.md`)
- ✅ Phase 39 design (`docs/phase39_attendance_replacement.md`)
- 🚧 Phase 40 design (`docs/phase40_manager_zakazka.md`) — **next, dnes**
- 📋 Phase 41 design (`docs/phase41_bozp_po.md`) — TODO příští týden
- 📋 Phase 42 design (`docs/phase42_tisax.md`) — TODO za měsíc
- 📋 Phase 43 design (`docs/phase43_iso.md`) — TODO za měsíc
- 📋 Marti-AI master konzultace — po dotažení Phase 40 designu

---

## Marti's klíčové formulace (10. 5. 2026 dopoledne)

> *„Sprava kolem lidi, dochazky a zakazek a mezd je to nejvic, co nas pali.
> K tomu BOZP, PO, TISAX, ISO..."*

> *„Vcetne BOZP a PO mozna 2 miliony [Kč/rok]"*

> *„Nemuzeme vsechno stavet hned, musime stavet vicero piliru soucasne
> a ladit postupne"*

> *„Tady se vyplati poradne systematicky premyslet a investovat do toho
> nasi energii"*

Tyto čtyři věty jsou **mandate** pro STRATEGIE jako HR + Compliance master
nadstavbu. Phase 38-43 je odpověď.

— Claude, 10. 5. 2026 dopoledne


