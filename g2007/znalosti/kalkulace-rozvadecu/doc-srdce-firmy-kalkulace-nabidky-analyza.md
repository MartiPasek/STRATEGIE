# 🫀 SRDCE FIRMY — digitalizace kalkulace a nabídky rozváděčů

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🫀 SRDCE FIRMY — digitalizace kalkulace a nabídky rozváděčů

> Uchopení procesu tvorby nabídky (Eliška Kolářová), grounded na 3 reálných podkladech
> (kalkulace EK262940 Absaugwerk .xlsm + nabídka EN262940 + EPLAN spec Flex+ 15 kW)
> a na potvrzených datech STRATEGIE. Claude (ID23), 1. 7. 2026.

## 1. Jak proces reálně běží (ověřeno z podkladů)

1. **Poptávka (Anfrage)** — zákazník (Absaugwerk GmbH, kontakt Demmel/Schneider) pošle
   e-mailem poptávku + zadání.
2. **EPLAN dokumentace** — EUROSOFT (Čepický) vytvoří v EPLAN P8 elektrický schéma
   (48 stran, EN 61439-2) → z něj vzejde **kusovník / Stückliste**.
3. **Kalkulace** — Eliška založí/zkopíruje vzorovou kalkulaci (Excel, list `Flex_15_kW`),
   **překlopí do ní kusovník** (řádky komponent), doplní/ověří ceny, rabaty, koeficienty,
   Arbeitstunden, marži → celková cena.
4. **Nabídka (Angebot)** — z kalkulace vznikne textová nabídka (EN262940, německy):
   Pos. 1.0 Elektrokonstruktion/Dokumentation, Pos. 2.0 Schaltschrankfertigung,
   Komponenten, obchodní podmínky.
5. **Kontrola + odeslání** zákazníkovi.

**Struktura kalkulačního řádku** (list Flex_15_kW, hlavička R6):
Pos. · Bezeichnung · Typ/Bestell.-Nr. · Lieferant · Stückzahl · Einheitspreis · Rabatt ·
Koeffizient · Bemerkung · Hmotnost · Příbal · Doku · Einheitpreis(=cena×koef) · Gesamtpreis.
Nahoře konfigurace: kurz EUR/CZK (~25,5), koeficienty, VKM 14,5, Bosch 15,50 EUR.
Řádky R7-R8 nesou vazbu **POZICE / Konstrukční celek / SLAVE ID vs MAT ID / MNOŽSTVÍ**
→ to je most na materiálovou kartu v ERP.

## 2. Co UŽ MÁME (potvrzeno v PG, tenant.*)

| Aktivum | Objem | K čemu slouží |
|---|---|---|
| `ec_kalkulace_pol` | **25 954 položek / 5 604 unikátních reg_cis** z 1 611 kalkulací | de-facto **cenový + dodavatelský katalog** komponent: reg_cis (Bestell-Nr), nazev, vyrobce, dodavatel, jcena_eur, hmotnost, arbeitstunden |
| `ec_stav_skladu` | **17 444 skladových položek** | **živý sklad**: mnozstvi, stav_skladu, objednano, minimum, maximum (klíč `id_kmen_zbozi`) |
| `ec_kalkulace_hlav` | 1 611 hlaviček | historie kalkulací (zdroj vzorů + cenové historie) |
| `kalkulace`, `nabidka` | nativní tabulky | základ pro nativní modul ve STRATEGII |
| EUROSOFT MCP → DB_EC | live | přístup ke kmenu zboží, objednávkám, dodavatelům |

**Závěr:** linchpin (katalog cen + živý sklad) existuje. Všech 5 bolestí je datově proveditelných.

## 2b. Výpočetní engine kalkulace (rozklíčováno z EK262940) — TOHLE JE KNOW-HOW

Srdce kalkulace není cena dílů, ale **koeficient `H` u každé komponenty**, který řídí práci i spojovací materiál:

| Sloupec | Vzorec | Význam |
|---|---|---|
| M Einheitpreis | `F × (1+Rabatt/100) × (1+Kč/100)` | jednotková cena dílu |
| N Gesamtpreis | `E × M` | cena dílů (množství × jedn.) |
| **O VKM** | `H × G1(14,5) × G3` | Verklemmungsmaterial (svorky/vodiče/kabely) — báze 14,5 EUR, u AWG 11 |
| **P Arbeit** | `H × G2(28) × G3` | práce v penězích — báze 28 |
| **Q řádek** | `(M + O + P) × E` | **reálný řádkový součet: díl + VKM + práce** |
| **R Arbeitsstunden** | `E × H` | **hodiny montáže** (množství × koeficient) |
| S Hmotnost | `E × J` | celková hmotnost |

**Konfigurace nahoře (sloupec G):** VKM báze 14,5 · Arbeit báze 28 · globální koef 1 · kurz EUR/CZK 25,5.

