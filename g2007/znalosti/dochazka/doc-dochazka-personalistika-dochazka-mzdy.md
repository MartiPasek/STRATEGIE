# Personalistika zaměstnanců — docházka + mzdy (analýza + návrh)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Personalistika zaměstnanců — docházka + mzdy (analýza + návrh)

**Zdroj:** Šárka (mzdová účetní), předáno Marti 10. 6. 2026
**Autor analýzy:** Claude (id=23) · **Stav:** návrh k konzultaci Marti-AI (doctrine #8)
**Cíl:** jeden systém, kde pro každého zaměstnance vidíme VŠE potřebné pro docházku i mzdy — pravidla skupiny + individuální výjimky, nároky (dovolená/sick/HO), benefity a odměny.

## 1. Mapování na existující struktury (nestavět znovu)

| Oblast spec | Už máme | Doplnit |
|---|---|---|
| Skupiny lidí (ELEKTROMONTÉŘI/KANCELÁŘE) | `tenant.staff_group` (Výroba, …) + `org_post` | **pracovní režim** skupiny = sada pravidel (úvazek, nástup, přesčas, daň. úspory) |
| Úvazek / pracovní podmínky per člověk | `tenant.engagement` (SCD2 per člověk, finance v2) | rozšířit o úvazek h/týden, dny v týdnu, povinný nástup, neplacený přesčas |
| Nároky (dovolená, sick days, HO) | `tenant.entitlement` (finance v2) | typy nároků + senioritní bonusy + výjimky |
| Mzdové složky (stravenka, indiv. odměna, prémie) | `tenant.wage_component(_type)` | typy + pravidla výpočtu |
| Píchání / nahlášení nepřítomnosti | `tenant.att_action` (personalizace, design) + `att_entry` | vázat deadline nahlášení na režim skupiny |
| Benefity (věrnostní poukázky) | `tenant.benefit_*` (hotovo 9.6.) | sjednotit pod stejný vzor |

Klíč: **většina je rozšíření finance v2 + skupin, ne nový svět.**

## 2. Datový model (návrh)

### A) Pracovní režim skupiny — `tenant.work_mode`
Sada pravidel přiřaditelná skupině (ELEKTROMONTÉŘI, KANCELÁŘE):
- `tydenni_uvazek_h` (40), `dny_v_tydnu` (Po–Pá),
- `povinny_nastup` (07:00 / 09:00),
- `neplaceny_prescas_h_den` (0.0 / 0.5),
- `absence_deadline` (= povinný nástup),
- `vikend_jen_schvaleni` (bool), `homeoffice_jen_schvaleni` (bool),
- `dan_usp_obleceni` (ANO), `dan_usp_homeoffice` (ANO jen kancl),
- `homeoffice_limit_h` (kancl 48).
Vazba skupina→režim (FK na `staff_group` nebo nová `hr_group`).

### B) Individuální výjimky — rozšířit `tenant.engagement`
Per člověk (SCD2, už verzované) přepisy režimu:
- `uvazek_h` (Brudnová 35, Bernardová 32, Dvořáková 30, Veverková 20, Novotná 35, Vlková 15, …),
- `dny_v_tydnu` (Bernardová 4×8, Mózer 1× úterky, Vlková 0 dní),
- `pausalni_mzda` (Mózer), `flexibilni_min` (Marešová „může méně"),
- `homeoffice_h` (Zeman 64), `homeoffice_adresa` (z dohody o výkonu práce),
- `dan_usp_obleceni` / `dan_usp_homeoffice` override (Bláha: oblečení + HO i když elektro).

### C) Nároky — `tenant.entitlement` + `entitlement_type`
Typy: `dovolena`, `dodatkova_dovolena`, `sick_day`, `homeoffice`.
- Dovolená: základ 20 + dodatková 5 = 25.
- **Senioritní bonus** (pravidlo, ne ruční): +1 den po 10, +1 po 15, +1 po 20 letech (z data nástupu).
- Sick days: základ 2; výjimky Novotná +13 (=15), Brudnová +3 (=5); **nevyčerpané → proplatit 70 %** (mzdové pravidlo na konci roku).
- HO: kancl 48 h, Zeman 64 h.

### D) Mzdové složky / odměny — `tenant.wage_component_type`
- **Stravenkový paušál**: 82 Kč / odpracovaná směna; NEnáleží při sick day / OČR / PN / neodpracované směně → výpočet z docházky.
- **Individuální odměna od jednatele**: mimo mzdový výměr, jen ve finančních podmínkách (Trunec; dříve Purkar, Pěchouček). Příznak `mimo_vymer=true`, viditelnost omezená.
- **Prémie za vedení lidí**: individuální u vedoucích (Havlát, Šafránková, Veverka…) — vázat na roli vedoucího skupiny.
- **Prémie za loajalitu** (dobrovolný přesčas): odměna místo proplacení.

### E) Přesčasy — `tenant.overtime` (evidence) + pravidla
- Roční limit **150 h** (zákoník práce) — hlídka.
- Typ: `narizeny` (proplácen dle ZP) vs `dobrovolny` (prémie za loajalitu).
- Pozn.: ve smlouvách mzda „s přihlédnutím k přesčasu" — **výtka auditorů**, právní stanovisko **JUDr. Senfta** = OK, doporučení zvážit úpravu. → evidovat jako poznámku/risk, ne automatiku.

### F) Schémata odměn — číselníky
- **Doporučení**: 500 Kč za pohovor; nástup: elektromontér 30 000, VP/IT 50 000, PLC 100 000.
- Tabulka `tenant.referral_bonus_cis` (role → částka).

## 3. Docházka vs Mzdy — kde se co projeví

- **Docházka** (živě): povinný nástup, deadline nahlášení absence, víkend/HO jen po schválení, úvazek a dny v týdnu (plán × realita), čerpání dovolené/sick/HO.
- **Mzdy** (podklad): stravenka z odpracovaných směn, proplacení 70 % nevyčerpaných sick days, senioritní dovolená, individuální odměny, prémie, přesčasový limit.

## 4. Otevřené otázky pro Šárku / Marti

1. **Skupina vs režim**: ELEKTROMONTÉŘI/KANCELÁŘE = napojit na stávající `staff_group`, nebo samostatný číselník „pracovní režim"? (lidé můžou být v provozní skupině i v mzdovém režimu zvlášť)
2. **Senioritní dovolená**: počítat z `DatumNastupPP` (Helios) automaticky, nebo ručně potvrzovat?
3. **Stravenka**: „odpracovaná směna" = jakýkoli den s píchnutou prací, nebo min. počet hodin?
4. **Individuální odměna**: kdo ji smí vidět (jen jednatel + payroll_officer, dle finance v2 hranice Marti-AI)?
5. **HPP vs DPP/DPČ**: kde to Helios drží (TabMzNastupPP prázdná) — potřebujeme od Šárky.
6. **Poslední mzdové období** EC = 149 má jen 17 lidí (řídké) — bereme poslední uzavřené?

## 4b. ZÁVAZNÉ ZÁVĚRY konzultace Marti-AI (10. 6. 2026, doctrine #8)

1. **Skupina × režim = DVĚ oddělené dimenze.** `staff_group` = org realita; `work_mode` = mzdová/docházková konfigurace. `staff_group.work_mode_id` = skupinový default; `engagement.work_mode_id` (nullable) = individuální přepis. Resolver: `COALESCE(engagement.work_mode_id, staff_group.work_mode_id)`. (Bláha = ELEKTRO skupina + KANCL daň. úspora override — bez nové skupiny.)
2. **Pravidla = typované sloupce na `work_mode`, NE EAV.** Nová firma = nový řádek + hodnoty (konfigurace, ne kód). `absence_deadline` není sloupec — je to `povinny_nastup`.
3. **Resolver `resolve_work_params(person_id, date)`** jako view/aplikační funkce (NE trigger — side effects v SCD2 = past). Override sloupce v `engagement` (všechny nullable): `work_mode_id`, `uvazek_h_override`, `homeoffice_h_override`, `dan_usp_override`, `flexibilni_min`.
4. **Nároky = pravidlo (data) + snapshot při vzniku** (audit „proč 15 sick days"). `entitlement_rule` (base_amount, `seniority_rules` JSONB `[{after_years,bonus}]`) → generuje snapshot `entitlement` (rule_id, base, seniority_bonus, exception_amount, total, used, remaining). Výjimka (Novotná +13) v `entitlement`, ne v rule.
5. **Mzdové složky = formule jako data.** `wage_component_type`: `calculation_basis` (attendance_shifts/fixed/manual), `unit_amount` (82), `exclude_absence_types` JSONB, `mimo_vymer` bool, `payout_rule` JSONB (`{on:year_end, rate:0.70, basis:unused_sick}`).
6. **Citlivost = `mimo_vymer=true` + role-based visibility** (payroll_officer + jednatel vidí; vedoucí/HR ne). Architektonická hranice z finance v2, ne EUROSOFT specifikum.
7. **Prodejnost — 3 rizika:** (a) hardcoded absence typy → `tenant.absence_type` číselník, NE enum; (b) senioritní prahy v migraci → jen v `entitlement_rule.seniority_rules` per tenant; (c) `staff_group` code natvrdo v kódu → vše přes `work_mode` parametry. **Hned:** seed EUROSOFTu jako `is_seed_data`, oddělit od schema migrations; `work_mode`/`absence_type` tenant-owned.

**Pořadí DDL (Marti-AI):** 1) `absence_type` 2) `work_mode` 3) rozšíření `engagement` 4) `entitlement_rule`+`entitlement` 5) rozšíření `wage_component_type` 6) `overtime` 7) `referral_bonus_cis`. Kroky 1+2 NEzávisí na Šárce → stavíme hned.

**Marti-AI's 2 otázky pro Šárku (závazné pro kroky 4–5):**
- Stravenka: „odpracovaná směna" = jakýkoli docházkový záznam `is_worked=true`, nebo min. hodiny?
- HPP vs DPP/DPČ: potřeba jako sloupec v `engagement` (typ poměru) — senioritní pravidla i stravenka se liší.

## 5. Návrh postupu (fáze)

- **Fáze A — konzultace Marti-AI** (doctrine #8): model výše, hlavně A+B+C (režim, engagement rozšíření, nároky). Je spoluautorka finance v2, sedí jí to.
- **Fáze B — DDL + napojení**: `work_mode` + rozšíření `engagement` + `entitlement_type` + senioritní pravidlo.
- **Fáze C — výpočty**: stravenka z docházky, sick-day payout, přesčasový limit hlídka.
- **Fáze D — UI**: karta zaměstnance „vše pro docházku a mzdy" (režim + výjimky + nároky + odměny) v účetním/HR pohledu.

## Návaznosti
- [[finance_zamestnancu_v2]] · [[org_struktura_v2]] · [[kontakty-univerzalni-pravda]]
- `docs/dochazka_volby_personalizace.md` (personalizace píchání — deadline nahlášení sem patří)


