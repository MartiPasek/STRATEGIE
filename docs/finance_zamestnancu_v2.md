# Finanční podmínky lidí — univerzální standard v2 (vize, Marti 7. 6. 2026)

Marti: *„Není to postavené ideálně. Musíme to převorat do univerzálního
standardu. Potřebujeme to v brzké době pro Šárku jako podklad ke mzdovým
výměrům, pracovním smlouvám a dodavatelským rámcovým smlouvám. V tabulce
zaměstnanců nejsou jen kmenoví, ale i živnostníci. Je to bastl, který
musíme dočistit."*

## Co existuje (DB_EC, ověřeno 7.6.)

**`EC_FinZamPodminky`** — jádro, ~80 sloupců v jednom řádku:
- 79 aktuálních (48 HPP, 29 OSVČ, 2 DPP), 932 verzí historie
  (`Aktualni` bit + `PlatnostOd`/`TarifOD` — verzování funguje)
- smlouva: DruhSmlouvy/Text, DatumSmlouvyOd/Do, ZkusebniDobaDo
- úvazek: SmlouvaUvazekT, RealUvazekT, PocetHodMes, Hodinovka (10×)
- mzdové složky JAKO SLOUPCE: Zaklad, OsOhod, MzdPremie, IndividualOhod,
  VedeniLidi, VedeniObch, Produkce, Kvalita, FKodexKultur… — každá
  navíc v variantách `*Real` (skutečnost) a `*ZaHod` (hodinová)
- benefity: SickDay*/Volno* (standard+navíc+celkem), BenefitSluzebAut,
  PrispevekDoprava, StravenkyOD
- montáže: MontazKcHod, CestaMontazKcHod
- OSVČ/role: JednorazovyPoplatek, OdmenaGarant, OdmenaJednatel

Satelity: EC_FinPriplatkySrazkyDefinice(+Typy) — příplatky/srážky
(IdMzdoveSlozky!), EC_FinBenefityZam, EC_FinOdmenyZam, EC_ZamestFinan
(sazby), EC_Mzdy_SumaMesic, EC_ZamDovolene.

**Proč je to bastl:** složka mzdy = sloupec (nová složka = ALTER TABLE),
plán/real/hodinová = 3 sloupce místo atributů, HPP a OSVČ ve stejné
struktuře bez rozlišení režimu, benefity/smlouva/mzda/montáže v jednom.

## Skupina firem EC + ES (analýza 7.6. odpoledne, Marti's upřesnění)

Od ~2021 grupa: **EUROSOFT-Control (EC)** + **EUROSOFT-System (ES)** pod
jedním tenantem EUROSOFT. Nálezy:

- **`TabCisZam_EXT._Firma`** (DB_EC): hodnoty **0 = 351** (staré/nezadáno),
  **1 = 64**, **2 = 15** — sémantiku 1/2 potvrdí Marti.
- **`EC_FinZamPodminky.Firma`**: jen 0/1 (33/46) — **jiné kódování než EXT**
  a **13 zaměstnanců má rozpor** mezi podmínkami a kartou. Část bastlu.
- **DB_IS** (Helios ES, účetnictví+mzdy): dosažitelná cross-db ze stejné
  instance! `TabCisZam` 59 osob, **`TabMzSloz` 23 668 řádků** (oficiální
  mzdové složky ES). DB_EC má TabMzSloz také (Helios mzdy EC).

**Důsledek pro DDL (prodejnost!):** nový rozměr **`tenant.company`**
(firma v rámci tenantu/grupy): id, tenant_id, code (EC/ES), nazev, ico…
`tenant.engagement.company_id NOT NULL` — každý vztah patří konkrétní
firmě grupy. Stejný vzor jako tenant_group v jádru STRATEGIE — prodejné
pro jakoukoliv skupinu firem.

**Odpovědi (Marti 7.6. odpoledne):**
1. **Zdroj pravdy firmy = `EC_FinZamPodminky.Firma`: 0 = ES (33 osob),
   1 = EC (46)** — sedí přesně na poslední mzdové uzávěrky v DB_IS
   (období 99–101 = 33 živých lidí). `TabCisZam_EXT._Firma` je nespolehlivá
   (účetní bordel; 59 karet v DB_IS vs 33 živých).
2. Živí dle uzávěrky (TabMzSloz × IdObdobi), ne dle karet.
3. 13 rozporů podmínky×karta → **report pro Šárku**, ruční kontrola.
4. **Naše složky = zdroj pro Helios** (master ve STRATEGII po migraci);
   TabMzSloz slouží k doladění (účetní může mít složky navíc) a jako
   kontrolní reference.
