# =============================================================================
#  _spolecne.ps1 - sdilene funkce pro instalacni skripty sluzeb STRATEGIE
#
#  Zadal Jiri Honomichl 8. 9. 2026 pote, co se ukazalo, ze PET sluzeb na
#  aplikacnim serveru nema zadny instalacni postup a pri stavbe serveru znovu
#  by se musely poskladat rucne z hlavy.
#
#  Skripty NEJSOU jednorazove - jsou psane jako OPAKOVATELNE. Kdyz sluzba uz
#  existuje, jen srovnaji nastaveni; kdyz neexistuje, zalozi ji.
#
#  ⛔ TAJEMSTVI (tokeny, hesla, klice) NEJSOU v zadnem z techto skriptu a nikdy
#     tam nesmi byt. Predavaji se jako parametr -Promenne. Duvod - skripty jsou
#     v gitu, ktery vidi cela sit. Stejny princip jako setup_claude_instance.ps1.
#
#  Nacteni ze sesterskeho skriptu:  . "$PSScriptRoot\_spolecne.ps1"
# =============================================================================

$ErrorActionPreference = 'Stop'

function Test-Spravce {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Najdi-Nssm {
    # Poradi hledani: parametr -> PATH -> zname umisteni na 188.11 (overeno 8.9.2026)
    param([string]$Cesta)
    if ($Cesta -and (Test-Path $Cesta)) { return $Cesta }
    $vPath = (Get-Command nssm.exe -ErrorAction SilentlyContinue).Source
    if ($vPath) { return $vPath }
    foreach ($k in @('C:\Tools\nssm.exe', 'C:\nssm\nssm.exe', 'C:\Program Files\nssm\nssm.exe')) {
        if (Test-Path $k) { return $k }
    }
    throw "nssm.exe nenalezen. Predej cestu parametrem -Nssm, nebo ho doinstaluj."
}

function Nastav-Sluzbu {
    <#
      Zalozi sluzbu (kdyz neni) a srovna jeji nastaveni. Opakovatelne.
      Tajemstvi se predavaji v $Promenne jako hashtable NAZEV = HODNOTA.
    #>
    param(
        [Parameter(Mandatory)][string]$Nssm,
        [Parameter(Mandatory)][string]$Jmeno,
        [Parameter(Mandatory)][string]$Program,
        [string]$Parametry   = '',
        [Parameter(Mandatory)][string]$PracovniSlozka,
        [string]$Popis       = '',
        [string]$NazevKZobrazeni = '',
        [string]$Ucet        = 'LocalSystem',
        [string]$LogStdout   = '',
        [string]$LogStderr   = '',
        [int]$PauzaPredRestartemMs = 5000,
        [hashtable]$Promenne = @{},
        [switch]$Nespoustet
    )

    if (-not (Test-Path $PracovniSlozka)) {
        throw "Pracovni slozka neexistuje: $PracovniSlozka"
    }

    $existuje = $null -ne (Get-Service -Name $Jmeno -ErrorAction SilentlyContinue)
    if (-not $existuje) {
        Write-Host "  zakladam sluzbu $Jmeno" -ForegroundColor Cyan
        & $Nssm install $Jmeno $Program $Parametry | Out-Null
    } else {
        Write-Host "  sluzba $Jmeno uz existuje - jen srovnavam nastaveni" -ForegroundColor Yellow
        & $Nssm set $Jmeno Application $Program        | Out-Null
        & $Nssm set $Jmeno AppParameters $Parametry    | Out-Null
    }

    & $Nssm set $Jmeno AppDirectory     $PracovniSlozka | Out-Null
    & $Nssm set $Jmeno Start            SERVICE_AUTO_START | Out-Null
    & $Nssm set $Jmeno AppExit Default  Restart        | Out-Null
    & $Nssm set $Jmeno AppRestartDelay  $PauzaPredRestartemMs | Out-Null
    if ($NazevKZobrazeni) { & $Nssm set $Jmeno DisplayName $NazevKZobrazeni | Out-Null }
    if ($Popis)           { & $Nssm set $Jmeno Description $Popis | Out-Null }

    if ($LogStdout) {
        $slozka = Split-Path $LogStdout -Parent
        if (-not (Test-Path $slozka)) { New-Item -ItemType Directory -Force $slozka | Out-Null }
        & $Nssm set $Jmeno AppStdout $LogStdout | Out-Null
        $stderrCesta = $LogStdout
        if ($LogStderr) { $stderrCesta = $LogStderr }
        & $Nssm set $Jmeno AppStderr $stderrCesta | Out-Null
        & $Nssm set $Jmeno AppRotateFiles  1        | Out-Null
        & $Nssm set $Jmeno AppRotateOnline 1        | Out-Null
        & $Nssm set $Jmeno AppRotateBytes  10485760 | Out-Null
    }

    if ($Ucet -and $Ucet -ne 'LocalSystem') {
        Write-Host "  ucet $Ucet - heslo si NSSM vyzada, do skriptu nepatri" -ForegroundColor Yellow
        & $Nssm set $Jmeno ObjectName $Ucet | Out-Null
    } else {
        & $Nssm set $Jmeno ObjectName LocalSystem | Out-Null
    }

    if ($Promenne.Count -gt 0) {
        $radky = $Promenne.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }
        & $Nssm set $Jmeno AppEnvironmentExtra ($radky -join "`r`n") | Out-Null
        Write-Host ("  nastaveno {0} promennych prostredi: {1}" -f $Promenne.Count,
                    (($Promenne.Keys | Sort-Object) -join ', ')) -ForegroundColor Cyan
        Write-Host "  (hodnoty se zamerne nevypisuji)" -ForegroundColor DarkGray
    }

    if (-not $Nespoustet) {
        & $Nssm start $Jmeno 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }

    $stav = (Get-Service -Name $Jmeno -ErrorAction SilentlyContinue).Status
    Write-Host ("  {0} -> {1}" -f $Jmeno, $stav) -ForegroundColor Green
    return $stav
}
