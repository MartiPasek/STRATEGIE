# Nábor & personální pohovory — integrace + migrace do STRATEGIE (v2)

Marti 13. 6. 2026: *„Léčba šokem Šárky — prozkoumej systém v EC pro personální
pohovory a nabídni řešení k integraci a migraci přímo do STRATEGIE."*
Navazuje na ranní HR navigaci (větev **Externí personalistika — nábor**:
Inzeráty · Kandidáti · Pohovory · Pracovní nabídky).

## Co je v Centrále (DB_EC, ověřeno přes bridge 13.6.)

### Kde data REÁLNĚ jsou — `ec_jednani` s `Kategorie = 901`
Klíč dal Marti (přehled č. 12510). Náborové pohovory **nejsou** v modulu
`TabPers*` (ten je navržený, ale **prázdný** — TabPersUchazec 168 sl./0 řádků,
TabPersVyberRizeni 47 sl./0 řádků). Žijí v univerzální tabulce jednání
`ec_jednani` filtrované na **Kategorie = 901**. **1867 záznamů.**

**Pole kandidáta/pohovoru na `ec_jednani` (Kat 901):**
- identita: `Predmet`, `email`, `telefon`, `Alias`, `CisloKontOsoba`, `CisloOrg`
- recruiter/vlastník: `CisloZam` → `TabCisZam.PrijmeniJmeno`; `Autor`, `DatPorizeni`
- pipeline: **`Faze`** (text), **`Stav`**, `Typ` → `TabTypKontJed.Popis`
- termíny: `TerminPohovoru`, `TerminTestovacichDni`, `TerminNastupu`,
  `DatumJednaniOd/Do`
- profil: `Vzdelani`, `ProgramovaciJazyky`, `CiziJazyky` (+ Anglictina/Nemcina/
  DalsiJazyk), `PosledniZamestnani`, `DuvodOdchodu`, `Vyhlaska50`, `OchotaCestovat`
- nabídka/odmítnutí: `Sazba` = **PožadovanýPlat**, `Zdroj`, `DuvodZamitnuti`

**Pipeline (živé hodnoty `Faze`):** Ve hře (10) → 1. kolo (340) → 2. kolo (55)
→ nástup (139) → mimo hru (592) · prázdné (731). **Stav:** O otevřené (75),
U uzavřené (766), prázdné (1026).

### Číselníky (mají data — migrují se 1:1)
- `EC_Personalistika_FazePrijimacihoRizeni` — 6 fází (ID, Cislo, Faze)
- `EC_Personalistika_DuvodZamitnuti` — 15 důvodů zamítnutí (ID, Typ, Popis)
- `TabPersUchazecZdrojCis` — zdroje uchazečů (ID, Nazev)
- `EC_PersonalistikaSkoly` — 41 škol

### Pozor — DVA různé světy „pohovorů" (nepleť):
1. **Náborové pohovory** (externí) = `ec_jednani` Kat 901 (1867) — uchazeči zvenčí.
   → patří do větve **Nábor**.
2. **Hodnotící / výroční pohovory** (interní, se stávajícími zaměstnanci):
   - `EC_Personalistika_VyrocniPohovory` — 41 (CisloZam, DatPohovoru, Popis ntext)
   - `EC_HodnoceniVP_Uzavrene` — **606** uzavřených ročních hodnocení (38 sl.,
     výkonové metriky: PocetFaktur, FakturyCastkaCelkem, VyfakturovaneHodiny,
     odměny za EUR/hod/karty…). „VP" = výroční pohovor.
   → patří do větve **Interní personalistika → Jednotlivci** (hodnocení/rozvoj),
     řešíme jako druhý krok.

## Návrh — STRATEGIE model (`tenant.*`, prodejný standard)

Žádný „vše v jednom" bastl ani prázdný over-design. Čistá kostra zrcadlící
větev Nábor:

| Tabulka | Obsah |
|---|---|
| `tenant.recruit_posting` | inzerát / výběrové řízení: pozice, název, text inzerce, zdroj zveřejnění, stav (koncept/otevřeno/zavřeno), datum zahájení/zveřejnění/platnosti, recruiter (user_id), company_id |
| `tenant.recruit_candidate` | uchazeč: jméno, email, telefon, vzdělání, jazyky (prog./cizí), poslední zaměstnání, důvod odchodu, vyhláška 50, ochota cestovat, požadovaný plat, zdroj (FK číselník), poznámka |
| `tenant.recruit_application` | přihláška = kandidát × posting: **fáze** (FK), **stav**, termín pohovoru, termín test. dní, termín nástupu, hodnocení, důvod zamítnutí (FK), poznámka; **verzovatelné dotyky** (changed_by/at) |
| `tenant.recruit_interview` | jednotlivý pohovor v rámci přihlášky: kolo, datum/čas, účastníci (panel = user_id[]), hodnocení, závěr — *(volitelně; MVP může fázi+termín držet na application)* |
| `tenant.recruit_phase` | číselník fází: Ve hře / 1. kolo / 2. kolo / nástup / mimo hru (priority_order, is_terminal, is_hired) |
| `tenant.recruit_reject_reason` | číselník důvodů zamítnutí (15 z EC) |
| `tenant.recruit_source` | číselník zdrojů uchazečů |

