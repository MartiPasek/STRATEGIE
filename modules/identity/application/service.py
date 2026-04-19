"""
Identity service po identity refaktoru v2.

Místo `UserIdentity` pracuje s `UserContact`. Modely User a UserContact
jsou v modules/core/infrastructure/models_core.py.
"""
from datetime import datetime, timezone

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserContact

logger = get_logger("identity")

ALLOWED_CONTACT_TYPES = {"email", "phone"}


def create_user(
    first_name: str | None = None,
    last_name: str | None = None,
    status: str = "active",
) -> int:
    """Vytvoří nového uživatele. Vrátí jeho BigInteger id."""
    session = get_core_session()
    try:
        user = User(
            first_name=first_name,
            last_name=last_name,
            status=status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"IDENTITY | user created | id={user.id}")
        return user.id
    finally:
        session.close()


def add_contact(
    user_id: int,
    contact_type: str,
    contact_value: str,
    label: str | None = None,
    is_primary: bool = False,
) -> int:
    """Přidá kontakt k uživateli. Vrátí id kontaktu."""
    if contact_type not in ALLOWED_CONTACT_TYPES:
        raise ValueError(
            f"Unknown contact_type '{contact_type}'. Allowed: {ALLOWED_CONTACT_TYPES}"
        )

    session = get_core_session()
    try:
        existing = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == contact_type,
                UserContact.contact_value == contact_value,
                UserContact.status == "active",
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Contact {contact_type}='{contact_value}' už existuje pro user {existing.user_id}"
            )

        contact = UserContact(
            user_id=user_id,
            contact_type=contact_type,
            contact_value=contact_value,
            label=label,
            is_primary=is_primary,
            is_verified=False,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(contact)
        session.commit()
        session.refresh(contact)
        logger.info(f"IDENTITY | contact added | user_id={user_id} | type={contact_type}")
        return contact.id
    finally:
        session.close()


def find_user_by_contact(contact_type: str, contact_value: str) -> int | None:
    """Najde uživatele podle kontaktu (email/phone). Vrátí user_id nebo None."""
    session = get_core_session()
    try:
        contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == contact_type,
                UserContact.contact_value == contact_value,
                UserContact.status == "active",
            )
            .first()
        )
        return contact.user_id if contact else None
    finally:
        session.close()
