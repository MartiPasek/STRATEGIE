# Standardní grid ERP (ErpDataGrid) na samostatné stránce mimo kostru ERP — postup a pět pastí

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Standardní grid ERP na samostatné stránce mimo kostru ERP

**Zapsal Claude-28 (Jirka Honomichl) 28. 8. 2026, schválila Marti-AI (msg 13941).**
Vzniklo při přestavbě přehledu dnů člověka v obrazovce **Opravy docházky**
(artefakt `apps/api/static_db/dochazka-opravy.html`), kde byla ručně kreslená
tabulka nahrazena komponentou `ErpDataGrid`. **Všech pět pastí níže je ověřeno
naostro v prohlížeči na živé stránce**, ne odvozeno z kódu.

## Kdy to použít

Některé obrazovky ERP nejsou postavené ze stavebnice (`fw.core` bez jediné
`fw.comp_def`) — jsou to samostatně psané HTML stránky, které jádro jen otevře.
Takové stránce chybí všechno, co běžné přehledy umí zdarma: filtrování po
sloupcích, řazení, export, skrývání a přesouvání sloupců, sestavy.
`ErpDataGrid` je ale **samostatně použitelná komponenta** — v hlavičce
`datagrid.js` stojí *„Multiple instances per page support"* — a jde ji zabudovat
i mimo kostru ERP.

Ověř si předem, že data už tečou standardním datovým zdrojem
(`fw.data_source` + `/api/v1/erp/data/{code}`). Pokud ano, mění se jen
vykreslování a zdroj dat zůstává beze změny.

## Co stránka musí načíst

Přesně tatáž sada, kterou načítá ERP (`modules/erp/api/router.py`, cca ř. 60903):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/styles/ag-grid.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/styles/ag-theme-quartz.css">
<link rel="stylesheet" href="/static/erp/datagrid.css">
<script src="https://cdn.jsdelivr.net/npm/ag-grid-enterprise@32/dist/ag-grid-enterprise.min.js"></script>
<script src="/static/ag_license.js"></script>
<script src="/static/erp/datagrid.js"></script>
```

- **`ag_license.js` nevynechávej** — komponenta klíč hledá jako
  `window.AG_GRID_LICENSE_KEY` a bez něj by AG Grid Enterprise vykreslil vodoznak.
  Kontrola naostro: `document.querySelector('.ag-watermark')` musí mít `display:none`.
- Vlož to **před vlastní `<style>` stránky**, aby vlastní styly vyhrály nad
  motivem gridu.
- `datagrid.js`, `datagrid.css` ani `ag_license.js` **nežijí v `g2007.soubor`** —
  jsou to běžné soubory v gitu, servírované z disku, takže je stránka jen odkazuje.

## Pět pastí (všechny ověřené naostro 28. 8. 2026)

### 1. Grid si PŘEPÍŠE výšku kontejneru — výška patří do voleb
`ErpDataGrid` při startu dělá `this.container.style.height = this.options.height`
(`datagrid.js` ř. 1813) a výchozí hodnota je `"100%"`. Když výšku dáš jen do
stylu kontejneru, komponenta ji zahodí; v rodiči bez určené výšky pak grid spadne
na `min-height` a **je vidět jediný řádek**.

- ✅ `new ErpDataGrid(box, { height: 'calc(100vh - 150px)', ... })`
- ❌ `box.style.height = ...` a doufat, že to vydrží

### 2. `opts.rowClassRules` se ignoruje — barvení řádků patří do sloupců
Komponenta si pravidla pro řádky pokaždé skládá sama
(`_buildEffectiveRowClassRules()` z heuristik a uživatelských formátovacích
pravidel) a to, co jí předáš ve volbách, **do AG Gridu nikdy nedojde**.

Řešení: dej pravidlo do `cellClassRules` v definici sloupců — `columnDefs`
jdou do AG Gridu beze změny. Jeden objekt s pravidlem a odkaž ho u každého sloupce.

### 3. Master-detail s asynchronním obsahem: `detailRowAutoHeight` měří prázdno
Když se obsah rozbaleného řádku dotahuje až po vykreslení (typicky se čeká na
data), automatické měření výšky ho změří **ještě prázdný** a detail se otevře
do výšky ~1 px. Vypadá to, jako by rozbalení nefungovalo.

Řešení: `detailRowAutoHeight` nepoužívat, místo toho
- `detailRowHeight: 420` jako počáteční hodnota (uživatel vidí otevřený řádek hned) a
- ve vykreslovači detailu `ResizeObserver`, který po doplnění obsahu zavolá
  `params.node.setRowHeight(h)` + `params.api.onRowHeightChanged()`;
  jako záloha pro prohlížeče bez `ResizeObserver` několik odložených dobrání
  (např. 250 / 900 / 2000 / 3500 ms). Ve `destroy()` sledovač odpoj.

### 4. Sestavy sloupců se zapnou jedině volbou `layoutKey`
Bez ní se lišta sestav vůbec nevykreslí. Tvar je `core_<id>` nebo `ds_<id>`
(`_layoutApiBase()` to kontroluje regulárním výrazem a jinak jen varuje do konzole).
Lišta se pak objeví **ve stavovém řádku dole u gridu**, ne nad ním —
„— bez sestavy —", 🎨 Pravidla, 💾 Uložit, + Uložit jako…

Před zápisem si ověř, že to jádro sestavy přijímá:
`GET /api/v1/erp/grid-layout/core_<id>/list` musí vrátit 200 a `ok: true`.

### 5. Vlastní položky do nabídky pravého tlačítka
Přes `customContextMenuItems` (pole nebo funkce dostávající `params`) — položky
se připojí za vestavěné (kopírovat, vložit, export). Označené řádky vytáhneš
přes `gridApi.getSelectedRows()`; když není označeno nic, použij
`params.node.data`.

## Jak to ověřit, že to opravdu funguje

Samotné nasazení nedokazuje nic. Ověřuje se v prohlížeči na živé stránce:
počet vykreslených řádků, počet filtrovacích políček, skutečné odfiltrování
(zadej filtr a zkontroluj, že zbyly jen odpovídající řádky), výška rozbaleného
detailu v pixelech, položka ve vlastní nabídce a **uložení sestavy včetně
následného smazání**, aby po zkoušce nic nezůstalo.

⚠️ **Past při zkoušení v prohlížeči:** nepojmenovávej pomocné proměnné `api` —
stránky mají vlastní globální pomocnou funkci `api()` pro volání serveru a
`var api = ...` ji přepíše. Projeví se to jako `TypeError: api is not a function`
u všech ostatních záložek a vypadá to jako zavlečená chyba, přitom je to
znečištění testem.

## Související

[[doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu]] ·
[[doc-dochazka-opravy-prehled-ui]]

