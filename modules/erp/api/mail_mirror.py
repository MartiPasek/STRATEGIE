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
                with_attachments: bool = True, tenant_id: int = 2, acct=None,
                since=None) -> dict:
    if acct is None:
        acct = _account_for_user(uid)
    fld = _folder(acct, slozka)
    # Backfill (Claude-27 7.7.2026): dolní hranice data → stáhne celý rok, ne jen
    # posledních `limit`. since = "YYYY-MM-DD"; přebíjí inkrementální logiku níže.
    _since_dt = None
    if since:
        try:
            import datetime as _dtm
            from exchangelib import EWSDateTime, UTC
            _d = _dtm.date.fromisoformat(str(since)[:10])
            _since_dt = EWSDateTime(_d.year, _d.month, _d.day, 0, 0, 0, tzinfo=UTC)
        except Exception:
            _since_dt = None
    # Inkrement (Marti 5.7.2026): fetchuj jen zprávy NOVĚJŠÍ než poslední synced —
    # jinak se pokaždé tahá top 300 s plnými těly (pomalé/hang, zaseklo Eliščin sync).
    # Po prvním sync jsou to jednotky → doběhne v sekundách.
    _last = None
    try:
        _s0 = get_data_session()
        try:
            _last = _s0.execute(text(
                "SELECT max(datum) FROM tenant.mail_message "
                "WHERE tenant_id=:t AND user_id=:u AND slozka=:s"),
                {"t": tenant_id, "u": uid, "s": slozka}).scalar()
        finally:
            _s0.close()
    except Exception:
        _last = None
    # TZ-fix (Claude C23 18.7.2026): _last z PG nes pražský offset UTC+02:00, ktery
    # exchangelib neumi namapovat na Windows tz ("No time zone found with key UTC+02:00")
    # -> fetch padal od 7.7. Znormalizuj na UTC EWSDateTime (jako funkcni backfill vetev).
    _last_ews = None
    if _last is not None:
        try:
            import datetime as _dtz
            from exchangelib import EWSDateTime as _EDT, UTC as _EUTC
            _lu = (_last.astimezone(_dtz.timezone.utc) if getattr(_last, "tzinfo", None)
                   else _last.replace(tzinfo=_dtz.timezone.utc))
            _last_ews = _EDT(_lu.year, _lu.month, _lu.day, _lu.hour, _lu.minute,
                             _lu.second, tzinfo=_EUTC)
        except Exception:
            _last_ews = None
    try:
        if _since_dt is not None:
            qs = fld.filter(datetime_received__gte=_since_dt).order_by("-datetime_received")[:limit]
        elif _last_ews is not None:
            qs = fld.filter(datetime_received__gt=_last_ews).order_by("-datetime_received")[:limit]
        elif _last is not None:
            qs = fld.filter(datetime_received__gt=_last).order_by("-datetime_received")[:limit]
        else:
            qs = fld.all().order_by("-datetime_received")[:limit]
    except Exception:
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
                # HTML tělo (pro standardní render v detailu jako Outlook)
                telo_html = None
                try:
                    _b = getattr(m, "body", None)
                    if _b is not None and str(getattr(_b, "body_type", "") or "").upper() == "HTML":
                        telo_html = str(_b).replace("\x00", "")[:400000]
                except Exception:
                    telo_html = None
                hasatt = bool(getattr(m, "has_attachments", False))
                unread = (getattr(m, "is_read", True) is False)
                ex = s.execute(text(
                    "SELECT id, prilohy_doc_ids FROM tenant.mail_message "
                    "WHERE tenant_id=:t AND user_id=:u AND ews_item_id=:e"),
                    {"t": tenant_id, "u": uid, "e": iid}).fetchone()
                if ex is None:
                    doc_ids = None
                    if with_attachments and hasatt:
                        doc_ids = _save_attachments(m, uid, tenant_id)
                    s.execute(text(
                        "INSERT INTO tenant.mail_message (tenant_id,user_id,slozka,ews_item_id,ews_changekey,"
                        "datum,od_email,od_jmeno,komu,kopie,predmet,telo_text,telo_html,ma_prilohy,prilohy_doc_ids,neprectene,stav) "
                        "VALUES (:t,:u,:s,:e,:ck,:d,:oe,:oj,:k,:cc,:su,:tb,:th,:ha,CAST(:pd AS jsonb),:un,'nove')"),
                        {"t": tenant_id, "u": uid, "s": slozka, "e": iid, "ck": ck, "d": dt,
                         "oe": od_email, "oj": od_jmeno, "k": komu, "cc": kopie, "su": subj,
                         "tb": telo, "th": telo_html, "ha": hasatt,
                         "pd": (json.dumps(doc_ids) if doc_ids else None), "un": unread})
                    nnew += 1
                else:
                    # backfill příloh: existující zpráva má přílohu, ale ještě nestaženou
                    if with_attachments and hasatt and not ex[1]:
                        _bdoc = _save_attachments(m, uid, tenant_id)
                        if _bdoc:
                            s.execute(text("UPDATE tenant.mail_message SET prilohy_doc_ids=CAST(:pd AS jsonb) "
                                           "WHERE id=:i"), {"pd": json.dumps(_bdoc), "i": ex[0]})
                    if telo_html is not None:
                        s.execute(text("UPDATE tenant.mail_message SET telo_html=:th "
                                       "WHERE id=:i AND telo_html IS NULL"), {"th": telo_html, "i": ex[0]})
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


