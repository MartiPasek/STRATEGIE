"""
Siemens OCI integrace (C23, 26.-27.7.2026) — dostupnost + dodaci termin + cena dle MLFB.
Cte prihlasovaci udaje z trezoru (tenant.user_secret, Fernet), vola SiePortal OCI
BACKGROUND_SEARCH. OVERENO 27.7.2026: vraci NEW_ITEM-* vc. LEADTIME (dodaci lhuta ve
dnech), PRICE, CURRENCY, DESCRIPTION, LONGTEXT, VENDORMAT (=MLFB). Heslo se NIKDY
nevraci ani neloguje. Cockpit-only (_is_cockpit). Vola SERVER (sit + Fernet), ne Claude.

Endpointy:
  POST /app/oci/lookup  -> {ok, mlfb, exact:{...}, count, items:[...]}  (ostra funkce)
  POST /app/oci/probe   -> syrove odpovedi (debug: LOGIN/BACKGROUND_SEARCH/VALIDATE/QUANTITYCHECK)

Pozn.: Siemens mall je za Akamai bot-ochranou -> nutne realisticke hlavicky prohlizece,
jinak 403. OCI odpoved je HTML formular se skrytymi NEW_ITEM-* poli (parsujeme primo,
auto-submit na HOOK_URL nepotrebujeme).
"""
from __future__ import annotations
import re as _re
import html as _html
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

oci_router = APIRouter(prefix="/api/v1/erp", tags=["oci"])

_HOOK = "https://app.strategie-ai.com/oci-return"
_BROWSER_HDRS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
    "Referer": "https://mall.industry.siemens.com/",
    "Origin": "https://mall.industry.siemens.com",
    "Content-Type": "application/x-www-form-urlencoded",
}


def _read_cred(s):
    """Vrati (username, url, secret_enc) polozky OCI z trezoru, nebo None."""
    from sqlalchemy import text as _t
    return s.execute(_t(
        "SELECT username, url, secret_enc FROM tenant.user_secret "
        "WHERE tenant_id=2 AND (label ILIKE '%oci%' OR label ILIKE '%sieportal%' "
        "OR label ILIKE '%siemens%') ORDER BY id DESC LIMIT 1")).first()


def _parse_fields(htmlstr: str) -> dict:
    """Vytahni skryta <input name='NEW_ITEM-...' value='...'> pole (oba poradi atributu)."""
    out = {}
    if not htmlstr:
        return out
    for m in _re.finditer(
            r'(?is)<input\b[^>]*?\bname=["\'](NEW_ITEM-[^"\']+)["\'][^>]*?\bvalue=["\']([^"\']*)["\']', htmlstr):
        out[m.group(1)] = _html.unescape(m.group(2))
    for m in _re.finditer(
            r'(?is)<input\b[^>]*?\bvalue=["\']([^"\']*)["\'][^>]*?\bname=["\'](NEW_ITEM-[^"\']+)["\']', htmlstr):
        out.setdefault(m.group(2), _html.unescape(m.group(1)))
    return out


