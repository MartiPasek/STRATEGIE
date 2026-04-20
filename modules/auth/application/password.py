"""
Password hashing utility.

Používáme bcrypt (konzistentní s Caddy Basic Auth vrstvou a industry standard).
Hash je 60 znaků, prefix $2b$12$... s 12 cost rounds -- pár desítek ms na
verify na moderním CPU, dost na zabrzdění brute-force i při úniku hash DB.

API:
    hash_password(plain)          -> str        # bcrypt hash
    verify_password(plain, hash)  -> bool       # timing-safe compare

Bezpečnostní poznámky:
- bcrypt.hashpw vyžaduje bytes na vstupu (UTF-8 encoding tady).
- bcrypt.checkpw je timing-safe -> žádný risk timing attacku.
- Max délka hesla u bcrypt je 72 bytes; delší se interně ořeže. Pro našich
  uživatelů irrelevantní, ale enforce minimum 8 znaků na aplikační vrstvě.
"""
from __future__ import annotations

import bcrypt


BCRYPT_ROUNDS = 12  # ~100-300 ms na verify; přijatelný UX × brute-force cost
MIN_PASSWORD_LENGTH = 8


class PasswordTooShort(ValueError):
    """Heslo je kratší než MIN_PASSWORD_LENGTH."""


def hash_password(plain: str) -> str:
    """Zahashuje heslo bcryptem s BCRYPT_ROUNDS cost.

    Raises:
        PasswordTooShort: pokud plain < MIN_PASSWORD_LENGTH znaků.
    """
    if plain is None or len(plain) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShort(
            f"Heslo musí mít alespoň {MIN_PASSWORD_LENGTH} znaků."
        )
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str | None) -> bool:
    """Ověří heslo proti uloženému hashi. Timing-safe.

    Returns False pro libovolný malformed hash nebo None -- callers tak
    můžou bezpečně volat i pro usery bez nastaveného hesla (NULL v DB).
    """
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed hash v DB -- nesmí shodit login, jen failne verify.
        return False
