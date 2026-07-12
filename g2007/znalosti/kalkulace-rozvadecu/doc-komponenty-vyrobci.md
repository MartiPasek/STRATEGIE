# 🧰 Komponenty & výrobci — technický přehled (řada přístupnost AI)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🧰 Komponenty & výrobci — technický přehled (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Martiho zadání: projít poslední rok KalkulacePoložek,
> zjistit prioritní výrobce komponent, které používáme, a mít o nich patřičný technický přehled.
> Data = `ec_kalkulace_pol` (poslední rok, 691 kalkulací). Katalogy = odkazy na **oficiální** zdroje
> (nereprodukuji copyright — shrnuji řady + logiku obj. čísel + klíčové parametry a odkazuji).
> Živé — plním přes `@@KBREAD`/web. **Nahrání konkrétních PDF katalogů do RAG = na pokyn Martiho.**

## Používání za poslední rok (řádky kalkulací · různých dílů · kusů · € materiálu)

| # | Výrobce | Řádků | Dílů | Kusů | € | Co dělá |
|---|---|---|---|---|---|---|
| 1 | **SIEMENS** | 6039 | 1182 | 19144 | **1 088 689** | řízení, jištění, PLC — páteř |
| 2 | **RITTAL** | 2240 | 428 | 5602 | 290 836 | skříně, přípojnice, klima |
| 3 | **PHOENIX CONTACT** | 1275 | 291 | 11826 | 38 721 | svorky, konektory, značení |
| 4 | **ROCKWELL** (Allen-Bradley) | 765 | 140 | 5453 | 17 155 | svorky, tlačítka, PLC |
| 5 | (EC — interní) | 690 | 18 | 1347 | 21 767 | vlastní díly |
| 6 | **HARTING** | 581 | 113 | 5140 | 18 099 | průmyslové konektory Han |
| 7 | **EATON** (Moeller) | 551 | 198 | 1718 | 40 594 | motor. jištění, stykače |
| 8 | **LAPP KABEL** | 425 | 169 | 4374 | 12 400 | kabely, vývodky |
| 9 | **FINDER** | 361 | 46 | 2140 | 13 816 | relé, patice, zdroje |
| 10 | **WAGO** | 357 | 59 | 2875 | 7 352 | svorky, I/O |
| 11 | **SCHNEIDER** | 341 | 208 | 842 | 30 152 | skříně Spacial, Modicon |
| 12 | (Beistellung — dodá zákazník) | 320 | 75 | 602 | 0 | — |
| 13 | **WEIDMÜLLER** | 221 | 66 | 2838 | 9 539 | svorky, konektory, zdroje |
| 14 | **MURRELEKTRONIK** | 179 | 81 | 397 | 21 917 | MICO, zdroje, I/O, rozhraní |
| 15 | **OEZ** | 151 | 18 | 902 | 2 185 | jističe Minia, pojistky (CZ, dnes Siemens) |
| 16 | **SCHRACK** (TE) | 143 | 57 | 251 | 8 410 | relé, jističe, patice |
| 17 | **B&R** | 131 | 131 | 1445 | 0 | PLC X20, servo (dnes ABB) |
| 18 | **OMRON** | 130 | 19 | 211 | 7 409 | relé, PLC, timery, čidla |
| 19 | **WÖHNER** | 108 | 56 | 304 | 4 933 | přípojnicové systémy |
| 20 | **ABB** | 108 | 11 | 113 | 3 264 | jističe, stykače, zdroje |

## 1. SIEMENS ⭐ páteř (obj. číslo bez mezer, prefix = řada)

Řady, které reálně používáme (dle prefixu obj. čísla):
- **SIRIUS** — průmyslové spínání/jištění: `3RV2` motorové spouštěče (jistič, do 55/45 kW/400 V),
  `3RT2` stykače, `3RH2` pomocné stykače, `3TG1` mini stykače, `3RA2` load feeder = 3RV2+3RT2,
  `3RQ`/`3RS` relé. Ovládací a signální: **`3SU1` SIRIUS ACT** (tlačítka, signálky 22 mm — u nás
  nejvíc, 152 dílů). Vypínače: `3LD` hlavní/nouzové.
- **SENTRON** — nn jištění/rozvod: `5SY`/`5SL` modulární jističe (MCB), `5ST3` přípojnice/pomocné
  ke jističům, `5SU` proudové chrániče, `3VA`/`3NP` výkonové jističe/odpínače, `7KM`/`7KT` PAC měřiče.
