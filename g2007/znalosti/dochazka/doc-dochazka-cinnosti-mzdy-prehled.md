# Přehled pro Claude: docházkové činnosti a jejich vliv na mzdy

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přehled pro Claude: docházkové činnosti a jejich vliv na mzdy

> **Zdroje:** `Všechny procedury.sql`, `Tab_proc_trigger.sql`, související exporty (soubor `Mzdy_proc_tab` byl prázdný).  
> **Účel:** Dokumentace pro vývoj nového systému docházky — jaké speciality mají jednotlivé činnosti (`DruhCinnosti`) a jak ovlivňují mzdy, stravenky a kontroly.

---

## Kontext systému

Docházka běží v **EUROSOFT-Control** (`DB_EC`), mzdy se přenášejí do **HELIOS** (`DB_IS` / `DB_EC` dle `CisloZam`). Každý záznam v `EC_Dochazka` má číselný kód **`DruhCinnosti`**, který určuje mzdové chování.

### Datový tok (mzdový řetězec)

```
EC_Dochazka (surová docházka)
    → EC_Dochazka_DenniSumace (denní agregace podle činností)
    → EC_Dochazka_SumaDen
    → EC_Mzdy_PrepocetMesicZam (měsíční přepočet zaměstnance)
    → EC_Mzdy_SumaMesic
    → EC_ContrMzdyPrenesDoMezd (import do HELIOS → TABPREDZP)
    → EC_ContrMzdyVypocitejMzdu
```

**Klíčové procedury:** `EC_Mzdy_GenerujMesic`, `EC_Mzdy_PrepocetMesicZam`, `EC_ContrMzdyPrenesDoMezd`, `EC_Dochazka_DenniSumace`.

---

## Základní princip kódů činností

| Rozsah | Význam |
|--------|--------|
| **1–9** | Práce (dílna, režie, HO, montáž…) — pro mzdy se mapují na **1** (`DruhCinn_Mzdy`) |
| **6** | Výchozí činnost (DB default) |
| **≥ 20** | Absence / speciální typy s vlastní mzdovou složkou |
| **119, 123** | Přestávky (oběd, svačina) → tabulka `EC_Dochazka_Prestavky` |

Vypočtený sloupec:

```sql
DruhCinn_Mzdy = CASE WHEN DruhCinnosti <= 9 THEN 1 ELSE DruhCinnosti END
```

---

## Stravenky — nejdůležitější pravidla

Stravenky se **nepočítají po kusech**, ale jako **měsíční paušál**:

- **CisloMS 793** (stravenkový paušál)
- **82 Kč / den**
- Starý model CisloMS 952 je **zakomentovaný / neaktivní**

### Kdo má nárok

- Pouze **HPP** (`_HPP = 1`)
- **DPP** → vždy 0 stravenek
- Nárok od data **`TabCisZam_EXT._StravenkyOD`** (typicky 3 měsíce po nástupu)
- **FPD < 6** → 0 stravenek (nízký úvazek)

### Denní výpočet (`EC_Dochazka_DenniSumace`)

- Výchozí: **1 stravenka/den**
- **Nulování** pokud:
  - jakákoli činnost **DruhCinnosti 20–26** (absence)
  - **sobota/neděle**
  - méně než **4 měsíce** od nástupu
- Uložení: `PocetStravenek = @PocetStravenek * @HPP`

### Měsíční výpočet (`EC_Mzdy_PrepocetMesicZam`)

Počáteční hodnota = počet pracovních dnů v měsíci, pak se **odečítají dny**, kdy je na `EC_Dochazka_SumaDen`:

| Pole v SumaDen | Činnost | Odečítá stravenku? |
|----------------|---------|-------------------|
| `CasDovolena` | 20 | **ANO** |
| `CasLekar` | 21 | **ANO** |
| `CasNemoc` | 22 | **ANO, jen pokud > 2 h/den** |
| `CasOCR` | 23 | **ANO** |
| `CasOtec` | 33 | **ANO** |
| `CasMontaz` | 9 | **ANO** (služební cesta = bez stravenky) |
| `CasNepritomen` | 34 | **ANO** |
| `CasVolno60` | 35 | **ANO** |
| `CasVolno70` | 47 | **ANO** |
| `CasVolno80` | 50 | **ANO** |
| `CasVolno90` | 51 | **ANO** |
| `CasMaterska` | 36 | **ANO** |
| `CasNeplVolno` | 39 | **ANO** |
| `CasPrekazkaVPraci` | 138 | **ANO** |

