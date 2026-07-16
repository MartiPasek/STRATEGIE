"""Univerzální bankovní napojení (Bank API) — backend, Fáze 1 (Claude id=23, 24.6.2026).

Connection per firma per banka + bezpečné uložení mTLS certifikátu (.p12) + Client ID +
heslo do trezoru (Fernet, _vault_fernet — stejný jako datovky). Read-only adaptér (RB
Premium API) → staging tenant.bank_transaction_raw (increment 2).

Schéma: docs/bank_api_schema_v1.sql. Konzultace + review Marti-AI: docs/bank_api_napojeni_v1.md.
Spec RB Premium API: docs/bank_api_rb_adapter.md (host api.rb.cz, X-IBM-Client-Id + mTLS).

Bezpečnost: certifikát + heslo + client_id se ukládají jako JEDEN Fernet-šifrovaný JSON
blob ve fw.app_secret (skey='bankcert:<connection_id>'), bank_connection.vault_ref = ten skey.
Nikdy plaintext do DB/logu/odpovědi. Parent-only.
"""
from __future__ import annotations

import base64
import json as _json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text as _t

bank_router = APIRouter(prefix="/api/v1/erp", tags=["bank-api"])
_TENANT = 2


# ── session + identita (lazy import z router, ať není cirkulární) ──
def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _is_parent(uid):
    # Okruh řídicího pultu = rodiče + scoped approveři (Petra 18 finance+HR, Šárka 13
    # personalistika). Marti 30.6.2026: „stejná práva pro nás pro všechny — naše sandboxy."
    # Banka/pokladny/finance/saldo/účtování = finanční moduly cockpitu → celý okruh.
    from modules.erp.api.router import is_marti_parent, _SCOPED_APPROVER_UIDS
    try:
        return bool(is_marti_parent(uid)) or (uid in _SCOPED_APPROVER_UIDS)
    except Exception:
        return False


def _fernet():
    from modules.erp.api.router import _vault_fernet
    return _vault_fernet()


def _enc_text(plain: str):
    f = _fernet()
    if not f or plain is None:
        return None
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def _dec_text(enc):
    f = _fernet()
    if not f or not enc:
        return None
    try:
        return f.decrypt(enc.encode("ascii")).decode("utf-8")
    except Exception:
        return None


# ── trezor: cert bundle (client_id + p12 + heslo) jako 1 šifrovaný blob ──
def _store_cert_bundle(s, connection_id: int, client_id: str, p12_b64: str, password: str):
    """Zašifruje {client_id, p12, password} a uloží do fw.app_secret. Vrací skey (vault_ref)."""
    f = _fernet()
    if not f:
        return None
    skey = "bankcert:%d" % connection_id
    blob = _json.dumps({"client_id": client_id or "", "p12_b64": p12_b64 or "", "password": password or ""})
    sval = f.encrypt(blob.encode("utf-8")).decode("ascii")
    s.execute(_t("INSERT INTO fw.app_secret(skey,sval) VALUES(:k,:v) "
                 "ON CONFLICT (skey) DO UPDATE SET sval=EXCLUDED.sval"), {"k": skey, "v": sval})
    return skey


def load_cert_bundle(s, vault_ref: str):
    """Pro adaptér (increment 2): dešifruje bundle ephemeral. NIKDY nelogovat výsledek."""
    f = _fernet()
    if not f or not vault_ref:
        return None
    row = s.execute(_t("SELECT sval FROM fw.app_secret WHERE skey=:k"), {"k": vault_ref}).first()
    if not row or not row[0]:
        return None
    try:
        return _json.loads(f.decrypt(row[0].encode("ascii")).decode("utf-8"))
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════
# GET /app/bank/overview — providers + connections + účty (bez tajemství)
# ════════════════════════════════════════════════════════════════════
@bank_router.get("/app/bank/overview")
def bank_overview(request: Request):
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        provs = [dict(r) for r in s.execute(_t(
            "SELECT id, kod, nazev, base_url, auth_typ, aktivni FROM tenant.bank_provider "
            "WHERE aktivni ORDER BY nazev")).mappings().all()]
        comps = [dict(r) for r in s.execute(_t(
            "SELECT id, code, nazev FROM tenant.company WHERE tenant_id=:tn AND COALESCE(aktivni,true) "
            "ORDER BY id"), {"tn": _TENANT}).mappings().all()]
        conns = [dict(r) for r in s.execute(_t(
            "SELECT c.id, c.company_id, co.code AS company_code, co.nazev AS company_nazev, "
            "c.provider_id, p.nazev AS provider_nazev, c.nazev, c.stav, "
            "(c.vault_ref IS NOT NULL) AS has_cert, c.created_at, c.updated_at "
            "FROM tenant.bank_connection c "
            "LEFT JOIN tenant.company co ON co.id=c.company_id "
            "LEFT JOIN tenant.bank_provider p ON p.id=c.provider_id "
            "WHERE c.tenant_id=:tn ORDER BY c.id"), {"tn": _TENANT}).mappings().all()]
        accs = [dict(r) for r in s.execute(_t(
            "SELECT a.id, a.connection_id, a.cislo_uctu, a.nazev, a.mena, "
            "a.sc_historie, a.sc_zustatky, a.sc_vypisy, a.sc_platby, a.aktivni "
            "FROM tenant.bank_connection_account a "
            "JOIN tenant.bank_connection c ON c.id=a.connection_id "
            "WHERE c.tenant_id=:tn ORDER BY a.id"), {"tn": _TENANT}).mappings().all()]
        for c in conns:
            c["accounts"] = [a for a in accs if a["connection_id"] == c["id"]]
        return {"ok": True, "providers": provs, "companies": comps, "connections": conns}
    finally:
        s.close()


# ════════════════════════════════════════════════════════════════════
# POST /app/bank/setup — vytvoř connection + účty + ulož cert (vše v 1)
# body: {company_id, provider_kod, nazev, client_id, p12_base64, password,
#        accounts:[{cislo_uctu, nazev, mena, sc_historie, sc_zustatky, sc_vypisy}]}
# ════════════════════════════════════════════════════════════════════
@bank_router.post("/app/bank/setup")
async def bank_setup(request: Request):
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    if not _fernet():
        return JSONResponse({"ok": False, "error": "vault_not_configured — nastav STRATEGIE_VAULT_KEY / fw.app_secret."},
                            status_code=400)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)

    company_id = body.get("company_id")
    provider_kod = (body.get("provider_kod") or "RB_PREMIUM_API").strip()
    nazev = (body.get("nazev") or "").strip() or "Bankovní napojení"
    client_id = (body.get("client_id") or "").strip()
    p12_b64 = (body.get("p12_base64") or "").strip()
    password = body.get("password") or ""
    accounts = body.get("accounts") or []

    # validace base64 certu (pokud zadán)
    if p12_b64:
        try:
            base64.b64decode(p12_b64, validate=True)
        except Exception:
            return JSONResponse({"ok": False, "error": "p12_base64 neni validni base64"}, status_code=400)

    s = _sess()
    try:
        prov = s.execute(_t("SELECT id FROM tenant.bank_provider WHERE kod=:k"), {"k": provider_kod}).first()
        if not prov:
            return JSONResponse({"ok": False, "error": "provider_not_found: " + provider_kod}, status_code=400)
        provider_id = prov[0]

        conn_id = body.get("connection_id")
        if conn_id:
            s.execute(_t("UPDATE tenant.bank_connection SET company_id=:co, provider_id=:p, nazev=:n, "
                         "updated_at=now() WHERE id=:id AND tenant_id=:tn"),
                      {"co": company_id, "p": provider_id, "n": nazev, "id": conn_id, "tn": _TENANT})
        else:
            conn_id = s.execute(_t(
                "INSERT INTO tenant.bank_connection (tenant_id, company_id, provider_id, nazev, stav, created_by) "
                "VALUES (:tn,:co,:p,:n,'active',:by) RETURNING id"),
                {"tn": _TENANT, "co": company_id, "p": provider_id, "n": nazev, "by": "user:%s" % uid}).scalar()

        # účty: synchronizuj JEN když je seznam zadán (jinak nech discover-naplněné být)
        if accounts:
            s.execute(_t("DELETE FROM tenant.bank_connection_account WHERE connection_id=:c"), {"c": conn_id})
        for a in accounts:
            cislo = (a.get("cislo_uctu") or "").strip()
            if not cislo:
                continue
            s.execute(_t(
                "INSERT INTO tenant.bank_connection_account "
                "(connection_id, cislo_uctu, nazev, mena, sc_historie, sc_zustatky, sc_vypisy, sc_platby) "
                "VALUES (:c,:cu,:n,:m,:h,:z,:v,false)"),
                {"c": conn_id, "cu": cislo, "n": (a.get("nazev") or "").strip() or None,
                 "m": (a.get("mena") or "CZK").strip(),
                 "h": bool(a.get("sc_historie", True)), "z": bool(a.get("sc_zustatky", True)),
                 "v": bool(a.get("sc_vypisy", True))})

        # cert bundle do trezoru (jen když je cert zadán)
        if client_id or p12_b64:
            skey = _store_cert_bundle(s, conn_id, client_id, p12_b64, password)
            if skey:
                s.execute(_t("UPDATE tenant.bank_connection SET vault_ref=:r, updated_at=now() "
                             "WHERE id=:id"), {"r": skey, "id": conn_id})
        s.commit()
        return {"ok": True, "connection_id": conn_id, "has_cert": bool(client_id or p12_b64)}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}, status_code=500)
    finally:
        s.close()


# ════════════════════════════════════════════════════════════════════
# RB Premium API adaptér (read) — mTLS z trezoru (ephemeral), host api.rb.cz
# Spec: docs/bank_api_rb_adapter.md. X-IBM-Client-Id + klientský cert (.p12).
# ════════════════════════════════════════════════════════════════════
_RB_BASE = "https://api.rb.cz/rbcz/premium/api"


def _p12_to_pem(p12_b64: str, password: str):
    """PKCS#12 (.p12) → (cert_chain_pem_bytes, key_pem_bytes). Ephemeral v paměti."""
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
    import base64 as _b64
    data = _b64.b64decode(p12_b64)
    pwd = (password or "").encode("utf-8") or None
    key, cert, addl = pkcs12.load_key_and_certificates(data, pwd)
    cert_pem = cert.public_bytes(Encoding.PEM)
    for c in (addl or []):
        cert_pem += c.public_bytes(Encoding.PEM)
    key_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    return cert_pem, key_pem


def _rb_call(bundle: dict, method: str, path: str, params=None, json_body=None, accept=None,
             data=None, content_type=None, extra_headers=None, timeout=40):
    """mTLS volání na RB. Cert z trezoru → ephemeral temp PEM (smaže se hned). Vrací requests.Response.

    json_body = JSON payload (Content-Type application/json).
    data = syrové tělo (bytes/str) — pro import dávky (Gemini/SEPA-XML soubor); pošli i content_type.
    extra_headers = dict dalších hlaviček (např. Batch-Import-Format).
    """
    import requests, tempfile, os, uuid
    cert_pem, key_pem = _p12_to_pem(bundle.get("p12_b64") or "", bundle.get("password") or "")
    cf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); cf.write(cert_pem); cf.close()
    kf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); kf.write(key_pem); kf.close()
    try:
        headers = {"X-IBM-Client-Id": bundle.get("client_id") or "", "X-Request-Id": uuid.uuid4().hex[:60]}
        if accept:
            headers["Accept"] = accept
        if content_type:
            headers["Content-Type"] = content_type
        if extra_headers:
            headers.update({k: v for k, v in extra_headers.items() if v is not None})
        return requests.request(method, _RB_BASE + path, headers=headers, params=params,
                                json=json_body, data=data, cert=(cf.name, kf.name), timeout=timeout)
    finally:
        for p in (cf.name, kf.name):
            try:
                os.unlink(p)
            except Exception:
                pass


# ── Fáze 2: PLATBY — import dávky (platáku) do RB. NIKDY neprovede platbu, jen nahraje do IB (FOR_SIGN). ──
# Batch-Import-Format hodnoty RB Premium API (POST /payments/batches, autoritativní swagger 1.1.20240910):
#   GEMINI-P11 (tuzemský platák .p11 = náš CZK render), GEMINI-P32, GEMINI-F84 (zahraniční .f84 = náš EUR),
#   ABO-KPC, DOM-XML, SEPA-XML, CFD, CFU, CFA. Consumes text/plain. Vrací {batchFileId}.
_RB_BATCH_FORMATS = ("GEMINI-P11", "GEMINI-P32", "GEMINI-F84",
                     "ABO-KPC", "DOM-XML", "SEPA-XML", "CFD", "CFU", "CFA")
# mapování naší měny/typu platáku → RB Gemini formát
_RB_GEMINI_BY_MENA = {"CZK": "GEMINI-P11", "EUR": "GEMINI-F84"}


def _rb_import_batch(bundle: dict, content, batch_format: str, batch_name=None, combined=False):
    """Nahraje dávku plateb (obsah platáku) do RB → IB jako koncept k PODPISU. NEPROVEDE platbu.
    content = bytes (CP1250 Gemini soubor) nebo str; vrací (ok, dict). Člověk pak podepíše v bankovnictví.
    combined=True → Batch-Combined-Payments (sdružené platáky). Batch-Autocorrect necháváme default (true)."""
    if isinstance(content, str):
        content = content.encode("cp1250", "replace")
    xh = {"Batch-Import-Format": batch_format}
    if batch_name:
        xh["Batch-Name"] = str(batch_name)[:50]
    if combined:
        xh["Batch-Combined-Payments"] = "true"
    r = _rb_call(bundle, "POST", "/payments/batches", data=content,
                 content_type="text/plain", extra_headers=xh,
                 accept="application/json", timeout=60)
    ok = 200 <= r.status_code < 300
    try:
        body = r.json()
    except Exception:
        body = {"text": (r.text or "")[:400]}
    err = None
    if not ok and isinstance(body, dict):
        err = body.get("error") or body.get("error_description")
    return ok, {"http": r.status_code, "batchFileId": (body or {}).get("batchFileId"),
                "error": err, "raw": body}


def _rb_batch_status(bundle: dict, batch_file_id: str):
    """Stav importované dávky: batchFileStatus (OK/ERROR/DELETED) + per-dávka status
    (DRAFT/ERROR/FOR_SIGN/VERIFIED/PASSING_TO_BANK/PASSED/…). 202 = ještě se zpracovává."""
    r = _rb_call(bundle, "GET", "/payments/batches/%s" % batch_file_id,
                 accept="application/json", timeout=40)
    ok = 200 <= r.status_code < 300
    try:
        body = r.json()
    except Exception:
        body = {"text": (r.text or "")[:400]}
    items = []
    if isinstance(body, dict):
        for it in (body.get("batchItems") or []):
            items.append({"status": it.get("status"), "batchType": it.get("batchType"),
                          "pocet": it.get("numberOfPayments"), "suma": it.get("sumAmount"),
                          "mena": it.get("sumAmountCurrencyId")})
    return ok, {"http": r.status_code,
                "batchFileStatus": (body or {}).get("batchFileStatus"),
                "errorCode": (body or {}).get("errorCode"),
                "errorDescription": (body or {}).get("errorDescription"),
                "polozky": items, "raw": body}


def _rb_accounts(bundle: dict):
    out, page = [], 1
    while True:
        r = _rb_call(bundle, "GET", "/accounts", params={"page": page, "size": 50})
        if r.status_code == 204:
            break
        r.raise_for_status()
        j = r.json()
        out += j.get("accounts", [])
        if j.get("last", True):
            break
        page += 1
    return out


def _norm_tx(t: dict, ccy: str) -> dict:
    amt = t.get("amount", {}) or {}
    det = ((t.get("entryDetails", {}) or {}).get("transactionDetails", {}) or {})
    cp = ((det.get("relatedParties", {}) or {}).get("counterParty", {}) or {})
    acc = (cp.get("account", {}) or {})
    rem = (det.get("remittanceInformation", {}) or {})
    cref = (rem.get("creditorReferenceInformation", {}) or {})
    bd = t.get("bookingDate") or ""
    return {
        "ext_id": str(t.get("entryReference") or ""),
        "datum": bd[:10] or None,
        "castka": amt.get("value"),
        "mena": amt.get("currency") or ccy,
        "smer": "out" if t.get("creditDebitIndication") == "DBIT" else "in",
        "protiucet": acc.get("iban") or acc.get("accountNumber"),
        "vs": cref.get("variable"), "ks": cref.get("constant"), "ss": cref.get("specific"),
        "zprava": rem.get("unstructured") or det.get("originatorMessage"),
        "raw": t,
    }


def _bundle_for(s, connection_id: int):
    row = s.execute(_t("SELECT vault_ref FROM tenant.bank_connection WHERE id=:id AND tenant_id=:tn"),
                    {"id": connection_id, "tn": _TENANT}).first()
    if not row or not row[0]:
        return None
    return load_cert_bundle(s, row[0])


def _log(s, conn_id, acc_id, operace, uroven, actor, vysledek, detail=None):
    try:
        s.execute(_t("INSERT INTO tenant.bank_api_log (connection_id, account_id, operace, uroven, actor, vysledek, detail) "
                     "VALUES (:c,:a,:o,:u,:ac,:v,CAST(:d AS jsonb))"),
                  {"c": conn_id, "a": acc_id, "o": operace, "u": uroven, "ac": actor, "v": vysledek,
                   "d": _json.dumps(detail or {})})
    except Exception:
        pass


