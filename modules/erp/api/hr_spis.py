"""Osobní spis zaměstnance — HR pohled + zaměstnanecký self-service.

Návrh: docs/osobni_spis_navrh.md (schváleno Marti 1.7.2026, konzultace Marti-AI).
Vůdčí princip (Šárka): jednoduché, systematické, uživatelsky přívětivé.
  - HR (rodič nebo skupina 'HR') vidí u každého člověka jeho aktuální dokumenty.
  - Zaměstnanec vidí ve své appce jen SVOJE (row-level filtr v service vrstvě).
  - Každý přístup HR k dokumentům konkrétního člověka se loguje (GDPR).

Tabulky: tenant.hr_spis_typ / hr_spis_dokument / hr_spis_pristup_log (1.7.2026).
Soubory zůstávají v Centrále; STRATEGIE drží jen referenci + metadata.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

hr_spis_router = APIRouter(prefix="/api/v1/erp", tags=["hr-spis"])
_TENANT = 2  # EUROSOFT


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _hr_ok(s, uid) -> bool:
    from modules.erp.api.router import _hr_can_manage
    try:
        return _hr_can_manage(s, uid)
    except Exception:
        return False


def _log(subjekt_user_id, dokument_id, pristupil_uid, akce, ip=None):
    """GDPR audit přístupu — best-effort (nikdy neshodí čtení)."""
    try:
        from modules.strategie_pg.application import service as _pg
        cm = _pg.get_session(); s = cm.__enter__()
        try:
            s.execute(_t(
                "INSERT INTO tenant.hr_spis_pristup_log "
                "(tenant_id, dokument_id, subjekt_user_id, pristupil_user_id, akce, ip) "
                "VALUES (:t,:d,:su,:pu,:a,:ip)"),
                {"t": _TENANT, "d": dokument_id, "su": subjekt_user_id,
                 "pu": pristupil_uid, "a": akce, "ip": ip})
        finally:
            cm.__exit__(None, None, None)
    except Exception:
        pass


@hr_spis_router.get("/app/hr-spis/lide")
async def hr_spis_lide(req: Request):
    """Seznam lidí (kdo má aktuální pracovní poměr) + počet platných dokumentů."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    cm, s = None, None
    try:
        s = _sess()
        if not _hr_ok(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        rows = s.execute(_t(
            "SELECT e.id, e.full_name, "
            " (SELECT c.code FROM tenant.engagement en LEFT JOIN tenant.company c ON c.id=en.company_id "
            "   WHERE en.employee_id=e.id AND en.is_current=true LIMIT 1) firma, "
            " (SELECT count(*) FROM tenant.hr_spis_dokument d WHERE d.tenant_id=:t AND d.employee_id=e.id "
            "   AND (d.platnost_do IS NULL OR d.platnost_do >= CURRENT_DATE)) pocet "
            "FROM tenant.att_employee e "
            "WHERE e.tenant_id=:t AND COALESCE(e.full_name,'')<>'' "
            "  AND EXISTS (SELECT 1 FROM tenant.engagement en WHERE en.employee_id=e.id AND en.is_current=true) "
            "ORDER BY e.full_name"), {"t": _TENANT}).fetchall()
        lide = [{"id": r[0], "jmeno": r[1], "firma": r[2] or "", "pocet_platnych": int(r[3] or 0)}
                for r in rows]
        return JSONResponse({"ok": True, "lide": lide})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        if s is not None:
            try: s.close()
            except Exception: pass


@hr_spis_router.get("/app/hr-spis/osoba/{emp_id}")
async def hr_spis_osoba(emp_id: int, req: Request):
    """Dokumenty konkrétní osoby (HR pohled). Loguje přístup (GDPR)."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    s = None
    try:
        s = _sess()
        if not _hr_ok(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        er = s.execute(_t("SELECT full_name, user_id FROM tenant.att_employee WHERE id=:e AND tenant_id=:t"),
                       {"e": emp_id, "t": _TENANT}).first()
        if not er:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        rows = s.execute(_t(
            "SELECT d.id, d.typ_kod, COALESCE(t.nazev,d.typ_kod) typ_nazev, d.nazev, "
            " to_char(d.platnost_od,'YYYY-MM-DD'), to_char(d.platnost_do,'YYYY-MM-DD'), "
            " d.podepsano, to_char(d.podepsano_dne,'YYYY-MM-DD'), "
            " (d.platnost_do IS NULL OR d.platnost_do >= CURRENT_DATE) aktualni, d.zdroj "
            "FROM tenant.hr_spis_dokument d LEFT JOIN tenant.hr_spis_typ t ON t.kod=d.typ_kod "
            "WHERE d.tenant_id=:t AND d.employee_id=:e "
            "ORDER BY COALESCE(t.poradi,100), d.platnost_od DESC NULLS LAST"),
            {"t": _TENANT, "e": emp_id}).fetchall()
        dok = [{"id": r[0], "typ": r[1], "typ_nazev": r[2], "nazev": r[3],
                "platnost_od": r[4], "platnost_do": r[5], "podepsano": bool(r[6]),
                "podepsano_dne": r[7], "aktualni": bool(r[8]), "zdroj": r[9]} for r in rows]
        _log(er[1], None, uid, "list", (req.client.host if req.client else None))
        return JSONResponse({"ok": True, "osoba": {"id": emp_id, "jmeno": er[0]}, "dokumenty": dok})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        if s is not None:
            try: s.close()
            except Exception: pass


@hr_spis_router.get("/app/moje-dokumenty")
async def moje_dokumenty(req: Request):
    """Zaměstnanecký self-service — jen SVOJE aktuální a podepsané dokumenty.
    Row-level filtr v service vrstvě (ne jen v UI). Whitelist polí (bez stav/zdroj)."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    s = None
    try:
        s = _sess()
        rows = s.execute(_t(
            "SELECT d.id, COALESCE(t.nazev,d.typ_kod) typ_nazev, d.nazev, "
            " to_char(d.platnost_od,'YYYY-MM-DD'), to_char(d.platnost_do,'YYYY-MM-DD'), "
            " to_char(d.podepsano_dne,'YYYY-MM-DD') "
            "FROM tenant.hr_spis_dokument d LEFT JOIN tenant.hr_spis_typ t ON t.kod=d.typ_kod "
            "WHERE d.tenant_id=:t "
            "  AND d.employee_id IN (SELECT id FROM tenant.att_employee WHERE tenant_id=:t AND user_id=:u) "
            "  AND d.podepsano = true "
            "  AND (d.platnost_do IS NULL OR d.platnost_do >= CURRENT_DATE) "
            "ORDER BY COALESCE(t.poradi,100)"), {"t": _TENANT, "u": uid}).fetchall()
        dok = [{"id": r[0], "typ_nazev": r[1], "nazev": r[2],
                "platnost_od": r[3], "platnost_do": r[4], "podepsano_dne": r[5]} for r in rows]
        _log(uid, None, uid, "self-list", (req.client.host if req.client else None))
        return JSONResponse({"ok": True, "dokumenty": dok})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        if s is not None:
            try: s.close()
            except Exception: pass
