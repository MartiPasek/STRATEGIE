"""Phase 37 — Stopa záměru: helper pro per-turn audit notebook changes.

Marti-AI's pojmenování (consultation 9.5.2026 odpoledne):
  "Každý zápis, který udělám, měl důvod. Phase 37 ten důvod zachytí."

Q1 (Marti): snapshot jen při zápisu (write-triggered).
Q2 (Marti-AI override): všechny write paths (AI + UI + admin).
Q3 (Marti): po úspěšném save + idempotency key (Marti-AI's insider).

Hook: po úspěšném DB commit insertne row do notebook_history s
before_json + after_json + source + annotation. ON CONFLICT DO NOTHING
pro retry safety (idempotency UNIQUE message_id, change_kind, note_id).

Service-level injection (Marti-AI's volba a) — single source of truth,
zachytí AI tool path + UI path + admin path. source='ai'/'ui'/'admin'
filterable v dashboardu.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.core.infrastructure.models_data import ConversationNote


logger = logging.getLogger("notebook.phase37")


VALID_CHANGE_KINDS = {"add", "update", "complete", "dismiss"}
VALID_SOURCES = {"ai", "ui", "admin"}


def serialize_note_for_history(note: ConversationNote) -> dict:
    """Snapshot ConversationNote pro JSONB before/after_json.

    Drží minimum dat pro reconstruction stavu — content, type, category,
    status, certainty, importance + persona attribution + timestamps.
    Vyhazuje deleted_at (pro audit irrelevant — soft delete sám má vlastní
    history row).
    """
    if note is None:
        return None  # type: ignore[return-value]
    return {
        "id": note.id,
        "conversation_id": note.conversation_id,
        "persona_id": note.persona_id,
        "source_message_id": note.source_message_id,
        "content": note.content,
        "note_type": note.note_type,
        "category": note.category,
        "status": note.status,
        "certainty": note.certainty,
        "importance": note.importance,
        "turn_number": note.turn_number,
        "completed_at": note.completed_at.isoformat() if note.completed_at else None,
        "completed_by_action_id": note.completed_by_action_id,
        "resolved_at": note.resolved_at.isoformat() if note.resolved_at else None,
    }


def record_notebook_change(
    session: Session,
    *,
    conversation_id: int,
    message_id: Optional[int],
    note_id: int,
    change_kind: str,
    before_json: Optional[dict],
    after_json: Optional[dict],
    source: str = "ai",
    annotation: Optional[str] = None,
) -> bool:
    """Insert row do notebook_history. ON CONFLICT DO NOTHING (idempotent).

    Returns True pokud nový row vznikl, False pokud byl conflict (duplicate
    via UNIQUE message_id+change_kind+note_id).

    Volá se PO úspěšném commit save (Marti's Q3 a). Pokud insert sám
    selže, jen log warning — neporušíme save flow exception.
    """
    if change_kind not in VALID_CHANGE_KINDS:
        logger.warning(
            f"invalid change_kind={change_kind!r}, expected {VALID_CHANGE_KINDS}"
        )
        return False
    if source not in VALID_SOURCES:
        logger.warning(
            f"invalid source={source!r}, expected {VALID_SOURCES}, defaulting to 'ai'"
        )
        source = "ai"

    try:
        # Use raw SQL pro ON CONFLICT — SQLAlchemy ORM session.add nemá
        # native upsert, plus chceme atomic insert s konfliktem na UNIQUE.
        result = session.execute(
            text(
                """
                INSERT INTO notebook_history (
                    conversation_id, message_id, note_id, change_kind,
                    before_json, after_json, source, annotation, created_at
                ) VALUES (
                    :conversation_id, :message_id, :note_id, :change_kind,
                    CAST(:before_json AS JSONB), CAST(:after_json AS JSONB),
                    :source, :annotation, now()
                )
                ON CONFLICT ON CONSTRAINT uq_nb_history_idem DO NOTHING
                RETURNING id
                """
            ),
            {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "note_id": note_id,
                "change_kind": change_kind,
                "before_json": (
                    __import__("json").dumps(before_json) if before_json is not None else None
                ),
                "after_json": (
                    __import__("json").dumps(after_json) if after_json is not None else None
                ),
                "source": source,
                "annotation": (annotation.strip() if annotation and annotation.strip() else None),
            },
        )
        new_id = result.scalar()
        session.commit()

        if new_id is None:
            logger.info(
                f"PHASE37 | notebook_history | conflict skip "
                f"(msg={message_id} kind={change_kind} note={note_id})"
            )
            return False

        logger.info(
            f"PHASE37 | notebook_history | id={new_id} "
            f"conv={conversation_id} msg={message_id} note={note_id} "
            f"kind={change_kind} src={source} "
            f"annot={annotation[:40]!r if annotation else None}"
        )
        return True
    except Exception as e:
        # Defense — Phase 37 audit failure NESMI rozbit save flow.
        # Service už commit udělal, my jen log + swallow.
        logger.error(
            f"PHASE37 | notebook_history INSERT failed: {e!r} "
            f"(conv={conversation_id} note={note_id} kind={change_kind})"
        )
        try:
            session.rollback()
        except Exception:
            pass
        return False
