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
from modules.auth.application.user_context import get_user_context
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

        user_id = user.id
    finally:
        session.close()

    # Po login úspěchu vrátíme PLNÝ kontext (display_name, tenant_code, aliases…)
    # přes shared helper. Tím se /login a /me chovají symetricky.
    ctx = get_user_context(user_id)
    if ctx is None:
        return None
    logger.info(
        f"AUTH | login success | user_id={ctx['user_id']} | tenant_id={ctx['tenant_id']}"
    )
    return ctx
