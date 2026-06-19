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

## Cutover 1. 7. 2026 — co MUSÍ být živé
- **Od 1.7. STRATEGIE zachytává náklady/hodiny/výnosy po zakázce dopředu** (docházka +
  work_alloc + zakázky + faktury → každý náklad má zakázku u nás). To je jediná „tvrdá"
  podmínka k 1.7. — nic se nesmí ztratit, když Helios přestane dělit.
- V Heliosu založit „velkou zakázku" a od 1.7. na ni účtovat vše.
- Most faktura→Helios + úhrada←Helios funkční (i kdyby zpočátku poloautomaticky).

## Tři pojistky (aby to nebyl skok do prázdna)
1. Zakázková analytika u nás **stojí a je důvěryhodná** dřív/současně s 1.7.
2. **Import historie nákladů do 30.6.** (spojitost roku).
3. **WIP / nedokončená výroba k závěrce 2026** doložitelná z naší analytiky (čas do konce roku).

## Harmonogram
- **do 1. 7. 2026 (11 dní):** cutover‑ready — capture nákladů po zakázce u nás + velká
  zakázka v Heliosu + most faktur/úhrad.
- **červenec–srpen (2 měsíce):** operativa + fakturace + reporting plně u nás; dozrávání
  dashboardů; paralelní kontrola, že zaúčtování sedí.
- **průběžně do závěrky 2026:** WIP/nedokončená výroba z naší analytiky.
- **1. 1. 2027:** úklid účetní osnovy/středisek v Heliosu (samostatná, administrativní dohra).

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
