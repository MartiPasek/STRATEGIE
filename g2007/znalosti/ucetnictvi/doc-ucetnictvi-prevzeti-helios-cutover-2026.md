# Převzetí Heliosu — cílová architektura + cutover 1. 7. 2026

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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

## Zásoby — Způsob B (Marti 19.6.)
Druhá velká úspora: **Způsob B zásob** — nákupy rovnou do spotřeby, **žádné účtování
příjemek/výdejek** přes skladové účty (~56 % řádků deníku). Protože doklady jdou přepsat
zpětně, na konci roku stačí **vyřadit/zneaktivnit účty pro příjemky/výdejky** → celý rok
je v Způsobu B. Konzistentní s „flip‑na‑konci".
- **Co Způsob B nesundá:** k závěrce vyžaduje **ocenění zásob (inventura) k 31.12.** —
  konečný stav skladu se stanoví a zaúčtuje jednorázově. **Pozn. (Marti): fyzickou inventuru
  na konci roku děláme tak jako tak** → Způsob B tedy nestojí nic navíc, konečný stav dá
  existující inventura. STRATEGIE k ní jen dodá skladovou evidenci/podklad (a WIP).

**Jednotný vzorec:** Helios = tenká finanční kniha (bez zakázek/středisek, Způsob B);
STRATEGIE = veškerá operativní a analytická pravda (zakázky, náklady, WIP, sklad) →
Heliosu dodáváme jen **závěrkové figury (WIP + konečný stav zásob)**.

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

## ZÁVĚRY KONZULTACE MARTI‑AI (19. 6. 2026) — ZÁVAZNÉ
Marti‑AI přijala architekturu spoluautorsky. Závazné body:

**Faktura → Helios (systém vzniku vs záznamu):**
- Faktura má `helios_status ∈ {pending, mirrored, rejected}` + `helios_doc_id`. Dokud
  není `mirrored`, je neuzavřená — **neposílat zákazníkovi**.
- **Push, ne sync** (jednosměrný tok; zpět čteme JEN stav úhrady → dvojí pravda nevzniká).
- Číslo řady přiděluje **výhradně STRATEGIE**, Helios přebírá jako string/cizí klíč, nesahá
  na vlastní řadu. **Ověřit s Martií, že Helios neodmítne formát čísla.**
- **Denní cross-check** Σ vydaných faktur STRATEGIE vs Helios → diff ≠ 0 = alert (levná pojistka).
- **Přímá editace faktury v Heliosu** = procesní riziko → blokovat / označit „jen Helios oprava"
  + zpětně synchronizovat. Probrat s Martií jako pravidlo.

**Datový model = řetězené doklady, ne monolit:**
`poptávka → nabídka → objednávka → ZAKÁZKA (pivot) → faktura → úhrada(←Helios)`. Každý doklad
vlastní tabulka + `parent_id`/`zakazka_id`, vlastní lifecycle/ACL/archivace. **Zakázka =
jedna tabulka `sw_zakazka` s `typ IN('SW','VR')`** (už máme). VR si přidá `production_order`
mezi objednávku a zakázku bez zásahu do zbytku.

**WIP — auditovatelně (TISAX/ISO):**
- `wip_snapshot` **append-only**, immutable po uzavření závěrky (žádný UPDATE/DELETE).
- **Metoda (rozhodnuto Marti 19.6.): NV = přímé náklady + poměrné rozpuštění režie na
  rozpracované zakázky.** Každá rozpracovaná zakázka = přímé náklady (materiál + práce +
  přímé subdodávky) + alikvotní podíl režie období.
  - **Klíč rozpuštění režie:** poměrem přímých nákladů zakázky (default/doporučeno):
    `režie_na_zakázku = režie_období × (přímé_náklady_zakázky ÷ Σ přímých nákladů rozprac.)`.
    Alternativa = poměrem hodin. **Klíč fixní + zdokumentovaný** (auditovatelnost, ne ad‑hoc).
  - Stav rozpracovanosti (která zakázka je k datu „rozpracovaná") schvaluje vedoucí
    (`approved_by/at`).
- Helios dostane **jedno číslo** (WIP celkem k 31.12.); detail po zakázkách žije u nás, auditor
  čte přímo ze STRATEGIE. Metodika = knowledge_entry. Čtyři oči před zaúčtováním.

**Flip — definition of done (nepodkročitelné):**
1. Import plné historie (zakázka+středisko+částky+typ) → **křížový součet STRATEGIE = Helios**.
2. Záloha Heliosu **+ doložená RESTORE na test prostředí** (ne jen backup!).
3. Script proběhl **na kopii (staging)** + Martia zkontrolovala DPH sestavy a saldokonto.
4. **Paralelní měsíc** — korunová shoda zaúčtování × faktury STRATEGIE.
5. **Zdokumentovaný rollback** (kdo/jak/do kdy + co s fakturami, co přišly mezitím) — nejčastěji
   se přeskočí → flip je pak nevratný de facto.

**Mzdová data (ACL/retence):** `visibility_scope='payroll_only'`, samostatné, composer
neinjektuje. Podklady → Helios **strukturovaným importem (CSV/XML), ne přímé API** (Martia
kontroluje). Pásky vidí jen zaměstnanec + Martia + jednatel. Retence 10 let, append-only.

**Pořadí (závazné):** 1) most faktura→Helios (PRVNÍ, ruční test 1 faktury celou cestou až po
DPH s Martií) → 2) most úhrada←Helios → 3) oběh zakázky → 4) analytika/WIP → 5) import historie
+ flip script (ÚPLNĚ POSLEDNÍ). Kde se to láme: podcenění mostu faktura/Helios (jiné požadavky
na strukturu DPH dokladu) → proto první ruční test, ne rovnou automatizace.

**Zásoby (Způsob B):** skladová evidence operativně u nás (kdo/co/na jakou zakázku), ne účetně.
31.12. inventura + ocenění **FIFO/průměr (zvolit jednu, zdokumentovat)** → hodnota → Helios
jednorázově (MD 112/DAL 501). `closing_snapshot` (WIP+zásoby) schválený jednatelem+účetní, PDF archiv.

**Největší rizika dle Marti‑AI:** (1) přímá editace faktur v Heliosu, (2) vynechaný restore-test
před flipem, (3) **náležitosti daňového dokladu + DPH mapování** — Martia musí dát **písemné „ano"
před prvním ostrým odesláním faktury zákazníkovi**.

---

## Konzultace Marti‑AI (doctrine #8) — otázky (zodpovězeno výše)
1. Hranice „systém vzniku vs systém záznamu": je číslování faktur u nás + zrcadlo do Heliosu
   správné, nebo vidí riziko dvojí pravdy?
2. Jak nejčistěji řešit **WIP** z naší zakázkové analytiky, aby obstál u auditu (TISAX/ISO)?
3. Datový model „oběh zakázky" (poptávka→…→faktura→úhrada) — jedna entita se stavy, nebo
   oddělené doklady? (návaznost na sw_zakazka/typ SW|VR).
4. Co považuje za minimální „cutover‑ready" k 1.7., aby se nic neztratilo.


