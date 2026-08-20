# Vyhodnoceni zakazek: PENIZE prepnuty na nase tabulky (krok 4, hotovo 6.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Penize uz se pocitaji z nasich tabulek

**Hotovo a overeno 6. 8. 2026** (C28/Jirka). Posledni, ctvrty krok prepnuti.
Navrh schvalila Marti-AI (msg 12214), vyklad potvrdila Kristyna Ksirova 5. 8.

## Co se zmenilo

Do 6. 8. cetly `ec.vypocet_konstant` i `ec.vyhodnoceni_uzavrit` penize z **`ec.dochazka.kc_celkem`**
- zrcadla Centraly, ktere ma **3 radky**. Uzaverka by tedy vyplaty spocitala jako nulove.

Nyni: **hodiny z `tenant.vyroba_work` x superhruba sazba ulozena U RADKU**.
Po zmene **zadna z 12 funkci schematu `ec` uz nesaha na zadne zrcadlo Centraly** (overeno dotazem).

## Sazba je SNAPSHOT u radku, ne dopocet

Nove sloupce `tenant.vyroba_work.sazba_kc_hod` (hruba) a `sazba_superhruba_kc_hod`.
Rozhodnuti Marti-AI: *"dopocitavat za behu znamena, ze historicke prepocty dostanou DNESNI
sazbu, ne sazbu platnou tehdy. U penez je to presne ten problem, ktery snapshot resi."*

Vypocet: soucet mesicnich `wage_component` (kind='monthly') deleno `engagement.fond_mesic_h`
**z verze pomeru platne K DATU RADKU**, superhruba = x1,4 u HPP a x1,0 u OSVC/DPP.

**Backfill: 24 073 z 24 428 radku (98,5 %).** Zbylych 355 nema mzdove slozky nebo fond hodin
(lide bez pracovniho pomeru) - zustavaji NULL **vedome**, at je videt, ze se to nespocitalo.

## Overeni sazeb proti Centrale

`EC_FinZamPodminky` (HrHodsFK i SuperhrHodsFK) u **11 lidi**: os. 1, 11, 16, 21, 126, 147,
435, 474, 483, 488, 536 - **nula odchylek u obou sazeb**.

## Overeni penez na zakazce VR10584 (po lidech)

**5 ze 6 lidi sedi s Centralou NA KORUNU** (3 074 · 729 · 13 730 · 505 · 570).
Sesty (os. 147) se lisi o **38 Kc z 20 225** (0,19 %): my pocitame 341,95, Centralina
`kc_celkem` u tech radku pouzila 333,91. Nase hodnota pritom **odpovida vlastnim aktualnim
podminkam Centraly** pro tohoto cloveka (`SuperhrHodsFK` = 341,95) - Centralina historicka
castka byla spocitana jinou sazbou, kterou v nasi historii vubec nemame.

## ⚠️ NALEZ: zadna verze pracovniho pomeru nema konec platnosti

`tenant.engagement` ma **939 verzi a u VSECH je `valid_to` NULL**. Historie je tedy
"otevreny stoh" - ktera verze plati, rozhoduje **vyhradne `valid_from`** (nejnovejsi <= datum).
Nas vypocet s tim pracuje spravne, ale **pripadna chybna nebo prekryvajici se verze by
tise vyhrala** a nikdo by si toho nevsiml. Stoji za zvazeni doplnit `valid_to`.

## Past pri overovani (uz potreti tentyz jev)

`ec.vyhodnoceni_zakazka.celkem_s_premiemi` je **snimek k datu vyhodnoceni**. Porovnavat
proti nemu aktualni prepocet nema smysl - na zakazce se pracovalo dal. Porovnavej penize
**po lidech proti `EC_Dochazka.Kc_Celkem`**, ne proti hlavicce.

