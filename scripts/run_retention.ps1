# Faze 10 -- wrapper pro Windows Task Scheduler.
# Spousti llm_calls_retention.py pres poetry. Kontext: CD do repo rootu aby
# poetry nasel pyproject.toml + vyrstvena .venv.
#
# Task Scheduler konfigurace (registrace viz README / CLAUDE.md workflow):
#   Action  : powershell.exe
#   Args    : -NoProfile -ExecutionPolicy Bypass -File D:\projekty\strategie\scripts\run_retention.ps1
#   Start in: D:\projekty\strategie  (nepovinny kdyz $PSScriptRoot funguje)
#   Trigger : Daily 03:00
#
# Output jde do Task Scheduler historie. Pro logovani do souboru lze
# pripojit: " *>> D:\projekty\strategie\logs\retention.log"
# (v Task args po zavirajici -File ceste).
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] LLM retention start"
python -m poetry run python scripts/llm_calls_retention.py
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] LLM retention done"
