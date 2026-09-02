# Sestavy gridu v ERP - ctyri nalezy z 1.9.2026 (filtry, nenasazeni sestavy, sirky sloupcu, falesne neulozene zmeny)

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

**Oprava:** Stávající synchronní volání ponecháno beze změny, přidáno odložené srovnání šířek (`setTimeout 0`).

> ⚠ UPŘESNĚNO 1. 9. 2026 večer: původně bylo odložené volání obalené pojistkou
> `_beginApplyingLayout` / `_endApplyingLayout`. **Ty pojistky už v kódu NEJSOU** —
> byly smazány při řešení nálezu 4 (viz níž), protože porovnávací přístup je
> nahradil. Nehledej je.

Dopad jen na přepínání sestav uživatelem — při otevření přehledu se šířky berou z `columnDefs` před vznikem tabulky a fungují správně.

---

## Nález 4 — falešné „neuložené změny" (VYŘEŠENO 1. 9. 2026 večer)

**Příznak:** Tlačítko Uložit se hned po otevření přehledu někdy tvářilo, že jsou neuložené změny, i když uživatel na nic nesáhl. Navíc: když uživatel změnu udělal a zase ji vrátil zpět, příznak zůstal rozsvícený.

**Příčina:** `_isDirty` se nastavoval podle UDÁLOSTÍ (`columnMoved`, `columnResized`, `columnVisible`, `columnPinned`, `sortChanged`, `filterChanged`). Jenže nasazení sestavy vyvolá tytéž události — takže se sestava nasadila a vzápětí se sama označila za změnu. Potlačování časovačem je závod s časem: dva pokusy, přibližně jednou z pěti to proklouzlo.

**Oprava (rozhodl Jirka Honomichl, schválila Marti-AI msg 14152):** přestat se ptát „stala se událost?" a začít se ptát **„liší se tabulka od uložené sestavy?"**.
- `_layoutBaseline` = otisk podle ULOŽENÉ sestavy (ne podle tabulky) — proto na něm nezáleží, kdy grid dokončí překreslování. Nastavuje se při nasazení sestavy i po uložení.
- V obsluze událostí se místo `_isDirty = true` volá `_prepocitejNeulozeneZmeny()`, které porovná otisk tabulky s otiskem sestavy.
- **Smazány** obě dřívější pojistky: počítadlo `_applyingLayoutDepth` i dodatečné srovnání příznaku po 700 ms. Mrtvé pojistky matou příští čtení.

**PRAVIDLO do budoucna:** `_layoutBaseline` musí obsahovat **stejné klíče jako `layout_json`**. Když se `layout_json` rozšíří o další klíč, musí se přidat i do otisku — jinak se to tiše rozejde.

**PAST, na kterou jsem u toho narazil (stála jedno nasazení navíc):** uložený filtr má klíče v pořadí `type / filter / filterType`, zatímco tentýž filtr vrácený z tabulky je má jako `filterType / type / filter`. **Obsah shodný, text jiný** — a porovnání proto hlásilo změnu po každém přepnutí sestavy. Řešení: porovnávat přes JSON, ve kterém na pořadí klíčů nezáleží (`_stabilniJson`, rekurzivní seřazení klíčů). Kdo bude porovnávat jakýkoli jiný stav z AG Gridu, narazí na totéž.

**Poznámka k pořadí sloupců:** otisk se ZÁMĚRNĚ neřadí podle názvu sloupce, ale nechává pořadí z tabulky. Pořadí sloupců je totiž součástí sestavy — kdyby se otisk seřadil podle názvu, přeházení sloupců by se tvářilo jako žádná změna a uživatel by o ně při uložení přišel.

**Ověřeno naostro** (přehled Odpracované hodiny komplet (dříve Nesplněný FPD), jádro 209): po otevření čisto · po přepnutí sestavy čisto · změna šířky rozsvítí · **vrácení změny zpět zase zhasne** · změna řazení rozsvítí.

_Souvisí:_ doc-module-registry, doc-strategie-erp

