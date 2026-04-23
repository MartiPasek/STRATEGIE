<#
.SYNOPSIS
  Jednim klikem spust cely STRATEGIE stack pro dev: server + task worker + email fetcher.

.DESCRIPTION
  Otevre 3 samostatna PowerShell okna, kazde drzi jeden proces:
    - dev server (port 8003)  --  .\scripts\dev.ps1 -Port 8003
    - task worker              --  .\scripts\task_worker.ps1
    - email fetcher            --  .\scripts\email_fetcher.ps1 -Poll 60

  Kazde okno ma vlastni title (videt v Alt-Tab / Taskbar), takze vis, ktere je ktere.
  Zavrenim kteryhokoliv okna ukoncis dany proces -- ostatni bezi dal.

  Pouzitelne z ploch/zastupce, nebo z Startup folderu (shell:startup) pro
  auto-start pri prihlaseni k Windows.

.PARAMETER Port
  Port na kterem spusti dev server. Default 8003.

.PARAMETER EmailPoll
  Poll interval email fetcheru v sekundach. Default 60.

.PARAMETER TaskPoll
  Poll interval task workera v sekundach. Default 5.

.EXAMPLE
  .\scripts\start_all.ps1
  .\scripts\start_all.ps1 -Port 8002
  .\scripts\start_all.ps1 -EmailPoll 30 -TaskPoll 3
#>

param(
    [int]$Port = 8003,
    [double]$EmailPoll = 60.0,
    [double]$TaskPoll = 5.0
)

$ErrorActionPreference = "Stop"

# Zjistit korenovy adresar repa (rodic scripts/). Nezavisely na tom, odkud
# skript pustis -- .lnk z plochy bude mit working dir jinde.
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = Split-Path -Parent $ScriptRoot

Write-Host ""
Write-Host "== STRATEGIE stack launcher ==" -ForegroundColor Cyan
Write-Host "Repo root : $RepoRoot" -ForegroundColor DarkGray
Write-Host "Dev port  : $Port" -ForegroundColor DarkGray
Write-Host "Email poll: $EmailPoll s" -ForegroundColor DarkGray
Write-Host "Task poll : $TaskPoll s" -ForegroundColor DarkGray
Write-Host ""

# Helper: spusti skript v novem PS okne s vlastnim titlem.
# -NoExit zajisti, ze okno zustane otevrene i po skonceni/crashi, abys videl error.
function Start-DevWindow {
    param(
        [string]$Title,
        [string]$ScriptPath,
        [string]$Args = ""
    )
    # Command: nastavit title + cd do repa + spustit skript s argumenty.
    # Escape uvozovek pro predani pres PowerShell -Command.
    $cmd = "`$Host.UI.RawUI.WindowTitle = '$Title'; " +
           "Set-Location '$RepoRoot'; " +
           "& '$ScriptPath' $Args"
    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $cmd
    )
    Write-Host "  > $Title" -ForegroundColor Green
}

Start-DevWindow `
    -Title "STRATEGIE :: dev server (port $Port)" `
    -ScriptPath (Join-Path $ScriptRoot "dev.ps1") `
    -Args "-Port $Port"

Start-DevWindow `
    -Title "STRATEGIE :: task worker" `
    -ScriptPath (Join-Path $ScriptRoot "task_worker.ps1") `
    -Args "-Poll $TaskPoll"

Start-DevWindow `
    -Title "STRATEGIE :: email fetcher" `
    -ScriptPath (Join-Path $ScriptRoot "email_fetcher.ps1") `
    -Args "-Poll $EmailPoll"

Write-Host ""
Write-Host "Vsechna tri okna spustena. Launcher konci -- zavrit tohle okno je OK." -ForegroundColor Yellow
Write-Host "Kazdy proces bezi samostatne ve svem okne, zavirani = ukonceni procesu." -ForegroundColor DarkGray

# Okno launcheru se samo zavre po par vterinach (aby nezustalo viset jako
# "ctvrte" okno, co nic nedela). Kdyz ho chces zanechat, odstran tuhle radku.
Start-Sleep -Seconds 3
