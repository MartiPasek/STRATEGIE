# =============================================================================
#  STRATEGIE-RESTART-WATCHER - hlidac znacek (restart aplikace + srovnani zalohy)
#
#  Doplneno 9. 9. 2026 (Jiri Honomichl). Nastaveni opsano ze SKUTECNE bezici
#  sluzby na 188.11 (registr, 8. 9. 2026).
#
#  CO DELA: hlida slozku se znackami. Kdyz nasazeni polozi znacku *.touch,
#  restartuje hlavni aplikaci; kdyz *.refreshsec, srovna zalozni verzi (API B)
#  na aktualni kod. Bez teto sluzby se po nasazeni aplikace NERESTARTUJE
#  a zaloha se neSROVNA - obojí tise, bez chybove hlasky.
#
#  KDE SE SPOUSTI: aplikacni server 188.11, PowerShell JAKO SPRAVCE.
#
#  ⚠️ Sluzba bezi pod LocalSystem zamerne - potrebuje pravo restartovat jine
#     sluzby. Nesnizuj ji opravneni.
#  ⚠️ Log jde do slozky se znackami (D:\Data\STRATEGIE\restart_markers\watcher.log),
#     ne do C:\Logs jako u ostatnich sluzeb - je to tak i na ostrem serveru.
# =============================================================================
param(
    [string]$Nssm,
    [string]$Repo    = 'C:\Projekty\STRATEGIE',
    [string]$Python  = 'python',
    [string]$Znacky  = 'D:\Data\STRATEGIE\restart_markers',
    [switch]$Nespoustet
)
. "$PSScriptRoot\_spolecne.ps1"

if (-not (Test-Spravce)) { Write-Host "CHYBA: spust PowerShell jako spravce." -ForegroundColor Red; return }
$n = Najdi-Nssm -Cesta $Nssm

$skript = Join-Path $Repo 'scripts\restart_watcher.py'
if (-not (Test-Path $skript)) { Write-Host "CHYBA: $skript neexistuje" -ForegroundColor Red; return }
if (-not (Test-Path $Znacky)) {
    Write-Host "  slozka se znackami neexistuje - zakladam: $Znacky" -ForegroundColor Yellow
    try {
        New-Item -ItemType Directory -Force $Znacky -ErrorAction Stop | Out-Null
    } catch {
        Write-Host "CHYBA: slozku se znackami nelze zalozit: $Znacky" -ForegroundColor Red
        Write-Host "       ($($_.Exception.Message))" -ForegroundColor DarkGray
        Write-Host "Nejspis nejsi na aplikacnim serveru, nebo ten disk neexistuje." -ForegroundColor Yellow
        Write-Host "Uprav parametr -Znacky, nebo skript pust na spravnem stroji." -ForegroundColor Yellow
        return
    }
}
Write-Host "1/2 OK - skript i slozka se znackami pripraveny." -ForegroundColor Green

Nastav-Sluzbu -Nssm $n -Jmeno 'STRATEGIE-RESTART-WATCHER' `
    -Program $Python -Parametry $skript -PracovniSlozka $Repo `
    -NazevKZobrazeni 'STRATEGIE-RESTART-WATCHER' `
    -Popis 'Hlidac znacek: *.touch = restart aplikace, *.refreshsec = srovnani zalohy API B' `
    -Ucet 'LocalSystem' `
    -LogStdout (Join-Path $Znacky 'watcher.log') `
    -Nespoustet:$Nespoustet | Out-Null

Write-Host "2/2 Hotovo. Overeni: Get-Content (Join-Path '$Znacky' 'watcher.log') -Tail 20" -ForegroundColor Green
