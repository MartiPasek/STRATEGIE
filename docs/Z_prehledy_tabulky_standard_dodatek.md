# Standard přehledů — dodatek 22.7.2026 (roztahování + sticky mezera)

Dvě věci, na které jsme narazili u „Docházka po zakázkách" a promítli i do pokladen/faktur:

## Roztahování sloupců přes <colgroup>/<col> + vodicí čára
- Šířky nastavuj přes **`<colgroup><col style="width:Npx">`** (jeden `<col>` na sloupec,
  vč. krajního sloupce značek), NE přes `style="width"` na `<th>` — u `table-layout:fixed`
  th-šířka spolehlivě nezabírá. Po změně nastav i **celkovou šířku tabulky** `table.style.width = součet`.
- **Roztahování při mnoha řádcích (14k+):** NEpřekresluj tabulku na každý pohyb myši — sekalo by to.
  Při `mousedown` na `.dgrip` ukaž **svislou vodicí čáru** (`position:fixed;width:2px;background:#2563eb`),
  na `mousemove` posouvej jen ji, a **šířku sloupce nastav až na `mouseup`** (jeden reflow). Plynulé.
- Dvojklik na `.dgrip` = zpět na výchozí šířku. Šířky se NEUKLÁDAJÍ (po refreshi výchozí).

## Sticky: mezera mezi hlavičkou a filtrem („prosvítání" při rolování)
- Hlavička (`top:0`) a filtrovací řádek (`top:<výška hlavičky>`) jsou dva samostatné sticky
  řádky → sub-pixel rounding mezi nimi občas nechá prosvítat 1px při rolování (měly to i pokladny/faktury).
- **Fix: filtr přisadit o 1px pod hlavičku (překryv).** `frow td` má `top = výška_hlavičky − 1`.
  U pokladen bylo `top:25px → 24px`, u faktur `top:31px → 30px`. U docházky se výška hlavičky
  měří v JS (`hrow.offsetHeight`) a `top = hh − 1`. Chová se to pak jako jeden pevně spjatý dvojřádek.
- Offset (výška hlavičky) se **liší per tabulka** — změř, nekopíruj naslepo.

## Sticky hlavička — gotcha
`thead th` nesmí mít dvakrát `position` (např. `position:sticky` + `position:relative`) — poslední
vyhrává a hlavička přestane být sticky (roluje pryč). Sticky sám o sobě stačí i jako containing
block pro absolutně poziconovaný `.dgrip`.
