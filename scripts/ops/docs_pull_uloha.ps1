# =============================================================================
#  docs_pull_uloha.ps1 - zalozi naplanovanou ulohu STRATEGIE-DOCS-Pull
# =============================================================================
#  Zadal Jiri Honomichl, napsal Claude-28. 14. 9. 2026.
#  Spousti to CLOVEK na plzenskem serveru 192.168.30.11 (AI tam menit nesmi -
#  znalost doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji).
#
#  CO TO DELA
#  Zalozi tydenni ulohu, ktera prebira zalohu DOKUMENTU z Prahy:
#      nazev   STRATEGIE-DOCS-Pull
#      kdy     kazdou nedeli v 06:00 (mimo okno nocni zalohy databaze 3:30-5:00,
#              ktera jede po te same zasekavajici se lince)
#      ucet    SYSTEM, nejvyssi opravneni
#      spusti  powershell -NoProfile -ExecutionPolicy Bypass -File C:\scripts\docs_pull.ps1
#  Popis cele cesty: znalost doc-provoz-zaloha-dokumentu-do-plzne-balik-a-prevzeti.
#
#  BEZPECNE VLASTNOSTI
#   - kdyz uloha uz existuje, NEJDRIV si ulozi jeji zalohu do XML a pak ji prepise
#   - kdyz cokoli selze, **sam se vrati** (starou ulohu obnovi ze zalohy,
#     novou smaze) - server tedy nezustane v rozdelanem stavu
#   - nezalozi ulohu, ktera by ukazovala na neexistujici skript
#   - na konci si praci **precte zpatky** a vypise, co v systemu opravdu je
#   - nesaha na zadnou jinou ulohu (zejmena ne na STRATEGIE-DR-PullRestore)
#
#  JAK SPUSTIT
#     vzdalena plocha na 192.168.30.11 -> powershell_ise "jako spravce" -> F5
#     .\docs_pull_uloha.ps1 -JenUkaz    # nic nemeni, jen ukaze, co je teraz
#     .\docs_pull_uloha.ps1             # zalozi (nebo prepise) ulohu
#  Okno nezavira (prikaz exit v ISE zavre cele okno - znalost
#  doc-system-strategie-skript-pro-cloveka-v-ise-nesmi-koncit-prikazem-exit).
# =============================================================================

param(
  [string]$Nazev   = 'STRATEGIE-DOCS-Pull',
  [string]$Skript  = 'C:\scripts\docs_pull.ps1',
  [string]$Cas     = '06:00',
  [string]$Den     = 'Sunday',
  [string]$ZalohyDo = 'C:\scripts\_zalohy_uloh',
  [switch]$JenUkaz
)

$ErrorActionPreference = 'Stop'

function Rekni($t) { Write-Host $t }

