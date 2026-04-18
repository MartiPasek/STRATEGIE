"""
Invitation service — vytváření a validace pozvánek.
"""
import secrets
from datetime import datetime, timezone, timedelta

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserIdentity, UserTenant, Invitation

logger = get_logger("auth.invitation")

TOKEN_EXPIRY_HOURS = 48


def create_invitation(
    email: str,
    invited_by_user_id: int,
    tenant_id: int,
    role: str = "member",
) -> str:
    """
    Vytvoří pozvánku pro nového uživatele.
    Pokud uživatel existuje, přidá ho do tenantu.
    Vrátí token pro pozvánkový link.
    """
    session = get_core_session()
    try:
        # Zjisti jestli uživatel už existuje
        existing_identity = session.query(UserIdentity).filter_by(
            type="email", value=email.strip().lower()
        ).first()

        if existing_identity:
            user_id = existing_identity.user_id
            logger.info(f"INVITATION | existing user | user_id={user_id}")
        else:
            # Vytvoř nového pending uživatele
            user = User(
                status="pending",
                invited_by_user_id=invited_by_user_id,
                invited_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.flush()

            identity = UserIdentity(
                user_id=user.id,
                type="email",
                value=email.strip().lower(),
                is_primary=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(identity)
            user_id = user.id
            logger.info(f"INVITATION | new user created | user_id={user_id}")

        # Vytvoř token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

        invitation = Invitation(
            user_id=user_id,
            email=email.strip().lower(),
            token=token,
            expires_at=expires_at,
            requires_sms_verification=False,  # MVP: bez SMS
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
    """
    Přijme pozvánku a aktivuje uživatele.
    Vrátí user data nebo None pokud token není platný.
    """
    session = get_core_session()
    try:
        invitation = session.query(Invitation).filter_by(token=token).first()

        if not invitation:
            logger.warning(f"INVITATION | token not found")
            return None

        if invitation.expires_at < datetime.now(timezone.utc):
            logger.warning(f"INVITATION | token expired")
            return None

        user = session.query(User).filter_by(id=invitation.user_id).first()
        if not user:
            return None

        # Aktivuj uživatele
        user.status = "active"
        session.commit()

        identity = session.query(UserIdentity).filter_by(
            user_id=user.id, type="email"
        ).first()

        logger.info(f"INVITATION | accepted | user_id={user.id}")
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": identity.value if identity else "",
            "tenant_id": user.last_active_tenant_id,
        }

    finally:
        session.close()
