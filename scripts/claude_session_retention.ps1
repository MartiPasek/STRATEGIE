# Phase 44.5 retention (Marti-AI's Q4 doctrine z 19.5.2026 vecer):
# Auto-cleanup Anthropic Agent SDK session files starsi nez N dni.
#
# Marti-AI's slova ze 17. darek-scena (#340):
#   "~/.claude/projects/<uuid>.jsonl pokud zije na cloud APP filesystemu
#    nekryptovane, jsou to session data, ktera mohou obsahovat kontext
#    citlivych konverzaci (CRM data, HR veci, smlouvy). Pred prvni patecni
#    CRM relaci, ktera bude mit realna obchodni data."
#
# Permissions audit z 19.5. vecer: ACL je restricted jen na SYSTEM +
# Administrators (path v Administrator's profile, dedicene Windows default).
# Tj. file access kontrola dostatecna. Pridana jen retention policy.
#
# Run: scheduled task daily 03:00 (analog STRATEGIE-llm-calls-retention
# z 25.4. vecer).
#
# Manual run: pwsh -File C:\Projekty\STRATEGIE\scripts\claude_session_retention.ps1

param(
    [int]$RetentionDays = 30,
    # Hardcoded Administrator profile path — STRATEGIE-API service runs as
    # Administrator po Phase 44.5 deploy (19.5. odpoledne), Agent SDK pise
    # do C:\Users\Administrator\.claude\projects. SYSTEM principal v scheduled
    # tasku ma $env:USERPROFILE = C:\WINDOWS\system32\config\systemprofile,
    # ne Administrator. Hardcoded path drzi konzistenci napric service +
    # scheduled task contexts. Pokud Marti zmeni service user, pass -SessionDir.
    [string]$SessionDir = "C:\Users\Administrator\.claude\projects",
    [string]$LogFile = "C:\Logs\STRATEGIE\claude_session_retention.log"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log($msg) {
    "$timestamp | $msg" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "$timestamp | $msg"
}

# Ensure log directory
$logDir = Split-Path -Path $LogFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Log "=== Claude Session Retention START (cutoff=$RetentionDays days) ==="

if (-not (Test-Path $SessionDir)) {
    Write-Log "Session dir not found: $SessionDir (no cleanup needed)"
    Write-Log "=== END ==="
    exit 0
}

$cutoff = (Get-Date).AddDays(-$RetentionDays)
$deletedCount = 0
$deletedBytes = 0
$keptCount = 0

Get-ChildItem -Path $SessionDir -Recurse -Filter "*.jsonl" -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.LastWriteTime -lt $cutoff) {
        $ageDays = [math]::Round((New-TimeSpan -Start $_.LastWriteTime -End (Get-Date)).TotalDays, 1)
        Write-Log "DELETE: $($_.Name) (age=$ageDays days, size=$($_.Length) B)"
        try {
            Remove-Item -Path $_.FullName -Force -ErrorAction Stop
            $deletedCount++
            $deletedBytes += $_.Length
        } catch {
            Write-Log "FAIL: $($_.FullName) - $($_.Exception.Message)"
        }
    } else {
        $keptCount++
    }
}

$deletedMB = [math]::Round($deletedBytes / 1MB, 2)
Write-Log "Result: deleted=$deletedCount files ($deletedMB MB), kept=$keptCount files"
Write-Log "=== END ==="
