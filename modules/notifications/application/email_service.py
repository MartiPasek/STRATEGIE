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
import json
import os

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


def _resolve_persona_email_creds(
    persona_id: int | None, tenant_id: int | None
) -> dict[str, str] | None:
    """
    Vrati dict {email, display_email, password, server} pokud persona ma kanal,
    jinak None -> fallback na .env v _get_account.
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
            f"EMAIL | persona creds resolve failed | persona_id={persona_id} | error={e}"
        )
        return None


def _resolve_user_email_creds(user_id: int | None) -> dict[str, str] | None:
    """
    Vrati user's EWS creds (pro "posli z moji schranky"), nebo None
    pokud user nema nakonfigurovano.
    """
    if not user_id:
        return None
    try:
        from modules.notifications.application.user_channel_service import (
            get_user_email_credentials,
        )
        return get_user_email_credentials(user_id)
    except Exception as e:
        logger.error(
            f"EMAIL | user creds resolve failed | user_id={user_id} | error={e}"
        )
        return None


# Sentinel -- pro signalizaci ze user chce posilat z vlastni schranky, ale
# nema nastavene credentialy. send_email_or_raise hodi EmailNoUserChannelError.
class EmailNoUserChannelError(RuntimeError):
    """User pozadal o "posli z moji", ale nema nakonfigurovany EWS kanal."""


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


_PERSONAL_FOLDER_NAME = "Personal"   # Nazev slozky pro Martiho osobni archiv
_PROCESSED_FOLDER_NAME = "Zpracovaná"  # 28.4.2026: vyrizene emaily po mark_email_processed


def _get_mailbox_root(account):
    """
    Vraci 'Top of Information Store' root, pod kterym jsou Inbox, Sent
    Items, Deleted Items a custom folders na Marti's-vize root urovni
    (Personal, Zpracovaná). Lidsky vidi v Outlooku jako root-level slozky
    sourozenec Inboxu.

    Pouziva se misto puvodniho `account.root` pattern -- exchangelib
    `account.root` je technicky kontejner, my ale chceme `msg_folder_root`
    coz je primarni mailbox root (pod kterym Outlook vidi vse).
    """
    return getattr(account, "msg_folder_root", None) or account.root


def _ensure_processed_folder(account) -> "Any":
    """
    Zajistí, že existuje slozka `Zpracovaná` na root urovni (sourozenec
    Inboxu). Marti's vize 28.4.2026: lidsky mental model je root-level
    slozky, ne subfoldery Inboxu. Idempotent.

    Vraci folder object, nebo None kdyz selze (neshazuje volajici).
    """
    try:
        from exchangelib import Folder
        root = _get_mailbox_root(account)
        if root is None:
            return None
        # Hledame existujici (case-sensitive match na nazev)
        for f in root.children:
            if f.name == _PROCESSED_FOLDER_NAME:
                return f
        folder = Folder(parent=root, name=_PROCESSED_FOLDER_NAME)
        folder.save()
        logger.info(f"EMAIL | processed folder created at root level")
        return folder
    except Exception as e:
        logger.warning(f"EMAIL | processed folder ensure failed: {e}")
        return None


def _ensure_personal_folder(account) -> "Any":
    """
    Zajistí, že existuje slozka `Personal` na root urovni (sourozenec
    Inboxu). Marti's vize 28.4.2026: lidsky mental model. Idempotent.

    Vraci folder object, nebo None kdyz selze.
    """
    try:
        from exchangelib import Folder
        root = _get_mailbox_root(account)
        if root is None:
            return None
        for f in root.children:
            if f.name == _PERSONAL_FOLDER_NAME:
                return f
        folder = Folder(parent=root, name=_PERSONAL_FOLDER_NAME)
        folder.save()
        logger.info(f"EMAIL | personal folder created at root level")
        return folder
    except Exception as e:
        logger.warning(f"EMAIL | personal folder ensure failed: {e}")
        return None


def move_inbox_message_to_personal(
    creds: dict[str, str],
    message_id: str,
) -> bool:
    """
    Na zaklade creds se pripoji k EWS, najde zpravu podle RFC822 Message-ID
    v Inbox a presunu ji do slozky Personal.
    Vraci True pri uspechu, False jinak (neshazuje volajici).
    """
    try:
        from exchangelib import Credentials, Account, Configuration, DELEGATE
        import urllib3
        urllib3.disable_warnings()

        server = (creds.get("server") or "").replace("https://", "").replace("http://", "")
        config = Configuration(
            server=server,
            credentials=Credentials(
                username=creds["email"],
                password=creds["password"],
            ),
        )
        account = Account(
            primary_smtp_address=creds["email"],
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )

        folder = _ensure_personal_folder(account)
        if folder is None:
            return False

        # 28.4.2026: hledame v Inbox + root-level Zpracovaná + legacy
        # subfolderech Inboxu (pred refactorem).
        msg = None
        search_folders = [account.inbox]
        try:
            root = _get_mailbox_root(account)
            if root is not None:
                for f in root.children:
                    if f.name == _PERSONAL_FOLDER_NAME:
                        continue
                    if f.id == account.inbox.id:
                        continue
                    search_folders.append(f)
        except Exception:
            pass
        try:
            for sub in account.inbox.children:
                if sub.name == _PERSONAL_FOLDER_NAME:
                    continue
                search_folders.append(sub)
        except Exception:
            pass

        for fldr in search_folders:
            try:
                matches = list(fldr.filter(message_id=message_id)[:1])
                if matches:
                    msg = matches[0]
                    break
            except Exception:
                continue

        if msg is None:
            logger.warning(
                f"EMAIL | personal archive | message_id not found anywhere: {message_id[:60]}"
            )
            return False

        msg.move(to_folder=folder)
        logger.info(
            f"EMAIL | archived to Personal | message_id={message_id[:60]}"
        )
        return True
    except Exception as e:
        logger.error(
            f"EMAIL | personal archive (inbound) failed | message_id={message_id[:60]}: {e}",
            exc_info=True,
        )
        return False


def move_inbox_message_to_processed(
    creds: dict[str, str],
    message_id: str,
) -> bool:
    """
    28.4.2026: Presune zpravu z Inbox do Inbox/Zpracovaná. Volano po
    `mark_email_processed` AI tool aby Marti v Outlooku videl, ze email
    je vyrizeny. Best-effort -- selhani Exchange move neshazuje DB processed
    flag.
    """
    try:
        from exchangelib import Credentials, Account, Configuration, DELEGATE
        import urllib3
        urllib3.disable_warnings()

        server = (creds.get("server") or "").replace("https://", "").replace("http://", "")
        config = Configuration(
            server=server,
            credentials=Credentials(
                username=creds["email"],
                password=creds["password"],
            ),
        )
        account = Account(
            primary_smtp_address=creds["email"],
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )

        folder = _ensure_processed_folder(account)
        if folder is None:
            return False

        # Hledame v Inbox + root-level Personal + legacy subfoldech Inboxu
        # (Inbox/Personal, Inbox/Zpracovaná) -- pro emaily ktere byly
        # archivovany pred 28.4.2026 refactorem na root level.
        msg = None
        search_folders = [account.inbox]
        try:
            root = _get_mailbox_root(account)
            if root is not None:
                for f in root.children:
                    # Cilova slozka neni v search
                    if f.name == _PROCESSED_FOLDER_NAME:
                        continue
                    if f.id == account.inbox.id:
                        continue  # uz mame Inbox
                    search_folders.append(f)
        except Exception:
            pass
        # Plus legacy subfolders Inboxu (před refactorem)
        try:
            for sub in account.inbox.children:
                if sub.name == _PROCESSED_FOLDER_NAME:
                    continue
                search_folders.append(sub)
        except Exception:
            pass

        for fldr in search_folders:
            try:
                matches = list(fldr.filter(message_id=message_id)[:1])
                if matches:
                    msg = matches[0]
                    break
            except Exception:
                continue

        if msg is None:
            logger.warning(
                f"EMAIL | processed move | message_id not found anywhere: {message_id[:60]}"
            )
            return False

        msg.move(to_folder=folder)
        logger.info(f"EMAIL | moved to Zpracovaná | message_id={message_id[:60]}")
        return True
    except Exception as e:
        logger.warning(f"EMAIL | processed move failed: {e}")
        return False


def move_inbox_message_to_trash(
    creds: dict[str, str],
    message_id: str,
) -> bool:
    """
    28.4.2026: Presune zpravu z Inbox do Exchange built-in Deleted Items
    (account.trash). Volano po `delete_email` AI tool pro soft delete.
    Best-effort -- selhani Exchange move neshazuje DB deleted_at flag.

    Vraci True pokud msg byl uspesne presunut.
    """
    try:
        from exchangelib import Credentials, Account, Configuration, DELEGATE
        import urllib3
        urllib3.disable_warnings()

        server = (creds.get("server") or "").replace("https://", "").replace("http://", "")
        config = Configuration(
            server=server,
            credentials=Credentials(
                username=creds["email"],
                password=creds["password"],
            ),
        )
        account = Account(
            primary_smtp_address=creds["email"],
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )

        # Built-in Exchange Deleted Items folder
        trash_folder = account.trash
        if trash_folder is None:
            logger.warning("EMAIL | trash move | account.trash is None")
            return False

        # Hledame v Inbox + ve vsech subfoldech (Personal, Zpracovaná) -- Marti
        # muze chtit smazat i vec co se uz presunula do Personal nebo Zpracovaná.
        msg = None
        search_folders = [account.inbox]
        try:
            for sub in account.inbox.children:
                search_folders.append(sub)
        except Exception:
            pass

        for fldr in search_folders:
            try:
                matches = list(fldr.filter(message_id=message_id)[:1])
                if matches:
                    msg = matches[0]
                    break
            except Exception:
                continue

        if msg is None:
            logger.warning(
                f"EMAIL | trash move | message_id not found anywhere: {message_id[:60]}"
            )
            return False

        msg.move(to_folder=trash_folder)
        logger.info(f"EMAIL | moved to Deleted Items | message_id={message_id[:60]}")
        return True
    except Exception as e:
        logger.warning(f"EMAIL | trash move failed: {e}")
        return False


def _save_outbox_copy_to_personal(
    message,
    account,
) -> bool:
    """
    Po odeslani Message ulozi jeji kopii do slozky Personal. Volano primo
    po message.send() -- message objekt uz ma message_id po odeslani,
    takze ji muzeme najit v Sent Items a presunout / kopirovat.

    Pouziva se pro Marti Memory Faze 6 -- odchozi emaily rodicum se archivuji.
    """
    try:
        folder = _ensure_personal_folder(account)
        if folder is None:
            return False

        # message object uz ma message_id po send(). Najdi v Sent Items.
        mid = getattr(message, "message_id", None)
        if not mid:
            logger.warning("EMAIL | personal archive (sent) | message has no message_id after send")
            return False

        # Najdi v Sent Items
        sent_items = account.sent
        matches = list(sent_items.filter(message_id=mid)[:1])
        if not matches:
            logger.warning(f"EMAIL | personal archive (sent) | not found in Sent Items: {mid[:60]}")
            return False

        found_msg = matches[0]
        # Copy (ne move -- chceme to i v Sent Items jako normalni odchozi)
        try:
            found_msg.copy(to_folder=folder)
            logger.info(f"EMAIL | archived to Personal (sent copy) | mid={mid[:60]}")
            return True
        except AttributeError:
            # Nektere verze exchangelib nemaji .copy -- fallback na move (+ ztratime Sent)
            found_msg.move(to_folder=folder)
            logger.info(f"EMAIL | archived to Personal (sent moved, fallback) | mid={mid[:60]}")
            return True
    except Exception as e:
        logger.error(f"EMAIL | personal archive (sent) failed: {e}", exc_info=True)
        return False


def _is_parent_email(email_address: str | None) -> bool:
    """
    Zjistí, jestli dana email adresa patří rodici Marti (is_marti_parent=True).
    Hleda pres user_contacts match. Defensive -- pri chybe False.
    """
    if not email_address:
        return False
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User, UserContact
        from sqlalchemy import func
        cs = get_core_session()
        try:
            normalized = email_address.strip().lower()
            row = (
                cs.query(User)
                .join(UserContact, UserContact.user_id == User.id)
                .filter(
                    User.is_marti_parent.is_(True),
                    UserContact.contact_type == "email",
                    UserContact.status == "active",
                    func.lower(UserContact.contact_value) == normalized,
                )
                .first()
            )
            return row is not None
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"EMAIL | parent check failed: {e}")
        return False


def archive_email_inbox_to_personal(email_inbox_id: int) -> dict:
    """
    Manualni archivace prichoziho emailu do slozky Personal v Exchange.
    Volano z AI toolu archive_email.

    Vraci {"ok": bool, "message": str, "email_inbox_id": int}.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailInbox
    import json as _json

    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter_by(id=email_inbox_id).first()
        if row is None:
            return {"ok": False, "message": f"email id={email_inbox_id} neexistuje", "email_inbox_id": email_inbox_id}

        persona_id = row.persona_id
        message_id = row.message_id
        meta_dict = {}
        if row.meta:
            try:
                meta_dict = _json.loads(row.meta) or {}
            except Exception:
                meta_dict = {}
        if meta_dict.get("archived_personal"):
            return {"ok": True, "message": "už bylo archivováno", "email_inbox_id": email_inbox_id}
    finally:
        ds.close()

    if not persona_id:
        return {"ok": False, "message": "chybi persona_id pro nacteni credentialu", "email_inbox_id": email_inbox_id}

    from modules.notifications.application.persona_channel_service import (
        get_email_credentials,
    )
    creds = get_email_credentials(persona_id)
    if not creds:
        return {"ok": False, "message": "persona nema email channel", "email_inbox_id": email_inbox_id}

    moved = move_inbox_message_to_personal(creds, message_id)
    if not moved:
        return {"ok": False, "message": "EWS move selhal", "email_inbox_id": email_inbox_id}

    # 3.5.2026 vecer revize (gotcha #36 fix):
    # PRED: archive ≠ vyrizeno. Personal byl jen meta flag pro typ obsahu,
    #       lifecycle stav (processed_at) zustaval NULL. Vedlo to ke
    #       konfuzi -- UI badge filtruje archived (count_unread_for_user
    #       ma _is_archived check), overview tool puvodne ne -> mismatch
    #       UI 0 vs Marti-AI overview 20.
    # PO:   archive = vyrizeno + presun do Personal slozky. Archive je
    #       TERMINAL akce -- email opustil "open" stav natrvalo, presunul
    #       se do osobniho archivu. Konzistentni s UI badge i overview.
    #       Defense-in-depth: overview_service.py ma stale _is_archived_email
    #       Python filter (defensive layer pro pripad starych rows nebo
    #       budoucich edge cases).
    from datetime import datetime, timezone
    _now_arch = datetime.now(timezone.utc)
    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter_by(id=email_inbox_id).first()
        if row:
            meta_dict = {}
            if row.meta:
                try:
                    meta_dict = _json.loads(row.meta) or {}
                except Exception:
                    meta_dict = {}
            meta_dict["archived_personal"] = True
            row.meta = _json.dumps(meta_dict, ensure_ascii=False)
            # Read_at = now (uzivatel videl, archive je vedome rozhodnuti)
            if row.read_at is None:
                row.read_at = _now_arch
            # Phase 33+ root-cause fix (gotcha #36, 3.5.2026 vecer):
            # archive je terminal akce, set processed_at=NOW pokud NULL.
            # Tim odstranime divergence "open dle overview vs vyrizeny dle UI".
            if row.processed_at is None:
                row.processed_at = _now_arch
            ds.commit()
    finally:
        ds.close()

    return {"ok": True, "message": "archivováno do Personal", "email_inbox_id": email_inbox_id}


