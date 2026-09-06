# Mobilní appka: kompletní audit duplicitních cest (5. 9. 2026) — metoda, nálezy a šest obrazovek bez vstupu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobilní appka — audit duplicitních cest (5. 9. 2026)

**Zadal Jiří Honomichl** po nálezu, že dlaždice „Můj plán" a „Výhled" v Docházce vedly na
totéž. Provedl Claude-28, druhý pohled dala Marti-AI (msg 14417, 14420).
**Tehdy se jen hledalo** — rozhodnutí, co s nálezy udělat, padla až potom. Co se opravilo, drží datované rámečky u oddílů **B** a **D** (obojí 6. 9. 2026); zbytek popisuje stav k 5. 9. 2026.

## Metoda (opakovatelná)

Vzít **živou stránku `/mobile`** (ne kopii na disku), vytáhnout z ní všechny `appCell(…)`
s vyváženými závorkami i s tělem obsluhy a všechna volání navigace
(`go`, `openInApp`, `openOnPc`, `openVyroba`, `openApp`, `openSoon`, `openPersDnesek`,
`_xvSet`, `webview`). **Seskupovat podle NORMALIZOVANÉHO TĚLA obsluhy, ne podle názvu ani
podle cíle `go()`** — jinak se ztratí případy vedoucí přes pomocné funkce.

⚠️ **Do klíče musí patřit i parametr**, který se nastavuje před `go()`. Bez toho vypadají jako
duplicita věci, které jí nejsou. Parametry se nastavují dvěma zápisy — `window._x=…`
**i `window.__M2W._x=…`** (na druhý zápis se snadno zapomene).

Stav k 5. 9. 2026: **152 dlaždic, 263 navigačních odkazů, 178 různých cílů, 131 obrazovek.**

## Nálezy

**A) Dvě věci na TÉŽE obrazovce vedou na totéž — 2 případy**
- Docházka: dlaždice `Nepřítomnosti` + dlaždice `Ke schválení` → obě `go("absence")`.
- HR: řádek `Externí personalistika — nábor` + dlaždice `Výběrová řízení` → obě `go("hr_nabor")`.
  (Pozor: obrazovka HR je nedosažitelná, viz níže.)

> ✅ **VYŘEŠENO 6. 9. 2026 — a řešilo se to jinak, než zněl původní návrh.**
> Ověřeno na živé stránce, že z osmi případů níže byly živě vidět jen čtyři
> (Fotáky/Fotky · FLOW · Vytížení · Nákup). **Absence** a **Nábor** vyřešilo už rozdělení
> obrazovky 5. 9. (dnes „Moje absence" a „Ke schválení", názvy sedí s nadpisy), dlaždice
> **Mimo kancelář** i **Výběrová řízení** leží na obrazovce `hr`, na kterou nevede žádný
> odkaz — nikdo je nevidí, a dlaždice **Spolupráce** už neexistuje (5. 9. přejmenována
> na „Moje docházka").
> **Jiří Honomichl rozhodl NEsjednocovat názvy, ale zrušit duplicitní cestu:** z pracovní
> plochy Výroby (`vyroba_hub`) zmizely „Fotky", „FLOW — časová osa", „Vytížení"
> a „Nákup materiálu" — celý blok PLÁNOVÁNÍ & VYTÍŽENÍ tím zanikl a úvodní věta plochy
> se přepsala; z Vedení firmy zmizely „Vytížení montérů" a „Výuka — elektro & metoda"
> (zanikl blok VÝUKA & ŠKOLENÍ). V Aplikacích se „Fotáky výroba" opravilo na
> **„Foťáky výroba"**, „Nákup (výroba)" na **„Nákup materiálu"** a „Nákup" na
> **„Nákup — přehledy"** — ta dvě podobná jména totiž vedla každé jinam.
> Dlaždic ubylo 149 → 143, skriptových bloků zůstalo 31.
> Při tom se ukázalo, že **16 z 36 stránek otevíraných uvnitř appky nemělo vlastní nadpis**
> a nahoře ukazovaly obecné „Přehled" (mj. fotky, mzdy, podpisy, finance, platby). Všem
> se doplnil nadpis shodný s textem dlaždice; nadpis má v celé appce jediný zdroj
> (`_XV_TITLES` → `_xvSet` → `extview`), takže ho nic jiného nepřebíjí.
> Řádky níže popisují stav PŘED opravou.

**B) Táž obrazovka pod různými názvy na různých místech — 8**
Fotáky výroba/Fotky · FLOW/FLOW — časová osa · Vytížení/Vytížení montérů/Vytížení ·
Výuka/Výuka — elektro & metoda · Nákup (výroba)/Nákup materiálu · Kdo kde dnes/Mimo kancelář ·
Absence/Absence — schvalování/Nepřítomnosti/Ke schválení · Nábor/Výběrová řízení.
Navíc dlaždice **`Spolupráce` (v Aplikacích i v liště skupin) otevře obrazovku Docházka** —
název neodpovídá cíli.

