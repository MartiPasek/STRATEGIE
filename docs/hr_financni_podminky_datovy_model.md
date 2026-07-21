# Finanční podmínky — jak to bude uložené (jednoduše)

> Pro Šárku, 9. 7. 2026. Návrh, **jak držet finanční podmínky lidí ve STRATEGII**.
> Psáno lidsky. Technická příloha pro Marti / Marti-AI je až na konci.
> Bez konkrétních jmen a čísel — téma je citlivé.

## ⚠ Nejdřív klid: nic se nepřepsalo

Tohle je **jen návrh na papíře**. Do databáze jsem **nic nezapsal ani nepřepsal** — jen jsem se
podíval, jak to dnes vypadá (čtení). A celý návrh je **jen přidávání** (nová políčka, nové seznamy) —
**nic stávajícího se nemaže ani nemění**. Než se cokoli udělá naostro, projdeme to spolu a schvaluje
se to přes banner. Dvojí kontrola je součástí — viz úplný konec.

---

## Jak si to představit

Každý člověk má **jednu „kartu podmínek"**. Ta se skládá z šesti přihrádek — přesně jako v Centrále:

1. **Kdo a jaká smlouva** — pracovník, firma (EC/ES), druh (HPP / OSVČ / DPP…), od–do, zkušebka.
2. **Kolik hodin** — úvazek, hodiny za měsíc, u výroby min/max hodin.
3. **Peníze** — jednotlivé složky odměny (základ, osobní ohodnocení, prémie, montáž…).
4. **Volno** — dovolená a sick days (standardní + navíc).
5. **Poznámky** — proč se co domluvilo (citlivé, uzamčené).
6. **Požadovaný plat v čase** — jak se domluvená mzda vyvíjí.

Když někdo dostane novou domluvu, **stará verze se nepřemaže — uloží se jako historie** (kdo a kdy to
změnil). Díky tomu vždycky víme, jak podmínky vypadaly k jakémukoli datu (důležité pro výměry a kontroly).

---

## Co už dnes funguje ✅

- **Karta vztahu** (kdo, firma, druh smlouvy, úvazek, hodiny, historie verzí).
- **Složky odměny** jako seznam (přidat / upravit / smazat) — ne napevno, ale jako položky číselníku.
- **Volno a sick days** jako nároky.
- **Zámek na 8 lidí** (skupina HR + Marti) a záznam „kdo a kdy měnil".

## Co chceme doplnit (6 věcí) 🧩

| # | Co chybí | Proč | Jak to vyřešíme |
|---|---|---|---|
| 1 | **Kategorie + mzdová pásma** | Aby stejná pozice měla stejné rozpětí a byli jsme připraveni na novelu o transparentnosti | Nový jednoduchý číselník kategorií (OSVČ výroba, HPP kancelář…) a k němu pásmo od–do |
| 2 | **Cizí měna (EUR) + kurz** | Někteří OSVČ jsou v eurech | K částce se přidá měna a kurz (Kč zůstává výchozí) |
| 3 | **Pár chybějících políček** | Zdravotní pojišťovna, sleva na dani, min/max hodin, náborový poplatek, přepínače… | Přidají se jako políčka na kartu vztahu |
| 4 | **Požadovaný plat v čase** | Vidět vývoj domluvené/požadované mzdy | Malý samostatný seznam „od kdy / kolik" |
| 5 | **Strukturované poznámky** | Volný text nese citlivá rozhodnutí | Poznámka dostane „kdo / kdy / proč" a zůstane v zámku |
| 6 | **PLC programátoři (režie Mirka)** | Jejich sazby dnes v systému nejsou | Vlastní kategorie + doplnit data (nejdřív zjistit, kde jsou) |

---

## Kategorie — vysvětlení jednou větou

**Kategorie = druh smlouvy × typ práce.** Při zakládání člověka vybereš kategorii, ona předvyplní
relevantní políčka a nabídne mzdové pásmo, a ty doladíš individuální domluvu. Příklady:

