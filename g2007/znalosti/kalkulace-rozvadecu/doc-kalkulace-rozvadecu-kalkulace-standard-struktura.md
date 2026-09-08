# 📐 Kalkulace — struktura STANDARDu, skládačka skříní a tvorba obj. čísel (řada AI)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 📐 Kalkulace — struktura STANDARDu, skládačka skříní a tvorba obj. čísel (řada AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Martiho zadání: získat dobrý přehled o Excel kalkulaci —
> vychází z **STANDARDu** (vzorová kalkulace), položky řazené sestupně (Rittal skříně → skupiny dílů
> specifické napětím/výkonem/kontakty…), pomocné kontakty vždy u své skupiny; pochopit **skládačku**
> skříní (bočnice zvlášť, skříně k sobě) a **tvorbu objednacích čísel** (Siemens 6ES7 apod.).
> Čteno z reálné kalkulace EK262940 (Absaugwerk, list Flex_15_kW). Doplňuje `srdce_firmy_kalkulace…`.

## 1. Co je STANDARD (vzorová kalkulace)
Kalkulace = kopie **vzorové kalkulace = „STANDARD"**: obsahuje **VŠECHNY standardní položky**
firmy v pevném logickém pořadí (stovky řádků). Kalkulant jen **nastaví množství (Stückzahl)** u
položek, které daná zakázka potřebuje; zbytek zůstane 0. Koeficient → hodiny + VKM (viz SRDCE FIRMY).
Řazení jde **shora dolů** od skříní přes mechaniku/klima k elektrickým skupinám.

## 2. Řazení a seskupení položek (jak jdou za sebou)

**A. Rittal skříně (nosná konstrukce) — sestupně dle rozměrů**
- `VX Schaltschrank` B×H×T (např. 800×2000×600), řazené podle šířky/výšky/hloubky sestupně.
- `VX Seitenwand` (bočnice) — **samostatné položky** (viz §3 skládačka).
- `VX Sockel` (sokl) — přední/zadní (v/h) a boční (s), výšky 100/200 mm.

**B. Příslušenství skříně**
- Klemmprofil, průchodky (`Kabelverschraubungen` plast/metal), rychlomontáž (SONAPky).
- **Transport:** `Transportösen`, `Kombiwinkel`.
- **Spojení skříní k sobě (baying):** `Anreihverbinder` (vnější), `Anreihlasche`/`Anreihblock` (vnitřní), `Anreihkit` VX↔TS8.
- **Osvětlení:** LED 2P/3P (100‑240V), napájecí + propojovací kabely (oranžová/žlutá), **dveřní spínače (`Türschalter`)** — s/bez kabelu, barvy, Rittal/Richter/Siemens `3SE`. → **pomocný díl (spínač) je u své skupiny (osvětlení).**
- Panty (`Scharnier`), zámky/kliky (`Komfortgriff`, Ergoform), kapsy na schéma (`Schaltplantasche`) dle šířky dveří.
- Svorkové skříňky (`Klemmkasten`) dle rozměru; kompaktní skříně **AE** (`Schrank` B×H×T) dle rozměru; E‑boxy (EB); pulty (`TP Pult`); podlahové plechy; **barva (`Farbe`)**.
- **Zásuvky (`Steckdose`)** dle země: DE/FR/CZ/UK/IT/USA (Legrand, Murr **MSDD**/MSVD NEMA/GFCI), datové zásuvky Profibus SUB‑D9 / Profinet RJ45 (Murr), USB.

**C. Napájení a rozvod**
- Potenciálové bloky (Erico UDJ), paušál Cu vedení pro velké motory.
- **Přípojnicový systém (`Schienensystem`)** Rittal 250/400/630/800/1600 A (dle proudu), **adaptéry** `Adapter S0/S2/S3` a pod jističe `NZM` (dle velikosti/proudu), Wöhner.

**D. Klimatizace**
- Termostaty (`Schaltschrankthermostat` — červený topení 1NC / modrý ventilátor 1NO).
- **Ventilátory (`Lüfter`)** dle průtoku (55/105/160/230/550/700 m³/h) + **výstupní filtry** (`Austrittfilter`) — filtr hned u ventilátoru.
- **Chladicí jednotky (`Kühlgerät`)** dle výkonu (500 W–5800 W), boční/střešní, 230V vs 3×400V s motorovou ochranou.

**E. Hlavní vypínače / odpínače / jističe (elektrické jádro)**
- Nouzové/hlavní: Schneider `Vario`, **Siemens `3LD`** (odpínač/Not‑Aus) dle proudu — **každý hned následuje svou `Klemmenabdeckung` (`3LD92xx`) dle proudu.**
- Eaton `P3`/Kraus&Naimer hlavní vypínače; Eaton **`PN1/PN2/PN3/N4`** odpínače dle proudu (63…1250 A); Eaton **`NZM`** výkonové jističe (`NZMB1/2/3/4`) dle proudu + jejich příslušenství: dveřní rukojeť (`XTVDVR`), prodlužovací osa (`XV6`), tunelová svorka (`XKA`), krytka (`XKSA`), IP2X (`XIPK`), **podpěťová spoušť (`XU208‑240AC`/`XU24DC`)**, výstražný štítek (`ZFS`), **pomocné kontakty (`Hilfsschalter M22‑K10 1NO / M22‑K01 1NC`)** — vždy u své skupiny.

