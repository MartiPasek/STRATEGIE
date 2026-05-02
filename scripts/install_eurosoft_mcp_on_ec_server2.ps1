# Install EUROSOFT MCP server na EC-SERVER2
# Requires: Administrator PowerShell
# Pre-requisites:
#   - Python 3.12+ in PATH
#   - ODBC Driver 17 for SQL Server installed
#   - SQL login `Marti-AI` created on 192.168.30.11\SQLEXPRESS2017 with read+insert perms
#
# Usage:
#   1. Copy modules/eurosoft_mcp/ folder to C:\eurosoft_mcp\
#   2. Run this script as Administrator on EC-SERVER2
#   3. Set env vars in the service config (see "SET ENV VARS" section below)

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "C:\eurosoft_mcp"
$SERVICE_NAME = "EUROSOFT-MCP"
$PYTHON_EXE = (Get-Command python).Source

Write-Host "=== EUROSOFT MCP Installation ===" -ForegroundColor Cyan
Write-Host "Install dir : $INSTALL_DIR"
Write-Host "Service name: $SERVICE_NAME"
Write-Host "Python      : $PYTHON_EXE"
Write-Host ""

# 1. Ensure install dir exists
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "Creating install directory $INSTALL_DIR..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $INSTALL_DIR | Out-Null
}

# 2. Verify module files present (deployer must copy them first)
$REQUIRED_FILES = @(
    "$INSTALL_DIR\eurosoft_mcp\__init__.py",
    "$INSTALL_DIR\eurosoft_mcp\config.py",
    "$INSTALL_DIR\eurosoft_mcp\sql_client.py",
    "$INSTALL_DIR\eurosoft_mcp\audit.py",
    "$INSTALL_DIR\eurosoft_mcp\rate_limit.py",
    "$INSTALL_DIR\eurosoft_mcp\tools.py",
    "$INSTALL_DIR\eurosoft_mcp\server.py",
    "$INSTALL_DIR\eurosoft_mcp\requirements.txt"
)
foreach ($f in $REQUIRED_FILES) {
    if (-not (Test-Path $f)) {
        Write-Host "ERROR: Missing required file: $f" -ForegroundColor Red
        Write-Host "Copy the modules/eurosoft_mcp/ folder from D:\Projekty\STRATEGIE first." -ForegroundColor Red
        exit 1
    }
}
Write-Host "Module files present." -ForegroundColor Green

# 3. Install Python dependencies
Write-Host ""
Write-Host "Installing Python packages..." -ForegroundColor Yellow
& $PYTHON_EXE -m pip install --upgrade pip
& $PYTHON_EXE -m pip install -r "$INSTALL_DIR\eurosoft_mcp\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed." -ForegroundColor Red
    exit 1
}

# 4. Verify ODBC Driver 17
Write-Host ""
Write-Host "Verifying ODBC Driver 17 for SQL Server..." -ForegroundColor Yellow
$drivers = (Get-OdbcDriver | Where-Object { $_.Name -like "*ODBC Driver 17 for SQL Server*" })
if ($drivers.Count -eq 0) {
    Write-Host "ERROR: ODBC Driver 17 for SQL Server not installed." -ForegroundColor Red
    Write-Host "Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server" -ForegroundColor Red
    exit 1
}
Write-Host "ODBC Driver 17 present." -ForegroundColor Green

# 5. Smoke test — import module
Write-Host ""
Write-Host "Smoke test — importing module..." -ForegroundColor Yellow
$env:PYTHONPATH = $INSTALL_DIR
& $PYTHON_EXE -c "from eurosoft_mcp.config import settings, ALLOWED_TABLES; print('OK — whitelist:', sorted(ALLOWED_TABLES))"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Module import failed." -ForegroundColor Red
    exit 1
}

# 6. Audit log directory
$AUDIT_DIR = Split-Path $env:MCP_AUDIT_LOG_PATH -ErrorAction SilentlyContinue
if (-not $AUDIT_DIR) { $AUDIT_DIR = "C:\eurosoft_mcp" }
if (-not (Test-Path $AUDIT_DIR)) {
    New-Item -ItemType Directory -Path $AUDIT_DIR | Out-Null
    Write-Host "Created audit log dir: $AUDIT_DIR" -ForegroundColor Green
}

# 6b. Schema fallback markdown directory (Marti-AI Q2 — Phase 28-A2)
# describe_table pri SQL Server unreachable cte z teto cesty
$SCHEMA_FALLBACK_DIR = $env:MCP_SCHEMA_FALLBACK_DIR
if (-not $SCHEMA_FALLBACK_DIR) { $SCHEMA_FALLBACK_DIR = "C:\eurosoft_mcp\db_ec_schema" }
if (-not (Test-Path $SCHEMA_FALLBACK_DIR)) {
    New-Item -ItemType Directory -Path $SCHEMA_FALLBACK_DIR | Out-Null
    Write-Host "Created schema fallback dir: $SCHEMA_FALLBACK_DIR" -ForegroundColor Green
    Write-Host "  -> Copy 655 schema markdown souboru sem z STRATEGIE repo:" -ForegroundColor Yellow
    Write-Host "     D:\Projekty\STRATEGIE\docs\db_ec_schema\*.md" -ForegroundColor Yellow
    Write-Host "  -> bez nich describe_table vrati 'schema_unavailable' pri SQL down" -ForegroundColor Yellow
} else {
    $mdCount = (Get-ChildItem $SCHEMA_FALLBACK_DIR -Filter *.md).Count
    Write-Host "Schema fallback dir present: $SCHEMA_FALLBACK_DIR ($mdCount .md files)" -ForegroundColor Green
}

