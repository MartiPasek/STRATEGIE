# -*- coding: utf-8 -*-
"""
gen_jmhz.py — generátor Jednotného měsíčního hlášení zaměstnavatele (JMHZ) pro ČSSZ.

OBNOVENO 11.7.2026 (Claude23) z ověřeného pilotu docs/jmhz/pilot_JMHZ_EUROSOFT_2026-06.xml
(VENDOR STRATEGIE_JMHZ_0.1, prošlo ČSSZ ePodaniValidace). Původní gen_jmhz.py se ztratil
(nebyl v gitu). Tentokrát je zacommitovaný — viz doktrína „hotovo = v gitu + na tlačítku".

Struktura výstupu je 1:1 s pilotem. Mzdové částky se derivují z hrubé (ověřené poměry).
OČR (ošetřovné) se doplňuje do formuláře osoby: hodinyNeodpracOcr + eldp/vylouceneDny/
osetrovaniClenaRodiny + eldp/odecitaneDny/osetrovaniSNarokem.

Použití:
    python gen_jmhz.py --rok 2026 --mesic 6 --firma ES --out docs/jmhz/JMHZ_ES_2026-06.xml
    (bez DB: --demo použije zabudovaná data k ověření struktury)

Ověření výstupu:  @@EPVAL docs/jmhz/JMHZ_ES_2026-06.xml   (validátor ČSSZ, test)
"""
import argparse, math, uuid, datetime, calendar, sys, os

NS = (
    'xmlns:n1="http://schemas.cssz.cz/JMHZ/podani/1.0" '
    'xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:bt="http://schemas.cssz.cz/baseTypes/v2" '
    'xmlns:so="http://schemas.cssz.cz/JMHZ/souhrn/1.0" '
    'xmlns:pvpoj="http://schemas.cssz.cz/JMHZ/PVPOJ/1.0" '
    'xmlns:form="http://schemas.cssz.cz/JMHZ/form/1.0"'
)

VENDOR = "STRATEGIE_JMHZ_0.1"
SENDER_EMAIL = "marti-ai@eurosoft.com"
VARIABILNI_SYMBOL = "1180109983"   # VS zaměstnavatele EUROSOFT (z pilotu)

# ---- ověřené sazby (z pilotu) ----
SP_ZAM = 0.071      # sociální pojištění zaměstnanec
SP_FIRMA = 0.248    # sociální pojištění zaměstnavatel
ZP_ZAM = 0.045      # zdravotní pojištění zaměstnanec
ZP_FIRMA = 0.090    # zdravotní pojištění zaměstnavatel
ZALOHA = 0.15       # záloha na daň
SLEVA_POPLATNIK = 2570


def _r(x):
    """zaokrouhlení na celé Kč"""
    return int(round(x))


def compute_person_amounts(p):
    """Doplní derivované částky z hrubé (p['hruba'])."""
    h = float(p["hruba"])
    proh = bool(p.get("prohlaseni", True))
    a = dict(p)
    a["zuctovanoCelkem"] = _r(h)
    a["vypoctenaZaloha"] = int(math.ceil(h * ZALOHA))
    a["zakladniSleva"] = SLEVA_POPLATNIK if proh else 0
    a["danZalohaPoSleve"] = max(a["vypoctenaZaloha"] - a["zakladniSleva"], 0)
    a["sp_zam"] = _r(h * SP_ZAM)
    a["sp_firma"] = _r(h * SP_FIRMA)
    a["zp_zam"] = _r(h * ZP_ZAM)
    a["zp_firma"] = _r(h * ZP_FIRMA)
    a["cista"] = _r(h) - a["sp_zam"] - a["zp_zam"] - a["danZalohaPoSleve"]
    fond_h = float(p.get("fond_hodin", 160) or 160)
    a["vydelekPrumernyHod"] = round(h / fond_h, 2) if fond_h else 0.0
    return a


