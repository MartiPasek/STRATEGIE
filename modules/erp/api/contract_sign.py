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


def _pdf_resp(data):
    """PDF z DB (bytea) → HTTP odpověď. X-Frame SAMEORIGIN, ať jde vložit do iframe
    v podpisovém portálu (jinak prohlížeč/Caddy vložení odmítne)."""
    if not data:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    from fastapi.responses import Response
    return Response(content=bytes(data), media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="smlouva.pdf"',
                             "X-Frame-Options": "SAMEORIGIN",
                             "Content-Security-Policy": "frame-ancestors 'self'"})


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
        # Režim 'self' (Marti 2.7.2026): jen náš (interní) SES podpis, protistrana
        # NEpodepisuje — je jen příjemcem hotového podepsaného PDF (uloženo do
        # counterparty_email, ale bez counterparty signatáře → finalizace po našem podpisu).
        mode = (b.get("mode") or "bilateral").strip().lower()
        pdf_b64 = b.get("pdf_b64") or ""
        if "," in pdf_b64[:80] and ";base64" in pdf_b64[:80]:
            pdf_b64 = pdf_b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(pdf_b64)
        except Exception:
            raw = b""
        if not raw or raw[:4] != b"%PDF":
            return JSONResponse({"ok": False, "error": "Nahraj prosím PDF soubor smlouvy."})
        if mode != "self" and (not cp_name or "@" not in cp_email):
            return JSONResponse({"ok": False, "error": "Vyplň jméno a e-mail protistrany."})
        sha = hashlib.sha256(raw).hexdigest()
        row = s.execute(_t("""INSERT INTO tenant.contract_sign(tenant_id,title,doc_sha256,our_party,
            counterparty_name,counterparty_email,note,stav,created_by)
            VALUES(:t,:ti,:sha,:our,:cn,:ce,:no,'draft',:by) RETURNING id"""),
            {"t": tid, "ti": title, "sha": sha, "our": our, "cn": cp_name, "ce": cp_email, "no": note, "by": uid}).first()
        cid = int(row[0])
        # PDF ukládáme přímo do DB (bytea) — nezávislé na disku hostitele, přenositelné.
        s.execute(_t("UPDATE tenant.contract_sign SET pdf_orig=:b WHERE id=:c"),
                  {"b": raw, "c": cid})
        # signatáři: interní (my) + protistrana
        s.execute(_t("""INSERT INTO tenant.contract_sign_party(tenant_id,contract_id,role,jmeno,email,user_id,poradi)
            VALUES(:t,:c,'internal',:j,NULL,:u,1)"""), {"t": tid, "c": cid, "j": _user_name(s, uid), "u": uid})
        # counterparty signatář JEN v bilaterálním režimu; v 'self' je příjemce bez podpisu
        if mode != "self":
            s.execute(_t("""INSERT INTO tenant.contract_sign_party(tenant_id,contract_id,role,jmeno,email,poradi)
                VALUES(:t,:c,'counterparty',:j,:e,2)"""), {"t": tid, "c": cid, "j": cp_name, "e": cp_email})
        s.commit()
        _log(s, tid, cid, "created", _user_name(s, uid), _client_ip(req), detail=title)
        s.commit()
        return {"ok": True, "id": cid}
    except Exception as exc:
        try:
            s.rollback()
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": "Vytvoření se nezdařilo: " + type(exc).__name__}, status_code=500)
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


