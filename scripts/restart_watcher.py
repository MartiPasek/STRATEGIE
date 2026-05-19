"""Phase 42 — STRATEGIE-RESTART-WATCHER service.

Standalone Python service co bezi jako NSSM Windows service na cloud APP.
Sleduje marker files v D:\\Data\\STRATEGIE\\restart_markers\\ a kazdy detekovany
*.touch file trigeruje Restart-Service STRATEGIE-API.

Marti's Q1 doctrine (Phase 42 design 18.5. vecer): NSSM watchdog -- separate
service, neni v STRATEGIE-API process (vyhne se gotcha 'sluzba restartuje
sebe sama v middle of HTTP request').

Workflow:
  1. propose_deployment v Marti-AI / chat
  2. approve_deployment -> deployment_service vola git pull + touch marker
  3. RESTART-WATCHER kazde 2s scanuje MARKER_DIR
  4. Pri nalezeni *.touch file:
     a. precte JSON (proposal_id, proposed_by)
     b. presune file do MARKER_DIR/processed/<timestamp>_<orig_name>
     c. spusti `nssm restart STRATEGIE-API` (synchronous)
     d. log do D:\\Data\\STRATEGIE\\restart_markers\\watcher.log
  5. Po restartu STRATEGIE-API: pull novy kod uz funguje

NSSM install (jednorazove na cloud APP):
  # Vytvorit marker dir pokud neexistuje
  New-Item -ItemType Directory -Path "C:\\Data\\STRATEGIE\\restart_markers" -Force

  C:\\Tools\\nssm.exe install STRATEGIE-RESTART-WATCHER python ^
    "C:\\Projekty\\STRATEGIE\\scripts\\restart_watcher.py"
  C:\\Tools\\nssm.exe set STRATEGIE-RESTART-WATCHER AppDirectory C:\\Projekty\\STRATEGIE
  C:\\Tools\\nssm.exe set STRATEGIE-RESTART-WATCHER AppStdout ^
    C:\\Data\\STRATEGIE\\restart_markers\\watcher.log
  C:\\Tools\\nssm.exe set STRATEGIE-RESTART-WATCHER AppStderr ^
    C:\\Data\\STRATEGIE\\restart_markers\\watcher.log
  C:\\Tools\\nssm.exe set STRATEGIE-RESTART-WATCHER Start SERVICE_AUTO_START
  C:\\Tools\\nssm.exe start STRATEGIE-RESTART-WATCHER

Usage manual (development / debug):
  python scripts/restart_watcher.py
  -> Ctrl+C to stop
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration
# Cloud APP nema D: drive (gotcha 19.5.2026). Default je C:\Data\STRATEGIE\restart_markers.
# Configurable: nastavit env STRATEGIE_RESTART_MARKER_DIR pokud chces jinde.
MARKER_DIR = Path(
    os.environ.get("STRATEGIE_RESTART_MARKER_DIR")
    or r"C:\Data\STRATEGIE\restart_markers"
)
PROCESSED_DIR = MARKER_DIR / "processed"
LOG_FILE = MARKER_DIR / "watcher.log"
SCAN_INTERVAL_SEC = 2.0
NSSM_EXE = r"C:\Tools\nssm.exe"
TARGET_SERVICE = "STRATEGIE-API"
RESTART_TIMEOUT_SEC = 60


def _log(msg: str) -> None:
    """Append timestamped line do watcher.log + stdout (NSSM zachyti AppStdout)."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


def _restart_strategie_api() -> tuple[bool, str]:
    """Spusti `nssm restart STRATEGIE-API` synchronne. Returns (ok, output)."""
    cmd = [NSSM_EXE, "restart", TARGET_SERVICE]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RESTART_TIMEOUT_SEC,
            encoding="utf-8",
            errors="replace",
        )
        ok = result.returncode == 0
        return ok, (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return False, f"nssm restart timed out after {RESTART_TIMEOUT_SEC}s"
    except FileNotFoundError:
        return False, f"NSSM not found at {NSSM_EXE}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _process_marker(marker_path: Path) -> None:
    """Precte JSON marker, presune do processed/, restartne STRATEGIE-API."""
    try:
        raw = marker_path.read_text(encoding="utf-8")
        info = json.loads(raw) if raw.strip() else {}
        proposal_id = info.get("proposal_id", "?")
        proposed_by = info.get("proposed_by", "unknown")
    except Exception as exc:
        proposal_id = "?"
        proposed_by = "unknown"
        _log(f"marker parse failed: {marker_path.name}: {exc}")

    _log(f"detected marker: {marker_path.name} (proposal={proposal_id}, by={proposed_by})")

    # Move to processed BEFORE restart (idempotency -- nezopakuje pri rychlém scanu)
    try:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = PROCESSED_DIR / f"{ts}_{marker_path.name}"
        marker_path.rename(dest)
        _log(f"moved marker to processed: {dest.name}")
    except OSError as exc:
        _log(f"WARNING: marker move failed (will retry next scan): {exc}")
        return

    # Trigger restart
    _log(f"restarting {TARGET_SERVICE} via NSSM...")
    ok, output = _restart_strategie_api()
    if ok:
        _log(f"{TARGET_SERVICE} restart OK: {output[:200]}")
    else:
        _log(f"FAIL {TARGET_SERVICE} restart: {output[:500]}")


def _scan_once() -> int:
    """Single pass: scan MARKER_DIR pro *.touch files, process each. Returns count."""
    if not MARKER_DIR.exists():
        return 0
    try:
        touch_files = sorted(MARKER_DIR.glob("*.touch"))
    except OSError as exc:
        _log(f"scan glob failed: {exc}")
        return 0
    for mp in touch_files:
        try:
            _process_marker(mp)
        except Exception as exc:
            _log(f"_process_marker crashed on {mp.name}: {exc}")
    return len(touch_files)


def main() -> None:
    _log(f"STRATEGIE-RESTART-WATCHER started (PID {sys.argv}, scan_dir={MARKER_DIR})")
    _log(f"NSSM: {NSSM_EXE}, target service: {TARGET_SERVICE}, interval={SCAN_INTERVAL_SEC}s")
    try:
        while True:
            try:
                _scan_once()
            except Exception as exc:
                _log(f"scan loop crash: {type(exc).__name__}: {exc}")
            time.sleep(SCAN_INTERVAL_SEC)
    except KeyboardInterrupt:
        _log("STRATEGIE-RESTART-WATCHER stopped (Ctrl+C)")


if __name__ == "__main__":
    main()
