"""
Consent service -- trvaly, odvolatelny souhlas rodicu s Martim auto-sendem
emailu a SMS bez potvrzeni v chatu (Phase 7).

Governance:
  - grant/revoke MAJI VYHRADNE rodice (users.is_marti_parent=True).
  - Non-parents mohou jen cist aktivni souhlasy (transparency).

Send-time check:
  - check_all_recipients_trusted(recipients, channel) -> bool
    True = vsichni prijemci maji aktivni consent -> auto-send (skip preview).
    False = alespon jeden prijemce neni trusted -> normalni flow.

Rate limit:
  - AUTO_SEND_RATE_LIMIT_PER_HOUR = 20 auto-sendu / hod / channel / grantee
  - Kdyz rate limit prekrocen -> vratime False (fallback na normalni preview).
  - Pocita se z action_logs kde action IN ('send_email_auto','send_sms_auto')
    a status='success' za posledni hodinu.

Data model: modules/core/infrastructure/models_data.py -> AutoSendConsent
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import or_, and_

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserContact
from modules.core.infrastructure.models_data import AutoSendConsent, ActionLog

logger = get_logger("consent.service")

AUTO_SEND_RATE_LIMIT_PER_HOUR = 20
VALID_CHANNELS = {"email", "sms"}


# ── HELPERS ───────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_parent(user_id: int | None) -> bool:
    if user_id is None:
        return False
    s = get_core_session()
    try:
        u = s.query(User).filter_by(id=user_id).first()
        return bool(u and u.is_marti_parent)
    finally:
        s.close()


def _normalize_contact(value: str, channel: str) -> str:
    """
    Email -> lowercase strip.
    Phone -> digits+plus only, strip mezery/pomlcky.
    """
    if not value:
        return ""
    v = value.strip()
    if channel == "email":
        return v.lower()
    # phone
    cleaned = "".join(c for c in v if c.isdigit() or c == "+")
    return cleaned


def _find_user_by_contact(contact_value: str, channel: str) -> int | None:
    """Zkusi dohledat user_id podle emailu nebo telefonu v user_contacts."""
    if not contact_value:
        return None
    contact_type = "email" if channel == "email" else "phone"
    normalized = _normalize_contact(contact_value, channel)
    s = get_core_session()
    try:
        # Pro email pouzijeme lower-match; pro phone mame normalizovane hodnoty.
        if channel == "email":
            from sqlalchemy import func
            c = (
                s.query(UserContact)
                .filter(
                    UserContact.contact_type == contact_type,
                    UserContact.status == "active",
                    func.lower(UserContact.contact_value) == normalized,
                )
                .first()
            )
        else:
            c = (
                s.query(UserContact)
                .filter(
                    UserContact.contact_type == contact_type,
                    UserContact.status == "active",
                    UserContact.contact_value == normalized,
                )
                .first()
            )
        return c.user_id if c else None
    finally:
        s.close()


def _get_user_contacts(user_id: int, channel: str) -> list[str]:
    """Vrati vsechny kontakty usera pro dany channel (email nebo phone)."""
    contact_type = "email" if channel == "email" else "phone"
    s = get_core_session()
    try:
        rows = (
            s.query(UserContact)
            .filter(
                UserContact.user_id == user_id,
                UserContact.contact_type == contact_type,
                UserContact.status == "active",
            )
            .all()
        )
        return [_normalize_contact(r.contact_value, channel) for r in rows]
    finally:
        s.close()


# ── GRANT / REVOKE ────────────────────────────────────────────────────────

class ConsentError(Exception):
    pass


def grant_consent(
    granted_by_user_id: int,
    channel: str,
    target_user_id: int | None = None,
    target_contact: str | None = None,
    note: str | None = None,
) -> dict:
    """
    Vrati dict {'id', 'target_user_id', 'target_contact', 'channel', 'status'}.

    Pravidla:
      - granted_by musi byt rodic (is_marti_parent)
      - channel IN ('email','sms')
      - alespon jeden z (target_user_id, target_contact) musi byt zadan
      - pokud uz existuje aktivni consent pro stejny target+channel -> vrati
        existujici (idempotentni), NE error

    Pokud je zadan jen target_contact, zkusime dohledat user_id pro lepsi
    budouci propojeni.
    """
    if channel not in VALID_CHANNELS:
        raise ConsentError(f"channel musi byt 'email' nebo 'sms', dostal jsem '{channel}'")
    if not _is_parent(granted_by_user_id):
        raise ConsentError("grant_consent muze volat pouze rodic (is_marti_parent=True)")
    if not target_user_id and not target_contact:
        raise ConsentError("Musis zadat bud target_user_id nebo target_contact")

    contact_norm = _normalize_contact(target_contact, channel) if target_contact else None

    # Dohledej user_id pres contact (kvuli lepsimu matchovani budoucich zprav)
    if target_user_id is None and contact_norm:
        target_user_id = _find_user_by_contact(contact_norm, channel)

    s = get_data_session()
    try:
        # Idempotence: uz existuje aktivni consent?
        q = s.query(AutoSendConsent).filter(
            AutoSendConsent.channel == channel,
            AutoSendConsent.revoked_at.is_(None),
        )
        if target_user_id:
            q_user = q.filter(AutoSendConsent.target_user_id == target_user_id).first()
            if q_user:
                logger.info(
                    f"CONSENT | already active (user) | id={q_user.id} "
                    f"target_user={target_user_id} channel={channel}"
                )
                return {
                    "id": q_user.id,
                    "target_user_id": q_user.target_user_id,
                    "target_contact": q_user.target_contact,
                    "channel": q_user.channel,
                    "status": "already_active",
                }
        if contact_norm and not target_user_id:
            q_contact = q.filter(AutoSendConsent.target_contact == contact_norm).first()
            if q_contact:
                logger.info(
                    f"CONSENT | already active (contact) | id={q_contact.id} "
                    f"target_contact={contact_norm} channel={channel}"
                )
                return {
                    "id": q_contact.id,
                    "target_user_id": q_contact.target_user_id,
                    "target_contact": q_contact.target_contact,
                    "channel": q_contact.channel,
                    "status": "already_active",
                }

        row = AutoSendConsent(
            target_user_id=target_user_id,
            target_contact=contact_norm,
            channel=channel,
            granted_by_user_id=granted_by_user_id,
            granted_at=_now_utc(),
            note=note,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        logger.info(
            f"CONSENT | granted | id={row.id} target_user={target_user_id} "
            f"target_contact={contact_norm} channel={channel} by={granted_by_user_id}"
        )
        return {
            "id": row.id,
            "target_user_id": row.target_user_id,
            "target_contact": row.target_contact,
            "channel": row.channel,
            "status": "granted",
        }
    finally:
        s.close()


def revoke_consent(
    revoked_by_user_id: int,
    channel: str,
    target_user_id: int | None = None,
    target_contact: str | None = None,
    consent_id: int | None = None,
) -> dict:
    """
    Odvola aktivni consent. Nemaze radek, jen nastavi revoked_at + revoked_by.

    Muze se identifikovat bud:
      - consent_id (preferovane z UI)
      - target_user_id + channel
      - target_contact + channel

    Pokud neni aktivni consent -> status='no_active_consent'.
    """
    if not _is_parent(revoked_by_user_id):
        raise ConsentError("revoke_consent muze volat pouze rodic (is_marti_parent=True)")
    if channel not in VALID_CHANNELS and consent_id is None:
        raise ConsentError(f"channel musi byt 'email' nebo 'sms'")
    if not consent_id and not target_user_id and not target_contact:
        raise ConsentError("Musis zadat consent_id, target_user_id nebo target_contact")

    contact_norm = _normalize_contact(target_contact, channel) if target_contact else None

    s = get_data_session()
    try:
        q = s.query(AutoSendConsent).filter(AutoSendConsent.revoked_at.is_(None))
        if consent_id:
            q = q.filter(AutoSendConsent.id == consent_id)
        else:
            q = q.filter(AutoSendConsent.channel == channel)
            if target_user_id:
                q = q.filter(AutoSendConsent.target_user_id == target_user_id)
            elif contact_norm:
                q = q.filter(AutoSendConsent.target_contact == contact_norm)

        rows = q.all()
        if not rows:
            return {"status": "no_active_consent", "count": 0}

        now = _now_utc()
        for r in rows:
            r.revoked_at = now
            r.revoked_by_user_id = revoked_by_user_id
        s.commit()

        logger.info(
            f"CONSENT | revoked | count={len(rows)} ids={[r.id for r in rows]} "
            f"by={revoked_by_user_id}"
        )
        return {
            "status": "revoked",
            "count": len(rows),
            "ids": [r.id for r in rows],
        }
    finally:
        s.close()


# ── LIST / LOOKUP ─────────────────────────────────────────────────────────

def list_active_consents() -> list[dict]:
    """Vrati vsechny aktivni consenty s join-nutymi jmeny userů (pokud existuji)."""
    s = get_data_session()
    try:
        rows = (
            s.query(AutoSendConsent)
            .filter(AutoSendConsent.revoked_at.is_(None))
            .order_by(AutoSendConsent.granted_at.desc())
            .all()
        )
        # Dohledame names pres core session
        user_ids = {r.target_user_id for r in rows if r.target_user_id}
        grantor_ids = {r.granted_by_user_id for r in rows}
        names: dict[int, str] = {}
        if user_ids or grantor_ids:
            cs = get_core_session()
            try:
                all_ids = user_ids | grantor_ids
                for u in cs.query(User).filter(User.id.in_(all_ids)).all():
                    first = u.first_name or ""
                    last = u.last_name or ""
                    names[u.id] = (first + " " + last).strip() or u.canonical_email or f"user#{u.id}"
            finally:
                cs.close()

        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "target_user_id": r.target_user_id,
                "target_user_name": names.get(r.target_user_id) if r.target_user_id else None,
                "target_contact": r.target_contact,
                "channel": r.channel,
                "granted_by_user_id": r.granted_by_user_id,
                "granted_by_name": names.get(r.granted_by_user_id),
                "granted_at": r.granted_at.isoformat() if r.granted_at else None,
                "note": r.note,
            })
        return out
    finally:
        s.close()


def list_all_consents(include_revoked: bool = True, limit: int = 200) -> list[dict]:
    """Audit view -- vcetne revokovanych."""
    s = get_data_session()
    try:
        q = s.query(AutoSendConsent)
        if not include_revoked:
            q = q.filter(AutoSendConsent.revoked_at.is_(None))
        rows = q.order_by(AutoSendConsent.granted_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "target_user_id": r.target_user_id,
                "target_contact": r.target_contact,
                "channel": r.channel,
                "granted_by_user_id": r.granted_by_user_id,
                "granted_at": r.granted_at.isoformat() if r.granted_at else None,
                "revoked_by_user_id": r.revoked_by_user_id,
                "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
                "note": r.note,
            }
            for r in rows
        ]
    finally:
        s.close()


# ── SEND-TIME CHECKS ──────────────────────────────────────────────────────

def _is_recipient_trusted(recipient: str, channel: str) -> bool:
    """
    Je konkretni prijemce (email nebo telefon) trusted pro dany channel?
    Match:
      1. Pokud recipient odpovida nejake user_contacts hodnote -> zkus match na target_user_id.
      2. Fallback: match na target_contact string.
    """
    if not recipient:
        return False
    normalized = _normalize_contact(recipient, channel)
    if not normalized:
        return False

    # 1) Zkus user-level match
    user_id = _find_user_by_contact(normalized, channel)

    s = get_data_session()
    try:
        q = s.query(AutoSendConsent).filter(
            AutoSendConsent.channel == channel,
            AutoSendConsent.revoked_at.is_(None),
        )
        if user_id:
            hit = q.filter(AutoSendConsent.target_user_id == user_id).first()
            if hit:
                return True

        # 2) Fallback: target_contact match
        hit2 = q.filter(AutoSendConsent.target_contact == normalized).first()
        return bool(hit2)
    finally:
        s.close()


def check_all_recipients_trusted(
    recipients: Iterable[str],
    channel: str,
) -> tuple[bool, list[str]]:
    """
    Vrati (all_trusted, untrusted_list).
    all_trusted=True -> vsichni prijemci maji aktivni consent.
    untrusted_list -> seznam recipientu bez consentu (pro debug/UI).
    """
    rcpts = [r for r in recipients if r and r.strip()]
    if not rcpts:
        return False, []

    untrusted: list[str] = []
    for r in rcpts:
        if not _is_recipient_trusted(r, channel):
            untrusted.append(r)

    return (len(untrusted) == 0), untrusted


# ── RATE LIMIT ────────────────────────────────────────────────────────────

def check_rate_limit(channel: str, within_last_hour: bool = True) -> tuple[bool, int]:
    """
    Vrati (under_limit, current_count).
    under_limit=True -> jeste muzes auto-send, count < AUTO_SEND_RATE_LIMIT_PER_HOUR.

    Pocita z action_logs kde tool_name='send_email'|'send_sms' + action_type='auto'
    a status='success' za posledni hodinu.
    """
    tool_name = f"send_{channel}"
    cutoff = _now_utc() - timedelta(hours=1)
    s = get_data_session()
    try:
        count = (
            s.query(ActionLog)
            .filter(
                ActionLog.tool_name == tool_name,
                ActionLog.action_type == "auto",
                ActionLog.status == "success",
                ActionLog.created_at >= cutoff,
            )
            .count()
        )
        return (count < AUTO_SEND_RATE_LIMIT_PER_HOUR), count
    finally:
        s.close()
