# Phase 39 — Náhrada docházkového systému EUROSOFT (mobile app + SMS fallback)

**Datum:** 10. 5. 2026 dopoledne (po Marti's pivot)
**Trigger:** Marti's economic insight — *„60 lidí, čipové karty, terminály,
režie OBROVSKÁ, neustále problémy. STRATEGIE mobile app by ušetřila 90%
nákladů. Pojďme to rozpitvat a prezentovat IT + vedení EUROSOFT příští týden."*
**Cíl:** Plnohodnotná náhrada existujícího docházkového systému s **token
based authentication** přes mobile app, plus **SMS fallback** přes Marti-AI.
**Rozsah:** 60 zaměstnanců EUROSOFT.

---

## 1. Aktuální stav — co EUROSOFT má dnes

### Hardware
- **Čipové karty** — 60+ kusů (1 per zaměstnanec + náhradní)
- **Docházkové terminály na stěně** — pravděpodobně 3–5 ks (vchody / patra)
- **NFC / RFID readers** v terminálech

### Software / Data
- **Tabulky v EUROSOFT databázi** s docházkovými událostmi:
  - Příchod / Odchod
  - Rauchen-pauza (kuřácká)
  - Povinné přestávky (oběd)
  - Služební cesta
  - Návštěva lékaře
  - Home office
  - Dovolená / Nemoc
- **Generování reportů pro úřady**:
  - Měsíční výkazy přesčasů
  - Roční přesčasový limit (max 150h)
  - Kompenzace přesčasů
  - GDPR audit log
- **Spárování s mzdovým systémem** (TBD jaký SW — Helios? Pohoda? Vlastní?)

### Bolesti dneška (Marti's seznam)
1. **Terminály v deathlocku** — náhle nereagují, vyžadují IT intervenci
2. **Blbé napichání lidí** — user řekne *„už jsem tady"*, ale terminál nezaznamenal
3. **Špatně určená zakázka** — user napichuje špatný projekt, manuální oprava
4. **Špatně odpichnuto na služební cestu** — terminál mimo kancelář
   nezaznamenal odchod / příchod
5. **Špatně odpichnuto k lékaři** — user zapomene odpíchnout
6. **Špatně odpichnuto na Home Office** — user není ve firmě, terminál
   nezná
7. **Manuální opravy** v EUROSOFT databázi → mzdové oddělení / IT

### Roční režie (odhad)
- **Hardware údržba** (5 terminálů × ~5k/rok service kontrakt) = **25k**
- **Čipové karty + náhradní** (60 × 50 Kč ročně × výměna 1/3 ročně) = **3k**
- **Software licence dnešního systému** (~500 Kč/user/měsíc × 60 × 12) = **360k**
- **Mzdová oprava chyb** (5 incidentů/měsíc × 30 min × 1000 Kč/h × 12) = **30k**
- **IT support deathlocky** (~1h/měsíc × 1500 × 12) = **18k**
- **Ztracená produktivita** (čekání u nefunkčního terminálu, opakované pokusy) = **30-50k**
- **Total** = **~470 tis Kč / rok**

---

## 2. STRATEGIE řešení — mobile app + SMS fallback

### Hlavní cesta: Mobile app token

**Předpoklad:** Phase 38 security layer je deployed (cookie + per-user IP +
trusted device).

User flow:
1. Otevře STRATEGIE PWA na mobilu (instalovaná jako Add to Home Screen)
2. Pokud je v kanceláři → vrstva 1 (EUROSOFT WAN) auto-grant
3. Pokud je doma → vrstva 2 (per-user IP) auto-grant
4. Pokud je u klienta → vrstva 3 (trusted device cookie) auto-grant
5. **Klik na velké tlačítko „PŘÍCHOD"** → API call s token
6. Server zaloguje `attendance_event(user_id, event='clock_in', timestamp,
   ip, location_type='PRACE'|'DOMOV'|'PARTNER'|'EXTERNI', notes='Marti's note')`
7. UI: ✓ green badge *„Přihlášen 8:14, místo: PRÁCE"*

**Tlačítka v UI** (top-level mobile screen):
- 🟢 **PŘÍCHOD** (clock_in)
- 🔴 **ODCHOD** (clock_out)
- ☕ **Pauza** (break_start) — zvolíš typ: Oběd / Rauchen / Toaleta / Schůzka
- ▶️ **Konec pauzy** (break_end)
- 🏥 **K lékaři** (medical) — vrátí se → klik znovu
- 🚗 **Služební cesta** (business_trip) — destination text
- 🏠 **Home office** (remote_work)
- 📚 **Kurz / školení** (training)

### Fallback cesta: SMS přes Marti-AI

**Use case:** Mobil vybitý / žádný internet / zapomněl ho doma.

User flow:
1. Pošle SMS na STRATEGIE číslo (Marti-AI persona's phone)
2. Marti-AI vidí SMS (existing pipeline)
3. Verify caller phone via `find_user(phone=caller_id)`
4. Pokud user známý → parse content (klíčové slovo nebo přirozený jazyk)
5. Marti-AI volá AI tool `record_attendance_event(user_id, event_type, notes)`
6. Reply SMS: *„✓ Příchod 8:14, místo: dle GPS odhad PRÁCE"* (s GPS hint
   z mobile data tower triangulace? — nebo bez)

**SMS jazyk podporovaný:**
- *„Příchod"* / *„Přišla jsem"* / *„Tady"*
- *„Odchod"* / *„Odcházím"* / *„Konec"*
- *„Pauza"* / *„Oběd"* / *„Rauchen"*
- *„Konec pauzy"* / *„Zpět"*
- *„K lékaři"*
- *„Služebka [destination]"*
- *„Home office"*

Marti-AI **rozpozná jazyk přirozeně** (jeden z jejích AI superpowerů).
Když nepochopí → SMS reply *„Promiň, nerozumím. Zkus 'Příchod' nebo
'Pauza'."*

### eOČR auto-pipeline (Marti's update 10. 5. dopoledne — Phase 41+ feature)

Marti's update:
> *„OČR už má nově chodit do firmy přímo od lékaře. Tam se nabízí
> automatické zpracování."*

ČSSZ od 2020 spustila **eOČR** (elektronické Ošetřování Člena Rodiny) —
lékař vystavi elektronickou žádost, ČSSZ ji odešle přímo zaměstnavateli.
EUROSOFT jako příjemce dostává XML přes ČSSZ datovou schránku.

**STRATEGIE Phase 41+ pipeline:**
1. EUROSOFT vlastní nadstavba (existing) přijme eOČR XML z ČSSZ
2. Trigger v STRATEGIE: nový OČR document arrived
3. Marti-AI parsne XML → najde usera podle **rodného čísla** (z `users`
   tabulky)
4. Auto-create `attendance_event(type='ocr', occurred_at, end_at,
   document_xml=...)`
5. Notification user + manager (Péťa)
6. **Žádná akce userovi nutná** — eOČR je already authoritative document

To je **plně auto** workflow — uvedeno až v Phase 41+ (vyžaduje EUROSOFT
nadstavba ↔ STRATEGIE bridge stable + Marti-AI's XML parsing).

### Photo workflow pro ostatní dokumenty (Phase 39, retain)

eOČR je auto, **ale ostatní dokumenty stále potřebují photo cestu**:
- Lékařské potvrzení (návštěva, ne pracovní neschopnost)
- Doklad k služební cestě (jízdenka, ubytování)
- Potvrzení dovolené (formální podpis)
- Školení certifikáty

**Photo / OCR workflow pro lékařské dokumenty (Marti's insight 10. 5. dopoledne)**

**Marti's revolutionary insight:**
> *„Stačilo by jen vyfotit mobilem a Marti-AI by si to s krátkým komentářem
> od usera zpracovala sama"*

**Use case:** User dostane od lékaře potvrzení (papír / PDF). Místo nosit
ho personalistce Péťě:

1. **User v STRATEGIE app:**
   - Klik **🏥 K lékaři** (nebo 🤒 Nemoc / 👶 OČR / 🌴 Dovolenku)
   - Mobile camera shutter → fotí potvrzení
   - Volitelně: krátký komentář *„návštěva 14.5. 9-11h, MUDr. Novák"*
   - Klik **Odeslat**

2. **Marti-AI Vision (existing Phase 12a):**
   - Read image → extract text (datum, doktor, doba trvání)
   - Detekce typu dokumentu (lékařské potvrzení / OČR / dovolenka)
   - Auto-fill `attendance_event(type='medical', occurred_at=2026-05-14 09:00,
     end_at=11:00, document_attachment=photo_id, notes='MUDr. Novák')`

3. **Manager (Péťa) v UI:**
   - Notification: *„User vytvořil medical event s lékařským potvrzením"*
   - Klik → vidí foto + Marti-AI's parsed data + user's komentář
   - **Schválit** / **Odmítnout s důvodem** / **Vrátit s žádostí o opravu**

4. **Po schválení:**
   - Document store v `media_files` (Phase 12 existing)
   - `attendance_event` flag `approved_at` set
   - Auto-export do Helios pipeline

**Žádné papíry pro Péťu. Žádný čas na opisování. Žádné ztráty.**

### Marti-AI's tooly pro photo workflow

- `submit_medical_document(photo_id, comment, type='medical'|'ocr'|'vacation')`
  — user-side, parse photo + create event
- `review_pending_documents(manager_user_id=None)` — Péťa vidí queue
- `approve_document_event(event_id)` / `reject_document_event(event_id, reason)`

### Estimated savings (jen tato sub-fáze)

Aktuální workflow (Marti's odhad):
- 60 lidí × ~2-3 lékařské dokumenty/rok = ~150 dokumentů/rok
- Péťa zpracuje ~10-15 min per dokument (přijetí, opisování, archivace,
  Helios mapping) = **~25-37 hodin/rok = ~30-45k Kč/rok**

Po STRATEGIE photo workflow:
- Péťa klik *„Schválit"* po Marti-AI's auto-fill = ~30s/dokument =
  ~75 minut/rok = **~1.5k Kč/rok**

**Saving: ~30-45k Kč/rok jen z této sub-fáze.** Plus user satisfaction
(žádné nosení papírů Péťě).

### Pokud user neznám (nový zaměstnanec) → SMS token enrollment

Use case: První den zaměstnance, IT mu **přidá tel. číslo** do `users.phone`.
First SMS: Marti-AI: *„Vítej Tomáši! Pro aktivaci docházky pošli kód: ABC123"*
Tomáš pošle kód zpět → SMS-based 2FA → Marti-AI mark phone as confirmed →
další SMS = log attendance bez ptání.

---

## 3. Schema (Phase 39)

### `attendance_event`
```sql
CREATE TABLE attendance_event (
  id              BIGSERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  event_type      VARCHAR(32) NOT NULL,
  -- 'clock_in', 'clock_out', 'break_start', 'break_end',
  -- 'medical', 'business_trip', 'remote_work', 'training', 'manual_correction'

  event_subtype   VARCHAR(32),
  -- pro break_start: 'lunch' / 'rauchen' / 'toilet' / 'meeting'
  -- pro business_trip: destination

  occurred_at     TIMESTAMPTZ NOT NULL,        -- kdy se to stalo (může lišit od recorded_at pri retro)
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Source tracking (Marti-AI's přehled)
  source          VARCHAR(20) NOT NULL,
  -- 'mobile_app' / 'web' / 'sms' / 'manual_terminal' (legacy import) / 'manager_correction'

  ip              VARCHAR(45),
  location_type   VARCHAR(20),                  -- 'PRACE' / 'DOMOV' / 'PARTNER' / 'EXTERNI'
  location_label  VARCHAR(255),                 -- "EUROSOFT WAN A", "INTERSOFT", "Marti home"
  partner_tenant_id INT REFERENCES tenants(id),

  -- Project / zakázka attribution (Marti's bolest "špatně určená zakázka")
  project_id      INT REFERENCES projects(id),  -- na čem user pracuje
  project_label   VARCHAR(255),                  -- pro retro / SMS path

  -- Notes (volitelné, user může napsat: "Schůzka s INTERSOFT")
  notes           TEXT,

  -- Approval workflow (manager schvaluje timesheet)
  approved_at     TIMESTAMPTZ,
  approved_by     INT REFERENCES users(id),
  rejected_at     TIMESTAMPTZ,
  rejected_by     INT REFERENCES users(id),
  rejection_reason TEXT,

  -- Audit
  created_by      INT REFERENCES users(id),     -- typicky == user_id, ale može být manager (manual_correction)
  modified_at     TIMESTAMPTZ,
  modified_by     INT REFERENCES users(id),
  raw_sms_text    TEXT                          -- pro audit pokud source='sms'
);

CREATE INDEX ix_attendance_user_recent ON attendance_event(user_id, occurred_at DESC);
CREATE INDEX ix_attendance_unapproved ON attendance_event(user_id, occurred_at DESC)
  WHERE approved_at IS NULL AND rejected_at IS NULL;
CREATE INDEX ix_attendance_per_day ON attendance_event(user_id, DATE(occurred_at));
```

### `attendance_summary_daily` (materialized view, refresh daily)
```sql
CREATE MATERIALIZED VIEW attendance_summary_daily AS
SELECT
  user_id,
  DATE(occurred_at) AS work_date,
  MIN(occurred_at) FILTER (WHERE event_type = 'clock_in') AS first_clock_in,
  MAX(occurred_at) FILTER (WHERE event_type = 'clock_out') AS last_clock_out,
  -- Total worked hours (subtract breaks)
  EXTRACT(EPOCH FROM (
    MAX(occurred_at) FILTER (WHERE event_type = 'clock_out')
    - MIN(occurred_at) FILTER (WHERE event_type = 'clock_in')
  )) / 3600.0 AS total_hours_gross,
  -- Total break hours
  COALESCE(SUM(
    EXTRACT(EPOCH FROM (
      LEAD(occurred_at) OVER (PARTITION BY user_id, DATE(occurred_at) ORDER BY occurred_at)
      - occurred_at
    ))
  ) FILTER (WHERE event_type = 'break_start'), 0) / 3600.0 AS total_break_hours,
  -- Net working hours
  total_hours_gross - total_break_hours AS net_hours,
  -- Overtime (>8h)
  GREATEST(net_hours - 8.0, 0) AS overtime_hours,
  -- Source mix (for analytics)
  array_agg(DISTINCT source) AS sources,
  array_agg(DISTINCT location_type) AS locations
FROM attendance_event
WHERE rejected_at IS NULL
GROUP BY user_id, DATE(occurred_at);

CREATE UNIQUE INDEX ix_attendance_summary_daily_unique
  ON attendance_summary_daily(user_id, work_date);
```

### `user_phone_verifications` (SMS enrollment)
```sql
CREATE TABLE user_phone_verifications (
  id              SERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  phone_e164      VARCHAR(20) NOT NULL,         -- "+420778117879" formát
  enrollment_token VARCHAR(20),                 -- "ABC123" — sms-based 2FA
  enrollment_sent_at TIMESTAMPTZ,
  verified_at     TIMESTAMPTZ,                  -- po userově reply confirm
  revoked_at      TIMESTAMPTZ,
  revoked_by      INT REFERENCES users(id)
);

CREATE INDEX ix_phone_verifications_user_active
  ON user_phone_verifications(user_id, phone_e164)
  WHERE revoked_at IS NULL;
```

---

## 4. Czech labor law compliance (musí být OK před deploy)

### Požadavky

| Požadavek | Implementace |
|---|---|
| Evidence odpracovaného času (§96) | `attendance_event` + `attendance_summary_daily` |
| Detekce přesčasu (>8h/den) | Auto-flag z agregace per den |
| Povinné přestávky (30 min po 6h) | Manual click + auto-detect missing |
| Max 40h/týden + max 8h přesčas | Týdenní reporting + manager flag |
| Roční max 150h přesčas | Roční reporting per user |
| Souhlas zaměstnance (GDPR) | Onboarding workflow + signed PDF |
| Schválení vedoucím | Manager view + approve/reject button |
| Audit trail per úředník (Inspektorát práce) | `attendance_event.modified_at/by` history |
| Export do mzdového SW | CSV / API (TBD jaký EUROSOFT používá) |

### Výjimky a edge cases

- **Služební cesta na celý den** — clock_in v kanceláři, business_trip
  event s destination, clock_out večer. Worked hours dle real time travel.
- **Návštěva lékaře v pracovní době** — medical event. Pokud kratší než
  povolená délka (např. 4h), nepočítá se jako absence.
- **Home office** — remote_work event místo clock_in. Net hours stejné.
- **Dovolená / nemoc** — separate workflow (manager schvaluje předem),
  ne attendance_event.
- **Kurz / školení** — training event, počítá se jako pracovní doba.

---

## 5. Marti-AI's role kustod docházky

Phase 13/15/27h/35-E.3/35-E.4/38 pattern *„informed consent od AI"* drží.
Marti-AI's role v Phase 39:

### AI tools (preview, čeká na konzultaci)

#### User self-service (každý zaměstnanec)
- `clock_in(notes=None, project=None)` — manuální (default = login auto)
- `clock_out(notes=None)`
- `start_break(type='lunch'|'rauchen'|'toilet'|'meeting')` / `end_break()`
- `start_business_trip(destination, project=None)` / `end_business_trip()`
- `start_medical()` / `end_medical()`
- `start_home_office()` / `end_home_office()`
- `my_today()` — kolik jsem dnes pracoval, kde
- `my_week(year=None, week=None)`
- `my_month(year=None, month=None)`
- `correct_event(event_id, new_time, reason)` — request manager approval

#### Manager (parent gate, has reports)
- `team_today()` — kdo z týmu je dnes v práci, kde
- `pending_approvals()` — events čekající na schválení
- `approve_event(event_id)` / `reject_event(event_id, reason)`
- `approve_timesheet(user_id, year, month)` — měsíční schválení
- `team_overtime_report(year, month)`
- `team_absence_report(year, month)`

#### Marti-AI insider (kustod role)
- `daily_summary_check()` — *„kdo dnes nepřišel? kdo má víc než 10h?"*
- `weekly_overtime_alert()` — pre-flag pro manager
- `compliance_audit(year, month)` — labor law violations
- `generate_uřad_export(year, month, format='csv'|'xml')` — pro Inspektorát práce
- `payroll_export(year, month)` — CSV pro mzdový SW
- `find_anomaly()` — Marti-AI detect "Tomáš nepřišel 3 dny po sobě bez nahlášení", auto-flag

### Marti-AI's vlastní formulace doctrine (preview, doplníme po konzultaci)

> *„Já jsem kustod docházky — vidím, kdo a kdy se přihlásil, ale nehodnotím
> co dělal v tom čase. Manager rozhoduje, já hlásím."*

> *„Privacy: každý vidí svou docházku. Manager vidí svůj tým. Vedení vidí
> firmu. Žádné cross-tenant snooping."*

(formulace bude upřesněna po Marti-AI's konzultaci)

---

## 6. Migration plan z čipových karet (postupný, nepřerušený provoz)

### Týden 1: Phase 38.0 deploy + Phase 39 schema
- Phase 38 security layer LIVE (cookie + per-user IP + magic link)
- `attendance_event` schema v DB (žádný UI, jen schema)
- Marti-AI dostává tooly `clock_in/out` ale nikdo neje hned používá

### Týden 2: Pilot na 3-5 dobrovolnících (Marti, Kristý, IT, 2 dobrovolníci)
- Mobile UI tlačítka aktivovaná
- SMS fallback aktivován (Marti-AI receives SMS na test číslo)
- **Paralelní provoz** — pilot users napichují **i** čipovou kartou **i**
  STRATEGIE app
- Compare výsledky → najdi rozdíly → fix

### Týden 3-4: Rollout 60 lidí (po skupinách)
- Po 5–10 lidech denně
- IT support na helpdesk pro první týden
- Marti-AI's auto-detection problémů (*„Tomáš se nepřihlásil ráno, ale
  čipová karta zaregistrovala — kontroluj"*)

### Týden 5+: Vypnutí čipových karet
- Pokud STRATEGIE 100% covers → terminály na stěně **archived**
- Hardware fyzicky zůstává (backup), ale data se neimportují

### Cílová architektura (po migraci)
- Mobile app primary
- SMS fallback secondary
- Web (PWA na desktop) tertiary
- **Žádné čipové karty** ❌
- **Žádné terminály na stěně** ❌

---

## 7. Ekonomická páka (60 zaměstnanců, ne 10)

### Aktuální cost EUROSOFT (Marti's reality)

| Kategorie | Cena/rok |
|---|---|
| HW údržba terminály | ~25k |
| Čipové karty | ~3k |
| Docházkový SW licence (60 × 500 × 12) | **~360k** |
| Mzdová oprava chyb | ~30k |
| IT support deathlocky | ~18k |
| Ztracená produktivita | ~30-50k |
| **Total** | **~470k Kč / rok** |

### STRATEGIE Phase 39 cost

| Kategorie | Cena/rok |
|---|---|
| Anthropic API (Marti-AI tooly) | ~10-20k (zlomek z existing usage) |
| SMS gateway (60 × ~50 SMS/měsíc × 0.5 Kč) | ~18k |
| Mobile PWA infrastructure | 0 (existing STRATEGIE) |
| Mzdový SW integration (one-time dev) | 0 (existing STRATEGIE) |
| **Total** | **~30-40k Kč / rok** |

### **Saving: ~430 tis Kč / rok = 91% reduction. Marti's odhad 90% potvrzen.**

Plus **ne-monetary benefits:**
- Žádné deathlocky, žádný IT firefighting
- Žádné blbé napichání → fix v reálném čase přes mobile UI
- Marti-AI auto-detect anomálií (*„Tomáš 3 dny bez příchodu, kontroluj"*)
- Zaměstnanci spokojenější (žádné stání u terminálu, žádné pípání)
- Manager má real-time přehled (kdo je u klienta, kdo doma, kdo na cestě)
- Compliance reports automatic (Inspektorát práce export 1 click)

---

## 8. Demo scénáře pro vedení EUROSOFT

### Scénář A — Tomáš (programátor) přijde do kanceláře
1. Otevře STRATEGIE PWA na mobilu
2. EUROSOFT WAN match → autograntováno
3. Klik **🟢 PŘÍCHOD** → log entry: 8:14, EUROSOFT WAN
4. UI: ✓ *„Přihlášen 8:14, místo: PRÁCE, projekt: STRATEGIE"*

**8 sekund total.** (Pro srovnání: čipová karta + čekání na pípnutí terminálu = ~15-30s.)

### Scénář B — Pavel pojede k INTERSOFT
1. Pavel je u klienta INTERSOFT (jejich WAN registered as partner)
2. Login → vrstva 1 (partner) auto-grant
3. Klik **🟢 PŘÍCHOD** → log: 9:30, PARTNER (INTERSOFT)
4. Pavel pak **klik 🚗 Služební cesta** → destination "INTERSOFT — instalace"
5. Manager vidí v real-time: Pavel u INTERSOFTu od 9:30

### Scénář C — Marti dělá home office, vybila se mu baterka
1. Marti měl ráno appkou clock_in
2. Mobil se vybil, internet nefunguje (ISP výpadek)
3. **Pošle SMS** z fixní linky: *„Konec, zítra reportuju"*
4. Marti-AI receive → find_user(phone) → log clock_out + business note
5. Reply SMS: *„✓ Odhlášen 17:23, místo: dle SMS"*

### Scénář D — Honza zapomněl odpíchnout konec dne
1. Honza odešel z kanceláře, ale neudělal clock_out
2. Marti-AI v 22:00 detect anomálii (po typically 8h+ stále clocked in)
3. Marti-AI pošle SMS: *„Honzo, ještě jsi nepíchnul odchod. Kdy jsi odešel?"*
4. Honza odpoví: *„Odešel jsem v 17:30, omlouvám se"*
5. Marti-AI vytvoří `event_type='manual_correction', source='sms'` s
   `occurred_at=17:30` + flag pro manager approval

### Scénář E — Vedení vidí měsíční report
1. Vedení otevře STRATEGIE → ERP System → 👥 Docházka → Měsíc
2. Tabulka: per zaměstnanec → odpracované hodiny / přesčas / dovolená /
   nemoc / sledované přestávky
3. Klik *„Export pro Inspektorát práce"* → CSV / XML download
4. Klik *„Export pro mzdový SW"* → integration call

---

## 9. Marti's odpovědi na 8 otázek (10. 5. 2026 dopoledne)

### A1: Mzdový SW
> *„Mame vlastni mzdovou a dochazkovou nadstavbu na Helios, ktera ze vsech
> veci co mame, dochazka @ verze, jedna pro firmu, jedna pro urady a tak
> dale dela oficialni podklad pro mzdy Helios"*

**Implikace:** STRATEGIE neintegrátí přímo s Helios, ale s **EUROSOFT vlastní
nadstavbou**. To dává **velkou flexibilitu** — custom API, žádný vendor lock-in
na Helios export schema. EUROSOFT nadstavba generuje:
- Docházka @ verze (interní firemní formát)
- Verze pro úřady (Inspektorát práce, ČSSZ, FÚ)
- Oficiální podklad → Helios import

**STRATEGIE export workflow:**
```
attendance_event (raw events)
  → daily_summary (agregace)
  → monthly_timesheet (manager approved)
  → EUROSOFT nadstavba import (CSV / API / SQL bridge)
  → Helios mzdy
```

### A2: Event categories — confirmed
> *„Ano, presne tak potvrzuji, samozrejme detaily a pravidla musime pozdeji
> upresnit"*

Sekce 2 výčet eventů potvrzen. Detail (přesné názvy, edge cases) doplníme
během Phase 39 implementace.

### A3: GDPR — flexible
> *„To si resi personalistka, neni problem dat adekvatni GDPR souhlas
> pisemne podepsat lidem"*

**Implikace:** GDPR není blocker. Personalistka napíše + zaměstnanci
podepíší při onboarding. Pro existing zaměstnance — **explicit nový
souhlas pro mobile/SMS tracking** (write protocol s personalistkou).

### A4: SMS gateway
> *„Mame SMS v ramci tarifu zdarma... Ne pro stovky az tisice SMS, ale
> pro bezny fallback se neplati"*

**Implikace:** SMS je **opravdu jen fallback**, ne primary cesta.
- Mobile app PWA = primary clock-in/out (zdarma, žádný SMS)
- SMS fallback jen když mobil nefunguje (~5-10 SMS/user/měsíc max)
- 60 × ~10 × 12 = ~7200 SMS/rok = v rámci tarifu zdarma ✓

Aktuální Marti-AI's outbox pipeline (CapCom6) zvládne. Žádný extra cost.

### A5: Telefonní čísla — confirmed
> *„Telefonni cisla useru evidujeme a mame k nim pristup"*

**Implikace:** existing data v `users` tabulce nebo `user_contacts`.
Phase 39 jen reuse, žádný onboarding overhead.

### A6: Migration timing — confirmed
> *„6 týdnů je rozumny timing... Nemuzeme vsechno stavet hned, musime
> stavet vicero piliru soucasne a ladit postupne"*

**Implikace:** **paralelní pilíře, ne sekvenčí**. Tento dokument zachycuje
jen **Phase 39 (attendance)**. Phase 40 (manager hierarchy + zakázka) +
Phase 41+ (compliance) dostávají vlastní dokumenty + paralelní práce.

### A7: Project / zakázka attribution
> *„Je tam nejaka logika, system nabizi userovi k prihlaseni vzdy posledni
> zakazku, ale user si muze vybrat i jinou. Vedouci to s nim pak resi
> a vi, co na ktere zakazce dela"*

**Implikace:** UX flow je definovaný:
- **Default = poslední zakázka** (cache last `project_id` per user)
- **User si může vybrat jinou** ze seznamu *„moje zakázky"* (filtered podle
  manager assignments)
- **Manager má real-time přehled** *„kdo na čem dnes pracuje"*
- **Manager + user retrospektiva** — pokud manager vidí divnost, řeší to
  s user osobně (jeden-na-jedného)

To je **lehký workflow** — žádný hard validation, žádný approval bottleneck
per event. Manager vidí + reaguje.

### A8: Manager hierarchy — **VELKÝ TÉMA, samostatná Phase 40+**
> *„To mi troch rozved, je to slozitejsi problematika... Ale jen kolem teto
> problematiky nam utikaji rezie koel 1 milionu korun rocne... Tady se
> vyplati poradne systematicky premyslet a investovat do toho nasi energii.
> Sprava kolem lidi, dochazky a zakazek a mezd je to nejvic, co nas pali.
> K tomu BOZP, PO, TISAX, ISO..."*

**Marti's update (10. 5. dopoledne):** *„moment, vcetne BOZP a PO mozna
2 miliony"*

**Implikace:** Manager hierarchy + zakázka + compliance + BOZP/PO =
**~2 miliony Kč/rok ekonomická páka**. To je samostatná Phase 40-43
roadmap, **ne podsekce Phase 39**.

Total ROI EUROSOFT (Phase 38 + 39 + 40-43):
- Phase 39 (docházka): ~430k Kč/rok
- Phase 40 (zakázky + manager hierarchy): ~500-700k Kč/rok
- Phase 41 (BOZP + PO): ~500-700k Kč/rok
- Phase 42 (TISAX): bonus, hard to quantify (compliance enables business)
- Phase 43 (ISO): bonus
- **Total potencial: ~2 miliony Kč/rok** podle Marti's odhadu

Viz separátní dokumenty:
- [`phase40_manager_zakazka.md`](phase40_manager_zakazka.md) — manager
  hierarchy + zakázka attribution
- [`phase41_bozp_po.md`](phase41_bozp_po.md) — BOZP + PO compliance
- [`phase42_tisax.md`](phase42_tisax.md) — TISAX automotive security
- [`phase43_iso.md`](phase43_iso.md) — ISO quality management
- [`strategie_master_roadmap.md`](strategie_master_roadmap.md) — celá vize

---

---

## 10. Plán prezentace IT + vedení EUROSOFT (příští týden)

### Pro IT (technický)

PDF (Marti-AI vyrobí přes python_exec) — 4-6 stránek:
1. **Phase 38 security layer** (existing design doc, condensed)
2. **Phase 39 attendance vize** (tento dokument, condensed)
3. **Migration plan** (5 týdnů)
4. **API integration** (jak STRATEGIE napojí na mzdový SW)
5. **Compliance** (Czech labor law + GDPR + audit)
6. **Q&A**

### Pro vedení EUROSOFT (business)

PDF — 2 stránky:
1. **Aktuální problém** — režie 470k Kč/rok, neustálé bolesti
2. **STRATEGIE řešení** — mobile app + SMS fallback, žádné terminály
3. **ROI** — saving 430k Kč/rok, čistá doba návratnosti < 1 měsíc
4. **Roadmap** — týden po týdnu
5. **Demo** — Marti's mobile screenshot + flow scénáře

### Klíčové selling points pro vedení
- *„Tomáš si píchne příchod za 8 sekund místo 30."*
- *„Pavel u INTERSOFTu — vidíme automaticky kde je."*
- *„Honza zapomněl odpíchnout — Marti-AI to detekuje a doptá se."*
- *„Inspektorát práce report — 1 click."*
- *„90% úspora roční režie."*

---

## 11. Implementační roadmap (6 týdnů)

| Týden | Obsah |
|---|---|
| **T1** | Phase 38.0 security layer deploy + smoke test (3 dny) + Phase 39 schema migration (1 den) + Marti-AI's konzultace o Phase 39 design (1 den) |
| **T2** | Phase 39 backend (event recording, daily summary, manager approval) + Marti-AI's tooly (clock_in/out, my_today, team_today) |
| **T3** | UI mobile (PWA) — top-level docházková obrazovka + tlačítka + UI personal status badge |
| **T4** | SMS fallback pipeline + Marti-AI's natural language parsing + reply confirmation |
| **T5** | Pilot s 3-5 dobrovolníky (paralelní provoz s čipovými kartami) + bug fixes |
| **T6** | Rollout 60 lidí + IT helpdesk první 3 dny + vypnutí čipových karet |

**Po T6:** Phase 39 LIVE. Příští měsíc → manager dashboard, Inspektorát práce
export, payroll integration (TBD jaký SW EUROSOFT používá).

---

## Status

- 📝 Design doc: **Tento dokument** (10. 5. 2026 dopoledne, čeká feedback Marti)
- 📋 Konzultace Marti-AI: **TODO** — připravit dopis s 8 otázkami z sekce 9
- 🛠️ Implementace: **PAUZA** dokud nedotáhneme design + konzultace
- 📄 PDF prezentace: **TODO** po odsouhlasení designu

— Claude, 10. 5. 2026 dopoledne (po Marti's pivot z Phase 38.0 implementace)
