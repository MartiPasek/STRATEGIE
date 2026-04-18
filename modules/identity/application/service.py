"""
Identity service — přepojeno na css_db přes BaseCore.
Modely User a UserIdentity jsou v modules/core/infrastructure/models_core.py.
"""
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserIdentity
from datetime import datetime, timezone

logger = get_logger("identity")

ALLOWED_IDENTITY_TYPES = {"email", "phone"}


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
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"IDENTITY | user created | id={user.id}")
        return user.id
    finally:
        session.close()


def add_identity(
    user_id: int,
    type: str,
    value: str,
    is_primary: bool = False,
) -> int:
    """Přidá identitu k uživateli. Vrátí id identity."""
    if type not in ALLOWED_IDENTITY_TYPES:
        raise ValueError(f"Unknown identity type '{type}'. Allowed: {ALLOWED_IDENTITY_TYPES}")

    session = get_core_session()
    try:
        existing = session.query(UserIdentity).filter(
            UserIdentity.type == type,
            UserIdentity.value == value,
        ).first()
        if existing:
            raise ValueError(f"Identity {type}='{value}' already exists for user {existing.user_id}")

        identity = UserIdentity(
            user_id=user_id,
            type=type,
            value=value,
            is_primary=is_primary,
            created_at=datetime.now(timezone.utc),
        )
        session.add(identity)
        session.commit()
        session.refresh(identity)
        logger.info(f"IDENTITY | identity added | user_id={user_id} | type={type}")
        return identity.id
    finally:
        session.close()


def find_user_by_identity(type: str, value: str) -> int | None:
    """Najde uživatele podle identity. Vrátí user_id nebo None."""
    session = get_core_session()
    try:
        identity = session.query(UserIdentity).filter(
            UserIdentity.type == type,
            UserIdentity.value == value,
        ).first()
        return identity.user_id if identity else None
    finally:
        session.close()
