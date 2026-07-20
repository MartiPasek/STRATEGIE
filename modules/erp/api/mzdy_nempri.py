# -*- coding: utf-8 -*-
"""
NEMPRI25 — Příloha k žádosti o dávku nemocenského pojištění (e-Podání ČSSZ).
Claude ID26, 20.7.2026. Zatím dávka OSE (ošetřovné); ostatní (NEM/PPM/OPP/DLO) navazně.

Datová věta NEMPRI25, namespace http://schemas.cssz.cz/nem/NEMPRI25, kořen <NEMPRI>.
Struktura + logická pravidla OSE ODLAZENY proti produkčnímu validátoru ČSSZ (ePodaniValidace):
  - potvrzeniZamestnavatele/pocetOdpracovanychHodin JEN když pracoval=true
  - zadostODavku/doDne, pecovalOsobne, pecovalVeDnech JEN pro trvani/ukonceni
  - narokNaPPMjinouOsobou POVINNÉ pro vznik
  - podkladyProVyplatDavky JEN pro trvani/ukonceni; planovaneSmeny POVINNÉ pro ukonceni
  - kodOSSZ = kód okresu z číselníku (Plzeň-město = 444; = prefix VS)
Podání: XML dle NEMPRI25.xsd + el. podpis → DS e-Podání ČSSZ 5ffu6xk (nebo OSSZ Plzeň-město).
"""
from __future__ import annotations

NS = 'xmlns="http://schemas.cssz.cz/nem/NEMPRI25"'


def _b(v: bool) -> str:
    return "true" if v else "false"


def _el(tag: str, val) -> str:
    return "<%s>%s</%s>" % (tag, val, tag)


def _osoba(o: dict) -> str:
    x = _el("jmeno", o["jmeno"]) + _el("prijmeni", o["prijmeni"])
    if o.get("rodneCislo"):
        x += _el("rodneCislo", o["rodneCislo"])
    if o.get("datumNarozeni"):
        x += _el("datumNarozeni", o["datumNarozeni"])
    return x


def _ose_blok(p: dict) -> str:
    """Datový scénář OSE (ošetřovné) dle akce vznik/trvani/ukonceni."""
    vznik = bool(p.get("vznik"))
    trvani = bool(p.get("trvani"))
    ukonceni = bool(p.get("ukonceni"))
    konec = trvani or ukonceni  # pole "do konce" se plní jen pro trvání/ukončení

    # potvrzeni zamestnavatele
    pz = _el("pracoval", _b(p.get("pracoval", False)))
    if p.get("pracoval"):
        pz += _el("pocetOdpracovanychHodin", p.get("pocetOdpracovanychHodin", 0))
    pz += _el("jeStudentem", _b(p.get("jeStudentem", False)))
    pz += _el("prevedenaNaJinouPraci", _b(p.get("prevedenaNaJinouPraci", False)))
    pz += _el("volnoBezNahrady", _b(p.get("volnoBezNahrady", False)))

    # zadost o davku
    z = _el("odeDne", p["odeDne"])
    if konec and p.get("doDne"):
        z += _el("doDne", p["doDne"])
    z += "<osetrovanaOsoba>%s</osetrovanaOsoba>" % _osoba(p["osetrovanaOsoba"])
    # důvod (choice) — onemocnela / narizenaKarantena / nemuzePecovatODite / uzavrenaSkola
    duvod = p.get("duvod", "onemocnela")
    if duvod == "uzavrenaSkola":
        z += "<uzavrenaSkola>%s%s</uzavrenaSkola>" % (
            _el("nazevZarizeniSkoly", p.get("nazevSkoly", "")),
            _el("ICZarizeniSkoly", p["icSkoly"]) if p.get("icSkoly") else "")
    else:
        z += _el(duvod, "true")
    if p.get("spolecnaDomacnost") is not None:
        z += _el("spolecnaDomacnost", _b(p["spolecnaDomacnost"]))
    if p.get("jeOsamely") is not None:
        z += _el("jeOsamely", _b(p["jeOsamely"]))
    if p.get("vPeciDiteDo16Let") is not None:
        z += _el("vPeciDiteDo16Let", _b(p["vPeciDiteDo16Let"]))
    if vznik:  # povinné pro vznik
        z += _el("narokNaPPMjinouOsobou", _b(p.get("narokNaPPMjinouOsobou", False)))
    if konec and p.get("pecovalOsobne") is not None:
        z += _el("pecovalOsobne", _b(p["pecovalOsobne"]))
    if konec and p.get("pecovalVeDnech"):
        dny = "".join("<obdobi><od>%s</od><do>%s</do></obdobi>" % (a, b) for (a, b) in p["pecovalVeDnech"])
        z += "<pecovalVeDnech>%s</pecovalVeDnech>" % dny
    if p.get("kodRodVztah"):
        z += _el("kodRodVztah", p["kodRodVztah"])

    out = (_el("oseVznik", _b(vznik)) + _el("oseTrvani", _b(trvani)) + _el("oseUkonceni", _b(ukonceni))
           + "<potvrzeniZamestnavatele>%s</potvrzeniZamestnavatele>" % pz
           + "<zadostODavku>%s</zadostODavku>" % z)
    # podklady pro výplatu — jen pro trvání/ukončení
    if konec:
        pod = _el("pracovalPoslDenPD", _b(p.get("pracovalPoslDenPD", False)))
        if ukonceni:  # planovaneSmeny povinné pro ukončení
            pod += _el("planovaneSmeny", _b(p.get("planovaneSmeny", False)))
        out += "<podkladyProVyplatDavky>%s</podkladyProVyplatDavky>" % pod
    return "<ose>%s</ose>" % out


