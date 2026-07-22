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
        return JSONResponse({"ok": True, "obdobi": obdobi, "pocet": len(rows),
                             "rows": [dict(r) for r in rows]})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass
