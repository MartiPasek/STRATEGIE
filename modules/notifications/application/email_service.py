"""
Email service přes Exchange Web Services (EWS).
Používá knihovnu exchangelib.

Po fázi 5a (persona_channels) podporuje:
  - send_email(to, subject, body, persona_id=None, tenant_id=None)
      pouziva creds z persona_channels pokud persona_id. Pokud kanal
      chybi, fallback na globalni .env EWS (backward compat).
  - _get_account(email, password, server) prijma parametry, fallback
    na settings.ews_* pokud None.

Migrace existujicich pozvanek / password-reset emailu:
  send_invitation_email / send_password_reset_email dnes volaji send_email
  bez persona_id -> fallback na global -> funguje jak pred. Tyhle funkce
  posilaji "systemove" emaily (ne jmenem persony), takze global is fine.
"""
from __future__ import annotations

from core.config import settings
from core.logging import get_logger

logger = get_logger("notifications.email")


def _get_account(email: str | None = None, password: str | None = None, server: str | None = None):
    """
    Vytvori EWS pripojeni. Pokud nejsou parametry predany, fallback na
    settings.ews_* (backward compat pro pozvanky/password-reset).
    """
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    import urllib3
    urllib3.disable_warnings()

    ews_email = email or settings.ews_email
    ews_password = password or settings.ews_password
    ews_server = server or settings.ews_server

    if not ews_email or not ews_password or not ews_server:
        raise RuntimeError(
            "EWS credentials chybi. Bud nastavte v .env (EWS_EMAIL/EWS_PASSWORD/EWS_SERVER), "
            "nebo predejte persona_id s nakonfigurovanym persona_channels kanalem."
        )

    credentials = Credentials(
        username=ews_email,
        password=ews_password,
    )

    config = Configuration(
        server=ews_server.replace("https://", "").replace("http://", ""),
        credentials=credentials,
    )

    account = Account(
        primary_smtp_address=ews_email,
        config=config,
        autodiscover=False,
        access_type=DELEGATE,
    )
    return account


def _resolve_email_creds(persona_id: int | None, tenant_id: int | None) -> dict[str, str] | None:
    """
    Vrati dict {email, password, server} pokud persona_id ma kanal,
    jinak None -> _get_account dela fallback na settings.
    Oddelene aby bylo jednoduse testovat.
    """
    if not persona_id:
        return None
    try:
        from modules.notifications.application.persona_channel_service import (
            get_email_credentials,
        )
        return get_email_credentials(persona_id, tenant_id=tenant_id)
    except Exception as e:
        logger.error(
            f"EMAIL | creds resolve failed | persona_id={persona_id} | error={e}"
        )
        return None


# ── Specificke vyjimky pro jemnejsi error handling v callerech ────────────

class EmailAuthError(RuntimeError):
    """EWS server odmitl prihlasovaci udaje (spatny email/heslo/MFA chybi)."""


class EmailSendError(RuntimeError):
    """Obecna chyba pri odesilani emailu (connection, server-side, ...)."""


def _is_auth_error(exc: Exception) -> bool:
    """
    Rozpozna, zda je exception od exchangelib auth selhani.
    exchangelib.errors.UnauthorizedError je HTTP 401 pri EWS auth.
    Nekdy taky chodi ServerBusyError / RateLimitError pri brute-force
    ochranne; ty neblokujeme jako auth fail.
    """
    try:
        from exchangelib.errors import UnauthorizedError
        if isinstance(exc, UnauthorizedError):
            return True
    except ImportError:
        pass
    msg = str(exc).lower()
    # Fallback textova detekce (pro pripad jinych verzi exchangelib)
    return "invalid credentials" in msg or "unauthorized" in msg or "401" in msg


