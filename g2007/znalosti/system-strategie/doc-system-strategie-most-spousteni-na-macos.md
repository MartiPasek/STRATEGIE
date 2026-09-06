# Most na macOS (launchd)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Most na macOS (launchd)

> oblast: system-strategie · Jirka (C28) + Claude, 10. 8. 2026. Overeno v ostrem provozu.
> Doplnuje `most-kanaly` (kanaly a protokol) a `doc-system-strategie-bridge-most-lanes-ops`
> (lanes, OPS) o spousteni na Macu. Instalace na Windows pres NSSM se nemeni.

## Runner je uz ted multiplatformni — doladovat nebylo co

`docs/team/Jirka28.md` vedl macOS variantu jako nedodelek. Ukazalo se, ze
`scripts/claude_sql_runner.py` bezi na Macu bez jedine upravy: pouziva **jen stdlib**
(urllib, pathlib) a `_git_exe()` zkousi nejdriv `git` z PATH, teprve pak windowsove cesty.
Windowsova byla **pouze instalace** pres NSSM, popsana v jeho docstringu.

## Instalace (PR MartiPasek/STRATEGIE#3)

```sh
printf '%s' '<token>' > ~/.strategie_deploy_token && chmod 600 ~/.strategie_deploy_token
cp scripts/cz.strategie.claude-sql.plist.template ~/Library/LaunchAgents/cz.strategie.claude-sql.plist
sed -i '' "s|__REPO__|$PWD|g" ~/Library/LaunchAgents/cz.strategie.claude-sql.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/cz.strategie.claude-sql.plist
```

Kontrola `launchctl list | grep strategie`, odinstalace
`launchctl bootout gui/$(id -u)/cz.strategie.claude-sql`, logy `scripts/claude_sql/bridge.log`.

## Dve rozhodnuti, ktera stoji za zopakovani

1. **Token NEPATRI do plistu.** `scripts/claude_sql/run_bridge_macos.sh` ho cte z
   `~/.strategie_deploy_token` (chmod 600). V plistu by byl citelny pres `launchctl print`
   a skoncil by v zaloze domovskeho adresare.
2. **Kdyz token jeste neni, wrapper CEKA misto aby skoncil chybou.** S `KeepAlive` by ho
   launchd restartoval porad dokola; takhle most nabehne sam do 30 s po vzniku souboru,
   takze poradi „nainstaluj most" a „doplnil jsem token" je jedno.

Wrapper si repo odvodi z umisteni skriptu (`${0:A:h}`), takze funguje at je klon kdekoliv;
ID instance bere z env `CLAUDE_INSTANCE_ID`, jinak z `scripts/claude_sql/INSTANCE_ID.txt`.

## Kde token vzit

Vydava ho Marti (tyz token, jaky ma cloud APP pro `/api/v1/erp/diag-sql`). Na Windows stroji
byva v konfiguraci sluzby `STRATEGIE-CLAUDE-SQL`, ale **ne vzdy jako NSSM sluzba** — na
Jirkove Windows stroji registrova cesta
`HKLM\SYSTEM\CurrentControlSet\Services\STRATEGIE-CLAUDE-SQL\Parameters` neexistuje, takze
hledat i v promennych prostredi (User/Machine) a mezi bezicimi python procesy.

## Overeno 10. 8. 2026

Na Macu (Claude-28): heartbeat OK a vidi ostatni instance, cteni pres `diag-sql` prochazi,
`@@G2007ADD` zapsal znalost `doc-system-strategie-ios-build-upload-a-past-dvou-contentview`
(overeno ctenim, chunky > 0).

## ✅ STRATEGIE_GIT_PAT doplnen, `git push` z Macu FUNGUJE (6. 9. 2026)

**NEPLATI uz dolni sekce „CHYBI STRATEGIE_GIT_PAT"** — problem je opraveny, text nize je
ponechany jako historie diagnozy.

