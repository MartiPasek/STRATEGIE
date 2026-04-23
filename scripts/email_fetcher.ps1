<#
.SYNOPSIS
  Spusti STRATEGIE email fetcher -- polluje Exchange (EWS) a stahuje
  prichozi emaily do email_inbox.

.DESCRIPTION
  Fetcher je out-of-process proti uvicornu -- restart uvicornu neovlivni
  bezici polling. Pro dev staci pustit tenhle skript v samostatnem PS
  okne vedle .\scripts\dev.ps1 a .\scripts\task_worker.ps1.

  Produkce: systemd/Task Scheduler + auto-restart.

  Shutdown: Ctrl+C (dokonci aktualni poll cycle, pak skonci).

.PARAMETER Poll
  Poll interval v sekundach. Default 60. Pro okamzity fetch ma UI tlacitko
  "Fetch now" -- neni potreba kratsi polling.

.PARAMETER Verbose
  Zapne DEBUG logging.

.EXAMPLE
  .\scripts\email_fetcher.ps1
  .\scripts\email_fetcher.ps1 -Poll 30
  .\scripts\email_fetcher.ps1 -Verbose
#>

param(
    [double]$Poll = 60.0,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "== STRATEGIE email fetcher ==" -ForegroundColor Cyan
Write-Host "Poll interval: $Poll s" -ForegroundColor DarkGray
Write-Host "Shutdown: Ctrl+C (graceful po aktualnim pollu)" -ForegroundColor DarkGray
Write-Host ""

$workerArgs = @("run", "python", "scripts/email_fetcher.py", "--poll", "$Poll")
if ($Verbose) {
    $workerArgs += "--verbose"
}

python -m poetry @workerArgs
