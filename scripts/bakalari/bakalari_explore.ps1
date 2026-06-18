# Bakalari - read-only pruzkum schematu (Faze 0) - cista PowerShell verze.
# Spustit na NTB s VPN do Nerudovky. Nic se neinstaluje (vestaveny .NET SqlClient).
# Heslo se zada v okenku (paste Ctrl+V), nikam se neuklada. Skript je jen ctteci.
#
# SPUSTENI:
#   powershell -ExecutionPolicy Bypass -File .\bakalari_explore.ps1
# Nebo cely obsah zkopiruj a vloz do okna Windows PowerShell.

$ErrorActionPreference = "Stop"
$server = "172.16.6.225,1433"
$db     = "bakalari"
$user   = "BakaRO"
$out    = (Join-Path ([Environment]::GetFolderPath('Desktop')) "bakalari_schema_dump.txt")

$kw = @("rozvrh","hodin","predmet","ucitel","trida","mistnost","ucebna","vyuk",
        "uvazek","skupin","kabinet","zvon","obdobi","lesson","timetable","teacher",
        "class","room","subject","schedule","perioda")

# --- heslo pres male okenko (paste funguje, skryte) ---
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$frm = New-Object System.Windows.Forms.Form
$frm.Text = "Heslo k uctu BakaRO"; $frm.Width = 400; $frm.Height = 170
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
if (-not $pwd) { Write-Host "Nezadano zadne heslo, koncim."; exit 1 }
Write-Host ("Heslo zadano, pocet znaku: " + $pwd.Length)

# --- connection string builderem (spravne zaescapuje heslo) ---
$csb = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
$csb."Data Source"            = $server
$csb."Initial Catalog"        = $db
$csb."User ID"                = $user
$csb."Password"               = $pwd
$csb."Encrypt"                = $false
$csb."TrustServerCertificate" = $true
$csb."Connect Timeout"        = 15

Write-Host "Pripojuji se na $server, DB $db, ucet $user ..."
$cn = New-Object System.Data.SqlClient.SqlConnection $csb.ConnectionString
try { $cn.Open() }
catch {
  Write-Host "CHYBA pripojeni: $($_.Exception.Message)"
  Write-Host "Zkontroluj: zapnuta VPN do Nerudovky, spravne heslo, dostupnost serveru."
  exit 2
}

# Dotaz -> pole radku, kazdy radek = pole hodnot (cteni po poradi sloupcu).
function Q([string]$sql) {
  $cmd = $cn.CreateCommand(); $cmd.CommandText = $sql
  $rd = $cmd.ExecuteReader()
  $rows = New-Object System.Collections.Generic.List[object]
  while ($rd.Read()) {
    $o = New-Object object[] $rd.FieldCount
    for ($i = 0; $i -lt $rd.FieldCount; $i++) {
      $v = $rd.GetValue($i)
      $o[$i] = ($(if ($v -is [DBNull]) { "" } else { [string]$v }))
    }
    $rows.Add($o)
  }
  $rd.Close()
  return $rows
}

$L = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $L.Add($s); Write-Host $s }

W("# BAKALARI - pruzkum schematu (read-only)")
W("# " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "  server=$server  db=$db")
W("")

try { $v = Q("SELECT @@VERSION"); W("## Verze SQL serveru"); if ($v.Count) { W($v[0][0]) }; W("") }
catch { W("(verze se nenacetla: $($_.Exception.Message))") }

$tbl = Q("SELECT s.name, t.name, COALESCE(SUM(p.rows),0) " +
         "FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id " +
         "LEFT JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1) " +
         "GROUP BY s.name,t.name ORDER BY s.name,t.name")

W("## Tabulky (" + $tbl.Count + " celkem)")
W("")
W("### Pravdepodobne ROZVRHOVE tabulky:")
foreach ($r in $tbl) {
  $n = ([string]$r[1]).ToLower()
  if ($kw | Where-Object { $n.Contains($_) }) { W("  - " + $r[0] + "." + $r[1] + "  (" + $r[2] + " radku)") }
}
W("")
W("### Vsechny tabulky (schema.tabulka . radku):")
foreach ($r in $tbl) { W("  " + $r[0] + "." + $r[1] + " . " + $r[2]) }
W("")

W("## Sloupce vsech tabulek")
$cols = Q("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, " +
          "CAST(CHARACTER_MAXIMUM_LENGTH AS varchar(20)), IS_NULLABLE " +
          "FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION")
$cur = ""
foreach ($r in $cols) {
  $key = [string]$r[0] + "." + [string]$r[1]
  if ($key -ne $cur) { W(""); W("### " + $key); $cur = $key }
  $ln = "  " + $r[2] + " : " + $r[3]
  if ($r[4] -ne "" -and $r[4] -ne "-1") { $ln += "(" + $r[4] + ")" }
  if ($r[5] -eq "NO") { $ln += " NOT NULL" }
  W($ln)
}

$cn.Close()
Set-Content -Path $out -Value $L -Encoding UTF8
Write-Host ""
Write-Host "HOTOVO. Vystup ulozen do: $out"
Write-Host "Posli tenhle soubor Claudovi (Martinovi)."