Postup dle Jirkova rozhodnuti 28. 8. 2026 (`doc-system-strategie-ios-jeden-repos-vse-do-strategie`,
navod `MAC_NASTAVENI_STRATEGIE.md` v sitove slozce `_pro MAC`): token vzat z `.git/config`
Windows klonu (soubor `config(git token).txt` v te same sitove slozce, obsahoval remote URL
s `x-access-token:<PAT>@github.com`), Jirka ho sam ulozil pres `!` prikaz v terminalu do
`~/.strategie_git_pat` (chmod 600) — **Claude token nikdy nevidel jako text, jen extrahoval
sed prikazem, ktery Jirka sam spustil.**

Do `scripts/claude_sql/run_bridge_macos.sh` doplneno cteni tohoto souboru + `export
STRATEGIE_GIT_PAT=...`, stejnym principem jako `STRATEGIE_DEPLOY_TOKEN` (volitelne, nic
neceka/neblokuje kdyz soubor chybi — `claude_sql_runner.py` bez nej jen zkusi fallback
`git push origin main`). Most restartovan (`launchctl kickstart -k gui/$UID/cz.strategie.claude-sql`),
heartbeat OK.

**Overeno naostro:** spusten `CLAUDE_DEPLOY_GO.txt` bez uvedenych souboru (jen `git add -A`
no-op + push, nic se necommitovalo, protoze nebylo co) → `# DEPLOY: OK`, `git push` konecne
nahral commit `f872b5e8` visici lokalne od 10. 8. 2026 (`49618c0f..f872b5e8 HEAD -> main`),
nasledny cloud deploy probehl (3 soubory, API restart). Produkce overena po nasazeni:
`https://strategie-ai.com/mobile` i `/api/v1/erp/app-version` obe HTTP 200.

**⚠️ Vedlejsi nález pri teto oprave, NEVYRESENO:** skript, ktery most na Macu skutecne
spousti (`scripts/claude_sql/run_bridge_macos.sh`), lezi v cele **gitignorovane** slozce
(`.gitignore:71` ignoruje `scripts/claude_sql/` celou) — tenhle skutecne bezici skript tedy
**neni v gitu vubec**. Prave nahrany commit `f872b5e8` pritom obsahuje JINOU, drivejsi verzi
téhož skriptu na ceste `scripts/run_bridge_macos.sh` (trackovana, ale nikym nepouzivana —
jiny zpusob odvozeni cesty k repu, jiny nazev promenne pro token). Dva soubory resi totez
jinak = tichy rozpor (bod 14 pravidel). Nesjednoceno, ceka na Jirkovo rozhodnuti (smazat
starou trackovanou verzi, nebo presunout live skript do trackovane cesty).

## ⚠️ HISTORIE (do 6. 9. 2026 platilo, uz NEPLATI) — CHYBĚLA STRATEGIE_GIT_PAT

Instalace z 10.8.2026 výše vyřešila **čtení** (heartbeat, `@@` dotazy, `@@G2007ADD`) — psaní
do databáze funguje. **`git push` (deploy kanál `CLAUDE_DEPLOY_GO.txt`) na Macu ale
NEFUNGOVAL**, protože `run_bridge_macos.sh` nastavoval jen `STRATEGIE_DEPLOY_TOKEN`, ne
`STRATEGIE_GIT_PAT` (runner ho čte volitelně; bez něj zkoušel `git push origin main` bez PAT
v URL, a protože runner sám vypíná credential helper, push spadal na `fatal: could not read
Username for 'https://github.com': terminal prompts disabled`).

Ověřeno naostro 26.8.2026: commit visící lokálně od 10.8.2026 se přes `CLAUDE_DEPLOY_GO.txt`
nepodařilo nahrát — `git add`/rebase proběhly OK, `git push` spadl přesně na výše popsanou
chybu. Nic se tím nerozbilo (commit zůstal bezpečně lokálně), jen se nenahrál — a právě tenhle
commit (`f872b5e8`) se 6. 9. 2026 konečně nahrál, viz sekce výše.

