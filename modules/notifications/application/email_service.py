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


def send_invitation_email(to: str, invited_by: str, token: str) -> bool:
    """
    Odešle pozvánkový email do STRATEGIE.
    """
    link = f"http://localhost:8001/invite/{token}"

    subject = f"{invited_by} tě pozval do STRATEGIE"
    body = f"""Ahoj,

{invited_by} tě pozval do systému STRATEGIE.

STRATEGIE je AI platforma pro práci, komunikaci a rozhodování v týmu.

Pro vstup klikni na tento odkaz:
{link}

Odkaz je platný 48 hodin.

S pozdravem,
Tým STRATEGIE
"""
    return send_email(to=to, subject=subject, body=body)
