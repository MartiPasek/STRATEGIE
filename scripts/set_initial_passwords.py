"""
Admin nástroj -- nastav hesla stávajícím userům, kteří přešli z passwordless MVP.

Použití:
    python scripts/set_initial_passwords.py

Vypíše seznam aktivních userů, prosí o heslo pro každého (interaktivně,
neuvidíš co píšeš), zahashuje bcryptem a uloží do users.password_hash.

Můžeš preskočit usera (Enter bez hesla) -- jeho password_hash zůstane NULL
a login mu poteká s 403 PasswordNotSet, dokud mu heslo nenastavíš.

Bezpečnostní poznámky:
- Heslo se nikdy nelogguje ani neukládá nikam jinam než jako bcrypt hash.
- Heslo musí mít aspoň MIN_PASSWORD_LENGTH (8) znaků.
- Při zadávání se nezobrazuje (getpass).
- Po skončení skriptu doporuč ihned otestovat login.
"""
from __future__ import annotations

import getpass
import sys
from datetime import datetime, timezone

# Ensure project root on PYTHONPATH (script is in scripts/, model code je v modules/)
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database_core import get_core_session
from modules.auth.application.password import hash_password, PasswordTooShort, MIN_PASSWORD_LENGTH
from modules.core.infrastructure.models_core import User, UserContact


def list_active_users() -> list[tuple[User, str]]:
    """Vrátí list (user, primary_email) aktivních userů, seřazené podle id."""
    session = get_core_session()
    try:
        users = session.query(User).filter_by(status="active").order_by(User.id).all()
        # Vytáhni primary email pro každého (z user_contacts)
        result: list[tuple[User, str]] = []
        for u in users:
            contact = (
                session.query(UserContact)
                .filter_by(user_id=u.id, contact_type="email", status="active")
                .order_by(UserContact.is_primary.desc(), UserContact.id.asc())
                .first()
            )
            email = contact.contact_value if contact else "(no email)"
            result.append((u, email))
        return result
    finally:
        session.close()


def set_password_for_user(user_id: int, plain_password: str) -> None:
    """Zahashuje a uloží heslo. Aktualizuje password_set_at."""
    h = hash_password(plain_password)
    session = get_core_session()
    try:
        u = session.query(User).filter_by(id=user_id).first()
        if not u:
            raise ValueError(f"User {user_id} neexistuje.")
        u.password_hash = h
        u.password_set_at = datetime.now(timezone.utc)
        session.commit()
    finally:
        session.close()


def prompt_password_twice(prompt_label: str) -> str | None:
    """Zeptá se dvakrát, vrátí heslo nebo None pokud user preskočí (prazdne)."""
    while True:
        p1 = getpass.getpass(f"{prompt_label} (Enter = preskoc): ")
        if not p1:
            return None
        p2 = getpass.getpass("Zopakuj heslo: ")
        if p1 != p2:
            print("  ! Hesla se neshoduji, zkus znovu.")
            continue
        if len(p1) < MIN_PASSWORD_LENGTH:
            print(f"  ! Heslo musi mit aspon {MIN_PASSWORD_LENGTH} znaku.")
            continue
        return p1


def main() -> None:
    print("=" * 60)
    print("STRATEGIE -- set initial passwords")
    print("=" * 60)
    users = list_active_users()
    if not users:
        print("Zadni aktivni useri.")
        return

    print(f"\nNalezeno {len(users)} aktivnich userů:\n")
    for u, email in users:
        name = " ".join(filter(None, [u.first_name, u.last_name])) or "(no name)"
        has_pwd = "[ma heslo]" if u.password_hash else "[BEZ hesla]"
        print(f"  #{u.id:>3}  {name:30s}  {email:35s}  {has_pwd}")

    print("\nZadej heslo pro kazdeho usera (nebo Enter pro preskoceni).\n")

    set_count = 0
    skip_count = 0
    for u, email in users:
        name = " ".join(filter(None, [u.first_name, u.last_name])) or email
        label = f"  Heslo pro #{u.id} {name}"
        plain = prompt_password_twice(label)
        if plain is None:
            print(f"  -> preskoceno (#{u.id}).")
            skip_count += 1
            continue
        try:
            set_password_for_user(u.id, plain)
            print(f"  -> hash ulozen (#{u.id}).")
            set_count += 1
        except PasswordTooShort as e:
            print(f"  ! {e}")
        except Exception as e:
            print(f"  ! Chyba pri ukladani: {e}")

    print(f"\nHotovo. Nastaveno: {set_count}. Preskoceno: {skip_count}.")
    print("Doporuceni: hned otestuj login pres https://app.strategie-system.com")


if __name__ == "__main__":
    main()
