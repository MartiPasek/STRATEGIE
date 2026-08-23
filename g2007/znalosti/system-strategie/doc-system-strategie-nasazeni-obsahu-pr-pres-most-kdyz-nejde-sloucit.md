# Jak nasadit obsah PR pres most, kdyz na GitHubu neni pravo slouceni - a tri kontroly, bez kterych smazes cizi praci

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Nasazeni obsahu PR pres most (kdyz slouceni na GitHubu nejde)

Zapsal Claude-28 (Jirka Honomichl) **23.8.2026**, schvalila Marti-AI (msg 13474).
Postup je **overeny na ostrem nasazeni** iOS notifikaci (PR `MartiPasek/STRATEGIE#5`),
ne navrzeny od stolu.

## Kdy to nastane

Sdilene repo `MartiPasek/STRATEGIE` je verejne, ale **pravo zapisu ma malokdo**. Kdyz je
clovek prihlasen uctem bez tohoto prava, GitHub **slucovaci tlacitko vubec nezobrazi** -
ukaze jen zelene "no conflicts with base branch" a vedle ikonu "Unable to merge".

**Nepleti si to s konfliktem.** Rozliseni: `GET /repos/<owner>/<repo>/pulls/<n>` vrati
`mergeable_state`. Kdyz je `clean` a tlacitko presto neni, je to **otazka prav, ne obsahu**.
Overit se to da i primo: `GET /repos/<owner>/<repo>` s prihlasenim vrati `permissions`
(`pull` / `push` / `admin`).

**Precedens:** PR 2, PR 4 (18.-19.8.2026) i PR 5 (23.8.2026) se **nikdy neslouzily**
(`merged=false`, jen `closed`). Jejich obsah se do `main` dostal pres most. Je to zavedena
cesta, ne improvizace.

## ⚠️ TRI KONTROLY, BEZ KTERYCH SMAZES CIZI PRACI

Vetev PR byva **daleko pozadu** za `main` (dnes 74 zmen). Kdyz z ni soubory jen zkopirujes,
**vratis vsechno, co se v nich mezitim na `main` zmenilo** - presne incident z 31.7.2026.

**1) Zjisti spolecny zaklad vetve a main.**
`GET /repos/<owner>/<repo>/compare/main...<fork-owner>:<repo>:<vetev>` -> `merge_base_commit.sha`
(+ `behind_by` / `ahead_by`). Dnes: zaklad `445a47f5`, PR byl 74 zmen pozadu.

**2) Over, ze se ZADNY z menenych souboru na main od toho zakladu nezmenil.**
```
git log <zaklad>..HEAD --name-only -- <cesta1> <cesta2> ...
```
**Prazdny vystup = bezpecne**, kopie odpovida presne diffu PR. Kdyz neco vypise, **kopirovat
NESMIS** - musis prenest zmenu, ne soubor.

Druhy, nezavisly zpusob: porovnat otisky blobu `git rev-parse <zaklad>:<cesta>` proti
`git rev-parse HEAD:<cesta>`.
⚠️ **PAST:** u souboru, ktere PR teprve zaklada, `git rev-parse` selze na obou stranach
a naivni skript to vyhodnoti jako "lisi se". Nove soubory over pres `git cat-file -e`
(v `HEAD` NE, v zakladu NE, na disku NE = opravdu novy).

**3) Po zkopirovani over rozsah zmen proti PR.**
`git diff --stat` musi sedet na cisla z PR (dnes **14 souboru, +1528 / -26**, sedelo 1:1)
a `git status --porcelain | wc -l` musi dat presne pocet souboru z PR - **nic navic**.
Nesedi-li to, **zastav**.

## Postup

1. Zkontroluj, ze pracovni kopie je **cista** (`git status --porcelain` prazdny).
2. Kontroly 1 a 2 vyse.
3. Stahni soubory ze **spicky PR**, ne z vetve podle jmena (vetev se muze hnout):
   `https://raw.githubusercontent.com/<fork-owner>/<repo>/<sha>/<cesta>`.
   Seznam souboru vcetne stavu (`added`/`modified`/`renamed`) a binarnich:
   `GET /repos/<owner>/<repo>/pulls/<n>/files`.
4. Zkopiruj do pracovni kopie (binarni soubory po bajtech, ne pres text).
5. Kontrola 3 vyse.
6. Nasad pres most: `CLAUDE_DEPLOY.txt` (1. radek = jednoradkova zprava, dal **VYJMENOVANE
   cesty**, nikdy `ALL`), pak jako posledni `CLAUDE_DEPLOY_GO.txt`.
7. **Precti CELY `CLAUDE_DEPLOY_OUT.txt`**, ne jen prvni radek - hlavicka umi rict OK, i kdyz
   se dole neco nepovedlo (viz `doc-system-strategie-most-deploy-git-add-spadne-na-smazane-ceste`).
   Zkontroluj radek `N files changed` proti ocekavani.
8. **Do zpravy commitu napis, ze jde o obsah PR c. X, spicku a duvod**, proc se neslucovalo -
   jinak nikdo nedohleda, odkud se to vzalo.
9. **PR zavri** (nesloucen) s poznamkou, ktery commit obsah nese. Zavrit ho smi autor PR
   nebo nekdo s pravem zapisu.

## Co po nasazeni jeste zkontrolovat

- **Zavislosti.** Kdyz PR meni `pyproject.toml`, over, jestli meni i `poetry.lock`.
  Dnes NEMENIL a chybela knihovna `h2` - viz
  `doc-system-strategie-ios-notifikace-bod-obnovy-pred-nasazenim-2026-08-23`.
  **Tvrzeni v popisu PR o zavislostech neber jako fakt, over ho.**
- **Neco, co PR predpoklada v databazi** (tabulky, vlastnictvi, prava) - PR o tom nic nevi.

## Proc radeji tudy nez "nejak to sloucit"

Jde to i tak, ze se pouzije ulozeny pristup s pravem zapisu. **Ale pozor:** pristup ulozeny
u projektu patri **konkretnimu cloveku** (dnes Marti Paskovi, s pravy spravce). Pushnout jim
zmenu je v poradku (autorstvi commitu se nastavuje zvlast), ale **napsat jeho jmenem verejny
komentar nebo zavrit cizi PR uz je vystupovani za neho** - to se nedela bez jeho vedomi.
Dnes to Jirka vyresil tak, ze PR zavrel sam.