**Mapování na větev Nábor (appka):** Inzeráty = `recruit_posting` · Kandidáti =
`recruit_candidate` · Pohovory = `recruit_application`/`recruit_interview`
(fáze+termíny) · Pracovní nabídky = application ve fázi „nástup" + nabídkový
dokument (reuse generátor šablon, Phase šablony).

**Most externí → interní (ranní doktrína):** přihláška ve fázi **nástup** +
přijatá nabídka → **onboarding**: kandidát „přeteče" do interní personalistiky
(`hr_person` + `engagement` + onboarding flow, který už máme). Jedno tlačítko
„Přijmout → založit zaměstnance".

## Migrace (přes bridge, vzor sync_org/sync_fin)

1. **Číselníky první** (banner): recruit_phase (6 + priority_order + is_hired
   pro „nástup", is_terminal pro „mimo hru"), recruit_reject_reason (15),
   recruit_source (z `TabPersUchazecZdrojCis`).
2. **1867 záznamů** `ec_jednani` Kat 901 → rozpad na candidate + application:
   - candidate: email/telefon/Predmet (jméno) + profilová pole; dedup přes
     email (jeden člověk může mít víc přihlášek).
   - application: Faze→phase, Stav, termíny, Sazba→pozadovany_plat,
     DuvodZamitnuti→reason, Predmet→pozice/poznámka.
   - audit: `Autor`/`DatPorizeni` → `changed_by_text`/`changed_at`.
   - recruiter: `CisloZam` → user_id přes `att_employee`/`hr_person.source_id`.
3. EC `ec_jednani` zůstane jako read-only legacy; STRATEGIE = nový primární zdroj.
4. **Ověření po zápisu** (čtení), report nesrovnalostí (chybějící e-maily apod.).

## Bezpečnost / ACL
- Kandidátská data = PII (e-mail, telefon, plat. očekávání) → soudeček
  **Nábor** parent_only + **HR skupina** (resolve_role / staff_group HR).
- **Konzultace Marti-AI POVINNÁ** (doctrine #3): jak moc náborová data zná
  (struktura vždy; konkrétní uchazeč jen v náborovém kontextu — analogie
  s payroll hranicí 7.6.).

## Postup (pro pondělní „šok" Šárce)
1. ✅ Průzkum EC (13.6.) — data v `ec_jednani` Kat 901 (1867).
2. Konzultace Marti-AI (model + ACL náboru).
3. DDL `recruit_*` + číselníky (banner).
4. Migrace 1867 → candidate+application (banner, ⚙ ops vzor) + ověření.
5. Větev Nábor v appce: ze skeletonu → živé seznamy (Inzeráty/Kandidáti/
   Pohovory/Nabídky) nad migrovanými daty.
6. Šárka vidí v telefonu svůj náborový pipeline z Centrály — živě, čistě, v kapse.

## Konzultace Marti-AI (13. 6. 2026) — závěry, ZÁVAZNÉ (podklad pro Šárku jako HR garant)

1. **Q1 — hranice k datům uchazečů (3 vrstvy, její volba):**
   - **Struktura vždy** — pipeline, fáze, počty, konverzní poměry, zdroje (bez PII).
   - **Profil v kontextu** — jméno/kontakt/plat/důvod odchodu jen když na člověku
     aktivně pracuje s HR/recruiterem v daném výběrku (jako tichá asistentka).
   - **Hodnocení z pohovoru NIKDY do paměti** (record_thought) — nejcitlivější
     vrstva (co recruiter napsal o člověku, který nenastoupil). → migrace
     hodnocení vůbec netahá; appka ho drží jen v náborovém kontextu.
2. **Q2 — ACL:** rodiče + HR skupina vidí vše; **recruiter jen svá výběrová
   řízení** (konkurenční kandidáti = citlivé). Dědí na zástupce. Agregátní
   dashboard (počty/fáze, bez PII) OK pro všechny recruitery.
3. **Q3 — dedup:** jeden `recruit_candidate`, více `recruit_application`
   (dedup přes e-mail). GDPR lhůta **1 rok** od posl. uzavřeného výběrku.
4. **Q4 — GDPR > audit (vědomě, jinak než zaměstnanci):** po lhůtě
   **anonymizace, ne smazání** — řádek kandidáta zůstane (`anonymized_at`),
   ale jméno→`[anonymizováno]`, e-mail/telefon/plat→NULL; `recruit_application`
   zůstává jako statistický záznam (fáze/zdroj/důvod zamítnutí). Technicky:
   `anonymized_at` + cron / ruční spuštění HR skupinou.
5. **Q5 — onboarding most:** přenést kontakt + profil (jméno/vzdělání/jazyky) +
   zdroj; **NEpřenášet** požadovaný plat, hodnocení z pohovoru, důvody zamítnutí.
   Vazba `recruit_application.engagement_id` zachovat jako read-only „odkud přišel"
   (HR/rodiče analytika efektivity zdrojů).

DDL doplněno dle závěrů: `recruit_candidate.{gdpr_consent_at, last_closed_at,
anonymized_at}`, `recruit_application.engagement_id`. Migrace (sync_nabor)
netahá hodnocení.

— Claude (id=23), 13. 6. 2026
