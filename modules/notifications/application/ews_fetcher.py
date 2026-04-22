"""
EWS fetcher -- stahuje unread emaily z Exchange do email_inbox.

Pull model (oproti SMS push):
    exchange INBOX  <--- poll ----  tento modul
                                        |
                                        v
                                  email_inbox_service.store_inbound_email()
                                        |
                                        v
                                  email_inbox tabulka

Volano bud z:
  - scripts/email_fetcher.py (out-of-process worker, pravidelny polling 60s)
  - POST /api/v1/email/fetch/{persona_id} (manualni trigger z UI tlacitka)

Za kazdou persona_channel (channel_type='email', is_enabled=True) vytvorime
EWS spojeni pod jejim uctem, prectame unread, ulozime do DB, oznacime jako
is_read=True v Exchange (aby se to pri dalsim pollu neopakovalo).

Chyba u jedne persony nesmi shodit ostatni -- vzdy try/except per-persona.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from typing import Any

from core.logging import get_logger
from modules.notifications.application import email_inbox_service
from modules.notifications.application.persona_channel_service import (
    get_email_credentials,
)

logger = get_logger("notifications.ews_fetcher")


# Kolik zprav maximalne stahneme v jednom pollu (ochrana proti peaku).
# Kdyz je jich vic v INBOX, dalsi prijdou v dalsim pollu -- razeny od nejstarsich,
# aby se kazdy dostal na radu.
FETCH_LIMIT_PER_POLL = 50


class EwsFetcherError(Exception):
    """Baseline chyba EWS fetchera (connect / parse / auth)."""


# ── HTML -> plaintext prevod ───────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _html_to_text(html: str) -> str:
    """
    Primitivni prevod HTML na text pro uchovani v body. Nic fancy --
    stripe tagy, normalizuje whitespace. Pro vetsinu emailu postacuje.
    Pro AI prompt v PR3 bude takhle jasnejsi kontext nez raw HTML.
    """
    if not html:
        return ""
    no_tags = _HTML_TAG_RE.sub(" ", html)
    # HTML entities -- nejcastejsi
    no_tags = (
        no_tags.replace("&nbsp;", " ")
               .replace("&amp;", "&")
               .replace("&lt;", "<")
               .replace("&gt;", ">")
               .replace("&quot;", '"')
               .replace("&#39;", "'")
    )
    return _WHITESPACE_RE.sub(" ", no_tags).strip()


# ── EWS connect ────────────────────────────────────────────────────────────

def _connect_account(creds: dict[str, str]):
    """
    Postavi exchangelib.Account pres persona credentials. Sjednocene s
    email_service._get_account, ale s parametry (ne .env fallback).

    Pozn.: kazdy call vytvori noveho klienta -- kdyby bylo potreba persistent
    connection, budeme keshovat. Pro interval 60s / few requests/call je to
    OK. Pro densi polling bude vhodne pool.
    """
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    import urllib3
    urllib3.disable_warnings()

    server = (creds.get("server") or "").replace("https://", "").replace("http://", "")
    if not (creds.get("email") and creds.get("password") and server):
        raise EwsFetcherError(
            f"EWS creds nejsou kompletni: email={bool(creds.get('email'))}, "
            f"password={bool(creds.get('password'))}, server={bool(server)}"
        )

    try:
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
        return account
    except Exception as e:
        raise EwsFetcherError(f"EWS connect failed: {e}") from e


# ── Extrakce dat ze zpravy ────────────────────────────────────────────────

def _extract_message_fields(msg) -> dict[str, Any]:
    """
    Z exchangelib.Message vytahne fields potrebne pro store_inbound_email.
    Defensivni -- kazde pole muze byt None.
    """
    # Message-ID (RFC822). exchangelib ho vystavi pod atributem .message_id.
    # Pro jistotu fallback na synthetic hash.
    message_id = getattr(msg, "message_id", None)
    if not message_id:
        # synthetic = hash(from + subject + received). Deterministicke,
        # takze dedup stale funguje pri opakovanem fetchi.
        from_raw = getattr(getattr(msg, "sender", None), "email_address", None) or ""
        subj_raw = getattr(msg, "subject", "") or ""
        dt_raw = getattr(msg, "datetime_received", None)
        dt_str = dt_raw.isoformat() if dt_raw else "unknown"
        message_id = f"synthetic:{hash((from_raw, subj_raw, dt_str))}"

    # From
    sender = getattr(msg, "sender", None)
    from_email = getattr(sender, "email_address", None) if sender else None
    from_name = getattr(sender, "name", None) if sender else None
    if not from_email:
        # Fallback -- zachytime nejake aspon "unknown" aby nepadal NOT NULL
        from_email = "unknown@unknown"

    # To (muze byt vic, vezmeme vsechny do meta a primarni = prvni pro storage;
    # persona resolver stejne resi, komu to prislo, na zaklade creds.email)
    to_list = []
    if getattr(msg, "to_recipients", None):
        for r in msg.to_recipients:
            if r and getattr(r, "email_address", None):
                to_list.append(r.email_address)

    cc_list = []
    if getattr(msg, "cc_recipients", None):
        for r in msg.cc_recipients:
            if r and getattr(r, "email_address", None):
                cc_list.append(r.email_address)

    # Subject + body
    subject = getattr(msg, "subject", None) or None

    # Body: exchangelib ma .body (Body) nebo .text_body (plaintext, kdyz existuje).
    # Preferujeme text_body. Fallback na body s HTML stripem.
    body_text = None
    try:
        tb = getattr(msg, "text_body", None)
        if tb:
            body_text = str(tb).strip() or None
    except Exception:
        body_text = None
    if not body_text:
        try:
            b = getattr(msg, "body", None)
            if b:
                body_text = _html_to_text(str(b))
                body_text = body_text or None
        except Exception:
            body_text = None

    # Received datetime (timezone aware)
    received_at = None
    try:
        dt = getattr(msg, "datetime_received", None)
        if dt:
            # exchangelib vrati EWSDateTime (subclass datetime s tzinfo).
            # Convert na datetime s UTC aby serializace DB byla konzistentni.
            received_at = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.debug(f"EWS | received_at parse failed: {e}")
        received_at = datetime.now(timezone.utc)

    # Meta = JSON s dodatecnymi fieldy pro debug/PR3 features
    has_attachments = bool(getattr(msg, "has_attachments", False))
    importance = getattr(msg, "importance", None)
    meta = {
        "cc": cc_list,
        "to_all": to_list,
        "has_attachments": has_attachments,
        "importance": str(importance) if importance else None,
    }

    return {
        "from_email": from_email,
        "from_name": from_name,
        "subject": subject,
        "body": body_text,
        "message_id": message_id,
        "received_at": received_at or datetime.now(timezone.utc),
        "meta": json.dumps(meta, ensure_ascii=False),
    }


# ── Public: fetch per persona ──────────────────────────────────────────────

def fetch_unread_for_persona(
    persona_id: int,
    tenant_id: int | None = None,
    limit: int = FETCH_LIMIT_PER_POLL,
) -> dict[str, Any]:
    """
    Fetchne unread emaily z INBOX persony, ulozi do email_inbox, oznaci jako
    is_read=True v Exchange.

    Vraci:
      {
        "persona_id": int,
        "new": int,       # nove stazene
        "deduped": int,   # uz byly v DB (restart/overlap)
        "errors": int,    # kolik zprav selhalo pri ulozeni
        "status": "ok" | "no_channel" | "connect_failed" | "fetch_failed",
        "detail": str | None
      }

    Chybovy status:
      no_channel      = persona nema email kanal -> nothing to do (not an error)
      connect_failed  = EWS auth/connect failed
      fetch_failed    = inbox query selhal
    """
    creds = get_email_credentials(persona_id, tenant_id=tenant_id)
    if not creds:
        return {
            "persona_id": persona_id,
            "new": 0,
            "deduped": 0,
            "errors": 0,
            "status": "no_channel",
            "detail": None,
        }

    # Pravidlo: login UPN (creds["email"]) je SECRET -- nesmi nikam jinam nez
    # do _get_account. Pro storage / logovani pouzijeme display_identifier
    # (verejna SMTP adresa). Kdyz display neni nastaveny, SKIPneme personu --
    # nechceme riskovat leak loginu do email_inbox.to_email.
    display = (creds.get("display_email") or "").strip().lower()
    if not display:
        logger.warning(
            f"EWS | skip | persona_id={persona_id} | "
            f"display_identifier v persona_channels neni nastaven -- nelze bezpecne "
            f"pouzit (chranime login UPN pred leakem)"
        )
        return {
            "persona_id": persona_id,
            "new": 0,
            "deduped": 0,
            "errors": 0,
            "status": "no_channel",
            "detail": "display_identifier missing",
        }
    to_email_for_storage = display

    try:
        account = _connect_account(creds)
    except EwsFetcherError as e:
        # Login UPN nikdy do logu, jen persona_id + display adresa.
        logger.error(
            f"EWS | connect failed | persona_id={persona_id} | display={display} | {e}"
        )
        return {
            "persona_id": persona_id,
            "new": 0,
            "deduped": 0,
            "errors": 0,
            "status": "connect_failed",
            "detail": str(e),
        }

    new_count = 0
    deduped_count = 0
    error_count = 0

    try:
        # Unread messages, od nejstarsich (aby kdyz je jich vic nez limit,
        # ostatni prijdou v dalsich pollech, ale uz videli starsi).
        unread_qs = (
            account.inbox
            .filter(is_read=False)
            .order_by("datetime_received")
        )
        # .filter / .order_by / [:limit] je lazy -- limit slicing pouzijeme.
        messages = list(unread_qs[:limit])
    except Exception as e:
        # Login UPN do logu NEPATRI (chran credential) -- jen display + persona_id.
        logger.error(
            f"EWS | fetch failed | persona_id={persona_id} | display={display} | {e}",
            exc_info=True,
        )
        return {
            "persona_id": persona_id,
            "new": 0,
            "deduped": 0,
            "errors": 0,
            "status": "fetch_failed",
            "detail": str(e),
        }

    logger.info(
        f"EWS | fetch | persona_id={persona_id} | display={display} | "
        f"unread_found={len(messages)}"
    )

    for msg in messages:
        try:
            fields = _extract_message_fields(msg)
            result = email_inbox_service.store_inbound_email(
                from_email=fields["from_email"],
                to_email=to_email_for_storage,
                subject=fields["subject"],
                body=fields["body"],
                message_id=fields["message_id"],
                received_at=fields["received_at"],
                from_name=fields["from_name"],
                meta=fields["meta"],
            )
            if result.get("deduped"):
                deduped_count += 1
            else:
                new_count += 1

            # Oznacime v EWS jako precteny. Delame to bez ohledu na deduped --
            # kdyz je uz u nas ale v EWS stale unread, chceme ho docistit,
            # jinak se v pristim pollu znovu stahne a zbytecne zatezi DB unique
            # constraint.
            try:
                msg.is_read = True
                msg.save(update_fields=["is_read"])
            except Exception as mark_err:
                logger.warning(
                    f"EWS | mark_read failed | persona_id={persona_id} | "
                    f"message_id={fields['message_id'][:60]} | {mark_err}"
                )

        except Exception as per_msg_err:
            error_count += 1
            logger.error(
                f"EWS | per-message failed | persona_id={persona_id} | {per_msg_err}",
                exc_info=True,
            )
            # Pokracujeme na dalsi zpravu -- jedna vadna nesmi zablokovat celou davku.

    logger.info(
        f"EWS | fetch done | persona_id={persona_id} | new={new_count} | "
        f"deduped={deduped_count} | errors={error_count}"
    )

    return {
        "persona_id": persona_id,
        "new": new_count,
        "deduped": deduped_count,
        "errors": error_count,
        "status": "ok",
        "detail": None,
    }


# ── Public: fetch all active personas ──────────────────────────────────────

def fetch_all_active_personas() -> dict[str, Any]:
    """
    Iteruje vsechny persona_channels (channel_type='email', is_enabled=True),
    za kazdou persona_id provede fetch_unread_for_persona. Agreguje statistiky.

    Pouzito workerem scripts/email_fetcher.py a manualni trigger
    POST /api/v1/email/fetch-all.

    Kazda persona bezi v samostatnem try/except; selhani jedne neshodi ostatni.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import PersonaChannel

    cs = get_core_session()
    try:
        # Distinct persona_id -- jedna persona muze mit vic kanalu (tenant-specific
        # + global), staci iterovat unikatni.
        rows = (
            cs.query(PersonaChannel.persona_id, PersonaChannel.tenant_id)
            .filter(
                PersonaChannel.channel_type == "email",
                PersonaChannel.is_enabled.is_(True),
            )
            .all()
        )
    finally:
        cs.close()

    # Dedup (persona_id, tenant_id). Per-channel spojeni nejde sdilet, ale
    # stejnej persona+tenant se nemusi fetchovat dvakrat (je to ten samy inbox).
    seen: set[tuple[int, int | None]] = set()
    unique_targets: list[tuple[int, int | None]] = []
    for persona_id, tenant_id in rows:
        key = (persona_id, tenant_id)
        if key in seen:
            continue
        seen.add(key)
        unique_targets.append(key)

    logger.info(f"EWS | fetch_all | targets={len(unique_targets)}")

    total_new = 0
    total_deduped = 0
    total_errors = 0
    per_persona: list[dict[str, Any]] = []

    for persona_id, tenant_id in unique_targets:
        try:
            result = fetch_unread_for_persona(persona_id, tenant_id=tenant_id)
            total_new += result["new"]
            total_deduped += result["deduped"]
            total_errors += result["errors"]
            per_persona.append(result)
        except Exception as e:
            logger.error(
                f"EWS | fetch_all | persona_id={persona_id} | unexpected error: {e}",
                exc_info=True,
            )
            per_persona.append({
                "persona_id": persona_id,
                "new": 0,
                "deduped": 0,
                "errors": 1,
                "status": "fetch_failed",
                "detail": str(e),
            })
            total_errors += 1

    return {
        "targets": len(unique_targets),
        "total_new": total_new,
        "total_deduped": total_deduped,
        "total_errors": total_errors,
        "per_persona": per_persona,
    }
