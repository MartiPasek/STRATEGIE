# Cloud Helios 188.12 - dve SQL instance na statickem portu 1433 (vypadek vyplatnic 7.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo (7.8.2026)

Vyplatnice v ERP hlasily "0 lidi, obdobi v cloudu neni" u obou firem. Most `db=mssql188`
vracel `InterfaceError 28000 - Login failed for user 'sa' (18456)` za ~35 ms.
Vypadalo to jako spatne heslo `sa` nebo chybejici `MSSQL188_CONN`. Nebylo to ani jedno.

## Skutecna pricina (overeno v errorlogu a registru 188.12)

Na stroji 10.200.188.12 bezi DVE SQL instance - `MSSQLSERVER` (ucetni, server name
EUR-DB-MSSQL-1P, data na disku D) a `SQLEXPRESS`. Obe maji v registru
`SuperSocketNetLib\Tcp\IPAll\TcpPort = 1433` staticky, `TcpDynamicPorts` prazdne.
Kdo nastartuje driv, port dostane; druhy zustane bez TCP listeneru.

Casova osa
- 6.8. 22\01 restart VM (prace CMIS - disky, RAM 4094 -> 5272 MB)
- 6.8. 22\37 ucetni instance nabehla, ale `Server TCP provider failed to listen on 1433.
  Tcp port is already in use` (chyby 17182 a 26023) - port uz drzela SQLEXPRESS
- 7.8. cely den klient z 188.11 na 188.12 port 1433 trefoval SQLEXPRESS, kde ma `sa`
  jine heslo -> 18456. Heslo sa se nemenilo (`sys.sql_logins.modify_date` = 27.6.2026)
- 7.8. 18\26 restart ucetni instance - stale padl na obsazeny port
- 7.8. 18\41\12 cisty start, protoze sluzba `MSSQL$SQLEXPRESS` byla zakazana
  (registr `Start = 4`). Vyplatnice se vratily.

## Mina, ktera trva

Oba porty jsou porad staticky 1433. Drzi to jen to, ze SQLEXPRESS je disabled.
Kdyz ji nekdo znovu povoli a stroj se restartuje, vypadek se opakuje.
Trvala oprava je dat SQLEXPRESS jiny port (nebo dynamicke porty), pripadne ji odinstalovat.

## Jak takovou vec priste rozpoznat (postup)

1. "Login failed" NEznamena automaticky spatne heslo. Kdyz se poverovaci udaj nemenil,
   ptej se, KDO odpovida - ne jestli heslo sedi.
2. Over jmeno serveru z jineho kanalu, nez ktery selhava - Marti-AI umi remote exec
   z 188.11, staci `sqlcmd -S 10.200.188.12 -Q "SELECT @@SERVERNAME"`. Jine jmeno
   nez EUR-DB-MSSQL-1P = mluvis se spatnou instanci.
3. Kdyz uz spojeni jde, errorlog pres `xp_readerrorlog` (most nevraci rowset z EXEC,
   takze `INSERT INTO` docasne tabulky a pak `SELECT`). Archiv 1 az 4 = starsi logy,
   log se pretaci pri kazdem startu.
4. `sys.dm_os_sys_info.sqlserver_start_time` rekne, kdy instance nastartovala,
   `sys.sql_logins.modify_date` rekne, jestli se heslo vubec menilo.
5. Instance a porty z registru - `xp_regenumvalues` na
   `SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL` a `xp_regread` na
   `MSSQL17.<instance>\MSSQLServer\SuperSocketNetLib\Tcp\IPAll`.

## Druha strana problemu - nas kod to zamlci

`mzdy_vyplatnice` (g2007.python, v router.py uz jen delegat) dela
`if not (_ro.get("ok") and _ro.get("rows")) -> return {"ok"\: True, "lidi"\: [],
"pozn"\: "obdobi v cloudu neni"}`. Chyba spojeni se tim prevlekne za prazdny uspesny
vysledek a uzivatel vidi "0 lidi" misto "server neodpovida". Stejny vzor ma cely
sdileny `_mssql188_query` - vraci `{ok\: false}` misto vyjimky, takze kazde volajici
misto si musi `ok` ohlidat samo. Blast radius - vyplatnice a detail, financni podminky,
import mzdovych plataku, JMHZ, saldo_praha_ec/es, `@@XFER`.

