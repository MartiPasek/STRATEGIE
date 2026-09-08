# =============================================================================
#  STRATEGIE-EMAIL-FETCHER - stahovani posty (EWS) do schranek person
#
#  Doplneno 9. 9. 2026 (Jiri Honomichl). Nastaveni opsano ze SKUTECNE bezici
#  sluzby na 188.11 (registr, 8. 9. 2026).
#
#  KDE SE SPOUSTI: aplikacni server 188.11, PowerShell JAKO SPRAVCE.
#  ⛔ TAJEMSTVI (prihlaseni do posty) predavej parametrem -Promenne.
#     Prihlasovaci jmeno schranky je citlivy udaj - nesmi do logu ani do gitu.
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
if (-not (Test-Path (Join-Path $Repo 'scripts\email_fetcher.py'))) {
    Write-Host "CHYBA: scripts\email_fetcher.py neni v $Repo" -ForegroundColor Red; return
}
Write-Host "1/2 OK - vse nalezeno." -ForegroundColor Green

Nastav-Sluzbu -Nssm $n -Jmeno 'STRATEGIE-EMAIL-FETCHER' `
    -Program $Python -Parametry 'scripts\email_fetcher.py' -PracovniSlozka $Repo `
    -NazevKZobrazeni 'STRATEGIE Email Fetcher (EWS polling)' `
    -Popis 'EWS polling -> email_inbox per persona (60s default).' `
    -Ucet 'LocalSystem' `
    -LogStdout 'C:\Logs\STRATEGIE\strategie-email-fetcher-stdout.log' `
    -LogStderr 'C:\Logs\STRATEGIE\strategie-email-fetcher-stderr.log' `
    -Promenne $Promenne -Nespoustet:$Nespoustet | Out-Null

Write-Host "2/2 Hotovo. Overeni: Get-Content C:\Logs\STRATEGIE\strategie-email-fetcher-stdout.log -Tail 20" -ForegroundColor Green
