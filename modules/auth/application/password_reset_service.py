"""
Password reset service -- forgot password flow logic.

API:
    create_reset_token(email)        -> str | None       # token nebo None pokud user neexistuje
    get_reset_info(token)            -> dict | None      # peek bez consume
    consume_reset_token(token, plain_password)  -> dict | None   # set new password

Bezpecnostni navrh:
- create_reset_token vraci None tise pokud email neexistuje (no enumeration).
  Caller (router) by mel vzdy odpovedet 200 OK at uz token vznikl nebo ne.
- Tokeny jsou jednorazove (used_at) + casove omezene (TOKEN_EXPIRY_MINUTES).
- Pri novem requestu invalidujeme stare aktivni tokeny stejneho usera.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta

from core.database_core import get_core_session
from core.logging import get_logger
from modules.auth.application.password import hash_password
from modules.core.infrastructure.models_core import (
    User, UserContact, PasswordResetToken,
)

logger = get_logger("auth.password_reset")

TOKEN_EXPIRY_MINUTES = 60


def create_reset_token(email: str) -> tuple[str, int, str | None] | None:
    """
    Vytvori reset token pro usera s danym emailem.

    Returns:
        (token, user_id, first_name) pokud user existuje a je aktivni
        None pokud email neni v systemu (caller by mel stejne vratit 200 OK,
        no-enumeration: utocnik nesmi zjistit zda email existuje)
    """
    needle = email.strip().lower()
    session = get_core_session()
    try:
        contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .first()
        )
        if not contact:
            logger.info(f"PASSWORD_RESET | no contact for email | email={email}")
            return None

        user = session.query(User).filter_by(id=contact.user_id).first()
        if not user or user.status != "active":
            logger.info(f"PASSWORD_RESET | user not active | email={email}")
            return None

        # Invaliduj stare aktivni tokeny stejneho usera (best practice -- jen
        # posledni request je platny, predchozi se zneplatni i kdyby unikly).
        now = datetime.now(timezone.utc)
        old_active = (
            session.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .all()
        )
        for old in old_active:
            old.used_at = now   # treat as consumed -> invalidates

        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)

        prt = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            sent_to_email=contact.contact_value,
            created_at=now,
        )
        session.add(prt)
        session.commit()

        logger.info(
            f"PASSWORD_RESET | token created | user_id={user.id} | "
            f"token={token[:8]}... | invalidated_old={len(old_active)}"
        )
        return (token, user.id, user.first_name)
    except Exception as e:
        session.rollback()
        logger.error(f"PASSWORD_RESET | create failed: {e}")
        raise
    finally:
        session.close()


def get_reset_info(token: str) -> dict | None:
    """Peek na reset token. Vraci masked email pro UI ('m***@gmail.com')
    + first_name aby user videl pro jaky ucet meni heslo. Bez consume."""
    session = get_core_session()
    try:
        prt = session.query(PasswordResetToken).filter_by(token=token).first()
        if not prt:
            return None
        if prt.used_at is not None:
            return None
        if prt.expires_at < datetime.now(timezone.utc):
            return None

        user = session.query(User).filter_by(id=prt.user_id).first()
        if not user or user.status != "active":
            return None

        return {
            "email_masked": _mask_email(prt.sent_to_email),
            "first_name": user.first_name,
            "valid": True,
        }
    finally:
        session.close()


def consume_reset_token(token: str, new_password: str) -> dict | None:
    """
    Spotrebuje token: nastavi nove heslo, oznaci token jako pouzity.

    Returns:
        {user_id, email} pokud se podarilo
        None pokud token neexistuje, expiroval, nebo byl uz pouzity
    Raises:
        PasswordTooShort: nove heslo je kratsi nez MIN_PASSWORD_LENGTH
                          (vyhodi pred zasahem do DB)
    """
    # Hash predem -- aby PasswordTooShort vyhodilo bez DB transakce
    new_hash = hash_password(new_password)   # raises PasswordTooShort

    session = get_core_session()
    try:
        prt = session.query(PasswordResetToken).filter_by(token=token).first()
        if not prt:
            logger.warning("PASSWORD_RESET | consume: token not found")
            return None
        if prt.used_at is not None:
            logger.warning(f"PASSWORD_RESET | consume: token already used | token={token[:8]}...")
            return None
        if prt.expires_at < datetime.now(timezone.utc):
            logger.warning(f"PASSWORD_RESET | consume: token expired | token={token[:8]}...")
            return None

        user = session.query(User).filter_by(id=prt.user_id).first()
        if not user or user.status != "active":
            logger.warning(f"PASSWORD_RESET | consume: user not active | user_id={prt.user_id}")
            return None

        now = datetime.now(timezone.utc)
        user.password_hash = new_hash
        user.password_set_at = now
        prt.used_at = now
        session.commit()

        logger.info(
            f"PASSWORD_RESET | password changed via reset | user_id={user.id} | "
            f"token={token[:8]}..."
        )
        return {"user_id": user.id, "email": prt.sent_to_email}
    except Exception as e:
        session.rollback()
        logger.error(f"PASSWORD_RESET | consume failed: {e}")
        raise
    finally:
        session.close()


def _mask_email(email: str) -> str:
    """'martin.pasek@example.com' -> 'm**********@example.com'.
    Pro UI -- ukazat ze je to ten spravny ucet, bez plneho ungeranti adresy."""
    if "@" not in email:
        return email
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return f"{local[0]}*@{domain}"
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"
