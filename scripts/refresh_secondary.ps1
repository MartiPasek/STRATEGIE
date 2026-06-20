# refresh_secondary.ps1
# Obnova zalozni (blue-green) instance: srovna slozku STRATEGIE-prev s aktualni
# primarni STRATEGIE a restartuje sluzbu STRATEGIE-API-B.
# Zaloha = co bezi, kdyby primarni API-A vypadlo. Spoustet na cloud APP jako Admin.
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File C:\Projekty\STRATEGIE\scripts\refresh_secondary.ps1
#   (volitelne -Deps  ... navic poetry install v zaloze, kdyz pribyly zavislosti)
#
# ASCII-only (doctrine #110 - PowerShell nema rad diakritiku/em-dash/sipky).

param(
  [string]$Src     = "C:\Projekty\STRATEGIE",
  [string]$Dst     = "C:\Projekty\STRATEGIE-prev",
  [string]$Service = "STRATEGIE-API-B",
  [string]$Nssm    = "C:\Tools\nssm.exe",
  [switch]$Deps
)

$ErrorActionPreference = "Stop"
function Log($m){ Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m) }

Log "=== Refresh zalozni instance ==="
Log ("Zdroj (primarni): {0}" -f $Src)
Log ("Cil   (zaloha)  : {0}" -f $Dst)
Log ("Sluzba          : {0}" -f $Service)

if(-not (Test-Path $Src)){ throw "Zdroj neexistuje: $Src" }
if(-not (Test-Path $Dst)){ throw "Cil (zaloha) neexistuje: $Dst" }

# 1) Zastav zalozni sluzbu, aby nebyly zamknute soubory pri kopirovani.
Log "1/4 Zastavuji $Service ..."
& $Nssm stop $Service | Out-Null
Start-Sleep -Seconds 2

# 2) Zrcadli kod + static z primarni do zalohy. Vynech venv/.git/cache/node_modules/logs,
#    aby se nezbouralo vlastni prostredi zalohy. /MIR = presna kopie (vc. mazani odstranenych).
Log "2/4 Kopiruji slozku (robocopy /MIR, bez venv/.git/cache) ..."
$excl = @(".git",".venv","venv","node_modules","__pycache__",".idea",".pytest_cache","logs")
robocopy $Src $Dst /MIR /XD $excl /XF *.pyc /R:1 /W:1 /NFL /NDL /NP /NJH /NJS | Out-Null
$rc = $LASTEXITCODE
# robocopy navratove kody: 0-7 = uspech, 8+ = chyba.
if($rc -ge 8){
  Log "robocopy CHYBA (exit=$rc) - startuji zpet $Service"
  & $Nssm start $Service | Out-Null
  throw "robocopy selhal (exit=$rc)"
}
Log "robocopy OK (exit=$rc; 1=zkopirovano, 0=nic noveho, oboje OK)"

# 3) Volitelne dorovnani zavislosti (kdyz pribyl novy pip balicek).
# POZOR: poetry pise normalni hlasky ("Creating virtualenv...") do stderr -> s
# ErrorActionPreference=Stop by to PowerShell vzal jako fatal a skript spadl PRED
# startem B (B by zustal zastaveny). Proto Continue + catch + start vzdy probehne.
if($Deps){
  Log "3/4 poetry install v zaloze ..."
  Push-Location $Dst
  $eap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    & python -m poetry install 2>&1 | ForEach-Object { Log ("  poetry: {0}" -f $_) }
    if($LASTEXITCODE -ne 0){ Log ("poetry install exit={0} (pokracuji, B zkusim nastartovat)" -f $LASTEXITCODE) }
    else { Log "poetry install OK" }
  } catch {
    Log ("poetry install vyjimka: {0} (pokracuji)" -f $_.Exception.Message)
  } finally {
    $ErrorActionPreference = $eap
    Pop-Location
  }
} else {
  Log "3/4 poetry install preskocen (kdyby zaloha nenabehla, spust znovu s -Deps)"
}

# 4) Nastartuj zalozni sluzbu.
Log "4/4 Startuji $Service ..."
& $Nssm start $Service | Out-Null
Start-Sleep -Seconds 3
$st = (& $Nssm status $Service)
Log ("Hotovo. Stav {0}: {1}" -f $Service, $st)
Log "Over: strategie-ai.com/web v anonymnim okne - zaloha ma jet aktualni verzi."
