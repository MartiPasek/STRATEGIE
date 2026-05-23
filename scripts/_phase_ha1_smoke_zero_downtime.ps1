# ============================================================
# Phase HA-1 SMOKE: zero-downtime restart proof
# ============================================================
# Run AFTER:
#   - STRATEGIE-API-B installed + started
#   - Caddyfile updated s 2 upstreams + reload
#
# Co testuje:
#   1. Background curl loop /api/v1/health (1× per 200ms = 5 req/s)
#   2. Track which instance odpovídá (primary/secondary)
#   3. During loop → Restart-Service STRATEGIE-API (primary)
#   4. Verify ZERO 502/503 errors — všechny requesty by měly jít přes
#      secondary během restart window (~5-10s)
# ============================================================

param(
    [string]$Url = "https://strategie-ai.com/api/v1/health",
    [int]$DurationSeconds = 60,
    [string]$RestartService = "STRATEGIE-API",
    [int]$RestartAfterSeconds = 10
)

Write-Host "Phase HA-1 zero-downtime smoke test"
Write-Host "  URL:             $Url"
Write-Host "  Duration:        ${DurationSeconds}s"
Write-Host "  Restart service: $RestartService (after ${RestartAfterSeconds}s)"
Write-Host ""

$Counts = @{
    "primary"   = 0
    "secondary" = 0
    "error"     = 0
}
$ErrorDetails = @()
$RestartTriggered = $false
$StartTime = Get-Date

while ((New-TimeSpan -Start $StartTime).TotalSeconds -lt $DurationSeconds) {
    $Elapsed = [int](New-TimeSpan -Start $StartTime).TotalSeconds

    # Trigger restart at marked time
    if (-not $RestartTriggered -and $Elapsed -ge $RestartAfterSeconds) {
        Write-Host "[$Elapsed s] === RESTARTING $RestartService ==="
        Start-Job -ScriptBlock {
            param($svc)
            Restart-Service $svc -Force
        } -ArgumentList $RestartService | Out-Null
        $RestartTriggered = $true
    }

    try {
        $Resp = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 3 -ErrorAction Stop
        $Instance = $Resp.instance
        $Counts[$Instance]++
        $InstanceShort = if ($Instance -eq "primary") { "P" } else { "S" }
        Write-Host "[$Elapsed s] ${InstanceShort}" -NoNewline
    } catch {
        $Counts["error"]++
        $ErrCode = "?"
        if ($_.Exception.Response) {
            $ErrCode = [int]$_.Exception.Response.StatusCode
        }
        $ErrorDetails += "[$Elapsed s] $ErrCode $($_.Exception.Message)"
        Write-Host "[$Elapsed s] X" -NoNewline -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host ""
Write-Host "=== Phase HA-1 SMOKE RESULTS ==="
Write-Host ""
Write-Host "Primary    (8001): $($Counts['primary']) requests"
Write-Host "Secondary  (8002): $($Counts['secondary']) requests"
Write-Host "Errors     (502/timeout): $($Counts['error']) requests"
Write-Host ""

if ($Counts['error'] -eq 0) {
    Write-Host "✓ ZERO-DOWNTIME ACHIEVED — žádné 502/timeout errors during restart" -ForegroundColor Green
} elseif ($Counts['error'] -le 2) {
    Write-Host "⚠ ALMOST ZERO-DOWNTIME — $($Counts['error']) errors (race v Caddy fail detection)" -ForegroundColor Yellow
    Write-Host "  → Pojd snizit health_interval na 1s pro tighter detection."
} else {
    Write-Host "✗ HA-1 FAIL — $($Counts['error']) errors je moc. Caddy failover nezavadi." -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:"
    $ErrorDetails | ForEach-Object { Write-Host "  $_" }
}

Write-Host ""
Write-Host "Verify v fw.diag_log:"
Write-Host "  SELECT id, level, message, extra->>'event', extra->>'instance', created_at"
Write-Host "  FROM fw.diag_log WHERE module_id = 'api.lifecycle'"
Write-Host "  ORDER BY id DESC LIMIT 10;"
Write-Host "  → Expect: startup/shutdown events during restart window"
