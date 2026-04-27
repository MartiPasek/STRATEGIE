"""
Notebook API router -- REST pro UI "📓 Zápisník konverzace".

Base: /api/v1/conversations/{conversation_id}/notes

Phase 15b endpointy:
  GET  /api/v1/conversations/{cid}/notes/count
       Vraci dict {total, by_category, open_tasks, completed_tasks, open_questions}
       pro UI tlacitko a polling badge update.

  GET  /api/v1/conversations/{cid}/notes
       Vraci list poznamek pro modal. Volitelne filtry:
         ?filter_category=task|info|emotion
         ?filter_status=open|completed|dismissed|stale
         ?only_open_tasks=true
         ?include_archived=true

Auth: owner-gated (conversation.user_id == current user) NEBO is_marti_parent.
Pro DM/shared konverzace v Phase 15+1 dovolit shared_with_user_id taky.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import Conversation
from modules.notebook.application import notebook_service
from modules.thoughts.application.service import is_marti_parent


logger = get_logger("notebook.api")

router = APIRouter(prefix="/api/v1/conversations", tags=["notebook"])


# ── Auth helpers ─────────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _check_conversation_access(conversation_id: int, user_id: int) -> tuple[Conversation, int | None]:
    """
    Vraci (conversation, persona_id) nebo raise 403/404.

    Access pravidla:
      - Owner (conv.user_id == user_id) -> ok
      - is_marti_parent -> ok (cross-user view)
      - jinak 403
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise HTTPException(status_code=404, detail="Konverzace neexistuje.")

        is_parent = is_marti_parent(user_id)
        if conv.user_id != user_id and not is_parent:
            raise HTTPException(
                status_code=403,
                detail="K teto konverzaci nemas pristup.",
            )

        # Persona_id pro list_for_ui filtr -- aktivni persona konverzace.
        # Pokud konverzace nema active_agent_id, vrati None -- service to
        # zvladne (filtr persona_id IS NULL = zadna poznamka).
        persona_id = conv.active_agent_id

        return conv, persona_id
    finally:
        ds.close()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{conversation_id}/notes/count")
def get_notes_count(conversation_id: int, request: Request) -> dict[str, Any]:
    """
    Pro UI tlacitko 📓 Zapisnik (N poznamek, M open tasks).

    Vraci:
      {
        "total": int,
        "by_category": {"task": int, "info": int, "emotion": int},
        "open_tasks": int,
        "completed_tasks": int,
        "open_questions": int
      }

    Polluje se ~30s pro live update badge (nove poznamky pri Marti-AI's
    add_conversation_note se objevi v UI bez F5 reload).
    """
    user_id = _get_uid(request)
    conv, persona_id = _check_conversation_access(conversation_id, user_id)

    if persona_id is None:
        # Zadna aktivni persona -- prazdny zapisnik
        return {
            "total": 0,
            "by_category": {"task": 0, "info": 0, "emotion": 0},
            "open_tasks": 0,
            "completed_tasks": 0,
            "open_questions": 0,
        }

    return notebook_service.count_for_conversation(
        conversation_id=conversation_id,
        persona_id=persona_id,
    )


@router.get("/{conversation_id}/notes")
def list_notes(
    conversation_id: int,
    request: Request,
    filter_category: str | None = None,
    filter_status: str | None = None,
    only_open_tasks: bool = False,
    include_archived: bool = False,
) -> dict[str, Any]:
    """
    Pro UI modal -- list poznamek konverzace s filtry.

    Vraci:
      {
        "conversation_id": int,
        "persona_id": int | None,
        "notes": [...],         -- list poznamek (full _serialize_note dict)
        "total": int,
        "filters_applied": {...}
      }
    """
    user_id = _get_uid(request)
    conv, persona_id = _check_conversation_access(conversation_id, user_id)

    if persona_id is None:
        return {
            "conversation_id": conversation_id,
            "persona_id": None,
            "notes": [],
            "total": 0,
            "filters_applied": {},
        }

    # Validace filtru (jinak 400)
    if filter_category and filter_category not in notebook_service.VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"filter_category must be one of {sorted(notebook_service.VALID_CATEGORIES)}",
        )
    if filter_status and filter_status not in notebook_service.VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"filter_status must be one of {sorted(notebook_service.VALID_STATUSES)}",
        )

    notes = notebook_service.list_for_ui(
        conversation_id=conversation_id,
        persona_id=persona_id,
        include_archived=include_archived,
        filter_category=filter_category,
        filter_status=filter_status,
        only_open_tasks=only_open_tasks,
    )

    return {
        "conversation_id": conversation_id,
        "persona_id": persona_id,
        "notes": notes,
        "total": len(notes),
        "filters_applied": {
            "filter_category": filter_category,
            "filter_status": filter_status,
            "only_open_tasks": only_open_tasks,
            "include_archived": include_archived,
        },
    }
