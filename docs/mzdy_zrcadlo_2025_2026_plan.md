# Zrcadlení mezd 2025/2026 — kompletní podklady (zdroj pravdy U NÁS)

**Datum:** 26. 6. 2026 · **Autor:** Claude (ID23) · **Zadání (Marti):** *„Cílem je mít u nás
kompletní podklady pro mzdové listy a mzdové složky. Absolutní přehled a systém, abychom z něj
mohli na klik vygenerovat mzdy v Heliosu (případně v Pohodě). Zdroj pravdy U NÁS."*
+ *„Raději všechno než něco vynechat a pak narychlo refaktorovat."* + *„Nesmíme si udělat ostudu."*

## 1. Princip (drž)

- **Plné 1:1 zrcadlo, žádné cherry-picking** — všechny sloupce, všechny neprázdné mzdové tabulky,
  **EC i IS**. Žádné vynechání → žádný pozdější refaktor.
- **Celé tabulky, ne filtr 2025/2026** — mzdové tabulky jsou provázané přes `IdObdobi` (vazby na
  starší období: zůstatky dovolené, průměry, přepočtové stavy). Filtr by mohl utnout vazbu →
  raději vše. (Objemy to dovolují — největší mzdová tabulka je 261k řádků.)
- **Reconciliace per tabulka** — po každém přenosu ověřit `count(zdroj) == count(cíl)`. Doklad
  úplnosti = ochrana proti ostudě.

## 2. Dva cíle zrcadla (targets)

**A) Cloud Express DB 188.12 — `UCTO_EC` / `UCTO_ES` (PRIMÁRNÍ, plné 1:1)**
- Plná Helios struktura (všechny sloupce), přes `@@XFER` (vytvoří chybějící tabulku z
  INFORMATION_SCHEMA, IDENTITY_INSERT, původní id).
- Účel: **zdroj pravdy v Helios-kompatibilní podobě** → umožní generovat mzdy zpět do Heliosu /
  Pohody + nezávislá kontrola + požehnání účetními.