@contract_router.get("/app/sign/pending-count")
def sign_pending_count(req: Request):
    """Počet dokumentů čekajících na náš (interní) podpis — pro badge v appce."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return {"ok": True, "count": 0}
        n = s.execute(_t("""SELECT count(DISTINCT c.id) FROM tenant.contract_sign c
            JOIN tenant.contract_sign_party p ON p.contract_id=c.id AND p.role='internal'
            WHERE c.tenant_id=:t AND COALESCE(p.signed,false)=false
              AND COALESCE(c.stav,'') NOT IN ('completed','hotovo','podepsano','zruseno')"""),
            {"t": tid}).scalar() or 0
        return {"ok": True, "count": int(n)}
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
        data = s.execute(_t("SELECT COALESCE(pdf_final,pdf_orig) FROM tenant.contract_sign WHERE tenant_id=:t AND id=:c"),
                         {"t": tid, "c": cid}).scalar()
        return _pdf_resp(data)
    finally:
        s.close()


def _sign_pdf_bytes(s, tid, cid):
    return s.execute(_t("SELECT COALESCE(pdf_final,pdf_orig) FROM tenant.contract_sign WHERE tenant_id=:t AND id=:c"),
                     {"t": tid, "c": cid}).scalar()


@contract_router.get("/app/sign/{cid}/pages")
def sign_pages(cid: int, req: Request):
    """Počet stránek PDF — pro obrázkový náhled (webview nevykreslí PDF v iframe)."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        data = _sign_pdf_bytes(s, tid, cid)
        if not data:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        n = 0
        try:
            import fitz as _fz
            _d = _fz.open(stream=bytes(data), filetype="pdf")
            n = int(_d.page_count); _d.close()
        except Exception:
            n = 0
        if not n:
            try:
                import pypdfium2 as _pf
                n = len(_pf.PdfDocument(bytes(data)))
            except Exception:
                n = 1
        return {"ok": True, "pages": max(1, n)}
    finally:
        s.close()


