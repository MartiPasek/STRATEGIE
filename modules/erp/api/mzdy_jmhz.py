# -*- coding: utf-8 -*-
"""JMHZ (Jednotné měsíční hlášení zaměstnavatele, ČSSZ) — generace + ověření U MZDÁM.

Server-side: čte spočítané mzdy PŘÍMO z cloud Heliosu (TabZamVyp) za firma/rok/měsíc,
sestaví JMHZ podání a umí ho poslat na oficiální ČSSZ validátor. Znovuspustitelné
z TLAČÍTKA na stránce Výplatnice (výběr firma + rok + měsíc).

Kostra je stavěná po hácích, které doplňujeme BOD PO BODU:
  load_persons_helios   — základ z Heliosu (hrubá, SP/ZP/daň/čistá)         [hotovo]
  attach_identifikatory — IK MPSV / ID PPV (teď placeholder → reálná RČ)    [BOD 1]
  attach_absence        — OČR / nemoc / dovolená z docházky do ELDP         [BOD 2]
  attach_dane           — sleva na dítě / daňové zvýhodnění (čistá = Helios)[BOD 3]
  (pojistný vztah DPP/DPČ u 0-pojištění / 0-příjem)                         [BOD 4]

Historie: obnoveno z ověřeného pilotu 3.7.2026 (STRATEGIE_JMHZ_0.1, prošlo ČSSZ
ePodaniValidace). 12.7.2026 přesun ke mzdám + generace z Heliosu + tlačítko (Claude23).
Ověřeno 12.7.2026: 17/17 EC + 33/33 ES OK proti ČSSZ TEST.
"""
import math, uuid, datetime, calendar
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

# ---------------------------------------------------------------------------
# Konstanty podání
# ---------------------------------------------------------------------------
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
# VS zaměstnavatele u ČSSZ (Marti 12.7.2026, potvrzeno). EC = "EUROSOFT - Control",
# ES = "EUROSOFT - System". Stejný VS se používá i pro automatické stahování notifikací
# k nemocenské/OČR (eNeschopenka). Zdroj pravdy — drž tady + v paměti [[cssz-vs-zamestnavatele]].
VS_ZAMESTNAVATELE = {"EC": "4445158191", "ES": "4442058998"}
DEFAULT_VS = "4445158191"

# ověřené sazby (z pilotu)
SP_ZAM = 0.071
SP_FIRMA = 0.248
ZP_ZAM = 0.045
ZP_FIRMA = 0.090
ZALOHA = 0.15
SLEVA_POPLATNIK = 2570

# ELDP — mapování Helios sloupců TabMzJmhzEldp → XSD elementy, V POŘADÍ XSD
# (formCommonTypes.xsd: vylouceneDnyType / odecitaneDnyType). BOD 4.
VD_MAP = [
    ("VD_DocasnaPN", "docasNeschopnost"),
    ("VD_PPM", "penezitaPomocMaterstvi"),
    ("VD_OCR", "osetrovaniClenaRodiny"),
    ("VD_Otcovska", "otcovska"),
    ("VD_Paragraf_16", "vyloucenePar16"),
    ("VD_Paragraf_18", "vyloucenePar18"),
    ("VD_OmluvenaNeprit", "omluvenaNepritomnost"),
    ("VD_PracNechopnost", "pracovniNeschopnost"),
    ("VD_VyplaceniDavek", "vyplaceniDavek"),
]
OD_MAP = [
    ("OD_DocasnaPN", "pracovniNeschopnost"),
    ("OD_PPM", "materstvi"),
    ("OD_OCR_s_narokem", "osetrovaniSNarokem"),
    ("OD_OCR_bez_naroku", "osetrovaniBezNaroku"),
    ("OD_Otcovska", "otcovska"),
    ("OD_NeplaceneVolno", "neplaceneVolno"),
    ("OD_NeomluvenaAbs", "neomluveneAbsence"),
]

# ZMR — zaměstnání malého rozsahu / dohody BEZ účasti na pojištění. ELDP kód dle druhu vztahu:
# DPP → T++, DPČ → A++ (oficiální ČSSZ vzory TS 1.4 036 / 021). Helios u nich drží v TabMzJmhzEldp
# PRÁZDNÝ Kod a druh vztahu tam není → explicitní mapa (potvrzeno s Marti 17.7.2026: Senft #374 i
# Herejtová #525 = DPP → T++). Default mimo mapu = T++ (DPP). TODO: až bude Marti-AI mít přístup
# do UCTO_EC/ES, odvodit druh vztahu z Helios (TabMzJmhzPP / pojistný vztah) a mapu zrušit.
ZMR_KOD = {("EC", 374): "T++", ("EC", 525): "T++"}
ZMR_KOD_DEFAULT = "T++"
JEDNATEL_OIC = {"1122284229"}  # Marti Pašek — jednatel (druh činnosti S) → cinnostKS (40343)


def _r(x):
    return int(round(x))


