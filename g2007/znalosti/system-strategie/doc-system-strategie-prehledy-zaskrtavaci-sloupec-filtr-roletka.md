# Zaškrtávací sloupec v přehledu má mít ve filtru roletku, ne klikací přepínač

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zaškrtávací sloupec = roletka ve filtru

> Zadala **Peťa Šafránková 25. 8. 2026**, provedl Claude-26. Platí pro **všechny přehledy**.

## Pravidlo

Sloupec, který nese **✓ nebo prázdno** (schváleno, doloženo, vyřízeno, zkontrolováno…),
musí mít ve filtračním řádku **rozbalovací seznam se třemi volbami**

- `–` = vše
- `✓` = jen zaškrtnuté
- `✗` = jen nezaškrtnuté

Peťa 25. 8. 2026 doslova — *„nemám jak vybrat, že chci vidět schválené a neschválené."*

## Proč roletka a ne klikací přepínač

Do 25. 8. 2026 se zaškrtávací sloupce filtrovaly **přepínačem** — klikáním dokola
(✓ → prázdné → vše). Dvě potíže

1. nebylo poznat, v jakém stavu filtr právě je
2. v úzkém sloupci (28 px) to vypadalo jako prázdné psací políčko, takže to nikdo nenašel

Na roletce je nastavení vidět na první pohled a dá se vybrat přímo.

## Jak se to zapojí

V definici sloupce musí být příznak **bool** s hodnotou 1, vedle šířky a zarovnání.
**Bez něj sloupec dostane obyčejné psací políčko a filtrovat prakticky nejde.**
Přesně tahle chyba byla ve Správě docházky u sloupce Schváleno — příznak tam chyběl,
zatímco sousední sloupec VedSchvaleno ho měl a fungoval.

Hodnoty filtru

- prázdný řetězec = vše
- `ano` = buňka obsahuje ✓
- `ne` = neobsahuje

Porovnání si buňku převede na `✓ano` nebo `ne`, takže pravidlo funguje i tam,
kde je ✓ součástí delšího textu.

## Na co nezapomenout

- Křížek **„zrušit filtry"** musí vyprázdnit **i roletky**, ne jen psací políčka.
- Vzhled roletky stejný jako u psacích políček — tmavé pozadí, neutrální rámeček.
- Roletka reaguje na **změnu hodnoty**, ne na kliknutí. Starý klikací přepínač se ruší,
  jinak by si obojí přepisovalo filtr navzájem.

## Kde to je hotové

Správa docházky, soubor `apps/api/static_db/dochazka-po-zakazkach.html` (g2007.soubor),
sloupec **Schváleno**. Do ostatních přehledů se doplňuje, kdykoli se v nich
na zaškrtávací sloupec sáhne.

Souvisí — pravidla tvorby přehledů drží `docs/team/Peta26_pokyny.md`,
oddíl o interakci přehledů (řazení, filtry, ukazatel).

