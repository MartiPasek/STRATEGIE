# Servery STRATEGIE - sluzby, watchery, skripty (inventar co kde bezi)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Servery STRATEGIE - sluzby, watchery, skripty (inventar co kde bezi)

Stav 27.7.2026. Doplnuje id 135 (doc-system-strategie-produkcni-infra), ktere melo o 188.12 jen "PostgreSQL 16 + pgvector". Cil: mit na jednom miste, co na kterem serveru bezi za sluzby/watchery a jake skripty to spousteji.

## Prehled serveru
- 188.11 EUR-APP-1P - aplikacni server (cloud APP), public https://strategie-ai.com
- 188.12 EUR-DB-MSSQL-1P - datovy/DB server (PostgreSQL 16 + MSSQL), sem se delaji zalohy
- 30.11 EC-SERVER2 - Plzen standby (DR cil)

## 188.11 (EUR-APP-1P) - aplikacni server
NSSM sluzby: STRATEGIE-API (8002, current), STRATEGIE-API-B (8003, day-old snapshot, blue-green), STRATEGIE-CADDY (LB, lb_policy first + pin/unpin fallback), STRATEGIE-EMAIL-FETCHER, STRATEGIE-TASK-WORKER, STRATEGIE-QUESTION-GENERATOR.

## 188.12 (EUR-DB-MSSQL-1P) - datovy/DB server
- PostgreSQL 16 (+pgvector), produkcni data_db (loopback localhost:5432, datadir D:/PostgreSQL/16/data). PG sluzba bezi pod NT AUTHORITY\NETWORK SERVICE (NENI admin: umi spoustet prikazy, cist soubory, ZAPIS do C:\Scripts a PG datadiru; NEUMI zapis do korene D:\, ani menit/restartovat sluzby/tasky).
- MSSQL instance (odtud jmeno serveru) - mimo dosah PG mostu.
- NSSM sluzby (jedina vlastni): STRATEGIE-APID-WATCHER (ucet LocalSystem) -> spousti C:\Scripts\apid_watcher.ps1 ve smycce (15s). POZOR: NEDELA dump. Jen (a) listuje zalohy z E:\STRATEGIE do fw.apid_backup (appka z toho cte "seznam zaloh"), (b) na pozadavek z fw.apid_restore_req obnovi vybranou zalohu do data_db_test (API-D test-restore; produkce netknuta). Log C:\Scripts\apid_watcher.log.

### C:\Scripts na 188.12 (vlastni kopie, NE z gitu - menit primo na serveru)
- backup_data_db.ps1 - denni pg_dump -Fc -Z6 --no-owner do E:\STRATEGIE\<yyyy-MM-dd>\data_db_<HHMMSS>.dump. Ma v sobe vlastni retenci 30 dni.
- prune_pg_backups.ps1 - Root=E:\STRATEGIE, KeepDays=11, MinKeep=7. Bezi po dumpu a maze starsi slozky. PREBIJI 30 dni z backup_data_db.ps1 -> SKUTECNA RETENCE JE ~11 DNI (min. 7 nejnovejsich).
- push_dump.ps1 - Root=E:\STRATEGIE, posila nejnovejsi *.dump RAW POSTem na https://strategie-ai.com/api/v1/ops/dr/upload (hlavicka X-DR-Token).
- apid_watcher.ps1 (viz sluzba vyse), setup_apid_watcher_service.ps1, apid_grants.sql.

### Zalohy
Disk E:\STRATEGIE (E: = 10 GB, temer plny). Jeden dump ~0.75 GB a roste ~22 MB/den. Efektivni retence ~11 dni. Denni podslozky yyyy-MM-dd.

### fw.ops_run - NOVE (27.7.2026, Cowork)
Auditovany, whitelistem hlidany OS-exec kanal na 188.12 pres Postgres: fw.ops_run(p_cmd) pousti prikaz z fw.ops_whitelist (green) pres COPY FROM PROGRAM (bezi jako NETWORK SERVICE), vystup do fw.ops_out. Dosahne na nej Cowork (SQL most) i Marti-AI (in-app, je na DB superuser). Reverzibilni: DROP FUNCTION fw.ops_run + DROP TABLE fw.ops_out/ops_stage/ops_whitelist.

