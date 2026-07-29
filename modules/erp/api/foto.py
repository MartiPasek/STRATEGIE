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

import base64
import io
import json as _json
import math
import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

from core.database_data import get_data_session

foto_router = APIRouter(prefix="/api/v1/erp/app/foto", tags=["foto"])

TENANT = 2

# Vision model (levný, umí obrázky) — sjednoceno s ai_processing.
_FOTO_AI_MODEL = "claude-haiku-4-5-20251001"

# Výchozí prompt (když model nemá vlastní ai_prompt_text). Vrací striktní JSON.
_FOTO_DEFAULT_PROMPT = (
    "Jsi kontrolor kvality fotodokumentace ve výrobě rozvaděčů. Ohodnoť tuto "
    "fotografii a vrať POUZE validní JSON (bez textu okolo) v tomto tvaru:\n"
    '{"ostrost":0-10,"svetelnost":0-10,"kompozice":0-10,"relevance":0-10,'
    '"ocr":0-10,"sum":0-10,"celkem":0-10,"verdikt":"ok"|"prefotit",'
    '"duvod":"krátký důvod pokud prefotit, jinak null","kontext":"stručně co je na fotce",'
    '"issues":["konkrétní problémy"]}\n'
    "Pravidla: 0=nejhorší, 10=nejlepší. ostrost=zaostření (rozmazané=nízké), "
    "svetelnost=expozice, kompozice=rámování, relevance=zda fotka dává smysl jako "
    "dokumentace, ocr=čitelnost štítků/textu (pokud nejsou, dej 5), sum=absence šumu. "
    "celkem=celkový dojem 0-10. verdikt=\"prefotit\" pokud celkem<6 nebo je fotka "
    "rozmazaná/tmavá/nečitelná. Nejčastější vada je rozmazání. České důvody: "
    "rozmazané, příliš_tmavé, příliš_světlé, špatný_úhel, odlesky, nečitelné_štítky, neúplný_obsah."
)


def _clamp10(v):
    try:
        return round(max(0.0, min(10.0, float(v))), 2)
    except Exception:
        return None


def _norm_laplacian(raw: float):
    """Ondrova normalizace: 0-5000+ (výš=líp) → 0-10, log."""
    return round(max(0.0, min(10.0, math.log10(max(raw, 1.0)) * 2.5)), 2)


def _load_image(media_id: int, uid: int, max_dim: int = 1024):
    """Vrátí (base64_jpeg, PIL.Image) nebo (None, None)."""
    from modules.media.application import service as media_service
    from PIL import Image
    serving = media_service.get_media_for_serving(int(media_id), uid)
    if not serving:
        return None, None
    _row, abs_path = serving
    im = Image.open(abs_path).convert("RGB")
    w, h = im.size
    if max(w, h) > max_dim:
        r = max_dim / float(max(w, h))
        im = im.resize((max(1, int(w * r)), max(1, int(h * r))))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode(), im


def _laplacian_var(im) -> float:
    import numpy as np
    g = np.asarray(im.convert("L"), dtype=np.float64)
    if g.shape[0] < 3 or g.shape[1] < 3:
        return 0.0
    lap = (-4.0 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1]
           + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var())


def _ai_eval(b64: str, prompt: str) -> dict:
    import anthropic
    from core.config import settings
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=_FOTO_AI_MODEL, max_tokens=700,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
            {"type": "text", "text": prompt},
        ]}])
    txt = "".join(b.text for b in msg.content if hasattr(b, "text") and b.text).strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt.strip())
    return _json.loads(txt)


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