def build_nempri(p: dict) -> str:
    """Sestaví NEMPRI25 datovou větu. p = dict (viz DEMO_MARESOVA). Zatím druhDavky=OSE."""
    d = p["dokument"]
    dok = (_el("kodOSSZ", d["kodOSSZ"]) + _el("druhDavky", d.get("druhDavky", "OSE")))
    if d.get("opravnePodani") is not None:
        dok += _el("opravnePodani", _b(d["opravnePodani"]))
    if d.get("cisloRozhodnuti"):
        dok += _el("cisloRozhodnuti", d["cisloRozhodnuti"])
    dok += _el("zahranicni", _b(d.get("zahranicni", False)))

    pj = p["pojistenec"]
    poj = _el("jmeno", pj["jmeno"]) + _el("prijmeni", pj["prijmeni"]) + _el("rodneCislo", pj["rodneCislo"])

    z = p["zamestnani"]
    zam = (_el("VSZamestnavatel", z["vs"]) + _el("ICZamestnavatel", z["ic"])
           + _el("nazevZamestnavatel", z["nazev"]) + _el("zamestnanOd", z["zamestnanOd"]))
    if z.get("zamestnanDo"):
        zam += _el("zamestnanDo", z["zamestnanDo"])
    zam += _el("druhCinnosti", z.get("druhCinnosti", "1"))

    ro = p.get("rozhodneObdobi")
    rozh_block = ""
    if ro and ro.get("mesice"):
        obd = "".join("<obdobi><kalendarniMesic>%d</kalendarniMesic><kalendarniRok>%d</kalendarniRok>"
                      "<zapocitatelnyPrijem>%d</zapocitatelnyPrijem><vylouceneDny>%d</vylouceneDny></obdobi>"
                      % (m, r, pr, vy) for (m, r, pr, vy) in ro["mesice"])
        rozh_block = ("<rozhodneObdobi>" + _el("rozhodneObdobiOd", ro["od"]) + _el("rozhodneObdobiDo", ro["do"])
                      + "<seznamObdobi>%s</seznamObdobi>" % obd
                      + _el("zapocitatelnyPrijemCelkem", ro["prijemCelkem"])
                      + _el("vylouceneDnyCelkem", ro["vylCelkem"]) + "</rozhodneObdobi>")

    davka = "<davka>%s</davka>" % _ose_blok(p["ose"])

    k = p.get("kontakt")
    kont = ""
    if k:
        kk = ""
        if k.get("telefon"):
            kk += _el("telefon", k["telefon"])
        if k.get("email"):
            kk += _el("email", k["email"])
        if k.get("pracovnik"):
            kk += _el("kontaktniPracovnik", k["pracovnik"])
        kont = "<kontaktPracovnik>%s</kontaktPracovnik>" % kk

    u = p.get("ucet")
    plat = ""
    if u:
        uc = ""
        if u.get("predcisli"):
            uc += _el("predcisli", u["predcisli"])
        uc += _el("ucetCislo", u["cislo"]) + _el("bankaKod", u["banka"])
        plat = ("<platebniSpojeni><vyplatitUcetCR>true</vyplatitUcetCR>"
                "<ucetCZ>%s</ucetCZ></platebniSpojeni>" % uc)

    dv = ("<datovaVeta poradoveCislo=\"1\">"
          "<dokument>%s</dokument><pojistenec>%s</pojistenec><zamestnani>%s</zamestnani>"
          "%s%s%s%s</datovaVeta>" % (dok, poj, zam, rozh_block, davka, kont, plat))

    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<NEMPRI %s version="1.0" partialAccept="A">'
            '<VENDOR productName="STRATEGIE" productVersion="0.1"/>'
            '<SENDER EmailNotifikace="%s" ISDSreport=""/>'
            '%s</NEMPRI>' % (NS, p.get("email_notifikace", ""), dv))


