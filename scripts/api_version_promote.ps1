#Requires -RunAsAdministrator
# =====================================================================
# Phase API Versioned Routing - Etapa F (23.5.2026)
# api_version_promote.ps1 - snapshot rotation + DB update + restart secondary
# =====================================================================
# Co dela:
#   1. Robocopy C:\Projekty\STRATEGIE -> C:\Projekty\STRATEGIE-prev (mirror)
#   2. Python (psycopg2):
#        - SELECT current's version_string + released_at + git_sha
#        - UPDATE previous SET (version_string, released_at, git_sha) = current's values
#          (previous teted "stari V1.3.25" = frozen snapshot tohoto okamziku)
#        - UPDATE current SET version_string=increment(current), released_at=NOW()
#          (current dostane V1.3.26, ready pro dalsi deploy)
#   3. Restart-Service STRATEGIE-API-B (loads new previous code)
#   4. Health check 8003
#
# Marti's vize z 23.5. odpoledne:
#   "Mela by se inkrementovat zatim jednoduse automaticky posledni cislo
#    vzdy pri kopirovani adresare actual na previous. Tj, behem push a
#    pull by se mel menit jen datum aktualni verze."
#
# Usage (na cloud APP):
#   cd C:\Projekty\STRATEGIE
#   .\scripts\api_version_promote.ps1
#
# ASCII-only (gotcha #110 PS5.1 cp1250 default).
# =====================================================================

$ErrorActionPreference = "Stop"

$Source = "C:\Projekty\STRATEGIE"
$Target = "C:\Projekty\STRATEGIE-prev"
$SecondaryService = "STRATEGIE-API-B"
$SecondaryPort = 8003
$PythonExe = "C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs\strategie-W5adySD1-py3.14\Scripts\python.exe"

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
    exit 1
}

Write-Host "=== Phase API Versioned Routing - Promotion ===" -ForegroundColor Cyan
Write-Host ""

# =====================================================================
# 1. Pre-snapshot: show current state
# =====================================================================
Write-Host "=== Step 1: Pre-snapshot state ===" -ForegroundColor Cyan
$srcSha = (& git -C $Source log -1 --pretty=format:"%h %s" 2>$null)
Write-Host "  Source HEAD: $srcSha"

if (Test-Path $Target) {
    $tgtSha = (& git -C $Target log -1 --pretty=format:"%h %s" 2>$null)
    Write-Host "  Target HEAD (will be overwritten): $tgtSha"
}
Write-Host ""

# =====================================================================
# 2. Robocopy snapshot
# =====================================================================
Write-Host "=== Step 2: Robocopy mirror $Source -> $Target ===" -ForegroundColor Cyan
$StartTime = Get-Date
robocopy $Source $Target /MIR /XJ /NFL /NDL /R:1 /W:1 | Out-Null
$ec = $LASTEXITCODE
$Elapsed = (Get-Date) - $StartTime

if ($ec -ge 8) {
    Write-Error "Robocopy failed (exit code $ec)"
    exit 1
}
Write-Host "  Done in $([int]$Elapsed.TotalSeconds)s (robocopy exit code $ec = success)"
Write-Host ""

# =====================================================================
# 3. DB update via Python venv
# =====================================================================
Write-Host "=== Step 3: UPDATE fw.api_version (rotate + increment) ===" -ForegroundColor Cyan
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    exit 1
}

$GitSha = (& git -C $Source rev-parse HEAD).Trim()

$PyScript = @"
import os, sys, re
sys.path.insert(0, r'$Source')
from dotenv import load_dotenv
load_dotenv(r'$Source\.env')
import psycopg2

url = os.environ.get('STRATEGIE_DATA_DB_URL') or os.environ.get('DATABASE_URL')
if not url:
    print('FAIL: STRATEGIE_DATA_DB_URL not set'); sys.exit(1)
