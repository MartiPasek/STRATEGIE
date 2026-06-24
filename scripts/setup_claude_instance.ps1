# setup_claude_instance.ps1 - turnkey setup watcheru pro libovolnou instanci Claude.
# Marti 24.6.2026. Spustit JAKO SPRAVCE na cilovem pocitaci.
# Tajemstvi (token, PAT) se NEukladaji do kodu - predavaji se jako parametry.
#
# Priklady:
#   Sarka  (25):  setup_claude_instance.ps1 -InstanceId 25 -InstanceName Sarka -Token "<t>" -GitPat "<p>"
#   Peta   (26):  setup_claude_instance.ps1 -InstanceId 26 -InstanceName Peta  -Token "<t>" -GitPat "<p>"
#   Jirka  (28):  setup_claude_instance.ps1 -InstanceId 28 -InstanceName Jirka -Token "<t>" -GitPat "<p>"
#   Tym CMS(27):  setup_claude_instance.ps1 -InstanceId 27 -InstanceName Tym   -Token "<t>" -GitPat "<p>"
#
param(
    [Parameter(Mandatory=$true)][string]$InstanceId,
    [Parameter(Mandatory=$true)][string]$InstanceName,
    [Parameter(Mandatory=$true)][string]$Token,
    [string]$GitPat = "",
    [string]$Repo   = "D:\Projekty\STRATEGIE",
    [string]$Python = "C:\Python312\python.exe",
    [string]$Nssm   = "C:\Tools\nssm.exe"
)
$ErrorActionPreference = "Stop"
Write-Host ("== Claude setup (instance " + $InstanceId + " / " + $InstanceName + ") ==") -ForegroundColor Cyan

# 1) Repo (clone nebo pull)
if (Test-Path "$Repo\.git") {
    Write-Host "Repo existuje -> git pull"
    git -C $Repo pull
} else {
    Write-Host "Klonuji repo do $Repo"
    git clone https://github.com/MartiPasek/STRATEGIE.git $Repo
}

# 2) INSTANCE_ID (gitignored, per-stroj)
Set-Content -Path "$Repo\scripts\claude_sql\INSTANCE_ID.txt" -Value $InstanceId -NoNewline
Write-Host ("INSTANCE_ID.txt = " + $InstanceId)

# 3) Logy
New-Item -ItemType Directory -Force -Path "C:\Logs\STRATEGIE" | Out-Null

# 4) NSSM sluzba (cista reinstalace)
if (Get-Service STRATEGIE-CLAUDE-SQL -ErrorAction SilentlyContinue) {
    Write-Host "Sluzba existuje -> zastavuji a odebiram"
    & $Nssm stop STRATEGIE-CLAUDE-SQL
    & $Nssm remove STRATEGIE-CLAUDE-SQL confirm
}
& $Nssm install STRATEGIE-CLAUDE-SQL $Python "$Repo\scripts\claude_sql_runner.py"
& $Nssm set STRATEGIE-CLAUDE-SQL AppDirectory $Repo
& $Nssm set STRATEGIE-CLAUDE-SQL AppStdout ("C:\Logs\STRATEGIE\claude_sql_" + $InstanceId + ".log")
& $Nssm set STRATEGIE-CLAUDE-SQL AppStderr ("C:\Logs\STRATEGIE\claude_sql_" + $InstanceId + ".log")
& $Nssm set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START

# Tajemstvi do AppEnvironmentExtra (NE systemove promenne - SCM cache!)
$envArgs = @(
    "STRATEGIE_DEPLOY_TOKEN=$Token",
    "CLAUDE_INSTANCE_ID=$InstanceId",
    "CLAUDE_INSTANCE_NAME=$InstanceName"
)
if ($GitPat -ne "") { $envArgs += "STRATEGIE_GIT_PAT=$GitPat" }
& $Nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra @envArgs

Start-Service STRATEGIE-CLAUDE-SQL
Start-Sleep -Seconds 3
$svc = Get-Service STRATEGIE-CLAUDE-SQL
Write-Host ("Sluzba STRATEGIE-CLAUDE-SQL: " + $svc.Status) -ForegroundColor Green

Write-Host ""
Write-Host "HOTOVO (bridge bezi). Dalsi krok:" -ForegroundColor Cyan
Write-Host (" 1) Otevri Cowork (Claude desktop) na tomto stroji s pristupem ke slozce " + $Repo)
Write-Host (" 2) Claude si nacte svuj MD (docs/team/) + CLAUDE.md (krabicka)")
Write-Host (" 3) Over presence: v fw.claude_instance se objevi radek " + $InstanceId + " . " + $InstanceName)
Write-Host ""
Write-Host "Pri potizich: C:\Logs\STRATEGIE\claude_sql_$InstanceId.log (401 = spatny token v AppEnvironmentExtra)"
