# setup_api_d.ps1 - jednorazove postaveni prostredi API D (obnova + testovani na nezivych datech)
# Marti 16.6.2026. ASCII-only (doctrine #110). Spousti se na CLOUD APP (10.200.188.11).
# Hesla NEjsou v souboru - postgres heslo dej do promenne prostredi PGPASSWORD pred spustenim,
# nebo pouzij .pgpass. Token do NSSM AppEnvironmentExtra (ne Machine env).
#
# Co to udela:
#   1) Vytvori prazdnou test DB data_db_test na cloud SQL (10.200.188.12).
#   2) Pripravi kopii kodu pro API D (C:\Projekty\STRATEGIE-apid) z aktualni produkce.
#   3) Zaregistruje NSSM sluzbu STRATEGIE-API-D na portu 8004, mirici na data_db_test,
#      v rezimu APID (vypnute odchozi akce - mail/SMS/MCP write).
#   4) Vypise Caddy snippet pro /apid/.
#
# POZN: uprav promenne nize podle reality (cesty, port, user). Pak spust v PowerShellu jako admin.

$ErrorActionPreference = "Stop"

# --- konfigurace (uprav dle reality) ---------------------------------------
$PGHOST   = "10.200.188.12"
$PGUSER   = "postgres"
$TESTDB   = "data_db_test"
$PORT     = "8004"
$SRC      = "C:\Projekty\STRATEGIE"          # produkcni kod (zdroj kopie)
$APID_DIR = "C:\Projekty\STRATEGIE-apid"     # kod pro API D (kopie)
$NSSM     = "C:\Tools\nssm.exe"
$PY       = "$SRC\.venv\Scripts\python.exe"  # uprav, pokud venv jinde
$SVC      = "STRATEGIE-API-D"
# DATABASE_DATA_URL pro API D (heslo NEdavej sem - pouzij placeholder a vloz pri spusteni)
$DATA_URL = "postgresql://strategie:__HESLO__@$PGHOST:5432/$TESTDB"
# ---------------------------------------------------------------------------

Write-Host "== 1) Vytvarim test DB $TESTDB na $PGHOST ==" -ForegroundColor Cyan
& createdb -h $PGHOST -U $PGUSER $TESTDB 2>$null
Write-Host "   (pokud uz existuje, preskoceno)"

Write-Host "== 2) Kopiruji kod do $APID_DIR (bez .git, .venv) ==" -ForegroundColor Cyan
robocopy $SRC $APID_DIR /MIR /XD ".git" ".venv" "node_modules" "__pycache__" /NFL /NDL /NJH /NJS /NP | Out-Null

Write-Host "== 3) Registruji NSSM sluzbu $SVC na portu $PORT ==" -ForegroundColor Cyan
& $NSSM install $SVC $PY "-m" "uvicorn" "apps.api.main:app" "--host" "127.0.0.1" "--port" $PORT
& $NSSM set $SVC AppDirectory $APID_DIR
# Rezim APID: vypne odchozi akce + ukaze na test DB. AppEnvironmentExtra (ne Machine env).
& $NSSM set $SVC AppEnvironmentExtra `
    "STRATEGIE_ENV=apid" `
    "STRATEGIE_READONLY_OUTBOUND=1" `
    ("DATABASE_DATA_URL=" + $DATA_URL)
& $NSSM set $SVC Start SERVICE_DEMAND_START   # rucni start (jen kdyz potrebujes)
Write-Host "   Hotovo. Pred startem nahrad __HESLO__ v DATABASE_DATA_URL skutecnym heslem:"
Write-Host "   nssm set $SVC AppEnvironmentExtra ... DATABASE_DATA_URL=postgresql://strategie:HESLO@$PGHOST:5432/$TESTDB"

Write-Host ""
Write-Host "== 4) Caddy snippet (pridej do Caddyfile k strategie-ai.com) ==" -ForegroundColor Cyan
Write-Host '   handle /apid/* {'
Write-Host '     uri strip_prefix /apid'
Write-Host ("     reverse_proxy 127.0.0.1:" + $PORT)
Write-Host '   }'
Write-Host ""
Write-Host "Hotovo. API D postavene (sluzba je DEMAND - spust pri obnove). Obnovu spoustej scriptem restore_to_apid.ps1." -ForegroundColor Green
