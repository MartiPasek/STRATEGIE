# EC_ZakazkyZisk

**Schema**: dbo · **Cluster**: Finance · **Rows**: 4,674 · **Size**: 4.14 MB · **Sloupců**: 70 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Irelevantni` | bit | NE | ((0)) |  |
| 3 | `CisloZakazky` | nvarchar(50) | ANO |  |  |
| 4 | `ObjednavkyP` | numeric(18,2) | ANO |  |  |
| 5 | `FakturyV` | numeric(18,2) | ANO |  |  |
| 6 | `ObjednavkyV` | numeric(18,2) | ANO |  |  |
| 7 | `FakturyP` | numeric(18,2) | ANO |  |  |
| 8 | `Kalkulace` | numeric(18,2) | ANO |  |  |
| 9 | `CisloKalkulace` | nvarchar(50) | ANO |  |  |
| 10 | `VKM` | numeric(18,2) | ANO |  |  |
| 11 | `NakladyCelkem` | numeric(18,2) | ANO |  |  |
| 12 | `NakladyCelkemPevne` | numeric(18,2) | ANO |  |  |
| 13 | `VynosyCelkem` | numeric(18,2) | ANO |  |  |
| 14 | `NakladyRezie` | numeric(18,2) | ANO |  |  |
| 15 | `NakladyReziePevne` | numeric(18,2) | ANO |  |  |
| 16 | `ZiskZakazky` | numeric(18,2) | ANO |  |  |
| 17 | `ZiskZakazkyPevny` | numeric(18,2) | ANO |  |  |
| 18 | `Kurz` | numeric(18,2) | ANO |  |  |
| 19 | `NakladyMaterial` | numeric(18,2) | ANO |  |  |
| 20 | `NakladyMonter` | numeric(18,2) | ANO |  |  |
| 21 | `Stredisko` | nvarchar(10) | ANO |  |  |
| 22 | `KalkHodinyCelkem` | numeric(18,2) | ANO |  |  |
| 23 | `RealHodinyCelkem` | numeric(18,2) | ANO |  |  |
| 24 | `DatumKonecReal` | datetime | ANO |  |  |
| 25 | `Ukonceno` | bit | ANO |  |  |
| 26 | `RezieNaKalkHod` | numeric(18,2) | ANO |  |  |
| 27 | `RezieNaKalkHodPevne` | numeric(18,2) | ANO |  |  |
| 28 | `RezieCelkemRok` | numeric(18,2) | ANO |  |  |
| 29 | `RezieCelkemRokPevne` | numeric(18,2) | ANO |  |  |
| 30 | `DatPosledniVF` | datetime | ANO |  |  |
| 31 | `DatPorizeni_Y` | int | ANO |  |  |
| 32 | `DatPorizeni_M` | int | ANO |  |  |
| 33 | `DatPorizeni_W` | int | ANO |  |  |
| 34 | `DatPorizeni_D` | int | ANO |  |  |
| 35 | `StornoVydejkyZakCelkem` | numeric(18,2) | ANO |  |  |
| 36 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 37 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 38 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 39 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 40 | `RezieZakZKalk` | numeric(18,2) | ANO |  |  |
| 41 | `RezieZakZKalkPevne` | numeric(18,2) | ANO |  |  |
| 42 | `SumKalkMaterial` | numeric(18,2) | ANO |  |  |
| 43 | `Posledni` | bit | ANO |  |  |
| 44 | `RozdilMaterial` | numeric(18,2) | ANO |  |  |
| 45 | `RozdilHodin` | numeric(18,2) | ANO |  |  |
| 46 | `DatOdvozuZDopr` | nvarchar(100) | ANO |  |  |
| 47 | `SlouceneZakazky` | bit | ANO |  |  |
| 48 | `SlouceneZakazkySeznam` | nvarchar(100) | ANO |  |  |
| 49 | `SumKalkMaterialSlouc` | numeric(18,2) | ANO |  |  |
| 50 | `KalkHodinyCelkemSlouc` | numeric(18,2) | ANO |  |  |
| 51 | `RealHodinyCelkemSlouc` | numeric(18,2) | ANO |  |  |
| 52 | `NakladyMaterialSlouc` | numeric(18,2) | ANO |  |  |
| 53 | `NakladyMonterSlouc` | numeric(18,2) | ANO |  |  |
| 54 | `VKM_Koef` | numeric(18,2) | ANO |  |  |
| 55 | `KalkHodinyCelkemRok` | numeric(18,2) | ANO |  |  |
| 56 | `PrumMzdaDilnaHod` | numeric(6,2) | ANO |  |  |
| 57 | `PremieLidiZak` | numeric(8,2) | ANO |  |  |
| 58 | `MzdaDochMonter` | numeric(8,2) | ANO |  |  |
| 59 | `ZbyvaOdpracovatHod` | numeric(6,2) | ANO |  |  |
| 60 | `ZbyvaOdpracovatKc` | numeric(8,2) | ANO |  |  |
| 61 | `ViceHodiny` | numeric(6,2) | ANO | ((0)) |  |
| 62 | `NakladyCelkemPevneZKalkHod` | numeric(18,2) | ANO |  |  |
| 63 | `ZiskZakazkyPevnyZKalkHod` | numeric(18,2) | ANO |  |  |
| 64 | `KCPraceMonterNaKalkHod` | numeric(18,2) | ANO |  |  |
| 65 | `Resit` | bit | ANO | ((0)) |  |
| 66 | `ResitPoznamka` | nvarchar(4000) | ANO |  |  |
| 67 | `CasPriprava` | numeric(5,2) | ANO |  |  |
| 68 | `CasZkusebna` | numeric(5,2) | ANO |  |  |
| 69 | `PocetMonteru` | int | ANO |  |  |
| 70 | `RealHodinyCelkemEf` | numeric(18,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZakazkyZisk` (CLUSTERED) — `ID`
