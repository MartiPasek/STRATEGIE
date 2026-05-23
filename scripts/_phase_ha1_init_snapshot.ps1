#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 Blue-Green: Initial snapshot
# Copy C:\Projekty\STRATEGIE -> C:\Projekty\STRATEGIE-prev
# ============================================================
# ASCII-only (gotcha #110 PS5.1 cp1250 default).
# Run ONCE pri prvni instalaci blue-green deploy.
# Pak daily_rotation.ps1 prepise snapshot pred kazdym git pull.
# ============================================================

$Source = "C:\Projekty\STRATEGIE"
$Target = "C:\Projekty\STRATEGIE-prev"

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
    exit 1
}

if (Test-Path $Target) {
    Write-Host "Target already exists: $Target"
    $resp = Read-Host "Overwrite? (yes/no)"
    if ($resp -ne "yes") {
        Write-Host "Aborted."
        exit 0
    }
    Write-Host "Removing existing target..."
    Remove-Item -Path $Target -Recurse -Force -ErrorAction Stop
}

Write-Host "Copying $Source to $Target ..."
Write-Host "(includes .git for git operations, full mirror)"
$StartTime = Get-Date

# Robocopy: /MIR mirror, /XJ exclude junctions, /NFL /NDL quiet, /R:1 /W:1 fast fail
robocopy $Source $Target /MIR /XJ /NFL /NDL /R:1 /W:1 | Out-Null
$ec = $LASTEXITCODE

$Elapsed = (Get-Date) - $StartTime
Write-Host ""

# Robocopy exit codes 0-7 = success (some files copied/skipped is OK)
if ($ec -ge 8) {
    Write-Error "Robocopy failed (exit code $ec)"
    exit 1
}

Write-Host "Done in $([int]$Elapsed.TotalSeconds)s (robocopy exit code $ec = success)"
Write-Host ""
Write-Host "Verify both checkouts on same commit:"
Write-Host "  cd $Source"
Write-Host "  git log -1 --oneline"
Write-Host "  cd $Target"
Write-Host "  git log -1 --oneline"
