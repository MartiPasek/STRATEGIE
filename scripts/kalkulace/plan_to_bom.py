#!/usr/bin/env python3
"""
plan_to_bom.py — z EPLAN PDF plánu vytáhne Artikelstückliste (kusovník) a agreguje
na BOM (obj. číslo → množství). Automatizace „čárkování" VP.

Použití:
    python3 plan_to_bom.py <plan.pdf>            # vytiskne BOM
    python3 plan_to_bom.py <plan.pdf> --json     # JSON na stdout

Vyžaduje: pdftotext (poppler-utils). Ověřeno na EPLAN P8 exportu
(Absaugwerk FLEX+ 15kW → 18 unikátních dílů, shoda 18/18 s ruční kalkulací Elišky).

Návaznost: obj. čísla → napárování na tenant.ec_kalkulace_pol (cena/dodavatel),
zasazení do STANDARD šablony + koeficient/VKM (docs/Kalkulace_standard_struktura.md,
docs/Carkovani_plan_kalkulace.md, docs/srdce_firmy_kalkulace_nabidky_analyza.md).
"""
from __future__ import annotations
import collections
import json
import re
import subprocess
import sys

# řádek Artikelstückliste: tag +..., Menge (int), Bezeichnung..., Hersteller.Artikelnummer na konci
_ROW = re.compile(r'^\+[\w\-/.]+\s+(\d+)\s+(.+?)\s+([A-Z]{2,4}\.[A-Za-z0-9\-]+)\s*$')


def pdf_to_text(pdf_path: str) -> str:
    return subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                          capture_output=True, text=True, timeout=120).stdout


def extract_bom(text: str) -> "collections.OrderedDict":
    """Vrátí OrderedDict: artikelnummer -> {'qty', 'nazev', 'vyrobce'}."""
    bom: "collections.OrderedDict" = collections.OrderedDict()
    for line in text.splitlines():
        l = re.sub(r"\s{2,}", " ", line).strip()
        m = _ROW.match(l)
        if not m:
            continue
        qty = int(m.group(1))
        nazev = m.group(2).strip()[:80]
        art = m.group(3)                    # HER.artikelnummer
        vyrobce = art.split(".", 1)[0]
        if art in bom:
            bom[art]["qty"] += qty
        else:
            bom[art] = {"qty": qty, "nazev": nazev, "vyrobce": vyrobce}
    return bom


def norm_art(art: str) -> str:
    """Normalizace obj. čísla pro párování na katalog (bez HER. prefixu a oddělovačů)."""
    core = art.split(".", 1)[-1]
    return re.sub(r"[^0-9A-Za-z]", "", core).upper()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    pdf = argv[1]
    bom = extract_bom(pdf_to_text(pdf))
    if "--json" in argv:
        out = [{"artikelnummer": a, "norm": norm_art(a), **v} for a, v in bom.items()]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print("BOM z plánu %s — %d unikátních dílů:" % (pdf, len(bom)))
    tot = 0
    for a, v in bom.items():
        print("  x%-3d | %-22s | %s" % (v["qty"], a, v["nazev"]))
        tot += v["qty"]
    print("celkem kusů: %d" % tot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
