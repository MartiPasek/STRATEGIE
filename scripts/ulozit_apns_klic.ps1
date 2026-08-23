# ulozit_apns_klic.ps1
# Ulozi APNs klic pro iOS notifikace do trezoru fw.app_secret.
# Spoustet na cloud APP (tam, kde bezi STRATEGIE-API) jako Admin.
#
# Pouziti:
#   powershell -ExecutionPolicy Bypass -File .\ulozit_apns_klic.ps1 -KeyPath C:\klice\AuthKey_2YZ86LSQ25.p8
#   (volitelne -SetEnv ... navic doplni APNS_ENABLED=1 do .env)
#   (volitelne -CheckOnly ... jen zkontroluje, co uz v trezoru je, nic nezapise)
#
# Klic se NIKDY nevypisuje do konzole ani do logu - Python si ho nacte primo
# ze souboru a posle do DB jako parametr dotazu. Do prikazove radky se nedostane.
#
# ASCII-only (doctrine #110 - PowerShell nema rad diakritiku/em-dash/sipky).

param(
  [Parameter(Mandatory=$true)]
  [string]$KeyPath,                                  # cesta k AuthKey_XXXXXXXXXX.p8
  [string]$KeyId    = "2YZ86LSQ25",                  # Key ID z developer.apple.com
  [string]$TeamId   = "D3Y6Y63UMA",
  [string]$Topic    = "cz.strategie.mobile",
  [string]$RepoRoot = "C:\Projekty\STRATEGIE",
  [switch]$SetEnv,                                   # doplnit APNS_* do .env
  [switch]$CheckOnly                                 # jen kontrola, nic nezapisovat
)

$ErrorActionPreference = "Stop"

function Log($m){ Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m) }

Log "=== Ulozeni APNs klice do trezoru fw.app_secret ==="

# ------------------------------------------------------------------ kontroly
if(-not (Test-Path $RepoRoot)){ throw "Repo neexistuje: $RepoRoot" }

if(-not $CheckOnly){
  if(-not (Test-Path $KeyPath)){ throw "Soubor s klicem neexistuje: $KeyPath" }
  $raw = Get-Content -Path $KeyPath -Raw
  if($raw -notmatch '-----BEGIN PRIVATE KEY-----'){
    throw "Soubor nevypada jako .p8 klic (chybi -----BEGIN PRIVATE KEY-----): $KeyPath"
  }
  if($raw -notmatch '-----END PRIVATE KEY-----'){
    throw "Soubor je useknuty (chybi -----END PRIVATE KEY-----): $KeyPath"
  }
  Log ("Klic OK: {0} ({1} bajtu), Key ID {2}" -f (Split-Path $KeyPath -Leaf), $raw.Length, $KeyId)
}

# ------------------------------------------------- jak se na tomhle stroji pousti python
# Zavislosti (sqlalchemy, psycopg2) jsou v poetry venv projektu - zkusime nejdriv
# poetry, teprve pak holy python.
Push-Location $RepoRoot
$PyCmd = $null
try {
  & python -m poetry run python -c "import sqlalchemy" 2>$null
  if($LASTEXITCODE -eq 0){ $PyCmd = "poetry" }
} catch {}
if(-not $PyCmd){
  try {
    & python -c "import sqlalchemy" 2>$null
    if($LASTEXITCODE -eq 0){ $PyCmd = "python" }
  } catch {}
}
if(-not $PyCmd){
  Pop-Location
  throw "Nenasel jsem python se sqlalchemy. Zkus v $RepoRoot spustit 'python -m poetry install'."
}
Log ("Python: {0}" -f $PyCmd)

# --------------------------------------------------------------- telo v Pythonu
# Pouziva projektove pripojeni (core.database), takze nepotrebuje zadne heslo
# navic - vezme si stejny connection string jako samotne API.
$PyBody = @'
import sys, pathlib
sys.path.insert(0, ".")
from sqlalchemy import text
from core.database import get_session

cesta_klice = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
key_id = sys.argv[2] if len(sys.argv) > 2 else ""
jen_kontrola = (len(sys.argv) > 3 and sys.argv[3] == "check")

