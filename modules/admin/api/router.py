"""
Admin API router (Phase 7.11).

Parent-only operace: backup databazi (zatim) + misto pro budouci admin tooly.
"""
from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.admin.application import backup_service
from modules.thoughts.application.service import is_marti_parent

logger = get_logger("admin.api")

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _require_parent(user_id: int) -> None:
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Tato operace je dostupna pouze rodicum Marti (is_marti_parent=True).",
        )


@router.post("/backup-databases")
def backup_databases(req: Request):
    """
    Dumpne obe DB (css_db + data_db) do backups/YYYY-MM-DD/*.dump.
    Parent-only, synchronni operace (wait for pg_dump).

    Vraci:
      {
        "status": "ok" | "failed",
        "date": "YYYY-MM-DD",
        "out_dir": "...",
        "files": [{"label","file_name","size_bytes","duration_s"}, ...],
        "error": None | "..."
      }
    """
    uid = _get_uid(req)
    _require_parent(uid)
    logger.info(f"ADMIN | backup requested | user={uid}")
    result = backup_service.run_backup()
    logger.info(
        f"ADMIN | backup result | status={result.get('status')} | "
        f"files={len(result.get('files') or [])}"
    )
    return result
