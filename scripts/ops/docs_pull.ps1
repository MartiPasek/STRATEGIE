# =============================================================================
#  docs_pull.ps1 - prevzeti zalohy DOKUMENTU z Prahy do Plzne
# =============================================================================
#  Zadal Jiri Honomichl, napsal Claude-28, schvalila Marti-AI (msg 15492).
#  14. 9. 2026.
#
#  PROC: slozka C:\Data\STRATEGIE\Dokumenty (prilohy z firemni posty) NENI
#  v zadne zaloze - nocni DR retez Praha -> Plzen veze jen databazi.
#  Zjisteno 8. 9. 2026, znalost doc-provoz-zalohuje-se-jen-databaze-dokumenty-a-instalace-ne.
#  Merenim 13. 9. 2026: 51 569 souboru a 19 759 MB na disku, ale jen 994 MB
#  RUZNEHO obsahu (jeden mail na sto lidi se ulozi stokrat). Zalohuje se proto
#  jen unikatni obsah v jednom baliku zip - to je tech ~1 GB, ne 19 GB.
#
#  KDE VZNIKA BALIK: v Praze na 188.11 ho stavi g2007.python kod=dokumenty_zaloha_balik.
#  Push do Prahy neni potreba - balik lezi na temze stroji, kde bezi API.
#
#  TENTO SKRIPT NESAHA NA DATABAZI ANI NA NOCNI OBNOVU. Je uplne samostatny
#  vedle dr_pull_restore.ps1 a pouziva jine adresy (/api/v1/ops/docs/...).
#
#  BEZPECNE VLASTNOSTI
#   - stahuje s navazovanim (hlavicka Range), 30 pokusu, kratke limity -
#     protoze linka Praha-Plzen se po nekolika stech MB zasekava
#     (znalost doc-system-strategie-dr-stahovani-se-zasekava-ne-zpomaluje)
#   - po stazeni overi otisk SHA-256 proti tomu, co hlasi Praha; kdyz nesedi,
#     NIC neroztali a skonci chybou
#   - stavajici zaloha se prepise az ve chvili, kdy je nova cela a overena
#     (nejdriv rozbali do _nove, pak prehodi); pri jakekoli chybe zustava stara
#   - kdyz uz mame tentyz otisk, NESTAHUJE VUBEC NIC (neplytva linkou)
#   - po uspesnem rozbaleni balik zip smaze (neplytva mistem v Plzni)
#
#  JAK SPUSTIT RUCNE (vzdalena plocha na 192.168.30.11, powershell_ise, F5):
#     .\docs_pull.ps1 -JenOvereni     # nic nestahne, jen rekne, co je v Praze
#     .\docs_pull.ps1                 # prevezme zalohu
#
#  NAPLANOVANA ULOHA (doporuceno 1x tydne, nedele 6:00 - mimo okno nocni
#  zalohy databaze, ktera bezi 3:30-5:00 na te same zasekavajici se lince):
#     schtasks /Create /TN "STRATEGIE-DOCS-Pull" /SC WEEKLY /D SUN /ST 06:00 ^
#       /RU SYSTEM /RL HIGHEST ^
#       /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\scripts\docs_pull.ps1"
# =============================================================================

param(
  [string]$Base     = 'https://strategie-ai.com',
  [string]$Token    = $env:DR_TRANSFER_TOKEN,
  [string]$Incoming = 'D:\STRATEGIE_IN',
  [string]$Cil      = 'D:\STRATEGIE_DOKUMENTY',
  [int]$Pokusu      = 30,
  [int]$PauzaS      = 20,
  [switch]$JenOvereni
)

$ErrorActionPreference = 'Stop'
$Log = Join-Path $Incoming '_docspull.log'

