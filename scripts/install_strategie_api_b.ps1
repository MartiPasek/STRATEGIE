#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 (23.5.2026): Install STRATEGIE-API-B NSSM service
# Secondary instance, port 8003 (primary already runs on 8002)
# ============================================================
# ASCII-only (gotcha #110 PS5.1 cp1250).
# ============================================================

$ServiceName = "STRATEGIE-API-B"
$SecondaryPort = "8003"
$NssmPath = "C:\Tools\nssm.exe"

if (-not (Test-Path $NssmPath)) {
    Write-Error "NSSM not found at $NssmPath"
    exit 1
}

# Helper: get NSSM property, strip trailing CR/LF/whitespace
function Get-NssmProp {
    param([string]$svc, [string]$prop)
    $val = & $NssmPath get $svc $prop 2>$null
    if ($null -eq $val) { return "" }
    return ($val | Out-String).Trim()
}

# Discover existing STRATEGIE-API config (mirror Python + dir + env)
$PrimaryApp = Get-NssmProp "STRATEGIE-API" "Application"
$PrimaryDir = Get-NssmProp "STRATEGIE-API" "AppDirectory"
$PrimaryArgs = Get-NssmProp "STRATEGIE-API" "AppParameters"
$PrimaryEnv = Get-NssmProp "STRATEGIE-API" "AppEnvironmentExtra"

if (-not $PrimaryApp -or -not (Test-Path $PrimaryApp)) {
    Write-Error "STRATEGIE-API not installed or Python path invalid. Cannot mirror."
    Write-Host "  Application reported: '$PrimaryApp'"
    exit 1
}

Write-Host "Mirroring STRATEGIE-API config:"
Write-Host "  Application:  '$PrimaryApp'"
Write-Host "  AppDirectory: '$PrimaryDir'"
Write-Host "  AppArgs:      '$PrimaryArgs'"
Write-Host ""

# Replace --port N with --port 8003 in args
$SecondaryArgs = $PrimaryArgs -replace "--port\s+\d+", "--port $SecondaryPort"
if ($SecondaryArgs -eq $PrimaryArgs) {
    Write-Warning "Primary args missing '--port N'. Appending."
    $SecondaryArgs = $PrimaryArgs.TrimEnd() + " --port $SecondaryPort"
}
Write-Host "Secondary args: '$SecondaryArgs'"
Write-Host ""

# If service exists, remove first (idempotent reinstall)
$Existing = & $NssmPath status $ServiceName 2>$null
if ($Existing) {
    Write-Host "Service $ServiceName exists (status: $Existing). Removing for clean reinstall..."
    & $NssmPath stop $ServiceName 2>$null
    Start-Sleep -Seconds 2
    & $NssmPath remove $ServiceName confirm
    Start-Sleep -Seconds 1
}

Write-Host "Installing NSSM service: $ServiceName"

# Install service (args as single string, NSSM parses)
$ArgsArray = $SecondaryArgs.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
& $NssmPath install $ServiceName $PrimaryApp @ArgsArray
& $NssmPath set $ServiceName AppDirectory $PrimaryDir
& $NssmPath set $ServiceName DisplayName "STRATEGIE API (Secondary, port $SecondaryPort)"
& $NssmPath set $ServiceName Description "Phase HA-1 secondary API. Load-balanced with STRATEGIE-API via Caddy."
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Environment variables — NSSM expects single multi-line string s LF (NOT CRLF).
# Filter out any UVICORN_PORT / STRATEGIE_INSTANCE_NAME from primary env, then append ours.
$EnvLines = @()
if ($PrimaryEnv) {
    foreach ($line in ($PrimaryEnv -split "`r?`n")) {
        $clean = $line.Trim()
        if ($clean -eq "") { continue }
        if ($clean -match '^(UVICORN_PORT|STRATEGIE_INSTANCE_NAME)=') { continue }
        $EnvLines += $clean
    }
}
$EnvLines += "UVICORN_PORT=$SecondaryPort"
$EnvLines += "STRATEGIE_INSTANCE_NAME=secondary"

# NSSM requires \n (LF) not CRLF for env entries. Join with LF only.
$EnvBlock = $EnvLines -join "`n"

Write-Host "Environment block to set:"
$EnvLines | ForEach-Object { Write-Host "  $_" }

& $NssmPath set $ServiceName AppEnvironmentExtra $EnvBlock

# Log rotation
$LogDir = "C:\Logs\STRATEGIE"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
& $NssmPath set $ServiceName AppStdout "$LogDir\strategie-api-b.stdout.log"
& $NssmPath set $ServiceName AppStderr "$LogDir\strategie-api-b.stderr.log"
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateBytes 10485760
& $NssmPath set $ServiceName AppRotateOnline 1

# Restart on crash
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000

Write-Host ""
Write-Host "DONE. Service $ServiceName installed (port $SecondaryPort)."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  Start-Service $ServiceName"
Write-Host "  Start-Sleep -Seconds 5"
Write-Host "  Invoke-RestMethod http://localhost:$SecondaryPort/api/v1/health"
Write-Host "  # Expect: {ok:True, instance:'secondary', port:$SecondaryPort}"
Write-Host ""
Write-Host "Verify env:"
Write-Host "  & '$NssmPath' get $ServiceName AppEnvironmentExtra"
Write-Host "  & '$NssmPath' get $ServiceName AppParameters"
