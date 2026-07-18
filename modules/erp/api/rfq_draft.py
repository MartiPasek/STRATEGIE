"""
RFQ / e-mailové koncepty (Vydané poptávky) — Claude ID23, 18. 7. 2026.

Cíl (Marti item 1): naučit se vytvářet KONCEPTY e-mailů. AI složí kompletní
e-mail (poptávku dodavateli) a "odešle" ho do složky Koncepty (Drafts) v
Exchange — BEZ reálného odeslání. Člověk si ho ve schránce zkontroluje a
případně odešle. Odpovědi pak chodí do té samé schránky, ze které se poptávka
odeslala (návazně budeme sledovat příjem nabídek → napojení na vypopt_nabidka).

Základ = existující EWS infrastruktura v email_service.py (exchangelib). Draft
se od odeslání liší jen tím, že místo `message.send_and_save()` voláme
`message.save()` do složky `account.drafts` (distinguished folder, mapuje se
na "Koncepty" bez ohledu na jazyk schránky).
"""
from __future__ import annotations

from core.config import settings
from core.logging import get_logger

from modules.notifications.application.email_service import (
    _get_account,
    _parse_recipients,
    _apply_persona_signature,
    _load_attachment_files,
    _resolve_persona_email_creds,
    _resolve_user_email_creds,
    _is_auth_error,
    EmailNoUserChannelError,
    EmailAuthError,
    EmailSendError,
)

logger = get_logger("erp.rfq_draft")


def create_email_draft(
    to,
    subject: str,
    body: str,
    persona_id: int | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    from_identity: str = "user",
    cc=None,
    bcc=None,
    attachment_document_ids: list[int] | None = None,
    attachment_paths: list[str] | None = None,
    html_body: bool = False,
    inline_images: list | None = None,
) -> dict:
    """
    Sestaví kompletní e-mail a ULOŽÍ ho jako KONCEPT do složky Koncepty (Drafts)
    ve schránce. NEODESÍLÁ. Vrací dict {ok, draft_id, folder, sender, to, ...}.

    Výběr schránky (creds):
      from_identity="user"    → z EWS kanálu uživatele (users.ews_*), user_id povinné.
      from_identity="persona" → z persona_channels (persona_id).
      fallback (bez creds)    → globální settings.ews_* (systémová schránka).

    Přílohy:
      attachment_document_ids → z tabulky documents (jako u send_email).
      attachment_paths        → absolutní cesty souborů na hostiteli API.
    """
    from exchangelib import Message, Mailbox

    to_list = _parse_recipients(to)
    if not to_list:
        raise EmailSendError("žádný platný příjemce v `to`")
    cc_list = _parse_recipients(cc)
    bcc_list = _parse_recipients(bcc)

    # --- credentialy schránky ---
    if from_identity == "user":
        creds = _resolve_user_email_creds(user_id)
        if not creds:
            raise EmailNoUserChannelError(
                f"user_id={user_id} nemá nakonfigurovaný EWS kanál"
            )
    else:
        creds = _resolve_persona_email_creds(persona_id, tenant_id)

    if creds:
        account = _get_account(
            email=creds["email"],
            password=creds["password"],
            server=creds["server"],
        )
        sender = creds.get("display_email") or creds["email"]
    else:
        account = _get_account()
        sender = settings.ews_email

    # --- složka Koncepty (Drafts) ---
    try:
        drafts_folder = account.drafts
    except Exception as e:
        raise EmailSendError(f"nelze najít složku Koncepty (Drafts): {e}")

    msg_kwargs: dict = {
        "account": account,
        "folder": drafts_folder,
        "subject": subject,
        "to_recipients": [Mailbox(email_address=a) for a in to_list],
    }
    if cc_list:
        msg_kwargs["cc_recipients"] = [Mailbox(email_address=a) for a in cc_list]
    if bcc_list:
        msg_kwargs["bcc_recipients"] = [Mailbox(email_address=a) for a in bcc_list]

    sig_attachments: list = []
    if html_body:
        try:
            from exchangelib import HTMLBody
            msg_kwargs["body"] = HTMLBody(body)
        except Exception:
            msg_kwargs["body"] = body
    else:
        # persona_id=None → noop, body zůstane plain (žádný cizí podpis)
        sig_body, sig_attachments = _apply_persona_signature(persona_id, body)
        msg_kwargs["body"] = sig_body

    message = Message(**msg_kwargs)

    for _att in sig_attachments:
        try:
            message.attach(_att)
        except Exception as _e:
            logger.warning(f"DRAFT | signature attach failed: {_e}")

    if inline_images:
        import os as _os, mimetypes as _mt
        from exchangelib import FileAttachment
        for _ii in inline_images:
            try:
                _fp, _cid = _ii
                with open(_fp, "rb") as _fh:
                    _data = _fh.read()
                _ct = _mt.guess_type(_fp)[0] or "application/octet-stream"
                message.attach(FileAttachment(
                    name=_os.path.basename(_fp), content=_data,
                    content_id=_cid, content_type=_ct, is_inline=True))
            except Exception as _e:
                logger.warning(f"DRAFT | inline attach failed: {_e}")

    if attachment_document_ids:
        try:
            for _da in _load_attachment_files(
                attachment_document_ids, caller_tenant_id=tenant_id, is_parent=True
            ):
                try:
                    message.attach(_da)
                except Exception as _e:
                    logger.warning(f"DRAFT | doc attach failed: {_e}")
        except (ValueError, PermissionError, OverflowError) as _e:
            raise EmailSendError(f"Příloha selhala: {_e}")

    if attachment_paths:
        import os as _os2
        from exchangelib import FileAttachment as _FA2
        for _fp in attachment_paths:
            try:
                with open(_fp, "rb") as _fh:
                    _data = _fh.read()
                message.attach(_FA2(name=_os2.path.basename(_fp), content=_data))
            except Exception as _e:
                logger.warning(f"DRAFT | file attach failed ({_fp}): {_e}")

    # --- ULOŽIT jako koncept (NE odeslat) ---
    try:
        message.save()  # CreateItem do drafts_folder, žádný SendItem
    except Exception as e:
        if _is_auth_error(e):
            logger.error(f"DRAFT | auth-failed | to={to_list} | {e}")
            raise EmailAuthError(str(e)) from e
        logger.error(f"DRAFT | save failed | to={to_list} | {e}")
        raise EmailSendError(str(e)) from e

    draft_id = getattr(message, "id", None)
    logger.info(
        f"EMAIL DRAFT | uložen | from={sender} | to={to_list} | "
        f"cc={cc_list or '-'} | subj={subject!r} | "
        f"folder={getattr(drafts_folder, 'name', None)}"
    )
    return {
        "ok": True,
        "draft_id": draft_id,
        "folder": getattr(drafts_folder, "name", None),
        "sender": sender,
        "to": to_list,
        "cc": cc_list,
        "bcc": bcc_list,
        "subject": subject,
    }