function Zalozit {

  # --- 1) jsem spravce? ------------------------------------------------------
  $jsemSpravce = ([Security.Principal.WindowsPrincipal] `
      [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $jsemSpravce) {
    Rekni '1) POZOR: nebezim jako spravce - zalozeni ulohy pod uctem SYSTEM neprojde.'
    Rekni '   Spust prosim ISE pres pravy klik -> "Spustit jako spravce" a zkus znovu.'
    return 2
  }
  Rekni '1) Bezim jako spravce - OK.'

  # --- 2) existuje skript, na ktery ukazujeme? -------------------------------
  if (-not (Test-Path $Skript)) {
    Rekni ('2) CHYBI SKRIPT ' + $Skript + ' - ulohu nezakladam, aby neukazovala do prazdna.')
    Rekni '   Nejdriv na server uloz docs_pull.ps1 a pak spust tenhle skript znovu.'
    return 1
  }
  Rekni ('2) Skript ' + $Skript + ' na serveru je - OK.')

  # --- 3) uz uloha existuje? pak zalohu do XML -------------------------------
  $stara = $null
  try { $stara = Get-ScheduledTask -TaskName $Nazev -ErrorAction Stop } catch { $stara = $null }

  if ($stara) { Rekni '3) Uloha uz existuje - budu ji prepisovat.' }
  else        { Rekni '3) Uloha zatim neexistuje - zakladam novou.' }

  # --- 4) jen ukazat a skoncit? --------------------------------------------
  # Zamerne PRED zalohou: v tomhle rezimu se na server NEZAPISUJE vubec nic,
  # ani zalozni XML. "Nic nemeni" ma znamenat doopravdy nic.
  if ($JenUkaz) {
    if ($stara) {
      Rekni '4) Rezim JenUkaz - takhle je uloha nastavena dnes:'
      ($stara | Select-Object TaskName, State | Format-List | Out-String) | Write-Host
      ($stara.Triggers | Out-String) | Write-Host
      ($stara.Actions  | Out-String) | Write-Host
    } else {
      Rekni '4) Rezim JenUkaz - uloha neexistuje. Nic jsem nezmenil.'
    }
    return 0
  }

  # --- 4b) zaloha stavajici ulohy do XML (az kdyz budeme opravdu menit) -----
  $zalohaXml = $null
  if ($stara) {
    if (-not (Test-Path $ZalohyDo)) { New-Item -ItemType Directory -Path $ZalohyDo | Out-Null }
    $zalohaXml = Join-Path $ZalohyDo ($Nazev + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.xml')
    (Export-ScheduledTask -TaskName $Nazev) | Set-Content -Path $zalohaXml -Encoding utf8
    Rekni ('4b) Zalohu stavajici ulohy jsem ulozil do ' + $zalohaXml)
  }

  # --- 5) zalozeni / prepsani -----------------------------------------------
  try {
    # -WindowStyle Hidden: pri automatickem behu se nesmi objevit zadne okno
    # (vyslovny pozadavek Jirky Honomichla 14. 9. 2026). Pod uctem SYSTEM by
    # okno videt nebylo ani tak, ale takhle to plati i kdyz ulohu nekdo spusti rucne.
    $akce = New-ScheduledTaskAction -Execute 'powershell.exe' `
              -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' +
                         $Skript + '"')
    $spoust = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Den -At $Cas
    $ucet = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    # StartWhenAvailable: kdyz byl server v nedeli 6:00 vypnuty, uloha se dozene pozdeji.
    # ExecutionTimeLimit 3 h: stavba baliku 14 min + stahovani s 30 pokusy se tam vejde.
    # IgnoreNew: kdyby predchozi beh jeste bezel, druhy se nespusti.
    $nastaveni = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                   -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
                   -MultipleInstances IgnoreNew

    if ($stara) { Unregister-ScheduledTask -TaskName $Nazev -Confirm:$false }
    Register-ScheduledTask -TaskName $Nazev -Action $akce -Trigger $spoust `
      -Principal $ucet -Settings $nastaveni `
      -Description ('Prebira zalohu dokumentu z Prahy (docs_pull.ps1). Zalozeno ' +
                    (Get-Date -Format 'd.M.yyyy') + ' podle znalosti ' +
                    'doc-provoz-zaloha-dokumentu-do-plzne-balik-a-prevzeti.') | Out-Null
    Rekni '5) Uloha zalozena.'
  } catch {
    Rekni ('5) ZALOZENI SELHALO: ' + $_.Exception.Message)
    # vraceni do puvodniho stavu
    try {
      if (Get-ScheduledTask -TaskName $Nazev -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Nazev -Confirm:$false
      }
    } catch {}
    if ($zalohaXml -and (Test-Path $zalohaXml)) {
      try {
        Register-ScheduledTask -TaskName $Nazev -Xml (Get-Content $zalohaXml -Raw) | Out-Null
        Rekni '5) Puvodni uloha obnovena ze zalohy - server je ve stavu, v jakem byl.'
      } catch {
        Rekni ('5) POZOR: obnova ze zalohy se nepovedla. XML lezi v ' + $zalohaXml)
      }
    } else {
      Rekni '5) Nic jsem nezalozil, puvodni stav byl "uloha neexistuje" - server je jako predtim.'
    }
    return 1
  }

  # --- 6) precti si praci zpatky --------------------------------------------
  try {
    $nova = Get-ScheduledTask -TaskName $Nazev -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName $Nazev
    $spousteni = ($nova.Triggers | ForEach-Object {
        ($_.CimClass.CimClassName + ' ' + $_.StartBoundary + ' ' + $_.DaysOfWeek) }) -join ' | '
    $prikaz = ($nova.Actions | ForEach-Object { ($_.Execute + ' ' + $_.Arguments) }) -join ' | '

    Rekni ''
    Rekni '6) TAKHLE TO V SYSTEMU OPRAVDU JE (precteno zpatky, ne z mych slov):'
    Rekni ('   nazev        : ' + $nova.TaskName)
    Rekni ('   stav         : ' + $nova.State)
    Rekni ('   ucet         : ' + $nova.Principal.UserId + ', uroven ' + $nova.Principal.RunLevel)
    Rekni ('   spousteni    : ' + $spousteni)
    Rekni ('   prikaz       : ' + $prikaz)
    Rekni ('   pristi beh   : ' + $info.NextRunTime)

    $sedi = ($nova.State -ne 'Disabled') -and ($prikaz -like ('*' + $Skript + '*'))
    if (-not $sedi) {
      Rekni '6) NECO NESEDI - uloha je vypnuta, nebo neukazuje na spravny skript. Rekni to Claudovi.'
      return 1
    }
    Rekni ''
    Rekni '7) OK - hotovo. Od pristi nedele 6:00 se zaloha dokumentu prebira sama.'
    Rekni '   Zapis kazdeho behu najdes v D:\STRATEGIE_IN\_docspull.log'
    Rekni ('   Vyzkouset to hned muzes prikazem: Start-ScheduledTask -TaskName ' + $Nazev)
  } catch {
    Rekni ('6) Kontrolni precteni selhalo: ' + $_.Exception.Message)
    return 1
  }

  return 0
}

# ---------------------------------------------------------------------------
#  Prikaz exit v ISE zavre cele okno a clovek pak neuvidi vysledek
#  (znalost doc-system-strategie-skript-pro-cloveka-v-ise-nesmi-koncit-prikazem-exit).
#  @(...)[-1] je pojistka, kdyby neco uvnitr proteklo do vystupu.
# ---------------------------------------------------------------------------
$vysledek = @(Zalozit)
$kod = [int]$vysledek[-1]

if ($Host.Name -like '*ISE*') {
  Write-Host ''
  Write-Host ('=== HOTOVO. Navratovy kod: {0} (0 = vse v poradku) ===' -f $kod)
  Write-Host '=== Okno nechavam otevrene, aby slo vysledek precist. ==='
} else {
  exit $kod
}
