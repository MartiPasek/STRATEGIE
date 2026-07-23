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


_DOW_CZ = ['Po', 'Ut', 'St', 'Ct', 'Pa', 'So', 'Ne']


def _dzt_ec_office_hist(s) -> list[dict]:
    """Kancelář (lidé BEZ výrobní práce) leden–květen 2026 přímo z Centrály
    (EC_Dochazka, read-only). Výroba je už v PG (vyroba_work), tu z EC vynecháme.
    Vrací řádky ve stejném tvaru jako přehled, kind='C' (jen ke čtení)."""
    from sqlalchemy import text as _t
    prod = [int(r[0]) for r in s.execute(_t(
        "SELECT DISTINCT cislo_zam FROM tenant.vyroba_work "
        "WHERE tenant_id=2 AND source_system IN ('app','centrala1') "
        "AND datum>='2026-01-01' AND cislo_zam ~ '^[0-9]+$'")).all()]
    jmena = {}
    for cz, nm in s.execute(_t(
            "SELECT cislo_zam, full_name FROM tenant.att_employee "
            "WHERE tenant_id=2 AND cislo_zam ~ '^[0-9]+$'")).all():
        try:
            jmena[int(cz)] = nm
        except Exception:
            pass
    ciny = {}
    for ec, nm in s.execute(_t(
            "SELECT ec_cislo, name FROM tenant.vyroba_cinnost WHERE ec_cislo IS NOT NULL")).all():
        try:
            ciny[int(ec)] = nm
        except Exception:
            pass
    prod_clause = ""
    if prod:
        prod_clause = " AND CisloZam NOT IN (" + ",".join(str(p) for p in prod) + ")"
    q = ("SELECT ID, DatumPripadu, CisloZam, DruhCinnosti, CisloZakazky, "
         "CasZacatek, CasKonec, CasCelkemVcRezii, ISNULL(ZamPoznamka,'') AS pozn "
         "FROM dbo.EC_Dochazka "
         "WHERE DatumPripadu>='2026-01-01' AND DatumPripadu<'2026-06-01'" + prod_clause +
         " ORDER BY DatumPripadu DESC, CasZacatek")
    out = []
    from modules.eurosoft_mcp.sql_client import get_cursor
    with get_cursor("DB_EC") as cur:
        cur.execute(q)
        cols = [d[0] for d in cur.description]
        for rec in cur.fetchall():
            r = {cols[i]: rec[i] for i in range(len(cols))}
            d = r.get("DatumPripadu")
            if d is None:
                continue
            try:
                cz = int(r.get("CisloZam"))
            except Exception:
                cz = None
            od = r.get("CasZacatek")
            kon = r.get("CasKonec")
            hv = r.get("CasCelkemVcRezii")
            hod = round(float(hv), 2) if hv is not None else None
            od_t = od.strftime("%H:%M") if od else None
            kon_t = kon.strftime("%H:%M") if kon else None
            den_iso = d.strftime("%Y-%m-%d")
            jm = jmena.get(cz) or ("Zam " + str(cz))
            dc = r.get("DruhCinnosti")
            cin = ciny.get(int(dc)) if dc is not None else None
            zak = r.get("CisloZakazky") or "Rezie"
            pozn = r.get("pozn") or ""
            out.append({
                "PraceAktivni": "", "CisloZakazky": zak, "JmenoPrijmeni": jm,
                "CisloZam": cz, "DruhCinnosti": dc, "CinnostText": cin,
                "DenVTydnu": _DOW_CZ[d.weekday()],
                "CasZacatek": d.strftime("%d.%m.%Y") + ((" " + od_t) if od_t else ""),
                "CasKonec": (kon.strftime("%d.%m.%Y %H:%M") if kon else None),
                "CasCelkem": hod, "Odkud": "z Centrály", "Smlouva": None,
                "Poznamka": pozn, "DatumPripadu": d.strftime("%d.%m.%Y"),
                "Rok": d.year, "Mesic": d.month,
                "_kind": "C", "_id": int(r.get("ID")) if r.get("ID") is not None else None,
                "_zak": zak, "_cin_id": None,
                "_od_d": (od.strftime("%Y-%m-%d") if od else den_iso), "_od_t": od_t,
                "_kon_d": (kon.strftime("%Y-%m-%d") if kon else None), "_kon_t": kon_t,
                "_hod": hod, "_pozn": pozn, "_src": "z Centrály", "_cz": cz, "_jm": jm,
            })
    return out


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
    # 'all' (Vše) = stejná data jako 'vse', jen bez omezení na poslední 2 měsíce
    base = "budoucnost" if obdobi == "budoucnost" else "vse"
    ds_code = _DZT_DATASET[base]
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        sql = s.execute(_t("SELECT sql_text FROM fw.data_set WHERE code=:c"), {"c": ds_code}).scalar()
        if not sql:
            return JSONResponse({"ok": False, "error": "dataset_missing"}, status_code=500)
        if obdobi == "all":
            # odstraň spodní mez „poslední 2 měsíce" → zůstane celé (d <= CURRENT_DATE)
            sql = sql.replace(
                "AND d >= (date_trunc('month', CURRENT_DATE) - INTERVAL '1 month')::date", "")
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
        if obdobi == "all":
            # Kancelář leden–květen z Centrály (read-only). Best-effort: bez Centrály přehled funguje dál.
            try:
                out += _dzt_ec_office_hist(s)
                out.sort(key=lambda r: (r.get("_od_d") or ""), reverse=True)
            except Exception as _e:  # noqa: BLE001
                import logging as _lg
                _lg.getLogger("dochazka_zak_tab").warning("EC hist read failed: %s", _e)
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


