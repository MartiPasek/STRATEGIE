# =============================================================================
#  docs_pull.ps1 - prevzeti zalohy DOKUMENTU z Prahy do Plzne
# =============================================================================
#  Zadal Jiri Honomichl, napsal Claude-28, schvalila Marti-AI (msg 15492, 15534).
#  14. 9. 2026.
#
#  PROC: slozka C:\Data\STRATEGIE\Dokumenty (prilohy z firemni posty) NENI
#  v zadne zaloze - nocni DR retez Praha -> Plzen veze jen databazi.
#  Zjisteno 8. 9. 2026, znalost doc-provoz-zalohuje-se-jen-databaze-dokumenty-a-instalace-ne.
#  Merenim 13. 9. 2026: 51 569 souboru a 19 759 MB na disku, ale jen 999 MB
#  RUZNEHO obsahu (jeden mail na sto lidi se ulozi stokrat). Zalohuje se proto
#  jen unikatni obsah v jednom baliku zip - to je tech ~1 GB, ne 19 GB.
#
#  CELY BEH RIDI TENHLE SKRIPT (a tedy jedina naplanovana uloha v Plzni):
#    1. zepta se Prahy, co ma pripravene            GET  /api/v1/ops/docs/meta
#    2. kdyz tam balik neni, vyvola jeho stavbu     POST /api/v1/ops/docs/build
#       a ceka (stavba trva 13-14 minut)
#    3. stahne s navazovanim                        GET  /api/v1/ops/docs/download
#    4. overi otisk, rozbali, prehodi
#    5. ohlasi Praze hotovo, at balik smaze         POST /api/v1/ops/docs/done
#  V Praze tak balik lezi jen tech ~20 minut, co se prenasi - ne cely tyden.
#  V Praze NENI nic naplanovaneho; zadnou automatiku tam nehledej.
#
#  TENTO SKRIPT NESAHA NA DATABAZI ANI NA NOCNI OBNOVU. Je uplne samostatny
#  vedle dr_pull_restore.ps1 a pouziva jine adresy (/api/v1/ops/docs/...).
#
#  BEZPECNE VLASTNOSTI
#   - stahuje s navazovanim (hlavicka Range), 30 pokusu, kratke limity -
#     protoze linka Praha-Plzen se po nekolika stech MB zasekava
#     (znalost doc-system-strategie-dr-stahovani-se-zasekava-ne-zpomaluje).
#     Pri prvnim ostrem behu 14. 9. 2026 to zabralo hned: 4 pokusy z 30.
#   - po stazeni overi otisk SHA-256 proti tomu, co hlasi Praha; kdyz nesedi,
#     NIC neroztali a skonci chybou
#   - stavajici zaloha se prepise az ve chvili, kdy je nova cela a overena
#     (nejdriv rozbali do _nove, pak prehodi); pri jakekoli chybe zustava stara
#   - kdyz uz mame tentyz otisk, NESTAHUJE nic a jen rekne Praze, at balik smaze
#   - po uspesnem rozbaleni balik zip smaze (neplytva mistem v Plzni)
#   - kdyz stavba v Praze spadne, dozvi se DUVOD a skonci hned - neceka na limit
#
#  JAK SPUSTIT RUCNE (vzdalena plocha na 192.168.30.11, powershell_ise, F5):
#     .\docs_pull.ps1 -JenOvereni   # nic nestahne ani nestavi, jen se zepta Prahy
#     .\docs_pull.ps1               # cely beh vcetne vyvolani stavby
#     .\docs_pull.ps1 -Nestavej     # prevezme jen to, co uz v Praze lezi
#  V ISE okno nezavira (viz poznamka na konci skriptu).
#
#  NAPLANOVANA ULOHA - JEDINA, kterou je potreba zalozit (1x tydne, nedele 6:00,
#  tedy mimo okno nocni zalohy databaze 3:30-5:00 na te same lince):
#     nazev  STRATEGIE-DOCS-Pull
#     ucet   SYSTEM, nejvyssi opravneni
#     spusti powershell -NoProfile -ExecutionPolicy Bypass -File C:\scripts\docs_pull.ps1
# =============================================================================

