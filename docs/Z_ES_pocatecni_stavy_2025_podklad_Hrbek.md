# Počáteční stavy účtů k 1. 1. 2025 — INTERSOFT (ES)

**Podklad pro:** Tomáš Hrbek (daňař + závěrkář, Martia 2000)
**Připravil:** STRATEGIE (Claude/ID23) · 27. 6. 2026 · **k odbornému posouzení a doúčtování**

> Tento dokument je **strojově spočítaný podklad**, ne hotová účetní závěrka. Mechanickou
> část (kumulace zůstatků z deníku) jsme udělali; **profesní rozhodnutí a zaúčtování
> počátečních stavů necháváme na Tomáši Hrbkovi** — transparentně, s plnými daty.

## Situace ES (zjištěno z deníku)

- ES **nepoužívá explicitní počáteční stavy** (sborník 090) — ani 2024, ani 2025 (na rozdíl
  od EUROSOFTu, který je dělá řádně přes 090). Helios u ES dopočítává zůstatky kumulativně.
- V kumulativu **před 1. 1. 2025** jsou **otevřené náklady a výnosy** (třídy 5 a 6 nikdy
  nezavřené uzávěrkou) a **chybí třída 0/1 (majetek/zásoby) i třída 4 (vlastní kapitál)**.
- Deník dvojzápisem **sedí** (MD ≈ DAL), ale pro čistý start 2025 je potřeba **uzavřít 5/6 a
  výsledek převést do kapitálu** — to je odborné rozhodnutí.

## Výpočet — kumulativní zůstatky k 1. 1. 2025 (vše před 2025)

### A) Rozvahové účty (třídy 2, 3) — PŘENÁŠÍ SE jako počáteční stav

| Účet | MD | DAL | Zůstatek (MD−DAL) | Strana |
|---|---:|---:|---:|---|
| 221001 Banka | 22 528 021,26 | 26 864 168,90 | −4 336 147,64 | DAL |
| 261004 Peníze na cestě | 1 350,00 | 0 | +1 350,00 | MD |
| 311001 Odběratelé | 42 766 131,59 | 22 343 317,26 | +20 422 814,33 | MD |
| 314100 Poskytnuté zálohy | −948,49 | 1 895,01 | −2 843,50 | DAL |
| 321001 Dodavatelé | 12 691 897,90 | 12 989 051,61 | −297 153,71 | DAL |
| 331000 Zaměstnanci | 41 408 708,00 | 41 390 695,00 | +18 013,00 | MD |
| 333000 Ost. závazky k zam. | 7 546 380,00 | 32 459 172,00 | −24 912 792,00 | DAL |
| 335003 Pohl. za zam. | 0 | 20 830,00 | −20 830,00 | DAL |
| 336100 SP | 4 334 456,00 | 10 709 126,00 | −6 374 670,00 | DAL |
| 336200 ZP | 69 053,00 | 1 796 906,00 | −1 727 853,00 | DAL |
| 336201 ZP | 4 402,00 | 80 411,00 | −76 009,00 | DAL |
| 336202 ZP | 501 712,00 | 1 483 609,00 | −981 897,00 | DAL |
| 336203 ZP | 13 276,00 | 330 572,00 | −317 296,00 | DAL |
| 336204 ZP | 32 554,00 | 894 627,00 | −862 073,00 | DAL |
| 342100 Daň ze záv. čin. | 375 000,00 | 0 | +375 000,00 | MD |
| 342200 Ost. přímé daně | 4 031 726,00 | 5 188 381,00 | −1 156 655,00 | DAL |
| 343010 DPH | 0 | 7 420 559,18 | −7 420 559,18 | DAL |
| 343310 DPH | 940 214,93 | 0 | +940 214,93 | MD |
| 379000 Jiné závazky | 23 927,00 | 262 213,00 | −238 286,00 | DAL |
| 383000 Výdaje příš. obd. | 1 750,00 | 0 | +1 750,00 | MD |
| 384000 Výnosy příš. obd. | 0 | 4 788,00 | −4 788,00 | DAL |

**Součet rozvahových:** strana MD (aktiva) **21 759 142,26**, strana DAL (pasiva) **48 729 853,03**
→ **netto −26 970 710,77** (závazky převyšují aktiva o ~27 M).

### B) Výsledkové účty (třídy 5, 6) — NEPŘENÁŠÍ SE, uzavírají se do výsledku

- **Náklady (5):** 501002, 518001/004/008/100, 521000/001/002, 524000/100, 527000/001, 548000
  → **celkem MD 62 311 495,18**
- **Výnosy (6):** 601001 (440 531,78), 602001 (34 895 464,63), 648000 (4 788,00)
  → **celkem DAL 35 340 784,41**
- **Hospodářský výsledek (kumulativně): ZTRÁTA 26 970 710,77** (= 62 311 495,18 − 35 340 784,41)

### C) Kontrola — proč to sedí
Netto rozvahových (−26 970 710,77) **přesně odpovídá** akumulovanému výsledku (ztráta 26 970 710,77).
Tj. po uzavření 5/6 a převedení ztráty do vlastního kapitálu bude počáteční rozvaha **vyrovnaná**:

> Aktiva (21 759 142,26) + akumulovaná ztráta v kapitálu (26 970 710,77, strana MD)
> = Pasiva (48 729 853,03). ✅ MD = DAL.

## Co potřebujeme od Tomáše (odborné rozhodnutí)

1. **Účet pro akumulovanou ztrátu 26 970 710,77** — navrhujeme **429 Neuhrazená ztráta minulých
   let** (příp. 431 Výsledek hospodaření ve schvalovacím řízení). Potvrď účet.
2. **Uzavření 5/6** za minulá období (přes 710 → výsledek) — formálně, ať 2025 startuje od nuly.
3. **Potvrzení rozvahových zůstatků** (tabulka A) proti ES daňovému přiznání / rozvaze 2024.
4. **Chybějící majetek/zásoby (tř. 0/1) a vlastní kapitál (tř. 4)** — je ES takto zjednodušená
   (divize bez majetku a kapitálu), nebo má být doplněno?
5. Po odsouhlasení: **zaúčtovat počáteční stavy** k 1. 1. 2025 (sborník 090, jako EUROSOFT) —
   můžeme připravit zápis dle tvého zadání.

## Pro srovnání — EUROSOFT (EC) je čistý

EC dělá počáteční stavy řádně přes **sborník 090** (80 účtů, MD = DAL = 1 723 509 115 Kč,
rozdíl 0,004 Kč zaokrouhlení) a tyto PS **už jsou v cloud zrcadle 2025**. EC hotové.

---
*Data: TabDenik DB_IS (ES) kumulativně < 1.1.2025. K dispozici plný rozpis i jednotlivé pohyby.*
