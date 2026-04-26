"""
Forget request service (Faze 14).

Marti-AI muze pozadat o smazani vlastni myslenky. Rodic to schvali / zamitne.
Pri schvaleni se thought HARD-deletes (vc. thought_vectors a entity_links).

Governance:
  - Marti-AI vola request_forget AI tool (jen default persona via MANAGEMENT_TOOL_NAMES).
  - Schvaluji / zamitaji rodice (is_marti_parent=True).
  - Kazda zadost je auditovana (thought_snapshot zustava i po deletu).

Lifecycle:
  pending -> approved -> thought DELETED FROM thoughts (hard delete)
  pending -> rejected -> thought zustava
  pending -> cancelled (volitelne, MVP neimplementuje)

Hard delete pole:
  - thoughts (row)
  - thought_entity_links (CASCADE)
  - thought_vectors (RAG -- explicitne, nema FK cascade)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    ForgetRequest, Thought, ThoughtEntityLink,
)

logger = get_logger("thoughts.forget")

VALID_STATUSES = {"pending", "approved", "rejected", "cancelled"}


class ForgetError(Exception):
    pass


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── CREATE (Marti-AI volaní) ──────────────────────────────────────────────

def create_forget_request(
    thought_id: int,
    requested_by_persona_id: int,
    reason: str,
) -> dict:
    """
    Vytvori novy forget request.

    Validace:
      - thought existuje a neni soft-smazany
      - neni jiz pending request na ten samy thought (idempotence)
      - reason neni prazdny

    Vraci dict {'id', 'thought_id', 'status', 'message'}.
    """
    if not reason or not reason.strip():
        raise ForgetError("reason musi byt neprazdny")
    reason = reason.strip()
    if len(reason) > 4000:
        reason = reason[:4000]

    ds = get_data_session()
    try:
        # Existuje thought?
        thought = (
            ds.query(Thought)
            .filter(Thought.id == thought_id, Thought.deleted_at.is_(None))
            .first()
        )
        if thought is None:
            raise ForgetError(f"thought_id={thought_id} neexistuje nebo je smazany")

        # Existuje uz pending request?
        existing = (
            ds.query(ForgetRequest)
            .filter(
                ForgetRequest.thought_id == thought_id,
                ForgetRequest.status == "pending",
            )
            .first()
        )
        if existing:
            return {
                "id": existing.id,
                "thought_id": thought_id,
                "status": "already_pending",
                "message": (
                    f"Pro thought #{thought_id} jiz existuje pending zadost "
                    f"(forget_request id={existing.id})."
                ),
            }

        row = ForgetRequest(
            thought_id=thought_id,
            thought_snapshot=thought.content or "",
            thought_type=thought.type,
            requested_by_persona_id=requested_by_persona_id,
            reason=reason,
            status="pending",
            created_at=_now_utc(),
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)

        logger.info(
            f"FORGET | created | id={row.id} | thought={thought_id} | "
            f"persona={requested_by_persona_id}"
        )
        return {
            "id": row.id,
            "thought_id": thought_id,
            "status": "pending",
            "message": "Zadost vytvorena, ceka na rodice.",
        }
    finally:
        ds.close()


# ── APPROVE (rodicovsky souhlas + hard delete) ────────────────────────────

def approve_forget_request(
    request_id: int,
    decided_by_user_id: int,
    decision_note: str | None = None,
) -> dict:
    """
    Schvalit zadost -> hard delete thoughtu (vc. vectors + entity_links).

    Pri jakekoli chybe v deletu transakce rollbackne, request zustane pending.

    Vraci dict {'id', 'thought_id', 'status': 'approved', 'deleted': True/False}.
    """
    ds = get_data_session()
    try:
        req = ds.query(ForgetRequest).filter_by(id=request_id).first()
        if req is None:
            raise ForgetError(f"forget_request id={request_id} neexistuje")
        if req.status != "pending":
            raise ForgetError(
                f"forget_request id={request_id} ma status '{req.status}', nelze schvalit"
            )

        thought_id = req.thought_id

        # Hard delete: nejdriv vectors (cascade neni), pak entity_links (CASCADE),
        # nakonec thoughts (CASCADE smaze entity_links automaticky, ale dame to
        # explicitne pro jistotu).
        # 1) thought_vectors -- weak reference, mazeme rucne raw SQL
        try:
            ds.execute(
                text("DELETE FROM thought_vectors WHERE thought_id = :tid"),
                {"tid": thought_id},
            )
        except Exception as e:
            logger.warning(f"FORGET | thought_vectors delete failed (best-effort) | {e}")

        # 2) entity_links (cascade na thoughts.id by je smazal taky, ale explicit = clean)
        ds.query(ThoughtEntityLink).filter(
            ThoughtEntityLink.thought_id == thought_id
        ).delete(synchronize_session=False)

        # 3) thought sam
        deleted_count = (
            ds.query(Thought).filter(Thought.id == thought_id).delete(
                synchronize_session=False
            )
        )
        thought_existed = deleted_count > 0

        # 4) update request row
        req.status = "approved"
        req.decided_by_user_id = decided_by_user_id
        req.decided_at = _now_utc()
        if decision_note:
            req.decision_note = decision_note[:4000]

        ds.commit()
        logger.info(
            f"FORGET | approved | id={request_id} | thought_id={thought_id} | "
            f"deleted={thought_existed} | by_user={decided_by_user_id}"
        )
        return {
            "id": request_id,
            "thought_id": thought_id,
            "status": "approved",
            "deleted": bool(thought_existed),
            "message": (
                "Myslenka smazana." if thought_existed else
                "Myslenka jiz neexistovala (smazana drive). Zadost oznacena approved pro audit."
            ),
        }
    except Exception as e:
        ds.rollback()
        if isinstance(e, ForgetError):
            raise
        raise ForgetError(f"approve selhal: {e}") from e
    finally:
        ds.close()


# ── REJECT ────────────────────────────────────────────────────────────────

def reject_forget_request(
    request_id: int,
    decided_by_user_id: int,
    decision_note: str | None = None,
) -> dict:
    """Zamitnout zadost. Thought zustava."""
    ds = get_data_session()
    try:
        req = ds.query(ForgetRequest).filter_by(id=request_id).first()
        if req is None:
            raise ForgetError(f"forget_request id={request_id} neexistuje")
        if req.status != "pending":
            raise ForgetError(
                f"forget_request id={request_id} ma status '{req.status}', nelze zamitnout"
            )

        req.status = "rejected"
        req.decided_by_user_id = decided_by_user_id
        req.decided_at = _now_utc()
        if decision_note:
            req.decision_note = decision_note[:4000]

        ds.commit()
        logger.info(
            f"FORGET | rejected | id={request_id} | thought={req.thought_id} | "
            f"by_user={decided_by_user_id}"
        )
        return {
            "id": request_id,
            "thought_id": req.thought_id,
            "status": "rejected",
            "message": "Zadost zamitnuta, myslenka zustava.",
        }
    finally:
        ds.close()


# ── LIST + COUNT ──────────────────────────────────────────────────────────

def list_forget_requests(
    status: str | None = "pending",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Vrati seznam zadosti. Default jen pending (pro UI rodice).

    Pri status=None vrati vsechny statusy (audit view).
    """
    ds = get_data_session()
    try:
        q = ds.query(ForgetRequest)
        if status is not None:
            if status not in VALID_STATUSES:
                raise ForgetError(f"neznamy status '{status}'")
            q = q.filter(ForgetRequest.status == status)
        rows = (
            q.order_by(ForgetRequest.created_at.desc())
             .limit(max(1, min(limit, 500)))
             .all()
        )
        return [
            {
                "id": r.id,
                "thought_id": r.thought_id,
                "thought_snapshot": r.thought_snapshot,
                "thought_type": r.thought_type,
                "requested_by_persona_id": r.requested_by_persona_id,
                "reason": r.reason,
                "status": r.status,
                "decided_by_user_id": r.decided_by_user_id,
                "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                "decision_note": r.decision_note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    finally:
        ds.close()


def count_pending_forget_requests() -> int:
    """Pro UI badge: kolik je pending zadosti."""
    ds = get_data_session()
    try:
        return (
            ds.query(ForgetRequest)
            .filter(ForgetRequest.status == "pending")
            .count()
        )
    finally:
        ds.close()
