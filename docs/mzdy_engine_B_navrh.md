# Mzdový engine — návrh varianty B (náš script, z aktuální docházky)

**Autor:** Claude ID23 · 27. 6. 2026 · pro Marti + Kristý
**Kontext:** Tři cesty výpočtu mezd, všechny → **stejné mzdy**:
- **A** = staré Helios procedury (`EC_Mzdy_GenerujMesic` …) — referenční pravda
- **B** = náš script nad **office** daty (DB_EC), **nepotřebuje uzavřenou docházku**, jede z aktuální
- **C** = náš script nad **cloud** Heliosem (188.12)

Tento dokument = návrh **B** (a tím i C, je to stejný kód jen jiná DB).

---

## 1. Co dělá cesta A (rozklíčováno z procedur)

`EC_Mzdy_GenerujMesic(@Rok,@Mesic,@PrepocetDochazky)`:
1. `EC_KontrolaMzdy` — kontroly
2. *(volitelně)* `EC_Dochazka_DenniSumaceMesicVsichni` — **přepočet denních sumací docházky** (sem patří to „uzavírání/příprava docházky", co tě brzdí)
3. `DELETE EC_Mzdy_SumaMesic` pro měsíc (smaže starý výpočet)
4. **Výběr zaměstnanců** z `EC_FinZamPodminky` (aktivní, smlouva HPP/DPP, má v měsíci docházku nebo odměnu)
5. cyklus per zaměstnanec → **`EC_Mzdy_PrepocetMesicZam`** = jádro výpočtu
6. `EC_Mzdy_Konto_GenerujPropadle`

**Klíč pro B:** veškerá „těžká práce" rozpadu docházky na hodiny a částky **už je hotová** v denních sumacích `EC_Dochazka_SumaDen`. A umí se přepočítat kdykoliv (`EC_Dochazka_DenniSumaceMesicVsichni` / `EC_DochazkaPrepocetMzdy`) — **bez uzavírání měsíce**. To je důvod, proč B z aktuální docházky dává smysl.

---

## 2. Datové zdroje pro B (vše v DB_EC / cloud UCTO_EC)

| Tabulka | K čemu | Klíčové sloupce |
|---|---|---|
| **`EC_Dochazka_SumaDen`** | denní sumace docházky (1 řádek = zaměstnanec × den) | `CisloZam, DatumPripadu(_Y/_M), CasCelkem, FPD, ZakladZaHod, OsOhodZaHod, VykonOhodZaHod, CasPrescas, CasDovolena, CasSickDay, CasNemoc, CasLekar, CasOCR, Cas*Volno*, Konto, KontoPlacene` |
| **`EC_FinZamPodminky`** | finanční podmínky zaměstnance (sazby, úvazek, smlouva) | `CisloZam, PlatnostOd, DruhSmlouvy, Zaklad, OsOhod, IndividualOhod, ZakladZaHod, OsOhodZaHod, SmlouvaUvazekT, RealUvazekT, ZdrPojKod, PodepsaneProhl, Odpocet1Mesic, SrazetNeodpracovaneHodiny` |
| **`EC_FinPriplatkySrazkyDefinice`** | jednorázové příplatky/srážky/cesťáky | `CisloZam, Castka, Typ (10/30/40 ohodnocení, 47 cesťák), Schvaleno, PlatnostOd/Do` |
| **`EC_DochKalendar`** | prac. dny v měsíci | `Rok, Mesic, PracDni` |
| **`EC_Svatky`** | svátky / prac. volno (víkend, svátek) | `Datum, je_st_svatek, je_prac_volno` |
| **`EC_Mzdy_SumaMesic`** | měsíční souhrn (výstup A; pro B = konto z min. měsíce) | `CisloZam, Rok, Mesic, Konto*, DovolenaCerpano, SickDayCerpano` |
| `TabCisZam` + `_EXT` | karta zaměstnance | `Cislo, _DatumOdchodu, _Neaktivni, _Firma, Stredisko` |

**Konstanta:** `@HodMesKonst = 174` (fond hodin/měsíc), hodinová sazba `= (OsOhod+IndividualOhod+Zaklad)/174`.

---

## 3. Výpočet B — per zaměstnanec, per měsíc

### 3a. Výběr zaměstnanců (jako A)
Z `EC_FinZamPodminky` (nejnovější platná podmínka ≤ konec měsíce) JOIN `TabCisZam(_EXT)`:
- smlouva HPP/DPP (`EC_GetSmlouvaProMzdy`), datum odchodu ≥ tento měsíc,
- a (má schválenou odměnu v `EC_FinPriplatkySrazkyDefinice`) **nebo** (má docházku v `EC_Dochazka` v měsíci).

### 3b. Hrubá mzda (z denních sumací — žádné uzavírání)
Agregace `EC_Dochazka_SumaDen` za (CisloZam, Rok, Mesic):
```
základ        = Σ (FPD × ZakladZaHod)            -- odpracováno × sazba
osobní ohod.  = Σ (FPD × VykonOhodZaHod)
přesčasy      = Σ CasPrescas × sazba × koeficient (víkend 1.35 / svátek 2.0 / zbytek 1.25)
náhrady       = dovolená/svátky/lékař/nemoc(náhrada 14 dní)… z Cas* sloupců × průměr
+ příplatky/odměny (typ 10/30/40) − srážky + cesťáky (typ 47, nedaní se)
= HRUBÁ MZDA
```
> Pozn.: A to počítá řádek po řádku do mzdových složek (`CisloMS`). B může pro v1
> spočítat **souhrnné částky** (hrubá, základ daně, odvody, čistá) a teprve ve v2
> rozpadnout na složky `CisloMS` 1:1 jako A (pro přesnou shodu složek).

### 3c. Odvody a daň (zákonné vzorce 2025/2026 — ne firemní logika)
```
SP zaměstnanec = 6,5 % × hrubá           SP zaměstnavatel = 24,8 % × hrubá
ZP zaměstnanec = 4,5 % × hrubá           ZP zaměstnavatel = 9,0 % × hrubá  (min. VZ = min. mzda)
základ daně    = hrubá (superhrubá zrušena 2021)
záloha daně    = 15 % × zaokr. základ
– sleva na poplatníka (2 570 Kč/měs, jen když PodepsaneProhl=1)
– daňové zvýhodnění na děti (z karty)
čistá mzda     = hrubá − SP_zam − ZP_zam − daň_po_slevě − ostatní srážky + bonusy
```
Sazby/slevy = **verzovaný číselník** (legislativa per rok) — ať se rok mění bez zásahu do kódu.

### 3d. Výstup B
Návrh: vlastní tabulka **`tenant.mzda_b_radek`** (nebo přímo do Helios `TabMzSloz`/`TabPredzp`
pro 1:1 shodu). Doporučení: **v1 do vlastní tabulky** (zam, období, hrubá, SP/ZP/daň, čistá,
zdroj='B'), ať nic nepřepisuje Helios; až bude B = A ověřeno, volitelně zapisovat i do složek.

---

## 4. Validace: delta přehled A = B (= C)
Separátní přehled „**Mzdy — porovnání cest**" (per období, per zaměstnanec):
| Zaměstnanec | A hrubá | B hrubá | Δ | A čistá | B čistá | Δ | … |
- zelená = sedí na korunu, červená = rozdíl → klik rozbalí složky/dny ke zjištění příčiny.
- Spouští se v **sandboxu** (Claude python) nad zrcadlenými daty — nuluje riziko.
- Cíl: **0 rozdílů na všech zaměstnancích za 2025** (historie jako testovací sada) → pak důvěra.

---

## 5. Proč B (a ne hned C)
- B běží nad **office** daty, kde je živá docházka → můžeš generovat **kdykoliv z aktuálního stavu**, bez „uzavři docházku" kroku.
- C = identický kód nad cloudem (188.12) — spustíme, jakmile B sedí proti A. Rozdíl jen connection string.

## 6. Otevřené otázky (na tebe/Kristý)
1. **Rozpad na složky `CisloMS`** chceme hned (kvůli 1:1 shodě výplatnice), nebo stačí souhrn v1 a složky ve v2?
2. **Náhrady mzdy** (dovolená/nemoc/svátek) — počítat průměrem (`PrumerHV` z podmínek) jako A, nebo zjednodušeně sazbou ve v1?
3. **Konto hodin** (převody mezi měsíci) — řešit v1, nebo až ve v2? (A to dělá přes `EC_Mzdy_SumaMesic`.)
4. Výstup B do **vlastní tabulky** (bezpečné, doporučuji) vs. přímo do Helios složek.
5. Číselník **sazeb/slev** (SP/ZP/daň/sleva/min.mzda) per rok — potvrdit hodnoty 2025 i 2026.

---

## 7. Co je hotové (cesta A, dnes)
Konzole `/mzdy-prehled` → panel „Zpracování aktuálního období": 3 sady tlačítek (A živé:
Vstupní data → Generovat → Kontrola → Zrcadlit → Smazat; B/C placeholder) + monitor
kancelář × cloud „rovná se". `EXEC` procedury přes most ověřen (`EC_KontrolaMzdy` proběhla).

**Další krok po schválení tohoto návrhu:** postavit `mzda_b_engine` (Python v sandboxu)
+ delta přehled A↔B nad daty 2025, doladit k 0 rozdílů, pak zapojit jako cesta B do konzole.
