"""Fotky pro výrobu — REST API (Etapa 1).

Univerzální fotodokumentace: fotka (binárka přes modul `media`) se váže na
generický předmět (predmet_typ + predmet_ref, např. zakázka) a na záběr ze
šablony (tenant.foto_zaber). Model kvality + AI hodnocení dle Ondrova
ai-processing-v2 (HeliosDB EC_Foto_*), přeloženo do PostgreSQL.

Prefix: /api/v1/erp/app/foto
Čte i zapisuje jen do PG (schéma tenant). Auth = cookie/token jako zbytek app.
Claude C23 pro Martiho, 29.7.2026.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

from core.database_data import get_data_session

foto_router = APIRouter(prefix="/api/v1/erp/app/foto", tags=["foto"])

TENANT = 2


def _uid(req: Request):
    """User id z tokenu/cookie — sdílený helper z erp routeru."""
    try:
        from modules.erp.api.router import _uid_from_token_or_cookie
        return _uid_from_token_or_cookie(req)
    except Exception:
        try:
            return int(req.cookies.get("user_id") or 0) or None
        except Exception:
            return None


# ── Šablony focení ──────────────────────────────────────────────────────────
@foto_router.get("/sablony")
def sablony(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    s = get_data_session()
    try:
        rows = s.execute(_t(
            "SELECT id, kod, nazev, predmet_typ FROM tenant.foto_sablona "
            "WHERE tenant_id=:t AND aktivni ORDER BY poradi NULLS LAST, id"),
            {"t": TENANT}).fetchall()
        return JSONResponse({"ok": True, "sablony": [
            {"id": r[0], "kod": r[1], "nazev": r[2], "predmet_typ": r[3]} for r in rows]})
    finally:
        s.close()


@foto_router.get("/sablona/{kod}")
def sablona_detail(kod: str, req: Request) -> JSONResponse:
    """Šablona + její záběry seskupené (co se má vyfotit)."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    s = get_data_session()
    try:
        srow = s.execute(_t(
            "SELECT id, kod, nazev, predmet_typ FROM tenant.foto_sablona "
            "WHERE tenant_id=:t AND kod=:k"), {"t": TENANT, "k": kod}).fetchone()
        if not srow:
            return JSONResponse({"ok": False, "error": "sablona_nenalezena"}, status_code=404)
        zab = s.execute(_t(
            "SELECT id, skupina, nazev, napoveda, vzorove_media_id, povinny, poradi "
            "FROM tenant.foto_zaber WHERE tenant_id=:t AND sablona_id=:sid AND aktivni "
            "ORDER BY poradi NULLS LAST, id"),
            {"t": TENANT, "sid": srow[0]}).fetchall()
        return JSONResponse({"ok": True,
            "sablona": {"id": srow[0], "kod": srow[1], "nazev": srow[2], "predmet_typ": srow[3]},
            "zabery": [{"id": z[0], "skupina": z[1], "nazev": z[2], "napoveda": z[3],
                        "vzorove_media_id": z[4], "povinny": z[5], "poradi": z[6]} for z in zab]})
    finally:
        s.close()


