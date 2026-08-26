# Most na macOS (launchd) — teď i s chybějícím STRATEGIE_GIT_PAT (26.8.2026)

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

1. **Token NEPATRI do plistu.** `scripts/run_bridge_macos.sh` ho cte z
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

## ⚠️ CHYBÍ STRATEGIE_GIT_PAT — `git push` přes most na Macu selhává (zjištěno 26.8.2026)

Instalace z 10.8.2026 výše vyřešila **čtení** (heartbeat, `@@` dotazy, `@@G2007ADD`) — psaní
do databáze funguje. **`git push` (deploy kanál `CLAUDE_DEPLOY_GO.txt`) na Macu ale NEFUNGUJE**,
protože `scripts/run_bridge_macos.sh` nastavuje jen `STRATEGIE_DEPLOY_TOKEN`, ne
`STRATEGIE_GIT_PAT` (runner ho čte volitelně, viz jeho docstring řádek ~45; bez něj zkouší
`git push origin main` bez PAT v URL, a protože runner sám vypíná credential helper
(`credential.helper=` prázdné, kvůli běhu bez uživatelské session), push spadne na
`fatal: could not read Username for 'https://github.com': terminal prompts disabled`).

**Ověřeno naostro 26.8.2026:** commit visící lokálně od 10.8.2026
(`feat(bridge): spousteni Claude SQL mostu na macOS`) se přes `CLAUDE_DEPLOY_GO.txt` nepodařilo
nahrát — `git add`/rebase proběhly OK, `git push` spadl přesně na výše popsanou chybu. Nic se
tím nerozbilo (commit zůstal bezpečně lokálně), jen se nenahrálo.

**Postup opravy (příště, Jirka + Marti):**
1. Na Windows notebooku zjistit `STRATEGIE_GIT_PAT` — `nssm get STRATEGIE-CLAUDE-SQL
   AppEnvironmentExtra` (jako Administrator). Pokud tam není, služba běží pod uživatelským
   účtem (`nssm get STRATEGIE-CLAUDE-SQL ObjectName` ukáže jméno místo `LocalSystem`) a git
   push tam jede přes uložené přihlášení ve Správě přihlašovacích údajů Windows
   (`git:https://github.com`), ne přes PAT v proměnné prostředí.
2. Na Macu **stejný princip jako u `STRATEGIE_DEPLOY_TOKEN`** (bod „Dvě rozhodnutí" výše) —
   token NEPATŘÍ do plistu. Přidat do `run_bridge_macos.sh` čtení z nového souboru
   `~/.strategie_git_pat` (chmod 600) + `export STRATEGIE_GIT_PAT=...`, restartovat most
   (`launchctl kickstart -k gui/$UID/cz.strategie.claude-sql`) — ten pak umí nahrát i tuhle
   úpravu skriptu samotnou, protože k tomu momentu už PAT má.
3. **Token nikdy neposílat do chatu s AI** — psát ho rovnou do souboru přes vlastní terminál
   (`!` příkaz v Claude Code), stejně jako u `STRATEGIE_DEPLOY_TOKEN`.

Do té doby: commity v `STRATEGIE-repo` udělané na Macu (typicky přes `@@G2007ADD`, který píše
přímo do DB, ne do gitu — ten kanál funguje beze změny) se dají nahrát i ručně z Windows
notebooku, nebo počkat na tuhle opravu.

