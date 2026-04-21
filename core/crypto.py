"""
Symetricke sifrovani kredencialu (Fernet / AES-128-CBC + HMAC).

Pouziti: EWS hesla v `persona_channels.credentials_encrypted` a budouci
`user_channels`. Klic je v settings.encryption_key (.env ENCRYPTION_KEY),
nikdy necommituj do gitu.

Format: encrypt(plaintext: str) -> str (base64url token), decrypt(token) -> str.

Rotace klice: zatim manualne (napsat helper skript co dekriptuje starym,
encryptuje novym). Az to bude rutina, muzeme pridat `encryption_key_prev`
pro kratkodobou rotaci (dekriptuj oba, encryptuj novym).
"""
from __future__ import annotations
from core.config import settings

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as e:
    # bcrypt pulls cryptography transitively, ale pro jistotu pridame
    # aspon hezkou hlasku v pripade ze to nekdy zmizi z venv.
    raise ImportError(
        "cryptography nenalezeno -- `pip install cryptography` nebo "
        "`poetry add cryptography` (obvykle je transitivne pres bcrypt)"
    ) from e


class CryptoConfigError(RuntimeError):
    """ENCRYPTION_KEY v .env chybi, je prazdny, nebo ma spatny format."""


class CryptoDecryptError(RuntimeError):
    """Sifrovane data nelze dekryptovat (spatny klic nebo porusena data)."""


_fernet_cache: Fernet | None = None


def _get_fernet() -> Fernet:
    """Vrati Fernet instanci s aktualnim klicem ze settings. Caches globalne."""
    global _fernet_cache
    if _fernet_cache is not None:
        return _fernet_cache

    key = (settings.encryption_key or "").strip()
    if not key:
        raise CryptoConfigError(
            "ENCRYPTION_KEY chybi v .env. Vygeneruj pres:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
            "a pridej do .env jako ENCRYPTION_KEY=..."
        )

    try:
        _fernet_cache = Fernet(key.encode())
    except Exception as e:
        raise CryptoConfigError(
            f"ENCRYPTION_KEY ma spatny format (ocekava 32 bytu base64url): {e}"
        ) from e

    return _fernet_cache


def encrypt(plaintext: str) -> str:
    """Zasifruje retezec. Vrati base64url token (str)."""
    if plaintext is None:
        raise ValueError("encrypt: plaintext cannot be None")
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(ciphertext: str) -> str:
    """Desifruje token. Raise CryptoDecryptError pri spatnem klici nebo corruptu."""
    if not ciphertext:
        raise ValueError("decrypt: ciphertext cannot be empty")
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise CryptoDecryptError(
            "Nelze dekryptovat -- spatny ENCRYPTION_KEY, nebo poskozena data. "
            "(pokud jsi menil klic v .env, hesla v DB jsou zasifrovana starym)"
        ) from e


def encrypt_optional(plaintext: str | None) -> str | None:
    """Nullable wrapper -- pokud je plaintext None, vrati None."""
    if plaintext is None:
        return None
    return encrypt(plaintext)


def decrypt_optional(ciphertext: str | None) -> str | None:
    """Nullable wrapper -- pokud je ciphertext None, vrati None."""
    if ciphertext is None:
        return None
    return decrypt(ciphertext)
