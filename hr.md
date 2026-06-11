# HR / Mzdy / Docházka — pracovní kontext

> Zakládá Claude (id=23), 11. 6. 2026 večer, na žádost Martiho:
> „Založ hr.md a podrobně to popiš, ať v pondělí, až to budeme ladit,
> nevycházíme opět z nuly."
>
> **Účel:** kompletní stav analýzy mezd + docházky, aby pondělní ladění
> s Kristý a Peťou navázalo bez ztráty kontextu. Čti shora dolů; sekce
> „OTEVŘENÉ OTÁZKY NA PONDĚLÍ" a „CO DÁL" jsou nejdůležitější.

---

## 1. Tři systémy, které se musí srovnat

| Systém | Co je | Role |
|---|---|---|
| **STRATEGIE** | náš nový systém (PostgreSQL `data_db`, tenant 2) | cílový — sem vše importujeme a počítáme |
| **Centrála docházka (EC)** | MSSQL `DB_EC`, čteno přes EUROSOFT MCP / SQL bridge | **zdroj pravdy pro docházku** (odpracováno, absence, konto přesčasů) |
| **Helios** | mzdový systém (DB_EC + DB_IS, cross-db) | **zdroj pravdy pro vyplacené mzdy** (skutečně proplaceno) |

Cíl: STRATEGIE má sedět s Heliosem **na haléř**. Není to odhad, je to
deterministická matematika (Martiho slova) — pokud máme všechny vstupy.

---

## 2. Analýza mezd květen 2026 — výsledek

### 2a. Hlavní zjištění (mzdové složky)
Srovnání našich plánovaných složek (`tenant.wage_component`, = EC podmínky
`EC_FinZamPodminky`) vs Helios skutečnost (květen 2026). Po **krácení
odpracovanými hodinami** delta základu spadla z **+143 965 Kč na −3 015 Kč**
na 50 lidí → **naše data sedí**, plošný rozdíl byl jen krácení.

Helios platí **hodinovkou**: `plán × odpracováno/fond`. Náhrady
(dovolená/lékař) platí **zvlášť** pod jinou složkou. Proto se nesmí krátit
„placeno" hodinami, ale **odpracovanými** (`odpracováno = CasCelkem − absence`).

### 2b. Rozpad delty po složkách (před krácením, STRATEGIE − HELIOS)
| Složka | Lidí | STRATEGIE | HELIOS | Δ | Zdroj rozdílu |
|---|---|---|---|---|---|
| Základ | 24 | 1 587 961 | 1 443 996 | **+143 965** | krácení hodinami (po krácení ≈ 0) |
| Os. ohodnocení (+Landmark korekce) | 32 | 190 455 | 110 431 | +80 024 | krácení + Landmark přesun |
| Prémie | 23 | 43 397 | 21 797 | +21 600 | plánovaná vs skutečná prémie |
| Společník/jednatel | 3 | 0 | 204 100 | −204 100 | odměny mimo EC podmínky (viz 2c) |

### 2c. Jednatelské/společnické odměny (mimo EC podmínky, platí jen Helios)
Doplněno do `tenant.wage_component`, typ `component_type_id=13`
(`jednatelska_odmena`, kind=oneoff):
- **Marti Pašek** (č. 2 EC + č. 41 ES): **90 800** EC + 90 800 ES — HOTOVO (dřív).
- **Branislav Mózer** (č. 47 EC, engagement 785): **22 500** — HOTOVO 11. 6. (banner #248).
- Pozn.: 11 lidí má u nás „Odměna jednatele **1 000 Kč**" (Svoboda, Diviš,
  Voříšek, Honal, Lev, Erhard, Trunec, Namjak, Urbanová, Čiviš, Kilberger),
  Helios v květnu nic. **K ověření**, jestli reálná měsíční odměna nebo placeholder.

### 2d. „Jen STRATEGIE" případy — vysvětlené, NEjsou chyba
| Osoba | č. | Δ | Důvod |
|---|---|---|---|
| Michelle Šafránková | 381 | +34 500 | **mateřská** — nepobírá mzdu, Helios základ 0 |
| Ondřej Senft | 374 | +9 000 | **DPP paušál 9 000/měs** — jde jen od nás |
| Světlana Herejtová | 525 | +4 000 | **úklizečka, sporadicky** — bez fixní mzdy/hodin |