# ── @@ příkaz pro most (test / ruční tvorba konceptu) ─────────────────────────
#
# Formát:
#   @@RFQDRAFT TEST
#       → uloží testovací koncept do schránky Marti (user 1), příjemce = on sám.
#   @@RFQDRAFT user=<id> to=<email[,email]> [cc=<email>] subj=<...> | <tělo>
#       → uloží koncept z uživatelské schránky. Tělo je za znakem '|'.
#
def rfq_draft_cmd(rest: str) -> dict:
    """Dispatch handler pro @@RFQDRAFT (most → JSONResponse columns/rows)."""
    raw = (rest or "").strip()

    def _err(msg: str) -> dict:
        return {"ok": True, "columns": ["chyba"], "rows": [[msg]]}

    try:
        if raw.upper().startswith("TEST") or raw == "":
            res = create_email_draft(
                to="m.pasek@eurosoft.com",
                subject="STRATEGIE — test konceptu (Claude ID23)",
                body=(
                    "Ahoj Marti,\n\n"
                    "tohle je testovací KONCEPT vytvořený systémem STRATEGIE "
                    "(Claude ID23). Uložil jsem ho do složky Koncepty ve Tvé "
                    "schránce — nikam se neodeslal.\n\n"
                    "Pokud ho tam vidíš, umíme skládat vydané poptávky jako "
                    "koncepty a lidi je jen zkontrolují a odešlou.\n\n"
                    "— STRATEGIE"
                ),
                user_id=1,
                from_identity="user",
            )
            return {
                "ok": True,
                "columns": ["výsledek", "schránka", "složka", "příjemce", "draft_id"],
                "rows": [[
                    "KONCEPT uložen ✓",
                    res.get("sender"),
                    res.get("folder"),
                    ", ".join(res.get("to") or []),
                    (res.get("draft_id") or "")[:40] if res.get("draft_id") else "",
                ]],
            }

        # parsování: klíč=hodnota tokeny do '|', za '|' je tělo
        head, _, body = raw.partition("|")
        body = body.strip() or "(prázdné tělo)"
        toks = head.split()
        params: dict = {}
        subj_parts: list[str] = []
        for t in toks:
            if "=" in t and t.split("=", 1)[0] in ("user", "to", "cc", "subj", "persona", "tenant"):
                k, v = t.split("=", 1)
                params[k] = v
            else:
                subj_parts.append(t)
        # subj může být buď subj=... nebo volný text (mimo jiné klíče)
        subject = params.get("subj") or " ".join(subj_parts) or "(bez předmětu)"
        subject = subject.replace("_", " ")

        to = params.get("to")
        if not to:
            return _err("chybí to=<email>")
        user_id = int(params["user"]) if params.get("user") else None
        persona_id = int(params["persona"]) if params.get("persona") else None
        tenant_id = int(params["tenant"]) if params.get("tenant") else None
        from_identity = "persona" if persona_id else "user"

        res = create_email_draft(
            to=to,
            subject=subject,
            body=body,
            cc=params.get("cc"),
            user_id=user_id,
            persona_id=persona_id,
            tenant_id=tenant_id,
            from_identity=from_identity,
        )
        return {
            "ok": True,
            "columns": ["výsledek", "schránka", "složka", "příjemce", "předmět"],
            "rows": [[
                "KONCEPT uložen ✓",
                res.get("sender"),
                res.get("folder"),
                ", ".join(res.get("to") or []),
                res.get("subject"),
            ]],
        }
    except EmailNoUserChannelError as e:
        return _err(f"schránka nenakonfigurována: {e}")
    except (EmailAuthError, EmailSendError) as e:
        return _err(f"selhalo: {e}")
    except Exception as e:
        return _err(f"neočekávaná chyba: {type(e).__name__}: {e}")
