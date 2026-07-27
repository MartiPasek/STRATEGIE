"""
Siemens OCI5 sonda (C23, 26.7.2026) — empiricky zjisti, co SiePortal OCI endpoint
opravdu umi. Precte prihlasovaci udaje z trezoru (tenant.user_secret, Fernet),
zavola Siemens OCI s background funkcemi (LOGIN / BACKGROUND_SEARCH / VALIDATE /
QUANTITYCHECK) na zadane MLFB a vrati SYROVE odpovedi (zkraceny excerpt).
HESLO se NIKDY nevraci ani neloguje — v excerptech i chybach se redaktuje na ***.
Cockpit/parent-only (_is_cockpit). Vola server (ma sit + Fernet klic), ne Claude.
"""
from __future__ import annotations
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

oci_router = APIRouter(prefix="/api/v1/erp", tags=["oci-probe"])

# (nazev, extra parametry) — "%MLFB%" se nahradi zadanym MLFB
_OCI_ATTEMPTS = [
    ("BACKGROUND_SEARCH", {"FUNCTION": "BACKGROUND_SEARCH", "SEARCHSTRING": "%MLFB%"}),
    ("VALIDATE", {"FUNCTION": "VALIDATE", "PRODUCTID": "%MLFB%", "QUANTITY": "1"}),
    ("QUANTITYCHECK", {"FUNCTION": "QUANTITYCHECK", "EXT_PRODUCT_ID": "%MLFB%", "QUANTITY": "1"}),
]

# Siemens mall je za Akamai bot-ochranou → serverovy request bez UA dostane 403.
# Posilame realisticke hlavicky prohlizece (nejnizsi tier Akamai to obvykle pusti).
_BROWSER_HDRS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
    "Referer": "https://mall.industry.siemens.com/",
    "Origin": "https://mall.industry.siemens.com",
    "Content-Type": "application/x-www-form-urlencoded",
}


@oci_router.post("/app/oci/probe")
async def oci_probe(req: Request) -> JSONResponse:
    from modules.erp.api.router import (
        _uid_from_token_or_cookie, _att_session, _vault_fernet, _is_cockpit)
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    mlfb = str((b or {}).get("mlfb") or "").strip()
    from sqlalchemy import text as _t
    f = _vault_fernet()
    if f is None:
        return JSONResponse({"ok": False, "error": "vault_not_configured"})
    cm, s = _att_session()
    try:
        if not _is_cockpit(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden",
                                 "note": "Jen cockpit (rodice / Petra / Sarka)."}, status_code=403)
        row = s.execute(_t(
            "SELECT username, url, secret_enc FROM tenant.user_secret "
            "WHERE tenant_id=2 AND (label ILIKE '%oci%' OR label ILIKE '%sieportal%' "
            "OR label ILIKE '%siemens%') ORDER BY id DESC LIMIT 1")).first()
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
        return JSONResponse({"ok": False, "error": "decrypt_failed",
                             "note": "Sifrovaci klic na serveru neodpovida."})
    if not url:
        return JSONResponse({"ok": False, "error": "no_url",
                             "note": "Polozka v trezoru nema vyplnene URL."})

    import requests as _rq

    def _redact(txt):
        if not txt:
            return txt
        if password:
            txt = txt.replace(password, "***")
        return txt

    base = {"USERNAME": username, "PASSWORD": password}
    results = []
    for name, extra in ([("LOGIN", {})] + _OCI_ATTEMPTS):
        params = dict(base)
        if name == "LOGIN":
            params.update({"HOOK_URL": "https://app.strategie-ai.com/oci-return",
                           "OCI_VERSION": "5.0", "returntarget": "_top"})
        else:
            if not mlfb:
                results.append({"function": name, "skipped": "chybi MLFB"})
                continue
            params.update({k: (mlfb if v == "%MLFB%" else v) for k, v in extra.items()})
        try:
            r = _rq.post(url, data=params, headers=_BROWSER_HDRS, timeout=12, allow_redirects=True)
            body = r.text or ""
            results.append({
                "function": name,
                "http_status": r.status_code,
                "content_type": r.headers.get("content-type", ""),
                "final_url": str(r.url),
                "body_len": len(body),
                "excerpt": _redact(body[:1800]),
            })
        except Exception as exc:
            results.append({"function": name, "error": _redact(str(exc))[:300]})
    return JSONResponse({"ok": True, "username": username, "url": url,
                         "mlfb": mlfb, "results": results})
