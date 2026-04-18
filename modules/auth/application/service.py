from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserIdentity

logger = get_logger("auth")


def login_by_email(email: str) -> dict | None:
    """
    Jednoduchý login přes email.
    MVP: bez hesla, bez SMS — jen ověření existence v DB.
    Vrátí user data nebo None pokud uživatel neexistuje.
    """
    session = get_core_session()
    try:
        identity = session.query(UserIdentity).filter(
            UserIdentity.type == "email",
            UserIdentity.value == email.strip().lower()
        ).first()


        if not identity:
            logger.warning(f"AUTH | login failed | email={email}")
            return None

        user = session.query(User).filter_by(id=identity.user_id).first()
        if not user or user.status != "active":
            logger.warning(f"AUTH | user inactive | email={email}")
            return None

        logger.info(f"AUTH | login success | user_id={user.id}")
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": email,
            "tenant_id": user.last_active_tenant_id,
        }
    finally:
        session.close()
