# push_dump.ps1 - DR: po nocni zaloze (3:00) nahraje nejnovejsi data_db dump z 188.12 k API.
# Scheduled task na 188.12 v 3:15. ASCII-only (#110). UploadFile = stream POST body.
param(
  [string]$Root  = 'E:\STRATEGIE',
  [string]$Api   = 'https://strategie-ai.com/api/v1/ops/dr/upload',
  [string]$Token = $env:DR_TRANSFER_TOKEN
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$log = Join-Path $Root '_push.log'
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $log $l -Encoding UTF8 }catch{} }
if(-not $Token){ Log "Chybi token (env DR_TRANSFER_TOKEN nebo -Token)"; exit 2 }
$dump = Get-ChildItem $Root -Recurse -Filter *.dump -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $dump){ Log "Zadny *.dump v $Root"; exit 1 }
Log ("Nahravam " + $dump.Name + " (" + [math]::Round($dump.Length/1MB,1) + " MB) -> API")
$t0 = Get-Date
$wc = New-Object System.Net.WebClient
$wc.Headers.Add('X-DR-Token',$Token)
$resp = $wc.UploadFile(($Api + "?name=" + [Uri]::EscapeDataString($dump.Name)), "POST", $dump.FullName)
$sec = [math]::Round(((Get-Date)-$t0).TotalSeconds,1)
Log ("OK: " + [Text.Encoding]::UTF8.GetString($resp) + " za " + $sec + "s")
