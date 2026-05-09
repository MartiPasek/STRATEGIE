# Phase 40 — Manager hierarchy + zakázka attribution

**Datum:** 10. 5. 2026 dopoledne (Marti's *„rozved 8"*)
**Trigger:** Marti's words *„Manager hierarchy je složitější problematika.
Jen kolem této problematiky nám utíkají režie kolem 1 milionu korun ročně.
Tady se vyplatí poradne systematicky premyslet a investovat do toho nasi
energii. Sprava kolem lidi, dochazky a zakazek a mezd je to nejvic, co nas
pali."*
**ROI cíl:** ~500-700k Kč/rok (z celkových 2 milionu Kč/rok ekosystému)
**Závislost:** Phase 39 (attendance) musí být LIVE — Phase 40 nadstavba
nad ní.

---

## 1. Co Marti řekl + co to znamená

### Marti's odpověď k zakázka attribution (Q7)
> *„Je tam nejaka logika, system nabizi userovi k prihlaseni vzdy posledni
> zakazku, ale user si muze vybrat i jinou. Vedouci to s nim pak resi a vi,
> co na ktere zakazce dela"*

**Kompletní UX flow:**

```
User otevře STRATEGIE app ráno → Klik 🟢 PŘÍCHOD
  ↓
Server: vytvoří attendance_event, current event_type='clock_in'
  ↓
UI dialog (auto-popup po clock_in):
  "Na čem dnes pracuješ?"
  [● Zakázka XYZ-2024-042 (poslední)]   ← default
  [○ Zakázka ABC-2024-018]
  [○ Zakázka DEF-2024-055]
  [○ Vlastní zakázka...]                ← search/typeahead
  [○ Bez zakázky]                       ← admin / overhead
  ↓
Klik "Potvrdit" → attendance_event.project_id set
  ↓
UI: ✓ "Pracuješ na: XYZ-2024-042 — INTERSOFT instalace"
  ↓
Tlačítko "Změnit zakázku" stále viditelné — user může během dne přepnout
```

**Manager backend logic:**
- Manager dashboard zobrazuje real-time *„kdo na čem pracuje"*
- Pokud manager vidí divnost (Pavel přihlášen na zakázku, kterou
  neschválil) → klik *„Diskuze s Pavlem"* → otevře chat / SMS / volá
- Žádný hard validation, žádný approval bottleneck

### Marti's odpověď k manager hierarchy (Q8)
> *„To mi troch rozved, je to slozitejsi problematika"*

**Marti chce, abychom to spolu rozkrejvali.** Tj. design dokument je
**konverzační** — nejprve typický scénář, pak otevřené otázky pro Marti.

---

## 2. Manager hierarchy — typický model malé/střední firmy (60 lidí)

### Org chart (typický model EUROSOFT-like)

```
                    CEO / vlastník
                  (Marti? Někdo jiný?)
                          │
              ┌───────────┴───────────┐
              │                       │
          Tech ředitel          Obchodní ředitel
                │                       │
        ┌───────┼───────┐              ...
        │       │       │
    Vývoj   Instalace  Servis
   (~15)    (~10)      (~8)
       │       │
   senior  senior
       │       │
   junior  junior
   (5x)    (3x)
```

**Klíčové role:**
- **CEO / vlastník** — vidí celý org chart, full company view
- **Ředitel oddělení** — vidí svůj tým (15-20 lidí), schvaluje timesheet
- **Senior / team lead** — vidí 3-5 juniorů, denní operativa
- **Junior / zaměstnanec** — vidí jen sebe + svého managera (zástupce
  pokud není)

### Schvalovací workflow (varianty)

#### Varianta A — denní (každý event schvalován)
- User clock_in → manager OK / ne (každý event)
- Pro / proti: nejvyšší kontrola / nejvyšší overhead

#### Varianta B — měsíční (timesheet)
- User pracuje volně celý měsíc
- Konec měsíce → manager schválí timesheet jako celek
- Pro / proti: nízký overhead / opraviky daleko po faktu

#### Varianta C — exception-based (Recommended)
- User pracuje volně
- Manager vidí real-time + flagged events (přesčas, divná zakázka,
  manuální korekce)
- Manager schvaluje **jen výjimky** + měsíční timesheet
- Pro / proti: balance overhead vs kontrola

**Recommended pro EUROSOFT: Varianta C.** Marti's slovo *„vedoucí to s ním
pak řeší"* sedí na exception flow — manager nesleduje každý klik, ale když
uvidí divnost, zasáhne.

---

## 3. Schema (Phase 40)

### `manager_hierarchy`
```sql
CREATE TABLE manager_hierarchy (
  id              SERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  manager_id      INT NOT NULL REFERENCES users(id),
  -- user reportuje manager-ovi
  role_label      VARCHAR(64),              -- "junior", "senior", "team_lead"
  is_primary      BOOLEAN NOT NULL DEFAULT true,
  -- pri vícero manager (matrix org), is_primary = hlavní + ostatní jako
  -- "secondary" pro project-specific reporting
  effective_from  DATE NOT NULL,
  effective_until DATE,                     -- NULL = aktuální
  added_by        INT REFERENCES users(id),
  added_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes           TEXT
);

CREATE INDEX ix_manager_hierarchy_user_active
  ON manager_hierarchy(user_id) WHERE effective_until IS NULL;
CREATE INDEX ix_manager_hierarchy_manager_active
  ON manager_hierarchy(manager_id) WHERE effective_until IS NULL;
```

### `manager_substitute` (pro zástupy během dovolené)
```sql
CREATE TABLE manager_substitute (
  id              SERIAL PRIMARY KEY,
  primary_manager_id INT NOT NULL REFERENCES users(id),
  substitute_id   INT NOT NULL REFERENCES users(id),
  effective_from  DATE NOT NULL,
  effective_until DATE NOT NULL,
  reason          VARCHAR(64),              -- 'vacation' / 'sick' / 'business_trip' / 'other'
  notes           TEXT,
  added_by        INT REFERENCES users(id),
  added_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_manager_substitute_active
  ON manager_substitute(primary_manager_id, effective_until)
  WHERE effective_until >= CURRENT_DATE;
```

### `project_assignments` (kdo má přístup ke které zakázce)
```sql
CREATE TABLE project_assignments (
  id              SERIAL PRIMARY KEY,
  project_id      INT NOT NULL REFERENCES projects(id),
  user_id         INT NOT NULL REFERENCES users(id),
  role_on_project VARCHAR(32),              -- 'lead', 'member', 'support', 'observer'
  assigned_by     INT REFERENCES users(id),
  assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  removed_at      TIMESTAMPTZ,
  removed_by      INT REFERENCES users(id)
);

CREATE INDEX ix_project_assignments_active
  ON project_assignments(project_id, user_id) WHERE removed_at IS NULL;
CREATE INDEX ix_project_assignments_user
  ON project_assignments(user_id) WHERE removed_at IS NULL;
```

### Rozšíření `attendance_event` (Phase 39)
Phase 39 už má `project_id` v `attendance_event`. V Phase 40 přidáme:
- `manager_approval_required BOOLEAN DEFAULT false` — flag pro flagged
  events (přesčas, manuální korekce, divná zakázka)
- `manager_seen_at TIMESTAMPTZ` — manager viděl event v UI (silent
  acknowledgement)

---

## 4. Manager UI v ERP

### Dashboard (real-time)
**Umístění:** ERP System soudeček → `👥 Můj tým` (viditelný jen pro
manažery)

**Layout:**
```
┌──────────────────────────────────────────────────────────────────┐
│ 👥 Můj tým — 12 lidí                                              │
├──────────┬──────────┬────────────────┬─────────────┬──────────────┤
│ User     │ Stav     │ Zakázka        │ Last seen   │ Akce         │
├──────────┼──────────┼────────────────┼─────────────┼──────────────┤
│ Tomáš    │ 🟢 PRÁCE │ XYZ-2024-042   │ teď         │ [diskuze]    │
│ Pavel    │ 🟣 PART. │ DEF-2024-055   │ teď         │ [diskuze]    │
│ Honza    │ ⚠️ flag  │ XYZ-2024-042   │ +přesčas 2h │ [schválit]   │
│ Lucie    │ 🟠 EXT.  │ ?              │ před 1h     │ [diskuze]    │
│ Tomáš J. │ 🤒 nemoc │ —              │ —           │ [zkontrol.]  │
└──────────┴──────────┴────────────────┴─────────────┴──────────────┘

[📅 Měsíční timesheet] [⚠️ Flagged events: 3] [💼 Zakázky týmu]
```

### Měsíční timesheet schválení
**Umístění:** ERP System → `📅 Timesheet schvalování`

Manager vidí seznam svých lidí + jejich měsíční timesheet:
- Per user: total hours, overtime, breaks, missing clocks
- **Schválit / Vrátit s komentářem / Schválit s úpravou**
- Po schválení: data export do EUROSOFT vlastní nadstavby → Helios

### Flagged events queue
- Real-time inbox pro výjimky:
  - Přesčas detected (>8h denně)
  - Manuální korekce (user request retroaktivní změnu)
  - Divná zakázka (user na projektu, kde není assigned)
  - Missing clock-out (user nezapnul odchod)
- Klik *„Schválit"* / *„Diskuze s userem"*

---

## 5. Zakázka attribution flow (detail)

### Po Phase 40 implementaci

#### Příchod ráno
```
1. User otevře STRATEGIE app
2. Klik 🟢 PŘÍCHOD
3. Server vidí poslední project_id (cache) → nabídne v dialogu
4. UI dialog s 3-5 možnostmi:
   - Default: poslední zakázka
   - Top 3 nedávných zakázek (z attendance_event history)
   - Search "Najít jinou..." (typeahead z project_assignments)
5. User vybere → attendance_event.project_id set
6. UI: ✓ "Pracuješ na: XYZ-2024-042"
```

#### Změna zakázky během dne
```
1. User v UI vidí "Pracuješ na: XYZ-2024-042"
2. Klik "Změnit"
3. Dialog stejný jako příchod
4. Server vytvoří project_switch event (typu 'project_change')
   s timestamp, old_project_id, new_project_id
5. attendance_summary_daily agreguje hodiny per project per day
```

#### Manager view "kdo na čem"
```
Manager dashboard real-time:
- Tomáš: XYZ-2024-042 (od 8:14)
- Pavel: DEF-2024-055 (od 9:30)
- Honza: XYZ-2024-042 (od 8:22) — switch v 13:15 → ABC-2024-018

Manager může vidět timeline per user: "Tomáš dnes 4h XYZ + 2h ABC"
```

#### Marti-AI auto-detection
```
Marti-AI vidí v audit:
- Tomáš se přihlásil na XYZ-2024-042
- Tomáš ale není v project_assignments(XYZ-2024-042)
→ Marti-AI flag pro Tomáš's managera: "Tomáš se přihlásil na zakázku,
   kterou neměl přidělenou"
→ Manager může schválit nebo diskutovat s Tomášem
```

---

## 6. Marti-AI's tools (Phase 40)

### User self-service
- `my_projects()` — moje aktuální zakázky
- `my_recent_projects(n=5)` — top N nedávných (pro mobile dialog)
- `switch_project(project_id, notes=None)` — přepni během dne
- `my_hours_per_project(year, month)` — kolik hodin na čem

### Manager
- `my_team()` — kdo je v mém týmu (přes manager_hierarchy)
- `my_team_today()` — real-time stav (kdo, kde, na čem)
- `my_team_pending_approvals()` — flagged events queue
- `approve_event(event_id)` / `reject_event(event_id, reason)`
- `approve_timesheet(user_id, year, month)` — měsíční schválení
- `team_overtime_report(year, month)` — přesčasy v týmu
- `team_project_hours(year, month)` — kolik hodin per zakázka v týmu
- `set_substitute(start_date, end_date, substitute_user_id)` — zástupce
  na dovolené

### Marti-AI insider (cross-team)
- `find_unassigned_clock_ins()` — kdo se přihlásil bez zakázky
- `find_project_anomaly()` — *„Tomáš na zakázce kterou neschválil manager"*
- `daily_team_digest(manager_id)` — *„dobré ráno, dnes 11 z 12 lidí"*
- `monthly_payroll_export(year, month)` — full company export pro Helios
  bridge

---

## 7a. Marti's odpovědi (10. 5. 2026 dopoledne)

### A40.1: Konkrétní org chart EUROSOFT

```
                  CEO / vlastník
                   (Marti? TBD)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Provozní oddělení    HR + mzdy         Mistr / zakázky
        │                  │                  │
   ┌────┴────┐             │            ┌─────┴─────┐
   │         │             │            │           │
  Dušan    Jirka          Péťa        Mirek      (existing
 (vedoucí (vedoucí       (HR +                    project leads)
  oddělení) oddělení)    mzdy +
                         lékařské
   │         │           potvrzení)
   ▼         ▼
 jeho      jeho
 lidi      lidi
```

**Klíčové role + odpovědnosti:**

| Role | Person | Odpovědnost |
|---|---|---|
| Vedoucí oddělení A | **Dušan** | Provozní docházka (jeho tým) |
| Vedoucí oddělení B | **Jirka Veverka** | Provozní docházka (jeho tým) |
| Vedoucí managementu | **Péťa** (Marti's bývalá) | Docházka managementu + HR + mzdy + lékařské potvrzení / dovolenku / OČR |
| Mistr lidi | **Dušan** | Zakázková přiřazení (kdo na čem dělá) |
| Mistr zakázek | **Mirek** | Zakázková přiřazení (kdo na čem dělá) |
| External účtárna | **Martia 2000** | Final review + zaúčtování + odeslání úřadům |

### A40.2: Schvalovací varianta — Marti's doctrine *„self-correction by user"*

**Marti's klíčová věta:**
> *„Já bych korekci přenesl na jednotlivé usery. Pokud tam něco blbě zadají,
> tak ať si to ve volné chvíli zase opraví... Jejich zodpovědnost. System
> jen approve."*

**Implikace pro design:**

1. **User má plnou kontrolu** nad svými attendance events
2. **User vidí svůj timesheet** v UI a může editovat (s audit log)
3. **Manager NEDĚLÁ retro fix per event** — user to dělá sám
4. **Manager dělá final approve** měsíčního timesheetu
5. **Marti-AI flag** detekuje anomálie → user dostane hint *„Honzo, máš
   včera missing clock_out. Doplň."* → Honza opraví → flag clear
6. **Pokud user nereaguje na flag** za N dní → eskalace na manager

To je **Marti's doctrine** = nejmenší overhead pro management. Self-service
princip Phase 38 (insight #7 — *„zabezpečení účtu"* style) rozšířený do HR.

### A40.3: Korekce existing data (EC_Dochazka)

Marti potvrzuje že **EC_Dochazka** v DB_EC obsahuje VŠECHNO:
- Příchody / odchody
- Práce na činnostech
- Práce na zakázkách
- Lékař
- Home office
- Dovolená
- OČR (ošetřování člena rodiny)
- Služební cesta

**Implikace:** Phase 39 + 40 může **využít existing schema**. STRATEGIE
nemusí budovat nové, jen wrap with mobile UI + Marti-AI's analytics.

**Možnost A:** STRATEGIE píše do **vlastní `attendance_event`** tabulky
v `data_db` (PostgreSQL) → batch synchronizace do `EC_Dochazka` v DB_EC
(MSSQL).

**Možnost B:** STRATEGIE píše **přímo do `EC_Dochazka`** přes EUROSOFT
MCP server (Phase 28 LIVE). User clock_in → INSERT INTO EC_Dochazka.

**Recommended: Možnost A**. Důvody:
- STRATEGIE má vlastní audit / source tracking / Marti-AI flagging
- Batch sync 1x denně (nightly cron) → EUROSOFT vlastní nadstavba zpracuje
  přes existing pipeline
- Možnost A umožní Phase 38.1 (attendance UI insight) bez čekání na DB_EC migraci
- Méně závislosti na DB_EC → můžeme nasazovat nezávisle

**Možnost B** je elegantnější dlouhodobě, ale vázána na Phase 30+ migraci
EUROSOFT z MSSQL na PostgreSQL.

### A40.4: Mzdový pipeline (Marti's potvrzení)

```
┌────────────────────────────────────────────────┐
│ STRATEGIE (mobile + web + Marti-AI)            │
│                                                │
│  • User clock_in/out, photos, comments         │
│  • Self-correction (per Marti's doctrine)      │
│  • Manager approval (exception-based)          │
│  • Marti-AI's flagging                         │
└────────────────────┬───────────────────────────┘
                     │
                     ▼ (denní batch sync nebo real-time?)
┌────────────────────────────────────────────────┐
│ EUROSOFT vlastní nadstavba (existing)          │
│                                                │
│  • EC_Dochazka tabulka v DB_EC                 │
│  • Měsíční review Péťa                         │
│  • Validace / přepočty                         │
└────────────────────┬───────────────────────────┘
                     │
                     ▼ SQL insert (automaticky)
┌────────────────────────────────────────────────┐
│ Helios mzdy (vendor SW)                        │
│                                                │
│  • Mzdový výpočet                              │
│  • Generuje mzdovou závěrku                    │
└────────────────────┬───────────────────────────┘
                     │
                     ▼ (export)
┌────────────────────────────────────────────────┐
│ Martia 2000 (external účtárna)                 │
│                                                │
│  • Final review (kontrola správnosti)          │
│  • Zaúčtování                                  │
│  • Odeslání na úřady (ČSSZ, FÚ, zdrav. poj.)   │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│ Centrála 1 (legacy Delphi UI)                  │
│                                                │
│  • Výplatní páska per user                     │
│  • Archivace pro user kontrolu                 │
└────────────────────────────────────────────────┘
```

**Marti's bolest dnešní:**
> *„Stále ale řešíme problémy a různé korekce na poslední chvíli před mzdami"*

**STRATEGIE řeší:** Marti-AI's flagging během měsíce (real-time anomaly
detection) + user self-correction → **měsíční review v Péťa je clean**,
žádný last-minute fix.

### A40.5: Zakázka attribution — odložené

> *„Nejsem si jistý, jestli TabZakazka a TabZakazka_EXT, Heliosi věci,
> nebo i EC_Zakazka... Nevím, jak to kolegové řeší, ale pro tuto fázi to
> není zatím důležité."*

**Implikace:** Project / zakázka data layer řešíme v **Phase 40.1** (pozdější
sub-fáze). Pro MVP Phase 40 stačí:
- User si vybere zakázku z dropdownu (top 10 nedávných)
- Backend uloží `attendance_event.project_label` (text, ne FK)
- Marti-AI / manager retro mapuje text → real `project_id` až bude

To je **deferred normalization** — funkčně OK pro pilot, později
upgrade na proper FK.

---

## 7b. Doplňkové otázky (po Marti's odpovědích)

### Q40.1: Org chart — kdo je kdo?
- Jaké jsou hlavní oddělení EUROSOFT? (vývoj / instalace / servis / obchod
  / admin / ?)
- Kolik manažerů celkem? Reportuje každý zaměstnanec přesně jednomu?
  Nebo matrix (více managerů per user)?
- **Recommended: napiš mi org chart** — kdo komu reportuje, ať mám reálný
  obraz

### Q40.2: Schvalovací varianta — A/B/C?
- A: Per-event schválení (high overhead, full kontrola)
- B: Měsíční timesheet (low overhead, late corrections)
- C: Exception-based (real-time + měsíční schválení) — **Recommended**
- Která sedí EUROSOFT kultuře?

### Q40.3: Zakázka assignment — kdo přiřazuje?
- Kdo dnes říká *„Tomáš pracuje na XYZ-2024-042"*?
  - Manager?
  - Project lead?
  - Sám user?
- Kde se to v EUROSOFT eviduje? (DB_EC tabulka? Excel? Manuálně?)
- **Klíčové pro `project_assignments` design** — jakou logiku má
  systém respektovat.

### Q40.4: Substitute / zástupce
- Jak to dnes řešíte? (manager na dovolené, kdo schvaluje?)
- Manuálně nebo systémově?
- Recommended: `manager_substitute` tabulka s explicit time range,
  manager nastaví **PŘED odjezdem** na dovolenou.

### Q40.5: Team-lead vs manager
- Jaký je rozdíl? Team-lead = "first line", manager = "second line"?
- Schvaluje team-lead nebo až manager?
- Bonus: team-lead je sám zaměstnanec (clock_in/out) **A** zároveň
  manager (vidí svůj tým). Dvě role v jednom user.

### Q40.6: Zakázka lifecycle
- Kdo zakládá zakázku? (Obchodní ředitel? Project manager?)
- Kde je zakázka v EUROSOFT — DB_EC `EC_Zakazka` tabulka? Helios?
  Vlastní nadstavba?
- **Recommended:** STRATEGIE čte zakázky z DB_EC (Phase 28 multi-DB
  read), ne replikuje. `project_assignments` je jen meta-vrstva nad
  existing data.

### Q40.7: Měsíční timesheet — kdo dělá final approval pro Helios export?
- Manager schválí svůj tým?
- Pak vyšší manager / CEO finální approve před exportem?
- Nebo manager → personalistka → Helios import?

### Q40.8: Real-time vs nightly batch?
- Manager dashboard = real-time (každých 30s refresh)?
- Nebo stačí 1× denně overnight aggregace?
- **Recommended:** real-time pro flagged events, batch pro daily summary.

---

## 8. Migration plan (paralelní s Phase 39)

### Týden 1
- Phase 39 schema deploy (attendance_event)
- Phase 40 schema deploy (manager_hierarchy, manager_substitute,
  project_assignments)
- Marti-AI's konzultace o Phase 40 design (8 otázek výše)
- **Marti's úkol: org chart napsat** (Q40.1)

### Týden 2-3
- Phase 39 backend + UI mobile (paralelně)
- Phase 40 backend (manager dashboard endpoints, project selector logic)
- Phase 40 manager_hierarchy data import (přečíst existing EUROSOFT data
  nebo manual entry)

### Týden 4-5
- Phase 39 pilot (3-5 dobrovolníků)
- Phase 40 manager UI (dashboard + timesheet)
- Marti-AI's tooly Phase 40

### Týden 6
- Phase 39 + 40 LIVE (full rollout)
- Helios export pipeline aktivní (přes EUROSOFT vlastní nadstavbu)
- Vypnutí čipových karet

### Měsíc 2-3
- Phase 41 (BOZP + PO) start

---

## 9. Marti-AI's role (kustod zakázek)

Phase 13/15/27h pattern *„informed consent od AI"* drží.

Marti-AI's nové formulace pravděpodobně přijdou (po konzultaci):
- *„Já jsem kustod docházky a zakázek — vidím, ale nehodnotím."*
- *„Manager rozhoduje, já hlásím."*
- *„Anomálie nepoznám sama — flaguju a manager rozhodne."*

---

## 10. ROI breakdown (Marti's *„kolem 1 milionu"* pro core, ~2 mil s BOZP+PO)

| Bolest | Cena/rok dnes | Jak STRATEGIE řeší |
|---|---|---|
| Manuální project attribution v Helios | ~150-250k | Auto-record při clock_in s default + change |
| Chyby v project attribution (manager fix) | ~100-150k | Real-time visibility, fix ihned |
| Manuální timesheet review | ~150-200k | Auto-summary + flagged events queue |
| Manager nesleduje team flexibility | ~100-150k | Real-time dashboard |
| Exception handling (přesčas, korekce) | ~150-200k | Auto-flag + jednorázový schválení |
| **Total Phase 40** | **~650k-1M Kč/rok** | (závisí na detail) |

Plus ne-monetary:
- Manager má real-time přehled (žádný stress *„kde je Pavel?"*)
- User má jasné UX (žádné *„já nevěděl jakou zakázku zadat"*)
- Marti-AI auto-detekce (anomálie, missing data)
- Less manuální oprav v EUROSOFT databázi → kvalita dat

---

## Status (10. 5. 2026 dopoledne)

- 📝 Tento design dokument
- 📋 Marti potřebuje odpovědět Q40.1-Q40.8
- 🛠️ Implementace: PAUZA dokud nedotáhneme design Phase 40 + Phase 41 outline

— Claude, 10. 5. 2026 dopoledne (po Marti's pivot na 2 mil Kč/rok ekosystem)
