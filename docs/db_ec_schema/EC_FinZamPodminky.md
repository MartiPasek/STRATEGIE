# EC_FinZamPodminky

**Schema**: dbo · **Cluster**: Finance · **Rows**: 929 · **Size**: 1.02 MB · **Sloupců**: 79 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Hodinovka` | bit | NE | ((0)) |  |
| 4 | `PlatnostOd` | datetime | ANO |  |  |
| 5 | `StrucnyPopisPracPozic` | nvarchar(250) | ANO |  |  |
| 6 | `SmlouvaUvazekT` | numeric(18,2) | ANO |  |  |
| 7 | `RealUvazekT` | numeric(18,2) | ANO |  |  |
| 8 | `HodTMin` | numeric(18,2) | ANO |  |  |
| 9 | `HodTOptimal` | numeric(18,2) | ANO |  |  |
| 10 | `HodTMax` | numeric(18,2) | ANO |  |  |
| 11 | `PocetHodMes` | numeric(18,2) | ANO |  |  |
| 12 | `ZakladZaHod` | numeric(18,2) | ANO |  |  |
| 13 | `HrHodBezFK` | numeric(18,2) | ANO |  |  |
| 14 | `SuperhrHodsFK` | numeric(18,2) | ANO |  |  |
| 15 | `SuperhrsFKSD` | numeric(18,2) | ANO |  |  |
| 16 | `SuperhrsFKSDDN` | numeric(18,2) | ANO |  |  |
| 17 | `SuperHrsFKSDReal` | numeric(18,2) | ANO |  |  |
| 18 | `HrHodsFK` | numeric(18,2) | ANO |  |  |
| 19 | `Zaklad` | numeric(18,0) | ANO |  |  |
| 20 | `OsOhodZaHod` | numeric(18,0) | ANO |  |  |
| 21 | `OsOhod` | numeric(18,0) | ANO |  |  |
| 22 | `OsOhodReal` | numeric(18,2) | ANO |  |  |
| 23 | `MzdPremie` | numeric(18,2) | ANO |  |  |
| 24 | `MzdPremieReal` | numeric(18,2) | ANO |  |  |
| 25 | `VykonOhodZaHod` | numeric(18,0) | ANO |  |  |
| 26 | `VedeniObch` | numeric(18,0) | ANO |  |  |
| 27 | `VedeniObchReal` | numeric(18,2) | ANO |  |  |
| 28 | `VedeniLidi` | numeric(18,2) | ANO |  |  |
| 29 | `VedeniLidiReal` | numeric(18,2) | ANO |  |  |
| 30 | `FKodexKultur` | numeric(18,2) | ANO |  |  |
| 31 | `FKodexKulturReal` | numeric(18,2) | ANO |  |  |
| 32 | `Produkce` | numeric(18,2) | ANO |  |  |
| 33 | `ProdukceReal` | numeric(18,2) | ANO |  |  |
| 34 | `IndividualOhod` | numeric(18,2) | ANO |  |  |
| 35 | `IndividualOhodReal` | numeric(18,2) | ANO |  |  |
| 36 | `MzdaCelkemHod` | numeric(18,2) | ANO |  |  |
| 37 | `MzdaCelkem` | numeric(18,2) | ANO |  |  |
| 38 | `MzdaCelkemReal` | numeric(18,2) | ANO |  |  |
| 39 | `MzdaPlnyUvazek` | numeric(18,2) | ANO |  |  |
| 40 | `MzdaSuperhruba` | numeric(18,2) | ANO |  |  |
| 41 | `MzdaSuperhrubaReal` | numeric(18,2) | ANO |  |  |
| 42 | `VolnoStandard` | int | ANO |  |  |
| 43 | `VolnoNavic` | int | ANO |  |  |
| 44 | `VolnoCelkem` | int | ANO |  |  |
| 45 | `SickDayStandard` | int | ANO |  |  |
| 46 | `SickDayNavic` | numeric(18,0) | ANO |  |  |
| 47 | `SickDayCelkem` | numeric(19,0) | ANO |  |  |
| 48 | `DruhSmlouvy` | int | ANO |  |  |
| 49 | `DruhSmlouvyText` | varchar(12) | NE |  |  |
| 50 | `JednorazovyPoplatek` | numeric(18,0) | ANO |  |  |
| 51 | `Aktualni` | bit | NE | ((0)) |  |
| 52 | `OdmenaGarant` | numeric(18,2) | ANO |  |  |
| 53 | `OdmenaJednatel` | numeric(18,2) | ANO |  |  |
| 54 | `NeplacenyPrescas` | numeric(9,2) | ANO |  |  |
| 55 | `DatumSmlouvyOd` | datetime | ANO |  |  |
| 56 | `DatumSmlouvyDo` | datetime | ANO |  |  |
| 57 | `ZkusebniDobaDo` | datetime | ANO |  |  |
| 58 | `PodepsaneProhl` | bit | NE | ((0)) |  |
| 59 | `ZdrPojKod` | int | ANO |  |  |
| 60 | `SrazetNeodpracovaneHodiny` | bit | NE | ((1)) |  |
| 61 | `PozadovanyPlat` | nvarchar(250) | ANO |  |  |
| 62 | `BenefitSluzebAut` | numeric(18,2) | ANO |  |  |
| 63 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 64 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 65 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 66 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 67 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 68 | `DopocZkDobu` | bit | ANO | ((0)) |  |
| 69 | `StravenkyOD` | datetime | ANO |  |  |
| 70 | `TarifOD` | datetime | ANO |  |  |
| 71 | `Kvalita` | numeric(18,2) | ANO |  |  |
| 72 | `KvalitaReal` | numeric(18,2) | ANO |  |  |
| 73 | `RezieMax` | numeric(18,2) | ANO |  |  |
| 74 | `Firma` | int | NE | ((0)) |  |
| 75 | `PrispevekDoprava` | int | ANO | ((0)) |  |
| 76 | `MontazKcHod` | numeric(18,2) | ANO |  |  |
| 77 | `CestaMontazKcHod` | numeric(18,2) | ANO |  |  |
| 78 | `ZakladReal` | numeric(18,2) | ANO |  |  |
| 79 | `Odpocet1Mesic` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_FinZamPodminky` (CLUSTERED) — `ID`
- **INDEX** `IX_FinZamPodminky_OndraTest` (NONCLUSTERED) — `CisloZam`
