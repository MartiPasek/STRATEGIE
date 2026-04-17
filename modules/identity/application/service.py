from core.database import get_db_session
from core.logging import get_logger
from modules.identity.infrastructure.models import User, UserIdentity

logger = get_logger("identity")

# MVP typy identit
ALLOWED_IDENTITY_TYPES = {"email", "phone"}


def create_user() -> str:
    """
    Vytvoří nového uživatele bez identit.
    Vrátí jeho UUID.
    """
    session = get_db_session()
    try:
        user = User()
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"IDENTITY | user created | id={user.id}")
        return user.id
    finally:
        session.close()


def add_identity(
    user_id: str,
    type: str,
    value: str,
    is_primary: bool = False,
) -> str:
    """
    Přidá identitu (email nebo phone) k uživateli.
    Vrátí UUID nové identity.
    Raises ValueError při neznámém typu nebo duplicitní hodnotě.
    """
    if type not in ALLOWED_IDENTITY_TYPES:
        raise ValueError(f"Unknown identity type '{type}'. Allowed: {ALLOWED_IDENTITY_TYPES}")

    session = get_db_session()
    try:
        # Kontrola duplicity před insertem
        existing = session.query(UserIdentity).filter_by(type=type, value=value).first()
        if existing:
            raise ValueError(f"Identity {type}='{value}' already exists for user {existing.user_id}")

        identity = UserIdentity(
            user_id=user_id,
            type=type,
            value=value,
            is_primary=is_primary,
        )
        session.add(identity)
        session.commit()
        session.refresh(identity)
        logger.info(f"IDENTITY | identity added | user_id={user_id} | type={type}")
        return identity.id
    finally:
        session.close()


def find_user_by_identity(type: str, value: str) -> str | None:
    """
    Najde uživatele podle identity (email nebo phone).
    Vrátí user_id nebo None.
    """
    session = get_db_session()
    try:
        identity = session.query(UserIdentity).filter_by(type=type, value=value).first()
        return identity.user_id if identity else None
    finally:
        session.close()