@bank_router.post("/app/bank/connection/{cid}/discover")
async def bank_discover(cid: int, request: Request):
    """Test spojení + načtení seznamu účtů z banky → upsert bank_connection_account."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        bundle = _bundle_for(s, cid)
        if not bundle:
            return JSONResponse({"ok": False, "error": "Napojení nemá uložený certifikát."}, status_code=400)
        try:
            accs = _rb_accounts(bundle)
        except Exception as exc:
            _log(s, cid, None, "get_accounts", "batch", "user:%s" % uid, "ERROR:%s" % type(exc).__name__)
            s.commit()
            return JSONResponse({"ok": False, "error": "RB volání selhalo: %s: %s" % (type(exc).__name__, str(exc)[:160])}, status_code=502)
        n = 0
        for a in accs:
            cislo = a.get("accountNumber") or ""
            if not cislo:
                continue
            mena = a.get("mainCurrency") or "CZK"
            nazev = a.get("accountName") or a.get("friendlyName")
            res = s.execute(_t(
                "INSERT INTO tenant.bank_connection_account (connection_id, cislo_uctu, nazev, mena, sc_historie, sc_zustatky, sc_vypisy, sc_platby) "
                "SELECT :c,:cu,:n,:m,true,true,true,false WHERE NOT EXISTS "
                "(SELECT 1 FROM tenant.bank_connection_account WHERE connection_id=:c AND cislo_uctu=:cu)"),
                {"c": cid, "cu": cislo, "n": nazev, "m": mena})
            n += (res.rowcount or 0)
        _log(s, cid, None, "get_accounts", "batch", "user:%s" % uid, "OK:%d" % len(accs))
        s.commit()
        return {"ok": True, "found": len(accs), "upserted": n,
                "accounts": [{"cislo_uctu": a.get("accountNumber"), "nazev": a.get("accountName"),
                              "mena": a.get("mainCurrency"), "iban": a.get("iban"),
                              "typ": a.get("accountTypeId")} for a in accs]}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/bank/connection/{cid}/load")
async def bank_load_tx(cid: int, request: Request):
    """Načte transakce (posledních 90 dní) pro účty s scope historie → staging bank_transaction_raw."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    import datetime as _dt
    s = _sess()
    try:
        bundle = _bundle_for(s, cid)
        if not bundle:
            return JSONResponse({"ok": False, "error": "Napojení nemá uložený certifikát."}, status_code=400)
        accs = [dict(r) for r in s.execute(_t(
            "SELECT id, cislo_uctu, mena FROM tenant.bank_connection_account "
            "WHERE connection_id=:c AND aktivni AND sc_historie ORDER BY id"), {"c": cid}).mappings().all()]
        date_to = _dt.date.today()
        date_from = date_to - _dt.timedelta(days=89)
        total, per = 0, []
        for a in accs:
            ccy = a["mena"] or "CZK"
            got = 0
            try:
                page = 1
                while True:
                    r = _rb_call(bundle, "GET", "/accounts/%s/%s/transactions" % (a["cislo_uctu"], ccy),
                                 params={"from": date_from.isoformat(), "to": date_to.isoformat(), "page": page})
                    if r.status_code == 204:
                        break
                    r.raise_for_status()
                    j = r.json()
                    for t in j.get("transactions", []):
                        tx = _norm_tx(t, ccy)
                        if not tx["ext_id"]:
                            continue
                        s.execute(_t(
                            "INSERT INTO tenant.bank_transaction_raw "
                            "(account_id, ext_id, datum, castka, mena, smer, protiucet, vs, ks, ss, zprava, raw) "
                            "VALUES (:aid,:e,:d,:ca,:m,:sm,:pu,:vs,:ks,:ss,:z,CAST(:raw AS jsonb)) "
                            "ON CONFLICT (account_id, ext_id) WHERE ext_id IS NOT NULL DO NOTHING"),
                            {"aid": a["id"], "e": tx["ext_id"], "d": tx["datum"], "ca": tx["castka"],
                             "m": tx["mena"], "sm": tx["smer"], "pu": tx["protiucet"], "vs": tx["vs"],
                             "ks": tx["ks"], "ss": tx["ss"], "z": tx["zprava"], "raw": _json.dumps(tx["raw"])})
                        got += 1
                    if j.get("lastPage", True):
                        break
                    page += 1
                _log(s, cid, a["id"], "get_transactions", "batch", "user:%s" % uid, "OK:%d" % got)
            except Exception as exc:
                _log(s, cid, a["id"], "get_transactions", "batch", "user:%s" % uid, "ERROR:%s" % type(exc).__name__)
                per.append({"ucet": a["cislo_uctu"], "chyba": "%s: %s" % (type(exc).__name__, str(exc)[:120])})
                continue
            total += got
            per.append({"ucet": a["cislo_uctu"], "nacteno": got})
        s.commit()
        return {"ok": True, "od": date_from.isoformat(), "do": date_to.isoformat(),
                "celkem": total, "ucty": per}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}, status_code=500)
    finally:
        s.close()


def _rb_balance(bundle, cislo_uctu, ccy):
    """Zůstatek účtu z RB API (GET /accounts/{acc}/{ccy}/balance). Parsuje běžné tvary
    odpovědi defenzivně. → float | None. Claude 8.7.2026."""
    try:
        r = _rb_call(bundle, "GET", "/accounts/%s/%s/balance" % (cislo_uctu, ccy))
        if r.status_code == 204:
            return None
        r.raise_for_status()
        j = r.json()
    except Exception:
        return None

    def _num(x):
        if isinstance(x, dict):
            x = x.get("value")
        try:
            return float(x)
        except Exception:
            return None
    if isinstance(j, dict):
        for key in ("currentBalance", "availableBalance", "balance", "bookedBalance",
                    "closingBalance", "value"):
            if key in j:
                v = _num(j[key])
                if v is not None:
                    return v
        for arrkey in ("balances", "accountBalances"):
            arr = j.get(arrkey)
            if isinstance(arr, list) and arr:
                first = arr[0] if isinstance(arr[0], dict) else {}
                v = _num(first.get("amount") or first.get("balance") or first)
                if v is not None:
                    return v
    return None


def _rb_balances(bundle, cislo_uctu):
    """Zůstatky účtu ze VŠECH měn: GET /accounts/{cislo}/balance → currencyFolders[].
    → {currency: value}. Bere CLBD (účetní zůstatek), fallback CLAV (disponibilní).
    Ověřeno na reálné RB odpovědi (Marti 8.7.2026). Jeden call = CZK i EUR."""
    r = _rb_call(bundle, "GET", "/accounts/%s/balance" % cislo_uctu)
    if r.status_code == 204:
        return {}
    r.raise_for_status()
    j = r.json()
    out = {}
    for f in (j.get("currencyFolders") or []):
        ccy = f.get("currency")
        if not ccy:
            continue
        bals = {}
        for b in (f.get("balances") or []):
            if b.get("balanceType") and b.get("value") is not None:
                bals[b["balanceType"]] = b["value"]
        val = bals.get("CLBD")
        if val is None:
            val = bals.get("CLAV")
        if val is not None:
            try:
                out[ccy] = float(val)
            except Exception:
                pass
    return out


def sync_all_tx(days: int = 90):
    """Automatický sync bankovních výpisů: pro VŠECHNA aktivní napojení načte transakce
    (posl. `days` dní) pro účty se scope historie + zjistí zůstatky (scope zůstatky).
    Idempotentní (ON CONFLICT DO NOTHING). Volá se ze scheduleru i ručně. Claude 8.7.2026."""
    import datetime as _dt
    s = _sess()
    nacteno, zustatku, chyb = 0, 0, 0
    try:
        conns = [r[0] for r in s.execute(_t(
            "SELECT id FROM tenant.bank_connection WHERE tenant_id=:tn ORDER BY id"),
            {"tn": _TENANT}).fetchall()]
        date_to = _dt.date.today()
        date_from = date_to - _dt.timedelta(days=max(1, days) - 1)
        for cid in conns:
            bundle = _bundle_for(s, cid)
            if not bundle:
                continue
            accs = [dict(r) for r in s.execute(_t(
                "SELECT id, cislo_uctu, COALESCE(nazev,'') nazev, mena, sc_historie, sc_zustatky "
                "FROM tenant.bank_connection_account "
                "WHERE connection_id=:c AND aktivni AND (sc_historie OR sc_zustatky) ORDER BY id"),
                {"c": cid}).mappings().all()]
            present = {(a["cislo_uctu"], (a["mena"] or "CZK")) for a in accs}

            def _ensure_ccy_acc(cislo, ccy, nazev):
                row = s.execute(_t(
                    "SELECT id FROM tenant.bank_connection_account "
                    "WHERE connection_id=:c AND cislo_uctu=:cu AND mena=:m"),
                    {"c": cid, "cu": cislo, "m": ccy}).first()
                if row:
                    return row[0]
                return s.execute(_t(
                    "INSERT INTO tenant.bank_connection_account "
                    "(connection_id, cislo_uctu, nazev, mena, sc_historie, sc_zustatky, sc_vypisy, sc_platby) "
                    "VALUES (:c,:cu,:n,:m,true,true,true,false) RETURNING id"),
                    {"c": cid, "cu": cislo, "n": ((nazev or "") + " (" + ccy + ")").strip(), "m": ccy}).scalar()

            for a in accs:
                ccy_main = a["mena"] or "CZK"
                # kanály = hlavní měna účtu + (jednou) EUR SONDA pro ne-EUR účet bez EUR řádku.
                # EUROSOFT drží EUR pod stejným číslem účtu (platby zahraničně z CZK) →
                # RB je vrací přes /accounts/{cislo}/EUR/. EUR řádek se založí líně jen když data jsou.
                channels = [(a["id"], a["cislo_uctu"], ccy_main, a.get("sc_historie"))]
                if ccy_main != "EUR" and (a["cislo_uctu"], "EUR") not in present:
                    channels.append((None, a["cislo_uctu"], "EUR", True))
                for (acc_id, cislo, ccy, do_hist) in channels:
                    probe = acc_id is None
                    if do_hist:
                        try:
                            page = 1
                            while True:
                                r = _rb_call(bundle, "GET", "/accounts/%s/%s/transactions" % (cislo, ccy),
                                             params={"from": date_from.isoformat(), "to": date_to.isoformat(), "page": page})
                                if r.status_code == 204:
                                    break
                                r.raise_for_status()
                                j = r.json()
                                txs = j.get("transactions", [])
                                if txs and acc_id is None:
                                    acc_id = _ensure_ccy_acc(cislo, ccy, a["nazev"])
                                for t in txs:
                                    tx = _norm_tx(t, ccy)
                                    if not tx["ext_id"]:
                                        continue
                                    res = s.execute(_t(
                                        "INSERT INTO tenant.bank_transaction_raw "
                                        "(account_id, ext_id, datum, castka, mena, smer, protiucet, vs, ks, ss, zprava, raw) "
                                        "VALUES (:aid,:e,:d,:ca,:m,:sm,:pu,:vs,:ks,:ss,:z,CAST(:raw AS jsonb)) "
                                        "ON CONFLICT (account_id, ext_id) WHERE ext_id IS NOT NULL DO NOTHING"),
                                        {"aid": acc_id, "e": tx["ext_id"], "d": tx["datum"], "ca": tx["castka"],
                                         "m": tx["mena"], "sm": tx["smer"], "pu": tx["protiucet"], "vs": tx["vs"],
                                         "ks": tx["ks"], "ss": tx["ss"], "z": tx["zprava"], "raw": _json.dumps(tx["raw"])})
                                    nacteno += (res.rowcount or 0)
                                if j.get("lastPage", True):
                                    break
                                page += 1
                        except Exception:
                            if not probe:
                                chyb += 1
                                _log(s, cid, acc_id, "get_transactions", "sched", "system", "ERROR:%s" % ccy)
                # ZŮSTATKY — jeden call /accounts/{cislo}/balance → všechny měny (currencyFolders)
                if a.get("sc_zustatky"):
                    try:
                        for fccy, val in _rb_balances(bundle, a["cislo_uctu"]).items():
                            aid = a["id"] if fccy == ccy_main else _ensure_ccy_acc(a["cislo_uctu"], fccy, a["nazev"])
                            s.execute(_t("UPDATE tenant.bank_connection_account "
                                         "SET zustatek=:z, zustatek_mena=:m, zustatek_at=now() WHERE id=:id"),
                                      {"z": val, "m": fccy, "id": aid})
                            zustatku += 1
                    except Exception:
                        chyb += 1
                        _log(s, cid, a["id"], "get_balance", "sched", "system", "ERROR")
            s.commit()
        # po nasyncování rovnou spárovat (aby výpisy nebyly věčně „nové")
        napar = None
        try:
            napar = parovat_all(s).get("naparovano")
        except Exception:
            try:
                s.rollback()
            except Exception:
                pass
        return {"ok": True, "done": True, "nacteno": nacteno, "zustatku": zustatku,
                "chyb": chyb, "naparovano": napar}
    except Exception as exc:
        try:
            s.rollback()
        except Exception:
            pass
        return {"ok": False, "done": True, "_msg": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
    finally:
        s.close()


@bank_router.post("/app/bank/sync-now")
async def bank_sync_now(request: Request):
    """Ruční spuštění sync výpisů + zůstatků (tlačítko „Načíst teď"). Parent/cockpit."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    out = sync_all_tx()
    return out


@bank_router.get("/app/bank/zustatky")
def bank_zustatky(request: Request):
    """Zůstatky účtů (z posledního sync) + poslední transakce. Pro kartu nad výpisy.
    Parent/cockpit. Claude 8.7.2026."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        rows = s.execute(_t(
            "SELECT a.cislo_uctu, COALESCE(a.nazev,''), COALESCE(a.mena,'CZK'), a.zustatek, "
            "  COALESCE(a.zustatek_mena, a.mena, 'CZK'), "
            "  to_char(a.zustatek_at AT TIME ZONE 'Europe/Prague','DD.MM.YYYY HH24:MI'), "
            "  COALESCE(c.company_id,1), "
            "  (SELECT to_char(max(t.datum),'DD.MM.YYYY') FROM tenant.bank_transaction_raw t WHERE t.account_id=a.id) "
            "FROM tenant.bank_connection_account a "
            "LEFT JOIN tenant.bank_connection c ON c.id=a.connection_id "
            "WHERE COALESCE(a.aktivni,true) ORDER BY c.company_id, a.cislo_uctu")).fetchall()
        out = []
        for r in rows:
            out.append({"ucet": r[0], "nazev": r[1], "mena": r[2],
                        "zustatek": float(r[3]) if r[3] is not None else None,
                        "zustatek_mena": r[4], "zustatek_at": r[5] or "",
                        "firma": int(r[6]) if r[6] is not None else 1,
                        "posledni_tx": r[7] or ""})
        return {"ok": True, "ucty": out}
    finally:
        s.close()


@bank_router.get("/app/bank/vypisy")
def bank_vypisy(request: Request):
    """Výpisy — richší list (vč. id pro detail + protistrana z raw). Filtry firma+měna.
    Nahrazuje /app/platby/vypisy pro UI. Claude 8.7.2026."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma = (request.query_params.get("firma") or "all").strip()
    mena = (request.query_params.get("mena") or "all").strip().upper()
    s = _sess()
    try:
        conds, params = [], {}
        if firma in ("1", "2"):
            params["ff"] = int(firma); conds.append("c.company_id = :ff")
        if mena in ("CZK", "EUR"):
            params["mm"] = mena; conds.append("COALESCE(NULLIF(t.mena,''),'CZK') = :mm")
        base = ("FROM tenant.bank_transaction_raw t "
                "LEFT JOIN tenant.bank_connection_account a ON a.id=t.account_id "
                "LEFT JOIN tenant.bank_connection c ON c.id=a.connection_id"
                + ((" WHERE " + " AND ".join(conds)) if conds else ""))
        rows = s.execute(_t(
            "SELECT t.id, to_char(t.datum,'DD.MM.YYYY') d, t.castka, COALESCE(NULLIF(t.mena,''),'CZK') mena, "
            "  COALESCE(t.smer,'') smer, COALESCE(t.protiucet,'') protiucet, COALESCE(t.vs,'') vs, "
            "  LEFT(COALESCE(t.zprava,''),90) zprava, COALESCE(t.par_metoda,'') met, "
            "  COALESCE(t.par_doklad_rada,'') rada, COALESCE(t.par_zakazka,'') zak, COALESCE(t.par_kategorie,'') kat, "
            "  COALESCE(c.company_id,1) firma, "
            "  COALESCE(t.raw #>> '{entryDetails,transactionDetails,relatedParties,counterParty,name}','') protistrana "
            + base + " ORDER BY t.datum DESC, t.id DESC LIMIT 300"), params).fetchall()
        _KATLBL = {"mzda": "mzdy", "dan": "daň", "dan_mzda": "daň ze mzdy", "soc_poj": "sociální",
                   "zdrav_poj": "zdrav. poj.", "karta": "karta", "zak_pojisteni": "zák. pojištění",
                   "poplatek": "bank. poplatek", "vnitroskupina": "vnitroskupina", "opakovana": "opakovaná"}
        out = []
        for r in rows:
            met, rada, zak, kat = r[8], r[9], r[10], r[11]
            if zak:
                par = "zakázka " + zak
            elif rada:
                par = "doklad " + rada
            elif kat:
                par = _KATLBL.get(kat, kat)
            elif met:
                par = "platák" if met == "platak" else met
            else:
                par = ""
            out.append({"id": int(r[0]), "datum": r[1], "castka": float(r[2]) if r[2] is not None else 0.0,
                        "mena": r[3], "smer": r[4], "protiucet": r[5], "vs": r[6], "zprava": r[7],
                        "parovani": par, "naparovano": bool(met),
                        "firma": int(r[12]) if r[12] is not None else 1, "protistrana": r[13]})
        cnt = s.execute(_t("SELECT count(*) " + base), params).scalar()
        napar = s.execute(_t("SELECT count(*) " + base + (" AND " if conds else " WHERE ")
                             + "t.par_metoda IS NOT NULL"), params).scalar()
        posl = s.execute(_t("SELECT to_char(max(t.datum),'DD.MM.YYYY') " + base), params).scalar()
        return {"ok": True, "polozky": out, "posledni": posl, "total": int(cnt or 0),
                "naparovano": int(napar or 0), "shown": len(out)}
    finally:
        s.close()


@bank_router.get("/app/bank/vypis-detail")
def bank_vypis_detail(request: Request):
    """Detail jedné transakce — vše z raw (protistrana, valuty, VS/KS/SS, karta,
    kód transakce, zprávy) + syrové JSON. Marti 8.7.2026 („detail to jistí")."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        tid = int(request.query_params.get("id"))
    except Exception:
        return JSONResponse({"ok": False, "error": "Zadej id."}, status_code=400)
    s = _sess()
    try:
        r = s.execute(_t(
            "SELECT t.id, to_char(t.datum,'DD.MM.YYYY'), t.castka, COALESCE(NULLIF(t.mena,''),'CZK'), "
            "  COALESCE(t.smer,''), COALESCE(t.protiucet,''), COALESCE(t.vs,''), COALESCE(t.ks,''), "
            "  COALESCE(t.ss,''), COALESCE(t.zprava,''), COALESCE(t.stav_parovani,''), COALESCE(t.ext_id,''), "
            "  COALESCE(c.company_id,1), COALESCE(a.cislo_uctu,''), COALESCE(t.par_metoda,''), "
            "  COALESCE(t.par_doklad_rada,''), COALESCE(t.par_zakazka,''), COALESCE(t.par_kategorie,''), t.raw "
            "FROM tenant.bank_transaction_raw t "
            "LEFT JOIN tenant.bank_connection_account a ON a.id=t.account_id "
            "LEFT JOIN tenant.bank_connection c ON c.id=a.connection_id WHERE t.id=:id"), {"id": tid}).first()
        if not r:
            return JSONResponse({"ok": False, "error": "Transakce nenalezena."}, status_code=404)
        raw = r[18] or {}
        if isinstance(raw, str):
            try:
                raw = _json.loads(raw)
            except Exception:
                raw = {}
        det = ((raw.get("entryDetails", {}) or {}).get("transactionDetails", {}) or {})
        cp = ((det.get("relatedParties", {}) or {}).get("counterParty", {}) or {})
        acc = (cp.get("account", {}) or {})
        rem = (det.get("remittanceInformation", {}) or {})
        _met, _rada, _zak, _kat = r[14], r[15], r[16], r[17]
        _katlbl = {"mzda": "mzdy", "dan": "daň", "dan_mzda": "daň ze mzdy", "soc_poj": "sociální",
                   "zdrav_poj": "zdrav. poj.", "karta": "karta", "zak_pojisteni": "zák. pojištění",
                   "poplatek": "bank. poplatek", "vnitroskupina": "vnitroskupina", "opakovana": "opakovaná"}
        if _zak:
            _par = "zakázka " + _zak + (" (doklad " + _rada + ")" if _rada else "")
        elif _rada:
            _par = "doklad " + _rada
        elif _kat:
            _par = _katlbl.get(_kat, _kat)
        elif _met:
            _par = "platák" if _met == "platak" else _met
        else:
            _par = ""
        detail = {
            "id": int(r[0]), "datum": r[1], "castka": float(r[2]) if r[2] is not None else 0.0,
            "mena": r[3], "smer": r[4], "protiucet": r[5], "vs": r[6], "ks": r[7], "ss": r[8],
            "zprava": r[9], "stav": r[10], "ext_id": r[11],
            "firma": int(r[12]) if r[12] is not None else 1, "nas_ucet": r[13],
            "parovani": _par, "par_metoda": _met,
            "protistrana_nazev": cp.get("name") or "",
            "protistrana_ucet": acc.get("iban") or acc.get("accountNumber") or "",
            "value_date": (raw.get("valueDate") or "")[:10],
            "booking_date": (raw.get("bookingDate") or "")[:10],
            "card": det.get("paymentCardNumber") or "",
            "bank_code": ((raw.get("bankTransactionCode", {}) or {}).get("code") or ""),
            "unstructured": rem.get("unstructured") or "",
            "originator": rem.get("originatorMessage") or "",
            "raw_pretty": _json.dumps(raw, ensure_ascii=False, indent=2),
        }
        return {"ok": True, "detail": detail}
    finally:
        s.close()


@bank_router.post("/app/bank/payment/import-batch")
async def bank_import_batch(request: Request):
    """Nahraje dávku plateb (platák) do RB IB k PODPISU. NEPROVEDE platbu — člověk podepíše v bankovnictví.
    Body JSON: {conn_id, format, content?  |  gemini_ref?, validate:false}.
      format = SEPA-XML/DOM-XML/ABO-KPC/CFD/CFU/CFA/GEMINI-* (náš .p11/.f84 render = GEMINI-*).
      content = obsah dávky (text) — např. výstup scripts/rb/gemini_render.
      validate=true → jen ověří strukturu volání bez odeslání (žádné volání RB).
    Pojistky: parent/cockpit; platba se v bance jen připraví, podpis je LIDSKÝ krok."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    cid = body.get("conn_id")
    fmt = (body.get("format") or "").strip()
    content = body.get("content")
    batch_name = body.get("batch_name")
    combined = bool(body.get("combined"))
    validate = bool(body.get("validate"))
    if not cid or not fmt:
        return JSONResponse({"ok": False, "error": "Chybí conn_id nebo format."}, status_code=400)
    if fmt not in _RB_BATCH_FORMATS:
        return JSONResponse({"ok": False, "error": "Neznámý formát dávky: %s (povolené: %s)"
                             % (fmt, ", ".join(_RB_BATCH_FORMATS))}, status_code=400)
    if not content:
        return JSONResponse({"ok": False, "error": "Chybí obsah dávky (content)."}, status_code=400)
    # validate = suchý běh: neposílá do banky, jen potvrdí, že by volání proběhlo
    if validate:
        b = content.encode("cp1250", "replace") if isinstance(content, str) else content
        return {"ok": True, "validate": True, "format": fmt, "combined": combined, "bytes": len(b),
                "note": "Suchý běh — do banky se NIC neodeslalo. Reálný import spusť bez validate."}
    s = _sess()
    try:
        bundle = _bundle_for(s, cid)
        if not bundle:
            return JSONResponse({"ok": False, "error": "Napojení nemá uložený certifikát."}, status_code=400)
        try:
            ok, res = _rb_import_batch(bundle, content, fmt, batch_name=batch_name, combined=combined)
        except Exception as exc:
            _log(s, cid, None, "import_payment_batch", "event", "user:%s" % uid, "ERROR:%s" % type(exc).__name__,
                 {"format": fmt, "err": str(exc)[:200]})
            s.commit()
            return JSONResponse({"ok": False, "error": "RB import selhal: %s: %s"
                                 % (type(exc).__name__, str(exc)[:200])}, status_code=502)
        _log(s, cid, None, "import_payment_batch", "event", "user:%s" % uid,
             ("OK:%s" % res.get("batchFileId")) if ok else ("HTTP:%s:%s" % (res.get("http"), res.get("error"))),
             {"format": fmt, "batchFileId": res.get("batchFileId"), "error": res.get("error")})
        s.commit()
        if not ok:
            return JSONResponse({"ok": False, "error": "RB odmítla dávku (HTTP %s: %s)"
                                 % (res.get("http"), res.get("error") or "?"),
                                 "detail": res.get("raw")}, status_code=502)
        return {"ok": True, "batchFileId": res.get("batchFileId"),
                "note": "Dávka nahrána do internetového bankovnictví jako koncept. Platbu je nutné PODEPSAT v bance (lidský krok)."}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/bank/payment/batch-status")
async def bank_batch_status(request: Request):
    """Stav importované dávky v IB: ?conn_id=&batch_file_id=  → DRAFT/FOR_SIGN/VERIFIED/PASSED."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    cid = request.query_params.get("conn_id")
    bfid = request.query_params.get("batch_file_id")
    if not cid or not bfid:
        return JSONResponse({"ok": False, "error": "Chybí conn_id nebo batch_file_id."}, status_code=400)
    s = _sess()
    try:
        bundle = _bundle_for(s, int(cid))
        if not bundle:
            return JSONResponse({"ok": False, "error": "Napojení nemá uložený certifikát."}, status_code=400)
        ok, res = _rb_batch_status(bundle, bfid)
        return {"ok": ok, "http": res.get("http"), "batchFileStatus": res.get("batchFileStatus"),
                "errorCode": res.get("errorCode"), "errorDescription": res.get("errorDescription"),
                "polozky": res.get("polozky")}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}, status_code=500)
    finally:
        s.close()