### NEPORADEK / k systemovemu doreseni na 188.12
1. RETENCE SI ODPORUJE: backup_data_db.ps1 = 30 dni vs prune_pg_backups.ps1 = 11 dni. Skutecne plati 11 (prune bezi po dumpu). Sjednotit na jedno cislo na jednom miste (nechat retenci jen v prune, z backup_data_db.ps1 ji vyhodit - nebo naopak), at je jasno.
2. CIM JE DUMP DENNE SPOUSTEN? Na 188.12 je jedina NSSM sluzba (APID-WATCHER) a ta dump nedela. Zadny STRATEGIE-* Windows scheduled task neni videt z neadmin uctu (NETWORK SERVICE). backup_data_db.ps1 + push_dump.ps1 + prune tedy spousti bud admin-owned Windows scheduled task, NEBO SQL Server Agent job (server ma MSSQL) - z PG mostu to nelze potvrdit. NUTNO overit adminem/RDP nebo v SQL Server Agent a doplnit sem.
3. E: (10 GB) je na zalohy poddimenzovany. Reseni: velke D: (viz disk-navrh pro CMIS) + presmerovat backup_data_db.ps1 / push_dump.ps1 / prune_pg_backups.ps1 z E:\STRATEGIE na D:\STRATEGIE (cesta je natvrdo v kodu, C:\Scripts je prepisatelny; dump bezi jako SYSTEM -> na D: zapise; zmena se chytne pri pristim dennim behu, restart netreba). Do apid_watcher.ps1 pridat D:\STRATEGIE do $CANDS. POZOR: dokud D: neni zvetseny, hlidat volno na D: (je na nem i produkcni DB - plne D: = vypadek DB).

