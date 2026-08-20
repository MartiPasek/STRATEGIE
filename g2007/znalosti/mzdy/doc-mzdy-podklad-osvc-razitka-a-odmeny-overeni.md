# Podklad OSVC: overeni neorazitkovane rezie a sjednoceni filtru odmen (19.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Overeni razitek rezie + filtr odmen (19. 8. 2026)

Claude-24 (Kristy). Uzavira dva body ze seznamu `doc-mzdy-podklad-osvc-co-chybi`.

## 1) Neorazitkovana rezie — PROVERENO, vse v poradku

Otazka znela, jestli rezie bez razitka `fakturace_obj_id` uz nebyla proplacena pres Centralu
(pak by ji podklad fakturoval podruhe). Rozpad podle `source_system`:

| c. zam | app (jen STRATEGIE) | centrala1 | manual_fix |
|---|---|---|---|
| 327 Vorisek | 26,06 h (21 radku) | — | — |
| 346 Kilberger | 3,40 h (3) | — | — |
| 370 Honal | 21,06 h (15) | — | — |
| 425 Nosek | 18,96 h (10) | 16,93 h (15) | 0,65 h (1) |
| 464 Vasyl | 0,51 h (1) | — | — |

- Radky `app` a `manual_fix` **nemaji v Centrale protejsek** → proplacene byt nemohly.
- Noskovych 15 radku `centrala1` (source_id 1852109…1853713, cervenec 2026) overeno primo
  v `EC_Dochazka`: **`KC_Real`, `IDPolVOBJ` i `IDPolPF` jsou u vsech prazdne** → nefakturovane.

**Zaver: razitka z Faze 0 jsou spravna, nic dorazitkovavat netreba.** Vsechna neorazitkovana
rezie je legitimni nefakturovana prace.

## 2) Filtr odmen sjednocen s Centralou

Kandidat `podklad_vyplaceni_pdf_faze1` bere odmeny nove presne jako `_Priprava`:
`id_pol_vobj IS NULL AND dat_vyplaceni IS NULL`. Odstraneny obe nase podminky navic:

- **`schvaleno`** (Kristy 19.8.2026: *"V Centrale bylo na ozdobu, ve strategii uz to nejak
  resime? Pokud ne, filtr na schvaleno tam nedavej"*). Overeno: v zrcadle `ec.pripl_srazky`
  je **0 neschvalenych radku z 2 979**; sloupec `schvaleno` pouziva v celem systemu jen
  `mzdy_stravenky_rows`; cilovy model `tenant.wage_movement` sloupec pro schvaleni NEMA.
- **`id_pol_pf`** (faktura). V Centrale je podminka zakomentovana (Swobi 5.8.2020:
  *"Dulezite je, ze uz je to v objednavce"*). Duvod potvrdila Kristy: proti opakovanemu
  zarazeni chrani `IDPolVobj` — jakmile podklad zalozi radek do objednavky, odmena ho dostane
  a pri dalsim spusteni uz se do podkladu nedostane. Faktura k tomu potreba neni.

Dopad na cisla: **zadny** (u vsech 8 aktivnich OSVC je rozdil mezi obema variantami filtru
nulovy — zadna neschvalena odmena, zadna odmena s fakturou bez objednavky).

