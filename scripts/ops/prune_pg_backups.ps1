# ============================================================================
# prune_pg_backups.ps1 - retence dennich PostgreSQL zaloh na 188.12 (disk E:)
# Bezi jako denni scheduled task po nocnim dumpu (03:00). Maze foldery
# yyyy-MM-dd starsi nez -KeepDays. Bezpecnostni pojistka: vzdy nechá poslednich
# -MinKeep nejnovejsich slozek, i kdyby byly starsi nez KeepDays.
# ASCII-only (gotcha #110). Suchy beh: -WhatIfList vypise, nic nemaze.
# ============================================================================
param(
  [string]$Root      = 'E:\STRATEGIE',
  [int]   $KeepDays  = 14,
  [int]   $MinKeep   = 7,
  [switch]$WhatIfList
)
$ErrorActionPreference = 'Stop'
$log = Join-Path $Root '_prune.log'
function Log($m){
  $line = ('{0}  {1}' -f ([DateTime]::Now.ToString('s')), $m)
  Write-Output $line
  try { Add-Content -Path $log -Value $line -Encoding UTF8 } catch {}
}

if(-not (Test-Path $Root)){ Log ("Root not found: " + $Root); exit 1 }

# Jen slozky pojmenovane datem yyyy-MM-dd
$all = Get-ChildItem $Root -Directory |
  Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } |
  Sort-Object Name
if($all.Count -eq 0){ Log "Zadne zalohy nenalezeny."; exit 0 }

$cutoff = (Get-Date).Date.AddDays(-$KeepDays)
$keepNewest = ($all | Select-Object -Last $MinKeep | ForEach-Object { $_.Name })

$toDelete = $all | Where-Object {
  ([datetime]::ParseExact($_.Name,'yyyy-MM-dd',$null) -lt $cutoff) -and
  ($keepNewest -notcontains $_.Name)
}

if(-not $toDelete -or $toDelete.Count -eq 0){
  Log ("Neni co mazat (celkem={0}, KeepDays={1}, MinKeep={2})." -f $all.Count,$KeepDays,$MinKeep)
  exit 0
}

if($WhatIfList){
  Log ("[SUCHY BEH] Smazal bych: " + (($toDelete | ForEach-Object { $_.Name }) -join ', '))
  exit 0
}

foreach($d in $toDelete){
  try   { Remove-Item $d.FullName -Recurse -Force; Log ("Smazano " + $d.Name) }
  catch { Log ("CHYBA " + $d.Name + ": " + $_.Exception.Message) }
}
$left = (Get-ChildItem $Root -Directory | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' }).Count
Log ("Hotovo. Ponechano " + $left + " zaloh.")