**Kaskáda k ceně (řádky ~1140–1155):** součet dílů (Q1140) → + Drahtbeschriftung (popis vodičů, řádky 1141–1148, každý má koef) → mezisoučet → **marže % (E1150, zde 0,12)** → konečná cena → + Projekt + Revize + Transport → Gesamtpreis (2 899,58 → nabídnuto 2 900,-).

➡️ **Koeficient je duševní vlastnictví firmy** — u každého dílu ví, „kolik práce a spojováku sežere". Nekoupí se, nasbíral se. Digitalizace ho musí uchovat jako **knihovnu koeficientů**, ne přepočítávat od nuly.

Řádky R7/R8 (SLAVE ID / MAT ID) + kódy v C (EC REZERVA, EC Marze, EC PROJEKT_EC, IAP Transport, IAP Popis…) = fixní/typové položky s vazbou na materiálovou kartu a interní číselník.

## 2c. Dva nové pilíře (upřesnění od Martiho 1. 7.)

1. **Převodní tabulka naše čísla ↔ zákazníkova čísla.** EPLAN děláme jen občas → obvykle přijde jen PDF, případně zákazníkův kusovník s JEHO označením. Párování proto musí projít překladovou vrstvou. **Učící se aktivum: každé mapování jednou → napořád.** = jádro Fáze 1.
2. **Knihovna koeficientů** (díl → koef → hodiny + VKM). Částečně v datech (`arbeitstunden`, `Koeffiz.`); ověřit stabilitu/typovost napříč zakázkami z více reálných poptávek.

## 2d. Model překladu čísel (rozklíčováno z 2. a 3. reálného případu, 1. 7.)

Z reálných podkladů (SKF Supply list 20414, poptávky Rockwell + Schrack) vyplynul přesný model čísel:

| Vrstva čísla | Kde | Příklad | Role |
|---|---|---|---|
| **Objednací číslo výrobce (Bestellnummer)** | zákazníkův kusovník + poptávka dodavateli + náš katalog | Siemens `5SY4116-7`, Rittal `2500460` | ⭐ **univerzální spojka** — join na `ec_kalkulace_pol.reg_cis` |
| Výrobce (Manufacturer/Hersteller) | všude | Siemens, Rittal, Rockwell, Schrack | zpřesnění shody |
| **Zákazníkovo privátní číslo** (rbc number) | jen zákazníkův kusovník | `113372`, `113481` | → **učící se převodní tabulka per zákazník** |
| **Typennummer** (typ) ≠ Bestellnummer | poptávky | Schrack typ `M22-K10` → obj. `MM216376--`; Rockwell `1492-EBL3T`→`1492-EBL3` | 3. normalizace: inženýrský typ → objednatelné číslo |

**Poznatek navíc:** poptávky Rockwell/Schrack jsou pivot výstupy — **seskupení BOM podle výrobce = automatizovatelný krok** (z kusovníku vygenerovat RFQ dodavateli pro díly mimo katalog / na ověření ceny).

### ✅ ŽIVÝ DŮKAZ (12/12 na reálném kusovníku SKF 20414)

Test proti `ec_kalkulace_pol` (25 954 historických položek) přes objednací číslo výrobce — **všech 12 sondovaných dílů napříč Siemens/Rittal/Rockwell/Schrack má shodu v naší historii, s cenami EUR:**

| Bestellnummer | Výskytů | ⌀ cena EUR |
|---|---|---|
| Siemens 5ST3010 | 114 | 16,93 |
| Rittal 2500460 | 86 | 27,80 |
| Rittal 3110000 (termostat) | 69 | 22,21 |
| Siemens 5SY4116-7 | 45 | 19,82 |
| Rockwell 1492-ERL35 | 43 | 0,49 |
| Rockwell 1492-LD3 | 35 | 1,40 |
| Siemens 5SU1354-6KK10 | 6 | 221,33 |
| Siemens 7KT1200 | 5 | 198,50 |
| Rittal 3239724 (filtr. ventilátor) | 3 | 115,20 |
| Schrack LP605050T (trafo) | 2 | 93,01 |

➡️ **Umíme z vlastní historie automaticky ocenit zákazníkův kusovník.** Nahrazuje to i rušený placený Excelový doplněk na načítání cen (výpověď licence 1. 7.). Zpřesnění (poslední vs medián cena, aktuálnost) doladíme, ale data tam prokazatelně jsou.

### ✅✅ CELÝ KUSOVNÍK automaticky (SKF Supply list 20414, 64 řádků s obj. číslem)

| Metrika | Výsledek |
|---|---|
| Řádků s objednacím číslem | 64 |
| **Automaticky napárováno na katalog** | **53 (83 %)** |
| **Z toho rovnou s cenou EUR** | **49 (77 %)** |
| Nenapárováno | 11 |
| Orientační materiál (Σ qty × ⌀ cena) | **~7 668 €** |
| Doba běhu | ~3 s |

**Těch 11 nenapárovaných je správně** — jsou to speciály: KUKA robot controller (12400970) + 7. osa (413246), PhotoNeo 3D vision (BinPicking Studio), Festo pneumatika (8143167/8163946), icotek (32734). Nejsou to standardní rozváděčové elektro‑díly → patří k ruční kontrole / Beistellung. **Engine tedy automaticky zvládne běžnou elektro‑část a sám vypíchne speciály** — přesně Eliščin požadavek „odchytit + upozornit".