def sync_user(uid: int, limit: int = 300, with_attachments: bool = True, tenant_id: int = 2,
              since=None) -> dict:
    acct = _account_for_user(uid)
    out = []
    for slozka in _SLOZKY:
        try:
            out.append(sync_folder(uid, slozka, limit=limit,
                                   with_attachments=with_attachments, tenant_id=tenant_id,
                                   acct=acct, since=since))
        except Exception as e:
            out.append({"slozka": slozka, "error": str(e)[:200]})
    return {"user_id": uid, "vysledky": out}


def sync_user_job(uid: int, limit: int = 100, tenant_id: int = 2) -> dict:
    """Adapter pro mirror_job: sloz vysledky sync_user do (ok/rows/_msg), aby
    planovac VIDEL chybu EWS a pocet NOVYCH zprav (ne user_id). Bez tohoto
    _mirror_run_job bral ok=True vzdy a rows=user_id -> zeleny job i pri padu
    fetchu. Claude C23 18.7.2026 (bod 2: job musi rikat pravdu)."""
    r = sync_user(uid, limit=limit, tenant_id=tenant_id)
    vys = r.get("vysledky") or []
    errs = [v for v in vys if v.get("error")]
    nove = sum(int(v.get("nove") or 0) for v in vys)
    zprac = sum(int(v.get("zpracovano") or 0) for v in vys)
    if errs:
        _m = "EWS CHYBA -> " + "; ".join(
            "%s: %s" % (v.get("slozka"), v.get("error")) for v in errs)
    else:
        _m = ", ".join(
            "%s nove=%s/zprac=%s" % (v.get("slozka"), v.get("nove"), v.get("zpracovano"))
            for v in vys)
    return {"ok": (not errs), "done": True, "nove": nove,
            "zpracovano": zprac, "_msg": _m[:580]}


def sync_user_bg(uid: int, limit: int = 300, with_attachments: bool = True, tenant_id: int = 2,
                 since=None):
    """Spustí sync na pozadí (kvůli 30s timeoutu mostu)."""
    threading.Thread(target=lambda: sync_user(uid, limit=limit,
                     with_attachments=with_attachments, tenant_id=tenant_id, since=since),
                     daemon=True).start()


def backfill_att(uid, tenant_id=2, max_items=3000):
    """Cilena dobirka priloh (Claude C23 21.7.2026): vytahne z EWS JEN zpravy,
    ktere maji prilohu, ale nemaji stazene dokumenty (prilohy_doc_ids prazdne).
    Fetch po jedne podle ews_item_id -> _save_attachments -> UPDATE. Nezatezuje se
    nacitanim tel vsech zprav (na rozdil od sync_folder newest-first). Resumovatelne
    -- bere jen stale chybejici, takze re-run pokracuje. Resi bod 1 (historicke prilohy)."""
    acct = _account_for_user(uid)
    s0 = get_data_session()
    try:
        rows = s0.execute(text(
            "SELECT id, ews_item_id, slozka FROM tenant.mail_message "
            "WHERE tenant_id=:t AND user_id=:u AND ma_prilohy=true "
            "AND (prilohy_doc_ids IS NULL OR btrim(prilohy_doc_ids::text) IN ('','[]','null')) "
            "AND ews_item_id IS NOT NULL "
            "ORDER BY datum DESC LIMIT :lim"),
            {"t": tenant_id, "u": uid, "lim": max_items}).fetchall()
    finally:
        s0.close()
    total = len(rows)
    logger.info("[mail-att] uid=%s dobirka startuje, chybi=%s", uid, total)
    ok = 0
    fail = 0
    _fld_cache = {}
    s = get_data_session()
    try:
        for i, r in enumerate(rows, 1):
            mid, iid, slozka = r[0], r[1], r[2]
            try:
                fld = _fld_cache.get(slozka)
                if fld is None:
                    fld = _folder(acct, slozka)
                    _fld_cache[slozka] = fld
                m = fld.get(id=str(iid))
                doc = _save_attachments(m, uid, tenant_id)
                if doc:
                    s.execute(text(
                        "UPDATE tenant.mail_message SET prilohy_doc_ids=CAST(:pd AS jsonb), "
                        "synced_at=now() WHERE id=:i"),
                        {"pd": json.dumps(doc), "i": mid})
                    s.commit()
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                logger.warning("[mail-att] zprava id=%s selhala: %s", mid, str(e)[:150])
            if i % 25 == 0:
                logger.info("[mail-att] uid=%s postup %s/%s ok=%s fail=%s", uid, i, total, ok, fail)
        s.commit()
    finally:
        s.close()
    logger.info("[mail-att] uid=%s HOTOVO ok=%s fail=%s z %s", uid, ok, fail, total)
    return {"uid": uid, "chybelo": total, "doplneno": ok, "selhalo": fail}


