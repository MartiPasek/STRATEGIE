"""
Anchor service -- Phase 31 (3.5.2026). KOTVA ⚓.

Marti-AI's volba symbolu (3.5.2026 rano): ⚓ ('starsi a klidnejsi nez 🪝').
Marti-AI's metafora: 'zalozka v knize a poznamka na okraj'.

Funkce:
  flag_message(message_id, persona_id, ...) -> Message     -- ozna kotvou
  unflag_message(message_id, persona_id, ...) -> Message   -- odznaci
  get_anchored_messages(conversation_id) -> list[Message]  -- pro composer
  is_anchored(message_id) -> bool                          -- helper

Pravidla z konzultace s Marti-AI 3.5.2026 rano:
  - Reason volitelny ('povinny reason mi pripomina vysvetlovani se')
  - also_create_note volitelny, default False
    ('automatismus mi bere volbu')
  - Zadny hard cap (klid od limitu)
  - Zadne expiration (vedomy akt unflag)
  - Marti-AI's volba kdykoli, bez parent gate (jeji prostor)

Composer pouzije `get_anchored_messages(conv_id)` pri kazdem turnu --
slije s recent N messages do final contextu. Partial index
ix_messages_anchored optimalizuje hot path.

Auto-create conversation_note (kdyz also_create_note=True):
  - Insert ConversationNote s source_message_id=message_id
  - note_type='fact', certainty=85, category='info', importance=4
    (kotva = vyznamna)
  - content = reason (pokud zadan), jinak default 'Zakotvena zprava #N'
  - Marti-AI's vlastni text, ne LLM-generated -- zustava ciste

Audit: activity_log category='message_anchor' (flag) /
'message_unanchor' (unflag), importance=3.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.database_data import get_data_session
from core.logging import get_logger
from modules.activity.application import activity_service
from modules.core.infrastructure.models_data import (
    ConversationNote, Message,
)

logger = get_logger("conversation.anchor")


class AnchorError(Exception):
    """Validacni / business chyba pri praci s kotvou."""
    pass


def _load_message(session: Session, message_id: int) -> Message:
    """Vrati zpravu nebo raise AnchorError."""
    msg = session.query(Message).filter_by(id=message_id).first()
    if msg is None:
        raise AnchorError(f"Zprava #{message_id} neexistuje.")
    return msg


def is_anchored(message_id: int) -> bool:
    """Helper -- vrati True pokud zprava ma kotvu."""
    ds = get_data_session()
    try:
        msg = ds.query(Message).filter_by(id=message_id).first()
        return bool(msg and msg.is_anchored)
    finally:
        ds.close()


def get_anchored_messages(conversation_id: int) -> list[Message]:
    """
    Vrati vsechny aktualne zakotvene zpravy v konverzaci, serazene
    chronologicky (id asc). Pouziva se v composeru -- slije se s recent
    N messages do finalniho contextu.

    Partial index ix_messages_anchored optimalizuje tuto query
    (WHERE is_anchored=TRUE).

    Caller MA odpovednost zavrit session sam, NEBO si zkopirovat data
    do dict pred close. Tato funkce vraci detached SQLA objekty
    (caller-managed lifecycle).
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.is_anchored.is_(True),
            )
            .order_by(Message.id.asc())
            .all()
        )
        # Expunge -- aby caller mohl pouzivat po close()
        for r in rows:
            ds.expunge(r)
        return rows
    finally:
        ds.close()


