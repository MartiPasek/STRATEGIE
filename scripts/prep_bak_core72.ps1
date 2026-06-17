# prep_bak_core72.ps1 - pripravi schema "bak" (jen core 72) z data_db_test do produkcni data_db.
# Zadani od Claude-24 (varianta B): Claude-23 pripravi bak, Claude-24 pak chirurgicky apply.
# BEZI NA DATOVEM SERVERU (10.200.188.12), kde jsou data_db i data_db_test LOKALNE.
# ASCII-only (doctrine #110). Heslo: PGPASSWORD v env nebo .pgpass (NEdavat sem).
# Spust v PowerShellu:  .\prep_bak_core72.ps1
#
# PREDPOKLAD: data_db_test uz obsahuje PONDELNI zalohu (15.6.). Kdyz ne, skript STOPne
#   v kroku 0 - obnov pondelni .dump (restore_to_apid.ps1 -List) a spust znovu.
# Produkcnich fw.* se NEDOTYKA - jen vytvori a naplni schema bak.

$ErrorActionPreference = "Stop"
$PGUSER = "postgres"
$H      = "10.200.188.12"   # DB server (po siti, jako restore_to_apid.ps1). Na DB serveru klidne "localhost".
$PROD   = "data_db"
$TEST   = "data_db_test"
$TMP    = "C:\Temp"

# psql/pg_dump v PATH (jako u apid_watcher)
$pgbin = @("C:\Program Files\PostgreSQL\16\bin","C:\Program Files\PostgreSQL\15\bin",
           "C:\Program Files\PostgreSQL\17\bin","C:\Program Files\PostgreSQL\14\bin") |
         Where-Object { Test-Path $_ } | Select-Object -First 1
if ($pgbin -and ($env:Path -notlike "*$pgbin*")) { $env:Path = $pgbin + ";" + $env:Path }
if (-not (Test-Path $TMP)) { New-Item -ItemType Directory -Path $TMP | Out-Null }

function Q([string]$db, [string]$sql) {
  return ((& psql -h $H -U $PGUSER -d $db -v ON_ERROR_STOP=1 -t -A -c $sql) | Out-String).Trim()
}

Write-Host "== 0) Kontrola, ze data_db_test je PONDELNI rano (core 72) ==" -ForegroundColor Cyan
$cnt    = Q $TEST "SELECT count(*) FROM fw.comp_def WHERE core_id=72;"
$has288 = Q $TEST "SELECT count(*) FROM fw.comp_def WHERE core_id=72 AND id=288;"
$has792 = Q $TEST "SELECT count(*) FROM fw.comp_def WHERE core_id=72 AND id=792;"
Write-Host ("   comp_def(core72)=" + $cnt + "  id288=" + $has288 + "  id792=" + $has792)
if ($has288 -ne "1" -or $has792 -ne "0") {
  Write-Host "STOP: data_db_test NENI pondelni rano (ocekavam id288=1 a id792=0)." -ForegroundColor Red
  Write-Host "      Obnov spravny pondelni .dump:  .\restore_to_apid.ps1 -List  -> vyber pondelni -> restore, pak spust znovu." -ForegroundColor Yellow
  return
}
Write-Host "   OK - 288 ano / 792 ne -> je to pondelni rano." -ForegroundColor Green

Write-Host "== 1) Vytvarim schema bak + 5 tabulek v produkci ($PROD) (fw.* se NEDOTYKAM) ==" -ForegroundColor Cyan
$ddl = "CREATE SCHEMA IF NOT EXISTS bak;" +
  "DROP TABLE IF EXISTS bak.comp_def;       CREATE TABLE bak.comp_def       (LIKE fw.comp_def       INCLUDING DEFAULTS);" +
  "DROP TABLE IF EXISTS bak.data_source_op; CREATE TABLE bak.data_source_op (LIKE fw.data_source_op INCLUDING DEFAULTS);" +
  "DROP TABLE IF EXISTS bak.core;           CREATE TABLE bak.core           (LIKE fw.core           INCLUDING DEFAULTS);" +
  "DROP TABLE IF EXISTS bak.data_set;       CREATE TABLE bak.data_set       (LIKE fw.data_set       INCLUDING DEFAULTS);" +
  "DROP TABLE IF EXISTS bak.data_source;    CREATE TABLE bak.data_source    (LIKE fw.data_source    INCLUDING DEFAULTS);"
& psql -h $H -U $PGUSER -d $PROD -v ON_ERROR_STOP=1 -c $ddl | Out-Null
# Prava pro roli "Marti-AI" (pod tou cte bridge - Claude-23 i Claude-24), jinak "permission denied for schema bak".
& psql -h $H -U $PGUSER -d $PROD -v ON_ERROR_STOP=1 -c 'GRANT USAGE ON SCHEMA bak TO "Marti-AI"; GRANT SELECT ON ALL TABLES IN SCHEMA bak TO "Marti-AI";' | Out-Null

function Copy-One([string]$selectSql, [string]$target, [string]$csv) {
  $p = Join-Path $TMP $csv
  & psql -h $H -U $PGUSER -d $TEST -v ON_ERROR_STOP=1 -c ("\copy (" + $selectSql + ") TO '" + $p + "' (FORMAT csv)") | Out-Null
  & psql -h $H -U $PGUSER -d $PROD -v ON_ERROR_STOP=1 -c ("\copy " + $target + " FROM '" + $p + "' (FORMAT csv)") | Out-Null
  Remove-Item $p -ErrorAction SilentlyContinue
  Write-Host ("   kopirovano -> " + $target)
}

Write-Host "== 2) Kopiruji data data_db_test -> bak (presne, vsechny sloupce vcetne id) ==" -ForegroundColor Cyan
Copy-One "SELECT * FROM fw.comp_def WHERE core_id=72"       "bak.comp_def"       "bak_comp_def.csv"
Copy-One "SELECT * FROM fw.data_source_op WHERE core_id=72" "bak.data_source_op" "bak_dso.csv"
Copy-One "SELECT * FROM fw.core WHERE id=72"                "bak.core"           "bak_core.csv"
Copy-One "SELECT * FROM fw.data_set"                        "bak.data_set"       "bak_data_set.csv"
Copy-One "SELECT * FROM fw.data_source"                     "bak.data_source"    "bak_data_source.csv"

Write-Host "== 3) Kontrola v produkci (bak) ==" -ForegroundColor Cyan
$chk = Q $PROD ("SELECT 'comp_def='||(SELECT count(*) FROM bak.comp_def)||" +
  "' | 288='||(SELECT count(*) FROM bak.comp_def WHERE id=288)||" +
  "' | 792='||(SELECT count(*) FROM bak.comp_def WHERE id=792)||" +
  "' | dso='||(SELECT count(*) FROM bak.data_source_op)||" +
  "' | data_set='||(SELECT count(*) FROM bak.data_set)||" +
  "' | data_source='||(SELECT count(*) FROM bak.data_source);")
Write-Host ("   " + $chk) -ForegroundColor Green
Write-Host ""
Write-Host "HOTOVO. Schema bak.* je pripravene v produkci. comp_def ma byt ~40, 288=1, 792=0." -ForegroundColor Green
Write-Host "Napis Kristy / Claude-24, ze bak.* je hotove (a posli radek kontroly vyse)." -ForegroundColor Green
