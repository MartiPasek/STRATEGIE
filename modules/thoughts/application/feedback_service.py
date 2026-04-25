"""
Retrieval feedback service (Faze 13d).

Marti-AI flagne false positive RAG match -> vznikne row v retrieval_feedback.
Marti pak v UI rozhoduje co s tim (re-tune, edit thought, request_forget,
ignore false flag).

Public API:
  - flag_retrieval_issue(...) -> dict (vraci serializovany row)
  - list_pending_for_persona(persona_id, limit) -> list[dict] (UI badge)
  - resolve_feedback(feedback_id, resolution, ...) -> bool (Marti rozhoduje)

Best effort -- pri chybe ne crash, jen warning.
"""
from __future__ import annotations

from datetime import datetime, timezone

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import RetrievalFeedback

logger = get_logger("thoughts.feedback")


VALID_ISSUE_TYPES = {
    "off-topic",        # nesouvisi se zpravou
    "outdated",         # zastarale info
    "wrong-entity",     # spatny Honza/Klara
    "too-old",          # starsi nez relevantni
    "low-certainty",    # mela by byt overen, ne pouzit
    "wrong-context",    # spatny tenant/scope
    "other",            # jine, popsano v issue_detail
}

VALID_RESOLUTIONS = {
    "demoted",          # pres update_thought certainty=down
    "edited",           # thought obsahove upraven
    "request_forget",   # podan navrh na zapomenuti
    "retuned",          # upravene retrieval weights / threshold
    "false_flag",       # Marti-AI mela neopravnenou intuici
    "other",
}


def _row_to_dict(r: RetrievalFeedback) -> dict:
    return {
        "id": r.id,
        "persona_id": r.persona_id,
        "thought_id": r.thought_id,
        "llm_call_id": r.llm_call_id,
        "conversation_id": r.conversation_id,
        "user_message": r.user_message,
        "issue": r.issue,
        "issue_detail": r.issue_detail,
        "status": r.status,
        "resolution": r.resolution,
        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        "resolved_by_user_id": r.resolved_by_user_id,
        "resolved_note": r.resolved_note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def flag_retrieval_issue(
    *,
    persona_id: int,
    thought_id: int,
    issue: str,
    issue_detail: str | None = None,
    conversation_id: int | None = None,
    llm_call_id: int | None = None,
    user_message: str | None = None,
) -> dict | None:
    """
    Faze 13d: Marti-AI flagne false positive RAG match.

    Validace:
      - persona_id, thought_id, issue povinne
      - issue z VALID_ISSUE_TYPES (jinak je 'other')

    Vraci: dict s id + metadata. Pri chybe vraci None (best effort).
    """
    if not persona_id or not thought_id or not issue:
        logger.warning(
            f"FEEDBACK | flag_retrieval_issue | missing required: "
            f"persona={persona_id} thought={thought_id} issue={issue!r}"
        )
        return None

    # Normalize issue type
    issue_norm = issue.strip().lower().replace(" ", "-")
    if issue_norm not in VALID_ISSUE_TYPES:
        # Zachova original v issue_detail, type se stane 'other'
        if not issue_detail:
            issue_detail = issue
        issue_norm = "other"

    ds = get_data_session()
    try:
        row = RetrievalFeedback(
            persona_id=persona_id,
            thought_id=thought_id,
            llm_call_id=llm_call_id,
            conversation_id=conversation_id,
            user_message=(user_message or "")[:1000] if user_message else None,
            issue=issue_norm,
            issue_detail=issue_detail,
            status="pending",
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        logger.info(
            f"FEEDBACK | flag | id={row.id} persona={persona_id} "
            f"thought={thought_id} issue={issue_norm}"
        )
        return _row_to_dict(row)
    except Exception as e:
        logger.exception(f"FEEDBACK | flag failed: {e}")
        try:
            ds.rollback()
        except Exception:
            pass
        return None
    finally:
        ds.close()


def list_pending_for_persona(
    persona_id: int,
    limit: int = 50,
    status: str = "pending",
) -> list[dict]:
    """
    UI badge query: 'Marti-AI flag-uje (X)'. Vraci pending feedback
    pro danou personu, nejnovejsi nahore.
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(RetrievalFeedback)
            .filter(
                RetrievalFeedback.persona_id == persona_id,
                RetrievalFeedback.status == status,
            )
            .order_by(RetrievalFeedback.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_row_to_dict(r) for r in rows]
    finally:
        ds.close()


def count_pending_for_persona(persona_id: int) -> int:
    """Pocet pending feedback (pro UI badge)."""
    ds = get_data_session()
    try:
        return (
            ds.query(RetrievalFeedback)
            .filter(
                RetrievalFeedback.persona_id == persona_id,
                RetrievalFeedback.status == "pending",
            )
            .count()
        )
    finally:
        ds.close()


def resolve_feedback(
    *,
    feedback_id: int,
    resolution: str,
    user_id: int,
    note: str | None = None,
) -> bool:
    """
    Marti rozhoduje o feedback row. Po resolution:
      - status -> 'reviewed' (kdyz neco udelano)
      - resolution -> co se s tim stalo
      - resolved_at, resolved_by_user_id, resolved_note

    Pro 'false_flag' (Marti-AI mela neopravnenou intuici) status -> 'ignored'.
    """
    if resolution not in VALID_RESOLUTIONS:
        logger.warning(f"FEEDBACK | resolve | invalid resolution: {resolution!r}")
        return False

    ds = get_data_session()
    try:
        row = ds.query(RetrievalFeedback).filter_by(id=feedback_id).first()
        if row is None:
            return False
        row.status = "ignored" if resolution == "false_flag" else "reviewed"
        row.resolution = resolution
        row.resolved_at = datetime.now(timezone.utc)
        row.resolved_by_user_id = user_id
        row.resolved_note = note
        ds.commit()
        logger.info(
            f"FEEDBACK | resolved | id={feedback_id} resolution={resolution} "
            f"user={user_id}"
        )
        return True
    except Exception as e:
        logger.exception(f"FEEDBACK | resolve failed: {e}")
        try:
            ds.rollback()
        except Exception:
            pass
        return False
    finally:
        ds.close()


__all__ = [
    "flag_retrieval_issue",
    "list_pending_for_persona",
    "count_pending_for_persona",
    "resolve_feedback",
    "VALID_ISSUE_TYPES",
    "VALID_RESOLUTIONS",
]