def compute_person_amounts(p):
    """Spočítá částky pro JMHZ. Pokud máme reálné spočítané hodnoty z Heliosu
    (helios_ready = TabZamVyp), použije je NAPŘÍMO → čistá + daň + SP/ZP sedí 1:1 na Helios
    (BOD 3). Jinak derivuje z hrubé (SP/ZP přesně sazby, daň jen sleva poplatníka)."""
    h = float(p["hruba"])
    proh = bool(p.get("prohlaseni", True))
    a = dict(p)
    a["vz_sp"] = int(p["vz_sp"]) if p.get("vz_sp") is not None else _r(h)
    a["sp_firma_form"] = int(math.ceil(a["vz_sp"] * SP_FIRMA))  # 20315: pojistne zamestnavatele na formulari = ceil(VZ*0.248)
    a["zuctovanoCelkem"] = _r(h)
    fond_h = float(p.get("fond_hodin", 160) or 160)
    a["vydelekPrumernyHod"] = round(h / fond_h, 2) if fond_h else 0.0

    if p.get("helios_ready"):
        sp_zam = int(p.get("helios_sp_zam", 0) or 0)
        zp_zam = int(p.get("helios_zp_zam", 0) or 0)
        sp_firma = int(p.get("helios_sp_firma", 0) or 0)
        cista = int(p.get("helios_cista", 0) or 0)
        vyp_zaloha = int(p.get("helios_dan", 0) or 0)   # DanZakladni = vypočtená záloha (před slevou)
        withheld = _r(h) - sp_zam - zp_zam - cista       # reálně sražená záloha po slevách/zvýhodnění
        a["sp_zam"] = sp_zam
        a["sp_firma"] = sp_firma
        a["zp_zam"] = zp_zam
        a["zp_firma"] = int(p.get("helios_zp_firma") or _r(h * ZP_FIRMA))
        a["cista"] = cista
        a["vypoctenaZaloha"] = vyp_zaloha
        a["danZalohaPoSleve"] = max(withheld, 0)
        a["danBonus"] = max(-withheld, 0)
        # sleva poplatníka + prohlášení z TabMzJmhzPP (attach_dane), fallback 2570
        if p.get("zakladniSleva_real") is not None:
            a["zakladniSleva"] = int(p.get("zakladniSleva_real"))
        else:
            a["zakladniSleva"] = SLEVA_POPLATNIK if proh else 0
        if p.get("zmr"):  # ZMR / dohoda bez účasti — nulové SP i ZP (čistá/daň zůstává z Heliosu)
            a["sp_zam"] = 0
            a["sp_firma"] = 0
            a["zp_zam"] = 0
            a["zp_firma"] = 0
        return a

    # --- fallback: derivace z hrubé (bez Helios hodnot) ---
    a["vypoctenaZaloha"] = int(math.ceil(h * ZALOHA))
    a["zakladniSleva"] = SLEVA_POPLATNIK if proh else 0
    a["danZalohaPoSleve"] = max(a["vypoctenaZaloha"] - a["zakladniSleva"], 0)
    a["danBonus"] = 0
    a["sp_zam"] = _r(h * SP_ZAM)
    a["sp_firma"] = _r(h * SP_FIRMA)
    a["zp_zam"] = _r(h * ZP_ZAM)
    a["zp_firma"] = _r(h * ZP_FIRMA)
    a["cista"] = _r(h) - a["sp_zam"] - a["zp_zam"] - a["danZalohaPoSleve"]
    return a


