"""
Email service přes Exchange Web Services (EWS).
Používá knihovnu exchangelib.
"""
from core.config import settings
from core.logging import get_logger

logger = get_logger("notifications.email")



def _get_account():
    """Vytvoří EWS připojení k Exchange serveru."""    
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    import urllib3
    urllib3.disable_warnings()

    credentials = Credentials(
        username=settings.ews_email,
        password=settings.ews_password,
    )

    config = Configuration(
        server=settings.ews_server.replace("https://", "").replace("http://", ""),
        credentials=credentials,
    )

    account = Account(
        primary_smtp_address=settings.ews_email,
        config=config,
        autodiscover=False,
        access_type=DELEGATE,
    )
    return account


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Odešle email přes EWS.
    Vrátí True při úspěchu, False při selhání.
    """
    try:
        from exchangelib import Message, Mailbox

        account = _get_account()

        message = Message(
            account=account,
            subject=subject,
            body=body,
            to_recipients=[Mailbox(email_address=to)],
        )
        message.send()

        logger.info(f"EMAIL | sent | to={to} | subject={subject}")
        return True

    except Exception as e:
        logger.error(f"EMAIL | failed | to={to} | error={e}")
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
