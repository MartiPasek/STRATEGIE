"""
Database backup service (Phase 7.11).

Dumpne obe databaze (css_db, data_db) pres `pg_dump -Fc` (custom format,
compressed, restorable pres pg_restore). Soubory jdou do:
    <repo_root>/backups/YYYY-MM-DD/css_db_HHMMSS.dump
    <repo_root>/backups/YYYY-MM-DD/data_db_HHMMSS.dump

Volano z:
- API endpoint POST /api/v1/admin/backup-databases (UI tlacitko)
- PowerShell skript scripts/backup_dbs.ps1 (CLI)

Bezpecnost:
- backups/ je v .gitignore -- nikdy ne do gitu (obsahuje PII + emaily).
- Operace je parent-only (viz router guard).
- Pri behu se PGPASSWORD nastavuje do env child procesu, ne do logu.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from core.config import settings
from core.logging import get_logger

logger = get_logger("admin.backup")


class BackupError(Exception):
    pass


def _repo_root() -> Path:
    """
    Najde root repa: hleda od cwd nahoru soubor `pyproject.toml` nebo `.git`.
    Fallback: cwd.
    """
    cwd = Path(os.getcwd()).resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return cwd


def _resolve_pg_dump() -> str:
    """
    Najde pg_dump binarku. Poradi:
      1. Env var PG_DUMP_PATH (override)
      2. pg_dump v PATH
      3. Typicka Windows umisteni (Program Files\\PostgreSQL\\<v>\\bin)
    """
    override = os.environ.get("PG_DUMP_PATH")
    if override and Path(override).exists():
        return override

    found = shutil.which("pg_dump")
    if found:
        return found

    # Windows fallback
    program_files_candidates = [
        Path(r"C:\Program Files\PostgreSQL"),
        Path(r"C:\Program Files (x86)\PostgreSQL"),
    ]
    for base in program_files_candidates:
        if not base.exists():
            continue
        # Najdi nejvyssi verzi (napr. "16", "15", "14")
        versions = sorted(
            [d for d in base.iterdir() if d.is_dir() and d.name.isdigit()],
            key=lambda d: int(d.name),
            reverse=True,
        )
        for v in versions:
            candidate = v / "bin" / "pg_dump.exe"
            if candidate.exists():
                return str(candidate)

    raise BackupError(
        "pg_dump nenalezen. Nainstaluj PostgreSQL klienta, nebo nastav "
        "env var PG_DUMP_PATH na absolutni cestu k pg_dump(.exe)."
    )


def _parse_db_url(url: str) -> tuple[str, str, str, str, str]:
    """
    Vrati (host, port, user, password, dbname).
    Pro pouziti v PGPASSWORD + pg_dump command line args.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("postgresql", "postgres"):
        raise BackupError(f"Nepodporovane DB URL schema '{parsed.scheme}' (ocekavam postgresql://)")
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)
    user = parsed.username or ""
    password = parsed.password or ""
    dbname = (parsed.path or "").lstrip("/")
    if not dbname:
        raise BackupError(f"DB URL neobsahuje nazev databaze: {url[:40]}...")
    return host, port, user, password, dbname


def _dump_one(label: str, db_url: str, out_dir: Path, pg_dump: str) -> dict:
    """
    Dumpne jednu DB do out_dir/<label>_<HHMMSS>.dump (custom format, compressed).
    Vraci dict s file_path, size_bytes, duration_s.
    """
    host, port, user, password, dbname = _parse_db_url(db_url)
    ts = datetime.now().strftime("%H%M%S")
    out_file = out_dir / f"{label}_{ts}.dump"

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        pg_dump,
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", dbname,
        "-Fc",             # custom format (compressed, restorable s pg_restore)
        "-Z", "6",         # komprese level 6 (default je 6, explicitne pro jistotu)
        "--no-owner",      # restore ma byt idempotentni i v cilove DB kde nemuze vlastnik existovat
        "-f", str(out_file),
    ]

    logger.info(
        f"BACKUP | dumping {label} | host={host} db={dbname} -> {out_file.name}"
    )
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min hard limit
        )
    except subprocess.TimeoutExpired:
        raise BackupError(f"{label}: pg_dump timeout (>10 min)")
    except FileNotFoundError as e:
        raise BackupError(f"{label}: pg_dump binarka nenalezena ({e})")

    duration = time.time() - t0

    if proc.returncode != 0:
        # Vycisti cast-way file
        try:
            out_file.unlink(missing_ok=True)
        except Exception:
            pass
        stderr_tail = (proc.stderr or "")[-500:]
        raise BackupError(
            f"{label}: pg_dump selhal (exit={proc.returncode}). "
            f"Stderr tail: {stderr_tail}"
        )

    size = out_file.stat().st_size if out_file.exists() else 0
    logger.info(
        f"BACKUP | done {label} | size={size} B | duration={duration:.2f}s"
    )
    return {
        "label": label,
        "file_path": str(out_file),
        "file_name": out_file.name,
        "size_bytes": size,
        "duration_s": round(duration, 2),
    }


def run_backup() -> dict:
    """
    Dumpne obe DB. Vraci dict:
    {
      "status": "ok" | "failed",
      "date": "YYYY-MM-DD",
      "out_dir": "...",
      "files": [{"label", "file_path", "file_name", "size_bytes", "duration_s"}, ...],
      "error": None | "..."
    }
    """
    try:
        pg_dump = _resolve_pg_dump()
    except BackupError as e:
        return {
            "status": "failed",
            "error": str(e),
            "date": None,
            "out_dir": None,
            "files": [],
        }

    if not settings.database_core_url or not settings.database_data_url:
        return {
            "status": "failed",
            "error": "database_core_url nebo database_data_url neni v .env",
            "date": None,
            "out_dir": None,
            "files": [],
        }

    today = datetime.now().strftime("%Y-%m-%d")
    backups_base = os.environ.get("BACKUPS_DIR") or str(_repo_root() / "backups")
    out_dir = Path(backups_base) / today
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {
            "status": "failed",
            "error": f"nelze vytvorit out_dir {out_dir}: {e}",
            "date": today,
            "out_dir": str(out_dir),
            "files": [],
        }

    files: list[dict] = []
    errors: list[str] = []
    for label, url in (
        ("css_db", settings.database_core_url),
        ("data_db", settings.database_data_url),
    ):
        try:
            info = _dump_one(label, url, out_dir, pg_dump)
            files.append(info)
        except BackupError as e:
            errors.append(str(e))
            logger.error(f"BACKUP | {label} failed | {e}")
        except Exception as e:
            errors.append(f"{label}: {e}")
            logger.exception(f"BACKUP | {label} unexpected | {e}")

    status = "ok" if not errors else "failed"
    return {
        "status": status,
        "date": today,
        "out_dir": str(out_dir),
        "files": files,
        "error": "; ".join(errors) if errors else None,
    }