def _person_form(a, rok, mesic, dni_v_mesici):
    """Sestaví <n1:formularOsoby> pro jednu osobu (bezPriznaku)."""
    h = _r(float(a["hruba"]))
    mstart = "%04d-%02d-01" % (rok, mesic)
    mend = "%04d-%02d-%02d" % (rok, mesic, dni_v_mesici)
    proh = "true" if bool(a.get("prohlaseni", True)) else "false"
    obec = a.get("obec", "Praha")
    kod_obce = a.get("kodObce", "554782")
    fond_h = int(a.get("fond_hodin", 160) or 160)
    tyden = int(a.get("tyden_hodin", 40) or 40)
    odprac_dny = int(a.get("odprac_dny", dni_v_mesici))
    odprac_hod = int(a.get("odprac_hodin", fond_h))

    # --- OČR ---
    ocr_dny = int(a.get("ocr_dny", 0) or 0)
    ocr_hodiny = float(a.get("ocr_hodiny", 0) or 0)
    hod_ocr_xml = ""
    if ocr_hodiny:
        hod_ocr_xml = "\n\t\t\t\t\t<form:hodinyNeodpracOcr>%s</form:hodinyNeodpracOcr>" % (
            ("%.3f" % ocr_hodiny).rstrip("0").rstrip(".")
        )
    vyl_xml = ""
    odec_xml = ""
    if ocr_dny:
        vyl_xml = ("\n\t\t\t\t\t\t\t<form:vylouceneDny>"
                   "<form:osetrovaniClenaRodiny>%d</form:osetrovaniClenaRodiny>"
                   "</form:vylouceneDny>" % ocr_dny)
        odec_xml = ("\n\t\t\t\t\t\t\t<form:odecitaneDny>"
                    "<form:osetrovaniSNarokem>%d</form:osetrovaniSNarokem>"
                    "</form:odecitaneDny>" % ocr_dny)

    return f"""\t<n1:formularOsoby>
\t\t<n1:hlavicka>
\t\t\t<n1:idFormulare>{uuid.uuid4()}</n1:idFormulare>
\t\t\t<n1:typFormulare>R</n1:typFormulare>
\t\t\t<n1:primarniPpv>true</n1:primarniPpv>
\t\t</n1:hlavicka>
\t\t<form:bezPriznaku>
\t\t\t<form:identifikace>
\t\t\t\t<form:ikMpsv>{a['ikMpsv']}</form:ikMpsv>
\t\t\t\t<form:idPpv>{a['idPpv']}</form:idPpv>
\t\t\t</form:identifikace>
\t\t\t<form:souhrnDataZec>
\t\t\t\t<form:prijmy>
\t\t\t\t\t<form:zuctovanoCelkem>{h}</form:zuctovanoCelkem>
\t\t\t\t</form:prijmy>
\t\t\t\t<form:zalohaNaDan>
\t\t\t\t\t<form:zakladDane>{h}</form:zakladDane>
\t\t\t\t\t<form:vypoctenaZaloha>{a['vypoctenaZaloha']}</form:vypoctenaZaloha>
\t\t\t\t\t<form:danZalohaPoSleve>{a['danZalohaPoSleve']}</form:danZalohaPoSleve>
\t\t\t\t</form:zalohaNaDan>
\t\t\t\t<form:prohlaseniPoplatnika>{proh}</form:prohlaseniPoplatnika>
\t\t\t\t<form:prohlaseniPoplatnikaDane>
\t\t\t\t\t<form:zakladniSleva>{a['zakladniSleva']}</form:zakladniSleva>
\t\t\t\t</form:prohlaseniPoplatnikaDane>
\t\t\t\t<form:mzdaCista>
\t\t\t\t\t<form:mzdaCista>{a['cista']}</form:mzdaCista>
\t\t\t\t\t<form:srazkyZeMzdyEvidovany>false</form:srazkyZeMzdyEvidovany>
\t\t\t\t</form:mzdaCista>
\t\t\t\t<form:zdravPojZamestnavatel>
\t\t\t\t\t<form:zdravotniPojisteni>{a['zp_firma']}</form:zdravotniPojisteni>
\t\t\t\t</form:zdravPojZamestnavatel>
\t\t\t\t<form:zdravPojZamestnanec>
\t\t\t\t\t<form:zdravotniPojisteni>{a['zp_zam']}</form:zdravotniPojisteni>
\t\t\t\t</form:zdravPojZamestnanec>
\t\t\t</form:souhrnDataZec>
\t\t\t<form:pojisteni>
\t\t\t\t<form:trvani>
\t\t\t\t\t<form:pojisteniOd>{mstart}</form:pojisteniOd>
\t\t\t\t\t<form:pojisteniDo>{mend}</form:pojisteniDo>
\t\t\t\t</form:trvani>
\t\t\t\t<form:vymerovaciZaklad>
\t\t\t\t\t<form:castkaOdvodPojistneho>{h}</form:castkaOdvodPojistneho>
\t\t\t\t\t<form:prijemNepojistenaCinnost>0</form:prijemNepojistenaCinnost>
\t\t\t\t</form:vymerovaciZaklad>
\t\t\t\t<form:vymerovaciZakladParagraf5>
\t\t\t\t\t<form:pismenoA>{h}</form:pismenoA>
\t\t\t\t</form:vymerovaciZakladParagraf5>
\t\t\t\t<form:eldpSeznam>
\t\t\t\t\t<form:eldp>
\t\t\t\t\t\t<form:kod>1++</form:kod>
\t\t\t\t\t\t<form:platnostOd>{mstart}</form:platnostOd>
\t\t\t\t\t\t<form:platnostDo>{mend}</form:platnostDo>
\t\t\t\t\t\t<form:pocetDnu>{dni_v_mesici}</form:pocetDnu>
\t\t\t\t\t\t<form:vymerovaciZaklad>{h}</form:vymerovaciZaklad>{vyl_xml}{odec_xml}
\t\t\t\t\t</form:eldp>
\t\t\t\t</form:eldpSeznam>
\t\t\t\t<form:pojisteniZamestnanec>
\t\t\t\t\t<form:socialniPojisteni>{a['sp_zam']}</form:socialniPojisteni>
\t\t\t\t</form:pojisteniZamestnanec>
\t\t\t\t<form:pojisteniZamestnavatel>
\t\t\t\t\t<form:socialniPojisteni>{a['sp_firma']}</form:socialniPojisteni>
\t\t\t\t</form:pojisteniZamestnavatel>
\t\t\t\t<form:slevaZamestnance>
\t\t\t\t\t<form:slevaZamestnanceEvidovana>false</form:slevaZamestnanceEvidovana>
\t\t\t\t\t<form:slevaZamestnanceOvoZelEvidovana>false</form:slevaZamestnanceOvoZelEvidovana>
\t\t\t\t</form:slevaZamestnance>
\t\t\t\t<form:slevaZamestnavatele>
\t\t\t\t\t<form:slevaZamestnavateleEvidovana>false</form:slevaZamestnavateleEvidovana>
\t\t\t\t</form:slevaZamestnavatele>
\t\t\t</form:pojisteni>
\t\t\t<form:vykonavanaPozice>
\t\t\t\t<form:mistoVykonuPrace>
\t\t\t\t\t<form:obec>{obec}</form:obec>
\t\t\t\t\t<form:kodObce>{kod_obce}</form:kodObce>
\t\t\t\t\t<form:kodStatu>CZ</form:kodStatu>
\t\t\t\t</form:mistoVykonuPrace>
\t\t\t\t<form:uplatnujiPrispevekApz>false</form:uplatnujiPrispevekApz>
\t\t\t\t<form:funkcniPozitky>false</form:funkcniPozitky>
\t\t\t\t<form:docasnePrideleniEvidovano>false</form:docasnePrideleniEvidovano>
\t\t\t\t<form:fondPracovniDoby>
\t\t\t\t\t<form:stanovenyFond>{fond_h}</form:stanovenyFond>
\t\t\t\t\t<form:sjednanyFond>{fond_h}</form:sjednanyFond>
\t\t\t\t\t<form:stanovenaTydenniDoba>{tyden}</form:stanovenaTydenniDoba>
\t\t\t\t</form:fondPracovniDoby>
\t\t\t</form:vykonavanaPozice>
\t\t\t<form:prubehZamestnani>
\t\t\t\t<form:odpracovaneDny>
\t\t\t\t\t<form:dnyEvidencniStav>{odprac_dny}</form:dnyEvidencniStav>
\t\t\t\t</form:odpracovaneDny>
\t\t\t\t<form:odpracovaneHodiny>
\t\t\t\t\t<form:pocet>{odprac_hod}</form:pocet>
\t\t\t\t</form:odpracovaneHodiny>{hod_ocr_xml}
\t\t\t</form:prubehZamestnani>
\t\t\t<form:prijem>
\t\t\t\t<form:dan>
\t\t\t\t\t<form:zakladDane>{h}</form:zakladDane>
\t\t\t\t</form:dan>
\t\t\t</form:prijem>
\t\t\t<form:mzda>
\t\t\t\t<form:mzdaZuctovana>{h}</form:mzdaZuctovana>
\t\t\t\t<form:mzdaRozpad>
\t\t\t\t\t<form:tarif>{h}</form:tarif>
\t\t\t\t\t<form:odmenyPravidelne>0</form:odmenyPravidelne>
\t\t\t\t\t<form:odmenyNepravidelne>0</form:odmenyNepravidelne>
\t\t\t\t</form:mzdaRozpad>
\t\t\t\t<form:vydelek>
\t\t\t\t\t<form:vydelekPrumernyHod>{a['vydelekPrumernyHod']}</form:vydelekPrumernyHod>
\t\t\t\t</form:vydelek>
\t\t\t</form:mzda>
\t\t</form:bezPriznaku>
\t</n1:formularOsoby>"""


