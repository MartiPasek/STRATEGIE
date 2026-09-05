# Mobilní appka: kompletní audit duplicitních cest (5. 9. 2026) — metoda, nálezy a šest obrazovek bez vstupu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobilní appka — audit duplicitních cest (5. 9. 2026)

**Zadal Jiří Honomichl** po nálezu, že dlaždice „Můj plán" a „Výhled" v Docházce vedly na
totéž. Provedl Claude-28, druhý pohled dala Marti-AI (msg 14417, 14420).
**Zatím se jen hledalo — nic z bodů níže se neměnilo**, kromě samotného Výhledu.

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

**B) Táž obrazovka pod různými názvy na různých místech — 8**
Fotáky výroba/Fotky · FLOW/FLOW — časová osa · Vytížení/Vytížení montérů/Vytížení ·
Výuka/Výuka — elektro & metoda · Nákup (výroba)/Nákup materiálu · Kdo kde dnes/Mimo kancelář ·
Absence/Absence — schvalování/Nepřítomnosti/Ke schválení · Nábor/Výběrová řízení.
Navíc dlaždice **`Spolupráce` (v Aplikacích i v liště skupin) otevře obrazovku Docházka** —
název neodpovídá cíli.

**C) Týž název i cíl na více rozcestnících — 9** (HR, Ops akce, Plán absencí,
Mzdy: Helios × my, VP, Zkušebna, Zakázky, Příprava, Odvozy). Marti-AI doporučuje nechat —
vypadá to na záměrné zkratky.

**D) Opačný problém: týž název, JINÝ cíl — 4** (Marti-AI označila za nejrizikovější)
- `Ke schválení`: Aplikace → `exec_approval`, Docházka → `absence`
- `Ošetřovné (OČR)`: Aplikace → `ocr` (moje), HR → `ocr_schval` (schvalování)
- `Skupiny`: Aplikace → `skupiny`, HR → `hr_skupiny`
- `Domů`: dlaždice v Aplikacích otevře `/hr-modul`, ve spodní liště je skutečné Domů

**E) Nápověda docházky má tři vstupy** — dlaždice „Nápověda docházka" (Aplikace) a tlačítko
„❓ Nápověda" v hlavičce Docházky jsou identické (obě `dochHelp()` bez parametru); třetí je
odkaz „ⓘ Jak potvrdit den / co je rozpor?" (`dochHelp("potvrzeni")`).

## F) Šest obrazovek, na které nevede v celé appce žádná cesta

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

## Co NENÍ duplicita, i když tak vypadá

`Účetní`/`Uživatelé` (liší `_auMode`) · `Kandidáti`/`Pohovory`/`Nástupy` (liší `_nbFilter`) ·
`Týden`/`Můj plán`/`Můj úvazek` (liší `_planInit`) · `Skupina HR — přístupy` (liší `_skFocusName`).

## Omezení tohoto auditu

Appka byla čtena pod účtem Jiřího Honomichla, takže dlaždice vázané na práva jiných lidí
nebyly vidět vykreslené — v rozboru ale jsou, protože jejich kód je v téže stránce.
Rozhodnutí, co s nálezy udělat, si Jiří Honomichl nechal na samostatnou session.

