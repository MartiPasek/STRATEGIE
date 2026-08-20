# Claude SQL most na macOS — launchd misto NSSM, token ze souboru

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

