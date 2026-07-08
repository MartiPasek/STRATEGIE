# -*- coding: utf-8 -*-
"""Generátor platáků (task #44/#45) — návrh k platbě → .p11 (CZK) / .f84 (EUR).

Fáze 1 = PREVIEW (nic nezapisuje): vezme návrh k platbě (stejná selekce jako
/app/platby/navrh), k faktuře dotáhne účet příjemce z DB_EC, ověří ho proti
dodavateli + §109 (JEN VARUJE, neblokuje — Marti 8.7.2026), klasifikuje dle
platebního dne (Út/Čt) a vyrenderuje řádek platáku (byte-exact z
scripts/rb/gemini_render.py) — vrátí náhled + cílovou cestu. Fáze 2 = COMMIT
(samostatný potvrzený krok) zapíše soubory + úhradový zámek (platak_uhrada_lock).

Endpointy registrované na sdíleném api_router (prefix /api/v1/erp):
  GET /app/platby/platak/preview?firma=1|2|all&mena=CZK|EUR|all

Scope: rodiče + Petra (18) + cockpit (stejně jako /platby).
Claude ID23, 8.7.2026.
"""
import json as _j
import datetime as _dt

from starlette.requests import Request
from starlette.responses import JSONResponse

# api_router + auth helpery z hlavního routeru (dekorátor se registruje při importu)
from modules.erp.api.router import (
    api_router,
    _uid_from_token_or_cookie,
    _is_parent,
    _is_cockpit,
)

# ------------------------------------------------------------------ render (1:1)
# Převzato beze změny z scripts/rb/gemini_render.py (byte-exact ověřeno na 12/12
# vzorcích EUROSOFTu). Vloženo přímo, aby modul neměl závislost na scripts/ path.


def _r(fill, val, width):
    """RIGHT(fill+val, width) — číselné pole, doplněné VLEVO (fill=nuly)."""
    return (fill + str(val))[-width:]


def _l(val, width):
    """LEFT(val+mezery, width) — text VPRAVO mezerami, ořez na width."""
    return (str(val) + " " * width)[:width]


def _ucet(cislouctu):
    """'předčíslí-číslo' → (předčíslí 6, číslo 10). Bez '-' → předčíslí 000000."""
    s = str(cislouctu or "")
    if "-" in s:
        pre, cis = s.split("-", 1)
        return _r("0000000000", pre, 6), _r("0000000000", cis, 10)
    return "000000", _r("0000000000", s, 10)


def render_tuz_line(porad, datum_vytv, castka, ks, vs, ss, kod_ustavu_prij,
                    ucet_prij, ucet_klient, datum_splat, ucel):
    """Jeden řádek TUZ (.p11). datum_*='YYMMDD'."""
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
    """Jeden řádek ZAHR (.f84). datum_vytv8='YYYYMMDD', datum_splat='YYMMDD'."""
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
# Plátcovské (naše) CZK účty per firma (EUR jde jako zahraniční z CZK účtu).
# Ověřeno v ostrém běhu 7.7. TODO: číst z tenant.bank_connection_account.
_NAS_UCET = {1: "9251651001", 2: "3047813002"}
_FIRMA_KOD = {1: "EC", 2: "ES"}

# Platební dny = Úterý (weekday 1) + Čtvrtek (weekday 3). Marti 7.7.2026.
_PLATEBNI_DNY = {1, 3}


def _next_platebni_den(dnes):
    """Nejbližší platební den STRICTNĚ po dnešku (Út/Čt)."""
    d = dnes + _dt.timedelta(days=1)
    for _ in range(14):
        if d.weekday() in _PLATEBNI_DNY:
            return d
        d = d + _dt.timedelta(days=1)
    return dnes + _dt.timedelta(days=1)


