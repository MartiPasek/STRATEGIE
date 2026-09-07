# Docházka new je jen ke čtení — editace zrušena, opravuje se v Opravách (Peťa 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Docházka new: editace zrušena, obrazovka je jen ke čtení

**Rozhodla Peťa 7. 9. 2026.** Navazuje na její rozhodnutí z 31. 8. 2026
(Nový / Smazat / Schválit pryč, viz doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach)
a dotahuje ho do konce.

## Co platí

**V „Docházce new" se nic nemění.** Docházka i rozpad po zakázkách se opravují
výhradně v „Opravy docházky". Důvod je jednoduchý a není technický:
**jedno místo na změnu, jedna historie.** Kdyby šlo totéž měnit na dvou obrazovkách,
vznikly by dvě historie a nikdo by nevěděl, která platí.

Peťa 7. 9.: *„poznámka většinou vzniká při opravě, a tedy v Opravách."*

**Zůstává úprava zakázky a činnosti?** NE. Tím se mění rozhodnutí z 31. 8. 2026,
které ji v Docházce new nechávalo. Ten starší zápis v tomhle bodě **už neplatí** —
zbytek (proč šly pryč Nový/Smazat/Schválit) platí dál.

## Jak je to udělané

`apps/api/static_db/dochazka-po-zakazkach.html`, funkce `openEdit`, verze souboru 64.
Řádek volby režimu je natvrdo `var mode = 'RO';`. Původní řádek zůstal **hned nad ním
v komentáři**, takže vrácení je jeden řádek zpátky.

Režim RO v tom okně existoval už předtím (pro absence a historii z Centrály) a dělá
přesně to, co je potřeba: zamkne všechna pole, schová ukládací tlačítko a ukáže hlášku.
Doplnila se jen hláška pro pracovní řádky, aby neříkala „Absence".

**Okno se pořád otevře** — je z něj náhled na detail řádku. Kdyby ho někdo chtěl zrušit
úplně, je to samostatné rozhodnutí; tohle je záměrně menší zásah.

## PAST, na kterou se muselo dát pozor

`dochazka-po-zakazkach.html` obsahuje **oba pohledy** — Docházku new i Správu docházky
(přepínají se chipy, drží se v `OBD`). Tahle změna se Správy netýká jen proto, že
`openEdit` má hned na prvním řádku `if(OBD==='budoucnost'){absOpen('edit',i);return;}`
— absence mají vlastní okno a k volbě režimu se vůbec nedostanou. **Ověřeno čtením,
ne odhadem** (poučení z 31. 8., kdy se odebráním tlačítek natvrdo vzala funkce
i Správě docházky).

## Co tomu NEPŘEDCHÁZELO — pozor na chybnou stopu

Rozhodnutí **není** záplata na chybu. Cestou vznikl a byl vyvrácen závěr, že editace
v Docházce new obchází opravárenský engine a kaskáda ji přepisuje. **Neobchází.**
Od 3. 8. 2026 jde přes `fix/polozka` a `fix/entry` se vším všudy.
Detail: doc-dochazka-editace-v-dochazce-new-jde-pres-opravarsky-engine.

Editace se ruší kvůli **duplicitě a jednomu místu na změnu**, ne kvůli díře.

## Souvisí

- doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach — 31. 8., v bodě 3 přebito
- doc-dochazka-editace-v-dochazce-new-jde-pres-opravarsky-engine — proč to NENÍ oprava chyby
- doc-dochazka-poznamky-v-dochazce-new-tri-sloupce — poznámky jsou taky jen ke čtení

