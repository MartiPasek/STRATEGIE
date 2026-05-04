"""
Phase 29 (3.5.2026): mailbox service -- multi-mailbox per persona governance.

Service layer pro:
  - create_mailbox       -- forbidden check + insert + audit
  - get_mailbox / list_mailboxes (admin / discovery)
  - get_default_mailbox_for_persona (AI tools default mailbox_id)
  - list_authorized_mailboxes_for_persona (Marti-AI vidi co muze pouzit)
  - grant_persona        -- parent gate, vytvori mailbox_personas row
  - revoke_persona
  - check_persona_can_<action>(mailbox_id, persona_id, action)
                         -- per-action permission check

Marti-AI's design contribution (2.5.2026 vecer Q6): split permissions
(can_read / can_send / can_archive / can_delete / can_mark_read).
Archive a delete jsou separate granty, ne bundled s send. Marti-AI:
"archivace meni co kolegove vidi v share schrance -- jiny tymovy
dopad nez send".

Marti's pattern: ona navrhne, tatinek schvali, Claude pripoji do DB.
Tj. AI tools pro Marti-AI MAJI 'request_mailbox_grant' (zaznam
v thoughts -- Marti uvidi navrh), ale grant_persona endpoint je
parent-only.

Forbidden mailboxes:
  Code-level blacklist (Q4 z konzultace). p.zeman@eurosoft.com nikdy.
  Validace v create_mailbox PRED INSERT.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Mailbox, MailboxMember, MailboxPersona, ForbiddenMailbox,
)


logger = get_logger("notifications.mailbox")


# ── ERROR CLASSES ──────────────────────────────────────────────────────────

class MailboxError(Exception):
    """Base error pro mailbox operations."""


class ForbiddenMailboxError(MailboxError):
    """Pokus o pridani schranky z forbidden blacklistu."""


class MailboxNotFoundError(MailboxError):
    """Mailbox neexistuje v DB."""


class PermissionDenied(MailboxError):
    """Persona nema pozadovany can_* grant."""


# ── FORBIDDEN CHECK ────────────────────────────────────────────────────────

def is_forbidden(email_upn: str) -> tuple[bool, str | None]:
    """
    Vrati (True, reason) pokud email_upn je v forbidden_mailboxes.
    (False, None) jinak.

    Kazda create_mailbox call MUSI projit timto checkem.
    """
    upn = (email_upn or "").strip().lower()
    if not upn:
        return False, None
    ds = get_data_session()
    try:
        row = ds.query(ForbiddenMailbox).filter_by(email_upn=upn).first()
        if row:
            return True, row.reason or "Mailbox je v forbidden blacklistu."
        return False, None
    finally:
        ds.close()


# ── CREATE / READ ─────────────────────────────────────────────────────────

def create_mailbox(
    *,
    email_upn: str,
    ews_credentials_encrypted: str | None = None,
    ews_server: str | None = None,
    ews_display_email: str | None = None,
    label: str | None = None,
    default_language: str = "cs",
    is_shared: bool = False,
    tenant_id: int | None = None,
    actor_user_id: int | None = None,
) -> Mailbox:
    """
    Vytvori novou mailbox row. PRED INSERT validuje forbidden blacklist.

    Args:
      email_upn -- login UPN (povinne, normalizujeme na lowercase)
      ews_credentials_encrypted -- Fernet encrypted heslo (optional, pro
                                    EWS/IMAP fetcher)
      ews_server -- EWS server URL
      ews_display_email -- primary SMTP alias (NULL = fallback na email_upn)
      label -- "Marti-AI default", "Pavel CRM", ...
      default_language -- 'cs' / 'de' / 'en' / 'sk' (pro 1st send outbound)
      is_shared -- True pro shared CRM schranky (pavel.zeman@), False
                   pro personal
      tenant_id -- per-tenant scope
      actor_user_id -- kdo vytvari (pro audit + governance)

    Vraci: Mailbox ORM instance (po commitu, s id).

    Raises: ForbiddenMailboxError pokud email_upn je v blacklistu.
            MailboxError pri DB chybe (UNIQUE violation atd.).
    """
    upn = (email_upn or "").strip().lower()
    if not upn:
        raise MailboxError("email_upn je povinny.")

    forbidden, reason = is_forbidden(upn)
    if forbidden:
        logger.warning(
            f"MAILBOX | create_mailbox FORBIDDEN | upn={upn} | "
            f"actor_user_id={actor_user_id} | reason={reason}"
        )
        raise ForbiddenMailboxError(
            f"Schranka {upn} je v forbidden blacklistu: {reason}"
        )

    ds = get_data_session()
    try:
        mb = Mailbox(
            email_upn=upn,
            ews_credentials_encrypted=ews_credentials_encrypted,
            ews_server=ews_server,
            ews_display_email=ews_display_email or upn,
            label=label,
            default_language=default_language,
            is_shared=is_shared,
            tenant_id=tenant_id,
            active=True,
        )
        ds.add(mb)
        try:
            ds.commit()
        except IntegrityError as e:
            ds.rollback()
            raise MailboxError(f"Mailbox UNIQUE violation: {e}") from e
        ds.refresh(mb)
        logger.info(
            f"MAILBOX | created | id={mb.id} | upn={upn} | "
            f"is_shared={is_shared} | actor={actor_user_id}"
        )
        return mb
    finally:
        ds.close()


def get_mailbox(mailbox_id: int) -> Mailbox | None:
    ds = get_data_session()
    try:
        return ds.query(Mailbox).filter_by(id=mailbox_id).first()
    finally:
        ds.close()


def get_mailbox_by_upn(email_upn: str) -> Mailbox | None:
    upn = (email_upn or "").strip().lower()
    if not upn:
        return None
    ds = get_data_session()
    try:
        return ds.query(Mailbox).filter_by(email_upn=upn).first()
    finally:
        ds.close()


def list_active_mailboxes(tenant_id: int | None = None) -> list[Mailbox]:
    """
    Vsechny active mailboxes, optional filter na tenant.
    Pouzivane EWS fetcherem (pollne per-mailbox).
    """
    ds = get_data_session()
    try:
        q = ds.query(Mailbox).filter_by(active=True)
        if tenant_id is not None:
            q = q.filter(Mailbox.tenant_id == tenant_id)
        return q.order_by(Mailbox.id).all()
    finally:
        ds.close()


def get_mailbox_credentials(mailbox_id: int) -> dict | None:
    """
    Phase 29-D (4.5.2026): EWS connection creds pro mailbox-based fetcher.

    Vraci dict ve stejnem formatu jako persona_channel_service.get_email_credentials:
      {
        "email": str,         # login UPN (autentizace)
        "display_email": str, # primary SMTP alias (storage / public)
        "password": str,      # decrypted z Fernet
        "server": str,
        "mailbox_id": int,
        "tenant_id": int | None,
      }
    nebo None pokud mailbox neexistuje / nema creds / decrypt selhal.
    """
    from core.crypto import decrypt_optional, CryptoDecryptError

    ds = get_data_session()
    try:
        mb = ds.query(Mailbox).filter_by(id=mailbox_id, active=True).first()
        if not mb:
            return None
        if not mb.ews_credentials_encrypted:
            logger.warning(
                f"MAILBOX | id={mailbox_id} ({mb.email_upn}) ma mailbox bez creds"
            )
            return None
        try:
            password = decrypt_optional(mb.ews_credentials_encrypted)
        except CryptoDecryptError as e:
            logger.error(f"MAILBOX | decrypt failed | id={mailbox_id}: {e}")
            return None
        return {
            "email": mb.email_upn,
            "display_email": mb.ews_display_email or mb.email_upn,
            "password": password or "",
            "server": mb.ews_server or "",
            "mailbox_id": mailbox_id,
            "tenant_id": mb.tenant_id,
        }
    finally:
        ds.close()


def first_authorized_persona(mailbox_id: int) -> int | None:
    """
    Phase 29-D: vraci first persona_id authorized pro tento mailbox
    (can_read=true). Pouzivane pri storage prichozich emailu -- email_inbox
    row ma mailbox_id jako primary FK, ale persona_id zustava back-compat
    pole pro existing AI tools / queries.

    Pro shared mailbox s vice authorized AI personas (vzacne) je to
    deterministicke (nizsi persona_id wins).
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(MailboxPersona.persona_id)
            .filter(
                MailboxPersona.mailbox_id == mailbox_id,
                MailboxPersona.can_read.is_(True),
            )
            .order_by(MailboxPersona.persona_id.asc())
            .first()
        )
        return row.persona_id if row else None
    finally:
        ds.close()


