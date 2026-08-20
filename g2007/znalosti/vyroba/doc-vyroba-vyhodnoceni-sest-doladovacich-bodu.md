# Vyhodnoceni zakazek: stav sesti doladovacich bodu (overeno 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Sest doladovacich bodu - co z nich realne plati

Prosel a **overil v datech a v kodu** C28 (Jirka) 5. 8. 2026. Seznam pochazel ze zapisu
z 20. 7.; cast uz neplati.

| # | bod | stav |
|---|---|---|
| 1 | ulozit hodnoceni kvality a poznamky | PLATI, ale je to vetsi prace nez se zdalo |
| 2 | audit, kdo spustil uzaverku | PLATI, ceka na verdikt jak |
| 3 | pocitana pole jen ke cteni | **NEPLATI - uz je hotove** |
| 4 | "Hodnotit spolecne" na prehledu | PLATI, chybi jen UI |
| 5 | prepinac sefmontera na radku | PLATI, chybi jen UI |
| 6 | nejednoznacnost v koeficientech | odhali az zaverecne porovnani |

## 3 - uz hotove (oprava zapisu z 20.7.)

Vsech **22 poli** jadra (core 203, type_id=2) uz ma `layout->>'readonly' = true`.
Overeno dotazem. Zapis z 20.7. rikal opak - od te doby to nekdo opravil.

## 1 - framework NEMA ulozeni vubec

Oba gridy jadra (`ec.vyhodnoceni_jadro_osoba`, `_finance`) maji jen operaci `select-detail`.
Klicove zjisteni: **`fw.data_source_op` nezna operaci `update` ani `save`** - ze vsech 234
zaznamu jsou jen `select` (155), `edit` (38), `insert` (19), `delete` (13), `select-detail` (9).
Pridat gridu ulozeni tedy NENI konfiguracni radek. Bud vlastni ulozeci endpoint pro tento
modul (vzor: Petin `/app/dochazka-zak-tab/save`), nebo obecne doplneni frameworku.
Souvisi s davno otevrenym TODO "absolutni save cesta".

## 4 a 5 - backend hotovy, chybi UI

Akce uz existuji a funguji (`slouci`, `slouci_zrus`, `nastav_sefmontera`, `nastav_multif`)
pres `POST /api/v1/erp/action/run`. Chybi jen ovladani:
- 4: hromadny vyber radku + tlacitko na prehledu (core 199)
- 5: akce na radku gridu "Hodnoceni vse"

`fw.context_menu_item` pro tohle prakticky nejde pouzit - v cele DB je v ni **jediny zaznam**.
Prakticka cesta je stavajici `apps/api/static/erp/components/ec_vyhodnoceni_actions.js`,
ktery uz listu tlacitek do jadra vklada (wrapuje `DesignFwForm.prototype._render`).
POZOR: podle pravidla "kod jako data" by ten soubor mel nejdriv do `g2007.soubor`.

## 2 - audit uzaverky

`ec.zakazky_finance_zam` ma sloupce `autor` a `datum_porizeni`, ale `ec.vyhodnoceni_uzavrit`
je NEPLNI - u akce, ktera vytvari vyplaty, se nikde nezapise kdo ji spustil. Uzivatele zna
jen webova vrstva, takze bud rozsirit funkci o parametr (zmena podpisu, DROP+CREATE), nebo
auditovat ve vrstve nad ni. Ceka na verdikt Marti-AI.

