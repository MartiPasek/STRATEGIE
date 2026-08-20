# Vyhodnoceni zakazek: hodnotici pole (flexibilita, chybovost, estetika) jsou MRTVA - overeno v Centrale

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hodnotici pole flexibilita / chybovost / estetika jsou mrtva

**Overeno 5. 8. 2026** (C28/Jirka) primo v Centrale (DB_EC), na dotaz Jirky, jaka je stupnice.

## Zjisteni: stupnice NIKDE NENI, protoze se pole nikdy nepouzila

| co jsem hledal | vysledek |
|---|---|
| hodnoty v datech `EC_TempVyhodnoceniZak` | **vsech 15 316 radku ma 1** u vsech tri poli |
| tyz stav u nas (`ec.vyhodnoceni_osoba`) | vsech 15 306 radku ma 1 |
| vychozi hodnota sloupcu | `((1))` |
| kontrolni omezeni (CHECK) na tabulce | **0** |
| ciselnik / prevodni tabulka | **zadna** |
| procedury, pohledy, funkce zminujici tato pole | **0 objektu v cele DB_EC** |
| typ sloupce | `tinyint` (tedy technicky 0-255) |

**V cele databazi Centraly na tyto tri sloupce nesaha ani jeden kus kodu.** Nic s nimi
nepocita, nic je nevaliduje, nikdo je nikdy nevyplnil - jsou jen vychozi jednicka.

## Co z toho plyne

Stupnice bud existuje pouze ve **formulari Centraly (Delphi)**, do ktereho z DB nevidime,
nebo nikdy nevznikla a pole zustala jako nedodelek. **Z dat se odvodit neda.**

Prakticky: hodnoceni kvality **neni co migrovat** - neni tam zadna historie ani pravidlo.
Kdyz se ma pouzivat, je to **nova funkce**, ne prevzeti stare, a stupnici musi urcit
**Dusan** (vedouci vyroby).

## Dopad na ukladaci skript

`g2007.python` kod `vyhodnoceni_osoba_uloz` proto hlida jen rozsah `0-255` (rozsah
puvodniho typu). Az Dusan stupnici urci, doplnit spravnou kontrolu.

Realne vyplnovana jsou u hodnoceni jen **poznamky** (VV / VP / sefmonter) - ma je 1 867 radku.