# ════════════════════════════════════════════════════════════════════
# PÁROVACÍ ENGINE (Marti 24.6.2026): banka ↔ objednávková páteř ↔ zakázka.
# Multi-key, set-based (indexy ltrim(cislo)/ltrim(vs)). Idempotentní (reset+refill).
# Klíče v pořadí: A) opakovaná (účet+KS→predpis), B) naše číslo dokladu (VS→doklad,
# řada určí typ: 600 FV, 601 vnitroskupina, 920+ přijaté objednávky → zakázka).
# Model: docs/parovani_banka_objednavky_model.md
# ════════════════════════════════════════════════════════════════════
_PAR_RADA_PRIO = [
    (["600"], "fv_zakaznik"),
    (["601"], "vnitroskupina"),
    (["920", "910", "900", "940", "950"], "prijata_objednavka"),
    (["800", "801"], "vydana_objednavka"),
    (["630", "640", "500", "501"], "ostatni_doklad"),
]


def parovat_all(s):
    """Párovací engine nad bank_transaction_raw (idempotentní full re-run). Naplní
    par_metoda/rada/zakazka/kategorie/doklad. Sdílí endpoint i automatický sync. Vrací souhrn.
    Claude 8.7.2026 (vytaženo z bank_parovat, aby běželo i po syncu)."""
    if True:
        # reset (idempotentní re-run)
        s.execute(_t("UPDATE tenant.bank_transaction_raw SET par_metoda=NULL, par_doklad_rada=NULL, "
                     "par_zakazka=NULL, par_kategorie=NULL, par_doklad_id=NULL"))
        # A) opakované platby (účet + KS → bank_predpis)
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t SET par_metoda='opakovana', par_at=now(), "
            "par_kategorie=(SELECT p.kategorie FROM tenant.bank_predpis p WHERE p.aktivni "
            "  AND (p.match_ucet IS NULL OR t.protiucet LIKE p.match_ucet) "
            "  AND (p.match_ks IS NULL OR t.ks=p.match_ks) "
            "  AND (p.match_ucet IS NOT NULL OR p.match_ks IS NOT NULL) ORDER BY p.priorita LIMIT 1) "
            "WHERE t.par_metoda IS NULL AND EXISTS (SELECT 1 FROM tenant.bank_predpis p WHERE p.aktivni "
            "  AND (p.match_ucet IS NULL OR t.protiucet LIKE p.match_ucet) "
            "  AND (p.match_ks IS NULL OR t.ks=p.match_ks) "
            "  AND (p.match_ucet IS NOT NULL OR p.match_ks IS NOT NULL))"))
        # B) naše číslo dokladu (VS → ec_doklad_zbozi.cislo), po prioritě řad
        for radas, _lbl in _PAR_RADA_PRIO:
            s.execute(_t(
                "UPDATE tenant.bank_transaction_raw t "
                "SET par_metoda='doklad', par_doklad_rada=m.rada, par_doklad_id=m.id, "
                "    par_zakazka=NULLIF(m.cislo_zakazky,''), par_at=now() "
                "FROM tenant.ec_doklad_zbozi m "
                "WHERE t.par_metoda IS NULL AND t.vs IS NOT NULL AND t.vs<>'' "
                "  AND ltrim(m.cislo,'0')=ltrim(t.vs,'0') AND m.rada = ANY(:radas)"),
                {"radas": radas})
        # C) odchozí: zpráva "RRRNNNNNN" = řada + číslo NAŠÍ faktury → objednávka → zakázka
        #    (platbu generujeme ze systému, do zprávy dáme referenci na fakturu, kterou platíme)
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t "
            "SET par_metoda='doklad_zprava', par_doklad_rada=d.rada, par_doklad_id=d.id, "
            "    par_zakazka=NULLIF(d.cislo_zakazky,''), par_at=now() "
            "FROM tenant.ec_doklad_zbozi d "
            "WHERE t.par_metoda IS NULL AND t.zprava ~ '^\\d{4}' "
            "  AND d.rada = (regexp_match(t.zprava, '^(\\d{3})0*(\\d+)'))[1] "
            "  AND ltrim(d.cislo,'0') = (regexp_match(t.zprava, '^(\\d{3})0*(\\d+)'))[2]"))
        # C2) NÁŠ PLATÁK — odchozí platbu, kterou jsme generovali, ZNÁME z platak_uhrada_lock.
        #     Match: částka+měna + (supplier VS z locku shoduje t.vs  NEBO  „ID:{id_fak}" ve zprávě
        #     = to co jsme dali do .f84). Zakázku doplní ec_doklad_zbozi (EC); u ES (mirror nemá)
        #     zůstane jen 'platak' — ale platba je spárovaná (vazbu na doklad známe). Claude 8.7.
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t "
            "SET par_metoda='platak', par_doklad_id=l.id_fak, par_doklad_rada=d.rada, "
            "    par_zakazka=NULLIF(d.cislo_zakazky,''), par_at=now() "
            "FROM tenant.platak_uhrada_lock l "
            "LEFT JOIN tenant.ec_doklad_zbozi d ON d.id = l.id_fak "
            "WHERE t.par_metoda IS NULL AND t.smer='out' "
            "  AND abs(abs(t.castka) - l.castka) < 0.5 "
            "  AND COALESCE(NULLIF(t.mena,''),'CZK') = COALESCE(l.mena,'CZK') "
            "  AND ( (COALESCE(t.vs,'')<>'' "
            "         AND regexp_replace(COALESCE(l.doklad_vs,''),'\\D','','g')<>'' "
            "         AND ltrim(t.vs,'0') = ltrim(regexp_replace(l.doklad_vs,'\\D','','g'),'0')) "
            "       OR t.zprava ~ ('ID' || chr(58) || '0*' || l.id_fak || '([^0-9]|$)') )"))
        # C3) NÁŠ DOKLAD KDEKOLIV ve zprávě (ne jen na začátku). Helios dává do zprávy
        #     „ID:{platak}:{vs} {NÁŠ doklad}" — vytáhni token s NAŠÍ řadou (500/501/530/531/
        #     540/541/600/601/630/640) odkudkoliv a spáruj na ec_doklad_zbozi. Marti 8.7.: „Helios
        #     paruje pres ID, jen jsme si ho nedotahli."
        _rgx = "(500|501|530|531|540|541|600|601|630|640)"
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t "
            "SET par_metoda='doklad_zprava', par_doklad_rada=d.rada, par_doklad_id=d.id, "
            "    par_zakazka=NULLIF(d.cislo_zakazky,''), par_at=now() "
            "FROM tenant.ec_doklad_zbozi d "
            "WHERE t.par_metoda IS NULL "
            "  AND t.zprava ~ ('(^|[^0-9])' || :rgx || '[0-9]{5,7}([^0-9]|$)') "
            "  AND d.rada = (regexp_match(t.zprava, '(?:^|[^0-9])' || :rgx || '0*([0-9]+)(?:[^0-9]|$)'))[1] "
            "  AND ltrim(d.cislo,'0') = (regexp_match(t.zprava, '(?:^|[^0-9])' || :rgx || '0*([0-9]+)(?:[^0-9]|$)'))[2]"),
            {"rgx": _rgx})
        # D) opakované přes text/účet — mzdy/pojištění/daně co mají KS/účet varianty mimo bank_predpis
        #    (Marti 24.6.: Helios mzdy generuje 'Výplata na účet' dávky; pojišťovny/ČSSZ/FÚ dle účtu)
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t SET par_metoda='opakovana', par_at=now(), "
            "par_kategorie = CASE "
            "  WHEN zprava ILIKE '%%Výplata na účet%%' THEN 'mzda' "
            "  WHEN protiucet LIKE '%%77627311' OR zprava ILIKE '%%daň%%' THEN 'dan' "
            "  WHEN protiucet LIKE '%%7928311' OR zprava ILIKE '%%Soc. pojištění%%' THEN 'soc_poj' "
            "  WHEN zprava ILIKE '%%pojišť%%' THEN 'zdrav_poj' ELSE 'opakovana' END "
            "WHERE par_metoda IS NULL AND (zprava ILIKE '%%Výplata na účet%%' OR zprava ILIKE '%%pojišť%%' "
            "  OR zprava ILIKE '%%Soc. pojištění%%' OR protiucet LIKE '%%7928311' OR zprava ILIKE '%%daň%%' "
            "  OR protiucet LIKE '%%77627311')"))
        # E) platby kartou (KS 1178: Google Ads, Makro, Alza…) + zákonné pojištění (diakritika)
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t SET par_metoda='opakovana', par_at=now(), "
            "par_kategorie = CASE WHEN ltrim(ks,'0')='1178' THEN 'karta' "
            "  WHEN zprava ILIKE '%%pojištění%%' THEN 'zak_pojisteni' ELSE par_kategorie END "
            "WHERE par_metoda IS NULL AND (ltrim(ks,'0')='1178' OR zprava ILIKE '%%pojištění%%')"))
        # F) vnitroskupina — protiúčet je jeden z NAŠICH účtů (převod EC↔ES / mezi účty). Claude 8.7.
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t SET par_metoda='vnitroskupina', "
            "  par_kategorie='vnitroskupina', par_at=now() "
            "FROM (SELECT DISTINCT cislo_uctu FROM tenant.bank_connection_account "
            "      WHERE COALESCE(aktivni,true) AND COALESCE(cislo_uctu,'')<>'') o "
            "WHERE t.par_metoda IS NULL AND t.protiucet LIKE '%%'||o.cislo_uctu"))
        # G) bankovní poplatky / souhrnné položky / úroky. Claude 8.7.
        s.execute(_t(
            "UPDATE tenant.bank_transaction_raw t SET par_metoda='opakovana', "
            "  par_kategorie='poplatek', par_at=now() "
            "WHERE par_metoda IS NULL AND (zprava ILIKE '%%Souhrnná položka%%' "
            "  OR zprava ILIKE '%%poplat%%' OR zprava ILIKE '%%úrok%%' OR zprava ILIKE '%%Cena za%%')"))
        s.commit()
        # souhrn
        celkem = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw")).scalar()
        by_met = [dict(r) for r in s.execute(_t(
            "SELECT COALESCE(par_metoda,'(nenaparovano)') AS metoda, COALESCE(par_doklad_rada,'') AS rada, "
            "count(*) AS pocet, round(sum(abs(castka))) AS objem "
            "FROM tenant.bank_transaction_raw GROUP BY 1,2 ORDER BY pocet DESC")).mappings().all()]
        naparovano = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw WHERE par_metoda IS NOT NULL")).scalar()
        se_zak = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw WHERE par_zakazka IS NOT NULL")).scalar()
        return {"celkem": int(celkem or 0), "naparovano": int(naparovano or 0),
                "se_zakazkou": int(se_zak or 0), "rozpad": by_met}


@bank_router.post("/app/bank/parovat")
def bank_parovat(request: Request):
    """Spustí párovací engine nad bank_transaction_raw. Parent-only."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        out = parovat_all(s)
        return {"ok": True, **out}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# ── Systém pokladen + kartových účtů (zrcadlo Helios TabDruhPokladen) ──
def _mcp_rows(sql: str, db_name: str):
    """Read přes EUROSOFT MCP. Vrátí list dictů (lower-case klíče).

    Odolné vůči zaseknuté SSE session: když MCP vrátí prázdnou/nevalidní
    odpověď (typicky 'JSONDecodeError: line 1 column 1' = stará mrtvá session,
    která se sama neobnovuje), vynutí reconnect klienta a zkusí ještě jednou.
    (Claude-26 16.7.2026 — bez toho padal sync pokladen/dokladů na prázdno.)"""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupné")

    _last = {"raw": None}

    def _call_parse():
        raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                                 {"sql": sql, "db_name": db_name}, conversation_id=None)
        _last["raw"] = raw
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return None
            return _json.loads(raw)
        return raw

    r = None
    for _attempt in (1, 2):
        try:
            r = _call_parse()
        except Exception:
            r = None
        if r is not None:
            break
        try:
            mcp._reconnect()
        except Exception:
            pass
    if r is None:
        _rawtxt = _last["raw"]
        _rawtxt = (str(_rawtxt)[:200] if _rawtxt is not None else "None")
        raise RuntimeError("MCP dotaz selhal (db=%s) — surová odpoved=%r" % (db_name, _rawtxt))
    rows = []
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error"))[:200])
        for k in ("rows", "data", "result", "records"):
            if isinstance(r.get(k), list):
                rows = r[k]
                break
    elif isinstance(r, list):
        rows = r
    return [{(k or "").lower(): v for k, v in d.items()} for d in rows]


def _sync_pokladny_firma(s, db_name: str, firma: str) -> int:
    sql = ("SELECT Cislo, Nazev, Mena, UcetMD, UcetDAL, Sbornik, CisloZakazky "
           "FROM dbo.TabDruhPokladen")
    rows = _mcp_rows(sql, db_name)
    n = 0
    for d in rows:
        cislo = (d.get("cislo") or "").strip()
        if not cislo:
            continue
        nazev = (d.get("nazev") or "").strip()
        mena = (d.get("mena") or "").strip() or "CZK"
        typ = "kartovy_ucet" if "kartov" in nazev.lower() else "pokladna"
        s.execute(_t(
            "INSERT INTO tenant.ucet_pokladna (firma,cislo,nazev,mena,typ,ucet_md,ucet_dal,sbornik,cislo_zakazky,synced_at) "
            "VALUES (:f,:c,:n,:m,:typ,:md,:dal,:sb,:cz,now()) "
            "ON CONFLICT (firma,cislo) DO UPDATE SET nazev=EXCLUDED.nazev, mena=EXCLUDED.mena, "
            "typ=EXCLUDED.typ, ucet_md=EXCLUDED.ucet_md, ucet_dal=EXCLUDED.ucet_dal, "
            "sbornik=EXCLUDED.sbornik, cislo_zakazky=EXCLUDED.cislo_zakazky, synced_at=now()"),
            {"f": firma, "c": cislo, "n": nazev, "m": mena, "typ": typ,
             "md": (d.get("ucetmd") or "").strip() or None, "dal": (d.get("ucetdal") or "").strip() or None,
             "sb": (d.get("sbornik") or "").strip() or None, "cz": (d.get("cislozakazky") or "").strip() or None})
        n += 1
    return n


@bank_router.post("/app/bank/sync-pokladny")
async def bank_sync_pokladny(request: Request):
    """Zrcadlí Helios TabDruhPokladen (EC=DB_EC, ES=DB_IS) → tenant.ucet_pokladna."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        ec = _sync_pokladny_firma(s, "DB_EC", "EC")
        es = _sync_pokladny_firma(s, "DB_IS", "ES")
        s.commit()
        return {"ok": True, "ec": ec, "es": es}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/bank/pokladny")
