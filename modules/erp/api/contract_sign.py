"""Elektronické podepisování smluv (Marti 1.7.2026) — bilaterální SES + silný audit.

Cíl: smlouvy (např. s certifikační firmou) podepsat elektronicky bez tisku/scanu.
Naše strana podepíše klikem (SES), protistraně pošleme bezpečný odkaz na tokenový
portál (bez loginu), kde si smlouvu prohlédne a podepíše. Po obou podpisech se
sestaví finální PDF s podpisovou doložkou (jména/časy/IP/hash dokumentu) a rozešle
se oběma stranám. Právně: pro běžné B2B smlouvy je SES + auditní stopa dostačující
(eIDAS / obč. zákoník). Reuse vzorů z iso_cockpit (tokenový portál, servírování).

Tabulky: tenant.contract_sign / contract_sign_party / contract_sign_log.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import text as _t

contract_router = APIRouter(prefix="/api/v1/erp", tags=["contract-sign"])

_DOC_STORE_ROOT = os.environ.get("STRATEGIE_DOC_STORE") or r"D:\Data\STRATEGIE\Dokumenty"
_CONTRACT_DIR = os.path.join(_DOC_STORE_ROOT, "contracts")
_DEFAULT_TENANT = 2  # EUROSOFT-Control (hlavní firma)


# ── helpers (lazy import z router.py, ať není cirkulární) ──
def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _can(uid, s):
    """Kdo smí spravovat podpisy smluv = finanční/HR okruh (rodiče + Petra/Šárka +
    skupiny Finance/HR + účetní firma). Reuse _is_cockpit z router.py."""
    if not uid:
        return False
    try:
        from modules.erp.api.router import _is_cockpit
        return _is_cockpit(s, uid)
    except Exception:
        return False


def _user_name(s, uid):
    try:
        r = s.execute(_t("SELECT COALESCE(first_name,'')||' '||COALESCE(last_name,'') j FROM public.users WHERE id=:i"),
                      {"i": uid}).first()
        return (r.j.strip() if r and r.j else ("user %s" % uid))
    except Exception:
        return "user %s" % uid


def _tenant(req, uid, s):
    q = req.query_params.get("tenant")
    if q:
        try:
            return int(q)
        except Exception:
            pass
    try:
        r = s.execute(_t("SELECT last_active_tenant_id FROM public.users WHERE id=:i"), {"i": uid}).first()
        if r and r.last_active_tenant_id:
            return int(r.last_active_tenant_id)
    except Exception:
        pass
    return _DEFAULT_TENANT


def _client_ip(req):
    return (req.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (req.client.host if req.client else "") or "")


def _log(s, tid, cid, akce, kdo, ip, device="", detail=""):
    try:
        s.execute(_t("""INSERT INTO tenant.contract_sign_log(tenant_id,contract_id,akce,kdo,ip,device,detail)
            VALUES(:t,:c,:a,:k,:ip,:d,:det)"""),
            {"t": tid, "c": cid, "a": akce, "k": kdo, "ip": ip, "d": device[:300], "det": detail[:500]})
    except Exception:
        pass


def _serve_pdf(path, download_name="smlouva.pdf"):
    if not path:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    full = os.path.normpath(path)
    root = os.path.normpath(_CONTRACT_DIR)
    if not full.startswith(root) or not os.path.isfile(full):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return FileResponse(full, media_type="application/pdf",
                        headers={"Content-Disposition": 'inline; filename="%s"' % download_name})


def _envelope(s, tid, cid):
    return s.execute(_t("""SELECT id,title,stav,our_party,counterparty_name,counterparty_email,note,
        doc_sha256,soubor_path,final_path,created_at,completed_at FROM tenant.contract_sign
        WHERE tenant_id=:t AND id=:c"""), {"t": tid, "c": cid}).mappings().first()


def _parties(s, cid):
    return s.execute(_t("""SELECT id,role,jmeno,email,signed,podpis_text,signed_at,signed_ip,poradi
        FROM tenant.contract_sign_party WHERE contract_id=:c ORDER BY poradi,id"""), {"c": cid}).mappings().all()


def _party_dicts(rows):
    out = []
    for r in rows:
        out.append({"id": r["id"], "role": r["role"], "jmeno": r["jmeno"], "email": r["email"],
                    "signed": bool(r["signed"]), "podpis_text": r["podpis_text"],
                    "signed_at": r["signed_at"].isoformat() if r["signed_at"] else None})
    return out


# ═══════════════ INTERNÍ (přihlášení, finanční/HR okruh) ═══════════════

@contract_router.post("/app/sign/create")
async def sign_create(req: Request):
    """Vytvoří obálku k podpisu: nahraje PDF (base64), spočítá sha256, založí
    interního signatáře (aktuální uživatel) + protistranu (jméno+email, nepodepsáno)."""
    uid = _uid(req)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        title = (b.get("title") or "").strip()[:300] or "Smlouva"
        cp_name = (b.get("counterparty_name") or "").strip()[:200]
        cp_email = (b.get("counterparty_email") or "").strip()[:200]
        note = (b.get("note") or "").strip()[:1000] or None
        our = (b.get("our_party") or "EUROSOFT-Control s.r.o.").strip()[:200]
        pdf_b64 = b.get("pdf_b64") or ""
        if "," in pdf_b64[:80] and ";base64" in pdf_b64[:80]:
            pdf_b64 = pdf_b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(pdf_b64)
        except Exception:
            raw = b""
        if not raw or raw[:4] != b"%PDF":
            return JSONResponse({"ok": False, "error": "Nahraj prosím PDF soubor smlouvy."})
        if not cp_name or "@" not in cp_email:
            return JSONResponse({"ok": False, "error": "Vyplň jméno a e-mail protistrany."})
        sha = hashlib.sha256(raw).hexdigest()
        row = s.execute(_t("""INSERT INTO tenant.contract_sign(tenant_id,title,doc_sha256,our_party,
            counterparty_name,counterparty_email,note,stav,created_by)
            VALUES(:t,:ti,:sha,:our,:cn,:ce,:no,'draft',:by) RETURNING id"""),
            {"t": tid, "ti": title, "sha": sha, "our": our, "cn": cp_name, "ce": cp_email, "no": note, "by": uid}).first()
        cid = int(row[0])
        os.makedirs(os.path.join(_CONTRACT_DIR, str(tid)), exist_ok=True)
        path = os.path.join(_CONTRACT_DIR, str(tid), "%d_orig.pdf" % cid)
        with open(path, "wb") as f:
            f.write(raw)
        s.execute(_t("UPDATE tenant.contract_sign SET soubor_path=:p WHERE id=:c"), {"p": path, "c": cid})
        # signatáři: interní (my) + protistrana
        s.execute(_t("""INSERT INTO tenant.contract_sign_party(tenant_id,contract_id,role,jmeno,email,user_id,poradi)
            VALUES(:t,:c,'internal',:j,NULL,:u,1)"""), {"t": tid, "c": cid, "j": _user_name(s, uid), "u": uid})
        s.execute(_t("""INSERT INTO tenant.contract_sign_party(tenant_id,contract_id,role,jmeno,email,poradi)
            VALUES(:t,:c,'counterparty',:j,:e,2)"""), {"t": tid, "c": cid, "j": cp_name, "e": cp_email})
        s.commit()
        _log(s, tid, cid, "created", _user_name(s, uid), _client_ip(req), detail=title)
        s.commit()
        return {"ok": True, "id": cid}
    except Exception as exc:
        import traceback
        try:
            s.rollback()
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": "DEBUG: " + repr(exc)[:400],
                             "tb": traceback.format_exc()[-800:]}, status_code=500)
    finally:
        s.close()


@contract_router.get("/app/sign/list")
def sign_list(req: Request):
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        rows = s.execute(_t("""SELECT id,title,stav,counterparty_name,counterparty_email,
            to_char(created_at,'DD.MM.YYYY HH24:MI') created FROM tenant.contract_sign
            WHERE tenant_id=:t ORDER BY id DESC LIMIT 200"""), {"t": tid}).mappings().all()
        return {"ok": True, "items": [dict(r) for r in rows]}
    finally:
        s.close()


@contract_router.get("/app/sign/{cid}")
def sign_detail(cid: int, req: Request):
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        e = _envelope(s, tid, cid)
        if not e:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        logs = s.execute(_t("""SELECT akce,kdo,ip,to_char(at,'DD.MM.YYYY HH24:MI:SS') at FROM tenant.contract_sign_log
            WHERE contract_id=:c ORDER BY id"""), {"c": cid}).mappings().all()
        d = dict(e)
        d["created_at"] = e["created_at"].isoformat() if e["created_at"] else None
        d["completed_at"] = e["completed_at"].isoformat() if e["completed_at"] else None
        return {"ok": True, "envelope": d, "parties": _party_dicts(_parties(s, cid)),
                "log": [dict(l) for l in logs], "has_final": bool(e["final_path"])}
    finally:
        s.close()


@contract_router.get("/app/sign/{cid}/pdf")
def sign_pdf(cid: int, req: Request):
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        e = _envelope(s, tid, cid)
        if not e:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        return _serve_pdf(e["final_path"] or e["soubor_path"], (e["title"] or "smlouva") + ".pdf")
    finally:
        s.close()


@contract_router.post("/app/sign/{cid}/our-sign")
async def sign_our(cid: int, req: Request):
    """Náš (interní) SES podpis klikem — audit kdo/kdy/IP/zařízení."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        e = _envelope(s, tid, cid)
        if not e:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        jmeno = _user_name(s, uid)
        ip = _client_ip(req)
        zar = (req.headers.get("user-agent") or "")[:300]
        pt = "Elektronicky podepsal %s dne %s (SES)" % (jmeno, datetime.now().strftime("%d.%m.%Y %H:%M"))
        s.execute(_t("""UPDATE tenant.contract_sign_party SET signed=true,podpis_text=:pt,signed_at=now(),
            signed_ip=:ip,signed_device=:z,jmeno=:j WHERE contract_id=:c AND role='internal'"""),
            {"pt": pt, "ip": ip, "z": zar, "j": jmeno, "c": cid})
        s.commit()
        _log(s, tid, cid, "our_signed", jmeno, ip, zar)
        _maybe_finalize(s, tid, cid)
        s.commit()
        return {"ok": True, "podpis": pt}
    finally:
        s.close()


