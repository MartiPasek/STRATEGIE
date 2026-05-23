#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 (23.5.2026): Install STRATEGIE-API-B NSSM service
# (port 8002, secondary instance)
# ============================================================
# ASCII-only (gotcha #110 - em-dash/Czech smart quotes break PS5.1
# default cp1250 encoding). All special chars replaced.
# ============================================================

$ServiceName = "STRATEGIE-API-B"
$NssmPath = "C:\Tools\nssm.exe"

# Discover existing STRATEGIE-API config (mirror Python path + AppDirectory + env)
$PrimaryApp = & $NssmPath get "STRATEGIE-API" Application 2>$null
$PrimaryDir = & $NssmPath get "STRATEGIE-API" AppDirectory 2>$null
$PrimaryArgs = & $NssmPath get "STRATEGIE-API" AppParameters 2>$null
$PrimaryEnv = & $NssmPath get "STRATEGIE-API" AppEnvironmentExtra 2>$null

if (-not $PrimaryApp -or -not (Test-Path $PrimaryApp)) {
    Write-Error "STRATEGIE-API not installed or Python path invalid. Cannot mirror config."
    Write-Host "  Get-Service STRATEGIE-API"
    Write-Host "  nssm get STRATEGIE-API Application"
    exit 1
}

Write-Host "Mirroring STRATEGIE-API config:"
Write-Host "  Application:  $PrimaryApp"
Write-Host "  AppDirectory: $PrimaryDir"
Write-Host "  AppArgs:      $PrimaryArgs"
Write-Host ""

# Replace --port 8001 with --port 8003 in args
$SecondaryArgs = $PrimaryArgs -replace "--port\s+\d+", "--port 8003"
if ($SecondaryArgs -eq $PrimaryArgs) {
    Write-Warning "Primary args don't contain '--port N' pattern. Will append --port 8003."
    $SecondaryArgs = $PrimaryArgs.TrimEnd() + " --port 8003"
}
Write-Host "Secondary args: $SecondaryArgs"
Write-Host ""

# Check if already installed
$Existing = & $NssmPath status $ServiceName 2>$null
if ($Existing) {
    Write-Host "Service $ServiceName already exists. Status: $Existing"
    Write-Host "To reinstall: nssm remove $ServiceName confirm; then re-run."
    exit 0
}

Write-Host "Installing NSSM service: $ServiceName"

# Install service (args as single string passed to nssm)
$ArgsArray = $SecondaryArgs.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
& $NssmPath install $ServiceName $PrimaryApp @ArgsArray
& $NssmPath set $ServiceName AppDirectory $PrimaryDir
& $NssmPath set $ServiceName DisplayName "STRATEGIE API (Secondary, port 8002)"
& $NssmPath set $ServiceName Description "Phase HA-1 secondary API instance. Load-balanced with STRATEGIE-API (port 8001) via Caddy."
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Environment vars: inherit from primary + override port + instance name
if ($PrimaryEnv) {
    # Strip any existing UVICORN_PORT / STRATEGIE_INSTANCE_NAME (case-insensitive)
    $LinesIn = $PrimaryEnv -split "`r?`n"
    $LinesOut = @()
    foreach ($line in $LinesIn) {
        if ($line -match '^(UVICORN_PORT|STRATEGIE_INSTANCE_NAME)=') { continue }
        $LinesOut += $line
    }
    $LinesOut += "UVICORN_PORT=8002"
    $LinesOut += "STRATEGIE_INSTANCE_NAME=secondary"
    $NewEnv = $LinesOut -join "`r`n"
    & $NssmPath set $ServiceName AppEnvironmentExtra $NewEnv
} else {
    Write-Warning "Primary has no AppEnvironmentExtra. Setting minimum."
    & $NssmPath set $ServiceName AppEnvironmentExtra "UVICORN_PORT=8002`r`nSTRATEGIE_INSTANCE_NAME=secondary"
}

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
Write-Host "DONE. Service $ServiceName installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  Start-Service $ServiceName"
Write-Host "  Start-Sleep -Seconds 5"
Write-Host "  Invoke-RestMethod http://localhost:8002/api/v1/health"
Write-Host "  # Expect: {ok:True, instance:'secondary', port:8002}"
