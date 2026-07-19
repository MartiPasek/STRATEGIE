# fetch_dump.ps1 - DR: stahne nejnovejsi data_db dump z Prahy (streaming) do Incoming.
# Bezi jako denni scheduled task na plzenskem boxu PRED restore_data_db.ps1.
# ASCII-only (#110). WebClient.DownloadFile = stream na disk (nizka pamet, i pro 500MB+).
param(
  [string]$Base    = 'https://strategie-ai.com',
  [string]$Token   = $env:DR_TRANSFER_TOKEN,   # stejny token jako na API serveru
  [string]$Incoming= 'D:\STRATEGIE_IN'
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if(-not $Token){ Write-Error "Chybi token (param -Token nebo env DR_TRANSFER_TOKEN)"; exit 2 }
New-Item -ItemType Directory -Force -Path $Incoming | Out-Null
$log = Join-Path $Incoming '_fetch.log'
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $log $l -Encoding UTF8 }catch{} }

# 1) meta (jmeno + velikost) — kontrola dosahu + preskoceni pokud uz mame
$metaUrl = "$Base/api/v1/ops/dr/meta"
try {
  $wc = New-Object System.Net.WebClient; $wc.Headers.Add('X-DR-Token',$Token)
  $meta = $wc.DownloadString($metaUrl) | ConvertFrom-Json
} catch { Log ("META fail: " + $_.Exception.Message); exit 1 }
if(-not $meta.ok){ Log ("Server: " + ($meta.error) + " (" + $meta.hint + ") root=" + $meta.root); exit 1 }
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss'); $dest = Join-Path $Incoming ('data_db_'+$stamp+'.dump')


# 2) stazeni streamem
$tmp = "$dest.part"
Log ("Stahuji zivy pg_dump streamem -> " + $dest)
$t0 = Get-Date
$wc2 = New-Object System.Net.WebClient; $wc2.Headers.Add('X-DR-Token',$Token)
$wc2.DownloadFile("$Base/api/v1/ops/dr/stream-dump", $tmp)
$sec = [math]::Round(((Get-Date)-$t0).TotalSeconds,1)
$got = (Get-Item $tmp).Length
if($got -lt 1024){ Log ("Dump podezrele maly ("+$got+" B), mazu part."); Remove-Item $tmp -Force; exit 1 }
Move-Item $tmp $dest -Force
Log ("OK: " + (Split-Path $dest -Leaf) + " za " + $sec + "s (" + [math]::Round($got/1MB,1) + " MB)")
