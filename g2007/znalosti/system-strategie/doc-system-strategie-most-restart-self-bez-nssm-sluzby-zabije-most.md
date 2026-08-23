# restart_self bez NSSM sluzby most uz nenahodi - ale na Jirkove stroji sluzba OD 21.8.2026 EXISTUJE (opraveno 24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# restart_self bez nainstalovane NSSM sluzby = most uz nenabehne

> **OPRAVA 24. 8. 2026 (rozhodl Jirka Honomichl, souhlasila Marti-AI, msg 13537).**
> **Tvrzeni nize, ze na stroji JiriH-ntb zadna sluzba `STRATEGIE-CLAUDE-*` neexistuje, UZ NEPLATI.**
> Premereno naostro 24. 8. 2026 primo na tom stroji: sluzba **`STRATEGIE-CLAUDE-SQL` existuje a bezi**
> (StartType Automatic, NSSM `nssm.exe` PID 12400, jeho potomek `python.exe` PID 22892 bezi
> od 21. 8. 2026 rano). Restart tedy funguje - `Restart-Service STRATEGIE-CLAUDE-SQL`
> (ucet Jirky ma admin prava), overeni = novy radek `forwarder started` ve `watcher.log`.
>
> **Obecne pouceni teto znalosti plati dal** - na stroji, kde sluzba NENI, `restart_self` most
> zabije a uz ho nenahodi, protoze `Restart-Service` nema co restartovat. Meni se jen fakt
> o jednom konkretnim stroji. Prave proto **pred `restart_self` vzdy over `service_status`
> / `Get-Service`, a to v OBOU smerech** - stav se na stroji casem meni, jak ukazal tenhle pripad.

**Zjisteno 17. 8. 2026 na stroji JiriH-ntb (Claude-28).**

## Co se stalo
Jedna session na stroji nasadila opravu `scripts/claude_sql_runner.py` a hned po ni
poslala do OPS lane `restart_self`. Most se ukoncil a **uz nenabehl**. Ostatni session
na stejnem stroji zustaly bez pristupu k DB - jejich `CLAUDE*_GO.txt` lezel nezpracovany
a ve `watcher.log` po radku "OPS bridge: restart_self ... OK" uz nic dalsiho nebylo.

## Pricina
`_restart_self()` v runneru spusti odpojeny PowerShell s
`Restart-Service -Name 'STRATEGIE-CLAUDE-SQL' -Force` a pak se **sam ukonci** (`sys.exit(0)`).
Na tomto stroji tehdy **zadna sluzba `STRATEGIE-CLAUDE-*` neexistovala** (overeno `Get-Service`
17. 8. 2026; **od 21. 8. 2026 uz existuje** - viz OPRAVA nahore)
- most tu bezel jako obycejny proces `python scripts/claude_sql_runner.py`.
`Restart-Service` tedy selze, restartovat neni co a proces uz je pryc.

Navratovka `restart_self` je proto **klamna**: do `CLAUDE_OPS_LOG.txt` se zapise "OK"
uz PRED restartem, takze audit tvrdi OK i v pripade, kdy se most nevratil.
**Tahle cast plati porad a nezavisle na tom, jestli sluzba existuje.**

## Jak ho nahodit zpatky
Token uz je v uzivatelskych promennych prostredi (`STRATEGIE_DEPLOY_TOKEN`, User),
takze staci spustit proces znovu:
`Start-Process python -ArgumentList "scripts\claude_sql_runner.py" -WorkingDirectory C:\projekty\STRATEGIE -WindowStyle Hidden`
Runner ma singleton lock, takze druha instance se sama ukonci - spustit ho navic neuskodi.
Overeni: novy radek ve `watcher.log` + libovolny SELECT pres most projde.
Na stroji, kde sluzba **existuje** (dnes JiriH-ntb), se misto toho pouzije
`Restart-Service STRATEGIE-CLAUDE-SQL`.

## Doporuceni
- **Pred `restart_self` overit, ze sluzba na stroji opravdu existuje** (`service_status`),
  jinak most nerestartujes, ale zabijes. **Overuj to znovu, ne z pameti ani z teto znalosti** -
  presne tohle se mezi 17. a 21. 8. 2026 zmenilo, aniz by to nekde vyskocilo.
- Na strojich bez NSSM sluzby restartovat most spustenim procesu, ne pres OPS lane.
- Pozor na souvislost: `restart_self` je **spolecny kanal pro cely stroj**, ne per-lane -
  polozi most vsem session na tom pocitaci naraz.

## Souvisejici
- `doc-system-strategie-restart-api-pres-most-hlasi-uspech-ale-nerestartuje` - u sluzby
  `STRATEGIE-API` plati opacna past: restart pres most vrati `rc: 0`, ale aplikace bezi dal.
  Spolecne pouceni obou znalosti: **navratovka restartu nedokazuje nic, overuj PID nebo log.**

