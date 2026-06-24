# setup_claude27.ps1 - turnkey setup watcheru pro instanci Claude-27 (tym-instance)
# Marti 24.6.2026. Spustit JAKO SPRAVCE na sdilenem pocitaci Marti-AI.
# Tajemstvi (token, PAT) se NEukladaji do kodu - predavaji se jako parametry.
#
# Priklad:
#   powershell -ExecutionPolicy Bypass -File setup_claude27.ps1 -Token "<deploy token>" -GitPat "<github PAT>"
#
param(
    [string]$Repo   = "D:\Projekty\STRATEGIE",
    [string]$Python = "C:\Python312\python.exe",
    [string]$Nssm   = "C:\Tools\nssm.exe",
    [Parameter(Mandatory=$true)][string]$Token,
    [string]$GitPat = ""
)
$ErrorActionPreference = "Stop"
Write-Host "== Claude-27 setup (instance 27, tym-instance) ==" -ForegroundColor Cyan

# 1) Repo (clone nebo pull)
if (Test-Path "$Repo\.git") {
    Write-Host "Repo existuje -> git pull"
    git -C $Repo pull
} else {
    Write-Host "Klonuji repo do $Repo"
    git clone https://github.com/MartiPasek/STRATEGIE.git $Repo
}

# 2) INSTANCE_ID = 27 (gitignored, per-stroj)
Set-Content -Path "$Repo\scripts\claude_sql\INSTANCE_ID.txt" -Value "27" -NoNewline
Write-Host "INSTANCE_ID.txt = 27"

# 3) Logy
New-Item -ItemType Directory -Force -Path "C:\Logs\STRATEGIE" | Out-Null

# 4) NSSM sluzba (cista reinstalace, kdyby uz existovala)
if (Get-Service STRATEGIE-CLAUDE-SQL -ErrorAction SilentlyContinue) {
    Write-Host "Sluzba existuje -> zastavuji a odebiram pro cistou reinstalaci"
    & $Nssm stop STRATEGIE-CLAUDE-SQL
    & $Nssm remove STRATEGIE-CLAUDE-SQL confirm
}
& $Nssm install STRATEGIE-CLAUDE-SQL $Python "$Repo\scripts\claude_sql_runner.py"
& $Nssm set STRATEGIE-CLAUDE-SQL AppDirectory $Repo
& $Nssm set STRATEGIE-CLAUDE-SQL AppStdout "C:\Logs\STRATEGIE\claude_sql_27.log"
& $Nssm set STRATEGIE-CLAUDE-SQL AppStderr "C:\Logs\STRATEGIE\claude_sql_27.log"
& $Nssm set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START

# Tajemstvi do AppEnvironmentExtra (NE do systemovych promennych - SCM cache!)
$envArgs = @(
    "STRATEGIE_DEPLOY_TOKEN=$Token",
    "CLAUDE_INSTANCE_ID=27",
    "CLAUDE_INSTANCE_NAME=Tym"
)
if ($GitPat -ne "") { $envArgs += "STRATEGIE_GIT_PAT=$GitPat" }
& $Nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra @envArgs

Start-Service STRATEGIE-CLAUDE-SQL
Start-Sleep -Seconds 3
$svc = Get-Service STRATEGIE-CLAUDE-SQL
Write-Host ("Sluzba STRATEGIE-CLAUDE-SQL: " + $svc.Status) -ForegroundColor Green

Write-Host ""
Write-Host "HOTOVO (bridge bezi). Dalsi kroky pro Claude-27 naziva:" -ForegroundColor Cyan
Write-Host " 1) Otevri Cowork (Claude desktop) na tomto stroji s pristupem ke slozce $Repo"
Write-Host " 2) Claude-27 si nacte docs/team27/Claude27.MD (master) + osobni MD (Mirek/Zuzka/Misa/Eliska)"
Write-Host " 3) Over presence: v fw.claude_instance se objevi radek 27 . Tym . <hostname>"
Write-Host " 4) Claude-27 zkontroluje frontu prikazem:  @@Q27 LIST"
Write-Host ""
Write-Host "Pri potizich: C:\Logs\STRATEGIE\claude_sql_27.log (401 = spatny token v AppEnvironmentExtra)"
