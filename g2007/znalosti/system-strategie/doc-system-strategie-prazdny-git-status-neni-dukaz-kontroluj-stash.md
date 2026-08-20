# Prazdny git status NENI dukaz, ze se nic neztrací - autostash z pullu drzi zmeny mimo dohled (17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se stalo

17. 8. 2026 jsem na Jirkove stroji (`C:\projekty\STRATEGIE`) na konec session overoval, ze je vse zacommitovane. `git status` byl **prazdny**, `HEAD == origin/main`, `LOCAL_STATUS.txt` hlasil "LOKAL AKTUALNI". Podle vsech obvyklych kontrol bylo cisto.

`git stash list` ale mel **dve polozky, oba `autostash` z 5. 8. 2026** - tedy 12 dni stare.

## Proc to vznika

Pull pres most dela `git pull --rebase --autostash` (a stejne tak deploy protokol). Autostash rozpracovane zmeny **odlozi, aby rebase prosel - a zpatky uz je nevrati**, kdyz rebase skonci necekane. Ta zmena pak **existuje, ale nikde ji nevidis**: `git status` je prazdny, protoze v pracovni kopii uz nic neni.

Je to stejny mechanismus, kterym Jirkovi jednou visela dokumentace **11 dni** necommitnuta - pull ji jen porad odkladal.

## Zavazne pravidlo na konec session

**`git status` prazdny NENI dukaz, ze se nic neztraci. Vzdy zkontroluj i `git stash list`.**

Kdyz tam neco je, **NEMAZAT** - nejdriv zjisti, co v tom je, a rozhodnuti nech na cloveku:

1. `git log -1 --format="%ci  %s" "stash@{N}"` - jak je to stare.
2. `git stash show --stat "stash@{N}"` - ktere soubory.
3. **Porovnej odlozenou verzi s dnesnim stavem**, ne jen "je ten kod v HEAD":
   `git diff "stash@{N}:<cesta>" "HEAD:<cesta>"`
   Prazdny vystup = totozne. Kdyz vystup ukazuje, co **HEAD ma navic**, je HEAD nadmnozina a stash je zastarala kopie - zahodit ho nic neztrati.
   Pozor na syntaxi: `git stash show -p "stash@{N}" -- <cesta>` **spadne** na "Too many revisions specified", pouzij `git diff "stash@{N}^" "stash@{N}" -- <cesta>`.
4. Teprve po odsouhlaseni clovekem `git stash drop`.

## Konkretni vysledek z 17. 8. 2026 (aby to nikdo neresil znovu)

| | Obsah | Verdikt |
|---|---|---|
| `stash@{0}` | jen `WORK_LOCK.txt` | bezcenne - koordinace se 5. 8. presunula na `@@WORK`/`@@LOCK`/`@@WHO` |
| `stash@{1}` | `WORK_LOCK.txt` + `modules/erp/api/vyhodnoceni_actions.py` | **uz je v projektu**, HEAD je nadmnozina |

Kod ve `stash@{1}` byl audit uzaverky (`ec.akce_audit`). V HEAD je **i** navazujici opravneni na penezni akce (`_EC_AKCE_S_OPRAVNENIM`, `ec.akce_opravneni`), ktere ve stashi jeste nebylo. **Zahozeni obou stashu nic neztrati**, ale nechal jsem to na Jirkovi - mazani cizi odlozene prace neni moje rozhodnuti.

**Vedlejsi poznamka:** `WORK_LOCK.txt` je **stale sledovan gitem** (`git ls-files` ho vraci), proto dal dela konflikty. Neni to zavada - je to znamy prechodny stav, soubor ma jit do `.gitignore`, az budou vsechny instance na `@@WORK`. `apps/api/static_db/` uz v `.gitignore` je (r. 156) a `git ls-files` tam vraci 0.

Souvisi: [[doc-system-strategie-koordinace-instanci-work-lock-pres-most]], [[doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu]]

