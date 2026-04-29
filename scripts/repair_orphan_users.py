"""
Repair: najde usery bez zadne aktivni tenant membership a pripoji je
do tenantu invitora.

Pouziti (po uprave invitation_service.py):
  python -m poetry run python scripts/repair_orphan_users.py

Co dela:
  1. Projde vsechny aktivni usery bez UserTenant (nebo jen s invited/archived).
  2. Pokud maji invited_by_user_id, prida je jako 'member' do tenantu invitora
     (invitor.last_active_tenant_id v momente pozvani -- proxy).
  3. Jinak preskoci a jen zaloguje (budeme muset rucne).

Bezpecne: neduplikuje, jen pridava chybejici.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import get_session
from modules.core.infrastructure.models_core import User, UserTenant


def main() -> None:
    session = get_session()
    try:
        users = session.query(User).filter(User.status == "active").all()
        fixed = 0
        skipped = 0

        for user in users:
            active_memberships = (
                session.query(UserTenant)
                .filter_by(user_id=user.id, membership_status="active")
                .count()
            )
            if active_memberships > 0:
                continue  # user je v poradku

            # Hledame tenant kam ho zaradit
            target_tenant_id = None
            if user.invited_by_user_id:
                inviter = session.query(User).filter_by(id=user.invited_by_user_id).first()
                if inviter and inviter.last_active_tenant_id:
                    target_tenant_id = inviter.last_active_tenant_id

            if not target_tenant_id:
                print(f"  SKIP user_id={user.id} ({user.first_name} {user.last_name}): nevim kam ho dat")
                skipped += 1
                continue

            # Check if membership row existuje (invited/inactive/archived)
            existing = (
                session.query(UserTenant)
                .filter_by(user_id=user.id, tenant_id=target_tenant_id)
                .first()
            )
            if existing:
                existing.membership_status = "active"
                existing.updated_at = datetime.now(timezone.utc)
                print(f"  ACTIVATE user_id={user.id} ({user.first_name} {user.last_name}) "
                      f"-> tenant_id={target_tenant_id} (existing row flipped to active)")
            else:
                ut = UserTenant(
                    user_id=user.id,
                    tenant_id=target_tenant_id,
                    role="member",
                    membership_status="active",
                    joined_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(ut)
                print(f"  ADD  user_id={user.id} ({user.first_name} {user.last_name}) "
                      f"-> tenant_id={target_tenant_id} (new UserTenant)")

            if not user.last_active_tenant_id:
                user.last_active_tenant_id = target_tenant_id

            fixed += 1

        session.commit()
        print(f"\n== HOTOVO ==  opraveno: {fixed},  preskoceno: {skipped}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
