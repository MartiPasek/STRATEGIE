"""CardDAV read-only server — caller-ID sync aktivní sady (Fáze 1.5, 2.6.2026).

Vystavuje user.carddav_active_contact jako CardDAV adresáře, které si telefon
(Android přes DAVx5, iOS nativně) nasynchronizuje → příchozí hovor ukáže jméno.

Read-only z pohledu telefonu (zrcadlí server). Oddělené kolekce 'real' a
'potential' (Marti's B). Auth: HTTP Basic, password = app-specific token
(user.carddav_token, sha256 hash). Username = login_name (kosmetické, identita
je z tokenu).

URL strom (mount /carddav):
  /.well-known/carddav            → 301 /carddav/
  /carddav/                       → PROPFIND: current-user-principal
  /carddav/p/{uid}/               → PROPFIND: principal (addressbook-home-set)
  /carddav/ab/{uid}/              → PROPFIND Depth:1: seznam adresářů (real/potential)
  /carddav/ab/{uid}/{book}/       → PROPFIND Depth:1: seznam vCard; REPORT: multiget/sync
  /carddav/ab/{uid}/{book}/{id}.vcf → GET vCard

POZN: CardDAV klienti jsou citliví na přesný XML. v1 = nejčastější subset
(DAVx5 + iOS). Ladí se podle logů klienta.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from xml.sax.saxutils import escape as _xesc

from fastapi import APIRouter, Request, Response
from fastapi.responses import (HTMLResponse, JSONResponse, PlainTextResponse,
                               RedirectResponse)
from sqlalchemy import text as _sql

logger = logging.getLogger("strategie.carddav")

carddav_router = APIRouter()

# Správa tokenů (F1.6) — session auth, mount /api/v1/erp/carddav.
carddav_mgmt_router = APIRouter(prefix="/api/v1/erp/carddav", tags=["carddav-mgmt"])

# Bezpečnostní limity self-service.
_MAX_ACTIVE_TOKENS = 5  # kolik zařízení smí mít user současně připojeno

_NS = (
    'xmlns:d="DAV:" '
    'xmlns:card="urn:ietf:params:xml:ns:carddav" '
    'xmlns:cs="http://calendarserver.org/ns/"'
)
_BOOKS = ("real", "potential")
_BOOK_LABEL = {"real": "STRATEGIE — Reální klienti",
               "potential": "STRATEGIE — Potenciální klienti"}


# ── Auth ────────────────────────────────────────────────────────────────

def _auth_uid(request: Request) -> int | None:
    """Basic auth → token (password) → user_id z user.carddav_token."""
    auth = request.headers.get("authorization", "")
    if not auth[:6].lower() == "basic ":
        return None
    try:
        decoded = base64.b64decode(auth[6:].strip()).decode("utf-8", "replace")
    except Exception:
        return None
    _user, _sep, pwd = decoded.partition(":")
    if not pwd:
        return None
    th = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            'SELECT user_id FROM "user".carddav_token '
            'WHERE token_hash = :h AND revoked_at IS NULL'
        ), {"h": th}).first()
        if not row:
            return None
        s.execute(_sql('UPDATE "user".carddav_token SET last_used_at = now() '
                       'WHERE token_hash = :h'), {"h": th})
        s.commit()
        return int(row[0])
    except Exception as exc:
        logger.warning("[carddav auth] %s", exc)
        return None
    finally:
        s.close()


def _unauthorized() -> Response:
    return Response(status_code=401, headers={
        "WWW-Authenticate": 'Basic realm="STRATEGIE CardDAV"'})


# ── DB ──────────────────────────────────────────────────────────────────

def _fetch_book_rows(uid: int, book: str) -> list[dict]:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        rows = s.execute(_sql('''
            SELECT id, contact_ref, vcard_cache, last_active_at
            FROM "user".carddav_active_contact
            WHERE user_id = :uid AND addressbook = :book AND removed_at IS NULL
            ORDER BY id
        '''), {"uid": uid, "book": book}).mappings().all()
        return [dict(r) for r in rows]
    finally:
        s.close()


def _fetch_vcard(uid: int, rid: int) -> str | None:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            'SELECT vcard_cache FROM "user".carddav_active_contact '
            'WHERE id = :id AND user_id = :uid AND removed_at IS NULL'
        ), {"id": rid, "uid": uid}).first()
        return row[0] if row and row[0] else None
    finally:
        s.close()


def _etag(vcard: str | None) -> str:
    return '"' + hashlib.sha1((vcard or "").encode("utf-8")).hexdigest()[:16] + '"'


def _ctag(rows: list[dict]) -> str:
    h = hashlib.sha1()
    for r in rows:
        h.update(str(r["id"]).encode())
        h.update(str(r["last_active_at"]).encode())
        h.update((r.get("vcard_cache") or "").encode("utf-8"))
    return "ct-" + h.hexdigest()[:16]


# ── XML helpers ──────────────────────────────────────────────────────────

def _ms(body: str) -> Response:
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<d:multistatus ' + _NS + '>' + body + '</d:multistatus>')
    return Response(content=xml, status_code=207,
                    media_type='application/xml; charset=utf-8')


def _resp_ok(href: str, props: str) -> str:
    return ('<d:response><d:href>' + _xesc(href) + '</d:href>'
            '<d:propstat><d:prop>' + props + '</d:prop>'
            '<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>')


# ── Method dispatch ───────────────────────────────────────────────────────

@carddav_router.api_route("/.well-known/carddav",
                          methods=["GET", "PROPFIND", "OPTIONS"])
def well_known(request: Request):
    return RedirectResponse(url="/carddav/", status_code=301)


# ── QR handoff stránka pro telefon (F1.6/F1.7) ─────────────────────────────
# Veřejná (nonce je autorizace) — telefon ji otevře po naskenování QR z PC.
# Ukáže token + URL + login (každé s tlačítkem Kopírovat) + návod DAVx5/iOS.

def _handoff_page_html(d: dict) -> str:
    tok = _xesc(d.get("token_plain") or "")
    url = _xesc(d.get("carddav_url") or "")
    usr = _xesc(d.get("username") or "")
    lbl = _xesc(d.get("device_label") or "Telefon")
    server = (d.get("carddav_url") or "").replace("https://", "").replace(
        "http://", "").replace("/carddav/", "").rstrip("/")
    server = _xesc(server)

    def field(label, value, fid):
        return (
            '<div class="fld"><div class="lbl">' + label + '</div>'
            '<div class="row"><code id="' + fid + '">' + value + '</code>'
            '<button class="cp" data-t="' + fid + '">Kopírovat</button></div></div>')

    return (
        '<!doctype html><html lang="cs"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>STRATEGIE — připojení kontaktů</title><style>'
        '*{box-sizing:border-box}body{margin:0;font-family:-apple-system,'
        'Segoe UI,Roboto,sans-serif;background:#0f1620;color:#e8eef5;'
        'padding:18px 16px 40px;line-height:1.5}'
        '.card{max-width:520px;margin:0 auto}'
        'h1{font-size:19px;margin:4px 0 2px}.sub{color:#9fb0c4;font-size:13px;'
        'margin-bottom:16px}'
        '.fld{margin:10px 0}.lbl{font-size:12px;color:#9fb0c4;margin-bottom:3px}'
        '.row{display:flex;gap:8px;align-items:stretch}'
        'code{flex:1;background:#1a2531;border:1px solid #2c3a4c;border-radius:8px;'
        'padding:11px 12px;font-size:14px;color:#dbe6f2;word-break:break-all;'
        'display:flex;align-items:center}'
        '.cp{background:#e8b923;color:#1c2530;border:none;border-radius:8px;'
        'padding:0 16px;font-size:14px;font-weight:700;cursor:pointer;'
        'white-space:nowrap}'
        '.cp.ok{background:#2f9e6e;color:#fff}'
        'h2{font-size:15px;color:#7fd6c2;margin:20px 0 6px}'
        'ol{margin:0 0 8px 20px;padding:0}li{margin:4px 0;font-size:14px}'
        '.note{color:#8aa0b8;font-size:12.5px;margin-top:14px}'
        '.exp{color:#cdb87a;font-size:12px;margin-top:6px}'
        '</style></head><body><div class="card">'
        '<h1>📱 Připojení kontaktů STRATEGIE</h1>'
        '<div class="sub">Pro zařízení „' + lbl + '". Zkopíruj údaje níž do '
        'aplikace DAVx5 (Android) nebo do Nastavení → Kontakty (iPhone).</div>'
        + field("Adresa (URL)", url, "f_url")
        + field("Uživatel", usr, "f_usr")
        + field("Token (heslo)", tok, "f_tok")
        + '<div class="exp">⏱ Tato stránka je platná ~' + str(_HANDOFF_TTL_MIN)
        + ' minut. Token zadej do aplikace co nejdřív.</div>'
        '<h2>📱 Android</h2><ol>'
        '<li>Nainstaluj <b>DAVx5</b> (Google Play — malý jednorázový poplatek; '
        'nebo zdarma přes <b>F-Droid</b>).</li>'
        '<li>DAVx5 → <b>+</b> → <b>Přihlásit pomocí URL a uživ. jména</b>.</li>'
        '<li>URL = <b>Adresa</b> výše, Uživatel = <b>Uživatel</b> výše → Pokračovat.</li>'
        '<li>Heslo = <b>Token</b> výše → Přihlásit.</li>'
        '<li>Účet → <b>Metoda seskupování kontaktů</b> → <b>Skupiny jako kategorie (CATEGORIES)</b>.</li>'
        '<li><b>Obnovit seznam adresářů</b> → vyber <i>Reální / Potenciální klienti</i>.</li>'
        '<li><b>⟳ Synchronizovat</b> (nebo stáhni seznam dolů) — DAVx5 ukáže svoji sync notifikaci.</li>'
        '<li>Zapni <b>Synchronizace v pravidelných intervalech</b> + vyber <b>interval</b> (např. 1–4 h). '
        '<i>„VPN vyžaduje nadřazené připojení"</i> nech <b>vypnuté</b>.</li></ol>'
        '<h2>🍏 iPhone</h2><ol>'
        '<li>Nastavení → <b>Kontakty</b> → Účty → Přidat účet → Jiný → <b>CardDAV</b>.</li>'
        '<li>Server: <b>' + server + '</b></li>'
        '<li>Uživatel = <b>Uživatel</b>, Heslo = <b>Token</b> výše → Uložit.</li></ol>'
        '<div class="note">Sync je jednosměrný a jen pro čtení — telefon zrcadlí '
        'STRATEGII. Sada se doplňuje, jak voláš klientům.</div>'
        '</div><script>'
        'function cp(btn){var id=btn.getAttribute("data-t");'
        'var t=document.getElementById(id).textContent;'
        'function ok(){btn.textContent="✓ Zkopírováno";btn.classList.add("ok");'
        'setTimeout(function(){btn.textContent="Kopírovat";btn.classList.remove("ok");},1600);}'
        'try{if(navigator.clipboard&&navigator.clipboard.writeText){'
        'navigator.clipboard.writeText(t).then(ok,function(){fb(t,ok);});}'
        'else fb(t,ok);}catch(e){fb(t,ok);}}'
        'function fb(t,ok){try{var a=document.createElement("textarea");a.value=t;'
        'a.style.position="fixed";a.style.opacity="0";document.body.appendChild(a);'
        'a.select();document.execCommand("copy");a.remove();ok();}catch(e){}}'
        'document.querySelectorAll(".cp").forEach(function(b){'
        'b.addEventListener("click",function(){cp(b);});});'
        '</script></body></html>')


@carddav_router.get("/carddav-setup/{nonce}")
def carddav_setup_page(nonce: str) -> HTMLResponse:
    d = _fetch_handoff(nonce)
    if not d:
        return HTMLResponse(
            '<!doctype html><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<body style="font-family:sans-serif;background:#0f1620;color:#e8eef5;'
            'padding:30px;text-align:center;line-height:1.6">'
            '<h2>⏱ Odkaz vypršel</h2><p style="color:#9fb0c4">Tahle stránka už '
            'není platná. Ve STRATEGII vygeneruj nový přístup a naskenuj QR znovu.</p>'
            '</body>', status_code=404)
    return HTMLResponse(_handoff_page_html(d))


# ── Veřejná stránka pro spárování NAŠÍ appky (Android, i nepřihlášený telefon) ──
# Marti 6.6.2026: čerstvý telefon (nikdy nepřihlášený) si přes /app-pair appku
# nestáhne (download chce login). Tahle stránka je VEŘEJNÁ (nonce = autorizace),
# takže telefon: naskenuje QR → stáhne APK bez loginu → po instalaci spáruje.

def _app_setup_html(nonce: str, origin: str, deeplink: str, label: str) -> str:
    lbl = _xesc(label or "Telefon")
    dl = _xesc(deeplink)
    apk = "/app-setup/" + _xesc(nonce) + "/apk"
    return (
        '<!doctype html><html lang="cs"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>STRATEGIE Mobil — instalace</title><style>'
        '*{box-sizing:border-box}body{margin:0;font-family:-apple-system,Segoe UI,'
        'Roboto,sans-serif;background:#0f1620;color:#e8eef5;padding:20px 16px 40px;'
        'line-height:1.5}.card{max-width:520px;margin:0 auto}h1{font-size:20px;'
        'margin:4px 0 2px}.sub{color:#9fb0c4;font-size:13px;margin-bottom:18px}'
        '.btn{display:block;text-align:center;text-decoration:none;border-radius:10px;'
        'padding:14px;font-size:15px;font-weight:700;margin:10px 0}'
        '.dl{background:#e8b923;color:#1c2530}.pair{background:#1f3a2e;color:#cdeede;'
        'border:1px solid #3a7a4a}.step{background:#1a2531;border:1px solid #2c3a4c;'
        'border-radius:10px;padding:12px 14px;margin:10px 0;font-size:14px}'
        '.n{display:inline-block;background:#e8b923;color:#1c2530;width:22px;height:22px;'
        'border-radius:11px;text-align:center;line-height:22px;font-weight:700;'
        'margin-right:8px}.note{color:#8aa0b8;font-size:12.5px;margin-top:16px}'
        '</style></head><body><div class="card">'
        '<h1>📲 STRATEGIE Mobil</h1>'
        '<div class="sub">Instalace a spárování telefonu „' + lbl + '" — bez přihlašování.</div>'
        '<div class="step"><span class="n">1</span>Stáhni a nainstaluj appku '
        '(po stažení ťukni na soubor → Instalovat; povol „instalaci z tohoto zdroje").</div>'
        '<a class="btn dl" href="' + apk + '">⬇️ Stáhnout appku (APK)</a>'
        '<div class="step"><span class="n">2</span>Po instalaci appku otevři a '
        '<b>přihlas se svým účtem STRATEGIE</b> — tím se určí, čí telefon to je a '
        'jaká má práva. Pak appka nabídne spárování.</div>'
        '<div class="note">Jen pro <b>Android</b>. iPhone používá nativní kontakty (CardDAV) — '
        'tam se vrať do STRATEGIE a zvol „🍏 iPhone". Odkaz je platný ~' + str(_HANDOFF_TTL_MIN) +
        ' min.</div></div></body></html>')


@carddav_router.get("/app-setup/{nonce}")
def app_setup_page(nonce: str) -> HTMLResponse:
    d = _fetch_handoff(nonce)
    if not d:
        return HTMLResponse(
            '<!doctype html><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<body style="font-family:sans-serif;background:#0f1620;color:#e8eef5;'
            'padding:30px;text-align:center;line-height:1.6">'
            '<h2>⏱ Odkaz vypršel</h2><p style="color:#9fb0c4">Ve STRATEGII vygeneruj '
            'nové spárování a naskenuj QR znovu.</p></body>', status_code=404)
    url = d.get("carddav_url") or ""
    origin = url.replace("https://", "").replace("http://", "")
    origin = (url[:url.find("/carddav")] if "/carddav" in url else url).rstrip("/")
    tok = d.get("token_plain") or ""
    from urllib.parse import quote as _q
    deeplink = ("strategiemobil://pair?u=" + _q(origin, safe="") +
                "&t=" + _q(tok, safe="") + "&k=mobile")
    return HTMLResponse(_app_setup_html(nonce, origin, deeplink,
                                        d.get("device_label") or "Telefon"))


@carddav_router.get("/app-setup/{nonce}/apk")
def app_setup_apk(nonce: str):
    d = _fetch_handoff(nonce)
    if not d:
        return Response(status_code=404)
    import os as _os
    try:
        from modules.erp.api.router import _app_latest_row, _app_releases_dir
    except Exception as exc:
        logger.warning("[app-setup apk] import: %s", exc)
        return Response(status_code=500)
    row = _app_latest_row("mobile")
    fn = row.get("apk_file")
    if not fn:
        return Response(status_code=404)
    path = _os.path.join(_app_releases_dir("mobile"), fn)
    if not _os.path.isfile(path):
        return Response(status_code=404)
    from fastapi.responses import FileResponse as _FR
    return _FR(path, media_type="application/vnd.android.package-archive",
               filename="strategie-mobil.apk")


@carddav_router.api_route(
    "/carddav/{path:path}",
    methods=["OPTIONS", "PROPFIND", "REPORT", "GET", "HEAD"])
async def carddav_entry(path: str, request: Request):
    method = request.method.upper()

    if method == "OPTIONS":
        return Response(status_code=200, headers={
            "DAV": "1, 2, 3, addressbook",
            "Allow": "OPTIONS, GET, HEAD, PROPFIND, REPORT",
        })

    uid = _auth_uid(request)
    if uid is None:
        return _unauthorized()

    segs = [p for p in path.split("/") if p != ""]
    depth = request.headers.get("depth", "0")

    # /carddav/  → principal discovery
    if len(segs) == 0:
        if method == "PROPFIND":
            props = ('<d:current-user-principal><d:href>/carddav/p/'
                     + str(uid) + '/</d:href></d:current-user-principal>'
                     '<d:resourcetype><d:collection/></d:resourcetype>')
            return _ms(_resp_ok("/carddav/", props))
        return Response(status_code=405)

    # /carddav/p/{uid}/ → principal props
    if segs[0] == "p":
        if method == "PROPFIND":
            props = ('<d:resourcetype><d:principal/></d:resourcetype>'
                     '<d:displayname>STRATEGIE</d:displayname>'
                     '<card:addressbook-home-set><d:href>/carddav/ab/'
                     + str(uid) + '/</d:href></card:addressbook-home-set>'
                     '<d:current-user-principal><d:href>/carddav/p/'
                     + str(uid) + '/</d:href></d:current-user-principal>')
            return _ms(_resp_ok("/carddav/p/" + str(uid) + "/", props))
        return Response(status_code=405)

    # /carddav/ab/...
    if segs[0] == "ab":
        # /carddav/ab/{uid}/  → home (list addressbooks)
        if len(segs) == 2:
            if method == "PROPFIND":
                body = _resp_ok("/carddav/ab/" + str(uid) + "/",
                                '<d:resourcetype><d:collection/></d:resourcetype>'
                                '<d:displayname>STRATEGIE</d:displayname>')
                if depth != "0":
                    for b in _BOOKS:
                        rows = _fetch_book_rows(uid, b)
                        body += _resp_ok(
                            "/carddav/ab/" + str(uid) + "/" + b + "/",
                            '<d:resourcetype><d:collection/>'
                            '<card:addressbook/></d:resourcetype>'
                            '<d:displayname>' + _xesc(_BOOK_LABEL[b]) + '</d:displayname>'
                            '<cs:getctag>' + _ctag(rows) + '</cs:getctag>'
                            '<card:supported-address-data>'
                            '<card:address-data-type content-type="text/vcard" version="3.0"/>'
                            '</card:supported-address-data>')
                return _ms(body)
            return Response(status_code=405)

        # /carddav/ab/{uid}/{book}/  → addressbook collection
        if len(segs) == 3:
            book = segs[2]
            if book not in _BOOKS:
                return Response(status_code=404)
            rows = _fetch_book_rows(uid, book)
            base = "/carddav/ab/" + str(uid) + "/" + book + "/"

            if method == "PROPFIND":
                body = _resp_ok(base,
                    '<d:resourcetype><d:collection/><card:addressbook/></d:resourcetype>'
                    '<d:displayname>' + _xesc(_BOOK_LABEL[book]) + '</d:displayname>'
                    '<cs:getctag>' + _ctag(rows) + '</cs:getctag>')
                if depth != "0":
                    for r in rows:
                        href = base + str(r["id"]) + ".vcf"
                        body += _resp_ok(href,
                            '<d:resourcetype/>'
                            '<d:getetag>' + _etag(r.get("vcard_cache")) + '</d:getetag>'
                            '<d:getcontenttype>text/vcard; charset=utf-8</d:getcontenttype>')
                return _ms(body)

            if method == "REPORT":
                raw = (await request.body()).decode("utf-8", "replace")
                # addressbook-multiget: vrať vCardy pro <d:href> v těle.
                if "addressbook-multiget" in raw or "<d:href" in raw or "<href" in raw:
                    import re as _re
                    hrefs = _re.findall(r"<[^>]*href[^>]*>([^<]+)</[^>]*href>", raw)
                    by_id = {r["id"]: r for r in rows}
                    body = ""
                    for h in hrefs:
                        m = _re.search(r"/(\d+)\.vcf", h)
                        if not m:
                            continue
                        r = by_id.get(int(m.group(1)))
                        if not r:
                            body += ('<d:response><d:href>' + _xesc(h) + '</d:href>'
                                     '<d:status>HTTP/1.1 404 Not Found</d:status></d:response>')
                            continue
                        body += _resp_ok(h,
                            '<d:getetag>' + _etag(r.get("vcard_cache")) + '</d:getetag>'
                            '<card:address-data>' + _xesc(r.get("vcard_cache") or "")
                            + '</card:address-data>')
                    return _ms(body)
                # addressbook-query / sync-collection → vrať vše.
                body = ""
                for r in rows:
                    href = base + str(r["id"]) + ".vcf"
                    body += _resp_ok(href,
                        '<d:getetag>' + _etag(r.get("vcard_cache")) + '</d:getetag>'
                        '<card:address-data>' + _xesc(r.get("vcard_cache") or "")
                        + '</card:address-data>')
                return _ms(body)
            return Response(status_code=405)

        # /carddav/ab/{uid}/{book}/{id}.vcf  → GET vCard
        if len(segs) == 4 and segs[3].endswith(".vcf"):
            try:
                rid = int(segs[3][:-4])
            except ValueError:
                return Response(status_code=404)
            if method in ("GET", "HEAD"):
                vc = _fetch_vcard(uid, rid)
                if vc is None:
                    return Response(status_code=404)
                return Response(content=("" if method == "HEAD" else vc),
                                media_type="text/vcard; charset=utf-8",
                                headers={"ETag": _etag(vc)})
            if method == "PROPFIND":
                vc = _fetch_vcard(uid, rid)
                if vc is None:
                    return Response(status_code=404)
                href = "/carddav/ab/" + str(uid) + "/" + segs[2] + "/" + segs[3]
                return _ms(_resp_ok(href,
                    '<d:getetag>' + _etag(vc) + '</d:getetag>'
                    '<d:getcontenttype>text/vcard; charset=utf-8</d:getcontenttype>'))
            return Response(status_code=405)

    return Response(status_code=404)


# ══════════════════════════════════════════════════════════════════════════
# F1.6 — Self-service správa tokenů (přihlášený user spravuje SVÁ zařízení)
# ══════════════════════════════════════════════════════════════════════════
#  GET  /api/v1/erp/carddav/info     → údaje pro připojení (URL, login, počet
#                                       kontaktů, návod), bez tajemství
#  GET  /api/v1/erp/carddav/tokens   → seznam zařízení usera (bez tokenu)
#  POST /api/v1/erp/carddav/token    → vygeneruje token (vrátí PLAINTEXT 1×)
#  POST /api/v1/erp/carddav/token/{id}/revoke → odpojí zařízení
#
# Auth: session cookie user_id (každý spravuje JEN svá zařízení). Token sám
# se nikdy nečte z DB (drží se jen sha256 hash) — proto se vrací jedenkrát
# při vytvoření; jinak nutno vygenerovat nový.


def _session_uid(request: Request) -> int | None:
    """Přihlášený user z cookie (stejná identita jako ERP/Chat)."""
    raw = request.cookies.get("user_id")
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _carddav_base(request: Request) -> str:
    """Veřejná base URL pro CardDAV (z hostu requestu; prod = strategie-ai.com).

    Respektuje reverse-proxy hlavičky (Caddy) a vynutí https mimo localhost.
    """
    host = (request.headers.get("x-forwarded-host")
            or request.headers.get("host") or "").strip()
    if not host:
        from core.config import settings
        return (settings.app_base_url or "https://strategie-ai.com").rstrip("/")
    proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
    if not proto:
        proto = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
    return f"{proto}://{host}"


def _user_login(uid: int) -> str:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            "SELECT COALESCE(NULLIF(login_name,''), NULLIF(short_name,''), "
            "'user'||id::text) FROM public.users WHERE id = :id"
        ), {"id": uid}).first()
        return row[0] if row else ("user" + str(uid))
    finally:
        s.close()


def _user_display(uid: int) -> str:
    """Zobrazované jméno uživatele (kdo je k zařízení spárovaný)."""
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            "SELECT COALESCE(NULLIF(TRIM(COALESCE(first_name,'')||' '||"
            "COALESCE(last_name,'')),''), NULLIF(short_name,''), "
            "NULLIF(login_name,''), 'Uživatel '||id::text) "
            "FROM public.users WHERE id = :id"
        ), {"id": uid}).first()
        return row[0] if row else ("Uživatel " + str(uid))
    finally:
        s.close()


def _user_phone(uid: int) -> str | None:
    """Nejnovější ověřené číslo uživatele (z appky/zařízení) — pro zobrazení
    v párování i u zařízení bez vlastního čísla na tokenu. Marti 6.6.2026."""
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            "SELECT phone_number FROM fw.mobile_device "
            "WHERE user_id = :u AND phone_number IS NOT NULL "
            "ORDER BY phone_verified_at DESC NULLS LAST LIMIT 1"
        ), {"u": uid}).first()
        if row and row[0]:
            return row[0]
        row = s.execute(_sql(
            'SELECT phone_number FROM "user".carddav_token '
            'WHERE user_id = :u AND phone_number IS NOT NULL '
            'ORDER BY id DESC LIMIT 1'
        ), {"u": uid}).first()
        return row[0] if row and row[0] else None
    except Exception:
        return None
    finally:
        s.close()


def _active_contact_count(uid: int) -> int:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql(
            'SELECT count(*) FROM "user".carddav_active_contact '
            'WHERE user_id = :uid AND removed_at IS NULL'
        ), {"uid": uid}).first()
        return int(row[0]) if row else 0
    finally:
        s.close()


_HANDOFF_TTL_MIN = 15  # jak dlouho je QR/odkaz pro telefon platný


def _make_handoff(uid: int, plaintext: str, carddav_url: str,
                  username: str, device_label: str) -> str | None:
    """Vytvoří jednorázovou handoff stránku (token na telefon přes QR).
    Vrací nonce, nebo None (např. když tabulka ještě neexistuje — token se
    vytvoří tak jako tak, jen bez QR)."""
    nonce = secrets.token_urlsafe(32)
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        # úklid prošlých (best-effort)
        try:
            s.execute(_sql('DELETE FROM "user".carddav_handoff '
                           'WHERE expires_at < now()'))
        except Exception:
            pass
        s.execute(_sql('''
            INSERT INTO "user".carddav_handoff
                (nonce, user_id, token_plain, carddav_url, username,
                 device_label, expires_at)
            VALUES (:n, :uid, :tok, :url, :usr, :lbl,
                    now() + (:ttl || ' minutes')::interval)
        '''), {"n": nonce, "uid": uid, "tok": plaintext, "url": carddav_url,
               "usr": username, "lbl": device_label,
               "ttl": str(_HANDOFF_TTL_MIN)})
        s.commit()
        return nonce
    except Exception as exc:
        s.rollback()
        logger.warning("[carddav handoff create] %s", exc)
        return None
    finally:
        s.close()


def _fetch_handoff(nonce: str) -> dict | None:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        row = s.execute(_sql('''
            SELECT token_plain, carddav_url, username, device_label
            FROM "user".carddav_handoff
            WHERE nonce = :n AND expires_at > now()
        '''), {"n": nonce}).mappings().first()
        if row:
            try:
                s.execute(_sql('UPDATE "user".carddav_handoff '
                               'SET viewed_at = now() WHERE nonce = :n'),
                          {"n": nonce})
                s.commit()
            except Exception:
                s.rollback()
        return dict(row) if row else None
    except Exception as exc:
        logger.warning("[carddav handoff fetch] %s", exc)
        return None
    finally:
        s.close()


def _list_tokens(uid: int) -> list[dict]:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        rows = s.execute(_sql('''
            SELECT id, device_label, phone_number,
                   to_char(created_at,  'YYYY-MM-DD HH24:MI') AS created,
                   to_char(last_used_at, 'YYYY-MM-DD HH24:MI') AS last_used,
                   (revoked_at IS NOT NULL) AS revoked
            FROM "user".carddav_token
            WHERE user_id = :uid
            ORDER BY (revoked_at IS NOT NULL), id DESC
        '''), {"uid": uid}).mappings().all()
        return [dict(r) for r in rows]
    finally:
        s.close()


def _conn_info(request: Request, uid: int) -> dict:
    base = _carddav_base(request)
    login = _user_login(uid)
    return {
        "carddav_url": base + "/carddav/",
        "well_known": base + "/.well-known/carddav",
        "username": login,
        "user_name": _user_display(uid),
        "phone_number": _user_phone(uid),
        "books": [
            {"key": "real", "label": _BOOK_LABEL["real"]},
            {"key": "potential", "label": _BOOK_LABEL["potential"]},
        ],
        "active_contacts": _active_contact_count(uid),
        "max_devices": _MAX_ACTIVE_TOKENS,
    }


@carddav_mgmt_router.get("/info")
def carddav_info(request: Request) -> JSONResponse:
    """Údaje pro připojení + počet připravených kontaktů (bez tajemství)."""
    uid = _session_uid(request)
    if uid is None:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    info = _conn_info(request, uid)
    info["ok"] = True
    info["tokens"] = _list_tokens(uid)
    return JSONResponse(info)


@carddav_mgmt_router.get("/tokens")
def carddav_tokens(request: Request) -> JSONResponse:
    uid = _session_uid(request)
    if uid is None:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return JSONResponse({"ok": True, "tokens": _list_tokens(uid)})


@carddav_mgmt_router.post("/token")
async def carddav_token_create(request: Request) -> JSONResponse:
    """Vygeneruje nový token pro zařízení. Plaintext vrací JEN TEĎ (1×)."""
    uid = _session_uid(request)
    if uid is None:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

    label = ""
    try:
        body = await request.json()
        label = str((body or {}).get("device_label") or "").strip()[:80]
    except Exception:
        label = ""
    if not label:
        label = "Telefon"

    from core.database_data import get_data_session
    s = get_data_session()
    try:
        active = s.execute(_sql(
            'SELECT count(*) FROM "user".carddav_token '
            'WHERE user_id = :uid AND revoked_at IS NULL'
        ), {"uid": uid}).scalar() or 0
        if int(active) >= _MAX_ACTIVE_TOKENS:
            return JSONResponse({
                "ok": False, "error": "limit",
                "message": (f"Máš už {active} připojených zařízení (max "
                            f"{_MAX_ACTIVE_TOKENS}). Nejdřív některé odpoj.")
            }, status_code=429)

        plaintext = "STG-DAV-" + secrets.token_urlsafe(24)
        token_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
        row = s.execute(_sql('''
            INSERT INTO "user".carddav_token (user_id, device_label, token_hash, created_at)
            VALUES (:uid, :label, :h, now())
            RETURNING id
        '''), {"uid": uid, "label": label, "h": token_hash}).first()
        s.commit()
        new_id = int(row[0]) if row else None
    except Exception as exc:
        s.rollback()
        logger.warning("[carddav token create] %s", exc)
        return JSONResponse({"ok": False, "error": "server",
                             "message": str(exc)}, status_code=500)
    finally:
        s.close()

    info = _conn_info(request, uid)
    info.update({"ok": True, "token_id": new_id, "device_label": label,
                 "token": plaintext, "tokens": _list_tokens(uid)})
    # QR handoff: jednorázová stránka pro telefon (token + návod). Best-effort.
    nonce = _make_handoff(uid, plaintext, info.get("carddav_url", ""),
                          info.get("username", ""), label)
    if nonce:
        info["handoff_url"] = _carddav_base(request) + "/carddav-setup/" + nonce
        info["app_setup_url"] = _carddav_base(request) + "/app-setup/" + nonce
        info["handoff_ttl_min"] = _HANDOFF_TTL_MIN
    return JSONResponse(info)


@carddav_mgmt_router.post("/token/{token_id}/revoke")
def carddav_token_revoke(token_id: int, request: Request) -> JSONResponse:
    uid = _session_uid(request)
    if uid is None:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        res = s.execute(_sql(
            'UPDATE "user".carddav_token SET revoked_at = now() '
            'WHERE id = :id AND user_id = :uid AND revoked_at IS NULL'
        ), {"id": token_id, "uid": uid})
        s.commit()
        changed = res.rowcount or 0
    except Exception as exc:
        s.rollback()
        logger.warning("[carddav token revoke] %s", exc)
        return JSONResponse({"ok": False, "error": "server",
                             "message": str(exc)}, status_code=500)
    finally:
        s.close()
    return JSONResponse({"ok": True, "revoked": int(changed),
                         "tokens": _list_tokens(uid)})


# ── F1.4: obnova/sjednocení aktivní sady ───────────────────────────────────
# Starší vCardy (zavedené před prefixem STR-) nemají STR-Z/STR-P v jméně ani
# CATEGORIES → v telefonu se nenajdou přes "STR-" a nejsou ve skupinách.
# Tahle obnova jim to doplní in-place a bumpne (ctag/etag se změní → telefon
# při příští synchronizaci stáhne aktuální verzi). Bez MCP/CRM fetche.

_FN_PREFIX = {"real": "STR-Z", "potential": "STR-P"}
_CAT_LABEL = {"real": "Zákazníci", "potential": "Potenciální"}


def _normalize_vcard(vcard: str, addressbook: str) -> tuple[str, bool]:
    """Doplní STR- prefix do FN a CATEGORIES (pokud chybí). Vrací (vcard, změněno)."""
    prefix = _FN_PREFIX.get(addressbook, "STR-Z")
    cat = _CAT_LABEL.get(addressbook, "Zákazníci")
    sep = "\r\n" if "\r\n" in vcard else "\n"
    lines = vcard.split(sep)
    changed = False
    has_cat = False
    fn_idx = None
    for i, ln in enumerate(lines):
        up = ln.upper()
        if up.startswith("FN:"):
            fn_idx = i
            val = ln[3:]
            if not val.lstrip().startswith("STR-"):
                lines[i] = "FN:" + prefix + " " + val
                changed = True
        elif up.startswith("CATEGORIES"):
            has_cat = True
    if not has_cat and fn_idx is not None:
        ins = fn_idx + 1
        if ins < len(lines) and lines[ins].upper().startswith("ORG"):
            ins += 1
        lines.insert(ins, "CATEGORIES:" + cat)
        changed = True
    return (sep.join(lines), changed)


def _carddav_refresh_user(uid: int) -> dict:
    from core.database_data import get_data_session
    s = get_data_session()
    refreshed = 0
    total = 0
    try:
        rows = s.execute(_sql('''
            SELECT id, addressbook, vcard_cache
            FROM "user".carddav_active_contact
            WHERE user_id = :uid AND removed_at IS NULL
        '''), {"uid": uid}).mappings().all()
        total = len(rows)
        for r in rows:
            new_vc, changed = _normalize_vcard(r["vcard_cache"] or "",
                                               r["addressbook"])
            if changed:
                s.execute(_sql(
                    'UPDATE "user".carddav_active_contact '
                    'SET vcard_cache = :vc, last_active_at = now() WHERE id = :id'
                ), {"vc": new_vc, "id": r["id"]})
                refreshed += 1
        s.commit()
    except Exception as exc:
        s.rollback()
        logger.warning("[carddav refresh] %s", exc)
        return {"ok": False, "error": "server", "message": str(exc)}
    finally:
        s.close()
    return {"ok": True, "refreshed": refreshed, "total": total}


@carddav_mgmt_router.post("/refresh")
def carddav_refresh(request: Request) -> JSONResponse:
    """Sjednotí aktivní sadu (STR- prefix + CATEGORIES) a bumpne → telefon
    při příští synchronizaci stáhne aktuální kontakty."""
    uid = _session_uid(request)
    if uid is None:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    res = _carddav_refresh_user(uid)
    return JSONResponse(res, status_code=200 if res.get("ok") else 500)
