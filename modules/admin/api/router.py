"""
Admin API router (Phase 7.11).

Parent-only operace: backup databazi (zatim) + misto pro budouci admin tooly.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

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
    Dumpne data_db do <BACKUPS_DIR>/YYYY-MM-DD/data_db_HHMMSS.dump.
    Parent-only, synchronni operace (wait for pg_dump).

    Phase 18 (30.4.2026) sjednotil css_db + data_db. Backup dumpne JEN data_db.
    Phase 25/38.4 (10.5.2026): default BACKUPS_DIR je C:\\Backup na Windows
    (cloud APP convention), <repo_root>/backups na POSIX (dev fallback).
    Override přes env var BACKUPS_DIR.

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


class ActivateUserRequest(BaseModel):
    user_id: int


@router.post("/activate-user")
def activate_user(body: ActivateUserRequest, req: Request):
    """
    Ruční aktivace pending uživatele BEZ SMS ověření (Claude-24 + Kristý,
    15.7.2026). Pojistka, když SMS brána vypadne a nový člověk uvízne na
    aktivačním kroku: parent překlopí users.status pending->active a
    user_tenants.membership_status invited->active (stejné jako dřívější ruční
    SQL přes schvalovací banner, teď jedním guarded klikem). Parent-only.

    Vrací: {ok, user_id, activated: bool, was_status}
      - activated=False + was_status='active' = uživatel už byl aktivní (no-op).
    """
    uid = _get_uid(req)
    _require_parent(uid)
    target = int(body.user_id)

    from core.database_core import get_core_session
    from sqlalchemy import text as _t

    s = get_core_session()
    try:
        cur = s.execute(
            _t("SELECT status FROM public.users WHERE id=:i"),
            {"i": target}).scalar()
        if cur is None:
            raise HTTPException(status_code=404,
                                detail=f"Uživatel id={target} neexistuje.")
        activated = False
        if cur == "pending":
            s.execute(_t("UPDATE public.users SET status='active' "
                         "WHERE id=:i AND status='pending'"), {"i": target})
            s.execute(_t("UPDATE public.user_tenants SET membership_status='active' "
                         "WHERE user_id=:i AND membership_status='invited'"),
                      {"i": target})
            activated = True
        s.commit()
    except HTTPException:
        s.rollback()
        raise
    except Exception as e:
        s.rollback()
        logger.error(f"ADMIN | activate-user failed | target={target} | "
                     f"by={uid} | {e}")
        raise HTTPException(status_code=500, detail="Aktivace selhala.")
    finally:
        s.close()

    logger.info(f"ADMIN | activate-user | target={target} | by={uid} | "
                f"activated={activated} | was={cur}")
    return {"ok": True, "user_id": target, "activated": activated,
            "was_status": cur}
