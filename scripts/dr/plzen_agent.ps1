# plzen_agent.ps1 — Plzeň DR relay poller (Claude C23, 23.7.2026)
# Každý běh (scheduled task à 1-2 min, SYSTEM): vyzvedne z Prahy zařazené příkazy,
# spustí je lokálně, vrátí stdout/stderr/rc. Vyprázdní frontu (loop, cap 10/běh).
# Enqueue dělá jen Claude na Martiho pokyn + vše auditováno ve fw.plzen_cmd_queue.
# Poller je druhá pojistka: ODMÍTNE destruktivní vzory (drop db, format, diskpart, ...).
param(
  [string]$Base  = 'https://strategie-ai.com',
  [string]$Token = '@@PLZEN_TOKEN@@',
  [string]$Log   = 'D:\STRATEGIE_IN\_plzen_agent.log',
  [int]$MaxPerRun = 10
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
function Log($m){ $l=('{0}  {1}' -f ([DateTime]::Now.ToString('s')),$m); Write-Output $l; try{ Add-Content $Log $l -Encoding UTF8 }catch{} }

# Katastrofické vzory — poller je NESPUSTÍ a nahlásí zpět jako 'refused'.
$deny = @(
  'drop\s+database', 'drop\s+schema', 'truncate\s+table',
  '\bdiskpart\b', 'Clear-Disk', 'Format-Volume', 'format\s+[A-Za-z]:',
  'Remove-Item\s+["'']?[A-Za-z]:\\?["'']?\s', 'rd\s+/s', 'rmdir\s+/s',
  'rm\s+-rf\s+/'
)

function Post-Result($nonce,$status,$rc,$out,$err,$ms){
  $body = @{ nonce=$nonce; status=$status; exit_code=$rc; stdout=$out; stderr=$err; duration_ms=$ms } | ConvertTo-Json -Depth 3
  try {
    $w = New-Object System.Net.WebClient
    $w.Headers.Add('X-Plzen-Token',$Token)
    $w.Headers.Add('Content-Type','application/json; charset=utf-8')
    $w.Encoding = [System.Text.Encoding]::UTF8
    $w.UploadString("$Base/api/v1/ops/plzen/result",'POST',$body) | Out-Null
  } catch { Log ("result POST fail: " + $_.Exception.Message) }
}

$n = 0
while($n -lt $MaxPerRun){
  $n++
  try {
    $w = New-Object System.Net.WebClient
    $w.Headers.Add('X-Plzen-Token',$Token)
    $w.Encoding = [System.Text.Encoding]::UTF8
    $resp = $w.DownloadString("$Base/api/v1/ops/plzen/pending")
  } catch { Log ("pending fail: " + $_.Exception.Message); break }
  try { $j = $resp | ConvertFrom-Json } catch { Log "pending: nevalidni JSON"; break }
  if(-not $j.cmd){ break }   # fronta prázdná / relay vypnutá

  $nonce = [string]$j.cmd.nonce
  $label = [string]$j.cmd.label
  $command = [string]$j.cmd.command
  Log ("PRIKAZ nonce=$nonce label=$label")

  $blocked = $false
  foreach($p in $deny){ if($command -imatch $p){ $blocked = $true; break } }
  if($blocked){
    Log ("ODMITNUTO (denylist): " + $label)
    Post-Result $nonce 'refused' -999 '' 'Odmitnuto pollerem: prikaz odpovida destruktivnimu vzoru (denylist).' 0
    continue
  }

  $t0 = Get-Date
  $of = [IO.Path]::GetTempFileName(); $ef = [IO.Path]::GetTempFileName()
  $rc = -1
  try {
    $p = Start-Process -FilePath 'powershell.exe' `
         -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-Command',$command) `
         -RedirectStandardOutput $of -RedirectStandardError $ef -NoNewWindow -Wait -PassThru
    $rc = $p.ExitCode
  } catch { $rc = -1; Add-Content $ef ("Start-Process fail: " + $_.Exception.Message) }
  $ms = [int]((Get-Date)-$t0).TotalMilliseconds

  $out = ''; $err = ''
  try { $out = [string](Get-Content $of -Raw -ErrorAction SilentlyContinue) } catch {}
  try { $err = [string](Get-Content $ef -Raw -ErrorAction SilentlyContinue) } catch {}
  Remove-Item $of,$ef -ErrorAction SilentlyContinue
  if($out.Length -gt 180000){ $out = $out.Substring(0,180000) + "`n...[oriznuto]" }
  if($err.Length -gt 180000){ $err = $err.Substring(0,180000) + "`n...[oriznuto]" }

  $status = if($rc -eq 0){ 'done' } else { 'error' }
  Log ("HOTOVO rc=$rc dur=${ms}ms")
  Post-Result $nonce $status $rc $out $err $ms
}
