from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.memory.api.schemas import SaveMemoryRequest, SaveMemoryResponse, MemoryListResponse
from modules.memory.application.service import save_memory, get_memories

logger = get_logger("memory.api")

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.post("/", response_model=SaveMemoryResponse)
def save(request: SaveMemoryRequest, req: Request) -> SaveMemoryResponse:
    """Ruční uložení paměti."""
    user_id_str = req.cookies.get("user_id")
    user_id = int(user_id_str) if user_id_str else None

    memory_id = save_memory(
        content=request.content,
        user_id=user_id,
        project_id=request.project_id,
    )
    return SaveMemoryResponse(id=memory_id, content=request.content)


@router.get("/", response_model=MemoryListResponse)
def list_memories(req: Request) -> MemoryListResponse:
    """Načte paměti přihlášeného uživatele."""
    user_id_str = req.cookies.get("user_id")
    user_id = int(user_id_str) if user_id_str else None

    memories = get_memories(user_id=user_id)
    return MemoryListResponse(memories=memories)