async def bank_pokladny(request: Request):
    """Seznam pokladen/kartových účtů + registr karet (pro editor)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        pok = [dict(r) for r in s.execute(_t(
            "SELECT id,firma,cislo,nazev,mena,typ,ucet_md,ucet_dal,sbornik,cislo_zakazky,aktivni "
            "FROM tenant.ucet_pokladna ORDER BY firma,cislo")).mappings().all()]
        karty = [dict(r) for r in s.execute(_t(
            "SELECT c.id,c.masked_pan,c.nazev,c.drzitel,c.firma,c.pokladna_cislo,c.stredisko,c.pozn,c.aktivni, "
            "(SELECT count(*) FROM tenant.bank_transaction_raw t WHERE ltrim(t.ks,'0')='1178' "
            "  AND t.raw->'entryDetails'->'transactionDetails'->>'paymentCardNumber'=c.masked_pan) AS pocet_plateb "
            "FROM tenant.bank_card c ORDER BY c.firma,c.masked_pan")).mappings().all()]
        kartove_ucty = [p for p in pok if p["typ"] == "kartovy_ucet"]
        pokl_sync_at = s.execute(_t(
            "SELECT to_char(max(synced_at) AT TIME ZONE 'Europe/Prague','DD.MM.YYYY HH24:MI') "
            "FROM tenant.ec_doklad_pokladna")).scalar()
        return {"ok": True, "pokladny": pok, "karty": karty, "kartove_ucty": kartove_ucty,
                "pokl_sync_at": pokl_sync_at}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/bank/card/{card_id}")
async def bank_card_update(card_id: int, request: Request):
    """Editace karty (držitel/středisko/kartový účet/název/aktivní) — pro Peťu."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    sets, params = [], {"id": card_id}
    for col in ("nazev", "drzitel", "stredisko", "pokladna_cislo"):
        if col in body:
            sets.append("%s=:%s" % (col, col))
            params[col] = (str(body[col]).strip() or None) if body[col] is not None else None
    if "aktivni" in body:
        sets.append("aktivni=:aktivni")
        params["aktivni"] = bool(body["aktivni"])
    if not sets:
        return JSONResponse({"ok": False, "error": "nic ke změně"}, status_code=400)
    s = _sess()
    try:
        s.execute(_t("UPDATE tenant.bank_card SET %s WHERE id=:id" % ",".join(sets)), params)
        s.commit()
        return {"ok": True}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# ── Zrcadlo jednotlivých pokladních dokladů (TabPokladna + TabPolozkyPokl) — Claude-26 15.7.2026 ──
def _sync_pokl_doklady_rada(s, db_name, firma, rada, rok):
    """Zrcadlí doklady jedné pokladny (RadaDokladuPokl) za daný rok z Heliosu do
    tenant.ec_doklad_pokladna(+_polozka). Idempotentní (ON CONFLICT). Vrací (n_hlavicek, n_polozek)."""
    rada = str(rada).strip()
    rok = int(rok)
    sql_h = (
        "SELECT ID, RadaDokladuPokl, PoradoveCislo, TypDokladu, StavDokladu, Popis, "
        "CAST(Poznamka AS nvarchar(4000)) AS Poznamka, Prilohy, "
        "CONVERT(varchar(10), DatPripad, 23) AS DatPripad, "
        "CONVERT(varchar(10), DatUctovani, 23) AS DatUctovani, "
        "CONVERT(varchar(10), DUZP, 23) AS DUZP, "
        "CONVERT(varchar(19), DatPorizeno, 126) AS DatPorizeno, "
        "CONVERT(varchar(10), DatPorizeni, 23) AS DatPorizeni, "
        "CisloOrg, CisloZam, ParovaciZnak, CisloZakazky, CisloNakladovyOkruh, "
        "Mena, CastkaMena, StavPokladny, Uhrada, SaldoDokladu, CastkaD, Autor, "
        "ext._BVPolPokl AS BVPolPokl "
        "FROM dbo.TabPokladna "
        "LEFT JOIN dbo.TabPokladna_EXT ext ON ext.ID = dbo.TabPokladna.ID "
        "WHERE RadaDokladuPokl = '" + rada + "' AND (YEAR(DatPripad) = " + str(rok) + " OR DatPripad IS NULL)"
    )
    nh = 0
    for d in _mcp_rows(sql_h, db_name):
        s.execute(_t(
            "INSERT INTO tenant.ec_doklad_pokladna "
            "(tenant_id,firma,src_id,rada_pokladny,poradove_cislo,typ_dokladu,stav_dokladu,popis,poznamka,"
            "prilohy,dat_pripad,dat_uctovani,duzp,dat_porizeno,dat_porizeni,cislo_org,cislo_zam,parovaci_znak,zakazka,"
            "naklad_okruh,mena,castka_mena,stav_pokladny,uhrada,saldo_dokladu,castka_dokladu,bv_seznam,autor,synced_at) VALUES "
            "(:tn,:f,:sid,:rada,:pc,:typ,:stav,:popis,:pozn,:pril,"
            "NULLIF(:dprip,'')::date,NULLIF(:duct,'')::date,NULLIF(:duzp,'')::date,NULLIF(:dpor,'')::timestamp,NULLIF(:dporiz,'')::date,"
            ":org,:zam,:paro,:zak,:nok,:mena,:castka,:stavp,:uhr,:saldo,:castkad,:bvsez,:autor,now()) "
            "ON CONFLICT (firma,src_id) DO UPDATE SET rada_pokladny=EXCLUDED.rada_pokladny,"
            "poradove_cislo=EXCLUDED.poradove_cislo,typ_dokladu=EXCLUDED.typ_dokladu,stav_dokladu=EXCLUDED.stav_dokladu,"
            "popis=EXCLUDED.popis,poznamka=EXCLUDED.poznamka,prilohy=EXCLUDED.prilohy,dat_pripad=EXCLUDED.dat_pripad,"
            "dat_uctovani=EXCLUDED.dat_uctovani,duzp=EXCLUDED.duzp,dat_porizeno=EXCLUDED.dat_porizeno,dat_porizeni=EXCLUDED.dat_porizeni,"
            "cislo_org=EXCLUDED.cislo_org,cislo_zam=EXCLUDED.cislo_zam,parovaci_znak=EXCLUDED.parovaci_znak,"
            "zakazka=EXCLUDED.zakazka,naklad_okruh=EXCLUDED.naklad_okruh,mena=EXCLUDED.mena,"
            "castka_mena=EXCLUDED.castka_mena,stav_pokladny=EXCLUDED.stav_pokladny,"
            "uhrada=EXCLUDED.uhrada,saldo_dokladu=EXCLUDED.saldo_dokladu,castka_dokladu=EXCLUDED.castka_dokladu,"
            "bv_seznam=EXCLUDED.bv_seznam,autor=EXCLUDED.autor,synced_at=now()"),
            {"tn": _TENANT, "f": firma, "sid": d.get("id"),
             "rada": (d.get("radadokladupokl") or "").strip() or None,
             "pc": d.get("poradovecislo"), "typ": d.get("typdokladu"), "stav": d.get("stavdokladu"),
             "popis": (d.get("popis") or "").strip() or None, "pozn": (d.get("poznamka") or "").strip() or None,
             "pril": d.get("prilohy"), "dprip": d.get("datpripad") or "", "duct": d.get("datuctovani") or "",
             "duzp": d.get("duzp") or "", "dpor": d.get("datporizeno") or "", "dporiz": d.get("datporizeni") or "",
             "org": d.get("cisloorg"), "zam": d.get("cislozam"),
             "paro": (d.get("parovaciznak") or "").strip() or None, "zak": (d.get("cislozakazky") or "").strip() or None,
             "nok": (d.get("cislonakladovyokruh") or "").strip() or None, "mena": (d.get("mena") or "").strip() or None,
             "castka": d.get("castkamena"), "stavp": d.get("stavpokladny"),
             "uhr": d.get("uhrada"), "saldo": d.get("saldodokladu"), "castkad": d.get("castkad"),
             "bvsez": ((d.get("bvpolpokl") or "").strip().rstrip(",").strip() or None),
             "autor": (d.get("autor") or "").strip() or None})
        nh += 1
    sql_p = (
        "SELECT p.ID, p.IDPokladna, p.TypPolozky, p.SazbaDPH, p.ZakladDPH, p.CastkaDPH, p.CelkemDPH, "
        "p.CastkaMena, p.Mena, CAST(p.Popis AS nvarchar(4000)) AS Popis, p.CisloUcet, p.Utvar, p.CisloZakazky "
        "FROM dbo.TabPolozkyPokl p JOIN dbo.TabPokladna h ON h.ID = p.IDPokladna "
        "WHERE h.RadaDokladuPokl = '" + rada + "' AND (YEAR(h.DatPripad) = " + str(rok) + " OR h.DatPripad IS NULL)"
    )
    npoz = 0
    for d in _mcp_rows(sql_p, db_name):
        s.execute(_t(
            "INSERT INTO tenant.ec_doklad_pokladna_polozka "
            "(tenant_id,firma,src_id,doklad_src_id,rada_pokladny,typ_polozky,ucet,utvar,zakazka,"
            "sazba_dph,zaklad_dph,castka_dph,celkem_dph,castka_mena,mena,popis,synced_at) VALUES "
            "(:tn,:f,:sid,:dsid,:rada,:typ,:ucet,:utvar,:zak,:saz,:zdph,:cdph,:cel,:castka,:mena,:popis,now()) "
            "ON CONFLICT (firma,src_id) DO UPDATE SET doklad_src_id=EXCLUDED.doklad_src_id,"
            "rada_pokladny=EXCLUDED.rada_pokladny,typ_polozky=EXCLUDED.typ_polozky,ucet=EXCLUDED.ucet,"
            "utvar=EXCLUDED.utvar,zakazka=EXCLUDED.zakazka,sazba_dph=EXCLUDED.sazba_dph,zaklad_dph=EXCLUDED.zaklad_dph,"
            "castka_dph=EXCLUDED.castka_dph,celkem_dph=EXCLUDED.celkem_dph,castka_mena=EXCLUDED.castka_mena,"
            "mena=EXCLUDED.mena,popis=EXCLUDED.popis,synced_at=now()"),
            {"tn": _TENANT, "f": firma, "sid": d.get("id"), "dsid": d.get("idpokladna"), "rada": rada,
             "typ": d.get("typpolozky"), "ucet": (d.get("cisloucet") or "").strip() or None,
             "utvar": (d.get("utvar") or "").strip() or None, "zak": (d.get("cislozakazky") or "").strip() or None,
             "saz": d.get("sazbadph"), "zdph": d.get("zakladdph"), "cdph": d.get("castkadph"),
             "cel": d.get("celkemdph"), "castka": d.get("castkamena"), "mena": (d.get("mena") or "").strip() or None,
             "popis": (d.get("popis") or "").strip() or None})
        npoz += 1
    return nh, npoz


@bank_router.post("/app/bank/sync-pokl-doklady")
async def bank_sync_pokl_doklady(request: Request):
    """Zrcadlí doklady jedné pokladny za rok (?rada=075&rok=2026). Parent-only."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    import datetime as _dtx
    rada = (request.query_params.get("rada") or "").strip()
    rok = (request.query_params.get("rok") or "").strip()
    if not rada:
        return JSONResponse({"ok": False, "error": "chybí rada pokladny"}, status_code=400)
    rok_i = int(rok) if rok.isdigit() else _dtx.date.today().year
    s = _sess()
    try:
        nh, npoz = _sync_pokl_doklady_rada(s, "DB_EC", "EC", rada, rok_i)
        s.commit()
        return {"ok": True, "hlavicky": nh, "polozky": npoz, "rada": rada, "rok": rok_i}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


def _sync_pokl_doklady_all(s, rok):
    """Zrcadlí doklady VŠECH pokladen (z ucet_pokladna) za daný rok. Vrací (n_hlavicek, n_polozek, n_pokladen)."""
    radas = [r[0] for r in s.execute(_t(
        "SELECT DISTINCT cislo FROM tenant.ucet_pokladna WHERE cislo IS NOT NULL ORDER BY cislo")).all()]
    th = tp = 0
    for rada in radas:
        nh, npoz = _sync_pokl_doklady_rada(s, "DB_EC", "EC", rada, rok)
        th += nh
        tp += npoz
    return th, tp, len(radas)


@bank_router.post("/app/bank/sync-pokl-doklady-all")
async def bank_sync_pokl_doklady_all(request: Request):
    """Jedním vrzem: obnoví seznam pokladen (nové naskočí) + zrcadlí doklady všech pokladen za rok. Parent-only."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    import datetime as _dtx
    rok = (request.query_params.get("rok") or "").strip()
    rok_i = int(rok) if rok.isdigit() else _dtx.date.today().year
    s = _sess()
    try:
        # 1) obnovit číselník pokladen (aby nové pokladny naskočily samy).
        #    Best-effort per DB — výpadek/nedostupnost jedné firmy NEsmí zabít
        #    natažení dokladů. (MCP přijímá jen DB_EC / DB_ST; ES = DB_ST, dřív DB_IS.)
        seznam = 0
        seznam_chyby = []
        for _db, _f in (("DB_EC", "EC"), ("DB_ST", "ES")):
            try:
                seznam += _sync_pokladny_firma(s, _db, _f)
            except Exception as _e:
                seznam_chyby.append("%s(%s): %s" % (_f, _db, str(_e)[:100]))
        # 2) doklady všech pokladen za rok (zdroj DB_EC)
        th, tp, npok = _sync_pokl_doklady_all(s, rok_i)
        s.commit()
        return {"ok": True, "pokladen_seznam": seznam,
                "seznam_chyby": (seznam_chyby or None),
                "hlavicky": th, "polozky": tp, "pokladen": npok, "rok": rok_i}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/bank/pokl-doklady")
async def bank_pokl_doklady(request: Request):
    """Doklady jedné pokladny (?rada=075&rok=2026) z našeho zrcadla. Parent-only."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    rada = (request.query_params.get("rada") or "").strip()
    rok = (request.query_params.get("rok") or "").strip()
    if not rada:
        return JSONResponse({"ok": False, "error": "chybí rada pokladny"}, status_code=400)
    s = _sess()
    try:
        where = "firma='EC' AND rada_pokladny=:rada"
        params = {"rada": rada}
        if rok.isdigit():
            where += " AND (EXTRACT(YEAR FROM dat_pripad)=:rok OR dat_pripad IS NULL)"
            params["rok"] = int(rok)
        rows = [dict(r) for r in s.execute(_t(
            "SELECT d.src_id, d.poradove_cislo, d.typ_dokladu, d.popis, d.prilohy, "
            "to_char(d.dat_porizeni,'DD.MM.YYYY') AS dat_porizeni, "
            "to_char(d.dat_pripad,'DD.MM.YYYY') AS dat_pripad, "
            "to_char(d.dat_uctovani,'DD.MM.YYYY') AS dat_uctovani, "
            "to_char(d.dat_porizeno,'DD.MM.YYYY HH24:MI') AS dat_porizeno, "
            "d.uhrada, d.saldo_dokladu, d.castka_dokladu, d.castka_mena, d.stav_pokladny, d.mena, "
            "d.zakazka, d.naklad_okruh, d.parovaci_znak, d.cislo_org, d.autor, d.poznamka, d.bv_seznam, "
            "(SELECT max(p.utvar) FROM tenant.ec_doklad_pokladna_polozka p "
            " WHERE p.firma='EC' AND p.doklad_src_id=d.src_id AND p.utvar IS NOT NULL) AS utvar, "
            "(SELECT count(*) FROM tenant.ec_doklad_pokladna_polozka p "
            " WHERE p.firma='EC' AND p.doklad_src_id=d.src_id) AS pocet_polozek "
            "FROM tenant.ec_doklad_pokladna d WHERE " + where + " "
            "ORDER BY d.poradove_cislo DESC"), params).mappings().all()]
        for r in rows:
            for k in ("uhrada", "saldo_dokladu", "castka_dokladu", "castka_mena", "stav_pokladny"):
                if r.get(k) is not None:
                    r[k] = float(r[k])
        syncat = s.execute(_t(
            "SELECT to_char(max(synced_at) AT TIME ZONE 'Europe/Prague','DD.MM.YYYY HH24:MI') "
            "FROM tenant.ec_doklad_pokladna WHERE firma='EC' AND rada_pokladny=:rada"), {"rada": rada}).scalar()
        roky = [int(x[0]) for x in s.execute(_t(
            "SELECT DISTINCT EXTRACT(YEAR FROM dat_pripad)::int AS r "
            "FROM tenant.ec_doklad_pokladna WHERE firma='EC' AND rada_pokladny=:rada AND dat_pripad IS NOT NULL "
            "ORDER BY r DESC"), {"rada": rada}).all()]
        return {"ok": True, "doklady": rows, "sync_at": syncat, "roky": roky, "rada": rada, "rok": rok}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# ── Posting engine: párování → živý deník (actor=automat, jistota z předkontace) ──
@bank_router.post("/app/uctovani/bank-post")
async def uctovani_bank_post(request: Request):
    """Promění napárované bankovní transakce na zápisy v tenant.ucetni_denik.
    Actor = automat (deterministický), jistota z bank_predkontace. Idempotentní
    (zdroj='bank' + zdroj_id). Jen CZK; EUR čeká na kurz. ?dry=1 = náhled bez zápisu."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    dry = (request.query_params.get("dry") or "") in ("1", "true", "yes")
    s = _sess()
    try:
        rows = s.execute(_t(
            "SELECT t.id, t.datum, t.ext_id, t.castka, t.mena, t.zprava, t.par_kategorie, t.par_metoda, t.par_zakazka, "
            "COALESCE(pk.ucet_md, pr.ucet_md, pm.ucet_md) AS ucet_md, COALESCE(pk.ucet_dal, pr.ucet_dal, pm.ucet_dal) AS ucet_dal, "
            "COALESCE(pk.base_jistota, pr.base_jistota, pm.base_jistota) AS jistota, COALESCE(pk.klic, pr.klic, pm.klic) AS pravidlo "
            "FROM tenant.bank_transaction_raw t "
            "LEFT JOIN tenant.bank_predkontace pk ON pk.tenant_id=:tn AND pk.typ_klice='kategorie' AND pk.klic=t.par_kategorie AND pk.aktivni AND (pk.smer IS NULL OR pk.smer=t.smer) "
            "LEFT JOIN tenant.bank_predkontace pr ON pr.tenant_id=:tn AND pr.typ_klice='rada' AND pr.klic=t.par_doklad_rada AND pr.aktivni AND (pr.smer IS NULL OR pr.smer=t.smer) "
            "LEFT JOIN tenant.bank_predkontace pm ON pm.tenant_id=:tn AND pm.typ_klice='metoda' AND pm.klic=t.par_metoda AND pm.aktivni AND (pm.smer IS NULL OR pm.smer=t.smer) "
            "WHERE t.par_metoda IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM tenant.ucetni_denik d WHERE d.zdroj='bank' AND CAST(d.zdroj_id AS text)=CAST(t.id AS text))"),
            {"tn": _TENANT}).mappings().all()

        souhrn = {"kandidatu": len(rows), "zapsano": 0, "bez_pravidla": 0, "eur_ceka": 0,
                  "jistota_vysoka": 0, "jistota_stredni": 0, "jistota_nizka": 0}
        for r in rows:
            if not r["ucet_md"]:
                souhrn["bez_pravidla"] += 1
                continue
            mena = (r["mena"] or "CZK").upper()
            if mena != "CZK":
                souhrn["eur_ceka"] += 1
                continue
            j = float(r["jistota"] or 0)
            zak = r["par_zakazka"]
            jzdroj = "predkontace:%s" % (r["pravidlo"] or "")
            if zak:
                # Celý řetězec doklad → (schválená) objednávka → zakázka rozpleten → bonus jistoty
                j = min(99.0, j + 10.0)
                jzdroj += "+zakazka:%s" % zak
            if j >= 90:
                souhrn["jistota_vysoka"] += 1
            elif j >= 70:
                souhrn["jistota_stredni"] += 1
            else:
                souhrn["jistota_nizka"] += 1
            if not dry:
                popis = ("Banka: %s" % (r["pravidlo"] or "")) + ((" zak %s" % zak) if zak else "") + ((" — " + (r["zprava"] or "")[:70]) if r["zprava"] else "")
                s.execute(_t(
                    "INSERT INTO tenant.ucetni_denik "
                    "(tenant_id, datum, doklad, ucet_md, ucet_dal, castka, mena, popis, kategorie, zdroj, zdroj_id, "
                    " actor_type, actor_id, jistota, jistota_zdroj, review_stav, created_at) "
                    "VALUES (:tn,:datum,:doklad,:md,:dal,:castka,'CZK',:popis,:kat,'bank',:zid,"
                    " 'automat','automat:bank_v1',:jist,:jzdroj,'nezkontrolovano',now())"),
                    {"tn": _TENANT, "datum": r["datum"], "doklad": (r["ext_id"] or "")[:64],
                     "md": r["ucet_md"], "dal": r["ucet_dal"], "castka": abs(float(r["castka"] or 0)),
                     "popis": popis[:240], "kat": r["par_kategorie"] or r["par_metoda"], "zid": str(r["id"]),
                     "jist": j, "jzdroj": jzdroj[:120]})
                souhrn["zapsano"] += 1
        if not dry:
            # Změnový log: vznik pro každý nově zaúčtovaný automat-zápis (idempotentní)
            s.execute(_t(
                "INSERT INTO tenant.ucetni_denik_log (tenant_id, denik_id, akce, actor_type, actor_id, nova_hodnota, ts) "
                "SELECT :tn, d.id, 'vznik', d.actor_type, d.actor_id, "
                "jsonb_build_object('castka',d.castka,'ucet_md',d.ucet_md,'ucet_dal',d.ucet_dal,'jistota',d.jistota,'kategorie',d.kategorie,'jistota_zdroj',d.jistota_zdroj), now() "
                "FROM tenant.ucetni_denik d WHERE d.zdroj='bank' AND d.actor_type='automat' "
                "AND NOT EXISTS (SELECT 1 FROM tenant.ucetni_denik_log l WHERE l.denik_id=d.id AND l.akce='vznik')"),
                {"tn": _TENANT})
            s.commit()
        return {"ok": True, "dry": dry, "souhrn": souhrn}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/denik")
