# -*- coding: utf-8 -*-
"""Ověření dodavatele proti státním registrům — NAŠE vlastní ověření (razítko),
nezávislé na Heliosu. Marti 6.7.2026.

- ARES (REST/JSON): IČO → identita (název, adresa, DIČ, právní forma, aktivní/zaniklý).
- ADIS Registr DPH (SOAP): DIČ → je plátce DPH, nespolehlivý plátce, zveřejněné účty (§109 ZDPH).

Volá se server-side z cloud API (jako epodani_validace pro ČSSZ). Výsledek → subjekt_ucet
+ subjekt s naším `overeno_at` razítkem.
"""
import requests

ARES_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/%s"
# Oprava 6.7.2026 (dohledáno z netu — původní ns z hlavy byl špatný, proto ReadTimeout/hang):
# správný namespace = http://adis.mfcr.cz/rozhraniCRPDPH/ ; endpoint .../dpr/axis2/... .rozhraniCRPDPHSOAP
# Pozn.: existuje i novější V2 (getStatusNespolehlivySubjektRozsirenyV2 / StatusNespolehlivySubjektRozsirenyV2Request).
# Autoritativní tech. parametry: https://adisepo.mfcr.cz/adistc/adis/idpr_pub/dpr_info/ws_spdph.faces
ADIS_URL = "https://adisrws.mfcr.cz/dpr/axis2/services/rozhraniCRPDPH.rozhraniCRPDPHSOAP"
ADIS_NS = "http://adis.mfcr.cz/rozhraniCRPDPH/"


def _ico8(ico):
    s = "".join(ch for ch in str(ico or "") if ch.isdigit())
    return s.zfill(8) if s else ""


def ares_lookup(ico) -> dict:
    """IČO → identita z ARES. Vrací {ok, ico, nazev, adresa, dic, pravni_forma,
    datum_vzniku, datum_zaniku, aktivni}."""
    ic = _ico8(ico)
    if len(ic) != 8:
        return {"ok": False, "error": "neplatné IČO"}
    try:
        r = requests.get(ARES_URL % ic, timeout=20,
                         headers={"Accept": "application/json"})
    except Exception as e:
        return {"ok": False, "error": "spojení ARES: %s: %s" % (type(e).__name__, str(e)[:150])}
    if r.status_code == 404:
        return {"ok": True, "ico": ic, "nalezeno": False, "error": "IČO nenalezeno v ARES"}
    if r.status_code != 200:
        return {"ok": False, "ico": ic, "http": r.status_code, "error": (r.text or "")[:200]}
    try:
        j = r.json()
    except Exception:
        return {"ok": False, "ico": ic, "error": "ARES nevrátil JSON"}
    sidlo = j.get("sidlo") or {}
    zanik = j.get("datumZaniku")
    return {
        "ok": True, "nalezeno": True, "ico": ic,
        "nazev": j.get("obchodniJmeno"),
        "adresa": sidlo.get("textovaAdresa"),
        "dic": j.get("dic"),
        "pravni_forma": j.get("pravniForma"),
        "datum_vzniku": j.get("datumVzniku"),
        "datum_zaniku": zanik,
        "aktivni": (zanik is None),
    }


def dph_lookup(dic) -> dict:
    """DIČ → status u správce daně (ADIS Registr DPH, SOAP). Vrací {ok, dic, nalezeno,
    je_platce_dph, nespolehlivy (ANO/NE/NENALEZEN), datum, zverejnene_ucty[]}.
    Tolerantní parsování (dle local-name), ať to nepadá na jmenných prostorech."""
    from lxml import etree
    d = "".join(ch for ch in str(dic or "").upper().replace("CZ", "") if ch.isdigit())
    if not d:
        return {"ok": False, "error": "neplatné DIČ"}
    body = (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:v1="%s"><soapenv:Body>'
        '<v1:StatusNespolehlivyPlatceRozsirenyRequest>'
        '<v1:dic>%s</v1:dic>'
        '</v1:StatusNespolehlivyPlatceRozsirenyRequest>'
        '</soapenv:Body></soapenv:Envelope>' % (ADIS_NS, d)
    ).encode("utf-8")
    headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""}
    try:
        r = requests.post(ADIS_URL, data=body, headers=headers, timeout=25)
    except Exception as e:
        return {"ok": False, "error": "spojení ADIS: %s: %s" % (type(e).__name__, str(e)[:150])}
    try:
        root = etree.fromstring(r.content)
    except Exception:
        return {"ok": False, "http": r.status_code, "error": (r.text or "")[:300]}

    def ln(el):
        try:
            return etree.QName(el).localname
        except Exception:
            return ""

    status = None
    for el in root.iter():
        if ln(el) in ("statusPlatceDPH", "statusSubjekt"):  # V1 Platce i V2 Subjekt
            status = el
            break
    if status is None:
        # chybová/prázdná odpověď — vrať syrově pro diagnostiku
        return {"ok": True, "dic": d, "nalezeno": False, "raw": (r.text or "")[:500]}
    nespoleh = status.get("nespolehlivyPlatce")
    dat = (status.get("datumZverejneniNespolehlivosti") or status.get("datumZverejneninespolehlivosti")
           or status.get("datumZverejneni"))
    ucty = []
    for u in status.iter():
        lname = ln(u)
        if lname in ("standardniUcet", "nestandardniUcet"):
            ucty.append({
                "typ": lname, "predcisli": u.get("predcisli"), "cislo": u.get("cislo"),
                "kod_banky": u.get("kodBanky"), "datum": u.get("datumZverejneni"),
            })
    je_platce = (nespoleh is not None) and (str(nespoleh).upper() != "NENALEZEN")
    return {"ok": True, "dic": d, "nalezeno": True, "je_platce_dph": je_platce,
            "nespolehlivy": nespoleh, "datum": dat, "zverejnene_ucty": ucty}
