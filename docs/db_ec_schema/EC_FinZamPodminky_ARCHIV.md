# EC_FinZamPodminky_ARCHIV

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 60 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPuv` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `Hodinovka` | bit | NE | ((0)) |  |
| 5 | `PlatnostOd` | datetime | ANO | ((0)) |  |
| 6 | `StrucnyPopisPracPozic` | nvarchar(250) | ANO |  |  |
| 7 | `RealUvazekT` | numeric(18,2) | ANO |  |  |
| 8 | `SmlouvaUvazekT` | numeric(18,2) | ANO |  |  |
| 9 | `HodTMin` | numeric(18,2) | ANO |  |  |
| 10 | `HodTOptimal` | numeric(18,2) | ANO |  |  |
| 11 | `HodTMax` | numeric(18,2) | ANO |  |  |
| 12 | `PocetHodMes` | numeric(18,2) | ANO |  |  |
| 13 | `ZakladZaHod` | numeric(18,0) | ANO |  |  |
| 14 | `HrHodBezFK` | numeric(18,2) | ANO |  |  |
| 15 | `SuperhrHodsFK` | numeric(18,2) | ANO |  |  |
| 16 | `SuperhrsFKSD` | numeric(18,2) | ANO |  |  |
| 17 | `SuperHrsFKSDReal` | numeric(18,2) | ANO |  |  |
| 18 | `HrHodsFK` | numeric(18,2) | ANO |  |  |
| 19 | `Zaklad` | numeric(18,0) | ANO |  |  |
| 20 | `OsOhodZaHod` | numeric(18,0) | ANO |  |  |
| 21 | `OsOhod` | numeric(18,0) | ANO |  |  |
| 22 | `VykonOhodZaHod` | numeric(18,0) | ANO |  |  |
| 23 | `VedeniObch` | numeric(18,0) | ANO |  |  |
| 24 | `VedeniLidi` | numeric(18,0) | ANO |  |  |
| 25 | `FKodexKultur` | numeric(18,0) | ANO |  |  |
| 26 | `Produkce` | numeric(18,0) | ANO |  |  |
| 27 | `IndividualOhod` | numeric(18,0) | ANO |  |  |
| 28 | `MzdaCelkemHod` | numeric(18,0) | ANO |  |  |
| 29 | `MzdaCelkem` | numeric(18,0) | ANO |  |  |
| 30 | `MzdaPlnyUvazek` | numeric(18,0) | ANO |  |  |
| 31 | `VolnoStandard` | int | ANO |  |  |
| 32 | `VolnoNavic` | int | ANO |  |  |
| 33 | `VolnoCelkem` | int | ANO |  |  |
| 34 | `SickDayStandard` | int | ANO |  |  |
| 35 | `SickDayNavic` | numeric(18,0) | ANO |  |  |
| 36 | `SickDayCelkem` | numeric(18,0) | ANO |  |  |
| 37 | `DruhSmlouvy` | int | ANO |  |  |
| 38 | `DruhSmlouvyText` | varchar(50) | ANO |  |  |
| 39 | `JednorazovyPoplatek` | numeric(18,0) | ANO |  |  |
| 40 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 41 | `Aktualni` | bit | ANO |  |  |
| 42 | `DatumSmlouvyOd` | datetime | ANO |  |  |
| 43 | `DatumSmlouvyDo` | datetime | ANO |  |  |
| 44 | `NeplacenyPrescas` | numeric(9,2) | ANO |  |  |
| 45 | `OdmenaGarant` | numeric(18,2) | ANO |  |  |
| 46 | `ZkusebniDobaDo` | datetime | ANO |  |  |
| 47 | `PodepsaneProhl` | bit | ANO |  |  |
| 48 | `ZdrPojKod` | int | ANO |  |  |
| 49 | `SrazetNeodpracovaneHodiny` | bit | ANO | ((1)) |  |
| 50 | `PozadovanyPlat` | nvarchar(250) | ANO |  |  |
| 51 | `BenefitSluzebAut` | numeric(18,2) | ANO |  |  |
| 52 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 53 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 54 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 55 | `DatZmeny` | datetime | ANO |  |  |
| 56 | `Archivoval` | nvarchar(50) | ANO | (suser_sname()) |  |
| 57 | `DatArchivace` | datetime | NE | (getdate()) |  |
| 58 | `Kvalita` | numeric(18,2) | ANO |  |  |
| 59 | `RezieMax` | numeric(18,2) | ANO |  |  |
| 60 | `Firma` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_FinZamPodminky_ARCHIV_1` (CLUSTERED) — `ID`