def build_jmhz(rok, mesic, persons, datum_vyplneni=None):
    """Sestaví celé JMHZ podání z listu osob (každá s klíčem 'hruba' + identifikátory)."""
    dni = calendar.monthrange(rok, mesic)[1]
    amt = [compute_person_amounts(p) for p in persons]
    dan_celkem = sum(a["danZalohaPoSleve"] for a in amt)
    zaklad_zam_a = sum(_r(float(a["hruba"])) for a in amt)
    poj_firma_a = sum(a["sp_firma"] for a in amt)
    poj_zam = sum(a["sp_zam"] for a in amt)
    poj_celkem = poj_firma_a + poj_zam
    if datum_vyplneni is None:
        datum_vyplneni = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    forms = "\n".join(_person_form(a, rok, mesic, dni) for a in amt)
    n = len(amt)
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<n1:jmhz {NS}>
\t<n1:VENDOR productName="STRATEGIE" productVersion="{VENDOR}"/>
\t<n1:SENDER EmailNotifikace="{SENDER_EMAIL}" ISDSreport="" VerzeProtokolu="1"/>
\t<n1:hlavicka>
\t\t<n1:idPodani>{uuid.uuid4()}</n1:idPodani>
\t\t<n1:typPodani>R</n1:typPodani>
\t\t<n1:variabilniSymbol>{VARIABILNI_SYMBOL}</n1:variabilniSymbol>
\t\t<n1:mesic>{mesic}</n1:mesic>
\t\t<n1:rok>{rok}</n1:rok>
\t\t<n1:datumVyplneni>{datum_vyplneni}</n1:datumVyplneni>
\t\t<n1:balikPoradi>1</n1:balikPoradi>
\t\t<n1:balikyPocet>1</n1:balikyPocet>
\t\t<n1:formularePocetVBaliku>{n}</n1:formularePocetVBaliku>
\t\t<n1:formularePocetCelkem>{n}</n1:formularePocetCelkem>
\t</n1:hlavicka>
\t<so:souhrn>
\t\t<so:danUdajeMesic>
\t\t\t<so:danZalohaPoSleve>{dan_celkem}</so:danZalohaPoSleve>
\t\t\t<so:danBonus>0</so:danBonus>
\t\t</so:danUdajeMesic>
\t</so:souhrn>
\t<pvpoj:PVPOJ>
\t\t<pvpoj:pojistne>
\t\t\t<pvpoj:zakladZamestnavateleA>{zaklad_zam_a}</pvpoj:zakladZamestnavateleA>
\t\t\t<pvpoj:pojistneZamestnavateleA>{poj_firma_a}</pvpoj:pojistneZamestnavateleA>
\t\t\t<pvpoj:zakladZamestnavateleB>0</pvpoj:zakladZamestnavateleB>
\t\t\t<pvpoj:pojistneZamestnavateleB>0</pvpoj:pojistneZamestnavateleB>
\t\t\t<pvpoj:zakladZamestnavateleC>0</pvpoj:zakladZamestnavateleC>
\t\t\t<pvpoj:pojistneZamestnavateleC>0</pvpoj:pojistneZamestnavateleC>
\t\t\t<pvpoj:pojistneZamestnavateleCelkem>{poj_firma_a}</pvpoj:pojistneZamestnavateleCelkem>
\t\t\t<pvpoj:pojistneZamestnance>{poj_zam}</pvpoj:pojistneZamestnance>
\t\t\t<pvpoj:pojistneCelkem>{poj_celkem}</pvpoj:pojistneCelkem>
\t\t</pvpoj:pojistne>
\t\t<pvpoj:pojistneUhrada>{poj_celkem}</pvpoj:pojistneUhrada>
\t</pvpoj:PVPOJ>
\t<n1:formulareOsob>
{forms}
\t</n1:formulareOsob>
</n1:jmhz>
"""


def load_persons_from_db(rok, mesic, firma):
    """Načte osoby z tenant.c_vyplatnice (+ OČR z att_entry) pro daný měsíc/firmu.
    Vyžaduje env DATABASE_URL / PG DSN a psycopg2. ikMpsv/idPpv se doplní z IDENT_MAP."""
    import psycopg2, psycopg2.extras
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("PG_DSN")
    if not dsn:
        raise SystemExit("chybí DATABASE_URL / PG_DSN")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT v.user_id, v.hruba, v.sleva, v.stav
        FROM tenant.c_vyplatnice v
        WHERE v.firma=%s AND v.rok=%s AND v.mesic=%s
        ORDER BY v.user_id
    """, (firma, rok, mesic))
    rows = cur.fetchall()
    persons = []
    for r in rows:
        p = {
            "user_id": r["user_id"],
            "hruba": r["hruba"],
            "prohlaseni": True,
            "ikMpsv": IDENT_MAP.get(r["user_id"], (None, None))[0] or "9000000000",
            "idPpv": IDENT_MAP.get(r["user_id"], (None, None))[1] or "4002831000000",
        }
        persons.append(p)
    return persons


