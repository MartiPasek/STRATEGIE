"""
Email inbox service -- ukladani a zobrazovani prichozich emailu.

Architektura (pull model):
    Exchange (INBOX)  <--- poll EWS ----  scripts/email_fetcher.py
                                               |
                                               v
                                         email_inbox tabulka

Tim, ze email je pull (na rozdil od SMS push), musi nekdo aktivne fetchnout.
Tenhle soubor je STORAGE + READ vrstva. Vlastni EWS fetch je v
`ews_fetcher.py`, ktery pak pro kazdou zpravu zavola `store_inbound_email()`.

PR2 scope: bez auto-create tasku. Email prijde -> ulozi se do inboxu ->
user vidi badge v hlavicce + muze rucne kliknout "Navrhni odpoved" v UI
(to spusti task, ale to je PR3).

store_inbound_email() provadi:
  1. normalizaci email adres (lowercase)
  2. resolve persony podle to_email pres persona_channels
  3. dedup pres UNIQUE (persona_id, message_id) -- duplikat -> vrati existing
  4. zapis do email_inbox se read_at = NULL, processed_at = NULL
"""
from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import EmailInbox

logger = get_logger("notifications.email_inbox")


class EmailInboxError(Exception):
    """Baseline chyba pro email inbox operace."""


class EmailInboxValidationError(EmailInboxError):
    """Neplatna email adresa nebo prazdna data."""


# ── NORMALIZACE ────────────────────────────────────────────────────────────

def normalize_email(addr: str | None) -> str:
    """
    Lowercase + strip. Nepokouси se prepisovat IDN / puny, jen spodni uroven
    pravidel, at match v persona_channels funguje case-insensitive.
    """
    if not addr:
        raise EmailInboxValidationError("prazdna email adresa")
    cleaned = addr.strip().lower()
    if "@" not in cleaned:
        raise EmailInboxValidationError(f"neplatny email format: {addr!r}")
    return cleaned


# ── PERSONA RESOLVER ───────────────────────────────────────────────────────

def _resolve_persona_by_email(to_email: str) -> tuple[int | None, int | None]:
    """
    Zjisti, ktera persona "vlastni" tuto email adresu. Vrati (persona_id, tenant_id).

    Hleda se v persona_channels: channel_type='email' a identifier NEBO
    display_identifier match toEmail (case-insensitive). is_enabled musi byt True.

    Priorita:
      1. identifier exact match (login UPN) -- nejsilnejsi match
      2. display_identifier match (primary SMTP alias)
      3. Nic -> vrati (None, None), email se ulozi bez personu (admin view)
    """
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import PersonaChannel
        from sqlalchemy import func, or_

        cs = get_core_session()
        try:
            # 1) Identifier match (login UPN)
            ch = (
                cs.query(PersonaChannel)
                .filter(
                    PersonaChannel.channel_type == "email",
                    PersonaChannel.is_enabled.is_(True),
                    func.lower(PersonaChannel.identifier) == to_email,
                )
                .order_by(PersonaChannel.is_primary.desc(), PersonaChannel.id.asc())
                .first()
            )
            if ch:
                return ch.persona_id, ch.tenant_id

            # 2) Display identifier match (SMTP alias)
            ch = (
                cs.query(PersonaChannel)
                .filter(
                    PersonaChannel.channel_type == "email",
                    PersonaChannel.is_enabled.is_(True),
                    func.lower(PersonaChannel.display_identifier) == to_email,
                )
                .order_by(PersonaChannel.is_primary.desc(), PersonaChannel.id.asc())
                .first()
            )
            if ch:
                return ch.persona_id, ch.tenant_id

            return None, None
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"EMAIL | inbox | persona resolve failed: {e}")
        return None, None


# ── STORE ──────────────────────────────────────────────────────────────────

