# -*- coding: utf-8 -*-
"""Katalog VDA ISA 6.0.3 (TISAX) — úroveň modulů a kapitol.

Zdroj: ENX Association, VDA ISA 6.0.3 (publ. 2024-04-25, základ TISAX assessmentů
od 2024-04-01). Oficiální dotazník (přesné znění kontrol) = enx.com/isa6-en.xlsx.
Tady držíme strukturu modulů a kapitol (stabilní); přesné otázky se importují
z oficiálního Excelu. Information Security modul je mapovaný na ISO 27001 Annex A
(překryv = "jedna investice, dva výsledky").

3 moduly:
  IS = Information Security (povinný; ~ ISO 27001)
  PS = Prototype Protection (jen pokud v rozsahu — automotive prototypy)
  DP = Data Protection (pokud zpracování osobních údajů na pokyn, GDPR čl. 28)
"""
# (modul, kod, nazev, applicable_default, iso_map)
TISAX = [
    # ── Information Security (mapováno z ISO 27001) ──
    ("Information Security", "IS-1", "Zásady a organizace bezpečnosti informací", True, "ISO A.5.1–5.8"),
    ("Information Security", "IS-2", "Lidské zdroje (HR security)", True, "ISO A.6"),
    ("Information Security", "IS-3", "Fyzická bezpečnost a kontinuita", True, "ISO A.7, A.5.29/5.30"),
    ("Information Security", "IS-4", "Správa identit a přístupů (IAM)", True, "ISO A.5.15–5.18, A.8.2–8.5"),
    ("Information Security", "IS-5", "IT bezpečnost / kryptografie / provoz", True, "ISO A.8.x"),
    ("Information Security", "IS-6", "Vztahy s dodavateli", True, "ISO A.5.19–5.23"),
    ("Information Security", "IS-7", "Compliance a řízení souladu", True, "ISO A.5.31–5.37, A.8.34"),
    # ── Prototype Protection (jen automotive prototypy) ──
    ("Prototype Protection", "PS-1", "Organizační požadavky na ochranu prototypů", False, None),
    ("Prototype Protection", "PS-2", "Fyzická a environmentální bezpečnost prostor", False, None),
    ("Prototype Protection", "PS-3", "Manipulace s prototypy / vozidly / díly", False, None),
    ("Prototype Protection", "PS-4", "Zkušební jízdy, akce, foto/film", False, None),
    # ── Data Protection (GDPR čl. 28 — zpracování na pokyn) ──
    ("Data Protection", "DP-1", "Zpracování osobních údajů na pokyn (GDPR čl. 28)", True, "ISO A.5.34"),
]
