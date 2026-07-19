# push_dump.ps1 - DR: po nocni zaloze nahraje nejnovejsi data_db dump z 188.12 k API.
# RAW stream body (NE multipart - WebClient.UploadFile balí do form-data a rozbije archiv).
# Scheduled task na 188.12 @3:15. ASCII-only (#110).
param(
  [string]$Root  = 'E:\STRATEGIE',
  [string]$Url   = 'https://strategie-ai.com/api/v1/ops/dr/upload',
  [string]$Token = $env:DR_TRANSFER_TOKEN
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$log = Join-Path $Root '_push.log'
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $log $l -Encoding UTF8 }catch{} }
if(-not $Token){ Log "Chybi token"; exit 2 }
$dump = Get-ChildItem $Root -Recurse -Filter *.dump -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $dump){ Log "Zadny *.dump v $Root"; exit 1 }
Log ("Push " + $dump.Name + " (" + [math]::Round($dump.Length/1MB,1) + " MB) RAW")
$t0 = Get-Date
$req = [Net.HttpWebRequest]::Create($Url + "?name=" + [Uri]::EscapeDataString($dump.Name))
$req.Method = "POST"; $req.Headers.Add("X-DR-Token",$Token); $req.ContentType = "application/octet-stream"
$req.AllowWriteStreamBuffering = $false; $req.Timeout = 600000; $req.ReadWriteTimeout = 600000
$fs = [IO.File]::OpenRead($dump.FullName); $req.ContentLength = $fs.Length
try {
  $rs = $req.GetRequestStream(); $fs.CopyTo($rs); $rs.Close(); $fs.Close()
  $resp = $req.GetResponse(); $sr = New-Object IO.StreamReader($resp.GetResponseStream())
  Log ("OK: " + $sr.ReadToEnd() + " za " + [math]::Round(((Get-Date)-$t0).TotalSeconds,1) + "s"); $resp.Close()
} catch { $fs.Close(); Log ("PUSH fail: " + $_.Exception.Message); exit 1 }
