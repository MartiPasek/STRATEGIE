# setup_apid_watcher_service.ps1 - zaregistruje apid_watcher jako NSSM sluzbu.
# Marti 16.6.2026. ASCII-only. Spousti se na DATOVEM serveru (10.200.188.12) jako admin.
# Watcher pak bezi porad (i po odhlaseni/restartu) a bere pozadavky obnovy z appky.
#
# Heslo postgres se dava do AppEnvironmentExtra (doctrine: ne Machine env).
# __HESLO__ nahrad skutecnym heslem PRED spustenim (nebo dopln nssm set prikazem nize).

$ErrorActionPreference = "Stop"

# --- konfigurace (uprav dle reality na .12) ---
$NSSM   = "C:\Tools\nssm.exe"            # kde je nssm.exe na .12 (zkopiruj z APP, kdyz neni)
$SVC    = "STRATEGIE-APID-WATCHER"
$SCRIPT = "C:\Scripts\apid_watcher.ps1"  # kam jsi ulozil watcher
$PSEXE  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$PGPASS = "__HESLO__"                    # heslo postgres
# ----------------------------------------------

if (-not (Test-Path $NSSM))   { throw "nssm.exe nenalezen: $NSSM (zkopiruj z APP serveru nebo stahni)" }
if (-not (Test-Path $SCRIPT)) { throw "watcher nenalezen: $SCRIPT" }

Write-Host "== Registruji sluzbu $SVC ==" -ForegroundColor Cyan
& $NSSM install $SVC $PSEXE "-NoProfile -ExecutionPolicy Bypass -File `"$SCRIPT`""
& $NSSM set $SVC AppDirectory (Split-Path $SCRIPT)
& $NSSM set $SVC AppEnvironmentExtra ("PGPASSWORD=" + $PGPASS)
& $NSSM set $SVC Start SERVICE_AUTO_START
& $NSSM set $SVC AppStdout "C:\Scripts\apid_watcher.log"
& $NSSM set $SVC AppStderr "C:\Scripts\apid_watcher.err.log"
& $NSSM set $SVC AppRotateFiles 1
& $NSSM set $SVC AppRotateBytes 5000000

Write-Host "== Startuji ==" -ForegroundColor Cyan
& $NSSM start $SVC
Start-Sleep -Seconds 2
& $NSSM status $SVC

Write-Host ""
Write-Host "Hotovo. Watcher bezi jako sluzba $SVC (auto-start)." -ForegroundColor Green
Write-Host "Log: C:\Scripts\apid_watcher.log"
Write-Host "Kdyby heslo nesedelo: nssm set $SVC AppEnvironmentExtra PGPASSWORD=skutecne_heslo ; nssm restart $SVC"
