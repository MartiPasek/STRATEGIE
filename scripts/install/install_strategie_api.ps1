# =============================================================================
#  STRATEGIE-API - hlavni aplikace (FastAPI/uvicorn na portu 8002)
#
#  Doplneno 9. 9. 2026 (Jiri Honomichl). Do te doby tato sluzba NEMELA zadny
#  instalacni postup - pri stavbe serveru znovu by se skladala rucne z hlavy.
#  Nastaveni opsano ze SKUTECNE bezici sluzby na 188.11 (registr, 8. 9. 2026).
#
#  KDE SE SPOUSTI: aplikacni server 188.11, PowerShell JAKO SPRAVCE.
#
#  ⛔ TAJEMSTVI: sluzba potrebuje promenne prostredi s tokeny a hesly. V tomhle
#     skriptu NEJSOU a nikdy tu byt nesmi (je v gitu, ktery vidi cela sit).
#     Predej je parametrem -Promenne, napriklad:
#         .\install_strategie_api.ps1 -Promenne @{ STRATEGIE_DEPLOY_TOKEN='...' }
#     Kdyz -Promenne vynechas, uz nastavene promenne zustanou beze zmeny.
#     Nazvy, ktere sluzba k 8. 9. 2026 mela: STRATEGIE_DEPLOY_TOKEN,
#     STRATEGIE_VAULT_KEY, MSSQL188_CONN.
#
#  ⚠️ UCET: sluzba bezi pod uctem .\Administrator (ne LocalSystem) - kvuli pristupu
#     k virtualnimu prostrediu Poetry v profilu toho uctu. NSSM si pri zmene uctu
#     vyzada heslo; do skriptu nepatri.
# =============================================================================
param(
    [string]$Nssm,
    [string]$Repo = 'C:\Projekty\STRATEGIE',
    [string]$Python = 'C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs\strategie-W5adySD1-py3.14\Scripts\python.exe',
    [int]$Port = 8002,
    [string]$Ucet = '.\Administrator',
    [hashtable]$Promenne = @{},
    [switch]$Nespoustet
)
. "$PSScriptRoot\_spolecne.ps1"

if (-not (Test-Spravce)) { Write-Host "CHYBA: spust PowerShell jako spravce." -ForegroundColor Red; return }
Write-Host "1/3 OK - bezim s pravy spravce na $env:COMPUTERNAME." -ForegroundColor Green

$n = Najdi-Nssm -Cesta $Nssm
if (-not (Test-Path $Python)) {
    Write-Host "CHYBA: python virtualniho prostredi nenalezen: $Python" -ForegroundColor Red
    Write-Host "Uprav parametr -Python. Cestu zjistis pres: poetry env info --path" -ForegroundColor Yellow
    return
}
Write-Host "2/3 OK - nssm ($n) i python nalezeny." -ForegroundColor Green

Nastav-Sluzbu -Nssm $n -Jmeno 'STRATEGIE-API' `
    -Program $Python `
    -Parametry ("-m uvicorn apps.api.main:app --host 0.0.0.0 --port {0}" -f $Port) `
    -PracovniSlozka $Repo `
    -NazevKZobrazeni 'STRATEGIE API (uvicorn)' `
    -Popis ("FastAPI/uvicorn na :{0} -- reverse-proxied via Caddy" -f $Port) `
    -Ucet $Ucet `
    -LogStdout 'C:\Logs\STRATEGIE\api-stdout.log' `
    -LogStderr 'C:\Logs\STRATEGIE\api-stderr.log' `
    -Promenne $Promenne `
    -Nespoustet:$Nespoustet | Out-Null

Write-Host "3/3 Hotovo. Overeni: Invoke-RestMethod http://127.0.0.1:$Port/api/v1/api-info" -ForegroundColor Green