def _ec_query(sql):
    """DB_EC read přes EUROSOFT MCP (eurosoft_strategie_query_raw). → list[dict]."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupný")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
    r = (_j.loads(raw) if isinstance(raw, str) else raw) or {}
    if not r.get("ok"):
        raise RuntimeError("DB_EC: " + str(r.get("message") or r.get("error"))[:200])
    cols = r.get("columns") or []
    out = []
    for row in (r.get("rows") or []):
        out.append(dict(zip(cols, row)) if isinstance(row, list) else row)
    return out


def _clean(v):
    """None/NUL → čistý string (most občas přitáhne \\x00)."""
    if v is None:
        return ""
    return str(v).replace(chr(0), "").strip()


@api_router.get("/app/platby/platak/preview")
def platak_preview(req: Request):
    """PREVIEW generátoru platáků — NIC nezapisuje. Vezme návrh k platbě, dotáhne
    účty příjemců z DB_EC, ověří (jen varuje), klasifikuje dle platebního dne a
    vyrenderuje řádky. Vrací per firma+měna položky + náhled + cílovou cestu."""
    uid = _uid_from_token_or_cookie(req)
    from core.database_data import get_data_session as _g
    from sqlalchemy import text as _t
    s = _g()
    try:
        if not (uid and (_is_parent(s, uid) or int(uid) == 18 or _is_cockpit(s, uid))):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

        firma = (req.query_params.get("firma") or "all").strip()
        mena_f = (req.query_params.get("mena") or "all").strip().upper()

        # --- 1) NÁVRH k platbě z PG (stejná selekce jako /app/platby/navrh) -----
        params = {}
        ffilter = ""
        _uf = "(CASE WHEN p.rada IN ('501','531','541') THEN 2 ELSE 1 END)"
        if firma in ("1", "2"):
            params["ff"] = int(firma)
            ffilter = " AND " + _uf + " = :ff "
        mfilter = ""
        if mena_f in ("CZK", "EUR"):
            params["mm"] = mena_f
            mfilter = " AND p.mena = :mm "
        rows = s.execute(_t(
            "WITH u AS (SELECT id_fak, SUM(castka) AS paid FROM ("
            "  SELECT id_fak, castka FROM tenant.oz_uhrady WHERE firma=1"
            "  UNION ALL SELECT id_fak, castka FROM tenant.platak_uhrada_lock) x GROUP BY id_fak) "
            "SELECT p.id, p.mena, p.doklad, COALESCE(NULLIF(p.dodavatel,''),p.zkratka,'?') dod, "
            "  COALESCE(p.var_symbol,'') vs, to_char(p.splatnost::date,'DD.MM.YYYY') splat, "
            "  p.splatnost::date splat_d, "
            "  ((CASE WHEN p.mena='CZK' THEN p.suma_kc ELSE p.suma_val END) - COALESCE(u.paid,0)) open_saldo, "
            "  COALESCE(p.popis,'') popis, " + _uf + " AS ufirma "
            "FROM tenant.oz_pf_platba p LEFT JOIN u ON u.id_fak=p.id "
            "WHERE p.realizovano=1 AND NOT p.fin_zakaz AND p.nehradit=0 AND p.suma_po_zao>0 "
            "  AND p.obdobi>22 AND p.rada NOT LIKE '52%' "
            "  AND now()::date >= (p.splatnost::date - (p.dny_pred_platbou||' days')::interval) "
            "  AND ((CASE WHEN p.mena='CZK' THEN p.suma_kc ELSE p.suma_val END) - COALESCE(u.paid,0)) > 0.5 "
            + ffilter + mfilter +
            "ORDER BY p.mena, p.splatnost"), params).fetchall()

        navrh = []
        for r in rows:
            navrh.append({
                "id_fak": int(r[0]), "mena": r[1], "doklad": r[2] or "",
                "dodavatel": r[3] or "", "vs": r[4] or "", "splatnost": r[5],
                "splat_d": r[6], "castka": round(float(r[7]), 2) if r[7] is not None else 0.0,
                "popis": (r[8] or "")[:70], "firma": int(r[9]) if r[9] is not None else 1,
            })
        if not navrh:
            return {"ok": True, "skupiny": [], "pocet": 0,
                    "info": "V návrhu není nic k platbě pro tento filtr."}

        # --- 2) ÚČTY PŘÍJEMCŮ z DB_EC (bulk podle id faktury) ------------------
        ids = sorted({it["id_fak"] for it in navrh})
        inlist = ",".join(str(i) for i in ids)
        ucty = {}
        ec_err = None
        try:
            ec_rows = _ec_query(
                "SELECT d.ID id_fak, d.DodFak, d.CisloOrg dok_org, "
                "  bs.CisloUctu, bs.IBANElektronicky, bs.IBANPisemny, bs.IDUstavu, "
                "  bs.IDOrg, bs.CilovaZeme, bs.UcetVSeznamuSpravDane sd, "
                "  bu.KodUstavu, bu.SWIFTUstavu, bu.NazevUstavu, "
                "  org.CisloOrg ucet_org, org.Firma org_firma, org.Ulice org_ulice, "
                "  org.UliceSCisly org_ulice2, org.Misto org_misto, org.PSC org_psc, "
                "  org.IdZeme org_zeme, zbu.Nazev zbu_nazev, zorg.Nazev zorg_nazev "
                "FROM TabDokladyZbozi d "
                "LEFT JOIN TabBankSpojeni bs ON bs.ID = d.IDBankSpoj "
                "LEFT JOIN TabPenezniUstavy bu ON bu.ID = bs.IDUstavu "
                "LEFT JOIN TabCisOrg org ON org.ID = bs.IDOrg "
                "LEFT JOIN TabZeme zbu ON zbu.ISOKod = SUBSTRING(bu.SWIFTUstavu,5,2) "
                "LEFT JOIN TabZeme zorg ON zorg.ISOKod = bs.CilovaZeme "
                "WHERE d.ID IN (" + inlist + ")")
            for er in ec_rows:
                ucty[int(er.get("id_fak"))] = er
        except Exception as exc:
            ec_err = str(exc)[:200]

        # --- 3) sestavení + verdikt + render ----------------------------------
        dnes = _dt.date.today()
        nextpd = _next_platebni_den(dnes)
        datum_vytv6 = dnes.strftime("%y%m%d")
        datum_vytv8 = dnes.strftime("%Y%m%d")

        # skupiny per (firma, měna)
        buckets = {}
        for it in navrh:
            key = (it["firma"], it["mena"])
            buckets.setdefault(key, []).append(it)

        skupiny = []
        for (frm, mena), items in sorted(buckets.items(), key=lambda k: (k[0][0], k[0][1])):
            nas = _NAS_UCET.get(frm, "")
            out_items = []
            porad = 0
            for it in items:
                acc = ucty.get(it["id_fak"], {}) or {}
                warns = []
                # Datum splatnosti na platáku = VŽDY DNEŠNÍ (Peťa 8.7.2026), i když má
                # faktura splatnost později — platba se provede dnes, ne až v den splatnosti.
                sp = it["splat_d"] or dnes
                datum_splat6 = dnes.strftime("%y%m%d")
                plati = bool(sp <= nextpd)  # plať, když nepočká s rezervou na příští PD

                # anti-podvod (JEN VARUJE):
                dok_org = _clean(acc.get("dok_org"))
                ucet_org = _clean(acc.get("ucet_org"))
                sd = acc.get("sd")
                verdikt = "ok"
                if not acc:
                    verdikt = "chybi"; warns.append("Faktura nenalezena v DB_EC")
                elif not _clean(acc.get("CisloUctu")) and not _clean(acc.get("IBANElektronicky")) and not _clean(acc.get("IBANPisemny")):
                    verdikt = "chybi"; warns.append("Chybí účet příjemce na faktuře")
                else:
                    if dok_org and ucet_org and dok_org != ucet_org:
                        verdikt = "podezrely"
                        warns.append("Účet nepatří dodavateli z faktury (org %s ≠ %s)" % (ucet_org, dok_org))
                    if not (sd in (1, "1", True)):
                        if verdikt == "ok":
                            verdikt = "amber"
                        warns.append("Účet není zveřejněný u správce daně (§109)")

                line = None
                delka = 0
                if verdikt != "chybi":
                    if mena == "CZK":
                        line = render_tuz_line(
                            porad=porad + 1, datum_vytv=datum_vytv6, castka=it["castka"],
                            ks="", vs=it["vs"], ss="", kod_ustavu_prij=_clean(acc.get("KodUstavu")),
                            ucet_prij=_clean(acc.get("CisloUctu")), ucet_klient=nas,
                            datum_splat=datum_splat6, ucel=(it["doklad"] + " " + it["dodavatel"]).strip())
                    else:
                        iban = _clean(acc.get("IBANElektronicky")) or _clean(acc.get("IBANPisemny")).replace(" ", "")
                        zeme = _clean(acc.get("org_zeme")) or _clean(acc.get("CilovaZeme"))
                        op_misto = (_clean(acc.get("org_psc")) + " " + _clean(acc.get("org_misto"))).strip()
                        line = render_zahr_line(
                            porad=porad + 1, datum_vytv8=datum_vytv8, castka=it["castka"], mena="EUR",
                            up_nazev=_clean(acc.get("NazevUstavu")), up_ulice="", up_misto="",
                            zup_nazev=_clean(acc.get("zbu_nazev")), op_firma=_clean(acc.get("org_firma")),
                            op_ulice=_clean(acc.get("org_ulice")) or _clean(acc.get("org_ulice2")),
                            op_misto=op_misto, zop_nazev=_clean(acc.get("zorg_nazev")),
                            nas_ucet=nas, iban=iban, poplatky="SHA", tit="", cil_zeme=zeme,
                            hlav_id=it["id_fak"], p1=it["vs"], p2="", p3="", p4="", priorita=0,
                            nas_mena="CZK", swift=_clean(acc.get("SWIFTUstavu")), datum_splat=datum_splat6)
                    delka = len(line) if line else 0
                    porad += 1

                # účet příjemce pro zobrazení
                if mena == "CZK":
                    ucet_disp = _clean(acc.get("CisloUctu"))
                    if _clean(acc.get("KodUstavu")):
                        ucet_disp += "/" + _clean(acc.get("KodUstavu"))
                else:
                    ucet_disp = _clean(acc.get("IBANElektronicky")) or _clean(acc.get("IBANPisemny"))

                out_items.append({
                    "id_fak": it["id_fak"], "doklad": it["doklad"], "dodavatel": it["dodavatel"],
                    "vs": it["vs"], "splatnost": it["splatnost"], "castka": it["castka"],
                    "ucet": ucet_disp, "verdikt": verdikt, "warns": warns,
                    "plati": plati, "delka": delka,
                    "nahled": (line[:120] + "…") if (line and len(line) > 120) else (line or ""),
                })

            plati_items = [x for x in out_items if x["plati"] and x["verdikt"] != "chybi"]
            fname = "PAY_%s_%s.%s" % ("TUZ" if mena == "CZK" else "ZAHR",
                                      dnes.strftime("%d-%m-%Y"), "p11" if mena == "CZK" else "f84")
            cesta = "D:\\data\\RB\\Platební příkazy\\%s\\%s\\" % (_FIRMA_KOD.get(frm, "?"),
                                                                  dnes.strftime("%Y%m%d"))
            skupiny.append({
                "firma": frm, "firma_kod": _FIRMA_KOD.get(frm, "?"), "mena": mena,
                "pocet": len(out_items), "pocet_plati": len(plati_items),
                "suma": round(sum(x["castka"] for x in out_items), 2),
                "suma_plati": round(sum(x["castka"] for x in plati_items), 2),
                "cesta": cesta, "soubor": fname, "polozky": out_items,
            })

        return {"ok": True, "skupiny": skupiny, "pocet": len(navrh),
                "dnes": dnes.strftime("%d.%m.%Y"),
                "pristi_platebni_den": nextpd.strftime("%d.%m.%Y"),
                "ec_error": ec_err,
                "info": ("POZOR: účty z DB_EC se nepodařilo načíst (%s)" % ec_err) if ec_err else None}
    finally:
        s.close()
