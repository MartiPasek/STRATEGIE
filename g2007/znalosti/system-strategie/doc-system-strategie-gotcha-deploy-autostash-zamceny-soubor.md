# GOTCHA: deploy most + zamceny soubor = rozdelana prace zmizi do autostashe, ktery NENI v git stash list (27.7.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Co se stalo (i28, 27.7.2026)
Deploy pres most spadl na "KONFLIKT (rebase)" - ale ZADNY konflikt s jinou instanci to nebyl. Hlaska:
  rebase: Created autostash: 52d63402
  error: unable to unlink old 'APP/Mobile/version.properties': Invalid argument
  fatal: could not reset --hard
Pricinou byl bezici Gradle demon (java, start 14:59:59) z buildu mobilni appky, ktery DRZEL APP/Mobile/version.properties. Rebase soubor nedokazal prepsat a skoncil v pulce.

# Proc je to nebezpecne
`rebase --autostash` nejdriv odlozi rozdelane (uncommitted) zmeny a pak dela `reset --hard`. Kdyz reset selze:
  - pracovni strom zustane CASTECNE resetovany (moje rozdelana prace na build.gradle.kts byla pryc),
  - odlozeny balicek NENI videt v `git stash list` (autostash rebase se uklada do .git/rebase-merge/autostash, ne do stash reflogu),
  - v .git/rebase-merge zbyde jen soubor `autostash` (bez head-name/orig-head), takze `git rebase --abort` ani nejde - "no rebase in progress".
Kdo tohle nevi, mysli si, ze o praci prisel.

# Obnova (funguje)
1. sha odlozeneho balicku: `cat .git/rebase-merge/autostash`
2. co v nem je: `git show --stat <sha>`
3. porovnat s pracovnim stromem: `git diff <sha> -- <cesta>`
4. vratit soubor: `git checkout <sha> -- <soubor>` a hned `git restore --staged <soubor>`
   (checkout soubor ZASTAGUJE - kdyz to nechas, nejblizsi deploy ho omylem commitne!)
5. kdyz je soubor zamceny i pro checkout, zapsat obsah primo (Write / `git show <sha>:<cesta>`)
6. nakonec smazat zbytek: `rm -rf .git/rebase-merge`

# Jak se tomu vyhnout
- Pred deployem mit cisty pracovni strom, nebo aspon vedet, co v nem lezi (`git status --short`).
- Kdyz bezi build mobilni appky (Gradle demon), NEDEPLOYOVAT - demon drzi APP/Mobile/version.properties.
- Demona NEZABIJET jen kvuli deployi: muze bezet ostry build pro Google Play. Radsi pockat.
- Obchazka kdyz je lokal uz srovnany s origin (`git rev-list --left-right --count origin/main...HEAD` = 0 vlevo): rebase je prazdny, deploy projde i se spinavym stromem. Push sam o sobe se pracovniho stromu nedotyka.
- "KONFLIKT (rebase)" v CLAUDE_DEPLOY_OUT.txt NEZNAMENA automaticky konflikt s jinou instanci - precti si duvod, muze to byt zamceny soubor.

# Poznamka
Deploy je jinak bezpecny: pri selhani rebase NEPUSHNE a nenasadi (commit uz je lokalne hotovy). Souvisi [[doc-system-strategie-dev-workflow-prikazy]].

