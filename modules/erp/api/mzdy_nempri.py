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

    ro = p["rozhodneObdobi"]
    obd = "".join("<obdobi><kalendarniMesic>%d</kalendarniMesic><kalendarniRok>%d</kalendarniRok>"
                  "<zapocitatelnyPrijem>%d</zapocitatelnyPrijem><vylouceneDny>%d</vylouceneDny></obdobi>"
                  % (m, r, pr, vy) for (m, r, pr, vy) in ro["mesice"])
    rozh = (_el("rozhodneObdobiOd", ro["od"]) + _el("rozhodneObdobiDo", ro["do"])
            + "<seznamObdobi>%s</seznamObdobi>" % obd
            + _el("zapocitatelnyPrijemCelkem", ro["prijemCelkem"])
            + _el("vylouceneDnyCelkem", ro["vylCelkem"]))

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
          "<rozhodneObdobi>%s</rozhodneObdobi>%s%s%s</datovaVeta>" % (dok, poj, zam, rozh, davka, kont, plat))

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