@contract_router.get("/app/sign/{cid}/img/{page}")
def sign_img(cid: int, page: int, req: Request, dpi: int = 140):
    """Stránka PDF vykreslená jako PNG (robustní náhled i v mobilním webview). dpi = ostrost pro zoom."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        data = _sign_pdf_bytes(s, tid, cid)
        if not data:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        p = max(0, int(page))
        _dpi = max(72, min(240, int(dpi or 140)))
        img = None
        # rasterizér 1: PyMuPDF (fitz)
        try:
            import io as _io
            from PIL import Image as _Img
            import fitz as _fz
            _d = _fz.open(stream=bytes(data), filetype="pdf")
            if p < _d.page_count:
                pix = _d[p].get_pixmap(dpi=_dpi)
                img = _Img.open(_io.BytesIO(pix.tobytes("png")))
            _d.close()
        except Exception:
            img = None
        # rasterizér 2 (fallback): pypdfium2 — čistý wheel bez systémových závislostí
        if img is None:
            try:
                import pypdfium2 as _pf
                _pdf = _pf.PdfDocument(bytes(data))
                if p < len(_pdf):
                    img = _pdf[p].render(scale=_dpi / 72.0).to_pil()
            except Exception:
                img = None
        if img is None:
            return JSONResponse({"ok": False, "error": "render_failed"}, status_code=500)
        try:
            import io as _io2
            buf = _io2.BytesIO(); img.save(buf, "PNG")
            from fastapi.responses import Response
            return Response(content=buf.getvalue(), media_type="image/png",
                            headers={"Cache-Control": "private, max-age=120"})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": "encode_failed: " + type(exc).__name__}, status_code=500)
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
                        body=body, persona_id=1, from_identity="persona", tenant_id=tid, purpose="user_request")
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
        data = s.execute(_t("SELECT COALESCE(pdf_final,pdf_orig) FROM tenant.contract_sign WHERE id=:c"),
                         {"c": r["contract_id"]}).scalar()
        return _pdf_resp(data)
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
    orig = s.execute(_t("SELECT pdf_orig FROM tenant.contract_sign WHERE id=:c"), {"c": cid}).scalar()
    _sig_bytes = None
    try:
        _iuid = s.execute(_t("SELECT user_id FROM tenant.contract_sign_party WHERE contract_id=:c AND role='internal'"),
                          {"c": cid}).scalar()
        if _iuid:
            _sb = s.execute(_t("SELECT png_b64 FROM tenant.user_signature WHERE user_id=:u"), {"u": _iuid}).scalar()
            if _sb:
                _sig_bytes = base64.b64decode(_sb)
    except Exception:
        _sig_bytes = None
    final_bytes = _build_final_pdf(bytes(orig) if orig else b"", e, parties, _sig_bytes) if orig else None
    if final_bytes:
        s.execute(_t("UPDATE tenant.contract_sign SET stav='completed',pdf_final=:f,completed_at=now(),updated_at=now() "
                     "WHERE id=:c"), {"f": final_bytes, "c": cid})
    else:
        # fallback: doložka se nepovedla → originál poslouží jako finální (stav completed)
        s.execute(_t("UPDATE tenant.contract_sign SET stav='completed',completed_at=now(),updated_at=now() "
                     "WHERE id=:c"), {"c": cid})
    s.commit()
    _log(s, tid, cid, "completed", "systém", "", e["title"] or "")
    s.commit()
    # notifikace oběma stranám — finální podepsané PDF PŘÍMO V PŘÍLOZE (přes upload_document → doc_id)
    try:
        from modules.notifications.application.email_service import queue_email
        emails = []
        cp = [p for p in parties if p["role"] == "counterparty"]
        if cp and cp[0]["email"]:
            emails.append(cp[0]["email"])
        # self-režim: příjemce podepsaného PDF je v envelope.counterparty_email (bez signatáře)
        if e.get("counterparty_email"):
            emails.append(e["counterparty_email"])
        our_uid = s.execute(_t("SELECT user_id FROM tenant.contract_sign_party WHERE contract_id=:c AND role='internal'"),
                            {"c": cid}).scalar()
        if our_uid:
            oem = s.execute(_t("""SELECT contact_value FROM public.user_contacts WHERE user_id=:u
                AND contact_type='email' AND status='active' ORDER BY is_primary DESC, id LIMIT 1"""),
                {"u": our_uid}).scalar()
            if oem:
                emails.append(oem)
        # finální PDF (s doložkou) → dokument → příloha e-mailu
        doc_id = None
        try:
            if final_bytes:
                from modules.rag.application.service import upload_document
                fn = ("Podepsano_" + (e["title"] or "smlouva"))[:120] + ".pdf"
                doc_id = upload_document(file_bytes=final_bytes, filename=fn, tenant_id=tid,
                                        user_id=(our_uid or 1))
        except Exception:
            doc_id = None
        if doc_id:
            body = ("Dobrý den,\n\ndokument %s byl elektronicky podepsán"
                    "(prostý el. podpis dle eIDAS + auditní stopa). V příloze najdete finální podepsané "
                    "PDF s podpisovou doložkou (jména, časy, IP, otisk dokumentu). Tisk ani sken není potřeba.\n\n"
                    "S pozdravem\n%s") % (e["title"], e["our_party"] or "STRATEGIE-System s.r.o.")
        else:
            body = ("Dobrý den,\n\ndokument %s byl elektronicky podepsán"
                    "(prostý el. podpis dle eIDAS + auditní stopa). Finální podepsané PDF s podpisovou "
                    "doložkou je k dispozici přes odkaz, který jsme Vám k podpisu zaslali.\n\nS pozdravem\n%s") % (
                        e["title"], e["our_party"] or "STRATEGIE-System s.r.o.")
        for em in set(emails):
            try:
                queue_email(to=em, subject="Podepsáno: %s" % e["title"], body=body,
                            persona_id=1, from_identity="persona", tenant_id=tid, purpose="user_request",
                            attachment_document_ids=([doc_id] if doc_id else None))
            except Exception:
                pass
    except Exception:
        pass


@contract_router.post("/app/sign/{cid}/regenerate")
async def sign_regenerate(cid: int, req: Request):
    """Přegeneruj finální PDF hotové smlouvy novým renderem doložky (Marti 10.7.2026):
    doplněný symetrický podpisový blok protistrany + oprava fontu (DejaVu, plná čeština).
    Neposílá znovu odkaz k podpisu, jen přerenderuje pdf_final z uloženého originálu +
    podpisů. ?resend=1 → přepošle aktualizované finální PDF v příloze oběma stranám."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        e = _envelope(s, tid, cid)
        if not e:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        parties = _parties(s, cid)
        orig = s.execute(_t("SELECT pdf_orig FROM tenant.contract_sign WHERE id=:c"), {"c": cid}).scalar()
        if not orig:
            return JSONResponse({"ok": False, "error": "chybí originál PDF"}, status_code=400)
        _sig_bytes = None
        try:
            _iuid = s.execute(_t("SELECT user_id FROM tenant.contract_sign_party WHERE contract_id=:c AND role='internal'"),
                              {"c": cid}).scalar()
            if _iuid:
                _sb = s.execute(_t("SELECT png_b64 FROM tenant.user_signature WHERE user_id=:u"), {"u": _iuid}).scalar()
                if _sb:
                    _sig_bytes = base64.b64decode(_sb)
        except Exception:
            _sig_bytes = None
        final_bytes = _build_final_pdf(bytes(orig), e, parties, _sig_bytes)
        if not final_bytes:
            return JSONResponse({"ok": False, "error": "render doložky selhal"}, status_code=500)
        s.execute(_t("UPDATE tenant.contract_sign SET pdf_final=:f,updated_at=now() WHERE id=:c"),
                  {"f": final_bytes, "c": cid})
        s.commit()
        try:
            _log(s, tid, cid, "regenerated", _user_name(s, uid), _client_ip(req), "",
                 "přegenerování finálního PDF (doložka obou stran)")
            s.commit()
        except Exception:
            pass
        resend = str(req.query_params.get("resend") or "").strip().lower() in ("1", "true", "ano")
        sent = []
        if resend:
            try:
                from modules.notifications.application.email_service import queue_email
                emails = []
                cp = [p for p in parties if p["role"] == "counterparty"]
                if cp and cp[0].get("email"):
                    emails.append(cp[0]["email"])
                if e.get("counterparty_email"):
                    emails.append(e["counterparty_email"])
                our_uid = s.execute(_t("SELECT user_id FROM tenant.contract_sign_party WHERE contract_id=:c AND role='internal'"),
                                    {"c": cid}).scalar()
                if our_uid:
                    oem = s.execute(_t("""SELECT contact_value FROM public.user_contacts WHERE user_id=:u
                        AND contact_type='email' AND status='active' ORDER BY is_primary DESC, id LIMIT 1"""),
                        {"u": our_uid}).scalar()
                    if oem:
                        emails.append(oem)
                doc_id = None
                try:
                    from modules.rag.application.service import upload_document
                    fn = ("Podepsano_" + (e["title"] or "smlouva"))[:120] + ".pdf"
                    doc_id = upload_document(file_bytes=final_bytes, filename=fn, tenant_id=tid, user_id=(our_uid or 1))
                except Exception:
                    doc_id = None
                body = ("Dobrý den,\n\nv příloze zasíláme aktualizované finální podepsané PDF dokumentu %s "
                        "s podpisovou doložkou obou stran (auditní stopa: jména, časy, IP, otisk dokumentu). "
                        "Tisk ani sken není potřeba.\n\nS pozdravem\n%s") % (
                            e["title"], e["our_party"] or "STRATEGIE-System s.r.o.")
                for em in set(emails):
                    try:
                        queue_email(to=em, subject="Podepsáno (aktualizováno): %s" % e["title"], body=body,
                                    persona_id=1, from_identity="persona", tenant_id=tid, purpose="user_request",
                                    attachment_document_ids=([doc_id] if doc_id else None))
                        sent.append(em)
                    except Exception:
                        pass
            except Exception:
                pass
        return {"ok": True, "cid": cid, "velikost": len(final_bytes), "resend": resend, "odeslano": sent}
    finally:
        s.close()