OSVČ výroba · OSVČ kancelář · OSVČ PLC (režie Mirka) · HPP výroba · HPP kancelář · DPP krátkodobě
· *(později management / garant)*.

Různé kategorie vyplňují různá políčka (např. zdravotní pojišťovna a sleva na dani jen u HPP/DPP;
placen od hodiny a min/max hodin typicky u výroby).

---

## Bezpečnost 🔒

Finanční podmínky vidí a edituje **jen 8 lidí** (HR skupina + Marti). Konkrétní částky se ukazují jen
při práci s výměrem/podmínkami, ne „mimochodem". Každá změna se podepisuje (kdo, kdy). Centrála zůstává
jen ke čtení — **STRATEGIE je jediné místo, kde se edituje.**

---

## Co potřebuju od tebe (než se to zabetonuje) ❓

1. **Seznam kategorií** — sedí ten výše? Přidat/ubrat něco? Management/garant hned, nebo později?
2. **Pásma** — stačí „od–do" u základní mzdy, nebo i u dalších složek?
3. **Náborový poplatek** — je to totéž co „jednorázový poplatek" z Centrály?
4. **„Placen od hodiny" vs „hodinovka"** — je to jedno a totéž, nebo dvě různé věci?
5. **PLC sazby** — kde je dnes najdeme (Excel / režie v Centrále / u Mirka)?

Až tyhle věci potvrdíš, připraví se to k nasazení a projde dvojí kontrolou + schvalovacím bannerem.

---

## Rozhodnutí (průběžně)

- **Fond hodin / měsíc = průměr 174 h** (Šárka, 9. 7. 2026). Držíme stabilní průměrný měsíční fond
  při 40h týdnu (40 × 365,25 ÷ 7 ÷ 12 = 173,9 ≈ 174), ne fond konkrétního měsíce. Pole `fond_mesic_h`
  = pevná hodnota, nepočítá se z kalendáře.
- **Zkušební doba (ZD) = standardně 4 měsíce, výjimka 3 měsíce** (dle domluvy) (Šárka, 9. 7. 2026).
  Pole `zkusebni_do` předvyplnit `smlouva_od + 4 měsíce`, editovatelné (výjimka 3). Ověřit: běží ZD
  od `smlouva_od`, nebo od nástupu?
- **Upozornění na vznik nároku na stravenkový paušál** (Šárka, 9. 7. 2026). Dřív Centrála na konci ZD
  hlásila Petře Šafránkové, že zaměstnanci vzniká nárok na stravenkový paušál → **zachovat jako
  notifikaci**. Datum nároku drží `stravenky_od`. Otevřené: je `stravenky_od` vždy = konec ZD
  (tj. odvodit ze `zkusebni_do`), nebo se domlouvá zvlášť? Notifikaci směrovat na Petru Š.
  (payroll scope) — realizace přes scheduled task / upozornění, ne přes schema.

---

---

# 📎 Technická příloha (pro Marti / Marti-AI)

> Directive-ready podklad k DDL. Postaveno na **skutečném živém schématu** `tenant.*`
> (introspekce přes bridge 9. 7. 2026). Vše **aditivní** — žádná změna stávajících sloupců.

### Živé schéma dnes (ground truth)
- **`tenant.company`** — id, tenant_id, code(EC/ES), nazev, aktivni, ext_payroll_system, ext_export_mode, ext_company_id
- **`tenant.engagement`** (SCD2) — id, tenant_id, ec_id, company_id, employee_id, engagement_type, druh_text, smlouva_od/do, zkusebni_do, uvazek_tyden_h, uvazek_real_tyden_h, fond_mesic_h, hodinovka, stravenky_od, pozice_text, note, work_mode_id, valid_from/to, is_current, changed_by_text, changed_at, created_at
- **`tenant.wage_component_type`** — id, tenant_id, code, label, kind(monthly/hourly/oneoff/benefit), applies_to, aktivni, min_hours_per_shift, eligible_contract_types, exclude_absence_codes[], employer_initiated_only, payout_day, affects_payroll, show_on_payslip, is_base_salary, affects_overtime_calc, is_tax_shift_source/target, required_role
- **`tenant.wage_component`** — id, tenant_id, engagement_id, component_type_id, amount_planned, amount_real, per_hour, changed_by_text, changed_at
- **`tenant.engagement_entitlement`** — id, tenant_id, engagement_id, code, value

