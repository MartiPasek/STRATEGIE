"""Phase 24-F REST router -- UI Pyramida Browser.

3 endpointy:
  GET /api/v1/md_pyramid/list -- list vsech md (filtered per viewer)
  GET /api/v1/md_pyramid/md/{id} -- konkretni md content (read-only)
  GET /api/v1/md_pyramid/count -- count pro badge polling

Auth: cookie user_id. Vsechny endpointy returnu 401 bez auth.
"""
from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.md_pyramid.application import service as md_pyr_service
from core.database_core import get_core_session
from modules.core.infrastructure.models_core import User

logger = get_logger("md_pyramid.api")

router = APIRouter(prefix="/api/v1/md_pyramid", tags=["md_pyramid"])


def _get_viewer_context(req: Request) -> tuple[int, bool]:
    """Vrat (user_id, is_parent). Raise 401 bez auth."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            raise HTTPException(status_code=401, detail="User nenalezen.")
        is_parent = bool(getattr(u, "is_marti_parent", False))
    finally:
        cs.close()

    return user_id, is_parent


@router.get("/list")
def list_pyramid(req: Request, include_archived: bool = False) -> dict:
    """Vrati list md_documents pro UI sidebar.

    Parent vidi vse, non-parent jen vlastni md1.
    include_archived=true (parent only): vrati i archived rows.
    """
    user_id, is_parent = _get_viewer_context(req)
    # Non-parent nesmi videt archived (vse archived rovna se 'parent matters')
    effective_include = include_archived and is_parent
    items = md_pyr_service.list_pyramid_for_ui(
        viewer_user_id=user_id,
        is_parent=is_parent,
        include_archived=effective_include,
    )
    return {
        "items": items,
        "is_parent_view": is_parent,
        "include_archived": effective_include,
        "count": len(items),
    }


@router.get("/md/{md_id}")
def get_md(md_id: int, req: Request) -> dict:
    """Vrati konkretni md content (read-only) pro UI modal.

    Permission filter:
      - parent: vidi vsechny md (vc. internal_only sekci, vc. archived)
      - non-parent: jen vlastni md1, internal_only sekce vyriznute
    """
    user_id, is_parent = _get_viewer_context(req)
    item = md_pyr_service.get_md_for_ui(
        md_id=md_id,
        viewer_user_id=user_id,
        is_parent=is_parent,
        allow_archived=is_parent,
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="md_document nenalezeno nebo nemas pristup.",
        )
    return item


@router.post("/md/{md_id}/archive")
def archive_md(md_id: int, req: Request, body: dict | None = None) -> dict:
    """Phase 24-D: Archive md (parent only). Soft delete, vratne pres restore."""
    user_id, is_parent = _get_viewer_context(req)
    if not is_parent:
        raise HTTPException(status_code=403, detail="Jen rodic muze archivovat md.")
    reason = (body or {}).get("reason") or ""
    try:
        result = md_pyr_service.archive_md_document(
            md_id=md_id, triggered_by_user_id=user_id, reason=reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/md/{md_id}/reset")
def reset_md(md_id: int, req: Request, body: dict | None = None) -> dict:
    """Phase 24-D: Reset md (parent only). Hard reset content na default template."""
    user_id, is_parent = _get_viewer_context(req)
    if not is_parent:
        raise HTTPException(status_code=403, detail="Jen rodic muze resetovat md.")
    reason = (body or {}).get("reason") or ""
    try:
        result = md_pyr_service.reset_md_document(
            md_id=md_id, triggered_by_user_id=user_id, reason=reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/md/{md_id}/restore")
def restore_md(md_id: int, req: Request) -> dict:
    """Phase 24-D: Restore md z archived/reset zpet na active (parent only)."""
    user_id, is_parent = _get_viewer_context(req)
    if not is_parent:
        raise HTTPException(status_code=403, detail="Jen rodic muze obnovit md.")
    try:
        result = md_pyr_service.restore_md_document(
            md_id=md_id, triggered_by_user_id=user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/count")
def count_pyramid(req: Request) -> dict:
    """Vrati pocet md rows viditelnych pro viewera. Pro UI badge polling."""
    user_id, is_parent = _get_viewer_context(req)
    items = md_pyr_service.list_pyramid_for_ui(
        viewer_user_id=user_id, is_parent=is_parent,
    )
    return {"count": len(items)}
