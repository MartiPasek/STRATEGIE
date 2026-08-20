# Mobilni editor oprav: useky rozpadu (parita s ERP)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co pribylo (5.8.2026, zadal Jirka)
Mobilni editor oprav (Firma > Spoluprace > Opravy dochazky) do te doby NEZOBRAZOVAL rozpad vubec -
ani u zivych radku, ani u stornovanych. U stornovaneho radku tak byla videt jen zakazka z hlavicky,
coz je POSLEDNI volba dne, ne to, co se ten cas delalo. Stejna past jako v ERP (viz
[[doc-dochazka-opravy-sedy-rozpad-stornovanych-radku]]).

Nove: pod kazdym radkem, ktery ma useky, jdou zobrazit - u STORNOVANEHO sede kurzivou "pod puvodne"
s oznacenim "pred opravou", u ziveho modre "pod zakazka". Vse jen ke cteni.
Ve sloupci Typ je misto jedne zakazky "rozpad (N krat)", kdyz je useku vic.

## Rozdil proti ERP: TUKNUTI, ne dvojklik
Na mobilu neni dvojklik. Useky jsou sbalene a rozbali/sbali je JEDNO TUKNUTI na radek.
Klik na tlacitka (tuzka, kos) rozbalovani nespousti - osetreno pres ev.target.closest('button').

## Kde to zije a jak se to nasazuje
- zdroj: g2007.soubor pps/api/static/mobile_parts/60_dochazka.js
- artefakt: g2007.soubor pps/api/static/mobile.html
**Zmena se zapisuje do OBOU** (chirurgicky replace), pak @@G2007EXPORT apps/api/static/mobile.html.

### PROC NE @@G2007PUBLISH
PUBLISH by artefakt PRESKLADAL z fragmentu. To je nebezpecne, kdyz nekdo (dnes Kristy 13:32)
zasahl primo do artefaktu a jeho zmena jeste neni ve fragmentu - preskladanim by zmizela.
EXPORT jen zapise obsah z DB na disk, nic neprepocitava.
**Overeni po nasazeni:** /mobile musi vratit HTTP 200 a mit <script 28x (kostra appky).
Kdyz je scriptu vyrazne min, doslo k preskladani a je to spatne.

## PAST: git u mobilu ZAOSTAVA
Kopie 60_dochazka.js v gitu byla 5.8. o 3737 znaku STARSI nez verze v g2007.soubor
(C23 delal 11:43 "rederivaci ze zivaku"). **Zdroj pravdy pro mobil je DB, ne git** -
pred upravou si stahni verzi z g2007.soubor, nikdy needituj lokalni kopii z gitu naslepo.

## Overeno 5.8.2026 na produkci
Nosek 3.8. v mobilu: stornovany radek 06:01-12:21 ukazuje "rozpad (6 krat)", po tuknuti se rozbali
sest useku vcetne VR10669 a obou nakladek, s vlnovkou u dopoctenych koncu. Konzole bez chyb,
kostra appky netknuta (28 script tagu pred i po).

