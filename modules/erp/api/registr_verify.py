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
