# Přehledy (grid) — interakční standard: řazení, filtry, ukazatel výběru

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přehledy (grid) — interakční standard: řazení, filtry, ukazatel výběru

> Zapsal Claude-26 (Peťa) 29. 7. 2026, doplněno 30. 7. 2026. Závazné pro VŠECHNY velké přehledy STRATEGIE
> i pro každý nově vytvořený. Referenční implementace: `apps/api/static/dochazka-po-zakazkach.html`
> (Docházka new / Správa docházky), `pokladny.html` (Pokladní doklady), `platby.html` (Přijaté faktury),
> `dochazka-kontrola.html` (Kontrolní přehledy). Vzhled tabulek (rámeček, sticky hlavička, šířky sloupců,
> datumový filtr) řeší samostatná pravidla — tohle je o INTERAKCI.

## Ukazatel u počtu řádků
„Řádků: X (z Y) · **vybráno: N**" — X = po filtru, Y = celkem, N = počet označených řádků. Aktualizuje se **živě** při změně výběru (ne jen při překreslení). U pokladen/faktur je dole pod tabulkou, u docházky nahoře u chipů (element `#info`).

## Řazení klikem na název sloupce
- 1. klik = **vzestupně** (šipka ▲ v hlavičce), 2. klik na tentýž = **sestupně** (▼), 3. klik = **zpět na výchozí** (pořadí dle datasetu).
- Klik na **úchyt šířky** sloupce (`dgrip`/`colgrip`) NEŘADÍ — guard v handleru.
- Porovnání podle **typu sloupce**: číslo (parse, čárka/tečka), datum (`_dnum`/`_inum`), ✓/bool, jinak text (`localeCompare 'cs'`). Řadí se **vyfiltrované** pole; u faktur přes `list.slice().sort()` (nemutovat zdrojové `_faktury`).
- Stav: `SORT{k,dir}` (resp. `DSORT`, `FSORT`). Klik na hlavičku = delegovaný listener na `thead` na řádek s názvy (`tr:first-child th[data-sk]`).
- **Zelené tlačítko „↺ výchozí řazení"** u počtu, zobrazí se jen když je seřazeno.

## Filtr sloupce — pravý klik do filtračního políčka
Pravý klik (`contextmenu`) do filtračního políčka = **pop-up menu**: „Jen prázdné · Jen neprázdné · Smaž · Vlastní…". Levý klik / psaní = klasický filtr „obsahuje" (beze změny). **Žádná šipka/roletka.**
- „Prázdné" = hodnota null / false / prázdný řetězec.
- Psaní do políčka režim prázdné/neprázdné zruší. Stav: `FILMODE` (resp. `DFILMODE`, `_fMode`).
- ✕ „zrušit filtry" maže i tyto režimy i vlastní filtr.

## Filtr BEZ diakritiky (Peťa 29.7.2026)
Textové filtry (psací i „Vlastní") **ignorují diakritiku** — „kroner" najde „Króner", „prace" najde „Práce". Normalizuje se **obě strany** porovnání helperem `_norm(s){ return String(s).toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu,''); }` (malá písmena + odstranění háčků/čárek). U čísel navíc čárka→tečka. Platí ve všech přehledech.

## Vlastní filtr (spodní panel „Vlastní…")
Víc podmínek na sloupce, operátory **Obsahuje / Neobsahuje / Rovná se / Nerovná se**, spojené **A / NEBO** („+ přidat podmínku"). **Filtruje ŽIVĚ — bez OK** (aplikuje se hned při vyplnění/změně hodnoty i při přidání/odebrání podmínky). Panel má jen **Zavřít** a **Smazat vše**. Prázdná hodnota podmínku ignoruje. Aktivní filtr = zelený indikátor „⚙ vlastní filtr (N)" u počtu (klik = upravit, ✕ = zrušit). Stav: `VFILT` (pole `{join:'and'|'or'|null, k, op:'has'|'nhas'|'eq'|'ne', val}`), vyhodnocení zleva doprava (A=AND, NEBO=OR), první podmínka bez spojky. Porovnání přes `_norm` (bez diakritiky).

## Výběr řádků (jako Přijaté faktury)
Prostý klik NEoznačuje — jen posune „aktuální řádek" (▶). **Ctrl+klik** přepne jeden řádek (• / modré), **Shift+klik** označí úsek od aktuálního. Klik do filtru/vstupu řádek nevybírá.

## Kopírování buňky přes Ctrl+C (Peta 30.7.2026)
Jako v Centrále: **klik do buňky ji označí** (výrazný rámeček `td.cellact`) a **Ctrl+C zkopíruje celý text té buňky** (bez tažení myší). Implementace = univerzální samostatný blok (IIFE na konci stránky, guard `window.__cellCopyInit`), který si sám vloží `<style>` a naváže dva delegované listenery na `document`:
- **click**: `e.target.closest('td')`; bere jen buňky v tabulce třídy **`dokl` / `fakt` / `sumtab`**; přeskočí buňku značek (`.mk`), „Načítám" (`.ld`) a buňky se vstupem (`input/select/button` = řádek filtru). Označí buňku (`td.cellact`), předchozí odznačí.
- **keydown Ctrl/Cmd+C**: když je fokus v `INPUT/TEXTAREA/SELECT` NEBO je ručně označený text (`window.getSelection`), nechá **nativní** chování. Jinak zkopíruje `td.textContent` (trim; fallback atribut `title`) přes `navigator.clipboard.writeText` (fallback skrytá `textarea` + `execCommand('copy')`) a buňku krátce probliskne (`td.cellcopied`, 350 ms).

Styl: `td.cellact{outline:2px solid #4a9eff;outline-offset:-2px} td.cellcopied{background:rgba(74,158,255,.45)!important}`. Blok je identický ve všech čtyřech přehledech; při plném překreslení tabulky se `cellact` přirozeně ztratí (nevadí).

## Barvy
Tlačítka „výchozí řazení" a „vlastní filtr": zelená `background:#0f2a22; color:#4fe0aa; border:1px solid #2dd4bf`.

## Pravidlo
Kdykoli stavíš nový přehled (nebo upravuješ stávající), přidej tam **všechny** tyto interakce (řazení, filtry, filtr bez diakritiky, ukazatel výběru, výběr řádků, kopírování buňky přes Ctrl+C) — ať se přehledy chovají jednotně (uživatelé to znají z Centrály).