def _build_final_pdf(orig_bytes, e, parties, sig_png_bytes=None):
    """Sestaví finální PDF (bytes): originál + podpisová doložka (+ obrázek podpisu). Vrací bytes nebo None."""
    try:
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader, PdfWriter
    except Exception:
        return False
    try:
        # Unicode font s plnou českou diakritikou (ě/ř/ů/ď/ť/ň) — reportlab Helvetica (WinAnsi)
        # je nemá a dělá z nich ■. Robustní kaskáda (Marti 10.7.2026): _font_files() vezme
        # repo fonts/DejaVuSans.ttf (plná čeština) → Windows fonty → reportlab Vera. Dřív to
        # spoléhalo jen na C:\Windows\Fonts\verdana.ttf, která na serveru chyběla → registrace
        # spadla do except → Helvetica → rozdrolená diakritika v doložce. DejaVu v repu to řeší.
        FN, FB, FI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
        try:
            import os as _os
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from modules.erp.api.doc_templates import _font_files as _ff
            if "CzSans" not in set(pdfmetrics.getRegisteredFontNames()):
                _n, _b = _ff()
                if _n:
                    pdfmetrics.registerFont(TTFont("CzSans", _n))
                    pdfmetrics.registerFont(TTFont("CzSans-Bold", _b or _n))
                    _it = _n
                    for _c in (_n.replace("DejaVuSans.ttf", "DejaVuSans-Oblique.ttf"),
                               _n.replace("verdana.ttf", "verdanai.ttf"),
                               _n.replace("arial.ttf", "ariali.ttf")):
                        if _c != _n and _os.path.exists(_c):
                            _it = _c
                            break
                    pdfmetrics.registerFont(TTFont("CzSans-It", _it))
            if "CzSans" in set(pdfmetrics.getRegisteredFontNames()):
                FN, FB, FI = "CzSans", "CzSans-Bold", "CzSans-It"
        except Exception:
            pass
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        y = H - 30 * mm
        c.setFont(FB, 15)
        c.drawString(25 * mm, y, "Podpisová doložka — elektronické podepsání")
        y -= 10 * mm
        c.setFont(FN, 10)
        def line(txt, dy=6.2 * mm, bold=False):
            nonlocal y
            c.setFont(FB if bold else FN, 10)
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
        if sig_png_bytes:
            try:
                line("Podpis za %s:" % (e["our_party"] or "nás"), bold=True)
                sig = ImageReader(io.BytesIO(sig_png_bytes))
                iw, ih = sig.getSize()
                dispw = 55 * mm
                disph = dispw * ih / float(iw)
                c.drawImage(sig, 25 * mm, y - disph, width=dispw, height=disph,
                            mask="auto", preserveAspectRatio=True)
                c.line(25 * mm, y - disph - 1 * mm, 25 * mm + dispw, y - disph - 1 * mm)
                y = y - disph - 8 * mm
            except Exception:
                pass
        # Podpisový blok protistrany (Marti 10.7.2026): jejich auditní stopa se ukáže
        # rovnocenně k našemu bloku — slušnost vůči protistraně + poctivá doložka. Textový
        # SES „podpis" (jméno + čas + IP + e-mail); nezávisle na tom, kdo a z jakého e-mailu
        # podepsal — vykreslíme, co máme v auditní stopě.
        _cp = next((q for q in parties if q.get("role") != "internal" and q.get("signed")), None)
        if _cp:
            _csat = _cp["signed_at"].strftime("%d.%m.%Y %H:%M:%S") if _cp.get("signed_at") else "?"
            _cpnm = (_cp.get("jmeno") or "").strip()
            line("Podpis za protistranu%s:" % ((" — " + _cpnm) if _cpnm else ""), bold=True)
            line("   elektronicky (SES) podepsáno %s" % _csat)
            _cptail = "   IP %s" % (_cp.get("signed_ip") or "?")
            if _cp.get("email"):
                _cptail += ", e-mail %s" % _cp["email"]
            line(_cptail)
            try:
                c.line(25 * mm, y + 3 * mm, 25 * mm + 55 * mm, y + 3 * mm)
            except Exception:
                pass
            y -= 5 * mm
        line("Tato doložka je auditní stopou elektronického podpisu. Obě strany vyjádřily")
        line("souhlas s elektronickým podepsáním. Integritu dokumentu ověřuje SHA-256 otisk výše.")
        c.setFont(FI, 8)
        c.drawString(25 * mm, 15 * mm, "Vygenerováno systémem STRATEGIE dne %s" % datetime.now().strftime("%d.%m.%Y %H:%M"))
        c.showPage(); c.save()
        buf.seek(0)
        w = PdfWriter()
        for pg in PdfReader(io.BytesIO(orig_bytes)).pages:
            w.add_page(pg)
        for pg in PdfReader(buf).pages:
            w.add_page(pg)
        out = io.BytesIO()
        w.write(out)
        return out.getvalue()
    except Exception:
        return None


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


