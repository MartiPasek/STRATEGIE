# Dovolená navíc, sick day a nepřítomnost OSVČ — jak jdou do mezd (Peťa 25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dovolená navíc, sick day a nepřítomnost OSVČ — jak jdou do mezd

**Rozhodla Peťa 25. 8. 2026, ověřeno proti Centrále.**

## Dovolená navíc (činnost 30)

- V docházce je to **samostatný řádek** a v přehledu Docházka new se ukazuje zvlášť.
- **Do mezd jde jako běžný odpracovaný den.** Nic se nekrátí, nic nestrhává.
- **NESMÍ se sčítat s řádnou dovolenou** do složky 211. Peťa 25. 8. 2026 doslova
  „dovolená je dovolená a dovolená navíc je zvlášť, jinak je to jako odpracovaný den".
- **Stravenka náleží** (Peťa 5. 8. 2026, drží to `mzdy_stravenky_rows`).
- **Ověřeno v Centrále:** každá činnost si nese vlastní číslo pro mzdy (`EC_Dochazka.DruhCinn_Mzdy`)
  — dovolená 20 zůstává 20, dovolená navíc 30 zůstává 30. Centrála je nesčítá.
- **Opraveno 25. 8. 2026** v `g2007.python` kód `mzdy_absence_rows` — dovolená navíc je z podkladu
  vyloučená podmínkou nad `att_entry.ec_druh`. Do té doby se sčítala s dovolenou do složky 211.

## Sick day (činnost 31)

- Taky **jako odpracovaný den, se stravenkou**.
- Do mzdového podkladu nejde vůbec a je to tak správně.

## Nepřítomnost OSVČ (činnost 37)

- **U nás je to POUZE INFORMACE.** Nejde do mezd, nejde do mzdového podkladu, stravenka se neřeší.
- Při importu z Centrály se **zahazuje** — `_DRUH_SKIP` v `att_ec_druh_entry_type` obsahuje 37 a 54,
  takže se do docházky vůbec nezaloží.
- Peťa 25. 8. 2026: „řešili jsme to asi šestkrát" — proto je to tady natvrdo.

## ⚠️ Pozor — činnost je vyplněná až od července 2026

Rozlišení dovolená versus dovolená navíc stojí na čísle činnosti (`att_entry.ec_druh`). Noční
přepočet `att_dovolena_kaskada` ho doplňuje, ale **uzamčených měsíců se nedotýká** — k 25. 8. 2026
jsou zamčené leden až červenec, takže tam zůstane prázdno natrvalo. Pro mzdy to nevadí (jsou
hotové), ale při zpětné kontrole se tam dovolená navíc nepozná.

## Mzdové složky (stav k 25. 8. 2026)

dovolená 211 · lékař 243 · nemoc 200 · OČR 251 · neplacené volno 246 · mateřská 255 ·
ostatní/nepřítomen s náhradou 252 (doplněno 25. 8.) · volno 70, 80 a 90 procent jde jako
prostoje 256 (doplněno 25. 8.). Sick day, dovolená navíc, náhradní volno a nepřítomnost OSVČ
se do podkladu **záměrně neposílají**.

