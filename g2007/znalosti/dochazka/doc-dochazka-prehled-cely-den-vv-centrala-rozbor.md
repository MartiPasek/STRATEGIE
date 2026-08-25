# Prehled "Cely den - VV" ze stare Centraly - kompletni rozbor pred prenosem do STRATEGIE (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prehled "Cely den - VV" — nastroj vedouciho vyroby

**Kdo ho pouziva:** Dusan Havlat (v Centrale zamestnanec c. 105), vedouci vyroby. Kontroluje a opravuje jim dochazku.
**Proc to resime:** pichani se presunulo do STRATEGIE a **Dusanovi se prehled vyprazdnil pod rukama**.

## Zlom: 22.-23. 7. 2026

Do te doby chodilo do Centraly 60-90 pichnuti denne od 30 lidi. Pak nula. Od 4. 8. 2026 uz tam nepribylo jedine skutecne pichnuti — zbyly jen dopredu zadane dovolene (2-7 zaznamu denne se starym datem porizeni).

Ve STRATEGII ve stejny den (25. 8. 2026): **260 zaznamu, 56 lidi, 486 hodin.**

**Dusanova posledni vyrizena chyba je z 22. 7. 2026** — presne tehdy mu dosla data. Neprestal pracovat, prisel o nastroj.

Souvisi: `doc-dochazka-sync-dochazky-z-centraly-ukoncen-2026-08-14`.

## Z ceho se obrazovka sklada

Ctyri prehledy Centraly (cislo je ve sloupci `Cislo` tabulky `EC_DELPHI_TabObecnyPrehled`, NE v `ID`):

| cast | cislo | nazev v Centrale |
|---|---|---|
| horni seznam (den po dni, posledni 3 mesice) | 2060 | Dochazka - cely den small |
| soucet po cinnostech | 2062 | Dochazka suma na cinnosti small |
| detail dne (jednotliva pichnuti) | 2061 | Cely den detail - small |
| pole nahore + mesic/rok pro tisk | 2088 | Dochazka detail |

**Zdroj dat:** `EC_Dochazka` (prace) + `EC_Dochazka_Prestavky` (prestavky ZVLAST), ciselnik zamestnancu, dva ciselniky cinnosti, zakazky se zakaznikem.

**Cas celkem** = (od prichodu do odchodu minus pauza minus "blbost" minus rezie) deleno 60.

**Editace** pres okno "Dochazka - upravy" (formular 9, pro vkladani varianta 1275), uklada procedura `EC_Dochazka_Jadro_Ulozit`, stara podoba se pred ulozenim archivuje do `ec_dochazka_tempJadro_archiv`.

## Pojistky pri uprave (STRATEGIE je musi mit taky)

1. **Uzavreny mzdovy mesic** nejde menit ani mazat (kontrola proti `TabMzdObd` a `EC_Mzdy_SumaMesic`).
2. **Absence** (dovolena, nemoc, lekar, OCR, sick day, otcovska, materska, neplacene volno, nahradni volno, nepritomnost OSVC) se v dochazce upravovat NEDAJI — jen ve Sprave dochazky. Vyjimku maji jen Peta a Kristyna, a i tem to pripomene.
3. **Cas zacatku** smi v Centrale menit jen ctyri lide: Peta, Kristyna, Honza Svoboda, Dusan. *(Rozhodnuti Jirka 25. 8. 2026: ve STRATEGII se to bude resit PRAVY k prehledu, ne jmeny v kodu.)*
4. **Pracovnika u hromadne zmeny** smi menit jen Peta.
5. Kazda rucni zmena se archivuje.

## Akce prave tlacitka — a jak casto se REALNE pouzivaji

Za 12 mesicu (do 25. 8. 2026):

| akce | procedura | pouzito |
|---|---|---|
| Smazat zaznam | EC_Dochazka_SmazatZaznam | **852** |
| Kontrola dochazky - dlouhodoba | EC_KontrolaDochazky_Dlouhodoba | **178** |
| DOCHAZKA nastav parametry hromadne | EC_Dochazka_HromadnyUpdatePolozek | **79** |
| PRESTAVKY nastav parametry hromadne | ..._Prestavky | **42** |
| Kontrola dochazky (jeden den) | EC_KontrolaDochazky | 12 |
| Archiv dne | otevre prehled 2084 | 5 |
| Dogeneruj obed | EC_Dochazka_DogenerujPauzu_Priprava | 2 |
| Srovnej casy | EC_Dochazka_SrovnejCasy | 1 |
| Prodluz obed | EC_Dochazka_ProdluzObed | 0 |
| Smazat cely den | **zadna akce — mrtva polozka menu** | — |

**Kdo chyby vyrizuje** (za 12 mesicu): Dusan **1 339**, Michelle 865, Peta 276, Kristyna 1.

## Rozhodnuti Jirky (25. 8. 2026)

- Stavi se **jen ve STRATEGII**, stara Centrala se resit nebude.
- **Z Centraly se neprenaseji zadna data** — hrozilo by prepsani toho, co uz mame.
- Prenaseji se **vsechny sloupce ze zdroje**, ne jen dnes viditelne.
- Skupiny lidi se neresi (vec Sarky).
- Tisk az uplne nakonec; volba mesice a roku ma byt **osobni nastaveni uzivatele** (v Centrale je to tak taky — tabulka `EC_Dochazka_tisk` na prihlaseneho uzivatele).
- Automaticke opravy dat se **nezavedou, dokud je nepotvrdi Dusan**.

Souvisi: `doc-dochazka-kontrola-dochazky-centrala-co-hlida-a-co-tise-opravuje`, `doc-dochazka-anomaly-ciselnik-druhu-chyb-chybi`.