async def uctovani_denik_view(request: Request):
    """Přehled účetního deníku — řazený dle jistoty (nejistější nahoře = triáž pro účetní)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    stav = request.query_params.get("stav") or ""
    pasmo = request.query_params.get("pasmo") or ""
    klic = request.query_params.get("klic") or ""
    try:
        limit = min(1000, int(request.query_params.get("limit") or 300))
    except Exception:
        limit = 300
    s = _sess()
    try:
        # Pohled = fyzická pravda tabulky (žádné skrývání). Deník je živý sandbox —
        # co je v tabulce, to se ukáže. Marti 25.6.2026: "deník nesmí lhát o svém stavu".
        base = "WHERE tenant_id=:tn"
        summ = dict(s.execute(_t(
            "SELECT count(*) AS pocet, COALESCE(round(sum(castka)),0) AS objem, "
            "count(*) FILTER (WHERE jistota>=90) AS j_vys, count(*) FILTER (WHERE jistota>=70 AND jistota<90) AS j_str, "
            "count(*) FILTER (WHERE jistota<70) AS j_niz, "
            "count(*) FILTER (WHERE review_stav='nezkontrolovano') AS ceka "
            "FROM tenant.ucetni_denik " + base), {"tn": _TENANT}).mappings().first())
        where = base
        params = {"tn": _TENANT, "lim": limit}
        if stav:
            where += " AND review_stav=:stav"
            params["stav"] = stav
        if pasmo == "nizka":
            where += " AND jistota<70"
        elif pasmo == "stredni":
            where += " AND jistota>=70 AND jistota<90"
        elif pasmo == "vysoka":
            where += " AND jistota>=90"
        if klic:
            where += " AND jistota_zdroj IN ('predkontace_'||:klic, 'predkontace_'||:klic||'+zakazka')"
            params["klic"] = klic
        rows = [dict(r) for r in s.execute(_t(
            "SELECT id, datum, doklad, ucet_md, ucet_dal, castka, mena, popis, kategorie, actor_type, actor_id, "
            "jistota, jistota_zdroj, review_stav, zdroj FROM tenant.ucetni_denik " + where +
            " ORDER BY jistota ASC NULLS FIRST, datum DESC LIMIT :lim"), params).mappings().all()]
        for r in rows:
            if r.get("datum") is not None:
                r["datum"] = str(r["datum"])[:10]
            if r.get("jistota") is not None:
                r["jistota"] = float(r["jistota"])
            if r.get("castka") is not None:
                r["castka"] = float(r["castka"])
        return {"ok": True, "souhrn": summ, "zapisy": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/denik/detail")
async def denik_detail(request: Request):
    """Zpověď zápisu — klik na automata: kdo/kdy/na základě čeho + celý změnový log."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        eid = int(request.query_params.get("id") or 0)
    except Exception:
        eid = 0
    s = _sess()
    try:
        e = s.execute(_t(
            "SELECT id, datum, doklad, ucet_md, ucet_dal, castka, mena, popis, kategorie, "
            "actor_type, actor_id, jistota, jistota_zdroj, review_stav, review_at, zdroj, zdroj_id "
            "FROM tenant.ucetni_denik WHERE id=:id AND tenant_id=:tn"), {"id": eid, "tn": _TENANT}).mappings().first()
        if not e:
            return JSONResponse({"ok": False, "error": "zápis nenalezen"}, status_code=404)
        e = dict(e)
        for k in ("datum", "review_at", "jistota", "castka"):
            if e.get(k) is not None:
                e[k] = (float(e[k]) if k in ("jistota", "castka") else str(e[k]))
        log = [dict(r) for r in s.execute(_t(
            "SELECT akce, actor_type, actor_id, to_char(ts,'DD.MM.YYYY HH24:MI') AS kdy, poznamka "
            "FROM tenant.ucetni_denik_log WHERE denik_id=:id ORDER BY ts"), {"id": eid}).mappings().all()]
        # Konkrétní pravidlo (kuchařka), podle kterého se zaúčtovalo
        klic = (e.get("jistota_zdroj") or "").replace("predkontace_", "").replace("+zakazka", "").strip()
        pravidla = []
        if klic:
            pravidla = [dict(r) for r in s.execute(_t(
                "SELECT klic, typ_klice, smer, ucet_md, ucet_dal, base_jistota, pozn "
                "FROM tenant.bank_predkontace WHERE tenant_id=:tn AND klic=:k"),
                {"tn": _TENANT, "k": klic}).mappings().all()]
            for p in pravidla:
                if p.get("base_jistota") is not None:
                    p["base_jistota"] = float(p["base_jistota"])
        return {"ok": True, "zapis": e, "log": log, "pravidla": pravidla}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/denik/review")
async def denik_review(request: Request):
    """Účetní akce na zápisu: zkontrolováno / schváleno / vráceno automatu / oprava účtů.
    Píše do změnového logu (append-only). Deník = sandbox, běží přímo."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    eid = int(body.get("id") or 0)
    akce = (body.get("akce") or "").strip()
    _MAP = {"zkontrolovano": "zkontrolovano", "schvaleno": "schvaleno",
            "vraceno": "vraceno_automatu", "nazpet": "nezkontrolovano"}
    if akce not in _MAP and akce != "oprav":
        return JSONResponse({"ok": False, "error": "neznámá akce"}, status_code=400)
    s = _sess()
    try:
        if akce == "oprav":
            md = (str(body.get("ucet_md") or "")).strip()
            dal = (str(body.get("ucet_dal") or "")).strip()
            if not md or not dal:
                return JSONResponse({"ok": False, "error": "chybí účty"}, status_code=400)
            stara = s.execute(_t("SELECT ucet_md||'/'||ucet_dal FROM tenant.ucetni_denik WHERE id=:id AND tenant_id=:tn"),
                              {"id": eid, "tn": _TENANT}).scalar()
            s.execute(_t("UPDATE tenant.ucetni_denik SET ucet_md=:md, ucet_dal=:dal, "
                         "review_stav='opraveno', review_user_id=:u, review_at=now() WHERE id=:id AND tenant_id=:tn"),
                      {"md": md, "dal": dal, "u": uid, "id": eid, "tn": _TENANT})
            s.execute(_t("INSERT INTO tenant.ucetni_denik_log (tenant_id, denik_id, akce, actor_type, actor_id, poznamka, ts) "
                         "VALUES (:tn,:id,'oprava_uctu','human',:aid,:pozn,now())"),
                      {"tn": _TENANT, "id": eid, "aid": "human:%s" % uid, "pozn": "%s -> %s/%s" % (stara, md, dal)})
        else:
            rs = _MAP[akce]
            extra = ", schvalil=:u2, schvalil_at=now()" if akce == "schvaleno" else ""
            params = {"rs": rs, "u": uid, "id": eid, "tn": _TENANT}
            if akce == "schvaleno":
                params["u2"] = uid
            s.execute(_t("UPDATE tenant.ucetni_denik SET review_stav=:rs, review_user_id=:u, review_at=now()" + extra +
                         " WHERE id=:id AND tenant_id=:tn"), params)
            s.execute(_t("INSERT INTO tenant.ucetni_denik_log (tenant_id, denik_id, akce, actor_type, actor_id, ts) "
                         "VALUES (:tn,:id,:akce,'human',:aid,now())"),
                      {"tn": _TENANT, "id": eid, "akce": rs, "aid": "human:%s" % uid})
        s.commit()
        return {"ok": True}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/predkontace")
async def predkontace_kucharka(request: Request):
    """Kuchařka automata — všechna předkontační pravidla (na základě čeho účtuje)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT id, klic, typ_klice, smer, ucet_md, ucet_dal, base_jistota, pozn, aktivni, "
            "to_char(created_at,'DD.MM.YYYY HH24:MI') AS vzniklo, "
            "(SELECT count(*) FROM tenant.ucetni_denik d WHERE d.tenant_id=:tn AND d.jistota_zdroj LIKE 'predkontace_'||bank_predkontace.klic||'%') AS pouzito "
            "FROM tenant.bank_predkontace WHERE tenant_id=:tn "
            "ORDER BY base_jistota DESC, typ_klice, klic"), {"tn": _TENANT}).mappings().all()]
        for r in rows:
            if r.get("base_jistota") is not None:
                r["base_jistota"] = float(r["base_jistota"])
        return {"ok": True,
                "postavil": "Claude (id=23) — 24.6.2026 v noci, schváleno Marti přes banner (#662, #664)",
                "pravidla": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# Posting SQL automatu bank_v1 (idempotentní, jen CZK, jistota + bonus za zakázku)
_BANK_POST_SQL = (
    "INSERT INTO tenant.ucetni_denik (tenant_id, datum, doklad, ucet_md, ucet_dal, castka, mena, popis, "
    "kategorie, zdroj, zdroj_id, actor_type, actor_id, jistota, jistota_zdroj, review_stav, created_at) "
    "SELECT :tn, t.datum, left(t.ext_id,64), COALESCE(pk.ucet_md,pr.ucet_md,pm.ucet_md), "
    "COALESCE(pk.ucet_dal,pr.ucet_dal,pm.ucet_dal), abs(t.castka), 'CZK', "
    "left('Banka: '||COALESCE(pk.klic,pr.klic,pm.klic,'')||CASE WHEN t.par_zakazka IS NOT NULL THEN ' zak '||t.par_zakazka ELSE '' END||COALESCE(' - '||left(t.zprava,70),''),240), "
    "COALESCE(t.par_kategorie,t.par_metoda), 'bank', t.id, 'automat', :aid, "
    "LEAST(99, COALESCE(pk.base_jistota,pr.base_jistota,pm.base_jistota)+CASE WHEN t.par_zakazka IS NOT NULL THEN 10 ELSE 0 END), "
    "'predkontace_'||COALESCE(pk.klic,pr.klic,pm.klic,'')||CASE WHEN t.par_zakazka IS NOT NULL THEN '+zakazka' ELSE '' END, "
    "'nezkontrolovano', now() "
    "FROM tenant.bank_transaction_raw t "
    "LEFT JOIN tenant.bank_predkontace pk ON pk.tenant_id=:tn AND pk.typ_klice='kategorie' AND pk.klic=t.par_kategorie AND pk.aktivni AND (pk.smer IS NULL OR pk.smer=t.smer) "
    "LEFT JOIN tenant.bank_predkontace pr ON pr.tenant_id=:tn AND pr.typ_klice='rada' AND pr.klic=t.par_doklad_rada AND pr.aktivni AND (pr.smer IS NULL OR pr.smer=t.smer) "
    "LEFT JOIN tenant.bank_predkontace pm ON pm.tenant_id=:tn AND pm.typ_klice='metoda' AND pm.klic=t.par_metoda AND pm.aktivni AND (pm.smer IS NULL OR pm.smer=t.smer) "
    "WHERE t.par_metoda IS NOT NULL AND (t.mena='CZK' OR t.mena IS NULL) "
    "AND COALESCE(pk.ucet_md,pr.ucet_md,pm.ucet_md) IS NOT NULL "
    "AND NOT EXISTS (SELECT 1 FROM tenant.ucetni_denik d WHERE d.zdroj='bank' AND d.zdroj_id=t.id)")


@bank_router.get("/app/uctovani/automat")
async def automat_info(request: Request):
    """Občanka automatu: kdo vytvořil/schválil, verze, aktivní, jak se spouští + log běhů."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    kod = (request.query_params.get("kod") or "bank_v1").strip()
    s = _sess()
    try:
        a = s.execute(_t(
            "SELECT kod, nazev, verze, popis, vytvoril, to_char(vytvoreno,'DD.MM.YYYY HH24:MI') AS vytvoreno, "
            "schvalil, to_char(schvaleno,'DD.MM.YYYY HH24:MI') AS schvaleno, aktivni, spousteni, "
            "to_char(posledni_beh,'DD.MM.YYYY HH24:MI') AS posledni_beh "
            "FROM tenant.automat WHERE tenant_id=:tn AND kod=:k"), {"tn": _TENANT, "k": kod}).mappings().first()
        if not a:
            return JSONResponse({"ok": False, "error": "automat nenalezen"}, status_code=404)
        runs = [dict(r) for r in s.execute(_t(
            "SELECT spustil, to_char(spusteno,'DD.MM.YYYY HH24:MI') AS kdy, zapsano, vysledek, trvani_ms "
            "FROM tenant.automat_run WHERE tenant_id=:tn AND automat_kod=:k ORDER BY spusteno DESC LIMIT 15"),
            {"tn": _TENANT, "k": kod}).mappings().all()]
        pravidel = s.execute(_t("SELECT count(*) FROM tenant.bank_predkontace WHERE tenant_id=:tn AND aktivni"), {"tn": _TENANT}).scalar()
        zapisu = s.execute(_t("SELECT count(*) FROM tenant.ucetni_denik WHERE tenant_id=:tn AND actor_id=:aid"),
                           {"tn": _TENANT, "aid": "automat:" + kod}).scalar()
        return {"ok": True, "automat": dict(a), "behy": runs, "pocet_pravidel": pravidel, "pocet_zapisu": zapisu}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/automat/run")
async def automat_run_now(request: Request):
    """Ruční spuštění automatu — zaúčtuje nové napárované transakce + zapíše běh do logu."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    kod = (body.get("kod") or "bank_v1").strip()
    import time as _time
    s = _sess()
    try:
        akt = s.execute(_t("SELECT aktivni FROM tenant.automat WHERE tenant_id=:tn AND kod=:k"),
                        {"tn": _TENANT, "k": kod}).scalar()
        if akt is None:
            return JSONResponse({"ok": False, "error": "automat nenalezen"}, status_code=404)
        if not akt:
            return JSONResponse({"ok": False, "error": "automat je DEAKTIVOVANÝ — nejdřív ho aktivuj"}, status_code=400)
        t0 = _time.time()
        rr = s.execute(_t(_BANK_POST_SQL), {"tn": _TENANT, "aid": "automat:" + kod})
        zapsano = rr.rowcount if rr.rowcount is not None else 0
        s.execute(_t(
            "INSERT INTO tenant.ucetni_denik_log (tenant_id, denik_id, akce, actor_type, actor_id, nova_hodnota, ts) "
            "SELECT :tn, d.id, 'vznik', d.actor_type, d.actor_id, "
            "jsonb_build_object('castka',d.castka,'ucet_md',d.ucet_md,'ucet_dal',d.ucet_dal,'jistota',d.jistota), now() "
            "FROM tenant.ucetni_denik d WHERE d.zdroj='bank' AND d.actor_type='automat' "
            "AND NOT EXISTS (SELECT 1 FROM tenant.ucetni_denik_log l WHERE l.denik_id=d.id AND l.akce='vznik')"),
            {"tn": _TENANT})
        ms = int((_time.time() - t0) * 1000)
        vysl = "zaúčtováno %d nových" % zapsano if zapsano else "nic nového k zaúčtování"
        s.execute(_t("INSERT INTO tenant.automat_run (tenant_id, automat_kod, spustil, zapsano, vysledek, trvani_ms) "
                     "VALUES (:tn,:k,:who,:z,:v,:ms)"),
                  {"tn": _TENANT, "k": kod, "who": "human:%s" % uid, "z": zapsano, "v": vysl, "ms": ms})
        s.execute(_t("UPDATE tenant.automat SET posledni_beh=now() WHERE tenant_id=:tn AND kod=:k"), {"tn": _TENANT, "k": kod})
        s.commit()
        return {"ok": True, "zapsano": zapsano, "trvani_ms": ms}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/automat/toggle")
async def automat_toggle(request: Request):
    """Aktivace / deaktivace automatu."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    kod = (body.get("kod") or "bank_v1").strip()
    s = _sess()
    try:
        nova = s.execute(_t("UPDATE tenant.automat SET aktivni = NOT aktivni WHERE tenant_id=:tn AND kod=:k RETURNING aktivni"),
                         {"tn": _TENANT, "k": kod}).scalar()
        s.commit()
        return {"ok": True, "aktivni": nova}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/automaty")
async def automaty_list(request: Request):
    """Seznam (registr) všech automatů — u každého hned vidět, zda je aktivní."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT a.kod, a.nazev, a.verze, a.aktivni, a.spousteni, a.vytvoril, "
            "to_char(a.posledni_beh,'DD.MM.YYYY HH24:MI') AS posledni_beh, "
            "(SELECT count(*) FROM tenant.ucetni_denik d WHERE d.tenant_id=a.tenant_id AND d.actor_id='automat:'||a.kod) AS pocet_zapisu "
            "FROM tenant.automat a WHERE a.tenant_id=:tn ORDER BY a.kod"), {"tn": _TENANT}).mappings().all()]
        return {"ok": True, "automaty": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/predkontace/save")
async def predkontace_save(request: Request):
    """Editace / aktivace pravidla (podautomatu) — účty, jistota, poznámka, aktivní."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    rid = int(body.get("id") or 0)
    sets, params = [], {"id": rid, "tn": _TENANT}
    for col in ("ucet_md", "ucet_dal", "pozn"):
        if col in body:
            sets.append("%s=:%s" % (col, col))
            params[col] = (str(body[col]).strip() or None) if body[col] is not None else None
    if "base_jistota" in body and body["base_jistota"] is not None:
        try:
            sets.append("base_jistota=:bj")
            params["bj"] = max(0, min(100, float(body["base_jistota"])))
        except Exception:
            pass
    if "aktivni" in body:
        sets.append("aktivni=:akt")
        params["akt"] = bool(body["aktivni"])
    if not sets:
        return JSONResponse({"ok": False, "error": "nic ke změně"}, status_code=400)
    s = _sess()
    try:
        s.execute(_t("UPDATE tenant.bank_predkontace SET %s WHERE id=:id AND tenant_id=:tn" % ",".join(sets)), params)
        s.commit()
        return {"ok": True}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/hromady")
async def doklady_hromady(request: Request):
    """Roztříděná halda dokladů na hromady: přijaté/vydané faktury, banka, pokladna."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        firma = (request.query_params.get("firma") or "EC").upper()

        def cnt(sql, p=None):
            r = s.execute(_t(sql), p or {}).mappings().first()
            return {"ks": r["c"], "objem": float(r["o"] or 0)}
        # EC faktury = zrcadlo Centrály (ec_doklad_zbozi); ES faktury = z Heliosu (es_doklad_zbozi)
        dtbl = "tenant.ec_doklad_zbozi" if firma == "EC" else "tenant.es_doklad_zbozi"
        fp = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM " + dtbl + " WHERE rada LIKE '5%'")
        fv = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM " + dtbl + " WHERE rada LIKE '6%'")
        # VO = vydané objednávky (řada 800/801). Marti 25.6.2026.
        vo = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM " + dtbl + " WHERE rada LIKE '8%'")
        # PO = přijaté objednávky (řada 920) = zdroj zakázek pro párování. Marti 25.6.2026.
        po = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM " + dtbl + " WHERE rada LIKE '92%'")
        # PP = přijaté poptávky (řada 900) = poptávka od zákazníka → vzniká kalkulace+nabídka. Marti 25.6.2026.
        pp = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM " + dtbl + " WHERE rada LIKE '90%'")
        # Kalkulace/nabídky (řada 910 + EC_KalkulaceHlav) — jen EC. Marti 25.6.2026.
        kalk = cnt("SELECT count(*) c, COALESCE(round(sum(celkem_cena)),0) o FROM tenant.ec_kalkulace") \
            if firma == "EC" else {"ks": 0, "objem": 0}
        # Předkontace (TabUKod 1:1 z Heliosu) — EC i ES. Marti 25.6.2026.
        pred = cnt("SELECT count(*) c, 0 o FROM tenant.%sukod" % ("ec_" if firma == "EC" else "es_"))
        fpn = "Přijaté faktury (FP)"
        fvn = "Vydané faktury (FV)"
        bk = cnt("SELECT count(*) c, COALESCE(round(sum(abs(t.castka))),0) o FROM tenant.bank_transaction_raw t "
                 "JOIN tenant.bank_connection_account a ON a.id=t.account_id "
                 "JOIN tenant.bank_connection c ON c.id=a.connection_id "
                 "JOIN tenant.company co ON co.id=c.company_id WHERE co.code=:f", {"f": firma})
        pk = cnt("SELECT count(*) c, 0 o FROM tenant.ucet_pokladna WHERE tenant_id=:tn AND firma=:f", {"tn": _TENANT, "f": firma})
        return {"ok": True, "firma": firma, "firma_nazev": ("EUROSOFT-Control" if firma == "EC" else "EUROSOFT-System"),
                "hromady": [
            {"kod": "fp", "ikona": "📥", "nazev": fpn, "ks": fp["ks"], "objem": fp["objem"]},
            {"kod": "fv", "ikona": "📤", "nazev": fvn, "ks": fv["ks"], "objem": fv["objem"]},
            {"kod": "vo", "ikona": "📋", "nazev": "Vydané objednávky (VO)", "ks": vo["ks"], "objem": vo["objem"]},
            {"kod": "po", "ikona": "📑", "nazev": "Přijaté objednávky (PO)", "ks": po["ks"], "objem": po["objem"]},
            {"kod": "pp", "ikona": "❓", "nazev": "Přijaté poptávky (PP)", "ks": pp["ks"], "objem": pp["objem"]},
            {"kod": "kalk", "ikona": "🧮", "nazev": "Nabídky/Kalkulace (910)", "ks": kalk["ks"], "objem": kalk["objem"]},
            {"kod": "kontace", "ikona": "🧾", "nazev": "Předkontace (Helios 1:1)", "ks": pred["ks"], "objem": 0},
            {"kod": "banka", "ikona": "🏦", "nazev": "Bankovní výpisy", "ks": bk["ks"], "objem": bk["objem"]},
            {"kod": "pokladna", "ikona": "💵", "nazev": "Pokladna", "ks": pk["ks"], "objem": pk["objem"]},
        ]}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/hromada")
async def doklady_hromada(request: Request):
    """Doklady v jedné hromadě (typ=fp|fv|banka|pokladna)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    typ = (request.query_params.get("typ") or "").strip()
    firma = (request.query_params.get("firma") or "EC").upper()
    s = _sess()
    dtbl = "tenant.ec_doklad_zbozi" if firma == "EC" else "tenant.es_doklad_zbozi"
    try:
        if typ in ("fp", "fv", "vo"):
            rl = {"fp": "5%", "fv": "6%", "vo": "8%"}[typ]
            rows = [dict(r) for r in s.execute(_t(
                "SELECT id, to_char(COALESCE(dat_realizace,dat_porizeni),'DD.MM.YYYY') AS datum, cislo, rada, "
                "COALESCE(nazev,'') AS nazev, mena, round(suma_bez_dph) AS castka, "
                "cislo_org, COALESCE(cislo_zakazky,'') AS zakazka, COALESCE(stav_fakturace,'') AS stav "
                "FROM " + dtbl + " WHERE rada LIKE :rl "
                "ORDER BY COALESCE(dat_realizace,dat_porizeni) ASC NULLS LAST, cislo ASC LIMIT 200"),
                {"rl": rl}).mappings().all()]
        elif typ == "kontace":
            _kp = "ec_" if firma == "EC" else "es_"
            rows = [dict(r) for r in s.execute(_t(
                "SELECT u.id, u.cislokontace AS cislo, COALESCE(u.nazev,'') AS nazev, "
                "COALESCE(u.radadokladu,'') AS rada, COALESCE(u.sbornik,'') AS sbornik, u.druhpohybu, "
                "(SELECT count(*) FROM tenant.%sukod_radek r WHERE r.idukod=u.id) AS radku "
                "FROM tenant.%sukod u ORDER BY u.cislokontace" % (_kp, _kp))).mappings().all()]
        elif typ == "kalk":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT id, id_kalk, to_char(dat_porizeni,'DD.MM.YYYY') AS datum, doklad AS cislo, "
                "COALESCE(cislo_kalkulace,'') AS cislo_kalk, COALESCE(nazev,'') AS nazev, "
                "COALESCE(cislo_zakazky,'') AS zakazka, pocet_polozek, round(celkem_cena) AS castka, "
                "COALESCE(resitel,'') AS resitel "
                "FROM tenant.ec_kalkulace ORDER BY dat_porizeni DESC NULLS LAST, id DESC LIMIT 200")).mappings().all()]
        elif typ == "po":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT id, to_char(dat_porizeni,'DD.MM.YYYY') AS datum, cislo, "
                "COALESCE(nazev,'') AS nazev, COALESCE(cislo_zakazky,'') AS zakazka, "
                "COALESCE(navazna_objednavka,'') AS ref_zak, COALESCE(popis_dodavky,'') AS popis, "
                "mena, round(suma_bez_dph) AS castka "
                "FROM " + dtbl + " WHERE rada LIKE '92%' "
                "ORDER BY dat_porizeni DESC NULLS LAST, cislo DESC LIMIT 200")).mappings().all()]
        elif typ == "pp":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT id, to_char(dat_porizeni,'DD.MM.YYYY') AS datum, cislo, "
                "COALESCE(nazev,'') AS nazev, COALESCE(cislo_zakazky,'') AS zakazka, "
                "COALESCE(navazna_objednavka,'') AS navazny, COALESCE(popis_dodavky,'') AS popis "
                "FROM " + dtbl + " WHERE rada LIKE '90%' "
                "ORDER BY dat_porizeni DESC NULLS LAST, cislo DESC LIMIT 200")).mappings().all()]
        elif typ == "banka":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT to_char(t.datum,'DD.MM.YYYY') AS datum, t.ext_id AS doklad, round(t.castka) AS castka, t.mena, "
                "COALESCE(t.vs,'') AS vs, t.smer, left(COALESCE(t.zprava,''),50) AS zprava "
                "FROM tenant.bank_transaction_raw t "
                "JOIN tenant.bank_connection_account a ON a.id=t.account_id "
                "JOIN tenant.bank_connection c ON c.id=a.connection_id "
                "JOIN tenant.company co ON co.id=c.company_id WHERE co.code=:f "
                "ORDER BY t.datum ASC LIMIT 200"), {"f": firma}).mappings().all()]
        elif typ == "pokladna":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT cislo, nazev, mena, typ, COALESCE(ucet_md,'') AS ucet FROM tenant.ucet_pokladna "
                "WHERE tenant_id=:tn AND firma=:f ORDER BY cislo"), {"tn": _TENANT, "f": firma}).mappings().all()]
        else:
            return JSONResponse({"ok": False, "error": "neznámý typ"}, status_code=400)
        for r in rows:
            if r.get("castka") is not None:
                r["castka"] = float(r["castka"])
        return {"ok": True, "typ": typ, "polozky": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/osnova")
async def ucetni_osnova(request: Request):
    """Účtová osnova po letech (z deníku) — účty + obrat per rok, ať se dají roky porovnat."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma = (request.query_params.get("firma") or "EC").upper()
    tbl = "tenant.ec_denik" if firma == "EC" else "tenant.es_denik"
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT ucet, rok, round(sum(abs(castka))) AS obrat, count(*) AS radku "
            "FROM " + tbl + " WHERE ucet IS NOT NULL AND ucet<>'' "
            "GROUP BY ucet, rok ORDER BY ucet, rok")).mappings().all()]
        roky = sorted({int(r["rok"]) for r in rows if r["rok"] is not None})
        # pivot: účet → {rok: {obrat, radku}}
        osnova = {}
        for r in rows:
            u = r["ucet"]
            osnova.setdefault(u, {"ucet": u, "roky": {}})
            osnova[u]["roky"][int(r["rok"])] = {"obrat": float(r["obrat"] or 0), "radku": r["radku"]}
        polozky = sorted(osnova.values(), key=lambda x: x["ucet"])
        return {"ok": True, "firma": firma,
                "firma_nazev": ("EUROSOFT-Control" if firma == "EC" else "EUROSOFT-System"),
                "roky": roky, "polozky": polozky}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/rady")