def _person_form(a, rok, mesic, dni_v_mesici):
    h = _r(float(a["hruba"]))
    mzda_rozpad_xml = "" if h == 0 else ("<form:mzdaRozpad>"
        "<form:tarif>%d</form:tarif>"
        "<form:odmenyPravidelne>0</form:odmenyPravidelne>"
        "<form:odmenyNepravidelne>0</form:odmenyNepravidelne>"
        "</form:mzdaRozpad>" % h)
    mstart = "%04d-%02d-01" % (rok, mesic)
    mend = "%04d-%02d-%02d" % (rok, mesic, dni_v_mesici)
    proh = "true" if bool(a.get("prohlaseni", True)) else "false"
    obec = a.get("obec", "Plzeň")
    kod_obce = a.get("kodObce", "554791")
    fond_h = int(a.get("fond_hodin", 160) or 160)
    tyden = int(a.get("tyden_hodin", 40) or 40)
    odprac_dny = int(a.get("odprac_dny", dni_v_mesici))
    odprac_hod = int(a.get("odprac_hodin", fond_h))

    # --- neodpracované hodiny OČR (z docházky; hodiny = pracovní, doplněk k VD dnům) ---
    ocr_hodiny = float(a.get("ocr_hodiny", 0) or 0)
    hod_ocr_xml = ""
    if ocr_hodiny:
        _oh = ("%.3f" % ocr_hodiny).rstrip("0").rstrip(".")
        hod_ocr_xml = ("\n\t\t\t\t<form:neodpracovaneHodiny>"
                       "\n\t\t\t\t\t<form:hodinyNeodpracCelkem>%s</form:hodinyNeodpracCelkem>"
                       "\n\t\t\t\t\t<form:hodinyNeodpracOcr>%s</form:hodinyNeodpracOcr>"
                       "\n\t\t\t\t</form:neodpracovaneHodiny>" % (_oh, _oh))

    # --- ELDP z Heliosu (BOD 4): typ prac. poměru (Kod) + vyloučené/odečitatelné doby ---
    # Autoritativní zdroj = TabMzJmhzEldp (mzdové karty). Kód: 1++ běžný PP, S++ jednatel,
    # prázdný → DPP malého rozsahu (fallback 1++, viz pozn. u attach_eldp). Kategorie
    # vyloučených/odečítaných dnů se skládají v POŘADÍ XSD (VD_MAP / OD_MAP).
    eldp_kod = (a.get("eldp_kod") or "").strip() or "1++"
    vd = a.get("eldp_vd") or {}
    vd_celkem = int(a.get("eldp_vd_celkem", 0) or 0)
    vyl_xml = ""
    if vd_celkem or any(vd.values()):
        _p = ["<form:vylouceneDobyCelkem>%d</form:vylouceneDobyCelkem>" % vd_celkem]
        for _col, _el in VD_MAP:
            _v = int(vd.get(_el, 0) or 0)
            if _v:
                _p.append("<form:%s>%d</form:%s>" % (_el, _v, _el))
        vyl_xml = "\n\t\t\t\t\t\t\t<form:vylouceneDny>" + "".join(_p) + "</form:vylouceneDny>"
    od = a.get("eldp_od") or {}
    od_celkem = int(a.get("eldp_od_celkem", 0) or 0)
    odec_xml = ""
    if od_celkem or any(od.values()):
        _p = ["<form:odecitaneDobyCelkem>%d</form:odecitaneDobyCelkem>" % od_celkem]
        for _col, _el in OD_MAP:
            _v = int(od.get(_el, 0) or 0)
            if _v:
                _p.append("<form:%s>%d</form:%s>" % (_el, _v, _el))
        odec_xml = "\n\t\t\t\t\t\t\t<form:odecitaneDny>" + "".join(_p) + "</form:odecitaneDny>"

    # --- ZMR (zaměstnání malého rozsahu / DPP bez účasti na pojištění) ---
    # Detekce: prázdný Kod v Helios ELDP (attach_eldp → zmr=True, eldp_kod=T++/A++). Struktura
    # dle oficiálních ČSSZ vzorů (TS 1.4 036 DPP / 021 DPČ): vyměř. základ jen prijemNepojistenaCinnost,
    # BEZ vymerovaciZakladParagraf5; SP i ZP = 0 (řeší compute_person_amounts); ELDP bez vyl./odečít. dob.
    if bool(a.get("zmr")):
        vyl_xml = ""
        odec_xml = ""
        vz_par5_xml = ("\t\t\t\t<form:vymerovaciZaklad>\n"
                       "\t\t\t\t\t<form:prijemNepojistenaCinnost>%d</form:prijemNepojistenaCinnost>\n"
                       "\t\t\t\t</form:vymerovaciZaklad>" % h)
    else:
        vz_par5_xml = ("\t\t\t\t<form:vymerovaciZaklad>\n"
                       "\t\t\t\t\t<form:castkaOdvodPojistneho>%d</form:castkaOdvodPojistneho>\n"
                       "\t\t\t\t\t<form:prijemNepojistenaCinnost>0</form:prijemNepojistenaCinnost>\n"
                       "\t\t\t\t</form:vymerovaciZaklad>\n"
                       "\t\t\t\t<form:vymerovaciZakladParagraf5>\n"
                       "\t\t\t\t\t<form:pismenoA>%d</form:pismenoA>\n"
                       "\t\t\t\t</form:vymerovaciZakladParagraf5>" % (a['vz_sp'], a['vz_sp']))

    if str(a.get("ikMpsv", "")).strip() in JEDNATEL_OIC:
        # cinnostKS = jednatel / člen orgánu PO (druh činnosti "S"). Struktura ověřena proti
        # produkčnímu validátoru ČSSZ 20.7.2026 (bez vymerovaciZakladParagraf5 a slevaZamestnavatele,
        # bez prubehZamestnani a mzda). Řeší chybu 40343.
        return (
            "\t<n1:formularOsoby>"
            "<n1:hlavicka><n1:idFormulare>%s</n1:idFormulare><n1:typFormulare>R</n1:typFormulare><n1:primarniPpv>true</n1:primarniPpv></n1:hlavicka>"
            "<form:cinnostKS>"
            "<form:identifikace><form:ikMpsv>%s</form:ikMpsv><form:idPpv>%s</form:idPpv></form:identifikace>"
            "<form:souhrnDataZec>"
            "<form:prijmy><form:zuctovanoCelkem>%d</form:zuctovanoCelkem></form:prijmy>"
            "<form:zalohaNaDan><form:zakladDane>%d</form:zakladDane><form:vypoctenaZaloha>%d</form:vypoctenaZaloha><form:danZalohaPoSleve>%d</form:danZalohaPoSleve></form:zalohaNaDan>"
            "<form:prohlaseniPoplatnika>%s</form:prohlaseniPoplatnika>"
            "<form:prohlaseniPoplatnikaDane><form:zakladniSleva>%d</form:zakladniSleva></form:prohlaseniPoplatnikaDane>"
            "<form:zdravPojZamestnanec><form:zdravotniPojisteni>%d</form:zdravotniPojisteni></form:zdravPojZamestnanec>"
            "</form:souhrnDataZec>"
            "<form:pojisteni>"
            "<form:trvani><form:pojisteniOd>%s</form:pojisteniOd><form:pojisteniDo>%s</form:pojisteniDo></form:trvani>"
            "<form:vymerovaciZaklad><form:castkaOdvodPojistneho>%d</form:castkaOdvodPojistneho><form:prijemNepojistenaCinnost>0</form:prijemNepojistenaCinnost></form:vymerovaciZaklad>"
            "<form:eldpSeznam><form:eldp><form:kod>%s</form:kod><form:platnostOd>%s</form:platnostOd><form:platnostDo>%s</form:platnostDo><form:pocetDnu>%d</form:pocetDnu><form:vymerovaciZaklad>%d</form:vymerovaciZaklad></form:eldp></form:eldpSeznam>"
            "<form:pojisteniZamestnanec><form:socialniPojisteni>%d</form:socialniPojisteni></form:pojisteniZamestnanec>"
            "<form:pojisteniZamestnavatel><form:socialniPojisteni>%d</form:socialniPojisteni></form:pojisteniZamestnavatel>"
            "<form:slevaZamestnance><form:slevaZamestnanceEvidovana>false</form:slevaZamestnanceEvidovana><form:slevaZamestnanceOvoZelEvidovana>false</form:slevaZamestnanceOvoZelEvidovana></form:slevaZamestnance>"
            "</form:pojisteni>"
            "<form:vykonavanaPozice><form:mistoVykonuPrace><form:obec>%s</form:obec><form:kodObce>%s</form:kodObce><form:kodStatu>CZ</form:kodStatu></form:mistoVykonuPrace><form:uplatnujiPrispevekApz>false</form:uplatnujiPrispevekApz><form:funkcniPozitky>false</form:funkcniPozitky><form:docasnePrideleniEvidovano>false</form:docasnePrideleniEvidovano><form:fondPracovniDoby><form:stanovenyFond>%d</form:stanovenyFond><form:sjednanyFond>%d</form:sjednanyFond><form:stanovenaTydenniDoba>%d</form:stanovenaTydenniDoba></form:fondPracovniDoby></form:vykonavanaPozice>"
            "<form:prijem><form:dan><form:zakladDane>%d</form:zakladDane></form:dan></form:prijem>"
            "</form:cinnostKS>"
            "</n1:formularOsoby>"
        ) % (uuid.uuid4(), a["ikMpsv"], a["idPpv"], h, h, a["vypoctenaZaloha"], a["danZalohaPoSleve"], proh, a["zakladniSleva"], a["zp_zam"], mstart, mend, a["vz_sp"], eldp_kod, mstart, mend, dni_v_mesici, a["vz_sp"], a["sp_zam"], a["sp_firma_form"], obec, kod_obce, fond_h, fond_h, tyden, h)

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
{vz_par5_xml}
\t\t\t\t<form:eldpSeznam>
\t\t\t\t\t<form:eldp>
\t\t\t\t\t\t<form:kod>{eldp_kod}</form:kod>
\t\t\t\t\t\t<form:platnostOd>{mstart}</form:platnostOd>
\t\t\t\t\t\t<form:platnostDo>{mend}</form:platnostDo>
\t\t\t\t\t\t<form:pocetDnu>{dni_v_mesici}</form:pocetDnu>
\t\t\t\t\t\t<form:vymerovaciZaklad>{a['vz_sp']}</form:vymerovaciZaklad>{vyl_xml}{odec_xml}
\t\t\t\t\t</form:eldp>
\t\t\t\t</form:eldpSeznam>
\t\t\t\t<form:pojisteniZamestnanec>
\t\t\t\t\t<form:socialniPojisteni>{a['sp_zam']}</form:socialniPojisteni>
\t\t\t\t</form:pojisteniZamestnanec>
\t\t\t\t<form:pojisteniZamestnavatel>
\t\t\t\t\t<form:socialniPojisteni>{a['sp_firma_form']}</form:socialniPojisteni>
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
\t\t\t\t<form:mzdaZuctovana>{h}</form:mzdaZuctovana>{mzda_rozpad_xml}
\t\t\t\t<form:vydelek>
\t\t\t\t\t<form:vydelekPrumernyHod>{a['vydelekPrumernyHod']}</form:vydelekPrumernyHod>
\t\t\t\t</form:vydelek>
\t\t\t</form:mzda>
\t\t</form:bezPriznaku>
\t</n1:formularOsoby>"""


def build_jmhz(rok, mesic, persons, datum_vyplneni=None, vs=None, opravne=False, id_podani=None):
    """Sestaví celé JMHZ podání z listu osob (každá s 'hruba' + identifikátory)."""
    vs = vs or DEFAULT_VS
    dni = calendar.monthrange(rok, mesic)[1]
    amt = [compute_person_amounts(p) for p in persons]
    dan_celkem = sum(a["danZalohaPoSleve"] for a in amt)
    bonus_celkem = sum(a.get("danBonus", 0) for a in amt)
    # ZMR / dohody bez účasti se nezapočítávají do vyměř. základu zaměstnavatele (PVPOJ)
    zaklad_zam_a = sum(_r(float(a["hruba"])) for a in amt if not a.get("zmr"))
    poj_firma_a = sum(a["sp_firma"] for a in amt)
    poj_zam = sum(a["sp_zam"] for a in amt)
    poj_celkem = poj_firma_a + poj_zam
    if datum_vyplneni is None:
        datum_vyplneni = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    forms = "\n".join(_person_form(a, rok, mesic, dni) for a in amt)
    if opravne:
        forms = forms.replace("<n1:typFormulare>R</n1:typFormulare>", "<n1:typFormulare>O</n1:typFormulare>")
    _typ_podani = "O" if opravne else "R"
    _id_podani = id_podani or str(uuid.uuid4())
    n = len(amt)
    pocet_formularu = n + 2  # 20235: ČSSZ počítá i SOUHRN + PVPOJ
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<n1:jmhz {NS}>
\t<n1:VENDOR productName="STRATEGIE" productVersion="{VENDOR}"/>
\t<n1:SENDER EmailNotifikace="{SENDER_EMAIL}" ISDSreport="" VerzeProtokolu="1"/>
\t<n1:hlavicka>
\t\t<n1:idPodani>{_id_podani}</n1:idPodani>
\t\t<n1:typPodani>{_typ_podani}</n1:typPodani>
\t\t<n1:variabilniSymbol>{vs}</n1:variabilniSymbol>
\t\t<n1:mesic>{mesic}</n1:mesic>
\t\t<n1:rok>{rok}</n1:rok>
\t\t<n1:datumVyplneni>{datum_vyplneni}</n1:datumVyplneni>
\t\t<n1:balikPoradi>1</n1:balikPoradi>
\t\t<n1:balikyPocet>1</n1:balikyPocet>
\t\t<n1:formularePocetVBaliku>{pocet_formularu}</n1:formularePocetVBaliku>
\t\t<n1:formularePocetCelkem>{pocet_formularu}</n1:formularePocetCelkem>
\t</n1:hlavicka>
\t<so:souhrn>
\t\t<so:danUdajeMesic>
\t\t\t<so:danZalohaPoSleve>{dan_celkem}</so:danZalohaPoSleve>
\t\t\t<so:danBonus>{bonus_celkem}</so:danBonus>
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


# ---------------------------------------------------------------------------
# Zdroj dat — cloud Helios (TabZamVyp) + hooky bod po bodu
# ---------------------------------------------------------------------------
def load_persons_helios(firma, rok, mesic):
    """Načte spočítané mzdy z cloud Heliosu (TabZamVyp) pro firma/rok/měsíc.
    Vrací list dictů se základními poli (hrubá + reálné SP/ZP/daň/čistá z Heliosu)."""
    from modules.erp.api import router as _r
    cloud_db = _r._firma_cloud_db(firma)
    ro = _r._mssql188_query("SELECT IdObdobi FROM " + cloud_db +
                            ".dbo.TabMzdObd WHERE Rok=" + str(int(rok)) +
                            " AND Mesic=" + str(int(mesic)))
    if not (ro.get("ok") and ro.get("rows")):
        return []
    idobd = int(ro["rows"][0][0])
    q = ("SELECT z.Cislo, RTRIM(z.Prijmeni), RTRIM(z.Jmeno), v.ZamestnanecId, "
         "CAST(ISNULL(v.HrubaMzda,0) AS int), CAST(ISNULL(v.SocPojZam,0) AS int), "
         "CAST(ISNULL(v.ZdrPojZam,0) AS int), CAST(ISNULL(v.DanZakladni,0) AS int), "
         "CAST(ISNULL(v.DanovyBonus,0) AS int), CAST(ISNULL(v.CistaMzda,0) AS int), "
         "CAST(ISNULL(v.SocPojFirma,0) AS int), "
         "CAST(ISNULL(v.ZakladSocPoj,0) AS int) "
         "FROM " + cloud_db + ".dbo.TabZamVyp v "
         "JOIN " + cloud_db + ".dbo.TabCisZam z ON z.ID=v.ZamestnanecId "
         "WHERE v.IdObdobi=" + str(idobd) + " ORDER BY z.Prijmeni, z.Jmeno")
    r = _r._mssql188_query(q)
    persons = []
    if r.get("ok") and r.get("rows"):
        for v in r["rows"]:
            persons.append({
                "cislo": v[0], "prijmeni": (v[1] or "").strip(), "jmeno": (v[2] or "").strip(),
                "zid": int(v[3] or 0), "hruba": int(v[4] or 0),
                "helios_sp_zam": int(v[5] or 0), "helios_zp_zam": int(v[6] or 0),
                "helios_dan": int(v[7] or 0), "helios_bonus": int(v[8] or 0),
                "helios_cista": int(v[9] or 0), "helios_sp_firma": int(v[10] or 0), "vz_sp": int(v[11] or 0),
                "helios_ready": True,
            })
    return persons


def attach_identifikatory(persons, firma, rok, mesic):
    """BOD 1 — reálné IK MPSV (Helios OsobniIC) + ID PPV z TabMzJmhzPP (poslední dostupný
    měsíc ≤ zvolené období, primární PPV). Identifikátory jsou stálé, takže se přebírají
    z posledního měsíce, kdy účetní JMHZ v Heliosu generovala (duben/květen 2026 dál).
    Fallback = placeholder per os.č. (pro osoby bez historie JMHZ; ČSSZ TEST je bere)."""
    from modules.erp.api import router as _r
    cloud_db = _r._firma_cloud_db(firma)
    obd = int(rok) * 100 + int(mesic)
    q = ("WITH latest AS ("
         "SELECT j.CisZam_ID AS zid, j.OsobniIC AS ik, j.ID_PPV AS ppv, "
         "ROW_NUMBER() OVER (PARTITION BY j.CisZam_ID ORDER BY o.Rok DESC, o.Mesic DESC) rn "
         "FROM " + cloud_db + ".dbo.TabMzJmhzPP j "
         "JOIN " + cloud_db + ".dbo.TabMzdObd o ON o.IdObdobi=j.IdObdobi "
         "WHERE j.PrimarniPPV=1 AND (o.Rok*100+o.Mesic)<=" + str(obd) + " "
         "AND LEN(ISNULL(j.OsobniIC,''))>0) "
         "SELECT zid, ik, ppv FROM latest WHERE rn=1")
    mp = {}
    try:
        r = _r._mssql188_query(q)
        if r.get("ok") and r.get("rows"):
            for v in r["rows"]:
                mp[int(v[0])] = ((v[1] or "").strip(), (v[2] or "").strip())
    except Exception:
        mp = {}
    for p in persons:
        zid = int(p.get("zid") or 0)
        real = mp.get(zid)
        c = int(p.get("cislo") or 0)
        if real and real[0]:
            p["ikMpsv"] = real[0]
            p["idPpv"] = real[1] or ("4002831" + str(c).zfill(6))
            p["ident_zdroj"] = "helios"
        else:
            p["ikMpsv"] = "9" + str(c).zfill(9)
            p["idPpv"] = "4002831" + str(c).zfill(6)
            p["ident_zdroj"] = "placeholder"
    return persons


def attach_absence(persons, firma, rok, mesic):
    """BOD 2 — OČR (ošetřovné) z docházky (tenant.att_ocr_case) → ocr_dny/ocr_hodiny + ELDP.

    Napojení: schválené OČR case překrývající zvolený měsíc, per company=firma, matchnuté
    na osobu přes att_employee.cislo_zam == Helios číslo (p['cislo']). Doplní vyloučené +
    odečitatelné dny a neodpracované hodiny OČR do formuláře; odpracované dny/hodiny
    zůstávají na fondu (tak, jak to prošlo ČSSZ TEST 12.7.2026 — Kristý ES č.21, 4 dny/32 h).
    Bezpečné aditivně: když osoba nemá OČR match, nechá ji beze změny."""
    import calendar as _cal, datetime as _dt
    from sqlalchemy import text as _t
    from core.database_data import get_data_session as _g
    fu = (firma or "").upper()
    mstart = _dt.date(int(rok), int(mesic), 1)
    mend = _dt.date(int(rok), int(mesic), _cal.monthrange(int(rok), int(mesic))[1])
    rows = []
    try:
        s = _g()
        try:
            res = s.execute(_t(
                "SELECT e.cislo_zam, oc.datum_od, oc.datum_do, COALESCE(oc.dny_count,0) "
                "FROM tenant.att_ocr_case oc "
                "JOIN tenant.att_employee e ON e.id=oc.employee_id "
                "WHERE oc.company=:firma AND oc.stav='schvaleno' "
                "AND oc.datum_od<=:mend AND oc.datum_do>=:mstart"),
                {"firma": fu, "mstart": mstart, "mend": mend}).fetchall()
            rows = [((str(x[0]).strip() if x[0] is not None else ""), x[1], x[2], int(x[3] or 0))
                    for x in res]
        finally:
            s.close()
    except Exception:
        rows = []
    if not rows:
        return persons

    # OČR dny per Helios číslo (překryv case s měsícem; celý case v měsíci → dny_count)
    by_cislo = {}
    for cz, od, do, cnt in rows:
        if not cz or not od or not do:
            continue
        i_od = od if od > mstart else mstart
        i_do = do if do < mend else mend
        if i_od > i_do:
            continue
        if od >= mstart and do <= mend and cnt:
            days = cnt
        else:
            days = sum(1 for k in range((i_do - i_od).days + 1)
                       if (i_od + _dt.timedelta(days=k)).weekday() < 5)
        if days:
            by_cislo[cz] = by_cislo.get(cz, 0) + days

    for p in persons:
        cz = str(p.get("cislo") if p.get("cislo") is not None else "").strip()
        d = by_cislo.get(cz)
        if d:
            tyden = float(p.get("tyden_hodin", 40) or 40)
            p["ocr_dny"] = int(d)
            p["ocr_hodiny"] = round(d * (tyden / 5.0), 3)
            p["ocr_zdroj"] = "att_ocr_case"
    return persons


def attach_dane(persons, firma, rok, mesic):
    """BOD 3 — daň + čistá bereme reálně z Heliosu (TabZamVyp, helios_ready → compute
    použije napřímo, čistá sedí 1:1). Sem doplníme jen STÁLÉ daňové příznaky z TabMzJmhzPP
    (poslední měsíc): prohlášení poplatníka + sleva poplatníka. Daňové zvýhodnění na děti je
    už zohledněné v reálné čisté/sražené záloze z Heliosu."""
    from modules.erp.api import router as _r
    cloud_db = _r._firma_cloud_db(firma)
    obd = int(rok) * 100 + int(mesic)
    q = ("WITH latest AS ("
         "SELECT j.CisZam_ID AS zid, j.prohlPoplatnika AS proh, j.prohlZakladniSleva AS sleva, "
         "ROW_NUMBER() OVER (PARTITION BY j.CisZam_ID ORDER BY o.Rok DESC, o.Mesic DESC) rn "
         "FROM " + cloud_db + ".dbo.TabMzJmhzPP j "
         "JOIN " + cloud_db + ".dbo.TabMzdObd o ON o.IdObdobi=j.IdObdobi "
         "WHERE j.PrimarniPPV=1 AND (o.Rok*100+o.Mesic)<=" + str(obd) + ") "
         "SELECT zid, proh, sleva FROM latest WHERE rn=1")
    mp = {}
    try:
        r = _r._mssql188_query(q)
        if r.get("ok") and r.get("rows"):
            for v in r["rows"]:
                mp[int(v[0])] = (v[1], v[2])
    except Exception:
        mp = {}
    for p in persons:
        zid = int(p.get("zid") or 0)
        d = mp.get(zid)
        if d is not None:
            proh_raw, sleva_raw = d
            if proh_raw is not None:
                p["prohlaseni"] = bool(proh_raw)
            if sleva_raw is not None:
                p["zakladniSleva_real"] = int(round(float(sleva_raw)))
    return persons


def attach_eldp(persons, firma, rok, mesic):
    """BOD 4 — typ pracovního poměru (Kod) + vyloučené/odečitatelné doby z Heliosu
    (TabMzJmhzEldp = ELDP na mzdové kartě, UCTO_EC/UCTO_ES). Autoritativní zdroj.
    Klíč = CisZam_ID (=zid = TabZamVyp.ZamestnanecId = TabCisZam.ID, shodně s TabMzJmhzPP
    u attach_identifikatory). Kód: 1++ běžný PP, S++ společník/jednatel, prázdný → DPP
    malého rozsahu bez účasti na pojištění (ve formuláři fallback 1++, dořeší se dle
    chování Heliosu). Kategorie VD/OD se sčítají přes všechny ELDP segmenty osoby v měsíci."""
    from modules.erp.api import router as _r
    cloud_db = _r._firma_cloud_db(firma)
    ro = _r._mssql188_query("SELECT IdObdobi FROM " + cloud_db +
                            ".dbo.TabMzdObd WHERE Rok=" + str(int(rok)) +
                            " AND Mesic=" + str(int(mesic)))
    if not (ro.get("ok") and ro.get("rows")):
        return persons
    idobd = int(ro["rows"][0][0])
    cols = [c for c, _ in VD_MAP] + [c for c, _ in OD_MAP]
    sel = ", ".join("CAST(ISNULL(e." + c + ",0) AS int)" for c in cols)
    q = ("SELECT e.CisZam_ID, ISNULL(RTRIM(e.Kod),''), "
         "CAST(ISNULL(e.VD_Celkem,0) AS int), CAST(ISNULL(e.OD_Celkem,0) AS int), " + sel +
         " FROM " + cloud_db + ".dbo.TabMzJmhzEldp e WHERE e.IdObdobi=" + str(idobd))
    agg = {}
    try:
        r = _r._mssql188_query(q)
        if r.get("ok") and r.get("rows"):
            for v in r["rows"]:
                zid = int(v[0] or 0)
                kod = (v[1] or "").strip()
                vd_cel = int(v[2] or 0)
                od_cel = int(v[3] or 0)
                base = 4
                vd = {}
                for i, (_c, el) in enumerate(VD_MAP):
                    dv = int(v[base + i] or 0)
                    if dv:
                        vd[el] = vd.get(el, 0) + dv
                od = {}
                obase = base + len(VD_MAP)
                for i, (_c, el) in enumerate(OD_MAP):
                    dv = int(v[obase + i] or 0)
                    if dv:
                        od[el] = od.get(el, 0) + dv
                a = agg.get(zid)
                if a is None:
                    agg[zid] = {"kod": kod, "vd": vd, "od": od,
                                "vd_celkem": vd_cel, "od_celkem": od_cel}
                else:  # více ELDP segmentů v měsíci → sčítat doby, kód = první neprázdný
                    if not a["kod"] and kod:
                        a["kod"] = kod
                    for el, dv in vd.items():
                        a["vd"][el] = a["vd"].get(el, 0) + dv
                    for el, dv in od.items():
                        a["od"][el] = a["od"].get(el, 0) + dv
                    a["vd_celkem"] += vd_cel
                    a["od_celkem"] += od_cel
    except Exception:
        agg = {}
    fu = (firma or "").upper()
    for p in persons:
        zid = int(p.get("zid") or 0)
        a = agg.get(zid)
        if a is not None:
            kod = (a["kod"] or "").strip()
            if not kod:  # prázdný Kod v Helios ELDP → ZMR / dohoda bez účasti na pojištění
                p["zmr"] = True
                p["eldp_kod"] = ZMR_KOD.get((fu, int(p.get("cislo") or 0)), ZMR_KOD_DEFAULT)
                p["eldp_vd"] = {}
                p["eldp_od"] = {}
                p["eldp_vd_celkem"] = 0
                p["eldp_od_celkem"] = 0
            else:
                p["eldp_kod"] = kod
                p["eldp_vd"] = a["vd"]
                p["eldp_od"] = a["od"]
                p["eldp_vd_celkem"] = a["vd_celkem"]
                p["eldp_od_celkem"] = a["od_celkem"]
            p["eldp_zdroj"] = "helios"
    return persons


def prepare_persons(firma, rok, mesic):
    ps = load_persons_helios(firma, rok, mesic)
    ps = attach_identifikatory(ps, firma, rok, mesic)
    ps = attach_absence(ps, firma, rok, mesic)
    ps = attach_dane(ps, firma, rok, mesic)
    ps = attach_eldp(ps, firma, rok, mesic)
    for p in ps:
        p["jmeno_full"] = ("%s %s" % (p.get("jmeno", ""), p.get("prijmeni", ""))).strip()
        p.setdefault("obec", "Plzeň")
        p.setdefault("kodObce", "554791")
        p.setdefault("fond_hodin", 160)
        p.setdefault("prohlaseni", True)
    return ps


def generate_xml(firma, rok, mesic, opravne=False, id_podani=None):
    ps = prepare_persons(firma, rok, mesic)
    vs = VS_ZAMESTNAVATELE.get((firma or "").upper(), DEFAULT_VS)
    xml = build_jmhz(rok, mesic, ps, vs=vs, opravne=opravne, id_podani=id_podani)
    return xml, ps


def generate_and_validate(firma, rok, mesic, prod=False, opravne=False, id_podani=None):
    xml, ps = generate_xml(firma, rok, mesic, opravne=opravne, id_podani=id_podani)
    from modules.erp.api import epodani_validace as ev
    res = ev.validate_xml_string(xml, test=(not prod))
    idx = {p.get("ikMpsv"): p for p in ps}
    for v in res.get("vysledky", []):
        p = idx.get(v.get("ikMpsv"))
        if p:
            v["cislo"] = p.get("cislo")
            v["jmeno"] = p.get("jmeno_full")
            v["hruba"] = p.get("hruba")
            v["ident_zdroj"] = p.get("ident_zdroj")
            if p.get("ocr_dny"):
                v["ocr_dny"] = p.get("ocr_dny")
            _k = (p.get("eldp_kod") or "").strip() or "1++"
            v["eldp_kod"] = _k
            if p.get("eldp_vd"):
                v["eldp_vd"] = p.get("eldp_vd")
    ok_cnt = sum(1 for v in res.get("vysledky", []) if v.get("ok"))
    ident_helios = sum(1 for p in ps if p.get("ident_zdroj") == "helios")
    ocr_osoby = [{"cislo": p.get("cislo"), "jmeno": p.get("jmeno_full"), "dny": p.get("ocr_dny")}
                 for p in ps if p.get("ocr_dny")]
    # ELDP přehled (BOD 4): rozložení kódů + osoby s vyloučenou dobou
    _kod_dist = {}
    for p in ps:
        _k = (p.get("eldp_kod") or "").strip() or "1++"
        _kod_dist[_k] = _kod_dist.get(_k, 0) + 1
    eldp_helios = sum(1 for p in ps if p.get("eldp_zdroj") == "helios")
    zmr_osoby = [{"cislo": p.get("cislo"), "jmeno": p.get("jmeno_full"),
                  "kod": p.get("eldp_kod"), "hruba": p.get("hruba")}
                 for p in ps if p.get("zmr")]
    vd_osoby = [{"cislo": p.get("cislo"), "jmeno": p.get("jmeno_full"),
                 "kod": (p.get("eldp_kod") or "").strip() or "1++",
                 "vd": p.get("eldp_vd"), "od": p.get("eldp_od") or None}
                for p in ps if p.get("eldp_vd") or p.get("eldp_od")]
    return {
        "ok": res.get("ok"), "firma": (firma or "").upper(), "rok": rok, "mesic": mesic,
        "prostredi": ("PRODUKCE" if prod else "test"),
        "pocet": len(ps), "ok_pocet": ok_cnt, "chyb": len(ps) - ok_cnt,
        "ident_helios": ident_helios, "ident_placeholder": len(ps) - ident_helios,
        "ocr_pocet": len(ocr_osoby), "ocr_osoby": ocr_osoby,
        "eldp_helios": eldp_helios, "eldp_kod_dist": _kod_dist,
        "vd_pocet": len(vd_osoby), "vd_osoby": vd_osoby,
        "zmr_pocet": len(zmr_osoby), "zmr_osoby": zmr_osoby,
        "vysledky": res.get("vysledky", []),
    }


# ---------------------------------------------------------------------------
# HTTP endpointy (tlačítko na Výplatnici)
# ---------------------------------------------------------------------------
jmhz_router = APIRouter(prefix="/api/v1/erp", tags=["mzdy-jmhz"])


def _guard(req):
    from modules.erp.api import router as _r
    from core.database_data import get_data_session as _g
    uid = _r._uid_from_token_or_cookie(req)
    s = _g()
    try:
        ok = _r._is_cockpit(s, uid)
    finally:
        s.close()
    return uid, ok


def _parse_obdobi(req):
    import datetime as _dt
    now = _dt.date.today()
    firma = (req.query_params.get("firma") or "ES").upper()
    try:
        rok = int(req.query_params.get("rok") or now.year)
        mesic = int(req.query_params.get("mesic") or now.month)
    except Exception:
        rok, mesic = now.year, now.month
    return firma, rok, mesic


@jmhz_router.get("/app/mzdy/jmhz/overit")
def jmhz_overit(req: Request):
    """Vygeneruje JMHZ za období z Heliosu a ověří každou osobu u ČSSZ (test). Parent-only."""
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma, rok, mesic = _parse_obdobi(req)
    prod = (req.query_params.get("prod") or "").lower() in ("1", "true", "ano")
    try:
        out = generate_and_validate(firma, rok, mesic, prod=prod)
    except Exception as e:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400])},
                            status_code=200)
    return out


@jmhz_router.get("/app/mzdy/jmhz/xml")
def jmhz_xml(req: Request):
    """Stáhne JMHZ XML za období (pro podání přes ePortál/datovku). Parent-only."""
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    firma, rok, mesic = _parse_obdobi(req)
    _oprav = (req.query_params.get("opravne") or "").lower() in ("1", "true", "ano")
    _guid = req.query_params.get("guid") or None
    try:
        xml, ps = generate_xml(firma, rok, mesic, opravne=_oprav, id_podani=_guid)
    except Exception as e:
        return JSONResponse({"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400])},
                            status_code=200)
    fn = "JMHZ_%s_%04d-%02d%s.xml" % (firma, rok, mesic, ("_O" if _oprav else ""))
    return Response(content=xml, media_type="application/xml",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % fn})
