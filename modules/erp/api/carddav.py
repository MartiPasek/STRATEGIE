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
from xml.sax.saxutils import escape as _xesc

from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import text as _sql

logger = logging.getLogger("strategie.carddav")

carddav_router = APIRouter()

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