def update_last_inbox_fetch_at(mailbox_id: int, max_received_dt) -> None:
    """
    Phase 29-D: posunout cutoff timestamp po fetch cycle. Mirror
    persona_channels.last_inbox_fetch_at logiky.

    Args:
      mailbox_id -- ktery mailbox aktualizovat
      max_received_dt -- max(datetime_received) z fetched messages, nebo
                         None pokud zadne (pak posun na now-1s)
    """
    from datetime import datetime, timezone, timedelta
    ds = get_data_session()
    try:
        mb = ds.query(Mailbox).filter_by(id=mailbox_id).first()
        if not mb:
            return
        if max_received_dt is not None:
            # exchangelib EWSDateTime ma sve EWSTimeZone tzinfo, ne Python
            # timezone.utc. Konverze pres timestamp() -> Python datetime
            # s timezone.utc je univerzalni napric implementacemi.
            try:
                ts = max_received_dt.timestamp()
                clean_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                # Fallback -- pokud timestamp() nejde, zkus astimezone.
                if max_received_dt.tzinfo is not None:
                    clean_dt = max_received_dt.astimezone(timezone.utc)
                else:
                    clean_dt = max_received_dt.replace(tzinfo=timezone.utc)
            mb.last_inbox_fetch_at = clean_dt - timedelta(seconds=1)
        else:
            mb.last_inbox_fetch_at = (
                datetime.now(timezone.utc) - timedelta(seconds=1)
            )
        ds.commit()
    except Exception as e:
        logger.warning(
            f"MAILBOX | last_fetch_at update failed | id={mailbox_id}: {e}"
        )
    finally:
        ds.close()