---

## 3. Dvouřádkový mzdový model (Martiho rozhodnutí 11. 6.)

Místo tichého krácení základu → **dvě složky (linky)** u každé měsíční mzdy:

1. **Základní mzda dle výměru** = plná smluvní částka (sedí 1:1 s mzdovým
   výměrem / EC podmínkami). Nikdy se nečísluje dolů.
2. **Poměrná úprava za odpracovanou dobu** = ± `výměr × (odpracováno/fond − 1)`.

Součet = „poměrná část měsíční mzdy" dle ZP → sedí s Heliosem.

### Právní podklad (ZP — ověřeno web searchem)
- Poměrná část měsíční mzdy = `MMzda × odpracovaná doba / měsíční fond`.
- Omluvené neodpracované hodiny (dovolená/lékař/svátek) = **náhrada mzdy** (vlastní složka).
- **Přesčas** (nad fond): u EUROSOFTu se řeší **navýšením PRÉMIE**, ne samostatnou
  složkou přesčasu na pásce (Martiho potvrzení). Jinak by ze zákona = mzda + příplatek min. 25 % (§114 ZP).
- Krácení se týká jen **Základní mzda + Osobní ohodnocení**. Pohyby (prémie,
  oblečení, HO, cestovné, srážka) se nekrátí.
- Zdroje: praceamzda.cz (poměrná část), epravo.cz (krácení mzdy), MPSV příručka, ZP §109–112.

### Co je už v systému (čeká na schválení)
- **Banner #249** — nová složka číselníku `tenant.wage_component_type`:
  `code='pomerna_uprava_doby'`, label „Poměrná úprava za odpracovanou dobu",
  kind=pohyb, employer_initiated. *(čeká na schválení)*
- **Banner #250** — view `tenant.v_mzda_dvouradky` — živý výpočet z naší
  docházky (`att_entry`): per měsíc per osoba → výměr (základ+os.ohod) →
  poměr `odpracováno/fond` → ± úprava → mzda za odpracovanou dobu.
  fond = `engagement.fond_mesic_h(174) × úvazek/40`. *(čeká na schválení)*
- **POZOR:** view bude správný **až po 1:1 importu docházky** (viz sekce 4),
  protože teď naše docházka nemá absence a hodiny nesedí.

---

## 4. PROBLÉM DOCHÁZKY — naše data NEJSOU 1:1 (klíčové!)

### 4a. Stav teď (špatně)
`tenant.att_entry` za 2026 obsahuje migraci `source_system='centrala1'`, ale:
- **jen kategorie `presence`** (odpracováno) — **žádné absence** (dovolená/lékař/nemoc…)
- migrace vzala EC `CasCelkem` (= celkem započteno, **včetně** absencí) jako
  odpracováno → odpracováno **nadhodnocené** přesně o absence
- naše `presence ≈ 152 h` plošně = EC „celkem", ne skutečně odpracováno
- + demo/testovací statusy z prezentace výroby + Martiho testy

**Proto se mzda nemůže srovnat** — chybí rozdělení odpracováno / absence / konto.

### 4b. Rozhodnutí Martiho (11. 6.)
> „My nesmíme mít demo docházku v systému. Musíme ji importnout 1:1 od 1.1.2026."

**Hranice (Marti zvolil): celé 1.1.→dnes z EC, plná náhrada.** Smazat vše naše
(vč. reálných píchnutí z appky po 6.6.), nahradit 1:1 z EC. Appka přebírá od příště.

### 4c. ZDROJ pro 1:1 import = `EC_Dochazka_SumaDen` (MSSQL DB_EC)
Denní souhrn na osobu (`CisloZam`, `DatumPripadu`). Klíčové sloupce:

**Odpracováno + práce:**
- `CasCelkem` = celkem započtené hodiny dne (**vč. absencí i přesčasu**)
- `CasPrescas` = denní přesčas (je součástí CasCelkem)
- `CasMontaz`, `CasRezie` = kategorie práce; `CasPauza`
- **Odpracováno = `CasCelkem − Σ absence`**

