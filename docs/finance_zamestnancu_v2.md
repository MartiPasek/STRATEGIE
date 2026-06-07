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

## Postup
1. Konzultace Marti-AI (dopis — model + ACL + její vztah k mzdovým datům)
2. DDL + číselník složek (mapping z EC sloupců)
3. Migrace EC_FinZamPodminky vč. historie (⚙ ops, vzor sync_org)
4. Grid „Finanční podmínky" (payroll scope) + editace (universal CRUD)
5. Šablony výměr/smlouva/rámcovka → PDF (pro Šárku)