def store_inbound_email(
    *,
    from_email: str,
    to_email: str,
    subject: str | None,
    body: str | None,
    message_id: str,
    received_at: datetime | None = None,
    from_name: str | None = None,
    meta: str | None = None,
) -> dict:
    """
    Zapise prichozi email do email_inbox. Rucne se mape persona podle to_email.

    message_id je RFC822 Message-ID z Exchange -- MUSIME ho mit, jinak neumime
    dedup. Pokud by fetcher dostal zpravu bez Message-ID (velmi vzacne),
    MUSI si sam dopocitat synthetic ID (hash from+subject+received) a predat.

    Returns:
        {"id": int, "persona_id": int|None, "from_email": str, "to_email": str,
         "subject": str|None, "received_at": iso-str, "deduped": bool}

    Duplikat = UNIQUE constraint na (persona_id, message_id). Fetcher polluje
    opakovane a nemusi presne zvladnout "uz ulozeno?" -- proto catch IntegrityError
    a vratime existing row s flag `deduped=True`.
    """
    if not message_id or not message_id.strip():
        raise EmailInboxValidationError("chybi message_id (nutne pro dedup)")

    from_email_norm = normalize_email(from_email)
    to_email_norm = normalize_email(to_email)

    # Body muze byt None (EWS nekdy nevrati body napr. pri error parsing) --
    # ulozime NULL, at UI videt "prazdny body, podivej se do Outlooku".
    body_clean = (body or "").strip() or None
    subject_clean = (subject or "").strip()[:998] or None

    persona_id, tenant_id = _resolve_persona_by_email(to_email_norm)

    if received_at is None:
        received_at = datetime.now(timezone.utc)

    ds = get_data_session()
    try:
        row = EmailInbox(
            persona_id=persona_id,
            tenant_id=tenant_id,
            from_email=from_email_norm,
            from_name=(from_name or None),
            to_email=to_email_norm,
            subject=subject_clean,
            body=body_clean,
            message_id=message_id.strip()[:998],
            received_at=received_at,
            meta=meta,
        )
        ds.add(row)
        try:
            ds.commit()
        except IntegrityError:
            # Duplikat pres UNIQUE (persona_id, message_id). Nacteme existing
            # a vratime s deduped=True. Zabranime tim 500 na fetch restart.
            ds.rollback()
            existing = (
                ds.query(EmailInbox)
                .filter(
                    EmailInbox.persona_id == persona_id,
                    EmailInbox.message_id == message_id.strip()[:998],
                )
                .first()
            )
            if existing is None:
                # Nastalo s neco jineho nez nase unique -- nechame chybu probublat
                raise
            logger.debug(
                f"EMAIL | inbox | dedup hit | persona_id={persona_id} | "
                f"message_id={message_id[:60]}"
            )
            return {
                "id": existing.id,
                "persona_id": existing.persona_id,
                "from_email": existing.from_email,
                "to_email": existing.to_email,
                "subject": existing.subject,
                "received_at": existing.received_at.isoformat() if existing.received_at else None,
                "deduped": True,
            }

        ds.refresh(row)
        logger.info(
            f"EMAIL | inbox | stored | id={row.id} | from={from_email_norm} | "
            f"to={to_email_norm} | persona_id={persona_id} | "
            f"subject_len={len(subject_clean or '')} | body_len={len(body_clean or '')}"
        )
        return {
            "id": row.id,
            "persona_id": row.persona_id,
            "from_email": row.from_email,
            "to_email": row.to_email,
            "subject": row.subject,
            "received_at": row.received_at.isoformat() if row.received_at else None,
            "deduped": False,
        }
    finally:
        ds.close()


# ── READ (UI) ──────────────────────────────────────────────────────────────