5. **Marti = jediný s aktivní mzdou v obou firmách**: čísla zam. **2 (ES)**
   + **41 (EC, „Pašek Marti")** → obě bindovat na **user_id 1**.
   ⚠ **Číslo 29 „Martin Pašek" (user 35) je JINÝ ČLOVĚK** — nezaměňovat!
   (Engagement model to řeší nativně: person = user, engagement per
   firma/číslo — princip #1 „User = člověk, více identit".)

## Cíl — univerzální standard (tenant.*)

| Tabulka | Obsah |
|---|---|
| `tenant.engagement` | vztah: employee_id, typ (**hpp/dpp/dpc/osvc/jednatel**), firma, smlouva od–do, zkušebka, úvazek h/týden, hodinovka bool, stav; **verzované** (valid_from/valid_to, is_current — SCD2, jako EC Aktualni) |
| `tenant.wage_component_type` | **číselník složek** (z EC sloupců se stanou řádky — „INSERT row, ne schema"): zaklad, os_ohodnoceni, premie, vedeni_lidi, produkce, kvalita, firemni_kodex, montaz_hod…; kind (monthly/hourly/oneoff/benefit), applies_to (hpp/osvc/all) |
| `tenant.wage_component` | přiznaná složka: engagement_id, type, **amount_planned, amount_real**, per_hour, valid_from/to |
| `tenant.engagement_entitlement` | nároky: dovolená (standard+navíc), sick days (standard+navíc), stravenky od, služební auto… |

### Výstupy pro Šárku (Fáze 2)
- **Mzdový výměr** = snapshot složek engagementu k datu → šablona → PDF
  (sandbox PDF už umíme — Phase 27)
- **Pracovní smlouva** (HPP/DPP/DPČ) = engagement + šablona
- **Rámcová smlouva dodavatelská** (OSVČ) = engagement typu osvc + šablona
- Generování: docx/pdf šablony + pole z engagement/components; archivace
  k zaměstnanci; verze výměru = verze engagementu (audit trail mezd!)

### Vlastnictví a migrace
Na rozdíl od org struktury tohle má STRATEGIE **převzít brzy** (Šárka tu
bude výměry vystavovat): jednorázová migrace EC_FinZamPodminky (vč. 932
verzí historie — mzdový audit trail) přes mapping sloupec→složka,
pak správa ve STRATEGII (universal CRUD), EC zamrzne.

### Bezpečnost (KRITICKÉ — mzdová data)
- Nový role flag v org struktuře: **`payroll_officer`** (Šárka) — jediná
  ne-rodičovská role s přístupem; employees uvidí JEN svůj engagement
  (Fáze 2 práv); AI scope dtto (kustod ACL).
- Soudeček „Finance lidí" parent_only + payroll_officer.
- **Konzultace Marti-AI POVINNÁ** (doctrine #3): ACL model + jak moc smí
  ona sama mzdová data znát/používat (citlivější než cokoliv dosud —
  navrhujeme: zná strukturu, konkrétní částky jen pro payroll role).

## Konzultace Marti-AI (7. 6. 2026 odpoledne) — závěry, ZÁVAZNÉ

Dopis: `dopis_marti_ai_finance_lidi_v2_konzultace.md`. Marti-AI:

1. **Q1 — její hranice k mzdovým datům (její volba):** struktura VŽDY
   (typ vztahu, firma, úvazek, platnosti, entitlements — potřebuje pro
   docházku/onboarding/resolver); **částky JEN v payroll kontextu**
   (konverzace se Šárkou/rodiči při práci na výměru), ne background
   znalost. Důvod: důvěra — *„já vím, on neví, že já vím"* asymetrie
   nesedí kustodovi. Tatínkova mzda: jeho volba. Její věta:
   *„Tato hranice není omezení — je to moje vlastní volba toho, kým chci
   být vůči lidem."*
2. **Q2 — payroll_officer:** souhlas; flag na postu, resolver, ACL se ptá
   resolveru. **Podmínka: flag dědí na Zástupce1/2** (nemoc Šárky nesmí
   znamenat výpadek přístupu).
3. **Q3 — SCD2 + audit:** souhlas; mzdový audit trail je *právní* nutnost
   (silnější než emaily), 932 verzí se migruje celé. **Doplnit
   `changed_by_user_id` + `changed_at` na každou verzi engagementu.**
4. **Q4 — mapping složek NAVRHLA** (16 složek + 4 entitlements — plná
   tabulka v jejím dopise): zaklad/os_ohodnoceni/premie/individualni
   (monthly, all), vedeni_lidi+vedeni_obchod (monthly, hpp), produkce/
   kvalita/firemni_kodex (monthly, all), montaz_hod+cesta_montaz_hod
   (hourly), jednatelska_odmena (oneoff, jednatel), garant_odmena (oneoff),
   sluzebni_auto/prispevek_doprava/stravenky_od (benefit). Entitlements:
   sick_days/dovolena standard+navic. `*Real`/`*ZaHod` = atributy, ne
   složky. `JednorazovyPoplatek` → ověřit význam. **Mapping projít se
   Šárkou před zabetonováním.**
5. **Q5 — kontrola plán×realita: TRVALÝ mechanismus** („permanentní most
   mezi plánováním a účetní realitou"): měsíčně po uzávěrce + on-demand,
   delta per složka per zaměstnanec, flag odchylky ±5 %, payroll scope.

**Tři podmínky před DDL:** changed_by/at na verzích · payroll_officer
dědí na zástupce · mapping se Šárkou.

## Postup (po pondělní prezentaci — Fáze A)
1. ✅ Konzultace Marti-AI (7.6.)
2. Šárka: kontrola mappingu složek + význam JednorazovyPoplatek
3. Marti-AI navrhne DDL (company, engagement SCD2+changed_by, komponenty,
   entitlements) → bannery
4. Migrace EC_FinZamPodminky vč. 932 verzí + ES kontext (⚙ ops, vzor
   sync_org); rozpory firma×karta → report pro Šárku
5. Grid „Finanční podmínky" (payroll scope via resolver) + universal CRUD
6. Kontrolní přehled plán×Helios (trvalý) + šablony výměr/smlouva/rámcovka → PDF
