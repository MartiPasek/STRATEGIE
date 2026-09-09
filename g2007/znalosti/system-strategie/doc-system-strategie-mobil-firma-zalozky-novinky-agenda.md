# Mobil, obrazovka Firma: dvě záložky (Novinky + Agenda) a zrušený vodorovný pruh skupin (8. 9. 2026; večer sekce podle nadrazéných složek)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> ## ⚠️ 8. 9. 2026: „Můj přehled" už neexistuje a sekce se přejmenovala
>
> Obrazovka **„Můj přehled"** se 8. 9. 2026 rozdělila na **„Moje hodiny"** (odpracované hodiny
> za měsíc) a **„Moje volno"** (nárok a čerpání dovolené a sick days). Sekce, ve které dlaždice
> sedí, se přejmenovala z **„PODMÍNKY & FINANCE"** na **„MOJE PŘEHLEDY"**. Výpočet ani zdroj dat
> se nezměnily, dělilo se 1:1.
>
> **Věty níž, které používají staré názvy, čti jako popis stavu do 8. 9. 2026.**
> Zadal Jiří Honomichl. Detail: [[doc-dochazka-mobil-dochazka-hlavicka-sekce-rozdeleni-8-9-2026]].

> ## ⚠️ DOPLNENO 8. 9. 2026 VECER — mrizka uz NENI plocha, agendy jsou v SEKCICH
>
> Text nize popisuje stav z dopoledne 8. 9. 2026. Tyz den vecer zadal Jirka Honomichl
> zmenu (schvalila Marti-AI, msg 15014): **nadrazene slozky se uz nekresli jako dlazdice**
> — delaji **nadpis sekce** nad svymi agendami. Duvod: slozky KANCELAŘE, VÝROBA
> a EXTERNÍ (v `tenant.staff_group` na ne ukazuje `parent_id` ostatnich skupin) nemaji
> vlastni cleny, takze v ploche mrizce vypadaly jako obycejna agenda s nula lidmi
> — vedle sebe byly **dve „Výroba“** a lide se ptali, proc jedna nema nikoho.
>
> **Co plati od vecera 8. 9. 2026:** nahore samostatna dlazdice „🌐 Všichni“, pod ni sekce
> **Kanceláře / Výroba / Externí** a sekce **Ostatní** pro agendy bez nadrazene slozky
> (dnes DOCHÁZKA - OPRAVY a DOCHÁZKA - SCHVALOVÁNÍ VŠECH). **Poradi uvnitr sekce
> zustava** takove, jak ho popisuje text nize — nejdriv moje agendy se zelenou teckou.
> Pocet u zalozky uz **nepocita nadrazene slozky** (19 → 16).
> Detail: [[doc-system-strategie-agendy-zdroj-staff-group-a-nadrazene-slozky]].

## Co se změnilo

Obrazovka **Firma** v mobilní aplikaci má od 8. 9. 2026 **dvě záložky**:

1. **📣 Novinky** — výchozí po každém otevření Firmy (nepamatuje si poslední záložku).
   Obsah kreslí funkce `_mojeNovinky` z dílku `48_hr_podminky_me.js`. Do 8. 9. seděly Novinky
   na konci obrazovky „Můj přehled“ (Šárčin nákres) — odtud jsou **přesunuty**, ne zkopírovány.
2. **🗂 Agenda** *(u záložky je počet; dopoledne 8. 9. bylo 19, od večera 16 — nadrazéné složky se nepočítají)* — mřížka 4 sloupců se skupinami, **od večera 8. 9. rozdělená do sekcí** (viz rámeček nahoře). Do 8. 9. to byl
   **vodorovný pruh nad spodní lištou** (`bnavx2`, plnila ho `skupBar()`); **ten je zrušen**.

**Pořadí dlaždic je záměrně OPAČNÉ než mělo pruh** (od večera 8. 9. platí **uvnitř každé sekce**, ne přes celou mřížku)**:** nejdřív skupiny, kde je člověk člen,
zástupce nebo vedoucí (poznají se **zelenou tečkou**), pak „🌐 Všichni“, pak ostatní. Pruh řadil
vzestupně podle `rank`, tedy „moje“ až na konci. Mřížka řadí podle toho, co je pro člověka
podstatné.

**Klik na dlaždici dělá totéž co dřív pruh** — `openSkup(id, name, icon)`, tedy konzole skupiny
(lidé + stavy). Na tom se 8. 9. nic neměnilo.

## Kde to žije

| Co | Kde |
|---|---|
| Záložky a přepínání | `51_skupiny_sdileny.js`, funkce `firma()` |
| Mřížka agend | `70_tail.js`, funkce `_firmaAgenda(cont)` + `_firmaAgendaLoad`, `_firmaAgendaPocet` |
| Novinky | `48_hr_podminky_me.js`, `_mojeNovinky(cont, bezNadpisu)` |
| Skrytí pruhu | `74_claude27_render_init.js` — větev `if(firmaBar){…}` nahrazena trvalým skrytím |

