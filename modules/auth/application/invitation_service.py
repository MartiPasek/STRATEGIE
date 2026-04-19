"""
Invitation service po identity refaktoru v2.

Místo `user_identities` pracuje s `user_contacts`. Při vytvoření pozvánky:
  - Pokud uživatel s daným emailem existuje (user_contacts) → použij ho
  - Jinak vytvoř nového pending usera + email kontakt
Tabulky `invitations` a `onboarding_sessions` zůstávají beze změny.
"""
import secrets
from datetime import datetime, timezone, timedelta

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    User, UserContact, UserTenant, Invitation,
)

logger = get_logger("auth.invitation")

TOKEN_EXPIRY_HOURS = 48


def create_invitation(
    email: str,
    invited_by_user_id: int,
    tenant_id: int,
    role: str = "member",
    first_name: str | None = None,
    last_name: str | None = None,
    gender: str | None = None,
) -> str:
    """
    Vytvoří pozvánku pro nového uživatele.
    Pokud uživatel se zadaným emailem už existuje, jen vytvoří invitation token.
    Pokud ne, vytvoří pending usera + email kontakt.

    first_name/last_name/gender — pokud zadáno, uloží se na user record při
    vytváření. Pozvaný pak v welcome screen vidí svoje jméno (poznán) místo
    prázdného formuláře.
    """
    needle = email.strip().lower()
    session = get_core_session()
    try:
        existing_contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .first()
        )

        if existing_contact:
            user_id = existing_contact.user_id
            logger.info(f"INVITATION | existing user | user_id={user_id}")
            # Pokud existující user nemá jméno a my ho teď známe, doplň ho.
            existing_user = session.query(User).filter_by(id=user_id).first()
            if existing_user:
                if first_name and not existing_user.first_name:
                    existing_user.first_name = first_name.strip()
                if last_name and not existing_user.last_name:
                    existing_user.last_name = last_name.strip()
                if gender and not existing_user.gender:
                    existing_user.gender = gender
        else:
            user = User(
                status="pending",
                first_name=(first_name or "").strip() or None,
                last_name=(last_name or "").strip() or None,
                gender=gender,
                invited_by_user_id=invited_by_user_id,
                invited_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.flush()

            contact = UserContact(
                user_id=user.id,
                contact_type="email",
                contact_value=needle,
                label=None,
                is_primary=True,
                is_verified=False,
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(contact)
            user_id = user.id
            logger.info(f"INVITATION | new pending user created | user_id={user_id}")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

        invitation = Invitation(
            user_id=user_id,
            email=needle,
            token=token,
            expires_at=expires_at,
            requires_sms_verification=False,    # MVP: bez SMS
            created_at=datetime.now(timezone.utc),
        )
        session.add(invitation)
        session.commit()

        logger.info(f"INVITATION | created | email={email} | token={token[:8]}...")
        return token

    except Exception as e:
        session.rollback()
        logger.error(f"INVITATION | failed: {e}")
        raise
    finally:
        session.close()


def accept_invitation(token: str) -> dict | None:
    """Přijme pozvánku a aktivuje uživatele."""
    session = get_core_session()
    try:
        invitation = session.query(Invitation).filter_by(token=token).first()
        if not invitation:
            logger.warning("INVITATION | token not found")
            return None

        if invitation.expires_at < datetime.now(timezone.utc):
            logger.warning("INVITATION | token expired")
            return None

        user = session.query(User).filter_by(id=invitation.user_id).first()
        if not user:
            return None

        user.status = "active"
        session.commit()

        primary_contact = (
            session.query(UserContact)
            .filter_by(user_id=user.id, contact_type="email", is_primary=True, status="active")
            .first()
        )

        logger.info(f"INVITATION | accepted | user_id={user.id}")
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": primary_contact.contact_value if primary_contact else invitation.email,
            "tenant_id": user.last_active_tenant_id,
        }
    finally:
        session.close()
