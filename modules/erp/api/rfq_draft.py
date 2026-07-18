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
def poptavka_koncept(
    doklad: str,
    to_email: str,
    to_name: str,
    dodavatel: str,
    polozka: str,
    mnozstvi: str,
    termin: str | None,
    user_id: int,
    cc: str | None = None,
    send: bool = False,
) -> dict:
    """
    Složí konkrétní poptávkový e-mail (RFQ) jménem uživatele (schránka user_id).
    send=False → uloží jako KONCEPT do Konceptů; send=True → reálně odešle.
    """
    osloveni = "Dobrý den,"
    termin_veta = ("Požadovaný termín dodání: %s.\n" % termin) if termin else ""
    body = (
        "%s\n\n"
        "obracíme se na Vás s poptávkou a prosíme o cenovou nabídku na následující položku:\n\n"
        "  • %s — %s ks\n\n"
        "Prosíme o uvedení jednotkové ceny, dodací lhůty a platnosti nabídky.\n"
        "Naše číslo poptávky: %s.\n"
        "%s\n"
        "Předem děkuji za Vaši nabídku.\n\n"
        "S pozdravem\n"
        "Eliška Kolářová\n"
        "nákup / EUROSOFT-Control s.r.o."
        % (osloveni, polozka, mnozstvi, doklad, termin_veta)
    )
    subject = "Poptávka %s — %s" % (doklad, polozka)
    if send:
        from modules.notifications.application.email_service import send_email_or_raise
        send_email_or_raise(
            to=to_email,
            subject=subject,
            body=body,
            cc=cc,
            user_id=user_id,
            from_identity="user",
        )
        return {"ok": True, "sender": "e.kolarova@eurosoft-control.cz",
                "folder": "ODESLÁNO", "to": _parse_recipients(to_email),
                "cc": _parse_recipients(cc), "subject": subject, "draft_id": None}
    return create_email_draft(
        to=to_email,
        subject=subject,
        body=body,
        cc=cc,
        user_id=user_id,
        from_identity="user",
    )


def read_mailbox_inbox(user_id: int, limit: int = 8) -> list[dict]:
    """Přečti posledních N zpráv z inboxu schránky uživatele (EWS)."""
    creds = _resolve_user_email_creds(user_id)
    if not creds:
        raise EmailNoUserChannelError("user_id=%s nemá EWS kanál" % user_id)
    account = _get_account(email=creds["email"], password=creds["password"], server=creds["server"])
    out = []
    for msg in account.inbox.all().order_by("-datetime_received")[:limit]:
        try:
            sender = getattr(msg.sender, "email_address", None) if getattr(msg, "sender", None) else None
            dt = getattr(msg, "datetime_received", None)
            body = getattr(msg, "text_body", None) or getattr(msg, "body", None) or ""
            body = " ".join(str(body).split())
            out.append({
                "id": getattr(msg, "id", None),
                "subject": getattr(msg, "subject", None),
                "from": sender,
                "dt": str(dt)[:19] if dt else None,
                "preview": body[:240],
                "text": body[:2000],
            })
        except Exception as _e:
            logger.warning("read_mailbox_inbox item failed: %s" % _e)
    return out


def rfq_inbox_cmd(rest: str) -> dict:
    """@@RFQINBOX <user_id> [n] — přečti inbox schránky uživatele."""
    toks = (rest or "").split()

    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    if not toks or not toks[0].isdigit():
        return _err("použij: @@RFQINBOX <user_id> [pocet]")
    uid = int(toks[0])
    n = int(toks[1]) if len(toks) > 1 and toks[1].isdigit() else 8
    try:
        msgs = read_mailbox_inbox(uid, n)
        if not msgs:
            return {"ok": True, "columns": ["inbox"], "rows": [["(prázdný)"]]}
        rows = [["%s | %s" % (m.get("dt") or "?", m.get("from") or "?"),
                 "%s — %s" % (m.get("subject") or "(bez předmětu)", m.get("preview") or "")] for m in msgs]
        return {"ok": True, "columns": ["kdy | od", "předmět — náhled"], "rows": rows}
    except EmailNoUserChannelError as e:
        return _err("schránka nenakonfigurována: %s" % e)
    except Exception as e:
        return _err("čtení inboxu selhalo: %s: %s" % (type(e).__name__, e))


