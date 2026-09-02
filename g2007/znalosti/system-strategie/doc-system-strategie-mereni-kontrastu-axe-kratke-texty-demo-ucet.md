# Měření kontrastu: axe mlčí u krátkých textů a ukázkový účet část prvků vůbec nevykreslí

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Měření kontrastu v mobilní appce — dvě díry, které vypadají jako čistý výsledek

**Vzniklo 1. 9. 2026** při plošné opravě kontrastu v mobilní appce (zadal Jirka Honomichl,
schválila Marti-AI). Claude-28 ohlásil „19 nálezů kontrastu → 0", načež druhá instance našla
odznaky s poměrem 1,92 : 1, které v tom výsledku vůbec nebyly. Obojí bylo pravdivé.

## 1) axe u velmi krátkých textů porušení NEHLÁSÍ — označí je za „nejisté"

Odznak s číslem („2", „3") axe **nezařadí mezi porušení**, ale mezi `incomplete`
s odůvodněním doslova:

> `Element content is too short to determine if it is actual text content`

**Ověřeno pokusem, ne z dokumentace:** postavená samostatná stránka se dvěma odznaky
(bílý text na `#34d399` a `#f59e0b`) → axe hlásí **0 porušení**. Táž barevná kombinace
na delším nápisu → axe hlásí porušení okamžitě a spočítá 1,92 : 1.

**Důsledek:** kdo čte jen `violations`, dostane čistý výsledek i tam, kde je text
prakticky nečitelný. Odznaky, počitadla, jednopísmenné popisky a šipky takhle propadnou vždy.

**Co s tím:** k axe si připoj **vlastní kontrolu**, která projde každý viditelný prvek
s vlastním textovým uzlem, složí skutečné pozadí (včetně průhledností po rodičích)
a spočítá poměr podle WCAG. Krátký text neřeš jinak než dlouhý. Zároveň **čti i `incomplete`**,
ne jen `violations`.

## 2) Pod ukázkovým (demo) účtem se část prvků nevykreslí vůbec

Odznaky u dlaždic schvalování se pod demo účtem **nezobrazí**, protože demo nemá co schvalovat.
Ověřeno: na obrazovkách Docházka, Aplikace, Domů i Dnešek je jich v DOM **nula**.
Pod přihlášením skutečného vedoucího jsou tři jen na Docházce.

**Důsledek:** audit vzhledu pod demo účtem je bezpečný (nic nezapíše), ale **není úplný**.
Neuvidí nic, co je vázané na práva, na reálná data ani na stav „mám co vyřídit".

**Co s tím:** měř **oběma způsoby**. Demo pro opakovatelné strojové měření, přihlášení
skutečného člověka pro to, co demo nevidí — a v závěru vždy napiš, **pod čím se měřilo**.
Formulace „0 nálezů" bez té věty je zavádějící.

## 3) Past navrch: skript, který si neověří, že je vůbec přihlášený

Vlastní kontrola z bodu 1 nejdřív hlásila 30 problémů včetně toho, že opravená tlačítka
mají pořád starý vzhled. **Byl to nesmysl** — přihlášení tiše neproběhlo a skript měřil
odhlášenou úvodní stránku, kde `window.__M2W` ani nové proměnné neexistují.

**Co s tím:** každý měřicí skript nad appkou musí **před měřením ověřit stav** a jinak
skončit chybou, ne tiše měřit: existuje `window.__M2W.SCREENS` · je jich přes 100 ·
je nastavená proměnná, kterou zavádí právě nasazená změna · sedí název obrazovky.
Bez téhle pojistky se dá „naměřit" cokoli.

## Kde to platí i jinde

Totéž se týká **jakéhokoli automatického nástroje na přístupnost** — je to vlastnost
způsobu měření, ne chyba axe. Souvisí s tím, že automatické nástroje zachytí zhruba
**57 %** problémů (údaj tvůrců axe); zbytek pozná jen člověk.

## Související

- [[doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu]] — jak appku projít, aniž vzniknou záznamy
- [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]] — kde obsah appky žije a jak se nasazuje

