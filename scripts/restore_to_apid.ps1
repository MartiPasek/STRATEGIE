# restore_to_apid.ps1 - obnova vybrane zalohy data_db do testovaci DB (API D).
# Marti 16.6.2026. ASCII-only. Spousti se na CLOUD APP. Produkce se NEDOTKNE.
#
# Rezimy:
#   .\restore_to_apid.ps1 -List                 vypis dostupnych zaloh
#   .\restore_to_apid.ps1 "zaloha.dump"         jednorazova obnova konkretni zalohy
#   .\restore_to_apid.ps1 -Watch                WATCHER: ceka na pozadavek z appky
#                                               (C:\Backup\_apid_restore.req) a obnovi
#                                               -> takhle to jede "na klik" z appky.
# Heslo: PGPASSWORD v env nebo .pgpass (NEdavat sem).

param([string]$File, [switch]$List, [switch]$Watch)
$ErrorActionPreference = "Stop"

# --- konfigurace (uprav dle reality) ---
$PGHOST    = "10.200.188.12"
$PGUSER    = "postgres"
$TESTDB    = "data_db_test"
$BACKUPDIR = "C:\Backup"
$NSSM      = "C:\Tools\nssm.exe"
$SVC       = "STRATEGIE-API-D"
$REQ       = Join-Path $BACKUPDIR "_apid_restore.req"
$OUT       = Join-Path $BACKUPDIR "_apid_restore.out"
# ---------------------------------------

function Do-Restore([string]$fname) {
  $path = Join-Path $BACKUPDIR $fname
  if (-not (Test-Path $path)) { throw "Zaloha neexistuje: $path" }
  Write-Host "== Obnova '$fname' do $TESTDB (NE do produkce) =="
  & $NSSM stop $SVC 2>$null
  & dropdb   -h $PGHOST -U $PGUSER --if-exists $TESTDB
  & createdb -h $PGHOST -U $PGUSER $TESTDB
  if ($fname -like "*.sql") {
    & psql -h $PGHOST -U $PGUSER -d $TESTDB -f $path
  } else {
    & pg_restore -h $PGHOST -U $PGUSER -d $TESTDB --no-owner --clean --if-exists $path
  }
  & $NSSM start $SVC
  Write-Host "Hotovo. API D bezi na datech ze zalohy '$fname'."
}

function Write-Out([bool]$ok, [string]$fname, [string]$err) {
  $o = @{ ok = $ok; file = $fname; finished = (Get-Date).ToString("dd.MM.yyyy HH:mm"); error = $err } | ConvertTo-Json -Compress
  Set-Content -Path $OUT -Value $o -Encoding UTF8
}

if ($List) {
  Get-ChildItem $BACKUPDIR -File | Where-Object { $_.Extension -in ".dump",".backup",".sql" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}, LastWriteTime | Format-Table -AutoSize
  return
}

if ($Watch) {
  Write-Host "WATCHER bezi. Cekam na pozadavky obnovy z appky ($REQ)... Ctrl+C ukonci." -ForegroundColor Cyan
  while ($true) {
    try {
      if (Test-Path $REQ) {
        $req = Get-Content $REQ -Raw | ConvertFrom-Json
        $fname = $req.file
        Remove-Item $REQ -Force
        Write-Host ("[" + (Get-Date).ToString("HH:mm:ss") + "] Pozadavek: " + $fname)
        try { Do-Restore $fname; Write-Out $true $fname "" }
        catch { Write-Host ("CHYBA: " + $_.Exception.Message) -ForegroundColor Red; Write-Out $false $fname $_.Exception.Message }
      }
    } catch { Write-Host ("watcher chyba: " + $_.Exception.Message) -ForegroundColor Yellow }
    Start-Sleep -Seconds 8
  }
}

if (-not $File) { Write-Host "Zadej nazev zalohy, -List nebo -Watch." -ForegroundColor Yellow; return }
try { Do-Restore $File; Write-Out $true $File "" }
catch { Write-Out $false $File $_.Exception.Message; throw }
Write-Host "Otevri: https://strategie-ai.com/apid/   (neziva data - bez odchozich akci)"
