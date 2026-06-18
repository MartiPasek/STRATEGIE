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
  [string]$RwRoots = "D:\data;\\192.168.30.11\data;\\192.168.30.10\Data;D:\Data\ZZ_Marti-AI RW",
  [string]$RoRoots = "D:\Data\ZZ_Marti-AI RO"
)

$ErrorActionPreference = "Stop"

# najdi nssm
$nssm = $null
foreach ($p in @("C:\Tools\nssm.exe","C:\nssm\nssm.exe","nssm.exe")) {
  try { & $p version *> $null; $nssm = $p; break } catch { }
}
if (-not $nssm) { Write-Host "CHYBA: nssm.exe nenalezen (zkus C:\Tools\nssm.exe)"; exit 1 }
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
