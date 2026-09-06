# Kontrola, ze text dlazdice sedi s nadpisem obrazovky - metoda, tri pasti a vysledek (6. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Sedi text dlazdice s nadpisem obrazovky, kam vede?

> Zadal Jiri Honomichl 6. 9. 2026, schvalila Marti-AI (msg 14574). Navazuje na
> `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026` a
> `doc-system-strategie-mobil-odstraneni-ctyr-duplicitnich-nazvu-6-9-2026`.

## Vysledek

Ze **129 prvku**, ktere v appce otviraji obrazovku, jich **90 sedelo** a **12 se opravilo**.
Zbytek odpadl jako mrtve obrazovky nebo zamerne zkratky (viz nize).

Opraveno - **Moje absence** (drive Nepritomnosti) - **Personalni slozky** (drive Karta zamestnance) -
**Listecky - schvalovani** - **Nemoc a OCR - prehled** - **Mzdy Helios x STRATEGIE** (2x) -
**Import dochazky** - **Datove schranky** - **Obnova databaze do API D** - a tri nadpisy obrazovek
srovnane s odkazem (**Nutne nekoho sehnat**, **Stav odeslanych SMS**, **Podminky**).

U **Podminek** se menil NADPIS, ne dlazdice - obrazovka pokryva vsechny tri urovne
(system, skupiny i jednotlivce), takze "Podminky jednotlivcu" byl vecne nepravdivy nadpis.

## Metoda (opakovatelna)

Nad **zivou strankou** `/mobile`:
1. Nadpis obrazovky = telo funkce obsahuje `app.innerHTML = topbar("...")`.
2. Prvek = `appCell("ikona","text",...)`, `row(...)`, `navBtn(...)`; cil = prvni navigacni
   volani v JEHO obsluze.
3. Porovnavej po znormalizovani (pryc emoji a interpunkce, mala pismena, bez diakritiky)
   a ber i castecnou shodu - kratsi text dlazdice smi byt podretezcem delsiho nadpisu.

## TRI PASTI, na kterych to poprve selhalo

1. **Cil od sousedni dlazdice.** Kdyz se navigace hleda "nekde za popiskem", chytne se
   `go()` NASLEDUJICI dlazdice. Vzniklo 17 falesnych nalezu (napr. "Dokumentace" -> Uzivatele).
   **Hledej jen do zacatku dalsiho prvku.**
2. **Prvek, ktery vubec nenaviguje.** Radek "Vycistit a nacist" jen obnovi data - cil se opet
   sebral od souseda. **Trvej na tom, ze prvni volani v obsluze JE navigace.**
3. **Nadpis nastavuje pomocna funkce.** `doch_dnesek` vola `_dnesScreen("Dnesek")`, vlastni
   `topbar(...)` nema - hledani "do 900 znaku" pretecelo do dalsi funkce a vzalo cizi nadpis.
   **Omez hledani telem funkce** a pomocne funkce resi zvlast.

## Co NENI nalez

- **Mrtve obrazovky.** Na `hr` ani `hr_interni` nevede ziva cesta, takze nesoulady na nich
  nikdo nevidi. Devet z 26 puvodnich "nalezu" byly tyhle.
- **Hlubsi odkaz s parametrem.** "Ucetni" (`_auMode`) a "Skupina HR - pristupy" (`_skFocusName`)
  otviraji tutez obrazovku v jinem rezimu - nazev nese smysl navic a menit se NEMA.

## Kolika lidi se to tykalo

Dlazdice v Aplikacich a Dochazce vidi vsichni; ty v HR jen financni a HR okruh - nazvy jsou
v `_is_cockpit` (rodice + Sarka a Petra + clenove skupin HR, Finance, Ucetnictvi, Banka).