@contract_router.post("/app/sign/{cid}/send")
async def sign_send(cid: int, req: Request):
    """Vygeneruje token pro protistranu a pošle e-mail s odkazem na podpisový portál."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        e = _envelope(s, tid, cid)
        if not e:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        tok = secrets.token_urlsafe(24)
        th = hashlib.sha256(tok.encode()).hexdigest()
        s.execute(_t("""UPDATE tenant.contract_sign_party SET token_hash=:th WHERE contract_id=:c AND role='counterparty'"""),
                  {"th": th, "c": cid})
        s.execute(_t("UPDATE tenant.contract_sign SET stav='sent',updated_at=now() WHERE id=:c AND stav IN ('draft')"),
                  {"c": cid})
        s.commit()
        odkaz = "https://strategie-ai.com/podpis/%s" % tok
        body = ("Dobrý den,\n\nspolečnost %s Vám zasílá k elektronickému podpisu dokument: %s.\n\n"
                "Podepsat můžete online zde (bez registrace, stačí kliknout):\n%s\n\n"
                "Po podpisu Vám i nám přijde finální podepsané PDF s auditní stopou. "
                "Tisk ani sken není potřeba.\n\nS pozdravem\n%s") % (
                    e["our_party"] or "EUROSOFT-Control s.r.o.", e["title"], odkaz, e["our_party"] or "EUROSOFT-Control s.r.o.")
        sent = False
        try:
            from modules.notifications.application.email_service import queue_email
            queue_email(to=e["counterparty_email"], subject="K elektronickému podpisu: %s" % e["title"],
                        body=body, persona_id=1, from_identity="persona", tenant_id=tid, purpose="contract_sign")
            sent = True
        except Exception as exc:
            _log(s, tid, cid, "send_error", _user_name(s, uid), _client_ip(req), detail=str(exc)[:400])
            s.commit()
        _log(s, tid, cid, "sent", _user_name(s, uid), _client_ip(req), detail=e["counterparty_email"])
        s.commit()
        return {"ok": True, "sent": sent, "odkaz": odkaz}
    finally:
        s.close()


# ═══════════════ EXTERNÍ PORTÁL (bez loginu, jen platný token) ═══════════════

def _by_token(s, token):
    if not token:
        return None
    th = hashlib.sha256(token.encode()).hexdigest()
    return s.execute(_t("""SELECT p.id party_id, p.contract_id, p.jmeno, p.email, p.signed,
        c.tenant_id, c.title, c.our_party, c.stav, c.soubor_path, c.final_path
        FROM tenant.contract_sign_party p JOIN tenant.contract_sign c ON c.id=p.contract_id
        WHERE p.token_hash=:th AND p.role='counterparty' LIMIT 1"""), {"th": th}).mappings().first()


@contract_router.get("/app/sign/portal/{token}/data")
def portal_data(token: str, req: Request):
    s = _sess()
    try:
        r = _by_token(s, token)
        if not r:
            return JSONResponse({"ok": False, "error": "neplatný odkaz"}, status_code=404)
        _log(s, r["tenant_id"], r["contract_id"], "viewed", r["jmeno"], _client_ip(req),
             (req.headers.get("user-agent") or "")[:300])
        s.commit()
        return {"ok": True, "title": r["title"], "our_party": r["our_party"], "jmeno": r["jmeno"],
                "signed": bool(r["signed"]), "stav": r["stav"], "has_final": bool(r["final_path"])}
    finally:
        s.close()


@contract_router.get("/app/sign/portal/{token}/pdf")
def portal_pdf(token: str, req: Request):
    s = _sess()
    try:
        r = _by_token(s, token)
        if not r:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        return _serve_pdf(r["final_path"] or r["soubor_path"], (r["title"] or "smlouva") + ".pdf")
    finally:
        s.close()


@contract_router.post("/app/sign/portal/{token}/sign")
async def portal_sign(token: str, req: Request):
    """Externí SES podpis protistranou — jméno + souhlas s elektronickým podpisem, audit IP/UA."""
    b = await req.json()
    s = _sess()
    try:
        r = _by_token(s, token)
        if not r:
            return JSONResponse({"ok": False, "error": "neplatný odkaz"}, status_code=404)
        if r["signed"]:
            return {"ok": True, "already": True}
        jmeno = (b.get("jmeno") or "").strip()[:200] or r["jmeno"]
        if not b.get("souhlas"):
            return JSONResponse({"ok": False, "error": "Potvrď prosím souhlas s elektronickým podpisem."})
        ip = _client_ip(req)
        zar = (req.headers.get("user-agent") or "")[:300]
        pt = "Elektronicky podepsal %s dne %s (SES)" % (jmeno, datetime.now().strftime("%d.%m.%Y %H:%M"))
        s.execute(_t("""UPDATE tenant.contract_sign_party SET signed=true,podpis_text=:pt,signed_at=now(),
            signed_ip=:ip,signed_device=:z,jmeno=:j WHERE id=:pid"""),
            {"pt": pt, "ip": ip, "z": zar, "j": jmeno, "pid": r["party_id"]})
        s.commit()
        _log(s, r["tenant_id"], r["contract_id"], "signed", jmeno, ip, zar)
        _maybe_finalize(s, r["tenant_id"], r["contract_id"])
        s.commit()
        return {"ok": True, "podpis": pt}
    finally:
        s.close()


# ═══════════════ FINALIZACE (obě strany podepsaly → PDF s doložkou + e-mail) ═══════════════

def _maybe_finalize(s, tid, cid):
    parties = _parties(s, cid)
    if not parties or any(not p["signed"] for p in parties):
        # aktualizuj stav na partially_signed pokud aspoň jeden podepsal
        if any(p["signed"] for p in parties):
            s.execute(_t("UPDATE tenant.contract_sign SET stav='partially_signed',updated_at=now() "
                         "WHERE id=:c AND stav<>'completed'"), {"c": cid})
        return
    e = _envelope(s, tid, cid)
    if not e or e["stav"] == "completed":
        return
    final_path = os.path.join(_CONTRACT_DIR, str(tid), "%d_signed.pdf" % cid)
    ok = _build_final_pdf(e["soubor_path"], final_path, e, parties)
    if not ok:
        final_path = e["soubor_path"]  # fallback: originál (doložka se nepovedla)
    s.execute(_t("UPDATE tenant.contract_sign SET stav='completed',final_path=:f,completed_at=now(),updated_at=now() "
                 "WHERE id=:c"), {"f": final_path, "c": cid})
    s.commit()
    _log(s, tid, cid, "completed", "systém", "", e["title"] or "")
    s.commit()
    # rozeslat oběma stranám (interní e-mail + protistrana)
    try:
        from modules.notifications.application.email_service import queue_email
        emails = []
        cp = [p for p in parties if p["role"] == "counterparty"]
        if cp and cp[0]["email"]:
            emails.append(cp[0]["email"])
        # interní kopie na tvůrce/rodiče: pošli na e-mail našeho signatáře, pokud známe
        our_uid = s.execute(_t("SELECT user_id FROM tenant.contract_sign_party WHERE contract_id=:c AND role='internal'"),
                            {"c": cid}).scalar()
        if our_uid:
            oem = s.execute(_t("""SELECT contact_value FROM public.user_contacts WHERE user_id=:u
                AND contact_type='email' AND status='active' ORDER BY is_primary DESC, id LIMIT 1"""),
                {"u": our_uid}).scalar()
            if oem:
                emails.append(oem)
        body = ("Dobrý den,\n\nsmlouva %s byla elektronicky podepsána oběma stranami. "
                "V příloze najdete finální podepsané PDF s podpisovou doložkou a auditní stopou.\n\n"
                "S pozdravem\n%s") % (e["title"], e["our_party"] or "EUROSOFT-Control s.r.o.")
        doc_id = _store_final_as_document(s, tid, cid, e, final_path)
        for em in set(emails):
            try:
                queue_email(to=em, subject="Podepsáno: %s" % e["title"], body=body,
                            persona_id=1, from_identity="persona", tenant_id=tid, purpose="contract_signed",
                            attachment_document_ids=[doc_id] if doc_id else None)
            except Exception:
                pass
    except Exception:
        pass


def _store_final_as_document(s, tid, cid, e, final_path):
    """Uloží finální PDF do public.documents (pro přílohu e-mailu). Vrací doc_id nebo None."""
    try:
        if not final_path or not os.path.isfile(final_path):
            return None
        r = s.execute(_t("""INSERT INTO public.documents(tenant_id,name,file_type,storage_path,created_at)
            VALUES(:t,:n,'pdf',:p,now()) RETURNING id"""),
            {"t": tid, "n": "Podepsáno/" + (e["title"] or "smlouva") + ".pdf", "p": final_path}).first()
        s.commit()
        return int(r[0]) if r else None
    except Exception:
        s.rollback()
        return None


def _build_final_pdf(orig_path, out_path, e, parties):
    """Sestaví finální PDF: originál + podpisová doložka (strana s údaji o podpisech + hash)."""
    try:
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader, PdfWriter
    except Exception:
        return False
    try:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        y = H - 30 * mm
        c.setFont("Helvetica-Bold", 15)
        c.drawString(25 * mm, y, "Podpisová doložka — elektronické podepsání")
        y -= 10 * mm
        c.setFont("Helvetica", 10)
        def line(txt, dy=6.2 * mm, bold=False):
            nonlocal y
            c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
            for chunk in _wrap(txt, 95):
                c.drawString(25 * mm, y, chunk); y -= dy
        line("Dokument: %s" % (e["title"] or ""), bold=True)
        line("SHA-256 dokumentu: %s" % (e["doc_sha256"] or ""))
        line("")
        line("Podpisy (prostý elektronický podpis dle eIDAS, SES):", bold=True)
        for p in parties:
            role = "Za %s" % (e["our_party"] or "nás") if p["role"] == "internal" else "Protistrana"
            sat = p["signed_at"].strftime("%d.%m.%Y %H:%M:%S") if p["signed_at"] else "?"
            line("• %s: %s" % (role, p["jmeno"] or ""))
            line("   podepsáno %s, IP %s" % (sat, p["signed_ip"] or "?"))
            if p["email"]:
                line("   e-mail: %s" % p["email"])
        line("")
        line("Tato doložka je auditní stopou elektronického podpisu. Obě strany vyjádřily")
        line("souhlas s elektronickým podepsáním. Integritu dokumentu ověřuje SHA-256 otisk výše.")
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(25 * mm, 15 * mm, "Vygenerováno systémem STRATEGIE dne %s" % datetime.now().strftime("%d.%m.%Y %H:%M"))
        c.showPage(); c.save()
        buf.seek(0)
        w = PdfWriter()
        for pg in PdfReader(orig_path).pages:
            w.add_page(pg)
        for pg in PdfReader(buf).pages:
            w.add_page(pg)
        with open(out_path, "wb") as f:
            w.write(f)
        return True
    except Exception:
        return False


def _wrap(txt, n):
    txt = str(txt or "")
    out, cur = [], ""
    for word in txt.split(" "):
        if len(cur) + len(word) + 1 > n:
            out.append(cur); cur = word
        else:
            cur = (cur + " " + word).strip()
    out.append(cur)
    return out or [""]
