# Záloha PostgreSQL data_db přes pg_dump.
# Výstup: $BACKUPS_DIR\YYYY-MM-DD\data_db_HHMMSS.dump
# Formát: custom (-Fc), komprese 6 -- restore přes `pg_restore`.
#
# Phase 18 (30.4.2026): sjednoceno do jedné DB (data_db). css_db deprecated.
# Phase 25/38.4 (10.5.2026): default BACKUPS_DIR=C:\Backup na cloud APP.
#
# Použití:
#   .\scripts\backup_dbs.ps1
#   .\scripts\backup_dbs.ps1 -BackupsDir D:\custom\path     # override
#
# Pre-req:
#   - PostgreSQL klient (pg_dump.exe) v PATH nebo přes env var PG_DUMP_PATH
#   - .env soubor s DATABASE_DATA_URL
#
# Alternativa: backup přes UI tlačítko v profile dropdown (Marti volá
# POST /api/v1/admin/backup-databases).

param(
    [string]$BackupsDir = $null
)

$ErrorActionPreference = 'Stop'

# --- Najdi repo root (tam kde je pyproject.toml) ---
$repoRoot = $PSScriptRoot
if (-not (Test-Path (Join-Path $repoRoot "..\pyproject.toml"))) {
    Write-Error "scripts\backup_dbs.ps1 musi byt v <repo>\scripts\ a mit <repo>\pyproject.toml"
}
$repoRoot = Resolve-Path (Join-Path $repoRoot "..")

# --- Nacti .env (jen pro DB URL) ---
$envFile = Join-Path $repoRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Error ".env soubor neexistuje na $envFile"
}
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*$') { return }
    if ($_ -match '^\s*([^=]+?)\s*=\s*(.*)$') {
        $k = $matches[1]
        $v = $matches[2].Trim('"').Trim("'")
        $envVars[$k] = $v
    }
}

$dataUrl = $envVars['DATABASE_DATA_URL']
if (-not $dataUrl) {
    Write-Error "V .env chybi DATABASE_DATA_URL"
}

# --- Najdi pg_dump ---
$pgDump = $env:PG_DUMP_PATH
if (-not $pgDump -or -not (Test-Path $pgDump)) {
    $pgDump = (Get-Command pg_dump -ErrorAction SilentlyContinue).Source
}
if (-not $pgDump) {
    # Windows fallback -- nejvyssi verze v Program Files
    $candidates = @(
        "C:\Program Files\PostgreSQL",
        "C:\Program Files (x86)\PostgreSQL"
    ) | Where-Object { Test-Path $_ }
    foreach ($base in $candidates) {
        $versions = Get-ChildItem $base -Directory |
            Where-Object { $_.Name -match '^\d+$' } |
            Sort-Object { [int]$_.Name } -Descending
        foreach ($v in $versions) {
            $candidate = Join-Path $v.FullName "bin\pg_dump.exe"
            if (Test-Path $candidate) { $pgDump = $candidate; break }
        }
        if ($pgDump) { break }
    }
}
if (-not $pgDump) {
    Write-Error "pg_dump nenalezen. Nainstaluj PostgreSQL klienta nebo nastav env var PG_DUMP_PATH."
}
Write-Host "[INFO] pg_dump: $pgDump"

# --- Parse URL -> host/port/user/pass/db ---
function Parse-PgUrl($url) {
    # postgresql://user:pass@host:port/db
    if ($url -notmatch '^postgres(?:ql)?://([^:]+):([^@]*)@([^:/]+):?(\d+)?/(.+)$') {
        throw "Neumim parsovat URL: $url"
    }
    return [PSCustomObject]@{
        User = $matches[1]
        Pass = $matches[2]
        Host = $matches[3]
        Port = if ($matches[4]) { $matches[4] } else { "5432" }
        Db   = $matches[5]
    }
}

$dataParsed = Parse-PgUrl $dataUrl

# --- Priprav out dir ---
# Priorita: -BackupsDir param > env BACKUPS_DIR > C:\Backup (Windows) > <repo>\backups
if (-not $BackupsDir) {
    $BackupsDir = $env:BACKUPS_DIR
}
if (-not $BackupsDir) {
    if ($IsWindows -or $env:OS -match 'Windows') {
        $BackupsDir = "C:\Backup"
    } else {
        $BackupsDir = Join-Path $repoRoot "backups"
    }
}

$today = (Get-Date).ToString("yyyy-MM-dd")
$outDir = Join-Path $BackupsDir $today
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
Write-Host "[INFO] Backup dir: $outDir"

function Dump-Db($label, $parsed) {
    $ts = (Get-Date).ToString("HHmmss")
    $outFile = Join-Path $outDir "${label}_${ts}.dump"
    Write-Host "[INFO] Dumping $label ($($parsed.Host)/$($parsed.Db)) -> $outFile"

    $env:PGPASSWORD = $parsed.Pass
    try {
        & $pgDump `
            -h $parsed.Host `
            -p $parsed.Port `
            -U $parsed.User `
            -d $parsed.Db `
            -Fc `
            -Z 6 `
            --no-owner `
            -f $outFile 2>&1 | ForEach-Object { Write-Host "  $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Error "pg_dump ${label} selhal (exit=$LASTEXITCODE)"
        }
        $size = (Get-Item $outFile).Length
        $sizeMb = [math]::Round($size / 1MB, 2)
        Write-Host "[OK]  $label done -- ${sizeMb} MB" -ForegroundColor Green
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# Phase 18 (30.4.2026): jen data_db. css_db deprecated/dropped.
Dump-Db "data_db" $dataParsed

Write-Host ""
Write-Host "[DONE] Backup kompletni -- $outDir" -ForegroundColor Green
Write-Host ""
Write-Host "Nezapomen: backups/ NEPATRI do gitu (PII + emaily + thoughts)."
Write-Host "Kopiruj dumps rucne na OneDrive / externi disk kvuli disaster recovery."
