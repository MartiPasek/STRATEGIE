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


def send_email_or_raise(
    to: str,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    from_identity: str = "persona",
) -> None:
    """
    Odesle email. V pripade selhani hodi EmailAuthError / EmailSendError /
    EmailNoUserChannelError.

    from_identity:
      "persona"  (default) -- posila z persona_channels (Marti-AI),
                              fallback na .env pokud persona nema kanal.
      "user"               -- posila z user's EWS kanalu (users.ews_*).
                              Pokud user kanal nema, hodi EmailNoUserChannelError.
    """
    try:
        from exchangelib import Message, Mailbox

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
            # Sender v logu = VYHRADNE display (SMTP alias). Login UPN je SECRET
            # a nesmi se objevit nikde mimo _get_account / persona_channels.
            # Kdyz display chybi, maskujeme sender abychom nepsali login.
            sender = creds.get("display_email") or f"<persona_id={persona_id} display missing>"
        else:
            # Fallback: globalni .env. Pro pozvanky / password-reset / backward compat.
            # (Jen pro persona mode; user mode by uz byl rejected.)
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
            f"EMAIL | sent | identity={from_identity} | from={sender} | to={to} | subject={subject}"
        )
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


# ── OUTBOX: queue + flush worker ──────────────────────────────────────────

# Maximalni pocet pokusu nez email oznacime jako trvale failed. Pri flush
# workera se kazdy pokus inkrementuje attempts; po dosazeni limitu uz ho
# worker nevezme. User muze v administraci manualne zretransmitovat.
MAX_SEND_ATTEMPTS = 5


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
    return send_email(to=to, subject=subject, body=body)
