# Datum vzniku PP: Helios ho má u každého jinak (u někoho první nástup, u jiného až druhou smlouvu) — proto se zatím nepřenáší

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Kontext

Při stavbě přenosu mzdové karty ze STRATEGIE do pražského Heliosu (viz
`doc-mzdy-prenos-mzdove-karty-do-heliosu`) mělo přibýt i to, co posílala Centrála navíc
k úvazku: druh PP, zkušební doba, datum vzniku a ukončení PP. Peťa 8. 9. 2026: *„je potřeba
mít ve STRATEGII stejné údaje jako v Centrále."*

Při ověřování se ukázalo, že **datum vzniku PP se přenášet nedá** — nevíme, co je správně.

## Co se zjistilo (8. 9. 2026, EC, porovnáno s Heliosem)

| kdo | naše smlouvy | Helios |
|---|---|---|
| Veverka EC 14 | 1.8.2016 (na rok) → 1.8.2017 → 1.2.2019 | **1.8.2016** = první nástup |
| Kolářová EC 24 | 1.6.2020 (na rok) → 1.6.2021 | **1.6.2020** = první nástup |
| Honomichlová EC 420 | 1.9.2018 → 1.2.2019 | **1.9.2018** = první nástup |
| Zeman EC 40 | 1.3.2020 (na rok) → 1.3.2021 | **1.3.2021** = až druhá smlouva |
| Trunec EC 465 | 1.8.2021 (na rok) → 1.8.2022 | **1.8.2022** = až druhá smlouva |
| Navrátil EC 472 | 1.8.2021 (na rok) → 1.8.2022 | **1.8.2022** = až druhá smlouva |

**Helios nemá jednotné pravidlo.** U prvních tří drží datum prvního nástupu, u druhých tří
až datum druhé smlouvy — přestože Veverka, Zeman, Trunec i Navrátil měli identický průběh:
rok na dobu určitou, pak neurčitá.

Ani jedno z obou možných pravidel proto nefunguje pro všechny:
- „nejstarší výměr" → sedí u prvních tří, neplatí u Zemana/Trunce/Navrátila
- „aktuální výměr" → sedí u druhých tří, neplatí u Veverky

## A nepořádek i na naší straně

`engagement.smlouva_od` se mění i tam, kde ke změně smlouvy nedošlo. Veverka měl
1.8.2017 (neurčitá) a pak se to přepsalo na 1.2.2019, přestože šlo jen o změnu mzdy.
Lidé mají 9–10 výměrů a `smlouva_od` na nich neodpovídá jedné smlouvě.

## Co se NEpotvrdilo

Peťa měla podezření na **anglický kalendář** (prohozený den a měsíc při importu).
**Ověřeno, nepotvrdilo se** — data jsou uložená správně, žádné prohození. Rozdíly jsou
věcné, ne formátové.

## Stav ostatních údajů (8. 9. 2026, 50 lidí na HPP)

| údaj | stav |
|---|---|
| týdenní + denní úvazek | přenáší se, běží od 7. 9. |
| kalendář | přenáší se, běží od 7. 9. |
| druh PP | umíme odvodit (typ smlouvy + je/není datum do) |
| datum ukončení PP | **prázdno u 38 z 50** |
| zkušební doba | **vyplněno u 12 z 50**, všem už uplynula |
| datum vzniku PP | **nepřenášet**, viz výše |

⚠ **Zkušebku nepřepisovat prázdnem.** Centrála ji přepisovala vždycky, ale ona ji
vyplněnou měla; my ne. Slepé srovnání by ji v Heliosu smazalo 38 lidem a nahradilo ničím.
Totéž platí pro datum ukončení — prázdnem nepřepisovat, jinak by u odcházejícího člověka
Helios počítal mzdu dál.

## Čeká se

Peťa poslala 8. 9. 2026 Šárce Novotné podklad se třemi otázkami:
1. Co je datum vzniku PP, když se doba určitá překlopí na neurčitou?
2. Má se doplnit historie zkušebních dob, nebo je vést jen u nových?
3. Je prázdné datum ukončení opravdu proto, že mají neurčitou?

**Bez těch odpovědí se přenáší jen úvazek, kalendář a druh PP.** U mezd je lepší neposlat
nic než poslat špatně.

## Mimochodem — další důkaz, že přenos umřel

Zdroj, ze kterého Centrála brala (`EC_Mzdy_SumaMesic` v DB_EC): 5/2026 a 6/2026 po 50
řádcích, **7/2026 ani jeden, 8/2026 jediný**.