# ═══════════════ SAMOOBSLUŽNÝ PODPIS (Marti 2.7.2026) ═══════════════
# Nahraný PDF podepíše uloženým podpisem přihlášeného uživatele (SES + doložka
# + obrázek podpisu z tenant.user_signature), název MP_RRMMDD. Řeší přenos přes
# prohlížeč (upload do cloudu). Delivery: download | email (z marti-ai@ za uživatele) | save.

def _initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    return ("".join(p[0].upper() for p in parts[:2]) or "XX")


def _mp_filename(name: str, title: str) -> str:
    import re
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        d = datetime.now(ZoneInfo("Europe/Prague"))
    except Exception:
        d = datetime.now()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title or "").strip("_")[:60] or "dokument"
    return "%s_%s_%s_podepsano.pdf" % (_initials(name), d.strftime("%y%m%d"), slug)


def _build_self_signed_pdf(orig_bytes, signer_name, our_party, sig_png_bytes, doc_title):
    """Doložka (SES) + obrázek podpisu → připojí za originál. Vrací bytes / None."""
    import io
    import os as _os
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Prague"))
    except Exception:
        now = datetime.now()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from pypdf import PdfReader, PdfWriter
    except Exception:
        return None
    try:
        FN, FB, FI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
        try:
            _fd = (_os.environ.get("WINDIR") or "C:\\Windows") + "\\Fonts\\"
            if "CzSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("CzSans", _fd + "verdana.ttf"))
                pdfmetrics.registerFont(TTFont("CzSans-Bold", _fd + "verdanab.ttf"))
                pdfmetrics.registerFont(TTFont("CzSans-It", _fd + "verdanai.ttf"))
            FN, FB, FI = "CzSans", "CzSans-Bold", "CzSans-It"
        except Exception:
            pass
        sha = hashlib.sha256(orig_bytes).hexdigest()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        y = H - 28 * mm

        def L(t, dy=6.6 * mm, f=FN, sz=10):
            nonlocal y
            c.setFont(f, sz)
            c.drawString(24 * mm, y, t)
            y -= dy

        c.setFont(FB, 15)
        c.drawString(24 * mm, y, "PODPISOVÁ DOLOŽKA — elektronický podpis")
        y -= 11 * mm
        L("Dokument: %s" % (doc_title or ""), f=FB)
        L("Za: %s" % (our_party or ""))
        y -= 3 * mm
        L("Elektronicky podepsal:  %s" % signer_name, f=FB)
        L("Datum a čas:  %s (Europe/Prague)" % now.strftime("%d.%m.%Y %H:%M"))
        L("Způsob podpisu:  prostý elektronický podpis (SES) dle nařízení eIDAS č. 910/2014")
        L("Provedeno přes systém STRATEGIE na pokyn oprávněné osoby.")
        y -= 4 * mm
        c.setFont(FN, 9)
        c.drawString(24 * mm, y, "Podpis:")
        y -= 2 * mm
        if sig_png_bytes:
            try:
                sig = ImageReader(io.BytesIO(sig_png_bytes))
                iw, ih = sig.getSize()
                dispw = 58 * mm
                disph = dispw * ih / float(iw)
                c.drawImage(sig, 24 * mm, y - disph, width=dispw, height=disph,
                            mask="auto", preserveAspectRatio=True)
                c.line(24 * mm, y - disph - 1 * mm, 24 * mm + dispw, y - disph - 1 * mm)
                y = y - disph - 8 * mm
            except Exception:
                y -= 8 * mm
        c.setFont(FN, 8)
        for i in range(0, len(sha), 64):
            c.drawString(24 * mm, y, ("SHA-256 originálu: " if i == 0 else "                   ") + sha[i:i + 64])
            y -= 5 * mm
        c.setFont(FI, 8)
        c.drawString(24 * mm, 15 * mm, "Vygenerováno systémem STRATEGIE dne %s" % now.strftime("%d.%m.%Y %H:%M"))
        c.showPage()
        c.save()
        buf.seek(0)
        w = PdfWriter()
        for pg in PdfReader(io.BytesIO(orig_bytes)).pages:
            w.add_page(pg)
        for pg in PdfReader(buf).pages:
            w.add_page(pg)
        out = io.BytesIO()
        w.write(out)
        return out.getvalue()
    except Exception:
        return None