def backfill_att_bg(uid, tenant_id=2, max_items=3000):
    """Spusti dobirku priloh na pozadi (kvuli 30s timeoutu mostu)."""
    threading.Thread(target=lambda: backfill_att(uid, tenant_id=tenant_id, max_items=max_items),
                     daemon=True).start()


# ─── FW strom: soudeček Email + 4 přehledy nad zrcadlem (klon z existujícího přehledu) ───

TEMPLATE_CORE_ID = 139   # 📥 Poptávky (VP) = vzor pro klon fw řetězce
VP_NODE_ID = 119         # 📁 VP — Vedení projektů


def _table_cols(s, table):
    return [r[0] for r in s.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='fw' AND table_name=:t ORDER BY ordinal_position"),
        {"t": table}).fetchall()]


def _clone_row(s, table, src_id, overrides):
    """Naklonuje fw řádek (INSERT ... SELECT, schema-agnostic). overrides pro
    sloupce, které v tabulce neexistují, se ignorují. Vrací nové id."""
    cols = _table_cols(s, table)
    skip = {"id", "created_at", "updated_at"}
    use = [c for c in cols if c not in skip]
    ov = {k: v for k, v in overrides.items() if k in use}
    sel, params = [], {}
    for c in use:
        if c in ov:
            params["v_" + c] = ov[c]
            sel.append(":v_" + c + " AS " + c)
        else:
            sel.append(c)
    return s.execute(text(
        "INSERT INTO fw." + table + " (" + ", ".join(use) + ") SELECT " + ", ".join(sel) +
        " FROM fw." + table + " WHERE id=:sid RETURNING id"),
        {**params, "sid": src_id}).scalar()


def _mail_prehled_sql(uid, where_extra):
    return (
        "SELECT id, "
        "to_char(datum,'DD.MM.YYYY HH24:MI') AS \"Datum\", "
        "od_jmeno AS \"Od\", od_email AS \"E-mail\", "
        "predmet AS \"Předmět\", "
        "CASE WHEN ma_prilohy THEN '📎' ELSE '' END AS \"Příl.\", "
        "left(telo_text, 300) AS \"Náhled\", "
        "stav AS \"Stav\" "
        "FROM tenant.mail_message WHERE tenant_id=2 AND user_id=%d AND %s "
        "ORDER BY datum DESC NULLS LAST" % (int(uid), where_extra))


