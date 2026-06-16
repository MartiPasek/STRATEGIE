# restore_to_apid.ps1 - obnova vybrane zalohy data_db do testovaci DB (API D).
# Marti 16.6.2026. ASCII-only. Spousti se na CLOUD APP. Produkce se NEDOTKNE.
# Pouziti:  .\restore_to_apid.ps1 "nazev_zalohy.dump"     (soubor v $BACKUPDIR)
#           .\restore_to_apid.ps1 -List                  (vypis dostupnych zaloh)
# Heslo: PGPASSWORD v env nebo .pgpass (NEdavat sem).

param([string]$File, [switch]$List)
$ErrorActionPreference = "Stop"

# --- konfigurace (uprav dle reality) ---
$PGHOST    = "10.200.188.12"
$PGUSER    = "postgres"
$TESTDB    = "data_db_test"
$BACKUPDIR = "C:\Backup"
$NSSM      = "C:\Tools\nssm.exe"
$SVC       = "STRATEGIE-API-D"
# ---------------------------------------

if ($List) {
  Write-Host "Dostupne zalohy v $BACKUPDIR :" -ForegroundColor Cyan
  Get-ChildItem $BACKUPDIR -File | Where-Object { $_.Extension -in ".dump",".backup",".sql" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, @{n="Velikost(MB)";e={[math]::Round($_.Length/1MB,1)}}, LastWriteTime |
    Format-Table -AutoSize
  return
}
if (-not $File) { Write-Host "Zadej nazev zalohy nebo -List." -ForegroundColor Yellow; return }

$path = Join-Path $BACKUPDIR $File
if (-not (Test-Path $path)) { throw "Zaloha neexistuje: $path" }

Write-Host "== Obnova '$File' do $TESTDB (NE do produkce) ==" -ForegroundColor Cyan
Write-Host "1) Zastavuji API D, aby nedrzela spojeni..."
& $NSSM stop $SVC 2>$null

Write-Host "2) Drop + create $TESTDB ..."
& dropdb   -h $PGHOST -U $PGUSER --if-exists $TESTDB
& createdb -h $PGHOST -U $PGUSER $TESTDB

Write-Host "3) pg_restore (nebo psql pro .sql) ..."
if ($File -like "*.sql") {
  & psql -h $PGHOST -U $PGUSER -d $TESTDB -f $path
} else {
  & pg_restore -h $PGHOST -U $PGUSER -d $TESTDB --no-owner --clean --if-exists $path
}

Write-Host "4) Start API D ..."
& $NSSM start $SVC

Write-Host "Hotovo. API D bezi na obnovenych datech ze zalohy '$File'." -ForegroundColor Green
Write-Host "Otevri: https://strategie-ai.com/apid/   (neziva data - bez odchozich akci)"
