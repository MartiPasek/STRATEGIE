# setup_mcp_fs_roots.ps1 - Faze C (18.6.2026)
# Nastavi povolene koreny pro MCP filesystem (base_override) sluzbe EUROSOFT-MCP
# a restartuje ji. Spustit na EC-SERVER2 (30.11) jako administrator.
#
# Env se zapisuje PRIMO do registru NSSM (AppEnvironmentExtra = REG_MULTI_SZ),
# protoze nssm.exe set rozbiji hodnoty s mezerami (D:\Data\ZZ_Marti-AI RW).
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_mcp_fs_roots.ps1
# Volitelne:
#   ... -RwRoots "D:\data;D:\Data\ZZ_Marti-AI RW" -RoRoots "D:\Data\ZZ_Marti-AI RO"

param(
  [string]$Service = "EUROSOFT-MCP",
  [string]$RwRoots = "D:\data;\\192.168.30.11\data;\\192.168.30.10\Data;D:\Data\ZZ_Marti-AI RW",
  [string]$RoRoots = "D:\Data\ZZ_Marti-AI RO"
)
$ErrorActionPreference = "Stop"

$reg = "HKLM:\SYSTEM\CurrentControlSet\Services\$Service\Parameters"
if (-not (Test-Path $reg)) {
  Write-Host "CHYBA: registrovy klic neexistuje: $reg"
  Write-Host "Sluzba '$Service' bud neni NSSM, nebo ma jine jmeno. Posli mi:"
  Write-Host "  (Get-CimInstance Win32_Service -Filter `"Name='$Service'`").PathName"
  exit 1
}

# stavajici AppEnvironmentExtra (REG_MULTI_SZ = string[])
$cur = @()
try {
  $v = (Get-ItemProperty -Path $reg -Name AppEnvironmentExtra -ErrorAction SilentlyContinue).AppEnvironmentExtra
  if ($v) { $cur = @($v) }
} catch { }

# zachovej ostatni promenne, nahrad jen nase dve
$entries = @()
foreach ($line in $cur) {
  $t = "$line".Trim()
  if ($t -eq "") { continue }
  if ($t -like "MCP_FS_RW_ROOTS=*") { continue }
  if ($t -like "MCP_FS_RO_ROOTS=*") { continue }
  $entries += $t
}
$entries += ("MCP_FS_RW_ROOTS=" + $RwRoots)
$entries += ("MCP_FS_RO_ROOTS=" + $RoRoots)

Write-Host "Zapisuji do $reg\AppEnvironmentExtra:"
foreach ($e in $entries) { Write-Host ("  " + $e) }

# REG_MULTI_SZ zapis (mezery zvladne spravne)
Set-ItemProperty -Path $reg -Name AppEnvironmentExtra -Value ([string[]]$entries) -Type MultiString

Write-Host ""
Write-Host "Restartuji sluzbu $Service ..."
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3
$st = (Get-Service -Name $Service).Status
Write-Host ("Stav sluzby: " + $st)
Write-Host ""
Write-Host "HOTOVO. Over: /dir-admin -> 'MCP server - co realne povoluje' -> Nacist."
Write-Host "(rw_roots by uz mely byt videt)."