def _parse_nabidka(text: str) -> dict:
    """Z textu nabídky vytáhne cenu, měnu, platnost, dodací lhůtu (best-effort)."""
    import re
    out = {}
    # cena + měna: "1500EUR", "1 500,00 EUR", "1500 €", "12 345 Kč"
    m = re.search(r'(\d[\d\s\.]*?)(?:,(\d+))?\s*(EUR|€|K[čc]|CZK)', text, re.IGNORECASE)
    if m:
        whole = m.group(1).replace(" ", "").replace(".", "")
        dec = m.group(2) or "0"
        try:
            out["cena"] = float("%s.%s" % (whole, dec))
        except Exception:
            pass
        mena = m.group(3).upper()
        out["mena"] = "EUR" if mena in ("EUR", "€") else "CZK"
    # platnost: "do 15.9.2026", "platná do 15. 9. 2026"
    mp = re.search(r'plat[a-zíé]*\s*(?:do)?\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', text, re.IGNORECASE)
    if not mp:
        mp = re.search(r'do\s+(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', text, re.IGNORECASE)
    if mp:
        out["platnost_do"] = "%s-%02d-%02d" % (mp.group(3), int(mp.group(2)), int(mp.group(1)))
    # dodací lhůta: "14 dni", "dodaci termin je 14 dní", "KW 36"
    md = re.search(r'(\d+)\s*(dn[íiy]|dní|t[ýy]dn|weeks?|Tage?)', text, re.IGNORECASE)
    if md:
        out["dodaci_lhuta"] = md.group(0)
    return out


def fetch_message_mime(user_id: int, subject_contains: str) -> dict | None:
    """Najde v inboxu zprávu dle předmětu a vrátí její kompletní MIME (.eml bytes)."""
    creds = _resolve_user_email_creds(user_id)
    if not creds:
        raise EmailNoUserChannelError("user_id=%s nemá EWS kanál" % user_id)
    account = _get_account(email=creds["email"], password=creds["password"], server=creds["server"])
    for msg in account.inbox.all().order_by("-datetime_received")[:15]:
        if subject_contains in (getattr(msg, "subject", None) or ""):
            mime = getattr(msg, "mime_content", None)
            if isinstance(mime, str):
                mime = mime.encode("utf-8", "replace")
            sender = getattr(msg.sender, "email_address", None) if getattr(msg, "sender", None) else None
            return {"subject": msg.subject, "from": sender, "mime": mime,
                    "bytes": len(mime) if mime else 0}
    return None


def rfq_msg_cmd(rest: str) -> dict:
    """
    @@RFQMSG — vezme celý e-mail s nabídkou (EVP260231) z Elišciny schránky jako MIME
    a uloží ho jako .eml do složky poptávky (D:\\Data\\poptavky_V\\EVP260231).
    """
    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    try:
        from modules.erp.api.rfq_doklad import save_bytes_to_poptavka_dir
        doklad = "EVP260231"
        subj_key = doklad
        arg = (rest or "").strip()
        if arg:
            subj_key = arg
        m = fetch_message_mime(34, subj_key)
        if not m or not m.get("mime"):
            return _err("v Elišcině schránce jsem nenašel zprávu (%s) nebo nemá MIME" % subj_key)
        fname = "%s.eml" % doklad
        r = save_bytes_to_poptavka_dir(doklad, fname, m["mime"])
        if not r.get("ok"):
            return _err("uložení .eml selhalo: %s" % (r.get("error") or r))
        return {
            "ok": True,
            "columns": ["výsledek", "soubor", "velikost", "od / předmět"],
            "rows": [[
                "Celý e-mail uložen jako .eml ✓",
                "D:\\Data\\poptavky_V\\%s\\%s" % (doklad, fname),
                "%s B" % m.get("bytes"),
                "%s — %s" % (m.get("from") or "?", m.get("subject") or ""),
            ]],
        }
    except EmailNoUserChannelError as e:
        return _err("schránka nenakonfigurována: %s" % e)
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))


