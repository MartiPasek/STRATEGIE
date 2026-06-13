# Build podepsaneho AAB pro Google Play (gradlew bundleRelease).
# Pouziva release signingConfig (strategie-release.jks pres keystore.properties).
# Marti 9.6.2026. ASCII-only (doctrine #110).
$ErrorActionPreference = "Stop"
$mobile = Join-Path $PSScriptRoot "..\APP\Mobile"
Set-Location $mobile

# JAVA_HOME: pouzij stavajici, jinak zkus Android Studio JBR
if (-not $env:JAVA_HOME -or -not (Test-Path $env:JAVA_HOME)) {
    foreach ($c in @(
        "C:\Program Files\Android\Android Studio\jbr",
        "C:\Program Files\Android\Android Studio1\jbr",
        "C:\Program Files\Android\Android Studio Preview\jbr"
    )) { if (Test-Path $c) { $env:JAVA_HOME = $c; break } }
}
Write-Host "JAVA_HOME = $env:JAVA_HOME"
Write-Host "Spoustim: gradlew.bat bundleRelease ..."
Write-Host ""

& .\gradlew.bat bundleRelease --console=plain

$aab = Join-Path $mobile "app\build\outputs\bundle\release\app-release.aab"
Write-Host ""
if (Test-Path $aab) {
    $kb = [int]((Get-Item $aab).Length / 1KB)
    Write-Host "=========================================="
    Write-Host "HOTOVO. Podepsany AAB:"
    Write-Host $aab
    Write-Host ("Velikost: {0} KB" -f $kb)
    Write-Host "=========================================="
} else {
    Write-Host "CHYBA: AAB nenalezen. Zkontroluj vystup gradle vyse."
}
