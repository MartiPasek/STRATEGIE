# Mobil, obsluha dochazky: otevreni menu uz neposouva stranku skoro na konec (9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 9. 9. 2026 ("obrazovka se posune uplne dolu, a to nechci"), schvalila Marti-AI (msg 15252). Provedl Claude-28.**
Zdroj: `g2007.soubor`, kod `apps/api/static/mobile_parts/60_dochazka.js`.

## Co se delo

Po kliku na **Potrebuji ti neco rict** nebo **Tady budu jinde** stranka poskocila
temer na konec, i kdyz karta s menu byla cela videt. Zmereno na zive appce:
posun **z 0 na 321 bodu**, pricemz maximum stranky bylo 373. Nadpis, sekce
i blok zakazky tim zmizely nad okrajem.

## Proc

Obe menu (`showOpts` i `showJinde`) koncila
`bw.scrollIntoView({behavior:"smooth", block:"start"})`.
**`block:"start"` srovna vrsek prvku s vrskem okna VZDY** - i kdyz uz je prvek
cely viditelny. Protoze karta sedi vysoko a stranka je kratka, znamenalo to
odrolovat skoro vsechno.

## Oprava

`block:"nearest"` - **posune jen kdyz je potreba, a nejmensim moznym kusem.**
Kdyz je menu videt, neudela nic. Overeno na zive appce: po otevreni menu
zustala stranka na 0.

## Co se zamerne NEMENILO

Ostatni mista na te obrazovce, kde se `block:"start"` pouziva schvalne, aby
neco "skocilo na oci" - karty ke schvaleni dne, panel zpravy vedoucimu,
formular opravy dne a hlasovy vstup. Tam je vynucene odrolovani zamer.
Po oprave je v souboru 5 mist se `start` a 5 s `nearest`.

## Co si z toho vzit

**`scrollIntoView({block:"start"})` neni "ukaz to" - je to "posun to na vrsek okna".**
Pro "at je to videt" patri `block:"nearest"`.