async def rady_predkontace(request: Request):
    """Řady dokladů (sborníky) a jejich předkontace — jaké účty se na danou řadu reálně účtují."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma = (request.query_params.get("firma") or "EC").upper()
    tbl = "tenant.ec_denik" if firma == "EC" else "tenant.es_denik"
    s = _sess()
    try:
        roky = [int(r[0]) for r in s.execute(_t("SELECT DISTINCT rok FROM " + tbl + " WHERE rok IS NOT NULL ORDER BY rok")).all()]
        try:
            rok = int(request.query_params.get("rok") or (roky[-1] if roky else 0))
        except Exception:
            rok = roky[-1] if roky else 0
        rady = [dict(r) for r in s.execute(_t(
            "SELECT d.sbornik AS kod, COALESCE(sb.nazev,'') AS nazev, COALESCE(sb.druh,'') AS druh, "
            "count(*) AS radku, round(sum(abs(d.castka))) AS obrat, "
            "string_agg(DISTINCT d.ucet, ', ' ORDER BY d.ucet) FILTER (WHERE d.ucet IS NOT NULL AND d.ucet<>'') AS ucty "
            "FROM " + tbl + " d LEFT JOIN tenant.ucet_sbornik sb ON sb.kod=d.sbornik AND sb.tenant_id=:tn "
            "WHERE d.rok=:rok AND d.sbornik IS NOT NULL "
            "GROUP BY d.sbornik, sb.nazev, sb.druh ORDER BY count(*) DESC"),
            {"tn": _TENANT, "rok": rok}).mappings().all()]
        for r in rady:
            if r.get("obrat") is not None:
                r["obrat"] = float(r["obrat"] or 0)
        return {"ok": True, "firma": firma, "rok": rok, "roky": roky, "rady": rady}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/doklad-pdf")
async def doklad_pdf(request: Request):
    """Proklik na fyzický papír — naskenovaná faktura z EUROSOFT serveru přes MCP."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    cislo = (request.query_params.get("cislo") or "").strip()
    typ = (request.query_params.get("typ") or "fp").strip().lower()
    firma = (request.query_params.get("firma") or "EC").upper()
    iddok = (request.query_params.get("id") or "").strip()
    if not cislo and not iddok:
        return JSONResponse({"ok": False, "error": "chybí id/číslo"}, status_code=400)
    # ── Dokument otevři PŘÍMO z doc_path (JmenoACesta / EC_Doklad_NajdiDokument,
    #    autoritativní vazba TabDokumVazba/TabDokumenty), ne hádání složek. Lookup přes
    #    unikátní id (PoradoveCislo se u PF opakuje). Soubor může být i .docx/.msg/.jpeg.
    #    Platí pro EC i ES (sjednoceno 25.6.2026). Když doc_path chybí (starší EC bez
    #    skenu) → fallback na složku D:\data\FakturyP|V\<cislo> níže. ──
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    import json as _je, base64 as _be, ntpath as _np, mimetypes as _mt
    _dtbl = "tenant.ec_doklad_zbozi" if firma == "EC" else "tenant.es_doklad_zbozi"
    s2 = _sess()
    try:
        if iddok:
            dp = s2.execute(_t("SELECT doc_path FROM " + _dtbl + " "
                               "WHERE id=:i AND doc_path IS NOT NULL AND doc_path<>''"),
                            {"i": int(iddok)}).scalar()
        else:
            dp = s2.execute(_t("SELECT doc_path FROM " + _dtbl + " "
                               "WHERE cislo=:c AND doc_path IS NOT NULL AND doc_path<>'' "
                               "ORDER BY id DESC LIMIT 1"), {"c": cislo}).scalar()
    except Exception:
        dp = None
    finally:
        s2.close()
    if dp:
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return JSONResponse({"ok": False, "error": "EUROSOFT MCP nedostupný"}, status_code=503)
        try:
            # UNC \\192.168.30.11\data\... → lokální D:\data\... (MCP RO root je D:\data na EC-SERVER2)
            dp_loc = ("D:\\data" + dp[len("\\\\192.168.30.11\\data"):]) \
                     if dp.lower().startswith("\\\\192.168.30.11\\data") else dp
            # doc_path může být konkrétní SOUBOR (VF/PF) nebo SLOŽKA dokladu (VO:
            # ObjednavkyV\EOS<cislo> — VO nejsou v DMS, jen soubor ve složce).
            if _np.splitext(dp_loc)[1]:
                folder = _np.dirname(dp_loc); fname = _np.basename(dp_loc)
            else:
                folder = dp_loc; fname = ""
            # Preferuj PDF: pokud fname není .pdf (.msg/.docx) nebo chybí (složka),
            # projdi složku dokladu a vezmi papír (.pdf). Marti 25.6.2026.
            if (not fname) or (not fname.lower().endswith(".pdf")):
                try:
                    lraw = mcp.call_tool_sync("eurosoft_eurosoft_file_list",
                                              {"user_namespace": "ro", "base_override": folder, "subpath": ""},
                                              conversation_id=None)
                    lr = _je.loads(lraw) if isinstance(lraw, str) else lraw
                    its = (lr.get("items") or lr.get("files") or lr.get("entries") or []) if isinstance(lr, dict) else (lr or [])
                    for it in its:
                        nm = (it.get("name") or it.get("filename") or it.get("path")) if isinstance(it, dict) else it
                        if nm and str(nm).lower().endswith(".pdf"):
                            fname = str(nm)
                            break
                except Exception:
                    pass
            if not fname:
                return JSONResponse({"ok": False, "error": "Ve složce dokladu není PDF: " + dp}, status_code=404)
            raw2 = mcp.call_tool_sync("eurosoft_eurosoft_file_read",
                                      {"user_namespace": "ro", "base_override": folder,
                                       "path": fname, "encoding": "base64"}, conversation_id=None)
            r2 = _je.loads(raw2) if isinstance(raw2, str) else raw2
            if isinstance(r2, dict) and r2.get("ok") is False:
                return JSONResponse({"ok": False, "error": "Soubor nenalezen/nečitelný: " + dp,
                                     "detail": str(r2.get("error") or r2.get("message") or "")[:200]}, status_code=404)
            b64 = (r2.get("content") or r2.get("data") or "") if isinstance(r2, dict) else str(r2)
            data = _be.b64decode(b64) if b64 else b""
            if not data:
                return JSONResponse({"ok": False, "error": "Soubor prázdný"}, status_code=404)
            import urllib.parse as _up
            ctype = _mt.guess_type(fname)[0] or "application/octet-stream"
            disp = "inline" if ctype == "application/pdf" or ctype.startswith("image/") else "attachment"
            # HTTP hlavička = latin-1; český název souboru → RFC 5987 filename* (UTF-8)
            # + ASCII fallback (cislo+přípona), ať to nespadne na diakritice.
            _ext = _np.splitext(fname)[1] or ".bin"
            _ascii = ((cislo or "doklad").encode("ascii", "ignore").decode() or "doklad") + _ext
            cd = "%s; filename=\"%s\"; filename*=UTF-8''%s" % (disp, _ascii, _up.quote(fname))
            return Response(content=data, media_type=ctype, headers={"Content-Disposition": cd})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": "Čtení skenu selhalo: %s: %s" % (type(exc).__name__, str(exc)[:200]),
                                 "doc_path": dp}, status_code=502)
    # Fallback (jen EC, starší doklady bez doc_path): D:\data\FakturyP\FP<cislo> (FP) /
    # D:\data\FakturyV\FV<cislo> (FV) — ověřená cesta přes MCP (handoff 25.6.).
    if firma != "EC":
        return JSONResponse({"ok": False, "error": "Doklad nemá naskenovaný papír (doc_path)"}, status_code=404)
    if typ == "fv":
        base = "D:\\data\\FakturyV\\FV" + cislo
    else:
        base = "D:\\data\\FakturyP\\FP" + cislo
    try:
        import json as _j, base64 as _b64
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return JSONResponse({"ok": False, "error": "EUROSOFT MCP nedostupný"}, status_code=503)
        raw = mcp.call_tool_sync("eurosoft_eurosoft_file_list",
                                 {"user_namespace": "ro", "base_override": base, "subpath": ""}, conversation_id=None)
        r = _j.loads(raw) if isinstance(raw, str) else raw
        if isinstance(r, dict) and r.get("ok") is False:
            return JSONResponse({"ok": False, "error": "Složka dokladu nenalezena: " + base}, status_code=404)
        items = (r.get("items") or r.get("files") or r.get("entries") or []) if isinstance(r, dict) else (r or [])
        pdf_name = None
        for it in items:
            nm = (it.get("name") or it.get("filename") or it.get("path")) if isinstance(it, dict) else it
            if nm and str(nm).lower().endswith(".pdf"):
                pdf_name = nm
                break
        if not pdf_name:
            return JSONResponse({"ok": False, "error": "Doklad nemá naskenovaný PDF papír"}, status_code=404)
        raw2 = mcp.call_tool_sync("eurosoft_eurosoft_file_read",
                                  {"user_namespace": "ro", "base_override": base, "path": pdf_name, "encoding": "base64"},
                                  conversation_id=None)
        r2 = _j.loads(raw2) if isinstance(raw2, str) else raw2
        b64 = (r2.get("content") or r2.get("data") or "") if isinstance(r2, dict) else str(r2)
        data = _b64.b64decode(b64) if b64 else b""
        if not data:
            return JSONResponse({"ok": False, "error": "PDF prázdné"}, status_code=404)
        return Response(content=data, media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=%s%s.pdf" % (typ.upper(), cislo)})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)


@bank_router.post("/app/uctovani/sync-es-faktury")
async def sync_es_faktury(request: Request):
    """Dotáhne ES doklady (FP/FV + VO vydané objednávky, 2025+) z Heliosu DB_IS
    → tenant.es_doklad_zbozi. VO = řada 8 (Marti 25.6.2026)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _int(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _str(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = ("SELECT d.ID, d.Cislo, d.RadaDokladu, d.CisloOrg, RTRIM(d.CisloZakazky) CisloZakazky, "
           "d.Nazev, d.Mena, d.StavFakturace, CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
           "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DatRealizace,23) dr "
           "FROM [DB_IS].dbo.TabDokladyZbozi d WHERE (d.RadaDokladu LIKE '5%' OR d.RadaDokladu LIKE '6%' OR d.RadaDokladu LIKE '8%') "
           "AND d.DatPorizeni >= '2025-01-01'")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        n = 0
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.es_doklad_zbozi (src_id, cislo, rada, cislo_org, cislo_zakazky, nazev, mena, "
                "stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, synced_at) "
                "VALUES (:sid,:c,:r,:co,:cz,:n,:m,:sf,:s,:dp,:dr,now()) "
                "ON CONFLICT (src_id) DO UPDATE SET cislo=excluded.cislo, rada=excluded.rada, "
                "cislo_org=excluded.cislo_org, cislo_zakazky=excluded.cislo_zakazky, nazev=excluded.nazev, "
                "mena=excluded.mena, stav_fakturace=excluded.stav_fakturace, suma_bez_dph=excluded.suma_bez_dph, "
                "dat_porizeni=excluded.dat_porizeni, dat_realizace=excluded.dat_realizace, synced_at=now()"),
                {"sid": _int(r.get("id")), "c": _str(r.get("cislo")), "r": _str(r.get("radadokladu")),
                 "co": _int(r.get("cisloorg")), "cz": _str(r.get("cislozakazky")), "n": _str(r.get("nazev")),
                 "m": _str(r.get("mena")), "sf": _str(r.get("stavfakturace")), "s": _num(r.get("sumakcbezdph")),
                 "dp": _str(r.get("dp")), "dr": _str(r.get("dr"))})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-es-vf")
async def sync_es_vf(request: Request):
    """1:1 zrcadlo ES Vydaných faktur z DB_EC (přehled 10120, Marti 25.6.2026):
    rada 601/641 (NOT IN 600/620/630/640), DruhPohybuZbo 13-14, IDSklad NULL,
    roky 2025-26. cislo = PoradoveCislo. doc_path = JmenoACesta (preferuj UNC
    cestu \\server), je_sken z TabDokumVazba (IdentVazby=9). DELETE+INSERT řad 6%
    = čistý mirror. Vazba doklad->sken je autoritativní (ne hádání složek)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.CisloOrg, RTRIM(d.CisloZakazky) CisloZakazky, "
        "o.Nazev, d.Mena, d.StavFakturace, CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DUZP,23) dr, "
        "(CASE (SELECT count(*) FROM TabDokumVazba WHERE IdTab=d.ID AND IdentVazby=9) WHEN 0 THEN 0 ELSE 1 END) je_sken, "
        "(SELECT TOP 1 dok.JmenoACesta FROM TabDokumVazba v JOIN TabDokumenty dok ON dok.ID=v.IdDok "
        " WHERE v.IdTab=d.ID AND v.IdentVazby=9 AND dok.JmenoACesta LIKE '\\\\%' ORDER BY dok.ID DESC) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.IDSklad IS NULL AND d.DruhPohybuZbo BETWEEN 13 AND 14 AND d.PoradoveCislo>=0 "
        "AND d.RadaDokladu NOT IN (600,620,630,640) AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.es_doklad_zbozi WHERE rada LIKE '6%'"))
        n = 0
        sken = 0
        for r in rows:
            js = bool(_i(r.get("je_sken")) or 0)
            if js:
                sken += 1
            s.execute(_t(
                "INSERT INTO tenant.es_doklad_zbozi (src_id, cislo, rada, cislo_org, cislo_zakazky, nazev, mena, "
                "stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken, synced_at) "
                "VALUES (:sid,:c,:r,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,:js,now())"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")), "n": _s(r.get("nazev")),
                 "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")), "s": _n(r.get("sumakcbezdph")),
                 "dp": _s(r.get("dp")), "dr": _s(r.get("dr")), "doc": _s(r.get("doc_path")), "js": js})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n, "se_skenem": sken}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-es-vo")
