# Publikuje release APK do STRATEGIE app distribuce (fw.app_version).
# ASCII only (PowerShell 5.1 cp1250 safe). Pouziva curl.exe (Windows 10/11).
#
# Pouziti:
#   .\scripts\publish_mobile_apk.ps1
#   .\scripts\publish_mobile_apk.ps1 -Notes "v1.14 dial poller"
#
# Predpoklady:
#   - release build hotovy: APP\Mobile\app\build\outputs\apk\release\app-release.apk
#   - env STRATEGIE_DEPLOY_TOKEN na NB (stejna hodnota jako na cloud APP)
#
# Po uploadu appky pollnou /app/<key>/latest, uvidi vyssi version_code a stahnou.
param(
  [string]$AppKey  = "mobile",
  [string]$BaseUrl = "https://strategie-ai.com",
  [string]$AppName = "STRATEGIE Mobil",
  [string]$Notes   = ""
)
$ErrorActionPreference = "Stop"
$root    = Split-Path -Parent $PSScriptRoot
$apk     = Join-Path $root "APP\Mobile\app\build\outputs\apk\release\app-release.apk"
$verFile = Join-Path $root "APP\Mobile\version.properties"

if (-not (Test-Path $apk))     { Write-Host "CHYBA: APK nenalezeno: $apk" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $verFile)) { Write-Host "CHYBA: version.properties nenalezeno: $verFile" -ForegroundColor Red; exit 1 }

$vc = (Select-String -Path $verFile -Pattern '^versionCode=(.+)$').Matches.Groups[1].Value.Trim()
$vn = (Select-String -Path $verFile -Pattern '^versionName=(.+)$').Matches.Groups[1].Value.Trim()
if (-not $vc -or -not $vn) { Write-Host "CHYBA: nelze precist versionCode/versionName" -ForegroundColor Red; exit 1 }

$token = $env:STRATEGIE_DEPLOY_TOKEN
if (-not $token) {
  Write-Host "CHYBA: chybi env STRATEGIE_DEPLOY_TOKEN na NB." -ForegroundColor Red
  Write-Host "Nastav: [System.Environment]::SetEnvironmentVariable('STRATEGIE_DEPLOY_TOKEN','<secret>','User')" -ForegroundColor Yellow
  exit 1
}
if (-not $Notes) { $Notes = "v$vn (code $vc)" }

$size = (Get-Item $apk).Length
Write-Host ("Publikuji {0} v{1} (code {2}), {3} B -> {4}" -f $AppKey, $vn, $vc, $size, $BaseUrl) -ForegroundColor Cyan
$url = "$BaseUrl/api/v1/erp/app/$AppKey/upload"
$resp = & curl.exe -s -X POST $url `
  -H "X-Deploy-Token: $token" `
  -F "file=@$apk;type=application/vnd.android.package-archive" `
  -F "version_code=$vc" `
  -F "version_name=$vn" `
  -F "app_name=$AppName" `
  -F "notes=$Notes"
Write-Host "Odpoved uploadu:" -ForegroundColor Green
Write-Host $resp

# Overeni - co je ted nejnovejsi verze v distribuci
$latest = & curl.exe -s "$BaseUrl/api/v1/erp/app/$AppKey/latest" -H "X-Deploy-Token: $token"
Write-Host "Latest v distribuci:" -ForegroundColor Green
Write-Host $latest