def rfq_finish_cmd(rest: str) -> dict:
    """
    @@RFQFINISH — doplní na poptávku EVP260231 řešitele (Eliška), kontaktní osobu
    (P. Kunová), druh ceny (Obecná) a uloží přijatou nabídku (e-mail) do adresáře
    poptávky na sdíleném disku.
    """
    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    try:
        from modules.erp.api.rfq_doklad import (
            update_poptavka_header, update_poptavka_nabidka, save_file_to_poptavka_dir,
        )
        doklad = "EVP260231"
        doklad_id = 751135
        # 1) řešitel Eliška (CisloZam=24) + kontaktní osoba P. Kunová (TabCisKOs.ID=198)
        uh = update_poptavka_header(doklad_id, cislo_zam=24, kontakt_osoba=198)
        # 2) druh ceny Obecná (1)
        un = update_poptavka_nabidka(doklad_id, druh_ceny=1)
        # 3) nabídku (e-mail) do adresáře poptávky
        msgs = read_mailbox_inbox(34, 10)
        m = next((x for x in msgs if doklad in (x.get("subject") or "")), None)
        saved = "-"
        if m:
            obsah = (
                "Přijatá nabídka k poptávce %s\n"
                "Od: %s\nDatum: %s\nPředmět: %s\n\n%s\n"
                % (doklad, m.get("from"), m.get("dt"), m.get("subject"), m.get("text") or m.get("preview"))
            )
            sr = save_file_to_poptavka_dir(doklad, "nabidka_%s.txt" % doklad, obsah)
            saved = ("uloženo do %s\\nabidka_%s.txt" % ("D:\\Data\\poptavky_V\\" + doklad, doklad)) if sr.get("ok") else ("uložení selhalo: %s" % (sr.get("error") or sr))
        else:
            saved = "nabídkový e-mail k %s ve schránce nenalezen" % doklad
        return {
            "ok": True,
            "columns": ["krok", "stav"],
            "rows": [
                ["řešitel Eliška (CisloZam=24)", "OK ✓" if uh.get("ok") else ("SELHAL: %s" % uh.get("error"))],
                ["kontaktní osoba P. Kunová (198)", "OK ✓" if uh.get("ok") else "-"],
                ["druh ceny = Obecná (1)", "OK ✓" if un.get("ok") else ("SELHAL: %s" % un.get("error"))],
                ["nabídka do adresáře", saved],
            ],
        }
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))