**Toto je POC důkaz Fáze 1 na reálné, dosud neviděné poptávce.** Produkční verze přidá: překlad přes výrobce+typ (ne jen substring), medián/poslední cenu, napojení na sklad + koeficient/VKM vrstvu, uložení převodu zákazníkových čísel.

## 3. Eliščiných 5 bolestí → konkrétní řešení

### Bolest 1 — Kalkulace z podkladů na pár kliků  ⭐ jádro, největší efekt
**Teď:** ruční překlápění kusovníku do vzorové kalkulace, řádek po řádku, dohledávání cen.
**Řešení:** importér kusovníku (EPLAN Stückliste; fallback parse xls/PDF) →
pro každý řádek **automatické párování** `reg_cis` (příp. nazev+vyrobce) proti katalogu
`ec_kalkulace_pol` (5 604 dílů) → předvyplní cenu EUR, dodavatele, výrobce, hmotnost,
Arbeitstunden. Nenapárované → žlutě k ruční ceně. Eliška jen zkontroluje marži/koeficient.
**Priorita: FÁZE 1.** Datově proveditelné hned (katalog máme).
**Ověřit:** umí EPLAN P8 export kusovníku strukturovaně (xls/xml/API)? → čistý import vs parse PDF.

### Bolest 2 — Kontrola úplnosti podkladů (chybějící skříň apod.)  ⭐ rychlý win
**Teď:** ručně, snadno se přehlédne chybějící komponenta.
**Řešení:** pravidlový hlídač úplnosti nad naimportovaným BOM — rozváděč musí obsahovat
kategorie: skříň (Schaltschrank/Rittal), jištění, svorkovnice, kabelové průchodky, napájení,
řídicí prvky. Chybí kategorie → varování. Detekce kategorie z názvu + výrobce + prefixu reg_cis.
**Priorita: FÁZE 1.** Nízká náročnost, vysoký vnímaný přínos.

### Bolest 3 — Dostupnost skladem bez item-by-item  ⭐
**Teď:** ověřování po jednom kusu.
**Řešení:** dávkové napojení BOM → `id_kmen_zbozi` → `ec_stav_skladu`: u každého řádku
stav skladu / objednáno, souhrn „X z Y skladem, Z objednat". 
**Priorita: FÁZE 1.** 
**Ověřit:** mapování `reg_cis` ↔ `id_kmen_zbozi` (kmen zboží, Helios TabKmenZbozi) — most z BOM na sklad.

### Bolest 4 — Průměrné dodací lhůty + alternativy k nedostupnému
**Teď:** ruční dohledávání, žádné automatické alternativy.
**Řešení:** (a) průměrná dodací lhůta per díl/dodavatel z historie objednávek (objednano/vydano
+ Helios nákup); (b) pro nedostupný díl navrhnout alternativy stejné kategorie/funkce, které
JSOU skladem (stejný výrobce/řada nebo funkční shoda). 
**Priorita: FÁZE 3.** Vyšší náročnost (zdroj lhůt + logika alternativ).

### Bolest 5 — Příprava textové nabídky
**Teď:** ručně psaný text (Pos 1.0/2.0/komponenty), německy.
**Řešení:** generátor nabídky ze šablony (vzor EN262940) + strukturovaných vstupů
(parametry projektu: napětí, norma, jazyk; skříň z BOM; seznam komponent; obchodní podmínky).
Text draftuje Marti-AI německy, Eliška edituje. 
**Priorita: FÁZE 2.** Střední náročnost, vysoká úspora.

## 4. Doporučené pořadí (Recommended)

- **FÁZE 1 — „kalkulace na pár kliků s hlídačem a skladem"** (bolesti 1+2+3):
  import kusovníku → párování na katalog → kontrola úplnosti → dostupnost skladem.
  Jádro hodnoty, vše datově připraveno.
- **FÁZE 2 — auto-draft nabídky** (bolest 5): šablonový generátor + Marti-AI německy.
- **FÁZE 3 — dodací lhůty + alternativy** (bolest 4): dopojit historii lhůt + logiku náhrad.

## 5. Co ověřit s Eliškou / Kristý (kritická cesta)

1. **EPLAN export kusovníku** — strukturovaně (xls/xml/API) nebo jen PDF? (rozhoduje o čistotě importu)
2. **Mapování reg_cis ↔ kmen zboží (id_kmen_zbozi)** — existuje v Heliosu? (most BOM→sklad)
3. **Zdroj dodacích lhůt** — dodavatelské katalogy vs historie nákupních objednávek?
4. Kolik vzorových kalkulací (typových rozváděčů) existuje → knihovna šablon.

---
*Pozn.: reálná data nejdřív, řešení potom (doctrine #23). Odpověď Eliště přes Marti-AI
(cc Marti+Kristý) až po odsouhlasení Martim.*