- **SIMATIC** (TIA) — automatizace: `6ES7` S7-1500/1200/ET200 (CPU + I/O moduly, SM331 analog),
  `6ED1` **LOGO!** (logika + TD displej), `6GK1`/`6GK5` SIMATIC NET (Profinet/Ethernet, RJ45),
  `6XV1` sběrnicové kabely (Profinet/Profibus), `6EP` **SITOP** zdroje.
- Svorky/signalizace: `8WH`/`8WA` řadové svorky, `8WD` signalizační sloupy, `8US1`/`8PQ` přípojnice.
- 📖 Katalog **IC 10** (SIRIUS), **LV 10** (SENTRON), **ST 70** (SIMATIC) — [Industrial Controls
  catalog](https://www.siemens.com/en-us/content/industrial-controls-catalog/) · [SIRIUS](https://www.siemens.com/en-us/products/sirius/)
  · Industry Mall + support.industry.siemens.com (datasheety dle obj. čísla).

## 2. RITTAL — skříně, přípojnice, klima (obj. číslo 7místné)

- **Skříně:** `VX25` (nástěnné/stojanové oceloplechové, modul 25 mm — vlajková řada), `AX`/`KX`
  kompaktní, `TS8` (starší), `EB` montážní rámy. Příslušenství: montážní desky, dveře, panty
  (`8618330`), transportní oka (`4568000`), sokly VX.
- **Přípojnicový systém RiLine / Ri4Power:** 185 mm rozteč do **2100 A**, dle **IEC 61439**;
  držáky přípojnic (`9340000`), OM-adaptéry (`3431030`, 65 A), měděné přípojnice.
- **Klima:** chladicí jednotky Blue e/Blue e+, ventilátory s filtrem (`3239724`), termostaty
  (`3110000`), topení, výměníky. Osvětlení/servis: LED (`2500220`), zásuvky, dveřní spínače (`2500460`).
- 📖 [VX25 Ri4Power Technical System Catalogue](https://www.rittal.com/com_en/vx25/) · System
  Catalogue 36 (Power distribution) · Rittal ePOCKET/eCat + „Rittal Configuration System" (RiCS).

## 3. PHOENIX CONTACT — svorky, konektory, značení (obj. číslo číselné, série dle názvu)

- **Řadové svorky CLIPLINE complete:** připojení **PT** (Push-in — u nás nejvíc, `3209510` průchozí
  0,14–…, `3210567` dvoupatrová), **UT** (šroub), **ST** (pružina), **QT** (QUICKON). Nožové,
  oddělovací, můstky, koncové desky.
- **Značení:** `WMTB`/UC/UCT popisové štítky (`0830525`), tiskárny THERMOMARK.
- **Konektory:** HEAVYCON (těžké), M12/M8 (senzory), COMBICON (pluggable svorky do DPS).
- **Napájení/ochrana:** QUINT/UNO/STEP zdroje, TRABTECH přepěťové ochrany, relé PLC-INTERFACE.
- 📖 [Terminal blocks](https://www.phoenixcontact.com/en-us/products/terminal-blocks) · CLIPLINE
  complete interaktivní katalog · datasheety dle obj. čísla na phoenixcontact.com.

## 4. EATON (Moeller) — motorové jištění, stykače (řada xStart)

- **Motorové spouštěče (MPCB):** `PKZM01` (do 25 A), `PKZM0` (do 32 A), `PKZM4` (do 65 A), `PKE`
  elektronické. Kombinace se stykači **`DILM`** (AC-3), softstartéry `DS7`. Pomocné kontakty `NHI`,
  otočné rukojeti (uzamykatelné `030851`), přípojnicové adaptéry 45 mm.
- Dále: jističe `PL`/`FAZ` (MCB), chrániče `PF`, relé `ETR`/`EASY` (easyE4 mini-PLC), tlačítka `M22`,
  zdroje. 📖 [PKZ MPCB](https://www.eaton.com/gb/en-gb/catalog/industrial-control--drives--automation---sensors/pkz-motor-protective-circuit-breaker.html)
  · [Switching & protecting motors – product range catalog (PDF)](https://ecat.eaton.com/flip-cat/MOTCONT1_EN/) · ecat.eaton.com.

## 5. SCHNEIDER ELECTRIC — skříně Spacial, Modicon

- **Rozváděčové skříně Spacial:** prefix **`NSY`** — `NSYSM`/`S3D` (oceloplechové), `NSYCRN`
  (kompaktní), + příslušenství (krytky `NSYCSP`, klecové matice `NSYCNFM8`, montážní desky).
- **PLC Modicon:** `BMX` = **M340** (CPU + I/O + svorkovnice `BMXFTB`), `BME` = M580, `TM2xx/TM3`
  Machine. Dále **TeSys** (stykače `LC1D`, motor. jističe `GV2/GV3`), **Acti9** (MCB `iC60`),
  **PowerLogic** měření, **Harmony** tlačítka (XB4/XB5), **Phaseo** zdroje.
- 📖 se.com (Product catalogue + „mySchneider" + Spacial/Modicon reference guides), datasheety dle ref.

## 6. Další výrobci (technický profil)

- **ROCKWELL / Allen-Bradley:** svorky `1492`, tlačítka/signálky `800F`/`800FP` (22 mm), PLC
  ControlLogix `1756` / CompactLogix `5069`/`5370` / Micro800, relé `700`. → hodně u zákazníků s AB.
- **HARTING:** těžké průmyslové konektory **Han** (Han-Modular, Han A/B/D/E, Han-Eco), pouzdra,
  RJ Industrial / ix Industrial (data). Obj. čísla `09…`.
- **LAPP:** kabely **ÖLFLEX** (ovládací), **UNITRONIC** (data), **ETHERLINE**, vývodky **SKINTOP**,
  značení **FLEXIMARK**.
- **FINDER:** relé série `40`/`55`/`62`/`66`, patice `95`/`93`/`96`, časová relé `80`/`85`, zdroje
  `78`, převodníky `4C`/`7S` (přepěťová ochrana kontaktů).
- **WAGO:** řadové svorky **TOPJOB S** (`2xxx`, push-in), svorky **221/222** (spojovací), I/O systém
  `750`/`750-XTR`, zdroje `787`, relé/opto moduly.
- **WEIDMÜLLER:** svorky **Klippon** (série `A`/`W`, `Z` push-in), konektory OMNIMATE, zdroje
  PROtop/PROeco, značení MultiCard.
- **MURRELEKTRONIK:** **MICO** (elektronické jištění 24 V), zdroje **Emparro**, odrušovací moduly,
  I/O **MVK/Impact67/Cube67** (fieldbus), rozhraní **Modlink**, panelové **MSDD**.
- **SCHRACK** (TE Connectivity): relé (série `RT`/`PT`/`MT`), jističe `BM`/`BO`, patice, zásuvky
  rozváděčové `BZ`, přepěťové ochrany.
- **OMRON:** relé `G2R`/`MY`/`LY`, patice `PYF`, časová relé `H3`, čítače/měřiče `H7`, PLC `CP1`/`NX`,
  zdroje `S8`, safety relé `G9S`.
- **WÖHNER:** přípojnicové systémy **60Classic / CrossBoard / MOTUS**, pojistkové odpínače,
  adaptéry na přípojnice.
- **ABB:** MCB `S200`, chrániče, stykače `AF`, motor. jističe `MS`, zdroje `CP-E`, relé `CR`.
- **B&R** (ABB): řídicí systém **X20** (modulární PLC/I/O), Power Panel HMI, servo **ACOPOS**. → u
  zákazníků s B&R architekturou.
- **OEZ** (dnes Siemens): jističe **Minia** (`LTN`/`LPN`), pojistkové odpínače **Varius**, svodiče.

## Postřehy pro digitalizaci (návaznost na SRDCE FIRMY)
- **Obj. číslo výrobce = univerzální klíč** (potvrzeno u kalkulace: 83 % kusovníku napárováno na náš
  katalog). Technický přehled řad umožní: (1) rozpoznat z čísla řadu/typ dílu, (2) navrhnout
  alternativu (stejná funkce, jiný výrobce — Siemens 5SY ↔ ABB S200 ↔ Eaton PL), (3) dotáhnout
  datasheet automaticky (odkaz na support portál výrobce dle obj. čísla).
- **Alternativy = konkrétní byznys hodnota:** při nedostupnosti / ceně navrhnout ekvivalent
  (svorky Phoenix PT ↔ WAGO TOPJOB S ↔ Weidmüller; stykače Siemens 3RT ↔ Eaton DILM ↔ ABB AF).
- **TODO:** stáhnout konkrétní datasheety top dílů (na pokyn), doplnit dodací lhůty per výrobce
  (z historie objednávek), a napojit na kontrolu dostupnosti (`ec_stav_skladu`).

— Claude (ID23) 🧰🔌📚

Sources (oficiální katalogy): Siemens Industrial Controls / SIRIUS · Rittal VX25 Ri4Power · Phoenix
Contact Terminal blocks / CLIPLINE · Eaton PKZ / Switching & protecting motors · Schneider se.com.


