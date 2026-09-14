# Mobil: tlačítka a rozbalovací menu mají pozadí dlaždice a bílý text (14. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobil — tlačítka a rozbalovací menu mají pozadí dlaždice (14. 9. 2026)

**Rozhodl Jiří Honomichl 14. 9. 2026** (den po nasazení nového vzhledu „Modré světlo"), zapsal Claude-28.
Podnět: na osobní obrazovce měl `▶️ START` zelené pozadí s téměř černým textem a dlaždičky
Zakázka/Činnost byly skoro průhledné se šedým textem — tři různé podklady vedle sebe.

## Co od 14. 9. 2026 platí

Tlačítka a rozbalovací menu **uvnitř obrazovek** mají stejné pozadí jako dlaždice s ikonou
(třída `tile`, tedy modrý přechod nad `#1a2029`, rámeček `#313a4b`) a **vždy bílý text**.
Kontrast bílé na `#1a2029` je 14,8 : 1.

**Výjimky, které rozhodl Jiří Honomichl:**
- **spodní lišta, záložky v ní a šipka zpět** (`tabbtn`, `navbackbtn`, `back`) — beze změny;
  jsou to ovládací prvky aplikace, ne akce na obrazovce,
- **červené tlačítko u mazání a rušení** (třída `warn`) — zůstává červené jako výstraha,
- **oranžové blikání u nevybrané zakázky nebo činnosti** (třída `cin-pulse`) — má u sebe
  příznak `important`, takže si barvu drží; je to upozornění, ne akce.

**Kde to žije:** dílek `apps/api/static/mobile_parts/02_styles.html` (tabulka `g2007.soubor`),
blok úplně na konci pod hlavičkou `TLACITKA A ROZBALOVACI MENU MAJI POZADI DLAZDICE`.
Mění se v databázi a pak `@@G2007PUBLISH apps/api/static_db/mobile.html`.

## ⚠️ Gotcha 1 — „dám to na konec souboru" NESTAČÍ

Blok na konci souboru **nevyhrává automaticky**. Vyhrává pravidlo, které má **víc podmínek**,
a teprve při shodě rozhoduje pořadí. Ranní pravidlo pro hlavní tlačítka mělo šest podmínek
(`:root button:not(.ghost):not(.green):not(.warn):not(.sm):not(.tabbtn):not(.navbackbtn)`),
nový obecný zápis jen čtyři — takže **hlavní tlačítka („Uložit", „Ok") si dál kreslila
modrofialový přechod**, i když byl nový blok pod ním. Na snímku obrazovky to nebylo vidět,
protože ta tlačítka na testované obrazovce nebyla.

**Řešení, které je v souboru použité:** nový blok obsahuje **záměrně SHODNÝ selektor** se starším
pravidlem (plus vlastní obecný). Shodně silná pravidla rozhoduje pořadí → vyhraje to níž.
Alternativa `!important` se **nepoužila schválně** — přebila by i oranžové blikání, které
`important` používá právem.

## ⚠️ Gotcha 2 — 107 ze 450 tlačítek má barvu zapsanou přímo u sebe

Společné pravidlo ve stylech se k nim **nedostane** — barva zapsaná přímo u prvku je silnější.
Změřeno 14. 9. 2026 na živé stránce: **450 tlačítek, z toho 107 s vlastní barvou**, v rozpadu
(103 výskytů ve zdroji): modrá 30 · zelená 23 · šedá plocha 18 · průhledná 15 (většinou
**záložky uvnitř obrazovek** typu „📣 Novinky / 🗂 Agenda" na Firmě, a „Zrušit") · červená 10 ·
oranžová 4 (docházka: „✅ Konec", „⏱ Prodloužit") · fialová 3.

Nejvíc jich je v dílcích `48_hr_podminky_me.js` (18), `40_bakalari_ops_kara.js` (17),
`60_dochazka.js` (12), `47_hr_absence_ocr.js` (11), `50_skupiny_vyroba.js` (10).

**Stav k 14. 9. 2026: Jiří Honomichl rozhodl s nimi zatím nic nedělat.** Kdo je bude chtít
srovnat, musí počítat s tím, že plošné `!important` zasáhne i ty průhledné záložky
a červené „Zamítnout" — a to Jirka srovnat nechtěl.

## Jak se to ověřuje (ne snímkem obrazovky)

Na živé `/mobile` v prohlížeči vytvoř prvek dané třídy a přečti spočítané styly:
```js
const b=document.createElement('button'); b.className='green full';
document.body.appendChild(b); getComputedStyle(b).backgroundColor;
```
Snímek obrazovky dokáže jen to, co je zrovna vykreslené — a zakryté okno prohlížeče
se překreslovat přestane. Viz [[doc-system-strategie-mereni-v-prohlizeci-skryta-stranka-neprekresluje]].

## Související

- [[doc-system-strategie-mobil-vzhled-nasazeni-2026-09-14]] — nový vzhled „Modré světlo" a pasti z jeho nasazení
- [[doc-system-strategie-mobil-pojmenovane-barvy-a-struktura-stranky]] — pojmenované barvy a naměřené kontrasty
- [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]] — kde obsah aplikace žije a jak se publikuje

