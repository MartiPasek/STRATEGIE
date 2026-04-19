"""
Projects API router — CRUD + switch pro projekty.
Base: /api/v1/projects
"""
from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.projects.application import service as project_service
from modules.projects.application.service import (
    ProjectError, NotTenantMember, NotProjectMember, NotAuthorizedToCreate,
)
from modules.projects.api.schemas import (
    ProjectInfo, CreateProjectRequest, CreateProjectResponse,
    SwitchProjectRequest, SwitchProjectResponse, RenameProjectRequest,
)

logger = get_logger("projects.api")

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


@router.get("/list", response_model=list[ProjectInfo])
def list_projects(req: Request):
    """Seznam aktivních projektů v aktuálním tenantu usera, seřazeno podle aktivity."""
    user_id = _get_uid(req)
    rows = project_service.list_projects_for_user(user_id)
    return [ProjectInfo(**r) for r in rows]


@router.post("/create", response_model=CreateProjectResponse)
def create_project(body: CreateProjectRequest, req: Request):
    """Vytvoří nový projekt v aktuálním tenantu. MVP: jen tenant owner."""
    user_id = _get_uid(req)
    try:
        project_id = project_service.create_project(user_id=user_id, name=body.name)
    except NotTenantMember as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotAuthorizedToCreate as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CreateProjectResponse(id=project_id, name=body.name.strip())


@router.post("/switch", response_model=SwitchProjectResponse)
def switch_project(body: SwitchProjectRequest, req: Request):
    """
    Přepne aktivní projekt usera. body.project_id = None znamená 'bez projektu'.
    """
    user_id = _get_uid(req)
    try:
        result = project_service.switch_project_for_user(
            user_id=user_id, project_id=body.project_id
        )
    except NotProjectMember as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SwitchProjectResponse(**result)


@router.post("/{project_id}/archive")
def archive_project(project_id: int, req: Request):
    """Archivuj projekt (is_active=False). Opravnění: project owner / tenant owner."""
    user_id = _get_uid(req)
    try:
        ok = project_service.archive_project(user_id=user_id, project_id=project_id)
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": ok}


@router.patch("/{project_id}/rename")
def rename_project(project_id: int, body: RenameProjectRequest, req: Request):
    """Přejmenuj projekt. Opravnění: project owner / tenant owner."""
    user_id = _get_uid(req)
    try:
        ok = project_service.rename_project(
            user_id=user_id, project_id=project_id, new_name=body.name
        )
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": ok, "name": body.name.strip()}
