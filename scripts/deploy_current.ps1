#Requires -RunAsAdministrator
# =====================================================================
# Phase: API Versioned Routing - deploy_current.ps1
# =====================================================================
# Wrapper for daily current-instance deployment.
# ASCII-only (gotcha #110 PS5.1 cp1250 default).
#
# What it does:
#   1. git pull origin main (v repo)
#   2. Restart-Service STRATEGIE-API
#   3. UPDATE fw.api_version SET released_at=NOW(), git_sha=<HEAD> WHERE version_code='current'
#   4. Print summary (commit, time, status, health check)
#
# Usage (on cloud APP):
#   cd C:\Projekty\STRATEGIE
#   .\scripts\deploy_current.ps1
#
# Marti's "drz jednoduchost" doctrine: nahrazuje rucni "git pull + Restart-Service"
# za 1 wrapper, ktery zaroven aktualizuje fw.api_version.released_at + git_sha.
# =====================================================================

$ErrorActionPreference = "Stop"

$RepoPath = "C:\Projekty\STRATEGIE"
$ServiceName = "STRATEGIE-API"
$HealthUrl = "http://localhost:8002/api/v1/health"
# Python venv (poetry) - obsahuje psycopg2, pouzivame ho misto psql
# (psql neni v PATH na cloud APP, PG bezi na 10.200.188.12)
$PythonExe = "C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs\strategie-W5adySD1-py3.14\Scripts\python.exe"

# =====================================================================
# 1. Git pull
# =====================================================================
Write-Host "=== Step 1: git pull ===" -ForegroundColor Cyan
Push-Location $RepoPath
try {
    git pull origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git pull failed (exit code $LASTEXITCODE)"
        exit 1
    }
    $GitSha = (git rev-parse HEAD).Trim()
    $GitShaShort = (git rev-parse --short HEAD).Trim()
    Write-Host "  HEAD: $GitShaShort"
}
finally {
    Pop-Location
}

# =====================================================================
# 2. Restart service
# =====================================================================
Write-Host ""
Write-Host "=== Step 2: Restart-Service $ServiceName ===" -ForegroundColor Cyan
Restart-Service $ServiceName -Force
Start-Sleep -Seconds 3

# Verify running
$svc = Get-Service $ServiceName
if ($svc.Status -ne "Running") {
    Write-Error "Service $ServiceName failed to restart (status: $($svc.Status))"
    exit 1
}
Write-Host "  Status: $($svc.Status)"

# =====================================================================
# 3. UPDATE released_at + git_sha (via Python venv psycopg2)
# =====================================================================
Write-Host ""
Write-Host "=== Step 3: UPDATE fw.api_version ===" -ForegroundColor Cyan
if (-not (Test-Path $PythonExe)) {
    Write-Warning "Python venv not found: $PythonExe - skipping DB update"
    Write-Warning "(Service restarted ALE fw.api_version.released_at NOT updated)"
}
else {
    # Python script reads STRATEGIE_DATA_DB_URL from env (set v NSSM)
    # nebo nactena z .env. Pouzivame stejny conn string jako STRATEGIE-API.
    $PyScript = @"
import os, sys
sys.path.insert(0, r'$RepoPath')
from dotenv import load_dotenv
load_dotenv(r'$RepoPath\.env')
import psycopg2
url = os.environ.get('STRATEGIE_DATA_DB_URL') or os.environ.get('DATABASE_URL')
if not url:
    print('FAIL: STRATEGIE_DATA_DB_URL not set'); sys.exit(1)
# Convert sqlalchemy URL -> psycopg2 (drop postgresql+psycopg2:// prefix)
url = url.replace('postgresql+psycopg2://', 'postgresql://').replace('postgresql+asyncpg://', 'postgresql://')
conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()
cur.execute(""""""
UPDATE fw.api_version
SET released_at = NOW(),
    git_sha = %s
WHERE version_code = 'current'
RETURNING version_string,
          TO_CHAR(released_at, 'DD.MM. HH24:MI') AS released,
          SUBSTRING(git_sha, 1, 7) AS sha
"""""", ('$GitSha',))
row = cur.fetchone()
if row:
    print(f'  Updated: {row[0]} -> released_at={row[1]}, git_sha={row[2]}')
else:
    print('  WARN: 0 rows updated (version_code=current not found?)')
cur.close(); conn.close()
"@
    & $PythonExe -c $PyScript
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Python UPDATE failed (exit code $LASTEXITCODE)"
    }
}

# =====================================================================
# 4. Summary
# =====================================================================
Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Commit:  $GitShaShort"
Write-Host "Time:    $(Get-Date -Format 'dd.MM. HH:mm')"
Write-Host "Service: $($svc.Status)"
Write-Host ""
Write-Host "Health check:"
try {
    $health = Invoke-RestMethod $HealthUrl -TimeoutSec 5
    Write-Host "  $($health | ConvertTo-Json -Compress)"
}
catch {
    Write-Warning "Health check failed: $($_.Exception.Message)"
    Write-Host "  Check log: Get-Content C:\Logs\STRATEGIE\strategie-api.stderr.log -Tail 30"
}

Write-Host ""
Write-Host "Verify aktualni verze v patice:"
Write-Host "  cd $RepoPath ; .\scripts\verify_api_versions.ps1   # (TODO Etapa F)"