## 30.11 (EC-SERVER2) - Plzen standby (DR cil)
- NSSM sluzba eurosoft-mcp - MCP ops/filesystem (Bearer, https://api.eurosoft.com/marti-mcp -> Caddy -> 127.0.0.1:8765). Self-update git pull (@@MCPUPDATE).
- Scheduled task STRATEGIE-DR-PullRestore (SYSTEM, 3:30) -> C:\scripts\dr_pull_restore.ps1 (stahne dump z Prahy, pg_restore do lokalni data_db). Opraveno 27.7. (ErrorActionPreference).
- STRATEGIE-DR-SelfCheck (3:45) - kontrola cerstvosti dat -> fw.dr_selfcheck.
- Plzen watcher (na Marti NB, ne na serveru) - relay CLAUDE_SQL bridge -> Praha diag-sql.

## DR retez (denni, cely)
3:00 dump na 188.12 (backup_data_db.ps1 -> E:\STRATEGIE) -> 3:15 push_dump.ps1 -> Praha POST /api/v1/ops/dr/upload -> 3:30 30.11 STRATEGIE-DR-PullRestore stahne + pg_restore -> 3:45 self-check.

## POTVRZENO 27.7 (RDP diag) - spoustece na 188.12 = Windows scheduled tasky (vse RunAs SYSTEM)
- STRATEGIE-data-db-backup   @3:00  -> powershell -File C:\scripts\backup_data_db.ps1  (dump do E:\STRATEGIE)
- STRATEGIE-DR-Push          @3:15  -> C:\scripts\push_dump.ps1  (push RAW do Prahy /dr/upload)
- STRATEGIE-PG-Backup-Prune  @3:30  -> C:\Scripts\prune_pg_backups.ps1  (retence 11 dni)
- STRATEGIE-DiskWatch        @30min -> C:\ProgramData\STRATEGIE-DiskWatch\check.ps1  (plni fw.disk_monitor)
NEJSOU to NSSM sluzby ani SQL Server Agent joby - jsou to scheduled tasky vlastnene SYSTEM/adminem, proto je neadmin ucet (NETWORK SERVICE, pod kterym bezi PG + fw.ops_run) v schtasks nevidel. Bod 2 z 'NEPORADEK' timto vyresen.


## HOTOVO 27.7: presmerovani zaloh E: -> D: (overeno)
Skripty backup_data_db.ps1 / push_dump.ps1 / prune_pg_backups.ps1 prepnuty z E:\STRATEGIE na D:\STRATEGIE, retence sjednocena na 11 dni (30 v backup_data_db.ps1 srovnano na 11 = shoda s prune). apid_watcher.ps1 ma D:\STRATEGIE v $CANDS jako prvni. Test (schtasks /run jako admin): dump 759 MB na D:\STRATEGIE\2026-07-27, push do Prahy OK za 16.4s. Zalohy skriptu: C:\Scripts\*.bak_20260727_132052. Nocni run 3:00/3:15/3:30 nyni jede na D:.
- ZBYVA: stare dumpy na E:\STRATEGIE uz nic nepruneuje (prune presel na D:) - smazat pri ruseni E: (CMIS).

## STROP AUTONOMIE na 188.12 (dulezite k fw.ops_run)
fw.ops_run / COPY FROM PROGRAM bezi jako NT AUTHORITY\NETWORK SERVICE. UMI: spoustet prikazy, cist libovolne soubory (pg_read_file, superuser), VYTVARET nove soubory v C:\Scripts. NEUMI: PREPSAT stavajici admin-vlastnene soubory (WriteAllText -> AccessDenied), zapsat do korene D:\, menit/spoustet scheduled tasky (schtasks /run) ani sluzby - to vse potrebuje admin (RDP) nebo ucet tasku (SYSTEM). POZOR: WriteAllText na nepovoleny soubor NEHODI viditelnou chybu pres COPY FROM PROGRAM (stderr mimo zaznam), skript klamne rekne EDITED - vzdy overovat pres mtime (pg_stat_file). Postup uprav skriptu: apply_*.ps1 nahrat do C:\Scripts (umim), ale SPUSTIT musi admin.


## HOTOVO 27.7: presun starych zaloh E: -> D: + E:/F: vyprazdneny
robocopy E:\STRATEGIE D:\STRATEGIE /E /MOVE (admin) - presunuto 12 dennich slozek (2026-07-16..27). Na D:\STRATEGIE nyni 13 dumpu (~8.4 GB), 2026-07-27 ma 2 (ranni 3:00 + testovaci). E: i F: nyni PRAZDNE. Vse (DB data + dokumenty + zalohy) je na D:. Retence 11 dni (prune 3:30) drzi ~11-12 slozek.
- DOPAD NA CMIS/disk navrh: puvodni navrh (velke D:, zrusit E:/F:) je tim pripraveny - zalohy uz jsou na D:, E:/F: jdou zrusit a jejich misto (2x10 GB) pridat k D:. Aktualizovat disk-navrh pro CMIS podle toho.


## HOTOVO 29.7: externi pristup DR - strategie-system.com (Plzen 30.11)
Caddy na 30.11 (C:\caddy\Caddyfile, sluzba "Caddy", admin port 2019, LE email m.pasek@eurosoft.com) serviruje:
- api.eurosoft.com -> /marti-mcp/ -> localhost port 8765 (MCP), /ondra-mcp/ -> 8766
- strategie-system.com -> reverse_proxy 127.0.0.1 port 8080 (STRATEGIE app = ziva DR zaloha nad lokalni obnovenou data_db). Bind 127.0.0.1 192.168.30.11.
Stav 29.7.: blok v Caddyfile PLATNY (caddy validate rc=0), Caddy reloadnut (rc=0), STRATEGIE-API na 30.11 RUNNING, Caddy drzi PLATNY LE certifikat pro strategie-system.com (cert_hash d4f33b39..., expiry ~2026-10, aktivni ACME renewal). DNS na 30.11 presmeroval Michal. => uzivatel muze zadat strategie-system.com misto strategie-ai.com a pracovat dal (RTO ~okamzite dle DR planu id 115).
Pozn.: WebFetch z Cowork cloudu na strategie-system.com = ConnectTimeout (IP datacentra mimo povolene zdroje); platny LE cert ale dokazuje verejnou dosazitelnost na portech 80/443. Realny test = prohlizec uzivatele.

## MCP 30.11 rozsireni 29.7
- filesystem_tools.py: C:\caddy pridano do RW roots (cteni/zapis Caddyfile bez RDP).
- ops_tools.py: nove GREEN akce eurosoft_ops_run: caddy_validate a caddy_reload (reload atomicky - spatny config odmitnut, stary bezi dal). Commit f9dff3945 / MCP git_sha f79219b2.
- GOTCHA: @@MCPUPDATE na 30.11 selhalo 2x (git credential-manager-core is not a git command + Cannot rebase onto multiple branches), napotreti proslo. Git na 30.11 ma vadny credential helper - srovnat pri RDP (git config credential.helper), jinak self-update obcas nechytne.


## 29.7: denik obnov (audit) - body 3 a 4
#4 OVERENO funkcni: stavova stranka GET /app/dr/status (posledni verdikt + 14denni historie, cockpit) + denik fw.dr_selfcheck (psan denne 3:45 z PLZEN) + push pri NENI_OK do fw.mobile_command (overeno - pushe 21/23/25/26/27.7 vznikly; po oprave restoru 28+29.7 verdikt OK, data cerstva ~4-5h).
#3 PRICINA: muj 27.7 prepis dr_pull_restore.ps1 vynechal krok archivace stazeneho dumpu -> 30denni historie na Plzni (D:\STRATEGIE_ARCHIVE) zamrzla (posledni datovany dump 07-24/27). check.ps1 (C:\ProgramData\STRATEGIE-DRCheck\check.ps1, SYSTEM, 3:45) cte retez z D:\STRATEGIE_ARCHIVE dle mtime a POSILA na /dr/selfcheck - cte spravne, jen se archiv neplnil.
#3 OPRAVA (nasazeno): dr_pull_restore.ps1 po uspesne obnove (rc 0 nebo 1 = normal u --clean) kopiruje dump do D:\STRATEGIE_ARCHIVE\data_db_<yyyy-MM-dd>.dump + prune na 30 dni. dr_ops.py verdikt nove hlida cerstvost retezu (nejnovejsi archiv starsi nez 2 dny -> NENI_OK) = denik sam odhali, kdyz archivace spadne. Naplni se od nocniho behu 3:30.
POZOR k proverit: blue-green /dr/meta vs /dr/download byva v poledne nekonzistentni (rucni dr_task_run spadl na "Velikost nesedi"; meta hlasila 43h stary dump 766MB = 28.7, ackoli push 29.7 3:15 781MB OK). Nocni pull 3:30 konzistentni (self-check zeleny). Stare archivy 07-25/26/27 jsou duplikaty (stejna velikost) z rozbite ery - vyprsi pres 30d prune.


## 29.7: denik obnov i v mobilni Appce
Karta "Denni obnova zalohy (DR Plzen)" pridana do mobile.html - sekce "Vedeni firmy" > "OBNOVA (DR ZALOHA PLZEN)", zrcadli cockpit /marti (verdikt, stari dat, pocty, retez X/30, 14denni historie), fetch /app/dr/status, gated rodic/HR (endpoint sam skryje pro ostatni). Commit 21c401244. Cockpit (ERP) = /marti; App = Vedeni firmy. Push pri chybe chodil uz predtim (fw.mobile_command).


## 29.7 vecer: kde jsou zalohy + oprava partial-file
Marti hlasil "DB obnovena, ale soubor z dneska 3:00 v archivu neni". Zjisteno:
- Autoritativni 30denni historie dumpu je na 188.12 D:\STRATEGIE\<datum>\ (dnes data_db_030002.dump 782 MB) + posledni push na Prahe. Data NEJSOU ztracena.
- Na Plzni se DB obnovuje z pracovni kopie D:\STRATEGIE_IN\data_db_030002.dump (prepisovana kazdy den). Datovana kopie na Plzni (D:\STRATEGIE_ARCHIVE) se od 27.7 neplnila = regrese #3 (uz opraveno, plni se od nocniho 3:30).
- V archivu 07-25/26/27 jsou duplikaty (stejny cas 24.7 3:30, stejna velikost 716717 kB) z rozbite ery - vyprsi pres 30d prune.
- Muj dopoledni rucni dr_task_run spadl na "Velikost nesedi" (blue-green /dr/meta vs /dr/download) a NECHAL v D:\STRATEGIE_IN useknuty partial 234 MB pres funkcni soubor. OPRAVENO: dr_pull_restore.ps1 stahuje do $dest.part, overi velikost, teprve pak Move-Item; pri nesouladu/chybe partial smaze. Funkcni pracovni kopie uz se nemuze prepsat partialem. Nocni beh 3:30 partial prepise cerstvym stazenim (size mismatch -> refetch).


