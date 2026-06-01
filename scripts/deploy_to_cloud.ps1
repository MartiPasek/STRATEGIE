# ============================================================================
# deploy_to_cloud.ps1 (NB) - push-to-deploy trigger (Marti 1.6.2026)
# ----------------------------------------------------------------------------
# Zavola cloud APP /deploy/now pres X-Deploy-Token -> git pull + restart API
# (Phase 42 RESTART-WATCHER). Spustit po `git push origin main`.
#
# Predpoklad:
#   1. Na NB nastaven env STRATEGIE_DEPLOY_TOKEN (stejna hodnota jako na cloudu)
#        [System.Environment]::SetEnvironmentVariable('STRATEGIE_DEPLOY_TOKEN','<secret>','User')
#   2. Na cloud APP nastaven env STRATEGIE_DEPLOY_TOKEN + restart STRATEGIE-API
#        (jinak token auth nefunguje a endpoint vyzaduje parent session)
#
# Usage:
#   powershell -File scripts\deploy_to_cloud.ps1
#   (volitelne -Description "popis")
# ============================================================================
param(
    [string]$Description = "Deploy z NB skriptu (deploy_to_cloud.ps1)",
    [string]$Url = "https://strategie-ai.com/api/v1/erp/deploy/now"
)

$ErrorActionPreference = "Stop"

$Token = $env:STRATEGIE_DEPLOY_TOKEN
if (-not $Token) {
    Write-Host "CHYBA: chybi env STRATEGIE_DEPLOY_TOKEN na NB." -ForegroundColor Red
    Write-Host "Nastav: [System.Environment]::SetEnvironmentVariable('STRATEGIE_DEPLOY_TOKEN','<secret>','User')" -ForegroundColor Yellow
    exit 1
}

$body = @{ description = $Description } | ConvertTo-Json

Write-Host "Volam $Url ..." -ForegroundColor Cyan
try {
    $resp = Invoke-RestMethod -Uri $Url -Method Post `
        -Headers @{ "X-Deploy-Token" = $Token; "Content-Type" = "application/json" } `
        -Body $body -TimeoutSec 60
} catch {
    Write-Host "Deploy request SELHAL: $_" -ForegroundColor Red
    exit 1
}

if ($resp.ok -or $resp.status -eq "deployed") {
    Write-Host ("OK - nasazeno: {0} souboru, target {1}. API se restartuje (~5s)." -f $resp.files_changed, $resp.target_sha) -ForegroundColor Green
} elseif ($resp.reason -eq "already_up_to_date") {
    Write-Host "Cloud uz bezi na nejnovejsi verzi (nic k nasazeni)." -ForegroundColor Yellow
} else {
    Write-Host ("Nenasazeno: reason={0} error={1}" -f $resp.reason, $resp.error) -ForegroundColor Yellow
}
