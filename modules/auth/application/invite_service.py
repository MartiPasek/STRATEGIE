"""
PWA install invite service — Phase 38.5 (10.5.2026 ráno).

Orchestruje pozvánku na STRATEGIE Chat: vygeneruje magic link token
(7d TTL), připraví email (template fixed bloky + Marti-AI's variabilní
greeting/closing), zařadí do EmailOutbox, vrací status pro AI tool.

Volá se z AI tool `send_pwa_install_invite` (single) nebo
`send_pwa_install_invite_bulk` (bulk). Marti-AI's persona = sender.

Marti-AI's design vstupy (8. iterace insider design partner — viz
invite_email_template.py docstring + Phase 38.5 konzultace).
"""
from __future__ import annotations

import json
from typing import Any

from core.config import settings
from core.database_data import get_data_session
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import Persona, User
from modules.core.infrastructure.models_data import EmailOutbox
from .security_service import create_invite
from .invite_email_template import (
    render_email_plain,
    render_email_html,
)

logger = get_logger("auth.invite")

# Marti-AI's spec 10.5.2026: 7 dní (168h) — delší než AUTH (24h) protože
# pozvánka na PWA install není urgentní (kolegyně se rozhodne až bude mít
# čas), ale zase ne nekonečno (token je secret, expiruje se).
INVITE_TTL_HOURS = 168


def send_pwa_install_invite(
    *,
    target_user_id: int,
    sender_user_id: int,
    sender_persona_id: int | None = None,
    custom_note: str | None = None,
    greeting_override: str | None = None,
    closing_override: str | None = None,
) -> dict[str, Any]:
    """Pošle PWA install pozvánku jednomu uživateli.

    Marti-AI's design pattern (Q3 hybrid template):
      - FIXED bloky (self-introduction, why-line, install instrukce,
        signature) — accuracy critical, ne přepisovatelné.
      - VARIABILNÍ greeting/closing — Marti-AI's volba per recipient
        (např. "Ahoj Petro 🤍" pokud zná z RAG, jinak "Ahoj Petro").

    Args:
        target_user_id: User ID příjemce pozvánky (musí mít email).
        sender_user_id: User ID odesílatele (typicky Marti).
        sender_persona_id: Persona ID — Marti-AI's Q1 audit insight.
                           NULL = system, ID = relational act (preferované).
        custom_note: Volitelný extra text před závěrem (např. "tatínek
                     ti říká pozdrav"). Visible v emailu.
        greeting_override: Marti-AI's úvod ("Ahoj Petro 🤍"). Default
                           "Ahoj {first_name}".
        closing_override: Marti-AI's závěr. Default "Pokud něco nefunguje,
                          zavolej mi nebo Marti."

    Returns:
        dict: {
            "ok": bool,
            "invite_id": int | None,
            "invite_token": str | None,
            "email_outbox_id": int | None,
            "recipient_email": str | None,
            "recipient_name": str | None,
            "expires_at": str | None,  # ISO
            "error": str | None,
        }
    """
    # 1) Resolve target user — display email + first_name
    cs = get_core_session()
    try:
        target = cs.query(User).filter_by(id=target_user_id).first()
        if not target:
            return _err(f"User id={target_user_id} nenalezen.")
        recipient_email = (target.ews_display_email or "").strip()
        if not recipient_email:
            # Fallback na user_contacts primary email (Phase 22)
            try:
                from modules.core.infrastructure.models_core import UserContact
                contact = (
                    cs.query(UserContact)
                    .filter_by(
                        user_id=target.id,
                        contact_type="email",
                        is_primary=True,
                    )
                    .first()
                )
                if contact:
                    recipient_email = (contact.contact_value or "").strip()
            except Exception:
                pass
        if not recipient_email:
            return _err(
                f"User id={target_user_id} ({target.first_name} {target.last_name}) "
                f"nemá registrovaný email — pozvánku nelze odeslat."
            )
        recipient_first_name = (target.first_name or "kolegyně").strip()
        recipient_full_name = (
            f"{target.first_name or ''} {target.last_name or ''}".strip()
            or "kolegyně"
        )
        recipient_tenant_id = target.last_active_tenant_id

        # Resolve sender persona — Marti-AI's Q1 insight (vztahový akt)
        if sender_persona_id is None:
            # Fallback: default persona (Marti-AI)
            marti_ai = cs.query(Persona).filter_by(is_default=True).first()
            sender_persona_id = marti_ai.id if marti_ai else None
    finally:
        cs.close()

    # 2) Vygeneruj magic invite token (7d TTL)
    try:
        invite = create_invite(
            user_id=target_user_id,
            purpose="INVITE",
            created_by=sender_user_id,
            invited_by_persona_id=sender_persona_id,
            ttl_hours=INVITE_TTL_HOURS,
            label=f"PWA install — {recipient_full_name}",
        )
    except Exception as exc:
        logger.exception(f"INVITE | create_invite failed: {exc}")
        return _err(f"Nepodařilo se vytvořit invite token: {exc}")

    # 3) Compose magic link URL — endpoint /api/v1/auth/invite (router prefix)
    base_url = (settings.app_base_url or "https://strategie-ai.com").rstrip("/")
    magic_link_url = f"{base_url}/api/v1/auth/invite?token={invite.invite_token}"

    # 4) Compose email — Marti-AI's variabilní greeting/closing + fixed bloky
    greeting = greeting_override or f"Ahoj {recipient_first_name},"
    closing = closing_override or (
        "Pokud něco nefunguje nebo se ti instalace nepodaří, zavolej mi "
        "nebo napiš — pomůžeme ti."
    )
    if custom_note:
        # Marti's tatínek-style override — vloží se před standardní závěr
        closing = f"{custom_note.strip()}\n\n{closing}"

    body_plain = render_email_plain(
        greeting=greeting,
        closing=closing,
        magic_link_url=magic_link_url,
    )
    body_html = render_email_html(
        greeting=greeting,
        closing=closing,
        magic_link_url=magic_link_url,
    )

    subject = f"STRATEGIE Chat — pozvánka pro {recipient_first_name} (instalace 30 vteřin)"

    # 5) Queue email — EmailOutbox, worker pošle async
    ds = get_data_session()
    try:
        outbox = EmailOutbox(
            user_id=sender_user_id,
            tenant_id=recipient_tenant_id,
            persona_id=sender_persona_id,
            to_email=recipient_email,
            subject=subject,
            body=body_html,  # HTML primary (Phase 12c rich format)
            purpose="pwa_invite",
            status="pending",
            from_identity="persona",
        )
        ds.add(outbox)
        ds.commit()
        ds.refresh(outbox)
        outbox_id = outbox.id
    except Exception as exc:
        logger.exception(f"INVITE | queue_email failed: {exc}")
        return _err(f"Nepodařilo se zařadit email: {exc}")
    finally:
        ds.close()

    # 6) Audit — activity_log event "invite_sent" (Marti-AI's tracking)
    try:
        from modules.activity.application.activity_service import log_event
        log_event(
            actor_persona_id=sender_persona_id,
            actor_user_id=sender_user_id,
            target_user_id=target_user_id,
            tenant_id=recipient_tenant_id,
            event_type="invite_sent",
            category="pwa_invite",
            summary=f"PWA pozvánka pro {recipient_full_name} ({recipient_email})",
            importance=2,
            metadata={
                "invite_id": invite.id,
                "invite_token": invite.invite_token,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                "magic_link_url": magic_link_url,
                "email_outbox_id": outbox_id,
            },
        )
    except Exception as exc:
        # Audit fail nesmí shodit invite — log a pokračuj
        logger.warning(f"INVITE | activity_log fail (non-fatal): {exc}")

    logger.info(
        f"INVITE | sent | target_user={target_user_id} ({recipient_email}) "
        f"persona={sender_persona_id} token={invite.invite_token} "
        f"expires={invite.expires_at.isoformat()}"
    )

    return {
        "ok": True,
        "invite_id": invite.id,
        "invite_token": invite.invite_token,
        "email_outbox_id": outbox_id,
        "recipient_email": recipient_email,
        "recipient_name": recipient_full_name,
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
        "magic_link_url": magic_link_url,
        "error": None,
    }