s = get_session()
try:
    s.execute(text(
        "CREATE TABLE IF NOT EXISTS fw.app_secret ("
        " skey text PRIMARY KEY, sval text)"))
    s.commit()

    if not jen_kontrola:
        klic = cesta_klice.read_text(encoding="utf-8").strip()
        if not klic.startswith("-----BEGIN PRIVATE KEY-----"):
            print("CHYBA: soubor nevypada jako .p8 klic")
            sys.exit(2)
        s.execute(text(
            "INSERT INTO fw.app_secret (skey, sval) VALUES (:k1, :v1), (:k2, :v2) "
            "ON CONFLICT (skey) DO UPDATE SET sval = EXCLUDED.sval"),
            {"k1": "apns_key_id", "v1": key_id, "k2": "apns_key_p8", "v2": klic})
        s.commit()
        print("ZAPSANO")

    # Overeni ctenim - klic se NEvypisuje, jen delka a prvni radek.
    rows = s.execute(text(
        "SELECT skey, length(sval) AS delka, left(sval, 27) AS zacatek "
        "FROM fw.app_secret WHERE skey LIKE 'apns%' ORDER BY skey")).mappings().all()
    if not rows:
        print("V TREZORU NIC NENI")
        sys.exit(3)
    for r in rows:
        print("  {0:14s} delka={1:<5} {2}".format(r["skey"], r["delka"], r["zacatek"]))

    ok_id = any(r["skey"] == "apns_key_id" and r["delka"] == 10 for r in rows)
    ok_p8 = any(r["skey"] == "apns_key_p8"
                and r["zacatek"].startswith("-----BEGIN PRIVATE KEY") for r in rows)
    print("OVERENO OK" if (ok_id and ok_p8) else "OVERENI SELHALO")
    sys.exit(0 if (ok_id and ok_p8) else 4)
finally:
    s.close()
'@

$PyFile = Join-Path $env:TEMP ("apns_ulozit_{0}.py" -f (Get-Random))
Set-Content -Path $PyFile -Value $PyBody -Encoding UTF8

try {
  $mode = if($CheckOnly){ "check" } else { "write" }
  $klicArg = if($CheckOnly){ "" } else { $KeyPath }
  if($PyCmd -eq "poetry"){
    & python -m poetry run python $PyFile $klicArg $KeyId $mode
  } else {
    & python $PyFile $klicArg $KeyId $mode
  }
  $rc = $LASTEXITCODE
} finally {
  Remove-Item -Path $PyFile -Force -ErrorAction SilentlyContinue
  Pop-Location
}

if($rc -ne 0){ throw "Ulozeni/overeni selhalo (navratovy kod $rc)." }
Log "Trezor v poradku."

# ------------------------------------------------------------------ .env (volitelne)
if($SetEnv){
  $EnvFile = Join-Path $RepoRoot ".env"
  if(-not (Test-Path $EnvFile)){ throw ".env neexistuje: $EnvFile" }
  Copy-Item $EnvFile ("{0}.bak_{1}" -f $EnvFile, (Get-Date -Format "yyyyMMdd_HHmmss"))
  $obsah = Get-Content $EnvFile

  # Klic samotny do .env NEDAVAME - je v trezoru. Sem jen prepinac a identifikatory.
  $chceme = @{
    "APNS_ENABLED"  = "1"
    "APNS_KEY_ID"   = $KeyId
    "APNS_TEAM_ID"  = $TeamId
    "APNS_TOPIC"    = $Topic
  }
  foreach($k in $chceme.Keys){
    $radek = "{0}={1}" -f $k, $chceme[$k]
    if($obsah -match ("^{0}=" -f [regex]::Escape($k))){
      $obsah = $obsah -replace ("^{0}=.*$" -f [regex]::Escape($k)), $radek
      Log ("  .env: prepsano {0}" -f $k)
    } else {
      $obsah += $radek
      Log ("  .env: doplneno {0}" -f $k)
    }
  }
  Set-Content -Path $EnvFile -Value $obsah -Encoding UTF8
  Log ("Zaloha puvodniho .env je vedle nej (.bak_...).")
}

Write-Host ""
Log "HOTOVO."
Write-Host ""
Write-Host "Co jeste musi probehnout, nez notifikace zacnou chodit:"
Write-Host "  1) zmergovat PR MartiPasek/STRATEGIE#5 (serverova cast notifikaci)"
Write-Host "  2) v $RepoRoot spustit: python -m poetry lock ; python -m poetry install"
Write-Host "     (pribyly h2 - APNs jede vyhradne pres HTTP/2 - a pyjwt[crypto])"
if(-not $SetEnv){
Write-Host "  3) do .env doplnit APNS_ENABLED=1  (nebo spustit tenhle skript s -SetEnv)"
} else {
Write-Host "  3) .env je nastaveny"
}
Write-Host "  4) restartovat sluzbu STRATEGIE-API a v logu zkontrolovat radek:"
Write-Host "     [ios_push] odesilaci smycka nastartovana"
Write-Host "  5) test: POST /api/v1/erp/app/ios/push/test (posle si sam sobe notifikaci)"
