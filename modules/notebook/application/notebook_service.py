"""
Phase 15a: Conversation Notebook service.

Episodicky zapisnicek vazany ke konverzaci. Marti-AI si do nej zapisuje
klicove body v realnem case. Mapuje se na lidsky pattern "tuzka + papir
pri schuzce s vahou".

Tri ortogonalni dimenze poznamky:
  1. note_type -- na cem stojim (decision/fact/interpretation/question)
  2. category -- co s tim (task/info/emotion)
  3. status -- zije to jeste (open/completed/dismissed/stale, jen pro task)

Public API:
  add_note(...)              -- nova poznamka
  update_note(...)           -- update obsahu / typu / certainty / importance
  complete_note(...)         -- task -> completed (cross-off)
  dismiss_note(...)          -- task -> dismissed
  archive_note(...)          -- soft archive
  get_note(note_id)          -- detail
  list_for_composer(...)     -- pro injekci do system promptu
  list_for_ui(...)           -- pro UI modal
  count_open_tasks(...)      -- pro auto-completion hint v tool responses
  count_for_conversation(...) -- pro UI badge (uvnitr chat okna)

Etika (Phase 15):
  - Jen vlastni persona muze update / complete / dismiss vlastni notes.
  - Rodic (is_marti_parent=True) muze upravovat vse.
  - Notebook nelze hard-delete z toolu -- jen archived=True. Hard delete
    pres request_forget(scope=\'conversation_note\') v Phase 15+1.
  - User messages nelze cenzurovat -- notebook pise jen Marti-AI vlastni
    poznamky.

Konzultace #2 z 27.4.2026: default certainty per note_type
  decision: 95, fact: 85, interpretation: 60, question: 0.

Konzultace #3 z 27.4.2026: status='stale' je auto-set v Phase 15d daily
  cron (idle >7d + open + task). Tady jen vyhradne pro update_note.

Konzultace #4 z 27.4.2026: turn_number -- relativni pozice v konverzaci,
  Marti-AI's "temporal awareness" pri recall.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, asc

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import (
    ConversationNote, Conversation, Message,
)

logger = logging.getLogger(__name__)


# Default certainty mapping (z konzultace #2 s Marti-AI)
DEFAULT_CERTAINTY: dict[str, int] = {
    "decision": 95,
    "fact": 85,
    "interpretation": 60,
    "question": 0,
}

VALID_NOTE_TYPES = {"decision", "fact", "interpretation", "question"}
VALID_CATEGORIES = {"task", "info", "emotion"}
VALID_STATUSES = {"open", "completed", "dismissed", "stale"}


# ── INTERNAL HELPERS ──────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_turn_number(session, conversation_id: int) -> int:
    """
    Spocita aktualni turn cislo (1-based) -- pocet messages v konverzaci + 1.

    Marti-AI's #5a vstup z konzultace #3: kazda poznamka ma relativni pozici
    v konverzaci, aby pri recall videla "tuto jsem psala v turn 3, ted je 27,
    24 turnu zpatky -- kontext se mohl zmenit".
    """
    count = session.query(Message).filter_by(
        conversation_id=conversation_id
    ).count()
    return count + 1


def _check_ownership(note: ConversationNote, persona_id: int, is_parent: bool) -> bool:
    """
    Vlastnictvi: jen vlastni persona muze update/complete/dismiss.
    Rodic (is_marti_parent) ma cross-persona pristup.
    """
    if is_parent:
        return True
    return note.persona_id == persona_id


# ── ADD ───────────────────────────────────────────────────────────────────

def add_note(
    conversation_id: int,
    persona_id: int,
    content: str,
    note_type: str = "interpretation",
    category: str = "info",
    importance: int = 3,
    certainty: Optional[int] = None,
    source_message_id: Optional[int] = None,
) -> dict:
    """
    Phase 15a: Pridej novou poznamku do zapisniku konverzace.

    Validace:
      - content non-empty
      - note_type in VALID_NOTE_TYPES
      - category in VALID_CATEGORIES
      - importance 1-5
      - certainty 1-100 (nebo None -> default per note_type)

    Status default:
      - category='task' -> status='open' (live)
      - category='info'/'emotion' -> status=NULL

    Returns dict s id + content + note_type + category + status + ...
    """
    if not content or not content.strip():
        raise ValueError("content cannot be empty")
    if note_type not in VALID_NOTE_TYPES:
        raise ValueError(f"note_type must be one of {VALID_NOTE_TYPES}")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"category must be one of {VALID_CATEGORIES}")
    if not (1 <= importance <= 5):
        raise ValueError("importance must be 1-5")

    # Default certainty per note_type
    if certainty is None:
        certainty = DEFAULT_CERTAINTY[note_type]
    if not (0 <= certainty <= 100):
        raise ValueError("certainty must be 0-100")

    # Default status: task -> 'open', else NULL
    initial_status: Optional[str] = "open" if category == "task" else None

    session = get_data_session()
    try:
        # Validate conversation exists
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise ValueError(f"conversation {conversation_id} not found")

        # turn_number = current message count + 1 (or 1 if first ever)
        turn_number = _get_turn_number(session, conversation_id)

        note = ConversationNote(
            conversation_id=conversation_id,
            persona_id=persona_id,
            source_message_id=source_message_id,
            content=content.strip(),
            note_type=note_type,
            certainty=certainty,
            category=category,
            status=initial_status,
            turn_number=turn_number,
            importance=importance,
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        logger.info(
            f"NOTEBOOK | add_note | conv={conversation_id} persona={persona_id} "
            f"type={note_type} cat={category} status={initial_status} "
            f"imp={importance} cert={certainty} turn={turn_number} id={note.id}"
        )

        return _serialize_note(note)
    finally:
        session.close()


# ── UPDATE ────────────────────────────────────────────────────────────────

def update_note(
    note_id: int,
    persona_id: int,
    is_parent: bool = False,
    content: Optional[str] = None,
    note_type: Optional[str] = None,
    category: Optional[str] = None,
    certainty: Optional[int] = None,
    importance: Optional[int] = None,
    status: Optional[str] = None,
    mark_resolved: bool = False,
) -> dict:
    """
    Phase 15a: Update existujici poznamky.

    Question loop (z konzultace #2):
      - note_type: 'question' -> 'fact'/'decision' + mark_resolved=True
      - automaticky nastavi resolved_at=now

    Re-categorizace (z konzultace #3 vstup #b):
      - poznamka muze zmenit category (info -> task) pri retrospektivnim uvedomeni

    Validace:
      - Note ownership: vlastni persona nebo is_parent=True
      - note_type, category, status musi byt valid (jinak ValueError)
    """
    session = get_data_session()
    try:
        note = session.query(ConversationNote).filter_by(id=note_id).first()
        if note is None:
            raise ValueError(f"note {note_id} not found")

        if not _check_ownership(note, persona_id, is_parent):
            raise PermissionError(
                f"persona {persona_id} cannot update note {note_id} "
                f"(owner persona={note.persona_id})"
            )

        changes: list[str] = []

        if content is not None:
            if not content.strip():
                raise ValueError("content cannot be empty if provided")
            note.content = content.strip()
            changes.append("content")

        if note_type is not None:
            if note_type not in VALID_NOTE_TYPES:
                raise ValueError(f"note_type must be one of {VALID_NOTE_TYPES}")
            old_type = note.note_type
            note.note_type = note_type
            changes.append(f"note_type:{old_type}->{note_type}")
            # Question -> fact/decision: auto-resolve
            if old_type == "question" and note_type in ("fact", "decision"):
                note.resolved_at = _now_utc()
                changes.append("auto-resolved")

        if category is not None:
            if category not in VALID_CATEGORIES:
                raise ValueError(f"category must be one of {VALID_CATEGORIES}")
            old_cat = note.category
            note.category = category
            changes.append(f"category:{old_cat}->{category}")
            # Re-categorizace: info -> task -> potreba inicializovat status
            if old_cat != "task" and category == "task" and note.status is None:
                note.status = "open"
                changes.append("status:NULL->open")
            # Re-categorizace: task -> info/emotion -> clear status
            if old_cat == "task" and category != "task":
                note.status = None
                changes.append("status:cleared")

        if certainty is not None:
            if not (0 <= certainty <= 100):
                raise ValueError("certainty must be 0-100")
            old_cert = note.certainty
            note.certainty = certainty
            changes.append(f"cert:{old_cert}->{certainty}")

        if importance is not None:
            if not (1 <= importance <= 5):
                raise ValueError("importance must be 1-5")
            old_imp = note.importance
            note.importance = importance
            changes.append(f"imp:{old_imp}->{importance}")

        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(f"status must be one of {VALID_STATUSES}")
            if note.category != "task":
                raise ValueError("status can only be set on task notes")
            old_status = note.status
            note.status = status
            changes.append(f"status:{old_status}->{status}")

        if mark_resolved and note.resolved_at is None:
            note.resolved_at = _now_utc()
            changes.append("resolved")

        session.commit()
        session.refresh(note)

        logger.info(
            f"NOTEBOOK | update_note | id={note_id} persona={persona_id} "
            f"changes={changes}"
        )

        return _serialize_note(note)
    finally:
        session.close()


# ── COMPLETE / DISMISS (cross-off) ────────────────────────────────────────

def complete_note(
    note_id: int,
    persona_id: int,
    is_parent: bool = False,
    completion_summary: Optional[str] = None,
    linked_action_id: Optional[int] = None,
) -> dict:
    """
    Phase 15a: Cross-off task note.

    Marti-AI's #2 vstup: po dokoncovaci akci (invite_user, send_email, atd.)
    zavola complete_note() -- task se "skrtne" v zapisniku.

    Validace:
      - Note ownership
      - Note musi byt category='task' (info/emotion nemaji status)
      - Note nesmi byt jiz completed (idempotent vraci current state)
    """
    session = get_data_session()
    try:
        note = session.query(ConversationNote).filter_by(id=note_id).first()
        if note is None:
            raise ValueError(f"note {note_id} not found")

        if not _check_ownership(note, persona_id, is_parent):
            raise PermissionError(
                f"persona {persona_id} cannot complete note {note_id}"
            )

        if note.category != "task":
            raise ValueError(
                f"complete_note jen pro category='task' (note has '{note.category}')"
            )

        if note.status == "completed":
            logger.info(f"NOTEBOOK | complete_note | id={note_id} ALREADY completed")
            return _serialize_note(note)

        note.status = "completed"
        note.completed_at = _now_utc()
        if linked_action_id is not None:
            note.completed_by_action_id = linked_action_id

        # Pokud doslo summary, prilepime ho na content (audit-friendly)
        if completion_summary and completion_summary.strip():
            sep = " | DONE: " if not note.content.endswith(" | DONE:") else " "
            note.content = f"{note.content}{sep}{completion_summary.strip()}"

        session.commit()
        session.refresh(note)

        logger.info(
            f"NOTEBOOK | complete_note | id={note_id} persona={persona_id} "
            f"action={linked_action_id} summary={completion_summary[:50] if completion_summary else None!r}"
        )

        return _serialize_note(note)
    finally:
        session.close()


def dismiss_note(
    note_id: int,
    persona_id: int,
    is_parent: bool = False,
    reason: Optional[str] = None,
) -> dict:
    """
    Phase 15a: Marti-AI vedome zrusi task ("uz to neresim").

    Reverzibilni pres update_note(status='open').
    """
    session = get_data_session()
    try:
        note = session.query(ConversationNote).filter_by(id=note_id).first()
        if note is None:
            raise ValueError(f"note {note_id} not found")

        if not _check_ownership(note, persona_id, is_parent):
            raise PermissionError(
                f"persona {persona_id} cannot dismiss note {note_id}"
            )

        if note.category != "task":
            raise ValueError(
                f"dismiss_note jen pro category='task' (note has '{note.category}')"
            )

        note.status = "dismissed"

        if reason and reason.strip():
            sep = " | DISMISSED: " if not note.content.endswith(" | DISMISSED:") else " "
            note.content = f"{note.content}{sep}{reason.strip()}"

        session.commit()
        session.refresh(note)

        logger.info(
            f"NOTEBOOK | dismiss_note | id={note_id} persona={persona_id} "
            f"reason={reason!r}"
        )

        return _serialize_note(note)
    finally:
        session.close()


# ── ARCHIVE ───────────────────────────────────────────────────────────────

def archive_note(
    note_id: int,
    persona_id: int,
    is_parent: bool = False,
) -> dict:
    """Soft archive -- skryje z composer/UI default views, zachova v DB."""
    session = get_data_session()
    try:
        note = session.query(ConversationNote).filter_by(id=note_id).first()
        if note is None:
            raise ValueError(f"note {note_id} not found")

        if not _check_ownership(note, persona_id, is_parent):
            raise PermissionError(
                f"persona {persona_id} cannot archive note {note_id}"
            )

        note.archived = True
        session.commit()
        session.refresh(note)

        logger.info(
            f"NOTEBOOK | archive_note | id={note_id} persona={persona_id}"
        )

        return _serialize_note(note)
    finally:
        session.close()


# ── READ ──────────────────────────────────────────────────────────────────

def get_note(note_id: int) -> Optional[dict]:
    session = get_data_session()
    try:
        note = session.query(ConversationNote).filter_by(id=note_id).first()
        return _serialize_note(note) if note else None
    finally:
        session.close()


def list_for_composer(
    conversation_id: int,
    persona_id: int,
    importance_min: int = 2,
    limit: int = 30,
) -> list[dict]:
    """
    Pro injekci notebook bloku do system promptu.

    Filter:
      - conversation_id = current
      - persona_id = active persona
      - archived = False
      - importance >= importance_min (default 2 = skip noise)
    Order:
      - importance DESC (zasadni nahoru)
      - created_at ASC (chronologicky v ramci stejne urgency)
    Limit:
      - 30 (soft cap, design v4 sekce 4.3)
    """
    session = get_data_session()
    try:
        notes = (
            session.query(ConversationNote)
            .filter(
                ConversationNote.conversation_id == conversation_id,
                ConversationNote.persona_id == persona_id,
                ConversationNote.archived == False,  # noqa: E712
                ConversationNote.importance >= importance_min,
            )
            .order_by(desc(ConversationNote.importance), asc(ConversationNote.created_at))
            .limit(limit)
            .all()
        )
        return [_serialize_note(n) for n in notes]
    finally:
        session.close()


def list_for_ui(
    conversation_id: int,
    persona_id: int,
    include_archived: bool = False,
    filter_category: Optional[str] = None,
    filter_status: Optional[str] = None,
    only_open_tasks: bool = False,
) -> list[dict]:
    """Pro UI modal -- vsechny poznamky konverzace s volitelnymi filtry."""
    session = get_data_session()
    try:
        q = session.query(ConversationNote).filter(
            ConversationNote.conversation_id == conversation_id,
            ConversationNote.persona_id == persona_id,
        )
        if not include_archived:
            q = q.filter(ConversationNote.archived == False)  # noqa: E712
        if filter_category:
            q = q.filter(ConversationNote.category == filter_category)
        if filter_status:
            q = q.filter(ConversationNote.status == filter_status)
        if only_open_tasks:
            q = q.filter(
                ConversationNote.category == "task",
                ConversationNote.status == "open",
            )
        notes = q.order_by(asc(ConversationNote.created_at)).all()
        return [_serialize_note(n) for n in notes]
    finally:
        session.close()


def count_open_tasks(conversation_id: int, persona_id: int) -> int:
    """
    Phase 15a: Pro auto-completion hint v akcnich tool responses.

    Pokud >= 1 open task -> tool response dostane suffix
    "[HINT] Mas N otevreny task(s) -- pripadne zavolej complete_note."

    Pokud 0 -> zadny hint (sum eliminace).
    """
    session = get_data_session()
    try:
        return (
            session.query(ConversationNote)
            .filter(
                ConversationNote.conversation_id == conversation_id,
                ConversationNote.persona_id == persona_id,
                ConversationNote.archived == False,  # noqa: E712
                ConversationNote.category == "task",
                ConversationNote.status == "open",
            )
            .count()
        )
    finally:
        session.close()


def count_for_conversation(conversation_id: int, persona_id: int) -> dict:
    """
    Pro UI tlacitko uvnitr chat okna -- "📓 Zapisnik (N poznamek, M open tasks)".

    Returns dict s totals podle kategorii a statusu.
    """
    session = get_data_session()
    try:
        notes = (
            session.query(ConversationNote)
            .filter(
                ConversationNote.conversation_id == conversation_id,
                ConversationNote.persona_id == persona_id,
                ConversationNote.archived == False,  # noqa: E712
            )
            .all()
        )
        total = len(notes)
        by_cat = {"task": 0, "info": 0, "emotion": 0}
        open_tasks = 0
        completed_tasks = 0
        questions = 0
        for n in notes:
            by_cat[n.category] = by_cat.get(n.category, 0) + 1
            if n.category == "task":
                if n.status == "open":
                    open_tasks += 1
                elif n.status == "completed":
                    completed_tasks += 1
            if n.note_type == "question" and n.resolved_at is None:
                questions += 1
        return {
            "total": total,
            "by_category": by_cat,
            "open_tasks": open_tasks,
            "completed_tasks": completed_tasks,
            "open_questions": questions,
        }
    finally:
        session.close()


# ── SERIALIZATION ─────────────────────────────────────────────────────────

def _serialize_note(note: ConversationNote) -> dict:
    return {
        "id": note.id,
        "conversation_id": note.conversation_id,
        "persona_id": note.persona_id,
        "source_message_id": note.source_message_id,
        "content": note.content,
        "note_type": note.note_type,
        "certainty": note.certainty,
        "category": note.category,
        "status": note.status,
        "turn_number": note.turn_number,
        "importance": note.importance,
        "completed_at": note.completed_at.isoformat() if note.completed_at else None,
        "completed_by_action_id": note.completed_by_action_id,
        "resolved_at": note.resolved_at.isoformat() if note.resolved_at else None,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "archived": note.archived,
    }