**Absence (každá ve svém sloupci, hodiny):**
`CasDovolena`, `CasLekar`, `CasNemoc`, `CasMaterska`, `CasOCR`, `CasSickDay`,
`CasOtec`, `CasNeplVolno`, `CasPrekazkaVPraci`, `CasNahradniVolno`,
`CasNarizenoVolno`, `CasNeplacenyPrescas`…

**Konto přesčasů (v téže tabulce!):**
- `Konto` = saldo konta na konci (přenáší se měsíc→měsíc, **může být záporné**)
- `KontoPlacene` = proplacené hodiny konta tento měsíc
- `KontoPlaceneKC` / `KontoPlaceneKCCelkem` = proplaceno v Kč
- `KontoPlaceneMax`, `NeplacenyPrescas`

**Identita:** `EC_Dochazka_SumaDen.CisloZam = TabCisZam.Cislo` (jméno z TabCisZam).
Naše mapování: `hr_person.source_id = EC Cislo`, `att_employee.cislo_zam = EC Cislo`.

### 4d. Reconciliation formule (Martiho „jasná matematika")
```
placeno (Helios) = odpracováno
                 + náhrady (dovolená + lékař + nemoc + mateřská + OČR + …)
                 + SVÁTKY (nejsou v docházce! květen 2026 = 2 dny = 16 h plný úvazek)
                 + proplacené konto (KontoPlacene)
                 − hodiny převedené do konta
```
- **Króner (456)** ověřeno: odpracováno 72 + dovolená 80 + svátky 16 = 168 ✓ (= Helios placeno); jeho Konto = 0.
- **Šafránková Michelle (381)**: celý měsíc mateřská 152 h, 0 odpracováno.
- Konto hraje u lidí s přesčasem (Veverka 31.78 h přesčas, Čepický 37.60…);
  proplacené konto v Kč mají Hájek (1 407), Urbanová (2 232), Brudnová (618), Jakešová (608), Sedláčková (267), Diviš (153).

### 4e. Typy záznamů u nás (`tenant.att_entry_type`, tenant 2)
| id | code | category | id | code | category |
|---|---|---|---|---|---|
| 1 | work | presence | 4 | sick | absence |
| 2 | overhead | presence | 5 | medical | absence |
| 3 | vacation | absence | 6 | family_care | absence |
**Chybí doplnit** (banner): maternity, paternity, neplacené volno, náhradní
volno, překážka v práci, sick day — ať pokryjí EC sloupce (úkol #56).

---

## 5. SVÁTKY
- Docházka (`EC_Dochazka_SumaDen`) svátky **NEzapočítává** (není záznam).
- Helios je platí navíc jako náhradu.
- Květen 2026: **1. 5. a 8. 5.** = 2 dny = **16 h** u plného úvazku (úvazek/40 poměr).
- Zdroj svátků u nás: `tenant.att_calendar*` (zrcadlo EC_Svatky, Kristý = zdroj pravdy).

---

## 6. OTEVŘENÉ OTÁZKY NA PONDĚLÍ (Marti + Kristý + Peťa)

1. **Je sada vstupů kompletní?** odpracováno + absence + svátky + proplacené
   konto ± přenos = Helios placeno. Vstupuje do mzdy ještě něco?
   - příplatky (noční / víkend / svátek navíc)?
   - ruční korekce v Heliosu mimo docházku?
2. **Konto přesčasů — proplácení**: řídí se výhradně `KontoPlacene*` v SumaDen,
   nebo to spouští ještě něco v Heliosu? Je saldo `Konto` správně přenášené z dubna?
3. **1 000 Kč „Odměna jednatele"** u 11 lidí — reálná měsíční odměna, nebo placeholder?
4. **Odpracováno definice**: `CasCelkem − absence` je správně? (vč. přesčasu uvnitř)
5. Potvrdit **hranici importu** (Marti zvolil: celé 1.1.→dnes z EC, plná náhrada).

---

## 7. CO DÁL (plán implementace — úkoly #56–60)

1. **#56** Doplnit chybějící `att_entry_type` (maternity, paternity, neplac.
   volno, náhr. volno, překážka, sick day) — banner.
