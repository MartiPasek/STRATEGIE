# Standard vzhledu přehledů (tabulek) — sloupec značek, křížek, výběr

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Standard vzhledu přehledů (tabulek) ve STRATEGII — jak mají vypadat

> Marti + Peťa, závazné pro VŠECHNY velké přehledy (Faktury, Pokladní doklady,
> Docházka po zakázkách…). Ať se to neřeší u každého přehledu znovu. Referenční
> vzor: `apps/api/static/pokladny.html` (`table.dokl`) a `platby.html` (`table.fakt`).
> Zapsáno 22.7.2026 (Peťa: „skutečně si to zapiš, ať to nemusíme řešit v každém přehledu").

## Krajní úzký sloupec značek (18–20 px) — ÚPLNĚ VLEVO, PŘED prvním sloupcem
Tohle je nejčastěji zapomínané. Ten sloupec plní DVĚ role:
- **V řádku filtru** (ne v hlavičce, ne „nahoře"): **✕**, které zruší **jen filtry
  sloupců** (na data ani šířku nemá vliv). Klik → vymaže všechna filtrovací okénka.
- **V datových řádcích: značky výběru** — **• (tečka)** u vybraných řádků,
  **▶ (šipka)** u řádku, na kterém uživatel naposledy stál (aktuální).
  Klik na řádek = přepnout výběr; **Shift+klik** = označit celý úsek. Vybraný řádek
  se navíc zvýrazní (modře). Buňky mají `padding:0`/`2px 0`, jinak se ✕/značka ořízne.
- U faktur tuhle roli plní sloupec se zaškrtávátky; ✕ ve filtru a ▶ u aktuálního řádku.

## Hlavička
- **Přilepená (sticky), tučná (700), bílá, tmavé pozadí `#1c2636`, modré podtržení
  2px `#34506f`.** Pozadí `top:0`.
- **BEZ velkých písmen** (Peťa 22.7.2026) — text nadpisů **klasicky: první velké,
  pak malé** (jak je zdroj). NEPOUŽÍVAT `text-transform:uppercase`. (Dřív standard
  velká písmena měl; 22.7. zrušeno u pokladen i faktur i docházky.)

## Filtrovací řádek
- **POD názvy sloupců** (ne nad), `<tr class="frow">` hned za `<tr>` s `<th>`.
- Oba řádky sticky: názvy `top:0`, filtry `top:<PŘESNÁ výška řádku názvů>` — offset
  se **liší per tabulka** (faktury 31px kvůli „vybrat vše", pokladny 25px). Změř
  `thead th`, nekopíruj naslepo, jinak vznikne mezera/překryv při rolování.
- **Filtrovací okénka černá, ohraničená** (pozadí `#0b0d10`, rámeček `#363b43`,
  světlý text; řádek filtrů `#08090c`) — ať jsou vidět jako samostatná okénka.
- **Filtr čísel bere čárku i tečku** — hodnotu i hledaný text normalizuj
  (odstraň mezery, `,`→`.`), ať „280,02" i „280.02" najde totéž.

## Tabulka, sloupce, šířky
- **Rámeček** kolem tabulky (1px `#2a3546`, radius 8px) + silnější stylované posuvníky.
- **Buňky:** jemné oddělovače, přetečení ořízni třemi tečkami (…), hover zvýraznění řádku.
- **Zaškrtávací (ano/ne) sloupce:** hlavička 1 písmeno (R/Ú/S/Z…) + tooltip s celým
  názvem, úzké.
- **Číselné sloupce** (Částka, Saldo, číslo…) zarovnané **doprava**, dost široké.
- **Roztahování sloupců** tažením za pravý okraj; kurzor **jednoduchá dvojšipka
  `ew-resize`** (žádný modrý proužek, NE `col-resize`); i `document.body.cursor` během
  tažení. **Dvojklik na okraj = zpět na výchozí šířku.**
- **Šířky: pevné VÝCHOZÍ pro všechny, tažení je DOČASNÉ** — po obnovení zpět na
  výchozí. **NEUKLÁDAT** do prohlížeče (localStorage). Výchozí šířky se mění v kódu.

## Po deploji
Ověř, že server SERVÍRUJE novou verzi (cache) — po nasazení tvrdý refresh (Ctrl+Shift+R).

## Kde je to použito
`pokladny.html`, `platby.html`, `dochazka-po-zakazkach.html` (Docházka po zakázkách —
vlastní stránka mimo framework grid právě kvůli tomuhle standardu + šířkám + ✕).


