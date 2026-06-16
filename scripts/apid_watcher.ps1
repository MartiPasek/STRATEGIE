# apid_watcher.ps1 - WATCHER na DATOVEM serveru (10.200.188.12).
# Marti 16.6.2026. ASCII-only. Bezi tam, kde jsou ZALOHY a PostgreSQL.
#
# Co dela ve smycce:
#   1) Najde slozku se zalohami (projde i disk E:) a vypise seznam do tabulky
#      fw.apid_backup (appka z ni cte "seznam zaloh").
#   2) Vezme cekajici pozadavek z fw.apid_restore_req (status pending), obnovi
#      vybranou zalohu do data_db_test (drop+create+pg_restore) a zapise vysledek.
#   Produkce data_db se NEDOTKNE.
#
# Heslo postgres: PGPASSWORD v env nebo .pgpass (NEdavat sem).
# Spust:  .\apid_watcher.ps1            (smycka)
#         .\apid_watcher.ps1 -Once      (jeden pruchod - test)

param([switch]$Once)
$ErrorActionPreference = "Stop"

# --- konfigurace ---
$PGUSER = "postgres"
$MAINDB = "data_db"        # kde jsou fw.* tabulky (kanal)
$TESTDB = "data_db_test"   # cilova testovaci DB pro obnovu (API D)
# Kandidati slozky se zalohami - projde v tomto poradi, vezme prvni s nejakou zalohou.
# Marti: zalohy nejspis na E:. Pridej/uprav cesty dle reality.
$CANDS = @("E:\Backup","E:\Zalohy","E:\backup","E:\PostgreSQL\Backup","E:\",
           "C:\Backup","D:\Backup")
# -------------------

function PSQL([string]$db, [string]$sql) { & psql -h localhost -U $PGUSER -d $db -v ON_ERROR_STOP=1 -t -A -c $sql }

function Find-BackupDir() {
  foreach ($d in $CANDS) {
    if (Test-Path $d) {
      $f = Get-ChildItem $d -File -ErrorAction SilentlyContinue |
           Where-Object { $_.Extension -in ".dump",".backup",".sql" }
      if ($f) { return $d }
    }
  }
  return $null
}

function Publish-Backups([string]$dir) {
  $files = Get-ChildItem $dir -File | Where-Object { $_.Extension -in ".dump",".backup",".sql" }
  PSQL $MAINDB "TRUNCATE fw.apid_backup;" | Out-Null
  foreach ($x in $files) {
    $nm = $x.Name.Replace("'","''")
    $dr = $dir.Replace("'","''")
    $mb = [math]::Round($x.Length/1MB,1)
    $mt = $x.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    PSQL $MAINDB "INSERT INTO fw.apid_backup (name,dir,size_mb,mtime,listed_at) VALUES ('$nm','$dr',$mb,'$mt',now());" | Out-Null
  }
  Write-Host ("[" + (Get-Date).ToString("HH:mm:ss") + "] Publikovano zaloh: " + $files.Count + " z " + $dir)
}

function Process-Requests([string]$dir) {
  $id = (PSQL $MAINDB "SELECT id FROM fw.apid_restore_req WHERE status='pending' ORDER BY id LIMIT 1;").Trim()
  if (-not $id) { return }
  $file = (PSQL $MAINDB "SELECT file FROM fw.apid_restore_req WHERE id=$id;").Trim()
  Write-Host ("[" + (Get-Date).ToString("HH:mm:ss") + "] Obnova #$id : $file")
  PSQL $MAINDB "UPDATE fw.apid_restore_req SET status='running' WHERE id=$id;" | Out-Null
  try {
    $path = Join-Path $dir $file
    if (-not (Test-Path $path)) { throw "Zaloha neexistuje: $path" }
    & dropdb   -h localhost -U $PGUSER --if-exists $TESTDB
    & createdb -h localhost -U $PGUSER $TESTDB
    if ($file -like "*.sql") {
      & psql -h localhost -U $PGUSER -d $TESTDB -f $path
    } else {
      & pg_restore -h localhost -U $PGUSER -d $TESTDB --no-owner --clean --if-exists $path
    }
    $msg = ("Obnoveno do " + $TESTDB + " ze zalohy " + $file)
    PSQL $MAINDB "UPDATE fw.apid_restore_req SET status='done', result='$($msg.Replace("'","''"))', finished_at=now() WHERE id=$id;" | Out-Null
    Write-Host "  OK: $msg" -ForegroundColor Green
  } catch {
    $err = $_.Exception.Message.Replace("'","''")
    PSQL $MAINDB "UPDATE fw.apid_restore_req SET status='error', result='$err', finished_at=now() WHERE id=$id;" | Out-Null
    Write-Host ("  CHYBA: " + $_.Exception.Message) -ForegroundColor Red
  }
}

function Tick() {
  $dir = Find-BackupDir
  if (-not $dir) { Write-Host ("[" + (Get-Date).ToString("HH:mm:ss") + "] Zalohy nenalezeny v kandidatnich slozkach. Uprav `$CANDS.") -ForegroundColor Yellow; return }
  Publish-Backups $dir
  Process-Requests $dir
}

if ($Once) { Tick; return }
Write-Host "apid_watcher bezi (datovy server). Ctrl+C ukonci." -ForegroundColor Cyan
while ($true) { try { Tick } catch { Write-Host ("tick chyba: " + $_.Exception.Message) -ForegroundColor Yellow }; Start-Sleep -Seconds 15 }
