"""Analýza hospodaření zakázek (Marti 10.7.2026, na žádost Radka Hellmayera).

Zrcadlo EC_ZakazkyZisk (EC Helios / DB_EC přes eurosoft MCP) do cloud pg
(tenant.zakazky_zisk_mirror) + analytické API a stránka /zakazky-analyza.
Sledujeme: vývoj VR zakázek přes 1. pololetí let 2022–2026 (pocovid), poměr
kalkulovaných vs reálných hodin, a rozdělení podle dodávky materiálu
(naše dodávka vs Beistellung/zákazník) + porovnání ziskovosti.

Dimenze roku = rok poslední vydané faktury (DatPosledniVF), viz zápis 10.7.
Materiál proxy: NakladyMaterial > prah (default 1000 Kč) = "s naším materiálem".
"""
from __future__ import annotations

import os
import json as _json
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from sqlalchemy import text as _t

from modules.erp.api.contract_sign import contract_router as zakazky_router

MATERIAL_PRAH = 1000.0   # Kč: NakladyMaterial nad prah = zakázka s naší dodávkou materiálu
ROK_OD, ROK_DO = 2021, 2026


# ── helpers (lazy import z router.py) ──
def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _pg():
    from core.database_data import get_data_session
    return get_data_session()


def _erp_member_or_403(uid):
    """Tým (business okruh). Vrací None při OK, jinak JSONResponse 403."""
    if not uid:
        return JSONResponse({"ok": False, "error": "Nepřihlášen"}, status_code=401)
    try:
        from modules.erp.api.router import _require_erp_member
        _require_erp_member(uid)
        return None
    except Exception:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)


def _admin_ok(uid, s):
    """Refresh zrcadla = rodič nebo cockpit (finance/HR)."""
    if not uid:
        return False
    try:
        from modules.erp.api.router import is_marti_parent, _is_cockpit
        return bool(is_marti_parent(uid) or _is_cockpit(s, uid))
    except Exception:
        return False


def _ec_query(sql):
    """Dotaz na EC Helios (DB_EC) přes eurosoft MCP. Vrací list dictů nebo vyhodí."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EC Helios (MCP) nedostupný")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
    r = _json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error"))[:200])
        for k in ("rows", "data", "result", "records"):
            if isinstance(r.get(k), list):
                return r[k]
        return []
    return r if isinstance(r, list) else []


_DDL = """
CREATE TABLE IF NOT EXISTS tenant.zakazky_zisk_mirror (
    cislo_zakazky   text,
    nazev           text,
    rok_vf          int,
    mesic_vf        int,
    prefix          text,
    vynosy          numeric(18,2),
    naklady_pevne   numeric(18,2),
    zisk_pevny      numeric(18,2),
    naklady_material numeric(18,2),
    kalk_material   numeric(18,2),
    kalk_hodiny     numeric(18,2),
    real_hodiny     numeric(18,2),
    real_hodiny_ef  numeric(18,2),
    stredisko       text,
    ukonceno        int,
    refreshed_at    timestamptz DEFAULT now()
);
"""

_EC_SQL = (
    "SELECT CisloZakazky, Nazev, "
    "YEAR(DatPosledniVF) AS rok_vf, MONTH(DatPosledniVF) AS mesic_vf, "
    "LEFT(CisloZakazky,2) AS prefix, "
    "CAST(ISNULL(VynosyCelkem,0) AS decimal(18,2)) AS vynosy, "
    "CAST(ISNULL(NakladyCelkemPevne,0) AS decimal(18,2)) AS naklady_pevne, "
    "CAST(ISNULL(ZiskZakazkyPevny,0) AS decimal(18,2)) AS zisk_pevny, "
    "CAST(ISNULL(NakladyMaterial,0) AS decimal(18,2)) AS naklady_material, "
    "CAST(ISNULL(SumKalkMaterial,0) AS decimal(18,2)) AS kalk_material, "
    "CAST(ISNULL(KalkHodinyCelkem,0) AS decimal(18,2)) AS kalk_hodiny, "
    "CAST(ISNULL(RealHodinyCelkem,0) AS decimal(18,2)) AS real_hodiny, "
    "CAST(ISNULL(RealHodinyCelkemEf,0) AS decimal(18,2)) AS real_hodiny_ef, "
    "ISNULL(CAST(Stredisko AS varchar(60)),'') AS stredisko, "
    "CAST(ISNULL(Ukonceno,0) AS int) AS ukonceno "
    "FROM EC_ZakazkyZisk "
    "WHERE Irelevantni=0 AND DatPosledniVF IS NOT NULL "
    "AND YEAR(DatPosledniVF) BETWEEN " + str(ROK_OD) + " AND " + str(ROK_DO)
)

_COLS = ["cislo_zakazky", "nazev", "rok_vf", "mesic_vf", "prefix", "vynosy",
         "naklady_pevne", "zisk_pevny", "naklady_material", "kalk_material",
         "kalk_hodiny", "real_hodiny", "real_hodiny_ef", "stredisko", "ukonceno"]

# EC_ZakazkyZisk vrací názvy sloupců různě (case); mapuj lower→náš klíč.
_EC_MAP = {
    "cislozakazky": "cislo_zakazky", "nazev": "nazev", "rok_vf": "rok_vf",
    "mesic_vf": "mesic_vf", "prefix": "prefix", "vynosy": "vynosy",
    "naklady_pevne": "naklady_pevne", "zisk_pevny": "zisk_pevny",
    "naklady_material": "naklady_material", "kalk_material": "kalk_material",
    "kalk_hodiny": "kalk_hodiny", "real_hodiny": "real_hodiny",
    "real_hodiny_ef": "real_hodiny_ef", "stredisko": "stredisko", "ukonceno": "ukonceno",
}


def _num(v):
    try:
        return float(v)
    except Exception:
        return 0.0


@zakazky_router.post("/app/zakazky/mirror-refresh")
async def zakazky_mirror_refresh(req: Request):
    """Přečti EC_ZakazkyZisk z EC Heliosu a přepiš zrcadlo v cloudu. Parent/cockpit."""
    uid = _uid(req)
    s = _pg()
    try:
        if not _admin_ok(uid, s):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        try:
            rows = _ec_query(_EC_SQL)
        except Exception as exc:
            return JSONResponse({"ok": False, "error": "EC dotaz: " + str(exc)[:200]}, status_code=502)
        # normalizace řádků
        norm = []
        for d in rows:
            dd = {(k or "").lower(): v for k, v in d.items()}
            rec = {}
            for lk, our in _EC_MAP.items():
                rec[our] = dd.get(lk)
            for c in ("vynosy", "naklady_pevne", "zisk_pevny", "naklady_material",
                      "kalk_material", "kalk_hodiny", "real_hodiny", "real_hodiny_ef"):
                rec[c] = _num(rec.get(c))
            for c in ("rok_vf", "mesic_vf", "ukonceno"):
                try:
                    rec[c] = int(rec.get(c) or 0)
                except Exception:
                    rec[c] = 0
            for c in ("cislo_zakazky", "nazev", "prefix", "stredisko"):
                rec[c] = (str(rec.get(c)) if rec.get(c) is not None else "")[:200]
            norm.append(rec)
        # zápis do pg: DDL + truncate + bulk insert
        s.execute(_t(_DDL))
        s.execute(_t("TRUNCATE tenant.zakazky_zisk_mirror"))
        ins = _t("INSERT INTO tenant.zakazky_zisk_mirror "
                 "(cislo_zakazky,nazev,rok_vf,mesic_vf,prefix,vynosy,naklady_pevne,zisk_pevny,"
                 "naklady_material,kalk_material,kalk_hodiny,real_hodiny,real_hodiny_ef,stredisko,ukonceno,refreshed_at) "
                 "VALUES (:cislo_zakazky,:nazev,:rok_vf,:mesic_vf,:prefix,:vynosy,:naklady_pevne,:zisk_pevny,"
                 ":naklady_material,:kalk_material,:kalk_hodiny,:real_hodiny,:real_hodiny_ef,:stredisko,:ukonceno,now())")
        B = 500
        for i in range(0, len(norm), B):
            s.execute(ins, norm[i:i + B])
        s.commit()
        return {"ok": True, "pocet": len(norm), "refreshed_at": datetime.now().strftime("%d.%m.%Y %H:%M")}
    finally:
        s.close()


def _agg(s, where_extra):
    """Agregace nad zrcadlem, group by rok_vf, jen 1. pololetí (mesic 1-6)."""
    q = ("SELECT rok_vf AS rok, COUNT(*) AS pocet, "
         "COALESCE(SUM(vynosy),0) AS vynosy, COALESCE(SUM(naklady_pevne),0) AS naklady, "
         "COALESCE(SUM(zisk_pevny),0) AS zisk, COALESCE(SUM(kalk_hodiny),0) AS kalk_hod, "
         "COALESCE(SUM(real_hodiny),0) AS real_hod "
         "FROM tenant.zakazky_zisk_mirror "
         "WHERE mesic_vf BETWEEN 1 AND 6 AND rok_vf BETWEEN 2022 AND 2026 " + where_extra +
         " GROUP BY rok_vf ORDER BY rok_vf")
    out = []
    for r in s.execute(_t(q)).mappings().all():
        vyn = float(r["vynosy"]); zis = float(r["zisk"]); kh = float(r["kalk_hod"]); rh = float(r["real_hod"])
        out.append({
            "rok": int(r["rok"]), "pocet": int(r["pocet"]),
            "vynosy": round(vyn), "naklady": round(float(r["naklady"])), "zisk": round(zis),
            "marze": round(zis / vyn * 100, 1) if vyn else 0.0,
            "kalk_hod": round(kh), "real_hod": round(rh),
            "ratio": round(rh / kh, 3) if kh else 0.0,
        })
    return out


def _agg_material(s):
    """H1 per rok, rozdělené podle dodávky materiálu (proxy NakladyMaterial > prah)."""
    q = ("SELECT rok_vf AS rok, "
         "CASE WHEN naklady_material > :prah THEN 'nas' ELSE 'beistellung' END AS skupina, "
         "COUNT(*) AS pocet, COALESCE(SUM(vynosy),0) AS vynosy, COALESCE(SUM(zisk_pevny),0) AS zisk "
         "FROM tenant.zakazky_zisk_mirror "
         "WHERE mesic_vf BETWEEN 1 AND 6 AND rok_vf BETWEEN 2022 AND 2026 "
         "GROUP BY rok_vf, CASE WHEN naklady_material > :prah THEN 'nas' ELSE 'beistellung' END "
         "ORDER BY rok_vf")
    out = []
    for r in s.execute(_t(q), {"prah": MATERIAL_PRAH}).mappings().all():
        vyn = float(r["vynosy"]); zis = float(r["zisk"])
        out.append({"rok": int(r["rok"]), "skupina": r["skupina"], "pocet": int(r["pocet"]),
                    "vynosy": round(vyn), "zisk": round(zis),
                    "marze": round(zis / vyn * 100, 1) if vyn else 0.0})
    return out


@zakazky_router.get("/app/zakazky/analyza")
def zakazky_analyza(req: Request):
    """Data pro stránku: VR trend, všechny zakázky, hodiny, materiál. Tým (ERP)."""
    uid = _uid(req)
    err = _erp_member_or_403(uid)
    if err:
        return err
    s = _pg()
    try:
        try:
            cnt = s.execute(_t("SELECT COUNT(*) FROM tenant.zakazky_zisk_mirror")).scalar()
        except Exception:
            cnt = 0
        if not cnt:
            return {"ok": True, "prazdne": True, "info": "Zrcadlo je prázdné — spusť refresh."}
        ra = s.execute(_t("SELECT MAX(refreshed_at) FROM tenant.zakazky_zisk_mirror")).scalar()
        return {
            "ok": True,
            "obdobi": "1. pololetí (leden–červen)",
            "refreshed_at": ra.strftime("%d.%m.%Y %H:%M") if ra else None,
            "material_prah": MATERIAL_PRAH,
            "vr": _agg(s, "AND prefix = 'VR'"),
            "vse": _agg(s, ""),
            "material": _agg_material(s),
        }
    finally:
        s.close()


def _static_path(name):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(root, "apps", "api", "static", name)


@zakazky_router.get("/zakazky-analyza")
def zakazky_analyza_page(req: Request):
    """Stránka analýzy zakázek pro Radka a tým."""
    uid = _uid(req)
    err = _erp_member_or_403(uid)
    if err:
        # nepřihlášené pošli na login
        if not uid:
            return HTMLResponse('<meta http-equiv="refresh" content="0; url=/?return=%2Fapi%2Fv1%2Ferp%2Fzakazky-analyza">')
        return err
    p = _static_path("zakazky-analyza.html")
    if os.path.isfile(p):
        return FileResponse(p, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return HTMLResponse("<h1>Stránka se připravuje.</h1>")