def send_email_or_raise(
    to: str,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Odesle email. V pripade selhani hodi EmailAuthError (spatne udaje)
    nebo EmailSendError (ostatni). Pri uspechu vraci None.
    """
    try:
        from exchangelib import Message, Mailbox

        creds = _resolve_email_creds(persona_id, tenant_id)
        if creds:
            account = _get_account(
                email=creds["email"],
                password=creds["password"],
                server=creds["server"],
            )
            sender = creds["email"]
        else:
            # Fallback: globalni .env. Pro pozvanky / password-reset / backward compat.
            account = _get_account()
            sender = settings.ews_email

        message = Message(
            account=account,
            subject=subject,
            body=body,
            to_recipients=[Mailbox(email_address=to)],
        )
        message.send()

        logger.info(
            f"EMAIL | sent | from={sender} | to={to} | subject={subject}"
        )
    except Exception as e:
        if _is_auth_error(e):
            logger.error(f"EMAIL | auth-failed | to={to} | error={e}")
            raise EmailAuthError(str(e)) from e
        logger.error(f"EMAIL | failed | to={to} | error={e}")
        raise EmailSendError(str(e)) from e


def send_email(
    to: str,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
) -> bool:
    """
    Backward-compat wrapper: vrati True pri uspechu, False pri selhani.
    Chyba jde do logu. Pro jemnejsi error handling (auth vs. jine) pouzij
    send_email_or_raise().
    """
    try:
        send_email_or_raise(to, subject, body, persona_id=persona_id, tenant_id=tenant_id)
        return True
    except (EmailAuthError, EmailSendError):
        return False
    except Exception as e:
        logger.error(f"EMAIL | unexpected | to={to} | error={e}")
        return False


def send_invitation_email(
    to: str,
    invited_by: str,
    token: str,
    invitee_first_name: str | None = None,
    invitee_gender: str | None = None,
) -> bool:
    """
    Odešle pozvánkový email do STRATEGIE.
    Base URL ze settings.app_base_url (nactene z .env pres pydantic-settings).
    Pro production deploy nastavit APP_BASE_URL=https://app.strategie-system.com.

    Pokud známe křestní jméno pozvaného (invitee_first_name), použij ho v oslovení
    ve vokativu podle rodu — pozvaný tak hned vidí, že ho systém zná a oslovuje
    ho česky správně ("Ahoj Kláro," místo "Ahoj Klára,").
    """
    from shared.czech import to_vocative
    from core.config import settings

    base_url = settings.app_base_url.rstrip("/")
    link = f"{base_url}/invite/{token}"

    vocative = to_vocative(invitee_first_name, invitee_gender).strip()
    greeting = f"Ahoj {vocative}," if vocative else "Ahoj,"

    subject = f"{invited_by} tě pozval do STRATEGIE"
    body = f"""{greeting}

{invited_by} tě pozval do systému STRATEGIE.

STRATEGIE je AI platforma pro práci, komunikaci a rozhodování v týmu.

Pro vstup klikni na tento odkaz:
{link}

Odkaz je platný 48 hodin.

S pozdravem,
Tým STRATEGIE
"""
    return send_email(to=to, subject=subject, body=body)


def send_password_reset_email(
    to: str,
    token: str,
    first_name: str | None = None,
    gender: str | None = None,
) -> bool:
    """
    Odesle email s linkem pro obnovu hesla. Link je platny 60 minut,
    jednorazovy. Pokud uzivatel o reset nezadal, nemusi delat nic --
    token si sam vyprsi a lze ho rovnou ignorovat.
    """
    from shared.czech import to_vocative
    from core.config import settings

    base_url = settings.app_base_url.rstrip("/")
    link = f"{base_url}/reset/{token}"

    vocative = to_vocative(first_name, gender).strip() if first_name else ""
    greeting = f"Ahoj {vocative}," if vocative else "Ahoj,"

    subject = "Obnovení hesla — STRATEGIE"
    body = f"""{greeting}

někdo (pravděpodobně ty) požádal o obnovu hesla k tvému účtu v systému STRATEGIE.

Klikni na tento odkaz pro nastavení nového hesla:
{link}

Odkaz je platný 60 minut a dá se použít jen jednou.

Pokud jsi o reset nežádal, ignoruj tento email. Tvoje současné heslo zůstává v platnosti, nikdo se k tvému účtu nedostal.

S pozdravem,
Tým STRATEGIE
"""
    return send_email(to=to, subject=subject, body=body)
