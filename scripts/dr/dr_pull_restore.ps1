# dr_pull_restore.ps1 - Plzen DR (@3:30): stahne nejnovejsi dump z API a restorne do data_db.
param(
  [string]$Base    = 'https://strategie-ai.com',
  [string]$Token   = $env:DR_TRANSFER_TOKEN,
  [string]$Incoming= 'D:\STRATEGIE_IN',
  [string]$PgBin   = 'C:\Program Files\PostgreSQL\16\bin',
  [string]$Db      = 'data_db'
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
New-Item -ItemType Directory -Force $Incoming | Out-Null
$log = Join-Path $Incoming '_pullrestore.log'
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $log $l -Encoding UTF8 }catch{} }
if(-not $Token){ Log "Chybi token"; exit 2 }
$wc = New-Object System.Net.WebClient; $wc.Headers.Add('X-DR-Token',$Token)
try { $m = $wc.DownloadString("$Base/api/v1/ops/dr/meta") | ConvertFrom-Json } catch { Log ("META fail: "+$_.Exception.Message); exit 1 }
if(-not $m.stored){ Log "Na API neni ulozeny dump"; exit 1 }
$dest = Join-Path $Incoming $m.name
Log ("Stahuji " + $m.name + " (" + [math]::Round($m.size/1MB,1) + " MB, age=" + $m.age_s + "s)")
$t0 = Get-Date
$wc2 = New-Object System.Net.WebClient; $wc2.Headers.Add('X-DR-Token',$Token)
$wc2.DownloadFile("$Base/api/v1/ops/dr/download",$dest)
if((Get-Item $dest).Length -ne $m.size){ Log "Velikost nesedi - koncim"; exit 1 }
Log ("Stazeno za " + [math]::Round(((Get-Date)-$t0).TotalSeconds,1) + "s, restore...")
& "$PgBin\pg_restore.exe" -h localhost -U postgres -d $Db --clean --if-exists --no-owner --no-privileges $dest 2>&1 | ForEach-Object { Log ("  " + $_) }
Log ("Restore rc=" + $LASTEXITCODE + " (data_db obnovena)")
