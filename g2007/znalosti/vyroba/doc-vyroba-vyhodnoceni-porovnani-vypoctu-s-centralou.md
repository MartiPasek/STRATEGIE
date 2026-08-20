# Vyhodnoceni zakazek: nas vypocet POROVNAN s Centralou (5.8.2026) - sedi

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Porovnani naseho vypoctu proti Centrale

**Provedeno a uklizeno 5. 8. 2026** (C28/Jirka). Prvni skutecne porovnani CELEHO retezce
vypoctu, ne jen hodin.

## Jak

Puvodni vysledky z Centraly zazalohovany -> zakazka prepoctena NASIM kodem pres
`/api/v1/erp/action/run` (priprava -> vypocet_konstant -> prepocet) -> porovnano ->
**data vracena presne do puvodniho stavu** (overeno: hlavicky i pocty lidi i sumy premii sedi).

## Ferova mnozina je mala - a proc

Porovnavat lze jen zakazky, ktere jsou (a) odemcene = rok 2026, (b) maji hodiny u nas,
(c) uzavrene k datu a (d) po tom datu na nich nepribyly zadne hodiny. Podminka (d) je
klicova: reference z Centraly je **snimek k datu vyhodnoceni**, kdezto nas prepocet bere
aktualni hodiny. Zakazek splnujicich vse je **5**, z toho 3 realne porovnatelne
(VR10490 a VR10511 jsou z roku 2025, jejich hodiny u nas nejsou).

## Vysledek

| zakazka | odpracovano | kalkulovano | usetreno | premie | lidi |
|---|---|---|---|---|---|
| **VR10584** | 63,43 = 63,43 | 67 = 67 | 3,57 = 3,57 | **480 = 480** | 6 = 6 |
| **VR10659** | 55,44 = 55,44 | 49 = 49 | 0 = 0 | **0 = 0** | 7 = 7 |
| VR10442 | 592,97 = 592,97 | 498 = 498 | 0 = 0 | 500 vs 0 | 12 = 12 |

**Dve ze tri sedi uplne presne** - vcetne premii, tedy cely retezec hodiny -> kalkulace ->
usetreny cas -> premie na osobu -> soucet.

## Ten jediny rozdil je VYSVETLENY a nas vypocet je SPRAVNE

VR10442, os. c. 474: hodiny sedi presne (270,95 = 270,95), rozdil je **premie sefmontera 500 Kc**.
Duvod: zakazka je **pretazena** - odpracovano **592,97** vs limit **572,70**. Podminka pro premii
sefmontera je `odpracovano <= limit`, takze pri pretazeni premie NENALEZI a nas vypocet spravne
dava 0. Sefmonter je urceny stejne u nas i v referenci (1 = 1).
Centrala ma ulozenych 500 z doby, kdy zakazka jeste pretazena nebyla - je to stary snimek,
ne rozpor ve vzorci.

## Co z toho plyne

Portovany vypocet reprodukuje Centralu. Nejednoznacnost ve vypoctu konstant (vazeni
odpracovaneho efektivitou), ktera byla vedena jako otevrena od 20. 7., se na tomto vzorku
NEPROJEVILA - `odpracovano` i `odpracovano_ef` sedi. Neznamena to, ze neexistuje;
znamena to, ze na techto zakazkach nema vliv (vsichni maji efektivitu 100 %).

