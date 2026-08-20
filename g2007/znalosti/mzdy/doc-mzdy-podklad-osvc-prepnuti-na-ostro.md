# Podklad fakturace OSVC: prepnuti noveho vypoctu na ostro (19.8.2026) + jak vratit zpet

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Prepnuti podkladu OSVC na ostro — 19. 8. 2026

Claude-24 (Kristy), schvalila Kristy. Uzavira Fazi 1.

## Co se stalo

Zdroj kandidata `podklad_vyplaceni_pdf_faze1` byl zkopirovan do ostreho kodu
**`podklad_vyplaceni_pdf`** (verze 9, md5 `ea32c21bc3e0c1671c12cb1abe543a62`, 35 102 znaku).
Od te chvile pocitaji novou logikou i vsichni volajici: tlacitko „Podklady OSVC" ve FLOW,
`podklad_ukol_send` (ukol na Nakup) i `podklad_osvc_zapis` (Faze 2).

## Overeni po prepnuti (`@@PYRUN podklad_vyplaceni_pdf`)

| c. | jmeno | pred (v8) | po (v9) |
|---|---|---|---|
| 105 | Havlat (pausalista) | 2 991 452 | **0** |
| 327 | Vorisek | 118 863 | 128 945 (15 r.) |
| 346 | Kilberger | 101 437 | 102 557 (5 r.) |
| 372 | Erhard | 196 503 | 159 127 (42 r.) |

Vsechny behy `_stav = OK`, `_verze = 9`.

## ROLLBACK — jak vratit puvodni vypocet

Puvodni verze 8 je ulozena byte-presne, md5 **`bb0effb599d3f4802b5fa23788dd80f6`**,
delka 19 600 znaku. Je dohledatelna ve dvou mistech:

1. `g2007.python_historie` — `SELECT zdroj FROM g2007.python_historie
   WHERE kod='podklad_vyplaceni_pdf' AND verze=8`
2. lokalne u Claude-24: `outputs/podklad_vyplaceni_pdf_v8.py`

Postup navratu: prekopirovat zdroj verze 8 zpet do `g2007.python`
(`UPDATE ... SET zdroj = (SELECT zdroj FROM g2007.python_historie WHERE kod=... AND verze=8)`)
a **overit md5 ctenim** — musi vyjit `bb0effb5…`. Zadny restart neni potreba,
`erp_registry` si nacte novou verzi sam.

## Zbyva

- `podklad_vyplaceni_pdf_faze1` je ted uz jen kopie ostreho kodu — po overeni v provozu
  smazat (DELETE je gated, jde pres schvalovaci banner).
- Faze 2 krok 3: zapis polozek objednavky do Heliosu (`TabPohybyZbozi` +
  `EC_Zakazky_PlatbyZam` + razitka `IDPolVObj`), viz `docs/navrh_osvc_faze2_zapis_zpet.md`.