param(
  [string]$Base     = 'https://strategie-ai.com',
  [string]$Token    = $env:DR_TRANSFER_TOKEN,
  [string]$Incoming = 'D:\STRATEGIE_IN',
  [string]$Cil      = 'D:\STRATEGIE_DOKUMENTY',
  [int]$Pokusu      = 30,
  [int]$PauzaS      = 20,
  [int]$CekaniMin   = 45,
  [switch]$JenOvereni,
  [switch]$Nestavej
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

function Prevzeti {

if (-not $Token) { Log '1) CHYBI token (DR_TRANSFER_TOKEN) - koncim'; return 2 }
$hdr = @{ 'X-DR-Token' = $Token }

function Zeptej-SePrahy {
  return Invoke-RestMethod "$Base/api/v1/ops/docs/meta" -Headers $hdr -TimeoutSec 60
}

function Ohlas-Hotovo($otisk) {
  try {
    $o = Invoke-RestMethod "$Base/api/v1/ops/docs/done" -Method Post -Headers $hdr `
           -ContentType 'application/json' -TimeoutSec 120 `
           -Body (@{ sha256 = $otisk } | ConvertTo-Json -Compress)
    if ($o.ok) { Log ('8) Ohlaseno Praze - balik tam smazan, uvolneno {0} MB' -f $o.uvolneno_mb) }
    else       { Log ('8) Praha balik nesmazala: ' + $o.error + ' ' + $o.info) }
  } catch {
    # Neni to duvod k chybe celeho behu - zaloha uz je v Plzni v poradku.
    Log ('8) Ohlaseni Praze se nepovedlo (zaloha je ale prevzata): ' + $_.Exception.Message)
  }
}

# --- 1) co je v Praze pripraveno ---------------------------------------------
try { $m = Zeptej-SePrahy } catch { Log ('1) META fail: ' + $_.Exception.Message); return 1 }

$stavFile = Join-Path $Cil '_stav.json'
$mujOtisk = ''
if (Test-Path $stavFile) {
  try { $mujOtisk = ('' + (Get-Content $stavFile -Raw | ConvertFrom-Json).sha256).ToLower() } catch {}
}

if ($m.stavba) { Log ('1) Stav stavby v Praze: ' + $m.stavba.stav + ' ' + $m.stavba.zprava) }

if ($m.stored) {
  Log ('1) Praha ma balik: {0} MB, otisk {1}..., stari {2} h, souboru {3}, ruznych obsahu {4}' -f `
        [math]::Round(([int64]$m.size) / 1MB, 1), ('' + $m.sha256).Substring(0, 12), `
        [math]::Round(([int]$m.age_s) / 3600.0, 1), $m.souboru_prectenych, $m.ruznych_obsahu)
} else {
  Log '1) Praha zadny balik pripraveny nema'
}

if ($JenOvereni) { Log '2) Rezim JenOvereni - nic nestahuji ani nestavim, koncim'; return 0 }

# --- 2) uz to mame? ----------------------------------------------------------
if ($m.stored -and $mujOtisk -and ('' + $m.sha256).ToLower() -eq $mujOtisk) {
  Log '2) Tentyz balik uz tady mame - NESTAHUJI nic, jen rikam Praze, at ho smaze'
  Ohlas-Hotovo $mujOtisk
  return 0
}

# --- 3) kdyz v Praze nic neni, vyvolej stavbu a pockej -----------------------
if (-not $m.stored) {
  if ($Nestavej) { Log '3) Prepinac Nestavej - stavbu nevyvolavam, koncim bez chyby'; return 0 }
  try {
    $b = Invoke-RestMethod "$Base/api/v1/ops/docs/build" -Method Post -Headers $hdr -TimeoutSec 120
    if ($b.spusteno) { Log '3) Stavba baliku v Praze spustena (trva 13-14 minut)' }
    else             { Log ('3) Stavba uz bezela (' + $b.bezi_s + ' s) - cekam na ni') }
  } catch {
    Log ('3) Stavbu nelze spustit: ' + $_.Exception.Message); return 1
  }

  $doKdy = (Get-Date).AddMinutes($CekaniMin)
  while ((Get-Date) -lt $doKdy) {
    Start-Sleep -Seconds 60
    try { $m = Zeptej-SePrahy } catch { Log ('3) Dotaz na stav selhal: ' + $_.Exception.Message); continue }
    $s = $m.stavba
    if ($s -and $s.stav -eq 'chyba') {
      Log ('3) STAVBA V PRAZE SPADLA: ' + $s.zprava + ' - koncim, stara zaloha zustava')
      return 1
    }
    if ($s -and $s.zaseklo_se) {
      Log '3) Stavba v Praze bezi nesmyslne dlouho (nad 45 min) - koncim, at neblokuji ulohu'
      return 1
    }
    if ($m.stored) { Log ('3) Balik je hotovy: {0} MB' -f [math]::Round(([int64]$m.size) / 1MB, 1)); break }
    if ($s) { Log ('3) ... stavba bezi ' + [math]::Round(([int]$s.bezi_s) / 60.0, 1) + ' min') }
  }
  if (-not $m.stored) { Log ('3) Balik do limitu ' + $CekaniMin + ' min nevznikl - koncim'); return 1 }
}

$velikost = [int64]$m.size
$otisk    = ('' + $m.sha256).ToLower()
if (-not $otisk) { Log '4) Praha neposlala otisk - bez nej nestahuji (nemel bych co overit)'; return 1 }

# --- 4) stazeni s navazovanim ------------------------------------------------
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
    $kodOdpovedi = [int]$rs.StatusCode
    if ($mam -gt 0 -and $kodOdpovedi -ne 206) {
      # server poslal cely soubor misto zbytku - pripojenim by vznikl zmetek
      $rs.Close(); Remove-Item $part -Force -ErrorAction SilentlyContinue
      Log ('4) Pokus {0}: navazani nefunguje (kod {1}) - zacinam od zacatku' -f $i, $kodOdpovedi)
      continue
    }
    if ($mam -gt 0) { Log ('4) Pokus {0}: navazuji od {1} MB' -f $i, [math]::Round($mam / 1MB, 1)) }

    $vstup = $rs.GetResponseStream()
    $vystup = New-Object IO.FileStream($part, [IO.FileMode]::Append, [IO.FileAccess]::Write)
    try {
      $buf = New-Object byte[] 1048576
      while (($n = $vstup.Read($buf, 0, $buf.Length)) -gt 0) { $vystup.Write($buf, 0, $n) }
    } finally {
      $vystup.Close(); $vstup.Close(); $rs.Close()
    }

    $mam = (Get-Item $part).Length
    if ($mam -ge $velikost) { $hotovo = $true; Log ('4) Stazeno cele ({0} MB) na {1}. pokus z {2}' -f [math]::Round($mam / 1MB, 1), $i, $Pokusu); break }
    Log ('4) Pokus {0}: mam {1} z {2} MB, zkousim dal' -f $i, [math]::Round($mam / 1MB, 1), [math]::Round($velikost / 1MB, 1))
  } catch {
    Log ('4) Pokus {0} fail: {1}' -f $i, $_.Exception.Message)
  }
  Start-Sleep -Seconds $PauzaS
}

