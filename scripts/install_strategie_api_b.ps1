#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 (23.5.2026, Marti's "production safety"):
# Install STRATEGIE-API-B NSSM service (port 8002, secondary instance)
# ============================================================
#
# Marti's spec: "Kdyz zase na pul hodiny zastavime jedno API, tak aby
# druhe nadale bezelo." Druhá API instance pro zero-downtime restart.
#
# Cíl:
#   - NSSM service "STRATEGIE-API-B" na portu 8002
#   - Same Python module (modules.erp.api / apps.api.main:app)
#   - Same DB connections (data_db single source of truth)
#   - Env: UVICORN_PORT=8002, STRATEGIE_INSTANCE_NAME=secondary
#
# Existing STRATEGIE-API (port 8001) zůstává nezměněn.
#
# Background services (STRATEGIE-EMAIL-FETCHER, STRATEGIE-TASK-WORKER,
# STRATEGIE-QUESTION-GENERATOR) zůstávají single-instance — neovlivněno.
# ============================================================

$ServiceName = "STRATEGIE-API-B"
$AppRoot = "C:\Projekty\STRATEGIE"
$NssmPath = "C:\Tools\nssm.exe"
$PythonPath = "C:\Python314\python.exe"

# Find python via existing STRATEGIE-API config (mirror)
if (-not (Test-Path $PythonPath)) {
    $ExistingPath = & $NssmPath get "STRATEGIE-API" Application 2>$null
    if ($ExistingPath -and (Test-Path $ExistingPath)) {
        $PythonPath = $ExistingPath
        Write-Host "Reuse Python from STRATEGIE-API: $PythonPath"
    } else {
        Write-Error "Python.exe not found. Set `$PythonPath manually."
        exit 1
    }
}

# Check if already installed
$Existing = & $NssmPath status $ServiceName 2>$null
if ($Existing) {
    Write-Host "Service $ServiceName already exists. Status: $Existing"
    Write-Host "To reinstall: nssm remove $ServiceName confirm; then re-run."
    exit 0
}

Write-Host "Installing NSSM service: $ServiceName"
Write-Host "  Python:       $PythonPath"
Write-Host "  AppRoot:      $AppRoot"
Write-Host "  Port:         8002"
Write-Host "  Instance:     secondary"
Write-Host ""

# Install service
& $NssmPath install $ServiceName $PythonPath "-m" "uvicorn" "apps.api.main:app" "--host" "0.0.0.0" "--port" "8002"
& $NssmPath set $ServiceName AppDirectory $AppRoot
& $NssmPath set $ServiceName DisplayName "STRATEGIE API (Secondary, port 8002)"
& $NssmPath set $ServiceName Description "Phase HA-1 secondary API instance pro zero-downtime restart. Load-balanced s STRATEGIE-API (port 8001) přes Caddy round-robin."
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Environment variables (mirror STRATEGIE-API + override port + instance name)
$EnvFromPrimary = & $NssmPath get "STRATEGIE-API" AppEnvironmentExtra 2>$null
if ($EnvFromPrimary) {
    Write-Host "Inheriting env from STRATEGIE-API + override UVICORN_PORT + STRATEGIE_INSTANCE_NAME"
    # Append our overrides — NSSM AppEnvironmentExtra format: KEY=VALUE (multi-line)
    $NewEnv = $EnvFromPrimary -replace "(?m)^UVICORN_PORT=.*$", "" -replace "(?m)^STRATEGIE_INSTANCE_NAME=.*$", ""
    $NewEnv = $NewEnv.TrimEnd() + "`r`nUVICORN_PORT=8002`r`nSTRATEGIE_INSTANCE_NAME=secondary"
    & $NssmPath set $ServiceName AppEnvironmentExtra $NewEnv
} else {
    Write-Warning "STRATEGIE-API has no AppEnvironmentExtra — set env manually"
    & $NssmPath set $ServiceName AppEnvironmentExtra "UVICORN_PORT=8002`r`nSTRATEGIE_INSTANCE_NAME=secondary"
}

# Log rotation (10 MB, keep 5 backups)
$LogDir = "C:\Logs\STRATEGIE"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
& $NssmPath set $ServiceName AppStdout "$LogDir\strategie-api-b.stdout.log"
& $NssmPath set $ServiceName AppStderr "$LogDir\strategie-api-b.stderr.log"
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateBytes 10485760
& $NssmPath set $ServiceName AppRotateOnline 1

# Restart on crash: 5s delay
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000

Write-Host ""
Write-Host "✓ NSSM service $ServiceName installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Start service:    Start-Service $ServiceName"
Write-Host "  2. Verify port 8002: Test-NetConnection -ComputerName localhost -Port 8002"
Write-Host "  3. Verify health:    Invoke-RestMethod http://localhost:8002/api/v1/health"
Write-Host "  4. Update Caddyfile pro round-robin (viz scripts/_phase_ha1_caddyfile.txt)"
Write-Host "  5. Reload Caddy:     Restart-Service STRATEGIE-CADDY"
Write-Host ""
Write-Host "fw.diag_log audit:"
Write-Host '  SELECT id, level, message, extra FROM fw.diag_log'
Write-Host "  WHERE module_id = 'api.lifecycle' ORDER BY id DESC LIMIT 5;"