def list_inbox_for_ui(
    *,
    persona_id: int,
    filter_mode: str = "new",    # 'new' | 'processed'
    limit: int = 50,
) -> list[dict]:
    """
    Seznam prichozich emailu pro UI taby 'Prichozi' / 'Zpracovane'.
    Razeno od nejnovejsich.

    filter_mode:
      'new'       -- jen emails kde processed_at IS NULL (slozka Prichozi)
      'processed' -- jen emails kde processed_at IS NOT NULL (Zpracovane)
    """
    if filter_mode not in ("new", "processed"):
        raise EmailInboxValidationError(
            f"neznamy filter_mode '{filter_mode}' (ocekavam 'new' nebo 'processed')"
        )

    ds = get_data_session()
    try:
        q = ds.query(EmailInbox).filter(EmailInbox.persona_id == persona_id)
        if filter_mode == "new":
            q = q.filter(EmailInbox.processed_at.is_(None))
        else:
            q = q.filter(EmailInbox.processed_at.isnot(None))
        rows = (
            q.order_by(EmailInbox.received_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )
        return [
            {
                "id": r.id,
                "from_email": r.from_email,
                "from_name": r.from_name,
                "to_email": r.to_email,
                "subject": r.subject,
                "body": r.body,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                # Faze 6: meta obsahuje archived_personal flag pro UI
                "archived_personal": _is_archived(r.meta),
            }
            for r in rows
        ]
    finally:
        ds.close()


def _is_archived(meta_raw: str | None) -> bool:
    """Pomocna funkce: parsuje meta JSON a vraci meta.archived_personal flag."""
    if not meta_raw:
        return False
    try:
        import json as _j
        m = _j.loads(meta_raw)
        return bool(isinstance(m, dict) and m.get("archived_personal"))
    except Exception:
        return False


def mark_read(inbox_id: int) -> dict | None:
    """
    Oznaci email jako precteny (read_at = now). Pouziva se pri otevreni
    detailu v UI. Idempotent -- druhy volani read_at uz nezmeni.

    Vraci dict s updated daty, None pokud email neexistuje.
    """
    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter(EmailInbox.id == inbox_id).first()
        if row is None:
            return None
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            ds.commit()
            ds.refresh(row)
            logger.info(f"EMAIL | inbox | marked read | id={inbox_id}")
        return {
            "id": row.id,
            "read_at": row.read_at.isoformat() if row.read_at else None,
            "processed_at": row.processed_at.isoformat() if row.processed_at else None,
        }
    finally:
        ds.close()


def mark_inbox_processed(inbox_id: int) -> dict | None:
    """
    Manualni 'mark as processed' override z UI. Nastavi processed_at = now.
    Pouziva se kdyz user chce pohnout email do Zpracovanych bez ohledu na
    tasky (napr. reklama co nepotrebuje odpoved).

    V PR3 to zacne volat kaskada z tasks.service.mark_task_done() tak jak
    to uz dela sms_inbox. Prozatim jen manual.
    """
    ds = get_data_session()
    try:
        row = ds.query(EmailInbox).filter(EmailInbox.id == inbox_id).first()
        if row is None:
            return None
        if row.processed_at is None:
            row.processed_at = datetime.now(timezone.utc)
            if row.read_at is None:
                row.read_at = row.processed_at
            ds.commit()
            ds.refresh(row)
            logger.info(f"EMAIL | inbox | marked processed (manual) | id={inbox_id}")
        return {
            "id": row.id,
            "processed_at": row.processed_at.isoformat(),
            "read_at": row.read_at.isoformat() if row.read_at else None,
        }
    finally:
        ds.close()


# ── COUNTERS (header badge) ────────────────────────────────────────────────

def count_unread(persona_id: int) -> int:
    """
    Pocet emailu persony, ktere jeste uzivatel nevidel (read_at IS NULL)
    a nejsou zpracovane (processed_at IS NULL). Pouziva se v badge v hlavicce.
    """
    ds = get_data_session()
    try:
        return (
            ds.query(EmailInbox)
            .filter(
                EmailInbox.persona_id == persona_id,
                EmailInbox.read_at.is_(None),
                EmailInbox.processed_at.is_(None),
            )
            .count()
        )
    finally:
        ds.close()


def count_unread_for_user(user_id: int) -> int:
    """
    Agregovany pocet neprectenych emailu pro vsechny persony, ktere user
    videl (global personas + persony v jeho aktivnim tenantu).

    Pro header badge. Kombinuje se s count_unread_sms_for_user() v API
    endpointu /unread-counts.

    Poznamka: dnes je to "view-scope" (globalni + current tenant personas),
    ne "ownership-scope" (persony ktere user spravuje). To zjednodusuje
    badge, ale jednou se nam stane ze user prepne tenant a po chvili se
    ukaze counter jine persony. V PR3, kdyz pridame tab 'Email' do UI,
    prepocitame to cez aktualne vybranou personu.
    """
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import Persona, User

        cs = get_core_session()
        try:
            user = cs.query(User).filter_by(id=user_id).first()
            current_tenant_id = user.last_active_tenant_id if user else None

            persona_ids = [
                p.id
                for p in cs.query(Persona).all()
                if p.tenant_id is None or p.tenant_id == current_tenant_id
            ]
        finally:
            cs.close()

        if not persona_ids:
            return 0

        ds = get_data_session()
        try:
            return (
                ds.query(EmailInbox)
                .filter(
                    EmailInbox.persona_id.in_(persona_ids),
                    EmailInbox.read_at.is_(None),
                    EmailInbox.processed_at.is_(None),
                )
                .count()
            )
        finally:
            ds.close()

    except Exception as e:
        logger.warning(f"EMAIL | inbox | count_unread_for_user failed: {e}")
        return 0


# ── TASK INTEGRATION (PR3) ────────────────────────────────────────────────

def suggest_reply(inbox_id: int) -> dict:
    """
    Manualne trigne AI draft odpovedi -- vytvori task se source_type='email_inbox'
    a source_id=inbox_id. Task executor (worker) ho pak pobere a vygeneruje
    draft, ktery UI nacte pres get_draft_for_inbox().

    Pouziva se v UI tlacitkem "Navrhni odpoved" na emailu. User musi kliknout
    aktivne -- auto-create z store_inbound_email nedelame (viz PR3 scope).

    Vraci dict:
      {
        "email_id": int,
        "task_id": int,
        "status": "open",
        "title": str,       # task.title (lidsky citelny)
      }

    Raises EmailInboxValidationError pokud email neexistuje.
    """
    ds = get_data_session()
    try:
        email = ds.query(EmailInbox).filter_by(id=inbox_id).first()
        if email is None:
            raise EmailInboxValidationError(f"Email id={inbox_id} neexistuje")
        sender = email.from_email
        subj = email.subject or "(bez předmětu)"
        persona_id = email.persona_id
        tenant_id = email.tenant_id
    finally:
        ds.close()

    if persona_id is None:
        raise EmailInboxValidationError(
            f"Email id={inbox_id} nema persona mapping -- nelze spustit AI task "
            f"(persona kanal pravdepodobne chybi)"
        )

    # Lazy import tasks -- stejny pattern jako u SMS (zabranime cyklu).
    from modules.tasks.application import service as task_service

    # Title: kratka verze pro UI list. 255 znaku limit v DB.
    preview_subj = subj[:120]
    title = f"Email od {sender}: {preview_subj}"
    if len(title) > 255:
        title = title[:252] + "..."

    task = task_service.create_task_from_source(
        tenant_id=tenant_id,
        persona_id=persona_id,
        source_type="email_inbox",
        source_id=inbox_id,
        title=title,
        description=(email.body or f"Email od {sender}, předmět: {subj}"),
        priority="normal",
    )
    logger.info(
        f"EMAIL | inbox | suggest_reply | email_id={inbox_id} | "
        f"task_id={task['id']} | persona={persona_id}"
    )
    return {
        "email_id": inbox_id,
        "task_id": task["id"],
        "status": task["status"],
        "title": task["title"],
    }


def reply_to_inbox(
    *,
    inbox_id: int,
    body: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
) -> dict:
    """
    Odpoved na prichozi email:
      1. queue_email() -- zapise do email_outbox (worker pote odesle pres EWS)
      2. email_inbox.processed_at = now (presun do 'Zpracovane')
      3. cancel open tasku nad timto emailem (user odpovedel primo)

    In-progress tasky ponechame (jejich executor uz claim ma). Done tasky
    zustavaji pro audit.

    Vraci dict:
      {
        "email_id": int,
        "outbox_id": int,
        "outbox_status": "pending",
        "processed_at": iso-str,
        "cancelled_tasks": int,
      }
    """
    from modules.notifications.application.email_service import queue_email

    ds = get_data_session()
    try:
        email = ds.query(EmailInbox).filter(EmailInbox.id == inbox_id).first()
        if email is None:
            raise EmailInboxValidationError(f"Email id={inbox_id} neexistuje")
        to_email_addr = email.from_email
        persona_id = email.persona_id
        effective_tenant = tenant_id if tenant_id is not None else email.tenant_id
        orig_subject = email.subject or ""
    finally:
        ds.close()

    # Reply subject: "Re: " prefix pokud tam jeste neni.
    reply_subject = orig_subject if orig_subject.lower().startswith("re:") else f"Re: {orig_subject}"

    # 1) Do email_outbox -- worker pote odesle
    outbox = queue_email(
        to=to_email_addr,
        subject=reply_subject.strip() or "Re:",
        body=body,
        persona_id=persona_id,
        tenant_id=effective_tenant,
        user_id=user_id,
        from_identity="persona",
        purpose="user_request",
    )

    # 2) Mark processed + 3) cancel tasky
    from modules.core.infrastructure.models_data import Task as _Task
    now = datetime.now(timezone.utc)
    cancelled = 0
    ds = get_data_session()
    try:
        email_row = ds.query(EmailInbox).filter(EmailInbox.id == inbox_id).first()
        if email_row is not None and email_row.processed_at is None:
            email_row.processed_at = now
            if email_row.read_at is None:
                email_row.read_at = now

        open_tasks = (
            ds.query(_Task)
            .filter(
                _Task.source_type == "email_inbox",
                _Task.source_id == inbox_id,
                _Task.status == "open",
            )
            .all()
        )
        for t in open_tasks:
            t.status = "cancelled"
            t.completed_at = now
            t.result_summary = "[zruseno] user odpovedel primo z UI"
            cancelled += 1

        ds.commit()
    finally:
        ds.close()

    logger.info(
        f"EMAIL | inbox | reply sent | email_id={inbox_id} | outbox_id={outbox['id']} | "
        f"cancelled_tasks={cancelled}"
    )

    return {
        "email_id": inbox_id,
        "outbox_id": outbox["id"],
        "outbox_status": outbox["status"],
        "processed_at": now.isoformat(),
        "cancelled_tasks": cancelled,
    }


def get_draft_for_inbox(inbox_id: int) -> dict:
    """
    Vrati nejnovejsi non-empty result_summary z tasku nad timto emailem --
    UI ho pouzije pro prefill reply textarea (AI uz napsala draft).

    Priorita statusu: done > in_progress > failed.

    Return:
      {"draft": str | None, "task_id": int | None, "task_status": str | None}
    """
    from modules.core.infrastructure.models_data import Task as _Task

    ds = get_data_session()
    try:
        for preferred_status in ("done", "in_progress", "failed"):
            t = (
                ds.query(_Task)
                .filter(
                    _Task.source_type == "email_inbox",
                    _Task.source_id == inbox_id,
                    _Task.status == preferred_status,
                    _Task.result_summary.isnot(None),
                )
                .order_by(_Task.completed_at.desc().nulls_last(), _Task.id.desc())
                .first()
            )
            if t is not None and t.result_summary:
                return {
                    "draft": t.result_summary,
                    "task_id": t.id,
                    "task_status": t.status,
                }
        return {"draft": None, "task_id": None, "task_status": None}
    finally:
        ds.close()


def list_personal_for_ui(
    *,
    persona_id: int,
    tenant_id: int | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Personal tab (Faze 7.8) -- merged view rodicovske korespondence:
    (a) incoming emaily kde meta.archived_personal=true
    (b) outgoing emaily kde to_email odpovida rodici Marti (is_marti_parent)

    Vraci unified list serazeny od nejnovejsich. Kazdy zaznam ma 'direction'
    field ('in'|'out') pro UI ikonku sipky.

    Incoming archivace se deje automaticky v ews_fetcher (Faze 6). Outgoing
    detekujeme at read-time pres _is_parent_email (stejny pattern jako
    archivace pri sendu -- neni nutna DB migrace).
    """
    from modules.core.infrastructure.models_data import EmailOutbox
    from modules.notifications.application.email_service import _is_parent_email
    import json as _json

    ds = get_data_session()
    try:
        # (a) Incoming - filter na archived_personal flag v meta
        incoming_rows = (
            ds.query(EmailInbox)
            .filter(EmailInbox.persona_id == persona_id)
            .order_by(EmailInbox.received_at.desc())
            .limit(max(1, min(limit * 2, 400)))  # over-fetch, post-filter archived
            .all()
        )
        incoming_items = []
        for r in incoming_rows:
            if not _is_archived(r.meta):
                continue
            incoming_items.append({
                "id": r.id,
                "direction": "in",
                "source_type": "inbox",
                "from_email": r.from_email,
                "from_name": r.from_name,
                "to_email": r.to_email,
                "subject": r.subject,
                "body": r.body,
                "ts": r.received_at.isoformat() if r.received_at else None,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            })

        # (b) Outgoing - per-row kontrola, ze to_email je rodic
        outgoing_q = ds.query(EmailOutbox).filter(EmailOutbox.persona_id == persona_id)
        if tenant_id is not None:
            outgoing_q = outgoing_q.filter(EmailOutbox.tenant_id == tenant_id)
        outgoing_rows = (
            outgoing_q
            .order_by(EmailOutbox.created_at.desc())
            .limit(max(1, min(limit * 2, 400)))
            .all()
        )
        outgoing_items = []
        for r in outgoing_rows:
            if not _is_parent_email(r.to_email):
                continue
            outgoing_items.append({
                "id": r.id,
                "direction": "out",
                "source_type": "outbox",
                "from_email": None,
                "from_name": None,
                "to_email": r.to_email,
                "subject": r.subject,
                "body": r.body,
                "ts": (r.sent_at or r.created_at).isoformat() if (r.sent_at or r.created_at) else None,
                "status": r.status,
            })

        # Merge + sort by ts desc
        merged = incoming_items + outgoing_items
        merged.sort(key=lambda x: x.get("ts") or "", reverse=True)
        return merged[:limit]
    finally:
        ds.close()


def list_outbox_for_ui(
    *,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Seznam odchozich emailu pro tab 'Odeslane'. Razeno od nejnovejsich.
    Filtrujeme podle persona_id (vlastnik kanalu) + tenant_id pro izolaci.
    """
    from modules.core.infrastructure.models_data import EmailOutbox
    import json as _json

    ds = get_data_session()
    try:
        q = ds.query(EmailOutbox)
        if persona_id is not None:
            q = q.filter(EmailOutbox.persona_id == persona_id)
        if tenant_id is not None:
            q = q.filter(EmailOutbox.tenant_id == tenant_id)
        rows = (
            q.order_by(EmailOutbox.created_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )
        result = []
        for r in rows:
            cc_list = _json.loads(r.cc) if r.cc else []
            result.append({
                "id": r.id,
                "to_email": r.to_email,
                "cc": cc_list,
                "subject": r.subject,
                "body": r.body,
                "status": r.status,
                "purpose": r.purpose,
                "attempts": r.attempts,
                "last_error": r.last_error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            })
        return result
    finally:
        ds.close()
