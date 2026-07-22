# Standard vzhledu přehledů (tabulek) — recept + přesné hodnoty + gotchy

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Standard vzhledu přehledů (tabulek) ve STRATEGII — jak mají vypadat

> Marti + Peťa, ZÁVAZNÉ pro všechny velké přehledy. Peťa 22.7.2026: „poznamenej si to,
> ať příště řeknem náš standardní vzhled tabulek a udělá se to napoprvé." Referenční
> vzor = `apps/api/static/pokladny.html` (`table.dokl`) + `platby.html` (`table.fakt`).
> Nová stránka typu docházka po zakázkách = `apps/api/static/dochazka-po-zakazkach.html`.

## ⚡ Recept „udělej to napoprvé" (přesné hodnoty ke zkopírování z pokladny.html)
```css
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:8px 12px 6px;background:#0f1420;color:#e8edf6}
.tw{overflow:auto;max-height:calc(100vh - 52px);border:1px solid #2a3546;border-radius:8px;background:#0f1420}   /* okno až skoro dolů */
.tw::-webkit-scrollbar{width:13px;height:13px}
.tw::-webkit-scrollbar-track{background:#131b26}
.tw::-webkit-scrollbar-thumb{background:#33445c;border-radius:7px;border:2px solid #131b26}
table.dokl{table-layout:fixed;border-collapse:collapse;font-size:12.5px;width:auto}
table.dokl th,table.dokl td{border-right:1px solid #2a3546;border-bottom:1px solid #232c3b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:5px 8px}
table.dokl thead th{position:sticky;top:0;z-index:3;background:#1c2636;color:#ffffff;font-size:11px;font-weight:700;text-align:left;border-bottom:2px solid #34506f;position:relative}
table.dokl thead tr.frow td{position:sticky;top:25px;z-index:2;padding:3px 4px;background:#08090c;border-right:1px solid #24344f;border-bottom:1px solid #24344f}  /* top = PŘESNÁ výška th (~25px), změř! */
table.dokl tbody td{color:#f4f7fc}
table.dokl tbody tr{cursor:pointer}
table.dokl tbody tr:hover{background:#131d2b}
table.dokl th.r,table.dokl td.r{text-align:right}   /* číselné sloupce doprava */
table.dokl thead th .dgrip{position:absolute;top:0;right:0;width:7px;height:100%;cursor:ew-resize;z-index:5;user-select:none}  /* NE col-resize (modrý proužek) */
table.dokl .frow input{width:100%;box-sizing:border-box;padding:2px 6px;font-size:11px;border:1px solid #363b43;border-radius:4px;background:#0b0d10;color:#e9eef5}
```
- **Pozadí těla i .tw = `#0f1420`** (ne #0f141a — jinak je vidět barevný rozdíl).
- **Filtrovací okénka: BEZ placeholderu** (žádné „…"). Prostě `<input data-k="...">`.
- **Šířky sloupců** = pevné VÝCHOZÍ v kódu (pole COLS `{k,h,w,r,...}`); tažení za `.dgrip`
  je DOČASNÉ, dvojklik = zpět na výchozí; **NEUKLÁDAT** do localStorage.
- **Filtr čísel bere čárku i tečku**: normalizuj hodnotu i dotaz (odstraň mezery, `,`→`.`).

## Krajní úzký sloupec značek (18–20 px) — ÚPLNĚ VLEVO, PŘED prvním sloupcem
- **V řádku filtru** (frow, ne v hlavičce): **✕** které zruší **jen filtry sloupců**
  (`onclick` → vymaže všechna okénka). NE nahoře, NE v hlavičce.
- **V datových řádcích: značky výběru** — **•** u vybraných, **▶** u aktuálního (naposledy
  kl_iknutého) řádku. Klik = přepnout výběr, **Shift+klik** = úsek, vybraný řádek modře.
- Buňky sloupce mají `padding:2px 0;text-align:center`, jinak se ✕/značka ořízne.

## Hlavička
- Sticky, tučná (700), bílá, pozadí `#1c2636`, modré podtržení 2px `#34506f`.
- **BEZ velkých písmen** (Peťa 22.7.2026) — nadpisy klasicky první velké, pak malé.
  NIKDY `text-transform:uppercase` (zrušeno i v pokladny.html + platby.html 22.7.).

## Filtrovací řádek POD názvy (ne nad)
`<thead>`: nejdřív `<tr>` s `<th>`, pod ním `<tr class="frow">`. Oba sticky: názvy `top:0`,
filtry `top:<výška th>` — offset se **liší per tabulka** (faktury 31px, pokladny/docházka 25px),
změř, jinak mezera/překryv při rolování.

## ⚠️ Gotchy (na tyhle jsme 22.7. narazili — příště rovnou)
- **Framework grid vs vlastní stránka:** když jádro (`fw.core`) MÁ napojený data_source
  grid, `page_render.dispatchPageRender` vykreslí framework AG-grid (tečky ⋮ + „Hledat ve
  všech sloupcích") a k iframe se NEDOSTANE. Iframe hook vlastní stránky proto musí být
  **na ZAČÁTKU `dispatchPageRender`** (před fetchem page-spec), gated na `coreCode` —
  NE v `_renderDraftedPlaceholder` (ta cesta běží jen pro jádra BEZ rootu).
- **Endpoint musí serializovat Decimal/date do JSON** — `numeric` z PG přijde jako
  `Decimal` → `JSONResponse` spadne „Object of type Decimal is not JSON serializable".
  Převeď: `float(v) if isinstance(v,Decimal)`, `v.isoformat()` pro date/datetime.
- **Jeden zdroj pravdy:** endpoint bere SQL z `fw.data_set` (`SELECT sql_text ... WHERE code=`)
  a spustí ho — sloupce/logika zůstávají v data_setu, stránka jen renderuje.
- **Po deploji tvrdý refresh (Ctrl+Shift+R)** — `page_render.js` se cachuje; zavření/otevření
  záložky nestačí, servíruje se stará verze (doctrine „OS restart > revert").
- XFO/CSP hlavičky na route stránky (`X-Frame-Options: SAMEORIGIN`), jinak se v ERP iframe
  nenačte (globální middleware dává DENY).

## Kde je použito
`pokladny.html`, `platby.html`, `dochazka-po-zakazkach.html`.


