# SQL Server — Daily backup data_db setup

**Datum:** 9. 5. 2026 (Phase 38.4 Krok 7 — Marti's *„C zitra"* z dne)
**Cíl:** Automatický daily backup `data_db` na cloud SQL serveru
(10.200.188.12) přes Windows Task Scheduler v 3:00 ráno.

## Architektura

```
SQL server 10.200.188.12
├── PostgreSQL 16 (běží lokálně na :5432)
├── data_db (target)
├── C:\scripts\backup_data_db.ps1 (PS skript, volá pg_dump localhost)
├── E:\STRATEGIE\YYYY-MM-DD\data_db_HHMMSS.dump (output, retention 30 dní)
├── Windows Task Scheduler "STRATEGIE-data-db-backup"
│   └── Daily 3:00, run as SYSTEM
└── .pgpass v SYSTEM profilu (auth bez prompt)
```

## Setup (one-shot, RDP do SQL serveru, admin PowerShell)

### Krok 1 — Vytvoř adresáře

```powershell
New-Item -Path "C:\scripts" -ItemType Directory -Force
New-Item -Path "E:\STRATEGIE" -ItemType Directory -Force
```

### Krok 2 — Zkopíruj skript

Z NB (D:\Projekty\STRATEGIE\scripts\backup_data_db_sqlserver.ps1) zkopíruj
na SQL server jako:

```
C:\scripts\backup_data_db.ps1
```

(Lze přes RDP clipboard, UNC `\\10.200.188.12\C$\scripts\` z NB,
nebo `git pull` pokud máš repo i na SQL serveru.)

### Krok 3 — Vytvoř `.pgpass` v SYSTEM profilu

SYSTEM user profil je v:
```
C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql\
```

Tahle cesta typicky neexistuje. Vytvoř ji + `pgpass.conf`:

```powershell
$systemPgPass = "C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql"
New-Item -Path $systemPgPass -ItemType Directory -Force

# Vytvor pgpass.conf s heslem postgres usera.
# Format: hostname:port:database:username:password
$pgPassContent = "localhost:5432:data_db:postgres:HESLO_TADY"
Set-Content -Path "$systemPgPass\pgpass.conf" -Value $pgPassContent -Encoding ASCII -NoNewline
```

**⚠ HESLO_TADY = skutečné heslo postgres usera na SQL serveru.**
Marti ho zná (dnes večer při GRANT debug ho zadal v SSMS).

### Krok 4 — Manuální smoke test

Spusť skript ručně **pod SYSTEM userem** (přes `psexec` z Sysinternals,
nebo přímo v Task Scheduler s "Run now"):

```powershell
# Varianta A: standalone test pod aktuálním adminem
# (pokud má .pgpass v Administrator profilu — jinak Variant B)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\scripts\backup_data_db.ps1

# Varianta B: test pod SYSTEM (psexec.exe z Sysinternals)
psexec.exe -i -s powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File C:\scripts\backup_data_db.ps1
```

Očekávaný výstup:
```
[INFO] 2026-05-09 234500: backup start -> E:\STRATEGIE\2026-05-09\data_db_234500.dump
[INFO] pg_dump: C:\Program Files\PostgreSQL\16\bin\pg_dump.exe
[OK] Backup hotovy: 12.34 MB za 5.7s
[DONE] 2026-05-09 234500
```

### Krok 5 — Register Scheduled Task

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\scripts\backup_data_db.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At 3:00am

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName "STRATEGIE-data-db-backup" `
    -Description "Phase 38.4: Daily data_db backup pres pg_dump (3:00 rano, retention 30 dni)" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings
```

### Krok 6 — Test via Task Scheduler

```powershell
Start-ScheduledTask -TaskName "STRATEGIE-data-db-backup"

# Po par sekundach zkontroluj
Get-ScheduledTaskInfo -TaskName "STRATEGIE-data-db-backup"
# LastRunTime + LastTaskResult (0 = OK, jinak exit code)

# Plus zkontroluj E:\STRATEGIE\YYYY-MM-DD\
Get-ChildItem "E:\STRATEGIE" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
    Get-ChildItem | Format-Table Name, Length, LastWriteTime
```

## Restore (kdyby bylo potřeba)

```powershell
# pg_restore z konkretni zalohy do nove DB (nebo --clean pro overwrite)
& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" `
    -h localhost -p 5432 -U postgres `
    -d data_db_restore `
    --no-owner `
    --verbose `
    "E:\STRATEGIE\2026-05-09\data_db_030001.dump"
```

## Troubleshooting

### Task hlásí exit code != 0

Zkontroluj v Task Scheduler History (vyžaduje Event Log enable v Settings):
- **0x1** = obecná chyba (často auth — `.pgpass` chybí nebo špatné heslo)
- **0x2** = soubor nenalezen (pg_dump nebo skript)
- **timeout 30 min** — DB příliš velká, zvýšit `-ExecutionTimeLimit`

### `.pgpass` nefunguje

Ověř obsah a permissions:

```powershell
Get-Content C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql\pgpass.conf
# Musi byt: localhost:5432:data_db:postgres:<heslo>
# BEZ trailing newline (-NoNewline v Set-Content)
```

PostgreSQL ignoruje `.pgpass` pokud má příliš permissive permissions
na *NIX, na Windows kontrola slabší — stačí, že SYSTEM má read.

### Heslo postgres usera neznám / zapomněl

```powershell
# Reset hesla z lokální admin PowerShell (vyžaduje superuser access):
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d postgres
# Pak v psql:
ALTER USER postgres PASSWORD 'nove_heslo';
\q
# Pak update .pgpass se stejnym heslem
```

## Vztah k UI backup tlačítku

UI dropdown *„Zálohovat databáze"* (Marti's profile menu) volá API
endpoint `POST /api/v1/admin/backup-databases` na **cloud APP serveru**
(10.200.188.11). To je **separátní** od daily SQL server backup:

| | Manuální (UI) | Auto (Task Scheduler) |
|---|---|---|
| Kde běží | Cloud APP 10.200.188.11 | Cloud SQL 10.200.188.12 |
| Spouští | Marti klik | Cron 3:00 ráno |
| pg_dump source | PG_DUMP_PATH na APP | Native v PATH na SQL |
| Connection | Přes network (10.200.188.12:5432) | Loopback localhost |
| Output | `C:\Backup\` na APP | `E:\STRATEGIE\` na SQL |
| Use case | Pre-deploy backup, ad-hoc | Disaster recovery |

**Oba dumpy jsou validní** — různé location je redundance, ne duplicita.

## Future improvements

- **OneDrive sync**: nakopírovat `E:\STRATEGIE\` do OneDrive denně (nebo
  weekly) pro off-site disaster recovery. Marti's pattern *„kopiruj
  rucne"* automatizovat přes scheduled task #2.
- **Email notifikace pri failu**: scheduled task on-fail trigger →
  send_email Marti přes STRATEGIE API. Vyžaduje: API endpoint pro
  external notify nebo SMTP fallback.
- **Health check dashboard**: ERP System soudeček nový grid
  *„Backups"* — list YYYY-MM-DD složek + jejich velikost + last
  successful run. Marti vidí v ERP UI.