url = url.replace('postgresql+psycopg2://', 'postgresql://').replace('postgresql+asyncpg://', 'postgresql://')

conn = psycopg2.connect(url)
conn.autocommit = False
cur = conn.cursor()

# 1) Get current's state
cur.execute('SELECT version_string, released_at, git_sha FROM fw.api_version WHERE version_code = %s', ('current',))
current_row = cur.fetchone()
if not current_row:
    print('FAIL: current row not found'); sys.exit(1)
cur_version, cur_released, cur_sha = current_row
print(f'  Current was: version_string={cur_version}, released_at={cur_released}, git_sha={cur_sha[:7] if cur_sha else None}')

# 2) UPDATE previous = current's old values (frozen snapshot of "today's V1.3.25")
cur.execute('''
    UPDATE fw.api_version
    SET version_string = %s, released_at = %s, git_sha = %s
    WHERE version_code = %s
    RETURNING version_string
''', (cur_version, cur_released, cur_sha, 'previous'))
prev_updated = cur.fetchone()
print(f'  Previous now: version_string={prev_updated[0] if prev_updated else None}')

# 3) Increment current's version_string (V1.3.25 -> V1.3.26)
m = re.match(r'^(V\d+\.\d+\.)(\d+)$', cur_version)
if not m:
    print(f'FAIL: cannot parse version_string {cur_version!r}'); sys.exit(1)
new_version = f'{m.group(1)}{int(m.group(2)) + 1}'
print(f'  Auto-increment: {cur_version} -> {new_version}')

# 4) UPDATE current = new version + NOW() + new git_sha
cur.execute('''
    UPDATE fw.api_version
    SET version_string = %s, released_at = NOW(), git_sha = %s
    WHERE version_code = %s
    RETURNING version_string, TO_CHAR(released_at, 'DD.MM. HH24:MI') AS released
''', (new_version, '$GitSha', 'current'))
new_cur = cur.fetchone()
print(f'  Current now: version_string={new_cur[0]}, released_at={new_cur[1]}')

conn.commit()
cur.close(); conn.close()
print('  COMMIT OK')
"@

& $PythonExe -c $PyScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python DB update failed (exit code $LASTEXITCODE)"
    exit 1
}
Write-Host ""

# =====================================================================
# 4. Restart secondary
# =====================================================================
Write-Host "=== Step 4: Restart-Service $SecondaryService ===" -ForegroundColor Cyan
try {
    Restart-Service $SecondaryService -Force -ErrorAction Stop
    Start-Sleep -Seconds 5
    $svc = Get-Service $SecondaryService
    Write-Host "  Status: $($svc.Status)"

    if ($svc.Status -ne "Running") {
        Write-Warning "Secondary failed to start (status: $($svc.Status))"
    }
    else {
        $health = Invoke-RestMethod "http://localhost:$SecondaryPort/api/v1/health" -TimeoutSec 5
        Write-Host "  Health: $($health | ConvertTo-Json -Compress)"
    }
}
catch {
    Write-Warning "Secondary restart/health-check failed: $($_.Exception.Message)"
    Write-Host "  Check log: Get-Content C:\Logs\STRATEGIE\strategie-api-b.stderr.log -Tail 30"
}
Write-Host ""

# =====================================================================
# 5. Summary
# =====================================================================
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Promotion complete:"
Write-Host "  - Mirror snapshot: $Source -> $Target"
Write-Host "  - DB: previous = old current (frozen snapshot)"
Write-Host "  - DB: current = new version_string (auto-incremented) + NOW()"
Write-Host "  - Secondary restarted on port $SecondaryPort"
Write-Host ""
Write-Host "Browser: hard reload https://strategie-ai.com (Ctrl+Shift+R)"
Write-Host "  - Pill v paticce: nove V1.3.X (auto-incremented)"
Write-Host "  - Dropup: previous row ma timestamp z promotion momentu"
Write-Host "  - Po pin na previous: secondary teted ma stejny kod jako current"
