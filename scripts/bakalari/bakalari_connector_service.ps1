# Bakalari ctemy most - SERVISNI KONEKTOR (Faze 1 / produkce).
# Bezi SKRYTE v relaci uzivatele (kvuli VPN), spusteny Naplanovanou ulohou "pri prihlaseni".
# Konfigurace z prostredi (zadne okenko, zadny prompt) -> muze bezet bez obsluhy.
# READ-ONLY: pousti jen SELECT/WITH/EXPLAIN/SHOW. Heslo cte z env (nastavi Marti lokalne).
#
# Pozaduje uzivatelske env promenne (setx ... pak odhlaseni/prihlaseni):
#   STRATEGIE_DEPLOY_TOKEN, BAKA_PASS  (povinne)
#   BAKA_SERVER (default 172.16.6.225,1433), BAKA_DB (default bakalari), BAKA_USER (default BakaRO)
#
# Log: vedle skriptu do bakalari_service.log

$ProgressPreference = 'SilentlyContinue'
try { [System.Net.WebRequest]::DefaultWebProxy = $null } catch {}
try { [System.Net.ServicePointManager]::Expect100Continue = $false } catch {}
try { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 } catch {}

$base   = "https://strategie-ai.com/api/v1/erp"
$pollMs = 2500
$logf   = Join-Path $PSScriptRoot "bakalari_service.log"

function Log($m) {
  $line = ("[" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + "] " + $m)
  try { Add-Content -Path $logf -Value $line -Encoding UTF8 } catch {}
}

$server = if ($env:BAKA_SERVER) { $env:BAKA_SERVER } else { "172.16.6.225,1433" }
$db     = if ($env:BAKA_DB)     { $env:BAKA_DB }     else { "bakalari" }
$user   = if ($env:BAKA_USER)   { $env:BAKA_USER }   else { "BakaRO" }
$token  = $env:STRATEGIE_DEPLOY_TOKEN
$pwd    = $env:BAKA_PASS

if (-not $token -or -not $pwd) {
  Log "CHYBI STRATEGIE_DEPLOY_TOKEN nebo BAKA_PASS v env -> koncim. Nastav pres setx a prihlas se znovu."
  exit 1
}
Log ("Start. Cil: " + $server + " / " + $db + " / " + $user)

$csb = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
$csb."Data Source" = $server; $csb."Initial Catalog" = $db
$csb."User ID" = $user; $csb."Password" = $pwd
$csb."Encrypt" = $false; $csb."TrustServerCertificate" = $true; $csb."Connect Timeout" = 15
$connStr = $csb.ConnectionString
$cn = $null
function Ensure-Conn {
  if ($cn -eq $null -or $cn.State -ne "Open") {
    if ($cn -ne $null) { try { $cn.Close() } catch {} }
    $script:cn = New-Object System.Data.SqlClient.SqlConnection $connStr
    $cn.Open()
  }
}

$hdr = @{ "X-Deploy-Token" = $token }
Log ("Pollovani co " + ($pollMs/1000) + "s. Cloud: " + $base)

while ($true) {
 try {
  $p = $null
  try {
    $p = Invoke-RestMethod -Method Get -Uri "$base/bakalari/pending" -Headers $hdr -TimeoutSec 20
  } catch {
    Log ("pending chyba: " + $_.Exception.Message); Start-Sleep -Milliseconds 4000; continue
  }
  if (-not $p.query) { Start-Sleep -Milliseconds $pollMs; continue }

  $qid = $p.query.id; $sql = [string]$p.query.sql
  Log ("dotaz #" + $qid + ": " + ($sql.Substring(0, [Math]::Min(80, $sql.Length))))

  $okFlag = $false; $resultObj = $null; $errMsg = $null
  if ($sql -notmatch '^\s*(SELECT|WITH|EXPLAIN|SHOW)\b') {
    $errMsg = "Konektor je READ-ONLY (jen SELECT/WITH/EXPLAIN/SHOW)."
  } else {
    try {
      Ensure-Conn
      $cmd = $cn.CreateCommand(); $cmd.CommandText = $sql; $cmd.CommandTimeout = 60
      $rd = $cmd.ExecuteReader()
      $cols = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $cols += $rd.GetName($i) }
      $rows = New-Object System.Collections.ArrayList
      while ($rd.Read()) {
        $o = [ordered]@{}
        for ($i = 0; $i -lt $rd.FieldCount; $i++) {
          $v = $rd.GetValue($i)
          $o[[string]$cols[$i]] = ($(if ($v -is [DBNull]) { $null } else { $v }))
        }
        [void]$rows.Add($o)
      }
      $rd.Close()
      $arr = @($rows)
      $resultObj = @{ ok = $true; columns = $cols; rows = $arr; count = $arr.Count }
      $okFlag = $true
    } catch {
      $errMsg = $_.Exception.Message
      try { if ($cn -ne $null) { $cn.Close() } } catch {}
      $script:cn = $null
    }
  }

  if ($okFlag) { $body = @{ id = $qid; ok = $true;  result = $resultObj } | ConvertTo-Json -Depth 10 -Compress }
  else         { $body = @{ id = $qid; ok = $false; error  = $errMsg }   | ConvertTo-Json -Compress }
  try {
    $bb = [System.Text.Encoding]::UTF8.GetBytes($body)
    $rq = [System.Net.HttpWebRequest]::Create("$base/bakalari/result")
    $rq.Method = "POST"; $rq.ContentType = "application/json; charset=utf-8"
    $rq.Headers.Add("X-Deploy-Token", $token)
    $rq.Timeout = 30000; $rq.ReadWriteTimeout = 30000; $rq.ServicePoint.Expect100Continue = $false
    $rq.ContentLength = $bb.Length
    $st = $rq.GetRequestStream(); $st.Write($bb, 0, $bb.Length); $st.Close()
    $rq.GetResponse().Close()
    Log ("    -> " + $(if ($okFlag) { "OK (" + $resultObj.count + " radku)" } else { "CHYBA: " + $errMsg }))
  } catch {
    Log ("    -> odeslani vysledku selhalo: " + $_.Exception.Message)
  }
 } catch {
  Log ("smycka vyjimka: " + $_.Exception.Message); Start-Sleep -Milliseconds 3000
 }
}
