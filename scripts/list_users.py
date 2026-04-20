"""
Vypise aktivni usery a jejich emaily. Slouzi k identifikaci spravneho
loginu pred spustenim set_initial_passwords.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database_core import get_core_session
from modules.core.infrastructure.models_core import User, UserContact


def main() -> None:
    session = get_core_session()
    try:
        users = session.query(User).filter_by(status="active").order_by(User.id).all()
        if not users:
            print("Zadni aktivni useri.")
            return
        print(f"\nAktivni useri ({len(users)}):\n")
        print(f"{'ID':>4}  {'Jmeno':<25}  {'Heslo':<12}  Emaily")
        print("-" * 90)
        for u in users:
            contacts = (
                session.query(UserContact)
                .filter_by(user_id=u.id, contact_type="email", status="active")
                .all()
            )
            emails = ", ".join(c.contact_value for c in contacts) or "(zadny)"
            name = " ".join(filter(None, [u.first_name, u.last_name])) or "(no name)"
            has_pwd = "[ma heslo]" if u.password_hash else "[BEZ hesla]"
            print(f"  {u.id:>3}  {name:<25}  {has_pwd:<12}  {emails}")
        print()
    finally:
        session.close()


if __name__ == "__main__":
    main()