@contract_router.post("/app/sign/self")
async def sign_self(req: Request):
    """Samoobslužný podpis PDF: nahraný PDF podepíše uloženým podpisem přihlášeného
    uživatele. delivery = download | email | save. E-mail jde z marti-ai@ (za uživatele)."""
    uid = _uid(req)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        pdf_b64 = b.get("pdf_b64") or ""
        if "," in pdf_b64[:80] and ";base64" in pdf_b64[:80]:
            pdf_b64 = pdf_b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(pdf_b64)
        except Exception:
            raw = b""
        if not raw or raw[:4] != b"%PDF":
            return JSONResponse({"ok": False, "error": "Nahraj prosím PDF soubor."})
        title = (b.get("title") or "").strip()[:200] or "Dokument"
        delivery = (b.get("delivery") or "download").strip().lower()
        recipient = (b.get("recipient_email") or "").strip()[:200]
        our = (b.get("our_party") or "EUROSOFT - Control s.r.o.").strip()[:200]
        name = _user_name(s, uid)
        sig_b64 = s.execute(_t("SELECT png_b64 FROM tenant.user_signature WHERE user_id=:u"),
                            {"u": uid}).scalar()
        sig_bytes = base64.b64decode(sig_b64) if sig_b64 else None
        final = _build_self_signed_pdf(raw, name, our, sig_bytes, title)
        if not final:
            return JSONResponse({"ok": False, "error": "Podepsání PDF se nezdařilo."}, status_code=500)
        fn = _mp_filename(name, title)
        _log(s, tid, 0, "self_signed", name, _client_ip(req), detail=title)
        s.commit()
        if delivery == "download":
            return {"ok": True, "filename": fn, "pdf_b64": base64.b64encode(final).decode(),
                    "has_signature": bool(sig_bytes)}
        # email / save → do úložiště dokumentů
        try:
            from modules.rag.application.service import upload_document
            doc_id = upload_document(file_bytes=final, filename=fn, tenant_id=tid, user_id=uid)
        except Exception as _ue:
            return JSONResponse({"ok": False, "error": "Uložení dokumentu selhalo: %s" % type(_ue).__name__}, status_code=500)
        if delivery == "email":
            if "@" not in recipient:
                return JSONResponse({"ok": False, "error": "Zadej e-mail příjemce."})
            oem = s.execute(_t("""SELECT contact_value FROM public.user_contacts WHERE user_id=:u
                AND contact_type='email' AND status='active' ORDER BY is_primary DESC, id LIMIT 1"""),
                {"u": uid}).scalar()
            subj = (b.get("subject") or "").strip()[:250] or ("Podepsáno: %s" % title)
            body = (b.get("body") or "").strip() or (
                    "Dobrý den,\n\nv příloze zasílám elektronicky podepsaný dokument: %s.\n"
                    "Podepsáno prostým elektronickým podpisem (SES dle eIDAS) s podpisovou doložkou "
                    "(datum, otisk SHA-256). Tisk ani sken není potřeba.\n\nS pozdravem\n%s\n\n"
                    "(Odesláno systémem STRATEGIE jménem %s.)") % (title, name, name)
            from modules.notifications.application.email_service import queue_email
            queue_email(to=recipient, subject=subj, body=body,
                        persona_id=1, from_identity="persona", tenant_id=tid, purpose="user_request",
                        attachment_document_ids=[doc_id], cc=([oem] if oem else None))
            return {"ok": True, "sent": True, "recipient": recipient, "filename": fn, "doc_id": doc_id}
        return {"ok": True, "saved": True, "filename": fn, "doc_id": doc_id}
    except Exception as exc:
        try:
            s.rollback()
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": "Selhalo: %s" % type(exc).__name__}, status_code=500)
    finally:
        s.close()


