# ============================================================
# Phase HA-1 SMOKE: zero-downtime restart proof
# ============================================================
# ASCII-only (gotcha #110 - PS5.1 cp1250 default breaks em-dash + arrows).
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
        if (-not $Instance) { $Instance = "unknown" }
        if ($Counts.ContainsKey($Instance)) {
            $Counts[$Instance]++
        } else {
            $Counts[$Instance] = 1
        }
        if ($Instance -eq "primary") {
            Write-Host "P" -NoNewline
        } elseif ($Instance -eq "secondary") {
            Write-Host "S" -NoNewline
        } else {
            Write-Host "?" -NoNewline
        }
    } catch {
        $Counts["error"]++
        $ErrCode = "?"
        if ($_.Exception.Response) {
            $ErrCode = [int]$_.Exception.Response.StatusCode
        }
        $ErrorDetails += "[$Elapsed s] $ErrCode $($_.Exception.Message)"
        Write-Host "X" -NoNewline -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host ""
Write-Host "=== Phase HA-1 SMOKE RESULTS ==="
Write-Host ""
foreach ($k in $Counts.Keys) {
    Write-Host "  $k : $($Counts[$k]) requests"
}
Write-Host ""

if ($Counts["error"] -eq 0) {
    Write-Host "OK - ZERO-DOWNTIME ACHIEVED - no errors during restart" -ForegroundColor Green
} elseif ($Counts["error"] -le 2) {
    Write-Host "WARN - ALMOST ZERO-DOWNTIME - $($Counts['error']) errors (Caddy fail detect race)" -ForegroundColor Yellow
    Write-Host "  Reduce health_interval to 1s for tighter detection."
} else {
    Write-Host "FAIL - HA-1 FAIL - $($Counts['error']) errors. Caddy failover not engaged." -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:"
    $ErrorDetails | ForEach-Object { Write-Host "  $_" }
}

Write-Host ""
Write-Host "Verify in fw.diag_log (DBeaver):"
Write-Host "  SELECT id, level, message, extra->>'event' AS evt,"
Write-Host "         extra->>'instance' AS inst, created_at"
Write-Host "  FROM fw.diag_log WHERE module_id = 'api.lifecycle'"
Write-Host "  ORDER BY id DESC LIMIT 10;"
