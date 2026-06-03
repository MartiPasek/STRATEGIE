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
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
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


def _list_tokens(uid: int) -> list[dict]:
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        rows = s.execute(_sql('''
            SELECT id, device_label,
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