**Výjimka nemoc:** pokud nemoc ≤ 2 hodiny za den a zaměstnanec odpracoval zbytek dne, stravenka **zůstává**.

**Korekce:** `EC_FinPriplatkySrazkyDefinice` kde **Typ = 8** (schválené).

---

## Kompletní přehled činností (`DruhCinnosti`)

### Práce (0–19)

| Kód | Název / význam | Stravenky | Mzdy / speciální pravidla |
|-----|----------------|-----------|---------------------------|
| **1–9** | Práce (dílna, režie…) | Normálně ANO | CisloMS **1** (základ); počítá se do `CasCelkemPrace` |
| **6** | Výchozí činnost | ANO | DB default |
| **8** | Home office | ANO | Auto `ZamPoznamka='HO'` |
| **9** | Služební cesta / montáž | **NE** (měsíčně) | Vyžaduje cesťák; vyloučeno z některých kontrol odhlášení |
| **10** | Nařízené volno | **NE** (20–26) | Srážka **10 % z hrubé** (`SrazkaNarVolno`); buduje **placené konto** (`KontoPlacene`) |
| **12** | Nahrazení nařízeného volna | ANO | Snižuje konto; **vyloučeno z převodu přesčasů**; proplácí se z konta |
| **27** | Odměna z fin. zakázek | ANO | Vyloučeno z kontroly překryvu |

### Absence a volno (≥ 20)

| Kód | Název | Stravenky | CisloMS | % platu | Zdroj dat |
|-----|-------|-----------|---------|---------|-----------|
| **20** | Dovolená (D) | NE | **211** | 100 % | Docházka |
| **21** | Lékař (L) | NE | **243** | 100 % | Docházka |
| **22** | Nemocenská (N) | NE* | **200** | dle ZP | `EC_Dochazka_Udalosti` Typ=1 |
| **23** | OČR | NE | **251** | dle ZP | Udalosti Typ=2 |
| **26** | Volno bez mzdy | NE | **246** | **0 %** | Udalosti Typ=25 |
| **28** | Čerpání časového konta | — | — | — | `HodinyDoFPD=0` |
| **29** | Osobní hodnocení | — | — | — | Generovaný záznam |
| **30** | Dovolená navíc (DN) | NE | — | 100 % | Stejná logika jako 20 |
| **31** | Sick day (SD) | NE | — | 100 % | Speciální výpočet půldnů |
| **33** | Otcovská | NE | **254** | dle ZP | Udalosti Typ=18 |
| **34** | Nepřítomen / ostatní | NE | **252** | 100 % | Udalosti Typ=19 |
| **35** | Volno 60 % | NE | **256** | **60 %** | Udalosti Typ=20 |
| **36** | Mateřská | NE | **255** | — | Import do mezd **zakomentován** (2/2026) |
| **37** | Neplacené volno (NO) | — | — | — | Editace jen přes Správu docházky |
| **39** | Neplacené volno (nahrazení) | NE | **246** | **100 %** | `EC_GetSeznamMzdNeplV` |
| **47** | Volno 70 % | NE | **256** | **70 %** | Udalosti Typ=30 |
| **50** | Volno 80 % | NE | **256** | **80 %** | Udalosti Typ=26 |
| **51** | Volno 90 % | NE | **256** | **90 %** | Udalosti Typ=27 |
| **54** | Nepřítomen pro APS | — | — | — | **Nové 2026**, `EC_EventTyp` ID=31 |
| **138** | Překážka v práci | NE | **256** | **100 %** | Udalosti Typ=29 |

### Přestávky a ostatní

| Kód | Název | Poznámka |
|-----|-------|----------|
| **119** | Oběd | `JePrestavka=1` → `EC_Dochazka_Prestavky`; max. délka `MaxDobaMin` |
| **123** | Svačina | Přestávka; dědí poslední zakázku |
| **125** | Služební cesta | Noční kontrola auto-prodlouží na 8 h |
| **133** | Náhradní volno (NV) | Počítá se do denního součtu hodin; `NekontrolovatPrekryv` možné |
| **136** | Výpomoc | Vyloučeno z kontroly překryvu přestávek |

---

## Mapování událostí → činností (`EC_EventTyp`)

