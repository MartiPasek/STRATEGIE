# =====================================================================
#  setup_keystore.ps1  —  rozbali upload keystore do APP/Mobile/
# =====================================================================
#  Pripravi podpisovy klic pro build play AAB. Rozbali z dodaneho ZIPu
#  (od Martiho) soubory:
#     - strategie-release.jks    (upload klic)
#     - keystore.properties      (cesta ke klici + 3 hesla)
#  do slozky APP/Mobile/ a OVERI, ze je git ignoruje.
#
#  !!! BEZPECNOST — TAJNA DATA NIKDY NA GIT !!!
#  strategie-release.jks i keystore.properties jsou PODPISOVY KLIC + HESLA.
#  Nesmi se dostat do gitu, na chat, do mailu ani nikam ven. Tento repo je
#  proti tomu pojisteny v APP/Mobile/.gitignore (radky `*.jks`,
#  `/keystore.properties`). Tento skript to navic pred koncem zkontroluje a
#  kdyby nahodou ignor nesedel, SKONCI s chybou (radeji nic nez unik klice).
#  Klic dostavas od Martiho JEN bezpecnym kanalem (USB osobne / Bitwarden /
#  7z s heslem). Tento skript zadna hesla nevypisuje na obrazovku.
#
#  Pouziti (PowerShell, ze slozky APP/Mobile nebo odkudkoli):
#     ./setup_keystore.ps1
#     ./setup_keystore.ps1 -ZipPath "C:\cesta\strategie-upload-key.zip"
# =====================================================================

param(
    [string]$ZipPath = (Join-Path $env:USERPROFILE 'Downloads\strategie-upload-key.zip'),
    [string]$MobileDir = (Join-Path $PSScriptRoot '.')
)

$ErrorActionPreference = 'Stop'
$MobileDir = (Resolve-Path $MobileDir).Path

if (-not (Test-Path $ZipPath)) {
    Write-Host "CHYBA: ZIP nenalezen: $ZipPath" -ForegroundColor Red
    Write-Host "Predej cestu: ./setup_keystore.ps1 -ZipPath 'C:\...\strategie-upload-key.zip'"
    exit 1
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$want = @('strategie-release.jks', 'keystore.properties')
$archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    foreach ($name in $want) {
        $entry = $archive.Entries | Where-Object { $_.FullName -eq $name }
        if ($null -eq $entry) {
            Write-Host "CHYBA: v ZIPu chybi '$name'." -ForegroundColor Red
            exit 1
        }
        $out = Join-Path $MobileDir $name
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $out, $true)
        # Vypisuji JEN nazev a velikost — NIKDY obsah (zadna hesla na obrazovku).
        $len = (Get-Item $out).Length
        Write-Host "OK  rozbaleno: $name ($len B)" -ForegroundColor Green
    }
} finally {
    $archive.Dispose()
}

# --- BEZPECNOSTNI POJISTKA: oba soubory MUSI byt git-ignored -----------
Write-Host ""
Write-Host "Kontrola, ze git tajne soubory ignoruje..." -ForegroundColor Cyan
$leak = $false
foreach ($name in $want) {
    $rel = "APP/Mobile/$name"
    & git -C (Split-Path (Split-Path $MobileDir)) check-ignore -q $rel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "!!! VAROVANI: $rel NENI git-ignored — tajny soubor by mohl jit na git!" -ForegroundColor Red
        $leak = $true
    } else {
        Write-Host "OK  git ignoruje: $rel" -ForegroundColor Green
    }
}
if ($leak) {
    Write-Host ""
    Write-Host "ZASTAVENO. Doplnte do APP/Mobile/.gitignore radky '*.jks' a '/keystore.properties'," -ForegroundColor Red
    Write-Host "pak spustte skript znovu. NEcommitujte, dokud to nesedi." -ForegroundColor Red
    exit 2
}

Write-Host ""
Write-Host "HOTOVO. Keystore je pripraveny. Dalsi krok = podepsany build:" -ForegroundColor Green
Write-Host "   ./scripts/build_aab.ps1        (vyrobi bundle/playRelease/app-play-release.aab)" -ForegroundColor White
Write-Host "Pak AAB nahraj do Play Console (Produkce / testovaci track)." -ForegroundColor White
Write-Host ""
Write-Host "Pripominka: strategie-release.jks ani keystore.properties NIKDY necommituj." -ForegroundColor Yellow
