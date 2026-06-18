# setup_mcp_fs_roots.ps1 - Faze C (18.6.2026)
# Nastavi povolene koreny pro MCP filesystem (base_override) na EUROSOFT-MCP
# a restartuje sluzbu. Spustit na EC-SERVER2 (30.11) jako administrator.
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File setup_mcp_fs_roots.ps1
# Volitelne vlastni koreny:
#   ... -RwRoots "D:\data;D:\Data\ZZ_Marti-AI RW" -RoRoots "D:\Data\ZZ_Marti-AI RO"
#
# RW = koreny se ZAPISEM (uzivatele pisi i ctou). RO = jen cteni (ma prednost).
# Jemna konfigurace (ktere podslozky, kdo) je v STRATEGII (/dir-admin).

param(
  [string]$Service = "EUROSOFT-MCP",
  [string]$NssmPath = "",
  [string]$RwRoots = "D:\data;\\192.168.30.11\data;\\192.168.30.10\Data;D:\Data\ZZ_Marti-AI RW",
  [string]$RoRoots = "D:\Data\ZZ_Marti-AI RO"
)

$ErrorActionPreference = "Stop"

# najdi nssm - 0) parametr, 1) z definice sluzby (PathName), 2) znama mista, 3) PATH
$nssm = $null
if ($NssmPath -and (Test-Path $NssmPath)) { $nssm = $NssmPath }
if (-not $nssm) {
  try {
    $svc = Get-CimInstance Win32_Service -Filter "Name='$Service'" -ErrorAction SilentlyContinue
    if ($svc -and $svc.PathName) {
      Write-Host ("binPath sluzby: " + $svc.PathName)
      if ($svc.PathName -match '([A-Za-z]:\\[^"]*nssm\.exe)') { $nssm = $Matches[1] }
    }
  } catch { }
}
if (-not $nssm) {
  foreach ($p in @("C:\Tools\nssm.exe","C:\nssm\nssm.exe","C:\Windows\nssm.exe","D:\Tools\nssm.exe")) {
    if (Test-Path $p) { $nssm = $p; break }
  }
}
if (-not $nssm) {
  $cmd = Get-Command nssm.exe -ErrorAction SilentlyContinue
  if ($cmd) { $nssm = $cmd.Source }
}
if (-not $nssm) {
  Write-Host "CHYBA: nssm.exe nenalezen."
  Write-Host "Zjisti cestu k sluzbe rucne:"
  Write-Host "  (Get-CimInstance Win32_Service -Filter `"Name='$Service'`").PathName"
  Write-Host "a spust skript znovu s parametrem -NssmPath <cesta\nssm.exe>, nebo mi tu cestu posli."
  exit 1
}
Write-Host "nssm: $nssm"
Write-Host "sluzba: $Service"

# stavajici AppEnvironmentExtra (zachovat ostatni promenne!)
$cur = & $nssm get $Service AppEnvironmentExtra 2>$null
$entries = @()
if ($cur) {
  foreach ($line in ($cur -split "`r?`n")) {
    $t = $line.Trim()
    if ($t -eq "") { continue }
    if ($t -like "MCP_FS_RW_ROOTS=*") { continue }   # nahradime
    if ($t -like "MCP_FS_RO_ROOTS=*") { continue }
    $entries += $t
  }
}
$entries += ("MCP_FS_RW_ROOTS=" + $RwRoots)
$entries += ("MCP_FS_RO_ROOTS=" + $RoRoots)

Write-Host ""
Write-Host "Nastavuji AppEnvironmentExtra na:"
foreach ($e in $entries) { Write-Host ("  " + $e) }

& $nssm set $Service AppEnvironmentExtra @entries | Out-Null

Write-Host ""
Write-Host "Restartuji sluzbu $Service ..."
& $nssm restart $Service | Out-Null
Start-Sleep -Seconds 3
$st = & $nssm status $Service
Write-Host ("Stav sluzby: " + $st)
Write-Host ""
Write-Host "HOTOVO. Over v appce: /dir-admin -> 'MCP server - co realne povoluje' -> Nacist."