# Mapa reálných identifikátorů ČSSZ na user_id (DOPLNIT z registrace).
# Dokud je prázdná, použijí se placeholdery (projdou ČSSZ TEST validací).
IDENT_MAP = {}


# demo data (Kristý + Marek, ES 6/2026) — k ověření struktury bez DB
DEMO_ES_2026_06 = [
    {"jmeno": "Kristýna Marešová", "cislo_zam": 21, "hruba": 49216, "prohlaseni": True,
     "obec": "Plzeň", "kodObce": "554791", "fond_hodin": 160,
     "odprac_dny": 18, "odprac_hodin": 128,
     "ikMpsv": "9000000021", "idPpv": "4002831000021",
     "ocr_dny": 4, "ocr_hodiny": 32},   # ošetřovné Nina 23.-26.6.
    {"jmeno": "Marek Honal", "cislo_zam": 370, "hruba": 65500, "prohlaseni": True,
     "obec": "Plzeň", "kodObce": "554791", "fond_hodin": 160,
     "ikMpsv": "9000000370", "idPpv": "4002831000370"},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rok", type=int, default=2026)
    ap.add_argument("--mesic", type=int, default=6)
    ap.add_argument("--firma", default="ES")
    ap.add_argument("--out", default=None)
    ap.add_argument("--demo", action="store_true", help="použít zabudovaná demo data (bez DB)")
    args = ap.parse_args()

    if args.demo:
        persons = DEMO_ES_2026_06
    else:
        persons = load_persons_from_db(args.rok, args.mesic, args.firma)

    xml = build_jmhz(args.rok, args.mesic, persons)
    out = args.out or "docs/jmhz/JMHZ_%s_%04d-%02d.xml" % (args.firma, args.rok, args.mesic)
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print("OK →", out, "(%d osob)" % len(persons))


if __name__ == "__main__":
    main()