if (-not $hotovo) { Log '4) NEDOSTAHOVANO ani po vsech pokusech - stara zaloha zustava nedotcena'; return 1 }

$mam = (Get-Item $part).Length
if ($mam -ne $velikost) {
  Log ('5) Velikost nesedi ({0} != {1}) - mazu a koncim' -f $mam, $velikost)
  Remove-Item $part -Force; return 1
}

# --- 5) kontrola otisku ------------------------------------------------------
$spocteny = (Get-FileHash $part -Algorithm SHA256).Hash.ToLower()
if ($spocteny -ne $otisk) {
  Log ('5) OTISK NESEDI - stazene zahazuji, NIC neroztaluji. spocteno {0}..., ceka se {1}...' -f `
        $spocteny.Substring(0, 12), $otisk.Substring(0, 12))
  Remove-Item $part -Force; return 1
}
Move-Item $part $zip -Force
Log '5) Otisk sedi - balik je cely a neporuseny'

# --- 6) rozbaleni do _nove a az potom prehozeni ------------------------------
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
  Log ('6) Rozbaleni selhalo: ' + $_.Exception.Message)
  Remove-Item $nove -Recurse -Force -ErrorAction SilentlyContinue
  Log '6) Stara zaloha zustava nedotcena'
  return 1
}
$pocet = (Get-ChildItem $nove -File -Recurse | Measure-Object).Count
Log ('6) Rozbaleno {0} souboru' -f $pocet)

if (Test-Path $aktualni) { Move-Item $aktualni $predchozi -Force }
Move-Item $nove $aktualni -Force
if (Test-Path $predchozi) { Remove-Item $predchozi -Recurse -Force -ErrorAction SilentlyContinue }
Log '7) Prehozeno - aktualni zaloha dokumentu je nova'

# --- 7) uklid, zaznam o stavu a ohlaseni do Prahy ---------------------------
Remove-Item $zip -Force -ErrorAction SilentlyContinue
@{
  sha256   = $otisk
  velikost = $velikost
  souboru  = $pocet
  prevzato = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
} | ConvertTo-Json | Set-Content -Path $stavFile -Encoding utf8

Ohlas-Hotovo $otisk

$volno = [math]::Round((Get-PSDrive ($Cil.Substring(0, 1))).Free / 1GB, 1)
Log ('9) OK - hotovo. Balik zip smazan v Plzni i v Praze, volno na disku {0} GB' -f $volno)
Log '--- docs_pull konec ---'
  return 0
}

# ---------------------------------------------------------------------------
#  Proc se neukoncuje prikazem exit: v PowerShell ISE exit zavre CELE OKNO
#  a clovek pak neuvidi vysledek (narazil na to Jirka Honomichl 14. 9. 2026
#  pri prvnim ostrem spusteni v Plzni). Naplanovana uloha ale navratovy kod
#  potrebuje, takze se exit pousti jen mimo ISE.
# ---------------------------------------------------------------------------
# @(...)[-1] je pojistka: kdyby nekdy neco uvnitr proteklo do vystupu,
# navratovym kodem je vzdy posledni hodnota, tedy to nase return.
$vysledek = @(Prevzeti)
$kod = [int]$vysledek[-1]

if ($Host.Name -like '*ISE*') {
  Write-Host ''
  Write-Host ('=== HOTOVO. Navratovy kod: {0} (0 = vse v poradku) ===' -f $kod)
  Write-Host ('=== Cely zapis prubehu: {0} ===' -f $Log)
  Write-Host '=== Okno nechavam otevrene, aby slo vysledek precist. ==='
} else {
  exit $kod
}
