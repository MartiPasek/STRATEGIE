"""
User channel service -- EWS credentialy uzivatele pro "posli z moji schranky".

MVP: flat fields na `users` tabulce (ews_email / ews_password_encrypted /
ews_server / ews_display_email). Jedna schranka per user. Pokud by nekdy
bylo treba vic schranek per user, refactor na user_channels tabulku.

Paralela k persona_channel_service, ale s odlisnym schematem -- dokud
nebude multi-mailbox treba, flat fields staci.
"""
from __future__ import annotations
from typing import Any

from core.database_core import get_core_session
from core.logging import get_logger
from core.crypto import decrypt_optional, encrypt, CryptoDecryptError
from modules.core.infrastructure.models_core import User

logger = get_logger("notifications.user_channels")


def get_user_email_credentials(user_id: int) -> dict[str, str] | None:
    """
    Vrati dict s EWS credentialy uzivatele:
      {
        "email": str,           # UPN / login
        "display_email": str,   # Primary SMTP alias (fallback na email)
        "password": str,        # desifrovane heslo
        "server": str,
      }
    nebo None kdyz user EWS nenakonfiguroval.
    """
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            return None
        if not (u.ews_email and u.ews_password_encrypted and u.ews_server):
            return None
        try:
            password = decrypt_optional(u.ews_password_encrypted)
        except CryptoDecryptError as e:
            logger.error(
                f"USER CHANNEL | email | decrypt failed | user_id={user_id}: {e}"
            )
            return None
        return {
            "email": u.ews_email,
            "display_email": u.ews_display_email or u.ews_email,
            "password": password or "",
            "server": u.ews_server,
        }
    finally:
        cs.close()


def has_user_email(user_id: int) -> bool:
    """Rychly check bez desifrovani -- ma user nastaveny EWS kanal?"""
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            return False
        return bool(u.ews_email and u.ews_password_encrypted and u.ews_server)
    finally:
        cs.close()


def get_user_display_email(user_id: int) -> str | None:
    """Jen display email pro prezentaci (composer, preview) -- bez desifrovani."""
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u or not u.ews_email:
            return None
        return u.ews_display_email or u.ews_email
    finally:
        cs.close()


def upsert_user_email(
    user_id: int,
    email: str,
    password: str,
    server: str,
    display_email: str | None = None,
) -> dict[str, Any]:
    """
    Ulozi (nebo prepise) EWS credentialy uzivatele. Heslo sifrujeme Fernetem.
    """
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            raise ValueError(f"user #{user_id} nenalezen")
        u.ews_email = email
        u.ews_password_encrypted = encrypt(password)
        u.ews_server = server
        u.ews_display_email = display_email
        cs.commit()
        cs.refresh(u)
        logger.info(
            f"USER CHANNEL | email | upsert | user_id={user_id} | "
            f"login={email} | display={display_email or email}"
        )
        return {
            "user_id": u.id,
            "ews_email": u.ews_email,
            "ews_display_email": u.ews_display_email,
            "ews_server": u.ews_server,
        }
    finally:
        cs.close()


def clear_user_email(user_id: int) -> bool:
    """Smaze EWS kredencialy uzivatele (pro rotaci nebo opt-out)."""
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            return False
        u.ews_email = None
        u.ews_password_encrypted = None
        u.ews_server = None
        u.ews_display_email = None
        cs.commit()
        logger.info(f"USER CHANNEL | email | cleared | user_id={user_id}")
        return True
    finally:
        cs.close()