# ── Vyhodnocení fotky: offline metrika (Laplacian) + AI vision → známka ──────
@foto_router.post("/vyhodnotit")
async def vyhodnotit(req: Request) -> JSONResponse:
    """Body: {foto_id}. Spočítá offline ostrost + pošle fotku do AI (vision),
    uloží foto_vysledek + foto_hodnoceni a nastaví verdikt ok/prefotit."""
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
        fr = s.execute(_t(
            "SELECT f.media_id, f.sablona_id FROM tenant.foto f "
            "WHERE f.tenant_id=:t AND f.id=:i"), {"t": TENANT, "i": int(fid)}).fetchone()
        if not fr or not fr[0]:
            return JSONResponse({"ok": False, "error": "foto/media nenalezeno"}, status_code=404)
        media_id = fr[0]
        # model kvality (výchozí) + prompt
        mr = s.execute(_t(
            "SELECT id, hranice_excellent, hranice_good, hranice_fair, "
            " COALESCE(ai_prompt_text,'') FROM tenant.foto_model "
            "WHERE tenant_id=:t AND je_vychozi ORDER BY id LIMIT 1"), {"t": TENANT}).fetchone()
        model_id = mr[0] if mr else None
        h_exc = float(mr[1]) if mr else 8.0
        h_good = float(mr[2]) if mr else 6.0
        h_fair = float(mr[3]) if mr else 4.0
        prompt = (mr[4] if mr and mr[4] else "") or _FOTO_DEFAULT_PROMPT

        # 1) offline ostrost (Laplacian)
        lap_norm = None
        try:
            b64, im = _load_image(media_id, uid)
            if im is not None:
                lap_norm = _norm_laplacian(_laplacian_var(im))
        except Exception as exc:  # noqa
            b64 = None
            _lap_err = str(exc)[:200]
        if not b64:
            return JSONResponse({"ok": False, "error": "nelze nacist obrazek"}, status_code=500)

        # 2) AI vision
        try:
            ai = _ai_eval(b64, prompt)
        except Exception as exc:  # noqa
            s.execute(_t("UPDATE tenant.foto SET stav='ai_chyba', chyba_text=:e, "
                         "pocet_pokusu=COALESCE(pocet_pokusu,0)+1 WHERE tenant_id=:t AND id=:i"),
                      {"e": str(exc)[:400], "t": TENANT, "i": int(fid)})
            s.commit()
            return JSONResponse({"ok": False, "error": "ai_selhalo: " + str(exc)[:200]}, status_code=502)

        o = {k: _clamp10(ai.get(k)) for k in ("ostrost", "svetelnost", "kompozice", "relevance", "ocr", "sum")}
        celkem = _clamp10(ai.get("celkem"))
        if celkem is None:
            vals = [v for v in o.values() if v is not None]
            celkem = round(sum(vals) / len(vals), 2) if vals else 5.0
        kontext = str(ai.get("kontext") or "")[:1000]
        duvod = ai.get("duvod")
        issues = ai.get("issues") or []
        ai_verdikt = str(ai.get("verdikt") or "").lower()

        # 3) verdikt: AI + tvrdý override na rozmazanost
        blurry = (lap_norm is not None and lap_norm < 2.5) or (o.get("ostrost") is not None and o["ostrost"] < 4)
        verdikt = "prefotit" if (ai_verdikt == "prefotit" or celkem < h_fair or blurry) else "ok"
        if celkem >= h_exc:
            znamka = "excellent"
        elif celkem >= h_good:
            znamka = "good"
        elif celkem >= h_fair:
            znamka = "fair"
        else:
            znamka = "poor"
        poznamka = (duvod + " | " if duvod else "") + (", ".join([str(x) for x in issues])[:400] if issues else "")

        # 4) zápis výsledků (upsert vysledek + insert hodnoceni + stav)
        s.execute(_t(
            "INSERT INTO tenant.foto_vysledek (tenant_id, foto_id, laplacian_skore, "
            " ai_ostrost, ai_svetelnost, ai_kompozice, ai_relevance, ai_ocr, ai_sum, ai_kontext, "
            " datum_analyzy_metrik, datum_analyzy_ai) "
            "VALUES (:t,:f,:lap,:o,:sv,:ko,:re,:oc,:su,:kx,now(),now()) "
            "ON CONFLICT (foto_id) DO UPDATE SET laplacian_skore=EXCLUDED.laplacian_skore, "
            " ai_ostrost=EXCLUDED.ai_ostrost, ai_svetelnost=EXCLUDED.ai_svetelnost, "
            " ai_kompozice=EXCLUDED.ai_kompozice, ai_relevance=EXCLUDED.ai_relevance, "
            " ai_ocr=EXCLUDED.ai_ocr, ai_sum=EXCLUDED.ai_sum, ai_kontext=EXCLUDED.ai_kontext, "
            " datum_analyzy_metrik=now(), datum_analyzy_ai=now()"),
            {"t": TENANT, "f": int(fid), "lap": lap_norm, "o": o["ostrost"], "sv": o["svetelnost"],
             "ko": o["kompozice"], "re": o["relevance"], "oc": o["ocr"], "su": o["sum"], "kx": kontext})
        s.execute(_t(
            "INSERT INTO tenant.foto_hodnoceni (tenant_id, foto_id, model_id, celkove_hodnoceni, "
            " celkove_hodnoceni_text, verdikt, ai_poznamka) "
            "VALUES (:t,:f,:m,:c,:ct,:v,:p)"),
            {"t": TENANT, "f": int(fid), "m": model_id, "c": celkem, "ct": znamka,
             "v": verdikt, "p": poznamka or None})
        s.execute(_t("UPDATE tenant.foto SET stav=:st WHERE tenant_id=:t AND id=:i"),
                  {"st": ("prefotit" if verdikt == "prefotit" else "ok"), "t": TENANT, "i": int(fid)})
        s.commit()
        return JSONResponse({"ok": True, "foto_id": int(fid), "celkem": celkem, "znamka": znamka,
                             "verdikt": verdikt, "laplacian": lap_norm, "kontext": kontext,
                             "metriky": o, "poznamka": poznamka})
    except Exception as exc:
        s.rollback()
        return JSONResponse({"ok": False, "error": str(exc)[:300]}, status_code=500)
    finally:
        s.close()
