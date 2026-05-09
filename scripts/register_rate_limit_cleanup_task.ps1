# Phase 38.2 — Register Windows Task Scheduler nightly cleanup pro rate_limit buckets.
#
# Spouští se jednorázově jako Administrator na cloud APP.
# Analog STRATEGIE-llm-calls-retention z 25.4. večer.
#
# Stagger: llm_calls retention běží 03:00, rate_limit cleanup běží 03:30
# (oba malé jobs, ale separace pro snadnější diagnostiku).

$ErrorActionPreference = "Stop"

$TaskName = "STRATEGIE-rate-limit-cleanup"
$ProjectRoot = "C:\Projekty\STRATEGIE"
$ScriptPath = "$ProjectRoot\scripts\rate_limit_cleanup.py"
$LogPath = "C:\logs\strategie\rate_limit_cleanup.log"

# Test že soubor existuje
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script nenalezen: $ScriptPath"
    exit 1
}

# Akce — spustit Python script přes poetry, working dir = repo root.
# Logování stdout+stderr do C:\logs\strategie\rate_limit_cleanup.log
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -Command `"cd '$ProjectRoot'; python -m poetry run python scripts\rate_limit_cleanup.py 2>&1 | Tee-Object -FilePath '$LogPath' -Append`""

# Trigger — denně v 03:30 (po llm_calls retention v 03:00)
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:30AM

# Settings — pokud běží během trigger, neskakuj. Pokud neběží OS, run on next start.
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Principal — SYSTEM (žádný password potřeba, full DB access)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Unregister existing (pokud reinstall)
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task: $TaskName"
}

# Register
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Phase 38.2 — Nightly cleanup expirovaných verify_rate_buckets (retention 7d)."

Write-Host "Registered: $TaskName"
Write-Host "Next run: $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)"
Write-Host ""
Write-Host "Manual test (běh ihned):"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "Log:"
Write-Host "  Get-Content $LogPath -Tail 20"