@contract_router.post("/app/mail/send-doc")
async def mail_send_doc(req: Request):
    """Obecné odeslání e-mailu z AI schránky (marti-ai@, persona 1) s jednou přílohou
    (dokument v base64). Parent / finance-HR okruh. Marti 10.7.2026 — odpověď na dotaz
    kolegy + příloha. Body: {to, cc:[], subject, body, filename, doc_b64}."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not _can(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        raw = None
        fn = "priloha.pdf"
        ct = (req.headers.get("content-type") or "")
        if "multipart/form-data" in ct:
            # Spolehlivý přenos přílohy = skutečný soubor (ne base64 v JSON, který se
            # při dlouhém řetězci poškodí). Marti 10.7.2026.
            form = await req.form()
            to = str(form.get("to") or "").strip()
            _cc = form.get("cc") or ""
            cc = [x.strip() for x in str(_cc).split(",") if x.strip()]
            subject = str(form.get("subject") or "").strip()
            body = str(form.get("body") or "").strip()
            upl = form.get("file")
            if upl is not None and hasattr(upl, "read"):
                raw = await upl.read()
                fn = (getattr(upl, "filename", None) or "priloha.pdf")[:120]
        else:
            try:
                b = await req.json()
            except Exception:
                b = {}
            b = b or {}
            to = str(b.get("to") or "").strip()
            cc = [str(x).strip() for x in (b.get("cc") or []) if str(x).strip()]
            subject = str(b.get("subject") or "").strip()
            body = str(b.get("body") or "").strip()
            fn = str(b.get("filename") or "priloha.pdf").strip()[:120]
            doc_b64 = b.get("doc_b64") or ""
            if doc_b64:
                try:
                    raw = base64.b64decode(doc_b64)
                except Exception as exc:
                    return JSONResponse({"ok": False, "error": "base64 přílohy: " + str(exc)[:120]}, status_code=400)
            rf = str(b.get("repo_file") or "").strip()
            if rf and not raw:
                # Příloha přenesena na server přes git (spolehlivé, byte-přesné) místo base64
                # v JSON (dlouhý řetězec se cestou komolí). Marti 10.7.2026.
                try:
                    import os as _osrf
                    _root = _osrf.path.abspath(_osrf.path.join(_osrf.path.dirname(__file__), "..", "..", ".."))
                    _p = _osrf.path.normpath(_osrf.path.join(_root, rf))
                    if _p.startswith(_root) and _osrf.path.isfile(_p):
                        with open(_p, "rb") as _fh:
                            raw = _fh.read()
                        fn = _osrf.path.basename(_p)[:120]
                    else:
                        return JSONResponse({"ok": False, "error": "repo_file nenalezen"}, status_code=400)
                except Exception as exc:
                    return JSONResponse({"ok": False, "error": "repo_file: " + str(exc)[:120]}, status_code=500)
        if "@" not in to or not subject or not body:
            return JSONResponse({"ok": False, "error": "Chybí to / subject / body."}, status_code=400)
        att_ids = None
        if raw:
            try:
                from modules.rag.application.service import upload_document
                doc_id = upload_document(file_bytes=raw, filename=fn, tenant_id=tid, user_id=uid)
                att_ids = [doc_id] if doc_id else None
            except Exception as exc:
                return JSONResponse({"ok": False, "error": "příloha selhala: " + str(exc)[:150]}, status_code=500)
        from modules.notifications.application.email_service import queue_email
        try:
            res = queue_email(to=to, subject=subject[:250], body=body, cc=(cc or None),
                              persona_id=1, from_identity="persona", tenant_id=tid,
                              purpose="user_request", attachment_document_ids=att_ids)
        except Exception as exc:
            return JSONResponse({"ok": False, "error": "odeslání selhalo: " + str(exc)[:150]}, status_code=500)
        return {"ok": True, "vysledek": res, "to": to, "cc": cc, "priloha": bool(att_ids)}
    finally:
        s.close()
