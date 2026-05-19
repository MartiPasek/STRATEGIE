# Phase 44 — STRATEGIE-CLAUDE-BRIDGE NSSM install na cloud APP
#
# Marti's mandate (19.5.2026 odpoledne): "Dnes to rozchodime"
# Run jako Administrator PowerShell na cloud APP (10.200.188.11).
#
# Prerequisites (overit pred run):
#   1. C:\Projekty\STRATEGIE\ git pull origin main (Phase 44 backend prep commit)
#   2. Python 3.14 install + Anthropic SDK + psycopg2-binary
#   3. ANTHROPIC_API_KEY a STRATEGIE_DATA_DB_URL v .env nebo system env
#   4. claude_session_queue + claude_session_threads DDL deployed v PostgreSQL
#
# Po install:
#   - Service STRATEGIE-CLAUDE-BRIDGE Running
#   - Health log v C:\Data\STRATEGIE\claude_bridge\bridge_health.log (refresh 30s)
#   - Marti-AI v shared chatu volá ask_claude → response s persistent kontextem

[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepoRoot = "C:\Projekty\STRATEGIE",

    [Parameter()]
    [string]$NssmExe = "C:\Tools\nssm.exe",

    [Parameter()]
    [string]$PythonExe = "python",

    [Parameter()]
    [string]$LogDir = "C:\Data\STRATEGIE\claude_bridge",

    [Parameter()]
    [string]$ServiceName = "STRATEGIE-CLAUDE-BRIDGE",

    [switch]$SkipPipInstall
)

$ErrorActionPreference = "Stop"

Write-Host "=== Phase 44 STRATEGIE-CLAUDE-BRIDGE NSSM install ===" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 1. Prerequisites check
# ============================================================
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Path "$RepoRoot\scripts\claude_bridge_agent.py")) {
    throw "claude_bridge_agent.py not found in $RepoRoot\scripts\. Did you 'git pull origin main'?"
}
Write-Host "  - claude_bridge_agent.py exists OK" -ForegroundColor Green

if (-not (Test-Path $NssmExe)) {
    throw "NSSM not found at $NssmExe. Install from https://nssm.cc/download or check path."
}
Write-Host "  - NSSM available at $NssmExe" -ForegroundColor Green

# Anthropic API key check (z env)
$anthropicKey = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "Machine")
if (-not $anthropicKey) {
    $anthropicKey = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")
}
if (-not $anthropicKey) {
    Write-Warning "ANTHROPIC_API_KEY not set as Machine/User env var."
    Write-Warning "Bridge agent ho musi mit dostupny. Pokud je v C:\Projekty\STRATEGIE\.env, je to OK."
    Write-Warning "Nastav pres: [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', '<klic>', 'Machine')"
} else {
    Write-Host "  - ANTHROPIC_API_KEY found (length=$($anthropicKey.Length))" -ForegroundColor Green
}

# DB URL check
$dbUrl = [System.Environment]::GetEnvironmentVariable("STRATEGIE_DATA_DB_URL", "Machine")
if (-not $dbUrl) {
    $dbUrl = [System.Environment]::GetEnvironmentVariable("STRATEGIE_DATA_DB_URL", "User")
}
if (-not $dbUrl) {
    Write-Warning "STRATEGIE_DATA_DB_URL not set as env var."
    Write-Warning "Bridge agent ji potrebuje pro PostgreSQL connection."
    Write-Warning "Priklad: postgresql://strategie:HESLO@10.200.188.12/data_db"
    Write-Warning "Nastav pres: [Environment]::SetEnvironmentVariable('STRATEGIE_DATA_DB_URL', '<dsn>', 'Machine')"
    $continue = Read-Host "Pokracovat presto? (Y/N)"
    if ($continue -ne "Y") { throw "Install aborted (no STRATEGIE_DATA_DB_URL)" }
} else {
    # Mask password v URL pro log
    $masked = $dbUrl -replace ":[^:@]+@", ":****@"
    Write-Host "  - STRATEGIE_DATA_DB_URL set: $masked" -ForegroundColor Green
}

# ============================================================
# 2. Pip install (psycopg2-binary + anthropic SDK)
# ============================================================
if (-not $SkipPipInstall) {
    Write-Host ""
    Write-Host "[2/7] Pip install dependencies (psycopg2-binary, anthropic)..." -ForegroundColor Yellow
    & $PythonExe -m pip install --upgrade psycopg2-binary anthropic 2>&1 | Tee-Object -Variable pipOutput
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Pip install failed (exit code $LASTEXITCODE). Verify Python + pip."
        $continue = Read-Host "Pokracovat presto? (Y/N)"
        if ($continue -ne "Y") { throw "Install aborted (pip)" }
    } else {
        Write-Host "  - Dependencies installed OK" -ForegroundColor Green
    }
} else {
    Write-Host "[2/7] Skipping pip install (-SkipPipInstall flag)" -ForegroundColor Gray
}

