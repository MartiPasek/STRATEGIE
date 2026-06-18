# Bakalari ctemy most - KONEKTOR (Faze 1). Bezi na NB s VPN do Nerudovky.
# Pollne nas cloud (odchozi HTTPS + token), spusti READ-ONLY SELECT proti
# Bakalarum (vestaveny .NET SqlClient) a vrati vysledek. Nic se neinstaluje.
# Heslo k BakaRO se zada v okenku pri startu (nikam se neuklada).
#
# SPUSTENI (Windows PowerShell, na NB s VPN):
#   powershell -ExecutionPolicy Bypass -File .\bakalari_connector.ps1
# Nech bezet po dobu prace. Ctrl+C ukonci.

$ErrorActionPreference = "Stop"

# --- ZRYCHLENI HTTP (klicove pres VPN) ---
# Bez tohoto Invoke-RestMethod kazde volani hleda WPAD proxy (i nekolik minut!).
$ProgressPreference = 'SilentlyContinue'
try { [System.Net.WebRequest]::DefaultWebProxy = $null } catch {}
try { [System.Net.ServicePointManager]::Expect100Continue = $false } catch {}
try { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 } catch {}

$base   = "https://strategie-ai.com/api/v1/erp"
$pollMs = 2500

# --- cilovy server (prompt s defaultem na TEST) ---
$server = Read-Host "Bakalari server IP,port [Enter = 172.16.6.225,1433 (TEST)]"
if (-not $server) { $server = "172.16.6.225,1433" }
$db = Read-Host "Databaze [Enter = bakalari]"
if (-not $db) { $db = "bakalari" }
$user = Read-Host "SQL login [Enter = BakaRO]"
if (-not $user) { $user = "BakaRO" }
Write-Host ("Cil: " + $server + " / " + $db + " / " + $user)

# --- token (z env, jinak prompt) ---
$token = $env:STRATEGIE_DEPLOY_TOKEN
if (-not $token) {
  $token = Read-Host "STRATEGIE_DEPLOY_TOKEN (z cloudu)"
}
if (-not $token) { Write-Host "Bez tokenu nelze, koncim."; exit 1 }

# --- heslo BakaRO pres okenko (paste Ctrl+V, skryte) ---
Add-Type -AssemblyName System.Windows.Forms
$frm = New-Object System.Windows.Forms.Form
$frm.Text = "Heslo k uctu BakaRO (konektor)"; $frm.Width = 400; $frm.Height = 170
$frm.TopMost = $true; $frm.StartPosition = "CenterScreen"
$lbl = New-Object System.Windows.Forms.Label
$lbl.Text = "Vloz heslo (Ctrl+V) a dej OK:"; $lbl.Left = 12; $lbl.Top = 14; $lbl.Width = 360
$tb = New-Object System.Windows.Forms.TextBox
$tb.UseSystemPasswordChar = $true; $tb.Left = 12; $tb.Top = 42; $tb.Width = 360
$btn = New-Object System.Windows.Forms.Button
$btn.Text = "OK"; $btn.Left = 290; $btn.Top = 78; $btn.Width = 82
$btn.Add_Click({ $frm.Tag = $tb.Text; $frm.Close() })
$frm.AcceptButton = $btn
$frm.Controls.AddRange(@($lbl, $tb, $btn))
[void]$tb.Focus(); [void]$frm.ShowDialog()
$pwd = [string]$frm.Tag
if (-not $pwd) { Write-Host "Nezadano heslo, koncim."; exit 1 }

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
Write-Host "Konektor Bakalari bezi. Pollovani co $($pollMs/1000)s. Ctrl+C ukonci."
Write-Host "Cloud: $base   server: $server"

while ($true) {
  try {
    $p = Invoke-RestMethod -Method Get -Uri "$base/bakalari/pending" -Headers $hdr -TimeoutSec 20
  } catch {
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] pending chyba: " + $_.Exception.Message)
    Start-Sleep -Milliseconds 4000; continue
  }
  if (-not $p.query) { Start-Sleep -Milliseconds $pollMs; continue }

  $qid = $p.query.id; $sql = [string]$p.query.sql
  Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] dotaz #" + $qid + ": " + ($sql.Substring(0, [Math]::Min(80, $sql.Length))))

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
    # Primy HttpWebRequest s UTF-8 byty - obchazi pomalost Invoke-RestMethod u non-ASCII tela
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
    $req = [System.Net.HttpWebRequest]::Create("$base/bakalari/result")
    $req.Method = "POST"
    $req.ContentType = "application/json; charset=utf-8"
    $req.Headers.Add("X-Deploy-Token", $token)
    $req.Timeout = 30000
    $req.ReadWriteTimeout = 30000
    $req.ServicePoint.Expect100Continue = $false
    $req.ContentLength = $bodyBytes.Length
    $rs = $req.GetRequestStream(); $rs.Write($bodyBytes, 0, $bodyBytes.Length); $rs.Close()
    $resp = $req.GetResponse(); $resp.Close()
    Write-Host ("    -> " + $(if ($okFlag) { "OK (" + $resultObj.count + " radku)" } else { "CHYBA: " + $errMsg }))
  } catch {
    Write-Host ("    -> odeslani vysledku selhalo: " + $_.Exception.Message)
  }
}
