# @@restart_self na stroji BEZ NSSM sluzby most nezabije jen docasne - uz se nevrati (17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# restart_self bez nainstalovane NSSM sluzby = most uz nenabehne

**Zjisteno 17. 8. 2026 na stroji JiriH-ntb (Claude-28).**

## Co se stalo
Jedna session na stroji nasadila opravu `scripts/claude_sql_runner.py` a hned po ni
poslala do OPS lane `restart_self`. Most se ukoncil a **uz nenabehl**. Ostatni session
na stejnem stroji zustaly bez pristupu k DB - jejich `CLAUDE*_GO.txt` lezel nezpracovany
a ve `watcher.log` po radku "OPS bridge: restart_self ... OK" uz nic dalsiho nebylo.

## Pricina
`_restart_self()` v runneru spusti odpojeny PowerShell s
`Restart-Service -Name 'STRATEGIE-CLAUDE-SQL' -Force` a pak se **sam ukonci** (`sys.exit(0)`).
Na tomto stroji ale **zadna sluzba `STRATEGIE-CLAUDE-*` neexistuje** (overeno `Get-Service`)
- most tu bezi jako obycejny proces `python scripts/claude_sql_runner.py`.
`Restart-Service` tedy selze, restartovat neni co a proces uz je pryc.

Navratovka `restart_self` je proto **klamna**: do `CLAUDE_OPS_LOG.txt` se zapise "OK"
uz PRED restartem, takze audit tvrdi OK i v pripade, kdy se most nevratil.

## Jak ho nahodit zpatky
Token uz je v uzivatelskych promennych prostredi (`STRATEGIE_DEPLOY_TOKEN`, User),
takze staci spustit proces znovu:
`Start-Process python -ArgumentList "scripts\claude_sql_runner.py" -WorkingDirectory C:\projekty\STRATEGIE -WindowStyle Hidden`
Runner ma singleton lock, takze druha instance se sama ukonci - spustit ho navic neuskodi.
Overeni: novy radek ve `watcher.log` + libovolny SELECT pres most projde.

## Doporuceni
- **Pred `restart_self` overit, ze sluzba na stroji opravdu existuje** (`service_status`),
  jinak most nerestartujes, ale zabijes.
- Na strojich bez NSSM sluzby restartovat most spustenim procesu, ne pres OPS lane.
- Pozor na souvislost: `restart_self` je **spolecny kanal pro cely stroj**, ne per-lane -
  polozi most vsem session na tom pocitaci naraz.

