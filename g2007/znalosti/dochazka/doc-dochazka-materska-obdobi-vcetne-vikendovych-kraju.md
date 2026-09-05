# Mateřská: zápis o období včetně víkendových krajů, do mzdy nejde (Peťa 4. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mateřská — období se zadává celé, i s víkendovými kraji

**Peťa 4. 9. 2026:** *„mateřská se neposílá do výplaty, vyplácí ji sociálka, ale musí to
být zadané správně, tak jako to bylo v Centrále. Nechodí to ze žádosti — člověk nepracuje
a nic s appkou nedělá."*

## Pravidlo

- **Období** (`tenant.att_absence_request`) = skutečný rozsah **včetně víkendových krajů**.
  Tak to měla Centrála (`EC_Dochazka_Udalosti`, mateřská tam běžela vcelku).
- **Denní záznamy** dál jen na pracovní dny — na hodinách se nemění nic.
- **Do mzdy mateřská nejde**, platí ji ČSSZ. Evidence ale musí sedět.
- **Nevzniká ze žádosti** — zakládá ji Peťa nebo Michelle ručně ve Správě docházky.

## Co se stalo (a proč to nebylo vidět)

Michelle Šafránková (381) měla za srpen 2026 v docházce dny mateřské, ale **žádný zápis
o období** — dny vznikly přes Opravy docházky (`source` = `manual_fix`, `source_id`
prázdné). Navíc jí chybělo 3.–7. 8. (pět pracovních dnů), mateřská začínala až 10. 8.

Odhalilo se to při kontrole srpnových mezd, ne kontrolou docházky: u Landmarku vyšlo,
že na něj Michelle podle pravidel nárok má, i když ho mít nemá. Důvod byl, že nemá
odpracovaný den — a při hledání proč se ukázalo těch pět nepokrytých dnů.

**Landmark sám o sobě je v pořádku** — engine dá nulu každému, kdo nemá odpracované dny
(OBL se počítá z nich, HO z podílu odpracovaného fondu). Není potřeba pravidlo
„na mateřské se Landmark nedává".

## Oprava 4. 9. 2026

1. Peťa doplnila chybějící dny 3.–7. 8. (staré řádky přešly do `superseded`, platné jsou
   nové `confirmed` — proto to v přehledu vypadalo, že řádek zmizel).
2. Doplněn zápis o období **1. 8. – 31. 8. 2026** (`stav=approved`, `materialized=true`),
   tedy včetně soboty 1. 8. — request #2708.
3. Všech **21 srpnových dnů** dostalo vazbu na ten doklad (`source_id`) — request #2709.

## Proč v přehledu skáče datum na 3. 8.

Přehled Správy docházky (`fw.data_set` 178 `dochazka.zakazky_budoucnost_list`) kreslí
**ostrovy z denních záznamů**, ne období z dokladu. Když období začíná v sobotu, první
den ostrova je pondělí. Peťa 4. 9.: *„ve Správě musí být vidět první a poslední den
měsíce bez ohledu na to, zda je to víkend."* → **otevřené, viz sekce níž.**

## Otevřené

Přehled má u absencí ukazovat období z dokladu, ne okraje ostrova ze dnů. Je to změna
v 16 000 znaků dlouhém dotazu nad obrazovkou, na které se dělají mzdy — dělat s zálohou
a mimo uzávěrku.

## Souvisí

[[doc-mzdy-obdobi-nemoci-do-mezd-z-neschopenky-ne-z-pracovnich-dnu]] (u nemoci a OČR jde
skutečné období z dokladu i do mezd) · [[doc-dochazka-absence-pres-prelom-mesice-dva-doklady]]

