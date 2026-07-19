# fetch_dump.ps1 - DR: stahne ulozeny nocni dump z API do Incoming (Plzen, 3:30).
# ASCII-only (#110). Nasledne spousti restore_data_db.ps1. WebClient stream na disk.
param(
  [string]$Base    = 'https://strategie-ai.com',
  [string]$Token   = $env:DR_TRANSFER_TOKEN,
  [string]$Incoming= 'D:\STRATEGIE_IN'
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if(-not $Token){ Write-Error "Chybi token"; exit 2 }
New-Item -ItemType Directory -Force -Path $Incoming | Out-Null
$log = Join-Path $Incoming '_fetch.log'
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $log $l -Encoding UTF8 }catch{} }
$wc = New-Object System.Net.WebClient; $wc.Headers.Add('X-DR-Token',$Token)
try { $meta = $wc.DownloadString("$Base/api/v1/ops/dr/meta") | ConvertFrom-Json }
catch { Log ("META fail: " + $_.Exception.Message); exit 1 }
if(-not $meta.stored){ Log "Na API zatim neni ulozeny dump (push z 188.12?)"; exit 1 }
$dest = Join-Path $Incoming $meta.name
if((Test-Path $dest) -and ((Get-Item $dest).Length -eq $meta.size)){ Log ("Uz mam " + $meta.name + " - preskakuji."); exit 0 }
$tmp = "$dest.part"
Log ("Stahuji " + $meta.name + " (" + [math]::Round($meta.size/1MB,1) + " MB) age=" + $meta.age_s + "s")
$t0 = Get-Date
$wc2 = New-Object System.Net.WebClient; $wc2.Headers.Add('X-DR-Token',$Token)
$wc2.DownloadFile("$Base/api/v1/ops/dr/download", $tmp)
$got = (Get-Item $tmp).Length
if($got -ne $meta.size){ Log ("Velikost nesedi ("+$got+"!="+$meta.size+"), mazu."); Remove-Item $tmp -Force; exit 1 }
Move-Item $tmp $dest -Force
Log ("OK: " + $meta.name + " za " + [math]::Round(((Get-Date)-$t0).TotalSeconds,1) + "s (" + [math]::Round($got/1MB,1) + " MB)")