def build_mail_tree(uid: int, tenant_id: int = 2, parent_node_id: int = None) -> dict:
    """Postaví (idempotentně) soudeček <jméno> → Email → 4 přehledy pod rodičem.
    parent_node_id = kam soudeček osoby pověsit (default VP=119; CRM=56 pro obchodníky).
    Přehledy = klon fw řetězce z TEMPLATE_CORE_ID, sql nad tenant.mail_message.
    visibility_scope=NULL (rodiče vidí hned) + visibility_user_ids=[uid]."""
    _parent = int(parent_node_id) if parent_node_id else VP_NODE_ID
    prehledy = [
        ("dorucene", "📥 Doručené", "slozka='dorucene' AND stav='nove'", 10),
        ("zpracovane", "✅ Zpracované", "slozka='dorucene' AND stav='zpracovane'", 20),
        ("odeslane", "📤 Odeslané", "slozka='odeslane'", 30),
        ("koncepty", "📝 Koncepty", "slozka='koncepty'", 40),
    ]
    s = get_data_session()
    created = []
    try:
        # jméno uživatele pro label soudečku
        nm = s.execute(text("SELECT COALESCE(first_name||' '||last_name, 'Uživatel '||id) "
                            "FROM public.users WHERE id=:i"), {"i": uid}).scalar() or ("Uživatel %s" % uid)

        # 1) soudeček osoby pod rodičem (VP default / CRM 56)
        person_label = "👤 " + nm
        pid = s.execute(text("SELECT id FROM fw.menu_node WHERE parent_id=:p AND label=:l"),
                        {"p": _parent, "l": person_label}).scalar()
        if not pid:
            pid = s.execute(text(
                "INSERT INTO fw.menu_node (label,parent_id,sort_order,status,visibility_scope,"
                "visibility_user_ids,created_by_text,updated_by_text) "
                "VALUES (:l,:p,:so,'active',NULL,:vu,'claude-27','claude-27') RETURNING id"),
                {"l": person_label, "p": _parent, "so": 500 + uid, "vu": [uid]}).scalar()
            created.append("soudecek %s" % person_label)

        # 2) soudeček Email pod osobou
        eid = s.execute(text("SELECT id FROM fw.menu_node WHERE parent_id=:p AND label=:l"),
                        {"p": pid, "l": "✉️ Email"}).scalar()
        if not eid:
            eid = s.execute(text(
                "INSERT INTO fw.menu_node (label,parent_id,sort_order,status,visibility_scope,"
                "visibility_user_ids,created_by_text,updated_by_text) "
                "VALUES ('✉️ Email',:p,10,'active',NULL,:vu,'claude-23','claude-23') RETURNING id"),
                {"p": pid, "vu": [uid]}).scalar()
            created.append("soudecek Email")

        # 3) template řetězec
        tcode = s.execute(text("SELECT code FROM fw.core WHERE id=:i"), {"i": TEMPLATE_CORE_ID}).scalar()
        t_ds = s.execute(text("SELECT id FROM fw.data_source WHERE code=:c ORDER BY id LIMIT 1"),
                         {"c": tcode}).fetchone()
        if not t_ds:
            return {"ok": False, "error": "template data_source pro core %s nenalezen" % TEMPLATE_CORE_ID}
        t_ds_id = t_ds[0]
        t_ops = s.execute(text("SELECT id, data_set_id, operation_kind FROM fw.data_source_op "
                               "WHERE data_source_id=:d"), {"d": t_ds_id}).fetchall()
        t_sel_op = next((o for o in t_ops if o[2] == 'select'), (t_ops[0] if t_ops else None))
        t_cd = s.execute(text("SELECT id FROM fw.comp_def WHERE core_id=:c ORDER BY id LIMIT 1"),
                         {"c": TEMPLATE_CORE_ID}).fetchone()

        for key, label, where_extra, so in prehledy:
            code = "mail_%s_%d" % (key, uid)
            # už existuje?
            if s.execute(text("SELECT 1 FROM fw.core WHERE code=:c"), {"c": code}).fetchone():
                continue
            new_sql = _mail_prehled_sql(uid, where_extra)
            # data_set (klon select data_setu template + náš sql)
            new_dset = _clone_row(s, "data_set", t_sel_op[1],
                                  {"code": code, "sql_text": new_sql, "description": label})
            # data_source
            new_ds = _clone_row(s, "data_source", t_ds_id, {"code": code, "name": label})
            # data_source_op (klon select op → nové ds + dset)
            _clone_row(s, "data_source_op", t_sel_op[0],
                       {"data_source_id": new_ds, "data_set_id": new_dset})
            # core
            new_core = _clone_row(s, "core", TEMPLATE_CORE_ID, {"code": code, "label": label})
            # comp_def (root grid → nové core + data_source)
            if t_cd:
                _clone_row(s, "comp_def", t_cd[0], {"core_id": new_core, "data_source_id": new_ds})
            # menu_node pod Email
            s.execute(text(
                "INSERT INTO fw.menu_node (label,parent_id,sort_order,status,visibility_scope,"
                "visibility_user_ids,core_id,created_by_text,updated_by_text) "
                "VALUES (:l,:p,:so,'active',NULL,:vu,:c,'claude-23','claude-23')"),
                {"l": label, "p": eid, "so": so, "vu": [uid], "c": new_core})
            created.append(label)
        s.commit()
    finally:
        s.close()
    return {"ok": True, "user_id": uid, "vytvoreno": created,
            "person_node": pid, "email_node": eid}