async def sync_es_vo(request: Request):
    """1:1 zrcadlo ES Vydaných objednávek z DB_EC (přehled 10150, Marti 25.6.2026):
    rada 801, DruhPohybuZbo=6, roky 2025-26. cislo=PoradoveCislo. VO NEJSOU v Helios
    DMS (je_sken=0, EC_Doklad_NajdiDokument prázdné) → doc_path = SLOŽKA
    \\\\192.168.30.11\\data\\ObjednavkyV\\EOS<cislo> (papír se dohledá listingem při
    otevření). DELETE+INSERT řad 8% = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.CisloOrg, RTRIM(d.CisloZakazky) CisloZakazky, "
        "o.Nazev, d.Mena, d.StavFakturace, CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DatRealizace,23) dr, "
        "'\\\\192.168.30.11\\data\\ObjednavkyV\\EOS' + RTRIM(CAST(d.PoradoveCislo AS varchar(20))) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.RadaDokladu=801 AND d.DruhPohybuZbo=6 AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.es_doklad_zbozi WHERE rada LIKE '8%'"))
        n = 0
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.es_doklad_zbozi (src_id, cislo, rada, cislo_org, cislo_zakazky, nazev, mena, "
                "stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken, synced_at) "
                "VALUES (:sid,:c,:r,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,false,now())"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")), "n": _s(r.get("nazev")),
                 "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")), "s": _n(r.get("sumakcbezdph")),
                 "dp": _s(r.get("dp")), "dr": _s(r.get("dr")), "doc": _s(r.get("doc_path"))})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-es-pf")
async def sync_es_pf(request: Request):
    """1:1 zrcadlo ES Přijatých faktur z DB_EC (přehled 10100, Marti 25.6.2026):
    rada 501/511/521/531/541, DruhPohybuZbo 18-19, roky 2025-26. cislo=PoradoveCislo,
    doc_path = dbo.EC_Doklad_NajdiDokument(ID) (plná cesta vč. souboru, i .docx/.msg/.jpeg),
    je_sken z TabDokumVazba (IdentVazby=9). DELETE+INSERT řad 5% = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.CisloOrg, RTRIM(d.CisloZakazky) CisloZakazky, "
        "o.Nazev, d.Mena, d.StavFakturace, CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DUZP,23) dr, "
        "(CASE (SELECT count(*) FROM TabDokumVazba WHERE IdTab=d.ID AND IdentVazby=9) WHEN 0 THEN 0 ELSE 1 END) je_sken, "
        "dbo.EC_Doklad_NajdiDokument(d.ID) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.DruhPohybuZbo BETWEEN 18 AND 19 AND d.PoradoveCislo>=0 "
        "AND d.RadaDokladu IN (501,511,521,531,541) AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.es_doklad_zbozi WHERE rada LIKE '5%'"))
        n = 0
        sken = 0
        for r in rows:
            js = bool(_i(r.get("je_sken")) or 0)
            if js:
                sken += 1
            s.execute(_t(
                "INSERT INTO tenant.es_doklad_zbozi (src_id, cislo, rada, cislo_org, cislo_zakazky, nazev, mena, "
                "stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken, synced_at) "
                "VALUES (:sid,:c,:r,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,:js,now())"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")), "n": _s(r.get("nazev")),
                 "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")), "s": _n(r.get("sumakcbezdph")),
                 "dp": _s(r.get("dp")), "dr": _s(r.get("dr")), "doc": _s(r.get("doc_path")), "js": js})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n, "se_skenem": sken}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-pf")
async def sync_ec_pf(request: Request):
    """1:1 zrcadlo EC Přijatých faktur z DB_EC (přehled 2300, Marti 25.6.2026):
    DruhPohybuZbo 18-19, rada 500/510/520/530/540/560/590, roky 2025-26.
    cislo=PoradoveCislo, doc_path = dbo.EC_Doklad_NajdiDokument(ID) (plná cesta vč.
    souboru, i .xls/.docx), je_sken z TabDokumVazba (IdentVazby=9). DELETE+INSERT řad
    5% = čistý mirror 2025-26."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.DruhPohybuZbo, d.CisloOrg, "
        "RTRIM(d.CisloZakazky) CisloZakazky, o.Nazev, d.Mena, d.StavFakturace, "
        "CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DUZP,23) dr, "
        "(CASE (SELECT count(*) FROM TabDokumVazba WHERE IdTab=d.ID AND IdentVazby=9) WHEN 0 THEN 0 ELSE 1 END) je_sken, "
        "dbo.EC_Doklad_NajdiDokument(d.ID) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.DruhPohybuZbo BETWEEN 18 AND 19 AND d.PoradoveCislo>=0 "
        "AND d.RadaDokladu IN (500,510,520,530,540,560,590) AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_doklad_zbozi WHERE rada LIKE '5%'"))
        n = 0
        sken = 0
        for r in rows:
            js = bool(_i(r.get("je_sken")) or 0)
            if js:
                sken += 1
            s.execute(_t(
                "INSERT INTO tenant.ec_doklad_zbozi (src_id, cislo, rada, druh_pohybu, cislo_org, cislo_zakazky, "
                "nazev, mena, stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken) "
                "VALUES (:sid,:c,:r,:dph,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,:js)"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "dph": _i(r.get("druhpohybuzbo")), "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")),
                 "n": _s(r.get("nazev")), "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")),
                 "s": _n(r.get("sumakcbezdph")), "dp": _s(r.get("dp")), "dr": _s(r.get("dr")),
                 "doc": _s(r.get("doc_path")), "js": js})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n, "se_skenem": sken}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-fv")
async def sync_ec_fv(request: Request):
    """1:1 zrcadlo EC Vydaných faktur z DB_EC (přehled 260, Marti 25.6.2026):
    DruhPohybuZbo 13-14, IDSklad IS NULL, rada NOT IN (601,621,631,641) (ty jsou ES),
    roky 2025-26. cislo=PoradoveCislo, doc_path = dbo.EC_Doklad_NajdiDokument(ID),
    je_sken z TabDokumVazba (IdentVazby=9). DELETE+INSERT řad 6% = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.DruhPohybuZbo, d.CisloOrg, "
        "RTRIM(d.CisloZakazky) CisloZakazky, o.Nazev, d.Mena, d.StavFakturace, "
        "CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DUZP,23) dr, "
        "(CASE (SELECT count(*) FROM TabDokumVazba WHERE IdTab=d.ID AND IdentVazby=9) WHEN 0 THEN 0 ELSE 1 END) je_sken, "
        "dbo.EC_Doklad_NajdiDokument(d.ID) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.DruhPohybuZbo BETWEEN 13 AND 14 AND d.IDSklad IS NULL AND d.PoradoveCislo>=0 "
        "AND d.RadaDokladu NOT IN (601,621,631,641) AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_doklad_zbozi WHERE rada LIKE '6%'"))
        n = 0
        sken = 0
        for r in rows:
            js = bool(_i(r.get("je_sken")) or 0)
            if js:
                sken += 1
            s.execute(_t(
                "INSERT INTO tenant.ec_doklad_zbozi (src_id, cislo, rada, druh_pohybu, cislo_org, cislo_zakazky, "
                "nazev, mena, stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken) "
                "VALUES (:sid,:c,:r,:dph,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,:js)"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "dph": _i(r.get("druhpohybuzbo")), "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")),
                 "n": _s(r.get("nazev")), "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")),
                 "s": _n(r.get("sumakcbezdph")), "dp": _s(r.get("dp")), "dr": _s(r.get("dr")),
                 "doc": _s(r.get("doc_path")), "js": js})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n, "se_skenem": sken}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-vo")
async def sync_ec_vo(request: Request):
    """1:1 zrcadlo EC Vydaných objednávek z DB_EC (přehled 210, Marti 25.6.2026):
    rada 800, IDSklad='001', roky 2025-26. cislo=PoradoveCislo. VO NEJSOU v DMS →
    doc_path = SLOŽKA \\\\192.168.30.11\\data\\ObjednavkyV\\EO<cislo> (label EC_GetDoklad =
    EO<PoradoveCislo>, papír se dohledá listingem při otevření). DELETE+INSERT řad 8%."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.DruhPohybuZbo, d.CisloOrg, "
        "RTRIM(d.CisloZakazky) CisloZakazky, o.Nazev, d.Mena, d.StavFakturace, "
        "CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp, CONVERT(varchar(10),d.DatRealizace,23) dr, "
        "'\\\\192.168.30.11\\data\\ObjednavkyV\\EO' + RTRIM(CAST(d.PoradoveCislo AS varchar(20))) doc_path "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.IDSklad='001' AND d.RadaDokladu=800 AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_doklad_zbozi WHERE rada LIKE '8%'"))
        n = 0
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.ec_doklad_zbozi (src_id, cislo, rada, druh_pohybu, cislo_org, cislo_zakazky, "
                "nazev, mena, stav_fakturace, suma_bez_dph, dat_porizeni, dat_realizace, doc_path, je_sken) "
                "VALUES (:sid,:c,:r,:dph,:co,:cz,:n,:m,:sf,:s,:dp,:dr,:doc,false)"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "dph": _i(r.get("druhpohybuzbo")), "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")),
                 "n": _s(r.get("nazev")), "m": _s(r.get("mena")), "sf": _s(r.get("stavfakturace")),
                 "s": _n(r.get("sumakcbezdph")), "dp": _s(r.get("dp")), "dr": _s(r.get("dr")),
                 "doc": _s(r.get("doc_path"))})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-po")
async def sync_ec_po(request: Request):
    """1:1 zrcadlo EC Přijatých objednávek z DB_EC (přehled 506, Marti 25.6.2026):
    DruhPohybuZbo 11, rada 920, roky 2025-26. ZDROJ ZAKÁZEK pro párování příchozích
    plateb (zákazník referencuje svou objednávku → navazna_objednavka → cislo_zakazky).
    cislo=PoradoveCislo. DELETE+INSERT řad 9% = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.DruhPohybuZbo, d.CisloOrg, o.Nazev, "
        "RTRIM(d.CisloZakazky) CisloZakazky, d.NavaznaObjednavka, d.Mena, "
        "CAST(d.SumaKcBezDPH AS numeric(19,2)) SumaKcBezDPH, "
        "SUBSTRING(REPLACE(SUBSTRING(d.PopisDodavky,1,255),NCHAR(13)+NCHAR(10),NCHAR(32)),1,255) PopisDodavky, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.DruhPohybuZbo=11 AND d.RadaDokladu=920 AND d.PoradoveCislo>=0 "
        "AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_doklad_zbozi WHERE rada LIKE '92%'"))
        n = 0
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.ec_doklad_zbozi (src_id, cislo, rada, druh_pohybu, cislo_org, cislo_zakazky, "
                "navazna_objednavka, nazev, popis_dodavky, mena, suma_bez_dph, dat_porizeni) "
                "VALUES (:sid,:c,:r,:dph,:co,:cz,:no,:n,:pop,:m,:s,:dp)"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "dph": _i(r.get("druhpohybuzbo")), "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")),
                 "no": _s(r.get("navaznaobjednavka")), "n": _s(r.get("nazev")), "pop": _s(r.get("popisdodavky")),
                 "m": _s(r.get("mena")), "s": _n(r.get("sumakcbezdph")), "dp": _s(r.get("dp"))})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


def _kalk_n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _kalk_i(v):
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _kalk_s(v):
    v = (str(v).replace("\x00", "").strip() if v is not None else "")
    return v or None


@bank_router.post("/app/uctovani/sync-ec-kalkulace")
async def sync_ec_kalkulace(request: Request):
    """1:1 zrcadlo EC nabídek/kalkulací z DB_EC (přehled 505, Marti 25.6.2026):
    rada 910 (nabídka zákazníkovi) + EC_KalkulaceHlav (kalkulace výroby rozváděče),
    roky 2025-26. Hlavička → tenant.ec_kalkulace. Položky zvlášť (sync-ec-kalk-pol).
    Z kalkulací se generují VO a výdejky na zakázky."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    sql = (
        "SELECT d.ID src_doklad_id, k.ID id_kalk, k.CisloKalkulace, dbo.EC_GetDoklad(d.ID) doklad, "
        "RTRIM(d.CisloZakazky) cislo_zakazky, d.CisloOrg, o.Nazev, d.StredNaklad stredisko, "
        "(SELECT count(*) FROM EC_KalkulacePolozky WHERE IDHlav=k.ID) pocet_polozek, "
        "CAST(k.CelkemCena AS numeric(19,2)) celkem_cena, CAST(k.CelkemHod AS numeric(19,2)) celkem_hod, "
        "CAST(k.MarzeProcent AS numeric(9,2)) marze_proc, CONVERT(varchar(10),d.DatPorizeni,23) dp, "
        "d.Autor, z.LoginID resitel, d.Splneno, "
        "SUBSTRING(REPLACE(SUBSTRING(d.Poznamka,1,255),NCHAR(13)+NCHAR(10),NCHAR(32)),1,255) poznamka "
        "FROM TabDokladyZbozi d JOIN EC_KalkulaceHlav k ON d.ID=k.IDDoklad "
        "LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg LEFT JOIN TabCisZam z ON d.CisloZam=z.Cislo "
        "WHERE d.RadaDokladu='910' AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_kalkulace"))
        batch = [{
            "sd": _kalk_i(r.get("src_doklad_id")), "ik": _kalk_i(r.get("id_kalk")),
            "ck": _kalk_s(r.get("cislokalkulace")), "dk": _kalk_s(r.get("doklad")),
            "cz": _kalk_s(r.get("cislo_zakazky")), "co": _kalk_i(r.get("cisloorg")),
            "nz": _kalk_s(r.get("nazev")), "st": _kalk_s(r.get("stredisko")),
            "pp": _kalk_i(r.get("pocet_polozek")), "cc": _kalk_n(r.get("celkem_cena")),
            "ch": _kalk_n(r.get("celkem_hod")), "mp": _kalk_n(r.get("marze_proc")),
            "dp": _kalk_s(r.get("dp")), "au": _kalk_s(r.get("autor")), "re": _kalk_s(r.get("resitel")),
            "sp": _kalk_i(r.get("splneno")), "po": _kalk_s(r.get("poznamka"))} for r in rows]
        if batch:
            s.execute(_t(
                "INSERT INTO tenant.ec_kalkulace (src_doklad_id, id_kalk, cislo_kalkulace, doklad, "
                "cislo_zakazky, cislo_org, nazev, stredisko, pocet_polozek, celkem_cena, celkem_hod, "
                "marze_proc, dat_porizeni, autor, resitel, splneno, poznamka) VALUES "
                "(:sd,:ik,:ck,:dk,:cz,:co,:nz,:st,:pp,:cc,:ch,:mp,:dp,:au,:re,:sp,:po)"), batch)
        s.commit()
        return {"ok": True, "zapsano": len(batch)}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-kalk-pol")
async def sync_ec_kalk_pol(request: Request):
    """Položky kalkulací EC z DB_EC (EC_KalkulacePolozky, Marti 25.6.2026): BOM výroby
    rozváděčů (RegCis, Bezeichnung, PocetKusu, ceny, Objednano/Vydano, dodavatel,
    zakázka). Keyset stránkování po 5000 (26k řádků). DELETE+INSERT = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    base = (
        "SELECT TOP 5000 p.ID, p.IDHlav id_kalk, p.Pos, p.RegCis, p.Bezeichnung nazev, p.Vyrobce, "
        "p.PocetKusu, p.JCenaEUR, p.Einheitpreis, p.GesamtPreis, p.Dodavatel, RTRIM(p.CisloZakazky) cislo_zakazky, "
        "p.Objednano, p.Vydano, p.Arbeitstunden, p.Hmotnost "
        "FROM EC_KalkulacePolozky p JOIN EC_KalkulaceHlav k ON k.ID=p.IDHlav "
        "JOIN TabDokladyZbozi d ON d.ID=k.IDDoklad "
        "WHERE d.RadaDokladu='910' AND YEAR(d.DatPorizeni) IN (2025,2026) AND p.ID > %d "
        "ORDER BY p.ID")
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_kalkulace_pol"))
        total = 0
        last_id = 0
        ins = _t(
            "INSERT INTO tenant.ec_kalkulace_pol (id_kalk, pos, reg_cis, nazev, vyrobce, pocet_kusu, "
            "jcena_eur, einheitpreis, gesamt_preis, dodavatel, cislo_zakazky, objednano, vydano, "
            "arbeitstunden, hmotnost) VALUES "
            "(:ik,:po,:rc,:nz,:vy,:pk,:jc,:ei,:gp,:do,:cz,:ob,:vy2,:ar,:hm)")
        for _ in range(50):  # max 250k řádků, pojistka
            try:
                rows = _mcp_rows(base % last_id, "DB_EC")
            except Exception as exc:
                s.rollback()
                return JSONResponse({"ok": False, "error": "Helios (MCP) @%d: %s" % (last_id, str(exc)[:180])}, status_code=502)
            if not rows:
                break
            batch = [{
                "ik": _kalk_i(r.get("id_kalk")), "po": _kalk_i(r.get("pos")), "rc": _kalk_s(r.get("regcis")),
                "nz": _kalk_s(r.get("nazev")), "vy": _kalk_s(r.get("vyrobce")), "pk": _kalk_n(r.get("pocetkusu")),
                "jc": _kalk_n(r.get("jcenaeur")), "ei": _kalk_n(r.get("einheitpreis")), "gp": _kalk_n(r.get("gesamtpreis")),
                "do": _kalk_i(r.get("dodavatel")), "cz": _kalk_s(r.get("cislo_zakazky")), "ob": _kalk_n(r.get("objednano")),
                "vy2": _kalk_n(r.get("vydano")), "ar": _kalk_n(r.get("arbeitstunden")), "hm": _kalk_n(r.get("hmotnost"))}
                for r in rows]
            s.execute(ins, batch)
            total += len(batch)
            last_id = max(_kalk_i(r.get("id")) or 0 for r in rows)
            if len(rows) < 5000:
                break
        s.commit()
        return {"ok": True, "zapsano": total}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/kalkulace-pol")
