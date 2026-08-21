# Projekce znalosti v gitu se sama neobnovuje - jak ji srovnat (provedeno 20.8.2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Fakt, ktery je potreba znat
`@@G2007ADD` zapise znalost do DB a preindexuje vektory, ale **projekci do gitu (`g2007/znalosti/`) NEVOLA**. Kopie v gitu proto zaostava a nikde to nehlasi chybu.
**Zdroj pravdy je vzdy databaze.** Kopie na disku slouzi jen ke cteni historie a k diffum - znalost se z ni nesmi cist jako z pravdy.

## Doklad z 20.8.2026
Pred obnovou - v DB 472 aktivnich znalosti, v gitu jen **186** souboru. Vsechny ctyri znalosti zapsane ten den (rozpad v potvrzeni dne, deleni zaznamu, mapa, banner u Noskovy znalosti) v gitu **nebyly**.
Po obnove - v gitu **476** souboru vcetne vsech ctyr. Rozdil 286 znalosti byl nasbirany za tri tydny.

## Jak se to srovna
`GET /g2007/export?git=1` na app serveru (`apps/api/main.py`, funkce `export_g2007_docs` v `modules/conversation/application/composer.py`).
Chova se takto - vysype cely strom `g2007/` z DB (nastroje, kufry, entity, grafy, znalosti; 20.8. to bylo 658 souboru), pak `git add g2007` (**jen tuhle slozku, ne cely strom** - cizi rozdelanou praci tedy sebrat nemuze), commitne jen kdyz je co, `pull --rebase origin main` a `push`. Soubory jen prepisuje a pridava, **nic nemaze**.

## PAST, na kterou jsem 20.8. naletel
Prvni volani vratilo HTTP 200 a commit **probehl**, ale ja si vysledek neulozil. Druhe volani proto uz spravne hlasilo *"nic ke commitu (beze zmen)"* - a to vypadalo, jako by nastroj nefungoval. **Nespolehat na navratovku druheho behu; overit `git log` / `git ls-files g2007/znalosti | wc -l`.**

## Po obnove
Na svem stroji `git pull` (u Claudu pres `CLAUDE_PULL_GO.txt`). Commit je autorem app serveru ("Marti Pasek", zprava `g2007 export (generovano z DB)`) a rebasuje se na aktualni origin, takze cizi commity zustavaji - 20.8. se takto korektne srovnal i commit jineho sezeni z 06:41.

## Doporuceni
Spoustet po vetsi davce zapisu do G2007 (napr. na konci session), ne po kazde znalosti. Do te doby plati - **znalost cti z DB, ne ze souboru**.

