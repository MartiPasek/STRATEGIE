<#
.SYNOPSIS
  Spusti STRATEGIE question generator (Marti active learning, Faze 4).

.DESCRIPTION
  Polluje DB: (1) generuje nove otazky ze low-certainty myslenek pres LLM,
  (2) zpracovava textove odpovedi rodicu nocnim LLM batch.

  Default interval 6h. Manualni trigger je k dispozici z UI tlacitkem
  v "Otazky od Marti" modalu (POST /api/v1/marti-questions/generate).

  Produkce: systemd / NSSM jako STRATEGIE-QUESTION-GENERATOR service.

  Shutdown: Ctrl+C (graceful).

.PARAMETER Poll
  Interval v sekundach. Default 21600 (6h).

.PARAMETER Verbose
  DEBUG logging.

.EXAMPLE
  .\scripts\question_generator.ps1
  .\scripts\question_generator.ps1 -Poll 1800    # 30 min pro testovani
#>

param(
    [double]$Poll = 21600.0,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "== STRATEGIE question generator ==" -ForegroundColor Cyan
Write-Host "Poll interval: $Poll s ($($Poll/3600) h)" -ForegroundColor DarkGray
Write-Host "Shutdown: Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

$workerArgs = @("run", "python", "scripts/question_generator.py", "--poll", "$Poll")
if ($Verbose) {
    $workerArgs += "--verbose"
}

python -m poetry @workerArgs
