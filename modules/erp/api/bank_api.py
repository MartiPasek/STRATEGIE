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

        # účty: smaž a vlož znovu (jednoduchý sync)
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
