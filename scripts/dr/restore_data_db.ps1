# restore_data_db.ps1 - DR Den 2: obnov data_db z nejnovejsiho dumpu (plzensky box).
# Bezi jako denni scheduled task PO prenosu dumpu z Prahy. ASCII-only (#110).
# Vstup: nejnovejsi *.dump v -Incoming (kam prenosovy krok slozi dump z Prahy).
# Vystup: restore do lokalni data_db + log. Idempotentni (--clean --if-exists).
param(
  [string]$Incoming = 'D:\STRATEGIE_IN',
  [string]$Db       = 'data_db',
  [string]$PgBin    = 'C:\Program Files\PostgreSQL\16\bin'
)
$ErrorActionPreference = 'Stop'
$log = Join-Path $Incoming '_restore.log'
function Log($m){ $l = ('{0}  {1}' -f ([DateTime]::Now.ToString('s')), $m); Write-Output $l; try{ Add-Content -Path $log -Value $l -Encoding UTF8 }catch{} }

if(-not (Test-Path $Incoming)){ Log ("Incoming chybi: " + $Incoming); exit 1 }
$isready = Join-Path $PgBin 'pg_isready.exe'
& $isready -h localhost | Out-Null
if($LASTEXITCODE -ne 0){ Log "PostgreSQL neni ready (pg_isready fail)"; exit 1 }

$dump = Get-ChildItem $Incoming -Recurse -Filter *.dump -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $dump){ Log "Zadny *.dump v Incoming."; exit 0 }

Log ("Restore start: " + $dump.FullName + " -> " + $Db)
$restore = Join-Path $PgBin 'pg_restore.exe'
$t0 = Get-Date
& $restore -h localhost -U postgres -d $Db --clean --if-exists --no-owner $dump.FullName 2>&1 |
  ForEach-Object { Log ("  " + $_) }
$rc = $LASTEXITCODE
$sec = [math]::Round(((Get-Date) - $t0).TotalSeconds,1)
if($rc -eq 0){ Log ("Restore OK za " + $sec + "s (dump " + $dump.Name + ")") }
else { Log ("Restore FAIL rc=" + $rc + " po " + $sec + "s"); exit $rc }