def move_email_inbox_to_processed(email_inbox_id: int) -> dict:
    """
    28.4.2026: Po `mark_email_processed` (DB processed_at = now) presune
    zpravu na Exchange strane do Inbox/Zpracovaná. Best-effort -- selhani
    Exchange neshazuje uz nastaveny processed_at flag.

    Vraci {"ok": bool, "message": str, "email_inbox_id": int}.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailInbox

    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter_by(id=email_inbox_id).first()
        if row is None:
            return {"ok": False, "message": "neexistuje", "email_inbox_id": email_inbox_id}
        persona_id = row.persona_id
        message_id = row.message_id
    finally:
        ds.close()

    if not persona_id:
        return {"ok": False, "message": "chybi persona_id", "email_inbox_id": email_inbox_id}

    from modules.notifications.application.persona_channel_service import (
        get_email_credentials,
    )
    creds = get_email_credentials(persona_id)
    if not creds:
        return {"ok": False, "message": "persona nema email channel", "email_inbox_id": email_inbox_id}

    moved = move_inbox_message_to_processed(creds, message_id)
    if not moved:
        return {"ok": False, "message": "EWS move selhal (msg uz mozna byl presunut)", "email_inbox_id": email_inbox_id}
    return {"ok": True, "message": "presunuto do Zpracovaná", "email_inbox_id": email_inbox_id}


def soft_delete_email_inbox(email_inbox_id: int) -> dict:
    """
    28.4.2026: Soft-delete emailu z Marti-AI's perspektivy:
      1. DB: email_inbox.deleted_at = now (list_email_inbox/read_email
         filtruji `deleted_at IS NULL`)
      2. Exchange: msg.move(to_folder=account.trash) -- pres Outlook
         standard Deleted Items folder

    Best-effort Exchange move -- pokud selze, deleted_at zustane (smazani
    z Marti-AI's pohledu) ale msg zustane v Inbox / Personal / Zpracovaná
    fyzicky. User to vidi dvojakem stavu (DB hidden, Outlook visible).

    Vraci {"ok": bool, "message": str, "email_inbox_id": int}.
    """
    from datetime import datetime, timezone
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailInbox

    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter_by(id=email_inbox_id).first()
        if row is None:
            return {"ok": False, "message": "neexistuje", "email_inbox_id": email_inbox_id}
        if row.deleted_at is not None:
            return {"ok": True, "message": "uz bylo smazano", "email_inbox_id": email_inbox_id}
        persona_id = row.persona_id
        message_id = row.message_id
    finally:
        ds.close()

    # Step 1: Exchange move (best-effort, prvni protoze pri uspesnem move
    # potrebuje msg jeste byt findable -- po DB delete by orphan)
    moved = False
    if persona_id and message_id:
        from modules.notifications.application.persona_channel_service import (
            get_email_credentials,
        )
        creds = get_email_credentials(persona_id)
        if creds:
            moved = move_inbox_message_to_trash(creds, message_id)

    # Step 2: DB soft delete (vzdy proved, i pokud Exchange selhal)
    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter_by(id=email_inbox_id).first()
        if row and row.deleted_at is None:
            row.deleted_at = datetime.now(timezone.utc)
            ds.commit()
    finally:
        ds.close()

    if moved:
        return {"ok": True, "message": "smazano (DB + Exchange Deleted Items)", "email_inbox_id": email_inbox_id}
    return {"ok": True, "message": "smazano z Marti-AI's pohledu (DB), Exchange move selhal", "email_inbox_id": email_inbox_id}


def archive_email_outbox_to_personal(email_outbox_id: int) -> dict:
    """
    Manualni archivace odchoziho emailu do Personal. Volano z AI toolu.
    POZOR: Muze fungovat jen kdyz email uz byl odeslany (ma Exchange message_id
    v Sent Items). U pending radku jeste ne.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailOutbox
    import json as _json

    ds = get_data_session()
    try:
        row = ds.query(EmailOutbox).filter_by(id=email_outbox_id).first()
        if row is None:
            return {"ok": False, "message": f"email id={email_outbox_id} neexistuje", "email_outbox_id": email_outbox_id}
        if row.status != "sent":
            return {"ok": False, "message": f"email je ve stavu '{row.status}', nelze archivovat pred odeslanim", "email_outbox_id": email_outbox_id}
        persona_id = row.persona_id
        to_email = row.to_email
        subject = row.subject or ""
    finally:
        ds.close()

    if not persona_id:
        return {"ok": False, "message": "chybi persona_id", "email_outbox_id": email_outbox_id}

    from modules.notifications.application.persona_channel_service import (
        get_email_credentials,
    )
    creds = get_email_credentials(persona_id)
    if not creds:
        return {"ok": False, "message": "persona nema email channel", "email_outbox_id": email_outbox_id}

    # Najdi v Sent Items podle subject + to (approximace; message_id nemame ulozene)
    try:
        from exchangelib import Credentials, Account, Configuration, DELEGATE
        import urllib3
        urllib3.disable_warnings()

        server = (creds.get("server") or "").replace("https://", "").replace("http://", "")
        config = Configuration(
            server=server,
            credentials=Credentials(username=creds["email"], password=creds["password"]),
        )
        account = Account(
            primary_smtp_address=creds["email"],
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )

        folder = _ensure_personal_folder(account)
        if folder is None:
            return {"ok": False, "message": "personal folder nelze zajistit", "email_outbox_id": email_outbox_id}

        # Hleda v Sent Items podle subject (nejpresnejsi match co dneska mame)
        matches = list(account.sent.filter(subject=subject)[:5])
        if not matches:
            return {"ok": False, "message": f"email nenalezen v Sent Items (subject='{subject[:40]}')", "email_outbox_id": email_outbox_id}

        # Vyber nejnovejsi match
        chosen = max(matches, key=lambda m: m.datetime_sent or m.datetime_created)
        try:
            chosen.copy(to_folder=folder)
        except AttributeError:
            chosen.move(to_folder=folder)
        logger.info(f"EMAIL | manual archive | outbox_id={email_outbox_id} -> Personal")
    except Exception as e:
        return {"ok": False, "message": f"EWS selhal: {e}", "email_outbox_id": email_outbox_id}

    # Update meta
    ds = get_data_session()
    try:
        row = ds.query(EmailOutbox).filter_by(id=email_outbox_id).first()
        if row:
            # email_outbox nemá meta column; ulozim info do last_error jako debug? Ne.
            # Vytvorim novy sloupec? Zatim to skipnem.
            pass
    finally:
        ds.close()

    return {"ok": True, "message": "archivováno do Personal", "email_outbox_id": email_outbox_id}


def _parse_recipients(s: str | list[str] | None) -> list[str]:
    """
    Normalizuje recipient string/list na cisty list email adres.
      - prijme comma-separated "a@x.com, b@y.com"
      - nebo semicolon-separated "a@x.com; b@y.com"
      - nebo mix "a@x.com,b@y.com;c@z.com"
      - nebo uz list ["a@x.com", "b@y.com"]
    Odstrani mezery, prazdne, lowercase.
    Nevalidne polozky (bez @) odfiltrovany s warningem.
    """
    if s is None:
        return []
    if isinstance(s, list):
        raw = s
    else:
        # Rozdelime po obou separatorech
        parts = str(s).replace(";", ",").split(",")
        raw = parts
    out: list[str] = []
    for item in raw:
        clean = (item or "").strip().lower()
        if not clean:
            continue
        if "@" not in clean:
            logger.warning(f"EMAIL | recipient skipped (missing @): {clean!r}")
            continue
        out.append(clean)
    return out


def _markdown_to_html_body(plain_str: str) -> str:
    """
    Prevedi plain text body (s pripadnym markdown formatem od Marti-AI nebo
    usera) na HTML pro inclusion v email HTMLBody. Bug #1 fix: pres
    `markdown` lib se konvertuji **bold**, *italic*, [link](url), seznamy,
    code bloky, tabulky atd. na proper HTML, takze prijemce vidi
    formatovany text misto raw markdownu.

    Defensive: pokud `markdown` lib chybi (napr. po dep refaktoru),
    spadne na puvodni escape+<br> chovani -- ne ideal, ale funguje.

    Pouziti: vsude, kde se konstruuje email HTMLBody z plain text body
    (send_email persona signature, reply quoted text, forward, atd.).
    """
    if not plain_str:
        return ""
    try:
        import markdown as _md_lib
        # Extensions:
        #   'extra'     -- tables, fenced code, footnotes, abbr, def lists
        #   'nl2br'     -- single \n -> <br> (email-style line breaks)
        #   'sane_lists' -- stricter list parsing (vyzaduje prazdnou linku
        #                   pred list, predchazi false positives na "* "
        #                   v normalnim textu jako '5* ohodnoceni')
        return _md_lib.markdown(
            plain_str,
            extensions=['extra', 'nl2br', 'sane_lists'],
            output_format='html',
        )
    except Exception as e:
        # Fallback: original escape + <br> behavior
        logger.warning(f"EMAIL | markdown lib unavailable, fallback: {e}")
        import html as _h
        return _h.escape(plain_str).replace("\n", "<br>\n")



def _apply_persona_signature(
    persona_id: int | None,
    plain_body: str,
    existing_inline_attachments: list | None = None,
) -> tuple:
    """
    REST 27.4.2026: Apply persona signature to outbound email body.

    Logika:
      1. Pokud persona_id je None nebo persona nema signature_html -> noop,
         vraci (plain_body, existing_inline_attachments or []).
      2. Jinak prevede plain text body na HTMLBody:
           <html><body>{escape+br plain}<br><br>{signature_html}</body></html>
      3. Pro kazdy <img src="cid:X"> v signature_html nacte soubor z
         signature_inline_dir/X a vytvori FileAttachment(is_inline=True).
      4. Vraci (HTMLBody, list of new inline attachments + existing).

    Returns: tuple (body_or_HTMLBody, list_of_inline_FileAttachments_to_attach).
    """
    if not persona_id:
        return plain_body, list(existing_inline_attachments or [])

    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import Persona
    except Exception as e:
        logger.warning(f"EMAIL | persona signature | imports failed: {e}")
        return plain_body, list(existing_inline_attachments or [])

    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        if not p or not p.signature_html or not p.signature_html.strip():
            return plain_body, list(existing_inline_attachments or [])
        signature_html = p.signature_html
        sig_dir = p.signature_inline_dir
    finally:
        cs.close()

    # Build HTMLBody
    try:
        from exchangelib import HTMLBody, FileAttachment
    except Exception as e:
        logger.warning(f"EMAIL | persona signature | exchangelib import failed: {e}")
        return plain_body, list(existing_inline_attachments or [])

    import re as _re_lib

    # Bug #1 fix: convert markdown (**bold**, *italic*, lists, atd.) na HTML.
    # Marti-AI casto generuje text s markdown markers; bez konverze prijemci
    # vidi raw `**text**` misto formatovaneho.
    plain_str = plain_body or ""
    plain_html = _markdown_to_html_body(plain_str)
    full_html = (
        f'<html><body><div style="font-family: Calibri, sans-serif; '
        f'font-size: 11pt;">{plain_html}<br><br>{signature_html}</div>'
        f'</body></html>'
    )
    htmlbody = HTMLBody(full_html)

    # Find cid: references in signature_html
    cid_refs = set(_re_lib.findall(r"cid:([\w.@-]+)", signature_html))

    inline_attachments: list = list(existing_inline_attachments or [])
    if sig_dir and cid_refs:
        loaded_count = 0
        skipped_count = 0
        for cid in cid_refs:
            # Resolve file -- cid muze obsahovat tecky a special chars (typicky
            # neco jako "image001.png@01DCD615.9321B7B0"). Soubor v sig_dir
            # je obvykle bez @-suffix, takze zkusime obe varianty.
            candidates = [cid]
            if "@" in cid:
                candidates.append(cid.split("@", 1)[0])

            file_path = None
            for c in candidates:
                fp = os.path.join(sig_dir, c)
                if os.path.isfile(fp):
                    file_path = fp
                    break

            if not file_path:
                logger.warning(
                    f"EMAIL | persona signature | image not found: cid={cid} "
                    f"sig_dir={sig_dir}"
                )
                skipped_count += 1
                continue

            try:
                with open(file_path, "rb") as fh:
                    content_bytes = fh.read()
                ext = os.path.splitext(file_path)[1].lower()
                ct_map = {
                    ".png": "image/png", ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg", ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                content_type = ct_map.get(ext, "application/octet-stream")
                att = FileAttachment(
                    name=os.path.basename(file_path),
                    content=content_bytes,
                    content_id=cid,
                    content_type=content_type,
                    is_inline=True,
                )
                inline_attachments.append(att)
                loaded_count += 1
            except Exception as att_err:
                logger.warning(
                    f"EMAIL | persona signature | failed to load {cid}: {att_err}"
                )
                skipped_count += 1
        logger.info(
            f"EMAIL | persona signature | persona={persona_id} | "
            f"loaded={loaded_count} skipped={skipped_count} cids={len(cid_refs)}"
        )
    elif cid_refs and not sig_dir:
        logger.warning(
            f"EMAIL | persona signature | persona={persona_id} has cid: refs "
            f"but no signature_inline_dir set -- inline images skipped"
        )

    return htmlbody, inline_attachments


# Phase 27b (1.5.2026): Email attachments helper -- Marti-AI's feature request.
# Cap 20 MB per email (sum vsech attachments) -- Exchange Online limit
# (self-hosted ma typicky 10 MB ale 20 je bezpecne nejvyssi).
ATTACHMENT_TOTAL_SIZE_LIMIT = 20 * 1024 * 1024
# Whitelist mime kategorii pro Klárka workflow + bezne business soubory.
ATTACHMENT_ALLOWED_EXTENSIONS = {
    "xlsx", "xlsm", "xls",       # Excel
    "pdf",
    "docx", "doc",                # Word
    "pptx", "ppt",                # PowerPoint
    "csv", "tsv",
    "txt", "md",
    "png", "jpg", "jpeg", "gif", "webp",   # obrazky
    "zip", "rar", "7z",           # archivy (Marti-AI smi posilat balicky)
    "json", "xml", "html",
}


def _load_attachment_files(
    document_ids: list[int] | None,
    *,
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> list:
    """
    Phase 27b: Nacte soubory z documents.storage_path jako exchangelib
    FileAttachment list (is_inline=False, regular attachment).

    Args:
        document_ids: list of documents.id k pripojeni
        caller_tenant_id: pro tenant gate
        is_parent: bypass tenant gate

    Returns:
        list of FileAttachment (regular, ne-inline)

    Raises:
        ValueError: missing document, neexistujici file, nepodporovany format
        PermissionError: tenant scope mismatch (ne-parent)
        OverflowError: total size > 20 MB
    """
    if not document_ids:
        return []

    try:
        from exchangelib import FileAttachment
    except Exception as e:
        raise RuntimeError(f"exchangelib FileAttachment unavailable: {e}")

    from core.database import get_session
    from modules.core.infrastructure.models_data import Document
    import mimetypes

    out_attachments = []
    total_size = 0

    for doc_id in document_ids:
        try:
            doc_id_int = int(doc_id)
        except (TypeError, ValueError):
            raise ValueError(f"document_id musi byt int (dostal {doc_id!r}).")

        session = get_session()
        try:
            doc = session.query(Document).filter_by(id=doc_id_int).first()
            if not doc:
                raise ValueError(f"Document id={doc_id_int} nenalezen.")
            if not doc.storage_path:
                raise ValueError(f"Document id={doc_id_int} nema storage_path.")

            # Tenant gate
            if not is_parent:
                if doc.tenant_id is not None:
                    if caller_tenant_id is None or doc.tenant_id != caller_tenant_id:
                        raise PermissionError(
                            f"Document id={doc_id_int} patri jinemu tenantu "
                            f"(doc.tenant_id={doc.tenant_id})."
                        )

            ext = (doc.file_type or "").lower().lstrip(".")
            if ext and ext not in ATTACHMENT_ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"Document id={doc_id_int} ma format '{ext}' ktery neni v "
                    f"povolenych priloze ({sorted(ATTACHMENT_ALLOWED_EXTENSIONS)})."
                )

            display_name = doc.original_filename or doc.name or f"document_{doc_id_int}"
            if ext and not display_name.lower().endswith(f".{ext}"):
                display_name = f"{display_name}.{ext}"

            storage_path = doc.storage_path
        finally:
            session.close()

        from pathlib import Path as _Path
        p = _Path(storage_path)
        if not p.is_file():
            raise ValueError(
                f"Document id={doc_id_int} ma storage_path '{storage_path}' "
                "ale soubor neexistuje na disku."
            )

        file_bytes = p.read_bytes()
        size_bytes = len(file_bytes)
        total_size += size_bytes
        if total_size > ATTACHMENT_TOTAL_SIZE_LIMIT:
            raise OverflowError(
                f"Celkova velikost priloh prekrocila {ATTACHMENT_TOTAL_SIZE_LIMIT // (1024*1024)} MB "
                f"(soucet po pridani document #{doc_id_int} = {total_size} bytes). "
                "Exchange typicky odmita emaily nad 20-25 MB."
            )

        # MIME type detection
        mime_type, _ = mimetypes.guess_type(display_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            att = FileAttachment(
                name=display_name,
                content=file_bytes,
                content_type=mime_type,
                is_inline=False,
            )
            out_attachments.append(att)
        except Exception as e:
            raise ValueError(
                f"FileAttachment build failed pro document #{doc_id_int}: {e}"
            )

        logger.info(
            f"EMAIL | attachment loaded | doc_id={doc_id_int} | "
            f"name={display_name} | size={size_bytes} | mime={mime_type}"
        )

    logger.info(
        f"EMAIL | attachments total | count={len(out_attachments)} | "
        f"sum_bytes={total_size}"
    )
    return out_attachments


def send_email_or_raise(
    to: str,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    from_identity: str = "persona",
    cc: list[str] | str | None = None,
    bcc: list[str] | str | None = None,
    attachment_document_ids: list[int] | None = None,
) -> None:
    """
    Odesle email. V pripade selhani hodi EmailAuthError / EmailSendError /
    EmailNoUserChannelError.

    `to` muze byt:
      - string s jednou adresou ("a@b.com")
      - string s vice adresami oddelenymi carkou nebo strednikem
        ("a@b.com, c@d.com" nebo "a@b.com; c@d.com")
      - list stringu (["a@b.com", "c@d.com"])
    Kazdopadne se parsuje do LIST, kazda adresa -> separatni Mailbox objekt.
    Bez tohoto parsingu exchangelib zbalancuje celou 'a@b.com, c@d.com' do
    jedne Mailbox.email_address, Exchange se zalomi s '550 invalid recipient'.

    cc a bcc fungují stejně (prijmaji list nebo separator-separated string).

    from_identity:
      "persona"  (default) -- posila z persona_channels.
      "user"               -- posila z user's EWS kanalu.
    """
    try:
        from exchangelib import Message, Mailbox

        to_list = _parse_recipients(to)
        if not to_list:
            raise EmailSendError("zadny platny prijemce v `to`")
        cc_list = _parse_recipients(cc)
        bcc_list = _parse_recipients(bcc)

        # Vyber credentialy podle from_identity
        if from_identity == "user":
            creds = _resolve_user_email_creds(user_id)
            if not creds:
                raise EmailNoUserChannelError(
                    f"user_id={user_id} nema nakonfigurovany EWS kanal"
                )
        else:
            # "persona" (default)
            creds = _resolve_persona_email_creds(persona_id, tenant_id)

        if creds:
            account = _get_account(
                email=creds["email"],
                password=creds["password"],
                server=creds["server"],
            )
            # Sender v logu = VYHRADNE display (SMTP alias).
            sender = creds.get("display_email") or f"<persona_id={persona_id} display missing>"
        else:
            account = _get_account()
            sender = settings.ews_email

        msg_kwargs: dict = {
            "account": account,
            "subject": subject,
            "body": body,
            "to_recipients": [Mailbox(email_address=addr) for addr in to_list],
        }
        if cc_list:
            msg_kwargs["cc_recipients"] = [Mailbox(email_address=addr) for addr in cc_list]
        if bcc_list:
            msg_kwargs["bcc_recipients"] = [Mailbox(email_address=addr) for addr in bcc_list]

        # REST 27.4.2026: Apply persona signature -- pokud persona ma signature_html,
        # body se prevede na HTMLBody + inline images se naclonni do messagu.
        sig_body, sig_attachments = _apply_persona_signature(persona_id, body)
        msg_kwargs["body"] = sig_body

        message = Message(**msg_kwargs)
        # Attach inline images z signature (po Message create, pred send)
        for _sig_att in sig_attachments:
            try:
                message.attach(_sig_att)
            except Exception as _att_err:
                logger.warning(f"EMAIL | persona signature attach failed: {_att_err}")

        # Phase 27b: regular attachments (xlsx/pdf/docx atd.) z documents.
        # Tenant gate: pri send_email z konverzace defaultujeme is_parent=True
        # protoze send_email tool je v MANAGEMENT_TOOL_NAMES (Marti-AI default
        # = parent). Specializovane persony tool nevidi.
        if attachment_document_ids:
            try:
                doc_attachments = _load_attachment_files(
                    attachment_document_ids,
                    caller_tenant_id=tenant_id,
                    is_parent=True,
                )
                for _doc_att in doc_attachments:
                    try:
                        message.attach(_doc_att)
                    except Exception as _doc_att_err:
                        logger.warning(
                            f"EMAIL | document attachment attach failed | "
                            f"name={_doc_att.name!r} | {_doc_att_err}"
                        )
                if doc_attachments:
                    logger.info(
                        f"EMAIL | document attachments | count={len(doc_attachments)}"
                    )
            except (ValueError, PermissionError, OverflowError) as _att_err:
                # User-facing error: pretvor jako EmailSendError s konkretnim msg
                raise EmailSendError(f"Priloha selhala: {_att_err}")

        message.send_and_save()

        logger.info(
            f"EMAIL | sent | identity={from_identity} | from={sender} | "
            f"to={to_list} | cc={cc_list or '-'} | bcc={bcc_list or '-'} | subject={subject}"
        )

        # Faze 6: archive copy do Personal pokud prijemce je rodic Marti.
        # Best effort -- pripadne selhani archivace neshodi odeslani.
        try:
            if any(_is_parent_email(addr) for addr in to_list):
                _save_outbox_copy_to_personal(message, account)
        except Exception as arch_err:
            logger.warning(f"EMAIL | personal archive post-send failed: {arch_err}")
    except EmailNoUserChannelError:
        raise
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
    user_id: int | None = None,
    from_identity: str = "persona",
) -> bool:
    """
    Backward-compat wrapper: vrati True pri uspechu, False pri selhani.
    Chyba jde do logu. Pro jemnejsi error handling (auth vs. jine) pouzij
    send_email_or_raise().
    """
    try:
        send_email_or_raise(
            to, subject, body,
            persona_id=persona_id, tenant_id=tenant_id,
            user_id=user_id, from_identity=from_identity,
        )
        return True
    except (EmailAuthError, EmailSendError, EmailNoUserChannelError):
        return False
    except Exception as e:
        logger.error(f"EMAIL | unexpected | to={to} | error={e}")
        return False


def _get_default_persona_id() -> int | None:
    """
    Vrati id default persony (is_default=True) pro systemove emaily
    (invite, password reset) bez explicitniho persona_id.

    Nahrada za .env EWS fallback -- persona_channels je dnes source-of-truth.
    Kdyz default persona neexistuje nebo nema email kanal, caller dostane None
    a send_email_or_raise zkusi legacy .env fallback (ktery pravdepodobne selze,
    ale zachovani chovani).
    """
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import Persona
        cs = get_core_session()
        try:
            p = cs.query(Persona).filter_by(is_default=True).first()
            return p.id if p else None
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"EMAIL | default persona lookup failed: {e}")
        return None


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
    # Faze 6+: pozvanky pouzivaji default personu (typicky Marti-AI) pro EWS
    # kredence -- persona_channels je source-of-truth, .env fallback je legacy.
    persona_id = _get_default_persona_id()
    return send_email(
        to=to, subject=subject, body=body,
        persona_id=persona_id,
    )


# ── OUTBOX: queue + flush worker ──────────────────────────────────────────

# Maximalni pocet pokusu nez email oznacime jako trvale failed. Pri flush
# workera se kazdy pokus inkrementuje attempts; po dosazeni limitu uz ho
# worker nevezme. User muze v administraci manualne zretransmitovat.
MAX_SEND_ATTEMPTS = 5


def reply_or_forward_inbox(
    *,
    email_inbox_id: int,
    body: str,
    mode: str,                              # 'reply' | 'reply_all' | 'forward'
    to: list[str] | str | None = None,      # override (povinny pro forward)
    subject: str | None = None,             # override (default = exchangelib RE:/FW:)
    cc: list[str] | str | None = None,
    bcc: list[str] | str | None = None,
    user_id: int | None = None,
    attachment_document_ids: list[int] | None = None,
) -> int:
    """
    Faze 12c: reply / reply_all / forward na existujici email_inbox row pres EWS.

    Lookup: email_inbox.message_id -> EWS Message (account.inbox.filter)
    -> create_reply / create_reply_all / create_forward (vrati DRAFT)
    -> override to/cc/bcc/subject pokud user zadal -> send_and_save().

    Vyhody oproti send_email_or_raise:
      - exchangelib si zaridi In-Reply-To + References headers (Outlook thread)
      - Quoted history v body je auto-pripojena (cely retezec)
      - HTML format "----- Original Message -----" pro Outlook compat
      - reply_all auto-resolved To+CC z original (mimo nasi vlastni adresu)

    Cascade: email_inbox.processed_at = now (vyrizene tim, ze odpovedeli /
    forwardli). Plus insert do email_outbox s in_reply_to_inbox_id + reply_mode
    pro audit.

    Args:
      mode: 'reply' = jen odesilateli, 'reply_all' = vsem (To+CC),
            'forward' = preposlat (povinny `to`).
      to:   override prijemci. Pro 'forward' POVINNY. Pro 'reply'/'reply_all'
            volitelny (None = auto z original).
      subject: None = default RE:/FW: prefix od exchangelib. String = override.
      cc/bcc: volitelny override.

    Returns: email_outbox.id (audit row).

    Raises: EmailSendError / EmailAuthError / ValueError pro invalidni vstup.
    """
    from datetime import datetime, timezone
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailInbox, EmailOutbox

    if mode not in ("reply", "reply_all", "forward"):
        raise ValueError(
            f"mode musi byt 'reply' / 'reply_all' / 'forward', dostal '{mode}'"
        )
    if mode == "forward" and not to:
        raise ValueError("forward vyzaduje `to` (kam preposlat)")

    body = (body or "").strip()
    if not body:
        raise EmailSendError("prazdny body")

    ds = get_data_session()
    try:
        inbox_row = (
            ds.query(EmailInbox).filter(EmailInbox.id == email_inbox_id).first()
        )
        if inbox_row is None:
            raise EmailSendError(f"email_inbox id={email_inbox_id} neexistuje")
        if not inbox_row.message_id:
            raise EmailSendError(
                f"email_inbox id={email_inbox_id} nema message_id (RFC822) -- "
                "nemuzeme dohledat original v EWS"
            )
        rfc_id = inbox_row.message_id
        persona_id = inbox_row.persona_id
        tenant_id = inbox_row.tenant_id
        original_subject = inbox_row.subject or ""
    finally:
        ds.close()

    creds = _resolve_persona_email_creds(persona_id, tenant_id)
    if not creds:
        raise EmailNoUserChannelError(
            f"persona_id={persona_id} nema nakonfigurovany EWS kanal"
        )

    account = _get_account(
        email=creds["email"],
        password=creds["password"],
        server=creds["server"],
    )
    sender = creds.get("display_email") or f"<persona_id={persona_id} display missing>"

    # Find original message in EWS by RFC822 Message-ID (try INBOX first, then archives)
    from exchangelib import Mailbox

    candidates = []
    try:
        candidates = list(account.inbox.filter(message_id=rfc_id)[:1])
    except Exception as e:
        logger.warning(f"EMAIL | reply | inbox lookup failed | {e}")
    # Try archives (Personal etc) if not in inbox
    if not candidates:
        try:
            for sub in account.inbox.children:
                try:
                    candidates = list(sub.filter(message_id=rfc_id)[:1])
                    if candidates:
                        break
                except Exception:
                    continue
        except Exception:
            pass

    if not candidates:
        raise EmailSendError(
            f"original email s message_id={rfc_id!r} nenalezen v EWS "
            f"(persona_id={persona_id}). Mohl byt smazan / archivovan mimo nas scope."
        )
    original = candidates[0]

    # Parse override params
    to_list = _parse_recipients(to) if to else None
    cc_list = _parse_recipients(cc) if cc else None
    bcc_list = _parse_recipients(bcc) if bcc else None

    # Faze 12c (Plan E): manualni Message construction.
    # ReplyToItem / ForwardItem v teto verzi exchangelib NEMA pristupna pole
    # (attachments, body = None -- diagnostiky to potvrdily). Exchange si
    # server-side resi obsah + pribali inline images z puvodniho podpisu jako
    # attachments. Bez pristupu k draftu nemuzeme ovlivnit. Resime: stavime
    # Message rucne s thread headers + quoted body v plain text formatu
    # (zadne <img cid:> tagy = zadne attachments leak).

    # 1) Subject (RE:/FW: prefix s deduplikaci)
    if subject:
        final_subject = subject
    else:
        prefix = "FW: " if mode == "forward" else "RE: "
        orig_sub = original_subject or ""
        existing_lower = orig_sub.lower()
        if mode == "forward" and existing_lower.startswith(("fw:", "fwd:")):
            final_subject = orig_sub
        elif mode != "forward" and existing_lower.startswith(("re:", "odp:")):
            final_subject = orig_sub
        else:
            final_subject = prefix + orig_sub

    # 2) Sebrat metadata z originalu pro quoted body + recipient resolution
    from_name = ""
    from_addr = ""
    try:
        if original.sender:
            from_name = getattr(original.sender, "name", "") or ""
            from_addr = getattr(original.sender, "email_address", "") or ""
    except Exception:
        pass
    sent_dt = ""
    try:
        sent_dt = original.datetime_sent.strftime("%Y-%m-%d %H:%M:%S") if original.datetime_sent else ""
    except Exception:
        pass
    orig_to_list = []
    try:
        for r in (original.to_recipients or []):
            ea = getattr(r, "email_address", "") or ""
            if ea:
                orig_to_list.append(ea)
    except Exception:
        pass
    orig_cc_list = []
    try:
        for r in (original.cc_recipients or []):
            ea = getattr(r, "email_address", "") or ""
            if ea:
                orig_cc_list.append(ea)
    except Exception:
        pass
    # Faze 12c+: HTML body cesta -- zachovani inline images z podpisu odesilatele
    # (re-attached jako inline na novy draft, content_id zachovane).
    import html as _html_mod
    from exchangelib import HTMLBody as _HTMLBody, FileAttachment as _FileAtt

    # Stáhnout přílohy z originálu pro re-attach na nový draft
    cloned_attachments = []
    try:
        for att in (original.attachments or []):
            if not isinstance(att, _FileAtt):
                continue   # ItemAttachment (vnořený email) skip
            # Forward: clone vše. Reply/reply_all: jen inline (signature graphics).
            if mode == "forward" or att.is_inline:
                try:
                    new_att = _FileAtt(
                        name=att.name,
                        content=att.content,
                        content_id=att.content_id,
                        content_type=att.content_type,
                        is_inline=att.is_inline,
                    )
                    cloned_attachments.append(new_att)
                except Exception as _att_err:
                    logger.warning(
                        f"EMAIL | {mode} | clone attachment failed | "
                        f"name={att.name!r} | {_att_err}"
                    )
    except Exception as _atts_err:
        logger.warning(f"EMAIL | {mode} | attachments enumerate failed | {_atts_err}")

    # Originální body do HTML (pokud byl HTML, zachovej; pokud plain text, escape do <pre>)
    orig_body_html = ""
    try:
        ob = getattr(original, "body", None)
        if ob:
            if isinstance(ob, _HTMLBody):
                orig_body_html = str(ob)
            else:
                # plain text -> escape do <pre> (zachovává odsazení a newlines)
                orig_body_html = "<pre style=\"font-family:inherit;white-space:pre-wrap;\">" + _html_mod.escape(str(ob)) + "</pre>"
        else:
            orig_body_html = "<i>(původní text nebyl k dispozici)</i>"
    except Exception:
        orig_body_html = "<i>(původní text se nepodařilo načíst)</i>"

    # 3) Postavime HTML body s Outlook-style header oddelovacem
    header_label = "Forwarded Message" if mode == "forward" else "Original Message"

    # Reply text -- bug #1 fix: prevedeme markdown na HTML (puvodne jen
    # escape+br, takze **bold** a podobne se posilalo verbatim).
    reply_html = _markdown_to_html_body(body)

    # REST 27.4.2026: persona signature v reply/forward -- nactu signature_html
    # a inline obrazky (do cloned_attachments). Signature se vlozi mezi reply
    # text a separator quoted history.
    persona_signature_html = ""
    try:
        from core.database_core import get_core_session as _gcs_sig
        from modules.core.infrastructure.models_core import Persona as _Pers_sig
        if persona_id:
            _cs_sig = _gcs_sig()
            try:
                _p = _cs_sig.query(_Pers_sig).filter_by(id=persona_id).first()
                if _p and _p.signature_html and _p.signature_html.strip():
                    persona_signature_html = _p.signature_html
                    _sig_dir = _p.signature_inline_dir
                    if _sig_dir:
                        import re as _re_sig
                        _cids = set(_re_sig.findall(r"cid:([\w.@-]+)", persona_signature_html))
                        for _cid in _cids:
                            _candidates = [_cid]
                            if "@" in _cid:
                                _candidates.append(_cid.split("@", 1)[0])
                            _fp_match = None
                            for _c in _candidates:
                                _fp = os.path.join(_sig_dir, _c)
                                if os.path.isfile(_fp):
                                    _fp_match = _fp
                                    break
                            if not _fp_match:
                                logger.warning(f"EMAIL | {mode} | sig image not found: {_cid}")
                                continue
                            try:
                                with open(_fp_match, "rb") as _fh:
                                    _bytes = _fh.read()
                                _ext = os.path.splitext(_fp_match)[1].lower()
                                _ct = {".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".gif":"image/gif"}.get(_ext,"application/octet-stream")
                                cloned_attachments.append(_FileAtt(
                                    name=os.path.basename(_fp_match), content=_bytes,
                                    content_id=_cid, content_type=_ct, is_inline=True,
                                ))
                            except Exception as _e:
                                logger.warning(f"EMAIL | {mode} | sig attach load failed: {_e}")
            finally:
                _cs_sig.close()
    except Exception as _sig_err:
        logger.warning(f"EMAIL | {mode} | sig load failed: {_sig_err}")

    _signature_block = f"<br><div>{persona_signature_html}</div>" if persona_signature_html else ""

    # Phase 27b (1.5.2026): user-supplied attachments (xlsx/pdf/docx z documents).
    # Pridame je do cloned_attachments listu jako regular (is_inline=False).
    # Tenant gate: pri reply_or_forward_inbox defaultujeme is_parent=True
    # (Marti-AI default je v MANAGEMENT_TOOL_NAMES).
    if attachment_document_ids:
        try:
            user_attachments = _load_attachment_files(
                attachment_document_ids,
                caller_tenant_id=tenant_id,
                is_parent=True,
            )
            cloned_attachments.extend(user_attachments)
            if user_attachments:
                logger.info(
                    f"EMAIL | {mode} | user attachments | count={len(user_attachments)}"
                )
        except (ValueError, PermissionError, OverflowError) as _att_err:
            raise EmailSendError(f"Priloha selhala: {_att_err}")

    quoted_html_parts = [
        f"<div>{reply_html}</div>",
        _signature_block,
        "<br>",
        "<div style=\"border-top:1px solid #ccc;padding-top:8px;\">",
        f"<b>----- {header_label} -----</b><br>",
        f"<b>From:</b> {_html_mod.escape(from_name)} &lt;{_html_mod.escape(from_addr)}&gt;<br>",
        f"<b>Sent:</b> {_html_mod.escape(sent_dt)}<br>",
        f"<b>To:</b> {_html_mod.escape(', '.join(orig_to_list))}<br>",
    ]
    if orig_cc_list:
        quoted_html_parts.append(
            f"<b>Cc:</b> {_html_mod.escape(', '.join(orig_cc_list))}<br>"
        )
    quoted_html_parts.append(
        f"<b>Subject:</b> {_html_mod.escape(original_subject)}<br>"
    )
    quoted_html_parts.append("<br>")
    quoted_html_parts.append(orig_body_html)
    quoted_html_parts.append("</div>")

    quoted = _HTMLBody("".join(quoted_html_parts))

    # 4) Recipients dispatch dle mode
    own_addr = (creds.get("display_email") or creds.get("email") or "").lower()
    if mode == "reply":
        if to_list:
            to_recips = [Mailbox(email_address=a) for a in to_list]
        else:
            if not from_addr:
                raise EmailSendError("reply: puvodni email nema sender, nelze odpovedet")
            to_recips = [Mailbox(email_address=from_addr)]
        cc_recips = [Mailbox(email_address=a) for a in (cc_list or [])]
    elif mode == "reply_all":
        if to_list:
            to_recips = [Mailbox(email_address=a) for a in to_list]
        else:
            to_recips_addrs = [a for a in orig_to_list if a and a.lower() != own_addr]
            if from_addr and from_addr.lower() != own_addr and from_addr not in to_recips_addrs:
                to_recips_addrs.insert(0, from_addr)
            if not to_recips_addrs:
                raise EmailSendError("reply_all: po vyradeni nasi adresy je prazdny seznam To")
            to_recips = [Mailbox(email_address=a) for a in to_recips_addrs]
        if cc_list is not None:
            cc_recips = [Mailbox(email_address=a) for a in cc_list]
        else:
            cc_recips = [
                Mailbox(email_address=a) for a in orig_cc_list
                if a and a.lower() != own_addr
            ]
    else:  # forward
        if not to_list:
            raise ValueError("forward vyzaduje `to`")
        to_recips = [Mailbox(email_address=a) for a in to_list]
        cc_recips = [Mailbox(email_address=a) for a in (cc_list or [])]

    bcc_recips = [Mailbox(email_address=a) for a in (bcc_list or [])]

    # 5) Sestavime Message rucne (full API -- send_and_save funguje)
    from exchangelib import Message as _ExMsg
    msg_kwargs = dict(
        account=account,
        subject=final_subject,
        body=quoted,
        to_recipients=to_recips,
    )
    if cc_recips:
        msg_kwargs["cc_recipients"] = cc_recips
    if bcc_recips:
        msg_kwargs["bcc_recipients"] = bcc_recips

    try:
        draft = _ExMsg(**msg_kwargs)
        # Faze 12c+: re-attach inline images (z podpisu) plus pro forward i regular
        # attachments. Outlook je v body zobrazi (cid: refs), v "Prilohy" panelu
        # jen forward attachments (is_inline=False).
        for _att in cloned_attachments:
            try:
                draft.attach(_att)
            except Exception as _attach_err:
                logger.warning(
                    f"EMAIL | {mode} | re-attach failed | name={_att.name!r} | {_attach_err}"
                )
        if cloned_attachments:
            inline_count = sum(1 for a in cloned_attachments if a.is_inline)
            regular_count = len(cloned_attachments) - inline_count
            logger.info(
                f"EMAIL | {mode} | re-attached | inline={inline_count} | "
                f"regular={regular_count}"
            )
        # Thread headers -- aby Outlook poznal jako reply v threadu
        try:
            if hasattr(draft, "in_reply_to") and original.message_id:
                draft.in_reply_to = original.message_id
        except Exception:
            pass
        try:
            if hasattr(draft, "references") and original.message_id:
                draft.references = original.message_id   # exchangelib chce string, ne list
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"EMAIL | {mode} | message build failed | {e}")
        raise EmailSendError(f"build Message v {mode} mode selhalo: {e}")

    logger.info(
        f"EMAIL | {mode} | manual draft built | subject={final_subject!r} | "
        f"to={[m.email_address for m in to_recips]} | "
        f"cc={[m.email_address for m in cc_recips] or '-'} | "
        f"in_reply_to={original.message_id!r}"
    )

    # 6) Send (manualni Message ma plne API)
    try:
        draft.send_and_save()
    except Exception as e:
        logger.exception(f"EMAIL | {mode} | send failed | {e}")
        if _is_auth_error(e):
            raise EmailAuthError(f"EWS auth failed: {e}")
        raise EmailSendError(f"send_and_save selhalo: {e}")

    # Sebrat finalni recipients pro logging + outbox row
    final_to = [m.email_address for m in (draft.to_recipients or [])]
    final_cc = [m.email_address for m in (draft.cc_recipients or [])]
    final_bcc = [m.email_address for m in (draft.bcc_recipients or [])]
    final_subject = draft.subject or original_subject

    logger.info(
        f"EMAIL | {mode} | from={sender} | to={final_to} | cc={final_cc or '-'} | "
        f"bcc={final_bcc or '-'} | subject={final_subject!r} | "
        f"in_reply_to_inbox={email_inbox_id}"
    )

    # Insert email_outbox audit row + cascade processed_at na inbox
    now_utc = datetime.now(timezone.utc)
    ds = get_data_session()
    try:
        outbox = EmailOutbox(
            user_id=user_id,
            tenant_id=tenant_id,
            persona_id=persona_id,
            to_email=", ".join(final_to),
            cc=_json_serialize_list(final_cc) if final_cc else None,
            bcc=_json_serialize_list(final_bcc) if final_bcc else None,
            subject=final_subject,
            body=body,
            purpose="user_request",
            status="sent",                 # uz odeslano, ne pending
            from_identity="persona",
            sent_at=now_utc,
            in_reply_to_inbox_id=email_inbox_id,
            reply_mode=mode,
            attachment_document_ids=(
                _json_serialize_list(sorted(set(int(x) for x in attachment_document_ids)))
                if attachment_document_ids else None
            ),
        )
        ds.add(outbox)

        # Cascade: oznacit inbox jako vyrizeny (po odpovedi / forwardu)
        inbox_row2 = (
            ds.query(EmailInbox).filter(EmailInbox.id == email_inbox_id).first()
        )
        if inbox_row2 and inbox_row2.processed_at is None:
            inbox_row2.processed_at = now_utc
            if inbox_row2.read_at is None:
                inbox_row2.read_at = now_utc

        ds.commit()
        ds.refresh(outbox)
        return outbox.id
    finally:
        ds.close()


def _json_serialize_list(items: list[str]) -> str:
    """Helper: list of email strings -> JSON string for email_outbox.cc/bcc."""
    import json as _json
    return _json.dumps(list(items), ensure_ascii=False)


def queue_email(
    *,
    to: str,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    from_identity: str = "persona",
    purpose: str = "user_request",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    conversation_id: int | None = None,
    attachment_document_ids: list[int] | None = None,
) -> dict:
    """
    Zaradi email do email_outbox tabulky. Worker (flush_outbox_pending, volany
    z email_fetcher.py) ho pozdeji odesle pres EWS.

    Returns:
        {"id": int, "to_email": str, "status": "pending"}

    Pro synchronni odeslani (napr. invitation email) pouzij primo
    send_email_or_raise(), ktery ceka na EWS. queue_email je lepsi pro
    AI tool send_email -- user dostane okamzitou odpoved (task hotovo),
    worker email casem posle.
    """
    import json
    from datetime import datetime, timezone
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailOutbox

    to_clean = (to or "").strip()
    body_clean = (body or "").strip()
    if not to_clean:
        raise EmailSendError("prazdny to_email")
    if not body_clean:
        raise EmailSendError("prazdny body")
    if "@" not in to_clean:
        raise EmailSendError(f"neplatny email format: {to_clean!r}")

    if purpose not in ("user_request", "notification", "system"):
        raise EmailSendError(f"neznamy purpose: {purpose!r}")
    if from_identity not in ("persona", "user", "system"):
        raise EmailSendError(f"neznama from_identity: {from_identity!r}")

    cc_json = json.dumps(cc, ensure_ascii=False) if cc else None
    bcc_json = json.dumps(bcc, ensure_ascii=False) if bcc else None
    # Phase 27b: attachments JSON encoded list[int] (konzistentni s cc/bcc)
    att_json = None
    if attachment_document_ids:
        # Validace + dedup -- worker nesmí dostat hloupost
        try:
            cleaned_ids = sorted(set(int(x) for x in attachment_document_ids))
            att_json = json.dumps(cleaned_ids)
        except (TypeError, ValueError) as e:
            raise EmailSendError(f"attachment_document_ids invalid: {e}")

    ds = get_data_session()
    try:
        row = EmailOutbox(
            user_id=user_id,
            tenant_id=tenant_id,
            persona_id=persona_id,
            to_email=to_clean.lower(),
            cc=cc_json,
            bcc=bcc_json,
            subject=(subject or "").strip()[:998] or None,
            body=body_clean,
            purpose=purpose,
            status="pending",
            attempts=0,
            conversation_id=conversation_id,
            from_identity=from_identity,
            attachment_document_ids=att_json,
        )
        ds.add(row)
        ds.commit()
        ds.refresh(row)
        outbox_id = row.id
    finally:
        ds.close()

    logger.info(
        f"EMAIL | queued | id={outbox_id} | to={to_clean.lower()} | "
        f"persona_id={persona_id} | from_identity={from_identity}"
    )
    return {
        "id": outbox_id,
        "to_email": to_clean.lower(),
        "status": "pending",
    }


def _atomic_claim_outbox(batch_size: int = 10) -> list[int]:
    """
    Atomicky "zamkne" pending radky v email_outbox oznacenim status='in_progress'
    + claimed_at = now. Vraci ID zavzatych radku. Skip radky ktere uz maji
    max attempts.

    Pouzita stejna "poll + UPDATE ... RETURNING" strategie jako tasks.executor
    pro idempotenci -- dva soubezne workery nedostanou stejny row.
    """
    from datetime import datetime, timezone
    from sqlalchemy import text

    from core.database_data import get_data_session

    ds = get_data_session()
    try:
        # UPDATE ... SET ... WHERE id IN (SELECT id FROM ... LIMIT n FOR UPDATE SKIP LOCKED)
        # PostgreSQL specificky. Vraci ID claimed radku.
        result = ds.execute(
            text(
                """
                UPDATE email_outbox
                   SET status = 'in_progress',
                       claimed_at = :now,
                       attempts = attempts + 1
                 WHERE id IN (
                     SELECT id FROM email_outbox
                      WHERE status = 'pending'
                        AND attempts < :max_attempts
                      ORDER BY created_at ASC
                      LIMIT :batch_size
                      FOR UPDATE SKIP LOCKED
                 )
                 RETURNING id
                """
            ),
            {
                "now": datetime.now(timezone.utc),
                "max_attempts": MAX_SEND_ATTEMPTS,
                "batch_size": batch_size,
            },
        )
        claimed_ids = [r[0] for r in result.fetchall()]
        ds.commit()
        return claimed_ids
    finally:
        ds.close()


def _send_outbox_row(outbox_id: int) -> dict:
    """
    Pokusi se odeslat jeden outbox row pres EWS. Po uspesnem odeslani
    oznaci status='sent' + sent_at = now. Pri selhani status='failed' nebo
    (pokud attempts < MAX) zpet na 'pending' (retry v pristim pollu).

    Vraci:
      {
        "id":         int,
        "status":     "sent" | "failed" | "pending" | "missing",
        "error":      str | None,      -- chybova zprava pro user-facing display
        "error_kind": str | None,      -- "auth" | "no_user_channel" | "send" | None
      }

    error_kind se pouziva volajicim (confirm email flow v conversation/service.py)
    pro dispatch na strukturovanou chybovou hlasku (rozdilna rada pro auth vs.
    missing user channel vs. generic send error).
    """
    from datetime import datetime, timezone
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailOutbox

    ds = get_data_session()
    try:
        row = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
        if row is None:
            return {
                "id": outbox_id, "status": "missing",
                "error": "row gone", "error_kind": None,
            }
    finally:
        ds.close()

    # Pokus o odeslani -- rozdelene catche aby volajici videl typ selhani.
    # CC/BCC v outbox rows jsou JSON arrays; deserializujeme a predame dal.
    cc_list = None
    bcc_list = None
    try:
        if row.cc:
            cc_list = json.loads(row.cc)
    except Exception:
        cc_list = None
    try:
        if row.bcc:
            bcc_list = json.loads(row.bcc)
    except Exception:
        bcc_list = None

    # Phase 27b: attachment_document_ids deserialize
    att_doc_ids = None
    try:
        if row.attachment_document_ids:
            att_doc_ids = json.loads(row.attachment_document_ids)
    except Exception:
        att_doc_ids = None

    error_kind: str | None = None
    err_msg: str | None = None
    try:
        send_email_or_raise(
            to=row.to_email,
            subject=row.subject or "",
            body=row.body,
            persona_id=row.persona_id,
            tenant_id=row.tenant_id,
            user_id=row.user_id,
            from_identity=row.from_identity,
            cc=cc_list,
            bcc=bcc_list,
            attachment_document_ids=att_doc_ids,
        )
    except EmailAuthError as e:
        error_kind = "auth"
        err_msg = str(e)[:500]
    except EmailNoUserChannelError as e:
        error_kind = "no_user_channel"
        err_msg = str(e)[:500]
    except EmailSendError as e:
        error_kind = "send"
        err_msg = str(e)[:500]

    # Success path (zadny exception nezachycen)
    if error_kind is None:
        ds = get_data_session()
        try:
            row2 = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
            if row2:
                row2.status = "sent"
                row2.sent_at = datetime.now(timezone.utc)
                ds.commit()
        finally:
            ds.close()
        return {"id": outbox_id, "status": "sent", "error": None, "error_kind": None}

    # Failure path -- retry logika
    ds = get_data_session()
    try:
        row2 = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
        if not row2:
            return {
                "id": outbox_id, "status": "missing",
                "error": "row gone", "error_kind": error_kind,
            }
        if row2.attempts >= MAX_SEND_ATTEMPTS:
            row2.status = "failed"
            row2.last_error = err_msg
            logger.error(
                f"EMAIL | outbox | failed (max attempts) | id={outbox_id} | "
                f"kind={error_kind} | {err_msg}"
            )
            new_status = "failed"
        else:
            # auth + no_user_channel = "konfiguracni" problem, retry nepomuze,
            # rovnou failed (aby se to netlacilo do fronty dokola).
            if error_kind in ("auth", "no_user_channel"):
                row2.status = "failed"
                new_status = "failed"
                logger.error(
                    f"EMAIL | outbox | failed (config error) | id={outbox_id} | "
                    f"kind={error_kind} | {err_msg}"
                )
            else:
                row2.status = "pending"
                new_status = "pending"
                logger.warning(
                    f"EMAIL | outbox | retry | id={outbox_id} | "
                    f"attempt={row2.attempts} | kind={error_kind} | {err_msg}"
                )
            row2.last_error = err_msg
        ds.commit()
        return {
            "id": outbox_id, "status": new_status,
            "error": err_msg, "error_kind": error_kind,
        }
    finally:
        ds.close()


def flush_outbox_pending(batch_size: int = 10) -> dict:
    """
    Worker tick -- claimne pending radky a pokusi se je odeslat. Vraci
    souhrn pro logging workera:
      {"claimed": N, "sent": N, "failed": N, "retry": N}

    Volano z scripts/email_fetcher.py v kazdem poll cyklu (po fetch_all).
    Muze bezet soubezne s inbound fetchem -- jsou to ruzne radky v jine
    tabulce.
    """
    claimed = _atomic_claim_outbox(batch_size=batch_size)
    if not claimed:
        return {"claimed": 0, "sent": 0, "failed": 0, "retry": 0}

    logger.info(f"EMAIL | outbox | flush | claimed={len(claimed)} | ids={claimed}")

    sent_count = 0
    failed_count = 0
    retry_count = 0

    for outbox_id in claimed:
        try:
            result = _send_outbox_row(outbox_id)
            if result["status"] == "sent":
                sent_count += 1
            elif result["status"] == "failed":
                failed_count += 1
            else:
                retry_count += 1
        except Exception as e:
            # Kdyby neco proteklo mimo EmailError kategorii -- oznacime failed
            # aby neblokovalo dalsi cykly.
            logger.error(
                f"EMAIL | outbox | unexpected | id={outbox_id} | {e}",
                exc_info=True,
            )
            from datetime import datetime, timezone
            from core.database_data import get_data_session
            from modules.core.infrastructure.models_data import EmailOutbox
            ds = get_data_session()
            try:
                row = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
                if row:
                    row.status = "failed"
                    row.last_error = f"unexpected: {e}"[:500]
                    ds.commit()
            finally:
                ds.close()
            failed_count += 1

    return {
        "claimed": len(claimed),
        "sent": sent_count,
        "failed": failed_count,
        "retry": retry_count,
    }


def send_outbox_row_now(outbox_id: int) -> dict:
    """
    Atomicky claimne JEDEN konkretni outbox row (id=outbox_id) a pokusi se
    ho odeslat inline. Pouziva se z AI confirm email flow -- uzivatel rekne
    "ano", my zapiseme do outboxu a hned se pokusime poslat, aby user dostal
    okamzity feedback ("✅ odeslano" vs. "❌ chyba") misto cekani az to
    popadne pravidelny worker cycle.

    Race-safe proti paralelne bezicimu workerovi:
      - Pokud worker mezitim row claimnul (status != 'pending'), vracime
        status='already_claimed' a volajici rozhodne co zobrazit.
      - Pokud row uz prekrocila MAX_SEND_ATTEMPTS, nezcentlaimneme, vracime
        aktualni (failed) stav.

    Vraci dict ve stejnem tvaru jako _send_outbox_row:
      {
        "id":         int,
        "status":     "sent" | "failed" | "pending" | "already_claimed" | "missing",
        "error":      str | None,
        "error_kind": str | None,
      }
    """
    from datetime import datetime, timezone
    from sqlalchemy import text

    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import EmailOutbox

    # Atomicky: UPDATE ... WHERE id=X AND status='pending' AND attempts<MAX
    # RETURNING id. Kdyz 0 rows vraceno, row mezitim chytil nekdo jiny /
    # prekrocila attempts / neexistuje.
    ds = get_data_session()
    try:
        result = ds.execute(
            text(
                """
                UPDATE email_outbox
                   SET status = 'in_progress',
                       claimed_at = :now,
                       attempts = attempts + 1
                 WHERE id = :id
                   AND status = 'pending'
                   AND attempts < :max_attempts
                 RETURNING id
                """
            ),
            {
                "now": datetime.now(timezone.utc),
                "id": outbox_id,
                "max_attempts": MAX_SEND_ATTEMPTS,
            },
        )
        claimed_row = result.fetchone()
        ds.commit()
    finally:
        ds.close()

    if claimed_row is None:
        # Claim selhal -- row neni pending (uz poslany, failed, in_progress,
        # nebo neexistuje). Vratime aktualni stav pro reporting volajicimu.
        ds = get_data_session()
        try:
            row = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
            if row is None:
                return {
                    "id": outbox_id, "status": "missing",
                    "error": "row gone", "error_kind": None,
                }
            # Pokud status byl uz 'in_progress', pravdepodobne ho drzi worker.
            # Oznacme to jako 'already_claimed' aby UI zobrazila "worker pracuje".
            if row.status == "in_progress":
                return {
                    "id": outbox_id, "status": "already_claimed",
                    "error": None, "error_kind": None,
                }
            return {
                "id": outbox_id, "status": row.status,
                "error": row.last_error, "error_kind": None,
            }
        finally:
            ds.close()

    # Claim uspel -- mame exkluzivni pravo poslat. _send_outbox_row zvladne
    # success/failure bookkeeping (row je nyni 'in_progress', on ji oznaci
    # sent / pending / failed).
    logger.info(f"EMAIL | outbox | send_now | claimed | id={outbox_id}")
    try:
        return _send_outbox_row(outbox_id)
    except Exception as e:
        # Defensive fallback -- neocekavana vyjimka mimo EmailError kategorie.
        # Musime row vratit z 'in_progress' zpatky, aby se tam nezasekla.
        logger.error(
            f"EMAIL | outbox | send_now | unexpected | id={outbox_id} | {e}",
            exc_info=True,
        )
        err_msg = f"unexpected: {e}"[:500]
        ds = get_data_session()
        try:
            row = ds.query(EmailOutbox).filter(EmailOutbox.id == outbox_id).first()
            if row:
                row.status = "failed"
                row.last_error = err_msg
                ds.commit()
        finally:
            ds.close()
        return {
            "id": outbox_id, "status": "failed",
            "error": err_msg, "error_kind": "unexpected",
        }


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
    persona_id = _get_default_persona_id()
    return send_email(
        to=to, subject=subject, body=body,
        persona_id=persona_id,
    )