@doch_zak_tab_router.get("/app/dochazka-zak-tab/cinnosti")
def dochazka_zak_tab_cinnosti(req: Request) -> JSONResponse:
    """Seznam činností pro roletku ve formuláři úprav (id, ec_cislo, název)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid or not _dzt_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    from sqlalchemy import text as _t
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            rows = s.execute(_t(
                "SELECT id, ec_cislo, name FROM tenant.vyroba_cinnost "
                "WHERE COALESCE(name,'')<>'' ORDER BY name")).mappings().all()
        finally:
            s.close()
        out = [{"id": int(r["id"]), "ec": r["ec_cislo"], "name": r["name"]} for r in rows]
        return JSONResponse({"ok": True, "cinnosti": out})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)


def _dzt_parse_ts(d: str | None, t: str | None) -> str | None:
    """'YYYY-MM-DD' + 'HH:MM' → 'YYYY-MM-DD HH:MM' (None když chybí datum)."""
    d = (d or "").strip()
    if not d:
        return None
    t = (t or "").strip() or "00:00"
    return d + " " + t


@doch_zak_tab_router.post("/app/dochazka-zak-tab/save")
async def dochazka_zak_tab_save(req: Request) -> JSONResponse:
    """Uloží opravu řádku práce (tenant.vyroba_work). Edituje se jen kind='W'
    (práce na zakázce, app i Centrála). Absence (kind='A') se tu neupravují.
    Ukládají se: zakazka_ref, cinnost_id, od, konec, hodiny, poznamka.
    Pauza/Vedoucí poznámka/zaškrtávátka zatím nemají v DB místo — dodělá se."""
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
    kind = str((body or {}).get("kind") or "").upper()
    try:
        rid = int((body or {}).get("id"))
    except Exception:
        return JSONResponse({"ok": False, "error": "chybí id záznamu"}, status_code=400)
    if kind != "W":
        return JSONResponse({"ok": False, "error": "Tady lze upravit jen práci na zakázce. "
                             "Absence (dovolená/nemoc/lékař) se opravují v modulu Opravy docházky."},
                            status_code=400)
    zak = (str((body or {}).get("zakazka") or "").strip()) or None
    cin_raw = (body or {}).get("cinnost_id")
    try:
        cin_id = int(cin_raw) if cin_raw not in (None, "", "null") else None
    except Exception:
        cin_id = None
    od = _dzt_parse_ts((body or {}).get("od_d"), (body or {}).get("od_t"))
    if not od:
        return JSONResponse({"ok": False, "error": "Vyplň Začátek (datum a čas)."}, status_code=400)
    kon = _dzt_parse_ts((body or {}).get("kon_d"), (body or {}).get("kon_t"))
    pozn = (body or {}).get("poznamka")
    if pozn is not None:
        pozn = str(pozn)[:2000]
    # hodiny: klient posílá spočtený Čas; jinak dopočítáme z (konec-od). Nezáporné.
    hod = (body or {}).get("hodiny")
    try:
        hod = float(hod) if hod not in (None, "") else None
    except Exception:
        hod = None
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        # kontrola: řádek existuje a je to práce v našem tenantu
        cur = s.execute(_t("SELECT source_system, od, konec, hodiny FROM tenant.vyroba_work "
                           "WHERE id=:id AND tenant_id=2"), {"id": rid}).mappings().first()
        if not cur:
            return JSONResponse({"ok": False, "error": "Záznam nenalezen."}, status_code=404)
        # dopočet hodin, když je nezadal klient a máme konec
        if hod is None and kon is not None:
            r2 = s.execute(_t("SELECT EXTRACT(EPOCH FROM ((:kon)::timestamptz-(:od)::timestamptz))/3600.0"),
                           {"od": od, "kon": kon}).scalar()
            try:
                hod = round(float(r2), 2)
            except Exception:
                hod = None
        if hod is not None and hod < 0:
            return JSONResponse({"ok": False, "error": "Konec je před začátkem — zkontroluj časy."},
                                status_code=400)
        s.execute(_t(
            "UPDATE tenant.vyroba_work SET "
            " zakazka_ref=:zak, cinnost_id=:cin, od=(:od)::timestamptz, "
            " konec=CASE WHEN :kon IS NULL THEN NULL ELSE (:kon)::timestamptz END, "
            " hodiny=:hod, poznamka=:pozn, updated_at=now() "
            "WHERE id=:id AND tenant_id=2"),
            {"zak": zak, "cin": cin_id, "od": od, "kon": kon, "hod": hod,
             "pozn": pozn, "id": rid})
        s.commit()
        return JSONResponse({"ok": True, "id": rid, "hodiny": hod})
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
