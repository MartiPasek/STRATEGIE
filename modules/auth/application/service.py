"""
Auth service po identity refaktoru v2.

Login flow:
  1. Najdi user_contacts WHERE contact_type='email' AND contact_value=:email
                              AND status='active' (case insensitive)
  2. 0 výsledků → None (UI vrátí 401 'Email nenalezen')
  3. 2+ výsledků → AmbiguousEmail exception (router vrátí 401 s jasnou zprávou)
  4. SELECT users WHERE id=:user_id AND status='active'
  5. Pokud users.last_active_tenant_id NULL → vezmi první aktivní user_tenants
"""
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User, UserContact, UserTenant

logger = get_logger("auth")


class AmbiguousEmailError(Exception):
    """Email odpovídá víc než jednomu aktivnímu uživateli — kontaktuj admina."""


def login_by_email(email: str) -> dict | None:
    """
    Jednoduchý login přes email. MVP: bez hesla.
    Vrátí user data nebo None pokud uživatel neexistuje / není aktivní.
    Při ambiguous match vyhodí AmbiguousEmailError.
    """
    needle = email.strip().lower()
    session = get_core_session()
    try:
        contacts = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .all()
        )

        if not contacts:
            logger.warning(f"AUTH | login failed (no contact) | email={email}")
            return None

        if len(contacts) > 1:
            logger.error(
                f"AUTH | login ambiguous | email={email} | "
                f"matches={len(contacts)} | user_ids={[c.user_id for c in contacts]}"
            )
            raise AmbiguousEmailError(
                f"Email '{email}' používá více účtů. Kontaktuj admina."
            )

        contact = contacts[0]
        user = session.query(User).filter_by(id=contact.user_id).first()
        if not user or user.status != "active":
            logger.warning(f"AUTH | user inactive | email={email}")
            return None

        # Fallback pro tenant_id: pokud user nemá last_active_tenant_id,
        # vezmi první aktivní member ship.
        tenant_id = user.last_active_tenant_id
        if tenant_id is None:
            ut = (
                session.query(UserTenant)
                .filter_by(user_id=user.id, membership_status="active")
                .order_by(UserTenant.id.asc())
                .first()
            )
            if ut:
                tenant_id = ut.tenant_id
                user.last_active_tenant_id = tenant_id
                session.commit()

        logger.info(f"AUTH | login success | user_id={user.id} | tenant_id={tenant_id}")
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": contact.contact_value,
            "tenant_id": tenant_id,
        }
    finally:
        session.close()