**C) Týž název i cíl na více rozcestnících — 9** (HR, Ops akce, Plán absencí,
Mzdy: Helios × my, VP, Zkušebna, Zakázky, Příprava, Odvozy). Marti-AI doporučuje nechat —
vypadá to na záměrné zkratky.

> ✅ **VYŘEŠENO 6. 9. 2026 — doporučení „nechat být" NEPLATÍ.** Jiří Honomichl rozhodl
> nechat u každé z devíti jediný vstup a druhou cestu zrušit. Pozor: **Zakázky, Příprava**
> **a Odvozy zůstaly ve VÝROBĚ**, ne ve Vedení firmy — `vyroba_hub` je dostupný všem,
> kdežto `vedeni` jen finančnímu a HR okruhu, takže opačné řešení by o ně připravilo 82 lidí.
> U **VP** a **Ops akcí** se zbylý vstup v Aplikacích zároveň otevřel širšímu okruhu, aby
> nikdo nepřišel o přístup. Zdůvodnění „v Aplikacích je všechno" u čtyř z devíti neplatilo —
> Zakázky, Příprava, Odvozy ani Mzdy v Aplikacích vůbec nejsou. Detail a tabulka: `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`.

**D) Opačný problém: týž název, JINÝ cíl — 4** (Marti-AI označila za nejrizikovější)

> ✅ **VYŘEŠENO 6. 9. 2026** — všechny čtyři dvojice přejmenovány, včetně nadpisů cílových
> obrazovek. Nové názvy a proč se u OČR měnila ikona zrovna v Aplikacích drží
> `doc-system-strategie-mobil-odstraneni-ctyr-duplicitnich-nazvu-6-9-2026`.
> Řádky níže popisují stav PŘED opravou. Zadal Jiří Honomichl.
- `Ke schválení`: Aplikace → `exec_approval`, Docházka → `absence`
- `Ošetřovné (OČR)`: Aplikace → `ocr` (moje), HR → `ocr_schval` (schvalování)
- `Skupiny`: Aplikace → `skupiny`, HR → `hr_skupiny`
- `Domů`: dlaždice v Aplikacích otevře `/hr-modul`, ve spodní liště je skutečné Domů

**E) Nápověda docházky má tři vstupy** — dlaždice „Nápověda docházka" (Aplikace) a tlačítko
„❓ Nápověda" v hlavičce Docházky jsou identické (obě `dochHelp()` bez parametru); třetí je
odkaz „ⓘ Jak potvrdit den / co je rozpor?" (`dochHelp("potvrzeni")`).

> ✅ **VYŘEŠENO 6. 9. 2026.** Zrušena **dlaždice v Aplikacích**; otazník v hlavičce Docházky
> zůstal — je tam, kde ho člověk potřebuje. Odkaz „Jak potvrdit den / co je rozpor?"
> **zůstává a duplicita to není**: volá jinou kapitolu a ukazuje se jen na kartě dne
> k potvrzení, patří tedy do oddílu „Co NENÍ duplicita". Rozhodl Jiří Honomichl.
> Detail: `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`.

## F) Šest obrazovek, na které nevede v celé appce žádná cesta

