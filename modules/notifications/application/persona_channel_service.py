"""
Persona channel service -- nacitani a uprava komunikacnich kanalu persony.

Typicke pouziti:
  creds = get_email_credentials(persona_id, tenant_id)
  # -> {"email": "marti-ai@eurosoft.com", "password": "xxx", "server": "..."}
  # Nebo None pokud persona nema nakonfigurovany email kanal.

Per-tenant fallback:
  Hleda se prvne (persona_id, tenant_id) match. Pokud neni, fallback na
  (persona_id, tenant_id=NULL) = globalni kanal. Pokud ani to neni, None.
"""
from __future__ import annotations
from typing import Any

from core.database_core import get_core_session
from core.logging import get_logger
from core.crypto import decrypt_optional, encrypt, CryptoDecryptError
from modules.core.infrastructure.models_core import PersonaChannel

logger = get_logger("notifications.persona_channels")


def get_channel(
    persona_id: int,
    channel_type: str,
    tenant_id: int | None = None,
    fallback_to_global: bool = True,
) -> PersonaChannel | None:
    """
    Vrati primarni kanal dane persony daneho typu. Nejdriv hleda per-tenant,
    pak globalni (tenant_id=NULL) fallback.

    channel_type: "email" | "phone"
    """
    cs = get_core_session()
    try:
        # 1) Per-tenant primarni
        if tenant_id is not None:
            c = (
                cs.query(PersonaChannel)
                .filter_by(
                    persona_id=persona_id,
                    channel_type=channel_type,
                    tenant_id=tenant_id,
                    is_enabled=True,
                    is_primary=True,
                )
                .first()
            )
            if c:
                return c

        # 2) Globalni primarni
        if fallback_to_global:
            c = (
                cs.query(PersonaChannel)
                .filter_by(
                    persona_id=persona_id,
                    channel_type=channel_type,
                    tenant_id=None,
                    is_enabled=True,
                    is_primary=True,
                )
                .first()
            )
            if c:
                return c

        # 3) Jakekoliv enabled (backup, kdyz nikdo nenastavil is_primary)
        c = (
            cs.query(PersonaChannel)
            .filter_by(
                persona_id=persona_id,
                channel_type=channel_type,
                is_enabled=True,
            )
            .order_by(PersonaChannel.id.asc())
            .first()
        )
        return c
    finally:
        cs.close()


def get_email_credentials(
    persona_id: int,
    tenant_id: int | None = None,
) -> dict[str, str] | None:
    """
    Vrati dict s EWS credentialy pro personu:
      {
        "email": str,         # UPN / login -- pouzit k autentizaci
        "display_email": str, # Co prezentovat (SMTP alias) -- fallback na email
        "password": str,
        "server": str,
      }
    nebo None kdyz kanal neni nakonfigurovany.
    Desifruje heslo pres Fernet.
    """
    ch = get_channel(persona_id, "email", tenant_id=tenant_id)
    if not ch:
        return None
    if not ch.credentials_encrypted:
        logger.warning(
            f"CHANNELS | email | persona_id={persona_id} ma kanal bez kredence"
        )
        return None
    try:
        password = decrypt_optional(ch.credentials_encrypted)
    except CryptoDecryptError as e:
        logger.error(f"CHANNELS | email | decrypt failed | persona_id={persona_id}: {e}")
        return None
    return {
        "email": ch.identifier,
        "display_email": ch.display_identifier or ch.identifier,
        "password": password or "",
        "server": ch.server or "",
    }


def upsert_email_channel(
    persona_id: int,
    email: str,
    password: str,
    server: str,
    display_email: str | None = None,
    tenant_id: int | None = None,
    is_primary: bool = True,
) -> dict[str, Any]:
    """
    Vytvori nebo aktualizuje email kanal persony. Heslo se zasifruje.

    email         = login UPN (na co se prihlasujeme na Exchange)
    display_email = co prezentujeme navenek (primary SMTP alias). Pokud
                    None, pouzije se `email`.
    """
    cs = get_core_session()
    try:
        existing = (
            cs.query(PersonaChannel)
            .filter_by(
                persona_id=persona_id,
                tenant_id=tenant_id,
                channel_type="email",
                is_primary=True,
            )
            .first()
        )
        encrypted = encrypt(password)
        if existing:
            existing.identifier = email
            existing.display_identifier = display_email
            existing.credentials_encrypted = encrypted
            existing.server = server
            existing.is_enabled = True
            cs.commit()
            cs.refresh(existing)
            row = existing
            action = "updated"
        else:
            row = PersonaChannel(
                persona_id=persona_id,
                tenant_id=tenant_id,
                channel_type="email",
                identifier=email,
                display_identifier=display_email,
                credentials_encrypted=encrypted,
                server=server,
                is_primary=is_primary,
                is_enabled=True,
            )
            cs.add(row)
            cs.commit()
            cs.refresh(row)
            action = "created"

        logger.info(
            f"CHANNELS | email | {action} | persona_id={persona_id} | "
            f"tenant_id={tenant_id} | login={email} | display={display_email or email}"
        )
        return {
            "id": row.id,
            "persona_id": row.persona_id,
            "tenant_id": row.tenant_id,
            "channel_type": row.channel_type,
            "identifier": row.identifier,
            "display_identifier": row.display_identifier,
            "server": row.server,
            "is_primary": row.is_primary,
            "is_enabled": row.is_enabled,
            "action": action,
        }
    finally:
        cs.close()