| EventTyp ID | Text | DruhCinnosti |
|-------------|------|--------------|
| 1 | Nemoc | 22 |
| 2 | OČR | 23 |
| 18 | Otcovská | 33 |
| 19 | Ostatní/Nepřítomen | 34 |
| 20 | Volno 60 % | 35 |
| 21 | Mateřská | 36 |
| 25 | Volno bez mzdy | 26 |
| 26 | Volno 80 % | 50 |
| 27 | Volno 90 % | 51 |
| 29 | Překážka v práci | 138 |
| 30 | Volno 70 % | 47 |
| **31** | **APS** | **54** (nasazení 2026) |

Absence se zadávají ve **Správě docházky** (`EC_Dochazka_Udalosti`), ne v běžné docházce.

---

## Další výjimky a speciální pravidla

### 1. Nařízené volno (10) + nahrazení (12)

- **10:** 10 % srážka z hrubé; hodiny jdou do placeného konta
- **12:** čerpá konto; **nepřevádí se do přesčasů** (proplácí se jinak)

### 2. FPD strop pro absence (≥ 20)

- Absence se krátí na `min(FPD, 8 h)` nebo polovinu
- **Výjimka: lékař (21)** — nekrátí se (návštěva s rodinným příslušníkem = celý FPD)

### 3. Počítání dnů dovolené / sick day

- **20, 30:** 0,5 dne nebo 1 den dle délky vs. denní FPD
- **31 (SD):** speciální zaokrouhlování po 2 hodinách

### 4. Přesčasy — vyloučené činnosti

Z báze přesčasů jsou vyňaty: `9, 10, 12, 20–37, 39, 47, 50, 51, 133, 138`.

Kód **12** navíc nesmí jít do převodu hodin.

### 5. Ochrana před smazáním z běžné docházky

Tyto kódy **nelze mazat** z přehledu Docházka (jen ze Správy docházky):

`10, 20, 21, 22, 23, 30, 31, 33, 34, 35, 36, 47, 50, 51, 138`

### 6. Omezená editace (jen admin / Správa docházky)

`20, 21, 22, 23, 30, 31, 33, 34, 35, 36, 37, 39, 50, 51, 133, 10`

### 7. Konfigurace činností (tabulky)

`EC_Dochazka_CinnostiRezie` (režie) + `EC_DilnaCinnosti` (dílna), UNION:

| Flag | Význam |
|------|--------|
| `JePrestavka` | Záznam jde do `EC_Dochazka_Prestavky` |
| `NekontrolovatPrekryv` | Přeskočit kontrolu překryvu |
| `DogenerovatDoch` | Auto-dogenerovat celý den (08:00–08:00+FPD) |
| `MaxDobaMin` | Max. délka přestávky |

### 8. Noční kontrola docházky

- Montáž **(9):** chyba bez cesťáku
- Služební cesta **(125):** auto-prodloužení na 8 h
- Oběd **(119):** kontrola délky vs. `MaxDobaMin`
- Překryv: respektuje `NekontrolovatPrekryv` (historicky hardcoded 133, 136)

---

## Co musí nový docházkový systém respektovat

1. **`DruhCinnosti` je klíčový** — určuje mzdy, stravenky, přesčasy i kontroly.
2. **Absence (≥ 20)** se zadávají přes Správu docházky / události, ne jako běžná práce.
3. **Stravenky** se počítají měsíčně z pracovních dnů minus absence; montáž (9) stravenku **odečítá**.
4. **Nemoc ≤ 2 h** stravenku **neodečítá**.
5. **Nařízené volno (10/12)** má vlastní konto logiku — nesmí se míchat s přesčasy.
6. **Přestávky (119, 123)** jsou oddělená tabulka, ne hlavní docházka.
7. Nový kód **54 (APS)** je v nasazení — pole `CasNepritAPS` v `EC_Dochazka_SumaDen`.

---

## Co v souborech chybí

V exportech **nejsou INSERT data** pro `EC_Dochazka_CinnostiRezie` a `EC_DilnaCinnosti` — konkrétní názvy a flagy u jednotlivých pracovních činností (1–5, 7 atd.) je potřeba dotáhnout z live DB:

```sql
SELECT Cislo, Nazev, JePrestavka, NekontrolovatPrekryv, DogenerovatDoch, MaxDobaMin
FROM EC_Dochazka_CinnostiRezie
UNION ALL
SELECT Cislo, Nazev, JePrestavka, NekontrolovatPrekryv, DogenerovatDoch, MaxDobaMin
FROM EC_DilnaCinnosti
ORDER BY Cislo;
```

---

*Vygenerováno: červen 2026*


