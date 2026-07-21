# Karta zaměstnance — profilová hlavička (zadání k implementaci do ERP)

> Zpracováno se Šárkou (Claude-25), 10. 7. 2026. Vizuály: `docs/karta_zamestnance_hlavicka/`.
> **Stav: připraveno k implementaci. Nenasazeno.** Blokuje středisko (viz níže) + čeká na Martiho rozhodnutí o čištění `mod.hr_person`.

## Cíl

Nad stávající dlaždicový přehled na kartě zaměstnance (Základní údaje, Pracovní údaje,
Finanční podmínky, …) přidat **profilovou hlavičku**, která dá to hlavní na první pohled.
Zbytek zůstává za dlaždicemi (uživatel si rozklikne). Vzhled = dark, jako zbytek ERP.

## Co hlavička obsahuje

1. **Foto** zaměstnance (kolečko) + malý odznak fotoaparátu = úprava z mobilu.
2. **Jméno a příjmení.**
3. Řádek **pozice · středisko · firma · město**.
4. **Stav**: Aktivní / Ve výpovědní době / Neaktivní (odvozeno, ne ručně).
5. **Chytrá upozornění** (chipy vpravo): propadlá/blížící se lékařská prohlídka nebo BOZP,
   konec zkušební doby / smlouvy na dobu určitou, narozeniny / pracovní výročí.
6. **Přehled dovolené**: tři dlaždice — dní zbývá / dní využito / dní v plánu.
7. **Rychlé odkazy**: Požádat o nepřítomnost, Organizační struktura, Kalendář.

Náhledy: `nahled_svetly.png` (celá karta se záložkami), `nahled_tmavy_bernardova.png`
(hlavička v dark stylu ERP na reálném zaměstnanci).

## Zdroje dat (důležité — bez Excelu)

| Údaj | Zdroj |
|---|---|
| Jméno, příjmení, tituly, nar., RČ | `mod.hr_person` |
| Nástup / odchod / stav / firma / úvazek | `mod.hr_person_role` (`valid_from`, `valid_until`, `is_active`, `attrs.firma`, `role_kind`) |
| Kontakty, adresa (město) | `mod.hr_person_contact` / `mod.hr_person_address` |
| Dovolená (zbývá/využito/plán) | docházkový/absenční modul |
| Lékařská prohlídka (platnost) | modul lékařských prohlídek |
| Foto | soubor `Příjmení_Jméno` ve složce Foto; úprava zaměstnancem z mobilu + **schválení HR** |

**Stav zaměstnance**: Aktivní = `is_active = true` a (`valid_until` je NULL nebo >= dnes);
Ve výpovědní době = běží výpovědní doba; Neaktivní = `valid_until` v minulosti.

**Filtr aktivních v seznamu**: seznam „Zaměstnanci" defaultně jen aktivní; přepínač
Aktivní / Ve výpovědní době / Bývalí / Všichni. Tím se schovají i technické záznamy.

## ⚠ Blokující / otevřené

1. **Středisko (pozice) NENÍ v `mod.hr_person`.** Migrace z DB_EC (`TabCisZam`) ho netáhne
   (`scripts/migrate_hr_from_dbec.py` nemá středisko ve SELECTu). Bez dotažení budou pole
   „pozice · středisko" prázdná. → **Rozšířit migraci** (přidat středisko z `TabCisZam`),
   nebo číst z DB_EC. Číselník: **001 Výroba rozvaděčů a projekce, 002 Automatizace,
   900 Režie/vedení.** (Řeší Marti — zásah do DB.)
2. **Čištění `mod.hr_person`** — tabulka má 429 řádků, jen 83 aktivních; zbytek bývalí,
   osoby bez role a ~70 „neosob" (Skupina/systémové účty/Výpomoc/NEPOUŽÍVAT/bez jména)
   + 26 skupin duplicit. Rozpad: `Karta zaměstnance/HR_person_kontrola_2026-07.xlsx`.
   Rozhodnutí čistit vs. jen filtrovat → posláno Martimu (10.7.).
3. Ověřit, že seznam v UI čte čistě z `hr_person` (na screenshotu se objevil záznam,
   který v `hr_person` není).

## Implementace (návrh postupu po dovolené Šárky)

1. Marti: rozšířit migraci o středisko + rozhodnout o čištění `hr_person`.
2. Přidat komponentu hlavičky nad dlaždicový přehled karty zaměstnance (dark styl dle náhledu).
3. Napojit pole na zdroje z tabulky výše; stav a upozornění odvozovat, ne zadávat.
4. Foto: render ze složky Foto (`Příjmení_Jméno`), upload z mobilu + schvalovací krok HR.
5. Seznam zaměstnanců: default filtr aktivních + přepínač stavu.

## Souvislosti
- Word návrh (kompletní): `Karta zaměstnance/HR_a_Lide_Karta_zamestnance_navrh.docx`
- Aktuální seznam + kontrola: `Karta zaměstnance/Aktualni_seznam_zamestnancu_2026-07.xlsx`, `…/HR_person_kontrola_2026-07.xlsx`
