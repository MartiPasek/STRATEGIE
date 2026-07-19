# DR Den 1 — Instalace PostgreSQL 16 na plzeňském boxu (RDP)

**Kdo:** člověk přes RDP (červená kategorie — instalace SW; MCP to nespustí).
**Cíl:** na plzeňském serveru běží PostgreSQL 16 s prázdnou DB `data_db` = cíl pro denní restore.
**Čas:** ~10 minut. Vše jako **admin PowerShell** na tom boxu.

> Za `HESLO_POSTGRES` a `DATADIR` dosaď reálné hodnoty (viz kroky). Heslo si ulož (dáme ho do `.pgpass`).

## 1) Stáhni instalátor PostgreSQL 16 (EDB, Windows x64)
Pokud má box internet:
```powershell
$inst = "$env:TEMP\pg16-setup.exe"
Invoke-WebRequest -Uri "https://get.enterprisedb.com/postgresql/postgresql-16.9-1-windows-x64.exe" -OutFile $inst
```
Bez internetu: stáhni ten .exe na stroj s netem a zkopíruj na box (RDP schránka / UNC), pak `$inst = "C:\cesta\pg16-setup.exe"`.

## 2) Vyber datadir (na datovém disku, ne C:)
```powershell
$DATADIR = "D:\PostgreSQL\16\data"     # uprav dle disků boxu (kde je místo)
New-Item -ItemType Directory -Force -Path (Split-Path $DATADIR) | Out-Null
```

## 3) Silent install
```powershell
$PW = "HESLO_POSTGRES"                  # <-- zvol silné heslo superusera 'postgres'
& $inst --mode unattended --unattendedmodeui minimal `
  --superpassword $PW --serverport 5432 `
  --prefix "C:\Program Files\PostgreSQL\16" --datadir $DATADIR `
  --servicename "postgresql-x64-16"
```
Počkej, než doběhne (služba `postgresql-x64-16` se založí a nastartuje).

## 4) Ověř běh + vytvoř data_db
```powershell
$env:PGPASSWORD = $PW
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
& "C:\Program Files\PostgreSQL\16\bin\pg_isready.exe" -h localhost        # ma vratit "accepting connections"
& $psql -U postgres -h localhost -c "CREATE DATABASE data_db;"
& $psql -U postgres -h localhost -c "\l" | Select-String data_db
Remove-Item Env:\PGPASSWORD
```

## 5) `.pgpass` pro automatický restore (SYSTEM profil = běží pod scheduled taskem)
```powershell
$pp = "C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql"
New-Item -ItemType Directory -Force -Path $pp | Out-Null
Set-Content -Path "$pp\pgpass.conf" -Value "localhost:5432:data_db:postgres:HESLO_POSTGRES" -Encoding ASCII -NoNewline
```

## 6) Firewall (jen pokud budeš k PG přistupovat po síti; pro lokální restore NETŘEBA)
```powershell
# New-NetFirewallRule -DisplayName "PostgreSQL 5432" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow
```

## Hotovo když:
- `pg_isready` = accepting connections,
- `\l` ukazuje `data_db`,
- existuje `...\systemprofile\...\postgresql\pgpass.conf`.

Pak napiš Claudovi „PG stojí" → jede Den 2 (restore skript + denní task).