def rfq_react_cmd(rest: str) -> dict:
    """
    @@RFQREACT — najde v Elišcině schránce odpověď na poptávku EVP260231, vytáhne
    nabídku (cena/platnost/lhůta), zapíše ji na doklad (EXT nabídková pole) a pošle
    potvrzení odesílateli. Reakce na přijatou nabídku (item 3).
    """
    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    try:
        from modules.erp.api.rfq_doklad import (
            update_poptavka_nabidka, read_poptavka_nabidka,
        )
        from modules.notifications.application.email_service import send_email_or_raise
        doklad = "EVP260231"
        doklad_id = 751135
        uid = 34
        msgs = read_mailbox_inbox(uid, 10)
        m = next((x for x in msgs if doklad in (x.get("subject") or "")), None)
        if not m:
            return _err("v Elišcině schránce jsem nenašel odpověď na %s" % doklad)
        text = m.get("text") or m.get("preview") or ""
        parsed = _parse_nabidka(text)
        if not parsed.get("cena"):
            return _err("z odpovědi jsem nevytáhl cenu — text: %s" % text[:160])
        popis = "Diagnostický přístroj CDM11A"
        if parsed.get("dodaci_lhuta"):
            popis = "%s (dodání %s)" % (popis, parsed["dodaci_lhuta"])
        cislo_nab = "e-mail %s" % (m.get("dt") or "")[:10]
        up = update_poptavka_nabidka(
            doklad_id,
            cena=parsed.get("cena"),
            platnost_do=parsed.get("platnost_do"),
            dodavatel="SEW-EURODRIVE CZ s.r.o.",
            popis=popis,
            cislo_nabidky=cislo_nab,
        )
        if not up.get("ok"):
            return _err("zápis nabídky na doklad selhal: %s" % up.get("error"))
        nb = read_poptavka_nabidka(doklad_id)
        # potvrzení odesílateli (jménem Elišky)
        odeslano = "-"
        sender_email = m.get("from")
        if sender_email:
            try:
                send_email_or_raise(
                    to=sender_email,
                    subject="RE: Poptávka %s — děkujeme za nabídku" % doklad,
                    body=(
                        "Dobrý den,\n\n"
                        "děkujeme za Vaši nabídku k poptávce %s (Diagnostický přístroj CDM11A). "
                        "Nabídku jsme zaevidovali: cena %s %s, platnost do %s. "
                        "Ozveme se s objednávkou.\n\n"
                        "S pozdravem\nEliška Kolářová\nnákup / EUROSOFT-Control s.r.o."
                        % (doklad, parsed.get("cena"), parsed.get("mena") or "EUR",
                           parsed.get("platnost_do") or "-")
                    ),
                    user_id=uid,
                    from_identity="user",
                )
                odeslano = "potvrzení odesláno na %s" % sender_email
            except Exception as _e:
                odeslano = "potvrzení se nepodařilo: %s" % _e
        return {
            "ok": True,
            "columns": ["krok", "hodnota"],
            "rows": [
                ["nabídka rozpoznána", "cena %s %s, platnost %s, lhůta %s" % (
                    parsed.get("cena"), parsed.get("mena") or "EUR",
                    parsed.get("platnost_do") or "?", parsed.get("dodaci_lhuta") or "?")],
                ["zapsáno na doklad %s" % doklad, "cena=%s platnost=%s dodavatel=%s" % (
                    nb.get("cena"), nb.get("platnost"), nb.get("dodavatel"))],
                ["potvrzení", odeslano],
                ["→ 4. cenový zdroj", "@@VYPOPT SYNC pak nabídku vtáhne do vypopt_nabidka"],
            ],
        }
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))


def rfq_send_cmd(rest: str) -> dict:
    """
    @@RFQSEND DEMO — konkrétní poptávka jménem Elišky (user 34) na SEW-EURODRIVE
    (doklad EVP260231), položka diagnostický přístroj CDM11A, prodejkyni P. Kunové.
    Uloží KONCEPT do Elišciny schránky. NEODESÍLÁ.
    """
    raw = (rest or "").strip()

    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    try:
        if not raw or raw.upper().startswith("DEMO"):
            from modules.erp.api.rfq_doklad import read_poptavka, update_poptavka_ext
            doklad = "EVP260231"
            doklad_id = 751135
            polozka = "Diagnostický přístroj SEW CDM11A"
            # sjednoť název poptávky na dokladu s položkou (koherence doklad↔e-mail)
            update_poptavka_ext(doklad_id, polozka)
            hdr = read_poptavka(doklad_id)
            termin = hdr.get("termin")  # 'YYYY-MM-DD'
            termin_cz = None
            if termin:
                try:
                    y, m, d = termin.split("-")
                    termin_cz = "%d. %d. %s" % (int(d), int(m), y)
                except Exception:
                    termin_cz = termin
            res = poptavka_koncept(
                doklad=doklad,
                to_email="m.pasek@eurosoft.com",
                to_name="Kunová Pavla",
                dodavatel="SEW-EURODRIVE CZ s.r.o.",
                polozka=polozka,
                mnozstvi="1",
                termin=termin_cz,
                user_id=34,
                send=True,
            )
            return {
                "ok": True,
                "columns": ["výsledek", "odesláno z", "komu", "předmět"],
                "rows": [[
                    "Poptávka ODESLÁNA ✓ (jménem Elišky)",
                    res.get("sender"),
                    ", ".join(res.get("to") or []),
                    res.get("subject"),
                ]],
            }
        return _err("použij: @@RFQSEND DEMO")
    except EmailNoUserChannelError as e:
        return _err("Elišcina schránka nenakonfigurována: %s" % e)
    except (EmailAuthError, EmailSendError) as e:
        return _err("selhalo: %s" % e)
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))


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
