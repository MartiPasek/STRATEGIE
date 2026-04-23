<#
.SYNOPSIS
  Spusti STRATEGIE task worker -- polluje DB a zpracovava AI tasky.

.DESCRIPTION
  Worker je out-of-process proti uvicornu -- restart uvicornu (napr. po
  code change) neovlivni bezici tasky. Pro dev staci pustit tenhle skript
  v samostatnem PS okne vedle .\scripts\dev.ps1.

  Produkce: systemd/Task Scheduler + auto-restart.

  Shutdown: Ctrl+C (dokonci aktualni task batch, pak skonci).

.PARAMETER Poll
  Poll interval v sekundach. Default 5. Kratsi = svizenejsi reakce, vetsi DB zatez.

.PARAMETER Batch
  Max pocet tasku zpracovanych v jednom pollu. Default 3.

.PARAMETER Verbose
  Zapne DEBUG logging.

.EXAMPLE
  .\scripts\task_worker.ps1
  .\scripts\task_worker.ps1 -Poll 2 -Batch 5
  .\scripts\task_worker.ps1 -Verbose
#>

param(
    [double]$Poll = 5.0,
    [int]$Batch = 3,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "== STRATEGIE task worker ==" -ForegroundColor Cyan
Write-Host "Poll interval: $Poll s | Batch: $Batch" -ForegroundColor DarkGray
Write-Host "Shutdown: Ctrl+C (graceful po aktualnim batchi)" -ForegroundColor DarkGray
Write-Host ""

$workerArgs = @("run", "python", "scripts/task_worker.py",
                "--poll", "$Poll", "--batch", "$Batch")
if ($Verbose) {
    $workerArgs += "--verbose"
}

python -m poetry @workerArgs
