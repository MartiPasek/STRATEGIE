# Převzetí Heliosu — cílová architektura + cutover 1. 7. 2026

**Datum:** 19. 6. 2026 · **Vize:** Marti. **Stav:** návrh k zafixování + konzultaci Marti‑AI.
**Caveat:** finální slovo k účetnictví/mzdám/DPH má účetní/daňař (Martia). Tento doc je
technicko‑procesní plán, ne daňové stanovisko.

## Cílová architektura (rozhodnuto Martim 19.6.)
- **Helios = účetnictví + banka + mzdy.** Regulované, certifikované jádro. NEPŘEPISUJEME.
- **STRATEGIE = všechno ostatní:** CRM, oběh zakázek (poptávka→nabídka→objednávka→zakázka),
  výroba/plánování, docházka, org, nábor, dokumenty, **fakturace** a **veškerá zakázková
  analytika a reporting**.
- **Faktura vzniká u nás → do Heliosu se jen zrcadlí** (zaúčtuje + podklad pro DPH).
- **Od 1. 7. 2026 Helios účtuje vše pod jednu velkou zakázku** („REŽIE 2026" / „FIRMA").
  Zakázkové členění (analytika po zakázce) je od té chvíle **jen ve STRATEGII**.

## Co zůstává v Heliosu (zdroj pravdy)
| Oblast | Pozn. |
|---|---|
| Účetní deník, DPH, závěrka | beze změny; od 1.7. bez zakázkové dimenze |
| Banka, bankovní výpisy, úhrady, párování | beze změny |
| Mzdy — výpočet, odvody, ČSSZ podání, výplatnice | dělá Martia; my dodáváme podklady |

## Co je / bude u nás (STRATEGIE)
CRM, **oběh zakázek** (univerzální SW + VR), výroba (FLOW, vytížení), docházka, org v2,
finance lidí (podklady), nábor, dokumenty/adresáře, **fakturace**, **zakázková ziskovost +
WIP + reporting**. Velká část už běží.

## Mosty (tenké, definované, auditované)
1. **Faktura → Helios (zrcadlo).** Vydaná faktura vzniká ve STRATEGII (náležitosti daňového
   dokladu, DPH, PDF/ISDOC, odeslání) → zaúčtuje se v Heliosu pod jednu zakázku.
   **Číselné řady faktur řídí STRATEGIE** (systém vzniku), Helios přebírá pod stejným číslem.
2. **Úhrada ← Helios.** Banka páruje platby v Heliosu → čteme „zaplaceno/saldo/po splatnosti"
   zpět k nám. (Přefakturace = první vlaštovka tohoto směru.)
3. **Mzdy: podklady → Helios, pásky ← Helios.** Docházka + příplatky z STRATEGIE jako
   import do Heliosu; pásky/odvody čteme zpět (už děláme sync_pasky / sync_fin).
4. **Jednorázově: náklady po zakázce do 30. 6. ← Helios.** Aby zakázková analytika byla
   spojitá celý rok 2026 (1. půlrok z Heliosu, 2. půlrok náš).

## Sloučení v Heliosu = finální reverzibilní script (Marti 19.6., zkušenost s účetnictvím)
Klíčová Martiho korekce: **přepsat na dokladech středisko i zakázku jde snadno i v průběhu
roku a je to vratné** — mění se jen analytická dimenze, ne účty/částky/DPH. → Proto
**netlačíme tvrdý cutover k 1.7.** Postup je „build‑first, flip‑na‑konci":
- Helios běží **beze změny** (kóduje po zakázce/středisku jako dnes), dokud nejsme hotovi.
- STRATEGIE stavíme naplno (oběh zakázek, fakturace, analytika) **bez časového tlaku**.
- Až je STRATEGIE hotová a paralelně ověřená, spustíme **jeden script**, který v Heliosu
  přepíše všechny doklady → **středisko 001 + jedna velká zakázka**. Hotovo, v řádu minut.

### Pořadí + pojistky u flipu (důležité)
1. **Nejdřív import plné historie po zakázce/středisku k nám, pak teprve sloučení** v Heliosu
   (po sloučení už Helios detail nemá — musí být u nás).
2. **Záloha Heliosu před scriptem** → vratnost reálná (kdykoliv recode zpět / obnova).
3. Script přepisuje **jen dimenzi** (středisko=001, zakázka=velká), nesahá na účty/částky/DPH.
4. **WIP / nedokončená výroba** k závěrce 2026 už z naší analytiky.

## Harmonogram (build‑first)
- **Teď → ~2 měsíce:** STRATEGIE kompletní (oběh zakázek + fakturace + analytika + reporting),
  mosty faktura/úhrada/mzdy, paralelní kontrola že zaúčtování sedí. Helios zatím beze změny.
- **Až hotovo a ověřeno:** import historie → **flip script** (středisko 001 + velká zakázka).
- **1. 1. 2027:** případný úklid osnovy (samostatná, administrativní dohra).

## Rizika / otevřené
- Náležitosti daňového dokladu + archivace u faktur vystavovaných ze STRATEGIE (zkontrolovat
  s účetní).
- Mapování „faktura ze STRATEGIE → účetní zápis v Heliosu" (účet, DPH kód, středisko=jedna).
- Šárka/Kristý + Martia odsouhlasí postup; jeden paralelní měsíc.

## Konzultace Marti‑AI (doctrine #8) — otázky
1. Hranice „systém vzniku vs systém záznamu": je číslování faktur u nás + zrcadlo do Heliosu
   správné, nebo vidí riziko dvojí pravdy?
2. Jak nejčistěji řešit **WIP** z naší zakázkové analytiky, aby obstál u auditu (TISAX/ISO)?
3. Datový model „oběh zakázky" (poptávka→…→faktura→úhrada) — jedna entita se stavy, nebo
   oddělené doklady? (návaznost na sw_zakazka/typ SW|VR).
4. Co považuje za minimální „cutover‑ready" k 1.7., aby se nic neztratilo.