**F. Pojistky**
- Wöhner válcové D0/E18/E27/E33 (pojistkové spodky + pojistky dle proudu, gG/Neozed/Diazed), Rittal/Wöhner NH odpínače (`Trenner NH00/NH1/NH2/NH3` dle velikosti a proudu) + mikrospínač signalizace, OEZ NH pojistky `PNA` (dle velikosti 000/00/1/2/3 a proudu 10…630 A, gG).

**G. Měření**
- Proudové transformátory (MBS `ASK` — převod xxx/1A nebo /5A, VA, třída), analyzátory/měřiče (Weigel `EQ72/EQ96` ampérmetry/voltmetry dle rozsahu), převodníky 4‑20 mA.

**H. Motorová ochrana + stykače (SIRIUS) — dle proudu, velikosti a připojení**
- **Motorové jističe Siemens `3RV`** — řazené **sestupně dle proudového rozsahu**: velikost **S00 = `3RV2011`** (0,11‑12,5 A), **S0 = `3RV2021`** (10‑40 A). Každý rozsah = svůj kód (viz §4).
- Pomocné kontakty `3RV2901` (HK 1NO/1NC/2NO), spojovací bloky MS‑stykač `3RA29xx`/`3RA19xx` (dle velikosti a AC/DC).
- (dále) **stykače `3RT2`** dle výkonu + **napětí cívky** (v koncovce čísla) + pomocné kontakty `3RH2`; jističe `5SY` dle **charakteristiky B/C/D**; svorky **šroubové vs pružinové**.

## 3. 🧩 Skládačka skříně (ta „hádanka") — jak se to staví
Rozvaděč = **sestava (Anreihschrank)** složená z více VX skříní vedle sebe:
- **Bočnice se objednávají ZVLÁŠŤ**, protože **sousední skříně sdílí vnitřní stěnu** → u řady **N**
  skříní stačí **2 krajní bočnice** (ne 2×N). VX skříň se proto v sestavě bere **bez bočnic** a
  `VX Seitenwand` je samostatná položka (1 VE = 2 ks).
- **Skříně k sobě = baying:** `Anreihverbinder` (vnější spojka), `Anreihlasche`/`Anreihblock`
  (vnitřní), příp. `Anreihkit` na přechod VX25 ↔ TS8.
- **Sokl:** přední+zadní (v/h) dle šířky + boční (s) dle hloubky, výška 100/200 mm.
- **Transport:** `Transportösen` (oka) + `Kombiwinkel`.
- ➡️ **Konfigurátor:** z cílových rozměrů sestavy → počet skříní + jejich šířky/výšky/hloubky +
  **2 bočnice na kraj** + baying spojky mezi nimi + sokl (obvod) + transport. To je „skládačka".

## 4. 🔢 Tvorba objednacích čísel (kódují variantu — klíč pro digitalizaci)
Objednací číslo výrobce **není náhodné — kóduje typ + parametry**. Kalkulant vybírá variantu
změnou koncovky/středu čísla:
- **Siemens 3RV motorový jistič:** `3RV20` **[11=S00 / 21=S0]** `-` **[proudový rozsah]** **[připojení]**.
  Příklad: `3RV2011‑0FA10` = S00, rozsah 3,5‑5 A, **`10` = šroubové připojení**; `3RV2011‑0FA20` =
  **`20` = pružinové (Federzuganschluss)**. Proud roste kódem `0AA`(0,11‑0,16)→…→`1KA`(9‑12,5 A).
- **Siemens 3RT2 stykač:** koncovka kóduje **napětí ovládací cívky** (24V DC / 230V AC / …) — proto
  se stykače v kalkulaci berou „dle řídicího napětí cívky" + k nim pomocné kontakty `3RH2`.
- **Siemens 5SY MCB:** `5SY` **[charakteristika a póly]** `-` **[proud]** → char. **B/C/D** + jm. proud.
- **Siemens 6ES7 (SIMATIC):** kóduje **řadu S7** (`3xx` = S7‑300/ET200, `5xx` = S7‑1500) + **typ modulu**
  (CPU / DI / DO / AI / AO / komunikace) + variantu (rozsah, kanály). Skládá se dle automatizační
  architektury; přesná koncovka = přesný modul (např. SM331 8×AI).
- **Siemens 3LD odpínač** + krytka `3LD92xx` dle proudu; **Eaton NZM** `NZMB[1‑4]‑A[proud]` +
  příslušenství s `-X…`; **OEZ PNA** pojistka dle NH velikosti + proudu + gG.
- **Princip:** z požadavku (funkce + proud/výkon + napětí cívky + šroub/pružina + charakteristika)
  jde **složit přesné objednací číslo** — a naopak z čísla **rozpoznat parametry**. To je jádro
  auto‑kalkulace (SRDCE FIRMY) i kontroly úplnosti.

## 5. Postřehy pro digitalizaci
- **Vzorová kalkulace = strojově čitelná šablona:** skupiny + varianty jsou fixní → generátor může
  z EPLAN kusovníku napárovat do skupin a předvyplnit množství; pomocné kontakty/krytky navrhnout
  automaticky ke své skupině (to, co dnes hlídá kalkulant zpaměti).
- **Konfigurátor skříně:** z rozměrů poskládat skládačku (skříně + 2 bočnice + baying + sokl + transport).
- **Kodér/dekodér obj. čísel:** knihovna pravidel per výrobce (3RV/3RT2/5SY/6ES7/NZM…) → z parametrů
  číslo a zpět; napojení na `Komponenty_vyrobci.md` + datasheety (`@@DS`).

— Claude (ID23) 📐🧩🔢


