"""Docházka po zakázkách — data pro vlastní stránku ve stylu standardu přehledů
(table.dokl, vzor pokladny.html). Peťa + Claude‑26, 22.7.2026.

Přehled zůstává definovaný v JEDNOM místě — data_setu `dochazka.zakazky_vse_list`
(resp. `dochazka.zakazky_budoucnost_list`). Endpoint jen vezme jeho SQL a spustí ho,
aby vlastní stránka renderovala TÁŽ data jako dřív framework grid. Jen čte (PG).

Gate = shodný s viditelností uzlu „🕒 Docházka" (11 lidí) + rodičovský bypass.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

doch_zak_tab_router = APIRouter(prefix="/api/v1/erp", tags=["dochazka-zak-tab"])

_DZT_ALLOWED = {1, 11, 13, 16, 17, 18, 20, 41, 107, 108, 109}
_DZT_DATASET = {
    "vse": "dochazka.zakazky_vse_list",
    "budoucnost": "dochazka.zakazky_budoucnost_list",
}


_DZT_WIDTHS_KEY = "dochazka_col_widths"


def _dzt_can_save(uid: int | None) -> bool:
    """Kdo smí měnit SDÍLENÉ výchozí šířky: rodiče (Marti/Kristý/Jirka) + Peťa (18)."""
    if not uid:
        return False
    if int(uid) in (1, 11, 20, 18):
        return True
    from sqlalchemy import text as _t
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            return bool(s.execute(_t("SELECT COALESCE(is_marti_parent,false) FROM public.users WHERE id=:u"),
                                  {"u": int(uid)}).scalar())
        finally:
            s.close()
    except Exception:
        return False


def _dzt_can(uid: int | None) -> bool:
    if not uid:
        return False
    if int(uid) in _DZT_ALLOWED:
        return True
    from sqlalchemy import text as _t
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            return bool(s.execute(_t("SELECT COALESCE(is_marti_parent,false) FROM public.users WHERE id=:u"),
                                  {"u": int(uid)}).scalar())
        finally:
            s.close()
    except Exception:
        return False


@doch_zak_tab_router.get("/app/dochazka-zak-tab/data")
def dochazka_zak_tab_data(req: Request) -> JSONResponse:
    """Řádky přehledu docházky po zakázkách (obdobi=vse|budoucnost)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if not _dzt_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    obdobi = (req.query_params.get("obdobi") or "vse").strip().lower()
    ds_code = _DZT_DATASET.get(obdobi, _DZT_DATASET["vse"])
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        sql = s.execute(_t("SELECT sql_text FROM fw.data_set WHERE code=:c"), {"c": ds_code}).scalar()
        if not sql:
            return JSONResponse({"ok": False, "error": "dataset_missing"}, status_code=500)
        rows = s.execute(_t(sql)).mappings().all()
        from decimal import Decimal as _D
        import datetime as _dt

        def _conv(v):
            if isinstance(v, _D):
                return float(v)
            if isinstance(v, (_dt.date, _dt.datetime)):
                return v.isoformat()
            return v
        out = [{k: _conv(v) for k, v in dict(r).items()} for r in rows]
        return JSONResponse({"ok": True, "obdobi": obdobi, "pocet": len(out), "rows": out})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


@doch_zak_tab_router.get("/app/dochazka-zak-tab/widths")
def dochazka_zak_tab_widths_get(req: Request) -> JSONResponse:
    """Šířky sloupců: `base` = sdílené výchozí pro všechny; `me` = osobní uložené
    tažení tohoto uživatele (má přednost). Osobní se ukládají do DB (jako dřív
    framework grid), aby je Claude viděl a mohl je povýšit na výchozí."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid or not _dzt_can(uid):
        return JSONResponse({"ok": True, "base": {}, "me": {}})
    from sqlalchemy import text as _t
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            base = s.execute(_t("SELECT hodnota FROM tenant.att_ui_pref WHERE kod=:k"),
                             {"k": _DZT_WIDTHS_KEY}).scalar()
            me = s.execute(_t("SELECT hodnota FROM tenant.att_ui_pref WHERE kod=:k"),
                           {"k": _DZT_WIDTHS_KEY + "_u" + str(int(uid))}).scalar()
        finally:
            s.close()
        return JSONResponse({"ok": True, "base": base or {}, "me": me or {}})
    except Exception:
        return JSONResponse({"ok": True, "base": {}, "me": {}})


@doch_zak_tab_router.post("/app/dochazka-zak-tab/widths")
async def dochazka_zak_tab_widths_set(req: Request) -> JSONResponse:
    """Uloží OSOBNÍ šířky uživatele do DB (kdokoliv z povolených 11). Tím je Claude
    může přečíst a povýšit na sdílené výchozí (kod bez _u<uid>)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if not _dzt_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        body = await req.json()
    except Exception:
        body = {}
    widths = (body or {}).get("widths")
    if not isinstance(widths, dict):
        return JSONResponse({"ok": False, "error": "bad_widths"}, status_code=400)
    # sanitizace: jen {sloupec: kladné číslo}
    clean = {}
    for k, v in widths.items():
        try:
            iv = int(v)
        except Exception:
            continue
        if isinstance(k, str) and 20 <= iv <= 1200:
            clean[k[:40]] = iv
    import json as _j
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    key = _DZT_WIDTHS_KEY + "_u" + str(int(uid))
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        s.execute(_t(
            "INSERT INTO tenant.att_ui_pref (kod, hodnota, updated_by, updated_at) "
            "VALUES (:k, CAST(:v AS jsonb), :u, now()) "
            "ON CONFLICT (kod) DO UPDATE SET hodnota=CAST(:v AS jsonb), updated_by=:u, updated_at=now()"),
            {"k": key, "v": _j.dumps(clean), "u": int(uid)})
        s.commit()
        return JSONResponse({"ok": True, "ulozeno": len(clean)})
    except Exception as exc:  # noqa: BLE001
        try:
            s.rollback()
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass
