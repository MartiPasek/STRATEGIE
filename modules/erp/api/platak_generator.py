# -*- coding: utf-8 -*-
"""Generátor platáků (task #44/#45) — návrh k platbě → .p11 (CZK) / .f84 (EUR).

PREVIEW (nic nezapisuje) + COMMIT (zapíše soubor + úhradový zámek) + SMAZAT
(smaže soubor + uvolní zámek → saldo zpět) + seznam vygenerovaných.

Endpointy (na sdíleném api_router, prefix /api/v1/erp):
  GET  /app/platby/platak/preview?firma=1|2|all&mena=CZK|EUR|all   — náhled
  POST /app/platby/platak/commit   {firma, mena}                    — vygeneruj
  POST /app/platby/platak/smazat   {platak_id}                      — smaž + odemkni
  GET  /app/platby/platak/vygenerovane                              — seznam

Model (Marti 8.7.2026): preview-first; anti-podvod JEN VARUJE (negeneruje se nic
tvrdě); datum splatnosti VŽDY dnešní (Peťa); zámek jako v Heliosu = měkký při
vytvoření platáku (tenant.platak_uhrada_lock s platak_id), smazání platáku ho uvolní.

Scope: rodiče + Petra (18) + cockpit. Claude ID23.
"""
import json as _j
import base64 as _b64
import datetime as _dt

from starlette.requests import Request
from starlette.responses import JSONResponse

from modules.erp.api.router import (
    api_router,
    _uid_from_token_or_cookie,
    _is_parent,
    _is_cockpit,
)

# ------------------------------------------------------------------ render (1:1)
# Převzato beze změny z scripts/rb/gemini_render.py (byte-exact 12/12 vzorků).


def _r(fill, val, width):
    return (fill + str(val))[-width:]


def _l(val, width):
    return (str(val) + " " * width)[:width]


def _ucet(cislouctu):
    s = str(cislouctu or "")
    if "-" in s:
        pre, cis = s.split("-", 1)
        return _r("0000000000", pre, 6), _r("0000000000", cis, 10)
    return "000000", _r("0000000000", s, 10)


def render_tuz_line(porad, datum_vytv, castka, ks, vs, ss, kod_ustavu_prij,
                    ucet_prij, ucet_klient, datum_splat, ucel):
    hal = int(round(float(castka) * 100))
    pre_prij, cis_prij = _ucet(ucet_prij)
    ucel = ucel or ""
    parts = [
        _r("000000", porad, 6), "11", datum_vytv, "5500", "   ",
        _l(kod_ustavu_prij, 4), "   ", _r("00000000000000", hal, 15),
        datum_splat, _r("0000000000", ks or "", 10), _r("0000000000", vs or "", 10),
        _r("0000000000", ss or "", 10), "000000", _r("000000000", ucet_klient, 10),
        pre_prij, cis_prij, _l(ucel, 140), " " * 20, " " * 20,
        _r("000000000000", vs or "", 10), "0000000000", ucel[:140],
    ]
    return "".join(parts)


def render_zahr_line(porad, datum_vytv8, castka, mena, up_nazev, up_ulice, up_misto,
                     zup_nazev, op_firma, op_ulice, op_misto, zop_nazev, nas_ucet, iban,
                     poplatky, tit, cil_zeme, hlav_id, p1, p2, p3, p4, priorita, nas_mena,
                     swift, datum_splat):
    castka_s = "%.2f" % float(castka)
    parts = [
        "INT", _r("000000", porad, 6), datum_vytv8, _l(up_nazev, 35), _l(up_ulice, 35),
        _l(up_misto, 35), _l(zup_nazev, 35), _l(op_firma, 35), _l(op_ulice, 35),
        _l(op_misto, 35), _l(zop_nazev, 35), _r("00000000000000", castka_s, 16),
        (mena or ""), _r("000000000", nas_ucet, 10), _l(iban, 34),
        _l((poplatky or "") + "   ", 3), _r("000", tit or "", 3),
        _l((cil_zeme or "") + "  ", 2), "ID:" + _r("00000", hlav_id, 6) + ":",
        _l(p1, 35), _l(p2, 35), _l(p3, 35), _l(p4, 25), " " * 20,
        ("01" if int(priorita or 0) == 0 else "02"), _l((nas_mena or "") + "   ", 3),
        _r("0000000000", hlav_id, 10), "02", "02", " " * 123, _l(swift, 11),
        "000000", datum_splat,
    ]
    return "".join(parts)


# ------------------------------------------------------------------ konfigurace
_NAS_UCET = {1: "9251651001", 2: "3047813002"}   # plátcovské účty (stejné číslo pro CZK i EUR; měna účtu se řídí měnou platby)
_FIRMA_KOD = {1: "EC", 2: "ES"}
_PLATEBNI_DNY = {1, 3}   # Út + Čt (Marti 7.7.)


def _next_platebni_den(dnes):
    d = dnes + _dt.timedelta(days=1)
    for _ in range(14):
        if d.weekday() in _PLATEBNI_DNY:
            return d
        d = d + _dt.timedelta(days=1)
    return dnes + _dt.timedelta(days=1)


def _clean(v):
    if v is None:
        return ""
    return str(v).replace(chr(0), "").strip()