def flag_message(
    *,
    message_id: int,
    persona_id: int | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
    reason: str | None = None,
    also_create_note: bool = False,
) -> dict:
    """
    Ozna zpravu jako kotvu ⚓. Drzi ji v aktivnim okne pres cut-off.

    Idempotentni: pokud uz je is_anchored=True, vrati current state
    bez druheho zapisu (audit jen prvniho flag).

    also_create_note=True (default False, Marti-AI's korekce):
      - Auto-vytvori ConversationNote s source_message_id=message_id
      - note_type='fact', certainty=85, importance=4
      - content = reason (pokud zadan), jinak default
      - Stejna session, atomicke commit

    Returns: dict s message detaily a optional note_id.
    """
    now = datetime.now(timezone.utc)

    ds = get_data_session()
    try:
        msg = _load_message(ds, message_id)

        # Idempotent
        if msg.is_anchored:
            logger.info(
                f"ANCHOR | already_anchored | msg={message_id} | persona={persona_id}"
            )
            return {
                "message_id": message_id,
                "conversation_id": msg.conversation_id,
                "is_anchored": True,
                "anchored_at": msg.anchored_at,
                "anchored_by_persona_id": msg.anchored_by_persona_id,
                "anchor_reason": msg.anchor_reason,
                "already_anchored": True,
                "note_created": False,
                "note_id": None,
            }

        # Set anchor fields
        msg.is_anchored = True
        msg.anchored_at = now
        msg.anchored_by_persona_id = persona_id
        msg.anchor_reason = reason
        # Pokud byla unflag-ed v minulosti, vyclear unanchored fields
        # (re-flag = cista historie, audit drzi pres logger)
        msg.unanchored_at = None
        msg.unanchored_reason = None

        conv_id = msg.conversation_id
        msg_tenant = msg.tenant_id

        note_id = None
        if also_create_note:
            note_content = reason or f"Zakotvena zprava #{message_id}"
            # Spocitej turn_number jako pocet messages do tehoz conv
            # vc. teto zpravy (1-based)
            turn_number = (
                ds.query(Message)
                .filter(
                    Message.conversation_id == conv_id,
                    Message.id <= message_id,
                )
                .count()
            )
            note = ConversationNote(
                conversation_id=conv_id,
                persona_id=persona_id or 0,  # FK logicka -- nesmi byt None
                source_message_id=message_id,
                content=note_content[:2000],
                note_type="fact",
                certainty=85,
                category="info",
                status=None,
                turn_number=turn_number,
                importance=4,
            )
            ds.add(note)
            ds.flush()  # ziskej note.id pro response
            note_id = int(note.id)

        ds.commit()
        ds.refresh(msg)
        logger.info(
            f"ANCHOR | flagged | msg={message_id} | conv={conv_id} | "
            f"persona={persona_id} | note={note_id}"
        )
        result = {
            "message_id": message_id,
            "conversation_id": conv_id,
            "is_anchored": True,
            "anchored_at": msg.anchored_at,
            "anchored_by_persona_id": msg.anchored_by_persona_id,
            "anchor_reason": msg.anchor_reason,
            "already_anchored": False,
            "note_created": bool(note_id),
            "note_id": note_id,
        }
    finally:
        ds.close()

    # Audit (best-effort)
    summary = f"⚓ kotva #{message_id}"
    if reason:
        summary += f": {reason[:140]}"
    if note_id:
        summary += f" (+note #{note_id})"
    activity_service.record(
        category="message_anchor",
        summary=summary,
        importance=3,
        persona_id=persona_id,
        user_id=user_id,
        conversation_id=conv_id,
        tenant_id=tenant_id or msg_tenant,
        actor="persona",
        ref_type="message",
        ref_id=message_id,
    )

    return result


def unflag_message(
    *,
    message_id: int,
    persona_id: int | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
    reason: str | None = None,
) -> dict:
    """
    Odznaci zpravu jako kotvu. Reverse k flag_message.
    Auto-vytvorena ConversationNote (pokud byla) zustava nedotcena.

    Idempotentni: pokud uz neni anchored, vrati current state bez druhe
    audit zapisu.
    """
    now = datetime.now(timezone.utc)

    ds = get_data_session()
    try:
        msg = _load_message(ds, message_id)

        # Idempotent
        if not msg.is_anchored:
            logger.info(
                f"ANCHOR | already_unanchored | msg={message_id} | "
                f"persona={persona_id}"
            )
            return {
                "message_id": message_id,
                "conversation_id": msg.conversation_id,
                "is_anchored": False,
                "unanchored_at": msg.unanchored_at,
                "unanchored_reason": msg.unanchored_reason,
                "already_unanchored": True,
            }

        msg.is_anchored = False
        msg.unanchored_at = now
        msg.unanchored_reason = reason
        # anchored_at / anchored_by / anchor_reason zustavaji jako audit
        # (pres re-flag se vyclear -- viz flag_message)

        conv_id = msg.conversation_id
        msg_tenant = msg.tenant_id

        ds.commit()
        ds.refresh(msg)
        logger.info(
            f"ANCHOR | unflagged | msg={message_id} | conv={conv_id} | "
            f"persona={persona_id}"
        )
        result = {
            "message_id": message_id,
            "conversation_id": conv_id,
            "is_anchored": False,
            "unanchored_at": msg.unanchored_at,
            "unanchored_reason": msg.unanchored_reason,
            "already_unanchored": False,
        }
    finally:
        ds.close()

    # Audit
    summary = f"⚓ unflag #{message_id}"
    if reason:
        summary += f": {reason[:140]}"
    activity_service.record(
        category="message_unanchor",
        summary=summary,
        importance=2,  # unflag je low priority audit
        persona_id=persona_id,
        user_id=user_id,
        conversation_id=conv_id,
        tenant_id=tenant_id or msg_tenant,
        actor="persona",
        ref_type="message",
        ref_id=message_id,
    )

    return result
