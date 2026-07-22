# Standard přehledů — šířky sloupců (jednorázové, sdílené vychozi spravuje Claude)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Standard přehledů — šířky sloupců: chování (dodatek 22.7.2026)

Závazné pravidlo (Peťa 22.7.2026), doplňuje standard vzhledu přehledů:

## Tažení sloupce = VŽDY jen jednorázové
- Uživatel si může sloupec roztáhnout tažením za pravý okraj, ale **po obnovení stránky
  (odchod/příchod) se vše vrátí na ZÁKLADNÍ nastavení.** Platí pro KAŽDÉHO — i pro Peťu
  a rodiče. **Žádné ukládání osobních šířek** (žádný localStorage per-uživatel).
- Dvojklik na okraj = zpět na základní šířku (taky jen vizuálně).

## Základní (sdílené) šířky pro všechny
- Změní se **jen když to někdo výslovně vyžádá** — nastaví je **Claude**, ne uživatel.
- **ŽÁDNÉ tlačítko „uložit šířky jako výchozí" na stránce** (Peťa to výslovně nechce —
  „proste bychom to zase řešili s tebou").
- Kam: do kódu (pole `COLS` / `DCOLW_DEF` / `_faktColDef`), NEBO do DB tabulky
  **`tenant.att_ui_pref`** (jsonb, kod `dochazka_col_widths`). Výhoda DB varianty:
  Claude ji změní přes SQL most **bez deploye** a projeví se všem hned po refreshi.
  Stránka čte přes `GET /app/dochazka-zak-tab/widths` (jen povolení uživatelé; POST endpoint
  existuje, ale z UI se nevolá — psát smí rodiče/Peťa, nastavuje to Claude).

## Proč tak
Osobní „zapamatování" (localStorage) vede k tomu, že každý má jiné šířky a nedá se to
centrálně řídit; navíc se do toho nedá „koukat" (server to nevidí). Model = jedny sdílené
základní šířky (spravuje Claude na vyžádání) + dočasné jednorázové tažení pro každého.