# ── Nahrání fotky (naváže existující media_id jako fotku předmětu) ───────────
@foto_router.post("/attach")
async def attach(req: Request) -> JSONResponse:
    """Body: {predmet_typ, predmet_ref, sablona_kod?, zaber_id?, media_id, jmeno_souboru?, ucel?, ucel_detail?}
    Binárka se nahrává zvlášť přes /api/v1/media/upload → sem přijde media_id."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    predmet_typ = str((body or {}).get("predmet_typ") or "zakazka").strip()[:30]
    predmet_ref = str((body or {}).get("predmet_ref") or "").strip()[:50]
    media_id = (body or {}).get("media_id")
    if not predmet_ref or not media_id:
        return JSONResponse({"ok": False, "error": "chybi predmet_ref nebo media_id"}, status_code=400)
    sablona_kod = (body or {}).get("sablona_kod")
    zaber_id = (body or {}).get("zaber_id")
    jmeno = str((body or {}).get("jmeno_souboru") or "")[:255] or None
    ucel = str((body or {}).get("ucel") or "")[:50] or None
    ucel_detail = str((body or {}).get("ucel_detail") or "")[:200] or None
    s = get_data_session()
    try:
        sablona_id = None
        if sablona_kod:
            r = s.execute(_t("SELECT id FROM tenant.foto_sablona WHERE tenant_id=:t AND kod=:k"),
                          {"t": TENANT, "k": sablona_kod}).fetchone()
            sablona_id = r[0] if r else None
        row = s.execute(_t(
            "INSERT INTO tenant.foto (tenant_id, sablona_id, zaber_id, predmet_typ, predmet_ref, "
            " media_id, jmeno_souboru, ucel, ucel_detail, autor_user_id, stav) "
            "VALUES (:t,:sid,:zid,:pt,:pr,:mid,:jm,:uc,:ud,:u,'nova') RETURNING id"),
            {"t": TENANT, "sid": sablona_id, "zid": zaber_id, "pt": predmet_typ, "pr": predmet_ref,
             "mid": int(media_id), "jm": jmeno, "uc": ucel, "ud": ucel_detail, "u": uid}).fetchone()
        s.commit()
        return JSONResponse({"ok": True, "foto_id": row[0]})
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    finally:
        s.close()


# ── Sada = všechny fotky jednoho předmětu + známky + pokrytí ────────────────
@foto_router.get("/sada")
def sada(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    predmet_typ = (req.query_params.get("predmet_typ") or "zakazka").strip()[:30]
    predmet_ref = (req.query_params.get("predmet_ref") or "").strip()[:50]
    if not predmet_ref:
        return JSONResponse({"ok": False, "error": "chybi predmet_ref"}, status_code=400)
    s = get_data_session()
    try:
        rows = s.execute(_t(
            "SELECT f.id, f.media_id, f.zaber_id, z.skupina, z.nazev, f.stav, "
            " to_char(f.datum_vlozeni,'DD.MM HH24:MI') AS kdy, "
            " h.celkove_hodnoceni, h.celkove_hodnoceni_text, h.verdikt, "
            " v.brisque_skore, v.laplacian_skore, v.ai_kontext "
            "FROM tenant.foto f "
            "LEFT JOIN tenant.foto_zaber z ON z.id=f.zaber_id "
            "LEFT JOIN tenant.foto_hodnoceni h ON h.foto_id=f.id "
            "LEFT JOIN tenant.foto_vysledek v ON v.foto_id=f.id "
            "WHERE f.tenant_id=:t AND f.predmet_typ=:pt AND f.predmet_ref=:pr "
            "ORDER BY z.poradi NULLS LAST, f.id DESC"),
            {"t": TENANT, "pt": predmet_typ, "pr": predmet_ref}).fetchall()
        fotky = [{"id": r[0], "media_id": r[1], "zaber_id": r[2], "skupina": r[3], "zaber": r[4],
                  "stav": r[5], "kdy": r[6], "hodnoceni": (float(r[7]) if r[7] is not None else None),
                  "znamka": r[8], "verdikt": r[9], "brisque": r[10], "laplacian": r[11],
                  "ai_kontext": r[12]} for r in rows]
        return JSONResponse({"ok": True, "predmet_typ": predmet_typ, "predmet_ref": predmet_ref,
                             "pocet": len(fotky), "fotky": fotky})
    finally:
        s.close()


# ── Smazání fotky (soft — jen naše vazba; binárka zůstává v media) ──────────
@foto_router.post("/smazat")
async def smazat(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    fid = (body or {}).get("foto_id")
    if not fid:
        return JSONResponse({"ok": False, "error": "chybi foto_id"}, status_code=400)
    s = get_data_session()
    try:
        s.execute(_t("DELETE FROM tenant.foto WHERE tenant_id=:t AND id=:i AND autor_user_id=:u"),
                  {"t": TENANT, "i": int(fid), "u": uid})
        s.commit()
        return JSONResponse({"ok": True})
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    finally:
        s.close()


# ── Přehled pro vedoucího: předměty (zakázky) + počty ───────────────────────
@foto_router.get("/prehled")
def prehled(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    s = get_data_session()
    try:
        rows = s.execute(_t(
            "SELECT f.predmet_typ, f.predmet_ref, count(*) AS pocet, "
            " count(*) FILTER (WHERE h.verdikt='prefotit') AS prefotit, "
            " max(f.datum_vlozeni) AS posledni "
            "FROM tenant.foto f LEFT JOIN tenant.foto_hodnoceni h ON h.foto_id=f.id "
            "WHERE f.tenant_id=:t "
            "GROUP BY f.predmet_typ, f.predmet_ref "
            "ORDER BY max(f.datum_vlozeni) DESC LIMIT 200"),
            {"t": TENANT}).fetchall()
        return JSONResponse({"ok": True, "predmety": [
            {"predmet_typ": r[0], "predmet_ref": r[1], "pocet": r[2], "prefotit": r[3],
             "posledni": (r[4].strftime("%d.%m %H:%M") if r[4] else None)} for r in rows]})
    finally:
        s.close()
