"""
Seed skript — vytvoří prvního uživatele (Marti) v css_db.
Spustit jednou: python scripts/seed_first_user.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from core.database_core import get_core_session
from modules.core.infrastructure.models_core import (
    User, UserIdentity, Tenant, UserTenant, Project, UserProject
)


def seed():
    session = get_core_session()
    try:
        # 1. Najdi tenant EUROSOFT
        tenant = session.query(Tenant).filter_by(name="EUROSOFT").first()
        if not tenant:
            print("ERROR: Tenant EUROSOFT nenalezen. Spusť nejdřív seed dat v psql.")
            return

        # 2. Vytvoř uživatele Marti
        existing = session.query(UserIdentity).filter_by(
            type="email", value="m.pasek@eurosoft.com"
        ).first()

        if existing:
            print(f"Uživatel už existuje: user_id={existing.user_id}")
            return

        user = User(
            status="active",
            first_name="Marti",
            last_name="Pašek",
            last_active_tenant_id=tenant.id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.flush()  # získáme user.id

        # 3. Přidej email identitu
        identity = UserIdentity(
            user_id=user.id,
            type="email",
            value="m.pasek@eurosoft.com",
            is_primary=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(identity)

        # 4. Propoj s tenantem jako owner
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=tenant.id,
            role="owner",
            created_at=datetime.now(timezone.utc),
        )
        session.add(user_tenant)

        # 5. Vytvoř default projekt pro tenant
        project = session.query(Project).filter_by(
            tenant_id=tenant.id, name="Default"
        ).first()

        if not project:
            project = Project(
                tenant_id=tenant.id,
                name="Default",
                owner_user_id=user.id,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(project)
            session.flush()

        # 6. Přidej uživatele do projektu
        user_project = UserProject(
            user_id=user.id,
            project_id=project.id,
            role="owner",
            created_at=datetime.now(timezone.utc),
        )
        session.add(user_project)

        session.commit()

        print(f"✓ Uživatel vytvořen: id={user.id}, email=m.pasek@eurosoft.com")
        print(f"✓ Tenant: EUROSOFT (id={tenant.id})")
        print(f"✓ Projekt: Default (id={project.id})")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