def _num(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None


def _group_items(fields: dict) -> list:
    """NEW_ITEM-FIELD[n] + NEW_ITEM-LONGTEXT_n:132[] -> seznam polozek dle indexu."""
    items = {}
    for k, v in fields.items():
        m = _re.match(r'NEW_ITEM-([A-Za-z_]+)\[(\d+)\]$', k)
        if m:
            items.setdefault(int(m.group(2)), {})[m.group(1).upper()] = v
            continue
        m2 = _re.match(r'NEW_ITEM-LONGTEXT_(\d+):\d+\[\]$', k)
        if m2:
            items.setdefault(int(m2.group(1)), {})["LONGTEXT"] = v
    out = []
    for idx in sorted(items):
        it = items[idx]
        lt = str(it.get("LEADTIME", "")).strip()
        out.append({
            "mlfb": it.get("VENDORMAT", ""),
            "description": it.get("DESCRIPTION", ""),
            "longtext": it.get("LONGTEXT", ""),
            "price": _num(it.get("PRICE")),
            "currency": it.get("CURRENCY", ""),
            "price_unit": it.get("PRICEUNIT", ""),
            "unit": it.get("UNIT", ""),
            "leadtime_days": (int(lt) if lt.isdigit() else lt),
        })
    return out


async def _auth_cockpit(req):
    """Vrati (uid, err_json). err_json != None => vrat ho rovnou."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return None, JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return uid, None


@oci_router.post("/app/oci/lookup")
async def oci_lookup(req: Request) -> JSONResponse:
    from modules.erp.api.router import _att_session, _vault_fernet, _is_cockpit
    uid, err = await _auth_cockpit(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        b = {}
    mlfb = str((b or {}).get("mlfb") or "").strip()
    if not mlfb:
        return JSONResponse({"ok": False, "error": "no_mlfb", "note": "Zadej MLFB dilu."})
    f = _vault_fernet()
    if f is None:
        return JSONResponse({"ok": False, "error": "vault_not_configured"})
    cm, s = _att_session()
    try:
        if not _is_cockpit(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden",
                                 "note": "Jen cockpit (rodice / Petra / Sarka)."}, status_code=403)
        row = _read_cred(s)
    finally:
        cm.__exit__(None, None, None)
    if not row:
        return JSONResponse({"ok": False, "error": "cred_not_found",
                             "note": "V trezoru neni polozka se Siemens/OCI/SiePortal v nazvu."})
    username = row[0] or ""
    url = (row[1] or "").strip()
    try:
        password = f.decrypt((row[2] or "").encode()).decode()
    except Exception:
        return JSONResponse({"ok": False, "error": "decrypt_failed"})
    if not url:
        return JSONResponse({"ok": False, "error": "no_url"})

    import requests as _rq
    params = {"USERNAME": username, "PASSWORD": password, "HOOK_URL": _HOOK,
              "OCI_VERSION": "5.0", "returntarget": "_top",
              "FUNCTION": "BACKGROUND_SEARCH", "SEARCHSTRING": mlfb}
    try:
        r = _rq.post(url, data=params, headers=_BROWSER_HDRS, timeout=15, allow_redirects=True)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": "http_error", "note": str(exc)[:200]})
    if r.status_code != 200:
        return JSONResponse({"ok": False, "error": "http_%d" % r.status_code,
                             "note": "Siemens vratil HTTP %d." % r.status_code})
    items = _group_items(_parse_fields(r.text or ""))
    up = mlfb.upper()
    exact = next((x for x in items if (x.get("mlfb") or "").upper() == up), None)
    return JSONResponse({"ok": True, "mlfb": mlfb, "exact": exact,
                         "count": len(items), "items": items})


# (nazev, extra) — "%MLFB%" se nahradi zadanym MLFB
_OCI_ATTEMPTS = [
    ("BACKGROUND_SEARCH", {"FUNCTION": "BACKGROUND_SEARCH", "SEARCHSTRING": "%MLFB%"}),
    ("VALIDATE", {"FUNCTION": "VALIDATE", "PRODUCTID": "%MLFB%", "QUANTITY": "1"}),
    ("QUANTITYCHECK", {"FUNCTION": "QUANTITYCHECK", "EXT_PRODUCT_ID": "%MLFB%", "QUANTITY": "1"}),
]


@oci_router.post("/app/oci/probe")
async def oci_probe(req: Request) -> JSONResponse:
    """Debug: syrove odpovedi vice OCI funkci — heslo se redaktuje na ***."""
    from modules.erp.api.router import _att_session, _vault_fernet, _is_cockpit
    uid, err = await _auth_cockpit(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        b = {}
    mlfb = str((b or {}).get("mlfb") or "").strip()
    f = _vault_fernet()
    if f is None:
        return JSONResponse({"ok": False, "error": "vault_not_configured"})
    cm, s = _att_session()
    try:
        if not _is_cockpit(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        row = _read_cred(s)
    finally:
        cm.__exit__(None, None, None)
    if not row:
        return JSONResponse({"ok": False, "error": "cred_not_found"})
    username = row[0] or ""
    url = (row[1] or "").strip()
    try:
        password = f.decrypt((row[2] or "").encode()).decode()
    except Exception:
        return JSONResponse({"ok": False, "error": "decrypt_failed"})
    if not url:
        return JSONResponse({"ok": False, "error": "no_url"})

    import requests as _rq

    def _redact(t):
        return (t.replace(password, "***") if (t and password) else t)

    def _vis(h):
        if not h:
            return ""
        h = _re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
        h = _re.sub(r"(?s)<[^>]+>", " ", h)
        return _redact(_re.sub(r"\s+", " ", h).strip()[:800])

    def _title(h):
        m = _re.search(r"(?is)<title[^>]*>(.*?)</title>", h or "")
        return (m.group(1).strip()[:140] if m else "")

    common = {"USERNAME": username, "PASSWORD": password, "HOOK_URL": _HOOK,
              "OCI_VERSION": "5.0", "returntarget": "_top"}
    results = []
    for name, extra in ([("LOGIN", {})] + _OCI_ATTEMPTS):
        params = dict(common)
        if name != "LOGIN":
            if not mlfb:
                results.append({"function": name, "skipped": "chybi MLFB"})
                continue
            params.update({k: (mlfb if v == "%MLFB%" else v) for k, v in extra.items()})
        try:
            r = _rq.post(url, data=params, headers=_BROWSER_HDRS, timeout=12, allow_redirects=True)
            body = r.text or ""
            results.append({
                "function": name, "http_status": r.status_code,
                "content_type": r.headers.get("content-type", ""),
                "final_url": str(r.url), "body_len": len(body),
                "title": _title(body), "text": _vis(body),
                "oci_fields": _parse_fields(body), "excerpt": _redact(body[:800]),
            })
        except Exception as exc:
            results.append({"function": name, "error": _redact(str(exc))[:300]})
    return JSONResponse({"ok": True, "username": username, "url": url,
                         "mlfb": mlfb, "results": results})
