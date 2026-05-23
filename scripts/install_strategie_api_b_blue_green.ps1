#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 Blue-Green (23.5.2026): Reinstall STRATEGIE-API-B
# AppDirectory: C:\Projekty\STRATEGIE-prev (day-old snapshot)
# Port: 8003, instance: secondary
# ============================================================
# Workflow (Marti's vize):
#   Primary (8002): aktualni kod z C:\Projekty\STRATEGIE
#   Secondary (8003): den stary kod z C:\Projekty\STRATEGIE-prev
#   Caddy lb_policy first: primary preferred, secondary fail-over only
# ============================================================

$ServiceName = "STRATEGIE-API-B"
$SecondaryPort = "8003"
$SecondaryDir = "C:\Projekty\STRATEGIE-prev"
$NssmPath = "C:\Tools\nssm.exe"

if (-not (Test-Path $NssmPath)) {
    Write-Error "NSSM not found: $NssmPath"
    exit 1
}

if (-not (Test-Path $SecondaryDir)) {
    Write-Error "Secondary checkout not found: $SecondaryDir"
    Write-Host "Run first: .\scripts\_phase_ha1_init_snapshot.ps1"
    exit 1
}

# Helper (same fix as install_strategie_api_b.ps1)
function Get-NssmPropOneLine {
    param([string]$svc, [string]$prop)
    $raw = & $NssmPath get $svc $prop 2>$null
    if ($null -eq $raw) { return "" }
    $str = [string]::Join('', @($raw))
    $str = $str -replace '[\x00-\x1F\x7F]+', ''
    return $str.Trim()
}

function Get-NssmPropMultiLine {
    param([string]$svc, [string]$prop)
    $raw = & $NssmPath get $svc $prop 2>$null
    if ($null -eq $raw) { return @() }
    $str = [string]::Join("`n", @($raw))
    $lines = $str -split "[\r\n]+"
    $clean = @()
    foreach ($l in $lines) {
        $c = ($l -replace '[\x00-\x09\x0B-\x1F\x7F]', '').Trim()
        if ($c -ne "") { $clean += $c }
    }
    return @($clean)
}

# Mirror primary config (Python path, args) - same shared venv
$PrimaryApp = Get-NssmPropOneLine "STRATEGIE-API" "Application"
$PrimaryArgs = Get-NssmPropOneLine "STRATEGIE-API" "AppParameters"
$PrimaryEnvLines = Get-NssmPropMultiLine "STRATEGIE-API" "AppEnvironmentExtra"

Write-Host "Mirroring STRATEGIE-API:"
Write-Host "  Application:  [$PrimaryApp]   (shared venv)"
Write-Host "  AppArgs:      [$PrimaryArgs]"
Write-Host ""

if (-not $PrimaryApp -or -not (Test-Path $PrimaryApp)) {
    Write-Error "Primary Python path invalid: [$PrimaryApp]"
    exit 1
}

# Override port in args
$SecondaryArgs = $PrimaryArgs -replace "--port\s+\d+", "--port $SecondaryPort"
if ($SecondaryArgs -eq $PrimaryArgs) {
    $SecondaryArgs = $PrimaryArgs.TrimEnd() + " --port $SecondaryPort"
}
Write-Host "Secondary args: [$SecondaryArgs]"
Write-Host "Secondary dir:  [$SecondaryDir]   (day-old snapshot, NOT C:\Projekty\STRATEGIE)"
Write-Host ""

# Idempotent reinstall
$Existing = & $NssmPath status $ServiceName 2>$null
if ($Existing) {
    Write-Host "Removing existing $ServiceName..."
    & $NssmPath stop $ServiceName 2>$null | Out-Null
    Start-Sleep -Seconds 2
    & $NssmPath remove $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "Installing $ServiceName (blue-green secondary)..."
$ArgsArray = $SecondaryArgs.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
& $NssmPath install $ServiceName $PrimaryApp @ArgsArray | Out-Null

# KEY DIFFERENCE: AppDirectory points to day-old snapshot
& $NssmPath set $ServiceName AppDirectory $SecondaryDir | Out-Null

& $NssmPath set $ServiceName DisplayName "STRATEGIE API (Secondary, port $SecondaryPort, day-old snapshot)" | Out-Null
& $NssmPath set $ServiceName Description "Phase HA-1 Blue-Green: serves yesterday's code from $SecondaryDir. Fail-over target pro primary." | Out-Null
& $NssmPath set $ServiceName Start SERVICE_AUTO_START | Out-Null

# Env: inherit primary + override port + instance name
$EnvOut = @()
foreach ($line in $PrimaryEnvLines) {
    if ($line -match '^(UVICORN_PORT|STRATEGIE_INSTANCE_NAME|STRATEGIE_PROJECT_ROOT|STRATEGIE_REPO_ROOT)=') { continue }
    $EnvOut += $line
}
# Point env vars to secondary dir too (so code reading STRATEGIE_PROJECT_ROOT
# loads files z C:\Projekty\STRATEGIE-prev, ne z primary)
$EnvOut += "STRATEGIE_PROJECT_ROOT=$($SecondaryDir -replace '\\', '/')"
$EnvOut += "STRATEGIE_REPO_ROOT=$($SecondaryDir -replace '\\', '/')"
$EnvOut += "UVICORN_PORT=$SecondaryPort"
$EnvOut += "STRATEGIE_INSTANCE_NAME=secondary"

Write-Host "Env ($($EnvOut.Count) entries):"
foreach ($e in $EnvOut) { Write-Host "  > $e" }
$EnvBlock = ($EnvOut -join "`n")
& $NssmPath set $ServiceName AppEnvironmentExtra $EnvBlock | Out-Null

# Logs
$LogDir = "C:\Logs\STRATEGIE"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
& $NssmPath set $ServiceName AppStdout "$LogDir\strategie-api-b.stdout.log" | Out-Null
& $NssmPath set $ServiceName AppStderr "$LogDir\strategie-api-b.stderr.log" | Out-Null
& $NssmPath set $ServiceName AppRotateFiles 1 | Out-Null
& $NssmPath set $ServiceName AppRotateBytes 10485760 | Out-Null
& $NssmPath set $ServiceName AppRotateOnline 1 | Out-Null

# Restart on crash
& $NssmPath set $ServiceName AppExit Default Restart | Out-Null
& $NssmPath set $ServiceName AppRestartDelay 5000 | Out-Null

Write-Host ""
Write-Host "DONE - blue-green secondary configured."
Write-Host ""
Write-Host "Next:"
Write-Host "  Start-Service $ServiceName"
Write-Host "  Start-Sleep -Seconds 5"
Write-Host "  Invoke-RestMethod http://localhost:$SecondaryPort/api/v1/health"
Write-Host ""
Write-Host "Verify secondary loads from snapshot:"
Write-Host "  cd $SecondaryDir"
Write-Host "  git log -1 --oneline"
Write-Host "  # should be DAY-OLD or older commit (not current primary HEAD)"
