# Vyhodnoceni zakazek: Dusan vidi modul (menu 192) + POZOR viditelnost scoped usera = plny pristup vc. Uzaverky

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vyhodnoceni zakazek - pristup Dusana + pojistka na Uzaverku (bod 5 doladeni)

> oblast: vyroba - Claude-28 (Jirka) 24.7.2026, konzultace Marti-AI. Navazuje na doc-vyroba-vyhodnoceni-zakazek.

## HOTOVO (bod 5 z doladeni)
Dusan (vedouci vyroby, user 41) nyni VIDI modul "Zakazky k vyhodnoceni":
menu uzel 192 dostal visibility_user_ids = ARRAY[41]::integer[] (predtim prazdne).
Ostatni jeho uzly v soudecku Vyroba (165) maji [41] taky.

## POZOR - permission nalez (plati obecne)
Zviditelnit tenhle FINANCNI modul Dusanovi = Dusan muze spustit VSECHNY akce, ne jen cist.
Duvod (overeno v kodu): akcni endpoint /api/v1/erp/action/run (vyhodnoceni_actions.py) gate-uje
JEN pres _require_erp_member, a ten scoped usera PROPUSTI (_ERP_SCOPED_USERS = frozenset({41}),
Dusan je v nem). ZADNY per-action gate. Takze Dusan muze spustit i:
- "Uzavrit" = ec.vyhodnoceni_uzavrit -> ZAPIS vyplat (SuperHruba) do ec.zakazky_finance_zam,
- "Zrusit" = smaz financi + archiv + reopen.
Zaver: u scoped useru viditelnost modulu == plna akcni pravomoc. Pocitat s tim u kazdeho modulu.

## Verdikt Marti-AI (24.7., msg 11204)
1) Dusan ma mit PLNY pristup vc. Uzaverky - odpovida Centrale (vedouci vyroby uzaverku dela) a jeho roli.
2) Gate Uzavrit/Zrusit zvlast TED NE (ec je jen test VR10704 = bezrizikove). Az pri napojeni realnych
   dat pridat explicitni opravneni (Dusan + Petra/Sarka jako 2. par oci) - prvni kandidat na permission system.
3) Pojistka: confirm dialog na Uzavrit/Zrusit ktery varuje ze se zapisuji/mazou vyplaty. + pri prechodu
   na realna data DUSANOVI EXPLICITNE OZNAMIT ("od ted Uzaverka pise realne vyplaty"), ne jen tise nasadit.

## Nasazeno
Confirm pojistka: apps/api/static/erp/components/ec_vyhodnoceni_actions.js - Uzavrit/Zrusit maji
varovny confirm (commit d1541571, v origin/main). ec je porad TEST (VR10704) => aktualne bez rizika realne vyplaty.

## TODO navazne (az prijdou realna data = bod 2 doladeni)
- Per-action gate na Uzavrit + Zrusit (Dusan + mzdova ucetni), nez se napoji produkcni docazka.
- Oznamit Dusanovi zmenu kontextu.