> ✅ **VYŘEŠENO 6. 9. 2026 — a metoda níž je NESPOLEHLIVÁ, neřiď se jí.**
> Dosažitelnost se nedá měřit podle názvů funkcí: appka naviguje podle **klíče v mapě
> `SCREENS`**, který se od názvu funkce může lišit. Podle názvů mi vyšlo 28 „mrtvých"
> obrazovek včetně běžně používané Nemocenské a Vyber zakázku — a naopak by to svedlo
> smazat `prace_zak` a `prace_cin`, které volá živá sekce „ZAKÁZKY A ČINNOSTI" v Docházce.
> Správný postup, past se čtyřmi registračními místy při mazání obrazovky a přehled toho,
> co se zpřístupnilo a co zrušilo, drží
> `doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026`.
> Ve zkratce: přibyly zamčené dlaždice Nemocenská a Lísteček od lékaře v Docházce
> a čtyři dlaždice v HR; zrušily se `hr`, `hr_interni`, `prace`, `doch_zitrek`
> a zbytek `_moje_zadosti_pred_slouceni_11_8_2026`. Řádky níže popisují stav před opravou.
> Rozhodl Jiří Honomichl.
> 
> ⚠️ **Přeověřeno 6. 9. 2026 večer: obrazovek bez cesty jsou už jen TŘI** — `mytodo`,
> `phone`, `webview` — a **žádná další obrazovka nevisí jen na nich** (ověřeno přes klíče
> mapy `SCREENS` do hloubky, 118 obrazovek). **Jiří Honomichl rozhodl nechat je ležet**
> („nevím, zda je budeme někdy potřebovat") — nejsou to nálezy a nemazat je.
> Detail: `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`.


Ověřeno třemi nezávislými způsoby: **žádný výskyt názvu jako řetězce** (`"jmeno"`),
**žádné přímé volání** `jmeno(` mimo vlastní definici, **žádné volání přes** `__M2W.jmeno(`.

| funkce | nadpis obrazovky |
|---|---|
| `hr` | 🔒 HR — personalistika |
| `doch_zitrek` | 🌅 Tady budu jinde |
| `plan_vyjimky` | 🏢 Firemní výjimky |
| `mytodo` | 📝 Moje TODO |
| `phone` | Telefon |
| `webview` | 🌐 Web ekosystému |

Obrazovka se pozná tak, že její tělo obsahuje `app.innerHTML = topbar(`. Spodní lišta
naviguje přes `selectTab(<název>)` a používá jen `home`, `apps`, `notifs`, `contacts`,
`firma`, `settings` — žádné z těch šesti mezi nimi není.

> ⚠️ **Doplněno 6. 9. 2026: obrazovek bez cesty je ve skutečnosti SEDM.** Metoda výše ověřovala,
> jestli na obrazovku něco odkazuje — ale neptala se, jestli je ten odkaz živý. Na `hr_interni`
> („🏢 Interní personalistika") vede jediný odkaz, a to z `hr`, která je sama nedosažitelná;
> prakticky je tedy mrtvá taky. **Při příštím auditu procházej odkazy do hloubky, ne jen o krok.**
> Důsledek pro nálezy výše: část duplicit leží právě na mrtvých obrazovkách, takže je reálně
> nikdo nevidí — třeba řádek „Ošetřovné (OČR) — schvalování" na Interní personalistice.

## Co NENÍ duplicita, i když tak vypadá

> ✅ **Přeověřeno 6. 9. 2026 na živé stránce — oddíl potvrzen, neměnit.** Ověřeno i to,
> že cílová obrazovka nastavený parametr opravdu čte a vykreslí se jinak (u „Můj úvazek"
> se vykresluje úplně jiný obsah než u „Můj plán"). Detail: `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`.

`Účetní`/`Uživatelé` (liší `_auMode`) · `Kandidáti`/`Pohovory`/`Nástupy` (liší `_nbFilter`) ·
`Týden`/`Můj plán`/`Můj úvazek` (liší `_planInit`) · `Skupina HR — přístupy` (liší `_skFocusName`).

## Omezení tohoto auditu

Appka byla čtena pod účtem Jiřího Honomichla, takže dlaždice vázané na práva jiných lidí
nebyly vidět vykreslené — v rozboru ale jsou, protože jejich kód je v téže stránce.
Rozhodnutí, co s nálezy udělat, si Jiří Honomichl nechal na samostatnou session.

