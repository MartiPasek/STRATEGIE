# =============================================================================
#  STRATEGIE-CADDY - brana (HTTPS + smerovani na aplikaci)
#
#  Doplneno 9. 9. 2026 (Jiri Honomichl). Nastaveni opsano ze SKUTECNE bezici
#  sluzby na 188.11 (registr, 8. 9. 2026).
#
#  KDE SE SPOUSTI: aplikacni server 188.11, PowerShell JAKO SPRAVCE.
#
#  ⚠️ POZOR: tohle je brana, pres kterou tece VSECHEN provoz. Kdyz se rozbije,
#     nefunguje web nikomu. Skript proto pred zalozenim sluzby nastaveni OVERI
#     (caddy validate) a bez platneho nastaveni sluzbu nespusti.
#
#  Zive nastaveni je C:\caddy\Caddyfile (NE kopie v projektu - ta je jen sablona).
# =============================================================================
param(
    [string]$Nssm,
    [string]$Caddy  = 'C:\caddy\caddy.exe',
    [string]$Config = 'C:\caddy\Caddyfile',
    [switch]$Nespoustet
)
. "$PSScriptRoot\_spolecne.ps1"

if (-not (Test-Spravce)) { Write-Host "CHYBA: spust PowerShell jako spravce." -ForegroundColor Red; return }
Write-Host "1/4 OK - bezim s pravy spravce na $env:COMPUTERNAME." -ForegroundColor Green

$n = Najdi-Nssm -Cesta $Nssm
foreach ($c in @($Caddy, $Config)) {
    if (-not (Test-Path $c)) { Write-Host "CHYBA: nenalezeno: $c" -ForegroundColor Red; return }
}
Write-Host "2/4 OK - nssm, caddy.exe i nastaveni nalezeny." -ForegroundColor Green

Write-Host "3/4 Overuji nastaveni brany pred zalozenim sluzby..." -ForegroundColor Cyan
$vysledek = & $Caddy validate --config $Config 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "CHYBA: nastaveni brany NENI platne - sluzbu nezakladam." -ForegroundColor Red
    $vysledek | Select-Object -Last 15
    return
}
Write-Host "     nastaveni je platne." -ForegroundColor Green

Nastav-Sluzbu -Nssm $n -Jmeno 'STRATEGIE-CADDY' `
    -Program $Caddy `
    -Parametry ("run --config {0}" -f $Config) `
    -PracovniSlozka (Split-Path $Caddy -Parent) `
    -NazevKZobrazeni 'STRATEGIE Caddy reverse proxy' `
    -Popis 'Caddy: HTTPS termination + reverse_proxy localhost:8002' `
    -Ucet 'LocalSystem' `
    -LogStdout 'C:\Logs\STRATEGIE\caddy-stdout.log' `
    -LogStderr 'C:\Logs\STRATEGIE\caddy-stderr.log' `
    -Nespoustet:$Nespoustet | Out-Null

Write-Host "4/4 Hotovo. Overeni zvenku: https://strategie-ai.com/api/v1/health" -ForegroundColor Green
Write-Host "     Zmeny nastaveni za behu se delaji pres admin API (port 2019), ne restartem." -ForegroundColor DarkGray
