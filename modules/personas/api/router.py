"""
Personas API router — list + direct switch + avatar upload.
Base: /api/v1/personas
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse

from core.logging import get_logger
from modules.personas.application import service as persona_service
from modules.personas.application.service import PersonaError
from modules.personas.api.schemas import (
    PersonaInfo, SwitchPersonaRequest, SwitchPersonaResponse,
    CreatePersonaRequest, CreatePersonaResponse,
    UpdatePersonaRequest, PersonaDetail,
)

logger = get_logger("personas.api")

router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


@router.get("/list", response_model=list[PersonaInfo])
def list_personas(req: Request):
    """Seznam dostupných person pro current usera (globální + jeho tenant)."""
    user_id = _get_uid(req)
    rows = persona_service.list_personas_for_user(user_id)
    return [PersonaInfo(**r) for r in rows]


@router.post("/create", response_model=CreatePersonaResponse)
def create_persona(body: CreatePersonaRequest, req: Request):
    """Vytvoří novou personu. MVP: JEN SUPERADMIN (user_id=1 Marti)."""
    user_id = _get_uid(req)
    # Second gate — i kdyby se nekdo dostal do volani, superadmin check
    # je v service vrstve. Tento endpoint tim padem vraci 403 pro vsechny
    # non-admin requesty (viz service).
    try:
        result = persona_service.create_persona(
            user_id=user_id,
            name=body.name,
            description=body.description,
            system_prompt=body.system_prompt,
        )
    except PersonaError as e:
        # Superadmin check hlaska -> 403; ostatni -> 400.
        msg = str(e)
        if "superadmin" in msg.lower():
            raise HTTPException(status_code=403, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return CreatePersonaResponse(**result)


@router.get("/{persona_id}", response_model=PersonaDetail)
def get_persona(persona_id: int, req: Request):
    """Detail persony (vč. plného system_prompt) — pro edit modal."""
    user_id = _get_uid(req)
    try:
        result = persona_service.get_persona_detail(
            user_id=user_id, persona_id=persona_id,
        )
    except PersonaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PersonaDetail(**result)


@router.patch("/{persona_id}", response_model=CreatePersonaResponse)
def update_persona(persona_id: int, body: UpdatePersonaRequest, req: Request):
    """Edit persony (name / system_prompt). JEN SUPERADMIN + ne globální."""
    user_id = _get_uid(req)
    try:
        result = persona_service.update_persona(
            user_id=user_id,
            persona_id=persona_id,
            name=body.name,
            description=body.description,
            system_prompt=body.system_prompt,
        )
    except PersonaError as e:
        msg = str(e)
        if "superadmin" in msg.lower():
            raise HTTPException(status_code=403, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return CreatePersonaResponse(id=result["id"], name=result["name"])


@router.post("/switch", response_model=SwitchPersonaResponse)
def switch_persona(body: SwitchPersonaRequest, req: Request):
    """Přepni personu konverzace přímo podle persona_id."""
    user_id = _get_uid(req)
    try:
        result = persona_service.switch_persona_direct(
            user_id=user_id,
            conversation_id=body.conversation_id,
            persona_id=body.persona_id,
        )
    except PersonaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SwitchPersonaResponse(**result)


# ── AVATAR (foto persony) ────────────────────────────────────────────────

@router.post("/{persona_id}/avatar")
async def upload_avatar(persona_id: int, req: Request, file: UploadFile = File(...)):
    """Upload avatar fotky pro personu. Resize na 256x256 JPEG, ulozeni
    do {AVATARS_STORAGE_DIR}/persona_{id}.jpg + DB persona.avatar_path.
    Pristup: jen superadmin (jako create/edit persona)."""
    from modules.personas.application import avatar_service
    from modules.personas.application.service import _is_superadmin

    user_id = _get_uid(req)
    if not _is_superadmin(user_id):
        raise HTTPException(status_code=403, detail="Avatar smi nahrat jen superadmin.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Chybí filename.")
    content = await file.read()
    try:
        path = avatar_service.save_avatar(persona_id, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload selhal: {e}")
    return {"status": "uploaded", "path": path}


@router.get("/{persona_id}/avatar")
def get_avatar(persona_id: int, req: Request):
    """Servne ulozeny avatar (JPEG). 404 pokud persona avatar nemá."""
    from modules.personas.application import avatar_service
    _ = _get_uid(req)   # auth-only (zadny privilege check, vsichni v tenantu vidi)
    path = avatar_service.get_avatar_path(persona_id)
    if not path:
        raise HTTPException(status_code=404, detail="Avatar neexistuje.")
    return FileResponse(path, media_type="image/jpeg")


@router.delete("/{persona_id}/avatar")
def delete_avatar(persona_id: int, req: Request):
    """Smaze avatar (soubor + DB cesta). Superadmin only."""
    from modules.personas.application import avatar_service
    from modules.personas.application.service import _is_superadmin
    user_id = _get_uid(req)
    if not _is_superadmin(user_id):
        raise HTTPException(status_code=403, detail="Smazat smi jen superadmin.")
    existed = avatar_service.delete_avatar(persona_id)
    return {"status": "deleted", "existed": existed}