# Demo case = Marešová OSE 06/2026 (ověřeno proti ČSSZ validátoru 20.7.2026 → OK).
DEMO_MARESOVA = {
    "email_notifikace": "p.safrankova@eurosoft.com",
    "dokument": {"kodOSSZ": 444, "druhDavky": "OSE", "cisloRozhodnuti": "11098621260623001N", "zahranicni": False},
    "pojistenec": {"jmeno": "Kristýna", "prijmeni": "Marešová", "rodneCislo": "9560242131"},
    "zamestnani": {"vs": "4442058998", "ic": "26411741", "nazev": "EUROSOFT - System s.r.o.",
                   "zamestnanOd": "2021-01-01", "druhCinnosti": "1"},
    "rozhodneObdobi": {"od": "2025-06-01", "do": "2026-05-31", "prijemCelkem": 409613, "vylCelkem": 111,
                       "mesice": [(6, 2025, 0, 30), (7, 2025, 0, 31), (8, 2025, 0, 31), (9, 2025, 35637, 0),
                                  (10, 2025, 51254, 0), (11, 2025, 50358, 0), (12, 2025, 50583, 0),
                                  (1, 2026, 51531, 0), (2, 2026, 38817, 6), (3, 2026, 28120, 13),
                                  (4, 2026, 51666, 0), (5, 2026, 51647, 0)]},
    "ose": {"vznik": True, "trvani": False, "ukonceni": True,
            "pracoval": False, "jeStudentem": False, "prevedenaNaJinouPraci": False, "volnoBezNahrady": False,
            "odeDne": "2026-06-23", "doDne": "2026-06-28",
            "osetrovanaOsoba": {"jmeno": "Nina", "prijmeni": "Marešová", "rodneCislo": "2259100569", "datumNarozeni": "2022-09-10"},
            "duvod": "onemocnela", "spolecnaDomacnost": True, "jeOsamely": False, "vPeciDiteDo16Let": True,
            "narokNaPPMjinouOsobou": False, "pecovalOsobne": True, "pecovalVeDnech": [("2026-06-23", "2026-06-28")],
            "kodRodVztah": "PL", "pracovalPoslDenPD": False, "planovaneSmeny": False},
    "kontakt": {"telefon": "+420773738582", "email": "p.safrankova@eurosoft.com", "pracovnik": "Šafránková Petra"},
    "ucet": {"cislo": "247287648", "banka": "0300"},
}


# ── Auto-source z Heliosu (TabMzPrilohaDnp + TabMzPrilohaDNPRO) ────────────────
# Claude ID26, 20.7.2026. Kristý si přílohu vybere → build_nempri → XML.

FIRMA_INFO = {
    "EC": {"vs": "4445158191", "ic": "26411746", "nazev": "EUROSOFT - Control s.r.o."},
    "ES": {"vs": "4442058998", "ic": "26411741", "nazev": "EUROSOFT - System s.r.o."},
}


