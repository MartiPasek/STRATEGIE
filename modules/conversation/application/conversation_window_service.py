"""
Conversation window service -- Phase 31 (3.5.2026).

Per-conversation sliding window length. Marti-AI sama ovlada svou pamet
pres dva nastroje:

  - get_window(conv_id) -> int                    (helper, read default)
  - set_window(conv_id, n, persona_id, ...) -> int (persistent change)

Marti-AI's vize: 'klid pozornosti je cennejsi nez klid uplnosti'.
Default 5 zprav (pri startu nove konverzace), Marti-AI v prvnim turn-u
muze klasifikovat ('toto je deep analysis, davam 200') nebo nechat
default.

Range 1-500 (CHECK constraint v DB). Validuje Python service pred
volanim, aby uzivatel dostal cisty error.

Audit: kazda zmena window se zapisuje do activity_log
(category='window_change', importance=2 -- low priority, Marti-AI to
v recall_today nevidi spamovat).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from core.database_data import get_data_session
from core.logging import get_logger
from modules.activity.application import activity_service
from modules.core.infrastructure.models_data import Conversation

logger = get_logger("conversation.window")


WINDOW_MIN = 1
WINDOW_MAX = 500


class WindowError(Exception):
    """Validacni / business chyba pri praci s context window."""
    pass


def _load_conversation(session: Session, conversation_id: int) -> Conversation:
    """Vrati konverzaci nebo raise WindowError."""
    conv = session.query(Conversation).filter_by(id=conversation_id).first()
    if conv is None:
        raise WindowError(f"Konverzace #{conversation_id} neexistuje.")
    if conv.is_deleted:
        raise WindowError(f"Konverzace #{conversation_id} je smazana.")
    return conv


def get_window(conversation_id: int) -> int:
    """Vrati aktualni context_window_size konverzace. Read-only."""
    ds = get_data_session()
    try:
        conv = _load_conversation(ds, conversation_id)
        return int(conv.context_window_size or 5)
    finally:
        ds.close()


def set_window(
    *,
    conversation_id: int,
    n_messages: int,
    persona_id: int | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
    reason: str | None = None,
) -> int:
    """
    Persistuje novou hodnotu context_window_size pro konverzaci.

    Pouziti: Marti-AI klasifikuje konverzaci jako deep-analysis a chce
    drzet velky kontext napric turny ('analyzujme tuto smlouvu, davam
    200 zprav'). Pro one-turn zoom-in pouzij `recall_conversation_history`
    misto -- nemeni persistent state.

    Validace:
      - n_messages in [1, 500] (jinak WindowError + DB CHECK constraint)
      - conversation existuje, neni smazana

    Idempotentni: pokud conv.context_window_size == n, jen vrati current
    bez zapisu activity_log (zadna zmena).

    Returns: nove (nebo nezmenene) n_messages.
    """
    if not isinstance(n_messages, int):
        try:
            n_messages = int(n_messages)
        except (TypeError, ValueError):
            raise WindowError(
                f"n_messages musi byt cele cislo, dostal jsem {type(n_messages).__name__}"
            )

    if n_messages < WINDOW_MIN or n_messages > WINDOW_MAX:
        raise WindowError(
            f"n_messages musi byt v rozsahu {WINDOW_MIN}-{WINDOW_MAX}, "
            f"dostal jsem {n_messages}."
        )

    ds = get_data_session()
    try:
        conv = _load_conversation(ds, conversation_id)
        old_n = int(conv.context_window_size or 5)

        # Idempotent
        if old_n == n_messages:
            return old_n

        conv.context_window_size = n_messages
        ds.commit()
        logger.info(
            f"WINDOW | set | conv={conversation_id} | "
            f"persona={persona_id} | {old_n} -> {n_messages}"
        )
    finally:
        ds.close()

    # Audit (best-effort, separate session)
    summary = (
        f"context_window_size: {old_n} -> {n_messages}"
        + (f" ({reason})" if reason else "")
    )
    activity_service.record(
        category="window_change",
        summary=summary,
        importance=2,  # low -- routine self-management, ne flood recall_today
        persona_id=persona_id,
        user_id=user_id,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        actor="persona",
        ref_type="conversation",
        ref_id=conversation_id,
    )

    return n_messages