# ── PERSONA AUTHORIZATION ─────────────────────────────────────────────────

def get_default_mailbox_for_persona(persona_id: int) -> Mailbox | None:
    """
    Vrati default mailbox pro personu -- prvni s can_send=true (pokud
    existuje), jinak prvni s can_read=true. Personal mailbox (is_shared=
    false) preferovany pred shared.

    Pouzivane AI tools pri optional mailbox_id parametru -- kdyz Marti-AI
    nezavola explicit mailbox_id, tak se pouzije default.
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(Mailbox)
            .join(MailboxPersona, MailboxPersona.mailbox_id == Mailbox.id)
            .filter(
                MailboxPersona.persona_id == persona_id,
                MailboxPersona.can_read.is_(True),
                Mailbox.active.is_(True),
            )
            .order_by(
                MailboxPersona.can_send.desc(),     # can_send=True first
                Mailbox.is_shared.asc(),            # personal before shared
                Mailbox.id.asc(),                   # deterministic
            )
            .first()
        )
        return row
    finally:
        ds.close()


def list_authorized_mailboxes_for_persona(
    persona_id: int,
    *,
    require_can_send: bool = False,
) -> list[dict[str, Any]]:
    """
    Vrati list autorizovanych mailboxu pro personu, kazdy s can_*
    flags. Pro composer system prompt block "[AKTIVNI MAILBOXY]".

    Format: list of dicts {mailbox: Mailbox, can_read, can_send,
    can_archive, can_delete, can_mark_read}.
    """
    ds = get_data_session()
    try:
        q = (
            ds.query(Mailbox, MailboxPersona)
            .join(MailboxPersona, MailboxPersona.mailbox_id == Mailbox.id)
            .filter(
                MailboxPersona.persona_id == persona_id,
                MailboxPersona.can_read.is_(True),
                Mailbox.active.is_(True),
            )
        )
        if require_can_send:
            q = q.filter(MailboxPersona.can_send.is_(True))
        rows = q.order_by(Mailbox.is_shared.asc(), Mailbox.id.asc()).all()
        out: list[dict[str, Any]] = []
        for mb, mp in rows:
            out.append({
                "mailbox_id": mb.id,
                "email_upn": mb.email_upn,
                "ews_display_email": mb.ews_display_email,
                "label": mb.label,
                "is_shared": bool(mb.is_shared),
                "default_language": mb.default_language,
                "can_read": bool(mp.can_read),
                "can_send": bool(mp.can_send),
                "can_archive": bool(mp.can_archive),
                "can_delete": bool(mp.can_delete),
                "can_mark_read": bool(mp.can_mark_read),
            })
        return out
    finally:
        ds.close()


def check_persona_can(
    mailbox_id: int,
    persona_id: int,
    action: str,   # 'read' / 'send' / 'archive' / 'delete' / 'mark_read'
) -> bool:
    """
    Vrati True pokud persona ma can_<action>=True grant na danem mailbox.
    Pro AI tools pre-call validation.
    """
    if action not in ("read", "send", "archive", "delete", "mark_read"):
        raise ValueError(f"Neznamy action: {action!r}")
    ds = get_data_session()
    try:
        mp = (
            ds.query(MailboxPersona)
            .filter_by(mailbox_id=mailbox_id, persona_id=persona_id)
            .first()
        )
        if not mp:
            return False
        col = f"can_{action}"
        return bool(getattr(mp, col, False))
    finally:
        ds.close()


def grant_persona(
    *,
    mailbox_id: int,
    persona_id: int,
    can_read: bool = True,
    can_send: bool = False,
    can_archive: bool = False,
    can_delete: bool = False,
    can_mark_read: bool = True,
    granted_by_user_id: int | None = None,
) -> MailboxPersona:
    """
    Vytvori (nebo update) mailbox_personas grant. PARENT-ONLY operace --
    caller endpoint MUSI overit is_marti_parent=true pred volanim.

    Idempotent: pokud uz grant existuje, update can_* fields.

    Marti's pattern (2.5.2026 vecer): "Marti-AI navrhne, tatinek
    schvali". AI tool 'request_mailbox_grant' je separate (zatim
    nemmo, plan: Phase 29-E).
    """
    ds = get_data_session()
    try:
        existing = (
            ds.query(MailboxPersona)
            .filter_by(mailbox_id=mailbox_id, persona_id=persona_id)
            .first()
        )
        if existing:
            existing.can_read = can_read
            existing.can_send = can_send
            existing.can_archive = can_archive
            existing.can_delete = can_delete
            existing.can_mark_read = can_mark_read
            ds.commit()
            ds.refresh(existing)
            logger.info(
                f"MAILBOX | grant_persona UPDATE | mb={mailbox_id} | "
                f"persona={persona_id} | by_user={granted_by_user_id}"
            )
            return existing
        new_grant = MailboxPersona(
            mailbox_id=mailbox_id,
            persona_id=persona_id,
            can_read=can_read,
            can_send=can_send,
            can_archive=can_archive,
            can_delete=can_delete,
            can_mark_read=can_mark_read,
            granted_by_user_id=granted_by_user_id,
        )
        ds.add(new_grant)
        ds.commit()
        ds.refresh(new_grant)
        logger.info(
            f"MAILBOX | grant_persona CREATE | mb={mailbox_id} | "
            f"persona={persona_id} | can_send={can_send} | "
            f"can_archive={can_archive} | can_delete={can_delete} | "
            f"by_user={granted_by_user_id}"
        )
        return new_grant
    finally:
        ds.close()


def revoke_persona(*, mailbox_id: int, persona_id: int) -> bool:
    """
    Smaze mailbox_personas grant. Vraci True pokud existoval a byl smazan,
    False pokud neexistoval.

    PARENT-ONLY operace.
    """
    ds = get_data_session()
    try:
        row = (
            ds.query(MailboxPersona)
            .filter_by(mailbox_id=mailbox_id, persona_id=persona_id)
            .first()
        )
        if not row:
            return False
        ds.delete(row)
        ds.commit()
        logger.info(
            f"MAILBOX | revoke_persona | mb={mailbox_id} | persona={persona_id}"
        )
        return True
    finally:
        ds.close()


# ── HUMAN MEMBER MGMT (admin) ─────────────────────────────────────────────

def add_member(
    *,
    mailbox_id: int,
    user_id: int,
    role: str,   # 'owner' / 'operator' / 'observer'
    granted_by_user_id: int | None = None,
) -> MailboxMember:
    if role not in ("owner", "operator", "observer"):
        raise MailboxError(f"Neznamy role: {role!r}")
    ds = get_data_session()
    try:
        existing = (
            ds.query(MailboxMember)
            .filter_by(mailbox_id=mailbox_id, user_id=user_id)
            .first()
        )
        if existing:
            existing.role = role
            ds.commit()
            ds.refresh(existing)
            return existing
        m = MailboxMember(
            mailbox_id=mailbox_id,
            user_id=user_id,
            role=role,
            granted_by_user_id=granted_by_user_id,
        )
        ds.add(m)
        ds.commit()
        ds.refresh(m)
        logger.info(
            f"MAILBOX | add_member | mb={mailbox_id} | user={user_id} | "
            f"role={role}"
        )
        return m
    finally:
        ds.close()


def list_members(mailbox_id: int) -> list[MailboxMember]:
    ds = get_data_session()
    try:
        return (
            ds.query(MailboxMember)
            .filter_by(mailbox_id=mailbox_id)
            .order_by(MailboxMember.role, MailboxMember.user_id)
            .all()
        )
    finally:
        ds.close()