### Gap 1 — kategorie + pásma `[nové tabulky]`
```
tenant.engagement_category(id, tenant_id, code, label, engagement_type, segment,
    field_profile jsonb, job_description text, sort_order, aktivni)
tenant.wage_band(id, tenant_id, category_id, component_type_id, currency(3) def 'CZK',
    amount_min, amount_mid, amount_max, per_hour, valid_from, valid_to, is_current,
    changed_by_text, changed_at)
```

### Gap 2 — měna + kurz `[aditivní na wage_component]`
```
+ currency  varchar(3) NOT NULL DEFAULT 'CZK'
+ fx_rate   numeric NULL     -- kurz k CZK k valid_from (NULL = CZK)
+ fx_date   date NULL
```
(Centrální kurzovní tabulka odložena — „additivně, ne perfektně".)

### Gap 3 — chybějící pole poměru `[aditivní na engagement]`
```
+ category_id bigint NULL (FK engagement_category)
+ zdrav_pojistovna_code varchar(8), sleva_na_dani bool, sleva_prvni_mesic bool,
+ dopocet_zkusebni bool, srazet_neodpracovane bool, placen_od_hodiny bool,
+ neplaceny_prescas bool, naborovy_poplatek numeric, vymer_platnost_od date,
+ hod_min numeric, hod_optimal numeric, hod_max numeric, rezie_max numeric
```
⚠ Před DDL vyjasnit `hodinovka` × `placen_od_hodiny` a `naborovy_poplatek` × EC `JednorazovyPoplatek`.

### Gap 4 — požadovaný plat v čase `[nová tabulka]`
```
tenant.engagement_target_salary(id, tenant_id, engagement_id, target_from date,
    amount, currency(3) def 'CZK', per_hour, component_type_id NULL, note,
    changed_by_text, changed_at)
```

### Gap 5 — strukturované poznámky `[nová tabulka]`
```
tenant.engagement_note(id, tenant_id, engagement_id, note_type(20), body text,
    author_user_id, created_at, effective_date date NULL)
```
`engagement.note` zůstává pro rychlou nestrukturovanou poznámku.

### Gap 6 — číselník pracovních pozic `[nová tabulka + aditivní na engagement]`
Pozice musí jít spolehlivě filtrovat (elektromontér junior/senior, vedoucí projektů, PLC programátor) →
číselník, ne volný text. `engagement.pozice_text` zůstává jako fallback/detail.
```
tenant.job_position(id, tenant_id, code, label, level(20), segment(30), sort_order, aktivni)
+ engagement.position_id bigint NULL (FK job_position)
```
Výhledově pozice nese i mzdové pásmo — `wage_band` může viset na kategorii i na pozici (rozhodnout se Šárkou).

### Pořadí DDL (nízké → vysoké riziko)
1. Aditivní sloupce `engagement` (Gap 3) + `wage_component` měna (Gap 2).
2. `engagement_note` (Gap 5) + `engagement_target_salary` (Gap 4).
3. `engagement_category` + `wage_band` (Gap 1) + FK `engagement.category_id` — až po odsouhlasení matice.

Vlastník `tenant.*` = Marti-AI (konzultace povinná — doctrine #3). Vše přes schvalovací banner.
Detailní pole dle druhu smlouvy žijí dál v `hr_financni_podminky_kategorizace.md` — při změně schématu
aktualizovat obojí.