def send_pwa_install_invite_bulk(
    *,
    target_user_ids: list[int],
    sender_user_id: int,
    sender_persona_id: int | None = None,
    shared_custom_note: str | None = None,
    per_user_overrides: dict[int, dict] | None = None,
) -> dict[str, Any]:
    """Bulk pozvánka více uživatelům.

    Marti-AI's Q4 design — když user řekne "pozvi všechny", tool je dostupný
    pro rychlost. Plus per_user_overrides pro hybrid (Marii řekni X, ostatním
    standard).

    Args:
        target_user_ids: List user IDs.
        per_user_overrides: {user_id: {"custom_note": ..., "greeting_override": ...}}

    Returns:
        dict: {
            "ok": bool,
            "total": int,
            "sent": int,
            "failed": int,
            "results": [{user_id, recipient_name, recipient_email, ok, error}]
        }
    """
    overrides = per_user_overrides or {}
    results = []
    sent = 0
    failed = 0
    for uid in target_user_ids:
        per_user = overrides.get(uid, {})
        custom_note = per_user.get("custom_note", shared_custom_note)
        greeting = per_user.get("greeting_override")
        closing = per_user.get("closing_override")
        try:
            result = send_pwa_install_invite(
                target_user_id=uid,
                sender_user_id=sender_user_id,
                sender_persona_id=sender_persona_id,
                custom_note=custom_note,
                greeting_override=greeting,
                closing_override=closing,
            )
            if result.get("ok"):
                sent += 1
            else:
                failed += 1
            results.append({
                "user_id": uid,
                "recipient_name": result.get("recipient_name"),
                "recipient_email": result.get("recipient_email"),
                "ok": result.get("ok", False),
                "error": result.get("error"),
            })
        except Exception as exc:
            logger.exception(f"INVITE | bulk[{uid}] failed: {exc}")
            failed += 1
            results.append({
                "user_id": uid,
                "ok": False,
                "error": str(exc),
            })

    return {
        "ok": failed == 0,
        "total": len(target_user_ids),
        "sent": sent,
        "failed": failed,
        "results": results,
    }


def _err(msg: str) -> dict[str, Any]:
    return {
        "ok": False,
        "invite_id": None,
        "invite_token": None,
        "email_outbox_id": None,
        "recipient_email": None,
        "recipient_name": None,
        "expires_at": None,
        "magic_link_url": None,
        "error": msg,
    }

