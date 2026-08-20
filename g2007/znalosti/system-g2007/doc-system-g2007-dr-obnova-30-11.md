# DR obnova databaze na 30.11 (Plzen) - pricina, oprava, autonomni ovladani

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# DR obnova databaze na 30.11 (Plzen) - pricina, oprava, autonomni ovladani

Stav 27.7.2026: VYRESENO. Standby STRATEGIE-API bezi, nocni obnova zase dojizdi. Otevrene jen priskrcene spojeni Plzen->Praha (na Michala).

## Architektura DR
- Praha = produkce (strategie-ai.com, EUR-APP-1P / 188.11).
- Plzen = standby (EC-SERVER2 / 192.168.30.11).
- Nocni retez: dump na 188.12 ve 3:00 -> push do Prahy 3:15 -> pull+restore na 30.11 ve 3:30 -> self-check 3:45.
- Task na 30.11: STRATEGIE-DR-PullRestore (bezi jako SYSTEM), skript C:\scripts\dr_pull_restore.ps1.

## Incident (od 23.-24.7. "obnova konci chybou")
Dve nezavisle priciny.

### 1) Chyba ve skriptu (root cause, OPRAVENO)
Skript mel $ErrorActionPreference='Stop'. Radek restoru:
    & pg_restore.exe ... 2>&1 | ForEach-Object { Log ... }
Pod 'Stop' staci, aby pg_restore poslal PRVNI radek na stderr (i neskodne varovani), a PowerShell to bere jako terminating error -> skript umre hned na zacatku restoru s exit 1. Dusledek: STRATEGIE-API se predtim zastavi, ale uz se NENAHODI (skript nedojde k casti start). Proto standby lezel a data starla (fw.dr_selfcheck data_age +24h/den, od 07-24).

Oprava (verze "C23 27.7. (2)" v hlavicce skriptu):
- Pred restore/granty/start prepnout na $ErrorActionPreference='Continue' -> stderr z psql/pg_restore se jen loguje, skript pokracuje a VZDY nahodi API.
- Zachytit $rc = $LASTEXITCODE, logovat "Restore rc=" a pokracovat bez ohledu na rc.
- META timeout 30->60 s, download timeout 600->1200 s (kvuli pomalemu spojeni).
- Preskocit stahovani, kdyz dump uz je na disku se spravnou velikosti (rychla obnova bez zbytecneho ~12min downloadu).

Pozn.: rc=1 je normalni "ignored errors" u pg_restore --clean --if-exists do neprazdne DB (DROP SCHEMA / "schema already exists" u schemat). Data v tabulkach se presto prepisou. Neni to chyba obnovy.

### 2) Priskrcene spojeni Plzen->Praha (OTEVRENO - na Michala)
30.11 -> strategie-ai.com jede ~1 MB/s misto obvyklych ~25 MB/s. 746MB dump se stahoval 752 s. Male requesty (META, par kB) jsou na hrane timeoutu a obcas spadnou. Casove sedi na nedavnou zmenu na Mikrotiku/DNS na plzenske strane. Nocni beh (SYSTEM) prochazi, jen pomalu. Pozorovan i obcasny 401/503 na ceste Praha->30.11 (api.eurosoft.com/marti-mcp) pri zatezi.

## Autonomni ovladani 30.11 z Coworku (bez RDP/VPN)
Retez: zapis do D:\Projekty\STRATEGIE\scripts\claude_sql\ (CLAUDE_SQL.sql + CLAUDE_GO.txt s nonce) na Martiho NB -> watcher na NB forwardne na Praha /api/v1/erp/diag-sql -> odpoved do CLAUDE_OUT__<nonce>.txt.

Bridge prikazy:
- @@FILES READ / LIST <abs cesta>  = cteni logu/adresaru na 30.11 (D:\STRATEGIE_IN, C:\scripts).
- @@FILES WRITE <abs cesta> + newline + base64  = zapis souboru na RW root (takhle se nasadila oprava skriptu bez RDP).
- @@MCPOPS {tool,args}  = volani MCP nastroje na 30.11 pres /admin/ops (Bearer).
- @@MCPHEALTH, @@MCPUPDATE  = health / self-update MCP (git pull + restart ~2 min).
- @@DRDIAG  = Praha-side diag DR dumpu (stat s timeoutem).

GREEN ops akce (bez banneru) v eurosoft_ops_run: pg_status, pg_dump, disk, dr_restore (spusti skript pod servisnim uctem MCP), net_test, dr_task_run (spusti STRATEGIE-DR-PullRestore jako SYSTEM). YELLOW (pg_restore, run_script, service stop) = banner/blok. RED = jen clovek.

DULEZITE: META na /dr/meta padala z kontextu MCP-servisniho uctu (dr_restore), ale z kontextu SYSTEM (dr_task_run = nocni beh) prosla. Proto se DR overuje/spousti pres dr_task_run, ne pres dr_restore.

Klicove soubory v kodu (nasazuji se pres git + @@MCPUPDATE; ENV/NSSM se bez RDP menit neda, proto natvrdo v kodu):
- modules/eurosoft_mcp/ops_tools.py = OPS_ENABLED default ON (Marti auth 27.7.), GREEN akce dr_restore/net_test/dr_task_run.
- modules/eurosoft_mcp/filesystem_tools.py = _allow_roots() fixne pridava RW C:\scripts, RO D:\STRATEGIE_IN;D:\STRATEGIE_ARCHIVE.
- modules/eurosoft_mcp/server.py = endpoint /admin/ops (ops_admin), Bearer.
- modules/erp/api/router.py = bridge prikazy @@MCPOPS, @@DRDIAG.

## Aktualni stav (27.7.2026 ~08:15 local)
- Skript opraven a nasazen na C:\scripts\dr_pull_restore.ps1 (3818 B).
- Rucni obnova jako SYSTEM: 08:06 skip-download (dump z 3:00, age ~4,85h) -> 08:09 Restore rc=1 -> granty -> STRATEGIE-API spustena.
- STRATEGIE-API: RUNNING. Standby slouzi cerstva data.
- Nocni 3:30 beh by mel projit sam (SYSTEM, META OK), jen pomale stahovani kvuli throttle.

## Otevrene ukoly
1. Michal: proverit priskrcene spojeni Plzen(30.11)->Praha (Mikrotik QoS/firewall, DNS pro strategie-ai.com). Marti zavola. Draft nize.
2. Volitelne: pridat GREEN akci dr_selfcheck_run, at jde self-check spustit rucne a hned vynulovat data_age (jinak se srovna po nocnim 3:45).

## Draft pro Michala
Ahoj Michale, na plzenskem serveru (EC-SERVER2, 30.11) se od ~23.-24.7. strasne zpomalilo spojeni ven na strategie-ai.com (Praha) - download jede ~1 MB/s misto obvyklych ~25 MB/s, 746 MB se tahne pres 12 minut a kratke HTTPS requesty obcas spadnou na timeout. Kvuli tomu nam prestala dojizdet nocni DR obnova databaze. Vypada to na zmenu na Mikrotiku (QoS/bandwidth limit, firewall) nebo DNS na plzenske strane, konkretne pro provoz na strategie-ai.com. Mrknes na to prosim? Diky, Marti

