"""
User context helper — sdílený mezi /login a /me.

Vrátí kompletní obraz o uživateli + jeho aktuálním tenantovém kontextu.
Pokud něco chybí (např. user_tenant_profile nebo tenant), použije se
fallback (first_name, "—", apod.).
"""
from sqlalchemy.orm import Session

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    User, UserContact, UserAlias,
    Tenant, UserTenant, UserTenantProfile,
)

logger = get_logger("auth.user_context")


def get_user_context(user_id: int) -> dict | None:
    """
    Vrátí dict pro LoginResponse / /me.

    Klíče:
      user_id, first_name, last_name, email, tenant_id,
      display_name, tenant_name, tenant_code, aliases (list[str])

    Vrátí None pokud user neexistuje nebo není active.

    Logika tenantu:
      - Bere users.last_active_tenant_id
      - Pokud None, vezme první aktivní user_tenants
      - Profile (user_tenant_profiles) je optional — fallback na first_name
    """
    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            return None

        # Primární email (pro display, nemusí být v této chvíli unikátní u
        # mírnějšího indexu, ale typicky bude jen jeden primary)
        primary_contact = (
            session.query(UserContact)
            .filter_by(user_id=user_id, contact_type="email", is_primary=True, status="active")
            .first()
        )
        # Fallback — kterýkoli aktivní email
        if primary_contact is None:
            primary_contact = (
                session.query(UserContact)
                .filter_by(user_id=user_id, contact_type="email", status="active")
                .first()
            )
        email_value = primary_contact.contact_value if primary_contact else ""

        # Tenant — last_active_tenant_id, jinak první aktivní membership
        tenant_id = user.last_active_tenant_id
        if tenant_id is None:
            ut = (
                session.query(UserTenant)
                .filter_by(user_id=user_id, membership_status="active")
                .order_by(UserTenant.id.asc())
                .first()
            )
            if ut:
                tenant_id = ut.tenant_id
                user.last_active_tenant_id = tenant_id
                session.commit()

        tenant_name = None
        tenant_code = None
        display_name = None

        if tenant_id is not None:
            tenant = session.query(Tenant).filter_by(id=tenant_id, status="active").first()
            if tenant:
                tenant_name = tenant.tenant_name
                tenant_code = tenant.tenant_code

                # Profile pro tento tenant (přes user_tenants)
                ut = (
                    session.query(UserTenant)
                    .filter_by(user_id=user_id, tenant_id=tenant_id)
                    .first()
                )
                if ut:
                    profile = (
                        session.query(UserTenantProfile)
                        .filter_by(user_tenant_id=ut.id)
                        .first()
                    )
                    if profile:
                        display_name = profile.display_name

        # Aliasy — primary first, ostatní seřazené podle ID
        aliases_rows = (
            session.query(UserAlias)
            .filter_by(user_id=user_id, status="active")
            .order_by(UserAlias.is_primary.desc(), UserAlias.id.asc())
            .all()
        )
        aliases = [a.alias_value for a in aliases_rows]

        # Všechny aktivní tenanty, jichž je user členem — pro dropdown
        available_tenants = _list_user_tenants(session, user_id)

        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": email_value,
            "tenant_id": tenant_id,
            "gender": user.gender,
            "short_name": user.short_name,
            "display_name": display_name or user.first_name,    # fallback
            "tenant_name": tenant_name,
            "tenant_code": tenant_code,
            "aliases": aliases,
            "available_tenants": available_tenants,
        }
    finally:
        session.close()


def _list_user_tenants(session: Session, user_id: int) -> list[dict]:
    """Vrátí všechny aktivní tenanty usera, abecedně podle tenant_name."""
    rows = (
        session.query(Tenant)
        .join(UserTenant, UserTenant.tenant_id == Tenant.id)
        .filter(
            UserTenant.user_id == user_id,
            UserTenant.membership_status == "active",
            Tenant.status == "active",
        )
        .order_by(Tenant.tenant_name.asc())
        .all()
    )
    return [
        {
            "tenant_id": t.id,
            "tenant_name": t.tenant_name,
            "tenant_code": t.tenant_code,
            "tenant_type": t.tenant_type,
        }
        for t in rows
    ]