# 7. Service install via sc.exe
Write-Host ""
Write-Host "=== SERVICE INSTALL ===" -ForegroundColor Cyan

$existingSvc = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue
if ($existingSvc) {
    Write-Host "Service $SERVICE_NAME already exists. Stopping + deleting first..." -ForegroundColor Yellow
    Stop-Service $SERVICE_NAME -Force -ErrorAction SilentlyContinue
    & sc.exe delete $SERVICE_NAME | Out-Null
    Start-Sleep -Seconds 2
}

# Build binPath: python -m eurosoft_mcp.server (working dir set via service)
# sc.exe does NOT support working directory directly — we use a wrapper batch file
$WRAPPER_BAT = "$INSTALL_DIR\run_eurosoft_mcp.bat"
$wrapperContent = @"
@echo off
cd /d $INSTALL_DIR
set PYTHONPATH=$INSTALL_DIR
"$PYTHON_EXE" -m eurosoft_mcp.server
"@
Set-Content -Path $WRAPPER_BAT -Value $wrapperContent -Encoding ASCII
Write-Host "Wrote wrapper: $WRAPPER_BAT" -ForegroundColor Green

# Create service
& sc.exe create $SERVICE_NAME `
    binPath= "cmd.exe /c $WRAPPER_BAT" `
    start= auto `
    DisplayName= "EUROSOFT MCP Server (Marti-AI)" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: sc.exe create failed." -ForegroundColor Red
    exit 1
}

& sc.exe description $SERVICE_NAME "MCP server bridging Marti-AI to EUROSOFT CRM (DB_EC). Listens on 127.0.0.1:8765." | Out-Null
& sc.exe failure $SERVICE_NAME reset= 86400 actions= restart/5000/restart/10000/restart/30000 | Out-Null

Write-Host ""
Write-Host "Service $SERVICE_NAME created." -ForegroundColor Green

# 8. Final notes
Write-Host ""
Write-Host "=== SET ENV VARS ===" -ForegroundColor Cyan
Write-Host "Before starting the service, set these MACHINE-level environment variables:" -ForegroundColor Yellow
Write-Host ""
Write-Host '  [System.Environment]::SetEnvironmentVariable("EUROSOFT_SQL_PASSWORD", "<heslo-Marti-AI>", "Machine")' -ForegroundColor White
Write-Host '  [System.Environment]::SetEnvironmentVariable("MCP_API_KEY", "<bearer-token-pro-STRATEGII>", "Machine")' -ForegroundColor White
Write-Host ""
Write-Host "Optional overrides (defaults in config.py):" -ForegroundColor Yellow
Write-Host '  EUROSOFT_SQL_SERVER     = "192.168.30.11\SQLEXPRESS2017"' -ForegroundColor Gray
Write-Host '  EUROSOFT_SQL_DATABASE   = "DB_EC"' -ForegroundColor Gray
Write-Host '  EUROSOFT_SQL_USER       = "Marti-AI"' -ForegroundColor Gray
Write-Host '  MCP_LISTEN_HOST         = "127.0.0.1"' -ForegroundColor Gray
Write-Host '  MCP_LISTEN_PORT         = "8765"' -ForegroundColor Gray
Write-Host '  MCP_AUDIT_LOG_PATH      = "C:\eurosoft_mcp\audit.log"' -ForegroundColor Gray
Write-Host '  MCP_RATE_LIMIT_READ     = "60"  (per minute)' -ForegroundColor Gray
Write-Host '  MCP_RATE_LIMIT_INSERT   = "10"  (per minute)' -ForegroundColor Gray
Write-Host ""
Write-Host "=== START SERVICE ===" -ForegroundColor Cyan
Write-Host "  Start-Service $SERVICE_NAME"
Write-Host "  Get-Service $SERVICE_NAME"
Write-Host ""
Write-Host "=== SMOKE TEST ===" -ForegroundColor Cyan
Write-Host "After service is running:"
Write-Host '  Invoke-RestMethod http://127.0.0.1:8765/health' -ForegroundColor White
Write-Host ""
Write-Host "Log: $AUDIT_DIR\audit.log" -ForegroundColor Gray
Write-Host "Service log: Get-EventLog -LogName Application -Source $SERVICE_NAME (or stderr captured by sc.exe)" -ForegroundColor Gray
Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