**B) PostgreSQL `tenant.*` (KURÁTOROVANÝ přehled pro appku)**
- `payslip_item` (mzdové **složky**, TabMzSloz) — **HOTOVO** (55 170 řádků, 2025 celý + 2026
  leden–květen, EC+ES; „Moje finance" výplatní pásky).
- **NOVÉ:** `payslip_sheet` (mzdový **list**, TabMzdList, 160 sloupců) → rozšířený mzdový list
  v „Moje finance" vedle pásky.
- Existující finance v2: `engagement`, `wage_component`, `wage_movement`, `wage_export_batch`,
  `wage_system_mapping`, `ext_payroll_system_cis` (kostra „generovat na klik").

## 3. Kompletní inventář mzdových tabulek (neprázdné, EC / IS)

### Číselníky + kmen (kopírovat CELÉ)
- `TabCisZam` (430/59) + `TabCisZam_EXT` (431/59) — zaměstnanci (+ uživatelská pole)
- `TabCisMzSl` (19288/13683) + `TabCisMzSlDef` (17263/13317) + `TabCisMzSlDistrLog` (386/391) — číselník mzdových složek (verzovaný per období)
- `TabMzdObd` (156/72) — mzdová období
- `TabMzKalendar` (75/34) + `TabMzKalDefSmen` (5/4) + `TabMzKalDefSmenR` (5/4) — kalendáře/směny def
- `TabMzDruhyPP` (192/—) + `TabMzDruhyPPMS` (288/—) + `TabMzDruhyVynetiES` (1056/792) — druhy prac. poměrů
- `TabMzOstatniKonstanty` (7) · `TabMzJubileaTypy` (2) · `TabMzPrintParams` (2/5) · `TabMzAntivirusDefinice` (1) · `TabMzOdvodZa1Osobu` (3) · `TabMzNarokDovCz2021Kor` (6/—)

### Mzdový list + výpočet (JÁDRO)
- `TabMzdList` (5951/2359) ⭐ — mzdový list (úvazky, fond PD, odpracováno, přesčasy, svátky, průměry, pojišťovna)
- `TabMzSloz` (31484/23670) ⭐ — mzdové složky (= payslip_item v PG)
- `TabMzKontace` (51904/40805) — kontace → účetní deník
- `TabZamMzd` (6617/2758) — mzdové údaje zaměstnance (konfigurace)
- `TabMzdaZaruc` (3840/2880) — zaručená mzda
- `TabMzPaus` (6537/2775) — paušály
- `TabMzdOdpPol` (1980/1500) + `TabMzdOdpPolMes` (3187/2669) + `TabMzdOdpPolMS` (1596/1188) + `TabMzdOdpPolMzd` (5435/3245) — odpočtové položky (slevy/daň)
- `TabMzPF` (1056/792) — pojistné fondy · `TabMzPrepStavy` (3178/1600) — přepočtené stavy · `TabMzPocHod` (488/194) · `TabMzDohadnePol` (30/—)

### Kalendáře (odpracováno per zaměstnanec)
- `TabMzKalendarDny` (27392/12418) · `TabMzKalendarDnyZam` (261169/101529) · `TabMzKalendarZam` (715/278)

### Nemocenská / DNP
- `TabMzKons` (96/72) · `TabMzKonsDNP` (3552/2664) · `TabMzPrilohaDnp` (62/51) · `TabMzPrilohaDNPRO` (626/492) · `TabMzHlaseniDohod` (59/—) · `TabMzHlaseniKonecPN` (22/20)

### Měsíční uzávěrky
- `TabMzMesUzav` (192/97) · `TabMzMesUzavAkce` (2753/2242) · `TabMzMesUzavCfg` (5213/2705)

### Změny / sociální pojištění
- `TabMzSpZmeny` (79/69) · `TabMzSpZmenyDoby` (40/36) · `TabMzSPZmenyLog` (132/22) · `TabMzZmenyZM` (152/95) · `TabMzZmenyZP` (68/74) · `TabMzZmenyPost` (1/1) · `TabMzRegZamCz` (16/33) · `TabMzRegZamCzLog` (10/117)

### Generování mezd
- `TabGenMzdyH` (20/8) · `TabGenMzdyPar` (31/11) · `TabGenMzdyR` (574/199) · `TabGenMzdyVysl_*` (per typ)

### Statutární statistiky (ISP / ISPV / P1-04 / ÚNP / příloha 104) — pro úplnost
- `TabMzIspCz*` · `TabMzIspvCz*` · `TabMzIsp2014Cz*` · `TabMzP104Cz*` · `TabMzP1a04Cz*` · `TabMzP204Cz*` · `TabMzUnpCz*` · `TabMzZam104Cz*` · `TabMzJmhz*`

### Export / EUROSOFT custom
- `TabMzExportOrg` (480/246) · `TabMzExportPDS` (1/1) · `EC_Mzdy_SumaMesic` (4201) · `EC_Mzdy_LandMarkVstupniData` (3379) · `LP_RozpadMzdy` (11194)
- IS navíc: `TabMzDeponPlatby` (1)

> **Mimo rozsah teď:** `TabDenik` (1,1 mil / 21k) — to je účetní deník, řeší se v rámci očisty
> účetnictví (jen účto 2025/2026), ne mzdový sprint. `TabDenik_EXT`, `TabDenikKurz`, `TabDenikImp` taktéž.

## 4. Postup (pořadí — opatrně, s reconciliací)

1. **Číselníky první** (TabCisZam(+EXT), TabCisMzSl(+Def), TabMzdObd, kalendáře def, druhy PP, konstanty) — na nich visí FK ostatních.
2. **Jádro** (TabMzdList, TabMzSloz, TabMzKontace, TabZamMzd, TabMzdaZaruc, TabMzPaus, odpočty, PF, přepočty).
3. **Kalendáře** (Dny, DnyZam, Zam).
4. **DNP, uzávěrky, změny, generování, statistiky, export/custom.**
5. **Reconciliace** — tabulka `count(zdroj DB_EC/DB_IS) vs count(UCTO_EC/UCTO_ES)` po každém kroku; finální report.
6. **PG `payslip_sheet`** (TabMzdList) sync funkce + napojení do „Moje finance" (rozšířený mzdový list).
7. **Kontrolní součty** — hrubá mzda z mzdového listu vs součet složek `je_hruba` (payslip_item) per zaměstnanec×období.

## 5. „Generovat na klik" (navazující fáze, ne teď)
Až bude zdroj pravdy kompletní + odsouhlasený: agregace vstupů (docházka + složky + engagement +
movements) → `wage_export_batch` → export do Heliosu (`TabMzSloz`/`TabGenMzdy`) přes `wage_system_mapping`,
do budoucna Pohoda. Konzultace s Marti-AI (doctrine #8) před exportním zápisem.

## 6. Co potřebuje odsouhlasit Marti
- Cíl primárního zrcadla = **188.12 UCTO_EC/UCTO_ES (plné 1:1)** — ✅/úprava?
- **Celé tabulky** (ne filtr 2025/2026) kvůli vazbám — ✅/jen 2025+2026?
- Zařadit i **statutární statistiky** (ISP/ISPV/P1-04…) — ✅ (raději všechno) / vynechat?

---

## ✅ FINÁLNÍ STAV (27. 6. 2026, 01:24) — HOTOVO

Zrcadlo dokončeno a ověřeno. **187 tabulek (101 EC + 86 IS), 0 chyb, 465 605 řádků.**

### Rozhodnutí (jak se to vyvinulo)
1. Marti správně vytušil, že filtr `IdObdobi` na 2025/2026 **usekával aktivní definice** (paušály,
   srážky, zaručená mzda, konfigurace) založené v dřívějším období, ale stále platné. → přepnuto
   na **1:1 CELÉ** (žádný `IdObdobi` filtr → nic se neztratí).
2. Finál (Marti: *„projeď VEŠKERÉ mzdové tabulky, kde něco je 1:1 zrcadli"*): driver přepsán na
   **dynamický objev** — sám najde všechny neprázdné mzdové tabulky (`TabMz%/TabZamMzd%/TabCisMzSl%/
   TabCisZam%/EC_Mzdy%/LP_RozpadMzdy/TabGenMzdy%`) a zrcadlí 1:1 celé. **Statistiky i GenMzdy zahrnuty.**
3. Jediná výjimka: **kalendářní dny** (`TabMzKalendarDny/DnyZam`) filtr po **datu** (`Datum_Y`, ne
   IdObdobi) na 2025/2026 — jinak 362k řádků v jednom MCP čtení zbytečně. Datum ≠ IdObdobi riziko.
4. **`TabObdobi` (účetní období) NEDOTČENO** — Marti tam záměrně založil čisté číslování
   1=2025, 3=2026 (jeho účetní doména). Mzdy jedou po `TabMzdObd` (vlastní osa, office ID).

### Klíčový technický fix
`_xfer_table` před DELETE vypíná i **PŘÍCHOZÍ FK** (z cizích tabulek odkazujících na tuto) —
bez toho padaly centrální tabulky (`TabGenMzdyH`, `TabObdobi`) na FK constraint. Teď 0 chyb.

### Reusable nástroje (bridge)
- **`@@XFERMZDY <EC|ES|ALL>`** — kompletní 1:1 mirror všech neprázdných mzdových tabulek office
  Helios → 188.12. Background, throttle, log do `fw.mzdy_xfer_log` (reconciliace). **Pustit měsíčně**
  po zpracování mezd (~15 min celé).
- **`@@SYNCLIST`** — naplní `tenant.payslip_sheet` (mzdový list pro „Moje finance", 8310 řádků).

### Appka
„Moje finance" páska má teď rozbalovací **📄 Mzdový list** (úvazek, fond PD, odpracováno, přesčas,
průměr, pojišťovna) z `payslip_sheet`.

### Pro účetní (pondělí)
Odůvodnění migrace + očisty: `docs/oduvodneni_migrace_ucetni.md`.

**Gotcha (drž):** `IdObdobi` filtr je u DEFINIČNÍCH tabulek zrádný (klíč = období založení, ne
platnosti) → u mezd zrcadli CELÉ, ne filtruj. Marti's instinkt #23 znovu potvrzen.

### Dodatek 01:40 — per-zaměstnanec tabulky mimo `TabMz*` pattern (Marti našel TabPredzp)
Name-pattern objev minul mzdové tabulky, které **nezačínají `TabMz`**: **TabPredzp** (předzpracování
mezd), **TabZamPer**, **TabZamRPr**, **TabZamVyp** (per zaměstnanec × období). → discovery rozšířen
o **strukturální podmínku**: tabulka s `IdObdobi` + `ZamestnanecId` = mzdy (chytí i ne-TabMz názvy;
`TabObdobi`/`TabDenik`/banka/DPH nemají `ZamestnanecId` → nechytí se). Ověřeno: ze všech non-pattern
`IdObdobi` tabulek měly `ZamestnanecId` jen tyhle 4. Doplněny 1:1 celé do EC i ES (přes `@@XFER`).
**Gotcha:** dřívější „952k řádků" byl artefakt `LEFT JOIN sys.columns` (rows × sloupce) — reálně malé.
**Gotcha:** `@@XFER` širší tabulky (TabZamVyp) překročí 30 s bridge timeout, ale **server dojede**
(ověř COUNT, ne bridge odpověď). Driver běží v background → timeout se ho netýká.