2. **#57** Finální mapování EC SumaDen sloupce → naše entry_type (+ konto handling).
3. **#58** Vyčistit demo + neúplnou migraci docházky 2026 (DELETE, se zálohou stavu).
4. **#59** **1:1 import `EC_Dochazka_SumaDen` → `att_entry` od 1.1.2026.**
   - Cross-DB (MSSQL→PG) → potřebuje **server-side migrate endpoint** (čte EC přes
     MCP, mapuje, idempotentně zapisuje), NE jen bridge SQL (tisíce řádků).
   - Jeden záznam na nenulovou složku času; `source='import'`,
     `source_system='centrala1'`, `source_id=ID`. Idempotentní (re-run nezdvojuje).
   - Konto: importovat jako vlastní pole/tabulku (saldo + proplaceno), ne jako att_entry.
5. **#60** Verifikace: měsíční součty na osobu = Helios placeno na haléř.
6. Po importu: dotáhnout dvouřádkový model (#249/#250) — pak `v_mzda_dvouradky`
   sedne přesně.

**Pravidlo: žádné mazání docházky, dokud reconciliation (dry-run) nesedne přesně.**

---

## 8. Vygenerované soubory (v kořeni D:\Projekty\STRATEGIE)
| Soubor | Co |
|---|---|
| `Dochazka_kveten2026_EC_souhrn_konto.xlsx` | EC docházka 5/2026, 57 lidí, vč. konta (pro Kristý+Peťu) |
| `Delta_dochazka_kveten2026_STRATEGIE_HELIOS.xlsx` | **trojřádek STR/HEL/Δ docházky** — ukazuje, co import opraví |
| `Mzdy_dvouradkovy_model_STRATEGIE_HELIOS_kveten2026.xlsx` | dvouřádkový mzdový model (výměr + poměrná úprava) |
| `Srovnani_mzdy_STRATEGIE-krac-odprac_HELIOS_kveten2026.xlsx` | mzdy 3řádek, krácení odpracovanými hodinami (delta ≈ 0) |
| zdroje: `Srovnani_mzdy_kveten_2026_pruchod2_hodiny.xlsx` (hodiny), `_pruchod3_slozky.xlsx` (složky) | mezivýpočty |

---

## 9. Gotchy / technické (ať se neztrácí čas)
- **Bridge OUT usekává** velké/široké výsledky (preview). Číst `CLAUDE_OUT.txt`
  **host-side Read toolem** (mount truncuje), nebo dotaz jako 1 sloupec `CONCAT(...;...)`.
- **SQL NULL propagace**: `celkem − absence` kde absence NULL → NULL. Vždy `ISNULL()/COALESCE()`.
- **Fond**: full-time květen = **168 h skutečně** (placeno plná docházka), ale
  `engagement.fond_mesic_h = 174` (smluvní). Hodinovka Heliosu dělí ~174.
  Pro krácení používat **odpracováno**, ne placeno.
- **`cislo_zam` je varchar** v PG (`IN ('2','41')`, ne `IN (2,41)`).
- **`TabBankSpojeni.IDZam = TabCisZam.ID`** (ne Cislo) — kdyby se řešila banka.
- Bridge write = approval banner (parent klikne). Read jde sám.
- EC firma kód: **0 = ES, 1 = EC** (v EC_FinZamPodminky `Firma`).

---

## 10. Slovník osob (mzdové zvláštnosti, ať je po ruce)
- **Marti Pašek** = č. **2 (ES)** + č. **41 (EC)**. POZOR „Martin Pašek" č. 29
  (user 35) je **JINÝ člověk**! Při slučování identit se VŽDY ptej.
- **Mózer Branislav** č. 47 — jednatel, odměna 22 500 (doplněna).
- **Šafránková Michelle** č. 381 — mateřská. **Šafránková ml. Petra** č. 1 — jiná osoba.
- **Senft Ondřej** č. 374 — DPP 9 000 paušál.
- **Herejtová Světlana** č. 525 — úklizečka sporadicky, bez fixní mzdy.
- **Króner Martin** č. 456 — referenční případ reconciliation (72 odpr + 80 dov + 16 svátek = 168).
