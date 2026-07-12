# 🧮 Kalkulační engine v DB_EC (2014) — inventura, model, plán oživení (řada AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Marti v roce 2014 postavil v DB_EC kompletní datový
> model kalkulačního systému rozváděčů — *„kterýmu ale nikdo nikdy nevdechl reálnej život"*.
> Zadání: „Oprášíme to, zmodernizujeme a postavíme z toho engine." Tento dokument = inventura
> tabulek, rozklíčovaný model a plán. Navazuje na `Kalkulace_standard_struktura.md`,
> `Carkovani_plan_kalkulace.md`, `srdce_firmy_kalkulace_nabidky_analyza.md`.

## 🔑 Zásadní zjištění
Ten Excel STANDARD, který dělá Eliška ručně, byl **v roce 2014 navržen jako živý DB systém**.
Všechny stavební kameny jsou v DB_EC a **naplněné reálnými daty**:

| Tabulka | Řádků | Co drží |
|---|---|---|
| **EC_KalkKoeficienty** | 3676 | **K_VKM + K_ARB per díl** (IDKmenZbozi) — knihovna koeficientů (namontovací pracnost + spojovací materiál). To je „H" z Excelu. |
| **EC_KalkCena** | 2029 | **CC — ceníková cena** per díl (EUR). Náhrada za vypovězený licencovaný Excel add-in! |
| **EC_KalkRabaty** | 2466 | **Rabaty per díl** ve dvou typech: **Prodejní** (2303 dílů → prodejní/kalkulační cena) + **Nákupní** (93 dílů → NC naše nákupní). Klíč i na CisloOrg/CisloOrgDod (per firma/dodavatel). |
| **EC_KalkSkupiny** | 141 | **STANDARD skupiny** (Cislo, Nazev, Poradi) — logické skupiny v pevném pořadí (Rittal skříně, 3RV jističe, stykače…). |
| **EC_KalkSkupinyPolozky** | 1675 | **Položky STANDARDu** — ID_Skupina + IDKmenZbozi + Poradi. To je vzorová kalkulace = šablona. |
| **EC_KalkSestavySkup / …Polozky** | 2 / 199 | Sestavy = které skupiny jsou na kterém „listu" (ID_List, PoradiListu) — jak Excel má listy per sekci skříně. |
| **EC_KalkulaceHlav** | 7423 | Hlavičky kalkulací: **VKM, Arbeit, Koeffizient, MarzeProcent, CelkemHmotnost** (globální báze per kalkulace) + řešitel + řada dokladu + Objednat/Objednávám. |
| EC_KalkObjMatHlav | 7689 | Objednávky materiálu z kalkulací. |
| EC_KalkCena_ARCHIV / …Rabaty_ARCHIV / …Koeficienty_ARCHIV | | Archivy (verzování cen/rabatů/koeficientů). |

**Živost:** hlavičkovou/objednávkovou část **někdo používá dodnes** (poslední `EC_KalkulaceHlav`
= dnes 1. 7. 2026 14:37) — slouží k objednávání materiálu. Ale **výpočtový engine** (STANDARD
šablona + koeficient + cena → VKM/Arbeit/cena) **nikdy nebyl napojen na workflow** — kalkulanti
to pořád počítají v Excelu. To je ta „nevdechnutá duše".

## 🔗 Jak model odpovídá Excelu (1:1 mapování)
| Excel (Eliščin list) | DB_EC 2014 |
|---|---|
| Globální báze G1 (VKM), G2 (Arbeit), G3 (koef), marže | `EC_KalkulaceHlav.VKM / Arbeit / Koeffizient / MarzeProcent` |
| Sloupec F = Einheitspreis = **CC** | `EC_KalkCena.KalkCena` (EUR) |
| Sloupec G = **Rabatt** (per výrobce) | `EC_KalkRabaty.Rabat` (Prodejní) |
| Sloupec H = **koeficient** | `EC_KalkKoeficienty.K_VKM` = `K_ARB` |
| M = F×(1+G/100)×(1+G4/100) | prodejní cena = CC × (1 + prodejní_rabat/100) × (1+global) |
| O = VKM = H×G1×G3 | K_VKM × Hlav.VKM × Hlav.Koeffizient |
| P = Arbeit = H×G2×G3 | K_ARB × Hlav.Arbeit × Hlav.Koeffizient |
| STANDARD (skupiny + položky) | `EC_KalkSkupiny` + `EC_KalkSkupinyPolozky` |
| NC (naše nákupní) | CC × (1 + nákupní_rabat/100) |

