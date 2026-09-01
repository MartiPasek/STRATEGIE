# Datagrid sestavy tri nalezy 2026 09 01

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Tři opravené chyby v datagrid.js (sestavy gridu) — filtry, race condition onFirstDataRendered, šířky sloupců. Commit ee07eab9, 1. 9. 2026.**

# Datagrid — tři nálezy a opravy sestav (1. 9. 2026, commit ee07eab9)

Týká se `apps/api/static/erp/datagrid.js`, všech 98 tabulek v ERP.
Opravoval C-28 (Jirka Honomichl), schválila Marti-AI.

---

## Nález 1 — Filtry se do sestavy neukládaly vůbec

**Příznak:** Uložená sestava neobnovovala filtry při otevření přehledu.

**Příčina:** `saveAsLayout` (r. 3828) a `updateLayout` (r. 3863) sestavovaly `layout_json` výhradně z `columns`, `formatting_rules` a `heuristics_enabled`. Řetězce `getFilterModel` ani `setFilterModel` se v celém souboru nevyskytovaly.

**Oprava:**
- Do `layout_json` v `saveAsLayout` i `updateLayout` přidán `filter_model` z `getFilterModel`.
- V `_applyLayout` (r. 3610) se po aplikaci sloupců volá `setFilterModel`.
- Totéž v cestě přes `initialLayout` v `onFirstDataRendered` (~r. 3060), kde se `_applyLayout` záměrně nevolá.
- Přidána událost `filterChanged` do `_setupDirtyTracking` (r. 5389) — bez ní se tlačítko Uložit nerozsvítilo po změně filtru.

**Zpětná kompatibilita:** Staré sestavy bez klíče `filter_model` — při načtení se filtry vyčistí (`setFilterModel({})`) místo ponechání filtrů z předchozí sestavy. Záměrné rozhodnutí: sestava = celý pohled.

---

## Nález 2 — Uložená sestava se při otevření přehledu nasazovala jen někdy

**Příznak:** Při opakovaném otevření téhož přehledu se sestava (filtry, řazení, pořadí sloupců, barevná pravidla) nasadila jen někdy — ze čtyř pokusů jednou.

**Příčina:** Veškerá práce visela na události `onFirstDataRendered` (~r. 2896), která někdy vůbec nepřijde. Prokázáno měřením: po nenasazení sestavy byl `_lastFetchedAt` null, přestože `_currentLayoutId` i `options.initialLayout` měly správné hodnoty. Ruční zavolání `_applyLayout` sestavu nasadilo celou a bez chyby.

**Oprava:** Blok v `onFirstDataRendered` vytažen do samostatné metody `_applyInitialLayoutOnce()` s pojistkou (proběhne nejvýše jednou). Metoda se volá:
1. Z `onFirstDataRendered` jako dosud.
2. Ze záchranného časovače 500 ms po vzniku gridu, pokud dosud neprobě hla.

Stávající logika `_applyLayout` nezměněna (komentáře v kódu varují před problikáváním při přímém volání).

---

## Nález 3 — Šířky sloupců se při přepnutí sestavy nenasazovaly

**Příznak:** Přepínání mezi sestavami se správnými šířkami (např. 121 vs. 300) zanechávalo šířku na původní hodnotě (185) bez ohledu na uloženou hodnotu.

**Příčina:** V `_applyLayout` trojice operací: (1) `setGridOption("columnDefs", newDefs)`, (2) `applyColumnState`, (3) `setColumnWidths`. `setGridOption` s novými `columnDefs` přestavuje sloupce až po dokončení funkce a zahazuje šířky nastavené synchronně uvnitř. Ověřeno: `setColumnWidths` volané synchronně nemá účinek; totéž `setColumnWidths` odložené o jeden tik (`setTimeout 0`) funguje spolehlivě.

**Oprava:** Stávající synchronní volání ponecháno beze změny, přidáno odložené srovnání šířek (`setTimeout 0`) obalené pojistkou `_beginApplyingLayout/_endApplyingLayout` (zabrání falešným "neuloženým změnám" při přepínání).

Dopad jen na přepínání sestav uživatelem — při otevření přehledu se šířky berou z `columnDefs` před vznikem tabulky a fungují správně.

---

## Otevřené — falešné "neuložené změny" při otevření přehledu

Kosmetická vada, data se neztrácejí. Tlačítko Uložit se někdy tváří jako "jsou neuložené změny" hned po otevření přehledu, i když uživatel na nic nesáhl. Dva pokusy o potlačení časovačem — jednou z pěti to proklouzne. Správné řešení: porovnávat skutečný stav tabulky proti uložené sestavě místo naslouchání událostem. Čeká na Jirkovo rozhodnutí (hned nebo later).

_Souvisí:_ doc-module-registry, doc-strategie-erp

