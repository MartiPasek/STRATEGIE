# Centrala uz nevede dochazku - jeji PocetHodin je zastaraly a nesmi prepsat nase hodiny

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Centrala uz nevede dochazku. Jeji hodiny jsou zastarale.

**Zapsala C24 (Kristy) 11. 9. 2026** po vlastnim omylu, na ktery upozornila Kristy otazkou.
Overeno v kode i v datech.

## Jadro veci

Ve vyhodnoceni zakazek plati **dva ruzne zdroje pravdy** a je nutne je nemichat:

| udaj | zdroj pravdy |
|---|---|
| kalkulovane hodiny, sazby, sefmonter, slouceni | **Centrala** (pres `tenant.oz_zakazky`) |
| **odpracovane hodiny** | **MY** (`tenant.vyroba_work`) |

`ec.prepocet_vyhodnoceni` pocita `pocet_hodin` osob z `tenant.vyroba_work`.
Importer `vyhodnoceni_import_historie` ale mapuje `pocet_hodin <- EC_TempVyhodnoceniZak.PocetHodin`,
tedy z Centraly - a **sync dochazky z Centraly skoncil 14. 8. 2026**.

## Namerene rozdily (11. 9. 2026)

| zakazka | hodiny z Centraly | nase dochazka | rozdil |
|---|---|---|---|
| VR10608 | 375,60 h | **463,13 h** | −87,5 h |
| VR10641 | 351,40 h | **430,12 h** | −78,7 h |
| VR10686 | 1,29 h | **9,94 h** | −8,65 h |

Nejde o zaokrouhleni. Jde o desitky hodin, ktere v Centrale proste nejsou.

## Muj omyl (at ho nikdo neopakuje)

Navrhla jsem storno postavene na vete *"puvodni stav je porad v Centrale, sync ho vrati"*.
Ta veta plati pro kalkulaci a sazby, **neplati pro odpracovane hodiny**. Storno melo
odznacit hlavicku i osoby zpatky na `zdroj='centrala'`, aby je sync prepsal - cimz by
**vedome vymenilo spravne hodiny za zastarale**. Nasazeno request #2882, vraceno #2884
tentyz den, nez to nekdo pouzil.

## Spravne pojeti storna

**Storno vraci AKCI (uzaverku), ne PREPOCET.** `ec.vyhodnoceni_zrusit` ma:
- smazat mzdove radky te uzaverky (parovani na `import_src_id`),
- odmitnout se, kdyz uz odmena odesla do Heliosu (`status='exported'` nebo `exported_at`),
- zarchivovat a smazat financni radky,
- otevrit zakazku.

**Hlavicka a osoby maji zustat prepoctene** - odrazi skutecne odpracovane hodiny.
Pri dalsim vyhodnoceni se stejne prepocitaji znovu z aktualni dochazky.

## Pravidlo k zapamatovani

Nez nekam napises *"puvodni stav vezmeme z Centraly"*, **rozeber si, ktery sloupec odkud
pochazi**. U tabulky, ktera michá prevzata a spocitana data, neexistuje jeden zdroj pravdy
pro cely radek. `ec.vyhodnoceni_osoba` je presne takova tabulka.

## Souvisejici

Znacka `zdroj='strategie'` chrani nase radky pred synchronizaci - dava ji
`ec.vypocet_konstant` (hlavicka, 10. 9.) a `ec.prepocet_vyhodnoceni` (osoby, 11. 9.).
Osoby byly od 10. 9. do 11. 9. nechranene a sync je hodinu co hodinu vracel na hodnoty
z Centraly; projevilo se to na VR10641, kde hlavicka rikala 430,12 h a osoby 351,40 h.
Naprava = spustit Prepocet hodnoceni.

