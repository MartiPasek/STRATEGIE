# CLAUDE_PULL_GO hlasi CONFLICT porad dokola - lokal je zaparkovany na stare feature vetvi, ne na main (24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# CLAUDE_PULL_GO hlasi CONFLICT porad dokola - lokal je zaparkovany na stare feature vetvi

Zapsal Claude-28 (Mac), 24.8.2026, po incidentu v ramci startovni rutiny. Souvisi s
[[doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit]] a
[[doc-system-strategie-github-prava-uctu-na-sdilenem-repu-a-gh-cli]].

## Co se stalo

Krok 1 startovni rutiny (`CLAUDE_PULL_GO.txt`) opakovane hazel:

```
CONFLICT (add/add): Merge conflict in modules/erp/api/ios_push.py
Could not apply 8b731b3f... feat(ios): APNs notifikace - serverova cast
```

Vypadalo to jako kolize s cizi praci. Nebyla.

## Pricina

Sdileny lokalni klon (`~/Projekty/STRATEGIE/STRATEGIE-repo` na Macu, obdobne na Windows)
byl porad zaparkovany na vetvi `feat/ios-push-server` - to je vetev, na ktere vznikl
PR #5. PR uz byl **davno uzavreny** a jeho obsah uz je v `main` (dostal se tam pres most,
viz `doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit`).

`CLAUDE_PULL_GO` dela `fetch + rebase --autostash` **aktualne vybrane vetve** na
`origin/main` - **necekuje si sam main**, predpoklada, ze lokal uz na spravne vetvi je.
Kdyz zustane zaparkovany na uzavrene feature vetvi, kazdy pull se snazi znovu prehrat
uz-zdeployovany commit na novejsi `main` -> `add/add` konflikt, porad dokola, u kazde
session, ktera pull spusti.

## Jak poznat, ze je to tohle, ne skutecny konflikt

`git status` (read-only, bezpecne pustit primo) ukaze `On branch feat/...` misto `main`.
Porovnat s `git log <branch>` - kdyz commit, na kterem to padne, uz je obsahove
v `origin/main` (jinou cestou, napr. primym commitem pres most), je to presne tenhle pripad.

## Oprava - musi ji udelat clovek, ne Claude pres most

**Bridge nema prikaz na `git checkout`** - potvrdila Marti-AI (msg 13616): `CLAUDE_PULL_GO`
pocita s tim, ze lokal uz je na spravne vetvi, checkout musi udelat operator rucne
mimo most (git checkout/reset/rebase pres bash na tehle sdilene repo je jinak zakazane -
zanechalo by zamek, ktery blokuje ukladani zmen cele siti).

```sh
cd ~/Projekty/STRATEGIE/STRATEGIE-repo
git checkout main
git pull --rebase --autostash
```

Kdyz rebase najde konflikt (stavalo se to u souboru, ktere ma stara vetev pozadu za `main` -
napr. `project.pbxproj` s cislem verze, `ContentView.swift` se starsim komentarem u markeru):
resit rucne, typicky se ponecha HEAD (novejsi, aktualni `main`) strana, protoze incoming
je uz stary a superseded. Po `git add <soubor> && git rebase --continue` to normalne dobehne.

## Prevence do budouctna

Po kazdem "fork+PR nebo primy commit pres most" nasazeni (viz
`doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit`) zkontrolovat,
jestli sdileny lokalni klon nezustal zaparkovany na te feature vetvi, a pred koncem session
ho vratit na `main`. Jinak dalsi session, ktera spusti krok 1 startovni rutiny, narazi
na tenhle stejny zdanlivy "konflikt" a muze si myslet, ze jde o kolizi s cizi praci.

