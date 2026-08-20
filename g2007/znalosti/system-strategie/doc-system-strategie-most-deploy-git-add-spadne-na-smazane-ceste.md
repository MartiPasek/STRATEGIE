# Most - deploy hlasil OK, i kdyz git add spadl a soubory se necommitly (OPRAVENO 18. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **Stav - OPRAVENO 18. 8. 2026** commitem `28e1397b` (Jirka, schvalila Marti-AI msg 12897). Projevi se na kazdem stroji az po `git pull` + restartu watcheru. Dokud restart neprobehl, plati stare chovani popsane nize.

## Co se stalo (18. 8. 2026, Claude-28 / Jirka)

Deploy pres most (`CLAUDE_DEPLOY.txt` + `CLAUDE_DEPLOY_GO.txt`) obsahoval dva soubory - jeden **smazany pres `git rm`** (`APP/iOS/ContentView.swift`) a jeden upraveny (`docs/apple_jirka_navod_2.md`).

Watcher udelal `git add -- <oba soubory>` a **cely prikaz spadl**:

```
## git add APP/iOS/ContentView.swift docs/apple_jirka_navod_2.md - FAIL(rc=128)
fatal: pathspec 'APP/iOS/ContentView.swift' did not match any files
```

Deploy presto **pokracoval** a nahore napsal `# DEPLOY: OK`. Commit vznikl jen z toho, co uz bylo naindexovane driv - **upraveny navod se do commitu vubec nedostal** a skoncil v autostashi. Commit message pritom tvrdil, ze obsahuje oboji.

## Presna pricina (otestovano, ne odhadnuto)

Rozhoduje, jestli cesta jeste nekde je:

| Situace cesty | `git add -- <cesta>` | Pozn. |
|---|---|---|
| Existuje na disku | **OK** | bezny pripad |
| Smazana na disku, ale **porad tracked** | **OK**, naindexuje `D` | `git add` mazani zvlada |
| Uz odstranena pres **`git rm`** (neni na disku ANI v indexu) | **rc=128** | tohle nas polozilo |
| Neexistuje vubec (preklep) | rc=128 | spravne |

**Pozor na slepou uličku** - `git add -A -- <uz git-rm-nuta cesta>` spadne **uplne stejne**. Prvni navrh opravy byl prave "pridat -A" a **byl by k nicemu**; vyslo to najevo az pri testu v samostatnem pisecku. Kdyz cesta neni na disku ani v indexu, neni co matchovat a zadny prepinac `add` to nezmeni.

## Proc to bylo nebezpecne

- **Hlavicka hlasila OK**, push probehl, commit existoval. Jen v nem chybela cast prace.
- **Padal cely `git add`, ne jen ta jedna cesta** - nenaindexoval se **ANI JEDEN** z uvedenych souboru.
- Kdyz uz neco naindexovane bylo, vznikl **commit s jinym obsahem, nez rika jeho popis**. To je horsi nez cisty pad.

## Jak to je opravene

Ve vetvi pro vyjmenovane soubory (`_process_deploy`) se cesty pred `git add` roztridi na tri hromadky:

1. **na disku, nebo smazana ale porad tracked** -> jde do `git add`,
2. **neni na disku ani v indexu, ale JE mezi staged zmenami** (typicky po `git rm`) -> **preskocit**, do vypisu jde poznamka `## git add - POZNAMKA`; commit to vezme sam, protoze watcher pousti `git commit` bez `-a` nad celym indexem,
3. **neni nikde** -> preklep, deploy se **zastavi**.

Druha cast opravy - kdyz staging skonci nenulovym `rc`, deploy zapise **`# DEPLOY: ZASTAVEN (git add)`**, nic nepushne ani nenasadi. Stejny vzor jako `py_compile` gate o kus niz. Vetev `ALL` a zbytek deploye jsou beze zmeny.

**Overeno** - logika otestovana v pisecku na vsech ctyrech pripadech z tabulky (zaradila je spravne, po pridani sedi index `D`, `D`, `M`), pote **ostry test pres most**: seznam s neexistujici cestou vratil `DEPLOY - ZASTAVEN (git add)`, HEAD se nezmenil a pracovni kopie zustala cista.

## Co si z toho odnest i po oprave

- **Cti CELY `CLAUDE_DEPLOY_OUT.txt`, ne jen prvni radek.** Hlavicka nemusi vedet o vsem, co se dole stalo.
- **Kontroluj radek `N files changed`** proti tomu, co jsi cekal, a po deployi `git status`.
- Mazani souboru **nemusis** uvadet v seznamu cest - staged `git rm` se do commitu dostane samo (uvest ho ale uz neni chyba, nova vetev si s tim poradi).

Souvisi s bodem 4 pravidel prace (diffstat kontrola pred pushem) - presne ten typ tiche odchylky, kterou ma hlidat technika, ne kazen.