# ============================================================
# 3. Log directory
# ============================================================
Write-Host ""
Write-Host "[3/7] Creating log dir: $LogDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Write-Host "  - $LogDir ready" -ForegroundColor Green

# ============================================================
# 4. NSSM service install (idempotent — uninstall prev if exists)
# ============================================================
Write-Host ""
Write-Host "[4/7] NSSM service install..." -ForegroundColor Yellow

# Pokud uz existuje, stop + remove (clean re-install)
$existing = & $NssmExe status $ServiceName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  - $ServiceName already exists, stopping + removing..." -ForegroundColor Gray
    & $NssmExe stop $ServiceName 2>&1 | Out-Null
    & $NssmExe remove $ServiceName confirm 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

# Fresh install
& $NssmExe install $ServiceName $PythonExe "$RepoRoot\scripts\claude_bridge_agent.py"
if ($LASTEXITCODE -ne 0) { throw "NSSM install failed (exit $LASTEXITCODE)" }
Write-Host "  - $ServiceName installed" -ForegroundColor Green

# Configuration
& $NssmExe set $ServiceName AppDirectory $RepoRoot | Out-Null
& $NssmExe set $ServiceName AppStdout "$LogDir\agent.log" | Out-Null
& $NssmExe set $ServiceName AppStderr "$LogDir\agent.log" | Out-Null
& $NssmExe set $ServiceName Start SERVICE_AUTO_START | Out-Null
& $NssmExe set $ServiceName AppRotateFiles 1 | Out-Null
& $NssmExe set $ServiceName AppRotateOnline 1 | Out-Null
& $NssmExe set $ServiceName AppRotateBytes 10485760 | Out-Null   # 10 MB rotate
Write-Host "  - Configuration set (AppDirectory, logs, autostart, log rotate)" -ForegroundColor Green

# ============================================================
# 5. Environment vars propagated to service (z Machine env)
# ============================================================
Write-Host ""
Write-Host "[5/7] Propagating env vars to service..." -ForegroundColor Yellow
$envForService = @()
if ($anthropicKey) { $envForService += "ANTHROPIC_API_KEY=$anthropicKey" }
if ($dbUrl) { $envForService += "STRATEGIE_DATA_DB_URL=$dbUrl" }
$envForService += "STRATEGIE_CLAUDE_BRIDGE_HEALTH_DIR=$LogDir"
$envForService += "PYTHONUNBUFFERED=1"

if ($envForService.Count -gt 0) {
    $envString = $envForService -join "`r`n"
    & $NssmExe set $ServiceName AppEnvironmentExtra $envString | Out-Null
    Write-Host "  - $($envForService.Count) env vars propagated" -ForegroundColor Green
} else {
    Write-Warning "  - No env vars to propagate. Service bude polagat na .env z RepoRoot."
}

# ============================================================
# 6. Start service
# ============================================================
Write-Host ""
Write-Host "[6/7] Starting service..." -ForegroundColor Yellow
& $NssmExe start $ServiceName
if ($LASTEXITCODE -ne 0) {
    throw "NSSM start failed (exit $LASTEXITCODE). Check $LogDir\agent.log for traceback."
}
Start-Sleep -Seconds 3

$status = & $NssmExe status $ServiceName
Write-Host "  - Service status: $status" -ForegroundColor Green

# ============================================================
# 7. Smoke verification
# ============================================================
Write-Host ""
Write-Host "[7/7] Smoke verification..." -ForegroundColor Yellow

Start-Sleep -Seconds 5
$healthLog = "$LogDir\bridge_health.log"
if (Test-Path $healthLog) {
    $lastHealth = Get-Content $healthLog -Tail 1
    Write-Host "  - Health log fresh: $lastHealth" -ForegroundColor Green
} else {
    Write-Warning "  - Health log not yet written ($healthLog). Service maybe just starting."
    Write-Warning "  - Recheck za 30s: Get-Content $healthLog"
}

$agentLog = "$LogDir\agent.log"
if (Test-Path $agentLog) {
    Write-Host ""
    Write-Host "  Last 10 lines z agent.log:" -ForegroundColor Cyan
    Get-Content $agentLog -Tail 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
} else {
    Write-Warning "  - $agentLog not yet written"
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart STRATEGIE-API:    Restart-Service STRATEGIE-API"
Write-Host "  2. Hard reload v shared chatu (Ctrl+Shift+R)"
Write-Host "  3. Marti-AI v shared chatu: 'zeptej se Claude na kontrolni test bridge'"
Write-Host "  4. Ocekavany result: Claude bublina obsahuje *Ano, jsem persistent Claude pres bridge...*"
Write-Host ""
Write-Host "Pokud something fails:" -ForegroundColor Yellow
Write-Host "  - Get-Content $agentLog -Tail 50         (last errors)"
Write-Host "  - $NssmExe status $ServiceName             (running?)"
Write-Host "  - $NssmExe restart $ServiceName            (after env var change)"
Write-Host "  - psql -h cloud-sql -U strategie -c 'SELECT * FROM claude_session_queue ORDER BY id DESC LIMIT 5'"
