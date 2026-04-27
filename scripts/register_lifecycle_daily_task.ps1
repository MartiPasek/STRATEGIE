# Registrace Windows Task Scheduler task pro Phase 15e: daily lifecycle cron.
#
# Detekuje stale tasks (open + idle >7d) a archived konverzace ve TTL >90d,
# denne ve 3:30 rano (po llm_calls_retention v 3:00).
#
# Pouziti (jako admin):
#   powershell -ExecutionPolicy Bypass -File .\scripts\register_lifecycle_daily_task.ps1
#
# Po registraci task je v 'Task Scheduler Library' -> hledej "STRATEGIE-lifecycle-daily".
# Spustit rucne: Start-ScheduledTask -TaskName "STRATEGIE-lifecycle-daily"
# Smazat: Unregister-ScheduledTask -TaskName "STRATEGIE-lifecycle-daily" -Confirm:$false

$ErrorActionPreference = 'Stop'

$TaskName = "STRATEGIE-lifecycle-daily"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Script   = Join-Path $RepoRoot "scripts\lifecycle_daily.py"

if (-not (Test-Path $Script)) {
    Write-Error "Skript nenalezen: $Script"
}

# --- Najdi pythona ---
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Error "Python nenalezen v PATH."
}
Write-Host "[INFO] python: $pythonExe"

# --- Action: python -m poetry run python scripts\lifecycle_daily.py ---
$Action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "-m poetry run python scripts\lifecycle_daily.py" `
    -WorkingDirectory $RepoRoot

# --- Trigger: kazdy den ve 3:30 (po llm_calls_retention) ---
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:30am

# --- Settings: stable, retry pri failu, max 30 min ---
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# --- Principal ---
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# --- Description ---
$Description = @"
Phase 15e: denni lifecycle cron.
1. Stale task detection: status='open' + idle >=7d -> 'stale'.
2. Hard-delete TTL: archived + archived_at >=90d -> pending_hard_delete.
   Personal konverzace IMMUNE.
Repo: $RepoRoot
Script: $Script
"@

# --- Pokud uz task existuje, prepise se ---
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[INFO] Task '$TaskName' jiz existuje, prepiseme."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $Description `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal | Out-Null

Write-Host ""
Write-Host "[OK] Task '$TaskName' zaregistrovan." -ForegroundColor Green
Write-Host ""
Write-Host "Overit:    Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "Spustit:   Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Dry run:   python -m poetry run python scripts\lifecycle_daily.py --dry-run"
Write-Host "Historie:  Get-ScheduledTaskInfo -TaskName '$TaskName'"
Write-Host "Smazat:    Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""