## 🔑 K_VKM vs K_ARB (poznámka Marti 1. 7.)
Původně **jeden koeficient**; Braňo ho chtěl **rozdělit** na VKM-část a Arbeit-část (někde to dává
smysl — díl může mít jinou pracnost montáže než spotřebu spojovacího materiálu). Dnes jsou **u všech
3676 dílů K_VKM = K_ARB** (rozdělení je připravené, ale zatím se neliší). **Rozhodnutí: necháme
rozdělené** — engine počítá VKM z K_VKM a Arbeit z K_ARB nezávisle, takže až je někdo rozliší,
model to unese bez změny.

## 🎯 Coverage (kompletnost dat)
- Koeficient: **3676 dílů** ✓ (nejbohatší — jádro know-how)
- CC cena: **2029 dílů** (doplnit zbytek = náhrada add-inu)
- Prodejní rabat: **2303 dílů** · Nákupní rabat: 93 dílů (nákupní je řídký — dobudovat pro marži)
- STANDARD: **141 skupin / 1675 položek** (vzorová kalkulace)

## ➡️ Plán oživení (návrh)
1. **Zrcadlit engine tabulky do PG** (`tenant.kalk_koef`, `kalk_cena`, `kalk_rabat`, `kalk_skupina`,
   `kalk_skupina_pol`, + cross-ref na `TabKmenZbozi` = obj. číslo/název). Reuse `@@XFER` / MCP read.
2. **Postavit výpočtový engine** (server-side, deterministický): vstup = BOM (z čárkování PDF parseru
   nebo ruční) → pro každý díl: CC × prodejní rabat = cena, × koeficient → VKM + Arbeit, × množství →
   hodiny; součet + marže + hmotnost. Přesně Excel logika, ale jako služba.
3. **STANDARD-driven UI**: kalkulace z šablony (skupiny + položky, nastav množství) NEBO auto-předvyplnit
   z PDF plánu (parser). Pomocné kontakty/krytky navrhnout ke skupině (kontrola úplnosti).
4. **Ceník CC + rabaty = náhrada vypovězeného add-inu** — CC z našich dat automaticky do kalkulace.
5. **Marže/NC vrstva**: nákupní rabat → NC → marže vůči prodejní ceně (kontrola ziskovosti).

## ✅ STAV — LIVE (1. 7. 2026 večer)
Oživeno end-to-end, ověřeno:
1. **Zrcadlo** `tenant.kalk_*` (`@@KALKSYNC`): koef 3676, cena 2029, rabat 2466, STANDARD 141/1675, sestavy 2/199, kmen. Baseline `zdroj='ec2014'`.
2. **Výpočtový engine** `compute()` + `@@KALKCALC`: CC×rabat→cena, koef→VKM/Arbeit, hodiny, řádek, součet, marže. Priorita zdroje `std*` > `ec2014`. Ověřeno na Absaugwerku (VX skříň CC 803 × −14 % = 690,58 € — sedí na Eliščin Excel na cent).
3. **Refresh** `refresh_std()` + `@@KALKSTD`: staging (`tenant.kalk_std_stage`) z aktuální STANDARD kalkulace (EK262420: 479 cen, 501 rabatů, 446 koef, +154 nových dílů) → merge s tagem `std2026`. Opakovatelné pro jakoukoli aktuální kalkulaci.
4. **UI** `/kalkulace` (dlaždice ve Finance, ACL `_is_cockpit`): 🧮 Kalkulačka (kusovník → engine → řádky+součet+marže), 📋 STANDARD šablona (skupiny→položky), 🔩 Katalog dílů (hledání + CC/rabat/koef+zdroj), ℹ️ Stav. Přidávání dílů do kalkulačky klikem. Endpointy `/app/kalk/info|dily|standard|compute`.

**Soubory:** `modules/erp/api/kalkulace_engine.py` (sync+compute+refresh+dotazy), dispatch v `router.diag_sql` (`@@KALK*`) + endpointy `/app/kalk/*`, `apps/api/static/kalkulace.html`, dlaždice `finance.html`, page `main.py`.

**TODO dál:** plný refresh ze VŠECH aktuálních STANDARD kalkulací (pokrytí cen ~500→tisíce); per-zákazník sestavy (`kalk_sestava` CisloOrg) do UI; napojení na čárkování (PDF plán → BOM → kalkulačka jedním klikem); uložení kalkulace (hlavička+řádky) + marže/NC vrstva; nákupní rabat → NC → kontrola marže.

— Claude (ID23) 🧮📐
