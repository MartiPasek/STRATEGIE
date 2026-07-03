# -*- coding: utf-8 -*-
"""ePodaniValidace — volání oficiálního validátoru ČSSZ (SOAP 1.1, anonymní).

Testovací prostředí:  https://t-epodani.cssz.cz/ePodaniValidace.svc
Produkční prostředí:  https://epodani.cssz.cz/ePodaniValidace.svc
SOAPAction: "ePodaniValidace"; operace ValidujPodani → VysledekKod (OK / chyby).

JMHZ: validátor ověřuje JEDEN <n1:formularOsoby> naráz → proženeme každou osobu.
PREZEC/REGZEC: obalí se celý kořenový element.

Marti / ID23, 3.7.2026 — „ověření naostro proti ČSSZ".
"""
import os, uuid, datetime, html
import requests
from lxml import etree

TEST_URL = "https://t-epodani.cssz.cz/ePodaniValidace.svc"
PROD_URL = "https://epodani.cssz.cz/ePodaniValidace.svc"
SOAP_ACTION = "ePodaniValidace"
URN = "urn:cz:isvs:cssz:schemas:ePodaniValidace:v1"

# kořen repa (…/STRATEGIE) — modul je v modules/erp/api/
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DOCS_JMHZ = os.path.join(_REPO, "docs", "jmhz")

NS = {
    "n1": "http://schemas.cssz.cz/JMHZ/podani/1.0",
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
}


def _envelope(payload_xml: str) -> str:
    rid = str(uuid.uuid4()).upper()
    cas = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    return (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:urn="%s"><soapenv:Body><urn:ValidujPodani>'
        '<urn:PozadavekId>%s</urn:PozadavekId>'
        '<urn:PozadavekCas>%s</urn:PozadavekCas>'
        '%s'
        '</urn:ValidujPodani></soapenv:Body></soapenv:Envelope>'
        % (URN, rid, cas, payload_xml)
    )


def _call(payload_xml: str, test: bool = True) -> dict:
    url = TEST_URL if test else PROD_URL
    body = _envelope(payload_xml).encode("utf-8")
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"%s"' % SOAP_ACTION,
    }
    try:
        r = requests.post(url, data=body, headers=headers, timeout=30)
    except Exception as e:
        return {"ok": False, "chyba_spojeni": "%s: %s" % (type(e).__name__, str(e)[:200])}
    out = {"http": r.status_code}
    txt = r.text or ""
    # VysledekKod
    try:
        rt = etree.fromstring(r.content)
        kod = rt.find(".//{%s}VysledekKod" % URN)
        out["VysledekKod"] = kod.text if kod is not None else None
        # posbírej případné chyby (elementy obsahující 'hyb' nebo 'Text'/'Popis')
        chyby = []
        for el in rt.iter():
            tag = etree.QName(el).localname
            if tag in ("Chyba", "chyba", "Text", "Popis", "Detail", "Kod", "faultstring") and (el.text or "").strip():
                chyby.append("%s: %s" % (tag, el.text.strip()[:300]))
        if chyby:
            out["detaily"] = chyby[:40]
    except Exception:
        out["raw"] = txt[:1500]
    out["ok"] = (out.get("VysledekKod") == "OK")
    return out


def validate_file(fname: str, test: bool = True) -> dict:
    """@@EPVAL <soubor> — soubor v docs/jmhz/. Rozpozná JMHZ vs PREZEC/REGZEC."""
    path = fname if os.path.isabs(fname) else os.path.join(DOCS_JMHZ, fname)
    if not os.path.exists(path):
        return {"ok": False, "error": "soubor nenalezen: %s" % path}
    tree = etree.parse(path)
    root = tree.getroot()
    rtag = etree.QName(root).localname
    prostredi = "test" if test else "PRODUKCE"

    # JMHZ podání → validuj každou formularOsoby zvlášť
    if rtag == "jmhz":
        osoby = root.findall(".//{%s}formularOsoby" % NS["n1"])
        vysledky = []
        for i, o in enumerate(osoby, 1):
            payload = etree.tostring(o, encoding="unicode")
            res = _call(payload, test=test)
            # identifikace osoby (ikMpsv) pro přehled
            ik = o.find(".//{http://schemas.cssz.cz/JMHZ/form/1.0}ikMpsv")
            vysledky.append({"osoba": i, "ikMpsv": (ik.text if ik is not None else None), **res})
        ok = all(v.get("ok") for v in vysledky) if vysledky else False
        return {"ok": ok, "typ": "JMHZ", "prostredi": prostredi, "pocet": len(osoby), "vysledky": vysledky}

    # PREZEC / REGZEC → obal celý kořen
    if rtag in ("PREZEC", "REGZEC"):
        payload = etree.tostring(root, encoding="unicode")
        res = _call(payload, test=test)
        return {"ok": res.get("ok"), "typ": rtag, "prostredi": prostredi, **res}

    return {"ok": False, "error": "neznámý kořen: %s" % rtag}
