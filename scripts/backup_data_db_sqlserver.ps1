# Daily backup data_db na cloud SQL serveru (10.200.188.12).
# Spousti se pres Windows Task Scheduler 3:00 rano pod SYSTEM userem.
#
# Output: E:\STRATEGIE\YYYY-MM-DD\data_db_HHMMSS.dump
#         (custom format -Fc, komprese 6, restore pres pg_restore)
# Retention: 30 dni (starsi YYYY-MM-DD slozky se auto-mazaji)
#
# Auth: .pgpass v SYSTEM profilu
#   C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql\pgpass.conf
#   Format radku: localhost:5432:data_db:postgres:<heslo>
#
# Phase 38.4 Krok 7 (9.5.2026): scheduled task na SQL serveru misto na APP.
# Vyhody:
#   - Nativni pg_dump (zadny PG_DUMP_PATH workaround jako na APP serveru)
#   - Loopback connection (zadny network overhead)
#   - Independent na APP serveru (kdyby APP byl down, backup stale jede)
#
# Manualni standalone test:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\scripts\backup_data_db.ps1
#
# Setup pokyny: docs/sql_server_backup_setup.md (nebo viz Marti's CLAUDE.md
# dodatek 9.5.2026 vecer).

$ErrorActionPreference = 'Stop'

# ── Connection params (lokalni loopback) ───────────────────
$pgHost = "localhost"
$pgPort = "5432"
$pgUser = "postgres"
$pgDb = "data_db"

# ── Output dir per den ─────────────────────────────────────
$today = (Get-Date).ToString("yyyy-MM-dd")
$outDir = "E:\STRATEGIE\$today"
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$ts = (Get-Date).ToString("HHmmss")
$outFile = Join-Path $outDir "data_db_${ts}.dump"

Write-Host "[INFO] $today ${ts}: backup start -> $outFile"

# ── Najdi pg_dump.exe ──────────────────────────────────────
# Priorita: env PG_DUMP_PATH > pg_dump v PATH > Program Files PostgreSQL
$pgDump = $env:PG_DUMP_PATH
if (-not $pgDump -or -not (Test-Path $pgDump)) {
    $cmd = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($cmd) { $pgDump = $cmd.Source }
}
if (-not $pgDump) {
    $candidates = @(
        "C:\Program Files\PostgreSQL"
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
    Write-Error "pg_dump nenalezen. Cekal jsem PostgreSQL 16 v PATH nebo C:\Program Files\PostgreSQL\16\bin\."
}
Write-Host "[INFO] pg_dump: $pgDump"

# ── Spust dump ─────────────────────────────────────────────
# .pgpass musi byt v SYSTEM profilu (auth bez prompt)
# pg_dump pouzije .pgpass automaticky -- staci aby existoval na spravnem miste.

$startTs = Get-Date
& $pgDump `
    -h $pgHost `
    -p $pgPort `
    -U $pgUser `
    -d $pgDb `
    -Fc `
    -Z 6 `
    --no-owner `
    -f $outFile 2>&1 | ForEach-Object { Write-Host "  $_" }

if ($LASTEXITCODE -ne 0) {
    # Cleanup: smaz half-written file
    if (Test-Path $outFile) { Remove-Item $outFile -Force -ErrorAction SilentlyContinue }
    Write-Error "pg_dump selhal (exit=$LASTEXITCODE). Zkontroluj .pgpass + connection params."
}

$duration = ((Get-Date) - $startTs).TotalSeconds
$size = (Get-Item $outFile).Length
$sizeMb = [math]::Round($size / 1MB, 2)
Write-Host "[OK] Backup hotovy: ${sizeMb} MB za $([math]::Round($duration, 1))s"

# ── Retention 30 dni ───────────────────────────────────────
$retentionDays = 30
$cutoff = (Get-Date).AddDays(-$retentionDays)
$deletedCount = 0
$deletedSizeMb = 0.0

Get-ChildItem -Path "E:\STRATEGIE" -Directory -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^\d{4}-\d{2}-\d{2}$' -and
    [datetime]::ParseExact($_.Name, 'yyyy-MM-dd', $null) -lt $cutoff
} | ForEach-Object {
    $folderSize = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    $folderSizeMb = if ($folderSize) { [math]::Round($folderSize / 1MB, 2) } else { 0 }
    Write-Host "[CLEANUP] Mazu starou zalohu: $($_.FullName) (${folderSizeMb} MB)"
    Remove-Item -Path $_.FullName -Recurse -Force
    $deletedCount++
    $deletedSizeMb += $folderSizeMb
}

if ($deletedCount -gt 0) {
    Write-Host "[CLEANUP] Smazano $deletedCount starych slozek = ${deletedSizeMb} MB (retention $retentionDays dni)"
}

Write-Host "[DONE] $today ${ts}"
