# -*- coding: utf-8 -*-
"""Zrcadlo poštovní schránky uživatele (EWS → PG tenant.mail_message).

Fáze 1 = jen prohlížeč: čteme Doručené/Odeslané/Koncepty, ukládáme hlavičky +
text těla + přílohy (do dokumentů). Do Outlooku NEZAPISUJEME. `stav` (nove/
zpracovane) je NÁŠ sticky příznak — sync ho u existující zprávy nepřepisuje.

Přihlášení: username = users.ews_email (plný e-mail/UPN), schránka = ews_display_email.
Heslo se jen dešifruje pro EWS, nikdy se nevrací ani neloguje.  ID23, 3.7.2026.
"""
import json
import logging
import threading

from sqlalchemy import text
from core.database_data import get_data_session
from core.crypto import decrypt

logger = logging.getLogger(__name__)

_SLOZKY = ("dorucene", "odeslane", "koncepty")


def _account_for_user(uid: int):
    s = get_data_session()
    try:
        r = s.execute(text(
            "SELECT ews_email, ews_password_encrypted, ews_server, ews_display_email "
            "FROM public.users WHERE id=:i"), {"i": uid}).fetchone()
    finally:
        s.close()
    if not r or not r[0] or not r[1]:
        raise RuntimeError("uživatel nemá napojenou schránku (ews_email/heslo)")
    login, pw_enc, server, display = r[0], r[1], r[2], r[3]
    pw = decrypt(pw_enc)
    smtp = display or login
    import urllib3
    urllib3.disable_warnings()
    from exchangelib import Credentials, Account, Configuration, DELEGATE
    cfg = Configuration(
        server=str(server or "").replace("https://", "").replace("http://", ""),
        credentials=Credentials(username=login, password=pw))
    acct = Account(primary_smtp_address=smtp, config=cfg, autodiscover=False, access_type=DELEGATE)
    pw = None
    return acct


def _folder(acct, slozka):
    if slozka == "dorucene":
        return acct.inbox
    if slozka == "odeslane":
        return acct.sent
    if slozka == "koncepty":
        return acct.drafts
    raise ValueError("neznámá složka %s" % slozka)


def _recips_str(recips):
    try:
        return ", ".join([(getattr(x, "email_address", None) or getattr(x, "name", "") or "")
                           for x in (recips or [])])[:1000] or None
    except Exception:
        return None


def _save_attachments(m, uid: int, tenant_id: int):
    from modules.rag.application.service import upload_document
    ids = []
    try:
        for a in (m.attachments or []):
            try:
                content = getattr(a, "content", None)  # jen FileAttachment
                if content is None:
                    continue
                name = getattr(a, "name", None) or "priloha"
                did = upload_document(file_bytes=content, filename=name,
                                      tenant_id=tenant_id, user_id=uid)
                ids.append(did)
            except Exception as e:
                logger.warning("[mail] priloha selhala: %s", str(e)[:120])
    except Exception:
        pass
    return ids or None


def sync_folder(uid: int, slozka: str, limit: int = 300,
                with_attachments: bool = True, tenant_id: int = 2, acct=None) -> dict:
    if acct is None:
        acct = _account_for_user(uid)
    fld = _folder(acct, slozka)
    try:
        qs = fld.all().order_by("-datetime_received")[:limit]
    except Exception:
        qs = fld.all()[:limit]
    s = get_data_session()
    n = 0
    nnew = 0
    try:
        for m in qs:
            try:
                iid = getattr(m, "id", None) or getattr(m, "item_id", None)
                if iid is None:
                    continue
                iid = str(iid)
                ck = str(getattr(m, "changekey", "") or "")
                dt = getattr(m, "datetime_received", None) or getattr(m, "datetime_sent", None)
                od_email = od_jmeno = None
                snd = getattr(m, "sender", None) or getattr(m, "author", None)
                if snd is not None:
                    od_email = getattr(snd, "email_address", None)
                    od_jmeno = getattr(snd, "name", None)
                komu = _recips_str(getattr(m, "to_recipients", None))
                kopie = _recips_str(getattr(m, "cc_recipients", None))
                subj = (getattr(m, "subject", None) or "")[:500]
                telo = getattr(m, "text_body", None)
                if not telo:
                    b = getattr(m, "body", None)
                    telo = str(b) if b else None
                if telo:
                    telo = telo.replace("\x00", "")[:100000]
                hasatt = bool(getattr(m, "has_attachments", False))
                unread = (getattr(m, "is_read", True) is False)
                ex = s.execute(text(
                    "SELECT id FROM tenant.mail_message "
                    "WHERE tenant_id=:t AND user_id=:u AND ews_item_id=:e"),
                    {"t": tenant_id, "u": uid, "e": iid}).fetchone()
                if ex is None:
                    doc_ids = None
                    if with_attachments and hasatt:
                        doc_ids = _save_attachments(m, uid, tenant_id)
                    s.execute(text(
                        "INSERT INTO tenant.mail_message (tenant_id,user_id,slozka,ews_item_id,ews_changekey,"
                        "datum,od_email,od_jmeno,komu,kopie,predmet,telo_text,ma_prilohy,prilohy_doc_ids,neprectene,stav) "
                        "VALUES (:t,:u,:s,:e,:ck,:d,:oe,:oj,:k,:cc,:su,:tb,:ha,CAST(:pd AS jsonb),:un,'nove')"),
                        {"t": tenant_id, "u": uid, "s": slozka, "e": iid, "ck": ck, "d": dt,
                         "oe": od_email, "oj": od_jmeno, "k": komu, "cc": kopie, "su": subj,
                         "tb": telo, "ha": hasatt, "pd": (json.dumps(doc_ids) if doc_ids else None),
                         "un": unread})
                    nnew += 1
                else:
                    s.execute(text("UPDATE tenant.mail_message SET ews_changekey=:ck, neprectene=:un, "
                                   "synced_at=now() WHERE id=:i"), {"ck": ck, "un": unread, "i": ex[0]})
                n += 1
                if n % 40 == 0:
                    s.commit()
            except Exception as e:
                logger.warning("[mail] zprava selhala: %s", str(e)[:150])
        s.commit()
    finally:
        s.close()
    logger.info("[mail] sync uid=%s slozka=%s zpracovano=%s nove=%s", uid, slozka, n, nnew)
    return {"slozka": slozka, "zpracovano": n, "nove": nnew}


def sync_user(uid: int, limit: int = 300, with_attachments: bool = True, tenant_id: int = 2) -> dict:
    acct = _account_for_user(uid)
    out = []
    for slozka in _SLOZKY:
        try:
            out.append(sync_folder(uid, slozka, limit=limit,
                                   with_attachments=with_attachments, tenant_id=tenant_id, acct=acct))
        except Exception as e:
            out.append({"slozka": slozka, "error": str(e)[:200]})
    return {"user_id": uid, "vysledky": out}


def sync_user_bg(uid: int, limit: int = 300, with_attachments: bool = True, tenant_id: int = 2):
    """Spustí sync na pozadí (kvůli 30s timeoutu mostu)."""
    threading.Thread(target=lambda: sync_user(uid, limit=limit,
                     with_attachments=with_attachments, tenant_id=tenant_id), daemon=True).start()
