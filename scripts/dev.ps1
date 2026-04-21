<#
.SYNOPSIS
  Spustí STRATEGIE dev server. Před startem uvolní port, pokud je obsazený.

.DESCRIPTION
  Řeší běžný Windows problém, kdy po Ctrl+C v uvicornu zůstává port v
  TIME_WAIT nebo zombie proces. Skript najde všechny procesy držící daný
  port a ukončí je (force kill). Teprve potom spustí uvicorn.

.PARAMETER Port
  Port, na kterém má uvicorn běžet. Default: 8002.

.PARAMETER Reload
  Když je zadán (switch), spustí uvicorn s --reload pro auto-restart
  při změně souborů.

.EXAMPLE
  .\scripts\dev.ps1
  .\scripts\dev.ps1 -Port 8003
  .\scripts\dev.ps1 -Reload
#>

param(
    [int]$Port   = 8002,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "══ STRATEGIE dev server ══" -ForegroundColor Cyan
Write-Host "Port: $Port" -ForegroundColor DarkGray

# ── 1) Uvolnění portu ───────────────────────────────────────────────────
function Free-Port {
    param([int]$P)
    try {
        $connections = Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue
    } catch {
        $connections = $null
    }

    # Fallback přes netstat (univerzálnější než Get-NetTCPConnection)
    $pids = @()
    if ($connections) {
        $pids = $connections.OwningProcess | Select-Object -Unique
    } else {
        $netstat = netstat -ano | Select-String ":$P\s" | Select-String "LISTENING"
        foreach ($line in $netstat) {
            $parts = $line.ToString().Trim() -split "\s+"
            if ($parts.Count -ge 5) {
                $pids += [int]$parts[-1]
            }
        }
        $pids = $pids | Sort-Object -Unique
    }

    if (-not $pids -or $pids.Count -eq 0) {
        Write-Host "Port $P je volný." -ForegroundColor Green
        return
    }

    foreach ($procId in $pids) {
        if ($procId -eq 0) { continue }
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Write-Host ("Ukončuji: PID=$procId ({0})" -f $proc.ProcessName) -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction Stop
        } catch {
            Write-Host "Nepodařilo se ukončit PID=$procId ($_)" -ForegroundColor Red
        }
    }
    # Pauza, ať Windows uvolní socket. 300ms se nekdy ukazalo jako malo --
    # nasledny uvicorn bind pak padal s WinError 10048 (TIME_WAIT). 2s je
    # bezpecnejsi kompromis.
    Start-Sleep -Seconds 2
    Write-Host "Port $P uvolněn." -ForegroundColor Green
}

Free-Port -P $Port

# ── 2) Sestavení příkazu pro uvicorn ────────────────────────────────────
$uvicornArgs = @("run", "uvicorn", "apps.api.main:app", "--port", "$Port")
if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host ""
Write-Host "Spouštím: python -m poetry $($uvicornArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

python -m poetry @uvicornArgs
