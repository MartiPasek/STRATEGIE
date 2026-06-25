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
        def cnt(sql, p=None):
            r = s.execute(_t(sql), p or {}).mappings().first()
            return {"ks": r["c"], "objem": float(r["o"] or 0)}
        fp = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM tenant.ec_doklad_zbozi WHERE rada LIKE '5%'")
        fv = cnt("SELECT count(*) c, COALESCE(round(sum(suma_bez_dph)),0) o FROM tenant.ec_doklad_zbozi WHERE rada LIKE '6%'")
        bk = cnt("SELECT count(*) c, COALESCE(round(sum(abs(castka))),0) o FROM tenant.bank_transaction_raw")
        pk = cnt("SELECT count(*) c, 0 o FROM tenant.ucet_pokladna WHERE tenant_id=:tn", {"tn": _TENANT})
        return {"ok": True, "hromady": [
            {"kod": "fp", "ikona": "📥", "nazev": "Přijaté faktury (FP)", "ks": fp["ks"], "objem": fp["objem"]},
            {"kod": "fv", "ikona": "📤", "nazev": "Vydané faktury (FV)", "ks": fv["ks"], "objem": fv["objem"]},
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
    s = _sess()
    try:
        if typ in ("fp", "fv"):
            rl = "5%" if typ == "fp" else "6%"
            rows = [dict(r) for r in s.execute(_t(
                "SELECT cislo, rada, COALESCE(nazev,'') AS nazev, mena, round(suma_bez_dph) AS castka, "
                "cislo_org, COALESCE(cislo_zakazky,'') AS zakazka, COALESCE(stav_fakturace,'') AS stav "
                "FROM tenant.ec_doklad_zbozi WHERE rada LIKE :rl ORDER BY cislo DESC LIMIT 200"),
                {"rl": rl}).mappings().all()]
        elif typ == "banka":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT to_char(datum,'DD.MM.YYYY') AS datum, ext_id AS doklad, round(castka) AS castka, mena, "
                "COALESCE(vs,'') AS vs, smer, left(COALESCE(zprava,''),50) AS zprava "
                "FROM tenant.bank_transaction_raw ORDER BY datum DESC LIMIT 200")).mappings().all()]
        elif typ == "pokladna":
            rows = [dict(r) for r in s.execute(_t(
                "SELECT cislo, nazev, mena, typ, COALESCE(ucet_md,'') AS ucet FROM tenant.ucet_pokladna "
                "WHERE tenant_id=:tn ORDER BY firma, cislo"), {"tn": _TENANT}).mappings().all()]
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
