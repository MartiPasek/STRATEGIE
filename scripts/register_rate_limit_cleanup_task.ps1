# Phase 38.2 - Register Windows Task Scheduler nightly cleanup pro rate_limit buckets.
#
# Spousti se jednorazove jako Administrator na cloud APP.
# Analog STRATEGIE-llm-calls-retention z 25.4. vecer.
#
# Stagger: llm_calls retention bezi 03:00, rate_limit cleanup bezi 03:30.

$ErrorActionPreference = "Stop"

$TaskName    = "STRATEGIE-rate-limit-cleanup"
$ProjectRoot = "C:\Projekty\STRATEGIE"
$ScriptPath  = "$ProjectRoot\scripts\rate_limit_cleanup.py"
$LogPath     = "C:\logs\strategie\rate_limit_cleanup.log"

# Test ze soubor existuje
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script nenalezen: $ScriptPath"
    exit 1
}

# Ensure log directory exists
$LogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Build the inner command (escaped for ScheduledTaskAction Argument string).
# We avoid backtick-double-quote nesting by using single quotes inside.
$InnerCmd = "cd '$ProjectRoot'; python -m poetry run python scripts\rate_limit_cleanup.py *>&1 | Out-File -FilePath '$LogPath' -Append -Encoding UTF8"

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$InnerCmd`""

# Trigger - denne v 03:30 (po llm_calls retention v 03:00)
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:30AM

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Principal - SYSTEM (zadny password potreba)
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
    -TaskName    $TaskName `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Principal   $Principal `
    -Description "Phase 38.2 nightly cleanup expirovanych verify_rate_buckets (retention 7d)."

Write-Host "Registered: $TaskName"
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host ("Next run: {0}" -f $Info.NextRunTime)
Write-Host ""
Write-Host "Manual test (run now):"
Write-Host ("  Start-ScheduledTask -TaskName {0}" -f $TaskName)
Write-Host ""
Write-Host "Log:"
Write-Host ("  Get-Content {0} -Tail 20" -f $LogPath)
