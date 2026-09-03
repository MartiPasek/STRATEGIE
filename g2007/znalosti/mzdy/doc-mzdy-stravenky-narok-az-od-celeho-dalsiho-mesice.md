# Stravenky: narok az od 1. dne CELEHO DALSIHO mesice po zkusebce (smernice 1301, oprava 3.9.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Stravenky: narok vznika az od celeho dalsiho mesice

**Peta + C26, 3.9.2026.** Overeno proti trem zdrojum najednou - smernici, kodu Centraly a datum.

## Pravidlo

Smernice EUROSOFT **c. 1301 v5** "Firemni benefit - penezity prispevek na stravovani",
platna od 3.4.2023, aktivni (ostatnich sest stravenkovych smernic je v archivu):

> "Penezity prispevek na stravovani se poskytuje vlastnim zamestnancum konajicim praci
> v pracovnim pomeru **od 1. dne kalendarniho mesice, jenz nasleduje po mesici, v nemz
> zamestnanci uplynula zkusebni doba**."

| Zkusebka do | Narok od |
|---|---|
| 26.7. | 1.8. |
| 31.8. | 1.9. |
| 3.9. (posunuta nemoci) | **1.10.** |

Centrala pocita stejne - `EC_KartaZam_DatStravenkyOd` nastavuje `_StravenkyOd` na prvni den
mesice po zkusebce a vola se s uz POSUNUTYM datem, takze prodlouzeni zkusebky narok odsune.

## Co bylo spatne (opraveno 3.9.2026)

`mzdy_stravenky_rows` mel v podmince naroku navic vetev:

```
zkusebni_do < 1. den mesice                    <- spravne
OR zkusebni_do = posledni den mesice           <- CHYBA, odstraneno
```

Ta druha radka davala stravenky uz za mesic, v nemz zkusebka koncila poslednim dnem.
Proti smernici o cely mesic. **NEVRACET** - v kodu je u toho komentar.

Realny dopad zadny: jediny clovek se zkusebkou v 7-8/2026 byl Jan Perina (536, do 26.7.),
kteremu vychazel srpen tak i tak.

## Na co navazuje

Nove datum zkusebky ctou stravenky primo, nic se rucne nenastavuje. Posun o nemoc resi
denni automat - viz [[doc-dochazka-zkusebni-doba-posun-o-nemoc]].
Kde se stravenky pocitaji: [[doc-mzdy-svatky-fond-stravenky-prescas]] (velka zed).

