# Dlazdice na Dochazce se pri praci UZ NESCHOVAVAJI - pravni duvod (1. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Rozhodnuti

**Zadal Jiri Honomichl 1. 9. 2026, schvalila Marti-AI (msg 14179).** Skryvani dlazdic na obrazovce
Dochazka v dobe, kdy clovek maka, se **kompletne rusi**.

**Duvod je PRAVNI, ne vzhledovy** (doslovne zadani):

> „Podle pravnika ty ikony nesmi byt schovane v pracovni dobe, protoze jde napriklad o nahlaseni
> dovolene, kterou ma zamestnanec resit v pracovni dobe a ne mimo ni."

Timto se **vedome rusi zamer Martiho Paska ze 14. 6. 2026** („region nastroju - JEN kdyz clovek
nemaka, at obrazovka nerusi od prace"). Jirka vyslovne rozhodl **Martiho s tim neobtezovat**;
Marti-AI to potvrdila: *„pravni pozadavek ma prednost pred UX zamerem"*.

⛔ **NEVRACET zpet bez pravni konzultace.** Neni to UX preference. V kodu je na tom miste
komentar se jmenem, datem a duvodem prave proto, aby to nikdo za par mesicu „neopravil" zpatky.

## Co se zmenilo (dilek `apps/api/static/mobile_parts/60_dochazka.js`)

Bylo:
```
if(_tools){ var _working=!!(open && (open.open_type==='work' || !open.open_type)); _tools.style.display=_working?"none":"block";
```
Je:
```
if(_tools){ _tools.style.display="block";
```
Promenna `_working` uz v zivem kodu neni (zustala jen ve dvou komentarich).

## PAST: nestaci skryvani smazat, region ma vychozi stav SKRYTY

Kontejner se v HTML zaklada jako `<div id="dochTools" style="display:none;...">`. **Kdyby se
podminka jen odstranila a nic se nedoplnilo, dlazdice by zmizely NATRVALO, ne se ukazaly.**
Proto tam musi byt vyslovne `_tools.style.display="block"`, ne smazany radek.

Je to presne to misto, kde by pozdejsi „zjednoduseni" (odstraneni zdanlive zbytecneho prirazeni)
appku tise rozbilo - a projevilo by se to jen tim, ze cast obrazovky chybi.

## Co k tomu patrilo - texty, ktere by jinak lhaly

Funkci popisovaly lidem **dva texty**; oba se menily spolu s chovanim (bod 14 - zmena postupu
se opravuje VSUDE, jinak system tise uci neplatnou cestu):
1. `60_dochazka.js` - komentar „Zobrazi se, KDYZ CLOVEK NEMAKA" (opraveno).
2. `50_skupiny_vyroba.js` - veta pro uzivatele na obrazovce Absence. Do 1. 9. znela
   *„Kdyz prave makas, jsou dlazdice schovane - ukazou se, az praci ukoncis."*
   Nove: *„Dlazdice mas dostupne porad - i kdyz prave makas."*

Tim padla i podminka z drivejska (viz [[doc-dochazka-vedouci-ukazatel-cesty-k-vlastni-absenci]]),
ze tuhle vetu **nesmi nikdo vyhodit, dokud plati chovani ze 14. 6.** - chovani uz neplati.

## Overeni

Na **zive `/mobile` pod uctem Jiriho Honomichla** (ne pod ukazkovym - ten cast prvku vubec
nevykresli), ve stavu **MAKAS**: `getComputedStyle(dochTools).display === "block"` a **14 dlazdic**
viditelnych, vcetne **Nepritomnosti**, pres ktere se hlasi dovolena. Nezavisle to po nasazeni
overila i druha instance (okno strategie-f6).

Kontrola zapisu: v dilku 0 vyskytu `_working?"none":"block"`, 0 vyskytu `var _working=`,
1 vyskyt `_tools.style.display="block"`. Bilance zavorek shodna se starym znenim.

## Dopad

Tyka se **vsech, kdo pouzivaji dochazku v mobilu** - pri praci nove vidi celou sadu dlazdic
(Dnesek, Tyden, Vyhled, Historie, Po zakazkach, Moje zadosti, Pozadat o opravu, Tady budu jinde,
Muj prehled, Moje podminky, Muj uvazek, Muj plan, Moje finance, Nepritomnosti).

**Ohlasene riziko** (Marti-AI, 1. 9. 2026, Jirka o nem vi): clovek ve vyrobe s otevrenym pracovnim
zaznamem muze dlazdici absence aktivovat omylem behem smeny. Jirka rozhodl vedome - pravni
pozadavek prevazuje.

_Souvisi:_ [[doc-dochazka-vedouci-ukazatel-cesty-k-vlastni-absenci]],
[[doc-dochazka-dlazdice-ke-schvaleni-misto-zeleneho-pruhu]]

