"""Docházka po zakázkách — data pro vlastní stránku ve stylu standardu přehledů
(table.dokl, vzor pokladny.html). Peťa + Claude‑26, 22.7.2026.

Přehled zůstává definovaný v JEDNOM místě — data_setu `dochazka.zakazky_vse_list`
(resp. `dochazka.zakazky_budoucnost_list`). Endpoint jen vezme jeho SQL a spustí ho,
aby vlastní stránka renderovala TÁŽ data jako dřív framework grid. Jen čte (PG).

Gate = shodný s viditelností uzlu „🕒 Docházka" (11 lidí) + rodičovský bypass.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
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
                "WHERE COALESCE(name,'')<>'' AND COALESCE(active,true) "
                "ORDER BY name")).mappings().all()
        finally:
            s.close()
        out = [{"id": int(r["id"]), "ec": r["ec_cislo"], "name": r["name"]} for r in rows]
        return JSONResponse({"ok": True, "cinnosti": out})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)


@doch_zak_tab_router.get("/app/dochazka-zak-tab/zakazky")
def dochazka_zak_tab_zakazky(req: Request) -> JSONResponse:
    """Píchatelné zakázky pro našeptávač Zakázky ve formuláři (cislo, nazev, typ).
    Stejný zdroj jako Opravy docházky (tenant.zakazka, pichatelna=true), REZIE první."""
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
                "SELECT cislo, COALESCE(nazev,'') AS nazev, COALESCE(typ,'') AS typ "
                "FROM tenant.zakazka WHERE tenant_id=2 AND pichatelna=true "
                "ORDER BY (typ='REZIE') DESC, cislo")).mappings().all()
        finally:
            s.close()
        out = [{"cislo": r["cislo"], "nazev": r["nazev"], "typ": r["typ"]} for r in rows]
        return JSONResponse({"ok": True, "zakazky": out})
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


@doch_zak_tab_router.post("/app/dochazka-zak-tab/save-new")
async def dochazka_zak_tab_save_new(req: Request) -> JSONResponse:
    """Založí NOVÝ řádek práce (tenant.vyroba_work) pro osobu dle cislo_zam.
    source_system='app'. Vrací id nového řádku."""
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
    cz = str((body or {}).get("cislo_zam") or "").strip()
    if not cz:
        return JSONResponse({"ok": False, "error": "Chybí pracovník."}, status_code=400)
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
        emp_uid = s.execute(_t("SELECT user_id FROM tenant.att_employee "
                               "WHERE tenant_id=2 AND cislo_zam=:cz AND user_id IS NOT NULL LIMIT 1"),
                            {"cz": cz}).scalar()
        if not emp_uid:
            return JSONResponse({"ok": False, "error": "Pracovníka (č. " + cz + ") se nepodařilo najít."},
                                status_code=400)
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
        new_id = s.execute(_t(
            "INSERT INTO tenant.vyroba_work "
            " (tenant_id, user_id, cislo_zam, datum, od, konec, zakazka_ref, cinnost_id, "
            "  hodiny, poznamka, source_system, created_by, created_at, updated_at) "
            "VALUES (2, :uid, :cz, (:od)::timestamptz::date, (:od)::timestamptz, "
            "  CASE WHEN :kon IS NULL THEN NULL ELSE (:kon)::timestamptz END, "
            "  :zak, :cin, :hod, :pozn, 'app', :creator, now(), now()) RETURNING id"),
            {"uid": emp_uid, "cz": cz, "od": od, "kon": kon, "zak": zak, "cin": cin_id,
             "hod": hod, "pozn": pozn, "creator": uid}).scalar()
        s.commit()
        return JSONResponse({"ok": True, "id": new_id, "hodiny": hod})
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


@doch_zak_tab_router.post("/app/dochazka-zak-tab/save-doch-meta")
async def dochazka_zak_tab_save_doch_meta(req: Request) -> JSONResponse:
    """Uloží k docházkovému záznamu (att_entry) POZNÁMKY a zaškrtávátka, které
    NEmají vliv na mzdy: note (zaměstnanec pozn.), vedouci_poznamka, ved_schvaleno.
    Zapisuje na AKTIVNÍ řádek — když byl původní opraven přes fix/entry (supersede),
    najde nový řádek (source_id=orig). Časy/hodiny se řeší přes fix/entry zvlášť."""
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
    try:
        orig = int((body or {}).get("id"))
    except Exception:
        return JSONResponse({"ok": False, "error": "chybí id"}, status_code=400)
    has_note = "note" in (body or {})
    has_vp = "vedouci_poznamka" in (body or {})
    has_vs = "ved_schvaleno" in (body or {})
    note = str((body or {}).get("note") or "")[:2000] if has_note else None
    vp = str((body or {}).get("vedouci_poznamka") or "")[:2000] if has_vp else None
    vs = bool((body or {}).get("ved_schvaleno")) if has_vs else None
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        # aktivní řádek: nový (source_id=orig) má přednost před orig samotným
        aid = s.execute(_t(
            "SELECT id FROM tenant.att_entry "
            "WHERE tenant_id=2 AND COALESCE(status,'')<>'superseded' AND (source_id=:o OR id=:o) "
            "ORDER BY (id=:o)::int ASC, id DESC LIMIT 1"), {"o": orig}).scalar()
        if not aid:
            return JSONResponse({"ok": False, "error": "Záznam nenalezen (nebo byl nahrazen)."},
                                status_code=404)
        sets, params = [], {"id": aid}
        if has_note:
            sets.append("note=:note"); params["note"] = note
        if has_vp:
            sets.append("vedouci_poznamka=:vp"); params["vp"] = vp
        if has_vs:
            sets.append("ved_schvaleno=:vs"); params["vs"] = vs
        if not sets:
            return JSONResponse({"ok": True, "id": aid, "note": "nic ke změně"})
        s.execute(_t("UPDATE tenant.att_entry SET " + ", ".join(sets) + " WHERE id=:id AND tenant_id=2"),
                  params)
        s.commit()
        return JSONResponse({"ok": True, "id": aid})
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


@doch_zak_tab_router.post("/app/dochazka-zak-tab/delete-usek")
async def dochazka_zak_tab_delete_usek(req: Request) -> JSONResponse:
    """Smaže JEDEN výrobní úsek (řádek tenant.vyroba_work, kind='W') — zneaktivní ho
    (is_active=false) + audit do poznámky (kdo/proč). Postup dle Jirky (24.7.2026,
    ověřeno v kódu): work_alloc NEMAZAT (osiřel by řádek), sync is_active nevrací,
    v přehledech (Docházka new i Dušanův) je is_active filtrované → úsek zmizí, ale
    v DB zůstane pro dohledatelnost. Vratné (is_active zpět na true). Povinný důvod."""
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
    try:
        rid = int((body or {}).get("id"))
    except Exception:
        return JSONResponse({"ok": False, "error": "chybí id řádku"}, status_code=400)
    reason = str((body or {}).get("reason") or "").strip()[:300]
    if not reason:
        return JSONResponse({"ok": False, "error": "Důvod smazání je povinný (kvůli auditu)."}, status_code=400)
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        row = s.execute(_t("SELECT is_active, source_system FROM tenant.vyroba_work "
                           "WHERE id=:id AND tenant_id=2"), {"id": rid}).mappings().first()
        if not row:
            return JSONResponse({"ok": False, "error": "Úsek nenalezen."}, status_code=404)
        if row["is_active"] is False:
            return JSONResponse({"ok": True, "id": rid, "note": "už bylo smazané"})
        actor = s.execute(_t(
            "SELECT COALESCE(NULLIF(TRIM(COALESCE(first_name,'')||' '||COALESCE(last_name,'')),''),'?') "
            "FROM public.users WHERE id=:u"), {"u": int(uid)}).scalar() or "?"
        tag = "🗑 SMAZÁNO (" + actor + "): " + reason
        s.execute(_t(
            "UPDATE tenant.vyroba_work SET is_active=false, updated_at=now(), "
            " poznamka = CASE WHEN COALESCE(poznamka,'')='' THEN :tag ELSE poznamka || ' / ' || :tag END "
            "WHERE id=:id AND tenant_id=2 AND is_active=true"), {"id": rid, "tag": tag})
        s.commit()
        return JSONResponse({"ok": True, "id": rid})
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


# ── Import z výkazu práce (EUROSOFT Work Report .xlsx) ────────────────────────
# List „Stunden": C2=pracovník (jen zobrazení), G5=číslo zam (podle něj se páruje),
# G2=výchozí zakázka, C5=výchozí druh činnosti. Datové řádky 8..34:
#   B=datum, C=hodiny (NETTO, pauza už odečtená), D=od, E=do, F=pauza,
#   G=činnost (název), H=činnost č. (= vyroba_cinnost.ec_cislo), I=poznámka, J=zakázka.
# Zapisujeme do tenant.vyroba_work stejně jako „Nový" (save-new), source_system='app'
# (jinak by řádky nebyly v přehledu — dataset filtruje source_system IN ('app','centrala1')).
# Ochrana proti duplicitě: (user_id, datum, od) — opakovaný import téhož výkazu nepřidá hodiny.
def _dzt_norm_date(v) -> str | None:
    """Různé podoby datumu z Excelu → 'YYYY-MM-DD' (None, když prázdné/nečitelné)."""
    import datetime as _dt
    if v is None:
        return None
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%Y/%m/%d"):
        try:
            return _dt.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s[:10]


def _dzt_norm_time(v) -> str | None:
    """'HH:MM' z time/datetime/textu (None, když prázdné)."""
    import datetime as _dt
    if v is None:
        return None
    if isinstance(v, (_dt.time, _dt.datetime)):
        return v.strftime("%H:%M")
    s = str(v).strip()
    if not s:
        return None
    try:
        p = s.split(":")
        return "%02d:%02d" % (int(p[0]), int(p[1]))
    except Exception:
        return s[:5]


def _dzt_parse_vykaz(raw: bytes) -> tuple[dict, list[dict]]:
    """Naparsuje jeden Work Report (.xlsx) → (hlavička, řádky). Bez DB."""
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    ws = wb["Stunden"] if "Stunden" in wb.sheetnames else wb.worksheets[0]

    def _c(ref):
        return ws[ref].value
    hdr = {
        "worker_name": (str(_c("C2")).strip() if _c("C2") is not None else ""),
        "cislo_zam": (str(_c("G5")).strip() if _c("G5") is not None else ""),
        "order_default": (str(_c("G2")).strip() if _c("G2") is not None else ""),
        "customer": (str(_c("C4")).strip() if _c("C4") is not None else ""),
    }
    rows: list[dict] = []
    for r in range(8, 35):
        datum = _dzt_norm_date(ws.cell(r, 2).value)   # B
        if not datum:
            continue
        hraw = ws.cell(r, 3).value                     # C = hodiny (netto)
        try:
            hod = float(hraw) if hraw not in (None, "") else 0.0
        except Exception:
            hod = 0.0
        if hod == 0:
            continue
        cin_cislo = ws.cell(r, 8).value                # H
        try:
            cin_cislo = int(cin_cislo) if cin_cislo not in (None, "") else None
        except Exception:
            cin_cislo = None
        zak = ws.cell(r, 10).value                      # J
        zak = (str(zak).strip() if zak not in (None, "") else "") or hdr["order_default"]
        pozn = ws.cell(r, 9).value                       # I
        rows.append({
            "datum": datum,
            "hodiny": round(hod, 2),
            "od": _dzt_norm_time(ws.cell(r, 4).value),   # D
            "do": _dzt_norm_time(ws.cell(r, 5).value),   # E
            "cin_name": (str(ws.cell(r, 7).value).strip() if ws.cell(r, 7).value else ""),  # G
            "cin_cislo": cin_cislo,
            "zakazka": zak,
            "poznamka": (str(pozn).strip() if pozn not in (None, "") else ""),
        })
    try:
        wb.close()
    except Exception:
        pass
    return hdr, rows


@doch_zak_tab_router.post("/app/dochazka-zak-tab/import-vykaz")
async def dochazka_zak_tab_import_vykaz(
    req: Request,
    files: list[UploadFile] = File(...),
    commit: str = Form("0"),
) -> JSONResponse:
    """Import výkazu(ů) práce z Excelu do tenant.vyroba_work.
    commit='0' → náhled (nic se nezapíše); commit='1' → zápis nenaduplikovaných řádků.
    Vrací per-soubor rozpis s ověřením pracovníka/činnosti/zakázky a stavem každého řádku."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if not _dzt_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    do_commit = str(commit or "0").strip() in ("1", "true", "yes", "on")
    if not files:
        return JSONResponse({"ok": False, "error": "Nebyl nahrán žádný soubor."}, status_code=400)

    # Načti obsah souborů + naparsuj (limit velikosti)
    parsed: list[dict] = []
    for f in files:
        try:
            raw = await f.read()
        except Exception:
            raw = b""
        if not raw:
            parsed.append({"filename": f.filename, "error": "Prázdný soubor."})
            continue
        if len(raw) > 6 * 1024 * 1024:
            parsed.append({"filename": f.filename, "error": "Soubor je příliš velký (max 6 MB)."})
            continue
        try:
            hdr, rows = _dzt_parse_vykaz(raw)
        except Exception as exc:  # noqa: BLE001
            parsed.append({"filename": f.filename, "error": "Nepodařilo se přečíst Excel: " + str(exc)[:120]})
            continue
        parsed.append({"filename": f.filename, "hdr": hdr, "rows": rows})

    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        # Číselník činností: ec_cislo→(id,name) + name(lower)→id
        cin_by_ec: dict[int, tuple[int, str]] = {}
        cin_by_name: dict[str, int] = {}
        for cid, ec, nm in s.execute(_t(
                "SELECT id, ec_cislo, name FROM tenant.vyroba_cinnost "
                "WHERE COALESCE(active,true)")).all():
            if ec is not None:
                try:
                    cin_by_ec[int(ec)] = (int(cid), nm)
                except Exception:
                    pass
            if nm:
                cin_by_name[str(nm).strip().lower()] = int(cid)

        out_files = []
        total = {"ok": 0, "duplicate": 0, "error": 0, "inserted": 0}
        for pf in parsed:
            if pf.get("error"):
                out_files.append({"filename": pf["filename"], "error": pf["error"]})
                total["error"] += 1
                continue
            hdr, rows = pf["hdr"], pf["rows"]
            cz = str(hdr.get("cislo_zam") or "").strip()
            emp_uid = None
            emp_name = None
            if cz:
                res = s.execute(_t(
                    "SELECT user_id, full_name FROM tenant.att_employee "
                    "WHERE tenant_id=2 AND cislo_zam=:cz AND user_id IS NOT NULL LIMIT 1"),
                    {"cz": cz}).first()
                if res:
                    emp_uid, emp_name = res[0], res[1]
            worker_ok = emp_uid is not None

            out_rows = []
            f_sum = {"ok": 0, "duplicate": 0, "error": 0}
            for r in rows:
                warn = []
                status = "ok"
                # činnost
                cin_id = None
                cin_db = None
                if r["cin_cislo"] is not None and r["cin_cislo"] in cin_by_ec:
                    cin_id, cin_db = cin_by_ec[r["cin_cislo"]]
                elif r["cin_name"] and r["cin_name"].lower() in cin_by_name:
                    cin_id = cin_by_name[r["cin_name"].lower()]
                    cin_db = r["cin_name"]
                if cin_id is None:
                    warn.append("činnost nerozpoznána (uloží se bez druhu)")
                # zakázka — kontrola píchatelnosti (jen varování)
                zak = (r["zakazka"] or "").strip() or None
                zak_ok = True
                if zak:
                    zr = s.execute(_t(
                        "SELECT COALESCE(pichatelna,false), COALESCE(nazev,'') FROM tenant.zakazka "
                        "WHERE tenant_id=2 AND cislo=:z LIMIT 1"), {"z": zak}).first()
                    if not zr:
                        zak_ok = False
                        warn.append("zakázka '" + zak + "' neexistuje")
                    elif not zr[0]:
                        zak_ok = False
                        warn.append("zakázka '" + zak + "' není píchatelná")
                # časy
                od = (r["datum"] + " " + r["od"]) if r["od"] else (r["datum"] + " 00:00")
                kon = (r["datum"] + " " + r["do"]) if r["do"] else None
                # stav řádku
                dup = False
                if not worker_ok:
                    status = "error"
                    warn.insert(0, "pracovník č. " + (cz or "?") + " nenalezen")
                else:
                    dup = bool(s.execute(_t(
                        "SELECT 1 FROM tenant.vyroba_work "
                        "WHERE tenant_id=2 AND user_id=:u AND datum=:d "
                        "  AND od=(:od)::timestamptz AND is_active LIMIT 1"),
                        {"u": emp_uid, "d": r["datum"], "od": od}).first())
                    if dup:
                        status = "duplicate"
                out_rows.append({
                    "datum": r["datum"], "od": r["od"], "do": r["do"], "hodiny": r["hodiny"],
                    "cin_cislo": r["cin_cislo"], "cin_name": r["cin_name"], "cin_id": cin_id,
                    "cin_db": cin_db, "zakazka": zak, "zakazka_ok": zak_ok,
                    "poznamka": r["poznamka"], "status": status, "warn": warn,
                    "_od": od, "_kon": kon, "_emp_uid": emp_uid, "_cz": cz, "_cin_id": cin_id,
                })
                f_sum[status] = f_sum.get(status, 0) + 1

            # commit = zapiš jen řádky se status 'ok'
            inserted_ids = []
            if do_commit and worker_ok:
                for orow in out_rows:
                    if orow["status"] != "ok":
                        continue
                    try:
                        nid = s.execute(_t(
                            "INSERT INTO tenant.vyroba_work "
                            " (tenant_id, user_id, cislo_zam, datum, od, konec, zakazka_ref, cinnost_id, "
                            "  hodiny, poznamka, source_system, created_by, created_at, updated_at) "
                            "VALUES (2, :uid, :cz, (:od)::timestamptz::date, (:od)::timestamptz, "
                            "  CASE WHEN :kon IS NULL THEN NULL ELSE (:kon)::timestamptz END, "
                            "  :zak, :cin, :hod, :pozn, 'app', :creator, now(), now()) RETURNING id"),
                            {"uid": orow["_emp_uid"], "cz": orow["_cz"], "od": orow["_od"],
                             "kon": orow["_kon"], "zak": orow["zakazka"], "cin": orow["_cin_id"],
                             "hod": orow["hodiny"], "pozn": (orow["poznamka"] or None),
                             "creator": uid}).scalar()
                        inserted_ids.append(int(nid))
                        orow["status"] = "inserted"
                    except Exception as exc:  # noqa: BLE001
                        orow["status"] = "error"
                        orow["warn"].append("zápis selhal: " + str(exc)[:80])
                        f_sum["error"] = f_sum.get("error", 0) + 1

            # očisti interní klíče z výstupu
            for orow in out_rows:
                for k in ("_od", "_kon", "_emp_uid", "_cz", "_cin_id"):
                    orow.pop(k, None)

            total["ok"] += f_sum.get("ok", 0) if not do_commit else 0
            total["duplicate"] += f_sum.get("duplicate", 0)
            total["error"] += f_sum.get("error", 0)
            total["inserted"] += len(inserted_ids)
            out_files.append({
                "filename": pf["filename"],
                "worker": {"cislo": cz, "name_excel": hdr.get("worker_name"),
                           "name_db": emp_name, "resolved": worker_ok},
                "customer": hdr.get("customer"),
                "order_default": hdr.get("order_default"),
                "rows": out_rows,
                "summary": f_sum,
                "inserted_ids": inserted_ids,
            })

        if do_commit:
            s.commit()
        return JSONResponse({"ok": True, "mode": ("commit" if do_commit else "preview"),
                             "files": out_files, "totals": total})
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