def _mcp():
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    m = get_eurosoft_mcp_client()
    if m is None:
        raise RuntimeError("EUROSOFT MCP nedostupný")
    return m


def _ec_query(sql):
    """DB_EC read přes EUROSOFT MCP → list[dict]."""
    raw = _mcp().call_tool_sync("eurosoft_strategie_query_raw",
                                {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
    r = (_j.loads(raw) if isinstance(raw, str) else raw) or {}
    if not r.get("ok"):
        raise RuntimeError("DB_EC: " + str(r.get("message") or r.get("error"))[:200])
    cols = r.get("columns") or []
    return [dict(zip(cols, row)) if isinstance(row, list) else row for row in (r.get("rows") or [])]


def _mcp_file_write(abs_dir, fn, b64c):
    raw = _mcp().call_tool_sync("eurosoft_eurosoft_file_write",
                                {"user_namespace": "rw", "base_override": abs_dir, "path": fn,
                                 "content": b64c, "encoding": "base64", "mode": "overwrite"},
                                conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if not (isinstance(r, dict) and r.get("ok")):
        raise RuntimeError("MCP zápis: " + str((r or {}).get("error"))[:160])
    return r


def _mcp_file_delete(abs_dir, fn):
    raw = _mcp().call_tool_sync("eurosoft_eurosoft_file_delete",
                                {"user_namespace": "rw", "base_override": abs_dir, "path": fn},
                                conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    return isinstance(r, dict) and r.get("ok")


def _mcp_file_read(abs_dir, fn):
    """Přečti soubor přes MCP (RO) → bytes."""
    raw = _mcp().call_tool_sync("eurosoft_eurosoft_file_read",
                                {"user_namespace": "ro", "base_override": abs_dir, "path": fn,
                                 "encoding": "base64"}, conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict) and r.get("ok") is False:
        raise RuntimeError(str(r.get("error"))[:160])
    b64 = (r.get("content") or r.get("data") or "") if isinstance(r, dict) else str(r)
    return _b64.b64decode(b64)


def _mcp_file_list(abs_dir):
    """Výpis složky přes MCP (RO) → list[{nazev, typ, velikost}]."""
    raw = _mcp().call_tool_sync("eurosoft_eurosoft_file_list",
                                {"user_namespace": "ro", "base_override": abs_dir, "subpath": ""},
                                conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict) and r.get("ok") is False:
        raise RuntimeError(str(r.get("error"))[:160])
    items = (r.get("items") or r.get("files") or r.get("entries") or []) if isinstance(r, dict) else (r or [])
    out = []
    for it in items:
        if isinstance(it, dict):
            out.append({"nazev": it.get("name") or it.get("filename") or it.get("path"),
                        "typ": it.get("type") or ("dir" if it.get("is_dir") else "file"),
                        "velikost": it.get("size")})
        else:
            out.append({"nazev": it, "typ": "", "velikost": None})
    return out


# ------------------------------------------------------------------ jádro
_NAVRH_SQL = (
    "WITH u AS (SELECT id_fak, SUM(castka) AS paid FROM ("
    "  SELECT id_fak, castka_po_bance AS castka FROM tenant.oz_uhrady WHERE firma=1"
    "  UNION ALL SELECT id_fak, castka FROM tenant.platak_uhrada_lock) x GROUP BY id_fak) "
    "SELECT p.id, p.mena, p.doklad, COALESCE(NULLIF(p.dodavatel,''),p.zkratka,'?') dod, "
    "  COALESCE(p.var_symbol,'') vs, to_char(p.splatnost::date,'DD.MM.YYYY') splat, "
    "  p.splatnost::date splat_d, "
    "  ((CASE WHEN p.mena='CZK' THEN p.suma_kc ELSE p.suma_val END) - COALESCE(u.paid,0)) open_saldo, "
    "  COALESCE(p.popis,'') popis, (CASE WHEN p.rada IN ('501','531','541') THEN 2 ELSE 1 END) AS ufirma, "
    "  p.skonto, p.skonto_do "
    "FROM tenant.oz_pf_platba p LEFT JOIN u ON u.id_fak=p.id "
    "WHERE p.realizovano=1 AND NOT p.fin_zakaz AND p.nehradit=0 AND p.suma_po_zao>0 "
    "  AND p.obdobi>22 AND p.rada NOT LIKE '52%' "
    "  AND p.splatnost::date <= :cutoff "
    "  AND ((CASE WHEN p.mena='CZK' THEN p.suma_kc ELSE p.suma_val END) - COALESCE(u.paid,0)) > 0.5 "
    "{ffilter}{mfilter} ORDER BY p.mena, p.splatnost"
)


def _parse_cutoff(v):
    """ISO 'YYYY-MM-DD' -> date; prazdne/spatne -> dnes+7 (Peta: 'splatnost do')."""
    if v:
        try:
            return _dt.date.fromisoformat(str(v)[:10])
        except Exception:
            pass
    return _dt.date.today() + _dt.timedelta(days=7)


def _build_groups(s, firma, mena_f, cutoff=None):
    """Návrh → účty z DB_EC → verdikt (jen varuje) → payment-day. Vrací
    (groups, meta). cutoff = posledni datum splatnosti (Peta: 'splatnost do'). NIC nezapisuje."""
    from sqlalchemy import text as _t
    if cutoff is None:
        cutoff = _dt.date.today() + _dt.timedelta(days=7)
    params = {"cutoff": cutoff}
    ffilter = ""
    if firma in ("1", "2"):
        params["ff"] = int(firma)
        ffilter = " AND (CASE WHEN p.rada IN ('501','531','541') THEN 2 ELSE 1 END) = :ff "
    mfilter = ""
    if mena_f in ("CZK", "EUR"):
        params["mm"] = mena_f
        mfilter = " AND p.mena = :mm "
    sql = _NAVRH_SQL.replace("{ffilter}", ffilter).replace("{mfilter}", mfilter)
    rows = s.execute(_t(sql), params).fetchall()

    navrh = []
    for r in rows:
        navrh.append({
            "id_fak": int(r[0]), "mena": r[1], "doklad": r[2] or "", "dodavatel": r[3] or "",
            "vs": r[4] or "", "splatnost": r[5], "splat_d": r[6],
            "castka": round(float(r[7]), 2) if r[7] is not None else 0.0,
            "popis": (r[8] or "")[:70], "firma": int(r[9]) if r[9] is not None else 1,
            "skonto": round(float(r[10]), 2) if r[10] is not None else 0.0,
            "skonto_do": r[11],
        })

    dnes = _dt.date.today()
    nextpd = _next_platebni_den(dnes)
    meta = {"dnes": dnes, "nextpd": nextpd, "cutoff": cutoff,
            "datum_vytv6": dnes.strftime("%y%m%d"), "datum_vytv8": dnes.strftime("%Y%m%d"),
            "datum_splat6": dnes.strftime("%y%m%d")}   # Peťa: splatnost VŽDY dnešní

    # Skonto (Peta 13.7.): když dnes <= skonto_do, plať SNÍŽENOU částku (částka − skonto).
    # Zámek drží PLNOU částku (saldo nevisí); Helios při zaúčtování výpisu doplní úhradu „Skonto".
    for _it in navrh:
        _sk = _it.get("skonto") or 0.0
        _it["skonto_uplat"] = 0.0
        if _sk and _it.get("skonto_do"):
            try:
                if dnes <= _dt.date.fromisoformat(str(_it["skonto_do"])[:10]):
                    _it["skonto_uplat"] = round(float(_sk), 2)
            except Exception:
                pass
        _it["castka_platba"] = round(float(_it["castka"]) - _it["skonto_uplat"], 2)

    # účty příjemců z DB_EC (bulk)
    ucty, ec_err = {}, None
    ids = sorted({it["id_fak"] for it in navrh})
    if ids:
        try:
            for er in _ec_query(
                "SELECT d.ID id_fak, d.DodFak, d.CisloOrg dok_org, bs.CisloUctu, bs.IBANElektronicky, "
                "  bs.IBANPisemny, bs.IDUstavu, bs.IDOrg, bs.CilovaZeme, bs.UcetVSeznamuSpravDane sd, "
                "  bu.KodUstavu, bu.SWIFTUstavu, bu.NazevUstavu, org.CisloOrg ucet_org, org.Firma org_firma, "
                "  org.Ulice org_ulice, org.UliceSCisly org_ulice2, org.Misto org_misto, org.PSC org_psc, "
                "  org.IdZeme org_zeme, zbu.Nazev zbu_nazev, zorg.Nazev zorg_nazev "
                "FROM TabDokladyZbozi d "
                "LEFT JOIN TabBankSpojeni bs ON bs.ID = d.IDBankSpoj "
                "LEFT JOIN TabPenezniUstavy bu ON bu.ID = bs.IDUstavu "
                "LEFT JOIN TabCisOrg org ON org.ID = bs.IDOrg "
                "LEFT JOIN TabZeme zbu ON zbu.ISOKod = SUBSTRING(bu.SWIFTUstavu,5,2) "
                "LEFT JOIN TabZeme zorg ON zorg.ISOKod = bs.CilovaZeme "
                "WHERE d.ID IN (" + ",".join(str(i) for i in ids) + ")"):
                ucty[int(er.get("id_fak"))] = er
        except Exception as exc:
            ec_err = str(exc)[:200]

    buckets = {}
    for it in navrh:
        acc = ucty.get(it["id_fak"], {}) or {}
        warns = []
        sp = it["splat_d"] or dnes
        it["plati"] = bool(sp <= cutoff)

        dok_org = _clean(acc.get("dok_org"))
        ucet_org = _clean(acc.get("ucet_org"))
        sd = acc.get("sd")
        verdikt = "ok"
        has_ucet = _clean(acc.get("CisloUctu")) or _clean(acc.get("IBANElektronicky")) or _clean(acc.get("IBANPisemny"))
        if not acc:
            verdikt = "chybi"; warns.append("Faktura nenalezena v DB_EC")
        elif not has_ucet:
            verdikt = "chybi"; warns.append("Chybí účet příjemce na faktuře")
        else:
            if dok_org and ucet_org and dok_org != ucet_org:
                verdikt = "podezrely"
                warns.append("Účet nepatří dodavateli z faktury (org %s != %s)" % (ucet_org, dok_org))
            if not (sd in (1, "1", True)):
                if verdikt == "ok":
                    verdikt = "amber"
                warns.append("Účet není zveřejněný u správce daně (§109)")

        if it["mena"] == "CZK":
            ud = _clean(acc.get("CisloUctu"))
            if _clean(acc.get("KodUstavu")):
                ud += "/" + _clean(acc.get("KodUstavu"))
        else:
            ud = _clean(acc.get("IBANElektronicky")) or _clean(acc.get("IBANPisemny"))
        it["acc"] = acc
        it["verdikt"] = verdikt
        it["warns"] = warns
        it["ucet"] = ud
        buckets.setdefault((it["firma"], it["mena"]), []).append(it)

    meta["ec_err"] = ec_err
    return buckets, meta


def _render_item(it, porad, meta):
    """Vyrenderuj jeden řádek platáku pro položku (nebo None u chybâjícího účtu)."""
    if it["verdikt"] == "chybi":
        return None
    acc = it["acc"]
    mena = it["mena"]
    nas = _NAS_UCET.get(it["firma"], "")
    if mena == "CZK":
        return render_tuz_line(
            porad=porad, datum_vytv=meta["datum_vytv6"], castka=it.get("castka_platba", it["castka"]), ks="", vs=it["vs"],
            ss="", kod_ustavu_prij=_clean(acc.get("KodUstavu")), ucet_prij=_clean(acc.get("CisloUctu")),
            ucet_klient=nas, datum_splat=meta["datum_splat6"],
            ucel=(it["doklad"] + " " + it["dodavatel"]).strip())
    iban = _clean(acc.get("IBANElektronicky")) or _clean(acc.get("IBANPisemny")).replace(" ", "")
    zeme = _clean(acc.get("org_zeme")) or _clean(acc.get("CilovaZeme"))
    op_misto = (_clean(acc.get("org_psc")) + " " + _clean(acc.get("org_misto"))).strip()
    return render_zahr_line(
        porad=porad, datum_vytv8=meta["datum_vytv8"], castka=it.get("castka_platba", it["castka"]), mena="EUR",
        up_nazev=_clean(acc.get("NazevUstavu")), up_ulice="", up_misto="",
        zup_nazev=_clean(acc.get("zbu_nazev")), op_firma=_clean(acc.get("org_firma")),
        op_ulice=_clean(acc.get("org_ulice")) or _clean(acc.get("org_ulice2")),
        op_misto=op_misto, zop_nazev=_clean(acc.get("zorg_nazev")), nas_ucet=nas, iban=iban,
        poplatky="SHA", tit="", cil_zeme=zeme, hlav_id=it["id_fak"], p1=it["vs"], p2="", p3="",
        p4="", priorita=0, nas_mena="EUR", swift=_clean(acc.get("SWIFTUstavu")),
        datum_splat=meta["datum_splat6"])


def _target(firma, mena, dnes, now):
    """(abs_dir, filename) pro platák."""
    kod = _FIRMA_KOD.get(firma, "?")
    ymd = dnes.strftime("%Y%m%d")
    abs_dir = "D:\\data\\RB\\Platební příkazy\\%s\\%s" % (kod, ymd)
    ext = "p11" if mena == "CZK" else "f84"
    pref = "PAY_TUZ" if mena == "CZK" else "PAY_ZAHR"
    tstamp = "%d-%02d-%02d" % (now.hour, now.minute, now.second)   # hodina bez vodicí nuly
    fn = "%s_%s_%s.%s" % (pref, dnes.strftime("%d-%m-%Y"), tstamp, ext)
    return abs_dir, fn


# ------------------------------------------------------------------ endpointy
@api_router.get("/app/platby/platak/preview")
def platak_preview(req: Request):
    """Náhled — NIC nezapisuje."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        firma = (req.query_params.get("firma") or "all").strip()
        mena_f = (req.query_params.get("mena") or "all").strip().upper()
        cutoff = _parse_cutoff(req.query_params.get("splatnost_do"))
        buckets, meta = _build_groups(s, firma, mena_f, cutoff)
        if not buckets:
            return {"ok": True, "skupiny": [], "pocet": 0,
                    "dnes": meta["dnes"].strftime("%d.%m.%Y"),
                    "pristi_platebni_den": meta["nextpd"].strftime("%d.%m.%Y"),
                    "info": ("POZOR: účty z DB_EC se nenačetly (%s)" % meta["ec_err"]) if meta["ec_err"] else
                            "V návrhu není nic k platbě pro tento filtr."}
        skupiny = []
        pocet = 0
        for (frm, mena), items in sorted(buckets.items(), key=lambda k: (k[0][0], k[0][1])):
            pocet += len(items)
            out_items, porad = [], 0
            for it in items:
                line = None
                if it["verdikt"] != "chybi":
                    porad += 1
                    line = _render_item(it, porad, meta)
                out_items.append({
                    "id_fak": it["id_fak"], "doklad": it["doklad"], "dodavatel": it["dodavatel"],
                    "vs": it["vs"], "splatnost": it["splatnost"], "castka": it["castka"],
                    "ucet": it["ucet"], "verdikt": it["verdikt"], "warns": it["warns"],
                    "plati": it["plati"], "delka": len(line) if line else 0,
                    "nahled": (line[:110] + "…") if (line and len(line) > 110) else (line or ""),
                })
            plati_items = [x for x in out_items if x["plati"] and x["verdikt"] != "chybi"]
            abs_dir, fn = _target(frm, mena, meta["dnes"], _dt.datetime.now())
            skupiny.append({
                "firma": frm, "firma_kod": _FIRMA_KOD.get(frm, "?"), "mena": mena,
                "pocet": len(out_items), "pocet_plati": len(plati_items),
                "suma": round(sum(x["castka"] for x in out_items), 2),
                "suma_plati": round(sum(x["castka"] for x in plati_items), 2),
                "cesta": abs_dir + "\\", "soubor": fn, "polozky": out_items,
            })
        return {"ok": True, "skupiny": skupiny, "pocet": pocet,
                "dnes": meta["dnes"].strftime("%d.%m.%Y"),
                "pristi_platebni_den": meta["nextpd"].strftime("%d.%m.%Y"),
                "ec_error": meta["ec_err"]}
    finally:
        s.close()


@api_router.post("/app/platby/platak/commit")
async def platak_commit(req: Request):
    """Vygeneruj platák pro firmu+měnu: render → zápis .p11/.f84 na disk +
    úhradový zámek (platak_uhrada_lock s platak_id) + hlavička bank_platak.
    Zapisuje jen položky 'platí teď' s účtem. Marti 8.7.2026."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        b = await req.json()
        firma = str((b or {}).get("firma") or "").strip()
        mena = str((b or {}).get("mena") or "").strip().upper()
        cutoff = _parse_cutoff((b or {}).get("splatnost_do"))
        if firma not in ("1", "2") or mena not in ("CZK", "EUR"):
            return JSONResponse({"ok": False, "error": "Zadej firmu (1/2) a měnu (CZK/EUR)."}, status_code=400)
        frm = int(firma)

        buckets, meta = _build_groups(s, firma, mena, cutoff)
        if meta["ec_err"]:
            return JSONResponse({"ok": False, "error": "Účty z DB_EC se nenačetly: " + meta["ec_err"]}, status_code=502)
        items = buckets.get((frm, mena), [])
        gen = [it for it in items if it["plati"] and it["verdikt"] != "chybi"]
        skip_odloz = [it for it in items if not it["plati"]]
        skip_chybi = [it for it in items if it["plati"] and it["verdikt"] == "chybi"]
        # Zkouška: only_id = vygeneruj platák jen s jednou vybranou fakturou (Peťa 9.7.2026)
        only_id = (b or {}).get("only_id")
        if only_id not in (None, "", 0, "0"):
            try:
                oid = int(only_id)
            except Exception:
                return JSONResponse({"ok": False, "error": "only_id musí být číslo faktury."}, status_code=400)
            gen = [it for it in gen if it["id_fak"] == oid]
            if not gen:
                return JSONResponse({"ok": False, "error": "Zvolená faktura není v návrhu 'platí teď' s účtem (nejde vyzkoušet)."}, status_code=400)
        if not gen:
            return JSONResponse({"ok": False, "error": "Není co vygenerovat (žádná faktura 'platí teď' s účtem)."}, status_code=400)

        # render souboru (kontinuální pořadí)
        lines = []
        for i, it in enumerate(gen, start=1):
            ln = _render_item(it, i, meta)
            if ln is None:
                return JSONResponse({"ok": False, "error": "Render selhal u dokladu %s." % it["doklad"]}, status_code=500)
            lines.append(ln)
        content = b"".join(ln.encode("cp1250") + b"\r\n" for ln in lines)
        b64c = _b64.b64encode(content).decode("ascii")
        suma = round(sum(it.get("castka_platba", it["castka"]) for it in gen), 2)

        now = _dt.datetime.now()
        abs_dir, fn = _target(frm, mena, meta["dnes"], now)
        typ = "tuz" if mena == "CZK" else "zahr"

        # 1) hlavička (flush pro id), 2) zápis souboru, 3) zámky + doplň soubor, commit.
        try:
            pid = s.execute(_t(
                "INSERT INTO tenant.bank_platak (firma, typ, mena, nas_ucet, datum_vytvoreni, "
                "  datum_splatnosti, pocet_polozek, suma, stav, vytvoril_user_id) "
                "VALUES (:firma, :typ, :mena, :nas, CURRENT_DATE, CURRENT_DATE, :pocet, :suma, "
                "  'vygenerovano', :uid) RETURNING id"),
                {"firma": frm, "typ": typ, "mena": mena, "nas": _NAS_UCET.get(frm, ""),
                 "pocet": len(gen), "suma": suma, "uid": int(uid)}).scalar()
            s.flush()
            _mcp_file_write(abs_dir, fn, b64c)   # zápis na disk (když spadne → rollback)
            for it in gen:
                s.execute(_t(
                    "INSERT INTO tenant.platak_uhrada_lock (firma, id_fak, castka, mena, doklad_vs, "
                    "  dodavatel, splatnost, platak_id) "
                    "VALUES (:firma, :idf, :castka, :mena, :vs, :dod, :splat, :pid)"),
                    {"firma": frm, "idf": it["id_fak"], "castka": it["castka"], "mena": mena,
                     "vs": (it["vs"] or it["doklad"])[:60], "dod": (it["dodavatel"] or "")[:120],
                     "splat": it["splat_d"], "pid": pid})
            s.execute(_t("UPDATE tenant.bank_platak SET soubor_nazev=:fn, soubor_cesta=:cesta WHERE id=:pid"),
                      {"fn": fn, "cesta": abs_dir + "\\", "pid": pid})
            s.commit()
        except Exception as exc:
            s.rollback()
            return JSONResponse({"ok": False, "error": "Generování selhalo: " + str(exc)[:200]}, status_code=500)

        return {"ok": True, "platak_id": int(pid), "firma_kod": _FIRMA_KOD.get(frm, "?"),
                "mena": mena, "soubor": fn, "cesta": abs_dir + "\\", "pocet": len(gen), "suma": suma,
                "zamek_uvolnitelny": len(gen), "odlozeno": len(skip_odloz), "bez_uctu": len(skip_chybi)}
    finally:
        s.close()


@api_router.post("/app/platby/platak/smazat")
async def platak_smazat(req: Request):
    """Smaž vygenerovaný platák: uvolní úhradový zámek (faktury zpět do návrhu →
    saldo obnoveno) + smaže soubor z disku + hlavička stav='smazano'. Marti 8.7.2026."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        b = await req.json()
        try:
            pid = int((b or {}).get("platak_id"))
        except Exception:
            return JSONResponse({"ok": False, "error": "Zadej platak_id."}, status_code=400)

        row = s.execute(_t("SELECT soubor_nazev, soubor_cesta, stav FROM tenant.bank_platak WHERE id=:pid"),
                        {"pid": pid}).fetchone()
        if not row:
            return JSONResponse({"ok": False, "error": "Platák nenalezen."}, status_code=404)
        fn, cesta, stav = row[0], row[1], row[2]

        # 1) uvolni zámek (nejdůležitější — saldo zpět) + hlavička smazano.
        uvolneno = s.execute(_t("DELETE FROM tenant.platak_uhrada_lock WHERE platak_id=:pid"),
                             {"pid": pid}).rowcount
        s.execute(_t("UPDATE tenant.bank_platak SET stav='smazano' WHERE id=:pid"), {"pid": pid})
        s.commit()

        # 2) smaž soubor z disku (best-effort — zámek už uvolněn).
        file_ok, file_msg = None, None
        if fn and cesta:
            try:
                file_ok = _mcp_file_delete(cesta.rstrip("\\"), fn)
                if not file_ok:
                    file_msg = "Soubor se nepodařilo smazat (možná už není)."
            except Exception as exc:
                file_ok = False
                file_msg = "Mazání souboru: " + str(exc)[:120]

        return {"ok": True, "platak_id": pid, "uvolneno_zamku": int(uvolneno),
                "soubor_smazan": file_ok, "soubor_pozn": file_msg,
                "info": "Zámek uvolněn, faktury jsou zpět v návrhu (saldo obnoveno)."}
    finally:
        s.close()


@api_router.get("/app/platby/platak/vygenerovane")
def platak_vygenerovane(req: Request):
    """Seznam vygenerovaných platáků (naše, stav='vygenerovano') — pro zobrazení
    a možnost smazat. Marti 8.7.2026."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        rows = s.execute(_t(
            "SELECT id, firma, typ, mena, COALESCE(soubor_nazev,''), COALESCE(pocet_polozek,0), "
            "  COALESCE(suma,0), to_char(datum_vytvoreni,'DD.MM.YYYY'), "
            "  to_char(created_at AT TIME ZONE 'Europe/Prague','DD.MM.YYYY HH24:MI') "
            "FROM tenant.bank_platak WHERE stav='vygenerovano' "
            "ORDER BY created_at DESC NULLS LAST, id DESC LIMIT 100")).fetchall()
        out = []
        for r in rows:
            out.append({"id": int(r[0]), "firma": int(r[1]) if r[1] is not None else 0,
                        "firma_kod": _FIRMA_KOD.get(int(r[1]) if r[1] is not None else 0, "?"),
                        "typ": r[2], "mena": r[3], "soubor": r[4], "pocet": int(r[5]),
                        "suma": float(r[6]) if r[6] is not None else 0.0,
                        "datum": r[7] or "", "vytvoreno": r[8] or ""})
        return {"ok": True, "plataky": out, "pocet": len(out)}
    finally:
        s.close()


@api_router.get("/app/platby/platak/detail")
def platak_detail(req: Request):
    """Detail platáku: hlavička + položky (ze zámku) + obsah souboru (.p11/.f84
    přečtený z disku, cp1250). Pro zobrazení, co v platáku je. Marti 8.7.2026."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        try:
            pid = int(req.query_params.get("id"))
        except Exception:
            return JSONResponse({"ok": False, "error": "Zadej id."}, status_code=400)
        row = s.execute(_t(
            "SELECT id, firma, typ, mena, COALESCE(soubor_nazev,''), COALESCE(soubor_cesta,''), "
            "  COALESCE(pocet_polozek,0), COALESCE(suma,0), to_char(datum_vytvoreni,'DD.MM.YYYY'), "
            "  to_char(created_at AT TIME ZONE 'Europe/Prague','DD.MM.YYYY HH24:MI'), stav, "
            "  COALESCE(nas_ucet,'') FROM tenant.bank_platak WHERE id=:pid"), {"pid": pid}).fetchone()
        if not row:
            return JSONResponse({"ok": False, "error": "Platák nenalezen."}, status_code=404)
        frm = int(row[1]) if row[1] is not None else 0
        header = {"id": int(row[0]), "firma": frm, "firma_kod": _FIRMA_KOD.get(frm, "?"),
                  "typ": row[2], "mena": row[3], "soubor": row[4], "cesta": row[5],
                  "pocet": int(row[6]), "suma": float(row[7]) if row[7] is not None else 0.0,
                  "datum": row[8] or "", "vytvoreno": row[9] or "", "stav": row[10] or "",
                  "nas_ucet": row[11] or ""}
        pol = s.execute(_t(
            "SELECT id_fak, COALESCE(dodavatel,''), COALESCE(doklad_vs,''), castka, mena, "
            "  to_char(splatnost,'DD.MM.YYYY') FROM tenant.platak_uhrada_lock "
            "WHERE platak_id=:pid ORDER BY id"), {"pid": pid}).fetchall()
        polozky = [{"id_fak": int(p[0]), "dodavatel": p[1] or "", "vs": p[2] or "",
                    "castka": float(p[3]) if p[3] is not None else 0.0, "mena": p[4] or "",
                    "splatnost": p[5] or ""} for p in pol]
        obsah, obsah_err = [], None
        if header["soubor"] and header["cesta"]:
            try:
                b = _mcp_file_read(header["cesta"].rstrip("\\"), header["soubor"])
                txt = b.decode("cp1250", "replace").replace("\r\n", "\n")
                obsah = [ln for ln in txt.split("\n") if ln.strip()]
            except Exception as exc:
                obsah_err = str(exc)[:160]
        return {"ok": True, "header": header, "polozky": polozky,
                "obsah": obsah, "obsah_err": obsah_err}
    finally:
        s.close()


@api_router.get("/app/platby/platak/soubory")
def platak_soubory(req: Request):
    """Výpis fyzických souborů ve složkách platáků na disku (z distinct cest
    našich platáků). Marti 8.7.2026 — „vidět tu složku s těmi soubory"."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        cesty = s.execute(_t(
            "SELECT DISTINCT soubor_cesta FROM tenant.bank_platak "
            "WHERE soubor_cesta IS NOT NULL AND soubor_cesta<>'' "
            "ORDER BY soubor_cesta DESC LIMIT 20")).fetchall()
        slozky = []
        for (cesta,) in cesty:
            try:
                files = [f for f in _mcp_file_list(cesta.rstrip("\\")) if f["typ"] != "dir"]
                slozky.append({"cesta": cesta, "soubory": files, "err": None})
            except Exception as exc:
                slozky.append({"cesta": cesta, "soubory": [], "err": str(exc)[:160]})
        return {"ok": True, "slozky": slozky, "pocet": len(slozky)}
    finally:
        s.close()


# ============ IMPORT MZDOVÝCH PLATÁKŮ z Helios (UCTO) → Platební centrum ============
# Marti 10.7.2026: mzdové platáky vygeneruje Helios (TabPlatTuz + TabPlatTuzR v cloud
# UCTO_EC/UCTO_ES). Tenhle endpoint je přečte, vyrenderuje .p11 STEJNÝM renderem jako
# dodavatelské (render_tuz_line, byte-exact) a uloží do tenant.bank_platak + soubor na
# disk → objeví se v „Platáky k platbě", odeslatelné do RB. Každý platák (Mzdy na účet /
# Odvody / Kooperativa …) = jeden .p11 soubor. ?dry=1 → jen náhled, NIC nezapisuje.
@api_router.post("/app/platby/platak/mzdy-import")
async def platak_mzdy_import(req: Request):
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    from modules.erp.api.router import _mssql188_query
    from collections import OrderedDict as _OD
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        try:
            b = await req.json()
        except Exception:
            b = {}
        b = b or {}
        firma = str(b.get("firma") or req.query_params.get("firma") or "").strip().upper()
        dry = str(b.get("dry") or req.query_params.get("dry") or "").strip().lower() in ("1", "true", "ano")
        _now = _dt.date.today()
        try:
            rok = int(b.get("rok") or req.query_params.get("rok") or _now.year)
            mesic = int(b.get("mesic") or req.query_params.get("mesic") or _now.month)
        except Exception:
            rok, mesic = _now.year, _now.month
        if firma in ("1", "EC"):
            frm, cloud_db = 1, "UCTO_EC"
        elif firma in ("2", "ES"):
            frm, cloud_db = 2, "UCTO_ES"
        else:
            return JSONResponse({"ok": False, "error": "Zadej firmu EC nebo ES."}, status_code=400)
        _ro = _mssql188_query("SELECT IdObdobi FROM " + cloud_db + ".dbo.TabMzdObd WHERE Rok=" +
                              str(rok) + " AND Mesic=" + str(mesic))
        if not (_ro.get("ok") and _ro.get("rows")):
            return JSONResponse({"ok": False, "error": "období v cloud Heliosu není (TabMzdObd)"}, status_code=400)
        idobd = int(_ro["rows"][0][0])
        q = ("SELECT p.ID, dv.Nazev, p.Mena, r.Castka, "
             "ISNULL(r.VariabilniSymbol,''), ISNULL(r.KonstantniSymbol,''), ISNULL(r.SpecifickySymbol,''), "
             "ISNULL(bs.CisloUctu,''), ISNULL(pu.KodUstavu,''), ISNULL(r.UcelPlatby,'') "
             "FROM " + cloud_db + ".dbo.TabPlatTuz p "
             "JOIN " + cloud_db + ".dbo.TabDefPlatPrik dv ON p.MzdPredpis=dv.Kod AND p.IdMzdObd=dv.IdObdobi "
             "JOIN " + cloud_db + ".dbo.TabPlatTuzR r ON r.IDHlavaPP=p.ID "
             "LEFT JOIN " + cloud_db + ".dbo.TabBankSpojeni bs ON r.IDBankSpojeni=bs.ID "
             "LEFT JOIN " + cloud_db + ".dbo.TabPenezniUstavy pu ON r.IDBankUstavu=pu.ID "
             "WHERE p.IdMzdObd=" + str(idobd) + " ORDER BY p.ID, r.ID")
        rr = _mssql188_query(q)
        if not rr.get("ok"):
            return JSONResponse({"ok": False, "error": "čtení Helios platáků: " + str(rr.get("error"))[:200]}, status_code=502)
        rows = rr.get("rows") or []
        if not rows:
            return {"ok": True, "plataky": [], "info": "V Heliosu nejsou platáky pro toto období."}
        groups = _OD()
        for row in rows:
            plid = int(row[0])
            if plid not in groups:
                groups[plid] = {"nazev": _clean(row[1]), "mena": (_clean(row[2]) or "CZK").upper(), "lines": []}
            groups[plid]["lines"].append(row)
        nas = _NAS_UCET.get(frm, "")
        dnes = _dt.date.today()
        dv6 = dnes.strftime("%y%m%d")
        now = _dt.datetime.now()
        out = []
        for plid, g in groups.items():
            if g["mena"] != "CZK":
                out.append({"platak": g["nazev"], "preskoceno": "zatím jen CZK tuzemské", "mena": g["mena"]})
                continue
            lines = []
            suma = 0.0
            for i, row in enumerate(g["lines"], start=1):
                castka = float(row[3] or 0)
                suma += castka
                lines.append(render_tuz_line(
                    porad=i, datum_vytv=dv6, castka=castka, ks=_clean(row[5]), vs=_clean(row[4]),
                    ss=_clean(row[6]), kod_ustavu_prij=_clean(row[8]), ucet_prij=_clean(row[7]),
                    ucet_klient=nas, datum_splat=dv6, ucel=(_clean(row[9]) or g["nazev"])))
            content = b"".join(ln.encode("cp1250") + b"\r\n" for ln in lines)
            b64c = _b64.b64encode(content).decode("ascii")
            abs_dir, fn = _target(frm, "CZK", dnes, now)
            fn = fn[:-4] + "_" + str(plid) + fn[-4:]   # unikátní soubor per platák
            info = {"platak": g["nazev"], "mena": "CZK", "pocet": len(lines),
                    "suma": round(suma, 2), "soubor": fn, "cesta": abs_dir + "\\",
                    "nahled": [(l[:120] + "…") if len(l) > 120 else l for l in lines[:2]]}
            if dry:
                info["polozky"] = [{"ucet": _clean(rw[7]), "kod": _clean(rw[8]),
                                    "castka": round(float(rw[3] or 0), 2),
                                    "vs": _clean(rw[4]), "ucel": (_clean(rw[9]) or g["nazev"])}
                                   for rw in g["lines"]]
            if not dry:
                try:
                    pid = s.execute(_t(
                        "INSERT INTO tenant.bank_platak (firma, typ, mena, nas_ucet, datum_vytvoreni, "
                        "datum_splatnosti, pocet_polozek, suma, stav, soubor_nazev, soubor_cesta, poznamka, vytvoril_user_id) "
                        "VALUES (:firma,'tuz','CZK',:nas,CURRENT_DATE,CURRENT_DATE,:pocet,:suma,'vygenerovano',:fn,:cesta,:pozn,:uid) RETURNING id"),
                        {"firma": frm, "nas": nas, "pocet": len(lines), "suma": round(suma, 2),
                         "fn": fn, "cesta": abs_dir + "\\", "pozn": "MZDY: " + g["nazev"], "uid": int(uid)}).scalar()
                    s.flush()
                    _mcp_file_write(abs_dir, fn, b64c)
                    s.commit()
                    info["platak_id"] = int(pid)
                except Exception as exc:
                    s.rollback()
                    info["chyba"] = str(exc)[:200]
            out.append(info)
        return {"ok": True, "firma": _FIRMA_KOD.get(frm, "?"), "idobdobi": idobd, "dry": dry,
                "pocet_plataku": len([x for x in out if x.get("pocet")]),
                "suma_celkem": round(sum(x.get("suma", 0) for x in out), 2), "plataky": out}
    finally:
        s.close()