async def kalkulace_pol(request: Request):
    """Položky jedné kalkulace (drill-down z hromady kalkulací)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        idk = int(request.query_params.get("id_kalk") or 0)
    except (TypeError, ValueError):
        idk = 0
    if not idk:
        return JSONResponse({"ok": False, "error": "chybí id_kalk"}, status_code=400)
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT pos, COALESCE(reg_cis,'') AS reg_cis, COALESCE(nazev,'') AS nazev, "
            "COALESCE(vyrobce,'') AS vyrobce, pocet_kusu, round(jcena_eur::numeric,2) AS jcena_eur, "
            "round(gesamt_preis::numeric,2) AS gesamt_preis, COALESCE(cislo_zakazky,'') AS zakazka, "
            "objednano, vydano FROM tenant.ec_kalkulace_pol WHERE id_kalk=:k "
            "ORDER BY pos NULLS LAST, id"), {"k": idk}).mappings().all()]
        for r in rows:
            for c in ("pocet_kusu", "jcena_eur", "gesamt_preis", "objednano", "vydano"):
                if r.get(c) is not None:
                    r[c] = float(r[c])
        return {"ok": True, "id_kalk": idk, "polozky": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-ec-pp")
async def sync_ec_pp(request: Request):
    """1:1 zrcadlo EC Přijatých poptávek z DB_EC (přehled 504, Marti 25.6.2026):
    rada 900 (poptávka od zákazníka), roky 2025-26. Z poptávky vzniká kalkulace +
    nabídka (910). cislo=PoradoveCislo, navazny_doklad = EC_GetDoklad(NavaznyDoklad).
    DELETE+INSERT řad 90% = čistý mirror."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _i(v):
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _s(v):
        v = (str(v).replace("\x00", "").strip() if v is not None else "")
        return v or None

    sql = (
        "SELECT d.ID, d.PoradoveCislo, d.RadaDokladu, d.DruhPohybuZbo, d.CisloOrg, o.Nazev, "
        "RTRIM(d.CisloZakazky) CisloZakazky, dbo.EC_GetDoklad(d.NavaznyDoklad) NavaznyDoklad, "
        "SUBSTRING(REPLACE(SUBSTRING(d.Poznamka,1,255),NCHAR(13)+NCHAR(10),NCHAR(32)),1,255) PopisDodavky, "
        "CONVERT(varchar(10),d.DatPorizeni,23) dp "
        "FROM TabDokladyZbozi d LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "WHERE d.RadaDokladu=900 AND d.PoradoveCislo>=0 AND YEAR(d.DatPorizeni) IN (2025,2026)")
    try:
        rows = _mcp_rows(sql, "DB_EC")
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "Helios (MCP): %s" % str(exc)[:200]}, status_code=502)
    s = _sess()
    try:
        s.execute(_t("DELETE FROM tenant.ec_doklad_zbozi WHERE rada LIKE '90%'"))
        n = 0
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.ec_doklad_zbozi (src_id, cislo, rada, druh_pohybu, cislo_org, cislo_zakazky, "
                "navazna_objednavka, nazev, popis_dodavky, dat_porizeni) "
                "VALUES (:sid,:c,:r,:dph,:co,:cz,:nd,:n,:pop,:dp)"),
                {"sid": _i(r.get("id")), "c": _s(r.get("poradovecislo")), "r": _s(r.get("radadokladu")),
                 "dph": _i(r.get("druhpohybuzbo")), "co": _i(r.get("cisloorg")), "cz": _s(r.get("cislozakazky")),
                 "nd": _s(r.get("navaznydoklad")), "n": _s(r.get("nazev")), "pop": _s(r.get("popisdodavky")),
                 "dp": _s(r.get("dp"))})
            n += 1
        s.commit()
        return {"ok": True, "zapsano": n}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


def _kontace_sync(firma):
    """1:1 zrcadlo účetních kódů/kontací z Heliosu (Marti 25.6.2026). PRAVDA JE
    V HELIOSU, my podle ní jen účtujeme. Kontace (TabUKod) = řada+druh pohybu →
    sborník; řádky (TabRadekUKod) = předkontace MD/DAL per sazba DPH; skupiny
    (TabSkupUKod)+vazby (Tab1NUKod); per-rok platnost (TabUKodDef) + období
    (TabObdobi). firma 'ES' → DB_IS / tenant.es_*, 'EC' → DB_EC / tenant.ec_*."""
    src = "[DB_IS].dbo." if firma == "ES" else "dbo."
    P = "es_" if firma == "ES" else "ec_"

    def _b(v):
        return bool(v) if v not in (None, "") else None

    res = {}
    s = _sess()
    try:
        rows = _mcp_rows(
            "SELECT ID, CisloKontace, DruhPohybu, RadaDokladu, Nazev, Zakladni, Sbornik, "
            "CONVERT(varchar(10),DatumOd,23) datumod, CONVERT(varchar(10),DatumDo,23) datumdo "
            "FROM %sTabUKod" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%sukod" % P))
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.%sukod (id, cislokontace, druhpohybu, radadokladu, nazev, "
                "zakladni, sbornik, datumod, datumdo) VALUES (:i,:ck,:dp,:rd,:nz,:zk,:sb,:od,:do)" % P),
                {"i": _kalk_i(r.get("id")), "ck": _kalk_i(r.get("cislokontace")), "dp": _kalk_i(r.get("druhpohybu")),
                 "rd": _kalk_s(r.get("radadokladu")), "nz": _kalk_s(r.get("nazev")), "zk": _b(r.get("zakladni")),
                 "sb": _kalk_s(r.get("sbornik")), "od": _kalk_s(r.get("datumod")), "do": _kalk_s(r.get("datumdo"))})
        res["kontace"] = len(rows)
        rows = _mcp_rows(
            "SELECT Id, IDUKod, Radek, DruhRadku, SazbaDPH, UcetMD, UcetDAL, CiziMena, Zaporne, "
            "UplatnitDPH, CisloOrg, PomerKoef FROM %sTabRadekUKod" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%sukod_radek" % P))
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.%sukod_radek (id, idukod, radek, druhradku, sazbadph, ucetmd, "
                "ucetdal, cizimena, zaporne, uplatnitdph, cisloorg, pomerkoef) "
                "VALUES (:id,:iu,:rk,:dr,:sd,:md,:dal,:cm,:zp,:ud,:co,:pk)" % P),
                {"id": _kalk_i(r.get("id")), "iu": _kalk_i(r.get("idukod")), "rk": _kalk_i(r.get("radek")),
                 "dr": _kalk_i(r.get("druhradku")), "sd": _kalk_n(r.get("sazbadph")), "md": _kalk_s(r.get("ucetmd")),
                 "dal": _kalk_s(r.get("ucetdal")), "cm": _b(r.get("cizimena")), "zp": _b(r.get("zaporne")),
                 "ud": _b(r.get("uplatnitdph")), "co": _kalk_i(r.get("cisloorg")), "pk": _kalk_n(r.get("pomerkoef"))})
        res["radky"] = len(rows)
        rows = _mcp_rows("SELECT ID, Nazev FROM %sTabSkupUKod" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%sukod_skupina" % P))
        for r in rows:
            s.execute(_t("INSERT INTO tenant.%sukod_skupina (id, nazev) VALUES (:i,:n)" % P),
                      {"i": _kalk_i(r.get("id")), "n": _kalk_s(r.get("nazev"))})
        res["skupiny"] = len(rows)
        rows = _mcp_rows("SELECT IDSkup, CisloUKod, DruhPohybu, RadaDokladu FROM %sTab1NUKod" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%s1n_ukod" % P))
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.%s1n_ukod (idskup, cisloukod, druhpohybu, radadokladu) "
                "VALUES (:s,:c,:dp,:rd)" % P),
                {"s": _kalk_i(r.get("idskup")), "c": _kalk_i(r.get("cisloukod")),
                 "dp": _kalk_i(r.get("druhpohybu")), "rd": _kalk_s(r.get("radadokladu"))})
        res["vazby"] = len(rows)
        # per-rok platnost kontace (TabUKodDef: idukod × idobdobi → blokovano)
        rows = _mcp_rows("SELECT ID, IdUKod, IdObdobi, Blokovano FROM %sTabUKodDef" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%sukod_def" % P))
        for r in rows:
            s.execute(_t("INSERT INTO tenant.%sukod_def (id, idukod, idobdobi, blokovano) "
                         "VALUES (:i,:iu,:io,:bl)" % P),
                      {"i": _kalk_i(r.get("id")), "iu": _kalk_i(r.get("idukod")),
                       "io": _kalk_i(r.get("idobdobi")), "bl": _b(r.get("blokovano"))})
        res["def"] = len(rows)
        # účetní období (TabObdobi: idobdobi → rok)
        rows = _mcp_rows(
            "SELECT Id, Nazev, CONVERT(varchar(10),DatumOd,23) od, CONVERT(varchar(10),DatumDo,23) do "
            "FROM %sTabObdobi" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%sobdobi" % P))
        for r in rows:
            s.execute(_t("INSERT INTO tenant.%sobdobi (id, nazev, datumod, datumdo) VALUES (:i,:n,:od,:do)" % P),
                      {"i": _kalk_i(r.get("id")), "n": _kalk_s(r.get("nazev")),
                       "od": _kalk_s(r.get("od")), "do": _kalk_s(r.get("do"))})
        res["obdobi"] = len(rows)
        # sborníky (TabSbornik = účetní řady; DUD název + default MD/DAL)
        rows = _mcp_rows(
            "SELECT Id, Cislo, Nazev, DruhData, UcetMD, UcetDAL, Strana FROM %sTabSbornik" % src, "DB_EC")
        s.execute(_t("DELETE FROM tenant.%ssbornik" % P))
        for r in rows:
            s.execute(_t(
                "INSERT INTO tenant.%ssbornik (id, cislo, nazev, druhdata, ucetmd, ucetdal, strana) "
                "VALUES (:i,:c,:n,:dd,:md,:dal,:st)" % P),
                {"i": _kalk_i(r.get("id")), "c": _kalk_s(r.get("cislo")), "n": _kalk_s(r.get("nazev")),
                 "dd": _kalk_i(r.get("druhdata")), "md": _kalk_s(r.get("ucetmd")),
                 "dal": _kalk_s(r.get("ucetdal")), "st": _kalk_i(r.get("strana"))})
        res["sbornik"] = len(rows)
        s.commit()
        return res
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@bank_router.post("/app/uctovani/sync-es-kontace")
async def sync_es_kontace(request: Request):
    """1:1 zrcadlo ES kontací z Heliosu DB_IS (viz _kontace_sync)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        return {"ok": True, **_kontace_sync("ES")}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)


@bank_router.post("/app/uctovani/sync-ec-kontace")
async def sync_ec_kontace(request: Request):
    """1:1 zrcadlo EC kontací z Heliosu DB_EC (viz _kontace_sync)."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        return {"ok": True, **_kontace_sync("EC")}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)


@bank_router.get("/app/uctovani/kontace")
async def kontace_list(request: Request):
    """Účetní kódy/kontace (1:1 z Heliosu) — řada+druh pohybu → sborník + počet řádků MD/DAL."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma = (request.query_params.get("firma") or "ES").upper()
    _kp = "ec_" if firma == "EC" else "es_"
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT u.id, u.cislokontace, u.druhpohybu, COALESCE(u.radadokladu,'') AS rada, "
            "COALESCE(u.nazev,'') AS nazev, COALESCE(u.sbornik,'') AS sbornik, "
            "COALESCE(sb.nazev,'') AS sbornik_nazev, u.zakladni, "
            "to_char(u.datumod,'DD.MM.YYYY') AS datumod, to_char(u.datumdo,'DD.MM.YYYY') AS datumdo, "
            "(SELECT count(*) FROM tenant.{p}ukod_radek r WHERE r.idukod=u.id) AS radku "
            "FROM tenant.{p}ukod u LEFT JOIN tenant.{p}sbornik sb ON sb.cislo=u.sbornik "
            "ORDER BY u.cislokontace".format(p=_kp))).mappings().all()]
        return {"ok": True, "firma": firma, "kontace": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/kontace-skupiny")
async def kontace_skupiny(request: Request):
    """Skupiny účetních kódů (TabSkupUKod) + kontace v každé skupině (Tab1NUKod). 1:1 Helios."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma = (request.query_params.get("firma") or "ES").upper()
    _kp = "ec_" if firma == "EC" else "es_"
    s = _sess()
    try:
        skup = [dict(r) for r in s.execute(_t(
            "SELECT id, COALESCE(nazev,'') AS nazev FROM tenant.{p}ukod_skupina ORDER BY id".format(p=_kp))).mappings().all()]
        links = [dict(r) for r in s.execute(_t(
            "SELECT l.idskup, l.cisloukod, COALESCE(u.nazev,'') AS nazev, COALESCE(u.radadokladu,'') AS rada, "
            "COALESCE(u.sbornik,'') AS sbornik, u.id AS idukod "
            "FROM tenant.{p}1n_ukod l LEFT JOIN tenant.{p}ukod u ON u.cislokontace=l.cisloukod "
            "ORDER BY l.idskup, l.cisloukod".format(p=_kp))).mappings().all()]
        by = {}
        for l in links:
            by.setdefault(l["idskup"], []).append(l)
        for g in skup:
            g["kontace"] = by.get(g["id"], [])
        return {"ok": True, "firma": firma, "skupiny": skup}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


@bank_router.get("/app/uctovani/kontace-radky")
async def kontace_radky(request: Request):
    """Řádky jedné kontace (předkontace MD/DAL per sazba DPH) — drill-down."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        idu = int(request.query_params.get("idukod") or request.query_params.get("src_id_ukod") or 0)
    except (TypeError, ValueError):
        idu = 0
    firma = (request.query_params.get("firma") or "ES").upper()
    _kp = "ec_" if firma == "EC" else "es_"
    s = _sess()
    try:
        rows = [dict(r) for r in s.execute(_t(
            "SELECT radek, druhradku, sazbadph, COALESCE(ucetmd,'') AS ucetmd, "
            "COALESCE(ucetdal,'') AS ucetdal, cizimena, zaporne, uplatnitdph "
            "FROM tenant.%sukod_radek WHERE idukod=:i ORDER BY radek" % _kp), {"i": idu}).mappings().all()]
        for r in rows:
            if r.get("sazbadph") is not None:
                r["sazbadph"] = float(r["sazbadph"])
        return {"ok": True, "radky": rows}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# ════════════════════════════════════════════════════════════════════
# Automatický scheduler výpisů (Claude 8.7.2026) — bez zásahu do router.py.
# Lehké vlákno startující při importu modulu. Bezpečné proti dvojímu běhu
# (blue-green A+B) přes PG advisory lock držený po celou dobu sync + kontrolu
# stáří posledního běhu (bank_api_log 'sync_all') + per-proces throttle.
# ════════════════════════════════════════════════════════════════════
import time as _time_mod

_BANK_SYNC_LOCK_ID = 778812
_BANK_SYNC_STARTED = [False]
_BANK_SYNC_LAST_MONO = [0.0]
_BANK_SYNC_MIN_S = 3300   # ~55 min


def _bank_sync_tick():
    now_mono = _time_mod.monotonic()
    if _BANK_SYNC_LAST_MONO[0] and (now_mono - _BANK_SYNC_LAST_MONO[0]) < _BANK_SYNC_MIN_S:
        return
    from core.database_data import get_data_session as _g
    s = _g()
    got = False
    try:
        got = s.execute(_t("SELECT pg_try_advisory_lock(:k)"), {"k": _BANK_SYNC_LOCK_ID}).scalar()
        if not got:
            return
        # cross-instance freshness dle posledního zalogovaného sync_all
        try:
            last = s.execute(_t("SELECT max(created_at) FROM tenant.bank_api_log "
                                "WHERE operace='sync_all'")).scalar()
            if last is not None:
                import datetime as _dt
                if (_dt.datetime.now(getattr(last, "tzinfo", None)) - last).total_seconds() < _BANK_SYNC_MIN_S:
                    _BANK_SYNC_LAST_MONO[0] = now_mono
                    return
        except Exception:
            pass
        sync_all_tx()
        _BANK_SYNC_LAST_MONO[0] = now_mono
        try:
            _log(s, None, None, "sync_all", "sched", "system", "OK")
            s.commit()
        except Exception:
            pass
    finally:
        if got:
            try:
                s.execute(_t("SELECT pg_advisory_unlock(:k)"), {"k": _BANK_SYNC_LOCK_ID})
                s.commit()
            except Exception:
                pass
        s.close()


def _bank_sync_loop():
    _time_mod.sleep(120)   # nech app nabootovat
    while True:
        try:
            _bank_sync_tick()
        except Exception:
            pass
        _time_mod.sleep(900)   # kontrola co 15 min; reálný sync ~1×/hod dle stáří


def _start_bank_sync_scheduler():
    if _BANK_SYNC_STARTED[0]:
        return
    _BANK_SYNC_STARTED[0] = True
    try:
        import os as _osx
        # JEN na primáru — na blue-green sekundáru (adresář STRATEGIE-prev) scheduler NEspouštěj
        # (stejně jako att_sync/mirror v main.py lifespan; jinak by po povýšení B běžel 2×). 8.7.
        if "prev" in _osx.path.abspath(__file__).lower():
            return
        import threading as _thr
        _thr.Thread(target=_bank_sync_loop, daemon=True, name="bank-sync").start()
    except Exception:
        pass


_start_bank_sync_scheduler()
