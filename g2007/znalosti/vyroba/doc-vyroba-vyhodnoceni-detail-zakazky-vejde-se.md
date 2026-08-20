# Vyhodnoceni zakazek: detail zakazky - lista tlacitek pri rolovani mizela (opraveno 6.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Detail zakazky: lista tlacitek zustava videt

**Podnet Dusana Havlata 6. 8. 2026:** *"pri zobrazeni detailu radku z prehledu nevidi cele
okno detailu a nevidi horni panel s tlacitky."* Opraveno tyz den (commit `ffcc5fcb`).

## Co bylo spatne (zmereno v prohlizeci, ne odhadem)

| | pred | po |
|---|---|---|
| obsah detailu | 1 223 px | **1 053 px** |
| viditelna cast | 861 px | 807 px |
| **musi se odrolovat** | **362 px** | **246 px** |
| lista tlacitek | 85 px, **odrolovala pryc** | 69 px, **zustava videt** |

**Okno detailu samo pretekalo? NE** - dialog se prizpusobuje obrazovce a vejde se.
Problem byl jen uvnitr: obsah je vyssi nez okno, takze se roluje - a lista tlacitek
odrolovala nahoru pryc. Uzivatel u tabulek dole uz nevidel, cim ma pokracovat.

## Co se udelalo

1. **Lista tlacitek prilepena nahoru** (`position: sticky`) - pri rolovani zustava videt.
   To byla vlastni podstata stiznosti.
2. **Kompaktnejsi tlacitka** (mensi padding a pismo, `white-space: nowrap`) - 85 -> 69 px.
3. **Zmenseny obe tabulky** (`fw.comp_def.layout.height_px`): Hodnoceni vse 320 -> 240,
   Finalni vyhodnoceni 240 -> 150. Maji vlastni rolovani, takze se v nich nic neztrati -
   roluje se uvnitr tabulky misto celeho okna. Je to **konfigurace v DB, zadny deploy**.

## Co zbyva a proc jsem to nedodelal

Porad se roluje o **246 px**. Nejvetsi zbyvajici kus jsou dve sekce s poli - **Souhrn**
a **Pomocne vypocty**, kazda 233 px, pod sebou. Kdyby byly **vedle sebe**, uspori se
presne tech ~233 px a detail by se vesel cely.

**Neudelal jsem to**, protoze `layout_x` ani `layout_w` **nema nastaveny ani jeden z 26
groupboxu v cele databazi** - vedle sebe to zatim nedela zadna obrazovka. Byl by to
pokus naslepo na formulari, ve kterem Dusan prave pracuje. Az bude klid, da se to zkusit
- ale chce to nejdriv overit, jak framework layout groupboxu resi.

## Rozpad vysky detailu (pro pripadne dalsi ladeni)

lista 69 · Souhrn 233 · Pomocne vypocty 233 · Hodnoceni vse 296 · Finalni vyhodnoceni 206

