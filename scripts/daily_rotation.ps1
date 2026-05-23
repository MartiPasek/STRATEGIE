#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 Blue-Green: Daily rotation (PRE-deploy snapshot)
# ============================================================
# Marti's workflow: spustit PRED kazdym `git pull` na primary.
#
# Co dela:
#   1. Snapshot C:\Projekty\STRATEGIE (aktualni) -> C:\Projekty\STRATEGIE-prev
#      (prepise vcerejsi snapshot s dnes-rano-pred-deploy verzi)
#   2. Restart STRATEGIE-API-B (loads new "yesterday's" snapshot)
#
# Po teto rotation Marti muze bezpecne `git pull origin main` na primary:
#   - Pokud nova verze spadne pri startup, Caddy auto-failover na secondary
#   - Secondary serve "dnes rano pred deploy" verzi (last known working)
# ============================================================

$Source = "C:\Projekty\STRATEGIE"
$Target = "C:\Projekty\STRATEGIE-prev"

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
    exit 1
}

Write-Host "=== Phase HA-1 Daily Rotation ==="
Write-Host ""

# Show current commit before snapshot
$srcCommit = (& git -C $Source log -1 --pretty=format:"%h %s" 2>$null)
Write-Host "Source commit: $srcCommit"

if (Test-Path $Target) {
    $tgtCommit = (& git -C $Target log -1 --pretty=format:"%h %s" 2>$null)
    Write-Host "Target commit (will be overwritten): $tgtCommit"
}
Write-Host ""

# 1) Snapshot
Write-Host "Snapshot $Source -> $Target ..."
$StartTime = Get-Date
robocopy $Source $Target /MIR /XJ /NFL /NDL /R:1 /W:1 | Out-Null
$ec = $LASTEXITCODE
$Elapsed = (Get-Date) - $StartTime
# Robocopy exit codes 0-7 = success (8+ = error)
if ($ec -ge 8) {
    Write-Error "Robocopy failed (exit code $ec)"
    exit 1
}
Write-Host "Snapshot done in $([int]$Elapsed.TotalSeconds)s"
Write-Host ""

# 2) Restart secondary to load new snapshot
Write-Host "Restarting STRATEGIE-API-B (loads new snapshot)..."
try {
    Restart-Service STRATEGIE-API-B -Force -ErrorAction Stop
    Start-Sleep -Seconds 5
    $health = Invoke-RestMethod http://localhost:8003/api/v1/health -TimeoutSec 5
    Write-Host "Secondary health: $($health | ConvertTo-Json -Compress)"
} catch {
    Write-Warning "Secondary restart/health-check failed: $($_.Exception.Message)"
    Write-Host "Check log: Get-Content C:\Logs\STRATEGIE\strategie-api-b.stderr.log -Tail 30"
    exit 1
}
Write-Host ""

Write-Host "=== Ready for primary deploy ==="
Write-Host ""
Write-Host "Now safe to:"
Write-Host "  cd $Source"
Write-Host "  git pull origin main"
Write-Host "  Restart-Service STRATEGIE-API"
Write-Host ""
Write-Host "If primary fails to start, Caddy auto-failover to secondary"
Write-Host "(serves snapshot from $Target)."
