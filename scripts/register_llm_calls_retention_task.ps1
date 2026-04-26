# Registrace Windows Task Scheduler task pro denni retenci llm_calls.
#
# Smaze radky starsi nez 30 dni, denne ve 3:00 rano (nizka aktivita).
#
# Pouziti (jako admin):
#   powershell -ExecutionPolicy Bypass -File .\scripts\register_llm_calls_retention_task.ps1
#
# Po registraci task je v 'Task Scheduler Library' -> hledej "STRATEGIE-llm-calls-retention".
# Spustit rucne: Start-ScheduledTask -TaskName "STRATEGIE-llm-calls-retention"
# Smazat: Unregister-ScheduledTask -TaskName "STRATEGIE-llm-calls-retention" -Confirm:$false

$ErrorActionPreference = 'Stop'

$TaskName = "STRATEGIE-llm-calls-retention"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Script   = Join-Path $RepoRoot "scripts\llm_calls_retention.py"

if (-not (Test-Path $Script)) {
    Write-Error "Skript nenalezen: $Script"
}

# --- Najdi pythona pro poetry env (pres `python -m poetry env info --path`) ---
# Pokud poetry neni v PATH, zkusim python -m poetry primo.
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Error "Python nenalezen v PATH. Nainstaluj Python nebo doplnim PATH."
}
Write-Host "[INFO] python: $pythonExe"

# --- Action: spusti python -m poetry run python scripts\llm_calls_retention.py ---
# Pracovni adresar repo root, aby poetry nasel pyproject.toml.
$Action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "-m poetry run python scripts\llm_calls_retention.py" `
    -WorkingDirectory $RepoRoot

# --- Trigger: kazdy den ve 3:00 ---
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:00am

# --- Settings: bezi i pri spanku, retry pri failu, max 30 minut ---
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# --- Principal: bezi pod aktualnim userem (nebo SYSTEM pokud je preferovano) ---
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# --- Description ---
$Description = @"
Faze 14 prep #4: denni cleanup tabulky llm_calls (retence 30 dni).
Smaze llm_calls.created_at < now() - interval '30 days'.
Repo: $RepoRoot
Script: $Script
Pres poetry env zajistime spravne dependencies.
"@

# --- Pokud uz task existuje, prepise se. ---
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
Write-Host "Historie:  Get-ScheduledTaskInfo -TaskName '$TaskName'"
Write-Host "Smazat:    Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""
Write-Host "Prvni spusteni: zitra 3:00 rano. Pro test ted spust Start-ScheduledTask."
