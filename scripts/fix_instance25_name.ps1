# Jednorazovy fix: doplni CLAUDE_INSTANCE_ID=25 + CLAUDE_INSTANCE_NAME=Sarka
# do env NSSM sluzby STRATEGIE-CLAUDE-SQL pres registr (token/PAT zustanou).
# Spoustet jako spravce. Po pouziti lze smazat.
$ErrorActionPreference = 'Stop'

$key = 'HKLM:\SYSTEM\CurrentControlSet\Services\STRATEGIE-CLAUDE-SQL\Parameters'
$cur = (Get-ItemProperty -Path $key -Name AppEnvironmentExtra).AppEnvironmentExtra

$new = @($cur | Where-Object { $_ -notmatch '^CLAUDE_INSTANCE_(ID|NAME)=' })
$new += 'CLAUDE_INSTANCE_ID=25'
$new += 'CLAUDE_INSTANCE_NAME=Sarka'

Set-ItemProperty -Path $key -Name AppEnvironmentExtra -Value ([string[]]$new) -Type MultiString
Write-Host ("Env aktualizovan. Pocet polozek: {0}" -f $new.Count)

Restart-Service STRATEGIE-CLAUDE-SQL
Start-Sleep 4

Write-Host "--- poslednich 5 radku logu ---"
Get-Content C:\Logs\STRATEGIE\claude_sql_25.log -Tail 5
