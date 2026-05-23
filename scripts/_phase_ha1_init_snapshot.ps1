#Requires -RunAsAdministrator
# ============================================================
# Phase HA-1 Blue-Green: Initial snapshot
# Copy C:\Projekty\STRATEGIE -> C:\Projekty\STRATEGIE-prev
# ============================================================
# Run ONCE pri prvni instalaci blue-green deploy.
# Pak daily_rotation.ps1 prepiše snapshot pred kazdym git pull.
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
    # Remove target — but preserve any local-only files (logs etc) by listing first
    Write-Host "Removing existing target..."
    Remove-Item -Path $Target -Recurse -Force
}

Write-Host "Copying $Source -> $Target ..."
Write-Host "(includes .git for git operations; excludes nothing — full mirror)"
$StartTime = Get-Date

# Robocopy is faster + reliable for large dirs (includes .git)
# /MIR = mirror (delete target files not in source)
# /XJ = exclude junction points (avoid pypoetry-cache cycles)
# /NFL /NDL = no file/dir listing (quiet)
# /R:1 /W:1 = retry 1× wait 1s (fast fail)
robocopy $Source $Target /MIR /XJ /NFL /NDL /R:1 /W:1

$Elapsed = (Get-Date) - $StartTime
Write-Host ""
Write-Host "Done in $([int]$Elapsed.TotalSeconds)s"
Write-Host ""
Write-Host "Verify:"
Write-Host "  cd $Target"
Write-Host "  git log -1 --oneline"
Write-Host "  # should match: cd $Source; git log -1 --oneline"
