#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 (23.5.2026): Install STRATEGIE-API-B NSSM service
# Secondary instance, port 8003 (primary runs on 8002)
# ============================================================
# v3: Robust NSSM output parsing (strip CR/LF/NUL/whitespace),
#     idempotent reinstall, LF-separated env.
# ============================================================

$ServiceName = "STRATEGIE-API-B"
$SecondaryPort = "8003"
$NssmPath = "C:\Tools\nssm.exe"

if (-not (Test-Path $NssmPath)) {
    Write-Error "NSSM not found at $NssmPath"
    exit 1
}

# Helper: extract single-line NSSM property (Application, AppDirectory, AppParameters).
# v3 fix: flatten all output to single string, strip ALL control chars (0x00-0x1F + 0x7F)
# including LF (0x0A) which prev regex missed.
function Get-NssmPropOneLine {
    param([string]$svc, [string]$prop)
    $raw = & $NssmPath get $svc $prop 2>$null
    if ($null -eq $raw) { return "" }
    # Flatten array to single string
    $str = [string]::Join('', @($raw))
    # Strip ALL control chars (NUL, BEL, BS, TAB, LF, VT, FF, CR, ..., US, DEL)
    $str = $str -replace '[\x00-\x1F\x7F]+', ''
    return $str.Trim()
}

# Helper: extract multi-line NSSM property (AppEnvironmentExtra).
# Returns array of non-empty trimmed lines.
function Get-NssmPropMultiLine {
    param([string]$svc, [string]$prop)
    $raw = & $NssmPath get $svc $prop 2>$null
    if ($null -eq $raw) { return @() }
    # Flatten to string first (may be array OR multi-line string)
    $str = [string]::Join("`n", @($raw))
    # Split on any newline style, strip remaining control chars per line
    $lines = $str -split "[\r\n]+"
    $clean = @()
    foreach ($l in $lines) {
        $c = ($l -replace '[\x00-\x09\x0B-\x1F\x7F]', '').Trim()  # keep LF (already split)
        if ($c -ne "") { $clean += $c }
    }
    return @($clean)
}

# === Discover STRATEGIE-API config ===
$PrimaryApp = Get-NssmPropOneLine "STRATEGIE-API" "Application"
$PrimaryDir = Get-NssmPropOneLine "STRATEGIE-API" "AppDirectory"
$PrimaryArgs = Get-NssmPropOneLine "STRATEGIE-API" "AppParameters"
$PrimaryEnvLines = Get-NssmPropMultiLine "STRATEGIE-API" "AppEnvironmentExtra"

Write-Host "Discovered STRATEGIE-API config:"
Write-Host "  Application:  [$PrimaryApp]"
Write-Host "  AppDirectory: [$PrimaryDir]"
Write-Host "  AppArgs:      [$PrimaryArgs]"
Write-Host "  Env lines:    $($PrimaryEnvLines.Count)"
foreach ($l in $PrimaryEnvLines) { Write-Host "    > $l" }
Write-Host ""

if (-not $PrimaryApp -or -not (Test-Path $PrimaryApp)) {
    Write-Error "Primary Python path invalid: [$PrimaryApp]"
    exit 1
}

# === Build secondary args (replace --port N with --port 8003) ===
$SecondaryArgs = $PrimaryArgs -replace "--port\s+\d+", "--port $SecondaryPort"
if ($SecondaryArgs -eq $PrimaryArgs) {
    Write-Warning "Primary args missing '--port N'. Appending."
    $SecondaryArgs = $PrimaryArgs.TrimEnd() + " --port $SecondaryPort"
}
Write-Host "Secondary args: [$SecondaryArgs]"
Write-Host ""

# === Idempotent reinstall — clean any prior state ===
$Existing = & $NssmPath status $ServiceName 2>$null
if ($Existing) {
    Write-Host "Service $ServiceName exists. Removing for clean reinstall..."
    & $NssmPath stop $ServiceName 2>$null | Out-Null
    Start-Sleep -Seconds 2
    & $NssmPath remove $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 2
    # Wait for SCM to fully clear
    $tries = 0
    while ((Get-Service $ServiceName -ErrorAction SilentlyContinue) -and ($tries -lt 5)) {
        Start-Sleep -Seconds 1
        $tries++
    }
}

# === Install ===
Write-Host "Installing $ServiceName..."
$ArgsArray = $SecondaryArgs.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
& $NssmPath install $ServiceName $PrimaryApp @ArgsArray | Out-Null
& $NssmPath set $ServiceName AppDirectory $PrimaryDir | Out-Null
& $NssmPath set $ServiceName DisplayName "STRATEGIE API (Secondary, port $SecondaryPort)" | Out-Null
& $NssmPath set $ServiceName Description "Phase HA-1 secondary. Load-balanced with STRATEGIE-API via Caddy." | Out-Null
& $NssmPath set $ServiceName Start SERVICE_AUTO_START | Out-Null

# === Env: inherit primary + override port + instance name ===
# Drop any existing UVICORN_PORT / STRATEGIE_INSTANCE_NAME entries
$EnvOut = @()
foreach ($line in $PrimaryEnvLines) {
    if ($line -match '^(UVICORN_PORT|STRATEGIE_INSTANCE_NAME)=') { continue }
    $EnvOut += $line
}
$EnvOut += "UVICORN_PORT=$SecondaryPort"
$EnvOut += "STRATEGIE_INSTANCE_NAME=secondary"

Write-Host "Setting env (LF-separated, $($EnvOut.Count) entries):"
foreach ($e in $EnvOut) { Write-Host "  > $e" }

# NSSM AppEnvironmentExtra: LF separator (NOT CRLF). Each entry: KEY=VALUE.
$EnvBlock = ($EnvOut -join "`n")
& $NssmPath set $ServiceName AppEnvironmentExtra $EnvBlock | Out-Null

# === Logs ===
$LogDir = "C:\Logs\STRATEGIE"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
& $NssmPath set $ServiceName AppStdout "$LogDir\strategie-api-b.stdout.log" | Out-Null
& $NssmPath set $ServiceName AppStderr "$LogDir\strategie-api-b.stderr.log" | Out-Null
& $NssmPath set $ServiceName AppRotateFiles 1 | Out-Null
& $NssmPath set $ServiceName AppRotateBytes 10485760 | Out-Null
& $NssmPath set $ServiceName AppRotateOnline 1 | Out-Null

# === Restart on crash ===
& $NssmPath set $ServiceName AppExit Default Restart | Out-Null
& $NssmPath set $ServiceName AppRestartDelay 5000 | Out-Null

Write-Host ""
Write-Host "DONE."
Write-Host ""
Write-Host "Verify config:"
Write-Host "  & '$NssmPath' get $ServiceName AppParameters"
Write-Host "  & '$NssmPath' get $ServiceName AppEnvironmentExtra"
Write-Host ""
Write-Host "Start + smoke:"
Write-Host "  Start-Service $ServiceName"
Write-Host "  Start-Sleep -Seconds 5"
Write-Host "  Invoke-RestMethod http://localhost:$SecondaryPort/api/v1/health"
Write-Host ""
Write-Host "If start fails, check log:"
Write-Host "  Get-Content C:\Logs\STRATEGIE\strategie-api-b.stderr.log -Tail 30"