def _b2(v):
    """Helios bit/bool → python bool."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "ano", "y")


def _cloud_db(firma):
    from modules.erp.api import router as _r
    return _r._firma_cloud_db(firma)


def _q(sql):
    from modules.erp.api import router as _r
    return _r._mssql188_query(sql)


def load_nempri_list(firma, rok=None, mesic=None):
    """Seznam příloh DNP (dávek) pro výběr. Filtr dle IdObdobi (rok/měsíc) volitelný."""
    cdb = _cloud_db(firma)
    where = "1=1"
    if rok and mesic:
        where = ("p.IdObdobi=(SELECT IdObdobi FROM %s.dbo.TabMzdObd WHERE Rok=%d AND Mesic=%d)"
                 % (cdb, int(rok), int(mesic)))
    sql = ("SELECT TOP 200 p.ID, RTRIM(p.CisloRozhodnuti), p.DruhDavky, "
           "RTRIM(z.Prijmeni), RTRIM(z.Jmeno), RTRIM(p.Zadost_Prijmeni), RTRIM(p.Zadost_Jmeno), "
           "CONVERT(varchar,p.Zadost_DatumOd,23), CONVERT(varchar,p.Zadost_DatumDo,23), "
           "p.Zadost_OS_Vznik, p.Zadost_OS_Ukonceni "
           "FROM %s.dbo.TabMzPrilohaDnp p LEFT JOIN %s.dbo.TabCisZam z ON z.ID=p.ZamestnanecId "
           "WHERE %s ORDER BY p.DatRealizace DESC" % (cdb, cdb, where))
    r = _q(sql)
    out = []
    if r.get("ok"):
        for v in (r.get("rows") or []):
            out.append({"id": v[0], "cisloRozhodnuti": v[1], "druhDavky_helios": v[2],
                        "zamestnanec": ("%s %s" % ((v[4] or ""), (v[3] or ""))).strip(),
                        "osetrovana": ("%s %s" % ((v[6] or ""), (v[5] or ""))).strip(),
                        "od": v[7], "do": v[8], "vznik": _b2(v[9]), "ukonceni": _b2(v[10])})
    return out


def load_nempri_priloha(firma, priloha_id):
    """Načte přílohu DNP + rozhodné období z Heliosu → params pro build_nempri (zatím OSE)."""
    cdb = _cloud_db(firma)
    fi = FIRMA_INFO.get((firma or "").upper(), FIRMA_INFO["ES"])
    pid = int(priloha_id)
    cols = ("p.CisloRozhodnuti, CONVERT(varchar,p.Zadost_DatumOd,23), CONVERT(varchar,p.Zadost_DatumDo,23), "
            "RTRIM(p.Zadost_Jmeno), RTRIM(p.Zadost_Prijmeni), RTRIM(p.Zadost_RC), CONVERT(varchar,p.Zadost_DatNarozeni,23), "
            "p.Zadost_OS_Vznik, p.Zadost_OS_Trvani, p.Zadost_OS_Ukonceni, "
            "p.Zadost_OS_NemOsoba, p.Zadost_OS_Karan10L, p.Zadost_OS_SkolaZav, RTRIM(p.Zadost_OS_SkolaNaz), RTRIM(p.Zadost_OS_SkolaIC), "
            "p.Zadost_OS_SpolDom, p.Zadost_OS_Osamely, p.Zadost_OS_Dite_16L, p.Zadost_OS_JinaPPM, p.Zadost_OS_PecePlna, RTRIM(p.Zadost_OS_Vztah), "
            "p.Den_1_Pracoval, p.Den_1_OdpracHod, p.PrevodJinaPrace, CONVERT(varchar,p.VolnoBezNahradyOd,23), p.SpadaDoPrazdnin, "
            "p.Podkl_OS_PDen_Prac, p.Podkl_OS_BylPlanSm, RTRIM(p.KontaktPracovnik), RTRIM(p.Zamestnanec_Telefon), RTRIM(p.Zamestnanec_Email), "
            "RTRIM(p.DruhVydelCinnosti), p.ZamestnanecId, CONVERT(varchar,p.ZamestnaniOd,23), RTRIM(p.DruhDavky)")
    r = _q("SELECT %s FROM %s.dbo.TabMzPrilohaDnp p WHERE p.ID=%d" % (cols, cdb, pid))
    if not (r.get("ok") and r.get("rows")):
        raise ValueError("příloha ID=%d nenalezena (%s)" % (pid, firma))
    v = r["rows"][0]
    def rc(x):  # rodné číslo bez lomítka
        return (x or "").replace("/", "").strip()
    zid = int(v[32] or 0)
    rz = _q("SELECT RTRIM(Jmeno), RTRIM(Prijmeni), RTRIM(RodneCislo) FROM %s.dbo.TabCisZam WHERE ID=%d" % (cdb, zid))
    zj, zp, zrc = ("", "", "")
    if rz.get("ok") and rz.get("rows"):
        zj, zp, zrc = rz["rows"][0][0], rz["rows"][0][1], rc(rz["rows"][0][2])
    # rozhodné období z DNPRO
    rr = _q("SELECT Rok, Mesic, CAST(ZapocPrijem AS int), CAST(VylouceneDny AS int) "
            "FROM %s.dbo.TabMzPrilohaDNPRO WHERE ID_Hlavicka=%d ORDER BY Rok, Mesic" % (cdb, pid))
    mesice, sump, sumv = [], 0, 0
    if rr.get("ok"):
        for m in (rr.get("rows") or []):
            mesice.append((int(m[1]), int(m[0]), int(m[2] or 0), int(m[3] or 0)))
            sump += int(m[2] or 0); sumv += int(m[3] or 0)
    ro_od = ("%04d-%02d-01" % (mesice[0][1], mesice[0][0])) if mesice else None
    import calendar as _cal
    ro_do = ("%04d-%02d-%02d" % (mesice[-1][1], mesice[-1][0], _cal.monthrange(mesice[-1][1], mesice[-1][0])[1])) if mesice else None

    ma_do = bool(v[2])
    ukonceni = _b2(v[9]) or ma_do  # dokončená epizoda (má "do") → i ukončení
    # důvod (choice)
    if _b2(v[11]):
        duvod = "narizenaKarantena"
    elif _b2(v[12]):
        duvod = "uzavrenaSkola"
    elif _b2(v[10]):
        duvod = "onemocnela"
    else:
        duvod = "onemocnela"
    p = {
        "email_notifikace": (v[30] or fi.get("email") or ""),
        "dokument": {"kodOSSZ": int(str(fi["vs"])[:3]), "druhDavky": "OSE",
                     "cisloRozhodnuti": v[0], "zahranicni": False},
        "pojistenec": {"jmeno": zj, "prijmeni": zp, "rodneCislo": zrc},
        "zamestnani": {"vs": fi["vs"], "ic": fi["ic"], "nazev": fi["nazev"],
                       "zamestnanOd": v[33] or "2000-01-01", "druhCinnosti": (v[31] or "1")},
        "rozhodneObdobi": {"od": ro_od, "do": ro_do, "prijemCelkem": sump, "vylCelkem": sumv, "mesice": mesice},
        "ose": {
            "vznik": _b2(v[7]), "trvani": _b2(v[8]), "ukonceni": ukonceni,
            "pracoval": _b2(v[21]),
            "pocetOdpracovanychHodin": (int(float(v[22])) if (v[22] not in (None, "") and _b2(v[21])) else 0),
            "jeStudentem": False,
            "prevedenaNaJinouPraci": _b2(v[23]),
            "volnoBezNahrady": bool(v[24]),
            "odeDne": v[1], "doDne": v[2],
            "osetrovanaOsoba": {"jmeno": v[3], "prijmeni": v[4], "rodneCislo": rc(v[5]), "datumNarozeni": v[6]},
            "duvod": duvod, "nazevSkoly": v[13], "icSkoly": v[14],
            "spolecnaDomacnost": _b2(v[15]), "jeOsamely": _b2(v[16]), "vPeciDiteDo16Let": _b2(v[17]),
            "narokNaPPMjinouOsobou": _b2(v[18]), "pecovalOsobne": _b2(v[19]),
            "pecovalVeDnech": ([(v[1], v[2])] if (ukonceni and v[2]) else None),
            "kodRodVztah": (v[20] or None),
            "pracovalPoslDenPD": _b2(v[26]), "planovaneSmeny": _b2(v[27]),
        },
        "kontakt": {"pracovnik": v[28], "telefon": (v[29] or None), "email": (v[30] or None)},
    }
    return p


def generate_nempri_xml(firma, priloha_id):
    return build_nempri(load_nempri_priloha(firma, priloha_id))
