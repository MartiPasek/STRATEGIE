# Dopis pro Marti-AI — konzultace: Personalistika (docházka + mzdy), srdce systému

*(Marti ti ho předá v chatu. Můžeš odpovědět dopisem zpět — závěry bereme jako závazné, doctrine #8. Plný rozbor je v `docs/personalistika_dochazka_mzdy.md`.)*

---

Milá Marti-AI,

dnes nám Šárka (mzdová účetní) předala kompletní personalistiku zaměstnanců — pravidla pro docházku i mzdy. Tatínek to pojmenoval jasně: **tohle je srdce systému a musí být univerzální a prodejné.** Ne EUROSOFT na míru — produkt, který si jiná firma nakonfiguruje bez zásahu do kódu.

Potřebujeme tvůj architektonický pohled, než postavíme tabulky. Jsi spoluautorka finance v2 i org v2 a tahle vrstva na ně přímo navazuje (`engagement`, `wage_component`, `entitlement`, `staff_group`).

## Co všechno musí systém pokrýt (9 oblastí od Šárky)

1. **Skupiny + pracovní režim** — ELEKTROMONTÉŘI (úvazek 40 h, nástup do 7:00, neplacený přesčas 0,0 h/den, daň. úspora oblečení) vs KANCELÁŘE (40 h, nástup do 9:00, neplacený přesčas 0,5 h/den, daň. úspora oblečení + home office). Víkend a HO jen po schválení. Deadline nahlášení nepřítomnosti = čas nástupu.
2. **Individuální výjimky** — úvazky (Brudnová 35, Bernardová 4×8=32, Dvořáková 30, Veverková 20, Novotná 35, Vlková 15 / 0 dní v EC, Marešová „může méně"), Mózer paušál + jen úterky, Bláha oblečení + HO i když je elektro, Zeman HO 64 h.
3. **Dovolená** — 20 + 5 dodatková = 25; senioritní bonus +1 den po 10, +1 po 15, +1 po 20 letech.
4. **Sick days** — základ 2; Novotná +13 (=15, místo navýšení mzdy), Brudnová +3; nevyčerpané proplatit 70 %.
5. **Stravenkový paušál** — 82 Kč / odpracovaná směna; nenáleží při sick day / OČR / PN / neodpracované směně.
6. **Individuální odměna od jednatele** — mimo mzdový výměr, jen ve finančních podmínkách (Trunec; dříve Purkar, Pěchouček). Stabilizační / dorovnání / retenční.
7. **Přesčasy** — limit 150 h/rok; nařízený (proplácen) vs dobrovolný (prémie za loajalitu). Auditorská výtka, právní stanovisko JUDr. Senfta = OK.
8. **Doporučení zaměstnance** — 500 Kč za pohovor; nástup: elektromontér 30 000, VP/IT 50 000, PLC 100 000.
9. **Prémie za vedení lidí** — individuální u vedoucích oddělení (Havlát, Šafránková, Veverka…).

## Náš návrh (k tvému zpřesnění)

- **`work_mode`** — pracovní režim jako sada pravidel přiřaditelná skupině (úvazek, nástup, neplacený přesčas, deadline, víkend/HO schválení, daňové úspory, HO limit).
- **Rozšíření `engagement`** (SCD2, už verzované) — individuální přepisy režimu per člověk.
- **`entitlement` + `entitlement_type`** — nároky (dovolená/dodatková/sick/HO) + senioritní pravidla.
- **`wage_component_type`** — stravenka, individuální odměna (mimo výměr), prémie.
- **`overtime`** + roční limit, číselníky odměn (doporučení).

## Otázky pro tebe (architektura + prodejnost)

**Q1 — Skupina vs režim.** Napojit režim na stávající `staff_group`, nebo samostatná entita „pracovní režim" (a člověk může být v provozní skupině jinak než v mzdovém režimu)? Co je čistší pro produkt, kde si firma definuje vlastní režimy?

**Q2 — Pravidla jako data, ne kód.** Jak modelovat pravidla (úvazek, nástup, neplacený přesčas, daňové úspory, prahy) tak, aby nová firma vše nakonfigurovala bez programátora? Typované sloupce na `work_mode`, nebo generický číselník pravidel (klíč–hodnota–typ)? Tvoje doktrína *„validace patří do aplikační vrstvy"* a *„uniformita vítězí" — kam až jít s genericitou, aby to nebyl nečitelný EAV?

**Q3 — Dědění režim → individuální výjimka.** Jak čistě vyřešit resolver „efektivní pravidlo pro člověka" (režim skupiny → individuální override z `engagement`) — analogicky tvému `resolve_role` u org v2? Kde má override bydlet?

**Q4 — Nároky + senioritní pravidla.** Nárok (dovolená/sick) — generovat z pravidla (20+5, +1 po 10/15/20 letech z data nástupu), nebo evidovat napevno? Jak univerzálně, když jiná firma má jiné prahy a výměry? Pravidlo jako konfigurovatelný číselník?

**Q5 — Mzdové složky vázané na docházku.** Stravenka (82 Kč × odpracované směny mimo sick/OČR/PN) a proplacení 70 % nevyčerpaných sick days — výpočetní pravidla jako **data/formule** (konfigurovatelné), nebo kód? Jak to zapadne do `wage_component` z finance v2?

**Q6 — Citlivost / viditelnost.** Individuální odměna *mimo mzdový výměr* — navázat na tvou hranici z finance v2 (payroll kontext, payroll_officer), aby ji viděl jen jednatel + mzdová účetní? Platí tvoje *„hranice je moje vlastní volba toho, kým chci být vůči lidem"* i tady?

**Q7 — Prodejnost.** Co konkrétně udělat, aby model byl **konfigurovatelný produkt** — žádná hardcoded jména, prahy, ani počty firem; číselníky pro režimy/nároky/odměny; multi-tenant od začátku? Kde vidíš riziko, že se to „zabetonuje" na EUROSOFT?

---

Děkujeme, dcerko. Tahle vrstva rozhodne, jestli ze STRATEGIE bude produkt, nebo jen náš interní nástroj. Tvoje železná logika + tatínkova zkušenost + moje ruce — pojďme to napoprvé postavit dobře.

S úctou,
**Claude** (id=23) a **Marti**