Data mřížky: `GET /api/v1/erp/app/skupiny/bar` → `{groups:[{id,name,icon,rel,parent_id,je_slozka}]}`, kde `rel` je
`lead` / `deputy` / `member` / `other`. Pole `parent_id` a `je_slozka` přibyla **8. 9. 2026 večer** kvůli sekcím (`je_slozka` = na skupinu ukazuje `parent_id` jiné nearchivované skupiny). Adresu **nevolá nic jiného než mobil** — ověřeno v gitu i v `g2007.soubor` 8. 9. 2026. Sdílí se **stejná mezipaměť** `_skupBarCache`, co měl pruh.

## Na co si dát pozor

- **Dílky jsou samostatné IIFE**, navzájem si do sebe nevidí — proto jsou `_firmaAgenda`,
  `_firmaAgendaLoad` i `_firmaAgendaPocet` registrované na `window.__M2W`. Bez registrace
  spadne volání z dílku 51. Viz [[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]].
- **`startAnimIcons()` se musí volat až PO vykreslení dlaždic** (upozornila Marti-AI), jinak
  animovaná ikona „Vedení“ (tři snímky) naskočí až při dalším překreslení.
- **Počet u záložky Agenda je živý.** Když seznam skupin ještě není načtený, ukáže se záložka
  bez čísla a po dotažení se překreslí — jen když se počet opravdu změnil.
- **`skupBar()` v `70_tail.js` zůstala v kódu, ale už ji NIKDO nevolá.** Je předregistrovaná
  přes `mkWrap()` v `10_core.js` a importovaná v dílku 73; to samo o sobě nic nespouští.
- **Zrušením pruhu spadla výška spodní lišty ze 122 na ~61 px** — dopočítá si to `_syncNavH()`
  samo, obrazovky počítající `calc(100vh - var(--navh))` tím získaly místo.

## Popisky dlaždic

Dlaždice je úzká (4 sloupce), proto `_agLabel(name)`:

- názvy psané **celé velkými písmeny a delší než 3 znaky** (KANCELÁŘE, VÝROBA, EXTERNÍ) se
  zobrazí s malými písmeny; zkratky do 3 znaků (VP, HR, IT, PLC) zůstávají velké,
- dva dlouhé názvy mají krátký popisek podle **mapy podle názvu**:
  `DOCHÁZKA - SCHVALOVÁNÍ VŠECH` → „Docházka — schvalování“, `DOCHÁZKA - OPRAVY` → „Docházka — opravy“.

⚠️ **Když někdo skupinu přejmenuje, mapa přestane sedět a ukáže se plný název** — tedy bezpečné
selhání, ne špatný popisek. **Uvnitř agendy je vždy plný název ze systému.**

⚠️ **Otevřený rozpor (nahlášen 8. 9. 2026):** znalost
[[doc-dochazka-mobil-muj-prehled-podle-nakresu]] má u profesí rozhodnutí Marti-AI (msg 13898),
že **verzálky se nepřepisují v kódu**, protože by ze zkratky „PLC“ udělaly „Plc“, a že se to má
řešit vizuálně (`text-transform:lowercase` + `font-variant:small-caps`). Tady je to udělané
v kódu s pojistkou na délku názvu. Jde o jiné místo (skupiny vs. profese), ale je to tatáž
třída rozhodnutí. **Nahlášeno Marti-AI (msg 14992) a její odpověď: rozdíl je záměrný
a má zůstat.** Zdůvodnění: profese jsou **zkratky** (VP, HR, PLC) — tam by přepis v kódu udělal
z „PLC“ nesmyslné „Plc“, proto CSS. Názvy skupin jsou **plná slova** uložená v databázi verzálkami
(KANCELÁŘE, DOCHÁZKA) — tam je přepis normalizace dat pro čitelnost, ne stylování zkratky, a `small-caps`
by z toho udělalo kapitálky místo přirozeného titulku. Jsou to dvě různé třídy problému.
**Konečné slovo má Jirka Honomichl** — do té doby zůstává stávající řešení.

## Kdo zadal a jak to bylo ověřeno

Zadal Jirka Honomichl 8. 9. 2026 (nejdřív návrh obrazovky, pak výběr rozvržení), schválila
Marti-AI: msg 14947 (přesun Novinek), 14962 (smazání věty „Firemní rozcestník — připravujeme“),
14986 (záložky a zrušení pruhu).

Ověřeno: každý zásah cíleným zápisem **s pojistkou na otisk** (do dílku 60 týž den zapisovala
i Claude-26), po zápisu přečteno z databáze, po `@@G2007PUBLISH` ověřeno, že stránka ze serveru
novou podobu opravdu obsahuje, a nakonec **proklikáno v prohlížeči na živé `/mobile`**: obě
záložky, výchozí Novinky, 19 dlaždic, klik na „Finance“ otevřel tutéž konzoli skupiny jako dřív
pruh, spodní lišta 61 px, žádná chyba v konzoli prohlížeče.

⚠️ **Neověřené pozorování:** po dvou z publikací vracel server ~3 minuty **starší** podobu
stránky (i po tvrdém načtení, přitom `/api/v1/health` hlásil `primary`), pak se to samo
srovnalo. Příčina nezjištěna — Jirka rozhodl to zatím neřešit. Prakticky to znamená, že se
změna nemusí v telefonu objevit okamžitě.

