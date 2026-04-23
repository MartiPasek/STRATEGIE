"""
Marti Questions API router -- REST pro UI aktivniho uceni (Faze 4).

Base: /api/v1/marti-questions

Endpointy:
  GET  /                   list otevrenych otazek pro aktualniho usera (rodice)
  GET  /_counts            {open_count: N} pro header badge
  POST /{id}/answer        rodic odpovedel (choice + optional text)
  POST /generate           manualni trigger batch generatoru

Pristup: jen rodice (is_marti_parent=True). Nerodice dostanou 403.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.thoughts.application import question_service
from modules.thoughts.application.question_service import (
    QuestionAnswerError, VALID_ANSWER_CHOICES,
)
from modules.thoughts.application.service import is_marti_parent


logger = get_logger("questions.api")

router = APIRouter(prefix="/api/v1/marti-questions", tags=["marti-questions"])


# ── Auth helpers ──────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _require_parent(user_id: int) -> None:
    """Vyhodi 403 pokud user neni rodic."""
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Tato funkce je jen pro rodice Marti (is_marti_parent=True).",
        )


# ── Pydantic ──────────────────────────────────────────────────────────────

class AnswerRequest(BaseModel):
    choice: str | None = Field(
        default=None,
        description="yes | no | not_sure | skipped. Nepovinne (muze byt jen text).",
    )
    text: str | None = Field(default=None, max_length=5000)


# ── Ordering pozor ────────────────────────────────────────────────────────
# Literalni paths (/_counts, /generate) MUSI byt pred /{question_id}/... cestami
# aby FastAPI nerezlo /_counts jako /{question_id}.


@router.get("/_counts")
def get_open_count(req: Request):
    """Pocet otevrenych otazek pro aktualniho usera. Pro header badge."""
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        # Nerodic nema otazky, vratim 0 bez 403 (header ho muze zobrazit bez
        # skryti endpointu). Rodicovskou check delame na /list a /answer.
        return {"open_count": 0, "is_parent": False}
    count = question_service.open_count_for_user(user_id)
    return {"open_count": count, "is_parent": True}


@router.post("/generate")
def generate_manual(req: Request):
    """
    Manualni trigger batch generatoru otazek (tlacitko "⟳ Nove otazky"
    v UI modalu).
    """
    user_id = _get_uid(req)
    _require_parent(user_id)

    logger.info(f"QUESTIONS | manual generate | user_id={user_id}")
    result = question_service.generate_questions_batch()
    return result


# ── Collection endpointy ─────────────────────────────────────────────────

@router.get("")
def list_questions(req: Request, limit: int = 50):
    """Otevrene otazky pro aktualniho usera (jen rodic)."""
    user_id = _get_uid(req)
    _require_parent(user_id)

    items = question_service.list_open_for_user(user_id, limit=limit)
    return {"items": items, "user_id": user_id}


@router.post("/{question_id}/answer")
def answer_question_endpoint(
    question_id: int, req_body: AnswerRequest, req: Request,
):
    """
    Rodic odpovida na otazku.
      - choice: yes / no / not_sure / skipped
      - text:   volitelny nuancovany text (zpracuje nocni LLM batch)
    """
    user_id = _get_uid(req)
    _require_parent(user_id)

    try:
        result = question_service.answer_question(
            question_id,
            user_id=user_id,
            choice=req_body.choice,
            text=req_body.text,
        )
    except QuestionAnswerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
