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
from fastapi.responses import JSONResponse
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
    from modules.erp.api.router import is_marti_parent
    try:
        return bool(is_marti_parent(uid))
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


def _rb_call(bundle: dict, method: str, path: str, params=None, json_body=None, accept=None, timeout=40):
    """mTLS volání na RB. Cert z trezoru → ephemeral temp PEM (smaže se hned). Vrací requests.Response."""
    import requests, tempfile, os, uuid
    cert_pem, key_pem = _p12_to_pem(bundle.get("p12_b64") or "", bundle.get("password") or "")
    cf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); cf.write(cert_pem); cf.close()
    kf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); kf.write(key_pem); kf.close()
    try:
        headers = {"X-IBM-Client-Id": bundle.get("client_id") or "", "X-Request-Id": uuid.uuid4().hex[:60]}
        if accept:
            headers["Accept"] = accept
        return requests.request(method, _RB_BASE + path, headers=headers, params=params,
                                json=json_body, cert=(cf.name, kf.name), timeout=timeout)
    finally:
        for p in (cf.name, kf.name):
            try:
                os.unlink(p)
            except Exception:
                pass


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


@bank_router.post("/app/bank/parovat")
def bank_parovat(request: Request):
    """Spustí párovací engine nad bank_transaction_raw. Naplní par_* (metoda/řada/zakázka/
    kategorie/doklad). Vrací souhrn. Parent-only."""
    uid = _uid(request)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
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
        s.commit()
        # souhrn
        celkem = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw")).scalar()
        by_met = [dict(r) for r in s.execute(_t(
            "SELECT COALESCE(par_metoda,'(nenaparovano)') AS metoda, COALESCE(par_doklad_rada,'') AS rada, "
            "count(*) AS pocet, round(sum(abs(castka))) AS objem "
            "FROM tenant.bank_transaction_raw GROUP BY 1,2 ORDER BY pocet DESC")).mappings().all()]
        naparovano = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw WHERE par_metoda IS NOT NULL")).scalar()
        se_zak = s.execute(_t("SELECT count(*) FROM tenant.bank_transaction_raw WHERE par_zakazka IS NOT NULL")).scalar()
        return {"ok": True, "celkem": celkem, "naparovano": naparovano, "se_zakazkou": se_zak,
                "rozpad": by_met}
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}, status_code=500)
    finally:
        s.close()


# ── Systém pokladen + kartových účtů (zrcadlo Helios TabDruhPokladen) ──
def _mcp_rows(sql: str, db_name: str):
    """Read přes EUROSOFT MCP. Vrátí list dictů (lower-case klíče)."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupné")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": db_name}, conversation_id=None)
    r = _json.loads(raw) if isinstance(raw, str) else raw
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
        return {"ok": True, "pokladny": pok, "karty": karty, "kartove_ucty": kartove_ucty}
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