function Log($t) {
  $r = ('{0} {1}' -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'), $t)
  Write-Host $r
  try { Add-Content -Path $Log -Value $r -Encoding utf8 } catch {}
}

if (-not (Test-Path $Incoming)) { New-Item -ItemType Directory -Path $Incoming | Out-Null }
Log '--- docs_pull start ---'

if (-not $Token) { Log '1) CHYBI token (DR_TRANSFER_TOKEN) - koncim'; exit 2 }
$hdr = @{ 'X-DR-Token' = $Token }

# --- 1) co je v Praze pripraveno ---------------------------------------------
try {
  $m = Invoke-RestMethod "$Base/api/v1/ops/docs/meta" -Headers $hdr -TimeoutSec 60
} catch {
  Log ('1) META fail: ' + $_.Exception.Message); exit 1
}
if (-not $m.stored) { Log '1) V Praze zadny balik neni (jeste nevznikl) - koncim bez chyby'; exit 0 }

$velikost = [int64]$m.size
$otisk    = ('' + $m.sha256).ToLower()
$stariH   = [math]::Round(([int]$m.age_s) / 3600.0, 1)
Log ('1) Praha hlasi: {0} MB, otisk {1}..., stari {2} h, souboru v puvodni slozce {3}, ruznych obsahu {4}' -f `
      [math]::Round($velikost / 1MB, 1), $otisk.Substring(0, [math]::Min(12, $otisk.Length)), $stariH, `
      $m.souboru_prectenych, $m.ruznych_obsahu)

if ($JenOvereni) { Log '2) Rezim JenOvereni - nic nestahuji, koncim'; exit 0 }
if (-not $otisk) { Log '2) Praha neposlala otisk - bez nej nestahuji (nemel bych co overit)'; exit 1 }

# --- 2) uz to mame? ----------------------------------------------------------
$stavFile = Join-Path $Cil '_stav.json'
if (Test-Path $stavFile) {
  try {
    $s = Get-Content $stavFile -Raw | ConvertFrom-Json
    if (('' + $s.sha256).ToLower() -eq $otisk) {
      Log ('2) Tentyz otisk uz tady mame (prevzato ' + $s.prevzato + ') - NESTAHUJI nic, koncim')
      exit 0
    }
  } catch {}
}

# --- 3) stazeni s navazovanim ------------------------------------------------
$zip  = Join-Path $Incoming 'dokumenty_dedup.zip'
$part = $zip + '.part'
if (Test-Path $zip) { Remove-Item $zip -Force }
# nedodelek z minuleho behu zahazujeme - navazuje se jen v ramci jednoho behu
if (Test-Path $part) { Remove-Item $part -Force }

$hotovo = $false
for ($i = 1; $i -le $Pokusu; $i++) {
  $mam = 0
  if (Test-Path $part) { $mam = (Get-Item $part).Length }
  if ($mam -ge $velikost) { $hotovo = $true; break }
  try {
    $rq = [Net.HttpWebRequest]::Create("$Base/api/v1/ops/docs/download")
    $rq.Method = 'GET'
    $rq.Headers.Add('X-DR-Token', $Token)
    $rq.Timeout = 120000            # navazani spojeni
    $rq.ReadWriteTimeout = 120000   # KLICOVE: mrtve spojeni se pozna za 2 min, ne za hodinu
    if ($mam -gt 0) { $rq.AddRange([int64]$mam) }

    $rs = $rq.GetResponse()
    $kod = [int]$rs.StatusCode
    if ($mam -gt 0 -and $kod -ne 206) {
      # server poslal cely soubor misto zbytku - pripojenim by vznikl zmetek
      $rs.Close(); Remove-Item $part -Force -ErrorAction SilentlyContinue
      Log ('3) Pokus {0}: navazani nefunguje (kod {1}) - zacinam od zacatku' -f $i, $kod)
      continue
    }
    if ($mam -gt 0) { Log ('3) Pokus {0}: navazuji od {1} MB' -f $i, [math]::Round($mam / 1MB, 1)) }

    $vstup = $rs.GetResponseStream()
    $vystup = New-Object IO.FileStream($part, [IO.FileMode]::Append, [IO.FileAccess]::Write)
    try {
      $buf = New-Object byte[] 1048576
      while (($n = $vstup.Read($buf, 0, $buf.Length)) -gt 0) { $vystup.Write($buf, 0, $n) }
    } finally {
      $vystup.Close(); $vstup.Close(); $rs.Close()
    }

    $mam = (Get-Item $part).Length
    if ($mam -ge $velikost) { $hotovo = $true; Log ('3) Stazeno cele ({0} MB) na {1}. pokus z {2}' -f [math]::Round($mam / 1MB, 1), $i, $Pokusu); break }
    Log ('3) Pokus {0}: mam {1} z {2} MB, zkousim dal' -f $i, [math]::Round($mam / 1MB, 1), [math]::Round($velikost / 1MB, 1))
  } catch {
    Log ('3) Pokus {0} fail: {1}' -f $i, $_.Exception.Message)
  }
  Start-Sleep -Seconds $PauzaS
}

if (-not $hotovo) { Log '3) NEDOSTAHOVANO ani po vsech pokusech - stara zaloha zustava nedotcena'; exit 1 }

$mam = (Get-Item $part).Length
if ($mam -ne $velikost) {
  Log ('4) Velikost nesedi ({0} != {1}) - mazu a koncim' -f $mam, $velikost)
  Remove-Item $part -Force; exit 1
}

# --- 4) kontrola otisku ------------------------------------------------------
$spocteny = (Get-FileHash $part -Algorithm SHA256).Hash.ToLower()
if ($spocteny -ne $otisk) {
  Log ('4) OTISK NESEDI - stazene zahazuji, NIC neroztaluji. spocteno {0}..., ceka se {1}...' -f `
        $spocteny.Substring(0, 12), $otisk.Substring(0, 12))
  Remove-Item $part -Force; exit 1
}
Move-Item $part $zip -Force
Log '4) Otisk sedi - balik je cely a neporuseny'

# --- 5) rozbaleni do _nove a az potom prehozeni ------------------------------
if (-not (Test-Path $Cil)) { New-Item -ItemType Directory -Path $Cil | Out-Null }
$nove       = Join-Path $Cil '_nove'
$aktualni   = Join-Path $Cil 'aktualni'
$predchozi  = Join-Path $Cil '_predchozi'
foreach ($d in @($nove, $predchozi)) { if (Test-Path $d) { Remove-Item $d -Recurse -Force } }
New-Item -ItemType Directory -Path $nove | Out-Null

try {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::ExtractToDirectory($zip, $nove)
} catch {
  Log ('5) Rozbaleni selhalo: ' + $_.Exception.Message)
  Remove-Item $nove -Recurse -Force -ErrorAction SilentlyContinue
  Log '5) Stara zaloha zustava nedotcena'
  exit 1
}
$pocet = (Get-ChildItem $nove -File -Recurse | Measure-Object).Count
Log ('5) Rozbaleno {0} souboru' -f $pocet)

if (Test-Path $aktualni) { Move-Item $aktualni $predchozi -Force }
Move-Item $nove $aktualni -Force
if (Test-Path $predchozi) { Remove-Item $predchozi -Recurse -Force -ErrorAction SilentlyContinue }
Log '6) Prehozeno - aktualni zaloha dokumentu je nova'

# --- 6) uklid a zaznam o stavu ----------------------------------------------
Remove-Item $zip -Force -ErrorAction SilentlyContinue
@{
  sha256   = $otisk
  velikost = $velikost
  souboru  = $pocet
  prevzato = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
  z_prahy_stare_h = $stariH
} | ConvertTo-Json | Set-Content -Path $stavFile -Encoding utf8

$volno = [math]::Round((Get-PSDrive ($Cil.Substring(0, 1))).Free / 1GB, 1)
Log ('7) OK - hotovo. Balik zip smazan, volno na disku {0} GB' -f $volno)
Log '--- docs_pull konec ---'
exit 0
