# EUROSOFT-MCP self-update restart (bezi jako SYSTEM scheduled task = mimo job
# sluzby, prezije Stop-Service). Stop -> robocopy repo->pkg (*.py) -> Start.
# Spousti ho @@MCPUPDATE pres jednorazovou naplanovanou ulohu. ASCII-only.
param(
  [string]$Svc = 'EUROSOFT-MCP',
  [string]$Src = 'C:\PROJEKTY\STRATEGIE\modules\eurosoft_mcp',
  [string]$Pkg = 'C:\eurosoft_mcp\eurosoft_mcp'
)
$log = 'C:\eurosoft_mcp\selfupdate_last.log'
"[{0}] start svc=$Svc" -f (Get-Date -Format s) | Out-File $log -Encoding ascii
try {
  Stop-Service $Svc -Force -ErrorAction SilentlyContinue
  $i = 0
  while (((Get-Service $Svc).Status -ne 'Stopped') -and ($i -lt 40)) {
    Start-Sleep -Milliseconds 500; $i++
  }
  "[{0}] stopped after {1} ticks" -f (Get-Date -Format s), $i | Out-File $log -Append -Encoding ascii
  Start-Sleep -Seconds 1
  robocopy $Src $Pkg *.py /NJH /NJS /NP /IS /R:8 /W:2 | Out-Null
  "[{0}] robocopy rc=$LASTEXITCODE" -f (Get-Date -Format s) | Out-File $log -Append -Encoding ascii
  Remove-Item -Recurse -Force "$Pkg\__pycache__" -ErrorAction SilentlyContinue
  Start-Service $Svc
  "[{0}] started" -f (Get-Date -Format s) | Out-File $log -Append -Encoding ascii
} catch {
  "[{0}] ERROR $($_.Exception.Message)" -f (Get-Date -Format s) | Out-File $log -Append -Encoding ascii
}
# uklid: smaz jednorazovou ulohu (nezablokuje pripadny dalsi beh)
schtasks /delete /tn EUROSOFT-MCP-SelfUpdate /f 2>$null | Out-Null
