# =============================================================================
#  STRATEGIE-TASK-WORKER - zpracovani fronty uloh
#  (odchozi SMS a e-maily, prepis hlasu, odlozene ulohy)
#
#  Doplneno 9. 9. 2026 (Jiri Honomichl). Nastaveni opsano ze SKUTECNE bezici
#  sluzby na 188.11 (registr, 8. 9. 2026).
#
#  KDE SE SPOUSTI: aplikacni server 188.11, PowerShell JAKO SPRAVCE.
#  ⛔ TAJEMSTVI predavej parametrem -Promenne, do skriptu nepatri.
# =============================================================================
param(
    [string]$Nssm,
    [string]$Repo = 'C:\Projekty\STRATEGIE',
    [string]$Python = 'C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs\strategie-W5adySD1-py3.14\Scripts\python.exe',
    [hashtable]$Promenne = @{},
    [switch]$Nespoustet
)
. "$PSScriptRoot\_spolecne.ps1"

if (-not (Test-Spravce)) { Write-Host "CHYBA: spust PowerShell jako spravce." -ForegroundColor Red; return }
$n = Najdi-Nssm -Cesta $Nssm
if (-not (Test-Path $Python)) { Write-Host "CHYBA: python nenalezen: $Python" -ForegroundColor Red; return }
if (-not (Test-Path (Join-Path $Repo 'scripts\task_worker.py'))) {
    Write-Host "CHYBA: scripts\task_worker.py neni v $Repo" -ForegroundColor Red; return
}
Write-Host "1/2 OK - vse nalezeno." -ForegroundColor Green

Nastav-Sluzbu -Nssm $n -Jmeno 'STRATEGIE-TASK-WORKER' `
    -Program $Python -Parametry 'scripts\task_worker.py' -PracovniSlozka $Repo `
    -NazevKZobrazeni 'STRATEGIE Task Worker' `
    -Popis 'Out-of-process task queue runner (auto-reply SMS, email send, Whisper, ...)' `
    -Ucet 'LocalSystem' `
    -LogStdout 'C:\Logs\STRATEGIE\strategie-task-worker-stdout.log' `
    -LogStderr 'C:\Logs\STRATEGIE\strategie-task-worker-stderr.log' `
    -Promenne $Promenne -Nespoustet:$Nespoustet | Out-Null

Write-Host "2/2 Hotovo. Overeni: Get-Content C:\Logs\STRATEGIE\strategie-task-worker-stdout.log -Tail 20" -ForegroundColor Green
