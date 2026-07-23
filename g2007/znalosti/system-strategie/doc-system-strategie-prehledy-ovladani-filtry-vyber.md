# Přehledy — ovládání: datumový filtr a výběr řádků (STANDARD)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přehledy — ovládání: datumový filtr a výběr řádků (STANDARD)

> oblast: `system-strategie` · typ: standard · rozsah: VŠECHNY přehledy/tabulky STRATEGIE.
> Zavedla Peťa 23. 7. 2026. Vzor = **Přijaté faktury** (`platby.html`).

Závazné chování pro každý přehled/tabulku. Když stavíš nebo upravuješ přehled, drž se toho.

## 1) Výběr řádků myší — JEN Ctrl a Shift (jako Excel/Windows)
- **Prostý klik** řádek **NEOZNAČUJE** a **ZRUŠÍ dosavadní označení** — jen posune „aktuální řádek" (šipka ▶).
- **Ctrl+klik** (Cmd na Macu) = přepne označení jednoho řádku (• / modré zvýraznění).
- **Shift+klik** = označí celý úsek od aktuálního řádku.
- Označení slouží k akcím nad výběrem (např. „Sumace označených"). Klik do filtru/vstupu řádek NEvybírá
  (guard `closest('input,select,…')`).
- Implementace vzor: `dochazka-po-zakazkach.html` (tbody click handler, `SELSET`/`CUR` + inkrementální `paintRow`).

## 2) Datumový filtr OD/DO — VŠUDE, kde je v přehledu sloupec s datem
- Datumový sloupec má ve filtrovacím řádku **klikací** filtr (ne psací) → popup **„Výběr období"**:
  **Jeden den** (nastaví OD i DO stejně) / **Datum OD** / **Datum DO** + tlačítka **vymazat / zrušit / OK**.
- Vzor: `openSplatFilter` (`platby.html`, sloupec Splatnost). Přeneseno do `dochazka-po-zakazkach.html`
  (`openDateFilter`) a `pokladny.html` (`openDateFilterP`).
- Filtrování: datum řádku i meze převeď na číslo (`_dnum` z `DD.MM.YYYY`, `_inum` z `YYYY-MM-DD`) a porovnej
  rozsah; bere i datum s časem („23.07.2026 08:44"). Ukládá se jako `FIL[sloupec+'_od']`/`_do`, ✕ je maže.

## 3) Přesná shoda u ID sloupců
- Číselné ID sloupce (osobní číslo, druh činnosti, rok, měsíc…) filtruj **přesnou shodou**, ne „obsahuje"
  (aby „1" našlo jen 1, ne 105/126…). Desetinné (hodiny) nech na „obsahuje".

Souvisí s doc-system-strategie-prehledy-tabulky-standard (vzhled) a doc-system-strategie-prehledy-sirky-sloupcu (šířky).

